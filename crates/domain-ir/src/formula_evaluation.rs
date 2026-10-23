//! Bounded exact-decimal mathematics. Never validates native cached values or execution authority.
mod exact;

use crate::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaBinaryOperator, FormulaCache, FormulaCell,
    FormulaCellDraft, FormulaDecimal, FormulaExpression, FormulaFunction, FormulaGridDimensions,
    FormulaLimits, FormulaNumberFormat, FormulaUnaryOperator, TABLE_FORMULA_SCHEMA_VERSION,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt, io,
};
use thiserror::Error;

pub const FORMULA_EVALUATION_PROFILE: &str = "hwpx-agent.exact-formula-evaluation/v1";
pub const FORMULA_EVALUATION_SCOPE: &str =
    "explicit_numeric_grid_exact_math_not_native_cache_layout_authority_or_execution";

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct EvaluationLimitConfig {
    pub cells: usize,
    pub work: usize,
    pub depth: usize,
    pub decimal_places: u8,
    pub integer_exponent: u32,
    pub input_bytes: usize,
    pub result_bytes: usize,
}
impl Default for EvaluationLimitConfig {
    fn default() -> Self {
        Self {
            cells: 65_536,
            work: 1_000_000,
            depth: 64,
            decimal_places: 12,
            integer_exponent: 128,
            input_bytes: 8 * 1024 * 1024,
            result_bytes: 8 * 1024 * 1024,
        }
    }
}
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, Serialize)]
pub struct EvaluationLimits(EvaluationLimitConfig);
impl EvaluationLimits {
    /// # Errors
    /// Rejects zero or hard-ceiling-exceeding limits; no silent clamping.
    pub fn new(c: EvaluationLimitConfig) -> Result<Self, EvaluationError> {
        if c.cells == 0
            || c.cells > 65_536
            || c.work == 0
            || c.work > 8_000_000
            || c.depth == 0
            || c.depth > 128
            || c.decimal_places > 18
            || c.integer_exponent == 0
            || c.integer_exponent > 256
            || c.input_bytes == 0
            || c.input_bytes > 16 * 1024 * 1024
            || c.result_bytes == 0
            || c.result_bytes > 16 * 1024 * 1024
        {
            return Err(EvaluationError::InvalidLimits);
        }
        Ok(Self(c))
    }
}
#[derive(Clone, Copy, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum EvaluationInput<'a> {
    Decimal {
        value: FormulaDecimal,
    },
    Formula {
        ast: &'a FormulaAst,
    },
    /// Blank, text, Boolean, unqualified or absent numeric input is not inferred as zero.
    Unavailable,
}
impl fmt::Debug for EvaluationInput<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("EvaluationInput(<redacted>)")
    }
}
#[derive(Clone, Copy, Serialize)]
pub struct EvaluationCell<'a> {
    pub coordinate: CellCoordinate,
    pub input: EvaluationInput<'a>,
}
impl fmt::Debug for EvaluationCell<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("EvaluationCell(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EvaluatedFormulaValue {
    pub coordinate: CellCoordinate,
    pub value: FormulaDecimal,
}
impl fmt::Debug for EvaluatedFormulaValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("EvaluatedFormulaValue(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct EvaluationReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub input_sha256: [u8; 32],
    pub result_sha256: [u8; 32],
    pub evaluated_targets: usize,
    pub computed_cells: usize,
    pub reused_dependency_values: usize,
    pub work_steps: usize,
}
pub struct FormulaEvaluation {
    values: Vec<EvaluatedFormulaValue>,
    receipt: EvaluationReceipt,
}
impl fmt::Debug for FormulaEvaluation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaEvaluation(<redacted>)")
    }
}
impl FormulaEvaluation {
    #[must_use]
    pub fn values(&self) -> &[EvaluatedFormulaValue] {
        &self.values
    }
    #[must_use]
    pub const fn receipt(&self) -> &EvaluationReceipt {
        &self.receipt
    }
}

/// Borrows explicit typed inputs. No cached result, default, deserialization or source authority.
pub struct FormulaEvaluationContext<'a> {
    dimensions: FormulaGridDimensions,
    cells: BTreeMap<(u32, u32), EvaluationInput<'a>>,
    limits: EvaluationLimits,
    input_sha256: [u8; 32],
}
impl fmt::Debug for FormulaEvaluationContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaEvaluationContext(<redacted>)")
    }
}
impl<'a> FormulaEvaluationContext<'a> {
    /// Reuses original AST/grid/coordinate validation and binds the complete ordered input.
    /// # Errors
    /// Rejects malformed/duplicate/out-of-bounds inputs, original AST failures or finite limits.
    pub fn bind(
        dimensions: FormulaGridDimensions,
        inputs: &[EvaluationCell<'a>],
        limits: EvaluationLimits,
        original_limits: FormulaLimits,
    ) -> Result<Self, EvaluationError> {
        let config = original_limits.config();
        if dimensions.rows == 0
            || dimensions.columns == 0
            || dimensions.rows > config.rows
            || dimensions.columns > config.columns
            || inputs.len() > limits.0.cells
        {
            return Err(EvaluationError::Grid);
        }
        // Stream into a bounded digest before cloning any AST. Never allocate whole grid JSON.
        let input_sha256 = hash_bounded(
            &(FORMULA_EVALUATION_PROFILE, dimensions, inputs, limits),
            limits.0.input_bytes,
        )
        .map_err(|_| EvaluationError::InputLimit)?;
        let mut cells = BTreeMap::new();
        for cell in inputs {
            if cell.coordinate.row >= dimensions.rows
                || cell.coordinate.column >= dimensions.columns
            {
                return Err(EvaluationError::OutOfBounds);
            }
            match cell.input {
                EvaluationInput::Decimal { value } => {
                    if value.scale() > config.decimal_places
                        || value.scale() > limits.0.decimal_places
                    {
                        return Err(EvaluationError::DecimalPrecision);
                    }
                }
                EvaluationInput::Formula { ast } => {
                    FormulaCell::from_draft(
                        FormulaCellDraft {
                            schema_version: TABLE_FORMULA_SCHEMA_VERSION.into(),
                            owner: cell.coordinate,
                            ast: FormulaAstDraft {
                                schema_version: ast.schema_version().into(),
                                expression: ast.expression().clone(),
                            },
                            cache: FormulaCache::Absent,
                            number_format: FormulaNumberFormat::General,
                        },
                        dimensions,
                        original_limits,
                    )
                    .map_err(|_| EvaluationError::OriginalAst)?;
                }
                EvaluationInput::Unavailable => (),
            }
            if cells.insert(key(cell.coordinate), cell.input).is_some() {
                return Err(EvaluationError::DuplicateCell);
            }
        }
        Ok(Self {
            dimensions,
            cells,
            limits,
            input_sha256,
        })
    }
    /// Evaluates all requested formula cells atomically, in caller order, with dependency memoization.
    /// # Errors
    /// Rejects cycles, missing numeric values, duplicate targets, work/depth/arithmetic limits.
    pub fn evaluate(
        &self,
        targets: &[CellCoordinate],
    ) -> Result<FormulaEvaluation, EvaluationError> {
        if targets.is_empty() {
            return Err(EvaluationError::EmptyTargets);
        }
        if targets.len() > self.limits.0.cells {
            return Err(EvaluationError::Grid);
        }
        let mut seen = BTreeSet::new();
        for target in targets {
            if !seen.insert(key(*target)) {
                return Err(EvaluationError::DuplicateTarget);
            }
            if !matches!(
                self.cells.get(&key(*target)),
                Some(EvaluationInput::Formula { .. })
            ) {
                return Err(EvaluationError::NotFormulaTarget);
            }
        }
        let mut engine = Engine {
            context: self,
            memo: BTreeMap::new(),
            visiting: BTreeSet::new(),
            work: 0,
            reused: 0,
        };
        let mut values = Vec::new();
        for coordinate in targets {
            values.push(EvaluatedFormulaValue {
                coordinate: *coordinate,
                value: engine.cell(*coordinate, 0)?,
            });
        }
        let result_sha256 = hash_bounded(&values, self.limits.0.result_bytes)
            .map_err(|_| EvaluationError::ResultLimit)?;
        Ok(FormulaEvaluation {
            receipt: EvaluationReceipt {
                profile: FORMULA_EVALUATION_PROFILE,
                qualification: FORMULA_EVALUATION_SCOPE,
                input_sha256: self.input_sha256,
                result_sha256,
                evaluated_targets: targets.len(),
                computed_cells: engine.memo.len(),
                reused_dependency_values: engine.reused,
                work_steps: engine.work,
            },
            values,
        })
    }
}
fn key(c: CellCoordinate) -> (u32, u32) {
    (c.row, c.column)
}
struct Engine<'a, 'input> {
    context: &'a FormulaEvaluationContext<'input>,
    memo: BTreeMap<(u32, u32), FormulaDecimal>,
    visiting: BTreeSet<(u32, u32)>,
    work: usize,
    reused: usize,
}
impl Engine<'_, '_> {
    fn tick(&mut self, depth: usize) -> Result<(), EvaluationError> {
        if depth > self.context.limits.0.depth {
            return Err(EvaluationError::DepthLimit);
        }
        self.work = self.work.checked_add(1).ok_or(EvaluationError::WorkLimit)?;
        if self.work > self.context.limits.0.work {
            return Err(EvaluationError::WorkLimit);
        }
        Ok(())
    }
    fn cell(&mut self, c: CellCoordinate, depth: usize) -> Result<FormulaDecimal, EvaluationError> {
        self.tick(depth)?;
        if c.row >= self.context.dimensions.rows || c.column >= self.context.dimensions.columns {
            return Err(EvaluationError::OutOfBounds);
        }
        if let Some(value) = self.memo.get(&key(c)) {
            self.reused += 1;
            return Ok(*value);
        }
        if !self.visiting.insert(key(c)) {
            return Err(EvaluationError::Cycle);
        }
        let result = match self.context.cells.get(&key(c)).copied() {
            Some(EvaluationInput::Decimal { value }) => Ok(value),
            Some(EvaluationInput::Formula { ast }) => self.scalar(ast.expression(), depth + 1),
            Some(EvaluationInput::Unavailable) | None => Err(EvaluationError::MissingValue),
        };
        self.visiting.remove(&key(c));
        let value = result?;
        self.memo.insert(key(c), value);
        Ok(value)
    }
    fn scalar(
        &mut self,
        expression: &FormulaExpression,
        depth: usize,
    ) -> Result<FormulaDecimal, EvaluationError> {
        self.tick(depth)?;
        let places = self.context.limits.0.decimal_places;
        match expression {
            FormulaExpression::Decimal { value } => exact::bound(*value, places),
            FormulaExpression::Cell { reference } => self.cell(
                CellCoordinate {
                    row: reference.row,
                    column: reference.column,
                },
                depth + 1,
            ),
            FormulaExpression::Range { .. } => Err(EvaluationError::RangeRequiresAggregate),
            FormulaExpression::Unary { operator, operand } => {
                let value = self.scalar(operand, depth + 1)?;
                match operator {
                    FormulaUnaryOperator::Positive => Ok(value),
                    FormulaUnaryOperator::Negative => exact::negate(value, places),
                }
            }
            FormulaExpression::Binary {
                operator,
                left,
                right,
            } => {
                let left = self.scalar(left, depth + 1)?;
                let right = self.scalar(right, depth + 1)?;
                if *operator == FormulaBinaryOperator::Power {
                    let steps =
                        exact::exponent_steps(right, self.context.limits.0.integer_exponent)?;
                    for _ in 0..steps {
                        self.tick(depth)?;
                    }
                    exact::power(left, right, places)
                } else {
                    exact::binary(*operator, left, right, places)
                }
            }
            FormulaExpression::Function {
                function,
                arguments,
            } => self.aggregate(*function, arguments, depth + 1),
        }
    }
    fn aggregate(
        &mut self,
        function: FormulaFunction,
        arguments: &[FormulaExpression],
        depth: usize,
    ) -> Result<FormulaDecimal, EvaluationError> {
        let mut result = exact::Accumulator::new(function);
        let mut count = 0i64;
        for arg in arguments {
            if let FormulaExpression::Range { range } = arg {
                self.tick(depth)?;
                for row in range.start.row..=range.end.row {
                    for column in range.start.column..=range.end.column {
                        let value = self.cell(CellCoordinate { row, column }, depth + 1)?;
                        result.push(value)?;
                        count = count.checked_add(1).ok_or(EvaluationError::Overflow)?;
                    }
                }
            } else {
                let value = self.scalar(arg, depth)?;
                result.push(value)?;
                count = count.checked_add(1).ok_or(EvaluationError::Overflow)?;
            }
        }
        if count == 0 {
            return Err(EvaluationError::MissingValue);
        }
        result.finish(function, count, self.context.limits.0.decimal_places)
    }
}

struct HashWriter {
    digest: Sha256,
    written: usize,
    limit: usize,
}
impl io::Write for HashWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let next = self
            .written
            .checked_add(bytes.len())
            .filter(|n| *n <= self.limit)
            .ok_or_else(|| io::Error::other("bounded formula evidence"))?;
        self.digest.update(bytes);
        self.written = next;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn hash_bounded<T: Serialize>(value: &T, limit: usize) -> Result<[u8; 32], serde_json::Error> {
    let mut writer = HashWriter {
        digest: Sha256::new(),
        written: 0,
        limit,
    };
    serde_json::to_writer(&mut writer, value)?;
    Ok(writer.digest.finalize().into())
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Error)]
pub enum EvaluationError {
    #[error("formula evaluation limits rejected")]
    InvalidLimits,
    #[error("formula evaluation exact grid rejected")]
    Grid,
    #[error("formula evaluation original AST rejected")]
    OriginalAst,
    #[error("formula evaluation duplicate cell rejected")]
    DuplicateCell,
    #[error("formula evaluation unavailable numeric input")]
    MissingValue,
    #[error("formula evaluation coordinate out of bounds")]
    OutOfBounds,
    #[error("formula evaluation target is not a formula")]
    NotFormulaTarget,
    #[error("formula evaluation duplicate target rejected")]
    DuplicateTarget,
    #[error("formula evaluation targets are empty")]
    EmptyTargets,
    #[error("formula evaluation cyclic dependency rejected")]
    Cycle,
    #[error("formula evaluation work budget exhausted")]
    WorkLimit,
    #[error("formula evaluation depth budget exhausted")]
    DepthLimit,
    #[error("formula evaluation input byte budget exhausted")]
    InputLimit,
    #[error("formula evaluation result byte budget exhausted")]
    ResultLimit,
    #[error("formula evaluation nonterminating decimal rejected")]
    NonTerminatingDecimal,
    #[error("formula evaluation decimal precision rejected")]
    DecimalPrecision,
    #[error("formula evaluation exact arithmetic overflow")]
    Overflow,
    #[error("formula evaluation division by zero")]
    DivisionByZero,
    #[error("formula evaluation fractional or over-limit exponent rejected")]
    UnsupportedExponent,
    #[error("formula evaluation zero to zero power rejected")]
    UndefinedPower,
    #[error("formula evaluation range requires aggregate context")]
    RangeRequiresAggregate,
}
