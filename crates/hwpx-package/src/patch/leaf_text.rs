//! Source-bound semantic leaf replacement. No fragment, caller offsets or namespace guessing.
use super::{
    ByteEdit, PatchError, PatchText, Transaction, XmlElementSelector, XmlTokenKind, escape_text,
};

impl Transaction<'_> {
    pub(super) fn plan_leaf_text_edit(
        &self,
        target: &XmlElementSelector,
        value: &PatchText,
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        self.check_value_limit(value.0.len())?;
        let document = self.element_context(target)?;
        let node = &document.elements()[target.element_index];
        if node.parent().is_none() {
            return Err(PatchError::RootMutation);
        }
        if node.first_child().is_some() {
            return Err(PatchError::FragmentInvalid);
        }
        let escaped = escape_text(value.value())?;
        // A literal CR is normalized to LF by XML. Preserve the semantic CR
        // without changing the generic text/attribute escaping paths.
        let escaped = if escaped.contains('\r') { escaped.replace('\r', "&#13;") } else { escaped };
        let (start, end, bytes) = if node.is_empty() {
            // The original indexed name/attributes are retained exactly. Only '/>' expands.
            let tag = node.start_tag_span();
            let name = node.start_name_span();
            let closing = document.with_source_bytes(|raw| {
                let tag_bytes = &raw[tag.start()..tag.end()];
                if !tag_bytes.ends_with(b"/>") {
                    return Err(PatchError::SelectorStale);
                }
                let mut bytes = Vec::new();
                bytes.extend_from_slice(b">");
                bytes.extend_from_slice(escaped.as_bytes());
                bytes.extend_from_slice(b"</");
                bytes.extend_from_slice(&raw[name.start()..name.end()]);
                bytes.extend_from_slice(b">");
                Ok(bytes)
            })?;
            (tag.end() - 2, tag.end(), closing)
        } else {
            let span = node.content_span().ok_or(PatchError::SelectorStale)?;
            for token in &document.tokens()
                [node.start_token() + 1..node.end_token().ok_or(PatchError::SelectorStale)?]
            {
                if token.element_index() != Some(target.element_index)
                    || !matches!(
                        token.kind(),
                        XmlTokenKind::Text | XmlTokenKind::Whitespace | XmlTokenKind::Reference
                    )
                {
                    return Err(PatchError::FragmentInvalid);
                }
            }
            (span.start(), span.end(), escaped.into_bytes())
        };
        edits.push(ByteEdit::new(
            target.part.collision_key(),
            start,
            end,
            bytes,
            origin,
        ));
        Ok(())
    }
}
