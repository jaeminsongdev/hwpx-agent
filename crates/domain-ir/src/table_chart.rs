use std::collections::HashSet;
use std::fmt;
use std::io::{self, Write};

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization;

use crate::{CellCoordinate, FormulaDecimal, LogicalId, TableGrid, TableGridError};

pub const TABLE_CHART_SCHEMA_VERSION: &str = "hwpx-agent.table-chart/v1";
pub const TABLE_CHART_FROM_TABLE_CAPABILITY_ID: &str = "table.chart_from_table";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableChartLimitConfig {
    pub input_bytes: usize,
    pub cells: usize,
    pub label_bytes: usize,
    pub identifier_bytes: usize,
    pub serialized_bytes: usize,
    pub decimal_scale: u8,
}

impl Default for TableChartLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 32 * 1024 * 1024,
            cells: 1_000_000,
            label_bytes: 1024 * 1024,
            identifier_bytes: 256,
            serialized_bytes: 128 * 1024 * 1024,
            decimal_scale: 18,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableChartLimits(TableChartLimitConfig);

impl TableChartLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_CELLS: usize = 1_000_000;
    pub const HARD_MAX_LABEL_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;
    pub const HARD_MAX_DECIMAL_SCALE: u8 = 38;

    /// Creates finite bounds for table-backed chart source planning.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling, or internally inconsistent limits.
    pub fn new(config: TableChartLimitConfig) -> Result<Self, TableChartError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.cells == 0
            || config.cells > Self::HARD_MAX_CELLS
            || config.label_bytes == 0
            || config.label_bytes > Self::HARD_MAX_LABEL_BYTES
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
            || config.decimal_scale > Self::HARD_MAX_DECIMAL_SCALE
        {
            return Err(TableChartError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableChartLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TableChartValueOrigin {
    Literal,
    FormulaDisplayCache {
        formula_sha256: String,
        cache_sha256: String,
    },
}

impl fmt::Debug for TableChartValueOrigin {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Literal => formatter.write_str("Literal"),
            Self::FormulaDisplayCache { .. } => {
                formatter.write_str("FormulaDisplayCache(<redacted>)")
            }
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TableChartValue {
    Blank,
    Number { value: FormulaDecimal },
    Text { value: String },
}

impl fmt::Debug for TableChartValue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Blank => formatter.write_str("Blank"),
            Self::Number { .. } => formatter.write_str("Number(<redacted>)"),
            Self::Text { .. } => formatter.write_str("Text(<redacted>)"),
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableChartCellDraft {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub source_sha256: String,
    pub value: TableChartValue,
    pub value_origin: TableChartValueOrigin,
}

impl fmt::Debug for TableChartCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartCellDraft")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("source_sha256", &"<redacted>")
            .field("value", &self.value)
            .field("value_origin", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartCell {
    master_cell_id: LogicalId,
    coordinate: CellCoordinate,
    source_sha256: String,
    value: TableChartValue,
    value_origin: TableChartValueOrigin,
}

impl TableChartCell {
    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
    }

    #[must_use]
    pub const fn coordinate(&self) -> CellCoordinate {
        self.coordinate
    }

    #[must_use]
    pub fn source_sha256(&self) -> &str {
        &self.source_sha256
    }

    #[must_use]
    pub const fn value(&self) -> &TableChartValue {
        &self.value
    }

    #[must_use]
    pub const fn value_origin(&self) -> &TableChartValueOrigin {
        &self.value_origin
    }
}

impl fmt::Debug for TableChartCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartCell")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("source_sha256", &"<redacted>")
            .field("value", &self.value)
            .field("value_origin", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableChartSourceStateDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub grid_sha256: String,
    pub table_state_sha256: String,
    pub cells: Vec<TableChartCellDraft>,
}

impl fmt::Debug for TableChartSourceStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartSourceStateDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_state_sha256", &"<redacted>")
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartSourceState {
    schema_version: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    table_state_sha256: String,
    cells: Vec<TableChartCell>,
}

impl fmt::Debug for TableChartSourceState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartSourceState")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_state_sha256", &"<redacted>")
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

impl TableChartSourceState {
    /// Validates a complete typed cell snapshot against one exact logical table grid.
    ///
    /// # Errors
    ///
    /// Rejects schema, limit, digest, grid, cell coverage, value, origin, and normalization drift.
    pub fn from_draft(
        draft: TableChartSourceStateDraft,
        grid: &TableGrid,
        limits: TableChartLimits,
    ) -> Result<Self, TableChartError> {
        if draft.schema_version != TABLE_CHART_SCHEMA_VERSION {
            return Err(TableChartError::UnsupportedVersion);
        }
        validate_identifier(&draft.table_id, limits)?;
        validate_digest(&draft.grid_sha256)?;
        validate_digest(&draft.table_state_sha256)?;
        if draft.grid_sha256 != grid_digest(grid)? {
            return Err(TableChartError::GridMismatch);
        }
        if draft.cells.len() > limits.0.cells {
            return Err(TableChartError::CellLimitExceeded);
        }
        if draft.cells.len() != grid.master_cell_count() {
            return Err(TableChartError::IncompleteCellSet);
        }

        let mut seen_ids = HashSet::with_capacity(draft.cells.len());
        let mut seen_coordinates = HashSet::with_capacity(draft.cells.len());
        let mut cells = Vec::new();
        cells
            .try_reserve_exact(draft.cells.len())
            .map_err(|_| TableChartError::AllocationFailed)?;
        for cell in draft.cells {
            validate_identifier(&cell.master_cell_id, limits)?;
            validate_digest(&cell.source_sha256)?;
            validate_value(&cell.value, limits)?;
            validate_origin(&cell.value_origin)?;
            if !seen_ids.insert(cell.master_cell_id.clone())
                || !seen_coordinates.insert((cell.coordinate.row, cell.coordinate.column))
            {
                return Err(TableChartError::DuplicateCell);
            }
            let span = grid
                .master_cell_at(cell.coordinate)
                .map_err(map_grid_error)?;
            if span.master_cell_id != cell.master_cell_id
                || span.row != cell.coordinate.row
                || span.column != cell.coordinate.column
            {
                return Err(TableChartError::CellGridMismatch);
            }
            cells.push(TableChartCell {
                master_cell_id: cell.master_cell_id,
                coordinate: cell.coordinate,
                source_sha256: cell.source_sha256,
                value: cell.value,
                value_origin: cell.value_origin,
            });
        }
        cells.sort_by_key(|cell| (cell.coordinate.row, cell.coordinate.column));
        if cells.iter().zip(grid.master_cells()).any(|(cell, span)| {
            cell.master_cell_id != span.master_cell_id
                || cell.coordinate.row != span.row
                || cell.coordinate.column != span.column
        }) {
            return Err(TableChartError::IncompleteCellSet);
        }

        let state = Self {
            schema_version: TABLE_CHART_SCHEMA_VERSION,
            table_id: draft.table_id,
            grid_sha256: draft.grid_sha256,
            table_state_sha256: draft.table_state_sha256,
            cells,
        };
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    /// Parses and validates a bounded untrusted table-chart source snapshot.
    ///
    /// # Errors
    ///
    /// Returns stable input, JSON, or semantic validation errors.
    pub fn from_json(
        bytes: &[u8],
        grid: &TableGrid,
        limits: TableChartLimits,
    ) -> Result<Self, TableChartError> {
        if bytes.len() > limits.0.input_bytes {
            return Err(TableChartError::InputLimitExceeded);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| TableChartError::InvalidJson)?;
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
    pub fn table_state_sha256(&self) -> &str {
        &self.table_state_sha256
    }

    #[must_use]
    pub fn cells(&self) -> &[TableChartCell] {
        &self.cells
    }

    /// Emits canonical bounded JSON in logical row-major order.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization or size error.
    pub fn canonical_json(&self, limits: TableChartLimits) -> Result<Vec<u8>, TableChartError> {
        to_bounded_json(self, limits.0.serialized_bytes)
    }

    /// Hashes the exact canonical source snapshot.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization errors.
    pub fn canonical_sha256(&self, limits: TableChartLimits) -> Result<[u8; 32], TableChartError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    fn cell_at(&self, coordinate: CellCoordinate) -> Option<&TableChartCell> {
        self.cells
            .binary_search_by_key(&(coordinate.row, coordinate.column), |cell| {
                (cell.coordinate.row, cell.coordinate.column)
            })
            .ok()
            .and_then(|index| self.cells.get(index))
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableChartRegion {
    pub start: CellCoordinate,
    pub end: CellCoordinate,
}

impl TableChartRegion {
    fn rows(self) -> Result<u32, TableChartError> {
        self.end
            .row
            .checked_sub(self.start.row)
            .and_then(|value| value.checked_add(1))
            .ok_or(TableChartError::InvalidRegion)
    }

    fn columns(self) -> Result<u32, TableChartError> {
        self.end
            .column
            .checked_sub(self.start.column)
            .and_then(|value| value.checked_add(1))
            .ok_or(TableChartError::InvalidRegion)
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableChartRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub chart_id: LogicalId,
    pub data_resource_id: LogicalId,
    pub source_region: TableChartRegion,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
}

impl fmt::Debug for TableChartRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("chart_id", &"<redacted>")
            .field("data_resource_id", &"<redacted>")
            .field("source_region", &self.source_region)
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    chart_id: LogicalId,
    data_resource_id: LogicalId,
    source_region: TableChartRegion,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
}

impl fmt::Debug for TableChartRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("chart_id", &"<redacted>")
            .field("data_resource_id", &"<redacted>")
            .field("source_region", &self.source_region)
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .finish()
    }
}

impl TableChartRequest {
    /// Validates exact state/flow bindings and a rectangular, unmerged cell-block selection.
    ///
    /// Cursor-only/default-data chart creation is intentionally excluded from this linked-table
    /// capability because it does not establish a table-data binding.
    ///
    /// # Errors
    ///
    /// Rejects schema, identifier, region, merge, state, flow, and limit drift.
    pub fn from_draft(
        draft: TableChartRequestDraft,
        state: &TableChartSourceState,
        grid: &TableGrid,
        current_document_flow_sha256: &str,
        limits: TableChartLimits,
    ) -> Result<Self, TableChartError> {
        if draft.schema_version != TABLE_CHART_SCHEMA_VERSION {
            return Err(TableChartError::UnsupportedVersion);
        }
        validate_identifier(&draft.table_id, limits)?;
        validate_identifier(&draft.chart_id, limits)?;
        validate_identifier(&draft.data_resource_id, limits)?;
        if draft.table_id == draft.chart_id
            || draft.table_id == draft.data_resource_id
            || draft.chart_id == draft.data_resource_id
        {
            return Err(TableChartError::IdentifierCollision);
        }
        validate_digest(&draft.expected_source_state_sha256)?;
        validate_digest(&draft.expected_document_flow_sha256)?;
        validate_digest(current_document_flow_sha256)?;
        if draft.table_id != state.table_id {
            return Err(TableChartError::TableIdentityMismatch);
        }
        if state.grid_sha256 != grid_digest(grid)? {
            return Err(TableChartError::GridMismatch);
        }
        if draft.expected_source_state_sha256 != hex(state.canonical_sha256(limits)?) {
            return Err(TableChartError::StateBindingMismatch);
        }
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(TableChartError::FlowBindingMismatch);
        }
        validate_region(draft.source_region, state, grid, limits)?;

        Ok(Self {
            schema_version: TABLE_CHART_SCHEMA_VERSION,
            capability_id: TABLE_CHART_FROM_TABLE_CAPABILITY_ID,
            table_id: draft.table_id,
            chart_id: draft.chart_id,
            data_resource_id: draft.data_resource_id,
            source_region: draft.source_region,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
        })
    }

    #[must_use]
    pub const fn capability_id(&self) -> &str {
        self.capability_id
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn chart_id(&self) -> &LogicalId {
        &self.chart_id
    }

    #[must_use]
    pub const fn data_resource_id(&self) -> &LogicalId {
        &self.data_resource_id
    }

    #[must_use]
    pub const fn source_region(&self) -> TableChartRegion {
        self.source_region
    }

    #[must_use]
    pub fn expected_source_state_sha256(&self) -> &str {
        &self.expected_source_state_sha256
    }

    #[must_use]
    pub fn expected_document_flow_sha256(&self) -> &str {
        &self.expected_document_flow_sha256
    }

    /// Emits a canonical request suitable for deterministic phase handoff.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization or size error.
    pub fn canonical_json(&self, limits: TableChartLimits) -> Result<Vec<u8>, TableChartError> {
        to_bounded_json(self, limits.0.serialized_bytes)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartCategory {
    coordinate: CellCoordinate,
    label: String,
    source_sha256: String,
}

impl TableChartCategory {
    #[must_use]
    pub const fn coordinate(&self) -> CellCoordinate {
        self.coordinate
    }

    #[must_use]
    pub fn label(&self) -> &str {
        &self.label
    }

    #[must_use]
    pub fn source_sha256(&self) -> &str {
        &self.source_sha256
    }
}

impl fmt::Debug for TableChartCategory {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartCategory")
            .field("coordinate", &self.coordinate)
            .field("label", &"<redacted>")
            .field("source_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartDataPoint {
    coordinate: CellCoordinate,
    value: Option<FormulaDecimal>,
    source_sha256: String,
    value_origin: TableChartValueOrigin,
}

impl TableChartDataPoint {
    #[must_use]
    pub const fn coordinate(&self) -> CellCoordinate {
        self.coordinate
    }

    #[must_use]
    pub const fn value(&self) -> Option<FormulaDecimal> {
        self.value
    }

    #[must_use]
    pub fn source_sha256(&self) -> &str {
        &self.source_sha256
    }

    #[must_use]
    pub const fn value_origin(&self) -> &TableChartValueOrigin {
        &self.value_origin
    }
}

impl fmt::Debug for TableChartDataPoint {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartDataPoint")
            .field("coordinate", &self.coordinate)
            .field("value", &self.value.map(|_| "<redacted>"))
            .field("source_sha256", &"<redacted>")
            .field("value_origin", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartSeries {
    header_coordinate: CellCoordinate,
    label: String,
    header_source_sha256: String,
    values: Vec<TableChartDataPoint>,
}

impl TableChartSeries {
    #[must_use]
    pub const fn header_coordinate(&self) -> CellCoordinate {
        self.header_coordinate
    }

    #[must_use]
    pub fn label(&self) -> &str {
        &self.label
    }

    #[must_use]
    pub fn header_source_sha256(&self) -> &str {
        &self.header_source_sha256
    }

    #[must_use]
    pub fn values(&self) -> &[TableChartDataPoint] {
        &self.values
    }
}

impl fmt::Debug for TableChartSeries {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartSeries")
            .field("header_coordinate", &self.header_coordinate)
            .field("label", &"<redacted>")
            .field("header_source_sha256", &"<redacted>")
            .field("value_count", &self.values.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartReceipt {
    pub ignored_corner: CellCoordinate,
    pub category_count: u32,
    pub series_count: u32,
    pub data_point_count: u64,
    pub blank_data_point_count: u64,
    pub source_table_preserved: bool,
    pub source_state_sha256_before: String,
    pub source_state_sha256_after: String,
    pub document_flow_sha256_before: String,
}

impl fmt::Debug for TableChartReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartReceipt")
            .field("ignored_corner", &self.ignored_corner)
            .field("category_count", &self.category_count)
            .field("series_count", &self.series_count)
            .field("data_point_count", &self.data_point_count)
            .field("blank_data_point_count", &self.blank_data_point_count)
            .field("source_table_preserved", &self.source_table_preserved)
            .field("source_state_sha256_before", &"<redacted>")
            .field("source_state_sha256_after", &"<redacted>")
            .field("document_flow_sha256_before", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableChartInitialType {
    ThreeDimensionalVerticalBar,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableChartInsertionContext {
    ExactSelectedCellBlock,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableChartPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    chart_id: LogicalId,
    data_resource_id: LogicalId,
    source_region: TableChartRegion,
    initial_type: TableChartInitialType,
    insertion_context: TableChartInsertionContext,
    categories: Vec<TableChartCategory>,
    series: Vec<TableChartSeries>,
    receipt: TableChartReceipt,
}

impl fmt::Debug for TableChartPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableChartPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("chart_id", &"<redacted>")
            .field("data_resource_id", &"<redacted>")
            .field("source_region", &self.source_region)
            .field("initial_type", &self.initial_type)
            .field("insertion_context", &self.insertion_context)
            .field("category_count", &self.categories.len())
            .field("series_count", &self.series.len())
            .field("receipt", &self.receipt)
            .finish()
    }
}

impl TableChartPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &str {
        self.capability_id
    }

    #[must_use]
    pub const fn table_id(&self) -> &LogicalId {
        &self.table_id
    }

    #[must_use]
    pub const fn chart_id(&self) -> &LogicalId {
        &self.chart_id
    }

    #[must_use]
    pub const fn data_resource_id(&self) -> &LogicalId {
        &self.data_resource_id
    }

    #[must_use]
    pub const fn source_region(&self) -> TableChartRegion {
        self.source_region
    }

    #[must_use]
    pub fn categories(&self) -> &[TableChartCategory] {
        &self.categories
    }

    #[must_use]
    pub fn series(&self) -> &[TableChartSeries] {
        &self.series
    }

    #[must_use]
    pub const fn initial_type(&self) -> TableChartInitialType {
        self.initial_type
    }

    #[must_use]
    pub const fn insertion_context(&self) -> TableChartInsertionContext {
        self.insertion_context
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableChartReceipt {
        &self.receipt
    }

    /// Emits the complete linked-data creation plan as canonical bounded JSON.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization or size error.
    pub fn canonical_json(&self, limits: TableChartLimits) -> Result<Vec<u8>, TableChartError> {
        to_bounded_json(self, limits.0.serialized_bytes)
    }

    /// Hashes the complete canonical linked-data creation plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization errors.
    pub fn canonical_sha256(&self, limits: TableChartLimits) -> Result<[u8; 32], TableChartError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

#[derive(Debug)]
pub struct TableChartBuilder;

impl TableChartBuilder {
    /// Projects one linked chart data plan from an exact rectangular table cell block.
    ///
    /// The corner is ignored, the remainder of the first row supplies series labels, the remainder
    /// of the first column supplies category labels, and the body must be numeric or blank.
    ///
    /// # Errors
    ///
    /// Revalidates every request/state/grid/flow binding and fails closed on stale or unsupported
    /// source data.
    pub fn build(
        request: &TableChartRequest,
        state: &TableChartSourceState,
        grid: &TableGrid,
        current_document_flow_sha256: &str,
        limits: TableChartLimits,
    ) -> Result<TableChartPlan, TableChartError> {
        validate_build_bindings(request, state, grid, current_document_flow_sha256, limits)?;
        validate_region(request.source_region, state, grid, limits)?;

        let region = request.source_region;
        let row_count = region.rows()?;
        let column_count = region.columns()?;
        let category_capacity =
            usize::try_from(row_count - 1).map_err(|_| TableChartError::AllocationFailed)?;
        let categories = build_categories(state, region, category_capacity)?;
        let (series, blank_data_point_count) = build_series(state, region, category_capacity)?;

        let data_point_count = u64::from(row_count - 1)
            .checked_mul(u64::from(column_count - 1))
            .ok_or(TableChartError::CountOverflow)?;
        let receipt = TableChartReceipt {
            ignored_corner: region.start,
            category_count: row_count - 1,
            series_count: column_count - 1,
            data_point_count,
            blank_data_point_count,
            source_table_preserved: true,
            source_state_sha256_before: request.expected_source_state_sha256.clone(),
            source_state_sha256_after: request.expected_source_state_sha256.clone(),
            document_flow_sha256_before: request.expected_document_flow_sha256.clone(),
        };
        let plan = TableChartPlan {
            schema_version: TABLE_CHART_SCHEMA_VERSION,
            capability_id: TABLE_CHART_FROM_TABLE_CAPABILITY_ID,
            table_id: request.table_id.clone(),
            chart_id: request.chart_id.clone(),
            data_resource_id: request.data_resource_id.clone(),
            source_region: request.source_region,
            initial_type: TableChartInitialType::ThreeDimensionalVerticalBar,
            insertion_context: TableChartInsertionContext::ExactSelectedCellBlock,
            categories,
            series,
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

fn validate_build_bindings(
    request: &TableChartRequest,
    state: &TableChartSourceState,
    grid: &TableGrid,
    current_document_flow_sha256: &str,
    limits: TableChartLimits,
) -> Result<(), TableChartError> {
    if request.table_id != state.table_id {
        return Err(TableChartError::TableIdentityMismatch);
    }
    if request.expected_source_state_sha256 != hex(state.canonical_sha256(limits)?) {
        return Err(TableChartError::StateBindingMismatch);
    }
    validate_digest(current_document_flow_sha256)?;
    if request.expected_document_flow_sha256 != current_document_flow_sha256 {
        return Err(TableChartError::FlowBindingMismatch);
    }
    if state.grid_sha256 != grid_digest(grid)? {
        return Err(TableChartError::GridMismatch);
    }
    Ok(())
}

fn build_categories(
    state: &TableChartSourceState,
    region: TableChartRegion,
    capacity: usize,
) -> Result<Vec<TableChartCategory>, TableChartError> {
    let mut categories = Vec::new();
    categories
        .try_reserve_exact(capacity)
        .map_err(|_| TableChartError::AllocationFailed)?;
    for row in (region.start.row + 1)..=region.end.row {
        let coordinate = CellCoordinate {
            row,
            column: region.start.column,
        };
        let cell = state
            .cell_at(coordinate)
            .ok_or(TableChartError::IncompleteCellSet)?;
        categories.push(TableChartCategory {
            coordinate,
            label: value_label(&cell.value),
            source_sha256: cell.source_sha256.clone(),
        });
    }
    Ok(categories)
}

fn build_series(
    state: &TableChartSourceState,
    region: TableChartRegion,
    value_capacity: usize,
) -> Result<(Vec<TableChartSeries>, u64), TableChartError> {
    let series_capacity =
        usize::try_from(region.columns()? - 1).map_err(|_| TableChartError::AllocationFailed)?;
    let mut series = Vec::new();
    series
        .try_reserve_exact(series_capacity)
        .map_err(|_| TableChartError::AllocationFailed)?;
    let mut blank_count = 0_u64;
    for column in (region.start.column + 1)..=region.end.column {
        let header_coordinate = CellCoordinate {
            row: region.start.row,
            column,
        };
        let header = state
            .cell_at(header_coordinate)
            .ok_or(TableChartError::IncompleteCellSet)?;
        let (values, series_blank_count) =
            build_series_values(state, region, column, value_capacity)?;
        blank_count = blank_count
            .checked_add(series_blank_count)
            .ok_or(TableChartError::CountOverflow)?;
        series.push(TableChartSeries {
            header_coordinate,
            label: value_label(&header.value),
            header_source_sha256: header.source_sha256.clone(),
            values,
        });
    }
    Ok((series, blank_count))
}

fn build_series_values(
    state: &TableChartSourceState,
    region: TableChartRegion,
    column: u32,
    capacity: usize,
) -> Result<(Vec<TableChartDataPoint>, u64), TableChartError> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| TableChartError::AllocationFailed)?;
    let mut blank_count = 0_u64;
    for row in (region.start.row + 1)..=region.end.row {
        let coordinate = CellCoordinate { row, column };
        let cell = state
            .cell_at(coordinate)
            .ok_or(TableChartError::IncompleteCellSet)?;
        let value = match cell.value {
            TableChartValue::Blank => {
                blank_count = blank_count
                    .checked_add(1)
                    .ok_or(TableChartError::CountOverflow)?;
                None
            }
            TableChartValue::Number { value } => Some(value),
            TableChartValue::Text { .. } => return Err(TableChartError::NonNumericDataCell),
        };
        values.push(TableChartDataPoint {
            coordinate,
            value,
            source_sha256: cell.source_sha256.clone(),
            value_origin: cell.value_origin.clone(),
        });
    }
    Ok((values, blank_count))
}

fn validate_region(
    region: TableChartRegion,
    state: &TableChartSourceState,
    grid: &TableGrid,
    limits: TableChartLimits,
) -> Result<(), TableChartError> {
    let rows = region.rows()?;
    let columns = region.columns()?;
    if rows < 2
        || columns < 2
        || region.end.row >= grid.rows()
        || region.end.column >= grid.columns()
    {
        return Err(TableChartError::InvalidRegion);
    }
    let cell_count = usize::try_from(
        u64::from(rows)
            .checked_mul(u64::from(columns))
            .ok_or(TableChartError::CountOverflow)?,
    )
    .map_err(|_| TableChartError::CellLimitExceeded)?;
    if cell_count > limits.0.cells {
        return Err(TableChartError::CellLimitExceeded);
    }
    for row in region.start.row..=region.end.row {
        for column in region.start.column..=region.end.column {
            let coordinate = CellCoordinate { row, column };
            let span = grid.master_cell_at(coordinate).map_err(map_grid_error)?;
            if span.row_span != 1
                || span.column_span != 1
                || span.row != row
                || span.column != column
            {
                return Err(TableChartError::MergedCellInSource);
            }
            let cell = state
                .cell_at(coordinate)
                .ok_or(TableChartError::IncompleteCellSet)?;
            if cell.master_cell_id != span.master_cell_id {
                return Err(TableChartError::CellGridMismatch);
            }
        }
    }
    Ok(())
}

fn validate_value(
    value: &TableChartValue,
    limits: TableChartLimits,
) -> Result<(), TableChartError> {
    match value {
        TableChartValue::Blank => Ok(()),
        TableChartValue::Number { value } => {
            if value.scale() > limits.0.decimal_scale
                || FormulaDecimal::new(value.coefficient(), value.scale()) != *value
            {
                return Err(TableChartError::InvalidNumber);
            }
            Ok(())
        }
        TableChartValue::Text { value } => {
            if value.len() > limits.0.label_bytes {
                return Err(TableChartError::LabelLimitExceeded);
            }
            if value.nfc().collect::<String>() != *value {
                return Err(TableChartError::NonCanonicalText);
            }
            Ok(())
        }
    }
}

fn validate_origin(origin: &TableChartValueOrigin) -> Result<(), TableChartError> {
    match origin {
        TableChartValueOrigin::Literal => Ok(()),
        TableChartValueOrigin::FormulaDisplayCache {
            formula_sha256,
            cache_sha256,
        } => {
            validate_digest(formula_sha256)?;
            validate_digest(cache_sha256)
        }
    }
}

fn value_label(value: &TableChartValue) -> String {
    match value {
        TableChartValue::Blank => String::new(),
        TableChartValue::Number { value } => decimal_label(*value),
        TableChartValue::Text { value } => value.clone(),
    }
}

fn decimal_label(value: FormulaDecimal) -> String {
    if value.scale() == 0 {
        return value.coefficient().to_string();
    }
    let negative = value.coefficient() < 0;
    let digits = value.coefficient().unsigned_abs().to_string();
    let scale = usize::from(value.scale());
    let mut output = String::new();
    if negative {
        output.push('-');
    }
    if digits.len() <= scale {
        output.push_str("0.");
        output.extend(std::iter::repeat_n('0', scale - digits.len()));
        output.push_str(&digits);
    } else {
        let split = digits.len() - scale;
        output.push_str(&digits[..split]);
        output.push('.');
        output.push_str(&digits[split..]);
    }
    output
}

fn validate_identifier(id: &LogicalId, limits: TableChartLimits) -> Result<(), TableChartError> {
    if id.as_str().len() > limits.0.identifier_bytes {
        return Err(TableChartError::IdentifierLimitExceeded);
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), TableChartError> {
    if value.len() != 64
        || !value
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
    {
        return Err(TableChartError::InvalidDigest);
    }
    Ok(())
}

fn grid_digest(grid: &TableGrid) -> Result<String, TableChartError> {
    grid.canonical_sha256()
        .map(hex)
        .map_err(|_| TableChartError::GridMismatch)
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    use std::fmt::Write as _;

    bytes
        .as_ref()
        .iter()
        .fold(String::new(), |mut output, byte| {
            let _ = write!(output, "{byte:02x}");
            output
        })
}

fn map_grid_error(error: TableGridError) -> TableChartError {
    match error {
        TableGridError::CoordinateOutOfBounds => TableChartError::InvalidRegion,
        _ => TableChartError::GridMismatch,
    }
}

fn to_bounded_json<T: Serialize>(value: &T, max_bytes: usize) -> Result<Vec<u8>, TableChartError> {
    let mut writer = BoundedWriter::new(max_bytes)?;
    serde_json::to_writer(&mut writer, value).map_err(|error| {
        if writer.limit_exceeded {
            TableChartError::SerializedLimitExceeded
        } else if writer.allocation_failed {
            TableChartError::AllocationFailed
        } else {
            let _ = error;
            TableChartError::SerializationFailed
        }
    })?;
    Ok(writer.bytes)
}

struct BoundedWriter {
    bytes: Vec<u8>,
    max_bytes: usize,
    limit_exceeded: bool,
    allocation_failed: bool,
}

impl BoundedWriter {
    fn new(max_bytes: usize) -> Result<Self, TableChartError> {
        if max_bytes == 0 || max_bytes > TableChartLimits::HARD_MAX_SERIALIZED_BYTES {
            return Err(TableChartError::InvalidLimit);
        }
        Ok(Self {
            bytes: Vec::new(),
            max_bytes,
            limit_exceeded: false,
            allocation_failed: false,
        })
    }
}

impl Write for BoundedWriter {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        let next = self
            .bytes
            .len()
            .checked_add(buffer.len())
            .ok_or_else(|| io::Error::other("serialized size overflow"))?;
        if next > self.max_bytes {
            self.limit_exceeded = true;
            return Err(io::Error::other("serialized limit exceeded"));
        }
        self.bytes.try_reserve(buffer.len()).map_err(|_| {
            self.allocation_failed = true;
            io::Error::other("allocation failed")
        })?;
        self.bytes.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum TableChartError {
    #[error("table-chart limits are invalid")]
    InvalidLimit,
    #[error("table-chart input exceeds the configured byte limit")]
    InputLimitExceeded,
    #[error("table-chart JSON is invalid")]
    InvalidJson,
    #[error("table-chart schema version is unsupported")]
    UnsupportedVersion,
    #[error("table-chart identifier exceeds the configured byte limit")]
    IdentifierLimitExceeded,
    #[error("table-chart identifiers collide")]
    IdentifierCollision,
    #[error("table-chart digest must be lowercase hexadecimal SHA-256")]
    InvalidDigest,
    #[error("table-chart grid binding does not match")]
    GridMismatch,
    #[error("table-chart table identity does not match")]
    TableIdentityMismatch,
    #[error("table-chart cell count exceeds the configured limit")]
    CellLimitExceeded,
    #[error("table-chart source cell set is incomplete")]
    IncompleteCellSet,
    #[error("table-chart source contains a duplicate cell")]
    DuplicateCell,
    #[error("table-chart source cell does not match the grid")]
    CellGridMismatch,
    #[error("table-chart label exceeds the configured byte limit")]
    LabelLimitExceeded,
    #[error("table-chart text is not NFC-normalized")]
    NonCanonicalText,
    #[error("table-chart number is non-canonical or exceeds the configured scale")]
    InvalidNumber,
    #[error("table-chart source region is invalid or smaller than two by two")]
    InvalidRegion,
    #[error("table-chart linked source cannot contain merged cells")]
    MergedCellInSource,
    #[error("table-chart data-body cell must be numeric or blank")]
    NonNumericDataCell,
    #[error("table-chart source-state binding changed")]
    StateBindingMismatch,
    #[error("table-chart document-flow binding changed")]
    FlowBindingMismatch,
    #[error("table-chart count overflowed")]
    CountOverflow,
    #[error("table-chart allocation failed")]
    AllocationFailed,
    #[error("table-chart canonical serialization failed")]
    SerializationFailed,
    #[error("table-chart canonical serialization exceeds the configured limit")]
    SerializedLimitExceeded,
}
