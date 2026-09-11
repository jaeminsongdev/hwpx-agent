use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use domain_ir::{
    MATH_AST_NORMALIZATION_VERSION, MATH_AST_SCHEMA_VERSION, MathAccent, MathAnnotationKind,
    MathAst, MathAstDraft, MathAstLimits, MathColor, MathDelimiter, MathDerivativeKind,
    MathDerivativeVariable, MathExpression, MathFunction, MathGreekLetter, MathLargeOperator,
    MathLetterCase, MathMatrixKind, MathNode, MathOperator, MathSourceSpan, MathStyleHint,
    MathSymbol, MathVariant,
};
use quick_xml::escape::EscapeError;
use quick_xml::events::{BytesDecl, BytesStart, Event};
use quick_xml::name::{NamespaceError, NamespaceResolver, ResolveResult};
use quick_xml::reader::NsReader;
use quick_xml::{Error as QuickXmlError, XmlVersion};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const MATHML_NAMESPACE: &str = "http://www.w3.org/1998/Math/MathML";
pub const MATHML_ADAPTER_SCHEMA_VERSION: &str = "hwpx-agent.mathml-adapter/v1";
pub const MATHML_PROFILE_VERSION: &str = "hwpx-agent.mathml-profile/finite-v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct MathMlAdapterLimitConfig {
    pub source_bytes: usize,
    pub events: usize,
    pub elements: usize,
    pub depth: usize,
    pub text_bytes: usize,
    pub total_text_bytes: usize,
    pub attributes_per_element: usize,
    pub attribute_bytes: usize,
    pub namespace_bindings: usize,
    pub children_per_element: usize,
    pub parser_depth: usize,
    pub serialized_bytes: usize,
}

impl Default for MathMlAdapterLimitConfig {
    fn default() -> Self {
        Self {
            source_bytes: 1024 * 1024,
            events: 65_536,
            elements: 8_192,
            depth: 128,
            text_bytes: 64 * 1024,
            total_text_bytes: 1024 * 1024,
            attributes_per_element: 8,
            attribute_bytes: 64 * 1024,
            namespace_bindings: 2_048,
            children_per_element: 512,
            parser_depth: 128,
            serialized_bytes: 8 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct MathMlAdapterLimits(MathMlAdapterLimitConfig);

impl MathMlAdapterLimits {
    pub const HARD_MAX_SOURCE_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_EVENTS: usize = 1_000_000;
    pub const HARD_MAX_ELEMENTS: usize = 65_536;
    pub const HARD_MAX_DEPTH: usize = 256;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_TOTAL_TEXT_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_ATTRIBUTES_PER_ELEMENT: usize = 64;
    pub const HARD_MAX_ATTRIBUTE_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_NAMESPACE_BINDINGS: usize = 4_096;
    pub const HARD_MAX_CHILDREN_PER_ELEMENT: usize = 4_096;
    pub const HARD_MAX_PARSER_DEPTH: usize = 256;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;

    /// Creates finite XML, tree, parser and output limits for the P07-03 adapter.
    ///
    /// # Errors
    ///
    /// Returns [`MathMlAdapterError::InvalidLimit`] for a zero, over-ceiling or inconsistent
    /// configuration.
    pub fn new(config: MathMlAdapterLimitConfig) -> Result<Self, MathMlAdapterError> {
        if config.source_bytes == 0
            || config.source_bytes > Self::HARD_MAX_SOURCE_BYTES
            || config.events == 0
            || config.events > Self::HARD_MAX_EVENTS
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.depth == 0
            || config.depth > Self::HARD_MAX_DEPTH
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.total_text_bytes == 0
            || config.total_text_bytes > Self::HARD_MAX_TOTAL_TEXT_BYTES
            || config.text_bytes > config.total_text_bytes
            || config.total_text_bytes > config.source_bytes
            || config.attributes_per_element == 0
            || config.attributes_per_element > Self::HARD_MAX_ATTRIBUTES_PER_ELEMENT
            || config.attribute_bytes == 0
            || config.attribute_bytes > Self::HARD_MAX_ATTRIBUTE_BYTES
            || config.namespace_bindings == 0
            || config.namespace_bindings > Self::HARD_MAX_NAMESPACE_BINDINGS
            || config.children_per_element == 0
            || config.children_per_element > Self::HARD_MAX_CHILDREN_PER_ELEMENT
            || config.parser_depth == 0
            || config.parser_depth > Self::HARD_MAX_PARSER_DEPTH
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(MathMlAdapterError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> MathMlAdapterLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathMlParseRequestDraft {
    pub schema_version: String,
    pub source: String,
}

impl fmt::Debug for MathMlParseRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MathMlParseRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("source", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathMlSourceProfile {
    Presentation,
    Content,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct MathMlParseResult {
    schema_version: &'static str,
    profile_version: &'static str,
    math_ast_schema_version: &'static str,
    normalization_version: &'static str,
    source_profile: MathMlSourceProfile,
    source_sha256: String,
    source_length_bytes: u32,
    element_count: usize,
    decoded_text_bytes: usize,
    ast: MathAst,
}

impl MathMlParseResult {
    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub const fn profile_version(&self) -> &'static str {
        self.profile_version
    }

    #[must_use]
    pub const fn source_profile(&self) -> MathMlSourceProfile {
        self.source_profile
    }

    #[must_use]
    pub fn source_sha256(&self) -> &str {
        &self.source_sha256
    }

    #[must_use]
    pub const fn source_length_bytes(&self) -> u32 {
        self.source_length_bytes
    }

    #[must_use]
    pub const fn element_count(&self) -> usize {
        self.element_count
    }

    #[must_use]
    pub const fn decoded_text_bytes(&self) -> usize {
        self.decoded_text_bytes
    }

    #[must_use]
    pub const fn ast(&self) -> &MathAst {
        &self.ast
    }

    /// Serializes the complete result without retaining raw `MathML` as a separate field.
    ///
    /// # Errors
    ///
    /// Returns a bounded serialization error when encoding exceeds the configured output limit.
    pub fn canonical_json(
        &self,
        limits: MathMlAdapterLimits,
    ) -> Result<Vec<u8>, MathMlAdapterError> {
        let bytes = serde_json::to_vec(self).map_err(|_| MathMlAdapterError::Serialization)?;
        if bytes.len() > limits.0.serialized_bytes {
            return Err(MathMlAdapterError::OutputLimit);
        }
        Ok(bytes)
    }
}

impl fmt::Debug for MathMlParseResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MathMlParseResult")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("math_ast_schema_version", &self.math_ast_schema_version)
            .field("normalization_version", &self.normalization_version)
            .field("source_profile", &self.source_profile)
            .field("source_sha256", &"<redacted>")
            .field("source_length_bytes", &"<redacted>")
            .field("element_count", &self.element_count)
            .field("decoded_text_bytes", &self.decoded_text_bytes)
            .field("ast", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum MathMlAdapterError {
    #[error("MathML adapter limit configuration is invalid")]
    InvalidLimit,
    #[error("MathML request is empty or exceeds its input limit")]
    InputLimit,
    #[error("MathML request JSON is invalid")]
    InvalidJson,
    #[error("MathML adapter schema version is unsupported")]
    UnsupportedVersion,
    #[error("MathML XML is malformed")]
    XmlMalformed,
    #[error("MathML XML declaration or encoding is forbidden")]
    EncodingForbidden,
    #[error("MathML DTD is forbidden")]
    DtdForbidden,
    #[error("MathML custom entity is forbidden")]
    EntityForbidden,
    #[error("MathML processing instruction is forbidden")]
    ProcessingInstructionForbidden,
    #[error("MathML CDATA is forbidden")]
    CdataForbidden,
    #[error("MathML namespace is invalid or unsupported")]
    NamespaceInvalid,
    #[error("MathML XML exceeded a finite resource limit")]
    XmlLimit,
    #[error("MathML source mixes content and presentation profiles")]
    MixedProfile,
    #[error("MathML element is outside the finite profile")]
    UnsupportedElement,
    #[error("MathML attribute is outside the finite profile")]
    UnsupportedAttribute,
    #[error("MathML text or token is invalid")]
    InvalidToken,
    #[error("MathML presentation semantics are ambiguous")]
    AmbiguousPresentation,
    #[error("MathML structure is invalid")]
    InvalidStructure,
    #[error("MathML could not be admitted into MathAst")]
    MathAst,
    #[error("MathML result exceeds its output limit")]
    OutputLimit,
    #[error("MathML result serialization failed")]
    Serialization,
}

impl MathMlAdapterError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "mathml_adapter_invalid_limit",
            Self::InputLimit => "mathml_adapter_input_limit",
            Self::InvalidJson => "mathml_adapter_invalid_json",
            Self::UnsupportedVersion => "mathml_adapter_unsupported_version",
            Self::XmlMalformed => "mathml_adapter_xml_malformed",
            Self::EncodingForbidden => "mathml_adapter_encoding_forbidden",
            Self::DtdForbidden => "mathml_adapter_dtd_forbidden",
            Self::EntityForbidden => "mathml_adapter_entity_forbidden",
            Self::ProcessingInstructionForbidden => "mathml_adapter_pi_forbidden",
            Self::CdataForbidden => "mathml_adapter_cdata_forbidden",
            Self::NamespaceInvalid => "mathml_adapter_namespace_invalid",
            Self::XmlLimit => "mathml_adapter_xml_limit",
            Self::MixedProfile => "mathml_adapter_mixed_profile",
            Self::UnsupportedElement => "mathml_adapter_unsupported_element",
            Self::UnsupportedAttribute => "mathml_adapter_unsupported_attribute",
            Self::InvalidToken => "mathml_adapter_invalid_token",
            Self::AmbiguousPresentation => "mathml_adapter_ambiguous_presentation",
            Self::InvalidStructure => "mathml_adapter_invalid_structure",
            Self::MathAst => "mathml_adapter_math_ast",
            Self::OutputLimit => "mathml_adapter_output_limit",
            Self::Serialization => "mathml_adapter_serialization",
        }
    }
}

#[derive(Clone)]
struct XmlElement {
    local_name: String,
    attributes: BTreeMap<String, String>,
    children: Vec<XmlElement>,
    text: String,
    span: MathSourceSpan,
}

struct XmlDocument {
    root: XmlElement,
    elements: usize,
    decoded_text_bytes: usize,
}

#[derive(Default)]
struct XmlState {
    events: usize,
    elements: usize,
    decoded_text_bytes: usize,
    root: Option<XmlElement>,
    declaration_seen: bool,
}

impl XmlDocument {
    fn parse(source: &[u8], limits: MathMlAdapterLimits) -> Result<Self, MathMlAdapterError> {
        if source.is_empty() || source.len() > limits.0.source_bytes {
            return Err(MathMlAdapterError::InputLimit);
        }
        std::str::from_utf8(source).map_err(|_| MathMlAdapterError::EncodingForbidden)?;
        let source_offset = u64::from(source.starts_with(&[0xEF, 0xBB, 0xBF])) * 3;
        let mut reader = NsReader::from_reader(source);
        reader.config_mut().enable_all_checks(true);
        reader
            .resolver_mut()
            .set_max_namespace_bindings(limits.0.namespace_bindings);
        let mut stack = Vec::new();
        let mut state = XmlState::default();
        loop {
            state.events = state
                .events
                .checked_add(1)
                .ok_or(MathMlAdapterError::XmlLimit)?;
            if state.events > limits.0.events {
                return Err(MathMlAdapterError::XmlLimit);
            }
            let event_start = reader.buffer_position();
            let event = reader.read_event().map_err(|error| map_xml_error(&error))?;
            let start = event_start
                .checked_add(source_offset)
                .ok_or(MathMlAdapterError::XmlMalformed)?;
            let end = reader
                .buffer_position()
                .checked_add(source_offset)
                .ok_or(MathMlAdapterError::XmlMalformed)?;
            let event_span = reader_span(start, end, source.len())?;
            let (namespace, event) = reader.resolver().resolve_event(event);
            if process_xml_event(
                event,
                &namespace,
                reader.resolver(),
                event_span,
                &mut stack,
                &mut state,
                limits,
            )? {
                break;
            }
        }
        if !stack.is_empty() {
            return Err(MathMlAdapterError::XmlMalformed);
        }
        let root = state.root.ok_or(MathMlAdapterError::XmlMalformed)?;
        Ok(Self {
            root,
            elements: state.elements,
            decoded_text_bytes: state.decoded_text_bytes,
        })
    }
}

#[allow(clippy::too_many_arguments)]
fn process_xml_event(
    event: Event<'_>,
    namespace: &ResolveResult<'_>,
    resolver: &NamespaceResolver,
    event_span: MathSourceSpan,
    stack: &mut Vec<XmlElement>,
    state: &mut XmlState,
    limits: MathMlAdapterLimits,
) -> Result<bool, MathMlAdapterError> {
    match event {
        Event::Start(element) => {
            if stack.len() >= limits.0.depth {
                return Err(MathMlAdapterError::XmlLimit);
            }
            count_element(state, limits)?;
            stack.push(read_element_start(
                &element,
                namespace,
                resolver,
                event_span.start_byte,
                limits,
            )?);
        }
        Event::Empty(element) => {
            count_element(state, limits)?;
            let mut node =
                read_element_start(&element, namespace, resolver, event_span.start_byte, limits)?;
            node.span.end_byte = event_span.end_byte;
            attach_element(node, stack, state, limits)?;
        }
        Event::End(_) => {
            require_mathml_namespace(namespace)?;
            let mut node = stack.pop().ok_or(MathMlAdapterError::XmlMalformed)?;
            node.span.end_byte = event_span.end_byte;
            attach_element(node, stack, state, limits)?;
        }
        Event::Text(text) => {
            let decoded = normalize_xml_newlines(text.as_ref());
            append_text(&decoded, stack, state, limits)?;
        }
        Event::GeneralRef(reference) => {
            let decoded = decode_reference(reference.as_ref())?;
            append_text(&decoded, stack, state, limits)?;
        }
        Event::Decl(declaration) => {
            if state.events != 1
                || state.declaration_seen
                || state.root.is_some()
                || !stack.is_empty()
            {
                return Err(MathMlAdapterError::XmlMalformed);
            }
            validate_declaration(&declaration)?;
            state.declaration_seen = true;
        }
        Event::DocType(_) => return Err(MathMlAdapterError::DtdForbidden),
        Event::PI(_) => return Err(MathMlAdapterError::ProcessingInstructionForbidden),
        Event::CData(_) => return Err(MathMlAdapterError::CdataForbidden),
        Event::Comment(_) => return Err(MathMlAdapterError::UnsupportedElement),
        Event::Eof => return Ok(true),
    }
    Ok(false)
}

fn count_element(
    state: &mut XmlState,
    limits: MathMlAdapterLimits,
) -> Result<(), MathMlAdapterError> {
    state.elements = state
        .elements
        .checked_add(1)
        .ok_or(MathMlAdapterError::XmlLimit)?;
    if state.elements > limits.0.elements {
        return Err(MathMlAdapterError::XmlLimit);
    }
    Ok(())
}

fn reader_span(
    start: u64,
    end: u64,
    source_len: usize,
) -> Result<MathSourceSpan, MathMlAdapterError> {
    let start = usize::try_from(start).map_err(|_| MathMlAdapterError::InputLimit)?;
    let end = usize::try_from(end).map_err(|_| MathMlAdapterError::InputLimit)?;
    if start > end || end > source_len {
        return Err(MathMlAdapterError::XmlMalformed);
    }
    Ok(MathSourceSpan {
        start_byte: u32::try_from(start).map_err(|_| MathMlAdapterError::InputLimit)?,
        end_byte: u32::try_from(end).map_err(|_| MathMlAdapterError::InputLimit)?,
    })
}

fn read_element_start(
    element: &BytesStart<'_>,
    namespace: &ResolveResult<'_>,
    resolver: &NamespaceResolver,
    start_byte: u32,
    limits: MathMlAdapterLimits,
) -> Result<XmlElement, MathMlAdapterError> {
    require_mathml_namespace(namespace)?;
    let local_name = element.local_name().as_ref().to_owned();
    let mut attributes = BTreeMap::new();
    let mut expanded = BTreeSet::new();
    let mut attribute_bytes = 0usize;
    for (index, attribute) in element.attributes().with_checks(true).enumerate() {
        if index >= limits.0.attributes_per_element {
            return Err(MathMlAdapterError::XmlLimit);
        }
        let attribute = attribute.map_err(|_| MathMlAdapterError::XmlMalformed)?;
        let key = attribute.key.as_ref();
        let namespace_declaration = key == "xmlns" || key.starts_with("xmlns:");
        let value = attribute
            .normalized_value(XmlVersion::Implicit1_0)
            .map_err(|error| map_xml_error(&error))?
            .into_owned();
        attribute_bytes = attribute_bytes
            .checked_add(key.len())
            .and_then(|count| count.checked_add(value.len()))
            .ok_or(MathMlAdapterError::XmlLimit)?;
        if attribute_bytes > limits.0.attribute_bytes {
            return Err(MathMlAdapterError::XmlLimit);
        }
        if namespace_declaration {
            if value != MATHML_NAMESPACE {
                return Err(MathMlAdapterError::NamespaceInvalid);
            }
            continue;
        }
        let (attribute_namespace, local) = resolver.resolve_attribute(attribute.key);
        if resolved_namespace(&attribute_namespace)?.is_some() {
            return Err(MathMlAdapterError::UnsupportedAttribute);
        }
        let local = local.as_ref().to_owned();
        if !expanded.insert(local.clone()) || attributes.insert(local, value).is_some() {
            return Err(MathMlAdapterError::XmlMalformed);
        }
    }
    Ok(XmlElement {
        local_name,
        attributes,
        children: Vec::new(),
        text: String::new(),
        span: MathSourceSpan {
            start_byte,
            end_byte: start_byte,
        },
    })
}

fn attach_element(
    node: XmlElement,
    stack: &mut [XmlElement],
    state: &mut XmlState,
    limits: MathMlAdapterLimits,
) -> Result<(), MathMlAdapterError> {
    if let Some(parent) = stack.last_mut() {
        if parent.children.len() >= limits.0.children_per_element {
            return Err(MathMlAdapterError::XmlLimit);
        }
        parent.children.push(node);
    } else if state.root.replace(node).is_some() {
        return Err(MathMlAdapterError::XmlMalformed);
    }
    Ok(())
}

fn append_text(
    text: &str,
    stack: &mut [XmlElement],
    state: &mut XmlState,
    limits: MathMlAdapterLimits,
) -> Result<(), MathMlAdapterError> {
    if text.len() > limits.0.text_bytes {
        return Err(MathMlAdapterError::XmlLimit);
    }
    if let Some(current) = stack.last_mut() {
        let next = current
            .text
            .len()
            .checked_add(text.len())
            .ok_or(MathMlAdapterError::XmlLimit)?;
        if next > limits.0.text_bytes {
            return Err(MathMlAdapterError::XmlLimit);
        }
        state.decoded_text_bytes = state
            .decoded_text_bytes
            .checked_add(text.len())
            .ok_or(MathMlAdapterError::XmlLimit)?;
        if state.decoded_text_bytes > limits.0.total_text_bytes {
            return Err(MathMlAdapterError::XmlLimit);
        }
        current.text.push_str(text);
    } else if !text.bytes().all(is_xml_whitespace) {
        return Err(MathMlAdapterError::XmlMalformed);
    }
    Ok(())
}

fn require_mathml_namespace(namespace: &ResolveResult<'_>) -> Result<(), MathMlAdapterError> {
    if resolved_namespace(namespace)? == Some(MATHML_NAMESPACE) {
        Ok(())
    } else {
        Err(MathMlAdapterError::NamespaceInvalid)
    }
}

fn resolved_namespace<'a>(
    namespace: &'a ResolveResult<'a>,
) -> Result<Option<&'a str>, MathMlAdapterError> {
    match namespace {
        ResolveResult::Unbound => Ok(None),
        ResolveResult::Bound(namespace) => Ok(Some(namespace.as_ref())),
        ResolveResult::Unknown(_) => Err(MathMlAdapterError::NamespaceInvalid),
    }
}

fn normalize_xml_newlines(text: &str) -> String {
    text.replace("\r\n", "\n").replace('\r', "\n")
}

fn decode_reference(reference: &str) -> Result<String, MathMlAdapterError> {
    let character = match reference {
        "amp" => '&',
        "lt" => '<',
        "gt" => '>',
        "apos" => '\'',
        "quot" => '"',
        _ => {
            let value = reference
                .strip_prefix("#x")
                .or_else(|| reference.strip_prefix("#X"))
                .and_then(|digits| u32::from_str_radix(digits, 16).ok())
                .or_else(|| {
                    reference
                        .strip_prefix('#')
                        .and_then(|digits| digits.parse::<u32>().ok())
                })
                .filter(|value| is_xml_character(*value))
                .and_then(char::from_u32)
                .ok_or(MathMlAdapterError::EntityForbidden)?;
            return Ok(value.to_string());
        }
    };
    Ok(character.to_string())
}

const fn is_xml_character(value: u32) -> bool {
    matches!(value, 0x09 | 0x0A | 0x0D | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x1_0000..=0x10_FFFF)
}

const fn is_xml_whitespace(byte: u8) -> bool {
    matches!(byte, b' ' | b'\t' | b'\r' | b'\n')
}

fn validate_declaration(declaration: &BytesDecl<'_>) -> Result<(), MathMlAdapterError> {
    let mut keys = BTreeSet::new();
    let mut order = 0u8;
    let declaration_start = BytesStart::from_content(declaration.as_ref(), 3);
    for attribute in declaration_start.attributes().with_checks(true) {
        let attribute = attribute.map_err(|_| MathMlAdapterError::XmlMalformed)?;
        let key = attribute.key.as_ref();
        if !matches!(key, "version" | "encoding" | "standalone") || !keys.insert(key.to_owned()) {
            return Err(MathMlAdapterError::XmlMalformed);
        }
        order = match (order, key) {
            (0, "version") => 1,
            (1, "encoding") => 2,
            (1 | 2, "standalone") => 3,
            _ => return Err(MathMlAdapterError::XmlMalformed),
        };
    }
    if declaration
        .version()
        .map_err(|_| MathMlAdapterError::XmlMalformed)?
        .as_ref()
        != "1.0"
    {
        return Err(MathMlAdapterError::EncodingForbidden);
    }
    if declaration
        .encoding()
        .transpose()
        .map_err(|_| MathMlAdapterError::XmlMalformed)?
        .is_some_and(|encoding| !encoding.eq_ignore_ascii_case("utf-8"))
    {
        return Err(MathMlAdapterError::EncodingForbidden);
    }
    if declaration
        .standalone()
        .transpose()
        .map_err(|_| MathMlAdapterError::XmlMalformed)?
        .is_some_and(|standalone| !matches!(standalone.as_ref(), "yes" | "no"))
    {
        return Err(MathMlAdapterError::XmlMalformed);
    }
    Ok(())
}

fn map_xml_error(error: &QuickXmlError) -> MathMlAdapterError {
    match error {
        QuickXmlError::Encoding(_) => MathMlAdapterError::EncodingForbidden,
        QuickXmlError::Escape(
            EscapeError::UnrecognizedEntity(_, _) | EscapeError::TooManyNestedEntities,
        ) => MathMlAdapterError::EntityForbidden,
        QuickXmlError::Namespace(
            NamespaceError::TooManyBindings(_) | NamespaceError::TooDeeplyNested(_),
        ) => MathMlAdapterError::XmlLimit,
        QuickXmlError::Namespace(_) => MathMlAdapterError::NamespaceInvalid,
        _ => MathMlAdapterError::XmlMalformed,
    }
}

#[derive(Clone, Copy, Debug)]
pub struct MathMlAdapter {
    limits: MathMlAdapterLimits,
    math_limits: MathAstLimits,
}

impl MathMlAdapter {
    /// Creates an adapter whose source bound is admissible by the supplied `MathAst` limits.
    ///
    /// # Errors
    ///
    /// Returns [`MathMlAdapterError::InvalidLimit`] when the limit sets are inconsistent.
    pub fn new(
        limits: MathMlAdapterLimits,
        math_limits: MathAstLimits,
    ) -> Result<Self, MathMlAdapterError> {
        let math_source_limit = usize::try_from(math_limits.config().source_bytes)
            .map_err(|_| MathMlAdapterError::InvalidLimit)?;
        if limits.0.source_bytes > math_source_limit {
            return Err(MathMlAdapterError::InvalidLimit);
        }
        Ok(Self {
            limits,
            math_limits,
        })
    }

    /// Parses a strict JSON request.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate-field, unknown-field and oversized JSON before parsing XML.
    pub fn parse_json(&self, bytes: &[u8]) -> Result<MathMlParseResult, MathMlAdapterError> {
        if bytes.is_empty() || bytes.len() > self.limits.0.serialized_bytes {
            return Err(MathMlAdapterError::InputLimit);
        }
        let request = serde_json::from_slice(bytes).map_err(|_| MathMlAdapterError::InvalidJson)?;
        self.parse(request)
    }

    /// Parses exactly one finite content or presentation `MathML` document into `MathAst`.
    ///
    /// # Errors
    ///
    /// Rejects unsafe XML, namespace/profile mixing, unsupported or ambiguous structures, finite
    /// limit breaches and AST admission failures without returning a partial tree.
    pub fn parse(
        &self,
        request: MathMlParseRequestDraft,
    ) -> Result<MathMlParseResult, MathMlAdapterError> {
        let MathMlParseRequestDraft {
            schema_version,
            source,
        } = request;
        if schema_version != MATHML_ADAPTER_SCHEMA_VERSION {
            return Err(MathMlAdapterError::UnsupportedVersion);
        }
        if source.is_empty()
            || source.len() > self.limits.0.source_bytes
            || source.len() > u32::MAX as usize
        {
            return Err(MathMlAdapterError::InputLimit);
        }
        let document = XmlDocument::parse(source.as_bytes(), self.limits)?;
        if document.root.local_name != "math" {
            return Err(MathMlAdapterError::UnsupportedElement);
        }
        require_attributes(&document.root, &[])?;
        require_structural_text(&document.root)?;
        if document.root.children.is_empty() {
            return Err(MathMlAdapterError::InvalidStructure);
        }
        let profile = classify_profile(&document.root.children)?;
        let mut root = match profile {
            MathMlSourceProfile::Presentation => parse_presentation_children(
                &document.root.children,
                document.root.span,
                self.limits.0.parser_depth,
            )?,
            MathMlSourceProfile::Content => {
                if document.root.children.len() != 1 {
                    return Err(MathMlAdapterError::InvalidStructure);
                }
                parse_content(&document.root.children[0], 1, self.limits.0.depth)?
            }
        };
        root.span = document.root.span;
        let source_length_bytes =
            u32::try_from(source.len()).map_err(|_| MathMlAdapterError::InputLimit)?;
        let ast = MathAst::from_draft(
            MathAstDraft {
                schema_version: MATH_AST_SCHEMA_VERSION.to_owned(),
                normalization_version: MATH_AST_NORMALIZATION_VERSION.to_owned(),
                source_length_bytes,
                root,
            },
            self.math_limits,
        )
        .map_err(|_| MathMlAdapterError::MathAst)?;
        let result = MathMlParseResult {
            schema_version: MATHML_ADAPTER_SCHEMA_VERSION,
            profile_version: MATHML_PROFILE_VERSION,
            math_ast_schema_version: MATH_AST_SCHEMA_VERSION,
            normalization_version: MATH_AST_NORMALIZATION_VERSION,
            source_profile: profile,
            source_sha256: hex::encode(Sha256::digest(source.as_bytes())),
            source_length_bytes,
            element_count: document.elements,
            decoded_text_bytes: document.decoded_text_bytes,
            ast,
        };
        let _ = result.canonical_json(self.limits)?;
        Ok(result)
    }
}

const PRESENTATION_ELEMENTS: &[&str] = &[
    "mrow",
    "mn",
    "mi",
    "mo",
    "mtext",
    "mfrac",
    "msqrt",
    "mroot",
    "msub",
    "msup",
    "msubsup",
    "mfenced",
    "mover",
    "munder",
    "munderover",
    "mstyle",
    "mtable",
    "mtr",
    "mtd",
];

const CONTENT_ELEMENTS: &[&str] = &[
    "apply",
    "cn",
    "ci",
    "cs",
    "plus",
    "minus",
    "times",
    "divide",
    "power",
    "factorial",
    "eq",
    "neq",
    "lt",
    "leq",
    "gt",
    "geq",
    "approx",
    "factorof",
    "and",
    "or",
    "not",
    "implies",
    "equivalent",
    "in",
    "notin",
    "subset",
    "prsubset",
    "union",
    "intersect",
    "setdiff",
    "compose",
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "log",
    "ln",
    "exp",
    "min",
    "max",
    "root",
    "degree",
    "sum",
    "product",
    "limit",
    "int",
    "lowlimit",
    "uplimit",
    "diff",
    "partialdiff",
    "bvar",
    "matrix",
    "matrixrow",
    "set",
    "condition",
    "infinity",
    "emptyset",
    "pi",
];

fn classify_profile(children: &[XmlElement]) -> Result<MathMlSourceProfile, MathMlAdapterError> {
    let mut presentation = false;
    let mut content = false;
    for child in children {
        presentation |= PRESENTATION_ELEMENTS.contains(&child.local_name.as_str());
        content |= CONTENT_ELEMENTS.contains(&child.local_name.as_str());
        if !presentation && !content {
            return Err(MathMlAdapterError::UnsupportedElement);
        }
    }
    match (presentation, content) {
        (true, false) => Ok(MathMlSourceProfile::Presentation),
        (false, true) => Ok(MathMlSourceProfile::Content),
        (true, true) => Err(MathMlAdapterError::MixedProfile),
        (false, false) => Err(MathMlAdapterError::UnsupportedElement),
    }
}

fn require_attributes(node: &XmlElement, allowed: &[&str]) -> Result<(), MathMlAdapterError> {
    if node
        .attributes
        .keys()
        .any(|key| !allowed.contains(&key.as_str()))
    {
        return Err(MathMlAdapterError::UnsupportedAttribute);
    }
    Ok(())
}

fn require_structural_text(node: &XmlElement) -> Result<(), MathMlAdapterError> {
    if node.text.bytes().all(is_xml_whitespace) {
        Ok(())
    } else {
        Err(MathMlAdapterError::InvalidStructure)
    }
}

fn require_leaf_text(node: &XmlElement) -> Result<&str, MathMlAdapterError> {
    if !node.children.is_empty() || node.text.is_empty() || node.text.chars().any(char::is_control)
    {
        return Err(MathMlAdapterError::InvalidToken);
    }
    if node.text.trim() != node.text {
        return Err(MathMlAdapterError::InvalidToken);
    }
    Ok(&node.text)
}

fn require_empty(node: &XmlElement) -> Result<(), MathMlAdapterError> {
    require_attributes(node, &[])?;
    if node.children.is_empty() && node.text.is_empty() {
        Ok(())
    } else {
        Err(MathMlAdapterError::InvalidStructure)
    }
}

fn make_node(span: MathSourceSpan, expression: MathExpression) -> MathNode {
    MathNode {
        span,
        style: None,
        expression,
    }
}

fn make_apply(span: MathSourceSpan, operator: MathOperator, arguments: Vec<MathNode>) -> MathNode {
    make_node(
        span,
        MathExpression::Apply {
            operator,
            arguments,
        },
    )
}

fn parse_style(node: &XmlElement) -> Result<Option<MathStyleHint>, MathMlAdapterError> {
    require_attributes(node, &["mathvariant", "mathcolor"])?;
    let variant = node
        .attributes
        .get("mathvariant")
        .map(|value| match value.as_str() {
            "normal" => Ok(MathVariant::Normal),
            "upright" => Ok(MathVariant::Upright),
            "italic" => Ok(MathVariant::Italic),
            "bold" => Ok(MathVariant::Bold),
            "bold-italic" => Ok(MathVariant::BoldItalic),
            "double-struck" => Ok(MathVariant::DoubleStruck),
            "fraktur" => Ok(MathVariant::Fraktur),
            "script" => Ok(MathVariant::Script),
            "sans-serif" => Ok(MathVariant::SansSerif),
            "monospace" => Ok(MathVariant::Monospace),
            _ => Err(MathMlAdapterError::UnsupportedAttribute),
        })
        .transpose()?;
    let color = node
        .attributes
        .get("mathcolor")
        .map(|value| parse_color(value))
        .transpose()?;
    Ok((variant.is_some() || color.is_some()).then_some(MathStyleHint { variant, color }))
}

fn parse_color(value: &str) -> Result<MathColor, MathMlAdapterError> {
    let hex = value
        .strip_prefix('#')
        .filter(|hex| hex.len() == 6)
        .ok_or(MathMlAdapterError::UnsupportedAttribute)?;
    let channel = |range: std::ops::Range<usize>| {
        u8::from_str_radix(&hex[range], 16).map_err(|_| MathMlAdapterError::UnsupportedAttribute)
    };
    Ok(MathColor {
        red: channel(0..2)?,
        green: channel(2..4)?,
        blue: channel(4..6)?,
    })
}

fn styled_leaf(
    node: &XmlElement,
    expression: MathExpression,
) -> Result<MathNode, MathMlAdapterError> {
    let mut result = make_node(node.span, expression);
    result.style = parse_style(node)?;
    Ok(result)
}

#[derive(Clone)]
enum PresentationItem {
    Node(MathNode),
    Prefix(MathOperator),
    Infix(MathOperator, u8),
    Factorial,
    FunctionApply,
    LargeHead {
        operator: MathLargeOperator,
        lower: Option<Box<MathNode>>,
        upper: Option<Box<MathNode>>,
        span: MathSourceSpan,
    },
}

fn parse_presentation_children(
    children: &[XmlElement],
    span: MathSourceSpan,
    parser_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    if children.is_empty() {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    let mut items = Vec::new();
    for child in children {
        items.push(parse_presentation_item(child, parser_depth)?);
    }
    PresentationParser::new(&items, parser_depth).parse(span)
}

fn parse_presentation_item(
    node: &XmlElement,
    parser_depth: usize,
) -> Result<PresentationItem, MathMlAdapterError> {
    match node.local_name.as_str() {
        "mn" | "mi" | "mtext" | "mo" => parse_presentation_leaf(node),
        "mrow" => {
            require_attributes(node, &[])?;
            require_structural_text(node)?;
            Ok(PresentationItem::Node(parse_presentation_children(
                &node.children,
                node.span,
                parser_depth,
            )?))
        }
        "mfrac" => {
            require_attributes(node, &[])?;
            require_structural_text(node)?;
            let [numerator, denominator] = node.children.as_slice() else {
                return Err(MathMlAdapterError::InvalidStructure);
            };
            Ok(PresentationItem::Node(make_node(
                node.span,
                MathExpression::Fraction {
                    numerator: Box::new(parse_presentation_node(numerator, parser_depth)?),
                    denominator: Box::new(parse_presentation_node(denominator, parser_depth)?),
                },
            )))
        }
        "msqrt" => {
            require_attributes(node, &[])?;
            require_structural_text(node)?;
            let radicand = parse_presentation_children(&node.children, node.span, parser_depth)?;
            Ok(PresentationItem::Node(make_node(
                node.span,
                MathExpression::Root {
                    degree: None,
                    radicand: Box::new(radicand),
                },
            )))
        }
        "mroot" => {
            require_attributes(node, &[])?;
            require_structural_text(node)?;
            let [radicand, degree] = node.children.as_slice() else {
                return Err(MathMlAdapterError::InvalidStructure);
            };
            Ok(PresentationItem::Node(make_node(
                node.span,
                MathExpression::Root {
                    degree: Some(Box::new(parse_presentation_node(degree, parser_depth)?)),
                    radicand: Box::new(parse_presentation_node(radicand, parser_depth)?),
                },
            )))
        }
        "msub" | "msup" | "msubsup" => parse_presentation_script(node, parser_depth),
        "mfenced" => parse_fenced(node, parser_depth).map(PresentationItem::Node),
        "mover" | "munder" | "munderover" => parse_presentation_over_under(node, parser_depth),
        "mstyle" => {
            require_structural_text(node)?;
            if node.children.len() != 1 {
                return Err(MathMlAdapterError::InvalidStructure);
            }
            let style = parse_style(node)?.ok_or(MathMlAdapterError::UnsupportedAttribute)?;
            let mut child = parse_presentation_node(&node.children[0], parser_depth)?;
            if child.style.is_some() {
                return Err(MathMlAdapterError::UnsupportedAttribute);
            }
            child.style = Some(style);
            child.span = node.span;
            Ok(PresentationItem::Node(child))
        }
        "mtable" => parse_presentation_matrix(node, parser_depth).map(PresentationItem::Node),
        _ => Err(MathMlAdapterError::UnsupportedElement),
    }
}

fn parse_presentation_leaf(node: &XmlElement) -> Result<PresentationItem, MathMlAdapterError> {
    match node.local_name.as_str() {
        "mn" => {
            let value = require_leaf_text(node)?.to_owned();
            Ok(PresentationItem::Node(styled_leaf(
                node,
                MathExpression::Number { value },
            )?))
        }
        "mi" => {
            let value = require_leaf_text(node)?;
            let expression = symbol_from_text(value).map_or_else(
                || MathExpression::Identifier {
                    name: value.to_owned(),
                },
                |symbol| MathExpression::Symbol { symbol },
            );
            Ok(PresentationItem::Node(styled_leaf(node, expression)?))
        }
        "mtext" => {
            if !node.children.is_empty()
                || node.text.is_empty()
                || node.text.chars().any(char::is_control)
            {
                return Err(MathMlAdapterError::InvalidToken);
            }
            Ok(PresentationItem::Node(styled_leaf(
                node,
                MathExpression::Text {
                    value: node.text.clone(),
                },
            )?))
        }
        "mo" => parse_operator_item(node),
        _ => Err(MathMlAdapterError::UnsupportedElement),
    }
}

fn parse_presentation_node(
    node: &XmlElement,
    parser_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    match parse_presentation_item(node, parser_depth)? {
        PresentationItem::Node(node) => Ok(node),
        _ => Err(MathMlAdapterError::InvalidStructure),
    }
}

fn parse_operator_item(node: &XmlElement) -> Result<PresentationItem, MathMlAdapterError> {
    require_attributes(node, &[])?;
    let value = require_leaf_text(node)?;
    if let Some(symbol) = symbol_from_text(value) {
        return Ok(PresentationItem::Node(make_node(
            node.span,
            MathExpression::Symbol { symbol },
        )));
    }
    let item = match value {
        "+" => PresentationItem::Infix(MathOperator::Add, 30),
        "−" | "-" => PresentationItem::Infix(MathOperator::Subtract, 30),
        "×" | "·" | "⁢" => PresentationItem::Infix(MathOperator::Multiply, 40),
        "/" | "÷" => PresentationItem::Infix(MathOperator::Divide, 40),
        "=" => PresentationItem::Infix(MathOperator::Equal, 20),
        "≠" => PresentationItem::Infix(MathOperator::NotEqual, 20),
        "<" => PresentationItem::Infix(MathOperator::LessThan, 20),
        "≤" => PresentationItem::Infix(MathOperator::LessThanOrEqual, 20),
        ">" => PresentationItem::Infix(MathOperator::GreaterThan, 20),
        "≥" => PresentationItem::Infix(MathOperator::GreaterThanOrEqual, 20),
        "≈" => PresentationItem::Infix(MathOperator::ApproximatelyEqual, 20),
        "∝" => PresentationItem::Infix(MathOperator::ProportionalTo, 20),
        "∧" => PresentationItem::Infix(MathOperator::LogicalAnd, 15),
        "∨" => PresentationItem::Infix(MathOperator::LogicalOr, 10),
        "⇒" => PresentationItem::Infix(MathOperator::Implies, 8),
        "⇔" => PresentationItem::Infix(MathOperator::Equivalent, 8),
        "∈" => PresentationItem::Infix(MathOperator::ElementOf, 20),
        "∉" => PresentationItem::Infix(MathOperator::NotElementOf, 20),
        "⊆" => PresentationItem::Infix(MathOperator::SubsetOf, 20),
        "⊂" => PresentationItem::Infix(MathOperator::ProperSubsetOf, 20),
        "⊇" => PresentationItem::Infix(MathOperator::SupersetOf, 20),
        "⊃" => PresentationItem::Infix(MathOperator::ProperSupersetOf, 20),
        "∪" => PresentationItem::Infix(MathOperator::Union, 25),
        "∩" => PresentationItem::Infix(MathOperator::Intersection, 25),
        "∖" => PresentationItem::Infix(MathOperator::SetDifference, 25),
        "∘" => PresentationItem::Infix(MathOperator::Compose, 40),
        "¬" => PresentationItem::Prefix(MathOperator::LogicalNot),
        "!" => PresentationItem::Factorial,
        "⁡" => PresentationItem::FunctionApply,
        _ => return Err(MathMlAdapterError::InvalidToken),
    };
    Ok(item)
}

fn parse_presentation_script(
    node: &XmlElement,
    parser_depth: usize,
) -> Result<PresentationItem, MathMlAdapterError> {
    require_attributes(node, &[])?;
    require_structural_text(node)?;
    let required = if node.local_name == "msubsup" { 3 } else { 2 };
    if node.children.len() != required {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    if let Some(operator) = large_operator_marker(&node.children[0])? {
        let (lower, upper) = match node.local_name.as_str() {
            "msub" => (
                Some(Box::new(parse_presentation_node(
                    &node.children[1],
                    parser_depth,
                )?)),
                None,
            ),
            "msup" => (
                None,
                Some(Box::new(parse_presentation_node(
                    &node.children[1],
                    parser_depth,
                )?)),
            ),
            _ => (
                Some(Box::new(parse_presentation_node(
                    &node.children[1],
                    parser_depth,
                )?)),
                Some(Box::new(parse_presentation_node(
                    &node.children[2],
                    parser_depth,
                )?)),
            ),
        };
        return Ok(PresentationItem::LargeHead {
            operator,
            lower,
            upper,
            span: node.span,
        });
    }
    let base = parse_presentation_node(&node.children[0], parser_depth)?;
    let (subscript, superscript) = match node.local_name.as_str() {
        "msub" => (
            Some(Box::new(parse_presentation_node(
                &node.children[1],
                parser_depth,
            )?)),
            None,
        ),
        "msup" => (
            None,
            Some(Box::new(parse_presentation_node(
                &node.children[1],
                parser_depth,
            )?)),
        ),
        _ => (
            Some(Box::new(parse_presentation_node(
                &node.children[1],
                parser_depth,
            )?)),
            Some(Box::new(parse_presentation_node(
                &node.children[2],
                parser_depth,
            )?)),
        ),
    };
    Ok(PresentationItem::Node(make_node(
        node.span,
        MathExpression::Script {
            base: Box::new(base),
            subscript,
            superscript,
        },
    )))
}

fn parse_fenced(node: &XmlElement, parser_depth: usize) -> Result<MathNode, MathMlAdapterError> {
    require_attributes(node, &["open", "close"])?;
    require_structural_text(node)?;
    let open = node.attributes.get("open").map_or("(", String::as_str);
    let close = node.attributes.get("close").map_or(")", String::as_str);
    let left = left_delimiter(open)?;
    let right = right_delimiter(close)?;
    let body = parse_presentation_children(&node.children, node.span, parser_depth)?;
    Ok(make_node(
        node.span,
        MathExpression::Delimited {
            left,
            body: Box::new(body),
            right,
        },
    ))
}

fn left_delimiter(value: &str) -> Result<MathDelimiter, MathMlAdapterError> {
    match value {
        "(" => Ok(MathDelimiter::LeftParenthesis),
        "[" => Ok(MathDelimiter::LeftBracket),
        "{" => Ok(MathDelimiter::LeftBrace),
        "⟨" => Ok(MathDelimiter::LeftAngle),
        "|" => Ok(MathDelimiter::VerticalBar),
        "‖" => Ok(MathDelimiter::DoubleVerticalBar),
        "⌊" => Ok(MathDelimiter::LeftFloor),
        "⌈" => Ok(MathDelimiter::LeftCeiling),
        "" => Ok(MathDelimiter::None),
        _ => Err(MathMlAdapterError::UnsupportedAttribute),
    }
}

fn right_delimiter(value: &str) -> Result<MathDelimiter, MathMlAdapterError> {
    match value {
        ")" => Ok(MathDelimiter::RightParenthesis),
        "]" => Ok(MathDelimiter::RightBracket),
        "}" => Ok(MathDelimiter::RightBrace),
        "⟩" => Ok(MathDelimiter::RightAngle),
        "|" => Ok(MathDelimiter::VerticalBar),
        "‖" => Ok(MathDelimiter::DoubleVerticalBar),
        "⌋" => Ok(MathDelimiter::RightFloor),
        "⌉" => Ok(MathDelimiter::RightCeiling),
        "" => Ok(MathDelimiter::None),
        _ => Err(MathMlAdapterError::UnsupportedAttribute),
    }
}

fn parse_presentation_over_under(
    node: &XmlElement,
    parser_depth: usize,
) -> Result<PresentationItem, MathMlAdapterError> {
    require_structural_text(node)?;
    let required = if node.local_name == "munderover" {
        3
    } else {
        2
    };
    if node.children.len() != required {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    if let Some(operator) = large_operator_marker(&node.children[0])? {
        return parse_over_under_large_head(node, operator, parser_depth);
    }
    let base = parse_presentation_node(&node.children[0], parser_depth)?;
    let marker_index = if node.local_name == "munderover" {
        2
    } else {
        1
    };
    let marker = leaf_operator_text(&node.children[marker_index])?;
    let is_accent = match node.local_name.as_str() {
        "mover" => {
            require_attributes(node, &["accent"])?;
            parse_boolean_attribute(node, "accent")?
                .ok_or(MathMlAdapterError::UnsupportedAttribute)?
        }
        "munder" => {
            require_attributes(node, &["accentunder"])?;
            parse_boolean_attribute(node, "accentunder")?
                .ok_or(MathMlAdapterError::UnsupportedAttribute)?
        }
        _ => return Err(MathMlAdapterError::UnsupportedElement),
    };
    if is_accent && node.local_name == "mover" {
        let accent = match marker {
            "→" => MathAccent::VectorArrow,
            "^" | "ˆ" => MathAccent::Hat,
            "¯" => MathAccent::Bar,
            "~" | "˜" => MathAccent::Tilde,
            "˙" => MathAccent::Dot,
            "¨" => MathAccent::DoubleDot,
            "ˇ" => MathAccent::Check,
            "´" => MathAccent::Acute,
            "`" => MathAccent::Grave,
            _ => return Err(MathMlAdapterError::InvalidToken),
        };
        return Ok(PresentationItem::Node(make_node(
            node.span,
            MathExpression::Accent {
                accent,
                base: Box::new(base),
            },
        )));
    }
    let annotation_kind = match (node.local_name.as_str(), marker) {
        ("mover", "⏞") => MathAnnotationKind::OverBrace,
        ("munder", "⏟") => MathAnnotationKind::UnderBrace,
        ("mover", "¯") => MathAnnotationKind::OverLine,
        ("munder", "_") => MathAnnotationKind::UnderLine,
        ("mover", "→") => MathAnnotationKind::OverArrow,
        ("munder", "→") => MathAnnotationKind::UnderArrow,
        _ => return Err(MathMlAdapterError::InvalidToken),
    };
    Ok(PresentationItem::Node(make_node(
        node.span,
        MathExpression::Annotated {
            annotation_kind,
            base: Box::new(base),
            annotation: None,
        },
    )))
}

fn parse_over_under_large_head(
    node: &XmlElement,
    operator: MathLargeOperator,
    parser_depth: usize,
) -> Result<PresentationItem, MathMlAdapterError> {
    require_attributes(node, &[])?;
    let (lower, upper) = match node.local_name.as_str() {
        "munder" => (
            Some(Box::new(parse_presentation_node(
                &node.children[1],
                parser_depth,
            )?)),
            None,
        ),
        "mover" => (
            None,
            Some(Box::new(parse_presentation_node(
                &node.children[1],
                parser_depth,
            )?)),
        ),
        "munderover" => (
            Some(Box::new(parse_presentation_node(
                &node.children[1],
                parser_depth,
            )?)),
            Some(Box::new(parse_presentation_node(
                &node.children[2],
                parser_depth,
            )?)),
        ),
        _ => return Err(MathMlAdapterError::UnsupportedElement),
    };
    Ok(PresentationItem::LargeHead {
        operator,
        lower,
        upper,
        span: node.span,
    })
}

fn parse_boolean_attribute(
    node: &XmlElement,
    name: &str,
) -> Result<Option<bool>, MathMlAdapterError> {
    node.attributes
        .get(name)
        .map(|value| match value.as_str() {
            "true" => Ok(true),
            "false" => Ok(false),
            _ => Err(MathMlAdapterError::UnsupportedAttribute),
        })
        .transpose()
}

fn leaf_operator_text(node: &XmlElement) -> Result<&str, MathMlAdapterError> {
    if node.local_name != "mo" {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    require_attributes(node, &[])?;
    require_leaf_text(node)
}

fn large_operator_marker(
    node: &XmlElement,
) -> Result<Option<MathLargeOperator>, MathMlAdapterError> {
    let value = if matches!(node.local_name.as_str(), "mo" | "mi") {
        require_attributes(node, &[])?;
        require_leaf_text(node)?
    } else {
        return Ok(None);
    };
    Ok(match value {
        "∑" => Some(MathLargeOperator::Sum),
        "∏" => Some(MathLargeOperator::Product),
        "lim" => Some(MathLargeOperator::Limit),
        "∫" => Some(MathLargeOperator::Integral {
            multiplicity: 1,
            contour: false,
        }),
        "∬" => Some(MathLargeOperator::Integral {
            multiplicity: 2,
            contour: false,
        }),
        "∭" => Some(MathLargeOperator::Integral {
            multiplicity: 3,
            contour: false,
        }),
        "∮" => Some(MathLargeOperator::Integral {
            multiplicity: 1,
            contour: true,
        }),
        _ => None,
    })
}

fn parse_presentation_matrix(
    node: &XmlElement,
    parser_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    require_attributes(node, &[])?;
    require_structural_text(node)?;
    if node.children.is_empty() {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    let mut rows = Vec::new();
    let mut width = None;
    for row in &node.children {
        if row.local_name != "mtr" {
            return Err(MathMlAdapterError::InvalidStructure);
        }
        require_attributes(row, &[])?;
        require_structural_text(row)?;
        if row.children.is_empty() {
            return Err(MathMlAdapterError::InvalidStructure);
        }
        let mut cells = Vec::new();
        for cell in &row.children {
            if cell.local_name != "mtd" {
                return Err(MathMlAdapterError::InvalidStructure);
            }
            require_attributes(cell, &[])?;
            require_structural_text(cell)?;
            cells.push(parse_presentation_children(
                &cell.children,
                cell.span,
                parser_depth,
            )?);
        }
        if width
            .replace(cells.len())
            .is_some_and(|expected| expected != cells.len())
        {
            return Err(MathMlAdapterError::InvalidStructure);
        }
        rows.push(cells);
    }
    Ok(make_node(
        node.span,
        MathExpression::Matrix {
            matrix_kind: MathMatrixKind::Plain,
            rows,
        },
    ))
}

struct PresentationParser<'a> {
    items: &'a [PresentationItem],
    index: usize,
    depth: usize,
    max_depth: usize,
}

impl<'a> PresentationParser<'a> {
    fn new(items: &'a [PresentationItem], max_depth: usize) -> Self {
        Self {
            items,
            index: 0,
            depth: 0,
            max_depth,
        }
    }

    fn parse(mut self, span: MathSourceSpan) -> Result<MathNode, MathMlAdapterError> {
        let mut root = self.parse_expression(0)?;
        if self.index != self.items.len() {
            return Err(MathMlAdapterError::AmbiguousPresentation);
        }
        root.span = span;
        Ok(root)
    }

    fn parse_expression(&mut self, minimum: u8) -> Result<MathNode, MathMlAdapterError> {
        if self.depth >= self.max_depth {
            return Err(MathMlAdapterError::XmlLimit);
        }
        self.depth += 1;
        let result = self.parse_expression_inner(minimum);
        self.depth -= 1;
        result
    }

    fn parse_expression_inner(&mut self, minimum: u8) -> Result<MathNode, MathMlAdapterError> {
        let mut left = self.parse_prefix()?;
        loop {
            match self.items.get(self.index) {
                Some(PresentationItem::Factorial) => {
                    self.index += 1;
                    let span = left.span;
                    left = make_apply(span, MathOperator::Factorial, vec![left]);
                }
                Some(PresentationItem::FunctionApply) => {
                    if 50 < minimum {
                        break;
                    }
                    self.index += 1;
                    let name = match &left.expression {
                        MathExpression::Identifier { name } => name.clone(),
                        _ => return Err(MathMlAdapterError::AmbiguousPresentation),
                    };
                    let argument = self.parse_expression(51)?;
                    let argument = unwrap_parenthesized(argument);
                    left = make_node(
                        left.span,
                        MathExpression::Function {
                            function: function_from_name(name),
                            arguments: vec![argument],
                        },
                    );
                }
                Some(PresentationItem::Infix(operator, precedence)) => {
                    if *precedence < minimum {
                        break;
                    }
                    if is_relation(*operator) && relation_root(&left) {
                        return Err(MathMlAdapterError::AmbiguousPresentation);
                    }
                    let operator = *operator;
                    let precedence = *precedence;
                    self.index += 1;
                    let right = self.parse_expression(precedence + 1)?;
                    let span = merged_span(left.span, right.span);
                    left = make_apply(span, operator, vec![left, right]);
                }
                Some(PresentationItem::Node(_) | PresentationItem::LargeHead { .. }) => {
                    return Err(MathMlAdapterError::AmbiguousPresentation);
                }
                Some(PresentationItem::Prefix(_)) => {
                    return Err(MathMlAdapterError::InvalidStructure);
                }
                None => break,
            }
        }
        Ok(left)
    }

    fn parse_prefix(&mut self) -> Result<MathNode, MathMlAdapterError> {
        match self.items.get(self.index).cloned() {
            Some(PresentationItem::Prefix(operator)) => {
                self.index += 1;
                let argument = self.parse_expression(50)?;
                let span = argument.span;
                Ok(make_apply(span, operator, vec![argument]))
            }
            Some(PresentationItem::Infix(MathOperator::Add, _)) => {
                self.index += 1;
                let argument = self.parse_expression(50)?;
                let span = argument.span;
                Ok(make_apply(span, MathOperator::Positive, vec![argument]))
            }
            Some(PresentationItem::Infix(MathOperator::Subtract, _)) => {
                self.index += 1;
                let argument = self.parse_expression(50)?;
                let span = argument.span;
                Ok(make_apply(span, MathOperator::Negative, vec![argument]))
            }
            Some(PresentationItem::Node(node)) => {
                self.index += 1;
                Ok(node)
            }
            Some(PresentationItem::LargeHead {
                operator,
                lower,
                upper,
                span,
            }) => {
                self.index += 1;
                let body = self.parse_expression(60)?;
                Ok(make_node(
                    merged_span(span, body.span),
                    MathExpression::LargeOperator {
                        operator,
                        body: Box::new(body),
                        lower,
                        upper,
                    },
                ))
            }
            _ => Err(MathMlAdapterError::InvalidStructure),
        }
    }
}

fn unwrap_parenthesized(node: MathNode) -> MathNode {
    let MathNode {
        span,
        style,
        expression,
    } = node;
    match expression {
        MathExpression::Delimited {
            left: MathDelimiter::LeftParenthesis,
            body,
            right: MathDelimiter::RightParenthesis,
        } if style.is_none() => *body,
        expression => MathNode {
            span,
            style,
            expression,
        },
    }
}

fn parse_content(
    node: &XmlElement,
    depth: usize,
    max_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    if depth > max_depth {
        return Err(MathMlAdapterError::XmlLimit);
    }
    match node.local_name.as_str() {
        "cn" => {
            require_attributes(node, &[])?;
            let value = require_leaf_text(node)?.to_owned();
            Ok(make_node(node.span, MathExpression::Number { value }))
        }
        "ci" => {
            require_attributes(node, &[])?;
            let value = require_leaf_text(node)?;
            let expression = symbol_from_text(value).map_or_else(
                || MathExpression::Identifier {
                    name: value.to_owned(),
                },
                |symbol| MathExpression::Symbol { symbol },
            );
            Ok(make_node(node.span, expression))
        }
        "cs" => {
            require_attributes(node, &[])?;
            if !node.children.is_empty()
                || node.text.is_empty()
                || node.text.chars().any(char::is_control)
            {
                return Err(MathMlAdapterError::InvalidToken);
            }
            Ok(make_node(
                node.span,
                MathExpression::Text {
                    value: node.text.clone(),
                },
            ))
        }
        "infinity" | "emptyset" | "pi" => {
            require_empty(node)?;
            let symbol = match node.local_name.as_str() {
                "infinity" => MathSymbol::Infinity,
                "emptyset" => MathSymbol::EmptySet,
                _ => MathSymbol::Greek {
                    letter: MathGreekLetter::Pi,
                    letter_case: MathLetterCase::Lower,
                },
            };
            Ok(make_node(node.span, MathExpression::Symbol { symbol }))
        }
        "apply" => parse_content_apply(node, depth + 1, max_depth),
        "matrix" => parse_content_matrix(node, depth + 1, max_depth),
        "set" => parse_content_set(node, depth + 1, max_depth),
        _ => Err(MathMlAdapterError::UnsupportedElement),
    }
}

fn parse_content_apply(
    node: &XmlElement,
    depth: usize,
    max_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    require_attributes(node, &[])?;
    require_structural_text(node)?;
    let (operator, tail) = node
        .children
        .split_first()
        .ok_or(MathMlAdapterError::InvalidStructure)?;
    require_empty(operator)?;
    match operator.local_name.as_str() {
        "root" => parse_content_root(node.span, tail, depth, max_depth),
        "sum" | "product" | "limit" | "int" => parse_content_large(
            node.span,
            operator.local_name.as_str(),
            tail,
            depth,
            max_depth,
        ),
        "diff" | "partialdiff" => parse_content_derivative(
            node.span,
            operator.local_name.as_str(),
            tail,
            depth,
            max_depth,
        ),
        "divide" => {
            let [numerator, denominator] = tail else {
                return Err(MathMlAdapterError::InvalidStructure);
            };
            Ok(make_node(
                node.span,
                MathExpression::Fraction {
                    numerator: Box::new(parse_content(numerator, depth, max_depth)?),
                    denominator: Box::new(parse_content(denominator, depth, max_depth)?),
                },
            ))
        }
        "power" => {
            let [base, exponent] = tail else {
                return Err(MathMlAdapterError::InvalidStructure);
            };
            Ok(make_node(
                node.span,
                MathExpression::Script {
                    base: Box::new(parse_content(base, depth, max_depth)?),
                    subscript: None,
                    superscript: Some(Box::new(parse_content(exponent, depth, max_depth)?)),
                },
            ))
        }
        "minus" => {
            let arguments = parse_content_arguments(tail, depth, max_depth)?;
            let operator = match arguments.len() {
                1 => MathOperator::Negative,
                2 => MathOperator::Subtract,
                _ => return Err(MathMlAdapterError::InvalidStructure),
            };
            Ok(make_apply(node.span, operator, arguments))
        }
        name if content_function(name).is_some() => {
            if tail.is_empty() {
                return Err(MathMlAdapterError::InvalidStructure);
            }
            let arguments = parse_content_arguments(tail, depth, max_depth)?;
            Ok(make_node(
                node.span,
                MathExpression::Function {
                    function: content_function(name)
                        .ok_or(MathMlAdapterError::UnsupportedElement)?,
                    arguments,
                },
            ))
        }
        name if content_operator(name).is_some() => {
            let operator = content_operator(name).ok_or(MathMlAdapterError::UnsupportedElement)?;
            let arguments = parse_content_arguments(tail, depth, max_depth)?;
            if !valid_operator_arity(operator, arguments.len()) {
                return Err(MathMlAdapterError::InvalidStructure);
            }
            Ok(make_apply(node.span, operator, arguments))
        }
        _ => Err(MathMlAdapterError::UnsupportedElement),
    }
}

fn parse_content_arguments(
    nodes: &[XmlElement],
    depth: usize,
    max_depth: usize,
) -> Result<Vec<MathNode>, MathMlAdapterError> {
    let mut output = Vec::new();
    for node in nodes {
        output.push(parse_content(node, depth, max_depth)?);
    }
    Ok(output)
}

fn parse_content_root(
    span: MathSourceSpan,
    children: &[XmlElement],
    depth: usize,
    max_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    let (degree, radicand) = if let [radicand] = children {
        (None, radicand)
    } else if let [degree, radicand] = children {
        if degree.local_name != "degree" {
            return Err(MathMlAdapterError::InvalidStructure);
        }
        require_attributes(degree, &[])?;
        require_structural_text(degree)?;
        let [value] = degree.children.as_slice() else {
            return Err(MathMlAdapterError::InvalidStructure);
        };
        (
            Some(Box::new(parse_content(value, depth, max_depth)?)),
            radicand,
        )
    } else {
        return Err(MathMlAdapterError::InvalidStructure);
    };
    Ok(make_node(
        span,
        MathExpression::Root {
            degree,
            radicand: Box::new(parse_content(radicand, depth, max_depth)?),
        },
    ))
}

fn parse_content_large(
    span: MathSourceSpan,
    name: &str,
    children: &[XmlElement],
    depth: usize,
    max_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    let mut index = 0usize;
    let lower = if children
        .get(index)
        .is_some_and(|child| child.local_name == "lowlimit")
    {
        let value = Box::new(parse_qualifier(&children[index], depth, max_depth)?);
        index += 1;
        Some(value)
    } else {
        None
    };
    let upper = if children
        .get(index)
        .is_some_and(|child| child.local_name == "uplimit")
    {
        let value = Box::new(parse_qualifier(&children[index], depth, max_depth)?);
        index += 1;
        Some(value)
    } else {
        None
    };
    if children.len() != index + 1 {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    let body = Box::new(parse_content(&children[index], depth, max_depth)?);
    let operator = match name {
        "sum" => MathLargeOperator::Sum,
        "product" => MathLargeOperator::Product,
        "limit" => MathLargeOperator::Limit,
        "int" => MathLargeOperator::Integral {
            multiplicity: 1,
            contour: false,
        },
        _ => return Err(MathMlAdapterError::UnsupportedElement),
    };
    Ok(make_node(
        span,
        MathExpression::LargeOperator {
            operator,
            body,
            lower,
            upper,
        },
    ))
}

fn parse_qualifier(
    node: &XmlElement,
    depth: usize,
    max_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    require_attributes(node, &[])?;
    require_structural_text(node)?;
    let [value] = node.children.as_slice() else {
        return Err(MathMlAdapterError::InvalidStructure);
    };
    parse_content(value, depth, max_depth)
}

fn parse_content_derivative(
    span: MathSourceSpan,
    name: &str,
    children: &[XmlElement],
    depth: usize,
    max_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    let (body, variables) = children
        .split_last()
        .ok_or(MathMlAdapterError::InvalidStructure)?;
    if variables.is_empty() || variables.iter().any(|node| node.local_name != "bvar") {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    let mut parsed_variables = Vec::new();
    for variable in variables {
        require_attributes(variable, &[])?;
        require_structural_text(variable)?;
        let (variable_node, order) = match variable.children.as_slice() {
            [value] => (value, 1),
            [value, degree] if degree.local_name == "degree" => {
                require_attributes(degree, &[])?;
                require_structural_text(degree)?;
                let [number] = degree.children.as_slice() else {
                    return Err(MathMlAdapterError::InvalidStructure);
                };
                if number.local_name != "cn" {
                    return Err(MathMlAdapterError::InvalidStructure);
                }
                let order = require_leaf_text(number)?
                    .parse::<u16>()
                    .ok()
                    .filter(|order| *order > 0)
                    .ok_or(MathMlAdapterError::InvalidToken)?;
                (value, order)
            }
            _ => return Err(MathMlAdapterError::InvalidStructure),
        };
        parsed_variables.push(MathDerivativeVariable {
            variable: Box::new(parse_content(variable_node, depth, max_depth)?),
            order,
        });
    }
    Ok(make_node(
        span,
        MathExpression::Derivative {
            derivative_kind: if name == "partialdiff" {
                MathDerivativeKind::Partial
            } else {
                MathDerivativeKind::Ordinary
            },
            expression: Box::new(parse_content(body, depth, max_depth)?),
            variables: parsed_variables,
        },
    ))
}

fn parse_content_matrix(
    node: &XmlElement,
    depth: usize,
    max_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    require_attributes(node, &[])?;
    require_structural_text(node)?;
    if node.children.is_empty() {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    let mut rows = Vec::new();
    let mut width = None;
    for row in &node.children {
        if row.local_name != "matrixrow" {
            return Err(MathMlAdapterError::InvalidStructure);
        }
        require_attributes(row, &[])?;
        require_structural_text(row)?;
        if row.children.is_empty() {
            return Err(MathMlAdapterError::InvalidStructure);
        }
        let cells = parse_content_arguments(&row.children, depth, max_depth)?;
        if width
            .replace(cells.len())
            .is_some_and(|expected| expected != cells.len())
        {
            return Err(MathMlAdapterError::InvalidStructure);
        }
        rows.push(cells);
    }
    Ok(make_node(
        node.span,
        MathExpression::Matrix {
            matrix_kind: MathMatrixKind::Plain,
            rows,
        },
    ))
}

fn parse_content_set(
    node: &XmlElement,
    depth: usize,
    max_depth: usize,
) -> Result<MathNode, MathMlAdapterError> {
    require_attributes(node, &[])?;
    require_structural_text(node)?;
    let [variable, condition] = node.children.as_slice() else {
        return Err(MathMlAdapterError::InvalidStructure);
    };
    if variable.local_name != "bvar" || condition.local_name != "condition" {
        return Err(MathMlAdapterError::InvalidStructure);
    }
    let element = parse_qualifier(variable, depth, max_depth)?;
    let condition = parse_qualifier(condition, depth, max_depth)?;
    Ok(make_node(
        node.span,
        MathExpression::SetBuilder {
            element: Box::new(element),
            condition: Box::new(condition),
        },
    ))
}

fn content_operator(name: &str) -> Option<MathOperator> {
    match name {
        "plus" => Some(MathOperator::Add),
        "times" => Some(MathOperator::Multiply),
        "factorial" => Some(MathOperator::Factorial),
        "eq" => Some(MathOperator::Equal),
        "neq" => Some(MathOperator::NotEqual),
        "lt" => Some(MathOperator::LessThan),
        "leq" => Some(MathOperator::LessThanOrEqual),
        "gt" => Some(MathOperator::GreaterThan),
        "geq" => Some(MathOperator::GreaterThanOrEqual),
        "approx" => Some(MathOperator::ApproximatelyEqual),
        "and" => Some(MathOperator::LogicalAnd),
        "or" => Some(MathOperator::LogicalOr),
        "not" => Some(MathOperator::LogicalNot),
        "implies" => Some(MathOperator::Implies),
        "equivalent" => Some(MathOperator::Equivalent),
        "in" => Some(MathOperator::ElementOf),
        "notin" => Some(MathOperator::NotElementOf),
        "subset" => Some(MathOperator::SubsetOf),
        "prsubset" => Some(MathOperator::ProperSubsetOf),
        "union" => Some(MathOperator::Union),
        "intersect" => Some(MathOperator::Intersection),
        "setdiff" => Some(MathOperator::SetDifference),
        "compose" => Some(MathOperator::Compose),
        _ => None,
    }
}

fn valid_operator_arity(operator: MathOperator, count: usize) -> bool {
    match operator {
        MathOperator::Positive
        | MathOperator::Negative
        | MathOperator::Factorial
        | MathOperator::LogicalNot => count == 1,
        MathOperator::Add
        | MathOperator::Multiply
        | MathOperator::LogicalAnd
        | MathOperator::LogicalOr
        | MathOperator::Union
        | MathOperator::Intersection => count >= 2,
        _ => count == 2,
    }
}

fn content_function(name: &str) -> Option<MathFunction> {
    match name {
        "sin" => Some(MathFunction::Sin),
        "cos" => Some(MathFunction::Cos),
        "tan" => Some(MathFunction::Tan),
        "cot" => Some(MathFunction::Cot),
        "sec" => Some(MathFunction::Sec),
        "csc" => Some(MathFunction::Csc),
        "arcsin" => Some(MathFunction::Arcsin),
        "arccos" => Some(MathFunction::Arccos),
        "arctan" => Some(MathFunction::Arctan),
        "sinh" => Some(MathFunction::Sinh),
        "cosh" => Some(MathFunction::Cosh),
        "tanh" => Some(MathFunction::Tanh),
        "log" => Some(MathFunction::Log),
        "ln" => Some(MathFunction::NaturalLog),
        "exp" => Some(MathFunction::Exponential),
        "min" => Some(MathFunction::Minimum),
        "max" => Some(MathFunction::Maximum),
        _ => None,
    }
}

fn function_from_name(name: String) -> MathFunction {
    content_function(&name).unwrap_or(MathFunction::Named { name })
}

const fn is_relation(operator: MathOperator) -> bool {
    matches!(
        operator,
        MathOperator::Equal
            | MathOperator::NotEqual
            | MathOperator::LessThan
            | MathOperator::LessThanOrEqual
            | MathOperator::GreaterThan
            | MathOperator::GreaterThanOrEqual
            | MathOperator::ApproximatelyEqual
            | MathOperator::ProportionalTo
            | MathOperator::ElementOf
            | MathOperator::NotElementOf
            | MathOperator::SubsetOf
            | MathOperator::ProperSubsetOf
            | MathOperator::SupersetOf
            | MathOperator::ProperSupersetOf
    )
}

fn relation_root(node: &MathNode) -> bool {
    matches!(
        node.expression,
        MathExpression::Apply { operator, .. } if is_relation(operator)
    )
}

const fn merged_span(left: MathSourceSpan, right: MathSourceSpan) -> MathSourceSpan {
    MathSourceSpan {
        start_byte: if left.start_byte < right.start_byte {
            left.start_byte
        } else {
            right.start_byte
        },
        end_byte: if left.end_byte > right.end_byte {
            left.end_byte
        } else {
            right.end_byte
        },
    }
}

fn symbol_from_text(value: &str) -> Option<MathSymbol> {
    let greek = match value {
        "α" => Some((MathGreekLetter::Alpha, MathLetterCase::Lower)),
        "β" => Some((MathGreekLetter::Beta, MathLetterCase::Lower)),
        "γ" => Some((MathGreekLetter::Gamma, MathLetterCase::Lower)),
        "δ" => Some((MathGreekLetter::Delta, MathLetterCase::Lower)),
        "ε" => Some((MathGreekLetter::Epsilon, MathLetterCase::Lower)),
        "ζ" => Some((MathGreekLetter::Zeta, MathLetterCase::Lower)),
        "η" => Some((MathGreekLetter::Eta, MathLetterCase::Lower)),
        "θ" => Some((MathGreekLetter::Theta, MathLetterCase::Lower)),
        "ι" => Some((MathGreekLetter::Iota, MathLetterCase::Lower)),
        "κ" => Some((MathGreekLetter::Kappa, MathLetterCase::Lower)),
        "λ" => Some((MathGreekLetter::Lambda, MathLetterCase::Lower)),
        "μ" => Some((MathGreekLetter::Mu, MathLetterCase::Lower)),
        "ν" => Some((MathGreekLetter::Nu, MathLetterCase::Lower)),
        "ξ" => Some((MathGreekLetter::Xi, MathLetterCase::Lower)),
        "ο" => Some((MathGreekLetter::Omicron, MathLetterCase::Lower)),
        "π" => Some((MathGreekLetter::Pi, MathLetterCase::Lower)),
        "ρ" => Some((MathGreekLetter::Rho, MathLetterCase::Lower)),
        "σ" => Some((MathGreekLetter::Sigma, MathLetterCase::Lower)),
        "τ" => Some((MathGreekLetter::Tau, MathLetterCase::Lower)),
        "υ" => Some((MathGreekLetter::Upsilon, MathLetterCase::Lower)),
        "φ" => Some((MathGreekLetter::Phi, MathLetterCase::Lower)),
        "χ" => Some((MathGreekLetter::Chi, MathLetterCase::Lower)),
        "ψ" => Some((MathGreekLetter::Psi, MathLetterCase::Lower)),
        "ω" => Some((MathGreekLetter::Omega, MathLetterCase::Lower)),
        "Γ" => Some((MathGreekLetter::Gamma, MathLetterCase::Upper)),
        "Δ" => Some((MathGreekLetter::Delta, MathLetterCase::Upper)),
        "Θ" => Some((MathGreekLetter::Theta, MathLetterCase::Upper)),
        "Λ" => Some((MathGreekLetter::Lambda, MathLetterCase::Upper)),
        "Ξ" => Some((MathGreekLetter::Xi, MathLetterCase::Upper)),
        "Π" => Some((MathGreekLetter::Pi, MathLetterCase::Upper)),
        "Σ" => Some((MathGreekLetter::Sigma, MathLetterCase::Upper)),
        "Υ" => Some((MathGreekLetter::Upsilon, MathLetterCase::Upper)),
        "Φ" => Some((MathGreekLetter::Phi, MathLetterCase::Upper)),
        "Ψ" => Some((MathGreekLetter::Psi, MathLetterCase::Upper)),
        "Ω" => Some((MathGreekLetter::Omega, MathLetterCase::Upper)),
        _ => None,
    };
    if let Some((letter, letter_case)) = greek {
        return Some(MathSymbol::Greek {
            letter,
            letter_case,
        });
    }
    match value {
        "∞" => Some(MathSymbol::Infinity),
        "∅" => Some(MathSymbol::EmptySet),
        "ℵ" => Some(MathSymbol::Aleph),
        "ℏ" => Some(MathSymbol::Hbar),
        "∂" => Some(MathSymbol::PartialDifferential),
        "∇" => Some(MathSymbol::Nabla),
        "∴" => Some(MathSymbol::Therefore),
        "∵" => Some(MathSymbol::Because),
        "…" => Some(MathSymbol::HorizontalEllipsis),
        "⋮" => Some(MathSymbol::VerticalEllipsis),
        "⋱" => Some(MathSymbol::DiagonalEllipsis),
        "°" => Some(MathSymbol::Degree),
        "′" => Some(MathSymbol::Prime),
        _ => None,
    }
}
