use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    CellCoordinate, FormulaAstDraft, FormulaCellDraft, LogicalId, TABLE_FORMULA_SCHEMA_VERSION,
    TABLE_RULING_SCHEMA_VERSION, TableGrid, TableGridError, TableRulingCellDraft, TableRulingError,
    TableRulingPayloadBlock, TableRulingState, TableRulingStateDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{
    RawEdit, TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits,
    TableRulingHwpxReadback, TableRulingHwpxReader,
};
use crate::preserving_xml::PreservingXmlDocument;
use crate::{
    TablePaginationHwpxError, TablePaginationHwpxLimits, TablePaginationHwpxReadback,
    TablePaginationHwpxReader, TablePlacementHwpxError, TablePlacementHwpxReadback,
    TablePlacementHwpxReader,
};

pub const TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-nested-table-hwpx/v1";
pub const TABLE_NESTED_TABLE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-nested-table-hwpx.hancom-2020-inline-template/1";
const TABLE_NESTED_TABLE_CAPABILITY_ID: &str = "table.nested_table";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableNestedTableHwpxLimits {
    pub ruling: TableRulingHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableNestedTableHwpxReadback {
    pub profile_id: &'static str,
    pub parent_table_ordinal: usize,
    pub parent_cell: CellCoordinate,
    pub placeholder_paragraph_ordinal: usize,
    pub payload_insert_index: usize,
    pub template_table_ordinal: usize,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub template_section_sha256: [u8; 32],
    pub insertion_context_sha256: String,
    pub nested_wrapper_sha256: String,
    pub source_table_count: usize,
    pub parent: TableRulingHwpxReadback,
    pub parent_pagination: TablePaginationHwpxReadback,
    pub template: TableRulingHwpxReadback,
    pub template_pagination: TablePaginationHwpxReadback,
    pub template_placement: TablePlacementHwpxReadback,
}

impl fmt::Debug for TableNestedTableHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNestedTableHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("parent_table_ordinal", &self.parent_table_ordinal)
            .field("parent_cell", &self.parent_cell)
            .field(
                "placeholder_paragraph_ordinal",
                &self.placeholder_paragraph_ordinal,
            )
            .field("payload_insert_index", &self.payload_insert_index)
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("source_table_count", &self.source_table_count)
            .field("parent_rows", &self.parent.grid.rows())
            .field("parent_columns", &self.parent.grid.columns())
            .field("nested_rows", &self.template.grid.rows())
            .field("nested_columns", &self.template.grid.columns())
            .field("nested_payload_blocks", &self.template.payload_block_count)
            .field("nested_formulas", &self.template.formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableNestedTableHwpxReader;

impl TableNestedTableHwpxReader {
    /// Reads one exact empty paragraph owned by a selected master cell plus one complete inline
    /// table template. Parent and nested tables are lifted independently so nested formulas never
    /// leak into the parent's formula state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, nonempty, non-inline, captioned, colliding, unbound or
    /// over-limit source/template state.
    #[allow(clippy::too_many_arguments)]
    pub fn read_context(
        header: &[u8],
        section: &[u8],
        parent_table_ordinal: usize,
        parent_cell: CellCoordinate,
        placeholder_paragraph_ordinal: usize,
        parent_binding: &TableRulingHwpxBinding,
        template_section: &[u8],
        template_table_ordinal: usize,
        template_binding: &TableRulingHwpxBinding,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<TableNestedTableHwpxReadback, TableNestedTableHwpxError> {
        let parent = TableRulingHwpxReader::read_existing_preserving_caption(
            header,
            section,
            parent_table_ordinal,
            parent_binding,
            &limits.ruling,
        )?;
        let master = parent.grid.master_cell_at(parent_cell)?;
        if master.row != parent_cell.row || master.column != parent_cell.column {
            return Err(TableNestedTableHwpxError::CoveredCellSelector);
        }
        let parent_pagination = TablePaginationHwpxReader::read_in_section(
            section,
            parent_table_ordinal,
            limits.pagination,
        )?;
        let document = PreservingXmlDocument::parse(section)?;
        let (placeholder, payload_insert_index) = selected_empty_cell_paragraph(
            section,
            &document,
            parent_table_ordinal,
            parent_cell,
            placeholder_paragraph_ordinal,
            parent.grid.master_cell_count(),
        )?;
        let insertion_context_sha256 = insertion_context_digest(
            section,
            &document,
            placeholder,
            parent_table_ordinal,
            parent_cell,
            placeholder_paragraph_ordinal,
        )?;
        let template = TableRulingHwpxReader::read_existing_preserving_caption(
            header,
            template_section,
            template_table_ordinal,
            template_binding,
            &limits.ruling,
        )?;
        let template_pagination = TablePaginationHwpxReader::read_in_section(
            template_section,
            template_table_ordinal,
            limits.pagination,
        )?;
        let template_placement = TablePlacementHwpxReader::read_in_section(
            template_section,
            template_table_ordinal,
            limits.ruling.layout,
        )?;
        if !template_placement.attachment_flags.treat_as_char
            || template_pagination.caption.is_some()
        {
            return Err(TableNestedTableHwpxError::UnsupportedTemplateProfile);
        }
        validate_template_payload_profile(template_section, template_table_ordinal)?;
        let nested_wrapper_sha256 =
            super::insertion_wrapper_semantic_digest(template_section, template_table_ordinal)?;
        validate_cross_table_logical_identities(&parent.state, &template.state, None)?;
        ensure_template_native_identity_available(
            section,
            template_section,
            template_table_ordinal,
        )?;
        Ok(TableNestedTableHwpxReadback {
            profile_id: TABLE_NESTED_TABLE_HWPX_PROFILE_ID,
            parent_table_ordinal,
            parent_cell,
            placeholder_paragraph_ordinal,
            payload_insert_index,
            template_table_ordinal,
            header_sha256: Sha256::digest(header).into(),
            section_sha256: Sha256::digest(section).into(),
            template_section_sha256: Sha256::digest(template_section).into(),
            insertion_context_sha256,
            nested_wrapper_sha256,
            source_table_count: TablePaginationHwpxReader::count_in_section(
                section,
                limits.pagination,
            )?,
            parent,
            parent_pagination,
            template,
            template_pagination,
            template_placement,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableNestedTableHwpxRequestDraft {
    pub schema_version: String,
    pub capability_id: String,
    pub parent_table_ordinal: usize,
    pub parent_cell: CellCoordinate,
    pub placeholder_paragraph_ordinal: usize,
    pub template_table_ordinal: usize,
    pub nested_payload_block_id: LogicalId,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_parent_state_sha256: String,
    pub expected_parent_grid_sha256: String,
    pub expected_parent_table_content_sha256: String,
    pub expected_template_section_sha256: String,
    pub expected_template_state_sha256: String,
    pub expected_template_grid_sha256: String,
    pub expected_template_table_content_sha256: String,
    pub expected_insertion_context_sha256: String,
    pub expected_nested_wrapper_sha256: String,
    pub expected_source_table_count: usize,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
}

impl fmt::Debug for TableNestedTableHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNestedTableHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("parent_table_ordinal", &self.parent_table_ordinal)
            .field("parent_cell", &self.parent_cell)
            .field(
                "placeholder_paragraph_ordinal",
                &self.placeholder_paragraph_ordinal,
            )
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("nested_payload_block_id", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableNestedTableHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    parent_table_ordinal: usize,
    parent_cell: CellCoordinate,
    placeholder_paragraph_ordinal: usize,
    template_table_ordinal: usize,
    nested_payload_block_id: LogicalId,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_parent_state_sha256: String,
    expected_parent_grid_sha256: String,
    expected_parent_table_content_sha256: String,
    expected_template_section_sha256: String,
    expected_template_state_sha256: String,
    expected_template_grid_sha256: String,
    expected_template_table_content_sha256: String,
    expected_insertion_context_sha256: String,
    expected_nested_wrapper_sha256: String,
    expected_source_table_count: usize,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
}

impl TableNestedTableHwpxRequest {
    /// Admits one exact nested-table insertion bound to source, template, parent-cell and flow
    /// state.
    ///
    /// # Errors
    ///
    /// Rejects schema, digest, identity, source, template, selector, flow or finite-limit drift.
    pub fn from_draft(
        draft: TableNestedTableHwpxRequestDraft,
        source: &TableNestedTableHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<Self, TableNestedTableHwpxError> {
        if draft.schema_version != TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION
            || draft.capability_id != TABLE_NESTED_TABLE_CAPABILITY_ID
        {
            return Err(TableNestedTableHwpxError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_parent_state_sha256,
            &draft.expected_parent_grid_sha256,
            &draft.expected_parent_table_content_sha256,
            &draft.expected_template_section_sha256,
            &draft.expected_template_state_sha256,
            &draft.expected_template_grid_sha256,
            &draft.expected_template_table_content_sha256,
            &draft.expected_insertion_context_sha256,
            &draft.expected_nested_wrapper_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        let request = Self {
            schema_version: TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION,
            capability_id: TABLE_NESTED_TABLE_CAPABILITY_ID,
            parent_table_ordinal: draft.parent_table_ordinal,
            parent_cell: draft.parent_cell,
            placeholder_paragraph_ordinal: draft.placeholder_paragraph_ordinal,
            template_table_ordinal: draft.template_table_ordinal,
            nested_payload_block_id: draft.nested_payload_block_id,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_parent_state_sha256: draft.expected_parent_state_sha256,
            expected_parent_grid_sha256: draft.expected_parent_grid_sha256,
            expected_parent_table_content_sha256: draft.expected_parent_table_content_sha256,
            expected_template_section_sha256: draft.expected_template_section_sha256,
            expected_template_state_sha256: draft.expected_template_state_sha256,
            expected_template_grid_sha256: draft.expected_template_grid_sha256,
            expected_template_table_content_sha256: draft.expected_template_table_content_sha256,
            expected_insertion_context_sha256: draft.expected_insertion_context_sha256,
            expected_nested_wrapper_sha256: draft.expected_nested_wrapper_sha256,
            expected_source_table_count: draft.expected_source_table_count,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ = TableNestedTableHwpxBuilder::build(
            &request,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and repeats full admission.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, duplicate-key, unknown-field, malformed or invalid requests.
    pub fn from_json(
        bytes: &[u8],
        source: &TableNestedTableHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<Self, TableNestedTableHwpxError> {
        if bytes.is_empty() || bytes.len() > serialized_limit(&limits) {
            return Err(TableNestedTableHwpxError::InputLimit);
        }
        super::create_hwpx::reject_duplicate_json_keys(bytes)
            .map_err(|_| TableNestedTableHwpxError::InvalidJson)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableNestedTableHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn parent_cell(&self) -> CellCoordinate {
        self.parent_cell
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes every binding under the configured finite deterministic bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<Vec<u8>, TableNestedTableHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the canonical bounded request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<[u8; 32], TableNestedTableHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableNestedTableHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNestedTableHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("parent_table_ordinal", &self.parent_table_ordinal)
            .field("parent_cell", &self.parent_cell)
            .field(
                "placeholder_paragraph_ordinal",
                &self.placeholder_paragraph_ordinal,
            )
            .field("template_table_ordinal", &self.template_table_ordinal)
            .field("nested_payload_block_id", &"<redacted>")
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_parent_state_sha256", &"<redacted>")
            .field("expected_parent_grid_sha256", &"<redacted>")
            .field("expected_parent_table_content_sha256", &"<redacted>")
            .field("expected_template_section_sha256", &"<redacted>")
            .field("expected_template_state_sha256", &"<redacted>")
            .field("expected_template_grid_sha256", &"<redacted>")
            .field("expected_template_table_content_sha256", &"<redacted>")
            .field("expected_insertion_context_sha256", &"<redacted>")
            .field("expected_nested_wrapper_sha256", &"<redacted>")
            .field(
                "expected_source_table_count",
                &self.expected_source_table_count,
            )
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableNestedTableHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_table_count: usize,
    target_table_count: usize,
    payload_insert_index: usize,
    source_parent_state_sha256: String,
    source_parent_grid_sha256: String,
    target_parent_state_sha256: String,
    target_nested_state_sha256: String,
    target_nested_grid_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    target_parent_state: TableRulingState,
    target_nested_state: TableRulingState,
    #[serde(skip_serializing)]
    target_nested_grid: TableGrid,
}

impl TableNestedTableHwpxPlan {
    #[must_use]
    pub const fn target_parent_state(&self) -> &TableRulingState {
        &self.target_parent_state
    }

    #[must_use]
    pub const fn target_nested_state(&self) -> &TableRulingState {
        &self.target_nested_state
    }

    #[must_use]
    pub const fn target_nested_grid(&self) -> &TableGrid {
        &self.target_nested_grid
    }

    /// Serializes the complete plan under the configured deterministic bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<Vec<u8>, TableNestedTableHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the canonical bounded plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<[u8; 32], TableNestedTableHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableNestedTableHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNestedTableHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("payload_insert_index", &self.payload_insert_index)
            .field("parent_cell_count", &self.target_parent_state.cells().len())
            .field("nested_rows", &self.target_nested_grid.rows())
            .field("nested_columns", &self.target_nested_grid.columns())
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableNestedTableHwpxBuilder;

impl TableNestedTableHwpxBuilder {
    /// Revalidates source/template/flow state and builds the exact parent-payload transition.
    ///
    /// # Errors
    ///
    /// Rejects any bound drift, identity collision, invalid state or finite-limit failure.
    pub fn build(
        request: &TableNestedTableHwpxRequest,
        source: &TableNestedTableHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<TableNestedTableHwpxPlan, TableNestedTableHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        validate_cross_table_logical_identities(
            &source.parent.state,
            &source.template.state,
            Some(&request.nested_payload_block_id),
        )?;
        let target_parent_state = state_with_inserted_payload(
            &source.parent.state,
            &source.parent.grid,
            source.parent_cell,
            source.payload_insert_index,
            &TableRulingPayloadBlock {
                block_id: request.nested_payload_block_id.clone(),
                payload_sha256: source.nested_wrapper_sha256.clone(),
            },
            &limits,
        )?;
        let target_table_count = source
            .source_table_count
            .checked_add(1)
            .ok_or(TableNestedTableHwpxError::OutputLimit)?;
        let plan = TableNestedTableHwpxPlan {
            schema_version: TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION,
            capability_id: TABLE_NESTED_TABLE_CAPABILITY_ID,
            request_sha256: hex(request.canonical_sha256(limits)?),
            source_table_count: source.source_table_count,
            target_table_count,
            payload_insert_index: source.payload_insert_index,
            source_parent_state_sha256: hex(source
                .parent
                .state
                .canonical_sha256(limits.ruling.ruling)?),
            source_parent_grid_sha256: hex(source.parent.grid.canonical_sha256()?),
            target_parent_state_sha256: hex(
                target_parent_state.canonical_sha256(limits.ruling.ruling)?
            ),
            target_nested_state_sha256: hex(source
                .template
                .state
                .canonical_sha256(limits.ruling.ruling)?),
            target_nested_grid_sha256: hex(source.template.grid.canonical_sha256()?),
            expected_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            target_parent_state,
            target_nested_state: source.template.state.clone(),
            target_nested_grid: source.template.grid.clone(),
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableNestedTableHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub template_section_sha256: [u8; 32],
    pub insertion_context_sha256: [u8; 32],
    pub nested_wrapper_sha256: [u8; 32],
    pub source_parent_state_sha256: [u8; 32],
    pub target_parent_state_sha256: [u8; 32],
    pub target_nested_state_sha256: [u8; 32],
    pub target_nested_grid_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub parent_payload_block_count: usize,
    pub nested_payload_block_count: usize,
    pub nested_formula_count: usize,
    pub parent_pagination_preserved: bool,
    pub nested_pagination_preserved: bool,
}

impl fmt::Debug for TableNestedTableHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNestedTableHwpxLoweringReceipt")
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field(
                "parent_payload_block_count",
                &self.parent_payload_block_count,
            )
            .field(
                "nested_payload_block_count",
                &self.nested_payload_block_count,
            )
            .field("nested_formula_count", &self.nested_formula_count)
            .field(
                "parent_pagination_preserved",
                &self.parent_pagination_preserved,
            )
            .field(
                "nested_pagination_preserved",
                &self.nested_pagination_preserved,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableNestedTableHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub parent_binding: TableRulingHwpxBinding,
    pub nested_binding: TableRulingHwpxBinding,
    pub parent_table_ordinal: usize,
    pub nested_table_ordinal: usize,
    pub receipt: TableNestedTableHwpxLoweringReceipt,
}

impl fmt::Debug for TableNestedTableHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNestedTableHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("parent_table_ordinal", &self.parent_table_ordinal)
            .field("nested_table_ordinal", &self.nested_table_ordinal)
            .field("receipt", &self.receipt)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableNestedTableHwpxLowerer;

impl TableNestedTableHwpxLowerer {
    /// Inserts one complete inline nested table and returns parts only after exact parent, nested,
    /// formula, pagination and table-count readback succeeds.
    ///
    /// # Errors
    ///
    /// Rejects source/template/request/plan/flow/identity/readback drift without returning partial
    /// output.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_at_cell_placeholder(
        header: &[u8],
        section: &[u8],
        parent_binding: &TableRulingHwpxBinding,
        template_section: &[u8],
        template_binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableNestedTableHwpxRequest,
        plan: &TableNestedTableHwpxPlan,
        limits: TableNestedTableHwpxLimits,
    ) -> Result<TableNestedTableHwpxLoweredParts, TableNestedTableHwpxError> {
        let source = TableNestedTableHwpxReader::read_context(
            header,
            section,
            request.parent_table_ordinal,
            request.parent_cell,
            request.placeholder_paragraph_ordinal,
            parent_binding,
            template_section,
            request.template_table_ordinal,
            template_binding,
            limits,
        )?;
        validate_request_source(request, &source, current_document_flow_sha256, &limits)?;
        let rebuilt = TableNestedTableHwpxBuilder::build(
            request,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableNestedTableHwpxError::PlanBindingMismatch);
        }
        let wrapper = super::insertion_wrapper(template_section, request.template_table_ordinal)?;
        if super::insertion_wrapper_semantic_digest(
            template_section,
            request.template_table_ordinal,
        )? != source.nested_wrapper_sha256
        {
            return Err(TableNestedTableHwpxError::SourceBindingMismatch);
        }
        ensure_template_native_identity_available(
            section,
            template_section,
            request.template_table_ordinal,
        )?;
        let document = PreservingXmlDocument::parse(section)?;
        let (placeholder, payload_insert_index) = selected_empty_cell_paragraph(
            section,
            &document,
            request.parent_table_ordinal,
            request.parent_cell,
            request.placeholder_paragraph_ordinal,
            source.parent.grid.master_cell_count(),
        )?;
        if payload_insert_index != plan.payload_insert_index {
            return Err(TableNestedTableHwpxError::PlanBindingMismatch);
        }
        let placeholder_span = super::element(&document, placeholder)?
            .outer_span()
            .ok_or(TableNestedTableHwpxError::ReadbackMismatch)?;
        let nested_table_ordinal = super::tables_before_offset(&document, placeholder_span.start());
        let mut edits = vec![RawEdit {
            start: placeholder_span.start(),
            end: placeholder_span.end(),
            replacement: wrapper,
        }];
        let output_section = super::apply_edits(
            section,
            &mut edits,
            limits.ruling.layout.config().output_bytes,
        )?;
        let output_parent_binding = parent_binding_with_inserted_payload(
            parent_binding,
            &source.parent,
            request.parent_cell,
            payload_insert_index,
            request.nested_payload_block_id.clone(),
        )?;
        let verified = verify_lowered_state(
            header,
            &output_section,
            (&output_parent_binding, template_binding),
            (request.parent_table_ordinal, nested_table_ordinal),
            &source,
            plan,
            &limits,
        )?;
        let receipt = lowering_receipt(
            header,
            &output_section,
            request,
            plan,
            &source,
            &verified,
            &limits,
        )?;
        Ok(TableNestedTableHwpxLoweredParts {
            header: header.to_vec(),
            section: output_section,
            parent_binding: output_parent_binding,
            nested_binding: template_binding.clone(),
            parent_table_ordinal: request.parent_table_ordinal,
            nested_table_ordinal,
            receipt,
        })
    }
}

struct VerifiedLoweredState {
    target_table_count: usize,
    parent_payload_block_count: usize,
    nested_payload_block_count: usize,
    nested_formula_count: usize,
    parent_pagination_preserved: bool,
    nested_pagination_preserved: bool,
}

fn verify_lowered_state(
    header: &[u8],
    output_section: &[u8],
    bindings: (&TableRulingHwpxBinding, &TableRulingHwpxBinding),
    ordinals: (usize, usize),
    source: &TableNestedTableHwpxReadback,
    plan: &TableNestedTableHwpxPlan,
    limits: &TableNestedTableHwpxLimits,
) -> Result<VerifiedLoweredState, TableNestedTableHwpxError> {
    let output_parent = TableRulingHwpxReader::read_existing_preserving_caption(
        header,
        output_section,
        ordinals.0,
        bindings.0,
        &limits.ruling,
    )?;
    let output_nested = TableRulingHwpxReader::read_existing_preserving_caption(
        header,
        output_section,
        ordinals.1,
        bindings.1,
        &limits.ruling,
    )?;
    let output_parent_pagination =
        TablePaginationHwpxReader::read_in_section(output_section, ordinals.0, limits.pagination)?;
    let output_nested_pagination =
        TablePaginationHwpxReader::read_in_section(output_section, ordinals.1, limits.pagination)?;
    let output_nested_placement = TablePlacementHwpxReader::read_in_section(
        output_section,
        ordinals.1,
        limits.ruling.layout,
    )?;
    let target_table_count =
        TablePaginationHwpxReader::count_in_section(output_section, limits.pagination)?;
    let parent_pagination_preserved =
        same_pagination_policy(&source.parent_pagination, &output_parent_pagination);
    let nested_pagination_preserved = source.template_pagination == output_nested_pagination;
    if output_parent.grid != source.parent.grid
        || output_parent.state != *plan.target_parent_state()
        || output_nested.grid != *plan.target_nested_grid()
        || output_nested.state != *plan.target_nested_state()
        || !parent_pagination_preserved
        || !nested_pagination_preserved
        || output_nested_placement != source.template_placement
        || !output_nested_placement.attachment_flags.treat_as_char
        || target_table_count != plan.target_table_count
    {
        return Err(TableNestedTableHwpxError::ReadbackMismatch);
    }
    Ok(VerifiedLoweredState {
        target_table_count,
        parent_payload_block_count: output_parent.payload_block_count,
        nested_payload_block_count: output_nested.payload_block_count,
        nested_formula_count: output_nested.formula_count,
        parent_pagination_preserved,
        nested_pagination_preserved,
    })
}

fn lowering_receipt(
    header: &[u8],
    output_section: &[u8],
    request: &TableNestedTableHwpxRequest,
    plan: &TableNestedTableHwpxPlan,
    source: &TableNestedTableHwpxReadback,
    verified: &VerifiedLoweredState,
    limits: &TableNestedTableHwpxLimits,
) -> Result<TableNestedTableHwpxLoweringReceipt, TableNestedTableHwpxError> {
    Ok(TableNestedTableHwpxLoweringReceipt {
        profile_id: TABLE_NESTED_TABLE_HWPX_PROFILE_ID,
        source_header_sha256: source.header_sha256,
        output_header_sha256: Sha256::digest(header).into(),
        source_section_sha256: source.section_sha256,
        output_section_sha256: Sha256::digest(output_section).into(),
        template_section_sha256: source.template_section_sha256,
        insertion_context_sha256: parse_digest(&source.insertion_context_sha256)?,
        nested_wrapper_sha256: parse_digest(&source.nested_wrapper_sha256)?,
        source_parent_state_sha256: source.parent.state.canonical_sha256(limits.ruling.ruling)?,
        target_parent_state_sha256: plan
            .target_parent_state()
            .canonical_sha256(limits.ruling.ruling)?,
        target_nested_state_sha256: plan
            .target_nested_state()
            .canonical_sha256(limits.ruling.ruling)?,
        target_nested_grid_sha256: plan.target_nested_grid().canonical_sha256()?,
        request_sha256: request.canonical_sha256(*limits)?,
        plan_sha256: plan.canonical_sha256(*limits)?,
        before_document_flow_sha256: parse_digest(&request.expected_document_flow_sha256)?,
        after_document_flow_sha256: parse_digest(&request.target_document_flow_sha256)?,
        source_table_count: source.source_table_count,
        target_table_count: verified.target_table_count,
        parent_payload_block_count: verified.parent_payload_block_count,
        nested_payload_block_count: verified.nested_payload_block_count,
        nested_formula_count: verified.nested_formula_count,
        parent_pagination_preserved: verified.parent_pagination_preserved,
        nested_pagination_preserved: verified.nested_pagination_preserved,
    })
}

#[derive(Debug, Error)]
pub enum TableNestedTableHwpxError {
    #[error("unsupported nested-table HWPX schema or capability")]
    UnsupportedVersion,
    #[error("nested-table HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid nested-table HWPX JSON")]
    InvalidJson,
    #[error("invalid nested-table HWPX digest or binding")]
    InvalidBinding,
    #[error("nested-table HWPX selector resolves to a covered non-master cell")]
    CoveredCellSelector,
    #[error("nested-table HWPX source, template, selector or flow drifted")]
    SourceBindingMismatch,
    #[error("nested-table HWPX requires a distinct target document flow")]
    FlowBindingMismatch,
    #[error("nested-table HWPX logical identities collide across parent and nested tables")]
    IdentityConflict,
    #[error("nested-table HWPX template is not an exact caption-free inline table paragraph")]
    UnsupportedTemplateProfile,
    #[error("nested-table HWPX native object or formula identity collides")]
    NativeIdentityCollision,
    #[error("nested-table HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("nested-table HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("nested-table HWPX serialization failed")]
    Serialization,
    #[error("nested-table HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    Model(#[from] TableRulingError),
    #[error(transparent)]
    Ruling(#[from] TableRulingHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
    #[error(transparent)]
    Placement(#[from] TablePlacementHwpxError),
    #[error(transparent)]
    Xml(#[from] crate::preserving_xml::PreservingXmlError),
}

impl TableNestedTableHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_nested_table_hwpx_unsupported_version",
            Self::InputLimit => "table_nested_table_hwpx_input_limit",
            Self::InvalidJson => "table_nested_table_hwpx_invalid_json",
            Self::InvalidBinding => "table_nested_table_hwpx_invalid_binding",
            Self::CoveredCellSelector => "table_nested_table_hwpx_covered_cell_selector",
            Self::SourceBindingMismatch => "table_nested_table_hwpx_source_binding_mismatch",
            Self::FlowBindingMismatch => "table_nested_table_hwpx_flow_binding_mismatch",
            Self::IdentityConflict => "table_nested_table_hwpx_identity_conflict",
            Self::UnsupportedTemplateProfile => {
                "table_nested_table_hwpx_unsupported_template_profile"
            }
            Self::NativeIdentityCollision => "table_nested_table_hwpx_native_identity_collision",
            Self::PlanBindingMismatch => "table_nested_table_hwpx_plan_binding_mismatch",
            Self::ReadbackMismatch => "table_nested_table_hwpx_readback_mismatch",
            Self::Serialization => "table_nested_table_hwpx_serialization",
            Self::OutputLimit => "table_nested_table_hwpx_output_limit",
            Self::Grid(_) => "table_nested_table_hwpx_grid",
            Self::Model(_) => "table_nested_table_hwpx_model",
            Self::Ruling(_) => "table_nested_table_hwpx_ruling",
            Self::Pagination(_) => "table_nested_table_hwpx_pagination",
            Self::Placement(_) => "table_nested_table_hwpx_placement",
            Self::Xml(_) => "table_nested_table_hwpx_xml",
        }
    }
}

fn validate_request_source(
    request: &TableNestedTableHwpxRequest,
    source: &TableNestedTableHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableNestedTableHwpxLimits,
) -> Result<(), TableNestedTableHwpxError> {
    require_digest(current_document_flow_sha256)?;
    if source.profile_id != TABLE_NESTED_TABLE_HWPX_PROFILE_ID
        || request.parent_table_ordinal != source.parent_table_ordinal
        || request.parent_cell != source.parent_cell
        || request.placeholder_paragraph_ordinal != source.placeholder_paragraph_ordinal
        || request.template_table_ordinal != source.template_table_ordinal
        || request.expected_header_sha256 != hex(source.header_sha256)
        || request.expected_section_sha256 != hex(source.section_sha256)
        || request.expected_parent_state_sha256
            != hex(source.parent.state.canonical_sha256(limits.ruling.ruling)?)
        || request.expected_parent_grid_sha256 != hex(source.parent.grid.canonical_sha256()?)
        || request.expected_parent_table_content_sha256 != hex(source.parent.table_content_sha256)
        || request.expected_template_section_sha256 != hex(source.template_section_sha256)
        || request.expected_template_state_sha256
            != hex(source
                .template
                .state
                .canonical_sha256(limits.ruling.ruling)?)
        || request.expected_template_grid_sha256 != hex(source.template.grid.canonical_sha256()?)
        || request.expected_template_table_content_sha256
            != hex(source.template.table_content_sha256)
        || request.expected_insertion_context_sha256 != source.insertion_context_sha256
        || request.expected_nested_wrapper_sha256 != source.nested_wrapper_sha256
        || request.expected_source_table_count != source.source_table_count
        || request.expected_document_flow_sha256 != current_document_flow_sha256
    {
        return Err(TableNestedTableHwpxError::SourceBindingMismatch);
    }
    if request.expected_document_flow_sha256 == request.target_document_flow_sha256 {
        return Err(TableNestedTableHwpxError::FlowBindingMismatch);
    }
    Ok(())
}

fn state_with_inserted_payload(
    source: &TableRulingState,
    grid: &TableGrid,
    coordinate: CellCoordinate,
    payload_insert_index: usize,
    payload: &TableRulingPayloadBlock,
    limits: &TableNestedTableHwpxLimits,
) -> Result<TableRulingState, TableNestedTableHwpxError> {
    let selected_master = grid.master_cell_at(coordinate)?;
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(source.cells().len())
        .map_err(|_| TableNestedTableHwpxError::OutputLimit)?;
    for cell in source.cells() {
        let mut blocks = cell.payload().to_vec();
        if cell.master_cell_id() == &selected_master.master_cell_id {
            if payload_insert_index > blocks.len() {
                return Err(TableNestedTableHwpxError::InvalidBinding);
            }
            blocks
                .try_reserve(1)
                .map_err(|_| TableNestedTableHwpxError::OutputLimit)?;
            blocks.insert(payload_insert_index, payload.clone());
        }
        cells.push(TableRulingCellDraft {
            master_cell_id: cell.master_cell_id().clone(),
            coordinate: cell.coordinate(),
            payload: blocks,
            properties: cell.properties().clone(),
            formula: cell.formula().map(formula_draft),
        });
    }
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: source.table_id().clone(),
            frame: source.frame(),
            grid_sha256: source.grid_sha256().to_owned(),
            table_properties_sha256: source.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: source.row_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: source.column_boundaries_hwpunit().to_vec(),
            edges: source.edges().to_vec(),
            cells,
        },
        grid,
        limits.ruling.formula,
        limits.ruling.ruling,
    )?)
}

fn formula_draft(formula: &domain_ir::FormulaCell) -> FormulaCellDraft {
    FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner: formula.owner(),
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: formula.ast().expression().clone(),
        },
        cache: formula.cache().clone(),
        number_format: formula.number_format(),
    }
}

fn parent_binding_with_inserted_payload(
    binding: &TableRulingHwpxBinding,
    parent: &TableRulingHwpxReadback,
    coordinate: CellCoordinate,
    payload_insert_index: usize,
    payload_id: LogicalId,
) -> Result<TableRulingHwpxBinding, TableNestedTableHwpxError> {
    let master_id = parent
        .grid
        .master_cell_at(coordinate)?
        .master_cell_id
        .clone();
    let mut output = binding.clone();
    let cell = output
        .cells
        .iter_mut()
        .find(|cell| cell.master_cell_id == master_id)
        .ok_or(TableNestedTableHwpxError::InvalidBinding)?;
    if payload_insert_index > cell.payload_block_ids.len() {
        return Err(TableNestedTableHwpxError::InvalidBinding);
    }
    cell.payload_block_ids
        .try_reserve(1)
        .map_err(|_| TableNestedTableHwpxError::OutputLimit)?;
    cell.payload_block_ids
        .insert(payload_insert_index, payload_id);
    Ok(output)
}

fn validate_cross_table_logical_identities(
    parent: &TableRulingState,
    nested: &TableRulingState,
    inserted_payload_id: Option<&LogicalId>,
) -> Result<(), TableNestedTableHwpxError> {
    let mut identifiers = BTreeSet::new();
    for state in [parent, nested] {
        if !identifiers.insert(state.table_id().clone()) {
            return Err(TableNestedTableHwpxError::IdentityConflict);
        }
        for cell in state.cells() {
            if !identifiers.insert(cell.master_cell_id().clone()) {
                return Err(TableNestedTableHwpxError::IdentityConflict);
            }
            for block in cell.payload() {
                if !identifiers.insert(block.block_id.clone()) {
                    return Err(TableNestedTableHwpxError::IdentityConflict);
                }
            }
        }
    }
    if inserted_payload_id.is_some_and(|identifier| !identifiers.insert(identifier.clone())) {
        return Err(TableNestedTableHwpxError::IdentityConflict);
    }
    Ok(())
}

fn selected_empty_cell_paragraph(
    source: &[u8],
    document: &PreservingXmlDocument,
    table_ordinal: usize,
    coordinate: CellCoordinate,
    paragraph_ordinal: usize,
    expected_cell_count: usize,
) -> Result<(usize, usize), TableNestedTableHwpxError> {
    let table = super::selected_table(document, table_ordinal)?;
    let cells = super::selected_cells(document, table, expected_cell_count)?;
    let cell = cells
        .into_iter()
        .find(|(_, address)| *address == coordinate)
        .map(|(index, _)| index)
        .ok_or(TableNestedTableHwpxError::InvalidBinding)?;
    let sub_list = super::unique_child(document, cell, "subList")?;
    let mut paragraphs = Vec::new();
    let mut child = super::element(document, sub_list)?.first_child();
    while let Some(index) = child {
        let value = super::element(document, index)?;
        if !super::has_name(value, "p") {
            return Err(TableNestedTableHwpxError::InvalidBinding);
        }
        paragraphs.push(index);
        child = value.next_sibling();
    }
    let paragraph = *paragraphs
        .get(paragraph_ordinal)
        .ok_or(TableNestedTableHwpxError::InvalidBinding)?;
    if !super::is_empty_scaffold(source, document, paragraph)? {
        return Err(TableNestedTableHwpxError::InvalidBinding);
    }
    let mut payload_insert_index = 0_usize;
    for prior in paragraphs.iter().take(paragraph_ordinal) {
        if super::is_payload_paragraph(source, document, *prior)? {
            payload_insert_index = payload_insert_index
                .checked_add(1)
                .ok_or(TableNestedTableHwpxError::OutputLimit)?;
        }
    }
    Ok((paragraph, payload_insert_index))
}

fn insertion_context_digest(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraph: usize,
    table_ordinal: usize,
    coordinate: CellCoordinate,
    paragraph_ordinal: usize,
) -> Result<String, TableNestedTableHwpxError> {
    let bytes = super::element_bytes(source, super::element(document, paragraph)?)?;
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-nested-table-hwpx-insertion-context/v1\0");
    digest.update(Sha256::digest(source));
    digest.update(table_ordinal.to_le_bytes());
    digest.update(coordinate.row.to_le_bytes());
    digest.update(coordinate.column.to_le_bytes());
    digest.update(paragraph_ordinal.to_le_bytes());
    digest.update(Sha256::digest(bytes));
    Ok(hex(digest.finalize()))
}

fn ensure_template_native_identity_available(
    destination_section: &[u8],
    template_section: &[u8],
    template_table_ordinal: usize,
) -> Result<(), TableNestedTableHwpxError> {
    super::ensure_native_table_id_available(
        destination_section,
        template_section,
        template_table_ordinal,
    )?;
    let template = PreservingXmlDocument::parse(template_section)?;
    let template_table = super::selected_table(&template, template_table_ordinal)?;
    let destination = PreservingXmlDocument::parse(destination_section)?;
    let mut begin_ids = BTreeSet::new();
    let mut field_ids = BTreeSet::new();
    for (index, value) in template.elements().iter().enumerate() {
        if !super::is_descendant(&template, index, template_table)?
            || !super::has_name(value, "fieldBegin")
        {
            continue;
        }
        begin_ids.insert(super::attribute(value, "id")?.to_owned());
        field_ids.insert(super::attribute(value, "fieldid")?.to_owned());
    }
    for value in destination.elements() {
        if super::has_name(value, "fieldBegin")
            && (begin_ids.contains(super::attribute(value, "id")?)
                || field_ids.contains(super::attribute(value, "fieldid")?))
        {
            return Err(TableNestedTableHwpxError::NativeIdentityCollision);
        }
    }
    Ok(())
}

fn validate_template_payload_profile(
    template_section: &[u8],
    template_table_ordinal: usize,
) -> Result<(), TableNestedTableHwpxError> {
    const EXTERNAL_RESOURCE_ELEMENTS: &[&str] =
        &["pic", "ole", "chart", "video", "audio", "embeddedObject"];
    const EXTERNAL_RESOURCE_ATTRIBUTES: &[&str] = &["binaryItemIDRef", "chartIDRef"];

    let document = PreservingXmlDocument::parse(template_section)?;
    let table = super::selected_table(&document, template_table_ordinal)?;
    let run = super::element(&document, table)?
        .parent()
        .ok_or(TableNestedTableHwpxError::UnsupportedTemplateProfile)?;
    let paragraph = super::element(&document, run)?
        .parent()
        .ok_or(TableNestedTableHwpxError::UnsupportedTemplateProfile)?;
    if !super::has_name(super::element(&document, run)?, "run")
        || !super::has_name(super::element(&document, paragraph)?, "p")
        || super::element(&document, paragraph)?.parent() != Some(document.root_element())
    {
        return Err(TableNestedTableHwpxError::UnsupportedTemplateProfile);
    }
    for (index, value) in document.elements().iter().enumerate() {
        if !super::is_descendant(&document, index, table)? {
            continue;
        }
        if EXTERNAL_RESOURCE_ELEMENTS.contains(&value.name().local_name())
            || value.attributes().iter().any(|attribute| {
                EXTERNAL_RESOURCE_ATTRIBUTES.contains(&attribute.name().local_name())
            })
        {
            return Err(TableNestedTableHwpxError::UnsupportedTemplateProfile);
        }
    }
    Ok(())
}

fn same_pagination_policy(
    before: &TablePaginationHwpxReadback,
    after: &TablePaginationHwpxReadback,
) -> bool {
    before.profile_id == after.profile_id
        && before.page_split == after.page_split
        && before.repeat_header_rows == after.repeat_header_rows
        && before.row_count == after.row_count
        && before.column_count == after.column_count
        && before.caption == after.caption
}

fn serialized_limit(limits: &TableNestedTableHwpxLimits) -> usize {
    limits
        .ruling
        .grid
        .config()
        .serialized_bytes
        .min(limits.ruling.ruling.config().serialized_bytes)
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limit: usize,
) -> Result<Vec<u8>, TableNestedTableHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableNestedTableHwpxError::Serialization)?;
    if bytes.len() > limit {
        return Err(TableNestedTableHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn require_digest(value: &str) -> Result<(), TableNestedTableHwpxError> {
    if value.len() != 64 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(TableNestedTableHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableNestedTableHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (slot, chunk) in output.iter_mut().zip(value.as_bytes().chunks_exact(2)) {
        let text =
            std::str::from_utf8(chunk).map_err(|_| TableNestedTableHwpxError::InvalidBinding)?;
        *slot =
            u8::from_str_radix(text, 16).map_err(|_| TableNestedTableHwpxError::InvalidBinding)?;
    }
    Ok(output)
}

fn hex(value: impl AsRef<[u8]>) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len().saturating_mul(2));
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
