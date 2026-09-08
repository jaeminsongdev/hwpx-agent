use std::fmt;
use std::io;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{CellCoordinate, LengthMicrometers, TableGrid};

pub const TABLE_GEOMETRY_SCHEMA_VERSION: &str = "hwpx-agent.table-geometry/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableGeometryLimitConfig {
    pub rows: usize,
    pub columns: usize,
    pub dimension_micrometers: u64,
    pub serialized_bytes: usize,
}

impl Default for TableGeometryLimitConfig {
    fn default() -> Self {
        Self {
            rows: 10_000,
            columns: 1_024,
            dimension_micrometers: 1_000_000_000,
            serialized_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableGeometryLimits(TableGeometryLimitConfig);

impl TableGeometryLimits {
    pub const HARD_MAX_ROWS: usize = 10_000;
    pub const HARD_MAX_COLUMNS: usize = 1_024;
    pub const HARD_MAX_DIMENSION_MICROMETERS: u64 = 1_000_000_000;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for table track geometry.
    ///
    /// # Errors
    ///
    /// Returns [`TableGeometryError::InvalidLimit`] for zero or over-ceiling values.
    pub fn new(config: TableGeometryLimitConfig) -> Result<Self, TableGeometryError> {
        if config.rows == 0
            || config.rows > Self::HARD_MAX_ROWS
            || config.columns == 0
            || config.columns > Self::HARD_MAX_COLUMNS
            || config.dimension_micrometers == 0
            || config.dimension_micrometers > Self::HARD_MAX_DIMENSION_MICROMETERS
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(TableGeometryError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableGeometryLimitConfig {
        self.0
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableGeometryStateDraft {
    pub schema_version: String,
    pub grid_sha256: String,
    pub row_heights: Vec<LengthMicrometers>,
    pub row_minimum_heights: Vec<LengthMicrometers>,
    pub column_widths: Vec<LengthMicrometers>,
    pub column_minimum_widths: Vec<LengthMicrometers>,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableGeometryState {
    schema_version: &'static str,
    grid_sha256: String,
    row_heights: Vec<LengthMicrometers>,
    row_minimum_heights: Vec<LengthMicrometers>,
    column_widths: Vec<LengthMicrometers>,
    column_minimum_widths: Vec<LengthMicrometers>,
}

impl TableGeometryState {
    /// Binds validated row and column track geometry to one exact table grid.
    ///
    /// # Errors
    ///
    /// Rejects count, dimension, minimum, grid, allocation, and serialization violations.
    pub fn new(
        grid: &TableGrid,
        row_heights: Vec<LengthMicrometers>,
        row_minimum_heights: Vec<LengthMicrometers>,
        column_widths: Vec<LengthMicrometers>,
        column_minimum_widths: Vec<LengthMicrometers>,
        limits: TableGeometryLimits,
    ) -> Result<Self, TableGeometryError> {
        let grid_sha256 = hex_digest(
            grid.canonical_sha256()
                .map_err(|_| TableGeometryError::GridRejected)?,
        );
        Self::from_draft(
            grid,
            TableGeometryStateDraft {
                schema_version: TABLE_GEOMETRY_SCHEMA_VERSION.to_owned(),
                grid_sha256,
                row_heights,
                row_minimum_heights,
                column_widths,
                column_minimum_widths,
            },
            limits,
        )
    }

    /// Validates an untrusted geometry draft against one exact table grid.
    ///
    /// # Errors
    ///
    /// Rejects unsupported versions, inexact grid identity, invalid tracks, or finite-limit
    /// violations.
    pub fn from_draft(
        grid: &TableGrid,
        draft: TableGeometryStateDraft,
        limits: TableGeometryLimits,
    ) -> Result<Self, TableGeometryError> {
        if draft.schema_version != TABLE_GEOMETRY_SCHEMA_VERSION {
            return Err(TableGeometryError::UnsupportedVersion);
        }
        let expected_grid_sha256 = hex_digest(
            grid.canonical_sha256()
                .map_err(|_| TableGeometryError::GridRejected)?,
        );
        if draft.grid_sha256 != expected_grid_sha256 {
            return Err(TableGeometryError::GridMismatch);
        }
        validate_track_counts(grid, &draft, limits)?;
        validate_tracks(
            &draft.row_heights,
            &draft.row_minimum_heights,
            limits.0.dimension_micrometers,
        )?;
        validate_tracks(
            &draft.column_widths,
            &draft.column_minimum_widths,
            limits.0.dimension_micrometers,
        )?;
        let state = Self {
            schema_version: TABLE_GEOMETRY_SCHEMA_VERSION,
            grid_sha256: expected_grid_sha256,
            row_heights: draft.row_heights,
            row_minimum_heights: draft.row_minimum_heights,
            column_widths: draft.column_widths,
            column_minimum_widths: draft.column_minimum_widths,
        };
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    /// Deserializes and validates an untrusted geometry document.
    ///
    /// # Errors
    ///
    /// Returns stable errors for oversized or malformed JSON and every invariant violation.
    pub fn from_json(
        grid: &TableGrid,
        bytes: &[u8],
        limits: TableGeometryLimits,
    ) -> Result<Self, TableGeometryError> {
        if bytes.len() > limits.0.serialized_bytes {
            return Err(TableGeometryError::InputLimitExceeded);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| TableGeometryError::InvalidJson)?;
        Self::from_draft(grid, draft, limits)
    }

    #[must_use]
    pub fn row_heights(&self) -> &[LengthMicrometers] {
        &self.row_heights
    }

    #[must_use]
    pub fn row_minimum_heights(&self) -> &[LengthMicrometers] {
        &self.row_minimum_heights
    }

    #[must_use]
    pub fn column_widths(&self) -> &[LengthMicrometers] {
        &self.column_widths
    }

    #[must_use]
    pub fn column_minimum_widths(&self) -> &[LengthMicrometers] {
        &self.column_minimum_widths
    }

    /// Returns the physical extent of the master cell covering `coordinate`.
    ///
    /// # Errors
    ///
    /// Rejects a mismatched grid, an out-of-bounds coordinate, or arithmetic overflow.
    pub fn cell_extent(
        &self,
        grid: &TableGrid,
        coordinate: CellCoordinate,
    ) -> Result<(LengthMicrometers, LengthMicrometers), TableGeometryError> {
        self.ensure_grid(grid)?;
        let cell = grid
            .master_cell_at(coordinate)
            .map_err(|_| TableGeometryError::CoordinateOutOfBounds)?;
        let row_end = cell
            .row
            .checked_add(cell.row_span)
            .ok_or(TableGeometryError::ArithmeticOverflow)?;
        let column_end = cell
            .column
            .checked_add(cell.column_span)
            .ok_or(TableGeometryError::ArithmeticOverflow)?;
        let height = sum_range(&self.row_heights, cell.row, row_end)?;
        let width = sum_range(&self.column_widths, cell.column, column_end)?;
        Ok((to_length(width)?, to_length(height)?))
    }

    /// Applies one bounded track operation atomically.
    ///
    /// The source state is never mutated. Equalization preserves the selected total whenever the
    /// integer average permits it, rounds upward otherwise, and grows only when a selected content
    /// minimum requires it.
    ///
    /// # Errors
    ///
    /// Rejects grid mismatch, invalid ranges or dimensions, arithmetic/serialization overflow, and
    /// allocation failure.
    pub fn apply(
        &self,
        grid: &TableGrid,
        operation: TableGeometryOperation,
        limits: TableGeometryLimits,
    ) -> Result<TableGeometryResult, TableGeometryError> {
        self.ensure_grid(grid)?;
        validate_state_limits(self, limits)?;
        let source_sha256 = self.canonical_sha256(limits)?;
        let mut output = self.clone();
        let (changed_rows, changed_columns) = match operation {
            TableGeometryOperation::EqualRowHeights { range } => {
                let (start, end) = checked_range(range, output.row_heights.len())?;
                let target = equalized_target(
                    &output.row_heights[start..end],
                    &output.row_minimum_heights[start..end],
                )?;
                let changed = replace_tracks(&mut output.row_heights, start, end, target)?;
                (changed, Vec::new())
            }
            TableGeometryOperation::EqualColumnWidths { range } => {
                let (start, end) = checked_range(range, output.column_widths.len())?;
                let target = equalized_target(
                    &output.column_widths[start..end],
                    &output.column_minimum_widths[start..end],
                )?;
                let changed = replace_tracks(&mut output.column_widths, start, end, target)?;
                (Vec::new(), changed)
            }
            TableGeometryOperation::SetRowMinimumHeight {
                range,
                minimum_height,
            } => {
                validate_dimension(minimum_height, limits.0.dimension_micrometers)?;
                let (start, end) = checked_range(range, output.row_heights.len())?;
                let mut changed = fallible_vec(end - start)?;
                for index in start..end {
                    let old_height = output.row_heights[index];
                    let old_minimum = output.row_minimum_heights[index];
                    output.row_minimum_heights[index] = minimum_height;
                    if old_height < minimum_height {
                        output.row_heights[index] = minimum_height;
                    }
                    if old_height != output.row_heights[index] || old_minimum != minimum_height {
                        changed.push(
                            u32::try_from(index)
                                .map_err(|_| TableGeometryError::ArithmeticOverflow)?,
                        );
                    }
                }
                (changed, Vec::new())
            }
        };
        validate_tracks(
            &output.row_heights,
            &output.row_minimum_heights,
            limits.0.dimension_micrometers,
        )?;
        validate_tracks(
            &output.column_widths,
            &output.column_minimum_widths,
            limits.0.dimension_micrometers,
        )?;
        let output_sha256 = output.canonical_sha256(limits)?;
        let receipt = TableGeometryReceipt {
            schema_version: TABLE_GEOMETRY_SCHEMA_VERSION,
            operation,
            grid_sha256: self.grid_sha256.clone(),
            source_state_sha256: hex_digest(source_sha256),
            output_state_sha256: hex_digest(output_sha256),
            changed_rows,
            changed_columns,
        };
        let _ = receipt.canonical_json(limits)?;
        Ok(TableGeometryResult {
            state: output,
            receipt,
        })
    }

    /// Emits stable compact JSON under the configured finite output limit.
    ///
    /// # Errors
    ///
    /// Returns a stable limit, allocation, or serialization error.
    pub fn canonical_json(
        &self,
        limits: TableGeometryLimits,
    ) -> Result<Vec<u8>, TableGeometryError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Hashes the canonical geometry state.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableGeometryLimits,
    ) -> Result<[u8; 32], TableGeometryError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    fn ensure_grid(&self, grid: &TableGrid) -> Result<(), TableGeometryError> {
        let digest = hex_digest(
            grid.canonical_sha256()
                .map_err(|_| TableGeometryError::GridRejected)?,
        );
        if self.grid_sha256 != digest {
            return Err(TableGeometryError::GridMismatch);
        }
        Ok(())
    }
}

impl fmt::Debug for TableGeometryState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableGeometryState")
            .field("rows", &self.row_heights.len())
            .field("columns", &self.column_widths.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableTrackRange {
    pub first: u32,
    pub count: u32,
}

impl TableTrackRange {
    #[must_use]
    pub const fn new(first: u32, count: u32) -> Self {
        Self { first, count }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case", tag = "kind", deny_unknown_fields)]
pub enum TableGeometryOperation {
    EqualRowHeights {
        range: TableTrackRange,
    },
    EqualColumnWidths {
        range: TableTrackRange,
    },
    SetRowMinimumHeight {
        range: TableTrackRange,
        minimum_height: LengthMicrometers,
    },
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableGeometryReceipt {
    schema_version: &'static str,
    operation: TableGeometryOperation,
    grid_sha256: String,
    source_state_sha256: String,
    output_state_sha256: String,
    changed_rows: Vec<u32>,
    changed_columns: Vec<u32>,
}

impl TableGeometryReceipt {
    #[must_use]
    pub const fn operation(&self) -> TableGeometryOperation {
        self.operation
    }

    #[must_use]
    pub fn changed_rows(&self) -> &[u32] {
        &self.changed_rows
    }

    #[must_use]
    pub fn changed_columns(&self) -> &[u32] {
        &self.changed_columns
    }

    #[must_use]
    pub fn source_state_sha256(&self) -> &str {
        &self.source_state_sha256
    }

    #[must_use]
    pub fn output_state_sha256(&self) -> &str {
        &self.output_state_sha256
    }

    /// Emits stable compact JSON under the configured finite output limit.
    ///
    /// # Errors
    ///
    /// Returns a stable limit, allocation, or serialization error.
    pub fn canonical_json(
        &self,
        limits: TableGeometryLimits,
    ) -> Result<Vec<u8>, TableGeometryError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for TableGeometryReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableGeometryReceipt")
            .field("operation", &self.operation)
            .field("changed_row_count", &self.changed_rows.len())
            .field("changed_column_count", &self.changed_columns.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableGeometryResult {
    state: TableGeometryState,
    receipt: TableGeometryReceipt,
}

impl TableGeometryResult {
    #[must_use]
    pub const fn state(&self) -> &TableGeometryState {
        &self.state
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableGeometryReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn into_parts(self) -> (TableGeometryState, TableGeometryReceipt) {
        (self.state, self.receipt)
    }
}

impl fmt::Debug for TableGeometryResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableGeometryResult")
            .field("state", &self.state)
            .field("receipt", &self.receipt)
            .finish()
    }
}

fn validate_track_counts(
    grid: &TableGrid,
    draft: &TableGeometryStateDraft,
    limits: TableGeometryLimits,
) -> Result<(), TableGeometryError> {
    let rows = usize::try_from(grid.rows()).map_err(|_| TableGeometryError::TrackCountOverflow)?;
    let columns =
        usize::try_from(grid.columns()).map_err(|_| TableGeometryError::TrackCountOverflow)?;
    if rows > limits.0.rows || columns > limits.0.columns {
        return Err(TableGeometryError::TrackLimitExceeded);
    }
    if draft.row_heights.len() != rows || draft.row_minimum_heights.len() != rows {
        return Err(TableGeometryError::RowCountMismatch);
    }
    if draft.column_widths.len() != columns || draft.column_minimum_widths.len() != columns {
        return Err(TableGeometryError::ColumnCountMismatch);
    }
    Ok(())
}

fn validate_tracks(
    values: &[LengthMicrometers],
    minimums: &[LengthMicrometers],
    maximum: u64,
) -> Result<(), TableGeometryError> {
    for (value, minimum) in values.iter().zip(minimums) {
        validate_dimension(*value, maximum)?;
        validate_dimension(*minimum, maximum)?;
        if value < minimum {
            return Err(TableGeometryError::MinimumViolation);
        }
    }
    Ok(())
}

fn validate_state_limits(
    state: &TableGeometryState,
    limits: TableGeometryLimits,
) -> Result<(), TableGeometryError> {
    if state.row_heights.len() > limits.0.rows || state.column_widths.len() > limits.0.columns {
        return Err(TableGeometryError::TrackLimitExceeded);
    }
    validate_tracks(
        &state.row_heights,
        &state.row_minimum_heights,
        limits.0.dimension_micrometers,
    )?;
    validate_tracks(
        &state.column_widths,
        &state.column_minimum_widths,
        limits.0.dimension_micrometers,
    )
}

fn validate_dimension(value: LengthMicrometers, maximum: u64) -> Result<u64, TableGeometryError> {
    let raw = value.as_i64();
    let positive = u64::try_from(raw).map_err(|_| TableGeometryError::InvalidDimension)?;
    if positive == 0 {
        return Err(TableGeometryError::InvalidDimension);
    }
    if positive > maximum {
        return Err(TableGeometryError::DimensionLimitExceeded);
    }
    Ok(positive)
}

fn checked_range(
    range: TableTrackRange,
    track_count: usize,
) -> Result<(usize, usize), TableGeometryError> {
    if range.count == 0 {
        return Err(TableGeometryError::EmptyRange);
    }
    let start = usize::try_from(range.first).map_err(|_| TableGeometryError::RangeOverflow)?;
    let count = usize::try_from(range.count).map_err(|_| TableGeometryError::RangeOverflow)?;
    let end = start
        .checked_add(count)
        .ok_or(TableGeometryError::RangeOverflow)?;
    if start >= track_count || end > track_count {
        return Err(TableGeometryError::RangeOutOfBounds);
    }
    Ok((start, end))
}

fn equalized_target(
    values: &[LengthMicrometers],
    minimums: &[LengthMicrometers],
) -> Result<LengthMicrometers, TableGeometryError> {
    let mut total = 0_u64;
    let mut maximum_minimum = 0_u64;
    for (value, minimum) in values.iter().zip(minimums) {
        total = total
            .checked_add(
                u64::try_from(value.as_i64())
                    .map_err(|_| TableGeometryError::ArithmeticOverflow)?,
            )
            .ok_or(TableGeometryError::ArithmeticOverflow)?;
        maximum_minimum = maximum_minimum.max(
            u64::try_from(minimum.as_i64()).map_err(|_| TableGeometryError::ArithmeticOverflow)?,
        );
    }
    let count = u64::try_from(values.len()).map_err(|_| TableGeometryError::ArithmeticOverflow)?;
    let average = total
        .checked_add(count - 1)
        .ok_or(TableGeometryError::ArithmeticOverflow)?
        / count;
    to_length(average.max(maximum_minimum))
}

fn replace_tracks(
    values: &mut [LengthMicrometers],
    start: usize,
    end: usize,
    target: LengthMicrometers,
) -> Result<Vec<u32>, TableGeometryError> {
    let mut changed = fallible_vec(end - start)?;
    for (index, value) in values.iter_mut().enumerate().take(end).skip(start) {
        if *value != target {
            *value = target;
            changed.push(u32::try_from(index).map_err(|_| TableGeometryError::ArithmeticOverflow)?);
        }
    }
    Ok(changed)
}

fn sum_range(
    values: &[LengthMicrometers],
    start: u32,
    end: u32,
) -> Result<u64, TableGeometryError> {
    let start = usize::try_from(start).map_err(|_| TableGeometryError::ArithmeticOverflow)?;
    let end = usize::try_from(end).map_err(|_| TableGeometryError::ArithmeticOverflow)?;
    let slice = values
        .get(start..end)
        .ok_or(TableGeometryError::CoordinateOutOfBounds)?;
    slice.iter().try_fold(0_u64, |total, value| {
        total
            .checked_add(
                u64::try_from(value.as_i64())
                    .map_err(|_| TableGeometryError::ArithmeticOverflow)?,
            )
            .ok_or(TableGeometryError::ArithmeticOverflow)
    })
}

fn to_length(value: u64) -> Result<LengthMicrometers, TableGeometryError> {
    Ok(LengthMicrometers::from_raw(
        i64::try_from(value).map_err(|_| TableGeometryError::ArithmeticOverflow)?,
    ))
}

fn hex_digest(bytes: [u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(output, "{byte:02x}");
    }
    output
}

fn fallible_vec<T>(capacity: usize) -> Result<Vec<T>, TableGeometryError> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| TableGeometryError::AllocationFailed)?;
    Ok(values)
}

fn serialize_bounded<T: Serialize + ?Sized>(
    value: &T,
    max_bytes: usize,
) -> Result<Vec<u8>, TableGeometryError> {
    if max_bytes == 0 || max_bytes > TableGeometryLimits::HARD_MAX_SERIALIZED_BYTES {
        return Err(TableGeometryError::InvalidLimit);
    }
    let mut writer = BoundedWriter::new(max_bytes);
    if serde_json::to_writer(&mut writer, value).is_err() {
        return Err(match writer.failure {
            WriterFailure::Limit => TableGeometryError::OutputLimitExceeded,
            WriterFailure::Allocation => TableGeometryError::AllocationFailed,
            WriterFailure::None => TableGeometryError::SerializationFailed,
        });
    }
    Ok(writer.bytes)
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
            return Err(io::Error::other("table geometry output limit"));
        };
        if next_length > self.max_bytes {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table geometry output limit"));
        }
        if self.bytes.try_reserve(buffer.len()).is_err() {
            self.failure = WriterFailure::Allocation;
            return Err(io::Error::other("table geometry allocation"));
        }
        self.bytes.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableGeometryError {
    #[error("table geometry limits are invalid")]
    InvalidLimit,
    #[error("table geometry schema version is unsupported")]
    UnsupportedVersion,
    #[error("table geometry JSON is invalid")]
    InvalidJson,
    #[error("table geometry grid cannot be validated")]
    GridRejected,
    #[error("table geometry is bound to a different grid")]
    GridMismatch,
    #[error("table geometry track count overflowed")]
    TrackCountOverflow,
    #[error("table geometry tracks exceed the configured limit")]
    TrackLimitExceeded,
    #[error("table geometry row count does not match the grid")]
    RowCountMismatch,
    #[error("table geometry column count does not match the grid")]
    ColumnCountMismatch,
    #[error("table geometry dimension must be positive")]
    InvalidDimension,
    #[error("table geometry dimension exceeds the configured limit")]
    DimensionLimitExceeded,
    #[error("table geometry is smaller than its content minimum")]
    MinimumViolation,
    #[error("table geometry range must be nonempty")]
    EmptyRange,
    #[error("table geometry range overflowed")]
    RangeOverflow,
    #[error("table geometry range is out of bounds")]
    RangeOutOfBounds,
    #[error("table geometry coordinate is out of bounds")]
    CoordinateOutOfBounds,
    #[error("table geometry arithmetic overflowed")]
    ArithmeticOverflow,
    #[error("table geometry serialized input exceeds the configured limit")]
    InputLimitExceeded,
    #[error("table geometry canonical output exceeds the configured limit")]
    OutputLimitExceeded,
    #[error("table geometry canonical serialization failed")]
    SerializationFailed,
    #[error("table geometry allocation failed")]
    AllocationFailed,
}

impl TableGeometryError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_geometry_invalid_limit",
            Self::UnsupportedVersion => "table_geometry_unsupported_version",
            Self::InvalidJson => "table_geometry_invalid_json",
            Self::GridRejected => "table_geometry_grid_rejected",
            Self::GridMismatch => "table_geometry_grid_mismatch",
            Self::TrackCountOverflow => "table_geometry_track_count_overflow",
            Self::TrackLimitExceeded => "table_geometry_track_limit_exceeded",
            Self::RowCountMismatch => "table_geometry_row_count_mismatch",
            Self::ColumnCountMismatch => "table_geometry_column_count_mismatch",
            Self::InvalidDimension => "table_geometry_invalid_dimension",
            Self::DimensionLimitExceeded => "table_geometry_dimension_limit_exceeded",
            Self::MinimumViolation => "table_geometry_minimum_violation",
            Self::EmptyRange => "table_geometry_empty_range",
            Self::RangeOverflow => "table_geometry_range_overflow",
            Self::RangeOutOfBounds => "table_geometry_range_out_of_bounds",
            Self::CoordinateOutOfBounds => "table_geometry_coordinate_out_of_bounds",
            Self::ArithmeticOverflow => "table_geometry_arithmetic_overflow",
            Self::InputLimitExceeded => "table_geometry_input_limit_exceeded",
            Self::OutputLimitExceeded => "table_geometry_output_limit_exceeded",
            Self::SerializationFailed => "table_geometry_serialization_failed",
            Self::AllocationFailed => "table_geometry_allocation_failed",
        }
    }
}
