use std::fmt;
use std::fmt::Write as _;

use domain_ir::{
    AlignStyle, AppearanceTargetKind, ArrowSize, ArrowStyle, ClassicShadow, ClassicShadowType,
    ColorTransform, ColorTransformKind, EffectColor, EffectScalar, FillAppearance, GlowEffect,
    GradientFill, GradientType, ImageAdjustment, ImageEffect, ImageFill, ImageFillMode,
    LineAppearance, LineEndCap, LinePattern, OBJECT_APPEARANCE_SCHEMA_VERSION, ObjectAppearance,
    ObjectAppearanceBuilder, ObjectAppearanceError, ObjectAppearanceLimits, ObjectAppearancePlan,
    ObjectHatchStyle as HatchStyle, OutlineStyle, PictureEffects, PictureShadow,
    PictureShadowStyle, ReflectionEffect, RgbColor, ScalarPair, SoftEdgeEffect, UnitFraction,
    UnitRange,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlTokenKind,
};

pub const OBJECT_APPEARANCE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.object-appearance-hwpx.hwpml-2011-static/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";
const FIXED_SCALE: i64 = 1_000_000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectAppearanceHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub output_bytes: usize,
    pub fragment_bytes: usize,
    pub numeric_text_bytes: usize,
}

impl Default for ObjectAppearanceHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 65_536,
            output_bytes: 32 * 1024 * 1024,
            fragment_bytes: 1024 * 1024,
            numeric_text_bytes: 64,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ObjectAppearanceHwpxLimits(ObjectAppearanceHwpxLimitConfig);

impl ObjectAppearanceHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_OBJECTS: usize = 262_144;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_FRAGMENT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_NUMERIC_TEXT_BYTES: usize = 256;

    /// Creates finite exact-source appearance limits without clamping.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or hard-ceiling-exceeding values.
    pub fn new(config: ObjectAppearanceHwpxLimitConfig) -> Result<Self, ObjectAppearanceHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
            || config.fragment_bytes == 0
            || config.fragment_bytes > Self::HARD_MAX_FRAGMENT_BYTES
            || config.fragment_bytes > config.output_bytes
            || config.numeric_text_bytes == 0
            || config.numeric_text_bytes > Self::HARD_MAX_NUMERIC_TEXT_BYTES
        {
            return Err(ObjectAppearanceHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectAppearanceHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectAppearanceHwpxReadback {
    pub target_kind: AppearanceTargetKind,
    pub appearance: ObjectAppearance,
    pub section_sha256: [u8; 32],
    pub object_sha256: [u8; 32],
    pub object_ordinal: usize,
    pub native_object_id: u32,
    pub native_instance_id: u32,
}

impl fmt::Debug for ObjectAppearanceHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearanceHwpxReadback")
            .field("target_kind", &self.target_kind)
            .field("object_ordinal", &self.object_ordinal)
            .field("appearance", &self.appearance)
            .field("identity", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct ObjectAppearanceHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    object_ordinal: usize,
    source_section_sha256: [u8; 32],
    source_object_sha256: [u8; 32],
    domain_plan: ObjectAppearancePlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl ObjectAppearanceHwpxPlan {
    #[must_use]
    pub const fn object_ordinal(&self) -> usize {
        self.object_ordinal
    }

    #[must_use]
    pub fn domain_plan(&self) -> &ObjectAppearancePlan {
        &self.domain_plan
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Returns bounded deterministic JSON for the immutable HWPX plan.
    ///
    /// # Errors
    ///
    /// Returns an output-limit or serialization failure.
    pub fn canonical_json(
        &self,
        limits: ObjectAppearanceHwpxLimits,
    ) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectAppearanceHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearanceHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("object_ordinal", &self.object_ordinal)
            .field(
                "capability_id",
                &self.domain_plan.operation().capability_id(),
            )
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectAppearanceHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_object_sha256: [u8; 32],
    pub output_object_sha256: [u8; 32],
    pub domain_plan_sha256: String,
    pub plan_sha256: String,
    pub source_bytes: usize,
    pub output_bytes: usize,
    pub modified_region_count: usize,
    pub outside_object_preserved: bool,
}

impl fmt::Debug for ObjectAppearanceHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectAppearanceHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("modified_region_count", &self.modified_region_count)
            .field("outside_object_preserved", &self.outside_object_preserved)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error)]
pub enum ObjectAppearanceHwpxError {
    #[error("object-appearance HWPX limits are invalid")]
    InvalidLimit,
    #[error("object-appearance HWPX section exceeds a finite limit")]
    InputLimit,
    #[error("object-appearance HWPX target is absent, nested, duplicated, or unsupported")]
    UnsupportedTarget,
    #[error("object-appearance HWPX attribute set is incomplete, duplicated, or unsupported")]
    InvalidAttribute,
    #[error("object-appearance HWPX number is noncanonical or outside the exact profile")]
    InvalidNumber,
    #[error("object-appearance HWPX enum is outside the reviewed public model")]
    InvalidEnum,
    #[error("object-appearance HWPX source section, object, identity, state, or flow drifted")]
    SourceDrift,
    #[error("object-appearance HWPX plan was tampered with")]
    PlanTampered,
    #[error("object-appearance HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("object-appearance HWPX allocation failed")]
    AllocationFailed,
    #[error("object-appearance HWPX lowered semantic readback differs")]
    ReadbackMismatch,
    #[error("object-appearance HWPX preservation proof differs")]
    PreservationMismatch,
    #[error("object-appearance domain validation failed")]
    Domain(#[from] ObjectAppearanceError),
    #[error("object-appearance preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl ObjectAppearanceHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_appearance_hwpx_invalid_limit",
            Self::InputLimit => "object_appearance_hwpx_input_limit",
            Self::UnsupportedTarget => "object_appearance_hwpx_unsupported_target",
            Self::InvalidAttribute => "object_appearance_hwpx_invalid_attribute",
            Self::InvalidNumber => "object_appearance_hwpx_invalid_number",
            Self::InvalidEnum => "object_appearance_hwpx_invalid_enum",
            Self::SourceDrift => "object_appearance_hwpx_source_drift",
            Self::PlanTampered => "object_appearance_hwpx_plan_tampered",
            Self::OutputLimit => "object_appearance_hwpx_output_limit",
            Self::AllocationFailed => "object_appearance_hwpx_allocation_failed",
            Self::ReadbackMismatch => "object_appearance_hwpx_readback_mismatch",
            Self::PreservationMismatch => "object_appearance_hwpx_preservation_mismatch",
            Self::Domain(_) => "object_appearance_hwpx_domain",
            Self::Preserving(_) => "object_appearance_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct ObjectAppearanceHwpxReader;

impl ObjectAppearanceHwpxReader {
    /// Strictly reads one direct-run static shape or picture appearance state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, unsupported, noncanonical or over-limit XML.
    pub fn read_in_section(
        source: &[u8],
        object_ordinal: usize,
        expected_native_object_id: u32,
        expected_native_instance_id: u32,
        appearance_limits: ObjectAppearanceLimits,
        hwpx_limits: ObjectAppearanceHwpxLimits,
    ) -> Result<ObjectAppearanceHwpxReadback, ObjectAppearanceHwpxError> {
        let parsed = parse_selected(source, object_ordinal, hwpx_limits)?;
        let (native_object_id, native_instance_id) = read_identity(&parsed)?;
        if native_object_id != expected_native_object_id
            || native_instance_id != expected_native_instance_id
        {
            return Err(ObjectAppearanceHwpxError::SourceDrift);
        }
        let appearance = read_appearance(&parsed, appearance_limits, hwpx_limits)?;
        Ok(ObjectAppearanceHwpxReadback {
            target_kind: parsed.target_kind,
            appearance,
            section_sha256: Sha256::digest(source).into(),
            object_sha256: parsed.object_sha256,
            object_ordinal,
            native_object_id,
            native_instance_id,
        })
    }
}

#[derive(Debug)]
pub struct ObjectAppearanceHwpxBuilder;

impl ObjectAppearanceHwpxBuilder {
    /// Binds a validated domain plan to one exact section and direct-run object.
    ///
    /// # Errors
    ///
    /// Rejects state, identity, source, plan or document-flow drift.
    pub fn plan(
        source: &[u8],
        object_ordinal: usize,
        domain_plan: &ObjectAppearancePlan,
        current_document_flow_sha256: &str,
        appearance_limits: ObjectAppearanceLimits,
        hwpx_limits: ObjectAppearanceHwpxLimits,
    ) -> Result<ObjectAppearanceHwpxPlan, ObjectAppearanceHwpxError> {
        let readback = ObjectAppearanceHwpxReader::read_in_section(
            source,
            object_ordinal,
            domain_plan.native_object_id(),
            domain_plan.native_instance_id(),
            appearance_limits,
            hwpx_limits,
        )?;
        if readback.target_kind != domain_plan.target_kind()
            || readback.appearance != *domain_plan.source()
        {
            return Err(ObjectAppearanceHwpxError::SourceDrift);
        }
        let _ = ObjectAppearanceBuilder::build(
            domain_plan,
            current_document_flow_sha256,
            appearance_limits,
        )?;
        let domain_plan_sha256 =
            hex(Sha256::digest(domain_plan.canonical_json(appearance_limits)?).into());
        let mut plan = ObjectAppearanceHwpxPlan {
            schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION,
            profile_id: OBJECT_APPEARANCE_HWPX_PROFILE_ID,
            object_ordinal,
            source_section_sha256: readback.section_sha256,
            source_object_sha256: readback.object_sha256,
            domain_plan: domain_plan.clone(),
            domain_plan_sha256,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_digest(&plan, hwpx_limits)?;
        let _ = plan.canonical_json(hwpx_limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct ObjectAppearanceHwpxLowerer;

impl ObjectAppearanceHwpxLowerer {
    /// Revalidates and lowers one immutable appearance plan into preserving section bytes.
    ///
    /// # Errors
    ///
    /// Rejects all plan, source, identity, state, flow, readback and preservation drift.
    pub fn lower_in_section(
        source: &[u8],
        plan: &ObjectAppearanceHwpxPlan,
        current_document_flow_sha256: &str,
        appearance_limits: ObjectAppearanceLimits,
        hwpx_limits: ObjectAppearanceHwpxLimits,
    ) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
        Self::lower_in_section_with_receipt(
            source,
            plan,
            current_document_flow_sha256,
            appearance_limits,
            hwpx_limits,
        )
        .map(|(bytes, _)| bytes)
    }

    /// Returns preserving output plus exact source/object/plan evidence.
    ///
    /// # Errors
    ///
    /// Applies the same fail-closed checks as [`Self::lower_in_section`].
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        plan: &ObjectAppearanceHwpxPlan,
        current_document_flow_sha256: &str,
        appearance_limits: ObjectAppearanceLimits,
        hwpx_limits: ObjectAppearanceHwpxLimits,
    ) -> Result<(Vec<u8>, ObjectAppearanceHwpxLoweringReceipt), ObjectAppearanceHwpxError> {
        validate_plan(plan, appearance_limits, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256 {
            return Err(ObjectAppearanceHwpxError::SourceDrift);
        }
        let parsed = parse_selected(source, plan.object_ordinal, hwpx_limits)?;
        if parsed.object_sha256 != plan.source_object_sha256 {
            return Err(ObjectAppearanceHwpxError::SourceDrift);
        }
        let (native_object_id, native_instance_id) = read_identity(&parsed)?;
        if native_object_id != plan.domain_plan.native_object_id()
            || native_instance_id != plan.domain_plan.native_instance_id()
            || parsed.target_kind != plan.domain_plan.target_kind()
        {
            return Err(ObjectAppearanceHwpxError::SourceDrift);
        }
        let source_appearance = read_appearance(&parsed, appearance_limits, hwpx_limits)?;
        if source_appearance != *plan.domain_plan.source() {
            return Err(ObjectAppearanceHwpxError::SourceDrift);
        }
        let semantic = ObjectAppearanceBuilder::build(
            &plan.domain_plan,
            current_document_flow_sha256,
            appearance_limits,
        )?;
        let (output, modified_region_count) =
            rewrite_appearance(source, &parsed, semantic.target(), hwpx_limits)?;
        let output_readback = ObjectAppearanceHwpxReader::read_in_section(
            &output,
            plan.object_ordinal,
            native_object_id,
            native_instance_id,
            appearance_limits,
            hwpx_limits,
        )?;
        if output_readback.target_kind != plan.domain_plan.target_kind()
            || output_readback.appearance != *semantic.target()
        {
            return Err(ObjectAppearanceHwpxError::ReadbackMismatch);
        }
        verify_outside_object_preserved(
            source,
            &output,
            parsed.object_span,
            output_readback.object_sha256,
        )?;
        let receipt = ObjectAppearanceHwpxLoweringReceipt {
            profile_id: OBJECT_APPEARANCE_HWPX_PROFILE_ID,
            capability_id: plan.domain_plan.operation().capability_id(),
            source_section_sha256: plan.source_section_sha256,
            output_section_sha256: output_readback.section_sha256,
            source_object_sha256: plan.source_object_sha256,
            output_object_sha256: output_readback.object_sha256,
            domain_plan_sha256: plan.domain_plan_sha256.clone(),
            plan_sha256: plan.plan_sha256.clone(),
            source_bytes: source.len(),
            output_bytes: output.len(),
            modified_region_count,
            outside_object_preserved: true,
        };
        Ok((output, receipt))
    }
}

fn validate_plan(
    plan: &ObjectAppearanceHwpxPlan,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<(), ObjectAppearanceHwpxError> {
    if plan.schema_version != OBJECT_APPEARANCE_SCHEMA_VERSION
        || plan.profile_id != OBJECT_APPEARANCE_HWPX_PROFILE_ID
        || hex(Sha256::digest(plan.domain_plan.canonical_json(appearance_limits)?).into())
            != plan.domain_plan_sha256
        || plan_digest(plan, hwpx_limits)? != plan.plan_sha256
    {
        return Err(ObjectAppearanceHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_digest(
    plan: &ObjectAppearanceHwpxPlan,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<String, ObjectAppearanceHwpxError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        profile_id: &'static str,
        object_ordinal: usize,
        source_section_sha256: [u8; 32],
        source_object_sha256: [u8; 32],
        domain_plan_sha256: &'a str,
    }
    let binding = Binding {
        schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION,
        profile_id: OBJECT_APPEARANCE_HWPX_PROFILE_ID,
        object_ordinal: plan.object_ordinal,
        source_section_sha256: plan.source_section_sha256,
        source_object_sha256: plan.source_object_sha256,
        domain_plan_sha256: &plan.domain_plan_sha256,
    };
    Ok(hex(
        Sha256::digest(serialize_bounded(&binding, limits)?).into()
    ))
}

struct ParsedObject {
    document: PreservingXmlDocument,
    root: usize,
    target_kind: AppearanceTargetKind,
    object_span: XmlByteSpan,
    object_sha256: [u8; 32],
    rendering: usize,
    line: Option<usize>,
    fill: Option<usize>,
    shadow: Option<usize>,
    effects: Option<usize>,
    image: Option<usize>,
}

fn parse_selected(
    source: &[u8],
    object_ordinal: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<ParsedObject, ObjectAppearanceHwpxError> {
    if source.is_empty() || source.len() > limits.0.section_bytes {
        return Err(ObjectAppearanceHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements || object_ordinal >= limits.0.objects {
        return Err(ObjectAppearanceHwpxError::InputLimit);
    }
    let (root, target_kind) = selected_run_object(&document, object_ordinal, limits)?;
    let rendering = unique_direct_child(&document, root, PARAGRAPH_NS, "renderingInfo")?
        .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
    let line = unique_direct_child(&document, root, PARAGRAPH_NS, "lineShape")?;
    let fill = unique_direct_child(&document, root, CORE_NS, "fillBrush")?;
    let shadow = unique_direct_child(&document, root, PARAGRAPH_NS, "shadow")?;
    let effects = unique_direct_child(&document, root, PARAGRAPH_NS, "effects")?;
    let image = unique_direct_child(&document, root, PARAGRAPH_NS, "img")?;
    match target_kind {
        AppearanceTargetKind::BasicShape => {
            if effects.is_some() || image.is_some() {
                return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
            }
        }
        AppearanceTargetKind::Picture => {
            if fill.is_some() || shadow.is_some() || effects.is_none() || image.is_none() {
                return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
            }
        }
    }
    let object_span = element(&document, root)?
        .outer_span()
        .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
    let object_sha256 = Sha256::digest(document.source_text(object_span)?.as_bytes()).into();
    Ok(ParsedObject {
        document,
        root,
        target_kind,
        object_span,
        object_sha256,
        rendering,
        line,
        fill,
        shadow,
        effects,
        image,
    })
}

fn selected_run_object(
    document: &PreservingXmlDocument,
    ordinal: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<(usize, AppearanceTargetKind), ObjectAppearanceHwpxError> {
    let mut seen = 0_usize;
    for (index, candidate) in document.elements().iter().enumerate() {
        let kind = if candidate.name().namespace() == Some(PARAGRAPH_NS) {
            match candidate.name().local_name() {
                "pic" => Some(AppearanceTargetKind::Picture),
                "line" | "rect" | "ellipse" | "polygon" | "curve" => {
                    Some(AppearanceTargetKind::BasicShape)
                }
                _ => None,
            }
        } else {
            None
        };
        let Some(kind) = kind else { continue };
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
        if parent.name().namespace() != Some(PARAGRAPH_NS) || parent.name().local_name() != "run" {
            continue;
        }
        if seen == ordinal {
            return Ok((index, kind));
        }
        seen = seen
            .checked_add(1)
            .ok_or(ObjectAppearanceHwpxError::InputLimit)?;
        if seen > limits.0.objects {
            return Err(ObjectAppearanceHwpxError::InputLimit);
        }
    }
    Err(ObjectAppearanceHwpxError::UnsupportedTarget)
}

fn read_identity(parsed: &ParsedObject) -> Result<(u32, u32), ObjectAppearanceHwpxError> {
    let root = element(&parsed.document, parsed.root)?;
    let id = unsigned(attribute(root, "id")?, u32::MAX)?;
    let instance = unsigned(attribute(root, "instid")?, u32::MAX)?;
    if id == 0 || instance == 0 {
        return Err(ObjectAppearanceHwpxError::InvalidNumber);
    }
    Ok((id, instance))
}

fn read_appearance(
    parsed: &ParsedObject,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<ObjectAppearance, ObjectAppearanceHwpxError> {
    let line = parsed
        .line
        .map(|index| parse_line(&parsed.document, index, hwpx_limits))
        .transpose()?;
    let appearance = match parsed.target_kind {
        AppearanceTargetKind::BasicShape => ObjectAppearance {
            line,
            fill: parsed
                .fill
                .map(|index| parse_fill(&parsed.document, index, appearance_limits, hwpx_limits))
                .transpose()?,
            shadow: parsed
                .shadow
                .map(|index| parse_classic_shadow(&parsed.document, index, hwpx_limits))
                .transpose()?,
            picture_effects: None,
            image_adjustment: None,
        },
        AppearanceTargetKind::Picture => ObjectAppearance {
            line,
            fill: None,
            shadow: None,
            picture_effects: parsed
                .effects
                .map(|index| {
                    parse_picture_effects(&parsed.document, index, appearance_limits, hwpx_limits)
                })
                .transpose()?
                .flatten(),
            image_adjustment: parsed
                .image
                .map(|index| parse_image_adjustment(&parsed.document, index, hwpx_limits))
                .transpose()?,
        },
    };
    appearance.validate(parsed.target_kind, appearance_limits)?;
    Ok(appearance)
}

fn parse_line(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<LineAppearance, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(
        value,
        &[
            "color",
            "width",
            "style",
            "endCap",
            "headStyle",
            "tailStyle",
            "headfill",
            "tailfill",
            "headSz",
            "tailSz",
            "outlineStyle",
            "alpha",
        ],
    )?;
    require_no_content(document, value)?;
    Ok(LineAppearance {
        color: color(attribute(value, "color")?)?,
        width_hwpunit: unsigned(attribute(value, "width")?, u32::MAX)?,
        pattern: parse_line_pattern(attribute(value, "style")?)?,
        end_cap: parse_line_end_cap(attribute(value, "endCap")?)?,
        head_style: parse_arrow_style(attribute(value, "headStyle")?)?,
        tail_style: parse_arrow_style(attribute(value, "tailStyle")?)?,
        head_filled: bool01(attribute(value, "headfill")?)?,
        tail_filled: bool01(attribute(value, "tailfill")?)?,
        head_size: parse_arrow_size(attribute(value, "headSz")?)?,
        tail_size: parse_arrow_size(attribute(value, "tailSz")?)?,
        outline_style: parse_outline_style(attribute(value, "outlineStyle")?)?,
        alpha: fraction(attribute(value, "alpha")?, limits)?,
    })
}

fn parse_fill(
    document: &PreservingXmlDocument,
    index: usize,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<FillAppearance, ObjectAppearanceHwpxError> {
    let root = element(document, index)?;
    require_exact_attributes(root, &[])?;
    let children = direct_children(document, index)?;
    if children.len() != 1 {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    let child = element(document, children[0])?;
    if child.name().namespace() != Some(CORE_NS) {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    match child.name().local_name() {
        "winBrush" => parse_window_brush(document, children[0], hwpx_limits),
        "gradation" => parse_gradient(document, children[0], appearance_limits, hwpx_limits),
        "imgBrush" => parse_image_fill(document, children[0], hwpx_limits),
        _ => Err(ObjectAppearanceHwpxError::UnsupportedTarget),
    }
}

fn parse_window_brush(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<FillAppearance, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_no_content(document, value)?;
    let hatch = optional_attribute(value, "hatchStyle")?;
    match hatch {
        None => {
            require_exact_attributes(value, &["faceColor", "hatchColor", "alpha"])?;
            if color(attribute(value, "hatchColor")?)?
                != (RgbColor {
                    red: 0,
                    green: 0,
                    blue: 0,
                })
            {
                return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
            }
            Ok(FillAppearance::Solid {
                color: color(attribute(value, "faceColor")?)?,
                alpha: fraction(attribute(value, "alpha")?, limits)?,
            })
        }
        Some(hatch) => {
            require_exact_attributes(value, &["faceColor", "hatchColor", "hatchStyle", "alpha"])?;
            Ok(FillAppearance::Pattern {
                face_color: color(attribute(value, "faceColor")?)?,
                hatch_color: color(attribute(value, "hatchColor")?)?,
                hatch_style: parse_hatch_style(hatch)?,
                alpha: fraction(attribute(value, "alpha")?, limits)?,
            })
        }
    }
}

fn parse_gradient(
    document: &PreservingXmlDocument,
    index: usize,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<FillAppearance, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(
        value,
        &[
            "type",
            "angle",
            "centerX",
            "centerY",
            "step",
            "colorNum",
            "stepCenter",
            "alpha",
        ],
    )?;
    let children = direct_children(document, index)?;
    let expected_count = usize::try_from(unsigned(attribute(value, "colorNum")?, u32::MAX)?)
        .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?;
    if children.len() != expected_count
        || children.len() < 2
        || children.len() > appearance_limits.config().gradient_colors
    {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    let mut colors = Vec::new();
    colors
        .try_reserve_exact(children.len())
        .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    for child in children {
        let color_element = element(document, child)?;
        if color_element.name().namespace() != Some(CORE_NS)
            || color_element.name().local_name() != "color"
        {
            return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
        }
        require_exact_attributes(color_element, &["value"])?;
        require_no_content(document, color_element)?;
        colors.push(color(attribute(color_element, "value")?)?);
    }
    Ok(FillAppearance::Gradient {
        gradient: GradientFill {
            gradient_type: parse_gradient_type(attribute(value, "type")?)?,
            angle_degrees: signed_i32(attribute(value, "angle")?)?,
            center_x_percent: signed_i32(attribute(value, "centerX")?)?,
            center_y_percent: signed_i32(attribute(value, "centerY")?)?,
            step_percent: signed_i32(attribute(value, "step")?)?,
            step_center_percent: signed_i32(attribute(value, "stepCenter")?)?,
            colors,
            alpha: fraction(attribute(value, "alpha")?, hwpx_limits)?,
        },
    })
}

fn parse_image_fill(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<FillAppearance, ObjectAppearanceHwpxError> {
    let root = element(document, index)?;
    require_exact_attributes(root, &["mode"])?;
    let image = unique_direct_child(document, index, CORE_NS, "img")?
        .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
    if direct_children(document, index)? != [image] {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    let image = element(document, image)?;
    require_exact_attributes(
        image,
        &["binaryItemIDRef", "bright", "contrast", "effect", "alpha"],
    )?;
    require_no_content(document, image)?;
    Ok(FillAppearance::Image {
        image: ImageFill {
            mode: parse_image_fill_mode(attribute(root, "mode")?)?,
            binary_item_id_ref: attribute(image, "binaryItemIDRef")?.to_owned(),
            brightness: signed_i32(attribute(image, "bright")?)?,
            contrast: signed_i32(attribute(image, "contrast")?)?,
            effect: parse_image_effect(attribute(image, "effect")?)?,
            alpha: fraction(attribute(image, "alpha")?, limits)?,
        },
    })
}

fn parse_classic_shadow(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<ClassicShadow, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(value, &["type", "color", "offsetX", "offsetY", "alpha"])?;
    require_no_content(document, value)?;
    Ok(ClassicShadow {
        shadow_type: parse_classic_shadow_type(attribute(value, "type")?)?,
        color: color(attribute(value, "color")?)?,
        offset_x_hwpunit: signed_i32(attribute(value, "offsetX")?)?,
        offset_y_hwpunit: signed_i32(attribute(value, "offsetY")?)?,
        alpha: fraction(attribute(value, "alpha")?, limits)?,
    })
}

fn parse_picture_effects(
    document: &PreservingXmlDocument,
    index: usize,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<Option<PictureEffects>, ObjectAppearanceHwpxError> {
    let root = element(document, index)?;
    require_exact_attributes(root, &[])?;
    let children = direct_children(document, index)?;
    if children.is_empty() {
        require_no_content(document, root)?;
        return Ok(None);
    }
    let mut effects = PictureEffects::default();
    for child in children {
        let value = element(document, child)?;
        if value.name().namespace() != Some(PARAGRAPH_NS) {
            return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
        }
        match value.name().local_name() {
            "pshadow" if effects.shadow.is_none() => {
                effects.shadow = Some(parse_picture_shadow(
                    document,
                    child,
                    appearance_limits,
                    hwpx_limits,
                )?);
            }
            "glow" if effects.glow.is_none() => {
                effects.glow = Some(parse_glow(document, child, appearance_limits, hwpx_limits)?);
            }
            "softEdge" if effects.soft_edge.is_none() => {
                effects.soft_edge = Some(parse_soft_edge(document, child, hwpx_limits)?);
            }
            "reflection" if effects.reflection.is_none() => {
                effects.reflection = Some(parse_reflection(document, child, hwpx_limits)?);
            }
            _ => return Err(ObjectAppearanceHwpxError::UnsupportedTarget),
        }
    }
    Ok(Some(effects))
}

fn parse_picture_shadow(
    document: &PreservingXmlDocument,
    index: usize,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<PictureShadow, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(
        value,
        &[
            "style",
            "alpha",
            "radius",
            "direction",
            "distance",
            "alignStyle",
            "rotationStyle",
        ],
    )?;
    let skew = required_child(document, index, "skew")?;
    let scale = required_child(document, index, "scale")?;
    let color = required_child(document, index, "effectsColor")?;
    if direct_children(document, index)? != [skew, scale, color] {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    Ok(PictureShadow {
        style: parse_picture_shadow_style(attribute(value, "style")?)?,
        alpha: fraction(attribute(value, "alpha")?, hwpx_limits)?,
        radius: scalar(attribute(value, "radius")?, appearance_limits, hwpx_limits)?,
        direction: scalar(
            attribute(value, "direction")?,
            appearance_limits,
            hwpx_limits,
        )?,
        distance: scalar(
            attribute(value, "distance")?,
            appearance_limits,
            hwpx_limits,
        )?,
        align_style: parse_align_style(attribute(value, "alignStyle")?)?,
        rotation_style: bool01(attribute(value, "rotationStyle")?)?,
        skew: parse_scalar_pair(document, skew, appearance_limits, hwpx_limits)?,
        scale: parse_scalar_pair(document, scale, appearance_limits, hwpx_limits)?,
        color: parse_effect_color(document, color, appearance_limits, hwpx_limits)?,
    })
}

fn parse_glow(
    document: &PreservingXmlDocument,
    index: usize,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<GlowEffect, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(value, &["alpha", "radius"])?;
    let color = required_child(document, index, "effectsColor")?;
    if direct_children(document, index)? != [color] {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    Ok(GlowEffect {
        alpha: fraction(attribute(value, "alpha")?, hwpx_limits)?,
        radius: scalar(attribute(value, "radius")?, appearance_limits, hwpx_limits)?,
        color: parse_effect_color(document, color, appearance_limits, hwpx_limits)?,
    })
}

fn parse_soft_edge(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<SoftEdgeEffect, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(value, &["radius"])?;
    require_no_content(document, value)?;
    Ok(SoftEdgeEffect {
        radius: EffectScalar(fixed_millionths(
            attribute(value, "radius")?,
            i64::MAX,
            limits,
        )?),
    })
}

fn parse_reflection(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<ReflectionEffect, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(
        value,
        &[
            "alignStyle",
            "radius",
            "direction",
            "distance",
            "rotationStyle",
            "fadeDirection",
        ],
    )?;
    let skew = required_child(document, index, "skew")?;
    let scale = required_child(document, index, "scale")?;
    let alpha = required_child(document, index, "alpha")?;
    let position = required_child(document, index, "pos")?;
    if direct_children(document, index)? != [skew, scale, alpha, position] {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    Ok(ReflectionEffect {
        align_style: parse_align_style(attribute(value, "alignStyle")?)?,
        radius: EffectScalar(fixed_millionths(
            attribute(value, "radius")?,
            i64::MAX,
            limits,
        )?),
        direction: EffectScalar(fixed_millionths(
            attribute(value, "direction")?,
            i64::MAX,
            limits,
        )?),
        distance: EffectScalar(fixed_millionths(
            attribute(value, "distance")?,
            i64::MAX,
            limits,
        )?),
        rotation_style: bool01(attribute(value, "rotationStyle")?)?,
        fade_direction: EffectScalar(fixed_millionths(
            attribute(value, "fadeDirection")?,
            i64::MAX,
            limits,
        )?),
        skew: parse_scalar_pair_unbounded(document, skew, limits)?,
        scale: parse_scalar_pair_unbounded(document, scale, limits)?,
        alpha: parse_unit_range(document, alpha, limits)?,
        position: parse_unit_range(document, position, limits)?,
    })
}

fn parse_scalar_pair(
    document: &PreservingXmlDocument,
    index: usize,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<ScalarPair, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(value, &["x", "y"])?;
    require_no_content(document, value)?;
    Ok(ScalarPair {
        x: scalar(attribute(value, "x")?, appearance_limits, hwpx_limits)?,
        y: scalar(attribute(value, "y")?, appearance_limits, hwpx_limits)?,
    })
}

fn parse_scalar_pair_unbounded(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<ScalarPair, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(value, &["x", "y"])?;
    require_no_content(document, value)?;
    Ok(ScalarPair {
        x: EffectScalar(fixed_millionths(attribute(value, "x")?, i64::MAX, limits)?),
        y: EffectScalar(fixed_millionths(attribute(value, "y")?, i64::MAX, limits)?),
    })
}

fn parse_unit_range(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<UnitRange, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(value, &["start", "end"])?;
    require_no_content(document, value)?;
    Ok(UnitRange {
        start: fraction(attribute(value, "start")?, limits)?,
        end: fraction(attribute(value, "end")?, limits)?,
    })
}

fn parse_effect_color(
    document: &PreservingXmlDocument,
    index: usize,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<EffectColor, ObjectAppearanceHwpxError> {
    let value = element(document, index)?;
    require_exact_attributes(value, &["type", "schemeIdx", "systemIdx", "presetIdx"])?;
    if attribute(value, "type")? != "RGB"
        || attribute(value, "schemeIdx")? != "-1"
        || attribute(value, "systemIdx")? != "-1"
        || attribute(value, "presetIdx")? != "-1"
    {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    let children = direct_children(document, index)?;
    let Some((&rgb_index, transform_indices)) = children.split_first() else {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    };
    if transform_indices.len() > appearance_limits.config().color_transforms {
        return Err(ObjectAppearanceHwpxError::InputLimit);
    }
    let rgb = element(document, rgb_index)?;
    if rgb.name().namespace() != Some(PARAGRAPH_NS) || rgb.name().local_name() != "rgb" {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    require_exact_attributes(rgb, &["r", "g", "b"])?;
    require_no_content(document, rgb)?;
    let mut transforms = Vec::new();
    transforms
        .try_reserve_exact(transform_indices.len())
        .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    for &transform_index in transform_indices {
        let transform = element(document, transform_index)?;
        if transform.name().namespace() != Some(PARAGRAPH_NS)
            || transform.name().local_name() != "effect"
        {
            return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
        }
        require_exact_attributes(transform, &["type", "value"])?;
        require_no_content(document, transform)?;
        transforms.push(ColorTransform {
            kind: parse_color_transform(attribute(transform, "type")?)?,
            value: scalar(
                attribute(transform, "value")?,
                appearance_limits,
                hwpx_limits,
            )?,
        });
    }
    Ok(EffectColor {
        rgb: RgbColor {
            red: u8::try_from(unsigned(attribute(rgb, "r")?, u32::from(u8::MAX))?)
                .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?,
            green: u8::try_from(unsigned(attribute(rgb, "g")?, u32::from(u8::MAX))?)
                .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?,
            blue: u8::try_from(unsigned(attribute(rgb, "b")?, u32::from(u8::MAX))?)
                .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?,
        },
        transforms,
    })
}

fn parse_image_adjustment(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<ImageAdjustment, ObjectAppearanceHwpxError> {
    let image = element(document, index)?;
    require_exact_attributes(
        image,
        &["binaryItemIDRef", "bright", "contrast", "effect", "alpha"],
    )?;
    require_no_content(document, image)?;
    let id = attribute(image, "binaryItemIDRef")?;
    if id.is_empty() || !id.is_ascii() {
        return Err(ObjectAppearanceHwpxError::InvalidAttribute);
    }
    Ok(ImageAdjustment {
        brightness: signed_i32(attribute(image, "bright")?)?,
        contrast: signed_i32(attribute(image, "contrast")?)?,
        effect: parse_image_effect(attribute(image, "effect")?)?,
        alpha: fraction(attribute(image, "alpha")?, limits)?,
    })
}

#[derive(Debug)]
struct ByteEdit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}

fn rewrite_appearance(
    source: &[u8],
    parsed: &ParsedObject,
    target: &ObjectAppearance,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<(Vec<u8>, usize), ObjectAppearanceHwpxError> {
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(8)
        .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    let insertion_span = element(&parsed.document, parsed.rendering)?
        .outer_span()
        .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
    let mut fragments = Vec::new();
    match parsed.target_kind {
        AppearanceTargetKind::BasicShape => {
            push_remove(&parsed.document, parsed.line, &mut edits)?;
            push_remove(&parsed.document, parsed.fill, &mut edits)?;
            push_remove(&parsed.document, parsed.shadow, &mut edits)?;
            if let Some(line) = &target.line {
                fragments.extend_from_slice(&line_fragment(line, limits)?);
            }
            if let Some(fill) = &target.fill {
                fragments.extend_from_slice(&fill_fragment(fill, limits)?);
            }
            if let Some(shadow) = &target.shadow {
                fragments.extend_from_slice(&classic_shadow_fragment(shadow, limits)?);
            }
        }
        AppearanceTargetKind::Picture => {
            push_remove(&parsed.document, parsed.line, &mut edits)?;
            if let Some(line) = &target.line {
                fragments.extend_from_slice(&line_fragment(line, limits)?);
            }
            let effects_index = parsed
                .effects
                .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
            let effects_span = element(&parsed.document, effects_index)?
                .outer_span()
                .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
            edits.push(ByteEdit {
                start: effects_span.start(),
                end: effects_span.end(),
                replacement: effects_fragment(target.picture_effects.as_ref(), limits)?,
            });
            let image_index = parsed
                .image
                .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
            let adjustment = target
                .image_adjustment
                .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?;
            push_attribute_edit(
                &parsed.document,
                image_index,
                "bright",
                adjustment.brightness.to_string(),
                &mut edits,
            )?;
            push_attribute_edit(
                &parsed.document,
                image_index,
                "contrast",
                adjustment.contrast.to_string(),
                &mut edits,
            )?;
            push_attribute_edit(
                &parsed.document,
                image_index,
                "effect",
                image_effect(adjustment.effect).to_owned(),
                &mut edits,
            )?;
            push_attribute_edit(
                &parsed.document,
                image_index,
                "alpha",
                fixed_text(i64::from(adjustment.alpha.millionths()))?,
                &mut edits,
            )?;
        }
    }
    if !fragments.is_empty() {
        if fragments.len() > limits.0.fragment_bytes {
            return Err(ObjectAppearanceHwpxError::OutputLimit);
        }
        edits.push(ByteEdit {
            start: insertion_span.end(),
            end: insertion_span.end(),
            replacement: fragments,
        });
    }
    let modified_region_count = edits.len();
    apply_edits(source, &mut edits, limits).map(|output| (output, modified_region_count))
}

fn push_remove(
    document: &PreservingXmlDocument,
    index: Option<usize>,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectAppearanceHwpxError> {
    if let Some(index) = index {
        edits.push(ByteEdit {
            start: element(document, index)?
                .outer_span()
                .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?
                .start(),
            end: element(document, index)?
                .outer_span()
                .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)?
                .end(),
            replacement: Vec::new(),
        });
    }
    Ok(())
}

fn push_attribute_edit(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    replacement: String,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectAppearanceHwpxError> {
    let span = unique_attribute(element(document, element_index)?, name)?.value_span();
    edits.push(ByteEdit {
        start: span.start(),
        end: span.end(),
        replacement: replacement.into_bytes(),
    });
    Ok(())
}

fn apply_edits(
    source: &[u8],
    edits: &mut [ByteEdit],
    limits: ObjectAppearanceHwpxLimits,
) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
    edits.sort_unstable_by_key(|edit| (edit.start, edit.end));
    let mut previous_end = 0_usize;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.start < previous_end || edit.end > source.len() {
            return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
        }
        previous_end = edit.end;
        output_len = output_len
            .checked_sub(edit.end - edit.start)
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(ObjectAppearanceHwpxError::OutputLimit)?;
    }
    if output_len > limits.0.output_bytes {
        return Err(ObjectAppearanceHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    let mut cursor = 0_usize;
    for edit in edits {
        output.extend_from_slice(&source[cursor..edit.start]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.end;
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(ObjectAppearanceHwpxError::OutputLimit);
    }
    Ok(output)
}

fn verify_outside_object_preserved(
    source: &[u8],
    output: &[u8],
    source_span: XmlByteSpan,
    output_object_sha256: [u8; 32],
) -> Result<(), ObjectAppearanceHwpxError> {
    let output_document = PreservingXmlDocument::parse(output)?;
    let output_span = output_document
        .elements()
        .iter()
        .find_map(|element| {
            let span = element.outer_span()?;
            let digest: [u8; 32] =
                Sha256::digest(output_document.source_text(span).ok()?.as_bytes()).into();
            (digest == output_object_sha256).then_some(span)
        })
        .ok_or(ObjectAppearanceHwpxError::PreservationMismatch)?;
    let mut restored = Vec::new();
    restored
        .try_reserve_exact(source.len())
        .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    restored.extend_from_slice(&output[..output_span.start()]);
    restored.extend_from_slice(&source[source_span.start()..source_span.end()]);
    restored.extend_from_slice(&output[output_span.end()..]);
    if restored != source {
        return Err(ObjectAppearanceHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn line_fragment(
    line: &LineAppearance,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
    let mut xml = String::new();
    write!(
        xml,
        concat!(
            "<hp:lineShape xmlns:hp=\"{}\" color=\"{}\" width=\"{}\" ",
            "style=\"{}\" endCap=\"{}\" headStyle=\"{}\" tailStyle=\"{}\" ",
            "headfill=\"{}\" tailfill=\"{}\" headSz=\"{}\" tailSz=\"{}\" ",
            "outlineStyle=\"{}\" alpha=\"{}\"/>"
        ),
        PARAGRAPH_NS,
        color_text(line.color),
        line.width_hwpunit,
        line_pattern(line.pattern),
        line_end_cap(line.end_cap),
        arrow_style(line.head_style),
        arrow_style(line.tail_style),
        bool_text(line.head_filled),
        bool_text(line.tail_filled),
        arrow_size(line.head_size),
        arrow_size(line.tail_size),
        outline_style(line.outline_style),
        fixed_text(i64::from(line.alpha.millionths()))?,
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    bounded_fragment(xml, limits)
}

fn fill_fragment(
    fill: &FillAppearance,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
    let mut xml = String::new();
    xml.push_str("<hc:fillBrush xmlns:hc=\"");
    xml.push_str(CORE_NS);
    xml.push_str("\">");
    match fill {
        FillAppearance::Solid { color, alpha } => {
            write!(
                xml,
                "<hc:winBrush faceColor=\"{}\" hatchColor=\"#000000\" alpha=\"{}\"/>",
                color_text(*color),
                fixed_text(i64::from(alpha.millionths()))?,
            )
            .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
        }
        FillAppearance::Pattern {
            face_color,
            hatch_color,
            hatch_style,
            alpha,
        } => {
            write!(
                xml,
                concat!(
                    "<hc:winBrush faceColor=\"{}\" hatchColor=\"{}\" ",
                    "hatchStyle=\"{}\" alpha=\"{}\"/>"
                ),
                color_text(*face_color),
                color_text(*hatch_color),
                hatch_style_text(*hatch_style),
                fixed_text(i64::from(alpha.millionths()))?,
            )
            .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
        }
        FillAppearance::Gradient { gradient } => write_gradient(&mut xml, gradient)?,
        FillAppearance::Image { image } => write_image_fill(&mut xml, image)?,
    }
    xml.push_str("</hc:fillBrush>");
    bounded_fragment(xml, limits)
}

fn write_gradient(
    xml: &mut String,
    gradient: &GradientFill,
) -> Result<(), ObjectAppearanceHwpxError> {
    write!(
        xml,
        concat!(
            "<hc:gradation type=\"{}\" angle=\"{}\" centerX=\"{}\" centerY=\"{}\" ",
            "step=\"{}\" colorNum=\"{}\" stepCenter=\"{}\" alpha=\"{}\">"
        ),
        gradient_type_text(gradient.gradient_type),
        gradient.angle_degrees,
        gradient.center_x_percent,
        gradient.center_y_percent,
        gradient.step_percent,
        gradient.colors.len(),
        gradient.step_center_percent,
        fixed_text(i64::from(gradient.alpha.millionths()))?,
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    for color in &gradient.colors {
        write!(xml, "<hc:color value=\"{}\"/>", color_text(*color))
            .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    }
    xml.push_str("</hc:gradation>");
    Ok(())
}

fn write_image_fill(xml: &mut String, image: &ImageFill) -> Result<(), ObjectAppearanceHwpxError> {
    let escaped_id = escape_attribute(&image.binary_item_id_ref)?;
    write!(
        xml,
        concat!(
            "<hc:imgBrush mode=\"{}\"><hc:img binaryItemIDRef=\"{}\" bright=\"{}\" ",
            "contrast=\"{}\" effect=\"{}\" alpha=\"{}\"/></hc:imgBrush>"
        ),
        image_fill_mode(image.mode),
        escaped_id,
        image.brightness,
        image.contrast,
        image_effect(image.effect),
        fixed_text(i64::from(image.alpha.millionths()))?,
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)
}

fn classic_shadow_fragment(
    shadow: &ClassicShadow,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
    bounded_fragment(
        format!(
            concat!(
                "<hp:shadow xmlns:hp=\"{}\" type=\"{}\" color=\"{}\" ",
                "offsetX=\"{}\" offsetY=\"{}\" alpha=\"{}\"/>"
            ),
            PARAGRAPH_NS,
            classic_shadow_type(shadow.shadow_type),
            color_text(shadow.color),
            shadow.offset_x_hwpunit,
            shadow.offset_y_hwpunit,
            fixed_text(i64::from(shadow.alpha.millionths()))?,
        ),
        limits,
    )
}

fn effects_fragment(
    effects: Option<&PictureEffects>,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
    let Some(effects) = effects else {
        return bounded_fragment(format!("<hp:effects xmlns:hp=\"{PARAGRAPH_NS}\"/>"), limits);
    };
    let mut xml = format!("<hp:effects xmlns:hp=\"{PARAGRAPH_NS}\">");
    if let Some(shadow) = &effects.shadow {
        write_picture_shadow(&mut xml, shadow)?;
    }
    if let Some(glow) = &effects.glow {
        write_glow(&mut xml, glow)?;
    }
    if let Some(soft_edge) = effects.soft_edge {
        write!(
            xml,
            "<hp:softEdge radius=\"{}\"/>",
            fixed_text(soft_edge.radius.millionths())?,
        )
        .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    }
    if let Some(reflection) = &effects.reflection {
        write_reflection(&mut xml, reflection)?;
    }
    xml.push_str("</hp:effects>");
    bounded_fragment(xml, limits)
}

fn write_picture_shadow(
    xml: &mut String,
    shadow: &PictureShadow,
) -> Result<(), ObjectAppearanceHwpxError> {
    write!(
        xml,
        concat!(
            "<hp:pshadow style=\"{}\" alpha=\"{}\" radius=\"{}\" direction=\"{}\" ",
            "distance=\"{}\" alignStyle=\"{}\" rotationStyle=\"{}\">"
        ),
        picture_shadow_style(shadow.style),
        fixed_text(i64::from(shadow.alpha.millionths()))?,
        fixed_text(shadow.radius.millionths())?,
        fixed_text(shadow.direction.millionths())?,
        fixed_text(shadow.distance.millionths())?,
        align_style(shadow.align_style),
        bool_text(shadow.rotation_style),
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    write_scalar_pair(xml, "skew", shadow.skew)?;
    write_scalar_pair(xml, "scale", shadow.scale)?;
    write_effect_color(xml, &shadow.color)?;
    xml.push_str("</hp:pshadow>");
    Ok(())
}

fn write_glow(xml: &mut String, glow: &GlowEffect) -> Result<(), ObjectAppearanceHwpxError> {
    write!(
        xml,
        "<hp:glow alpha=\"{}\" radius=\"{}\">",
        fixed_text(i64::from(glow.alpha.millionths()))?,
        fixed_text(glow.radius.millionths())?,
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    write_effect_color(xml, &glow.color)?;
    xml.push_str("</hp:glow>");
    Ok(())
}

fn write_reflection(
    xml: &mut String,
    reflection: &ReflectionEffect,
) -> Result<(), ObjectAppearanceHwpxError> {
    write!(
        xml,
        concat!(
            "<hp:reflection alignStyle=\"{}\" radius=\"{}\" direction=\"{}\" ",
            "distance=\"{}\" rotationStyle=\"{}\" fadeDirection=\"{}\">"
        ),
        align_style(reflection.align_style),
        fixed_text(reflection.radius.millionths())?,
        fixed_text(reflection.direction.millionths())?,
        fixed_text(reflection.distance.millionths())?,
        bool_text(reflection.rotation_style),
        fixed_text(reflection.fade_direction.millionths())?,
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    write_scalar_pair(xml, "skew", reflection.skew)?;
    write_scalar_pair(xml, "scale", reflection.scale)?;
    write_unit_range(xml, "alpha", reflection.alpha)?;
    write_unit_range(xml, "pos", reflection.position)?;
    xml.push_str("</hp:reflection>");
    Ok(())
}

fn write_scalar_pair(
    xml: &mut String,
    tag: &str,
    pair: ScalarPair,
) -> Result<(), ObjectAppearanceHwpxError> {
    write!(
        xml,
        "<hp:{tag} x=\"{}\" y=\"{}\"/>",
        fixed_text(pair.x.millionths())?,
        fixed_text(pair.y.millionths())?,
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)
}

fn write_unit_range(
    xml: &mut String,
    tag: &str,
    range: UnitRange,
) -> Result<(), ObjectAppearanceHwpxError> {
    write!(
        xml,
        "<hp:{tag} start=\"{}\" end=\"{}\"/>",
        fixed_text(i64::from(range.start.millionths()))?,
        fixed_text(i64::from(range.end.millionths()))?,
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)
}

fn write_effect_color(
    xml: &mut String,
    color: &EffectColor,
) -> Result<(), ObjectAppearanceHwpxError> {
    xml.push_str(
        "<hp:effectsColor type=\"RGB\" schemeIdx=\"-1\" systemIdx=\"-1\" presetIdx=\"-1\">",
    );
    write!(
        xml,
        "<hp:rgb r=\"{}\" g=\"{}\" b=\"{}\"/>",
        color.rgb.red, color.rgb.green, color.rgb.blue,
    )
    .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    for transform in &color.transforms {
        write!(
            xml,
            "<hp:effect type=\"{}\" value=\"{}\"/>",
            color_transform(transform.kind),
            fixed_text(transform.value.millionths())?,
        )
        .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    }
    xml.push_str("</hp:effectsColor>");
    Ok(())
}

fn bounded_fragment(
    xml: String,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
    if xml.len() > limits.0.fragment_bytes {
        return Err(ObjectAppearanceHwpxError::OutputLimit);
    }
    Ok(xml.into_bytes())
}

fn escape_attribute(value: &str) -> Result<String, ObjectAppearanceHwpxError> {
    if value.is_empty() || !value.is_ascii() {
        return Err(ObjectAppearanceHwpxError::InvalidAttribute);
    }
    let mut escaped = String::new();
    escaped
        .try_reserve(value.len())
        .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
    for character in value.chars() {
        match character {
            '&' => escaped.push_str("&amp;"),
            '<' => escaped.push_str("&lt;"),
            '"' => escaped.push_str("&quot;"),
            '\'' => escaped.push_str("&apos;"),
            _ if character.is_ascii_control() => {
                return Err(ObjectAppearanceHwpxError::InvalidAttribute);
            }
            _ => escaped.push(character),
        }
    }
    Ok(escaped)
}

fn parse_line_pattern(value: &str) -> Result<LinePattern, ObjectAppearanceHwpxError> {
    match value {
        "NONE" => Ok(LinePattern::None),
        "SOLID" => Ok(LinePattern::Solid),
        "DOT" => Ok(LinePattern::Dot),
        "DASH" => Ok(LinePattern::Dash),
        "DASH_DOT" => Ok(LinePattern::DashDot),
        "DASH_DOT_DOT" => Ok(LinePattern::DashDotDot),
        "LONG_DASH" => Ok(LinePattern::LongDash),
        "CIRCLE" => Ok(LinePattern::Circle),
        "DOUBLE_SLIM" => Ok(LinePattern::DoubleSlim),
        "SLIM_THICK" => Ok(LinePattern::SlimThick),
        "THICK_SLIM" => Ok(LinePattern::ThickSlim),
        "SLIM_THICK_SLIM" => Ok(LinePattern::SlimThickSlim),
        "WAVE" => Ok(LinePattern::Wave),
        "DOUBLEWAVE" => Ok(LinePattern::DoubleWave),
        "THICK3D" => Ok(LinePattern::Thick3d),
        "THICKREV3D" => Ok(LinePattern::ThickReverse3d),
        "3D" => Ok(LinePattern::ThreeD),
        "REV3D" => Ok(LinePattern::Reverse3d),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn line_pattern(value: LinePattern) -> &'static str {
    match value {
        LinePattern::None => "NONE",
        LinePattern::Solid => "SOLID",
        LinePattern::Dot => "DOT",
        LinePattern::Dash => "DASH",
        LinePattern::DashDot => "DASH_DOT",
        LinePattern::DashDotDot => "DASH_DOT_DOT",
        LinePattern::LongDash => "LONG_DASH",
        LinePattern::Circle => "CIRCLE",
        LinePattern::DoubleSlim => "DOUBLE_SLIM",
        LinePattern::SlimThick => "SLIM_THICK",
        LinePattern::ThickSlim => "THICK_SLIM",
        LinePattern::SlimThickSlim => "SLIM_THICK_SLIM",
        LinePattern::Wave => "WAVE",
        LinePattern::DoubleWave => "DOUBLEWAVE",
        LinePattern::Thick3d => "THICK3D",
        LinePattern::ThickReverse3d => "THICKREV3D",
        LinePattern::ThreeD => "3D",
        LinePattern::Reverse3d => "REV3D",
    }
}

fn parse_line_end_cap(value: &str) -> Result<LineEndCap, ObjectAppearanceHwpxError> {
    match value {
        "ROUND" => Ok(LineEndCap::Round),
        "FLAT" => Ok(LineEndCap::Flat),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn line_end_cap(value: LineEndCap) -> &'static str {
    match value {
        LineEndCap::Round => "ROUND",
        LineEndCap::Flat => "FLAT",
    }
}

fn parse_arrow_style(value: &str) -> Result<ArrowStyle, ObjectAppearanceHwpxError> {
    match value {
        "NORMAL" => Ok(ArrowStyle::Normal),
        "ARROW" => Ok(ArrowStyle::Arrow),
        "SPEAR" => Ok(ArrowStyle::Spear),
        "CONCAVE_ARROW" => Ok(ArrowStyle::ConcaveArrow),
        "EMPTY_DIAMOND" => Ok(ArrowStyle::EmptyDiamond),
        "EMPTY_CIRCLE" => Ok(ArrowStyle::EmptyCircle),
        "EMPTY_BOX" => Ok(ArrowStyle::EmptyBox),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn arrow_style(value: ArrowStyle) -> &'static str {
    match value {
        ArrowStyle::Normal => "NORMAL",
        ArrowStyle::Arrow => "ARROW",
        ArrowStyle::Spear => "SPEAR",
        ArrowStyle::ConcaveArrow => "CONCAVE_ARROW",
        ArrowStyle::EmptyDiamond => "EMPTY_DIAMOND",
        ArrowStyle::EmptyCircle => "EMPTY_CIRCLE",
        ArrowStyle::EmptyBox => "EMPTY_BOX",
    }
}

fn parse_arrow_size(value: &str) -> Result<ArrowSize, ObjectAppearanceHwpxError> {
    match value {
        "SMALL_SMALL" => Ok(ArrowSize::SmallSmall),
        "SMALL_MEDIUM" => Ok(ArrowSize::SmallMedium),
        "SMALL_LARGE" => Ok(ArrowSize::SmallLarge),
        "MEDIUM_SMALL" => Ok(ArrowSize::MediumSmall),
        "MEDIUM_MEDIUM" => Ok(ArrowSize::MediumMedium),
        "MEDIUM_LARGE" => Ok(ArrowSize::MediumLarge),
        "LARGE_SMALL" => Ok(ArrowSize::LargeSmall),
        "LARGE_MEDIUM" => Ok(ArrowSize::LargeMedium),
        "LARGE_LARGE" => Ok(ArrowSize::LargeLarge),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn arrow_size(value: ArrowSize) -> &'static str {
    match value {
        ArrowSize::SmallSmall => "SMALL_SMALL",
        ArrowSize::SmallMedium => "SMALL_MEDIUM",
        ArrowSize::SmallLarge => "SMALL_LARGE",
        ArrowSize::MediumSmall => "MEDIUM_SMALL",
        ArrowSize::MediumMedium => "MEDIUM_MEDIUM",
        ArrowSize::MediumLarge => "MEDIUM_LARGE",
        ArrowSize::LargeSmall => "LARGE_SMALL",
        ArrowSize::LargeMedium => "LARGE_MEDIUM",
        ArrowSize::LargeLarge => "LARGE_LARGE",
    }
}

fn parse_outline_style(value: &str) -> Result<OutlineStyle, ObjectAppearanceHwpxError> {
    match value {
        "NORMAL" => Ok(OutlineStyle::Normal),
        "OUTER" => Ok(OutlineStyle::Outer),
        "INNER" => Ok(OutlineStyle::Inner),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn outline_style(value: OutlineStyle) -> &'static str {
    match value {
        OutlineStyle::Normal => "NORMAL",
        OutlineStyle::Outer => "OUTER",
        OutlineStyle::Inner => "INNER",
    }
}

fn parse_hatch_style(value: &str) -> Result<HatchStyle, ObjectAppearanceHwpxError> {
    match value {
        "HORIZONTAL" => Ok(HatchStyle::Horizontal),
        "VERTICAL" => Ok(HatchStyle::Vertical),
        "BACK_SLASH" => Ok(HatchStyle::BackSlash),
        "SLASH" => Ok(HatchStyle::Slash),
        "CROSS" => Ok(HatchStyle::Cross),
        "CROSS_DIAGONAL" => Ok(HatchStyle::CrossDiagonal),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn hatch_style_text(value: HatchStyle) -> &'static str {
    match value {
        HatchStyle::Horizontal => "HORIZONTAL",
        HatchStyle::Vertical => "VERTICAL",
        HatchStyle::BackSlash => "BACK_SLASH",
        HatchStyle::Slash => "SLASH",
        HatchStyle::Cross => "CROSS",
        HatchStyle::CrossDiagonal => "CROSS_DIAGONAL",
    }
}

fn parse_gradient_type(value: &str) -> Result<GradientType, ObjectAppearanceHwpxError> {
    match value {
        "LINEAR" => Ok(GradientType::Linear),
        "RADIAL" => Ok(GradientType::Radial),
        "CONICAL" => Ok(GradientType::Conical),
        "SQUARE" => Ok(GradientType::Square),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn gradient_type_text(value: GradientType) -> &'static str {
    match value {
        GradientType::Linear => "LINEAR",
        GradientType::Radial => "RADIAL",
        GradientType::Conical => "CONICAL",
        GradientType::Square => "SQUARE",
    }
}

fn parse_image_fill_mode(value: &str) -> Result<ImageFillMode, ObjectAppearanceHwpxError> {
    match value {
        "TILE" => Ok(ImageFillMode::Tile),
        "TILE_HORZ_TOP" => Ok(ImageFillMode::TileHorizontalTop),
        "TILE_HORZ_BOTTOM" => Ok(ImageFillMode::TileHorizontalBottom),
        "TILE_VERT_LEFT" => Ok(ImageFillMode::TileVerticalLeft),
        "TILE_VERT_RIGHT" => Ok(ImageFillMode::TileVerticalRight),
        "TOTAL" => Ok(ImageFillMode::Total),
        "CENTER" => Ok(ImageFillMode::Center),
        "CENTER_TOP" => Ok(ImageFillMode::CenterTop),
        "CENTER_BOTTOM" => Ok(ImageFillMode::CenterBottom),
        "LEFT_CENTER" => Ok(ImageFillMode::LeftCenter),
        "LEFT_TOP" => Ok(ImageFillMode::LeftTop),
        "LEFT_BOTTOM" => Ok(ImageFillMode::LeftBottom),
        "RIGHT_CENTER" => Ok(ImageFillMode::RightCenter),
        "RIGHT_TOP" => Ok(ImageFillMode::RightTop),
        "RIGHT_BOTTOM" => Ok(ImageFillMode::RightBottom),
        "ZOOM" => Ok(ImageFillMode::Zoom),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn image_fill_mode(value: ImageFillMode) -> &'static str {
    match value {
        ImageFillMode::Tile => "TILE",
        ImageFillMode::TileHorizontalTop => "TILE_HORZ_TOP",
        ImageFillMode::TileHorizontalBottom => "TILE_HORZ_BOTTOM",
        ImageFillMode::TileVerticalLeft => "TILE_VERT_LEFT",
        ImageFillMode::TileVerticalRight => "TILE_VERT_RIGHT",
        ImageFillMode::Total => "TOTAL",
        ImageFillMode::Center => "CENTER",
        ImageFillMode::CenterTop => "CENTER_TOP",
        ImageFillMode::CenterBottom => "CENTER_BOTTOM",
        ImageFillMode::LeftCenter => "LEFT_CENTER",
        ImageFillMode::LeftTop => "LEFT_TOP",
        ImageFillMode::LeftBottom => "LEFT_BOTTOM",
        ImageFillMode::RightCenter => "RIGHT_CENTER",
        ImageFillMode::RightTop => "RIGHT_TOP",
        ImageFillMode::RightBottom => "RIGHT_BOTTOM",
        ImageFillMode::Zoom => "ZOOM",
    }
}

fn parse_image_effect(value: &str) -> Result<ImageEffect, ObjectAppearanceHwpxError> {
    match value {
        "REAL_PIC" => Ok(ImageEffect::RealPicture),
        "GRAY_SCALE" => Ok(ImageEffect::GrayScale),
        "BLACK_WHITE" => Ok(ImageEffect::BlackWhite),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn image_effect(value: ImageEffect) -> &'static str {
    match value {
        ImageEffect::RealPicture => "REAL_PIC",
        ImageEffect::GrayScale => "GRAY_SCALE",
        ImageEffect::BlackWhite => "BLACK_WHITE",
    }
}

fn parse_classic_shadow_type(value: &str) -> Result<ClassicShadowType, ObjectAppearanceHwpxError> {
    match value {
        "PARELLEL_LEFTTOP" => Ok(ClassicShadowType::ParallelLeftTop),
        "PARELLEL_RIGHTTOP" => Ok(ClassicShadowType::ParallelRightTop),
        "PARELLEL_LEFTBOTTOM" => Ok(ClassicShadowType::ParallelLeftBottom),
        "PARELLEL_RIGHTBOTTOM" => Ok(ClassicShadowType::ParallelRightBottom),
        "SHEAR_LEFTTOP" => Ok(ClassicShadowType::ShearLeftTop),
        "SHEAR_RIGHTTOP" => Ok(ClassicShadowType::ShearRightTop),
        "SHEAR_LEFTBOTTOM" => Ok(ClassicShadowType::ShearLeftBottom),
        "SHEAR_RIGHTBOTTOM" => Ok(ClassicShadowType::ShearRightBottom),
        "PERS_LEFTTOP" => Ok(ClassicShadowType::PerspectiveLeftTop),
        "PERS_RIGHTTOP" => Ok(ClassicShadowType::PerspectiveRightTop),
        "PERS_LEFTBOTTOM" => Ok(ClassicShadowType::PerspectiveLeftBottom),
        "PERS_RIGHTBOTTOM" => Ok(ClassicShadowType::PerspectiveRightBottom),
        "SCALE_NARROW" => Ok(ClassicShadowType::ScaleNarrow),
        "SCALE_ENLARGE" => Ok(ClassicShadowType::ScaleEnlarge),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn classic_shadow_type(value: ClassicShadowType) -> &'static str {
    match value {
        ClassicShadowType::ParallelLeftTop => "PARELLEL_LEFTTOP",
        ClassicShadowType::ParallelRightTop => "PARELLEL_RIGHTTOP",
        ClassicShadowType::ParallelLeftBottom => "PARELLEL_LEFTBOTTOM",
        ClassicShadowType::ParallelRightBottom => "PARELLEL_RIGHTBOTTOM",
        ClassicShadowType::ShearLeftTop => "SHEAR_LEFTTOP",
        ClassicShadowType::ShearRightTop => "SHEAR_RIGHTTOP",
        ClassicShadowType::ShearLeftBottom => "SHEAR_LEFTBOTTOM",
        ClassicShadowType::ShearRightBottom => "SHEAR_RIGHTBOTTOM",
        ClassicShadowType::PerspectiveLeftTop => "PERS_LEFTTOP",
        ClassicShadowType::PerspectiveRightTop => "PERS_RIGHTTOP",
        ClassicShadowType::PerspectiveLeftBottom => "PERS_LEFTBOTTOM",
        ClassicShadowType::PerspectiveRightBottom => "PERS_RIGHTBOTTOM",
        ClassicShadowType::ScaleNarrow => "SCALE_NARROW",
        ClassicShadowType::ScaleEnlarge => "SCALE_ENLARGE",
    }
}

fn parse_picture_shadow_style(
    value: &str,
) -> Result<PictureShadowStyle, ObjectAppearanceHwpxError> {
    match value {
        "OUTSIDE" => Ok(PictureShadowStyle::Outside),
        "INSIDE" => Ok(PictureShadowStyle::Inside),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn picture_shadow_style(value: PictureShadowStyle) -> &'static str {
    match value {
        PictureShadowStyle::Outside => "OUTSIDE",
        PictureShadowStyle::Inside => "INSIDE",
    }
}

fn parse_align_style(value: &str) -> Result<AlignStyle, ObjectAppearanceHwpxError> {
    match value {
        "TOP_LEFT" => Ok(AlignStyle::TopLeft),
        "TOP" => Ok(AlignStyle::Top),
        "TOP_RIGHT" => Ok(AlignStyle::TopRight),
        "LEFT" => Ok(AlignStyle::Left),
        "CENTER" => Ok(AlignStyle::Center),
        "RIGHT" => Ok(AlignStyle::Right),
        "BOTTOM_LEFT" => Ok(AlignStyle::BottomLeft),
        "BOTTOM" => Ok(AlignStyle::Bottom),
        "BOTTOM_RIGHT" => Ok(AlignStyle::BottomRight),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn align_style(value: AlignStyle) -> &'static str {
    match value {
        AlignStyle::TopLeft => "TOP_LEFT",
        AlignStyle::Top => "TOP",
        AlignStyle::TopRight => "TOP_RIGHT",
        AlignStyle::Left => "LEFT",
        AlignStyle::Center => "CENTER",
        AlignStyle::Right => "RIGHT",
        AlignStyle::BottomLeft => "BOTTOM_LEFT",
        AlignStyle::Bottom => "BOTTOM",
        AlignStyle::BottomRight => "BOTTOM_RIGHT",
    }
}

fn parse_color_transform(value: &str) -> Result<ColorTransformKind, ObjectAppearanceHwpxError> {
    match value {
        "ALPHA" => Ok(ColorTransformKind::Alpha),
        "ALPHA_MOD" => Ok(ColorTransformKind::AlphaMod),
        "ALPHA_OFF" => Ok(ColorTransformKind::AlphaOff),
        "RED" => Ok(ColorTransformKind::Red),
        "RED_MOD" => Ok(ColorTransformKind::RedMod),
        "RED_OFF" => Ok(ColorTransformKind::RedOff),
        "GREEN" => Ok(ColorTransformKind::Green),
        "GREEN_MOD" => Ok(ColorTransformKind::GreenMod),
        "GREEN_OFF" => Ok(ColorTransformKind::GreenOff),
        "BLUE" => Ok(ColorTransformKind::Blue),
        "BLUE_MOD" => Ok(ColorTransformKind::BlueMod),
        "BLUE_OFF" => Ok(ColorTransformKind::BlueOff),
        "HUE" => Ok(ColorTransformKind::Hue),
        "HUE_MOD" => Ok(ColorTransformKind::HueMod),
        "HUE_OFF" => Ok(ColorTransformKind::HueOff),
        "SAT" => Ok(ColorTransformKind::Saturation),
        "SAT_MOD" => Ok(ColorTransformKind::SaturationMod),
        "SAT_OFF" => Ok(ColorTransformKind::SaturationOff),
        "LUM" => Ok(ColorTransformKind::Luminance),
        "LUM_MOD" => Ok(ColorTransformKind::LuminanceMod),
        "LUM_OFF" => Ok(ColorTransformKind::LuminanceOff),
        "SHADE" => Ok(ColorTransformKind::Shade),
        "TINT" => Ok(ColorTransformKind::Tint),
        "GRAY" => Ok(ColorTransformKind::Gray),
        "COMP" => Ok(ColorTransformKind::Complement),
        "GAMMA" => Ok(ColorTransformKind::Gamma),
        "INV_GAMMA" => Ok(ColorTransformKind::InverseGamma),
        "INV" => Ok(ColorTransformKind::Inverse),
        _ => Err(ObjectAppearanceHwpxError::InvalidEnum),
    }
}

const fn color_transform(value: ColorTransformKind) -> &'static str {
    match value {
        ColorTransformKind::Alpha => "ALPHA",
        ColorTransformKind::AlphaMod => "ALPHA_MOD",
        ColorTransformKind::AlphaOff => "ALPHA_OFF",
        ColorTransformKind::Red => "RED",
        ColorTransformKind::RedMod => "RED_MOD",
        ColorTransformKind::RedOff => "RED_OFF",
        ColorTransformKind::Green => "GREEN",
        ColorTransformKind::GreenMod => "GREEN_MOD",
        ColorTransformKind::GreenOff => "GREEN_OFF",
        ColorTransformKind::Blue => "BLUE",
        ColorTransformKind::BlueMod => "BLUE_MOD",
        ColorTransformKind::BlueOff => "BLUE_OFF",
        ColorTransformKind::Hue => "HUE",
        ColorTransformKind::HueMod => "HUE_MOD",
        ColorTransformKind::HueOff => "HUE_OFF",
        ColorTransformKind::Saturation => "SAT",
        ColorTransformKind::SaturationMod => "SAT_MOD",
        ColorTransformKind::SaturationOff => "SAT_OFF",
        ColorTransformKind::Luminance => "LUM",
        ColorTransformKind::LuminanceMod => "LUM_MOD",
        ColorTransformKind::LuminanceOff => "LUM_OFF",
        ColorTransformKind::Shade => "SHADE",
        ColorTransformKind::Tint => "TINT",
        ColorTransformKind::Gray => "GRAY",
        ColorTransformKind::Complement => "COMP",
        ColorTransformKind::Gamma => "GAMMA",
        ColorTransformKind::InverseGamma => "INV_GAMMA",
        ColorTransformKind::Inverse => "INV",
    }
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ObjectAppearanceHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)
}

fn unique_direct_child(
    document: &PreservingXmlDocument,
    parent: usize,
    namespace: &str,
    local_name: &str,
) -> Result<Option<usize>, ObjectAppearanceHwpxError> {
    let mut found = None;
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let value = element(document, index)?;
        if value.name().namespace() == Some(namespace)
            && value.name().local_name() == local_name
            && found.replace(index).is_some()
        {
            return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
        }
        child = value.next_sibling();
    }
    Ok(found)
}

fn required_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, ObjectAppearanceHwpxError> {
    unique_direct_child(document, parent, PARAGRAPH_NS, local_name)?
        .ok_or(ObjectAppearanceHwpxError::UnsupportedTarget)
}

fn direct_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, ObjectAppearanceHwpxError> {
    if document.tokens().iter().any(|token| {
        token.element_index() == Some(parent)
            && matches!(
                token.kind(),
                XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment
            )
    }) {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    let mut output = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        output
            .try_reserve(1)
            .map_err(|_| ObjectAppearanceHwpxError::AllocationFailed)?;
        output.push(index);
        child = element(document, index)?.next_sibling();
    }
    Ok(output)
}

fn unique_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, ObjectAppearanceHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(ObjectAppearanceHwpxError::InvalidAttribute)?;
    if matches.next().is_some() {
        return Err(ObjectAppearanceHwpxError::InvalidAttribute);
    }
    Ok(value)
}

fn attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, ObjectAppearanceHwpxError> {
    Ok(unique_attribute(element, name)?.semantic_value())
}

fn optional_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<Option<&'a str>, ObjectAppearanceHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches.next();
    if matches.next().is_some() {
        return Err(ObjectAppearanceHwpxError::InvalidAttribute);
    }
    Ok(value.map(XmlAttributeToken::semantic_value))
}

fn require_exact_attributes(
    element: &XmlElementToken,
    expected: &[&str],
) -> Result<(), ObjectAppearanceHwpxError> {
    let actual = element
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
        .collect::<Vec<_>>();
    if actual.len() != expected.len()
        || actual.iter().any(|attribute| {
            attribute.name().namespace().is_some()
                || !expected.contains(&attribute.name().local_name())
        })
        || expected.iter().any(|name| {
            actual
                .iter()
                .filter(|attribute| attribute.name().local_name() == *name)
                .count()
                != 1
        })
    {
        return Err(ObjectAppearanceHwpxError::InvalidAttribute);
    }
    Ok(())
}

fn require_no_content(
    document: &PreservingXmlDocument,
    element: &XmlElementToken,
) -> Result<(), ObjectAppearanceHwpxError> {
    if element.first_child().is_some()
        || element.content_span().is_some_and(|span| {
            document
                .source_text(span)
                .map_or(true, |text| !text.trim().is_empty())
        })
    {
        return Err(ObjectAppearanceHwpxError::UnsupportedTarget);
    }
    Ok(())
}

fn color(value: &str) -> Result<RgbColor, ObjectAppearanceHwpxError> {
    let bytes = value.as_bytes();
    if bytes.len() != 7 || bytes[0] != b'#' || !bytes[1..].iter().all(u8::is_ascii_hexdigit) {
        return Err(ObjectAppearanceHwpxError::InvalidAttribute);
    }
    let parse = |offset| {
        u8::from_str_radix(&value[offset..offset + 2], 16)
            .map_err(|_| ObjectAppearanceHwpxError::InvalidAttribute)
    };
    Ok(RgbColor {
        red: parse(1)?,
        green: parse(3)?,
        blue: parse(5)?,
    })
}

fn color_text(value: RgbColor) -> String {
    format!("#{:02X}{:02X}{:02X}", value.red, value.green, value.blue)
}

fn bool01(value: &str) -> Result<bool, ObjectAppearanceHwpxError> {
    match value {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(ObjectAppearanceHwpxError::InvalidNumber),
    }
}

const fn bool_text(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}

fn unsigned(value: &str, maximum: u32) -> Result<u32, ObjectAppearanceHwpxError> {
    if !canonical_unsigned(value) {
        return Err(ObjectAppearanceHwpxError::InvalidNumber);
    }
    let parsed = value
        .parse::<u32>()
        .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?;
    if parsed > maximum {
        return Err(ObjectAppearanceHwpxError::InvalidNumber);
    }
    Ok(parsed)
}

fn signed_i32(value: &str) -> Result<i32, ObjectAppearanceHwpxError> {
    if !canonical_signed(value) {
        return Err(ObjectAppearanceHwpxError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)
}

fn canonical_unsigned(value: &str) -> bool {
    !value.is_empty()
        && value.bytes().all(|byte| byte.is_ascii_digit())
        && (value == "0" || !value.starts_with('0'))
}

fn canonical_signed(value: &str) -> bool {
    if let Some(rest) = value.strip_prefix('-') {
        !rest.is_empty() && rest.bytes().all(|byte| byte.is_ascii_digit()) && !rest.starts_with('0')
    } else {
        canonical_unsigned(value)
    }
}

fn fraction(
    value: &str,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<UnitFraction, ObjectAppearanceHwpxError> {
    let value = fixed_millionths(value, FIXED_SCALE, limits)?;
    let value = u32::try_from(value).map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?;
    UnitFraction::new(value).map_err(ObjectAppearanceHwpxError::Domain)
}

fn scalar(
    value: &str,
    appearance_limits: ObjectAppearanceLimits,
    hwpx_limits: ObjectAppearanceHwpxLimits,
) -> Result<EffectScalar, ObjectAppearanceHwpxError> {
    Ok(EffectScalar(fixed_millionths(
        value,
        appearance_limits.config().scalar_magnitude_millionths,
        hwpx_limits,
    )?))
}

fn fixed_millionths(
    value: &str,
    maximum: i64,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<i64, ObjectAppearanceHwpxError> {
    if value.is_empty() || value.len() > limits.0.numeric_text_bytes || value.starts_with('+') {
        return Err(ObjectAppearanceHwpxError::InvalidNumber);
    }
    let (negative, unsigned) = value
        .strip_prefix('-')
        .map_or((false, value), |rest| (true, rest));
    if unsigned.is_empty() {
        return Err(ObjectAppearanceHwpxError::InvalidNumber);
    }
    let mut parts = unsigned.split('.');
    let integer = parts
        .next()
        .ok_or(ObjectAppearanceHwpxError::InvalidNumber)?;
    let fractional = parts.next();
    if parts.next().is_some()
        || !canonical_unsigned(integer)
        || fractional.is_some_and(|digits| {
            digits.is_empty()
                || digits.len() > 6
                || !digits.bytes().all(|byte| byte.is_ascii_digit())
        })
    {
        return Err(ObjectAppearanceHwpxError::InvalidNumber);
    }
    let integer_value = integer
        .parse::<i64>()
        .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?;
    let fraction_value = match fractional {
        Some(digits) => {
            let parsed = digits
                .parse::<i64>()
                .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?;
            let digits_len = u32::try_from(digits.len())
                .map_err(|_| ObjectAppearanceHwpxError::InvalidNumber)?;
            parsed
                .checked_mul(10_i64.pow(6_u32.saturating_sub(digits_len)))
                .ok_or(ObjectAppearanceHwpxError::InvalidNumber)?
        }
        None => 0,
    };
    let magnitude = integer_value
        .checked_mul(FIXED_SCALE)
        .and_then(|whole| whole.checked_add(fraction_value))
        .ok_or(ObjectAppearanceHwpxError::InvalidNumber)?;
    let signed = if negative {
        magnitude
            .checked_neg()
            .ok_or(ObjectAppearanceHwpxError::InvalidNumber)?
    } else {
        magnitude
    };
    if signed
        .checked_abs()
        .is_none_or(|absolute| absolute > maximum)
    {
        return Err(ObjectAppearanceHwpxError::InvalidNumber);
    }
    Ok(signed)
}

fn fixed_text(value: i64) -> Result<String, ObjectAppearanceHwpxError> {
    let negative = value.is_negative();
    let magnitude = value
        .checked_abs()
        .ok_or(ObjectAppearanceHwpxError::InvalidNumber)?;
    let whole = magnitude / FIXED_SCALE;
    let fraction = magnitude % FIXED_SCALE;
    let mut output = if fraction == 0 {
        whole.to_string()
    } else {
        let mut fraction_text = format!("{fraction:06}");
        while fraction_text.ends_with('0') {
            let _ = fraction_text.pop();
        }
        format!("{whole}.{fraction_text}")
    };
    if negative && magnitude != 0 {
        output.insert(0, '-');
    }
    Ok(output)
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectAppearanceHwpxLimits,
) -> Result<Vec<u8>, ObjectAppearanceHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectAppearanceHwpxError::OutputLimit)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(ObjectAppearanceHwpxError::OutputLimit);
    }
    Ok(bytes)
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

#[cfg(test)]
#[allow(clippy::expect_used)] // Test construction uses expectations to keep tamper failures local.
mod tests {
    use domain_ir::{
        AppearanceOperation, AppearanceTargetKind, ArrowSize, ArrowStyle, LineEndCap, LinePattern,
        LogicalId, ObjectAppearanceLimitConfig, ObjectAppearanceRequest,
        ObjectAppearanceRequestDraft,
    };

    use super::*;

    const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

    #[test]
    fn tampered_private_plan_binding_is_rejected() {
        let appearance_limits = ObjectAppearanceLimits::new(ObjectAppearanceLimitConfig::default())
            .expect("appearance limits");
        let hwpx_limits =
            ObjectAppearanceHwpxLimits::new(ObjectAppearanceHwpxLimitConfig::default())
                .expect("HWPX limits");
        let target = ObjectAppearance {
            line: Some(LineAppearance {
                color: RgbColor {
                    red: 1,
                    green: 2,
                    blue: 3,
                },
                width_hwpunit: 10,
                pattern: LinePattern::Solid,
                end_cap: LineEndCap::Flat,
                head_style: ArrowStyle::Normal,
                tail_style: ArrowStyle::Normal,
                head_filled: false,
                tail_filled: false,
                head_size: ArrowSize::SmallSmall,
                tail_size: ArrowSize::SmallSmall,
                outline_style: OutlineStyle::Normal,
                alpha: UnitFraction::new(0).expect("alpha"),
            }),
            ..ObjectAppearance::default()
        };
        let request = ObjectAppearanceRequest::from_draft(
            ObjectAppearanceRequestDraft {
                schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request").expect("request id"),
                logical_object_id: LogicalId::parse("object").expect("object id"),
                native_object_id: 1,
                native_instance_id: 2,
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_B.to_owned(),
                target_kind: AppearanceTargetKind::BasicShape,
                operation: AppearanceOperation::SetLine,
                source: ObjectAppearance::default(),
                target,
            },
            FLOW_A,
            appearance_limits,
        )
        .expect("request");
        let domain_plan = ObjectAppearanceBuilder::plan(&request, FLOW_A, appearance_limits)
            .expect("domain plan");
        let domain_plan_sha256 = hex(Sha256::digest(
            domain_plan.canonical_json(appearance_limits).expect("json"),
        )
        .into());
        let mut plan = ObjectAppearanceHwpxPlan {
            schema_version: OBJECT_APPEARANCE_SCHEMA_VERSION,
            profile_id: OBJECT_APPEARANCE_HWPX_PROFILE_ID,
            object_ordinal: 0,
            source_section_sha256: [3; 32],
            source_object_sha256: [4; 32],
            domain_plan,
            domain_plan_sha256,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_digest(&plan, hwpx_limits).expect("digest");
        assert!(validate_plan(&plan, appearance_limits, hwpx_limits).is_ok());
        plan.object_ordinal = 1;
        assert!(matches!(
            validate_plan(&plan, appearance_limits, hwpx_limits),
            Err(ObjectAppearanceHwpxError::PlanTampered)
        ));
    }
}
