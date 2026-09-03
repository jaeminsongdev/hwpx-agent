use std::collections::{BTreeMap, BTreeSet};

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::character_style::{CharacterStyleCatalog, Color, LineType2};
use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken, XmlTokenKind,
};
use crate::text_flow::TextFlow;

pub const PARAGRAPH_STYLE_PROFILE_ID: &str = "hwpx-agent.paragraph-style/1";

const HEAD_NS: &str = "http://www.hancom.co.kr/hwpml/2011/head";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const CORE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/core";
const HWPUNIT_CHAR_NS: &str = "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar";
const METATAG_NS: &str = "http://www.hancom.co.kr/hwpml/2021/metatag";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ParagraphStyleLimitConfig {
    pub input_bytes: usize,
    pub elements: usize,
    pub styles: usize,
    pub border_fills: usize,
    pub references: usize,
}

impl Default for ParagraphStyleLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 2 * 1024 * 1024,
            elements: 32_768,
            styles: 16_384,
            border_fills: 16_384,
            references: 16_384,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ParagraphStyleLimits(ParagraphStyleLimitConfig);

impl ParagraphStyleLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 65_536;
    pub const HARD_MAX_STYLES: usize = 32_768;
    pub const HARD_MAX_BORDER_FILLS: usize = 32_768;
    pub const HARD_MAX_REFERENCES: usize = 32_768;

    /// Creates a finite current-Hangul-2020 paragraph-style limit set.
    ///
    /// # Errors
    ///
    /// Rejects zero limits and limits above their hard ceilings.
    pub fn new(config: ParagraphStyleLimitConfig) -> Result<Self, ParagraphStyleError> {
        let values = [
            (config.input_bytes, Self::HARD_MAX_INPUT_BYTES),
            (config.elements, Self::HARD_MAX_ELEMENTS),
            (config.styles, Self::HARD_MAX_STYLES),
            (config.border_fills, Self::HARD_MAX_BORDER_FILLS),
            (config.references, Self::HARD_MAX_REFERENCES),
        ];
        if values
            .into_iter()
            .any(|(value, ceiling)| value == 0 || value > ceiling)
        {
            return Err(ParagraphStyleError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ParagraphStyleLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum HorizontalAlignment {
    Justify,
    Left,
    Right,
    Center,
    Distribute,
    DistributeSpace,
}

impl HorizontalAlignment {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "JUSTIFY" => Ok(Self::Justify),
            "LEFT" => Ok(Self::Left),
            "RIGHT" => Ok(Self::Right),
            "CENTER" => Ok(Self::Center),
            "DISTRIBUTE" => Ok(Self::Distribute),
            "DISTRIBUTE_SPACE" => Ok(Self::DistributeSpace),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Justify => "JUSTIFY",
            Self::Left => "LEFT",
            Self::Right => "RIGHT",
            Self::Center => "CENTER",
            Self::Distribute => "DISTRIBUTE",
            Self::DistributeSpace => "DISTRIBUTE_SPACE",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum VerticalAlignment {
    Baseline,
    Top,
    Center,
    Bottom,
}

impl VerticalAlignment {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "BASELINE" => Ok(Self::Baseline),
            "TOP" => Ok(Self::Top),
            "CENTER" => Ok(Self::Center),
            "BOTTOM" => Ok(Self::Bottom),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Baseline => "BASELINE",
            Self::Top => "TOP",
            Self::Center => "CENTER",
            Self::Bottom => "BOTTOM",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum TextDirection {
    LeftToRight,
    RightToLeft,
}

impl TextDirection {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "LTR" => Ok(Self::LeftToRight),
            "RTL" => Ok(Self::RightToLeft),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::LeftToRight => "LTR",
            Self::RightToLeft => "RTL",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum HeadingType {
    None,
    Outline,
    Number,
    Bullet,
}

impl HeadingType {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "NONE" => Ok(Self::None),
            "OUTLINE" => Ok(Self::Outline),
            "NUMBER" => Ok(Self::Number),
            "BULLET" => Ok(Self::Bullet),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::Outline => "OUTLINE",
            Self::Number => "NUMBER",
            Self::Bullet => "BULLET",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct Heading {
    pub heading_type: HeadingType,
    pub id_ref: u32,
    pub level: u8,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum CompatibleHeading {
    Direct(Heading),
    MetaTag { current: Heading, fallback: Heading },
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum WordBreak {
    KeepWord,
    BreakWord,
    Hyphenation,
}

impl WordBreak {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "KEEP_WORD" => Ok(Self::KeepWord),
            "BREAK_WORD" => Ok(Self::BreakWord),
            "HYPHENATION" => Ok(Self::Hyphenation),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::KeepWord => "KEEP_WORD",
            Self::BreakWord => "BREAK_WORD",
            Self::Hyphenation => "HYPHENATION",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum LineWrap {
    Break,
    Squeeze,
    Keep,
}

impl LineWrap {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "BREAK" => Ok(Self::Break),
            "SQUEEZE" => Ok(Self::Squeeze),
            "KEEP" => Ok(Self::Keep),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Break => "BREAK",
            Self::Squeeze => "SQUEEZE",
            Self::Keep => "KEEP",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
#[allow(clippy::struct_excessive_bools)]
pub struct BreakSettings {
    pub latin_word: WordBreak,
    pub non_latin_word: WordBreak,
    pub widow_orphan: bool,
    pub keep_with_next: bool,
    pub keep_lines: bool,
    pub page_break_before: bool,
    pub line_wrap: LineWrap,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct AutoSpacing {
    pub e_asian_english: bool,
    pub e_asian_number: bool,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum MeasurementUnit {
    Character,
    HwpUnit,
}

impl MeasurementUnit {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "CHAR" => Ok(Self::Character),
            "HWPUNIT" => Ok(Self::HwpUnit),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Character => "CHAR",
            Self::HwpUnit => "HWPUNIT",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct HwpValue {
    pub value: i32,
    pub unit: MeasurementUnit,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct Margin {
    pub intent: HwpValue,
    pub left: HwpValue,
    pub right: HwpValue,
    pub previous: HwpValue,
    pub next: HwpValue,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum LineSpacingType {
    Percent,
    Fixed,
    BetweenLines,
    AtLeast,
}

impl LineSpacingType {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "PERCENT" => Ok(Self::Percent),
            "FIXED" => Ok(Self::Fixed),
            "BETWEEN_LINES" => Ok(Self::BetweenLines),
            "AT_LEAST" => Ok(Self::AtLeast),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Percent => "PERCENT",
            Self::Fixed => "FIXED",
            Self::BetweenLines => "BETWEEN_LINES",
            Self::AtLeast => "AT_LEAST",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct LineSpacing {
    pub spacing_type: LineSpacingType,
    pub value: i32,
    pub unit: MeasurementUnit,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct ParagraphLayout {
    pub margin: Margin,
    pub line_spacing: LineSpacing,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct CompatibleParagraphLayout {
    pub current: ParagraphLayout,
    pub fallback: ParagraphLayout,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct ParagraphBorder {
    pub border_fill_id_ref: u32,
    pub offset_left: i32,
    pub offset_right: i32,
    pub offset_top: i32,
    pub offset_bottom: i32,
    pub connect: bool,
    pub ignore_margin: bool,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum SlashType {
    None,
    Center,
    CenterBelow,
    CenterAbove,
    All,
}

impl SlashType {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "NONE" => Ok(Self::None),
            "CENTER" => Ok(Self::Center),
            "CENTER_BELOW" => Ok(Self::CenterBelow),
            "CENTER_ABOVE" => Ok(Self::CenterAbove),
            "ALL" => Ok(Self::All),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::Center => "CENTER",
            Self::CenterBelow => "CENTER_BELOW",
            Self::CenterAbove => "CENTER_ABOVE",
            Self::All => "ALL",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct Slash {
    pub slash_type: SlashType,
    pub crooked: bool,
    pub is_counter: bool,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum CenterLine {
    None,
    Vertical,
    Horizontal,
    Cross,
}

impl CenterLine {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "NONE" => Ok(Self::None),
            "VERTICAL" => Ok(Self::Vertical),
            "HORIZONTAL" => Ok(Self::Horizontal),
            "CROSS" => Ok(Self::Cross),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::Vertical => "VERTICAL",
            Self::Horizontal => "HORIZONTAL",
            Self::Cross => "CROSS",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum BorderWidth {
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

impl BorderWidth {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
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
            _ => Err(ParagraphStyleError::InvalidEnum),
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

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct BorderLine {
    pub line_type: LineType2,
    pub width: BorderWidth,
    pub color: Color,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum HatchStyle {
    Horizontal,
    Vertical,
    BackSlash,
    Slash,
    Cross,
    CrossDiagonal,
}

impl HatchStyle {
    fn parse(value: &str) -> Result<Self, ParagraphStyleError> {
        match value {
            "HORIZONTAL" => Ok(Self::Horizontal),
            "VERTICAL" => Ok(Self::Vertical),
            "BACK_SLASH" => Ok(Self::BackSlash),
            "SLASH" => Ok(Self::Slash),
            "CROSS" => Ok(Self::Cross),
            "CROSS_DIAGONAL" => Ok(Self::CrossDiagonal),
            _ => Err(ParagraphStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Horizontal => "HORIZONTAL",
            Self::Vertical => "VERTICAL",
            Self::BackSlash => "BACK_SLASH",
            Self::Slash => "SLASH",
            Self::Cross => "CROSS",
            Self::CrossDiagonal => "CROSS_DIAGONAL",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct WindowBrush {
    pub face_color: Color,
    pub hatch_color: Option<Color>,
    pub hatch_style: Option<HatchStyle>,
    pub alpha: u8,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct FillBrush {
    pub window: WindowBrush,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct BorderFill {
    pub id: u32,
    pub three_d: bool,
    pub shadow: bool,
    pub center_line: CenterLine,
    pub break_cell_separate_line: bool,
    pub slash: Slash,
    pub back_slash: Slash,
    pub left: BorderLine,
    pub right: BorderLine,
    pub top: BorderLine,
    pub bottom: BorderLine,
    pub diagonal: BorderLine,
    pub fill_brush: Option<FillBrush>,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
#[allow(clippy::struct_excessive_bools)]
pub struct ParagraphStyle {
    pub id: u32,
    pub tab_property_id_ref: u32,
    pub condense: u8,
    pub font_line_height: bool,
    pub snap_to_grid: bool,
    pub suppress_line_numbers: bool,
    pub checked: bool,
    pub text_direction: Option<TextDirection>,
    pub horizontal_alignment: HorizontalAlignment,
    pub vertical_alignment: VerticalAlignment,
    pub heading: CompatibleHeading,
    pub break_settings: BreakSettings,
    pub auto_spacing: AutoSpacing,
    pub layout: CompatibleParagraphLayout,
    pub border: ParagraphBorder,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ParagraphReferenceDomains {
    pub tab_property_ids: Vec<u32>,
    pub numbering_ids: Vec<u32>,
    pub bullet_ids: Vec<u32>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ParagraphStyleCatalog {
    pub border_fills: Vec<BorderFill>,
    pub references: ParagraphReferenceDomains,
    pub styles: Vec<ParagraphStyle>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DeduplicatedParagraphStyles {
    pub styles: Vec<ParagraphStyle>,
    pub old_to_new: Vec<u32>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ParagraphStyleLoweringReceipt {
    pub profile_id: &'static str,
    pub sha256: [u8; 32],
    pub output_bytes: usize,
    pub border_fill_count: usize,
    pub style_count: usize,
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum ParagraphStyleError {
    #[error("paragraph-style limits are invalid")]
    InvalidLimit,
    #[error("paragraph-style input exceeds its finite limit")]
    InputLimit,
    #[error("paragraph-style XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("paragraph-style root is not the current Hangul 2020 head profile")]
    WrongRoot,
    #[error("paragraph-style element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("paragraph-style count does not match content")]
    CountMismatch,
    #[error("paragraph-style identifier is invalid")]
    InvalidId,
    #[error("paragraph-style reference is dangling")]
    DanglingReference,
    #[error("paragraph-style numeric attribute is invalid")]
    InvalidNumber,
    #[error("paragraph-style boolean attribute is invalid")]
    InvalidBoolean,
    #[error("paragraph-style enum attribute is invalid")]
    InvalidEnum,
    #[error("paragraph-style color is invalid")]
    InvalidColor,
    #[error("paragraph-style value is outside the current-2020 range")]
    OutOfRange,
    #[error("paragraph-style count exceeds its finite limit")]
    StyleLimit,
    #[error("paragraph-style border/fill count exceeds its finite limit")]
    BorderFillLimit,
    #[error("paragraph-style reference domain exceeds its finite limit")]
    ReferenceLimit,
    #[error("paragraph-style element count exceeds its finite limit")]
    ElementLimit,
    #[error("paragraph-style output exceeds its finite limit")]
    OutputLimit,
    #[error("paragraph-style allocation failed")]
    AllocationFailed,
    #[error("paragraph-style lowered readback differs")]
    ReadbackMismatch,
}

impl ParagraphStyleError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "paragraph_style_invalid_limit",
            Self::InputLimit => "paragraph_style_input_limit",
            Self::Preserving(_) => "paragraph_style_preserving_xml",
            Self::WrongRoot => "paragraph_style_wrong_root",
            Self::UnsupportedShape => "paragraph_style_unsupported_shape",
            Self::CountMismatch => "paragraph_style_count_mismatch",
            Self::InvalidId => "paragraph_style_invalid_id",
            Self::DanglingReference => "paragraph_style_dangling_reference",
            Self::InvalidNumber => "paragraph_style_invalid_number",
            Self::InvalidBoolean => "paragraph_style_invalid_boolean",
            Self::InvalidEnum => "paragraph_style_invalid_enum",
            Self::InvalidColor => "paragraph_style_invalid_color",
            Self::OutOfRange => "paragraph_style_out_of_range",
            Self::StyleLimit => "paragraph_style_style_limit",
            Self::BorderFillLimit => "paragraph_style_border_fill_limit",
            Self::ReferenceLimit => "paragraph_style_reference_limit",
            Self::ElementLimit => "paragraph_style_element_limit",
            Self::OutputLimit => "paragraph_style_output_limit",
            Self::AllocationFailed => "paragraph_style_allocation_failed",
            Self::ReadbackMismatch => "paragraph_style_readback_mismatch",
        }
    }
}

#[derive(Debug)]
pub struct ParagraphStyleCatalogReader;

impl ParagraphStyleCatalogReader {
    /// Lifts the paragraph-style slice and its external reference domains from a full header.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, unbounded, non-dense, out-of-range, or dangling content.
    pub fn read(
        bytes: &[u8],
        limits: ParagraphStyleLimits,
    ) -> Result<ParagraphStyleCatalog, ParagraphStyleError> {
        let document = parse_document(bytes, limits)?;
        let ref_list = find_ref_list(&document)?;
        let references = read_reference_domains(&document, ref_list, limits)?;
        read_catalog(&document, ref_list, references, limits)
    }

    /// Lifts a deterministic P05-03 fragment using explicitly supplied P05-04/05 domains.
    ///
    /// # Errors
    ///
    /// Applies the same validation as [`Self::read`] and rejects malformed reference domains.
    pub fn read_with_reference_domains(
        bytes: &[u8],
        references: &ParagraphReferenceDomains,
        limits: ParagraphStyleLimits,
    ) -> Result<ParagraphStyleCatalog, ParagraphStyleError> {
        validate_reference_domains(references, limits)?;
        let document = parse_document(bytes, limits)?;
        let ref_list = find_ref_list(&document)?;
        read_catalog(
            &document,
            ref_list,
            copy_reference_domains(references)?,
            limits,
        )
    }
}

#[derive(Debug)]
pub struct ParagraphStyleCatalogWriter;

impl ParagraphStyleCatalogWriter {
    /// Lowers a typed catalog to deterministic P05-03 refList XML and reparses it.
    ///
    /// # Errors
    ///
    /// Rejects invalid public values, limit violations, dangling references, or readback drift.
    pub fn lower(
        catalog: &ParagraphStyleCatalog,
        limits: ParagraphStyleLimits,
    ) -> Result<Vec<u8>, ParagraphStyleError> {
        let (bytes, _) = Self::lower_with_receipt(catalog, limits)?;
        Ok(bytes)
    }

    /// Lowers a catalog and returns a deterministic integrity receipt.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`].
    pub fn lower_with_receipt(
        catalog: &ParagraphStyleCatalog,
        limits: ParagraphStyleLimits,
    ) -> Result<(Vec<u8>, ParagraphStyleLoweringReceipt), ParagraphStyleError> {
        validate_catalog(catalog, limits)?;
        let mut output = BoundedXml::new(limits.config().input_bytes)?;
        output.push("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")?;
        output.push("<hh:refList xmlns:hh=\"")?;
        output.push(HEAD_NS)?;
        output.push("\" xmlns:hp=\"")?;
        output.push(PARAGRAPH_NS)?;
        output.push("\" xmlns:hc=\"")?;
        output.push(CORE_NS)?;
        output.push("\">")?;
        write_border_fills(&mut output, &catalog.border_fills)?;
        write_paragraph_styles(&mut output, &catalog.styles)?;
        output.push("</hh:refList>")?;
        let bytes = output.finish();
        let readback = ParagraphStyleCatalogReader::read_with_reference_domains(
            &bytes,
            &catalog.references,
            limits,
        )?;
        if readback != *catalog {
            return Err(ParagraphStyleError::ReadbackMismatch);
        }
        let receipt = ParagraphStyleLoweringReceipt {
            profile_id: PARAGRAPH_STYLE_PROFILE_ID,
            sha256: <[u8; 32]>::from(Sha256::digest(&bytes)),
            output_bytes: bytes.len(),
            border_fill_count: catalog.border_fills.len(),
            style_count: catalog.styles.len(),
        };
        Ok((bytes, receipt))
    }
}

impl ParagraphStyleCatalog {
    /// Validates P05-02 character-style border references against this catalog.
    ///
    /// # Errors
    ///
    /// Returns `DanglingReference` if any typed character style names an absent border/fill.
    pub fn validate_character_style_references(
        &self,
        characters: &CharacterStyleCatalog,
    ) -> Result<(), ParagraphStyleError> {
        let ids = self
            .border_fills
            .iter()
            .map(|border| border.id)
            .collect::<BTreeSet<_>>();
        if characters.styles.iter().any(|style| {
            style
                .border_fill_id_ref
                .is_some_and(|reference| !ids.contains(&reference))
        }) {
            return Err(ParagraphStyleError::DanglingReference);
        }
        Ok(())
    }

    /// Deduplicates semantic paragraph styles in deterministic first-occurrence order.
    ///
    /// # Errors
    ///
    /// Rejects an invalid catalog or allocation/identifier overflow.
    pub fn deduplicate(
        &self,
        limits: ParagraphStyleLimits,
    ) -> Result<DeduplicatedParagraphStyles, ParagraphStyleError> {
        validate_catalog(self, limits)?;
        let mut seen = BTreeMap::<ParagraphStyle, u32>::new();
        let mut styles = Vec::new();
        let mut old_to_new = Vec::new();
        styles
            .try_reserve(self.styles.len())
            .map_err(|_| ParagraphStyleError::AllocationFailed)?;
        old_to_new
            .try_reserve(self.styles.len())
            .map_err(|_| ParagraphStyleError::AllocationFailed)?;
        for style in &self.styles {
            let mut semantic = style.clone();
            semantic.id = 0;
            let new_id = if let Some(existing) = seen.get(&semantic) {
                *existing
            } else {
                let allocated =
                    u32::try_from(styles.len()).map_err(|_| ParagraphStyleError::InvalidId)?;
                let mut canonical = style.clone();
                canonical.id = allocated;
                styles.push(canonical);
                seen.insert(semantic, allocated);
                allocated
            };
            old_to_new.push(new_id);
        }
        Ok(DeduplicatedParagraphStyles { styles, old_to_new })
    }
}

impl DeduplicatedParagraphStyles {
    /// Atomically rewrites only the typed P05-01 `paraPrIDRef` field.
    ///
    /// # Errors
    ///
    /// Rejects malformed mappings or references outside the original style domain.
    pub fn rewrite_text_flow(&self, flow: &mut TextFlow) -> Result<(), ParagraphStyleError> {
        self.validate_mapping()?;
        let Some(reference) = flow.paragraph.paragraph_property_id_ref else {
            return Ok(());
        };
        let index =
            usize::try_from(reference).map_err(|_| ParagraphStyleError::DanglingReference)?;
        let mapped = self
            .old_to_new
            .get(index)
            .copied()
            .ok_or(ParagraphStyleError::DanglingReference)?;
        flow.paragraph.paragraph_property_id_ref = Some(mapped);
        Ok(())
    }

    fn validate_mapping(&self) -> Result<(), ParagraphStyleError> {
        if self.styles.is_empty() || self.old_to_new.is_empty() {
            return Err(ParagraphStyleError::InvalidId);
        }
        for (position, style) in self.styles.iter().enumerate() {
            let expected = u32::try_from(position).map_err(|_| ParagraphStyleError::InvalidId)?;
            if style.id != expected {
                return Err(ParagraphStyleError::InvalidId);
            }
        }
        let count = u32::try_from(self.styles.len()).map_err(|_| ParagraphStyleError::InvalidId)?;
        if self.old_to_new.len() < self.styles.len()
            || self.old_to_new.iter().any(|mapped| *mapped >= count)
            || (0..count).any(|id| !self.old_to_new.contains(&id))
        {
            return Err(ParagraphStyleError::InvalidId);
        }
        Ok(())
    }
}

fn parse_document(
    bytes: &[u8],
    limits: ParagraphStyleLimits,
) -> Result<PreservingXmlDocument, ParagraphStyleError> {
    if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
        return Err(ParagraphStyleError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.config().elements {
        return Err(ParagraphStyleError::ElementLimit);
    }
    validate_document_envelope(&document)?;
    Ok(document)
}

fn find_ref_list(document: &PreservingXmlDocument) -> Result<usize, ParagraphStyleError> {
    let root_index = document.root_element();
    let root = element(document, root_index)?;
    if has_name(root, HEAD_NS, "refList") {
        Ok(root_index)
    } else if has_name(root, HEAD_NS, "head") {
        exactly_one_child(document, root_index, HEAD_NS, "refList")
    } else {
        Err(ParagraphStyleError::WrongRoot)
    }
}

fn read_catalog(
    document: &PreservingXmlDocument,
    ref_list: usize,
    references: ParagraphReferenceDomains,
    limits: ParagraphStyleLimits,
) -> Result<ParagraphStyleCatalog, ParagraphStyleError> {
    let border_index = exactly_one_child(document, ref_list, HEAD_NS, "borderFills")?;
    let para_index = exactly_one_child(document, ref_list, HEAD_NS, "paraProperties")?;
    let border_fills = read_border_fills(document, border_index, limits)?;
    let styles = read_paragraph_styles(document, para_index, limits)?;
    let catalog = ParagraphStyleCatalog {
        border_fills,
        references,
        styles,
    };
    validate_catalog(&catalog, limits)?;
    Ok(catalog)
}

fn read_reference_domains(
    document: &PreservingXmlDocument,
    ref_list: usize,
    limits: ParagraphStyleLimits,
) -> Result<ParagraphReferenceDomains, ParagraphStyleError> {
    let tabs = exactly_one_child(document, ref_list, HEAD_NS, "tabProperties")?;
    let numberings = exactly_one_child(document, ref_list, HEAD_NS, "numberings")?;
    let bullets = optional_one_child(document, ref_list, HEAD_NS, "bullets")?;
    let references = ParagraphReferenceDomains {
        tab_property_ids: read_id_domain(document, tabs, "tabPr", 0, limits)?,
        numbering_ids: read_id_domain(document, numberings, "numbering", 1, limits)?,
        bullet_ids: if let Some(bullets) = bullets {
            read_id_domain(document, bullets, "bullet", 1, limits)?
        } else {
            Vec::new()
        },
    };
    validate_reference_domains(&references, limits)?;
    Ok(references)
}

fn read_id_domain(
    document: &PreservingXmlDocument,
    index: usize,
    child_name: &str,
    first_id: u32,
    limits: ParagraphStyleLimits,
) -> Result<Vec<u32>, ParagraphStyleError> {
    let container = element(document, index)?;
    validate_attributes(container, &["itemCnt"])?;
    let declared = required_usize(container, "itemCnt")?;
    if declared > limits.config().references {
        return Err(ParagraphStyleError::ReferenceLimit);
    }
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != declared {
        return Err(ParagraphStyleError::CountMismatch);
    }
    let mut ids = Vec::new();
    ids.try_reserve_exact(declared)
        .map_err(|_| ParagraphStyleError::AllocationFailed)?;
    for (position, child_index) in children.into_iter().enumerate() {
        let child = element(document, child_index)?;
        require_name(child, HEAD_NS, child_name)?;
        let id = required_u32(child, "id")?;
        let expected = first_id
            .checked_add(u32::try_from(position).map_err(|_| ParagraphStyleError::InvalidId)?)
            .ok_or(ParagraphStyleError::InvalidId)?;
        if id != expected {
            return Err(ParagraphStyleError::InvalidId);
        }
        ids.push(id);
    }
    Ok(ids)
}

fn read_border_fills(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ParagraphStyleLimits,
) -> Result<Vec<BorderFill>, ParagraphStyleError> {
    let container = element(document, index)?;
    validate_attributes(container, &["itemCnt"])?;
    let declared = required_usize(container, "itemCnt")?;
    if declared == 0 || declared > limits.config().border_fills {
        return Err(ParagraphStyleError::BorderFillLimit);
    }
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != declared {
        return Err(ParagraphStyleError::CountMismatch);
    }
    let mut result = Vec::new();
    result
        .try_reserve_exact(declared)
        .map_err(|_| ParagraphStyleError::AllocationFailed)?;
    for (position, child_index) in children.into_iter().enumerate() {
        let value = read_border_fill(document, child_index)?;
        let expected = u32::try_from(position)
            .map_err(|_| ParagraphStyleError::InvalidId)?
            .checked_add(1)
            .ok_or(ParagraphStyleError::InvalidId)?;
        if value.id != expected {
            return Err(ParagraphStyleError::InvalidId);
        }
        result.push(value);
    }
    Ok(result)
}

fn read_border_fill(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<BorderFill, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "borderFill")?;
    validate_attributes(
        value,
        &[
            "id",
            "threeD",
            "shadow",
            "centerLine",
            "breakCellSeparateLine",
        ],
    )?;
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if !(children.len() == 7 || children.len() == 8) {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    let slash = read_slash(document, children[0], "slash")?;
    let back_slash = read_slash(document, children[1], "backSlash")?;
    let left = read_border_line(document, children[2], "leftBorder")?;
    let right = read_border_line(document, children[3], "rightBorder")?;
    let top = read_border_line(document, children[4], "topBorder")?;
    let bottom = read_border_line(document, children[5], "bottomBorder")?;
    let diagonal = read_border_line(document, children[6], "diagonal")?;
    let fill_brush = if children.len() == 8 {
        Some(read_fill_brush(document, children[7])?)
    } else {
        None
    };
    Ok(BorderFill {
        id: required_u32(value, "id")?,
        three_d: required_bool(value, "threeD")?,
        shadow: required_bool(value, "shadow")?,
        center_line: CenterLine::parse(required_attribute(value, "centerLine")?)?,
        break_cell_separate_line: required_bool(value, "breakCellSeparateLine")?,
        slash,
        back_slash,
        left,
        right,
        top,
        bottom,
        diagonal,
        fill_brush,
    })
}

fn read_slash(
    document: &PreservingXmlDocument,
    index: usize,
    name: &str,
) -> Result<Slash, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, name)?;
    validate_attributes(value, &["type", "Crooked", "isCounter"])?;
    require_no_children(document, index)?;
    Ok(Slash {
        slash_type: SlashType::parse(required_attribute(value, "type")?)?,
        crooked: required_bool(value, "Crooked")?,
        is_counter: required_bool(value, "isCounter")?,
    })
}

fn read_border_line(
    document: &PreservingXmlDocument,
    index: usize,
    name: &str,
) -> Result<BorderLine, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, name)?;
    validate_attributes(value, &["type", "width", "color"])?;
    require_no_children(document, index)?;
    let color = parse_color(required_attribute(value, "color")?)?;
    if color == Color::None {
        return Err(ParagraphStyleError::InvalidColor);
    }
    Ok(BorderLine {
        line_type: parse_line_type(required_attribute(value, "type")?)?,
        width: BorderWidth::parse(required_attribute(value, "width")?)?,
        color,
    })
}

fn read_fill_brush(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<FillBrush, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, CORE_NS, "fillBrush")?;
    validate_attributes(value, &[])?;
    require_only_whitespace_content(document, index)?;
    let window_index = exactly_one_child(document, index, CORE_NS, "winBrush")?;
    if child_indexes(document, index)?.len() != 1 {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    let window = element(document, window_index)?;
    validate_attributes(window, &["faceColor", "hatchColor", "hatchStyle", "alpha"])?;
    require_no_children(document, window_index)?;
    Ok(FillBrush {
        window: WindowBrush {
            face_color: parse_color(required_attribute(window, "faceColor")?)?,
            hatch_color: optional_attribute(window, "hatchColor")
                .map(parse_color)
                .transpose()?,
            hatch_style: optional_attribute(window, "hatchStyle")
                .map(HatchStyle::parse)
                .transpose()?,
            alpha: required_u8(window, "alpha")?,
        },
    })
}

fn read_paragraph_styles(
    document: &PreservingXmlDocument,
    index: usize,
    limits: ParagraphStyleLimits,
) -> Result<Vec<ParagraphStyle>, ParagraphStyleError> {
    let container = element(document, index)?;
    validate_attributes(container, &["itemCnt"])?;
    let declared = required_usize(container, "itemCnt")?;
    if declared == 0 || declared > limits.config().styles {
        return Err(ParagraphStyleError::StyleLimit);
    }
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != declared {
        return Err(ParagraphStyleError::CountMismatch);
    }
    let mut result = Vec::new();
    result
        .try_reserve_exact(declared)
        .map_err(|_| ParagraphStyleError::AllocationFailed)?;
    for (position, child_index) in children.into_iter().enumerate() {
        let style = read_paragraph_style(document, child_index)?;
        let expected = u32::try_from(position).map_err(|_| ParagraphStyleError::InvalidId)?;
        if style.id != expected {
            return Err(ParagraphStyleError::InvalidId);
        }
        result.push(style);
    }
    Ok(result)
}

fn read_paragraph_style(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<ParagraphStyle, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "paraPr")?;
    validate_attributes(
        value,
        &[
            "id",
            "tabPrIDRef",
            "condense",
            "fontLineHeight",
            "snapToGrid",
            "suppressLineNumbers",
            "checked",
            "textDir",
        ],
    )?;
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != 6 {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    let align = element(document, children[0])?;
    require_name(align, HEAD_NS, "align")?;
    validate_attributes(align, &["horizontal", "vertical"])?;
    require_no_children(document, children[0])?;
    let heading = if has_name(element(document, children[1])?, HEAD_NS, "heading") {
        CompatibleHeading::Direct(read_heading(document, children[1])?)
    } else {
        read_heading_switch(document, children[1])?
    };
    let break_settings = read_break_settings(document, children[2])?;
    let auto_spacing = read_auto_spacing(document, children[3])?;
    let layout = read_layout_switch(document, children[4])?;
    let border = read_paragraph_border(document, children[5])?;
    Ok(ParagraphStyle {
        id: required_u32(value, "id")?,
        tab_property_id_ref: required_u32(value, "tabPrIDRef")?,
        condense: required_u8(value, "condense")?,
        font_line_height: required_bool(value, "fontLineHeight")?,
        snap_to_grid: required_bool(value, "snapToGrid")?,
        suppress_line_numbers: required_bool(value, "suppressLineNumbers")?,
        checked: required_bool(value, "checked")?,
        text_direction: optional_attribute(value, "textDir")
            .map(TextDirection::parse)
            .transpose()?,
        horizontal_alignment: HorizontalAlignment::parse(required_attribute(align, "horizontal")?)?,
        vertical_alignment: VerticalAlignment::parse(required_attribute(align, "vertical")?)?,
        heading,
        break_settings,
        auto_spacing,
        layout,
        border,
    })
}

fn read_heading(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<Heading, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "heading")?;
    validate_attributes(value, &["type", "idRef", "level"])?;
    require_no_children(document, index)?;
    Ok(Heading {
        heading_type: HeadingType::parse(required_attribute(value, "type")?)?,
        id_ref: required_u32(value, "idRef")?,
        level: required_u8(value, "level")?,
    })
}

fn read_heading_switch(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<CompatibleHeading, ParagraphStyleError> {
    let (current_index, fallback_index) = read_switch(document, index, METATAG_NS)?;
    Ok(CompatibleHeading::MetaTag {
        current: read_heading(document, current_index)?,
        fallback: read_heading(document, fallback_index)?,
    })
}

fn read_break_settings(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<BreakSettings, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "breakSetting")?;
    validate_attributes(
        value,
        &[
            "breakLatinWord",
            "breakNonLatinWord",
            "widowOrphan",
            "keepWithNext",
            "keepLines",
            "pageBreakBefore",
            "lineWrap",
        ],
    )?;
    require_no_children(document, index)?;
    Ok(BreakSettings {
        latin_word: WordBreak::parse(required_attribute(value, "breakLatinWord")?)?,
        non_latin_word: WordBreak::parse(required_attribute(value, "breakNonLatinWord")?)?,
        widow_orphan: required_bool(value, "widowOrphan")?,
        keep_with_next: required_bool(value, "keepWithNext")?,
        keep_lines: required_bool(value, "keepLines")?,
        page_break_before: required_bool(value, "pageBreakBefore")?,
        line_wrap: LineWrap::parse(required_attribute(value, "lineWrap")?)?,
    })
}

fn read_auto_spacing(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<AutoSpacing, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "autoSpacing")?;
    validate_attributes(value, &["eAsianEng", "eAsianNum"])?;
    require_no_children(document, index)?;
    Ok(AutoSpacing {
        e_asian_english: required_bool(value, "eAsianEng")?,
        e_asian_number: required_bool(value, "eAsianNum")?,
    })
}

fn read_layout_switch(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<CompatibleParagraphLayout, ParagraphStyleError> {
    let (current_index, fallback_index) = read_switch_pair(document, index, HWPUNIT_CHAR_NS)?;
    Ok(CompatibleParagraphLayout {
        current: read_layout(document, current_index)?,
        fallback: read_layout(document, fallback_index)?,
    })
}

fn read_switch(
    document: &PreservingXmlDocument,
    index: usize,
    required_namespace: &str,
) -> Result<(usize, usize), ParagraphStyleError> {
    let (case_index, default_index) = read_switch_pair(document, index, required_namespace)?;
    let case_children = child_indexes(document, case_index)?;
    let default_children = child_indexes(document, default_index)?;
    if case_children.len() != 1 || default_children.len() != 1 {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    Ok((case_children[0], default_children[0]))
}

fn read_switch_pair(
    document: &PreservingXmlDocument,
    index: usize,
    required_namespace: &str,
) -> Result<(usize, usize), ParagraphStyleError> {
    let switch = element(document, index)?;
    require_name(switch, PARAGRAPH_NS, "switch")?;
    validate_attributes(switch, &[])?;
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != 2 {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    let case = element(document, children[0])?;
    let fallback = element(document, children[1])?;
    require_name(case, PARAGRAPH_NS, "case")?;
    require_name(fallback, PARAGRAPH_NS, "default")?;
    validate_attributes_with_namespace(case, &[(Some(PARAGRAPH_NS), "required-namespace")])?;
    validate_attributes(fallback, &[])?;
    if required_attribute_ns(case, PARAGRAPH_NS, "required-namespace")? != required_namespace {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    require_only_whitespace_content(document, children[0])?;
    require_only_whitespace_content(document, children[1])?;
    Ok((children[0], children[1]))
}

fn read_layout(
    document: &PreservingXmlDocument,
    branch_index: usize,
) -> Result<ParagraphLayout, ParagraphStyleError> {
    let children = child_indexes(document, branch_index)?;
    if children.len() != 2 {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    Ok(ParagraphLayout {
        margin: read_margin(document, children[0])?,
        line_spacing: read_line_spacing(document, children[1])?,
    })
}

fn read_margin(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<Margin, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "margin")?;
    validate_attributes(value, &[])?;
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    let names = ["intent", "left", "right", "prev", "next"];
    if children.len() != names.len() {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    let mut values = [HwpValue {
        value: 0,
        unit: MeasurementUnit::HwpUnit,
    }; 5];
    for (position, (child_index, name)) in children.into_iter().zip(names).enumerate() {
        let child = element(document, child_index)?;
        require_name(child, CORE_NS, name)?;
        validate_attributes(child, &["value", "unit"])?;
        require_no_children(document, child_index)?;
        values[position] = HwpValue {
            value: required_i32(child, "value")?,
            unit: optional_attribute(child, "unit")
                .map(MeasurementUnit::parse)
                .transpose()?
                .unwrap_or(MeasurementUnit::HwpUnit),
        };
    }
    Ok(Margin {
        intent: values[0],
        left: values[1],
        right: values[2],
        previous: values[3],
        next: values[4],
    })
}

fn read_line_spacing(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<LineSpacing, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "lineSpacing")?;
    validate_attributes(value, &["type", "value", "unit"])?;
    require_no_children(document, index)?;
    Ok(LineSpacing {
        spacing_type: LineSpacingType::parse(required_attribute(value, "type")?)?,
        value: required_i32(value, "value")?,
        unit: optional_attribute(value, "unit")
            .map(MeasurementUnit::parse)
            .transpose()?
            .unwrap_or(MeasurementUnit::HwpUnit),
    })
}

fn read_paragraph_border(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<ParagraphBorder, ParagraphStyleError> {
    let value = element(document, index)?;
    require_name(value, HEAD_NS, "border")?;
    validate_attributes(
        value,
        &[
            "borderFillIDRef",
            "offsetLeft",
            "offsetRight",
            "offsetTop",
            "offsetBottom",
            "connect",
            "ignoreMargin",
        ],
    )?;
    require_no_children(document, index)?;
    Ok(ParagraphBorder {
        border_fill_id_ref: required_u32(value, "borderFillIDRef")?,
        offset_left: required_i32(value, "offsetLeft")?,
        offset_right: required_i32(value, "offsetRight")?,
        offset_top: required_i32(value, "offsetTop")?,
        offset_bottom: required_i32(value, "offsetBottom")?,
        connect: required_bool(value, "connect")?,
        ignore_margin: required_bool(value, "ignoreMargin")?,
    })
}

fn validate_catalog(
    catalog: &ParagraphStyleCatalog,
    limits: ParagraphStyleLimits,
) -> Result<(), ParagraphStyleError> {
    validate_reference_domains(&catalog.references, limits)?;
    if catalog.border_fills.is_empty() || catalog.border_fills.len() > limits.config().border_fills
    {
        return Err(ParagraphStyleError::BorderFillLimit);
    }
    if catalog.styles.is_empty() || catalog.styles.len() > limits.config().styles {
        return Err(ParagraphStyleError::StyleLimit);
    }
    let mut border_ids = BTreeSet::new();
    for (position, border) in catalog.border_fills.iter().enumerate() {
        let expected = u32::try_from(position)
            .map_err(|_| ParagraphStyleError::InvalidId)?
            .checked_add(1)
            .ok_or(ParagraphStyleError::InvalidId)?;
        if border.id != expected || !border_ids.insert(border.id) {
            return Err(ParagraphStyleError::InvalidId);
        }
        validate_border_fill(border)?;
    }
    let tab_ids = catalog
        .references
        .tab_property_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let numbering_ids = catalog
        .references
        .numbering_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let bullet_ids = catalog
        .references
        .bullet_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    for (position, style) in catalog.styles.iter().enumerate() {
        let expected = u32::try_from(position).map_err(|_| ParagraphStyleError::InvalidId)?;
        if style.id != expected {
            return Err(ParagraphStyleError::InvalidId);
        }
        if style.condense > 75 {
            return Err(ParagraphStyleError::OutOfRange);
        }
        if !tab_ids.contains(&style.tab_property_id_ref)
            || !border_ids.contains(&style.border.border_fill_id_ref)
        {
            return Err(ParagraphStyleError::DanglingReference);
        }
        validate_heading(style.heading, &numbering_ids, &bullet_ids)?;
        if style.break_settings.non_latin_word == WordBreak::Hyphenation {
            return Err(ParagraphStyleError::InvalidEnum);
        }
        validate_layout(style.layout.current)?;
        validate_layout(style.layout.fallback)?;
    }
    Ok(())
}

fn validate_reference_domains(
    references: &ParagraphReferenceDomains,
    limits: ParagraphStyleLimits,
) -> Result<(), ParagraphStyleError> {
    for domain in [
        &references.tab_property_ids,
        &references.numbering_ids,
        &references.bullet_ids,
    ] {
        if domain.len() > limits.config().references {
            return Err(ParagraphStyleError::ReferenceLimit);
        }
        if domain.windows(2).any(|window| window[0] >= window[1]) {
            return Err(ParagraphStyleError::InvalidId);
        }
    }
    if references.tab_property_ids.is_empty()
        || !is_dense_domain(&references.tab_property_ids, 0)
        || (!references.numbering_ids.is_empty() && !is_dense_domain(&references.numbering_ids, 1))
        || (!references.bullet_ids.is_empty() && !is_dense_domain(&references.bullet_ids, 1))
    {
        return Err(ParagraphStyleError::InvalidId);
    }
    Ok(())
}

fn is_dense_domain(domain: &[u32], first_id: u32) -> bool {
    domain.iter().enumerate().all(|(position, id)| {
        u32::try_from(position)
            .ok()
            .and_then(|position| first_id.checked_add(position))
            == Some(*id)
    })
}

fn validate_border_fill(border: &BorderFill) -> Result<(), ParagraphStyleError> {
    for line in [
        border.left,
        border.right,
        border.top,
        border.bottom,
        border.diagonal,
    ] {
        if line.color == Color::None {
            return Err(ParagraphStyleError::InvalidColor);
        }
    }
    if let Some(brush) = border.fill_brush
        && brush.window.hatch_style.is_some()
        && brush.window.hatch_color.is_none()
    {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    Ok(())
}

fn validate_heading(
    heading: CompatibleHeading,
    numbering_ids: &BTreeSet<u32>,
    bullet_ids: &BTreeSet<u32>,
) -> Result<(), ParagraphStyleError> {
    let headings = match heading {
        CompatibleHeading::Direct(value) => [Some(value), None],
        CompatibleHeading::MetaTag { current, fallback } => [Some(current), Some(fallback)],
    };
    for value in headings.into_iter().flatten() {
        if value.level > 9 {
            return Err(ParagraphStyleError::OutOfRange);
        }
        match value.heading_type {
            HeadingType::None if value.id_ref == 0 && value.level == 0 => {}
            HeadingType::Outline if value.id_ref == 0 => {}
            HeadingType::Number if numbering_ids.contains(&value.id_ref) => {}
            HeadingType::Bullet if bullet_ids.contains(&value.id_ref) => {}
            HeadingType::None | HeadingType::Outline => {
                return Err(ParagraphStyleError::OutOfRange);
            }
            HeadingType::Number | HeadingType::Bullet => {
                return Err(ParagraphStyleError::DanglingReference);
            }
        }
    }
    Ok(())
}

fn validate_layout(layout: ParagraphLayout) -> Result<(), ParagraphStyleError> {
    if layout.line_spacing.spacing_type == LineSpacingType::Percent
        && !(0..=500).contains(&layout.line_spacing.value)
    {
        return Err(ParagraphStyleError::OutOfRange);
    }
    Ok(())
}

fn copy_reference_domains(
    source: &ParagraphReferenceDomains,
) -> Result<ParagraphReferenceDomains, ParagraphStyleError> {
    Ok(ParagraphReferenceDomains {
        tab_property_ids: copy_u32_slice(&source.tab_property_ids)?,
        numbering_ids: copy_u32_slice(&source.numbering_ids)?,
        bullet_ids: copy_u32_slice(&source.bullet_ids)?,
    })
}

fn copy_u32_slice(source: &[u32]) -> Result<Vec<u32>, ParagraphStyleError> {
    let mut output = Vec::new();
    output
        .try_reserve_exact(source.len())
        .map_err(|_| ParagraphStyleError::AllocationFailed)?;
    output.extend_from_slice(source);
    Ok(output)
}

fn write_border_fills(
    output: &mut BoundedXml,
    border_fills: &[BorderFill],
) -> Result<(), ParagraphStyleError> {
    output.push("<hh:borderFills itemCnt=\"")?;
    output.push_usize(border_fills.len())?;
    output.push("\">")?;
    for border in border_fills {
        output.push("<hh:borderFill id=\"")?;
        output.push_u32(border.id)?;
        output.push("\" threeD=\"")?;
        output.push_bool(border.three_d)?;
        output.push(" shadow=\"")?;
        output.push_bool(border.shadow)?;
        output.push(" centerLine=\"")?;
        output.push(border.center_line.as_str())?;
        output.push("\" breakCellSeparateLine=\"")?;
        output.push_bool(border.break_cell_separate_line)?;
        output.push(">")?;
        write_slash(output, "slash", border.slash)?;
        write_slash(output, "backSlash", border.back_slash)?;
        write_border_line(output, "leftBorder", border.left)?;
        write_border_line(output, "rightBorder", border.right)?;
        write_border_line(output, "topBorder", border.top)?;
        write_border_line(output, "bottomBorder", border.bottom)?;
        write_border_line(output, "diagonal", border.diagonal)?;
        if let Some(brush) = border.fill_brush {
            write_fill_brush(output, brush)?;
        }
        output.push("</hh:borderFill>")?;
    }
    output.push("</hh:borderFills>")
}

fn write_slash(
    output: &mut BoundedXml,
    name: &str,
    slash: Slash,
) -> Result<(), ParagraphStyleError> {
    output.push("<hh:")?;
    output.push(name)?;
    output.push(" type=\"")?;
    output.push(slash.slash_type.as_str())?;
    output.push("\" Crooked=\"")?;
    output.push_bool(slash.crooked)?;
    output.push(" isCounter=\"")?;
    output.push_bool(slash.is_counter)?;
    output.push("/>")
}

fn write_border_line(
    output: &mut BoundedXml,
    name: &str,
    line: BorderLine,
) -> Result<(), ParagraphStyleError> {
    output.push("<hh:")?;
    output.push(name)?;
    output.push(" type=\"")?;
    output.push(line_type_str(line.line_type))?;
    output.push("\" width=\"")?;
    output.push(line.width.as_str())?;
    output.push("\" color=\"")?;
    output.push_color(line.color)?;
    output.push("\"/>")
}

fn write_fill_brush(output: &mut BoundedXml, brush: FillBrush) -> Result<(), ParagraphStyleError> {
    output.push("<hc:fillBrush><hc:winBrush faceColor=\"")?;
    output.push_color(brush.window.face_color)?;
    if let Some(color) = brush.window.hatch_color {
        output.push("\" hatchColor=\"")?;
        output.push_color(color)?;
    }
    if let Some(style) = brush.window.hatch_style {
        output.push("\" hatchStyle=\"")?;
        output.push(style.as_str())?;
    }
    output.push("\" alpha=\"")?;
    output.push_u8(brush.window.alpha)?;
    output.push("\"/></hc:fillBrush>")
}

fn write_paragraph_styles(
    output: &mut BoundedXml,
    styles: &[ParagraphStyle],
) -> Result<(), ParagraphStyleError> {
    output.push("<hh:paraProperties itemCnt=\"")?;
    output.push_usize(styles.len())?;
    output.push("\">")?;
    for style in styles {
        output.push("<hh:paraPr id=\"")?;
        output.push_u32(style.id)?;
        output.push("\" tabPrIDRef=\"")?;
        output.push_u32(style.tab_property_id_ref)?;
        output.push("\" condense=\"")?;
        output.push_u8(style.condense)?;
        output.push("\" fontLineHeight=\"")?;
        output.push_bool(style.font_line_height)?;
        output.push(" snapToGrid=\"")?;
        output.push_bool(style.snap_to_grid)?;
        output.push(" suppressLineNumbers=\"")?;
        output.push_bool(style.suppress_line_numbers)?;
        output.push(" checked=\"")?;
        output.push_bool(style.checked)?;
        if let Some(direction) = style.text_direction {
            output.push(" textDir=\"")?;
            output.push(direction.as_str())?;
            output.push("\"")?;
        }
        output.push(">")?;
        output.push("<hh:align horizontal=\"")?;
        output.push(style.horizontal_alignment.as_str())?;
        output.push("\" vertical=\"")?;
        output.push(style.vertical_alignment.as_str())?;
        output.push("\"/>")?;
        write_compatible_heading(output, style.heading)?;
        write_break_settings(output, style.break_settings)?;
        write_auto_spacing(output, style.auto_spacing)?;
        write_layout_switch(output, style.layout)?;
        write_paragraph_border(output, style.border)?;
        output.push("</hh:paraPr>")?;
    }
    output.push("</hh:paraProperties>")
}

fn write_compatible_heading(
    output: &mut BoundedXml,
    heading: CompatibleHeading,
) -> Result<(), ParagraphStyleError> {
    match heading {
        CompatibleHeading::Direct(value) => write_heading(output, value),
        CompatibleHeading::MetaTag { current, fallback } => {
            output.push("<hp:switch><hp:case hp:required-namespace=\"")?;
            output.push(METATAG_NS)?;
            output.push("\">")?;
            write_heading(output, current)?;
            output.push("</hp:case><hp:default>")?;
            write_heading(output, fallback)?;
            output.push("</hp:default></hp:switch>")
        }
    }
}

fn write_heading(output: &mut BoundedXml, heading: Heading) -> Result<(), ParagraphStyleError> {
    output.push("<hh:heading type=\"")?;
    output.push(heading.heading_type.as_str())?;
    output.push("\" idRef=\"")?;
    output.push_u32(heading.id_ref)?;
    output.push("\" level=\"")?;
    output.push_u8(heading.level)?;
    output.push("\"/>")
}

fn write_break_settings(
    output: &mut BoundedXml,
    value: BreakSettings,
) -> Result<(), ParagraphStyleError> {
    output.push("<hh:breakSetting breakLatinWord=\"")?;
    output.push(value.latin_word.as_str())?;
    output.push("\" breakNonLatinWord=\"")?;
    output.push(value.non_latin_word.as_str())?;
    output.push("\" widowOrphan=\"")?;
    output.push_bool(value.widow_orphan)?;
    output.push(" keepWithNext=\"")?;
    output.push_bool(value.keep_with_next)?;
    output.push(" keepLines=\"")?;
    output.push_bool(value.keep_lines)?;
    output.push(" pageBreakBefore=\"")?;
    output.push_bool(value.page_break_before)?;
    output.push(" lineWrap=\"")?;
    output.push(value.line_wrap.as_str())?;
    output.push("\"/>")
}

fn write_auto_spacing(
    output: &mut BoundedXml,
    value: AutoSpacing,
) -> Result<(), ParagraphStyleError> {
    output.push("<hh:autoSpacing eAsianEng=\"")?;
    output.push_bool(value.e_asian_english)?;
    output.push(" eAsianNum=\"")?;
    output.push_bool(value.e_asian_number)?;
    output.push("/>")
}

fn write_layout_switch(
    output: &mut BoundedXml,
    value: CompatibleParagraphLayout,
) -> Result<(), ParagraphStyleError> {
    output.push("<hp:switch><hp:case hp:required-namespace=\"")?;
    output.push(HWPUNIT_CHAR_NS)?;
    output.push("\">")?;
    write_layout(output, value.current)?;
    output.push("</hp:case><hp:default>")?;
    write_layout(output, value.fallback)?;
    output.push("</hp:default></hp:switch>")
}

fn write_layout(
    output: &mut BoundedXml,
    value: ParagraphLayout,
) -> Result<(), ParagraphStyleError> {
    output.push("<hh:margin>")?;
    write_margin_value(output, "intent", value.margin.intent)?;
    write_margin_value(output, "left", value.margin.left)?;
    write_margin_value(output, "right", value.margin.right)?;
    write_margin_value(output, "prev", value.margin.previous)?;
    write_margin_value(output, "next", value.margin.next)?;
    output.push("</hh:margin><hh:lineSpacing type=\"")?;
    output.push(value.line_spacing.spacing_type.as_str())?;
    output.push("\" value=\"")?;
    output.push_i32(value.line_spacing.value)?;
    output.push("\" unit=\"")?;
    output.push(value.line_spacing.unit.as_str())?;
    output.push("\"/>")
}

fn write_margin_value(
    output: &mut BoundedXml,
    name: &str,
    value: HwpValue,
) -> Result<(), ParagraphStyleError> {
    output.push("<hc:")?;
    output.push(name)?;
    output.push(" value=\"")?;
    output.push_i32(value.value)?;
    output.push("\" unit=\"")?;
    output.push(value.unit.as_str())?;
    output.push("\"/>")
}

fn write_paragraph_border(
    output: &mut BoundedXml,
    value: ParagraphBorder,
) -> Result<(), ParagraphStyleError> {
    output.push("<hh:border borderFillIDRef=\"")?;
    output.push_u32(value.border_fill_id_ref)?;
    output.push("\" offsetLeft=\"")?;
    output.push_i32(value.offset_left)?;
    output.push("\" offsetRight=\"")?;
    output.push_i32(value.offset_right)?;
    output.push("\" offsetTop=\"")?;
    output.push_i32(value.offset_top)?;
    output.push("\" offsetBottom=\"")?;
    output.push_i32(value.offset_bottom)?;
    output.push("\" connect=\"")?;
    output.push_bool(value.connect)?;
    output.push(" ignoreMargin=\"")?;
    output.push_bool(value.ignore_margin)?;
    output.push("/>")
}

struct BoundedXml {
    value: String,
    maximum: usize,
}

impl BoundedXml {
    fn new(maximum: usize) -> Result<Self, ParagraphStyleError> {
        let mut value = String::new();
        value
            .try_reserve(maximum.min(16 * 1024))
            .map_err(|_| ParagraphStyleError::AllocationFailed)?;
        Ok(Self { value, maximum })
    }

    fn push(&mut self, value: &str) -> Result<(), ParagraphStyleError> {
        let length = self
            .value
            .len()
            .checked_add(value.len())
            .ok_or(ParagraphStyleError::OutputLimit)?;
        if length > self.maximum {
            return Err(ParagraphStyleError::OutputLimit);
        }
        self.value
            .try_reserve(value.len())
            .map_err(|_| ParagraphStyleError::AllocationFailed)?;
        self.value.push_str(value);
        Ok(())
    }

    fn push_bool(&mut self, value: bool) -> Result<(), ParagraphStyleError> {
        self.push(if value { "1\"" } else { "0\"" })
    }

    fn push_u8(&mut self, value: u8) -> Result<(), ParagraphStyleError> {
        self.push(&value.to_string())
    }

    fn push_u32(&mut self, value: u32) -> Result<(), ParagraphStyleError> {
        self.push(&value.to_string())
    }

    fn push_i32(&mut self, value: i32) -> Result<(), ParagraphStyleError> {
        self.push(&value.to_string())
    }

    fn push_usize(&mut self, value: usize) -> Result<(), ParagraphStyleError> {
        self.push(&value.to_string())
    }

    fn push_color(&mut self, color: Color) -> Result<(), ParagraphStyleError> {
        match color {
            Color::None => self.push("none"),
            Color::Rgb(red, green, blue) => {
                const HEX: &[u8; 16] = b"0123456789ABCDEF";
                let bytes = [
                    b'#',
                    HEX[usize::from(red >> 4)],
                    HEX[usize::from(red & 0x0F)],
                    HEX[usize::from(green >> 4)],
                    HEX[usize::from(green & 0x0F)],
                    HEX[usize::from(blue >> 4)],
                    HEX[usize::from(blue & 0x0F)],
                ];
                let value =
                    std::str::from_utf8(&bytes).map_err(|_| ParagraphStyleError::InvalidColor)?;
                self.push(value)
            }
        }
    }

    fn finish(self) -> Vec<u8> {
        self.value.into_bytes()
    }
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, ParagraphStyleError> {
    document
        .elements()
        .get(index)
        .ok_or(ParagraphStyleError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, namespace: &str, local_name: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local_name
}

fn require_name(
    element: &XmlElementToken,
    namespace: &str,
    local_name: &str,
) -> Result<(), ParagraphStyleError> {
    if has_name(element, namespace, local_name) {
        Ok(())
    } else {
        Err(ParagraphStyleError::UnsupportedShape)
    }
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, ParagraphStyleError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| ParagraphStyleError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn exactly_one_child(
    document: &PreservingXmlDocument,
    parent: usize,
    namespace: &str,
    local_name: &str,
) -> Result<usize, ParagraphStyleError> {
    let mut found = None;
    for index in child_indexes(document, parent)? {
        let child = element(document, index)?;
        if child.name().local_name() != local_name {
            continue;
        }
        if !has_name(child, namespace, local_name) || found.replace(index).is_some() {
            return Err(ParagraphStyleError::UnsupportedShape);
        }
    }
    found.ok_or(ParagraphStyleError::UnsupportedShape)
}

fn optional_one_child(
    document: &PreservingXmlDocument,
    parent: usize,
    namespace: &str,
    local_name: &str,
) -> Result<Option<usize>, ParagraphStyleError> {
    let mut found = None;
    for index in child_indexes(document, parent)? {
        let child = element(document, index)?;
        if child.name().local_name() != local_name {
            continue;
        }
        if !has_name(child, namespace, local_name) || found.replace(index).is_some() {
            return Err(ParagraphStyleError::UnsupportedShape);
        }
    }
    Ok(found)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), ParagraphStyleError> {
    let expected = allowed.iter().map(|name| (None, *name)).collect::<Vec<_>>();
    validate_attributes_with_namespace(element, &expected)
}

fn validate_attributes_with_namespace(
    element: &XmlElementToken,
    allowed: &[(Option<&str>, &str)],
) -> Result<(), ParagraphStyleError> {
    let mut seen = BTreeSet::<(Option<&str>, &str)>::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let key = (attribute.name().namespace(), attribute.name().local_name());
        if !allowed.contains(&key) || !seen.insert(key) {
            return Err(ParagraphStyleError::UnsupportedShape);
        }
    }
    Ok(())
}

fn optional_attribute<'a>(element: &'a XmlElementToken, name: &str) -> Option<&'a str> {
    element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == name
        })
        .map(XmlAttributeToken::semantic_value)
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, ParagraphStyleError> {
    optional_attribute(element, name).ok_or(ParagraphStyleError::UnsupportedShape)
}

fn required_attribute_ns<'a>(
    element: &'a XmlElementToken,
    namespace: &str,
    name: &str,
) -> Result<&'a str, ParagraphStyleError> {
    element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace() == Some(namespace)
                && attribute.name().local_name() == name
        })
        .map(XmlAttributeToken::semantic_value)
        .ok_or(ParagraphStyleError::UnsupportedShape)
}

fn parse_u32(value: &str) -> Result<u32, ParagraphStyleError> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ParagraphStyleError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| ParagraphStyleError::InvalidNumber)
}

fn parse_i32(value: &str) -> Result<i32, ParagraphStyleError> {
    let digits = value.strip_prefix('-').unwrap_or(value);
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(ParagraphStyleError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| ParagraphStyleError::InvalidNumber)
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, ParagraphStyleError> {
    parse_u32(required_attribute(element, name)?)
}

fn required_usize(element: &XmlElementToken, name: &str) -> Result<usize, ParagraphStyleError> {
    usize::try_from(required_u32(element, name)?).map_err(|_| ParagraphStyleError::InvalidNumber)
}

fn required_u8(element: &XmlElementToken, name: &str) -> Result<u8, ParagraphStyleError> {
    u8::try_from(required_u32(element, name)?).map_err(|_| ParagraphStyleError::OutOfRange)
}

fn required_i32(element: &XmlElementToken, name: &str) -> Result<i32, ParagraphStyleError> {
    parse_i32(required_attribute(element, name)?)
}

fn required_bool(element: &XmlElementToken, name: &str) -> Result<bool, ParagraphStyleError> {
    match required_attribute(element, name)? {
        "1" | "true" => Ok(true),
        "0" | "false" => Ok(false),
        _ => Err(ParagraphStyleError::InvalidBoolean),
    }
}

fn parse_color(value: &str) -> Result<Color, ParagraphStyleError> {
    if value == "none" {
        return Ok(Color::None);
    }
    let Some(hex) = value.strip_prefix('#') else {
        return Err(ParagraphStyleError::InvalidColor);
    };
    if hex.len() != 6 || !hex.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(ParagraphStyleError::InvalidColor);
    }
    let red = u8::from_str_radix(&hex[0..2], 16).map_err(|_| ParagraphStyleError::InvalidColor)?;
    let green =
        u8::from_str_radix(&hex[2..4], 16).map_err(|_| ParagraphStyleError::InvalidColor)?;
    let blue = u8::from_str_radix(&hex[4..6], 16).map_err(|_| ParagraphStyleError::InvalidColor)?;
    Ok(Color::Rgb(red, green, blue))
}

fn parse_line_type(value: &str) -> Result<LineType2, ParagraphStyleError> {
    match value {
        "NONE" => Ok(LineType2::None),
        "SOLID" => Ok(LineType2::Solid),
        "DOT" => Ok(LineType2::Dot),
        "DASH" => Ok(LineType2::Dash),
        "DASH_DOT" => Ok(LineType2::DashDot),
        "DASH_DOT_DOT" => Ok(LineType2::DashDotDot),
        "LONG_DASH" => Ok(LineType2::LongDash),
        "CIRCLE" => Ok(LineType2::Circle),
        "DOUBLE_SLIM" => Ok(LineType2::DoubleSlim),
        "SLIM_THICK" => Ok(LineType2::SlimThick),
        "THICK_SLIM" => Ok(LineType2::ThickSlim),
        "SLIM_THICK_SLIM" => Ok(LineType2::SlimThickSlim),
        _ => Err(ParagraphStyleError::InvalidEnum),
    }
}

const fn line_type_str(value: LineType2) -> &'static str {
    match value {
        LineType2::None => "NONE",
        LineType2::Solid => "SOLID",
        LineType2::Dot => "DOT",
        LineType2::Dash => "DASH",
        LineType2::DashDot => "DASH_DOT",
        LineType2::DashDotDot => "DASH_DOT_DOT",
        LineType2::LongDash => "LONG_DASH",
        LineType2::Circle => "CIRCLE",
        LineType2::DoubleSlim => "DOUBLE_SLIM",
        LineType2::SlimThick => "SLIM_THICK",
        LineType2::ThickSlim => "THICK_SLIM",
        LineType2::SlimThickSlim => "SLIM_THICK_SLIM",
    }
}

fn require_no_children(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), ParagraphStyleError> {
    require_only_whitespace_content(document, index)?;
    if element(document, index)?.first_child().is_some() {
        return Err(ParagraphStyleError::UnsupportedShape);
    }
    Ok(())
}

fn require_only_whitespace_content(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), ParagraphStyleError> {
    let value = element(document, index)?;
    if value.is_empty() {
        return Ok(());
    }
    let end = value
        .end_token()
        .ok_or(ParagraphStyleError::UnsupportedShape)?;
    for token in &document.tokens()[(value.start_token() + 1)..end] {
        if token.element_index() != Some(index) {
            continue;
        }
        if matches!(
            token.kind(),
            XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment
        ) {
            return Err(ParagraphStyleError::UnsupportedShape);
        }
    }
    Ok(())
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), ParagraphStyleError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(ParagraphStyleError::UnsupportedShape);
        }
    }
    Ok(())
}
