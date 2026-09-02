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
pub(crate) struct SafeXmlElement {
    pub qualified_name: String,
    pub local_name: String,
    pub namespace: Option<String>,
    pub attributes: BTreeMap<String, String>,
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
}

impl SafeXmlDocument {
    pub fn parse(bytes: &[u8], limits: SafeXmlLimits) -> Result<Self, SafeXmlError> {
        if bytes.len() > limits.config().input_bytes {
            return Err(SafeXmlError::InputLimit);
        }
        let mut reader = NsReader::from_reader(bytes);
        reader.config_mut().enable_all_checks(true);
        reader
            .resolver_mut()
            .set_max_namespace_bindings(limits.config().namespace_bindings);

        let initial_capacity = limits
            .config()
            .events
            .min(bytes.len().saturating_div(2).saturating_add(1));
        let mut output = Vec::new();
        output
            .try_reserve_exact(initial_capacity)
            .map_err(|_| SafeXmlError::AllocationFailed)?;
        let mut state = ParseState::default();

        loop {
            let event = reader
                .read_event()
                .map_err(|error| map_quick_xml_error(&error))?;
            let (namespace, event) = reader.resolver().resolve_event(event);
            state.count_event(limits)?;
            match event {
                Event::Start(element) => {
                    let next_depth = state.next_depth(limits)?;
                    state.begin_root_if_needed()?;
                    state.count_node(limits)?;
                    let element =
                        safe_element(&element, &namespace, reader.resolver(), next_depth, limits)?;
                    push_event(&mut output, SafeXmlEvent::Start(element))?;
                    state.depth = next_depth;
                }
                Event::Empty(element) => {
                    let element_depth = state.next_depth(limits)?;
                    state.begin_root_if_needed()?;
                    state.count_node(limits)?;
                    let element = safe_element(
                        &element,
                        &namespace,
                        reader.resolver(),
                        element_depth,
                        limits,
                    )?;
                    push_event(&mut output, SafeXmlEvent::Empty(element))?;
                }
                Event::End(_) => {
                    resolved_namespace(&namespace)?;
                    state.depth = state.depth.checked_sub(1).ok_or(SafeXmlError::Malformed)?;
                    push_event(&mut output, SafeXmlEvent::End)?;
                }
                Event::Text(text) => {
                    let length = text.as_ref().len();
                    if state.depth == 0 && !text.as_ref().chars().all(char::is_whitespace) {
                        return Err(SafeXmlError::Malformed);
                    }
                    state.count_text(length, limits)?;
                    state.count_node(limits)?;
                    push_event(&mut output, SafeXmlEvent::Text { bytes: length })?;
                }
                Event::GeneralRef(reference) => {
                    if state.depth == 0 || !is_safe_xml_reference(reference.as_ref()) {
                        return Err(SafeXmlError::CustomEntityForbidden);
                    }
                    state.count_text(1, limits)?;
                    state.count_node(limits)?;
                    push_event(&mut output, SafeXmlEvent::Reference)?;
                }
                Event::Comment(_) => {
                    state.count_node(limits)?;
                    push_event(&mut output, SafeXmlEvent::Comment)?;
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
                    push_event(&mut output, SafeXmlEvent::Declaration)?;
                }
                Event::DocType(_) => return Err(SafeXmlError::DtdForbidden),
                Event::PI(_) => return Err(SafeXmlError::ProcessingInstructionForbidden),
                Event::CData(_) => return Err(SafeXmlError::CdataForbidden),
                Event::Eof => break,
            }
        }
        if state.depth != 0 || state.root_count != 1 {
            return Err(SafeXmlError::Malformed);
        }
        Ok(Self { events: output })
    }
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
    let mut expanded_attributes = BTreeSet::new();
    let mut total_attribute_bytes = 0_usize;
    for (index, attribute) in element.attributes().with_checks(true).enumerate() {
        if index >= limits.config().attributes_per_element {
            return Err(SafeXmlError::AttributeLimit);
        }
        let attribute = attribute.map_err(|_| SafeXmlError::Malformed)?;
        let key = attribute.key.as_ref().to_owned();
        if key != "xmlns" && !key.starts_with("xmlns:") {
            let (attribute_namespace, local_name) = resolver.resolve_attribute(attribute.key);
            let expanded_name = (
                resolved_namespace(&attribute_namespace)?.map(str::to_owned),
                local_name.as_ref().to_owned(),
            );
            if !expanded_attributes.insert(expanded_name) {
                return Err(SafeXmlError::DuplicateAttribute);
            }
        }
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

fn push_event(output: &mut Vec<SafeXmlEvent>, event: SafeXmlEvent) -> Result<(), SafeXmlError> {
    output
        .try_reserve(1)
        .map_err(|_| SafeXmlError::AllocationFailed)?;
    output.push(event);
    Ok(())
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
