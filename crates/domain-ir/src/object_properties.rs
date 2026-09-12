use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const OBJECT_PROPERTIES_SCHEMA_VERSION: &str = "hwpx-agent.object-properties/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectPropertiesLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub text_bytes: usize,
    pub hyperlink_bytes: usize,
    pub opaque_entries: usize,
    pub opaque_key_bytes: usize,
    pub opaque_value_bytes: usize,
    pub extent_hwpunit: u32,
    pub image_pixels: u32,
    pub image_dpi: u32,
}

impl Default for ObjectPropertiesLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 512 * 1024,
            output_bytes: 512 * 1024,
            text_bytes: 64 * 1024,
            hyperlink_bytes: 8 * 1024,
            opaque_entries: 1_024,
            opaque_key_bytes: 512,
            opaque_value_bytes: 64 * 1024,
            extent_hwpunit: 1_000_000_000,
            image_pixels: 1_000_000,
            image_dpi: 100_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObjectPropertiesLimits(ObjectPropertiesLimitConfig);

impl ObjectPropertiesLimits {
    pub const HARD_MAX_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 16_384;
    pub const HARD_MAX_EXTENT_HWPUNIT: u32 = 2_000_000_000;
    pub const HARD_MAX_IMAGE_PIXELS: u32 = 10_000_000;
    pub const HARD_MAX_IMAGE_DPI: u32 = 1_000_000;

    /// Creates finite limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: ObjectPropertiesLimitConfig) -> Result<Self, ObjectPropertiesError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.hyperlink_bytes == 0
            || config.hyperlink_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
            || config.opaque_key_bytes == 0
            || config.opaque_key_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.opaque_value_bytes == 0
            || config.opaque_value_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.extent_hwpunit == 0
            || config.extent_hwpunit > Self::HARD_MAX_EXTENT_HWPUNIT
            || config.image_pixels == 0
            || config.image_pixels > Self::HARD_MAX_IMAGE_PIXELS
            || config.image_dpi == 0
            || config.image_dpi > Self::HARD_MAX_IMAGE_DPI
        {
            return Err(ObjectPropertiesError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ObjectPropertiesLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectPropertyKind {
    BasicShape,
    TextBox,
    Picture,
    Chart,
    DrawingCanvas,
    EmbeddedObject,
    FormObject,
    ParagraphBand,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectPropertyMargins {
    pub left_hwpunit: u32,
    pub right_hwpunit: u32,
    pub top_hwpunit: u32,
    pub bottom_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectCaptionSide {
    Left,
    Right,
    Top,
    Bottom,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectCaptionNumbering {
    None,
    Picture,
    Table,
    Equation,
    UserDefined,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectCaption {
    pub side: ObjectCaptionSide,
    pub gap_hwpunit: u32,
    pub width_hwpunit: u32,
    pub numbering: ObjectCaptionNumbering,
    pub label: String,
    pub text: String,
}

impl fmt::Debug for ObjectCaption {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectCaption")
            .field("side", &self.side)
            .field("numbering", &self.numbering)
            .field("text", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectTextBoxVerticalAlignment {
    Top,
    Center,
    Bottom,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TextBoxDirection {
    Horizontal,
    Vertical,
    VerticalRightToLeft,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TextBoxProperties {
    pub margins: ObjectPropertyMargins,
    pub vertical_alignment: ObjectTextBoxVerticalAlignment,
    pub direction: TextBoxDirection,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ImageProperties {
    pub original_width_px: u32,
    pub original_height_px: u32,
    pub horizontal_scale_millionths: u32,
    pub vertical_scale_millionths: u32,
    pub horizontal_dpi: u32,
    pub vertical_dpi: u32,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectAltText {
    pub title: String,
    pub description: String,
}

impl fmt::Debug for ObjectAltText {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ObjectAltText(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ObjectHyperlink {
    Https { uri: String },
    Mailto { address: String },
    Bookmark { name: String },
}

impl fmt::Debug for ObjectHyperlink {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let kind = match self {
            Self::Https { .. } => "https",
            Self::Mailto { .. } => "mailto",
            Self::Bookmark { .. } => "bookmark",
        };
        formatter
            .debug_struct("ObjectHyperlink")
            .field("kind", &kind)
            .field("target", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OpaqueObjectProperty {
    pub namespace: String,
    pub name: String,
    pub value: String,
}

impl fmt::Debug for OpaqueObjectProperty {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("OpaqueObjectProperty(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectPropertiesStateDraft {
    pub schema_version: String,
    pub logical_object_id: LogicalId,
    pub native_object_id: u32,
    pub native_instance_id: u32,
    pub object_kind: ObjectPropertyKind,
    pub geometry_state_sha256: String,
    pub appearance_state_sha256: String,
    pub payload_state_sha256: String,
    pub resource_inventory_sha256: String,
    pub embedded_content_state_sha256: String,
    pub outer_margins: ObjectPropertyMargins,
    pub caption: Option<ObjectCaption>,
    pub text_box: Option<TextBoxProperties>,
    pub image: Option<ImageProperties>,
    pub aspect_locked: bool,
    pub protected: bool,
    pub printable: bool,
    pub alt_text: Option<ObjectAltText>,
    pub hyperlink: Option<ObjectHyperlink>,
    pub opaque_properties: Vec<OpaqueObjectProperty>,
}

impl fmt::Debug for ObjectPropertiesStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectPropertiesStateDraft")
            .field("object_kind", &self.object_kind)
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectPropertiesState {
    schema_version: &'static str,
    logical_object_id: LogicalId,
    native_object_id: u32,
    native_instance_id: u32,
    object_kind: ObjectPropertyKind,
    geometry_state_sha256: String,
    appearance_state_sha256: String,
    payload_state_sha256: String,
    resource_inventory_sha256: String,
    embedded_content_state_sha256: String,
    outer_margins: ObjectPropertyMargins,
    caption: Option<ObjectCaption>,
    text_box: Option<TextBoxProperties>,
    image: Option<ImageProperties>,
    aspect_locked: bool,
    protected: bool,
    printable: bool,
    alt_text: Option<ObjectAltText>,
    hyperlink: Option<ObjectHyperlink>,
    opaque_properties: Vec<OpaqueObjectProperty>,
}

impl ObjectPropertiesState {
    /// Validates and seals a complete object-property state.
    ///
    /// # Errors
    ///
    /// Rejects invalid versions, identities, digests, kind-specific state, text, links or bounds.
    pub fn from_draft(
        draft: ObjectPropertiesStateDraft,
        limits: ObjectPropertiesLimits,
    ) -> Result<Self, ObjectPropertiesError> {
        if draft.schema_version != OBJECT_PROPERTIES_SCHEMA_VERSION {
            return Err(ObjectPropertiesError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION,
            logical_object_id: draft.logical_object_id,
            native_object_id: draft.native_object_id,
            native_instance_id: draft.native_instance_id,
            object_kind: draft.object_kind,
            geometry_state_sha256: draft.geometry_state_sha256,
            appearance_state_sha256: draft.appearance_state_sha256,
            payload_state_sha256: draft.payload_state_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            embedded_content_state_sha256: draft.embedded_content_state_sha256,
            outer_margins: draft.outer_margins,
            caption: draft.caption,
            text_box: draft.text_box,
            image: draft.image,
            aspect_locked: draft.aspect_locked,
            protected: draft.protected,
            printable: draft.printable,
            alt_text: draft.alt_text,
            hyperlink: draft.hyperlink,
            opaque_properties: draft.opaque_properties,
        };
        validate_state(&state, limits)?;
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub const fn object_kind(&self) -> ObjectPropertyKind {
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
    pub const fn outer_margins(&self) -> ObjectPropertyMargins {
        self.outer_margins
    }

    #[must_use]
    pub const fn caption(&self) -> Option<&ObjectCaption> {
        self.caption.as_ref()
    }

    #[must_use]
    pub const fn text_box(&self) -> Option<TextBoxProperties> {
        self.text_box
    }

    #[must_use]
    pub const fn image(&self) -> Option<ImageProperties> {
        self.image
    }

    #[must_use]
    pub const fn aspect_locked(&self) -> bool {
        self.aspect_locked
    }

    #[must_use]
    pub const fn protected(&self) -> bool {
        self.protected
    }

    #[must_use]
    pub const fn printable(&self) -> bool {
        self.printable
    }

    #[must_use]
    pub const fn alt_text(&self) -> Option<&ObjectAltText> {
        self.alt_text.as_ref()
    }

    #[must_use]
    pub const fn hyperlink(&self) -> Option<&ObjectHyperlink> {
        self.hyperlink.as_ref()
    }

    /// Serializes the complete state deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ObjectPropertiesLimits,
    ) -> Result<Vec<u8>, ObjectPropertiesError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_sha256(
        &self,
        limits: ObjectPropertiesLimits,
    ) -> Result<String, ObjectPropertiesError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for ObjectPropertiesState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectPropertiesState")
            .field("object_kind", &self.object_kind)
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ObjectPropertiesOperation {
    SetMarginCaption {
        outer_margins: ObjectPropertyMargins,
        caption: Option<ObjectCaption>,
    },
    SetTextBoxProperties {
        properties: TextBoxProperties,
    },
    SetImageProperties {
        properties: ImageProperties,
    },
    SetAspectLock {
        enabled: bool,
    },
    SetObjectProtect {
        enabled: bool,
    },
    SetPrintable {
        enabled: bool,
    },
    SetAltText {
        value: Option<ObjectAltText>,
    },
    SetObjectHyperlink {
        value: Option<ObjectHyperlink>,
    },
}

impl ObjectPropertiesOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::SetMarginCaption { .. } => "obj.margin_caption",
            Self::SetTextBoxProperties { .. } => "obj.textbox_properties",
            Self::SetImageProperties { .. } => "obj.image_properties",
            Self::SetAspectLock { .. } => "obj.aspect_lock",
            Self::SetObjectProtect { .. } => "obj.object_protect",
            Self::SetPrintable { .. } => "obj.printable",
            Self::SetAltText { .. } => "obj.alt_text",
            Self::SetObjectHyperlink { .. } => "obj.object_hyperlink",
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectPropertiesRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: ObjectPropertiesOperation,
}

impl fmt::Debug for ObjectPropertiesRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectPropertiesRequestDraft")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectPropertiesRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ObjectPropertiesOperation,
}

impl ObjectPropertiesRequest {
    /// Validates one exact property transition against current state and document flow.
    ///
    /// # Errors
    ///
    /// Rejects version, digest, state, flow, family, value, no-op or output drift.
    pub fn from_draft(
        draft: ObjectPropertiesRequestDraft,
        current: &ObjectPropertiesState,
        current_document_flow_sha256: &str,
        limits: ObjectPropertiesLimits,
    ) -> Result<Self, ObjectPropertiesError> {
        if draft.schema_version != OBJECT_PROPERTIES_SCHEMA_VERSION {
            return Err(ObjectPropertiesError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if current.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(ObjectPropertiesError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(ObjectPropertiesError::DocumentFlowDrift);
        }
        let _ = apply_operation(current, &draft.operation, limits)?;
        let request = Self {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION,
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
        current: &ObjectPropertiesState,
        current_document_flow_sha256: &str,
        limits: ObjectPropertiesLimits,
    ) -> Result<Self, ObjectPropertiesError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(ObjectPropertiesError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| ObjectPropertiesError::InvalidJson)?;
        Self::from_draft(draft, current, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn operation(&self) -> &ObjectPropertiesOperation {
        &self.operation
    }

    /// Serializes the complete request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ObjectPropertiesLimits,
    ) -> Result<Vec<u8>, ObjectPropertiesError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for ObjectPropertiesRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectPropertiesRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectPropertiesPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state: ObjectPropertiesState,
    source_state_sha256: String,
    target_state: ObjectPropertiesState,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ObjectPropertiesOperation,
    plan_sha256: String,
}

impl ObjectPropertiesPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn source_state(&self) -> &ObjectPropertiesState {
        &self.source_state
    }

    #[must_use]
    pub const fn target_state(&self) -> &ObjectPropertiesState {
        &self.target_state
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
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }
}

impl fmt::Debug for ObjectPropertiesPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectPropertiesPlan")
            .field("capability_id", &self.capability_id)
            .field("identity", &"<redacted>")
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct ObjectPropertiesBuilder;

impl ObjectPropertiesBuilder {
    /// Creates a deterministic plan after rechecking exact state and flow.
    ///
    /// # Errors
    ///
    /// Rejects request, source-state, document-flow, target-state or output drift.
    pub fn plan(
        current: &ObjectPropertiesState,
        request: &ObjectPropertiesRequest,
        current_document_flow_sha256: &str,
        limits: ObjectPropertiesLimits,
    ) -> Result<ObjectPropertiesPlan, ObjectPropertiesError> {
        require_digest(current_document_flow_sha256)?;
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(ObjectPropertiesError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(ObjectPropertiesError::DocumentFlowDrift);
        }
        let target_state = apply_operation(current, &request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = ObjectPropertiesPlan {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION,
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

    /// Revalidates the sealed plan, exact current state and flow before publishing a target.
    ///
    /// # Errors
    ///
    /// Rejects plan tampering, source-state drift and document-flow drift.
    pub fn build(
        plan: &ObjectPropertiesPlan,
        current: &ObjectPropertiesState,
        current_document_flow_sha256: &str,
        limits: ObjectPropertiesLimits,
    ) -> Result<ObjectPropertiesResult, ObjectPropertiesError> {
        require_digest(current_document_flow_sha256)?;
        if plan.schema_version != OBJECT_PROPERTIES_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan_binding_sha256(plan, limits)? != plan.plan_sha256
            || plan.source_state.canonical_sha256(limits)? != plan.source_state_sha256
            || plan.target_state.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(ObjectPropertiesError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(ObjectPropertiesError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(ObjectPropertiesError::DocumentFlowDrift);
        }
        let recomputed = apply_operation(&plan.source_state, &plan.operation, limits)?;
        if recomputed != plan.target_state {
            return Err(ObjectPropertiesError::PlanTampered);
        }
        let receipt = ObjectPropertiesReceipt {
            schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION,
            capability_id: plan.capability_id,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: plan.target_state_sha256.clone(),
            source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
            target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
            plan_sha256: plan.plan_sha256.clone(),
        };
        let _ = serialize_bounded(&receipt, limits)?;
        Ok(ObjectPropertiesResult {
            state: plan.target_state.clone(),
            receipt,
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ObjectPropertiesReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for ObjectPropertiesReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectPropertiesReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ObjectPropertiesResult {
    pub state: ObjectPropertiesState,
    pub receipt: ObjectPropertiesReceipt,
}

impl fmt::Debug for ObjectPropertiesResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ObjectPropertiesResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum ObjectPropertiesError {
    #[error("object property limits are invalid")]
    InvalidLimit,
    #[error("object property input exceeds a finite limit")]
    InputLimit,
    #[error("object property JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("object property schema version is unsupported")]
    UnsupportedVersion,
    #[error("object property identity is invalid")]
    InvalidIdentity,
    #[error("object property digest is invalid")]
    InvalidDigest,
    #[error("object property state is invalid for its object kind")]
    KindMismatch,
    #[error("object property value is invalid")]
    InvalidValue,
    #[error("object hyperlink target is invalid or unsafe")]
    InvalidHyperlink,
    #[error("object property opaque state is invalid")]
    InvalidOpaqueState,
    #[error("object property operation is a no-op")]
    Noop,
    #[error("object property source state drifted")]
    SourceStateDrift,
    #[error("object property document flow drifted")]
    DocumentFlowDrift,
    #[error("object property plan was tampered with")]
    PlanTampered,
    #[error("object property serialization failed")]
    Serialization,
    #[error("object property serialized output exceeds a finite limit")]
    OutputLimit,
}

impl ObjectPropertiesError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "object_properties_invalid_limit",
            Self::InputLimit => "object_properties_input_limit",
            Self::InvalidJson => "object_properties_invalid_json",
            Self::UnsupportedVersion => "object_properties_unsupported_version",
            Self::InvalidIdentity => "object_properties_invalid_identity",
            Self::InvalidDigest => "object_properties_invalid_digest",
            Self::KindMismatch => "object_properties_kind_mismatch",
            Self::InvalidValue => "object_properties_invalid_value",
            Self::InvalidHyperlink => "object_properties_invalid_hyperlink",
            Self::InvalidOpaqueState => "object_properties_invalid_opaque_state",
            Self::Noop => "object_properties_noop",
            Self::SourceStateDrift => "object_properties_source_state_drift",
            Self::DocumentFlowDrift => "object_properties_document_flow_drift",
            Self::PlanTampered => "object_properties_plan_tampered",
            Self::Serialization => "object_properties_serialization",
            Self::OutputLimit => "object_properties_output_limit",
        }
    }
}

fn apply_operation(
    source: &ObjectPropertiesState,
    operation: &ObjectPropertiesOperation,
    limits: ObjectPropertiesLimits,
) -> Result<ObjectPropertiesState, ObjectPropertiesError> {
    validate_state(source, limits)?;
    let mut target = source.clone();
    match operation {
        ObjectPropertiesOperation::SetMarginCaption {
            outer_margins,
            caption,
        } => {
            target.outer_margins = *outer_margins;
            target.caption.clone_from(caption);
        }
        ObjectPropertiesOperation::SetTextBoxProperties { properties } => {
            if source.object_kind != ObjectPropertyKind::TextBox {
                return Err(ObjectPropertiesError::KindMismatch);
            }
            target.text_box = Some(*properties);
        }
        ObjectPropertiesOperation::SetImageProperties { properties } => {
            if source.object_kind != ObjectPropertyKind::Picture {
                return Err(ObjectPropertiesError::KindMismatch);
            }
            target.image = Some(*properties);
        }
        ObjectPropertiesOperation::SetAspectLock { enabled } => {
            target.aspect_locked = *enabled;
        }
        ObjectPropertiesOperation::SetObjectProtect { enabled } => {
            target.protected = *enabled;
        }
        ObjectPropertiesOperation::SetPrintable { enabled } => target.printable = *enabled,
        ObjectPropertiesOperation::SetAltText { value } => target.alt_text.clone_from(value),
        ObjectPropertiesOperation::SetObjectHyperlink { value } => {
            target.hyperlink.clone_from(value);
        }
    }
    validate_state(&target, limits)?;
    if &target == source {
        return Err(ObjectPropertiesError::Noop);
    }
    Ok(target)
}

fn validate_state(
    state: &ObjectPropertiesState,
    limits: ObjectPropertiesLimits,
) -> Result<(), ObjectPropertiesError> {
    if state.schema_version != OBJECT_PROPERTIES_SCHEMA_VERSION
        || state.native_object_id == 0
        || state.native_instance_id == 0
    {
        return Err(ObjectPropertiesError::InvalidIdentity);
    }
    for digest in [
        &state.geometry_state_sha256,
        &state.appearance_state_sha256,
        &state.payload_state_sha256,
        &state.resource_inventory_sha256,
        &state.embedded_content_state_sha256,
    ] {
        require_digest(digest)?;
    }
    validate_margins(state.outer_margins, limits)?;
    if let Some(caption) = &state.caption
        && (caption.width_hwpunit == 0
            || caption.width_hwpunit > limits.0.extent_hwpunit
            || caption.gap_hwpunit > limits.0.extent_hwpunit
            || !valid_text(&caption.label, limits.0.text_bytes, false)
            || !valid_text(&caption.text, limits.0.text_bytes, true))
    {
        return Err(ObjectPropertiesError::InvalidValue);
    }
    match (state.object_kind, state.text_box, state.image) {
        (ObjectPropertyKind::TextBox, Some(properties), None) => {
            validate_margins(properties.margins, limits)?;
        }
        (ObjectPropertyKind::Picture, None, Some(properties)) => {
            validate_image(properties, limits)?;
        }
        (ObjectPropertyKind::TextBox | ObjectPropertyKind::Picture, _, _)
        | (_, Some(_), _)
        | (_, _, Some(_)) => return Err(ObjectPropertiesError::KindMismatch),
        _ => {}
    }
    if let Some(alt_text) = &state.alt_text
        && (!valid_text(&alt_text.title, limits.0.text_bytes, true)
            || !valid_text(&alt_text.description, limits.0.text_bytes, true))
    {
        return Err(ObjectPropertiesError::InvalidValue);
    }
    if let Some(hyperlink) = &state.hyperlink {
        validate_hyperlink(hyperlink, limits)?;
    }
    if state.opaque_properties.len() > limits.0.opaque_entries {
        return Err(ObjectPropertiesError::InvalidOpaqueState);
    }
    let mut keys = BTreeSet::new();
    for property in &state.opaque_properties {
        if !valid_token(&property.namespace, limits.0.opaque_key_bytes)
            || !valid_token(&property.name, limits.0.opaque_key_bytes)
            || !valid_text(&property.value, limits.0.opaque_value_bytes, true)
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(ObjectPropertiesError::InvalidOpaqueState);
        }
    }
    Ok(())
}

fn validate_margins(
    margins: ObjectPropertyMargins,
    limits: ObjectPropertiesLimits,
) -> Result<(), ObjectPropertiesError> {
    if [
        margins.left_hwpunit,
        margins.right_hwpunit,
        margins.top_hwpunit,
        margins.bottom_hwpunit,
    ]
    .into_iter()
    .any(|value| value > limits.0.extent_hwpunit)
    {
        return Err(ObjectPropertiesError::InvalidValue);
    }
    Ok(())
}

fn validate_image(
    image: ImageProperties,
    limits: ObjectPropertiesLimits,
) -> Result<(), ObjectPropertiesError> {
    if image.original_width_px == 0
        || image.original_height_px == 0
        || image.original_width_px > limits.0.image_pixels
        || image.original_height_px > limits.0.image_pixels
        || image.horizontal_scale_millionths == 0
        || image.vertical_scale_millionths == 0
        || image.horizontal_scale_millionths > 100_000_000
        || image.vertical_scale_millionths > 100_000_000
        || image.horizontal_dpi == 0
        || image.vertical_dpi == 0
        || image.horizontal_dpi > limits.0.image_dpi
        || image.vertical_dpi > limits.0.image_dpi
    {
        return Err(ObjectPropertiesError::InvalidValue);
    }
    Ok(())
}

fn validate_hyperlink(
    hyperlink: &ObjectHyperlink,
    limits: ObjectPropertiesLimits,
) -> Result<(), ObjectPropertiesError> {
    let valid = match hyperlink {
        ObjectHyperlink::Https { uri } => {
            uri.starts_with("https://")
                && !uri[8..].is_empty()
                && valid_link_text(uri, limits.0.hyperlink_bytes)
                && !uri.contains('#')
        }
        ObjectHyperlink::Mailto { address } => {
            valid_link_text(address, limits.0.hyperlink_bytes)
                && address.matches('@').count() == 1
                && !address.starts_with('@')
                && !address.ends_with('@')
                && !address.contains(':')
        }
        ObjectHyperlink::Bookmark { name } => valid_token(name, limits.0.hyperlink_bytes),
    };
    if !valid {
        return Err(ObjectPropertiesError::InvalidHyperlink);
    }
    Ok(())
}

fn valid_token(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
}

fn valid_text(value: &str, max_bytes: usize, allow_empty: bool) -> bool {
    (allow_empty || !value.is_empty())
        && value.len() <= max_bytes
        && !value.chars().any(|character| {
            character == '\0'
                || (character.is_control() && !matches!(character, '\n' | '\r' | '\t'))
        })
}

fn valid_link_text(value: &str, max_bytes: usize) -> bool {
    valid_text(value, max_bytes, false)
        && !value.chars().any(char::is_whitespace)
        && !value.contains('\\')
}

fn require_digest(value: &str) -> Result<(), ObjectPropertiesError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(ObjectPropertiesError::InvalidDigest);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &ObjectPropertiesPlan,
    limits: ObjectPropertiesLimits,
) -> Result<String, ObjectPropertiesError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a ObjectPropertiesOperation,
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
    limits: ObjectPropertiesLimits,
) -> Result<Vec<u8>, ObjectPropertiesError> {
    let bytes = serde_json::to_vec(value).map_err(|_| ObjectPropertiesError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(ObjectPropertiesError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ObjectPropertiesError> {
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
        .map_err(|_| ObjectPropertiesError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| ObjectPropertiesError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Test setup uses expectations only to isolate private-plan tampering.
mod private_tests {
    use super::*;

    const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> ObjectPropertiesLimits {
        ObjectPropertiesLimits::new(ObjectPropertiesLimitConfig::default()).expect("limits")
    }

    fn state() -> ObjectPropertiesState {
        ObjectPropertiesState::from_draft(
            ObjectPropertiesStateDraft {
                schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
                logical_object_id: LogicalId::parse("shape-1").expect("id"),
                native_object_id: 1,
                native_instance_id: 2,
                object_kind: ObjectPropertyKind::BasicShape,
                geometry_state_sha256: FLOW_A.to_owned(),
                appearance_state_sha256: FLOW_A.to_owned(),
                payload_state_sha256: FLOW_A.to_owned(),
                resource_inventory_sha256: FLOW_A.to_owned(),
                embedded_content_state_sha256: FLOW_A.to_owned(),
                outer_margins: ObjectPropertyMargins {
                    left_hwpunit: 1,
                    right_hwpunit: 2,
                    top_hwpunit: 3,
                    bottom_hwpunit: 4,
                },
                caption: None,
                text_box: None,
                image: None,
                aspect_locked: false,
                protected: false,
                printable: true,
                alt_text: None,
                hyperlink: None,
                opaque_properties: Vec::new(),
            },
            limits(),
        )
        .expect("state")
    }

    #[test]
    fn private_plan_tampering_is_rejected() {
        let state = state();
        let request = ObjectPropertiesRequest::from_draft(
            ObjectPropertiesRequestDraft {
                schema_version: OBJECT_PROPERTIES_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: state.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: FLOW_A.to_owned(),
                target_document_flow_sha256: FLOW_A.to_owned(),
                operation: ObjectPropertiesOperation::SetAspectLock { enabled: true },
            },
            &state,
            FLOW_A,
            limits(),
        )
        .expect("request");
        let mut plan =
            ObjectPropertiesBuilder::plan(&state, &request, FLOW_A, limits()).expect("plan");
        plan.target_state.protected = true;
        assert_eq!(
            ObjectPropertiesBuilder::build(&plan, &state, FLOW_A, limits()),
            Err(ObjectPropertiesError::PlanTampered)
        );
    }
}
