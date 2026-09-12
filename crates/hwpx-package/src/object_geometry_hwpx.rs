use std::fmt;

use domain_ir::{
    LogicalId, OBJECT_GEOMETRY_SCHEMA_VERSION, ObjectAffineMatrix, ObjectAnchor,
    ObjectComponentGeometry, ObjectExtent, ObjectFlip, ObjectGeometryBuilder, ObjectGeometryError,
    ObjectGeometryLimits, ObjectGeometryPlan, ObjectGeometryState, ObjectGeometryStateDraft,
    ObjectHeightReference, ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectKind,
    ObjectNumberingType, ObjectOuterMargins, ObjectPoint, ObjectPosition, ObjectRotation,
    ObjectSize, ObjectTextFlow, ObjectTextWrap, ObjectTransform, ObjectVerticalAlignment,
    ObjectVerticalReference, ObjectWidthReference, ObjectWrap,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};

pub const OBJECT_GEOMETRY_HWPX_PROFILE_ID: &str =
    "hwpx-agent.object-geometry-hwpx.hwpml-2011-common-component/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";
const FIXED_SCALE: i64 = 1_000_000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectGeometryHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub output_bytes: usize,
    pub matrix_text_bytes: usize,
}

impl Default for ObjectGeometryHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 65_536,
            output_bytes: 32 * 1024 * 1024,
            matrix_text_bytes: 64,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ObjectGeometryHwpxLimits(ObjectGeometryHwpxLimitConfig);

impl ObjectGeometryHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_OBJECTS: usize = 262_144;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_MATRIX_TEXT_BYTES: usize = 256;

    /// Creates finite exact-source HWPX geometry limits.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling, or section/output-inconsistent limits.
    pub fn new(config: ObjectGeometryHwpxLimitConfig) -> Result<Self, ObjectGeometryHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
            || config.matrix_text_bytes == 0
            || config.matrix_text_bytes > Self::HARD_MAX_MATRIX_TEXT_BYTES
        {
            return Err(ObjectGeometryHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectGeometryHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectGeometryHwpxReadback {
    pub state: ObjectGeometryState,
    pub section_sha256: [u8; 32],
    pub object_sha256: [u8; 32],
    pub object_ordinal: usize,
}

impl fmt::Debug for ObjectGeometryHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryHwpxReadback")
            .field("object_kind", &self.state.object_kind())
            .field("object_ordinal", &self.object_ordinal)
            .field("identity", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct ObjectGeometryHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    object_ordinal: usize,
    source_section_sha256: [u8; 32],
    source_object_sha256: [u8; 32],
    source_document_flow_sha256: String,
    domain_plan: ObjectGeometryPlan,
    plan_sha256: String,
}

impl ObjectGeometryHwpxPlan {
    #[must_use]
    pub const fn object_ordinal(&self) -> usize {
        self.object_ordinal
    }

    #[must_use]
    pub fn domain_plan(&self) -> &ObjectGeometryPlan {
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
        limits: ObjectGeometryHwpxLimits,
    ) -> Result<Vec<u8>, ObjectGeometryHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectGeometryHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("object_ordinal", &self.object_ordinal)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectGeometryHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_object_sha256: [u8; 32],
    pub output_object_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub source_bytes: usize,
    pub output_bytes: usize,
    pub modified_attribute_count: usize,
}

impl fmt::Debug for ObjectGeometryHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("modified_attribute_count", &self.modified_attribute_count)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectGeometryHwpxError {
    #[error("object geometry HWPX limits are invalid")]
    InvalidLimit,
    #[error("object geometry HWPX section exceeds a finite limit")]
    InputLimit,
    #[error("object geometry HWPX common component is absent, duplicated, or unsupported")]
    UnsupportedShape,
    #[error("object geometry HWPX attribute is absent or duplicated")]
    InvalidAttribute,
    #[error("object geometry HWPX boolean is not canonical 0 or 1")]
    InvalidBoolean,
    #[error("object geometry HWPX number is noncanonical or out of range")]
    InvalidNumber,
    #[error("object geometry HWPX enum is outside the reviewed public model")]
    InvalidEnum,
    #[error("object geometry HWPX fixed-point matrix is not exactly representable")]
    InvalidMatrix,
    #[error("object geometry HWPX section or object source drifted")]
    SourceDrift,
    #[error("object geometry HWPX plan was tampered with")]
    PlanTampered,
    #[error("object geometry HWPX lowered semantic readback differs")]
    ReadbackMismatch,
    #[error("object geometry HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("object geometry HWPX allocation failed")]
    AllocationFailed,
    #[error("object geometry domain validation failed")]
    Domain(#[from] ObjectGeometryError),
    #[error("object geometry preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl ObjectGeometryHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_geometry_hwpx_invalid_limit",
            Self::InputLimit => "object_geometry_hwpx_input_limit",
            Self::UnsupportedShape => "object_geometry_hwpx_unsupported_shape",
            Self::InvalidAttribute => "object_geometry_hwpx_invalid_attribute",
            Self::InvalidBoolean => "object_geometry_hwpx_invalid_boolean",
            Self::InvalidNumber => "object_geometry_hwpx_invalid_number",
            Self::InvalidEnum => "object_geometry_hwpx_invalid_enum",
            Self::InvalidMatrix => "object_geometry_hwpx_invalid_matrix",
            Self::SourceDrift => "object_geometry_hwpx_source_drift",
            Self::PlanTampered => "object_geometry_hwpx_plan_tampered",
            Self::ReadbackMismatch => "object_geometry_hwpx_readback_mismatch",
            Self::OutputLimit => "object_geometry_hwpx_output_limit",
            Self::AllocationFailed => "object_geometry_hwpx_allocation_failed",
            Self::Domain(_) => "object_geometry_hwpx_domain",
            Self::Preserving(_) => "object_geometry_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct ObjectGeometryHwpxReader;

impl ObjectGeometryHwpxReader {
    /// Reads one run-level public-model common shape component by document order.
    ///
    /// # Errors
    ///
    /// Rejects malformed, nested-only, incomplete, duplicated or over-limit XML.
    pub fn read_in_section(
        source: &[u8],
        object_ordinal: usize,
        object_id: LogicalId,
        state_limits: ObjectGeometryLimits,
        hwpx_limits: ObjectGeometryHwpxLimits,
    ) -> Result<ObjectGeometryHwpxReadback, ObjectGeometryHwpxError> {
        let parsed = parse_selected(source, object_ordinal, hwpx_limits)?;
        let state = read_state(&parsed, object_id, state_limits, hwpx_limits)?;
        Ok(ObjectGeometryHwpxReadback {
            state,
            section_sha256: Sha256::digest(source).into(),
            object_sha256: parsed.object_sha256,
            object_ordinal,
        })
    }
}

#[derive(Debug)]
pub struct ObjectGeometryHwpxBuilder;

impl ObjectGeometryHwpxBuilder {
    /// Binds a validated domain plan to an exact section and exact object at request time.
    ///
    /// # Errors
    ///
    /// Rejects source state/flow drift, unsupported XML, finite-limit failure or plan mismatch.
    pub fn plan(
        source: &[u8],
        object_ordinal: usize,
        domain_plan: &ObjectGeometryPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectGeometryLimits,
        hwpx_limits: ObjectGeometryHwpxLimits,
    ) -> Result<ObjectGeometryHwpxPlan, ObjectGeometryHwpxError> {
        let readback = ObjectGeometryHwpxReader::read_in_section(
            source,
            object_ordinal,
            domain_plan.target_state().object_id().clone(),
            state_limits,
            hwpx_limits,
        )?;
        let _ = ObjectGeometryBuilder::build(
            domain_plan,
            &readback.state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let mut plan = ObjectGeometryHwpxPlan {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION,
            profile_id: OBJECT_GEOMETRY_HWPX_PROFILE_ID,
            object_ordinal,
            source_section_sha256: readback.section_sha256,
            source_object_sha256: readback.object_sha256,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            domain_plan: domain_plan.clone(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = hex(Sha256::digest(serialize_bounded(&plan, hwpx_limits)?).into());
        let _ = serialize_bounded(&plan, hwpx_limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct ObjectGeometryHwpxLowerer;

impl ObjectGeometryHwpxLowerer {
    /// Revalidates and lowers one immutable geometry plan into preserving section bytes.
    ///
    /// # Errors
    ///
    /// Rejects any plan, section, object, state or flow drift; no partial bytes are returned.
    pub fn lower_in_section(
        source: &[u8],
        plan: &ObjectGeometryHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectGeometryLimits,
        hwpx_limits: ObjectGeometryHwpxLimits,
    ) -> Result<Vec<u8>, ObjectGeometryHwpxError> {
        Self::lower_in_section_with_receipt(
            source,
            plan,
            current_document_flow_sha256,
            state_limits,
            hwpx_limits,
        )
        .map(|(bytes, _)| bytes)
    }

    /// Returns preserving output plus source/object/state integrity evidence.
    ///
    /// # Errors
    ///
    /// Applies the same fail-closed checks as [`Self::lower_in_section`].
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        plan: &ObjectGeometryHwpxPlan,
        current_document_flow_sha256: &str,
        state_limits: ObjectGeometryLimits,
        hwpx_limits: ObjectGeometryHwpxLimits,
    ) -> Result<(Vec<u8>, ObjectGeometryHwpxLoweringReceipt), ObjectGeometryHwpxError> {
        validate_plan(plan, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
        {
            return Err(ObjectGeometryHwpxError::SourceDrift);
        }
        let parsed = parse_selected(source, plan.object_ordinal, hwpx_limits)?;
        if parsed.object_sha256 != plan.source_object_sha256 {
            return Err(ObjectGeometryHwpxError::SourceDrift);
        }
        let source_state = read_state(
            &parsed,
            plan.domain_plan.target_state().object_id().clone(),
            state_limits,
            hwpx_limits,
        )?;
        let result = ObjectGeometryBuilder::build(
            &plan.domain_plan,
            &source_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let target_state = result.state;
        let source_state_sha256 = source_state.canonical_sha256(state_limits)?;
        let target_state_sha256 = target_state.canonical_sha256(state_limits)?;
        let mut edits = geometry_edits(&parsed, &source_state, &target_state, hwpx_limits)?;
        let modified_attribute_count = edits.len();
        let output = apply_edits(source, &mut edits, hwpx_limits)?;
        let output_readback = ObjectGeometryHwpxReader::read_in_section(
            &output,
            plan.object_ordinal,
            target_state.object_id().clone(),
            state_limits,
            hwpx_limits,
        )?;
        if output_readback.state != target_state {
            return Err(ObjectGeometryHwpxError::ReadbackMismatch);
        }
        let receipt = ObjectGeometryHwpxLoweringReceipt {
            profile_id: OBJECT_GEOMETRY_HWPX_PROFILE_ID,
            capability_id: plan.domain_plan.capability_id(),
            source_section_sha256: plan.source_section_sha256,
            output_section_sha256: output_readback.section_sha256,
            source_object_sha256: plan.source_object_sha256,
            output_object_sha256: output_readback.object_sha256,
            source_state_sha256,
            target_state_sha256,
            plan_sha256: plan.plan_sha256.clone(),
            source_bytes: source.len(),
            output_bytes: output.len(),
            modified_attribute_count,
        };
        Ok((output, receipt))
    }
}

fn validate_plan(
    plan: &ObjectGeometryHwpxPlan,
    limits: ObjectGeometryHwpxLimits,
) -> Result<(), ObjectGeometryHwpxError> {
    if plan.schema_version != OBJECT_GEOMETRY_SCHEMA_VERSION
        || plan.profile_id != OBJECT_GEOMETRY_HWPX_PROFILE_ID
    {
        return Err(ObjectGeometryHwpxError::PlanTampered);
    }
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    let expected = hex(Sha256::digest(serialize_bounded(&unsigned, limits)?).into());
    if expected != plan.plan_sha256 {
        return Err(ObjectGeometryHwpxError::PlanTampered);
    }
    Ok(())
}

struct ParsedObject {
    document: PreservingXmlDocument,
    root: usize,
    size: usize,
    position: usize,
    outer_margin: usize,
    offset: usize,
    original_size: usize,
    current_size: usize,
    flip: usize,
    rotation: usize,
    translation_matrix: usize,
    scale_matrix: usize,
    rotation_matrix: usize,
    object_kind: ObjectKind,
    object_sha256: [u8; 32],
}

fn parse_selected(
    source: &[u8],
    object_ordinal: usize,
    limits: ObjectGeometryHwpxLimits,
) -> Result<ParsedObject, ObjectGeometryHwpxError> {
    if source.is_empty() || source.len() > limits.0.section_bytes {
        return Err(ObjectGeometryHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements || object_ordinal >= limits.0.objects {
        return Err(ObjectGeometryHwpxError::InputLimit);
    }
    let (root, object_kind) = selected_run_object(&document, object_ordinal, limits)?;
    let size = unique_child(&document, root, "sz")?;
    let position = unique_child(&document, root, "pos")?;
    let outer_margin = unique_child(&document, root, "outMargin")?;
    let offset = unique_child(&document, root, "offset")?;
    let original_size = unique_child(&document, root, "orgSz")?;
    let current_size = unique_child(&document, root, "curSz")?;
    let flip = unique_child(&document, root, "flip")?;
    let rotation = unique_child(&document, root, "rotationInfo")?;
    let rendering = unique_child(&document, root, "renderingInfo")?;
    let translation_matrix = unique_child(&document, rendering, "transMatrix")?;
    let scale_matrix = unique_child(&document, rendering, "scaMatrix")?;
    let rotation_matrix = unique_child(&document, rendering, "rotMatrix")?;
    let outer = element(&document, root)?
        .outer_span()
        .ok_or(ObjectGeometryHwpxError::UnsupportedShape)?;
    let object_sha256 = Sha256::digest(document.source_text(outer)?.as_bytes()).into();
    Ok(ParsedObject {
        document,
        root,
        size,
        position,
        outer_margin,
        offset,
        original_size,
        current_size,
        flip,
        rotation,
        translation_matrix,
        scale_matrix,
        rotation_matrix,
        object_kind,
        object_sha256,
    })
}

fn selected_run_object(
    document: &PreservingXmlDocument,
    ordinal: usize,
    limits: ObjectGeometryHwpxLimits,
) -> Result<(usize, ObjectKind), ObjectGeometryHwpxError> {
    let mut seen = 0_usize;
    for (index, candidate) in document.elements().iter().enumerate() {
        let Some(kind) = object_kind(candidate) else {
            continue;
        };
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(ObjectGeometryHwpxError::UnsupportedShape)?;
        if !has_name(parent, "run") {
            continue;
        }
        if seen == ordinal {
            return Ok((index, kind));
        }
        seen = seen
            .checked_add(1)
            .ok_or(ObjectGeometryHwpxError::InputLimit)?;
        if seen > limits.0.objects {
            return Err(ObjectGeometryHwpxError::InputLimit);
        }
    }
    Err(ObjectGeometryHwpxError::UnsupportedShape)
}

fn object_kind(element: &XmlElementToken) -> Option<ObjectKind> {
    if element.name().namespace() != Some(PARAGRAPH_NS) {
        return None;
    }
    match element.name().local_name() {
        "pic" => Some(ObjectKind::Picture),
        "rect" => Some(ObjectKind::Rectangle),
        "ellipse" => Some(ObjectKind::Ellipse),
        "line" => Some(ObjectKind::Line),
        "arc" => Some(ObjectKind::Arc),
        "polygon" => Some(ObjectKind::Polygon),
        "curve" => Some(ObjectKind::Curve),
        "connectLine" => Some(ObjectKind::ConnectLine),
        "container" => Some(ObjectKind::Container),
        "ole" => Some(ObjectKind::Ole),
        "video" => Some(ObjectKind::Video),
        "textart" => Some(ObjectKind::TextArt),
        _ => None,
    }
}

#[allow(clippy::too_many_lines)] // Keeps the reviewed native field mapping in one auditable block.
fn read_state(
    parsed: &ParsedObject,
    object_id: LogicalId,
    state_limits: ObjectGeometryLimits,
    hwpx_limits: ObjectGeometryHwpxLimits,
) -> Result<ObjectGeometryState, ObjectGeometryHwpxError> {
    let root = element(&parsed.document, parsed.root)?;
    let size = element(&parsed.document, parsed.size)?;
    let position = element(&parsed.document, parsed.position)?;
    let outer_margin = element(&parsed.document, parsed.outer_margin)?;
    let offset = element(&parsed.document, parsed.offset)?;
    let original_size = element(&parsed.document, parsed.original_size)?;
    let current_size = element(&parsed.document, parsed.current_size)?;
    let flip = element(&parsed.document, parsed.flip)?;
    let rotation = element(&parsed.document, parsed.rotation)?;
    let draft = ObjectGeometryStateDraft {
        schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION.to_owned(),
        object_id,
        object_kind: parsed.object_kind,
        native_object_id: unsigned(root, "id", u32::MAX)?,
        native_instance_id: unsigned(root, "instid", u32::MAX)?,
        z_order: signed_i32(root, "zOrder")?,
        numbering_type: parse_numbering_type(attribute(root, "numberingType")?)?,
        locked: bool01(root, "lock")?,
        size: ObjectSize {
            width_hwpunit: unsigned(size, "width", state_limits.config().extent_hwpunit)?,
            width_reference: parse_width_reference(attribute(size, "widthRelTo")?)?,
            height_hwpunit: unsigned(size, "height", state_limits.config().extent_hwpunit)?,
            height_reference: parse_height_reference(attribute(size, "heightRelTo")?)?,
            protect: bool01(size, "protect")?,
        },
        anchor: ObjectAnchor {
            treat_as_character: bool01(position, "treatAsChar")?,
            affect_line_spacing: bool01(position, "affectLSpacing")?,
            flow_with_text: bool01(position, "flowWithText")?,
            allow_overlap: bool01(position, "allowOverlap")?,
            hold_anchor_and_shape: bool01(position, "holdAnchorAndSO")?,
            horizontal_reference: parse_horizontal_reference(attribute(position, "horzRelTo")?)?,
            vertical_reference: parse_vertical_reference(attribute(position, "vertRelTo")?)?,
        },
        position: ObjectPosition {
            horizontal_alignment: parse_horizontal_alignment(attribute(position, "horzAlign")?)?,
            vertical_alignment: parse_vertical_alignment(attribute(position, "vertAlign")?)?,
            horizontal_offset_hwpunit: unsigned(
                position,
                "horzOffset",
                state_limits.config().extent_hwpunit,
            )?,
            vertical_offset_hwpunit: unsigned(
                position,
                "vertOffset",
                state_limits.config().extent_hwpunit,
            )?,
        },
        wrap: ObjectWrap {
            text_wrap: parse_text_wrap(attribute(root, "textWrap")?)?,
            text_flow: parse_text_flow(attribute(root, "textFlow")?)?,
        },
        outer_margins: ObjectOuterMargins {
            left_hwpunit: unsigned(outer_margin, "left", state_limits.config().extent_hwpunit)?,
            right_hwpunit: unsigned(outer_margin, "right", state_limits.config().extent_hwpunit)?,
            top_hwpunit: unsigned(outer_margin, "top", state_limits.config().extent_hwpunit)?,
            bottom_hwpunit: unsigned(outer_margin, "bottom", state_limits.config().extent_hwpunit)?,
        },
        component: ObjectComponentGeometry {
            offset: ObjectPoint {
                x_hwpunit: unsigned(offset, "x", state_limits.config().extent_hwpunit)?,
                y_hwpunit: unsigned(offset, "y", state_limits.config().extent_hwpunit)?,
            },
            original_size: extent(original_size, state_limits)?,
            current_size: extent(current_size, state_limits)?,
            flip: ObjectFlip {
                horizontal: bool01(flip, "horizontal")?,
                vertical: bool01(flip, "vertical")?,
            },
            rotation: ObjectRotation {
                angle_degrees: signed_i32(rotation, "angle")?,
                center_x_hwpunit: unsigned(
                    rotation,
                    "centerX",
                    state_limits.config().extent_hwpunit,
                )?,
                center_y_hwpunit: unsigned(
                    rotation,
                    "centerY",
                    state_limits.config().extent_hwpunit,
                )?,
                rotate_image: bool01(rotation, "rotateimage")?,
            },
            transform: ObjectTransform {
                translation: matrix(
                    element(&parsed.document, parsed.translation_matrix)?,
                    state_limits,
                    hwpx_limits,
                )?,
                scale: matrix(
                    element(&parsed.document, parsed.scale_matrix)?,
                    state_limits,
                    hwpx_limits,
                )?,
                rotation: matrix(
                    element(&parsed.document, parsed.rotation_matrix)?,
                    state_limits,
                    hwpx_limits,
                )?,
            },
        },
    };
    Ok(ObjectGeometryState::from_draft(draft, state_limits)?)
}

fn extent(
    element: &XmlElementToken,
    limits: ObjectGeometryLimits,
) -> Result<ObjectExtent, ObjectGeometryHwpxError> {
    Ok(ObjectExtent {
        width_hwpunit: unsigned(element, "width", limits.config().extent_hwpunit)?,
        height_hwpunit: unsigned(element, "height", limits.config().extent_hwpunit)?,
    })
}

fn matrix(
    element: &XmlElementToken,
    state_limits: ObjectGeometryLimits,
    hwpx_limits: ObjectGeometryHwpxLimits,
) -> Result<ObjectAffineMatrix, ObjectGeometryHwpxError> {
    let coefficient = |name| {
        fixed_millionths(
            attribute(element, name)?,
            state_limits.config().matrix_coefficient_millionths,
            hwpx_limits.0.matrix_text_bytes,
        )
    };
    Ok(ObjectAffineMatrix {
        e1_millionths: coefficient("e1")?,
        e2_millionths: coefficient("e2")?,
        e3_millionths: coefficient("e3")?,
        e4_millionths: coefficient("e4")?,
        e5_millionths: coefficient("e5")?,
        e6_millionths: coefficient("e6")?,
    })
}

fn geometry_edits(
    parsed: &ParsedObject,
    source: &ObjectGeometryState,
    target: &ObjectGeometryState,
    hwpx_limits: ObjectGeometryHwpxLimits,
) -> Result<Vec<ByteEdit>, ObjectGeometryHwpxError> {
    if source.object_id() != target.object_id()
        || source.object_kind() != target.object_kind()
        || source.native_object_id() != target.native_object_id()
        || source.native_instance_id() != target.native_instance_id()
        || source.z_order() != target.z_order()
        || source.numbering_type() != target.numbering_type()
    {
        return Err(ObjectGeometryHwpxError::SourceDrift);
    }
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(64)
        .map_err(|_| ObjectGeometryHwpxError::AllocationFailed)?;
    push_bool_change(
        &parsed.document,
        parsed.root,
        "lock",
        source.locked(),
        target.locked(),
        &mut edits,
    )?;
    size_edits(parsed, source.size(), target.size(), &mut edits)?;
    anchor_edits(parsed, source.anchor(), target.anchor(), &mut edits)?;
    position_edits(parsed, source.position(), target.position(), &mut edits)?;
    wrap_edits(
        parsed,
        source.wrap(),
        target.wrap(),
        source.outer_margins(),
        target.outer_margins(),
        &mut edits,
    )?;
    component_edits(
        parsed,
        source.component(),
        target.component(),
        hwpx_limits,
        &mut edits,
    )?;
    Ok(edits)
}

fn size_edits(
    parsed: &ParsedObject,
    source: ObjectSize,
    target: ObjectSize,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectGeometryHwpxError> {
    push_change(
        &parsed.document,
        parsed.size,
        "width",
        source.width_hwpunit,
        target.width_hwpunit,
        target.width_hwpunit.to_string(),
        edits,
    )?;
    push_change(
        &parsed.document,
        parsed.size,
        "widthRelTo",
        source.width_reference,
        target.width_reference,
        width_reference(target.width_reference).to_owned(),
        edits,
    )?;
    push_change(
        &parsed.document,
        parsed.size,
        "height",
        source.height_hwpunit,
        target.height_hwpunit,
        target.height_hwpunit.to_string(),
        edits,
    )?;
    push_change(
        &parsed.document,
        parsed.size,
        "heightRelTo",
        source.height_reference,
        target.height_reference,
        height_reference(target.height_reference).to_owned(),
        edits,
    )?;
    push_bool_change(
        &parsed.document,
        parsed.size,
        "protect",
        source.protect,
        target.protect,
        edits,
    )
}

fn anchor_edits(
    parsed: &ParsedObject,
    source: ObjectAnchor,
    target: ObjectAnchor,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectGeometryHwpxError> {
    for (name, old, new) in [
        (
            "treatAsChar",
            source.treat_as_character,
            target.treat_as_character,
        ),
        (
            "affectLSpacing",
            source.affect_line_spacing,
            target.affect_line_spacing,
        ),
        ("flowWithText", source.flow_with_text, target.flow_with_text),
        ("allowOverlap", source.allow_overlap, target.allow_overlap),
        (
            "holdAnchorAndSO",
            source.hold_anchor_and_shape,
            target.hold_anchor_and_shape,
        ),
    ] {
        push_bool_change(&parsed.document, parsed.position, name, old, new, edits)?;
    }
    push_change(
        &parsed.document,
        parsed.position,
        "horzRelTo",
        source.horizontal_reference,
        target.horizontal_reference,
        horizontal_reference(target.horizontal_reference).to_owned(),
        edits,
    )?;
    push_change(
        &parsed.document,
        parsed.position,
        "vertRelTo",
        source.vertical_reference,
        target.vertical_reference,
        vertical_reference(target.vertical_reference).to_owned(),
        edits,
    )
}

fn position_edits(
    parsed: &ParsedObject,
    source: ObjectPosition,
    target: ObjectPosition,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectGeometryHwpxError> {
    push_change(
        &parsed.document,
        parsed.position,
        "horzAlign",
        source.horizontal_alignment,
        target.horizontal_alignment,
        horizontal_alignment(target.horizontal_alignment).to_owned(),
        edits,
    )?;
    push_change(
        &parsed.document,
        parsed.position,
        "vertAlign",
        source.vertical_alignment,
        target.vertical_alignment,
        vertical_alignment(target.vertical_alignment).to_owned(),
        edits,
    )?;
    push_change(
        &parsed.document,
        parsed.position,
        "horzOffset",
        source.horizontal_offset_hwpunit,
        target.horizontal_offset_hwpunit,
        target.horizontal_offset_hwpunit.to_string(),
        edits,
    )?;
    push_change(
        &parsed.document,
        parsed.position,
        "vertOffset",
        source.vertical_offset_hwpunit,
        target.vertical_offset_hwpunit,
        target.vertical_offset_hwpunit.to_string(),
        edits,
    )
}

fn wrap_edits(
    parsed: &ParsedObject,
    source: ObjectWrap,
    target: ObjectWrap,
    source_margins: ObjectOuterMargins,
    target_margins: ObjectOuterMargins,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectGeometryHwpxError> {
    push_change(
        &parsed.document,
        parsed.root,
        "textWrap",
        source.text_wrap,
        target.text_wrap,
        text_wrap(target.text_wrap).to_owned(),
        edits,
    )?;
    push_change(
        &parsed.document,
        parsed.root,
        "textFlow",
        source.text_flow,
        target.text_flow,
        text_flow(target.text_flow).to_owned(),
        edits,
    )?;
    for (name, old, new) in [
        (
            "left",
            source_margins.left_hwpunit,
            target_margins.left_hwpunit,
        ),
        (
            "right",
            source_margins.right_hwpunit,
            target_margins.right_hwpunit,
        ),
        (
            "top",
            source_margins.top_hwpunit,
            target_margins.top_hwpunit,
        ),
        (
            "bottom",
            source_margins.bottom_hwpunit,
            target_margins.bottom_hwpunit,
        ),
    ] {
        push_change(
            &parsed.document,
            parsed.outer_margin,
            name,
            old,
            new,
            new.to_string(),
            edits,
        )?;
    }
    Ok(())
}

#[allow(clippy::too_many_lines)] // Keeps the exact common-component preservation map together.
fn component_edits(
    parsed: &ParsedObject,
    source: ObjectComponentGeometry,
    target: ObjectComponentGeometry,
    hwpx_limits: ObjectGeometryHwpxLimits,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectGeometryHwpxError> {
    for (element_index, name, old, new) in [
        (
            parsed.offset,
            "x",
            source.offset.x_hwpunit,
            target.offset.x_hwpunit,
        ),
        (
            parsed.offset,
            "y",
            source.offset.y_hwpunit,
            target.offset.y_hwpunit,
        ),
        (
            parsed.original_size,
            "width",
            source.original_size.width_hwpunit,
            target.original_size.width_hwpunit,
        ),
        (
            parsed.original_size,
            "height",
            source.original_size.height_hwpunit,
            target.original_size.height_hwpunit,
        ),
        (
            parsed.current_size,
            "width",
            source.current_size.width_hwpunit,
            target.current_size.width_hwpunit,
        ),
        (
            parsed.current_size,
            "height",
            source.current_size.height_hwpunit,
            target.current_size.height_hwpunit,
        ),
    ] {
        push_change(
            &parsed.document,
            element_index,
            name,
            old,
            new,
            new.to_string(),
            edits,
        )?;
    }
    for (name, old, new) in [
        ("horizontal", source.flip.horizontal, target.flip.horizontal),
        ("vertical", source.flip.vertical, target.flip.vertical),
    ] {
        push_bool_change(&parsed.document, parsed.flip, name, old, new, edits)?;
    }
    push_change(
        &parsed.document,
        parsed.rotation,
        "angle",
        source.rotation.angle_degrees,
        target.rotation.angle_degrees,
        target.rotation.angle_degrees.to_string(),
        edits,
    )?;
    for (name, old, new) in [
        (
            "centerX",
            source.rotation.center_x_hwpunit,
            target.rotation.center_x_hwpunit,
        ),
        (
            "centerY",
            source.rotation.center_y_hwpunit,
            target.rotation.center_y_hwpunit,
        ),
    ] {
        push_change(
            &parsed.document,
            parsed.rotation,
            name,
            old,
            new,
            new.to_string(),
            edits,
        )?;
    }
    push_bool_change(
        &parsed.document,
        parsed.rotation,
        "rotateimage",
        source.rotation.rotate_image,
        target.rotation.rotate_image,
        edits,
    )?;
    matrix_edits(
        &parsed.document,
        parsed.translation_matrix,
        source.transform.translation,
        target.transform.translation,
        hwpx_limits,
        edits,
    )?;
    matrix_edits(
        &parsed.document,
        parsed.scale_matrix,
        source.transform.scale,
        target.transform.scale,
        hwpx_limits,
        edits,
    )?;
    matrix_edits(
        &parsed.document,
        parsed.rotation_matrix,
        source.transform.rotation,
        target.transform.rotation,
        hwpx_limits,
        edits,
    )
}

fn matrix_edits(
    document: &PreservingXmlDocument,
    element_index: usize,
    source: ObjectAffineMatrix,
    target: ObjectAffineMatrix,
    limits: ObjectGeometryHwpxLimits,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectGeometryHwpxError> {
    for (name, old, new) in [
        ("e1", source.e1_millionths, target.e1_millionths),
        ("e2", source.e2_millionths, target.e2_millionths),
        ("e3", source.e3_millionths, target.e3_millionths),
        ("e4", source.e4_millionths, target.e4_millionths),
        ("e5", source.e5_millionths, target.e5_millionths),
        ("e6", source.e6_millionths, target.e6_millionths),
    ] {
        let replacement = fixed_text(new)?;
        if replacement.len() > limits.0.matrix_text_bytes {
            return Err(ObjectGeometryHwpxError::OutputLimit);
        }
        push_change(document, element_index, name, old, new, replacement, edits)?;
    }
    Ok(())
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

#[allow(clippy::needless_pass_by_value)] // Callers pass small Copy native values of many types.
fn push_change<T: Eq>(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    source: T,
    target: T,
    replacement: String,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectGeometryHwpxError> {
    if source == target {
        return Ok(());
    }
    let attribute = unique_attribute(element(document, element_index)?, name)?;
    edits
        .try_reserve(1)
        .map_err(|_| ObjectGeometryHwpxError::AllocationFailed)?;
    edits.push(ByteEdit {
        span: attribute.value_span(),
        replacement: replacement.into_bytes(),
    });
    Ok(())
}

fn push_bool_change(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    source: bool,
    target: bool,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), ObjectGeometryHwpxError> {
    push_change(
        document,
        element_index,
        name,
        source,
        target,
        bool_text(target).to_owned(),
        edits,
    )
}

fn apply_edits(
    source: &[u8],
    edits: &mut [ByteEdit],
    limits: ObjectGeometryHwpxLimits,
) -> Result<Vec<u8>, ObjectGeometryHwpxError> {
    edits.sort_unstable_by_key(|edit| edit.span.start());
    let mut previous_end = 0;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.span.start() < previous_end || edit.span.end() > source.len() {
            return Err(ObjectGeometryHwpxError::UnsupportedShape);
        }
        previous_end = edit.span.end();
        output_len = output_len
            .checked_sub(edit.span.len())
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(ObjectGeometryHwpxError::OutputLimit)?;
    }
    if output_len > limits.0.output_bytes {
        return Err(ObjectGeometryHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| ObjectGeometryHwpxError::AllocationFailed)?;
    let mut cursor = 0;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.span.start()]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.span.end();
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(ObjectGeometryHwpxError::OutputLimit);
    }
    Ok(output)
}

fn unique_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, ObjectGeometryHwpxError> {
    let mut found = None;
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let value = element(document, index)?;
        if has_child_name(value, local_name) && found.replace(index).is_some() {
            return Err(ObjectGeometryHwpxError::UnsupportedShape);
        }
        child = value.next_sibling();
    }
    found.ok_or(ObjectGeometryHwpxError::UnsupportedShape)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ObjectGeometryHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ObjectGeometryHwpxError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn has_child_name(element: &XmlElementToken, local_name: &str) -> bool {
    let expected_namespace = match local_name {
        "transMatrix" | "scaMatrix" | "rotMatrix" => CORE_NS,
        _ => PARAGRAPH_NS,
    };
    element.name().namespace() == Some(expected_namespace)
        && element.name().local_name() == local_name
}

fn unique_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, ObjectGeometryHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(ObjectGeometryHwpxError::InvalidAttribute)?;
    if matches.next().is_some() {
        return Err(ObjectGeometryHwpxError::InvalidAttribute);
    }
    Ok(value)
}

fn attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, ObjectGeometryHwpxError> {
    Ok(unique_attribute(element, name)?.semantic_value())
}

fn bool01(element: &XmlElementToken, name: &str) -> Result<bool, ObjectGeometryHwpxError> {
    match attribute(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(ObjectGeometryHwpxError::InvalidBoolean),
    }
}

fn unsigned(
    element: &XmlElementToken,
    name: &str,
    maximum: u32,
) -> Result<u32, ObjectGeometryHwpxError> {
    let value = attribute(element, name)?;
    if !canonical_unsigned(value) {
        return Err(ObjectGeometryHwpxError::InvalidNumber);
    }
    let parsed = value
        .parse::<u32>()
        .map_err(|_| ObjectGeometryHwpxError::InvalidNumber)?;
    if parsed > maximum {
        return Err(ObjectGeometryHwpxError::InvalidNumber);
    }
    Ok(parsed)
}

fn signed_i32(element: &XmlElementToken, name: &str) -> Result<i32, ObjectGeometryHwpxError> {
    let value = attribute(element, name)?;
    if !canonical_signed(value) {
        return Err(ObjectGeometryHwpxError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| ObjectGeometryHwpxError::InvalidNumber)
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

fn fixed_millionths(
    value: &str,
    maximum: i64,
    text_limit: usize,
) -> Result<i64, ObjectGeometryHwpxError> {
    if value.is_empty() || value.len() > text_limit || value.starts_with('+') {
        return Err(ObjectGeometryHwpxError::InvalidMatrix);
    }
    let (negative, unsigned) = value
        .strip_prefix('-')
        .map_or((false, value), |rest| (true, rest));
    if unsigned.is_empty() {
        return Err(ObjectGeometryHwpxError::InvalidMatrix);
    }
    let mut parts = unsigned.split('.');
    let integer = parts.next().ok_or(ObjectGeometryHwpxError::InvalidMatrix)?;
    let fractional = parts.next();
    if parts.next().is_some()
        || !canonical_unsigned(integer)
        || fractional.is_some_and(|digits| {
            digits.is_empty()
                || digits.len() > 6
                || !digits.bytes().all(|byte| byte.is_ascii_digit())
        })
    {
        return Err(ObjectGeometryHwpxError::InvalidMatrix);
    }
    let integer_value = integer
        .parse::<i64>()
        .map_err(|_| ObjectGeometryHwpxError::InvalidMatrix)?;
    let fraction_value = match fractional {
        Some(digits) => {
            let parsed = digits
                .parse::<i64>()
                .map_err(|_| ObjectGeometryHwpxError::InvalidMatrix)?;
            let digits_len =
                u32::try_from(digits.len()).map_err(|_| ObjectGeometryHwpxError::InvalidMatrix)?;
            parsed
                .checked_mul(10_i64.pow(6_u32.saturating_sub(digits_len)))
                .ok_or(ObjectGeometryHwpxError::InvalidMatrix)?
        }
        None => 0,
    };
    let magnitude = integer_value
        .checked_mul(FIXED_SCALE)
        .and_then(|whole| whole.checked_add(fraction_value))
        .ok_or(ObjectGeometryHwpxError::InvalidMatrix)?;
    let signed = if negative {
        magnitude
            .checked_neg()
            .ok_or(ObjectGeometryHwpxError::InvalidMatrix)?
    } else {
        magnitude
    };
    if signed
        .checked_abs()
        .is_none_or(|absolute| absolute > maximum)
    {
        return Err(ObjectGeometryHwpxError::InvalidMatrix);
    }
    Ok(signed)
}

fn fixed_text(value: i64) -> Result<String, ObjectGeometryHwpxError> {
    let negative = value.is_negative();
    let magnitude = value
        .checked_abs()
        .ok_or(ObjectGeometryHwpxError::InvalidMatrix)?;
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

fn parse_numbering_type(value: &str) -> Result<ObjectNumberingType, ObjectGeometryHwpxError> {
    match value {
        "NONE" => Ok(ObjectNumberingType::None),
        "PICTURE" => Ok(ObjectNumberingType::Picture),
        "TABLE" => Ok(ObjectNumberingType::Table),
        "EQUATION" => Ok(ObjectNumberingType::Equation),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn parse_text_wrap(value: &str) -> Result<ObjectTextWrap, ObjectGeometryHwpxError> {
    match value {
        "SQUARE" => Ok(ObjectTextWrap::Square),
        "TOP_AND_BOTTOM" => Ok(ObjectTextWrap::TopAndBottom),
        "BEHIND_TEXT" => Ok(ObjectTextWrap::BehindText),
        "IN_FRONT_OF_TEXT" => Ok(ObjectTextWrap::InFrontOfText),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn text_wrap(value: ObjectTextWrap) -> &'static str {
    match value {
        ObjectTextWrap::Square => "SQUARE",
        ObjectTextWrap::TopAndBottom => "TOP_AND_BOTTOM",
        ObjectTextWrap::BehindText => "BEHIND_TEXT",
        ObjectTextWrap::InFrontOfText => "IN_FRONT_OF_TEXT",
    }
}

fn parse_text_flow(value: &str) -> Result<ObjectTextFlow, ObjectGeometryHwpxError> {
    match value {
        "BOTH_SIDES" => Ok(ObjectTextFlow::BothSides),
        "LEFT_ONLY" => Ok(ObjectTextFlow::LeftOnly),
        "RIGHT_ONLY" => Ok(ObjectTextFlow::RightOnly),
        "LARGEST_ONLY" => Ok(ObjectTextFlow::LargestOnly),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn text_flow(value: ObjectTextFlow) -> &'static str {
    match value {
        ObjectTextFlow::BothSides => "BOTH_SIDES",
        ObjectTextFlow::LeftOnly => "LEFT_ONLY",
        ObjectTextFlow::RightOnly => "RIGHT_ONLY",
        ObjectTextFlow::LargestOnly => "LARGEST_ONLY",
    }
}

fn parse_horizontal_reference(
    value: &str,
) -> Result<ObjectHorizontalReference, ObjectGeometryHwpxError> {
    match value {
        "PAPER" => Ok(ObjectHorizontalReference::Paper),
        "PAGE" => Ok(ObjectHorizontalReference::Page),
        "COLUMN" => Ok(ObjectHorizontalReference::Column),
        "PARA" => Ok(ObjectHorizontalReference::Paragraph),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn horizontal_reference(value: ObjectHorizontalReference) -> &'static str {
    match value {
        ObjectHorizontalReference::Paper => "PAPER",
        ObjectHorizontalReference::Page => "PAGE",
        ObjectHorizontalReference::Column => "COLUMN",
        ObjectHorizontalReference::Paragraph => "PARA",
    }
}

fn parse_vertical_reference(
    value: &str,
) -> Result<ObjectVerticalReference, ObjectGeometryHwpxError> {
    match value {
        "PAPER" => Ok(ObjectVerticalReference::Paper),
        "PAGE" => Ok(ObjectVerticalReference::Page),
        "PARA" => Ok(ObjectVerticalReference::Paragraph),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn vertical_reference(value: ObjectVerticalReference) -> &'static str {
    match value {
        ObjectVerticalReference::Paper => "PAPER",
        ObjectVerticalReference::Page => "PAGE",
        ObjectVerticalReference::Paragraph => "PARA",
    }
}

fn parse_horizontal_alignment(
    value: &str,
) -> Result<ObjectHorizontalAlignment, ObjectGeometryHwpxError> {
    match value {
        "LEFT" => Ok(ObjectHorizontalAlignment::Left),
        "CENTER" => Ok(ObjectHorizontalAlignment::Center),
        "RIGHT" => Ok(ObjectHorizontalAlignment::Right),
        "INSIDE" => Ok(ObjectHorizontalAlignment::Inside),
        "OUTSIDE" => Ok(ObjectHorizontalAlignment::Outside),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn horizontal_alignment(value: ObjectHorizontalAlignment) -> &'static str {
    match value {
        ObjectHorizontalAlignment::Left => "LEFT",
        ObjectHorizontalAlignment::Center => "CENTER",
        ObjectHorizontalAlignment::Right => "RIGHT",
        ObjectHorizontalAlignment::Inside => "INSIDE",
        ObjectHorizontalAlignment::Outside => "OUTSIDE",
    }
}

fn parse_vertical_alignment(
    value: &str,
) -> Result<ObjectVerticalAlignment, ObjectGeometryHwpxError> {
    match value {
        "TOP" => Ok(ObjectVerticalAlignment::Top),
        "CENTER" => Ok(ObjectVerticalAlignment::Center),
        "BOTTOM" => Ok(ObjectVerticalAlignment::Bottom),
        "INSIDE" => Ok(ObjectVerticalAlignment::Inside),
        "OUTSIDE" => Ok(ObjectVerticalAlignment::Outside),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn vertical_alignment(value: ObjectVerticalAlignment) -> &'static str {
    match value {
        ObjectVerticalAlignment::Top => "TOP",
        ObjectVerticalAlignment::Center => "CENTER",
        ObjectVerticalAlignment::Bottom => "BOTTOM",
        ObjectVerticalAlignment::Inside => "INSIDE",
        ObjectVerticalAlignment::Outside => "OUTSIDE",
    }
}

fn parse_width_reference(value: &str) -> Result<ObjectWidthReference, ObjectGeometryHwpxError> {
    match value {
        "PAPER" => Ok(ObjectWidthReference::Paper),
        "PAGE" => Ok(ObjectWidthReference::Page),
        "COLUMN" => Ok(ObjectWidthReference::Column),
        "PARA" => Ok(ObjectWidthReference::Paragraph),
        "ABSOLUTE" => Ok(ObjectWidthReference::Absolute),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn width_reference(value: ObjectWidthReference) -> &'static str {
    match value {
        ObjectWidthReference::Paper => "PAPER",
        ObjectWidthReference::Page => "PAGE",
        ObjectWidthReference::Column => "COLUMN",
        ObjectWidthReference::Paragraph => "PARA",
        ObjectWidthReference::Absolute => "ABSOLUTE",
    }
}

fn parse_height_reference(value: &str) -> Result<ObjectHeightReference, ObjectGeometryHwpxError> {
    match value {
        "PAPER" => Ok(ObjectHeightReference::Paper),
        "PAGE" => Ok(ObjectHeightReference::Page),
        "ABSOLUTE" => Ok(ObjectHeightReference::Absolute),
        _ => Err(ObjectGeometryHwpxError::InvalidEnum),
    }
}

fn height_reference(value: ObjectHeightReference) -> &'static str {
    match value {
        ObjectHeightReference::Paper => "PAPER",
        ObjectHeightReference::Page => "PAGE",
        ObjectHeightReference::Absolute => "ABSOLUTE",
    }
}

const fn bool_text(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectGeometryHwpxLimits,
) -> Result<Vec<u8>, ObjectGeometryHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectGeometryHwpxError::OutputLimit)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(ObjectGeometryHwpxError::OutputLimit);
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
