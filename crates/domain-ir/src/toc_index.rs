use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LinkAnchor, LogicalId, OpaqueLinkProperty};

pub const TOC_INDEX_SCHEMA_VERSION: &str = "hwpx-agent.toc-index/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TocIndexLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub sections: usize,
    pub toc_sources: usize,
    pub toc_marks: usize,
    pub index_marks: usize,
    pub generated_blocks: usize,
    pub occupied_native_ids: usize,
    pub opaque_entries: usize,
}

impl Default for TocIndexLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            sections: 4096,
            toc_sources: 1_000_000,
            toc_marks: 1_000_000,
            index_marks: 1_000_000,
            generated_blocks: 65_536,
            occupied_native_ids: 1_000_000,
            opaque_entries: 65_536,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TocIndexLimits(TocIndexLimitConfig);

impl TocIndexLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;

    /// Creates finite limits without silently clamping any value.
    ///
    /// # Errors
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding limits.
    pub fn new(config: TocIndexLimitConfig) -> Result<Self, TocIndexError> {
        let counts = [
            config.sections,
            config.toc_sources,
            config.toc_marks,
            config.index_marks,
            config.generated_blocks,
            config.occupied_native_ids,
            config.opaque_entries,
        ];
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || counts
                .into_iter()
                .any(|count| count == 0 || count > Self::HARD_MAX_ITEMS)
        {
            return Err(TocIndexError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TocIndexLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TocIndexSectionState {
    pub section_id: LogicalId,
    pub paragraph_count: u32,
    pub run_topology_sha256: String,
    pub inline_topology_sha256: String,
    pub page_assignment_sha256: String,
    pub opaque_section_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for TocIndexSectionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocIndexSectionState")
            .field("paragraph_count", &self.paragraph_count)
            .field("locked", &self.locked)
            .field("section", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TocSource {
    pub logical_source_id: LogicalId,
    pub anchor: LinkAnchor,
    pub level: u8,
    pub text_sha256: String,
    pub numbering_linkage_sha256: String,
    pub style_sha256: String,
    pub page_assignment_sha256: String,
    pub opaque_source_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for TocSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocSource")
            .field("level", &self.level)
            .field("locked", &self.locked)
            .field("source", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TocMarkNativeTag {
    TitleMark,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TocMark {
    pub logical_mark_id: LogicalId,
    pub source_id: LogicalId,
    pub anchor: LinkAnchor,
    pub native_tag: TocMarkNativeTag,
    pub ignore: bool,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for TocMark {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocMark")
            .field("native_tag", &self.native_tag)
            .field("ignore", &self.ignore)
            .field("locked", &self.locked)
            .field("mark", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum IndexMarkNativeTag {
    Indexmark,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct IndexMark {
    pub logical_mark_id: LogicalId,
    pub control_id: u32,
    pub anchor: LinkAnchor,
    pub native_tag: IndexMarkNativeTag,
    pub first_key_sha256: String,
    pub second_key_sha256: Option<String>,
    pub first_sort_key_sha256: String,
    pub second_sort_key_sha256: Option<String>,
    pub page_assignment_sha256: String,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for IndexMark {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IndexMark")
            .field("native_tag", &self.native_tag)
            .field("has_second_key", &self.second_key_sha256.is_some())
            .field("locked", &self.locked)
            .field("mark", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TocLeaderKind {
    None,
    Dot,
    Dash,
    Solid,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TocSettings {
    pub minimum_level: u8,
    pub maximum_level: u8,
    pub include_page_numbers: bool,
    pub right_align_page_numbers: bool,
    pub hyperlink_entries: bool,
    pub leader: TocLeaderKind,
    pub level_style_sha256: Vec<String>,
    pub page_number_format_sha256: String,
    pub numbering_render_policy_sha256: String,
}

impl fmt::Debug for TocSettings {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocSettings")
            .field("minimum_level", &self.minimum_level)
            .field("maximum_level", &self.maximum_level)
            .field("include_page_numbers", &self.include_page_numbers)
            .field("right_align_page_numbers", &self.right_align_page_numbers)
            .field("hyperlink_entries", &self.hyperlink_entries)
            .field("leader", &self.leader)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct IndexSettings {
    pub locale: String,
    pub collation_profile_sha256: String,
    pub heading_style_sha256: String,
    pub entry_style_sha256: String,
    pub subentry_style_sha256: String,
    pub page_number_format_sha256: String,
    pub duplicate_page_policy_sha256: String,
    pub column_layout_sha256: String,
}

impl fmt::Debug for IndexSettings {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IndexSettings")
            .field("locale", &"<redacted>")
            .field("settings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum GeneratedCacheStatus {
    Current,
    Stale,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GeneratedCache {
    pub source_projection_sha256: String,
    pub generated_content_sha256: String,
    pub status: GeneratedCacheStatus,
}

impl fmt::Debug for GeneratedCache {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GeneratedCache")
            .field("status", &self.status)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TocNativeBeginTag {
    FieldBegin,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TocNativeEndTag {
    FieldEnd,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TocFieldType {
    Tableofcontents,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TocSemanticBinding {
    UnverifiedFieldParameters,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TocNativePair {
    pub begin_tag: TocNativeBeginTag,
    pub end_tag: TocNativeEndTag,
    pub field_type: TocFieldType,
    pub semantic_binding: TocSemanticBinding,
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

impl fmt::Debug for TocNativePair {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocNativePair")
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
pub struct TocGeneratedBlock {
    pub logical_block_id: LogicalId,
    pub begin_control_id: u32,
    pub field_id: u32,
    pub anchor: LinkAnchor,
    pub settings: TocSettings,
    pub cache: GeneratedCache,
    pub native_pair: TocNativePair,
    pub opaque_generated_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl TocGeneratedBlock {
    /// Computes the complete TOC source projection for cache classification.
    ///
    /// # Errors
    /// Returns an input validation, serialization, or output-limit failure.
    pub fn projection_sha256(
        sources: &[TocSource],
        marks: &[TocMark],
        settings: &TocSettings,
        limits: TocIndexLimits,
    ) -> Result<String, TocIndexError> {
        #[derive(Serialize)]
        struct Projection<'a> {
            sources: Vec<&'a TocSource>,
            marks: Vec<&'a TocMark>,
            settings: &'a TocSettings,
        }
        validate_toc_settings(settings)?;
        let marked_source_ids = marks
            .iter()
            .map(|mark| &mark.source_id)
            .collect::<BTreeSet<_>>();
        let applicable_sources = sources
            .iter()
            .filter(|source| {
                source.level >= settings.minimum_level
                    && source.level <= settings.maximum_level
                    && marked_source_ids.contains(&source.logical_source_id)
            })
            .collect::<Vec<_>>();
        let applicable_source_ids = applicable_sources
            .iter()
            .map(|source| &source.logical_source_id)
            .collect::<BTreeSet<_>>();
        let applicable_marks = marks
            .iter()
            .filter(|mark| applicable_source_ids.contains(&mark.source_id))
            .collect::<Vec<_>>();
        Ok(hex(Sha256::digest(serialize_bounded(
            &Projection {
                sources: applicable_sources,
                marks: applicable_marks,
                settings,
            },
            limits,
        )?)
        .into()))
    }
}

impl fmt::Debug for TocGeneratedBlock {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocGeneratedBlock")
            .field(
                "levels",
                &(self.settings.minimum_level, self.settings.maximum_level),
            )
            .field("locked", &self.locked)
            .field("block", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum IndexGeneratedBinding {
    UnverifiedGeneratedRange,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct IndexGeneratedBlock {
    pub logical_block_id: LogicalId,
    pub anchor: LinkAnchor,
    pub semantic_binding: IndexGeneratedBinding,
    pub settings: IndexSettings,
    pub cache: GeneratedCache,
    pub opaque_generated_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl IndexGeneratedBlock {
    /// Computes the complete index-mark projection for cache classification.
    ///
    /// # Errors
    /// Returns an input validation, serialization, or output-limit failure.
    pub fn projection_sha256(
        marks: &[IndexMark],
        settings: &IndexSettings,
        limits: TocIndexLimits,
    ) -> Result<String, TocIndexError> {
        #[derive(Serialize)]
        struct Projection<'a> {
            marks: &'a [IndexMark],
            settings: &'a IndexSettings,
        }
        validate_index_settings(settings)?;
        Ok(hex(Sha256::digest(serialize_bounded(
            &Projection { marks, settings },
            limits,
        )?)
        .into()))
    }
}

impl fmt::Debug for IndexGeneratedBlock {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IndexGeneratedBlock")
            .field("semantic_binding", &self.semantic_binding)
            .field("locked", &self.locked)
            .field("block", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TocIndexDocumentStateDraft {
    pub schema_version: String,
    pub sections: Vec<TocIndexSectionState>,
    pub toc_sources: Vec<TocSource>,
    pub toc_marks: Vec<TocMark>,
    pub index_marks: Vec<IndexMark>,
    pub toc_blocks: Vec<TocGeneratedBlock>,
    pub index_blocks: Vec<IndexGeneratedBlock>,
    pub occupied_non_toc_index_control_ids: Vec<u32>,
    pub occupied_non_toc_index_field_ids: Vec<u32>,
    pub occupied_non_toc_index_field_name_sha256: Vec<String>,
    pub non_toc_index_content_sha256: String,
    pub unrelated_field_inventory_sha256: String,
    pub reference_inventory_sha256: String,
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

impl fmt::Debug for TocIndexDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("TocIndexDocumentStateDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TocIndexDocumentState {
    schema_version: &'static str,
    sections: Vec<TocIndexSectionState>,
    toc_sources: Vec<TocSource>,
    toc_marks: Vec<TocMark>,
    index_marks: Vec<IndexMark>,
    toc_blocks: Vec<TocGeneratedBlock>,
    index_blocks: Vec<IndexGeneratedBlock>,
    occupied_non_toc_index_control_ids: Vec<u32>,
    occupied_non_toc_index_field_ids: Vec<u32>,
    occupied_non_toc_index_field_name_sha256: Vec<String>,
    non_toc_index_content_sha256: String,
    unrelated_field_inventory_sha256: String,
    reference_inventory_sha256: String,
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

impl TocIndexDocumentState {
    /// Validates and seals the complete TOC/index inventory.
    ///
    /// # Errors
    /// Rejects malformed, dangling, stale, colliding, protected, or oversized state.
    pub fn from_draft(
        draft: TocIndexDocumentStateDraft,
        limits: TocIndexLimits,
    ) -> Result<Self, TocIndexError> {
        if draft.schema_version != TOC_INDEX_SCHEMA_VERSION {
            return Err(TocIndexError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: TOC_INDEX_SCHEMA_VERSION,
            sections: draft.sections,
            toc_sources: draft.toc_sources,
            toc_marks: draft.toc_marks,
            index_marks: draft.index_marks,
            toc_blocks: draft.toc_blocks,
            index_blocks: draft.index_blocks,
            occupied_non_toc_index_control_ids: draft.occupied_non_toc_index_control_ids,
            occupied_non_toc_index_field_ids: draft.occupied_non_toc_index_field_ids,
            occupied_non_toc_index_field_name_sha256: draft
                .occupied_non_toc_index_field_name_sha256,
            non_toc_index_content_sha256: draft.non_toc_index_content_sha256,
            unrelated_field_inventory_sha256: draft.unrelated_field_inventory_sha256,
            reference_inventory_sha256: draft.reference_inventory_sha256,
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
        validate_state(&state, limits)?;
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub fn toc_marks(&self) -> &[TocMark] {
        &self.toc_marks
    }

    #[must_use]
    pub fn toc_sources(&self) -> &[TocSource] {
        &self.toc_sources
    }

    #[must_use]
    pub fn index_marks(&self) -> &[IndexMark] {
        &self.index_marks
    }

    #[must_use]
    pub fn toc_blocks(&self) -> &[TocGeneratedBlock] {
        &self.toc_blocks
    }

    #[must_use]
    pub fn index_blocks(&self) -> &[IndexGeneratedBlock] {
        &self.index_blocks
    }

    /// Serializes the complete state deterministically within its configured bound.
    ///
    /// # Errors
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: TocIndexLimits) -> Result<Vec<u8>, TocIndexError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical state.
    ///
    /// # Errors
    /// Returns a serialization or output-limit failure.
    pub fn canonical_sha256(&self, limits: TocIndexLimits) -> Result<String, TocIndexError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for TocIndexDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocIndexDocumentState")
            .field("toc_source_count", &self.toc_sources.len())
            .field("toc_mark_count", &self.toc_marks.len())
            .field("index_mark_count", &self.index_marks.len())
            .field(
                "generated_count",
                &(self.toc_blocks.len() + self.index_blocks.len()),
            )
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TocIndexOperation {
    TocMarkInsert {
        insertion_index: usize,
        mark: TocMark,
    },
    TocMarkHide {
        mark_id: LogicalId,
    },
    TocCreate {
        insertion_index: usize,
        block: Box<TocGeneratedBlock>,
    },
    IndexMarkInsert {
        insertion_index: usize,
        mark: IndexMark,
    },
    IndexCreate {
        insertion_index: usize,
        block: Box<IndexGeneratedBlock>,
    },
}

impl TocIndexOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::TocMarkInsert { .. } => "ref.toc_mark",
            Self::TocMarkHide { .. } => "ref.toc_hide_mark",
            Self::TocCreate { .. } => "ref.toc_create",
            Self::IndexMarkInsert { .. } => "ref.index_mark",
            Self::IndexCreate { .. } => "ref.index_create",
        }
    }
}

impl fmt::Debug for TocIndexOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocIndexOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TocIndexRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: TocIndexOperation,
}

impl fmt::Debug for TocIndexRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("TocIndexRequestDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TocIndexRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: TocIndexOperation,
}

impl TocIndexRequest {
    /// Strictly parses a bounded request and validates exact source/flow state.
    ///
    /// # Errors
    /// Rejects duplicate or unknown JSON keys, drift, invalid operations, or limits.
    pub fn from_json(
        bytes: &[u8],
        source: &TocIndexDocumentState,
        current_document_flow_sha256: &str,
        limits: TocIndexLimits,
    ) -> Result<Self, TocIndexError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(TocIndexError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft: TocIndexRequestDraft =
            serde_json::from_slice(bytes).map_err(|_| TocIndexError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    /// Validates a typed request against current state and document flow.
    ///
    /// # Errors
    /// Rejects version, state/flow drift, malformed digests, or invalid operations.
    pub fn from_draft(
        draft: TocIndexRequestDraft,
        source: &TocIndexDocumentState,
        current_document_flow_sha256: &str,
        limits: TocIndexLimits,
    ) -> Result<Self, TocIndexError> {
        if draft.schema_version != TOC_INDEX_SCHEMA_VERSION {
            return Err(TocIndexError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_source_state_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        if source.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(TocIndexError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(TocIndexError::DocumentFlowDrift);
        }
        let request = Self {
            schema_version: TOC_INDEX_SCHEMA_VERSION,
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

impl fmt::Debug for TocIndexRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocIndexRequest")
            .field("capability_id", &self.capability_id())
            .field("request", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TocIndexPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: TocIndexOperation,
    target_state: TocIndexDocumentState,
    seal_sha256: String,
}

impl TocIndexPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn target_state(&self) -> &TocIndexDocumentState {
        &self.target_state
    }
}

impl fmt::Debug for TocIndexPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocIndexPlan")
            .field("capability_id", &self.capability_id)
            .field("plan", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TocIndexBuilder;

impl TocIndexBuilder {
    /// Builds a sealed exact-state plan.
    ///
    /// # Errors
    /// Rechecks source/flow drift and rejects invalid or protected operations.
    pub fn plan(
        source: &TocIndexDocumentState,
        request: &TocIndexRequest,
        current_document_flow_sha256: &str,
        limits: TocIndexLimits,
    ) -> Result<TocIndexPlan, TocIndexError> {
        if source.canonical_sha256(limits)? != request.expected_source_state_sha256 {
            return Err(TocIndexError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(TocIndexError::DocumentFlowDrift);
        }
        let target_state = apply_operation(source, &request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = TocIndexPlan {
            schema_version: TOC_INDEX_SCHEMA_VERSION,
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

    /// Rechecks and materializes a sealed exact-state plan.
    ///
    /// # Errors
    /// Rejects plan tampering, source/flow drift, or target mismatch.
    pub fn build(
        plan: &TocIndexPlan,
        current: &TocIndexDocumentState,
        current_document_flow_sha256: &str,
        limits: TocIndexLimits,
    ) -> Result<TocIndexResult, TocIndexError> {
        if plan.schema_version != TOC_INDEX_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan.seal_sha256 != plan_binding_sha256(plan, limits)?
        {
            return Err(TocIndexError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(TocIndexError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(TocIndexError::DocumentFlowDrift);
        }
        let rebuilt = apply_operation(current, &plan.operation, limits)?;
        if rebuilt != plan.target_state
            || rebuilt.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(TocIndexError::PlanTampered);
        }
        Ok(TocIndexResult {
            state: rebuilt,
            receipt: TocIndexReceipt {
                schema_version: TOC_INDEX_SCHEMA_VERSION,
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
pub struct TocIndexReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for TocIndexReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocIndexReceipt")
            .field("capability_id", &self.capability_id)
            .field("receipt", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TocIndexResult {
    pub state: TocIndexDocumentState,
    pub receipt: TocIndexReceipt,
}

impl fmt::Debug for TocIndexResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TocIndexResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum TocIndexError {
    #[error("TOC/index limits are invalid")]
    InvalidLimit,
    #[error("TOC/index input exceeds a finite limit")]
    InputLimit,
    #[error("TOC/index JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("TOC/index schema version is unsupported")]
    UnsupportedVersion,
    #[error("TOC/index identity, ordering, or anchor is invalid")]
    InvalidIdentity,
    #[error("TOC source or mark is missing, duplicated, or incompatible")]
    InvalidMark,
    #[error("TOC/index generated cache or settings are inconsistent")]
    InvalidGeneratedState,
    #[error("TOC/index native binding is unsupported or inconsistent")]
    InvalidNativeBinding,
    #[error("TOC field name collides with an occupied field name")]
    FieldNameConflict,
    #[error("TOC/index digest, locale, or opaque payload is invalid")]
    InvalidPayload,
    #[error("TOC/index insertion index is invalid")]
    InvalidInsertionIndex,
    #[error("TOC/index target, section, or document is protected")]
    Protected,
    #[error("TOC/index source state drifted")]
    SourceStateDrift,
    #[error("TOC/index document flow drifted")]
    DocumentFlowDrift,
    #[error("TOC/index plan was tampered with")]
    PlanTampered,
    #[error("TOC/index serialization failed")]
    Serialization,
    #[error("TOC/index serialized output exceeds a finite limit")]
    OutputLimit,
}

impl TocIndexError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "toc_index_invalid_limit",
            Self::InputLimit => "toc_index_input_limit",
            Self::InvalidJson => "toc_index_invalid_json",
            Self::UnsupportedVersion => "toc_index_unsupported_version",
            Self::InvalidIdentity => "toc_index_invalid_identity",
            Self::InvalidMark => "toc_index_invalid_mark",
            Self::InvalidGeneratedState => "toc_index_invalid_generated_state",
            Self::InvalidNativeBinding => "toc_index_invalid_native_binding",
            Self::FieldNameConflict => "toc_index_field_name_conflict",
            Self::InvalidPayload => "toc_index_invalid_payload",
            Self::InvalidInsertionIndex => "toc_index_invalid_insertion_index",
            Self::Protected => "toc_index_protected",
            Self::SourceStateDrift => "toc_index_source_state_drift",
            Self::DocumentFlowDrift => "toc_index_document_flow_drift",
            Self::PlanTampered => "toc_index_plan_tampered",
            Self::Serialization => "toc_index_serialization",
            Self::OutputLimit => "toc_index_output_limit",
        }
    }
}

fn apply_operation(
    source: &TocIndexDocumentState,
    operation: &TocIndexOperation,
    limits: TocIndexLimits,
) -> Result<TocIndexDocumentState, TocIndexError> {
    validate_state(source, limits)?;
    if source.document_locked {
        return Err(TocIndexError::Protected);
    }
    let mut target = source.clone();
    match operation {
        TocIndexOperation::TocMarkInsert {
            insertion_index,
            mark,
        } => {
            if *insertion_index > target.toc_marks.len() {
                return Err(TocIndexError::InvalidInsertionIndex);
            }
            validate_toc_mark(mark, &target.sections, &target.toc_sources, limits)?;
            if mark.ignore {
                return Err(TocIndexError::InvalidMark);
            }
            ensure_section_unlocked(&target.sections, &mark.anchor.section_id)?;
            target.toc_marks.insert(*insertion_index, mark.clone());
            reclassify_toc_blocks(&mut target, limits)?;
        }
        TocIndexOperation::TocMarkHide { mark_id } => {
            let index = exact_index(&target.toc_marks, |mark| mark.logical_mark_id == *mark_id)
                .map_err(|_| TocIndexError::InvalidMark)?;
            if target.toc_marks[index].locked {
                return Err(TocIndexError::Protected);
            }
            ensure_section_unlocked(&target.sections, &target.toc_marks[index].anchor.section_id)?;
            if target.toc_marks[index].ignore {
                return Err(TocIndexError::InvalidMark);
            }
            target.toc_marks[index].ignore = true;
            reclassify_toc_blocks(&mut target, limits)?;
        }
        TocIndexOperation::TocCreate {
            insertion_index,
            block,
        } => {
            if *insertion_index > target.toc_blocks.len() {
                return Err(TocIndexError::InvalidInsertionIndex);
            }
            ensure_section_unlocked(&target.sections, &block.anchor.section_id)?;
            validate_toc_block(block, &target, limits)?;
            if block.cache.status != GeneratedCacheStatus::Current {
                return Err(TocIndexError::InvalidGeneratedState);
            }
            target
                .toc_blocks
                .insert(*insertion_index, block.as_ref().clone());
        }
        TocIndexOperation::IndexMarkInsert {
            insertion_index,
            mark,
        } => {
            if *insertion_index > target.index_marks.len() {
                return Err(TocIndexError::InvalidInsertionIndex);
            }
            validate_index_mark(mark, &target.sections, limits)?;
            ensure_section_unlocked(&target.sections, &mark.anchor.section_id)?;
            target.index_marks.insert(*insertion_index, mark.clone());
            reclassify_index_blocks(&mut target, limits)?;
        }
        TocIndexOperation::IndexCreate {
            insertion_index,
            block,
        } => {
            if *insertion_index > target.index_blocks.len() {
                return Err(TocIndexError::InvalidInsertionIndex);
            }
            ensure_section_unlocked(&target.sections, &block.anchor.section_id)?;
            validate_index_block(block, &target, limits)?;
            if block.cache.status != GeneratedCacheStatus::Current {
                return Err(TocIndexError::InvalidGeneratedState);
            }
            target
                .index_blocks
                .insert(*insertion_index, block.as_ref().clone());
        }
    }
    validate_state(&target, limits)?;
    Ok(target)
}

fn reclassify_toc_blocks(
    state: &mut TocIndexDocumentState,
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    for block in &mut state.toc_blocks {
        let current = TocGeneratedBlock::projection_sha256(
            &state.toc_sources,
            &state.toc_marks,
            &block.settings,
            limits,
        )?;
        block.cache.status = if current == block.cache.source_projection_sha256 {
            GeneratedCacheStatus::Current
        } else {
            GeneratedCacheStatus::Stale
        };
    }
    Ok(())
}

fn reclassify_index_blocks(
    state: &mut TocIndexDocumentState,
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    for block in &mut state.index_blocks {
        let current =
            IndexGeneratedBlock::projection_sha256(&state.index_marks, &block.settings, limits)?;
        block.cache.status = if current == block.cache.source_projection_sha256 {
            GeneratedCacheStatus::Current
        } else {
            GeneratedCacheStatus::Stale
        };
    }
    Ok(())
}

fn validate_state(
    state: &TocIndexDocumentState,
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    if state.schema_version != TOC_INDEX_SCHEMA_VERSION
        || state.sections.is_empty()
        || state.sections.len() > limits.0.sections
        || state.toc_sources.len() > limits.0.toc_sources
        || state.toc_marks.len() > limits.0.toc_marks
        || state.index_marks.len() > limits.0.index_marks
        || state.toc_blocks.len() > limits.0.generated_blocks
        || state.index_blocks.len() > limits.0.generated_blocks
        || state.occupied_non_toc_index_control_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_toc_index_field_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_toc_index_field_name_sha256.len() > limits.0.occupied_native_ids
    {
        return Err(TocIndexError::InvalidIdentity);
    }
    for digest in [
        &state.non_toc_index_content_sha256,
        &state.unrelated_field_inventory_sha256,
        &state.reference_inventory_sha256,
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
    validate_sorted_ids(&state.occupied_non_toc_index_control_ids)?;
    validate_sorted_ids(&state.occupied_non_toc_index_field_ids)?;
    validate_sorted_digests(&state.occupied_non_toc_index_field_name_sha256)?;

    validate_sections_and_sources(state, limits)?;
    validate_marks_and_blocks(state, limits)
}

fn validate_sections_and_sources(
    state: &TocIndexDocumentState,
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    let mut section_ids = BTreeSet::new();
    for section in &state.sections {
        if section.paragraph_count == 0 || !section_ids.insert(&section.section_id) {
            return Err(TocIndexError::InvalidIdentity);
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
    let mut source_anchors = BTreeSet::new();
    for source in &state.toc_sources {
        validate_toc_source(source, &state.sections, limits)?;
        if !source_ids.insert(&source.logical_source_id) || !source_anchors.insert(&source.anchor) {
            return Err(TocIndexError::InvalidIdentity);
        }
    }
    Ok(())
}

fn validate_marks_and_blocks(
    state: &TocIndexDocumentState,
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    let mut logical_ids = BTreeSet::new();
    let mut mark_anchors = BTreeSet::new();
    for mark in &state.toc_marks {
        validate_toc_mark(mark, &state.sections, &state.toc_sources, limits)?;
        if !logical_ids.insert(&mark.logical_mark_id) || !mark_anchors.insert(&mark.anchor) {
            return Err(TocIndexError::InvalidIdentity);
        }
    }

    let mut control_ids = BTreeSet::new();
    for mark in &state.index_marks {
        validate_index_mark(mark, &state.sections, limits)?;
        if !logical_ids.insert(&mark.logical_mark_id)
            || !mark_anchors.insert(&mark.anchor)
            || !control_ids.insert(mark.control_id)
            || state
                .occupied_non_toc_index_control_ids
                .binary_search(&mark.control_id)
                .is_ok()
        {
            return Err(TocIndexError::InvalidIdentity);
        }
    }

    let mut field_ids = BTreeSet::new();
    let mut field_names = BTreeSet::new();
    let mut block_anchors = BTreeSet::new();
    for block in &state.toc_blocks {
        validate_toc_block(block, state, limits)?;
        if !logical_ids.insert(&block.logical_block_id)
            || !control_ids.insert(block.begin_control_id)
            || !field_ids.insert(block.field_id)
            || !block_anchors.insert(&block.anchor)
            || state
                .occupied_non_toc_index_control_ids
                .binary_search(&block.begin_control_id)
                .is_ok()
            || state
                .occupied_non_toc_index_field_ids
                .binary_search(&block.field_id)
                .is_ok()
        {
            return Err(TocIndexError::InvalidIdentity);
        }
        if let Some(name) = &block.native_pair.field_name_sha256
            && (!field_names.insert(name)
                || state
                    .occupied_non_toc_index_field_name_sha256
                    .binary_search(name)
                    .is_ok())
        {
            return Err(TocIndexError::FieldNameConflict);
        }
    }
    for block in &state.index_blocks {
        validate_index_block(block, state, limits)?;
        if !logical_ids.insert(&block.logical_block_id) || !block_anchors.insert(&block.anchor) {
            return Err(TocIndexError::InvalidIdentity);
        }
    }
    Ok(())
}

fn validate_toc_source(
    source: &TocSource,
    sections: &[TocIndexSectionState],
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    validate_anchor_in_sections(&source.anchor, sections)?;
    if !(1..=10).contains(&source.level) {
        return Err(TocIndexError::InvalidMark);
    }
    for digest in [
        &source.text_sha256,
        &source.numbering_linkage_sha256,
        &source.style_sha256,
        &source.page_assignment_sha256,
        &source.opaque_source_state_sha256,
    ] {
        require_digest(digest)?;
    }
    validate_opaque(&source.opaque_properties, limits)
}

fn validate_toc_mark(
    mark: &TocMark,
    sections: &[TocIndexSectionState],
    sources: &[TocSource],
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    validate_anchor_in_sections(&mark.anchor, sections)?;
    if mark.native_tag != TocMarkNativeTag::TitleMark {
        return Err(TocIndexError::InvalidNativeBinding);
    }
    let source_index = exact_index(sources, |source| source.logical_source_id == mark.source_id)
        .map_err(|_| TocIndexError::InvalidMark)?;
    if !anchor_contains(&sources[source_index].anchor, &mark.anchor) {
        return Err(TocIndexError::InvalidMark);
    }
    require_digest(&mark.opaque_native_payload_sha256)?;
    validate_opaque(&mark.opaque_properties, limits)
}

fn validate_index_mark(
    mark: &IndexMark,
    sections: &[TocIndexSectionState],
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    validate_anchor_in_sections(&mark.anchor, sections)?;
    if mark.control_id == 0 || mark.native_tag != IndexMarkNativeTag::Indexmark {
        return Err(TocIndexError::InvalidNativeBinding);
    }
    if mark.second_key_sha256.is_some() != mark.second_sort_key_sha256.is_some() {
        return Err(TocIndexError::InvalidMark);
    }
    for digest in [
        Some(mark.first_key_sha256.as_str()),
        mark.second_key_sha256.as_deref(),
        Some(mark.first_sort_key_sha256.as_str()),
        mark.second_sort_key_sha256.as_deref(),
        Some(mark.page_assignment_sha256.as_str()),
        Some(mark.opaque_native_payload_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest)?;
    }
    validate_opaque(&mark.opaque_properties, limits)
}

fn validate_toc_block(
    block: &TocGeneratedBlock,
    state: &TocIndexDocumentState,
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    validate_anchor_in_sections(&block.anchor, &state.sections)?;
    validate_toc_settings(&block.settings)?;
    if block.begin_control_id == 0
        || block.field_id == 0
        || block.native_pair.begin_tag != TocNativeBeginTag::FieldBegin
        || block.native_pair.end_tag != TocNativeEndTag::FieldEnd
        || block.native_pair.field_type != TocFieldType::Tableofcontents
        || block.native_pair.semantic_binding != TocSemanticBinding::UnverifiedFieldParameters
        || block.native_pair.end_begin_control_id_ref != block.begin_control_id
        || block.native_pair.end_field_id != block.field_id
        || block.native_pair.z_order < -1
    {
        return Err(TocIndexError::InvalidNativeBinding);
    }
    for digest in [
        Some(block.cache.source_projection_sha256.as_str()),
        Some(block.cache.generated_content_sha256.as_str()),
        block.native_pair.field_name_sha256.as_deref(),
        Some(block.native_pair.parameters_sha256.as_str()),
        block.native_pair.sub_list_sha256.as_deref(),
        block.native_pair.meta_tag_sha256.as_deref(),
        Some(block.native_pair.opaque_begin_state_sha256.as_str()),
        Some(block.native_pair.opaque_end_state_sha256.as_str()),
        Some(block.opaque_generated_state_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest)?;
    }
    validate_opaque(&block.opaque_properties, limits)?;
    let projection = TocGeneratedBlock::projection_sha256(
        &state.toc_sources,
        &state.toc_marks,
        &block.settings,
        limits,
    )?;
    let expected = if projection == block.cache.source_projection_sha256 {
        GeneratedCacheStatus::Current
    } else {
        GeneratedCacheStatus::Stale
    };
    if expected != block.cache.status {
        return Err(TocIndexError::InvalidGeneratedState);
    }
    Ok(())
}

fn validate_index_block(
    block: &IndexGeneratedBlock,
    state: &TocIndexDocumentState,
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    validate_anchor_in_sections(&block.anchor, &state.sections)?;
    validate_index_settings(&block.settings)?;
    if block.semantic_binding != IndexGeneratedBinding::UnverifiedGeneratedRange {
        return Err(TocIndexError::InvalidNativeBinding);
    }
    for digest in [
        &block.cache.source_projection_sha256,
        &block.cache.generated_content_sha256,
        &block.opaque_generated_state_sha256,
    ] {
        require_digest(digest)?;
    }
    validate_opaque(&block.opaque_properties, limits)?;
    let projection =
        IndexGeneratedBlock::projection_sha256(&state.index_marks, &block.settings, limits)?;
    let expected = if projection == block.cache.source_projection_sha256 {
        GeneratedCacheStatus::Current
    } else {
        GeneratedCacheStatus::Stale
    };
    if expected != block.cache.status {
        return Err(TocIndexError::InvalidGeneratedState);
    }
    Ok(())
}

fn validate_toc_settings(settings: &TocSettings) -> Result<(), TocIndexError> {
    if settings.minimum_level == 0
        || settings.maximum_level > 10
        || settings.minimum_level > settings.maximum_level
        || settings.level_style_sha256.len()
            != usize::from(settings.maximum_level - settings.minimum_level + 1)
        || (!settings.include_page_numbers && settings.right_align_page_numbers)
    {
        return Err(TocIndexError::InvalidGeneratedState);
    }
    for digest in settings.level_style_sha256.iter().chain([
        &settings.page_number_format_sha256,
        &settings.numbering_render_policy_sha256,
    ]) {
        require_digest(digest)?;
    }
    Ok(())
}

fn validate_index_settings(settings: &IndexSettings) -> Result<(), TocIndexError> {
    if !valid_locale(&settings.locale) {
        return Err(TocIndexError::InvalidPayload);
    }
    for digest in [
        &settings.collation_profile_sha256,
        &settings.heading_style_sha256,
        &settings.entry_style_sha256,
        &settings.subentry_style_sha256,
        &settings.page_number_format_sha256,
        &settings.duplicate_page_policy_sha256,
        &settings.column_layout_sha256,
    ] {
        require_digest(digest)?;
    }
    Ok(())
}

fn validate_anchor_in_sections(
    anchor: &LinkAnchor,
    sections: &[TocIndexSectionState],
) -> Result<(), TocIndexError> {
    let index = exact_index(sections, |section| section.section_id == anchor.section_id)?;
    let section = &sections[index];
    if anchor.start > anchor.end
        || anchor.start.paragraph_ordinal >= section.paragraph_count
        || anchor.end.paragraph_ordinal >= section.paragraph_count
    {
        return Err(TocIndexError::InvalidIdentity);
    }
    Ok(())
}

fn ensure_section_unlocked(
    sections: &[TocIndexSectionState],
    section_id: &LogicalId,
) -> Result<(), TocIndexError> {
    let index = exact_index(sections, |section| section.section_id == *section_id)?;
    if sections[index].locked {
        return Err(TocIndexError::Protected);
    }
    Ok(())
}

fn exact_index<T>(values: &[T], predicate: impl Fn(&T) -> bool) -> Result<usize, TocIndexError> {
    let mut matches = values
        .iter()
        .enumerate()
        .filter(|(_, value)| predicate(value))
        .map(|(index, _)| index);
    let index = matches.next().ok_or(TocIndexError::InvalidIdentity)?;
    if matches.next().is_some() {
        return Err(TocIndexError::InvalidIdentity);
    }
    Ok(index)
}

fn anchor_contains(owner: &LinkAnchor, child: &LinkAnchor) -> bool {
    owner.section_id == child.section_id && owner.start <= child.start && child.end <= owner.end
}

fn validate_sorted_ids(ids: &[u32]) -> Result<(), TocIndexError> {
    if ids.first().is_some_and(|id| *id == 0) || ids.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(TocIndexError::InvalidIdentity);
    }
    Ok(())
}

fn validate_sorted_digests(digests: &[String]) -> Result<(), TocIndexError> {
    for digest in digests {
        require_digest(digest)?;
    }
    if digests.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(TocIndexError::InvalidIdentity);
    }
    Ok(())
}

fn validate_opaque(
    properties: &[OpaqueLinkProperty],
    limits: TocIndexLimits,
) -> Result<(), TocIndexError> {
    if properties.len() > limits.0.opaque_entries {
        return Err(TocIndexError::InvalidPayload);
    }
    let mut keys = BTreeSet::new();
    for property in properties {
        if !valid_token(&property.namespace)
            || !valid_token(&property.name)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(TocIndexError::InvalidPayload);
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

fn require_digest(value: &str) -> Result<(), TocIndexError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(TocIndexError::InvalidPayload);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &TocIndexPlan,
    limits: TocIndexLimits,
) -> Result<String, TocIndexError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a TocIndexOperation,
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
    limits: TocIndexLimits,
) -> Result<Vec<u8>, TocIndexError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TocIndexError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(TocIndexError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TocIndexError> {
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
        .map_err(|_| TocIndexError::InvalidJson)?;
    deserializer.end().map_err(|_| TocIndexError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod private_tests {
    use super::*;
    use crate::LinkPoint;

    const D: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> TocIndexLimits {
        TocIndexLimits::new(TocIndexLimitConfig::default()).expect("limits")
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

    fn state() -> TocIndexDocumentState {
        TocIndexDocumentState::from_draft(
            TocIndexDocumentStateDraft {
                schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
                sections: vec![TocIndexSectionState {
                    section_id: LogicalId::parse("section-1").expect("id"),
                    paragraph_count: 1,
                    run_topology_sha256: D.to_owned(),
                    inline_topology_sha256: D.to_owned(),
                    page_assignment_sha256: D.to_owned(),
                    opaque_section_state_sha256: D.to_owned(),
                    locked: false,
                }],
                toc_sources: vec![TocSource {
                    logical_source_id: LogicalId::parse("source-1").expect("id"),
                    anchor: anchor(0, 5),
                    level: 1,
                    text_sha256: D.to_owned(),
                    numbering_linkage_sha256: D.to_owned(),
                    style_sha256: D.to_owned(),
                    page_assignment_sha256: D.to_owned(),
                    opaque_source_state_sha256: D.to_owned(),
                    opaque_properties: Vec::new(),
                    locked: false,
                }],
                toc_marks: Vec::new(),
                index_marks: Vec::new(),
                toc_blocks: Vec::new(),
                index_blocks: Vec::new(),
                occupied_non_toc_index_control_ids: Vec::new(),
                occupied_non_toc_index_field_ids: Vec::new(),
                occupied_non_toc_index_field_name_sha256: Vec::new(),
                non_toc_index_content_sha256: D.to_owned(),
                unrelated_field_inventory_sha256: D.to_owned(),
                reference_inventory_sha256: D.to_owned(),
                note_inventory_sha256: D.to_owned(),
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

    #[test]
    fn private_plan_tampering_is_rejected() {
        let source = state();
        let request = TocIndexRequest::from_draft(
            TocIndexRequestDraft {
                schema_version: TOC_INDEX_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: D.to_owned(),
                target_document_flow_sha256: D.to_owned(),
                operation: TocIndexOperation::TocMarkInsert {
                    insertion_index: 0,
                    mark: TocMark {
                        logical_mark_id: LogicalId::parse("mark-1").expect("id"),
                        source_id: LogicalId::parse("source-1").expect("id"),
                        anchor: anchor(0, 5),
                        native_tag: TocMarkNativeTag::TitleMark,
                        ignore: false,
                        opaque_native_payload_sha256: D.to_owned(),
                        opaque_properties: Vec::new(),
                        locked: false,
                    },
                },
            },
            &source,
            D,
            limits(),
        )
        .expect("request");
        let mut plan = TocIndexBuilder::plan(&source, &request, D, limits()).expect("plan");
        plan.target_state_sha256 =
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".to_owned();
        plan.seal_sha256 = plan_binding_sha256(&plan, limits()).expect("reseal");
        assert_eq!(
            TocIndexBuilder::build(&plan, &source, D, limits()),
            Err(TocIndexError::PlanTampered)
        );
    }
}
