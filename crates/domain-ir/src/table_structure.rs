use std::collections::BTreeSet;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    FormulaCache, FormulaCachePolicy, FormulaCell, FormulaError, FormulaGridDimensions,
    FormulaGridEdit, FormulaLimits, LogicalId, TableGrid, TableGridError, TableGridLimits,
    TableOperationError, TableOperationReceipt, TableRulingAxis, TableRulingCell, TableRulingEdge,
    TableRulingError, TableRulingLimits, TableRulingState, TableRulingStateDraft,
};

pub const TABLE_STRUCTURE_SCHEMA_VERSION: &str = "hwpx-agent.table-structure/v1";
pub const TABLE_INSERT_ROWS_CAPABILITY_ID: &str = "table.insert_rows";
pub const TABLE_INSERT_COLUMNS_CAPABILITY_ID: &str = "table.insert_columns";
pub const TABLE_DELETE_ROWS_CAPABILITY_ID: &str = "table.delete_rows";
pub const TABLE_DELETE_COLUMNS_CAPABILITY_ID: &str = "table.delete_columns";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableStructureLimitConfig {
    pub input_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for TableStructureLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 32 * 1024 * 1024,
            serialized_bytes: 128 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableStructureLimits {
    config: TableStructureLimitConfig,
    pub grid: TableGridLimits,
    pub formula: FormulaLimits,
    pub ruling: TableRulingLimits,
}

impl TableStructureLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates one finite structural-transition limit bundle.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling or internally inconsistent byte bounds.
    pub fn new(
        config: TableStructureLimitConfig,
        grid: TableGridLimits,
        formula: FormulaLimits,
        ruling: TableRulingLimits,
    ) -> Result<Self, TableStructureError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TableStructureError::InvalidLimit);
        }
        Ok(Self {
            config,
            grid,
            formula,
            ruling,
        })
    }

    #[must_use]
    pub const fn config(self) -> TableStructureLimitConfig {
        self.config
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableStructureOperation {
    InsertRows,
    InsertColumns,
    DeleteRows,
    DeleteColumns,
}

impl TableStructureOperation {
    #[must_use]
    pub const fn capability_id(self) -> &'static str {
        match self {
            Self::InsertRows => TABLE_INSERT_ROWS_CAPABILITY_ID,
            Self::InsertColumns => TABLE_INSERT_COLUMNS_CAPABILITY_ID,
            Self::DeleteRows => TABLE_DELETE_ROWS_CAPABILITY_ID,
            Self::DeleteColumns => TABLE_DELETE_COLUMNS_CAPABILITY_ID,
        }
    }

    const fn axis(self) -> StructureAxis {
        match self {
            Self::InsertRows | Self::DeleteRows => StructureAxis::Rows,
            Self::InsertColumns | Self::DeleteColumns => StructureAxis::Columns,
        }
    }

    const fn kind(self) -> StructureKind {
        match self {
            Self::InsertRows | Self::InsertColumns => StructureKind::Insert,
            Self::DeleteRows | Self::DeleteColumns => StructureKind::Delete,
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct TableStructureRequestDraft {
    pub schema_version: String,
    pub operation: TableStructureOperation,
    pub index: u32,
    pub count: u32,
    pub new_master_cell_ids: Vec<LogicalId>,
    pub expected_source_state_sha256: String,
    pub expected_source_grid_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub target_state: TableRulingStateDraft,
}

impl fmt::Debug for TableStructureRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("operation", &self.operation)
            .field("index", &self.index)
            .field("count", &self.count)
            .field("new_master_cell_count", &self.new_master_cell_ids.len())
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_source_grid_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .field("target_state", &self.target_state)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStructureRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    operation: TableStructureOperation,
    index: u32,
    count: u32,
    new_master_cell_ids: Vec<LogicalId>,
    expected_source_state_sha256: String,
    expected_source_grid_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    target_state: TableRulingState,
    #[serde(skip)]
    target_grid: TableGrid,
}

impl TableStructureRequest {
    /// Admits one complete structural transition against an exact source state, grid and flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, digest, grid-operation, geometry, cell, formula, cache, edge or limit drift.
    pub fn from_draft(
        draft: TableStructureRequestDraft,
        source_state: &TableRulingState,
        source_grid: &TableGrid,
        current_document_flow_sha256: &str,
        limits: TableStructureLimits,
    ) -> Result<Self, TableStructureError> {
        if draft.schema_version != TABLE_STRUCTURE_SCHEMA_VERSION {
            return Err(TableStructureError::UnsupportedVersion);
        }
        for digest in [
            &draft.expected_source_state_sha256,
            &draft.expected_source_grid_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        let (target_grid, operation_receipt) = apply_grid_operation(
            source_grid,
            draft.operation,
            draft.index,
            draft.count,
            draft.new_master_cell_ids.clone(),
            limits.grid,
        )?;
        let target_state = TableRulingState::from_draft(
            draft.target_state,
            &target_grid,
            limits.formula,
            limits.ruling,
        )?;
        let request = Self {
            schema_version: TABLE_STRUCTURE_SCHEMA_VERSION,
            capability_id: draft.operation.capability_id(),
            operation: draft.operation,
            index: draft.index,
            count: draft.count,
            new_master_cell_ids: draft.new_master_cell_ids,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_source_grid_sha256: draft.expected_source_grid_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            target_state,
            target_grid,
        };
        validate_source_binding(
            &request,
            source_state,
            source_grid,
            current_document_flow_sha256,
            limits,
        )?;
        let _ = validate_transition(
            source_state,
            source_grid,
            &request.target_state,
            &request.target_grid,
            request.edit(source_grid)?,
            &operation_receipt,
            limits,
        )?;
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and applies the same exact transition admission.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate, unknown or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        source_state: &TableRulingState,
        source_grid: &TableGrid,
        current_document_flow_sha256: &str,
        limits: TableStructureLimits,
    ) -> Result<Self, TableStructureError> {
        if bytes.is_empty() || bytes.len() > limits.config.input_bytes {
            return Err(TableStructureError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableStructureError::InvalidJson)?;
        Self::from_draft(
            draft,
            source_state,
            source_grid,
            current_document_flow_sha256,
            limits,
        )
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn operation(&self) -> TableStructureOperation {
        self.operation
    }

    #[must_use]
    pub const fn index(&self) -> u32 {
        self.index
    }

    #[must_use]
    pub const fn count(&self) -> u32 {
        self.count
    }

    #[must_use]
    pub fn new_master_cell_ids(&self) -> &[LogicalId] {
        &self.new_master_cell_ids
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
    pub fn expected_document_flow_sha256(&self) -> &str {
        &self.expected_document_flow_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }

    /// Serializes the complete typed request under its finite output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableStructureLimits,
    ) -> Result<Vec<u8>, TableStructureError> {
        serialize_bounded(self, limits)
    }

    /// Hashes the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableStructureLimits,
    ) -> Result<[u8; 32], TableStructureError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    fn edit(&self, source_grid: &TableGrid) -> Result<EditSpec, TableStructureError> {
        EditSpec::new(self.operation, self.index, self.count, source_grid)
    }
}

impl fmt::Debug for TableStructureRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("operation", &self.operation)
            .field("index", &self.index)
            .field("count", &self.count)
            .field("new_master_cell_count", &self.new_master_cell_ids.len())
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_source_grid_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("target_document_flow_sha256", &"<redacted>")
            .field("target_state", &self.target_state)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStructureReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    operation: TableStructureOperation,
    index: u32,
    count: u32,
    before_state_sha256: String,
    after_state_sha256: String,
    before_grid_sha256: String,
    after_grid_sha256: String,
    before_document_flow_sha256: String,
    after_document_flow_sha256: String,
    preserved_master_cell_count: usize,
    inserted_master_cell_count: usize,
    deleted_master_cell_count: usize,
    preserved_edge_count: usize,
    introduced_edge_count: usize,
    removed_edge_count: usize,
    formula_rebased_count: usize,
    formula_cache_cleared_count: usize,
    formula_cache_updated_count: usize,
    formula_deleted_count: usize,
}

impl TableStructureReceipt {
    #[must_use]
    pub const fn operation(&self) -> TableStructureOperation {
        self.operation
    }

    #[must_use]
    pub const fn preserved_master_cell_count(&self) -> usize {
        self.preserved_master_cell_count
    }

    #[must_use]
    pub const fn inserted_master_cell_count(&self) -> usize {
        self.inserted_master_cell_count
    }

    #[must_use]
    pub const fn deleted_master_cell_count(&self) -> usize {
        self.deleted_master_cell_count
    }

    #[must_use]
    pub const fn preserved_edge_count(&self) -> usize {
        self.preserved_edge_count
    }

    #[must_use]
    pub const fn introduced_edge_count(&self) -> usize {
        self.introduced_edge_count
    }

    #[must_use]
    pub const fn removed_edge_count(&self) -> usize {
        self.removed_edge_count
    }

    #[must_use]
    pub const fn formula_rebased_count(&self) -> usize {
        self.formula_rebased_count
    }

    #[must_use]
    pub const fn formula_cache_cleared_count(&self) -> usize {
        self.formula_cache_cleared_count
    }

    #[must_use]
    pub const fn formula_cache_updated_count(&self) -> usize {
        self.formula_cache_updated_count
    }

    #[must_use]
    pub const fn formula_deleted_count(&self) -> usize {
        self.formula_deleted_count
    }
}

impl fmt::Debug for TableStructureReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructureReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("operation", &self.operation)
            .field("index", &self.index)
            .field("count", &self.count)
            .field(
                "preserved_master_cell_count",
                &self.preserved_master_cell_count,
            )
            .field(
                "inserted_master_cell_count",
                &self.inserted_master_cell_count,
            )
            .field("deleted_master_cell_count", &self.deleted_master_cell_count)
            .field("preserved_edge_count", &self.preserved_edge_count)
            .field("introduced_edge_count", &self.introduced_edge_count)
            .field("removed_edge_count", &self.removed_edge_count)
            .field("formula_rebased_count", &self.formula_rebased_count)
            .field(
                "formula_cache_cleared_count",
                &self.formula_cache_cleared_count,
            )
            .field(
                "formula_cache_updated_count",
                &self.formula_cache_updated_count,
            )
            .field("formula_deleted_count", &self.formula_deleted_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableStructurePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_sha256: String,
    before_state: TableRulingState,
    after_state: TableRulingState,
    #[serde(skip)]
    before_grid: TableGrid,
    #[serde(skip)]
    after_grid: TableGrid,
    operation_receipt: TableOperationReceipt,
    receipt: TableStructureReceipt,
}

impl TableStructurePlan {
    #[must_use]
    pub const fn before_state(&self) -> &TableRulingState {
        &self.before_state
    }

    #[must_use]
    pub const fn after_state(&self) -> &TableRulingState {
        &self.after_state
    }

    #[must_use]
    pub const fn before_grid(&self) -> &TableGrid {
        &self.before_grid
    }

    #[must_use]
    pub const fn after_grid(&self) -> &TableGrid {
        &self.after_grid
    }

    #[must_use]
    pub const fn operation_receipt(&self) -> &TableOperationReceipt {
        &self.operation_receipt
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableStructureReceipt {
        &self.receipt
    }

    /// Serializes the complete transition and receipts under the configured bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: TableStructureLimits,
    ) -> Result<Vec<u8>, TableStructureError> {
        serialize_bounded(self, limits)
    }

    /// Hashes the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failure.
    pub fn canonical_sha256(
        &self,
        limits: TableStructureLimits,
    ) -> Result<[u8; 32], TableStructureError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableStructurePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableStructurePlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("before_dimensions", &grid_dimensions(&self.before_grid))
            .field("after_dimensions", &grid_dimensions(&self.after_grid))
            .field("operation_receipt", &self.operation_receipt)
            .field("receipt", &self.receipt)
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct TableStructureBuilder;

impl TableStructureBuilder {
    /// Revalidates the exact source and constructs one complete structural transition plan.
    ///
    /// # Errors
    ///
    /// Rejects source/flow drift or any grid, geometry, cell, formula, cache and edge mismatch.
    pub fn build(
        request: &TableStructureRequest,
        source_state: &TableRulingState,
        source_grid: &TableGrid,
        current_document_flow_sha256: &str,
        limits: TableStructureLimits,
    ) -> Result<TableStructurePlan, TableStructureError> {
        validate_source_binding(
            request,
            source_state,
            source_grid,
            current_document_flow_sha256,
            limits,
        )?;
        let (target_grid, operation_receipt) = apply_grid_operation(
            source_grid,
            request.operation,
            request.index,
            request.count,
            request.new_master_cell_ids.clone(),
            limits.grid,
        )?;
        if target_grid != request.target_grid {
            return Err(TableStructureError::TargetGridMismatch);
        }
        let counts = validate_transition(
            source_state,
            source_grid,
            &request.target_state,
            &target_grid,
            request.edit(source_grid)?,
            &operation_receipt,
            limits,
        )?;
        let receipt = TableStructureReceipt {
            schema_version: TABLE_STRUCTURE_SCHEMA_VERSION,
            capability_id: request.capability_id,
            operation: request.operation,
            index: request.index,
            count: request.count,
            before_state_sha256: hex(source_state.canonical_sha256(limits.ruling)?),
            after_state_sha256: hex(request.target_state.canonical_sha256(limits.ruling)?),
            before_grid_sha256: hex(source_grid.canonical_sha256()?),
            after_grid_sha256: hex(target_grid.canonical_sha256()?),
            before_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            after_document_flow_sha256: request.target_document_flow_sha256.clone(),
            preserved_master_cell_count: operation_receipt.preserved_master_cells().len(),
            inserted_master_cell_count: operation_receipt.inserted_master_cell_ids().len(),
            deleted_master_cell_count: operation_receipt.deleted_master_cell_ids().len(),
            preserved_edge_count: counts.preserved_edges,
            introduced_edge_count: counts.introduced_edges,
            removed_edge_count: counts.removed_edges,
            formula_rebased_count: counts.formulas_rebased,
            formula_cache_cleared_count: counts.formula_caches_cleared,
            formula_cache_updated_count: counts.formula_caches_updated,
            formula_deleted_count: counts.formulas_deleted,
        };
        let plan = TableStructurePlan {
            schema_version: TABLE_STRUCTURE_SCHEMA_VERSION,
            capability_id: request.capability_id,
            request_sha256: hex(request.canonical_sha256(limits)?),
            before_state: source_state.clone(),
            after_state: request.target_state.clone(),
            before_grid: source_grid.clone(),
            after_grid: target_grid,
            operation_receipt,
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum StructureAxis {
    Rows,
    Columns,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum StructureKind {
    Insert,
    Delete,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct EditSpec {
    operation: TableStructureOperation,
    axis: StructureAxis,
    kind: StructureKind,
    index: u32,
    count: u32,
    dimension: u32,
    before: FormulaGridDimensions,
}

impl EditSpec {
    fn new(
        operation: TableStructureOperation,
        index: u32,
        count: u32,
        source_grid: &TableGrid,
    ) -> Result<Self, TableStructureError> {
        let dimension = match operation.axis() {
            StructureAxis::Rows => source_grid.rows(),
            StructureAxis::Columns => source_grid.columns(),
        };
        if count == 0 {
            return Err(TableOperationError::ZeroCount.into());
        }
        Ok(Self {
            operation,
            axis: operation.axis(),
            kind: operation.kind(),
            index,
            count,
            dimension,
            before: grid_dimensions(source_grid),
        })
    }

    const fn formula_edit(self) -> FormulaGridEdit {
        match self.operation {
            TableStructureOperation::InsertRows => FormulaGridEdit::InsertRows {
                before: self.before,
                index: self.index,
                count: self.count,
            },
            TableStructureOperation::InsertColumns => FormulaGridEdit::InsertColumns {
                before: self.before,
                index: self.index,
                count: self.count,
            },
            TableStructureOperation::DeleteRows => FormulaGridEdit::DeleteRows {
                before: self.before,
                index: self.index,
                count: self.count,
            },
            TableStructureOperation::DeleteColumns => FormulaGridEdit::DeleteColumns {
                before: self.before,
                index: self.index,
                count: self.count,
            },
        }
    }
}

#[derive(Default)]
struct TransitionCounts {
    preserved_edges: usize,
    introduced_edges: usize,
    removed_edges: usize,
    formulas_rebased: usize,
    formula_caches_cleared: usize,
    formula_caches_updated: usize,
    formulas_deleted: usize,
}

fn apply_grid_operation(
    source_grid: &TableGrid,
    operation: TableStructureOperation,
    index: u32,
    count: u32,
    new_master_cell_ids: Vec<LogicalId>,
    limits: TableGridLimits,
) -> Result<(TableGrid, TableOperationReceipt), TableStructureError> {
    let result = match operation {
        TableStructureOperation::InsertRows => {
            source_grid.insert_rows(index, count, new_master_cell_ids, limits)?
        }
        TableStructureOperation::InsertColumns => {
            source_grid.insert_columns(index, count, new_master_cell_ids, limits)?
        }
        TableStructureOperation::DeleteRows => {
            if !new_master_cell_ids.is_empty() {
                return Err(TableStructureError::UnexpectedNewMasterCells);
            }
            source_grid.delete_rows(index, count, limits)?
        }
        TableStructureOperation::DeleteColumns => {
            if !new_master_cell_ids.is_empty() {
                return Err(TableStructureError::UnexpectedNewMasterCells);
            }
            source_grid.delete_columns(index, count, limits)?
        }
    };
    Ok(result.into_parts())
}

fn validate_source_binding(
    request: &TableStructureRequest,
    source_state: &TableRulingState,
    source_grid: &TableGrid,
    current_document_flow_sha256: &str,
    limits: TableStructureLimits,
) -> Result<(), TableStructureError> {
    require_digest(current_document_flow_sha256)?;
    if source_state.grid_sha256() != hex(source_grid.canonical_sha256()?) {
        return Err(TableStructureError::SourceGridMismatch);
    }
    if request.expected_source_state_sha256 != hex(source_state.canonical_sha256(limits.ruling)?) {
        return Err(TableStructureError::SourceStateMismatch);
    }
    if request.expected_source_grid_sha256 != hex(source_grid.canonical_sha256()?) {
        return Err(TableStructureError::SourceGridMismatch);
    }
    if request.expected_document_flow_sha256 != current_document_flow_sha256 {
        return Err(TableStructureError::DocumentFlowMismatch);
    }
    Ok(())
}

fn validate_transition(
    source_state: &TableRulingState,
    source_grid: &TableGrid,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    edit: EditSpec,
    operation_receipt: &TableOperationReceipt,
    limits: TableStructureLimits,
) -> Result<TransitionCounts, TableStructureError> {
    if source_state.grid_sha256() != hex(source_grid.canonical_sha256()?)
        || target_state.grid_sha256() != hex(target_grid.canonical_sha256()?)
    {
        return Err(TableStructureError::TargetGridMismatch);
    }
    validate_geometry(source_state, target_state, edit)?;
    let mut counts = validate_cells(
        source_state,
        target_state,
        edit,
        operation_receipt,
        limits.formula,
    )?;
    let edge_counts = validate_edges(source_state, target_state, edit)?;
    counts.preserved_edges = edge_counts.0;
    counts.introduced_edges = edge_counts.1;
    counts.removed_edges = edge_counts.2;
    Ok(counts)
}

fn validate_geometry(
    source: &TableRulingState,
    target: &TableRulingState,
    edit: EditSpec,
) -> Result<(), TableStructureError> {
    if source.table_id() != target.table_id()
        || source.table_properties_sha256() != target.table_properties_sha256()
        || source.frame().left_hwpunit != target.frame().left_hwpunit
        || source.frame().top_hwpunit != target.frame().top_hwpunit
    {
        return Err(TableStructureError::GeometryMismatch);
    }
    let (source_active, target_active, source_inactive, target_inactive) = match edit.axis {
        StructureAxis::Rows => (
            source.row_boundaries_hwpunit(),
            target.row_boundaries_hwpunit(),
            source.column_boundaries_hwpunit(),
            target.column_boundaries_hwpunit(),
        ),
        StructureAxis::Columns => (
            source.column_boundaries_hwpunit(),
            target.column_boundaries_hwpunit(),
            source.row_boundaries_hwpunit(),
            target.row_boundaries_hwpunit(),
        ),
    };
    if source_inactive != target_inactive {
        return Err(TableStructureError::GeometryMismatch);
    }
    let source_sizes = track_sizes(source_active)?;
    let target_sizes = track_sizes(target_active)?;
    let index = usize::try_from(edit.index).map_err(|_| TableStructureError::GeometryMismatch)?;
    let count = usize::try_from(edit.count).map_err(|_| TableStructureError::GeometryMismatch)?;
    let exact = match edit.kind {
        StructureKind::Insert => {
            index <= source_sizes.len()
                && index
                    .checked_add(count)
                    .is_some_and(|end| end <= target_sizes.len())
                && source_sizes[..index] == target_sizes[..index]
                && source_sizes[index..] == target_sizes[index + count..]
        }
        StructureKind::Delete => index.checked_add(count).is_some_and(|end| {
            end <= source_sizes.len()
                && source_sizes[..index] == target_sizes[..index]
                && source_sizes[end..] == target_sizes[index..]
        }),
    };
    if !exact {
        return Err(TableStructureError::GeometryMismatch);
    }
    Ok(())
}

fn track_sizes(boundaries: &[u32]) -> Result<Vec<u32>, TableStructureError> {
    let mut sizes = Vec::new();
    sizes
        .try_reserve_exact(boundaries.len().saturating_sub(1))
        .map_err(|_| TableStructureError::AllocationFailed)?;
    for pair in boundaries.windows(2) {
        sizes.push(
            pair[1]
                .checked_sub(pair[0])
                .ok_or(TableStructureError::GeometryMismatch)?,
        );
    }
    Ok(sizes)
}

fn validate_cells(
    source: &TableRulingState,
    target: &TableRulingState,
    edit: EditSpec,
    receipt: &TableOperationReceipt,
    formula_limits: FormulaLimits,
) -> Result<TransitionCounts, TableStructureError> {
    let mut counts = TransitionCounts::default();
    for remap in receipt.preserved_master_cells() {
        let before = source
            .cell(remap.master_cell_id())
            .ok_or(TableStructureError::CellPreservationMismatch)?;
        let after = target
            .cell(remap.master_cell_id())
            .ok_or(TableStructureError::CellPreservationMismatch)?;
        if before.coordinate() != remap.before()
            || after.coordinate() != remap.after()
            || before.payload() != after.payload()
            || before.properties() != after.properties()
        {
            return Err(TableStructureError::CellPreservationMismatch);
        }
        validate_formula_transition(before, after, edit, formula_limits, &mut counts)?;
    }
    for identifier in receipt.inserted_master_cell_ids() {
        let cell = target
            .cell(identifier)
            .ok_or(TableStructureError::InsertedCellMismatch)?;
        if !cell.payload().is_empty() || cell.formula().is_some() {
            return Err(TableStructureError::InsertedCellMismatch);
        }
        if source.cell(identifier).is_some() {
            return Err(TableStructureError::InsertedCellMismatch);
        }
    }
    for identifier in receipt.deleted_master_cell_ids() {
        let cell = source
            .cell(identifier)
            .ok_or(TableStructureError::DeletedCellMismatch)?;
        if target.cell(identifier).is_some() {
            return Err(TableStructureError::DeletedCellMismatch);
        }
        if cell.formula().is_some() {
            counts.formulas_deleted = counts
                .formulas_deleted
                .checked_add(1)
                .ok_or(TableStructureError::OutputLimit)?;
        }
    }
    let covered = receipt
        .preserved_master_cells()
        .len()
        .checked_add(receipt.deleted_master_cell_ids().len())
        .ok_or(TableStructureError::OutputLimit)?;
    let target_covered = receipt
        .preserved_master_cells()
        .len()
        .checked_add(receipt.inserted_master_cell_ids().len())
        .ok_or(TableStructureError::OutputLimit)?;
    if covered != source.cells().len() || target_covered != target.cells().len() {
        return Err(TableStructureError::CellPreservationMismatch);
    }
    Ok(counts)
}

fn validate_formula_transition(
    source: &TableRulingCell,
    target: &TableRulingCell,
    edit: EditSpec,
    limits: FormulaLimits,
    counts: &mut TransitionCounts,
) -> Result<(), TableStructureError> {
    match (source.formula(), target.formula()) {
        (None, None) => Ok(()),
        (None, Some(_)) | (Some(_), None) => Err(TableStructureError::FormulaMismatch),
        (Some(before), Some(after)) => {
            let (expected, cache_cleared, cache_updated) =
                transformed_formula(before, after, edit.formula_edit(), limits)?;
            if expected != *after {
                return Err(TableStructureError::FormulaMismatch);
            }
            if before.owner() != after.owner() || before.ast() != after.ast() {
                counts.formulas_rebased = counts
                    .formulas_rebased
                    .checked_add(1)
                    .ok_or(TableStructureError::OutputLimit)?;
            }
            if cache_cleared {
                counts.formula_caches_cleared = counts
                    .formula_caches_cleared
                    .checked_add(1)
                    .ok_or(TableStructureError::OutputLimit)?;
            }
            if cache_updated {
                counts.formula_caches_updated = counts
                    .formula_caches_updated
                    .checked_add(1)
                    .ok_or(TableStructureError::OutputLimit)?;
            }
            Ok(())
        }
    }
}

fn transformed_formula(
    source: &FormulaCell,
    target: &FormulaCell,
    edit: FormulaGridEdit,
    limits: FormulaLimits,
) -> Result<(FormulaCell, bool, bool), TableStructureError> {
    if source.cache() == target.cache()
        && let Ok(preserved) =
            source.apply_grid_edit(edit, FormulaCachePolicy::Preserve, None, limits)
        && preserved == *target
    {
        return Ok((preserved, false, false));
    }
    match target.cache() {
        FormulaCache::Absent => Ok((
            source.apply_grid_edit(edit, FormulaCachePolicy::Clear, None, limits)?,
            !matches!(source.cache(), FormulaCache::Absent),
            false,
        )),
        cache @ FormulaCache::Unverified { .. } => Ok((
            source.apply_grid_edit(
                edit,
                FormulaCachePolicy::Update,
                Some(cache.clone()),
                limits,
            )?,
            false,
            true,
        )),
    }
}

type EdgeKey = (TableRulingAxis, u32, u32);

fn validate_edges(
    source: &TableRulingState,
    target: &TableRulingState,
    edit: EditSpec,
) -> Result<(usize, usize, usize), TableStructureError> {
    let mut preserved_targets = BTreeSet::new();
    let mut mapped_sources = 0_usize;
    for source_edge in source.edges() {
        let targets = mapped_edge_keys(source_edge, edit)?;
        if !targets.is_empty() {
            mapped_sources = mapped_sources
                .checked_add(1)
                .ok_or(TableStructureError::OutputLimit)?;
        }
        for key in targets {
            let target_edge = target
                .edge(key.0, key.1, key.2)
                .ok_or(TableStructureError::EdgePreservationMismatch)?;
            if target_edge.line_sha256 != source_edge.line_sha256 {
                return Err(TableStructureError::EdgePreservationMismatch);
            }
            preserved_targets.insert(key);
        }
    }
    let introduced = target
        .edges()
        .len()
        .checked_sub(preserved_targets.len())
        .ok_or(TableStructureError::EdgePreservationMismatch)?;
    let removed = source
        .edges()
        .len()
        .checked_sub(mapped_sources)
        .ok_or(TableStructureError::EdgePreservationMismatch)?;
    Ok((preserved_targets.len(), introduced, removed))
}

fn mapped_edge_keys(
    edge: &TableRulingEdge,
    edit: EditSpec,
) -> Result<Vec<EdgeKey>, TableStructureError> {
    let edited_boundary_axis = match edit.axis {
        StructureAxis::Rows => TableRulingAxis::Horizontal,
        StructureAxis::Columns => TableRulingAxis::Vertical,
    };
    if edge.axis == edited_boundary_axis {
        return Ok(boundary_targets(edge.boundary, edit)?
            .into_iter()
            .map(|boundary| (edge.axis, boundary, edge.offset))
            .collect());
    }
    Ok(track_target(edge.offset, edit)?
        .into_iter()
        .map(|offset| (edge.axis, edge.boundary, offset))
        .collect())
}

fn boundary_targets(boundary: u32, edit: EditSpec) -> Result<Vec<u32>, TableStructureError> {
    match edit.kind {
        StructureKind::Insert => match boundary.cmp(&edit.index) {
            std::cmp::Ordering::Less => Ok(vec![boundary]),
            std::cmp::Ordering::Equal => Ok(vec![
                boundary,
                boundary
                    .checked_add(edit.count)
                    .ok_or(TableStructureError::EdgePreservationMismatch)?,
            ]),
            std::cmp::Ordering::Greater => Ok(vec![
                boundary
                    .checked_add(edit.count)
                    .ok_or(TableStructureError::EdgePreservationMismatch)?,
            ]),
        },
        StructureKind::Delete => {
            let end = edit
                .index
                .checked_add(edit.count)
                .ok_or(TableStructureError::EdgePreservationMismatch)?;
            if boundary < edit.index {
                Ok(vec![boundary])
            } else if boundary > end {
                Ok(vec![
                    boundary
                        .checked_sub(edit.count)
                        .ok_or(TableStructureError::EdgePreservationMismatch)?,
                ])
            } else if (boundary == edit.index && edit.index > 0)
                || (boundary == end && end < edit.dimension)
            {
                Ok(vec![edit.index])
            } else {
                Ok(Vec::new())
            }
        }
    }
}

fn track_target(track: u32, edit: EditSpec) -> Result<Option<u32>, TableStructureError> {
    match edit.kind {
        StructureKind::Insert => {
            if track < edit.index {
                Ok(Some(track))
            } else {
                Ok(Some(
                    track
                        .checked_add(edit.count)
                        .ok_or(TableStructureError::EdgePreservationMismatch)?,
                ))
            }
        }
        StructureKind::Delete => {
            let end = edit
                .index
                .checked_add(edit.count)
                .ok_or(TableStructureError::EdgePreservationMismatch)?;
            if track < edit.index {
                Ok(Some(track))
            } else if track >= end {
                Ok(Some(
                    track
                        .checked_sub(edit.count)
                        .ok_or(TableStructureError::EdgePreservationMismatch)?,
                ))
            } else {
                Ok(None)
            }
        }
    }
}

#[derive(Debug, Error)]
pub enum TableStructureError {
    #[error("table structure limits are invalid")]
    InvalidLimit,
    #[error("unsupported table structure schema version")]
    UnsupportedVersion,
    #[error("table structure input exceeds its finite bound")]
    InputLimit,
    #[error("invalid table structure JSON")]
    InvalidJson,
    #[error("table structure digest binding is invalid")]
    InvalidDigest,
    #[error("table structure source state drifted")]
    SourceStateMismatch,
    #[error("table structure source grid drifted")]
    SourceGridMismatch,
    #[error("table structure document flow drifted")]
    DocumentFlowMismatch,
    #[error("delete operations cannot declare new master cells")]
    UnexpectedNewMasterCells,
    #[error("table structure target grid mismatched the exact operation")]
    TargetGridMismatch,
    #[error("table structure geometry did not preserve unaffected tracks")]
    GeometryMismatch,
    #[error("table structure survivor cell state drifted")]
    CellPreservationMismatch,
    #[error("table structure inserted cell is missing, nonempty or formula-bearing")]
    InsertedCellMismatch,
    #[error("table structure deleted cell did not disappear exactly")]
    DeletedCellMismatch,
    #[error("table structure formula or cache transition is not exact")]
    FormulaMismatch,
    #[error("table structure unaffected edge state drifted")]
    EdgePreservationMismatch,
    #[error("table structure allocation failed")]
    AllocationFailed,
    #[error("table structure serialization failed")]
    Serialization,
    #[error("table structure output exceeds its finite bound")]
    OutputLimit,
    #[error(transparent)]
    Operation(#[from] TableOperationError),
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    Formula(#[from] FormulaError),
    #[error(transparent)]
    Ruling(#[from] TableRulingError),
}

impl TableStructureError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_structure_invalid_limit",
            Self::UnsupportedVersion => "table_structure_version",
            Self::InputLimit => "table_structure_input_limit",
            Self::InvalidJson => "table_structure_invalid_json",
            Self::InvalidDigest => "table_structure_invalid_digest",
            Self::SourceStateMismatch => "table_structure_source_state_mismatch",
            Self::SourceGridMismatch => "table_structure_source_grid_mismatch",
            Self::DocumentFlowMismatch => "table_structure_document_flow_mismatch",
            Self::UnexpectedNewMasterCells => "table_structure_unexpected_new_master_cells",
            Self::TargetGridMismatch => "table_structure_target_grid_mismatch",
            Self::GeometryMismatch => "table_structure_geometry_mismatch",
            Self::CellPreservationMismatch => "table_structure_cell_preservation_mismatch",
            Self::InsertedCellMismatch => "table_structure_inserted_cell_mismatch",
            Self::DeletedCellMismatch => "table_structure_deleted_cell_mismatch",
            Self::FormulaMismatch => "table_structure_formula_mismatch",
            Self::EdgePreservationMismatch => "table_structure_edge_preservation_mismatch",
            Self::AllocationFailed => "table_structure_allocation",
            Self::Serialization => "table_structure_serialization",
            Self::OutputLimit => "table_structure_output_limit",
            Self::Operation(_) => "table_structure_grid_operation",
            Self::Grid(_) => "table_structure_grid",
            Self::Formula(_) => "table_structure_formula",
            Self::Ruling(_) => "table_structure_ruling",
        }
    }
}

fn grid_dimensions(grid: &TableGrid) -> FormulaGridDimensions {
    FormulaGridDimensions {
        rows: grid.rows(),
        columns: grid.columns(),
    }
}

fn require_digest(value: &str) -> Result<(), TableStructureError> {
    if value.len() != 64
        || value
            .as_bytes()
            .iter()
            .any(|byte| !matches!(*byte, b'0'..=b'9' | b'a'..=b'f'))
    {
        return Err(TableStructureError::InvalidDigest);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: TableStructureLimits,
) -> Result<Vec<u8>, TableStructureError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableStructureError::Serialization)?;
    if bytes.len() > limits.config.serialized_bytes {
        return Err(TableStructureError::OutputLimit);
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

#[allow(clippy::too_many_lines)]
fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), TableStructureError> {
    struct RootVisitor;
    struct AnyVisitor;
    struct Seed;

    impl<'de> serde::de::DeserializeSeed<'de> for Seed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(AnyVisitor)
        }
    }

    fn visit_map<'de, A>(mut map: A) -> Result<(), A::Error>
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

    impl<'de> serde::de::Visitor<'de> for RootVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }

        fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            visit_map(map)
        }
    }

    impl<'de> serde::de::Visitor<'de> for AnyVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("any JSON value")
        }

        fn visit_map<A>(self, map: A) -> Result<Self::Value, A::Error>
        where
            A: serde::de::MapAccess<'de>,
        {
            visit_map(map)
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
    serde::de::Deserializer::deserialize_map(&mut deserializer, RootVisitor)
        .map_err(|_| TableStructureError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| TableStructureError::InvalidJson)
}
