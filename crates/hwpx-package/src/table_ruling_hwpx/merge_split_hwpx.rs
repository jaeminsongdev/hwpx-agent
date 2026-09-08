use std::collections::{BTreeMap, BTreeSet};

use domain_ir::{
    CellCoordinate, ContentPreservationPolicy, FormulaAstDraft, FormulaCell, FormulaCellDraft,
    LogicalId, TABLE_FORMULA_SCHEMA_VERSION, TABLE_RULING_SCHEMA_VERSION, TableCellContent,
    TableGrid, TableGridError, TableMergeSplitError, TableMergeSplitKind, TableMergeSplitResult,
    TableRulingAxis, TableRulingCellDraft, TableRulingCellProperties, TableRulingEdge,
    TableRulingError, TableRulingState, TableRulingStateDraft, TableSplitRequest,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::*;

pub const TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-merge-split-hwpx/v1";
pub const TABLE_MERGE_SPLIT_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-merge-split-hwpx.hancom-2020/1";

const SPLIT_CAPABILITY_ID: &str = "table.split_cell";
const MERGE_CAPABILITY_ID: &str = "table.merge_cells";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableMergeSplitHwpxLimits {
    pub ruling: TableRulingHwpxLimits,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TableMergeSplitHwpxOperation {
    Merge {
        selected_slots: Vec<CellCoordinate>,
        content_policy: ContentPreservationPolicy,
    },
    Split {
        master_cell_id: LogicalId,
        rows: u32,
        columns: u32,
        new_master_cell_ids: Vec<LogicalId>,
        content_policy: ContentPreservationPolicy,
        split_line_sha256: String,
    },
}

impl TableMergeSplitHwpxOperation {
    const fn capability_id(&self) -> &'static str {
        match self {
            Self::Merge { .. } => MERGE_CAPABILITY_ID,
            Self::Split { .. } => SPLIT_CAPABILITY_ID,
        }
    }
}

impl std::fmt::Debug for TableMergeSplitHwpxOperation {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Merge {
                selected_slots,
                content_policy,
            } => formatter
                .debug_struct("Merge")
                .field("selected_slot_count", &selected_slots.len())
                .field("content_policy", content_policy)
                .finish(),
            Self::Split {
                rows,
                columns,
                new_master_cell_ids,
                content_policy,
                ..
            } => formatter
                .debug_struct("Split")
                .field("master_cell_id", &"<redacted>")
                .field("rows", rows)
                .field("columns", columns)
                .field("new_master_cell_count", &new_master_cell_ids.len())
                .field("content_policy", content_policy)
                .field("split_line_sha256", &"<redacted>")
                .finish(),
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct TableMergeSplitHwpxRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub expected_state_sha256: String,
    pub expected_grid_sha256: String,
    pub expected_content_sha256: String,
    pub expected_document_flow_sha256: String,
    pub operation: TableMergeSplitHwpxOperation,
}

impl std::fmt::Debug for TableMergeSplitHwpxRequestDraft {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableMergeSplitHwpxRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("expected_state_sha256", &"<redacted>")
            .field("expected_grid_sha256", &"<redacted>")
            .field("expected_content_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("operation", &self.operation)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableMergeSplitHwpxRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    expected_state_sha256: String,
    expected_grid_sha256: String,
    expected_content_sha256: String,
    expected_document_flow_sha256: String,
    operation: TableMergeSplitHwpxOperation,
}

impl TableMergeSplitHwpxRequest {
    /// Validates an exact source binding and the complete merge/split operation before planning.
    ///
    /// # Errors
    ///
    /// Rejects version, digest, source, flow, operation, property, formula, content or limit drift.
    pub fn from_draft(
        draft: TableMergeSplitHwpxRequestDraft,
        source: &TableMergeSplitHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<Self, TableMergeSplitHwpxError> {
        if draft.schema_version != TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION {
            return Err(TableMergeSplitHwpxError::UnsupportedVersion);
        }
        for value in [
            &draft.expected_state_sha256,
            &draft.expected_grid_sha256,
            &draft.expected_content_sha256,
            &draft.expected_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(value)?;
        }
        if let TableMergeSplitHwpxOperation::Split {
            split_line_sha256, ..
        } = &draft.operation
        {
            require_digest(split_line_sha256)?;
        }
        let mut operation = draft.operation;
        if let TableMergeSplitHwpxOperation::Merge { selected_slots, .. } = &mut operation {
            selected_slots.sort_unstable();
        }
        let request = Self {
            schema_version: TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION,
            capability_id: operation.capability_id(),
            table_id: draft.table_id,
            expected_state_sha256: draft.expected_state_sha256,
            expected_grid_sha256: draft.expected_grid_sha256,
            expected_content_sha256: draft.expected_content_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            operation,
        };
        validate_request_source(&request, source, current_document_flow_sha256, &limits)?;
        let _ = TableMergeSplitHwpxBuilder::build(
            &request,
            source,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies the same exact source validation as `from_draft`.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        source: &TableMergeSplitHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<Self, TableMergeSplitHwpxError> {
        if bytes.is_empty() || bytes.len() > limits.ruling.ruling.config().input_bytes {
            return Err(TableMergeSplitHwpxError::InputLimit);
        }
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableMergeSplitHwpxError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn operation(&self) -> &TableMergeSplitHwpxOperation {
        &self.operation
    }

    /// Serializes the exact request under the configured ruling output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or finite output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<Vec<u8>, TableMergeSplitHwpxError> {
        serialize_bounded(self, limits.ruling.ruling.config().serialized_bytes)
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<[u8; 32], TableMergeSplitHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl std::fmt::Debug for TableMergeSplitHwpxRequest {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableMergeSplitHwpxRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("expected_state_sha256", &"<redacted>")
            .field("expected_grid_sha256", &"<redacted>")
            .field("expected_content_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("operation", &self.operation)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableMergeSplitHwpxReadback {
    pub profile_id: &'static str,
    pub ruling: TableRulingHwpxReadback,
    pub content: domain_ir::TableContentState,
    pub content_state_sha256: [u8; 32],
}

impl std::fmt::Debug for TableMergeSplitHwpxReadback {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableMergeSplitHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("rows", &self.ruling.grid.rows())
            .field("columns", &self.ruling.grid.columns())
            .field("master_cell_count", &self.ruling.grid.master_cell_count())
            .field("payload_block_count", &self.ruling.payload_block_count)
            .field("formula_count", &self.ruling.formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableMergeSplitHwpxReader;

impl TableMergeSplitHwpxReader {
    /// Reads one exact table into complete ruling, grid, content, formula and cache state.
    ///
    /// # Errors
    ///
    /// Propagates strict ruling/package admission and exact content-ownership validation.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<TableMergeSplitHwpxReadback, TableMergeSplitHwpxError> {
        let ruling = TableRulingHwpxReader::read_existing(
            header,
            section,
            table_ordinal,
            binding,
            limits.ruling,
        )?;
        let content = content_from_ruling(&ruling.grid, &ruling.state, limits.ruling.grid)?;
        let content_state_sha256 = content_state_sha256(&content);
        Ok(TableMergeSplitHwpxReadback {
            profile_id: TABLE_MERGE_SPLIT_HWPX_PROFILE_ID,
            ruling,
            content,
            content_state_sha256,
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableMergeSplitHwpxPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    domain_receipt_sha256: String,
    target_grid_sha256: String,
    target_content_sha256: String,
    target_state_sha256: String,
    #[serde(skip)]
    target_grid: TableGrid,
    target_state: TableRulingState,
    discarded_content_block_count: usize,
}

impl TableMergeSplitHwpxPlan {
    #[must_use]
    pub const fn target_grid(&self) -> &TableGrid {
        &self.target_grid
    }

    #[must_use]
    pub const fn target_state(&self) -> &TableRulingState {
        &self.target_state
    }

    #[must_use]
    pub const fn discarded_content_block_count(&self) -> usize {
        self.discarded_content_block_count
    }

    /// Serializes the complete target grid/state plan under the configured finite bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<Vec<u8>, TableMergeSplitHwpxError> {
        serialize_bounded(self, limits.ruling.ruling.config().serialized_bytes)
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<[u8; 32], TableMergeSplitHwpxError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl std::fmt::Debug for TableMergeSplitHwpxPlan {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableMergeSplitHwpxPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("target_rows", &self.target_grid.rows())
            .field("target_columns", &self.target_grid.columns())
            .field(
                "target_master_cell_count",
                &self.target_grid.master_cell_count(),
            )
            .field(
                "discarded_content_block_count",
                &self.discarded_content_block_count,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableMergeSplitHwpxBuilder;

impl TableMergeSplitHwpxBuilder {
    /// Revalidates the request against current source state and builds an exact target state.
    ///
    /// # Errors
    ///
    /// Rejects source/flow drift, invalid domain semantics, unpreservable selected properties or
    /// formulas, target-state inconsistency and finite serialization failure.
    pub fn build(
        request: &TableMergeSplitHwpxRequest,
        source: &TableMergeSplitHwpxReadback,
        current_document_flow_sha256: &str,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<TableMergeSplitHwpxPlan, TableMergeSplitHwpxError> {
        validate_request_source(request, source, current_document_flow_sha256, &limits)?;
        let result = build_domain_result(request.operation(), source, &limits)?;
        validate_direct_profile(request.operation(), source, &result)?;
        let target_state = build_target_state(source, &result, request.operation(), &limits)?;
        let domain_receipt = result
            .receipt()
            .canonical_json_with_max_bytes(limits.ruling.ruling.config().serialized_bytes)?;
        let plan = TableMergeSplitHwpxPlan {
            schema_version: TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: hex(request.canonical_sha256(limits)?),
            domain_receipt_sha256: hex(Sha256::digest(domain_receipt)),
            target_grid_sha256: hex(result.grid().canonical_sha256()?),
            target_content_sha256: hex(content_state_sha256(result.content())),
            target_state_sha256: hex(target_state.canonical_sha256(limits.ruling.ruling)?),
            target_grid: result.grid().clone(),
            target_state,
            discarded_content_block_count: result.receipt().discarded_content_block_ids().len(),
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableMergeSplitHwpxPartBinding {
    pub header_sha256: String,
    pub section_sha256: String,
    pub document_flow_sha256: String,
    pub source_state_sha256: String,
    pub source_grid_sha256: String,
    pub source_content_sha256: String,
    pub request_sha256: String,
    pub plan_sha256: String,
}

impl TableMergeSplitHwpxPartBinding {
    /// Binds request-time parts, flow, source state/grid/content, request and complete plan.
    ///
    /// # Errors
    ///
    /// Rejects malformed flow identity, source mismatch or rebuilt-plan drift.
    pub fn from_readback(
        source: &TableMergeSplitHwpxReadback,
        request: &TableMergeSplitHwpxRequest,
        plan: &TableMergeSplitHwpxPlan,
        document_flow_sha256: String,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<Self, TableMergeSplitHwpxError> {
        require_digest(&document_flow_sha256)?;
        validate_request_source(request, source, &document_flow_sha256, &limits)?;
        let rebuilt =
            TableMergeSplitHwpxBuilder::build(request, source, &document_flow_sha256, limits)?;
        if rebuilt != *plan {
            return Err(TableMergeSplitHwpxError::PlanBindingMismatch);
        }
        Ok(Self {
            header_sha256: hex(source.ruling.header_sha256),
            section_sha256: hex(source.ruling.section_sha256),
            document_flow_sha256,
            source_state_sha256: hex(source.ruling.state.canonical_sha256(limits.ruling.ruling)?),
            source_grid_sha256: hex(source.ruling.grid.canonical_sha256()?),
            source_content_sha256: hex(source.content_state_sha256),
            request_sha256: hex(request.canonical_sha256(limits)?),
            plan_sha256: hex(plan.canonical_sha256(limits)?),
        })
    }
}

impl std::fmt::Debug for TableMergeSplitHwpxPartBinding {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableMergeSplitHwpxPartBinding")
            .field("header_sha256", &"<redacted>")
            .field("section_sha256", &"<redacted>")
            .field("document_flow_sha256", &"<redacted>")
            .field("source_state_sha256", &"<redacted>")
            .field("source_grid_sha256", &"<redacted>")
            .field("source_content_sha256", &"<redacted>")
            .field("request_sha256", &"<redacted>")
            .field("plan_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableMergeSplitHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub source_grid_sha256: [u8; 32],
    pub target_grid_sha256: [u8; 32],
    pub source_content_sha256: [u8; 32],
    pub target_content_sha256: [u8; 32],
    pub request_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub document_flow_sha256: [u8; 32],
    pub added_border_fill_count: usize,
    pub source_payload_block_count: usize,
    pub target_payload_block_count: usize,
    pub preserved_formula_count: usize,
    pub discarded_content_block_count: usize,
}

impl std::fmt::Debug for TableMergeSplitHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableMergeSplitHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("added_border_fill_count", &self.added_border_fill_count)
            .field(
                "source_payload_block_count",
                &self.source_payload_block_count,
            )
            .field(
                "target_payload_block_count",
                &self.target_payload_block_count,
            )
            .field("preserved_formula_count", &self.preserved_formula_count)
            .field(
                "discarded_content_block_count",
                &self.discarded_content_block_count,
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableMergeSplitHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub receipt: TableMergeSplitHwpxLoweringReceipt,
}

impl std::fmt::Debug for TableMergeSplitHwpxLoweredParts {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableMergeSplitHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableMergeSplitHwpxLowerer;

impl TableMergeSplitHwpxLowerer {
    /// Lowers one exact merge/split plan and returns only after semantic reopen matches the target.
    ///
    /// # Errors
    ///
    /// Rejects any part/source/flow/request/plan drift, unsupported native style or selected formula,
    /// finite output failure, or exact target readback mismatch.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        part_binding: &TableMergeSplitHwpxPartBinding,
        current_document_flow_sha256: &str,
        request: &TableMergeSplitHwpxRequest,
        plan: &TableMergeSplitHwpxPlan,
        limits: TableMergeSplitHwpxLimits,
    ) -> Result<TableMergeSplitHwpxLoweredParts, TableMergeSplitHwpxError> {
        validate_part_binding(
            header,
            section,
            part_binding,
            current_document_flow_sha256,
            request,
            plan,
            &limits,
        )?;
        let source = TableMergeSplitHwpxReader::read_existing(
            header,
            section,
            table_ordinal,
            binding,
            limits,
        )?;
        validate_request_source(request, &source, current_document_flow_sha256, &limits)?;
        let rebuilt = TableMergeSplitHwpxBuilder::build(
            request,
            &source,
            current_document_flow_sha256,
            limits,
        )?;
        if rebuilt != *plan {
            return Err(TableMergeSplitHwpxError::PlanBindingMismatch);
        }
        let rendered = super::render_existing(
            header,
            section,
            table_ordinal,
            binding,
            &source.ruling.state,
            plan.target_state(),
            plan.target_grid(),
            true,
            &limits.ruling,
        )?;
        let target_binding = super::binding_from_state(plan.target_state(), plan.target_grid())?;
        let reopened = TableMergeSplitHwpxReader::read_existing(
            &rendered.header,
            &rendered.section,
            table_ordinal,
            &target_binding,
            limits,
        )?;
        if reopened.ruling.grid != *plan.target_grid()
            || reopened.ruling.state != *plan.target_state()
            || hex(reopened.content_state_sha256) != plan.target_content_sha256
        {
            return Err(TableMergeSplitHwpxError::ReadbackMismatch);
        }
        let receipt = TableMergeSplitHwpxLoweringReceipt {
            profile_id: TABLE_MERGE_SPLIT_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&rendered.header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&rendered.section).into(),
            source_state_sha256: source.ruling.state.canonical_sha256(limits.ruling.ruling)?,
            target_state_sha256: plan.target_state().canonical_sha256(limits.ruling.ruling)?,
            source_grid_sha256: source.ruling.grid.canonical_sha256()?,
            target_grid_sha256: plan.target_grid().canonical_sha256()?,
            source_content_sha256: source.content_state_sha256,
            target_content_sha256: reopened.content_state_sha256,
            request_sha256: request.canonical_sha256(limits)?,
            plan_sha256: plan.canonical_sha256(limits)?,
            document_flow_sha256: parse_digest(current_document_flow_sha256)?,
            added_border_fill_count: rendered.added_border_fill_count,
            source_payload_block_count: source.ruling.payload_block_count,
            target_payload_block_count: reopened.ruling.payload_block_count,
            preserved_formula_count: reopened.ruling.formula_count,
            discarded_content_block_count: plan.discarded_content_block_count,
        };
        Ok(TableMergeSplitHwpxLoweredParts {
            header: rendered.header,
            section: rendered.section,
            binding: target_binding,
            receipt,
        })
    }
}

#[derive(Debug, Error)]
pub enum TableMergeSplitHwpxError {
    #[error("table merge/split HWPX schema version is unsupported")]
    UnsupportedVersion,
    #[error("table merge/split HWPX input is empty or oversized")]
    InputLimit,
    #[error("table merge/split HWPX JSON is invalid")]
    InvalidJson,
    #[error("table merge/split HWPX digest or binding is invalid")]
    InvalidBinding,
    #[error("table merge/split HWPX source state, grid or content drifted")]
    SourceStateMismatch,
    #[error("table merge/split HWPX document flow drifted")]
    FlowBindingMismatch,
    #[error("table merge/split HWPX package part binding drifted")]
    PartBindingMismatch,
    #[error("table merge/split HWPX rebuilt plan differs from the bound plan")]
    PlanBindingMismatch,
    #[error("table merge/split HWPX selected cell properties cannot be losslessly combined")]
    UnsupportedSelectedProperties,
    #[error("table merge/split HWPX selected formula mutation is outside the reviewed profile")]
    UnsupportedSelectedFormula,
    #[error("table merge/split HWPX selected diagonal mutation is outside the reviewed profile")]
    UnsupportedSelectedDiagonal,
    #[error("table merge/split HWPX split line is absent from the bound edge-line catalog")]
    UnsupportedSplitLine,
    #[error("table merge/split HWPX semantic reopen differs from the target")]
    ReadbackMismatch,
    #[error("table merge/split HWPX allocation failed")]
    AllocationFailed,
    #[error("table merge/split HWPX serialization failed")]
    Serialization,
    #[error("table merge/split HWPX output exceeded its finite bound")]
    OutputLimit,
    #[error("table merge/split domain plan failed")]
    Domain(#[from] TableMergeSplitError),
    #[error("table merge/split grid admission failed")]
    Grid(#[from] TableGridError),
    #[error("table merge/split ruling state failed")]
    Ruling(#[from] TableRulingError),
    #[error("table merge/split HWPX ruling adapter failed")]
    Hwpx(#[from] TableRulingHwpxError),
}

impl TableMergeSplitHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::UnsupportedVersion => "table_merge_split_hwpx_unsupported_version",
            Self::InputLimit => "table_merge_split_hwpx_input_limit",
            Self::InvalidJson => "table_merge_split_hwpx_invalid_json",
            Self::InvalidBinding => "table_merge_split_hwpx_invalid_binding",
            Self::SourceStateMismatch => "table_merge_split_hwpx_source_state_mismatch",
            Self::FlowBindingMismatch => "table_merge_split_hwpx_flow_binding_mismatch",
            Self::PartBindingMismatch => "table_merge_split_hwpx_part_binding_mismatch",
            Self::PlanBindingMismatch => "table_merge_split_hwpx_plan_binding_mismatch",
            Self::UnsupportedSelectedProperties => {
                "table_merge_split_hwpx_unsupported_selected_properties"
            }
            Self::UnsupportedSelectedFormula => {
                "table_merge_split_hwpx_unsupported_selected_formula"
            }
            Self::UnsupportedSelectedDiagonal => {
                "table_merge_split_hwpx_unsupported_selected_diagonal"
            }
            Self::UnsupportedSplitLine => "table_merge_split_hwpx_unsupported_split_line",
            Self::ReadbackMismatch => "table_merge_split_hwpx_readback_mismatch",
            Self::AllocationFailed => "table_merge_split_hwpx_allocation",
            Self::Serialization => "table_merge_split_hwpx_serialization",
            Self::OutputLimit => "table_merge_split_hwpx_output_limit",
            Self::Domain(_) => "table_merge_split_hwpx_domain",
            Self::Grid(_) => "table_merge_split_hwpx_grid",
            Self::Ruling(_) => "table_merge_split_hwpx_ruling",
            Self::Hwpx(_) => "table_merge_split_hwpx_adapter",
        }
    }
}

fn validate_request_source(
    request: &TableMergeSplitHwpxRequest,
    source: &TableMergeSplitHwpxReadback,
    current_document_flow_sha256: &str,
    limits: &TableMergeSplitHwpxLimits,
) -> Result<(), TableMergeSplitHwpxError> {
    require_digest(current_document_flow_sha256)?;
    if request.table_id != *source.ruling.state.table_id()
        || request.expected_state_sha256
            != hex(source.ruling.state.canonical_sha256(limits.ruling.ruling)?)
        || request.expected_grid_sha256 != hex(source.ruling.grid.canonical_sha256()?)
        || request.expected_content_sha256 != hex(source.content_state_sha256)
    {
        return Err(TableMergeSplitHwpxError::SourceStateMismatch);
    }
    if request.expected_document_flow_sha256 != current_document_flow_sha256 {
        return Err(TableMergeSplitHwpxError::FlowBindingMismatch);
    }
    if request.capability_id != request.operation.capability_id() {
        return Err(TableMergeSplitHwpxError::InvalidBinding);
    }
    Ok(())
}

fn validate_part_binding(
    header: &[u8],
    section: &[u8],
    binding: &TableMergeSplitHwpxPartBinding,
    current_document_flow_sha256: &str,
    request: &TableMergeSplitHwpxRequest,
    plan: &TableMergeSplitHwpxPlan,
    limits: &TableMergeSplitHwpxLimits,
) -> Result<(), TableMergeSplitHwpxError> {
    for value in [
        &binding.header_sha256,
        &binding.section_sha256,
        &binding.document_flow_sha256,
        &binding.source_state_sha256,
        &binding.source_grid_sha256,
        &binding.source_content_sha256,
        &binding.request_sha256,
        &binding.plan_sha256,
        current_document_flow_sha256,
    ] {
        require_digest(value)?;
    }
    if binding.header_sha256 != hex(Sha256::digest(header))
        || binding.section_sha256 != hex(Sha256::digest(section))
        || binding.document_flow_sha256 != current_document_flow_sha256
        || binding.request_sha256 != hex(request.canonical_sha256(*limits)?)
        || binding.plan_sha256 != hex(plan.canonical_sha256(*limits)?)
        || request.expected_state_sha256 != binding.source_state_sha256
        || request.expected_grid_sha256 != binding.source_grid_sha256
        || request.expected_content_sha256 != binding.source_content_sha256
    {
        return Err(TableMergeSplitHwpxError::PartBindingMismatch);
    }
    Ok(())
}

fn build_domain_result(
    operation: &TableMergeSplitHwpxOperation,
    source: &TableMergeSplitHwpxReadback,
    limits: &TableMergeSplitHwpxLimits,
) -> Result<TableMergeSplitResult, TableMergeSplitHwpxError> {
    match operation {
        TableMergeSplitHwpxOperation::Merge {
            selected_slots,
            content_policy,
        } => Ok(source.ruling.grid.merge_cells(
            selected_slots.clone(),
            &source.content,
            *content_policy,
            limits.ruling.grid,
        )?),
        TableMergeSplitHwpxOperation::Split {
            master_cell_id,
            rows,
            columns,
            new_master_cell_ids,
            content_policy,
            ..
        } => Ok(source.ruling.grid.split_cell(
            TableSplitRequest::new(
                master_cell_id.clone(),
                *rows,
                *columns,
                new_master_cell_ids.clone(),
                *content_policy,
            ),
            &source.content,
            limits.ruling.grid,
        )?),
    }
}

fn validate_direct_profile(
    operation: &TableMergeSplitHwpxOperation,
    source: &TableMergeSplitHwpxReadback,
    result: &TableMergeSplitResult,
) -> Result<(), TableMergeSplitHwpxError> {
    if let TableMergeSplitHwpxOperation::Split {
        split_line_sha256, ..
    } = operation
        && !source
            .ruling
            .style_catalog
            .edge_line_sha256
            .iter()
            .any(|value| value == split_line_sha256)
    {
        return Err(TableMergeSplitHwpxError::UnsupportedSplitLine);
    }
    let receipt = result.receipt();
    let mut affected = BTreeSet::new();
    affected.insert(receipt.preserved_master_cell_id().clone());
    affected.extend(receipt.retired_master_cell_ids().iter().cloned());
    let mut selected_properties: Option<&TableRulingCellProperties> = None;
    for identifier in &affected {
        let cell = source
            .ruling
            .state
            .cell(identifier)
            .ok_or(TableMergeSplitHwpxError::SourceStateMismatch)?;
        if cell.formula().is_some() {
            return Err(TableMergeSplitHwpxError::UnsupportedSelectedFormula);
        }
        if cell.properties().slash_diagonal_sha256.is_some()
            || cell.properties().back_slash_diagonal_sha256.is_some()
        {
            return Err(TableMergeSplitHwpxError::UnsupportedSelectedDiagonal);
        }
        if receipt.operation() == TableMergeSplitKind::Merge {
            if selected_properties.is_some_and(|value| value != cell.properties()) {
                return Err(TableMergeSplitHwpxError::UnsupportedSelectedProperties);
            }
            selected_properties = Some(cell.properties());
        }
    }
    if matches!(operation, TableMergeSplitHwpxOperation::Merge { .. })
        != (receipt.operation() == TableMergeSplitKind::Merge)
    {
        return Err(TableMergeSplitHwpxError::PlanBindingMismatch);
    }
    Ok(())
}

fn build_target_state(
    source: &TableMergeSplitHwpxReadback,
    result: &TableMergeSplitResult,
    operation: &TableMergeSplitHwpxOperation,
    limits: &TableMergeSplitHwpxLimits,
) -> Result<TableRulingState, TableMergeSplitHwpxError> {
    let edges = build_target_edges(
        &source.ruling.grid,
        result.grid(),
        source.ruling.state.edges(),
        operation,
    )?;
    let mut payloads = BTreeMap::new();
    for cell in source.ruling.state.cells() {
        for block in cell.payload() {
            if payloads.insert(block.block_id.clone(), block).is_some() {
                return Err(TableMergeSplitHwpxError::InvalidBinding);
            }
        }
    }
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(result.grid().master_cell_count())
        .map_err(|_| TableMergeSplitHwpxError::AllocationFailed)?;
    for span in result.grid().master_cells() {
        let source_cell = source
            .ruling
            .state
            .cell(&span.master_cell_id)
            .or_else(|| {
                source
                    .ruling
                    .grid
                    .master_cell_at(CellCoordinate {
                        row: span.row,
                        column: span.column,
                    })
                    .ok()
                    .and_then(|owner| source.ruling.state.cell(&owner.master_cell_id))
            })
            .ok_or(TableMergeSplitHwpxError::SourceStateMismatch)?;
        let content = result
            .content()
            .cell(&span.master_cell_id)
            .ok_or(TableMergeSplitHwpxError::PlanBindingMismatch)?;
        let mut target_payload = Vec::new();
        target_payload
            .try_reserve_exact(content.content_block_ids().len())
            .map_err(|_| TableMergeSplitHwpxError::AllocationFailed)?;
        for identifier in content.content_block_ids() {
            target_payload.push(
                (*payloads
                    .get(identifier)
                    .ok_or(TableMergeSplitHwpxError::PlanBindingMismatch)?)
                .clone(),
            );
        }
        let formula = (source_cell.master_cell_id() == &span.master_cell_id)
            .then(|| source_cell.formula().map(formula_draft))
            .flatten();
        cells.push(TableRulingCellDraft {
            master_cell_id: span.master_cell_id.clone(),
            coordinate: CellCoordinate {
                row: span.row,
                column: span.column,
            },
            payload: target_payload,
            properties: source_cell.properties().clone(),
            formula,
        });
    }
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: source.ruling.state.table_id().clone(),
            frame: source.ruling.state.frame(),
            grid_sha256: hex(result.grid().canonical_sha256()?),
            table_properties_sha256: source.ruling.state.table_properties_sha256().to_owned(),
            row_boundaries_hwpunit: source.ruling.state.row_boundaries_hwpunit().to_vec(),
            column_boundaries_hwpunit: source.ruling.state.column_boundaries_hwpunit().to_vec(),
            edges,
            cells,
        },
        result.grid(),
        limits.ruling.formula,
        limits.ruling.ruling,
    )?)
}

fn build_target_edges(
    source_grid: &TableGrid,
    target_grid: &TableGrid,
    source_edges: &[TableRulingEdge],
    operation: &TableMergeSplitHwpxOperation,
) -> Result<Vec<TableRulingEdge>, TableMergeSplitHwpxError> {
    let split_line_sha256 = match operation {
        TableMergeSplitHwpxOperation::Split {
            split_line_sha256, ..
        } => Some(split_line_sha256.as_str()),
        TableMergeSplitHwpxOperation::Merge { .. } => None,
    };
    let mut output = Vec::new();
    output
        .try_reserve_exact(source_edges.len())
        .map_err(|_| TableMergeSplitHwpxError::AllocationFailed)?;
    for edge in source_edges {
        let before = adjacent_owners(source_grid, edge)?;
        let after = adjacent_owners(target_grid, edge)?;
        let mut target = edge.clone();
        if let (Some((before_left, before_right)), Some((after_left, after_right))) =
            (before, after)
        {
            let before_same = before_left == before_right;
            let after_same = after_left == after_right;
            match (before_same, after_same) {
                (false, true) => {
                    if split_line_sha256.is_some() {
                        return Err(TableMergeSplitHwpxError::PlanBindingMismatch);
                    }
                    target.line_sha256 = None;
                }
                (true, false) => {
                    target.line_sha256 = Some(
                        split_line_sha256
                            .ok_or(TableMergeSplitHwpxError::PlanBindingMismatch)?
                            .to_owned(),
                    );
                }
                _ => {}
            }
        }
        output.push(target);
    }
    Ok(output)
}

fn adjacent_owners(
    grid: &TableGrid,
    edge: &TableRulingEdge,
) -> Result<Option<(LogicalId, LogicalId)>, TableMergeSplitHwpxError> {
    let (left, right) = match edge.axis {
        TableRulingAxis::Horizontal if edge.boundary > 0 && edge.boundary < grid.rows() => (
            CellCoordinate {
                row: edge.boundary - 1,
                column: edge.offset,
            },
            CellCoordinate {
                row: edge.boundary,
                column: edge.offset,
            },
        ),
        TableRulingAxis::Vertical if edge.boundary > 0 && edge.boundary < grid.columns() => (
            CellCoordinate {
                row: edge.offset,
                column: edge.boundary - 1,
            },
            CellCoordinate {
                row: edge.offset,
                column: edge.boundary,
            },
        ),
        _ => return Ok(None),
    };
    Ok(Some((
        grid.master_cell_at(left)?.master_cell_id.clone(),
        grid.master_cell_at(right)?.master_cell_id.clone(),
    )))
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

fn content_from_ruling(
    grid: &TableGrid,
    state: &TableRulingState,
    limits: domain_ir::TableGridLimits,
) -> Result<domain_ir::TableContentState, TableMergeSplitHwpxError> {
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(state.cells().len())
        .map_err(|_| TableMergeSplitHwpxError::AllocationFailed)?;
    for cell in state.cells() {
        cells.push(TableCellContent::new(
            cell.master_cell_id().clone(),
            cell.payload()
                .iter()
                .map(|block| block.block_id.clone())
                .collect(),
        ));
    }
    Ok(domain_ir::TableContentState::new(grid, cells, limits)?)
}

fn content_state_sha256(value: &domain_ir::TableContentState) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-merge-split-hwpx-content/v1\0");
    hash_part(&mut digest, value.grid_sha256());
    hash_part(
        &mut digest,
        &u64::try_from(value.cells().len())
            .unwrap_or(u64::MAX)
            .to_be_bytes(),
    );
    for cell in value.cells() {
        hash_part(&mut digest, cell.master_cell_id().as_str().as_bytes());
        hash_part(
            &mut digest,
            &u64::try_from(cell.content_block_ids().len())
                .unwrap_or(u64::MAX)
                .to_be_bytes(),
        );
        for identifier in cell.content_block_ids() {
            hash_part(&mut digest, identifier.as_str().as_bytes());
        }
    }
    digest.finalize().into()
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableMergeSplitHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableMergeSplitHwpxError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableMergeSplitHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn require_digest(value: &str) -> Result<(), TableMergeSplitHwpxError> {
    if value.len() != 64
        || !value
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
    {
        return Err(TableMergeSplitHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableMergeSplitHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, slot) in output.iter_mut().enumerate() {
        let offset = index * 2;
        *slot = u8::from_str_radix(&value[offset..offset + 2], 16)
            .map_err(|_| TableMergeSplitHwpxError::InvalidBinding)?;
    }
    Ok(output)
}

fn hash_part(digest: &mut Sha256, value: &[u8]) {
    digest.update(u64::try_from(value.len()).unwrap_or(u64::MAX).to_be_bytes());
    digest.update(value);
}

fn hex(value: impl AsRef<[u8]>) -> String {
    let bytes = value.as_ref();
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(output, "{byte:02x}");
    }
    output
}
