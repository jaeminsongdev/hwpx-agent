use std::fmt;

use domain_ir::{
    ImageProperties, OBJECT_PROPERTIES_SCHEMA_VERSION, ObjectAltText, ObjectCaption,
    ObjectCaptionNumbering, ObjectCaptionSide, ObjectPropertiesBuilder, ObjectPropertiesError,
    ObjectPropertiesLimits, ObjectPropertiesPlan, ObjectPropertiesState, ObjectPropertyKind,
    ObjectPropertyMargins,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};

pub const OBJECT_COMMON_PROPERTIES_HWPX_PROFILE_ID: &str =
    "hwpx-agent.object-common-properties-hwpx.hwpml-2011-exact-native-fields/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HWPUNIT_PER_INCH: u64 = 7_200;
const SCALE_ONE: u64 = 1_000_000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectCommonPropertiesHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub edits: usize,
    pub text_bytes: usize,
    pub output_bytes: usize,
    pub plan_bytes: usize,
}

impl Default for ObjectCommonPropertiesHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 65_536,
            edits: 12,
            text_bytes: 64 * 1024,
            output_bytes: 32 * 1024 * 1024,
            plan_bytes: 2 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ObjectCommonPropertiesHwpxLimits(ObjectCommonPropertiesHwpxLimitConfig);

impl ObjectCommonPropertiesHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_OBJECTS: usize = 262_144;
    pub const HARD_MAX_EDITS: usize = 32;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_PLAN_BYTES: usize = 8 * 1024 * 1024;

    /// Creates finite limits for exact run-object property edits.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding limits.
    pub fn new(
        config: ObjectCommonPropertiesHwpxLimitConfig,
    ) -> Result<Self, ObjectCommonPropertiesHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.edits == 0
            || config.edits > Self::HARD_MAX_EDITS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
        {
            return Err(ObjectCommonPropertiesHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectCommonPropertiesHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectCommonPropertiesHwpxReadback {
    pub state: ObjectPropertiesState,
    pub capability_id: &'static str,
    pub section_sha256: [u8; 32],
    pub object_sha256: [u8; 32],
    pub property_sha256: [u8; 32],
    pub object_ordinal: usize,
}

impl fmt::Debug for ObjectCommonPropertiesHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCommonPropertiesHwpxReadback")
            .field("capability_id", &self.capability_id)
            .field("object_kind", &self.state.object_kind())
            .field("object_ordinal", &self.object_ordinal)
            .field("identity", &"<redacted>")
            .field("properties", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct ObjectCommonPropertiesHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    capability_id: &'static str,
    object_ordinal: usize,
    source_section_sha256: [u8; 32],
    source_object_sha256: [u8; 32],
    source_property_sha256: [u8; 32],
    source_document_flow_sha256: String,
    domain_plan: ObjectPropertiesPlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl ObjectCommonPropertiesHwpxPlan {
    #[must_use]
    pub const fn object_ordinal(&self) -> usize {
        self.object_ordinal
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
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
    /// Returns plan serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: ObjectCommonPropertiesHwpxLimits,
    ) -> Result<Vec<u8>, ObjectCommonPropertiesHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectCommonPropertiesHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCommonPropertiesHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("object_ordinal", &self.object_ordinal)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectCommonPropertiesHwpxLoweringReceipt {
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
    pub modified_span_count: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for ObjectCommonPropertiesHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCommonPropertiesHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("modified_span_count", &self.modified_span_count)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectCommonPropertiesHwpxError {
    #[error("object-common-properties HWPX limits are invalid")]
    InvalidLimit,
    #[error("object-common-properties HWPX section exceeds a finite limit")]
    InputLimit,
    #[error("object-common-properties HWPX target is absent, duplicated, or unsupported")]
    UnsupportedObject,
    #[error("object-common-properties operation has no exact native representation")]
    UnsupportedProfile,
    #[error("object-common-properties HWPX attribute is malformed or ambiguous")]
    InvalidAttribute,
    #[error("object-common-properties HWPX number is noncanonical or out of range")]
    InvalidNumber,
    #[error("object-common-properties HWPX text is malformed or unsupported")]
    InvalidText,
    #[error("object-common-properties HWPX section, object, state, or flow drifted")]
    SourceDrift,
    #[error("object-common-properties HWPX plan was tampered with")]
    PlanTampered,
    #[error("object-common-properties HWPX semantic readback differs")]
    ReadbackMismatch,
    #[error("object-common-properties HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("object-common-properties HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("object-common-properties HWPX allocation failed")]
    AllocationFailed,
    #[error("object-common-properties domain validation failed")]
    Domain(#[from] ObjectPropertiesError),
    #[error("object-common-properties preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl ObjectCommonPropertiesHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_common_properties_hwpx_invalid_limit",
            Self::InputLimit => "object_common_properties_hwpx_input_limit",
            Self::UnsupportedObject => "object_common_properties_hwpx_unsupported_object",
            Self::UnsupportedProfile => "object_common_properties_hwpx_unsupported_profile",
            Self::InvalidAttribute => "object_common_properties_hwpx_invalid_attribute",
            Self::InvalidNumber => "object_common_properties_hwpx_invalid_number",
            Self::InvalidText => "object_common_properties_hwpx_invalid_text",
            Self::SourceDrift => "object_common_properties_hwpx_source_drift",
            Self::PlanTampered => "object_common_properties_hwpx_plan_tampered",
            Self::ReadbackMismatch => "object_common_properties_hwpx_readback_mismatch",
            Self::PreservationMismatch => "object_common_properties_hwpx_preservation_mismatch",
            Self::OutputLimit => "object_common_properties_hwpx_output_limit",
            Self::AllocationFailed => "object_common_properties_hwpx_allocation_failed",
            Self::Domain(_) => "object_common_properties_hwpx_domain",
            Self::Preserving(_) => "object_common_properties_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct ObjectCommonPropertiesHwpxReader;

impl ObjectCommonPropertiesHwpxReader {
    /// Reads one exact run object using one of the four admitted native-property profiles.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, stale, lossy, or over-limit XML.
    pub fn read_in_section(
        source: &[u8],
        object_ordinal: usize,
        capability_id: &'static str,
        expected: &ObjectPropertiesState,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: ObjectCommonPropertiesHwpxLimits,
    ) -> Result<ObjectCommonPropertiesHwpxReadback, ObjectCommonPropertiesHwpxError> {
        let parsed = parse_selected(source, object_ordinal, hwpx_limits)?;
        if expected.object_kind() != parsed.object_kind
            || expected.native_object_id() != parsed.native_object_id
            || expected.native_instance_id() != parsed.native_instance_id
        {
            return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
        }
        let property_span = verify_expected(
            source,
            &parsed,
            capability_id,
            expected,
            state_limits,
            hwpx_limits,
        )?;
        Ok(ObjectCommonPropertiesHwpxReadback {
            state: expected.clone(),
            capability_id,
            section_sha256: Sha256::digest(source).into(),
            object_sha256: digest_span(
                source,
                outer_span(element(&parsed.document, parsed.root)?)?,
            )?,
            property_sha256: digest_span(source, property_span)?,
            object_ordinal,
        })
    }
}

#[derive(Debug)]
pub struct ObjectCommonPropertiesHwpxBuilder;

impl ObjectCommonPropertiesHwpxBuilder {
    /// Binds a domain plan to exact reviewed HWPML fields.
    ///
    /// # Errors
    ///
    /// Rejects unsupported semantics, domain drift, source drift, or finite-limit violations.
    pub fn plan(
        source: &[u8],
        object_ordinal: usize,
        domain_plan: &ObjectPropertiesPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: ObjectCommonPropertiesHwpxLimits,
    ) -> Result<ObjectCommonPropertiesHwpxPlan, ObjectCommonPropertiesHwpxError> {
        let capability_id = admitted_capability(domain_plan.capability_id())?;
        if domain_plan.source_document_flow_sha256() != current_document_flow_sha256 {
            return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
        }
        let readback = ObjectCommonPropertiesHwpxReader::read_in_section(
            source,
            object_ordinal,
            capability_id,
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
        verify_transition_profile(
            capability_id,
            domain_plan.source_state(),
            domain_plan.target_state(),
        )?;
        let domain_plan_sha256 = domain_plan.plan_sha256().to_owned();
        let mut plan = ObjectCommonPropertiesHwpxPlan {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION,
            profile_id: OBJECT_COMMON_PROPERTIES_HWPX_PROFILE_ID,
            capability_id,
            object_ordinal,
            source_section_sha256: readback.section_sha256,
            source_object_sha256: readback.object_sha256,
            source_property_sha256: readback.property_sha256,
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
pub struct ObjectCommonPropertiesHwpxLowerer;

impl ObjectCommonPropertiesHwpxLowerer {
    /// Revalidates the bound source and patches only reviewed native spans.
    ///
    /// # Errors
    ///
    /// Returns no output on unsupported semantics, drift, tampering, or preservation failure.
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        plan: &ObjectCommonPropertiesHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: ObjectCommonPropertiesHwpxLimits,
    ) -> Result<(Vec<u8>, ObjectCommonPropertiesHwpxLoweringReceipt), ObjectCommonPropertiesHwpxError>
    {
        validate_plan(plan, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || current_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
            || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        {
            return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
        }
        let source_readback = ObjectCommonPropertiesHwpxReader::read_in_section(
            source,
            plan.object_ordinal,
            plan.capability_id,
            plan.domain_plan.source_state(),
            state_limits,
            hwpx_limits,
        )?;
        if source_readback.object_sha256 != plan.source_object_sha256
            || source_readback.property_sha256 != plan.source_property_sha256
        {
            return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
        }
        let result = ObjectPropertiesBuilder::build(
            &plan.domain_plan,
            plan.domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        let target_state = result.state;
        verify_transition_profile(
            plan.capability_id,
            plan.domain_plan.source_state(),
            &target_state,
        )?;
        let parsed = parse_selected(source, plan.object_ordinal, hwpx_limits)?;
        let mut edits = property_edits(
            source,
            &parsed,
            plan.capability_id,
            plan.domain_plan.source_state(),
            &target_state,
            hwpx_limits,
        )?;
        if edits.is_empty() || edits.len() > hwpx_limits.0.edits {
            return Err(ObjectCommonPropertiesHwpxError::PlanTampered);
        }
        let modified_span_count = edits.len();
        let output = apply_edits(source, &mut edits, hwpx_limits)?;
        verify_preservation(source, &output, &edits)?;
        let output_readback = ObjectCommonPropertiesHwpxReader::read_in_section(
            &output,
            plan.object_ordinal,
            plan.capability_id,
            &target_state,
            state_limits,
            hwpx_limits,
        )?;
        let receipt = ObjectCommonPropertiesHwpxLoweringReceipt {
            profile_id: OBJECT_COMMON_PROPERTIES_HWPX_PROFILE_ID,
            capability_id: plan.capability_id,
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
            modified_span_count,
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
        plan: &ObjectCommonPropertiesHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectPropertiesLimits,
        hwpx_limits: ObjectCommonPropertiesHwpxLimits,
    ) -> Result<Vec<u8>, ObjectCommonPropertiesHwpxError> {
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
}

fn parse_selected(
    source: &[u8],
    object_ordinal: usize,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<ParsedObject, ObjectCommonPropertiesHwpxError> {
    if source.is_empty()
        || source.len() > limits.0.section_bytes
        || object_ordinal >= limits.0.objects
    {
        return Err(ObjectCommonPropertiesHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(ObjectCommonPropertiesHwpxError::InputLimit);
    }
    let root = selected_run_object(&document, object_ordinal, limits)?;
    let root_element = element(&document, root)?;
    let object_kind = object_kind(&document, root)?;
    let native_object_id = canonical_u32(source, strict_attribute(root_element, "id")?)?;
    let native_instance_id = canonical_u32(source, strict_attribute(root_element, "instid")?)?;
    if native_object_id == 0 || native_instance_id == 0 {
        return Err(ObjectCommonPropertiesHwpxError::InvalidNumber);
    }
    Ok(ParsedObject {
        document,
        root,
        object_kind,
        native_object_id,
        native_instance_id,
    })
}

fn admitted_capability(
    capability_id: &str,
) -> Result<&'static str, ObjectCommonPropertiesHwpxError> {
    match capability_id {
        "obj.margin_caption" => Ok("obj.margin_caption"),
        "obj.image_properties" => Ok("obj.image_properties"),
        "obj.printable" => Ok("obj.printable"),
        "obj.alt_text" => Ok("obj.alt_text"),
        _ => Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile),
    }
}

fn verify_transition_profile(
    capability_id: &str,
    source: &ObjectPropertiesState,
    target: &ObjectPropertiesState,
) -> Result<(), ObjectCommonPropertiesHwpxError> {
    match capability_id {
        "obj.margin_caption" => {
            let (Some(source_caption), Some(target_caption)) = (source.caption(), target.caption())
            else {
                if source.caption().is_none() && target.caption().is_none() {
                    return Ok(());
                }
                return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
            };
            verify_caption_profile(source_caption)?;
            verify_caption_profile(target_caption)
        }
        "obj.image_properties" if source.object_kind() == ObjectPropertyKind::Picture => {
            let source_image = source
                .image()
                .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedProfile)?;
            let target_image = target
                .image()
                .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedProfile)?;
            let _ = native_image_dimensions(source_image)?;
            let _ = native_image_dimensions(target_image)?;
            Ok(())
        }
        "obj.printable" if source.object_kind() == ObjectPropertyKind::FormObject => Ok(()),
        "obj.alt_text" => {
            verify_alt_profile(source.alt_text())?;
            verify_alt_profile(target.alt_text())?;
            if source.alt_text().is_some() != target.alt_text().is_some() {
                return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
            }
            Ok(())
        }
        _ => Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile),
    }
}

fn verify_caption_profile(caption: &ObjectCaption) -> Result<(), ObjectCommonPropertiesHwpxError> {
    if caption.numbering != ObjectCaptionNumbering::None {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    }
    Ok(())
}

fn verify_alt_profile(
    value: Option<&ObjectAltText>,
) -> Result<(), ObjectCommonPropertiesHwpxError> {
    if value.is_some_and(|alt| !alt.title.is_empty()) {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    }
    Ok(())
}

fn verify_expected(
    source: &[u8],
    parsed: &ParsedObject,
    capability_id: &str,
    expected: &ObjectPropertiesState,
    _state_limits: ObjectPropertiesLimits,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<XmlByteSpan, ObjectCommonPropertiesHwpxError> {
    match capability_id {
        "obj.margin_caption" => verify_margin_caption(source, parsed, expected, limits),
        "obj.image_properties" => verify_image(source, parsed, expected),
        "obj.printable" => verify_printable(source, parsed, expected),
        "obj.alt_text" => verify_alt_text(source, parsed, expected, limits),
        _ => Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile),
    }
}

fn verify_margin_caption(
    source: &[u8],
    parsed: &ParsedObject,
    expected: &ObjectPropertiesState,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<XmlByteSpan, ObjectCommonPropertiesHwpxError> {
    let margin = unique_direct_child(&parsed.document, parsed.root, "outMargin")?;
    let native_margins = parse_margins(source, element(&parsed.document, margin)?)?;
    if native_margins != expected.outer_margins() {
        return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
    }
    let captions = direct_children_named(&parsed.document, parsed.root, "caption")?;
    match (captions.as_slice(), expected.caption()) {
        ([], None) => outer_span(element(&parsed.document, parsed.root)?),
        ([caption], Some(expected_caption)) => {
            verify_caption_profile(expected_caption)?;
            verify_native_caption(source, &parsed.document, *caption, expected_caption, limits)?;
            outer_span(element(&parsed.document, parsed.root)?)
        }
        _ => Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile),
    }
}

fn verify_image(
    source: &[u8],
    parsed: &ParsedObject,
    expected: &ObjectPropertiesState,
) -> Result<XmlByteSpan, ObjectCommonPropertiesHwpxError> {
    if parsed.object_kind != ObjectPropertyKind::Picture {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    }
    let properties = expected
        .image()
        .ok_or(ObjectCommonPropertiesHwpxError::SourceDrift)?;
    let org = unique_direct_child(&parsed.document, parsed.root, "orgSz")?;
    let cur = unique_direct_child(&parsed.document, parsed.root, "curSz")?;
    let dim = unique_direct_child(&parsed.document, parsed.root, "imgDim")?;
    let native = native_image_dimensions(properties)?;
    if parse_pair(source, element(&parsed.document, org)?, "width", "height")?
        != (native.org_width, native.org_height)
        || parse_pair(source, element(&parsed.document, cur)?, "width", "height")?
            != (native.cur_width, native.cur_height)
        || parse_pair(
            source,
            element(&parsed.document, dim)?,
            "dimwidth",
            "dimheight",
        )? != (properties.original_width_px, properties.original_height_px)
    {
        return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
    }
    outer_span(element(&parsed.document, parsed.root)?)
}

fn verify_printable(
    source: &[u8],
    parsed: &ParsedObject,
    expected: &ObjectPropertiesState,
) -> Result<XmlByteSpan, ObjectCommonPropertiesHwpxError> {
    if parsed.object_kind != ObjectPropertyKind::FormObject {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    }
    let attribute = strict_attribute(element(&parsed.document, parsed.root)?, "printable")?;
    if canonical_bool(source, attribute)? != expected.printable() {
        return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
    }
    Ok(attribute.value_span())
}

fn verify_alt_text(
    source: &[u8],
    parsed: &ParsedObject,
    expected: &ObjectPropertiesState,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<XmlByteSpan, ObjectCommonPropertiesHwpxError> {
    verify_alt_profile(expected.alt_text())?;
    let comment = unique_direct_child(&parsed.document, parsed.root, "shapeComment")?;
    let span = element(&parsed.document, comment)?
        .content_span()
        .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedProfile)?;
    let native = decode_text(source, span, limits)?;
    let expected_description = expected
        .alt_text()
        .map_or("", |value| value.description.as_str());
    if native != expected_description {
        return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
    }
    Ok(span)
}

fn property_edits(
    source_bytes: &[u8],
    parsed: &ParsedObject,
    capability_id: &str,
    source: &ObjectPropertiesState,
    target: &ObjectPropertiesState,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<Vec<ByteEdit>, ObjectCommonPropertiesHwpxError> {
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(limits.0.edits)
        .map_err(|_| ObjectCommonPropertiesHwpxError::AllocationFailed)?;
    match capability_id {
        "obj.margin_caption" => margin_caption_edits(parsed, source, target, &mut edits)?,
        "obj.image_properties" => image_edits(parsed, source, target, &mut edits)?,
        "obj.printable" => push_attribute_change(
            &parsed.document,
            parsed.root,
            "printable",
            source.printable(),
            target.printable(),
            bool_text(target.printable()).to_owned(),
            &mut edits,
        )?,
        "obj.alt_text" => alt_text_edits(parsed, source, target, limits, &mut edits)?,
        _ => return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile),
    }
    for edit in &edits {
        if edit.span.end() > source_bytes.len() {
            return Err(ObjectCommonPropertiesHwpxError::UnsupportedObject);
        }
    }
    Ok(edits)
}

fn margin_caption_edits(
    parsed: &ParsedObject,
    source: &ObjectPropertiesState,
    target: &ObjectPropertiesState,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectCommonPropertiesHwpxError> {
    let margin = unique_direct_child(&parsed.document, parsed.root, "outMargin")?;
    let old = source.outer_margins();
    let new = target.outer_margins();
    for (name, source_value, target_value) in [
        ("left", old.left_hwpunit, new.left_hwpunit),
        ("right", old.right_hwpunit, new.right_hwpunit),
        ("top", old.top_hwpunit, new.top_hwpunit),
        ("bottom", old.bottom_hwpunit, new.bottom_hwpunit),
    ] {
        push_attribute_change(
            &parsed.document,
            margin,
            name,
            source_value,
            target_value,
            target_value.to_string(),
            edits,
        )?;
    }
    match (source.caption(), target.caption()) {
        (None, None) => Ok(()),
        (Some(old_caption), Some(new_caption)) => {
            let caption = unique_direct_child(&parsed.document, parsed.root, "caption")?;
            push_attribute_change(
                &parsed.document,
                caption,
                "side",
                old_caption.side,
                new_caption.side,
                caption_side_text(new_caption.side).to_owned(),
                edits,
            )?;
            push_attribute_change(
                &parsed.document,
                caption,
                "gap",
                old_caption.gap_hwpunit,
                new_caption.gap_hwpunit,
                new_caption.gap_hwpunit.to_string(),
                edits,
            )?;
            for name in ["width", "lastWidth"] {
                push_attribute_change(
                    &parsed.document,
                    caption,
                    name,
                    old_caption.width_hwpunit,
                    new_caption.width_hwpunit,
                    new_caption.width_hwpunit.to_string(),
                    edits,
                )?;
            }
            if rendered_caption_text(old_caption) != rendered_caption_text(new_caption) {
                let (_, text_span) = parse_caption_text_span(&parsed.document, caption)?;
                edits.push(ByteEdit {
                    span: text_span,
                    replacement: escape_xml_text(&rendered_caption_text(new_caption))?.into_bytes(),
                });
            }
            Ok(())
        }
        _ => Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile),
    }
}

fn image_edits(
    parsed: &ParsedObject,
    source: &ObjectPropertiesState,
    target: &ObjectPropertiesState,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectCommonPropertiesHwpxError> {
    let old = native_image_dimensions(
        source
            .image()
            .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedProfile)?,
    )?;
    let target_properties = target
        .image()
        .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedProfile)?;
    let new = native_image_dimensions(target_properties)?;
    let org = unique_direct_child(&parsed.document, parsed.root, "orgSz")?;
    let cur = unique_direct_child(&parsed.document, parsed.root, "curSz")?;
    let dim = unique_direct_child(&parsed.document, parsed.root, "imgDim")?;
    let source_properties = source
        .image()
        .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedProfile)?;
    for (element_index, name, source_value, target_value) in [
        (org, "width", old.org_width, new.org_width),
        (org, "height", old.org_height, new.org_height),
        (cur, "width", old.cur_width, new.cur_width),
        (cur, "height", old.cur_height, new.cur_height),
        (
            dim,
            "dimwidth",
            source_properties.original_width_px,
            target_properties.original_width_px,
        ),
        (
            dim,
            "dimheight",
            source_properties.original_height_px,
            target_properties.original_height_px,
        ),
    ] {
        push_attribute_change(
            &parsed.document,
            element_index,
            name,
            source_value,
            target_value,
            target_value.to_string(),
            edits,
        )?;
    }
    Ok(())
}

fn alt_text_edits(
    parsed: &ParsedObject,
    source: &ObjectPropertiesState,
    target: &ObjectPropertiesState,
    limits: ObjectCommonPropertiesHwpxLimits,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectCommonPropertiesHwpxError> {
    verify_alt_profile(source.alt_text())?;
    verify_alt_profile(target.alt_text())?;
    let old = source
        .alt_text()
        .map_or("", |value| value.description.as_str());
    let new = target
        .alt_text()
        .map_or("", |value| value.description.as_str());
    if old == new {
        return Ok(());
    }
    let comment = unique_direct_child(&parsed.document, parsed.root, "shapeComment")?;
    let span = element(&parsed.document, comment)?
        .content_span()
        .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedProfile)?;
    let replacement = escape_xml_text(new)?;
    if replacement.len() > limits.0.text_bytes {
        return Err(ObjectCommonPropertiesHwpxError::OutputLimit);
    }
    edits.push(ByteEdit {
        span,
        replacement: replacement.into_bytes(),
    });
    Ok(())
}

#[derive(Clone, Copy)]
struct NativeImageDimensions {
    org_width: u32,
    org_height: u32,
    cur_width: u32,
    cur_height: u32,
}

fn native_image_dimensions(
    value: ImageProperties,
) -> Result<NativeImageDimensions, ObjectCommonPropertiesHwpxError> {
    let org_width = pixels_to_hwpunit(value.original_width_px, value.horizontal_dpi)?;
    let org_height = pixels_to_hwpunit(value.original_height_px, value.vertical_dpi)?;
    let cur_width = scaled_hwpunit(org_width, value.horizontal_scale_millionths)?;
    let cur_height = scaled_hwpunit(org_height, value.vertical_scale_millionths)?;
    Ok(NativeImageDimensions {
        org_width,
        org_height,
        cur_width,
        cur_height,
    })
}

fn pixels_to_hwpunit(pixels: u32, dpi: u32) -> Result<u32, ObjectCommonPropertiesHwpxError> {
    let numerator = u64::from(pixels)
        .checked_mul(HWPUNIT_PER_INCH)
        .and_then(|value| value.checked_add(u64::from(dpi) / 2))
        .ok_or(ObjectCommonPropertiesHwpxError::InvalidNumber)?;
    let value = numerator / u64::from(dpi);
    u32::try_from(value)
        .ok()
        .filter(|value| *value != 0)
        .ok_or(ObjectCommonPropertiesHwpxError::InvalidNumber)
}

fn scaled_hwpunit(value: u32, scale: u32) -> Result<u32, ObjectCommonPropertiesHwpxError> {
    let result = u64::from(value)
        .checked_mul(u64::from(scale))
        .and_then(|current| current.checked_add(SCALE_ONE / 2))
        .ok_or(ObjectCommonPropertiesHwpxError::InvalidNumber)?
        / SCALE_ONE;
    u32::try_from(result)
        .ok()
        .filter(|value| *value != 0)
        .ok_or(ObjectCommonPropertiesHwpxError::InvalidNumber)
}

fn parse_margins(
    source: &[u8],
    element: &XmlElementToken,
) -> Result<ObjectPropertyMargins, ObjectCommonPropertiesHwpxError> {
    Ok(ObjectPropertyMargins {
        left_hwpunit: canonical_u32(source, strict_attribute(element, "left")?)?,
        right_hwpunit: canonical_u32(source, strict_attribute(element, "right")?)?,
        top_hwpunit: canonical_u32(source, strict_attribute(element, "top")?)?,
        bottom_hwpunit: canonical_u32(source, strict_attribute(element, "bottom")?)?,
    })
}

fn parse_pair(
    source: &[u8],
    element: &XmlElementToken,
    first: &str,
    second: &str,
) -> Result<(u32, u32), ObjectCommonPropertiesHwpxError> {
    Ok((
        canonical_u32(source, strict_attribute(element, first)?)?,
        canonical_u32(source, strict_attribute(element, second)?)?,
    ))
}

fn verify_native_caption(
    source: &[u8],
    document: &PreservingXmlDocument,
    caption: usize,
    expected: &ObjectCaption,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<XmlByteSpan, ObjectCommonPropertiesHwpxError> {
    let caption_element = element(document, caption)?;
    if lexical_value(source, strict_attribute(caption_element, "fullSz")?)? != "0" {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    }
    let side = match lexical_value(source, strict_attribute(caption_element, "side")?)? {
        "LEFT" => ObjectCaptionSide::Left,
        "RIGHT" => ObjectCaptionSide::Right,
        "TOP" => ObjectCaptionSide::Top,
        "BOTTOM" => ObjectCaptionSide::Bottom,
        _ => return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile),
    };
    let width_hwpunit = canonical_u32(source, strict_attribute(caption_element, "width")?)?;
    if canonical_u32(source, strict_attribute(caption_element, "lastWidth")?)? != width_hwpunit {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    }
    let (text_index, text_span) = parse_caption_text_span(document, caption)?;
    let text = decode_text(source, text_span, limits)?;
    if side != expected.side
        || canonical_u32(source, strict_attribute(caption_element, "gap")?)? != expected.gap_hwpunit
        || width_hwpunit != expected.width_hwpunit
        || text != rendered_caption_text(expected)
    {
        return Err(ObjectCommonPropertiesHwpxError::SourceDrift);
    }
    outer_span(element(document, text_index)?)
}

fn rendered_caption_text(caption: &ObjectCaption) -> String {
    format!("{}{}", caption.label, caption.text)
}

fn parse_caption_text_span(
    document: &PreservingXmlDocument,
    caption: usize,
) -> Result<(usize, XmlByteSpan), ObjectCommonPropertiesHwpxError> {
    let sublist = unique_direct_child(document, caption, "subList")?;
    let text_nodes = descendants_named(document, sublist, "t")?;
    let [text] = text_nodes.as_slice() else {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    };
    let text_element = element(document, *text)?;
    if text_element.first_child().is_some() {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    }
    let span = text_element
        .content_span()
        .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedProfile)?;
    Ok((*text, span))
}

fn decode_text(
    source: &[u8],
    span: XmlByteSpan,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<String, ObjectCommonPropertiesHwpxError> {
    let lexical = std::str::from_utf8(
        source
            .get(span.start()..span.end())
            .ok_or(ObjectCommonPropertiesHwpxError::InvalidText)?,
    )
    .map_err(|_| ObjectCommonPropertiesHwpxError::InvalidText)?;
    if lexical.len() > limits.0.text_bytes || lexical.contains('<') {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    }
    let decoded = unescape(lexical).map_err(|_| ObjectCommonPropertiesHwpxError::InvalidText)?;
    if decoded.len() > limits.0.text_bytes {
        return Err(ObjectCommonPropertiesHwpxError::InputLimit);
    }
    Ok(decoded.into_owned())
}

fn escape_xml_text(value: &str) -> Result<String, ObjectCommonPropertiesHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(ObjectCommonPropertiesHwpxError::InvalidText);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))
}

const fn invalid_xml_character(value: char) -> bool {
    !matches!(
        value as u32,
        0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF
    )
}

fn caption_side_text(value: ObjectCaptionSide) -> &'static str {
    match value {
        ObjectCaptionSide::Left => "LEFT",
        ObjectCaptionSide::Right => "RIGHT",
        ObjectCaptionSide::Top => "TOP",
        ObjectCaptionSide::Bottom => "BOTTOM",
    }
}

const fn bool_text(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

#[allow(clippy::needless_pass_by_value)]
fn push_attribute_change<T: Eq>(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    source: T,
    target: T,
    replacement: String,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectCommonPropertiesHwpxError> {
    if source == target {
        return Ok(());
    }
    edits
        .try_reserve(1)
        .map_err(|_| ObjectCommonPropertiesHwpxError::AllocationFailed)?;
    edits.push(ByteEdit {
        span: strict_attribute(element(document, element_index)?, name)?.value_span(),
        replacement: replacement.into_bytes(),
    });
    Ok(())
}

fn apply_edits(
    source: &[u8],
    edits: &mut [ByteEdit],
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<Vec<u8>, ObjectCommonPropertiesHwpxError> {
    edits.sort_unstable_by_key(|edit| edit.span.start());
    let mut previous_end = 0;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.span.start() < previous_end || edit.span.end() > source.len() {
            return Err(ObjectCommonPropertiesHwpxError::UnsupportedObject);
        }
        previous_end = edit.span.end();
        output_len = output_len
            .checked_sub(edit.span.len())
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(ObjectCommonPropertiesHwpxError::OutputLimit)?;
    }
    if output_len > limits.0.output_bytes {
        return Err(ObjectCommonPropertiesHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| ObjectCommonPropertiesHwpxError::AllocationFailed)?;
    let mut cursor = 0;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.span.start()]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.span.end();
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(ObjectCommonPropertiesHwpxError::OutputLimit);
    }
    Ok(output)
}

fn verify_preservation(
    source: &[u8],
    output: &[u8],
    edits: &[ByteEdit],
) -> Result<(), ObjectCommonPropertiesHwpxError> {
    let mut source_cursor = 0;
    let mut output_cursor = 0_usize;
    for edit in edits {
        let unchanged_len = edit
            .span
            .start()
            .checked_sub(source_cursor)
            .ok_or(ObjectCommonPropertiesHwpxError::PreservationMismatch)?;
        let output_unchanged_end = output_cursor
            .checked_add(unchanged_len)
            .ok_or(ObjectCommonPropertiesHwpxError::PreservationMismatch)?;
        let output_replacement_end = output_unchanged_end
            .checked_add(edit.replacement.len())
            .ok_or(ObjectCommonPropertiesHwpxError::PreservationMismatch)?;
        if output_replacement_end > output.len()
            || source[source_cursor..edit.span.start()]
                != output[output_cursor..output_unchanged_end]
            || edit.replacement != output[output_unchanged_end..output_replacement_end]
        {
            return Err(ObjectCommonPropertiesHwpxError::PreservationMismatch);
        }
        source_cursor = edit.span.end();
        output_cursor = output_replacement_end;
    }
    if source[source_cursor..] != output[output_cursor..] {
        return Err(ObjectCommonPropertiesHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn selected_run_object(
    document: &PreservingXmlDocument,
    ordinal: usize,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<usize, ObjectCommonPropertiesHwpxError> {
    let mut seen = 0_usize;
    for (index, candidate) in document.elements().iter().enumerate() {
        if !is_run_object(candidate) {
            continue;
        }
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedObject)?;
        if !has_name(parent, "run") {
            continue;
        }
        if seen == ordinal {
            return Ok(index);
        }
        seen = seen
            .checked_add(1)
            .ok_or(ObjectCommonPropertiesHwpxError::InputLimit)?;
        if seen > limits.0.objects {
            return Err(ObjectCommonPropertiesHwpxError::InputLimit);
        }
    }
    Err(ObjectCommonPropertiesHwpxError::UnsupportedObject)
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
                | "chart"
                | "checkBtn"
                | "radioBtn"
                | "comboBox"
                | "listBox"
                | "edit"
        )
}

fn object_kind(
    document: &PreservingXmlDocument,
    root: usize,
) -> Result<ObjectPropertyKind, ObjectCommonPropertiesHwpxError> {
    match element(document, root)?.name().local_name() {
        "pic" => Ok(ObjectPropertyKind::Picture),
        "rect" => match direct_children_named(document, root, "drawText")?.len() {
            0 => Ok(ObjectPropertyKind::BasicShape),
            1 => Ok(ObjectPropertyKind::TextBox),
            _ => Err(ObjectCommonPropertiesHwpxError::UnsupportedObject),
        },
        "ellipse" | "line" | "arc" | "polygon" | "curve" | "connectLine" => {
            Ok(ObjectPropertyKind::BasicShape)
        }
        "container" => Ok(ObjectPropertyKind::DrawingCanvas),
        "ole" | "video" => Ok(ObjectPropertyKind::EmbeddedObject),
        "chart" => Ok(ObjectPropertyKind::Chart),
        "checkBtn" | "radioBtn" | "comboBox" | "listBox" | "edit" => {
            Ok(ObjectPropertyKind::FormObject)
        }
        _ => Err(ObjectCommonPropertiesHwpxError::UnsupportedObject),
    }
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, ObjectCommonPropertiesHwpxError> {
    let mut children = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let candidate = element(document, index)?;
        if has_name(candidate, local_name) {
            children
                .try_reserve(1)
                .map_err(|_| ObjectCommonPropertiesHwpxError::AllocationFailed)?;
            children.push(index);
        }
        child = candidate.next_sibling();
    }
    Ok(children)
}

fn descendants_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, ObjectCommonPropertiesHwpxError> {
    let mut matches = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if has_name(candidate, local_name) && is_descendant(document, index, parent)? {
            matches
                .try_reserve(1)
                .map_err(|_| ObjectCommonPropertiesHwpxError::AllocationFailed)?;
            matches.push(index);
        }
    }
    Ok(matches)
}

fn is_descendant(
    document: &PreservingXmlDocument,
    candidate: usize,
    ancestor: usize,
) -> Result<bool, ObjectCommonPropertiesHwpxError> {
    let mut parent = element(document, candidate)?.parent();
    while let Some(index) = parent {
        if index == ancestor {
            return Ok(true);
        }
        parent = element(document, index)?.parent();
    }
    Ok(false)
}

fn unique_direct_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, ObjectCommonPropertiesHwpxError> {
    let children = direct_children_named(document, parent, local_name)?;
    let [child] = children.as_slice() else {
        return Err(ObjectCommonPropertiesHwpxError::UnsupportedProfile);
    };
    Ok(*child)
}

fn strict_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, ObjectCommonPropertiesHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration() && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(ObjectCommonPropertiesHwpxError::InvalidAttribute)?;
    if value.name().namespace().is_some() || matches.next().is_some() {
        return Err(ObjectCommonPropertiesHwpxError::InvalidAttribute);
    }
    Ok(value)
}

fn lexical_value<'a>(
    source: &'a [u8],
    attribute: &XmlAttributeToken,
) -> Result<&'a str, ObjectCommonPropertiesHwpxError> {
    std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(ObjectCommonPropertiesHwpxError::InvalidAttribute)?,
    )
    .map_err(|_| ObjectCommonPropertiesHwpxError::InvalidAttribute)
}

fn canonical_u32(
    source: &[u8],
    attribute: &XmlAttributeToken,
) -> Result<u32, ObjectCommonPropertiesHwpxError> {
    let value = lexical_value(source, attribute)?;
    if value.is_empty()
        || !value.bytes().all(|byte| byte.is_ascii_digit())
        || (value != "0" && value.starts_with('0'))
    {
        return Err(ObjectCommonPropertiesHwpxError::InvalidNumber);
    }
    value
        .parse::<u32>()
        .map_err(|_| ObjectCommonPropertiesHwpxError::InvalidNumber)
}

fn canonical_bool(
    source: &[u8],
    attribute: &XmlAttributeToken,
) -> Result<bool, ObjectCommonPropertiesHwpxError> {
    match lexical_value(source, attribute)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(ObjectCommonPropertiesHwpxError::InvalidAttribute),
    }
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, ObjectCommonPropertiesHwpxError> {
    element
        .outer_span()
        .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedObject)
}

fn digest_span(
    source: &[u8],
    span: XmlByteSpan,
) -> Result<[u8; 32], ObjectCommonPropertiesHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedObject)?,
    )
    .into())
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn validate_plan(
    plan: &ObjectCommonPropertiesHwpxPlan,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<(), ObjectCommonPropertiesHwpxError> {
    if plan.schema_version != OBJECT_PROPERTIES_SCHEMA_VERSION
        || plan.profile_id != OBJECT_COMMON_PROPERTIES_HWPX_PROFILE_ID
        || admitted_capability(plan.capability_id)? != plan.capability_id
        || plan.domain_plan.capability_id() != plan.capability_id
        || plan.source_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(ObjectCommonPropertiesHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &ObjectCommonPropertiesHwpxPlan,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<String, ObjectCommonPropertiesHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectCommonPropertiesHwpxLimits,
) -> Result<Vec<u8>, ObjectCommonPropertiesHwpxError> {
    let bytes =
        serde_json::to_vec(value).map_err(|_| ObjectCommonPropertiesHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(ObjectCommonPropertiesHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ObjectCommonPropertiesHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ObjectCommonPropertiesHwpxError::UnsupportedObject)
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
