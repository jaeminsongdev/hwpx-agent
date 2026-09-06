use std::fmt;
use std::io;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const TABLE_GRID_SCHEMA_VERSION: &str = "hwpx-agent.table-grid/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableGridLimitConfig {
    pub rows: u32,
    pub columns: u32,
    pub slots: usize,
    pub master_cells: usize,
    pub identifier_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for TableGridLimitConfig {
    fn default() -> Self {
        Self {
            rows: 10_000,
            columns: 1_024,
            slots: 1_000_000,
            master_cells: 1_000_000,
            identifier_bytes: 256,
            serialized_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableGridLimits(TableGridLimitConfig);

impl TableGridLimits {
    pub const HARD_MAX_ROWS: u32 = 10_000;
    pub const HARD_MAX_COLUMNS: u32 = 1_024;
    pub const HARD_MAX_SLOTS: usize = 1_000_000;
    pub const HARD_MAX_MASTER_CELLS: usize = 1_000_000;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 1_024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for the P06 table-grid boundary.
    ///
    /// # Errors
    ///
    /// Returns [`TableGridError::InvalidLimit`] for zero, over-ceiling, or internally inconsistent
    /// values.
    pub fn new(config: TableGridLimitConfig) -> Result<Self, TableGridError> {
        if config.rows == 0
            || config.rows > Self::HARD_MAX_ROWS
            || config.columns == 0
            || config.columns > Self::HARD_MAX_COLUMNS
            || config.slots == 0
            || config.slots > Self::HARD_MAX_SLOTS
            || config.master_cells == 0
            || config.master_cells > Self::HARD_MAX_MASTER_CELLS
            || config.master_cells > config.slots
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(TableGridError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableGridLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CellCoordinate {
    pub row: u32,
    pub column: u32,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCellSpan {
    pub master_cell_id: LogicalId,
    pub row: u32,
    pub column: u32,
    pub row_span: u32,
    pub column_span: u32,
}

impl TableCellSpan {
    /// Infers one rectangular span from an explicit set of covered logical slots.
    ///
    /// The top-left coordinate becomes the master-cell coordinate. Input order is irrelevant.
    ///
    /// # Errors
    ///
    /// Rejects empty, duplicate, over-limit, overflowing, or non-rectangular slot sets.
    pub fn from_covered_slots(
        master_cell_id: LogicalId,
        mut covered_slots: Vec<CellCoordinate>,
        limits: TableGridLimits,
    ) -> Result<Self, TableGridError> {
        validate_identifier(&master_cell_id, limits)?;
        if covered_slots.is_empty() {
            return Err(TableGridError::EmptySpan);
        }
        if covered_slots.len() > limits.0.slots {
            return Err(TableGridError::SlotLimitExceeded);
        }
        covered_slots.sort_unstable();
        if covered_slots.windows(2).any(|pair| pair[0] == pair[1]) {
            return Err(TableGridError::DuplicateCoveredSlot);
        }

        let first = covered_slots[0];
        let mut first_row = first.row;
        let mut first_column = first.column;
        let mut last_row = first.row;
        let mut last_column = first.column;
        for coordinate in &covered_slots[1..] {
            first_row = first_row.min(coordinate.row);
            first_column = first_column.min(coordinate.column);
            last_row = last_row.max(coordinate.row);
            last_column = last_column.max(coordinate.column);
        }
        let row_span = last_row
            .checked_sub(first_row)
            .and_then(|value| value.checked_add(1))
            .ok_or(TableGridError::SpanOverflow)?;
        let column_span = last_column
            .checked_sub(first_column)
            .and_then(|value| value.checked_add(1))
            .ok_or(TableGridError::SpanOverflow)?;
        let rectangle_size = checked_slot_capacity(row_span, column_span)?;
        if rectangle_size != covered_slots.len() {
            return Err(TableGridError::NonRectangularSpan);
        }

        Ok(Self {
            master_cell_id,
            row: first_row,
            column: first_column,
            row_span,
            column_span,
        })
    }

    #[must_use]
    pub fn covers(&self, coordinate: CellCoordinate) -> bool {
        let Some(row_end) = self.row.checked_add(self.row_span) else {
            return false;
        };
        let Some(column_end) = self.column.checked_add(self.column_span) else {
            return false;
        };
        coordinate.row >= self.row
            && coordinate.row < row_end
            && coordinate.column >= self.column
            && coordinate.column < column_end
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableGridDraft {
    pub schema_version: String,
    pub rows: u32,
    pub columns: u32,
    pub master_cells: Vec<TableCellSpan>,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableGrid {
    rows: u32,
    columns: u32,
    master_cells: Vec<TableCellSpan>,
    slot_master_indexes: Vec<usize>,
}

impl TableGrid {
    /// Validates and canonicalizes an untrusted table-grid draft.
    ///
    /// # Errors
    ///
    /// Fails closed on version, limit, identifier, span, overlap, gap, allocation, or serialization
    /// violations.
    pub fn from_draft(
        draft: TableGridDraft,
        limits: TableGridLimits,
    ) -> Result<Self, TableGridError> {
        if draft.schema_version != TABLE_GRID_SCHEMA_VERSION {
            return Err(TableGridError::UnsupportedVersion);
        }
        validate_dimensions(draft.rows, draft.columns, limits)?;
        if draft.master_cells.len() > limits.0.master_cells {
            return Err(TableGridError::MasterCellLimitExceeded);
        }

        let mut master_cells = draft.master_cells;
        master_cells.sort_by(|left, right| {
            (left.row, left.column, &left.master_cell_id).cmp(&(
                right.row,
                right.column,
                &right.master_cell_id,
            ))
        });
        validate_master_identifiers(&master_cells, limits)?;
        let slot_master_indexes =
            build_slot_map(draft.rows, draft.columns, &master_cells, limits.0.slots)?;
        let grid = Self {
            rows: draft.rows,
            columns: draft.columns,
            master_cells,
            slot_master_indexes,
        };
        let _ = grid.canonical_json_with_max_bytes(limits.0.serialized_bytes)?;
        Ok(grid)
    }

    /// Deserializes and validates an untrusted canonical table-grid document.
    ///
    /// # Errors
    ///
    /// Returns a stable error for oversized or malformed JSON and all invariant violations reported
    /// by [`Self::from_draft`].
    pub fn from_json(bytes: &[u8], limits: TableGridLimits) -> Result<Self, TableGridError> {
        if bytes.len() > limits.0.serialized_bytes {
            return Err(TableGridError::InputLimitExceeded);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| TableGridError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    /// Creates a table grid from logical dimensions and master-cell rectangles.
    ///
    /// # Errors
    ///
    /// Propagates every invariant and limit failure from [`Self::from_draft`].
    pub fn new(
        rows: u32,
        columns: u32,
        master_cells: Vec<TableCellSpan>,
        limits: TableGridLimits,
    ) -> Result<Self, TableGridError> {
        Self::from_draft(
            TableGridDraft {
                schema_version: TABLE_GRID_SCHEMA_VERSION.to_owned(),
                rows,
                columns,
                master_cells,
            },
            limits,
        )
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
    pub fn slot_count(&self) -> usize {
        self.slot_master_indexes.len()
    }

    #[must_use]
    pub fn master_cell_count(&self) -> usize {
        self.master_cells.len()
    }

    #[must_use]
    pub fn master_cells(&self) -> &[TableCellSpan] {
        &self.master_cells
    }

    /// Resolves a logical slot to its single master cell.
    ///
    /// # Errors
    ///
    /// Returns [`TableGridError::CoordinateOutOfBounds`] when the coordinate is outside the grid.
    pub fn master_cell_at(
        &self,
        coordinate: CellCoordinate,
    ) -> Result<&TableCellSpan, TableGridError> {
        if coordinate.row >= self.rows || coordinate.column >= self.columns {
            return Err(TableGridError::CoordinateOutOfBounds);
        }
        let slot_index = checked_slot_index(coordinate.row, coordinate.column, self.columns)?;
        let master_index = self.slot_master_indexes[slot_index];
        self.master_cells
            .get(master_index)
            .ok_or(TableGridError::UncoveredSlot)
    }

    /// Emits stable compact JSON with master cells ordered by their top-left coordinate.
    ///
    /// # Errors
    ///
    /// Returns a stable limit, allocation, or serialization error.
    pub fn canonical_json(&self) -> Result<Vec<u8>, TableGridError> {
        self.canonical_json_with_max_bytes(TableGridLimits::HARD_MAX_SERIALIZED_BYTES)
    }

    /// Emits stable compact JSON under a caller-provided finite output limit.
    ///
    /// # Errors
    ///
    /// Rejects zero or over-ceiling output limits and returns stable allocation/serialization errors.
    pub fn canonical_json_with_max_bytes(
        &self,
        max_bytes: usize,
    ) -> Result<Vec<u8>, TableGridError> {
        if max_bytes == 0 || max_bytes > TableGridLimits::HARD_MAX_SERIALIZED_BYTES {
            return Err(TableGridError::InvalidLimit);
        }
        let canonical = CanonicalTableGrid {
            schema_version: TABLE_GRID_SCHEMA_VERSION,
            rows: self.rows,
            columns: self.columns,
            master_cells: &self.master_cells,
        };
        let mut writer = BoundedWriter::new(max_bytes);
        if serde_json::to_writer(&mut writer, &canonical).is_err() {
            return Err(match writer.failure {
                WriterFailure::Limit => TableGridError::OutputLimitExceeded,
                WriterFailure::Allocation => TableGridError::AllocationFailed,
                WriterFailure::None => TableGridError::SerializationFailed,
            });
        }
        Ok(writer.bytes)
    }

    /// Hashes the canonical serialized table grid.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], TableGridError> {
        Ok(Sha256::digest(self.canonical_json()?).into())
    }
}

impl fmt::Debug for TableGrid {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableGrid")
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("master_cell_count", &self.master_cells.len())
            .finish_non_exhaustive()
    }
}

#[derive(Serialize)]
struct CanonicalTableGrid<'a> {
    schema_version: &'static str,
    rows: u32,
    columns: u32,
    master_cells: &'a [TableCellSpan],
}

fn validate_dimensions(
    rows: u32,
    columns: u32,
    limits: TableGridLimits,
) -> Result<usize, TableGridError> {
    if rows == 0 || columns == 0 {
        return Err(TableGridError::EmptyGrid);
    }
    if rows > limits.0.rows || columns > limits.0.columns {
        return Err(TableGridError::DimensionLimitExceeded);
    }
    let slot_count = checked_slot_capacity(rows, columns)?;
    if slot_count > limits.0.slots {
        return Err(TableGridError::SlotLimitExceeded);
    }
    Ok(slot_count)
}

fn validate_master_identifiers(
    master_cells: &[TableCellSpan],
    limits: TableGridLimits,
) -> Result<(), TableGridError> {
    let mut identifier_order = Vec::new();
    identifier_order
        .try_reserve_exact(master_cells.len())
        .map_err(|_| TableGridError::AllocationFailed)?;
    for (index, master_cell) in master_cells.iter().enumerate() {
        validate_identifier(&master_cell.master_cell_id, limits)?;
        identifier_order.push(index);
    }
    identifier_order.sort_unstable_by(|left, right| {
        master_cells[*left]
            .master_cell_id
            .cmp(&master_cells[*right].master_cell_id)
    });
    if identifier_order
        .windows(2)
        .any(|pair| master_cells[pair[0]].master_cell_id == master_cells[pair[1]].master_cell_id)
    {
        return Err(TableGridError::DuplicateMasterCell);
    }
    Ok(())
}

fn validate_identifier(
    identifier: &LogicalId,
    limits: TableGridLimits,
) -> Result<(), TableGridError> {
    if identifier.as_str().len() > limits.0.identifier_bytes {
        return Err(TableGridError::IdentifierLimitExceeded);
    }
    Ok(())
}

fn build_slot_map(
    rows: u32,
    columns: u32,
    master_cells: &[TableCellSpan],
    max_slots: usize,
) -> Result<Vec<usize>, TableGridError> {
    let slot_count = checked_slot_capacity(rows, columns)?;
    if slot_count > max_slots {
        return Err(TableGridError::SlotLimitExceeded);
    }
    let mut slot_master_indexes = Vec::new();
    slot_master_indexes
        .try_reserve_exact(slot_count)
        .map_err(|_| TableGridError::AllocationFailed)?;
    slot_master_indexes.resize(slot_count, usize::MAX);

    for (master_index, master_cell) in master_cells.iter().enumerate() {
        let row_end = master_cell
            .row
            .checked_add(master_cell.row_span)
            .ok_or(TableGridError::SpanOverflow)?;
        let column_end = master_cell
            .column
            .checked_add(master_cell.column_span)
            .ok_or(TableGridError::SpanOverflow)?;
        if master_cell.row_span == 0 || master_cell.column_span == 0 {
            return Err(TableGridError::EmptySpan);
        }
        if master_cell.row >= rows
            || master_cell.column >= columns
            || row_end > rows
            || column_end > columns
        {
            return Err(TableGridError::SpanOutOfBounds);
        }
        for row in master_cell.row..row_end {
            for column in master_cell.column..column_end {
                let slot_index = checked_slot_index(row, column, columns)?;
                if slot_master_indexes[slot_index] != usize::MAX {
                    return Err(TableGridError::OverlappingSpan);
                }
                slot_master_indexes[slot_index] = master_index;
            }
        }
    }
    if slot_master_indexes.contains(&usize::MAX) {
        return Err(TableGridError::UncoveredSlot);
    }
    Ok(slot_master_indexes)
}

fn checked_slot_capacity(rows: u32, columns: u32) -> Result<usize, TableGridError> {
    let rows = usize::try_from(rows).map_err(|_| TableGridError::SlotCapacityOverflow)?;
    let columns = usize::try_from(columns).map_err(|_| TableGridError::SlotCapacityOverflow)?;
    rows.checked_mul(columns)
        .ok_or(TableGridError::SlotCapacityOverflow)
}

fn checked_slot_index(row: u32, column: u32, columns: u32) -> Result<usize, TableGridError> {
    let row = usize::try_from(row).map_err(|_| TableGridError::SlotCapacityOverflow)?;
    let column = usize::try_from(column).map_err(|_| TableGridError::SlotCapacityOverflow)?;
    let columns = usize::try_from(columns).map_err(|_| TableGridError::SlotCapacityOverflow)?;
    row.checked_mul(columns)
        .and_then(|offset| offset.checked_add(column))
        .ok_or(TableGridError::SlotCapacityOverflow)
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

impl io::Write for BoundedWriter {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        let Some(next_length) = self.bytes.len().checked_add(buffer.len()) else {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table grid output limit"));
        };
        if next_length > self.max_bytes {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table grid output limit"));
        }
        if self.bytes.try_reserve(buffer.len()).is_err() {
            self.failure = WriterFailure::Allocation;
            return Err(io::Error::other("table grid allocation"));
        }
        self.bytes.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableGridError {
    #[error("table grid limits are invalid")]
    InvalidLimit,
    #[error("table grid schema version is unsupported")]
    UnsupportedVersion,
    #[error("table grid JSON is invalid")]
    InvalidJson,
    #[error("table grid dimensions must be nonzero")]
    EmptyGrid,
    #[error("table grid dimensions exceed the configured limit")]
    DimensionLimitExceeded,
    #[error("table grid slot capacity overflowed")]
    SlotCapacityOverflow,
    #[error("table grid slots exceed the configured limit")]
    SlotLimitExceeded,
    #[error("table grid master cells exceed the configured limit")]
    MasterCellLimitExceeded,
    #[error("table grid master-cell identifier exceeds the configured limit")]
    IdentifierLimitExceeded,
    #[error("table grid contains a duplicate master-cell identifier")]
    DuplicateMasterCell,
    #[error("table cell span must be nonempty")]
    EmptySpan,
    #[error("table cell span overflowed")]
    SpanOverflow,
    #[error("table cell span is outside the grid")]
    SpanOutOfBounds,
    #[error("explicit table-cell coverage contains a duplicate slot")]
    DuplicateCoveredSlot,
    #[error("explicit table-cell coverage is not rectangular")]
    NonRectangularSpan,
    #[error("table cell spans overlap")]
    OverlappingSpan,
    #[error("table grid contains an uncovered slot")]
    UncoveredSlot,
    #[error("table grid coordinate is out of bounds")]
    CoordinateOutOfBounds,
    #[error("table grid canonical output exceeds the configured limit")]
    OutputLimitExceeded,
    #[error("table grid serialized input exceeds the configured limit")]
    InputLimitExceeded,
    #[error("table grid canonical serialization failed")]
    SerializationFailed,
    #[error("table grid allocation failed")]
    AllocationFailed,
}

impl TableGridError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_grid_invalid_limit",
            Self::UnsupportedVersion => "table_grid_unsupported_version",
            Self::InvalidJson => "table_grid_invalid_json",
            Self::EmptyGrid => "table_grid_empty_grid",
            Self::DimensionLimitExceeded => "table_grid_dimension_limit_exceeded",
            Self::SlotCapacityOverflow => "table_grid_slot_capacity_overflow",
            Self::SlotLimitExceeded => "table_grid_slot_limit_exceeded",
            Self::MasterCellLimitExceeded => "table_grid_master_cell_limit_exceeded",
            Self::IdentifierLimitExceeded => "table_grid_identifier_limit_exceeded",
            Self::DuplicateMasterCell => "table_grid_duplicate_master_cell",
            Self::EmptySpan => "table_grid_empty_span",
            Self::SpanOverflow => "table_grid_span_overflow",
            Self::SpanOutOfBounds => "table_grid_span_out_of_bounds",
            Self::DuplicateCoveredSlot => "table_grid_duplicate_covered_slot",
            Self::NonRectangularSpan => "table_grid_non_rectangular_span",
            Self::OverlappingSpan => "table_grid_overlapping_span",
            Self::UncoveredSlot => "table_grid_uncovered_slot",
            Self::CoordinateOutOfBounds => "table_grid_coordinate_out_of_bounds",
            Self::OutputLimitExceeded => "table_grid_output_limit_exceeded",
            Self::InputLimitExceeded => "table_grid_input_limit_exceeded",
            Self::SerializationFailed => "table_grid_serialization_failed",
            Self::AllocationFailed => "table_grid_allocation_failed",
        }
    }
}
