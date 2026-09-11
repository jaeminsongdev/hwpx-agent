use std::collections::BTreeMap;
use std::fmt;

use domain_ir::{
    MATH_AST_NORMALIZATION_VERSION, MATH_AST_SCHEMA_VERSION, MathAccent, MathAst, MathAstDraft,
    MathAstLimits, MathCombinatorialKind, MathDelimiter, MathDerivativeKind,
    MathDerivativeVariable, MathExpression, MathFunction, MathGreekLetter, MathLargeOperator,
    MathLetterCase, MathNode, MathOperator, MathSourceSpan, MathStyleHint, MathSymbol, MathVariant,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const LATEX_ADAPTER_SCHEMA_VERSION: &str = "hwpx-agent.latex-adapter/v1";
pub const LATEX_PARSER_VERSION: &str = "hwpx-agent.latex-parser/tier-a-v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct LatexAdapterLimitConfig {
    pub source_bytes: usize,
    pub input_tokens: usize,
    pub expanded_tokens: usize,
    pub parse_depth: usize,
    pub macro_definitions: usize,
    pub macro_parameters: u8,
    pub macro_expansion_depth: usize,
    pub macro_expansions: usize,
    pub macro_replacement_bytes: usize,
    pub total_macro_bytes: usize,
    pub ambiguity_sites: usize,
    pub ambiguity_candidates: usize,
    pub serialized_bytes: usize,
}

impl Default for LatexAdapterLimitConfig {
    fn default() -> Self {
        Self {
            source_bytes: 1024 * 1024,
            input_tokens: 16_384,
            expanded_tokens: 32_768,
            parse_depth: 128,
            macro_definitions: 64,
            macro_parameters: 4,
            macro_expansion_depth: 16,
            macro_expansions: 4_096,
            macro_replacement_bytes: 64 * 1024,
            total_macro_bytes: 1024 * 1024,
            ambiguity_sites: 64,
            ambiguity_candidates: 4,
            serialized_bytes: 8 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct LatexAdapterLimits(LatexAdapterLimitConfig);

impl LatexAdapterLimits {
    pub const HARD_MAX_SOURCE_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_INPUT_TOKENS: usize = 131_072;
    pub const HARD_MAX_EXPANDED_TOKENS: usize = 262_144;
    pub const HARD_MAX_PARSE_DEPTH: usize = 256;
    pub const HARD_MAX_MACRO_DEFINITIONS: usize = 512;
    pub const HARD_MAX_MACRO_PARAMETERS: u8 = 9;
    pub const HARD_MAX_MACRO_EXPANSION_DEPTH: usize = 64;
    pub const HARD_MAX_MACRO_EXPANSIONS: usize = 65_536;
    pub const HARD_MAX_MACRO_REPLACEMENT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_TOTAL_MACRO_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_AMBIGUITY_SITES: usize = 1_024;
    pub const HARD_MAX_AMBIGUITY_CANDIDATES: usize = 16;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;

    /// Creates finite limits for the P07-02 LaTeX adapter.
    ///
    /// # Errors
    ///
    /// Returns [`LatexAdapterError::InvalidLimit`] for a zero, over-ceiling or internally
    /// inconsistent configuration.
    pub fn new(config: LatexAdapterLimitConfig) -> Result<Self, LatexAdapterError> {
        if config.source_bytes == 0
            || config.source_bytes > Self::HARD_MAX_SOURCE_BYTES
            || config.input_tokens == 0
            || config.input_tokens > Self::HARD_MAX_INPUT_TOKENS
            || config.expanded_tokens == 0
            || config.expanded_tokens > Self::HARD_MAX_EXPANDED_TOKENS
            || config.expanded_tokens < config.input_tokens
            || config.parse_depth == 0
            || config.parse_depth > Self::HARD_MAX_PARSE_DEPTH
            || config.macro_definitions == 0
            || config.macro_definitions > Self::HARD_MAX_MACRO_DEFINITIONS
            || config.macro_parameters > Self::HARD_MAX_MACRO_PARAMETERS
            || config.macro_expansion_depth == 0
            || config.macro_expansion_depth > Self::HARD_MAX_MACRO_EXPANSION_DEPTH
            || config.macro_expansions == 0
            || config.macro_expansions > Self::HARD_MAX_MACRO_EXPANSIONS
            || config.macro_replacement_bytes == 0
            || config.macro_replacement_bytes > Self::HARD_MAX_MACRO_REPLACEMENT_BYTES
            || config.total_macro_bytes == 0
            || config.total_macro_bytes > Self::HARD_MAX_TOTAL_MACRO_BYTES
            || config.total_macro_bytes < config.macro_replacement_bytes
            || config.ambiguity_sites == 0
            || config.ambiguity_sites > Self::HARD_MAX_AMBIGUITY_SITES
            || config.ambiguity_candidates < 2
            || config.ambiguity_candidates > Self::HARD_MAX_AMBIGUITY_CANDIDATES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(LatexAdapterError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> LatexAdapterLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LatexMacroDefinition {
    pub name: String,
    pub parameters: u8,
    pub replacement: String,
}

impl fmt::Debug for LatexMacroDefinition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LatexMacroDefinition")
            .field("name", &"<redacted>")
            .field("parameters", &self.parameters)
            .field("replacement", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LatexParseRequestDraft {
    pub schema_version: String,
    pub source: String,
    #[serde(default)]
    pub macros: Vec<LatexMacroDefinition>,
}

impl fmt::Debug for LatexParseRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LatexParseRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("source", &"<redacted>")
            .field("macros", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum LatexAmbiguityKind {
    ImplicitMultiplication,
    BareMultiLetterIdentifier,
    FunctionApplication,
    UnaryMinusPower,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct LatexAmbiguity {
    pub kind: LatexAmbiguityKind,
    pub span: MathSourceSpan,
}

impl fmt::Debug for LatexAmbiguity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LatexAmbiguity")
            .field("kind", &self.kind)
            .field("span", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum LatexCandidateChoice {
    ConventionalLatex,
    LiteralAdjacency,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct LatexCandidate {
    pub choice: LatexCandidateChoice,
    pub confidence_millionths: u32,
    pub ast: MathAst,
}

impl fmt::Debug for LatexCandidate {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LatexCandidate")
            .field("choice", &self.choice)
            .field("confidence_millionths", &self.confidence_millionths)
            .field("ast", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "state", rename_all = "snake_case")]
pub enum LatexParseOutcome {
    Parsed {
        ast: MathAst,
    },
    Ambiguous {
        confidence_basis: &'static str,
        ambiguities: Vec<LatexAmbiguity>,
        candidates: Vec<LatexCandidate>,
    },
}

impl fmt::Debug for LatexParseOutcome {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Parsed { .. } => formatter.write_str("LatexParseOutcome::Parsed(<redacted>)"),
            Self::Ambiguous {
                ambiguities,
                candidates,
                ..
            } => formatter
                .debug_struct("LatexParseOutcome::Ambiguous")
                .field("ambiguity_count", &ambiguities.len())
                .field("candidate_count", &candidates.len())
                .finish(),
        }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct LatexParseResult {
    schema_version: &'static str,
    parser_version: &'static str,
    math_ast_schema_version: &'static str,
    normalization_version: &'static str,
    source_sha256: String,
    source_length_bytes: u32,
    input_token_count: usize,
    expanded_token_count: usize,
    macro_expansion_count: usize,
    outcome: LatexParseOutcome,
}

impl LatexParseResult {
    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub const fn parser_version(&self) -> &'static str {
        self.parser_version
    }

    #[must_use]
    pub fn source_sha256(&self) -> &str {
        &self.source_sha256
    }

    #[must_use]
    pub const fn source_length_bytes(&self) -> u32 {
        self.source_length_bytes
    }

    #[must_use]
    pub const fn outcome(&self) -> &LatexParseOutcome {
        &self.outcome
    }

    #[must_use]
    pub const fn input_token_count(&self) -> usize {
        self.input_token_count
    }

    #[must_use]
    pub const fn expanded_token_count(&self) -> usize {
        self.expanded_token_count
    }

    #[must_use]
    pub const fn macro_expansion_count(&self) -> usize {
        self.macro_expansion_count
    }

    /// Serializes the complete result without retaining the source or macro bodies.
    ///
    /// # Errors
    ///
    /// Returns a bounded serialization error if the result cannot be encoded within the adapter
    /// limit.
    pub fn canonical_json(&self, limits: LatexAdapterLimits) -> Result<Vec<u8>, LatexAdapterError> {
        let bytes = serde_json::to_vec(self).map_err(|_| LatexAdapterError::Serialization)?;
        if bytes.len() > limits.0.serialized_bytes {
            return Err(LatexAdapterError::OutputLimit);
        }
        Ok(bytes)
    }
}

impl fmt::Debug for LatexParseResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LatexParseResult")
            .field("schema_version", &self.schema_version)
            .field("parser_version", &self.parser_version)
            .field("math_ast_schema_version", &self.math_ast_schema_version)
            .field("normalization_version", &self.normalization_version)
            .field("source_sha256", &"<redacted>")
            .field("source_length_bytes", &"<redacted>")
            .field("input_token_count", &self.input_token_count)
            .field("expanded_token_count", &self.expanded_token_count)
            .field("macro_expansion_count", &self.macro_expansion_count)
            .field("outcome", &self.outcome)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum LatexAdapterError {
    #[error("LaTeX adapter limit configuration is invalid")]
    InvalidLimit,
    #[error("LaTeX request is empty or exceeds its input limit")]
    InputLimit,
    #[error("LaTeX request JSON is invalid")]
    InvalidJson,
    #[error("LaTeX adapter schema version is unsupported")]
    UnsupportedVersion,
    #[error("LaTeX macro definition is invalid")]
    InvalidMacro,
    #[error("LaTeX macro definition is duplicated or reserved")]
    MacroConflict,
    #[error("LaTeX macro recursion is forbidden")]
    MacroRecursion,
    #[error("LaTeX macro expansion exceeded its finite limit")]
    MacroExpansionLimit,
    #[error("LaTeX token limit was exceeded")]
    TokenLimit,
    #[error("LaTeX parser depth limit was exceeded")]
    ParseDepthLimit,
    #[error("LaTeX syntax is malformed")]
    InvalidSyntax,
    #[error("LaTeX construct is outside the admitted Tier A profile")]
    UnsupportedSyntax,
    #[error("LaTeX ambiguity candidates exceeded their finite limit")]
    AmbiguityLimit,
    #[error("LaTeX could not be admitted into MathAst")]
    MathAst,
    #[error("LaTeX result exceeds its output limit")]
    OutputLimit,
    #[error("LaTeX result serialization failed")]
    Serialization,
}

impl LatexAdapterError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "latex_adapter_invalid_limit",
            Self::InputLimit => "latex_adapter_input_limit",
            Self::InvalidJson => "latex_adapter_invalid_json",
            Self::UnsupportedVersion => "latex_adapter_unsupported_version",
            Self::InvalidMacro => "latex_adapter_invalid_macro",
            Self::MacroConflict => "latex_adapter_macro_conflict",
            Self::MacroRecursion => "latex_adapter_macro_recursion",
            Self::MacroExpansionLimit => "latex_adapter_macro_expansion_limit",
            Self::TokenLimit => "latex_adapter_token_limit",
            Self::ParseDepthLimit => "latex_adapter_parse_depth_limit",
            Self::InvalidSyntax => "latex_adapter_invalid_syntax",
            Self::UnsupportedSyntax => "latex_adapter_unsupported_syntax",
            Self::AmbiguityLimit => "latex_adapter_ambiguity_limit",
            Self::MathAst => "latex_adapter_math_ast",
            Self::OutputLimit => "latex_adapter_output_limit",
            Self::Serialization => "latex_adapter_serialization",
        }
    }
}

#[derive(Clone)]
struct Token {
    kind: TokenKind,
    span: MathSourceSpan,
}

#[derive(Clone)]
enum TokenKind {
    Number(String),
    Identifier(String),
    Text(String),
    OperatorName(String),
    Parameter(u8),
    Command(String),
    Plus,
    Minus,
    Star,
    Slash,
    Equal,
    Less,
    Greater,
    Caret,
    Underscore,
    Bang,
    LeftBrace,
    RightBrace,
    LeftParenthesis,
    RightParenthesis,
    LeftBracket,
    RightBracket,
    Comma,
    VerticalBar,
}

fn span(start: usize, end: usize) -> Result<MathSourceSpan, LatexAdapterError> {
    Ok(MathSourceSpan {
        start_byte: u32::try_from(start).map_err(|_| LatexAdapterError::InputLimit)?,
        end_byte: u32::try_from(end).map_err(|_| LatexAdapterError::InputLimit)?,
    })
}

fn lex(source: &str, template: bool, limit: usize) -> Result<Vec<Token>, LatexAdapterError> {
    let mut tokens = Vec::new();
    let mut index = 0usize;
    while index < source.len() {
        let character = source[index..]
            .chars()
            .next()
            .ok_or(LatexAdapterError::InvalidSyntax)?;
        if character.is_whitespace() {
            index += character.len_utf8();
            continue;
        }
        let start = index;
        let (kind, next) = lex_one(source, index, template)?;
        index = next;
        if let Some(kind) = kind {
            tokens.push(Token {
                kind,
                span: span(start, index)?,
            });
            if tokens.len() > limit {
                return Err(LatexAdapterError::TokenLimit);
            }
        }
    }
    if tokens.is_empty() {
        return Err(LatexAdapterError::InputLimit);
    }
    Ok(tokens)
}

fn lex_one(
    source: &str,
    index: usize,
    template: bool,
) -> Result<(Option<TokenKind>, usize), LatexAdapterError> {
    let character = source[index..]
        .chars()
        .next()
        .ok_or(LatexAdapterError::InvalidSyntax)?;
    match character {
        '0'..='9' => lex_number(source, index).map(|(kind, next)| (Some(kind), next)),
        '\\' => lex_control(source, index),
        '#' if template => {
            let digit = source
                .as_bytes()
                .get(index + 1)
                .copied()
                .filter(u8::is_ascii_digit)
                .ok_or(LatexAdapterError::InvalidMacro)?;
            Ok((Some(TokenKind::Parameter(digit - b'0')), index + 2))
        }
        '%' | '&' | '$' | '~' | '#' => Err(LatexAdapterError::UnsupportedSyntax),
        _ if character.is_alphabetic() => {
            let mut end = index + character.len_utf8();
            while end < source.len() {
                let next = source[end..]
                    .chars()
                    .next()
                    .ok_or(LatexAdapterError::InvalidSyntax)?;
                if !next.is_alphabetic() {
                    break;
                }
                end += next.len_utf8();
            }
            Ok((
                Some(TokenKind::Identifier(source[index..end].to_owned())),
                end,
            ))
        }
        _ => simple_token(character)
            .map(|kind| (Some(kind), index + character.len_utf8()))
            .ok_or(LatexAdapterError::UnsupportedSyntax),
    }
}

fn lex_number(source: &str, start: usize) -> Result<(TokenKind, usize), LatexAdapterError> {
    let bytes = source.as_bytes();
    let mut end = start + 1;
    while end < bytes.len() && bytes[end].is_ascii_digit() {
        end += 1;
    }
    if end < bytes.len() && bytes[end] == b'.' {
        end += 1;
        let fractional_start = end;
        while end < bytes.len() && bytes[end].is_ascii_digit() {
            end += 1;
        }
        if fractional_start == end {
            return Err(LatexAdapterError::InvalidSyntax);
        }
    }
    Ok((TokenKind::Number(source[start..end].to_owned()), end))
}

fn lex_control(
    source: &str,
    start: usize,
) -> Result<(Option<TokenKind>, usize), LatexAdapterError> {
    let bytes = source.as_bytes();
    let mut end = start + 1;
    if end >= bytes.len() {
        return Err(LatexAdapterError::InvalidSyntax);
    }
    if bytes[end].is_ascii_alphabetic() {
        let name_start = end;
        while end < bytes.len() && bytes[end].is_ascii_alphabetic() {
            end += 1;
        }
        let name = &source[name_start..end];
        if matches!(name, "text" | "operatorname") {
            let (value, literal_end) = scan_literal_group(source, end)?;
            let kind = if name == "text" {
                TokenKind::Text(value)
            } else {
                TokenKind::OperatorName(value)
            };
            return Ok((Some(kind), literal_end));
        }
        return Ok((Some(TokenKind::Command(name.to_owned())), end));
    }
    let escaped = source[end..]
        .chars()
        .next()
        .ok_or(LatexAdapterError::InvalidSyntax)?;
    end += escaped.len_utf8();
    if matches!(escaped, ',' | ';' | ':' | '!' | ' ') {
        Ok((None, end))
    } else {
        Ok((Some(TokenKind::Command(escaped.to_string())), end))
    }
}

const fn simple_token(character: char) -> Option<TokenKind> {
    match character {
        '+' => Some(TokenKind::Plus),
        '-' => Some(TokenKind::Minus),
        '*' => Some(TokenKind::Star),
        '/' => Some(TokenKind::Slash),
        '=' => Some(TokenKind::Equal),
        '<' => Some(TokenKind::Less),
        '>' => Some(TokenKind::Greater),
        '^' => Some(TokenKind::Caret),
        '_' => Some(TokenKind::Underscore),
        '!' => Some(TokenKind::Bang),
        '{' => Some(TokenKind::LeftBrace),
        '}' => Some(TokenKind::RightBrace),
        '(' => Some(TokenKind::LeftParenthesis),
        ')' => Some(TokenKind::RightParenthesis),
        '[' => Some(TokenKind::LeftBracket),
        ']' => Some(TokenKind::RightBracket),
        ',' => Some(TokenKind::Comma),
        '|' => Some(TokenKind::VerticalBar),
        _ => None,
    }
}

fn scan_literal_group(source: &str, index: usize) -> Result<(String, usize), LatexAdapterError> {
    let bytes = source.as_bytes();
    if bytes.get(index) != Some(&b'{') {
        return Err(LatexAdapterError::InvalidSyntax);
    }
    let content_start = index + 1;
    let mut cursor = content_start;
    let mut escaped = false;
    while cursor < bytes.len() {
        let character = source[cursor..]
            .chars()
            .next()
            .ok_or(LatexAdapterError::InvalidSyntax)?;
        let width = character.len_utf8();
        if escaped {
            if !matches!(character, '{' | '}' | '\\' | '_' | '%') {
                return Err(LatexAdapterError::UnsupportedSyntax);
            }
            escaped = false;
            cursor += width;
            continue;
        }
        match character {
            '\\' => escaped = true,
            '{' => return Err(LatexAdapterError::UnsupportedSyntax),
            '}' => {
                let value = source[content_start..cursor]
                    .replace("\\{", "{")
                    .replace("\\}", "}")
                    .replace("\\_", "_")
                    .replace("\\%", "%")
                    .replace("\\\\", "\\");
                if value.is_empty() || value.chars().any(char::is_control) {
                    return Err(LatexAdapterError::InvalidSyntax);
                }
                return Ok((value, cursor + width));
            }
            _ if character.is_control() => return Err(LatexAdapterError::InvalidSyntax),
            _ => {}
        }
        cursor += width;
    }
    Err(LatexAdapterError::InvalidSyntax)
}

struct MacroTemplate {
    parameters: u8,
    tokens: Vec<Token>,
}

struct ExpansionState {
    expansions: usize,
}

const RESERVED_COMMANDS: &[&str] = &[
    "frac",
    "sqrt",
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "log",
    "ln",
    "exp",
    "min",
    "max",
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "omicron",
    "pi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "phi",
    "chi",
    "psi",
    "omega",
    "Gamma",
    "Delta",
    "Theta",
    "Lambda",
    "Xi",
    "Pi",
    "Sigma",
    "Upsilon",
    "Phi",
    "Psi",
    "Omega",
    "infty",
    "emptyset",
    "aleph",
    "hbar",
    "partial",
    "nabla",
    "therefore",
    "because",
    "ldots",
    "vdots",
    "ddots",
    "circ",
    "prime",
    "cdot",
    "times",
    "div",
    "ne",
    "neq",
    "le",
    "leq",
    "ge",
    "geq",
    "approx",
    "propto",
    "land",
    "lor",
    "neg",
    "implies",
    "iff",
    "in",
    "notin",
    "subset",
    "subseteq",
    "supset",
    "supseteq",
    "cup",
    "cap",
    "setminus",
    "circ",
    "vec",
    "hat",
    "bar",
    "tilde",
    "dot",
    "ddot",
    "check",
    "acute",
    "grave",
    "sum",
    "prod",
    "lim",
    "int",
    "iint",
    "iiint",
    "oint",
    "dv",
    "pdv",
    "binom",
    "set",
    "left",
    "right",
    "langle",
    "rangle",
    "lvert",
    "rvert",
    "lVert",
    "rVert",
    "lfloor",
    "rfloor",
    "lceil",
    "rceil",
    "mathbf",
    "mathrm",
    "mathit",
    "mathbb",
    "mathfrak",
    "mathsf",
    "mathtt",
    "text",
    "operatorname",
    "to",
];

fn build_macros(
    definitions: &[LatexMacroDefinition],
    limits: LatexAdapterLimits,
) -> Result<BTreeMap<String, MacroTemplate>, LatexAdapterError> {
    if definitions.len() > limits.0.macro_definitions {
        return Err(LatexAdapterError::MacroExpansionLimit);
    }
    let mut total_bytes = 0usize;
    let mut macros = BTreeMap::new();
    for definition in definitions {
        if definition.name.is_empty()
            || definition.name.len() > 32
            || !definition
                .name
                .bytes()
                .all(|byte| byte.is_ascii_alphabetic())
            || definition.parameters > limits.0.macro_parameters
            || definition.replacement.is_empty()
            || definition.replacement.len() > limits.0.macro_replacement_bytes
        {
            return Err(LatexAdapterError::InvalidMacro);
        }
        total_bytes = total_bytes
            .checked_add(definition.name.len())
            .and_then(|value| value.checked_add(definition.replacement.len()))
            .ok_or(LatexAdapterError::MacroExpansionLimit)?;
        if total_bytes > limits.0.total_macro_bytes
            || RESERVED_COMMANDS.contains(&definition.name.as_str())
            || macros.contains_key(&definition.name)
        {
            return Err(LatexAdapterError::MacroConflict);
        }
        let tokens = lex(&definition.replacement, true, limits.0.input_tokens)?;
        for token in &tokens {
            if let TokenKind::Parameter(parameter) = token.kind
                && (parameter == 0 || parameter > definition.parameters)
            {
                return Err(LatexAdapterError::InvalidMacro);
            }
        }
        macros.insert(
            definition.name.clone(),
            MacroTemplate {
                parameters: definition.parameters,
                tokens,
            },
        );
    }
    Ok(macros)
}

fn expand_macros(
    input: &[Token],
    macros: &BTreeMap<String, MacroTemplate>,
    limits: LatexAdapterLimits,
) -> Result<(Vec<Token>, usize), LatexAdapterError> {
    let mut state = ExpansionState { expansions: 0 };
    let output = expand_sequence(input, macros, limits, &mut state, 0, &mut Vec::new())?;
    Ok((output, state.expansions))
}

fn expand_sequence(
    input: &[Token],
    macros: &BTreeMap<String, MacroTemplate>,
    limits: LatexAdapterLimits,
    state: &mut ExpansionState,
    depth: usize,
    stack: &mut Vec<String>,
) -> Result<Vec<Token>, LatexAdapterError> {
    if depth > limits.0.macro_expansion_depth {
        return Err(LatexAdapterError::MacroExpansionLimit);
    }
    let mut output = Vec::new();
    let mut index = 0usize;
    while index < input.len() {
        let TokenKind::Command(name) = &input[index].kind else {
            if matches!(input[index].kind, TokenKind::Parameter(_)) {
                return Err(LatexAdapterError::InvalidMacro);
            }
            output.push(input[index].clone());
            index += 1;
            if output.len() > limits.0.expanded_tokens {
                return Err(LatexAdapterError::TokenLimit);
            }
            continue;
        };
        let Some(template) = macros.get(name) else {
            output.push(input[index].clone());
            index += 1;
            continue;
        };
        if stack.iter().any(|active| active == name) {
            return Err(LatexAdapterError::MacroRecursion);
        }
        state.expansions = state
            .expansions
            .checked_add(1)
            .ok_or(LatexAdapterError::MacroExpansionLimit)?;
        if state.expansions > limits.0.macro_expansions {
            return Err(LatexAdapterError::MacroExpansionLimit);
        }
        let invocation_start = input[index].span.start_byte;
        index += 1;
        let mut arguments = Vec::new();
        let mut invocation_end = input[index - 1].span.end_byte;
        for _ in 0..template.parameters {
            let (argument, next, end) = macro_argument(input, index)?;
            arguments.push(argument);
            index = next;
            invocation_end = end;
        }
        let invocation_span = MathSourceSpan {
            start_byte: invocation_start,
            end_byte: invocation_end,
        };
        let mut substituted = Vec::new();
        for token in &template.tokens {
            if let TokenKind::Parameter(parameter) = token.kind {
                let argument = arguments
                    .get(usize::from(parameter - 1))
                    .ok_or(LatexAdapterError::InvalidMacro)?;
                substituted.extend(argument.iter().cloned());
            } else {
                let mut token = token.clone();
                token.span = invocation_span;
                substituted.push(token);
            }
            if substituted.len() > limits.0.expanded_tokens {
                return Err(LatexAdapterError::TokenLimit);
            }
        }
        stack.push(name.clone());
        let expanded = expand_sequence(&substituted, macros, limits, state, depth + 1, stack)?;
        let popped = stack.pop();
        if popped.as_deref() != Some(name) {
            return Err(LatexAdapterError::MacroRecursion);
        }
        output.extend(expanded);
        if output.len() > limits.0.expanded_tokens {
            return Err(LatexAdapterError::TokenLimit);
        }
    }
    Ok(output)
}

fn macro_argument(
    input: &[Token],
    index: usize,
) -> Result<(Vec<Token>, usize, u32), LatexAdapterError> {
    if !matches!(
        input.get(index).map(|token| &token.kind),
        Some(TokenKind::LeftBrace)
    ) {
        return Err(LatexAdapterError::InvalidSyntax);
    }
    let mut depth = 1usize;
    let mut cursor = index + 1;
    while cursor < input.len() {
        match input[cursor].kind {
            TokenKind::LeftBrace => depth += 1,
            TokenKind::RightBrace => {
                depth -= 1;
                if depth == 0 {
                    if cursor == index + 1 {
                        return Err(LatexAdapterError::InvalidSyntax);
                    }
                    return Ok((
                        input[index + 1..cursor].to_vec(),
                        cursor + 1,
                        input[cursor].span.end_byte,
                    ));
                }
            }
            _ => {}
        }
        cursor += 1;
    }
    Err(LatexAdapterError::InvalidSyntax)
}

#[derive(Clone, Copy, Debug)]
pub struct LatexAdapter {
    limits: LatexAdapterLimits,
    math_limits: MathAstLimits,
}

impl LatexAdapter {
    /// Creates an adapter whose source limit is also admissible by the supplied `MathAst` limits.
    ///
    /// # Errors
    ///
    /// Returns [`LatexAdapterError::InvalidLimit`] if the two finite limit sets are inconsistent.
    pub fn new(
        limits: LatexAdapterLimits,
        math_limits: MathAstLimits,
    ) -> Result<Self, LatexAdapterError> {
        let math_source_limit = usize::try_from(math_limits.config().source_bytes)
            .map_err(|_| LatexAdapterError::InvalidLimit)?;
        if limits.0.source_bytes > math_source_limit {
            return Err(LatexAdapterError::InvalidLimit);
        }
        Ok(Self {
            limits,
            math_limits,
        })
    }

    /// Parses a strict JSON request and returns either one admitted AST or explicit candidates.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate-field, unknown-field and oversized JSON before parsing source.
    pub fn parse_json(&self, bytes: &[u8]) -> Result<LatexParseResult, LatexAdapterError> {
        if bytes.is_empty() || bytes.len() > self.limits.0.serialized_bytes {
            return Err(LatexAdapterError::InputLimit);
        }
        let request = serde_json::from_slice(bytes).map_err(|_| LatexAdapterError::InvalidJson)?;
        self.parse(request)
    }

    /// Parses the finite Tier A profile without choosing an ambiguous source interpretation.
    ///
    /// # Errors
    ///
    /// Rejects unsupported syntax, malformed or recursive macros, limit breaches and `MathAst`
    /// admission failures without returning a partial AST.
    pub fn parse(
        &self,
        request: LatexParseRequestDraft,
    ) -> Result<LatexParseResult, LatexAdapterError> {
        let LatexParseRequestDraft {
            schema_version,
            source,
            macros,
        } = request;
        if schema_version != LATEX_ADAPTER_SCHEMA_VERSION {
            return Err(LatexAdapterError::UnsupportedVersion);
        }
        if source.is_empty()
            || source.len() > self.limits.0.source_bytes
            || source.len() > u32::MAX as usize
        {
            return Err(LatexAdapterError::InputLimit);
        }
        let input = lex(&source, false, self.limits.0.input_tokens)?;
        let input_token_count = input.len();
        let definitions = build_macros(&macros, self.limits)?;
        let (expanded, macro_expansion_count) = expand_macros(&input, &definitions, self.limits)?;
        let expanded_token_count = expanded.len();
        let (preferred_root, preferred_ambiguities) = Parser::new(
            &expanded,
            ParseMode::Conventional,
            self.limits.0.parse_depth,
        )
        .parse()?;
        let source_length_bytes =
            u32::try_from(source.len()).map_err(|_| LatexAdapterError::InputLimit)?;
        let preferred = self.admit(preferred_root, source_length_bytes)?;
        let outcome = if preferred_ambiguities.is_empty() {
            LatexParseOutcome::Parsed { ast: preferred }
        } else {
            if self.limits.0.ambiguity_candidates < 2 {
                return Err(LatexAdapterError::AmbiguityLimit);
            }
            let (alternate_root, alternate_ambiguities) = Parser::new(
                &expanded,
                ParseMode::LiteralAdjacency,
                self.limits.0.parse_depth,
            )
            .parse()?;
            let alternate = self.admit(alternate_root, source_length_bytes)?;
            let mut by_site = BTreeMap::new();
            for ambiguity in preferred_ambiguities
                .into_iter()
                .chain(alternate_ambiguities)
            {
                by_site
                    .entry((
                        ambiguity.kind,
                        ambiguity.span.start_byte,
                        ambiguity.span.end_byte,
                    ))
                    .or_insert(ambiguity);
            }
            if by_site.len() > self.limits.0.ambiguity_sites {
                return Err(LatexAdapterError::AmbiguityLimit);
            }
            LatexParseOutcome::Ambiguous {
                confidence_basis: "deterministic_syntax_preference_not_empirical_probability",
                ambiguities: by_site.into_values().collect(),
                candidates: vec![
                    LatexCandidate {
                        choice: LatexCandidateChoice::ConventionalLatex,
                        confidence_millionths: 600_000,
                        ast: preferred,
                    },
                    LatexCandidate {
                        choice: LatexCandidateChoice::LiteralAdjacency,
                        confidence_millionths: 400_000,
                        ast: alternate,
                    },
                ],
            }
        };
        let result = LatexParseResult {
            schema_version: LATEX_ADAPTER_SCHEMA_VERSION,
            parser_version: LATEX_PARSER_VERSION,
            math_ast_schema_version: MATH_AST_SCHEMA_VERSION,
            normalization_version: MATH_AST_NORMALIZATION_VERSION,
            source_sha256: hex::encode(Sha256::digest(source.as_bytes())),
            source_length_bytes,
            input_token_count,
            expanded_token_count,
            macro_expansion_count,
            outcome,
        };
        let _ = result.canonical_json(self.limits)?;
        Ok(result)
    }

    fn admit(
        &self,
        root: MathNode,
        source_length_bytes: u32,
    ) -> Result<MathAst, LatexAdapterError> {
        MathAst::from_draft(
            MathAstDraft {
                schema_version: MATH_AST_SCHEMA_VERSION.to_owned(),
                normalization_version: MATH_AST_NORMALIZATION_VERSION.to_owned(),
                source_length_bytes,
                root,
            },
            self.math_limits,
        )
        .map_err(|_| LatexAdapterError::MathAst)
    }
}

#[derive(Clone, Copy, Eq, PartialEq)]
enum ParseMode {
    Conventional,
    LiteralAdjacency,
}

struct Parser<'a> {
    tokens: &'a [Token],
    index: usize,
    mode: ParseMode,
    depth: usize,
    max_depth: usize,
    ambiguities: BTreeMap<(LatexAmbiguityKind, u32, u32), LatexAmbiguity>,
}

impl<'a> Parser<'a> {
    fn new(tokens: &'a [Token], mode: ParseMode, max_depth: usize) -> Self {
        Self {
            tokens,
            index: 0,
            mode,
            depth: 0,
            max_depth,
            ambiguities: BTreeMap::new(),
        }
    }

    fn parse(mut self) -> Result<(MathNode, Vec<LatexAmbiguity>), LatexAdapterError> {
        let root = self.parse_expression(0)?;
        if self.index != self.tokens.len() {
            return Err(LatexAdapterError::InvalidSyntax);
        }
        Ok((root, self.ambiguities.into_values().collect()))
    }

    fn parse_expression(&mut self, minimum: u8) -> Result<MathNode, LatexAdapterError> {
        if self.depth >= self.max_depth {
            return Err(LatexAdapterError::ParseDepthLimit);
        }
        self.depth += 1;
        let result = self.parse_expression_inner(minimum);
        self.depth -= 1;
        result
    }

    fn parse_expression_inner(&mut self, minimum: u8) -> Result<MathNode, LatexAdapterError> {
        let mut left = self.parse_prefix()?;
        loop {
            if let Some(name) = bare_identifier(&left)
                && matches!(self.peek_kind(), Some(TokenKind::LeftParenthesis))
            {
                if 45 < minimum {
                    break;
                }
                let (arguments, group_span, body) = self.parse_parenthesized_arguments()?;
                let ambiguity_span = merged_span(left.span, group_span);
                self.record_ambiguity(LatexAmbiguityKind::FunctionApplication, ambiguity_span);
                left = if self.mode == ParseMode::Conventional {
                    make_node(
                        ambiguity_span,
                        MathExpression::Function {
                            function: MathFunction::Named {
                                name: name.to_owned(),
                            },
                            arguments,
                        },
                    )
                } else {
                    make_apply(
                        MathOperator::Multiply,
                        vec![
                            left,
                            make_node(
                                group_span,
                                MathExpression::Delimited {
                                    left: MathDelimiter::LeftParenthesis,
                                    body: Box::new(body),
                                    right: MathDelimiter::RightParenthesis,
                                },
                            ),
                        ],
                    )
                };
                continue;
            }

            if let Some((operator, precedence)) = self.infix_operator() {
                if precedence < minimum {
                    break;
                }
                if is_relation(operator) && relation_root(&left) {
                    return Err(LatexAdapterError::UnsupportedSyntax);
                }
                self.index += 1;
                let right = self.parse_expression(precedence + 1)?;
                left = make_apply(operator, vec![left, right]);
                continue;
            }

            if self.starts_primary() {
                if 45 < minimum {
                    break;
                }
                let right = self.parse_expression(46)?;
                let ambiguity_span = merged_span(left.span, right.span);
                self.record_ambiguity(LatexAmbiguityKind::ImplicitMultiplication, ambiguity_span);
                left = if self.mode == ParseMode::Conventional {
                    make_apply(MathOperator::Multiply, vec![left, right])
                } else {
                    make_row(vec![left, right])
                };
                continue;
            }
            break;
        }
        Ok(left)
    }

    fn parse_prefix(&mut self) -> Result<MathNode, LatexAdapterError> {
        if matches!(self.peek_kind(), Some(TokenKind::Plus | TokenKind::Minus)) {
            let operator_token = self
                .next()
                .cloned()
                .ok_or(LatexAdapterError::InvalidSyntax)?;
            let operator = if matches!(operator_token.kind, TokenKind::Plus) {
                MathOperator::Positive
            } else {
                MathOperator::Negative
            };
            let operand = self.parse_expression(50)?;
            let operand_source_span = operand.span;
            if operator == MathOperator::Negative
                && matches!(
                    operand.expression,
                    MathExpression::Script {
                        superscript: Some(_),
                        ..
                    }
                )
            {
                let ambiguity_span = merged_span(operator_token.span, operand.span);
                self.record_ambiguity(LatexAmbiguityKind::UnaryMinusPower, ambiguity_span);
                if self.mode == ParseMode::LiteralAdjacency {
                    return move_unary_inside_script(operator, operator_token.span, operand);
                }
            }
            return Ok(make_apply_with_span(
                operator,
                vec![operand],
                merged_span(operator_token.span, operand_source_span),
            ));
        }
        self.parse_postfixed_primary()
    }

    fn parse_postfixed_primary(&mut self) -> Result<MathNode, LatexAdapterError> {
        let mut base = self.parse_primary()?;
        let mut subscript = None;
        let mut superscript = None;
        while matches!(
            self.peek_kind(),
            Some(TokenKind::Caret | TokenKind::Underscore)
        ) {
            let marker = self
                .next()
                .cloned()
                .ok_or(LatexAdapterError::InvalidSyntax)?;
            let argument = self.parse_script_argument()?;
            if matches!(marker.kind, TokenKind::Caret) {
                if superscript.is_some() {
                    return Err(LatexAdapterError::InvalidSyntax);
                }
                superscript = Some(Box::new(argument));
            } else {
                if subscript.is_some() {
                    return Err(LatexAdapterError::InvalidSyntax);
                }
                subscript = Some(Box::new(argument));
            }
        }
        if subscript.is_some() || superscript.is_some() {
            let script_span = subscript
                .as_deref()
                .into_iter()
                .chain(superscript.as_deref())
                .map(|node| node.span)
                .fold(base.span, merged_span);
            base = make_node(
                script_span,
                MathExpression::Script {
                    base: Box::new(base),
                    subscript,
                    superscript,
                },
            );
        }
        while matches!(self.peek_kind(), Some(TokenKind::Bang)) {
            let marker = self
                .next()
                .cloned()
                .ok_or(LatexAdapterError::InvalidSyntax)?;
            let result_span = merged_span(base.span, marker.span);
            base = make_apply_with_span(MathOperator::Factorial, vec![base], result_span);
        }
        Ok(base)
    }

    fn parse_primary(&mut self) -> Result<MathNode, LatexAdapterError> {
        let token = self
            .next()
            .cloned()
            .ok_or(LatexAdapterError::InvalidSyntax)?;
        match token.kind {
            TokenKind::Number(value) => Ok(make_node(token.span, MathExpression::Number { value })),
            TokenKind::Identifier(name) => Ok(self.parse_identifier(name, token.span)),
            TokenKind::Text(value) => Ok(make_node(token.span, MathExpression::Text { value })),
            TokenKind::OperatorName(name) => self.parse_named_function(name, token.span),
            TokenKind::LeftBrace => self.parse_group_after_open(token.span),
            TokenKind::LeftParenthesis => self.parse_delimited_after_open(
                token.span,
                &TokenKind::RightParenthesis,
                MathDelimiter::LeftParenthesis,
                MathDelimiter::RightParenthesis,
            ),
            TokenKind::LeftBracket => self.parse_delimited_after_open(
                token.span,
                &TokenKind::RightBracket,
                MathDelimiter::LeftBracket,
                MathDelimiter::RightBracket,
            ),
            TokenKind::VerticalBar => self.parse_delimited_after_open(
                token.span,
                &TokenKind::VerticalBar,
                MathDelimiter::VerticalBar,
                MathDelimiter::VerticalBar,
            ),
            TokenKind::Command(name) => self.parse_command(&name, token.span),
            _ => Err(LatexAdapterError::InvalidSyntax),
        }
    }

    fn parse_identifier(&mut self, name: String, source_span: MathSourceSpan) -> MathNode {
        if name.chars().count() <= 1 {
            return make_identifier(source_span, name);
        }
        self.record_ambiguity(LatexAmbiguityKind::BareMultiLetterIdentifier, source_span);
        if self.mode == ParseMode::LiteralAdjacency {
            return make_identifier(source_span, name);
        }
        let characters = name
            .chars()
            .map(|character| make_identifier(source_span, character.to_string()))
            .collect();
        make_apply_with_span(MathOperator::Multiply, characters, source_span)
    }

    fn parse_group_after_open(
        &mut self,
        open_span: MathSourceSpan,
    ) -> Result<MathNode, LatexAdapterError> {
        let mut body = self.parse_expression(0)?;
        let close = self.expect_kind(&TokenKind::RightBrace)?;
        body.span = merged_span(open_span, close.span);
        Ok(body)
    }

    fn parse_delimited_after_open(
        &mut self,
        open_span: MathSourceSpan,
        close_kind: &TokenKind,
        left: MathDelimiter,
        right: MathDelimiter,
    ) -> Result<MathNode, LatexAdapterError> {
        let body = self.parse_expression(0)?;
        let close = self.expect_kind(close_kind)?;
        Ok(make_node(
            merged_span(open_span, close.span),
            MathExpression::Delimited {
                left,
                body: Box::new(body),
                right,
            },
        ))
    }

    fn parse_command(
        &mut self,
        name: &str,
        command_span: MathSourceSpan,
    ) -> Result<MathNode, LatexAdapterError> {
        if let Some(symbol) = symbol_command(name) {
            return Ok(make_node(command_span, MathExpression::Symbol { symbol }));
        }
        if let Some(function) = function_command(name) {
            return self.parse_function(function, command_span);
        }
        if let Some(accent) = accent_command(name) {
            let base = self.parse_required_group()?;
            return Ok(make_node(
                merged_span(command_span, base.span),
                MathExpression::Accent {
                    accent,
                    base: Box::new(base),
                },
            ));
        }
        if let Some(variant) = style_command(name) {
            let mut base = self.parse_required_group()?;
            let result_span = merged_span(command_span, base.span);
            let style = base.style.get_or_insert(MathStyleHint {
                variant: None,
                color: None,
            });
            if style.variant.is_none() {
                style.variant = Some(variant);
            }
            base.span = result_span;
            return Ok(base);
        }
        match name {
            "frac" => {
                let numerator = self.parse_required_group()?;
                let denominator = self.parse_required_group()?;
                Ok(make_node(
                    merged_span(command_span, denominator.span),
                    MathExpression::Fraction {
                        numerator: Box::new(numerator),
                        denominator: Box::new(denominator),
                    },
                ))
            }
            "sqrt" => self.parse_root(command_span),
            "sum" | "prod" | "lim" | "int" | "iint" | "iiint" | "oint" => {
                self.parse_large_operator(name, command_span)
            }
            "dv" | "pdv" => self.parse_derivative(name, command_span),
            "binom" => {
                let upper = self.parse_required_group()?;
                let lower = self.parse_required_group()?;
                Ok(make_node(
                    merged_span(command_span, lower.span),
                    MathExpression::Combinatorial {
                        combinatorial_kind: MathCombinatorialKind::Binomial,
                        upper: Box::new(upper),
                        lower: Box::new(lower),
                    },
                ))
            }
            "set" => {
                let element = self.parse_required_group()?;
                let condition = self.parse_required_group()?;
                Ok(make_node(
                    merged_span(command_span, condition.span),
                    MathExpression::SetBuilder {
                        element: Box::new(element),
                        condition: Box::new(condition),
                    },
                ))
            }
            "left" => self.parse_left_right(command_span),
            "neg" => {
                let argument = self.parse_postfixed_primary()?;
                let result_span = merged_span(command_span, argument.span);
                Ok(make_apply_with_span(
                    MathOperator::LogicalNot,
                    vec![argument],
                    result_span,
                ))
            }
            _ => Err(LatexAdapterError::UnsupportedSyntax),
        }
    }

    fn parse_named_function(
        &mut self,
        name: String,
        command_span: MathSourceSpan,
    ) -> Result<MathNode, LatexAdapterError> {
        if name.is_empty() || name.chars().any(char::is_whitespace) {
            return Err(LatexAdapterError::InvalidSyntax);
        }
        let (arguments, end) = self.parse_function_arguments()?;
        Ok(make_node(
            MathSourceSpan {
                start_byte: command_span.start_byte,
                end_byte: end,
            },
            MathExpression::Function {
                function: MathFunction::Named { name },
                arguments,
            },
        ))
    }

    fn parse_function(
        &mut self,
        function: MathFunction,
        command_span: MathSourceSpan,
    ) -> Result<MathNode, LatexAdapterError> {
        let mut subscript = None;
        let mut superscript = None;
        while matches!(
            self.peek_kind(),
            Some(TokenKind::Underscore | TokenKind::Caret)
        ) {
            let marker = self
                .next()
                .cloned()
                .ok_or(LatexAdapterError::InvalidSyntax)?;
            let argument = Box::new(self.parse_script_argument()?);
            if matches!(marker.kind, TokenKind::Underscore) {
                if !matches!(&function, MathFunction::Log) || subscript.replace(argument).is_some()
                {
                    return Err(LatexAdapterError::InvalidSyntax);
                }
            } else if superscript.replace(argument).is_some() {
                return Err(LatexAdapterError::InvalidSyntax);
            }
        }
        let (arguments, end) = self.parse_function_arguments()?;
        let function_span = MathSourceSpan {
            start_byte: command_span.start_byte,
            end_byte: end,
        };
        let function_node = make_node(
            function_span,
            MathExpression::Function {
                function,
                arguments,
            },
        );
        if subscript.is_some() || superscript.is_some() {
            Ok(make_node(
                function_span,
                MathExpression::Script {
                    base: Box::new(function_node),
                    subscript,
                    superscript,
                },
            ))
        } else {
            Ok(function_node)
        }
    }

    fn parse_function_arguments(&mut self) -> Result<(Vec<MathNode>, u32), LatexAdapterError> {
        match self.peek_kind() {
            Some(TokenKind::LeftBrace) => {
                let argument = self.parse_required_group()?;
                Ok((vec![argument.clone()], argument.span.end_byte))
            }
            Some(TokenKind::LeftParenthesis) => {
                let (arguments, group_span, _body) = self.parse_parenthesized_arguments()?;
                Ok((arguments, group_span.end_byte))
            }
            _ => {
                let argument = self.parse_postfixed_primary()?;
                Ok((vec![argument.clone()], argument.span.end_byte))
            }
        }
    }

    fn parse_parenthesized_arguments(
        &mut self,
    ) -> Result<(Vec<MathNode>, MathSourceSpan, MathNode), LatexAdapterError> {
        let open = self.expect_kind(&TokenKind::LeftParenthesis)?;
        let mut arguments = Vec::new();
        loop {
            arguments.push(self.parse_expression(0)?);
            if matches!(self.peek_kind(), Some(TokenKind::Comma)) {
                self.index += 1;
                continue;
            }
            break;
        }
        let close = self.expect_kind(&TokenKind::RightParenthesis)?;
        let body = if arguments.len() == 1 {
            arguments[0].clone()
        } else {
            make_row(arguments.clone())
        };
        Ok((arguments, merged_span(open.span, close.span), body))
    }

    fn parse_root(&mut self, command_span: MathSourceSpan) -> Result<MathNode, LatexAdapterError> {
        let degree = if matches!(self.peek_kind(), Some(TokenKind::LeftBracket)) {
            let open = self.expect_kind(&TokenKind::LeftBracket)?;
            let mut value = self.parse_expression(0)?;
            let close = self.expect_kind(&TokenKind::RightBracket)?;
            value.span = merged_span(open.span, close.span);
            Some(Box::new(value))
        } else {
            None
        };
        let radicand = self.parse_required_group()?;
        Ok(make_node(
            merged_span(command_span, radicand.span),
            MathExpression::Root {
                degree,
                radicand: Box::new(radicand),
            },
        ))
    }

    fn parse_large_operator(
        &mut self,
        name: &str,
        command_span: MathSourceSpan,
    ) -> Result<MathNode, LatexAdapterError> {
        let mut lower = None;
        let mut upper = None;
        while matches!(
            self.peek_kind(),
            Some(TokenKind::Caret | TokenKind::Underscore)
        ) {
            let marker = self
                .next()
                .cloned()
                .ok_or(LatexAdapterError::InvalidSyntax)?;
            let argument = self.parse_script_argument()?;
            if matches!(marker.kind, TokenKind::Caret) {
                if upper.replace(Box::new(argument)).is_some() {
                    return Err(LatexAdapterError::InvalidSyntax);
                }
            } else if lower.replace(Box::new(argument)).is_some() {
                return Err(LatexAdapterError::InvalidSyntax);
            }
        }
        let body = self.parse_required_group()?;
        let operator = match name {
            "sum" => MathLargeOperator::Sum,
            "prod" => MathLargeOperator::Product,
            "lim" => MathLargeOperator::Limit,
            "int" => MathLargeOperator::Integral {
                multiplicity: 1,
                contour: false,
            },
            "iint" => MathLargeOperator::Integral {
                multiplicity: 2,
                contour: false,
            },
            "iiint" => MathLargeOperator::Integral {
                multiplicity: 3,
                contour: false,
            },
            "oint" => MathLargeOperator::Integral {
                multiplicity: 1,
                contour: true,
            },
            _ => return Err(LatexAdapterError::UnsupportedSyntax),
        };
        Ok(make_node(
            merged_span(command_span, body.span),
            MathExpression::LargeOperator {
                operator,
                body: Box::new(body),
                lower,
                upper,
            },
        ))
    }

    fn parse_derivative(
        &mut self,
        name: &str,
        command_span: MathSourceSpan,
    ) -> Result<MathNode, LatexAdapterError> {
        let order = if matches!(self.peek_kind(), Some(TokenKind::LeftBracket)) {
            let _open = self.expect_kind(&TokenKind::LeftBracket)?;
            let token = self
                .next()
                .cloned()
                .ok_or(LatexAdapterError::InvalidSyntax)?;
            let TokenKind::Number(value) = token.kind else {
                return Err(LatexAdapterError::InvalidSyntax);
            };
            let parsed = value
                .parse::<u16>()
                .map_err(|_| LatexAdapterError::InvalidSyntax)?;
            let _close = self.expect_kind(&TokenKind::RightBracket)?;
            if parsed == 0 {
                return Err(LatexAdapterError::InvalidSyntax);
            }
            parsed
        } else {
            1
        };
        let expression = self.parse_required_group()?;
        let variable = self.parse_required_group()?;
        Ok(make_node(
            merged_span(command_span, variable.span),
            MathExpression::Derivative {
                derivative_kind: if name == "pdv" {
                    MathDerivativeKind::Partial
                } else {
                    MathDerivativeKind::Ordinary
                },
                expression: Box::new(expression),
                variables: vec![MathDerivativeVariable {
                    variable: Box::new(variable),
                    order,
                }],
            },
        ))
    }

    fn parse_left_right(
        &mut self,
        command_span: MathSourceSpan,
    ) -> Result<MathNode, LatexAdapterError> {
        let left = self.parse_delimiter(true)?;
        let body = self.parse_expression(0)?;
        let right_command = self
            .next()
            .cloned()
            .ok_or(LatexAdapterError::InvalidSyntax)?;
        if !matches!(right_command.kind, TokenKind::Command(ref name) if name == "right") {
            return Err(LatexAdapterError::InvalidSyntax);
        }
        let (right, end_span) = self.parse_delimiter_with_span(false)?;
        Ok(make_node(
            MathSourceSpan {
                start_byte: command_span.start_byte,
                end_byte: end_span.end_byte,
            },
            MathExpression::Delimited {
                left,
                body: Box::new(body),
                right,
            },
        ))
    }

    fn parse_delimiter(&mut self, left_side: bool) -> Result<MathDelimiter, LatexAdapterError> {
        self.parse_delimiter_with_span(left_side)
            .map(|(delimiter, _span)| delimiter)
    }

    fn parse_delimiter_with_span(
        &mut self,
        left_side: bool,
    ) -> Result<(MathDelimiter, MathSourceSpan), LatexAdapterError> {
        let token = self
            .next()
            .cloned()
            .ok_or(LatexAdapterError::InvalidSyntax)?;
        let delimiter = match (&token.kind, left_side) {
            (TokenKind::LeftParenthesis, true) => MathDelimiter::LeftParenthesis,
            (TokenKind::RightParenthesis, false) => MathDelimiter::RightParenthesis,
            (TokenKind::LeftBracket, true) => MathDelimiter::LeftBracket,
            (TokenKind::RightBracket, false) => MathDelimiter::RightBracket,
            (TokenKind::VerticalBar, _) => MathDelimiter::VerticalBar,
            (TokenKind::Command(name), true) if name == "{" => MathDelimiter::LeftBrace,
            (TokenKind::Command(name), false) if name == "}" => MathDelimiter::RightBrace,
            (TokenKind::Command(name), true) if name == "langle" => MathDelimiter::LeftAngle,
            (TokenKind::Command(name), false) if name == "rangle" => MathDelimiter::RightAngle,
            (TokenKind::Command(name), true) if name == "lvert" => MathDelimiter::VerticalBar,
            (TokenKind::Command(name), false) if name == "rvert" => MathDelimiter::VerticalBar,
            (TokenKind::Command(name), true) if name == "lVert" => MathDelimiter::DoubleVerticalBar,
            (TokenKind::Command(name), false) if name == "rVert" => {
                MathDelimiter::DoubleVerticalBar
            }
            (TokenKind::Command(name), true) if name == "lfloor" => MathDelimiter::LeftFloor,
            (TokenKind::Command(name), false) if name == "rfloor" => MathDelimiter::RightFloor,
            (TokenKind::Command(name), true) if name == "lceil" => MathDelimiter::LeftCeiling,
            (TokenKind::Command(name), false) if name == "rceil" => MathDelimiter::RightCeiling,
            _ => return Err(LatexAdapterError::InvalidSyntax),
        };
        Ok((delimiter, token.span))
    }

    fn parse_required_group(&mut self) -> Result<MathNode, LatexAdapterError> {
        let open = self.expect_kind(&TokenKind::LeftBrace)?;
        self.parse_group_after_open(open.span)
    }

    fn parse_script_argument(&mut self) -> Result<MathNode, LatexAdapterError> {
        if matches!(self.peek_kind(), Some(TokenKind::LeftBrace)) {
            self.parse_required_group()
        } else {
            self.parse_primary()
        }
    }

    fn infix_operator(&self) -> Option<(MathOperator, u8)> {
        match self.peek_kind()? {
            TokenKind::Plus => Some((MathOperator::Add, 30)),
            TokenKind::Minus => Some((MathOperator::Subtract, 30)),
            TokenKind::Star => Some((MathOperator::Multiply, 40)),
            TokenKind::Slash => Some((MathOperator::Divide, 40)),
            TokenKind::Equal => Some((MathOperator::Equal, 20)),
            TokenKind::Less => Some((MathOperator::LessThan, 20)),
            TokenKind::Greater => Some((MathOperator::GreaterThan, 20)),
            TokenKind::Command(name) => command_operator(name),
            _ => None,
        }
    }

    fn starts_primary(&self) -> bool {
        match self.peek_kind() {
            Some(
                TokenKind::Number(_)
                | TokenKind::Identifier(_)
                | TokenKind::Text(_)
                | TokenKind::OperatorName(_)
                | TokenKind::LeftBrace
                | TokenKind::LeftParenthesis
                | TokenKind::LeftBracket
                | TokenKind::VerticalBar,
            ) => true,
            Some(TokenKind::Command(name)) => name != "right" && command_operator(name).is_none(),
            _ => false,
        }
    }

    fn record_ambiguity(&mut self, kind: LatexAmbiguityKind, ambiguity_span: MathSourceSpan) {
        self.ambiguities
            .entry((kind, ambiguity_span.start_byte, ambiguity_span.end_byte))
            .or_insert(LatexAmbiguity {
                kind,
                span: ambiguity_span,
            });
    }

    fn peek_kind(&self) -> Option<&TokenKind> {
        self.tokens.get(self.index).map(|token| &token.kind)
    }

    fn next(&mut self) -> Option<&Token> {
        let token = self.tokens.get(self.index);
        self.index += usize::from(token.is_some());
        token
    }

    fn expect_kind(&mut self, expected: &TokenKind) -> Result<Token, LatexAdapterError> {
        let token = self
            .next()
            .cloned()
            .ok_or(LatexAdapterError::InvalidSyntax)?;
        if std::mem::discriminant(&token.kind) != std::mem::discriminant(expected) {
            return Err(LatexAdapterError::InvalidSyntax);
        }
        Ok(token)
    }
}

fn make_node(source_span: MathSourceSpan, expression: MathExpression) -> MathNode {
    MathNode {
        span: source_span,
        style: None,
        expression,
    }
}

fn make_identifier(source_span: MathSourceSpan, name: String) -> MathNode {
    make_node(source_span, MathExpression::Identifier { name })
}

fn make_apply(operator: MathOperator, arguments: Vec<MathNode>) -> MathNode {
    let source_span = arguments
        .iter()
        .map(|node| node.span)
        .reduce(merged_span)
        .unwrap_or(MathSourceSpan {
            start_byte: 0,
            end_byte: 0,
        });
    make_apply_with_span(operator, arguments, source_span)
}

fn make_apply_with_span(
    operator: MathOperator,
    arguments: Vec<MathNode>,
    source_span: MathSourceSpan,
) -> MathNode {
    make_node(
        source_span,
        MathExpression::Apply {
            operator,
            arguments,
        },
    )
}

fn make_row(items: Vec<MathNode>) -> MathNode {
    let source_span = items
        .iter()
        .map(|node| node.span)
        .reduce(merged_span)
        .unwrap_or(MathSourceSpan {
            start_byte: 0,
            end_byte: 0,
        });
    make_node(source_span, MathExpression::Row { items })
}

const fn merged_span(left: MathSourceSpan, right: MathSourceSpan) -> MathSourceSpan {
    MathSourceSpan {
        start_byte: if left.start_byte < right.start_byte {
            left.start_byte
        } else {
            right.start_byte
        },
        end_byte: if left.end_byte > right.end_byte {
            left.end_byte
        } else {
            right.end_byte
        },
    }
}

fn bare_identifier(node: &MathNode) -> Option<&str> {
    if let MathExpression::Identifier { name } = &node.expression {
        Some(name)
    } else {
        None
    }
}

fn move_unary_inside_script(
    operator: MathOperator,
    operator_span: MathSourceSpan,
    operand: MathNode,
) -> Result<MathNode, LatexAdapterError> {
    let MathExpression::Script {
        base,
        subscript,
        superscript,
    } = operand.expression
    else {
        return Err(LatexAdapterError::InvalidSyntax);
    };
    let negative_span = merged_span(operator_span, base.span);
    let negative = make_apply_with_span(operator, vec![*base], negative_span);
    Ok(MathNode {
        span: merged_span(operator_span, operand.span),
        style: operand.style,
        expression: MathExpression::Script {
            base: Box::new(negative),
            subscript,
            superscript,
        },
    })
}

const fn is_relation(operator: MathOperator) -> bool {
    matches!(
        operator,
        MathOperator::Equal
            | MathOperator::NotEqual
            | MathOperator::LessThan
            | MathOperator::LessThanOrEqual
            | MathOperator::GreaterThan
            | MathOperator::GreaterThanOrEqual
            | MathOperator::ApproximatelyEqual
            | MathOperator::ProportionalTo
            | MathOperator::ElementOf
            | MathOperator::NotElementOf
            | MathOperator::SubsetOf
            | MathOperator::ProperSubsetOf
            | MathOperator::SupersetOf
            | MathOperator::ProperSupersetOf
    )
}

fn relation_root(node: &MathNode) -> bool {
    matches!(
        node.expression,
        MathExpression::Apply { operator, .. } if is_relation(operator)
    )
}

fn command_operator(name: &str) -> Option<(MathOperator, u8)> {
    match name {
        "cdot" | "times" => Some((MathOperator::Multiply, 40)),
        "div" => Some((MathOperator::Divide, 40)),
        "ne" | "neq" => Some((MathOperator::NotEqual, 20)),
        "le" | "leq" => Some((MathOperator::LessThanOrEqual, 20)),
        "ge" | "geq" => Some((MathOperator::GreaterThanOrEqual, 20)),
        "approx" => Some((MathOperator::ApproximatelyEqual, 20)),
        "propto" => Some((MathOperator::ProportionalTo, 20)),
        "in" => Some((MathOperator::ElementOf, 20)),
        "notin" => Some((MathOperator::NotElementOf, 20)),
        "subset" => Some((MathOperator::ProperSubsetOf, 20)),
        "subseteq" => Some((MathOperator::SubsetOf, 20)),
        "supset" => Some((MathOperator::ProperSupersetOf, 20)),
        "supseteq" => Some((MathOperator::SupersetOf, 20)),
        "cup" => Some((MathOperator::Union, 25)),
        "cap" => Some((MathOperator::Intersection, 25)),
        "setminus" => Some((MathOperator::SetDifference, 25)),
        "circ" => Some((MathOperator::Compose, 40)),
        "land" => Some((MathOperator::LogicalAnd, 15)),
        "lor" => Some((MathOperator::LogicalOr, 10)),
        "implies" => Some((MathOperator::Implies, 8)),
        "iff" => Some((MathOperator::Equivalent, 8)),
        _ => None,
    }
}

fn function_command(name: &str) -> Option<MathFunction> {
    match name {
        "sin" => Some(MathFunction::Sin),
        "cos" => Some(MathFunction::Cos),
        "tan" => Some(MathFunction::Tan),
        "cot" => Some(MathFunction::Cot),
        "sec" => Some(MathFunction::Sec),
        "csc" => Some(MathFunction::Csc),
        "arcsin" => Some(MathFunction::Arcsin),
        "arccos" => Some(MathFunction::Arccos),
        "arctan" => Some(MathFunction::Arctan),
        "sinh" => Some(MathFunction::Sinh),
        "cosh" => Some(MathFunction::Cosh),
        "tanh" => Some(MathFunction::Tanh),
        "log" => Some(MathFunction::Log),
        "ln" => Some(MathFunction::NaturalLog),
        "exp" => Some(MathFunction::Exponential),
        "min" => Some(MathFunction::Minimum),
        "max" => Some(MathFunction::Maximum),
        _ => None,
    }
}

fn accent_command(name: &str) -> Option<MathAccent> {
    match name {
        "vec" => Some(MathAccent::VectorArrow),
        "hat" => Some(MathAccent::Hat),
        "bar" => Some(MathAccent::Bar),
        "tilde" => Some(MathAccent::Tilde),
        "dot" => Some(MathAccent::Dot),
        "ddot" => Some(MathAccent::DoubleDot),
        "check" => Some(MathAccent::Check),
        "acute" => Some(MathAccent::Acute),
        "grave" => Some(MathAccent::Grave),
        _ => None,
    }
}

fn style_command(name: &str) -> Option<MathVariant> {
    match name {
        "mathbf" => Some(MathVariant::Bold),
        "mathrm" => Some(MathVariant::Upright),
        "mathit" => Some(MathVariant::Italic),
        "mathbb" => Some(MathVariant::DoubleStruck),
        "mathfrak" => Some(MathVariant::Fraktur),
        "mathsf" => Some(MathVariant::SansSerif),
        "mathtt" => Some(MathVariant::Monospace),
        _ => None,
    }
}

fn symbol_command(name: &str) -> Option<MathSymbol> {
    let greek = match name {
        "alpha" => Some((MathGreekLetter::Alpha, MathLetterCase::Lower)),
        "beta" => Some((MathGreekLetter::Beta, MathLetterCase::Lower)),
        "gamma" => Some((MathGreekLetter::Gamma, MathLetterCase::Lower)),
        "delta" => Some((MathGreekLetter::Delta, MathLetterCase::Lower)),
        "epsilon" => Some((MathGreekLetter::Epsilon, MathLetterCase::Lower)),
        "zeta" => Some((MathGreekLetter::Zeta, MathLetterCase::Lower)),
        "eta" => Some((MathGreekLetter::Eta, MathLetterCase::Lower)),
        "theta" => Some((MathGreekLetter::Theta, MathLetterCase::Lower)),
        "iota" => Some((MathGreekLetter::Iota, MathLetterCase::Lower)),
        "kappa" => Some((MathGreekLetter::Kappa, MathLetterCase::Lower)),
        "lambda" => Some((MathGreekLetter::Lambda, MathLetterCase::Lower)),
        "mu" => Some((MathGreekLetter::Mu, MathLetterCase::Lower)),
        "nu" => Some((MathGreekLetter::Nu, MathLetterCase::Lower)),
        "xi" => Some((MathGreekLetter::Xi, MathLetterCase::Lower)),
        "omicron" => Some((MathGreekLetter::Omicron, MathLetterCase::Lower)),
        "pi" => Some((MathGreekLetter::Pi, MathLetterCase::Lower)),
        "rho" => Some((MathGreekLetter::Rho, MathLetterCase::Lower)),
        "sigma" => Some((MathGreekLetter::Sigma, MathLetterCase::Lower)),
        "tau" => Some((MathGreekLetter::Tau, MathLetterCase::Lower)),
        "upsilon" => Some((MathGreekLetter::Upsilon, MathLetterCase::Lower)),
        "phi" => Some((MathGreekLetter::Phi, MathLetterCase::Lower)),
        "chi" => Some((MathGreekLetter::Chi, MathLetterCase::Lower)),
        "psi" => Some((MathGreekLetter::Psi, MathLetterCase::Lower)),
        "omega" => Some((MathGreekLetter::Omega, MathLetterCase::Lower)),
        "Gamma" => Some((MathGreekLetter::Gamma, MathLetterCase::Upper)),
        "Delta" => Some((MathGreekLetter::Delta, MathLetterCase::Upper)),
        "Theta" => Some((MathGreekLetter::Theta, MathLetterCase::Upper)),
        "Lambda" => Some((MathGreekLetter::Lambda, MathLetterCase::Upper)),
        "Xi" => Some((MathGreekLetter::Xi, MathLetterCase::Upper)),
        "Pi" => Some((MathGreekLetter::Pi, MathLetterCase::Upper)),
        "Sigma" => Some((MathGreekLetter::Sigma, MathLetterCase::Upper)),
        "Upsilon" => Some((MathGreekLetter::Upsilon, MathLetterCase::Upper)),
        "Phi" => Some((MathGreekLetter::Phi, MathLetterCase::Upper)),
        "Psi" => Some((MathGreekLetter::Psi, MathLetterCase::Upper)),
        "Omega" => Some((MathGreekLetter::Omega, MathLetterCase::Upper)),
        _ => None,
    };
    if let Some((letter, letter_case)) = greek {
        return Some(MathSymbol::Greek {
            letter,
            letter_case,
        });
    }
    match name {
        "infty" => Some(MathSymbol::Infinity),
        "emptyset" => Some(MathSymbol::EmptySet),
        "aleph" => Some(MathSymbol::Aleph),
        "hbar" => Some(MathSymbol::Hbar),
        "partial" => Some(MathSymbol::PartialDifferential),
        "nabla" => Some(MathSymbol::Nabla),
        "therefore" => Some(MathSymbol::Therefore),
        "because" => Some(MathSymbol::Because),
        "ldots" => Some(MathSymbol::HorizontalEllipsis),
        "vdots" => Some(MathSymbol::VerticalEllipsis),
        "ddots" => Some(MathSymbol::DiagonalEllipsis),
        "circ" => Some(MathSymbol::Degree),
        "prime" => Some(MathSymbol::Prime),
        _ => None,
    }
}
