use std::fmt;

use domain_ir::{
    OBJECT_PROPERTIES_SCHEMA_VERSION, ObjectHyperlink, ObjectPropertiesBuilder,
    ObjectPropertiesError, ObjectPropertiesLimits, ObjectPropertiesPlan, ObjectPropertiesState,
    ObjectPropertyKind,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};

pub const OBJECT_HYPERLINK_HWPX_PROFILE_ID: &str =
    "hwpx-agent.object-hyperlink-hwpx.hwpml-2011-shape-component-root-href/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectHyperlinkHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub href_bytes: usize,
    pub output_bytes: usize,
    pub plan_bytes: usize,
}

impl Default for ObjectHyperlinkHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 65_536,
            href_bytes: 64 * 1024,
            output_bytes: 32 * 1024 * 1024,
            plan_bytes: 2 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ObjectHyperlinkHwpxLimits(ObjectHyperlinkHwpxLimitConfig);

impl ObjectHyperlinkHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_OBJECTS: usize = 262_144;
    pub const HARD_MAX_HREF_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_PLAN_BYTES: usize = 8 * 1024 * 1024;

    /// Creates finite exact-section limits without silently clamping values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding limits.
    pub fn new(config: ObjectHyperlinkHwpxLimitConfig) -> Result<Self, ObjectHyperlinkHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.href_bytes == 0
            || config.href_bytes > Self::HARD_MAX_HREF_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
        {
            return Err(ObjectHyperlinkHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectHyperlinkHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectHyperlinkHwpxReadback {
    pub state: ObjectPropertiesState,
    pub hyperlink: Option<ObjectHyperlink>,
    pub section_sha256: [u8; 32],
    pub object_sha256: [u8; 32],
    pub href_sha256: [u8; 32],
    pub object_ordinal: usize,
}

impl fmt::Debug for ObjectHyperlinkHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectHyperlinkHwpxReadback")
            .field("object_ordinal", &self.object_ordinal)
            .field("object_kind", &self.state.object_kind())
            .field("hyperlink_kind", &hyperlink_kind(self.hyperlink.as_ref()))
            .field("identity", &"<redacted>")
            .field("target", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct ObjectHyperlinkHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    object_ordinal: usize,
    source_section_sha256: [u8; 32],
    source_object_sha256: [u8; 32],
    source_href_sha256: [u8; 32],
    source_document_flow_sha256: String,
    domain_plan: ObjectPropertiesPlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl ObjectHyperlinkHwpxPlan {
    #[must_use]
    pub const fn object_ordinal(&self) -> usize {
        self.object_ordinal
    }

    #[must_use]
    pub const fn domain_plan(&self) -> &ObjectPropertiesPlan {
        &self.domain_plan
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Returns deterministic bounded JSON for the immutable HWPX plan.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: ObjectHyperlinkHwpxLimits,
    ) -> Result<Vec<u8>, ObjectHyperlinkHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectHyperlinkHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectHyperlinkHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("object_ordinal", &self.object_ordinal)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectHyperlinkHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_object_sha256: [u8; 32],
    pub output_object_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub modified_attribute_count: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for ObjectHyperlinkHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectHyperlinkHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("modified_attribute_count", &self.modified_attribute_count)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectHyperlinkHwpxError {
    #[error("object-hyperlink HWPX limits are invalid")]
    InvalidLimit,
    #[error("object-hyperlink HWPX section exceeds a finite limit")]
    InputLimit,
    #[error("object-hyperlink HWPX target is absent, duplicated, or unsupported")]
    UnsupportedObject,
    #[error("object-hyperlink HWPX attribute is malformed or ambiguous")]
    InvalidAttribute,
    #[error("object-hyperlink HWPX native identity is invalid")]
    InvalidIdentity,
    #[error("object-hyperlink HWPX value is unsupported or unsafe")]
    InvalidHyperlink,
    #[error("object-hyperlink HWPX section, object, state, or flow drifted")]
    SourceDrift,
    #[error("object-hyperlink HWPX plan was tampered with")]
    PlanTampered,
    #[error("object-hyperlink HWPX semantic readback differs")]
    ReadbackMismatch,
    #[error("object-hyperlink HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("object-hyperlink HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("object-hyperlink HWPX allocation failed")]
    AllocationFailed,
    #[error("object-hyperlink domain validation failed")]
    Domain(#[from] ObjectPropertiesError),
    #[error("object-hyperlink preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl ObjectHyperlinkHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_hyperlink_hwpx_invalid_limit",
            Self::InputLimit => "object_hyperlink_hwpx_input_limit",
            Self::UnsupportedObject => "object_hyperlink_hwpx_unsupported_object",
            Self::InvalidAttribute => "object_hyperlink_hwpx_invalid_attribute",
            Self::InvalidIdentity => "object_hyperlink_hwpx_invalid_identity",
            Self::InvalidHyperlink => "object_hyperlink_hwpx_invalid_hyperlink",
            Self::SourceDrift => "object_hyperlink_hwpx_source_drift",
            Self::PlanTampered => "object_hyperlink_hwpx_plan_tampered",
            Self::ReadbackMismatch => "object_hyperlink_hwpx_readback_mismatch",
            Self::PreservationMismatch => "object_hyperlink_hwpx_preservation_mismatch",
            Self::OutputLimit => "object_hyperlink_hwpx_output_limit",
            Self::AllocationFailed => "object_hyperlink_hwpx_allocation_failed",
            Self::Domain(_) => "object_hyperlink_hwpx_domain",
            Self::Preserving(_) => "object_hyperlink_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct ObjectHyperlinkHwpxReader;

impl ObjectHyperlinkHwpxReader {
    /// Reads one exact run-level common object against a complete expected state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, ambiguous, stale, or over-limit XML.
    pub fn read_in_section(
        source: &[u8],
        object_ordinal: usize,
        expected: &ObjectPropertiesState,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: ObjectHyperlinkHwpxLimits,
    ) -> Result<ObjectHyperlinkHwpxReadback, ObjectHyperlinkHwpxError> {
        let parsed = parse_selected(source, object_ordinal, state_limits, hwpx_limits)?;
        if expected.object_kind() != parsed.object_kind
            || expected.native_object_id() != parsed.native_object_id
            || expected.native_instance_id() != parsed.native_instance_id
            || expected.hyperlink() != parsed.hyperlink.as_ref()
        {
            return Err(ObjectHyperlinkHwpxError::SourceDrift);
        }
        Ok(ObjectHyperlinkHwpxReadback {
            state: expected.clone(),
            hyperlink: parsed.hyperlink,
            section_sha256: Sha256::digest(source).into(),
            object_sha256: parsed.object_sha256,
            href_sha256: parsed.href_sha256,
            object_ordinal,
        })
    }
}

#[derive(Debug)]
pub struct ObjectHyperlinkHwpxBuilder;

impl ObjectHyperlinkHwpxBuilder {
    /// Binds a validated hyperlink plan to one exact section/object href attribute.
    ///
    /// # Errors
    ///
    /// Rejects domain, source-state, flow, XML, or finite-limit drift.
    pub fn plan(
        source: &[u8],
        object_ordinal: usize,
        domain_plan: &ObjectPropertiesPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: ObjectHyperlinkHwpxLimits,
    ) -> Result<ObjectHyperlinkHwpxPlan, ObjectHyperlinkHwpxError> {
        if domain_plan.capability_id() != "obj.object_hyperlink"
            || domain_plan.source_document_flow_sha256() != current_document_flow_sha256
        {
            return Err(ObjectHyperlinkHwpxError::SourceDrift);
        }
        let readback = ObjectHyperlinkHwpxReader::read_in_section(
            source,
            object_ordinal,
            domain_plan.source_state(),
            state_limits,
            hwpx_limits,
        )?;
        let _ = ObjectPropertiesBuilder::build(
            domain_plan,
            domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        let domain_plan_sha256 = domain_plan.plan_sha256().to_owned();
        let mut plan = ObjectHyperlinkHwpxPlan {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION,
            profile_id: OBJECT_HYPERLINK_HWPX_PROFILE_ID,
            object_ordinal,
            source_section_sha256: readback.section_sha256,
            source_object_sha256: readback.object_sha256,
            source_href_sha256: readback.href_sha256,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            domain_plan: domain_plan.clone(),
            domain_plan_sha256,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, hwpx_limits)?;
        let _ = plan.canonical_json(hwpx_limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct ObjectHyperlinkHwpxLowerer;

impl ObjectHyperlinkHwpxLowerer {
    /// Revalidates and patches only the selected common object's href value span.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, state, flow, preservation, or readback drift.
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        plan: &ObjectHyperlinkHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: ObjectHyperlinkHwpxLimits,
    ) -> Result<(Vec<u8>, ObjectHyperlinkHwpxLoweringReceipt), ObjectHyperlinkHwpxError> {
        validate_plan(plan, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || current_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
            || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        {
            return Err(ObjectHyperlinkHwpxError::SourceDrift);
        }
        let source_readback = ObjectHyperlinkHwpxReader::read_in_section(
            source,
            plan.object_ordinal,
            plan.domain_plan.source_state(),
            state_limits,
            hwpx_limits,
        )?;
        if source_readback.object_sha256 != plan.source_object_sha256
            || source_readback.href_sha256 != plan.source_href_sha256
        {
            return Err(ObjectHyperlinkHwpxError::SourceDrift);
        }
        let result = ObjectPropertiesBuilder::build(
            &plan.domain_plan,
            plan.domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        let target_state = result.state;
        let parsed = parse_selected(source, plan.object_ordinal, state_limits, hwpx_limits)?;
        let replacement = escape_xml_attribute(&href_lexical(target_state.hyperlink()))?;
        if replacement.len() > hwpx_limits.0.href_bytes {
            return Err(ObjectHyperlinkHwpxError::OutputLimit);
        }
        let edit = ByteEdit {
            span: strict_attribute(element(&parsed.document, parsed.root)?, "href")?.value_span(),
            replacement: replacement.into_bytes(),
        };
        let output = apply_edit(source, &edit, hwpx_limits)?;
        verify_preservation(source, &output, &edit)?;
        let output_readback = ObjectHyperlinkHwpxReader::read_in_section(
            &output,
            plan.object_ordinal,
            &target_state,
            state_limits,
            hwpx_limits,
        )?;
        if output_readback.hyperlink.as_ref() != target_state.hyperlink() {
            return Err(ObjectHyperlinkHwpxError::ReadbackMismatch);
        }
        let receipt = ObjectHyperlinkHwpxLoweringReceipt {
            profile_id: OBJECT_HYPERLINK_HWPX_PROFILE_ID,
            capability_id: "obj.object_hyperlink",
            source_section_sha256: source_readback.section_sha256,
            output_section_sha256: output_readback.section_sha256,
            source_object_sha256: source_readback.object_sha256,
            output_object_sha256: output_readback.object_sha256,
            source_state_sha256: plan
                .domain_plan
                .source_state()
                .canonical_sha256(state_limits)?,
            target_state_sha256: target_state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            modified_attribute_count: 1,
            source_bytes: source.len(),
            output_bytes: output.len(),
        };
        Ok((output, receipt))
    }

    /// Returns preserving section bytes after the same fail-closed checks.
    ///
    /// # Errors
    ///
    /// Applies the same validation as [`Self::lower_in_section_with_receipt`].
    pub fn lower_in_section(
        source: &[u8],
        plan: &ObjectHyperlinkHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: ObjectHyperlinkHwpxLimits,
    ) -> Result<Vec<u8>, ObjectHyperlinkHwpxError> {
        Ok(Self::lower_in_section_with_receipt(
            source,
            plan,
            current_document_flow_sha256,
            state_limits,
            hwpx_limits,
        )?
        .0)
    }
}

struct ParsedObject {
    document: PreservingXmlDocument,
    root: usize,
    object_kind: ObjectPropertyKind,
    native_object_id: u32,
    native_instance_id: u32,
    hyperlink: Option<ObjectHyperlink>,
    object_sha256: [u8; 32],
    href_sha256: [u8; 32],
}

fn parse_selected(
    source: &[u8],
    object_ordinal: usize,
    state_limits: ObjectPropertiesLimits,
    limits: ObjectHyperlinkHwpxLimits,
) -> Result<ParsedObject, ObjectHyperlinkHwpxError> {
    if source.is_empty()
        || source.len() > limits.0.section_bytes
        || object_ordinal >= limits.0.objects
    {
        return Err(ObjectHyperlinkHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(ObjectHyperlinkHwpxError::InputLimit);
    }
    let root = selected_run_object(&document, object_ordinal, limits)?;
    let root_element = element(&document, root)?;
    let object_kind = object_kind(&document, root)?;
    let native_object_id = canonical_u32(source, strict_attribute(root_element, "id")?)?;
    let native_instance_id = canonical_u32(source, strict_attribute(root_element, "instid")?)?;
    if native_object_id == 0 || native_instance_id == 0 {
        return Err(ObjectHyperlinkHwpxError::InvalidIdentity);
    }
    let href_attribute = strict_attribute(root_element, "href")?;
    let raw = lexical_value(source, href_attribute)?;
    if raw.len() > limits.0.href_bytes {
        return Err(ObjectHyperlinkHwpxError::InputLimit);
    }
    let decoded = unescape(raw).map_err(|_| ObjectHyperlinkHwpxError::InvalidHyperlink)?;
    if decoded.len() > state_limits.config().text_bytes {
        return Err(ObjectHyperlinkHwpxError::InputLimit);
    }
    let hyperlink = parse_href(&decoded)?;
    Ok(ParsedObject {
        object_sha256: digest_span(source, outer_span(root_element)?)?,
        href_sha256: digest_span(source, href_attribute.value_span())?,
        document,
        root,
        object_kind,
        native_object_id,
        native_instance_id,
        hyperlink,
    })
}

fn parse_href(value: &str) -> Result<Option<ObjectHyperlink>, ObjectHyperlinkHwpxError> {
    if value.is_empty() {
        return Ok(None);
    }
    if value.starts_with("https://") {
        return Ok(Some(ObjectHyperlink::Https {
            uri: value.to_owned(),
        }));
    }
    if let Some(address) = value.strip_prefix("mailto:") {
        if address.is_empty() {
            return Err(ObjectHyperlinkHwpxError::InvalidHyperlink);
        }
        return Ok(Some(ObjectHyperlink::Mailto {
            address: address.to_owned(),
        }));
    }
    if let Some(name) = value.strip_prefix('#') {
        if name.is_empty() {
            return Err(ObjectHyperlinkHwpxError::InvalidHyperlink);
        }
        return Ok(Some(ObjectHyperlink::Bookmark {
            name: name.to_owned(),
        }));
    }
    Err(ObjectHyperlinkHwpxError::InvalidHyperlink)
}

fn href_lexical(value: Option<&ObjectHyperlink>) -> String {
    match value {
        None => String::new(),
        Some(ObjectHyperlink::Https { uri }) => uri.clone(),
        Some(ObjectHyperlink::Mailto { address }) => format!("mailto:{address}"),
        Some(ObjectHyperlink::Bookmark { name }) => format!("#{name}"),
    }
}

fn hyperlink_kind(value: Option<&ObjectHyperlink>) -> &'static str {
    match value {
        None => "none",
        Some(ObjectHyperlink::Https { .. }) => "https",
        Some(ObjectHyperlink::Mailto { .. }) => "mailto",
        Some(ObjectHyperlink::Bookmark { .. }) => "bookmark",
    }
}

fn object_kind(
    document: &PreservingXmlDocument,
    root: usize,
) -> Result<ObjectPropertyKind, ObjectHyperlinkHwpxError> {
    let element = element(document, root)?;
    match element.name().local_name() {
        "pic" => Ok(ObjectPropertyKind::Picture),
        "rect" => match direct_children_named(document, root, "drawText")?.len() {
            0 => Ok(ObjectPropertyKind::BasicShape),
            1 => Ok(ObjectPropertyKind::TextBox),
            _ => Err(ObjectHyperlinkHwpxError::UnsupportedObject),
        },
        "ellipse" | "line" | "arc" | "polygon" | "curve" | "connectLine" => {
            Ok(ObjectPropertyKind::BasicShape)
        }
        "container" => Ok(ObjectPropertyKind::DrawingCanvas),
        "ole" | "video" => Ok(ObjectPropertyKind::EmbeddedObject),
        _ => Err(ObjectHyperlinkHwpxError::UnsupportedObject),
    }
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

fn apply_edit(
    source: &[u8],
    edit: &ByteEdit,
    limits: ObjectHyperlinkHwpxLimits,
) -> Result<Vec<u8>, ObjectHyperlinkHwpxError> {
    if edit.span.end() > source.len() {
        return Err(ObjectHyperlinkHwpxError::UnsupportedObject);
    }
    let output_len = source
        .len()
        .checked_sub(edit.span.len())
        .and_then(|value| value.checked_add(edit.replacement.len()))
        .ok_or(ObjectHyperlinkHwpxError::OutputLimit)?;
    if output_len > limits.0.output_bytes {
        return Err(ObjectHyperlinkHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| ObjectHyperlinkHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..edit.span.start()]);
    output.extend_from_slice(&edit.replacement);
    output.extend_from_slice(&source[edit.span.end()..]);
    if output.len() != output_len {
        return Err(ObjectHyperlinkHwpxError::OutputLimit);
    }
    Ok(output)
}

fn verify_preservation(
    source: &[u8],
    output: &[u8],
    edit: &ByteEdit,
) -> Result<(), ObjectHyperlinkHwpxError> {
    let replacement_end = edit
        .span
        .start()
        .checked_add(edit.replacement.len())
        .ok_or(ObjectHyperlinkHwpxError::PreservationMismatch)?;
    if replacement_end > output.len()
        || source[..edit.span.start()] != output[..edit.span.start()]
        || edit.replacement != output[edit.span.start()..replacement_end]
        || source[edit.span.end()..] != output[replacement_end..]
    {
        return Err(ObjectHyperlinkHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn selected_run_object(
    document: &PreservingXmlDocument,
    ordinal: usize,
    limits: ObjectHyperlinkHwpxLimits,
) -> Result<usize, ObjectHyperlinkHwpxError> {
    let mut seen = 0_usize;
    for (index, candidate) in document.elements().iter().enumerate() {
        if !is_run_object(candidate) {
            continue;
        }
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(ObjectHyperlinkHwpxError::UnsupportedObject)?;
        if !has_name(parent, "run") {
            continue;
        }
        if seen == ordinal {
            return Ok(index);
        }
        seen = seen
            .checked_add(1)
            .ok_or(ObjectHyperlinkHwpxError::InputLimit)?;
        if seen > limits.0.objects {
            return Err(ObjectHyperlinkHwpxError::InputLimit);
        }
    }
    Err(ObjectHyperlinkHwpxError::UnsupportedObject)
}

fn is_run_object(element: &XmlElementToken) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS)
        && matches!(
            element.name().local_name(),
            "pic"
                | "rect"
                | "ellipse"
                | "line"
                | "arc"
                | "polygon"
                | "curve"
                | "connectLine"
                | "container"
                | "ole"
                | "video"
                | "textart"
        )
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, ObjectHyperlinkHwpxError> {
    let mut children = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let candidate = element(document, index)?;
        if has_name(candidate, local_name) {
            children
                .try_reserve(1)
                .map_err(|_| ObjectHyperlinkHwpxError::AllocationFailed)?;
            children.push(index);
        }
        child = candidate.next_sibling();
    }
    Ok(children)
}

fn strict_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, ObjectHyperlinkHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration() && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(ObjectHyperlinkHwpxError::InvalidAttribute)?;
    if value.name().namespace().is_some() || matches.next().is_some() {
        return Err(ObjectHyperlinkHwpxError::InvalidAttribute);
    }
    Ok(value)
}

fn lexical_value<'a>(
    source: &'a [u8],
    attribute: &XmlAttributeToken,
) -> Result<&'a str, ObjectHyperlinkHwpxError> {
    std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(ObjectHyperlinkHwpxError::InvalidAttribute)?,
    )
    .map_err(|_| ObjectHyperlinkHwpxError::InvalidAttribute)
}

fn canonical_u32(
    source: &[u8],
    attribute: &XmlAttributeToken,
) -> Result<u32, ObjectHyperlinkHwpxError> {
    let value = lexical_value(source, attribute)?;
    if value.is_empty()
        || !value.bytes().all(|byte| byte.is_ascii_digit())
        || (value != "0" && value.starts_with('0'))
    {
        return Err(ObjectHyperlinkHwpxError::InvalidIdentity);
    }
    value
        .parse::<u32>()
        .map_err(|_| ObjectHyperlinkHwpxError::InvalidIdentity)
}

fn escape_xml_attribute(value: &str) -> Result<String, ObjectHyperlinkHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(ObjectHyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;"))
}

const fn invalid_xml_character(value: char) -> bool {
    !matches!(
        value as u32,
        0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF
    )
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, ObjectHyperlinkHwpxError> {
    element
        .outer_span()
        .ok_or(ObjectHyperlinkHwpxError::UnsupportedObject)
}

fn digest_span(source: &[u8], span: XmlByteSpan) -> Result<[u8; 32], ObjectHyperlinkHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(ObjectHyperlinkHwpxError::UnsupportedObject)?,
    )
    .into())
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn validate_plan(
    plan: &ObjectHyperlinkHwpxPlan,
    limits: ObjectHyperlinkHwpxLimits,
) -> Result<(), ObjectHyperlinkHwpxError> {
    if plan.schema_version != OBJECT_PROPERTIES_SCHEMA_VERSION
        || plan.profile_id != OBJECT_HYPERLINK_HWPX_PROFILE_ID
        || plan.domain_plan.capability_id() != "obj.object_hyperlink"
        || plan.source_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(ObjectHyperlinkHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &ObjectHyperlinkHwpxPlan,
    limits: ObjectHyperlinkHwpxLimits,
) -> Result<String, ObjectHyperlinkHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectHyperlinkHwpxLimits,
) -> Result<Vec<u8>, ObjectHyperlinkHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectHyperlinkHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(ObjectHyperlinkHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ObjectHyperlinkHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ObjectHyperlinkHwpxError::UnsupportedObject)
}

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
