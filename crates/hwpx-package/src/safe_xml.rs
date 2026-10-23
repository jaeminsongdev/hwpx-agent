use std::collections::{BTreeMap, BTreeSet};

use quick_xml::escape::EscapeError;
use quick_xml::events::{BytesDecl, BytesStart, Event};
use quick_xml::name::{NamespaceError, NamespaceResolver, ResolveResult};
use quick_xml::reader::NsReader;
use quick_xml::{Error as QuickXmlError, XmlVersion};
use thiserror::Error;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct SafeXmlLimitConfig {
    pub input_bytes: usize,
    pub events: usize,
    pub nodes: usize,
    pub depth: usize,
    pub text_bytes: usize,
    pub total_text_bytes: usize,
    pub attributes_per_element: usize,
    pub attribute_bytes: usize,
    pub namespace_bindings: usize,
}

impl Default for SafeXmlLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 2 * 1024 * 1024,
            events: 100_000,
            nodes: 100_000,
            depth: 64,
            text_bytes: 1024 * 1024,
            total_text_bytes: 2 * 1024 * 1024,
            attributes_per_element: 32,
            attribute_bytes: 8 * 1024,
            namespace_bindings: 2_048,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub(crate) struct SafeXmlLimits(SafeXmlLimitConfig);

impl SafeXmlLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_EVENTS: usize = 1_000_000;
    pub const HARD_MAX_NODES: usize = 1_000_000;
    pub const HARD_MAX_DEPTH: usize = 256;
    pub const HARD_MAX_TEXT_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_TOTAL_TEXT_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_ATTRIBUTES_PER_ELEMENT: usize = 256;
    pub const HARD_MAX_ATTRIBUTE_BYTES: usize = 64 * 1024;
    pub const HARD_MAX_NAMESPACE_BINDINGS: usize = 4_096;

    pub fn new(config: SafeXmlLimitConfig) -> Result<Self, SafeXmlError> {
        let values = [
            (
                "input_bytes",
                config.input_bytes,
                Self::HARD_MAX_INPUT_BYTES,
            ),
            ("events", config.events, Self::HARD_MAX_EVENTS),
            ("nodes", config.nodes, Self::HARD_MAX_NODES),
            ("depth", config.depth, Self::HARD_MAX_DEPTH),
            ("text_bytes", config.text_bytes, Self::HARD_MAX_TEXT_BYTES),
            (
                "total_text_bytes",
                config.total_text_bytes,
                Self::HARD_MAX_TOTAL_TEXT_BYTES,
            ),
            (
                "attributes",
                config.attributes_per_element,
                Self::HARD_MAX_ATTRIBUTES_PER_ELEMENT,
            ),
            (
                "attribute_bytes",
                config.attribute_bytes,
                Self::HARD_MAX_ATTRIBUTE_BYTES,
            ),
            (
                "namespace_bindings",
                config.namespace_bindings,
                Self::HARD_MAX_NAMESPACE_BINDINGS,
            ),
        ];
        for (limit, value, ceiling) in values {
            if value == 0 || value > ceiling {
                return Err(SafeXmlError::InvalidLimit {
                    limit,
                    value,
                    ceiling,
                });
            }
        }
        if config.text_bytes > config.total_text_bytes
            || config.total_text_bytes > config.input_bytes
        {
            return Err(SafeXmlError::InvalidLimitRelation);
        }
        Ok(Self(config))
    }

    pub const fn config(self) -> SafeXmlLimitConfig {
        self.0
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct SafeXmlAttributeName {
    pub qualified_name: String,
    pub local_name: String,
    pub namespace: Option<String>,
    pub namespace_declaration: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct SafeXmlSpan {
    pub start: usize,
    pub end: usize,
}

impl SafeXmlSpan {
    fn from_reader_positions(start: u64, end: u64, input_len: usize) -> Result<Self, SafeXmlError> {
        let start = usize::try_from(start).map_err(|_| SafeXmlError::Malformed)?;
        let end = usize::try_from(end).map_err(|_| SafeXmlError::Malformed)?;
        if start > end || end > input_len {
            return Err(SafeXmlError::Malformed);
        }
        Ok(Self { start, end })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct SafeXmlElement {
    pub qualified_name: String,
    pub local_name: String,
    pub namespace: Option<String>,
    pub attributes: BTreeMap<String, String>,
    pub ordered_attribute_names: Vec<SafeXmlAttributeName>,
    pub depth: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum SafeXmlEvent {
    Declaration,
    Start(SafeXmlElement),
    Empty(SafeXmlElement),
    End,
    Text { bytes: usize },
    Reference,
    Comment,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct SafeXmlDocument {
    pub events: Vec<SafeXmlEvent>,
    pub spans: Vec<SafeXmlSpan>,
}

impl SafeXmlDocument {
    pub fn parse(bytes: &[u8], limits: SafeXmlLimits) -> Result<Self, SafeXmlError> {
        // A reservation hint, not an admission limit. Long text/attributes can
        // have very few events; never reserve the byte-derived event ceiling
        // up front. Original checked growth and every parser guard remain.
        Self::parse_with_capacity_hint(bytes, limits, 256)
    }

    fn parse_with_capacity_hint(
        bytes: &[u8],
        limits: SafeXmlLimits,
        capacity_hint: usize,
    ) -> Result<Self, SafeXmlError> {
        if bytes.len() > limits.config().input_bytes {
            return Err(SafeXmlError::InputLimit);
        }
        std::str::from_utf8(bytes).map_err(|_| SafeXmlError::EncodingForbidden)?;
        let source_offset = u64::from(bytes.starts_with(&[0xEF, 0xBB, 0xBF])) * 3;
        let mut reader = NsReader::from_reader(bytes);
        reader.config_mut().enable_all_checks(true);
        reader
            .resolver_mut()
            .set_max_namespace_bindings(limits.config().namespace_bindings);
        let initial_capacity = limits
            .config()
            .events
            .min(bytes.len().saturating_div(2).saturating_add(1))
            .min(capacity_hint);
        let mut output = SafeXmlOutput::new(initial_capacity)?;
        let mut state = ParseState::default();
        loop {
            let event_start = reader.buffer_position();
            let event = reader
                .read_event()
                .map_err(|error| map_quick_xml_error(&error))?;
            let span = SafeXmlSpan::from_reader_positions(
                event_start
                    .checked_add(source_offset)
                    .ok_or(SafeXmlError::Malformed)?,
                reader
                    .buffer_position()
                    .checked_add(source_offset)
                    .ok_or(SafeXmlError::Malformed)?,
                bytes.len(),
            )?;
            let (namespace, event) = reader.resolver().resolve_event(event);
            if process_safe_event(
                event,
                &namespace,
                reader.resolver(),
                span,
                &mut state,
                &mut output,
                limits,
            )? {
                break;
            }
        }
        if state.depth != 0 || state.root_count != 1 {
            return Err(SafeXmlError::Malformed);
        }
        Ok(output.finish())
    }
}

struct SafeXmlOutput {
    events: Vec<SafeXmlEvent>,
    spans: Vec<SafeXmlSpan>,
}

impl SafeXmlOutput {
    fn new(capacity: usize) -> Result<Self, SafeXmlError> {
        let mut events = Vec::new();
        events
            .try_reserve_exact(capacity)
            .map_err(|_| SafeXmlError::AllocationFailed)?;
        let mut spans = Vec::new();
        spans
            .try_reserve_exact(capacity)
            .map_err(|_| SafeXmlError::AllocationFailed)?;
        Ok(Self { events, spans })
    }

    fn push(&mut self, event: SafeXmlEvent, span: SafeXmlSpan) -> Result<(), SafeXmlError> {
        self.events
            .try_reserve(1)
            .map_err(|_| SafeXmlError::AllocationFailed)?;
        self.spans
            .try_reserve(1)
            .map_err(|_| SafeXmlError::AllocationFailed)?;
        self.events.push(event);
        self.spans.push(span);
        Ok(())
    }

    fn finish(self) -> SafeXmlDocument {
        SafeXmlDocument {
            events: self.events,
            spans: self.spans,
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn process_safe_event(
    event: Event<'_>,
    namespace: &ResolveResult<'_>,
    resolver: &NamespaceResolver,
    span: SafeXmlSpan,
    state: &mut ParseState,
    output: &mut SafeXmlOutput,
    limits: SafeXmlLimits,
) -> Result<bool, SafeXmlError> {
    state.count_event(limits)?;
    match event {
        Event::Start(element) => {
            let next_depth = state.next_depth(limits)?;
            state.begin_root_if_needed()?;
            state.count_node(limits)?;
            let element = safe_element(&element, namespace, resolver, next_depth, limits)?;
            output.push(SafeXmlEvent::Start(element), span)?;
            state.depth = next_depth;
        }
        Event::Empty(element) => {
            let element_depth = state.next_depth(limits)?;
            state.begin_root_if_needed()?;
            state.count_node(limits)?;
            let element = safe_element(&element, namespace, resolver, element_depth, limits)?;
            output.push(SafeXmlEvent::Empty(element), span)?;
        }
        Event::End(_) => {
            resolved_namespace(namespace)?;
            state.depth = state.depth.checked_sub(1).ok_or(SafeXmlError::Malformed)?;
            output.push(SafeXmlEvent::End, span)?;
        }
        Event::Text(text) => {
            let length = text.as_ref().len();
            if state.depth == 0 && !is_xml_whitespace(text.as_ref().as_bytes()) {
                return Err(SafeXmlError::Malformed);
            }
            state.count_text(length, limits)?;
            state.count_node(limits)?;
            output.push(SafeXmlEvent::Text { bytes: length }, span)?;
        }
        Event::GeneralRef(reference) => {
            if state.depth == 0 || !is_safe_xml_reference(reference.as_ref()) {
                return Err(SafeXmlError::CustomEntityForbidden);
            }
            state.count_text(1, limits)?;
            state.count_node(limits)?;
            output.push(SafeXmlEvent::Reference, span)?;
        }
        Event::Comment(_) => {
            state.count_node(limits)?;
            output.push(SafeXmlEvent::Comment, span)?;
        }
        Event::Decl(declaration) => {
            if state.events != 1
                || state.declaration_seen
                || state.root_count != 0
                || state.depth != 0
            {
                return Err(SafeXmlError::Malformed);
            }
            validate_declaration(&declaration)?;
            state.declaration_seen = true;
            output.push(SafeXmlEvent::Declaration, span)?;
        }
        Event::DocType(_) => return Err(SafeXmlError::DtdForbidden),
        Event::PI(_) => return Err(SafeXmlError::ProcessingInstructionForbidden),
        Event::CData(_) => return Err(SafeXmlError::CdataForbidden),
        Event::Eof => return Ok(true),
    }
    Ok(false)
}

#[derive(Debug, Default)]
struct ParseState {
    depth: usize,
    events: usize,
    nodes: usize,
    total_text_bytes: usize,
    root_count: usize,
    declaration_seen: bool,
}

impl ParseState {
    fn count_event(&mut self, limits: SafeXmlLimits) -> Result<(), SafeXmlError> {
        self.events = self.events.checked_add(1).ok_or(SafeXmlError::EventLimit)?;
        if self.events > limits.config().events {
            return Err(SafeXmlError::EventLimit);
        }
        Ok(())
    }

    fn count_node(&mut self, limits: SafeXmlLimits) -> Result<(), SafeXmlError> {
        self.nodes = self.nodes.checked_add(1).ok_or(SafeXmlError::NodeLimit)?;
        if self.nodes > limits.config().nodes {
            return Err(SafeXmlError::NodeLimit);
        }
        Ok(())
    }

    fn count_text(&mut self, length: usize, limits: SafeXmlLimits) -> Result<(), SafeXmlError> {
        if length > limits.config().text_bytes {
            return Err(SafeXmlError::TextLimit);
        }
        self.total_text_bytes = self
            .total_text_bytes
            .checked_add(length)
            .ok_or(SafeXmlError::TextLimit)?;
        if self.total_text_bytes > limits.config().total_text_bytes {
            return Err(SafeXmlError::TextLimit);
        }
        Ok(())
    }

    fn next_depth(&self, limits: SafeXmlLimits) -> Result<usize, SafeXmlError> {
        let depth = self.depth.checked_add(1).ok_or(SafeXmlError::DepthLimit)?;
        if depth > limits.config().depth {
            return Err(SafeXmlError::DepthLimit);
        }
        Ok(depth)
    }

    fn begin_root_if_needed(&mut self) -> Result<(), SafeXmlError> {
        if self.depth == 0 {
            self.root_count = self
                .root_count
                .checked_add(1)
                .ok_or(SafeXmlError::Malformed)?;
            if self.root_count > 1 {
                return Err(SafeXmlError::Malformed);
            }
        }
        Ok(())
    }
}

fn safe_element(
    element: &BytesStart<'_>,
    namespace: &ResolveResult<'_>,
    resolver: &NamespaceResolver,
    depth: usize,
    limits: SafeXmlLimits,
) -> Result<SafeXmlElement, SafeXmlError> {
    let qualified_name = element.name().as_ref().to_owned();
    let local_name = element.local_name().as_ref().to_owned();
    let namespace = resolved_namespace(namespace)?.map(str::to_owned);
    let mut attributes = BTreeMap::new();
    let mut ordered_attribute_names = Vec::new();
    let mut expanded_attributes = BTreeSet::new();
    let mut total_attribute_bytes = 0_usize;
    for (index, attribute) in element.attributes().with_checks(true).enumerate() {
        if index >= limits.config().attributes_per_element {
            return Err(SafeXmlError::AttributeLimit);
        }
        let attribute = attribute.map_err(|_| SafeXmlError::Malformed)?;
        let key = attribute.key.as_ref().to_owned();
        let namespace_declaration = key == "xmlns" || key.starts_with("xmlns:");
        let (attribute_namespace, attribute_local_name) = if namespace_declaration {
            (
                None,
                key.strip_prefix("xmlns:").unwrap_or("xmlns").to_owned(),
            )
        } else {
            let (attribute_namespace, local_name) = resolver.resolve_attribute(attribute.key);
            let attribute_namespace = resolved_namespace(&attribute_namespace)?.map(str::to_owned);
            (attribute_namespace, local_name.as_ref().to_owned())
        };
        if !namespace_declaration {
            let expanded_name = (attribute_namespace.clone(), attribute_local_name.clone());
            if !expanded_attributes.insert(expanded_name) {
                return Err(SafeXmlError::DuplicateAttribute);
            }
        }
        ordered_attribute_names
            .try_reserve(1)
            .map_err(|_| SafeXmlError::AllocationFailed)?;
        ordered_attribute_names.push(SafeXmlAttributeName {
            qualified_name: key.clone(),
            local_name: attribute_local_name,
            namespace: attribute_namespace,
            namespace_declaration,
        });
        let value = attribute
            .normalized_value(XmlVersion::Implicit1_0)
            .map_err(|error| map_quick_xml_error(&error))?
            .into_owned();
        total_attribute_bytes = total_attribute_bytes
            .checked_add(key.len())
            .and_then(|total| total.checked_add(value.len()))
            .ok_or(SafeXmlError::AttributeBytesLimit)?;
        if total_attribute_bytes > limits.config().attribute_bytes {
            return Err(SafeXmlError::AttributeBytesLimit);
        }
        if attributes.insert(key, value).is_some() {
            return Err(SafeXmlError::DuplicateAttribute);
        }
    }
    Ok(SafeXmlElement {
        qualified_name,
        local_name,
        namespace,
        attributes,
        ordered_attribute_names,
        depth,
    })
}

fn resolved_namespace<'a>(
    namespace: &'a ResolveResult<'a>,
) -> Result<Option<&'a str>, SafeXmlError> {
    match namespace {
        ResolveResult::Unbound => Ok(None),
        ResolveResult::Bound(namespace) => Ok(Some(namespace.as_ref())),
        ResolveResult::Unknown(_) => Err(SafeXmlError::NamespaceInvalid),
    }
}

fn validate_declaration(declaration: &BytesDecl<'_>) -> Result<(), SafeXmlError> {
    let mut keys = BTreeSet::new();
    let mut declaration_order = 0_u8;
    let declaration_start = BytesStart::from_content(declaration.as_ref(), 3);
    for attribute in declaration_start.attributes().with_checks(true) {
        let attribute = attribute.map_err(|_| SafeXmlError::Malformed)?;
        let key = attribute.key.as_ref();
        if !matches!(key, "version" | "encoding" | "standalone") || !keys.insert(key.to_owned()) {
            return Err(SafeXmlError::Malformed);
        }
        declaration_order = match (declaration_order, key) {
            (0, "version") => 1,
            (1, "encoding") => 2,
            (1 | 2, "standalone") => 3,
            _ => return Err(SafeXmlError::Malformed),
        };
    }
    if declaration
        .version()
        .map_err(|_| SafeXmlError::Malformed)?
        .as_ref()
        != "1.0"
    {
        return Err(SafeXmlError::EncodingForbidden);
    }
    if declaration
        .encoding()
        .transpose()
        .map_err(|_| SafeXmlError::Malformed)?
        .is_some_and(|encoding| !encoding.eq_ignore_ascii_case("utf-8"))
    {
        return Err(SafeXmlError::EncodingForbidden);
    }
    if declaration
        .standalone()
        .transpose()
        .map_err(|_| SafeXmlError::Malformed)?
        .is_some_and(|standalone| !matches!(standalone.as_ref(), "yes" | "no"))
    {
        return Err(SafeXmlError::Malformed);
    }
    Ok(())
}

fn is_safe_xml_reference(reference: &str) -> bool {
    if matches!(reference, "amp" | "lt" | "gt" | "apos" | "quot") {
        return true;
    }
    let value = reference
        .strip_prefix("#x")
        .or_else(|| reference.strip_prefix("#X"))
        .and_then(|digits| u32::from_str_radix(digits, 16).ok())
        .or_else(|| {
            reference
                .strip_prefix('#')
                .and_then(|digits| digits.parse::<u32>().ok())
        });
    value.is_some_and(is_xml_character)
}

fn is_xml_character(value: u32) -> bool {
    matches!(value, 0x09 | 0x0A | 0x0D | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x1_0000..=0x10_FFFF)
}

fn is_xml_whitespace(bytes: &[u8]) -> bool {
    bytes
        .iter()
        .all(|byte| matches!(byte, b' ' | b'\t' | b'\r' | b'\n'))
}

fn map_quick_xml_error(error: &QuickXmlError) -> SafeXmlError {
    match error {
        QuickXmlError::Encoding(_) => SafeXmlError::EncodingForbidden,
        QuickXmlError::Escape(
            EscapeError::UnrecognizedEntity(_, _) | EscapeError::TooManyNestedEntities,
        ) => SafeXmlError::CustomEntityForbidden,
        QuickXmlError::Namespace(
            NamespaceError::TooManyBindings(_) | NamespaceError::TooDeeplyNested(_),
        ) => SafeXmlError::NamespaceLimit,
        QuickXmlError::Namespace(_) => SafeXmlError::NamespaceInvalid,
        _ => SafeXmlError::Malformed,
    }
}

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum SafeXmlError {
    #[error("invalid finite safe XML limit for {limit}: {value} (ceiling {ceiling})")]
    InvalidLimit {
        limit: &'static str,
        value: usize,
        ceiling: usize,
    },
    #[error("safe XML text limits have an invalid relation")]
    InvalidLimitRelation,
    #[error("safe XML input exceeds its byte limit")]
    InputLimit,
    #[error("safe XML event limit exceeded")]
    EventLimit,
    #[error("safe XML node limit exceeded")]
    NodeLimit,
    #[error("safe XML depth limit exceeded")]
    DepthLimit,
    #[error("safe XML text limit exceeded")]
    TextLimit,
    #[error("safe XML attribute count limit exceeded")]
    AttributeLimit,
    #[error("safe XML attribute byte limit exceeded")]
    AttributeBytesLimit,
    #[error("safe XML namespace binding limit exceeded")]
    NamespaceLimit,
    #[error("safe XML namespace is invalid")]
    NamespaceInvalid,
    #[error("safe XML duplicate attribute")]
    DuplicateAttribute,
    #[error("safe XML is malformed")]
    Malformed,
    #[error("safe XML encoding or version is forbidden")]
    EncodingForbidden,
    #[error("safe XML DTD is forbidden")]
    DtdForbidden,
    #[error("safe XML custom entity is forbidden")]
    CustomEntityForbidden,
    #[error("safe XML processing instruction is forbidden")]
    ProcessingInstructionForbidden,
    #[error("safe XML CDATA is forbidden")]
    CdataForbidden,
    #[error("safe XML allocation failed")]
    AllocationFailed,
}

impl SafeXmlError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit { .. } => "safe_xml_invalid_limit",
            Self::InvalidLimitRelation => "safe_xml_invalid_limit_relation",
            Self::InputLimit => "safe_xml_input_limit",
            Self::EventLimit => "safe_xml_event_limit",
            Self::NodeLimit => "safe_xml_node_limit",
            Self::DepthLimit => "safe_xml_depth_limit",
            Self::TextLimit => "safe_xml_text_limit",
            Self::AttributeLimit => "safe_xml_attribute_limit",
            Self::AttributeBytesLimit => "safe_xml_attribute_bytes_limit",
            Self::NamespaceLimit => "safe_xml_namespace_limit",
            Self::NamespaceInvalid => "safe_xml_namespace_invalid",
            Self::DuplicateAttribute => "safe_xml_duplicate_attribute",
            Self::Malformed => "safe_xml_malformed",
            Self::EncodingForbidden => "safe_xml_encoding_forbidden",
            Self::DtdForbidden => "safe_xml_dtd_forbidden",
            Self::CustomEntityForbidden => "safe_xml_custom_entity_forbidden",
            Self::ProcessingInstructionForbidden => "safe_xml_pi_forbidden",
            Self::CdataForbidden => "safe_xml_cdata_forbidden",
            Self::AllocationFailed => "safe_xml_allocation_failed",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{SafeXmlDocument, SafeXmlError, SafeXmlEvent, SafeXmlLimitConfig, SafeXmlLimits};

    #[test]
    fn parses_namespace_resolved_xml10_and_safe_references() {
        let xml = br#"<?xml version="1.0" encoding="UTF-8"?><p:root xmlns:p="urn:test"><p:item>A &amp; B &#xAC00;</p:item></p:root>"#;
        let document = parse(xml).unwrap_or_else(|error| panic!("valid XML failed: {error}"));
        assert!(!document.events.is_empty());

        let rebound = br#"<p:root xmlns:p="urn:one"><p:item xmlns:p="urn:two"/></p:root>"#;
        let document = parse(rebound)
            .unwrap_or_else(|error| panic!("valid namespace rebinding failed: {error}"));
        assert!(document.events.iter().any(|event| matches!(
            event,
            SafeXmlEvent::Empty(element)
                if element.local_name == "item" && element.namespace.as_deref() == Some("urn:two")
        )));
    }

    #[test]
    fn blocks_dtd_custom_entity_pi_cdata_and_legacy_encoding() {
        let cases: &[(&[u8], &str)] = &[
            (br"<!DOCTYPE root><root/>", "safe_xml_dtd_forbidden"),
            (
                br"<root>&custom;</root>",
                "safe_xml_custom_entity_forbidden",
            ),
            (br"<?target data?><root/>", "safe_xml_pi_forbidden"),
            (br"<root><![CDATA[x]]></root>", "safe_xml_cdata_forbidden"),
            (
                br#"<?xml version="1.1"?><root/>"#,
                "safe_xml_encoding_forbidden",
            ),
            (
                br#"<?xml version="1.0" encoding="EUC-KR"?><root/>"#,
                "safe_xml_encoding_forbidden",
            ),
        ];
        for (xml, code) in cases {
            assert_code(xml, SafeXmlLimits::default(), code);
        }
    }

    #[test]
    fn rejects_malformed_namespace_attribute_and_root_shapes() {
        let cases: &[&[u8]] = &[
            br"<a><b></a>",
            br"<p:root/>",
            br#"<root a="1" a="2"/>"#,
            br#"<root xmlns:a="urn:x" xmlns:b="urn:x" a:id="1" b:id="2"/>"#,
            br#"<root p:id="1"/>"#,
            br#" <?xml version="1.0"?><root/>"#,
            br#"<!--before--><?xml version="1.0"?><root/>"#,
            br#"<?xml version="1.0" encoding="UTF-8" encoding="UTF-8"?><root/>"#,
            br#"<?xml version="1.0" standalone="yes" encoding="UTF-8"?><root/>"#,
            br"<one/><two/>",
            br"text<root/>",
            br"<root/>text",
            "<root/>\u{00A0}".as_bytes(),
        ];
        for xml in cases {
            let Err(error) = SafeXmlDocument::parse(xml, SafeXmlLimits::default()) else {
                panic!("malformed XML was accepted");
            };
            assert!(matches!(
                error,
                SafeXmlError::Malformed
                    | SafeXmlError::NamespaceInvalid
                    | SafeXmlError::DuplicateAttribute
            ));
        }
    }

    #[test]
    fn enforces_depth_event_node_text_attribute_and_namespace_limits() {
        let cases = [
            (
                SafeXmlLimitConfig {
                    input_bytes: 8,
                    text_bytes: 8,
                    total_text_bytes: 8,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root/>xx".as_slice(),
                "safe_xml_input_limit",
            ),
            (
                SafeXmlLimitConfig {
                    depth: 1,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root><child/></root>".as_slice(),
                "safe_xml_depth_limit",
            ),
            (
                SafeXmlLimitConfig {
                    events: 2,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root></root>".as_slice(),
                "safe_xml_event_limit",
            ),
            (
                SafeXmlLimitConfig {
                    nodes: 1,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root>text</root>".as_slice(),
                "safe_xml_node_limit",
            ),
            (
                SafeXmlLimitConfig {
                    text_bytes: 3,
                    total_text_bytes: 8,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root>four</root>".as_slice(),
                "safe_xml_text_limit",
            ),
            (
                SafeXmlLimitConfig {
                    text_bytes: 4,
                    total_text_bytes: 5,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root>abc<child/>def</root>".as_slice(),
                "safe_xml_text_limit",
            ),
            (
                SafeXmlLimitConfig {
                    attributes_per_element: 1,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root a=\"1\" b=\"2\"/>".as_slice(),
                "safe_xml_attribute_limit",
            ),
            (
                SafeXmlLimitConfig {
                    attribute_bytes: 4,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root long=\"value\"/>".as_slice(),
                "safe_xml_attribute_bytes_limit",
            ),
            (
                SafeXmlLimitConfig {
                    namespace_bindings: 1,
                    ..SafeXmlLimitConfig::default()
                },
                b"<root xmlns:a=\"urn:a\" xmlns:b=\"urn:b\"/>".as_slice(),
                "safe_xml_namespace_limit",
            ),
        ];
        for (config, xml, code) in cases {
            let limits = SafeXmlLimits::new(config)
                .unwrap_or_else(|error| panic!("test limit failed: {error}"));
            assert_code(xml, limits, code);
        }
    }

    #[test]
    fn finite_limit_contract_rejects_zero_overflow_and_bad_relations() {
        let zero = SafeXmlLimitConfig {
            nodes: 0,
            ..SafeXmlLimitConfig::default()
        };
        let Err(error) = SafeXmlLimits::new(zero) else {
            panic!("zero limit was accepted");
        };
        assert_eq!(error.code(), "safe_xml_invalid_limit");

        let relation = SafeXmlLimitConfig {
            input_bytes: 4,
            text_bytes: 4,
            total_text_bytes: 5,
            ..SafeXmlLimitConfig::default()
        };
        let Err(error) = SafeXmlLimits::new(relation) else {
            panic!("invalid relation was accepted");
        };
        assert_eq!(error.code(), "safe_xml_invalid_limit_relation");
    }

    fn parse(xml: &[u8]) -> Result<SafeXmlDocument, SafeXmlError> {
        SafeXmlDocument::parse(xml, SafeXmlLimits::default())
    }

    fn assert_code(xml: &[u8], limits: SafeXmlLimits, code: &str) {
        let Err(error) = SafeXmlDocument::parse(xml, limits) else {
            panic!("unsafe XML was accepted");
        };
        assert_eq!(error.code(), code);
    }
}

// P175 initial-capacity parity and sparse/dense allocation regression oracles.
#[cfg(test)]
#[path = "../tests/support/document_import_settings_inputs.rs"]
mod initial_capacity_inputs;

#[cfg(test)]
mod initial_capacity_tests {
    use super::*;
    use crate::{BoundedZipReader, PackageLimits};
    use std::{error::Error, io::Cursor};

    // usize::MAX restores exactly the original byte-derived reservation.
    // Both paths retain the entire original parser and every admission check.
    fn original(bytes: &[u8], limits: SafeXmlLimits) -> Result<SafeXmlDocument, SafeXmlError> {
        SafeXmlDocument::parse_with_capacity_hint(bytes, limits, usize::MAX)
    }

    #[test]
    fn all36_frozen_original_xml_events_spans_and_errors_equal_original_parser()
    -> Result<(), Box<dyn Error>> {
        let mut originals = 0;
        let mut parts = 0;
        for bytes in super::initial_capacity_inputs::actual_corpus()? {
            let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
            let xml_entries: Vec<_> = reader.entries().iter().filter(|entry| {
                entry.path.as_str().ends_with(".xml") || entry.path.as_str().ends_with(".hpf")
            }).map(|entry| entry.index).collect();
            assert!(!xml_entries.is_empty());
            for index in xml_entries {
                let xml = reader.read_entry(index)?;
                let old = original(&xml, SafeXmlLimits::default());
                let new = SafeXmlDocument::parse(&xml, SafeXmlLimits::default());
                assert_eq!(new, old);
                assert!(new.is_ok());
                parts += 1;
            }
            originals += 1;
        }
        assert_eq!(originals, 36);
        assert!(parts >= 36);
        Ok(())
    }

    #[test]
    fn long_sparse_text_reserves256_not100000_and_dense_events_still_grow()
    -> Result<(), Box<dyn Error>> {
        let sparse = format!("<root>{}</root>", "x".repeat(512 * 1024));
        let old = original(sparse.as_bytes(), SafeXmlLimits::default())?;
        let new = SafeXmlDocument::parse(sparse.as_bytes(), SafeXmlLimits::default())?;
        assert_eq!(new, old);
        assert_eq!(new.events.len(), 3);
        assert_eq!(new.spans.len(), 3);
        assert!(new.events.capacity() <= 256);
        assert!(new.spans.capacity() <= 256);
        assert!(old.events.capacity() >= 100_000);
        assert!(old.spans.capacity() >= 100_000);
        let dense = format!("<root>{}</root>", "<item/>".repeat(600));
        let old = original(dense.as_bytes(), SafeXmlLimits::default())?;
        let new = SafeXmlDocument::parse(dense.as_bytes(), SafeXmlLimits::default())?;
        assert_eq!(new, old);
        assert_eq!(new.events.len(), 602);
        assert!(new.events.capacity() >= 602);
        assert!(new.spans.capacity() >= 602);
        Ok(())
    }

    #[test]
    fn all_original_safety_limits_and_error_precedence_ignore_reservation_hint()
    -> Result<(), Box<dyn Error>> {
        let invalid: &[&[u8]] = &[
            b"", b"<root>", b"<a><b></a>", b"<p:root/>",
            br#"<root a="1" a="2"/>"#,
            br#"<root xmlns:a="urn:x" xmlns:b="urn:x" a:id="1" b:id="2"/>"#,
            br#"<root p:id="1"/>"#, br#" <?xml version="1.0"?><root/>"#,
            br#"<!--before--><?xml version="1.0"?><root/>"#,
            br#"<?xml version="1.0" encoding="UTF-8" encoding="UTF-8"?><root/>"#,
            br#"<?xml version="1.0" standalone="yes" encoding="UTF-8"?><root/>"#,
            b"<one/><two/>", b"text<root/>", b"<root/>text",
            "<root/>\u{00A0}".as_bytes(), b"<!DOCTYPE root><root/>",
            b"<root>&custom;</root>", b"<?target data?><root/>",
            b"<root><![CDATA[x]]></root>", br#"<?xml version="1.1"?><root/>"#,
            br#"<?xml version="1.0" encoding="EUC-KR"?><root/>"#,
            b"<root>\xff</root>",
        ];
        for xml in invalid {
            let old = original(xml, SafeXmlLimits::default());
            assert!(old.is_err());
            for hint in [0, 1, 256] {
                assert_eq!(SafeXmlDocument::parse_with_capacity_hint(xml, SafeXmlLimits::default(), hint), old);
            }
        }
        let cases: Vec<(SafeXmlLimitConfig, Vec<u8>)> = vec![
            (SafeXmlLimitConfig { input_bytes: 8, text_bytes: 8, total_text_bytes: 8,
                ..SafeXmlLimitConfig::default() }, b"<root/>xx".to_vec()),
            (SafeXmlLimitConfig { depth: 1, ..SafeXmlLimitConfig::default() }, b"<root><child/></root>".to_vec()),
            (SafeXmlLimitConfig { events: 2, ..SafeXmlLimitConfig::default() }, b"<root></root>".to_vec()),
            (SafeXmlLimitConfig { nodes: 1, ..SafeXmlLimitConfig::default() }, b"<root>text</root>".to_vec()),
            (SafeXmlLimitConfig { text_bytes: 3, total_text_bytes: 8,
                ..SafeXmlLimitConfig::default() }, b"<root>four</root>".to_vec()),
            (SafeXmlLimitConfig { text_bytes: 4, total_text_bytes: 5,
                ..SafeXmlLimitConfig::default() }, b"<root>abc<child/>def</root>".to_vec()),
            (SafeXmlLimitConfig { attributes_per_element: 1, ..SafeXmlLimitConfig::default() }, br#"<root a="1" b="2"/>"#.to_vec()),
            (SafeXmlLimitConfig { attribute_bytes: 4, ..SafeXmlLimitConfig::default() }, br#"<root long="value"/>"#.to_vec()),
            (SafeXmlLimitConfig { namespace_bindings: 1, ..SafeXmlLimitConfig::default() }, br#"<root xmlns:a="urn:a" xmlns:b="urn:b"/>"#.to_vec()),
            (SafeXmlLimitConfig { events: 500, ..SafeXmlLimitConfig::default() }, format!("<root>{}</root>", "<item/>".repeat(600)).into_bytes()),
        ];
        for (config, xml) in cases {
            let limits = SafeXmlLimits::new(config)?;
            let old = original(&xml, limits);
            assert!(old.is_err());
            for hint in [0, 1, 256] {
                assert_eq!(SafeXmlDocument::parse_with_capacity_hint(&xml, limits, hint), old);
            }
        }
        Ok(())
    }
}
