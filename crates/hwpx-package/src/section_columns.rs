use std::collections::BTreeSet;
use std::fmt::Write as _;

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken, XmlTokenKind,
};

pub const COLUMN_PROFILE_ID: &str = "hwpx-agent.section-columns/1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SectionColumnLimitConfig {
    pub input_bytes: usize,
    pub elements: usize,
    pub output_bytes: usize,
    pub sections: usize,
    pub spans_per_section: usize,
    pub columns_per_span: usize,
    pub max_hwpunit: u32,
    pub min_column_width: u32,
    pub control_id_bytes: usize,
}

impl Default for SectionColumnLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 4 * 1024 * 1024,
            elements: 131_072,
            output_bytes: 4 * 1024 * 1024,
            sections: 1_024,
            spans_per_section: 1_024,
            columns_per_span: 255,
            max_hwpunit: 566_930,
            min_column_width: 284,
            control_id_bytes: 64,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct SectionColumnLimits(SectionColumnLimitConfig);

impl SectionColumnLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 262_144;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_SECTIONS: usize = 4_096;
    pub const HARD_MAX_SPANS_PER_SECTION: usize = 4_096;
    pub const HARD_MAX_COLUMNS_PER_SPAN: usize = 255;
    pub const HARD_MAX_HWPUNIT: u32 = 5_669_292;
    pub const HARD_MAX_CONTROL_ID_BYTES: usize = 256;

    /// Creates finite section/column limits.
    ///
    /// # Errors
    ///
    /// Rejects zero limits, values above hard ceilings, or a minimum width above the unit ceiling.
    pub fn new(config: SectionColumnLimitConfig) -> Result<Self, SectionColumnError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.sections == 0
            || config.sections > Self::HARD_MAX_SECTIONS
            || config.spans_per_section == 0
            || config.spans_per_section > Self::HARD_MAX_SPANS_PER_SECTION
            || config.columns_per_span == 0
            || config.columns_per_span > Self::HARD_MAX_COLUMNS_PER_SPAN
            || config.max_hwpunit == 0
            || config.max_hwpunit > Self::HARD_MAX_HWPUNIT
            || config.min_column_width == 0
            || config.min_column_width > config.max_hwpunit
            || config.control_id_bytes == 0
            || config.control_id_bytes > Self::HARD_MAX_CONTROL_ID_BYTES
        {
            return Err(SectionColumnError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> SectionColumnLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ColumnType {
    Newspaper,
    BalancedNewspaper,
    Parallel,
}

impl ColumnType {
    fn parse(value: &str) -> Result<Self, SectionColumnError> {
        match value {
            "NEWSPAPER" => Ok(Self::Newspaper),
            "BALANCED_NEWSPAPER" => Ok(Self::BalancedNewspaper),
            "PARALLEL" => Ok(Self::Parallel),
            _ => Err(SectionColumnError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Newspaper => "NEWSPAPER",
            Self::BalancedNewspaper => "BALANCED_NEWSPAPER",
            Self::Parallel => "PARALLEL",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ColumnLayout {
    Left,
    Right,
    Mirror,
}

impl ColumnLayout {
    fn parse(value: &str) -> Result<Self, SectionColumnError> {
        match value {
            "LEFT" => Ok(Self::Left),
            "RIGHT" => Ok(Self::Right),
            "MIRROR" => Ok(Self::Mirror),
            _ => Err(SectionColumnError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Left => "LEFT",
            Self::Right => "RIGHT",
            Self::Mirror => "MIRROR",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ColumnLineType {
    None,
    Solid,
    Dot,
    Dash,
    DashDot,
    DashDotDot,
    LongDash,
    Circle,
    DoubleSlim,
    SlimThick,
    ThickSlim,
    SlimThickSlim,
    Wave,
    DoubleWave,
    Thick3d,
    ThickReverse3d,
    ThreeD,
    Reverse3d,
}

impl ColumnLineType {
    fn parse(value: &str) -> Result<Self, SectionColumnError> {
        match value {
            "NONE" => Ok(Self::None),
            "SOLID" => Ok(Self::Solid),
            "DOT" => Ok(Self::Dot),
            "DASH" => Ok(Self::Dash),
            "DASH_DOT" => Ok(Self::DashDot),
            "DASH_DOT_DOT" => Ok(Self::DashDotDot),
            "LONG_DASH" => Ok(Self::LongDash),
            "CIRCLE" => Ok(Self::Circle),
            "DOUBLE_SLIM" => Ok(Self::DoubleSlim),
            "SLIM_THICK" => Ok(Self::SlimThick),
            "THICK_SLIM" => Ok(Self::ThickSlim),
            "SLIM_THICK_SLIM" => Ok(Self::SlimThickSlim),
            "WAVE" => Ok(Self::Wave),
            "DOUBLEWAVE" => Ok(Self::DoubleWave),
            "THICK3D" => Ok(Self::Thick3d),
            "THICKREV3D" => Ok(Self::ThickReverse3d),
            "3D" => Ok(Self::ThreeD),
            "REV3D" => Ok(Self::Reverse3d),
            _ => Err(SectionColumnError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::Solid => "SOLID",
            Self::Dot => "DOT",
            Self::Dash => "DASH",
            Self::DashDot => "DASH_DOT",
            Self::DashDotDot => "DASH_DOT_DOT",
            Self::LongDash => "LONG_DASH",
            Self::Circle => "CIRCLE",
            Self::DoubleSlim => "DOUBLE_SLIM",
            Self::SlimThick => "SLIM_THICK",
            Self::ThickSlim => "THICK_SLIM",
            Self::SlimThickSlim => "SLIM_THICK_SLIM",
            Self::Wave => "WAVE",
            Self::DoubleWave => "DOUBLEWAVE",
            Self::Thick3d => "THICK3D",
            Self::ThickReverse3d => "THICKREV3D",
            Self::ThreeD => "3D",
            Self::Reverse3d => "REV3D",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ColumnLineWidth {
    Mm0_1,
    Mm0_12,
    Mm0_15,
    Mm0_2,
    Mm0_25,
    Mm0_3,
    Mm0_4,
    Mm0_5,
    Mm0_6,
    Mm0_7,
    Mm1_0,
    Mm1_5,
    Mm2_0,
    Mm3_0,
    Mm4_0,
    Mm5_0,
}

impl ColumnLineWidth {
    fn parse(value: &str) -> Result<Self, SectionColumnError> {
        match value {
            "0.1 mm" => Ok(Self::Mm0_1),
            "0.12 mm" => Ok(Self::Mm0_12),
            "0.15 mm" => Ok(Self::Mm0_15),
            "0.2 mm" => Ok(Self::Mm0_2),
            "0.25 mm" => Ok(Self::Mm0_25),
            "0.3 mm" => Ok(Self::Mm0_3),
            "0.4 mm" => Ok(Self::Mm0_4),
            "0.5 mm" => Ok(Self::Mm0_5),
            "0.6 mm" => Ok(Self::Mm0_6),
            "0.7 mm" => Ok(Self::Mm0_7),
            "1.0 mm" => Ok(Self::Mm1_0),
            "1.5 mm" => Ok(Self::Mm1_5),
            "2.0 mm" => Ok(Self::Mm2_0),
            "3.0 mm" => Ok(Self::Mm3_0),
            "4.0 mm" => Ok(Self::Mm4_0),
            "5.0 mm" => Ok(Self::Mm5_0),
            _ => Err(SectionColumnError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Mm0_1 => "0.1 mm",
            Self::Mm0_12 => "0.12 mm",
            Self::Mm0_15 => "0.15 mm",
            Self::Mm0_2 => "0.2 mm",
            Self::Mm0_25 => "0.25 mm",
            Self::Mm0_3 => "0.3 mm",
            Self::Mm0_4 => "0.4 mm",
            Self::Mm0_5 => "0.5 mm",
            Self::Mm0_6 => "0.6 mm",
            Self::Mm0_7 => "0.7 mm",
            Self::Mm1_0 => "1.0 mm",
            Self::Mm1_5 => "1.5 mm",
            Self::Mm2_0 => "2.0 mm",
            Self::Mm3_0 => "3.0 mm",
            Self::Mm4_0 => "4.0 mm",
            Self::Mm5_0 => "5.0 mm",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ColumnSeparator {
    pub line_type: ColumnLineType,
    pub width: ColumnLineWidth,
    pub color: u32,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ColumnSize {
    pub width: u32,
    pub gap: u32,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ColumnSizing {
    Equal { count: u16, gap: u32 },
    Custom(Vec<ColumnSize>),
}

impl ColumnSizing {
    #[must_use]
    pub fn column_count(&self) -> usize {
        match self {
            Self::Equal { count, .. } => usize::from(*count),
            Self::Custom(columns) => columns.len(),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ColumnDefinition {
    pub control_id: String,
    pub column_type: ColumnType,
    pub layout: ColumnLayout,
    pub sizing: ColumnSizing,
    pub separator: Option<ColumnSeparator>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ColumnMetrics {
    pub body_width: u32,
    pub column_count: u16,
    pub total_gap: u32,
    pub total_column_width: u32,
    pub minimum_column_width: u32,
    pub equal_width_remainder: u32,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SectionColumns {
    pub spans: Vec<ColumnDefinition>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SectionBoundary {
    pub before_section_index: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SectionColumnSequence {
    pub sections: Vec<SectionColumns>,
    pub boundaries: Vec<SectionBoundary>,
}

impl SectionColumnSequence {
    #[must_use]
    pub fn section_break_count(&self) -> usize {
        self.boundaries.len()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SectionColumnLoweringReceipt {
    pub profile_id: &'static str,
    pub sha256: [u8; 32],
    pub output_bytes: usize,
    pub metrics: ColumnMetrics,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SectionColumnPatchReceipt {
    pub profile_id: &'static str,
    pub source_sha256: [u8; 32],
    pub output_sha256: [u8; 32],
    pub output_bytes: usize,
    pub span_ordinal: usize,
    pub replaced_start: usize,
    pub replaced_end: usize,
    pub metrics: ColumnMetrics,
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum SectionColumnError {
    #[error("section/column limits are invalid")]
    InvalidLimit,
    #[error("section/column input exceeds its finite limit")]
    InputLimit,
    #[error("section/column element count exceeds its finite limit")]
    ElementLimit,
    #[error("section count exceeds its finite limit")]
    SectionLimit,
    #[error("column span count exceeds its finite limit")]
    SpanLimit,
    #[error("column count exceeds its finite limit")]
    ColumnLimit,
    #[error("section/column XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("section/column root is not in the current profile")]
    WrongRoot,
    #[error("section/column element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("section/column numeric value is invalid")]
    InvalidNumber,
    #[error("section/column boolean value is invalid")]
    InvalidBoolean,
    #[error("section/column enum value is invalid")]
    InvalidEnum,
    #[error("column control identity is invalid")]
    InvalidId,
    #[error("column separator color is invalid")]
    InvalidColor,
    #[error("column layout does not fit the body width")]
    LayoutOverflow,
    #[error("custom column sizes are not a closed exact layout")]
    CustomShape,
    #[error("selected column span does not exist")]
    SpanNotFound,
    #[error("section/column output exceeds its finite limit")]
    OutputLimit,
    #[error("section/column arithmetic overflowed")]
    ArithmeticOverflow,
    #[error("section/column allocation failed")]
    AllocationFailed,
    #[error("section/column semantic readback differs")]
    ReadbackMismatch,
}

impl SectionColumnError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "section_columns_invalid_limit",
            Self::InputLimit => "section_columns_input_limit",
            Self::ElementLimit => "section_columns_element_limit",
            Self::SectionLimit => "section_columns_section_limit",
            Self::SpanLimit => "section_columns_span_limit",
            Self::ColumnLimit => "section_columns_column_limit",
            Self::Preserving(_) => "section_columns_preserving_xml",
            Self::WrongRoot => "section_columns_wrong_root",
            Self::UnsupportedShape => "section_columns_unsupported_shape",
            Self::InvalidNumber => "section_columns_invalid_number",
            Self::InvalidBoolean => "section_columns_invalid_boolean",
            Self::InvalidEnum => "section_columns_invalid_enum",
            Self::InvalidId => "section_columns_invalid_id",
            Self::InvalidColor => "section_columns_invalid_color",
            Self::LayoutOverflow => "section_columns_layout_overflow",
            Self::CustomShape => "section_columns_custom_shape",
            Self::SpanNotFound => "section_columns_span_not_found",
            Self::OutputLimit => "section_columns_output_limit",
            Self::ArithmeticOverflow => "section_columns_arithmetic_overflow",
            Self::AllocationFailed => "section_columns_allocation_failed",
            Self::ReadbackMismatch => "section_columns_readback_mismatch",
        }
    }
}

impl ColumnDefinition {
    /// Calculates a checked column layout against an already validated printable body width.
    ///
    /// # Errors
    ///
    /// Rejects invalid identities, finite-limit violations, undersized columns, overflow, and
    /// custom layouts whose widths and following gaps do not consume the body exactly.
    pub fn metrics(
        &self,
        body_width: u32,
        limits: SectionColumnLimits,
    ) -> Result<ColumnMetrics, SectionColumnError> {
        validate_definition(self, body_width, limits)
    }
}

#[derive(Debug)]
pub struct SectionColumnReader;

impl SectionColumnReader {
    /// Reads one standalone current-profile `colPr`.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, unbounded, or impossible definitions.
    pub fn read(
        bytes: &[u8],
        body_width: u32,
        limits: SectionColumnLimits,
    ) -> Result<ColumnDefinition, SectionColumnError> {
        let document = parse_document(bytes, limits)?;
        let root = element(&document, document.root_element())?;
        if !has_name(root, PARAGRAPH_NS, "colPr") {
            return Err(SectionColumnError::WrongRoot);
        }
        let definition = read_definition(&document, document.root_element(), limits)?;
        validate_definition(&definition, body_width, limits)?;
        Ok(definition)
    }

    /// Reads every ordered `colPr` span from exactly one HWPX section part.
    ///
    /// # Errors
    ///
    /// Requires one section root, exactly one `secPr`, at least one bounded `ctrl/colPr`, and a
    /// valid layout for the supplied printable body width.
    pub fn read_section(
        bytes: &[u8],
        body_width: u32,
        limits: SectionColumnLimits,
    ) -> Result<SectionColumns, SectionColumnError> {
        let (document, indexes) = parse_section(bytes, limits)?;
        let mut spans = Vec::new();
        spans
            .try_reserve_exact(indexes.len())
            .map_err(|_| SectionColumnError::AllocationFailed)?;
        for index in indexes {
            let definition = read_definition(&document, index, limits)?;
            validate_definition(&definition, body_width, limits)?;
            spans.push(definition);
        }
        Ok(SectionColumns { spans })
    }

    /// Reads an ordered sequence of section parts. Every boundary between adjacent inputs is a
    /// typed section break; page-side start policy belongs to P05-08 rather than being guessed.
    ///
    /// # Errors
    ///
    /// Rejects an empty or oversized sequence and propagates any section failure atomically.
    pub fn read_sequence(
        sections: &[(&[u8], u32)],
        limits: SectionColumnLimits,
    ) -> Result<SectionColumnSequence, SectionColumnError> {
        if sections.is_empty() || sections.len() > limits.config().sections {
            return Err(SectionColumnError::SectionLimit);
        }
        let mut parsed = Vec::new();
        parsed
            .try_reserve_exact(sections.len())
            .map_err(|_| SectionColumnError::AllocationFailed)?;
        for (bytes, body_width) in sections {
            parsed.push(Self::read_section(bytes, *body_width, limits)?);
        }
        let boundary_count = parsed.len().saturating_sub(1);
        let mut boundaries = Vec::new();
        boundaries
            .try_reserve_exact(boundary_count)
            .map_err(|_| SectionColumnError::AllocationFailed)?;
        for before_section_index in 1..parsed.len() {
            boundaries.push(SectionBoundary {
                before_section_index,
            });
        }
        Ok(SectionColumnSequence {
            sections: parsed,
            boundaries,
        })
    }
}

#[derive(Debug)]
pub struct SectionColumnLowerer;

impl SectionColumnLowerer {
    /// Lowers one deterministic standalone `colPr` and re-lifts it for semantic equality.
    ///
    /// # Errors
    ///
    /// Rejects invalid/unbounded definitions, impossible layouts, and output/readback drift.
    pub fn lower_with_receipt(
        definition: &ColumnDefinition,
        body_width: u32,
        limits: SectionColumnLimits,
    ) -> Result<(Vec<u8>, SectionColumnLoweringReceipt), SectionColumnError> {
        let metrics = validate_definition(definition, body_width, limits)?;
        let bytes = lower_element(definition, true, limits.config().output_bytes)?;
        if SectionColumnReader::read(&bytes, body_width, limits)? != *definition {
            return Err(SectionColumnError::ReadbackMismatch);
        }
        let receipt = SectionColumnLoweringReceipt {
            profile_id: COLUMN_PROFILE_ID,
            sha256: Sha256::digest(&bytes).into(),
            output_bytes: bytes.len(),
            metrics,
        };
        Ok((bytes, receipt))
    }

    /// Lowers one deterministic standalone `colPr`.
    ///
    /// # Errors
    ///
    /// Rejects invalid/unbounded definitions, impossible layouts, and output/readback drift.
    pub fn lower(
        definition: &ColumnDefinition,
        body_width: u32,
        limits: SectionColumnLimits,
    ) -> Result<Vec<u8>, SectionColumnError> {
        Self::lower_with_receipt(definition, body_width, limits).map(|(bytes, _)| bytes)
    }

    /// Replaces only the selected ordered `colPr` span in one section and verifies every span.
    ///
    /// # Errors
    ///
    /// Rejects malformed sections, missing ordinals, limits, impossible layouts, or any semantic
    /// drift outside the selected span.
    pub fn replace_in_section(
        section: &[u8],
        span_ordinal: usize,
        definition: &ColumnDefinition,
        body_width: u32,
        limits: SectionColumnLimits,
    ) -> Result<(Vec<u8>, SectionColumnPatchReceipt), SectionColumnError> {
        let metrics = validate_definition(definition, body_width, limits)?;
        let original = SectionColumnReader::read_section(section, body_width, limits)?;
        if span_ordinal >= original.spans.len() {
            return Err(SectionColumnError::SpanNotFound);
        }
        let (document, indexes) = parse_section(section, limits)?;
        let index = *indexes
            .get(span_ordinal)
            .ok_or(SectionColumnError::SpanNotFound)?;
        let span = element(&document, index)?
            .outer_span()
            .ok_or(SectionColumnError::UnsupportedShape)?;
        let replacement = lower_element(definition, false, limits.config().output_bytes)?;
        let output_len = section
            .len()
            .checked_sub(span.len())
            .and_then(|value| value.checked_add(replacement.len()))
            .ok_or(SectionColumnError::OutputLimit)?;
        if output_len > limits.config().output_bytes {
            return Err(SectionColumnError::OutputLimit);
        }
        let mut output = Vec::new();
        output
            .try_reserve_exact(output_len)
            .map_err(|_| SectionColumnError::AllocationFailed)?;
        output.extend_from_slice(&section[..span.start()]);
        output.extend_from_slice(&replacement);
        output.extend_from_slice(&section[span.end()..]);
        let readback = SectionColumnReader::read_section(&output, body_width, limits)?;
        if readback.spans.len() != original.spans.len()
            || readback.spans.get(span_ordinal) != Some(definition)
            || readback.spans.iter().enumerate().any(|(index, value)| {
                index != span_ordinal && Some(value) != original.spans.get(index)
            })
        {
            return Err(SectionColumnError::ReadbackMismatch);
        }
        let receipt = SectionColumnPatchReceipt {
            profile_id: COLUMN_PROFILE_ID,
            source_sha256: Sha256::digest(section).into(),
            output_sha256: Sha256::digest(&output).into(),
            output_bytes: output.len(),
            span_ordinal,
            replaced_start: span.start(),
            replaced_end: span.end(),
            metrics,
        };
        Ok((output, receipt))
    }
}

fn validate_definition(
    definition: &ColumnDefinition,
    body_width: u32,
    limits: SectionColumnLimits,
) -> Result<ColumnMetrics, SectionColumnError> {
    validate_control_id(&definition.control_id, limits)?;
    if body_width == 0 || body_width > limits.config().max_hwpunit {
        return Err(SectionColumnError::LayoutOverflow);
    }
    if definition
        .separator
        .is_some_and(|separator| separator.color > 0x00ff_ffff)
    {
        return Err(SectionColumnError::InvalidColor);
    }
    match &definition.sizing {
        ColumnSizing::Equal { count, gap } => {
            let count_u16 = *count;
            let count = usize::from(count_u16);
            if count == 0 || count > limits.config().columns_per_span {
                return Err(SectionColumnError::ColumnLimit);
            }
            if *gap > limits.config().max_hwpunit || (count == 1 && *gap != 0) {
                return Err(SectionColumnError::LayoutOverflow);
            }
            let gap_count = u32::try_from(count.saturating_sub(1))
                .map_err(|_| SectionColumnError::ArithmeticOverflow)?;
            let total_gap = gap
                .checked_mul(gap_count)
                .ok_or(SectionColumnError::ArithmeticOverflow)?;
            let total_column_width = body_width
                .checked_sub(total_gap)
                .ok_or(SectionColumnError::LayoutOverflow)?;
            let count_u32 = u32::from(count_u16);
            let minimum_column_width = total_column_width / count_u32;
            if minimum_column_width < limits.config().min_column_width {
                return Err(SectionColumnError::LayoutOverflow);
            }
            Ok(ColumnMetrics {
                body_width,
                column_count: count_u16,
                total_gap,
                total_column_width,
                minimum_column_width,
                equal_width_remainder: total_column_width % count_u32,
            })
        }
        ColumnSizing::Custom(columns) => {
            if columns.is_empty() || columns.len() > limits.config().columns_per_span {
                return Err(SectionColumnError::ColumnLimit);
            }
            if columns.last().is_some_and(|column| column.gap != 0) {
                return Err(SectionColumnError::CustomShape);
            }
            let mut total_gap = 0_u32;
            let mut total_column_width = 0_u32;
            let mut minimum_column_width = u32::MAX;
            for column in columns {
                if column.width < limits.config().min_column_width
                    || column.width > limits.config().max_hwpunit
                    || column.gap > limits.config().max_hwpunit
                {
                    return Err(SectionColumnError::LayoutOverflow);
                }
                total_column_width = total_column_width
                    .checked_add(column.width)
                    .ok_or(SectionColumnError::ArithmeticOverflow)?;
                total_gap = total_gap
                    .checked_add(column.gap)
                    .ok_or(SectionColumnError::ArithmeticOverflow)?;
                minimum_column_width = minimum_column_width.min(column.width);
            }
            if total_column_width
                .checked_add(total_gap)
                .ok_or(SectionColumnError::ArithmeticOverflow)?
                != body_width
            {
                return Err(SectionColumnError::CustomShape);
            }
            Ok(ColumnMetrics {
                body_width,
                column_count: u16::try_from(columns.len())
                    .map_err(|_| SectionColumnError::ColumnLimit)?,
                total_gap,
                total_column_width,
                minimum_column_width,
                equal_width_remainder: 0,
            })
        }
    }
}

fn validate_control_id(value: &str, limits: SectionColumnLimits) -> Result<(), SectionColumnError> {
    if value.len() > limits.config().control_id_bytes
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
    {
        return Err(SectionColumnError::InvalidId);
    }
    Ok(())
}

fn parse_document(
    bytes: &[u8],
    limits: SectionColumnLimits,
) -> Result<PreservingXmlDocument, SectionColumnError> {
    if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
        return Err(SectionColumnError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.config().elements {
        return Err(SectionColumnError::ElementLimit);
    }
    validate_document_envelope(&document)?;
    Ok(document)
}

fn parse_section(
    bytes: &[u8],
    limits: SectionColumnLimits,
) -> Result<(PreservingXmlDocument, Vec<usize>), SectionColumnError> {
    let document = parse_document(bytes, limits)?;
    let root = element(&document, document.root_element())?;
    if !has_name(root, SECTION_NS, "sec") {
        return Err(SectionColumnError::WrongRoot);
    }
    let mut section_properties = None;
    let mut columns = Vec::new();
    for (index, value) in document.elements().iter().enumerate() {
        match value.name().local_name() {
            "secPr" => {
                if !has_name(value, PARAGRAPH_NS, "secPr")
                    || section_properties.replace(index).is_some()
                    || !has_parent_chain(
                        &document,
                        index,
                        &[
                            (PARAGRAPH_NS, "run"),
                            (PARAGRAPH_NS, "p"),
                            (SECTION_NS, "sec"),
                        ],
                    )?
                {
                    return Err(SectionColumnError::UnsupportedShape);
                }
            }
            "colPr" => {
                if !has_name(value, PARAGRAPH_NS, "colPr") {
                    return Err(SectionColumnError::UnsupportedShape);
                }
                let parent = value.parent().ok_or(SectionColumnError::UnsupportedShape)?;
                if !has_name(element(&document, parent)?, PARAGRAPH_NS, "ctrl")
                    || !has_parent_chain(
                        &document,
                        index,
                        &[
                            (PARAGRAPH_NS, "ctrl"),
                            (PARAGRAPH_NS, "run"),
                            (PARAGRAPH_NS, "p"),
                            (SECTION_NS, "sec"),
                        ],
                    )?
                {
                    return Err(SectionColumnError::UnsupportedShape);
                }
                if columns.len() >= limits.config().spans_per_section {
                    return Err(SectionColumnError::SpanLimit);
                }
                columns
                    .try_reserve(1)
                    .map_err(|_| SectionColumnError::AllocationFailed)?;
                columns.push(index);
            }
            _ => {}
        }
    }
    if section_properties.is_none() || columns.is_empty() {
        return Err(SectionColumnError::UnsupportedShape);
    }
    Ok((document, columns))
}

fn read_definition(
    document: &PreservingXmlDocument,
    index: usize,
    limits: SectionColumnLimits,
) -> Result<ColumnDefinition, SectionColumnError> {
    let column = element(document, index)?;
    if !has_name(column, PARAGRAPH_NS, "colPr") {
        return Err(SectionColumnError::WrongRoot);
    }
    validate_attributes(
        column,
        &["id", "type", "layout", "colCount", "sameSz", "sameGap"],
    )?;
    require_only_whitespace_content(document, index)?;
    let control_id = required_attribute(column, "id")?.to_owned();
    validate_control_id(&control_id, limits)?;
    let column_type = ColumnType::parse(required_attribute(column, "type")?)?;
    let layout = ColumnLayout::parse(required_attribute(column, "layout")?)?;
    let count = required_u16(column, "colCount")?;
    if count == 0 || usize::from(count) > limits.config().columns_per_span {
        return Err(SectionColumnError::ColumnLimit);
    }
    let same_size = required_bool01(column, "sameSz")?;
    let same_gap = required_u32(column, "sameGap")?;
    let children = child_indexes(document, index)?;
    let mut separator = None;
    let mut sizes = Vec::new();
    sizes
        .try_reserve_exact(usize::from(count))
        .map_err(|_| SectionColumnError::AllocationFailed)?;
    let mut sizes_started = false;
    for child_index in children {
        let child = element(document, child_index)?;
        if has_name(child, PARAGRAPH_NS, "colLine") {
            if separator.is_some() || sizes_started {
                return Err(SectionColumnError::UnsupportedShape);
            }
            separator = Some(read_separator(child)?);
        } else if has_name(child, PARAGRAPH_NS, "colSz") {
            sizes_started = true;
            if sizes.len() >= limits.config().columns_per_span {
                return Err(SectionColumnError::ColumnLimit);
            }
            sizes.push(read_size(child)?);
        } else {
            return Err(SectionColumnError::UnsupportedShape);
        }
    }
    let sizing = if same_size {
        if !sizes.is_empty() {
            return Err(SectionColumnError::CustomShape);
        }
        ColumnSizing::Equal {
            count,
            gap: same_gap,
        }
    } else {
        if same_gap != 0 || sizes.len() != usize::from(count) {
            return Err(SectionColumnError::CustomShape);
        }
        ColumnSizing::Custom(sizes)
    };
    Ok(ColumnDefinition {
        control_id,
        column_type,
        layout,
        sizing,
        separator,
    })
}

fn read_separator(element: &XmlElementToken) -> Result<ColumnSeparator, SectionColumnError> {
    validate_attributes(element, &["type", "width", "color"])?;
    if !element.is_empty() || element.first_child().is_some() {
        return Err(SectionColumnError::UnsupportedShape);
    }
    Ok(ColumnSeparator {
        line_type: ColumnLineType::parse(required_attribute(element, "type")?)?,
        width: ColumnLineWidth::parse(required_attribute(element, "width")?)?,
        color: parse_color(required_attribute(element, "color")?)?,
    })
}

fn read_size(element: &XmlElementToken) -> Result<ColumnSize, SectionColumnError> {
    validate_attributes(element, &["width", "gap"])?;
    if !element.is_empty() || element.first_child().is_some() {
        return Err(SectionColumnError::UnsupportedShape);
    }
    Ok(ColumnSize {
        width: required_u32(element, "width")?,
        gap: required_u32(element, "gap")?,
    })
}

fn lower_element(
    definition: &ColumnDefinition,
    include_namespace: bool,
    output_limit: usize,
) -> Result<Vec<u8>, SectionColumnError> {
    let namespace = if include_namespace {
        " xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\""
    } else {
        ""
    };
    let (count, same_size, same_gap) = match &definition.sizing {
        ColumnSizing::Equal { count, gap } => (*count, 1, *gap),
        ColumnSizing::Custom(columns) => (
            u16::try_from(columns.len()).map_err(|_| SectionColumnError::ColumnLimit)?,
            0,
            0,
        ),
    };
    let mut xml = format!(
        "<hp:colPr{namespace} id=\"{}\" type=\"{}\" layout=\"{}\" colCount=\"{count}\" sameSz=\"{same_size}\" sameGap=\"{same_gap}\"",
        definition.control_id,
        definition.column_type.as_str(),
        definition.layout.as_str(),
    );
    if definition.separator.is_none() && matches!(definition.sizing, ColumnSizing::Equal { .. }) {
        xml.push_str("/>");
    } else {
        xml.push('>');
        if let Some(separator) = definition.separator {
            write!(
                &mut xml,
                "<hp:colLine type=\"{}\" width=\"{}\" color=\"#{:06X}\"/>",
                separator.line_type.as_str(),
                separator.width.as_str(),
                separator.color,
            )
            .map_err(|_| SectionColumnError::AllocationFailed)?;
        }
        if let ColumnSizing::Custom(columns) = &definition.sizing {
            for column in columns {
                write!(
                    &mut xml,
                    "<hp:colSz width=\"{}\" gap=\"{}\"/>",
                    column.width, column.gap
                )
                .map_err(|_| SectionColumnError::AllocationFailed)?;
            }
        }
        xml.push_str("</hp:colPr>");
    }
    if xml.len() > output_limit {
        return Err(SectionColumnError::OutputLimit);
    }
    Ok(xml.into_bytes())
}

fn parse_color(value: &str) -> Result<u32, SectionColumnError> {
    if value.len() != 7
        || !value.starts_with('#')
        || !value[1..].bytes().all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(SectionColumnError::InvalidColor);
    }
    u32::from_str_radix(&value[1..], 16).map_err(|_| SectionColumnError::InvalidColor)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, SectionColumnError> {
    document
        .elements()
        .get(index)
        .ok_or(SectionColumnError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, namespace: &str, local_name: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local_name
}

fn has_parent_chain(
    document: &PreservingXmlDocument,
    index: usize,
    expected: &[(&str, &str)],
) -> Result<bool, SectionColumnError> {
    let mut current = Some(index);
    for (namespace, local_name) in expected {
        current = current.and_then(|value| document.elements().get(value)?.parent());
        let Some(parent) = current else {
            return Ok(false);
        };
        if !has_name(element(document, parent)?, namespace, local_name) {
            return Ok(false);
        }
    }
    Ok(true)
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, SectionColumnError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| SectionColumnError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), SectionColumnError> {
    let mut seen = BTreeSet::<&str>::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(SectionColumnError::UnsupportedShape);
        }
    }
    Ok(())
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, SectionColumnError> {
    element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == name
        })
        .map(XmlAttributeToken::semantic_value)
        .ok_or(SectionColumnError::UnsupportedShape)
}

fn required_u16(element: &XmlElementToken, name: &str) -> Result<u16, SectionColumnError> {
    required_decimal(element, name)?
        .parse()
        .map_err(|_| SectionColumnError::InvalidNumber)
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, SectionColumnError> {
    required_decimal(element, name)?
        .parse()
        .map_err(|_| SectionColumnError::InvalidNumber)
}

fn required_decimal<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, SectionColumnError> {
    let value = required_attribute(element, name)?;
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(SectionColumnError::InvalidNumber);
    }
    Ok(value)
}

fn required_bool01(element: &XmlElementToken, name: &str) -> Result<bool, SectionColumnError> {
    match required_attribute(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(SectionColumnError::InvalidBoolean),
    }
}

fn require_only_whitespace_content(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), SectionColumnError> {
    let value = element(document, index)?;
    if value.is_empty() {
        return Ok(());
    }
    let end = value
        .end_token()
        .ok_or(SectionColumnError::UnsupportedShape)?;
    for token in &document.tokens()[(value.start_token() + 1)..end] {
        if token.element_index() != Some(index) {
            continue;
        }
        match token.kind() {
            XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment => {
                return Err(SectionColumnError::UnsupportedShape);
            }
            XmlTokenKind::Whitespace if !document.source_text(token.span())?.trim().is_empty() => {
                return Err(SectionColumnError::UnsupportedShape);
            }
            _ => {}
        }
    }
    Ok(())
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), SectionColumnError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(SectionColumnError::UnsupportedShape);
        }
    }
    Ok(())
}
