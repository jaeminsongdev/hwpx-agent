use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const COMMENT_MODEL_SCHEMA_VERSION: &str = "hwpx-agent.comment-model/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CommentLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub sections: usize,
    pub authors: usize,
    pub styles: usize,
    pub hidden_explanations: usize,
    pub comments: usize,
    pub text_bytes: usize,
    pub opaque_entries: usize,
}

impl Default for CommentLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            sections: 4096,
            authors: 65_536,
            styles: 65_536,
            hidden_explanations: 65_536,
            comments: 1_000_000,
            text_bytes: 64 * 1024,
            opaque_entries: 4096,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CommentLimits(CommentLimitConfig);

impl CommentLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 65_536;

    /// Creates finite comment-model limits without silently clamping values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: CommentLimitConfig) -> Result<Self, CommentError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.sections == 0
            || config.sections > Self::HARD_MAX_ITEMS
            || config.authors == 0
            || config.authors > Self::HARD_MAX_ITEMS
            || config.styles == 0
            || config.styles > Self::HARD_MAX_ITEMS
            || config.hidden_explanations == 0
            || config.hidden_explanations > Self::HARD_MAX_ITEMS
            || config.comments == 0
            || config.comments > Self::HARD_MAX_ITEMS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
        {
            return Err(CommentError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> CommentLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HiddenExplanationNativeTag {
    HiddenComment,
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HiddenExplanationIdentity {
    pub logical_explanation_id: LogicalId,
}

impl fmt::Debug for HiddenExplanationIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("HiddenExplanationIdentity(<redacted>)")
    }
}

#[derive(Clone, Copy, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentPoint {
    pub paragraph_ordinal: u32,
    pub run_ordinal: u32,
    pub inline_ordinal: u32,
}

impl fmt::Debug for CommentPoint {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CommentPoint(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentAnchor {
    pub section_id: LogicalId,
    pub start: CommentPoint,
    pub end: CommentPoint,
}

impl fmt::Debug for CommentAnchor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CommentAnchor(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OpaqueCommentProperty {
    pub namespace: String,
    pub name: String,
    pub value_sha256: String,
}

impl fmt::Debug for OpaqueCommentProperty {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("OpaqueCommentProperty(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HiddenExplanationEntry {
    pub identity: HiddenExplanationIdentity,
    pub anchor: CommentAnchor,
    pub native_tag: HiddenExplanationNativeTag,
    pub enabled: bool,
    pub body_graph_sha256: String,
    pub plain_text_sha256: Option<String>,
    pub sub_list_sha256: String,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueCommentProperty>,
    pub locked: bool,
}

impl fmt::Debug for HiddenExplanationEntry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HiddenExplanationEntry")
            .field("enabled", &self.enabled)
            .field("locked", &self.locked)
            .field("payload", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentAuthor {
    pub author_id: u32,
    pub name_sha256: String,
    pub email_sha256: Option<String>,
    pub opaque_author_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for CommentAuthor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentAuthor")
            .field("locked", &self.locked)
            .field("author", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommentLineType {
    None,
    Solid,
    Dot,
    Dash,
    DashDot,
    DashDotDot,
    LongDash,
    Circle,
    DoubleSlim,
    SlimThick,
    ThickSlim,
    SlimThickSlim,
    Wave,
    DoubleWave,
    Thick3d,
    ThickReverse3d,
    ThreeDimensional,
    Reverse3d,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommentLineWidth {
    Mm0_1,
    Mm0_12,
    Mm0_15,
    Mm0_2,
    Mm0_25,
    Mm0_3,
    Mm0_4,
    Mm0_5,
    Mm0_6,
    Mm0_7,
    Mm1_0,
    Mm1_5,
    Mm2_0,
    Mm3_0,
    Mm4_0,
    Mm5_0,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommentMemoType {
    Normal,
    UserInsert,
    UserDelete,
    UserUpdate,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentStyle {
    pub style_id: u32,
    pub width_native_units: u32,
    pub line_width: CommentLineWidth,
    pub line_type: CommentLineType,
    pub line_color_rgb: u32,
    pub fill_color_rgb: u32,
    pub active_color_rgb: u32,
    pub memo_type: CommentMemoType,
    pub opaque_style_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for CommentStyle {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentStyle")
            .field("memo_type", &self.memo_type)
            .field("locked", &self.locked)
            .field("style", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommentNativeBeginTag {
    FieldBegin,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommentNativeEndTag {
    FieldEnd,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommentFieldType {
    Memo,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommentSemanticBinding {
    UnverifiedMemoParameters,
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentIdentity {
    pub logical_comment_id: LogicalId,
    pub begin_control_id: u32,
    pub field_id: u32,
}

impl fmt::Debug for CommentIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CommentIdentity(<redacted>)")
    }
}

#[derive(Clone, Copy, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentTimestamp {
    pub epoch_millis: u64,
    pub original_utc_offset_minutes: i16,
}

impl fmt::Debug for CommentTimestamp {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CommentTimestamp(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CommentVisibility {
    Shown,
    Hidden,
}

#[derive(Clone, Copy, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentResolution {
    pub resolved: bool,
    pub resolver_author_id: Option<u32>,
    pub resolved_at: Option<CommentTimestamp>,
}

impl fmt::Debug for CommentResolution {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentResolution")
            .field("resolved", &self.resolved)
            .field("metadata", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentEntry {
    pub identity: CommentIdentity,
    pub anchor: CommentAnchor,
    pub native_begin_tag: CommentNativeBeginTag,
    pub native_end_tag: CommentNativeEndTag,
    pub native_field_type: CommentFieldType,
    pub semantic_binding: CommentSemanticBinding,
    pub name_sha256: Option<String>,
    pub editable: bool,
    pub dirty: bool,
    pub z_order: i32,
    pub author_id: u32,
    pub created_at: CommentTimestamp,
    pub modified_at: Option<CommentTimestamp>,
    pub body_graph_sha256: String,
    pub plain_text_sha256: Option<String>,
    pub parameters_sha256: String,
    pub sub_list_sha256: String,
    pub style_id: u32,
    pub visibility: CommentVisibility,
    pub resolution: CommentResolution,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueCommentProperty>,
    pub locked: bool,
}

impl fmt::Debug for CommentEntry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentEntry")
            .field("visibility", &self.visibility)
            .field("resolved", &self.resolution.resolved)
            .field("locked", &self.locked)
            .field("payload", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentSectionState {
    pub section_id: LogicalId,
    pub memo_shape_id_ref: u32,
    pub opaque_section_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for CommentSectionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentSectionState")
            .field("locked", &self.locked)
            .field("section", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentDocumentStateDraft {
    pub schema_version: String,
    pub sections: Vec<CommentSectionState>,
    pub authors: Vec<CommentAuthor>,
    pub styles: Vec<CommentStyle>,
    pub hidden_explanations: Vec<HiddenExplanationEntry>,
    pub comments: Vec<CommentEntry>,
    pub non_comment_content_sha256: String,
    pub field_inventory_sha256: String,
    pub style_catalog_sha256: String,
    pub reference_inventory_sha256: String,
    pub resource_inventory_sha256: String,
    pub document_protection_sha256: String,
    pub opaque_document_state_sha256: String,
    pub document_locked: bool,
}

impl fmt::Debug for CommentDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CommentDocumentStateDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CommentDocumentState {
    schema_version: &'static str,
    sections: Vec<CommentSectionState>,
    authors: Vec<CommentAuthor>,
    styles: Vec<CommentStyle>,
    hidden_explanations: Vec<HiddenExplanationEntry>,
    comments: Vec<CommentEntry>,
    non_comment_content_sha256: String,
    field_inventory_sha256: String,
    style_catalog_sha256: String,
    reference_inventory_sha256: String,
    resource_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
    document_locked: bool,
}

impl CommentDocumentState {
    /// Validates and seals the complete ordered comment state.
    ///
    /// # Errors
    ///
    /// Rejects version, identity, native-shape, style, author/time, protection, digest, or limit failures.
    pub fn from_draft(
        draft: CommentDocumentStateDraft,
        limits: CommentLimits,
    ) -> Result<Self, CommentError> {
        if draft.schema_version != COMMENT_MODEL_SCHEMA_VERSION {
            return Err(CommentError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: COMMENT_MODEL_SCHEMA_VERSION,
            sections: draft.sections,
            authors: draft.authors,
            styles: draft.styles,
            hidden_explanations: draft.hidden_explanations,
            comments: draft.comments,
            non_comment_content_sha256: draft.non_comment_content_sha256,
            field_inventory_sha256: draft.field_inventory_sha256,
            style_catalog_sha256: draft.style_catalog_sha256,
            reference_inventory_sha256: draft.reference_inventory_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            document_protection_sha256: draft.document_protection_sha256,
            opaque_document_state_sha256: draft.opaque_document_state_sha256,
            document_locked: draft.document_locked,
        };
        validate_document_state(&state, limits)?;
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub fn sections(&self) -> &[CommentSectionState] {
        &self.sections
    }

    #[must_use]
    pub fn authors(&self) -> &[CommentAuthor] {
        &self.authors
    }

    #[must_use]
    pub fn styles(&self) -> &[CommentStyle] {
        &self.styles
    }

    #[must_use]
    pub fn hidden_explanations(&self) -> &[HiddenExplanationEntry] {
        &self.hidden_explanations
    }

    #[must_use]
    pub fn comments(&self) -> &[CommentEntry] {
        &self.comments
    }

    /// Serializes the complete state deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: CommentLimits) -> Result<Vec<u8>, CommentError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical comment state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_sha256(&self, limits: CommentLimits) -> Result<String, CommentError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for CommentDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentDocumentState")
            .field("section_count", &self.sections.len())
            .field("author_count", &self.authors.len())
            .field("style_count", &self.styles.len())
            .field("hidden_explanation_count", &self.hidden_explanations.len())
            .field("comment_count", &self.comments.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum CommentOperation {
    SetHiddenExplanation {
        target: HiddenExplanationIdentity,
        enabled: bool,
    },
    InsertComment {
        insertion_index: usize,
        comment: Box<CommentEntry>,
    },
    ReplaceStyle {
        style_id: u32,
        style: CommentStyle,
    },
    SetVisibility {
        target: CommentIdentity,
        visibility: CommentVisibility,
    },
    SetResolution {
        target: CommentIdentity,
        resolution: CommentResolution,
    },
}

impl CommentOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::SetHiddenExplanation { .. } => "ref.hidden_explanation",
            Self::InsertComment { .. } => "ref.comment_insert",
            Self::ReplaceStyle { .. } => "ref.comment_style",
            Self::SetVisibility { .. } => "ref.comment_show_hide",
            Self::SetResolution { .. } => "ref.comment_resolve",
        }
    }
}

impl fmt::Debug for CommentOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CommentRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: CommentOperation,
}

impl fmt::Debug for CommentRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CommentRequestDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CommentRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: CommentOperation,
}

impl CommentRequest {
    /// Validates an exact comment transition against current state and document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, state, flow, operation, protection, reference, or limit failures.
    pub fn from_draft(
        draft: CommentRequestDraft,
        current: &CommentDocumentState,
        current_document_flow_sha256: &str,
        limits: CommentLimits,
    ) -> Result<Self, CommentError> {
        if draft.schema_version != COMMENT_MODEL_SCHEMA_VERSION {
            return Err(CommentError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if current.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(CommentError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(CommentError::DocumentFlowDrift);
        }
        let _ = apply_operation(current, &draft.operation, limits)?;
        let request = Self {
            schema_version: COMMENT_MODEL_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict, bounded, duplicate-key-free request JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicated, unknown, oversized, stale, or invalid input.
    pub fn from_json(
        bytes: &[u8],
        current: &CommentDocumentState,
        current_document_flow_sha256: &str,
        limits: CommentLimits,
    ) -> Result<Self, CommentError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(CommentError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| CommentError::InvalidJson)?;
        Self::from_draft(draft, current, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub fn operation(&self) -> &CommentOperation {
        &self.operation
    }

    /// Serializes the request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: CommentLimits) -> Result<Vec<u8>, CommentError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for CommentRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CommentPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state: CommentDocumentState,
    source_state_sha256: String,
    target_state: CommentDocumentState,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: CommentOperation,
    plan_sha256: String,
}

impl CommentPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn target_state(&self) -> &CommentDocumentState {
        &self.target_state
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the sealed plan deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: CommentLimits) -> Result<Vec<u8>, CommentError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for CommentPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentPlan")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct CommentBuilder;

impl CommentBuilder {
    /// Builds and seals an immutable plan from current state and a validated request.
    ///
    /// # Errors
    ///
    /// Rejects state, flow, operation, protection, reference, or output drift.
    pub fn plan(
        current: &CommentDocumentState,
        request: &CommentRequest,
        current_document_flow_sha256: &str,
        limits: CommentLimits,
    ) -> Result<CommentPlan, CommentError> {
        require_digest(current_document_flow_sha256)?;
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(CommentError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(CommentError::DocumentFlowDrift);
        }
        let target_state = apply_operation(current, &request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = CommentPlan {
            schema_version: COMMENT_MODEL_SCHEMA_VERSION,
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
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }

    /// Revalidates a sealed plan against current state and flow before returning a result.
    ///
    /// # Errors
    ///
    /// Rejects state, flow, plan binding, operation, protection, reference, or output drift.
    pub fn build(
        plan: &CommentPlan,
        current: &CommentDocumentState,
        current_document_flow_sha256: &str,
        limits: CommentLimits,
    ) -> Result<CommentResult, CommentError> {
        validate_document_state(current, limits)?;
        if plan.schema_version != COMMENT_MODEL_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan.plan_sha256 != plan_binding_sha256(plan, limits)?
        {
            return Err(CommentError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256
            || current != &plan.source_state
        {
            return Err(CommentError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(CommentError::DocumentFlowDrift);
        }
        let recomputed = apply_operation(&plan.source_state, &plan.operation, limits)?;
        if recomputed != plan.target_state
            || recomputed.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(CommentError::PlanTampered);
        }
        let receipt = CommentReceipt {
            schema_version: COMMENT_MODEL_SCHEMA_VERSION,
            capability_id: plan.capability_id,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: plan.target_state_sha256.clone(),
            source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
            target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
            plan_sha256: plan.plan_sha256.clone(),
        };
        let _ = serialize_bounded(&receipt, limits)?;
        Ok(CommentResult {
            state: plan.target_state.clone(),
            receipt,
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CommentReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for CommentReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CommentResult {
    pub state: CommentDocumentState,
    pub receipt: CommentReceipt,
}

impl fmt::Debug for CommentResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CommentResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum CommentError {
    #[error("comment-model limits are invalid")]
    InvalidLimit,
    #[error("comment-model input exceeds a finite limit")]
    InputLimit,
    #[error("comment-model JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("comment-model schema version is unsupported")]
    UnsupportedVersion,
    #[error("comment, hidden-explanation, section, or native identity is invalid")]
    InvalidIdentity,
    #[error("comment anchor is invalid")]
    InvalidAnchor,
    #[error("comment author or timestamp is invalid")]
    InvalidAuthorTime,
    #[error("comment style is invalid")]
    InvalidStyle,
    #[error("comment native binding is unsupported or inconsistent")]
    InvalidNativeBinding,
    #[error("comment digest or opaque property is invalid")]
    InvalidPayload,
    #[error("comment insertion index is invalid")]
    InvalidInsertionIndex,
    #[error("comment target does not exist or is ambiguous")]
    TargetNotFound,
    #[error("comment, explanation, style, section, author, or document is protected")]
    Protected,
    #[error("comment operation is a no-op")]
    Noop,
    #[error("comment source state drifted")]
    SourceStateDrift,
    #[error("comment document flow drifted")]
    DocumentFlowDrift,
    #[error("comment plan was tampered with")]
    PlanTampered,
    #[error("comment serialization failed")]
    Serialization,
    #[error("comment serialized output exceeds a finite limit")]
    OutputLimit,
}

impl CommentError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "comment_invalid_limit",
            Self::InputLimit => "comment_input_limit",
            Self::InvalidJson => "comment_invalid_json",
            Self::UnsupportedVersion => "comment_unsupported_version",
            Self::InvalidIdentity => "comment_invalid_identity",
            Self::InvalidAnchor => "comment_invalid_anchor",
            Self::InvalidAuthorTime => "comment_invalid_author_time",
            Self::InvalidStyle => "comment_invalid_style",
            Self::InvalidNativeBinding => "comment_invalid_native_binding",
            Self::InvalidPayload => "comment_invalid_payload",
            Self::InvalidInsertionIndex => "comment_invalid_insertion_index",
            Self::TargetNotFound => "comment_target_not_found",
            Self::Protected => "comment_protected",
            Self::Noop => "comment_noop",
            Self::SourceStateDrift => "comment_source_state_drift",
            Self::DocumentFlowDrift => "comment_document_flow_drift",
            Self::PlanTampered => "comment_plan_tampered",
            Self::Serialization => "comment_serialization",
            Self::OutputLimit => "comment_output_limit",
        }
    }
}

fn apply_operation(
    source: &CommentDocumentState,
    operation: &CommentOperation,
    limits: CommentLimits,
) -> Result<CommentDocumentState, CommentError> {
    validate_document_state(source, limits)?;
    if source.document_locked {
        return Err(CommentError::Protected);
    }
    let mut target = source.clone();
    match operation {
        CommentOperation::SetHiddenExplanation {
            target: identity,
            enabled,
        } => apply_hidden_explanation(&mut target, identity, *enabled)?,
        CommentOperation::InsertComment {
            insertion_index,
            comment,
        } => apply_insert(&mut target, *insertion_index, comment, limits)?,
        CommentOperation::ReplaceStyle { style_id, style } => {
            apply_style(&mut target, *style_id, style)?;
        }
        CommentOperation::SetVisibility {
            target: identity,
            visibility,
        } => apply_visibility(&mut target, identity, *visibility)?,
        CommentOperation::SetResolution {
            target: identity,
            resolution,
        } => apply_resolution(&mut target, identity, *resolution)?,
    }
    validate_document_state(&target, limits)?;
    if &target == source {
        return Err(CommentError::Noop);
    }
    Ok(target)
}

fn apply_hidden_explanation(
    target: &mut CommentDocumentState,
    identity: &HiddenExplanationIdentity,
    enabled: bool,
) -> Result<(), CommentError> {
    let index = exact_explanation_index(&target.hidden_explanations, identity)?;
    let section_index = exact_section_index(
        &target.sections,
        &target.hidden_explanations[index].anchor.section_id,
    )?;
    if target.hidden_explanations[index].locked || target.sections[section_index].locked {
        return Err(CommentError::Protected);
    }
    if target.hidden_explanations[index].enabled == enabled {
        return Err(CommentError::Noop);
    }
    target.hidden_explanations[index].enabled = enabled;
    Ok(())
}

fn apply_insert(
    target: &mut CommentDocumentState,
    insertion_index: usize,
    comment: &CommentEntry,
    limits: CommentLimits,
) -> Result<(), CommentError> {
    if insertion_index > target.comments.len() {
        return Err(CommentError::InvalidInsertionIndex);
    }
    validate_comment(
        comment,
        |id| target.authors.iter().any(|author| author.author_id == id),
        |id| target.styles.iter().any(|style| style.style_id == id),
        limits,
    )?;
    let section_index = exact_section_index(&target.sections, &comment.anchor.section_id)?;
    if target.sections[section_index].locked {
        return Err(CommentError::Protected);
    }
    if comment.visibility != CommentVisibility::Shown || comment.resolution.resolved {
        return Err(CommentError::InvalidNativeBinding);
    }
    if target.comments.iter().any(|existing| {
        existing.identity.logical_comment_id == comment.identity.logical_comment_id
            || existing.identity.begin_control_id == comment.identity.begin_control_id
            || existing.identity.field_id == comment.identity.field_id
    }) {
        return Err(CommentError::InvalidIdentity);
    }
    target.comments.insert(insertion_index, comment.clone());
    Ok(())
}

fn apply_style(
    target: &mut CommentDocumentState,
    style_id: u32,
    style: &CommentStyle,
) -> Result<(), CommentError> {
    let index = exact_style_index(&target.styles, style_id)?;
    validate_style(style)?;
    if style.style_id != style_id {
        return Err(CommentError::InvalidStyle);
    }
    // A comment can reference a different style from its section's default.
    // Check its actual anchor section too, without a section scan per comment.
    let locked_sections: BTreeSet<_> = target
        .sections
        .iter()
        .filter(|section| section.locked)
        .map(|section| &section.section_id)
        .collect();
    if target.styles[index].locked
        || target
            .sections
            .iter()
            .any(|section| section.memo_shape_id_ref == style_id && section.locked)
        || target
            .comments
            .iter()
            .any(|comment| {
                comment.style_id == style_id
                    && (comment.locked || locked_sections.contains(&comment.anchor.section_id))
            })
    {
        return Err(CommentError::Protected);
    }
    if target.styles[index] == *style {
        return Err(CommentError::Noop);
    }
    target.styles[index].clone_from(style);
    Ok(())
}

fn apply_visibility(
    target: &mut CommentDocumentState,
    identity: &CommentIdentity,
    visibility: CommentVisibility,
) -> Result<(), CommentError> {
    let index = exact_comment_index(&target.comments, identity)?;
    let section_index =
        exact_section_index(&target.sections, &target.comments[index].anchor.section_id)?;
    if target.comments[index].locked || target.sections[section_index].locked {
        return Err(CommentError::Protected);
    }
    if target.comments[index].visibility == visibility {
        return Err(CommentError::Noop);
    }
    target.comments[index].visibility = visibility;
    Ok(())
}

fn apply_resolution(
    target: &mut CommentDocumentState,
    identity: &CommentIdentity,
    resolution: CommentResolution,
) -> Result<(), CommentError> {
    let index = exact_comment_index(&target.comments, identity)?;
    let section_index =
        exact_section_index(&target.sections, &target.comments[index].anchor.section_id)?;
    if target.comments[index].locked || target.sections[section_index].locked {
        return Err(CommentError::Protected);
    }
    validate_resolution(
        &resolution,
        target.comments[index].created_at,
        |id| target.authors.iter().any(|author| author.author_id == id),
    )?;
    if target.comments[index].resolution == resolution {
        return Err(CommentError::Noop);
    }
    target.comments[index].resolution = resolution;
    Ok(())
}

fn exact_explanation_index(
    explanations: &[HiddenExplanationEntry],
    identity: &HiddenExplanationIdentity,
) -> Result<usize, CommentError> {
    exact_index(explanations, |entry| entry.identity == *identity)
}

fn exact_comment_index(
    comments: &[CommentEntry],
    identity: &CommentIdentity,
) -> Result<usize, CommentError> {
    exact_index(comments, |entry| entry.identity == *identity)
}

fn exact_style_index(styles: &[CommentStyle], style_id: u32) -> Result<usize, CommentError> {
    exact_index(styles, |style| style.style_id == style_id)
}

fn exact_section_index(
    sections: &[CommentSectionState],
    section_id: &LogicalId,
) -> Result<usize, CommentError> {
    exact_index(sections, |section| section.section_id == *section_id)
}

fn exact_index<T>(items: &[T], predicate: impl Fn(&T) -> bool) -> Result<usize, CommentError> {
    let mut matches = items
        .iter()
        .enumerate()
        .filter(|(_, item)| predicate(item))
        .map(|(index, _)| index);
    let index = matches.next().ok_or(CommentError::TargetNotFound)?;
    if matches.next().is_some() {
        return Err(CommentError::TargetNotFound);
    }
    Ok(index)
}

fn validate_document_state(
    state: &CommentDocumentState,
    limits: CommentLimits,
) -> Result<(), CommentError> {
    if state.schema_version != COMMENT_MODEL_SCHEMA_VERSION
        || state.sections.is_empty()
        || state.sections.len() > limits.0.sections
        || state.authors.len() > limits.0.authors
        || state.styles.is_empty()
        || state.styles.len() > limits.0.styles
        || state.hidden_explanations.len() > limits.0.hidden_explanations
        || state.comments.len() > limits.0.comments
    {
        return Err(CommentError::InvalidIdentity);
    }
    for digest in [
        &state.non_comment_content_sha256,
        &state.field_inventory_sha256,
        &state.style_catalog_sha256,
        &state.reference_inventory_sha256,
        &state.resource_inventory_sha256,
        &state.document_protection_sha256,
        &state.opaque_document_state_sha256,
    ] {
        require_digest(digest).map_err(|_| CommentError::InvalidPayload)?;
    }

    let mut author_ids = BTreeSet::new();
    for author in &state.authors {
        if author.author_id == 0 || !author_ids.insert(author.author_id) {
            return Err(CommentError::InvalidAuthorTime);
        }
        for digest in [
            Some(author.name_sha256.as_str()),
            author.email_sha256.as_deref(),
            Some(author.opaque_author_state_sha256.as_str()),
        ]
        .into_iter()
        .flatten()
        {
            require_digest(digest).map_err(|_| CommentError::InvalidAuthorTime)?;
        }
    }

    let mut style_ids = BTreeSet::new();
    for style in &state.styles {
        validate_style(style)?;
        if !style_ids.insert(style.style_id) {
            return Err(CommentError::InvalidStyle);
        }
    }

    let mut section_ids = BTreeSet::new();
    for section in &state.sections {
        if section.memo_shape_id_ref == 0
            || !style_ids.contains(&section.memo_shape_id_ref)
            || !section_ids.insert(&section.section_id)
        {
            return Err(CommentError::InvalidIdentity);
        }
        require_digest(&section.opaque_section_state_sha256)
            .map_err(|_| CommentError::InvalidPayload)?;
    }

    let mut explanation_ids = BTreeSet::new();
    let mut explanation_anchors = BTreeSet::new();
    for explanation in &state.hidden_explanations {
        validate_explanation(explanation, limits)?;
        if !section_ids.contains(&explanation.anchor.section_id)
            || !explanation_ids.insert(&explanation.identity)
            || !explanation_anchors.insert(&explanation.anchor)
        {
            return Err(CommentError::InvalidIdentity);
        }
    }

    let mut logical_ids = BTreeSet::new();
    let mut begin_ids = BTreeSet::new();
    let mut field_ids = BTreeSet::new();
    for comment in &state.comments {
        // Reuse already validated IDs: do not scan both complete catalogs per comment.
        validate_comment(
            comment,
            |id| author_ids.contains(&id),
            |id| style_ids.contains(&id),
            limits,
        )?;
        if !section_ids.contains(&comment.anchor.section_id)
            || !logical_ids.insert(&comment.identity.logical_comment_id)
            || !begin_ids.insert(comment.identity.begin_control_id)
            || !field_ids.insert(comment.identity.field_id)
        {
            return Err(CommentError::InvalidIdentity);
        }
    }
    Ok(())
}

fn validate_explanation(
    explanation: &HiddenExplanationEntry,
    limits: CommentLimits,
) -> Result<(), CommentError> {
    validate_anchor(&explanation.anchor)?;
    for digest in [
        Some(explanation.body_graph_sha256.as_str()),
        explanation.plain_text_sha256.as_deref(),
        Some(explanation.sub_list_sha256.as_str()),
        Some(explanation.opaque_native_payload_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest).map_err(|_| CommentError::InvalidPayload)?;
    }
    validate_opaque(&explanation.opaque_properties, limits)
}

fn validate_comment(
    comment: &CommentEntry,
    author_exists: impl Fn(u32) -> bool,
    style_exists: impl Fn(u32) -> bool,
    limits: CommentLimits,
) -> Result<(), CommentError> {
    if comment.identity.begin_control_id == 0 || comment.identity.field_id == 0 {
        return Err(CommentError::InvalidIdentity);
    }
    validate_anchor(&comment.anchor)?;
    if comment.native_begin_tag != CommentNativeBeginTag::FieldBegin
        || comment.native_end_tag != CommentNativeEndTag::FieldEnd
        || comment.native_field_type != CommentFieldType::Memo
        || comment.semantic_binding != CommentSemanticBinding::UnverifiedMemoParameters
    {
        return Err(CommentError::InvalidNativeBinding);
    }
    if comment.author_id == 0
        || !author_exists(comment.author_id)
        || comment.style_id == 0
        || !style_exists(comment.style_id)
    {
        return Err(CommentError::InvalidIdentity);
    }
    validate_timestamp(comment.created_at)?;
    if comment.modified_at.is_some_and(|value| {
        validate_timestamp(value).is_err() || value.epoch_millis < comment.created_at.epoch_millis
    }) {
        return Err(CommentError::InvalidAuthorTime);
    }
    validate_resolution(&comment.resolution, comment.created_at, author_exists)?;
    for digest in [
        comment.name_sha256.as_deref(),
        Some(comment.body_graph_sha256.as_str()),
        comment.plain_text_sha256.as_deref(),
        Some(comment.parameters_sha256.as_str()),
        Some(comment.sub_list_sha256.as_str()),
        Some(comment.opaque_native_payload_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest).map_err(|_| CommentError::InvalidPayload)?;
    }
    validate_opaque(&comment.opaque_properties, limits)
}

fn validate_anchor(anchor: &CommentAnchor) -> Result<(), CommentError> {
    if anchor.start > anchor.end {
        return Err(CommentError::InvalidAnchor);
    }
    Ok(())
}

fn validate_timestamp(value: CommentTimestamp) -> Result<(), CommentError> {
    if !(-840..=840).contains(&value.original_utc_offset_minutes) {
        return Err(CommentError::InvalidAuthorTime);
    }
    Ok(())
}

fn validate_resolution(
    resolution: &CommentResolution,
    created_at: CommentTimestamp,
    author_exists: impl Fn(u32) -> bool,
) -> Result<(), CommentError> {
    match (
        resolution.resolved,
        resolution.resolver_author_id,
        resolution.resolved_at,
    ) {
        (false, None, None) => Ok(()),
        (true, Some(author_id), Some(resolved_at))
            if author_id != 0
                && author_exists(author_id)
                && validate_timestamp(resolved_at).is_ok()
                && resolved_at.epoch_millis >= created_at.epoch_millis =>
        {
            Ok(())
        }
        _ => Err(CommentError::InvalidAuthorTime),
    }
}

fn validate_style(style: &CommentStyle) -> Result<(), CommentError> {
    if style.style_id == 0
        || style.width_native_units == 0
        || style.line_color_rgb > 0x00ff_ffff
        || style.fill_color_rgb > 0x00ff_ffff
        || style.active_color_rgb > 0x00ff_ffff
        || require_digest(&style.opaque_style_sha256).is_err()
    {
        return Err(CommentError::InvalidStyle);
    }
    Ok(())
}

fn validate_opaque(
    properties: &[OpaqueCommentProperty],
    limits: CommentLimits,
) -> Result<(), CommentError> {
    if properties.len() > limits.0.opaque_entries {
        return Err(CommentError::InvalidPayload);
    }
    let mut keys = BTreeSet::new();
    for property in properties {
        if !valid_token(&property.namespace, limits.0.text_bytes)
            || !valid_token(&property.name, limits.0.text_bytes)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(CommentError::InvalidPayload);
        }
    }
    Ok(())
}

fn valid_token(value: &str, maximum: usize) -> bool {
    !value.is_empty()
        && value.len() <= maximum
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
}

fn require_digest(value: &str) -> Result<(), CommentError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(CommentError::InvalidPayload);
    }
    Ok(())
}

fn plan_binding_sha256(plan: &CommentPlan, limits: CommentLimits) -> Result<String, CommentError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a CommentOperation,
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
    limits: CommentLimits,
) -> Result<Vec<u8>, CommentError> {
    let bytes = serde_json::to_vec(value).map_err(|_| CommentError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(CommentError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), CommentError> {
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
        .map_err(|_| CommentError::InvalidJson)?;
    deserializer.end().map_err(|_| CommentError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Private setup keeps sealed-plan tampering local.
mod private_tests {
    use super::*;

    const DIGEST: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> CommentLimits {
        CommentLimits::new(CommentLimitConfig::default()).expect("limits")
    }

    fn timestamp() -> CommentTimestamp {
        CommentTimestamp {
            epoch_millis: 1_700_000_000_000,
            original_utc_offset_minutes: 540,
        }
    }

    fn style() -> CommentStyle {
        CommentStyle {
            style_id: 1,
            width_native_units: 55,
            line_width: CommentLineWidth::Mm0_12,
            line_type: CommentLineType::Solid,
            line_color_rgb: 0,
            fill_color_rgb: 0x00cc_ff99,
            active_color_rgb: 0x00ff_ff99,
            memo_type: CommentMemoType::Normal,
            opaque_style_sha256: DIGEST.to_owned(),
            locked: false,
        }
    }

    fn author() -> CommentAuthor {
        CommentAuthor {
            author_id: 1,
            name_sha256: DIGEST.to_owned(),
            email_sha256: None,
            opaque_author_state_sha256: DIGEST.to_owned(),
            locked: false,
        }
    }

    fn comment() -> CommentEntry {
        CommentEntry {
            identity: CommentIdentity {
                logical_comment_id: LogicalId::parse("comment-1").expect("id"),
                begin_control_id: 10,
                field_id: 20,
            },
            anchor: CommentAnchor {
                section_id: LogicalId::parse("section-1").expect("id"),
                start: CommentPoint {
                    paragraph_ordinal: 0,
                    run_ordinal: 0,
                    inline_ordinal: 0,
                },
                end: CommentPoint {
                    paragraph_ordinal: 0,
                    run_ordinal: 0,
                    inline_ordinal: 1,
                },
            },
            native_begin_tag: CommentNativeBeginTag::FieldBegin,
            native_end_tag: CommentNativeEndTag::FieldEnd,
            native_field_type: CommentFieldType::Memo,
            semantic_binding: CommentSemanticBinding::UnverifiedMemoParameters,
            name_sha256: None,
            editable: true,
            dirty: false,
            z_order: -1,
            author_id: 1,
            created_at: timestamp(),
            modified_at: None,
            body_graph_sha256: DIGEST.to_owned(),
            plain_text_sha256: Some(DIGEST.to_owned()),
            parameters_sha256: DIGEST.to_owned(),
            sub_list_sha256: DIGEST.to_owned(),
            style_id: 1,
            visibility: CommentVisibility::Shown,
            resolution: CommentResolution {
                resolved: false,
                resolver_author_id: None,
                resolved_at: None,
            },
            opaque_native_payload_sha256: DIGEST.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    fn state() -> CommentDocumentState {
        CommentDocumentState::from_draft(
            CommentDocumentStateDraft {
                schema_version: COMMENT_MODEL_SCHEMA_VERSION.to_owned(),
                sections: vec![CommentSectionState {
                    section_id: LogicalId::parse("section-1").expect("id"),
                    memo_shape_id_ref: 1,
                    opaque_section_state_sha256: DIGEST.to_owned(),
                    locked: false,
                }],
                authors: vec![author()],
                styles: vec![style()],
                hidden_explanations: Vec::new(),
                comments: Vec::new(),
                non_comment_content_sha256: DIGEST.to_owned(),
                field_inventory_sha256: DIGEST.to_owned(),
                style_catalog_sha256: DIGEST.to_owned(),
                reference_inventory_sha256: DIGEST.to_owned(),
                resource_inventory_sha256: DIGEST.to_owned(),
                document_protection_sha256: DIGEST.to_owned(),
                opaque_document_state_sha256: DIGEST.to_owned(),
                document_locked: false,
            },
            limits(),
        )
        .expect("state")
    }

    #[test]
    fn private_plan_tampering_is_rejected() {
        let source = state();
        let request = CommentRequest::from_draft(
            CommentRequestDraft {
                schema_version: COMMENT_MODEL_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: DIGEST.to_owned(),
                target_document_flow_sha256: DIGEST.to_owned(),
                operation: CommentOperation::InsertComment {
                    insertion_index: 0,
                    comment: Box::new(comment()),
                },
            },
            &source,
            DIGEST,
            limits(),
        )
        .expect("request");
        let mut plan = CommentBuilder::plan(&source, &request, DIGEST, limits()).expect("plan");
        plan.capability_id = "ref.comment_style";
        assert_eq!(
            CommentBuilder::build(&plan, &source, DIGEST, limits()),
            Err(CommentError::PlanTampered)
        );
    }
}
