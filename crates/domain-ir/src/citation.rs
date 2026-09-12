use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LinkAnchor, LogicalId, OpaqueLinkProperty};

pub const CITATION_SCHEMA_VERSION: &str = "hwpx-agent.citation/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CitationLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub sections: usize,
    pub sources: usize,
    pub citations: usize,
    pub source_references: usize,
    pub occupied_native_ids: usize,
    pub opaque_entries: usize,
}

impl Default for CitationLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            sections: 4096,
            sources: 1_000_000,
            citations: 1_000_000,
            source_references: 1024,
            occupied_native_ids: 1_000_000,
            opaque_entries: 4096,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CitationLimits(CitationLimitConfig);

impl CitationLimits {
    /// Creates finite citation limits.
    ///
    /// # Errors
    /// Returns [`CitationError::InvalidLimit`] when any bound is zero or the input can exceed the
    /// output representation.
    pub fn new(config: CitationLimitConfig) -> Result<Self, CitationError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.sections == 0
            || config.sources == 0
            || config.citations == 0
            || config.source_references == 0
            || config.occupied_native_ids == 0
            || config.opaque_entries == 0
        {
            return Err(CitationError::InvalidLimit);
        }
        Ok(Self(config))
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CitationSectionState {
    pub section_id: LogicalId,
    pub paragraph_count: u32,
    pub run_topology_sha256: String,
    pub inline_topology_sha256: String,
    pub page_assignment_sha256: String,
    pub opaque_section_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for CitationSectionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationSectionState")
            .field("paragraph_count", &self.paragraph_count)
            .field("locked", &self.locked)
            .field("section", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BibliographyPartPath {
    CustomBibliographyXml,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BibliographyManifestId {
    Bibliography,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BibliographyMediaType {
    ApplicationXml,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BibliographyFormatBinding {
    UnverifiedOpaquePart,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CitationSource {
    pub logical_source_id: LogicalId,
    pub provider_record_key_sha256: String,
    pub semantic_record_sha256: String,
    pub display_record_sha256: String,
    pub opaque_record_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for CitationSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationSource")
            .field("locked", &self.locked)
            .field("source", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct BibliographyCatalogState {
    pub logical_catalog_id: LogicalId,
    pub part_path: BibliographyPartPath,
    pub manifest_id: BibliographyManifestId,
    pub media_type: BibliographyMediaType,
    pub format_binding: BibliographyFormatBinding,
    pub part_sha256: String,
    pub provider_id_sha256: String,
    pub provider_version_sha256: String,
    pub locale: String,
    pub citation_style_sha256: String,
    pub sources: Vec<CitationSource>,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for BibliographyCatalogState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BibliographyCatalogState")
            .field("source_count", &self.sources.len())
            .field("format_binding", &self.format_binding)
            .field("locked", &self.locked)
            .field("catalog", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CitationLocatorKind {
    Page,
    Chapter,
    Section,
    Paragraph,
    Figure,
    Table,
    Other,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CitationLocator {
    pub kind: CitationLocatorKind,
    pub value_sha256: String,
}

impl fmt::Debug for CitationLocator {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationLocator")
            .field("kind", &self.kind)
            .field("value", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CitationDisplayOptions {
    pub locator: Option<CitationLocator>,
    pub prefix_sha256: Option<String>,
    pub suffix_sha256: Option<String>,
    pub suppress_author: bool,
    pub opaque_formatting_sha256: String,
}

impl fmt::Debug for CitationDisplayOptions {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationDisplayOptions")
            .field(
                "locator_kind",
                &self.locator.as_ref().map(|locator| locator.kind),
            )
            .field("suppress_author", &self.suppress_author)
            .field("formatting", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CitationCacheStatus {
    Current,
    Stale,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CitationCache {
    pub source_projection_sha256: String,
    pub displayed_text_sha256: String,
    pub status: CitationCacheStatus,
}

impl fmt::Debug for CitationCache {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationCache")
            .field("status", &self.status)
            .field("cache", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CitationNativeBeginTag {
    FieldBegin,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CitationNativeEndTag {
    FieldEnd,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CitationFieldType {
    Citation,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CitationSemanticBinding {
    UnverifiedFieldParameters,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CitationNativePair {
    pub begin_tag: CitationNativeBeginTag,
    pub end_tag: CitationNativeEndTag,
    pub field_type: CitationFieldType,
    pub semantic_binding: CitationSemanticBinding,
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

impl fmt::Debug for CitationNativePair {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationNativePair")
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
pub struct CitationNode {
    pub logical_citation_id: LogicalId,
    pub begin_control_id: u32,
    pub field_id: u32,
    pub anchor: LinkAnchor,
    pub source_ids: Vec<LogicalId>,
    pub display_options: CitationDisplayOptions,
    pub cache: CitationCache,
    pub native_pair: CitationNativePair,
    pub opaque_citation_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl CitationNode {
    /// Computes the exact provider/style/selected-record projection used by the visible cache.
    ///
    /// # Errors
    /// Returns a source-reference, serialization, or output-limit error.
    pub fn projection_sha256(
        catalog: &BibliographyCatalogState,
        source_ids: &[LogicalId],
        display_options: &CitationDisplayOptions,
        limits: CitationLimits,
    ) -> Result<String, CitationError> {
        #[derive(Serialize)]
        struct Projection<'a> {
            provider_id_sha256: &'a str,
            provider_version_sha256: &'a str,
            locale: &'a str,
            citation_style_sha256: &'a str,
            selected_sources: Vec<&'a CitationSource>,
            display_options: &'a CitationDisplayOptions,
        }
        validate_catalog(catalog, limits)?;
        validate_display_options(display_options)?;
        let selected_sources = select_sources(catalog, source_ids, limits)?;
        Ok(hex(Sha256::digest(serialize_bounded(
            &Projection {
                provider_id_sha256: &catalog.provider_id_sha256,
                provider_version_sha256: &catalog.provider_version_sha256,
                locale: &catalog.locale,
                citation_style_sha256: &catalog.citation_style_sha256,
                selected_sources,
                display_options,
            },
            limits,
        )?)
        .into()))
    }
}

impl fmt::Debug for CitationNode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationNode")
            .field("source_count", &self.source_ids.len())
            .field("locked", &self.locked)
            .field("citation", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CitationDocumentStateDraft {
    pub schema_version: String,
    pub sections: Vec<CitationSectionState>,
    pub bibliography: Option<BibliographyCatalogState>,
    pub citations: Vec<CitationNode>,
    pub occupied_non_citation_control_ids: Vec<u32>,
    pub occupied_non_citation_field_ids: Vec<u32>,
    pub occupied_non_citation_field_name_sha256: Vec<String>,
    pub non_citation_content_sha256: String,
    pub unrelated_field_inventory_sha256: String,
    pub reference_inventory_sha256: String,
    pub note_inventory_sha256: String,
    pub toc_index_inventory_sha256: String,
    pub object_inventory_sha256: String,
    pub numbering_inventory_sha256: String,
    pub style_catalog_sha256: String,
    pub relationship_inventory_sha256: String,
    pub resource_inventory_sha256: String,
    pub document_protection_sha256: String,
    pub opaque_document_state_sha256: String,
    pub document_locked: bool,
}

impl fmt::Debug for CitationDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationDocumentStateDraft")
            .field("section_count", &self.sections.len())
            .field("catalog_present", &self.bibliography.is_some())
            .field("citation_count", &self.citations.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(
    try_from = "CitationDocumentStateDraft",
    into = "CitationDocumentStateDraft"
)]
pub struct CitationDocumentState {
    schema_version: String,
    sections: Vec<CitationSectionState>,
    bibliography: Option<BibliographyCatalogState>,
    citations: Vec<CitationNode>,
    occupied_non_citation_control_ids: Vec<u32>,
    occupied_non_citation_field_ids: Vec<u32>,
    occupied_non_citation_field_name_sha256: Vec<String>,
    non_citation_content_sha256: String,
    unrelated_field_inventory_sha256: String,
    reference_inventory_sha256: String,
    note_inventory_sha256: String,
    toc_index_inventory_sha256: String,
    object_inventory_sha256: String,
    numbering_inventory_sha256: String,
    style_catalog_sha256: String,
    relationship_inventory_sha256: String,
    resource_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
    document_locked: bool,
}

impl CitationDocumentState {
    /// Validates and constructs a complete citation state.
    ///
    /// # Errors
    /// Returns a typed validation error for incomplete or inconsistent state.
    pub fn from_draft(
        draft: CitationDocumentStateDraft,
        limits: CitationLimits,
    ) -> Result<Self, CitationError> {
        let state = Self {
            schema_version: draft.schema_version,
            sections: draft.sections,
            bibliography: draft.bibliography,
            citations: draft.citations,
            occupied_non_citation_control_ids: draft.occupied_non_citation_control_ids,
            occupied_non_citation_field_ids: draft.occupied_non_citation_field_ids,
            occupied_non_citation_field_name_sha256: draft.occupied_non_citation_field_name_sha256,
            non_citation_content_sha256: draft.non_citation_content_sha256,
            unrelated_field_inventory_sha256: draft.unrelated_field_inventory_sha256,
            reference_inventory_sha256: draft.reference_inventory_sha256,
            note_inventory_sha256: draft.note_inventory_sha256,
            toc_index_inventory_sha256: draft.toc_index_inventory_sha256,
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
    pub fn bibliography(&self) -> Option<&BibliographyCatalogState> {
        self.bibliography.as_ref()
    }

    #[must_use]
    pub fn citations(&self) -> &[CitationNode] {
        &self.citations
    }

    /// Serializes the canonical validated state within the configured bound.
    ///
    /// # Errors
    /// Returns a validation, serialization, or output-limit error.
    pub fn canonical_json(&self, limits: CitationLimits) -> Result<Vec<u8>, CitationError> {
        validate_state(self, limits)?;
        serialize_bounded(self, limits)
    }

    /// Computes the canonical state digest.
    ///
    /// # Errors
    /// Returns a validation, serialization, or output-limit error.
    pub fn canonical_sha256(&self, limits: CitationLimits) -> Result<String, CitationError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl TryFrom<CitationDocumentStateDraft> for CitationDocumentState {
    type Error = CitationError;

    fn try_from(draft: CitationDocumentStateDraft) -> Result<Self, Self::Error> {
        let limits = CitationLimits::new(CitationLimitConfig::default())?;
        Self::from_draft(draft, limits)
    }
}

impl From<CitationDocumentState> for CitationDocumentStateDraft {
    fn from(state: CitationDocumentState) -> Self {
        Self {
            schema_version: state.schema_version,
            sections: state.sections,
            bibliography: state.bibliography,
            citations: state.citations,
            occupied_non_citation_control_ids: state.occupied_non_citation_control_ids,
            occupied_non_citation_field_ids: state.occupied_non_citation_field_ids,
            occupied_non_citation_field_name_sha256: state.occupied_non_citation_field_name_sha256,
            non_citation_content_sha256: state.non_citation_content_sha256,
            unrelated_field_inventory_sha256: state.unrelated_field_inventory_sha256,
            reference_inventory_sha256: state.reference_inventory_sha256,
            note_inventory_sha256: state.note_inventory_sha256,
            toc_index_inventory_sha256: state.toc_index_inventory_sha256,
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

impl fmt::Debug for CitationDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationDocumentState")
            .field("catalog_present", &self.bibliography.is_some())
            .field("citation_count", &self.citations.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum CitationOperation {
    CitationInsert {
        insertion_index: usize,
        citation: Box<CitationNode>,
    },
}

impl CitationOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::CitationInsert { .. } => "ref.citation_insert",
        }
    }
}

impl fmt::Debug for CitationOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CitationRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: CitationOperation,
}

impl fmt::Debug for CitationRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationRequestDraft")
            .field("capability_id", &self.operation.capability_id())
            .field("request", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CitationRequest {
    schema_version: String,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: CitationOperation,
}

impl CitationRequest {
    /// Validates a request against the exact current source and document flow.
    ///
    /// # Errors
    /// Returns a typed validation or drift error before any plan is produced.
    pub fn from_draft(
        draft: CitationRequestDraft,
        source: &CitationDocumentState,
        current_document_flow_sha256: &str,
        limits: CitationLimits,
    ) -> Result<Self, CitationError> {
        validate_state(source, limits)?;
        if draft.schema_version != CITATION_SCHEMA_VERSION {
            return Err(CitationError::InvalidSchema);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if draft.expected_source_state_sha256 != source.canonical_sha256(limits)? {
            return Err(CitationError::SourceStateDrift);
        }
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(CitationError::DocumentFlowDrift);
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
        source: &CitationDocumentState,
        current_document_flow_sha256: &str,
        limits: CitationLimits,
    ) -> Result<Self, CitationError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(CitationError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft: CitationRequestDraft =
            serde_json::from_slice(bytes).map_err(|_| CitationError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }
}

impl fmt::Debug for CitationRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("request", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CitationPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: CitationOperation,
    seal_sha256: String,
}

impl fmt::Debug for CitationPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationPlan")
            .field("capability_id", &self.capability_id)
            .field("plan", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CitationReceipt {
    pub schema_version: &'static str,
    pub capability_id: &'static str,
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub source_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
}

impl fmt::Debug for CitationReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationReceipt")
            .field("capability_id", &self.capability_id)
            .field("receipt", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CitationResult {
    pub state: CitationDocumentState,
    pub receipt: CitationReceipt,
}

impl fmt::Debug for CitationResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CitationResult")
            .field("capability_id", &self.receipt.capability_id)
            .field("result", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct CitationBuilder;

impl CitationBuilder {
    /// Plans a citation insertion while binding the exact source and target states.
    ///
    /// # Errors
    /// Returns a validation or drift error when the request does not match the current state.
    pub fn plan(
        source: &CitationDocumentState,
        request: &CitationRequest,
        current_document_flow_sha256: &str,
        limits: CitationLimits,
    ) -> Result<CitationPlan, CitationError> {
        validate_state(source, limits)?;
        require_digest(current_document_flow_sha256)?;
        if request.schema_version != CITATION_SCHEMA_VERSION {
            return Err(CitationError::InvalidSchema);
        }
        let source_state_sha256 = source.canonical_sha256(limits)?;
        if request.expected_source_state_sha256 != source_state_sha256 {
            return Err(CitationError::SourceStateDrift);
        }
        if request.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(CitationError::DocumentFlowDrift);
        }
        let target = apply_operation(source, &request.operation, limits)?;
        let mut plan = CitationPlan {
            schema_version: CITATION_SCHEMA_VERSION,
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

    /// Builds the planned target only after rechecking the seal, source state, and flow.
    ///
    /// # Errors
    /// Returns a tamper, validation, or drift error without returning partial state.
    pub fn build(
        plan: &CitationPlan,
        source: &CitationDocumentState,
        current_document_flow_sha256: &str,
        limits: CitationLimits,
    ) -> Result<CitationResult, CitationError> {
        validate_state(source, limits)?;
        require_digest(current_document_flow_sha256)?;
        if plan.schema_version != CITATION_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || require_digest(&plan.source_state_sha256).is_err()
            || require_digest(&plan.target_state_sha256).is_err()
            || require_digest(&plan.source_document_flow_sha256).is_err()
            || require_digest(&plan.target_document_flow_sha256).is_err()
            || require_digest(&plan.seal_sha256).is_err()
            || plan_binding_sha256(plan, limits)? != plan.seal_sha256
        {
            return Err(CitationError::PlanTampered);
        }
        if source.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(CitationError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(CitationError::DocumentFlowDrift);
        }
        let state = apply_operation(source, &plan.operation, limits)?;
        if state.canonical_sha256(limits)? != plan.target_state_sha256 {
            return Err(CitationError::PlanTampered);
        }
        Ok(CitationResult {
            state,
            receipt: CitationReceipt {
                schema_version: CITATION_SCHEMA_VERSION,
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
pub enum CitationError {
    #[error("invalid citation limit")]
    InvalidLimit,
    #[error("citation input exceeds limit")]
    InputLimit,
    #[error("invalid citation JSON")]
    InvalidJson,
    #[error("invalid citation schema")]
    InvalidSchema,
    #[error("invalid citation identity")]
    InvalidIdentity,
    #[error("bibliography catalog is missing or invalid")]
    InvalidCatalog,
    #[error("citation source is missing or ambiguous")]
    SourceMissing,
    #[error("citation state is invalid")]
    InvalidCitation,
    #[error("native citation binding is invalid")]
    InvalidNativeBinding,
    #[error("citation field name conflicts")]
    FieldNameConflict,
    #[error("citation target is protected")]
    Protected,
    #[error("citation source state drifted")]
    SourceStateDrift,
    #[error("citation document flow drifted")]
    DocumentFlowDrift,
    #[error("citation plan was tampered")]
    PlanTampered,
    #[error("citation serialization failed")]
    Serialization,
    #[error("citation output exceeds limit")]
    OutputLimit,
}

impl CitationError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "citation_invalid_limit",
            Self::InputLimit => "citation_input_limit",
            Self::InvalidJson => "citation_invalid_json",
            Self::InvalidSchema => "citation_invalid_schema",
            Self::InvalidIdentity => "citation_invalid_identity",
            Self::InvalidCatalog => "citation_invalid_catalog",
            Self::SourceMissing => "citation_source_missing",
            Self::InvalidCitation => "citation_invalid_citation",
            Self::InvalidNativeBinding => "citation_invalid_native_binding",
            Self::FieldNameConflict => "citation_field_name_conflict",
            Self::Protected => "citation_protected",
            Self::SourceStateDrift => "citation_source_state_drift",
            Self::DocumentFlowDrift => "citation_document_flow_drift",
            Self::PlanTampered => "citation_plan_tampered",
            Self::Serialization => "citation_serialization",
            Self::OutputLimit => "citation_output_limit",
        }
    }
}

fn apply_operation(
    source: &CitationDocumentState,
    operation: &CitationOperation,
    limits: CitationLimits,
) -> Result<CitationDocumentState, CitationError> {
    validate_state(source, limits)?;
    if source.document_locked {
        return Err(CitationError::Protected);
    }
    let mut target = source.clone();
    match operation {
        CitationOperation::CitationInsert {
            insertion_index,
            citation,
        } => {
            if *insertion_index > target.citations.len() {
                return Err(CitationError::InvalidIdentity);
            }
            let catalog = target
                .bibliography
                .as_ref()
                .ok_or(CitationError::InvalidCatalog)?;
            validate_citation(citation, catalog, &target.sections, limits)?;
            if citation.cache.status != CitationCacheStatus::Current {
                return Err(CitationError::InvalidCitation);
            }
            ensure_section_unlocked(&target.sections, &citation.anchor.section_id)?;
            target
                .citations
                .insert(*insertion_index, citation.as_ref().clone());
        }
    }
    validate_state(&target, limits)?;
    Ok(target)
}

fn validate_state(
    state: &CitationDocumentState,
    limits: CitationLimits,
) -> Result<(), CitationError> {
    if state.schema_version != CITATION_SCHEMA_VERSION
        || state.sections.is_empty()
        || state.sections.len() > limits.0.sections
        || state.citations.len() > limits.0.citations
        || state.occupied_non_citation_control_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_citation_field_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_citation_field_name_sha256.len() > limits.0.occupied_native_ids
    {
        return Err(CitationError::InvalidIdentity);
    }
    validate_sorted_ids(&state.occupied_non_citation_control_ids)?;
    validate_sorted_ids(&state.occupied_non_citation_field_ids)?;
    validate_sorted_digests(&state.occupied_non_citation_field_name_sha256)?;
    for digest in [
        &state.non_citation_content_sha256,
        &state.unrelated_field_inventory_sha256,
        &state.reference_inventory_sha256,
        &state.note_inventory_sha256,
        &state.toc_index_inventory_sha256,
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
            return Err(CitationError::InvalidIdentity);
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
    if let Some(catalog) = &state.bibliography {
        validate_catalog(catalog, limits)?;
    } else if !state.citations.is_empty() {
        return Err(CitationError::InvalidCatalog);
    }
    let mut citation_ids = BTreeSet::new();
    let mut control_ids = state
        .occupied_non_citation_control_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let mut field_ids = state
        .occupied_non_citation_field_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let mut field_names = state
        .occupied_non_citation_field_name_sha256
        .iter()
        .collect::<BTreeSet<_>>();
    for citation in &state.citations {
        let catalog = state
            .bibliography
            .as_ref()
            .ok_or(CitationError::InvalidCatalog)?;
        validate_citation(citation, catalog, &state.sections, limits)?;
        if !citation_ids.insert(&citation.logical_citation_id)
            || !control_ids.insert(citation.begin_control_id)
            || !field_ids.insert(citation.field_id)
        {
            return Err(CitationError::InvalidIdentity);
        }
        if citation
            .native_pair
            .field_name_sha256
            .as_ref()
            .is_some_and(|name| !field_names.insert(name))
        {
            return Err(CitationError::FieldNameConflict);
        }
    }
    Ok(())
}

fn validate_catalog(
    catalog: &BibliographyCatalogState,
    limits: CitationLimits,
) -> Result<(), CitationError> {
    if catalog.part_path != BibliographyPartPath::CustomBibliographyXml
        || catalog.manifest_id != BibliographyManifestId::Bibliography
        || catalog.media_type != BibliographyMediaType::ApplicationXml
        || catalog.format_binding != BibliographyFormatBinding::UnverifiedOpaquePart
        || catalog.sources.len() > limits.0.sources
        || !valid_locale(&catalog.locale)
    {
        return Err(CitationError::InvalidCatalog);
    }
    for digest in [
        &catalog.part_sha256,
        &catalog.provider_id_sha256,
        &catalog.provider_version_sha256,
        &catalog.citation_style_sha256,
    ] {
        require_digest(digest).map_err(|_| CitationError::InvalidCatalog)?;
    }
    validate_opaque(&catalog.opaque_properties, limits)
        .map_err(|_| CitationError::InvalidCatalog)?;
    let mut ids = BTreeSet::new();
    let mut provider_keys = BTreeSet::new();
    for source in &catalog.sources {
        if !ids.insert(&source.logical_source_id)
            || !provider_keys.insert(&source.provider_record_key_sha256)
        {
            return Err(CitationError::InvalidCatalog);
        }
        for digest in [
            &source.provider_record_key_sha256,
            &source.semantic_record_sha256,
            &source.display_record_sha256,
            &source.opaque_record_sha256,
        ] {
            require_digest(digest).map_err(|_| CitationError::InvalidCatalog)?;
        }
        validate_opaque(&source.opaque_properties, limits)
            .map_err(|_| CitationError::InvalidCatalog)?;
    }
    Ok(())
}

fn validate_citation(
    citation: &CitationNode,
    catalog: &BibliographyCatalogState,
    sections: &[CitationSectionState],
    limits: CitationLimits,
) -> Result<(), CitationError> {
    if citation.begin_control_id == 0
        || citation.field_id == 0
        || citation.native_pair.begin_tag != CitationNativeBeginTag::FieldBegin
        || citation.native_pair.end_tag != CitationNativeEndTag::FieldEnd
        || citation.native_pair.field_type != CitationFieldType::Citation
        || citation.native_pair.semantic_binding
            != CitationSemanticBinding::UnverifiedFieldParameters
        || citation.native_pair.end_begin_control_id_ref != citation.begin_control_id
        || citation.native_pair.end_field_id != citation.field_id
        || citation.native_pair.z_order < -1
    {
        return Err(CitationError::InvalidNativeBinding);
    }
    validate_anchor(&citation.anchor, sections)?;
    validate_display_options(&citation.display_options)?;
    select_sources(catalog, &citation.source_ids, limits)?;
    for digest in [
        Some(citation.cache.source_projection_sha256.as_str()),
        Some(citation.cache.displayed_text_sha256.as_str()),
        citation.native_pair.field_name_sha256.as_deref(),
        Some(citation.native_pair.parameters_sha256.as_str()),
        citation.native_pair.sub_list_sha256.as_deref(),
        citation.native_pair.meta_tag_sha256.as_deref(),
        Some(citation.native_pair.opaque_begin_state_sha256.as_str()),
        Some(citation.native_pair.opaque_end_state_sha256.as_str()),
        Some(citation.opaque_citation_state_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest)?;
    }
    validate_opaque(&citation.opaque_properties, limits)?;
    let projection = CitationNode::projection_sha256(
        catalog,
        &citation.source_ids,
        &citation.display_options,
        limits,
    )?;
    let expected = if projection == citation.cache.source_projection_sha256 {
        CitationCacheStatus::Current
    } else {
        CitationCacheStatus::Stale
    };
    if citation.cache.status != expected {
        return Err(CitationError::InvalidCitation);
    }
    Ok(())
}

fn validate_display_options(options: &CitationDisplayOptions) -> Result<(), CitationError> {
    for digest in [
        options
            .locator
            .as_ref()
            .map(|locator| locator.value_sha256.as_str()),
        options.prefix_sha256.as_deref(),
        options.suffix_sha256.as_deref(),
        Some(options.opaque_formatting_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest)?;
    }
    Ok(())
}

fn select_sources<'a>(
    catalog: &'a BibliographyCatalogState,
    source_ids: &[LogicalId],
    limits: CitationLimits,
) -> Result<Vec<&'a CitationSource>, CitationError> {
    if source_ids.is_empty() || source_ids.len() > limits.0.source_references {
        return Err(CitationError::SourceMissing);
    }
    let mut unique = BTreeSet::new();
    let mut selected = Vec::with_capacity(source_ids.len());
    for source_id in source_ids {
        if !unique.insert(source_id) {
            return Err(CitationError::SourceMissing);
        }
        let mut matches = catalog
            .sources
            .iter()
            .filter(|source| source.logical_source_id == *source_id);
        let source = matches.next().ok_or(CitationError::SourceMissing)?;
        if matches.next().is_some() {
            return Err(CitationError::SourceMissing);
        }
        selected.push(source);
    }
    Ok(selected)
}

fn validate_anchor(
    anchor: &LinkAnchor,
    sections: &[CitationSectionState],
) -> Result<(), CitationError> {
    let mut matches = sections
        .iter()
        .filter(|section| section.section_id == anchor.section_id);
    let section = matches.next().ok_or(CitationError::InvalidIdentity)?;
    if matches.next().is_some()
        || anchor.start > anchor.end
        || anchor.start.paragraph_ordinal >= section.paragraph_count
        || anchor.end.paragraph_ordinal >= section.paragraph_count
    {
        return Err(CitationError::InvalidIdentity);
    }
    Ok(())
}

fn ensure_section_unlocked(
    sections: &[CitationSectionState],
    section_id: &LogicalId,
) -> Result<(), CitationError> {
    let mut matches = sections
        .iter()
        .filter(|section| section.section_id == *section_id);
    let section = matches.next().ok_or(CitationError::InvalidIdentity)?;
    if matches.next().is_some() {
        return Err(CitationError::InvalidIdentity);
    }
    if section.locked {
        return Err(CitationError::Protected);
    }
    Ok(())
}

fn validate_sorted_ids(ids: &[u32]) -> Result<(), CitationError> {
    if ids.first().is_some_and(|id| *id == 0) || ids.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(CitationError::InvalidIdentity);
    }
    Ok(())
}

fn validate_sorted_digests(digests: &[String]) -> Result<(), CitationError> {
    for digest in digests {
        require_digest(digest)?;
    }
    if digests.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(CitationError::InvalidIdentity);
    }
    Ok(())
}

fn validate_opaque(
    properties: &[OpaqueLinkProperty],
    limits: CitationLimits,
) -> Result<(), CitationError> {
    if properties.len() > limits.0.opaque_entries {
        return Err(CitationError::InvalidCitation);
    }
    let mut keys = BTreeSet::new();
    for property in properties {
        if !valid_token(&property.namespace)
            || !valid_token(&property.name)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(CitationError::InvalidCitation);
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

fn require_digest(value: &str) -> Result<(), CitationError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(CitationError::InvalidCitation);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &CitationPlan,
    limits: CitationLimits,
) -> Result<String, CitationError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a CitationOperation,
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
    limits: CitationLimits,
) -> Result<Vec<u8>, CitationError> {
    let bytes = serde_json::to_vec(value).map_err(|_| CitationError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(CitationError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), CitationError> {
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
        .map_err(|_| CitationError::InvalidJson)?;
    deserializer.end().map_err(|_| CitationError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod private_tests {
    use super::*;
    use crate::LinkPoint;

    const D: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> CitationLimits {
        CitationLimits::new(CitationLimitConfig::default()).expect("limits")
    }

    fn anchor() -> LinkAnchor {
        LinkAnchor {
            section_id: LogicalId::parse("section-1").expect("id"),
            start: LinkPoint {
                paragraph_ordinal: 0,
                run_ordinal: 0,
                inline_ordinal: 0,
            },
            end: LinkPoint {
                paragraph_ordinal: 0,
                run_ordinal: 0,
                inline_ordinal: 1,
            },
        }
    }

    fn source() -> CitationSource {
        CitationSource {
            logical_source_id: LogicalId::parse("source-1").expect("id"),
            provider_record_key_sha256: D.to_owned(),
            semantic_record_sha256: D.to_owned(),
            display_record_sha256: D.to_owned(),
            opaque_record_sha256: D.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    fn options() -> CitationDisplayOptions {
        CitationDisplayOptions {
            locator: None,
            prefix_sha256: None,
            suffix_sha256: None,
            suppress_author: false,
            opaque_formatting_sha256: D.to_owned(),
        }
    }

    fn catalog() -> BibliographyCatalogState {
        BibliographyCatalogState {
            logical_catalog_id: LogicalId::parse("catalog-1").expect("id"),
            part_path: BibliographyPartPath::CustomBibliographyXml,
            manifest_id: BibliographyManifestId::Bibliography,
            media_type: BibliographyMediaType::ApplicationXml,
            format_binding: BibliographyFormatBinding::UnverifiedOpaquePart,
            part_sha256: D.to_owned(),
            provider_id_sha256: D.to_owned(),
            provider_version_sha256: D.to_owned(),
            locale: "ko-KR".to_owned(),
            citation_style_sha256: D.to_owned(),
            sources: vec![source()],
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    fn state() -> CitationDocumentState {
        CitationDocumentState::from_draft(
            CitationDocumentStateDraft {
                schema_version: CITATION_SCHEMA_VERSION.to_owned(),
                sections: vec![CitationSectionState {
                    section_id: LogicalId::parse("section-1").expect("id"),
                    paragraph_count: 1,
                    run_topology_sha256: D.to_owned(),
                    inline_topology_sha256: D.to_owned(),
                    page_assignment_sha256: D.to_owned(),
                    opaque_section_state_sha256: D.to_owned(),
                    locked: false,
                }],
                bibliography: Some(catalog()),
                citations: Vec::new(),
                occupied_non_citation_control_ids: Vec::new(),
                occupied_non_citation_field_ids: Vec::new(),
                occupied_non_citation_field_name_sha256: Vec::new(),
                non_citation_content_sha256: D.to_owned(),
                unrelated_field_inventory_sha256: D.to_owned(),
                reference_inventory_sha256: D.to_owned(),
                note_inventory_sha256: D.to_owned(),
                toc_index_inventory_sha256: D.to_owned(),
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

    fn citation(catalog: &BibliographyCatalogState) -> CitationNode {
        let display_options = options();
        let source_ids = vec![LogicalId::parse("source-1").expect("id")];
        CitationNode {
            logical_citation_id: LogicalId::parse("citation-1").expect("id"),
            begin_control_id: 100,
            field_id: 200,
            anchor: anchor(),
            cache: CitationCache {
                source_projection_sha256: CitationNode::projection_sha256(
                    catalog,
                    &source_ids,
                    &display_options,
                    limits(),
                )
                .expect("projection"),
                displayed_text_sha256: D.to_owned(),
                status: CitationCacheStatus::Current,
            },
            source_ids,
            display_options,
            native_pair: CitationNativePair {
                begin_tag: CitationNativeBeginTag::FieldBegin,
                end_tag: CitationNativeEndTag::FieldEnd,
                field_type: CitationFieldType::Citation,
                semantic_binding: CitationSemanticBinding::UnverifiedFieldParameters,
                end_begin_control_id_ref: 100,
                end_field_id: 200,
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
            opaque_citation_state_sha256: D.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    #[test]
    fn private_plan_tampering_is_rejected() {
        let source = state();
        let request = CitationRequest::from_draft(
            CitationRequestDraft {
                schema_version: CITATION_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: D.to_owned(),
                target_document_flow_sha256: D.to_owned(),
                operation: CitationOperation::CitationInsert {
                    insertion_index: 0,
                    citation: Box::new(citation(source.bibliography().expect("catalog"))),
                },
            },
            &source,
            D,
            limits(),
        )
        .expect("request");
        let mut plan = CitationBuilder::plan(&source, &request, D, limits()).expect("plan");
        plan.target_state_sha256 =
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".to_owned();
        plan.seal_sha256 = plan_binding_sha256(&plan, limits()).expect("reseal");
        assert_eq!(
            CitationBuilder::build(&plan, &source, D, limits()),
            Err(CitationError::PlanTampered)
        );
    }
}
