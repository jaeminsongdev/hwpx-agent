use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LogicalId, ObjectCaption};

pub const OBJECT_SPECIAL_SCHEMA_VERSION: &str = "hwpx-agent.object-special/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectSpecialLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub objects: usize,
    pub captions: usize,
    pub string_bytes: usize,
    pub asset_bytes: u64,
    pub extent_hwpunit: u32,
}

impl Default for ObjectSpecialLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            objects: 16_384,
            captions: 16_384,
            string_bytes: 64 * 1024,
            asset_bytes: 512 * 1024 * 1024,
            extent_hwpunit: 1_000_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectSpecialLimits(ObjectSpecialLimitConfig);

impl ObjectSpecialLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_OBJECTS: usize = 1_000_000;
    pub const HARD_MAX_STRING_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_ASSET_BYTES: u64 = 16 * 1024 * 1024 * 1024;
    pub const HARD_MAX_EXTENT_HWPUNIT: u32 = 2_000_000_000;

    /// Creates finite limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent or hard-ceiling-exceeding values.
    pub fn new(config: ObjectSpecialLimitConfig) -> Result<Self, ObjectSpecialError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.objects == 0
            || config.objects > Self::HARD_MAX_OBJECTS
            || config.captions == 0
            || config.captions > Self::HARD_MAX_OBJECTS
            || config.string_bytes == 0
            || config.string_bytes > Self::HARD_MAX_STRING_BYTES
            || config.asset_bytes == 0
            || config.asset_bytes > Self::HARD_MAX_ASSET_BYTES
            || config.extent_hwpunit == 0
            || config.extent_hwpunit > Self::HARD_MAX_EXTENT_HWPUNIT
        {
            return Err(ObjectSpecialError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectSpecialLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectIdentity {
    pub logical_object_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
}

impl fmt::Debug for ObjectIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ObjectIdentity(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SpecialObjectKind {
    DrawingGallery,
    FormObject,
    ParagraphBand,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum GalleryAssetKind {
    Image,
    Shape,
    TextBox,
    Chart,
    EmbeddedObject,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DrawingGalleryPayload {
    pub asset_id: String,
    pub relationship_id: String,
    pub asset_kind: GalleryAssetKind,
    pub media_type: String,
    pub byte_len: u64,
    pub payload_sha256: String,
    pub template_family: String,
    pub template_key: String,
}

impl fmt::Debug for DrawingGalleryPayload {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DrawingGalleryPayload")
            .field("asset_kind", &self.asset_kind)
            .field("asset", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StaticFormControlKind {
    PushButton,
    CheckBox,
    RadioButton,
    ComboBox,
    ListBox,
    EditBox,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct StaticFormPayload {
    pub control_kind: StaticFormControlKind,
    pub name: String,
    pub value: String,
    pub enabled: bool,
    pub printable: bool,
    pub active_content_present: bool,
    pub form_properties_sha256: String,
}

impl fmt::Debug for StaticFormPayload {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("StaticFormPayload")
            .field("control_kind", &self.control_kind)
            .field("active_content_present", &self.active_content_present)
            .field("content", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ParagraphBandPlacement {
    BeforeParagraph,
    BehindParagraph,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ParagraphBandPayload {
    pub paragraph_id: LogicalId,
    pub placement: ParagraphBandPlacement,
    pub height_hwpunit: u32,
    pub width_hwpunit: u32,
    pub band_style_sha256: String,
}

impl fmt::Debug for ParagraphBandPayload {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ParagraphBandPayload")
            .field("placement", &self.placement)
            .field("identity", &"<redacted>")
            .field("style", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum SpecialObjectPayload {
    DrawingGallery { gallery: DrawingGalleryPayload },
    FormObject { form: StaticFormPayload },
    ParagraphBand { band: ParagraphBandPayload },
}

impl fmt::Debug for SpecialObjectPayload {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let kind = match self {
            Self::DrawingGallery { .. } => SpecialObjectKind::DrawingGallery,
            Self::FormObject { .. } => SpecialObjectKind::FormObject,
            Self::ParagraphBand { .. } => SpecialObjectKind::ParagraphBand,
        };
        formatter
            .debug_struct("SpecialObjectPayload")
            .field("kind", &kind)
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SpecialObjectState {
    pub identity: ObjectIdentity,
    pub object_kind: SpecialObjectKind,
    pub geometry_state_sha256: String,
    pub appearance_state_sha256: String,
    pub property_state_sha256: String,
    pub resource_state_sha256: String,
    pub embedded_content_state_sha256: String,
    pub opaque_state_sha256: String,
    pub payload: SpecialObjectPayload,
}

impl fmt::Debug for SpecialObjectState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SpecialObjectState")
            .field("object_kind", &self.object_kind)
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectCaptionBinding {
    pub target: ObjectIdentity,
    pub caption: ObjectCaption,
}

impl fmt::Debug for ObjectCaptionBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ObjectCaptionBinding(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectSpecialDocumentStateDraft {
    pub schema_version: String,
    pub document_order: Vec<LogicalId>,
    pub external_objects: Vec<ObjectIdentity>,
    pub special_objects: Vec<SpecialObjectState>,
    pub captions: Vec<ObjectCaptionBinding>,
    pub paragraph_ids: Vec<LogicalId>,
    pub resource_ids: Vec<String>,
    pub relationship_ids: Vec<String>,
    pub document_payload_sha256: String,
    pub document_properties_sha256: String,
    pub resource_inventory_sha256: String,
    pub paragraph_inventory_sha256: String,
    pub opaque_document_state_sha256: String,
}

impl fmt::Debug for ObjectSpecialDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ObjectSpecialDocumentStateDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectSpecialDocumentState {
    schema_version: &'static str,
    document_order: Vec<LogicalId>,
    external_objects: Vec<ObjectIdentity>,
    special_objects: Vec<SpecialObjectState>,
    captions: Vec<ObjectCaptionBinding>,
    paragraph_ids: Vec<LogicalId>,
    resource_ids: Vec<String>,
    relationship_ids: Vec<String>,
    document_payload_sha256: String,
    document_properties_sha256: String,
    resource_inventory_sha256: String,
    paragraph_inventory_sha256: String,
    opaque_document_state_sha256: String,
}

impl ObjectSpecialDocumentState {
    /// Validates and seals a complete special-object inventory and its preserved document state.
    ///
    /// # Errors
    ///
    /// Rejects version, identity, ordering, payload, resource, caption or output drift.
    pub fn from_draft(
        draft: ObjectSpecialDocumentStateDraft,
        limits: ObjectSpecialLimits,
    ) -> Result<Self, ObjectSpecialError> {
        if draft.schema_version != OBJECT_SPECIAL_SCHEMA_VERSION {
            return Err(ObjectSpecialError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION,
            document_order: draft.document_order,
            external_objects: draft.external_objects,
            special_objects: draft.special_objects,
            captions: draft.captions,
            paragraph_ids: draft.paragraph_ids,
            resource_ids: draft.resource_ids,
            relationship_ids: draft.relationship_ids,
            document_payload_sha256: draft.document_payload_sha256,
            document_properties_sha256: draft.document_properties_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            paragraph_inventory_sha256: draft.paragraph_inventory_sha256,
            opaque_document_state_sha256: draft.opaque_document_state_sha256,
        };
        validate_state(&state, limits)?;
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub fn document_order(&self) -> &[LogicalId] {
        &self.document_order
    }

    #[must_use]
    pub fn special_objects(&self) -> &[SpecialObjectState] {
        &self.special_objects
    }

    #[must_use]
    pub fn captions(&self) -> &[ObjectCaptionBinding] {
        &self.captions
    }

    /// Calculates the canonical resource inventory digest used by this state.
    ///
    /// # Errors
    ///
    /// Rejects non-canonical resource lists or a serialization bound violation.
    pub fn resource_inventory_sha256_for(
        resource_ids: &[String],
        relationship_ids: &[String],
        limits: ObjectSpecialLimits,
    ) -> Result<String, ObjectSpecialError> {
        validate_name_inventory(resource_ids, limits)?;
        validate_name_inventory(relationship_ids, limits)?;
        Ok(hex(Sha256::digest(serialize_bounded(
            &(resource_ids, relationship_ids),
            limits,
        )?)
        .into()))
    }

    /// Serializes the complete state deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ObjectSpecialLimits,
    ) -> Result<Vec<u8>, ObjectSpecialError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_sha256(
        &self,
        limits: ObjectSpecialLimits,
    ) -> Result<String, ObjectSpecialError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for ObjectSpecialDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectSpecialDocumentState")
            .field("object_count", &self.document_order.len())
            .field("caption_count", &self.captions.len())
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ObjectSpecialOperation {
    InsertDrawingGallery {
        insertion_index: usize,
        object: SpecialObjectState,
    },
    InsertFormObject {
        insertion_index: usize,
        object: SpecialObjectState,
    },
    InsertParagraphBand {
        insertion_index: usize,
        object: SpecialObjectState,
    },
    InsertCaption {
        target: ObjectIdentity,
        caption: ObjectCaption,
    },
}

impl ObjectSpecialOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::InsertDrawingGallery { .. } => "obj.drawing_gallery",
            Self::InsertFormObject { .. } => "obj.form_object_insert",
            Self::InsertParagraphBand { .. } => "obj.paragraph_band_object",
            Self::InsertCaption { .. } => "obj.caption_insert",
        }
    }
}

impl fmt::Debug for ObjectSpecialOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectSpecialOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectSpecialRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: ObjectSpecialOperation,
}

impl fmt::Debug for ObjectSpecialRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectSpecialRequestDraft")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectSpecialRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ObjectSpecialOperation,
}

impl ObjectSpecialRequest {
    /// Validates one exact insertion against current inventory and document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, state, flow, identity, kind, resource, caption or output drift.
    pub fn from_draft(
        draft: ObjectSpecialRequestDraft,
        current: &ObjectSpecialDocumentState,
        current_document_flow_sha256: &str,
        limits: ObjectSpecialLimits,
    ) -> Result<Self, ObjectSpecialError> {
        if draft.schema_version != OBJECT_SPECIAL_SCHEMA_VERSION {
            return Err(ObjectSpecialError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if current.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(ObjectSpecialError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(ObjectSpecialError::DocumentFlowDrift);
        }
        let _ = apply_operation(current, &draft.operation, limits)?;
        let request = Self {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict, bounded and duplicate-key-free request JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized, stale or invalid input.
    pub fn from_json(
        bytes: &[u8],
        current: &ObjectSpecialDocumentState,
        current_document_flow_sha256: &str,
        limits: ObjectSpecialLimits,
    ) -> Result<Self, ObjectSpecialError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(ObjectSpecialError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| ObjectSpecialError::InvalidJson)?;
        Self::from_draft(draft, current, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub fn operation(&self) -> &ObjectSpecialOperation {
        &self.operation
    }

    /// Serializes the complete request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ObjectSpecialLimits,
    ) -> Result<Vec<u8>, ObjectSpecialError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectSpecialRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectSpecialRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectSpecialPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state: ObjectSpecialDocumentState,
    source_state_sha256: String,
    target_state: ObjectSpecialDocumentState,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ObjectSpecialOperation,
    plan_sha256: String,
}

impl ObjectSpecialPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn target_state(&self) -> &ObjectSpecialDocumentState {
        &self.target_state
    }
}

impl fmt::Debug for ObjectSpecialPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectSpecialPlan")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct ObjectSpecialBuilder;

impl ObjectSpecialBuilder {
    /// Creates a deterministic plan after rechecking exact inventory and flow.
    ///
    /// # Errors
    ///
    /// Rejects source-state, document-flow, operation or output drift.
    pub fn plan(
        current: &ObjectSpecialDocumentState,
        request: &ObjectSpecialRequest,
        current_document_flow_sha256: &str,
        limits: ObjectSpecialLimits,
    ) -> Result<ObjectSpecialPlan, ObjectSpecialError> {
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(ObjectSpecialError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(ObjectSpecialError::DocumentFlowDrift);
        }
        let target_state = apply_operation(current, &request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = ObjectSpecialPlan {
            schema_version: OBJECT_SPECIAL_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: request.request_id.clone(),
            source_state: current.clone(),
            source_state_sha256,
            target_state,
            target_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, limits)?;
        let _ = serialize_bounded(&plan, limits)?;
        Ok(plan)
    }

    /// Revalidates plan integrity, current inventory and current flow before publishing.
    ///
    /// # Errors
    ///
    /// Rejects plan tampering, source-state drift and document-flow drift.
    pub fn build(
        plan: &ObjectSpecialPlan,
        current: &ObjectSpecialDocumentState,
        current_document_flow_sha256: &str,
        limits: ObjectSpecialLimits,
    ) -> Result<ObjectSpecialResult, ObjectSpecialError> {
        if plan.schema_version != OBJECT_SPECIAL_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan_binding_sha256(plan, limits)? != plan.plan_sha256
            || plan.source_state.canonical_sha256(limits)? != plan.source_state_sha256
            || plan.target_state.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(ObjectSpecialError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(ObjectSpecialError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(ObjectSpecialError::DocumentFlowDrift);
        }
        if apply_operation(&plan.source_state, &plan.operation, limits)? != plan.target_state {
            return Err(ObjectSpecialError::PlanTampered);
        }
        Ok(ObjectSpecialResult {
            state: plan.target_state.clone(),
            receipt: ObjectSpecialReceipt {
                schema_version: OBJECT_SPECIAL_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                source_state_sha256: plan.source_state_sha256.clone(),
                target_state_sha256: plan.target_state_sha256.clone(),
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                plan_sha256: plan.plan_sha256.clone(),
            },
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectSpecialReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for ObjectSpecialReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectSpecialReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectSpecialResult {
    pub state: ObjectSpecialDocumentState,
    pub receipt: ObjectSpecialReceipt,
}

impl fmt::Debug for ObjectSpecialResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectSpecialResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectSpecialError {
    #[error("special-object limits are invalid")]
    InvalidLimit,
    #[error("special-object input exceeds a finite limit")]
    InputLimit,
    #[error("special-object JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("special-object schema version is unsupported")]
    UnsupportedVersion,
    #[error("special-object digest is invalid")]
    InvalidDigest,
    #[error("special-object identity or order is invalid")]
    InvalidIdentity,
    #[error("special-object kind and payload do not match")]
    KindMismatch,
    #[error("special-object payload is invalid")]
    InvalidPayload,
    #[error("special-object active content is denied")]
    ActiveContentDenied,
    #[error("special-object caption target is invalid or already captioned")]
    InvalidCaption,
    #[error("special-object insertion index is invalid")]
    InvalidInsertionIndex,
    #[error("special-object source state drifted")]
    SourceStateDrift,
    #[error("special-object document flow drifted")]
    DocumentFlowDrift,
    #[error("special-object plan was tampered with")]
    PlanTampered,
    #[error("special-object serialization failed")]
    Serialization,
    #[error("special-object output exceeds a finite limit")]
    OutputLimit,
}

impl ObjectSpecialError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_special_invalid_limit",
            Self::InputLimit => "object_special_input_limit",
            Self::InvalidJson => "object_special_invalid_json",
            Self::UnsupportedVersion => "object_special_unsupported_version",
            Self::InvalidDigest => "object_special_invalid_digest",
            Self::InvalidIdentity => "object_special_invalid_identity",
            Self::KindMismatch => "object_special_kind_mismatch",
            Self::InvalidPayload => "object_special_invalid_payload",
            Self::ActiveContentDenied => "object_special_active_content_denied",
            Self::InvalidCaption => "object_special_invalid_caption",
            Self::InvalidInsertionIndex => "object_special_invalid_insertion_index",
            Self::SourceStateDrift => "object_special_source_state_drift",
            Self::DocumentFlowDrift => "object_special_document_flow_drift",
            Self::PlanTampered => "object_special_plan_tampered",
            Self::Serialization => "object_special_serialization",
            Self::OutputLimit => "object_special_output_limit",
        }
    }
}

fn apply_operation(
    source: &ObjectSpecialDocumentState,
    operation: &ObjectSpecialOperation,
    limits: ObjectSpecialLimits,
) -> Result<ObjectSpecialDocumentState, ObjectSpecialError> {
    validate_state(source, limits)?;
    let mut target = source.clone();
    match operation {
        ObjectSpecialOperation::InsertDrawingGallery {
            insertion_index,
            object,
        } => insert_object(
            &mut target,
            *insertion_index,
            object,
            SpecialObjectKind::DrawingGallery,
            limits,
        )?,
        ObjectSpecialOperation::InsertFormObject {
            insertion_index,
            object,
        } => insert_object(
            &mut target,
            *insertion_index,
            object,
            SpecialObjectKind::FormObject,
            limits,
        )?,
        ObjectSpecialOperation::InsertParagraphBand {
            insertion_index,
            object,
        } => insert_object(
            &mut target,
            *insertion_index,
            object,
            SpecialObjectKind::ParagraphBand,
            limits,
        )?,
        ObjectSpecialOperation::InsertCaption {
            target: identity,
            caption,
        } => {
            let identities = identity_map(source)?;
            if identities
                .get(&identity.logical_object_id)
                .is_none_or(|current| current != identity)
                || source
                    .captions
                    .iter()
                    .any(|current| current.target.logical_object_id == identity.logical_object_id)
            {
                return Err(ObjectSpecialError::InvalidCaption);
            }
            validate_caption(caption, limits)?;
            let order = source
                .document_order
                .iter()
                .position(|id| id == &identity.logical_object_id)
                .ok_or(ObjectSpecialError::InvalidCaption)?;
            let insertion = target
                .captions
                .iter()
                .position(|binding| {
                    source
                        .document_order
                        .iter()
                        .position(|id| id == &binding.target.logical_object_id)
                        .is_some_and(|position| position > order)
                })
                .unwrap_or(target.captions.len());
            target.captions.insert(
                insertion,
                ObjectCaptionBinding {
                    target: identity.clone(),
                    caption: caption.clone(),
                },
            );
        }
    }
    validate_state(&target, limits)?;
    Ok(target)
}

fn insert_object(
    state: &mut ObjectSpecialDocumentState,
    insertion_index: usize,
    object: &SpecialObjectState,
    expected_kind: SpecialObjectKind,
    limits: ObjectSpecialLimits,
) -> Result<(), ObjectSpecialError> {
    if insertion_index > state.document_order.len() {
        return Err(ObjectSpecialError::InvalidInsertionIndex);
    }
    if object.object_kind != expected_kind || payload_kind(&object.payload) != expected_kind {
        return Err(ObjectSpecialError::KindMismatch);
    }
    validate_special_object(object, limits)?;
    if identity_map(state)?.contains_key(&object.identity.logical_object_id)
        || state.external_objects.iter().any(|identity| {
            identity.native_object_id == object.identity.native_object_id
                || identity.native_instance_id == object.identity.native_instance_id
        })
        || state.special_objects.iter().any(|current| {
            current.identity.native_object_id == object.identity.native_object_id
                || current.identity.native_instance_id == object.identity.native_instance_id
        })
    {
        return Err(ObjectSpecialError::InvalidIdentity);
    }
    let special_index = state
        .special_objects
        .iter()
        .filter(|current| {
            state.document_order[..insertion_index].contains(&current.identity.logical_object_id)
        })
        .count();
    state
        .document_order
        .insert(insertion_index, object.identity.logical_object_id.clone());
    state.special_objects.insert(special_index, object.clone());
    if let SpecialObjectPayload::DrawingGallery { gallery } = &object.payload {
        if state.resource_ids.binary_search(&gallery.asset_id).is_ok()
            || state
                .relationship_ids
                .binary_search(&gallery.relationship_id)
                .is_ok()
        {
            return Err(ObjectSpecialError::InvalidPayload);
        }
        let resource_index = state
            .resource_ids
            .binary_search(&gallery.asset_id)
            .unwrap_or_else(|index| index);
        state
            .resource_ids
            .insert(resource_index, gallery.asset_id.clone());
        let relationship_index = state
            .relationship_ids
            .binary_search(&gallery.relationship_id)
            .unwrap_or_else(|index| index);
        state
            .relationship_ids
            .insert(relationship_index, gallery.relationship_id.clone());
        state.resource_inventory_sha256 =
            ObjectSpecialDocumentState::resource_inventory_sha256_for(
                &state.resource_ids,
                &state.relationship_ids,
                limits,
            )?;
    }
    Ok(())
}

fn validate_state(
    state: &ObjectSpecialDocumentState,
    limits: ObjectSpecialLimits,
) -> Result<(), ObjectSpecialError> {
    if state.schema_version != OBJECT_SPECIAL_SCHEMA_VERSION
        || state.document_order.len() > limits.0.objects
        || state.external_objects.len() + state.special_objects.len() != state.document_order.len()
        || state.captions.len() > limits.0.captions
    {
        return Err(ObjectSpecialError::InvalidIdentity);
    }
    for digest in [
        &state.document_payload_sha256,
        &state.document_properties_sha256,
        &state.resource_inventory_sha256,
        &state.paragraph_inventory_sha256,
        &state.opaque_document_state_sha256,
    ] {
        require_digest(digest)?;
    }
    if ObjectSpecialDocumentState::resource_inventory_sha256_for(
        &state.resource_ids,
        &state.relationship_ids,
        limits,
    )? != state.resource_inventory_sha256
    {
        return Err(ObjectSpecialError::InvalidPayload);
    }
    let mut paragraphs = BTreeSet::new();
    if state.paragraph_ids.len() > limits.0.objects
        || state.paragraph_ids.iter().any(|id| !paragraphs.insert(id))
    {
        return Err(ObjectSpecialError::InvalidPayload);
    }
    let identities = identity_map(state)?;
    if identities.len() != state.document_order.len()
        || state.document_order.iter().enumerate().any(|(index, id)| {
            state.document_order[..index].contains(id) || !identities.contains_key(id)
        })
    {
        return Err(ObjectSpecialError::InvalidIdentity);
    }
    let mut native_objects = BTreeSet::new();
    let mut native_instances = BTreeSet::new();
    for identity in identities.values() {
        if identity.native_object_id == 0
            || identity.native_instance_id == 0
            || !native_objects.insert(identity.native_object_id)
            || !native_instances.insert(identity.native_instance_id)
        {
            return Err(ObjectSpecialError::InvalidIdentity);
        }
    }
    for object in &state.special_objects {
        validate_special_object(object, limits)?;
        validate_document_payload_binding(object, state, &paragraphs)?;
    }
    validate_subsequence(
        &state.document_order,
        state
            .external_objects
            .iter()
            .map(|identity| &identity.logical_object_id),
    )?;
    validate_subsequence(
        &state.document_order,
        state
            .special_objects
            .iter()
            .map(|object| &object.identity.logical_object_id),
    )?;
    let mut captioned = BTreeSet::new();
    let mut prior_position = None;
    for binding in &state.captions {
        if identities
            .get(&binding.target.logical_object_id)
            .is_none_or(|identity| identity != &binding.target)
            || !captioned.insert(&binding.target.logical_object_id)
        {
            return Err(ObjectSpecialError::InvalidCaption);
        }
        validate_caption(&binding.caption, limits)?;
        let position = state
            .document_order
            .iter()
            .position(|id| id == &binding.target.logical_object_id)
            .ok_or(ObjectSpecialError::InvalidCaption)?;
        if prior_position.is_some_and(|prior| prior >= position) {
            return Err(ObjectSpecialError::InvalidCaption);
        }
        prior_position = Some(position);
    }
    Ok(())
}

fn validate_document_payload_binding(
    object: &SpecialObjectState,
    state: &ObjectSpecialDocumentState,
    paragraphs: &BTreeSet<&LogicalId>,
) -> Result<(), ObjectSpecialError> {
    if let SpecialObjectPayload::DrawingGallery { gallery } = &object.payload
        && (state.resource_ids.binary_search(&gallery.asset_id).is_err()
            || state
                .relationship_ids
                .binary_search(&gallery.relationship_id)
                .is_err())
    {
        return Err(ObjectSpecialError::InvalidPayload);
    }
    if let SpecialObjectPayload::ParagraphBand { band } = &object.payload
        && !paragraphs.contains(&band.paragraph_id)
    {
        return Err(ObjectSpecialError::InvalidPayload);
    }
    Ok(())
}

fn identity_map(
    state: &ObjectSpecialDocumentState,
) -> Result<BTreeMap<LogicalId, ObjectIdentity>, ObjectSpecialError> {
    let mut identities = BTreeMap::new();
    for identity in state
        .external_objects
        .iter()
        .chain(state.special_objects.iter().map(|object| &object.identity))
    {
        if identities
            .insert(identity.logical_object_id.clone(), identity.clone())
            .is_some()
        {
            return Err(ObjectSpecialError::InvalidIdentity);
        }
    }
    Ok(identities)
}

fn validate_subsequence<'a>(
    order: &[LogicalId],
    ids: impl Iterator<Item = &'a LogicalId>,
) -> Result<(), ObjectSpecialError> {
    let mut prior = None;
    for id in ids {
        let position = order
            .iter()
            .position(|candidate| candidate == id)
            .ok_or(ObjectSpecialError::InvalidIdentity)?;
        if prior.is_some_and(|prior| prior >= position) {
            return Err(ObjectSpecialError::InvalidIdentity);
        }
        prior = Some(position);
    }
    Ok(())
}

fn validate_special_object(
    object: &SpecialObjectState,
    limits: ObjectSpecialLimits,
) -> Result<(), ObjectSpecialError> {
    if object.identity.native_object_id == 0
        || object.identity.native_instance_id == 0
        || object.object_kind != payload_kind(&object.payload)
    {
        return Err(ObjectSpecialError::KindMismatch);
    }
    for digest in [
        &object.geometry_state_sha256,
        &object.appearance_state_sha256,
        &object.property_state_sha256,
        &object.resource_state_sha256,
        &object.embedded_content_state_sha256,
        &object.opaque_state_sha256,
    ] {
        require_digest(digest)?;
    }
    match &object.payload {
        SpecialObjectPayload::DrawingGallery { gallery } => {
            if !valid_token(&gallery.asset_id, limits.0.string_bytes)
                || !valid_token(&gallery.relationship_id, limits.0.string_bytes)
                || !valid_media_type(&gallery.media_type, limits.0.string_bytes)
                || gallery.byte_len == 0
                || gallery.byte_len > limits.0.asset_bytes
                || !valid_token(&gallery.template_family, limits.0.string_bytes)
                || !valid_token(&gallery.template_key, limits.0.string_bytes)
            {
                return Err(ObjectSpecialError::InvalidPayload);
            }
            require_digest(&gallery.payload_sha256)?;
        }
        SpecialObjectPayload::FormObject { form } => {
            if form.active_content_present {
                return Err(ObjectSpecialError::ActiveContentDenied);
            }
            if !valid_token(&form.name, limits.0.string_bytes)
                || !valid_text(&form.value, limits.0.string_bytes, true)
            {
                return Err(ObjectSpecialError::InvalidPayload);
            }
            require_digest(&form.form_properties_sha256)?;
        }
        SpecialObjectPayload::ParagraphBand { band } => {
            if band.height_hwpunit == 0
                || band.width_hwpunit == 0
                || band.height_hwpunit > limits.0.extent_hwpunit
                || band.width_hwpunit > limits.0.extent_hwpunit
            {
                return Err(ObjectSpecialError::InvalidPayload);
            }
            require_digest(&band.band_style_sha256)?;
        }
    }
    Ok(())
}

fn validate_caption(
    caption: &ObjectCaption,
    limits: ObjectSpecialLimits,
) -> Result<(), ObjectSpecialError> {
    if caption.width_hwpunit == 0
        || caption.width_hwpunit > limits.0.extent_hwpunit
        || caption.gap_hwpunit > limits.0.extent_hwpunit
        || !valid_text(&caption.label, limits.0.string_bytes, false)
        || !valid_text(&caption.text, limits.0.string_bytes, true)
    {
        return Err(ObjectSpecialError::InvalidCaption);
    }
    Ok(())
}

fn validate_name_inventory(
    values: &[String],
    limits: ObjectSpecialLimits,
) -> Result<(), ObjectSpecialError> {
    if values.len() > limits.0.objects
        || values
            .iter()
            .any(|value| !valid_token(value, limits.0.string_bytes))
        || values.windows(2).any(|pair| pair[0] >= pair[1])
    {
        return Err(ObjectSpecialError::InvalidPayload);
    }
    Ok(())
}

fn payload_kind(payload: &SpecialObjectPayload) -> SpecialObjectKind {
    match payload {
        SpecialObjectPayload::DrawingGallery { .. } => SpecialObjectKind::DrawingGallery,
        SpecialObjectPayload::FormObject { .. } => SpecialObjectKind::FormObject,
        SpecialObjectPayload::ParagraphBand { .. } => SpecialObjectKind::ParagraphBand,
    }
}

fn valid_token(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.' | b':'))
}

fn valid_media_type(value: &str, max_bytes: usize) -> bool {
    value.len() <= max_bytes
        && value.split_once('/').is_some_and(|(left, right)| {
            !left.is_empty()
                && !right.is_empty()
                && left
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
                && right
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'+' | b'.'))
        })
}

fn valid_text(value: &str, max_bytes: usize, allow_empty: bool) -> bool {
    (allow_empty || !value.is_empty())
        && value.len() <= max_bytes
        && !value.chars().any(|character| {
            character == '\0'
                || (character.is_control() && !matches!(character, '\n' | '\r' | '\t'))
        })
}

fn require_digest(value: &str) -> Result<(), ObjectSpecialError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(ObjectSpecialError::InvalidDigest);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &ObjectSpecialPlan,
    limits: ObjectSpecialLimits,
) -> Result<String, ObjectSpecialError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a ObjectSpecialOperation,
    }
    let binding = Binding {
        schema_version: plan.schema_version,
        capability_id: plan.capability_id,
        request_id: &plan.request_id,
        source_state_sha256: &plan.source_state_sha256,
        target_state_sha256: &plan.target_state_sha256,
        source_document_flow_sha256: &plan.source_document_flow_sha256,
        target_document_flow_sha256: &plan.target_document_flow_sha256,
        operation: &plan.operation,
    };
    Ok(hex(
        Sha256::digest(serialize_bounded(&binding, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ObjectSpecialLimits,
) -> Result<Vec<u8>, ObjectSpecialError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectSpecialError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(ObjectSpecialError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ObjectSpecialError> {
    struct DuplicateVisitor;
    impl<'de> Visitor<'de> for DuplicateVisitor {
        type Value = ();
        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }
        fn visit_bool<E>(self, _: bool) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_i64<E>(self, _: i64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_u64<E>(self, _: u64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_f64<E>(self, _: f64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_str<E>(self, _: &str) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }
        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(DuplicateSeed)?.is_some() {}
            Ok(())
        }
        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            let mut keys = BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(de::Error::custom("duplicate JSON key"));
                }
                map.next_value_seed(DuplicateSeed)?;
            }
            Ok(())
        }
    }
    struct DuplicateSeed;
    impl<'de> de::DeserializeSeed<'de> for DuplicateSeed {
        type Value = ();
        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }
    }
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    de::DeserializeSeed::deserialize(DuplicateSeed, &mut deserializer)
        .map_err(|_| ObjectSpecialError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| ObjectSpecialError::InvalidJson)
}

#[cfg(test)]
mod private_tests {
    use super::*;

    #[test]
    fn error_code_is_content_free() {
        assert_eq!(
            ObjectSpecialError::PlanTampered.code(),
            "object_special_plan_tampered"
        );
    }
}
