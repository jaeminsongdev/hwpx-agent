use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization as _;

use crate::CellCoordinate;

pub const TABLE_FORMULA_SCHEMA_VERSION: &str = "hwpx-agent.table-formula/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FormulaLimitConfig {
    pub input_bytes: usize,
    pub nodes: usize,
    pub depth: usize,
    pub function_arguments: usize,
    pub cache_text_bytes: usize,
    pub rows: u32,
    pub columns: u32,
    pub decimal_places: u8,
    pub serialized_bytes: usize,
}

impl Default for FormulaLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 8 * 1024,
            nodes: 2_048,
            depth: 64,
            function_arguments: 256,
            cache_text_bytes: 4 * 1024,
            rows: 10_000,
            columns: 1_024,
            decimal_places: 12,
            serialized_bytes: 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct FormulaLimits(FormulaLimitConfig);

impl FormulaLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 64 * 1024;
    pub const HARD_MAX_NODES: usize = 65_536;
    pub const HARD_MAX_DEPTH: usize = 256;
    pub const HARD_MAX_FUNCTION_ARGUMENTS: usize = 4_096;
    pub const HARD_MAX_CACHE_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_ROWS: u32 = 10_000;
    pub const HARD_MAX_COLUMNS: u32 = 1_024;
    pub const HARD_MAX_DECIMAL_PLACES: u8 = 18;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 16 * 1024 * 1024;

    /// Creates finite limits for the P06-06 pure formula boundary.
    ///
    /// # Errors
    ///
    /// Returns [`FormulaError::InvalidLimit`] when any limit is zero or exceeds its hard ceiling.
    pub fn new(config: FormulaLimitConfig) -> Result<Self, FormulaError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.nodes == 0
            || config.nodes > Self::HARD_MAX_NODES
            || config.depth == 0
            || config.depth > Self::HARD_MAX_DEPTH
            || config.function_arguments == 0
            || config.function_arguments > Self::HARD_MAX_FUNCTION_ARGUMENTS
            || config.cache_text_bytes == 0
            || config.cache_text_bytes > Self::HARD_MAX_CACHE_TEXT_BYTES
            || config.rows == 0
            || config.rows > Self::HARD_MAX_ROWS
            || config.columns == 0
            || config.columns > Self::HARD_MAX_COLUMNS
            || config.decimal_places > Self::HARD_MAX_DECIMAL_PLACES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(FormulaError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> FormulaLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormulaReferenceKind {
    Relative,
    Absolute,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormulaCellReference {
    pub row: u32,
    pub column: u32,
    pub row_kind: FormulaReferenceKind,
    pub column_kind: FormulaReferenceKind,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormulaRange {
    pub start: FormulaCellReference,
    pub end: FormulaCellReference,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormulaGridDimensions {
    pub rows: u32,
    pub columns: u32,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormulaUnaryOperator {
    Positive,
    Negative,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormulaBinaryOperator {
    Add,
    Subtract,
    Multiply,
    Divide,
    Power,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormulaFunction {
    Sum,
    Average,
    Product,
}

#[derive(Clone, Copy, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormulaDecimal {
    coefficient: i64,
    scale: u8,
}

impl FormulaDecimal {
    /// Creates an exact base-10 value and removes redundant trailing fractional zeroes.
    #[must_use]
    pub const fn new(mut coefficient: i64, mut scale: u8) -> Self {
        while scale > 0 && coefficient % 10 == 0 {
            coefficient /= 10;
            scale -= 1;
        }
        Self { coefficient, scale }
    }

    #[must_use]
    pub const fn coefficient(self) -> i64 {
        self.coefficient
    }

    #[must_use]
    pub const fn scale(self) -> u8 {
        self.scale
    }

    fn is_canonical(self) -> bool {
        self.scale == 0 || self.coefficient % 10 != 0
    }

    fn write_canonical(self, output: &mut String) {
        if self.scale == 0 {
            output.push_str(&self.coefficient.to_string());
            return;
        }
        let negative = self.coefficient < 0;
        let digits = self.coefficient.unsigned_abs().to_string();
        if negative {
            output.push('-');
        }
        let scale = usize::from(self.scale);
        if digits.len() <= scale {
            output.push_str("0.");
            for _ in 0..(scale - digits.len()) {
                output.push('0');
            }
            output.push_str(&digits);
        } else {
            let split = digits.len() - scale;
            output.push_str(&digits[..split]);
            output.push('.');
            output.push_str(&digits[split..]);
        }
    }
}

impl fmt::Debug for FormulaDecimal {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormulaDecimal(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormulaExpression {
    Decimal {
        value: FormulaDecimal,
    },
    Cell {
        reference: FormulaCellReference,
    },
    Range {
        range: FormulaRange,
    },
    Unary {
        operator: FormulaUnaryOperator,
        operand: Box<FormulaExpression>,
    },
    Binary {
        operator: FormulaBinaryOperator,
        left: Box<FormulaExpression>,
        right: Box<FormulaExpression>,
    },
    Function {
        function: FormulaFunction,
        arguments: Vec<FormulaExpression>,
    },
}

impl fmt::Debug for FormulaExpression {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormulaExpression(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormulaAstDraft {
    pub schema_version: String,
    pub expression: FormulaExpression,
}

impl fmt::Debug for FormulaAstDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormulaAstDraft")
            .field("schema_version", &self.schema_version)
            .field("expression", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormulaAst {
    schema_version: &'static str,
    expression: FormulaExpression,
}

impl FormulaAst {
    /// Validates and canonicalizes a typed formula draft.
    ///
    /// # Errors
    ///
    /// Rejects the wrong version, non-canonical numbers, invalid references/ranges, or finite-limit
    /// violations.
    pub fn from_draft(draft: FormulaAstDraft, limits: FormulaLimits) -> Result<Self, FormulaError> {
        if draft.schema_version != TABLE_FORMULA_SCHEMA_VERSION {
            return Err(FormulaError::UnsupportedVersion);
        }
        validate_expression(&draft.expression, limits)?;
        let ast = Self {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION,
            expression: draft.expression,
        };
        let _ = ast.canonical_json(limits)?;
        Ok(ast)
    }

    /// Parses the admitted locale-neutral formula grammar.
    ///
    /// The grammar accepts decimal literals, A1 references with independent `$` row/column
    /// anchors, rectangular ranges, arithmetic, and exact `SUM`, `AVG`, and `PRODUCT` functions.
    ///
    /// # Errors
    ///
    /// Rejects malformed, non-ASCII, ambiguous, unsupported, or over-limit source text.
    pub fn parse(source: &str, limits: FormulaLimits) -> Result<Self, FormulaError> {
        if source.is_empty() || source.len() > limits.0.input_bytes || !source.is_ascii() {
            return Err(FormulaError::InputLimitOrEncoding);
        }
        let expression = Parser::new(source.as_bytes(), limits).parse()?;
        Self::from_draft(
            FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression,
            },
            limits,
        )
    }

    /// Deserializes and validates a typed formula document.
    ///
    /// # Errors
    ///
    /// Rejects empty or oversized bytes, malformed JSON, unknown fields, unsupported versions,
    /// invalid expressions, and outputs that exceed the configured serialization bound.
    pub fn from_json(bytes: &[u8], limits: FormulaLimits) -> Result<Self, FormulaError> {
        if bytes.is_empty() || bytes.len() > limits.0.serialized_bytes {
            return Err(FormulaError::InputLimitOrEncoding);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| FormulaError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub const fn expression(&self) -> &FormulaExpression {
        &self.expression
    }

    /// Compiles the AST to one deterministic, fully parenthesized formula string.
    ///
    /// # Errors
    ///
    /// Returns an error if canonical reference rendering overflows or the result exceeds the
    /// configured formula-source bound.
    pub fn canonical_formula(&self, limits: FormulaLimits) -> Result<String, FormulaError> {
        let mut output = String::new();
        write_expression(&self.expression, &mut output)?;
        if output.is_empty() || output.len() > limits.0.input_bytes {
            return Err(FormulaError::OutputLimit);
        }
        Ok(output)
    }

    /// Serializes the validated AST into bounded canonical JSON.
    ///
    /// # Errors
    ///
    /// Returns an error if serialization fails or the canonical bytes exceed the output bound.
    pub fn canonical_json(&self, limits: FormulaLimits) -> Result<Vec<u8>, FormulaError> {
        let bytes = serde_json::to_vec(self).map_err(|_| FormulaError::Serialization)?;
        if bytes.len() > limits.0.serialized_bytes {
            return Err(FormulaError::OutputLimit);
        }
        Ok(bytes)
    }

    /// Returns SHA-256 over canonical JSON.
    ///
    /// # Errors
    ///
    /// Propagates canonical JSON serialization and output-bound failures.
    pub fn canonical_sha256(&self, limits: FormulaLimits) -> Result<[u8; 32], FormulaError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    /// Rebases relative axes when a formula is copied from one owner cell to another.
    /// Absolute axes remain fixed. Any underflow or target-grid escape fails atomically.
    ///
    /// # Errors
    ///
    /// Rejects invalid exact dimensions, owners or references outside those dimensions, relative
    /// shifts that escape the grid, and any resulting invalid or over-limit AST.
    pub fn rebase(
        &self,
        from: CellCoordinate,
        to: CellCoordinate,
        dimensions: FormulaGridDimensions,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        validate_grid_dimensions(dimensions, limits)?;
        validate_coordinate_dimensions(from, dimensions)?;
        validate_coordinate_dimensions(to, dimensions)?;
        validate_expression_dimensions(&self.expression, dimensions)?;
        let row_delta = i64::from(to.row) - i64::from(from.row);
        let column_delta = i64::from(to.column) - i64::from(from.column);
        let expression = map_expression(&self.expression, &mut |reference| {
            Ok(FormulaCellReference {
                row: rebase_axis(
                    reference.row,
                    reference.row_kind,
                    row_delta,
                    dimensions.rows,
                )?,
                column: rebase_axis(
                    reference.column,
                    reference.column_kind,
                    column_delta,
                    dimensions.columns,
                )?,
                ..reference
            })
        })?;
        let result = Self::from_draft(
            FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression,
            },
            limits,
        )?;
        validate_expression_dimensions(&result.expression, dimensions)?;
        Ok(result)
    }

    /// Updates references for one structural row/column insertion or deletion.
    ///
    /// Anchors affect copy/rebase only. Structural edits update both absolute and relative
    /// references so they continue to identify the same surviving cell. A deleted endpoint is
    /// rejected instead of silently emitting a broken reference.
    ///
    /// # Errors
    ///
    /// Rejects invalid dimensions or edits, references outside the exact pre-edit grid, deleted
    /// endpoints, checked-arithmetic failures, and invalid or over-limit results.
    pub fn apply_grid_edit(
        &self,
        edit: FormulaGridEdit,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        let (before, after) = validate_grid_edit(edit, limits)?;
        validate_expression_dimensions(&self.expression, before)?;
        let expression = map_expression(&self.expression, &mut |reference| {
            transform_reference(reference, edit)
        })?;
        let result = Self::from_draft(
            FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression,
            },
            limits,
        )?;
        validate_expression_dimensions(&result.expression, after)?;
        Ok(result)
    }

    /// Transposes every cell reference from an exact `rows x columns` grid into the corresponding
    /// `columns x rows` grid.
    ///
    /// Row and column anchor kinds are axes, not decorations, so they are swapped together with
    /// their indexes. The expression tree, operators and function order remain unchanged.
    ///
    /// # Errors
    ///
    /// Rejects invalid or unsupported before/after dimensions, out-of-grid references and any
    /// resulting invalid or over-limit AST.
    pub fn transpose(
        &self,
        before: FormulaGridDimensions,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        validate_grid_dimensions(before, limits)?;
        validate_expression_dimensions(&self.expression, before)?;
        let after = transposed_dimensions(before, limits)?;
        let expression = map_expression(&self.expression, &mut |reference| {
            Ok(FormulaCellReference {
                row: reference.column,
                column: reference.row,
                row_kind: reference.column_kind,
                column_kind: reference.row_kind,
            })
        })?;
        let result = Self::from_draft(
            FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression,
            },
            limits,
        )?;
        validate_expression_dimensions(&result.expression, after)?;
        Ok(result)
    }
}

impl fmt::Debug for FormulaAst {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormulaAst")
            .field("schema_version", &self.schema_version)
            .field("expression", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormulaValue {
    Decimal { value: FormulaDecimal },
    Text { value: String },
    Boolean { value: bool },
    Error { value: FormulaErrorValue },
}

impl fmt::Debug for FormulaValue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("FormulaValue(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormulaErrorValue {
    DivisionByZero,
    InvalidReference,
    InvalidValue,
    Unavailable,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "state", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormulaCache {
    Absent,
    Unverified { value: FormulaValue },
}

impl fmt::Debug for FormulaCache {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let state = match self {
            Self::Absent => "absent",
            Self::Unverified { .. } => "unverified",
        };
        formatter
            .debug_struct("FormulaCache")
            .field("state", &state)
            .field("value", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormulaNumberFormat {
    General,
    Number {
        decimal_places: u8,
        use_grouping: bool,
    },
    Percent {
        decimal_places: u8,
    },
    Scientific {
        decimal_places: u8,
    },
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormulaCachePolicy {
    Preserve,
    Clear,
    Update,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FormulaGridEdit {
    InsertRows {
        before: FormulaGridDimensions,
        index: u32,
        count: u32,
    },
    DeleteRows {
        before: FormulaGridDimensions,
        index: u32,
        count: u32,
    },
    InsertColumns {
        before: FormulaGridDimensions,
        index: u32,
        count: u32,
    },
    DeleteColumns {
        before: FormulaGridDimensions,
        index: u32,
        count: u32,
    },
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FormulaCellDraft {
    pub schema_version: String,
    pub owner: CellCoordinate,
    pub ast: FormulaAstDraft,
    pub cache: FormulaCache,
    pub number_format: FormulaNumberFormat,
}

impl fmt::Debug for FormulaCellDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormulaCellDraft")
            .field("schema_version", &self.schema_version)
            .field("owner", &self.owner)
            .field("ast", &"<redacted>")
            .field("cache", &self.cache)
            .field("number_format", &self.number_format)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct FormulaCell {
    schema_version: &'static str,
    owner: CellCoordinate,
    ast: FormulaAst,
    cache: FormulaCache,
    number_format: FormulaNumberFormat,
}

impl FormulaCell {
    /// Validates one formula, its separate result cache, and number-format state.
    ///
    /// # Errors
    ///
    /// Rejects unsupported versions, invalid exact dimensions, owners or references outside the
    /// exact grid, invalid formulas, unbounded cache data, invalid number formats, and serialized
    /// output above the configured bound.
    pub fn from_draft(
        draft: FormulaCellDraft,
        dimensions: FormulaGridDimensions,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        if draft.schema_version != TABLE_FORMULA_SCHEMA_VERSION {
            return Err(FormulaError::UnsupportedVersion);
        }
        validate_grid_dimensions(dimensions, limits)?;
        validate_coordinate_dimensions(draft.owner, dimensions)?;
        let ast = FormulaAst::from_draft(draft.ast, limits)?;
        validate_expression_dimensions(ast.expression(), dimensions)?;
        validate_number_format(draft.number_format, limits)?;
        validate_cache(&draft.cache, limits)?;
        let cell = Self {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION,
            owner: draft.owner,
            ast,
            cache: draft.cache,
            number_format: draft.number_format,
        };
        let _ = cell.canonical_json(limits)?;
        Ok(cell)
    }

    /// Deserializes and validates a complete formula cell against exact table dimensions.
    ///
    /// # Errors
    ///
    /// Rejects empty or oversized bytes, malformed JSON, unknown fields, unsupported versions,
    /// invalid dimensions, owners or references outside the exact grid, invalid cache/format data,
    /// and outputs above the configured serialization bound.
    pub fn from_json(
        bytes: &[u8],
        dimensions: FormulaGridDimensions,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        if bytes.is_empty() || bytes.len() > limits.0.serialized_bytes {
            return Err(FormulaError::InputLimitOrEncoding);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| FormulaError::InvalidJson)?;
        Self::from_draft(draft, dimensions, limits)
    }

    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub const fn owner(&self) -> CellCoordinate {
        self.owner
    }

    #[must_use]
    pub const fn ast(&self) -> &FormulaAst {
        &self.ast
    }

    #[must_use]
    pub const fn cache(&self) -> &FormulaCache {
        &self.cache
    }

    #[must_use]
    pub const fn number_format(&self) -> FormulaNumberFormat {
        self.number_format
    }

    /// Applies a structural edit to the owner and references under an explicit cache policy.
    ///
    /// `preserve` is accepted only if canonical formula bytes do not change. `clear` accepts no
    /// replacement. `update` requires a separately supplied cache that validates against the new
    /// formula. This pure component admits only absent or explicitly unverified cache values;
    /// target-oracle promotion belongs to a later receipt-verifying adapter.
    ///
    /// # Errors
    ///
    /// Rejects invalid edits, deleted owners or references, cache-policy mismatches, cache
    /// preservation after a formula change, and invalid or over-limit results.
    pub fn apply_grid_edit(
        &self,
        edit: FormulaGridEdit,
        cache_policy: FormulaCachePolicy,
        updated_cache: Option<FormulaCache>,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        let (before, after) = validate_grid_edit(edit, limits)?;
        validate_coordinate_dimensions(self.owner, before)?;
        let owner = transform_coordinate(self.owner, edit)?.ok_or(FormulaError::OwnerDeleted)?;
        validate_coordinate_dimensions(owner, after)?;
        let ast = self.ast.apply_grid_edit(edit, limits)?;
        let before_digest = self.ast.canonical_sha256(limits)?;
        let after_digest = ast.canonical_sha256(limits)?;
        let cache = resolve_cache_policy(
            &self.cache,
            cache_policy,
            updated_cache,
            before_digest == after_digest,
            limits,
        )?;
        Self::from_parts(owner, ast, cache, self.number_format, after, limits)
    }

    /// Rebases a copied formula to a new owner under an explicit cache policy.
    ///
    /// # Errors
    ///
    /// Rejects invalid exact dimensions, owners or references outside the grid, relative shifts
    /// that escape the grid, cache-policy conflicts, and invalid or over-limit results.
    pub fn rebase(
        &self,
        to: CellCoordinate,
        dimensions: FormulaGridDimensions,
        cache_policy: FormulaCachePolicy,
        updated_cache: Option<FormulaCache>,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        let ast = self.ast.rebase(self.owner, to, dimensions, limits)?;
        let before_digest = self.ast.canonical_sha256(limits)?;
        let after_digest = ast.canonical_sha256(limits)?;
        let cache = resolve_cache_policy(
            &self.cache,
            cache_policy,
            updated_cache,
            before_digest == after_digest,
            limits,
        )?;
        Self::from_parts(to, ast, cache, self.number_format, dimensions, limits)
    }

    /// Moves a formula cell and all of its references through a full-table transpose.
    ///
    /// Cache handling is explicit. `preserve` is accepted only when the canonical AST is
    /// unchanged, `clear` removes the unverified cache, and `update` requires a separately supplied
    /// non-absent cache. This component never claims that a cached value was recalculated by
    /// Hangul.
    ///
    /// # Errors
    ///
    /// Rejects invalid dimensions, owners or references, unsupported transposed dimensions,
    /// cache-policy mismatches and any invalid or over-limit result.
    pub fn transpose(
        &self,
        before: FormulaGridDimensions,
        cache_policy: FormulaCachePolicy,
        updated_cache: Option<FormulaCache>,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        validate_grid_dimensions(before, limits)?;
        validate_coordinate_dimensions(self.owner, before)?;
        let after = transposed_dimensions(before, limits)?;
        let owner = CellCoordinate {
            row: self.owner.column,
            column: self.owner.row,
        };
        let ast = self.ast.transpose(before, limits)?;
        let before_digest = self.ast.canonical_sha256(limits)?;
        let after_digest = ast.canonical_sha256(limits)?;
        let cache = resolve_cache_policy(
            &self.cache,
            cache_policy,
            updated_cache,
            before_digest == after_digest,
            limits,
        )?;
        Self::from_parts(owner, ast, cache, self.number_format, after, limits)
    }

    /// Serializes the complete formula cell to bounded canonical JSON.
    ///
    /// # Errors
    ///
    /// Returns an error if serialization fails or the canonical bytes exceed the output bound.
    pub fn canonical_json(&self, limits: FormulaLimits) -> Result<Vec<u8>, FormulaError> {
        let bytes = serde_json::to_vec(self).map_err(|_| FormulaError::Serialization)?;
        if bytes.len() > limits.0.serialized_bytes {
            return Err(FormulaError::OutputLimit);
        }
        Ok(bytes)
    }

    /// Returns SHA-256 over the complete cell's canonical JSON.
    ///
    /// # Errors
    ///
    /// Propagates canonical JSON serialization and output-bound failures.
    pub fn canonical_sha256(&self, limits: FormulaLimits) -> Result<[u8; 32], FormulaError> {
        Ok(Sha256::digest(self.canonical_json(limits)?).into())
    }

    fn from_parts(
        owner: CellCoordinate,
        ast: FormulaAst,
        cache: FormulaCache,
        number_format: FormulaNumberFormat,
        dimensions: FormulaGridDimensions,
        limits: FormulaLimits,
    ) -> Result<Self, FormulaError> {
        validate_grid_dimensions(dimensions, limits)?;
        validate_coordinate_dimensions(owner, dimensions)?;
        validate_expression_dimensions(ast.expression(), dimensions)?;
        validate_number_format(number_format, limits)?;
        validate_cache(&cache, limits)?;
        let cell = Self {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION,
            owner,
            ast,
            cache,
            number_format,
        };
        let _ = cell.canonical_json(limits)?;
        Ok(cell)
    }
}

impl fmt::Debug for FormulaCell {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FormulaCell")
            .field("schema_version", &self.schema_version)
            .field("owner", &self.owner)
            .field("ast", &"<redacted>")
            .field("cache", &self.cache)
            .field("number_format", &self.number_format)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum FormulaError {
    #[error("formula limit is invalid")]
    InvalidLimit,
    #[error("formula schema version is unsupported")]
    UnsupportedVersion,
    #[error("formula source is empty, oversized, or not ASCII")]
    InputLimitOrEncoding,
    #[error("formula syntax is invalid or unsupported")]
    InvalidSyntax,
    #[error("formula JSON is invalid")]
    InvalidJson,
    #[error("formula tree exceeds node, depth, or argument limits")]
    TreeLimit,
    #[error("formula decimal is invalid or non-canonical")]
    InvalidDecimal,
    #[error("formula cell reference is outside the admitted grid")]
    ReferenceOutOfBounds,
    #[error("formula range is reversed or invalid")]
    InvalidRange,
    #[error("formula structural edit is invalid")]
    InvalidGridEdit,
    #[error("formula grid dimensions are invalid")]
    InvalidGridDimensions,
    #[error("formula reference was deleted by the structural edit")]
    ReferenceDeleted,
    #[error("formula owner was deleted by the structural edit")]
    OwnerDeleted,
    #[error("formula reference rebase escaped the grid")]
    RebaseOutOfBounds,
    #[error("formula cache shape or provenance is invalid")]
    InvalidCache,
    #[error("formula cache cannot be preserved after the formula changes")]
    CachePreservationConflict,
    #[error("formula cache policy and supplied replacement disagree")]
    CachePolicyMismatch,
    #[error("formula number format is invalid")]
    InvalidNumberFormat,
    #[error("formula output exceeds its finite bound")]
    OutputLimit,
    #[error("formula serialization failed")]
    Serialization,
    #[error("formula arithmetic or allocation overflowed")]
    Overflow,
}

impl FormulaError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_formula_invalid_limit",
            Self::UnsupportedVersion => "table_formula_unsupported_version",
            Self::InputLimitOrEncoding => "table_formula_input_limit_or_encoding",
            Self::InvalidSyntax => "table_formula_invalid_syntax",
            Self::InvalidJson => "table_formula_invalid_json",
            Self::TreeLimit => "table_formula_tree_limit",
            Self::InvalidDecimal => "table_formula_invalid_decimal",
            Self::ReferenceOutOfBounds => "table_formula_reference_out_of_bounds",
            Self::InvalidRange => "table_formula_invalid_range",
            Self::InvalidGridEdit => "table_formula_invalid_grid_edit",
            Self::InvalidGridDimensions => "table_formula_invalid_grid_dimensions",
            Self::ReferenceDeleted => "table_formula_reference_deleted",
            Self::OwnerDeleted => "table_formula_owner_deleted",
            Self::RebaseOutOfBounds => "table_formula_rebase_out_of_bounds",
            Self::InvalidCache => "table_formula_invalid_cache",
            Self::CachePreservationConflict => "table_formula_cache_preservation_conflict",
            Self::CachePolicyMismatch => "table_formula_cache_policy_mismatch",
            Self::InvalidNumberFormat => "table_formula_invalid_number_format",
            Self::OutputLimit => "table_formula_output_limit",
            Self::Serialization => "table_formula_serialization",
            Self::Overflow => "table_formula_overflow",
        }
    }
}

fn validate_expression(
    expression: &FormulaExpression,
    limits: FormulaLimits,
) -> Result<(), FormulaError> {
    let mut stack = vec![(expression, 1_usize)];
    let mut nodes = 0_usize;
    while let Some((current, depth)) = stack.pop() {
        nodes = nodes.checked_add(1).ok_or(FormulaError::Overflow)?;
        if nodes > limits.0.nodes || depth > limits.0.depth {
            return Err(FormulaError::TreeLimit);
        }
        let next_depth = depth.checked_add(1).ok_or(FormulaError::Overflow)?;
        match current {
            FormulaExpression::Decimal { value } => {
                if value.coefficient < 0
                    || value.scale > limits.0.decimal_places
                    || !value.is_canonical()
                {
                    return Err(FormulaError::InvalidDecimal);
                }
            }
            FormulaExpression::Cell { reference } => validate_reference(*reference, limits)?,
            FormulaExpression::Range { range } => validate_range(*range, limits)?,
            FormulaExpression::Unary { operand, .. } => stack.push((operand, next_depth)),
            FormulaExpression::Binary { left, right, .. } => {
                stack.push((right, next_depth));
                stack.push((left, next_depth));
            }
            FormulaExpression::Function { arguments, .. } => {
                if arguments.is_empty() || arguments.len() > limits.0.function_arguments {
                    return Err(FormulaError::TreeLimit);
                }
                for argument in arguments.iter().rev() {
                    stack.push((argument, next_depth));
                }
            }
        }
    }
    Ok(())
}

fn validate_expression_dimensions(
    expression: &FormulaExpression,
    dimensions: FormulaGridDimensions,
) -> Result<(), FormulaError> {
    let mut stack = vec![expression];
    while let Some(current) = stack.pop() {
        match current {
            FormulaExpression::Decimal { .. } => {}
            FormulaExpression::Cell { reference } => {
                validate_reference_dimensions(*reference, dimensions)?;
            }
            FormulaExpression::Range { range } => {
                validate_reference_dimensions(range.start, dimensions)?;
                validate_reference_dimensions(range.end, dimensions)?;
            }
            FormulaExpression::Unary { operand, .. } => stack.push(operand),
            FormulaExpression::Binary { left, right, .. } => {
                stack.push(right);
                stack.push(left);
            }
            FormulaExpression::Function { arguments, .. } => {
                stack.extend(arguments.iter().rev());
            }
        }
    }
    Ok(())
}

fn validate_reference_dimensions(
    reference: FormulaCellReference,
    dimensions: FormulaGridDimensions,
) -> Result<(), FormulaError> {
    validate_coordinate_dimensions(
        CellCoordinate {
            row: reference.row,
            column: reference.column,
        },
        dimensions,
    )
}

fn validate_coordinate_dimensions(
    coordinate: CellCoordinate,
    dimensions: FormulaGridDimensions,
) -> Result<(), FormulaError> {
    if coordinate.row >= dimensions.rows || coordinate.column >= dimensions.columns {
        return Err(FormulaError::ReferenceOutOfBounds);
    }
    Ok(())
}

fn validate_grid_dimensions(
    dimensions: FormulaGridDimensions,
    limits: FormulaLimits,
) -> Result<(), FormulaError> {
    if dimensions.rows == 0
        || dimensions.columns == 0
        || dimensions.rows > limits.0.rows
        || dimensions.columns > limits.0.columns
    {
        return Err(FormulaError::InvalidGridDimensions);
    }
    Ok(())
}

fn validate_reference(
    reference: FormulaCellReference,
    limits: FormulaLimits,
) -> Result<(), FormulaError> {
    if reference.row >= limits.0.rows || reference.column >= limits.0.columns {
        return Err(FormulaError::ReferenceOutOfBounds);
    }
    Ok(())
}

fn validate_range(range: FormulaRange, limits: FormulaLimits) -> Result<(), FormulaError> {
    validate_reference(range.start, limits)?;
    validate_reference(range.end, limits)?;
    if range.start.row > range.end.row || range.start.column > range.end.column {
        return Err(FormulaError::InvalidRange);
    }
    Ok(())
}

fn validate_number_format(
    format: FormulaNumberFormat,
    limits: FormulaLimits,
) -> Result<(), FormulaError> {
    let places = match format {
        FormulaNumberFormat::General => return Ok(()),
        FormulaNumberFormat::Number { decimal_places, .. }
        | FormulaNumberFormat::Percent { decimal_places }
        | FormulaNumberFormat::Scientific { decimal_places } => decimal_places,
    };
    if places > limits.0.decimal_places {
        return Err(FormulaError::InvalidNumberFormat);
    }
    Ok(())
}

fn validate_value(value: &FormulaValue, limits: FormulaLimits) -> Result<(), FormulaError> {
    match value {
        FormulaValue::Decimal { value } => {
            if value.scale > limits.0.decimal_places || !value.is_canonical() {
                return Err(FormulaError::InvalidDecimal);
            }
        }
        FormulaValue::Text { value } => {
            if value.len() > limits.0.cache_text_bytes || value.nfc().collect::<String>() != *value
            {
                return Err(FormulaError::InvalidCache);
            }
        }
        FormulaValue::Boolean { .. } | FormulaValue::Error { .. } => {}
    }
    Ok(())
}

fn validate_cache(cache: &FormulaCache, limits: FormulaLimits) -> Result<(), FormulaError> {
    match cache {
        FormulaCache::Absent => Ok(()),
        FormulaCache::Unverified { value } => validate_value(value, limits),
    }
}

fn resolve_cache_policy(
    current: &FormulaCache,
    policy: FormulaCachePolicy,
    updated: Option<FormulaCache>,
    formula_unchanged: bool,
    limits: FormulaLimits,
) -> Result<FormulaCache, FormulaError> {
    match (policy, updated) {
        (FormulaCachePolicy::Preserve, None) => {
            if !formula_unchanged {
                return Err(FormulaError::CachePreservationConflict);
            }
            Ok(current.clone())
        }
        (FormulaCachePolicy::Clear, None) => Ok(FormulaCache::Absent),
        (FormulaCachePolicy::Update, Some(cache)) => {
            if matches!(cache, FormulaCache::Absent) {
                return Err(FormulaError::CachePolicyMismatch);
            }
            validate_cache(&cache, limits)?;
            Ok(cache)
        }
        _ => Err(FormulaError::CachePolicyMismatch),
    }
}

fn map_expression<F>(
    expression: &FormulaExpression,
    transform: &mut F,
) -> Result<FormulaExpression, FormulaError>
where
    F: FnMut(FormulaCellReference) -> Result<FormulaCellReference, FormulaError>,
{
    Ok(match expression {
        FormulaExpression::Decimal { value } => FormulaExpression::Decimal { value: *value },
        FormulaExpression::Cell { reference } => FormulaExpression::Cell {
            reference: transform(*reference)?,
        },
        FormulaExpression::Range { range } => FormulaExpression::Range {
            range: FormulaRange {
                start: transform(range.start)?,
                end: transform(range.end)?,
            },
        },
        FormulaExpression::Unary { operator, operand } => FormulaExpression::Unary {
            operator: *operator,
            operand: Box::new(map_expression(operand, transform)?),
        },
        FormulaExpression::Binary {
            operator,
            left,
            right,
        } => FormulaExpression::Binary {
            operator: *operator,
            left: Box::new(map_expression(left, transform)?),
            right: Box::new(map_expression(right, transform)?),
        },
        FormulaExpression::Function {
            function,
            arguments,
        } => FormulaExpression::Function {
            function: *function,
            arguments: arguments
                .iter()
                .map(|argument| map_expression(argument, transform))
                .collect::<Result<Vec<_>, _>>()?,
        },
    })
}

fn rebase_axis(
    index: u32,
    kind: FormulaReferenceKind,
    delta: i64,
    bound: u32,
) -> Result<u32, FormulaError> {
    if kind == FormulaReferenceKind::Absolute {
        return Ok(index);
    }
    let shifted = i64::from(index)
        .checked_add(delta)
        .ok_or(FormulaError::Overflow)?;
    if shifted < 0 || shifted >= i64::from(bound) {
        return Err(FormulaError::RebaseOutOfBounds);
    }
    u32::try_from(shifted).map_err(|_| FormulaError::Overflow)
}

fn validate_grid_edit(
    edit: FormulaGridEdit,
    limits: FormulaLimits,
) -> Result<(FormulaGridDimensions, FormulaGridDimensions), FormulaError> {
    let (before, index, count, rows, insertion) = match edit {
        FormulaGridEdit::InsertRows {
            before,
            index,
            count,
        } => (before, index, count, true, true),
        FormulaGridEdit::DeleteRows {
            before,
            index,
            count,
        } => (before, index, count, true, false),
        FormulaGridEdit::InsertColumns {
            before,
            index,
            count,
        } => (before, index, count, false, true),
        FormulaGridEdit::DeleteColumns {
            before,
            index,
            count,
        } => (before, index, count, false, false),
    };
    if before.rows == 0
        || before.columns == 0
        || before.rows > limits.0.rows
        || before.columns > limits.0.columns
        || count == 0
    {
        return Err(FormulaError::InvalidGridEdit);
    }
    let bound = if rows { before.rows } else { before.columns };
    let after_bound = if insertion {
        if index > bound {
            return Err(FormulaError::InvalidGridEdit);
        }
        bound
            .checked_add(count)
            .ok_or(FormulaError::InvalidGridEdit)?
    } else {
        let end = index
            .checked_add(count)
            .ok_or(FormulaError::InvalidGridEdit)?;
        if index >= bound || end > bound || count == bound {
            return Err(FormulaError::InvalidGridEdit);
        }
        bound
            .checked_sub(count)
            .ok_or(FormulaError::InvalidGridEdit)?
    };
    if (rows && after_bound > limits.0.rows) || (!rows && after_bound > limits.0.columns) {
        return Err(FormulaError::InvalidGridEdit);
    }
    let after = if rows {
        FormulaGridDimensions {
            rows: after_bound,
            columns: before.columns,
        }
    } else {
        FormulaGridDimensions {
            rows: before.rows,
            columns: after_bound,
        }
    };
    Ok((before, after))
}

fn transposed_dimensions(
    before: FormulaGridDimensions,
    limits: FormulaLimits,
) -> Result<FormulaGridDimensions, FormulaError> {
    let after = FormulaGridDimensions {
        rows: before.columns,
        columns: before.rows,
    };
    validate_grid_dimensions(after, limits)?;
    Ok(after)
}

fn transform_reference(
    reference: FormulaCellReference,
    edit: FormulaGridEdit,
) -> Result<FormulaCellReference, FormulaError> {
    let coordinate = transform_coordinate(
        CellCoordinate {
            row: reference.row,
            column: reference.column,
        },
        edit,
    )?
    .ok_or(FormulaError::ReferenceDeleted)?;
    Ok(FormulaCellReference {
        row: coordinate.row,
        column: coordinate.column,
        ..reference
    })
}

fn transform_coordinate(
    coordinate: CellCoordinate,
    edit: FormulaGridEdit,
) -> Result<Option<CellCoordinate>, FormulaError> {
    let mut result = coordinate;
    match edit {
        FormulaGridEdit::InsertRows { index, count, .. } => {
            if result.row >= index {
                result.row = result
                    .row
                    .checked_add(count)
                    .ok_or(FormulaError::Overflow)?;
            }
        }
        FormulaGridEdit::DeleteRows { index, count, .. } => {
            let end = index.checked_add(count).ok_or(FormulaError::Overflow)?;
            if result.row >= index && result.row < end {
                return Ok(None);
            }
            if result.row >= end {
                result.row = result
                    .row
                    .checked_sub(count)
                    .ok_or(FormulaError::Overflow)?;
            }
        }
        FormulaGridEdit::InsertColumns { index, count, .. } => {
            if result.column >= index {
                result.column = result
                    .column
                    .checked_add(count)
                    .ok_or(FormulaError::Overflow)?;
            }
        }
        FormulaGridEdit::DeleteColumns { index, count, .. } => {
            let end = index.checked_add(count).ok_or(FormulaError::Overflow)?;
            if result.column >= index && result.column < end {
                return Ok(None);
            }
            if result.column >= end {
                result.column = result
                    .column
                    .checked_sub(count)
                    .ok_or(FormulaError::Overflow)?;
            }
        }
    }
    Ok(Some(result))
}

fn write_expression(
    expression: &FormulaExpression,
    output: &mut String,
) -> Result<(), FormulaError> {
    match expression {
        FormulaExpression::Decimal { value } => value.write_canonical(output),
        FormulaExpression::Cell { reference } => write_reference(*reference, output)?,
        FormulaExpression::Range { range } => {
            write_reference(range.start, output)?;
            output.push(':');
            write_reference(range.end, output)?;
        }
        FormulaExpression::Unary { operator, operand } => {
            output.push('(');
            output.push(match operator {
                FormulaUnaryOperator::Positive => '+',
                FormulaUnaryOperator::Negative => '-',
            });
            write_expression(operand, output)?;
            output.push(')');
        }
        FormulaExpression::Binary {
            operator,
            left,
            right,
        } => {
            output.push('(');
            write_expression(left, output)?;
            output.push(match operator {
                FormulaBinaryOperator::Add => '+',
                FormulaBinaryOperator::Subtract => '-',
                FormulaBinaryOperator::Multiply => '*',
                FormulaBinaryOperator::Divide => '/',
                FormulaBinaryOperator::Power => '^',
            });
            write_expression(right, output)?;
            output.push(')');
        }
        FormulaExpression::Function {
            function,
            arguments,
        } => {
            output.push_str(match function {
                FormulaFunction::Sum => "SUM",
                FormulaFunction::Average => "AVG",
                FormulaFunction::Product => "PRODUCT",
            });
            output.push('(');
            for (index, argument) in arguments.iter().enumerate() {
                if index != 0 {
                    output.push(',');
                }
                write_expression(argument, output)?;
            }
            output.push(')');
        }
    }
    Ok(())
}

fn write_reference(
    reference: FormulaCellReference,
    output: &mut String,
) -> Result<(), FormulaError> {
    if reference.column_kind == FormulaReferenceKind::Absolute {
        output.push('$');
    }
    write_column(reference.column, output)?;
    if reference.row_kind == FormulaReferenceKind::Absolute {
        output.push('$');
    }
    let row = reference.row.checked_add(1).ok_or(FormulaError::Overflow)?;
    output.push_str(&row.to_string());
    Ok(())
}

fn write_column(column: u32, output: &mut String) -> Result<(), FormulaError> {
    let mut value = column.checked_add(1).ok_or(FormulaError::Overflow)?;
    let mut reversed = [0_u8; 8];
    let mut length = 0_usize;
    while value > 0 {
        if length >= reversed.len() {
            return Err(FormulaError::Overflow);
        }
        let remainder = (value - 1) % 26;
        reversed[length] = b'A' + u8::try_from(remainder).map_err(|_| FormulaError::Overflow)?;
        length += 1;
        value = (value - 1) / 26;
    }
    for byte in reversed[..length].iter().rev() {
        output.push(char::from(*byte));
    }
    Ok(())
}

struct Parser<'a> {
    source: &'a [u8],
    cursor: usize,
    limits: FormulaLimits,
}

impl<'a> Parser<'a> {
    fn new(source: &'a [u8], limits: FormulaLimits) -> Self {
        Self {
            source,
            cursor: 0,
            limits,
        }
    }

    fn parse(mut self) -> Result<FormulaExpression, FormulaError> {
        self.skip_spaces();
        if self.consume(b'=') {
            self.skip_spaces();
        }
        let expression = self.parse_add_sub(1)?;
        self.skip_spaces();
        if self.cursor != self.source.len() {
            return Err(FormulaError::InvalidSyntax);
        }
        Ok(expression)
    }

    fn parse_add_sub(&mut self, depth: usize) -> Result<FormulaExpression, FormulaError> {
        self.check_depth(depth)?;
        let mut left = self.parse_mul_div(depth + 1)?;
        loop {
            self.skip_spaces();
            let operator = if self.consume(b'+') {
                FormulaBinaryOperator::Add
            } else if self.consume(b'-') {
                FormulaBinaryOperator::Subtract
            } else {
                break;
            };
            let right = self.parse_mul_div(depth + 1)?;
            left = FormulaExpression::Binary {
                operator,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_mul_div(&mut self, depth: usize) -> Result<FormulaExpression, FormulaError> {
        self.check_depth(depth)?;
        let mut left = self.parse_power(depth + 1)?;
        loop {
            self.skip_spaces();
            let operator = if self.consume(b'*') {
                FormulaBinaryOperator::Multiply
            } else if self.consume(b'/') {
                FormulaBinaryOperator::Divide
            } else {
                break;
            };
            let right = self.parse_power(depth + 1)?;
            left = FormulaExpression::Binary {
                operator,
                left: Box::new(left),
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_power(&mut self, depth: usize) -> Result<FormulaExpression, FormulaError> {
        self.check_depth(depth)?;
        let left = self.parse_unary(depth + 1)?;
        self.skip_spaces();
        if self.consume(b'^') {
            let right = self.parse_power(depth + 1)?;
            Ok(FormulaExpression::Binary {
                operator: FormulaBinaryOperator::Power,
                left: Box::new(left),
                right: Box::new(right),
            })
        } else {
            Ok(left)
        }
    }

    fn parse_unary(&mut self, depth: usize) -> Result<FormulaExpression, FormulaError> {
        self.check_depth(depth)?;
        self.skip_spaces();
        if self.consume(b'+') {
            return Ok(FormulaExpression::Unary {
                operator: FormulaUnaryOperator::Positive,
                operand: Box::new(self.parse_unary(depth + 1)?),
            });
        }
        if self.consume(b'-') {
            return Ok(FormulaExpression::Unary {
                operator: FormulaUnaryOperator::Negative,
                operand: Box::new(self.parse_unary(depth + 1)?),
            });
        }
        self.parse_primary(depth + 1)
    }

    fn parse_primary(&mut self, depth: usize) -> Result<FormulaExpression, FormulaError> {
        self.check_depth(depth)?;
        self.skip_spaces();
        if self.consume(b'(') {
            let expression = self.parse_add_sub(depth + 1)?;
            self.skip_spaces();
            if !self.consume(b')') {
                return Err(FormulaError::InvalidSyntax);
            }
            return Ok(expression);
        }
        if self.peek().is_some_and(|byte| byte.is_ascii_digit()) {
            return self.parse_decimal();
        }
        let checkpoint = self.cursor;
        if self
            .peek()
            .is_some_and(|byte| byte == b'$' || byte.is_ascii_alphabetic())
        {
            if self.peek().is_some_and(|byte| byte.is_ascii_alphabetic()) {
                let identifier = self.parse_letters()?;
                self.skip_spaces();
                if self.consume(b'(') {
                    return self.parse_function(identifier, depth + 1);
                }
            }
            self.cursor = checkpoint;
            let start = self.parse_reference()?;
            self.skip_spaces();
            if self.consume(b':') {
                self.skip_spaces();
                let end = self.parse_reference()?;
                return Ok(FormulaExpression::Range {
                    range: FormulaRange { start, end },
                });
            }
            return Ok(FormulaExpression::Cell { reference: start });
        }
        Err(FormulaError::InvalidSyntax)
    }

    fn parse_decimal(&mut self) -> Result<FormulaExpression, FormulaError> {
        let start = self.cursor;
        while self.peek().is_some_and(|byte| byte.is_ascii_digit()) {
            self.cursor += 1;
        }
        let integer_end = self.cursor;
        let mut scale = 0_u8;
        if self.consume(b'.') {
            let fractional_start = self.cursor;
            while self.peek().is_some_and(|byte| byte.is_ascii_digit()) {
                self.cursor += 1;
            }
            if self.cursor == fractional_start {
                return Err(FormulaError::InvalidSyntax);
            }
            scale = u8::try_from(self.cursor - fractional_start)
                .map_err(|_| FormulaError::InvalidDecimal)?;
        }
        if scale > self.limits.0.decimal_places {
            return Err(FormulaError::InvalidDecimal);
        }
        let mut digits = Vec::with_capacity(self.cursor - start);
        digits.extend_from_slice(&self.source[start..integer_end]);
        if scale > 0 {
            digits.extend_from_slice(&self.source[integer_end + 1..self.cursor]);
        }
        let text = std::str::from_utf8(&digits).map_err(|_| FormulaError::InvalidDecimal)?;
        let coefficient = text
            .parse::<i64>()
            .map_err(|_| FormulaError::InvalidDecimal)?;
        Ok(FormulaExpression::Decimal {
            value: FormulaDecimal::new(coefficient, scale),
        })
    }

    fn parse_reference(&mut self) -> Result<FormulaCellReference, FormulaError> {
        let column_kind = if self.consume(b'$') {
            FormulaReferenceKind::Absolute
        } else {
            FormulaReferenceKind::Relative
        };
        let letters = self.parse_letters()?;
        let column = parse_column(letters)?;
        let row_kind = if self.consume(b'$') {
            FormulaReferenceKind::Absolute
        } else {
            FormulaReferenceKind::Relative
        };
        let row_start = self.cursor;
        while self.peek().is_some_and(|byte| byte.is_ascii_digit()) {
            self.cursor += 1;
        }
        if self.cursor == row_start {
            return Err(FormulaError::InvalidSyntax);
        }
        let row_text = std::str::from_utf8(&self.source[row_start..self.cursor])
            .map_err(|_| FormulaError::InvalidSyntax)?;
        let one_based_row = row_text
            .parse::<u32>()
            .map_err(|_| FormulaError::InvalidSyntax)?;
        let row = one_based_row
            .checked_sub(1)
            .ok_or(FormulaError::InvalidSyntax)?;
        let reference = FormulaCellReference {
            row,
            column,
            row_kind,
            column_kind,
        };
        validate_reference(reference, self.limits)?;
        Ok(reference)
    }

    fn parse_function(
        &mut self,
        identifier: &'a [u8],
        depth: usize,
    ) -> Result<FormulaExpression, FormulaError> {
        let function = if identifier.eq_ignore_ascii_case(b"SUM") {
            FormulaFunction::Sum
        } else if identifier.eq_ignore_ascii_case(b"AVG") {
            FormulaFunction::Average
        } else if identifier.eq_ignore_ascii_case(b"PRODUCT") {
            FormulaFunction::Product
        } else {
            return Err(FormulaError::InvalidSyntax);
        };
        let mut arguments = Vec::new();
        self.skip_spaces();
        if self.peek() == Some(b')') {
            return Err(FormulaError::InvalidSyntax);
        }
        loop {
            if arguments.len() >= self.limits.0.function_arguments {
                return Err(FormulaError::TreeLimit);
            }
            arguments.push(self.parse_add_sub(depth + 1)?);
            self.skip_spaces();
            if self.consume(b')') {
                break;
            }
            if !self.consume(b',') {
                return Err(FormulaError::InvalidSyntax);
            }
            self.skip_spaces();
            if self.peek() == Some(b')') {
                return Err(FormulaError::InvalidSyntax);
            }
        }
        Ok(FormulaExpression::Function {
            function,
            arguments,
        })
    }

    fn parse_letters(&mut self) -> Result<&'a [u8], FormulaError> {
        let start = self.cursor;
        while self.peek().is_some_and(|byte| byte.is_ascii_alphabetic()) {
            self.cursor += 1;
        }
        if self.cursor == start {
            return Err(FormulaError::InvalidSyntax);
        }
        Ok(&self.source[start..self.cursor])
    }

    fn check_depth(&self, depth: usize) -> Result<(), FormulaError> {
        if depth > self.limits.0.depth {
            return Err(FormulaError::TreeLimit);
        }
        Ok(())
    }

    fn skip_spaces(&mut self) {
        while self.peek().is_some_and(|byte| byte.is_ascii_whitespace()) {
            self.cursor += 1;
        }
    }

    fn peek(&self) -> Option<u8> {
        self.source.get(self.cursor).copied()
    }

    fn consume(&mut self, expected: u8) -> bool {
        if self.peek() == Some(expected) {
            self.cursor += 1;
            true
        } else {
            false
        }
    }
}

fn parse_column(letters: &[u8]) -> Result<u32, FormulaError> {
    let mut value = 0_u32;
    for byte in letters {
        let upper = byte.to_ascii_uppercase();
        if !upper.is_ascii_uppercase() {
            return Err(FormulaError::InvalidSyntax);
        }
        value = value
            .checked_mul(26)
            .and_then(|current| current.checked_add(u32::from(upper - b'A' + 1)))
            .ok_or(FormulaError::Overflow)?;
    }
    value.checked_sub(1).ok_or(FormulaError::InvalidSyntax)
}
