use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    CellCoordinate, FormulaAstDraft, FormulaCell, FormulaCellDraft, PlannedWholeTable,
    TABLE_FORMULA_SCHEMA_VERSION, TABLE_PARTITION_SCHEMA_VERSION, TABLE_RULING_SCHEMA_VERSION,
    TableGrid, TableGridError, TablePartitionBuilder, TablePartitionError,
    TablePartitionFormulaPolicy, TablePartitionLimits, TablePartitionState,
    TablePartitionStateDraft, TableRulingAxis, TableRulingCellDraft, TableRulingEdge,
    TableRulingError, TableRulingFrame, TableRulingState, TableRulingStateDraft,
    WholeTableSplitPlan, WholeTableSplitRequest, WholeTableSplitRequestDraft,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{
    TableRulingHwpxBinding, TableRulingHwpxError, TableRulingHwpxLimits, TableRulingHwpxReadback,
    TableRulingHwpxReader,
};
use crate::{
    PreservingXmlDocument, PreservingXmlError, TableLayoutHwpxError, TableLayoutHwpxReader,
    TablePaginationHwpxError, TablePaginationHwpxLimits, TablePaginationHwpxReadback,
    TablePaginationHwpxReader,
};

pub const TABLE_SPLIT_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-split-hwpx/v1";
pub const TABLE_SPLIT_HWPX_PROFILE_ID: &str = "hwpx-agent.table-split-hwpx.hancom-2020-wrapper/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableSplitHwpxLimits {
    pub ruling: TableRulingHwpxLimits,
    pub partition: TablePartitionLimits,
    pub pagination: TablePaginationHwpxLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableSplitHwpxReadback {
    pub profile_id: &'static str,
    pub table_ordinal: usize,
    pub ruling: TableRulingHwpxReadback,
    pub partition: TablePartitionState,
    pub pagination: TablePaginationHwpxReadback,
    pub wrapper_sha256: [u8; 32],
}

impl std::fmt::Debug for TableSplitHwpxReadback {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableSplitHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("rows", &self.ruling.grid.rows())
            .field("columns", &self.ruling.grid.columns())
            .field("master_cell_count", &self.ruling.grid.master_cell_count())
            .field("payload_block_count", &self.ruling.payload_block_count)
            .field("formula_count", &self.ruling.formula_count)
            .field("page_split", &self.pagination.page_split)
            .field("repeat_header_rows", &self.pagination.repeat_header_rows)
            .field("has_caption", &self.pagination.caption.is_some())
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableSplitHwpxReader;

impl TableSplitHwpxReader {
    /// Reads one exact top-level current-Hangul-2020 table wrapper and complete semantic state.
    ///
    /// # Errors
    ///
    /// Rejects ruling, grid, payload, property, formula, wrapper or finite-bound drift.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: TableSplitHwpxLimits,
    ) -> Result<TableSplitHwpxReadback, TableSplitHwpxError> {
        let ruling = TableRulingHwpxReader::read_existing(
            header,
            section,
            table_ordinal,
            binding,
            limits.ruling,
        )?;
        let wrapper = wrapper_shape(section, table_ordinal)?;
        let pagination =
            TablePaginationHwpxReader::read_in_section(section, table_ordinal, limits.pagination)?;
        if pagination.row_count != ruling.grid.rows()
            || pagination.column_count != ruling.grid.columns()
            || pagination.repeat_header_rows != 0
            || pagination.caption.is_some()
        {
            return Err(TableSplitHwpxError::UnsupportedPaginationProfile);
        }
        let partition = partition_state_from_ruling(&ruling, &limits)?;
        Ok(TableSplitHwpxReadback {
            profile_id: TABLE_SPLIT_HWPX_PROFILE_ID,
            table_ordinal,
            ruling,
            partition,
            pagination,
            wrapper_sha256: wrapper.sha256,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct TableSplitHwpxRequestDraft {
    pub schema_version: String,
    pub table_ordinal: usize,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_wrapper_sha256: String,
    pub split: WholeTableSplitRequestDraft,
}

impl std::fmt::Debug for TableSplitHwpxRequestDraft {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableSplitHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_wrapper_sha256", &"<redacted>")
            .field("split", &self.split)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableSplitHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_ordinal: usize,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_wrapper_sha256: String,
    split: WholeTableSplitRequest,
}

impl TableSplitHwpxRequest {
    /// Admits one formula-free whole-table split bound to exact parts, wrapper, state and flow.
    ///
    /// # Errors
    ///
    /// Rejects version, part, wrapper, source, flow, formula-profile or domain drift.
    pub fn from_draft(
        draft: TableSplitHwpxRequestDraft,
        source: &TableSplitHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableSplitHwpxLimits,
    ) -> Result<Self, TableSplitHwpxError> {
        if draft.schema_version != TABLE_SPLIT_HWPX_SCHEMA_VERSION {
            return Err(TableSplitHwpxError::UnsupportedVersion);
        }
        for value in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_wrapper_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(value)?;
        }
        if draft.split.formula_policy != TablePartitionFormulaPolicy::Reject {
            return Err(TableSplitHwpxError::UnsupportedFormulaProfile);
        }
        let split = WholeTableSplitRequest::from_draft(
            draft.split,
            &source.partition,
            &source.ruling.grid,
            current_document_flow_sha256,
            limits.partition,
        )?;
        let request = Self {
            schema_version: TABLE_SPLIT_HWPX_SCHEMA_VERSION,
            capability_id: split.capability_id(),
            table_ordinal: draft.table_ordinal,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_wrapper_sha256: draft.expected_wrapper_sha256,
            split,
        };
        validate_request_source(&request, source)?;
        let _ =
            TableSplitHwpxBuilder::build(&request, source, current_document_flow_sha256, limits)?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies the same exact admission as [`Self::from_draft`].
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &TableSplitHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableSplitHwpxLimits,
    ) -> Result<Self, TableSplitHwpxError> {
        if bytes.is_empty()
            || bytes.len() > limits.partition.config().input_bytes
            || bytes.len() > limits.ruling.ruling.config().input_bytes
        {
            return Err(TableSplitHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableSplitHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn table_ordinal(&self) -> usize {
        self.table_ordinal
    }

    #[must_use]
    pub const fn split(&self) -> &WholeTableSplitRequest {
        &self.split
    }

    /// Serializes the complete typed request under the configured finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableSplitHwpxLimits,
    ) -> Result<Vec<u8>, TableSplitHwpxError> {
        serialize_bounded(self, limits.partition.config().serialized_bytes)
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableSplitHwpxLimits,
    ) -> Result<[u8; 32], TableSplitHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl std::fmt::Debug for TableSplitHwpxRequest {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableSplitHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_ordinal", &self.table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_wrapper_sha256", &"<redacted>")
            .field("split", &self.split)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableSplitHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    first_grid_sha256: String,
    second_grid_sha256: String,
    #[serde(skip)]
    first_grid: TableGrid,
    #[serde(skip)]
    second_grid: TableGrid,
    first_state: TableRulingState,
    second_state: TableRulingState,
    domain: WholeTableSplitPlan,
}

impl TableSplitHwpxPlan {
    #[must_use]
    pub const fn first_grid(&self) -> &TableGrid {
        &self.first_grid
    }

    #[must_use]
    pub const fn second_grid(&self) -> &TableGrid {
        &self.second_grid
    }

    #[must_use]
    pub const fn first_state(&self) -> &TableRulingState {
        &self.first_state
    }

    #[must_use]
    pub const fn second_state(&self) -> &TableRulingState {
        &self.second_state
    }

    #[must_use]
    pub const fn domain(&self) -> &WholeTableSplitPlan {
        &self.domain
    }

    /// Serializes the complete target states and domain plan under a finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableSplitHwpxLimits,
    ) -> Result<Vec<u8>, TableSplitHwpxError> {
        serialize_bounded(self, limits.partition.config().serialized_bytes)
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableSplitHwpxLimits,
    ) -> Result<[u8; 32], TableSplitHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl std::fmt::Debug for TableSplitHwpxPlan {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableSplitHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("first_rows", &self.first_grid.rows())
            .field("second_rows", &self.second_grid.rows())
            .field("columns", &self.first_grid.columns())
            .field("domain", &self.domain)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableSplitHwpxBuilder;

impl TableSplitHwpxBuilder {
    /// Revalidates source/flow and builds exact first and second HWPX semantic target states.
    ///
    /// # Errors
    ///
    /// Rejects source, flow, domain, geometry, payload, property or finite-bound drift.
    pub fn build(
        request: &TableSplitHwpxRequest,
        source: &TableSplitHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableSplitHwpxLimits,
    ) -> Result<TableSplitHwpxPlan, TableSplitHwpxError> {
        validate_request_source(request, source)?;
        require_digest(current_document_flow_sha256)?;
        if request.split.formula_policy() != TablePartitionFormulaPolicy::Reject {
            return Err(TableSplitHwpxError::UnsupportedFormulaProfile);
        }
        let domain = TablePartitionBuilder::split(
            &request.split,
            &source.partition,
            &source.ruling.grid,
            current_document_flow_sha256,
            limits.ruling.grid,
            limits.ruling.formula,
            limits.partition,
        )?;
        let first_grid = grid_from_planned(domain.first(), &limits)?;
        let second_grid = grid_from_planned(domain.second(), &limits)?;
        let split_row = request.split.split_before_row();
        let first_boundaries =
            split_row_boundaries(source.ruling.state.row_boundaries_hwpunit(), 0, split_row)?;
        let second_boundaries = split_row_boundaries(
            source.ruling.state.row_boundaries_hwpunit(),
            split_row,
            source.ruling.grid.rows(),
        )?;
        let first_state = target_state(
            domain.first(),
            &first_grid,
            source,
            0,
            first_boundaries,
            &limits,
        )?;
        let second_state = target_state(
            domain.second(),
            &second_grid,
            source,
            split_row,
            second_boundaries,
            &limits,
        )?;
        let plan = TableSplitHwpxPlan {
            schema_version: TABLE_SPLIT_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: hex(request.canonical_sha256(limits)?),
            first_grid_sha256: hex(first_grid.canonical_sha256()?),
            second_grid_sha256: hex(second_grid.canonical_sha256()?),
            first_grid,
            second_grid,
            first_state,
            second_state,
            domain,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableSplitHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_wrapper_sha256: [u8; 32],
    pub first_state_sha256: [u8; 32],
    pub second_state_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub preserved_master_cell_count: usize,
    pub preserved_payload_block_count: usize,
    pub created_table_count: usize,
    pub created_separator_paragraph_count: usize,
    pub allocated_native_id_count: usize,
}

impl std::fmt::Debug for TableSplitHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableSplitHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("source_table_count", &self.source_table_count)
            .field("target_table_count", &self.target_table_count)
            .field(
                "preserved_master_cell_count",
                &self.preserved_master_cell_count,
            )
            .field(
                "preserved_payload_block_count",
                &self.preserved_payload_block_count,
            )
            .field("created_table_count", &self.created_table_count)
            .field(
                "created_separator_paragraph_count",
                &self.created_separator_paragraph_count,
            )
            .field("allocated_native_id_count", &self.allocated_native_id_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableSplitHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub first_binding: TableRulingHwpxBinding,
    pub second_binding: TableRulingHwpxBinding,
    pub receipt: TableSplitHwpxLoweringReceipt,
}

impl std::fmt::Debug for TableSplitHwpxLoweredParts {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableSplitHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("first_binding", &self.first_binding)
            .field("second_binding", &self.second_binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableSplitHwpxLowerer;

impl TableSplitHwpxLowerer {
    /// Lowers an exact split and returns only after both resulting tables reopen semantically.
    ///
    /// # Errors
    ///
    /// Rejects part/source/flow/request/plan drift, wrapper or native-ID mismatch, finite output
    /// failure, or either target readback mismatch.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableSplitHwpxRequest,
        plan: &TableSplitHwpxPlan,
        limits: TableSplitHwpxLimits,
    ) -> Result<TableSplitHwpxLoweredParts, TableSplitHwpxError> {
        let source = TableSplitHwpxReader::read_existing(
            header,
            section,
            request.table_ordinal,
            binding,
            limits,
        )?;
        validate_request_source(request, &source)?;
        let rebuilt =
            TableSplitHwpxBuilder::build(request, &source, current_document_flow_sha256, limits)?;
        if rebuilt != *plan {
            return Err(TableSplitHwpxError::PlanBindingMismatch);
        }
        let (output_header, output_section, allocated_native_id_count) =
            render_split_section(header, section, binding, request, &source, plan, &limits)?;
        let source_table_count =
            TableLayoutHwpxReader::count_in_section(section, limits.ruling.layout)?;
        let target_table_count =
            TableLayoutHwpxReader::count_in_section(&output_section, limits.ruling.layout)?;
        if target_table_count
            != source_table_count
                .checked_add(1)
                .ok_or(TableSplitHwpxError::OutputLimit)?
        {
            return Err(TableSplitHwpxError::ReadbackMismatch);
        }
        let first_binding = super::binding_from_state(plan.first_state(), plan.first_grid())?;
        let second_binding = super::binding_from_state(plan.second_state(), plan.second_grid())?;
        let reopened_first = TableSplitHwpxReader::read_existing(
            &output_header,
            &output_section,
            request.table_ordinal,
            &first_binding,
            limits,
        )?;
        let second_ordinal = request
            .table_ordinal
            .checked_add(1)
            .ok_or(TableSplitHwpxError::OutputLimit)?;
        let reopened_second = TableSplitHwpxReader::read_existing(
            &output_header,
            &output_section,
            second_ordinal,
            &second_binding,
            limits,
        )?;
        if reopened_first.ruling.grid != *plan.first_grid()
            || reopened_first.ruling.state != *plan.first_state()
            || !partition_matches_planned(&reopened_first.partition, plan.domain.first())
            || reopened_second.ruling.grid != *plan.second_grid()
            || reopened_second.ruling.state != *plan.second_state()
            || !partition_matches_planned(&reopened_second.partition, plan.domain.second())
            || reopened_first.pagination.page_split != source.pagination.page_split
            || reopened_second.pagination.page_split != source.pagination.page_split
        {
            return Err(TableSplitHwpxError::ReadbackMismatch);
        }
        let domain_receipt = plan.domain.receipt();
        let receipt = TableSplitHwpxLoweringReceipt {
            profile_id: TABLE_SPLIT_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&output_header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&output_section).into(),
            source_wrapper_sha256: source.wrapper_sha256,
            first_state_sha256: plan.first_state().canonical_sha256(limits.ruling.ruling)?,
            second_state_sha256: plan.second_state().canonical_sha256(limits.ruling.ruling)?,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(&domain_receipt.before_flow_sha256)?,
            after_document_flow_sha256: parse_digest(&domain_receipt.after_flow_sha256)?,
            source_table_count,
            target_table_count,
            preserved_master_cell_count: domain_receipt.preserved_master_cell_count,
            preserved_payload_block_count: source.ruling.payload_block_count,
            created_table_count: domain_receipt.created_table_count,
            created_separator_paragraph_count: domain_receipt.created_separator_paragraph_count,
            allocated_native_id_count,
        };
        Ok(TableSplitHwpxLoweredParts {
            header: output_header,
            section: output_section,
            first_binding,
            second_binding,
            receipt,
        })
    }
}

#[allow(clippy::too_many_arguments)]
fn render_split_section(
    header: &[u8],
    section: &[u8],
    binding: &TableRulingHwpxBinding,
    request: &TableSplitHwpxRequest,
    source: &TableSplitHwpxReadback,
    plan: &TableSplitHwpxPlan,
    limits: &TableSplitHwpxLimits,
) -> Result<(Vec<u8>, Vec<u8>, usize), TableSplitHwpxError> {
    let first = super::render_split_existing(
        header,
        section,
        request.table_ordinal,
        binding,
        &source.ruling.state,
        plan.first_state(),
        plan.first_grid(),
        &limits.ruling,
    )?;
    let second = super::render_split_existing(
        header,
        section,
        request.table_ordinal,
        binding,
        &source.ruling.state,
        plan.second_state(),
        plan.second_grid(),
        &limits.ruling,
    )?;
    if first.header != second.header {
        return Err(TableSplitHwpxError::HeaderPlanMismatch);
    }
    let native_ids = allocate_native_ids(section, 3)?;
    let first_wrapper = patched_wrapper(
        &first.section,
        request.table_ordinal,
        None,
        None,
        false,
        limits,
    )?;
    let separator_wrapper = patched_wrapper(
        &first.section,
        request.table_ordinal,
        Some(native_ids[0]),
        None,
        true,
        limits,
    )?;
    let second_wrapper = patched_wrapper(
        &second.section,
        request.table_ordinal,
        Some(native_ids[1]),
        Some(native_ids[2]),
        false,
        limits,
    )?;
    let mut replacement = Vec::new();
    append_bounded(&mut replacement, &first_wrapper, limits)?;
    append_bounded(&mut replacement, &separator_wrapper, limits)?;
    append_bounded(&mut replacement, &second_wrapper, limits)?;
    let source_wrapper = wrapper_shape(section, request.table_ordinal)?;
    let output_section = replace_bounded(
        section,
        source_wrapper.outer.start(),
        source_wrapper.outer.end(),
        &replacement,
        limits,
    )?;
    Ok((first.header, output_section, native_ids.len()))
}

#[derive(Debug, Error)]
pub enum TableSplitHwpxError {
    #[error("unsupported table split HWPX schema version")]
    UnsupportedVersion,
    #[error("table split HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table split HWPX JSON")]
    InvalidJson,
    #[error("invalid table split HWPX binding")]
    InvalidBinding,
    #[error("table split HWPX source parts or wrapper drifted")]
    SourceBindingMismatch,
    #[error("table split HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("formula rebasing is outside this exact native split profile")]
    UnsupportedFormulaProfile,
    #[error("selected table is not the exact top-level Hangul wrapper profile")]
    UnsupportedWrapper,
    #[error("repeat-header or caption semantics are outside this exact native split profile")]
    UnsupportedPaginationProfile,
    #[error("native paragraph or table identity space is exhausted")]
    NativeIdExhausted,
    #[error("independent split renders produced different header catalogs")]
    HeaderPlanMismatch,
    #[error("table split HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table split HWPX allocation failed")]
    AllocationFailed,
    #[error("table split HWPX serialization failed")]
    Serialization,
    #[error("table split HWPX output exceeds a finite bound")]
    OutputLimit,
    #[error(transparent)]
    Partition(#[from] TablePartitionError),
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    ModelRuling(#[from] TableRulingError),
    #[error(transparent)]
    Ruling(#[from] TableRulingHwpxError),
    #[error(transparent)]
    Layout(#[from] TableLayoutHwpxError),
    #[error(transparent)]
    Pagination(#[from] TablePaginationHwpxError),
    #[error(transparent)]
    Xml(#[from] PreservingXmlError),
}

impl TableSplitHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_split_hwpx_version",
            Self::InputLimit => "table_split_hwpx_input_limit",
            Self::InvalidJson => "table_split_hwpx_invalid_json",
            Self::InvalidBinding => "table_split_hwpx_invalid_binding",
            Self::SourceBindingMismatch => "table_split_hwpx_source_binding_mismatch",
            Self::PlanBindingMismatch => "table_split_hwpx_plan_binding_mismatch",
            Self::UnsupportedFormulaProfile => "table_split_hwpx_formula_profile",
            Self::UnsupportedWrapper => "table_split_hwpx_wrapper_profile",
            Self::UnsupportedPaginationProfile => "table_split_hwpx_pagination_profile",
            Self::NativeIdExhausted => "table_split_hwpx_native_id_exhausted",
            Self::HeaderPlanMismatch => "table_split_hwpx_header_plan_mismatch",
            Self::ReadbackMismatch => "table_split_hwpx_readback_mismatch",
            Self::AllocationFailed => "table_split_hwpx_allocation",
            Self::Serialization => "table_split_hwpx_serialization",
            Self::OutputLimit => "table_split_hwpx_output_limit",
            Self::Partition(_) => "table_split_hwpx_partition",
            Self::Grid(_) => "table_split_hwpx_grid",
            Self::ModelRuling(_) => "table_split_hwpx_model_ruling",
            Self::Ruling(_) => "table_split_hwpx_ruling",
            Self::Layout(_) => "table_split_hwpx_layout",
            Self::Pagination(_) => "table_split_hwpx_pagination",
            Self::Xml(_) => "table_split_hwpx_xml",
        }
    }
}

fn validate_request_source(
    request: &TableSplitHwpxRequest,
    source: &TableSplitHwpxReadback,
) -> Result<(), TableSplitHwpxError> {
    if request.table_ordinal != source.table_ordinal
        || request.split.table_id() != source.partition.table_id()
        || request.expected_header_sha256 != hex(source.ruling.header_sha256)
        || request.expected_section_sha256 != hex(source.ruling.section_sha256)
        || request.expected_wrapper_sha256 != hex(source.wrapper_sha256)
    {
        return Err(TableSplitHwpxError::SourceBindingMismatch);
    }
    Ok(())
}

fn partition_matches_planned(state: &TablePartitionState, planned: &PlannedWholeTable) -> bool {
    state.table_id() == planned.table_id()
        && state.grid_sha256() == planned.grid_sha256()
        && state.table_properties_sha256() == planned.table_properties_sha256()
        && state.table_width_hwpunit() == planned.table_width_hwpunit()
        && state.column_widths_hwpunit() == planned.column_widths_hwpunit()
        && state.cells().len() == planned.cells().len()
        && state
            .cells()
            .iter()
            .zip(planned.cells())
            .all(|(left, right)| {
                left.master_cell_id() == right.master_cell_id()
                    && left.coordinate() == right.coordinate()
                    && left.payload_sha256() == right.payload_sha256()
                    && left.cell_properties_sha256() == right.cell_properties_sha256()
                    && left.formula() == right.formula()
            })
}

fn partition_state_from_ruling(
    ruling: &TableRulingHwpxReadback,
    limits: &TableSplitHwpxLimits,
) -> Result<TablePartitionState, TableSplitHwpxError> {
    let mut column_widths = Vec::new();
    column_widths
        .try_reserve_exact(ruling.grid.columns() as usize)
        .map_err(|_| TableSplitHwpxError::AllocationFailed)?;
    for pair in ruling.state.column_boundaries_hwpunit().windows(2) {
        column_widths.push(
            pair[1]
                .checked_sub(pair[0])
                .ok_or(TableSplitHwpxError::InvalidBinding)?,
        );
    }
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(ruling.state.cells().len())
        .map_err(|_| TableSplitHwpxError::AllocationFailed)?;
    for cell in ruling.state.cells() {
        cells.push(domain_ir::TablePartitionCellDraft {
            master_cell_id: cell.master_cell_id().clone(),
            coordinate: cell.coordinate(),
            payload_sha256: value_digest(cell.payload(), limits)?,
            cell_properties_sha256: value_digest(cell.properties(), limits)?,
            formula: cell.formula().map(formula_draft),
        });
    }
    Ok(TablePartitionState::from_draft(
        TablePartitionStateDraft {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION.to_owned(),
            table_id: ruling.state.table_id().clone(),
            grid_sha256: hex(ruling.grid.canonical_sha256()?),
            table_properties_sha256: ruling.state.table_properties_sha256().to_owned(),
            table_width_hwpunit: ruling.state.frame().width_hwpunit,
            column_widths_hwpunit: column_widths,
            cells,
        },
        &ruling.grid,
        limits.ruling.formula,
        limits.partition,
    )?)
}

fn grid_from_planned(
    planned: &PlannedWholeTable,
    limits: &TableSplitHwpxLimits,
) -> Result<TableGrid, TableSplitHwpxError> {
    let grid = TableGrid::new(
        planned.rows(),
        planned.columns(),
        planned.master_cells().to_vec(),
        limits.ruling.grid,
    )?;
    if planned.grid_sha256() != hex(grid.canonical_sha256()?) {
        return Err(TableSplitHwpxError::PlanBindingMismatch);
    }
    Ok(grid)
}

fn target_state(
    planned: &PlannedWholeTable,
    grid: &TableGrid,
    source: &TableSplitHwpxReadback,
    source_row_offset: u32,
    row_boundaries_hwpunit: Vec<u32>,
    limits: &TableSplitHwpxLimits,
) -> Result<TableRulingState, TableSplitHwpxError> {
    if planned.table_properties_sha256() != source.ruling.state.table_properties_sha256()
        || planned.table_width_hwpunit() != source.ruling.state.frame().width_hwpunit
        || planned.column_widths_hwpunit() != source.partition.column_widths_hwpunit()
        || planned.cells().len() != grid.master_cell_count()
    {
        return Err(TableSplitHwpxError::PlanBindingMismatch);
    }
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(planned.cells().len())
        .map_err(|_| TableSplitHwpxError::AllocationFailed)?;
    for planned_cell in planned.cells() {
        let source_cell = source
            .ruling
            .state
            .cell(planned_cell.master_cell_id())
            .ok_or(TableSplitHwpxError::SourceBindingMismatch)?;
        let source_coordinate = CellCoordinate {
            row: planned_cell
                .coordinate()
                .row
                .checked_add(source_row_offset)
                .ok_or(TableSplitHwpxError::PlanBindingMismatch)?,
            column: planned_cell.coordinate().column,
        };
        if source_cell.coordinate() != source_coordinate
            || planned_cell.payload_sha256() != value_digest(source_cell.payload(), limits)?
            || planned_cell.cell_properties_sha256()
                != value_digest(source_cell.properties(), limits)?
            || planned_cell.formula().is_some()
            || source_cell.formula().is_some()
        {
            return Err(TableSplitHwpxError::PlanBindingMismatch);
        }
        cells.push(TableRulingCellDraft {
            master_cell_id: planned_cell.master_cell_id().clone(),
            coordinate: planned_cell.coordinate(),
            payload: source_cell.payload().to_vec(),
            properties: source_cell.properties().clone(),
            formula: None,
        });
    }
    let height = *row_boundaries_hwpunit
        .last()
        .ok_or(TableSplitHwpxError::PlanBindingMismatch)?;
    let edges = translated_edges(
        &source.ruling.state,
        grid.rows(),
        grid.columns(),
        source_row_offset,
    )?;
    let source_frame = source.ruling.state.frame();
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: planned.table_id().clone(),
            frame: TableRulingFrame {
                left_hwpunit: source_frame.left_hwpunit,
                top_hwpunit: source_frame.top_hwpunit,
                width_hwpunit: planned.table_width_hwpunit(),
                height_hwpunit: height,
            },
            grid_sha256: hex(grid.canonical_sha256()?),
            table_properties_sha256: planned.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit,
            column_boundaries_hwpunit: source.ruling.state.column_boundaries_hwpunit().to_vec(),
            edges,
            cells,
        },
        grid,
        limits.ruling.formula,
        limits.ruling.ruling,
    )?)
}

fn split_row_boundaries(
    source: &[u32],
    start_row: u32,
    end_row: u32,
) -> Result<Vec<u32>, TableSplitHwpxError> {
    if start_row >= end_row {
        return Err(TableSplitHwpxError::PlanBindingMismatch);
    }
    let start = usize::try_from(start_row).map_err(|_| TableSplitHwpxError::PlanBindingMismatch)?;
    let end = usize::try_from(end_row).map_err(|_| TableSplitHwpxError::PlanBindingMismatch)?;
    let base = *source
        .get(start)
        .ok_or(TableSplitHwpxError::PlanBindingMismatch)?;
    let values = source
        .get(start..=end)
        .ok_or(TableSplitHwpxError::PlanBindingMismatch)?;
    let mut output = Vec::new();
    output
        .try_reserve_exact(values.len())
        .map_err(|_| TableSplitHwpxError::AllocationFailed)?;
    for value in values {
        output.push(
            value
                .checked_sub(base)
                .ok_or(TableSplitHwpxError::PlanBindingMismatch)?,
        );
    }
    Ok(output)
}

fn translated_edges(
    source: &TableRulingState,
    rows: u32,
    columns: u32,
    row_offset: u32,
) -> Result<Vec<TableRulingEdge>, TableSplitHwpxError> {
    let horizontal_count = usize::try_from(rows)
        .ok()
        .and_then(|rows| rows.checked_add(1))
        .and_then(|rows| rows.checked_mul(columns as usize))
        .ok_or(TableSplitHwpxError::AllocationFailed)?;
    let vertical_count = usize::try_from(columns)
        .ok()
        .and_then(|columns| columns.checked_add(1))
        .and_then(|columns| columns.checked_mul(rows as usize))
        .ok_or(TableSplitHwpxError::AllocationFailed)?;
    let mut output = Vec::new();
    output
        .try_reserve_exact(
            horizontal_count
                .checked_add(vertical_count)
                .ok_or(TableSplitHwpxError::AllocationFailed)?,
        )
        .map_err(|_| TableSplitHwpxError::AllocationFailed)?;
    for boundary in 0..=rows {
        let source_boundary = boundary
            .checked_add(row_offset)
            .ok_or(TableSplitHwpxError::PlanBindingMismatch)?;
        for offset in 0..columns {
            output.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256: source
                    .edge(TableRulingAxis::Horizontal, source_boundary, offset)
                    .ok_or(TableSplitHwpxError::SourceBindingMismatch)?
                    .line_sha256
                    .clone(),
            });
        }
    }
    for boundary in 0..=columns {
        for offset in 0..rows {
            let source_offset = offset
                .checked_add(row_offset)
                .ok_or(TableSplitHwpxError::PlanBindingMismatch)?;
            output.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256: source
                    .edge(TableRulingAxis::Vertical, boundary, source_offset)
                    .ok_or(TableSplitHwpxError::SourceBindingMismatch)?
                    .line_sha256
                    .clone(),
            });
        }
    }
    Ok(output)
}

#[derive(Clone, Copy, Debug)]
struct WrapperShape {
    table: usize,
    paragraph: usize,
    outer: crate::XmlByteSpan,
    sha256: [u8; 32],
}

fn wrapper_shape(
    section: &[u8],
    table_ordinal: usize,
) -> Result<WrapperShape, TableSplitHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let table = super::selected_table(&document, table_ordinal)?;
    let run = super::element(&document, table)?
        .parent()
        .ok_or(TableSplitHwpxError::UnsupportedWrapper)?;
    let paragraph = super::element(&document, run)?
        .parent()
        .ok_or(TableSplitHwpxError::UnsupportedWrapper)?;
    if !super::has_name(super::element(&document, run)?, "run")
        || !super::has_name(super::element(&document, paragraph)?, "p")
        || super::element(&document, paragraph)?.parent() != Some(document.root_element())
    {
        return Err(TableSplitHwpxError::UnsupportedWrapper);
    }
    let wrapper = super::insertion_wrapper(section, table_ordinal)?;
    let outer = super::element(&document, paragraph)?
        .outer_span()
        .ok_or(TableSplitHwpxError::UnsupportedWrapper)?;
    let _ = super::required_u32(super::element(&document, paragraph)?, "id")?;
    let _ = super::required_u32(super::element(&document, table)?, "id")?;
    Ok(WrapperShape {
        table,
        paragraph,
        outer,
        sha256: Sha256::digest(wrapper).into(),
    })
}

fn patched_wrapper(
    section: &[u8],
    table_ordinal: usize,
    paragraph_id: Option<u32>,
    table_id: Option<u32>,
    replace_table: bool,
    limits: &TableSplitHwpxLimits,
) -> Result<Vec<u8>, TableSplitHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let shape = wrapper_shape(section, table_ordinal)?;
    let mut edits = Vec::new();
    if let Some(value) = paragraph_id {
        super::push_attribute_edit(&document, shape.paragraph, "id", value, &mut edits)?;
    }
    if let Some(value) = table_id {
        super::push_attribute_edit(&document, shape.table, "id", value, &mut edits)?;
    }
    if replace_table {
        let span = super::element(&document, shape.table)?
            .outer_span()
            .ok_or(TableSplitHwpxError::UnsupportedWrapper)?;
        edits.push(super::RawEdit {
            start: span.start(),
            end: span.end(),
            replacement: b"<hp:t/>".to_vec(),
        });
    }
    Ok(super::apply_range_edits(
        section,
        shape.outer.start(),
        shape.outer.end(),
        &mut edits,
        limits.ruling.layout.config().output_bytes,
    )?)
}

fn allocate_native_ids(section: &[u8], count: usize) -> Result<Vec<u32>, TableSplitHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let mut used = BTreeSet::new();
    for value in document.elements() {
        if super::has_name(value, "p") || super::has_name(value, "tbl") {
            used.insert(super::required_u32(value, "id")?);
        }
    }
    let mut candidate = used.iter().next_back().copied().unwrap_or(0);
    let mut output = Vec::new();
    output
        .try_reserve_exact(count)
        .map_err(|_| TableSplitHwpxError::AllocationFailed)?;
    while output.len() < count {
        candidate = candidate
            .checked_add(1)
            .ok_or(TableSplitHwpxError::NativeIdExhausted)?;
        if used.insert(candidate) {
            output.push(candidate);
        }
    }
    Ok(output)
}

fn replace_bounded(
    source: &[u8],
    start: usize,
    end: usize,
    replacement: &[u8],
    limits: &TableSplitHwpxLimits,
) -> Result<Vec<u8>, TableSplitHwpxError> {
    if start > end || end > source.len() {
        return Err(TableSplitHwpxError::UnsupportedWrapper);
    }
    let output_len = source
        .len()
        .checked_sub(end - start)
        .and_then(|value| value.checked_add(replacement.len()))
        .ok_or(TableSplitHwpxError::OutputLimit)?;
    if output_len > limits.ruling.layout.config().output_bytes
        || output_len > limits.partition.config().serialized_bytes
    {
        return Err(TableSplitHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TableSplitHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..start]);
    output.extend_from_slice(replacement);
    output.extend_from_slice(&source[end..]);
    Ok(output)
}

fn append_bounded(
    output: &mut Vec<u8>,
    value: &[u8],
    limits: &TableSplitHwpxLimits,
) -> Result<(), TableSplitHwpxError> {
    let new_len = output
        .len()
        .checked_add(value.len())
        .ok_or(TableSplitHwpxError::OutputLimit)?;
    if new_len > limits.ruling.layout.config().output_bytes
        || new_len > limits.partition.config().serialized_bytes
    {
        return Err(TableSplitHwpxError::OutputLimit);
    }
    output
        .try_reserve(value.len())
        .map_err(|_| TableSplitHwpxError::AllocationFailed)?;
    output.extend_from_slice(value);
    Ok(())
}

fn formula_draft(value: &FormulaCell) -> FormulaCellDraft {
    FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner: value.owner(),
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: value.ast().expression().clone(),
        },
        cache: value.cache().clone(),
        number_format: value.number_format(),
    }
}

fn value_digest<T: Serialize + ?Sized>(
    value: &T,
    limits: &TableSplitHwpxLimits,
) -> Result<String, TableSplitHwpxError> {
    Ok(hex(Sha256::digest(serialize_bounded(
        value,
        limits.partition.config().serialized_bytes,
    )?)))
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableSplitHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableSplitHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableSplitHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TableSplitHwpxError> {
    struct DuplicateRejectingSeed;

    impl<'de> serde::de::DeserializeSeed<'de> for DuplicateRejectingSeed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateRejectingVisitor)
        }
    }

    struct DuplicateRejectingVisitor;

    impl<'de> serde::de::Visitor<'de> for DuplicateRejectingVisitor {
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
                map.next_value_seed(DuplicateRejectingSeed)?;
            }
            Ok(())
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::SeqAccess<'de>,
        {
            while sequence
                .next_element_seed(DuplicateRejectingSeed)?
                .is_some()
            {}
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
    serde::de::DeserializeSeed::deserialize(DuplicateRejectingSeed, &mut deserializer)
        .map_err(|_| TableSplitHwpxError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| TableSplitHwpxError::InvalidJson)
}

fn require_digest(value: &str) -> Result<(), TableSplitHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableSplitHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableSplitHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(chunk).map_err(|_| TableSplitHwpxError::InvalidBinding)?;
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableSplitHwpxError::InvalidBinding)?;
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
