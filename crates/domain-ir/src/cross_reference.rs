use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LinkAnchor, LogicalId, OpaqueLinkProperty};

pub const CROSS_REFERENCE_SCHEMA_VERSION: &str = "hwpx-agent.cross-reference/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CrossReferenceLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub sections: usize,
    pub targets: usize,
    pub cross_references: usize,
    pub dependencies: usize,
    pub occupied_native_ids: usize,
    pub opaque_entries: usize,
}

impl Default for CrossReferenceLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            sections: 4096,
            targets: 1_000_000,
            cross_references: 1_000_000,
            dependencies: 65_536,
            occupied_native_ids: 1_000_000,
            opaque_entries: 4096,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CrossReferenceLimits(CrossReferenceLimitConfig);

impl CrossReferenceLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_DEPENDENCIES: usize = 65_536;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 65_536;

    /// Creates finite limits without silently clamping any value.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding limits.
    pub fn new(config: CrossReferenceLimitConfig) -> Result<Self, CrossReferenceError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.sections == 0
            || config.sections > Self::HARD_MAX_ITEMS
            || config.targets == 0
            || config.targets > Self::HARD_MAX_ITEMS
            || config.cross_references == 0
            || config.cross_references > Self::HARD_MAX_ITEMS
            || config.dependencies == 0
            || config.dependencies > Self::HARD_MAX_DEPENDENCIES
            || config.occupied_native_ids == 0
            || config.occupied_native_ids > Self::HARD_MAX_ITEMS
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
        {
            return Err(CrossReferenceError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> CrossReferenceLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossReferenceTargetKind {
    Bookmark,
    Heading,
    NumberedParagraph,
    Caption,
    Footnote,
    Endnote,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossReferenceDisplayKind {
    TargetText,
    TargetName,
    NumberOnly,
    LabelAndNumber,
    PageNumber,
    RelativePosition,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossReferenceUpdatePolicy {
    PreserveCached,
    RecomputeAutomation,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossReferenceCacheStatus {
    Current,
    Stale,
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceTargetIdentity {
    pub logical_target_id: LogicalId,
}

impl fmt::Debug for CrossReferenceTargetIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CrossReferenceTargetIdentity(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceTarget {
    pub identity: CrossReferenceTargetIdentity,
    pub kind: CrossReferenceTargetKind,
    pub anchor: LinkAnchor,
    pub semantic_name_sha256: String,
    pub source_text_sha256: String,
    pub label_sha256: Option<String>,
    pub numbering_sha256: Option<String>,
    pub page_assignment_sha256: String,
    pub dependency_target_ids: Vec<LogicalId>,
    pub opaque_target_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl CrossReferenceTarget {
    /// Computes the exact target projection used to classify a cached display value.
    ///
    /// # Errors
    ///
    /// Rejects an incompatible display kind, malformed digest, or oversized projection.
    pub fn projection_sha256(
        &self,
        display_kind: CrossReferenceDisplayKind,
        reference_anchor: &LinkAnchor,
        limits: CrossReferenceLimits,
    ) -> Result<String, CrossReferenceError> {
        #[derive(Serialize)]
        struct Projection<'a> {
            kind: CrossReferenceTargetKind,
            display_kind: CrossReferenceDisplayKind,
            semantic_name_sha256: Option<&'a str>,
            source_text_sha256: Option<&'a str>,
            label_sha256: Option<&'a str>,
            numbering_sha256: Option<&'a str>,
            page_assignment_sha256: Option<&'a str>,
            target_anchor: Option<&'a LinkAnchor>,
            reference_anchor: Option<&'a LinkAnchor>,
        }

        validate_target_payload(self, limits)?;
        validate_display_kind(self, display_kind)?;
        let mut projection = Projection {
            kind: self.kind,
            display_kind,
            semantic_name_sha256: None,
            source_text_sha256: None,
            label_sha256: None,
            numbering_sha256: None,
            page_assignment_sha256: None,
            target_anchor: None,
            reference_anchor: None,
        };
        match display_kind {
            CrossReferenceDisplayKind::TargetText => {
                projection.source_text_sha256 = Some(&self.source_text_sha256);
            }
            CrossReferenceDisplayKind::TargetName => {
                projection.semantic_name_sha256 = Some(&self.semantic_name_sha256);
            }
            CrossReferenceDisplayKind::NumberOnly => {
                projection.numbering_sha256 = self.numbering_sha256.as_deref();
            }
            CrossReferenceDisplayKind::LabelAndNumber => {
                projection.label_sha256 = self.label_sha256.as_deref();
                projection.numbering_sha256 = self.numbering_sha256.as_deref();
            }
            CrossReferenceDisplayKind::PageNumber => {
                projection.page_assignment_sha256 = Some(&self.page_assignment_sha256);
            }
            CrossReferenceDisplayKind::RelativePosition => {
                projection.target_anchor = Some(&self.anchor);
                projection.reference_anchor = Some(reference_anchor);
            }
        }
        Ok(hex(
            Sha256::digest(serialize_bounded(&projection, limits)?).into()
        ))
    }
}

impl fmt::Debug for CrossReferenceTarget {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceTarget")
            .field("kind", &self.kind)
            .field("dependency_count", &self.dependency_target_ids.len())
            .field("locked", &self.locked)
            .field("target", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceIdentity {
    pub logical_cross_reference_id: LogicalId,
    pub begin_control_id: u32,
    pub field_id: u32,
}

impl fmt::Debug for CrossReferenceIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CrossReferenceIdentity(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossReferenceNativeBeginTag {
    FieldBegin,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossReferenceNativeEndTag {
    FieldEnd,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossReferenceFieldType {
    Crossref,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CrossReferenceSemanticBinding {
    UnverifiedFieldParameters,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceNativePair {
    pub begin_tag: CrossReferenceNativeBeginTag,
    pub end_tag: CrossReferenceNativeEndTag,
    pub field_type: CrossReferenceFieldType,
    pub semantic_binding: CrossReferenceSemanticBinding,
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

impl fmt::Debug for CrossReferenceNativePair {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceNativePair")
            .field("editable", &self.editable)
            .field("dirty", &self.dirty)
            .field("native", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceCache {
    pub target_projection_sha256: String,
    pub display_value_sha256: String,
    pub status: CrossReferenceCacheStatus,
}

impl fmt::Debug for CrossReferenceCache {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceCache")
            .field("status", &self.status)
            .field("cache", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceEntry {
    pub identity: CrossReferenceIdentity,
    pub anchor: LinkAnchor,
    pub containing_target_id: Option<LogicalId>,
    pub target_id: LogicalId,
    pub display_kind: CrossReferenceDisplayKind,
    pub update_policy: CrossReferenceUpdatePolicy,
    pub cache: CrossReferenceCache,
    pub native_pair: CrossReferenceNativePair,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for CrossReferenceEntry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceEntry")
            .field("display_kind", &self.display_kind)
            .field("update_policy", &self.update_policy)
            .field("cache_status", &self.cache.status)
            .field("locked", &self.locked)
            .field("reference", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceSectionState {
    pub section_id: LogicalId,
    pub paragraph_count: u32,
    pub run_topology_sha256: String,
    pub inline_topology_sha256: String,
    pub opaque_section_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for CrossReferenceSectionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceSectionState")
            .field("paragraph_count", &self.paragraph_count)
            .field("locked", &self.locked)
            .field("section", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceDocumentStateDraft {
    pub schema_version: String,
    pub sections: Vec<CrossReferenceSectionState>,
    pub targets: Vec<CrossReferenceTarget>,
    pub cross_references: Vec<CrossReferenceEntry>,
    pub occupied_non_cross_reference_begin_control_ids: Vec<u32>,
    pub occupied_non_cross_reference_field_ids: Vec<u32>,
    pub occupied_non_cross_reference_field_name_sha256: Vec<String>,
    pub non_cross_reference_content_sha256: String,
    pub unrelated_field_inventory_sha256: String,
    pub bookmark_inventory_sha256: String,
    pub note_inventory_sha256: String,
    pub object_inventory_sha256: String,
    pub numbering_inventory_sha256: String,
    pub style_catalog_sha256: String,
    pub relationship_inventory_sha256: String,
    pub resource_inventory_sha256: String,
    pub document_protection_sha256: String,
    pub opaque_document_state_sha256: String,
    pub document_locked: bool,
}

impl fmt::Debug for CrossReferenceDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CrossReferenceDocumentStateDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CrossReferenceDocumentState {
    schema_version: &'static str,
    sections: Vec<CrossReferenceSectionState>,
    targets: Vec<CrossReferenceTarget>,
    cross_references: Vec<CrossReferenceEntry>,
    occupied_non_cross_reference_begin_control_ids: Vec<u32>,
    occupied_non_cross_reference_field_ids: Vec<u32>,
    occupied_non_cross_reference_field_name_sha256: Vec<String>,
    non_cross_reference_content_sha256: String,
    unrelated_field_inventory_sha256: String,
    bookmark_inventory_sha256: String,
    note_inventory_sha256: String,
    object_inventory_sha256: String,
    numbering_inventory_sha256: String,
    style_catalog_sha256: String,
    relationship_inventory_sha256: String,
    resource_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
    document_locked: bool,
}

impl CrossReferenceDocumentState {
    /// Validates and seals the complete target graph and cross-reference inventory.
    ///
    /// # Errors
    ///
    /// Rejects malformed, dangling, cyclic, stale-status, collision, digest, protection, or limit state.
    pub fn from_draft(
        draft: CrossReferenceDocumentStateDraft,
        limits: CrossReferenceLimits,
    ) -> Result<Self, CrossReferenceError> {
        if draft.schema_version != CROSS_REFERENCE_SCHEMA_VERSION {
            return Err(CrossReferenceError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: CROSS_REFERENCE_SCHEMA_VERSION,
            sections: draft.sections,
            targets: draft.targets,
            cross_references: draft.cross_references,
            occupied_non_cross_reference_begin_control_ids: draft
                .occupied_non_cross_reference_begin_control_ids,
            occupied_non_cross_reference_field_ids: draft.occupied_non_cross_reference_field_ids,
            occupied_non_cross_reference_field_name_sha256: draft
                .occupied_non_cross_reference_field_name_sha256,
            non_cross_reference_content_sha256: draft.non_cross_reference_content_sha256,
            unrelated_field_inventory_sha256: draft.unrelated_field_inventory_sha256,
            bookmark_inventory_sha256: draft.bookmark_inventory_sha256,
            note_inventory_sha256: draft.note_inventory_sha256,
            object_inventory_sha256: draft.object_inventory_sha256,
            numbering_inventory_sha256: draft.numbering_inventory_sha256,
            style_catalog_sha256: draft.style_catalog_sha256,
            relationship_inventory_sha256: draft.relationship_inventory_sha256,
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
    pub fn targets(&self) -> &[CrossReferenceTarget] {
        &self.targets
    }

    #[must_use]
    pub fn cross_references(&self) -> &[CrossReferenceEntry] {
        &self.cross_references
    }

    /// Serializes the complete state deterministically within its configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: CrossReferenceLimits,
    ) -> Result<Vec<u8>, CrossReferenceError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_sha256(
        &self,
        limits: CrossReferenceLimits,
    ) -> Result<String, CrossReferenceError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for CrossReferenceDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceDocumentState")
            .field("section_count", &self.sections.len())
            .field("target_count", &self.targets.len())
            .field("reference_count", &self.cross_references.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum CrossReferenceOperation {
    Insert {
        insertion_index: usize,
        cross_reference: Box<CrossReferenceEntry>,
    },
}

impl CrossReferenceOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        "ref.crossref_insert"
    }
}

impl fmt::Debug for CrossReferenceOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CrossReferenceRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: CrossReferenceOperation,
}

impl fmt::Debug for CrossReferenceRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CrossReferenceRequestDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CrossReferenceRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: CrossReferenceOperation,
}

impl CrossReferenceRequest {
    /// Strictly parses and validates a bounded request against current state and flow.
    ///
    /// # Errors
    ///
    /// Rejects duplicate or unknown JSON keys, drift, invalid insertion, or limits.
    pub fn from_json(
        bytes: &[u8],
        source: &CrossReferenceDocumentState,
        current_document_flow_sha256: &str,
        limits: CrossReferenceLimits,
    ) -> Result<Self, CrossReferenceError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(CrossReferenceError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft: CrossReferenceRequestDraft =
            serde_json::from_slice(bytes).map_err(|_| CrossReferenceError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    /// Validates a typed request against current state and flow.
    ///
    /// # Errors
    ///
    /// Rejects version, state/flow drift, malformed digests, or invalid insertion.
    pub fn from_draft(
        draft: CrossReferenceRequestDraft,
        source: &CrossReferenceDocumentState,
        current_document_flow_sha256: &str,
        limits: CrossReferenceLimits,
    ) -> Result<Self, CrossReferenceError> {
        if draft.schema_version != CROSS_REFERENCE_SCHEMA_VERSION {
            return Err(CrossReferenceError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        if source.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(CrossReferenceError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(CrossReferenceError::DocumentFlowDrift);
        }
        let request = Self {
            schema_version: CROSS_REFERENCE_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = apply_operation(source, &request.operation, limits)?;
        Ok(request)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.operation.capability_id()
    }
}

impl fmt::Debug for CrossReferenceRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceRequest")
            .field("capability_id", &self.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CrossReferencePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: CrossReferenceOperation,
    target_state: CrossReferenceDocumentState,
    seal_sha256: String,
}

impl CrossReferencePlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn target_state(&self) -> &CrossReferenceDocumentState {
        &self.target_state
    }
}

impl fmt::Debug for CrossReferencePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferencePlan")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct CrossReferenceBuilder;

impl CrossReferenceBuilder {
    /// Builds a sealed exact-state insertion plan.
    ///
    /// # Errors
    ///
    /// Rechecks source/flow drift and rejects invalid, protected, dangling, cyclic, or stale inserts.
    pub fn plan(
        source: &CrossReferenceDocumentState,
        request: &CrossReferenceRequest,
        current_document_flow_sha256: &str,
        limits: CrossReferenceLimits,
    ) -> Result<CrossReferencePlan, CrossReferenceError> {
        if source.canonical_sha256(limits)? != request.expected_source_state_sha256 {
            return Err(CrossReferenceError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(CrossReferenceError::DocumentFlowDrift);
        }
        let target_state = apply_operation(source, &request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = CrossReferencePlan {
            schema_version: CROSS_REFERENCE_SCHEMA_VERSION,
            capability_id: request.capability_id(),
            request_id: request.request_id.clone(),
            source_state_sha256: request.expected_source_state_sha256.clone(),
            target_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            target_state,
            seal_sha256: String::new(),
        };
        plan.seal_sha256 = plan_binding_sha256(&plan, limits)?;
        Ok(plan)
    }

    /// Rechecks and materializes a sealed exact-state insertion plan.
    ///
    /// # Errors
    ///
    /// Rejects plan tampering, source/flow drift, or recomputed target mismatch.
    pub fn build(
        plan: &CrossReferencePlan,
        current: &CrossReferenceDocumentState,
        current_document_flow_sha256: &str,
        limits: CrossReferenceLimits,
    ) -> Result<CrossReferenceResult, CrossReferenceError> {
        if plan.schema_version != CROSS_REFERENCE_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan.seal_sha256 != plan_binding_sha256(plan, limits)?
        {
            return Err(CrossReferenceError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(CrossReferenceError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(CrossReferenceError::DocumentFlowDrift);
        }
        let rebuilt = apply_operation(current, &plan.operation, limits)?;
        if rebuilt != plan.target_state
            || rebuilt.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(CrossReferenceError::PlanTampered);
        }
        Ok(CrossReferenceResult {
            state: rebuilt,
            receipt: CrossReferenceReceipt {
                schema_version: CROSS_REFERENCE_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                request_id: plan.request_id.clone(),
                source_state_sha256: plan.source_state_sha256.clone(),
                target_state_sha256: plan.target_state_sha256.clone(),
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                plan_sha256: plan.seal_sha256.clone(),
            },
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CrossReferenceReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for CrossReferenceReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CrossReferenceResult {
    pub state: CrossReferenceDocumentState,
    pub receipt: CrossReferenceReceipt,
}

impl fmt::Debug for CrossReferenceResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CrossReferenceResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum CrossReferenceError {
    #[error("cross-reference limits are invalid")]
    InvalidLimit,
    #[error("cross-reference input exceeds a finite limit")]
    InputLimit,
    #[error("cross-reference JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("cross-reference schema version is unsupported")]
    UnsupportedVersion,
    #[error("cross-reference identity or anchor is invalid")]
    InvalidIdentity,
    #[error("cross-reference target is missing, duplicated, or incompatible")]
    InvalidTarget,
    #[error("cross-reference target graph contains a cycle")]
    ReferenceCycle,
    #[error("cross-reference native binding is unsupported or inconsistent")]
    InvalidNativeBinding,
    #[error("cross-reference field name collides with an occupied field name")]
    FieldNameConflict,
    #[error("cross-reference cache or update state is inconsistent")]
    InvalidCache,
    #[error("cross-reference digest or opaque property is invalid")]
    InvalidPayload,
    #[error("cross-reference insertion index is invalid")]
    InvalidInsertionIndex,
    #[error("cross-reference target, section, or document is protected")]
    Protected,
    #[error("cross-reference source state drifted")]
    SourceStateDrift,
    #[error("cross-reference document flow drifted")]
    DocumentFlowDrift,
    #[error("cross-reference plan was tampered with")]
    PlanTampered,
    #[error("cross-reference serialization failed")]
    Serialization,
    #[error("cross-reference serialized output exceeds a finite limit")]
    OutputLimit,
}

impl CrossReferenceError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "cross_reference_invalid_limit",
            Self::InputLimit => "cross_reference_input_limit",
            Self::InvalidJson => "cross_reference_invalid_json",
            Self::UnsupportedVersion => "cross_reference_unsupported_version",
            Self::InvalidIdentity => "cross_reference_invalid_identity",
            Self::InvalidTarget => "cross_reference_invalid_target",
            Self::ReferenceCycle => "cross_reference_cycle",
            Self::InvalidNativeBinding => "cross_reference_invalid_native_binding",
            Self::FieldNameConflict => "cross_reference_field_name_conflict",
            Self::InvalidCache => "cross_reference_invalid_cache",
            Self::InvalidPayload => "cross_reference_invalid_payload",
            Self::InvalidInsertionIndex => "cross_reference_invalid_insertion_index",
            Self::Protected => "cross_reference_protected",
            Self::SourceStateDrift => "cross_reference_source_state_drift",
            Self::DocumentFlowDrift => "cross_reference_document_flow_drift",
            Self::PlanTampered => "cross_reference_plan_tampered",
            Self::Serialization => "cross_reference_serialization",
            Self::OutputLimit => "cross_reference_output_limit",
        }
    }
}

fn apply_operation(
    source: &CrossReferenceDocumentState,
    operation: &CrossReferenceOperation,
    limits: CrossReferenceLimits,
) -> Result<CrossReferenceDocumentState, CrossReferenceError> {
    validate_document_state(source, limits)?;
    if source.document_locked {
        return Err(CrossReferenceError::Protected);
    }
    let CrossReferenceOperation::Insert {
        insertion_index,
        cross_reference,
    } = operation;
    if *insertion_index > source.cross_references.len() {
        return Err(CrossReferenceError::InvalidInsertionIndex);
    }
    let section_index = exact_section_index(&source.sections, &cross_reference.anchor.section_id)?;
    if source.sections[section_index].locked {
        return Err(CrossReferenceError::Protected);
    }
    validate_reference(
        cross_reference,
        &source.sections[section_index],
        &source.targets,
        limits,
    )?;
    if cross_reference.cache.status != CrossReferenceCacheStatus::Current {
        return Err(CrossReferenceError::InvalidCache);
    }
    if source.cross_references.iter().any(|existing| {
        existing.identity.logical_cross_reference_id
            == cross_reference.identity.logical_cross_reference_id
            || existing.identity.begin_control_id == cross_reference.identity.begin_control_id
            || existing.identity.field_id == cross_reference.identity.field_id
            || existing.anchor == cross_reference.anchor
    }) || source
        .occupied_non_cross_reference_begin_control_ids
        .binary_search(&cross_reference.identity.begin_control_id)
        .is_ok()
        || source
            .occupied_non_cross_reference_field_ids
            .binary_search(&cross_reference.identity.field_id)
            .is_ok()
    {
        return Err(CrossReferenceError::InvalidIdentity);
    }
    let mut target = source.clone();
    target
        .cross_references
        .insert(*insertion_index, cross_reference.as_ref().clone());
    validate_document_state(&target, limits)?;
    Ok(target)
}

fn validate_document_state(
    state: &CrossReferenceDocumentState,
    limits: CrossReferenceLimits,
) -> Result<(), CrossReferenceError> {
    if state.schema_version != CROSS_REFERENCE_SCHEMA_VERSION
        || state.sections.is_empty()
        || state.sections.len() > limits.0.sections
        || state.targets.len() > limits.0.targets
        || state.cross_references.len() > limits.0.cross_references
        || state.occupied_non_cross_reference_begin_control_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_cross_reference_field_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_cross_reference_field_name_sha256.len() > limits.0.occupied_native_ids
    {
        return Err(CrossReferenceError::InvalidIdentity);
    }
    for digest in [
        &state.non_cross_reference_content_sha256,
        &state.unrelated_field_inventory_sha256,
        &state.bookmark_inventory_sha256,
        &state.note_inventory_sha256,
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
    if invalid_native_id_inventory(&state.occupied_non_cross_reference_begin_control_ids)
        || invalid_native_id_inventory(&state.occupied_non_cross_reference_field_ids)
    {
        return Err(CrossReferenceError::InvalidIdentity);
    }
    validate_field_name_inventories(state)?;

    let mut section_ids = BTreeSet::new();
    for section in &state.sections {
        if section.paragraph_count == 0 || !section_ids.insert(&section.section_id) {
            return Err(CrossReferenceError::InvalidIdentity);
        }
        for digest in [
            &section.run_topology_sha256,
            &section.inline_topology_sha256,
            &section.opaque_section_state_sha256,
        ] {
            require_digest(digest)?;
        }
    }

    let mut target_index = BTreeMap::new();
    for (index, target) in state.targets.iter().enumerate() {
        let section_index = exact_section_index(&state.sections, &target.anchor.section_id)?;
        validate_target(target, &state.sections[section_index], limits)?;
        if target_index
            .insert(target.identity.logical_target_id.clone(), index)
            .is_some()
        {
            return Err(CrossReferenceError::InvalidIdentity);
        }
    }
    for target in &state.targets {
        for dependency in &target.dependency_target_ids {
            if dependency == &target.identity.logical_target_id
                || !target_index.contains_key(dependency)
            {
                return Err(CrossReferenceError::InvalidTarget);
            }
        }
    }

    let mut logical_ids = BTreeSet::new();
    let mut begin_ids = BTreeSet::new();
    let mut field_ids = BTreeSet::new();
    let mut anchors = BTreeSet::new();
    for reference in &state.cross_references {
        let section_index = exact_section_index(&state.sections, &reference.anchor.section_id)?;
        validate_reference(
            reference,
            &state.sections[section_index],
            &state.targets,
            limits,
        )?;
        if !logical_ids.insert(&reference.identity.logical_cross_reference_id)
            || !begin_ids.insert(reference.identity.begin_control_id)
            || !field_ids.insert(reference.identity.field_id)
            || !anchors.insert(&reference.anchor)
            || state
                .occupied_non_cross_reference_begin_control_ids
                .binary_search(&reference.identity.begin_control_id)
                .is_ok()
            || state
                .occupied_non_cross_reference_field_ids
                .binary_search(&reference.identity.field_id)
                .is_ok()
        {
            return Err(CrossReferenceError::InvalidIdentity);
        }
    }
    validate_acyclic_graph(state, &target_index)
}

fn validate_field_name_inventories(
    state: &CrossReferenceDocumentState,
) -> Result<(), CrossReferenceError> {
    for field_name in &state.occupied_non_cross_reference_field_name_sha256 {
        require_digest(field_name)?;
    }
    if state
        .occupied_non_cross_reference_field_name_sha256
        .windows(2)
        .any(|pair| pair[0] >= pair[1])
    {
        return Err(CrossReferenceError::InvalidIdentity);
    }
    let mut field_names = BTreeSet::new();
    for reference in &state.cross_references {
        if let Some(field_name) = &reference.native_pair.field_name_sha256
            && (!field_names.insert(field_name)
                || state
                    .occupied_non_cross_reference_field_name_sha256
                    .binary_search(field_name)
                    .is_ok())
        {
            return Err(CrossReferenceError::FieldNameConflict);
        }
    }
    Ok(())
}

fn validate_target(
    target: &CrossReferenceTarget,
    section: &CrossReferenceSectionState,
    limits: CrossReferenceLimits,
) -> Result<(), CrossReferenceError> {
    validate_anchor(&target.anchor, section)?;
    validate_target_payload(target, limits)?;
    if target.dependency_target_ids.len() > limits.0.dependencies
        || target
            .dependency_target_ids
            .windows(2)
            .any(|pair| pair[0] >= pair[1])
    {
        return Err(CrossReferenceError::InvalidTarget);
    }
    Ok(())
}

fn validate_target_payload(
    target: &CrossReferenceTarget,
    limits: CrossReferenceLimits,
) -> Result<(), CrossReferenceError> {
    for digest in [
        Some(target.semantic_name_sha256.as_str()),
        Some(target.source_text_sha256.as_str()),
        target.label_sha256.as_deref(),
        target.numbering_sha256.as_deref(),
        Some(target.page_assignment_sha256.as_str()),
        Some(target.opaque_target_state_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest)?;
    }
    validate_opaque(&target.opaque_properties, limits)
}

fn validate_reference(
    reference: &CrossReferenceEntry,
    section: &CrossReferenceSectionState,
    targets: &[CrossReferenceTarget],
    limits: CrossReferenceLimits,
) -> Result<(), CrossReferenceError> {
    if reference.identity.begin_control_id == 0
        || reference.identity.field_id == 0
        || reference.native_pair.begin_tag != CrossReferenceNativeBeginTag::FieldBegin
        || reference.native_pair.end_tag != CrossReferenceNativeEndTag::FieldEnd
        || reference.native_pair.field_type != CrossReferenceFieldType::Crossref
        || reference.native_pair.semantic_binding
            != CrossReferenceSemanticBinding::UnverifiedFieldParameters
        || reference.native_pair.end_begin_control_id_ref != reference.identity.begin_control_id
        || reference.native_pair.end_field_id != reference.identity.field_id
        || reference.native_pair.z_order < -1
    {
        return Err(CrossReferenceError::InvalidNativeBinding);
    }
    validate_anchor(&reference.anchor, section)?;
    let target_index = exact_target_index(targets, &reference.target_id)?;
    let target = &targets[target_index];
    if let Some(containing_target_id) = &reference.containing_target_id {
        let owner_index = exact_target_index(targets, containing_target_id)?;
        let owner = &targets[owner_index];
        if !anchor_contains(&owner.anchor, &reference.anchor) {
            return Err(CrossReferenceError::InvalidTarget);
        }
    }
    validate_display_kind(target, reference.display_kind)?;
    for digest in [
        Some(reference.cache.target_projection_sha256.as_str()),
        Some(reference.cache.display_value_sha256.as_str()),
        reference.native_pair.field_name_sha256.as_deref(),
        Some(reference.native_pair.parameters_sha256.as_str()),
        reference.native_pair.sub_list_sha256.as_deref(),
        reference.native_pair.meta_tag_sha256.as_deref(),
        Some(reference.native_pair.opaque_begin_state_sha256.as_str()),
        Some(reference.native_pair.opaque_end_state_sha256.as_str()),
        Some(reference.opaque_native_payload_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest)?;
    }
    validate_opaque(&reference.opaque_properties, limits)?;
    let current_projection =
        target.projection_sha256(reference.display_kind, &reference.anchor, limits)?;
    let expected = if current_projection == reference.cache.target_projection_sha256 {
        CrossReferenceCacheStatus::Current
    } else {
        CrossReferenceCacheStatus::Stale
    };
    if reference.cache.status != expected {
        return Err(CrossReferenceError::InvalidCache);
    }
    Ok(())
}

fn validate_display_kind(
    target: &CrossReferenceTarget,
    display_kind: CrossReferenceDisplayKind,
) -> Result<(), CrossReferenceError> {
    let compatible = match display_kind {
        CrossReferenceDisplayKind::TargetText
        | CrossReferenceDisplayKind::TargetName
        | CrossReferenceDisplayKind::PageNumber
        | CrossReferenceDisplayKind::RelativePosition => true,
        CrossReferenceDisplayKind::NumberOnly => target.numbering_sha256.is_some(),
        CrossReferenceDisplayKind::LabelAndNumber => {
            target.kind == CrossReferenceTargetKind::Caption
                && target.label_sha256.is_some()
                && target.numbering_sha256.is_some()
        }
    };
    if !compatible {
        return Err(CrossReferenceError::InvalidTarget);
    }
    Ok(())
}

fn validate_acyclic_graph(
    state: &CrossReferenceDocumentState,
    target_index: &BTreeMap<LogicalId, usize>,
) -> Result<(), CrossReferenceError> {
    let mut edges = BTreeSet::new();
    for (source, target) in state.targets.iter().enumerate() {
        for dependency in &target.dependency_target_ids {
            let destination = *target_index
                .get(dependency)
                .ok_or(CrossReferenceError::InvalidTarget)?;
            let _ = edges.insert((source, destination));
        }
    }
    for reference in &state.cross_references {
        if let Some(owner_id) = &reference.containing_target_id {
            let source = *target_index
                .get(owner_id)
                .ok_or(CrossReferenceError::InvalidTarget)?;
            let destination = *target_index
                .get(&reference.target_id)
                .ok_or(CrossReferenceError::InvalidTarget)?;
            let _ = edges.insert((source, destination));
        }
    }
    let mut indegree = vec![0usize; state.targets.len()];
    let mut outgoing = vec![Vec::new(); state.targets.len()];
    for (source, destination) in edges {
        outgoing[source].push(destination);
        indegree[destination] = indegree[destination]
            .checked_add(1)
            .ok_or(CrossReferenceError::ReferenceCycle)?;
    }
    let mut ready = BTreeSet::new();
    for (index, degree) in indegree.iter().enumerate() {
        if *degree == 0 {
            let _ = ready.insert(index);
        }
    }
    let mut visited = 0usize;
    while let Some(index) = ready.pop_first() {
        visited += 1;
        for destination in &outgoing[index] {
            indegree[*destination] -= 1;
            if indegree[*destination] == 0 {
                let _ = ready.insert(*destination);
            }
        }
    }
    if visited != state.targets.len() {
        return Err(CrossReferenceError::ReferenceCycle);
    }
    Ok(())
}

fn exact_section_index(
    sections: &[CrossReferenceSectionState],
    section_id: &LogicalId,
) -> Result<usize, CrossReferenceError> {
    exact_index(sections, |section| section.section_id == *section_id)
}

fn exact_target_index(
    targets: &[CrossReferenceTarget],
    target_id: &LogicalId,
) -> Result<usize, CrossReferenceError> {
    exact_index(targets, |target| {
        target.identity.logical_target_id == *target_id
    })
    .map_err(|_| CrossReferenceError::InvalidTarget)
}

fn exact_index<T>(
    values: &[T],
    predicate: impl Fn(&T) -> bool,
) -> Result<usize, CrossReferenceError> {
    let mut matches = values
        .iter()
        .enumerate()
        .filter(|(_, value)| predicate(value))
        .map(|(index, _)| index);
    let index = matches.next().ok_or(CrossReferenceError::InvalidIdentity)?;
    if matches.next().is_some() {
        return Err(CrossReferenceError::InvalidIdentity);
    }
    Ok(index)
}

fn validate_anchor(
    anchor: &LinkAnchor,
    section: &CrossReferenceSectionState,
) -> Result<(), CrossReferenceError> {
    if anchor.section_id != section.section_id
        || anchor.start > anchor.end
        || anchor.start.paragraph_ordinal >= section.paragraph_count
        || anchor.end.paragraph_ordinal >= section.paragraph_count
    {
        return Err(CrossReferenceError::InvalidIdentity);
    }
    Ok(())
}

fn anchor_contains(owner: &LinkAnchor, child: &LinkAnchor) -> bool {
    owner.section_id == child.section_id && owner.start <= child.start && child.end <= owner.end
}

fn invalid_native_id_inventory(ids: &[u32]) -> bool {
    ids.first().is_some_and(|identifier| *identifier == 0)
        || ids.windows(2).any(|pair| pair[0] >= pair[1])
}

fn validate_opaque(
    properties: &[OpaqueLinkProperty],
    limits: CrossReferenceLimits,
) -> Result<(), CrossReferenceError> {
    if properties.len() > limits.0.opaque_entries {
        return Err(CrossReferenceError::InvalidPayload);
    }
    let mut keys = BTreeSet::new();
    for property in properties {
        if !valid_token(&property.namespace)
            || !valid_token(&property.name)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(CrossReferenceError::InvalidPayload);
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

fn require_digest(value: &str) -> Result<(), CrossReferenceError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(CrossReferenceError::InvalidPayload);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &CrossReferencePlan,
    limits: CrossReferenceLimits,
) -> Result<String, CrossReferenceError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a CrossReferenceOperation,
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
    limits: CrossReferenceLimits,
) -> Result<Vec<u8>, CrossReferenceError> {
    let bytes = serde_json::to_vec(value).map_err(|_| CrossReferenceError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(CrossReferenceError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), CrossReferenceError> {
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
        .map_err(|_| CrossReferenceError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| CrossReferenceError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Private setup keeps sealed-plan tampering local.
mod private_tests {
    use super::*;
    use crate::LinkPoint;

    const DIGEST: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> CrossReferenceLimits {
        CrossReferenceLimits::new(CrossReferenceLimitConfig::default()).expect("limits")
    }

    fn anchor(start: u32, end: u32) -> LinkAnchor {
        LinkAnchor {
            section_id: LogicalId::parse("section-1").expect("id"),
            start: LinkPoint {
                paragraph_ordinal: 0,
                run_ordinal: 0,
                inline_ordinal: start,
            },
            end: LinkPoint {
                paragraph_ordinal: 0,
                run_ordinal: 0,
                inline_ordinal: end,
            },
        }
    }

    fn target() -> CrossReferenceTarget {
        CrossReferenceTarget {
            identity: CrossReferenceTargetIdentity {
                logical_target_id: LogicalId::parse("target-1").expect("id"),
            },
            kind: CrossReferenceTargetKind::Heading,
            anchor: anchor(0, 4),
            semantic_name_sha256: DIGEST.to_owned(),
            source_text_sha256: DIGEST.to_owned(),
            label_sha256: None,
            numbering_sha256: Some(DIGEST.to_owned()),
            page_assignment_sha256: DIGEST.to_owned(),
            dependency_target_ids: Vec::new(),
            opaque_target_state_sha256: DIGEST.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    fn reference(target: &CrossReferenceTarget) -> CrossReferenceEntry {
        let reference_anchor = anchor(6, 7);
        CrossReferenceEntry {
            identity: CrossReferenceIdentity {
                logical_cross_reference_id: LogicalId::parse("crossref-1").expect("id"),
                begin_control_id: 101,
                field_id: 201,
            },
            anchor: reference_anchor.clone(),
            containing_target_id: None,
            target_id: target.identity.logical_target_id.clone(),
            display_kind: CrossReferenceDisplayKind::TargetText,
            update_policy: CrossReferenceUpdatePolicy::PreserveCached,
            cache: CrossReferenceCache {
                target_projection_sha256: target
                    .projection_sha256(
                        CrossReferenceDisplayKind::TargetText,
                        &reference_anchor,
                        limits(),
                    )
                    .expect("projection"),
                display_value_sha256: DIGEST.to_owned(),
                status: CrossReferenceCacheStatus::Current,
            },
            native_pair: CrossReferenceNativePair {
                begin_tag: CrossReferenceNativeBeginTag::FieldBegin,
                end_tag: CrossReferenceNativeEndTag::FieldEnd,
                field_type: CrossReferenceFieldType::Crossref,
                semantic_binding: CrossReferenceSemanticBinding::UnverifiedFieldParameters,
                end_begin_control_id_ref: 101,
                end_field_id: 201,
                field_name_sha256: None,
                editable: true,
                dirty: false,
                z_order: -1,
                parameters_sha256: DIGEST.to_owned(),
                sub_list_sha256: None,
                meta_tag_sha256: None,
                opaque_begin_state_sha256: DIGEST.to_owned(),
                opaque_end_state_sha256: DIGEST.to_owned(),
            },
            opaque_native_payload_sha256: DIGEST.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    fn state(target: CrossReferenceTarget) -> CrossReferenceDocumentState {
        CrossReferenceDocumentState::from_draft(
            CrossReferenceDocumentStateDraft {
                schema_version: CROSS_REFERENCE_SCHEMA_VERSION.to_owned(),
                sections: vec![CrossReferenceSectionState {
                    section_id: LogicalId::parse("section-1").expect("id"),
                    paragraph_count: 1,
                    run_topology_sha256: DIGEST.to_owned(),
                    inline_topology_sha256: DIGEST.to_owned(),
                    opaque_section_state_sha256: DIGEST.to_owned(),
                    locked: false,
                }],
                targets: vec![target],
                cross_references: Vec::new(),
                occupied_non_cross_reference_begin_control_ids: Vec::new(),
                occupied_non_cross_reference_field_ids: Vec::new(),
                occupied_non_cross_reference_field_name_sha256: Vec::new(),
                non_cross_reference_content_sha256: DIGEST.to_owned(),
                unrelated_field_inventory_sha256: DIGEST.to_owned(),
                bookmark_inventory_sha256: DIGEST.to_owned(),
                note_inventory_sha256: DIGEST.to_owned(),
                object_inventory_sha256: DIGEST.to_owned(),
                numbering_inventory_sha256: DIGEST.to_owned(),
                style_catalog_sha256: DIGEST.to_owned(),
                relationship_inventory_sha256: DIGEST.to_owned(),
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
        let target = target();
        let reference = reference(&target);
        let source = state(target);
        let request = CrossReferenceRequest::from_draft(
            CrossReferenceRequestDraft {
                schema_version: CROSS_REFERENCE_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: DIGEST.to_owned(),
                target_document_flow_sha256: DIGEST.to_owned(),
                operation: CrossReferenceOperation::Insert {
                    insertion_index: 0,
                    cross_reference: Box::new(reference),
                },
            },
            &source,
            DIGEST,
            limits(),
        )
        .expect("request");
        let mut plan =
            CrossReferenceBuilder::plan(&source, &request, DIGEST, limits()).expect("plan");
        plan.target_state_sha256 =
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".to_owned();
        plan.seal_sha256 = plan_binding_sha256(&plan, limits()).expect("reseal");
        assert_eq!(
            CrossReferenceBuilder::build(&plan, &source, DIGEST, limits()),
            Err(CrossReferenceError::PlanTampered)
        );
    }
}
