use std::fmt::{self, Debug};

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::safe_xml::{
    SafeXmlAttributeName, SafeXmlDocument, SafeXmlElement, SafeXmlError, SafeXmlEvent,
    SafeXmlLimits, SafeXmlSpan,
};

const XMLNS_NAMESPACE: &str = "http://www.w3.org/2000/xmlns/";

/// A checked half-open byte range into the exact UTF-8 XML input.
#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct XmlByteSpan {
    start: usize,
    end: usize,
}

impl XmlByteSpan {
    fn checked(input: &str, start: usize, end: usize) -> Result<Self, PreservingXmlError> {
        if start > end
            || end > input.len()
            || !input.is_char_boundary(start)
            || !input.is_char_boundary(end)
        {
            return Err(PreservingXmlError::InvalidSpan);
        }
        Ok(Self { start, end })
    }

    #[must_use]
    pub const fn start(self) -> usize {
        self.start
    }

    #[must_use]
    pub const fn end(self) -> usize {
        self.end
    }

    #[must_use]
    pub const fn len(self) -> usize {
        self.end - self.start
    }

    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.start == self.end
    }
}

/// Namespace-resolved XML name metadata. Text and attribute values are not exposed.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct XmlName {
    qualified_name: String,
    prefix: Option<String>,
    local_name: String,
    namespace: Option<String>,
}

impl XmlName {
    fn new(qualified_name: String, local_name: String, namespace: Option<String>) -> Self {
        let prefix = qualified_name
            .split_once(':')
            .map(|(prefix, _)| prefix.to_owned());
        Self {
            qualified_name,
            prefix,
            local_name,
            namespace,
        }
    }

    #[must_use]
    pub fn qualified_name(&self) -> &str {
        &self.qualified_name
    }

    #[must_use]
    pub fn prefix(&self) -> Option<&str> {
        self.prefix.as_deref()
    }

    #[must_use]
    pub fn local_name(&self) -> &str {
        &self.local_name
    }

    #[must_use]
    pub fn namespace(&self) -> Option<&str> {
        self.namespace.as_deref()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum XmlQuoteStyle {
    Single,
    Double,
}

/// Structural metadata for one attribute without its untrusted raw value.
#[derive(Clone, Eq, PartialEq)]
pub struct XmlAttributeToken {
    name: XmlName,
    span: XmlByteSpan,
    name_span: XmlByteSpan,
    value_span: XmlByteSpan,
    quote: XmlQuoteStyle,
    namespace_declaration: bool,
    semantic_value: String,
}

impl Debug for XmlAttributeToken {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("XmlAttributeToken")
            .field("name", &self.name)
            .field("span", &self.span)
            .field("name_span", &self.name_span)
            .field("value_span", &self.value_span)
            .field("quote", &self.quote)
            .field("namespace_declaration", &self.namespace_declaration)
            .field("semantic_value_bytes", &self.semantic_value.len())
            .finish()
    }
}

impl XmlAttributeToken {
    #[must_use]
    pub const fn span(&self) -> XmlByteSpan {
        self.span
    }

    #[must_use]
    pub const fn name_span(&self) -> XmlByteSpan {
        self.name_span
    }

    #[must_use]
    pub const fn value_span(&self) -> XmlByteSpan {
        self.value_span
    }

    #[must_use]
    pub const fn quote_style(&self) -> XmlQuoteStyle {
        self.quote
    }

    #[must_use]
    pub const fn is_namespace_declaration(&self) -> bool {
        self.namespace_declaration
    }

    #[must_use]
    pub const fn name(&self) -> &XmlName {
        &self.name
    }

    pub(crate) fn semantic_value(&self) -> &str {
        &self.semantic_value
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum XmlTokenKind {
    ByteOrderMark,
    Declaration,
    StartElement,
    EmptyElement,
    EndElement,
    Text,
    Whitespace,
    Reference,
    Comment,
}

/// One exact source token. For markup tokens `element_index` identifies that
/// element; for content tokens it identifies the containing element.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct XmlToken {
    kind: XmlTokenKind,
    span: XmlByteSpan,
    element_index: Option<usize>,
}

impl XmlToken {
    #[must_use]
    pub const fn kind(&self) -> XmlTokenKind {
        self.kind
    }

    #[must_use]
    pub const fn span(&self) -> XmlByteSpan {
        self.span
    }

    #[must_use]
    pub const fn element_index(&self) -> Option<usize> {
        self.element_index
    }
}

/// Lightweight namespace-aware element index over immutable source bytes.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct XmlElementToken {
    name: XmlName,
    depth: usize,
    start_token: usize,
    end_token: Option<usize>,
    start_tag_span: XmlByteSpan,
    end_tag_span: Option<XmlByteSpan>,
    start_name_span: XmlByteSpan,
    end_name_span: Option<XmlByteSpan>,
    outer_span: Option<XmlByteSpan>,
    content_span: Option<XmlByteSpan>,
    attributes: Vec<XmlAttributeToken>,
    parent: Option<usize>,
    first_child: Option<usize>,
    last_child: Option<usize>,
    previous_sibling: Option<usize>,
    next_sibling: Option<usize>,
    empty: bool,
}

impl XmlElementToken {
    #[must_use]
    pub const fn name(&self) -> &XmlName {
        &self.name
    }

    #[must_use]
    pub const fn depth(&self) -> usize {
        self.depth
    }

    #[must_use]
    pub const fn start_token(&self) -> usize {
        self.start_token
    }

    #[must_use]
    pub const fn end_token(&self) -> Option<usize> {
        self.end_token
    }

    #[must_use]
    pub const fn start_tag_span(&self) -> XmlByteSpan {
        self.start_tag_span
    }

    #[must_use]
    pub const fn end_tag_span(&self) -> Option<XmlByteSpan> {
        self.end_tag_span
    }

    #[must_use]
    pub const fn start_name_span(&self) -> XmlByteSpan {
        self.start_name_span
    }

    #[must_use]
    pub const fn end_name_span(&self) -> Option<XmlByteSpan> {
        self.end_name_span
    }

    #[must_use]
    pub const fn outer_span(&self) -> Option<XmlByteSpan> {
        self.outer_span
    }

    #[must_use]
    pub const fn content_span(&self) -> Option<XmlByteSpan> {
        self.content_span
    }

    #[must_use]
    pub fn attributes(&self) -> &[XmlAttributeToken] {
        &self.attributes
    }

    #[must_use]
    pub const fn parent(&self) -> Option<usize> {
        self.parent
    }

    #[must_use]
    pub const fn first_child(&self) -> Option<usize> {
        self.first_child
    }

    #[must_use]
    pub const fn last_child(&self) -> Option<usize> {
        self.last_child
    }

    #[must_use]
    pub const fn previous_sibling(&self) -> Option<usize> {
        self.previous_sibling
    }

    #[must_use]
    pub const fn next_sibling(&self) -> Option<usize> {
        self.next_sibling
    }

    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.empty
    }
}

/// Exact-source XML token model. The source bytes stay private; callers receive
/// structural spans, namespace identities, and an integrity digest only.
#[derive(Eq, PartialEq)]
pub struct PreservingXmlDocument {
    original: Box<[u8]>,
    original_sha256: [u8; 32],
    tokens: Vec<XmlToken>,
    elements: Vec<XmlElementToken>,
    root_element: usize,
}

impl Debug for PreservingXmlDocument {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PreservingXmlDocument")
            .field("original_len", &self.original.len())
            .field("original_sha256", &self.original_sha256)
            .field("token_count", &self.tokens.len())
            .field("element_count", &self.elements.len())
            .field("root_element", &self.root_element)
            .finish()
    }
}

impl PreservingXmlDocument {
    /// Parses with the finite P03-03 defaults and builds exact source spans.
    ///
    /// # Errors
    ///
    /// Returns a stable fail-closed error if safety validation, token/span
    /// alignment, tree construction, or allocation fails.
    pub fn parse(bytes: &[u8]) -> Result<Self, PreservingXmlError> {
        Self::parse_with_limits(bytes, SafeXmlLimits::default())
    }

    pub(crate) fn parse_with_limits(
        bytes: &[u8],
        limits: SafeXmlLimits,
    ) -> Result<Self, PreservingXmlError> {
        let safe_document = SafeXmlDocument::parse(bytes, limits)?;
        let input = std::str::from_utf8(bytes)
            .map_err(|_| PreservingXmlError::Safe(SafeXmlError::EncodingForbidden))?;
        if safe_document.events.len() != safe_document.spans.len() {
            return Err(PreservingXmlError::TokenMismatch);
        }
        let mut builder = PreservingBuildState::new(safe_document.events.len(), limits)?;
        for (event, safe_span) in safe_document.events.into_iter().zip(safe_document.spans) {
            builder.consume(input, event, safe_span)?;
        }
        builder.finish(input, bytes)
    }

    #[must_use]
    pub fn tokens(&self) -> &[XmlToken] {
        &self.tokens
    }

    #[must_use]
    pub fn elements(&self) -> &[XmlElementToken] {
        &self.elements
    }

    #[must_use]
    pub const fn root_element(&self) -> usize {
        self.root_element
    }

    #[must_use]
    pub const fn original_len(&self) -> usize {
        self.original.len()
    }

    #[must_use]
    pub const fn original_sha256(&self) -> [u8; 32] {
        self.original_sha256
    }

    /// Internal immutable bytes for source-bound semantic readers, never a
    /// public raw-XML action or a writable source buffer.
    pub(crate) fn with_source_bytes<T>(&self, read: impl FnOnce(&[u8]) -> T) -> T {
        read(&self.original)
    }

    pub(crate) fn source_text(&self, span: XmlByteSpan) -> Result<&str, PreservingXmlError> {
        let bytes = self
            .original
            .get(span.start()..span.end())
            .ok_or(PreservingXmlError::InvalidSpan)?;
        std::str::from_utf8(bytes).map_err(|_| PreservingXmlError::InvalidSpan)
    }

    /// Compares the exact concatenation of every untouched token with the whole
    /// source, then verifies its digest without a whole-XML temporary buffer.
    /// No raw XML is exposed through the public API.
    ///
    /// # Errors
    ///
    /// Returns a span or equality error if exact reconstruction fails.
    pub fn verify_untouched_round_trip(&self) -> Result<(), PreservingXmlError> {
        let mut offset = 0usize;
        let mut byte_exact = true;
        for token in &self.tokens {
            let span = token.span;
            let bytes = self
                .original
                .get(span.start()..span.end())
                .ok_or(PreservingXmlError::InvalidSpan)?;
            let end = offset
                .checked_add(bytes.len())
                .ok_or(PreservingXmlError::UntouchedMismatch)?;
            // Compare bytes at the reconstructed position, not span offsets.
            // Keep checking every span even after a mismatch, preserving the
            // original invalid-span error precedence over final equality.
            byte_exact &= self.original.get(offset..end) == Some(bytes);
            offset = end;
        }
        // The entire reconstructed byte sequence was compared above. Only
        // after byte equality may hashing the equal original replace hashing
        // a separately allocated serialized copy; this is not hash-only replay.
        if !byte_exact
            || offset != self.original.len()
            || <[u8; 32]>::from(Sha256::digest(&self.original)) != self.original_sha256
        {
            return Err(PreservingXmlError::UntouchedMismatch);
        }
        Ok(())
    }

    // Preserve the original allocating implementation as an independent test
    // oracle. Production verification does not construct a serialized copy.
    #[cfg(test)]
    fn serialize_untouched(&self) -> Result<Vec<u8>, PreservingXmlError> {
        let mut output = Vec::new();
        output
            .try_reserve_exact(self.original.len())
            .map_err(|_| PreservingXmlError::AllocationFailed)?;
        for token in &self.tokens {
            let span = token.span;
            let bytes = self
                .original
                .get(span.start()..span.end())
                .ok_or(PreservingXmlError::InvalidSpan)?;
            output.extend_from_slice(bytes);
        }
        Ok(output)
    }
}

struct PreservingBuildState {
    tokens: Vec<XmlToken>,
    elements: Vec<XmlElementToken>,
    stack: Vec<usize>,
    root_element: Option<usize>,
    expected_start: usize,
}

impl PreservingBuildState {
    fn new(event_count: usize, limits: SafeXmlLimits) -> Result<Self, PreservingXmlError> {
        let mut tokens = Vec::new();
        tokens
            .try_reserve_exact(event_count)
            .map_err(|_| PreservingXmlError::AllocationFailed)?;
        let mut elements = Vec::new();
        elements
            .try_reserve_exact(event_count.min(limits.config().nodes))
            .map_err(|_| PreservingXmlError::AllocationFailed)?;
        let mut stack = Vec::new();
        stack
            .try_reserve_exact(limits.config().depth)
            .map_err(|_| PreservingXmlError::AllocationFailed)?;
        Ok(Self {
            tokens,
            elements,
            stack,
            root_element: None,
            expected_start: 0,
        })
    }

    fn consume(
        &mut self,
        input: &str,
        event: SafeXmlEvent,
        safe_span: SafeXmlSpan,
    ) -> Result<(), PreservingXmlError> {
        let mut span = checked_safe_span(input, safe_span)?;
        if self.expected_start == 0 && input.as_bytes().starts_with(&[0xEF, 0xBB, 0xBF]) {
            let bom_span = XmlByteSpan::checked(input, 0, 3)?;
            push_token(
                &mut self.tokens,
                XmlTokenKind::ByteOrderMark,
                bom_span,
                None,
            )?;
            self.expected_start = 3;
            if span.start() == 0 {
                span = XmlByteSpan::checked(input, 3, span.end())?;
            } else if span.start() != 3 {
                return Err(PreservingXmlError::TokenMismatch);
            }
        }
        if span.is_empty() || span.start() != self.expected_start {
            return Err(PreservingXmlError::TokenMismatch);
        }
        self.expected_start = span.end();
        match event {
            SafeXmlEvent::Declaration => {
                push_token(&mut self.tokens, XmlTokenKind::Declaration, span, None)
            }
            SafeXmlEvent::Start(element) => self.start(input, span, element),
            SafeXmlEvent::Empty(element) => self.empty(input, span, element),
            SafeXmlEvent::End => self.end(input, span),
            SafeXmlEvent::Text { .. } => {
                let kind = if input.as_bytes()[span.start()..span.end()]
                    .iter()
                    .all(|byte| matches!(byte, b' ' | b'\t' | b'\r' | b'\n'))
                {
                    XmlTokenKind::Whitespace
                } else {
                    XmlTokenKind::Text
                };
                self.content_token(kind, span)
            }
            SafeXmlEvent::Reference => self.content_token(XmlTokenKind::Reference, span),
            SafeXmlEvent::Comment => self.content_token(XmlTokenKind::Comment, span),
        }
    }

    fn start(
        &mut self,
        input: &str,
        span: XmlByteSpan,
        element: SafeXmlElement,
    ) -> Result<(), PreservingXmlError> {
        let parts = parse_start_tag(input, span, &element, false)?;
        let element_index = begin_element(
            &mut self.elements,
            &self.stack,
            &mut self.root_element,
            element,
            parts,
            self.tokens.len(),
            false,
        )?;
        push_token(
            &mut self.tokens,
            XmlTokenKind::StartElement,
            span,
            Some(element_index),
        )?;
        self.stack.push(element_index);
        Ok(())
    }

    fn empty(
        &mut self,
        input: &str,
        span: XmlByteSpan,
        element: SafeXmlElement,
    ) -> Result<(), PreservingXmlError> {
        let parts = parse_start_tag(input, span, &element, true)?;
        let content_anchor = parts.content_anchor;
        let element_index = begin_element(
            &mut self.elements,
            &self.stack,
            &mut self.root_element,
            element,
            parts,
            self.tokens.len(),
            true,
        )?;
        push_token(
            &mut self.tokens,
            XmlTokenKind::EmptyElement,
            span,
            Some(element_index),
        )?;
        let element = self
            .elements
            .get_mut(element_index)
            .ok_or(PreservingXmlError::TreeInvalid)?;
        element.end_token = Some(element.start_token);
        element.outer_span = Some(span);
        element.content_span = Some(XmlByteSpan::checked(input, content_anchor, content_anchor)?);
        Ok(())
    }

    fn end(&mut self, input: &str, span: XmlByteSpan) -> Result<(), PreservingXmlError> {
        let element_index = self.stack.pop().ok_or(PreservingXmlError::TreeInvalid)?;
        let end_name_span = {
            let expected_name = self
                .elements
                .get(element_index)
                .ok_or(PreservingXmlError::TreeInvalid)?
                .name
                .qualified_name();
            parse_end_tag(input, span, expected_name)?
        };
        let token_index = self.tokens.len();
        push_token(
            &mut self.tokens,
            XmlTokenKind::EndElement,
            span,
            Some(element_index),
        )?;
        let element = self
            .elements
            .get_mut(element_index)
            .ok_or(PreservingXmlError::TreeInvalid)?;
        element.end_token = Some(token_index);
        element.end_tag_span = Some(span);
        element.end_name_span = Some(end_name_span);
        element.outer_span = Some(XmlByteSpan::checked(
            input,
            element.start_tag_span.start(),
            span.end(),
        )?);
        element.content_span = Some(XmlByteSpan::checked(
            input,
            element.start_tag_span.end(),
            span.start(),
        )?);
        Ok(())
    }

    fn content_token(
        &mut self,
        kind: XmlTokenKind,
        span: XmlByteSpan,
    ) -> Result<(), PreservingXmlError> {
        push_token(&mut self.tokens, kind, span, self.stack.last().copied())
    }

    fn finish(
        self,
        input: &str,
        bytes: &[u8],
    ) -> Result<PreservingXmlDocument, PreservingXmlError> {
        if self.expected_start != input.len() || !self.stack.is_empty() {
            return Err(PreservingXmlError::TokenMismatch);
        }
        let root_element = self.root_element.ok_or(PreservingXmlError::TreeInvalid)?;
        if self.elements.iter().any(|element| {
            element.end_token.is_none()
                || element.outer_span.is_none()
                || element.content_span.is_none()
        }) {
            return Err(PreservingXmlError::TreeInvalid);
        }
        let mut original = Vec::new();
        original
            .try_reserve_exact(bytes.len())
            .map_err(|_| PreservingXmlError::AllocationFailed)?;
        original.extend_from_slice(bytes);
        Ok(PreservingXmlDocument {
            original: original.into_boxed_slice(),
            original_sha256: Sha256::digest(bytes).into(),
            tokens: self.tokens,
            elements: self.elements,
            root_element,
        })
    }
}

struct ParsedStartTag {
    tag_span: XmlByteSpan,
    name_span: XmlByteSpan,
    attributes: Vec<XmlAttributeToken>,
    content_anchor: usize,
}

fn checked_safe_span(input: &str, span: SafeXmlSpan) -> Result<XmlByteSpan, PreservingXmlError> {
    XmlByteSpan::checked(input, span.start, span.end)
}

fn push_token(
    tokens: &mut Vec<XmlToken>,
    kind: XmlTokenKind,
    span: XmlByteSpan,
    element_index: Option<usize>,
) -> Result<(), PreservingXmlError> {
    tokens
        .try_reserve(1)
        .map_err(|_| PreservingXmlError::AllocationFailed)?;
    tokens.push(XmlToken {
        kind,
        span,
        element_index,
    });
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn begin_element(
    elements: &mut Vec<XmlElementToken>,
    stack: &[usize],
    root_element: &mut Option<usize>,
    element: SafeXmlElement,
    parts: ParsedStartTag,
    start_token: usize,
    empty: bool,
) -> Result<usize, PreservingXmlError> {
    let index = elements.len();
    let parent = stack.last().copied();
    let previous_sibling = parent
        .and_then(|parent_index| elements.get(parent_index))
        .and_then(|parent_element| parent_element.last_child);
    if parent.is_none() && root_element.replace(index).is_some() {
        return Err(PreservingXmlError::TreeInvalid);
    }
    elements
        .try_reserve(1)
        .map_err(|_| PreservingXmlError::AllocationFailed)?;
    elements.push(XmlElementToken {
        name: XmlName::new(
            element.qualified_name,
            element.local_name,
            element.namespace,
        ),
        depth: element.depth,
        start_token,
        end_token: None,
        start_tag_span: parts.tag_span,
        end_tag_span: None,
        start_name_span: parts.name_span,
        end_name_span: None,
        outer_span: None,
        content_span: None,
        attributes: parts.attributes,
        parent,
        first_child: None,
        last_child: None,
        previous_sibling,
        next_sibling: None,
        empty,
    });
    if let Some(previous_sibling) = previous_sibling {
        elements
            .get_mut(previous_sibling)
            .ok_or(PreservingXmlError::TreeInvalid)?
            .next_sibling = Some(index);
    }
    if let Some(parent) = parent {
        let parent = elements
            .get_mut(parent)
            .ok_or(PreservingXmlError::TreeInvalid)?;
        if parent.first_child.is_none() {
            parent.first_child = Some(index);
        }
        parent.last_child = Some(index);
    }
    Ok(index)
}

fn parse_start_tag(
    input: &str,
    span: XmlByteSpan,
    element: &SafeXmlElement,
    empty: bool,
) -> Result<ParsedStartTag, PreservingXmlError> {
    let bytes = input.as_bytes();
    if span.len() < 3
        || bytes.get(span.start()) != Some(&b'<')
        || bytes.get(span.end() - 1) != Some(&b'>')
    {
        return Err(PreservingXmlError::TokenMismatch);
    }
    let close = if empty {
        let slash = span
            .end()
            .checked_sub(2)
            .ok_or(PreservingXmlError::InvalidSpan)?;
        if bytes.get(slash) != Some(&b'/') {
            return Err(PreservingXmlError::TokenMismatch);
        }
        slash
    } else {
        span.end() - 1
    };
    let name_start = span.start() + 1;
    let mut cursor = name_start;
    while cursor < close && !is_name_delimiter(bytes[cursor]) {
        cursor += 1;
    }
    if cursor == name_start || input.get(name_start..cursor) != Some(&element.qualified_name) {
        return Err(PreservingXmlError::TokenMismatch);
    }
    let name_span = XmlByteSpan::checked(input, name_start, cursor)?;
    let mut attributes = Vec::new();
    attributes
        .try_reserve_exact(element.ordered_attribute_names.len())
        .map_err(|_| PreservingXmlError::AllocationFailed)?;

    for expected in &element.ordered_attribute_names {
        skip_xml_whitespace(bytes, &mut cursor, close);
        if cursor >= close {
            return Err(PreservingXmlError::TokenMismatch);
        }
        let attribute_start = cursor;
        while cursor < close && !is_attribute_name_delimiter(bytes[cursor]) {
            cursor += 1;
        }
        if cursor == attribute_start
            || input.get(attribute_start..cursor) != Some(&expected.qualified_name)
        {
            return Err(PreservingXmlError::TokenMismatch);
        }
        let attribute_name_span = XmlByteSpan::checked(input, attribute_start, cursor)?;
        skip_xml_whitespace(bytes, &mut cursor, close);
        if bytes.get(cursor) != Some(&b'=') {
            return Err(PreservingXmlError::TokenMismatch);
        }
        cursor += 1;
        skip_xml_whitespace(bytes, &mut cursor, close);
        let quote = match bytes.get(cursor) {
            Some(b'\'') => XmlQuoteStyle::Single,
            Some(b'"') => XmlQuoteStyle::Double,
            _ => return Err(PreservingXmlError::TokenMismatch),
        };
        let quote_byte = bytes[cursor];
        cursor += 1;
        let value_start = cursor;
        while cursor < close && bytes[cursor] != quote_byte {
            cursor += 1;
        }
        if cursor >= close {
            return Err(PreservingXmlError::TokenMismatch);
        }
        let value_span = XmlByteSpan::checked(input, value_start, cursor)?;
        cursor += 1;
        let attribute_span = XmlByteSpan::checked(input, attribute_start, cursor)?;
        attributes.push(attribute_token(
            expected,
            attribute_span,
            attribute_name_span,
            value_span,
            quote,
            element
                .attributes
                .get(&expected.qualified_name)
                .ok_or(PreservingXmlError::TokenMismatch)?,
        ));
    }
    skip_xml_whitespace(bytes, &mut cursor, close);
    if cursor != close {
        return Err(PreservingXmlError::TokenMismatch);
    }
    Ok(ParsedStartTag {
        tag_span: span,
        name_span,
        attributes,
        content_anchor: close,
    })
}

fn attribute_token(
    attribute: &SafeXmlAttributeName,
    span: XmlByteSpan,
    name_span: XmlByteSpan,
    value_span: XmlByteSpan,
    quote: XmlQuoteStyle,
    semantic_value: &str,
) -> XmlAttributeToken {
    let namespace = if attribute.namespace_declaration {
        Some(XMLNS_NAMESPACE.to_owned())
    } else {
        attribute.namespace.clone()
    };
    XmlAttributeToken {
        name: XmlName::new(
            attribute.qualified_name.clone(),
            attribute.local_name.clone(),
            namespace,
        ),
        span,
        name_span,
        value_span,
        quote,
        namespace_declaration: attribute.namespace_declaration,
        semantic_value: semantic_value.to_owned(),
    }
}

fn parse_end_tag(
    input: &str,
    span: XmlByteSpan,
    expected_name: &str,
) -> Result<XmlByteSpan, PreservingXmlError> {
    let bytes = input.as_bytes();
    if span.len() < 4
        || bytes.get(span.start()) != Some(&b'<')
        || bytes.get(span.start() + 1) != Some(&b'/')
        || bytes.get(span.end() - 1) != Some(&b'>')
    {
        return Err(PreservingXmlError::TokenMismatch);
    }
    let name_start = span.start() + 2;
    let mut cursor = name_start;
    let close = span.end() - 1;
    while cursor < close && !is_name_delimiter(bytes[cursor]) {
        cursor += 1;
    }
    if cursor == name_start || input.get(name_start..cursor) != Some(expected_name) {
        return Err(PreservingXmlError::TokenMismatch);
    }
    let name_span = XmlByteSpan::checked(input, name_start, cursor)?;
    skip_xml_whitespace(bytes, &mut cursor, close);
    if cursor != close {
        return Err(PreservingXmlError::TokenMismatch);
    }
    Ok(name_span)
}

fn skip_xml_whitespace(bytes: &[u8], cursor: &mut usize, end: usize) {
    while *cursor < end && matches!(bytes[*cursor], b' ' | b'\t' | b'\r' | b'\n') {
        *cursor += 1;
    }
}

fn is_name_delimiter(byte: u8) -> bool {
    matches!(byte, b' ' | b'\t' | b'\r' | b'\n' | b'/' | b'>')
}

fn is_attribute_name_delimiter(byte: u8) -> bool {
    matches!(byte, b' ' | b'\t' | b'\r' | b'\n' | b'=')
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum PreservingXmlError {
    #[error("safe XML validation failed")]
    Safe(#[source] SafeXmlError),
    #[error("preserving XML byte span is invalid")]
    InvalidSpan,
    #[error("preserving XML token stream does not align with the source")]
    TokenMismatch,
    #[error("preserving XML tree index is invalid")]
    TreeInvalid,
    #[error("preserving XML allocation failed")]
    AllocationFailed,
    #[error("untouched XML reconstruction is not byte-exact")]
    UntouchedMismatch,
}

impl PreservingXmlError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::Safe(error) => error.code(),
            Self::InvalidSpan => "preserving_xml_invalid_span",
            Self::TokenMismatch => "preserving_xml_token_mismatch",
            Self::TreeInvalid => "preserving_xml_tree_invalid",
            Self::AllocationFailed => "preserving_xml_allocation_failed",
            Self::UntouchedMismatch => "preserving_xml_untouched_mismatch",
        }
    }
}

impl From<SafeXmlError> for PreservingXmlError {
    fn from(error: SafeXmlError) -> Self {
        Self::Safe(error)
    }
}

#[cfg(test)]
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod actual_roundtrip_inputs;

#[cfg(test)]
mod tests {
    use sha2::{Digest as _, Sha256};

    use super::{
        PreservingXmlDocument, PreservingXmlError, XMLNS_NAMESPACE, XmlByteSpan, XmlQuoteStyle,
        XmlTokenKind,
    };
    use crate::safe_xml::{SafeXmlLimitConfig, SafeXmlLimits};

    fn allocating_round_trip_oracle(
        document: &PreservingXmlDocument,
    ) -> Result<(), PreservingXmlError> {
        let serialized = document.serialize_untouched()?;
        if serialized.as_slice() != document.original.as_ref()
            || <[u8; 32]>::from(Sha256::digest(&serialized)) != document.original_sha256
        {
            return Err(PreservingXmlError::UntouchedMismatch);
        }
        Ok(())
    }

    #[test]
    fn streaming_round_trip_matches_allocating_oracle_for_all36_sources()
    -> Result<(), Box<dyn std::error::Error>> {
        use crate::document_import::{ImportedSourcePackage, SourceImportLimits};
        use domain_ir::DocumentId;
        let mut packages = 0;
        let mut xml_parts = 0;
        for bytes in super::actual_roundtrip_inputs::actual_corpus()? {
            let source = ImportedSourcePackage::import(
                &bytes,
                DocumentId::parse("streaming-xml-roundtrip-corpus")?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
            )?;
            let mut checked_parts = 0;
            for part in source.parts() {
                if let Some(xml) = part.xml() {
                    assert_eq!(allocating_round_trip_oracle(xml), Ok(()));
                    assert_eq!(
                        xml.verify_untouched_round_trip(),
                        allocating_round_trip_oracle(xml)
                    );
                    checked_parts += 1;
                }
            }
            assert_eq!(checked_parts, source.receipt().xml_parts);
            assert!(checked_parts > 0);
            xml_parts += checked_parts;
            source.verify_source(&bytes)?;
            packages += 1;
        }
        assert_eq!(packages, 36);
        assert!(xml_parts >= packages);
        Ok(())
    }

    #[test]
    fn streaming_round_trip_rejects_token_omission_duplication_reordering_and_gaps()
    -> Result<(), PreservingXmlError> {
        for case in 0..6 {
            let mut document = PreservingXmlDocument::parse(b"<root><a/>text<b/></root>")?;
            match case {
                0 => {
                    document.tokens.remove(0);
                }
                1 => {
                    document.tokens.pop();
                }
                2 => {
                    document.tokens.insert(1, document.tokens[1].clone());
                }
                3 => {
                    document.tokens.swap(1, 2);
                }
                4 => {
                    document.tokens[2].span.start += 1;
                }
                _ => {
                    document.tokens.clear();
                }
            }
            assert_eq!(
                allocating_round_trip_oracle(&document),
                Err(PreservingXmlError::UntouchedMismatch)
            );
            assert_eq!(
                document.verify_untouched_round_trip(),
                allocating_round_trip_oracle(&document)
            );
        }
        Ok(())
    }

    #[test]
    fn streaming_round_trip_preserves_invalid_span_precedence_after_byte_mismatch()
    -> Result<(), PreservingXmlError> {
        for span in [
            XmlByteSpan { start: 1, end: 0 },
            XmlByteSpan {
                start: 0,
                end: usize::MAX,
            },
        ] {
            let mut document = PreservingXmlDocument::parse(b"<root><a/></root>")?;
            document.tokens.remove(0);
            let last = document.tokens.len() - 1;
            document.tokens[last].span = span;
            assert_eq!(
                allocating_round_trip_oracle(&document),
                Err(PreservingXmlError::InvalidSpan)
            );
            assert_eq!(
                document.verify_untouched_round_trip(),
                allocating_round_trip_oracle(&document)
            );
        }
        Ok(())
    }

    #[test]
    fn streaming_round_trip_checks_digest_when_all_token_bytes_still_equal()
    -> Result<(), PreservingXmlError> {
        let mut document = PreservingXmlDocument::parse(b"<root>a</root>")?;
        document.original_sha256[0] ^= 1;
        assert_eq!(
            document.verify_untouched_round_trip(),
            allocating_round_trip_oracle(&document)
        );
        assert_eq!(
            document.verify_untouched_round_trip(),
            Err(PreservingXmlError::UntouchedMismatch)
        );
        let mut document = PreservingXmlDocument::parse(b"<root>a</root>")?;
        document.original[6] = b'b';
        assert_eq!(
            document.verify_untouched_round_trip(),
            allocating_round_trip_oracle(&document)
        );
        assert_eq!(
            document.verify_untouched_round_trip(),
            Err(PreservingXmlError::UntouchedMismatch)
        );
        Ok(())
    }

    #[test]
    fn streaming_round_trip_keeps_equal_bytes_from_different_span_positions()
    -> Result<(), PreservingXmlError> {
        let mut document = PreservingXmlDocument::parse(b"<root><a/><a/></root>")?;
        document.tokens[2].span = document.tokens[1].span;
        assert_eq!(allocating_round_trip_oracle(&document), Ok(()));
        assert_eq!(
            document.verify_untouched_round_trip(),
            allocating_round_trip_oracle(&document)
        );
        Ok(())
    }

    #[test]
    fn streaming_round_trip_preserves_large_unicode_references_bom_and_comments()
    -> Result<(), PreservingXmlError> {
        let xml = format!(
            "\u{feff}<!--before-->\r\n<root a='1'>{}<!--after--></root>\n",
            "한글&amp;".repeat(4096)
        );
        assert!(xml.len() > 32 * 1024);
        let document = PreservingXmlDocument::parse(xml.as_bytes())?;
        assert_eq!(allocating_round_trip_oracle(&document), Ok(()));
        assert_eq!(
            document.verify_untouched_round_trip(),
            allocating_round_trip_oracle(&document)
        );
        Ok(())
    }

    #[test]
    fn preserves_every_accepted_token_byte_and_digest() {
        let xml = concat!(
            "<?xml version=\"1.0\" encoding='UTF-8'?>\r\n",
            "<!--before--><p:root xmlns:p='urn:one' a = '1' p:b=\"&quot;\" secret='TOPSECRET'>\n",
            "  <p:item p:id='7'/>text &amp; 한글<!--inside-->\r\n",
            "</p:root>\n"
        )
        .as_bytes();
        let document = PreservingXmlDocument::parse(xml)
            .unwrap_or_else(|error| panic!("preserving parse failed: {error}"));
        document
            .verify_untouched_round_trip()
            .unwrap_or_else(|error| panic!("untouched verification failed: {error}"));
        let serialized = document
            .serialize_untouched()
            .unwrap_or_else(|error| panic!("serialization failed: {error}"));

        assert_eq!(serialized, xml);
        assert_eq!(document.original_len(), xml.len());
        assert_eq!(
            document.original_sha256(),
            <[u8; 32]>::from(Sha256::digest(xml))
        );
        assert_eq!(
            document.tokens().first().map(|token| token.span().start()),
            Some(0)
        );
        assert_eq!(
            document.tokens().last().map(|token| token.span().end()),
            Some(xml.len())
        );
        assert!(
            document
                .tokens()
                .windows(2)
                .all(|pair| pair[0].span().end() == pair[1].span().start())
        );
        assert!(
            document
                .tokens()
                .iter()
                .any(|token| token.kind() == XmlTokenKind::Reference)
        );
        assert!(
            document
                .tokens()
                .iter()
                .any(|token| token.kind() == XmlTokenKind::Comment)
        );
        assert!(
            document
                .tokens()
                .iter()
                .any(|token| token.kind() == XmlTokenKind::Whitespace)
        );

        let root = &document.elements()[document.root_element()];
        assert_eq!(root.name().namespace(), Some("urn:one"));
        assert_eq!(root.attributes()[1].quote_style(), XmlQuoteStyle::Single);
        assert_eq!(root.attributes()[2].quote_style(), XmlQuoteStyle::Double);
        let debug = format!("{document:?}");
        assert!(!debug.contains("before"));
        assert!(!debug.contains("한글"));
        assert!(!debug.contains("&quot;"));
        let element_debug = format!("{:?}", document.elements());
        assert!(!element_debug.contains("TOPSECRET"));
    }

    #[test]
    fn preserves_utf8_bom_as_an_explicit_non_markup_token() {
        let xml = b"\xEF\xBB\xBF<root/>";
        let document = PreservingXmlDocument::parse(xml)
            .unwrap_or_else(|error| panic!("BOM parse failed: {error}"));

        assert_eq!(document.tokens()[0].kind(), XmlTokenKind::ByteOrderMark);
        assert_eq!(
            document.tokens()[0].span(),
            XmlByteSpan { start: 0, end: 3 }
        );
        assert_eq!(
            document.elements()[0].start_tag_span(),
            XmlByteSpan { start: 3, end: 10 }
        );
        document
            .verify_untouched_round_trip()
            .unwrap_or_else(|error| panic!("BOM round trip failed: {error}"));
    }

    #[test]
    fn resolves_rebound_element_and_attribute_namespaces() {
        let xml = br#"<p:root xmlns:p="urn:one" p:a='x' plain="z" xml:lang='ko'><p:child xmlns:p='urn:two' p:a="y"/></p:root>"#;
        let document = PreservingXmlDocument::parse(xml)
            .unwrap_or_else(|error| panic!("namespace parse failed: {error}"));
        let root = &document.elements()[0];
        let child = &document.elements()[1];

        assert_eq!(root.name().prefix(), Some("p"));
        assert_eq!(root.name().namespace(), Some("urn:one"));
        assert_eq!(child.name().namespace(), Some("urn:two"));
        assert_eq!(
            root.attributes()[0].name().namespace(),
            Some(XMLNS_NAMESPACE)
        );
        assert!(root.attributes()[0].is_namespace_declaration());
        assert_eq!(root.attributes()[1].name().namespace(), Some("urn:one"));
        assert_eq!(root.attributes()[2].name().namespace(), None);
        assert_eq!(
            root.attributes()[3].name().namespace(),
            Some("http://www.w3.org/XML/1998/namespace")
        );
        assert_eq!(child.attributes()[1].name().namespace(), Some("urn:two"));
        document
            .verify_untouched_round_trip()
            .unwrap_or_else(|error| panic!("untouched verification failed: {error}"));
    }

    #[test]
    fn builds_parent_child_sibling_and_matching_tag_index() {
        let xml = br"<root><a/><b><c/></b><d/></root>";
        let document = PreservingXmlDocument::parse(xml)
            .unwrap_or_else(|error| panic!("tree parse failed: {error}"));
        let elements = document.elements();

        assert_eq!(document.root_element(), 0);
        assert_eq!(elements[0].first_child(), Some(1));
        assert_eq!(elements[0].last_child(), Some(4));
        assert_eq!(elements[1].next_sibling(), Some(2));
        assert_eq!(elements[2].previous_sibling(), Some(1));
        assert_eq!(elements[2].next_sibling(), Some(4));
        assert_eq!(elements[4].previous_sibling(), Some(2));
        assert_eq!(elements[2].first_child(), Some(3));
        assert_eq!(elements[3].parent(), Some(2));
        assert!(elements[1].is_empty());
        assert_eq!(elements[0].start_token(), 0);
        assert_eq!(elements[0].end_token(), Some(document.tokens().len() - 1));
        assert_eq!(
            elements[0].outer_span(),
            Some(XmlByteSpan {
                start: 0,
                end: xml.len()
            })
        );
    }

    #[test]
    fn inherits_safe_xml_fail_closed_policy_and_codes() {
        let cases: &[(&[u8], &str)] = &[
            (br"<!DOCTYPE root><root/>", "safe_xml_dtd_forbidden"),
            (
                br"<root>&custom;</root>",
                "safe_xml_custom_entity_forbidden",
            ),
            (br"<?target value?><root/>", "safe_xml_pi_forbidden"),
            (br"<root><![CDATA[x]]></root>", "safe_xml_cdata_forbidden"),
            (br"<p:root/>", "safe_xml_namespace_invalid"),
            (br"<root><a></root>", "safe_xml_malformed"),
            (b"<root>\xff</root>", "safe_xml_encoding_forbidden"),
        ];
        for (xml, expected_code) in cases {
            let Err(error) = PreservingXmlDocument::parse(xml) else {
                panic!("unsafe or malformed XML unexpectedly parsed");
            };
            assert_eq!(error.code(), *expected_code);
        }
    }

    #[test]
    fn preserving_parser_keeps_finite_safe_reader_limits() {
        let config = SafeXmlLimitConfig {
            events: 1,
            ..SafeXmlLimitConfig::default()
        };
        let limits = SafeXmlLimits::new(config)
            .unwrap_or_else(|error| panic!("valid limits rejected: {error}"));
        let Err(error) = PreservingXmlDocument::parse_with_limits(br"<root/>", limits) else {
            panic!("event limit unexpectedly accepted");
        };
        assert_eq!(error.code(), "safe_xml_event_limit");

        let Err(malformed) = PreservingXmlDocument::parse(br"<root a='1' trailing/>") else {
            panic!("malformed attribute unexpectedly accepted");
        };
        assert_eq!(malformed.code(), "safe_xml_malformed");
    }

    #[test]
    fn checked_spans_reject_bounds_order_and_utf8_splits() {
        let input = "가나다";
        assert_eq!(
            XmlByteSpan::checked(input, 0, input.len()),
            Ok(XmlByteSpan {
                start: 0,
                end: input.len()
            })
        );
        assert_eq!(
            XmlByteSpan::checked(input, 1, 2),
            Err(PreservingXmlError::InvalidSpan)
        );
        assert_eq!(
            XmlByteSpan::checked(input, 4, 3),
            Err(PreservingXmlError::InvalidSpan)
        );
        assert_eq!(
            XmlByteSpan::checked(input, 0, usize::MAX),
            Err(PreservingXmlError::InvalidSpan)
        );
    }
}
