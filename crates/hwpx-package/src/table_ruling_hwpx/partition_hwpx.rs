use std::cmp::Ordering;
use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    CellCoordinate, FormulaAstDraft, FormulaCell, FormulaCellDraft, PlannedWholeTable,
    TABLE_FORMULA_SCHEMA_VERSION, TABLE_PARTITION_SCHEMA_VERSION, TABLE_RULING_SCHEMA_VERSION,
    TableGrid, TableGridError, TableJoinSeparatorToken, TablePartitionBuilder, TablePartitionError,
    TablePartitionFormulaPolicy, TablePartitionLimits, TablePartitionState,
    TablePartitionStateDraft, TableRulingAxis, TableRulingCellDraft, TableRulingEdge,
    TableRulingError, TableRulingFrame, TableRulingState, TableRulingStateDraft,
    WholeTableJoinPlan, WholeTableJoinRequest, WholeTableJoinRequestDraft, WholeTableSplitPlan,
    WholeTableSplitRequest, WholeTableSplitRequestDraft,
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
    TablePaginationHwpxReader, XmlTokenKind,
};

pub const TABLE_SPLIT_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-split-hwpx/v1";
pub const TABLE_SPLIT_HWPX_PROFILE_ID: &str = "hwpx-agent.table-split-hwpx.hancom-2020-wrapper/1";
pub const TABLE_JOIN_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-join-hwpx/v1";
pub const TABLE_JOIN_HWPX_PROFILE_ID: &str = "hwpx-agent.table-join-hwpx.hancom-2020-wrapper/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableSplitHwpxLimits {
    pub ruling: TableRulingHwpxLimits,
    pub partition: TablePartitionLimits,
    pub pagination: TablePaginationHwpxLimits,
}

pub type TableJoinHwpxLimits = TableSplitHwpxLimits;

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

#[derive(Clone, Eq, PartialEq)]
pub struct TableJoinHwpxReadback {
    pub profile_id: &'static str,
    pub leading_table_ordinal: usize,
    pub trailing_table_ordinal: usize,
    pub leading: TableSplitHwpxReadback,
    pub trailing: TableSplitHwpxReadback,
    pub separator_tokens: Vec<TableJoinSeparatorToken>,
    pub separator_sha256: [u8; 32],
    pub separator_paragraph_count: usize,
}

impl std::fmt::Debug for TableJoinHwpxReadback {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableJoinHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("leading_table_ordinal", &self.leading_table_ordinal)
            .field("trailing_table_ordinal", &self.trailing_table_ordinal)
            .field("leading_rows", &self.leading.ruling.grid.rows())
            .field("trailing_rows", &self.trailing.ruling.grid.rows())
            .field("separator_token_count", &self.separator_tokens.len())
            .field("separator_paragraph_count", &self.separator_paragraph_count)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableJoinHwpxReader;

impl TableJoinHwpxReader {
    /// Reads two exact adjacent top-level table wrappers and their whitespace-only separator.
    ///
    /// # Errors
    ///
    /// Rejects non-adjacent wrappers, formulas, pagination divergence, non-whitespace separator
    /// content, or any complete ruling/partition state drift.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        leading_table_ordinal: usize,
        trailing_table_ordinal: usize,
        leading_binding: &TableRulingHwpxBinding,
        trailing_binding: &TableRulingHwpxBinding,
        limits: TableJoinHwpxLimits,
    ) -> Result<TableJoinHwpxReadback, TableJoinHwpxError> {
        if trailing_table_ordinal
            != leading_table_ordinal
                .checked_add(1)
                .ok_or(TableJoinHwpxError::UnsupportedWrapper)?
        {
            return Err(TableJoinHwpxError::NonAdjacentTables);
        }
        let leading = TableSplitHwpxReader::read_existing(
            header,
            section,
            leading_table_ordinal,
            leading_binding,
            limits,
        )?;
        let trailing = TableSplitHwpxReader::read_existing(
            header,
            section,
            trailing_table_ordinal,
            trailing_binding,
            limits,
        )?;
        if leading.ruling.formula_count != 0 || trailing.ruling.formula_count != 0 {
            return Err(TableJoinHwpxError::UnsupportedFormulaProfile);
        }
        if leading.pagination.page_split != trailing.pagination.page_split {
            return Err(TableJoinHwpxError::PaginationMismatch);
        }
        let separator = separator_shape(section, leading_table_ordinal, trailing_table_ordinal)?;
        Ok(TableJoinHwpxReadback {
            profile_id: TABLE_JOIN_HWPX_PROFILE_ID,
            leading_table_ordinal,
            trailing_table_ordinal,
            leading,
            trailing,
            separator_tokens: separator.tokens,
            separator_sha256: separator.sha256,
            separator_paragraph_count: separator.paragraph_count,
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct TableJoinHwpxRequestDraft {
    pub schema_version: String,
    pub leading_table_ordinal: usize,
    pub trailing_table_ordinal: usize,
    pub expected_header_sha256: String,
    pub expected_section_sha256: String,
    pub expected_leading_wrapper_sha256: String,
    pub expected_trailing_wrapper_sha256: String,
    pub expected_separator_sha256: String,
    pub join: WholeTableJoinRequestDraft,
}

impl std::fmt::Debug for TableJoinHwpxRequestDraft {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableJoinHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("leading_table_ordinal", &self.leading_table_ordinal)
            .field("trailing_table_ordinal", &self.trailing_table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_leading_wrapper_sha256", &"<redacted>")
            .field("expected_trailing_wrapper_sha256", &"<redacted>")
            .field("expected_separator_sha256", &"<redacted>")
            .field("join", &self.join)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableJoinHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    leading_table_ordinal: usize,
    trailing_table_ordinal: usize,
    expected_header_sha256: String,
    expected_section_sha256: String,
    expected_leading_wrapper_sha256: String,
    expected_trailing_wrapper_sha256: String,
    expected_separator_sha256: String,
    join: WholeTableJoinRequest,
}

impl TableJoinHwpxRequest {
    /// Admits one formula-free native join bound to both wrappers, the exact separator and flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, part, wrapper, separator, source-state, flow or domain-plan drift.
    pub fn from_draft(
        draft: TableJoinHwpxRequestDraft,
        source: &TableJoinHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableJoinHwpxLimits,
    ) -> Result<Self, TableJoinHwpxError> {
        if draft.schema_version != TABLE_JOIN_HWPX_SCHEMA_VERSION {
            return Err(TableJoinHwpxError::UnsupportedVersion);
        }
        for value in [
            &draft.expected_header_sha256,
            &draft.expected_section_sha256,
            &draft.expected_leading_wrapper_sha256,
            &draft.expected_trailing_wrapper_sha256,
            &draft.expected_separator_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(value).map_err(|_| TableJoinHwpxError::InvalidBinding)?;
        }
        if draft.join.formula_policy != TablePartitionFormulaPolicy::Reject {
            return Err(TableJoinHwpxError::UnsupportedFormulaProfile);
        }
        if draft.join.separator_tokens != source.separator_tokens {
            return Err(TableJoinHwpxError::SeparatorBindingMismatch);
        }
        let join = WholeTableJoinRequest::from_draft(
            draft.join,
            &source.leading.partition,
            &source.leading.ruling.grid,
            &source.trailing.partition,
            &source.trailing.ruling.grid,
            current_document_flow_sha256,
            limits.partition,
        )?;
        let request = Self {
            schema_version: TABLE_JOIN_HWPX_SCHEMA_VERSION,
            capability_id: join.capability_id(),
            leading_table_ordinal: draft.leading_table_ordinal,
            trailing_table_ordinal: draft.trailing_table_ordinal,
            expected_header_sha256: draft.expected_header_sha256,
            expected_section_sha256: draft.expected_section_sha256,
            expected_leading_wrapper_sha256: draft.expected_leading_wrapper_sha256,
            expected_trailing_wrapper_sha256: draft.expected_trailing_wrapper_sha256,
            expected_separator_sha256: draft.expected_separator_sha256,
            join,
        };
        validate_join_request_source(&request, source)?;
        let _ =
            TableJoinHwpxBuilder::build(&request, source, current_document_flow_sha256, limits)?;
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
        source: &TableJoinHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableJoinHwpxLimits,
    ) -> Result<Self, TableJoinHwpxError> {
        if bytes.is_empty()
            || bytes.len() > limits.partition.config().input_bytes
            || bytes.len() > limits.ruling.ruling.config().input_bytes
        {
            return Err(TableJoinHwpxError::InputLimit);
        }
        reject_duplicate_json_keys(bytes).map_err(|_| TableJoinHwpxError::InvalidJson)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableJoinHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn leading_table_ordinal(&self) -> usize {
        self.leading_table_ordinal
    }

    #[must_use]
    pub const fn trailing_table_ordinal(&self) -> usize {
        self.trailing_table_ordinal
    }

    #[must_use]
    pub const fn join(&self) -> &WholeTableJoinRequest {
        &self.join
    }

    /// Serializes the complete typed request under the configured finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableJoinHwpxLimits,
    ) -> Result<Vec<u8>, TableJoinHwpxError> {
        serialize_join_bounded(self, limits.partition.config().serialized_bytes)
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableJoinHwpxLimits,
    ) -> Result<[u8; 32], TableJoinHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl std::fmt::Debug for TableJoinHwpxRequest {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableJoinHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("leading_table_ordinal", &self.leading_table_ordinal)
            .field("trailing_table_ordinal", &self.trailing_table_ordinal)
            .field("expected_header_sha256", &"<redacted>")
            .field("expected_section_sha256", &"<redacted>")
            .field("expected_leading_wrapper_sha256", &"<redacted>")
            .field("expected_trailing_wrapper_sha256", &"<redacted>")
            .field("expected_separator_sha256", &"<redacted>")
            .field("join", &self.join)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableJoinHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    joined_grid_sha256: String,
    #[serde(skip)]
    joined_grid: TableGrid,
    joined_state: TableRulingState,
    #[serde(skip)]
    leading_grid: TableGrid,
    leading_state: TableRulingState,
    #[serde(skip)]
    trailing_grid: TableGrid,
    trailing_state: TableRulingState,
    domain: WholeTableJoinPlan,
}

impl TableJoinHwpxPlan {
    #[must_use]
    pub const fn joined_grid(&self) -> &TableGrid {
        &self.joined_grid
    }

    #[must_use]
    pub const fn joined_state(&self) -> &TableRulingState {
        &self.joined_state
    }

    #[must_use]
    pub const fn domain(&self) -> &WholeTableJoinPlan {
        &self.domain
    }

    /// Serializes the common-lattice target states and domain plan under a finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableJoinHwpxLimits,
    ) -> Result<Vec<u8>, TableJoinHwpxError> {
        serialize_join_bounded(self, limits.partition.config().serialized_bytes)
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableJoinHwpxLimits,
    ) -> Result<[u8; 32], TableJoinHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl std::fmt::Debug for TableJoinHwpxPlan {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableJoinHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("joined_rows", &self.joined_grid.rows())
            .field("joined_columns", &self.joined_grid.columns())
            .field("domain", &self.domain)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableJoinHwpxBuilder;

impl TableJoinHwpxBuilder {
    /// Revalidates both sources and builds the common-lattice native target states.
    ///
    /// # Errors
    ///
    /// Rejects source/flow drift, formula presence, unrepresentable geometry, junction-edge loss,
    /// payload/property mismatch or finite-limit failure.
    pub fn build(
        request: &TableJoinHwpxRequest,
        source: &TableJoinHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableJoinHwpxLimits,
    ) -> Result<TableJoinHwpxPlan, TableJoinHwpxError> {
        validate_join_request_source(request, source)?;
        require_digest(current_document_flow_sha256)
            .map_err(|_| TableJoinHwpxError::InvalidBinding)?;
        if request.join.formula_policy() != TablePartitionFormulaPolicy::Reject {
            return Err(TableJoinHwpxError::UnsupportedFormulaProfile);
        }
        let domain = TablePartitionBuilder::join(
            &request.join,
            &source.leading.partition,
            &source.leading.ruling.grid,
            &source.trailing.partition,
            &source.trailing.ruling.grid,
            current_document_flow_sha256,
            limits.ruling.grid,
            limits.ruling.formula,
            limits.partition,
        )?;
        let joined_grid = join_grid_from_planned(domain.joined(), &limits)?;
        let mappings = join_column_mappings(source, domain.joined())?;
        let joined_state =
            joined_target_state(domain.joined(), &joined_grid, source, &mappings, &limits)?;
        let leading_grid = projected_grid(
            &source.leading.ruling.grid,
            &joined_grid,
            &source.leading.ruling.state,
            0,
            limits.ruling.grid,
        )?;
        let trailing_grid = projected_grid(
            &source.trailing.ruling.grid,
            &joined_grid,
            &source.trailing.ruling.state,
            source.leading.ruling.grid.rows(),
            limits.ruling.grid,
        )?;
        let leading_state = projected_state(
            &joined_state,
            &leading_grid,
            &source.leading.ruling.state,
            0,
            &limits,
        )?;
        let trailing_state = projected_state(
            &joined_state,
            &trailing_grid,
            &source.trailing.ruling.state,
            source.leading.ruling.grid.rows(),
            &limits,
        )?;
        let plan = TableJoinHwpxPlan {
            schema_version: TABLE_JOIN_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: hex(request.canonical_sha256(limits)?),
            joined_grid_sha256: hex(joined_grid.canonical_sha256()?),
            joined_grid,
            joined_state,
            leading_grid,
            leading_state,
            trailing_grid,
            trailing_state,
            domain,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableJoinHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub leading_wrapper_sha256: [u8; 32],
    pub trailing_wrapper_sha256: [u8; 32],
    pub separator_sha256: [u8; 32],
    pub joined_state_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub before_document_flow_sha256: [u8; 32],
    pub after_document_flow_sha256: [u8; 32],
    pub source_table_count: usize,
    pub target_table_count: usize,
    pub preserved_master_cell_count: usize,
    pub preserved_payload_block_count: usize,
    pub removed_table_count: usize,
    pub removed_separator_token_count: usize,
    pub removed_separator_paragraph_count: usize,
}

impl std::fmt::Debug for TableJoinHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableJoinHwpxLoweringReceipt")
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
            .field("removed_table_count", &self.removed_table_count)
            .field(
                "removed_separator_token_count",
                &self.removed_separator_token_count,
            )
            .field(
                "removed_separator_paragraph_count",
                &self.removed_separator_paragraph_count,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableJoinHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub receipt: TableJoinHwpxLoweringReceipt,
}

impl std::fmt::Debug for TableJoinHwpxLoweredParts {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableJoinHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableJoinHwpxLowerer;

impl TableJoinHwpxLowerer {
    /// Lowers an exact join and returns only after the resulting table reopens semantically.
    ///
    /// # Errors
    ///
    /// Rejects part/source/flow/request/plan drift, separator or wrapper changes, finite output
    /// failure, table-count mismatch, or complete joined-state readback mismatch.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        leading_binding: &TableRulingHwpxBinding,
        trailing_binding: &TableRulingHwpxBinding,
        current_document_flow_sha256: &str,
        request: &TableJoinHwpxRequest,
        plan: &TableJoinHwpxPlan,
        limits: TableJoinHwpxLimits,
    ) -> Result<TableJoinHwpxLoweredParts, TableJoinHwpxError> {
        let source = TableJoinHwpxReader::read_existing(
            header,
            section,
            request.leading_table_ordinal,
            request.trailing_table_ordinal,
            leading_binding,
            trailing_binding,
            limits,
        )?;
        validate_join_request_source(request, &source)?;
        let rebuilt =
            TableJoinHwpxBuilder::build(request, &source, current_document_flow_sha256, limits)?;
        if rebuilt != *plan {
            return Err(TableJoinHwpxError::PlanBindingMismatch);
        }
        let source_table_count =
            TableLayoutHwpxReader::count_in_section(section, limits.ruling.layout)?;
        let (output_header, output_section) = render_join_section(
            header,
            section,
            leading_binding,
            trailing_binding,
            request,
            &source,
            plan,
            &limits,
        )?;
        let target_table_count =
            TableLayoutHwpxReader::count_in_section(&output_section, limits.ruling.layout)?;
        if target_table_count.checked_add(1) != Some(source_table_count) {
            return Err(TableJoinHwpxError::ReadbackMismatch);
        }
        let binding = super::binding_from_state(plan.joined_state(), plan.joined_grid())?;
        let reopened = TableSplitHwpxReader::read_existing(
            &output_header,
            &output_section,
            request.leading_table_ordinal,
            &binding,
            limits,
        )?;
        if reopened.ruling.grid != *plan.joined_grid()
            || reopened.ruling.state != *plan.joined_state()
            || !partition_matches_planned(&reopened.partition, plan.domain.joined())
            || reopened.pagination.page_split != source.leading.pagination.page_split
        {
            return Err(TableJoinHwpxError::ReadbackMismatch);
        }
        let domain_receipt = plan.domain.receipt();
        let receipt = TableJoinHwpxLoweringReceipt {
            profile_id: TABLE_JOIN_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&output_header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&output_section).into(),
            leading_wrapper_sha256: source.leading.wrapper_sha256,
            trailing_wrapper_sha256: source.trailing.wrapper_sha256,
            separator_sha256: source.separator_sha256,
            joined_state_sha256: plan.joined_state.canonical_sha256(limits.ruling.ruling)?,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            before_document_flow_sha256: parse_digest(&domain_receipt.before_flow_sha256)
                .map_err(|_| TableJoinHwpxError::InvalidBinding)?,
            after_document_flow_sha256: parse_digest(&domain_receipt.after_flow_sha256)
                .map_err(|_| TableJoinHwpxError::InvalidBinding)?,
            source_table_count,
            target_table_count,
            preserved_master_cell_count: domain_receipt.preserved_master_cell_count,
            preserved_payload_block_count: source
                .leading
                .ruling
                .payload_block_count
                .checked_add(source.trailing.ruling.payload_block_count)
                .ok_or(TableJoinHwpxError::OutputLimit)?,
            removed_table_count: domain_receipt.removed_table_count,
            removed_separator_token_count: domain_receipt.removed_separator_token_count,
            removed_separator_paragraph_count: source.separator_paragraph_count,
        };
        Ok(TableJoinHwpxLoweredParts {
            header: output_header,
            section: output_section,
            binding,
            receipt,
        })
    }
}

#[derive(Debug, Error)]
pub enum TableJoinHwpxError {
    #[error("unsupported table join HWPX schema version")]
    UnsupportedVersion,
    #[error("table join HWPX input exceeds a finite bound")]
    InputLimit,
    #[error("invalid table join HWPX JSON")]
    InvalidJson,
    #[error("invalid table join HWPX binding")]
    InvalidBinding,
    #[error("table join HWPX source parts or wrappers drifted")]
    SourceBindingMismatch,
    #[error("table join HWPX separator drifted")]
    SeparatorBindingMismatch,
    #[error("table join HWPX plan drifted")]
    PlanBindingMismatch,
    #[error("formula rebasing is outside this exact native join profile")]
    UnsupportedFormulaProfile,
    #[error("selected tables are not exact top-level Hangul wrappers")]
    UnsupportedWrapper,
    #[error("selected tables are not adjacent table ordinals")]
    NonAdjacentTables,
    #[error("table join separator is not an exact whitespace-only paragraph sequence")]
    UnsupportedSeparator,
    #[error("source table pagination policies differ")]
    PaginationMismatch,
    #[error("source table junction edges cannot both be preserved")]
    JunctionEdgeMismatch,
    #[error("table join HWPX semantic readback mismatched")]
    ReadbackMismatch,
    #[error("table join HWPX allocation failed")]
    AllocationFailed,
    #[error("table join HWPX serialization failed")]
    Serialization,
    #[error("table join HWPX output exceeds a finite bound")]
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
    SplitSource(#[from] TableSplitHwpxError),
    #[error(transparent)]
    Layout(#[from] TableLayoutHwpxError),
    #[error(transparent)]
    Xml(#[from] PreservingXmlError),
}

impl TableJoinHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_join_hwpx_version",
            Self::InputLimit => "table_join_hwpx_input_limit",
            Self::InvalidJson => "table_join_hwpx_invalid_json",
            Self::InvalidBinding => "table_join_hwpx_invalid_binding",
            Self::SourceBindingMismatch => "table_join_hwpx_source_binding_mismatch",
            Self::SeparatorBindingMismatch => "table_join_hwpx_separator_binding_mismatch",
            Self::PlanBindingMismatch => "table_join_hwpx_plan_binding_mismatch",
            Self::UnsupportedFormulaProfile => "table_join_hwpx_formula_profile",
            Self::UnsupportedWrapper => "table_join_hwpx_wrapper_profile",
            Self::NonAdjacentTables => "table_join_hwpx_non_adjacent",
            Self::UnsupportedSeparator => "table_join_hwpx_separator_profile",
            Self::PaginationMismatch => "table_join_hwpx_pagination_mismatch",
            Self::JunctionEdgeMismatch => "table_join_hwpx_junction_edge_mismatch",
            Self::ReadbackMismatch => "table_join_hwpx_readback_mismatch",
            Self::AllocationFailed => "table_join_hwpx_allocation",
            Self::Serialization => "table_join_hwpx_serialization",
            Self::OutputLimit => "table_join_hwpx_output_limit",
            Self::Partition(_) => "table_join_hwpx_partition",
            Self::Grid(_) => "table_join_hwpx_grid",
            Self::ModelRuling(_) => "table_join_hwpx_model_ruling",
            Self::Ruling(_) => "table_join_hwpx_ruling",
            Self::SplitSource(_) => "table_join_hwpx_source",
            Self::Layout(_) => "table_join_hwpx_layout",
            Self::Xml(_) => "table_join_hwpx_xml",
        }
    }
}

fn validate_join_request_source(
    request: &TableJoinHwpxRequest,
    source: &TableJoinHwpxReadback,
) -> Result<(), TableJoinHwpxError> {
    if request.leading_table_ordinal != source.leading_table_ordinal
        || request.trailing_table_ordinal != source.trailing_table_ordinal
        || request.join.leading_table_id() != source.leading.partition.table_id()
        || request.join.trailing_table_id() != source.trailing.partition.table_id()
        || request.join.separator_tokens() != source.separator_tokens
        || request.expected_header_sha256 != hex(source.leading.ruling.header_sha256)
        || request.expected_section_sha256 != hex(source.leading.ruling.section_sha256)
        || request.expected_leading_wrapper_sha256 != hex(source.leading.wrapper_sha256)
        || request.expected_trailing_wrapper_sha256 != hex(source.trailing.wrapper_sha256)
        || request.expected_separator_sha256 != hex(source.separator_sha256)
    {
        return Err(TableJoinHwpxError::SourceBindingMismatch);
    }
    Ok(())
}

#[derive(Debug)]
struct SeparatorShape {
    tokens: Vec<TableJoinSeparatorToken>,
    sha256: [u8; 32],
    paragraph_count: usize,
}

fn separator_shape(
    section: &[u8],
    leading_table_ordinal: usize,
    trailing_table_ordinal: usize,
) -> Result<SeparatorShape, TableJoinHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let leading = wrapper_shape(section, leading_table_ordinal)?;
    let trailing = wrapper_shape(section, trailing_table_ordinal)?;
    if leading.outer.end() > trailing.outer.start() {
        return Err(TableJoinHwpxError::NonAdjacentTables);
    }
    let mut tokens = Vec::new();
    let mut paragraph_count = 0_usize;
    let mut current = super::element(&document, leading.paragraph)?.next_sibling();
    while let Some(index) = current {
        if index == trailing.paragraph {
            break;
        }
        let paragraph = super::element(&document, index)?;
        if paragraph.parent() != Some(document.root_element()) || !super::has_name(paragraph, "p") {
            return Err(TableJoinHwpxError::UnsupportedSeparator);
        }
        let spaces = separator_paragraph_spaces(section, &document, index)?;
        if spaces > 0 {
            tokens.push(TableJoinSeparatorToken::SpaceRun { count: spaces });
        }
        tokens.push(TableJoinSeparatorToken::ParagraphBreak);
        paragraph_count = paragraph_count
            .checked_add(1)
            .ok_or(TableJoinHwpxError::OutputLimit)?;
        current = paragraph.next_sibling();
    }
    if current != Some(trailing.paragraph) || paragraph_count == 0 {
        return Err(TableJoinHwpxError::UnsupportedSeparator);
    }
    let bytes = section
        .get(leading.outer.end()..trailing.outer.start())
        .ok_or(TableJoinHwpxError::UnsupportedSeparator)?;
    for token in document.tokens() {
        let span = token.span();
        if span.start() < leading.outer.end() || span.end() > trailing.outer.start() {
            continue;
        }
        match token.kind() {
            XmlTokenKind::Comment
            | XmlTokenKind::Reference
            | XmlTokenKind::Declaration
            | XmlTokenKind::ByteOrderMark => {
                return Err(TableJoinHwpxError::UnsupportedSeparator);
            }
            XmlTokenKind::Text => {
                let container = token
                    .element_index()
                    .ok_or(TableJoinHwpxError::UnsupportedSeparator)?;
                if !super::has_name(super::element(&document, container)?, "t") {
                    return Err(TableJoinHwpxError::UnsupportedSeparator);
                }
            }
            XmlTokenKind::StartElement
            | XmlTokenKind::EmptyElement
            | XmlTokenKind::EndElement
            | XmlTokenKind::Whitespace => {}
        }
    }
    Ok(SeparatorShape {
        tokens,
        sha256: Sha256::digest(bytes).into(),
        paragraph_count,
    })
}

fn separator_paragraph_spaces(
    section: &[u8],
    document: &PreservingXmlDocument,
    paragraph: usize,
) -> Result<u32, TableJoinHwpxError> {
    let run = only_child_named(document, paragraph, "run")?;
    let text = only_child_named(document, run, "t")?;
    if super::element(document, text)?.first_child().is_some() {
        return Err(TableJoinHwpxError::UnsupportedSeparator);
    }
    let text_outer = super::element(document, text)?
        .outer_span()
        .ok_or(TableJoinHwpxError::UnsupportedSeparator)?;
    let paragraph_outer = super::element(document, paragraph)?
        .outer_span()
        .ok_or(TableJoinHwpxError::UnsupportedSeparator)?;
    let mut spaces = 0_u32;
    for token in document.tokens() {
        let span = token.span();
        if span.start() < paragraph_outer.start() || span.end() > paragraph_outer.end() {
            continue;
        }
        if span.start() < text_outer.start() || span.end() > text_outer.end() {
            if matches!(
                token.kind(),
                XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment
            ) {
                return Err(TableJoinHwpxError::UnsupportedSeparator);
            }
            continue;
        }
        match token.kind() {
            XmlTokenKind::Text | XmlTokenKind::Whitespace => {
                let bytes = section
                    .get(span.start()..span.end())
                    .ok_or(TableJoinHwpxError::UnsupportedSeparator)?;
                if bytes.iter().any(|byte| *byte != b' ') {
                    return Err(TableJoinHwpxError::UnsupportedSeparator);
                }
                spaces = spaces
                    .checked_add(
                        u32::try_from(bytes.len()).map_err(|_| TableJoinHwpxError::OutputLimit)?,
                    )
                    .ok_or(TableJoinHwpxError::OutputLimit)?;
            }
            XmlTokenKind::Reference | XmlTokenKind::Comment => {
                return Err(TableJoinHwpxError::UnsupportedSeparator);
            }
            _ => {}
        }
    }
    Ok(spaces)
}

fn only_child_named(
    document: &PreservingXmlDocument,
    parent: usize,
    name: &str,
) -> Result<usize, TableJoinHwpxError> {
    let child = super::element(document, parent)?
        .first_child()
        .ok_or(TableJoinHwpxError::UnsupportedSeparator)?;
    if super::element(document, child)?.next_sibling().is_some()
        || !super::has_name(super::element(document, child)?, name)
    {
        return Err(TableJoinHwpxError::UnsupportedSeparator);
    }
    Ok(child)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct JoinFraction {
    numerator: u64,
    denominator: u64,
}

impl Ord for JoinFraction {
    fn cmp(&self, other: &Self) -> Ordering {
        (u128::from(self.numerator) * u128::from(other.denominator))
            .cmp(&(u128::from(other.numerator) * u128::from(self.denominator)))
    }
}

impl PartialOrd for JoinFraction {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug)]
struct JoinColumnMappings {
    leading: Vec<u32>,
    trailing: Vec<u32>,
}

fn join_column_mappings(
    source: &TableJoinHwpxReadback,
    planned: &PlannedWholeTable,
) -> Result<JoinColumnMappings, TableJoinHwpxError> {
    let mut lattice = normalized_boundaries(&source.leading.partition)?;
    lattice.extend(normalized_boundaries(&source.trailing.partition)?);
    lattice.sort_unstable();
    lattice.dedup();
    if lattice.len().checked_sub(1) != Some(planned.columns() as usize) {
        return Err(TableJoinHwpxError::PlanBindingMismatch);
    }
    Ok(JoinColumnMappings {
        leading: mapping_for_state(&source.leading.partition, &lattice)?,
        trailing: mapping_for_state(&source.trailing.partition, &lattice)?,
    })
}

fn normalized_boundaries(
    state: &TablePartitionState,
) -> Result<Vec<JoinFraction>, TableJoinHwpxError> {
    let mut output = Vec::new();
    output
        .try_reserve_exact(state.column_widths_hwpunit().len() + 1)
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    output.push(JoinFraction {
        numerator: 0,
        denominator: 1,
    });
    let total = u64::from(state.table_width_hwpunit());
    let mut cumulative = 0_u64;
    for width in state.column_widths_hwpunit() {
        cumulative = cumulative
            .checked_add(u64::from(*width))
            .ok_or(TableJoinHwpxError::PlanBindingMismatch)?;
        let divisor = join_gcd(cumulative, total);
        output.push(JoinFraction {
            numerator: cumulative / divisor,
            denominator: total / divisor,
        });
    }
    Ok(output)
}

fn mapping_for_state(
    state: &TablePartitionState,
    lattice: &[JoinFraction],
) -> Result<Vec<u32>, TableJoinHwpxError> {
    let source = normalized_boundaries(state)?;
    let mut output = Vec::new();
    output
        .try_reserve_exact(source.len())
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    for boundary in source {
        let index = lattice
            .binary_search(&boundary)
            .map_err(|_| TableJoinHwpxError::PlanBindingMismatch)?;
        output.push(u32::try_from(index).map_err(|_| TableJoinHwpxError::OutputLimit)?);
    }
    Ok(output)
}

fn join_gcd(mut left: u64, mut right: u64) -> u64 {
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    left
}

fn join_grid_from_planned(
    planned: &PlannedWholeTable,
    limits: &TableJoinHwpxLimits,
) -> Result<TableGrid, TableJoinHwpxError> {
    let grid = TableGrid::new(
        planned.rows(),
        planned.columns(),
        planned.master_cells().to_vec(),
        limits.ruling.grid,
    )?;
    if planned.grid_sha256() != hex(grid.canonical_sha256()?) {
        return Err(TableJoinHwpxError::PlanBindingMismatch);
    }
    Ok(grid)
}

fn joined_target_state(
    planned: &PlannedWholeTable,
    grid: &TableGrid,
    source: &TableJoinHwpxReadback,
    mappings: &JoinColumnMappings,
    limits: &TableJoinHwpxLimits,
) -> Result<TableRulingState, TableJoinHwpxError> {
    if planned.table_properties_sha256() != source.leading.ruling.state.table_properties_sha256()
        || planned.cells().len() != grid.master_cell_count()
    {
        return Err(TableJoinHwpxError::PlanBindingMismatch);
    }
    let row_boundaries = joined_row_boundaries(source)?;
    let column_boundaries = cumulative_boundaries(planned.column_widths_hwpunit())?;
    if column_boundaries.last().copied() != Some(planned.table_width_hwpunit()) {
        return Err(TableJoinHwpxError::PlanBindingMismatch);
    }
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(planned.cells().len())
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    let leading_rows = source.leading.ruling.grid.rows();
    for planned_cell in planned.cells() {
        let (source_cell, expected_row, mapping) = if let Some(cell) = source
            .leading
            .ruling
            .state
            .cell(planned_cell.master_cell_id())
        {
            (cell, cell.coordinate().row, &mappings.leading)
        } else if let Some(cell) = source
            .trailing
            .ruling
            .state
            .cell(planned_cell.master_cell_id())
        {
            (
                cell,
                cell.coordinate()
                    .row
                    .checked_add(leading_rows)
                    .ok_or(TableJoinHwpxError::PlanBindingMismatch)?,
                &mappings.trailing,
            )
        } else {
            return Err(TableJoinHwpxError::SourceBindingMismatch);
        };
        let mapped_column = *mapping
            .get(
                usize::try_from(source_cell.coordinate().column)
                    .map_err(|_| TableJoinHwpxError::PlanBindingMismatch)?,
            )
            .ok_or(TableJoinHwpxError::PlanBindingMismatch)?;
        if planned_cell.coordinate()
            != (CellCoordinate {
                row: expected_row,
                column: mapped_column,
            })
            || planned_cell.payload_sha256() != value_digest(source_cell.payload(), limits)?
            || planned_cell.cell_properties_sha256()
                != value_digest(source_cell.properties(), limits)?
            || planned_cell.formula().is_some()
            || source_cell.formula().is_some()
        {
            return Err(TableJoinHwpxError::PlanBindingMismatch);
        }
        cells.push(TableRulingCellDraft {
            master_cell_id: planned_cell.master_cell_id().clone(),
            coordinate: planned_cell.coordinate(),
            payload: source_cell.payload().to_vec(),
            properties: source_cell.properties().clone(),
            formula: None,
        });
    }
    let edges = joined_edges(source, mappings, planned.columns())?;
    let source_frame = source.leading.ruling.state.frame();
    let height_hwpunit = *row_boundaries
        .last()
        .ok_or(TableJoinHwpxError::PlanBindingMismatch)?;
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: planned.table_id().clone(),
            frame: TableRulingFrame {
                left_hwpunit: source_frame.left_hwpunit,
                top_hwpunit: source_frame.top_hwpunit,
                width_hwpunit: planned.table_width_hwpunit(),
                height_hwpunit,
            },
            grid_sha256: hex(grid.canonical_sha256()?),
            table_properties_sha256: planned.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: row_boundaries,
            column_boundaries_hwpunit: column_boundaries,
            edges,
            cells,
        },
        grid,
        limits.ruling.formula,
        limits.ruling.ruling,
    )?)
}

fn joined_row_boundaries(source: &TableJoinHwpxReadback) -> Result<Vec<u32>, TableJoinHwpxError> {
    let leading = source.leading.ruling.state.row_boundaries_hwpunit();
    let trailing = source.trailing.ruling.state.row_boundaries_hwpunit();
    let base = *leading
        .last()
        .ok_or(TableJoinHwpxError::PlanBindingMismatch)?;
    let trailing_base = *trailing
        .first()
        .ok_or(TableJoinHwpxError::PlanBindingMismatch)?;
    let mut output = leading.to_vec();
    output
        .try_reserve(trailing.len().saturating_sub(1))
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    for value in trailing.iter().skip(1) {
        output.push(
            base.checked_add(
                value
                    .checked_sub(trailing_base)
                    .ok_or(TableJoinHwpxError::PlanBindingMismatch)?,
            )
            .ok_or(TableJoinHwpxError::OutputLimit)?,
        );
    }
    Ok(output)
}

fn cumulative_boundaries(widths: &[u32]) -> Result<Vec<u32>, TableJoinHwpxError> {
    let mut output = Vec::new();
    output
        .try_reserve_exact(widths.len() + 1)
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    output.push(0);
    let mut cumulative = 0_u32;
    for width in widths {
        cumulative = cumulative
            .checked_add(*width)
            .ok_or(TableJoinHwpxError::OutputLimit)?;
        output.push(cumulative);
    }
    Ok(output)
}

fn joined_edges(
    source: &TableJoinHwpxReadback,
    mappings: &JoinColumnMappings,
    columns: u32,
) -> Result<Vec<TableRulingEdge>, TableJoinHwpxError> {
    let leading_rows = source.leading.ruling.grid.rows();
    let trailing_rows = source.trailing.ruling.grid.rows();
    let rows = leading_rows
        .checked_add(trailing_rows)
        .ok_or(TableJoinHwpxError::OutputLimit)?;
    let capacity = usize::try_from(rows)
        .ok()
        .and_then(|rows| rows.checked_add(1))
        .and_then(|rows| rows.checked_mul(columns as usize))
        .and_then(|horizontal| {
            usize::try_from(columns)
                .ok()
                .and_then(|columns| columns.checked_add(1))
                .and_then(|columns| columns.checked_mul(rows as usize))
                .and_then(|vertical| horizontal.checked_add(vertical))
        })
        .ok_or(TableJoinHwpxError::AllocationFailed)?;
    let mut output = Vec::new();
    output
        .try_reserve_exact(capacity)
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    for boundary in 0..=rows {
        for offset in 0..columns {
            let line_sha256 = match boundary.cmp(&leading_rows) {
                Ordering::Less => mapped_horizontal_line(
                    &source.leading.ruling.state,
                    &mappings.leading,
                    boundary,
                    offset,
                )?,
                Ordering::Equal => {
                    let leading = mapped_horizontal_line(
                        &source.leading.ruling.state,
                        &mappings.leading,
                        leading_rows,
                        offset,
                    )?;
                    let trailing = mapped_horizontal_line(
                        &source.trailing.ruling.state,
                        &mappings.trailing,
                        0,
                        offset,
                    )?;
                    if leading != trailing {
                        return Err(TableJoinHwpxError::JunctionEdgeMismatch);
                    }
                    leading
                }
                Ordering::Greater => mapped_horizontal_line(
                    &source.trailing.ruling.state,
                    &mappings.trailing,
                    boundary - leading_rows,
                    offset,
                )?,
            };
            output.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256,
            });
        }
    }
    for boundary in 0..=columns {
        for offset in 0..rows {
            let (state, mapping, source_offset) = if offset < leading_rows {
                (&source.leading.ruling.state, &mappings.leading, offset)
            } else {
                (
                    &source.trailing.ruling.state,
                    &mappings.trailing,
                    offset - leading_rows,
                )
            };
            output.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256: mapped_vertical_line(state, mapping, boundary, source_offset)?,
            });
        }
    }
    Ok(output)
}

fn mapped_horizontal_line(
    state: &TableRulingState,
    mapping: &[u32],
    boundary: u32,
    target_offset: u32,
) -> Result<Option<String>, TableJoinHwpxError> {
    let source_offset = mapping
        .windows(2)
        .position(|pair| pair[0] <= target_offset && target_offset < pair[1])
        .ok_or(TableJoinHwpxError::PlanBindingMismatch)?;
    Ok(state
        .edge(
            TableRulingAxis::Horizontal,
            boundary,
            u32::try_from(source_offset).map_err(|_| TableJoinHwpxError::OutputLimit)?,
        )
        .ok_or(TableJoinHwpxError::SourceBindingMismatch)?
        .line_sha256
        .clone())
}

fn mapped_vertical_line(
    state: &TableRulingState,
    mapping: &[u32],
    target_boundary: u32,
    source_offset: u32,
) -> Result<Option<String>, TableJoinHwpxError> {
    let Some(source_boundary) = mapping
        .iter()
        .position(|boundary| *boundary == target_boundary)
    else {
        return Ok(None);
    };
    Ok(state
        .edge(
            TableRulingAxis::Vertical,
            u32::try_from(source_boundary).map_err(|_| TableJoinHwpxError::OutputLimit)?,
            source_offset,
        )
        .ok_or(TableJoinHwpxError::SourceBindingMismatch)?
        .line_sha256
        .clone())
}

fn projected_grid(
    source_grid: &TableGrid,
    joined_grid: &TableGrid,
    source_state: &TableRulingState,
    row_offset: u32,
    limits: domain_ir::TableGridLimits,
) -> Result<TableGrid, TableJoinHwpxError> {
    let mut spans = Vec::new();
    spans
        .try_reserve_exact(source_grid.master_cell_count())
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    for span in joined_grid.master_cells() {
        if source_state.cell(&span.master_cell_id).is_some() {
            spans.push(domain_ir::TableCellSpan {
                master_cell_id: span.master_cell_id.clone(),
                row: span
                    .row
                    .checked_sub(row_offset)
                    .ok_or(TableJoinHwpxError::PlanBindingMismatch)?,
                column: span.column,
                row_span: span.row_span,
                column_span: span.column_span,
            });
        }
    }
    if spans.len() != source_grid.master_cell_count() {
        return Err(TableJoinHwpxError::PlanBindingMismatch);
    }
    Ok(TableGrid::new(
        source_grid.rows(),
        joined_grid.columns(),
        spans,
        limits,
    )?)
}

fn projected_state(
    joined: &TableRulingState,
    projected_grid: &TableGrid,
    source: &TableRulingState,
    row_offset: u32,
    limits: &TableJoinHwpxLimits,
) -> Result<TableRulingState, TableJoinHwpxError> {
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(source.cells().len())
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    for cell in joined.cells() {
        if source.cell(cell.master_cell_id()).is_some() {
            cells.push(TableRulingCellDraft {
                master_cell_id: cell.master_cell_id().clone(),
                coordinate: CellCoordinate {
                    row: cell
                        .coordinate()
                        .row
                        .checked_sub(row_offset)
                        .ok_or(TableJoinHwpxError::PlanBindingMismatch)?,
                    column: cell.coordinate().column,
                },
                payload: cell.payload().to_vec(),
                properties: cell.properties().clone(),
                formula: None,
            });
        }
    }
    if cells.len() != source.cells().len() {
        return Err(TableJoinHwpxError::PlanBindingMismatch);
    }
    let rows = projected_grid.rows();
    let columns = projected_grid.columns();
    let mut edges = Vec::new();
    let capacity = usize::try_from(rows)
        .ok()
        .and_then(|rows| rows.checked_add(1))
        .and_then(|rows| rows.checked_mul(columns as usize))
        .and_then(|horizontal| {
            usize::try_from(columns)
                .ok()
                .and_then(|columns| columns.checked_add(1))
                .and_then(|columns| columns.checked_mul(rows as usize))
                .and_then(|vertical| horizontal.checked_add(vertical))
        })
        .ok_or(TableJoinHwpxError::AllocationFailed)?;
    edges
        .try_reserve_exact(capacity)
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    for boundary in 0..=rows {
        for offset in 0..columns {
            let joined_boundary = boundary
                .checked_add(row_offset)
                .ok_or(TableJoinHwpxError::PlanBindingMismatch)?;
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256: joined
                    .edge(TableRulingAxis::Horizontal, joined_boundary, offset)
                    .ok_or(TableJoinHwpxError::PlanBindingMismatch)?
                    .line_sha256
                    .clone(),
            });
        }
    }
    for boundary in 0..=columns {
        for offset in 0..rows {
            let joined_offset = offset
                .checked_add(row_offset)
                .ok_or(TableJoinHwpxError::PlanBindingMismatch)?;
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256: joined
                    .edge(TableRulingAxis::Vertical, boundary, joined_offset)
                    .ok_or(TableJoinHwpxError::PlanBindingMismatch)?
                    .line_sha256
                    .clone(),
            });
        }
    }
    let source_frame = source.frame();
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: source.table_id().clone(),
            frame: TableRulingFrame {
                left_hwpunit: source_frame.left_hwpunit,
                top_hwpunit: source_frame.top_hwpunit,
                width_hwpunit: joined.frame().width_hwpunit,
                height_hwpunit: source_frame.height_hwpunit,
            },
            grid_sha256: hex(projected_grid.canonical_sha256()?),
            table_properties_sha256: source.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: source.row_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: joined.column_boundaries_hwpunit().to_vec(),
            edges,
            cells,
        },
        projected_grid,
        limits.ruling.formula,
        limits.ruling.ruling,
    )?)
}

#[allow(clippy::too_many_arguments)]
fn render_join_section(
    header: &[u8],
    section: &[u8],
    leading_binding: &TableRulingHwpxBinding,
    trailing_binding: &TableRulingHwpxBinding,
    request: &TableJoinHwpxRequest,
    source: &TableJoinHwpxReadback,
    plan: &TableJoinHwpxPlan,
    limits: &TableJoinHwpxLimits,
) -> Result<(Vec<u8>, Vec<u8>), TableJoinHwpxError> {
    let rendered = render_projected_sources(
        header,
        section,
        leading_binding,
        trailing_binding,
        request,
        source,
        plan,
        limits,
    )?;
    let mut rows = table_rows_bytes(
        &rendered.section,
        request.leading_table_ordinal,
        limits.ruling.layout.config().output_bytes,
    )?;
    let trailing_rows = table_rows_bytes(
        &rendered.section,
        request.trailing_table_ordinal,
        limits.ruling.layout.config().output_bytes,
    )?;
    append_join_bounded(
        &mut rows,
        &trailing_rows,
        limits.ruling.layout.config().output_bytes,
    )?;
    let document = PreservingXmlDocument::parse(&rendered.section)?;
    let leading_root = super::selected_table(&document, request.leading_table_ordinal)?;
    let combined = super::patch_table(
        &rendered.section,
        &document,
        leading_root,
        &plan.joined_state,
        &plan.joined_grid,
        rows,
        limits.ruling.layout.config().output_bytes,
    )?;
    let combined = patch_joined_cell_topology(
        &combined,
        request.leading_table_ordinal,
        &plan.joined_grid,
        limits.ruling.layout.config().output_bytes,
    )?;
    let current_separator = separator_shape(
        &combined,
        request.leading_table_ordinal,
        request.trailing_table_ordinal,
    )?;
    if current_separator.sha256 != source.separator_sha256
        || current_separator.tokens != source.separator_tokens
    {
        return Err(TableJoinHwpxError::SeparatorBindingMismatch);
    }
    let leading_wrapper = wrapper_shape(&combined, request.leading_table_ordinal)?;
    let trailing_wrapper = wrapper_shape(&combined, request.trailing_table_ordinal)?;
    let retained = combined
        .get(leading_wrapper.outer.start()..leading_wrapper.outer.end())
        .ok_or(TableJoinHwpxError::UnsupportedWrapper)?
        .to_vec();
    let output = replace_bounded(
        &combined,
        leading_wrapper.outer.start(),
        trailing_wrapper.outer.end(),
        &retained,
        limits,
    )?;
    Ok((rendered.header, output))
}

#[allow(clippy::too_many_arguments)]
fn render_projected_sources(
    header: &[u8],
    section: &[u8],
    leading_binding: &TableRulingHwpxBinding,
    trailing_binding: &TableRulingHwpxBinding,
    request: &TableJoinHwpxRequest,
    source: &TableJoinHwpxReadback,
    plan: &TableJoinHwpxPlan,
    limits: &TableJoinHwpxLimits,
) -> Result<super::RenderedParts, TableJoinHwpxError> {
    let leading = super::render_partition_existing(
        header,
        section,
        request.leading_table_ordinal,
        leading_binding,
        &source.leading.ruling.state,
        &plan.leading_state,
        &plan.leading_grid,
        &limits.ruling,
    )?;
    let trailing = super::render_partition_existing(
        &leading.header,
        &leading.section,
        request.trailing_table_ordinal,
        trailing_binding,
        &source.trailing.ruling.state,
        &plan.trailing_state,
        &plan.trailing_grid,
        &limits.ruling,
    )?;
    let leading_projected_binding =
        super::binding_from_state(&plan.leading_state, &plan.leading_grid)?;
    let trailing_projected_binding =
        super::binding_from_state(&plan.trailing_state, &plan.trailing_grid)?;
    let reopened_leading = TableRulingHwpxReader::read_existing(
        &trailing.header,
        &trailing.section,
        request.leading_table_ordinal,
        &leading_projected_binding,
        limits.ruling,
    )?;
    let reopened_trailing = TableRulingHwpxReader::read_existing(
        &trailing.header,
        &trailing.section,
        request.trailing_table_ordinal,
        &trailing_projected_binding,
        limits.ruling,
    )?;
    if reopened_leading.grid != plan.leading_grid
        || reopened_leading.state != plan.leading_state
        || reopened_trailing.grid != plan.trailing_grid
        || reopened_trailing.state != plan.trailing_state
    {
        return Err(TableJoinHwpxError::ReadbackMismatch);
    }
    Ok(trailing)
}

fn patch_joined_cell_topology(
    section: &[u8],
    table_ordinal: usize,
    grid: &TableGrid,
    maximum: usize,
) -> Result<Vec<u8>, TableJoinHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let root = super::selected_table(&document, table_ordinal)?;
    let rows = super::direct_children_named(&document, root, "tr")?;
    if rows.len() != grid.rows() as usize {
        return Err(TableJoinHwpxError::ReadbackMismatch);
    }
    let mut edits = Vec::new();
    for (row_index, row) in rows.into_iter().enumerate() {
        let cells = super::direct_children_named(&document, row, "tc")?;
        let target = grid
            .master_cells()
            .iter()
            .filter(|span| span.row as usize == row_index)
            .collect::<Vec<_>>();
        if cells.len() != target.len() {
            return Err(TableJoinHwpxError::ReadbackMismatch);
        }
        for (cell, span) in cells.into_iter().zip(target) {
            let address = super::unique_child(&document, cell, "cellAddr")?;
            let cell_span = super::unique_child(&document, cell, "cellSpan")?;
            super::push_attribute_edit(&document, address, "rowAddr", span.row, &mut edits)?;
            super::push_attribute_edit(&document, address, "colAddr", span.column, &mut edits)?;
            super::push_attribute_edit(&document, cell_span, "rowSpan", span.row_span, &mut edits)?;
            super::push_attribute_edit(
                &document,
                cell_span,
                "colSpan",
                span.column_span,
                &mut edits,
            )?;
        }
    }
    Ok(super::apply_edits(section, &mut edits, maximum)?)
}

fn table_rows_bytes(
    section: &[u8],
    table_ordinal: usize,
    maximum: usize,
) -> Result<Vec<u8>, TableJoinHwpxError> {
    let document = PreservingXmlDocument::parse(section)?;
    let root = super::selected_table(&document, table_ordinal)?;
    let mut child = super::element(&document, root)?.first_child();
    let mut output = Vec::new();
    let mut count = 0_usize;
    while let Some(index) = child {
        let element = super::element(&document, index)?;
        if super::has_name(element, "tr") {
            let span = element
                .outer_span()
                .ok_or(TableJoinHwpxError::UnsupportedWrapper)?;
            let bytes = section
                .get(span.start()..span.end())
                .ok_or(TableJoinHwpxError::UnsupportedWrapper)?;
            append_join_bounded(&mut output, bytes, maximum)?;
            count = count
                .checked_add(1)
                .ok_or(TableJoinHwpxError::OutputLimit)?;
        }
        child = element.next_sibling();
    }
    if count == 0 {
        return Err(TableJoinHwpxError::UnsupportedWrapper);
    }
    Ok(output)
}

fn append_join_bounded(
    output: &mut Vec<u8>,
    value: &[u8],
    maximum: usize,
) -> Result<(), TableJoinHwpxError> {
    let length = output
        .len()
        .checked_add(value.len())
        .ok_or(TableJoinHwpxError::OutputLimit)?;
    if length > maximum {
        return Err(TableJoinHwpxError::OutputLimit);
    }
    output
        .try_reserve(value.len())
        .map_err(|_| TableJoinHwpxError::AllocationFailed)?;
    output.extend_from_slice(value);
    Ok(())
}

fn serialize_join_bounded<T: Serialize + ?Sized>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableJoinHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableJoinHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableJoinHwpxError::OutputLimit);
    }
    Ok(bytes)
}
