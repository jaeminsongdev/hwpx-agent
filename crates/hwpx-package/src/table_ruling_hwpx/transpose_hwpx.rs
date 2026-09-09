use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    TABLE_RULING_SCHEMA_VERSION, TableGrid, TableGridError, TableRulingAxis, TableRulingCellDraft,
    TableRulingEdge, TableRulingError, TableRulingFrame, TableRulingState, TableRulingStateDraft,
    TableTransposeBuilder, TableTransposeError, TableTransposeFormulaPolicy, TableTransposeLimits,
    TableTransposePlan, TableTransposeRequest, TableTransposeRequestDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{
    TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits, TableRulingHwpxReadback,
    TableRulingHwpxReader,
};
use crate::{
    TablePaginationHwpxError, TablePaginationHwpxLimits, TablePaginationHwpxReadback,
    TablePaginationHwpxReader,
};

pub const TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-transpose-hwpx/v1";
pub const TABLE_TRANSPOSE_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-transpose-hwpx.hancom-2020-wrapper/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableTransposeHwpxLimits {
    pub transpose: TableTransposeLimits,
    pub ruling: TableRulingHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableTransposeHwpxReadback {
    pub profile_id: &'static str,
    pub table_ordinal: usize,
    pub ruling: TableRulingHwpxReadback,
    pub pagination: TablePaginationHwpxReadback,
}

impl fmt::Debug for TableTransposeHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("rows", &self.ruling.grid.rows())
            .field("columns", &self.ruling.grid.columns())
            .field("master_cell_count", &self.ruling.grid.master_cell_count())
            .field("merged_cell_count", &merged_cell_count(&self.ruling.grid))
            .field("formula_count", &self.ruling.formula_count)
            .field("page_split", &self.pagination.page_split)
            .field("repeat_header_rows", &self.pagination.repeat_header_rows)
            .field("has_caption", &self.pagination.caption.is_some())
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableTransposeHwpxReader;

impl TableTransposeHwpxReader {
    /// Reads one complete current-Hangul-2020 table for exact native transposition.
    ///
    /// Arbitrary rectangular dimensions, rectangular merged cells, nonuniform physical tracks,
    /// payload blocks, cell properties, diagonals, page-split policy and captions are retained.
    /// Formula-bearing tables and repeat-header rows have no exact native transpose mapping in
    /// this profile and are rejected rather than approximated.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, over-limit, formula-bearing or repeat-header input.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: TableTransposeHwpxLimits,
    ) -> Result<TableTransposeHwpxReadback, TableTransposeHwpxError> {
        let ruling = TableRulingHwpxReader::read_existing_preserving_caption(
            header,
            section,
            table_ordinal,
            binding,
            &limits.ruling,
        )?;
        let pagination =
            TablePaginationHwpxReader::read_in_section(section, table_ordinal, limits.pagination)?;
        if pagination.row_count != ruling.grid.rows()
            || pagination.column_count != ruling.grid.columns()
        {
            return Err(TableTransposeHwpxError::ReadbackMismatch);
        }
        require_source_profile(&ruling, &pagination)?;
        Ok(TableTransposeHwpxReadback {
            profile_id: TABLE_TRANSPOSE_HWPX_PROFILE_ID,
            table_ordinal,
            ruling,
            pagination,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableTransposeHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub transpose: TableTransposeRequestDraft,
}

impl fmt::Debug for TableTransposeHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_source_grid_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .field("transpose", &self.transpose)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTransposeHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_ordinal: usize,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    transpose: TableTransposeRequest,
}

impl TableTransposeHwpxRequest {
    /// Binds one complete domain transpose request to exact source parts, state, grid and flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, digest, source, formula, pagination, flow or finite-bound drift.
    pub fn from_draft(
        draft: TableTransposeHwpxRequestDraft,
        source: &TableTransposeHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTransposeHwpxLimits,
    ) -> Result<Self, TableTransposeHwpxError> {
        if draft.schema_version != TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION {
            return Err(TableTransposeHwpxError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_source_state_sha256,
            &draft.expected_source_grid_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        let transpose = TableTransposeRequest::from_draft(
            draft.transpose,
            &source.ruling.grid,
            limits.ruling.formula,
            limits.transpose,
        )?;
        let request = Self {
            schema_version: TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION,
            capability_id: transpose.capability_id(),
            table_ordinal: draft.table_ordinal,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_source_grid_sha256: draft.expected_source_grid_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            transpose,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ = TableTransposeHwpxBuilder::build(
            &request,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies the same admission as [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or semantically invalid JSON.
    pub fn from_json(
        bytes: &[u8],
        source: &TableTransposeHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTransposeHwpxLimits,
    ) -> Result<Self, TableTransposeHwpxError> {
        if bytes.is_empty()
            || bytes.len() > limits.transpose.config().input_bytes
            || bytes.len() > limits.ruling.ruling.config().input_bytes
        {
            return Err(TableTransposeHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableTransposeHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn table_ordinal(&self) -> usize {
        self.table_ordinal
    }

    #[must_use]
    pub const fn transpose(&self) -> &TableTransposeRequest {
        &self.transpose
    }

    #[must_use]
    pub fn expected_document_flow_sha256(&self) -> &str {
        &self.expected_document_flow_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes the complete typed request under both configured output bounds.
    ///
    /// # Errors
    ///
    /// Rejects serialization or finite output failure.
    pub fn canonical_json(
        &self,
        limits: TableTransposeHwpxLimits,
    ) -> Result<Vec<u8>, TableTransposeHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableTransposeHwpxLimits,
    ) -> Result<[u8; 32], TableTransposeHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableTransposeHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_source_grid_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .field("transpose", &self.transpose)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTransposeHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    source_grid_sha256: String,
    target_grid_sha256: String,
    source_pagination_sha256: String,
    target_pagination_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    domain: TableTransposePlan,
    target_state: TableRulingState,
    #[serde(skip)]
    target_grid: TableGrid,
}

impl TableTransposeHwpxPlan {
    #[must_use]
    pub const fn domain(&self) -> &TableTransposePlan {
        &self.domain
    }

    #[must_use]
    pub const fn target_state(&self) -> &TableRulingState {
        &self.target_state
    }

    #[must_use]
    pub const fn target_grid(&self) -> &TableGrid {
        &self.target_grid
    }

    /// Serializes every semantic and integrity binding under both configured output bounds.
    ///
    /// # Errors
    ///
    /// Rejects serialization or finite output failure.
    pub fn canonical_json(
        &self,
        limits: TableTransposeHwpxLimits,
    ) -> Result<Vec<u8>, TableTransposeHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableTransposeHwpxLimits,
    ) -> Result<[u8; 32], TableTransposeHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableTransposeHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("source_rows", &self.target_grid.columns())
            .field("source_columns", &self.target_grid.rows())
            .field("target_rows", &self.target_grid.rows())
            .field("target_columns", &self.target_grid.columns())
            .field("domain", &self.domain)
            .field("target_state", &self.target_state)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableTransposeHwpxBuilder;

impl TableTransposeHwpxBuilder {
    /// Revalidates exact source state and builds a complete native transpose target.
    ///
    /// # Errors
    ///
    /// Rejects source, flow, domain, geometry, edge, payload, property or bound drift.
    pub fn build(
        request: &TableTransposeHwpxRequest,
        source: &TableTransposeHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableTransposeHwpxLimits,
    ) -> Result<TableTransposeHwpxPlan, TableTransposeHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        let domain = TableTransposeBuilder::build(
            &request.transpose,
            &source.ruling.grid,
            limits.ruling.grid,
            limits.ruling.formula,
            limits.transpose,
        )?;
        let target_grid = TableGrid::new(
            domain.rows(),
            domain.columns(),
            domain.master_cells().to_vec(),
            limits.ruling.grid,
        )?;
        let target_state = transposed_state(source, &domain, &target_grid, &limits)?;
        let source_state_sha256 =
            hex(source.ruling.state.canonical_sha256(limits.ruling.ruling)?);
        let target_state_sha256 = hex(target_state.canonical_sha256(limits.ruling.ruling)?);
        let semantic_noop =
            source.ruling.grid == target_grid && source.ruling.state == target_state;
        if semantic_noop
            != (request.expected_document_flow_sha256 == request.target_document_flow_sha256)
        {
            return Err(TableTransposeHwpxError::FlowBindingMismatch);
        }
        let plan = TableTransposeHwpxPlan {
            schema_version: TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: hex(request.canonical_sha256(limits)?),
            source_state_sha256,
            target_state_sha256,
            source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
            target_grid_sha256: hex(target_grid.canonical_sha256()?),
            source_pagination_sha256: pagination_digest(&source.pagination),
            target_pagination_sha256: transposed_pagination_digest(&source.pagination),
            expected_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            domain,
            target_state,
            target_grid,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableTransposeHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub source_grid_sha256: [u8; 32],
    pub target_grid_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub source_rows: u32,
    pub source_columns: u32,
    pub target_rows: u32,
    pub target_columns: u32,
    pub preserved_master_cell_count: usize,
    pub preserved_merged_cell_count: usize,
    pub preserved_payload_block_count: usize,
    pub preserved_edge_count: usize,
    pub preserved_cell_property_count: usize,
    pub added_border_fill_count: usize,
    pub page_split_preserved: bool,
    pub repeat_header_preserved: bool,
    pub caption_preserved: bool,
}

impl fmt::Debug for TableTransposeHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("source_rows", &self.source_rows)
            .field("source_columns", &self.source_columns)
            .field("target_rows", &self.target_rows)
            .field("target_columns", &self.target_columns)
            .field(
                "preserved_master_cell_count",
                &self.preserved_master_cell_count,
            )
            .field(
                "preserved_merged_cell_count",
                &self.preserved_merged_cell_count,
            )
            .field(
                "preserved_payload_block_count",
                &self.preserved_payload_block_count,
            )
            .field("preserved_edge_count", &self.preserved_edge_count)
            .field(
                "preserved_cell_property_count",
                &self.preserved_cell_property_count,
            )
            .field("added_border_fill_count", &self.added_border_fill_count)
            .field("page_split_preserved", &self.page_split_preserved)
            .field("repeat_header_preserved", &self.repeat_header_preserved)
            .field("caption_preserved", &self.caption_preserved)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableTransposeHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub receipt: TableTransposeHwpxLoweringReceipt,
}

impl fmt::Debug for TableTransposeHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableTransposeHwpxLowerer;

impl TableTransposeHwpxLowerer {
    /// Transposes one exact native table and returns only after complete semantic reopen.
    ///
    /// # Errors
    ///
    /// Rejects source, request, plan, state, grid, flow, pagination or readback drift without
    /// returning partial parts.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableTransposeHwpxRequest,
        plan: &TableTransposeHwpxPlan,
        limits: TableTransposeHwpxLimits,
    ) -> Result<TableTransposeHwpxLoweredParts, TableTransposeHwpxError> {
        let source = TableTransposeHwpxReader::read_existing(
            header,
            section,
            request.table_ordinal,
            binding,
            limits,
        )?;
        validate_request_source(request, &source, current_document_flow_sha256, &limits)?;
        let rebuilt = TableTransposeHwpxBuilder::build(
            request,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableTransposeHwpxError::PlanBindingMismatch);
        }
        let source_table_count =
            TablePaginationHwpxReader::count_in_section(section, limits.pagination)?;
        let rendered = super::render_transpose_existing(
            header,
            section,
            request.table_ordinal,
            binding,
            &source.ruling.state,
            plan.target_state(),
            plan.target_grid(),
            &limits.ruling,
        )?;
        let target_binding = super::binding_from_state(plan.target_state(), plan.target_grid())?;
        let reopened = TableTransposeHwpxReader::read_existing(
            &rendered.header,
            &rendered.section,
            request.table_ordinal,
            &target_binding,
            limits,
        )?;
        let target_table_count =
            TablePaginationHwpxReader::count_in_section(&rendered.section, limits.pagination)?;
        if reopened.ruling.grid != *plan.target_grid()
            || reopened.ruling.state != *plan.target_state()
            || reopened.pagination.page_split != source.pagination.page_split
            || reopened.pagination.repeat_header_rows != 0
            || reopened.pagination.row_count != source.pagination.column_count
            || reopened.pagination.column_count != source.pagination.row_count
            || reopened.pagination.caption != source.pagination.caption
            || reopened.ruling.payload_block_count != source.ruling.payload_block_count
            || reopened.ruling.formula_count != 0
            || target_table_count != source_table_count
        {
            return Err(TableTransposeHwpxError::ReadbackMismatch);
        }
        let receipt = TableTransposeHwpxLoweringReceipt {
            profile_id: TABLE_TRANSPOSE_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&rendered.header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&rendered.section).into(),
            source_state_sha256: source.ruling.state.canonical_sha256(limits.ruling.ruling)?,
            target_state_sha256: plan.target_state().canonical_sha256(limits.ruling.ruling)?,
            source_grid_sha256: source.ruling.grid.canonical_sha256()?,
            target_grid_sha256: plan.target_grid().canonical_sha256()?,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(request.expected_document_flow_sha256())?,
            after_document_flow_sha256: parse_digest(request.target_document_flow_sha256())?,
            source_table_count,
            target_table_count,
            source_rows: source.ruling.grid.rows(),
            source_columns: source.ruling.grid.columns(),
            target_rows: reopened.ruling.grid.rows(),
            target_columns: reopened.ruling.grid.columns(),
            preserved_master_cell_count: reopened.ruling.grid.master_cell_count(),
            preserved_merged_cell_count: merged_cell_count(&reopened.ruling.grid),
            preserved_payload_block_count: reopened.ruling.payload_block_count,
            preserved_edge_count: reopened.ruling.state.edges().len(),
            preserved_cell_property_count: reopened.ruling.state.cells().len(),
            added_border_fill_count: rendered.added_border_fill_count,
            page_split_preserved: true,
            repeat_header_preserved: true,
            caption_preserved: true,
        };
        Ok(TableTransposeHwpxLoweredParts {
            header: rendered.header,
            section: rendered.section,
            binding: target_binding,
            receipt,
        })
    }
}

#[derive(Debug, Error)]
pub enum TableTransposeHwpxError {
    #[error("unsupported table transpose HWPX schema version")]
    UnsupportedVersion,
    #[error("table transpose HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table transpose HWPX JSON")]
    InvalidJson,
    #[error("invalid table transpose HWPX binding")]
    InvalidBinding,
    #[error("table transpose HWPX source parts, state, grid or flow drifted")]
    SourceBindingMismatch,
    #[error("table transpose HWPX document-flow transition drifted")]
    FlowBindingMismatch,
    #[error("table transpose HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("selected table has formulas or repeat headers without an exact transpose mapping")]
    UnsupportedSourceProfile,
    #[error("table transpose HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table transpose HWPX serialization failed")]
    Serialization,
    #[error("table transpose HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Transpose(#[from] TableTransposeError),
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    ModelRuling(#[from] TableRulingError),
    #[error(transparent)]
    Ruling(#[from] TableRulingHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
}

impl TableTransposeHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_transpose_hwpx_unsupported_version",
            Self::InputLimit => "table_transpose_hwpx_input_limit",
            Self::InvalidJson => "table_transpose_hwpx_invalid_json",
            Self::InvalidBinding => "table_transpose_hwpx_invalid_binding",
            Self::SourceBindingMismatch => "table_transpose_hwpx_source_binding_mismatch",
            Self::FlowBindingMismatch => "table_transpose_hwpx_flow_binding_mismatch",
            Self::PlanBindingMismatch => "table_transpose_hwpx_plan_binding_mismatch",
            Self::UnsupportedSourceProfile => "table_transpose_hwpx_unsupported_source_profile",
            Self::ReadbackMismatch => "table_transpose_hwpx_readback_mismatch",
            Self::Serialization => "table_transpose_hwpx_serialization",
            Self::OutputLimit => "table_transpose_hwpx_output_limit",
            Self::Transpose(_) => "table_transpose_hwpx_domain",
            Self::Grid(_) => "table_transpose_hwpx_grid",
            Self::ModelRuling(_) => "table_transpose_hwpx_model_ruling",
            Self::Ruling(_) => "table_transpose_hwpx_ruling",
            Self::Pagination(_) => "table_transpose_hwpx_pagination",
        }
    }
}

fn validate_request_source(
    request: &TableTransposeHwpxRequest,
    source: &TableTransposeHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableTransposeHwpxLimits,
) -> Result<(), TableTransposeHwpxError> {
    require_digest(current_document_flow_sha256)?;
    require_source_profile(&source.ruling, &source.pagination)?;
    if request.table_ordinal != source.table_ordinal
        || request.expected_header_sha256 != hex(source.ruling.header_sha256)
        || request.expected_section_sha256 != hex(source.ruling.section_sha256)
        || request.expected_source_state_sha256
            != hex(source.ruling.state.canonical_sha256(limits.ruling.ruling)?)
        || request.expected_source_grid_sha256 != hex(source.ruling.grid.canonical_sha256()?)
        || request.expected_document_flow_sha256 != current_document_flow_sha256
        || request.transpose.table_id() != source.ruling.state.table_id()
        || request.transpose.grid_sha256() != request.expected_source_grid_sha256
        || request.transpose.table_properties_sha256()
            != source.ruling.state.table_properties_sha256()
        || request.transpose.formula_policy() != TableTransposeFormulaPolicy::Reject
        || request.transpose.cells().len() != source.ruling.state.cells().len()
    {
        return Err(TableTransposeHwpxError::SourceBindingMismatch);
    }
    for (request_cell, source_cell) in request
        .transpose
        .cells()
        .iter()
        .zip(source.ruling.state.cells())
    {
        if request_cell.master_cell_id() != source_cell.master_cell_id()
            || request_cell.coordinate() != source_cell.coordinate()
            || request_cell.payload_sha256()
                != component_digest(source_cell.payload(), serialized_limit(limits))?
            || request_cell.style_sha256()
                != component_digest(source_cell.properties(), serialized_limit(limits))?
            || request_cell.formula().is_some()
            || source_cell.formula().is_some()
        {
            return Err(TableTransposeHwpxError::SourceBindingMismatch);
        }
    }
    Ok(())
}

fn require_source_profile(
    ruling: &TableRulingHwpxReadback,
    pagination: &TablePaginationHwpxReadback,
) -> Result<(), TableTransposeHwpxError> {
    if ruling.formula_count != 0
        || ruling
            .state
            .cells()
            .iter()
            .any(|cell| cell.formula().is_some())
        || pagination.repeat_header_rows != 0
    {
        return Err(TableTransposeHwpxError::UnsupportedSourceProfile);
    }
    Ok(())
}

fn transposed_state(
    source: &TableTransposeHwpxReadback,
    domain: &TableTransposePlan,
    target_grid: &TableGrid,
    limits: &TableTransposeHwpxLimits,
) -> Result<TableRulingState, TableTransposeHwpxError> {
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(domain.relocations().len())
        .map_err(|_| TableTransposeHwpxError::OutputLimit)?;
    for relocation in domain.relocations() {
        let source_cell = source
            .ruling
            .state
            .cell(&relocation.master_cell_id)
            .ok_or(TableTransposeHwpxError::PlanBindingMismatch)?;
        if source_cell.coordinate() != relocation.before
            || source_cell.formula().is_some()
            || relocation.formula.is_some()
            || relocation.payload_sha256
                != component_digest(source_cell.payload(), serialized_limit(limits))?
            || relocation.style_sha256
                != component_digest(source_cell.properties(), serialized_limit(limits))?
        {
            return Err(TableTransposeHwpxError::PlanBindingMismatch);
        }
        cells.push(TableRulingCellDraft {
            master_cell_id: relocation.master_cell_id.clone(),
            coordinate: relocation.after,
            payload: source_cell.payload().to_vec(),
            properties: source_cell.properties().clone(),
            formula: None,
        });
    }
    let frame = source.ruling.state.frame();
    let state = TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: source.ruling.state.table_id().clone(),
            frame: TableRulingFrame {
                left_hwpunit: frame.left_hwpunit,
                top_hwpunit: frame.top_hwpunit,
                width_hwpunit: frame.height_hwpunit,
                height_hwpunit: frame.width_hwpunit,
            },
            grid_sha256: hex(target_grid.canonical_sha256()?),
            table_properties_sha256: source.ruling.state.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: source.ruling.state.column_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: source.ruling.state.row_boundaries_hwpunit().to_vec(),
            edges: transposed_edges(source.ruling.state.edges())?,
            cells,
        },
        target_grid,
        limits.ruling.formula,
        limits.ruling.ruling,
    )?;
    Ok(state)
}

fn transposed_edges(
    edges: &[TableRulingEdge],
) -> Result<Vec<TableRulingEdge>, TableTransposeHwpxError> {
    let mut output = Vec::new();
    output
        .try_reserve_exact(edges.len())
        .map_err(|_| TableTransposeHwpxError::OutputLimit)?;
    for edge in edges {
        output.push(TableRulingEdge {
            axis: match edge.axis {
                TableRulingAxis::Horizontal => TableRulingAxis::Vertical,
                TableRulingAxis::Vertical => TableRulingAxis::Horizontal,
            },
            boundary: edge.boundary,
            offset: edge.offset,
            line_sha256: edge.line_sha256.clone(),
        });
    }
    Ok(output)
}

fn merged_cell_count(grid: &TableGrid) -> usize {
    grid.master_cells()
        .iter()
        .filter(|cell| cell.row_span != 1 || cell.column_span != 1)
        .count()
}

fn pagination_digest(value: &TablePaginationHwpxReadback) -> String {
    pagination_semantic_digest(
        value,
        value.row_count,
        value.column_count,
        b"hwpx-agent.table-transpose-hwpx-pagination-source/v1\0",
    )
}

fn transposed_pagination_digest(value: &TablePaginationHwpxReadback) -> String {
    pagination_semantic_digest(
        value,
        value.column_count,
        value.row_count,
        b"hwpx-agent.table-transpose-hwpx-pagination-target/v1\0",
    )
}

fn pagination_semantic_digest(
    value: &TablePaginationHwpxReadback,
    rows: u32,
    columns: u32,
    domain: &[u8],
) -> String {
    let mut digest = Sha256::new();
    digest.update(domain);
    digest.update(match value.page_split {
        domain_ir::TablePageSplitPolicy::Allow => b"allow".as_slice(),
        domain_ir::TablePageSplitPolicy::AvoidRow => b"avoid-row".as_slice(),
        domain_ir::TablePageSplitPolicy::AvoidTable => b"avoid-table".as_slice(),
        domain_ir::TablePageSplitPolicy::RequiredKeep => b"required-keep".as_slice(),
    });
    digest.update(0_u32.to_le_bytes());
    digest.update(rows.to_le_bytes());
    digest.update(columns.to_le_bytes());
    if let Some(caption) = &value.caption {
        digest.update(b"caption\0");
        digest.update(match caption.side {
            domain_ir::CaptionSide::Top => b"top".as_slice(),
            domain_ir::CaptionSide::Bottom => b"bottom".as_slice(),
        });
        digest.update([u8::from(caption.full_size)]);
        digest.update(caption.width_hwpunit.to_le_bytes());
        digest.update(caption.gap_hwpunit.to_le_bytes());
        digest.update(caption.last_width_hwpunit.to_le_bytes());
        digest.update(caption.content_sha256);
    } else {
        digest.update(b"no-caption\0");
    }
    hex(digest.finalize())
}

fn component_digest<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<String, TableTransposeHwpxError> {
    Ok(hex(Sha256::digest(serialize_bounded(value, maximum)?)))
}

fn serialized_limit(limits: &TableTransposeHwpxLimits) -> usize {
    limits
        .transpose
        .config()
        .serialized_bytes
        .min(limits.ruling.ruling.config().serialized_bytes)
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableTransposeHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableTransposeHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableTransposeHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TableTransposeHwpxError> {
    struct Seed;
    struct Visitor;

    impl<'de> serde::de::DeserializeSeed<'de> for Seed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(Visitor)
        }
    }

    impl<'de> serde::de::Visitor<'de> for Visitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }

        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
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
    serde::de::DeserializeSeed::deserialize(Seed, &mut deserializer)
        .map_err(|_| TableTransposeHwpxError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| TableTransposeHwpxError::InvalidJson)
}

fn require_digest(value: &str) -> Result<(), TableTransposeHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableTransposeHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableTransposeHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text =
            std::str::from_utf8(chunk).map_err(|_| TableTransposeHwpxError::InvalidBinding)?;
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableTransposeHwpxError::InvalidBinding)?;
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
