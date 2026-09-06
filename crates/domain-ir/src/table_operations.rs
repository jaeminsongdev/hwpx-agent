use std::fmt;

use serde::Serialize;
use thiserror::Error;

use crate::{CellCoordinate, LogicalId, TableCellSpan, TableGrid, TableGridError, TableGridLimits};

pub const TABLE_OPERATIONS_SCHEMA_VERSION: &str = "hwpx-agent.table-operations/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableOperationKind {
    Create,
    InsertRows,
    InsertColumns,
    DeleteRows,
    DeleteColumns,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct TableDimensions {
    pub rows: u32,
    pub columns: u32,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableCellRemap {
    master_cell_id: LogicalId,
    before: CellCoordinate,
    after: CellCoordinate,
}

impl TableCellRemap {
    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
    }

    #[must_use]
    pub const fn before(&self) -> CellCoordinate {
        self.before
    }

    #[must_use]
    pub const fn after(&self) -> CellCoordinate {
        self.after
    }
}

impl fmt::Debug for TableCellRemap {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCellRemap")
            .field("master_cell_id", &"<redacted>")
            .field("before", &self.before)
            .field("after", &self.after)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableOperationReceipt {
    schema_version: &'static str,
    operation: TableOperationKind,
    before: Option<TableDimensions>,
    after: TableDimensions,
    preserved_master_cells: Vec<TableCellRemap>,
    inserted_master_cell_ids: Vec<LogicalId>,
    deleted_master_cell_ids: Vec<LogicalId>,
}

impl TableOperationReceipt {
    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub const fn operation(&self) -> TableOperationKind {
        self.operation
    }

    #[must_use]
    pub const fn before(&self) -> Option<TableDimensions> {
        self.before
    }

    #[must_use]
    pub const fn after(&self) -> TableDimensions {
        self.after
    }

    #[must_use]
    pub fn preserved_master_cells(&self) -> &[TableCellRemap] {
        &self.preserved_master_cells
    }

    #[must_use]
    pub fn inserted_master_cell_ids(&self) -> &[LogicalId] {
        &self.inserted_master_cell_ids
    }

    #[must_use]
    pub fn deleted_master_cell_ids(&self) -> &[LogicalId] {
        &self.deleted_master_cell_ids
    }
}

impl fmt::Debug for TableOperationReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableOperationReceipt")
            .field("schema_version", &self.schema_version)
            .field("operation", &self.operation)
            .field("before", &self.before)
            .field("after", &self.after)
            .field(
                "preserved_master_cell_count",
                &self.preserved_master_cells.len(),
            )
            .field(
                "inserted_master_cell_count",
                &self.inserted_master_cell_ids.len(),
            )
            .field(
                "deleted_master_cell_count",
                &self.deleted_master_cell_ids.len(),
            )
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableOperationResult {
    grid: TableGrid,
    receipt: TableOperationReceipt,
}

impl TableOperationResult {
    #[must_use]
    pub const fn grid(&self) -> &TableGrid {
        &self.grid
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableOperationReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn into_parts(self) -> (TableGrid, TableOperationReceipt) {
        (self.grid, self.receipt)
    }
}

impl fmt::Debug for TableOperationResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableOperationResult")
            .field("grid", &self.grid)
            .field("receipt", &self.receipt)
            .finish()
    }
}

impl TableGrid {
    /// Creates a fully unmerged grid from exact row-major master-cell identifiers.
    ///
    /// # Errors
    ///
    /// Rejects invalid dimensions, an inexact identifier count, duplicate/oversized identifiers,
    /// finite-limit violations, and allocation failures without publishing a partial grid.
    pub fn create_unmerged(
        rows: u32,
        columns: u32,
        master_cell_ids: Vec<LogicalId>,
        limits: TableGridLimits,
    ) -> Result<TableOperationResult, TableOperationError> {
        let expected = validate_result_dimensions(rows, columns, limits)?;
        if master_cell_ids.len() != expected {
            return Err(TableOperationError::NewMasterCellCountMismatch);
        }

        let mut master_cells = fallible_vec(expected)?;
        for (index, master_cell_id) in master_cell_ids.into_iter().enumerate() {
            let coordinate = coordinate_from_row_major(index, columns)?;
            master_cells.push(TableCellSpan {
                master_cell_id,
                row: coordinate.row,
                column: coordinate.column,
                row_span: 1,
                column_span: 1,
            });
        }
        let grid = TableGrid::new(rows, columns, master_cells, limits)?;
        let inserted_master_cell_ids = clone_identifiers(grid.master_cells())?;
        Ok(TableOperationResult {
            receipt: TableOperationReceipt {
                schema_version: TABLE_OPERATIONS_SCHEMA_VERSION,
                operation: TableOperationKind::Create,
                before: None,
                after: dimensions(&grid),
                preserved_master_cells: Vec::new(),
                inserted_master_cell_ids,
                deleted_master_cell_ids: Vec::new(),
            },
            grid,
        })
    }

    /// Inserts rows at a zero-based boundary and creates one unmerged master cell per new slot.
    ///
    /// # Errors
    ///
    /// Rejects zero count, an index outside `0..=rows`, an inexact new-ID count, finite-limit
    /// violations, or an insertion boundary crossing an existing row span.
    pub fn insert_rows(
        &self,
        index: u32,
        count: u32,
        new_master_cell_ids: Vec<LogicalId>,
        limits: TableGridLimits,
    ) -> Result<TableOperationResult, TableOperationError> {
        self.insert_axis(Axis::Rows, index, count, new_master_cell_ids, limits)
    }

    /// Inserts columns at a zero-based boundary and creates one unmerged master cell per new slot.
    ///
    /// # Errors
    ///
    /// Rejects zero count, an index outside `0..=columns`, an inexact new-ID count, finite-limit
    /// violations, or an insertion boundary crossing an existing column span.
    pub fn insert_columns(
        &self,
        index: u32,
        count: u32,
        new_master_cell_ids: Vec<LogicalId>,
        limits: TableGridLimits,
    ) -> Result<TableOperationResult, TableOperationError> {
        self.insert_axis(Axis::Columns, index, count, new_master_cell_ids, limits)
    }

    /// Deletes rows only when every intersected master cell is removed in full.
    ///
    /// # Errors
    ///
    /// Rejects zero/out-of-range deletion, deleting the final row, or partially intersecting a row
    /// span. Surviving master identities remain unchanged.
    pub fn delete_rows(
        &self,
        index: u32,
        count: u32,
        limits: TableGridLimits,
    ) -> Result<TableOperationResult, TableOperationError> {
        self.delete_axis(Axis::Rows, index, count, limits)
    }

    /// Deletes columns only when every intersected master cell is removed in full.
    ///
    /// # Errors
    ///
    /// Rejects zero/out-of-range deletion, deleting the final column, or partially intersecting a
    /// column span. Surviving master identities remain unchanged.
    pub fn delete_columns(
        &self,
        index: u32,
        count: u32,
        limits: TableGridLimits,
    ) -> Result<TableOperationResult, TableOperationError> {
        self.delete_axis(Axis::Columns, index, count, limits)
    }

    fn insert_axis(
        &self,
        axis: Axis,
        index: u32,
        count: u32,
        new_master_cell_ids: Vec<LogicalId>,
        limits: TableGridLimits,
    ) -> Result<TableOperationResult, TableOperationError> {
        if count == 0 {
            return Err(TableOperationError::ZeroCount);
        }
        let current_dimension = axis.dimension(self);
        if index > current_dimension {
            return Err(TableOperationError::InsertionIndexOutOfBounds);
        }
        let new_dimension = current_dimension
            .checked_add(count)
            .ok_or(TableOperationError::DimensionOverflow)?;
        let (new_rows, new_columns) = axis.replace_dimension(self, new_dimension);
        let result_slots = validate_result_dimensions(new_rows, new_columns, limits)?;
        let expected_new_cells = checked_product(count, axis.orthogonal_dimension(self))?;
        if new_master_cell_ids.len() != expected_new_cells {
            return Err(TableOperationError::NewMasterCellCountMismatch);
        }
        let expected_masters = self
            .master_cell_count()
            .checked_add(expected_new_cells)
            .ok_or(TableOperationError::DimensionOverflow)?;
        if expected_masters > limits.config().master_cells || expected_masters > result_slots {
            return Err(TableGridError::MasterCellLimitExceeded.into());
        }

        for master_cell in self.master_cells() {
            let start = axis.cell_start(master_cell);
            let end = axis.cell_end(master_cell)?;
            if start < index && index < end {
                return Err(TableOperationError::SpanBoundaryConflict);
            }
        }

        let mut master_cells = fallible_vec(expected_masters)?;
        let mut remaps = fallible_vec(self.master_cell_count())?;
        for master_cell in self.master_cells() {
            let mut shifted = master_cell.clone();
            if axis.cell_start(master_cell) >= index {
                axis.set_cell_start(
                    &mut shifted,
                    axis.cell_start(master_cell)
                        .checked_add(count)
                        .ok_or(TableOperationError::DimensionOverflow)?,
                );
            }
            remaps.push(TableCellRemap {
                master_cell_id: master_cell.master_cell_id.clone(),
                before: cell_coordinate(master_cell),
                after: cell_coordinate(&shifted),
            });
            master_cells.push(shifted);
        }

        let insert_end = index
            .checked_add(count)
            .ok_or(TableOperationError::DimensionOverflow)?;
        let mut identifiers = new_master_cell_ids.into_iter();
        match axis {
            Axis::Rows => {
                for row in index..insert_end {
                    for column in 0..self.columns() {
                        master_cells.push(single_slot(
                            identifiers
                                .next()
                                .ok_or(TableOperationError::NewMasterCellCountMismatch)?,
                            row,
                            column,
                        ));
                    }
                }
            }
            Axis::Columns => {
                for row in 0..self.rows() {
                    for column in index..insert_end {
                        master_cells.push(single_slot(
                            identifiers
                                .next()
                                .ok_or(TableOperationError::NewMasterCellCountMismatch)?,
                            row,
                            column,
                        ));
                    }
                }
            }
        }
        if identifiers.next().is_some() {
            return Err(TableOperationError::NewMasterCellCountMismatch);
        }

        let grid = TableGrid::new(new_rows, new_columns, master_cells, limits)?;
        let inserted_master_cell_ids = identifiers_in_band(&grid, axis, index, insert_end)?;
        Ok(TableOperationResult {
            receipt: TableOperationReceipt {
                schema_version: TABLE_OPERATIONS_SCHEMA_VERSION,
                operation: axis.insert_kind(),
                before: Some(dimensions(self)),
                after: dimensions(&grid),
                preserved_master_cells: remaps,
                inserted_master_cell_ids,
                deleted_master_cell_ids: Vec::new(),
            },
            grid,
        })
    }

    fn delete_axis(
        &self,
        axis: Axis,
        index: u32,
        count: u32,
        limits: TableGridLimits,
    ) -> Result<TableOperationResult, TableOperationError> {
        if count == 0 {
            return Err(TableOperationError::ZeroCount);
        }
        let current_dimension = axis.dimension(self);
        let delete_end = index
            .checked_add(count)
            .ok_or(TableOperationError::DeletionRangeOutOfBounds)?;
        if index >= current_dimension || delete_end > current_dimension {
            return Err(TableOperationError::DeletionRangeOutOfBounds);
        }
        let new_dimension = current_dimension - count;
        if new_dimension == 0 {
            return Err(TableOperationError::WouldEmptyGrid);
        }
        let (new_rows, new_columns) = axis.replace_dimension(self, new_dimension);
        validate_result_dimensions(new_rows, new_columns, limits)?;

        let mut master_cells = fallible_vec(self.master_cell_count())?;
        let mut remaps = fallible_vec(self.master_cell_count())?;
        let mut deleted = fallible_vec(self.master_cell_count())?;
        for master_cell in self.master_cells() {
            let start = axis.cell_start(master_cell);
            let end = axis.cell_end(master_cell)?;
            let intersects = start < delete_end && end > index;
            if intersects {
                if start >= index && end <= delete_end {
                    deleted.push(master_cell.master_cell_id.clone());
                    continue;
                }
                return Err(TableOperationError::SpanBoundaryConflict);
            }

            let mut shifted = master_cell.clone();
            if start >= delete_end {
                axis.set_cell_start(
                    &mut shifted,
                    start
                        .checked_sub(count)
                        .ok_or(TableOperationError::DimensionOverflow)?,
                );
            }
            remaps.push(TableCellRemap {
                master_cell_id: master_cell.master_cell_id.clone(),
                before: cell_coordinate(master_cell),
                after: cell_coordinate(&shifted),
            });
            master_cells.push(shifted);
        }

        let grid = TableGrid::new(new_rows, new_columns, master_cells, limits)?;
        Ok(TableOperationResult {
            receipt: TableOperationReceipt {
                schema_version: TABLE_OPERATIONS_SCHEMA_VERSION,
                operation: axis.delete_kind(),
                before: Some(dimensions(self)),
                after: dimensions(&grid),
                preserved_master_cells: remaps,
                inserted_master_cell_ids: Vec::new(),
                deleted_master_cell_ids: deleted,
            },
            grid,
        })
    }
}

#[derive(Clone, Copy)]
enum Axis {
    Rows,
    Columns,
}

impl Axis {
    const fn dimension(self, grid: &TableGrid) -> u32 {
        match self {
            Self::Rows => grid.rows(),
            Self::Columns => grid.columns(),
        }
    }

    const fn orthogonal_dimension(self, grid: &TableGrid) -> u32 {
        match self {
            Self::Rows => grid.columns(),
            Self::Columns => grid.rows(),
        }
    }

    const fn replace_dimension(self, grid: &TableGrid, value: u32) -> (u32, u32) {
        match self {
            Self::Rows => (value, grid.columns()),
            Self::Columns => (grid.rows(), value),
        }
    }

    const fn cell_start(self, cell: &TableCellSpan) -> u32 {
        match self {
            Self::Rows => cell.row,
            Self::Columns => cell.column,
        }
    }

    fn cell_end(self, cell: &TableCellSpan) -> Result<u32, TableOperationError> {
        self.cell_start(cell)
            .checked_add(match self {
                Self::Rows => cell.row_span,
                Self::Columns => cell.column_span,
            })
            .ok_or(TableOperationError::DimensionOverflow)
    }

    const fn set_cell_start(self, cell: &mut TableCellSpan, value: u32) {
        match self {
            Self::Rows => cell.row = value,
            Self::Columns => cell.column = value,
        }
    }

    const fn insert_kind(self) -> TableOperationKind {
        match self {
            Self::Rows => TableOperationKind::InsertRows,
            Self::Columns => TableOperationKind::InsertColumns,
        }
    }

    const fn delete_kind(self) -> TableOperationKind {
        match self {
            Self::Rows => TableOperationKind::DeleteRows,
            Self::Columns => TableOperationKind::DeleteColumns,
        }
    }
}

fn validate_result_dimensions(
    rows: u32,
    columns: u32,
    limits: TableGridLimits,
) -> Result<usize, TableOperationError> {
    if rows == 0 || columns == 0 {
        return Err(TableGridError::EmptyGrid.into());
    }
    let config = limits.config();
    if rows > config.rows || columns > config.columns {
        return Err(TableGridError::DimensionLimitExceeded.into());
    }
    let slots = checked_product(rows, columns)?;
    if slots > config.slots {
        return Err(TableGridError::SlotLimitExceeded.into());
    }
    Ok(slots)
}

fn checked_product(left: u32, right: u32) -> Result<usize, TableOperationError> {
    let left = usize::try_from(left).map_err(|_| TableOperationError::DimensionOverflow)?;
    let right = usize::try_from(right).map_err(|_| TableOperationError::DimensionOverflow)?;
    left.checked_mul(right)
        .ok_or(TableOperationError::DimensionOverflow)
}

fn coordinate_from_row_major(
    index: usize,
    columns: u32,
) -> Result<CellCoordinate, TableOperationError> {
    let columns = usize::try_from(columns).map_err(|_| TableOperationError::DimensionOverflow)?;
    if columns == 0 {
        return Err(TableGridError::EmptyGrid.into());
    }
    Ok(CellCoordinate {
        row: u32::try_from(index / columns).map_err(|_| TableOperationError::DimensionOverflow)?,
        column: u32::try_from(index % columns)
            .map_err(|_| TableOperationError::DimensionOverflow)?,
    })
}

fn single_slot(master_cell_id: LogicalId, row: u32, column: u32) -> TableCellSpan {
    TableCellSpan {
        master_cell_id,
        row,
        column,
        row_span: 1,
        column_span: 1,
    }
}

fn dimensions(grid: &TableGrid) -> TableDimensions {
    TableDimensions {
        rows: grid.rows(),
        columns: grid.columns(),
    }
}

fn cell_coordinate(cell: &TableCellSpan) -> CellCoordinate {
    CellCoordinate {
        row: cell.row,
        column: cell.column,
    }
}

fn fallible_vec<T>(capacity: usize) -> Result<Vec<T>, TableOperationError> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| TableOperationError::Grid(TableGridError::AllocationFailed))?;
    Ok(values)
}

fn clone_identifiers(cells: &[TableCellSpan]) -> Result<Vec<LogicalId>, TableOperationError> {
    let mut identifiers = fallible_vec(cells.len())?;
    identifiers.extend(cells.iter().map(|cell| cell.master_cell_id.clone()));
    Ok(identifiers)
}

fn identifiers_in_band(
    grid: &TableGrid,
    axis: Axis,
    start: u32,
    end: u32,
) -> Result<Vec<LogicalId>, TableOperationError> {
    let expected = grid
        .master_cells()
        .iter()
        .filter(|cell| {
            let coordinate = axis.cell_start(cell);
            coordinate >= start && coordinate < end
        })
        .count();
    let mut identifiers = fallible_vec(expected)?;
    identifiers.extend(
        grid.master_cells()
            .iter()
            .filter(|cell| {
                let coordinate = axis.cell_start(cell);
                coordinate >= start && coordinate < end
            })
            .map(|cell| cell.master_cell_id.clone()),
    );
    Ok(identifiers)
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableOperationError {
    #[error("table operation count must be nonzero")]
    ZeroCount,
    #[error("table insertion index is outside the grid boundary")]
    InsertionIndexOutOfBounds,
    #[error("table deletion range is outside the grid boundary")]
    DeletionRangeOutOfBounds,
    #[error("table operation would remove the final row or column")]
    WouldEmptyGrid,
    #[error("table operation new master-cell identifier count is inexact")]
    NewMasterCellCountMismatch,
    #[error("table operation crosses an existing merged-cell span")]
    SpanBoundaryConflict,
    #[error("table operation dimension arithmetic overflowed")]
    DimensionOverflow,
    #[error(transparent)]
    Grid(#[from] TableGridError),
}

impl TableOperationError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::ZeroCount => "table_operation_zero_count",
            Self::InsertionIndexOutOfBounds => "table_operation_insertion_index_out_of_bounds",
            Self::DeletionRangeOutOfBounds => "table_operation_deletion_range_out_of_bounds",
            Self::WouldEmptyGrid => "table_operation_would_empty_grid",
            Self::NewMasterCellCountMismatch => "table_operation_new_master_cell_count_mismatch",
            Self::SpanBoundaryConflict => "table_operation_span_boundary_conflict",
            Self::DimensionOverflow => "table_operation_dimension_overflow",
            Self::Grid(error) => error.code(),
        }
    }
}
