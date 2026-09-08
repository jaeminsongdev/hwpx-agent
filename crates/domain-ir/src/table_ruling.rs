use std::collections::{BTreeMap, HashMap, HashSet, VecDeque};
use std::fmt;
use std::io::{self, Write};

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    CellCoordinate, FormulaCache, FormulaCachePolicy, FormulaCell, FormulaCellDraft, FormulaError,
    FormulaGridDimensions, FormulaGridEdit, FormulaLimits, LogicalId, TableCellSpan, TableGrid,
    TableGridError, TableGridLimits,
};

pub const TABLE_RULING_SCHEMA_VERSION: &str = "hwpx-agent.table-ruling/v1";
pub const TABLE_DRAW_CAPABILITY_ID: &str = "table.draw";
pub const TABLE_ERASER_CAPABILITY_ID: &str = "table.eraser";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableRulingLimitConfig {
    pub input_bytes: usize,
    pub cells: usize,
    pub edges: usize,
    pub payload_blocks: usize,
    pub identifier_bytes: usize,
    pub dimension_hwpunit: u32,
    pub serialized_bytes: usize,
}

impl Default for TableRulingLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 32 * 1024 * 1024,
            cells: 1_000_000,
            edges: 2_100_000,
            payload_blocks: 1_000_000,
            identifier_bytes: 256,
            dimension_hwpunit: 1_000_000_000,
            serialized_bytes: 128 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableRulingLimits(TableRulingLimitConfig);

impl TableRulingLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_CELLS: usize = 1_000_000;
    pub const HARD_MAX_EDGES: usize = 2_100_000;
    pub const HARD_MAX_PAYLOAD_BLOCKS: usize = 1_000_000;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 1024;
    pub const HARD_MAX_DIMENSION_HWPUNIT: u32 = 2_000_000_000;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for table ruling and topology planning.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling, or internally inconsistent limits.
    pub fn new(config: TableRulingLimitConfig) -> Result<Self, TableRulingError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.cells == 0
            || config.cells > Self::HARD_MAX_CELLS
            || config.edges == 0
            || config.edges > Self::HARD_MAX_EDGES
            || config.payload_blocks > Self::HARD_MAX_PAYLOAD_BLOCKS
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.dimension_hwpunit == 0
            || config.dimension_hwpunit > Self::HARD_MAX_DIMENSION_HWPUNIT
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TableRulingError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableRulingLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableRulingFrame {
    pub left_hwpunit: u32,
    pub top_hwpunit: u32,
    pub width_hwpunit: u32,
    pub height_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableRulingAxis {
    Horizontal,
    Vertical,
}

/// One normalized unit edge in the table's complete ruling lattice.
#[derive(Clone, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableRulingEdge {
    pub axis: TableRulingAxis,
    /// Horizontal: row boundary. Vertical: column boundary.
    pub boundary: u32,
    /// Horizontal: column track. Vertical: row track.
    pub offset: u32,
    /// `None` is an explicit transparent line, not an absent topology record.
    pub line_sha256: Option<String>,
}

impl fmt::Debug for TableRulingEdge {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingEdge")
            .field("axis", &self.axis)
            .field("boundary", &self.boundary)
            .field("offset", &self.offset)
            .field(
                "line_sha256",
                &self.line_sha256.as_ref().map(|_| "<redacted>"),
            )
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableRulingPayloadBlock {
    pub block_id: LogicalId,
    pub payload_sha256: String,
}

impl fmt::Debug for TableRulingPayloadBlock {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingPayloadBlock")
            .field("block_id", &"<redacted>")
            .field("payload_sha256", &"<redacted>")
            .finish()
    }
}

/// Complete non-edge cell properties plus both diagonal directions.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableRulingCellProperties {
    pub non_ruling_properties_sha256: String,
    pub background_sha256: Option<String>,
    pub slash_diagonal_sha256: Option<String>,
    pub back_slash_diagonal_sha256: Option<String>,
}

impl fmt::Debug for TableRulingCellProperties {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingCellProperties")
            .field("non_ruling_properties_sha256", &"<redacted>")
            .field(
                "background_sha256",
                &self.background_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "slash_diagonal_sha256",
                &self.slash_diagonal_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "back_slash_diagonal_sha256",
                &self
                    .back_slash_diagonal_sha256
                    .as_ref()
                    .map(|_| "<redacted>"),
            )
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableRulingCellDraft {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub payload: Vec<TableRulingPayloadBlock>,
    pub properties: TableRulingCellProperties,
    pub formula: Option<FormulaCellDraft>,
}

impl fmt::Debug for TableRulingCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingCellDraft")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("payload_block_count", &self.payload.len())
            .field("properties", &self.properties)
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableRulingCell {
    master_cell_id: LogicalId,
    coordinate: CellCoordinate,
    payload: Vec<TableRulingPayloadBlock>,
    properties: TableRulingCellProperties,
    formula: Option<FormulaCell>,
}

impl TableRulingCell {
    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
    }

    #[must_use]
    pub const fn coordinate(&self) -> CellCoordinate {
        self.coordinate
    }

    #[must_use]
    pub fn payload(&self) -> &[TableRulingPayloadBlock] {
        &self.payload
    }

    #[must_use]
    pub const fn properties(&self) -> &TableRulingCellProperties {
        &self.properties
    }

    #[must_use]
    pub const fn formula(&self) -> Option<&FormulaCell> {
        self.formula.as_ref()
    }
}

impl fmt::Debug for TableRulingCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingCell")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("payload_block_count", &self.payload.len())
            .field("properties", &self.properties)
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableRulingStateDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub frame: TableRulingFrame,
    pub grid_sha256: String,
    pub table_properties_sha256: String,
    pub row_boundaries_hwpunit: Vec<u32>,
    pub column_boundaries_hwpunit: Vec<u32>,
    pub edges: Vec<TableRulingEdge>,
    pub cells: Vec<TableRulingCellDraft>,
}

impl fmt::Debug for TableRulingStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingStateDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("frame", &self.frame)
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("row_boundary_count", &self.row_boundaries_hwpunit.len())
            .field(
                "column_boundary_count",
                &self.column_boundaries_hwpunit.len(),
            )
            .field("edge_count", &self.edges.len())
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableRulingState {
    schema_version: &'static str,
    table_id: LogicalId,
    frame: TableRulingFrame,
    grid_sha256: String,
    table_properties_sha256: String,
    row_boundaries_hwpunit: Vec<u32>,
    column_boundaries_hwpunit: Vec<u32>,
    edges: Vec<TableRulingEdge>,
    cells: Vec<TableRulingCell>,
}

impl TableRulingState {
    /// Validates a complete grid, physical lattice, unit-edge, payload, property, formula and cache
    /// snapshot.
    ///
    /// # Errors
    ///
    /// Rejects schema, bounds, identity, digest, coverage, topology, formula, or serialization drift.
    pub fn from_draft(
        draft: TableRulingStateDraft,
        grid: &TableGrid,
        formula_limits: FormulaLimits,
        limits: TableRulingLimits,
    ) -> Result<Self, TableRulingError> {
        if draft.schema_version != TABLE_RULING_SCHEMA_VERSION {
            return Err(TableRulingError::UnsupportedVersion);
        }
        validate_identifier(&draft.table_id, limits)?;
        validate_frame(draft.frame, limits)?;
        validate_digest(&draft.grid_sha256)?;
        validate_digest(&draft.table_properties_sha256)?;
        if draft.grid_sha256 != grid_digest(grid)? {
            return Err(TableRulingError::GridMismatch);
        }
        validate_boundaries(
            &draft.row_boundaries_hwpunit,
            grid.rows(),
            draft.frame.height_hwpunit,
        )?;
        validate_boundaries(
            &draft.column_boundaries_hwpunit,
            grid.columns(),
            draft.frame.width_hwpunit,
        )?;
        let edges = validate_edges(draft.edges, grid, limits)?;
        let cells = validate_cells(draft.cells, grid, formula_limits, limits)?;
        validate_global_identities(&draft.table_id, &cells)?;
        Self::from_validated_parts(
            draft.table_id,
            draft.frame,
            draft.table_properties_sha256,
            draft.row_boundaries_hwpunit,
            draft.column_boundaries_hwpunit,
            edges,
            cells,
            grid,
            limits,
        )
    }

    /// Parses and validates bounded strict JSON against an exact logical grid.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, unknown, duplicate, or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        grid: &TableGrid,
        formula_limits: FormulaLimits,
        limits: TableRulingLimits,
    ) -> Result<Self, TableRulingError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableRulingError::InvalidJson)?;
        Self::from_draft(draft, grid, formula_limits, limits)
    }

    #[allow(clippy::too_many_arguments)]
    fn from_validated_parts(
        table_id: LogicalId,
        frame: TableRulingFrame,
        table_properties_sha256: String,
        row_boundaries_hwpunit: Vec<u32>,
        column_boundaries_hwpunit: Vec<u32>,
        edges: Vec<TableRulingEdge>,
        mut cells: Vec<TableRulingCell>,
        grid: &TableGrid,
        limits: TableRulingLimits,
    ) -> Result<Self, TableRulingError> {
        validate_identifier(&table_id, limits)?;
        validate_frame(frame, limits)?;
        validate_digest(&table_properties_sha256)?;
        validate_boundaries(&row_boundaries_hwpunit, grid.rows(), frame.height_hwpunit)?;
        validate_boundaries(
            &column_boundaries_hwpunit,
            grid.columns(),
            frame.width_hwpunit,
        )?;
        let edges = validate_edges(edges, grid, limits)?;
        validate_validated_cells(&mut cells, grid, limits)?;
        validate_global_identities(&table_id, &cells)?;
        let state = Self {
            schema_version: TABLE_RULING_SCHEMA_VERSION,
            table_id,
            frame,
            grid_sha256: grid_digest(grid)?,
            table_properties_sha256,
            row_boundaries_hwpunit,
            column_boundaries_hwpunit,
            edges,
            cells,
        };
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn frame(&self) -> TableRulingFrame {
        self.frame
    }

    #[must_use]
    pub fn grid_sha256(&self) -> &str {
        &self.grid_sha256
    }

    #[must_use]
    pub fn table_properties_sha256(&self) -> &str {
        &self.table_properties_sha256
    }

    #[must_use]
    pub fn row_boundaries_hwpunit(&self) -> &[u32] {
        &self.row_boundaries_hwpunit
    }

    #[must_use]
    pub fn column_boundaries_hwpunit(&self) -> &[u32] {
        &self.column_boundaries_hwpunit
    }

    #[must_use]
    pub fn edges(&self) -> &[TableRulingEdge] {
        &self.edges
    }

    #[must_use]
    pub fn cells(&self) -> &[TableRulingCell] {
        &self.cells
    }

    #[must_use]
    pub fn edge(
        &self,
        axis: TableRulingAxis,
        boundary: u32,
        offset: u32,
    ) -> Option<&TableRulingEdge> {
        self.edges
            .binary_search_by_key(&(axis, boundary, offset), |edge| {
                (edge.axis, edge.boundary, edge.offset)
            })
            .ok()
            .and_then(|index| self.edges.get(index))
    }

    #[must_use]
    pub fn cell(&self, master_cell_id: &LogicalId) -> Option<&TableRulingCell> {
        self.cells
            .iter()
            .find(|cell| cell.master_cell_id == *master_cell_id)
    }

    /// Emits deterministic bounded JSON with normalized edges and row-major cells.
    ///
    /// # Errors
    ///
    /// Returns a stable size, allocation, or serialization failure.
    pub fn canonical_json(&self, limits: TableRulingLimits) -> Result<Vec<u8>, TableRulingError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Hashes the complete canonical state.
    ///
    /// # Errors
    ///
    /// Propagates bounded serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableRulingLimits,
    ) -> Result<[u8; 32], TableRulingError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableRulingState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingState")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("frame", &self.frame)
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("row_boundary_count", &self.row_boundaries_hwpunit.len())
            .field(
                "column_boundary_count",
                &self.column_boundaries_hwpunit.len(),
            )
            .field("edge_count", &self.edges.len())
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableRulingFormulaPolicy {
    RejectRebase,
    RebaseAndClearTopologyStaleCache,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableRulingDiagonalDirection {
    Slash,
    BackSlash,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableRulingStroke {
    pub axis: TableRulingAxis,
    /// Horizontal: local y. Vertical: local x.
    pub fixed_hwpunit: u32,
    /// Horizontal: local x. Vertical: local y.
    pub start_hwpunit: u32,
    /// Horizontal: local x. Vertical: local y.
    pub end_hwpunit: u32,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TableRulingOperation {
    DrawOuterRectangle {
        frame: TableRulingFrame,
        initial_master_cell_id: LogicalId,
        table_properties_sha256: String,
        initial_cell_properties: TableRulingCellProperties,
        line_sha256: String,
        insertion_context_sha256: String,
    },
    DrawStroke {
        stroke: TableRulingStroke,
        line_sha256: String,
        new_master_cell_ids: Vec<LogicalId>,
        formula_policy: TableRulingFormulaPolicy,
    },
    DrawDiagonal {
        master_cell_id: LogicalId,
        direction: TableRulingDiagonalDirection,
        line_sha256: String,
    },
    EraseStroke {
        stroke: TableRulingStroke,
        formula_policy: TableRulingFormulaPolicy,
    },
    EraseDiagonal {
        master_cell_id: LogicalId,
        direction: TableRulingDiagonalDirection,
    },
}

impl TableRulingOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::DrawOuterRectangle { .. }
            | Self::DrawStroke { .. }
            | Self::DrawDiagonal { .. } => TABLE_DRAW_CAPABILITY_ID,
            Self::EraseStroke { .. } | Self::EraseDiagonal { .. } => TABLE_ERASER_CAPABILITY_ID,
        }
    }

    const fn is_outer_rectangle(&self) -> bool {
        matches!(self, Self::DrawOuterRectangle { .. })
    }
}

impl fmt::Debug for TableRulingOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::DrawOuterRectangle { frame, .. } => formatter
                .debug_struct("DrawOuterRectangle")
                .field("frame", frame)
                .finish_non_exhaustive(),
            Self::DrawStroke {
                stroke,
                new_master_cell_ids,
                formula_policy,
                ..
            } => formatter
                .debug_struct("DrawStroke")
                .field("stroke", stroke)
                .field("new_master_cell_count", &new_master_cell_ids.len())
                .field("formula_policy", formula_policy)
                .finish(),
            Self::DrawDiagonal { direction, .. } => formatter
                .debug_struct("DrawDiagonal")
                .field("direction", direction)
                .finish_non_exhaustive(),
            Self::EraseStroke {
                stroke,
                formula_policy,
            } => formatter
                .debug_struct("EraseStroke")
                .field("stroke", stroke)
                .field("formula_policy", formula_policy)
                .finish(),
            Self::EraseDiagonal { direction, .. } => formatter
                .debug_struct("EraseDiagonal")
                .field("direction", direction)
                .finish_non_exhaustive(),
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableRulingRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub expected_state_sha256: Option<String>,
    pub expected_grid_sha256: Option<String>,
    pub expected_document_flow_sha256: String,
    pub operation: TableRulingOperation,
}

impl fmt::Debug for TableRulingRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field(
                "expected_state_sha256",
                &self.expected_state_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "expected_grid_sha256",
                &self.expected_grid_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("operation", &self.operation)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableRulingRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    expected_state_sha256: Option<String>,
    expected_grid_sha256: Option<String>,
    expected_document_flow_sha256: String,
    operation: TableRulingOperation,
}

impl TableRulingRequest {
    /// Validates an outer-table creation context or binds an existing-table operation to exact
    /// state, grid and document-flow digests.
    ///
    /// # Errors
    ///
    /// Rejects schema, context, identity, geometry, state, grid, flow and operation drift.
    pub fn from_draft(
        draft: TableRulingRequestDraft,
        state: Option<&TableRulingState>,
        grid: Option<&TableGrid>,
        current_document_flow_sha256: &str,
        limits: TableRulingLimits,
    ) -> Result<Self, TableRulingError> {
        if draft.schema_version != TABLE_RULING_SCHEMA_VERSION {
            return Err(TableRulingError::UnsupportedVersion);
        }
        validate_identifier(&draft.table_id, limits)?;
        validate_digest(&draft.expected_document_flow_sha256)?;
        validate_digest(current_document_flow_sha256)?;
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(TableRulingError::FlowBindingMismatch);
        }
        validate_operation(&draft.operation, limits)?;
        if draft.operation.is_outer_rectangle() {
            if state.is_some()
                || grid.is_some()
                || draft.expected_state_sha256.is_some()
                || draft.expected_grid_sha256.is_some()
            {
                return Err(TableRulingError::ContextMismatch);
            }
            if let TableRulingOperation::DrawOuterRectangle {
                initial_master_cell_id,
                ..
            } = &draft.operation
                && *initial_master_cell_id == draft.table_id
            {
                return Err(TableRulingError::IdentifierCollision);
            }
        } else {
            let state = state.ok_or(TableRulingError::ContextMismatch)?;
            let grid = grid.ok_or(TableRulingError::ContextMismatch)?;
            let expected_state = draft
                .expected_state_sha256
                .as_deref()
                .ok_or(TableRulingError::ContextMismatch)?;
            let expected_grid = draft
                .expected_grid_sha256
                .as_deref()
                .ok_or(TableRulingError::ContextMismatch)?;
            validate_digest(expected_state)?;
            validate_digest(expected_grid)?;
            validate_existing_binding(
                &draft.table_id,
                expected_state,
                expected_grid,
                state,
                grid,
                limits,
            )?;
            validate_existing_operation(&draft.operation, state, grid)?;
        }
        let request = Self {
            schema_version: TABLE_RULING_SCHEMA_VERSION,
            capability_id: draft.operation.capability_id(),
            table_id: draft.table_id,
            expected_state_sha256: draft.expected_state_sha256,
            expected_grid_sha256: draft.expected_grid_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses a bounded strict request and validates all current bindings.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, unknown, duplicate, or stale input.
    pub fn from_json(
        bytes: &[u8],
        state: Option<&TableRulingState>,
        grid: Option<&TableGrid>,
        current_document_flow_sha256: &str,
        limits: TableRulingLimits,
    ) -> Result<Self, TableRulingError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableRulingError::InvalidJson)?;
        Self::from_draft(draft, state, grid, current_document_flow_sha256, limits)
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
    pub const fn operation(&self) -> &TableRulingOperation {
        &self.operation
    }

    /// Emits deterministic bounded request JSON.
    ///
    /// # Errors
    ///
    /// Returns a stable size, allocation, or serialization failure.
    pub fn canonical_json(&self, limits: TableRulingLimits) -> Result<Vec<u8>, TableRulingError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for TableRulingRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field(
                "expected_state_sha256",
                &self.expected_state_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "expected_grid_sha256",
                &self.expected_grid_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("expected_document_flow_sha256", &"<redacted>")
            .field("operation", &self.operation)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableRulingPlanKind {
    OuterRectangle,
    EdgeStroke,
    Diagonal,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableRulingPlannedGrid {
    rows: u32,
    columns: u32,
    grid_sha256: String,
    master_cells: Vec<TableCellSpan>,
}

impl TableRulingPlannedGrid {
    fn new(grid: &TableGrid) -> Result<Self, TableRulingError> {
        Ok(Self {
            rows: grid.rows(),
            columns: grid.columns(),
            grid_sha256: grid_digest(grid)?,
            master_cells: grid.master_cells().to_vec(),
        })
    }

    #[must_use]
    pub const fn rows(&self) -> u32 {
        self.rows
    }

    #[must_use]
    pub const fn columns(&self) -> u32 {
        self.columns
    }

    #[must_use]
    pub fn grid_sha256(&self) -> &str {
        &self.grid_sha256
    }

    #[must_use]
    pub fn master_cells(&self) -> &[TableCellSpan] {
        &self.master_cells
    }
}

impl fmt::Debug for TableRulingPlannedGrid {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingPlannedGrid")
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("grid_sha256", &"<redacted>")
            .field("master_cell_count", &self.master_cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableRulingReceipt {
    before_state_sha256: Option<String>,
    after_state_sha256: String,
    before_grid_sha256: Option<String>,
    after_grid_sha256: String,
    document_flow_sha256: String,
    insertion_context_sha256: Option<String>,
    edge_change_count: usize,
    diagonal_change_count: usize,
    created_master_cell_count: usize,
    retired_master_cell_count: usize,
    structural_merge_count: usize,
    nonstructural_transparent_edge_count: usize,
    payload_block_preserved_count: usize,
    formula_preserved_count: usize,
    formula_rebased_count: usize,
    formula_cache_cleared_count: usize,
    topology_changed: bool,
}

impl TableRulingReceipt {
    #[must_use]
    pub fn insertion_context_sha256(&self) -> Option<&str> {
        self.insertion_context_sha256.as_deref()
    }

    #[must_use]
    pub const fn topology_changed(&self) -> bool {
        self.topology_changed
    }

    #[must_use]
    pub const fn edge_change_count(&self) -> usize {
        self.edge_change_count
    }

    #[must_use]
    pub const fn diagonal_change_count(&self) -> usize {
        self.diagonal_change_count
    }

    #[must_use]
    pub const fn created_master_cell_count(&self) -> usize {
        self.created_master_cell_count
    }

    #[must_use]
    pub const fn retired_master_cell_count(&self) -> usize {
        self.retired_master_cell_count
    }

    #[must_use]
    pub const fn structural_merge_count(&self) -> usize {
        self.structural_merge_count
    }

    #[must_use]
    pub const fn nonstructural_transparent_edge_count(&self) -> usize {
        self.nonstructural_transparent_edge_count
    }

    #[must_use]
    pub const fn payload_block_preserved_count(&self) -> usize {
        self.payload_block_preserved_count
    }

    #[must_use]
    pub const fn formula_preserved_count(&self) -> usize {
        self.formula_preserved_count
    }

    #[must_use]
    pub const fn formula_rebased_count(&self) -> usize {
        self.formula_rebased_count
    }

    #[must_use]
    pub const fn formula_cache_cleared_count(&self) -> usize {
        self.formula_cache_cleared_count
    }
}

impl fmt::Debug for TableRulingReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingReceipt")
            .field(
                "before_state_sha256",
                &self.before_state_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("after_state_sha256", &"<redacted>")
            .field(
                "before_grid_sha256",
                &self.before_grid_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("after_grid_sha256", &"<redacted>")
            .field("document_flow_sha256", &"<redacted>")
            .field(
                "insertion_context_sha256",
                &self.insertion_context_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("edge_change_count", &self.edge_change_count)
            .field("diagonal_change_count", &self.diagonal_change_count)
            .field("created_master_cell_count", &self.created_master_cell_count)
            .field("retired_master_cell_count", &self.retired_master_cell_count)
            .field("structural_merge_count", &self.structural_merge_count)
            .field(
                "nonstructural_transparent_edge_count",
                &self.nonstructural_transparent_edge_count,
            )
            .field(
                "payload_block_preserved_count",
                &self.payload_block_preserved_count,
            )
            .field("formula_preserved_count", &self.formula_preserved_count)
            .field("formula_rebased_count", &self.formula_rebased_count)
            .field(
                "formula_cache_cleared_count",
                &self.formula_cache_cleared_count,
            )
            .field("topology_changed", &self.topology_changed)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableRulingPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    plan_kind: TableRulingPlanKind,
    after_grid: TableRulingPlannedGrid,
    after_state: TableRulingState,
    receipt: TableRulingReceipt,
}

impl TableRulingPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn plan_kind(&self) -> TableRulingPlanKind {
        self.plan_kind
    }

    #[must_use]
    pub const fn after_grid(&self) -> &TableRulingPlannedGrid {
        &self.after_grid
    }

    #[must_use]
    pub const fn after_state(&self) -> &TableRulingState {
        &self.after_state
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableRulingReceipt {
        &self.receipt
    }

    /// Emits deterministic bounded lowering-ready JSON.
    ///
    /// # Errors
    ///
    /// Returns a stable size, allocation, or serialization failure.
    pub fn canonical_json(&self, limits: TableRulingLimits) -> Result<Vec<u8>, TableRulingError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for TableRulingPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableRulingPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("plan_kind", &self.plan_kind)
            .field("after_grid", &self.after_grid)
            .field("after_state", &self.after_state)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
struct FormulaCounts {
    rebased: usize,
    caches_cleared: usize,
}

#[derive(Debug)]
pub struct TableRulingBuilder;

impl TableRulingBuilder {
    /// Builds one atomic ruling/topology plan and revalidates the exact state, grid and flow
    /// bindings immediately before planning.
    ///
    /// # Errors
    ///
    /// Returns a typed error and no partial plan or receipt on any drift or semantic failure.
    #[allow(clippy::too_many_arguments)]
    pub fn build(
        request: &TableRulingRequest,
        state: Option<&TableRulingState>,
        grid: Option<&TableGrid>,
        current_document_flow_sha256: &str,
        grid_limits: TableGridLimits,
        formula_limits: FormulaLimits,
        limits: TableRulingLimits,
    ) -> Result<TableRulingPlan, TableRulingError> {
        validate_identifier(&request.table_id, limits)?;
        validate_operation(&request.operation, limits)?;
        let _ = request.canonical_json(limits)?;
        validate_digest(current_document_flow_sha256)?;
        if request.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(TableRulingError::FlowBindingMismatch);
        }
        match &request.operation {
            TableRulingOperation::DrawOuterRectangle { .. } => {
                if state.is_some() || grid.is_some() {
                    return Err(TableRulingError::ContextMismatch);
                }
                Self::build_outer(request, grid_limits, limits)
            }
            operation => {
                let state = state.ok_or(TableRulingError::ContextMismatch)?;
                let grid = grid.ok_or(TableRulingError::ContextMismatch)?;
                validate_existing_binding(
                    &request.table_id,
                    request
                        .expected_state_sha256
                        .as_deref()
                        .ok_or(TableRulingError::ContextMismatch)?,
                    request
                        .expected_grid_sha256
                        .as_deref()
                        .ok_or(TableRulingError::ContextMismatch)?,
                    state,
                    grid,
                    limits,
                )?;
                validate_existing_operation(operation, state, grid)?;
                match operation {
                    TableRulingOperation::DrawStroke { .. } => Self::build_draw_stroke(
                        request,
                        state,
                        grid,
                        grid_limits,
                        formula_limits,
                        limits,
                    ),
                    TableRulingOperation::DrawDiagonal { .. }
                    | TableRulingOperation::EraseDiagonal { .. } => {
                        Self::build_diagonal(request, state, grid, limits)
                    }
                    TableRulingOperation::EraseStroke { .. } => Self::build_erase_stroke(
                        request,
                        state,
                        grid,
                        grid_limits,
                        formula_limits,
                        limits,
                    ),
                    TableRulingOperation::DrawOuterRectangle { .. } => {
                        Err(TableRulingError::ContextMismatch)
                    }
                }
            }
        }
    }

    fn build_outer(
        request: &TableRulingRequest,
        grid_limits: TableGridLimits,
        limits: TableRulingLimits,
    ) -> Result<TableRulingPlan, TableRulingError> {
        let TableRulingOperation::DrawOuterRectangle {
            frame,
            initial_master_cell_id,
            table_properties_sha256,
            initial_cell_properties,
            line_sha256,
            insertion_context_sha256,
        } = &request.operation
        else {
            return Err(TableRulingError::ContextMismatch);
        };
        let grid = TableGrid::new(
            1,
            1,
            vec![TableCellSpan {
                master_cell_id: initial_master_cell_id.clone(),
                row: 0,
                column: 0,
                row_span: 1,
                column_span: 1,
            }],
            grid_limits,
        )?;
        let edges = vec![
            TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary: 0,
                offset: 0,
                line_sha256: Some(line_sha256.clone()),
            },
            TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary: 1,
                offset: 0,
                line_sha256: Some(line_sha256.clone()),
            },
            TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary: 0,
                offset: 0,
                line_sha256: Some(line_sha256.clone()),
            },
            TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary: 1,
                offset: 0,
                line_sha256: Some(line_sha256.clone()),
            },
        ];
        let cells = vec![TableRulingCell {
            master_cell_id: initial_master_cell_id.clone(),
            coordinate: CellCoordinate { row: 0, column: 0 },
            payload: Vec::new(),
            properties: initial_cell_properties.clone(),
            formula: None,
        }];
        let state = TableRulingState::from_validated_parts(
            request.table_id.clone(),
            *frame,
            table_properties_sha256.clone(),
            vec![0, frame.height_hwpunit],
            vec![0, frame.width_hwpunit],
            edges,
            cells,
            &grid,
            limits,
        )?;
        let after_state_sha256 = state_digest(&state, limits)?;
        let after_grid_sha256 = grid_digest(&grid)?;
        let plan = TableRulingPlan {
            schema_version: TABLE_RULING_SCHEMA_VERSION,
            capability_id: TABLE_DRAW_CAPABILITY_ID,
            plan_kind: TableRulingPlanKind::OuterRectangle,
            after_grid: TableRulingPlannedGrid::new(&grid)?,
            after_state: state,
            receipt: TableRulingReceipt {
                before_state_sha256: None,
                after_state_sha256,
                before_grid_sha256: None,
                after_grid_sha256,
                document_flow_sha256: request.expected_document_flow_sha256.clone(),
                insertion_context_sha256: Some(insertion_context_sha256.clone()),
                edge_change_count: 4,
                diagonal_change_count: 0,
                created_master_cell_count: 1,
                retired_master_cell_count: 0,
                structural_merge_count: 0,
                nonstructural_transparent_edge_count: 0,
                payload_block_preserved_count: 0,
                formula_preserved_count: 0,
                formula_rebased_count: 0,
                formula_cache_cleared_count: 0,
                topology_changed: true,
            },
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }

    #[allow(clippy::too_many_arguments)]
    fn build_draw_stroke(
        request: &TableRulingRequest,
        state: &TableRulingState,
        grid: &TableGrid,
        grid_limits: TableGridLimits,
        formula_limits: FormulaLimits,
        limits: TableRulingLimits,
    ) -> Result<TableRulingPlan, TableRulingError> {
        let TableRulingOperation::DrawStroke {
            stroke,
            line_sha256,
            new_master_cell_ids,
            formula_policy,
        } = &request.operation
        else {
            return Err(TableRulingError::ContextMismatch);
        };
        let (rows, columns) = expanded_lattice(state, *stroke)?;
        let lattice_refined = rows.len() != state.row_boundaries_hwpunit.len()
            || columns.len() != state.column_boundaries_hwpunit.len();
        let remapped_grid = remap_grid(grid, state, &rows, &columns, grid_limits)?;
        let mut edges = resample_edges(state, &rows, &columns, limits)?;
        let indexed = indexed_stroke(*stroke, &rows, &columns, false)?;
        let edge_change_count = set_stroke_line(&mut edges, &indexed, Some(line_sha256.as_str()))?;
        let (mapped_cells, formula_counts) = remap_cells_for_lattice(
            state,
            grid,
            &rows,
            &columns,
            *formula_policy,
            formula_limits,
        )?;
        let split = split_cells_by_stroke(
            &remapped_grid,
            &mapped_cells,
            &indexed,
            new_master_cell_ids,
            limits,
        )?;
        if split.created != 0 && !lattice_refined && formula_count(&state.cells) != 0 {
            return Err(TableRulingError::FormulaTopologyAmbiguous);
        }
        let after_grid = TableGrid::new(
            remapped_grid.rows(),
            remapped_grid.columns(),
            split.spans,
            grid_limits,
        )?;
        validate_drawn_stroke_topology(&after_grid, &indexed)?;
        let after_state = TableRulingState::from_validated_parts(
            state.table_id.clone(),
            state.frame,
            state.table_properties_sha256.clone(),
            rows,
            columns,
            edges,
            split.cells,
            &after_grid,
            limits,
        )?;
        if edge_change_count == 0 && split.created == 0 {
            return Err(TableRulingError::NoSemanticChange);
        }
        build_existing_plan(
            request,
            state,
            grid,
            after_state,
            &after_grid,
            TableRulingPlanKind::EdgeStroke,
            edge_change_count,
            0,
            split.created,
            0,
            0,
            0,
            formula_counts,
            limits,
        )
    }

    fn build_diagonal(
        request: &TableRulingRequest,
        state: &TableRulingState,
        grid: &TableGrid,
        limits: TableRulingLimits,
    ) -> Result<TableRulingPlan, TableRulingError> {
        let (master_cell_id, direction, line) = match &request.operation {
            TableRulingOperation::DrawDiagonal {
                master_cell_id,
                direction,
                line_sha256,
            } => (master_cell_id, *direction, Some(line_sha256.clone())),
            TableRulingOperation::EraseDiagonal {
                master_cell_id,
                direction,
            } => (master_cell_id, *direction, None),
            _ => return Err(TableRulingError::ContextMismatch),
        };
        let mut cells = state.cells.clone();
        let cell = cells
            .iter_mut()
            .find(|cell| cell.master_cell_id == *master_cell_id)
            .ok_or(TableRulingError::MasterCellNotFound)?;
        let target = match direction {
            TableRulingDiagonalDirection::Slash => &mut cell.properties.slash_diagonal_sha256,
            TableRulingDiagonalDirection::BackSlash => {
                &mut cell.properties.back_slash_diagonal_sha256
            }
        };
        if *target == line {
            return Err(TableRulingError::NoSemanticChange);
        }
        *target = line;
        let after_state = TableRulingState::from_validated_parts(
            state.table_id.clone(),
            state.frame,
            state.table_properties_sha256.clone(),
            state.row_boundaries_hwpunit.clone(),
            state.column_boundaries_hwpunit.clone(),
            state.edges.clone(),
            cells,
            grid,
            limits,
        )?;
        build_existing_plan(
            request,
            state,
            grid,
            after_state,
            grid,
            TableRulingPlanKind::Diagonal,
            0,
            1,
            0,
            0,
            0,
            0,
            FormulaCounts::default(),
            limits,
        )
    }

    #[allow(clippy::too_many_arguments)]
    fn build_erase_stroke(
        request: &TableRulingRequest,
        state: &TableRulingState,
        grid: &TableGrid,
        grid_limits: TableGridLimits,
        formula_limits: FormulaLimits,
        limits: TableRulingLimits,
    ) -> Result<TableRulingPlan, TableRulingError> {
        let TableRulingOperation::EraseStroke {
            stroke,
            formula_policy,
        } = &request.operation
        else {
            return Err(TableRulingError::ContextMismatch);
        };
        let indexed = indexed_stroke(
            *stroke,
            &state.row_boundaries_hwpunit,
            &state.column_boundaries_hwpunit,
            true,
        )?;
        let mut edges = state.edges.clone();
        let selected_line_changes = set_stroke_line(&mut edges, &indexed, None)?;
        let merged = merge_cells_across_stroke(
            grid,
            state,
            &indexed,
            &mut edges,
            *formula_policy,
            formula_limits,
            limits,
        )?;
        let after_grid = TableGrid::new(grid.rows(), grid.columns(), merged.spans, grid_limits)?;
        let after_state = TableRulingState::from_validated_parts(
            state.table_id.clone(),
            state.frame,
            state.table_properties_sha256.clone(),
            state.row_boundaries_hwpunit.clone(),
            state.column_boundaries_hwpunit.clone(),
            edges,
            merged.cells,
            &after_grid,
            limits,
        )?;
        let edge_change_count = selected_line_changes
            .checked_add(merged.normalized_line_changes)
            .ok_or(TableRulingError::CountOverflow)?;
        if edge_change_count == 0 && merged.retired == 0 {
            return Err(TableRulingError::NoSemanticChange);
        }
        build_existing_plan(
            request,
            state,
            grid,
            after_state,
            &after_grid,
            TableRulingPlanKind::EdgeStroke,
            edge_change_count,
            0,
            0,
            merged.retired,
            merged.merge_groups,
            merged.nonstructural_transparent,
            merged.formula_counts,
            limits,
        )
    }
}

#[allow(clippy::too_many_arguments)]
fn build_existing_plan(
    request: &TableRulingRequest,
    before_state: &TableRulingState,
    before_grid: &TableGrid,
    after_state: TableRulingState,
    after_grid: &TableGrid,
    plan_kind: TableRulingPlanKind,
    edge_change_count: usize,
    diagonal_change_count: usize,
    created_master_cell_count: usize,
    retired_master_cell_count: usize,
    structural_merge_count: usize,
    nonstructural_transparent_edge_count: usize,
    formula_counts: FormulaCounts,
    limits: TableRulingLimits,
) -> Result<TableRulingPlan, TableRulingError> {
    let before_payloads = payload_count(&before_state.cells)?;
    let after_payloads = payload_count(&after_state.cells)?;
    if before_payloads != after_payloads {
        return Err(TableRulingError::PayloadPreservationFailure);
    }
    let before_formulas = formula_count(&before_state.cells);
    if before_formulas != formula_count(&after_state.cells) {
        return Err(TableRulingError::FormulaPreservationFailure);
    }
    let receipt = TableRulingReceipt {
        before_state_sha256: Some(state_digest(before_state, limits)?),
        after_state_sha256: state_digest(&after_state, limits)?,
        before_grid_sha256: Some(grid_digest(before_grid)?),
        after_grid_sha256: grid_digest(after_grid)?,
        document_flow_sha256: request.expected_document_flow_sha256.clone(),
        insertion_context_sha256: None,
        edge_change_count,
        diagonal_change_count,
        created_master_cell_count,
        retired_master_cell_count,
        structural_merge_count,
        nonstructural_transparent_edge_count,
        payload_block_preserved_count: before_payloads,
        formula_preserved_count: before_formulas,
        formula_rebased_count: formula_counts.rebased,
        formula_cache_cleared_count: formula_counts.caches_cleared,
        topology_changed: created_master_cell_count != 0 || retired_master_cell_count != 0,
    };
    let plan = TableRulingPlan {
        schema_version: TABLE_RULING_SCHEMA_VERSION,
        capability_id: request.capability_id,
        plan_kind,
        after_grid: TableRulingPlannedGrid::new(after_grid)?,
        after_state,
        receipt,
    };
    let _ = plan.canonical_json(limits)?;
    Ok(plan)
}

fn validate_operation(
    operation: &TableRulingOperation,
    limits: TableRulingLimits,
) -> Result<(), TableRulingError> {
    match operation {
        TableRulingOperation::DrawOuterRectangle {
            frame,
            initial_master_cell_id,
            table_properties_sha256,
            initial_cell_properties,
            line_sha256,
            insertion_context_sha256,
        } => {
            validate_frame(*frame, limits)?;
            validate_identifier(initial_master_cell_id, limits)?;
            validate_digest(table_properties_sha256)?;
            validate_properties(initial_cell_properties)?;
            if initial_cell_properties.slash_diagonal_sha256.is_some()
                || initial_cell_properties.back_slash_diagonal_sha256.is_some()
            {
                return Err(TableRulingError::OuterRectangleDiagonalConflict);
            }
            validate_digest(line_sha256)?;
            validate_digest(insertion_context_sha256)?;
        }
        TableRulingOperation::DrawStroke {
            line_sha256,
            new_master_cell_ids,
            ..
        } => {
            validate_digest(line_sha256)?;
            if new_master_cell_ids.len() > limits.0.cells {
                return Err(TableRulingError::CellLimitExceeded);
            }
            let mut seen = HashSet::with_capacity(new_master_cell_ids.len());
            for identifier in new_master_cell_ids {
                validate_identifier(identifier, limits)?;
                if !seen.insert(identifier.clone()) {
                    return Err(TableRulingError::DuplicateNewMasterCell);
                }
            }
        }
        TableRulingOperation::DrawDiagonal {
            master_cell_id,
            line_sha256,
            ..
        } => {
            validate_identifier(master_cell_id, limits)?;
            validate_digest(line_sha256)?;
        }
        TableRulingOperation::EraseDiagonal { master_cell_id, .. } => {
            validate_identifier(master_cell_id, limits)?;
        }
        TableRulingOperation::EraseStroke { .. } => {}
    }
    Ok(())
}

fn validate_existing_operation(
    operation: &TableRulingOperation,
    state: &TableRulingState,
    grid: &TableGrid,
) -> Result<(), TableRulingError> {
    match operation {
        TableRulingOperation::DrawStroke {
            stroke,
            new_master_cell_ids,
            ..
        } => {
            validate_stroke(*stroke, state.frame)?;
            let existing: HashSet<_> = grid
                .master_cells()
                .iter()
                .map(|span| span.master_cell_id.clone())
                .collect();
            let payload_ids: HashSet<_> = state
                .cells
                .iter()
                .flat_map(|cell| cell.payload.iter().map(|block| block.block_id.clone()))
                .collect();
            if new_master_cell_ids.iter().any(|identifier| {
                existing.contains(identifier)
                    || payload_ids.contains(identifier)
                    || *identifier == state.table_id
            }) {
                return Err(TableRulingError::IdentifierCollision);
            }
        }
        TableRulingOperation::EraseStroke { stroke, .. } => {
            validate_stroke(*stroke, state.frame)?;
            let _ = indexed_stroke(
                *stroke,
                &state.row_boundaries_hwpunit,
                &state.column_boundaries_hwpunit,
                true,
            )?;
        }
        TableRulingOperation::DrawDiagonal { master_cell_id, .. }
        | TableRulingOperation::EraseDiagonal { master_cell_id, .. } => {
            if state.cell(master_cell_id).is_none() {
                return Err(TableRulingError::MasterCellNotFound);
            }
        }
        TableRulingOperation::DrawOuterRectangle { .. } => {
            return Err(TableRulingError::ContextMismatch);
        }
    }
    Ok(())
}

fn validate_existing_binding(
    table_id: &LogicalId,
    expected_state_sha256: &str,
    expected_grid_sha256: &str,
    state: &TableRulingState,
    grid: &TableGrid,
    limits: TableRulingLimits,
) -> Result<(), TableRulingError> {
    if *table_id != state.table_id
        || expected_state_sha256 != state_digest(state, limits)?
        || expected_grid_sha256 != grid_digest(grid)?
        || state.grid_sha256 != expected_grid_sha256
        || state.cells.len() != grid.master_cell_count()
    {
        return Err(TableRulingError::StateBindingMismatch);
    }
    Ok(())
}

fn validate_frame(
    frame: TableRulingFrame,
    limits: TableRulingLimits,
) -> Result<(), TableRulingError> {
    if frame.width_hwpunit == 0
        || frame.height_hwpunit == 0
        || frame.width_hwpunit > limits.0.dimension_hwpunit
        || frame.height_hwpunit > limits.0.dimension_hwpunit
        || frame
            .left_hwpunit
            .checked_add(frame.width_hwpunit)
            .is_none()
        || frame
            .top_hwpunit
            .checked_add(frame.height_hwpunit)
            .is_none()
    {
        return Err(TableRulingError::InvalidFrame);
    }
    Ok(())
}

fn validate_boundaries(
    boundaries: &[u32],
    tracks: u32,
    extent: u32,
) -> Result<(), TableRulingError> {
    let expected = usize::try_from(tracks)
        .ok()
        .and_then(|value| value.checked_add(1))
        .ok_or(TableRulingError::CountOverflow)?;
    if boundaries.len() != expected
        || boundaries.first() != Some(&0)
        || boundaries.last() != Some(&extent)
        || boundaries.windows(2).any(|pair| pair[0] >= pair[1])
    {
        return Err(TableRulingError::InvalidLattice);
    }
    Ok(())
}

fn validate_edges(
    mut edges: Vec<TableRulingEdge>,
    grid: &TableGrid,
    limits: TableRulingLimits,
) -> Result<Vec<TableRulingEdge>, TableRulingError> {
    let expected = expected_edge_count(grid.rows(), grid.columns())?;
    if edges.len() != expected {
        return Err(TableRulingError::EdgeSetMismatch);
    }
    if edges.len() > limits.0.edges {
        return Err(TableRulingError::EdgeLimitExceeded);
    }
    edges.sort_by_key(|edge| (edge.axis, edge.boundary, edge.offset));
    if edges.windows(2).any(|pair| {
        (pair[0].axis, pair[0].boundary, pair[0].offset)
            == (pair[1].axis, pair[1].boundary, pair[1].offset)
    }) {
        return Err(TableRulingError::DuplicateEdge);
    }
    let mut cursor = 0usize;
    for boundary in 0..=grid.rows() {
        for offset in 0..grid.columns() {
            validate_expected_edge(
                edges.get(cursor),
                TableRulingAxis::Horizontal,
                boundary,
                offset,
            )?;
            cursor = cursor
                .checked_add(1)
                .ok_or(TableRulingError::CountOverflow)?;
        }
    }
    for boundary in 0..=grid.columns() {
        for offset in 0..grid.rows() {
            validate_expected_edge(
                edges.get(cursor),
                TableRulingAxis::Vertical,
                boundary,
                offset,
            )?;
            cursor = cursor
                .checked_add(1)
                .ok_or(TableRulingError::CountOverflow)?;
        }
    }
    for edge in &edges {
        validate_optional_digest(edge.line_sha256.as_deref())?;
    }
    Ok(edges)
}

fn validate_expected_edge(
    edge: Option<&TableRulingEdge>,
    axis: TableRulingAxis,
    boundary: u32,
    offset: u32,
) -> Result<(), TableRulingError> {
    if edge.is_none_or(|edge| (edge.axis, edge.boundary, edge.offset) != (axis, boundary, offset)) {
        return Err(TableRulingError::EdgeSetMismatch);
    }
    Ok(())
}

fn validate_cells(
    mut drafts: Vec<TableRulingCellDraft>,
    grid: &TableGrid,
    formula_limits: FormulaLimits,
    limits: TableRulingLimits,
) -> Result<Vec<TableRulingCell>, TableRulingError> {
    if drafts.len() != grid.master_cell_count() || drafts.len() > limits.0.cells {
        return Err(TableRulingError::CellSetMismatch);
    }
    drafts.sort_by(|left, right| {
        (left.coordinate, &left.master_cell_id).cmp(&(right.coordinate, &right.master_cell_id))
    });
    let dimensions = dimensions(grid);
    let mut cells = fallible_vec(drafts.len())?;
    for (draft, span) in drafts.into_iter().zip(grid.master_cells()) {
        if draft.master_cell_id != span.master_cell_id || draft.coordinate != span_coordinate(span)
        {
            return Err(TableRulingError::CellSetMismatch);
        }
        validate_identifier(&draft.master_cell_id, limits)?;
        validate_properties(&draft.properties)?;
        let formula = draft
            .formula
            .map(|formula| FormulaCell::from_draft(formula, dimensions, formula_limits))
            .transpose()?;
        if formula
            .as_ref()
            .is_some_and(|formula| formula.owner() != draft.coordinate)
        {
            return Err(TableRulingError::FormulaOwnerMismatch);
        }
        cells.push(TableRulingCell {
            master_cell_id: draft.master_cell_id,
            coordinate: draft.coordinate,
            payload: draft.payload,
            properties: draft.properties,
            formula,
        });
    }
    validate_validated_cells(&mut cells, grid, limits)?;
    Ok(cells)
}

fn validate_validated_cells(
    cells: &mut [TableRulingCell],
    grid: &TableGrid,
    limits: TableRulingLimits,
) -> Result<(), TableRulingError> {
    if cells.len() != grid.master_cell_count() || cells.len() > limits.0.cells {
        return Err(TableRulingError::CellSetMismatch);
    }
    cells.sort_by(|left, right| {
        (left.coordinate, &left.master_cell_id).cmp(&(right.coordinate, &right.master_cell_id))
    });
    let mut block_ids = HashSet::new();
    let mut payload_blocks = 0usize;
    for (cell, span) in cells.iter().zip(grid.master_cells()) {
        if cell.master_cell_id != span.master_cell_id || cell.coordinate != span_coordinate(span) {
            return Err(TableRulingError::CellSetMismatch);
        }
        validate_identifier(&cell.master_cell_id, limits)?;
        validate_properties(&cell.properties)?;
        if cell
            .formula
            .as_ref()
            .is_some_and(|formula| formula.owner() != cell.coordinate)
        {
            return Err(TableRulingError::FormulaOwnerMismatch);
        }
        payload_blocks = payload_blocks
            .checked_add(cell.payload.len())
            .ok_or(TableRulingError::CountOverflow)?;
        if payload_blocks > limits.0.payload_blocks {
            return Err(TableRulingError::PayloadBlockLimitExceeded);
        }
        for block in &cell.payload {
            validate_identifier(&block.block_id, limits)?;
            validate_digest(&block.payload_sha256)?;
            if !block_ids.insert(block.block_id.clone()) {
                return Err(TableRulingError::DuplicatePayloadBlock);
            }
        }
    }
    Ok(())
}

fn validate_properties(value: &TableRulingCellProperties) -> Result<(), TableRulingError> {
    validate_digest(&value.non_ruling_properties_sha256)?;
    validate_optional_digest(value.background_sha256.as_deref())?;
    validate_optional_digest(value.slash_diagonal_sha256.as_deref())?;
    validate_optional_digest(value.back_slash_diagonal_sha256.as_deref())
}

fn validate_global_identities(
    table_id: &LogicalId,
    cells: &[TableRulingCell],
) -> Result<(), TableRulingError> {
    let master_ids: HashSet<_> = cells
        .iter()
        .map(|cell| cell.master_cell_id.clone())
        .collect();
    if master_ids.contains(table_id)
        || cells.iter().any(|cell| {
            cell.payload
                .iter()
                .any(|block| block.block_id == *table_id || master_ids.contains(&block.block_id))
        })
    {
        return Err(TableRulingError::IdentifierCollision);
    }
    Ok(())
}

fn validate_stroke(
    stroke: TableRulingStroke,
    frame: TableRulingFrame,
) -> Result<(), TableRulingError> {
    let (fixed_limit, run_limit) = match stroke.axis {
        TableRulingAxis::Horizontal => (frame.height_hwpunit, frame.width_hwpunit),
        TableRulingAxis::Vertical => (frame.width_hwpunit, frame.height_hwpunit),
    };
    if stroke.start_hwpunit >= stroke.end_hwpunit
        || stroke.fixed_hwpunit > fixed_limit
        || stroke.end_hwpunit > run_limit
    {
        return Err(TableRulingError::InvalidStroke);
    }
    Ok(())
}

fn expanded_lattice(
    state: &TableRulingState,
    stroke: TableRulingStroke,
) -> Result<(Vec<u32>, Vec<u32>), TableRulingError> {
    validate_stroke(stroke, state.frame)?;
    let mut rows = state.row_boundaries_hwpunit.clone();
    let mut columns = state.column_boundaries_hwpunit.clone();
    match stroke.axis {
        TableRulingAxis::Horizontal => {
            insert_boundary(&mut rows, stroke.fixed_hwpunit);
            insert_boundary(&mut columns, stroke.start_hwpunit);
            insert_boundary(&mut columns, stroke.end_hwpunit);
        }
        TableRulingAxis::Vertical => {
            insert_boundary(&mut columns, stroke.fixed_hwpunit);
            insert_boundary(&mut rows, stroke.start_hwpunit);
            insert_boundary(&mut rows, stroke.end_hwpunit);
        }
    }
    Ok((rows, columns))
}

fn insert_boundary(boundaries: &mut Vec<u32>, value: u32) {
    if let Err(index) = boundaries.binary_search(&value) {
        boundaries.insert(index, value);
    }
}

#[derive(Clone, Copy, Debug)]
struct IndexedStroke {
    axis: TableRulingAxis,
    boundary: u32,
    start: u32,
    end: u32,
}

fn indexed_stroke(
    stroke: TableRulingStroke,
    rows: &[u32],
    columns: &[u32],
    require_existing: bool,
) -> Result<IndexedStroke, TableRulingError> {
    let lookup = |values: &[u32], value: u32| {
        values
            .binary_search(&value)
            .map_err(|_| TableRulingError::EraserOffRuling)
    };
    let (boundary, start, end) = match stroke.axis {
        TableRulingAxis::Horizontal => (
            lookup(rows, stroke.fixed_hwpunit)?,
            lookup(columns, stroke.start_hwpunit)?,
            lookup(columns, stroke.end_hwpunit)?,
        ),
        TableRulingAxis::Vertical => (
            lookup(columns, stroke.fixed_hwpunit)?,
            lookup(rows, stroke.start_hwpunit)?,
            lookup(rows, stroke.end_hwpunit)?,
        ),
    };
    if require_existing && start == end {
        return Err(TableRulingError::EraserOffRuling);
    }
    Ok(IndexedStroke {
        axis: stroke.axis,
        boundary: u32::try_from(boundary).map_err(|_| TableRulingError::CountOverflow)?,
        start: u32::try_from(start).map_err(|_| TableRulingError::CountOverflow)?,
        end: u32::try_from(end).map_err(|_| TableRulingError::CountOverflow)?,
    })
}

fn remap_grid(
    grid: &TableGrid,
    state: &TableRulingState,
    rows: &[u32],
    columns: &[u32],
    grid_limits: TableGridLimits,
) -> Result<TableGrid, TableRulingError> {
    let mut spans = fallible_vec(grid.master_cell_count())?;
    for span in grid.master_cells() {
        let old_row_end = span
            .row
            .checked_add(span.row_span)
            .ok_or(TableRulingError::CountOverflow)?;
        let old_column_end = span
            .column
            .checked_add(span.column_span)
            .ok_or(TableRulingError::CountOverflow)?;
        let row = mapped_boundary(
            rows,
            boundary_value(&state.row_boundaries_hwpunit, span.row)?,
        )?;
        let row_end = mapped_boundary(
            rows,
            boundary_value(&state.row_boundaries_hwpunit, old_row_end)?,
        )?;
        let column = mapped_boundary(
            columns,
            boundary_value(&state.column_boundaries_hwpunit, span.column)?,
        )?;
        let column_end = mapped_boundary(
            columns,
            boundary_value(&state.column_boundaries_hwpunit, old_column_end)?,
        )?;
        spans.push(TableCellSpan {
            master_cell_id: span.master_cell_id.clone(),
            row,
            column,
            row_span: row_end
                .checked_sub(row)
                .ok_or(TableRulingError::InvalidLattice)?,
            column_span: column_end
                .checked_sub(column)
                .ok_or(TableRulingError::InvalidLattice)?,
        });
    }
    TableGrid::new(
        track_count(rows)?,
        track_count(columns)?,
        spans,
        grid_limits,
    )
    .map_err(TableRulingError::from)
}

fn resample_edges(
    state: &TableRulingState,
    rows: &[u32],
    columns: &[u32],
    limits: TableRulingLimits,
) -> Result<Vec<TableRulingEdge>, TableRulingError> {
    let new_rows = track_count(rows)?;
    let new_columns = track_count(columns)?;
    let capacity = expected_edge_count(new_rows, new_columns)?;
    if capacity > limits.0.edges {
        return Err(TableRulingError::EdgeLimitExceeded);
    }
    let mut edges = fallible_vec(capacity)?;
    for boundary in 0..=new_rows {
        let y = boundary_value(rows, boundary)?;
        let old_boundary = state.row_boundaries_hwpunit.binary_search(&y).ok();
        for offset in 0..new_columns {
            let line_sha256 = if let Some(old_boundary) = old_boundary {
                let x = boundary_value(columns, offset)?;
                let old_offset = containing_track(&state.column_boundaries_hwpunit, x)?;
                state
                    .edge(
                        TableRulingAxis::Horizontal,
                        u32::try_from(old_boundary).map_err(|_| TableRulingError::CountOverflow)?,
                        old_offset,
                    )
                    .ok_or(TableRulingError::EdgeSetMismatch)?
                    .line_sha256
                    .clone()
            } else {
                None
            };
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256,
            });
        }
    }
    for boundary in 0..=new_columns {
        let x = boundary_value(columns, boundary)?;
        let old_boundary = state.column_boundaries_hwpunit.binary_search(&x).ok();
        for offset in 0..new_rows {
            let line_sha256 = if let Some(old_boundary) = old_boundary {
                let y = boundary_value(rows, offset)?;
                let old_offset = containing_track(&state.row_boundaries_hwpunit, y)?;
                state
                    .edge(
                        TableRulingAxis::Vertical,
                        u32::try_from(old_boundary).map_err(|_| TableRulingError::CountOverflow)?,
                        old_offset,
                    )
                    .ok_or(TableRulingError::EdgeSetMismatch)?
                    .line_sha256
                    .clone()
            } else {
                None
            };
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256,
            });
        }
    }
    Ok(edges)
}

fn set_stroke_line(
    edges: &mut [TableRulingEdge],
    stroke: &IndexedStroke,
    value: Option<&str>,
) -> Result<usize, TableRulingError> {
    let mut changed = 0usize;
    for offset in stroke.start..stroke.end {
        let edge = edge_mut(edges, stroke.axis, stroke.boundary, offset)?;
        if edge.line_sha256.as_deref() != value {
            edge.line_sha256 = value.map(str::to_owned);
            changed = changed
                .checked_add(1)
                .ok_or(TableRulingError::CountOverflow)?;
        }
    }
    Ok(changed)
}

fn edge_mut(
    edges: &mut [TableRulingEdge],
    axis: TableRulingAxis,
    boundary: u32,
    offset: u32,
) -> Result<&mut TableRulingEdge, TableRulingError> {
    let index = edges
        .binary_search_by_key(&(axis, boundary, offset), |edge| {
            (edge.axis, edge.boundary, edge.offset)
        })
        .map_err(|_| TableRulingError::EdgeSetMismatch)?;
    edges
        .get_mut(index)
        .ok_or(TableRulingError::EdgeSetMismatch)
}

fn remap_cells_for_lattice(
    state: &TableRulingState,
    grid: &TableGrid,
    rows: &[u32],
    columns: &[u32],
    policy: TableRulingFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<(Vec<TableRulingCell>, FormulaCounts), TableRulingError> {
    let original = state.cells.clone();
    let mut cells = original.clone();
    let mut dimensions = dimensions(grid);
    for (index, value) in rows.iter().enumerate().skip(1).take(rows.len() - 2) {
        if state.row_boundaries_hwpunit.binary_search(value).is_err() {
            let edit = FormulaGridEdit::InsertRows {
                before: dimensions,
                index: u32::try_from(index).map_err(|_| TableRulingError::CountOverflow)?,
                count: 1,
            };
            apply_formula_edit_to_cells(&mut cells, edit, policy, formula_limits)?;
            dimensions.rows = dimensions
                .rows
                .checked_add(1)
                .ok_or(TableRulingError::CountOverflow)?;
        }
    }
    for (index, value) in columns.iter().enumerate().skip(1).take(columns.len() - 2) {
        if state
            .column_boundaries_hwpunit
            .binary_search(value)
            .is_err()
        {
            let edit = FormulaGridEdit::InsertColumns {
                before: dimensions,
                index: u32::try_from(index).map_err(|_| TableRulingError::CountOverflow)?,
                count: 1,
            };
            apply_formula_edit_to_cells(&mut cells, edit, policy, formula_limits)?;
            dimensions.columns = dimensions
                .columns
                .checked_add(1)
                .ok_or(TableRulingError::CountOverflow)?;
        }
    }
    for (cell, original_cell) in cells.iter_mut().zip(&original) {
        let old_span = grid
            .master_cell_at(original_cell.coordinate)
            .map_err(TableRulingError::from)?;
        cell.coordinate = CellCoordinate {
            row: mapped_boundary(
                rows,
                boundary_value(&state.row_boundaries_hwpunit, old_span.row)?,
            )?,
            column: mapped_boundary(
                columns,
                boundary_value(&state.column_boundaries_hwpunit, old_span.column)?,
            )?,
        };
        if cell
            .formula
            .as_ref()
            .is_some_and(|formula| formula.owner() != cell.coordinate)
        {
            return Err(TableRulingError::FormulaOwnerMismatch);
        }
    }
    let counts = compare_formula_counts(&original, &cells)?;
    Ok((cells, counts))
}

fn apply_formula_edit_to_cells(
    cells: &mut [TableRulingCell],
    edit: FormulaGridEdit,
    policy: TableRulingFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<(), TableRulingError> {
    for cell in cells {
        if let Some(formula) = &cell.formula {
            cell.formula = Some(apply_formula_edit(formula, edit, policy, formula_limits)?);
        }
    }
    Ok(())
}

fn apply_formula_edit(
    formula: &FormulaCell,
    edit: FormulaGridEdit,
    policy: TableRulingFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<FormulaCell, TableRulingError> {
    match formula.apply_grid_edit(edit, FormulaCachePolicy::Preserve, None, formula_limits) {
        Ok(value) => Ok(value),
        Err(FormulaError::CachePreservationConflict)
            if policy == TableRulingFormulaPolicy::RebaseAndClearTopologyStaleCache =>
        {
            formula
                .apply_grid_edit(edit, FormulaCachePolicy::Clear, None, formula_limits)
                .map_err(TableRulingError::from)
        }
        Err(FormulaError::CachePreservationConflict) => {
            Err(TableRulingError::FormulaRebaseRequired)
        }
        Err(error) => Err(TableRulingError::Formula(error)),
    }
}

struct SplitBuild {
    spans: Vec<TableCellSpan>,
    cells: Vec<TableRulingCell>,
    created: usize,
}

fn split_cells_by_stroke(
    grid: &TableGrid,
    cells: &[TableRulingCell],
    stroke: &IndexedStroke,
    new_master_cell_ids: &[LogicalId],
    limits: TableRulingLimits,
) -> Result<SplitBuild, TableRulingError> {
    let mut spans = fallible_vec(
        grid.master_cell_count()
            .checked_add(new_master_cell_ids.len())
            .ok_or(TableRulingError::CountOverflow)?,
    )?;
    let mut output_cells = fallible_vec(spans.capacity())?;
    let mut id_cursor = 0usize;
    for (span, cell) in grid.master_cells().iter().zip(cells) {
        let components = components_for_span(span, stroke)?;
        if components.len() > 1
            && (cell.properties.slash_diagonal_sha256.is_some()
                || cell.properties.back_slash_diagonal_sha256.is_some())
        {
            return Err(TableRulingError::DiagonalSplitConflict);
        }
        for component in &components {
            let retained = component.row == span.row && component.column == span.column;
            let identifier = if retained {
                cell.master_cell_id.clone()
            } else {
                let identifier = new_master_cell_ids
                    .get(id_cursor)
                    .ok_or(TableRulingError::NewMasterCellCountMismatch)?
                    .clone();
                id_cursor = id_cursor
                    .checked_add(1)
                    .ok_or(TableRulingError::CountOverflow)?;
                identifier
            };
            spans.push(TableCellSpan {
                master_cell_id: identifier.clone(),
                row: component.row,
                column: component.column,
                row_span: component.row_span,
                column_span: component.column_span,
            });
            output_cells.push(if retained {
                TableRulingCell {
                    master_cell_id: identifier,
                    coordinate: CellCoordinate {
                        row: component.row,
                        column: component.column,
                    },
                    payload: cell.payload.clone(),
                    properties: cell.properties.clone(),
                    formula: cell.formula.clone(),
                }
            } else {
                TableRulingCell {
                    master_cell_id: identifier,
                    coordinate: CellCoordinate {
                        row: component.row,
                        column: component.column,
                    },
                    payload: Vec::new(),
                    properties: TableRulingCellProperties {
                        non_ruling_properties_sha256: cell
                            .properties
                            .non_ruling_properties_sha256
                            .clone(),
                        background_sha256: cell.properties.background_sha256.clone(),
                        slash_diagonal_sha256: None,
                        back_slash_diagonal_sha256: None,
                    },
                    formula: None,
                }
            });
        }
    }
    if id_cursor != new_master_cell_ids.len() || output_cells.len() > limits.0.cells {
        return Err(TableRulingError::NewMasterCellCountMismatch);
    }
    Ok(SplitBuild {
        spans,
        cells: output_cells,
        created: id_cursor,
    })
}

fn components_for_span(
    span: &TableCellSpan,
    stroke: &IndexedStroke,
) -> Result<Vec<TableCellSpan>, TableRulingError> {
    let slot_count = product(span.row_span, span.column_span)?;
    let mut visited = vec![false; slot_count];
    let mut components = Vec::new();
    for local_row in 0..span.row_span {
        for local_column in 0..span.column_span {
            let index = local_index(local_row, local_column, span.column_span)?;
            if visited[index] {
                continue;
            }
            visited[index] = true;
            let start = CellCoordinate {
                row: span.row + local_row,
                column: span.column + local_column,
            };
            let mut queue = VecDeque::from([start]);
            let mut min_row = start.row;
            let mut max_row = start.row;
            let mut min_column = start.column;
            let mut max_column = start.column;
            let mut count = 0usize;
            while let Some(current) = queue.pop_front() {
                count = count
                    .checked_add(1)
                    .ok_or(TableRulingError::CountOverflow)?;
                min_row = min_row.min(current.row);
                max_row = max_row.max(current.row);
                min_column = min_column.min(current.column);
                max_column = max_column.max(current.column);
                for neighbor in neighbors(current, span)? {
                    if stroke_blocks(current, neighbor, stroke) {
                        continue;
                    }
                    let neighbor_index = local_index(
                        neighbor.row - span.row,
                        neighbor.column - span.column,
                        span.column_span,
                    )?;
                    if !visited[neighbor_index] {
                        visited[neighbor_index] = true;
                        queue.push_back(neighbor);
                    }
                }
            }
            let row_span = max_row - min_row + 1;
            let column_span = max_column - min_column + 1;
            if product(row_span, column_span)? != count {
                return Err(TableRulingError::NonRectangularSplit);
            }
            components.push(TableCellSpan {
                master_cell_id: span.master_cell_id.clone(),
                row: min_row,
                column: min_column,
                row_span,
                column_span,
            });
        }
    }
    components.sort_by_key(|component| (component.row, component.column));
    Ok(components)
}

fn neighbors(
    coordinate: CellCoordinate,
    span: &TableCellSpan,
) -> Result<Vec<CellCoordinate>, TableRulingError> {
    let row_end = span
        .row
        .checked_add(span.row_span)
        .ok_or(TableRulingError::CountOverflow)?;
    let column_end = span
        .column
        .checked_add(span.column_span)
        .ok_or(TableRulingError::CountOverflow)?;
    let mut values = Vec::with_capacity(4);
    if coordinate.row > span.row {
        values.push(CellCoordinate {
            row: coordinate.row - 1,
            column: coordinate.column,
        });
    }
    if coordinate.row + 1 < row_end {
        values.push(CellCoordinate {
            row: coordinate.row + 1,
            column: coordinate.column,
        });
    }
    if coordinate.column > span.column {
        values.push(CellCoordinate {
            row: coordinate.row,
            column: coordinate.column - 1,
        });
    }
    if coordinate.column + 1 < column_end {
        values.push(CellCoordinate {
            row: coordinate.row,
            column: coordinate.column + 1,
        });
    }
    Ok(values)
}

fn stroke_blocks(left: CellCoordinate, right: CellCoordinate, stroke: &IndexedStroke) -> bool {
    match stroke.axis {
        TableRulingAxis::Horizontal if left.column == right.column => {
            let boundary = left.row.max(right.row);
            boundary == stroke.boundary && left.column >= stroke.start && left.column < stroke.end
        }
        TableRulingAxis::Vertical if left.row == right.row => {
            let boundary = left.column.max(right.column);
            boundary == stroke.boundary && left.row >= stroke.start && left.row < stroke.end
        }
        _ => false,
    }
}

fn validate_drawn_stroke_topology(
    grid: &TableGrid,
    stroke: &IndexedStroke,
) -> Result<(), TableRulingError> {
    for offset in stroke.start..stroke.end {
        if let Some((left, right)) = adjacent_cells(grid, stroke.axis, stroke.boundary, offset)?
            && left.master_cell_id == right.master_cell_id
        {
            return Err(TableRulingError::NonRectangularSplit);
        }
    }
    Ok(())
}

struct MergeBuild {
    spans: Vec<TableCellSpan>,
    cells: Vec<TableRulingCell>,
    retired: usize,
    merge_groups: usize,
    nonstructural_transparent: usize,
    normalized_line_changes: usize,
    formula_counts: FormulaCounts,
}

#[allow(clippy::too_many_arguments)]
fn merge_cells_across_stroke(
    grid: &TableGrid,
    state: &TableRulingState,
    stroke: &IndexedStroke,
    edges: &mut [TableRulingEdge],
    formula_policy: TableRulingFormulaPolicy,
    formula_limits: FormulaLimits,
    limits: TableRulingLimits,
) -> Result<MergeBuild, TableRulingError> {
    let (mut groups, nonstructural) = erased_groups(grid, stroke)?;
    let mut spans = fallible_vec(groups.len())?;
    let mut cells = fallible_vec(groups.len())?;
    let mut retired = 0usize;
    let mut merge_groups = 0usize;
    let mut normalized_line_changes = 0usize;
    let mut formula_counts = FormulaCounts::default();
    for indexes in groups.values_mut() {
        indexes.sort_unstable_by_key(|index| {
            let span = &grid.master_cells()[*index];
            (span.row, span.column)
        });
        if indexes.len() == 1 {
            let index = indexes[0];
            spans.push(grid.master_cells()[index].clone());
            cells.push(state.cells[index].clone());
            continue;
        }
        let merged =
            build_merged_group(grid, state, indexes, edges, formula_policy, formula_limits)?;
        spans.push(merged.span);
        cells.push(merged.cell);
        retired = retired
            .checked_add(merged.retired)
            .ok_or(TableRulingError::CountOverflow)?;
        merge_groups = merge_groups
            .checked_add(1)
            .ok_or(TableRulingError::CountOverflow)?;
        normalized_line_changes = normalized_line_changes
            .checked_add(merged.normalized_line_changes)
            .ok_or(TableRulingError::CountOverflow)?;
        formula_counts.rebased = formula_counts
            .rebased
            .checked_add(merged.formula_counts.rebased)
            .ok_or(TableRulingError::CountOverflow)?;
        formula_counts.caches_cleared = formula_counts
            .caches_cleared
            .checked_add(merged.formula_counts.caches_cleared)
            .ok_or(TableRulingError::CountOverflow)?;
    }
    if cells.len() > limits.0.cells {
        return Err(TableRulingError::CellLimitExceeded);
    }
    if retired != 0 {
        formula_counts.caches_cleared = formula_counts
            .caches_cleared
            .checked_add(clear_formula_caches_for_topology_change(
                &mut cells,
                dimensions(grid),
                formula_policy,
                formula_limits,
            )?)
            .ok_or(TableRulingError::CountOverflow)?;
    }
    Ok(MergeBuild {
        spans,
        cells,
        retired,
        merge_groups,
        nonstructural_transparent: nonstructural,
        normalized_line_changes,
        formula_counts,
    })
}

fn erased_groups(
    grid: &TableGrid,
    stroke: &IndexedStroke,
) -> Result<(BTreeMap<usize, Vec<usize>>, usize), TableRulingError> {
    let mut parent: Vec<usize> = (0..grid.master_cell_count()).collect();
    let index_by_id: HashMap<_, _> = grid
        .master_cells()
        .iter()
        .enumerate()
        .map(|(index, span)| (span.master_cell_id.clone(), index))
        .collect();
    let mut nonstructural = 0usize;
    for offset in stroke.start..stroke.end {
        let adjacent = adjacent_cells(grid, stroke.axis, stroke.boundary, offset)?;
        match adjacent {
            Some((left, right)) if left.master_cell_id != right.master_cell_id => {
                let left_index = *index_by_id
                    .get(&left.master_cell_id)
                    .ok_or(TableRulingError::CellSetMismatch)?;
                let right_index = *index_by_id
                    .get(&right.master_cell_id)
                    .ok_or(TableRulingError::CellSetMismatch)?;
                union(&mut parent, left_index, right_index);
            }
            _ => {
                nonstructural = nonstructural
                    .checked_add(1)
                    .ok_or(TableRulingError::CountOverflow)?;
            }
        }
    }
    let mut groups: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for index in 0..parent.len() {
        let root = find(&mut parent, index);
        groups.entry(root).or_default().push(index);
    }
    Ok((groups, nonstructural))
}

struct MergedGroup {
    span: TableCellSpan,
    cell: TableRulingCell,
    retired: usize,
    normalized_line_changes: usize,
    formula_counts: FormulaCounts,
}

fn build_merged_group(
    grid: &TableGrid,
    state: &TableRulingState,
    indexes: &[usize],
    edges: &mut [TableRulingEdge],
    formula_policy: TableRulingFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<MergedGroup, TableRulingError> {
    let rectangle = group_rectangle(grid, indexes)?;
    let survivor = &state.cells[indexes[0]];
    validate_merge_properties(state, indexes, survivor)?;
    let formula_indexes: Vec<_> = indexes
        .iter()
        .copied()
        .filter(|index| state.cells[*index].formula.is_some())
        .collect();
    if formula_indexes.len() > 1 {
        return Err(TableRulingError::MultipleFormulaMerge);
    }
    let mut payload = Vec::new();
    for index in indexes.iter().copied() {
        payload
            .try_reserve(state.cells[index].payload.len())
            .map_err(|_| TableRulingError::AllocationFailed)?;
        payload.extend(state.cells[index].payload.iter().cloned());
    }
    let coordinate = CellCoordinate {
        row: rectangle.row,
        column: rectangle.column,
    };
    let (formula, formula_counts) = merge_formula(
        state,
        &formula_indexes,
        coordinate,
        dimensions(grid),
        formula_policy,
        formula_limits,
    )?;
    let span = TableCellSpan {
        master_cell_id: survivor.master_cell_id.clone(),
        row: rectangle.row,
        column: rectangle.column,
        row_span: rectangle.row_span,
        column_span: rectangle.column_span,
    };
    let cell = TableRulingCell {
        master_cell_id: survivor.master_cell_id.clone(),
        coordinate,
        payload,
        properties: survivor.properties.clone(),
        formula,
    };
    Ok(MergedGroup {
        span,
        cell,
        retired: indexes.len() - 1,
        normalized_line_changes: clear_internal_edges(edges, &rectangle)?,
        formula_counts,
    })
}

fn validate_merge_properties(
    state: &TableRulingState,
    indexes: &[usize],
    survivor: &TableRulingCell,
) -> Result<(), TableRulingError> {
    if indexes.iter().any(|index| {
        state.cells[*index].properties.non_ruling_properties_sha256
            != survivor.properties.non_ruling_properties_sha256
            || state.cells[*index].properties.background_sha256
                != survivor.properties.background_sha256
    }) {
        return Err(TableRulingError::CellPropertiesConflict);
    }
    if indexes.iter().any(|index| {
        state.cells[*index]
            .properties
            .slash_diagonal_sha256
            .is_some()
            || state.cells[*index]
                .properties
                .back_slash_diagonal_sha256
                .is_some()
    }) {
        return Err(TableRulingError::DiagonalMergeConflict);
    }
    Ok(())
}

fn merge_formula(
    state: &TableRulingState,
    formula_indexes: &[usize],
    coordinate: CellCoordinate,
    dimensions: FormulaGridDimensions,
    formula_policy: TableRulingFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<(Option<FormulaCell>, FormulaCounts), TableRulingError> {
    let Some(index) = formula_indexes.first().copied() else {
        return Ok((None, FormulaCounts::default()));
    };
    let original = state.cells[index]
        .formula
        .as_ref()
        .ok_or(TableRulingError::FormulaPreservationFailure)?;
    let moved = if original.owner() == coordinate {
        original.clone()
    } else {
        rebase_formula(
            original,
            coordinate,
            dimensions,
            formula_policy,
            formula_limits,
        )?
    };
    Ok((
        Some(moved.clone()),
        FormulaCounts {
            rebased: usize::from(moved != *original),
            caches_cleared: usize::from(
                !matches!(original.cache(), FormulaCache::Absent)
                    && matches!(moved.cache(), FormulaCache::Absent),
            ),
        },
    ))
}

fn adjacent_cells(
    grid: &TableGrid,
    axis: TableRulingAxis,
    boundary: u32,
    offset: u32,
) -> Result<Option<(&TableCellSpan, &TableCellSpan)>, TableRulingError> {
    match axis {
        TableRulingAxis::Horizontal => {
            if boundary == 0 || boundary >= grid.rows() {
                return Ok(None);
            }
            Ok(Some((
                grid.master_cell_at(CellCoordinate {
                    row: boundary - 1,
                    column: offset,
                })?,
                grid.master_cell_at(CellCoordinate {
                    row: boundary,
                    column: offset,
                })?,
            )))
        }
        TableRulingAxis::Vertical => {
            if boundary == 0 || boundary >= grid.columns() {
                return Ok(None);
            }
            Ok(Some((
                grid.master_cell_at(CellCoordinate {
                    row: offset,
                    column: boundary - 1,
                })?,
                grid.master_cell_at(CellCoordinate {
                    row: offset,
                    column: boundary,
                })?,
            )))
        }
    }
}

fn group_rectangle(grid: &TableGrid, indexes: &[usize]) -> Result<TableCellSpan, TableRulingError> {
    let first = grid
        .master_cells()
        .get(indexes[0])
        .ok_or(TableRulingError::CellSetMismatch)?;
    let mut min_row = first.row;
    let mut min_column = first.column;
    let mut max_row = first.row + first.row_span;
    let mut max_column = first.column + first.column_span;
    let mut slots = 0usize;
    for index in indexes {
        let span = grid
            .master_cells()
            .get(*index)
            .ok_or(TableRulingError::CellSetMismatch)?;
        min_row = min_row.min(span.row);
        min_column = min_column.min(span.column);
        max_row = max_row.max(
            span.row
                .checked_add(span.row_span)
                .ok_or(TableRulingError::CountOverflow)?,
        );
        max_column = max_column.max(
            span.column
                .checked_add(span.column_span)
                .ok_or(TableRulingError::CountOverflow)?,
        );
        slots = slots
            .checked_add(product(span.row_span, span.column_span)?)
            .ok_or(TableRulingError::CountOverflow)?;
    }
    let row_span = max_row - min_row;
    let column_span = max_column - min_column;
    if product(row_span, column_span)? != slots {
        return Err(TableRulingError::NonRectangularMerge);
    }
    Ok(TableCellSpan {
        master_cell_id: first.master_cell_id.clone(),
        row: min_row,
        column: min_column,
        row_span,
        column_span,
    })
}

fn clear_internal_edges(
    edges: &mut [TableRulingEdge],
    rectangle: &TableCellSpan,
) -> Result<usize, TableRulingError> {
    let mut changed = 0usize;
    let row_end = rectangle.row + rectangle.row_span;
    let column_end = rectangle.column + rectangle.column_span;
    for boundary in rectangle.row + 1..row_end {
        for offset in rectangle.column..column_end {
            let edge = edge_mut(edges, TableRulingAxis::Horizontal, boundary, offset)?;
            if edge.line_sha256.take().is_some() {
                changed += 1;
            }
        }
    }
    for boundary in rectangle.column + 1..column_end {
        for offset in rectangle.row..row_end {
            let edge = edge_mut(edges, TableRulingAxis::Vertical, boundary, offset)?;
            if edge.line_sha256.take().is_some() {
                changed += 1;
            }
        }
    }
    Ok(changed)
}

fn rebase_formula(
    formula: &FormulaCell,
    to: CellCoordinate,
    dimensions: FormulaGridDimensions,
    policy: TableRulingFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<FormulaCell, TableRulingError> {
    match formula.rebase(
        to,
        dimensions,
        FormulaCachePolicy::Preserve,
        None,
        formula_limits,
    ) {
        Ok(value) => Ok(value),
        Err(FormulaError::CachePreservationConflict)
            if policy == TableRulingFormulaPolicy::RebaseAndClearTopologyStaleCache =>
        {
            formula
                .rebase(
                    to,
                    dimensions,
                    FormulaCachePolicy::Clear,
                    None,
                    formula_limits,
                )
                .map_err(TableRulingError::from)
        }
        Err(FormulaError::CachePreservationConflict) => {
            Err(TableRulingError::FormulaRebaseRequired)
        }
        Err(error) => Err(TableRulingError::Formula(error)),
    }
}

fn clear_formula_caches_for_topology_change(
    cells: &mut [TableRulingCell],
    dimensions: FormulaGridDimensions,
    policy: TableRulingFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<usize, TableRulingError> {
    let mut cleared = 0usize;
    for cell in cells {
        let Some(formula) = cell.formula.as_ref() else {
            continue;
        };
        if matches!(formula.cache(), FormulaCache::Absent) {
            continue;
        }
        if policy != TableRulingFormulaPolicy::RebaseAndClearTopologyStaleCache {
            return Err(TableRulingError::FormulaRebaseRequired);
        }
        cell.formula = Some(
            formula
                .rebase(
                    formula.owner(),
                    dimensions,
                    FormulaCachePolicy::Clear,
                    None,
                    formula_limits,
                )
                .map_err(TableRulingError::from)?,
        );
        cleared = cleared
            .checked_add(1)
            .ok_or(TableRulingError::CountOverflow)?;
    }
    Ok(cleared)
}

fn compare_formula_counts(
    before: &[TableRulingCell],
    after: &[TableRulingCell],
) -> Result<FormulaCounts, TableRulingError> {
    let mut counts = FormulaCounts::default();
    for (before_cell, after_cell) in before.iter().zip(after) {
        match (&before_cell.formula, &after_cell.formula) {
            (Some(before), Some(after)) => {
                if before != after {
                    counts.rebased = counts
                        .rebased
                        .checked_add(1)
                        .ok_or(TableRulingError::CountOverflow)?;
                }
                if !matches!(before.cache(), FormulaCache::Absent)
                    && matches!(after.cache(), FormulaCache::Absent)
                {
                    counts.caches_cleared = counts
                        .caches_cleared
                        .checked_add(1)
                        .ok_or(TableRulingError::CountOverflow)?;
                }
            }
            (None, None) => {}
            _ => return Err(TableRulingError::FormulaPreservationFailure),
        }
    }
    Ok(counts)
}

fn find(parent: &mut [usize], index: usize) -> usize {
    if parent[index] != index {
        parent[index] = find(parent, parent[index]);
    }
    parent[index]
}

fn union(parent: &mut [usize], left: usize, right: usize) {
    let left_root = find(parent, left);
    let right_root = find(parent, right);
    if left_root != right_root {
        let (small, large) = if left_root < right_root {
            (left_root, right_root)
        } else {
            (right_root, left_root)
        };
        parent[large] = small;
    }
}

fn containing_track(boundaries: &[u32], position: u32) -> Result<u32, TableRulingError> {
    let index = match boundaries.binary_search(&position) {
        Ok(index) if index + 1 < boundaries.len() => index,
        Err(index) if index > 0 && index < boundaries.len() => index - 1,
        Ok(_) | Err(_) => return Err(TableRulingError::InvalidLattice),
    };
    u32::try_from(index).map_err(|_| TableRulingError::CountOverflow)
}

fn mapped_boundary(boundaries: &[u32], position: u32) -> Result<u32, TableRulingError> {
    boundaries
        .binary_search(&position)
        .map_err(|_| TableRulingError::InvalidLattice)
        .and_then(|index| u32::try_from(index).map_err(|_| TableRulingError::CountOverflow))
}

fn boundary_value(boundaries: &[u32], index: u32) -> Result<u32, TableRulingError> {
    boundaries
        .get(usize::try_from(index).map_err(|_| TableRulingError::CountOverflow)?)
        .copied()
        .ok_or(TableRulingError::InvalidLattice)
}

fn track_count(boundaries: &[u32]) -> Result<u32, TableRulingError> {
    u32::try_from(
        boundaries
            .len()
            .checked_sub(1)
            .ok_or(TableRulingError::InvalidLattice)?,
    )
    .map_err(|_| TableRulingError::CountOverflow)
}

fn expected_edge_count(rows: u32, columns: u32) -> Result<usize, TableRulingError> {
    let rows = usize::try_from(rows).map_err(|_| TableRulingError::CountOverflow)?;
    let columns = usize::try_from(columns).map_err(|_| TableRulingError::CountOverflow)?;
    rows.checked_add(1)
        .and_then(|value| value.checked_mul(columns))
        .and_then(|horizontal| {
            columns
                .checked_add(1)
                .and_then(|value| value.checked_mul(rows))
                .and_then(|vertical| horizontal.checked_add(vertical))
        })
        .ok_or(TableRulingError::CountOverflow)
}

fn local_index(row: u32, column: u32, columns: u32) -> Result<usize, TableRulingError> {
    usize::try_from(row)
        .ok()
        .and_then(|row| {
            usize::try_from(columns)
                .ok()
                .and_then(|columns| row.checked_mul(columns))
        })
        .and_then(|offset| {
            usize::try_from(column)
                .ok()
                .and_then(|column| offset.checked_add(column))
        })
        .ok_or(TableRulingError::CountOverflow)
}

fn product(left: u32, right: u32) -> Result<usize, TableRulingError> {
    usize::try_from(left)
        .ok()
        .and_then(|left| {
            usize::try_from(right)
                .ok()
                .and_then(|right| left.checked_mul(right))
        })
        .ok_or(TableRulingError::CountOverflow)
}

fn payload_count(cells: &[TableRulingCell]) -> Result<usize, TableRulingError> {
    cells.iter().try_fold(0usize, |count, cell| {
        count
            .checked_add(cell.payload.len())
            .ok_or(TableRulingError::CountOverflow)
    })
}

fn formula_count(cells: &[TableRulingCell]) -> usize {
    cells.iter().filter(|cell| cell.formula.is_some()).count()
}

fn dimensions(grid: &TableGrid) -> FormulaGridDimensions {
    FormulaGridDimensions {
        rows: grid.rows(),
        columns: grid.columns(),
    }
}

fn span_coordinate(span: &TableCellSpan) -> CellCoordinate {
    CellCoordinate {
        row: span.row,
        column: span.column,
    }
}

fn grid_digest(grid: &TableGrid) -> Result<String, TableRulingError> {
    Ok(hex(grid.canonical_sha256()?))
}

fn state_digest(
    state: &TableRulingState,
    limits: TableRulingLimits,
) -> Result<String, TableRulingError> {
    Ok(hex(state.canonical_sha256(limits)?))
}

fn validate_input(bytes: &[u8], limits: TableRulingLimits) -> Result<(), TableRulingError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(TableRulingError::InputLimitExceeded);
    }
    Ok(())
}

fn validate_identifier(
    identifier: &LogicalId,
    limits: TableRulingLimits,
) -> Result<(), TableRulingError> {
    if identifier.as_str().len() > limits.0.identifier_bytes {
        return Err(TableRulingError::IdentifierLimitExceeded);
    }
    Ok(())
}

fn validate_optional_digest(value: Option<&str>) -> Result<(), TableRulingError> {
    if let Some(value) = value {
        validate_digest(value)?;
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), TableRulingError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableRulingError::InvalidDigest);
    }
    Ok(())
}

fn fallible_vec<T>(capacity: usize) -> Result<Vec<T>, TableRulingError> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| TableRulingError::AllocationFailed)?;
    Ok(values)
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    max_bytes: usize,
) -> Result<Vec<u8>, TableRulingError> {
    let mut writer = BoundedWriter::new(max_bytes);
    if serde_json::to_writer(&mut writer, value).is_err() {
        return Err(match writer.failure {
            WriterFailure::Limit => TableRulingError::OutputLimitExceeded,
            WriterFailure::Allocation => TableRulingError::AllocationFailed,
            WriterFailure::None => TableRulingError::SerializationFailed,
        });
    }
    Ok(writer.bytes)
}

fn hex(value: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum WriterFailure {
    None,
    Limit,
    Allocation,
}

struct BoundedWriter {
    bytes: Vec<u8>,
    max_bytes: usize,
    failure: WriterFailure,
}

impl BoundedWriter {
    const fn new(max_bytes: usize) -> Self {
        Self {
            bytes: Vec::new(),
            max_bytes,
            failure: WriterFailure::None,
        }
    }
}

impl Write for BoundedWriter {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        let Some(next_length) = self.bytes.len().checked_add(buffer.len()) else {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table ruling output limit"));
        };
        if next_length > self.max_bytes {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table ruling output limit"));
        }
        if self.bytes.try_reserve(buffer.len()).is_err() {
            self.failure = WriterFailure::Allocation;
            return Err(io::Error::other("table ruling allocation"));
        }
        self.bytes.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableRulingError {
    #[error("table ruling limits are invalid")]
    InvalidLimit,
    #[error("table ruling schema version is unsupported")]
    UnsupportedVersion,
    #[error("table ruling JSON is invalid")]
    InvalidJson,
    #[error("table ruling input is empty or exceeds its finite limit")]
    InputLimitExceeded,
    #[error("table ruling output exceeds its finite limit")]
    OutputLimitExceeded,
    #[error("table ruling serialization failed")]
    SerializationFailed,
    #[error("table ruling allocation failed")]
    AllocationFailed,
    #[error("table ruling identifier exceeds its finite limit")]
    IdentifierLimitExceeded,
    #[error("table ruling identifiers collide")]
    IdentifierCollision,
    #[error("table ruling digest is not canonical lowercase SHA-256")]
    InvalidDigest,
    #[error("table ruling frame is invalid")]
    InvalidFrame,
    #[error("table ruling physical lattice is invalid")]
    InvalidLattice,
    #[error("table ruling complete edge set does not match the grid")]
    EdgeSetMismatch,
    #[error("table ruling complete edge set contains a duplicate")]
    DuplicateEdge,
    #[error("table ruling edge count exceeds its finite limit")]
    EdgeLimitExceeded,
    #[error("table ruling complete cell set does not match the grid")]
    CellSetMismatch,
    #[error("table ruling cell count exceeds its finite limit")]
    CellLimitExceeded,
    #[error("table ruling payload block count exceeds its finite limit")]
    PayloadBlockLimitExceeded,
    #[error("table ruling payload block identity is duplicated")]
    DuplicatePayloadBlock,
    #[error("table ruling formula owner does not match its master cell")]
    FormulaOwnerMismatch,
    #[error("table ruling state is bound to a different grid")]
    GridMismatch,
    #[error("table ruling request context does not match the operation")]
    ContextMismatch,
    #[error("table ruling exact state or grid binding drifted")]
    StateBindingMismatch,
    #[error("table ruling document-flow binding drifted")]
    FlowBindingMismatch,
    #[error("table ruling outer rectangle cannot start with a diagonal")]
    OuterRectangleDiagonalConflict,
    #[error("table ruling stroke is invalid or outside the table frame")]
    InvalidStroke,
    #[error("table eraser stroke must follow existing ruling coordinates")]
    EraserOffRuling,
    #[error("table ruling new master-cell identity is duplicated")]
    DuplicateNewMasterCell,
    #[error("table ruling new master-cell identity count is inexact")]
    NewMasterCellCountMismatch,
    #[error("table ruling stroke would create a non-rectangular cell")]
    NonRectangularSplit,
    #[error("table ruling split cannot preserve an existing diagonal exactly")]
    DiagonalSplitConflict,
    #[error("table ruling target master cell was not found")]
    MasterCellNotFound,
    #[error("table eraser shared-edge merge would create a non-rectangular cell")]
    NonRectangularMerge,
    #[error("table eraser merge requires equal non-ruling cell properties")]
    CellPropertiesConflict,
    #[error("table eraser merge cannot preserve cell-local diagonals exactly")]
    DiagonalMergeConflict,
    #[error("table eraser merge cannot preserve more than one cell formula")]
    MultipleFormulaMerge,
    #[error("table ruling formula rebase requires the explicit clear-changed-cache policy")]
    FormulaRebaseRequired,
    #[error("table ruling split cannot preserve formula reference topology exactly")]
    FormulaTopologyAmbiguous,
    #[error("table ruling operation makes no semantic change")]
    NoSemanticChange,
    #[error("table ruling payload preservation invariant failed")]
    PayloadPreservationFailure,
    #[error("table ruling formula preservation invariant failed")]
    FormulaPreservationFailure,
    #[error("table ruling count arithmetic overflowed")]
    CountOverflow,
    #[error(transparent)]
    Grid(#[from] TableGridError),
    #[error(transparent)]
    Formula(#[from] FormulaError),
}

impl TableRulingError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_ruling_invalid_limit",
            Self::UnsupportedVersion => "table_ruling_unsupported_version",
            Self::InvalidJson => "table_ruling_invalid_json",
            Self::InputLimitExceeded => "table_ruling_input_limit_exceeded",
            Self::OutputLimitExceeded => "table_ruling_output_limit_exceeded",
            Self::SerializationFailed => "table_ruling_serialization_failed",
            Self::AllocationFailed => "table_ruling_allocation_failed",
            Self::IdentifierLimitExceeded => "table_ruling_identifier_limit_exceeded",
            Self::IdentifierCollision => "table_ruling_identifier_collision",
            Self::InvalidDigest => "table_ruling_invalid_digest",
            Self::InvalidFrame => "table_ruling_invalid_frame",
            Self::InvalidLattice => "table_ruling_invalid_lattice",
            Self::EdgeSetMismatch => "table_ruling_edge_set_mismatch",
            Self::DuplicateEdge => "table_ruling_duplicate_edge",
            Self::EdgeLimitExceeded => "table_ruling_edge_limit_exceeded",
            Self::CellSetMismatch => "table_ruling_cell_set_mismatch",
            Self::CellLimitExceeded => "table_ruling_cell_limit_exceeded",
            Self::PayloadBlockLimitExceeded => "table_ruling_payload_block_limit_exceeded",
            Self::DuplicatePayloadBlock => "table_ruling_duplicate_payload_block",
            Self::FormulaOwnerMismatch => "table_ruling_formula_owner_mismatch",
            Self::GridMismatch => "table_ruling_grid_mismatch",
            Self::ContextMismatch => "table_ruling_context_mismatch",
            Self::StateBindingMismatch => "table_ruling_state_binding_mismatch",
            Self::FlowBindingMismatch => "table_ruling_flow_binding_mismatch",
            Self::OuterRectangleDiagonalConflict => {
                "table_ruling_outer_rectangle_diagonal_conflict"
            }
            Self::InvalidStroke => "table_ruling_invalid_stroke",
            Self::EraserOffRuling => "table_ruling_eraser_off_ruling",
            Self::DuplicateNewMasterCell => "table_ruling_duplicate_new_master_cell",
            Self::NewMasterCellCountMismatch => "table_ruling_new_master_cell_count_mismatch",
            Self::NonRectangularSplit => "table_ruling_non_rectangular_split",
            Self::DiagonalSplitConflict => "table_ruling_diagonal_split_conflict",
            Self::MasterCellNotFound => "table_ruling_master_cell_not_found",
            Self::NonRectangularMerge => "table_ruling_non_rectangular_merge",
            Self::CellPropertiesConflict => "table_ruling_cell_properties_conflict",
            Self::DiagonalMergeConflict => "table_ruling_diagonal_merge_conflict",
            Self::MultipleFormulaMerge => "table_ruling_multiple_formula_merge",
            Self::FormulaRebaseRequired => "table_ruling_formula_rebase_required",
            Self::FormulaTopologyAmbiguous => "table_ruling_formula_topology_ambiguous",
            Self::NoSemanticChange => "table_ruling_no_semantic_change",
            Self::PayloadPreservationFailure => "table_ruling_payload_preservation_failure",
            Self::FormulaPreservationFailure => "table_ruling_formula_preservation_failure",
            Self::CountOverflow => "table_ruling_count_overflow",
            Self::Grid(error) => error.code(),
            Self::Formula(error) => error.code(),
        }
    }
}
