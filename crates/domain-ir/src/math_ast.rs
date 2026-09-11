use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization as _;

pub const MATH_AST_SCHEMA_VERSION: &str = "hwpx-agent.math-ast/v1";
pub const MATH_AST_NORMALIZATION_VERSION: &str = "hwpx-agent.math-ast-normalization/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct MathAstLimitConfig {
    pub source_bytes: u32,
    pub nodes: usize,
    pub depth: usize,
    pub children_per_node: usize,
    pub matrix_rows: usize,
    pub matrix_columns: usize,
    pub string_bytes: usize,
    pub total_string_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for MathAstLimitConfig {
    fn default() -> Self {
        Self {
            source_bytes: 1024 * 1024,
            nodes: 8_192,
            depth: 128,
            children_per_node: 512,
            matrix_rows: 256,
            matrix_columns: 256,
            string_bytes: 64 * 1024,
            total_string_bytes: 1024 * 1024,
            serialized_bytes: 4 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct MathAstLimits(MathAstLimitConfig);

impl MathAstLimits {
    pub const HARD_MAX_SOURCE_BYTES: u32 = 16 * 1024 * 1024;
    pub const HARD_MAX_NODES: usize = 65_536;
    pub const HARD_MAX_DEPTH: usize = 256;
    pub const HARD_MAX_CHILDREN_PER_NODE: usize = 4_096;
    pub const HARD_MAX_MATRIX_ROWS: usize = 1_024;
    pub const HARD_MAX_MATRIX_COLUMNS: usize = 1_024;
    pub const HARD_MAX_STRING_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_TOTAL_STRING_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;

    /// Creates finite limits for the P07-01 `MathAst` boundary.
    ///
    /// # Errors
    ///
    /// Returns [`MathAstError::InvalidLimit`] when a limit is zero, exceeds its hard ceiling, or
    /// cannot contain one value allowed by a subordinate limit.
    pub fn new(config: MathAstLimitConfig) -> Result<Self, MathAstError> {
        if config.source_bytes == 0
            || config.source_bytes > Self::HARD_MAX_SOURCE_BYTES
            || config.nodes == 0
            || config.nodes > Self::HARD_MAX_NODES
            || config.depth == 0
            || config.depth > Self::HARD_MAX_DEPTH
            || config.children_per_node == 0
            || config.children_per_node > Self::HARD_MAX_CHILDREN_PER_NODE
            || config.matrix_rows == 0
            || config.matrix_rows > Self::HARD_MAX_MATRIX_ROWS
            || config.matrix_columns == 0
            || config.matrix_columns > Self::HARD_MAX_MATRIX_COLUMNS
            || config.string_bytes == 0
            || config.string_bytes > Self::HARD_MAX_STRING_BYTES
            || config.total_string_bytes == 0
            || config.total_string_bytes > Self::HARD_MAX_TOTAL_STRING_BYTES
            || config.total_string_bytes < config.string_bytes
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(MathAstError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> MathAstLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathSourceSpan {
    pub start_byte: u32,
    pub end_byte: u32,
}

impl fmt::Debug for MathSourceSpan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("MathSourceSpan(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathVariant {
    Normal,
    Upright,
    Italic,
    Bold,
    BoldItalic,
    DoubleStruck,
    Fraktur,
    Script,
    SansSerif,
    Monospace,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathColor {
    pub red: u8,
    pub green: u8,
    pub blue: u8,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathStyleHint {
    pub variant: Option<MathVariant>,
    pub color: Option<MathColor>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathLetterCase {
    Lower,
    Upper,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathGreekLetter {
    Alpha,
    Beta,
    Gamma,
    Delta,
    Epsilon,
    Zeta,
    Eta,
    Theta,
    Iota,
    Kappa,
    Lambda,
    Mu,
    Nu,
    Xi,
    Omicron,
    Pi,
    Rho,
    Sigma,
    Tau,
    Upsilon,
    Phi,
    Chi,
    Psi,
    Omega,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum MathSymbol {
    Greek {
        letter: MathGreekLetter,
        letter_case: MathLetterCase,
    },
    Infinity,
    EmptySet,
    Aleph,
    Hbar,
    PartialDifferential,
    Nabla,
    Therefore,
    Because,
    HorizontalEllipsis,
    VerticalEllipsis,
    DiagonalEllipsis,
    Degree,
    Prime,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathOperator {
    Positive,
    Negative,
    Add,
    Subtract,
    Multiply,
    Divide,
    Power,
    Factorial,
    Equal,
    NotEqual,
    LessThan,
    LessThanOrEqual,
    GreaterThan,
    GreaterThanOrEqual,
    ApproximatelyEqual,
    ProportionalTo,
    LogicalNot,
    LogicalAnd,
    LogicalOr,
    Implies,
    Equivalent,
    ElementOf,
    NotElementOf,
    SubsetOf,
    ProperSubsetOf,
    SupersetOf,
    ProperSupersetOf,
    Union,
    Intersection,
    SetDifference,
    Compose,
}

impl MathOperator {
    const fn arity(self) -> MathArity {
        match self {
            Self::Positive | Self::Negative | Self::Factorial | Self::LogicalNot => {
                MathArity::Exact(1)
            }
            Self::Add
            | Self::Multiply
            | Self::LogicalAnd
            | Self::LogicalOr
            | Self::Union
            | Self::Intersection => MathArity::AtLeast(2),
            Self::Subtract
            | Self::Divide
            | Self::Power
            | Self::Equal
            | Self::NotEqual
            | Self::LessThan
            | Self::LessThanOrEqual
            | Self::GreaterThan
            | Self::GreaterThanOrEqual
            | Self::ApproximatelyEqual
            | Self::ProportionalTo
            | Self::Implies
            | Self::Equivalent
            | Self::ElementOf
            | Self::NotElementOf
            | Self::SubsetOf
            | Self::ProperSubsetOf
            | Self::SupersetOf
            | Self::ProperSupersetOf
            | Self::SetDifference
            | Self::Compose => MathArity::Exact(2),
        }
    }

    const fn associative(self) -> bool {
        matches!(
            self,
            Self::Add
                | Self::Multiply
                | Self::LogicalAnd
                | Self::LogicalOr
                | Self::Union
                | Self::Intersection
        )
    }
}

#[derive(Clone, Eq, PartialEq, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum MathFunction {
    Sin,
    Cos,
    Tan,
    Cot,
    Sec,
    Csc,
    Arcsin,
    Arccos,
    Arctan,
    Sinh,
    Cosh,
    Tanh,
    Log,
    NaturalLog,
    Exponential,
    Minimum,
    Maximum,
    Named { name: String },
}

impl fmt::Debug for MathFunction {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Named { .. } => "MathFunction::Named(<redacted>)",
            Self::Sin => "MathFunction::Sin",
            Self::Cos => "MathFunction::Cos",
            Self::Tan => "MathFunction::Tan",
            Self::Cot => "MathFunction::Cot",
            Self::Sec => "MathFunction::Sec",
            Self::Csc => "MathFunction::Csc",
            Self::Arcsin => "MathFunction::Arcsin",
            Self::Arccos => "MathFunction::Arccos",
            Self::Arctan => "MathFunction::Arctan",
            Self::Sinh => "MathFunction::Sinh",
            Self::Cosh => "MathFunction::Cosh",
            Self::Tanh => "MathFunction::Tanh",
            Self::Log => "MathFunction::Log",
            Self::NaturalLog => "MathFunction::NaturalLog",
            Self::Exponential => "MathFunction::Exponential",
            Self::Minimum => "MathFunction::Minimum",
            Self::Maximum => "MathFunction::Maximum",
        })
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathAccent {
    VectorArrow,
    Hat,
    Bar,
    Tilde,
    Dot,
    DoubleDot,
    Check,
    Acute,
    Grave,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathAnnotationKind {
    OverBrace,
    UnderBrace,
    OverLine,
    UnderLine,
    OverArrow,
    UnderArrow,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum MathLargeOperator {
    Limit,
    Sum,
    Product,
    Integral { multiplicity: u8, contour: bool },
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathDerivativeKind {
    Ordinary,
    Partial,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathDelimiter {
    None,
    LeftParenthesis,
    RightParenthesis,
    LeftBracket,
    RightBracket,
    LeftBrace,
    RightBrace,
    LeftAngle,
    RightAngle,
    VerticalBar,
    DoubleVerticalBar,
    LeftFloor,
    RightFloor,
    LeftCeiling,
    RightCeiling,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathMatrixKind {
    Plain,
    Parenthesized,
    Bracketed,
    Determinant,
    DoubleBar,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MathCombinatorialKind {
    Binomial,
    Permutation,
    Combination,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathDerivativeVariable {
    pub variable: Box<MathNode>,
    pub order: u16,
}

impl fmt::Debug for MathDerivativeVariable {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("MathDerivativeVariable(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathCase {
    pub value: MathNode,
    pub condition: Option<MathNode>,
}

impl fmt::Debug for MathCase {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("MathCase(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathAlignedLine {
    pub cells: Vec<MathNode>,
}

impl fmt::Debug for MathAlignedLine {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("MathAlignedLine(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum MathExpression {
    Number {
        value: String,
    },
    Identifier {
        name: String,
    },
    Text {
        value: String,
    },
    Symbol {
        symbol: MathSymbol,
    },
    Row {
        items: Vec<MathNode>,
    },
    Apply {
        operator: MathOperator,
        arguments: Vec<MathNode>,
    },
    Function {
        function: MathFunction,
        arguments: Vec<MathNode>,
    },
    Fraction {
        numerator: Box<MathNode>,
        denominator: Box<MathNode>,
    },
    Script {
        base: Box<MathNode>,
        subscript: Option<Box<MathNode>>,
        superscript: Option<Box<MathNode>>,
    },
    Root {
        degree: Option<Box<MathNode>>,
        radicand: Box<MathNode>,
    },
    Accent {
        accent: MathAccent,
        base: Box<MathNode>,
    },
    Annotated {
        annotation_kind: MathAnnotationKind,
        base: Box<MathNode>,
        annotation: Option<Box<MathNode>>,
    },
    LargeOperator {
        operator: MathLargeOperator,
        body: Box<MathNode>,
        lower: Option<Box<MathNode>>,
        upper: Option<Box<MathNode>>,
    },
    Derivative {
        derivative_kind: MathDerivativeKind,
        expression: Box<MathNode>,
        variables: Vec<MathDerivativeVariable>,
    },
    Delimited {
        left: MathDelimiter,
        body: Box<MathNode>,
        right: MathDelimiter,
    },
    Matrix {
        matrix_kind: MathMatrixKind,
        rows: Vec<Vec<MathNode>>,
    },
    Cases {
        cases: Vec<MathCase>,
    },
    Aligned {
        lines: Vec<MathAlignedLine>,
    },
    Combinatorial {
        combinatorial_kind: MathCombinatorialKind,
        upper: Box<MathNode>,
        lower: Box<MathNode>,
    },
    SetBuilder {
        element: Box<MathNode>,
        condition: Box<MathNode>,
    },
}

impl fmt::Debug for MathExpression {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("MathExpression(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathNode {
    pub span: MathSourceSpan,
    pub style: Option<MathStyleHint>,
    pub expression: MathExpression,
}

impl fmt::Debug for MathNode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("MathNode(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MathAstDraft {
    pub schema_version: String,
    pub normalization_version: String,
    pub source_length_bytes: u32,
    pub root: MathNode,
}

impl fmt::Debug for MathAstDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MathAstDraft")
            .field("schema_version", &self.schema_version)
            .field("normalization_version", &self.normalization_version)
            .field("source_length_bytes", &"<redacted>")
            .field("root", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct MathAst {
    schema_version: &'static str,
    normalization_version: &'static str,
    source_length_bytes: u32,
    root: MathNode,
}

impl MathAst {
    /// Validates and normalizes a complete typed `MathAst` draft.
    ///
    /// # Errors
    ///
    /// Rejects unknown versions, invalid spans or structures, malformed literals, and any finite
    /// limit violation.
    pub fn from_draft(draft: MathAstDraft, limits: MathAstLimits) -> Result<Self, MathAstError> {
        if draft.schema_version != MATH_AST_SCHEMA_VERSION {
            return Err(MathAstError::UnsupportedVersion);
        }
        if draft.normalization_version != MATH_AST_NORMALIZATION_VERSION {
            return Err(MathAstError::UnsupportedNormalizationVersion);
        }
        if draft.source_length_bytes == 0 || draft.source_length_bytes > limits.0.source_bytes {
            return Err(MathAstError::SourceLimit);
        }
        let mut normalizer = Normalizer::new(limits, draft.source_length_bytes);
        let root = normalizer.normalize_node(draft.root, None, 1)?;
        let ast = Self {
            schema_version: MATH_AST_SCHEMA_VERSION,
            normalization_version: MATH_AST_NORMALIZATION_VERSION,
            source_length_bytes: draft.source_length_bytes,
            root,
        };
        let _ = ast.canonical_json(limits)?;
        let _ = ast.semantic_json(limits)?;
        Ok(ast)
    }

    /// Deserializes, validates, and normalizes a complete typed `MathAst` document.
    ///
    /// # Errors
    ///
    /// Rejects empty or oversized bytes, malformed JSON, unknown fields, unsupported versions,
    /// invalid payloads, and normalized outputs beyond the configured bound.
    pub fn from_json(bytes: &[u8], limits: MathAstLimits) -> Result<Self, MathAstError> {
        if bytes.is_empty() || bytes.len() > limits.0.serialized_bytes {
            return Err(MathAstError::InputLimit);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| MathAstError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub const fn normalization_version(&self) -> &'static str {
        self.normalization_version
    }

    #[must_use]
    pub const fn source_length_bytes(&self) -> u32 {
        self.source_length_bytes
    }

    #[must_use]
    pub const fn root(&self) -> &MathNode {
        &self.root
    }

    /// Serializes the complete normalized AST, including source spans and style hints.
    ///
    /// # Errors
    ///
    /// Returns an error if serialization fails or exceeds the configured bound.
    pub fn canonical_json(&self, limits: MathAstLimits) -> Result<Vec<u8>, MathAstError> {
        bounded_json(self, limits)
    }

    /// Serializes the normalized semantic projection. Source spans and visual style hints are
    /// deliberately excluded so parser spelling and provenance do not change semantic identity.
    ///
    /// # Errors
    ///
    /// Returns an error if serialization fails or exceeds the configured bound.
    pub fn semantic_json(&self, limits: MathAstLimits) -> Result<Vec<u8>, MathAstError> {
        let projection = SemanticAst {
            schema_version: self.schema_version,
            normalization_version: self.normalization_version,
            root: semantic_node(&self.root),
        };
        bounded_json(&projection, limits)
    }

    /// Returns SHA-256 over the bounded semantic projection.
    ///
    /// # Errors
    ///
    /// Propagates semantic serialization and output-bound failures.
    pub fn semantic_sha256(&self, limits: MathAstLimits) -> Result<[u8; 32], MathAstError> {
        Ok(Sha256::digest(self.semantic_json(limits)?).into())
    }

    /// Compares normalized mathematical structure while ignoring source spans and style hints.
    #[must_use]
    pub fn semantically_eq(&self, other: &Self) -> bool {
        semantic_node(&self.root) == semantic_node(&other.root)
    }
}

impl fmt::Debug for MathAst {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MathAst")
            .field("schema_version", &self.schema_version)
            .field("normalization_version", &self.normalization_version)
            .field("source_length_bytes", &"<redacted>")
            .field("root", &"<redacted>")
            .finish()
    }
}

#[derive(Debug, Error, Clone, Copy, Eq, PartialEq)]
pub enum MathAstError {
    #[error("MathAst limit configuration is invalid")]
    InvalidLimit,
    #[error("MathAst input is empty or exceeds its byte limit")]
    InputLimit,
    #[error("MathAst schema version is unsupported")]
    UnsupportedVersion,
    #[error("MathAst normalization version is unsupported")]
    UnsupportedNormalizationVersion,
    #[error("MathAst JSON is invalid")]
    InvalidJson,
    #[error("MathAst source length is invalid or exceeds its limit")]
    SourceLimit,
    #[error("MathAst source span is invalid")]
    InvalidSpan,
    #[error("MathAst number is invalid")]
    InvalidNumber,
    #[error("MathAst identifier is invalid")]
    InvalidIdentifier,
    #[error("MathAst text is invalid")]
    InvalidText,
    #[error("MathAst operator or function arity is invalid")]
    InvalidArity,
    #[error("MathAst semantic structure is invalid")]
    InvalidStructure,
    #[error("MathAst finite limit was exceeded")]
    LimitExceeded,
    #[error("MathAst output exceeds its byte limit")]
    OutputLimit,
    #[error("MathAst serialization failed")]
    Serialization,
}

impl MathAstError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "math_ast_invalid_limit",
            Self::InputLimit => "math_ast_input_limit",
            Self::UnsupportedVersion => "math_ast_unsupported_version",
            Self::UnsupportedNormalizationVersion => "math_ast_unsupported_normalization_version",
            Self::InvalidJson => "math_ast_invalid_json",
            Self::SourceLimit => "math_ast_source_limit",
            Self::InvalidSpan => "math_ast_invalid_span",
            Self::InvalidNumber => "math_ast_invalid_number",
            Self::InvalidIdentifier => "math_ast_invalid_identifier",
            Self::InvalidText => "math_ast_invalid_text",
            Self::InvalidArity => "math_ast_invalid_arity",
            Self::InvalidStructure => "math_ast_invalid_structure",
            Self::LimitExceeded => "math_ast_limit_exceeded",
            Self::OutputLimit => "math_ast_output_limit",
            Self::Serialization => "math_ast_serialization",
        }
    }
}

#[derive(Clone, Copy)]
enum MathArity {
    Exact(usize),
    AtLeast(usize),
}

impl MathArity {
    const fn accepts(self, actual: usize) -> bool {
        match self {
            Self::Exact(expected) => actual == expected,
            Self::AtLeast(minimum) => actual >= minimum,
        }
    }
}

struct Normalizer {
    limits: MathAstLimits,
    source_length_bytes: u32,
    nodes: usize,
    total_string_bytes: usize,
}

impl Normalizer {
    const fn new(limits: MathAstLimits, source_length_bytes: u32) -> Self {
        Self {
            limits,
            source_length_bytes,
            nodes: 0,
            total_string_bytes: 0,
        }
    }

    fn normalize_node(
        &mut self,
        mut node: MathNode,
        parent_span: Option<MathSourceSpan>,
        depth: usize,
    ) -> Result<MathNode, MathAstError> {
        if depth > self.limits.0.depth {
            return Err(MathAstError::LimitExceeded);
        }
        self.nodes = self
            .nodes
            .checked_add(1)
            .ok_or(MathAstError::LimitExceeded)?;
        if self.nodes > self.limits.0.nodes {
            return Err(MathAstError::LimitExceeded);
        }
        self.validate_span(node.span, parent_span)?;
        if node
            .style
            .is_some_and(|style| style.variant.is_none() && style.color.is_none())
        {
            node.style = None;
        }
        node.expression = self.normalize_expression(node.expression, node.span, depth)?;
        Ok(node)
    }

    fn validate_span(
        &self,
        span: MathSourceSpan,
        parent_span: Option<MathSourceSpan>,
    ) -> Result<(), MathAstError> {
        if span.start_byte >= span.end_byte || span.end_byte > self.source_length_bytes {
            return Err(MathAstError::InvalidSpan);
        }
        if parent_span.is_some_and(|parent| {
            span.start_byte < parent.start_byte || span.end_byte > parent.end_byte
        }) {
            return Err(MathAstError::InvalidSpan);
        }
        Ok(())
    }

    #[allow(clippy::too_many_lines)]
    fn normalize_expression(
        &mut self,
        expression: MathExpression,
        span: MathSourceSpan,
        depth: usize,
    ) -> Result<MathExpression, MathAstError> {
        let child_depth = depth.checked_add(1).ok_or(MathAstError::LimitExceeded)?;
        match expression {
            MathExpression::Number { value } => Ok(MathExpression::Number {
                value: self.normalize_number(&value)?,
            }),
            MathExpression::Identifier { name } => Ok(MathExpression::Identifier {
                name: self.normalize_identifier(&name)?,
            }),
            MathExpression::Text { value } => Ok(MathExpression::Text {
                value: self.normalize_text(&value)?,
            }),
            MathExpression::Symbol { symbol } => Ok(MathExpression::Symbol { symbol }),
            MathExpression::Row { items } => {
                self.validate_count(items.len(), 1)?;
                Ok(MathExpression::Row {
                    items: self.normalize_nodes(items, span, child_depth)?,
                })
            }
            MathExpression::Apply {
                operator,
                arguments,
            } => {
                self.validate_count(arguments.len(), 1)?;
                if !operator.arity().accepts(arguments.len()) {
                    return Err(MathAstError::InvalidArity);
                }
                Ok(MathExpression::Apply {
                    operator,
                    arguments: self.normalize_nodes(arguments, span, child_depth)?,
                })
            }
            MathExpression::Function {
                function,
                arguments,
            } => {
                self.validate_count(arguments.len(), 1)?;
                let function = match function {
                    MathFunction::Named { name } => MathFunction::Named {
                        name: self.normalize_identifier(&name)?,
                    },
                    other => other,
                };
                Ok(MathExpression::Function {
                    function,
                    arguments: self.normalize_nodes(arguments, span, child_depth)?,
                })
            }
            MathExpression::Fraction {
                numerator,
                denominator,
            } => Ok(MathExpression::Fraction {
                numerator: Box::new(self.normalize_node(*numerator, Some(span), child_depth)?),
                denominator: Box::new(self.normalize_node(
                    *denominator,
                    Some(span),
                    child_depth,
                )?),
            }),
            MathExpression::Script {
                base,
                subscript,
                superscript,
            } => {
                if subscript.is_none() && superscript.is_none() {
                    return Err(MathAstError::InvalidStructure);
                }
                Ok(MathExpression::Script {
                    base: Box::new(self.normalize_node(*base, Some(span), child_depth)?),
                    subscript: self.normalize_optional(subscript, span, child_depth)?,
                    superscript: self.normalize_optional(superscript, span, child_depth)?,
                })
            }
            MathExpression::Root { degree, radicand } => Ok(MathExpression::Root {
                degree: self.normalize_optional(degree, span, child_depth)?,
                radicand: Box::new(self.normalize_node(*radicand, Some(span), child_depth)?),
            }),
            MathExpression::Accent { accent, base } => Ok(MathExpression::Accent {
                accent,
                base: Box::new(self.normalize_node(*base, Some(span), child_depth)?),
            }),
            MathExpression::Annotated {
                annotation_kind,
                base,
                annotation,
            } => Ok(MathExpression::Annotated {
                annotation_kind,
                base: Box::new(self.normalize_node(*base, Some(span), child_depth)?),
                annotation: self.normalize_optional(annotation, span, child_depth)?,
            }),
            MathExpression::LargeOperator {
                operator,
                body,
                lower,
                upper,
            } => {
                if matches!(operator, MathLargeOperator::Limit) && lower.is_none() {
                    return Err(MathAstError::InvalidStructure);
                }
                if matches!(operator, MathLargeOperator::Limit) && upper.is_some() {
                    return Err(MathAstError::InvalidStructure);
                }
                if let MathLargeOperator::Integral { multiplicity, .. } = operator
                    && !(1..=8).contains(&multiplicity)
                {
                    return Err(MathAstError::InvalidStructure);
                }
                Ok(MathExpression::LargeOperator {
                    operator,
                    body: Box::new(self.normalize_node(*body, Some(span), child_depth)?),
                    lower: self.normalize_optional(lower, span, child_depth)?,
                    upper: self.normalize_optional(upper, span, child_depth)?,
                })
            }
            MathExpression::Derivative {
                derivative_kind,
                expression,
                variables,
            } => {
                self.validate_count(variables.len(), 1)?;
                let expression =
                    Box::new(self.normalize_node(*expression, Some(span), child_depth)?);
                let mut normalized = Vec::with_capacity(variables.len());
                for variable in variables {
                    let order = variable.order;
                    if order == 0 {
                        return Err(MathAstError::InvalidStructure);
                    }
                    let variable =
                        self.normalize_node(*variable.variable, Some(span), child_depth)?;
                    if !is_derivative_variable(&variable.expression) {
                        return Err(MathAstError::InvalidStructure);
                    }
                    normalized.push(MathDerivativeVariable {
                        variable: Box::new(variable),
                        order,
                    });
                }
                Ok(MathExpression::Derivative {
                    derivative_kind,
                    expression,
                    variables: normalized,
                })
            }
            MathExpression::Delimited { left, body, right } => {
                if left == MathDelimiter::None && right == MathDelimiter::None {
                    return Err(MathAstError::InvalidStructure);
                }
                Ok(MathExpression::Delimited {
                    left,
                    body: Box::new(self.normalize_node(*body, Some(span), child_depth)?),
                    right,
                })
            }
            MathExpression::Matrix { matrix_kind, rows } => {
                if rows.is_empty() || rows.len() > self.limits.0.matrix_rows {
                    return Err(MathAstError::InvalidStructure);
                }
                let columns = rows.first().map_or(0, Vec::len);
                if columns == 0
                    || columns > self.limits.0.matrix_columns
                    || rows.iter().any(|row| row.len() != columns)
                    || (matrix_kind == MathMatrixKind::Determinant && rows.len() != columns)
                {
                    return Err(MathAstError::InvalidStructure);
                }
                let cell_count = rows
                    .len()
                    .checked_mul(columns)
                    .ok_or(MathAstError::LimitExceeded)?;
                if cell_count > self.limits.0.nodes {
                    return Err(MathAstError::LimitExceeded);
                }
                let mut normalized_rows = Vec::with_capacity(rows.len());
                for row in rows {
                    normalized_rows.push(self.normalize_nodes(row, span, child_depth)?);
                }
                Ok(MathExpression::Matrix {
                    matrix_kind,
                    rows: normalized_rows,
                })
            }
            MathExpression::Cases { cases } => {
                self.validate_count(cases.len(), 1)?;
                let mut normalized = Vec::with_capacity(cases.len());
                for case in cases {
                    normalized.push(MathCase {
                        value: self.normalize_node(case.value, Some(span), child_depth)?,
                        condition: self.normalize_optional_value(
                            case.condition,
                            span,
                            child_depth,
                        )?,
                    });
                }
                Ok(MathExpression::Cases { cases: normalized })
            }
            MathExpression::Aligned { lines } => {
                self.validate_count(lines.len(), 1)?;
                let columns = lines.first().map_or(0, |line| line.cells.len());
                if columns == 0
                    || columns > self.limits.0.children_per_node
                    || lines.iter().any(|line| line.cells.len() != columns)
                {
                    return Err(MathAstError::InvalidStructure);
                }
                let mut normalized = Vec::with_capacity(lines.len());
                for line in lines {
                    normalized.push(MathAlignedLine {
                        cells: self.normalize_nodes(line.cells, span, child_depth)?,
                    });
                }
                Ok(MathExpression::Aligned { lines: normalized })
            }
            MathExpression::Combinatorial {
                combinatorial_kind,
                upper,
                lower,
            } => Ok(MathExpression::Combinatorial {
                combinatorial_kind,
                upper: Box::new(self.normalize_node(*upper, Some(span), child_depth)?),
                lower: Box::new(self.normalize_node(*lower, Some(span), child_depth)?),
            }),
            MathExpression::SetBuilder { element, condition } => Ok(MathExpression::SetBuilder {
                element: Box::new(self.normalize_node(*element, Some(span), child_depth)?),
                condition: Box::new(self.normalize_node(*condition, Some(span), child_depth)?),
            }),
        }
    }

    fn normalize_nodes(
        &mut self,
        nodes: Vec<MathNode>,
        parent_span: MathSourceSpan,
        depth: usize,
    ) -> Result<Vec<MathNode>, MathAstError> {
        nodes
            .into_iter()
            .map(|node| self.normalize_node(node, Some(parent_span), depth))
            .collect()
    }

    fn normalize_optional(
        &mut self,
        node: Option<Box<MathNode>>,
        parent_span: MathSourceSpan,
        depth: usize,
    ) -> Result<Option<Box<MathNode>>, MathAstError> {
        node.map(|node| {
            self.normalize_node(*node, Some(parent_span), depth)
                .map(Box::new)
        })
        .transpose()
    }

    fn normalize_optional_value(
        &mut self,
        node: Option<MathNode>,
        parent_span: MathSourceSpan,
        depth: usize,
    ) -> Result<Option<MathNode>, MathAstError> {
        node.map(|node| self.normalize_node(node, Some(parent_span), depth))
            .transpose()
    }

    fn validate_count(&self, count: usize, minimum: usize) -> Result<(), MathAstError> {
        if count < minimum || count > self.limits.0.children_per_node {
            return Err(MathAstError::InvalidArity);
        }
        Ok(())
    }

    fn normalize_number(&mut self, value: &str) -> Result<String, MathAstError> {
        if value.is_empty()
            || !value.is_ascii()
            || value.bytes().filter(|byte| *byte == b'.').count() > 1
        {
            return Err(MathAstError::InvalidNumber);
        }
        let (integer, fraction) = value.split_once('.').unwrap_or((value, ""));
        if (integer.is_empty() && fraction.is_empty())
            || !integer.bytes().all(|byte| byte.is_ascii_digit())
            || !fraction.bytes().all(|byte| byte.is_ascii_digit())
        {
            return Err(MathAstError::InvalidNumber);
        }
        let integer = integer.trim_start_matches('0');
        let integer = if integer.is_empty() { "0" } else { integer };
        let fraction = fraction.trim_end_matches('0');
        let normalized = if fraction.is_empty() {
            integer.to_owned()
        } else {
            format!("{integer}.{fraction}")
        };
        self.record_string(&normalized)?;
        Ok(normalized)
    }

    fn normalize_identifier(&mut self, value: &str) -> Result<String, MathAstError> {
        let normalized = value.nfc().collect::<String>();
        if normalized.is_empty()
            || normalized
                .chars()
                .any(|character| character.is_control() || character.is_whitespace())
        {
            return Err(MathAstError::InvalidIdentifier);
        }
        self.record_string(&normalized)?;
        Ok(normalized)
    }

    fn normalize_text(&mut self, value: &str) -> Result<String, MathAstError> {
        let normalized = value.nfc().collect::<String>();
        if normalized.is_empty() || normalized.chars().any(char::is_control) {
            return Err(MathAstError::InvalidText);
        }
        self.record_string(&normalized)?;
        Ok(normalized)
    }

    fn record_string(&mut self, value: &str) -> Result<(), MathAstError> {
        if value.len() > self.limits.0.string_bytes {
            return Err(MathAstError::LimitExceeded);
        }
        self.total_string_bytes = self
            .total_string_bytes
            .checked_add(value.len())
            .ok_or(MathAstError::LimitExceeded)?;
        if self.total_string_bytes > self.limits.0.total_string_bytes {
            return Err(MathAstError::LimitExceeded);
        }
        Ok(())
    }
}

fn bounded_json<T: Serialize>(value: &T, limits: MathAstLimits) -> Result<Vec<u8>, MathAstError> {
    let bytes = serde_json::to_vec(value).map_err(|_| MathAstError::Serialization)?;
    if bytes.len() > limits.0.serialized_bytes {
        return Err(MathAstError::OutputLimit);
    }
    Ok(bytes)
}

#[derive(Eq, PartialEq, Serialize)]
struct SemanticAst<'a> {
    schema_version: &'a str,
    normalization_version: &'a str,
    root: SemanticNode<'a>,
}

#[derive(Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum SemanticNode<'a> {
    Number {
        value: &'a str,
    },
    Identifier {
        name: &'a str,
    },
    Text {
        value: &'a str,
    },
    Symbol {
        symbol: MathSymbol,
    },
    Row {
        items: Vec<Self>,
    },
    Apply {
        operator: MathOperator,
        arguments: Vec<Self>,
    },
    Function {
        function: &'a MathFunction,
        arguments: Vec<Self>,
    },
    Fraction {
        numerator: Box<Self>,
        denominator: Box<Self>,
    },
    Script {
        base: Box<Self>,
        subscript: Option<Box<Self>>,
        superscript: Option<Box<Self>>,
    },
    Root {
        degree: Option<Box<Self>>,
        radicand: Box<Self>,
    },
    Accent {
        accent: MathAccent,
        base: Box<Self>,
    },
    Annotated {
        annotation_kind: MathAnnotationKind,
        base: Box<Self>,
        annotation: Option<Box<Self>>,
    },
    LargeOperator {
        operator: MathLargeOperator,
        body: Box<Self>,
        lower: Option<Box<Self>>,
        upper: Option<Box<Self>>,
    },
    Derivative {
        derivative_kind: MathDerivativeKind,
        expression: Box<Self>,
        variables: Vec<SemanticDerivativeVariable<'a>>,
    },
    Delimited {
        left: MathDelimiter,
        body: Box<Self>,
        right: MathDelimiter,
    },
    Matrix {
        matrix_kind: MathMatrixKind,
        rows: Vec<Vec<Self>>,
    },
    Cases {
        cases: Vec<SemanticCase<'a>>,
    },
    Aligned {
        lines: Vec<Vec<Self>>,
    },
    Combinatorial {
        combinatorial_kind: MathCombinatorialKind,
        upper: Box<Self>,
        lower: Box<Self>,
    },
    SetBuilder {
        element: Box<Self>,
        condition: Box<Self>,
    },
}

#[derive(Eq, PartialEq, Serialize)]
struct SemanticDerivativeVariable<'a> {
    variable: SemanticNode<'a>,
    order: u16,
}

#[derive(Eq, PartialEq, Serialize)]
struct SemanticCase<'a> {
    value: SemanticNode<'a>,
    condition: Option<SemanticNode<'a>>,
}

#[allow(clippy::too_many_lines)]
fn semantic_node(node: &MathNode) -> SemanticNode<'_> {
    match &node.expression {
        MathExpression::Number { value } => SemanticNode::Number { value },
        MathExpression::Identifier { name } => SemanticNode::Identifier { name },
        MathExpression::Text { value } => SemanticNode::Text { value },
        MathExpression::Symbol { symbol } => SemanticNode::Symbol { symbol: *symbol },
        MathExpression::Row { items } => {
            let mut items = semantic_row_items(items);
            if items.len() == 1 {
                items.remove(0)
            } else {
                SemanticNode::Row { items }
            }
        }
        MathExpression::Apply {
            operator: MathOperator::Positive,
            arguments,
        } => semantic_node(&arguments[0]),
        MathExpression::Apply {
            operator,
            arguments,
        } if operator.associative() => {
            let mut projected = Vec::new();
            for argument in arguments {
                flatten_associative(*operator, argument, &mut projected);
            }
            SemanticNode::Apply {
                operator: *operator,
                arguments: projected,
            }
        }
        MathExpression::Apply {
            operator,
            arguments,
        } => SemanticNode::Apply {
            operator: *operator,
            arguments: arguments.iter().map(semantic_node).collect(),
        },
        MathExpression::Function {
            function,
            arguments,
        } => SemanticNode::Function {
            function,
            arguments: arguments.iter().map(semantic_node).collect(),
        },
        MathExpression::Fraction {
            numerator,
            denominator,
        } => SemanticNode::Fraction {
            numerator: Box::new(semantic_node(numerator)),
            denominator: Box::new(semantic_node(denominator)),
        },
        MathExpression::Script {
            base,
            subscript,
            superscript,
        } => SemanticNode::Script {
            base: Box::new(semantic_node(base)),
            subscript: subscript.as_deref().map(semantic_node).map(Box::new),
            superscript: superscript.as_deref().map(semantic_node).map(Box::new),
        },
        MathExpression::Root { degree, radicand } => {
            let degree = degree
                .as_deref()
                .filter(|degree| !is_number(degree, "2"))
                .map(semantic_node)
                .map(Box::new);
            SemanticNode::Root {
                degree,
                radicand: Box::new(semantic_node(radicand)),
            }
        }
        MathExpression::Accent { accent, base } => SemanticNode::Accent {
            accent: *accent,
            base: Box::new(semantic_node(base)),
        },
        MathExpression::Annotated {
            annotation_kind,
            base,
            annotation,
        } => SemanticNode::Annotated {
            annotation_kind: *annotation_kind,
            base: Box::new(semantic_node(base)),
            annotation: annotation.as_deref().map(semantic_node).map(Box::new),
        },
        MathExpression::LargeOperator {
            operator,
            body,
            lower,
            upper,
        } => SemanticNode::LargeOperator {
            operator: *operator,
            body: Box::new(semantic_node(body)),
            lower: lower.as_deref().map(semantic_node).map(Box::new),
            upper: upper.as_deref().map(semantic_node).map(Box::new),
        },
        MathExpression::Derivative {
            derivative_kind,
            expression,
            variables,
        } => SemanticNode::Derivative {
            derivative_kind: *derivative_kind,
            expression: Box::new(semantic_node(expression)),
            variables: variables
                .iter()
                .map(|variable| SemanticDerivativeVariable {
                    variable: semantic_node(&variable.variable),
                    order: variable.order,
                })
                .collect(),
        },
        MathExpression::Delimited { left, body, right } => SemanticNode::Delimited {
            left: *left,
            body: Box::new(semantic_node(body)),
            right: *right,
        },
        MathExpression::Matrix { matrix_kind, rows } => SemanticNode::Matrix {
            matrix_kind: *matrix_kind,
            rows: rows
                .iter()
                .map(|row| row.iter().map(semantic_node).collect())
                .collect(),
        },
        MathExpression::Cases { cases } => SemanticNode::Cases {
            cases: cases
                .iter()
                .map(|case| SemanticCase {
                    value: semantic_node(&case.value),
                    condition: case.condition.as_ref().map(semantic_node),
                })
                .collect(),
        },
        MathExpression::Aligned { lines } => SemanticNode::Aligned {
            lines: lines
                .iter()
                .map(|line| line.cells.iter().map(semantic_node).collect())
                .collect(),
        },
        MathExpression::Combinatorial {
            combinatorial_kind,
            upper,
            lower,
        } => SemanticNode::Combinatorial {
            combinatorial_kind: *combinatorial_kind,
            upper: Box::new(semantic_node(upper)),
            lower: Box::new(semantic_node(lower)),
        },
        MathExpression::SetBuilder { element, condition } => SemanticNode::SetBuilder {
            element: Box::new(semantic_node(element)),
            condition: Box::new(semantic_node(condition)),
        },
    }
}

fn flatten_associative<'a>(
    operator: MathOperator,
    node: &'a MathNode,
    output: &mut Vec<SemanticNode<'a>>,
) {
    if let MathExpression::Apply {
        operator: MathOperator::Positive,
        arguments,
    } = &node.expression
    {
        flatten_associative(operator, &arguments[0], output);
        return;
    }
    if let MathExpression::Apply {
        operator: nested_operator,
        arguments,
    } = &node.expression
        && *nested_operator == operator
    {
        for argument in arguments {
            flatten_associative(operator, argument, output);
        }
    } else {
        output.push(semantic_node(node));
    }
}

fn semantic_row_items(nodes: &[MathNode]) -> Vec<SemanticNode<'_>> {
    let mut output = Vec::new();
    for node in nodes {
        if let MathExpression::Row { items } = &node.expression {
            output.extend(semantic_row_items(items));
        } else {
            output.push(semantic_node(node));
        }
    }
    output
}

fn is_number(node: &MathNode, expected: &str) -> bool {
    matches!(&node.expression, MathExpression::Number { value } if value == expected)
}

fn is_derivative_variable(expression: &MathExpression) -> bool {
    matches!(
        expression,
        MathExpression::Identifier { .. }
            | MathExpression::Symbol {
                symbol: MathSymbol::Greek { .. }
            }
    )
}
