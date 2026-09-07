use std::fmt;
use std::io;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LengthMicrometers, LogicalId, RatioMillionths, TableGrid, TableGridError};

pub const TABLE_LAYOUT_SCHEMA_VERSION: &str = "hwpx-agent.table-layout/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableLayoutLimitConfig {
    pub columns: usize,
    pub cells: usize,
    pub rows: usize,
    pub dimension_micrometers: u64,
    pub serialized_bytes: usize,
}

impl Default for TableLayoutLimitConfig {
    fn default() -> Self {
        Self {
            columns: 1_024,
            cells: 1_000_000,
            rows: 10_000,
            dimension_micrometers: 1_000_000_000,
            serialized_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableLayoutLimits(TableLayoutLimitConfig);

impl TableLayoutLimits {
    pub const HARD_MAX_COLUMNS: usize = 1_024;
    pub const HARD_MAX_CELLS: usize = 1_000_000;
    pub const HARD_MAX_ROWS: usize = 10_000;
    pub const HARD_MAX_DIMENSION_MICROMETERS: u64 = 1_000_000_000;
    pub const HARD_MAX_RATIO_MILLIONTHS: u64 = 10_000_000;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;

    /// Creates finite limits for the P06-05 layout boundary.
    ///
    /// # Errors
    ///
    /// Returns [`TableLayoutError::InvalidLimit`] for zero or over-ceiling values.
    pub fn new(config: TableLayoutLimitConfig) -> Result<Self, TableLayoutError> {
        if config.columns == 0
            || config.columns > Self::HARD_MAX_COLUMNS
            || config.cells == 0
            || config.cells > Self::HARD_MAX_CELLS
            || config.rows == 0
            || config.rows > Self::HARD_MAX_ROWS
            || config.dimension_micrometers == 0
            || config.dimension_micrometers > Self::HARD_MAX_DIMENSION_MICROMETERS
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(TableLayoutError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableLayoutLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TableWidthSpec {
    Absolute { width: LengthMicrometers },
    Percent { ratio: RatioMillionths },
    FitContent,
    FitPage,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FontMetricStatus {
    Verified,
    Estimated,
    Missing,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FontMetricVerification {
    Verified,
    Unverified,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FontMetricEvidence {
    pub status: FontMetricStatus,
    pub profile_id: Option<String>,
    pub source_sha256: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableColumnConstraint {
    pub minimum_width: LengthMicrometers,
    pub preferred_width: LengthMicrometers,
    pub previous_width: LengthMicrometers,
    pub fixed_width: Option<LengthMicrometers>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableCellMeasure {
    pub master_cell_id: LogicalId,
    pub leading_margin: LengthMicrometers,
    pub trailing_margin: LengthMicrometers,
    pub unbreakable_content_width: LengthMicrometers,
    pub preferred_content_width: LengthMicrometers,
    pub line_height: LengthMicrometers,
    pub font_metric_evidence: FontMetricEvidence,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TableLayoutProblem {
    pub schema_version: String,
    pub width: TableWidthSpec,
    pub body_width: LengthMicrometers,
    pub columns: Vec<TableColumnConstraint>,
    pub cells: Vec<TableCellMeasure>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CellWidthDeficit {
    pub master_cell_id: LogicalId,
    pub required_minimum_width: LengthMicrometers,
    pub actual_width: LengthMicrometers,
    pub deficit: LengthMicrometers,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct TableLayoutObjective {
    pub body_overflow: LengthMicrometers,
    pub target_overflow: LengthMicrometers,
    pub target_underfill: LengthMicrometers,
    pub content_overflow: LengthMicrometers,
    pub estimated_total_row_height: LengthMicrometers,
    pub previous_width_change: LengthMicrometers,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct TableLayoutPlan {
    schema_version: &'static str,
    grid_sha256: String,
    font_metric_evidence_sha256: String,
    width: TableWidthSpec,
    body_width: LengthMicrometers,
    target_width: LengthMicrometers,
    column_widths: Vec<LengthMicrometers>,
    estimated_row_heights: Vec<LengthMicrometers>,
    total_width: LengthMicrometers,
    body_overflow: LengthMicrometers,
    target_overflow: LengthMicrometers,
    target_underfill: LengthMicrometers,
    content_deficits: Vec<CellWidthDeficit>,
    font_metric_verification: FontMetricVerification,
    objective: TableLayoutObjective,
}

impl TableLayoutPlan {
    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub fn grid_sha256(&self) -> &str {
        &self.grid_sha256
    }

    #[must_use]
    pub fn font_metric_evidence_sha256(&self) -> &str {
        &self.font_metric_evidence_sha256
    }

    #[must_use]
    pub const fn width(&self) -> TableWidthSpec {
        self.width
    }

    #[must_use]
    pub const fn body_width(&self) -> LengthMicrometers {
        self.body_width
    }

    #[must_use]
    pub const fn target_width(&self) -> LengthMicrometers {
        self.target_width
    }

    #[must_use]
    pub fn column_widths(&self) -> &[LengthMicrometers] {
        &self.column_widths
    }

    #[must_use]
    pub fn estimated_row_heights(&self) -> &[LengthMicrometers] {
        &self.estimated_row_heights
    }

    #[must_use]
    pub const fn total_width(&self) -> LengthMicrometers {
        self.total_width
    }

    #[must_use]
    pub const fn body_overflow(&self) -> LengthMicrometers {
        self.body_overflow
    }

    #[must_use]
    pub const fn target_overflow(&self) -> LengthMicrometers {
        self.target_overflow
    }

    #[must_use]
    pub const fn target_underfill(&self) -> LengthMicrometers {
        self.target_underfill
    }

    #[must_use]
    pub fn content_deficits(&self) -> &[CellWidthDeficit] {
        &self.content_deficits
    }

    #[must_use]
    pub const fn font_metric_verification(&self) -> FontMetricVerification {
        self.font_metric_verification
    }

    #[must_use]
    pub const fn objective(&self) -> &TableLayoutObjective {
        &self.objective
    }

    #[must_use]
    pub fn has_overflow(&self) -> bool {
        self.body_overflow.as_i64() != 0
            || self.target_overflow.as_i64() != 0
            || !self.content_deficits.is_empty()
    }

    /// Requires a fit and verified font metrics before a plan can be promoted to verified layout.
    ///
    /// # Errors
    ///
    /// Returns a stable overflow or font-metric error without mutating the plan.
    pub fn require_verified(&self) -> Result<(), TableLayoutError> {
        if self.has_overflow() {
            return Err(TableLayoutError::LayoutOverflow);
        }
        if self.target_underfill.as_i64() != 0 {
            return Err(TableLayoutError::TargetWidthUnsatisfied);
        }
        if self.font_metric_verification != FontMetricVerification::Verified {
            return Err(TableLayoutError::FontMetricsUnverified);
        }
        Ok(())
    }

    /// Emits stable compact JSON under the configured finite output limit.
    ///
    /// # Errors
    ///
    /// Returns a stable limit, allocation, or serialization error.
    pub fn canonical_json(&self, limits: TableLayoutLimits) -> Result<Vec<u8>, TableLayoutError> {
        let mut writer = BoundedWriter::new(limits.0.serialized_bytes);
        if serde_json::to_writer(&mut writer, self).is_err() {
            return Err(match writer.failure {
                WriterFailure::Limit => TableLayoutError::OutputLimitExceeded,
                WriterFailure::Allocation => TableLayoutError::AllocationFailed,
                WriterFailure::None => TableLayoutError::SerializationFailed,
            });
        }
        Ok(writer.bytes)
    }

    /// Hashes the canonical layout plan.
    ///
    /// # Errors
    ///
    /// Propagates canonical serialization failures.
    pub fn canonical_sha256(
        &self,
        limits: TableLayoutLimits,
    ) -> Result<[u8; 32], TableLayoutError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }
}

impl fmt::Debug for TableLayoutPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("TableLayoutPlan")
            .field("width", &self.width)
            .field("columns", &self.column_widths.len())
            .field("rows", &self.estimated_row_heights.len())
            .field("content_deficits", &self.content_deficits.len())
            .field("font_metric_verification", &self.font_metric_verification)
            .finish_non_exhaustive()
    }
}

pub struct TableLayoutSolver;

impl fmt::Debug for TableLayoutSolver {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("TableLayoutSolver")
    }
}

impl TableLayoutSolver {
    /// Produces a deterministic approximate column and row layout bound to an exact grid.
    ///
    /// Hard minimums are never shrunk. Unavoidable body or fixed-span overflow is returned in the
    /// plan; callers that require a verified fit must call [`TableLayoutPlan::require_verified`].
    ///
    /// # Errors
    ///
    /// Rejects unsupported versions, mismatched grids, invalid measurements, finite-limit failures,
    /// arithmetic overflow, and allocation failure.
    pub fn solve(
        grid: &TableGrid,
        problem: &TableLayoutProblem,
        limits: TableLayoutLimits,
    ) -> Result<TableLayoutPlan, TableLayoutError> {
        let (column_count, body_width, target_width, exact_target) =
            validate_problem(grid, problem, limits)?;
        let mut columns = initial_columns(problem, column_count, limits)?;
        let ordered_measures = ordered_measures(grid, &problem.cells, limits)?;
        for (_, measure) in &ordered_measures {
            validate_measure(measure, limits)?;
        }
        enforce_minimums(&mut columns, &ordered_measures, column_count, limits)?;
        apply_preferreds(
            &mut columns,
            &ordered_measures,
            column_count,
            target_width,
            exact_target,
            limits,
        )?;

        let total_width = checked_sum(&columns.widths)?;
        let body_overflow = total_width.saturating_sub(body_width);
        let target_overflow = total_width.saturating_sub(target_width);
        let target_underfill = if exact_target {
            target_width.saturating_sub(total_width)
        } else {
            0
        };
        let (content_deficits, content_overflow) =
            collect_content_deficits(&ordered_measures, &columns.widths, column_count)?;
        let estimated_rows = estimate_rows(grid, &ordered_measures, &columns.widths, limits)?;
        let estimated_total_row_height = checked_sum(&estimated_rows)?;
        let previous_width_change = previous_width_change(&columns)?;
        let metric_verification = metric_verification(&ordered_measures);
        let grid_sha256 = hex_digest(grid.canonical_sha256()?);
        let font_metric_evidence_sha256 = metric_evidence_digest(&ordered_measures);

        Ok(TableLayoutPlan {
            schema_version: TABLE_LAYOUT_SCHEMA_VERSION,
            grid_sha256,
            font_metric_evidence_sha256,
            width: problem.width,
            body_width: to_length(body_width)?,
            target_width: to_length(target_width)?,
            column_widths: lengths(&columns.widths)?,
            estimated_row_heights: lengths(&estimated_rows)?,
            total_width: to_length(total_width)?,
            body_overflow: to_length(body_overflow)?,
            target_overflow: to_length(target_overflow)?,
            target_underfill: to_length(target_underfill)?,
            content_deficits,
            font_metric_verification: metric_verification,
            objective: TableLayoutObjective {
                body_overflow: to_length(body_overflow)?,
                target_overflow: to_length(target_overflow)?,
                target_underfill: to_length(target_underfill)?,
                content_overflow: to_length(content_overflow)?,
                estimated_total_row_height: to_length(estimated_total_row_height)?,
                previous_width_change: to_length(previous_width_change)?,
            },
        })
    }
}

struct SolverColumns {
    widths: Vec<u64>,
    preferred: Vec<u64>,
    previous: Vec<u64>,
    automatic: Vec<bool>,
}

fn validate_problem(
    grid: &TableGrid,
    problem: &TableLayoutProblem,
    limits: TableLayoutLimits,
) -> Result<(usize, u64, u64, bool), TableLayoutError> {
    if problem.schema_version != TABLE_LAYOUT_SCHEMA_VERSION {
        return Err(TableLayoutError::UnsupportedVersion);
    }
    let column_count =
        usize::try_from(grid.columns()).map_err(|_| TableLayoutError::GridDimensionOverflow)?;
    let row_count =
        usize::try_from(grid.rows()).map_err(|_| TableLayoutError::GridDimensionOverflow)?;
    if column_count == 0
        || column_count > limits.0.columns
        || row_count == 0
        || row_count > limits.0.rows
    {
        return Err(TableLayoutError::GridLimitExceeded);
    }
    if problem.columns.len() != column_count {
        return Err(TableLayoutError::ColumnCountMismatch);
    }
    if problem.cells.len() != grid.master_cell_count() {
        return Err(TableLayoutError::CellCountMismatch);
    }
    if problem.cells.len() > limits.0.cells {
        return Err(TableLayoutError::CellLimitExceeded);
    }
    let body = positive_dimension(problem.body_width, limits.0.dimension_micrometers, false)?;
    let (target, exact) = target_width(problem.width, body, limits)?;
    Ok((column_count, body, target, exact))
}

fn target_width(
    specification: TableWidthSpec,
    body_width: u64,
    limits: TableLayoutLimits,
) -> Result<(u64, bool), TableLayoutError> {
    match specification {
        TableWidthSpec::Absolute { width } => Ok((
            positive_dimension(width, limits.0.dimension_micrometers, false)?,
            true,
        )),
        TableWidthSpec::Percent { ratio } => {
            let ratio = u64::try_from(ratio.as_i64())
                .map_err(|_| TableLayoutError::InvalidWidthSpecification)?;
            if ratio == 0 || ratio > TableLayoutLimits::HARD_MAX_RATIO_MILLIONTHS {
                return Err(TableLayoutError::InvalidWidthSpecification);
            }
            let scaled = u128::from(body_width)
                .checked_mul(u128::from(ratio))
                .and_then(|value| value.checked_add(500_000))
                .ok_or(TableLayoutError::ArithmeticOverflow)?;
            let target = u64::try_from(scaled / 1_000_000)
                .map_err(|_| TableLayoutError::ArithmeticOverflow)?;
            if target == 0 || target > limits.0.dimension_micrometers {
                return Err(TableLayoutError::DimensionLimitExceeded);
            }
            Ok((target, true))
        }
        TableWidthSpec::FitContent => Ok((body_width, false)),
        TableWidthSpec::FitPage => Ok((body_width, true)),
    }
}

fn initial_columns(
    problem: &TableLayoutProblem,
    column_count: usize,
    limits: TableLayoutLimits,
) -> Result<SolverColumns, TableLayoutError> {
    let mut columns = SolverColumns {
        widths: reserved(column_count)?,
        preferred: reserved(column_count)?,
        previous: reserved(column_count)?,
        automatic: reserved(column_count)?,
    };
    for column in &problem.columns {
        let minimum =
            positive_dimension(column.minimum_width, limits.0.dimension_micrometers, false)?;
        let preferred = positive_dimension(
            column.preferred_width,
            limits.0.dimension_micrometers,
            false,
        )?;
        let previous =
            positive_dimension(column.previous_width, limits.0.dimension_micrometers, false)?;
        if preferred < minimum {
            return Err(TableLayoutError::InvalidColumnConstraint);
        }
        let (width, automatic) = if let Some(fixed) = column.fixed_width {
            let fixed = positive_dimension(fixed, limits.0.dimension_micrometers, false)?;
            if fixed < minimum {
                return Err(TableLayoutError::InvalidColumnConstraint);
            }
            (fixed, false)
        } else {
            (minimum, true)
        };
        columns.widths.push(width);
        columns.preferred.push(if automatic {
            preferred.max(width)
        } else {
            width
        });
        columns.previous.push(previous);
        columns.automatic.push(automatic);
    }
    Ok(columns)
}

fn enforce_minimums(
    columns: &mut SolverColumns,
    measures: &[(&crate::TableCellSpan, &TableCellMeasure)],
    column_count: usize,
    limits: TableLayoutLimits,
) -> Result<(), TableLayoutError> {
    for (span, measure) in measures {
        let required = outer_width(measure, false)?;
        let indexes = span_indexes(span.column, span.column_span, column_count)?;
        let actual = sum_indexes(&columns.widths, &indexes)?;
        let adjustable = adjustable_indexes(&indexes, &columns.automatic)?;
        if actual < required && !adjustable.is_empty() {
            increase_evenly(
                &mut columns.widths,
                &adjustable,
                required - actual,
                limits.0.dimension_micrometers,
            )?;
        }
    }
    Ok(())
}

fn apply_preferreds(
    columns: &mut SolverColumns,
    measures: &[(&crate::TableCellSpan, &TableCellMeasure)],
    column_count: usize,
    target_width: u64,
    exact_target: bool,
    limits: TableLayoutLimits,
) -> Result<(), TableLayoutError> {
    let minimum_total = checked_sum(&columns.widths)?;
    if minimum_total > target_width {
        return Ok(());
    }
    let mut targets = copy_widths(&columns.preferred)?;
    for (span, measure) in measures {
        let preferred = outer_width(measure, true)?;
        let indexes = span_indexes(span.column, span.column_span, column_count)?;
        let actual = sum_indexes(&targets, &indexes)?;
        let adjustable = adjustable_indexes(&indexes, &columns.automatic)?;
        if actual < preferred && !adjustable.is_empty() {
            increase_evenly(
                &mut targets,
                &adjustable,
                preferred - actual,
                limits.0.dimension_micrometers,
            )?;
        }
    }
    allocate_toward_targets(&mut columns.widths, &targets, target_width - minimum_total)?;
    if exact_target {
        fill_body(columns, target_width, limits)?;
    }
    Ok(())
}

fn fill_body(
    columns: &mut SolverColumns,
    body_width: u64,
    limits: TableLayoutLimits,
) -> Result<(), TableLayoutError> {
    let total = checked_sum(&columns.widths)?;
    if total < body_width {
        let mut targets = copy_widths(&columns.widths)?;
        for (index, target) in targets.iter_mut().enumerate() {
            if columns.automatic[index] {
                *target = (*target).max(columns.previous[index]);
            }
        }
        allocate_toward_targets(&mut columns.widths, &targets, body_width - total)?;
    }
    let total = checked_sum(&columns.widths)?;
    if total < body_width {
        let automatic = true_indexes(&columns.automatic)?;
        if !automatic.is_empty() {
            increase_evenly(
                &mut columns.widths,
                &automatic,
                body_width - total,
                limits.0.dimension_micrometers,
            )?;
        }
    }
    Ok(())
}

fn collect_content_deficits(
    measures: &[(&crate::TableCellSpan, &TableCellMeasure)],
    widths: &[u64],
    column_count: usize,
) -> Result<(Vec<CellWidthDeficit>, u64), TableLayoutError> {
    let mut deficits = Vec::new();
    deficits
        .try_reserve_exact(measures.len())
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    let mut total = 0_u64;
    for (span, measure) in measures {
        let required = outer_width(measure, false)?;
        let indexes = span_indexes(span.column, span.column_span, column_count)?;
        let actual = sum_indexes(widths, &indexes)?;
        if actual < required {
            let deficit = required - actual;
            total = total
                .checked_add(deficit)
                .ok_or(TableLayoutError::ArithmeticOverflow)?;
            deficits.push(CellWidthDeficit {
                master_cell_id: measure.master_cell_id.clone(),
                required_minimum_width: to_length(required)?,
                actual_width: to_length(actual)?,
                deficit: to_length(deficit)?,
            });
        }
    }
    Ok((deficits, total))
}

fn previous_width_change(columns: &SolverColumns) -> Result<u64, TableLayoutError> {
    columns
        .widths
        .iter()
        .zip(&columns.previous)
        .try_fold(0_u64, |total, (current, previous)| {
            total
                .checked_add(current.abs_diff(*previous))
                .ok_or(TableLayoutError::ArithmeticOverflow)
        })
}

fn metric_verification(
    measures: &[(&crate::TableCellSpan, &TableCellMeasure)],
) -> FontMetricVerification {
    if measures
        .iter()
        .all(|(_, measure)| measure.font_metric_evidence.status == FontMetricStatus::Verified)
    {
        FontMetricVerification::Verified
    } else {
        FontMetricVerification::Unverified
    }
}

fn metric_evidence_digest(measures: &[(&crate::TableCellSpan, &TableCellMeasure)]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(b"hwpx-agent.table-layout.font-metric-evidence/v1\0");
    for (_, measure) in measures {
        update_digest_component(&mut hasher, measure.master_cell_id.as_str().as_bytes());
        let status = match measure.font_metric_evidence.status {
            FontMetricStatus::Verified => b"verified".as_slice(),
            FontMetricStatus::Estimated => b"estimated".as_slice(),
            FontMetricStatus::Missing => b"missing".as_slice(),
        };
        update_digest_component(&mut hasher, status);
        update_optional_digest_component(
            &mut hasher,
            measure.font_metric_evidence.profile_id.as_deref(),
        );
        update_optional_digest_component(
            &mut hasher,
            measure.font_metric_evidence.source_sha256.as_deref(),
        );
    }
    hex_digest(hasher.finalize().into())
}

fn update_digest_component(hasher: &mut Sha256, value: &[u8]) {
    hasher.update(u64::try_from(value.len()).unwrap_or(u64::MAX).to_be_bytes());
    hasher.update(value);
}

fn update_optional_digest_component(hasher: &mut Sha256, value: Option<&str>) {
    match value {
        Some(value) => {
            hasher.update([1]);
            update_digest_component(hasher, value.as_bytes());
        }
        None => hasher.update([0]),
    }
}

fn is_lower_hex_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn ordered_measures<'a>(
    grid: &'a TableGrid,
    measures: &'a [TableCellMeasure],
    limits: TableLayoutLimits,
) -> Result<Vec<(&'a crate::TableCellSpan, &'a TableCellMeasure)>, TableLayoutError> {
    let mut indexes = Vec::new();
    indexes
        .try_reserve_exact(measures.len())
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    indexes.extend(0..measures.len());
    indexes.sort_unstable_by(|left, right| {
        measures[*left]
            .master_cell_id
            .cmp(&measures[*right].master_cell_id)
    });
    if indexes
        .windows(2)
        .any(|pair| measures[pair[0]].master_cell_id == measures[pair[1]].master_cell_id)
    {
        return Err(TableLayoutError::DuplicateCellMeasure);
    }

    let mut ordered = Vec::new();
    ordered
        .try_reserve_exact(grid.master_cell_count())
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    for span in grid.master_cells() {
        let result = indexes
            .binary_search_by(|index| measures[*index].master_cell_id.cmp(&span.master_cell_id));
        let position = result.map_err(|_| TableLayoutError::MissingCellMeasure)?;
        let index = *indexes
            .get(position)
            .ok_or(TableLayoutError::InternalInvariant)?;
        ordered.push((span, &measures[index]));
    }
    if ordered.len() > limits.0.cells {
        return Err(TableLayoutError::CellLimitExceeded);
    }
    Ok(ordered)
}

fn validate_measure(
    measure: &TableCellMeasure,
    limits: TableLayoutLimits,
) -> Result<(), TableLayoutError> {
    let leading = positive_dimension(measure.leading_margin, limits.0.dimension_micrometers, true)?;
    let trailing = positive_dimension(
        measure.trailing_margin,
        limits.0.dimension_micrometers,
        true,
    )?;
    let minimum = positive_dimension(
        measure.unbreakable_content_width,
        limits.0.dimension_micrometers,
        true,
    )?;
    let preferred = positive_dimension(
        measure.preferred_content_width,
        limits.0.dimension_micrometers,
        true,
    )?;
    let _ = positive_dimension(measure.line_height, limits.0.dimension_micrometers, false)?;
    if preferred < minimum {
        return Err(TableLayoutError::InvalidCellMeasure);
    }
    validate_metric_evidence(&measure.font_metric_evidence)?;
    leading
        .checked_add(trailing)
        .and_then(|value| value.checked_add(preferred))
        .filter(|value| *value <= limits.0.dimension_micrometers)
        .ok_or(TableLayoutError::InvalidCellMeasure)?;
    Ok(())
}

fn validate_metric_evidence(evidence: &FontMetricEvidence) -> Result<(), TableLayoutError> {
    match evidence.status {
        FontMetricStatus::Verified | FontMetricStatus::Estimated => {
            let profile = evidence
                .profile_id
                .as_deref()
                .ok_or(TableLayoutError::InvalidFontMetricEvidence)?;
            let digest = evidence
                .source_sha256
                .as_deref()
                .ok_or(TableLayoutError::InvalidFontMetricEvidence)?;
            if profile.is_empty()
                || profile.trim() != profile
                || profile.len() > 256
                || profile.chars().any(char::is_control)
                || !is_lower_hex_sha256(digest)
            {
                return Err(TableLayoutError::InvalidFontMetricEvidence);
            }
        }
        FontMetricStatus::Missing => {
            if evidence.profile_id.is_some() || evidence.source_sha256.is_some() {
                return Err(TableLayoutError::InvalidFontMetricEvidence);
            }
        }
    }
    Ok(())
}

fn outer_width(measure: &TableCellMeasure, preferred: bool) -> Result<u64, TableLayoutError> {
    let content = if preferred {
        measure.preferred_content_width
    } else {
        measure.unbreakable_content_width
    };
    raw_nonnegative(measure.leading_margin)?
        .checked_add(raw_nonnegative(measure.trailing_margin)?)
        .and_then(|value| value.checked_add(raw_nonnegative(content).ok()?))
        .ok_or(TableLayoutError::ArithmeticOverflow)
}

fn estimate_rows(
    grid: &TableGrid,
    measures: &[(&crate::TableCellSpan, &TableCellMeasure)],
    widths: &[u64],
    limits: TableLayoutLimits,
) -> Result<Vec<u64>, TableLayoutError> {
    let row_count =
        usize::try_from(grid.rows()).map_err(|_| TableLayoutError::GridDimensionOverflow)?;
    let mut rows = Vec::new();
    rows.try_reserve_exact(row_count)
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    rows.resize(row_count, 0);
    for (span, measure) in measures {
        let indexes = span_indexes(span.column, span.column_span, widths.len())?;
        let outer = sum_indexes(widths, &indexes)?;
        let margins = raw_nonnegative(measure.leading_margin)?
            .checked_add(raw_nonnegative(measure.trailing_margin)?)
            .ok_or(TableLayoutError::ArithmeticOverflow)?;
        let available = outer.saturating_sub(margins).max(1);
        let preferred = raw_nonnegative(measure.preferred_content_width)?;
        let lines = if preferred == 0 {
            1
        } else {
            preferred
                .checked_add(available - 1)
                .ok_or(TableLayoutError::ArithmeticOverflow)?
                / available
        };
        let height = lines
            .checked_mul(raw_nonnegative(measure.line_height)?)
            .ok_or(TableLayoutError::ArithmeticOverflow)?;
        let row_span = u64::from(span.row_span);
        let share = height
            .checked_add(row_span - 1)
            .ok_or(TableLayoutError::ArithmeticOverflow)?
            / row_span;
        if share > limits.0.dimension_micrometers {
            return Err(TableLayoutError::DimensionLimitExceeded);
        }
        let first =
            usize::try_from(span.row).map_err(|_| TableLayoutError::GridDimensionOverflow)?;
        let end = usize::try_from(
            span.row
                .checked_add(span.row_span)
                .ok_or(TableLayoutError::GridDimensionOverflow)?,
        )
        .map_err(|_| TableLayoutError::GridDimensionOverflow)?;
        for row in rows
            .get_mut(first..end)
            .ok_or(TableLayoutError::GridDimensionOverflow)?
        {
            *row = (*row).max(share);
        }
    }
    Ok(rows)
}

fn allocate_toward_targets(
    widths: &mut [u64],
    targets: &[u64],
    budget: u64,
) -> Result<(), TableLayoutError> {
    if widths.len() != targets.len() {
        return Err(TableLayoutError::InternalInvariant);
    }
    let needs: Vec<u64> = widths
        .iter()
        .zip(targets)
        .map(|(width, target)| target.saturating_sub(*width))
        .collect();
    let total_need = checked_sum(&needs)?;
    let allocation = budget.min(total_need);
    if allocation == 0 {
        return Ok(());
    }
    let mut applied = 0_u64;
    for (index, need) in needs.iter().copied().enumerate() {
        if need == 0 {
            continue;
        }
        let share =
            u64::try_from(u128::from(allocation) * u128::from(need) / u128::from(total_need))
                .map_err(|_| TableLayoutError::ArithmeticOverflow)?;
        widths[index] = widths[index]
            .checked_add(share)
            .ok_or(TableLayoutError::ArithmeticOverflow)?;
        applied = applied
            .checked_add(share)
            .ok_or(TableLayoutError::ArithmeticOverflow)?;
    }
    let mut remainder = allocation - applied;
    while remainder != 0 {
        let mut advanced = false;
        for (index, target) in targets.iter().copied().enumerate() {
            if remainder == 0 {
                break;
            }
            if widths[index] < target {
                widths[index] += 1;
                remainder -= 1;
                advanced = true;
            }
        }
        if !advanced {
            return Err(TableLayoutError::InternalInvariant);
        }
    }
    Ok(())
}

fn increase_evenly(
    widths: &mut [u64],
    indexes: &[usize],
    amount: u64,
    maximum: u64,
) -> Result<(), TableLayoutError> {
    if indexes.is_empty() {
        return Err(TableLayoutError::InternalInvariant);
    }
    let count = u64::try_from(indexes.len()).map_err(|_| TableLayoutError::ArithmeticOverflow)?;
    let quotient = amount / count;
    let remainder = amount % count;
    for (ordinal, index) in indexes.iter().copied().enumerate() {
        let ordinal = u64::try_from(ordinal).map_err(|_| TableLayoutError::ArithmeticOverflow)?;
        let extra = quotient + u64::from(ordinal < remainder);
        let width = widths
            .get_mut(index)
            .ok_or(TableLayoutError::InternalInvariant)?;
        *width = width
            .checked_add(extra)
            .filter(|value| *value <= maximum)
            .ok_or(TableLayoutError::DimensionLimitExceeded)?;
    }
    Ok(())
}

fn adjustable_indexes(
    indexes: &[usize],
    automatic: &[bool],
) -> Result<Vec<usize>, TableLayoutError> {
    let mut result = Vec::new();
    result
        .try_reserve_exact(indexes.len())
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    for index in indexes {
        if *automatic
            .get(*index)
            .ok_or(TableLayoutError::InternalInvariant)?
        {
            result.push(*index);
        }
    }
    Ok(result)
}

fn true_indexes(values: &[bool]) -> Result<Vec<usize>, TableLayoutError> {
    let mut result = Vec::new();
    result
        .try_reserve_exact(values.len())
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    for (index, value) in values.iter().copied().enumerate() {
        if value {
            result.push(index);
        }
    }
    Ok(result)
}

fn reserved<T>(capacity: usize) -> Result<Vec<T>, TableLayoutError> {
    let mut result = Vec::new();
    result
        .try_reserve_exact(capacity)
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    Ok(result)
}

fn span_indexes(
    first: u32,
    count: u32,
    column_count: usize,
) -> Result<Vec<usize>, TableLayoutError> {
    let first = usize::try_from(first).map_err(|_| TableLayoutError::GridDimensionOverflow)?;
    let count = usize::try_from(count).map_err(|_| TableLayoutError::GridDimensionOverflow)?;
    let end = first
        .checked_add(count)
        .filter(|value| *value <= column_count)
        .ok_or(TableLayoutError::GridDimensionOverflow)?;
    let mut result = Vec::new();
    result
        .try_reserve_exact(count)
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    result.extend(first..end);
    Ok(result)
}

fn copy_widths(values: &[u64]) -> Result<Vec<u64>, TableLayoutError> {
    let mut result = Vec::new();
    result
        .try_reserve_exact(values.len())
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    result.extend_from_slice(values);
    Ok(result)
}

fn lengths(values: &[u64]) -> Result<Vec<LengthMicrometers>, TableLayoutError> {
    let mut result = Vec::new();
    result
        .try_reserve_exact(values.len())
        .map_err(|_| TableLayoutError::AllocationFailed)?;
    for value in values {
        result.push(to_length(*value)?);
    }
    Ok(result)
}

fn sum_indexes(values: &[u64], indexes: &[usize]) -> Result<u64, TableLayoutError> {
    indexes.iter().try_fold(0_u64, |total, index| {
        total
            .checked_add(
                *values
                    .get(*index)
                    .ok_or(TableLayoutError::InternalInvariant)?,
            )
            .ok_or(TableLayoutError::ArithmeticOverflow)
    })
}

fn checked_sum(values: &[u64]) -> Result<u64, TableLayoutError> {
    values.iter().try_fold(0_u64, |total, value| {
        total
            .checked_add(*value)
            .ok_or(TableLayoutError::ArithmeticOverflow)
    })
}

fn positive_dimension(
    value: LengthMicrometers,
    maximum: u64,
    allow_zero: bool,
) -> Result<u64, TableLayoutError> {
    let value = raw_nonnegative(value)?;
    if (!allow_zero && value == 0) || value > maximum {
        return Err(TableLayoutError::DimensionLimitExceeded);
    }
    Ok(value)
}

fn raw_nonnegative(value: LengthMicrometers) -> Result<u64, TableLayoutError> {
    u64::try_from(value.as_i64()).map_err(|_| TableLayoutError::InvalidDimension)
}

fn to_length(value: u64) -> Result<LengthMicrometers, TableLayoutError> {
    i64::try_from(value)
        .map(LengthMicrometers::from_raw)
        .map_err(|_| TableLayoutError::ArithmeticOverflow)
}

fn hex_digest(value: [u8; 32]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut result = String::with_capacity(64);
    for byte in value {
        result.push(char::from(HEX[usize::from(byte >> 4)]));
        result.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    result
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum TableLayoutError {
    #[error("table layout limits are invalid")]
    InvalidLimit,
    #[error("table layout schema version is unsupported")]
    UnsupportedVersion,
    #[error("table layout grid dimensions overflow the host representation")]
    GridDimensionOverflow,
    #[error("table layout grid exceeds configured limits")]
    GridLimitExceeded,
    #[error("table layout column count does not match the grid")]
    ColumnCountMismatch,
    #[error("table layout cell measurement count does not match the grid")]
    CellCountMismatch,
    #[error("table layout cell measurement limit was exceeded")]
    CellLimitExceeded,
    #[error("table layout has a duplicate cell measurement")]
    DuplicateCellMeasure,
    #[error("table layout is missing a grid cell measurement")]
    MissingCellMeasure,
    #[error("table layout dimension is negative")]
    InvalidDimension,
    #[error("table layout dimension exceeds the configured limit")]
    DimensionLimitExceeded,
    #[error("table layout column constraint is invalid")]
    InvalidColumnConstraint,
    #[error("table layout width specification is invalid")]
    InvalidWidthSpecification,
    #[error("table layout cell measurement is invalid")]
    InvalidCellMeasure,
    #[error("table layout font metric evidence is invalid")]
    InvalidFontMetricEvidence,
    #[error("table layout arithmetic overflowed")]
    ArithmeticOverflow,
    #[error("table layout allocation failed")]
    AllocationFailed,
    #[error("table layout serialization failed")]
    SerializationFailed,
    #[error("table layout output exceeds the configured limit")]
    OutputLimitExceeded,
    #[error("table layout has explicit body or content overflow")]
    LayoutOverflow,
    #[error("table layout exact target width could not be satisfied")]
    TargetWidthUnsatisfied,
    #[error("table layout font metrics are not verified")]
    FontMetricsUnverified,
    #[error("table layout internal invariant failed")]
    InternalInvariant,
    #[error(transparent)]
    Grid(#[from] TableGridError),
}

impl TableLayoutError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_layout_invalid_limit",
            Self::UnsupportedVersion => "table_layout_unsupported_version",
            Self::GridDimensionOverflow => "table_layout_grid_dimension_overflow",
            Self::GridLimitExceeded => "table_layout_grid_limit_exceeded",
            Self::ColumnCountMismatch => "table_layout_column_count_mismatch",
            Self::CellCountMismatch => "table_layout_cell_count_mismatch",
            Self::CellLimitExceeded => "table_layout_cell_limit_exceeded",
            Self::DuplicateCellMeasure => "table_layout_duplicate_cell_measure",
            Self::MissingCellMeasure => "table_layout_missing_cell_measure",
            Self::InvalidDimension => "table_layout_invalid_dimension",
            Self::DimensionLimitExceeded => "table_layout_dimension_limit_exceeded",
            Self::InvalidColumnConstraint => "table_layout_invalid_column_constraint",
            Self::InvalidWidthSpecification => "table_layout_invalid_width_specification",
            Self::InvalidCellMeasure => "table_layout_invalid_cell_measure",
            Self::InvalidFontMetricEvidence => "table_layout_invalid_font_metric_evidence",
            Self::ArithmeticOverflow => "table_layout_arithmetic_overflow",
            Self::AllocationFailed => "table_layout_allocation_failed",
            Self::SerializationFailed => "table_layout_serialization_failed",
            Self::OutputLimitExceeded => "table_layout_output_limit_exceeded",
            Self::LayoutOverflow => "table_layout_overflow",
            Self::TargetWidthUnsatisfied => "table_layout_target_width_unsatisfied",
            Self::FontMetricsUnverified => "table_layout_font_metrics_unverified",
            Self::InternalInvariant => "table_layout_internal_invariant",
            Self::Grid(error) => error.code(),
        }
    }
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
            return Err(io::Error::other("table layout output limit"));
        };
        if next_length > self.max_bytes {
            self.failure = WriterFailure::Limit;
            return Err(io::Error::other("table layout output limit"));
        }
        if self.bytes.try_reserve(buffer.len()).is_err() {
            self.failure = WriterFailure::Allocation;
            return Err(io::Error::other("table layout allocation"));
        }
        self.bytes.extend_from_slice(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
