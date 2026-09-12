use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LinkAnchor, LogicalId, OpaqueLinkProperty};

pub const MAIL_MERGE_SCHEMA_VERSION: &str = "hwpx-agent.mail-merge/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct MailMergeLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub sections: usize,
    pub data_sources: usize,
    pub columns_per_source: usize,
    pub fields: usize,
    pub occupied_native_ids: usize,
    pub opaque_entries: usize,
    pub records_per_source: u64,
}

impl Default for MailMergeLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            sections: 4096,
            data_sources: 4096,
            columns_per_source: 65_536,
            fields: 1_000_000,
            occupied_native_ids: 1_000_000,
            opaque_entries: 4096,
            records_per_source: 10_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct MailMergeLimits(MailMergeLimitConfig);

impl MailMergeLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 65_536;
    pub const HARD_MAX_RECORDS: u64 = 100_000_000;

    /// Creates finite mail-merge limits without silently clamping values.
    ///
    /// # Errors
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: MailMergeLimitConfig) -> Result<Self, MailMergeError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.sections == 0
            || config.sections > Self::HARD_MAX_ITEMS
            || config.data_sources == 0
            || config.data_sources > Self::HARD_MAX_ITEMS
            || config.columns_per_source == 0
            || config.columns_per_source > Self::HARD_MAX_ITEMS
            || config.fields == 0
            || config.fields > Self::HARD_MAX_ITEMS
            || config.occupied_native_ids == 0
            || config.occupied_native_ids > Self::HARD_MAX_ITEMS
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
            || config.records_per_source == 0
            || config.records_per_source > Self::HARD_MAX_RECORDS
        {
            return Err(MailMergeError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> MailMergeLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MailMergeSectionState {
    pub section_id: LogicalId,
    pub paragraph_count: u32,
    pub run_topology_sha256: String,
    pub inline_topology_sha256: String,
    pub page_assignment_sha256: String,
    pub opaque_section_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for MailMergeSectionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeSectionState")
            .field("paragraph_count", &self.paragraph_count)
            .field("locked", &self.locked)
            .field("section", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailMergeColumnType {
    Text,
    Integer,
    FixedDecimal,
    Date,
    Boolean,
    Opaque,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailMergeSensitivity {
    NonPersonal,
    Pseudonymous,
    Personal,
    Sensitive,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MailMergeColumn {
    pub logical_column_id: LogicalId,
    pub provider_column_key_sha256: String,
    pub display_name_sha256: String,
    pub column_type: MailMergeColumnType,
    pub nullable: bool,
    pub sensitivity: MailMergeSensitivity,
    pub semantic_definition_sha256: String,
    pub format_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for MailMergeColumn {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeColumn")
            .field("column_type", &self.column_type)
            .field("nullable", &self.nullable)
            .field("sensitivity", &self.sensitivity)
            .field("locked", &self.locked)
            .field("column", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MailMergeDataSource {
    pub logical_source_id: LogicalId,
    pub artifact_sha256: String,
    pub encryption_envelope_sha256: String,
    pub provider_id_sha256: String,
    pub provider_version_sha256: String,
    pub locale: String,
    pub schema_sha256: String,
    pub row_identity_manifest_sha256: String,
    pub record_count: u64,
    pub access_policy_sha256: String,
    pub pii_policy_sha256: String,
    pub encrypted_artifact: bool,
    pub columns: Vec<MailMergeColumn>,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for MailMergeDataSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeDataSource")
            .field("record_count", &self.record_count)
            .field("column_count", &self.columns.len())
            .field("encrypted_artifact", &self.encrypted_artifact)
            .field("locked", &self.locked)
            .field("source", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailMergeCacheStatus {
    Current,
    Stale,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MailMergeFieldCache {
    pub binding_projection_sha256: String,
    pub placeholder_text_sha256: String,
    pub status: MailMergeCacheStatus,
}

impl fmt::Debug for MailMergeFieldCache {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeFieldCache")
            .field("status", &self.status)
            .field("cache", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailMergeNativeBeginTag {
    FieldBegin,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailMergeNativeEndTag {
    FieldEnd,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailMergeFieldType {
    Mailmerge,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MailMergeSemanticBinding {
    UnverifiedFieldParameters,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MailMergeNativePair {
    pub begin_tag: MailMergeNativeBeginTag,
    pub end_tag: MailMergeNativeEndTag,
    pub field_type: MailMergeFieldType,
    pub semantic_binding: MailMergeSemanticBinding,
    pub end_begin_control_id_ref: u32,
    pub end_field_id: u32,
    pub field_name_sha256: Option<String>,
    pub editable: bool,
    pub dirty: bool,
    pub z_order: i32,
    pub parameters_sha256: String,
    pub sub_list_sha256: Option<String>,
    pub meta_tag_sha256: Option<String>,
    pub opaque_begin_state_sha256: String,
    pub opaque_end_state_sha256: String,
}

impl fmt::Debug for MailMergeNativePair {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeNativePair")
            .field("begin_tag", &self.begin_tag)
            .field("end_tag", &self.end_tag)
            .field("field_type", &self.field_type)
            .field("semantic_binding", &self.semantic_binding)
            .field("editable", &self.editable)
            .field("dirty", &self.dirty)
            .field("native", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MailMergeFieldNode {
    pub logical_field_id: LogicalId,
    pub begin_control_id: u32,
    pub field_id: u32,
    pub anchor: LinkAnchor,
    pub logical_source_id: LogicalId,
    pub logical_column_id: LogicalId,
    pub cache: MailMergeFieldCache,
    pub native_pair: MailMergeNativePair,
    pub opaque_field_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl MailMergeFieldNode {
    /// Computes the exact source/schema/selected-column projection for a template field.
    ///
    /// The external artifact bytes, row manifest, record count and unselected columns are excluded:
    /// they affect later generation, not the identity of this inserted template field.
    ///
    /// # Errors
    /// Returns a source, column, serialization, or output-limit error.
    pub fn projection_sha256(
        source: &MailMergeDataSource,
        column_id: &LogicalId,
        limits: MailMergeLimits,
    ) -> Result<String, MailMergeError> {
        #[derive(Serialize)]
        struct Projection<'a> {
            logical_source_id: &'a LogicalId,
            provider_id_sha256: &'a str,
            provider_version_sha256: &'a str,
            locale: &'a str,
            schema_sha256: &'a str,
            selected_column: &'a MailMergeColumn,
        }
        validate_source(source, limits)?;
        let column = select_column(source, column_id)?;
        Ok(hex(Sha256::digest(serialize_bounded(
            &Projection {
                logical_source_id: &source.logical_source_id,
                provider_id_sha256: &source.provider_id_sha256,
                provider_version_sha256: &source.provider_version_sha256,
                locale: &source.locale,
                schema_sha256: &source.schema_sha256,
                selected_column: column,
            },
            limits,
        )?)
        .into()))
    }
}

impl fmt::Debug for MailMergeFieldNode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeFieldNode")
            .field("cache_status", &self.cache.status)
            .field("locked", &self.locked)
            .field("field", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MailMergeDocumentStateDraft {
    pub schema_version: String,
    pub sections: Vec<MailMergeSectionState>,
    pub data_sources: Vec<MailMergeDataSource>,
    pub fields: Vec<MailMergeFieldNode>,
    pub occupied_non_mailmerge_control_ids: Vec<u32>,
    pub occupied_non_mailmerge_field_ids: Vec<u32>,
    pub occupied_non_mailmerge_field_name_sha256: Vec<String>,
    pub preview_inventory_sha256: String,
    pub batch_output_inventory_sha256: String,
    pub label_layout_catalog_sha256: String,
    pub non_mailmerge_content_sha256: String,
    pub unrelated_field_inventory_sha256: String,
    pub reference_inventory_sha256: String,
    pub note_inventory_sha256: String,
    pub toc_index_inventory_sha256: String,
    pub citation_inventory_sha256: String,
    pub object_inventory_sha256: String,
    pub numbering_inventory_sha256: String,
    pub style_catalog_sha256: String,
    pub relationship_inventory_sha256: String,
    pub resource_inventory_sha256: String,
    pub document_protection_sha256: String,
    pub opaque_document_state_sha256: String,
    pub document_locked: bool,
}

impl fmt::Debug for MailMergeDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeDocumentStateDraft")
            .field("section_count", &self.sections.len())
            .field("source_count", &self.data_sources.len())
            .field("field_count", &self.fields.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(
    try_from = "MailMergeDocumentStateDraft",
    into = "MailMergeDocumentStateDraft"
)]
pub struct MailMergeDocumentState {
    schema_version: String,
    sections: Vec<MailMergeSectionState>,
    data_sources: Vec<MailMergeDataSource>,
    fields: Vec<MailMergeFieldNode>,
    occupied_non_mailmerge_control_ids: Vec<u32>,
    occupied_non_mailmerge_field_ids: Vec<u32>,
    occupied_non_mailmerge_field_name_sha256: Vec<String>,
    preview_inventory_sha256: String,
    batch_output_inventory_sha256: String,
    label_layout_catalog_sha256: String,
    non_mailmerge_content_sha256: String,
    unrelated_field_inventory_sha256: String,
    reference_inventory_sha256: String,
    note_inventory_sha256: String,
    toc_index_inventory_sha256: String,
    citation_inventory_sha256: String,
    object_inventory_sha256: String,
    numbering_inventory_sha256: String,
    style_catalog_sha256: String,
    relationship_inventory_sha256: String,
    resource_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
    document_locked: bool,
}

impl MailMergeDocumentState {
    /// Validates and constructs a complete mail-merge template state.
    ///
    /// # Errors
    /// Returns a typed error for incomplete, unsafe, or inconsistent state.
    pub fn from_draft(
        draft: MailMergeDocumentStateDraft,
        limits: MailMergeLimits,
    ) -> Result<Self, MailMergeError> {
        let state = Self {
            schema_version: draft.schema_version,
            sections: draft.sections,
            data_sources: draft.data_sources,
            fields: draft.fields,
            occupied_non_mailmerge_control_ids: draft.occupied_non_mailmerge_control_ids,
            occupied_non_mailmerge_field_ids: draft.occupied_non_mailmerge_field_ids,
            occupied_non_mailmerge_field_name_sha256: draft
                .occupied_non_mailmerge_field_name_sha256,
            preview_inventory_sha256: draft.preview_inventory_sha256,
            batch_output_inventory_sha256: draft.batch_output_inventory_sha256,
            label_layout_catalog_sha256: draft.label_layout_catalog_sha256,
            non_mailmerge_content_sha256: draft.non_mailmerge_content_sha256,
            unrelated_field_inventory_sha256: draft.unrelated_field_inventory_sha256,
            reference_inventory_sha256: draft.reference_inventory_sha256,
            note_inventory_sha256: draft.note_inventory_sha256,
            toc_index_inventory_sha256: draft.toc_index_inventory_sha256,
            citation_inventory_sha256: draft.citation_inventory_sha256,
            object_inventory_sha256: draft.object_inventory_sha256,
            numbering_inventory_sha256: draft.numbering_inventory_sha256,
            style_catalog_sha256: draft.style_catalog_sha256,
            relationship_inventory_sha256: draft.relationship_inventory_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            document_protection_sha256: draft.document_protection_sha256,
            opaque_document_state_sha256: draft.opaque_document_state_sha256,
            document_locked: draft.document_locked,
        };
        validate_state(&state, limits)?;
        Ok(state)
    }

    #[must_use]
    pub fn data_sources(&self) -> &[MailMergeDataSource] {
        &self.data_sources
    }

    #[must_use]
    pub fn fields(&self) -> &[MailMergeFieldNode] {
        &self.fields
    }

    /// Serializes the canonical validated state within the configured bound.
    ///
    /// # Errors
    /// Returns a validation, serialization, or output-limit error.
    pub fn canonical_json(&self, limits: MailMergeLimits) -> Result<Vec<u8>, MailMergeError> {
        validate_state(self, limits)?;
        serialize_bounded(self, limits)
    }

    /// Computes the canonical state digest.
    ///
    /// # Errors
    /// Returns a validation, serialization, or output-limit error.
    pub fn canonical_sha256(&self, limits: MailMergeLimits) -> Result<String, MailMergeError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl TryFrom<MailMergeDocumentStateDraft> for MailMergeDocumentState {
    type Error = MailMergeError;

    fn try_from(draft: MailMergeDocumentStateDraft) -> Result<Self, Self::Error> {
        let limits = MailMergeLimits::new(MailMergeLimitConfig::default())?;
        Self::from_draft(draft, limits)
    }
}

impl From<MailMergeDocumentState> for MailMergeDocumentStateDraft {
    fn from(state: MailMergeDocumentState) -> Self {
        Self {
            schema_version: state.schema_version,
            sections: state.sections,
            data_sources: state.data_sources,
            fields: state.fields,
            occupied_non_mailmerge_control_ids: state.occupied_non_mailmerge_control_ids,
            occupied_non_mailmerge_field_ids: state.occupied_non_mailmerge_field_ids,
            occupied_non_mailmerge_field_name_sha256: state
                .occupied_non_mailmerge_field_name_sha256,
            preview_inventory_sha256: state.preview_inventory_sha256,
            batch_output_inventory_sha256: state.batch_output_inventory_sha256,
            label_layout_catalog_sha256: state.label_layout_catalog_sha256,
            non_mailmerge_content_sha256: state.non_mailmerge_content_sha256,
            unrelated_field_inventory_sha256: state.unrelated_field_inventory_sha256,
            reference_inventory_sha256: state.reference_inventory_sha256,
            note_inventory_sha256: state.note_inventory_sha256,
            toc_index_inventory_sha256: state.toc_index_inventory_sha256,
            citation_inventory_sha256: state.citation_inventory_sha256,
            object_inventory_sha256: state.object_inventory_sha256,
            numbering_inventory_sha256: state.numbering_inventory_sha256,
            style_catalog_sha256: state.style_catalog_sha256,
            relationship_inventory_sha256: state.relationship_inventory_sha256,
            resource_inventory_sha256: state.resource_inventory_sha256,
            document_protection_sha256: state.document_protection_sha256,
            opaque_document_state_sha256: state.opaque_document_state_sha256,
            document_locked: state.document_locked,
        }
    }
}

impl fmt::Debug for MailMergeDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeDocumentState")
            .field("source_count", &self.data_sources.len())
            .field("field_count", &self.fields.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum MailMergeOperation {
    FieldInsert {
        insertion_index: usize,
        field: Box<MailMergeFieldNode>,
    },
}

impl MailMergeOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::FieldInsert { .. } => "ref.mailmerge_field",
        }
    }
}

impl fmt::Debug for MailMergeOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MailMergeRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: MailMergeOperation,
}

impl fmt::Debug for MailMergeRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeRequestDraft")
            .field("capability_id", &self.operation.capability_id())
            .field("request", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct MailMergeRequest {
    schema_version: String,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: MailMergeOperation,
}

impl MailMergeRequest {
    /// Validates a request against the exact current state and document flow.
    ///
    /// # Errors
    /// Returns a typed validation or drift error before any plan exists.
    pub fn from_draft(
        draft: MailMergeRequestDraft,
        source: &MailMergeDocumentState,
        current_document_flow_sha256: &str,
        limits: MailMergeLimits,
    ) -> Result<Self, MailMergeError> {
        validate_state(source, limits)?;
        if draft.schema_version != MAIL_MERGE_SCHEMA_VERSION {
            return Err(MailMergeError::InvalidSchema);
        }
        for digest in [
            &draft.expected_source_state_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        if draft.expected_source_state_sha256 != source.canonical_sha256(limits)? {
            return Err(MailMergeError::SourceStateDrift);
        }
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(MailMergeError::DocumentFlowDrift);
        }
        let _ = apply_operation(source, &draft.operation, limits)?;
        Ok(Self {
            schema_version: draft.schema_version,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        })
    }

    /// Parses strict bounded JSON and validates it against the source.
    ///
    /// # Errors
    /// Rejects empty, oversized, duplicate-key, unknown-field, invalid, or drifted input.
    pub fn from_json(
        bytes: &[u8],
        source: &MailMergeDocumentState,
        current_document_flow_sha256: &str,
        limits: MailMergeLimits,
    ) -> Result<Self, MailMergeError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(MailMergeError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft: MailMergeRequestDraft =
            serde_json::from_slice(bytes).map_err(|_| MailMergeError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }
}

impl fmt::Debug for MailMergeRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("request", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct MailMergePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: MailMergeOperation,
    seal_sha256: String,
}

impl fmt::Debug for MailMergePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergePlan")
            .field("capability_id", &self.capability_id)
            .field("plan", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct MailMergeReceipt {
    pub schema_version: &'static str,
    pub capability_id: &'static str,
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub source_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
}

impl fmt::Debug for MailMergeReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeReceipt")
            .field("capability_id", &self.capability_id)
            .field("receipt", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct MailMergeResult {
    pub state: MailMergeDocumentState,
    pub receipt: MailMergeReceipt,
}

impl fmt::Debug for MailMergeResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MailMergeResult")
            .field("capability_id", &self.receipt.capability_id)
            .field("result", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct MailMergeBuilder;

impl MailMergeBuilder {
    /// Plans one field insertion while binding the complete source and target states.
    ///
    /// # Errors
    /// Returns a validation or drift error when the request is not exact.
    pub fn plan(
        source: &MailMergeDocumentState,
        request: &MailMergeRequest,
        current_document_flow_sha256: &str,
        limits: MailMergeLimits,
    ) -> Result<MailMergePlan, MailMergeError> {
        validate_state(source, limits)?;
        require_digest(current_document_flow_sha256)?;
        if request.schema_version != MAIL_MERGE_SCHEMA_VERSION {
            return Err(MailMergeError::InvalidSchema);
        }
        let source_state_sha256 = source.canonical_sha256(limits)?;
        if request.expected_source_state_sha256 != source_state_sha256 {
            return Err(MailMergeError::SourceStateDrift);
        }
        if request.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(MailMergeError::DocumentFlowDrift);
        }
        let target = apply_operation(source, &request.operation, limits)?;
        let mut plan = MailMergePlan {
            schema_version: MAIL_MERGE_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: request.request_id.clone(),
            source_state_sha256,
            target_state_sha256: target.canonical_sha256(limits)?,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            seal_sha256: String::new(),
        };
        plan.seal_sha256 = plan_binding_sha256(&plan, limits)?;
        Ok(plan)
    }

    /// Builds the target only after rechecking the seal, source state, and document flow.
    ///
    /// # Errors
    /// Returns a tamper, validation, or drift error without partial state.
    pub fn build(
        plan: &MailMergePlan,
        source: &MailMergeDocumentState,
        current_document_flow_sha256: &str,
        limits: MailMergeLimits,
    ) -> Result<MailMergeResult, MailMergeError> {
        validate_state(source, limits)?;
        require_digest(current_document_flow_sha256)?;
        if plan.schema_version != MAIL_MERGE_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || require_digest(&plan.source_state_sha256).is_err()
            || require_digest(&plan.target_state_sha256).is_err()
            || require_digest(&plan.source_document_flow_sha256).is_err()
            || require_digest(&plan.target_document_flow_sha256).is_err()
            || require_digest(&plan.seal_sha256).is_err()
            || plan_binding_sha256(plan, limits)? != plan.seal_sha256
        {
            return Err(MailMergeError::PlanTampered);
        }
        if source.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(MailMergeError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(MailMergeError::DocumentFlowDrift);
        }
        let state = apply_operation(source, &plan.operation, limits)?;
        if state.canonical_sha256(limits)? != plan.target_state_sha256 {
            return Err(MailMergeError::PlanTampered);
        }
        Ok(MailMergeResult {
            state,
            receipt: MailMergeReceipt {
                schema_version: MAIL_MERGE_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                source_state_sha256: plan.source_state_sha256.clone(),
                target_state_sha256: plan.target_state_sha256.clone(),
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
            },
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum MailMergeError {
    #[error("invalid mail-merge limit")]
    InvalidLimit,
    #[error("mail-merge input exceeds limit")]
    InputLimit,
    #[error("invalid mail-merge JSON")]
    InvalidJson,
    #[error("invalid mail-merge schema")]
    InvalidSchema,
    #[error("invalid mail-merge identity")]
    InvalidIdentity,
    #[error("mail-merge data source is missing or ambiguous")]
    SourceMissing,
    #[error("mail-merge column is missing or ambiguous")]
    ColumnMissing,
    #[error("mail-merge data source is unsafe or invalid")]
    InvalidDataSource,
    #[error("mail-merge field is invalid")]
    InvalidField,
    #[error("mail-merge native binding is invalid")]
    InvalidNativeBinding,
    #[error("mail-merge field name conflicts with existing state")]
    FieldNameConflict,
    #[error("mail-merge mutation is protected")]
    Protected,
    #[error("mail-merge source state drifted")]
    SourceStateDrift,
    #[error("mail-merge document flow drifted")]
    DocumentFlowDrift,
    #[error("mail-merge plan was tampered")]
    PlanTampered,
    #[error("mail-merge serialization failed")]
    Serialization,
    #[error("mail-merge output exceeds limit")]
    OutputLimit,
}

impl MailMergeError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "mail_merge_invalid_limit",
            Self::InputLimit => "mail_merge_input_limit",
            Self::InvalidJson => "mail_merge_invalid_json",
            Self::InvalidSchema => "mail_merge_invalid_schema",
            Self::InvalidIdentity => "mail_merge_invalid_identity",
            Self::SourceMissing => "mail_merge_source_missing",
            Self::ColumnMissing => "mail_merge_column_missing",
            Self::InvalidDataSource => "mail_merge_invalid_data_source",
            Self::InvalidField => "mail_merge_invalid_field",
            Self::InvalidNativeBinding => "mail_merge_invalid_native_binding",
            Self::FieldNameConflict => "mail_merge_field_name_conflict",
            Self::Protected => "mail_merge_protected",
            Self::SourceStateDrift => "mail_merge_source_state_drift",
            Self::DocumentFlowDrift => "mail_merge_document_flow_drift",
            Self::PlanTampered => "mail_merge_plan_tampered",
            Self::Serialization => "mail_merge_serialization",
            Self::OutputLimit => "mail_merge_output_limit",
        }
    }
}

fn apply_operation(
    source: &MailMergeDocumentState,
    operation: &MailMergeOperation,
    limits: MailMergeLimits,
) -> Result<MailMergeDocumentState, MailMergeError> {
    validate_state(source, limits)?;
    if source.document_locked {
        return Err(MailMergeError::Protected);
    }
    let mut target = source.clone();
    match operation {
        MailMergeOperation::FieldInsert {
            insertion_index,
            field,
        } => {
            if *insertion_index > target.fields.len() {
                return Err(MailMergeError::InvalidIdentity);
            }
            let data_source = select_source(&target.data_sources, &field.logical_source_id)?;
            validate_field(field, data_source, &target.sections, limits)?;
            if field.cache.status != MailMergeCacheStatus::Current {
                return Err(MailMergeError::InvalidField);
            }
            ensure_section_unlocked(&target.sections, &field.anchor.section_id)?;
            target
                .fields
                .insert(*insertion_index, field.as_ref().clone());
        }
    }
    validate_state(&target, limits)?;
    Ok(target)
}

fn validate_state(
    state: &MailMergeDocumentState,
    limits: MailMergeLimits,
) -> Result<(), MailMergeError> {
    if state.schema_version != MAIL_MERGE_SCHEMA_VERSION
        || state.sections.is_empty()
        || state.sections.len() > limits.0.sections
        || state.data_sources.len() > limits.0.data_sources
        || state.fields.len() > limits.0.fields
        || state.occupied_non_mailmerge_control_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_mailmerge_field_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_mailmerge_field_name_sha256.len() > limits.0.occupied_native_ids
    {
        return Err(MailMergeError::InvalidIdentity);
    }
    validate_sorted_ids(&state.occupied_non_mailmerge_control_ids)?;
    validate_sorted_ids(&state.occupied_non_mailmerge_field_ids)?;
    validate_sorted_digests(&state.occupied_non_mailmerge_field_name_sha256)?;
    for digest in [
        &state.preview_inventory_sha256,
        &state.batch_output_inventory_sha256,
        &state.label_layout_catalog_sha256,
        &state.non_mailmerge_content_sha256,
        &state.unrelated_field_inventory_sha256,
        &state.reference_inventory_sha256,
        &state.note_inventory_sha256,
        &state.toc_index_inventory_sha256,
        &state.citation_inventory_sha256,
        &state.object_inventory_sha256,
        &state.numbering_inventory_sha256,
        &state.style_catalog_sha256,
        &state.relationship_inventory_sha256,
        &state.resource_inventory_sha256,
        &state.document_protection_sha256,
        &state.opaque_document_state_sha256,
    ] {
        require_digest(digest)?;
    }
    let mut section_ids = BTreeSet::new();
    for section in &state.sections {
        if section.paragraph_count == 0 || !section_ids.insert(&section.section_id) {
            return Err(MailMergeError::InvalidIdentity);
        }
        for digest in [
            &section.run_topology_sha256,
            &section.inline_topology_sha256,
            &section.page_assignment_sha256,
            &section.opaque_section_state_sha256,
        ] {
            require_digest(digest)?;
        }
    }
    let mut source_ids = BTreeSet::new();
    for source in &state.data_sources {
        if !source_ids.insert(&source.logical_source_id) {
            return Err(MailMergeError::InvalidDataSource);
        }
        validate_source(source, limits)?;
    }
    let mut logical_field_ids = BTreeSet::new();
    let mut control_ids = state
        .occupied_non_mailmerge_control_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let mut field_ids = state
        .occupied_non_mailmerge_field_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let mut field_names = state
        .occupied_non_mailmerge_field_name_sha256
        .iter()
        .collect::<BTreeSet<_>>();
    for field in &state.fields {
        let source = select_source(&state.data_sources, &field.logical_source_id)?;
        validate_field(field, source, &state.sections, limits)?;
        if !logical_field_ids.insert(&field.logical_field_id)
            || !control_ids.insert(field.begin_control_id)
            || !field_ids.insert(field.field_id)
        {
            return Err(MailMergeError::InvalidIdentity);
        }
        if field
            .native_pair
            .field_name_sha256
            .as_ref()
            .is_some_and(|name| !field_names.insert(name))
        {
            return Err(MailMergeError::FieldNameConflict);
        }
    }
    Ok(())
}

fn validate_source(
    source: &MailMergeDataSource,
    limits: MailMergeLimits,
) -> Result<(), MailMergeError> {
    if !source.encrypted_artifact
        || source.columns.is_empty()
        || source.columns.len() > limits.0.columns_per_source
        || source.record_count > limits.0.records_per_source
        || !valid_locale(&source.locale)
    {
        return Err(MailMergeError::InvalidDataSource);
    }
    for digest in [
        &source.artifact_sha256,
        &source.encryption_envelope_sha256,
        &source.provider_id_sha256,
        &source.provider_version_sha256,
        &source.schema_sha256,
        &source.row_identity_manifest_sha256,
        &source.access_policy_sha256,
        &source.pii_policy_sha256,
    ] {
        require_digest(digest).map_err(|_| MailMergeError::InvalidDataSource)?;
    }
    validate_opaque(&source.opaque_properties, limits)
        .map_err(|_| MailMergeError::InvalidDataSource)?;
    let mut column_ids = BTreeSet::new();
    let mut provider_keys = BTreeSet::new();
    for column in &source.columns {
        if !column_ids.insert(&column.logical_column_id)
            || !provider_keys.insert(&column.provider_column_key_sha256)
        {
            return Err(MailMergeError::InvalidDataSource);
        }
        for digest in [
            &column.provider_column_key_sha256,
            &column.display_name_sha256,
            &column.semantic_definition_sha256,
            &column.format_sha256,
        ] {
            require_digest(digest).map_err(|_| MailMergeError::InvalidDataSource)?;
        }
        validate_opaque(&column.opaque_properties, limits)
            .map_err(|_| MailMergeError::InvalidDataSource)?;
    }
    Ok(())
}

fn validate_field(
    field: &MailMergeFieldNode,
    source: &MailMergeDataSource,
    sections: &[MailMergeSectionState],
    limits: MailMergeLimits,
) -> Result<(), MailMergeError> {
    if field.begin_control_id == 0
        || field.field_id == 0
        || field.native_pair.begin_tag != MailMergeNativeBeginTag::FieldBegin
        || field.native_pair.end_tag != MailMergeNativeEndTag::FieldEnd
        || field.native_pair.field_type != MailMergeFieldType::Mailmerge
        || field.native_pair.semantic_binding != MailMergeSemanticBinding::UnverifiedFieldParameters
        || field.native_pair.end_begin_control_id_ref != field.begin_control_id
        || field.native_pair.end_field_id != field.field_id
        || field.native_pair.z_order < -1
    {
        return Err(MailMergeError::InvalidNativeBinding);
    }
    validate_anchor(&field.anchor, sections)?;
    let _ = select_column(source, &field.logical_column_id)?;
    for digest in [
        Some(field.cache.binding_projection_sha256.as_str()),
        Some(field.cache.placeholder_text_sha256.as_str()),
        field.native_pair.field_name_sha256.as_deref(),
        Some(field.native_pair.parameters_sha256.as_str()),
        field.native_pair.sub_list_sha256.as_deref(),
        field.native_pair.meta_tag_sha256.as_deref(),
        Some(field.native_pair.opaque_begin_state_sha256.as_str()),
        Some(field.native_pair.opaque_end_state_sha256.as_str()),
        Some(field.opaque_field_state_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest)?;
    }
    validate_opaque(&field.opaque_properties, limits)?;
    let projection =
        MailMergeFieldNode::projection_sha256(source, &field.logical_column_id, limits)?;
    let expected = if projection == field.cache.binding_projection_sha256 {
        MailMergeCacheStatus::Current
    } else {
        MailMergeCacheStatus::Stale
    };
    if field.cache.status != expected {
        return Err(MailMergeError::InvalidField);
    }
    Ok(())
}

fn select_source<'a>(
    sources: &'a [MailMergeDataSource],
    source_id: &LogicalId,
) -> Result<&'a MailMergeDataSource, MailMergeError> {
    let mut matches = sources
        .iter()
        .filter(|source| source.logical_source_id == *source_id);
    let source = matches.next().ok_or(MailMergeError::SourceMissing)?;
    if matches.next().is_some() {
        return Err(MailMergeError::SourceMissing);
    }
    Ok(source)
}

fn select_column<'a>(
    source: &'a MailMergeDataSource,
    column_id: &LogicalId,
) -> Result<&'a MailMergeColumn, MailMergeError> {
    let mut matches = source
        .columns
        .iter()
        .filter(|column| column.logical_column_id == *column_id);
    let column = matches.next().ok_or(MailMergeError::ColumnMissing)?;
    if matches.next().is_some() {
        return Err(MailMergeError::ColumnMissing);
    }
    Ok(column)
}

fn validate_anchor(
    anchor: &LinkAnchor,
    sections: &[MailMergeSectionState],
) -> Result<(), MailMergeError> {
    let mut matches = sections
        .iter()
        .filter(|section| section.section_id == anchor.section_id);
    let section = matches.next().ok_or(MailMergeError::InvalidIdentity)?;
    if matches.next().is_some()
        || anchor.start > anchor.end
        || anchor.start.paragraph_ordinal >= section.paragraph_count
        || anchor.end.paragraph_ordinal >= section.paragraph_count
    {
        return Err(MailMergeError::InvalidIdentity);
    }
    Ok(())
}

fn ensure_section_unlocked(
    sections: &[MailMergeSectionState],
    section_id: &LogicalId,
) -> Result<(), MailMergeError> {
    let mut matches = sections
        .iter()
        .filter(|section| section.section_id == *section_id);
    let section = matches.next().ok_or(MailMergeError::InvalidIdentity)?;
    if matches.next().is_some() {
        return Err(MailMergeError::InvalidIdentity);
    }
    if section.locked {
        return Err(MailMergeError::Protected);
    }
    Ok(())
}

fn validate_sorted_ids(ids: &[u32]) -> Result<(), MailMergeError> {
    if ids.first().is_some_and(|id| *id == 0) || ids.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(MailMergeError::InvalidIdentity);
    }
    Ok(())
}

fn validate_sorted_digests(digests: &[String]) -> Result<(), MailMergeError> {
    for digest in digests {
        require_digest(digest)?;
    }
    if digests.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(MailMergeError::InvalidIdentity);
    }
    Ok(())
}

fn validate_opaque(
    properties: &[OpaqueLinkProperty],
    limits: MailMergeLimits,
) -> Result<(), MailMergeError> {
    if properties.len() > limits.0.opaque_entries {
        return Err(MailMergeError::InvalidField);
    }
    let mut keys = BTreeSet::new();
    for property in properties {
        if !valid_token(&property.namespace)
            || !valid_token(&property.name)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(MailMergeError::InvalidField);
        }
    }
    Ok(())
}

fn valid_token(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 1024
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
}

fn valid_locale(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 35
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
}

fn require_digest(value: &str) -> Result<(), MailMergeError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(MailMergeError::InvalidField);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &MailMergePlan,
    limits: MailMergeLimits,
) -> Result<String, MailMergeError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a MailMergeOperation,
    }
    Ok(hex(Sha256::digest(serialize_bounded(
        &Binding {
            schema_version: plan.schema_version,
            capability_id: plan.capability_id,
            request_id: &plan.request_id,
            source_state_sha256: &plan.source_state_sha256,
            target_state_sha256: &plan.target_state_sha256,
            source_document_flow_sha256: &plan.source_document_flow_sha256,
            target_document_flow_sha256: &plan.target_document_flow_sha256,
            operation: &plan.operation,
        },
        limits,
    )?)
    .into()))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: MailMergeLimits,
) -> Result<Vec<u8>, MailMergeError> {
    let bytes = serde_json::to_vec(value).map_err(|_| MailMergeError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(MailMergeError::OutputLimit);
    }
    Ok(bytes)
}

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut value = String::with_capacity(64);
    for byte in bytes {
        value.push(char::from(DIGITS[usize::from(byte >> 4)]));
        value.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    value
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), MailMergeError> {
    struct DuplicateVisitor;
    impl<'de> Visitor<'de> for DuplicateVisitor {
        type Value = ();
        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
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
        fn visit_string<E>(self, _value: String) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }
        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
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
        .map_err(|_| MailMergeError::InvalidJson)?;
    deserializer.end().map_err(|_| MailMergeError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod private_tests {
    use super::*;
    use crate::LinkPoint;

    const D: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn id(value: &str) -> LogicalId {
        LogicalId::parse(value).expect("id")
    }

    fn limits() -> MailMergeLimits {
        MailMergeLimits::new(MailMergeLimitConfig::default()).expect("limits")
    }

    fn source() -> MailMergeDocumentState {
        MailMergeDocumentState::from_draft(
            MailMergeDocumentStateDraft {
                schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
                sections: vec![MailMergeSectionState {
                    section_id: id("section-1"),
                    paragraph_count: 1,
                    run_topology_sha256: D.to_owned(),
                    inline_topology_sha256: D.to_owned(),
                    page_assignment_sha256: D.to_owned(),
                    opaque_section_state_sha256: D.to_owned(),
                    locked: false,
                }],
                data_sources: vec![MailMergeDataSource {
                    logical_source_id: id("source-1"),
                    artifact_sha256: D.to_owned(),
                    encryption_envelope_sha256: D.to_owned(),
                    provider_id_sha256: D.to_owned(),
                    provider_version_sha256: D.to_owned(),
                    locale: "ko-KR".to_owned(),
                    schema_sha256: D.to_owned(),
                    row_identity_manifest_sha256: D.to_owned(),
                    record_count: 1,
                    access_policy_sha256: D.to_owned(),
                    pii_policy_sha256: D.to_owned(),
                    encrypted_artifact: true,
                    columns: vec![MailMergeColumn {
                        logical_column_id: id("column-1"),
                        provider_column_key_sha256: D.to_owned(),
                        display_name_sha256: D.to_owned(),
                        column_type: MailMergeColumnType::Text,
                        nullable: false,
                        sensitivity: MailMergeSensitivity::Personal,
                        semantic_definition_sha256: D.to_owned(),
                        format_sha256: D.to_owned(),
                        opaque_properties: Vec::new(),
                        locked: false,
                    }],
                    opaque_properties: Vec::new(),
                    locked: false,
                }],
                fields: Vec::new(),
                occupied_non_mailmerge_control_ids: Vec::new(),
                occupied_non_mailmerge_field_ids: Vec::new(),
                occupied_non_mailmerge_field_name_sha256: Vec::new(),
                preview_inventory_sha256: D.to_owned(),
                batch_output_inventory_sha256: D.to_owned(),
                label_layout_catalog_sha256: D.to_owned(),
                non_mailmerge_content_sha256: D.to_owned(),
                unrelated_field_inventory_sha256: D.to_owned(),
                reference_inventory_sha256: D.to_owned(),
                note_inventory_sha256: D.to_owned(),
                toc_index_inventory_sha256: D.to_owned(),
                citation_inventory_sha256: D.to_owned(),
                object_inventory_sha256: D.to_owned(),
                numbering_inventory_sha256: D.to_owned(),
                style_catalog_sha256: D.to_owned(),
                relationship_inventory_sha256: D.to_owned(),
                resource_inventory_sha256: D.to_owned(),
                document_protection_sha256: D.to_owned(),
                opaque_document_state_sha256: D.to_owned(),
                document_locked: false,
            },
            limits(),
        )
        .expect("state")
    }

    fn field(source: &MailMergeDataSource) -> MailMergeFieldNode {
        let column_id = id("column-1");
        MailMergeFieldNode {
            logical_field_id: id("field-1"),
            begin_control_id: 1,
            field_id: 2,
            anchor: LinkAnchor {
                section_id: id("section-1"),
                start: LinkPoint {
                    paragraph_ordinal: 0,
                    run_ordinal: 0,
                    inline_ordinal: 0,
                },
                end: LinkPoint {
                    paragraph_ordinal: 0,
                    run_ordinal: 0,
                    inline_ordinal: 0,
                },
            },
            logical_source_id: id("source-1"),
            logical_column_id: column_id.clone(),
            cache: MailMergeFieldCache {
                binding_projection_sha256: MailMergeFieldNode::projection_sha256(
                    source,
                    &column_id,
                    limits(),
                )
                .expect("projection"),
                placeholder_text_sha256: D.to_owned(),
                status: MailMergeCacheStatus::Current,
            },
            native_pair: MailMergeNativePair {
                begin_tag: MailMergeNativeBeginTag::FieldBegin,
                end_tag: MailMergeNativeEndTag::FieldEnd,
                field_type: MailMergeFieldType::Mailmerge,
                semantic_binding: MailMergeSemanticBinding::UnverifiedFieldParameters,
                end_begin_control_id_ref: 1,
                end_field_id: 2,
                field_name_sha256: None,
                editable: true,
                dirty: false,
                z_order: -1,
                parameters_sha256: D.to_owned(),
                sub_list_sha256: None,
                meta_tag_sha256: None,
                opaque_begin_state_sha256: D.to_owned(),
                opaque_end_state_sha256: D.to_owned(),
            },
            opaque_field_state_sha256: D.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    #[test]
    fn private_plan_tampering_is_rejected() {
        let source = source();
        let request = MailMergeRequest::from_draft(
            MailMergeRequestDraft {
                schema_version: MAIL_MERGE_SCHEMA_VERSION.to_owned(),
                request_id: id("request-1"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: D.to_owned(),
                target_document_flow_sha256: D.to_owned(),
                operation: MailMergeOperation::FieldInsert {
                    insertion_index: 0,
                    field: Box::new(field(&source.data_sources[0])),
                },
            },
            &source,
            D,
            limits(),
        )
        .expect("request");
        let mut plan = MailMergeBuilder::plan(&source, &request, D, limits()).expect("plan");
        plan.target_document_flow_sha256 =
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".to_owned();
        assert_eq!(
            MailMergeBuilder::build(&plan, &source, D, limits()).expect_err("tamper"),
            MailMergeError::PlanTampered
        );
    }
}
