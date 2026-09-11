use std::collections::BTreeSet;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    LogicalId, ObjectGeometryLimits, ObjectGeometryState, ObjectGeometryStateDraft, ObjectKind,
};

pub const BASIC_SHAPE_SCHEMA_VERSION: &str = "hwpx-agent.basic-shape/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BasicShapeLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub points: usize,
    pub segments: usize,
    pub text_bytes: usize,
    pub name_bytes: usize,
    pub coordinate_magnitude_hwpunit: i32,
}

impl Default for BasicShapeLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 512 * 1024,
            output_bytes: 512 * 1024,
            points: 16_384,
            segments: 16_384,
            text_bytes: 256 * 1024,
            name_bytes: 4 * 1024,
            coordinate_magnitude_hwpunit: 1_000_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct BasicShapeLimits(BasicShapeLimitConfig);

impl BasicShapeLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_POINTS: usize = 65_536;
    pub const HARD_MAX_SEGMENTS: usize = 65_536;
    pub const HARD_MAX_TEXT_BYTES: usize = 2 * 1024 * 1024;
    pub const HARD_MAX_NAME_BYTES: usize = 16 * 1024;
    pub const HARD_MAX_COORDINATE_MAGNITUDE_HWPUNIT: i32 = 1_000_000_000;

    /// Creates finite basic-shape limits.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or hard-ceiling-exceeding values.
    pub fn new(config: BasicShapeLimitConfig) -> Result<Self, BasicShapeError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.input_bytes > config.output_bytes
            || config.points < 4
            || config.points > Self::HARD_MAX_POINTS
            || config.segments == 0
            || config.segments > Self::HARD_MAX_SEGMENTS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.name_bytes == 0
            || config.name_bytes > Self::HARD_MAX_NAME_BYTES
            || config.coordinate_magnitude_hwpunit <= 0
            || config.coordinate_magnitude_hwpunit > Self::HARD_MAX_COORDINATE_MAGNITUDE_HWPUNIT
        {
            return Err(BasicShapeError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> BasicShapeLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ShapePoint {
    pub x_hwpunit: i32,
    pub y_hwpunit: i32,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LineShape {
    pub is_reverse_hv: bool,
    pub start: ShapePoint,
    pub end: ShapePoint,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RectangleShape {
    pub ratio: u32,
    pub corners: [ShapePoint; 4],
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EllipseArcType {
    Normal,
    Pie,
    Chord,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EllipseShape {
    pub interval_dirty: bool,
    pub has_arc_properties: bool,
    pub arc_type: EllipseArcType,
    pub center: ShapePoint,
    pub axis_1: ShapePoint,
    pub axis_2: ShapePoint,
    pub start_1: ShapePoint,
    pub start_2: ShapePoint,
    pub end_1: ShapePoint,
    pub end_2: ShapePoint,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CurveSegmentType {
    Line,
    Curve,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CurveSegment {
    pub segment_type: CurveSegmentType,
    pub x1_hwpunit: i32,
    pub y1_hwpunit: i32,
    pub x2_hwpunit: i32,
    pub y2_hwpunit: i32,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FreeformShape {
    Polygon { points: Vec<ShapePoint> },
    Curve { segments: Vec<CurveSegment> },
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TextBoxMargins {
    pub left_hwpunit: u32,
    pub right_hwpunit: u32,
    pub top_hwpunit: u32,
    pub bottom_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TextBoxVerticalAlignment {
    Top,
    Center,
    Bottom,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TextBoxContent {
    pub last_width_hwpunit: u32,
    pub name: String,
    pub editable: bool,
    pub margins: TextBoxMargins,
    pub sublist_id: u32,
    pub paragraph_id: u32,
    pub paragraph_properties_id: u32,
    pub style_id: u32,
    pub character_properties_id: u32,
    pub text_width_hwpunit: u32,
    pub text_height_hwpunit: u32,
    pub vertical_alignment: TextBoxVerticalAlignment,
    pub text: String,
}

impl fmt::Debug for TextBoxContent {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TextBoxContent")
            .field("editable", &self.editable)
            .field("vertical_alignment", &self.vertical_alignment)
            .field("content", &"<redacted>")
            .field("native_ids", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum BasicShape {
    Line {
        line: LineShape,
    },
    Rectangle {
        rectangle: RectangleShape,
    },
    Ellipse {
        ellipse: EllipseShape,
    },
    TextBox {
        rectangle: RectangleShape,
        content: TextBoxContent,
    },
    Freeform {
        freeform: FreeformShape,
    },
}

impl BasicShape {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::TextBox { .. } => "obj.textbox_insert",
            Self::Freeform { .. } => "obj.freeform",
            _ => "obj.shape_insert",
        }
    }

    #[must_use]
    pub const fn object_kind(&self) -> ObjectKind {
        match self {
            Self::Line { .. } => ObjectKind::Line,
            Self::Rectangle { .. } | Self::TextBox { .. } => ObjectKind::Rectangle,
            Self::Ellipse { .. } => ObjectKind::Ellipse,
            Self::Freeform {
                freeform: FreeformShape::Polygon { .. },
            } => ObjectKind::Polygon,
            Self::Freeform {
                freeform: FreeformShape::Curve { .. },
            } => ObjectKind::Curve,
        }
    }

    #[must_use]
    pub const fn text_box_content(&self) -> Option<&TextBoxContent> {
        match self {
            Self::TextBox { content, .. } => Some(content),
            _ => None,
        }
    }

    /// Validates this shape against its complete common geometry state.
    ///
    /// # Errors
    ///
    /// Rejects geometry-kind, native-ID, topology, coordinate, text or limit violations.
    pub fn validate_for_geometry(
        &self,
        geometry: &ObjectGeometryState,
        limits: BasicShapeLimits,
    ) -> Result<(), BasicShapeError> {
        validate_shape(self, geometry, limits)
    }
}

impl fmt::Debug for BasicShape {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShape")
            .field("capability_id", &self.capability_id())
            .field("kind", &self.object_kind())
            .field("payload", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct BasicShapeRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub geometry: ObjectGeometryStateDraft,
    pub shape: BasicShape,
}

impl fmt::Debug for BasicShapeRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("request_id", &"<redacted>")
            .field("geometry", &"<redacted>")
            .field("shape", &"<redacted>")
            .field("flow", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct BasicShapeRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    geometry: ObjectGeometryState,
    shape: BasicShape,
}

impl BasicShapeRequest {
    /// Validates the complete common geometry and shape-specific semantic payload.
    ///
    /// # Errors
    ///
    /// Rejects schema, flow, geometry-kind, native ID, topology, text or size drift.
    pub fn from_draft(
        draft: BasicShapeRequestDraft,
        current_document_flow_sha256: &str,
        geometry_limits: ObjectGeometryLimits,
        limits: BasicShapeLimits,
    ) -> Result<Self, BasicShapeError> {
        if draft.schema_version != BASIC_SHAPE_SCHEMA_VERSION {
            return Err(BasicShapeError::UnsupportedVersion);
        }
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(BasicShapeError::FlowDrift);
        }
        let geometry = ObjectGeometryState::from_draft(draft.geometry, geometry_limits)?;
        validate_shape(&draft.shape, &geometry, limits)?;
        let request = Self {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            geometry,
            shape: draft.shape,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict, bounded and duplicate-key-free JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        current_document_flow_sha256: &str,
        geometry_limits: ObjectGeometryLimits,
        limits: BasicShapeLimits,
    ) -> Result<Self, BasicShapeError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(BasicShapeError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| BasicShapeError::InvalidJson)?;
        Self::from_draft(draft, current_document_flow_sha256, geometry_limits, limits)
    }

    #[must_use]
    pub fn request_id(&self) -> &LogicalId {
        &self.request_id
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    #[must_use]
    pub const fn geometry(&self) -> &ObjectGeometryState {
        &self.geometry
    }

    #[must_use]
    pub const fn shape(&self) -> &BasicShape {
        &self.shape
    }

    /// Serializes the complete request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(&self, limits: BasicShapeLimits) -> Result<Vec<u8>, BasicShapeError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for BasicShapeRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeRequest")
            .field("capability_id", &self.shape.capability_id())
            .field("request_id", &"<redacted>")
            .field("geometry", &"<redacted>")
            .field("shape", &"<redacted>")
            .field("flow", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct BasicShapePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    geometry: ObjectGeometryState,
    shape: BasicShape,
    geometry_sha256: String,
    shape_sha256: String,
    request_sha256: String,
    plan_sha256: String,
}

impl BasicShapePlan {
    #[must_use]
    pub fn request_id(&self) -> &LogicalId {
        &self.request_id
    }

    #[must_use]
    pub fn source_document_flow_sha256(&self) -> &str {
        &self.source_document_flow_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    #[must_use]
    pub const fn geometry(&self) -> &ObjectGeometryState {
        &self.geometry
    }

    #[must_use]
    pub const fn shape(&self) -> &BasicShape {
        &self.shape
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the complete plan deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(&self, limits: BasicShapeLimits) -> Result<Vec<u8>, BasicShapeError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for BasicShapePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapePlan")
            .field("capability_id", &self.capability_id)
            .field("request_id", &"<redacted>")
            .field("payload", &"<redacted>")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct BasicShapeReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    plan_sha256: String,
    target_document_flow_sha256: String,
    geometry_sha256: String,
    shape_sha256: String,
}

impl BasicShapeReceipt {
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }
}

impl fmt::Debug for BasicShapeReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct BasicShapeResult {
    geometry: ObjectGeometryState,
    shape: BasicShape,
    receipt: BasicShapeReceipt,
}

impl fmt::Debug for BasicShapeResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BasicShapeResult")
            .field("geometry", &"<redacted>")
            .field("shape", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish_non_exhaustive()
    }
}

impl BasicShapeResult {
    #[must_use]
    pub const fn geometry(&self) -> &ObjectGeometryState {
        &self.geometry
    }

    #[must_use]
    pub const fn shape(&self) -> &BasicShape {
        &self.shape
    }

    #[must_use]
    pub const fn receipt(&self) -> &BasicShapeReceipt {
        &self.receipt
    }
}

#[derive(Debug)]
pub struct BasicShapeBuilder;

#[derive(Serialize)]
struct BasicShapePlanBinding<'a> {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: &'a LogicalId,
    source_document_flow_sha256: &'a str,
    target_document_flow_sha256: &'a str,
    geometry_sha256: &'a str,
    shape_sha256: &'a str,
    request_sha256: &'a str,
}

impl BasicShapeBuilder {
    /// Creates a deterministic plan bound to the exact current document flow.
    ///
    /// # Errors
    ///
    /// Rejects request, geometry, payload, flow or serialization drift.
    pub fn plan(
        request: &BasicShapeRequest,
        current_document_flow_sha256: &str,
        geometry_limits: ObjectGeometryLimits,
        limits: BasicShapeLimits,
    ) -> Result<BasicShapePlan, BasicShapeError> {
        require_digest(current_document_flow_sha256)?;
        if request.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(BasicShapeError::FlowDrift);
        }
        validate_shape(&request.shape, &request.geometry, limits)?;
        let request_sha256 = hex(Sha256::digest(request.canonical_json(limits)?).into());
        let geometry_sha256 = request.geometry.canonical_sha256(geometry_limits)?;
        let shape_sha256 = hex(Sha256::digest(serialize_bounded(&request.shape, limits)?).into());
        let binding = BasicShapePlanBinding {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION,
            capability_id: request.shape.capability_id(),
            request_id: &request.request_id,
            source_document_flow_sha256: current_document_flow_sha256,
            target_document_flow_sha256: &request.target_document_flow_sha256,
            geometry_sha256: &geometry_sha256,
            shape_sha256: &shape_sha256,
            request_sha256: &request_sha256,
        };
        let plan_sha256 = hex(Sha256::digest(serialize_bounded(&binding, limits)?).into());
        let plan = BasicShapePlan {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION,
            capability_id: request.shape.capability_id(),
            request_id: request.request_id.clone(),
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            geometry: request.geometry.clone(),
            shape: request.shape.clone(),
            geometry_sha256,
            shape_sha256,
            request_sha256,
            plan_sha256,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }

    /// Revalidates every plan binding before publishing a semantic result.
    ///
    /// # Errors
    ///
    /// Rejects tampered plans and current-flow drift.
    pub fn build(
        plan: &BasicShapePlan,
        current_document_flow_sha256: &str,
        geometry_limits: ObjectGeometryLimits,
        limits: BasicShapeLimits,
    ) -> Result<BasicShapeResult, BasicShapeError> {
        require_digest(current_document_flow_sha256)?;
        if plan.schema_version != BASIC_SHAPE_SCHEMA_VERSION
            || plan.source_document_flow_sha256 != current_document_flow_sha256
            || plan.capability_id != plan.shape.capability_id()
        {
            return Err(BasicShapeError::BuildDrift);
        }
        validate_shape(&plan.shape, &plan.geometry, limits)?;
        let geometry_sha256 = plan.geometry.canonical_sha256(geometry_limits)?;
        let shape_sha256 = hex(Sha256::digest(serialize_bounded(&plan.shape, limits)?).into());
        if geometry_sha256 != plan.geometry_sha256 || shape_sha256 != plan.shape_sha256 {
            return Err(BasicShapeError::BuildDrift);
        }
        let binding = BasicShapePlanBinding {
            schema_version: BASIC_SHAPE_SCHEMA_VERSION,
            capability_id: plan.capability_id,
            request_id: &plan.request_id,
            source_document_flow_sha256: &plan.source_document_flow_sha256,
            target_document_flow_sha256: &plan.target_document_flow_sha256,
            geometry_sha256: &plan.geometry_sha256,
            shape_sha256: &plan.shape_sha256,
            request_sha256: &plan.request_sha256,
        };
        if hex(Sha256::digest(serialize_bounded(&binding, limits)?).into()) != plan.plan_sha256 {
            return Err(BasicShapeError::BuildDrift);
        }
        Ok(BasicShapeResult {
            geometry: plan.geometry.clone(),
            shape: plan.shape.clone(),
            receipt: BasicShapeReceipt {
                schema_version: BASIC_SHAPE_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                plan_sha256: plan.plan_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                geometry_sha256,
                shape_sha256,
            },
        })
    }
}

#[derive(Debug, Error)]
pub enum BasicShapeError {
    #[error("basic-shape limit configuration is invalid")]
    InvalidLimit,
    #[error("basic-shape schema version is unsupported")]
    UnsupportedVersion,
    #[error("basic-shape JSON is malformed")]
    InvalidJson,
    #[error("basic-shape JSON contains a duplicate key")]
    DuplicateJsonKey,
    #[error("basic-shape input limit was exceeded")]
    InputLimit,
    #[error("basic-shape output limit was exceeded")]
    OutputLimit,
    #[error("basic-shape digest is malformed")]
    InvalidDigest,
    #[error("basic-shape document flow drifted")]
    FlowDrift,
    #[error("basic-shape kind does not match common geometry")]
    KindMismatch,
    #[error("basic-shape topology is invalid")]
    InvalidTopology,
    #[error("basic-shape coordinate is invalid")]
    InvalidCoordinate,
    #[error("basic-shape text state is invalid")]
    InvalidText,
    #[error("basic-shape plan drifted before build")]
    BuildDrift,
    #[error("basic-shape serialization failed")]
    Serialization,
    #[error("object geometry validation failed")]
    Geometry(#[from] crate::ObjectGeometryError),
}

impl BasicShapeError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "basic_shape_invalid_limit",
            Self::UnsupportedVersion => "basic_shape_unsupported_version",
            Self::InvalidJson => "basic_shape_invalid_json",
            Self::DuplicateJsonKey => "basic_shape_duplicate_json_key",
            Self::InputLimit => "basic_shape_input_limit",
            Self::OutputLimit => "basic_shape_output_limit",
            Self::InvalidDigest => "basic_shape_invalid_digest",
            Self::FlowDrift => "basic_shape_flow_drift",
            Self::KindMismatch => "basic_shape_kind_mismatch",
            Self::InvalidTopology => "basic_shape_invalid_topology",
            Self::InvalidCoordinate => "basic_shape_invalid_coordinate",
            Self::InvalidText => "basic_shape_invalid_text",
            Self::BuildDrift => "basic_shape_build_drift",
            Self::Serialization => "basic_shape_serialization",
            Self::Geometry(error) => error.code(),
        }
    }
}

fn validate_shape(
    shape: &BasicShape,
    geometry: &ObjectGeometryState,
    limits: BasicShapeLimits,
) -> Result<(), BasicShapeError> {
    if shape.object_kind() != geometry.object_kind()
        || geometry.native_object_id() == geometry.native_instance_id()
    {
        return Err(BasicShapeError::KindMismatch);
    }
    match shape {
        BasicShape::Line { line } => {
            validate_point(line.start, limits)?;
            validate_point(line.end, limits)?;
            if line.start == line.end {
                return Err(BasicShapeError::InvalidTopology);
            }
        }
        BasicShape::Rectangle { rectangle } => validate_rectangle(rectangle, limits)?,
        BasicShape::Ellipse { ellipse } => validate_ellipse(ellipse, limits)?,
        BasicShape::TextBox { rectangle, content } => {
            validate_rectangle(rectangle, limits)?;
            validate_text_box(content, limits)?;
        }
        BasicShape::Freeform { freeform } => match freeform {
            FreeformShape::Polygon { points } => {
                if points.len() < 3 || points.len() > limits.0.points {
                    return Err(BasicShapeError::InvalidTopology);
                }
                for point in points {
                    validate_point(*point, limits)?;
                }
                if polygon_twice_area(points) == 0 {
                    return Err(BasicShapeError::InvalidTopology);
                }
                let unique = points.iter().copied().collect::<BTreeSet<_>>();
                if unique.len() < 3 {
                    return Err(BasicShapeError::InvalidTopology);
                }
            }
            FreeformShape::Curve { segments } => {
                if segments.is_empty() || segments.len() > limits.0.segments {
                    return Err(BasicShapeError::InvalidTopology);
                }
                for segment in segments {
                    for value in [
                        segment.x1_hwpunit,
                        segment.y1_hwpunit,
                        segment.x2_hwpunit,
                        segment.y2_hwpunit,
                    ] {
                        validate_coordinate(value, limits)?;
                    }
                    if segment.x1_hwpunit == segment.x2_hwpunit
                        && segment.y1_hwpunit == segment.y2_hwpunit
                    {
                        return Err(BasicShapeError::InvalidTopology);
                    }
                }
            }
        },
    }
    Ok(())
}

fn validate_rectangle(
    rectangle: &RectangleShape,
    limits: BasicShapeLimits,
) -> Result<(), BasicShapeError> {
    for point in rectangle.corners {
        validate_point(point, limits)?;
    }
    if polygon_twice_area(&rectangle.corners) == 0
        || rectangle
            .corners
            .iter()
            .copied()
            .collect::<BTreeSet<_>>()
            .len()
            != 4
    {
        return Err(BasicShapeError::InvalidTopology);
    }
    Ok(())
}

fn validate_ellipse(
    ellipse: &EllipseShape,
    limits: BasicShapeLimits,
) -> Result<(), BasicShapeError> {
    for point in [
        ellipse.center,
        ellipse.axis_1,
        ellipse.axis_2,
        ellipse.start_1,
        ellipse.start_2,
        ellipse.end_1,
        ellipse.end_2,
    ] {
        validate_point(point, limits)?;
    }
    let axis_1 = (
        i128::from(ellipse.axis_1.x_hwpunit) - i128::from(ellipse.center.x_hwpunit),
        i128::from(ellipse.axis_1.y_hwpunit) - i128::from(ellipse.center.y_hwpunit),
    );
    let axis_2 = (
        i128::from(ellipse.axis_2.x_hwpunit) - i128::from(ellipse.center.x_hwpunit),
        i128::from(ellipse.axis_2.y_hwpunit) - i128::from(ellipse.center.y_hwpunit),
    );
    if axis_1 == (0, 0) || axis_2 == (0, 0) || axis_1.0 * axis_2.1 - axis_1.1 * axis_2.0 == 0 {
        return Err(BasicShapeError::InvalidTopology);
    }
    Ok(())
}

fn validate_text_box(
    content: &TextBoxContent,
    limits: BasicShapeLimits,
) -> Result<(), BasicShapeError> {
    if content.sublist_id == 0
        || content.paragraph_id == 0
        || content.name.len() > limits.0.name_bytes
        || content.text.len() > limits.0.text_bytes
        || !valid_xml_text(&content.name)
        || !valid_xml_text(&content.text)
    {
        return Err(BasicShapeError::InvalidText);
    }
    Ok(())
}

fn validate_point(point: ShapePoint, limits: BasicShapeLimits) -> Result<(), BasicShapeError> {
    validate_coordinate(point.x_hwpunit, limits)?;
    validate_coordinate(point.y_hwpunit, limits)
}

fn validate_coordinate(value: i32, limits: BasicShapeLimits) -> Result<(), BasicShapeError> {
    if value
        .checked_abs()
        .is_none_or(|magnitude| magnitude > limits.0.coordinate_magnitude_hwpunit)
    {
        return Err(BasicShapeError::InvalidCoordinate);
    }
    Ok(())
}

fn polygon_twice_area(points: &[ShapePoint]) -> i128 {
    points
        .iter()
        .zip(points.iter().cycle().skip(1))
        .take(points.len())
        .map(|(left, right)| {
            i128::from(left.x_hwpunit) * i128::from(right.y_hwpunit)
                - i128::from(left.y_hwpunit) * i128::from(right.x_hwpunit)
        })
        .sum()
}

fn valid_xml_text(value: &str) -> bool {
    value.chars().all(|character| {
        matches!(character, '\u{9}' | '\u{a}' | '\u{d}')
            || ('\u{20}'..='\u{d7ff}').contains(&character)
            || ('\u{e000}'..='\u{fffd}').contains(&character)
            || ('\u{10000}'..='\u{10ffff}').contains(&character)
    })
}

fn require_digest(value: &str) -> Result<(), BasicShapeError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(BasicShapeError::InvalidDigest);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: BasicShapeLimits,
) -> Result<Vec<u8>, BasicShapeError> {
    let bytes = serde_json::to_vec(value).map_err(|_| BasicShapeError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(BasicShapeError::OutputLimit);
    }
    Ok(bytes)
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), BasicShapeError> {
    use serde::de::{DeserializeSeed, MapAccess, SeqAccess, Visitor};

    struct Seed;
    struct AnyVisitor;
    impl<'de> DeserializeSeed<'de> for Seed {
        type Value = ();
        fn deserialize<D>(self, deserializer: D) -> Result<(), D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(AnyVisitor)
        }
    }
    impl<'de> Visitor<'de> for AnyVisitor {
        type Value = ();
        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("duplicate-free JSON")
        }
        fn visit_map<A>(self, mut map: A) -> Result<(), A::Error>
        where
            A: MapAccess<'de>,
        {
            let mut keys = BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(serde::de::Error::custom("duplicate key"));
                }
                map.next_value_seed(Seed)?;
            }
            Ok(())
        }
        fn visit_seq<A>(self, mut sequence: A) -> Result<(), A::Error>
        where
            A: SeqAccess<'de>,
        {
            while sequence.next_element_seed(Seed)?.is_some() {}
            Ok(())
        }
        fn visit_bool<E>(self, _value: bool) -> Result<(), E> {
            Ok(())
        }
        fn visit_i64<E>(self, _value: i64) -> Result<(), E> {
            Ok(())
        }
        fn visit_u64<E>(self, _value: u64) -> Result<(), E> {
            Ok(())
        }
        fn visit_f64<E>(self, _value: f64) -> Result<(), E> {
            Ok(())
        }
        fn visit_str<E>(self, _value: &str) -> Result<(), E> {
            Ok(())
        }
        fn visit_string<E>(self, _value: String) -> Result<(), E> {
            Ok(())
        }
        fn visit_none<E>(self) -> Result<(), E> {
            Ok(())
        }
        fn visit_some<D>(self, deserializer: D) -> Result<(), D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            Seed.deserialize(deserializer)
        }
        fn visit_unit<E>(self) -> Result<(), E> {
            Ok(())
        }
        fn visit_newtype_struct<D>(self, deserializer: D) -> Result<(), D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            Seed.deserialize(deserializer)
        }
        fn visit_bytes<E>(self, _value: &[u8]) -> Result<(), E> {
            Ok(())
        }
        fn visit_byte_buf<E>(self, _value: Vec<u8>) -> Result<(), E> {
            Ok(())
        }
        fn visit_char<E>(self, _value: char) -> Result<(), E> {
            Ok(())
        }
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    Seed.deserialize(&mut deserializer).map_err(|error| {
        if error.to_string().contains("duplicate key") {
            BasicShapeError::DuplicateJsonKey
        } else {
            BasicShapeError::InvalidJson
        }
    })?;
    deserializer.end().map_err(|_| BasicShapeError::InvalidJson)
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

impl Ord for ShapePoint {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        (self.x_hwpunit, self.y_hwpunit).cmp(&(other.x_hwpunit, other.y_hwpunit))
    }
}

impl PartialOrd for ShapePoint {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}
