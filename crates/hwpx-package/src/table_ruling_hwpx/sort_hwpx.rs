use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use domain_ir::{
    CaptionSide, CellCoordinate, TABLE_RULING_SCHEMA_VERSION, TABLE_SORT_SCHEMA_VERSION,
    TABLE_TEXT_CONVERSION_SCHEMA_VERSION, TableCellSpan, TableFormulaMovePolicy, TableGrid,
    TableGridError, TablePageSplitPolicy, TableRulingCellDraft, TableRulingError, TableRulingState,
    TableRulingStateDraft, TableSortAxis, TableSortBuilder, TableSortError, TableSortKey,
    TableSortLimits, TableSortPlan, TableSortRegion, TableSortRequest, TableSortRequestDraft,
    TableSortValue, TableTextConversionError, TableTextConversionLimits, TableTextGrid,
    TableTextGridDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::create_hwpx::{self, TableCreateHwpxLimits};
use super::text_conversion_hwpx::{
    TableTextToTableHwpxError, TableTextToTableHwpxLimits, read_unmerged_text_grid,
};
use super::{
    TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits, TableRulingHwpxReadback,
    TableRulingHwpxReader,
};
use crate::{
    TablePaginationHwpxError, TablePaginationHwpxLimits, TablePaginationHwpxReadback,
    TablePaginationHwpxReader, TextFlowLimits,
};

pub const TABLE_SORT_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-sort-hwpx/v1";
pub const TABLE_SORT_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-sort-hwpx.hancom-2020-plain-unmerged/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableSortHwpxLimits {
    pub native: TableRulingHwpxLimits,
    pub pagination: TablePaginationHwpxLimits,
    pub text: TableTextConversionLimits,
    pub flow: TextFlowLimits,
    pub sort: TableSortLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableSortHwpxReadback {
    pub profile_id: &'static str,
    pub table_ordinal: usize,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub source_table_count: usize,
    pub ruling: TableRulingHwpxReadback,
    pub pagination: TablePaginationHwpxReadback,
    pub text_grid: TableTextGrid,
    pub text_grid_sha256: [u8; 32],
    pub pagination_policy_sha256: [u8; 32],
}

impl fmt::Debug for TableSortHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("source_table_count", &self.source_table_count)
            .field("rows", &self.ruling.grid.rows())
            .field("columns", &self.ruling.grid.columns())
            .field("payload_block_count", &self.ruling.payload_block_count)
            .field("formula_count", &self.ruling.formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableSortHwpxReader;

impl TableSortHwpxReader {
    /// Lifts a complete plain, unmerged current-profile table for deterministic semantic sorting.
    ///
    /// # Errors
    ///
    /// Rejects malformed, merged, formula-bearing, non-plain, multi-paragraph, opaque, ambiguous,
    /// or over-limit input.
    pub fn read_context(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: TableSortHwpxLimits,
    ) -> Result<TableSortHwpxReadback, TableSortHwpxError> {
        let ruling = TableRulingHwpxReader::read_existing_preserving_caption(
            header,
            section,
            table_ordinal,
            binding,
            &limits.native,
        )?;
        if ruling.formula_count != 0
            || ruling
                .state
                .cells()
                .iter()
                .any(|cell| cell.formula().is_some())
        {
            return Err(TableSortHwpxError::UnsupportedFormula);
        }
        require_unmerged(&ruling.grid)?;
        let pagination =
            TablePaginationHwpxReader::read_in_section(section, table_ordinal, limits.pagination)?;
        let text_grid = read_unmerged_text_grid(
            section,
            table_ordinal,
            &ruling.grid,
            &text_adapter_limits(&limits),
        )?;
        let source_table_count =
            TablePaginationHwpxReader::count_in_section(section, limits.pagination)?;
        Ok(TableSortHwpxReadback {
            profile_id: TABLE_SORT_HWPX_PROFILE_ID,
            table_ordinal,
            header_sha256: Sha256::digest(header).into(),
            section_sha256: Sha256::digest(section).into(),
            source_table_count,
            text_grid_sha256: text_grid.canonical_sha256(limits.text)?,
            pagination_policy_sha256: pagination_policy_sha256(&pagination),
            ruling,
            pagination,
            text_grid,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableSortHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub region: TableSortRegion,
    pub axis: TableSortAxis,
    pub keys: Vec<TableSortKey>,
    pub formula_move_policy: TableFormulaMovePolicy,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_table_content_sha256: String,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_text_grid_sha256: String,
    pub expected_pagination_policy_sha256: String,
    pub expected_source_table_count: usize,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
}

impl fmt::Debug for TableSortHwpxRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field("region", &self.region)
            .field("axis", &self.axis)
            .field("key_count", &self.keys.len())
            .field("formula_move_policy", &self.formula_move_policy)
            .field(
                "expected_source_table_count",
                &self.expected_source_table_count,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableSortHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_ordinal: usize,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_table_content_sha256: String,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_text_grid_sha256: String,
    expected_pagination_policy_sha256: String,
    expected_source_table_count: usize,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    semantic: TableSortRequest,
}

impl TableSortHwpxRequest {
    /// Binds one exact source table and a source-derived typed sort request to document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, source, state, grid, payload, sort-value, formula-policy, flow, or bound
    /// drift.
    pub fn from_draft(
        draft: TableSortHwpxRequestDraft,
        source: &TableSortHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableSortHwpxLimits,
    ) -> Result<Self, TableSortHwpxError> {
        if draft.schema_version != TABLE_SORT_HWPX_SCHEMA_VERSION {
            return Err(TableSortHwpxError::UnsupportedVersion);
        }
        require_request_digests(&draft, current_document_flow_sha256)?;
        if draft.formula_move_policy != TableFormulaMovePolicy::Reject {
            return Err(TableSortHwpxError::UnsupportedFormulaPolicy);
        }
        let semantic = semantic_request(
            source,
            draft.region,
            draft.axis,
            draft.keys,
            draft.formula_move_policy,
            &limits,
        )?;
        let request = Self {
            schema_version: TABLE_SORT_HWPX_SCHEMA_VERSION,
            capability_id: semantic.capability_id(),
            table_ordinal: draft.table_ordinal,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_table_content_sha256: draft.expected_table_content_sha256,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_source_grid_sha256: draft.expected_source_grid_sha256,
            expected_text_grid_sha256: draft.expected_text_grid_sha256,
            expected_pagination_policy_sha256: draft.expected_pagination_policy_sha256,
            expected_source_table_count: draft.expected_source_table_count,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            semantic,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ =
            TableSortHwpxBuilder::build(&request, source, current_document_flow_sha256, limits)?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies the same source-derived admission as `from_draft`.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown, or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &TableSortHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableSortHwpxLimits,
    ) -> Result<Self, TableSortHwpxError> {
        if bytes.is_empty() || bytes.len() > serialized_limit(&limits) {
            return Err(TableSortHwpxError::InputLimit);
        }
        create_hwpx::reject_duplicate_json_keys(bytes)
            .map_err(|_| TableSortHwpxError::InvalidJson)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableSortHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn semantic(&self) -> &TableSortRequest {
        &self.semantic
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes the complete typed request under the configured finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableSortHwpxLimits,
    ) -> Result<Vec<u8>, TableSortHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded deterministic request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableSortHwpxLimits,
    ) -> Result<[u8; 32], TableSortHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableSortHwpxRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("region", &self.semantic.region())
            .field("axis", &self.semantic.axis())
            .field("key_count", &self.semantic.keys().len())
            .field(
                "expected_source_table_count",
                &self.expected_source_table_count,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableSortHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    source_state_sha256: String,
    target_state_sha256: String,
    source_grid_sha256: String,
    target_grid_sha256: String,
    source_text_grid_sha256: String,
    target_text_grid_sha256: String,
    pagination_policy_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    source_table_count: usize,
    sort: TableSortPlan,
    target_state: TableRulingState,
    #[serde(skip)]
    target_grid: TableGrid,
    #[serde(skip)]
    target_text_grid: TableTextGrid,
}

impl TableSortHwpxPlan {
    #[must_use]
    pub const fn sort_plan(&self) -> &TableSortPlan {
        &self.sort
    }

    #[must_use]
    pub const fn target_state(&self) -> &TableRulingState {
        &self.target_state
    }

    #[must_use]
    pub const fn target_grid(&self) -> &TableGrid {
        &self.target_grid
    }

    #[must_use]
    pub const fn target_text_grid(&self) -> &TableTextGrid {
        &self.target_text_grid
    }

    /// Serializes all lowering semantics and integrity bindings under finite limits.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableSortHwpxLimits,
    ) -> Result<Vec<u8>, TableSortHwpxError> {
        serialize_bounded(self, serialized_limit(&limits))
    }

    /// Hashes the bounded deterministic plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableSortHwpxLimits,
    ) -> Result<[u8; 32], TableSortHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableSortHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("source_table_count", &self.source_table_count)
            .field("rows", &self.target_grid.rows())
            .field("columns", &self.target_grid.columns())
            .field("relocation_count", &self.sort.relocations().len())
            .field("changed", &self.sort.receipt().changed())
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableSortHwpxBuilder;

impl TableSortHwpxBuilder {
    /// Revalidates the source and builds an exact target grid/state relocation plan.
    ///
    /// # Errors
    ///
    /// Rejects source, request, sort, identity, state, grid, flow, or finite-limit drift.
    pub fn build(
        request: &TableSortHwpxRequest,
        source: &TableSortHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableSortHwpxLimits,
    ) -> Result<TableSortHwpxPlan, TableSortHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        let sort = TableSortBuilder::build(request.semantic.clone(), limits.sort)?;
        let semantic_noop = !sort.receipt().changed();
        if semantic_noop
            != (request.expected_document_flow_sha256 == request.target_document_flow_sha256)
        {
            return Err(TableSortHwpxError::FlowBindingMismatch);
        }
        let (target_grid, target_state) = target_state(source, &sort, &limits)?;
        let target_text_grid = target_text_grid(source, &sort, &limits)?;
        let plan = TableSortHwpxPlan {
            schema_version: TABLE_SORT_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: create_hwpx::hex(request.canonical_sha256(limits)?),
            source_state_sha256: create_hwpx::hex(
                source.ruling.state.canonical_sha256(limits.native.ruling)?,
            ),
            target_state_sha256: create_hwpx::hex(
                target_state.canonical_sha256(limits.native.ruling)?,
            ),
            source_grid_sha256: create_hwpx::hex(source.ruling.grid.canonical_sha256()?),
            target_grid_sha256: create_hwpx::hex(target_grid.canonical_sha256()?),
            source_text_grid_sha256: create_hwpx::hex(source.text_grid_sha256),
            target_text_grid_sha256: create_hwpx::hex(
                target_text_grid.canonical_sha256(limits.text)?,
            ),
            pagination_policy_sha256: create_hwpx::hex(source.pagination_policy_sha256),
            expected_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            source_table_count: source.source_table_count,
            sort,
            target_state,
            target_grid,
            target_text_grid,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableSortHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub source_grid_sha256: [u8; 32],
    pub target_grid_sha256: [u8; 32],
    pub source_text_grid_sha256: [u8; 32],
    pub target_text_grid_sha256: [u8; 32],
    pub pagination_policy_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub rows: u32,
    pub columns: u32,
    pub relocation_count: usize,
    pub changed: bool,
    pub payload_block_count: usize,
    pub formula_count: usize,
    pub added_border_fill_count: usize,
    pub page_split: TablePageSplitPolicy,
    pub repeat_header_rows: u32,
    pub caption_preserved: bool,
}

impl fmt::Debug for TableSortHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("relocation_count", &self.relocation_count)
            .field("changed", &self.changed)
            .field("payload_block_count", &self.payload_block_count)
            .field("formula_count", &self.formula_count)
            .field("added_border_fill_count", &self.added_border_fill_count)
            .field("page_split", &self.page_split)
            .field("repeat_header_rows", &self.repeat_header_rows)
            .field("caption_preserved", &self.caption_preserved)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableSortHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub receipt: TableSortHwpxLoweringReceipt,
}

impl fmt::Debug for TableSortHwpxLoweredParts {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableSortHwpxLowerer;

impl TableSortHwpxLowerer {
    /// Relocates complete source cells and returns only after exact state, text and pagination
    /// reopen.
    ///
    /// # Errors
    ///
    /// Rejects source, state, grid, payload, sort, flow, plan, pagination, or readback drift without
    /// returning partial parts.
    #[allow(clippy::too_many_arguments)]
    pub fn lower(
        header: &[u8],
        section: &[u8],
        binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableSortHwpxRequest,
        plan: &TableSortHwpxPlan,
        limits: TableSortHwpxLimits,
    ) -> Result<TableSortHwpxLoweredParts, TableSortHwpxError> {
        let source = TableSortHwpxReader::read_context(
            header,
            section,
            request.table_ordinal,
            binding,
            limits,
        )?;
        validate_request_source(request, &source, current_document_flow_sha256, &limits)?;
        let rebuilt =
            TableSortHwpxBuilder::build(request, &source, current_document_flow_sha256, limits)?;
        if rebuilt != *plan {
            return Err(TableSortHwpxError::PlanBindingMismatch);
        }
        let target_binding = super::binding_from_state(&plan.target_state, &plan.target_grid)?;
        let (output_header, output_section, added_border_fill_count) =
            if plan.sort.receipt().changed() {
                let rendered = super::render_structure_existing(
                    header,
                    section,
                    request.table_ordinal,
                    binding,
                    &source.ruling.state,
                    &plan.target_state,
                    &plan.target_grid,
                    &limits.native,
                )?;
                (
                    rendered.header,
                    rendered.section,
                    rendered.added_border_fill_count,
                )
            } else {
                (header.to_vec(), section.to_vec(), 0)
            };
        let reopened = TableSortHwpxReader::read_context(
            &output_header,
            &output_section,
            request.table_ordinal,
            &target_binding,
            limits,
        )?;
        if reopened.ruling.state != plan.target_state
            || reopened.ruling.grid != plan.target_grid
            || reopened.text_grid != plan.target_text_grid
            || create_hwpx::hex(reopened.text_grid_sha256) != plan.target_text_grid_sha256
            || !same_pagination_policy(&source.pagination, &reopened.pagination)
            || reopened.source_table_count != source.source_table_count
        {
            return Err(TableSortHwpxError::ReadbackMismatch);
        }
        let receipt = TableSortHwpxLoweringReceipt {
            profile_id: TABLE_SORT_HWPX_PROFILE_ID,
            source_header_sha256: source.header_sha256,
            output_header_sha256: Sha256::digest(&output_header).into(),
            source_section_sha256: source.section_sha256,
            output_section_sha256: Sha256::digest(&output_section).into(),
            source_state_sha256: source.ruling.state.canonical_sha256(limits.native.ruling)?,
            target_state_sha256: plan.target_state.canonical_sha256(limits.native.ruling)?,
            source_grid_sha256: source.ruling.grid.canonical_sha256()?,
            target_grid_sha256: plan.target_grid.canonical_sha256()?,
            source_text_grid_sha256: source.text_grid_sha256,
            target_text_grid_sha256: reopened.text_grid_sha256,
            pagination_policy_sha256: source.pagination_policy_sha256,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(&request.expected_document_flow_sha256)?,
            after_document_flow_sha256: parse_digest(&request.target_document_flow_sha256)?,
            source_table_count: source.source_table_count,
            target_table_count: reopened.source_table_count,
            rows: plan.target_grid.rows(),
            columns: plan.target_grid.columns(),
            relocation_count: plan.sort.relocations().len(),
            changed: plan.sort.receipt().changed(),
            payload_block_count: reopened.ruling.payload_block_count,
            formula_count: reopened.ruling.formula_count,
            added_border_fill_count,
            page_split: reopened.pagination.page_split,
            repeat_header_rows: reopened.pagination.repeat_header_rows,
            caption_preserved: reopened.pagination.caption.is_some(),
        };
        Ok(TableSortHwpxLoweredParts {
            header: output_header,
            section: output_section,
            binding: target_binding,
            receipt,
        })
    }
}

#[derive(Debug, Error)]
pub enum TableSortHwpxError {
    #[error("unsupported table-sort HWPX schema version")]
    UnsupportedVersion,
    #[error("table-sort HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table-sort HWPX JSON")]
    InvalidJson,
    #[error("table-sort HWPX source, state, grid, payload, or flow drifted")]
    SourceBindingMismatch,
    #[error("table-sort HWPX document-flow transition drifted")]
    FlowBindingMismatch,
    #[error("table-sort HWPX current profile requires a completely unmerged grid")]
    UnsupportedMergedCells,
    #[error("table-sort HWPX current profile does not move formulas")]
    UnsupportedFormula,
    #[error("table-sort HWPX current profile requires the reject formula policy")]
    UnsupportedFormulaPolicy,
    #[error("table-sort HWPX cell text cannot be classified safely")]
    UnsupportedSortValue,
    #[error("table-sort HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("table-sort HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table-sort HWPX allocation failed")]
    Allocation,
    #[error("table-sort HWPX serialization failed")]
    Serialization,
    #[error("table-sort HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    RulingModel(#[from] TableRulingError),
    #[error(transparent)]
    Sort(#[from] TableSortError),
    #[error(transparent)]
    TextModel(#[from] TableTextConversionError),
    #[error(transparent)]
    Native(#[from] TableRulingHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
    #[error(transparent)]
    TextAdapter(#[from] TableTextToTableHwpxError),
}

impl TableSortHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_sort_hwpx_unsupported_version",
            Self::InputLimit => "table_sort_hwpx_input_limit",
            Self::InvalidJson => "table_sort_hwpx_invalid_json",
            Self::SourceBindingMismatch => "table_sort_hwpx_source_binding_mismatch",
            Self::FlowBindingMismatch => "table_sort_hwpx_flow_binding_mismatch",
            Self::UnsupportedMergedCells => "table_sort_hwpx_unsupported_merged_cells",
            Self::UnsupportedFormula => "table_sort_hwpx_unsupported_formula",
            Self::UnsupportedFormulaPolicy => "table_sort_hwpx_unsupported_formula_policy",
            Self::UnsupportedSortValue => "table_sort_hwpx_unsupported_sort_value",
            Self::PlanBindingMismatch => "table_sort_hwpx_plan_binding_mismatch",
            Self::ReadbackMismatch => "table_sort_hwpx_readback_mismatch",
            Self::Allocation => "table_sort_hwpx_allocation",
            Self::Serialization => "table_sort_hwpx_serialization",
            Self::OutputLimit => "table_sort_hwpx_output_limit",
            Self::Grid(_) => "table_sort_hwpx_grid",
            Self::RulingModel(_) => "table_sort_hwpx_ruling_model",
            Self::Sort(_) => "table_sort_hwpx_sort",
            Self::TextModel(_) => "table_sort_hwpx_text_model",
            Self::Native(_) => "table_sort_hwpx_native",
            Self::Pagination(_) => "table_sort_hwpx_pagination",
            Self::TextAdapter(_) => "table_sort_hwpx_text_adapter",
        }
    }
}

fn require_request_digests(
    draft: &TableSortHwpxRequestDraft,
    current_document_flow_sha256: &str,
) -> Result<(), TableSortHwpxError> {
    for digest in [
        &draft.expected_header_sha256,
        &draft.expected_section_sha256,
        &draft.expected_table_content_sha256,
        &draft.expected_source_state_sha256,
        &draft.expected_source_grid_sha256,
        &draft.expected_text_grid_sha256,
        &draft.expected_pagination_policy_sha256,
        &draft.expected_document_flow_sha256,
        &draft.target_document_flow_sha256,
        current_document_flow_sha256,
    ] {
        create_hwpx::require_digest(digest)
            .map_err(|_| TableSortHwpxError::SourceBindingMismatch)?;
    }
    Ok(())
}

fn validate_request_source(
    request: &TableSortHwpxRequest,
    source: &TableSortHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableSortHwpxLimits,
) -> Result<(), TableSortHwpxError> {
    create_hwpx::require_digest(current_document_flow_sha256)
        .map_err(|_| TableSortHwpxError::SourceBindingMismatch)?;
    require_unmerged(&source.ruling.grid)?;
    if source.ruling.formula_count != 0
        || source
            .ruling
            .state
            .cells()
            .iter()
            .any(|cell| cell.formula().is_some())
    {
        return Err(TableSortHwpxError::UnsupportedFormula);
    }
    let rebuilt_semantic = semantic_request(
        source,
        request.semantic.region(),
        request.semantic.axis(),
        request.semantic.keys().to_vec(),
        request.semantic.formula_move_policy(),
        limits,
    )?;
    if source.profile_id != TABLE_SORT_HWPX_PROFILE_ID
        || source.ruling.profile_id != super::TABLE_RULING_HWPX_PROFILE_ID
        || request.table_ordinal != source.table_ordinal
        || request.expected_header_sha256 != create_hwpx::hex(source.header_sha256)
        || request.expected_section_sha256 != create_hwpx::hex(source.section_sha256)
        || request.expected_table_content_sha256
            != create_hwpx::hex(source.ruling.table_content_sha256)
        || request.expected_source_state_sha256
            != create_hwpx::hex(source.ruling.state.canonical_sha256(limits.native.ruling)?)
        || request.expected_source_grid_sha256
            != create_hwpx::hex(source.ruling.grid.canonical_sha256()?)
        || request.expected_text_grid_sha256 != create_hwpx::hex(source.text_grid_sha256)
        || request.expected_pagination_policy_sha256
            != create_hwpx::hex(source.pagination_policy_sha256)
        || request.expected_source_table_count != source.source_table_count
        || request.expected_document_flow_sha256 != current_document_flow_sha256
        || request.semantic != rebuilt_semantic
    {
        return Err(TableSortHwpxError::SourceBindingMismatch);
    }
    if request.semantic.formula_move_policy() != TableFormulaMovePolicy::Reject {
        return Err(TableSortHwpxError::UnsupportedFormulaPolicy);
    }
    Ok(())
}

fn semantic_request(
    source: &TableSortHwpxReadback,
    region: TableSortRegion,
    axis: TableSortAxis,
    keys: Vec<TableSortKey>,
    formula_move_policy: TableFormulaMovePolicy,
    limits: &TableSortHwpxLimits,
) -> Result<TableSortRequest, TableSortHwpxError> {
    if region.start.row > region.end.row || region.start.column > region.end.column {
        return Err(TableSortError::RegionOrder.into());
    }
    if region.end.row >= source.ruling.grid.rows()
        || region.end.column >= source.ruling.grid.columns()
    {
        return Err(TableSortError::RegionOutOfBounds.into());
    }
    let row_count = region
        .end
        .row
        .checked_sub(region.start.row)
        .and_then(|value| value.checked_add(1))
        .ok_or(TableSortHwpxError::SourceBindingMismatch)?;
    let column_count = region
        .end
        .column
        .checked_sub(region.start.column)
        .and_then(|value| value.checked_add(1))
        .ok_or(TableSortHwpxError::SourceBindingMismatch)?;
    let capacity = usize::try_from(row_count)
        .ok()
        .and_then(|rows| {
            usize::try_from(column_count)
                .ok()
                .and_then(|columns| rows.checked_mul(columns))
        })
        .ok_or(TableSortHwpxError::Allocation)?;
    if capacity > limits.sort.config().selected_cells {
        return Err(TableSortError::SelectionLimit.into());
    }
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(capacity)
        .map_err(|_| TableSortHwpxError::Allocation)?;
    for row in region.start.row..=region.end.row {
        for column in region.start.column..=region.end.column {
            let coordinate = CellCoordinate { row, column };
            let span = source.ruling.grid.master_cell_at(coordinate)?;
            if span.row != row
                || span.column != column
                || span.row_span != 1
                || span.column_span != 1
            {
                return Err(TableSortHwpxError::UnsupportedMergedCells);
            }
            let state_cell = source
                .ruling
                .state
                .cell(&span.master_cell_id)
                .ok_or(TableSortHwpxError::SourceBindingMismatch)?;
            let text = source
                .text_grid
                .cell(
                    usize::try_from(row).map_err(|_| TableSortHwpxError::SourceBindingMismatch)?,
                    usize::try_from(column)
                        .map_err(|_| TableSortHwpxError::SourceBindingMismatch)?,
                )
                .ok_or(TableSortHwpxError::SourceBindingMismatch)?;
            cells.push(domain_ir::TableSortCellDraft {
                coordinate,
                payload_sha256: aggregate_payload_digest(state_cell.payload())?,
                formula_sha256: None,
                sort_value: classify_sort_value(text)?,
            });
        }
    }
    Ok(TableSortRequest::from_draft(
        TableSortRequestDraft {
            schema_version: TABLE_SORT_SCHEMA_VERSION.to_owned(),
            table_id: source.ruling.state.table_id().clone(),
            region,
            axis,
            keys,
            formula_move_policy,
            cells,
        },
        &source.ruling.grid,
        limits.sort,
    )?)
}

fn target_state(
    source: &TableSortHwpxReadback,
    sort: &TableSortPlan,
    limits: &TableSortHwpxLimits,
) -> Result<(TableGrid, TableRulingState), TableSortHwpxError> {
    let mut source_by_destination = BTreeMap::new();
    let mut seen_sources = BTreeSet::new();
    for relocation in sort.relocations() {
        if source_by_destination
            .insert(relocation.destination(), relocation.source())
            .is_some()
            || !seen_sources.insert(relocation.source())
        {
            return Err(TableSortHwpxError::PlanBindingMismatch);
        }
        let source_span = source.ruling.grid.master_cell_at(relocation.source())?;
        let source_cell = source
            .ruling
            .state
            .cell(&source_span.master_cell_id)
            .ok_or(TableSortHwpxError::PlanBindingMismatch)?;
        if source_cell.formula().is_some() {
            return Err(TableSortHwpxError::UnsupportedFormula);
        }
        if relocation.payload_sha256() != aggregate_payload_digest(source_cell.payload())?
            || relocation.formula_sha256().is_some()
        {
            return Err(TableSortHwpxError::PlanBindingMismatch);
        }
    }
    let mut spans = Vec::new();
    spans
        .try_reserve_exact(source.ruling.grid.master_cell_count())
        .map_err(|_| TableSortHwpxError::Allocation)?;
    for destination in source.ruling.grid.master_cells() {
        let destination_coordinate = CellCoordinate {
            row: destination.row,
            column: destination.column,
        };
        let source_coordinate = source_by_destination
            .get(&destination_coordinate)
            .copied()
            .unwrap_or(destination_coordinate);
        let source_span = source.ruling.grid.master_cell_at(source_coordinate)?;
        spans.push(TableCellSpan {
            master_cell_id: source_span.master_cell_id.clone(),
            row: destination.row,
            column: destination.column,
            row_span: 1,
            column_span: 1,
        });
    }
    let target_grid = TableGrid::new(
        source.ruling.grid.rows(),
        source.ruling.grid.columns(),
        spans,
        limits.native.grid,
    )?;
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(target_grid.master_cell_count())
        .map_err(|_| TableSortHwpxError::Allocation)?;
    for span in target_grid.master_cells() {
        let source_cell = source
            .ruling
            .state
            .cell(&span.master_cell_id)
            .ok_or(TableSortHwpxError::PlanBindingMismatch)?;
        cells.push(TableRulingCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate: CellCoordinate {
                row: span.row,
                column: span.column,
            },
            payload: source_cell.payload().to_vec(),
            properties: source_cell.properties().clone(),
            formula: None,
        });
    }
    let target_grid_sha256 = create_hwpx::hex(target_grid.canonical_sha256()?);
    let target_state = TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: source.ruling.state.table_id().clone(),
            frame: source.ruling.state.frame(),
            grid_sha256: target_grid_sha256,
            table_properties_sha256: source.ruling.state.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: source.ruling.state.row_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: source.ruling.state.column_boundaries_hwpunit().to_vec(),
            edges: source.ruling.state.edges().to_vec(),
            cells,
        },
        &target_grid,
        limits.native.formula,
        limits.native.ruling,
    )?;
    Ok((target_grid, target_state))
}

fn target_text_grid(
    source: &TableSortHwpxReadback,
    sort: &TableSortPlan,
    limits: &TableSortHwpxLimits,
) -> Result<TableTextGrid, TableSortHwpxError> {
    let mut source_by_destination = BTreeMap::new();
    for relocation in sort.relocations() {
        if source_by_destination
            .insert(relocation.destination(), relocation.source())
            .is_some()
        {
            return Err(TableSortHwpxError::PlanBindingMismatch);
        }
    }
    let row_capacity =
        usize::try_from(source.ruling.grid.rows()).map_err(|_| TableSortHwpxError::Allocation)?;
    let column_capacity = usize::try_from(source.ruling.grid.columns())
        .map_err(|_| TableSortHwpxError::Allocation)?;
    let mut rows = Vec::new();
    rows.try_reserve_exact(row_capacity)
        .map_err(|_| TableSortHwpxError::Allocation)?;
    for row in 0..source.ruling.grid.rows() {
        let mut cells = Vec::new();
        cells
            .try_reserve_exact(column_capacity)
            .map_err(|_| TableSortHwpxError::Allocation)?;
        for column in 0..source.ruling.grid.columns() {
            let destination = CellCoordinate { row, column };
            let source_coordinate = source_by_destination
                .get(&destination)
                .copied()
                .unwrap_or(destination);
            let source_row = usize::try_from(source_coordinate.row)
                .map_err(|_| TableSortHwpxError::PlanBindingMismatch)?;
            let source_column = usize::try_from(source_coordinate.column)
                .map_err(|_| TableSortHwpxError::PlanBindingMismatch)?;
            cells.push(
                source
                    .text_grid
                    .cell(source_row, source_column)
                    .ok_or(TableSortHwpxError::PlanBindingMismatch)?
                    .to_owned(),
            );
        }
        rows.push(cells);
    }
    Ok(TableTextGrid::from_draft(
        TableTextGridDraft {
            schema_version: TABLE_TEXT_CONVERSION_SCHEMA_VERSION.to_owned(),
            rows,
        },
        limits.text,
    )?)
}

fn require_unmerged(grid: &TableGrid) -> Result<(), TableSortHwpxError> {
    if grid
        .master_cells()
        .iter()
        .any(|cell| cell.row_span != 1 || cell.column_span != 1)
    {
        return Err(TableSortHwpxError::UnsupportedMergedCells);
    }
    Ok(())
}

fn aggregate_payload_digest(
    values: &[domain_ir::TableRulingPayloadBlock],
) -> Result<String, TableSortHwpxError> {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-sort-hwpx-payload/v1\0");
    digest.update(
        u64::try_from(values.len())
            .map_err(|_| TableSortHwpxError::Allocation)?
            .to_le_bytes(),
    );
    for value in values {
        let identifier = value.block_id.as_str().as_bytes();
        digest.update(
            u64::try_from(identifier.len())
                .map_err(|_| TableSortHwpxError::Allocation)?
                .to_le_bytes(),
        );
        digest.update(identifier);
        digest.update(value.payload_sha256.as_bytes());
    }
    Ok(create_hwpx::hex(digest.finalize()))
}

fn classify_sort_value(value: &str) -> Result<TableSortValue, TableSortHwpxError> {
    if value.is_empty() {
        return Ok(TableSortValue::Blank);
    }
    if value == "false" || value == "true" {
        return Ok(TableSortValue::Boolean {
            value: value == "true",
        });
    }
    if canonical_integer_syntax(value) {
        return value
            .parse::<i64>()
            .map(|value| TableSortValue::Integer { value })
            .map_err(|_| TableSortHwpxError::UnsupportedSortValue);
    }
    if let Some((integer, fraction)) = canonical_decimal_parts(value) {
        if fraction.len() > 18 {
            return Err(TableSortHwpxError::UnsupportedSortValue);
        }
        let mut coefficient = String::new();
        coefficient
            .try_reserve(integer.len().saturating_add(fraction.len()))
            .map_err(|_| TableSortHwpxError::Allocation)?;
        coefficient.push_str(integer);
        coefficient.push_str(fraction);
        let coefficient = coefficient
            .parse::<i64>()
            .map_err(|_| TableSortHwpxError::UnsupportedSortValue)?;
        return Ok(TableSortValue::Decimal {
            coefficient,
            scale: u8::try_from(fraction.len())
                .map_err(|_| TableSortHwpxError::UnsupportedSortValue)?,
        });
    }
    Ok(TableSortValue::Text {
        value: value.to_owned(),
    })
}

fn canonical_integer_syntax(value: &str) -> bool {
    let unsigned = value.strip_prefix('-').unwrap_or(value);
    !unsigned.is_empty()
        && unsigned.bytes().all(|byte| byte.is_ascii_digit())
        && (unsigned == "0" || !unsigned.starts_with('0'))
        && value != "-0"
}

fn canonical_decimal_parts(value: &str) -> Option<(&str, &str)> {
    let (integer, fraction) = value.split_once('.')?;
    let unsigned = integer.strip_prefix('-').unwrap_or(integer);
    if unsigned.is_empty()
        || fraction.is_empty()
        || !unsigned.bytes().all(|byte| byte.is_ascii_digit())
        || !fraction.bytes().all(|byte| byte.is_ascii_digit())
        || (unsigned != "0" && unsigned.starts_with('0'))
        || integer == "-0" && fraction.bytes().all(|byte| byte == b'0')
    {
        return None;
    }
    Some((integer, fraction))
}

fn same_pagination_policy(
    source: &TablePaginationHwpxReadback,
    target: &TablePaginationHwpxReadback,
) -> bool {
    source.page_split == target.page_split
        && source.repeat_header_rows == target.repeat_header_rows
        && source.row_count == target.row_count
        && source.column_count == target.column_count
        && source.caption == target.caption
}

fn pagination_policy_sha256(value: &TablePaginationHwpxReadback) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-sort-hwpx-pagination-policy/v1\0");
    digest.update([match value.page_split {
        TablePageSplitPolicy::Allow => 0,
        TablePageSplitPolicy::AvoidRow => 1,
        TablePageSplitPolicy::AvoidTable => 2,
        TablePageSplitPolicy::RequiredKeep => 3,
    }]);
    digest.update(value.repeat_header_rows.to_le_bytes());
    digest.update(value.row_count.to_le_bytes());
    digest.update(value.column_count.to_le_bytes());
    match &value.caption {
        None => digest.update([0]),
        Some(caption) => {
            digest.update([1]);
            digest.update([match caption.side {
                CaptionSide::Top => 0,
                CaptionSide::Bottom => 1,
            }]);
            digest.update([u8::from(caption.full_size)]);
            digest.update(caption.width_hwpunit.to_le_bytes());
            digest.update(caption.gap_hwpunit.to_le_bytes());
            digest.update(caption.last_width_hwpunit.to_le_bytes());
            digest.update(caption.content_sha256);
        }
    }
    digest.finalize().into()
}

fn text_adapter_limits(limits: &TableSortHwpxLimits) -> TableTextToTableHwpxLimits {
    TableTextToTableHwpxLimits {
        create: TableCreateHwpxLimits {
            ruling: limits.native,
            pagination: limits.pagination,
        },
        text: limits.text,
        flow: limits.flow,
    }
}

fn serialized_limit(limits: &TableSortHwpxLimits) -> usize {
    limits
        .sort
        .config()
        .serialized_bytes
        .min(limits.native.ruling.config().serialized_bytes)
        .min(limits.native.grid.config().serialized_bytes)
        .min(limits.text.config().serialized_bytes)
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableSortHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableSortHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableSortHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableSortHwpxError> {
    create_hwpx::require_digest(value).map_err(|_| TableSortHwpxError::SourceBindingMismatch)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text =
            std::str::from_utf8(chunk).map_err(|_| TableSortHwpxError::SourceBindingMismatch)?;
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableSortHwpxError::SourceBindingMismatch)?;
    }
    Ok(output)
}
