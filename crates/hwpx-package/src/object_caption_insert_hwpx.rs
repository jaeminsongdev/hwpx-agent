use std::fmt;

use domain_ir::{
    OBJECT_SPECIAL_SCHEMA_VERSION, ObjectCaption, ObjectCaptionNumbering, ObjectCaptionSide,
    ObjectIdentity, ObjectSpecialBuilder, ObjectSpecialError, ObjectSpecialLimits,
    ObjectSpecialOperation, ObjectSpecialPlan,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};

pub const OBJECT_CAPTION_INSERT_HWPX_PROFILE_ID: &str =
    "hwpx-agent.object-caption-insert-hwpx.hwpml-2011-plain-static/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectCaptionInsertHwpxLimitConfig {
    pub section_bytes: usize,
    pub output_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub text_bytes: usize,
    pub plan_bytes: usize,
}

impl Default for ObjectCaptionInsertHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 16_384,
            text_bytes: 64 * 1024,
            plan_bytes: 8 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ObjectCaptionInsertHwpxLimits(ObjectCaptionInsertHwpxLimitConfig);

impl ObjectCaptionInsertHwpxLimits {
    pub const HARD_MAX_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 4_000_000;
    pub const HARD_MAX_OBJECTS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;

    /// Creates finite limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub const fn new(
        config: ObjectCaptionInsertHwpxLimitConfig,
    ) -> Result<Self, ObjectCaptionInsertHwpxError> {
        if config.section_bytes == 0
            || config.output_bytes < config.section_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_BYTES
        {
            return Err(ObjectCaptionInsertHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectCaptionInsertHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObjectCaptionInsertHwpxReadback {
    pub section_sha256: [u8; 32],
    pub object_sha256: [u8; 32],
    pub caption_sha256: Option<[u8; 32]>,
    pub native_object_id: u32,
    pub native_instance_id: u32,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCaptionInsertHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    source_section_sha256: [u8; 32],
    source_object_sha256: [u8; 32],
    target: ObjectIdentity,
    caption: ObjectCaption,
    domain_plan: ObjectSpecialPlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl ObjectCaptionInsertHwpxPlan {
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the bound plan within its configured finite limit.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failures.
    pub fn canonical_json(
        &self,
        limits: ObjectCaptionInsertHwpxLimits,
    ) -> Result<Vec<u8>, ObjectCaptionInsertHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectCaptionInsertHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCaptionInsertHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &"obj.caption_insert")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectCaptionInsertHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_object_sha256: [u8; 32],
    pub output_object_sha256: [u8; 32],
    pub caption_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub modified_span_count: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for ObjectCaptionInsertHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCaptionInsertHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("modified_span_count", &self.modified_span_count)
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectCaptionInsertHwpxError {
    #[error("object-caption HWPX limits are invalid")]
    InvalidLimit,
    #[error("object-caption HWPX input exceeds a finite limit")]
    InputLimit,
    #[error("object-caption HWPX object is unsupported or ambiguous")]
    UnsupportedObject,
    #[error("object-caption HWPX identity is invalid")]
    InvalidIdentity,
    #[error("object-caption HWPX profile cannot represent this caption")]
    UnsupportedProfile,
    #[error("object-caption HWPX source drifted")]
    SourceDrift,
    #[error("object-caption HWPX plan was tampered with")]
    PlanTampered,
    #[error("object-caption HWPX readback differs from the target state")]
    ReadbackMismatch,
    #[error("object-caption HWPX preservation check failed")]
    PreservationMismatch,
    #[error("object-caption HWPX text is invalid")]
    InvalidText,
    #[error("object-caption HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("object-caption HWPX allocation failed")]
    AllocationFailed,
    #[error(transparent)]
    Domain(#[from] ObjectSpecialError),
    #[error(transparent)]
    Preserving(#[from] PreservingXmlError),
}

impl ObjectCaptionInsertHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_caption_insert_hwpx_invalid_limit",
            Self::InputLimit => "object_caption_insert_hwpx_input_limit",
            Self::UnsupportedObject => "object_caption_insert_hwpx_unsupported_object",
            Self::InvalidIdentity => "object_caption_insert_hwpx_invalid_identity",
            Self::UnsupportedProfile => "object_caption_insert_hwpx_unsupported_profile",
            Self::SourceDrift => "object_caption_insert_hwpx_source_drift",
            Self::PlanTampered => "object_caption_insert_hwpx_plan_tampered",
            Self::ReadbackMismatch => "object_caption_insert_hwpx_readback_mismatch",
            Self::PreservationMismatch => "object_caption_insert_hwpx_preservation_mismatch",
            Self::InvalidText => "object_caption_insert_hwpx_invalid_text",
            Self::OutputLimit => "object_caption_insert_hwpx_output_limit",
            Self::AllocationFailed => "object_caption_insert_hwpx_allocation_failed",
            Self::Domain(_) => "object_caption_insert_hwpx_domain",
            Self::Preserving(_) => "object_caption_insert_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct ObjectCaptionInsertHwpxReader;

impl ObjectCaptionInsertHwpxReader {
    /// Reads one exact rectangle and its optional plain static caption.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, unsupported, or semantically different projections.
    pub fn read_in_section(
        source: &[u8],
        target: &ObjectIdentity,
        expected: Option<&ObjectCaption>,
        limits: ObjectCaptionInsertHwpxLimits,
    ) -> Result<ObjectCaptionInsertHwpxReadback, ObjectCaptionInsertHwpxError> {
        let parsed = parse_target(source, target, limits)?;
        let caption_sha256 = match (parsed.caption, expected) {
            (None, None) => None,
            (Some(index), Some(caption)) => {
                verify_native_caption(source, &parsed.document, index, caption, limits)?;
                Some(digest_span(
                    source,
                    outer_span(element(&parsed.document, index)?)?,
                )?)
            }
            _ => return Err(ObjectCaptionInsertHwpxError::ReadbackMismatch),
        };
        parsed.document.verify_untouched_round_trip()?;
        Ok(ObjectCaptionInsertHwpxReadback {
            section_sha256: Sha256::digest(source).into(),
            object_sha256: digest_span(
                source,
                outer_span(element(&parsed.document, parsed.root)?)?,
            )?,
            caption_sha256,
            native_object_id: target.native_object_id,
            native_instance_id: target.native_instance_id,
        })
    }
}

#[derive(Debug)]
pub struct ObjectCaptionInsertHwpxBuilder;

impl ObjectCaptionInsertHwpxBuilder {
    /// Binds one exact `obj.caption_insert` plan to immutable section bytes.
    ///
    /// # Errors
    ///
    /// Rejects capability, profile, identity, source, flow, or plan drift.
    pub fn plan(
        source: &[u8],
        domain_plan: &ObjectSpecialPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectSpecialLimits,
        hwpx_limits: ObjectCaptionInsertHwpxLimits,
    ) -> Result<ObjectCaptionInsertHwpxPlan, ObjectCaptionInsertHwpxError> {
        let (target, caption) = operation_binding(domain_plan)?;
        verify_profile(caption)?;
        if domain_plan.source_document_flow_sha256() != current_document_flow_sha256 {
            return Err(ObjectCaptionInsertHwpxError::SourceDrift);
        }
        let result = ObjectSpecialBuilder::build(
            domain_plan,
            domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        if &result.state != domain_plan.target_state() {
            return Err(ObjectCaptionInsertHwpxError::PlanTampered);
        }
        let source_readback =
            ObjectCaptionInsertHwpxReader::read_in_section(source, target, None, hwpx_limits)?;
        let mut plan = ObjectCaptionInsertHwpxPlan {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION,
            profile_id: OBJECT_CAPTION_INSERT_HWPX_PROFILE_ID,
            source_section_sha256: source_readback.section_sha256,
            source_object_sha256: source_readback.object_sha256,
            target: target.clone(),
            caption: caption.clone(),
            domain_plan: domain_plan.clone(),
            domain_plan_sha256: domain_plan.plan_sha256().to_owned(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, hwpx_limits)?;
        let _ = plan.canonical_json(hwpx_limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct ObjectCaptionInsertHwpxLowerer;

impl ObjectCaptionInsertHwpxLowerer {
    /// Inserts one reviewed native caption subtree and verifies exact preservation and readback.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, flow, profile, preservation, or readback drift.
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        plan: &ObjectCaptionInsertHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectSpecialLimits,
        hwpx_limits: ObjectCaptionInsertHwpxLimits,
    ) -> Result<(Vec<u8>, ObjectCaptionInsertHwpxLoweringReceipt), ObjectCaptionInsertHwpxError>
    {
        validate_plan(plan, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        {
            return Err(ObjectCaptionInsertHwpxError::SourceDrift);
        }
        let source_readback = ObjectCaptionInsertHwpxReader::read_in_section(
            source,
            &plan.target,
            None,
            hwpx_limits,
        )?;
        if source_readback.object_sha256 != plan.source_object_sha256 {
            return Err(ObjectCaptionInsertHwpxError::SourceDrift);
        }
        let result = ObjectSpecialBuilder::build(
            &plan.domain_plan,
            plan.domain_plan.source_state(),
            current_document_flow_sha256,
            state_limits,
        )?;
        if &result.state != plan.domain_plan.target_state() {
            return Err(ObjectCaptionInsertHwpxError::PlanTampered);
        }
        let parsed = parse_target(source, &plan.target, hwpx_limits)?;
        let root = element(&parsed.document, parsed.root)?;
        let end_tag = root
            .end_tag_span()
            .ok_or(ObjectCaptionInsertHwpxError::UnsupportedObject)?;
        let fragment = caption_fragment(root.name().prefix(), &plan.caption, hwpx_limits)?;
        let output = apply_insertion(source, end_tag.start(), fragment.as_bytes(), hwpx_limits)?;
        verify_insertion(source, &output, end_tag.start(), fragment.as_bytes())?;
        let output_readback = ObjectCaptionInsertHwpxReader::read_in_section(
            &output,
            &plan.target,
            Some(&plan.caption),
            hwpx_limits,
        )?;
        let caption_sha256 = output_readback
            .caption_sha256
            .ok_or(ObjectCaptionInsertHwpxError::ReadbackMismatch)?;
        let receipt = ObjectCaptionInsertHwpxLoweringReceipt {
            profile_id: OBJECT_CAPTION_INSERT_HWPX_PROFILE_ID,
            capability_id: "obj.caption_insert",
            source_section_sha256: source_readback.section_sha256,
            output_section_sha256: output_readback.section_sha256,
            source_object_sha256: source_readback.object_sha256,
            output_object_sha256: output_readback.object_sha256,
            caption_sha256,
            source_state_sha256: plan
                .domain_plan
                .source_state()
                .canonical_sha256(state_limits)?,
            target_state_sha256: result.state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            modified_span_count: 1,
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
        plan: &ObjectCaptionInsertHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectSpecialLimits,
        hwpx_limits: ObjectCaptionInsertHwpxLimits,
    ) -> Result<Vec<u8>, ObjectCaptionInsertHwpxError> {
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

struct ParsedTarget {
    document: PreservingXmlDocument,
    root: usize,
    caption: Option<usize>,
}

fn parse_target(
    source: &[u8],
    target: &ObjectIdentity,
    limits: ObjectCaptionInsertHwpxLimits,
) -> Result<ParsedTarget, ObjectCaptionInsertHwpxError> {
    if source.is_empty() || source.len() > limits.0.section_bytes {
        return Err(ObjectCaptionInsertHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(ObjectCaptionInsertHwpxError::InputLimit);
    }
    let mut selected = None;
    let mut objects = 0_usize;
    for (index, candidate) in document.elements().iter().enumerate() {
        if !is_admitted_object(candidate) {
            continue;
        }
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(ObjectCaptionInsertHwpxError::UnsupportedObject)?;
        if !has_name(parent, "run") {
            continue;
        }
        objects = objects
            .checked_add(1)
            .ok_or(ObjectCaptionInsertHwpxError::InputLimit)?;
        if objects > limits.0.objects {
            return Err(ObjectCaptionInsertHwpxError::InputLimit);
        }
        let object_id = canonical_u32(source, strict_attribute(candidate, "id")?)?;
        let instance_id = canonical_u32(source, strict_attribute(candidate, "instid")?)?;
        if object_id == target.native_object_id
            && instance_id == target.native_instance_id
            && selected.replace(index).is_some()
        {
            return Err(ObjectCaptionInsertHwpxError::InvalidIdentity);
        }
    }
    let root = selected.ok_or(ObjectCaptionInsertHwpxError::InvalidIdentity)?;
    let captions = direct_children_named(&document, root, "caption")?;
    let caption = match captions.as_slice() {
        [] => None,
        [value] => Some(*value),
        _ => return Err(ObjectCaptionInsertHwpxError::UnsupportedProfile),
    };
    Ok(ParsedTarget {
        document,
        root,
        caption,
    })
}

fn operation_binding(
    plan: &ObjectSpecialPlan,
) -> Result<(&ObjectIdentity, &ObjectCaption), ObjectCaptionInsertHwpxError> {
    if plan.capability_id() != "obj.caption_insert" {
        return Err(ObjectCaptionInsertHwpxError::UnsupportedProfile);
    }
    match plan.operation() {
        ObjectSpecialOperation::InsertCaption { target, caption } => Ok((target, caption)),
        _ => Err(ObjectCaptionInsertHwpxError::UnsupportedProfile),
    }
}

fn verify_profile(caption: &ObjectCaption) -> Result<(), ObjectCaptionInsertHwpxError> {
    if caption.numbering != ObjectCaptionNumbering::None {
        return Err(ObjectCaptionInsertHwpxError::UnsupportedProfile);
    }
    Ok(())
}

fn caption_fragment(
    prefix: Option<&str>,
    caption: &ObjectCaption,
    limits: ObjectCaptionInsertHwpxLimits,
) -> Result<String, ObjectCaptionInsertHwpxError> {
    verify_profile(caption)?;
    let text = format!("{}{}", caption.label, caption.text);
    let escaped = escape_xml_text(&text)?;
    if escaped.len() > limits.0.text_bytes {
        return Err(ObjectCaptionInsertHwpxError::OutputLimit);
    }
    let name = |local: &str| match prefix {
        Some(value) => format!("{value}:{local}"),
        None => local.to_owned(),
    };
    Ok(format!(
        "<{caption_tag} side=\"{side}\" fullSz=\"0\" width=\"{width}\" gap=\"{gap}\" lastWidth=\"{width}\"><{sublist}><{paragraph}><{run}><{text_tag}>{escaped}</{text_tag}></{run}></{paragraph}></{sublist}></{caption_tag}>",
        caption_tag = name("caption"),
        side = caption_side(caption.side),
        width = caption.width_hwpunit,
        gap = caption.gap_hwpunit,
        sublist = name("subList"),
        paragraph = name("p"),
        run = name("run"),
        text_tag = name("t"),
    ))
}

fn verify_native_caption(
    source: &[u8],
    document: &PreservingXmlDocument,
    caption_index: usize,
    expected: &ObjectCaption,
    limits: ObjectCaptionInsertHwpxLimits,
) -> Result<(), ObjectCaptionInsertHwpxError> {
    verify_profile(expected)?;
    let caption = element(document, caption_index)?;
    let attributes = caption
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
        .count();
    if attributes != 5
        || lexical_value(source, strict_attribute(caption, "side")?)? != caption_side(expected.side)
        || lexical_value(source, strict_attribute(caption, "fullSz")?)? != "0"
        || canonical_u32(source, strict_attribute(caption, "width")?)? != expected.width_hwpunit
        || canonical_u32(source, strict_attribute(caption, "gap")?)? != expected.gap_hwpunit
        || canonical_u32(source, strict_attribute(caption, "lastWidth")?)? != expected.width_hwpunit
    {
        return Err(ObjectCaptionInsertHwpxError::ReadbackMismatch);
    }
    let sublist = only_direct_child(document, caption_index, "subList")?;
    let paragraph = only_direct_child(document, sublist, "p")?;
    let run = only_direct_child(document, paragraph, "run")?;
    let text = only_direct_child(document, run, "t")?;
    if element(document, text)?.first_child().is_some() {
        return Err(ObjectCaptionInsertHwpxError::UnsupportedProfile);
    }
    let span = element(document, text)?
        .content_span()
        .ok_or(ObjectCaptionInsertHwpxError::UnsupportedProfile)?;
    let lexical = std::str::from_utf8(
        source
            .get(span.start()..span.end())
            .ok_or(ObjectCaptionInsertHwpxError::InvalidText)?,
    )
    .map_err(|_| ObjectCaptionInsertHwpxError::InvalidText)?;
    if lexical.len() > limits.0.text_bytes
        || lexical.contains('<')
        || xml_unescape(lexical)? != format!("{}{}", expected.label, expected.text)
    {
        return Err(ObjectCaptionInsertHwpxError::ReadbackMismatch);
    }
    Ok(())
}

fn only_direct_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, ObjectCaptionInsertHwpxError> {
    let values = direct_children_named(document, parent, local_name)?;
    match values.as_slice() {
        [value] => Ok(*value),
        _ => Err(ObjectCaptionInsertHwpxError::UnsupportedProfile),
    }
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, ObjectCaptionInsertHwpxError> {
    let mut values = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let candidate = element(document, index)?;
        if has_name(candidate, local_name) {
            values
                .try_reserve(1)
                .map_err(|_| ObjectCaptionInsertHwpxError::AllocationFailed)?;
            values.push(index);
        }
        child = candidate.next_sibling();
    }
    Ok(values)
}

fn is_admitted_object(element: &XmlElementToken) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == "rect"
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn strict_attribute<'a>(
    element: &'a XmlElementToken,
    local_name: &str,
) -> Result<&'a XmlAttributeToken, ObjectCaptionInsertHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == local_name
    });
    let value = matches
        .next()
        .ok_or(ObjectCaptionInsertHwpxError::UnsupportedProfile)?;
    if matches.next().is_some() {
        return Err(ObjectCaptionInsertHwpxError::UnsupportedProfile);
    }
    Ok(value)
}

fn lexical_value<'a>(
    source: &'a [u8],
    attribute: &XmlAttributeToken,
) -> Result<&'a str, ObjectCaptionInsertHwpxError> {
    std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(ObjectCaptionInsertHwpxError::UnsupportedProfile)?,
    )
    .map_err(|_| ObjectCaptionInsertHwpxError::UnsupportedProfile)
}

fn canonical_u32(
    source: &[u8],
    attribute: &XmlAttributeToken,
) -> Result<u32, ObjectCaptionInsertHwpxError> {
    let value = lexical_value(source, attribute)?;
    if value.is_empty()
        || !value.bytes().all(|byte| byte.is_ascii_digit())
        || (value != "0" && value.starts_with('0'))
    {
        return Err(ObjectCaptionInsertHwpxError::InvalidIdentity);
    }
    value
        .parse::<u32>()
        .map_err(|_| ObjectCaptionInsertHwpxError::InvalidIdentity)
}

fn caption_side(value: ObjectCaptionSide) -> &'static str {
    match value {
        ObjectCaptionSide::Left => "LEFT",
        ObjectCaptionSide::Right => "RIGHT",
        ObjectCaptionSide::Top => "TOP",
        ObjectCaptionSide::Bottom => "BOTTOM",
    }
}

fn escape_xml_text(value: &str) -> Result<String, ObjectCaptionInsertHwpxError> {
    if value.chars().any(invalid_xml_character) {
        return Err(ObjectCaptionInsertHwpxError::InvalidText);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))
}

fn xml_unescape(value: &str) -> Result<String, ObjectCaptionInsertHwpxError> {
    let mut output = String::with_capacity(value.len());
    let mut rest = value;
    while let Some(position) = rest.find('&') {
        output.push_str(&rest[..position]);
        let tail = &rest[position..];
        let (character, consumed) = if tail.starts_with("&amp;") {
            ('&', 5)
        } else if tail.starts_with("&lt;") {
            ('<', 4)
        } else if tail.starts_with("&gt;") {
            ('>', 4)
        } else {
            return Err(ObjectCaptionInsertHwpxError::InvalidText);
        };
        output.push(character);
        rest = &tail[consumed..];
    }
    output.push_str(rest);
    Ok(output)
}

const fn invalid_xml_character(value: char) -> bool {
    !matches!(
        value as u32,
        0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF
    )
}

fn apply_insertion(
    source: &[u8],
    position: usize,
    insertion: &[u8],
    limits: ObjectCaptionInsertHwpxLimits,
) -> Result<Vec<u8>, ObjectCaptionInsertHwpxError> {
    let output_len = source
        .len()
        .checked_add(insertion.len())
        .ok_or(ObjectCaptionInsertHwpxError::OutputLimit)?;
    if position > source.len() || output_len > limits.0.output_bytes {
        return Err(ObjectCaptionInsertHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| ObjectCaptionInsertHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..position]);
    output.extend_from_slice(insertion);
    output.extend_from_slice(&source[position..]);
    Ok(output)
}

fn verify_insertion(
    source: &[u8],
    output: &[u8],
    position: usize,
    insertion: &[u8],
) -> Result<(), ObjectCaptionInsertHwpxError> {
    let insertion_end = position
        .checked_add(insertion.len())
        .ok_or(ObjectCaptionInsertHwpxError::PreservationMismatch)?;
    if source[..position] != output[..position]
        || insertion != &output[position..insertion_end]
        || source[position..] != output[insertion_end..]
    {
        return Err(ObjectCaptionInsertHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn validate_plan(
    plan: &ObjectCaptionInsertHwpxPlan,
    limits: ObjectCaptionInsertHwpxLimits,
) -> Result<(), ObjectCaptionInsertHwpxError> {
    let (target, caption) = operation_binding(&plan.domain_plan)?;
    if plan.schema_version != OBJECT_SPECIAL_SCHEMA_VERSION
        || plan.profile_id != OBJECT_CAPTION_INSERT_HWPX_PROFILE_ID
        || target != &plan.target
        || caption != &plan.caption
        || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(ObjectCaptionInsertHwpxError::PlanTampered);
    }
    verify_profile(&plan.caption)
}

fn plan_binding_sha256(
    plan: &ObjectCaptionInsertHwpxPlan,
    limits: ObjectCaptionInsertHwpxLimits,
) -> Result<String, ObjectCaptionInsertHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectCaptionInsertHwpxLimits,
) -> Result<Vec<u8>, ObjectCaptionInsertHwpxError> {
    let bytes =
        serde_json::to_vec(value).map_err(|_| ObjectCaptionInsertHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(ObjectCaptionInsertHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ObjectCaptionInsertHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ObjectCaptionInsertHwpxError::UnsupportedObject)
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, ObjectCaptionInsertHwpxError> {
    element
        .outer_span()
        .ok_or(ObjectCaptionInsertHwpxError::UnsupportedObject)
}

fn digest_span(source: &[u8], span: XmlByteSpan) -> Result<[u8; 32], ObjectCaptionInsertHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(ObjectCaptionInsertHwpxError::UnsupportedObject)?,
    )
    .into())
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
