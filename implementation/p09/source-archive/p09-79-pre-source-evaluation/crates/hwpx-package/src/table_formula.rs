use std::collections::BTreeSet;

use domain_ir::{
    CellCoordinate, FormulaAst, FormulaAstDraft, FormulaCache, FormulaCell, FormulaCellDraft,
    FormulaDecimal, FormulaError, FormulaExpression, FormulaFunction, FormulaGridDimensions,
    FormulaLimits, FormulaNumberFormat, FormulaRange, FormulaReferenceKind, FormulaValue,
    TABLE_FORMULA_SCHEMA_VERSION,
};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlTokenKind,
};

mod number_format_hwpx;
mod thousands_hwpx;

pub use number_format_hwpx::{
    TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID, TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION,
    TableNumberFormatHwpxError, TableNumberFormatHwpxLowerer, TableNumberFormatHwpxLoweringReceipt,
    TableNumberFormatHwpxReadback, TableNumberFormatHwpxReader, TableNumberFormatHwpxRequest,
    TableNumberFormatHwpxRequestDraft,
};

pub use thousands_hwpx::{
    TABLE_THOUSANDS_HWPX_PROFILE_ID, TABLE_THOUSANDS_HWPX_SCHEMA_VERSION, TableThousandsHwpxError,
    TableThousandsHwpxLowerer, TableThousandsHwpxLoweringReceipt, TableThousandsHwpxReadback,
    TableThousandsHwpxReader, TableThousandsHwpxRequest, TableThousandsHwpxRequestDraft,
};

pub const TABLE_FORMULA_HWPX_PROFILE_ID: &str = "hwpx-agent.table-formula-hwpx.hancom-2020/1";
pub const TABLE_CANONICAL_FORMULA_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-canonical-formula-hwpx.hancom-2020/1";
pub(crate) const TABLE_AGGREGATE_FORMULA_HWPX_PROFILE_ID: &str =
    "hwpx-agent.table-aggregate-formula-hwpx.hancom-2020/1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const NATIVE_LEFT_FORMULA: &str = "=SUM(LEFT)";
const NATIVE_GENERAL_FORMAT: &str = "%g,";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableFormulaHwpxLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub elements: usize,
    pub tables: usize,
    pub cells: usize,
    pub formula_fields: usize,
    pub text_bytes: usize,
}

impl Default for TableFormulaHwpxLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            tables: 32_768,
            cells: 1_000_000,
            formula_fields: 65_536,
            text_bytes: 64 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableFormulaHwpxLimits(TableFormulaHwpxLimitConfig);

impl TableFormulaHwpxLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_TABLES: usize = 65_536;
    pub const HARD_MAX_CELLS: usize = 2_000_000;
    pub const HARD_MAX_FORMULA_FIELDS: usize = 131_072;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;

    /// Creates finite limits for the current-Hangul-2020 formula adapter.
    ///
    /// # Errors
    ///
    /// Returns [`TableFormulaHwpxError::InvalidLimit`] when any value is zero or exceeds its hard
    /// ceiling.
    pub fn new(config: TableFormulaHwpxLimitConfig) -> Result<Self, TableFormulaHwpxError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.tables == 0
            || config.tables > Self::HARD_MAX_TABLES
            || config.cells == 0
            || config.cells > Self::HARD_MAX_CELLS
            || config.formula_fields == 0
            || config.formula_fields > Self::HARD_MAX_FORMULA_FIELDS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
        {
            return Err(TableFormulaHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableFormulaHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TableFormulaHwpxReadback {
    pub profile_id: &'static str,
    pub rows: u32,
    pub columns: u32,
    pub formula: FormulaCell,
    pub formula_field_count: usize,
    pub unowned_sha256: [u8; 32],
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TableFormulaHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_sha256: [u8; 32],
    pub output_sha256: [u8; 32],
    pub source_formula_sha256: [u8; 32],
    pub target_formula_sha256: [u8; 32],
    pub unowned_sha256: [u8; 32],
    pub source_bytes: usize,
    pub output_bytes: usize,
    pub rows: u32,
    pub columns: u32,
    pub owner: CellCoordinate,
    pub modified_text_count: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct TableAggregateFormulaHwpxInsertionReceipt {
    pub source_sha256: [u8; 32],
    pub output_sha256: [u8; 32],
    pub target_formula_sha256: [u8; 32],
    pub owner: CellCoordinate,
    pub inserted_field_count: usize,
}

#[derive(Debug, Error)]
pub enum TableFormulaHwpxError {
    #[error("table formula HWPX limit is invalid")]
    InvalidLimit,
    #[error("table formula HWPX input is empty or oversized")]
    InputLimit,
    #[error("table formula HWPX output is oversized")]
    OutputLimit,
    #[error("table formula HWPX element limit was exceeded")]
    ElementLimit,
    #[error("table formula HWPX table limit was exceeded")]
    TableLimit,
    #[error("table formula HWPX cell limit was exceeded")]
    CellLimit,
    #[error("table formula HWPX formula-field limit was exceeded")]
    FormulaFieldLimit,
    #[error("table formula HWPX section root is unsupported")]
    WrongRoot,
    #[error("table formula HWPX source shape is unsupported")]
    UnsupportedShape,
    #[error("table formula HWPX number is invalid")]
    InvalidNumber,
    #[error("table formula HWPX text is invalid or oversized")]
    InvalidText,
    #[error("table formula HWPX target is not the exact native left-prefix mapping")]
    UnsupportedFormula,
    #[error("table formula HWPX target cache is unsupported")]
    UnsupportedCache,
    #[error("table formula HWPX semantic readback does not match the target")]
    ReadbackMismatch,
    #[error("table formula HWPX unowned bytes changed")]
    PreservationMismatch,
    #[error("table formula HWPX allocation failed")]
    AllocationFailed,
    #[error("table formula core rejected the value: {0}")]
    Formula(#[from] FormulaError),
    #[error("table formula XML is invalid: {0}")]
    Xml(#[from] PreservingXmlError),
}

impl TableFormulaHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_formula_hwpx_invalid_limit",
            Self::InputLimit => "table_formula_hwpx_input_limit",
            Self::OutputLimit => "table_formula_hwpx_output_limit",
            Self::ElementLimit => "table_formula_hwpx_element_limit",
            Self::TableLimit => "table_formula_hwpx_table_limit",
            Self::CellLimit => "table_formula_hwpx_cell_limit",
            Self::FormulaFieldLimit => "table_formula_hwpx_formula_field_limit",
            Self::WrongRoot => "table_formula_hwpx_wrong_root",
            Self::UnsupportedShape => "table_formula_hwpx_unsupported_shape",
            Self::InvalidNumber => "table_formula_hwpx_invalid_number",
            Self::InvalidText => "table_formula_hwpx_invalid_text",
            Self::UnsupportedFormula => "table_formula_hwpx_unsupported_formula",
            Self::UnsupportedCache => "table_formula_hwpx_unsupported_cache",
            Self::ReadbackMismatch => "table_formula_hwpx_readback_mismatch",
            Self::PreservationMismatch => "table_formula_hwpx_preservation_mismatch",
            Self::AllocationFailed => "table_formula_hwpx_allocation_failed",
            Self::Formula(_) => "table_formula_hwpx_formula_core",
            Self::Xml(_) => "table_formula_hwpx_invalid_xml",
        }
    }
}

#[derive(Debug)]
pub struct TableFormulaHwpxReader;

impl TableFormulaHwpxReader {
    /// Reads the single admitted formula from a table selected by zero-based document order.
    ///
    /// The current profile admits only Hangul 2020's exact `SUM(LEFT)` field shape and lifts it to
    /// the locale-neutral `SUM(A1:owner-left)` AST with an explicitly unverified decimal cache.
    ///
    /// # Errors
    ///
    /// Rejects unsafe XML, missing or ambiguous tables/cells/formulas, field-shape drift, unknown
    /// native syntax, mismatched field IDs, cache/visible-text drift, and finite-limit failures.
    pub fn read_in_section(
        bytes: &[u8],
        table_ordinal: usize,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<TableFormulaHwpxReadback, TableFormulaHwpxError> {
        Ok(read_shape(
            bytes,
            table_ordinal,
            limits,
            formula_limits,
            false,
            FormulaFieldProfile::LeftPrefix,
        )?
        .readback)
    }

    pub(crate) fn read_in_section_preserving_merged_topology(
        bytes: &[u8],
        table_ordinal: usize,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<TableFormulaHwpxReadback, TableFormulaHwpxError> {
        Ok(read_shape(
            bytes,
            table_ordinal,
            limits,
            formula_limits,
            true,
            FormulaFieldProfile::LeftPrefix,
        )?
        .readback)
    }

    pub(crate) fn read_aggregate_in_section(
        bytes: &[u8],
        table_ordinal: usize,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<TableFormulaHwpxReadback, TableFormulaHwpxError> {
        Ok(read_shape(
            bytes,
            table_ordinal,
            limits,
            formula_limits,
            false,
            FormulaFieldProfile::Aggregate,
        )?
        .readback)
    }

    /// Reads one selected canonical formula field while preserving every other formula as opaque
    /// unowned bytes.
    ///
    /// The selected field may contain the complete bounded locale-neutral formula grammar,
    /// including independently absolute row and column axes. Its native formula text must be the
    /// exact `=`-prefixed canonical AST. A blank cache is lifted as [`FormulaCache::Absent`]; a
    /// nonblank cache must be one canonical decimal mirrored by the visible result.
    ///
    /// # Errors
    ///
    /// Rejects an absent or ambiguous selected owner, noncanonical formula/cache text, malformed
    /// field identity, grid drift, or any finite-limit failure.
    pub fn read_canonical_cell_in_section(
        bytes: &[u8],
        table_ordinal: usize,
        owner: CellCoordinate,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<TableFormulaHwpxReadback, TableFormulaHwpxError> {
        Ok(
            read_canonical_cell_shape(bytes, table_ordinal, owner, limits, formula_limits)?
                .readback,
        )
    }

    /// Counts selected-profile formulas in one selected table after applying the same exact-shape
    /// validation as [`Self::read_in_section`].
    ///
    /// # Errors
    ///
    /// Applies the same fail-closed checks as [`Self::read_in_section`].
    pub fn formula_count_in_section(
        bytes: &[u8],
        table_ordinal: usize,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<usize, TableFormulaHwpxError> {
        Ok(read_shape(
            bytes,
            table_ordinal,
            limits,
            formula_limits,
            false,
            FormulaFieldProfile::LeftPrefix,
        )?
        .readback
        .formula_field_count)
    }
}

#[derive(Debug)]
pub struct TableFormulaHwpxLowerer;

impl TableFormulaHwpxLowerer {
    pub(crate) fn validate_target(
        target: &FormulaCell,
        limits: TableFormulaHwpxLimits,
    ) -> Result<(), TableFormulaHwpxError> {
        require_left_prefix(target)?;
        if target.number_format() != FormulaNumberFormat::General {
            return Err(TableFormulaHwpxError::UnsupportedFormula);
        }
        let result = cache_decimal_text(target.cache())?;
        if result.len() > limits.0.text_bytes {
            return Err(TableFormulaHwpxError::InvalidText);
        }
        let command = format!("{NATIVE_LEFT_FORMULA}??{NATIVE_GENERAL_FORMAT};;{result}");
        if command.len() > limits.0.text_bytes {
            return Err(TableFormulaHwpxError::InvalidText);
        }
        Ok(())
    }

    /// Lowers one exact left-prefix formula and unverified decimal cache into a selected section
    /// table without exposing native field commands through the public API.
    ///
    /// # Errors
    ///
    /// Rejects dimension/owner drift, non-left-prefix formulas, non-General formats, absent or
    /// non-decimal caches, source-shape drift, over-limit output, semantic readback drift, or any
    /// unowned-byte change.
    pub fn lower_in_section(
        source: &[u8],
        table_ordinal: usize,
        target: &FormulaCell,
        dimensions: FormulaGridDimensions,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<Vec<u8>, TableFormulaHwpxError> {
        Self::lower_in_section_with_receipt(
            source,
            table_ordinal,
            target,
            dimensions,
            limits,
            formula_limits,
        )
        .map(|(bytes, _)| bytes)
    }

    /// Applies [`Self::lower_in_section`] and returns source/target integrity evidence.
    ///
    /// # Errors
    ///
    /// Applies the same fail-closed checks as [`Self::lower_in_section`].
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        table_ordinal: usize,
        target: &FormulaCell,
        dimensions: FormulaGridDimensions,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<(Vec<u8>, TableFormulaHwpxLoweringReceipt), TableFormulaHwpxError> {
        lower_in_section_profile(
            source,
            table_ordinal,
            target,
            dimensions,
            limits,
            formula_limits,
            false,
        )
    }

    pub(crate) fn lower_in_section_preserving_merged_topology(
        source: &[u8],
        table_ordinal: usize,
        target: &FormulaCell,
        dimensions: FormulaGridDimensions,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<(Vec<u8>, TableFormulaHwpxLoweringReceipt), TableFormulaHwpxError> {
        lower_in_section_profile(
            source,
            table_ordinal,
            target,
            dimensions,
            limits,
            formula_limits,
            true,
        )
    }

    pub(crate) fn insert_aggregate_in_section(
        source: &[u8],
        table_ordinal: usize,
        target: &FormulaCell,
        dimensions: FormulaGridDimensions,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<(Vec<u8>, TableAggregateFormulaHwpxInsertionReceipt), TableFormulaHwpxError> {
        let native_formula = aggregate_native_formula(target, formula_limits)?;
        let result = cache_decimal_text(target.cache())?;
        if native_formula.len() > limits.0.text_bytes || result.len() > limits.0.text_bytes {
            return Err(TableFormulaHwpxError::InvalidText);
        }
        let command = format!("{native_formula}??{NATIVE_GENERAL_FORMAT};;{result}");
        if command.len() > limits.0.text_bytes {
            return Err(TableFormulaHwpxError::InvalidText);
        }

        let document = parse_document(source, limits)?;
        validate_document_envelope(&document)?;
        validate_section_root(&document)?;
        let table = table_indexes(&document, limits)?
            .get(table_ordinal)
            .copied()
            .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
        let grid = read_cells(&document, table, limits, false)?;
        if grid.rows != dimensions.rows || grid.columns != dimensions.columns {
            return Err(TableFormulaHwpxError::UnsupportedShape);
        }
        if !formula_fields(&document, table, limits)?.is_empty() {
            return Err(TableFormulaHwpxError::UnsupportedShape);
        }
        let cell = grid
            .cells
            .iter()
            .find_map(|(index, coordinate)| (*coordinate == target.owner()).then_some(*index))
            .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
        let run = empty_cell_run(&document, cell, limits)?;
        let span = element(&document, run)?
            .content_span()
            .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
        let (begin_id, field_id) = reserve_field_ids(&document)?;
        let prefix = element(&document, run)?.name().prefix();
        let replacement = aggregate_field_xml(
            prefix,
            begin_id,
            field_id,
            &command,
            &native_formula,
            &result,
        );
        let output = apply_edits(source, &mut [ByteEdit::new(span, replacement)], limits)?;
        let readback = TableFormulaHwpxReader::read_aggregate_in_section(
            &output,
            table_ordinal,
            limits,
            formula_limits,
        )?;
        if readback.rows != dimensions.rows
            || readback.columns != dimensions.columns
            || readback.formula != *target
            || readback.formula_field_count != 1
        {
            return Err(TableFormulaHwpxError::ReadbackMismatch);
        }
        let receipt = TableAggregateFormulaHwpxInsertionReceipt {
            source_sha256: Sha256::digest(source).into(),
            output_sha256: Sha256::digest(&output).into(),
            target_formula_sha256: target.canonical_sha256(formula_limits)?,
            owner: target.owner(),
            inserted_field_count: 1,
        };
        Ok((output, receipt))
    }

    /// Rewrites one selected canonical formula field and its explicitly bound cache.
    ///
    /// Other formula fields and all bytes outside the selected field's formula, command, cache and
    /// visible-result text spans are preserved exactly. The target must contain at least one
    /// absolute reference axis and retain `General` number formatting.
    ///
    /// # Errors
    ///
    /// Rejects owner/dimension drift, a target without an absolute axis, unsupported cache or
    /// format state, noncanonical native text, output-limit failure, semantic reopen mismatch, or
    /// any unowned-byte change.
    pub fn lower_canonical_cell_in_section_with_receipt(
        source: &[u8],
        table_ordinal: usize,
        owner: CellCoordinate,
        target: &FormulaCell,
        dimensions: FormulaGridDimensions,
        limits: TableFormulaHwpxLimits,
        formula_limits: FormulaLimits,
    ) -> Result<(Vec<u8>, TableFormulaHwpxLoweringReceipt), TableFormulaHwpxError> {
        let source_shape =
            read_canonical_cell_shape(source, table_ordinal, owner, limits, formula_limits)?;
        if dimensions.rows != source_shape.readback.rows
            || dimensions.columns != source_shape.readback.columns
            || target.owner() != owner
            || target.number_format() != FormulaNumberFormat::General
            || !expression_has_absolute_axis(target.ast().expression())
        {
            return Err(TableFormulaHwpxError::UnsupportedFormula);
        }
        let native_formula = canonical_native_formula(target, formula_limits)?;
        let result = canonical_cache_text(target.cache(), formula_limits)?;
        if native_formula.len() > limits.0.text_bytes || result.len() > limits.0.text_bytes {
            return Err(TableFormulaHwpxError::InvalidText);
        }
        let command = format!("{native_formula}??{NATIVE_GENERAL_FORMAT};;{result}");
        if command.len() > limits.0.text_bytes {
            return Err(TableFormulaHwpxError::InvalidText);
        }
        let mut edits = [
            ByteEdit::new(source_shape.command_span, command.into_bytes()),
            ByteEdit::new(source_shape.formula_span, native_formula.into_bytes()),
            ByteEdit::new(source_shape.last_result_span, result.as_bytes().to_vec()),
            ByteEdit::new(source_shape.visible_result_span, result.into_bytes()),
        ];
        let output = apply_edits(source, &mut edits, limits)?;
        let output_shape =
            read_canonical_cell_shape(&output, table_ordinal, owner, limits, formula_limits)?;
        if output_shape.readback.formula != *target
            || output_shape.readback.rows != dimensions.rows
            || output_shape.readback.columns != dimensions.columns
        {
            return Err(TableFormulaHwpxError::ReadbackMismatch);
        }
        if output_shape.readback.unowned_sha256 != source_shape.readback.unowned_sha256 {
            return Err(TableFormulaHwpxError::PreservationMismatch);
        }
        let receipt = TableFormulaHwpxLoweringReceipt {
            profile_id: TABLE_CANONICAL_FORMULA_HWPX_PROFILE_ID,
            source_sha256: Sha256::digest(source).into(),
            output_sha256: Sha256::digest(&output).into(),
            source_formula_sha256: source_shape
                .readback
                .formula
                .canonical_sha256(formula_limits)?,
            target_formula_sha256: target.canonical_sha256(formula_limits)?,
            unowned_sha256: output_shape.readback.unowned_sha256,
            source_bytes: source.len(),
            output_bytes: output.len(),
            rows: dimensions.rows,
            columns: dimensions.columns,
            owner,
            modified_text_count: edits.len(),
        };
        Ok((output, receipt))
    }
}

#[allow(clippy::too_many_arguments)]
fn lower_in_section_profile(
    source: &[u8],
    table_ordinal: usize,
    target: &FormulaCell,
    dimensions: FormulaGridDimensions,
    limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
    allow_merged_cells: bool,
) -> Result<(Vec<u8>, TableFormulaHwpxLoweringReceipt), TableFormulaHwpxError> {
    let source_shape = read_shape(
        source,
        table_ordinal,
        limits,
        formula_limits,
        allow_merged_cells,
        FormulaFieldProfile::LeftPrefix,
    )?;
    if dimensions.rows != source_shape.readback.rows
        || dimensions.columns != source_shape.readback.columns
        || target.owner() != source_shape.readback.formula.owner()
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    TableFormulaHwpxLowerer::validate_target(target, limits)?;
    let result = cache_decimal_text(target.cache())?;
    let command = format!("{NATIVE_LEFT_FORMULA}??{NATIVE_GENERAL_FORMAT};;{result}");

    let mut edits = [
        ByteEdit::new(source_shape.command_span, command.into_bytes()),
        ByteEdit::new(source_shape.last_result_span, result.as_bytes().to_vec()),
        ByteEdit::new(source_shape.visible_result_span, result.into_bytes()),
    ];
    let output = apply_edits(source, &mut edits, limits)?;
    let output_shape = read_shape(
        &output,
        table_ordinal,
        limits,
        formula_limits,
        allow_merged_cells,
        FormulaFieldProfile::LeftPrefix,
    )?;
    if &output_shape.readback.formula != target
        || output_shape.readback.rows != dimensions.rows
        || output_shape.readback.columns != dimensions.columns
    {
        return Err(TableFormulaHwpxError::ReadbackMismatch);
    }
    if output_shape.readback.unowned_sha256 != source_shape.readback.unowned_sha256 {
        return Err(TableFormulaHwpxError::PreservationMismatch);
    }
    let receipt = TableFormulaHwpxLoweringReceipt {
        profile_id: TABLE_FORMULA_HWPX_PROFILE_ID,
        source_sha256: Sha256::digest(source).into(),
        output_sha256: Sha256::digest(&output).into(),
        source_formula_sha256: source_shape
            .readback
            .formula
            .canonical_sha256(formula_limits)?,
        target_formula_sha256: target.canonical_sha256(formula_limits)?,
        unowned_sha256: output_shape.readback.unowned_sha256,
        source_bytes: source.len(),
        output_bytes: output.len(),
        rows: dimensions.rows,
        columns: dimensions.columns,
        owner: target.owner(),
        modified_text_count: edits.len(),
    };
    Ok((output, receipt))
}

#[derive(Debug)]
struct FormulaShape {
    readback: TableFormulaHwpxReadback,
    command_span: XmlByteSpan,
    formula_span: XmlByteSpan,
    last_result_span: XmlByteSpan,
    visible_result_span: XmlByteSpan,
}

/// Reads this exact source field, not a caller-selected formula/table/owner.
/// Existing field, grid, cache/visible parity and canonical AST guards remain
/// unchanged. Cache values remain explicitly unverified, never evaluated.
pub(crate) fn read_imported_field(
    document: &PreservingXmlDocument,
    field_begin: usize,
) -> Result<(FormulaGridDimensions, FormulaCell), TableFormulaHwpxError> {
    let limits = TableFormulaHwpxLimits::default();
    let formula_limits = FormulaLimits::default();
    if document.original_len() > limits.0.input_bytes
        || document.elements().len() > limits.0.elements
    {
        return Err(TableFormulaHwpxError::InputLimit);
    }
    validate_document_envelope(document)?;
    validate_section_root(document)?;
    let mut ancestor = element(document, field_begin)?.parent();
    let table = loop {
        let index = ancestor.ok_or(TableFormulaHwpxError::UnsupportedShape)?;
        let value = element(document, index)?;
        if has_paragraph_name(value, "tbl") {
            break index;
        }
        ancestor = value.parent();
    };
    let _ = table_indexes(document, limits)?;
    let grid = read_cells(document, table, limits, true)?;
    let cell = owning_direct_cell(document, field_begin, table)?;
    let owner = grid
        .cells
        .iter()
        .find_map(|(index, coordinate)| (*index == cell).then_some(*coordinate))
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    let envelope = validate_field_envelope(document, field_begin, limits)?;
    let parameters = read_field_parameters(document, envelope.parameters, limits)?;
    let profile = if parameters.native_formula.text == NATIVE_LEFT_FORMULA {
        FormulaFieldProfile::LeftPrefix
    } else {
        FormulaFieldProfile::Canonical
    };
    let dimensions = FormulaGridDimensions {
        rows: grid.rows,
        columns: grid.columns,
    };
    let field = read_field(
        document,
        field_begin,
        owner,
        dimensions,
        limits,
        formula_limits,
        profile,
    )?;
    Ok((dimensions, field.formula))
}

fn read_shape(
    bytes: &[u8],
    table_ordinal: usize,
    limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
    allow_merged_cells: bool,
    profile: FormulaFieldProfile,
) -> Result<FormulaShape, TableFormulaHwpxError> {
    let document = parse_document(bytes, limits)?;
    validate_document_envelope(&document)?;
    validate_section_root(&document)?;
    let tables = table_indexes(&document, limits)?;
    let table = tables
        .get(table_ordinal)
        .copied()
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    let grid = read_cells(&document, table, limits, allow_merged_cells)?;
    let formula_fields = formula_fields(&document, table, limits)?;
    if formula_fields.len() != 1 {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let field_begin = formula_fields[0];
    let cell = owning_direct_cell(&document, field_begin, table)?;
    let owner = grid
        .cells
        .iter()
        .find_map(|(index, coordinate)| (*index == cell).then_some(*coordinate))
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    let dimensions = FormulaGridDimensions {
        rows: grid.rows,
        columns: grid.columns,
    };
    let field = read_field(
        &document,
        field_begin,
        owner,
        dimensions,
        limits,
        formula_limits,
        profile,
    )?;
    let owned_spans = [
        field.command_span,
        field.formula_span,
        field.result_format_span,
        field.last_result_span,
        field.visible_result_span,
    ];
    let profile_id = match profile {
        FormulaFieldProfile::LeftPrefix => TABLE_FORMULA_HWPX_PROFILE_ID,
        FormulaFieldProfile::Aggregate => TABLE_AGGREGATE_FORMULA_HWPX_PROFILE_ID,
        FormulaFieldProfile::Canonical => TABLE_CANONICAL_FORMULA_HWPX_PROFILE_ID,
    };
    let unowned_sha256 = digest_excluding(bytes, &owned_spans, profile_id)?;
    Ok(FormulaShape {
        readback: TableFormulaHwpxReadback {
            profile_id,
            rows: grid.rows,
            columns: grid.columns,
            formula: field.formula,
            formula_field_count: formula_fields.len(),
            unowned_sha256,
        },
        command_span: field.command_span,
        formula_span: field.formula_span,
        last_result_span: field.last_result_span,
        visible_result_span: field.visible_result_span,
    })
}

fn read_canonical_cell_shape(
    bytes: &[u8],
    table_ordinal: usize,
    owner: CellCoordinate,
    limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
) -> Result<FormulaShape, TableFormulaHwpxError> {
    let document = parse_document(bytes, limits)?;
    validate_document_envelope(&document)?;
    validate_section_root(&document)?;
    let table = table_indexes(&document, limits)?
        .get(table_ordinal)
        .copied()
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    let grid = read_cells(&document, table, limits, true)?;
    let fields = formula_fields(&document, table, limits)?;
    let mut selected = None;
    for field_begin in &fields {
        let cell = owning_direct_cell(&document, *field_begin, table)?;
        let coordinate = grid
            .cells
            .iter()
            .find_map(|(index, coordinate)| (*index == cell).then_some(*coordinate))
            .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
        if coordinate == owner && selected.replace(*field_begin).is_some() {
            return Err(TableFormulaHwpxError::UnsupportedShape);
        }
    }
    let field_begin = selected.ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    let dimensions = FormulaGridDimensions {
        rows: grid.rows,
        columns: grid.columns,
    };
    let field = read_field(
        &document,
        field_begin,
        owner,
        dimensions,
        limits,
        formula_limits,
        FormulaFieldProfile::Canonical,
    )?;
    let owned_spans = [
        field.command_span,
        field.formula_span,
        field.last_result_span,
        field.visible_result_span,
    ];
    let unowned_sha256 =
        digest_excluding(bytes, &owned_spans, TABLE_CANONICAL_FORMULA_HWPX_PROFILE_ID)?;
    Ok(FormulaShape {
        readback: TableFormulaHwpxReadback {
            profile_id: TABLE_CANONICAL_FORMULA_HWPX_PROFILE_ID,
            rows: grid.rows,
            columns: grid.columns,
            formula: field.formula,
            formula_field_count: fields.len(),
            unowned_sha256,
        },
        command_span: field.command_span,
        formula_span: field.formula_span,
        last_result_span: field.last_result_span,
        visible_result_span: field.visible_result_span,
    })
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum FormulaFieldProfile {
    LeftPrefix,
    Aggregate,
    Canonical,
}

#[derive(Debug)]
struct FieldReadback {
    formula: FormulaCell,
    command_span: XmlByteSpan,
    formula_span: XmlByteSpan,
    result_format_span: XmlByteSpan,
    last_result_span: XmlByteSpan,
    visible_result_span: XmlByteSpan,
}

fn read_field(
    document: &PreservingXmlDocument,
    field_begin: usize,
    owner: CellCoordinate,
    dimensions: FormulaGridDimensions,
    limits: TableFormulaHwpxLimits,
    formula_limits: FormulaLimits,
    profile: FormulaFieldProfile,
) -> Result<FieldReadback, TableFormulaHwpxError> {
    let envelope = validate_field_envelope(document, field_begin, limits)?;
    let parameters = read_field_parameters(document, envelope.parameters, limits)?;
    if parameters.result_format.text != NATIVE_GENERAL_FORMAT
        || parameters.command.text
            != format!(
                "{}??{NATIVE_GENERAL_FORMAT};;{}",
                parameters.native_formula.text, parameters.last_result.text
            )
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let visible = leaf_text_with_span(document, envelope.visible_result, limits)?;
    if visible.text != parameters.last_result.text {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let cache =
        if parameters.last_result.text.is_empty() && profile == FormulaFieldProfile::Canonical {
            FormulaCache::Absent
        } else {
            FormulaCache::Unverified {
                value: FormulaValue::Decimal {
                    value: parse_canonical_decimal(parameters.last_result.text, formula_limits)?,
                },
            }
        };
    let ast = match profile {
        FormulaFieldProfile::LeftPrefix => {
            if parameters.native_formula.text != NATIVE_LEFT_FORMULA {
                return Err(TableFormulaHwpxError::UnsupportedShape);
            }
            left_prefix_ast(owner, formula_limits)?
        }
        FormulaFieldProfile::Aggregate => {
            aggregate_ast(parameters.native_formula.text, formula_limits)?
        }
        FormulaFieldProfile::Canonical => {
            canonical_native_ast(parameters.native_formula.text, formula_limits)?
        }
    };
    let formula = FormulaCell::from_draft(
        FormulaCellDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            owner,
            ast: FormulaAstDraft {
                schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
                expression: ast.expression().clone(),
            },
            cache,
            number_format: FormulaNumberFormat::General,
        },
        dimensions,
        formula_limits,
    )?;
    Ok(FieldReadback {
        formula,
        command_span: parameters.command.span,
        formula_span: parameters.native_formula.span,
        result_format_span: parameters.result_format.span,
        last_result_span: parameters.last_result.span,
        visible_result_span: visible.span,
    })
}

#[derive(Clone, Copy, Debug)]
struct FieldEnvelope {
    parameters: usize,
    visible_result: usize,
}

fn validate_field_envelope(
    document: &PreservingXmlDocument,
    field_begin: usize,
    limits: TableFormulaHwpxLimits,
) -> Result<FieldEnvelope, TableFormulaHwpxError> {
    let begin = element(document, field_begin)?;
    validate_attributes(
        begin,
        &[
            "id", "type", "name", "editable", "dirty", "zorder", "fieldid",
        ],
    )?;
    if required_attribute(begin, "type")? != "FORMULA"
        || !required_attribute(begin, "name")?.is_empty()
        || required_attribute(begin, "editable")? != "0"
        || required_attribute(begin, "dirty")? != "0"
        || required_attribute(begin, "zorder")? != "-1"
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let begin_id = required_positive_u64(begin, "id")?;
    let field_id = required_positive_u64(begin, "fieldid")?;

    let begin_ctrl = begin
        .parent()
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    if !has_paragraph_name(element(document, begin_ctrl)?, "ctrl")
        || child_indexes(document, begin_ctrl)? != [field_begin]
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let run = element(document, begin_ctrl)?
        .parent()
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    if !has_paragraph_name(element(document, run)?, "run") {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let run_children = child_indexes(document, run)?;
    if run_children.len() != 4
        || run_children[0] != begin_ctrl
        || !has_paragraph_name(element(document, run_children[1])?, "t")
        || !has_paragraph_name(element(document, run_children[2])?, "ctrl")
        || !has_paragraph_name(element(document, run_children[3])?, "t")
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    if !leaf_text(document, run_children[3], limits)?.is_empty() {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let end_children = child_indexes(document, run_children[2])?;
    if end_children.len() != 1
        || !has_paragraph_name(element(document, end_children[0])?, "fieldEnd")
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let end = element(document, end_children[0])?;
    validate_attributes(end, &["beginIDRef", "fieldid"])?;
    if required_positive_u64(end, "beginIDRef")? != begin_id
        || required_positive_u64(end, "fieldid")? != field_id
        || end.first_child().is_some()
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }

    let begin_children = child_indexes(document, field_begin)?;
    if begin_children.len() != 1
        || !has_paragraph_name(element(document, begin_children[0])?, "parameters")
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    Ok(FieldEnvelope {
        parameters: begin_children[0],
        visible_result: run_children[1],
    })
}

#[derive(Clone, Copy, Debug)]
struct NativeFieldParameters<'a> {
    command: LeafText<'a>,
    native_formula: LeafText<'a>,
    result_format: LeafText<'a>,
    last_result: LeafText<'a>,
}

fn read_field_parameters(
    document: &PreservingXmlDocument,
    parameters_index: usize,
    limits: TableFormulaHwpxLimits,
) -> Result<NativeFieldParameters<'_>, TableFormulaHwpxError> {
    let parameters = element(document, parameters_index)?;
    validate_attributes(parameters, &["cnt", "name"])?;
    if required_attribute(parameters, "cnt")? != "5"
        || !required_attribute(parameters, "name")?.is_empty()
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let params = child_indexes(document, parameters_index)?;
    if params.len() != 5 {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let prop = read_named_parameter(document, params[0], "integerParam", "Prop", limits)?;
    if prop.text != "8" {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let command = read_named_parameter(document, params[1], "stringParam", "Command", limits)?;
    let native_formula =
        read_named_parameter(document, params[2], "stringParam", "Formula", limits)?;
    let result_format =
        read_named_parameter(document, params[3], "stringParam", "ResultFormat", limits)?;
    let last_result =
        read_named_parameter(document, params[4], "stringParam", "LastResult", limits)?;
    Ok(NativeFieldParameters {
        command,
        native_formula,
        result_format,
        last_result,
    })
}

#[derive(Clone, Copy, Debug)]
struct LeafText<'a> {
    text: &'a str,
    span: XmlByteSpan,
}

fn read_named_parameter<'a>(
    document: &'a PreservingXmlDocument,
    index: usize,
    kind: &str,
    name: &str,
    limits: TableFormulaHwpxLimits,
) -> Result<LeafText<'a>, TableFormulaHwpxError> {
    let value = element(document, index)?;
    if !has_paragraph_name(value, kind) {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    validate_attributes(value, &["name"])?;
    if required_attribute(value, "name")? != name {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    leaf_text_with_span(document, index, limits)
}

fn left_prefix_ast(
    owner: CellCoordinate,
    formula_limits: FormulaLimits,
) -> Result<FormulaAst, TableFormulaHwpxError> {
    if owner.column == 0 {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    let relative = FormulaReferenceKind::Relative;
    Ok(FormulaAst::from_draft(
        FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: FormulaExpression::Function {
                function: FormulaFunction::Sum,
                arguments: vec![FormulaExpression::Range {
                    range: FormulaRange {
                        start: domain_ir::FormulaCellReference {
                            row: owner.row,
                            column: 0,
                            row_kind: relative,
                            column_kind: relative,
                        },
                        end: domain_ir::FormulaCellReference {
                            row: owner.row,
                            column: owner.column - 1,
                            row_kind: relative,
                            column_kind: relative,
                        },
                    },
                }],
            },
        },
        formula_limits,
    )?)
}

fn aggregate_ast(
    native_formula: &str,
    formula_limits: FormulaLimits,
) -> Result<FormulaAst, TableFormulaHwpxError> {
    let source = native_formula
        .strip_prefix('=')
        .ok_or(TableFormulaHwpxError::UnsupportedFormula)?;
    let ast = FormulaAst::parse(source, formula_limits)?;
    if ast.canonical_formula(formula_limits)? != source {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    let FormulaExpression::Function {
        function,
        arguments,
    } = ast.expression()
    else {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    };
    if !matches!(
        function,
        FormulaFunction::Sum | FormulaFunction::Average | FormulaFunction::Product
    ) || arguments.len() != 1
    {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    let FormulaExpression::Range { range } = &arguments[0] else {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    };
    if [
        range.start.row_kind,
        range.start.column_kind,
        range.end.row_kind,
        range.end.column_kind,
    ]
    .into_iter()
    .any(|kind| kind != FormulaReferenceKind::Relative)
    {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    Ok(ast)
}

fn canonical_native_ast(
    native_formula: &str,
    formula_limits: FormulaLimits,
) -> Result<FormulaAst, TableFormulaHwpxError> {
    let source = native_formula
        .strip_prefix('=')
        .ok_or(TableFormulaHwpxError::UnsupportedFormula)?;
    let ast = FormulaAst::parse(source, formula_limits)?;
    if ast.canonical_formula(formula_limits)? != source {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    Ok(ast)
}

fn canonical_native_formula(
    formula: &FormulaCell,
    formula_limits: FormulaLimits,
) -> Result<String, TableFormulaHwpxError> {
    if formula.number_format() != FormulaNumberFormat::General {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    let canonical = formula.ast().canonical_formula(formula_limits)?;
    let native = format!("={canonical}");
    if native
        .bytes()
        .any(|byte| matches!(byte, b'&' | b'<' | b'>' | b'\'' | b'"'))
        || canonical_native_ast(&native, formula_limits)? != *formula.ast()
    {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    Ok(native)
}

fn canonical_cache_text(
    cache: &FormulaCache,
    formula_limits: FormulaLimits,
) -> Result<String, TableFormulaHwpxError> {
    match cache {
        FormulaCache::Absent => Ok(String::new()),
        FormulaCache::Unverified {
            value: FormulaValue::Decimal { value },
        } => {
            let text = decimal_text(*value);
            if parse_canonical_decimal(&text, formula_limits)? != *value {
                return Err(TableFormulaHwpxError::UnsupportedCache);
            }
            Ok(text)
        }
        FormulaCache::Unverified { .. } => Err(TableFormulaHwpxError::UnsupportedCache),
    }
}

fn expression_has_absolute_axis(expression: &FormulaExpression) -> bool {
    match expression {
        FormulaExpression::Decimal { .. } => false,
        FormulaExpression::Cell { reference } => {
            reference.row_kind == FormulaReferenceKind::Absolute
                || reference.column_kind == FormulaReferenceKind::Absolute
        }
        FormulaExpression::Range { range } => {
            [range.start, range.end].into_iter().any(|reference| {
                reference.row_kind == FormulaReferenceKind::Absolute
                    || reference.column_kind == FormulaReferenceKind::Absolute
            })
        }
        FormulaExpression::Unary { operand, .. } => expression_has_absolute_axis(operand),
        FormulaExpression::Binary { left, right, .. } => {
            expression_has_absolute_axis(left) || expression_has_absolute_axis(right)
        }
        FormulaExpression::Function { arguments, .. } => {
            arguments.iter().any(expression_has_absolute_axis)
        }
    }
}

fn require_left_prefix(formula: &FormulaCell) -> Result<(), TableFormulaHwpxError> {
    let owner = formula.owner();
    let FormulaExpression::Function {
        function: FormulaFunction::Sum,
        arguments,
    } = formula.ast().expression()
    else {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    };
    if owner.column == 0 || arguments.len() != 1 {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    let FormulaExpression::Range { range } = &arguments[0] else {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    };
    let relative = FormulaReferenceKind::Relative;
    if range.start.row != owner.row
        || range.start.column != 0
        || range.start.row_kind != relative
        || range.start.column_kind != relative
        || range.end.row != owner.row
        || range.end.column != owner.column - 1
        || range.end.row_kind != relative
        || range.end.column_kind != relative
    {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    Ok(())
}

fn aggregate_native_formula(
    formula: &FormulaCell,
    formula_limits: FormulaLimits,
) -> Result<String, TableFormulaHwpxError> {
    if formula.number_format() != FormulaNumberFormat::General {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    let canonical = formula.ast().canonical_formula(formula_limits)?;
    let native = format!("={canonical}");
    if native
        .bytes()
        .any(|byte| matches!(byte, b'&' | b'<' | b'>' | b'\'' | b'"'))
        || aggregate_ast(&native, formula_limits)? != *formula.ast()
    {
        return Err(TableFormulaHwpxError::UnsupportedFormula);
    }
    Ok(native)
}

fn empty_cell_run(
    document: &PreservingXmlDocument,
    cell: usize,
    limits: TableFormulaHwpxLimits,
) -> Result<usize, TableFormulaHwpxError> {
    let sub_list = unique_named_child(document, &child_indexes(document, cell)?, "subList")?;
    let paragraphs = child_indexes(document, sub_list)?;
    if paragraphs.len() != 1 || !has_paragraph_name(element(document, paragraphs[0])?, "p") {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let runs = child_indexes(document, paragraphs[0])?;
    if runs.len() != 1 || !has_paragraph_name(element(document, runs[0])?, "run") {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let texts = child_indexes(document, runs[0])?;
    if texts.len() != 1
        || !has_paragraph_name(element(document, texts[0])?, "t")
        || !leaf_text(document, texts[0], limits)?.is_empty()
    {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    validate_attributes(element(document, texts[0])?, &[])?;
    Ok(runs[0])
}

fn reserve_field_ids(
    document: &PreservingXmlDocument,
) -> Result<(u64, u64), TableFormulaHwpxError> {
    let mut maximum = 0_u64;
    for value in document.elements() {
        if has_paragraph_name(value, "fieldBegin") {
            maximum = maximum.max(required_positive_u64(value, "id")?);
            maximum = maximum.max(required_positive_u64(value, "fieldid")?);
        } else if has_paragraph_name(value, "fieldEnd") {
            maximum = maximum.max(required_positive_u64(value, "beginIDRef")?);
            maximum = maximum.max(required_positive_u64(value, "fieldid")?);
        }
    }
    let begin_id = maximum
        .checked_add(1)
        .ok_or(TableFormulaHwpxError::InvalidNumber)?;
    let field_id = begin_id
        .checked_add(1)
        .ok_or(TableFormulaHwpxError::InvalidNumber)?;
    Ok((begin_id, field_id))
}

fn aggregate_field_xml(
    prefix: Option<&str>,
    begin_id: u64,
    field_id: u64,
    command: &str,
    formula: &str,
    result: &str,
) -> Vec<u8> {
    let qualified = |name: &str| prefix.map_or_else(|| name.to_owned(), |p| format!("{p}:{name}"));
    let ctrl = qualified("ctrl");
    let begin = qualified("fieldBegin");
    let parameters = qualified("parameters");
    let integer = qualified("integerParam");
    let string = qualified("stringParam");
    let text = qualified("t");
    let end = qualified("fieldEnd");
    format!(
        "<{ctrl}><{begin} id=\"{begin_id}\" type=\"FORMULA\" name=\"\" editable=\"0\" dirty=\"0\" zorder=\"-1\" fieldid=\"{field_id}\"><{parameters} cnt=\"5\" name=\"\"><{integer} name=\"Prop\">8</{integer}><{string} name=\"Command\">{command}</{string}><{string} name=\"Formula\">{formula}</{string}><{string} name=\"ResultFormat\">{NATIVE_GENERAL_FORMAT}</{string}><{string} name=\"LastResult\">{result}</{string}></{parameters}></{begin}></{ctrl}><{text}>{result}</{text}><{ctrl}><{end} beginIDRef=\"{begin_id}\" fieldid=\"{field_id}\"/></{ctrl}><{text}/>"
    )
    .into_bytes()
}

fn cache_decimal_text(cache: &FormulaCache) -> Result<String, TableFormulaHwpxError> {
    let FormulaCache::Unverified {
        value: FormulaValue::Decimal { value },
    } = cache
    else {
        return Err(TableFormulaHwpxError::UnsupportedCache);
    };
    Ok(decimal_text(*value))
}

fn parse_canonical_decimal(
    source: &str,
    formula_limits: FormulaLimits,
) -> Result<FormulaDecimal, TableFormulaHwpxError> {
    if source.is_empty() || !source.is_ascii() {
        return Err(TableFormulaHwpxError::InvalidText);
    }
    let (negative, magnitude) = source
        .strip_prefix('-')
        .map_or((false, source), |value| (true, value));
    if magnitude.is_empty() {
        return Err(TableFormulaHwpxError::InvalidText);
    }
    let ast = FormulaAst::parse(magnitude, formula_limits)?;
    if ast.canonical_formula(formula_limits)? != magnitude {
        return Err(TableFormulaHwpxError::InvalidText);
    }
    let FormulaExpression::Decimal { value } = ast.expression() else {
        return Err(TableFormulaHwpxError::InvalidText);
    };
    if !negative {
        return Ok(*value);
    }
    let coefficient = value
        .coefficient()
        .checked_neg()
        .filter(|value| *value != 0)
        .ok_or(TableFormulaHwpxError::InvalidText)?;
    Ok(FormulaDecimal::new(coefficient, value.scale()))
}

fn decimal_text(value: FormulaDecimal) -> String {
    let coefficient = value.coefficient();
    let scale = usize::from(value.scale());
    if scale == 0 {
        return coefficient.to_string();
    }
    let negative = coefficient < 0;
    let digits = coefficient.unsigned_abs().to_string();
    let mut output = String::new();
    if negative {
        output.push('-');
    }
    if digits.len() <= scale {
        output.push_str("0.");
        output.extend(std::iter::repeat_n('0', scale - digits.len()));
        output.push_str(&digits);
    } else {
        let split = digits.len() - scale;
        output.push_str(&digits[..split]);
        output.push('.');
        output.push_str(&digits[split..]);
    }
    output
}

#[derive(Debug)]
struct TableGridCells {
    rows: u32,
    columns: u32,
    cells: Vec<(usize, CellCoordinate)>,
}

fn read_cells(
    document: &PreservingXmlDocument,
    table: usize,
    limits: TableFormulaHwpxLimits,
    allow_merged_cells: bool,
) -> Result<TableGridCells, TableFormulaHwpxError> {
    let table_value = element(document, table)?;
    let rows = required_positive_u32(table_value, "rowCnt")?;
    let columns = required_positive_u32(table_value, "colCnt")?;
    let expected = usize::try_from(rows)
        .ok()
        .and_then(|value| value.checked_mul(usize::try_from(columns).ok()?))
        .ok_or(TableFormulaHwpxError::CellLimit)?;
    if expected > limits.0.cells {
        return Err(TableFormulaHwpxError::CellLimit);
    }
    let table_children = child_indexes(document, table)?;
    let row_indexes: Vec<_> = table_children
        .into_iter()
        .filter(|index| {
            element(document, *index).is_ok_and(|value| has_paragraph_name(value, "tr"))
        })
        .collect();
    if row_indexes.len() != usize::try_from(rows).map_err(|_| TableFormulaHwpxError::CellLimit)? {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(expected)
        .map_err(|_| TableFormulaHwpxError::AllocationFailed)?;
    let mut master_coordinates = BTreeSet::new();
    let mut covered_slots = BTreeSet::new();
    for row in row_indexes {
        for cell in child_indexes(document, row)? {
            if !has_paragraph_name(element(document, cell)?, "tc") {
                return Err(TableFormulaHwpxError::UnsupportedShape);
            }
            if cells.len() == limits.0.cells {
                return Err(TableFormulaHwpxError::CellLimit);
            }
            let children = child_indexes(document, cell)?;
            let address = unique_named_child(document, &children, "cellAddr")?;
            let span = unique_named_child(document, &children, "cellSpan")?;
            validate_attributes(element(document, address)?, &["colAddr", "rowAddr"])?;
            validate_attributes(element(document, span)?, &["colSpan", "rowSpan"])?;
            let column_span = required_positive_u32(element(document, span)?, "colSpan")?;
            let row_span = required_positive_u32(element(document, span)?, "rowSpan")?;
            if !allow_merged_cells && (column_span != 1 || row_span != 1) {
                return Err(TableFormulaHwpxError::UnsupportedShape);
            }
            let coordinate = CellCoordinate {
                row: required_u32(element(document, address)?, "rowAddr")?,
                column: required_u32(element(document, address)?, "colAddr")?,
            };
            if coordinate.row >= rows
                || coordinate.column >= columns
                || !master_coordinates.insert(coordinate)
            {
                return Err(TableFormulaHwpxError::UnsupportedShape);
            }
            let row_end = coordinate
                .row
                .checked_add(row_span)
                .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
            let column_end = coordinate
                .column
                .checked_add(column_span)
                .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
            if row_end > rows || column_end > columns {
                return Err(TableFormulaHwpxError::UnsupportedShape);
            }
            for row in coordinate.row..row_end {
                for column in coordinate.column..column_end {
                    if !covered_slots.insert(CellCoordinate { row, column }) {
                        return Err(TableFormulaHwpxError::UnsupportedShape);
                    }
                }
            }
            cells.push((cell, coordinate));
        }
    }
    if covered_slots.len() != expected {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    Ok(TableGridCells {
        rows,
        columns,
        cells,
    })
}

fn formula_fields(
    document: &PreservingXmlDocument,
    table: usize,
    limits: TableFormulaHwpxLimits,
) -> Result<Vec<usize>, TableFormulaHwpxError> {
    let mut formulas = Vec::new();
    for (index, value) in document.elements().iter().enumerate() {
        if !is_descendant(document, index, table)?
            || !has_paragraph_name(value, "fieldBegin")
            || nearest_ancestor_table(document, index)? != Some(table)
        {
            continue;
        }
        if required_attribute(value, "type")? != "FORMULA" {
            continue;
        }
        if formulas.len() == limits.0.formula_fields {
            return Err(TableFormulaHwpxError::FormulaFieldLimit);
        }
        formulas
            .try_reserve(1)
            .map_err(|_| TableFormulaHwpxError::AllocationFailed)?;
        formulas.push(index);
    }
    Ok(formulas)
}

fn nearest_ancestor_table(
    document: &PreservingXmlDocument,
    descendant: usize,
) -> Result<Option<usize>, TableFormulaHwpxError> {
    let mut current = element(document, descendant)?.parent();
    while let Some(index) = current {
        let value = element(document, index)?;
        if has_paragraph_name(value, "tbl") {
            return Ok(Some(index));
        }
        current = value.parent();
    }
    Ok(None)
}

fn owning_direct_cell(
    document: &PreservingXmlDocument,
    descendant: usize,
    table: usize,
) -> Result<usize, TableFormulaHwpxError> {
    let mut current = Some(descendant);
    while let Some(index) = current {
        let value = element(document, index)?;
        if has_paragraph_name(value, "tc") {
            let row = value
                .parent()
                .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
            if !has_paragraph_name(element(document, row)?, "tr")
                || element(document, row)?.parent() != Some(table)
            {
                return Err(TableFormulaHwpxError::UnsupportedShape);
            }
            return Ok(index);
        }
        if index == table {
            break;
        }
        current = value.parent();
    }
    Err(TableFormulaHwpxError::UnsupportedShape)
}

fn parse_document(
    bytes: &[u8],
    limits: TableFormulaHwpxLimits,
) -> Result<PreservingXmlDocument, TableFormulaHwpxError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(TableFormulaHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.0.elements {
        return Err(TableFormulaHwpxError::ElementLimit);
    }
    Ok(document)
}

fn validate_document_envelope(
    document: &PreservingXmlDocument,
) -> Result<(), TableFormulaHwpxError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(TableFormulaHwpxError::UnsupportedShape);
        }
    }
    Ok(())
}

fn validate_section_root(document: &PreservingXmlDocument) -> Result<(), TableFormulaHwpxError> {
    let root = element(document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(TableFormulaHwpxError::WrongRoot);
    }
    Ok(())
}

fn table_indexes(
    document: &PreservingXmlDocument,
    limits: TableFormulaHwpxLimits,
) -> Result<Vec<usize>, TableFormulaHwpxError> {
    let mut tables = Vec::new();
    for (index, value) in document.elements().iter().enumerate() {
        if has_paragraph_name(value, "tbl") {
            if tables.len() == limits.0.tables {
                return Err(TableFormulaHwpxError::TableLimit);
            }
            tables
                .try_reserve(1)
                .map_err(|_| TableFormulaHwpxError::AllocationFailed)?;
            tables.push(index);
        }
    }
    Ok(tables)
}

fn is_descendant(
    document: &PreservingXmlDocument,
    descendant: usize,
    ancestor: usize,
) -> Result<bool, TableFormulaHwpxError> {
    let mut current = element(document, descendant)?.parent();
    while let Some(index) = current {
        if index == ancestor {
            return Ok(true);
        }
        current = element(document, index)?.parent();
    }
    Ok(false)
}

fn leaf_text(
    document: &PreservingXmlDocument,
    index: usize,
    limits: TableFormulaHwpxLimits,
) -> Result<&str, TableFormulaHwpxError> {
    let value = element(document, index)?;
    if value.first_child().is_some() {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let Some(span) = value.content_span() else {
        return Ok("");
    };
    let text = document.source_text(span)?;
    validate_leaf_text(text, limits)?;
    Ok(text)
}

fn leaf_text_with_span(
    document: &PreservingXmlDocument,
    index: usize,
    limits: TableFormulaHwpxLimits,
) -> Result<LeafText<'_>, TableFormulaHwpxError> {
    let value = element(document, index)?;
    if value.first_child().is_some() {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    let span = value
        .content_span()
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    let text = document.source_text(span)?;
    validate_leaf_text(text, limits)?;
    Ok(LeafText { text, span })
}

fn validate_leaf_text(
    text: &str,
    limits: TableFormulaHwpxLimits,
) -> Result<(), TableFormulaHwpxError> {
    if text.len() > limits.0.text_bytes || !text.is_ascii() || text.contains('&') {
        return Err(TableFormulaHwpxError::InvalidText);
    }
    Ok(())
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, TableFormulaHwpxError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| TableFormulaHwpxError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn unique_named_child(
    document: &PreservingXmlDocument,
    children: &[usize],
    name: &str,
) -> Result<usize, TableFormulaHwpxError> {
    let mut matches = children.iter().copied().filter(|index| {
        element(document, *index).is_ok_and(|value| has_paragraph_name(value, name))
    });
    let value = matches
        .next()
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    if matches.next().is_some() {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    Ok(value)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, TableFormulaHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(TableFormulaHwpxError::UnsupportedShape)
}

fn has_paragraph_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), TableFormulaHwpxError> {
    let mut seen = BTreeSet::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(TableFormulaHwpxError::UnsupportedShape);
        }
    }
    Ok(())
}

fn unique_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, TableFormulaHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(TableFormulaHwpxError::UnsupportedShape)?;
    if matches.next().is_some() {
        return Err(TableFormulaHwpxError::UnsupportedShape);
    }
    Ok(value)
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, TableFormulaHwpxError> {
    Ok(unique_attribute(element, name)?.semantic_value())
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, TableFormulaHwpxError> {
    let value = required_attribute(element, name)?;
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(TableFormulaHwpxError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| TableFormulaHwpxError::InvalidNumber)
}

fn required_positive_u32(
    element: &XmlElementToken,
    name: &str,
) -> Result<u32, TableFormulaHwpxError> {
    let value = required_u32(element, name)?;
    if value == 0 {
        return Err(TableFormulaHwpxError::InvalidNumber);
    }
    Ok(value)
}

fn required_positive_u64(
    element: &XmlElementToken,
    name: &str,
) -> Result<u64, TableFormulaHwpxError> {
    let value = required_attribute(element, name)?;
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(TableFormulaHwpxError::InvalidNumber);
    }
    let parsed = value
        .parse()
        .map_err(|_| TableFormulaHwpxError::InvalidNumber)?;
    if parsed == 0 {
        return Err(TableFormulaHwpxError::InvalidNumber);
    }
    Ok(parsed)
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

impl ByteEdit {
    fn new(span: XmlByteSpan, replacement: Vec<u8>) -> Self {
        Self { span, replacement }
    }
}

fn apply_edits(
    source: &[u8],
    edits: &mut [ByteEdit],
    limits: TableFormulaHwpxLimits,
) -> Result<Vec<u8>, TableFormulaHwpxError> {
    edits.sort_unstable_by_key(|edit| edit.span.start());
    let mut prior_end = 0;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.span.start() < prior_end || edit.span.end() > source.len() {
            return Err(TableFormulaHwpxError::UnsupportedShape);
        }
        prior_end = edit.span.end();
        output_len = output_len
            .checked_sub(edit.span.len())
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(TableFormulaHwpxError::OutputLimit)?;
    }
    if output_len > limits.0.output_bytes {
        return Err(TableFormulaHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TableFormulaHwpxError::AllocationFailed)?;
    let mut cursor = 0;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.span.start()]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.span.end();
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(TableFormulaHwpxError::OutputLimit);
    }
    Ok(output)
}

fn digest_excluding(
    source: &[u8],
    spans: &[XmlByteSpan],
    profile_id: &str,
) -> Result<[u8; 32], TableFormulaHwpxError> {
    let mut sorted = spans.to_vec();
    sorted.sort_unstable_by_key(|span| span.start());
    let mut digest = Sha256::new();
    digest.update(profile_id.as_bytes());
    digest.update((sorted.len() as u64).to_be_bytes());
    let mut cursor = 0;
    for (ordinal, span) in sorted.iter().enumerate() {
        if span.start() < cursor || span.end() > source.len() {
            return Err(TableFormulaHwpxError::UnsupportedShape);
        }
        digest.update(&source[cursor..span.start()]);
        digest.update((ordinal as u64).to_be_bytes());
        cursor = span.end();
    }
    digest.update(&source[cursor..]);
    Ok(digest.finalize().into())
}
