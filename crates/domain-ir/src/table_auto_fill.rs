use std::collections::BTreeMap;
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{CellCoordinate, LogicalId, TableGrid, TableSortValue};

pub const TABLE_AUTO_FILL_SCHEMA_VERSION: &str = "hwpx-agent.table-auto-fill/v1";
pub const TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION: &str = "hwpx-agent.table-auto-fill-series/v1";
pub const TABLE_AUTO_FILL_CAPABILITY_ID: &str = "table.auto_fill";
pub const TABLE_AUTO_FILL_SERIES_CAPABILITY_ID: &str = "table.auto_fill_series";

pub type TableAutoFillValue = TableSortValue;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableAutoFillLimitConfig {
    pub input_bytes: usize,
    pub selected_cells: usize,
    pub series_items: usize,
    pub text_bytes: usize,
    pub total_text_bytes: usize,
    pub generation_work: u64,
    pub serialized_bytes: usize,
}

impl Default for TableAutoFillLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 4 * 1024 * 1024,
            selected_cells: 1_000_000,
            series_items: 4_096,
            text_bytes: 16 * 1024,
            total_text_bytes: 4 * 1024 * 1024,
            generation_work: 1_000_000,
            serialized_bytes: 64 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableAutoFillLimits(TableAutoFillLimitConfig);

impl TableAutoFillLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_SELECTED_CELLS: usize = 1_000_000;
    pub const HARD_MAX_SERIES_ITEMS: usize = 65_536;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_TOTAL_TEXT_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_GENERATION_WORK: u64 = 10_000_000;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for series admission and fill planning.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling or internally inconsistent limits.
    pub fn new(config: TableAutoFillLimitConfig) -> Result<Self, TableAutoFillError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.selected_cells == 0
            || config.selected_cells > Self::HARD_MAX_SELECTED_CELLS
            || config.series_items == 0
            || config.series_items > Self::HARD_MAX_SERIES_ITEMS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.total_text_bytes == 0
            || config.total_text_bytes > Self::HARD_MAX_TOTAL_TEXT_BYTES
            || config.text_bytes > config.total_text_bytes
            || config.generation_work == 0
            || config.generation_work > Self::HARD_MAX_GENERATION_WORK
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TableAutoFillError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableAutoFillLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableAutoFillOrder {
    RowMajor,
    ColumnMajor,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableAutoFillFormulaPolicy {
    Reject,
    ReplaceBound,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAutoFillRegion {
    pub start: CellCoordinate,
    pub end: CellCoordinate,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAutoFillNumber {
    pub coefficient: i64,
    pub scale: u8,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case", tag = "kind", deny_unknown_fields)]
pub enum TableAutoFillDefinition {
    ExplicitCycle {
        items: Vec<TableAutoFillValue>,
    },
    LinearNumber {
        start: TableAutoFillNumber,
        step: TableAutoFillNumber,
    },
    LinearDateDays {
        start_days_since_unix_epoch: i32,
        step_days: i32,
    },
}

impl fmt::Debug for TableAutoFillDefinition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ExplicitCycle { items } => formatter
                .debug_struct("ExplicitCycle")
                .field("item_count", &items.len())
                .finish(),
            Self::LinearNumber { .. } => formatter.write_str("LinearNumber(<redacted>)"),
            Self::LinearDateDays { .. } => formatter.write_str("LinearDateDays(<redacted>)"),
        }
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAutoFillSeriesDraft {
    pub schema_version: String,
    pub series_id: LogicalId,
    pub definition: TableAutoFillDefinition,
}

impl fmt::Debug for TableAutoFillSeriesDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillSeriesDraft")
            .field("schema_version", &self.schema_version)
            .field("series_id", &"<redacted>")
            .field("definition", &self.definition)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAutoFillSeries {
    schema_version: &'static str,
    capability_id: &'static str,
    series_id: LogicalId,
    definition: TableAutoFillDefinition,
}

impl TableAutoFillSeries {
    /// Validates and canonicalizes one reusable scalar fill series.
    ///
    /// # Errors
    ///
    /// Rejects version, empty series, scale, text and finite-limit violations.
    pub fn from_draft(
        draft: TableAutoFillSeriesDraft,
        limits: TableAutoFillLimits,
    ) -> Result<Self, TableAutoFillError> {
        if draft.schema_version != TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION {
            return Err(TableAutoFillError::UnsupportedSeriesVersion);
        }
        let mut definition = draft.definition;
        validate_definition(&mut definition, limits)?;
        let series = Self {
            schema_version: TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION,
            capability_id: TABLE_AUTO_FILL_SERIES_CAPABILITY_ID,
            series_id: draft.series_id,
            definition,
        };
        let _ = series.canonical_json(limits)?;
        Ok(series)
    }

    /// Parses strict bounded JSON into a validated series.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and semantic
    /// failures reported by [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        limits: TableAutoFillLimits,
    ) -> Result<Self, TableAutoFillError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableAutoFillError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn series_id(&self) -> &LogicalId {
        &self.series_id
    }

    #[must_use]
    pub const fn definition(&self) -> &TableAutoFillDefinition {
        &self.definition
    }

    /// Serializes the validated series under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(
        &self,
        limits: TableAutoFillLimits,
    ) -> Result<Vec<u8>, TableAutoFillError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over bounded canonical series JSON.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableAutoFillLimits,
    ) -> Result<[u8; 32], TableAutoFillError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    fn validate_for_limits(&self, limits: TableAutoFillLimits) -> Result<(), TableAutoFillError> {
        let mut definition = self.definition.clone();
        validate_definition(&mut definition, limits)?;
        if definition != self.definition {
            return Err(TableAutoFillError::SeriesBindingMismatch);
        }
        let _ = self.canonical_json(limits)?;
        Ok(())
    }

    fn value_at(&self, index: u64) -> Result<TableAutoFillValue, TableAutoFillError> {
        match &self.definition {
            TableAutoFillDefinition::ExplicitCycle { items } => {
                let length = u64::try_from(items.len())
                    .map_err(|_| TableAutoFillError::GenerationOverflow)?;
                let offset = usize::try_from(index % length)
                    .map_err(|_| TableAutoFillError::GenerationOverflow)?;
                items
                    .get(offset)
                    .cloned()
                    .ok_or(TableAutoFillError::GenerationOverflow)
            }
            TableAutoFillDefinition::LinearNumber { start, step } => {
                generate_number(*start, *step, index)
            }
            TableAutoFillDefinition::LinearDateDays {
                start_days_since_unix_epoch,
                step_days,
            } => {
                let offset = i128::from(*step_days)
                    .checked_mul(i128::from(index))
                    .ok_or(TableAutoFillError::GenerationOverflow)?;
                let value = i128::from(*start_days_since_unix_epoch)
                    .checked_add(offset)
                    .ok_or(TableAutoFillError::GenerationOverflow)?;
                let days_since_unix_epoch =
                    i32::try_from(value).map_err(|_| TableAutoFillError::GenerationOverflow)?;
                Ok(TableAutoFillValue::DateDays {
                    days_since_unix_epoch,
                })
            }
        }
    }
}

impl fmt::Debug for TableAutoFillSeries {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillSeries")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("series_id", &"<redacted>")
            .field("definition", &self.definition)
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAutoFillCellDraft {
    pub coordinate: CellCoordinate,
    pub payload_sha256: String,
    pub formula_sha256: Option<String>,
    pub style_sha256: String,
    pub current_value: TableAutoFillValue,
}

impl fmt::Debug for TableAutoFillCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillCellDraft")
            .field("coordinate", &self.coordinate)
            .field("payload_sha256", &"<redacted>")
            .field(
                "formula_sha256",
                &self.formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("style_sha256", &"<redacted>")
            .field("current_value", &self.current_value)
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableAutoFillRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub region: TableAutoFillRegion,
    pub order: TableAutoFillOrder,
    pub series_id: LogicalId,
    pub series_sha256: String,
    pub start_index: u64,
    pub formula_policy: TableAutoFillFormulaPolicy,
    pub cells: Vec<TableAutoFillCellDraft>,
}

impl fmt::Debug for TableAutoFillRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("region", &self.region)
            .field("order", &self.order)
            .field("series_id", &"<redacted>")
            .field("series_sha256", &"<redacted>")
            .field("start_index", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAutoFillRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    region: TableAutoFillRegion,
    order: TableAutoFillOrder,
    series_id: LogicalId,
    series_sha256: String,
    start_index: u64,
    formula_policy: TableAutoFillFormulaPolicy,
    cells: Vec<TableAutoFillCellDraft>,
}

impl TableAutoFillRequest {
    /// Validates one exact merge-free target region against a canonical series and table grid.
    ///
    /// # Errors
    ///
    /// Rejects version, grid, region, series binding, cell-set, formula-policy and finite-limit
    /// drift.
    pub fn from_draft(
        draft: TableAutoFillRequestDraft,
        series: &TableAutoFillSeries,
        grid: &TableGrid,
        limits: TableAutoFillLimits,
    ) -> Result<Self, TableAutoFillError> {
        if draft.schema_version != TABLE_AUTO_FILL_SCHEMA_VERSION {
            return Err(TableAutoFillError::UnsupportedRequestVersion);
        }
        series.validate_for_limits(limits)?;
        validate_digest(&draft.series_sha256)?;
        let actual_series_sha256 = hex(series.canonical_sha256(limits)?);
        if draft.series_id != *series.series_id() || draft.series_sha256 != actual_series_sha256 {
            return Err(TableAutoFillError::SeriesBindingMismatch);
        }
        let expected_cells = validate_region(draft.region, grid, limits)?;
        let work = u64::try_from(expected_cells).map_err(|_| TableAutoFillError::WorkLimit)?;
        if work > limits.0.generation_work {
            return Err(TableAutoFillError::WorkLimit);
        }
        let TableAutoFillRequestDraft {
            table_id,
            region,
            order,
            series_id,
            series_sha256,
            start_index,
            formula_policy,
            mut cells,
            ..
        } = draft;
        if cells.len() != expected_cells {
            return Err(TableAutoFillError::CellSetMismatch);
        }
        cells.sort_by_key(|cell| cell.coordinate);
        if cells
            .windows(2)
            .any(|pair| pair[0].coordinate == pair[1].coordinate)
        {
            return Err(TableAutoFillError::CellSetMismatch);
        }
        let mut cursor = 0_usize;
        for row in region.start.row..=region.end.row {
            for column in region.start.column..=region.end.column {
                let cell = cells
                    .get_mut(cursor)
                    .ok_or(TableAutoFillError::CellSetMismatch)?;
                if cell.coordinate != (CellCoordinate { row, column }) {
                    return Err(TableAutoFillError::CellSetMismatch);
                }
                validate_digest(&cell.payload_sha256)?;
                validate_digest(&cell.style_sha256)?;
                if let Some(formula_sha256) = &cell.formula_sha256 {
                    validate_digest(formula_sha256)?;
                    if formula_policy == TableAutoFillFormulaPolicy::Reject {
                        return Err(TableAutoFillError::FormulaPresent);
                    }
                }
                normalize_value(&mut cell.current_value);
                validate_value(&cell.current_value, limits)?;
                cursor = cursor
                    .checked_add(1)
                    .ok_or(TableAutoFillError::SelectionLimit)?;
            }
        }
        let grid_sha256 = hex(grid
            .canonical_sha256()
            .map_err(|_| TableAutoFillError::GridMismatch)?);
        let request = Self {
            schema_version: TABLE_AUTO_FILL_SCHEMA_VERSION,
            capability_id: TABLE_AUTO_FILL_CAPABILITY_ID,
            table_id,
            grid_sha256,
            region,
            order,
            series_id,
            series_sha256,
            start_index,
            formula_policy,
            cells,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and validates it against the exact series and table grid.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and semantic
    /// failures reported by [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        series: &TableAutoFillSeries,
        grid: &TableGrid,
        limits: TableAutoFillLimits,
    ) -> Result<Self, TableAutoFillError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TableAutoFillError::InvalidJson)?;
        Self::from_draft(draft, series, grid, limits)
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
    pub fn grid_sha256(&self) -> &str {
        &self.grid_sha256
    }

    #[must_use]
    pub const fn region(&self) -> TableAutoFillRegion {
        self.region
    }

    #[must_use]
    pub const fn order(&self) -> TableAutoFillOrder {
        self.order
    }

    #[must_use]
    pub const fn series_id(&self) -> &LogicalId {
        &self.series_id
    }

    #[must_use]
    pub fn series_sha256(&self) -> &str {
        &self.series_sha256
    }

    #[must_use]
    pub const fn start_index(&self) -> u64 {
        self.start_index
    }

    #[must_use]
    pub const fn formula_policy(&self) -> TableAutoFillFormulaPolicy {
        self.formula_policy
    }

    /// Serializes the complete validated request under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(
        &self,
        limits: TableAutoFillLimits,
    ) -> Result<Vec<u8>, TableAutoFillError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over bounded canonical request JSON.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableAutoFillLimits,
    ) -> Result<[u8; 32], TableAutoFillError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAutoFillRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("region", &self.region)
            .field("order", &self.order)
            .field("series_id", &"<redacted>")
            .field("series_sha256", &"<redacted>")
            .field("start_index", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAutoFillMutation {
    coordinate: CellCoordinate,
    sequence_index: u64,
    prior_payload_sha256: String,
    prior_formula_sha256: Option<String>,
    preserved_style_sha256: String,
    generated_value: TableAutoFillValue,
    clear_formula: bool,
}

impl TableAutoFillMutation {
    #[must_use]
    pub const fn coordinate(&self) -> CellCoordinate {
        self.coordinate
    }

    #[must_use]
    pub const fn sequence_index(&self) -> u64 {
        self.sequence_index
    }

    #[must_use]
    pub fn prior_payload_sha256(&self) -> &str {
        &self.prior_payload_sha256
    }

    #[must_use]
    pub fn prior_formula_sha256(&self) -> Option<&str> {
        self.prior_formula_sha256.as_deref()
    }

    #[must_use]
    pub fn preserved_style_sha256(&self) -> &str {
        &self.preserved_style_sha256
    }

    #[must_use]
    pub const fn generated_value(&self) -> &TableAutoFillValue {
        &self.generated_value
    }

    #[must_use]
    pub const fn clear_formula(&self) -> bool {
        self.clear_formula
    }
}

impl fmt::Debug for TableAutoFillMutation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillMutation")
            .field("coordinate", &self.coordinate)
            .field("sequence_index", &"<redacted>")
            .field("prior_payload_sha256", &"<redacted>")
            .field(
                "prior_formula_sha256",
                &self.prior_formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("preserved_style_sha256", &"<redacted>")
            .field("generated_value", &self.generated_value)
            .field("clear_formula", &self.clear_formula)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAutoFillReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    series_sha256: String,
    request_sha256: String,
    mutation_sha256: String,
    formula_policy: TableAutoFillFormulaPolicy,
    semantic_change_count: usize,
}

impl TableAutoFillReceipt {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
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
    pub fn series_sha256(&self) -> &str {
        &self.series_sha256
    }

    #[must_use]
    pub fn request_sha256(&self) -> &str {
        &self.request_sha256
    }

    #[must_use]
    pub fn mutation_sha256(&self) -> &str {
        &self.mutation_sha256
    }

    #[must_use]
    pub const fn formula_policy(&self) -> TableAutoFillFormulaPolicy {
        self.formula_policy
    }

    #[must_use]
    pub const fn semantic_change_count(&self) -> usize {
        self.semantic_change_count
    }

    /// Serializes the receipt under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(
        &self,
        limits: TableAutoFillLimits,
    ) -> Result<Vec<u8>, TableAutoFillError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for TableAutoFillReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("series_sha256", &"<redacted>")
            .field("request_sha256", &"<redacted>")
            .field("mutation_sha256", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .field("semantic_change_count", &self.semantic_change_count)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableAutoFillPlan {
    schema_version: &'static str,
    request: TableAutoFillRequest,
    mutations: Vec<TableAutoFillMutation>,
    receipt: TableAutoFillReceipt,
}

impl TableAutoFillPlan {
    #[must_use]
    pub const fn request(&self) -> &TableAutoFillRequest {
        &self.request
    }

    #[must_use]
    pub fn mutations(&self) -> &[TableAutoFillMutation] {
        &self.mutations
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableAutoFillReceipt {
        &self.receipt
    }

    /// Serializes the complete plan under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the configured bound.
    pub fn canonical_json(
        &self,
        limits: TableAutoFillLimits,
    ) -> Result<Vec<u8>, TableAutoFillError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over bounded canonical plan JSON.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableAutoFillLimits,
    ) -> Result<[u8; 32], TableAutoFillError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableAutoFillPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableAutoFillPlan")
            .field("schema_version", &self.schema_version)
            .field("request", &self.request)
            .field("mutation_count", &self.mutations.len())
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableAutoFillBuilder;

impl TableAutoFillBuilder {
    /// Builds a deterministic, coordinate-canonical and atomic scalar fill plan.
    ///
    /// # Errors
    ///
    /// Rejects generation overflow or output beyond the configured bound. No partial plan is
    /// returned.
    pub fn build(
        request: TableAutoFillRequest,
        series: &TableAutoFillSeries,
        limits: TableAutoFillLimits,
    ) -> Result<TableAutoFillPlan, TableAutoFillError> {
        series.validate_for_limits(limits)?;
        if request.series_id != *series.series_id()
            || request.series_sha256 != hex(series.canonical_sha256(limits)?)
        {
            return Err(TableAutoFillError::SeriesBindingMismatch);
        }
        let cells_by_coordinate: BTreeMap<_, _> = request
            .cells
            .iter()
            .map(|cell| (cell.coordinate, cell))
            .collect();
        let row_count = request.region.end.row - request.region.start.row + 1;
        let column_count = request.region.end.column - request.region.start.column + 1;
        let cell_count = u64::from(row_count)
            .checked_mul(u64::from(column_count))
            .ok_or(TableAutoFillError::SelectionLimit)?;
        let mut mutations = Vec::with_capacity(request.cells.len());
        let mut semantic_change_count = 0_usize;
        for ordinal in 0..cell_count {
            let coordinate = coordinate_at(&request, ordinal, row_count, column_count)?;
            let sequence_index = request
                .start_index
                .checked_add(ordinal)
                .ok_or(TableAutoFillError::GenerationOverflow)?;
            let generated_value = series.value_at(sequence_index)?;
            let cell = cells_by_coordinate
                .get(&coordinate)
                .ok_or(TableAutoFillError::CellSetMismatch)?;
            let clear_formula = cell.formula_sha256.is_some();
            if cell.current_value != generated_value || clear_formula {
                semantic_change_count = semantic_change_count
                    .checked_add(1)
                    .ok_or(TableAutoFillError::SelectionLimit)?;
            }
            mutations.push(TableAutoFillMutation {
                coordinate,
                sequence_index,
                prior_payload_sha256: cell.payload_sha256.clone(),
                prior_formula_sha256: cell.formula_sha256.clone(),
                preserved_style_sha256: cell.style_sha256.clone(),
                generated_value,
                clear_formula,
            });
        }
        mutations.sort_by_key(|mutation| mutation.coordinate);
        let request_sha256 = hex(request.canonical_sha256(limits)?);
        let mutation_sha256 =
            hex(Sha256::digest(serialize_bounded(&mutations, limits.0.serialized_bytes)?).into());
        let receipt = TableAutoFillReceipt {
            schema_version: TABLE_AUTO_FILL_SCHEMA_VERSION,
            capability_id: TABLE_AUTO_FILL_CAPABILITY_ID,
            table_id: request.table_id.clone(),
            grid_sha256: request.grid_sha256.clone(),
            series_sha256: request.series_sha256.clone(),
            request_sha256,
            mutation_sha256,
            formula_policy: request.formula_policy,
            semantic_change_count,
        };
        let _ = receipt.canonical_json(limits)?;
        let plan = TableAutoFillPlan {
            schema_version: TABLE_AUTO_FILL_SCHEMA_VERSION,
            request,
            mutations,
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableAutoFillError {
    #[error("table auto-fill limits are invalid")]
    InvalidLimit,
    #[error("table auto-fill series schema version is unsupported")]
    UnsupportedSeriesVersion,
    #[error("table auto-fill request schema version is unsupported")]
    UnsupportedRequestVersion,
    #[error("table auto-fill JSON input is empty or oversized")]
    InputLimit,
    #[error("table auto-fill JSON is invalid")]
    InvalidJson,
    #[error("table auto-fill series is empty or oversized")]
    SeriesItemLimit,
    #[error("table auto-fill scalar value is invalid or oversized")]
    ValueInvalid,
    #[error("table auto-fill series binding does not match")]
    SeriesBindingMismatch,
    #[error("table auto-fill region is reversed")]
    RegionOrder,
    #[error("table auto-fill region is outside the supplied grid")]
    RegionOutOfBounds,
    #[error("table auto-fill selection exceeds its configured bound")]
    SelectionLimit,
    #[error("table auto-fill region contains a merged cell")]
    MergedCell,
    #[error("table auto-fill grid cannot be bound canonically")]
    GridMismatch,
    #[error("table auto-fill cell set does not exactly cover the selected region")]
    CellSetMismatch,
    #[error("table auto-fill payload, formula or style digest is invalid")]
    DigestInvalid,
    #[error("table auto-fill formula policy rejects a selected formula cell")]
    FormulaPresent,
    #[error("table auto-fill generation work exceeds its configured bound")]
    WorkLimit,
    #[error("table auto-fill series generation overflowed")]
    GenerationOverflow,
    #[error("table auto-fill output exceeds its configured bound")]
    OutputLimit,
    #[error("table auto-fill serialization failed")]
    Serialization,
}

impl TableAutoFillError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_auto_fill_invalid_limit",
            Self::UnsupportedSeriesVersion => "table_auto_fill_unsupported_series_version",
            Self::UnsupportedRequestVersion => "table_auto_fill_unsupported_request_version",
            Self::InputLimit => "table_auto_fill_input_limit",
            Self::InvalidJson => "table_auto_fill_invalid_json",
            Self::SeriesItemLimit => "table_auto_fill_series_item_limit",
            Self::ValueInvalid => "table_auto_fill_value_invalid",
            Self::SeriesBindingMismatch => "table_auto_fill_series_binding_mismatch",
            Self::RegionOrder => "table_auto_fill_region_order",
            Self::RegionOutOfBounds => "table_auto_fill_region_out_of_bounds",
            Self::SelectionLimit => "table_auto_fill_selection_limit",
            Self::MergedCell => "table_auto_fill_merged_cell",
            Self::GridMismatch => "table_auto_fill_grid_mismatch",
            Self::CellSetMismatch => "table_auto_fill_cell_set_mismatch",
            Self::DigestInvalid => "table_auto_fill_digest_invalid",
            Self::FormulaPresent => "table_auto_fill_formula_present",
            Self::WorkLimit => "table_auto_fill_work_limit",
            Self::GenerationOverflow => "table_auto_fill_generation_overflow",
            Self::OutputLimit => "table_auto_fill_output_limit",
            Self::Serialization => "table_auto_fill_serialization",
        }
    }
}

fn validate_input(bytes: &[u8], limits: TableAutoFillLimits) -> Result<(), TableAutoFillError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(TableAutoFillError::InputLimit);
    }
    Ok(())
}

fn validate_definition(
    definition: &mut TableAutoFillDefinition,
    limits: TableAutoFillLimits,
) -> Result<(), TableAutoFillError> {
    match definition {
        TableAutoFillDefinition::ExplicitCycle { items } => {
            if items.is_empty() || items.len() > limits.0.series_items {
                return Err(TableAutoFillError::SeriesItemLimit);
            }
            let mut total_text_bytes = 0_usize;
            for item in items {
                normalize_value(item);
                validate_value(item, limits)?;
                if let TableAutoFillValue::Text { value } = item {
                    total_text_bytes = total_text_bytes
                        .checked_add(value.len())
                        .ok_or(TableAutoFillError::ValueInvalid)?;
                    if total_text_bytes > limits.0.total_text_bytes {
                        return Err(TableAutoFillError::ValueInvalid);
                    }
                }
            }
            Ok(())
        }
        TableAutoFillDefinition::LinearNumber { start, step } => {
            normalize_number(start)?;
            normalize_number(step)
        }
        TableAutoFillDefinition::LinearDateDays { .. } => Ok(()),
    }
}

fn validate_region(
    region: TableAutoFillRegion,
    grid: &TableGrid,
    limits: TableAutoFillLimits,
) -> Result<usize, TableAutoFillError> {
    if region.start.row > region.end.row || region.start.column > region.end.column {
        return Err(TableAutoFillError::RegionOrder);
    }
    if region.end.row >= grid.rows() || region.end.column >= grid.columns() {
        return Err(TableAutoFillError::RegionOutOfBounds);
    }
    let rows = usize::try_from(region.end.row - region.start.row + 1)
        .map_err(|_| TableAutoFillError::SelectionLimit)?;
    let columns = usize::try_from(region.end.column - region.start.column + 1)
        .map_err(|_| TableAutoFillError::SelectionLimit)?;
    let selected_cells = rows
        .checked_mul(columns)
        .ok_or(TableAutoFillError::SelectionLimit)?;
    if selected_cells > limits.0.selected_cells {
        return Err(TableAutoFillError::SelectionLimit);
    }
    for row in region.start.row..=region.end.row {
        for column in region.start.column..=region.end.column {
            let master = grid
                .master_cell_at(CellCoordinate { row, column })
                .map_err(|_| TableAutoFillError::GridMismatch)?;
            if master.row != row
                || master.column != column
                || master.row_span != 1
                || master.column_span != 1
            {
                return Err(TableAutoFillError::MergedCell);
            }
        }
    }
    Ok(selected_cells)
}

fn validate_value(
    value: &TableAutoFillValue,
    limits: TableAutoFillLimits,
) -> Result<(), TableAutoFillError> {
    match value {
        TableAutoFillValue::Decimal { scale, .. } if *scale > 18 => {
            Err(TableAutoFillError::ValueInvalid)
        }
        TableAutoFillValue::Text { value }
            if value.len() > limits.0.text_bytes
                || value.chars().any(|character| character == '\0') =>
        {
            Err(TableAutoFillError::ValueInvalid)
        }
        _ => Ok(()),
    }
}

fn normalize_value(value: &mut TableAutoFillValue) {
    let TableAutoFillValue::Decimal { coefficient, scale } = value else {
        return;
    };
    while *scale > 0 && *coefficient % 10 == 0 {
        *coefficient /= 10;
        *scale -= 1;
    }
    if *scale == 0 {
        *value = TableAutoFillValue::Integer {
            value: *coefficient,
        };
    }
}

fn normalize_number(number: &mut TableAutoFillNumber) -> Result<(), TableAutoFillError> {
    if number.scale > 18 {
        return Err(TableAutoFillError::ValueInvalid);
    }
    while number.scale > 0 && number.coefficient % 10 == 0 {
        number.coefficient /= 10;
        number.scale -= 1;
    }
    Ok(())
}

fn generate_number(
    start: TableAutoFillNumber,
    step: TableAutoFillNumber,
    index: u64,
) -> Result<TableAutoFillValue, TableAutoFillError> {
    let common_scale = start.scale.max(step.scale);
    let start = i128::from(start.coefficient)
        .checked_mul(10_i128.pow(u32::from(common_scale - start.scale)))
        .ok_or(TableAutoFillError::GenerationOverflow)?;
    let step = i128::from(step.coefficient)
        .checked_mul(10_i128.pow(u32::from(common_scale - step.scale)))
        .ok_or(TableAutoFillError::GenerationOverflow)?;
    let mut coefficient = step
        .checked_mul(i128::from(index))
        .and_then(|offset| start.checked_add(offset))
        .ok_or(TableAutoFillError::GenerationOverflow)?;
    let mut scale = common_scale;
    while scale > 0 && coefficient % 10 == 0 {
        coefficient /= 10;
        scale -= 1;
    }
    let coefficient =
        i64::try_from(coefficient).map_err(|_| TableAutoFillError::GenerationOverflow)?;
    if scale == 0 {
        Ok(TableAutoFillValue::Integer { value: coefficient })
    } else {
        Ok(TableAutoFillValue::Decimal { coefficient, scale })
    }
}

fn coordinate_at(
    request: &TableAutoFillRequest,
    ordinal: u64,
    row_count: u32,
    column_count: u32,
) -> Result<CellCoordinate, TableAutoFillError> {
    let (row_offset, column_offset) = match request.order {
        TableAutoFillOrder::RowMajor => (
            ordinal / u64::from(column_count),
            ordinal % u64::from(column_count),
        ),
        TableAutoFillOrder::ColumnMajor => (
            ordinal % u64::from(row_count),
            ordinal / u64::from(row_count),
        ),
    };
    let row = request
        .region
        .start
        .row
        .checked_add(u32::try_from(row_offset).map_err(|_| TableAutoFillError::SelectionLimit)?)
        .ok_or(TableAutoFillError::SelectionLimit)?;
    let column = request
        .region
        .start
        .column
        .checked_add(u32::try_from(column_offset).map_err(|_| TableAutoFillError::SelectionLimit)?)
        .ok_or(TableAutoFillError::SelectionLimit)?;
    Ok(CellCoordinate { row, column })
}

fn validate_digest(value: &str) -> Result<(), TableAutoFillError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableAutoFillError::DigestInvalid);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableAutoFillError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableAutoFillError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableAutoFillError::OutputLimit);
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
