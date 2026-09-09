use std::collections::HashSet;
use std::fmt;
use std::io::{self, Write};

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    CellCoordinate, FormulaAstDraft, FormulaCell, FormulaCellDraft, FormulaGridDimensions,
    FormulaLimits, FormulaNumberFormat, LogicalId, TABLE_FORMULA_SCHEMA_VERSION, TableGrid,
};

pub const TABLE_NUMBER_FORMAT_SCHEMA_VERSION: &str = "hwpx-agent.table-number-format/v1";
pub const TABLE_NUMBER_FORMAT_CAPABILITY_ID: &str = "table.number_format";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableNumberFormatLimitConfig {
    pub input_bytes: usize,
    pub cells: usize,
    pub selected_cells: usize,
    pub identifier_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for TableNumberFormatLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 32 * 1024 * 1024,
            cells: 1_000_000,
            selected_cells: 4096,
            identifier_bytes: 256,
            serialized_bytes: 128 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableNumberFormatLimits(TableNumberFormatLimitConfig);

impl TableNumberFormatLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_CELLS: usize = 1_000_000;
    pub const HARD_MAX_SELECTED_CELLS: usize = 1_000_000;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite bounds for an exact table-number-format operation.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling, or internally inconsistent limits.
    pub fn new(config: TableNumberFormatLimitConfig) -> Result<Self, TableNumberFormatError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.cells == 0
            || config.cells > Self::HARD_MAX_CELLS
            || config.selected_cells == 0
            || config.selected_cells > Self::HARD_MAX_SELECTED_CELLS
            || config.selected_cells > config.cells
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TableNumberFormatError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableNumberFormatLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableNumberFormatCellDraft {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub non_formula_payload_sha256: String,
    pub properties_sha256: String,
    pub formula: Option<FormulaCellDraft>,
}

impl fmt::Debug for TableNumberFormatCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatCellDraft")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("non_formula_payload_sha256", &"<redacted>")
            .field("properties_sha256", &"<redacted>")
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableNumberFormatCell {
    master_cell_id: LogicalId,
    coordinate: CellCoordinate,
    non_formula_payload_sha256: String,
    properties_sha256: String,
    formula: Option<FormulaCell>,
}

impl TableNumberFormatCell {
    #[must_use]
    pub const fn master_cell_id(&self) -> &LogicalId {
        &self.master_cell_id
    }

    #[must_use]
    pub const fn coordinate(&self) -> CellCoordinate {
        self.coordinate
    }

    #[must_use]
    pub fn non_formula_payload_sha256(&self) -> &str {
        &self.non_formula_payload_sha256
    }

    #[must_use]
    pub fn properties_sha256(&self) -> &str {
        &self.properties_sha256
    }

    #[must_use]
    pub const fn formula(&self) -> Option<&FormulaCell> {
        self.formula.as_ref()
    }
}

impl fmt::Debug for TableNumberFormatCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatCell")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("non_formula_payload_sha256", &"<redacted>")
            .field("properties_sha256", &"<redacted>")
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableNumberFormatStateDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub grid_sha256: String,
    pub table_properties_sha256: String,
    pub cells: Vec<TableNumberFormatCellDraft>,
}

impl fmt::Debug for TableNumberFormatStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatStateDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableNumberFormatState {
    schema_version: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    table_properties_sha256: String,
    cells: Vec<TableNumberFormatCell>,
}

impl TableNumberFormatState {
    /// Validates a complete master-cell snapshot against one exact logical table grid.
    ///
    /// Each cell binds non-formula payload and property digests. Formula-bearing cells additionally
    /// retain a fully typed owner, AST, display cache and number format.
    ///
    /// # Errors
    ///
    /// Rejects schema, limit, digest, identity, grid, coverage, formula-owner, and formula-state
    /// drift.
    pub fn from_draft(
        draft: TableNumberFormatStateDraft,
        grid: &TableGrid,
        limits: TableNumberFormatLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Self, TableNumberFormatError> {
        if draft.schema_version != TABLE_NUMBER_FORMAT_SCHEMA_VERSION {
            return Err(TableNumberFormatError::UnsupportedVersion);
        }
        validate_identifier(&draft.table_id, limits)?;
        validate_digest(&draft.grid_sha256)?;
        validate_digest(&draft.table_properties_sha256)?;
        if draft.grid_sha256 != grid_digest(grid)? {
            return Err(TableNumberFormatError::GridMismatch);
        }
        if draft.cells.len() > limits.0.cells {
            return Err(TableNumberFormatError::CellLimitExceeded);
        }
        if draft.cells.len() != grid.master_cell_count() {
            return Err(TableNumberFormatError::IncompleteCellSet);
        }

        validate_formula_dimensions(grid, formula_limits)?;
        let dimensions = formula_dimensions(grid);
        let mut seen_ids = HashSet::new();
        seen_ids
            .try_reserve(draft.cells.len())
            .map_err(|_| TableNumberFormatError::AllocationFailed)?;
        let mut seen_coordinates = HashSet::new();
        seen_coordinates
            .try_reserve(draft.cells.len())
            .map_err(|_| TableNumberFormatError::AllocationFailed)?;
        let mut cells = Vec::new();
        cells
            .try_reserve_exact(draft.cells.len())
            .map_err(|_| TableNumberFormatError::AllocationFailed)?;
        for cell in draft.cells {
            validate_identifier(&cell.master_cell_id, limits)?;
            validate_digest(&cell.non_formula_payload_sha256)?;
            validate_digest(&cell.properties_sha256)?;
            if !seen_ids.insert(cell.master_cell_id.clone())
                || !seen_coordinates.insert((cell.coordinate.row, cell.coordinate.column))
            {
                return Err(TableNumberFormatError::DuplicateCell);
            }
            let span = grid
                .master_cell_at(cell.coordinate)
                .map_err(|_| TableNumberFormatError::CellGridMismatch)?;
            if span.master_cell_id != cell.master_cell_id
                || span.row != cell.coordinate.row
                || span.column != cell.coordinate.column
            {
                return Err(TableNumberFormatError::CellGridMismatch);
            }
            let formula = cell
                .formula
                .map(|formula| FormulaCell::from_draft(formula, dimensions, formula_limits))
                .transpose()?;
            if formula
                .as_ref()
                .is_some_and(|formula| formula.owner() != cell.coordinate)
            {
                return Err(TableNumberFormatError::FormulaOwnerMismatch);
            }
            cells.push(TableNumberFormatCell {
                master_cell_id: cell.master_cell_id,
                coordinate: cell.coordinate,
                non_formula_payload_sha256: cell.non_formula_payload_sha256,
                properties_sha256: cell.properties_sha256,
                formula,
            });
        }
        cells.sort_by_key(|cell| cell.coordinate);
        if cells.iter().zip(grid.master_cells()).any(|(cell, span)| {
            cell.master_cell_id != span.master_cell_id
                || cell.coordinate.row != span.row
                || cell.coordinate.column != span.column
        }) {
            return Err(TableNumberFormatError::IncompleteCellSet);
        }

        let state = Self {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION,
            table_id: draft.table_id,
            grid_sha256: draft.grid_sha256,
            table_properties_sha256: draft.table_properties_sha256,
            cells,
        };
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    /// Parses strict bounded JSON and validates a complete state snapshot.
    ///
    /// # Errors
    ///
    /// Returns stable input, JSON, or semantic validation errors.
    pub fn from_json(
        bytes: &[u8],
        grid: &TableGrid,
        limits: TableNumberFormatLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Self, TableNumberFormatError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(TableNumberFormatError::InputLimitExceeded);
        }
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableNumberFormatError::InvalidJson)?;
        Self::from_draft(draft, grid, limits, formula_limits)
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
    pub fn cells(&self) -> &[TableNumberFormatCell] {
        &self.cells
    }

    /// Emits canonical bounded JSON in logical master-cell order.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization, allocation, or output-limit error.
    pub fn canonical_json(
        &self,
        limits: TableNumberFormatLimits,
    ) -> Result<Vec<u8>, TableNumberFormatError> {
        to_bounded_json(self, limits.0.serialized_bytes)
    }

    /// Hashes the exact canonical source snapshot.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableNumberFormatLimits,
    ) -> Result<[u8; 32], TableNumberFormatError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    fn cell_at(&self, coordinate: CellCoordinate) -> Option<&TableNumberFormatCell> {
        self.cells
            .binary_search_by_key(&coordinate, |cell| cell.coordinate)
            .ok()
            .and_then(|index| self.cells.get(index))
    }
}

impl fmt::Debug for TableNumberFormatState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatState")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableNumberFormatRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub selected_cells: Vec<CellCoordinate>,
    pub target_format: FormulaNumberFormat,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
}

impl fmt::Debug for TableNumberFormatRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("selected_cells", &self.selected_cells)
            .field("target_format", &self.target_format)
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableNumberFormatRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    selected_cells: Vec<CellCoordinate>,
    target_format: FormulaNumberFormat,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
}

impl TableNumberFormatRequest {
    /// Validates an exact formula-cell selection and binds it to source state, grid and flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, selection, format, identity, source-state, grid, and flow drift.
    pub fn from_draft(
        draft: TableNumberFormatRequestDraft,
        state: &TableNumberFormatState,
        grid: &TableGrid,
        current_document_flow_sha256: &str,
        limits: TableNumberFormatLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Self, TableNumberFormatError> {
        if draft.schema_version != TABLE_NUMBER_FORMAT_SCHEMA_VERSION {
            return Err(TableNumberFormatError::UnsupportedVersion);
        }
        validate_identifier(&draft.table_id, limits)?;
        validate_target_format(draft.target_format, formula_limits)?;
        validate_digest(&draft.expected_source_state_sha256)?;
        validate_digest(&draft.expected_document_flow_sha256)?;
        validate_digest(current_document_flow_sha256)?;
        validate_state_bindings(
            &draft.table_id,
            &draft.expected_source_state_sha256,
            &draft.expected_document_flow_sha256,
            state,
            grid,
            current_document_flow_sha256,
            limits,
        )?;
        if draft.selected_cells.is_empty() {
            return Err(TableNumberFormatError::EmptySelection);
        }
        if draft.selected_cells.len() > limits.0.selected_cells {
            return Err(TableNumberFormatError::SelectionLimitExceeded);
        }
        let mut selected_cells = draft.selected_cells;
        selected_cells.sort_unstable();
        if selected_cells.windows(2).any(|pair| pair[0] == pair[1]) {
            return Err(TableNumberFormatError::DuplicateSelection);
        }
        for coordinate in &selected_cells {
            let cell = state
                .cell_at(*coordinate)
                .ok_or(TableNumberFormatError::SelectionNotFormula)?;
            if cell.formula.is_none() {
                return Err(TableNumberFormatError::SelectionNotFormula);
            }
        }

        Ok(Self {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION,
            capability_id: TABLE_NUMBER_FORMAT_CAPABILITY_ID,
            table_id: draft.table_id,
            selected_cells,
            target_format: draft.target_format,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
        })
    }

    /// Parses strict bounded request JSON and validates all exact bindings.
    ///
    /// # Errors
    ///
    /// Returns stable input, JSON, or semantic validation errors.
    pub fn from_json(
        bytes: &[u8],
        state: &TableNumberFormatState,
        grid: &TableGrid,
        current_document_flow_sha256: &str,
        limits: TableNumberFormatLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Self, TableNumberFormatError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(TableNumberFormatError::InputLimitExceeded);
        }
        let draft =
            serde_json::from_slice(bytes).map_err(|_| TableNumberFormatError::InvalidJson)?;
        Self::from_draft(
            draft,
            state,
            grid,
            current_document_flow_sha256,
            limits,
            formula_limits,
        )
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
    pub fn selected_cells(&self) -> &[CellCoordinate] {
        &self.selected_cells
    }

    #[must_use]
    pub const fn target_format(&self) -> FormulaNumberFormat {
        self.target_format
    }

    /// Emits bounded canonical request JSON.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization, allocation, or output-limit error.
    pub fn canonical_json(
        &self,
        limits: TableNumberFormatLimits,
    ) -> Result<Vec<u8>, TableNumberFormatError> {
        to_bounded_json(self, limits.0.serialized_bytes)
    }
}

impl fmt::Debug for TableNumberFormatRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("selected_cells", &self.selected_cells)
            .field("target_format", &self.target_format)
            .field("expected_source_state_sha256", &"<redacted>")
            .field("expected_document_flow_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableNumberFormatReceipt {
    selected_formula_cells: usize,
    source_state_sha256_before: String,
    source_state_sha256_after: String,
    grid_sha256_before: String,
    grid_sha256_after: String,
    document_flow_sha256_before: String,
    document_flow_sha256_after: String,
    non_format_state_preserved: bool,
}

impl TableNumberFormatReceipt {
    #[must_use]
    pub const fn selected_formula_cells(&self) -> usize {
        self.selected_formula_cells
    }

    #[must_use]
    pub fn source_state_sha256_before(&self) -> &str {
        &self.source_state_sha256_before
    }

    #[must_use]
    pub fn source_state_sha256_after(&self) -> &str {
        &self.source_state_sha256_after
    }

    #[must_use]
    pub const fn non_format_state_preserved(&self) -> bool {
        self.non_format_state_preserved
    }
}

impl fmt::Debug for TableNumberFormatReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatReceipt")
            .field("selected_formula_cells", &self.selected_formula_cells)
            .field("source_state_sha256_before", &"<redacted>")
            .field("source_state_sha256_after", &"<redacted>")
            .field("grid_sha256_before", &"<redacted>")
            .field("grid_sha256_after", &"<redacted>")
            .field("document_flow_sha256_before", &"<redacted>")
            .field("document_flow_sha256_after", &"<redacted>")
            .field(
                "non_format_state_preserved",
                &self.non_format_state_preserved,
            )
            .finish()
    }
}

#[derive(Eq, PartialEq, Serialize)]
pub struct TableNumberFormatPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request: TableNumberFormatRequest,
    after_state: TableNumberFormatState,
    receipt: TableNumberFormatReceipt,
}

impl TableNumberFormatPlan {
    #[must_use]
    pub const fn request(&self) -> &TableNumberFormatRequest {
        &self.request
    }

    #[must_use]
    pub const fn after_state(&self) -> &TableNumberFormatState {
        &self.after_state
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableNumberFormatReceipt {
        &self.receipt
    }

    /// Emits bounded canonical plan JSON.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization, allocation, or output-limit error.
    pub fn canonical_json(
        &self,
        limits: TableNumberFormatLimits,
    ) -> Result<Vec<u8>, TableNumberFormatError> {
        to_bounded_json(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the canonical plan JSON.
    ///
    /// # Errors
    ///
    /// Propagates bounded canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableNumberFormatLimits,
    ) -> Result<[u8; 32], TableNumberFormatError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableNumberFormatPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableNumberFormatPlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("request", &self.request)
            .field("after_state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug)]
pub struct TableNumberFormatBuilder;

impl TableNumberFormatBuilder {
    /// Changes only number format on the exact selected formula owners.
    ///
    /// # Errors
    ///
    /// Revalidates source state, grid, document flow, selection and target format. Any stale or
    /// invalid input fails before a plan is returned.
    pub fn build(
        request: &TableNumberFormatRequest,
        state: &TableNumberFormatState,
        grid: &TableGrid,
        current_document_flow_sha256: &str,
        limits: TableNumberFormatLimits,
        formula_limits: FormulaLimits,
    ) -> Result<TableNumberFormatPlan, TableNumberFormatError> {
        validate_target_format(request.target_format, formula_limits)?;
        validate_state_bindings(
            &request.table_id,
            &request.expected_source_state_sha256,
            &request.expected_document_flow_sha256,
            state,
            grid,
            current_document_flow_sha256,
            limits,
        )?;

        let dimensions = formula_dimensions(grid);
        let mut cells = state.cells.clone();
        for coordinate in &request.selected_cells {
            let index = cells
                .binary_search_by_key(coordinate, |cell| cell.coordinate)
                .map_err(|_| TableNumberFormatError::SelectionNotFormula)?;
            let source = cells[index]
                .formula
                .as_ref()
                .ok_or(TableNumberFormatError::SelectionNotFormula)?;
            cells[index].formula = Some(FormulaCell::from_draft(
                FormulaCellDraft {
                    schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                    owner: source.owner(),
                    ast: FormulaAstDraft {
                        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                        expression: source.ast().expression().clone(),
                    },
                    cache: source.cache().clone(),
                    number_format: request.target_format,
                },
                dimensions,
                formula_limits,
            )?);
        }
        let after_state = TableNumberFormatState {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION,
            table_id: state.table_id.clone(),
            grid_sha256: state.grid_sha256.clone(),
            table_properties_sha256: state.table_properties_sha256.clone(),
            cells,
        };
        let before_sha256 = hex(state.canonical_sha256(limits)?);
        let after_sha256 = hex(after_state.canonical_sha256(limits)?);
        let receipt = TableNumberFormatReceipt {
            selected_formula_cells: request.selected_cells.len(),
            source_state_sha256_before: before_sha256,
            source_state_sha256_after: after_sha256,
            grid_sha256_before: state.grid_sha256.clone(),
            grid_sha256_after: state.grid_sha256.clone(),
            document_flow_sha256_before: request.expected_document_flow_sha256.clone(),
            document_flow_sha256_after: request.expected_document_flow_sha256.clone(),
            non_format_state_preserved: true,
        };
        let plan = TableNumberFormatPlan {
            schema_version: TABLE_NUMBER_FORMAT_SCHEMA_VERSION,
            capability_id: TABLE_NUMBER_FORMAT_CAPABILITY_ID,
            request: request.clone(),
            after_state,
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

fn validate_state_bindings(
    table_id: &LogicalId,
    expected_source_state_sha256: &str,
    expected_document_flow_sha256: &str,
    state: &TableNumberFormatState,
    grid: &TableGrid,
    current_document_flow_sha256: &str,
    limits: TableNumberFormatLimits,
) -> Result<(), TableNumberFormatError> {
    if table_id != &state.table_id {
        return Err(TableNumberFormatError::TableIdentityMismatch);
    }
    if state.grid_sha256 != grid_digest(grid)? {
        return Err(TableNumberFormatError::GridMismatch);
    }
    if expected_source_state_sha256 != hex(state.canonical_sha256(limits)?) {
        return Err(TableNumberFormatError::StateBindingMismatch);
    }
    validate_digest(current_document_flow_sha256)?;
    if expected_document_flow_sha256 != current_document_flow_sha256 {
        return Err(TableNumberFormatError::FlowBindingMismatch);
    }
    Ok(())
}

fn validate_target_format(
    format: FormulaNumberFormat,
    limits: FormulaLimits,
) -> Result<(), TableNumberFormatError> {
    let decimal_places = match format {
        FormulaNumberFormat::General => return Ok(()),
        FormulaNumberFormat::Number { decimal_places, .. }
        | FormulaNumberFormat::Percent { decimal_places }
        | FormulaNumberFormat::Scientific { decimal_places } => decimal_places,
    };
    if decimal_places > limits.config().decimal_places {
        return Err(TableNumberFormatError::InvalidNumberFormat);
    }
    Ok(())
}

fn formula_dimensions(grid: &TableGrid) -> FormulaGridDimensions {
    FormulaGridDimensions {
        rows: grid.rows(),
        columns: grid.columns(),
    }
}

fn validate_formula_dimensions(
    grid: &TableGrid,
    limits: FormulaLimits,
) -> Result<(), TableNumberFormatError> {
    if grid.rows() > limits.config().rows || grid.columns() > limits.config().columns {
        return Err(TableNumberFormatError::Formula(
            crate::FormulaError::InvalidGridDimensions,
        ));
    }
    Ok(())
}

fn validate_identifier(
    identifier: &LogicalId,
    limits: TableNumberFormatLimits,
) -> Result<(), TableNumberFormatError> {
    if identifier.as_str().len() > limits.0.identifier_bytes {
        return Err(TableNumberFormatError::IdentifierLimitExceeded);
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), TableNumberFormatError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(TableNumberFormatError::InvalidDigest);
    }
    Ok(())
}

fn grid_digest(grid: &TableGrid) -> Result<String, TableNumberFormatError> {
    grid.canonical_sha256()
        .map(hex)
        .map_err(|_| TableNumberFormatError::GridMismatch)
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

fn to_bounded_json<T: Serialize>(
    value: &T,
    max_bytes: usize,
) -> Result<Vec<u8>, TableNumberFormatError> {
    let mut writer = BoundedWriter::new(max_bytes)?;
    serde_json::to_writer(&mut writer, value).map_err(|error| {
        if writer.limit_exceeded {
            TableNumberFormatError::OutputLimitExceeded
        } else if writer.allocation_failed {
            TableNumberFormatError::AllocationFailed
        } else {
            let _ = error;
            TableNumberFormatError::SerializationFailed
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
    fn new(max_bytes: usize) -> Result<Self, TableNumberFormatError> {
        if max_bytes == 0 || max_bytes > TableNumberFormatLimits::HARD_MAX_SERIALIZED_BYTES {
            return Err(TableNumberFormatError::InvalidLimit);
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

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableNumberFormatError {
    #[error("table-number-format limits are invalid")]
    InvalidLimit,
    #[error("table-number-format input is empty or exceeds the configured byte limit")]
    InputLimitExceeded,
    #[error("table-number-format JSON is invalid")]
    InvalidJson,
    #[error("table-number-format schema version is unsupported")]
    UnsupportedVersion,
    #[error("table-number-format identifier exceeds the configured byte limit")]
    IdentifierLimitExceeded,
    #[error("table-number-format digest must be lowercase hexadecimal SHA-256")]
    InvalidDigest,
    #[error("table-number-format grid binding does not match")]
    GridMismatch,
    #[error("table-number-format table identity does not match")]
    TableIdentityMismatch,
    #[error("table-number-format cell count exceeds the configured limit")]
    CellLimitExceeded,
    #[error("table-number-format source cell set is incomplete")]
    IncompleteCellSet,
    #[error("table-number-format source contains a duplicate cell")]
    DuplicateCell,
    #[error("table-number-format source cell does not match the grid")]
    CellGridMismatch,
    #[error("table-number-format formula owner does not match its master cell")]
    FormulaOwnerMismatch,
    #[error("table-number-format selection is empty")]
    EmptySelection,
    #[error("table-number-format selection exceeds the configured limit")]
    SelectionLimitExceeded,
    #[error("table-number-format selection contains a duplicate cell")]
    DuplicateSelection,
    #[error("table-number-format selection is not an exact formula master-cell set")]
    SelectionNotFormula,
    #[error("table-number-format target format exceeds formula limits")]
    InvalidNumberFormat,
    #[error("table-number-format source-state binding does not match")]
    StateBindingMismatch,
    #[error("table-number-format document-flow binding does not match")]
    FlowBindingMismatch,
    #[error("table-number-format output exceeds the configured byte limit")]
    OutputLimitExceeded,
    #[error("table-number-format allocation failed")]
    AllocationFailed,
    #[error("table-number-format serialization failed")]
    SerializationFailed,
    #[error("table-number-format formula validation failed: {0}")]
    Formula(#[from] crate::FormulaError),
}

impl TableNumberFormatError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_number_format_invalid_limit",
            Self::InputLimitExceeded => "table_number_format_input_limit",
            Self::InvalidJson => "table_number_format_invalid_json",
            Self::UnsupportedVersion => "table_number_format_unsupported_version",
            Self::IdentifierLimitExceeded => "table_number_format_identifier_limit",
            Self::InvalidDigest => "table_number_format_invalid_digest",
            Self::GridMismatch => "table_number_format_grid_mismatch",
            Self::TableIdentityMismatch => "table_number_format_table_identity_mismatch",
            Self::CellLimitExceeded => "table_number_format_cell_limit",
            Self::IncompleteCellSet => "table_number_format_incomplete_cell_set",
            Self::DuplicateCell => "table_number_format_duplicate_cell",
            Self::CellGridMismatch => "table_number_format_cell_grid_mismatch",
            Self::FormulaOwnerMismatch => "table_number_format_formula_owner_mismatch",
            Self::EmptySelection => "table_number_format_empty_selection",
            Self::SelectionLimitExceeded => "table_number_format_selection_limit",
            Self::DuplicateSelection => "table_number_format_duplicate_selection",
            Self::SelectionNotFormula => "table_number_format_selection_not_formula",
            Self::InvalidNumberFormat => "table_number_format_invalid_number_format",
            Self::StateBindingMismatch => "table_number_format_state_binding_mismatch",
            Self::FlowBindingMismatch => "table_number_format_flow_binding_mismatch",
            Self::OutputLimitExceeded => "table_number_format_output_limit",
            Self::AllocationFailed => "table_number_format_allocation_failed",
            Self::SerializationFailed => "table_number_format_serialization_failed",
            Self::Formula(_) => "table_number_format_formula",
        }
    }
}
