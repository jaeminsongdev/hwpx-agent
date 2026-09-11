use std::fmt;

use domain_ir::{
    MATH_AST_NORMALIZATION_VERSION, MATH_AST_SCHEMA_VERSION, MathAccent, MathAlignedLine,
    MathAnnotationKind, MathAst, MathAstDraft, MathAstLimits, MathCase, MathCombinatorialKind,
    MathDelimiter, MathDerivativeKind, MathDerivativeVariable, MathExpression, MathFunction,
    MathGreekLetter, MathLargeOperator, MathLetterCase, MathMatrixKind, MathNode, MathOperator,
    MathSourceSpan, MathSymbol,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const EQEDIT_ADAPTER_SCHEMA_VERSION: &str = "hwpx-agent.eqedit-adapter/v1";
pub const EQEDIT_PROFILE_VERSION: &str = "hwpx-agent.eqedit-profile/hangul-2020-canonical-v1";
pub const EQEDIT_PARSER_VERSION: &str = "hwpx-agent.eqedit-parser/hangul-2020-v1";
pub const EQEDIT_COMPILER_VERSION: &str = "hwpx-agent.eqedit-compiler/hangul-2020-v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EqEditLimitConfig {
    pub source_bytes: usize,
    pub tokens: usize,
    pub token_bytes: usize,
    pub parse_depth: usize,
    pub compile_depth: usize,
    pub script_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for EqEditLimitConfig {
    fn default() -> Self {
        Self {
            source_bytes: 1024 * 1024,
            tokens: 32_768,
            token_bytes: 64 * 1024,
            parse_depth: 128,
            compile_depth: 128,
            script_bytes: 4 * 1024 * 1024,
            serialized_bytes: 8 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct EqEditLimits(EqEditLimitConfig);

impl EqEditLimits {
    pub const HARD_MAX_SOURCE_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_TOKENS: usize = 262_144;
    pub const HARD_MAX_TOKEN_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_PARSE_DEPTH: usize = 256;
    pub const HARD_MAX_COMPILE_DEPTH: usize = 256;
    pub const HARD_MAX_SCRIPT_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;

    /// Creates finite parser, compiler and result limits for the P07-04 `EqEdit` boundary.
    ///
    /// # Errors
    ///
    /// Returns [`EqEditError::InvalidLimit`] when a value is zero, exceeds its hard ceiling, or
    /// the script ceiling is smaller than the admitted source ceiling.
    pub fn new(config: EqEditLimitConfig) -> Result<Self, EqEditError> {
        if config.source_bytes == 0
            || config.source_bytes > Self::HARD_MAX_SOURCE_BYTES
            || config.tokens == 0
            || config.tokens > Self::HARD_MAX_TOKENS
            || config.token_bytes == 0
            || config.token_bytes > Self::HARD_MAX_TOKEN_BYTES
            || config.parse_depth == 0
            || config.parse_depth > Self::HARD_MAX_PARSE_DEPTH
            || config.compile_depth == 0
            || config.compile_depth > Self::HARD_MAX_COMPILE_DEPTH
            || config.script_bytes == 0
            || config.script_bytes > Self::HARD_MAX_SCRIPT_BYTES
            || config.script_bytes < config.source_bytes
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(EqEditError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> EqEditLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EqEditParseRequestDraft {
    pub schema_version: String,
    pub profile_version: String,
    pub source: String,
}

impl fmt::Debug for EqEditParseRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EqEditParseRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("source", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EqEditParseResult {
    schema_version: &'static str,
    profile_version: &'static str,
    parser_version: &'static str,
    math_ast_schema_version: &'static str,
    normalization_version: &'static str,
    source_sha256: String,
    source_length_bytes: u32,
    token_count: usize,
    ast: MathAst,
}

impl EqEditParseResult {
    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub const fn profile_version(&self) -> &'static str {
        self.profile_version
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
    pub const fn token_count(&self) -> usize {
        self.token_count
    }

    #[must_use]
    pub const fn ast(&self) -> &MathAst {
        &self.ast
    }

    /// Serializes the complete bounded parse result.
    ///
    /// # Errors
    ///
    /// Returns an output or serialization error when the configured result bound is exceeded.
    pub fn canonical_json(&self, limits: EqEditLimits) -> Result<Vec<u8>, EqEditError> {
        bounded_json(self, limits)
    }
}

impl fmt::Debug for EqEditParseResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EqEditParseResult")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("parser_version", &self.parser_version)
            .field("math_ast_schema_version", &self.math_ast_schema_version)
            .field("normalization_version", &self.normalization_version)
            .field("source_sha256", &"<redacted>")
            .field("source_length_bytes", &"<redacted>")
            .field("token_count", &self.token_count)
            .field("ast", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EqEditCompileResult {
    schema_version: &'static str,
    profile_version: &'static str,
    compiler_version: &'static str,
    parser_version: &'static str,
    math_ast_schema_version: &'static str,
    normalization_version: &'static str,
    semantic_sha256: String,
    script_sha256: String,
    script_length_bytes: u32,
    token_count: usize,
    script: String,
}

impl EqEditCompileResult {
    #[must_use]
    pub const fn profile_version(&self) -> &'static str {
        self.profile_version
    }

    #[must_use]
    pub fn semantic_sha256(&self) -> &str {
        &self.semantic_sha256
    }

    #[must_use]
    pub fn script_sha256(&self) -> &str {
        &self.script_sha256
    }

    #[must_use]
    pub fn script(&self) -> &str {
        &self.script
    }

    #[must_use]
    pub const fn script_length_bytes(&self) -> u32 {
        self.script_length_bytes
    }

    #[must_use]
    pub const fn token_count(&self) -> usize {
        self.token_count
    }

    /// Serializes the complete bounded compiler receipt, including emitted script.
    ///
    /// # Errors
    ///
    /// Returns an output or serialization error when the configured result bound is exceeded.
    pub fn canonical_json(&self, limits: EqEditLimits) -> Result<Vec<u8>, EqEditError> {
        bounded_json(self, limits)
    }
}

impl fmt::Debug for EqEditCompileResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EqEditCompileResult")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("compiler_version", &self.compiler_version)
            .field("parser_version", &self.parser_version)
            .field("math_ast_schema_version", &self.math_ast_schema_version)
            .field("normalization_version", &self.normalization_version)
            .field("semantic_sha256", &"<redacted>")
            .field("script_sha256", &"<redacted>")
            .field("script_length_bytes", &"<redacted>")
            .field("token_count", &self.token_count)
            .field("script", &"<redacted>")
            .finish()
    }
}

#[derive(Debug, Error, Clone, Copy, Eq, PartialEq)]
pub enum EqEditError {
    #[error("EqEdit limit configuration is invalid")]
    InvalidLimit,
    #[error("EqEdit source is empty or exceeds its finite bound")]
    InputLimit,
    #[error("EqEdit JSON is malformed, duplicated, unknown or oversized")]
    InvalidJson,
    #[error("EqEdit adapter schema version is unsupported")]
    UnsupportedVersion,
    #[error("EqEdit target profile is unsupported")]
    UnsupportedProfile,
    #[error("EqEdit token count or token size exceeds its finite bound")]
    TokenLimit,
    #[error("EqEdit parser depth exceeds its finite bound")]
    ParseDepthLimit,
    #[error("EqEdit source is syntactically invalid")]
    InvalidSyntax,
    #[error("EqEdit source uses syntax outside the exact target profile")]
    UnsupportedSyntax,
    #[error("MathAst contains an EqEdit-unrepresentable value")]
    UnrepresentableValue,
    #[error("MathAst expression is outside the EqEdit compiler profile")]
    UnsupportedExpression,
    #[error("MathAst node style is outside the EqEdit compiler profile")]
    UnsupportedStyle,
    #[error("MathAst admission failed")]
    MathAst,
    #[error("compiled EqEdit did not parse to the source semantic MathAst")]
    RoundTripMismatch,
    #[error("EqEdit output exceeds its finite bound")]
    OutputLimit,
    #[error("EqEdit result serialization failed")]
    Serialization,
}

impl EqEditError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "eqedit_invalid_limit",
            Self::InputLimit => "eqedit_input_limit",
            Self::InvalidJson => "eqedit_invalid_json",
            Self::UnsupportedVersion => "eqedit_unsupported_version",
            Self::UnsupportedProfile => "eqedit_unsupported_profile",
            Self::TokenLimit => "eqedit_token_limit",
            Self::ParseDepthLimit => "eqedit_parse_depth_limit",
            Self::InvalidSyntax => "eqedit_invalid_syntax",
            Self::UnsupportedSyntax => "eqedit_unsupported_syntax",
            Self::UnrepresentableValue => "eqedit_unrepresentable_value",
            Self::UnsupportedExpression => "eqedit_unsupported_expression",
            Self::UnsupportedStyle => "eqedit_unsupported_style",
            Self::MathAst => "eqedit_math_ast",
            Self::RoundTripMismatch => "eqedit_roundtrip_mismatch",
            Self::OutputLimit => "eqedit_output_limit",
            Self::Serialization => "eqedit_serialization",
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct EqEditEngine {
    limits: EqEditLimits,
    math_limits: MathAstLimits,
}

impl EqEditEngine {
    /// Creates the exact finite current-PC Hangul 2020 `EqEdit` engine.
    ///
    /// # Errors
    ///
    /// Returns an invalid-limit error when the output bound cannot contain the AST bound.
    pub fn new(limits: EqEditLimits, math_limits: MathAstLimits) -> Result<Self, EqEditError> {
        Ok(Self {
            limits,
            math_limits,
        })
    }

    /// Parses one strict JSON request and then one exact-profile `EqEdit` script.
    ///
    /// # Errors
    ///
    /// Rejects malformed/oversized JSON and every parse error from [`Self::parse`].
    pub fn parse_json(&self, bytes: &[u8]) -> Result<EqEditParseResult, EqEditError> {
        if bytes.is_empty() || bytes.len() > self.limits.0.serialized_bytes {
            return Err(EqEditError::InvalidJson);
        }
        let request = serde_json::from_slice(bytes).map_err(|_| EqEditError::InvalidJson)?;
        self.parse(request)
    }

    /// Parses one bounded `EqEdit` script into a normalized `MathAst`.
    ///
    /// # Errors
    ///
    /// Fails closed on profile drift, ambiguous/unsupported syntax, resource exhaustion, or AST
    /// admission failure. It never returns a partial tree.
    pub fn parse(
        &self,
        request: EqEditParseRequestDraft,
    ) -> Result<EqEditParseResult, EqEditError> {
        let EqEditParseRequestDraft {
            schema_version,
            profile_version,
            source,
        } = request;
        if schema_version != EQEDIT_ADAPTER_SCHEMA_VERSION {
            return Err(EqEditError::UnsupportedVersion);
        }
        if profile_version != EQEDIT_PROFILE_VERSION {
            return Err(EqEditError::UnsupportedProfile);
        }
        self.parse_source(&source)
    }

    /// Compiles one admitted `MathAst` to canonical current-profile `EqEdit` and verifies the
    /// semantic AST-to-script-to-AST property before returning it.
    ///
    /// # Errors
    ///
    /// Rejects styles, values, expressions or resource use outside the exact finite profile and
    /// rejects any internal semantic round-trip mismatch.
    pub fn compile(&self, ast: &MathAst) -> Result<EqEditCompileResult, EqEditError> {
        let mut compiler = Compiler::new(self.limits);
        compiler.compile_node(ast.root(), 1)?;
        let script = compiler.finish()?;
        let tokens = tokenize(&script, self.limits)?;
        let parsed = self.parse_tokens(&script, &tokens)?;
        if !ast.semantically_eq(&parsed) {
            return Err(EqEditError::RoundTripMismatch);
        }
        let semantic_sha256 = hex::encode(
            ast.semantic_sha256(self.math_limits)
                .map_err(|_| EqEditError::MathAst)?,
        );
        let script_sha256 = hex::encode(Sha256::digest(script.as_bytes()));
        let script_length_bytes =
            u32::try_from(script.len()).map_err(|_| EqEditError::OutputLimit)?;
        let result = EqEditCompileResult {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION,
            profile_version: EQEDIT_PROFILE_VERSION,
            compiler_version: EQEDIT_COMPILER_VERSION,
            parser_version: EQEDIT_PARSER_VERSION,
            math_ast_schema_version: MATH_AST_SCHEMA_VERSION,
            normalization_version: MATH_AST_NORMALIZATION_VERSION,
            semantic_sha256,
            script_sha256,
            script_length_bytes,
            token_count: tokens.len(),
            script,
        };
        let _ = result.canonical_json(self.limits)?;
        Ok(result)
    }

    fn parse_source(&self, source: &str) -> Result<EqEditParseResult, EqEditError> {
        if source.is_empty() || source.len() > self.limits.0.source_bytes {
            return Err(EqEditError::InputLimit);
        }
        let source_length_bytes =
            u32::try_from(source.len()).map_err(|_| EqEditError::InputLimit)?;
        let tokens = tokenize(source, self.limits)?;
        let ast = self.parse_tokens(source, &tokens)?;
        let result = EqEditParseResult {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION,
            profile_version: EQEDIT_PROFILE_VERSION,
            parser_version: EQEDIT_PARSER_VERSION,
            math_ast_schema_version: MATH_AST_SCHEMA_VERSION,
            normalization_version: MATH_AST_NORMALIZATION_VERSION,
            source_sha256: hex::encode(Sha256::digest(source.as_bytes())),
            source_length_bytes,
            token_count: tokens.len(),
            ast,
        };
        let _ = result.canonical_json(self.limits)?;
        Ok(result)
    }

    fn parse_tokens(&self, source: &str, tokens: &[Token]) -> Result<MathAst, EqEditError> {
        let root = Parser::new(tokens, self.limits.0.parse_depth).parse()?;
        MathAst::from_draft(
            MathAstDraft {
                schema_version: MATH_AST_SCHEMA_VERSION.to_owned(),
                normalization_version: MATH_AST_NORMALIZATION_VERSION.to_owned(),
                source_length_bytes: u32::try_from(source.len())
                    .map_err(|_| EqEditError::InputLimit)?,
                root,
            },
            self.math_limits,
        )
        .map_err(|_| EqEditError::MathAst)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
enum TokenKind {
    Number(String),
    Word(String),
    Text(String),
    Plus,
    Minus,
    Bang,
    Equal,
    Less,
    Greater,
    NotEqual,
    LessEqual,
    GreaterEqual,
    Equivalent,
    LeftBrace,
    RightBrace,
    LeftParenthesis,
    RightParenthesis,
    LeftBracket,
    RightBracket,
    VerticalBar,
    DoubleVerticalBar,
    Underscore,
    Caret,
    Ampersand,
    Hash,
    Comma,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct Token {
    kind: TokenKind,
    span: MathSourceSpan,
}

#[allow(clippy::too_many_lines)]
fn tokenize(source: &str, limits: EqEditLimits) -> Result<Vec<Token>, EqEditError> {
    let mut tokens = Vec::new();
    let mut indices = source.char_indices().peekable();
    while let Some((start, character)) = indices.next() {
        if character.is_whitespace() {
            continue;
        }
        if character.is_control() || matches!(character, '\\' | '~' | '`' | '\'') {
            return Err(EqEditError::UnsupportedSyntax);
        }
        let start_u32 = u32::try_from(start).map_err(|_| EqEditError::InputLimit)?;
        let (kind, end) = if character == '"' {
            let value_start = start + 1;
            let mut close = None;
            for (offset, next) in indices.by_ref() {
                if next == '"' {
                    close = Some(offset);
                    break;
                }
                if next.is_control() {
                    return Err(EqEditError::InvalidSyntax);
                }
            }
            let close = close.ok_or(EqEditError::InvalidSyntax)?;
            let value = &source[value_start..close];
            if value.is_empty() || value.len() > limits.0.token_bytes {
                return Err(EqEditError::TokenLimit);
            }
            (TokenKind::Text(value.to_owned()), close + 1)
        } else if character.is_ascii_digit()
            || (character == '.'
                && indices
                    .peek()
                    .is_some_and(|(_, next)| next.is_ascii_digit()))
        {
            let mut end = start + character.len_utf8();
            while let Some((offset, next)) = indices.peek().copied() {
                if !next.is_ascii_digit() && next != '.' {
                    break;
                }
                let _ = indices.next();
                end = offset + next.len_utf8();
            }
            let value = &source[start..end];
            if value.len() > limits.0.token_bytes {
                return Err(EqEditError::TokenLimit);
            }
            (TokenKind::Number(value.to_owned()), end)
        } else if is_word_character(character) {
            let mut end = start + character.len_utf8();
            while let Some((offset, next)) = indices.peek().copied() {
                if !is_word_character(next) {
                    break;
                }
                let _ = indices.next();
                end = offset + next.len_utf8();
            }
            let value = &source[start..end];
            if value.len() > limits.0.token_bytes {
                return Err(EqEditError::TokenLimit);
            }
            (TokenKind::Word(value.to_owned()), end)
        } else {
            let mut end = start + character.len_utf8();
            let kind = match character {
                '+' => TokenKind::Plus,
                '-' => TokenKind::Minus,
                '!' if indices.peek().is_some_and(|(_, next)| *next == '=') => {
                    let (offset, next) = indices.next().ok_or(EqEditError::InvalidSyntax)?;
                    end = offset + next.len_utf8();
                    TokenKind::NotEqual
                }
                '!' => TokenKind::Bang,
                '=' if indices.peek().is_some_and(|(_, next)| *next == '=') => {
                    let (offset, next) = indices.next().ok_or(EqEditError::InvalidSyntax)?;
                    end = offset + next.len_utf8();
                    TokenKind::Equivalent
                }
                '=' => TokenKind::Equal,
                '<' if indices.peek().is_some_and(|(_, next)| *next == '=') => {
                    let (offset, next) = indices.next().ok_or(EqEditError::InvalidSyntax)?;
                    end = offset + next.len_utf8();
                    TokenKind::LessEqual
                }
                '<' => TokenKind::Less,
                '>' if indices.peek().is_some_and(|(_, next)| *next == '=') => {
                    let (offset, next) = indices.next().ok_or(EqEditError::InvalidSyntax)?;
                    end = offset + next.len_utf8();
                    TokenKind::GreaterEqual
                }
                '>' => TokenKind::Greater,
                '{' => TokenKind::LeftBrace,
                '}' => TokenKind::RightBrace,
                '(' => TokenKind::LeftParenthesis,
                ')' => TokenKind::RightParenthesis,
                '[' => TokenKind::LeftBracket,
                ']' => TokenKind::RightBracket,
                '|' if indices.peek().is_some_and(|(_, next)| *next == '|') => {
                    let (offset, next) = indices.next().ok_or(EqEditError::InvalidSyntax)?;
                    end = offset + next.len_utf8();
                    TokenKind::DoubleVerticalBar
                }
                '|' => TokenKind::VerticalBar,
                '_' => TokenKind::Underscore,
                '^' => TokenKind::Caret,
                '&' => TokenKind::Ampersand,
                '#' => TokenKind::Hash,
                ',' => TokenKind::Comma,
                _ => return Err(EqEditError::UnsupportedSyntax),
            };
            (kind, end)
        };
        tokens.push(Token {
            kind,
            span: MathSourceSpan {
                start_byte: start_u32,
                end_byte: u32::try_from(end).map_err(|_| EqEditError::InputLimit)?,
            },
        });
        if tokens.len() > limits.0.tokens {
            return Err(EqEditError::TokenLimit);
        }
    }
    if tokens.is_empty() {
        return Err(EqEditError::InputLimit);
    }
    Ok(tokens)
}

fn is_word_character(character: char) -> bool {
    character.is_alphanumeric() || (!character.is_ascii() && !character.is_whitespace())
}

struct Parser<'a> {
    tokens: &'a [Token],
    index: usize,
    depth: usize,
    max_depth: usize,
}

impl<'a> Parser<'a> {
    const fn new(tokens: &'a [Token], max_depth: usize) -> Self {
        Self {
            tokens,
            index: 0,
            depth: 0,
            max_depth,
        }
    }

    fn parse(mut self) -> Result<MathNode, EqEditError> {
        let root = self.parse_expression(0)?;
        if self.index != self.tokens.len() {
            return Err(EqEditError::InvalidSyntax);
        }
        Ok(root)
    }

    fn parse_expression(&mut self, minimum: u8) -> Result<MathNode, EqEditError> {
        if self.depth >= self.max_depth {
            return Err(EqEditError::ParseDepthLimit);
        }
        self.depth += 1;
        let result = self.parse_expression_inner(minimum);
        self.depth -= 1;
        result
    }

    fn parse_expression_inner(&mut self, minimum: u8) -> Result<MathNode, EqEditError> {
        let mut left = self.parse_prefix()?;
        loop {
            if let Some((operator, precedence, fraction)) = self.infix_operator() {
                if precedence < minimum {
                    break;
                }
                if is_relation(operator) && relation_root(&left) {
                    return Err(EqEditError::UnsupportedSyntax);
                }
                self.index += 1;
                let right = self.parse_expression(precedence + 1)?;
                left = if fraction {
                    make_fraction_or_derivative(left, right)?
                } else {
                    make_apply(operator, vec![left, right])
                };
                continue;
            }
            if self.starts_primary() {
                const ROW_PRECEDENCE: u8 = 55;
                if ROW_PRECEDENCE < minimum {
                    break;
                }
                let right = self.parse_expression(ROW_PRECEDENCE + 1)?;
                left = make_row(vec![left, right]);
                continue;
            }
            break;
        }
        Ok(left)
    }

    fn parse_prefix(&mut self) -> Result<MathNode, EqEditError> {
        if matches!(self.peek_kind(), Some(TokenKind::Plus | TokenKind::Minus)) {
            let token = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
            let operator = if matches!(token.kind, TokenKind::Plus) {
                MathOperator::Positive
            } else {
                MathOperator::Negative
            };
            let argument = self.parse_expression(60)?;
            return Ok(make_apply_with_span(
                operator,
                vec![argument.clone()],
                merged_span(token.span, argument.span),
            ));
        }
        if matches!(self.peek_kind(), Some(TokenKind::Caret)) {
            let caret = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
            let degree = self.parse_script_argument()?;
            let command = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
            if !matches!(&command.kind, TokenKind::Word(name) if eq_word(name, "sqrt")) {
                return Err(EqEditError::UnsupportedSyntax);
            }
            let radicand = self.parse_required_group()?;
            return Ok(make_node(
                merged_span(caret.span, radicand.span),
                MathExpression::Root {
                    degree: Some(Box::new(degree)),
                    radicand: Box::new(radicand),
                },
            ));
        }
        self.parse_postfix()
    }

    fn parse_postfix(&mut self) -> Result<MathNode, EqEditError> {
        let mut node = self.parse_primary()?;
        let mut subscript = None;
        let mut superscript = None;
        while matches!(
            self.peek_kind(),
            Some(TokenKind::Underscore | TokenKind::Caret | TokenKind::Bang)
        ) {
            let marker = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
            if matches!(marker.kind, TokenKind::Bang) {
                node = make_apply_with_span(
                    MathOperator::Factorial,
                    vec![node.clone()],
                    merged_span(node.span, marker.span),
                );
                continue;
            }
            let argument = Box::new(self.parse_script_argument()?);
            if matches!(marker.kind, TokenKind::Underscore) {
                if subscript.replace(argument).is_some() {
                    return Err(EqEditError::InvalidSyntax);
                }
            } else if superscript.replace(argument).is_some() {
                return Err(EqEditError::InvalidSyntax);
            }
        }
        if subscript.is_some() || superscript.is_some() {
            let end = subscript
                .as_ref()
                .into_iter()
                .chain(superscript.as_ref())
                .map(|item| item.span.end_byte)
                .max()
                .ok_or(EqEditError::InvalidSyntax)?;
            let start = node.span.start_byte;
            node = make_node(
                MathSourceSpan {
                    start_byte: start,
                    end_byte: end,
                },
                MathExpression::Script {
                    base: Box::new(node),
                    subscript,
                    superscript,
                },
            );
        }
        Ok(node)
    }

    #[allow(clippy::too_many_lines)]
    fn parse_primary(&mut self) -> Result<MathNode, EqEditError> {
        let token = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
        match token.kind {
            TokenKind::Number(value) => Ok(make_node(token.span, MathExpression::Number { value })),
            TokenKind::Text(value) => Ok(make_node(token.span, MathExpression::Text { value })),
            TokenKind::LeftBrace => self.parse_group_after_open(token.span),
            TokenKind::LeftParenthesis => self.parse_raw_delimited(
                token.span,
                &TokenKind::RightParenthesis,
                MathDelimiter::LeftParenthesis,
                MathDelimiter::RightParenthesis,
            ),
            TokenKind::LeftBracket => self.parse_raw_delimited(
                token.span,
                &TokenKind::RightBracket,
                MathDelimiter::LeftBracket,
                MathDelimiter::RightBracket,
            ),
            // A bare vertical bar is lexically indistinguishable from its closing mate. The
            // canonical profile therefore requires LEFT/RIGHT for bars instead of guessing.
            TokenKind::VerticalBar | TokenKind::DoubleVerticalBar => {
                Err(EqEditError::UnsupportedSyntax)
            }
            TokenKind::Word(name) => self.parse_word(name, token.span),
            _ => Err(EqEditError::InvalidSyntax),
        }
    }

    fn parse_word(&mut self, name: String, span: MathSourceSpan) -> Result<MathNode, EqEditError> {
        if let Some(symbol) = parse_symbol(&name) {
            return Ok(make_node(span, MathExpression::Symbol { symbol }));
        }
        if let Some(accent) = parse_accent(&name) {
            let base = self.parse_required_group()?;
            return Ok(make_node(
                merged_span(span, base.span),
                MathExpression::Accent {
                    accent,
                    base: Box::new(base),
                },
            ));
        }
        if eq_word(&name, "overline") || eq_word(&name, "underline") {
            let base = self.parse_required_group()?;
            return Ok(make_node(
                merged_span(span, base.span),
                MathExpression::Annotated {
                    annotation_kind: if eq_word(&name, "overline") {
                        MathAnnotationKind::OverLine
                    } else {
                        MathAnnotationKind::UnderLine
                    },
                    base: Box::new(base),
                    annotation: None,
                },
            ));
        }
        if eq_word(&name, "sqrt") {
            let radicand = self.parse_required_group()?;
            return Ok(make_node(
                merged_span(span, radicand.span),
                MathExpression::Root {
                    degree: None,
                    radicand: Box::new(radicand),
                },
            ));
        }
        if let Some(operator) = parse_large_operator(&name) {
            return self.parse_large(operator, span);
        }
        if let Some(function) = parse_function(&name) {
            let argument = self.parse_required_group()?;
            return Ok(make_node(
                merged_span(span, argument.span),
                MathExpression::Function {
                    function,
                    arguments: vec![argument],
                },
            ));
        }
        if let Some(kind) = parse_matrix_kind(&name) {
            return self.parse_matrix(kind, span);
        }
        if eq_word(&name, "cases") {
            return self.parse_cases(span);
        }
        if eq_word(&name, "pile") {
            return self.parse_aligned(span);
        }
        if eq_word(&name, "binom") || eq_word(&name, "choose") {
            let upper = self.parse_required_group()?;
            let lower = self.parse_required_group()?;
            return Ok(make_node(
                merged_span(span, lower.span),
                MathExpression::Combinatorial {
                    combinatorial_kind: MathCombinatorialKind::Binomial,
                    upper: Box::new(upper),
                    lower: Box::new(lower),
                },
            ));
        }
        if eq_word(&name, "left") {
            return self.parse_left_right(span);
        }
        if eq_word(&name, "lnot") || eq_word(&name, "not") {
            let argument = self.parse_required_group()?;
            return Ok(make_apply_with_span(
                MathOperator::LogicalNot,
                vec![argument.clone()],
                merged_span(span, argument.span),
            ));
        }
        if is_reserved_word(&name) {
            return Err(EqEditError::UnsupportedSyntax);
        }
        if name.chars().count() > 9 {
            return Err(EqEditError::UnsupportedSyntax);
        }
        Ok(make_node(span, MathExpression::Identifier { name }))
    }

    fn parse_group_after_open(&mut self, open: MathSourceSpan) -> Result<MathNode, EqEditError> {
        if matches!(self.peek_kind(), Some(TokenKind::RightBrace)) {
            return Err(EqEditError::InvalidSyntax);
        }
        let mut node = self.parse_expression(0)?;
        let close = self.expect_discriminant(&TokenKind::RightBrace)?;
        node.span = merged_span(open, close.span);
        Ok(node)
    }

    fn parse_required_group(&mut self) -> Result<MathNode, EqEditError> {
        let open = self.expect_discriminant(&TokenKind::LeftBrace)?;
        self.parse_group_after_open(open.span)
    }

    fn parse_script_argument(&mut self) -> Result<MathNode, EqEditError> {
        if matches!(self.peek_kind(), Some(TokenKind::LeftBrace)) {
            self.parse_required_group()
        } else {
            self.parse_primary()
        }
    }

    fn parse_raw_delimited(
        &mut self,
        open: MathSourceSpan,
        close_kind: &TokenKind,
        left: MathDelimiter,
        right: MathDelimiter,
    ) -> Result<MathNode, EqEditError> {
        let body = self.parse_expression(0)?;
        let close = self.expect_discriminant(close_kind)?;
        Ok(make_node(
            merged_span(open, close.span),
            MathExpression::Delimited {
                left,
                body: Box::new(body),
                right,
            },
        ))
    }

    fn parse_large(
        &mut self,
        operator: MathLargeOperator,
        command_span: MathSourceSpan,
    ) -> Result<MathNode, EqEditError> {
        let mut lower = None;
        let mut upper = None;
        while matches!(
            self.peek_kind(),
            Some(TokenKind::Underscore | TokenKind::Caret)
        ) {
            let marker = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
            let argument = Box::new(self.parse_script_argument()?);
            if matches!(marker.kind, TokenKind::Underscore) {
                if lower.replace(argument).is_some() {
                    return Err(EqEditError::InvalidSyntax);
                }
            } else if upper.replace(argument).is_some() {
                return Err(EqEditError::InvalidSyntax);
            }
        }
        if matches!(operator, MathLargeOperator::Limit) && (lower.is_none() || upper.is_some()) {
            return Err(EqEditError::InvalidSyntax);
        }
        let body = self.parse_required_group()?;
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

    fn parse_matrix(
        &mut self,
        matrix_kind: MathMatrixKind,
        command_span: MathSourceSpan,
    ) -> Result<MathNode, EqEditError> {
        let (rows, close) = self.parse_grid()?;
        Ok(make_node(
            merged_span(command_span, close),
            MathExpression::Matrix { matrix_kind, rows },
        ))
    }

    fn parse_cases(&mut self, command_span: MathSourceSpan) -> Result<MathNode, EqEditError> {
        let (rows, close) = self.parse_grid()?;
        let mut cases = Vec::with_capacity(rows.len());
        for mut row in rows {
            if row.is_empty() || row.len() > 2 {
                return Err(EqEditError::InvalidSyntax);
            }
            let condition = if row.len() == 2 { row.pop() } else { None };
            let value = row.pop().ok_or(EqEditError::InvalidSyntax)?;
            cases.push(MathCase { value, condition });
        }
        Ok(make_node(
            merged_span(command_span, close),
            MathExpression::Cases { cases },
        ))
    }

    fn parse_aligned(&mut self, command_span: MathSourceSpan) -> Result<MathNode, EqEditError> {
        let (rows, close) = self.parse_grid()?;
        let lines = rows
            .into_iter()
            .map(|cells| MathAlignedLine { cells })
            .collect();
        Ok(make_node(
            merged_span(command_span, close),
            MathExpression::Aligned { lines },
        ))
    }

    fn parse_grid(&mut self) -> Result<(Vec<Vec<MathNode>>, MathSourceSpan), EqEditError> {
        let _open = self.expect_discriminant(&TokenKind::LeftBrace)?;
        let mut rows = Vec::new();
        let mut row = Vec::new();
        loop {
            row.push(self.parse_expression(0)?);
            match self.peek_kind() {
                Some(TokenKind::Ampersand) => self.index += 1,
                Some(TokenKind::Hash) => {
                    self.index += 1;
                    rows.push(row);
                    row = Vec::new();
                }
                Some(TokenKind::RightBrace) => {
                    let close = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
                    rows.push(row);
                    return Ok((rows, close.span));
                }
                _ => return Err(EqEditError::InvalidSyntax),
            }
        }
    }

    fn parse_left_right(&mut self, command_span: MathSourceSpan) -> Result<MathNode, EqEditError> {
        let (left, left_is_set) = self.parse_left_delimiter()?;
        if left_is_set {
            let element = self.parse_expression(0)?;
            let separator = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
            if !matches!(&separator.kind, TokenKind::Word(name) if eq_word(name, "vert")) {
                return Err(EqEditError::InvalidSyntax);
            }
            let condition = self.parse_expression(0)?;
            let close = self.expect_right_delimiter(MathDelimiter::RightBrace)?;
            return Ok(make_node(
                merged_span(command_span, close),
                MathExpression::SetBuilder {
                    element: Box::new(element),
                    condition: Box::new(condition),
                },
            ));
        }
        let body = self.parse_expression(0)?;
        let expected_right = matching_right(left).ok_or(EqEditError::UnsupportedSyntax)?;
        let close = self.expect_right_delimiter(expected_right)?;
        Ok(make_node(
            merged_span(command_span, close),
            MathExpression::Delimited {
                left,
                body: Box::new(body),
                right: expected_right,
            },
        ))
    }

    fn parse_left_delimiter(&mut self) -> Result<(MathDelimiter, bool), EqEditError> {
        let token = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
        match token.kind {
            TokenKind::LeftParenthesis => Ok((MathDelimiter::LeftParenthesis, false)),
            TokenKind::LeftBracket => Ok((MathDelimiter::LeftBracket, false)),
            TokenKind::VerticalBar => Ok((MathDelimiter::VerticalBar, false)),
            TokenKind::DoubleVerticalBar => Ok((MathDelimiter::DoubleVerticalBar, false)),
            TokenKind::Less => Ok((MathDelimiter::LeftAngle, false)),
            TokenKind::LeftBrace => Ok((MathDelimiter::LeftBrace, true)),
            _ => Err(EqEditError::UnsupportedSyntax),
        }
    }

    fn expect_right_delimiter(
        &mut self,
        expected: MathDelimiter,
    ) -> Result<MathSourceSpan, EqEditError> {
        let right = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
        if !matches!(&right.kind, TokenKind::Word(name) if eq_word(name, "right")) {
            return Err(EqEditError::InvalidSyntax);
        }
        let delimiter = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
        let actual = match delimiter.kind {
            TokenKind::RightParenthesis => MathDelimiter::RightParenthesis,
            TokenKind::RightBracket => MathDelimiter::RightBracket,
            TokenKind::VerticalBar => MathDelimiter::VerticalBar,
            TokenKind::DoubleVerticalBar => MathDelimiter::DoubleVerticalBar,
            TokenKind::Greater => MathDelimiter::RightAngle,
            TokenKind::RightBrace => MathDelimiter::RightBrace,
            _ => return Err(EqEditError::UnsupportedSyntax),
        };
        if actual != expected {
            return Err(EqEditError::InvalidSyntax);
        }
        Ok(delimiter.span)
    }

    fn infix_operator(&self) -> Option<(MathOperator, u8, bool)> {
        match self.peek_kind()? {
            TokenKind::Plus => Some((MathOperator::Add, 30, false)),
            TokenKind::Minus => Some((MathOperator::Subtract, 30, false)),
            TokenKind::Equal => Some((MathOperator::Equal, 10, false)),
            TokenKind::Less => Some((MathOperator::LessThan, 10, false)),
            TokenKind::Greater => Some((MathOperator::GreaterThan, 10, false)),
            TokenKind::NotEqual => Some((MathOperator::NotEqual, 10, false)),
            TokenKind::LessEqual => Some((MathOperator::LessThanOrEqual, 10, false)),
            TokenKind::GreaterEqual => Some((MathOperator::GreaterThanOrEqual, 10, false)),
            TokenKind::Equivalent => Some((MathOperator::Equivalent, 8, false)),
            TokenKind::Word(name) if eq_word(name, "over") => {
                Some((MathOperator::Divide, 50, true))
            }
            TokenKind::Word(name) => {
                word_operator(name).map(|(operator, precedence)| (operator, precedence, false))
            }
            _ => None,
        }
    }

    fn starts_primary(&self) -> bool {
        match self.peek_kind() {
            Some(
                TokenKind::Number(_)
                | TokenKind::Text(_)
                | TokenKind::LeftBrace
                | TokenKind::LeftParenthesis
                | TokenKind::LeftBracket
                | TokenKind::VerticalBar
                | TokenKind::DoubleVerticalBar,
            ) => true,
            Some(TokenKind::Word(name)) => {
                !eq_word(name, "right")
                    && !eq_word(name, "vert")
                    && !eq_word(name, "over")
                    && word_operator(name).is_none()
            }
            _ => false,
        }
    }

    fn peek_kind(&self) -> Option<&TokenKind> {
        self.tokens.get(self.index).map(|token| &token.kind)
    }

    fn next(&mut self) -> Option<&Token> {
        let token = self.tokens.get(self.index);
        self.index += usize::from(token.is_some());
        token
    }

    fn expect_discriminant(&mut self, expected: &TokenKind) -> Result<Token, EqEditError> {
        let token = self.next().cloned().ok_or(EqEditError::InvalidSyntax)?;
        if std::mem::discriminant(&token.kind) != std::mem::discriminant(expected) {
            return Err(EqEditError::InvalidSyntax);
        }
        Ok(token)
    }
}

struct Compiler {
    limits: EqEditLimits,
    output: String,
}

impl Compiler {
    fn new(limits: EqEditLimits) -> Self {
        Self {
            limits,
            output: String::new(),
        }
    }

    fn finish(self) -> Result<String, EqEditError> {
        if self.output.is_empty() || self.output.len() > self.limits.0.script_bytes {
            return Err(EqEditError::OutputLimit);
        }
        Ok(self.output)
    }

    #[allow(clippy::too_many_lines)]
    fn compile_node(&mut self, node: &MathNode, depth: usize) -> Result<(), EqEditError> {
        if depth > self.limits.0.compile_depth {
            return Err(EqEditError::OutputLimit);
        }
        if node.style.is_some() {
            return Err(EqEditError::UnsupportedStyle);
        }
        let child_depth = depth.checked_add(1).ok_or(EqEditError::OutputLimit)?;
        match &node.expression {
            MathExpression::Number { value } => self.push(value),
            MathExpression::Identifier { name } => {
                if !is_compilable_identifier(name) {
                    return Err(EqEditError::UnrepresentableValue);
                }
                self.push(name)
            }
            MathExpression::Text { value } => {
                if !is_compilable_text(value) {
                    return Err(EqEditError::UnrepresentableValue);
                }
                self.push("\"")?;
                self.push(value)?;
                self.push("\"")
            }
            MathExpression::Symbol { symbol } => self.push(symbol_token(*symbol)),
            MathExpression::Row { items } => self.compile_sequence(items, child_depth),
            MathExpression::Apply {
                operator,
                arguments,
            } => self.compile_apply(*operator, arguments, child_depth),
            MathExpression::Function {
                function,
                arguments,
            } => {
                if arguments.len() != 1 {
                    return Err(EqEditError::UnsupportedExpression);
                }
                let token = function_token(function).ok_or(EqEditError::UnsupportedExpression)?;
                self.push(token)?;
                self.push(" ")?;
                self.compile_group(&arguments[0], child_depth)
            }
            MathExpression::Fraction {
                numerator,
                denominator,
            } => {
                self.compile_group(numerator, child_depth)?;
                self.push(" OVER ")?;
                self.compile_group(denominator, child_depth)
            }
            MathExpression::Script {
                base,
                subscript,
                superscript,
            } => {
                self.compile_group(base, child_depth)?;
                if let Some(subscript) = subscript {
                    self.push(" _ ")?;
                    self.compile_group(subscript, child_depth)?;
                }
                if let Some(superscript) = superscript {
                    self.push(" ^ ")?;
                    self.compile_group(superscript, child_depth)?;
                }
                Ok(())
            }
            MathExpression::Root { degree, radicand } => {
                if let Some(degree) = degree {
                    self.push("^")?;
                    self.compile_group(degree, child_depth)?;
                    self.push(" SQRT ")?;
                } else {
                    self.push("SQRT ")?;
                }
                self.compile_group(radicand, child_depth)
            }
            MathExpression::Accent { accent, base } => {
                self.push(accent_token(*accent))?;
                self.push(" ")?;
                self.compile_group(base, child_depth)
            }
            MathExpression::Annotated {
                annotation_kind,
                base,
                annotation,
            } => {
                if annotation.is_some() {
                    return Err(EqEditError::UnsupportedExpression);
                }
                let command = match annotation_kind {
                    MathAnnotationKind::OverLine => "OVERLINE",
                    MathAnnotationKind::UnderLine => "UNDERLINE",
                    _ => return Err(EqEditError::UnsupportedExpression),
                };
                self.push(command)?;
                self.push(" ")?;
                self.compile_group(base, child_depth)
            }
            MathExpression::LargeOperator {
                operator,
                body,
                lower,
                upper,
            } => {
                self.push(large_operator_token(*operator)?)?;
                if let Some(lower) = lower {
                    self.push(" _ ")?;
                    self.compile_group(lower, child_depth)?;
                }
                if let Some(upper) = upper {
                    self.push(" ^ ")?;
                    self.compile_group(upper, child_depth)?;
                }
                self.push(" ")?;
                self.compile_group(body, child_depth)
            }
            MathExpression::Derivative {
                derivative_kind,
                expression,
                variables,
            } => self.compile_derivative(*derivative_kind, expression, variables, child_depth),
            MathExpression::Delimited { left, body, right } => {
                let (left_token, right_token) = delimiter_tokens(*left, *right)?;
                self.push("LEFT ")?;
                self.push(left_token)?;
                self.push(" ")?;
                self.compile_group(body, child_depth)?;
                self.push(" RIGHT ")?;
                self.push(right_token)
            }
            MathExpression::Matrix { matrix_kind, rows } => {
                self.push(matrix_token(*matrix_kind)?)?;
                self.push(" ")?;
                self.compile_grid(rows, child_depth)
            }
            MathExpression::Cases { cases } => {
                self.push("CASES {")?;
                for (index, case) in cases.iter().enumerate() {
                    if index > 0 {
                        self.push(" # ")?;
                    }
                    self.compile_group(&case.value, child_depth)?;
                    if let Some(condition) = &case.condition {
                        self.push(" & ")?;
                        self.compile_group(condition, child_depth)?;
                    }
                }
                self.push("}")
            }
            MathExpression::Aligned { lines } => {
                self.push("PILE {")?;
                for (line_index, line) in lines.iter().enumerate() {
                    if line_index > 0 {
                        self.push(" # ")?;
                    }
                    for (cell_index, cell) in line.cells.iter().enumerate() {
                        if cell_index > 0 {
                            self.push(" & ")?;
                        }
                        self.compile_group(cell, child_depth)?;
                    }
                }
                self.push("}")
            }
            MathExpression::Combinatorial {
                combinatorial_kind,
                upper,
                lower,
            } => {
                if *combinatorial_kind != MathCombinatorialKind::Binomial {
                    return Err(EqEditError::UnsupportedExpression);
                }
                self.push("BINOM ")?;
                self.compile_group(upper, child_depth)?;
                self.push(" ")?;
                self.compile_group(lower, child_depth)
            }
            MathExpression::SetBuilder { element, condition } => {
                self.push("LEFT { ")?;
                self.compile_group(element, child_depth)?;
                self.push(" VERT ")?;
                self.compile_group(condition, child_depth)?;
                self.push(" RIGHT }")
            }
        }
    }

    fn compile_sequence(&mut self, items: &[MathNode], depth: usize) -> Result<(), EqEditError> {
        for (index, item) in items.iter().enumerate() {
            if index > 0 {
                self.push(" ")?;
            }
            self.compile_group(item, depth)?;
        }
        Ok(())
    }

    fn compile_apply(
        &mut self,
        operator: MathOperator,
        arguments: &[MathNode],
        depth: usize,
    ) -> Result<(), EqEditError> {
        match operator {
            MathOperator::Positive | MathOperator::Negative | MathOperator::LogicalNot => {
                let argument = arguments
                    .first()
                    .ok_or(EqEditError::UnsupportedExpression)?;
                let token = match operator {
                    MathOperator::Positive => "+",
                    MathOperator::Negative => "-",
                    MathOperator::LogicalNot => "LNOT",
                    _ => return Err(EqEditError::UnsupportedExpression),
                };
                self.push(token)?;
                self.push(" ")?;
                self.compile_group(argument, depth)
            }
            MathOperator::Factorial => {
                let argument = arguments
                    .first()
                    .ok_or(EqEditError::UnsupportedExpression)?;
                self.compile_group(argument, depth)?;
                self.push("!")
            }
            _ => {
                let token = operator_token(operator).ok_or(EqEditError::UnsupportedExpression)?;
                for (index, argument) in arguments.iter().enumerate() {
                    if index > 0 {
                        self.push(" ")?;
                        self.push(token)?;
                        self.push(" ")?;
                    }
                    self.compile_group(argument, depth)?;
                }
                Ok(())
            }
        }
    }

    fn compile_group(&mut self, node: &MathNode, depth: usize) -> Result<(), EqEditError> {
        self.push("{")?;
        self.compile_node(node, depth)?;
        self.push("}")
    }

    fn compile_grid(&mut self, rows: &[Vec<MathNode>], depth: usize) -> Result<(), EqEditError> {
        self.push("{")?;
        for (row_index, row) in rows.iter().enumerate() {
            if row_index > 0 {
                self.push(" # ")?;
            }
            for (column_index, cell) in row.iter().enumerate() {
                if column_index > 0 {
                    self.push(" & ")?;
                }
                self.compile_group(cell, depth)?;
            }
        }
        self.push("}")
    }

    fn compile_derivative(
        &mut self,
        kind: MathDerivativeKind,
        expression: &MathNode,
        variables: &[MathDerivativeVariable],
        depth: usize,
    ) -> Result<(), EqEditError> {
        let total_order = variables.iter().try_fold(0_u16, |total, variable| {
            total
                .checked_add(variable.order)
                .ok_or(EqEditError::UnsupportedExpression)
        })?;
        let marker = match kind {
            MathDerivativeKind::Ordinary => "d",
            MathDerivativeKind::Partial => "PARTIAL",
        };
        self.push("{{{")?;
        self.push(marker)?;
        self.push("} ^ {")?;
        self.push(&total_order.to_string())?;
        self.push("}} ")?;
        self.compile_group(expression, depth)?;
        self.push("} OVER {")?;
        for (index, variable) in variables.iter().enumerate() {
            if index > 0 {
                self.push(" TIMES ")?;
            }
            self.push("{{")?;
            self.push(marker)?;
            self.push("} {")?;
            self.compile_node(&variable.variable, depth)?;
            self.push("} ^ {")?;
            self.push(&variable.order.to_string())?;
            self.push("}}")?;
        }
        self.push("}")
    }

    fn push(&mut self, value: &str) -> Result<(), EqEditError> {
        let length = self
            .output
            .len()
            .checked_add(value.len())
            .ok_or(EqEditError::OutputLimit)?;
        if length > self.limits.0.script_bytes {
            return Err(EqEditError::OutputLimit);
        }
        self.output.push_str(value);
        Ok(())
    }
}

fn make_node(span: MathSourceSpan, expression: MathExpression) -> MathNode {
    MathNode {
        span,
        style: None,
        expression,
    }
}

fn make_apply(operator: MathOperator, arguments: Vec<MathNode>) -> MathNode {
    let span = arguments
        .iter()
        .map(|node| node.span)
        .reduce(merged_span)
        .unwrap_or(MathSourceSpan {
            start_byte: 0,
            end_byte: 0,
        });
    make_apply_with_span(operator, arguments, span)
}

fn make_apply_with_span(
    operator: MathOperator,
    arguments: Vec<MathNode>,
    span: MathSourceSpan,
) -> MathNode {
    make_node(
        span,
        MathExpression::Apply {
            operator,
            arguments,
        },
    )
}

fn make_row(items: Vec<MathNode>) -> MathNode {
    let span = items
        .iter()
        .map(|node| node.span)
        .reduce(merged_span)
        .unwrap_or(MathSourceSpan {
            start_byte: 0,
            end_byte: 0,
        });
    make_node(span, MathExpression::Row { items })
}

fn make_fraction_or_derivative(
    numerator: MathNode,
    denominator: MathNode,
) -> Result<MathNode, EqEditError> {
    let span = merged_span(numerator.span, denominator.span);
    if let Some(expression) = recognize_derivative(&numerator, &denominator)? {
        return Ok(make_node(span, expression));
    }
    Ok(make_node(
        span,
        MathExpression::Fraction {
            numerator: Box::new(numerator),
            denominator: Box::new(denominator),
        },
    ))
}

fn recognize_derivative(
    numerator: &MathNode,
    denominator: &MathNode,
) -> Result<Option<MathExpression>, EqEditError> {
    let numerator_items = row_items(numerator);
    if numerator_items.len() != 2 {
        return Ok(None);
    }
    let Some((kind, total_order)) = derivative_marker_script(numerator_items[0]) else {
        return Ok(None);
    };
    let denominator_factors: Vec<&MathNode> = match &denominator.expression {
        MathExpression::Apply {
            operator: MathOperator::Multiply,
            arguments,
        } => arguments.iter().collect(),
        _ => vec![denominator],
    };
    let mut variables = Vec::new();
    let mut observed_total = 0_u16;
    for factor in denominator_factors {
        let items = row_items(factor);
        if items.len() != 2 || !derivative_marker_matches(items[0], kind) {
            return Ok(None);
        }
        let MathExpression::Script {
            base,
            subscript: None,
            superscript: Some(order),
        } = &items[1].expression
        else {
            return Ok(None);
        };
        let Some(order) = number_order(order) else {
            return Ok(None);
        };
        observed_total = observed_total
            .checked_add(order)
            .ok_or(EqEditError::InvalidSyntax)?;
        variables.push(MathDerivativeVariable {
            variable: Box::new((**base).clone()),
            order,
        });
    }
    if variables.is_empty() || observed_total != total_order {
        return Ok(None);
    }
    Ok(Some(MathExpression::Derivative {
        derivative_kind: kind,
        expression: Box::new(numerator_items[1].clone()),
        variables,
    }))
}

fn row_items(node: &MathNode) -> Vec<&MathNode> {
    match &node.expression {
        MathExpression::Row { items } => items.iter().collect(),
        _ => vec![node],
    }
}

fn derivative_marker_script(node: &MathNode) -> Option<(MathDerivativeKind, u16)> {
    let MathExpression::Script {
        base,
        subscript: None,
        superscript: Some(order),
    } = &node.expression
    else {
        return None;
    };
    let kind = derivative_marker(base)?;
    Some((kind, number_order(order)?))
}

fn derivative_marker_matches(node: &MathNode, expected: MathDerivativeKind) -> bool {
    derivative_marker(node) == Some(expected)
}

fn derivative_marker(node: &MathNode) -> Option<MathDerivativeKind> {
    match &node.expression {
        MathExpression::Identifier { name } if name == "d" => Some(MathDerivativeKind::Ordinary),
        MathExpression::Symbol {
            symbol: MathSymbol::PartialDifferential,
        } => Some(MathDerivativeKind::Partial),
        _ => None,
    }
}

fn number_order(node: &MathNode) -> Option<u16> {
    let MathExpression::Number { value } = &node.expression else {
        return None;
    };
    let order = value.parse().ok()?;
    (order > 0).then_some(order)
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

fn eq_word(actual: &str, expected: &str) -> bool {
    actual.eq_ignore_ascii_case(expected)
}

fn parse_symbol(name: &str) -> Option<MathSymbol> {
    if let Some((letter, letter_case)) = greek_symbol(name) {
        return Some(MathSymbol::Greek {
            letter,
            letter_case,
        });
    }
    match name.to_ascii_lowercase().as_str() {
        "inf" | "infinity" | "infty" => Some(MathSymbol::Infinity),
        "emptyset" => Some(MathSymbol::EmptySet),
        "aleph" => Some(MathSymbol::Aleph),
        "hbar" => Some(MathSymbol::Hbar),
        "partial" => Some(MathSymbol::PartialDifferential),
        "nabla" => Some(MathSymbol::Nabla),
        "therefore" => Some(MathSymbol::Therefore),
        "because" => Some(MathSymbol::Because),
        "cdots" | "ldots" => Some(MathSymbol::HorizontalEllipsis),
        "vdots" => Some(MathSymbol::VerticalEllipsis),
        "ddots" => Some(MathSymbol::DiagonalEllipsis),
        "deg" => Some(MathSymbol::Degree),
        "prime" => Some(MathSymbol::Prime),
        _ => None,
    }
}

fn greek_symbol(name: &str) -> Option<(MathGreekLetter, MathLetterCase)> {
    let lowercase = name.to_ascii_lowercase();
    let letter = match lowercase.as_str() {
        "alpha" => MathGreekLetter::Alpha,
        "beta" => MathGreekLetter::Beta,
        "gamma" => MathGreekLetter::Gamma,
        "delta" => MathGreekLetter::Delta,
        "epsilon" => MathGreekLetter::Epsilon,
        "zeta" => MathGreekLetter::Zeta,
        "eta" => MathGreekLetter::Eta,
        "theta" => MathGreekLetter::Theta,
        "iota" => MathGreekLetter::Iota,
        "kappa" => MathGreekLetter::Kappa,
        "lambda" => MathGreekLetter::Lambda,
        "mu" => MathGreekLetter::Mu,
        "nu" => MathGreekLetter::Nu,
        "xi" => MathGreekLetter::Xi,
        "omicron" => MathGreekLetter::Omicron,
        "pi" => MathGreekLetter::Pi,
        "rho" => MathGreekLetter::Rho,
        "sigma" => MathGreekLetter::Sigma,
        "tau" => MathGreekLetter::Tau,
        "upsilon" => MathGreekLetter::Upsilon,
        "phi" => MathGreekLetter::Phi,
        "chi" => MathGreekLetter::Chi,
        "psi" => MathGreekLetter::Psi,
        "omega" => MathGreekLetter::Omega,
        _ => return None,
    };
    let letter_case = if name.chars().next().is_some_and(char::is_uppercase) {
        MathLetterCase::Upper
    } else {
        MathLetterCase::Lower
    };
    Some((letter, letter_case))
}

fn parse_accent(name: &str) -> Option<MathAccent> {
    match name.to_ascii_lowercase().as_str() {
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

fn parse_function(name: &str) -> Option<MathFunction> {
    match name {
        "sin" => Some(MathFunction::Sin),
        "cos" => Some(MathFunction::Cos),
        "tan" => Some(MathFunction::Tan),
        "cot" => Some(MathFunction::Cot),
        "sec" => Some(MathFunction::Sec),
        "csc" | "cosec" => Some(MathFunction::Csc),
        "arcsin" => Some(MathFunction::Arcsin),
        "arccos" => Some(MathFunction::Arccos),
        "arctan" => Some(MathFunction::Arctan),
        "sinh" => Some(MathFunction::Sinh),
        "cosh" => Some(MathFunction::Cosh),
        "tanh" => Some(MathFunction::Tanh),
        "log" | "lg" => Some(MathFunction::Log),
        "ln" => Some(MathFunction::NaturalLog),
        "exp" | "Exp" => Some(MathFunction::Exponential),
        "min" => Some(MathFunction::Minimum),
        "max" => Some(MathFunction::Maximum),
        _ => None,
    }
}

fn parse_large_operator(name: &str) -> Option<MathLargeOperator> {
    match name.to_ascii_lowercase().as_str() {
        "lim" => Some(MathLargeOperator::Limit),
        "sum" => Some(MathLargeOperator::Sum),
        "prod" => Some(MathLargeOperator::Product),
        "int" => Some(MathLargeOperator::Integral {
            multiplicity: 1,
            contour: false,
        }),
        "dint" => Some(MathLargeOperator::Integral {
            multiplicity: 2,
            contour: false,
        }),
        "tint" => Some(MathLargeOperator::Integral {
            multiplicity: 3,
            contour: false,
        }),
        "oint" => Some(MathLargeOperator::Integral {
            multiplicity: 1,
            contour: true,
        }),
        "odint" => Some(MathLargeOperator::Integral {
            multiplicity: 2,
            contour: true,
        }),
        "otint" => Some(MathLargeOperator::Integral {
            multiplicity: 3,
            contour: true,
        }),
        _ => None,
    }
}

fn parse_matrix_kind(name: &str) -> Option<MathMatrixKind> {
    match name.to_ascii_lowercase().as_str() {
        "matrix" => Some(MathMatrixKind::Plain),
        "pmatrix" => Some(MathMatrixKind::Parenthesized),
        "bmatrix" => Some(MathMatrixKind::Bracketed),
        "dmatrix" => Some(MathMatrixKind::Determinant),
        _ => None,
    }
}

fn word_operator(name: &str) -> Option<(MathOperator, u8)> {
    match name.to_ascii_lowercase().as_str() {
        "times" => Some((MathOperator::Multiply, 40)),
        "div" | "divide" => Some((MathOperator::Divide, 40)),
        "neq" => Some((MathOperator::NotEqual, 10)),
        "le" | "leq" => Some((MathOperator::LessThanOrEqual, 10)),
        "ge" | "geq" => Some((MathOperator::GreaterThanOrEqual, 10)),
        "approx" => Some((MathOperator::ApproximatelyEqual, 10)),
        "propto" => Some((MathOperator::ProportionalTo, 10)),
        "in" => Some((MathOperator::ElementOf, 10)),
        "notin" | "nin" => Some((MathOperator::NotElementOf, 10)),
        "subseteq" => Some((MathOperator::SubsetOf, 10)),
        "subset" => Some((MathOperator::ProperSubsetOf, 10)),
        "supseteq" => Some((MathOperator::SupersetOf, 10)),
        "supset" => Some((MathOperator::ProperSupersetOf, 10)),
        "union" | "cup" => Some((MathOperator::Union, 25)),
        "inter" | "cap" => Some((MathOperator::Intersection, 25)),
        "circ" => Some((MathOperator::Compose, 40)),
        "sup" => Some((MathOperator::Power, 60)),
        "land" | "and" => Some((MathOperator::LogicalAnd, 20)),
        "lor" | "or" => Some((MathOperator::LogicalOr, 15)),
        "rarrow" => Some((MathOperator::Implies, 8)),
        "equiv" => Some((MathOperator::Equivalent, 8)),
        _ => None,
    }
}

fn is_reserved_word(name: &str) -> bool {
    matches!(
        name.to_ascii_lowercase().as_str(),
        "atop"
            | "bigg"
            | "buildrel"
            | "color"
            | "from"
            | "left"
            | "lpile"
            | "rel"
            | "right"
            | "rm"
            | "rmbold"
            | "bold"
            | "it"
            | "rpile"
            | "scale"
            | "phantom"
            | "to"
            | "under"
            | "underover"
            | "vert"
    ) || parse_symbol(name).is_some()
        || parse_accent(name).is_some()
        || parse_function(name).is_some()
        || parse_large_operator(name).is_some()
        || parse_matrix_kind(name).is_some()
        || word_operator(name).is_some()
        || [
            "sqrt",
            "cases",
            "pile",
            "binom",
            "choose",
            "overline",
            "underline",
        ]
        .iter()
        .any(|reserved| eq_word(name, reserved))
}

fn is_relation(operator: MathOperator) -> bool {
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

fn matching_right(left: MathDelimiter) -> Option<MathDelimiter> {
    match left {
        MathDelimiter::LeftParenthesis => Some(MathDelimiter::RightParenthesis),
        MathDelimiter::LeftBracket => Some(MathDelimiter::RightBracket),
        MathDelimiter::LeftAngle => Some(MathDelimiter::RightAngle),
        MathDelimiter::VerticalBar => Some(MathDelimiter::VerticalBar),
        MathDelimiter::DoubleVerticalBar => Some(MathDelimiter::DoubleVerticalBar),
        _ => None,
    }
}

fn is_compilable_identifier(name: &str) -> bool {
    !name.is_empty()
        && name.chars().count() <= 9
        && name
            .chars()
            .all(|character| character.is_ascii_alphanumeric())
        && name
            .chars()
            .next()
            .is_some_and(|character| character.is_ascii_alphabetic())
        && !is_reserved_word(name)
}

fn is_compilable_text(value: &str) -> bool {
    !value.is_empty()
        && !value.chars().any(|character| {
            character.is_control()
                || matches!(character, '"' | '{' | '}' | '#' | '&' | '~' | '`' | '\\')
        })
}

fn symbol_token(symbol: MathSymbol) -> &'static str {
    match symbol {
        MathSymbol::Greek {
            letter,
            letter_case,
        } => greek_token(letter, letter_case),
        MathSymbol::Infinity => "INF",
        MathSymbol::EmptySet => "EMPTYSET",
        MathSymbol::Aleph => "ALEPH",
        MathSymbol::Hbar => "HBAR",
        MathSymbol::PartialDifferential => "PARTIAL",
        MathSymbol::Nabla => "nabla",
        MathSymbol::Therefore => "THEREFORE",
        MathSymbol::Because => "BECAUSE",
        MathSymbol::HorizontalEllipsis => "CDOTS",
        MathSymbol::VerticalEllipsis => "VDOTS",
        MathSymbol::DiagonalEllipsis => "DDOTS",
        MathSymbol::Degree => "DEG",
        MathSymbol::Prime => "prime",
    }
}

fn greek_token(letter: MathGreekLetter, letter_case: MathLetterCase) -> &'static str {
    match (letter, letter_case) {
        (MathGreekLetter::Alpha, MathLetterCase::Lower) => "alpha",
        (MathGreekLetter::Alpha, MathLetterCase::Upper) => "Alpha",
        (MathGreekLetter::Beta, MathLetterCase::Lower) => "beta",
        (MathGreekLetter::Beta, MathLetterCase::Upper) => "Beta",
        (MathGreekLetter::Gamma, MathLetterCase::Lower) => "gamma",
        (MathGreekLetter::Gamma, MathLetterCase::Upper) => "Gamma",
        (MathGreekLetter::Delta, MathLetterCase::Lower) => "delta",
        (MathGreekLetter::Delta, MathLetterCase::Upper) => "Delta",
        (MathGreekLetter::Epsilon, MathLetterCase::Lower) => "epsilon",
        (MathGreekLetter::Epsilon, MathLetterCase::Upper) => "Epsilon",
        (MathGreekLetter::Zeta, MathLetterCase::Lower) => "zeta",
        (MathGreekLetter::Zeta, MathLetterCase::Upper) => "Zeta",
        (MathGreekLetter::Eta, MathLetterCase::Lower) => "eta",
        (MathGreekLetter::Eta, MathLetterCase::Upper) => "Eta",
        (MathGreekLetter::Theta, MathLetterCase::Lower) => "theta",
        (MathGreekLetter::Theta, MathLetterCase::Upper) => "Theta",
        (MathGreekLetter::Iota, MathLetterCase::Lower) => "iota",
        (MathGreekLetter::Iota, MathLetterCase::Upper) => "Iota",
        (MathGreekLetter::Kappa, MathLetterCase::Lower) => "kappa",
        (MathGreekLetter::Kappa, MathLetterCase::Upper) => "Kappa",
        (MathGreekLetter::Lambda, MathLetterCase::Lower) => "lambda",
        (MathGreekLetter::Lambda, MathLetterCase::Upper) => "Lambda",
        (MathGreekLetter::Mu, MathLetterCase::Lower) => "mu",
        (MathGreekLetter::Mu, MathLetterCase::Upper) => "Mu",
        (MathGreekLetter::Nu, MathLetterCase::Lower) => "nu",
        (MathGreekLetter::Nu, MathLetterCase::Upper) => "Nu",
        (MathGreekLetter::Xi, MathLetterCase::Lower) => "xi",
        (MathGreekLetter::Xi, MathLetterCase::Upper) => "Xi",
        (MathGreekLetter::Omicron, MathLetterCase::Lower) => "omicron",
        (MathGreekLetter::Omicron, MathLetterCase::Upper) => "Omicron",
        (MathGreekLetter::Pi, MathLetterCase::Lower) => "pi",
        (MathGreekLetter::Pi, MathLetterCase::Upper) => "Pi",
        (MathGreekLetter::Rho, MathLetterCase::Lower) => "rho",
        (MathGreekLetter::Rho, MathLetterCase::Upper) => "Rho",
        (MathGreekLetter::Sigma, MathLetterCase::Lower) => "sigma",
        (MathGreekLetter::Sigma, MathLetterCase::Upper) => "Sigma",
        (MathGreekLetter::Tau, MathLetterCase::Lower) => "tau",
        (MathGreekLetter::Tau, MathLetterCase::Upper) => "Tau",
        (MathGreekLetter::Upsilon, MathLetterCase::Lower) => "upsilon",
        (MathGreekLetter::Upsilon, MathLetterCase::Upper) => "Upsilon",
        (MathGreekLetter::Phi, MathLetterCase::Lower) => "phi",
        (MathGreekLetter::Phi, MathLetterCase::Upper) => "Phi",
        (MathGreekLetter::Chi, MathLetterCase::Lower) => "chi",
        (MathGreekLetter::Chi, MathLetterCase::Upper) => "Chi",
        (MathGreekLetter::Psi, MathLetterCase::Lower) => "psi",
        (MathGreekLetter::Psi, MathLetterCase::Upper) => "Psi",
        (MathGreekLetter::Omega, MathLetterCase::Lower) => "omega",
        (MathGreekLetter::Omega, MathLetterCase::Upper) => "Omega",
    }
}

const fn accent_token(accent: MathAccent) -> &'static str {
    match accent {
        MathAccent::VectorArrow => "VEC",
        MathAccent::Hat => "HAT",
        MathAccent::Bar => "BAR",
        MathAccent::Tilde => "TILDE",
        MathAccent::Dot => "DOT",
        MathAccent::DoubleDot => "DDOT",
        MathAccent::Check => "CHECK",
        MathAccent::Acute => "ACUTE",
        MathAccent::Grave => "GRAVE",
    }
}

fn function_token(function: &MathFunction) -> Option<&'static str> {
    match function {
        MathFunction::Sin => Some("sin"),
        MathFunction::Cos => Some("cos"),
        MathFunction::Tan => Some("tan"),
        MathFunction::Cot => Some("cot"),
        MathFunction::Sec => Some("sec"),
        MathFunction::Csc => Some("csc"),
        MathFunction::Arcsin => Some("arcsin"),
        MathFunction::Arccos => Some("arccos"),
        MathFunction::Arctan => Some("arctan"),
        MathFunction::Sinh => Some("sinh"),
        MathFunction::Cosh => Some("cosh"),
        MathFunction::Tanh => Some("tanh"),
        MathFunction::Log => Some("log"),
        MathFunction::NaturalLog => Some("ln"),
        MathFunction::Exponential => Some("exp"),
        MathFunction::Minimum => Some("min"),
        MathFunction::Maximum => Some("max"),
        MathFunction::Named { .. } => None,
    }
}

fn operator_token(operator: MathOperator) -> Option<&'static str> {
    match operator {
        MathOperator::Add => Some("+"),
        MathOperator::Subtract => Some("-"),
        MathOperator::Multiply => Some("TIMES"),
        MathOperator::Divide => Some("DIVIDE"),
        MathOperator::Power => Some("SUP"),
        MathOperator::Equal => Some("="),
        MathOperator::NotEqual => Some("NEQ"),
        MathOperator::LessThan => Some("<"),
        MathOperator::LessThanOrEqual => Some("LEQ"),
        MathOperator::GreaterThan => Some(">"),
        MathOperator::GreaterThanOrEqual => Some("GEQ"),
        MathOperator::ApproximatelyEqual => Some("APPROX"),
        MathOperator::ProportionalTo => Some("PROPTO"),
        MathOperator::LogicalAnd => Some("LAND"),
        MathOperator::LogicalOr => Some("LOR"),
        MathOperator::Implies => Some("RARROW"),
        MathOperator::Equivalent => Some("EQUIV"),
        MathOperator::ElementOf => Some("IN"),
        MathOperator::NotElementOf => Some("NOTIN"),
        MathOperator::SubsetOf => Some("SUBSETEQ"),
        MathOperator::ProperSubsetOf => Some("SUBSET"),
        MathOperator::SupersetOf => Some("SUPSETEQ"),
        MathOperator::ProperSupersetOf => Some("SUPSET"),
        MathOperator::Union => Some("UNION"),
        MathOperator::Intersection => Some("INTER"),
        MathOperator::Compose => Some("CIRC"),
        MathOperator::SetDifference
        | MathOperator::Positive
        | MathOperator::Negative
        | MathOperator::Factorial
        | MathOperator::LogicalNot => None,
    }
}

fn large_operator_token(operator: MathLargeOperator) -> Result<&'static str, EqEditError> {
    match operator {
        MathLargeOperator::Limit => Ok("lim"),
        MathLargeOperator::Sum => Ok("SUM"),
        MathLargeOperator::Product => Ok("PROD"),
        MathLargeOperator::Integral {
            multiplicity: 1,
            contour: false,
        } => Ok("INT"),
        MathLargeOperator::Integral {
            multiplicity: 2,
            contour: false,
        } => Ok("DINT"),
        MathLargeOperator::Integral {
            multiplicity: 3,
            contour: false,
        } => Ok("TINT"),
        MathLargeOperator::Integral {
            multiplicity: 1,
            contour: true,
        } => Ok("OINT"),
        MathLargeOperator::Integral {
            multiplicity: 2,
            contour: true,
        } => Ok("ODINT"),
        MathLargeOperator::Integral {
            multiplicity: 3,
            contour: true,
        } => Ok("OTINT"),
        MathLargeOperator::Integral { .. } => Err(EqEditError::UnsupportedExpression),
    }
}

fn matrix_token(kind: MathMatrixKind) -> Result<&'static str, EqEditError> {
    match kind {
        MathMatrixKind::Plain => Ok("MATRIX"),
        MathMatrixKind::Parenthesized => Ok("PMATRIX"),
        MathMatrixKind::Bracketed => Ok("BMATRIX"),
        MathMatrixKind::Determinant => Ok("DMATRIX"),
        MathMatrixKind::DoubleBar => Err(EqEditError::UnsupportedExpression),
    }
}

fn delimiter_tokens(
    left: MathDelimiter,
    right: MathDelimiter,
) -> Result<(&'static str, &'static str), EqEditError> {
    let pair = match (left, right) {
        (MathDelimiter::LeftParenthesis, MathDelimiter::RightParenthesis) => ("(", ")"),
        (MathDelimiter::LeftBracket, MathDelimiter::RightBracket) => ("[", "]"),
        (MathDelimiter::LeftAngle, MathDelimiter::RightAngle) => ("<", ">"),
        (MathDelimiter::VerticalBar, MathDelimiter::VerticalBar) => ("|", "|"),
        (MathDelimiter::DoubleVerticalBar, MathDelimiter::DoubleVerticalBar) => ("||", "||"),
        _ => return Err(EqEditError::UnsupportedExpression),
    };
    Ok(pair)
}

fn bounded_json<T: Serialize>(value: &T, limits: EqEditLimits) -> Result<Vec<u8>, EqEditError> {
    let bytes = serde_json::to_vec(value).map_err(|_| EqEditError::Serialization)?;
    if bytes.len() > limits.0.serialized_bytes {
        return Err(EqEditError::OutputLimit);
    }
    Ok(bytes)
}
