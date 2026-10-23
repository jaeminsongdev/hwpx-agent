use std::collections::BTreeSet;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const OBJECT_GEOMETRY_SCHEMA_VERSION: &str = "hwpx-agent.object-geometry/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectGeometryLimitConfig {
    pub input_bytes: usize,
    pub serialized_bytes: usize,
    pub extent_hwpunit: u32,
    pub matrix_coefficient_millionths: i64,
}

impl Default for ObjectGeometryLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 256 * 1024,
            serialized_bytes: 256 * 1024,
            extent_hwpunit: 100_000_000,
            matrix_coefficient_millionths: 1_000_000_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ObjectGeometryLimits(ObjectGeometryLimitConfig);

impl ObjectGeometryLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_EXTENT_HWPUNIT: u32 = 1_000_000_000;
    pub const HARD_MAX_MATRIX_COEFFICIENT_MILLIONTHS: i64 = 1_000_000_000_000_000;

    /// Creates finite limits for exact native object geometry.
    ///
    /// # Errors
    ///
    /// Rejects zero, negative, over-ceiling or input/output-inconsistent limits.
    pub fn new(config: ObjectGeometryLimitConfig) -> Result<Self, ObjectGeometryError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
            || config.extent_hwpunit == 0
            || config.extent_hwpunit > Self::HARD_MAX_EXTENT_HWPUNIT
            || config.matrix_coefficient_millionths <= 0
            || config.matrix_coefficient_millionths > Self::HARD_MAX_MATRIX_COEFFICIENT_MILLIONTHS
        {
            return Err(ObjectGeometryError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectGeometryLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectKind {
    Picture,
    Rectangle,
    Ellipse,
    Line,
    Arc,
    Polygon,
    Curve,
    ConnectLine,
    Container,
    Ole,
    Video,
    TextArt,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectNumberingType {
    None,
    Picture,
    Table,
    Equation,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectTextWrap {
    Square,
    TopAndBottom,
    BehindText,
    InFrontOfText,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectTextFlow {
    BothSides,
    LeftOnly,
    RightOnly,
    LargestOnly,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectHorizontalReference {
    Paper,
    Page,
    Column,
    Paragraph,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectVerticalReference {
    Paper,
    Page,
    Paragraph,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectHorizontalAlignment {
    Left,
    Center,
    Right,
    Inside,
    Outside,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectVerticalAlignment {
    Top,
    Center,
    Bottom,
    Inside,
    Outside,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectWidthReference {
    Paper,
    Page,
    Column,
    Paragraph,
    Absolute,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectHeightReference {
    Paper,
    Page,
    Absolute,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectExtent {
    pub width_hwpunit: u32,
    pub height_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectPoint {
    pub x_hwpunit: u32,
    pub y_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectSize {
    pub width_hwpunit: u32,
    pub width_reference: ObjectWidthReference,
    pub height_hwpunit: u32,
    pub height_reference: ObjectHeightReference,
    pub protect: bool,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[allow(clippy::struct_excessive_bools)] // Mirrors five independent OWPML `pos` flags exactly.
pub struct ObjectAnchor {
    pub treat_as_character: bool,
    pub affect_line_spacing: bool,
    pub flow_with_text: bool,
    pub allow_overlap: bool,
    pub hold_anchor_and_shape: bool,
    pub horizontal_reference: ObjectHorizontalReference,
    pub vertical_reference: ObjectVerticalReference,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectPosition {
    pub horizontal_alignment: ObjectHorizontalAlignment,
    pub vertical_alignment: ObjectVerticalAlignment,
    pub horizontal_offset_hwpunit: u32,
    pub vertical_offset_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectWrap {
    pub text_wrap: ObjectTextWrap,
    pub text_flow: ObjectTextFlow,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectOuterMargins {
    pub left_hwpunit: u32,
    pub right_hwpunit: u32,
    pub top_hwpunit: u32,
    pub bottom_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectFlip {
    pub horizontal: bool,
    pub vertical: bool,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectRotation {
    pub angle_degrees: i32,
    pub center_x_hwpunit: u32,
    pub center_y_hwpunit: u32,
    pub rotate_image: bool,
}

/// One OWPML affine matrix in deterministic fixed millionths.
///
/// OWPML stores the matrix as `[e1 e2 e3; e4 e5 e6]`: identity uses `e1=e5=1`,
/// and translation uses `e3`/`e6`. The public model declares six finite FLOAT coefficients.
/// Fixed millionths avoid platform-dependent JSON float serialization while retaining
/// six-decimal source precision.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectAffineMatrix {
    pub e1_millionths: i64,
    pub e2_millionths: i64,
    pub e3_millionths: i64,
    pub e4_millionths: i64,
    pub e5_millionths: i64,
    pub e6_millionths: i64,
}

impl ObjectAffineMatrix {
    pub const IDENTITY: Self = Self {
        e1_millionths: 1_000_000,
        e2_millionths: 0,
        e3_millionths: 0,
        e4_millionths: 0,
        e5_millionths: 1_000_000,
        e6_millionths: 0,
    };
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectTransform {
    pub translation: ObjectAffineMatrix,
    pub scale: ObjectAffineMatrix,
    pub rotation: ObjectAffineMatrix,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectComponentGeometry {
    pub offset: ObjectPoint,
    pub original_size: ObjectExtent,
    pub current_size: ObjectExtent,
    pub flip: ObjectFlip,
    pub rotation: ObjectRotation,
    pub transform: ObjectTransform,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectGeometryStateDraft {
    pub schema_version: String,
    pub object_id: LogicalId,
    pub object_kind: ObjectKind,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub z_order: i32,
    pub numbering_type: ObjectNumberingType,
    pub locked: bool,
    pub size: ObjectSize,
    pub anchor: ObjectAnchor,
    pub position: ObjectPosition,
    pub wrap: ObjectWrap,
    pub outer_margins: ObjectOuterMargins,
    pub component: ObjectComponentGeometry,
}

impl fmt::Debug for ObjectGeometryStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryStateDraft")
            .field("object_kind", &self.object_kind)
            .field("identity", &"<redacted>")
            .field("geometry", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectGeometryState {
    schema_version: &'static str,
    object_id: LogicalId,
    object_kind: ObjectKind,
    native_object_id: u32,
    native_instance_id: u32,
    z_order: i32,
    numbering_type: ObjectNumberingType,
    locked: bool,
    size: ObjectSize,
    anchor: ObjectAnchor,
    position: ObjectPosition,
    wrap: ObjectWrap,
    outer_margins: ObjectOuterMargins,
    component: ObjectComponentGeometry,
}

impl ObjectGeometryState {
    /// Validates a complete exact common-component state.
    ///
    /// # Errors
    ///
    /// Rejects schema drift, zero identity, invalid extents, angles, matrices or output bounds.
    pub fn from_draft(
        draft: ObjectGeometryStateDraft,
        limits: ObjectGeometryLimits,
    ) -> Result<Self, ObjectGeometryError> {
        if draft.schema_version != OBJECT_GEOMETRY_SCHEMA_VERSION {
            return Err(ObjectGeometryError::UnsupportedVersion);
        }
        if draft.native_object_id == 0 || draft.native_instance_id == 0 {
            return Err(ObjectGeometryError::InvalidIdentity);
        }
        let state = Self {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION,
            object_id: draft.object_id,
            object_kind: draft.object_kind,
            native_object_id: draft.native_object_id,
            native_instance_id: draft.native_instance_id,
            z_order: draft.z_order,
            numbering_type: draft.numbering_type,
            locked: draft.locked,
            size: draft.size,
            anchor: draft.anchor,
            position: draft.position,
            wrap: draft.wrap,
            outer_margins: draft.outer_margins,
            component: draft.component,
        };
        validate_state(&state, limits)?;
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    /// Parses strict bounded duplicate-free JSON.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicated, unknown or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        limits: ObjectGeometryLimits,
    ) -> Result<Self, ObjectGeometryError> {
        validate_input(bytes, limits)?;
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ObjectGeometryError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub fn object_id(&self) -> &LogicalId {
        &self.object_id
    }

    #[must_use]
    pub const fn object_kind(&self) -> ObjectKind {
        self.object_kind
    }

    #[must_use]
    pub const fn native_object_id(&self) -> u32 {
        self.native_object_id
    }

    #[must_use]
    pub const fn native_instance_id(&self) -> u32 {
        self.native_instance_id
    }

    #[must_use]
    pub const fn z_order(&self) -> i32 {
        self.z_order
    }

    #[must_use]
    pub const fn numbering_type(&self) -> ObjectNumberingType {
        self.numbering_type
    }

    #[must_use]
    pub const fn locked(&self) -> bool {
        self.locked
    }

    #[must_use]
    pub const fn size(&self) -> ObjectSize {
        self.size
    }

    #[must_use]
    pub const fn anchor(&self) -> ObjectAnchor {
        self.anchor
    }

    #[must_use]
    pub const fn position(&self) -> ObjectPosition {
        self.position
    }

    #[must_use]
    pub const fn wrap(&self) -> ObjectWrap {
        self.wrap
    }

    #[must_use]
    pub const fn outer_margins(&self) -> ObjectOuterMargins {
        self.outer_margins
    }

    #[must_use]
    pub const fn component(&self) -> ObjectComponentGeometry {
        self.component
    }

    /// Returns canonical bounded JSON.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ObjectGeometryLimits,
    ) -> Result<Vec<u8>, ObjectGeometryError> {
        serialize_bounded(self, limits)
    }

    /// Returns the canonical state digest.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_sha256(
        &self,
        limits: ObjectGeometryLimits,
    ) -> Result<String, ObjectGeometryError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }

    fn apply(
        &self,
        operation: ObjectGeometryOperation,
        limits: ObjectGeometryLimits,
    ) -> Result<Self, ObjectGeometryError> {
        validate_state(self, limits)?;
        let mut target = self.clone();
        match operation {
            ObjectGeometryOperation::SetLocked { enabled } => {
                if target.locked == enabled {
                    return Err(ObjectGeometryError::NoOp);
                }
                target.locked = enabled;
            }
            ObjectGeometryOperation::SetPosition { position } => target.position = position,
            ObjectGeometryOperation::SetSize { size, component } => {
                target.size = size;
                target.component = component;
            }
            ObjectGeometryOperation::SetAnchor { anchor } => target.anchor = anchor,
            ObjectGeometryOperation::SetWrap {
                wrap,
                outer_margins,
            } => {
                target.wrap = wrap;
                target.outer_margins = outer_margins;
            }
            ObjectGeometryOperation::SetRotation {
                rotation,
                transform,
            } => {
                target.component.rotation = rotation;
                target.component.transform = transform;
            }
            ObjectGeometryOperation::SetFlip { flip, transform } => {
                target.component.flip = flip;
                target.component.transform = transform;
            }
        }
        validate_state(&target, limits)?;
        let _ = target.canonical_json(limits)?;
        Ok(target)
    }
}

impl fmt::Debug for ObjectGeometryState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryState")
            .field("object_kind", &self.object_kind)
            .field("identity", &"<redacted>")
            .field("geometry", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ObjectGeometryOperation {
    SetLocked {
        enabled: bool,
    },
    SetPosition {
        position: ObjectPosition,
    },
    SetSize {
        size: ObjectSize,
        component: ObjectComponentGeometry,
    },
    SetAnchor {
        anchor: ObjectAnchor,
    },
    SetWrap {
        wrap: ObjectWrap,
        outer_margins: ObjectOuterMargins,
    },
    SetRotation {
        rotation: ObjectRotation,
        transform: ObjectTransform,
    },
    SetFlip {
        flip: ObjectFlip,
        transform: ObjectTransform,
    },
}

impl ObjectGeometryOperation {
    #[must_use]
    pub const fn capability_id(self) -> &'static str {
        match self {
            Self::SetLocked { .. } => "obj.object_protect",
            Self::SetPosition { .. } => "obj.position",
            Self::SetSize { .. } => "obj.size",
            Self::SetAnchor { .. } => "obj.anchor",
            Self::SetWrap { .. } => "obj.wrap",
            Self::SetRotation { .. } => "obj.rotate",
            Self::SetFlip { .. } => "obj.flip",
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectGeometryRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: ObjectGeometryOperation,
}

impl fmt::Debug for ObjectGeometryRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryRequestDraft")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectGeometryRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ObjectGeometryOperation,
}

impl ObjectGeometryRequest {
    /// Validates a request and both exact drift bindings.
    ///
    /// # Errors
    ///
    /// Rejects version, digest, source-state, flow or output drift.
    pub fn from_draft(
        draft: ObjectGeometryRequestDraft,
        source: &ObjectGeometryState,
        current_document_flow_sha256: &str,
        limits: ObjectGeometryLimits,
    ) -> Result<Self, ObjectGeometryError> {
        if draft.schema_version != OBJECT_GEOMETRY_SCHEMA_VERSION {
            return Err(ObjectGeometryError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if source.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(ObjectGeometryError::SourceStateDrift);
        }
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(ObjectGeometryError::DocumentFlowDrift);
        }
        let request = Self {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = serialize_bounded(&request, limits)?;
        Ok(request)
    }

    /// Parses strict bounded duplicate-free request JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicated, unknown, stale or invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &ObjectGeometryState,
        current_document_flow_sha256: &str,
        limits: ObjectGeometryLimits,
    ) -> Result<Self, ObjectGeometryError> {
        validate_input(bytes, limits)?;
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ObjectGeometryError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub fn request_id(&self) -> &LogicalId {
        &self.request_id
    }

    #[must_use]
    pub const fn operation(&self) -> ObjectGeometryOperation {
        self.operation
    }
}

impl fmt::Debug for ObjectGeometryRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectGeometryPlan {
    schema_version: &'static str,
    request_id: LogicalId,
    capability_id: &'static str,
    source_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    target_state: ObjectGeometryState,
    target_state_sha256: String,
    plan_sha256: String,
}

impl ObjectGeometryPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub fn target_state(&self) -> &ObjectGeometryState {
        &self.target_state
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
}

impl fmt::Debug for ObjectGeometryPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryPlan")
            .field("capability_id", &self.capability_id)
            .field("identity", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct ObjectGeometryBuilder;

impl ObjectGeometryBuilder {
    /// Produces a deterministic immutable plan after request-time revalidation.
    ///
    /// # Errors
    ///
    /// Rejects source-state or document-flow drift and every invalid target state.
    pub fn plan(
        source: &ObjectGeometryState,
        request: &ObjectGeometryRequest,
        current_document_flow_sha256: &str,
        limits: ObjectGeometryLimits,
    ) -> Result<ObjectGeometryPlan, ObjectGeometryError> {
        let source_state_sha256 = source.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(ObjectGeometryError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(ObjectGeometryError::DocumentFlowDrift);
        }
        let target_state = source.apply(request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = ObjectGeometryPlan {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION,
            request_id: request.request_id.clone(),
            capability_id: request.operation.capability_id(),
            source_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            target_state,
            target_state_sha256,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = hex(Sha256::digest(serialize_bounded(&plan, limits)?).into());
        let _ = serialize_bounded(&plan, limits)?;
        Ok(plan)
    }

    /// Revalidates the exact source at build time and returns the precomputed target plus receipt.
    ///
    /// # Errors
    ///
    /// Rejects plan tampering, source-state drift and document-flow drift.
    pub fn build(
        plan: &ObjectGeometryPlan,
        current: &ObjectGeometryState,
        current_document_flow_sha256: &str,
        limits: ObjectGeometryLimits,
    ) -> Result<ObjectGeometryResult, ObjectGeometryError> {
        require_digest(current_document_flow_sha256)?;
        let mut unsigned = plan.clone();
        unsigned.plan_sha256.clear();
        if hex(Sha256::digest(serialize_bounded(&unsigned, limits)?).into()) != plan.plan_sha256 {
            return Err(ObjectGeometryError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(ObjectGeometryError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(ObjectGeometryError::DocumentFlowDrift);
        }
        if plan.target_state.canonical_sha256(limits)? != plan.target_state_sha256 {
            return Err(ObjectGeometryError::PlanTampered);
        }
        let receipt = ObjectGeometryReceipt {
            schema_version: OBJECT_GEOMETRY_SCHEMA_VERSION,
            capability_id: plan.capability_id,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: plan.target_state_sha256.clone(),
            source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
            target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
            plan_sha256: plan.plan_sha256.clone(),
        };
        let _ = serialize_bounded(&receipt, limits)?;
        Ok(ObjectGeometryResult {
            state: plan.target_state.clone(),
            receipt,
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectGeometryReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for ObjectGeometryReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectGeometryReceipt")
            .field("capability_id", &self.capability_id)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObjectGeometryResult {
    pub state: ObjectGeometryState,
    pub receipt: ObjectGeometryReceipt,
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectGeometryError {
    #[error("object geometry limits are invalid")]
    InvalidLimit,
    #[error("object geometry input exceeds a finite limit")]
    InputLimit,
    #[error("object geometry JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("object geometry schema version is unsupported")]
    UnsupportedVersion,
    #[error("object geometry native identity is invalid")]
    InvalidIdentity,
    #[error("object geometry extent or offset is invalid")]
    InvalidExtent,
    #[error("object geometry transform is outside deterministic fixed-point bounds")]
    InvalidTransform,
    #[error("object geometry digest is not canonical SHA-256")]
    InvalidDigest,
    #[error("object geometry source state drifted")]
    SourceStateDrift,
    #[error("object geometry document flow drifted")]
    DocumentFlowDrift,
    #[error("object geometry plan was tampered with")]
    PlanTampered,
    #[error("object geometry operation would not change state")]
    NoOp,
    #[error("object geometry serialization failed")]
    Serialization,
    #[error("object geometry serialized output exceeds a finite limit")]
    OutputLimit,
}

impl ObjectGeometryError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_geometry_invalid_limit",
            Self::InputLimit => "object_geometry_input_limit",
            Self::InvalidJson => "object_geometry_invalid_json",
            Self::UnsupportedVersion => "object_geometry_unsupported_version",
            Self::InvalidIdentity => "object_geometry_invalid_identity",
            Self::InvalidExtent => "object_geometry_invalid_extent",
            Self::InvalidTransform => "object_geometry_invalid_transform",
            Self::InvalidDigest => "object_geometry_invalid_digest",
            Self::SourceStateDrift => "object_geometry_source_state_drift",
            Self::DocumentFlowDrift => "object_geometry_document_flow_drift",
            Self::PlanTampered => "object_geometry_plan_tampered",
            Self::NoOp => "object_geometry_no_op",
            Self::Serialization => "object_geometry_serialization",
            Self::OutputLimit => "object_geometry_output_limit",
        }
    }
}

fn validate_state(
    state: &ObjectGeometryState,
    limits: ObjectGeometryLimits,
) -> Result<(), ObjectGeometryError> {
    validate_size(state.size, limits)?;
    validate_point(state.component.offset, limits)?;
    validate_extent(state.component.original_size, limits)?;
    validate_extent(state.component.current_size, limits)?;
    validate_rotation(state.component.rotation, limits)?;
    validate_transform(state.component.transform, limits)?;
    for value in [
        state.position.horizontal_offset_hwpunit,
        state.position.vertical_offset_hwpunit,
        state.outer_margins.left_hwpunit,
        state.outer_margins.right_hwpunit,
        state.outer_margins.top_hwpunit,
        state.outer_margins.bottom_hwpunit,
    ] {
        validate_coordinate(value, limits)?;
    }
    Ok(())
}

fn validate_size(
    value: ObjectSize,
    limits: ObjectGeometryLimits,
) -> Result<(), ObjectGeometryError> {
    validate_extent(
        ObjectExtent {
            width_hwpunit: value.width_hwpunit,
            height_hwpunit: value.height_hwpunit,
        },
        limits,
    )
}

fn validate_point(
    value: ObjectPoint,
    limits: ObjectGeometryLimits,
) -> Result<(), ObjectGeometryError> {
    validate_coordinate(value.x_hwpunit, limits)?;
    validate_coordinate(value.y_hwpunit, limits)
}

fn validate_extent(
    value: ObjectExtent,
    limits: ObjectGeometryLimits,
) -> Result<(), ObjectGeometryError> {
    if value.width_hwpunit == 0 || value.height_hwpunit == 0 {
        return Err(ObjectGeometryError::InvalidExtent);
    }
    validate_coordinate(value.width_hwpunit, limits)?;
    validate_coordinate(value.height_hwpunit, limits)
}

fn validate_coordinate(
    value: u32,
    limits: ObjectGeometryLimits,
) -> Result<(), ObjectGeometryError> {
    if value > limits.0.extent_hwpunit {
        return Err(ObjectGeometryError::InvalidExtent);
    }
    Ok(())
}

fn validate_rotation(
    value: ObjectRotation,
    limits: ObjectGeometryLimits,
) -> Result<(), ObjectGeometryError> {
    validate_coordinate(value.center_x_hwpunit, limits)?;
    validate_coordinate(value.center_y_hwpunit, limits)
}

fn validate_transform(
    value: ObjectTransform,
    limits: ObjectGeometryLimits,
) -> Result<(), ObjectGeometryError> {
    for matrix in [value.translation, value.scale, value.rotation] {
        for coefficient in [
            matrix.e1_millionths,
            matrix.e2_millionths,
            matrix.e3_millionths,
            matrix.e4_millionths,
            matrix.e5_millionths,
            matrix.e6_millionths,
        ] {
            if coefficient
                .checked_abs()
                .is_none_or(|absolute| absolute > limits.0.matrix_coefficient_millionths)
            {
                return Err(ObjectGeometryError::InvalidTransform);
            }
        }
    }
    Ok(())
}

fn validate_input(bytes: &[u8], limits: ObjectGeometryLimits) -> Result<(), ObjectGeometryError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(ObjectGeometryError::InputLimit);
    }
    Ok(())
}

fn require_digest(value: &str) -> Result<(), ObjectGeometryError> {
    if value.len() != 64
        || value
            .as_bytes()
            .iter()
            .any(|byte| !matches!(*byte, b'0'..=b'9' | b'a'..=b'f'))
    {
        return Err(ObjectGeometryError::InvalidDigest);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectGeometryLimits,
) -> Result<Vec<u8>, ObjectGeometryError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectGeometryError::Serialization)?;
    if bytes.len() > limits.0.serialized_bytes {
        return Err(ObjectGeometryError::OutputLimit);
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

#[allow(clippy::too_many_lines)]
fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ObjectGeometryError> {
    struct RootVisitor;
    struct AnyVisitor;
    struct Seed;

    impl<'de> serde::de::DeserializeSeed<'de> for Seed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(AnyVisitor)
        }
    }

    fn visit_map<'de, A>(mut map: A) -> Result<(), A::Error>
    where
        A: serde::de::MapAccess<'de>,
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

    impl<'de> serde::de::Visitor<'de> for RootVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }

        fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            visit_map(map)
        }
    }

    impl<'de> serde::de::Visitor<'de> for AnyVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("any JSON value")
        }

        fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            visit_map(map)
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(Seed)?.is_some() {}
            Ok(())
        }

        fn visit_bool<E>(self, _value: bool) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_i64<E>(self, _value: i64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_u64<E>(self, _value: u64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_f64<E>(self, _value: f64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_str<E>(self, _value: &str) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    serde::de::Deserializer::deserialize_map(&mut deserializer, RootVisitor)
        .map_err(|_| ObjectGeometryError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| ObjectGeometryError::InvalidJson)
}
