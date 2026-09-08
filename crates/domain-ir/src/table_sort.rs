use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{CellCoordinate, LogicalId, TableGrid};

pub const TABLE_SORT_SCHEMA_VERSION: &str = "hwpx-agent.table-sort/v1";
pub const TABLE_SORT_CAPABILITY_ID: &str = "table.sort_cells";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableSortLimitConfig {
    pub input_bytes: usize,
    pub selected_cells: usize,
    pub sort_keys: usize,
    pub text_bytes: usize,
    pub comparison_work: u64,
    pub serialized_bytes: usize,
}

impl Default for TableSortLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 4 * 1024 * 1024,
            selected_cells: 1_000_000,
            sort_keys: 64,
            text_bytes: 16 * 1024,
            comparison_work: 100_000_000,
            serialized_bytes: 64 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableSortLimits(TableSortLimitConfig);

impl TableSortLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_SELECTED_CELLS: usize = 1_000_000;
    pub const HARD_MAX_SORT_KEYS: usize = 1_024;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_COMPARISON_WORK: u64 = 10_000_000_000;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for the table-sort boundary.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling or internally inconsistent limits.
    pub fn new(config: TableSortLimitConfig) -> Result<Self, TableSortError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.selected_cells == 0
            || config.selected_cells > Self::HARD_MAX_SELECTED_CELLS
            || config.sort_keys == 0
            || config.sort_keys > Self::HARD_MAX_SORT_KEYS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.comparison_work == 0
            || config.comparison_work > Self::HARD_MAX_COMPARISON_WORK
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TableSortError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableSortLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableSortAxis {
    Rows,
    Columns,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableSortDirection {
    Ascending,
    Descending,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableBlankOrder {
    First,
    Last,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableTextCollation {
    Binary,
    AsciiCaseInsensitive,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableFormulaMovePolicy {
    Reject,
    MoveVerbatim,
    RebaseRelative,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableSortRegion {
    pub start: CellCoordinate,
    pub end: CellCoordinate,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableSortKey {
    pub offset: u32,
    pub direction: TableSortDirection,
    pub blank_order: TableBlankOrder,
    pub text_collation: TableTextCollation,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case", tag = "kind", deny_unknown_fields)]
pub enum TableSortValue {
    Blank,
    Boolean { value: bool },
    Integer { value: i64 },
    Decimal { coefficient: i64, scale: u8 },
    DateDays { days_since_unix_epoch: i32 },
    Text { value: String },
}

impl fmt::Debug for TableSortValue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Blank => "TableSortValue::Blank",
            Self::Boolean { .. } => "TableSortValue::Boolean(<redacted>)",
            Self::Integer { .. } => "TableSortValue::Integer(<redacted>)",
            Self::Decimal { .. } => "TableSortValue::Decimal(<redacted>)",
            Self::DateDays { .. } => "TableSortValue::DateDays(<redacted>)",
            Self::Text { .. } => "TableSortValue::Text(<redacted>)",
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableSortCellDraft {
    pub coordinate: CellCoordinate,
    pub payload_sha256: String,
    pub formula_sha256: Option<String>,
    pub sort_value: TableSortValue,
}

impl fmt::Debug for TableSortCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortCellDraft")
            .field("coordinate", &self.coordinate)
            .field("payload_sha256", &"<redacted>")
            .field(
                "formula_sha256",
                &self.formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("sort_value", &self.sort_value)
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableSortRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub region: TableSortRegion,
    pub axis: TableSortAxis,
    pub keys: Vec<TableSortKey>,
    pub formula_move_policy: TableFormulaMovePolicy,
    pub cells: Vec<TableSortCellDraft>,
}

impl fmt::Debug for TableSortRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("region", &self.region)
            .field("axis", &self.axis)
            .field("keys", &self.keys)
            .field("formula_move_policy", &self.formula_move_policy)
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableSortRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    region: TableSortRegion,
    axis: TableSortAxis,
    keys: Vec<TableSortKey>,
    formula_move_policy: TableFormulaMovePolicy,
    cells: Vec<TableSortCellDraft>,
}

impl TableSortRequest {
    /// Validates and canonicalizes one exact merge-free table region and its sort keys.
    ///
    /// # Errors
    ///
    /// Rejects schema, region, grid, key, cell-set, digest, formula-policy and finite-limit drift.
    pub fn from_draft(
        draft: TableSortRequestDraft,
        grid: &TableGrid,
        limits: TableSortLimits,
    ) -> Result<Self, TableSortError> {
        let TableSortRequestDraft {
            schema_version,
            table_id,
            region,
            axis,
            keys,
            formula_move_policy,
            mut cells,
        } = draft;
        if schema_version != TABLE_SORT_SCHEMA_VERSION {
            return Err(TableSortError::UnsupportedVersion);
        }
        let expected_cells = validate_region(region, grid, limits)?;
        validate_keys(&keys, axis, region, limits)?;
        validate_comparison_work(axis, region, keys.len(), limits)?;
        if cells.len() != expected_cells {
            return Err(TableSortError::CellSetMismatch);
        }
        cells.sort_by_key(|cell| cell.coordinate);
        if cells
            .windows(2)
            .any(|pair| pair[0].coordinate == pair[1].coordinate)
        {
            return Err(TableSortError::CellSetMismatch);
        }
        let mut cursor = 0_usize;
        for row in region.start.row..=region.end.row {
            for column in region.start.column..=region.end.column {
                let cell = cells
                    .get_mut(cursor)
                    .ok_or(TableSortError::CellSetMismatch)?;
                if cell.coordinate != (CellCoordinate { row, column }) {
                    return Err(TableSortError::CellSetMismatch);
                }
                normalize_sort_value(&mut cell.sort_value);
                validate_cell(cell, limits)?;
                if cell.formula_sha256.is_some()
                    && formula_move_policy == TableFormulaMovePolicy::Reject
                {
                    return Err(TableSortError::FormulaPresent);
                }
                cursor = cursor
                    .checked_add(1)
                    .ok_or(TableSortError::SelectionLimit)?;
            }
        }
        let grid_sha256 = hex(grid
            .canonical_sha256()
            .map_err(|_| TableSortError::GridMismatch)?);
        let request = Self {
            schema_version: TABLE_SORT_SCHEMA_VERSION,
            capability_id: TABLE_SORT_CAPABILITY_ID,
            table_id,
            grid_sha256,
            region,
            axis,
            keys,
            formula_move_policy,
            cells,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and validates it against the exact supplied grid.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and every
    /// semantic failure reported by [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        grid: &TableGrid,
        limits: TableSortLimits,
    ) -> Result<Self, TableSortError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(TableSortError::InputLimit);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| TableSortError::InvalidJson)?;
        Self::from_draft(draft, grid, limits)
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
    pub const fn region(&self) -> TableSortRegion {
        self.region
    }

    #[must_use]
    pub const fn axis(&self) -> TableSortAxis {
        self.axis
    }

    #[must_use]
    pub fn keys(&self) -> &[TableSortKey] {
        &self.keys
    }

    #[must_use]
    pub const fn formula_move_policy(&self) -> TableFormulaMovePolicy {
        self.formula_move_policy
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    /// Serializes the complete validated request under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(&self, limits: TableSortLimits) -> Result<Vec<u8>, TableSortError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over bounded canonical request JSON.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(&self, limits: TableSortLimits) -> Result<[u8; 32], TableSortError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableSortRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("region", &self.region)
            .field("axis", &self.axis)
            .field("keys", &self.keys)
            .field("formula_move_policy", &self.formula_move_policy)
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableSortRelocation {
    source: CellCoordinate,
    destination: CellCoordinate,
    payload_sha256: String,
    formula_sha256: Option<String>,
}

impl TableSortRelocation {
    #[must_use]
    pub const fn source(&self) -> CellCoordinate {
        self.source
    }

    #[must_use]
    pub const fn destination(&self) -> CellCoordinate {
        self.destination
    }

    #[must_use]
    pub fn payload_sha256(&self) -> &str {
        &self.payload_sha256
    }

    #[must_use]
    pub fn formula_sha256(&self) -> Option<&str> {
        self.formula_sha256.as_deref()
    }
}

impl fmt::Debug for TableSortRelocation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortRelocation")
            .field("source", &self.source)
            .field("destination", &self.destination)
            .field("payload_sha256", &"<redacted>")
            .field(
                "formula_sha256",
                &self.formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableSortReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    request_sha256: String,
    relocation_sha256: String,
    formula_move_policy: TableFormulaMovePolicy,
    changed: bool,
}

impl TableSortReceipt {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn formula_move_policy(&self) -> TableFormulaMovePolicy {
        self.formula_move_policy
    }

    #[must_use]
    pub const fn changed(&self) -> bool {
        self.changed
    }

    #[must_use]
    pub fn grid_sha256(&self) -> &str {
        &self.grid_sha256
    }

    #[must_use]
    pub fn request_sha256(&self) -> &str {
        &self.request_sha256
    }

    #[must_use]
    pub fn relocation_sha256(&self) -> &str {
        &self.relocation_sha256
    }

    /// Serializes the receipt under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(&self, limits: TableSortLimits) -> Result<Vec<u8>, TableSortError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for TableSortReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("request_sha256", &"<redacted>")
            .field("relocation_sha256", &"<redacted>")
            .field("formula_move_policy", &self.formula_move_policy)
            .field("changed", &self.changed)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableSortPlan {
    schema_version: &'static str,
    request: TableSortRequest,
    relocations: Vec<TableSortRelocation>,
    receipt: TableSortReceipt,
}

impl TableSortPlan {
    #[must_use]
    pub const fn request(&self) -> &TableSortRequest {
        &self.request
    }

    #[must_use]
    pub fn relocations(&self) -> &[TableSortRelocation] {
        &self.relocations
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableSortReceipt {
        &self.receipt
    }

    /// Serializes the complete plan under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(&self, limits: TableSortLimits) -> Result<Vec<u8>, TableSortError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over bounded canonical plan JSON.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(&self, limits: TableSortLimits) -> Result<[u8; 32], TableSortError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableSortPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableSortPlan")
            .field("schema_version", &self.schema_version)
            .field("request", &self.request)
            .field("relocation_count", &self.relocations.len())
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableSortBuilder;

impl TableSortBuilder {
    /// Produces a deterministic stable line permutation and whole-cell relocation plan.
    ///
    /// # Errors
    ///
    /// Rejects output beyond the configured bound. The request is already fully validated, and no
    /// partial plan is returned.
    pub fn build(
        request: TableSortRequest,
        limits: TableSortLimits,
    ) -> Result<TableSortPlan, TableSortError> {
        let line_count = match request.axis {
            TableSortAxis::Rows => request.region.end.row - request.region.start.row + 1,
            TableSortAxis::Columns => request.region.end.column - request.region.start.column + 1,
        };
        let cross_count = match request.axis {
            TableSortAxis::Rows => request.region.end.column - request.region.start.column + 1,
            TableSortAxis::Columns => request.region.end.row - request.region.start.row + 1,
        };
        let cells_by_coordinate: BTreeMap<_, _> = request
            .cells
            .iter()
            .map(|cell| (cell.coordinate, cell))
            .collect();
        let mut source_lines: Vec<u32> = (0..line_count).collect();
        source_lines
            .sort_by(|left, right| compare_lines(&request, &cells_by_coordinate, *left, *right));

        let mut relocations = Vec::with_capacity(request.cells.len());
        let mut changed = false;
        for (destination_line, source_line) in source_lines.into_iter().enumerate() {
            let destination_line =
                u32::try_from(destination_line).map_err(|_| TableSortError::SelectionLimit)?;
            for cross in 0..cross_count {
                let source = line_coordinate(&request, source_line, cross);
                let destination = line_coordinate(&request, destination_line, cross);
                let cell = cells_by_coordinate
                    .get(&source)
                    .ok_or(TableSortError::CellSetMismatch)?;
                changed |= source != destination;
                relocations.push(TableSortRelocation {
                    source,
                    destination,
                    payload_sha256: cell.payload_sha256.clone(),
                    formula_sha256: cell.formula_sha256.clone(),
                });
            }
        }
        relocations.sort_by_key(|item| item.destination);
        let request_sha256 = hex(request.canonical_sha256(limits)?);
        let relocation_sha256 =
            hex(Sha256::digest(serialize_bounded(&relocations, limits.0.serialized_bytes)?).into());
        let receipt = TableSortReceipt {
            schema_version: TABLE_SORT_SCHEMA_VERSION,
            capability_id: TABLE_SORT_CAPABILITY_ID,
            table_id: request.table_id.clone(),
            grid_sha256: request.grid_sha256.clone(),
            request_sha256,
            relocation_sha256,
            formula_move_policy: request.formula_move_policy,
            changed,
        };
        let _ = receipt.canonical_json(limits)?;
        let plan = TableSortPlan {
            schema_version: TABLE_SORT_SCHEMA_VERSION,
            request,
            relocations,
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableSortError {
    #[error("table sort limits are invalid")]
    InvalidLimit,
    #[error("table sort schema version is unsupported")]
    UnsupportedVersion,
    #[error("table sort JSON input is empty or oversized")]
    InputLimit,
    #[error("table sort JSON is invalid")]
    InvalidJson,
    #[error("table sort region is reversed")]
    RegionOrder,
    #[error("table sort region is outside the supplied grid")]
    RegionOutOfBounds,
    #[error("table sort selection exceeds its configured bound")]
    SelectionLimit,
    #[error("table sort region contains a merged cell")]
    MergedCell,
    #[error("table sort grid cannot be bound canonically")]
    GridMismatch,
    #[error("table sort key set is empty or oversized")]
    KeyLimit,
    #[error("table sort key offsets are duplicated")]
    DuplicateKey,
    #[error("table sort key is outside the selected region")]
    KeyOutOfBounds,
    #[error("table sort comparison work exceeds its configured bound")]
    WorkLimit,
    #[error("table sort cell set does not exactly cover the selected region")]
    CellSetMismatch,
    #[error("table sort payload or formula digest is invalid")]
    DigestInvalid,
    #[error("table sort value is invalid or exceeds its configured bound")]
    SortValueInvalid,
    #[error("table sort formula policy rejects a selected formula cell")]
    FormulaPresent,
    #[error("table sort output exceeds its configured bound")]
    OutputLimit,
    #[error("table sort serialization failed")]
    Serialization,
}

impl TableSortError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_sort_invalid_limit",
            Self::UnsupportedVersion => "table_sort_unsupported_version",
            Self::InputLimit => "table_sort_input_limit",
            Self::InvalidJson => "table_sort_invalid_json",
            Self::RegionOrder => "table_sort_region_order",
            Self::RegionOutOfBounds => "table_sort_region_out_of_bounds",
            Self::SelectionLimit => "table_sort_selection_limit",
            Self::MergedCell => "table_sort_merged_cell",
            Self::GridMismatch => "table_sort_grid_mismatch",
            Self::KeyLimit => "table_sort_key_limit",
            Self::DuplicateKey => "table_sort_duplicate_key",
            Self::KeyOutOfBounds => "table_sort_key_out_of_bounds",
            Self::WorkLimit => "table_sort_work_limit",
            Self::CellSetMismatch => "table_sort_cell_set_mismatch",
            Self::DigestInvalid => "table_sort_digest_invalid",
            Self::SortValueInvalid => "table_sort_value_invalid",
            Self::FormulaPresent => "table_sort_formula_present",
            Self::OutputLimit => "table_sort_output_limit",
            Self::Serialization => "table_sort_serialization",
        }
    }
}

fn validate_region(
    region: TableSortRegion,
    grid: &TableGrid,
    limits: TableSortLimits,
) -> Result<usize, TableSortError> {
    if region.start.row > region.end.row || region.start.column > region.end.column {
        return Err(TableSortError::RegionOrder);
    }
    if region.end.row >= grid.rows() || region.end.column >= grid.columns() {
        return Err(TableSortError::RegionOutOfBounds);
    }
    let rows = usize::try_from(region.end.row - region.start.row + 1)
        .map_err(|_| TableSortError::SelectionLimit)?;
    let columns = usize::try_from(region.end.column - region.start.column + 1)
        .map_err(|_| TableSortError::SelectionLimit)?;
    let selected_cells = rows
        .checked_mul(columns)
        .ok_or(TableSortError::SelectionLimit)?;
    if selected_cells > limits.0.selected_cells {
        return Err(TableSortError::SelectionLimit);
    }
    for row in region.start.row..=region.end.row {
        for column in region.start.column..=region.end.column {
            let coordinate = CellCoordinate { row, column };
            let master = grid
                .master_cell_at(coordinate)
                .map_err(|_| TableSortError::GridMismatch)?;
            if master.row != row
                || master.column != column
                || master.row_span != 1
                || master.column_span != 1
            {
                return Err(TableSortError::MergedCell);
            }
        }
    }
    Ok(selected_cells)
}

fn validate_keys(
    keys: &[TableSortKey],
    axis: TableSortAxis,
    region: TableSortRegion,
    limits: TableSortLimits,
) -> Result<(), TableSortError> {
    if keys.is_empty() || keys.len() > limits.0.sort_keys {
        return Err(TableSortError::KeyLimit);
    }
    let bound = match axis {
        TableSortAxis::Rows => region.end.column - region.start.column + 1,
        TableSortAxis::Columns => region.end.row - region.start.row + 1,
    };
    if keys.iter().any(|key| key.offset >= bound) {
        return Err(TableSortError::KeyOutOfBounds);
    }
    let unique_offsets: BTreeSet<u32> = keys.iter().map(|key| key.offset).collect();
    if unique_offsets.len() != keys.len() {
        return Err(TableSortError::DuplicateKey);
    }
    Ok(())
}

fn validate_comparison_work(
    axis: TableSortAxis,
    region: TableSortRegion,
    key_count: usize,
    limits: TableSortLimits,
) -> Result<(), TableSortError> {
    let lines = u64::from(match axis {
        TableSortAxis::Rows => region.end.row - region.start.row + 1,
        TableSortAxis::Columns => region.end.column - region.start.column + 1,
    });
    let levels = if lines <= 1 {
        0
    } else {
        u64::from(u64::BITS - (lines - 1).leading_zeros())
    };
    let work = lines
        .checked_mul(levels)
        .and_then(|value| value.checked_mul(u64::try_from(key_count).ok()?))
        .ok_or(TableSortError::WorkLimit)?;
    if work > limits.0.comparison_work {
        return Err(TableSortError::WorkLimit);
    }
    Ok(())
}

fn validate_cell(cell: &TableSortCellDraft, limits: TableSortLimits) -> Result<(), TableSortError> {
    validate_digest(&cell.payload_sha256)?;
    if let Some(formula_sha256) = &cell.formula_sha256 {
        validate_digest(formula_sha256)?;
    }
    match &cell.sort_value {
        TableSortValue::Decimal { scale, .. } if *scale > 18 => {
            Err(TableSortError::SortValueInvalid)
        }
        TableSortValue::Text { value }
            if value.len() > limits.0.text_bytes
                || value.chars().any(|character| character == '\0') =>
        {
            Err(TableSortError::SortValueInvalid)
        }
        _ => Ok(()),
    }
}

fn normalize_sort_value(value: &mut TableSortValue) {
    let TableSortValue::Decimal { coefficient, scale } = value else {
        return;
    };
    while *scale > 0 && *coefficient % 10 == 0 {
        *coefficient /= 10;
        *scale -= 1;
    }
    if *scale == 0 {
        *value = TableSortValue::Integer {
            value: *coefficient,
        };
    }
}

fn validate_digest(value: &str) -> Result<(), TableSortError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableSortError::DigestInvalid);
    }
    Ok(())
}

fn compare_lines(
    request: &TableSortRequest,
    cells: &BTreeMap<CellCoordinate, &TableSortCellDraft>,
    left: u32,
    right: u32,
) -> Ordering {
    for key in &request.keys {
        let left_coordinate = key_coordinate(request, left, key.offset);
        let right_coordinate = key_coordinate(request, right, key.offset);
        let ordering = match (cells.get(&left_coordinate), cells.get(&right_coordinate)) {
            (Some(left), Some(right)) => {
                compare_key_values(&left.sort_value, &right.sort_value, *key)
            }
            (None, Some(_)) => Ordering::Less,
            (Some(_), None) => Ordering::Greater,
            (None, None) => Ordering::Equal,
        };
        if ordering != Ordering::Equal {
            return ordering;
        }
    }
    left.cmp(&right)
}

fn key_coordinate(request: &TableSortRequest, line: u32, offset: u32) -> CellCoordinate {
    match request.axis {
        TableSortAxis::Rows => CellCoordinate {
            row: request.region.start.row + line,
            column: request.region.start.column + offset,
        },
        TableSortAxis::Columns => CellCoordinate {
            row: request.region.start.row + offset,
            column: request.region.start.column + line,
        },
    }
}

fn line_coordinate(request: &TableSortRequest, line: u32, cross: u32) -> CellCoordinate {
    match request.axis {
        TableSortAxis::Rows => CellCoordinate {
            row: request.region.start.row + line,
            column: request.region.start.column + cross,
        },
        TableSortAxis::Columns => CellCoordinate {
            row: request.region.start.row + cross,
            column: request.region.start.column + line,
        },
    }
}

fn compare_key_values(
    left: &TableSortValue,
    right: &TableSortValue,
    key: TableSortKey,
) -> Ordering {
    match (left, right) {
        (TableSortValue::Blank, TableSortValue::Blank) => Ordering::Equal,
        (TableSortValue::Blank, _) => match key.blank_order {
            TableBlankOrder::First => Ordering::Less,
            TableBlankOrder::Last => Ordering::Greater,
        },
        (_, TableSortValue::Blank) => match key.blank_order {
            TableBlankOrder::First => Ordering::Greater,
            TableBlankOrder::Last => Ordering::Less,
        },
        _ => {
            let ordering = compare_nonblank(left, right, key.text_collation);
            match key.direction {
                TableSortDirection::Ascending => ordering,
                TableSortDirection::Descending => ordering.reverse(),
            }
        }
    }
}

fn compare_nonblank(
    left: &TableSortValue,
    right: &TableSortValue,
    collation: TableTextCollation,
) -> Ordering {
    if let (Some(left), Some(right)) = (numeric_parts(left), numeric_parts(right)) {
        return compare_numeric(left, right);
    }
    let rank = value_rank(left).cmp(&value_rank(right));
    if rank != Ordering::Equal {
        return rank;
    }
    match (left, right) {
        (TableSortValue::Boolean { value: left }, TableSortValue::Boolean { value: right }) => {
            left.cmp(right)
        }
        (
            TableSortValue::DateDays {
                days_since_unix_epoch: left,
            },
            TableSortValue::DateDays {
                days_since_unix_epoch: right,
            },
        ) => left.cmp(right),
        (TableSortValue::Text { value: left }, TableSortValue::Text { value: right }) => {
            match collation {
                TableTextCollation::Binary => left.cmp(right),
                TableTextCollation::AsciiCaseInsensitive => left
                    .bytes()
                    .map(|byte| byte.to_ascii_lowercase())
                    .cmp(right.bytes().map(|byte| byte.to_ascii_lowercase())),
            }
        }
        _ => Ordering::Equal,
    }
}

fn numeric_parts(value: &TableSortValue) -> Option<(i64, u8)> {
    match value {
        TableSortValue::Integer { value } => Some((*value, 0)),
        TableSortValue::Decimal { coefficient, scale } => Some((*coefficient, *scale)),
        _ => None,
    }
}

fn compare_numeric(left: (i64, u8), right: (i64, u8)) -> Ordering {
    let common_scale = left.1.max(right.1);
    let left = i128::from(left.0) * 10_i128.pow(u32::from(common_scale - left.1));
    let right = i128::from(right.0) * 10_i128.pow(u32::from(common_scale - right.1));
    left.cmp(&right)
}

const fn value_rank(value: &TableSortValue) -> u8 {
    match value {
        TableSortValue::Blank => 0,
        TableSortValue::Boolean { .. } => 1,
        TableSortValue::Integer { .. } | TableSortValue::Decimal { .. } => 2,
        TableSortValue::DateDays { .. } => 3,
        TableSortValue::Text { .. } => 4,
    }
}

fn serialize_bounded<T: Serialize>(value: &T, maximum: usize) -> Result<Vec<u8>, TableSortError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableSortError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableSortError::OutputLimit);
    }
    Ok(bytes)
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
