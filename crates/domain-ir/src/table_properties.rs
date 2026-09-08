use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{CellCoordinate, LogicalId, TableCellSpan, TableGrid};

pub const TABLE_PROPERTIES_SCHEMA_VERSION: &str = "hwpx-agent.table-properties/v1";
pub const TABLE_PROPERTIES_CAPABILITY_ID: &str = "table.properties";
pub const TABLE_CELL_BORDER_EACH_CAPABILITY_ID: &str = "table.cell_border_each";
pub const TABLE_CELL_BORDER_UNIFIED_CAPABILITY_ID: &str = "table.cell_border_unified";
pub const TABLE_CELL_DIAGONAL_CAPABILITY_ID: &str = "table.cell_diagonal";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TablePropertiesLimitConfig {
    pub input_bytes: usize,
    pub master_cells: usize,
    pub selected_slots: usize,
    pub identifier_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for TablePropertiesLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 16 * 1024 * 1024,
            master_cells: 1_000_000,
            selected_slots: 1_000_000,
            identifier_bytes: 256,
            serialized_bytes: 128 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TablePropertiesLimits(TablePropertiesLimitConfig);

impl TablePropertiesLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_MASTER_CELLS: usize = 1_000_000;
    pub const HARD_MAX_SELECTED_SLOTS: usize = 4_000_000;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 1_024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite bounds for table-property admission and planning.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling, or internally inconsistent bounds.
    pub fn new(config: TablePropertiesLimitConfig) -> Result<Self, TablePropertiesError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.master_cells == 0
            || config.master_cells > Self::HARD_MAX_MASTER_CELLS
            || config.selected_slots == 0
            || config.selected_slots > Self::HARD_MAX_SELECTED_SLOTS
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TablePropertiesError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TablePropertiesLimitConfig {
        self.0
    }
}

/// One optional digest mutation. `Clear` is distinct from an omitted (`Preserve`) mutation.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum TablePropertyDigestPatch {
    Preserve,
    Clear,
    Set { sha256: String },
}

impl TablePropertyDigestPatch {
    fn apply(&self, current: Option<&String>) -> Option<String> {
        match self {
            Self::Preserve => current.cloned(),
            Self::Clear => None,
            Self::Set { sha256 } => Some(sha256.clone()),
        }
    }

    const fn is_preserve(&self) -> bool {
        matches!(self, Self::Preserve)
    }
}

impl fmt::Debug for TablePropertyDigestPatch {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Preserve => formatter.write_str("Preserve"),
            Self::Clear => formatter.write_str("Clear"),
            Self::Set { .. } => formatter
                .debug_struct("Set")
                .field("sha256", &"<redacted>")
                .finish(),
        }
    }
}

/// Exact semantic identities for the four non-diagonal edges of one master cell.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCellBorderState {
    pub top_sha256: Option<String>,
    pub right_sha256: Option<String>,
    pub bottom_sha256: Option<String>,
    pub left_sha256: Option<String>,
}

impl fmt::Debug for TableCellBorderState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCellBorderState")
            .field(
                "top_sha256",
                &self.top_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "right_sha256",
                &self.right_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "bottom_sha256",
                &self.bottom_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "left_sha256",
                &self.left_sha256.as_ref().map(|_| "<redacted>"),
            )
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCellBorderPatch {
    pub top: TablePropertyDigestPatch,
    pub right: TablePropertyDigestPatch,
    pub bottom: TablePropertyDigestPatch,
    pub left: TablePropertyDigestPatch,
}

impl TableCellBorderPatch {
    const fn is_noop(&self) -> bool {
        self.top.is_preserve()
            && self.right.is_preserve()
            && self.bottom.is_preserve()
            && self.left.is_preserve()
    }
}

impl fmt::Debug for TableCellBorderPatch {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCellBorderPatch")
            .field("top", &self.top)
            .field("right", &self.right)
            .field("bottom", &self.bottom)
            .field("left", &self.left)
            .finish()
    }
}

/// A selection-level frame: four outer sides plus the two internal grid-line classes.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableUnifiedBorderPatch {
    pub outer_top: TablePropertyDigestPatch,
    pub outer_right: TablePropertyDigestPatch,
    pub outer_bottom: TablePropertyDigestPatch,
    pub outer_left: TablePropertyDigestPatch,
    pub inner_horizontal: TablePropertyDigestPatch,
    pub inner_vertical: TablePropertyDigestPatch,
}

impl TableUnifiedBorderPatch {
    const fn is_noop(&self) -> bool {
        self.outer_top.is_preserve()
            && self.outer_right.is_preserve()
            && self.outer_bottom.is_preserve()
            && self.outer_left.is_preserve()
            && self.inner_horizontal.is_preserve()
            && self.inner_vertical.is_preserve()
    }
}

impl fmt::Debug for TableUnifiedBorderPatch {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableUnifiedBorderPatch")
            .field("outer_top", &self.outer_top)
            .field("outer_right", &self.outer_right)
            .field("outer_bottom", &self.outer_bottom)
            .field("outer_left", &self.outer_left)
            .field("inner_horizontal", &self.inner_horizontal)
            .field("inner_vertical", &self.inner_vertical)
            .finish()
    }
}

/// Whether a diagonal is repeated in each selected cell or spans one rectangular selection.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableDiagonalApplyMode {
    EachCell,
    Unified,
}

/// OWPML slash topology. `None` disables the corresponding slash direction.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableDiagonalSlashType {
    None,
    Center,
    CenterBelow,
    CenterAbove,
    All,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableDiagonalSlash {
    pub slash_type: TableDiagonalSlashType,
    pub crooked: bool,
    pub is_counter: bool,
}

/// Optional horizontal/vertical center lines from the same OWPML border-fill facet.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableDiagonalCenterLine {
    None,
    Horizontal,
    Vertical,
    Cross,
}

/// Complete semantic value for one diagonal operation.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableDiagonalValue {
    pub slash: TableDiagonalSlash,
    pub back_slash: TableDiagonalSlash,
    pub center_line: TableDiagonalCenterLine,
    /// Identity of the validated line type, width, and color tuple.
    pub line_sha256: String,
}

impl fmt::Debug for TableDiagonalValue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableDiagonalValue")
            .field("slash", &self.slash)
            .field("back_slash", &self.back_slash)
            .field("center_line", &self.center_line)
            .field("line_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum TableDiagonalPatch {
    Clear,
    Set { value: TableDiagonalValue },
}

impl fmt::Debug for TableDiagonalPatch {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Clear => formatter.write_str("Clear"),
            Self::Set { value } => formatter.debug_tuple("Set").field(value).finish(),
        }
    }
}

/// Complete mutable property facets for one cell, excluding content and formula payloads.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCellPropertyValue {
    pub non_border_properties_sha256: String,
    pub borders: TableCellBorderState,
    pub background_sha256: Option<String>,
    pub diagonal_sha256: Option<String>,
}

impl fmt::Debug for TableCellPropertyValue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCellPropertyValue")
            .field("non_border_properties_sha256", &"<redacted>")
            .field("borders", &self.borders)
            .field(
                "background_sha256",
                &self.background_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "diagonal_sha256",
                &self.diagonal_sha256.as_ref().map(|_| "<redacted>"),
            )
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCellPropertyDraft {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub payload_sha256: String,
    pub formula_sha256: Option<String>,
    pub properties: TableCellPropertyValue,
}

impl fmt::Debug for TableCellPropertyDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCellPropertyDraft")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("payload_sha256", &"<redacted>")
            .field(
                "formula_sha256",
                &self.formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("properties", &self.properties)
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePropertiesStateDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub grid_sha256: String,
    pub table_properties_sha256: String,
    pub cells: Vec<TableCellPropertyDraft>,
}

impl fmt::Debug for TablePropertiesStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePropertiesStateDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePropertiesState {
    schema_version: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    table_properties_sha256: String,
    cells: Vec<TableCellPropertyDraft>,
}

impl TablePropertiesState {
    /// Validates a complete property snapshot against every master cell in an exact grid.
    ///
    /// # Errors
    ///
    /// Rejects version, identity, digest, finite-limit, grid, duplicate, missing, extra, or
    /// coordinate drift.
    pub fn from_draft(
        draft: TablePropertiesStateDraft,
        grid: &TableGrid,
        limits: TablePropertiesLimits,
    ) -> Result<Self, TablePropertiesError> {
        let TablePropertiesStateDraft {
            schema_version,
            table_id,
            grid_sha256,
            table_properties_sha256,
            mut cells,
        } = draft;
        if schema_version != TABLE_PROPERTIES_SCHEMA_VERSION {
            return Err(TablePropertiesError::UnsupportedVersion);
        }
        validate_identifier(&table_id, limits)?;
        validate_digest(&grid_sha256)?;
        validate_digest(&table_properties_sha256)?;
        if grid_sha256 != grid_digest(grid)? {
            return Err(TablePropertiesError::GridMismatch);
        }
        if cells.len() != grid.master_cell_count() || cells.len() > limits.0.master_cells {
            return Err(TablePropertiesError::CellSetMismatch);
        }
        cells.sort_by(|left, right| {
            (left.coordinate, &left.master_cell_id).cmp(&(right.coordinate, &right.master_cell_id))
        });
        if cells.windows(2).any(|pair| {
            pair[0].coordinate == pair[1].coordinate
                || pair[0].master_cell_id == pair[1].master_cell_id
        }) {
            return Err(TablePropertiesError::CellSetMismatch);
        }
        for (cell, span) in cells.iter().zip(grid.master_cells()) {
            if cell.master_cell_id != span.master_cell_id
                || cell.coordinate
                    != (CellCoordinate {
                        row: span.row,
                        column: span.column,
                    })
            {
                return Err(TablePropertiesError::CellSetMismatch);
            }
            validate_identifier(&cell.master_cell_id, limits)?;
            validate_digest(&cell.payload_sha256)?;
            validate_optional_digest(cell.formula_sha256.as_deref())?;
            validate_property_value(&cell.properties)?;
        }
        let state = Self {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION,
            table_id,
            grid_sha256,
            table_properties_sha256,
            cells,
        };
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    /// Parses strict bounded JSON and validates the complete snapshot against an exact grid.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and every failure
    /// reported by [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        grid: &TableGrid,
        limits: TablePropertiesLimits,
    ) -> Result<Self, TablePropertiesError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TablePropertiesError::InvalidJson)?;
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
    pub fn table_properties_sha256(&self) -> &str {
        &self.table_properties_sha256
    }

    #[must_use]
    pub fn cells(&self) -> &[TableCellPropertyDraft] {
        &self.cells
    }

    /// Serializes the canonical complete state under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the finite bound.
    pub fn canonical_json(
        &self,
        limits: TablePropertiesLimits,
    ) -> Result<Vec<u8>, TablePropertiesError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical state.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TablePropertiesLimits,
    ) -> Result<[u8; 32], TablePropertiesError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TablePropertiesState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePropertiesState")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum TablePropertiesOperation {
    SetProperties {
        table_properties_sha256: Option<String>,
        cell_properties_sha256: Option<String>,
    },
    BorderEach {
        border: TableCellBorderPatch,
        background: TablePropertyDigestPatch,
    },
    BorderUnified {
        border: TableUnifiedBorderPatch,
        background: TablePropertyDigestPatch,
    },
    CellDiagonal {
        apply_mode: TableDiagonalApplyMode,
        patch: TableDiagonalPatch,
    },
}

impl TablePropertiesOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::SetProperties { .. } => TABLE_PROPERTIES_CAPABILITY_ID,
            Self::BorderEach { .. } => TABLE_CELL_BORDER_EACH_CAPABILITY_ID,
            Self::BorderUnified { .. } => TABLE_CELL_BORDER_UNIFIED_CAPABILITY_ID,
            Self::CellDiagonal { .. } => TABLE_CELL_DIAGONAL_CAPABILITY_ID,
        }
    }
}

impl fmt::Debug for TablePropertiesOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::SetProperties {
                table_properties_sha256,
                cell_properties_sha256,
            } => formatter
                .debug_struct("SetProperties")
                .field(
                    "table_properties_sha256",
                    &table_properties_sha256.as_ref().map(|_| "<redacted>"),
                )
                .field(
                    "cell_properties_sha256",
                    &cell_properties_sha256.as_ref().map(|_| "<redacted>"),
                )
                .finish(),
            Self::BorderEach { border, background } => formatter
                .debug_struct("BorderEach")
                .field("border", border)
                .field("background", background)
                .finish(),
            Self::BorderUnified { border, background } => formatter
                .debug_struct("BorderUnified")
                .field("border", border)
                .field("background", background)
                .finish(),
            Self::CellDiagonal { apply_mode, patch } => formatter
                .debug_struct("CellDiagonal")
                .field("apply_mode", apply_mode)
                .field("patch", patch)
                .finish(),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct TablePropertyRegion {
    row: u32,
    column: u32,
    row_span: u32,
    column_span: u32,
}

impl TablePropertyRegion {
    /// Creates one non-empty bounded rectangular property region.
    ///
    /// # Errors
    ///
    /// Rejects zero spans and coordinate overflow. Grid containment remains the responsibility of
    /// the request validator that owns the exact [`TableGrid`].
    pub fn new(
        row: u32,
        column: u32,
        row_span: u32,
        column_span: u32,
    ) -> Result<Self, TablePropertiesError> {
        if row_span == 0
            || column_span == 0
            || row.checked_add(row_span).is_none()
            || column.checked_add(column_span).is_none()
        {
            return Err(TablePropertiesError::DimensionOverflow);
        }
        Ok(Self {
            row,
            column,
            row_span,
            column_span,
        })
    }

    #[must_use]
    pub const fn row(self) -> u32 {
        self.row
    }

    #[must_use]
    pub const fn column(self) -> u32 {
        self.column
    }

    #[must_use]
    pub const fn row_span(self) -> u32 {
        self.row_span
    }

    #[must_use]
    pub const fn column_span(self) -> u32 {
        self.column_span
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TablePropertiesRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub expected_state_sha256: String,
    pub selected_slots: Vec<CellCoordinate>,
    pub operation: TablePropertiesOperation,
}

impl fmt::Debug for TablePropertiesRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePropertiesRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("expected_state_sha256", &"<redacted>")
            .field("selected_slot_count", &self.selected_slots.len())
            .field("operation", &self.operation)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePropertiesRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    expected_state_sha256: String,
    selected_slots: Vec<CellCoordinate>,
    region: Option<TablePropertyRegion>,
    selected_master_cell_count: usize,
    operation: TablePropertiesOperation,
    #[serde(skip)]
    selected_master_indexes: Vec<usize>,
}

impl TablePropertiesRequest {
    /// Validates one exact property operation against a complete state and grid.
    ///
    /// # Errors
    ///
    /// Rejects binding drift, malformed property patches, out-of-bounds slots, non-rectangular
    /// unified selections, partial merged-cell selection, and invalid empty/table-only selections.
    pub fn from_draft(
        draft: TablePropertiesRequestDraft,
        state: &TablePropertiesState,
        grid: &TableGrid,
        limits: TablePropertiesLimits,
    ) -> Result<Self, TablePropertiesError> {
        let TablePropertiesRequestDraft {
            schema_version,
            table_id,
            expected_state_sha256,
            mut selected_slots,
            operation,
        } = draft;
        if schema_version != TABLE_PROPERTIES_SCHEMA_VERSION {
            return Err(TablePropertiesError::UnsupportedVersion);
        }
        validate_identifier(&table_id, limits)?;
        validate_digest(&expected_state_sha256)?;
        let current_grid_sha256 = grid_digest(grid)?;
        let current_state_sha256 = hex(state.canonical_sha256(limits)?);
        if table_id != state.table_id
            || state.grid_sha256 != current_grid_sha256
            || expected_state_sha256 != current_state_sha256
        {
            return Err(TablePropertiesError::StateBindingMismatch);
        }
        validate_operation(&operation)?;

        let cell_selection_required = operation_requires_cells(&operation);
        let (region, selected_master_indexes) = if selected_slots.is_empty() {
            if cell_selection_required {
                return Err(TablePropertiesError::SelectionRequired);
            }
            (None, Vec::new())
        } else {
            if !cell_selection_required {
                return Err(TablePropertiesError::SelectionForbidden);
            }
            validate_selection(
                &mut selected_slots,
                grid,
                operation_requires_rectangle(&operation),
                limits,
            )?
        };
        if selected_master_indexes.len() > limits.0.master_cells {
            return Err(TablePropertiesError::MasterCellLimit);
        }
        let request = Self {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION,
            capability_id: operation.capability_id(),
            table_id,
            grid_sha256: current_grid_sha256,
            expected_state_sha256,
            selected_slots,
            region,
            selected_master_cell_count: selected_master_indexes.len(),
            operation,
            selected_master_indexes,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and validates it against an exact state and grid.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and every failure
    /// reported by [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        state: &TablePropertiesState,
        grid: &TableGrid,
        limits: TablePropertiesLimits,
    ) -> Result<Self, TablePropertiesError> {
        validate_input(bytes, limits)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| TablePropertiesError::InvalidJson)?;
        Self::from_draft(draft, state, grid, limits)
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
    pub const fn region(&self) -> Option<TablePropertyRegion> {
        self.region
    }

    #[must_use]
    pub fn selected_slots(&self) -> &[CellCoordinate] {
        &self.selected_slots
    }

    #[must_use]
    pub const fn selected_master_cell_count(&self) -> usize {
        self.selected_master_cell_count
    }

    #[must_use]
    pub const fn operation(&self) -> &TablePropertiesOperation {
        &self.operation
    }

    /// Serializes the validated request under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the finite bound.
    pub fn canonical_json(
        &self,
        limits: TablePropertiesLimits,
    ) -> Result<Vec<u8>, TablePropertiesError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TablePropertiesLimits,
    ) -> Result<[u8; 32], TablePropertiesError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TablePropertiesRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePropertiesRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("expected_state_sha256", &"<redacted>")
            .field("selected_slot_count", &self.selected_slots.len())
            .field("region", &self.region)
            .field(
                "selected_master_cell_count",
                &self.selected_master_cell_count,
            )
            .field("operation", &self.operation)
            .field(
                "selected_master_indexes",
                &format_args!("{} derived entries", self.selected_master_indexes.len()),
            )
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableBorderEdgeRole {
    PerCell,
    SelectionOuter,
    SelectionInner,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct TableResolvedBorderRoles {
    pub top: TableBorderEdgeRole,
    pub right: TableBorderEdgeRole,
    pub bottom: TableBorderEdgeRole,
    pub left: TableBorderEdgeRole,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableCellPropertyMutation {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub before: TableCellPropertyValue,
    pub after: TableCellPropertyValue,
    pub payload_sha256: String,
    pub formula_sha256: Option<String>,
    pub border_roles: Option<TableResolvedBorderRoles>,
    pub diagonal_apply_mode: Option<TableDiagonalApplyMode>,
}

impl fmt::Debug for TableCellPropertyMutation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableCellPropertyMutation")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("before", &self.before)
            .field("after", &self.after)
            .field("payload_sha256", &"<redacted>")
            .field(
                "formula_sha256",
                &self.formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("border_roles", &self.border_roles)
            .field("diagonal_apply_mode", &self.diagonal_apply_mode)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePropertiesReceipt {
    pub schema_version: &'static str,
    pub capability_id: &'static str,
    pub table_id: LogicalId,
    pub request_sha256: String,
    pub grid_sha256: String,
    pub before_state_sha256: String,
    pub after_state_sha256: String,
    pub before_table_properties_sha256: String,
    pub after_table_properties_sha256: String,
    pub table_properties_changed: bool,
    pub total_master_cell_count: usize,
    pub selected_slot_count: usize,
    pub selected_master_cell_count: usize,
    pub selected_merged_cell_count: usize,
    pub changed_master_cell_count: usize,
    pub unchanged_selected_master_cell_count: usize,
    pub unselected_master_cell_preserved_count: usize,
    pub cell_properties_change_count: usize,
    pub border_side_change_count: usize,
    pub background_change_count: usize,
    pub diagonal_change_count: usize,
    pub diagonal_assignment_count: usize,
    pub per_cell_edge_assignment_count: usize,
    pub outer_edge_assignment_count: usize,
    pub inner_edge_assignment_count: usize,
    pub payload_preserved_count: usize,
    pub formula_preserved_count: usize,
    pub diagonal_preserved_count: usize,
}

impl fmt::Debug for TablePropertiesReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePropertiesReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("request_sha256", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("before_state_sha256", &"<redacted>")
            .field("after_state_sha256", &"<redacted>")
            .field("before_table_properties_sha256", &"<redacted>")
            .field("after_table_properties_sha256", &"<redacted>")
            .field("table_properties_changed", &self.table_properties_changed)
            .field("total_master_cell_count", &self.total_master_cell_count)
            .field("selected_slot_count", &self.selected_slot_count)
            .field(
                "selected_master_cell_count",
                &self.selected_master_cell_count,
            )
            .field(
                "selected_merged_cell_count",
                &self.selected_merged_cell_count,
            )
            .field("changed_master_cell_count", &self.changed_master_cell_count)
            .field(
                "unchanged_selected_master_cell_count",
                &self.unchanged_selected_master_cell_count,
            )
            .field(
                "unselected_master_cell_preserved_count",
                &self.unselected_master_cell_preserved_count,
            )
            .field(
                "cell_properties_change_count",
                &self.cell_properties_change_count,
            )
            .field("border_side_change_count", &self.border_side_change_count)
            .field("background_change_count", &self.background_change_count)
            .field("diagonal_change_count", &self.diagonal_change_count)
            .field("diagonal_assignment_count", &self.diagonal_assignment_count)
            .field(
                "per_cell_edge_assignment_count",
                &self.per_cell_edge_assignment_count,
            )
            .field(
                "outer_edge_assignment_count",
                &self.outer_edge_assignment_count,
            )
            .field(
                "inner_edge_assignment_count",
                &self.inner_edge_assignment_count,
            )
            .field("payload_preserved_count", &self.payload_preserved_count)
            .field("formula_preserved_count", &self.formula_preserved_count)
            .field("diagonal_preserved_count", &self.diagonal_preserved_count)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TablePropertiesPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    operation: TablePropertiesOperation,
    table_properties_sha256: String,
    mutations: Vec<TableCellPropertyMutation>,
    receipt: TablePropertiesReceipt,
}

impl TablePropertiesPlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn operation(&self) -> &TablePropertiesOperation {
        &self.operation
    }

    #[must_use]
    pub fn table_properties_sha256(&self) -> &str {
        &self.table_properties_sha256
    }

    #[must_use]
    pub fn mutations(&self) -> &[TableCellPropertyMutation] {
        &self.mutations
    }

    #[must_use]
    pub const fn receipt(&self) -> &TablePropertiesReceipt {
        &self.receipt
    }

    /// Serializes the complete atomic plan under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the finite bound.
    pub fn canonical_json(
        &self,
        limits: TablePropertiesLimits,
    ) -> Result<Vec<u8>, TablePropertiesError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TablePropertiesLimits,
    ) -> Result<[u8; 32], TablePropertiesError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TablePropertiesPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TablePropertiesPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("operation", &self.operation)
            .field("table_properties_sha256", &"<redacted>")
            .field("mutation_count", &self.mutations.len())
            .field("receipt", &"<redacted>")
            .finish()
    }
}

#[derive(Debug)]
pub struct TablePropertiesBuilder;

impl TablePropertiesBuilder {
    /// Builds a deterministic atomic table/cell property plan without mutating the input state.
    ///
    /// # Errors
    ///
    /// Rejects state/grid/request drift, selection drift, arithmetic overflow, allocation failure,
    /// and bounded output failure. No partial plan or receipt is returned.
    pub fn build(
        request: &TablePropertiesRequest,
        state: &TablePropertiesState,
        grid: &TableGrid,
        limits: TablePropertiesLimits,
    ) -> Result<TablePropertiesPlan, TablePropertiesError> {
        let grid_sha256 = grid_digest(grid)?;
        let before_state_sha256 = hex(state.canonical_sha256(limits)?);
        if request.grid_sha256 != grid_sha256
            || state.grid_sha256 != grid_sha256
            || request.table_id != state.table_id
            || request.expected_state_sha256 != before_state_sha256
            || state.cells.len() != grid.master_cell_count()
        {
            return Err(TablePropertiesError::BindingDrift);
        }

        let (after_cells, mutations, counts) = build_after_cells(request, state, grid, limits)?;

        let after_table_properties_sha256 = match &request.operation {
            TablePropertiesOperation::SetProperties {
                table_properties_sha256: Some(sha256),
                ..
            } => sha256.clone(),
            _ => state.table_properties_sha256.clone(),
        };
        let table_properties_changed =
            after_table_properties_sha256 != state.table_properties_sha256;
        let after_state = TablePropertiesState {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION,
            table_id: state.table_id.clone(),
            grid_sha256: grid_sha256.clone(),
            table_properties_sha256: after_table_properties_sha256.clone(),
            cells: after_cells,
        };
        let after_state_sha256 = hex(after_state.canonical_sha256(limits)?);
        let unselected_master_cell_preserved_count = state
            .cells
            .len()
            .checked_sub(request.selected_master_indexes.len())
            .ok_or(TablePropertiesError::MasterCellLimit)?;
        let formula_preserved_count = state
            .cells
            .iter()
            .filter(|cell| cell.formula_sha256.is_some())
            .count();
        let receipt = TablePropertiesReceipt {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION,
            capability_id: request.capability_id,
            table_id: state.table_id.clone(),
            request_sha256: hex(request.canonical_sha256(limits)?),
            grid_sha256,
            before_state_sha256,
            after_state_sha256,
            before_table_properties_sha256: state.table_properties_sha256.clone(),
            after_table_properties_sha256: after_table_properties_sha256.clone(),
            table_properties_changed,
            total_master_cell_count: state.cells.len(),
            selected_slot_count: request.selected_slots.len(),
            selected_master_cell_count: request.selected_master_indexes.len(),
            selected_merged_cell_count: counts.selected_merged,
            changed_master_cell_count: counts.changed,
            unchanged_selected_master_cell_count: counts.unchanged,
            unselected_master_cell_preserved_count,
            cell_properties_change_count: counts.cell_properties,
            border_side_change_count: counts.border_sides,
            background_change_count: counts.backgrounds,
            diagonal_change_count: counts.diagonals,
            diagonal_assignment_count: counts.diagonal_assignments,
            per_cell_edge_assignment_count: counts.per_cell_assignments,
            outer_edge_assignment_count: counts.outer_assignments,
            inner_edge_assignment_count: counts.inner_assignments,
            payload_preserved_count: state.cells.len(),
            formula_preserved_count,
            diagonal_preserved_count: state
                .cells
                .len()
                .checked_sub(counts.diagonals)
                .ok_or(TablePropertiesError::MasterCellLimit)?,
        };
        let plan = TablePropertiesPlan {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION,
            capability_id: request.capability_id,
            operation: request.operation.clone(),
            table_properties_sha256: after_table_properties_sha256,
            mutations,
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Default)]
struct MutationCounts {
    selected_merged: usize,
    changed: usize,
    unchanged: usize,
    cell_properties: usize,
    border_sides: usize,
    backgrounds: usize,
    diagonals: usize,
    diagonal_assignments: usize,
    per_cell_assignments: usize,
    outer_assignments: usize,
    inner_assignments: usize,
}

enum DiagonalResolution {
    NotTargeted,
    Clear,
    Set(String),
}

#[derive(Serialize)]
struct TableDiagonalIdentity<'a> {
    schema_version: &'static str,
    table_id: &'a LogicalId,
    grid_sha256: &'a str,
    apply_mode: TableDiagonalApplyMode,
    region: Option<TablePropertyRegion>,
    value: &'a TableDiagonalValue,
}

fn resolve_diagonal_identity(
    request: &TablePropertiesRequest,
    limits: TablePropertiesLimits,
) -> Result<DiagonalResolution, TablePropertiesError> {
    let TablePropertiesOperation::CellDiagonal { apply_mode, patch } = &request.operation else {
        return Ok(DiagonalResolution::NotTargeted);
    };
    match patch {
        TableDiagonalPatch::Clear => Ok(DiagonalResolution::Clear),
        TableDiagonalPatch::Set { value } => {
            Ok(DiagonalResolution::Set(table_diagonal_identity_sha256(
                &request.table_id,
                &request.grid_sha256,
                *apply_mode,
                request.region,
                value,
                limits,
            )?))
        }
    }
}

/// Computes the exact logical identity used for a native-validated table diagonal.
///
/// This is exposed for preserving adapters because HWPX stores the visible slash topology but not
/// whether multiple equal diagonals originated from one unified logical selection. The caller must
/// therefore supply the original application mode and region, which are validated and bound into
/// the same digest used by [`TablePropertiesBuilder`].
///
/// # Errors
///
/// Rejects malformed identifiers, grid or line digests, empty diagonal values, mode/region
/// mismatches, invalid regions, allocation failure, or bounded serialization failure.
pub fn table_diagonal_identity_sha256(
    table_id: &LogicalId,
    grid_sha256: &str,
    apply_mode: TableDiagonalApplyMode,
    region: Option<TablePropertyRegion>,
    value: &TableDiagonalValue,
    limits: TablePropertiesLimits,
) -> Result<String, TablePropertiesError> {
    validate_identifier(table_id, limits)?;
    validate_digest(grid_sha256)?;
    validate_diagonal_value(value)?;
    match (apply_mode, region) {
        (TableDiagonalApplyMode::EachCell, None) => {}
        (TableDiagonalApplyMode::Unified, Some(region))
            if region.row_span != 0
                && region.column_span != 0
                && region.row.checked_add(region.row_span).is_some()
                && region.column.checked_add(region.column_span).is_some() => {}
        _ => return Err(TablePropertiesError::BindingDrift),
    }
    let identity = TableDiagonalIdentity {
        schema_version: "hwpx-agent.table-diagonal-identity/v1",
        table_id,
        grid_sha256,
        apply_mode,
        region,
        value,
    };
    let bytes = serialize_bounded(&identity, limits.0.serialized_bytes)?;
    Ok(hex(Sha256::digest(bytes).into()))
}

fn build_after_cells(
    request: &TablePropertiesRequest,
    state: &TablePropertiesState,
    grid: &TableGrid,
    limits: TablePropertiesLimits,
) -> Result<
    (
        Vec<TableCellPropertyDraft>,
        Vec<TableCellPropertyMutation>,
        MutationCounts,
    ),
    TablePropertiesError,
> {
    let diagonal_resolution = resolve_diagonal_identity(request, limits)?;
    let mut after_cells = Vec::new();
    after_cells
        .try_reserve_exact(state.cells.len())
        .map_err(|_| TablePropertiesError::AllocationFailed)?;
    let mut mutations = Vec::new();
    mutations
        .try_reserve_exact(request.selected_master_indexes.len())
        .map_err(|_| TablePropertiesError::AllocationFailed)?;
    let mut selected_cursor = 0_usize;
    let mut counts = MutationCounts::default();
    for (index, (cell, span)) in state.cells.iter().zip(grid.master_cells()).enumerate() {
        if request.selected_master_indexes.get(selected_cursor) != Some(&index) {
            after_cells.push(cell.clone());
            continue;
        }
        let (after, roles, diagonal_apply_mode) = apply_operation(
            &cell.properties,
            span,
            request.region,
            &request.operation,
            &diagonal_resolution,
            &mut counts,
        )?;
        if after == cell.properties {
            counts.unchanged = checked_add(counts.unchanged, 1)?;
        } else {
            counts.changed = checked_add(counts.changed, 1)?;
        }
        if span.row_span != 1 || span.column_span != 1 {
            counts.selected_merged = checked_add(counts.selected_merged, 1)?;
        }
        mutations.push(TableCellPropertyMutation {
            master_cell_id: cell.master_cell_id.clone(),
            coordinate: cell.coordinate,
            before: cell.properties.clone(),
            after: after.clone(),
            payload_sha256: cell.payload_sha256.clone(),
            formula_sha256: cell.formula_sha256.clone(),
            border_roles: roles,
            diagonal_apply_mode,
        });
        after_cells.push(TableCellPropertyDraft {
            master_cell_id: cell.master_cell_id.clone(),
            coordinate: cell.coordinate,
            payload_sha256: cell.payload_sha256.clone(),
            formula_sha256: cell.formula_sha256.clone(),
            properties: after,
        });
        selected_cursor = checked_add(selected_cursor, 1)?;
    }
    if selected_cursor != request.selected_master_indexes.len() {
        return Err(TablePropertiesError::BindingDrift);
    }
    Ok((after_cells, mutations, counts))
}

fn apply_operation(
    before: &TableCellPropertyValue,
    span: &TableCellSpan,
    region: Option<TablePropertyRegion>,
    operation: &TablePropertiesOperation,
    diagonal_resolution: &DiagonalResolution,
    counts: &mut MutationCounts,
) -> Result<
    (
        TableCellPropertyValue,
        Option<TableResolvedBorderRoles>,
        Option<TableDiagonalApplyMode>,
    ),
    TablePropertiesError,
> {
    let mut after = before.clone();
    let (roles, diagonal_apply_mode) = match operation {
        TablePropertiesOperation::SetProperties {
            cell_properties_sha256,
            ..
        } => {
            if let Some(sha256) = cell_properties_sha256
                && after.non_border_properties_sha256 != *sha256
            {
                after.non_border_properties_sha256.clone_from(sha256);
                counts.cell_properties = checked_add(counts.cell_properties, 1)?;
            }
            (None, None)
        }
        TablePropertiesOperation::BorderEach { border, background } => {
            apply_border_patch(&mut after, border, counts)?;
            apply_background_patch(&mut after, background, counts)?;
            counts.per_cell_assignments = checked_add(counts.per_cell_assignments, 4)?;
            (
                Some(TableResolvedBorderRoles {
                    top: TableBorderEdgeRole::PerCell,
                    right: TableBorderEdgeRole::PerCell,
                    bottom: TableBorderEdgeRole::PerCell,
                    left: TableBorderEdgeRole::PerCell,
                }),
                None,
            )
        }
        TablePropertiesOperation::BorderUnified { border, background } => {
            let region = region.ok_or(TablePropertiesError::BindingDrift)?;
            let row_end = checked_end(region.row, region.row_span)?;
            let column_end = checked_end(region.column, region.column_span)?;
            let span_row_end = checked_end(span.row, span.row_span)?;
            let span_column_end = checked_end(span.column, span.column_span)?;
            let top_outer = span.row == region.row;
            let right_outer = span_column_end == column_end;
            let bottom_outer = span_row_end == row_end;
            let left_outer = span.column == region.column;
            let resolved = TableCellBorderPatch {
                top: if top_outer {
                    border.outer_top.clone()
                } else {
                    border.inner_horizontal.clone()
                },
                right: if right_outer {
                    border.outer_right.clone()
                } else {
                    border.inner_vertical.clone()
                },
                bottom: if bottom_outer {
                    border.outer_bottom.clone()
                } else {
                    border.inner_horizontal.clone()
                },
                left: if left_outer {
                    border.outer_left.clone()
                } else {
                    border.inner_vertical.clone()
                },
            };
            apply_border_patch(&mut after, &resolved, counts)?;
            apply_background_patch(&mut after, background, counts)?;
            let roles = TableResolvedBorderRoles {
                top: edge_role(top_outer),
                right: edge_role(right_outer),
                bottom: edge_role(bottom_outer),
                left: edge_role(left_outer),
            };
            for outer in [top_outer, right_outer, bottom_outer, left_outer] {
                if outer {
                    counts.outer_assignments = checked_add(counts.outer_assignments, 1)?;
                } else {
                    counts.inner_assignments = checked_add(counts.inner_assignments, 1)?;
                }
            }
            (Some(roles), None)
        }
        TablePropertiesOperation::CellDiagonal { apply_mode, .. } => {
            let resolved = match diagonal_resolution {
                DiagonalResolution::NotTargeted => return Err(TablePropertiesError::BindingDrift),
                DiagonalResolution::Clear => None,
                DiagonalResolution::Set(sha256) => Some(sha256.clone()),
            };
            if after.diagonal_sha256 != resolved {
                after.diagonal_sha256 = resolved;
                counts.diagonals = checked_add(counts.diagonals, 1)?;
            }
            counts.diagonal_assignments = checked_add(counts.diagonal_assignments, 1)?;
            (None, Some(*apply_mode))
        }
    };
    Ok((after, roles, diagonal_apply_mode))
}

const fn edge_role(outer: bool) -> TableBorderEdgeRole {
    if outer {
        TableBorderEdgeRole::SelectionOuter
    } else {
        TableBorderEdgeRole::SelectionInner
    }
}

fn apply_border_patch(
    value: &mut TableCellPropertyValue,
    patch: &TableCellBorderPatch,
    counts: &mut MutationCounts,
) -> Result<(), TablePropertiesError> {
    apply_digest_patch(
        &mut value.borders.top_sha256,
        &patch.top,
        &mut counts.border_sides,
    )?;
    apply_digest_patch(
        &mut value.borders.right_sha256,
        &patch.right,
        &mut counts.border_sides,
    )?;
    apply_digest_patch(
        &mut value.borders.bottom_sha256,
        &patch.bottom,
        &mut counts.border_sides,
    )?;
    apply_digest_patch(
        &mut value.borders.left_sha256,
        &patch.left,
        &mut counts.border_sides,
    )?;
    Ok(())
}

fn apply_background_patch(
    value: &mut TableCellPropertyValue,
    patch: &TablePropertyDigestPatch,
    counts: &mut MutationCounts,
) -> Result<(), TablePropertiesError> {
    apply_digest_patch(&mut value.background_sha256, patch, &mut counts.backgrounds)
}

fn apply_digest_patch(
    value: &mut Option<String>,
    patch: &TablePropertyDigestPatch,
    count: &mut usize,
) -> Result<(), TablePropertiesError> {
    let after = patch.apply(value.as_ref());
    if *value != after {
        *value = after;
        *count = checked_add(*count, 1)?;
    }
    Ok(())
}

fn validate_operation(operation: &TablePropertiesOperation) -> Result<(), TablePropertiesError> {
    match operation {
        TablePropertiesOperation::SetProperties {
            table_properties_sha256,
            cell_properties_sha256,
        } => {
            validate_optional_digest(table_properties_sha256.as_deref())?;
            validate_optional_digest(cell_properties_sha256.as_deref())?;
            if table_properties_sha256.is_none() && cell_properties_sha256.is_none() {
                return Err(TablePropertiesError::EmptyOperation);
            }
        }
        TablePropertiesOperation::BorderEach { border, background } => {
            validate_border_patch(border)?;
            validate_digest_patch(background)?;
            if border.is_noop() && background.is_preserve() {
                return Err(TablePropertiesError::EmptyOperation);
            }
        }
        TablePropertiesOperation::BorderUnified { border, background } => {
            for patch in [
                &border.outer_top,
                &border.outer_right,
                &border.outer_bottom,
                &border.outer_left,
                &border.inner_horizontal,
                &border.inner_vertical,
            ] {
                validate_digest_patch(patch)?;
            }
            if border.is_noop() && background.is_preserve() {
                return Err(TablePropertiesError::EmptyOperation);
            }
        }
        TablePropertiesOperation::CellDiagonal { patch, .. } => {
            if let TableDiagonalPatch::Set { value } = patch {
                validate_diagonal_value(value)?;
            }
        }
    }
    Ok(())
}

const fn operation_requires_cells(operation: &TablePropertiesOperation) -> bool {
    match operation {
        TablePropertiesOperation::SetProperties {
            cell_properties_sha256,
            ..
        } => cell_properties_sha256.is_some(),
        TablePropertiesOperation::BorderEach { .. }
        | TablePropertiesOperation::BorderUnified { .. }
        | TablePropertiesOperation::CellDiagonal { .. } => true,
    }
}

const fn operation_requires_rectangle(operation: &TablePropertiesOperation) -> bool {
    matches!(
        operation,
        TablePropertiesOperation::BorderUnified { .. }
            | TablePropertiesOperation::CellDiagonal {
                apply_mode: TableDiagonalApplyMode::Unified,
                ..
            }
    )
}

fn validate_diagonal_value(value: &TableDiagonalValue) -> Result<(), TablePropertiesError> {
    validate_digest(&value.line_sha256)?;
    if value.slash.slash_type == TableDiagonalSlashType::None
        && value.back_slash.slash_type == TableDiagonalSlashType::None
        && value.center_line == TableDiagonalCenterLine::None
    {
        return Err(TablePropertiesError::EmptyOperation);
    }
    Ok(())
}

fn validate_border_patch(patch: &TableCellBorderPatch) -> Result<(), TablePropertiesError> {
    for digest_patch in [&patch.top, &patch.right, &patch.bottom, &patch.left] {
        validate_digest_patch(digest_patch)?;
    }
    Ok(())
}

fn validate_digest_patch(patch: &TablePropertyDigestPatch) -> Result<(), TablePropertiesError> {
    if let TablePropertyDigestPatch::Set { sha256 } = patch {
        validate_digest(sha256)?;
    }
    Ok(())
}

fn validate_property_value(value: &TableCellPropertyValue) -> Result<(), TablePropertiesError> {
    validate_digest(&value.non_border_properties_sha256)?;
    validate_optional_digest(value.borders.top_sha256.as_deref())?;
    validate_optional_digest(value.borders.right_sha256.as_deref())?;
    validate_optional_digest(value.borders.bottom_sha256.as_deref())?;
    validate_optional_digest(value.borders.left_sha256.as_deref())?;
    validate_optional_digest(value.background_sha256.as_deref())?;
    validate_optional_digest(value.diagonal_sha256.as_deref())
}

fn validate_selection(
    selected_slots: &mut [CellCoordinate],
    grid: &TableGrid,
    require_rectangle: bool,
    limits: TablePropertiesLimits,
) -> Result<(Option<TablePropertyRegion>, Vec<usize>), TablePropertiesError> {
    if selected_slots.len() > limits.0.selected_slots {
        return Err(TablePropertiesError::SelectionLimit);
    }
    selected_slots.sort_unstable();
    if selected_slots.windows(2).any(|pair| pair[0] == pair[1]) {
        return Err(TablePropertiesError::DuplicateSelectedSlot);
    }
    let first = *selected_slots
        .first()
        .ok_or(TablePropertiesError::SelectionRequired)?;
    let mut first_row = first.row;
    let mut first_column = first.column;
    let mut last_row = first.row;
    let mut last_column = first.column;
    for coordinate in selected_slots.iter().copied() {
        if coordinate.row >= grid.rows() || coordinate.column >= grid.columns() {
            return Err(TablePropertiesError::SelectionOutOfBounds);
        }
        first_row = first_row.min(coordinate.row);
        first_column = first_column.min(coordinate.column);
        last_row = last_row.max(coordinate.row);
        last_column = last_column.max(coordinate.column);
    }
    let row_span = last_row
        .checked_sub(first_row)
        .and_then(|value| value.checked_add(1))
        .ok_or(TablePropertiesError::DimensionOverflow)?;
    let column_span = last_column
        .checked_sub(first_column)
        .and_then(|value| value.checked_add(1))
        .ok_or(TablePropertiesError::DimensionOverflow)?;
    if require_rectangle && checked_product(row_span, column_span)? != selected_slots.len() {
        return Err(TablePropertiesError::NonRectangularSelection);
    }
    let region = TablePropertyRegion {
        row: first_row,
        column: first_column,
        row_span,
        column_span,
    };
    let mut selected_master_indexes = Vec::new();
    selected_master_indexes
        .try_reserve_exact(grid.master_cell_count())
        .map_err(|_| TablePropertiesError::AllocationFailed)?;
    for (index, span) in grid.master_cells().iter().enumerate() {
        let (any_selected, all_selected) = span_selection(span, selected_slots)?;
        if any_selected && !all_selected {
            return Err(TablePropertiesError::MergedSelectionConflict);
        }
        if all_selected {
            selected_master_indexes.push(index);
        }
    }
    if selected_master_indexes.is_empty() {
        return Err(TablePropertiesError::SelectionRequired);
    }
    Ok((require_rectangle.then_some(region), selected_master_indexes))
}

fn span_selection(
    span: &TableCellSpan,
    selected_slots: &[CellCoordinate],
) -> Result<(bool, bool), TablePropertiesError> {
    let span_row_end = checked_end(span.row, span.row_span)?;
    let span_column_end = checked_end(span.column, span.column_span)?;
    let mut any_selected = false;
    let mut all_selected = true;
    for row in span.row..span_row_end {
        for column in span.column..span_column_end {
            let selected = selected_slots
                .binary_search(&CellCoordinate { row, column })
                .is_ok();
            any_selected |= selected;
            all_selected &= selected;
        }
    }
    Ok((any_selected, all_selected))
}

fn grid_digest(grid: &TableGrid) -> Result<String, TablePropertiesError> {
    Ok(hex(grid
        .canonical_sha256()
        .map_err(|_| TablePropertiesError::GridMismatch)?))
}

fn validate_input(bytes: &[u8], limits: TablePropertiesLimits) -> Result<(), TablePropertiesError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(TablePropertiesError::InputLimit);
    }
    Ok(())
}

fn validate_identifier(
    value: &LogicalId,
    limits: TablePropertiesLimits,
) -> Result<(), TablePropertiesError> {
    if value.as_str().len() > limits.0.identifier_bytes {
        return Err(TablePropertiesError::IdentifierLimit);
    }
    Ok(())
}

fn validate_optional_digest(value: Option<&str>) -> Result<(), TablePropertiesError> {
    if let Some(value) = value {
        validate_digest(value)?;
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), TablePropertiesError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TablePropertiesError::DigestInvalid);
    }
    Ok(())
}

fn checked_end(start: u32, span: u32) -> Result<u32, TablePropertiesError> {
    start
        .checked_add(span)
        .ok_or(TablePropertiesError::DimensionOverflow)
}

fn checked_product(left: u32, right: u32) -> Result<usize, TablePropertiesError> {
    let product = u64::from(left)
        .checked_mul(u64::from(right))
        .ok_or(TablePropertiesError::DimensionOverflow)?;
    usize::try_from(product).map_err(|_| TablePropertiesError::DimensionOverflow)
}

fn checked_add(value: usize, increment: usize) -> Result<usize, TablePropertiesError> {
    value
        .checked_add(increment)
        .ok_or(TablePropertiesError::MasterCellLimit)
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TablePropertiesError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TablePropertiesError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TablePropertiesError::OutputLimit);
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

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TablePropertiesError {
    #[error("table property limits are invalid")]
    InvalidLimit,
    #[error("table property schema version is unsupported")]
    UnsupportedVersion,
    #[error("table property JSON input is empty or oversized")]
    InputLimit,
    #[error("table property JSON is invalid")]
    InvalidJson,
    #[error("table property grid cannot be bound canonically")]
    GridMismatch,
    #[error("table property state does not exactly cover the grid master cells")]
    CellSetMismatch,
    #[error("table property identifier exceeds its configured bound")]
    IdentifierLimit,
    #[error("table property digest is invalid")]
    DigestInvalid,
    #[error("table property request does not bind the exact current state")]
    StateBindingMismatch,
    #[error("table property operation contains no mutation")]
    EmptyOperation,
    #[error("table property operation requires a selected cell range")]
    SelectionRequired,
    #[error("a table-only property operation cannot include selected cells")]
    SelectionForbidden,
    #[error("table property selection exceeds its configured bound")]
    SelectionLimit,
    #[error("table property selection contains a duplicate logical slot")]
    DuplicateSelectedSlot,
    #[error("table property selection contains a slot outside the grid")]
    SelectionOutOfBounds,
    #[error("table property selection must be one contiguous rectangle")]
    NonRectangularSelection,
    #[error("table property selection partially intersects a merged cell")]
    MergedSelectionConflict,
    #[error("table property dimensions overflow")]
    DimensionOverflow,
    #[error("table property request, state, or grid changed before build")]
    BindingDrift,
    #[error("table property master-cell work exceeds its configured bound")]
    MasterCellLimit,
    #[error("table property output exceeds its configured bound")]
    OutputLimit,
    #[error("table property serialization failed")]
    Serialization,
    #[error("table property allocation failed")]
    AllocationFailed,
}

impl TablePropertiesError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_properties_invalid_limit",
            Self::UnsupportedVersion => "table_properties_unsupported_version",
            Self::InputLimit => "table_properties_input_limit",
            Self::InvalidJson => "table_properties_invalid_json",
            Self::GridMismatch => "table_properties_grid_mismatch",
            Self::CellSetMismatch => "table_properties_cell_set_mismatch",
            Self::IdentifierLimit => "table_properties_identifier_limit",
            Self::DigestInvalid => "table_properties_digest_invalid",
            Self::StateBindingMismatch => "table_properties_state_binding_mismatch",
            Self::EmptyOperation => "table_properties_empty_operation",
            Self::SelectionRequired => "table_properties_selection_required",
            Self::SelectionForbidden => "table_properties_selection_forbidden",
            Self::SelectionLimit => "table_properties_selection_limit",
            Self::DuplicateSelectedSlot => "table_properties_duplicate_selected_slot",
            Self::SelectionOutOfBounds => "table_properties_selection_out_of_bounds",
            Self::NonRectangularSelection => "table_properties_non_rectangular_selection",
            Self::MergedSelectionConflict => "table_properties_merged_selection_conflict",
            Self::DimensionOverflow => "table_properties_dimension_overflow",
            Self::BindingDrift => "table_properties_binding_drift",
            Self::MasterCellLimit => "table_properties_master_cell_limit",
            Self::OutputLimit => "table_properties_output_limit",
            Self::Serialization => "table_properties_serialization",
            Self::AllocationFailed => "table_properties_allocation",
        }
    }
}
