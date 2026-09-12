use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const FIELD_ENGINE_SCHEMA_VERSION: &str = "hwpx-agent.field-engine/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FieldEngineLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub fields: usize,
    pub text_bytes: usize,
    pub name_bytes: usize,
    pub opaque_entries: usize,
}

impl Default for FieldEngineLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            fields: 65_536,
            text_bytes: 64 * 1024,
            name_bytes: 1024,
            opaque_entries: 4096,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FieldEngineLimits(FieldEngineLimitConfig);

impl FieldEngineLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_FIELDS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_NAME_BYTES: usize = 16 * 1024;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 65_536;

    /// Creates finite limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: FieldEngineLimitConfig) -> Result<Self, FieldEngineError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.fields == 0
            || config.fields > Self::HARD_MAX_FIELDS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.name_bytes == 0
            || config.name_bytes > Self::HARD_MAX_NAME_BYTES
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
        {
            return Err(FieldEngineError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> FieldEngineLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FieldIdentity {
    pub logical_field_id: LogicalId,
    pub native_begin_id: u32,
    pub native_end_id: u32,
}

impl fmt::Debug for FieldIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FieldIdentity(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FieldAnchor {
    pub paragraph_id: LogicalId,
    pub run_ordinal: u32,
    pub inline_ordinal: u32,
}

impl fmt::Debug for FieldAnchor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FieldAnchor(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FieldNumberFormat {
    Digit,
    CircledDigit,
    RomanUpper,
    RomanLower,
    LatinUpper,
    LatinLower,
    HangulSyllable,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectNumberKind {
    Picture,
    Table,
    Equation,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FieldDefinition {
    Named {
        name: String,
        parameter: String,
    },
    UserDefined {
        name: String,
    },
    ClickHere {
        prompt: String,
    },
    DateTime {
        format: String,
        locale: String,
        timezone_offset_minutes: i16,
    },
    FileName {
        include_path: bool,
    },
    PageNumber {
        format: FieldNumberFormat,
    },
    SectionNumber {
        format: FieldNumberFormat,
    },
    ObjectNumber {
        object_kind: ObjectNumberKind,
        format: FieldNumberFormat,
    },
}

impl FieldDefinition {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::Named { .. } => "ref.field_insert",
            Self::UserDefined { .. } => "ref.field_user",
            Self::ClickHere { .. } => "ref.field_click_here",
            Self::DateTime { .. } => "ref.field_date_time",
            Self::FileName { .. } => "ref.field_filename",
            Self::PageNumber { .. } => "ref.field_page_number",
            Self::SectionNumber { .. } => "ref.field_section_number",
            Self::ObjectNumber { .. } => "ref.field_object_number",
        }
    }

    #[must_use]
    pub const fn expects_number_result(&self) -> bool {
        matches!(
            self,
            Self::PageNumber { .. } | Self::SectionNumber { .. } | Self::ObjectNumber { .. }
        )
    }
}

impl fmt::Debug for FieldDefinition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldDefinition")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FieldCachedResult {
    Text { display: String },
    Number { value: i64, display: String },
}

impl FieldCachedResult {
    fn display(&self) -> &str {
        match self {
            Self::Text { display } | Self::Number { display, .. } => display,
        }
    }

    const fn is_number(&self) -> bool {
        matches!(self, Self::Number { .. })
    }
}

impl fmt::Debug for FieldCachedResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FieldCachedResult(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FieldUpdatePolicy {
    PreserveCached,
    RecomputeDirect,
    RecomputeAutomation,
    FreezeText,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FieldCacheStatus {
    Current,
    Stale,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OpaqueFieldProperty {
    pub namespace: String,
    pub name: String,
    pub value_sha256: String,
}

impl fmt::Debug for OpaqueFieldProperty {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("OpaqueFieldProperty(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FieldState {
    pub identity: FieldIdentity,
    pub anchor: FieldAnchor,
    pub definition: FieldDefinition,
    pub cached_result: FieldCachedResult,
    pub update_policy: FieldUpdatePolicy,
    pub cache_status: FieldCacheStatus,
    pub locked: bool,
    pub evaluation_context_sha256: Option<String>,
    pub character_style_sha256: String,
    pub paragraph_style_sha256: String,
    pub field_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueFieldProperty>,
}

impl fmt::Debug for FieldState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldState")
            .field("capability_id", &self.definition.capability_id())
            .field("locked", &self.locked)
            .field("cache_status", &self.cache_status)
            .field("identity", &"<redacted>")
            .field("content", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FieldDocumentStateDraft {
    pub schema_version: String,
    pub fields: Vec<FieldState>,
    pub non_field_content_sha256: String,
    pub style_catalog_sha256: String,
    pub reference_inventory_sha256: String,
    pub resource_inventory_sha256: String,
    pub opaque_document_state_sha256: String,
}

impl fmt::Debug for FieldDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FieldDocumentStateDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FieldDocumentState {
    schema_version: &'static str,
    fields: Vec<FieldState>,
    non_field_content_sha256: String,
    style_catalog_sha256: String,
    reference_inventory_sha256: String,
    resource_inventory_sha256: String,
    opaque_document_state_sha256: String,
}

impl FieldDocumentState {
    /// Validates and seals a complete field inventory and preserved document state.
    ///
    /// # Errors
    ///
    /// Rejects version, identity, anchor, result, policy, digest, or finite-limit failures.
    pub fn from_draft(
        draft: FieldDocumentStateDraft,
        limits: FieldEngineLimits,
    ) -> Result<Self, FieldEngineError> {
        if draft.schema_version != FIELD_ENGINE_SCHEMA_VERSION {
            return Err(FieldEngineError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION,
            fields: draft.fields,
            non_field_content_sha256: draft.non_field_content_sha256,
            style_catalog_sha256: draft.style_catalog_sha256,
            reference_inventory_sha256: draft.reference_inventory_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            opaque_document_state_sha256: draft.opaque_document_state_sha256,
        };
        validate_document_state(&state, limits)?;
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub fn fields(&self) -> &[FieldState] {
        &self.fields
    }

    /// Serializes the complete state deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: FieldEngineLimits) -> Result<Vec<u8>, FieldEngineError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_sha256(&self, limits: FieldEngineLimits) -> Result<String, FieldEngineError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for FieldDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldDocumentState")
            .field("field_count", &self.fields.len())
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FieldOperation {
    Insert {
        insertion_index: usize,
        field: FieldState,
    },
    UpdateResult {
        target: FieldIdentity,
        cached_result: FieldCachedResult,
        evaluation_context_sha256: String,
    },
    SetLock {
        target: FieldIdentity,
        locked: bool,
    },
}

impl FieldOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::Insert { field, .. } => field.definition.capability_id(),
            Self::UpdateResult { .. } => "ref.field_update",
            Self::SetLock { .. } => "ref.field_lock",
        }
    }
}

impl fmt::Debug for FieldOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FieldRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: FieldOperation,
}

impl fmt::Debug for FieldRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FieldRequestDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FieldRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: FieldOperation,
}

impl FieldRequest {
    /// Validates one exact field transition against current state and document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, source-state, flow, operation, collision, lock, or limit failures.
    pub fn from_draft(
        draft: FieldRequestDraft,
        current: &FieldDocumentState,
        current_document_flow_sha256: &str,
        limits: FieldEngineLimits,
    ) -> Result<Self, FieldEngineError> {
        if draft.schema_version != FIELD_ENGINE_SCHEMA_VERSION {
            return Err(FieldEngineError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if current.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(FieldEngineError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(FieldEngineError::DocumentFlowDrift);
        }
        let _ = apply_operation(current, &draft.operation, limits)?;
        let request = Self {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION,
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
        current: &FieldDocumentState,
        current_document_flow_sha256: &str,
        limits: FieldEngineLimits,
    ) -> Result<Self, FieldEngineError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(FieldEngineError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| FieldEngineError::InvalidJson)?;
        Self::from_draft(draft, current, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub fn operation(&self) -> &FieldOperation {
        &self.operation
    }

    /// Serializes the request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: FieldEngineLimits) -> Result<Vec<u8>, FieldEngineError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for FieldRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FieldPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state: FieldDocumentState,
    source_state_sha256: String,
    target_state: FieldDocumentState,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: FieldOperation,
    plan_sha256: String,
}

impl FieldPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn source_state(&self) -> &FieldDocumentState {
        &self.source_state
    }

    #[must_use]
    pub const fn target_state(&self) -> &FieldDocumentState {
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

    /// Serializes the sealed plan deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: FieldEngineLimits) -> Result<Vec<u8>, FieldEngineError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for FieldPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldPlan")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct FieldEngineBuilder;

impl FieldEngineBuilder {
    /// Builds and seals an immutable plan from current state and a validated request.
    ///
    /// # Errors
    ///
    /// Rejects source-state, flow, operation, or output drift.
    pub fn plan(
        current: &FieldDocumentState,
        request: &FieldRequest,
        current_document_flow_sha256: &str,
        limits: FieldEngineLimits,
    ) -> Result<FieldPlan, FieldEngineError> {
        require_digest(current_document_flow_sha256)?;
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(FieldEngineError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(FieldEngineError::DocumentFlowDrift);
        }
        let target_state = apply_operation(current, &request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = FieldPlan {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION,
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

    /// Revalidates the sealed plan against current state and flow before returning a result.
    ///
    /// # Errors
    ///
    /// Rejects source-state, flow, plan binding, operation, or output drift.
    pub fn build(
        plan: &FieldPlan,
        current: &FieldDocumentState,
        current_document_flow_sha256: &str,
        limits: FieldEngineLimits,
    ) -> Result<FieldResult, FieldEngineError> {
        validate_document_state(current, limits)?;
        if plan.schema_version != FIELD_ENGINE_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan.plan_sha256 != plan_binding_sha256(plan, limits)?
        {
            return Err(FieldEngineError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256
            || current != &plan.source_state
        {
            return Err(FieldEngineError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(FieldEngineError::DocumentFlowDrift);
        }
        let recomputed = apply_operation(&plan.source_state, &plan.operation, limits)?;
        if recomputed != plan.target_state
            || recomputed.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(FieldEngineError::PlanTampered);
        }
        let receipt = FieldReceipt {
            schema_version: FIELD_ENGINE_SCHEMA_VERSION,
            capability_id: plan.capability_id,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: plan.target_state_sha256.clone(),
            source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
            target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
            plan_sha256: plan.plan_sha256.clone(),
        };
        let _ = serialize_bounded(&receipt, limits)?;
        Ok(FieldResult {
            state: plan.target_state.clone(),
            receipt,
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FieldReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for FieldReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FieldResult {
    pub state: FieldDocumentState,
    pub receipt: FieldReceipt,
}

impl fmt::Debug for FieldResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FieldEngineError {
    #[error("field engine limits are invalid")]
    InvalidLimit,
    #[error("field engine input exceeds a finite limit")]
    InputLimit,
    #[error("field engine JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("field engine schema version is unsupported")]
    UnsupportedVersion,
    #[error("field identity or anchor is invalid or colliding")]
    InvalidIdentity,
    #[error("field digest is malformed")]
    InvalidDigest,
    #[error("field definition, result, or policy is invalid")]
    InvalidField,
    #[error("field insertion index is invalid")]
    InvalidInsertionIndex,
    #[error("field target does not exist or is ambiguous")]
    FieldNotFound,
    #[error("locked or frozen field cannot be updated")]
    FieldLocked,
    #[error("field operation is a no-op")]
    Noop,
    #[error("field source state drifted")]
    SourceStateDrift,
    #[error("field document flow drifted")]
    DocumentFlowDrift,
    #[error("field plan was tampered with")]
    PlanTampered,
    #[error("field serialization failed")]
    Serialization,
    #[error("field serialized output exceeds a finite limit")]
    OutputLimit,
}

impl FieldEngineError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "field_engine_invalid_limit",
            Self::InputLimit => "field_engine_input_limit",
            Self::InvalidJson => "field_engine_invalid_json",
            Self::UnsupportedVersion => "field_engine_unsupported_version",
            Self::InvalidIdentity => "field_engine_invalid_identity",
            Self::InvalidDigest => "field_engine_invalid_digest",
            Self::InvalidField => "field_engine_invalid_field",
            Self::InvalidInsertionIndex => "field_engine_invalid_insertion_index",
            Self::FieldNotFound => "field_engine_field_not_found",
            Self::FieldLocked => "field_engine_field_locked",
            Self::Noop => "field_engine_noop",
            Self::SourceStateDrift => "field_engine_source_state_drift",
            Self::DocumentFlowDrift => "field_engine_document_flow_drift",
            Self::PlanTampered => "field_engine_plan_tampered",
            Self::Serialization => "field_engine_serialization",
            Self::OutputLimit => "field_engine_output_limit",
        }
    }
}

fn apply_operation(
    source: &FieldDocumentState,
    operation: &FieldOperation,
    limits: FieldEngineLimits,
) -> Result<FieldDocumentState, FieldEngineError> {
    validate_document_state(source, limits)?;
    let mut target = source.clone();
    match operation {
        FieldOperation::Insert {
            insertion_index,
            field,
        } => {
            if *insertion_index > source.fields.len() {
                return Err(FieldEngineError::InvalidInsertionIndex);
            }
            validate_field(field, limits)?;
            if source.fields.iter().any(|existing| {
                existing.identity.logical_field_id == field.identity.logical_field_id
                    || existing.identity.native_begin_id == field.identity.native_begin_id
                    || existing.identity.native_end_id == field.identity.native_end_id
                    || existing.identity.native_begin_id == field.identity.native_end_id
                    || existing.identity.native_end_id == field.identity.native_begin_id
                    || existing.anchor == field.anchor
            }) {
                return Err(FieldEngineError::InvalidIdentity);
            }
            target.fields.insert(*insertion_index, field.clone());
        }
        FieldOperation::UpdateResult {
            target: identity,
            cached_result,
            evaluation_context_sha256,
        } => {
            require_digest(evaluation_context_sha256)?;
            let field = exact_target_mut(&mut target.fields, identity)?;
            if field.locked || field.update_policy == FieldUpdatePolicy::FreezeText {
                return Err(FieldEngineError::FieldLocked);
            }
            validate_result(&field.definition, cached_result, limits)?;
            if field.cached_result == *cached_result
                && field.cache_status == FieldCacheStatus::Current
                && field.evaluation_context_sha256.as_deref()
                    == Some(evaluation_context_sha256.as_str())
            {
                return Err(FieldEngineError::Noop);
            }
            field.cached_result.clone_from(cached_result);
            field.cache_status = FieldCacheStatus::Current;
            field.evaluation_context_sha256 = Some(evaluation_context_sha256.clone());
        }
        FieldOperation::SetLock {
            target: identity,
            locked,
        } => {
            let field = exact_target_mut(&mut target.fields, identity)?;
            if field.locked == *locked {
                return Err(FieldEngineError::Noop);
            }
            field.locked = *locked;
        }
    }
    validate_document_state(&target, limits)?;
    if &target == source {
        return Err(FieldEngineError::Noop);
    }
    Ok(target)
}

fn exact_target_mut<'a>(
    fields: &'a mut [FieldState],
    identity: &FieldIdentity,
) -> Result<&'a mut FieldState, FieldEngineError> {
    let mut matches = fields
        .iter_mut()
        .filter(|field| field.identity == *identity);
    let target = matches.next().ok_or(FieldEngineError::FieldNotFound)?;
    if matches.next().is_some() {
        return Err(FieldEngineError::FieldNotFound);
    }
    Ok(target)
}

fn validate_document_state(
    state: &FieldDocumentState,
    limits: FieldEngineLimits,
) -> Result<(), FieldEngineError> {
    if state.schema_version != FIELD_ENGINE_SCHEMA_VERSION || state.fields.len() > limits.0.fields {
        return Err(FieldEngineError::InvalidField);
    }
    for digest in [
        &state.non_field_content_sha256,
        &state.style_catalog_sha256,
        &state.reference_inventory_sha256,
        &state.resource_inventory_sha256,
        &state.opaque_document_state_sha256,
    ] {
        require_digest(digest)?;
    }
    let mut logical_ids = BTreeSet::new();
    let mut native_ids = BTreeSet::new();
    let mut anchors = BTreeSet::new();
    for field in &state.fields {
        validate_field(field, limits)?;
        if !logical_ids.insert(&field.identity.logical_field_id)
            || !native_ids.insert(field.identity.native_begin_id)
            || !native_ids.insert(field.identity.native_end_id)
            || !anchors.insert(&field.anchor)
        {
            return Err(FieldEngineError::InvalidIdentity);
        }
    }
    Ok(())
}

fn validate_field(field: &FieldState, limits: FieldEngineLimits) -> Result<(), FieldEngineError> {
    if field.identity.native_begin_id == 0
        || field.identity.native_end_id == 0
        || field.identity.native_begin_id == field.identity.native_end_id
    {
        return Err(FieldEngineError::InvalidIdentity);
    }
    validate_definition(&field.definition, limits)?;
    validate_result(&field.definition, &field.cached_result, limits)?;
    if field.update_policy == FieldUpdatePolicy::FreezeText
        && field.cache_status == FieldCacheStatus::Stale
    {
        return Err(FieldEngineError::InvalidField);
    }
    if let Some(digest) = &field.evaluation_context_sha256 {
        require_digest(digest)?;
    }
    for digest in [
        &field.character_style_sha256,
        &field.paragraph_style_sha256,
        &field.field_payload_sha256,
    ] {
        require_digest(digest)?;
    }
    if field.opaque_properties.len() > limits.0.opaque_entries {
        return Err(FieldEngineError::InvalidField);
    }
    let mut keys = BTreeSet::new();
    for property in &field.opaque_properties {
        if !valid_token(&property.namespace, limits.0.name_bytes)
            || !valid_token(&property.name, limits.0.name_bytes)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(FieldEngineError::InvalidField);
        }
    }
    Ok(())
}

fn validate_definition(
    definition: &FieldDefinition,
    limits: FieldEngineLimits,
) -> Result<(), FieldEngineError> {
    let valid = match definition {
        FieldDefinition::Named { name, parameter } => {
            valid_name(name, limits.0.name_bytes)
                && valid_text(parameter, limits.0.text_bytes, true)
        }
        FieldDefinition::UserDefined { name } => valid_name(name, limits.0.name_bytes),
        FieldDefinition::ClickHere { prompt } => valid_text(prompt, limits.0.text_bytes, false),
        FieldDefinition::DateTime {
            format,
            locale,
            timezone_offset_minutes,
        } => {
            valid_text(format, limits.0.name_bytes, false)
                && valid_locale(locale, limits.0.name_bytes)
                && (-1_080..=1_080).contains(timezone_offset_minutes)
        }
        FieldDefinition::FileName { .. }
        | FieldDefinition::PageNumber { .. }
        | FieldDefinition::SectionNumber { .. }
        | FieldDefinition::ObjectNumber { .. } => true,
    };
    if !valid {
        return Err(FieldEngineError::InvalidField);
    }
    Ok(())
}

fn validate_result(
    definition: &FieldDefinition,
    result: &FieldCachedResult,
    limits: FieldEngineLimits,
) -> Result<(), FieldEngineError> {
    if definition.expects_number_result() != result.is_number()
        || !valid_text(result.display(), limits.0.text_bytes, true)
    {
        return Err(FieldEngineError::InvalidField);
    }
    if let FieldCachedResult::Number { value, .. } = result
        && *value < 0
    {
        return Err(FieldEngineError::InvalidField);
    }
    Ok(())
}

fn valid_name(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && !value.chars().any(|character| {
            character == '\0' || character == '\\' || character == '/' || character.is_control()
        })
}

fn valid_locale(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
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

fn require_digest(value: &str) -> Result<(), FieldEngineError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(FieldEngineError::InvalidDigest);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &FieldPlan,
    limits: FieldEngineLimits,
) -> Result<String, FieldEngineError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a FieldOperation,
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
    limits: FieldEngineLimits,
) -> Result<Vec<u8>, FieldEngineError> {
    let bytes = serde_json::to_vec(value).map_err(|_| FieldEngineError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(FieldEngineError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), FieldEngineError> {
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
        .map_err(|_| FieldEngineError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| FieldEngineError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Private setup uses expectations to isolate sealed-plan tampering.
mod private_tests {
    use super::*;

    const DIGEST: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> FieldEngineLimits {
        FieldEngineLimits::new(FieldEngineLimitConfig::default()).expect("limits")
    }

    fn state() -> FieldDocumentState {
        FieldDocumentState::from_draft(
            FieldDocumentStateDraft {
                schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
                fields: Vec::new(),
                non_field_content_sha256: DIGEST.to_owned(),
                style_catalog_sha256: DIGEST.to_owned(),
                reference_inventory_sha256: DIGEST.to_owned(),
                resource_inventory_sha256: DIGEST.to_owned(),
                opaque_document_state_sha256: DIGEST.to_owned(),
            },
            limits(),
        )
        .expect("state")
    }

    #[test]
    fn private_plan_tampering_is_rejected() {
        let source = state();
        let field = FieldState {
            identity: FieldIdentity {
                logical_field_id: LogicalId::parse("field-1").expect("id"),
                native_begin_id: 1,
                native_end_id: 2,
            },
            anchor: FieldAnchor {
                paragraph_id: LogicalId::parse("paragraph-1").expect("id"),
                run_ordinal: 0,
                inline_ordinal: 0,
            },
            definition: FieldDefinition::UserDefined {
                name: "private-name".to_owned(),
            },
            cached_result: FieldCachedResult::Text {
                display: "private-result".to_owned(),
            },
            update_policy: FieldUpdatePolicy::PreserveCached,
            cache_status: FieldCacheStatus::Current,
            locked: false,
            evaluation_context_sha256: None,
            character_style_sha256: DIGEST.to_owned(),
            paragraph_style_sha256: DIGEST.to_owned(),
            field_payload_sha256: DIGEST.to_owned(),
            opaque_properties: Vec::new(),
        };
        let request = FieldRequest::from_draft(
            FieldRequestDraft {
                schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: DIGEST.to_owned(),
                target_document_flow_sha256: DIGEST.to_owned(),
                operation: FieldOperation::Insert {
                    insertion_index: 0,
                    field,
                },
            },
            &source,
            DIGEST,
            limits(),
        )
        .expect("request");
        let mut plan = FieldEngineBuilder::plan(&source, &request, DIGEST, limits()).expect("plan");
        plan.capability_id = "ref.field_lock";
        assert_eq!(
            FieldEngineBuilder::build(&plan, &source, DIGEST, limits()),
            Err(FieldEngineError::PlanTampered)
        );
    }
}
