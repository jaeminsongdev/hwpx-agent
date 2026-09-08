use std::cmp::Ordering;
use std::collections::HashSet;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    CellCoordinate, FormulaCache, FormulaCachePolicy, FormulaCell, FormulaCellDraft,
    FormulaGridDimensions, FormulaGridEdit, FormulaLimits, LogicalId, TableCellSpan, TableGrid,
    TableGridLimits,
};

pub const TABLE_PARTITION_SCHEMA_VERSION: &str = "hwpx-agent.table-partition/v1";
pub const TABLE_SPLIT_TABLE_CAPABILITY_ID: &str = "table.split_table";
pub const TABLE_JOIN_TABLE_CAPABILITY_ID: &str = "table.join_table";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TablePartitionLimitConfig {
    pub input_bytes: usize,
    pub master_cells: usize,
    pub separator_tokens: usize,
    pub separator_spaces: u32,
    pub identifier_bytes: usize,
    pub serialized_bytes: usize,
    pub table_width_hwpunit: u32,
}

impl Default for TablePartitionLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 32 * 1024 * 1024,
            master_cells: 1_000_000,
            separator_tokens: 4_096,
            separator_spaces: 1_000_000,
            identifier_bytes: 256,
            serialized_bytes: 128 * 1024 * 1024,
            table_width_hwpunit: 100_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TablePartitionLimits(TablePartitionLimitConfig);

impl TablePartitionLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_MASTER_CELLS: usize = 1_000_000;
    pub const HARD_MAX_SEPARATOR_TOKENS: usize = 65_536;
    pub const HARD_MAX_SEPARATOR_SPACES: u32 = 10_000_000;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 1_024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;
    pub const HARD_MAX_TABLE_WIDTH_HWPUNIT: u32 = 1_000_000_000;

    /// Creates finite bounds for whole-table split and join planning.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling or internally inconsistent limits.
    pub fn new(config: TablePartitionLimitConfig) -> Result<Self, TablePartitionError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.master_cells == 0
            || config.master_cells > Self::HARD_MAX_MASTER_CELLS
            || config.separator_tokens == 0
            || config.separator_tokens > Self::HARD_MAX_SEPARATOR_TOKENS
            || config.separator_spaces == 0
            || config.separator_spaces > Self::HARD_MAX_SEPARATOR_SPACES
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
            || config.table_width_hwpunit == 0
            || config.table_width_hwpunit > Self::HARD_MAX_TABLE_WIDTH_HWPUNIT
        {
            return Err(TablePartitionError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TablePartitionLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TablePartitionFormulaPolicy {
    Reject,
    RebaseAndClearCache,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TableJoinSeparatorToken {
    SpaceRun { count: u32 },
    ParagraphBreak,
    Content { content_sha256: String },
    Object { object_sha256: String },
}

impl fmt::Debug for TableJoinSeparatorToken {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::SpaceRun { count } => formatter
                .debug_struct("SpaceRun")
                .field("count", count)
                .finish(),
            Self::ParagraphBreak => formatter.write_str("ParagraphBreak"),
            Self::Content { .. } => formatter.write_str("Content(<redacted>)"),
            Self::Object { .. } => formatter.write_str("Object(<redacted>)"),
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePartitionCellDraft {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub payload_sha256: String,
    pub cell_properties_sha256: String,
    pub formula: Option<FormulaCellDraft>,
}

impl fmt::Debug for TablePartitionCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePartitionCellDraft")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("payload_sha256", &"<redacted>")
            .field("cell_properties_sha256", &"<redacted>")
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePartitionCell {
    master_cell_id: LogicalId,
    coordinate: CellCoordinate,
    payload_sha256: String,
    cell_properties_sha256: String,
    formula: Option<FormulaCell>,
}

impl TablePartitionCell {
    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
    }

    #[must_use]
    pub const fn coordinate(&self) -> CellCoordinate {
        self.coordinate
    }

    #[must_use]
    pub fn payload_sha256(&self) -> &str {
        &self.payload_sha256
    }

    #[must_use]
    pub fn cell_properties_sha256(&self) -> &str {
        &self.cell_properties_sha256
    }

    #[must_use]
    pub const fn formula(&self) -> Option<&FormulaCell> {
        self.formula.as_ref()
    }
}

impl fmt::Debug for TablePartitionCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePartitionCell")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("payload_sha256", &"<redacted>")
            .field("cell_properties_sha256", &"<redacted>")
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePartitionStateDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub grid_sha256: String,
    pub table_properties_sha256: String,
    pub table_width_hwpunit: u32,
    pub column_widths_hwpunit: Vec<u32>,
    pub cells: Vec<TablePartitionCellDraft>,
}

impl fmt::Debug for TablePartitionStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePartitionStateDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("table_width_hwpunit", &self.table_width_hwpunit)
            .field("column_count", &self.column_widths_hwpunit.len())
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePartitionState {
    schema_version: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    table_properties_sha256: String,
    table_width_hwpunit: u32,
    column_widths_hwpunit: Vec<u32>,
    cells: Vec<TablePartitionCell>,
}

impl TablePartitionState {
    /// Validates a complete table snapshot against one exact logical grid.
    ///
    /// # Errors
    ///
    /// Rejects schema, identifier, digest, grid, geometry, cell-set, formula and finite-limit
    /// drift.
    pub fn from_draft(
        draft: TablePartitionStateDraft,
        grid: &TableGrid,
        formula_limits: FormulaLimits,
        limits: TablePartitionLimits,
    ) -> Result<Self, TablePartitionError> {
        let TablePartitionStateDraft {
            schema_version,
            table_id,
            grid_sha256,
            table_properties_sha256,
            table_width_hwpunit,
            column_widths_hwpunit,
            mut cells,
        } = draft;
        if schema_version != TABLE_PARTITION_SCHEMA_VERSION {
            return Err(TablePartitionError::UnsupportedVersion);
        }
        validate_identifier(&table_id, limits)?;
        validate_digest(&grid_sha256)?;
        validate_digest(&table_properties_sha256)?;
        if grid_sha256 != grid_digest(grid)? {
            return Err(TablePartitionError::GridMismatch);
        }
        validate_column_widths(
            table_width_hwpunit,
            &column_widths_hwpunit,
            grid.columns(),
            limits,
        )?;
        if cells.len() != grid.master_cell_count() || cells.len() > limits.0.master_cells {
            return Err(TablePartitionError::CellSetMismatch);
        }
        cells.sort_by(|left, right| {
            (left.coordinate, &left.master_cell_id).cmp(&(right.coordinate, &right.master_cell_id))
        });
        if cells.windows(2).any(|pair| {
            pair[0].coordinate == pair[1].coordinate
                || pair[0].master_cell_id == pair[1].master_cell_id
        }) {
            return Err(TablePartitionError::CellSetMismatch);
        }
        let dimensions = dimensions(grid);
        let mut validated = fallible_vec(cells.len())?;
        for (cell, span) in cells.into_iter().zip(grid.master_cells()) {
            if cell.master_cell_id != span.master_cell_id
                || cell.coordinate != span_coordinate(span)
            {
                return Err(TablePartitionError::CellSetMismatch);
            }
            validate_identifier(&cell.master_cell_id, limits)?;
            validate_digest(&cell.payload_sha256)?;
            validate_digest(&cell.cell_properties_sha256)?;
            let formula = cell
                .formula
                .map(|formula| FormulaCell::from_draft(formula, dimensions, formula_limits))
                .transpose()
                .map_err(|_| TablePartitionError::FormulaInvalid)?;
            if formula
                .as_ref()
                .is_some_and(|formula| formula.owner() != cell.coordinate)
            {
                return Err(TablePartitionError::FormulaOwnerMismatch);
            }
            validated.push(TablePartitionCell {
                master_cell_id: cell.master_cell_id,
                coordinate: cell.coordinate,
                payload_sha256: cell.payload_sha256,
                cell_properties_sha256: cell.cell_properties_sha256,
                formula,
            });
        }
        Self::from_validated_parts(
            table_id,
            grid_sha256,
            table_properties_sha256,
            table_width_hwpunit,
            column_widths_hwpunit,
            validated,
            limits,
        )
    }

    /// Parses bounded strict JSON and validates it against an exact grid.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed or semantically invalid input.
    pub fn from_json(
        bytes: &[u8],
        grid: &TableGrid,
        formula_limits: FormulaLimits,
        limits: TablePartitionLimits,
    ) -> Result<Self, TablePartitionError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TablePartitionError::InvalidJson)?;
        Self::from_draft(draft, grid, formula_limits, limits)
    }

    fn from_validated_parts(
        table_id: LogicalId,
        grid_sha256: String,
        table_properties_sha256: String,
        table_width_hwpunit: u32,
        column_widths_hwpunit: Vec<u32>,
        cells: Vec<TablePartitionCell>,
        limits: TablePartitionLimits,
    ) -> Result<Self, TablePartitionError> {
        let state = Self {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION,
            table_id,
            grid_sha256,
            table_properties_sha256,
            table_width_hwpunit,
            column_widths_hwpunit,
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
    pub fn grid_sha256(&self) -> &str {
        &self.grid_sha256
    }

    #[must_use]
    pub fn table_properties_sha256(&self) -> &str {
        &self.table_properties_sha256
    }

    #[must_use]
    pub const fn table_width_hwpunit(&self) -> u32 {
        self.table_width_hwpunit
    }

    #[must_use]
    pub fn column_widths_hwpunit(&self) -> &[u32] {
        &self.column_widths_hwpunit
    }

    #[must_use]
    pub fn cells(&self) -> &[TablePartitionCell] {
        &self.cells
    }

    /// Serializes the canonical complete state under a finite output bound.
    ///
    /// # Errors
    ///
    /// Returns a stable bounded serialization failure.
    pub fn canonical_json(
        &self,
        limits: TablePartitionLimits,
    ) -> Result<Vec<u8>, TablePartitionError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical state.
    ///
    /// # Errors
    ///
    /// Propagates bounded serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TablePartitionLimits,
    ) -> Result<[u8; 32], TablePartitionError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TablePartitionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePartitionState")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("table_width_hwpunit", &self.table_width_hwpunit)
            .field("column_count", &self.column_widths_hwpunit.len())
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct WholeTableSplitRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub cursor: CellCoordinate,
    pub second_table_id: LogicalId,
    pub separator_paragraph_id: LogicalId,
    pub expected_state_sha256: String,
    pub expected_flow_sha256: String,
    pub formula_policy: TablePartitionFormulaPolicy,
}

impl fmt::Debug for WholeTableSplitRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WholeTableSplitRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("cursor", &self.cursor)
            .field("second_table_id", &"<redacted>")
            .field("separator_paragraph_id", &"<redacted>")
            .field("expected_state_sha256", &"<redacted>")
            .field("expected_flow_sha256", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct WholeTableSplitRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    cursor: CellCoordinate,
    split_before_row: u32,
    second_table_id: LogicalId,
    separator_paragraph_id: LogicalId,
    expected_state_sha256: String,
    expected_flow_sha256: String,
    formula_policy: TablePartitionFormulaPolicy,
}

impl WholeTableSplitRequest {
    /// Binds a whole-table split to the cursor row, exact table state and surrounding flow.
    ///
    /// # Errors
    ///
    /// Rejects the first row, an out-of-grid cursor, a row-spanning cell crossing the split,
    /// duplicate identities, formula-policy violations and stale state/flow bindings.
    pub fn from_draft(
        draft: WholeTableSplitRequestDraft,
        state: &TablePartitionState,
        grid: &TableGrid,
        current_flow_sha256: &str,
        limits: TablePartitionLimits,
    ) -> Result<Self, TablePartitionError> {
        if draft.schema_version != TABLE_PARTITION_SCHEMA_VERSION {
            return Err(TablePartitionError::UnsupportedVersion);
        }
        validate_identifier(&draft.table_id, limits)?;
        validate_identifier(&draft.second_table_id, limits)?;
        validate_identifier(&draft.separator_paragraph_id, limits)?;
        validate_digest(&draft.expected_state_sha256)?;
        validate_flow_binding(&draft.expected_flow_sha256, current_flow_sha256)?;
        validate_state_grid(state, grid)?;
        if draft.table_id != *state.table_id() {
            return Err(TablePartitionError::TableIdentityMismatch);
        }
        if draft.table_id == draft.second_table_id
            || draft.table_id == draft.separator_paragraph_id
            || draft.second_table_id == draft.separator_paragraph_id
        {
            return Err(TablePartitionError::DuplicateOutputIdentity);
        }
        if draft.cursor.row >= grid.rows() || draft.cursor.column >= grid.columns() {
            return Err(TablePartitionError::CursorOutOfBounds);
        }
        if draft.cursor.row == 0 {
            return Err(TablePartitionError::FirstRowSplit);
        }
        validate_split_boundary(grid, draft.cursor.row)?;
        if draft.formula_policy == TablePartitionFormulaPolicy::Reject
            && state.cells.iter().any(|cell| cell.formula.is_some())
        {
            return Err(TablePartitionError::FormulaPresent);
        }
        if draft.expected_state_sha256 != state_digest(state, limits)? {
            return Err(TablePartitionError::StateBindingMismatch);
        }
        let request = Self {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION,
            capability_id: TABLE_SPLIT_TABLE_CAPABILITY_ID,
            table_id: draft.table_id,
            grid_sha256: state.grid_sha256.clone(),
            cursor: draft.cursor,
            split_before_row: draft.cursor.row,
            second_table_id: draft.second_table_id,
            separator_paragraph_id: draft.separator_paragraph_id,
            expected_state_sha256: draft.expected_state_sha256,
            expected_flow_sha256: draft.expected_flow_sha256,
            formula_policy: draft.formula_policy,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses and validates a bounded split request.
    ///
    /// # Errors
    ///
    /// Propagates JSON, binding and semantic validation failures.
    pub fn from_json(
        bytes: &[u8],
        state: &TablePartitionState,
        grid: &TableGrid,
        current_flow_sha256: &str,
        limits: TablePartitionLimits,
    ) -> Result<Self, TablePartitionError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TablePartitionError::InvalidJson)?;
        Self::from_draft(draft, state, grid, current_flow_sha256, limits)
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
    pub const fn cursor(&self) -> CellCoordinate {
        self.cursor
    }

    #[must_use]
    pub const fn split_before_row(&self) -> u32 {
        self.split_before_row
    }

    #[must_use]
    pub const fn second_table_id(&self) -> &LogicalId {
        &self.second_table_id
    }

    #[must_use]
    pub const fn separator_paragraph_id(&self) -> &LogicalId {
        &self.separator_paragraph_id
    }

    #[must_use]
    pub const fn formula_policy(&self) -> TablePartitionFormulaPolicy {
        self.formula_policy
    }

    /// Serializes the exact split request under a finite output bound.
    ///
    /// # Errors
    ///
    /// Returns a stable bounded serialization failure.
    pub fn canonical_json(
        &self,
        limits: TablePartitionLimits,
    ) -> Result<Vec<u8>, TablePartitionError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates bounded serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TablePartitionLimits,
    ) -> Result<[u8; 32], TablePartitionError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for WholeTableSplitRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WholeTableSplitRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("cursor", &self.cursor)
            .field("split_before_row", &self.split_before_row)
            .field("second_table_id", &"<redacted>")
            .field("separator_paragraph_id", &"<redacted>")
            .field("expected_state_sha256", &"<redacted>")
            .field("expected_flow_sha256", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct WholeTableJoinRequestDraft {
    pub schema_version: String,
    pub leading_table_id: LogicalId,
    pub trailing_table_id: LogicalId,
    pub separator_tokens: Vec<TableJoinSeparatorToken>,
    pub expected_leading_state_sha256: String,
    pub expected_trailing_state_sha256: String,
    pub expected_flow_sha256: String,
    pub formula_policy: TablePartitionFormulaPolicy,
}

impl fmt::Debug for WholeTableJoinRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WholeTableJoinRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("leading_table_id", &"<redacted>")
            .field("trailing_table_id", &"<redacted>")
            .field("separator_token_count", &self.separator_tokens.len())
            .field("expected_leading_state_sha256", &"<redacted>")
            .field("expected_trailing_state_sha256", &"<redacted>")
            .field("expected_flow_sha256", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct WholeTableJoinRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    leading_table_id: LogicalId,
    trailing_table_id: LogicalId,
    leading_grid_sha256: String,
    trailing_grid_sha256: String,
    separator_tokens: Vec<TableJoinSeparatorToken>,
    expected_leading_state_sha256: String,
    expected_trailing_state_sha256: String,
    expected_flow_sha256: String,
    formula_policy: TablePartitionFormulaPolicy,
}

impl WholeTableJoinRequest {
    /// Binds a vertical table join to two exact states and a whitespace-only paragraph gap.
    ///
    /// Different column counts and widths are admitted; the planner constructs a common rational
    /// column lattice and uses the larger table width.
    ///
    /// # Errors
    ///
    /// Rejects identity/state drift, non-whitespace intervening content, a missing paragraph
    /// boundary, duplicate master identities, formula-policy violations and finite-limit excess.
    pub fn from_draft(
        draft: WholeTableJoinRequestDraft,
        leading_state: &TablePartitionState,
        leading_grid: &TableGrid,
        trailing_state: &TablePartitionState,
        trailing_grid: &TableGrid,
        current_flow_sha256: &str,
        limits: TablePartitionLimits,
    ) -> Result<Self, TablePartitionError> {
        if draft.schema_version != TABLE_PARTITION_SCHEMA_VERSION {
            return Err(TablePartitionError::UnsupportedVersion);
        }
        validate_identifier(&draft.leading_table_id, limits)?;
        validate_identifier(&draft.trailing_table_id, limits)?;
        validate_digest(&draft.expected_leading_state_sha256)?;
        validate_digest(&draft.expected_trailing_state_sha256)?;
        validate_flow_binding(&draft.expected_flow_sha256, current_flow_sha256)?;
        validate_state_grid(leading_state, leading_grid)?;
        validate_state_grid(trailing_state, trailing_grid)?;
        if draft.leading_table_id != *leading_state.table_id()
            || draft.trailing_table_id != *trailing_state.table_id()
        {
            return Err(TablePartitionError::TableIdentityMismatch);
        }
        if draft.leading_table_id == draft.trailing_table_id {
            return Err(TablePartitionError::DuplicateOutputIdentity);
        }
        validate_separator(&draft.separator_tokens, limits)?;
        let combined_cells = leading_state
            .cells
            .len()
            .checked_add(trailing_state.cells.len())
            .ok_or(TablePartitionError::MasterCellLimit)?;
        if combined_cells > limits.0.master_cells {
            return Err(TablePartitionError::MasterCellLimit);
        }
        let mut master_ids = HashSet::new();
        master_ids
            .try_reserve(combined_cells)
            .map_err(|_| TablePartitionError::AllocationFailed)?;
        for cell in leading_state.cells.iter().chain(&trailing_state.cells) {
            if !master_ids.insert(cell.master_cell_id.clone()) {
                return Err(TablePartitionError::DuplicateMasterCell);
            }
        }
        if draft.formula_policy == TablePartitionFormulaPolicy::Reject
            && leading_state
                .cells
                .iter()
                .chain(&trailing_state.cells)
                .any(|cell| cell.formula.is_some())
        {
            return Err(TablePartitionError::FormulaPresent);
        }
        if draft.expected_leading_state_sha256 != state_digest(leading_state, limits)?
            || draft.expected_trailing_state_sha256 != state_digest(trailing_state, limits)?
        {
            return Err(TablePartitionError::StateBindingMismatch);
        }
        let request = Self {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION,
            capability_id: TABLE_JOIN_TABLE_CAPABILITY_ID,
            leading_table_id: draft.leading_table_id,
            trailing_table_id: draft.trailing_table_id,
            leading_grid_sha256: leading_state.grid_sha256.clone(),
            trailing_grid_sha256: trailing_state.grid_sha256.clone(),
            separator_tokens: draft.separator_tokens,
            expected_leading_state_sha256: draft.expected_leading_state_sha256,
            expected_trailing_state_sha256: draft.expected_trailing_state_sha256,
            expected_flow_sha256: draft.expected_flow_sha256,
            formula_policy: draft.formula_policy,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses and validates a bounded join request.
    ///
    /// # Errors
    ///
    /// Propagates JSON, binding and semantic validation failures.
    #[allow(clippy::too_many_arguments)]
    pub fn from_json(
        bytes: &[u8],
        leading_state: &TablePartitionState,
        leading_grid: &TableGrid,
        trailing_state: &TablePartitionState,
        trailing_grid: &TableGrid,
        current_flow_sha256: &str,
        limits: TablePartitionLimits,
    ) -> Result<Self, TablePartitionError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TablePartitionError::InvalidJson)?;
        Self::from_draft(
            draft,
            leading_state,
            leading_grid,
            trailing_state,
            trailing_grid,
            current_flow_sha256,
            limits,
        )
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn leading_table_id(&self) -> &LogicalId {
        &self.leading_table_id
    }

    #[must_use]
    pub const fn trailing_table_id(&self) -> &LogicalId {
        &self.trailing_table_id
    }

    #[must_use]
    pub fn separator_tokens(&self) -> &[TableJoinSeparatorToken] {
        &self.separator_tokens
    }

    #[must_use]
    pub const fn formula_policy(&self) -> TablePartitionFormulaPolicy {
        self.formula_policy
    }

    /// Serializes the exact join request under a finite output bound.
    ///
    /// # Errors
    ///
    /// Returns a stable bounded serialization failure.
    pub fn canonical_json(
        &self,
        limits: TablePartitionLimits,
    ) -> Result<Vec<u8>, TablePartitionError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates bounded serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TablePartitionLimits,
    ) -> Result<[u8; 32], TablePartitionError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for WholeTableJoinRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WholeTableJoinRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("leading_table_id", &"<redacted>")
            .field("trailing_table_id", &"<redacted>")
            .field("leading_grid_sha256", &"<redacted>")
            .field("trailing_grid_sha256", &"<redacted>")
            .field("separator_token_count", &self.separator_tokens.len())
            .field("expected_leading_state_sha256", &"<redacted>")
            .field("expected_trailing_state_sha256", &"<redacted>")
            .field("expected_flow_sha256", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct PlannedWholeTable {
    table_id: LogicalId,
    grid_sha256: String,
    rows: u32,
    columns: u32,
    master_cells: Vec<TableCellSpan>,
    table_properties_sha256: String,
    table_width_hwpunit: u32,
    column_widths_hwpunit: Vec<u32>,
    cells: Vec<TablePartitionCell>,
}

impl PlannedWholeTable {
    fn new(grid: &TableGrid, state: &TablePartitionState) -> Self {
        Self {
            table_id: state.table_id.clone(),
            grid_sha256: state.grid_sha256.clone(),
            rows: grid.rows(),
            columns: grid.columns(),
            master_cells: grid.master_cells().to_vec(),
            table_properties_sha256: state.table_properties_sha256.clone(),
            table_width_hwpunit: state.table_width_hwpunit,
            column_widths_hwpunit: state.column_widths_hwpunit.clone(),
            cells: state.cells.clone(),
        }
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub fn grid_sha256(&self) -> &str {
        &self.grid_sha256
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
    pub fn master_cells(&self) -> &[TableCellSpan] {
        &self.master_cells
    }

    #[must_use]
    pub fn table_properties_sha256(&self) -> &str {
        &self.table_properties_sha256
    }

    #[must_use]
    pub const fn table_width_hwpunit(&self) -> u32 {
        self.table_width_hwpunit
    }

    #[must_use]
    pub fn column_widths_hwpunit(&self) -> &[u32] {
        &self.column_widths_hwpunit
    }

    #[must_use]
    pub fn cells(&self) -> &[TablePartitionCell] {
        &self.cells
    }
}

impl fmt::Debug for PlannedWholeTable {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlannedWholeTable")
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("master_cell_count", &self.master_cells.len())
            .field("table_properties_sha256", &"<redacted>")
            .field("table_width_hwpunit", &self.table_width_hwpunit)
            .field("column_width_count", &self.column_widths_hwpunit.len())
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct WholeTableSplitReceipt {
    pub schema_version: &'static str,
    pub capability_id: &'static str,
    pub request_sha256: String,
    pub before_flow_sha256: String,
    pub after_flow_sha256: String,
    pub before_state_sha256: String,
    pub first_state_sha256: String,
    pub second_state_sha256: String,
    pub split_before_row: u32,
    pub first_row_count: u32,
    pub second_row_count: u32,
    pub preserved_master_cell_count: usize,
    pub preserved_payload_count: usize,
    pub preserved_cell_properties_count: usize,
    pub formula_rebased_count: usize,
    pub formula_cache_cleared_count: usize,
    pub inherited_table_properties_count: usize,
    pub created_table_count: usize,
    pub created_separator_paragraph_count: usize,
}

impl fmt::Debug for WholeTableSplitReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WholeTableSplitReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("request_sha256", &"<redacted>")
            .field("before_flow_sha256", &"<redacted>")
            .field("after_flow_sha256", &"<redacted>")
            .field("before_state_sha256", &"<redacted>")
            .field("first_state_sha256", &"<redacted>")
            .field("second_state_sha256", &"<redacted>")
            .field("split_before_row", &self.split_before_row)
            .field("first_row_count", &self.first_row_count)
            .field("second_row_count", &self.second_row_count)
            .field(
                "preserved_master_cell_count",
                &self.preserved_master_cell_count,
            )
            .field("preserved_payload_count", &self.preserved_payload_count)
            .field(
                "preserved_cell_properties_count",
                &self.preserved_cell_properties_count,
            )
            .field("formula_rebased_count", &self.formula_rebased_count)
            .field(
                "formula_cache_cleared_count",
                &self.formula_cache_cleared_count,
            )
            .field(
                "inherited_table_properties_count",
                &self.inherited_table_properties_count,
            )
            .field("created_table_count", &self.created_table_count)
            .field(
                "created_separator_paragraph_count",
                &self.created_separator_paragraph_count,
            )
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct WholeTableJoinReceipt {
    pub schema_version: &'static str,
    pub capability_id: &'static str,
    pub request_sha256: String,
    pub before_flow_sha256: String,
    pub after_flow_sha256: String,
    pub leading_state_sha256: String,
    pub trailing_state_sha256: String,
    pub joined_state_sha256: String,
    pub leading_row_count: u32,
    pub trailing_row_count: u32,
    pub joined_row_count: u32,
    pub joined_column_count: u32,
    pub joined_width_hwpunit: u32,
    pub preserved_master_cell_count: usize,
    pub preserved_payload_count: usize,
    pub preserved_cell_properties_count: usize,
    pub formula_rebased_count: usize,
    pub formula_cache_cleared_count: usize,
    pub leading_table_properties_retained: bool,
    pub trailing_table_properties_discarded: bool,
    pub removed_table_count: usize,
    pub removed_separator_token_count: usize,
}

impl fmt::Debug for WholeTableJoinReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WholeTableJoinReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("request_sha256", &"<redacted>")
            .field("before_flow_sha256", &"<redacted>")
            .field("after_flow_sha256", &"<redacted>")
            .field("leading_state_sha256", &"<redacted>")
            .field("trailing_state_sha256", &"<redacted>")
            .field("joined_state_sha256", &"<redacted>")
            .field("leading_row_count", &self.leading_row_count)
            .field("trailing_row_count", &self.trailing_row_count)
            .field("joined_row_count", &self.joined_row_count)
            .field("joined_column_count", &self.joined_column_count)
            .field("joined_width_hwpunit", &self.joined_width_hwpunit)
            .field(
                "preserved_master_cell_count",
                &self.preserved_master_cell_count,
            )
            .field("preserved_payload_count", &self.preserved_payload_count)
            .field(
                "preserved_cell_properties_count",
                &self.preserved_cell_properties_count,
            )
            .field("formula_rebased_count", &self.formula_rebased_count)
            .field(
                "formula_cache_cleared_count",
                &self.formula_cache_cleared_count,
            )
            .field(
                "leading_table_properties_retained",
                &self.leading_table_properties_retained,
            )
            .field(
                "trailing_table_properties_discarded",
                &self.trailing_table_properties_discarded,
            )
            .field("removed_table_count", &self.removed_table_count)
            .field(
                "removed_separator_token_count",
                &self.removed_separator_token_count,
            )
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct WholeTableSplitPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    split_before_row: u32,
    separator_paragraph_id: LogicalId,
    first: PlannedWholeTable,
    second: PlannedWholeTable,
    receipt: WholeTableSplitReceipt,
}

impl WholeTableSplitPlan {
    #[must_use]
    pub const fn first(&self) -> &PlannedWholeTable {
        &self.first
    }

    #[must_use]
    pub const fn second(&self) -> &PlannedWholeTable {
        &self.second
    }

    #[must_use]
    pub const fn receipt(&self) -> &WholeTableSplitReceipt {
        &self.receipt
    }

    /// Serializes a lowering-ready split plan under a finite output bound.
    ///
    /// # Errors
    ///
    /// Returns a stable bounded serialization failure.
    pub fn canonical_json(
        &self,
        limits: TablePartitionLimits,
    ) -> Result<Vec<u8>, TablePartitionError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for WholeTableSplitPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WholeTableSplitPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("split_before_row", &self.split_before_row)
            .field("separator_paragraph_id", &"<redacted>")
            .field("first", &self.first)
            .field("second", &self.second)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct WholeTableJoinPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    joined: PlannedWholeTable,
    receipt: WholeTableJoinReceipt,
}

impl WholeTableJoinPlan {
    #[must_use]
    pub const fn joined(&self) -> &PlannedWholeTable {
        &self.joined
    }

    #[must_use]
    pub const fn receipt(&self) -> &WholeTableJoinReceipt {
        &self.receipt
    }

    /// Serializes a lowering-ready join plan under a finite output bound.
    ///
    /// # Errors
    ///
    /// Returns a stable bounded serialization failure.
    pub fn canonical_json(
        &self,
        limits: TablePartitionLimits,
    ) -> Result<Vec<u8>, TablePartitionError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for WholeTableJoinPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("WholeTableJoinPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("joined", &self.joined)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TablePartitionBuilder;

impl TablePartitionBuilder {
    /// Builds a pure, atomic whole-table split plan. The source table is never mutated.
    ///
    /// # Errors
    ///
    /// Rejects stale bindings, cross-boundary merged cells or formulas, invalid formula rebasing,
    /// grid-limit excess and bounded serialization failures.
    pub fn split(
        request: &WholeTableSplitRequest,
        state: &TablePartitionState,
        grid: &TableGrid,
        current_flow_sha256: &str,
        grid_limits: TableGridLimits,
        formula_limits: FormulaLimits,
        limits: TablePartitionLimits,
    ) -> Result<WholeTableSplitPlan, TablePartitionError> {
        validate_split_binding(request, state, grid, current_flow_sha256, limits)?;
        let (first_grid, second_grid) = split_grid(grid, request.split_before_row, grid_limits)?;
        let cells = split_cells(
            request,
            state,
            grid,
            &first_grid,
            &second_grid,
            formula_limits,
        )?;
        let first_state = TablePartitionState::from_validated_parts(
            state.table_id.clone(),
            grid_digest(&first_grid)?,
            state.table_properties_sha256.clone(),
            state.table_width_hwpunit,
            state.column_widths_hwpunit.clone(),
            cells.first,
            limits,
        )?;
        let second_state = TablePartitionState::from_validated_parts(
            request.second_table_id.clone(),
            grid_digest(&second_grid)?,
            state.table_properties_sha256.clone(),
            state.table_width_hwpunit,
            state.column_widths_hwpunit.clone(),
            cells.second,
            limits,
        )?;
        let request_sha256 = hex(request.canonical_sha256(limits)?);
        let first_state_sha256 = state_digest(&first_state, limits)?;
        let second_state_sha256 = state_digest(&second_state, limits)?;
        let after_flow_sha256 = split_flow_digest(
            &request.expected_flow_sha256,
            &first_state_sha256,
            &request.separator_paragraph_id,
            &second_state_sha256,
            limits,
        )?;
        let receipt = WholeTableSplitReceipt {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION,
            capability_id: TABLE_SPLIT_TABLE_CAPABILITY_ID,
            request_sha256,
            before_flow_sha256: request.expected_flow_sha256.clone(),
            after_flow_sha256,
            before_state_sha256: request.expected_state_sha256.clone(),
            first_state_sha256,
            second_state_sha256,
            split_before_row: request.split_before_row,
            first_row_count: first_grid.rows(),
            second_row_count: second_grid.rows(),
            preserved_master_cell_count: state.cells.len(),
            preserved_payload_count: state.cells.len(),
            preserved_cell_properties_count: state.cells.len(),
            formula_rebased_count: cells.counts.rebased,
            formula_cache_cleared_count: cells.counts.caches_cleared,
            inherited_table_properties_count: 2,
            created_table_count: 1,
            created_separator_paragraph_count: 1,
        };
        let plan = WholeTableSplitPlan {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION,
            capability_id: TABLE_SPLIT_TABLE_CAPABILITY_ID,
            split_before_row: request.split_before_row,
            separator_paragraph_id: request.separator_paragraph_id.clone(),
            first: PlannedWholeTable::new(&first_grid, &first_state),
            second: PlannedWholeTable::new(&second_grid, &second_state),
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }

    /// Builds a pure, atomic vertical whole-table join plan. Neither source table is mutated.
    ///
    /// # Errors
    ///
    /// Rejects stale bindings, unrepresentable common column geometry, formula transformation,
    /// grid-limit excess and bounded serialization failures.
    #[allow(clippy::too_many_arguments)]
    pub fn join(
        request: &WholeTableJoinRequest,
        leading_state: &TablePartitionState,
        leading_grid: &TableGrid,
        trailing_state: &TablePartitionState,
        trailing_grid: &TableGrid,
        current_flow_sha256: &str,
        grid_limits: TableGridLimits,
        formula_limits: FormulaLimits,
        limits: TablePartitionLimits,
    ) -> Result<WholeTableJoinPlan, TablePartitionError> {
        validate_join_binding(
            request,
            leading_state,
            leading_grid,
            trailing_state,
            trailing_grid,
            current_flow_sha256,
            limits,
        )?;
        let lattice = common_lattice(leading_state, trailing_state)?;
        let leading_mapping = boundary_mapping(leading_state, &lattice)?;
        let trailing_mapping = boundary_mapping(trailing_state, &lattice)?;
        let joined_width = leading_state
            .table_width_hwpunit
            .max(trailing_state.table_width_hwpunit);
        let joined_column_widths = materialize_column_widths(&lattice, joined_width)?;
        let joined_grid = join_grid(
            leading_grid,
            trailing_grid,
            &leading_mapping,
            &trailing_mapping,
            grid_limits,
        )?;
        let joined = build_join_state(
            &JoinBuildContext {
                leading_state,
                leading_grid,
                trailing_state,
                trailing_grid,
                leading_mapping: &leading_mapping,
                trailing_mapping: &trailing_mapping,
                joined_grid: &joined_grid,
            },
            joined_width,
            joined_column_widths,
            request.formula_policy,
            formula_limits,
            limits,
        )?;
        let joined_state = joined.state;
        let joined_state_sha256 = state_digest(&joined_state, limits)?;
        let after_flow_sha256 =
            join_flow_digest(&request.expected_flow_sha256, &joined_state_sha256, limits)?;
        let receipt = WholeTableJoinReceipt {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION,
            capability_id: TABLE_JOIN_TABLE_CAPABILITY_ID,
            request_sha256: hex(request.canonical_sha256(limits)?),
            before_flow_sha256: request.expected_flow_sha256.clone(),
            after_flow_sha256,
            leading_state_sha256: request.expected_leading_state_sha256.clone(),
            trailing_state_sha256: request.expected_trailing_state_sha256.clone(),
            joined_state_sha256,
            leading_row_count: leading_grid.rows(),
            trailing_row_count: trailing_grid.rows(),
            joined_row_count: joined_grid.rows(),
            joined_column_count: joined_grid.columns(),
            joined_width_hwpunit: joined_width,
            preserved_master_cell_count: joined_state.cells.len(),
            preserved_payload_count: joined_state.cells.len(),
            preserved_cell_properties_count: joined_state.cells.len(),
            formula_rebased_count: joined.counts.rebased,
            formula_cache_cleared_count: joined.counts.caches_cleared,
            leading_table_properties_retained: true,
            trailing_table_properties_discarded: true,
            removed_table_count: 1,
            removed_separator_token_count: request.separator_tokens.len(),
        };
        let plan = WholeTableJoinPlan {
            schema_version: TABLE_PARTITION_SCHEMA_VERSION,
            capability_id: TABLE_JOIN_TABLE_CAPABILITY_ID,
            joined: PlannedWholeTable::new(&joined_grid, &joined_state),
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

fn validate_split_binding(
    request: &WholeTableSplitRequest,
    state: &TablePartitionState,
    grid: &TableGrid,
    current_flow_sha256: &str,
    limits: TablePartitionLimits,
) -> Result<(), TablePartitionError> {
    validate_state_grid(state, grid)?;
    validate_flow_binding(&request.expected_flow_sha256, current_flow_sha256)?;
    if request.table_id != state.table_id
        || request.grid_sha256 != state.grid_sha256
        || request.expected_state_sha256 != state_digest(state, limits)?
        || request.split_before_row != request.cursor.row
        || request.split_before_row == 0
        || request.split_before_row >= grid.rows()
    {
        return Err(TablePartitionError::StateBindingMismatch);
    }
    validate_split_boundary(grid, request.split_before_row)
}

fn validate_join_binding(
    request: &WholeTableJoinRequest,
    leading_state: &TablePartitionState,
    leading_grid: &TableGrid,
    trailing_state: &TablePartitionState,
    trailing_grid: &TableGrid,
    current_flow_sha256: &str,
    limits: TablePartitionLimits,
) -> Result<(), TablePartitionError> {
    validate_state_grid(leading_state, leading_grid)?;
    validate_state_grid(trailing_state, trailing_grid)?;
    validate_flow_binding(&request.expected_flow_sha256, current_flow_sha256)?;
    if request.leading_table_id != leading_state.table_id
        || request.trailing_table_id != trailing_state.table_id
        || request.leading_grid_sha256 != leading_state.grid_sha256
        || request.trailing_grid_sha256 != trailing_state.grid_sha256
        || request.expected_leading_state_sha256 != state_digest(leading_state, limits)?
        || request.expected_trailing_state_sha256 != state_digest(trailing_state, limits)?
    {
        return Err(TablePartitionError::StateBindingMismatch);
    }
    validate_separator(&request.separator_tokens, limits)
}

fn validate_state_grid(
    state: &TablePartitionState,
    grid: &TableGrid,
) -> Result<(), TablePartitionError> {
    if state.grid_sha256 != grid_digest(grid)? || state.cells.len() != grid.master_cell_count() {
        return Err(TablePartitionError::GridMismatch);
    }
    Ok(())
}

fn validate_split_boundary(
    grid: &TableGrid,
    split_before_row: u32,
) -> Result<(), TablePartitionError> {
    for span in grid.master_cells() {
        let end = span
            .row
            .checked_add(span.row_span)
            .ok_or(TablePartitionError::JoinedGridUnsupported)?;
        if span.row < split_before_row && end > split_before_row {
            return Err(TablePartitionError::SpanBoundaryConflict);
        }
    }
    Ok(())
}

fn split_grid(
    grid: &TableGrid,
    split_before_row: u32,
    grid_limits: TableGridLimits,
) -> Result<(TableGrid, TableGrid), TablePartitionError> {
    validate_split_boundary(grid, split_before_row)?;
    let mut first = fallible_vec(grid.master_cell_count())?;
    let mut second = fallible_vec(grid.master_cell_count())?;
    for span in grid.master_cells() {
        if span.row < split_before_row {
            first.push(span.clone());
        } else {
            let mut shifted = span.clone();
            shifted.row = shifted
                .row
                .checked_sub(split_before_row)
                .ok_or(TablePartitionError::JoinedGridUnsupported)?;
            second.push(shifted);
        }
    }
    let first_grid = TableGrid::new(split_before_row, grid.columns(), first, grid_limits)
        .map_err(|_| TablePartitionError::JoinedGridUnsupported)?;
    let second_grid = TableGrid::new(
        grid.rows() - split_before_row,
        grid.columns(),
        second,
        grid_limits,
    )
    .map_err(|_| TablePartitionError::JoinedGridUnsupported)?;
    Ok((first_grid, second_grid))
}

#[derive(Default)]
struct FormulaCounts {
    rebased: usize,
    caches_cleared: usize,
}

struct SplitCells {
    first: Vec<TablePartitionCell>,
    second: Vec<TablePartitionCell>,
    counts: FormulaCounts,
}

fn split_cells(
    request: &WholeTableSplitRequest,
    state: &TablePartitionState,
    grid: &TableGrid,
    first_grid: &TableGrid,
    second_grid: &TableGrid,
    formula_limits: FormulaLimits,
) -> Result<SplitCells, TablePartitionError> {
    let mut result = SplitCells {
        first: fallible_vec(first_grid.master_cell_count())?,
        second: fallible_vec(second_grid.master_cell_count())?,
        counts: FormulaCounts::default(),
    };
    let before_dimensions = dimensions(grid);
    for cell in &state.cells {
        let original_cache = cell.formula.as_ref().map(FormulaCell::cache);
        let (coordinate, formula, first) = if cell.coordinate.row < request.split_before_row {
            let formula = rebase_split_formula(
                cell.formula.as_ref(),
                FormulaGridEdit::DeleteRows {
                    before: before_dimensions,
                    index: request.split_before_row,
                    count: grid.rows() - request.split_before_row,
                },
                request.formula_policy,
                formula_limits,
            )?;
            (cell.coordinate, formula, true)
        } else {
            let coordinate = CellCoordinate {
                row: cell.coordinate.row - request.split_before_row,
                column: cell.coordinate.column,
            };
            let formula = rebase_split_formula(
                cell.formula.as_ref(),
                FormulaGridEdit::DeleteRows {
                    before: before_dimensions,
                    index: 0,
                    count: request.split_before_row,
                },
                request.formula_policy,
                formula_limits,
            )?;
            (coordinate, formula, false)
        };
        if formula.is_some() {
            result.counts.rebased = checked_add(result.counts.rebased, 1)?;
            if original_cache.is_some_and(|cache| !matches!(cache, FormulaCache::Absent)) {
                result.counts.caches_cleared = checked_add(result.counts.caches_cleared, 1)?;
            }
        }
        let output = TablePartitionCell {
            master_cell_id: cell.master_cell_id.clone(),
            coordinate,
            payload_sha256: cell.payload_sha256.clone(),
            cell_properties_sha256: cell.cell_properties_sha256.clone(),
            formula,
        };
        if first {
            result.first.push(output);
        } else {
            result.second.push(output);
        }
    }
    Ok(result)
}

fn rebase_split_formula(
    formula: Option<&FormulaCell>,
    edit: FormulaGridEdit,
    policy: TablePartitionFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<Option<FormulaCell>, TablePartitionError> {
    match (formula, policy) {
        (None, _) => Ok(None),
        (Some(_), TablePartitionFormulaPolicy::Reject) => Err(TablePartitionError::FormulaPresent),
        (Some(formula), TablePartitionFormulaPolicy::RebaseAndClearCache) => formula
            .apply_grid_edit(edit, FormulaCachePolicy::Clear, None, formula_limits)
            .map(Some)
            .map_err(|_| TablePartitionError::FormulaCrossBoundary),
    }
}

#[derive(Clone, Copy, Eq, PartialEq)]
struct Fraction {
    numerator: u64,
    denominator: u64,
}

impl Ord for Fraction {
    fn cmp(&self, other: &Self) -> Ordering {
        (u128::from(self.numerator) * u128::from(other.denominator))
            .cmp(&(u128::from(other.numerator) * u128::from(self.denominator)))
    }
}

impl PartialOrd for Fraction {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn common_lattice(
    leading: &TablePartitionState,
    trailing: &TablePartitionState,
) -> Result<Vec<Fraction>, TablePartitionError> {
    let mut boundaries = table_boundaries(leading)?;
    boundaries.extend(table_boundaries(trailing)?);
    boundaries.sort_unstable();
    boundaries.dedup();
    if boundaries.len() < 2 {
        return Err(TablePartitionError::ColumnGeometryMismatch);
    }
    Ok(boundaries)
}

fn table_boundaries(state: &TablePartitionState) -> Result<Vec<Fraction>, TablePartitionError> {
    let mut result = fallible_vec(state.column_widths_hwpunit.len() + 1)?;
    result.push(Fraction {
        numerator: 0,
        denominator: 1,
    });
    let mut cumulative = 0_u64;
    let total = u64::from(state.table_width_hwpunit);
    for width in &state.column_widths_hwpunit {
        cumulative = cumulative
            .checked_add(u64::from(*width))
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?;
        let divisor = gcd(cumulative, total);
        result.push(Fraction {
            numerator: cumulative / divisor,
            denominator: total / divisor,
        });
    }
    Ok(result)
}

fn boundary_mapping(
    state: &TablePartitionState,
    lattice: &[Fraction],
) -> Result<Vec<u32>, TablePartitionError> {
    let source = table_boundaries(state)?;
    let mut mapping = fallible_vec(source.len())?;
    for boundary in source {
        let index = lattice
            .binary_search(&boundary)
            .map_err(|_| TablePartitionError::ColumnGeometryMismatch)?;
        mapping.push(u32::try_from(index).map_err(|_| TablePartitionError::JoinedGridUnsupported)?);
    }
    Ok(mapping)
}

fn materialize_column_widths(
    lattice: &[Fraction],
    table_width_hwpunit: u32,
) -> Result<Vec<u32>, TablePartitionError> {
    let mut positions = fallible_vec(lattice.len())?;
    for boundary in lattice {
        let scaled = u128::from(boundary.numerator) * u128::from(table_width_hwpunit);
        let denominator = u128::from(boundary.denominator);
        let rounded = scaled
            .checked_add(denominator / 2)
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?
            / denominator;
        positions
            .push(u32::try_from(rounded).map_err(|_| TablePartitionError::ColumnGeometryMismatch)?);
    }
    if positions.first() != Some(&0)
        || positions.last() != Some(&table_width_hwpunit)
        || positions.windows(2).any(|pair| pair[0] >= pair[1])
    {
        return Err(TablePartitionError::ColumnGeometryUnrepresentable);
    }
    let mut widths = fallible_vec(positions.len() - 1)?;
    for pair in positions.windows(2) {
        widths.push(pair[1] - pair[0]);
    }
    Ok(widths)
}

fn join_grid(
    leading: &TableGrid,
    trailing: &TableGrid,
    leading_mapping: &[u32],
    trailing_mapping: &[u32],
    grid_limits: TableGridLimits,
) -> Result<TableGrid, TablePartitionError> {
    let rows = leading
        .rows()
        .checked_add(trailing.rows())
        .ok_or(TablePartitionError::JoinedGridUnsupported)?;
    let columns = leading_mapping
        .last()
        .copied()
        .ok_or(TablePartitionError::ColumnGeometryMismatch)?;
    if columns
        != trailing_mapping
            .last()
            .copied()
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?
    {
        return Err(TablePartitionError::ColumnGeometryMismatch);
    }
    let capacity = leading
        .master_cell_count()
        .checked_add(trailing.master_cell_count())
        .ok_or(TablePartitionError::MasterCellLimit)?;
    let mut spans = fallible_vec(capacity)?;
    append_mapped_spans(&mut spans, leading, leading_mapping, 0)?;
    append_mapped_spans(&mut spans, trailing, trailing_mapping, leading.rows())?;
    TableGrid::new(rows, columns, spans, grid_limits)
        .map_err(|_| TablePartitionError::JoinedGridUnsupported)
}

fn append_mapped_spans(
    output: &mut Vec<TableCellSpan>,
    grid: &TableGrid,
    mapping: &[u32],
    row_offset: u32,
) -> Result<(), TablePartitionError> {
    for span in grid.master_cells() {
        let start = usize::try_from(span.column)
            .map_err(|_| TablePartitionError::ColumnGeometryMismatch)?;
        let end = usize::try_from(
            span.column
                .checked_add(span.column_span)
                .ok_or(TablePartitionError::ColumnGeometryMismatch)?,
        )
        .map_err(|_| TablePartitionError::ColumnGeometryMismatch)?;
        let mapped_start = *mapping
            .get(start)
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?;
        let mapped_end = *mapping
            .get(end)
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?;
        output.push(TableCellSpan {
            master_cell_id: span.master_cell_id.clone(),
            row: span
                .row
                .checked_add(row_offset)
                .ok_or(TablePartitionError::JoinedGridUnsupported)?,
            column: mapped_start,
            row_span: span.row_span,
            column_span: mapped_end
                .checked_sub(mapped_start)
                .ok_or(TablePartitionError::ColumnGeometryMismatch)?,
        });
    }
    Ok(())
}

struct JoinBuildContext<'a> {
    leading_state: &'a TablePartitionState,
    leading_grid: &'a TableGrid,
    trailing_state: &'a TablePartitionState,
    trailing_grid: &'a TableGrid,
    leading_mapping: &'a [u32],
    trailing_mapping: &'a [u32],
    joined_grid: &'a TableGrid,
}

struct JoinedState {
    state: TablePartitionState,
    counts: FormulaCounts,
}

fn build_join_state(
    context: &JoinBuildContext<'_>,
    joined_width: u32,
    joined_column_widths: Vec<u32>,
    policy: TablePartitionFormulaPolicy,
    formula_limits: FormulaLimits,
    limits: TablePartitionLimits,
) -> Result<JoinedState, TablePartitionError> {
    let mut cells = fallible_vec(
        context
            .leading_state
            .cells
            .len()
            .checked_add(context.trailing_state.cells.len())
            .ok_or(TablePartitionError::MasterCellLimit)?,
    )?;
    let mut counts = FormulaCounts::default();
    append_join_cells(
        &mut cells,
        context.leading_state,
        context.leading_grid,
        context.trailing_grid.rows(),
        0,
        context.leading_mapping,
        policy,
        formula_limits,
        &mut counts,
    )?;
    append_join_cells(
        &mut cells,
        context.trailing_state,
        context.trailing_grid,
        context.leading_grid.rows(),
        context.leading_grid.rows(),
        context.trailing_mapping,
        policy,
        formula_limits,
        &mut counts,
    )?;
    cells.sort_by(|left, right| {
        (left.coordinate, &left.master_cell_id).cmp(&(right.coordinate, &right.master_cell_id))
    });
    let state = TablePartitionState::from_validated_parts(
        context.leading_state.table_id.clone(),
        grid_digest(context.joined_grid)?,
        context.leading_state.table_properties_sha256.clone(),
        joined_width,
        joined_column_widths,
        cells,
        limits,
    )?;
    Ok(JoinedState { state, counts })
}

#[allow(clippy::too_many_arguments)]
fn append_join_cells(
    output: &mut Vec<TablePartitionCell>,
    state: &TablePartitionState,
    grid: &TableGrid,
    rows_to_insert: u32,
    row_offset: u32,
    mapping: &[u32],
    policy: TablePartitionFormulaPolicy,
    formula_limits: FormulaLimits,
    counts: &mut FormulaCounts,
) -> Result<(), TablePartitionError> {
    for cell in &state.cells {
        let mapped_column = *mapping
            .get(
                usize::try_from(cell.coordinate.column)
                    .map_err(|_| TablePartitionError::ColumnGeometryMismatch)?,
            )
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?;
        let coordinate = CellCoordinate {
            row: cell
                .coordinate
                .row
                .checked_add(row_offset)
                .ok_or(TablePartitionError::JoinedGridUnsupported)?,
            column: mapped_column,
        };
        let original_cache = cell.formula.as_ref().map(FormulaCell::cache);
        let formula = rebase_join_formula(
            cell.formula.as_ref(),
            grid,
            mapping,
            rows_to_insert,
            row_offset != 0,
            policy,
            formula_limits,
        )?;
        if let Some(formula) = &formula {
            if formula.owner() != coordinate {
                return Err(TablePartitionError::FormulaOwnerMismatch);
            }
            counts.rebased = checked_add(counts.rebased, 1)?;
            if original_cache.is_some_and(|cache| !matches!(cache, FormulaCache::Absent)) {
                counts.caches_cleared = checked_add(counts.caches_cleared, 1)?;
            }
        }
        output.push(TablePartitionCell {
            master_cell_id: cell.master_cell_id.clone(),
            coordinate,
            payload_sha256: cell.payload_sha256.clone(),
            cell_properties_sha256: cell.cell_properties_sha256.clone(),
            formula,
        });
    }
    Ok(())
}

fn rebase_join_formula(
    formula: Option<&FormulaCell>,
    grid: &TableGrid,
    mapping: &[u32],
    rows_to_insert: u32,
    insert_rows_before: bool,
    policy: TablePartitionFormulaPolicy,
    formula_limits: FormulaLimits,
) -> Result<Option<FormulaCell>, TablePartitionError> {
    let Some(mut formula) = formula.cloned() else {
        return Ok(None);
    };
    if policy == TablePartitionFormulaPolicy::Reject {
        return Err(TablePartitionError::FormulaPresent);
    }
    let mut dimensions = dimensions(grid);
    for column in 0..grid.columns() {
        let index =
            usize::try_from(column).map_err(|_| TablePartitionError::ColumnGeometryMismatch)?;
        let start = *mapping
            .get(index)
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?;
        let end = *mapping
            .get(index + 1)
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?;
        let count = end
            .checked_sub(start)
            .and_then(|width| width.checked_sub(1))
            .ok_or(TablePartitionError::ColumnGeometryMismatch)?;
        if count > 0 {
            formula = formula
                .apply_grid_edit(
                    FormulaGridEdit::InsertColumns {
                        before: dimensions,
                        index: start + 1,
                        count,
                    },
                    FormulaCachePolicy::Clear,
                    None,
                    formula_limits,
                )
                .map_err(|_| TablePartitionError::FormulaInvalid)?;
            dimensions.columns = dimensions
                .columns
                .checked_add(count)
                .ok_or(TablePartitionError::JoinedGridUnsupported)?;
        }
    }
    let row_index = if insert_rows_before { 0 } else { grid.rows() };
    formula = formula
        .apply_grid_edit(
            FormulaGridEdit::InsertRows {
                before: dimensions,
                index: row_index,
                count: rows_to_insert,
            },
            FormulaCachePolicy::Clear,
            None,
            formula_limits,
        )
        .map_err(|_| TablePartitionError::FormulaInvalid)?;
    Ok(Some(formula))
}

fn validate_separator(
    tokens: &[TableJoinSeparatorToken],
    limits: TablePartitionLimits,
) -> Result<(), TablePartitionError> {
    if tokens.is_empty() {
        return Err(TablePartitionError::EmptySeparator);
    }
    if tokens.len() > limits.0.separator_tokens {
        return Err(TablePartitionError::SeparatorLimit);
    }
    let mut spaces = 0_u32;
    let mut paragraph_break = false;
    for token in tokens {
        match token {
            TableJoinSeparatorToken::SpaceRun { count } => {
                if *count == 0 {
                    return Err(TablePartitionError::EmptySeparatorToken);
                }
                spaces = spaces
                    .checked_add(*count)
                    .ok_or(TablePartitionError::SeparatorLimit)?;
                if spaces > limits.0.separator_spaces {
                    return Err(TablePartitionError::SeparatorLimit);
                }
            }
            TableJoinSeparatorToken::ParagraphBreak => paragraph_break = true,
            TableJoinSeparatorToken::Content { content_sha256 }
            | TableJoinSeparatorToken::Object {
                object_sha256: content_sha256,
            } => {
                validate_digest(content_sha256)?;
                return Err(TablePartitionError::InterveningContent);
            }
        }
    }
    if !paragraph_break {
        return Err(TablePartitionError::MissingParagraphBreak);
    }
    Ok(())
}

#[derive(Serialize)]
struct SplitFlowIdentity<'a> {
    schema_version: &'static str,
    before_flow_sha256: &'a str,
    first_state_sha256: &'a str,
    separator_paragraph_id: &'a LogicalId,
    second_state_sha256: &'a str,
}

fn split_flow_digest(
    before_flow_sha256: &str,
    first_state_sha256: &str,
    separator_paragraph_id: &LogicalId,
    second_state_sha256: &str,
    limits: TablePartitionLimits,
) -> Result<String, TablePartitionError> {
    let identity = SplitFlowIdentity {
        schema_version: TABLE_PARTITION_SCHEMA_VERSION,
        before_flow_sha256,
        first_state_sha256,
        separator_paragraph_id,
        second_state_sha256,
    };
    Ok(hex(Sha256::digest(serialize_bounded(
        &identity,
        limits.0.serialized_bytes,
    )?)))
}

#[derive(Serialize)]
struct JoinFlowIdentity<'a> {
    schema_version: &'static str,
    before_flow_sha256: &'a str,
    joined_state_sha256: &'a str,
}

fn join_flow_digest(
    before_flow_sha256: &str,
    joined_state_sha256: &str,
    limits: TablePartitionLimits,
) -> Result<String, TablePartitionError> {
    let identity = JoinFlowIdentity {
        schema_version: TABLE_PARTITION_SCHEMA_VERSION,
        before_flow_sha256,
        joined_state_sha256,
    };
    Ok(hex(Sha256::digest(serialize_bounded(
        &identity,
        limits.0.serialized_bytes,
    )?)))
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TablePartitionError {
    #[error("table partition limits are invalid")]
    InvalidLimit,
    #[error("table partition schema version is unsupported")]
    UnsupportedVersion,
    #[error("table partition JSON input is empty or oversized")]
    InputLimit,
    #[error("table partition JSON is invalid")]
    InvalidJson,
    #[error("table partition identifier exceeds its configured bound")]
    IdentifierLimit,
    #[error("table partition digest is invalid")]
    DigestInvalid,
    #[error("table partition grid binding does not match")]
    GridMismatch,
    #[error("table partition master-cell set does not exactly match the grid")]
    CellSetMismatch,
    #[error("table partition table width or column geometry is invalid")]
    ColumnGeometryMismatch,
    #[error("table partition common column geometry cannot be represented in HWPUNIT")]
    ColumnGeometryUnrepresentable,
    #[error("table partition table identity does not match the bound state")]
    TableIdentityMismatch,
    #[error("table partition output identities must be distinct")]
    DuplicateOutputIdentity,
    #[error("table split cursor is outside the exact grid")]
    CursorOutOfBounds,
    #[error("table split cannot start at the first row")]
    FirstRowSplit,
    #[error("table split boundary crosses a row-spanning master cell")]
    SpanBoundaryConflict,
    #[error("table partition formula policy rejects formula cells")]
    FormulaPresent,
    #[error("table partition formula is invalid")]
    FormulaInvalid,
    #[error("table partition formula owner does not match its master cell")]
    FormulaOwnerMismatch,
    #[error("table split would create a cross-table formula reference")]
    FormulaCrossBoundary,
    #[error("table partition state binding is stale")]
    StateBindingMismatch,
    #[error("table partition document-flow binding is stale")]
    FlowBindingMismatch,
    #[error("table join separator is empty")]
    EmptySeparator,
    #[error("table join separator contains an empty token")]
    EmptySeparatorToken,
    #[error("table join separator exceeds its configured bound")]
    SeparatorLimit,
    #[error("table join separator contains non-whitespace content")]
    InterveningContent,
    #[error("table join separator has no paragraph break")]
    MissingParagraphBreak,
    #[error("table join source tables reuse a master-cell identity")]
    DuplicateMasterCell,
    #[error("table join master-cell work exceeds its configured bound")]
    MasterCellLimit,
    #[error("table split or join output grid is unsupported")]
    JoinedGridUnsupported,
    #[error("table partition output exceeds its configured bound")]
    OutputLimit,
    #[error("table partition serialization failed")]
    Serialization,
    #[error("table partition allocation failed")]
    AllocationFailed,
}

impl TablePartitionError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_partition_invalid_limit",
            Self::UnsupportedVersion => "table_partition_unsupported_version",
            Self::InputLimit => "table_partition_input_limit",
            Self::InvalidJson => "table_partition_invalid_json",
            Self::IdentifierLimit => "table_partition_identifier_limit",
            Self::DigestInvalid => "table_partition_digest_invalid",
            Self::GridMismatch => "table_partition_grid_mismatch",
            Self::CellSetMismatch => "table_partition_cell_set_mismatch",
            Self::ColumnGeometryMismatch => "table_partition_column_geometry_mismatch",
            Self::ColumnGeometryUnrepresentable => {
                "table_partition_column_geometry_unrepresentable"
            }
            Self::TableIdentityMismatch => "table_partition_table_identity_mismatch",
            Self::DuplicateOutputIdentity => "table_partition_duplicate_output_identity",
            Self::CursorOutOfBounds => "table_partition_cursor_out_of_bounds",
            Self::FirstRowSplit => "table_partition_first_row_split",
            Self::SpanBoundaryConflict => "table_partition_span_boundary_conflict",
            Self::FormulaPresent => "table_partition_formula_present",
            Self::FormulaInvalid => "table_partition_formula_invalid",
            Self::FormulaOwnerMismatch => "table_partition_formula_owner_mismatch",
            Self::FormulaCrossBoundary => "table_partition_formula_cross_boundary",
            Self::StateBindingMismatch => "table_partition_state_binding_mismatch",
            Self::FlowBindingMismatch => "table_partition_flow_binding_mismatch",
            Self::EmptySeparator => "table_partition_empty_separator",
            Self::EmptySeparatorToken => "table_partition_empty_separator_token",
            Self::SeparatorLimit => "table_partition_separator_limit",
            Self::InterveningContent => "table_partition_intervening_content",
            Self::MissingParagraphBreak => "table_partition_missing_paragraph_break",
            Self::DuplicateMasterCell => "table_partition_duplicate_master_cell",
            Self::MasterCellLimit => "table_partition_master_cell_limit",
            Self::JoinedGridUnsupported => "table_partition_joined_grid_unsupported",
            Self::OutputLimit => "table_partition_output_limit",
            Self::Serialization => "table_partition_serialization",
            Self::AllocationFailed => "table_partition_allocation",
        }
    }
}

fn validate_column_widths(
    table_width_hwpunit: u32,
    column_widths_hwpunit: &[u32],
    columns: u32,
    limits: TablePartitionLimits,
) -> Result<(), TablePartitionError> {
    if table_width_hwpunit == 0 || table_width_hwpunit > limits.0.table_width_hwpunit {
        return Err(TablePartitionError::ColumnGeometryMismatch);
    }
    if column_widths_hwpunit.len()
        != usize::try_from(columns).map_err(|_| TablePartitionError::ColumnGeometryMismatch)?
        || column_widths_hwpunit.contains(&0)
    {
        return Err(TablePartitionError::ColumnGeometryMismatch);
    }
    let sum = column_widths_hwpunit
        .iter()
        .try_fold(0_u32, |total, width| total.checked_add(*width));
    if sum != Some(table_width_hwpunit) {
        return Err(TablePartitionError::ColumnGeometryMismatch);
    }
    Ok(())
}

fn validate_identifier(
    identifier: &LogicalId,
    limits: TablePartitionLimits,
) -> Result<(), TablePartitionError> {
    if identifier.as_str().len() > limits.0.identifier_bytes {
        return Err(TablePartitionError::IdentifierLimit);
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), TablePartitionError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TablePartitionError::DigestInvalid);
    }
    Ok(())
}

fn validate_flow_binding(expected: &str, current: &str) -> Result<(), TablePartitionError> {
    validate_digest(expected)?;
    validate_digest(current)?;
    if expected != current {
        return Err(TablePartitionError::FlowBindingMismatch);
    }
    Ok(())
}

fn validate_input(bytes: &[u8], limits: TablePartitionLimits) -> Result<(), TablePartitionError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(TablePartitionError::InputLimit);
    }
    Ok(())
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

fn grid_digest(grid: &TableGrid) -> Result<String, TablePartitionError> {
    grid.canonical_sha256()
        .map(hex)
        .map_err(|_| TablePartitionError::GridMismatch)
}

fn state_digest(
    state: &TablePartitionState,
    limits: TablePartitionLimits,
) -> Result<String, TablePartitionError> {
    state.canonical_sha256(limits).map(hex)
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TablePartitionError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TablePartitionError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TablePartitionError::OutputLimit);
    }
    Ok(bytes)
}

fn fallible_vec<T>(capacity: usize) -> Result<Vec<T>, TablePartitionError> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| TablePartitionError::AllocationFailed)?;
    Ok(values)
}

fn checked_add(value: usize, increment: usize) -> Result<usize, TablePartitionError> {
    value
        .checked_add(increment)
        .ok_or(TablePartitionError::MasterCellLimit)
}

const fn gcd(mut left: u64, mut right: u64) -> u64 {
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    if left == 0 { 1 } else { left }
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    let bytes = bytes.as_ref();
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(output, "{byte:02x}");
    }
    output
}
