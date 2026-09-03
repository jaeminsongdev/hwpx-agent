use std::collections::BTreeMap;
use std::fmt::{self, Debug};

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken, XmlTokenKind,
};
use crate::text_flow::{ParagraphChild, TextFlow, TextRunItem};

pub const HANCOM_2020_HEAD_NAMESPACE: &str = "http://www.hancom.co.kr/hwpml/2011/head";
pub const CHARACTER_STYLE_PROFILE_ID: &str = "hwpx-agent.character-style/1";

const LANGUAGE_SLOTS: [LanguageSlot; 7] = [
    LanguageSlot::Hangul,
    LanguageSlot::Latin,
    LanguageSlot::Hanja,
    LanguageSlot::Japanese,
    LanguageSlot::Other,
    LanguageSlot::Symbol,
    LanguageSlot::User,
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CharacterStyleLimitConfig {
    pub input_bytes: usize,
    pub elements: usize,
    pub fonts_per_language: usize,
    pub styles: usize,
    pub string_bytes: usize,
}

impl Default for CharacterStyleLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 2 * 1024 * 1024,
            elements: 32_768,
            fonts_per_language: 4_096,
            styles: 16_384,
            string_bytes: 4_096,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct CharacterStyleLimits(CharacterStyleLimitConfig);

impl CharacterStyleLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 65_536;
    pub const HARD_MAX_FONTS_PER_LANGUAGE: usize = 16_384;
    pub const HARD_MAX_STYLES: usize = 32_768;
    pub const HARD_MAX_STRING_BYTES: usize = 16_384;

    /// Creates a finite current-2020 character-style limit set.
    ///
    /// # Errors
    ///
    /// Rejects zero values and values above their hard ceilings.
    pub fn new(config: CharacterStyleLimitConfig) -> Result<Self, CharacterStyleError> {
        let values = [
            (config.input_bytes, Self::HARD_MAX_INPUT_BYTES),
            (config.elements, Self::HARD_MAX_ELEMENTS),
            (config.fonts_per_language, Self::HARD_MAX_FONTS_PER_LANGUAGE),
            (config.styles, Self::HARD_MAX_STYLES),
            (config.string_bytes, Self::HARD_MAX_STRING_BYTES),
        ];
        if values
            .into_iter()
            .any(|(value, ceiling)| value == 0 || value > ceiling)
        {
            return Err(CharacterStyleError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> CharacterStyleLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum LanguageSlot {
    Hangul,
    Latin,
    Hanja,
    Japanese,
    Other,
    Symbol,
    User,
}

impl LanguageSlot {
    const fn upper(self) -> &'static str {
        match self {
            Self::Hangul => "HANGUL",
            Self::Latin => "LATIN",
            Self::Hanja => "HANJA",
            Self::Japanese => "JAPANESE",
            Self::Other => "OTHER",
            Self::Symbol => "SYMBOL",
            Self::User => "USER",
        }
    }

    const fn lower(self) -> &'static str {
        match self {
            Self::Hangul => "hangul",
            Self::Latin => "latin",
            Self::Hanja => "hanja",
            Self::Japanese => "japanese",
            Self::Other => "other",
            Self::Symbol => "symbol",
            Self::User => "user",
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct LanguageValues<T> {
    pub hangul: T,
    pub latin: T,
    pub hanja: T,
    pub japanese: T,
    pub other: T,
    pub symbol: T,
    pub user: T,
}

impl<T> LanguageValues<T> {
    fn get(&self, slot: LanguageSlot) -> &T {
        match slot {
            LanguageSlot::Hangul => &self.hangul,
            LanguageSlot::Latin => &self.latin,
            LanguageSlot::Hanja => &self.hanja,
            LanguageSlot::Japanese => &self.japanese,
            LanguageSlot::Other => &self.other,
            LanguageSlot::Symbol => &self.symbol,
            LanguageSlot::User => &self.user,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum FontType {
    Representative,
    TrueType,
    HancomFont,
}

impl FontType {
    fn parse(value: &str) -> Result<Self, CharacterStyleError> {
        match value {
            "REP" => Ok(Self::Representative),
            "TTF" => Ok(Self::TrueType),
            "HFT" => Ok(Self::HancomFont),
            _ => Err(CharacterStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Representative => "REP",
            Self::TrueType => "TTF",
            Self::HancomFont => "HFT",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum FontFamily {
    Unknown,
    Myungjo,
    Gothic,
    SansSerif,
    BrushScript,
    Decorative,
    NonRectMyungjo,
    NonRectGothic,
}

impl FontFamily {
    fn parse(value: &str) -> Result<Self, CharacterStyleError> {
        match value {
            "FCAT_UNKNOWN" => Ok(Self::Unknown),
            "FCAT_MYUNGJO" => Ok(Self::Myungjo),
            "FCAT_GOTHIC" => Ok(Self::Gothic),
            "FCAT_SSERIF" => Ok(Self::SansSerif),
            "FCAT_BRUSHSCRIPT" => Ok(Self::BrushScript),
            "FCAT_DECORATIVE" => Ok(Self::Decorative),
            "FCAT_NONRECTMJ" => Ok(Self::NonRectMyungjo),
            "FCAT_NONRECTGT" => Ok(Self::NonRectGothic),
            _ => Err(CharacterStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Unknown => "FCAT_UNKNOWN",
            Self::Myungjo => "FCAT_MYUNGJO",
            Self::Gothic => "FCAT_GOTHIC",
            Self::SansSerif => "FCAT_SSERIF",
            Self::BrushScript => "FCAT_BRUSHSCRIPT",
            Self::Decorative => "FCAT_DECORATIVE",
            Self::NonRectMyungjo => "FCAT_NONRECTMJ",
            Self::NonRectGothic => "FCAT_NONRECTGT",
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, Ord, PartialEq, PartialOrd)]
pub enum BinaryProperty {
    #[default]
    Off,
    On,
}

impl BinaryProperty {
    const fn is_on(self) -> bool {
        matches!(self, Self::On)
    }
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd)]
pub struct SubstituteFont {
    pub face: String,
    pub font_type: FontType,
    pub binary_item_id_ref: Option<String>,
}

impl Debug for SubstituteFont {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SubstituteFont")
            .field("face_bytes", &self.face.len())
            .field("font_type", &self.font_type)
            .field(
                "binary_item_id_ref_present",
                &self.binary_item_id_ref.is_some(),
            )
            .finish()
    }
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd)]
pub struct FontTypeInfo {
    pub family: FontFamily,
    pub serif_style: Option<String>,
    pub weight: i32,
    pub proportion: i32,
    pub contrast: i32,
    pub stroke_variation: i32,
    pub arm_style: BinaryProperty,
    pub letterform: BinaryProperty,
    pub midline: BinaryProperty,
    pub x_height: BinaryProperty,
}

impl Debug for FontTypeInfo {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FontTypeInfo")
            .field("family", &self.family)
            .field("serif_style_present", &self.serif_style.is_some())
            .field("weight", &self.weight)
            .field("proportion", &self.proportion)
            .field("contrast", &self.contrast)
            .field("stroke_variation", &self.stroke_variation)
            .field("arm_style", &self.arm_style)
            .field("letterform", &self.letterform)
            .field("midline", &self.midline)
            .field("x_height", &self.x_height)
            .finish()
    }
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd)]
pub struct FontFace {
    pub id: u32,
    pub face: String,
    pub font_type: FontType,
    pub is_embedded: bool,
    pub binary_item_id_ref: Option<String>,
    pub substitute: Option<SubstituteFont>,
    pub type_info: Option<FontTypeInfo>,
}

impl Debug for FontFace {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FontFace")
            .field("id", &self.id)
            .field("face_bytes", &self.face.len())
            .field("font_type", &self.font_type)
            .field("is_embedded", &self.is_embedded)
            .field(
                "binary_item_id_ref_present",
                &self.binary_item_id_ref.is_some(),
            )
            .field("substitute", &self.substitute)
            .field("type_info", &self.type_info)
            .finish()
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct FontFaceGroup {
    pub language: LanguageSlot,
    pub fonts: Vec<FontFace>,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum Color {
    None,
    Rgb(u8, u8, u8),
}

impl Color {
    const BLACK: Self = Self::Rgb(0, 0, 0);
    const DEFAULT_SHADOW: Self = Self::Rgb(0xB2, 0xB2, 0xB2);

    fn parse(value: &str) -> Result<Self, CharacterStyleError> {
        if value == "none" {
            return Ok(Self::None);
        }
        let Some(hex) = value.strip_prefix('#') else {
            return Err(CharacterStyleError::InvalidColor);
        };
        if hex.len() != 6 || !hex.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(CharacterStyleError::InvalidColor);
        }
        let red =
            u8::from_str_radix(&hex[0..2], 16).map_err(|_| CharacterStyleError::InvalidColor)?;
        let green =
            u8::from_str_radix(&hex[2..4], 16).map_err(|_| CharacterStyleError::InvalidColor)?;
        let blue =
            u8::from_str_radix(&hex[4..6], 16).map_err(|_| CharacterStyleError::InvalidColor)?;
        Ok(Self::Rgb(red, green, blue))
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum EmphasisMark {
    None,
    DotAbove,
    RingAbove,
    Tilde,
    Caron,
    Side,
    Colon,
    GraveAccent,
    AcuteAccent,
    Circumflex,
    Macron,
    HookAbove,
    DotBelow,
}

impl EmphasisMark {
    fn parse(value: &str) -> Result<Self, CharacterStyleError> {
        match value {
            "NONE" => Ok(Self::None),
            "DOT_ABOVE" => Ok(Self::DotAbove),
            "RING_ABOVE" => Ok(Self::RingAbove),
            "TILDE" => Ok(Self::Tilde),
            "CARON" => Ok(Self::Caron),
            "SIDE" => Ok(Self::Side),
            "COLON" => Ok(Self::Colon),
            "GRAVE_ACCENT" => Ok(Self::GraveAccent),
            "ACUTE_ACCENT" => Ok(Self::AcuteAccent),
            "CIRCUMFLEX" => Ok(Self::Circumflex),
            "MACRON" => Ok(Self::Macron),
            "HOOK_ABOVE" => Ok(Self::HookAbove),
            "DOT_BELOW" => Ok(Self::DotBelow),
            _ => Err(CharacterStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::DotAbove => "DOT_ABOVE",
            Self::RingAbove => "RING_ABOVE",
            Self::Tilde => "TILDE",
            Self::Caron => "CARON",
            Self::Side => "SIDE",
            Self::Colon => "COLON",
            Self::GraveAccent => "GRAVE_ACCENT",
            Self::AcuteAccent => "ACUTE_ACCENT",
            Self::Circumflex => "CIRCUMFLEX",
            Self::Macron => "MACRON",
            Self::HookAbove => "HOOK_ABOVE",
            Self::DotBelow => "DOT_BELOW",
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, Ord, PartialEq, PartialOrd)]
pub enum LineType1 {
    #[default]
    None,
    Solid,
    Dot,
    Thick,
    Dash,
    DashDot,
    DashDotDot,
}

impl LineType1 {
    fn parse(value: &str) -> Result<Self, CharacterStyleError> {
        match value {
            "NONE" => Ok(Self::None),
            "SOLID" => Ok(Self::Solid),
            "DOT" => Ok(Self::Dot),
            "THICK" => Ok(Self::Thick),
            "DASH" => Ok(Self::Dash),
            "DASH_DOT" => Ok(Self::DashDot),
            "DASH_DOT_DOT" => Ok(Self::DashDotDot),
            _ => Err(CharacterStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::Solid => "SOLID",
            Self::Dot => "DOT",
            Self::Thick => "THICK",
            Self::Dash => "DASH",
            Self::DashDot => "DASH_DOT",
            Self::DashDotDot => "DASH_DOT_DOT",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum LineType2 {
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
}

impl LineType2 {
    fn parse(value: &str) -> Result<Self, CharacterStyleError> {
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
            _ => Err(CharacterStyleError::InvalidEnum),
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
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum UnderlinePosition {
    None,
    Bottom,
    Center,
    Top,
}

impl UnderlinePosition {
    fn parse(value: &str) -> Result<Self, CharacterStyleError> {
        match value {
            "NONE" => Ok(Self::None),
            "BOTTOM" => Ok(Self::Bottom),
            "CENTER" => Ok(Self::Center),
            "TOP" => Ok(Self::Top),
            _ => Err(CharacterStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::Bottom => "BOTTOM",
            Self::Center => "CENTER",
            Self::Top => "TOP",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum ShadowType {
    None,
    Drop,
    Continuous,
}

impl ShadowType {
    fn parse(value: &str) -> Result<Self, CharacterStyleError> {
        match value {
            "NONE" => Ok(Self::None),
            "DROP" => Ok(Self::Drop),
            "CONTINUOUS" => Ok(Self::Continuous),
            _ => Err(CharacterStyleError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::Drop => "DROP",
            Self::Continuous => "CONTINUOUS",
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct Underline {
    pub position: UnderlinePosition,
    pub shape: LineType2,
    pub color: Color,
}

impl Default for Underline {
    fn default() -> Self {
        Self {
            position: UnderlinePosition::None,
            shape: LineType2::Solid,
            color: Color::BLACK,
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct Strikeout {
    pub shape: LineType2,
    pub color: Color,
}

impl Default for Strikeout {
    fn default() -> Self {
        Self {
            shape: LineType2::None,
            color: Color::BLACK,
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct Shadow {
    pub shadow_type: ShadowType,
    pub color: Color,
    pub offset_x: i16,
    pub offset_y: i16,
}

impl Default for Shadow {
    fn default() -> Self {
        Self {
            shadow_type: ShadowType::None,
            color: Color::DEFAULT_SHADOW,
            offset_x: 10,
            offset_y: 10,
        }
    }
}

#[derive(Clone, Debug, Default, Eq, Ord, PartialEq, PartialOrd)]
pub struct CharacterEffects {
    pub italic: BinaryProperty,
    pub bold: BinaryProperty,
    pub underline: Underline,
    pub strikeout: Strikeout,
    pub outline: LineType1,
    pub shadow: Shadow,
    pub emboss: BinaryProperty,
    pub engrave: BinaryProperty,
    pub superscript: BinaryProperty,
    pub subscript: BinaryProperty,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct CharacterStyle {
    pub id: u32,
    pub height: u32,
    pub text_color: Color,
    pub shade_color: Color,
    pub use_font_space: bool,
    pub use_kerning: bool,
    pub emphasis_mark: EmphasisMark,
    pub border_fill_id_ref: Option<u32>,
    pub font_refs: LanguageValues<u32>,
    pub ratios: LanguageValues<u16>,
    pub spacing: LanguageValues<i16>,
    pub relative_sizes: LanguageValues<u16>,
    pub offsets: LanguageValues<i16>,
    pub effects: CharacterEffects,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CharacterStyleCatalog {
    pub font_faces: Vec<FontFaceGroup>,
    pub styles: Vec<CharacterStyle>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DeduplicatedCharacterStyles {
    pub styles: Vec<CharacterStyle>,
    pub old_to_new: Vec<u32>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CharacterStyleLoweringReceipt {
    pub profile_id: &'static str,
    pub sha256: [u8; 32],
    pub output_bytes: usize,
    pub font_count: usize,
    pub style_count: usize,
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum CharacterStyleError {
    #[error("character-style limits are invalid")]
    InvalidLimit,
    #[error("character-style input exceeds its finite limit")]
    InputLimit,
    #[error("character-style XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("character-style root is not the current Hangul 2020 head profile")]
    WrongRoot,
    #[error("character-style element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("character-style count does not match content")]
    CountMismatch,
    #[error("character-style identifier is not unique and dense")]
    InvalidId,
    #[error("character-style reference is dangling")]
    DanglingReference,
    #[error("character-style numeric attribute is invalid")]
    InvalidNumber,
    #[error("character-style boolean attribute is invalid")]
    InvalidBoolean,
    #[error("character-style enum attribute is invalid")]
    InvalidEnum,
    #[error("character-style color is invalid")]
    InvalidColor,
    #[error("character-style value is outside the current-2020 range")]
    OutOfRange,
    #[error("character-style string is invalid or exceeds its finite limit")]
    InvalidString,
    #[error("character-style font count exceeds its finite limit")]
    FontLimit,
    #[error("character-style count exceeds its finite limit")]
    StyleLimit,
    #[error("character-style element count exceeds its finite limit")]
    ElementLimit,
    #[error("character-style output exceeds its finite limit")]
    OutputLimit,
    #[error("character-style allocation failed")]
    AllocationFailed,
    #[error("character-style lowered readback differs")]
    ReadbackMismatch,
}

impl CharacterStyleError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "character_style_invalid_limit",
            Self::InputLimit => "character_style_input_limit",
            Self::Preserving(_) => "character_style_preserving_xml",
            Self::WrongRoot => "character_style_wrong_root",
            Self::UnsupportedShape => "character_style_unsupported_shape",
            Self::CountMismatch => "character_style_count_mismatch",
            Self::InvalidId => "character_style_invalid_id",
            Self::DanglingReference => "character_style_dangling_reference",
            Self::InvalidNumber => "character_style_invalid_number",
            Self::InvalidBoolean => "character_style_invalid_boolean",
            Self::InvalidEnum => "character_style_invalid_enum",
            Self::InvalidColor => "character_style_invalid_color",
            Self::OutOfRange => "character_style_out_of_range",
            Self::InvalidString => "character_style_invalid_string",
            Self::FontLimit => "character_style_font_limit",
            Self::StyleLimit => "character_style_style_limit",
            Self::ElementLimit => "character_style_element_limit",
            Self::OutputLimit => "character_style_output_limit",
            Self::AllocationFailed => "character_style_allocation_failed",
            Self::ReadbackMismatch => "character_style_readback_mismatch",
        }
    }
}

#[derive(Debug)]
pub struct CharacterStyleCatalogReader;

impl CharacterStyleCatalogReader {
    /// Lifts the fontface and charProperties portions of a current-2020 header or refList.
    ///
    /// # Errors
    ///
    /// Returns a stable fail-closed error for malformed, unsupported, unbounded, out-of-range,
    /// non-dense, or reference-incomplete typed content.
    pub fn read(
        bytes: &[u8],
        limits: CharacterStyleLimits,
    ) -> Result<CharacterStyleCatalog, CharacterStyleError> {
        if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
            return Err(CharacterStyleError::InputLimit);
        }
        let document = PreservingXmlDocument::parse(bytes)?;
        if document.elements().len() > limits.config().elements {
            return Err(CharacterStyleError::ElementLimit);
        }
        validate_document_envelope(&document)?;
        let root_index = document.root_element();
        let root = element(&document, root_index)?;
        let ref_list_index = if has_name(root, "refList") {
            root_index
        } else if has_name(root, "head") {
            exactly_one_child(&document, root_index, "refList")?
        } else {
            return Err(CharacterStyleError::WrongRoot);
        };
        let fontfaces_index = exactly_one_child(&document, ref_list_index, "fontfaces")?;
        let char_properties_index = exactly_one_child(&document, ref_list_index, "charProperties")?;
        let font_faces = read_font_faces(&document, fontfaces_index, limits)?;
        let styles = read_character_styles(&document, char_properties_index, &font_faces, limits)?;
        let catalog = CharacterStyleCatalog { font_faces, styles };
        validate_catalog(&catalog, limits)?;
        Ok(catalog)
    }
}

#[derive(Debug)]
pub struct CharacterStyleCatalogWriter;

impl CharacterStyleCatalogWriter {
    /// Lowers a typed catalog to deterministic current-2020 refList XML and reparses it.
    ///
    /// # Errors
    ///
    /// Rejects invalid public model values, limit violations, dangling references, or a readback
    /// mismatch. No raw XML or installed-font fallback is accepted.
    pub fn lower(
        catalog: &CharacterStyleCatalog,
        limits: CharacterStyleLimits,
    ) -> Result<Vec<u8>, CharacterStyleError> {
        let (bytes, _) = Self::lower_with_receipt(catalog, limits)?;
        Ok(bytes)
    }

    /// Lowers a typed catalog and returns a deterministic integrity receipt.
    ///
    /// # Errors
    ///
    /// Applies the same validation and readback requirements as lower.
    pub fn lower_with_receipt(
        catalog: &CharacterStyleCatalog,
        limits: CharacterStyleLimits,
    ) -> Result<(Vec<u8>, CharacterStyleLoweringReceipt), CharacterStyleError> {
        validate_catalog(catalog, limits)?;
        let mut output = BoundedXml::new(limits.config().input_bytes)?;
        output.push("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")?;
        output.push("<hh:refList xmlns:hh=\"")?;
        output.push(HANCOM_2020_HEAD_NAMESPACE)?;
        output.push("\">")?;
        write_font_faces(&mut output, &catalog.font_faces)?;
        write_character_styles(&mut output, &catalog.styles)?;
        output.push("</hh:refList>")?;
        let bytes = output.finish();
        let readback = CharacterStyleCatalogReader::read(&bytes, limits)?;
        if readback != *catalog {
            return Err(CharacterStyleError::ReadbackMismatch);
        }
        let receipt = CharacterStyleLoweringReceipt {
            profile_id: CHARACTER_STYLE_PROFILE_ID,
            sha256: <[u8; 32]>::from(Sha256::digest(&bytes)),
            output_bytes: bytes.len(),
            font_count: catalog
                .font_faces
                .iter()
                .map(|group| group.fonts.len())
                .sum(),
            style_count: catalog.styles.len(),
        };
        Ok((bytes, receipt))
    }
}

impl CharacterStyleCatalog {
    /// Deduplicates semantic styles in deterministic first-occurrence order.
    ///
    /// # Errors
    ///
    /// Rejects an invalid catalog or allocation/identifier overflow.
    pub fn deduplicate(
        &self,
        limits: CharacterStyleLimits,
    ) -> Result<DeduplicatedCharacterStyles, CharacterStyleError> {
        validate_catalog(self, limits)?;
        let mut seen = BTreeMap::<CharacterStyle, u32>::new();
        let mut styles = Vec::new();
        let mut old_to_new = Vec::new();
        styles
            .try_reserve(self.styles.len())
            .map_err(|_| CharacterStyleError::AllocationFailed)?;
        old_to_new
            .try_reserve(self.styles.len())
            .map_err(|_| CharacterStyleError::AllocationFailed)?;
        for style in &self.styles {
            let mut semantic = style.clone();
            semantic.id = 0;
            let new_id = if let Some(existing) = seen.get(&semantic) {
                *existing
            } else {
                let allocated =
                    u32::try_from(styles.len()).map_err(|_| CharacterStyleError::InvalidId)?;
                let mut canonical = style.clone();
                canonical.id = allocated;
                styles.push(canonical);
                seen.insert(semantic, allocated);
                allocated
            };
            old_to_new.push(new_id);
        }
        Ok(DeduplicatedCharacterStyles { styles, old_to_new })
    }
}

impl DeduplicatedCharacterStyles {
    /// Rewrites only typed character-style references in a text flow.
    ///
    /// Opaque elements are never inspected or modified. The validation pass completes before the
    /// mutation pass, so a dangling reference leaves the whole flow unchanged.
    ///
    /// # Errors
    ///
    /// Rejects a malformed mapping or a typed reference outside the original style domain.
    pub fn rewrite_text_flow(&self, flow: &mut TextFlow) -> Result<(), CharacterStyleError> {
        self.validate_mapping()?;
        for child in &flow.children {
            let ParagraphChild::Run(run) = child else {
                continue;
            };
            validate_mapped_reference(&self.old_to_new, run.character_property_id_ref)?;
            for item in &run.items {
                if let TextRunItem::Text(span) = item {
                    validate_mapped_reference(&self.old_to_new, span.character_style_id_ref)?;
                }
            }
        }
        for child in &mut flow.children {
            let ParagraphChild::Run(run) = child else {
                continue;
            };
            rewrite_mapped_reference(&self.old_to_new, &mut run.character_property_id_ref)?;
            for item in &mut run.items {
                if let TextRunItem::Text(span) = item {
                    rewrite_mapped_reference(&self.old_to_new, &mut span.character_style_id_ref)?;
                }
            }
        }
        Ok(())
    }

    fn validate_mapping(&self) -> Result<(), CharacterStyleError> {
        if self.styles.is_empty() || self.old_to_new.is_empty() {
            return Err(CharacterStyleError::InvalidId);
        }
        for (position, style) in self.styles.iter().enumerate() {
            if style.id != u32::try_from(position).map_err(|_| CharacterStyleError::InvalidId)? {
                return Err(CharacterStyleError::InvalidId);
            }
        }
        let style_count =
            u32::try_from(self.styles.len()).map_err(|_| CharacterStyleError::InvalidId)?;
        if self.old_to_new.iter().any(|mapped| *mapped >= style_count) {
            return Err(CharacterStyleError::InvalidId);
        }
        Ok(())
    }
}

fn validate_mapped_reference(
    mapping: &[u32],
    reference: Option<u32>,
) -> Result<(), CharacterStyleError> {
    if let Some(reference) = reference {
        let index =
            usize::try_from(reference).map_err(|_| CharacterStyleError::DanglingReference)?;
        if index >= mapping.len() {
            return Err(CharacterStyleError::DanglingReference);
        }
    }
    Ok(())
}

fn rewrite_mapped_reference(
    mapping: &[u32],
    reference: &mut Option<u32>,
) -> Result<(), CharacterStyleError> {
    if let Some(value) = *reference {
        let index = usize::try_from(value).map_err(|_| CharacterStyleError::DanglingReference)?;
        let mapped = mapping
            .get(index)
            .copied()
            .ok_or(CharacterStyleError::DanglingReference)?;
        *reference = Some(mapped);
    }
    Ok(())
}

fn read_font_faces(
    document: &PreservingXmlDocument,
    index: usize,
    limits: CharacterStyleLimits,
) -> Result<Vec<FontFaceGroup>, CharacterStyleError> {
    let container = element(document, index)?;
    validate_attributes(container, &["itemCnt"])?;
    let declared = required_usize(container, "itemCnt")?;
    if declared != LANGUAGE_SLOTS.len() {
        return Err(CharacterStyleError::CountMismatch);
    }
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != LANGUAGE_SLOTS.len() {
        return Err(CharacterStyleError::CountMismatch);
    }
    let mut groups = Vec::new();
    groups
        .try_reserve_exact(LANGUAGE_SLOTS.len())
        .map_err(|_| CharacterStyleError::AllocationFailed)?;
    for (position, child_index) in children.into_iter().enumerate() {
        let language = LANGUAGE_SLOTS[position];
        let group = element(document, child_index)?;
        require_name(group, "fontface")?;
        validate_attributes(group, &["lang", "fontCnt"])?;
        if required_attribute(group, "lang")? != language.upper() {
            return Err(CharacterStyleError::UnsupportedShape);
        }
        let declared_fonts = required_usize(group, "fontCnt")?;
        if declared_fonts == 0 || declared_fonts > limits.config().fonts_per_language {
            return Err(CharacterStyleError::FontLimit);
        }
        require_only_whitespace_content(document, child_index)?;
        let font_indexes = child_indexes(document, child_index)?;
        if font_indexes.len() != declared_fonts {
            return Err(CharacterStyleError::CountMismatch);
        }
        let mut fonts = Vec::new();
        fonts
            .try_reserve_exact(declared_fonts)
            .map_err(|_| CharacterStyleError::AllocationFailed)?;
        for (font_position, font_index) in font_indexes.into_iter().enumerate() {
            let font = read_font(document, font_index, limits)?;
            let expected =
                u32::try_from(font_position).map_err(|_| CharacterStyleError::InvalidId)?;
            if font.id != expected {
                return Err(CharacterStyleError::InvalidId);
            }
            fonts.push(font);
        }
        groups.push(FontFaceGroup { language, fonts });
    }
    Ok(groups)
}

fn read_font(
    document: &PreservingXmlDocument,
    index: usize,
    limits: CharacterStyleLimits,
) -> Result<FontFace, CharacterStyleError> {
    let element = element(document, index)?;
    require_name(element, "font")?;
    validate_attributes(
        element,
        &["id", "face", "type", "isEmbedded", "binaryItemIDRef"],
    )?;
    let face = read_bounded_string(element, "face", limits)?;
    let binary_item_id_ref = read_optional_bounded_string(element, "binaryItemIDRef", limits)?;
    let is_embedded = required_bool(element, "isEmbedded")?;
    if is_embedded && binary_item_id_ref.is_none() {
        return Err(CharacterStyleError::DanglingReference);
    }
    require_only_whitespace_content(document, index)?;
    let mut substitute = None;
    let mut type_info = None;
    let mut last_rank = 0_u8;
    for child_index in child_indexes(document, index)? {
        let child = crate::character_style::element(document, child_index)?;
        let rank = match child.name().local_name() {
            "substFont" if has_name(child, "substFont") => {
                if substitute.is_some() {
                    return Err(CharacterStyleError::UnsupportedShape);
                }
                substitute = Some(read_substitute_font(child, limits)?);
                1
            }
            "typeInfo" if has_name(child, "typeInfo") => {
                if type_info.is_some() {
                    return Err(CharacterStyleError::UnsupportedShape);
                }
                type_info = Some(read_type_info(document, child_index, limits)?);
                2
            }
            _ => return Err(CharacterStyleError::UnsupportedShape),
        };
        if rank < last_rank {
            return Err(CharacterStyleError::UnsupportedShape);
        }
        last_rank = rank;
    }
    Ok(FontFace {
        id: required_u32(element, "id")?,
        face,
        font_type: FontType::parse(required_attribute(element, "type")?)?,
        is_embedded,
        binary_item_id_ref,
        substitute,
        type_info,
    })
}

fn read_substitute_font(
    element: &XmlElementToken,
    limits: CharacterStyleLimits,
) -> Result<SubstituteFont, CharacterStyleError> {
    validate_attributes(element, &["face", "type", "binaryItemIDRef"])?;
    if !element.is_empty() {
        return Err(CharacterStyleError::UnsupportedShape);
    }
    Ok(SubstituteFont {
        face: read_bounded_string(element, "face", limits)?,
        font_type: FontType::parse(required_attribute(element, "type")?)?,
        binary_item_id_ref: read_optional_bounded_string(element, "binaryItemIDRef", limits)?,
    })
}

fn read_type_info(
    document: &PreservingXmlDocument,
    index: usize,
    limits: CharacterStyleLimits,
) -> Result<FontTypeInfo, CharacterStyleError> {
    let element = element(document, index)?;
    validate_attributes(
        element,
        &[
            "familyType",
            "serifStyle",
            "weight",
            "proportion",
            "contrast",
            "strokeVariation",
            "armStyle",
            "letterform",
            "midline",
            "xHeight",
        ],
    )?;
    require_no_children(document, index)?;
    Ok(FontTypeInfo {
        family: FontFamily::parse(required_attribute(element, "familyType")?)?,
        serif_style: read_optional_bounded_string(element, "serifStyle", limits)?,
        weight: required_i32(element, "weight")?,
        proportion: required_i32(element, "proportion")?,
        contrast: required_i32(element, "contrast")?,
        stroke_variation: required_i32(element, "strokeVariation")?,
        arm_style: required_binary_property(element, "armStyle")?,
        letterform: required_binary_property(element, "letterform")?,
        midline: required_binary_property(element, "midline")?,
        x_height: required_binary_property(element, "xHeight")?,
    })
}

fn read_character_styles(
    document: &PreservingXmlDocument,
    index: usize,
    font_faces: &[FontFaceGroup],
    limits: CharacterStyleLimits,
) -> Result<Vec<CharacterStyle>, CharacterStyleError> {
    let container = element(document, index)?;
    validate_attributes(container, &["itemCnt"])?;
    let declared = required_usize(container, "itemCnt")?;
    if declared == 0 || declared > limits.config().styles {
        return Err(CharacterStyleError::StyleLimit);
    }
    require_only_whitespace_content(document, index)?;
    let children = child_indexes(document, index)?;
    if children.len() != declared {
        return Err(CharacterStyleError::CountMismatch);
    }
    let mut styles = Vec::new();
    styles
        .try_reserve_exact(declared)
        .map_err(|_| CharacterStyleError::AllocationFailed)?;
    for (position, child_index) in children.into_iter().enumerate() {
        let style = read_character_style(document, child_index)?;
        let expected = u32::try_from(position).map_err(|_| CharacterStyleError::InvalidId)?;
        if style.id != expected {
            return Err(CharacterStyleError::InvalidId);
        }
        validate_font_references(&style.font_refs, font_faces)?;
        styles.push(style);
    }
    Ok(styles)
}

fn read_character_style(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<CharacterStyle, CharacterStyleError> {
    let element = element(document, index)?;
    require_name(element, "charPr")?;
    validate_attributes(
        element,
        &[
            "id",
            "height",
            "textColor",
            "shadeColor",
            "useFontSpace",
            "useKerning",
            "symMark",
            "borderFillIDRef",
        ],
    )?;
    require_only_whitespace_content(document, index)?;
    let children = read_style_children(document, index)?;
    let height = required_u32(element, "height")?;
    if !(1..=100_000).contains(&height) {
        return Err(CharacterStyleError::OutOfRange);
    }
    Ok(CharacterStyle {
        id: required_u32(element, "id")?,
        height,
        text_color: Color::parse(required_attribute(element, "textColor")?)?,
        shade_color: Color::parse(required_attribute(element, "shadeColor")?)?,
        use_font_space: required_bool(element, "useFontSpace")?,
        use_kerning: required_bool(element, "useKerning")?,
        emphasis_mark: EmphasisMark::parse(required_attribute(element, "symMark")?)?,
        border_fill_id_ref: optional_u32(element, "borderFillIDRef")?,
        font_refs: children.font_refs,
        ratios: children.ratios,
        spacing: children.spacing,
        relative_sizes: children.relative_sizes,
        offsets: children.offsets,
        effects: children.effects,
    })
}

struct ParsedStyleChildren {
    font_refs: LanguageValues<u32>,
    ratios: LanguageValues<u16>,
    spacing: LanguageValues<i16>,
    relative_sizes: LanguageValues<u16>,
    offsets: LanguageValues<i16>,
    effects: CharacterEffects,
}

fn read_style_children(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<ParsedStyleChildren, CharacterStyleError> {
    let mut font_refs = None;
    let mut ratios = None;
    let mut spacing = None;
    let mut relative_sizes = None;
    let mut offsets = None;
    let mut effects = CharacterEffects::default();
    let mut seen_effects = [false; 10];
    let mut last_rank = 0_u8;
    for child_index in child_indexes(document, index)? {
        let child = crate::character_style::element(document, child_index)?;
        let rank = if has_name(child, "fontRef") {
            if font_refs.is_some() {
                return Err(CharacterStyleError::UnsupportedShape);
            }
            font_refs = Some(read_language_u32(document, child_index)?);
            1
        } else if has_name(child, "ratio") {
            if ratios.is_some() {
                return Err(CharacterStyleError::UnsupportedShape);
            }
            ratios = Some(read_language_u16(document, child_index, 50, 200)?);
            2
        } else if has_name(child, "spacing") {
            if spacing.is_some() {
                return Err(CharacterStyleError::UnsupportedShape);
            }
            spacing = Some(read_language_i16(
                document,
                child_index,
                LanguageRange::Uniform(-50, 50),
            )?);
            3
        } else if has_name(child, "relSz") {
            if relative_sizes.is_some() {
                return Err(CharacterStyleError::UnsupportedShape);
            }
            relative_sizes = Some(read_language_u16(document, child_index, 10, 250)?);
            4
        } else if has_name(child, "offset") {
            if offsets.is_some() {
                return Err(CharacterStyleError::UnsupportedShape);
            }
            offsets = Some(read_language_i16(
                document,
                child_index,
                LanguageRange::Offset,
            )?);
            5
        } else {
            read_effect(document, child_index, &mut effects, &mut seen_effects)?
        };
        if rank < last_rank {
            return Err(CharacterStyleError::UnsupportedShape);
        }
        last_rank = rank;
    }
    let Some(font_refs) = font_refs else {
        return Err(CharacterStyleError::UnsupportedShape);
    };
    let Some(ratios) = ratios else {
        return Err(CharacterStyleError::UnsupportedShape);
    };
    let Some(spacing) = spacing else {
        return Err(CharacterStyleError::UnsupportedShape);
    };
    let Some(relative_sizes) = relative_sizes else {
        return Err(CharacterStyleError::UnsupportedShape);
    };
    let Some(offsets) = offsets else {
        return Err(CharacterStyleError::UnsupportedShape);
    };
    Ok(ParsedStyleChildren {
        font_refs,
        ratios,
        spacing,
        relative_sizes,
        offsets,
        effects,
    })
}

fn read_effect(
    document: &PreservingXmlDocument,
    index: usize,
    effects: &mut CharacterEffects,
    seen: &mut [bool; 10],
) -> Result<u8, CharacterStyleError> {
    let element = element(document, index)?;
    let (rank, seen_index) = match element.name().local_name() {
        "italic" if has_name(element, "italic") => {
            effects.italic = BinaryProperty::On;
            (6, 0)
        }
        "bold" if has_name(element, "bold") => {
            effects.bold = BinaryProperty::On;
            (7, 1)
        }
        "underline" if has_name(element, "underline") => {
            validate_attributes(element, &["type", "shape", "color"])?;
            effects.underline = Underline {
                position: UnderlinePosition::parse(required_attribute(element, "type")?)?,
                shape: LineType2::parse(required_attribute(element, "shape")?)?,
                color: Color::parse(required_attribute(element, "color")?)?,
            };
            (8, 2)
        }
        "strikeout" if has_name(element, "strikeout") => {
            validate_attributes(element, &["shape", "color"])?;
            effects.strikeout = Strikeout {
                shape: LineType2::parse(required_attribute(element, "shape")?)?,
                color: Color::parse(required_attribute(element, "color")?)?,
            };
            (9, 3)
        }
        "outline" if has_name(element, "outline") => {
            validate_attributes(element, &["type"])?;
            effects.outline = LineType1::parse(required_attribute(element, "type")?)?;
            (10, 4)
        }
        "shadow" if has_name(element, "shadow") => {
            validate_attributes(element, &["type", "color", "offsetX", "offsetY"])?;
            let offset_x = required_i16(element, "offsetX")?;
            let offset_y = required_i16(element, "offsetY")?;
            if !(-100..=100).contains(&offset_x) || !(-100..=100).contains(&offset_y) {
                return Err(CharacterStyleError::OutOfRange);
            }
            effects.shadow = Shadow {
                shadow_type: ShadowType::parse(required_attribute(element, "type")?)?,
                color: Color::parse(required_attribute(element, "color")?)?,
                offset_x,
                offset_y,
            };
            (11, 5)
        }
        "emboss" if has_name(element, "emboss") => {
            effects.emboss = BinaryProperty::On;
            (12, 6)
        }
        "engrave" if has_name(element, "engrave") => {
            effects.engrave = BinaryProperty::On;
            (13, 7)
        }
        "supscript" if has_name(element, "supscript") => {
            effects.superscript = BinaryProperty::On;
            (14, 8)
        }
        "subscript" if has_name(element, "subscript") => {
            effects.subscript = BinaryProperty::On;
            (15, 9)
        }
        _ => return Err(CharacterStyleError::UnsupportedShape),
    };
    if seen[seen_index] {
        return Err(CharacterStyleError::UnsupportedShape);
    }
    seen[seen_index] = true;
    require_no_children(document, index)?;
    if !matches!(seen_index, 2..=5) {
        validate_attributes(element, &[])?;
    }
    Ok(rank)
}

fn read_language_u32(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<LanguageValues<u32>, CharacterStyleError> {
    let element = element(document, index)?;
    validate_language_element(document, index)?;
    Ok(LanguageValues {
        hangul: required_u32(element, "hangul")?,
        latin: required_u32(element, "latin")?,
        hanja: required_u32(element, "hanja")?,
        japanese: required_u32(element, "japanese")?,
        other: required_u32(element, "other")?,
        symbol: required_u32(element, "symbol")?,
        user: required_u32(element, "user")?,
    })
}

fn read_language_u16(
    document: &PreservingXmlDocument,
    index: usize,
    minimum: u16,
    maximum: u16,
) -> Result<LanguageValues<u16>, CharacterStyleError> {
    let element = element(document, index)?;
    validate_language_element(document, index)?;
    let read = |name| -> Result<u16, CharacterStyleError> {
        let value = required_u16(element, name)?;
        if !(minimum..=maximum).contains(&value) {
            return Err(CharacterStyleError::OutOfRange);
        }
        Ok(value)
    };
    Ok(LanguageValues {
        hangul: read("hangul")?,
        latin: read("latin")?,
        hanja: read("hanja")?,
        japanese: read("japanese")?,
        other: read("other")?,
        symbol: read("symbol")?,
        user: read("user")?,
    })
}

#[derive(Clone, Copy)]
enum LanguageRange {
    Uniform(i16, i16),
    Offset,
}

fn read_language_i16(
    document: &PreservingXmlDocument,
    index: usize,
    range: LanguageRange,
) -> Result<LanguageValues<i16>, CharacterStyleError> {
    let element = element(document, index)?;
    validate_language_element(document, index)?;
    let read = |slot: LanguageSlot| -> Result<i16, CharacterStyleError> {
        let value = required_i16(element, slot.lower())?;
        let (minimum, maximum) = match range {
            LanguageRange::Uniform(minimum, maximum) => (minimum, maximum),
            LanguageRange::Offset
                if matches!(
                    slot,
                    LanguageSlot::Hangul | LanguageSlot::Latin | LanguageSlot::Hanja
                ) =>
            {
                (-100, 100)
            }
            LanguageRange::Offset => (-100, 50),
        };
        if !(minimum..=maximum).contains(&value) {
            return Err(CharacterStyleError::OutOfRange);
        }
        Ok(value)
    };
    Ok(LanguageValues {
        hangul: read(LanguageSlot::Hangul)?,
        latin: read(LanguageSlot::Latin)?,
        hanja: read(LanguageSlot::Hanja)?,
        japanese: read(LanguageSlot::Japanese)?,
        other: read(LanguageSlot::Other)?,
        symbol: read(LanguageSlot::Symbol)?,
        user: read(LanguageSlot::User)?,
    })
}

fn validate_language_element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), CharacterStyleError> {
    let element = element(document, index)?;
    validate_attributes(
        element,
        &[
            "hangul", "latin", "hanja", "japanese", "other", "symbol", "user",
        ],
    )?;
    require_no_children(document, index)
}

fn validate_catalog(
    catalog: &CharacterStyleCatalog,
    limits: CharacterStyleLimits,
) -> Result<(), CharacterStyleError> {
    if catalog.font_faces.len() != LANGUAGE_SLOTS.len() {
        return Err(CharacterStyleError::CountMismatch);
    }
    for (position, group) in catalog.font_faces.iter().enumerate() {
        if group.language != LANGUAGE_SLOTS[position] {
            return Err(CharacterStyleError::UnsupportedShape);
        }
        if group.fonts.is_empty() || group.fonts.len() > limits.config().fonts_per_language {
            return Err(CharacterStyleError::FontLimit);
        }
        for (font_position, font) in group.fonts.iter().enumerate() {
            if font.id
                != u32::try_from(font_position).map_err(|_| CharacterStyleError::InvalidId)?
            {
                return Err(CharacterStyleError::InvalidId);
            }
            validate_string(&font.face, limits)?;
            validate_optional_string(font.binary_item_id_ref.as_deref(), limits)?;
            if font.is_embedded && font.binary_item_id_ref.is_none() {
                return Err(CharacterStyleError::DanglingReference);
            }
            if let Some(substitute) = &font.substitute {
                validate_string(&substitute.face, limits)?;
                validate_optional_string(substitute.binary_item_id_ref.as_deref(), limits)?;
            }
            if let Some(type_info) = &font.type_info {
                validate_optional_string(type_info.serif_style.as_deref(), limits)?;
            }
        }
    }
    if catalog.styles.is_empty() || catalog.styles.len() > limits.config().styles {
        return Err(CharacterStyleError::StyleLimit);
    }
    for (position, style) in catalog.styles.iter().enumerate() {
        if style.id != u32::try_from(position).map_err(|_| CharacterStyleError::InvalidId)? {
            return Err(CharacterStyleError::InvalidId);
        }
        if !(1..=100_000).contains(&style.height) {
            return Err(CharacterStyleError::OutOfRange);
        }
        if matches!(style.text_color, Color::None)
            || matches!(style.effects.underline.color, Color::None)
            || matches!(style.effects.strikeout.color, Color::None)
            || matches!(style.effects.shadow.color, Color::None)
        {
            return Err(CharacterStyleError::InvalidColor);
        }
        validate_font_references(&style.font_refs, &catalog.font_faces)?;
        validate_language_values(&style.ratios, 50, 200)?;
        validate_language_values(&style.relative_sizes, 10, 250)?;
        validate_signed_language_values(&style.spacing, LanguageRange::Uniform(-50, 50))?;
        validate_signed_language_values(&style.offsets, LanguageRange::Offset)?;
        if !(-100..=100).contains(&style.effects.shadow.offset_x)
            || !(-100..=100).contains(&style.effects.shadow.offset_y)
            || (style.effects.superscript.is_on() && style.effects.subscript.is_on())
        {
            return Err(CharacterStyleError::OutOfRange);
        }
    }
    Ok(())
}

fn validate_font_references(
    values: &LanguageValues<u32>,
    groups: &[FontFaceGroup],
) -> Result<(), CharacterStyleError> {
    if groups.len() != LANGUAGE_SLOTS.len() {
        return Err(CharacterStyleError::CountMismatch);
    }
    for (position, slot) in LANGUAGE_SLOTS.into_iter().enumerate() {
        let reference = usize::try_from(*values.get(slot))
            .map_err(|_| CharacterStyleError::DanglingReference)?;
        if reference >= groups[position].fonts.len() {
            return Err(CharacterStyleError::DanglingReference);
        }
    }
    Ok(())
}

fn validate_language_values(
    values: &LanguageValues<u16>,
    minimum: u16,
    maximum: u16,
) -> Result<(), CharacterStyleError> {
    for slot in LANGUAGE_SLOTS {
        if !(minimum..=maximum).contains(values.get(slot)) {
            return Err(CharacterStyleError::OutOfRange);
        }
    }
    Ok(())
}

fn validate_signed_language_values(
    values: &LanguageValues<i16>,
    range: LanguageRange,
) -> Result<(), CharacterStyleError> {
    for slot in LANGUAGE_SLOTS {
        let (minimum, maximum) = match range {
            LanguageRange::Uniform(minimum, maximum) => (minimum, maximum),
            LanguageRange::Offset
                if matches!(
                    slot,
                    LanguageSlot::Hangul | LanguageSlot::Latin | LanguageSlot::Hanja
                ) =>
            {
                (-100, 100)
            }
            LanguageRange::Offset => (-100, 50),
        };
        if !(minimum..=maximum).contains(values.get(slot)) {
            return Err(CharacterStyleError::OutOfRange);
        }
    }
    Ok(())
}

fn validate_string(value: &str, limits: CharacterStyleLimits) -> Result<(), CharacterStyleError> {
    if value.is_empty()
        || value.len() > limits.config().string_bytes
        || value.chars().any(|character| {
            character.is_control() || matches!(character as u32 & 0xffff, 0xfffe | 0xffff)
        })
    {
        return Err(CharacterStyleError::InvalidString);
    }
    Ok(())
}

fn validate_optional_string(
    value: Option<&str>,
    limits: CharacterStyleLimits,
) -> Result<(), CharacterStyleError> {
    if let Some(value) = value {
        validate_string(value, limits)?;
    }
    Ok(())
}

fn write_font_faces(
    output: &mut BoundedXml,
    groups: &[FontFaceGroup],
) -> Result<(), CharacterStyleError> {
    output.push("<hh:fontfaces itemCnt=\"")?;
    output.push_usize(groups.len())?;
    output.push("\">")?;
    for group in groups {
        output.push("<hh:fontface lang=\"")?;
        output.push(group.language.upper())?;
        output.push("\" fontCnt=\"")?;
        output.push_usize(group.fonts.len())?;
        output.push("\">")?;
        for font in &group.fonts {
            write_font(output, font)?;
        }
        output.push("</hh:fontface>")?;
    }
    output.push("</hh:fontfaces>")
}

fn write_font(output: &mut BoundedXml, font: &FontFace) -> Result<(), CharacterStyleError> {
    output.push("<hh:font id=\"")?;
    output.push_u32(font.id)?;
    output.push("\" face=\"")?;
    output.escaped(&font.face)?;
    output.push("\" type=\"")?;
    output.push(font.font_type.as_str())?;
    output.push("\" isEmbedded=\"")?;
    output.push_bool(font.is_embedded)?;
    output.optional_escaped_attribute(" binaryItemIDRef=\"", font.binary_item_id_ref.as_deref())?;
    if font.substitute.is_none() && font.type_info.is_none() {
        return output.push("/>");
    }
    output.push(">")?;
    if let Some(substitute) = &font.substitute {
        output.push("<hh:substFont face=\"")?;
        output.escaped(&substitute.face)?;
        output.push("\" type=\"")?;
        output.push(substitute.font_type.as_str())?;
        output.push("\"")?;
        output.optional_escaped_attribute(
            " binaryItemIDRef=\"",
            substitute.binary_item_id_ref.as_deref(),
        )?;
        output.push("/>")?;
    }
    if let Some(info) = &font.type_info {
        write_type_info(output, info)?;
    }
    output.push("</hh:font>")
}

fn write_type_info(
    output: &mut BoundedXml,
    info: &FontTypeInfo,
) -> Result<(), CharacterStyleError> {
    output.push("<hh:typeInfo familyType=\"")?;
    output.push(info.family.as_str())?;
    output.push("\"")?;
    output.optional_escaped_attribute(" serifStyle=\"", info.serif_style.as_deref())?;
    output.push(" weight=\"")?;
    output.push_i32(info.weight)?;
    output.push("\" proportion=\"")?;
    output.push_i32(info.proportion)?;
    output.push("\" contrast=\"")?;
    output.push_i32(info.contrast)?;
    output.push("\" strokeVariation=\"")?;
    output.push_i32(info.stroke_variation)?;
    output.push("\" armStyle=\"")?;
    output.push_bool(info.arm_style.is_on())?;
    output.push(" letterform=\"")?;
    output.push_bool(info.letterform.is_on())?;
    output.push(" midline=\"")?;
    output.push_bool(info.midline.is_on())?;
    output.push(" xHeight=\"")?;
    output.push_bool(info.x_height.is_on())?;
    output.push("/>")
}

fn write_character_styles(
    output: &mut BoundedXml,
    styles: &[CharacterStyle],
) -> Result<(), CharacterStyleError> {
    output.push("<hh:charProperties itemCnt=\"")?;
    output.push_usize(styles.len())?;
    output.push("\">")?;
    for style in styles {
        write_character_style(output, style)?;
    }
    output.push("</hh:charProperties>")
}

fn write_character_style(
    output: &mut BoundedXml,
    style: &CharacterStyle,
) -> Result<(), CharacterStyleError> {
    output.push("<hh:charPr id=\"")?;
    output.push_u32(style.id)?;
    output.push("\" height=\"")?;
    output.push_u32(style.height)?;
    output.push("\" textColor=\"")?;
    output.push_color(style.text_color)?;
    output.push("\" shadeColor=\"")?;
    output.push_color(style.shade_color)?;
    output.push("\" useFontSpace=\"")?;
    output.push_bool(style.use_font_space)?;
    output.push(" useKerning=\"")?;
    output.push_bool(style.use_kerning)?;
    output.push(" symMark=\"")?;
    output.push(style.emphasis_mark.as_str())?;
    output.push("\"")?;
    output.optional_u32_attribute(" borderFillIDRef=\"", style.border_fill_id_ref)?;
    output.push(">")?;
    write_language_u32(output, "fontRef", &style.font_refs)?;
    write_language_u16(output, "ratio", &style.ratios)?;
    write_language_i16(output, "spacing", &style.spacing)?;
    write_language_u16(output, "relSz", &style.relative_sizes)?;
    write_language_i16(output, "offset", &style.offsets)?;
    write_effects(output, &style.effects)?;
    output.push("</hh:charPr>")
}

fn write_language_u32(
    output: &mut BoundedXml,
    name: &str,
    values: &LanguageValues<u32>,
) -> Result<(), CharacterStyleError> {
    output.push("<hh:")?;
    output.push(name)?;
    for slot in LANGUAGE_SLOTS {
        output.push(" ")?;
        output.push(slot.lower())?;
        output.push("=\"")?;
        output.push_u32(*values.get(slot))?;
        output.push("\"")?;
    }
    output.push("/>")
}

fn write_language_u16(
    output: &mut BoundedXml,
    name: &str,
    values: &LanguageValues<u16>,
) -> Result<(), CharacterStyleError> {
    output.push("<hh:")?;
    output.push(name)?;
    for slot in LANGUAGE_SLOTS {
        output.push(" ")?;
        output.push(slot.lower())?;
        output.push("=\"")?;
        output.push_u16(*values.get(slot))?;
        output.push("\"")?;
    }
    output.push("/>")
}

fn write_language_i16(
    output: &mut BoundedXml,
    name: &str,
    values: &LanguageValues<i16>,
) -> Result<(), CharacterStyleError> {
    output.push("<hh:")?;
    output.push(name)?;
    for slot in LANGUAGE_SLOTS {
        output.push(" ")?;
        output.push(slot.lower())?;
        output.push("=\"")?;
        output.push_i16(*values.get(slot))?;
        output.push("\"")?;
    }
    output.push("/>")
}

fn write_effects(
    output: &mut BoundedXml,
    effects: &CharacterEffects,
) -> Result<(), CharacterStyleError> {
    if effects.italic.is_on() {
        output.push("<hh:italic/>")?;
    }
    if effects.bold.is_on() {
        output.push("<hh:bold/>")?;
    }
    output.push("<hh:underline type=\"")?;
    output.push(effects.underline.position.as_str())?;
    output.push("\" shape=\"")?;
    output.push(effects.underline.shape.as_str())?;
    output.push("\" color=\"")?;
    output.push_color(effects.underline.color)?;
    output.push("\"/>")?;
    output.push("<hh:strikeout shape=\"")?;
    output.push(effects.strikeout.shape.as_str())?;
    output.push("\" color=\"")?;
    output.push_color(effects.strikeout.color)?;
    output.push("\"/>")?;
    output.push("<hh:outline type=\"")?;
    output.push(effects.outline.as_str())?;
    output.push("\"/>")?;
    output.push("<hh:shadow type=\"")?;
    output.push(effects.shadow.shadow_type.as_str())?;
    output.push("\" color=\"")?;
    output.push_color(effects.shadow.color)?;
    output.push("\" offsetX=\"")?;
    output.push_i16(effects.shadow.offset_x)?;
    output.push("\" offsetY=\"")?;
    output.push_i16(effects.shadow.offset_y)?;
    output.push("\"/>")?;
    if effects.emboss.is_on() {
        output.push("<hh:emboss/>")?;
    }
    if effects.engrave.is_on() {
        output.push("<hh:engrave/>")?;
    }
    if effects.superscript.is_on() {
        output.push("<hh:supscript/>")?;
    }
    if effects.subscript.is_on() {
        output.push("<hh:subscript/>")?;
    }
    Ok(())
}

struct BoundedXml {
    value: String,
    maximum: usize,
}

impl BoundedXml {
    fn new(maximum: usize) -> Result<Self, CharacterStyleError> {
        let mut value = String::new();
        value
            .try_reserve(maximum.min(16 * 1024))
            .map_err(|_| CharacterStyleError::AllocationFailed)?;
        Ok(Self { value, maximum })
    }

    fn push(&mut self, value: &str) -> Result<(), CharacterStyleError> {
        let length = self
            .value
            .len()
            .checked_add(value.len())
            .ok_or(CharacterStyleError::OutputLimit)?;
        if length > self.maximum {
            return Err(CharacterStyleError::OutputLimit);
        }
        self.value
            .try_reserve(value.len())
            .map_err(|_| CharacterStyleError::AllocationFailed)?;
        self.value.push_str(value);
        Ok(())
    }

    fn push_usize(&mut self, value: usize) -> Result<(), CharacterStyleError> {
        self.push(&value.to_string())
    }

    fn push_u32(&mut self, value: u32) -> Result<(), CharacterStyleError> {
        self.push(&value.to_string())
    }

    fn push_u16(&mut self, value: u16) -> Result<(), CharacterStyleError> {
        self.push(&value.to_string())
    }

    fn push_i32(&mut self, value: i32) -> Result<(), CharacterStyleError> {
        self.push(&value.to_string())
    }

    fn push_i16(&mut self, value: i16) -> Result<(), CharacterStyleError> {
        self.push(&value.to_string())
    }

    fn push_bool(&mut self, value: bool) -> Result<(), CharacterStyleError> {
        self.push(if value { "1\"" } else { "0\"" })
    }

    fn optional_u32_attribute(
        &mut self,
        prefix: &str,
        value: Option<u32>,
    ) -> Result<(), CharacterStyleError> {
        if let Some(value) = value {
            self.push(prefix)?;
            self.push_u32(value)?;
            self.push("\"")?;
        }
        Ok(())
    }

    fn optional_escaped_attribute(
        &mut self,
        prefix: &str,
        value: Option<&str>,
    ) -> Result<(), CharacterStyleError> {
        if let Some(value) = value {
            self.push(prefix)?;
            self.escaped(value)?;
            self.push("\"")?;
        }
        Ok(())
    }

    fn escaped(&mut self, value: &str) -> Result<(), CharacterStyleError> {
        let mut start = 0;
        for (index, character) in value.char_indices() {
            let replacement = match character {
                '&' => "&amp;",
                '<' => "&lt;",
                '>' => "&gt;",
                '"' => "&quot;",
                '\'' => "&apos;",
                _ => continue,
            };
            self.push(&value[start..index])?;
            self.push(replacement)?;
            start = index + character.len_utf8();
        }
        self.push(&value[start..])
    }

    fn push_color(&mut self, color: Color) -> Result<(), CharacterStyleError> {
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
                    std::str::from_utf8(&bytes).map_err(|_| CharacterStyleError::InvalidColor)?;
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
) -> Result<&XmlElementToken, CharacterStyleError> {
    document
        .elements()
        .get(index)
        .ok_or(CharacterStyleError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(HANCOM_2020_HEAD_NAMESPACE)
        && element.name().local_name() == local_name
}

fn require_name(element: &XmlElementToken, local_name: &str) -> Result<(), CharacterStyleError> {
    if has_name(element, local_name) {
        Ok(())
    } else {
        Err(CharacterStyleError::UnsupportedShape)
    }
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, CharacterStyleError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| CharacterStyleError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn exactly_one_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, CharacterStyleError> {
    let mut found = None;
    for index in child_indexes(document, parent)? {
        let child = element(document, index)?;
        if child.name().local_name() != local_name {
            continue;
        }
        if !has_name(child, local_name) || found.replace(index).is_some() {
            return Err(CharacterStyleError::UnsupportedShape);
        }
    }
    found.ok_or(CharacterStyleError::UnsupportedShape)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), CharacterStyleError> {
    let mut seen = Vec::<&str>::new();
    seen.try_reserve(element.attributes().len())
        .map_err(|_| CharacterStyleError::AllocationFailed)?;
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some()
            || !allowed.contains(&name)
            || seen.contains(&name)
        {
            return Err(CharacterStyleError::UnsupportedShape);
        }
        seen.push(name);
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
) -> Result<&'a str, CharacterStyleError> {
    optional_attribute(element, name).ok_or(CharacterStyleError::UnsupportedShape)
}

fn parse_u32(value: &str) -> Result<u32, CharacterStyleError> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(CharacterStyleError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| CharacterStyleError::InvalidNumber)
}

fn parse_i32(value: &str) -> Result<i32, CharacterStyleError> {
    let digits = value.strip_prefix('-').unwrap_or(value);
    if digits.is_empty() || !digits.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(CharacterStyleError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| CharacterStyleError::InvalidNumber)
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, CharacterStyleError> {
    parse_u32(required_attribute(element, name)?)
}

fn optional_u32(element: &XmlElementToken, name: &str) -> Result<Option<u32>, CharacterStyleError> {
    optional_attribute(element, name).map(parse_u32).transpose()
}

fn required_usize(element: &XmlElementToken, name: &str) -> Result<usize, CharacterStyleError> {
    usize::try_from(required_u32(element, name)?).map_err(|_| CharacterStyleError::InvalidNumber)
}

fn required_u16(element: &XmlElementToken, name: &str) -> Result<u16, CharacterStyleError> {
    u16::try_from(required_u32(element, name)?).map_err(|_| CharacterStyleError::InvalidNumber)
}

fn required_i32(element: &XmlElementToken, name: &str) -> Result<i32, CharacterStyleError> {
    parse_i32(required_attribute(element, name)?)
}

fn required_i16(element: &XmlElementToken, name: &str) -> Result<i16, CharacterStyleError> {
    i16::try_from(required_i32(element, name)?).map_err(|_| CharacterStyleError::InvalidNumber)
}

fn required_bool(element: &XmlElementToken, name: &str) -> Result<bool, CharacterStyleError> {
    match required_attribute(element, name)? {
        "1" | "true" => Ok(true),
        "0" | "false" => Ok(false),
        _ => Err(CharacterStyleError::InvalidBoolean),
    }
}

fn required_binary_property(
    element: &XmlElementToken,
    name: &str,
) -> Result<BinaryProperty, CharacterStyleError> {
    Ok(if required_bool(element, name)? {
        BinaryProperty::On
    } else {
        BinaryProperty::Off
    })
}

fn read_bounded_string(
    element: &XmlElementToken,
    name: &str,
    limits: CharacterStyleLimits,
) -> Result<String, CharacterStyleError> {
    let value = required_attribute(element, name)?;
    validate_string(value, limits)?;
    copy_string(value)
}

fn read_optional_bounded_string(
    element: &XmlElementToken,
    name: &str,
    limits: CharacterStyleLimits,
) -> Result<Option<String>, CharacterStyleError> {
    optional_attribute(element, name)
        .map(|value| {
            validate_string(value, limits)?;
            copy_string(value)
        })
        .transpose()
}

fn copy_string(value: &str) -> Result<String, CharacterStyleError> {
    let mut copy = String::new();
    copy.try_reserve_exact(value.len())
        .map_err(|_| CharacterStyleError::AllocationFailed)?;
    copy.push_str(value);
    Ok(copy)
}

fn require_no_children(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), CharacterStyleError> {
    require_only_whitespace_content(document, index)?;
    if element(document, index)?.first_child().is_some() {
        return Err(CharacterStyleError::UnsupportedShape);
    }
    Ok(())
}

fn require_only_whitespace_content(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), CharacterStyleError> {
    let element = element(document, index)?;
    if element.is_empty() {
        return Ok(());
    }
    let end = element
        .end_token()
        .ok_or(CharacterStyleError::UnsupportedShape)?;
    for token in &document.tokens()[(element.start_token() + 1)..end] {
        if token.element_index() != Some(index) {
            continue;
        }
        if matches!(
            token.kind(),
            XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment
        ) {
            return Err(CharacterStyleError::UnsupportedShape);
        }
    }
    Ok(())
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), CharacterStyleError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(CharacterStyleError::UnsupportedShape);
        }
    }
    Ok(())
}
