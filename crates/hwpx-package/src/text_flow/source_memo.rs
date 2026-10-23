//! Source-preserving MEMO envelope; author/time/visibility/resolution remain unknown.
use super::{
    PreservingXmlDocument, ReadState, TextFlowError, child_indexes, element, has_name,
    require_only_whitespace_content, validate_parameter_entries,
};
#[cfg(test)]
mod meta_tests;

pub(super) fn validate_payload(
    document: &PreservingXmlDocument,
    payload: &[usize],
    state: &mut ReadState,
) -> Result<(), TextFlowError> {
    // Closed source-preserving sequence: parameters?, subList?, metaTag?.
    // Existing body-before-parameters, duplicate and nested-review negatives stay rejected.
    let mut position = 0;
    for name in ["parameters", "subList", "metaTag"] {
        if let Some(index) = payload.get(position).copied()
            && has_name(element(document, index)?, name)
        {
            match name {
                "parameters" => validate_parameter_entries(document, index, state)?,
                "subList" => validate_body(document, index, state)?,
                _ => {
                    state.count_item()?;
                    state.count_text(meta_tag_span(document, index)?.len())?;
                }
            }
            position += 1;
        }
    }
    if payload.is_empty() || position != payload.len() {
        return Err(TextFlowError::InvalidField);
    }
    Ok(())
}

pub(super) fn meta_tag_span(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<crate::XmlByteSpan, TextFlowError> {
    let meta = element(document, index)?;
    super::require_name(meta, "metaTag")?;
    super::validate_attributes(meta, &[])?;
    if meta.first_child().is_some() {
        return Err(TextFlowError::InvalidField);
    }
    meta.outer_span().ok_or(TextFlowError::InvalidField)
}

fn validate_body(
    document: &PreservingXmlDocument,
    body: usize,
    state: &mut ReadState,
) -> Result<(), TextFlowError> {
    require_only_whitespace_content(document, body)?;
    let paragraphs = child_indexes(document, body)?;
    if paragraphs.is_empty()
        || paragraphs
            .iter()
            .any(|p| !element(document, *p).is_ok_and(|e| has_name(e, "p")))
    {
        return Err(TextFlowError::InvalidField);
    }
    let span = element(document, body)?
        .outer_span()
        .ok_or(TextFlowError::InvalidField)?;
    state.count_text(span.len())?;
    // Preserve every byte, but do not silently accept nested review/field/note
    // semantics in this closed envelope. The typed body importer validates paragraphs.
    // Parser elements are in start-token order. Scan this contiguous subtree,
    // not the whole document again for every MEMO body.
    let last_token = element(document, body)?
        .end_token()
        .ok_or(TextFlowError::InvalidField)?;
    for e in document.elements()[body..]
        .iter()
        .take_while(|e| e.start_token() <= last_token)
    {
        if !e
            .outer_span()
            .is_some_and(|s| span.start() <= s.start() && s.end() <= span.end())
        {
            return Err(TextFlowError::InvalidField);
        }
        state.count_item()?;
        if [
            "fieldBegin",
            "fieldEnd",
            "hiddenComment",
            "footNote",
            "endNote",
        ]
        .iter()
        .any(|name| has_name(e, name))
        {
            return Err(TextFlowError::InvalidField);
        }
    }
    Ok(())
}
