use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    CellCoordinate, FormulaCachePolicy, FormulaCell, FormulaCellDraft, FormulaGridDimensions,
    FormulaLimits, LogicalId, TableCellSpan, TableGrid, TableGridLimits,
};

pub const TABLE_TRANSPOSE_SCHEMA_VERSION: &str = "hwpx-agent.table-transpose/v1";
pub const TABLE_TRANSPOSE_CAPABILITY_ID: &str = "table.transpose";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableTransposeLimitConfig {
    pub input_bytes: usize,
    pub master_cells: usize,
    pub identifier_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for TableTransposeLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 16 * 1024 * 1024,
            master_cells: 1_000_000,
            identifier_bytes: 256,
            serialized_bytes: 128 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableTransposeLimits(TableTransposeLimitConfig);

impl TableTransposeLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_MASTER_CELLS: usize = 1_000_000;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 1_024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for the table-transpose boundary.
    ///
    /// # Errors
    ///
    /// Rejects zero, over-ceiling or internally inconsistent values.
    pub fn new(config: TableTransposeLimitConfig) -> Result<Self, TableTransposeError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.master_cells == 0
            || config.master_cells > Self::HARD_MAX_MASTER_CELLS
            || config.identifier_bytes == 0
            || config.identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.input_bytes > config.serialized_bytes
        {
            return Err(TableTransposeError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableTransposeLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableTransposeFormulaPolicy {
    Reject,
    TransposeAndClearCache,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableTransposeCellDraft {
    pub master_cell_id: LogicalId,
    pub coordinate: CellCoordinate,
    pub payload_sha256: String,
    pub style_sha256: String,
    pub formula: Option<FormulaCellDraft>,
}

impl fmt::Debug for TableTransposeCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeCellDraft")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("payload_sha256", &"<redacted>")
            .field("style_sha256", &"<redacted>")
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableTransposeRequestDraft {
    pub schema_version: String,
    pub table_id: LogicalId,
    pub table_properties_sha256: String,
    pub formula_policy: TableTransposeFormulaPolicy,
    pub cells: Vec<TableTransposeCellDraft>,
}

impl fmt::Debug for TableTransposeRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("table_id", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTransposeCell {
    master_cell_id: LogicalId,
    coordinate: CellCoordinate,
    payload_sha256: String,
    style_sha256: String,
    formula: Option<FormulaCell>,
}

impl TableTransposeCell {
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
    pub fn style_sha256(&self) -> &str {
        &self.style_sha256
    }

    #[must_use]
    pub const fn formula(&self) -> Option<&FormulaCell> {
        self.formula.as_ref()
    }
}

impl fmt::Debug for TableTransposeCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeCell")
            .field("master_cell_id", &"<redacted>")
            .field("coordinate", &self.coordinate)
            .field("payload_sha256", &"<redacted>")
            .field("style_sha256", &"<redacted>")
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTransposeRequest {
    schema_version: &'static str,
    capability_id: &'static str,
    table_id: LogicalId,
    grid_sha256: String,
    table_properties_sha256: String,
    formula_policy: TableTransposeFormulaPolicy,
    cells: Vec<TableTransposeCell>,
}

impl TableTransposeRequest {
    /// Validates and binds an exact complete master-cell set to one table grid.
    ///
    /// # Errors
    ///
    /// Rejects schema, grid, identifier, digest, cell coverage, formula-owner, formula-policy and
    /// finite-limit drift.
    pub fn from_draft(
        draft: TableTransposeRequestDraft,
        grid: &TableGrid,
        formula_limits: FormulaLimits,
        limits: TableTransposeLimits,
    ) -> Result<Self, TableTransposeError> {
        let TableTransposeRequestDraft {
            schema_version,
            table_id,
            table_properties_sha256,
            formula_policy,
            mut cells,
        } = draft;
        if schema_version != TABLE_TRANSPOSE_SCHEMA_VERSION {
            return Err(TableTransposeError::UnsupportedVersion);
        }
        validate_identifier(&table_id, limits)?;
        validate_digest(&table_properties_sha256)?;
        if cells.len() != grid.master_cell_count() || cells.len() > limits.0.master_cells {
            return Err(TableTransposeError::CellSetMismatch);
        }
        cells.sort_by(|left, right| {
            (left.coordinate, &left.master_cell_id).cmp(&(right.coordinate, &right.master_cell_id))
        });
        if cells.windows(2).any(|pair| {
            pair[0].coordinate == pair[1].coordinate
                || pair[0].master_cell_id == pair[1].master_cell_id
        }) {
            return Err(TableTransposeError::CellSetMismatch);
        }

        let dimensions = FormulaGridDimensions {
            rows: grid.rows(),
            columns: grid.columns(),
        };
        let mut validated_cells = Vec::new();
        validated_cells
            .try_reserve_exact(cells.len())
            .map_err(|_| TableTransposeError::AllocationFailed)?;
        for (draft_cell, span) in cells.into_iter().zip(grid.master_cells()) {
            if draft_cell.master_cell_id != span.master_cell_id
                || draft_cell.coordinate
                    != (CellCoordinate {
                        row: span.row,
                        column: span.column,
                    })
            {
                return Err(TableTransposeError::CellSetMismatch);
            }
            validate_identifier(&draft_cell.master_cell_id, limits)?;
            validate_digest(&draft_cell.payload_sha256)?;
            validate_digest(&draft_cell.style_sha256)?;
            if draft_cell.formula.is_some() && formula_policy == TableTransposeFormulaPolicy::Reject
            {
                return Err(TableTransposeError::FormulaPresent);
            }
            let formula = draft_cell
                .formula
                .map(|formula| {
                    FormulaCell::from_draft(formula, dimensions, formula_limits)
                        .map_err(|_| TableTransposeError::FormulaInvalid)
                })
                .transpose()?;
            if formula
                .as_ref()
                .is_some_and(|formula| formula.owner() != draft_cell.coordinate)
            {
                return Err(TableTransposeError::FormulaOwnerMismatch);
            }
            validated_cells.push(TableTransposeCell {
                master_cell_id: draft_cell.master_cell_id,
                coordinate: draft_cell.coordinate,
                payload_sha256: draft_cell.payload_sha256,
                style_sha256: draft_cell.style_sha256,
                formula,
            });
        }
        let request = Self {
            schema_version: TABLE_TRANSPOSE_SCHEMA_VERSION,
            capability_id: TABLE_TRANSPOSE_CAPABILITY_ID,
            table_id,
            grid_sha256: hex(grid
                .canonical_sha256()
                .map_err(|_| TableTransposeError::GridMismatch)?),
            table_properties_sha256,
            formula_policy,
            cells: validated_cells,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict bounded JSON and validates it against an exact grid and formula limit set.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, malformed, duplicate-key or unknown-field JSON and every failure
    /// reported by [`Self::from_draft`].
    pub fn from_json(
        bytes: &[u8],
        grid: &TableGrid,
        formula_limits: FormulaLimits,
        limits: TableTransposeLimits,
    ) -> Result<Self, TableTransposeError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(TableTransposeError::InputLimit);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| TableTransposeError::InvalidJson)?;
        Self::from_draft(draft, grid, formula_limits, limits)
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
    pub fn table_properties_sha256(&self) -> &str {
        &self.table_properties_sha256
    }

    #[must_use]
    pub const fn formula_policy(&self) -> TableTransposeFormulaPolicy {
        self.formula_policy
    }

    #[must_use]
    pub fn cells(&self) -> &[TableTransposeCell] {
        &self.cells
    }

    /// Serializes the validated request under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the finite bound.
    pub fn canonical_json(
        &self,
        limits: TableTransposeLimits,
    ) -> Result<Vec<u8>, TableTransposeError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical request.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableTransposeLimits,
    ) -> Result<[u8; 32], TableTransposeError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableTransposeRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeRequest")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("formula_policy", &self.formula_policy)
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTransposeRelocation {
    pub master_cell_id: LogicalId,
    pub before: CellCoordinate,
    pub after: CellCoordinate,
    pub before_row_span: u32,
    pub before_column_span: u32,
    pub after_row_span: u32,
    pub after_column_span: u32,
    pub payload_sha256: String,
    pub style_sha256: String,
    pub before_formula_sha256: Option<String>,
    pub after_formula_sha256: Option<String>,
    pub formula: Option<FormulaCell>,
}

impl fmt::Debug for TableTransposeRelocation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeRelocation")
            .field("master_cell_id", &"<redacted>")
            .field("before", &self.before)
            .field("after", &self.after)
            .field("before_row_span", &self.before_row_span)
            .field("before_column_span", &self.before_column_span)
            .field("after_row_span", &self.after_row_span)
            .field("after_column_span", &self.after_column_span)
            .field("payload_sha256", &"<redacted>")
            .field("style_sha256", &"<redacted>")
            .field(
                "before_formula_sha256",
                &self.before_formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field(
                "after_formula_sha256",
                &self.after_formula_sha256.as_ref().map(|_| "<redacted>"),
            )
            .field("formula", &self.formula.as_ref().map(|_| "<redacted>"))
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTransposeReceipt {
    pub schema_version: &'static str,
    pub capability_id: &'static str,
    pub table_id: LogicalId,
    pub request_sha256: String,
    pub before_grid_sha256: String,
    pub after_grid_sha256: String,
    pub table_properties_sha256: String,
    pub master_cell_count: usize,
    pub merged_cell_count: usize,
    pub formula_count: usize,
    pub formula_changed_count: usize,
    pub semantic_change_count: usize,
    pub payload_preserved_count: usize,
    pub style_preserved_count: usize,
    pub cache_cleared_count: usize,
}

impl fmt::Debug for TableTransposeReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposeReceipt")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("table_id", &"<redacted>")
            .field("request_sha256", &"<redacted>")
            .field("before_grid_sha256", &"<redacted>")
            .field("after_grid_sha256", &"<redacted>")
            .field("table_properties_sha256", &"<redacted>")
            .field("master_cell_count", &self.master_cell_count)
            .field("merged_cell_count", &self.merged_cell_count)
            .field("formula_count", &self.formula_count)
            .field("formula_changed_count", &self.formula_changed_count)
            .field("semantic_change_count", &self.semantic_change_count)
            .field("payload_preserved_count", &self.payload_preserved_count)
            .field("style_preserved_count", &self.style_preserved_count)
            .field("cache_cleared_count", &self.cache_cleared_count)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableTransposePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    rows: u32,
    columns: u32,
    master_cells: Vec<TableCellSpan>,
    relocations: Vec<TableTransposeRelocation>,
    receipt: TableTransposeReceipt,
}

impl TableTransposePlan {
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
    pub fn relocations(&self) -> &[TableTransposeRelocation] {
        &self.relocations
    }

    #[must_use]
    pub const fn receipt(&self) -> &TableTransposeReceipt {
        &self.receipt
    }

    /// Serializes the complete atomic transpose plan under the configured output bound.
    ///
    /// # Errors
    ///
    /// Rejects serialization failure or output beyond the finite bound.
    pub fn canonical_json(
        &self,
        limits: TableTransposeLimits,
    ) -> Result<Vec<u8>, TableTransposeError> {
        serialize_bounded(self, limits.0.serialized_bytes)
    }

    /// Returns SHA-256 over the bounded canonical plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableTransposeLimits,
    ) -> Result<[u8; 32], TableTransposeError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableTransposePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableTransposePlan")
            .field("schema_version", &self.schema_version)
            .field("capability_id", &self.capability_id)
            .field("rows", &self.rows)
            .field("columns", &self.columns)
            .field("master_cell_count", &self.master_cells.len())
            .field("relocation_count", &self.relocations.len())
            .field("receipt", &"<redacted>")
            .finish()
    }
}

#[derive(Debug)]
pub struct TableTransposeBuilder;

impl TableTransposeBuilder {
    /// Builds a complete deterministic transpose plan without mutating its source grid.
    ///
    /// # Errors
    ///
    /// Rejects grid drift, unsupported transposed dimensions, invalid formula transformation,
    /// allocation failure or bounded output failure. No partial plan or receipt is returned.
    pub fn build(
        request: &TableTransposeRequest,
        grid: &TableGrid,
        grid_limits: TableGridLimits,
        formula_limits: FormulaLimits,
        limits: TableTransposeLimits,
    ) -> Result<TableTransposePlan, TableTransposeError> {
        let before_grid_sha256 = hex(grid
            .canonical_sha256()
            .map_err(|_| TableTransposeError::GridMismatch)?);
        if request.grid_sha256 != before_grid_sha256
            || request.cells.len() != grid.master_cell_count()
        {
            return Err(TableTransposeError::GridMismatch);
        }

        let output_grid = transpose_grid(grid, grid_limits)?;
        let after_grid_sha256 = hex(output_grid
            .canonical_sha256()
            .map_err(|_| TableTransposeError::TransposedGridUnsupported)?);
        let (relocations, counts) = transpose_cells(request, grid, formula_limits)?;
        let request_sha256 = hex(request.canonical_sha256(limits)?);
        let receipt = TableTransposeReceipt {
            schema_version: TABLE_TRANSPOSE_SCHEMA_VERSION,
            capability_id: TABLE_TRANSPOSE_CAPABILITY_ID,
            table_id: request.table_id.clone(),
            request_sha256,
            before_grid_sha256,
            after_grid_sha256,
            table_properties_sha256: request.table_properties_sha256.clone(),
            master_cell_count: request.cells.len(),
            merged_cell_count: counts.merged,
            formula_count: counts.formulas,
            formula_changed_count: counts.formulas_changed,
            semantic_change_count: counts.semantic_changes,
            payload_preserved_count: request.cells.len(),
            style_preserved_count: request.cells.len(),
            cache_cleared_count: counts.caches_cleared,
        };
        let plan = TableTransposePlan {
            schema_version: TABLE_TRANSPOSE_SCHEMA_VERSION,
            capability_id: TABLE_TRANSPOSE_CAPABILITY_ID,
            rows: output_grid.rows(),
            columns: output_grid.columns(),
            master_cells: output_grid.master_cells().to_vec(),
            relocations,
            receipt,
        };
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }
}

#[derive(Default)]
struct TransposeCounts {
    merged: usize,
    formulas: usize,
    formulas_changed: usize,
    semantic_changes: usize,
    caches_cleared: usize,
}

struct TransposedCell {
    relocation: TableTransposeRelocation,
    flags: TransposeCellFlags,
}

#[derive(Clone, Copy)]
struct TransposeCellFlags(u8);

impl TransposeCellFlags {
    const MERGED: u8 = 1;
    const FORMULA: u8 = 2;
    const FORMULA_CHANGED: u8 = 4;
    const SEMANTIC_CHANGED: u8 = 8;
    const CACHE_CLEARED: u8 = 16;

    const fn contains(self, flag: u8) -> bool {
        self.0 & flag != 0
    }
}

fn transpose_grid(
    grid: &TableGrid,
    grid_limits: TableGridLimits,
) -> Result<TableGrid, TableTransposeError> {
    let mut spans = Vec::new();
    spans
        .try_reserve_exact(grid.master_cell_count())
        .map_err(|_| TableTransposeError::AllocationFailed)?;
    for span in grid.master_cells() {
        spans.push(TableCellSpan {
            master_cell_id: span.master_cell_id.clone(),
            row: span.column,
            column: span.row,
            row_span: span.column_span,
            column_span: span.row_span,
        });
    }
    TableGrid::new(grid.columns(), grid.rows(), spans, grid_limits)
        .map_err(|_| TableTransposeError::TransposedGridUnsupported)
}

fn transpose_cells(
    request: &TableTransposeRequest,
    grid: &TableGrid,
    formula_limits: FormulaLimits,
) -> Result<(Vec<TableTransposeRelocation>, TransposeCounts), TableTransposeError> {
    let dimensions = FormulaGridDimensions {
        rows: grid.rows(),
        columns: grid.columns(),
    };
    let mut relocations = Vec::new();
    relocations
        .try_reserve_exact(request.cells.len())
        .map_err(|_| TableTransposeError::AllocationFailed)?;
    let mut counts = TransposeCounts::default();
    for (cell, span) in request.cells.iter().zip(grid.master_cells()) {
        let result = transpose_cell(cell, span, dimensions, formula_limits)?;
        counts.merged = checked_flag_add(
            counts.merged,
            result.flags.contains(TransposeCellFlags::MERGED),
        )?;
        counts.formulas = checked_flag_add(
            counts.formulas,
            result.flags.contains(TransposeCellFlags::FORMULA),
        )?;
        counts.formulas_changed = checked_flag_add(
            counts.formulas_changed,
            result.flags.contains(TransposeCellFlags::FORMULA_CHANGED),
        )?;
        counts.semantic_changes = checked_flag_add(
            counts.semantic_changes,
            result.flags.contains(TransposeCellFlags::SEMANTIC_CHANGED),
        )?;
        counts.caches_cleared = checked_flag_add(
            counts.caches_cleared,
            result.flags.contains(TransposeCellFlags::CACHE_CLEARED),
        )?;
        relocations.push(result.relocation);
    }
    Ok((relocations, counts))
}

fn transpose_cell(
    cell: &TableTransposeCell,
    span: &TableCellSpan,
    dimensions: FormulaGridDimensions,
    formula_limits: FormulaLimits,
) -> Result<TransposedCell, TableTransposeError> {
    let after = CellCoordinate {
        row: cell.coordinate.column,
        column: cell.coordinate.row,
    };
    let before_formula_sha256 = formula_digest(cell.formula.as_ref(), formula_limits)?;
    let formula = cell
        .formula
        .as_ref()
        .map(|formula| {
            formula.transpose(dimensions, FormulaCachePolicy::Clear, None, formula_limits)
        })
        .transpose()
        .map_err(|_| TableTransposeError::FormulaInvalid)?;
    let after_formula_sha256 = formula_digest(formula.as_ref(), formula_limits)?;
    let formula_changed = before_formula_sha256 != after_formula_sha256;
    let cache_cleared = cell
        .formula
        .as_ref()
        .is_some_and(|formula| !matches!(formula.cache(), crate::FormulaCache::Absent));
    let merged = span.row_span != 1 || span.column_span != 1;
    let semantic_changed =
        cell.coordinate != after || span.row_span != span.column_span || formula_changed;
    let mut flags = 0_u8;
    if merged {
        flags |= TransposeCellFlags::MERGED;
    }
    if cell.formula.is_some() {
        flags |= TransposeCellFlags::FORMULA;
    }
    if formula_changed {
        flags |= TransposeCellFlags::FORMULA_CHANGED;
    }
    if semantic_changed {
        flags |= TransposeCellFlags::SEMANTIC_CHANGED;
    }
    if cache_cleared {
        flags |= TransposeCellFlags::CACHE_CLEARED;
    }
    Ok(TransposedCell {
        relocation: TableTransposeRelocation {
            master_cell_id: cell.master_cell_id.clone(),
            before: cell.coordinate,
            after,
            before_row_span: span.row_span,
            before_column_span: span.column_span,
            after_row_span: span.column_span,
            after_column_span: span.row_span,
            payload_sha256: cell.payload_sha256.clone(),
            style_sha256: cell.style_sha256.clone(),
            before_formula_sha256,
            after_formula_sha256,
            formula,
        },
        flags: TransposeCellFlags(flags),
    })
}

fn formula_digest(
    formula: Option<&FormulaCell>,
    formula_limits: FormulaLimits,
) -> Result<Option<String>, TableTransposeError> {
    formula
        .map(|formula| formula.canonical_sha256(formula_limits))
        .transpose()
        .map_err(|_| TableTransposeError::FormulaInvalid)
        .map(|digest| digest.map(hex))
}

fn checked_flag_add(value: usize, increment: bool) -> Result<usize, TableTransposeError> {
    value
        .checked_add(usize::from(increment))
        .ok_or(TableTransposeError::MasterCellLimit)
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableTransposeError {
    #[error("table transpose limits are invalid")]
    InvalidLimit,
    #[error("table transpose schema version is unsupported")]
    UnsupportedVersion,
    #[error("table transpose JSON input is empty or oversized")]
    InputLimit,
    #[error("table transpose JSON is invalid")]
    InvalidJson,
    #[error("table transpose grid binding does not match")]
    GridMismatch,
    #[error("table transpose master-cell set does not exactly match the grid")]
    CellSetMismatch,
    #[error("table transpose identifier exceeds its configured bound")]
    IdentifierLimit,
    #[error("table transpose digest is invalid")]
    DigestInvalid,
    #[error("table transpose formula policy rejects a formula cell")]
    FormulaPresent,
    #[error("table transpose formula is invalid")]
    FormulaInvalid,
    #[error("table transpose formula owner does not match its master cell")]
    FormulaOwnerMismatch,
    #[error("the transposed grid exceeds an exact grid or formula dimension bound")]
    TransposedGridUnsupported,
    #[error("table transpose master-cell work exceeds its configured bound")]
    MasterCellLimit,
    #[error("table transpose output exceeds its configured bound")]
    OutputLimit,
    #[error("table transpose serialization failed")]
    Serialization,
    #[error("table transpose allocation failed")]
    AllocationFailed,
}

impl TableTransposeError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_transpose_invalid_limit",
            Self::UnsupportedVersion => "table_transpose_unsupported_version",
            Self::InputLimit => "table_transpose_input_limit",
            Self::InvalidJson => "table_transpose_invalid_json",
            Self::GridMismatch => "table_transpose_grid_mismatch",
            Self::CellSetMismatch => "table_transpose_cell_set_mismatch",
            Self::IdentifierLimit => "table_transpose_identifier_limit",
            Self::DigestInvalid => "table_transpose_digest_invalid",
            Self::FormulaPresent => "table_transpose_formula_present",
            Self::FormulaInvalid => "table_transpose_formula_invalid",
            Self::FormulaOwnerMismatch => "table_transpose_formula_owner_mismatch",
            Self::TransposedGridUnsupported => "table_transpose_grid_unsupported",
            Self::MasterCellLimit => "table_transpose_master_cell_limit",
            Self::OutputLimit => "table_transpose_output_limit",
            Self::Serialization => "table_transpose_serialization",
            Self::AllocationFailed => "table_transpose_allocation",
        }
    }
}

fn validate_identifier(
    identifier: &LogicalId,
    limits: TableTransposeLimits,
) -> Result<(), TableTransposeError> {
    if identifier.as_str().len() > limits.0.identifier_bytes {
        return Err(TableTransposeError::IdentifierLimit);
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), TableTransposeError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableTransposeError::DigestInvalid);
    }
    Ok(())
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    maximum: usize,
) -> Result<Vec<u8>, TableTransposeError> {
    let bytes = serde_json::to_vec(value).map_err(|_| TableTransposeError::Serialization)?;
    if bytes.len() > maximum {
        return Err(TableTransposeError::OutputLimit);
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
