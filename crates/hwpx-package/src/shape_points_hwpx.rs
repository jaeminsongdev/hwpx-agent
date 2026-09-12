use std::fmt;
use std::fmt::Write as _;

use domain_ir::{
    BasicShapeLimits, CurveSegment, CurveSegmentType, FreeformShape, ObjectGeometryLimits,
    ObjectGeometryState, ObjectKind, SHAPE_POINTS_SCHEMA_VERSION, ShapePoint, ShapePointsBuilder,
    ShapePointsError, ShapePointsLimits, ShapePointsPlan, ShapePointsState,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::object_geometry_hwpx::{
    ObjectGeometryHwpxError, ObjectGeometryHwpxLimits, ObjectGeometryHwpxReader,
};
use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken,
};

pub const SHAPE_POINTS_HWPX_PROFILE_ID: &str =
    "hwpx-agent.shape-points-hwpx.hwpml-2011-payload-island/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ShapePointsHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub objects: usize,
    pub payload_bytes: usize,
    pub output_bytes: usize,
    pub plan_bytes: usize,
}

impl Default for ShapePointsHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            objects: 65_536,
            payload_bytes: 4 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
            plan_bytes: 2 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ShapePointsHwpxLimits(ShapePointsHwpxLimitConfig);

impl ShapePointsHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_OBJECTS: usize = 262_144;
    pub const HARD_MAX_PAYLOAD_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_PLAN_BYTES: usize = 8 * 1024 * 1024;

    /// Creates finite exact-section limits without silently clamping values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding limits.
    pub fn new(config: ShapePointsHwpxLimitConfig) -> Result<Self, ShapePointsHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.payload_bytes == 0
            || config.payload_bytes > Self::HARD_MAX_PAYLOAD_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
        {
            return Err(ShapePointsHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ShapePointsHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ShapePointsHwpxReadback {
    pub geometry: ObjectGeometryState,
    pub freeform: FreeformShape,
    pub section_sha256: [u8; 32],
    pub object_sha256: [u8; 32],
    pub payload_sha256: [u8; 32],
    pub object_ordinal: usize,
}

impl fmt::Debug for ShapePointsHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsHwpxReadback")
            .field("object_kind", &self.geometry.object_kind())
            .field("object_ordinal", &self.object_ordinal)
            .field("identity", &"<redacted>")
            .field("payload", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct ShapePointsHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    object_ordinal: usize,
    source_section_sha256: [u8; 32],
    source_object_sha256: [u8; 32],
    source_payload_sha256: [u8; 32],
    source_document_flow_sha256: String,
    domain_plan: ShapePointsPlan,
    domain_plan_sha256: String,
    plan_sha256: String,
}

impl ShapePointsHwpxPlan {
    #[must_use]
    pub const fn object_ordinal(&self) -> usize {
        self.object_ordinal
    }

    #[must_use]
    pub const fn domain_plan(&self) -> &ShapePointsPlan {
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
        limits: ShapePointsHwpxLimits,
    ) -> Result<Vec<u8>, ShapePointsHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ShapePointsHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("object_ordinal", &self.object_ordinal)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ShapePointsHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_object_sha256: [u8; 32],
    pub output_object_sha256: [u8; 32],
    pub source_payload_sha256: [u8; 32],
    pub output_payload_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for ShapePointsHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ShapePointsHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ShapePointsHwpxError {
    #[error("shape-points HWPX limits are invalid")]
    InvalidLimit,
    #[error("shape-points HWPX section exceeds a finite limit")]
    InputLimit,
    #[error("shape-points HWPX target is absent, duplicated, or unsupported")]
    UnsupportedShape,
    #[error("shape-points HWPX payload attributes are malformed")]
    InvalidAttribute,
    #[error("shape-points HWPX payload number is noncanonical or out of range")]
    InvalidNumber,
    #[error("shape-points HWPX payload topology or ordering is unsupported")]
    InvalidPayload,
    #[error("shape-points HWPX section, object, payload, state, or flow drifted")]
    SourceDrift,
    #[error("shape-points HWPX plan was tampered with")]
    PlanTampered,
    #[error("shape-points HWPX semantic readback differs")]
    ReadbackMismatch,
    #[error("shape-points HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("shape-points HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("shape-points HWPX allocation failed")]
    AllocationFailed,
    #[error("shape-points domain validation failed")]
    Domain(#[from] ShapePointsError),
    #[error("shape-points geometry HWPX validation failed")]
    Geometry(#[from] ObjectGeometryHwpxError),
    #[error("shape-points preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl ShapePointsHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "shape_points_hwpx_invalid_limit",
            Self::InputLimit => "shape_points_hwpx_input_limit",
            Self::UnsupportedShape => "shape_points_hwpx_unsupported_shape",
            Self::InvalidAttribute => "shape_points_hwpx_invalid_attribute",
            Self::InvalidNumber => "shape_points_hwpx_invalid_number",
            Self::InvalidPayload => "shape_points_hwpx_invalid_payload",
            Self::SourceDrift => "shape_points_hwpx_source_drift",
            Self::PlanTampered => "shape_points_hwpx_plan_tampered",
            Self::ReadbackMismatch => "shape_points_hwpx_readback_mismatch",
            Self::PreservationMismatch => "shape_points_hwpx_preservation_mismatch",
            Self::OutputLimit => "shape_points_hwpx_output_limit",
            Self::AllocationFailed => "shape_points_hwpx_allocation_failed",
            Self::Domain(_) => "shape_points_hwpx_domain",
            Self::Geometry(_) => "shape_points_hwpx_geometry",
            Self::Preserving(_) => "shape_points_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct ShapePointsHwpxReader;

impl ShapePointsHwpxReader {
    /// Reads one run-level polygon or curve and checks its complete expected state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, nested-only, noncontiguous, incomplete, stale, or over-limit XML.
    pub fn read_in_section(
        source: &[u8],
        object_ordinal: usize,
        expected: &ShapePointsState,
        geometry_limits: ObjectGeometryLimits,
        geometry_hwpx_limits: ObjectGeometryHwpxLimits,
        shape_limits: BasicShapeLimits,
        hwpx_limits: ShapePointsHwpxLimits,
    ) -> Result<ShapePointsHwpxReadback, ShapePointsHwpxError> {
        let parsed = parse_selected(source, object_ordinal, shape_limits, hwpx_limits)?;
        let geometry = ObjectGeometryHwpxReader::read_in_section(
            source,
            object_ordinal,
            expected.geometry().object_id().clone(),
            geometry_limits,
            geometry_hwpx_limits,
        )?
        .state;
        if geometry != *expected.geometry() || parsed.freeform != *expected.freeform() {
            return Err(ShapePointsHwpxError::SourceDrift);
        }
        Ok(ShapePointsHwpxReadback {
            geometry,
            freeform: parsed.freeform,
            section_sha256: Sha256::digest(source).into(),
            object_sha256: parsed.object_sha256,
            payload_sha256: parsed.payload_sha256,
            object_ordinal,
        })
    }
}

#[derive(Debug)]
pub struct ShapePointsHwpxBuilder;

impl ShapePointsHwpxBuilder {
    /// Binds a validated point-edit plan to one exact section/object/payload island.
    ///
    /// # Errors
    ///
    /// Rejects domain, source-state, flow, XML, payload, or finite-limit drift.
    #[allow(clippy::too_many_arguments)]
    pub fn plan(
        source: &[u8],
        object_ordinal: usize,
        domain_plan: &ShapePointsPlan,
        current_document_flow_sha256: &str,
        geometry_limits: ObjectGeometryLimits,
        geometry_hwpx_limits: ObjectGeometryHwpxLimits,
        shape_limits: BasicShapeLimits,
        state_limits: ShapePointsLimits,
        hwpx_limits: ShapePointsHwpxLimits,
    ) -> Result<ShapePointsHwpxPlan, ShapePointsHwpxError> {
        let readback = ShapePointsHwpxReader::read_in_section(
            source,
            object_ordinal,
            domain_plan.source_state(),
            geometry_limits,
            geometry_hwpx_limits,
            shape_limits,
            hwpx_limits,
        )?;
        let _ = ShapePointsBuilder::build(
            domain_plan,
            domain_plan.source_state(),
            current_document_flow_sha256,
            shape_limits,
            state_limits,
        )?;
        let domain_plan_sha256 = domain_plan.plan_sha256().to_owned();
        let mut plan = ShapePointsHwpxPlan {
            schema_version: SHAPE_POINTS_SCHEMA_VERSION,
            profile_id: SHAPE_POINTS_HWPX_PROFILE_ID,
            object_ordinal,
            source_section_sha256: readback.section_sha256,
            source_object_sha256: readback.object_sha256,
            source_payload_sha256: readback.payload_sha256,
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
pub struct ShapePointsHwpxLowerer;

impl ShapePointsHwpxLowerer {
    /// Revalidates and replaces only the selected point/segment payload island.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, object, payload, state, flow, or readback drift.
    #[allow(clippy::too_many_arguments, clippy::too_many_lines)]
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        plan: &ShapePointsHwpxPlan,
        current_document_flow_sha256: &str,
        geometry_limits: ObjectGeometryLimits,
        geometry_hwpx_limits: ObjectGeometryHwpxLimits,
        shape_limits: BasicShapeLimits,
        state_limits: ShapePointsLimits,
        hwpx_limits: ShapePointsHwpxLimits,
    ) -> Result<(Vec<u8>, ShapePointsHwpxLoweringReceipt), ShapePointsHwpxError> {
        validate_plan(plan, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        {
            return Err(ShapePointsHwpxError::SourceDrift);
        }
        let source_readback = ShapePointsHwpxReader::read_in_section(
            source,
            plan.object_ordinal,
            plan.domain_plan.source_state(),
            geometry_limits,
            geometry_hwpx_limits,
            shape_limits,
            hwpx_limits,
        )?;
        if source_readback.object_sha256 != plan.source_object_sha256
            || source_readback.payload_sha256 != plan.source_payload_sha256
        {
            return Err(ShapePointsHwpxError::SourceDrift);
        }
        let result = ShapePointsBuilder::build(
            &plan.domain_plan,
            plan.domain_plan.source_state(),
            current_document_flow_sha256,
            shape_limits,
            state_limits,
        )?;
        let target_state = result.state;
        let parsed = parse_selected(source, plan.object_ordinal, shape_limits, hwpx_limits)?;
        let replacement = payload_fragment(
            target_state.freeform(),
            &parsed.payload_qualified_name,
            hwpx_limits,
        )?;
        let output = replace_span(source, parsed.payload_span, &replacement, hwpx_limits)?;
        let output_readback = ShapePointsHwpxReader::read_in_section(
            &output,
            plan.object_ordinal,
            &target_state,
            geometry_limits,
            geometry_hwpx_limits,
            shape_limits,
            hwpx_limits,
        )?;
        let output_parsed =
            parse_selected(&output, plan.object_ordinal, shape_limits, hwpx_limits)?;
        if source[..parsed.payload_span.start()] != output[..output_parsed.payload_span.start()]
            || source[parsed.payload_span.end()..] != output[output_parsed.payload_span.end()..]
        {
            return Err(ShapePointsHwpxError::PreservationMismatch);
        }
        let receipt = ShapePointsHwpxLoweringReceipt {
            profile_id: SHAPE_POINTS_HWPX_PROFILE_ID,
            capability_id: "obj.shape_edit_points",
            source_section_sha256: source_readback.section_sha256,
            output_section_sha256: output_readback.section_sha256,
            source_object_sha256: source_readback.object_sha256,
            output_object_sha256: output_readback.object_sha256,
            source_payload_sha256: source_readback.payload_sha256,
            output_payload_sha256: output_readback.payload_sha256,
            source_state_sha256: plan
                .domain_plan
                .source_state()
                .canonical_sha256(state_limits)?,
            target_state_sha256: target_state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
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
    #[allow(clippy::too_many_arguments)]
    pub fn lower_in_section(
        source: &[u8],
        plan: &ShapePointsHwpxPlan,
        current_document_flow_sha256: &str,
        geometry_limits: ObjectGeometryLimits,
        geometry_hwpx_limits: ObjectGeometryHwpxLimits,
        shape_limits: BasicShapeLimits,
        state_limits: ShapePointsLimits,
        hwpx_limits: ShapePointsHwpxLimits,
    ) -> Result<Vec<u8>, ShapePointsHwpxError> {
        Self::lower_in_section_with_receipt(
            source,
            plan,
            current_document_flow_sha256,
            geometry_limits,
            geometry_hwpx_limits,
            shape_limits,
            state_limits,
            hwpx_limits,
        )
        .map(|(bytes, _)| bytes)
    }
}

struct ParsedPayload {
    freeform: FreeformShape,
    payload_span: PayloadSpan,
    payload_qualified_name: String,
    object_sha256: [u8; 32],
    payload_sha256: [u8; 32],
}

#[derive(Clone, Copy)]
struct PayloadSpan {
    start: usize,
    end: usize,
}

impl PayloadSpan {
    const fn start(self) -> usize {
        self.start
    }

    const fn end(self) -> usize {
        self.end
    }

    const fn len(self) -> usize {
        self.end - self.start
    }
}

fn parse_selected(
    source: &[u8],
    object_ordinal: usize,
    shape_limits: BasicShapeLimits,
    limits: ShapePointsHwpxLimits,
) -> Result<ParsedPayload, ShapePointsHwpxError> {
    if source.is_empty()
        || source.len() > limits.0.section_bytes
        || object_ordinal >= limits.0.objects
    {
        return Err(ShapePointsHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(ShapePointsHwpxError::InputLimit);
    }
    let (root_index, kind) = selected_run_freeform(&document, object_ordinal, limits)?;
    let root = element(&document, root_index)?;
    let mut payload = Vec::new();
    let mut child = root.first_child();
    while let Some(index) = child {
        let value = element(&document, index)?;
        if is_payload(value, kind) {
            payload
                .try_reserve(1)
                .map_err(|_| ShapePointsHwpxError::AllocationFailed)?;
            payload.push(index);
        }
        child = value.next_sibling();
    }
    let required_minimum = if kind == ObjectKind::Polygon { 3 } else { 1 };
    let maximum = if kind == ObjectKind::Polygon {
        shape_limits.config().points
    } else {
        shape_limits.config().segments
    };
    if payload.len() < required_minimum || payload.len() > maximum {
        return Err(ShapePointsHwpxError::InvalidPayload);
    }
    for pair in payload.windows(2) {
        if element(&document, pair[0])?.next_sibling() != Some(pair[1]) {
            return Err(ShapePointsHwpxError::InvalidPayload);
        }
    }
    let first = element(&document, payload[0])?;
    let last = element(
        &document,
        *payload.last().ok_or(ShapePointsHwpxError::InvalidPayload)?,
    )?;
    if first.name().prefix().is_none()
        || payload.iter().any(|index| {
            element(&document, *index).map_or(true, |candidate| {
                candidate.name().qualified_name() != first.name().qualified_name()
            })
        })
    {
        return Err(ShapePointsHwpxError::InvalidPayload);
    }
    let first_span = first
        .outer_span()
        .ok_or(ShapePointsHwpxError::InvalidPayload)?;
    let last_span = last
        .outer_span()
        .ok_or(ShapePointsHwpxError::InvalidPayload)?;
    if first_span.start() > last_span.end() || last_span.end() > source.len() {
        return Err(ShapePointsHwpxError::InvalidPayload);
    }
    let payload_span = PayloadSpan {
        start: first_span.start(),
        end: last_span.end(),
    };
    if payload_span.len() > limits.0.payload_bytes {
        return Err(ShapePointsHwpxError::InputLimit);
    }
    let freeform = if kind == ObjectKind::Polygon {
        let mut points = Vec::new();
        points
            .try_reserve_exact(payload.len())
            .map_err(|_| ShapePointsHwpxError::AllocationFailed)?;
        for index in payload {
            points.push(read_point(element(&document, index)?)?);
        }
        FreeformShape::Polygon { points }
    } else {
        let mut segments = Vec::new();
        segments
            .try_reserve_exact(payload.len())
            .map_err(|_| ShapePointsHwpxError::AllocationFailed)?;
        for index in payload {
            segments.push(read_segment(element(&document, index)?)?);
        }
        FreeformShape::Curve { segments }
    };
    let object_span = root
        .outer_span()
        .ok_or(ShapePointsHwpxError::UnsupportedShape)?;
    Ok(ParsedPayload {
        freeform,
        payload_span,
        payload_qualified_name: first.name().qualified_name().to_owned(),
        object_sha256: Sha256::digest(&source[object_span.start()..object_span.end()]).into(),
        payload_sha256: Sha256::digest(&source[payload_span.start()..payload_span.end()]).into(),
    })
}

fn selected_run_freeform(
    document: &PreservingXmlDocument,
    ordinal: usize,
    limits: ShapePointsHwpxLimits,
) -> Result<(usize, ObjectKind), ShapePointsHwpxError> {
    let mut object_seen = 0_usize;
    for (index, candidate) in document.elements().iter().enumerate() {
        let Some(kind) = run_object_kind(candidate) else {
            continue;
        };
        let parent = candidate
            .parent()
            .and_then(|value| document.elements().get(value))
            .ok_or(ShapePointsHwpxError::UnsupportedShape)?;
        if parent.name().namespace() != Some(PARAGRAPH_NS) || parent.name().local_name() != "run" {
            continue;
        }
        if object_seen == ordinal {
            return match kind {
                ObjectKind::Polygon | ObjectKind::Curve => Ok((index, kind)),
                _ => Err(ShapePointsHwpxError::UnsupportedShape),
            };
        }
        object_seen = object_seen
            .checked_add(1)
            .ok_or(ShapePointsHwpxError::InputLimit)?;
        if object_seen > limits.0.objects {
            return Err(ShapePointsHwpxError::InputLimit);
        }
    }
    Err(ShapePointsHwpxError::UnsupportedShape)
}

fn run_object_kind(element: &XmlElementToken) -> Option<ObjectKind> {
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

fn is_payload(element: &XmlElementToken, kind: ObjectKind) -> bool {
    match kind {
        ObjectKind::Polygon => {
            element.name().namespace() == Some(CORE_NS) && element.name().local_name() == "pt"
        }
        ObjectKind::Curve => {
            element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == "seg"
        }
        _ => false,
    }
}

fn read_point(element: &XmlElementToken) -> Result<ShapePoint, ShapePointsHwpxError> {
    validate_attributes(element, &["x", "y"])?;
    if !element.is_empty() {
        return Err(ShapePointsHwpxError::InvalidPayload);
    }
    Ok(ShapePoint {
        x_hwpunit: signed_i32(element, "x")?,
        y_hwpunit: signed_i32(element, "y")?,
    })
}

fn read_segment(element: &XmlElementToken) -> Result<CurveSegment, ShapePointsHwpxError> {
    validate_attributes(element, &["type", "x1", "y1", "x2", "y2"])?;
    if !element.is_empty() {
        return Err(ShapePointsHwpxError::InvalidPayload);
    }
    let segment_type = match attribute(element, "type")? {
        "LINE" => CurveSegmentType::Line,
        "CURVE" => CurveSegmentType::Curve,
        _ => return Err(ShapePointsHwpxError::InvalidPayload),
    };
    Ok(CurveSegment {
        segment_type,
        x1_hwpunit: signed_i32(element, "x1")?,
        y1_hwpunit: signed_i32(element, "y1")?,
        x2_hwpunit: signed_i32(element, "x2")?,
        y2_hwpunit: signed_i32(element, "y2")?,
    })
}

fn payload_fragment(
    freeform: &FreeformShape,
    qualified_name: &str,
    limits: ShapePointsHwpxLimits,
) -> Result<Vec<u8>, ShapePointsHwpxError> {
    let expected_local = match freeform {
        FreeformShape::Polygon { .. } => "pt",
        FreeformShape::Curve { .. } => "seg",
    };
    if qualified_name
        .rsplit_once(':')
        .map_or(qualified_name, |(_, local)| local)
        != expected_local
    {
        return Err(ShapePointsHwpxError::SourceDrift);
    }
    let mut xml = String::new();
    match freeform {
        FreeformShape::Polygon { points } => {
            for point in points {
                write!(
                    xml,
                    "<{qualified_name} x=\"{}\" y=\"{}\"/>",
                    point.x_hwpunit, point.y_hwpunit
                )
                .map_err(|_| ShapePointsHwpxError::AllocationFailed)?;
            }
        }
        FreeformShape::Curve { segments } => {
            for segment in segments {
                let segment_type = match segment.segment_type {
                    CurveSegmentType::Line => "LINE",
                    CurveSegmentType::Curve => "CURVE",
                };
                write!(
                    xml,
                    "<{qualified_name} type=\"{segment_type}\" x1=\"{}\" y1=\"{}\" x2=\"{}\" y2=\"{}\"/>",
                    segment.x1_hwpunit,
                    segment.y1_hwpunit,
                    segment.x2_hwpunit,
                    segment.y2_hwpunit
                )
                .map_err(|_| ShapePointsHwpxError::AllocationFailed)?;
            }
        }
    }
    if xml.len() > limits.0.payload_bytes {
        return Err(ShapePointsHwpxError::OutputLimit);
    }
    Ok(xml.into_bytes())
}

fn replace_span(
    source: &[u8],
    span: PayloadSpan,
    replacement: &[u8],
    limits: ShapePointsHwpxLimits,
) -> Result<Vec<u8>, ShapePointsHwpxError> {
    let output_len = source
        .len()
        .checked_sub(span.len())
        .and_then(|value| value.checked_add(replacement.len()))
        .ok_or(ShapePointsHwpxError::OutputLimit)?;
    if output_len > limits.0.output_bytes {
        return Err(ShapePointsHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| ShapePointsHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..span.start()]);
    output.extend_from_slice(replacement);
    output.extend_from_slice(&source[span.end()..]);
    Ok(output)
}

fn validate_plan(
    plan: &ShapePointsHwpxPlan,
    limits: ShapePointsHwpxLimits,
) -> Result<(), ShapePointsHwpxError> {
    if plan.schema_version != SHAPE_POINTS_SCHEMA_VERSION
        || plan.profile_id != SHAPE_POINTS_HWPX_PROFILE_ID
        || plan.domain_plan.plan_sha256() != plan.domain_plan_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(ShapePointsHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &ShapePointsHwpxPlan,
    limits: ShapePointsHwpxLimits,
) -> Result<String, ShapePointsHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ShapePointsHwpxLimits,
) -> Result<Vec<u8>, ShapePointsHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ShapePointsHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(ShapePointsHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ShapePointsHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(ShapePointsHwpxError::UnsupportedShape)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), ShapePointsHwpxError> {
    if element
        .attributes()
        .iter()
        .any(XmlAttributeToken::is_namespace_declaration)
    {
        return Err(ShapePointsHwpxError::InvalidAttribute);
    }
    let attributes = element
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
        .collect::<Vec<_>>();
    if attributes.len() != allowed.len()
        || allowed.iter().any(|name| {
            attributes
                .iter()
                .filter(|attribute| {
                    attribute.name().namespace().is_none() && attribute.name().local_name() == *name
                })
                .count()
                != 1
        })
    {
        return Err(ShapePointsHwpxError::InvalidAttribute);
    }
    Ok(())
}

fn unique_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, ShapePointsHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(ShapePointsHwpxError::InvalidAttribute)?;
    if matches.next().is_some() {
        return Err(ShapePointsHwpxError::InvalidAttribute);
    }
    Ok(value)
}

fn attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, ShapePointsHwpxError> {
    Ok(unique_attribute(element, name)?.semantic_value())
}

fn signed_i32(element: &XmlElementToken, name: &str) -> Result<i32, ShapePointsHwpxError> {
    let value = attribute(element, name)?;
    if !canonical_signed(value) {
        return Err(ShapePointsHwpxError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| ShapePointsHwpxError::InvalidNumber)
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

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
