use std::collections::{BTreeMap, BTreeSet};
use std::fmt::{self, Write as _};

use quick_xml::escape::unescape;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::list_definition::NumberFormat;
use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken, XmlTokenKind,
};

pub const HEADER_FOOTER_PROFILE_ID: &str = "hwpx-agent.header-footer/1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const MASTER_PAGE_NS: &str = "http://www.hancom.co.kr/hwpml/2011/master-page";
const MASTER_PAGE_ROOT_NAMESPACES: &str = concat!(
    r#" xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app""#,
    r#" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph""#,
    r#" xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph""#,
    r#" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section""#,
    r#" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core""#,
    r#" xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head""#,
    r#" xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history""#,
    r#" xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page""#,
    r#" xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf""#,
    r#" xmlns:dc="http://purl.org/dc/elements/1.1/""#,
    r#" xmlns:opf="http://www.idpf.org/2007/opf/""#,
    r#" xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart""#,
    r#" xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar""#,
    r#" xmlns:epub="http://www.idpf.org/2007/ops""#,
    r#" xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0""#,
);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct HeaderFooterLimitConfig {
    pub input_bytes: usize,
    pub elements: usize,
    pub output_bytes: usize,
    pub definitions: usize,
    pub master_pages: usize,
    pub paragraphs: usize,
    pub runs: usize,
    pub inlines: usize,
    pub text_bytes: usize,
    pub identity_bytes: usize,
}

impl Default for HeaderFooterLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 4 * 1024 * 1024,
            elements: 131_072,
            output_bytes: 4 * 1024 * 1024,
            definitions: 64,
            master_pages: 64,
            paragraphs: 4_096,
            runs: 32_768,
            inlines: 131_072,
            text_bytes: 1024 * 1024,
            identity_bytes: 256,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct HeaderFooterLimits(HeaderFooterLimitConfig);

impl HeaderFooterLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 262_144;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_DEFINITIONS: usize = 256;
    pub const HARD_MAX_MASTER_PAGES: usize = 256;
    pub const HARD_MAX_PARAGRAPHS: usize = 16_384;
    pub const HARD_MAX_RUNS: usize = 131_072;
    pub const HARD_MAX_INLINES: usize = 262_144;
    pub const HARD_MAX_TEXT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_IDENTITY_BYTES: usize = 1_024;

    /// Creates finite header/footer limits.
    ///
    /// # Errors
    ///
    /// Rejects zero limits and values above the hard ceilings.
    pub fn new(config: HeaderFooterLimitConfig) -> Result<Self, HeaderFooterError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.definitions == 0
            || config.definitions > Self::HARD_MAX_DEFINITIONS
            || config.master_pages == 0
            || config.master_pages > Self::HARD_MAX_MASTER_PAGES
            || config.paragraphs == 0
            || config.paragraphs > Self::HARD_MAX_PARAGRAPHS
            || config.runs == 0
            || config.runs > Self::HARD_MAX_RUNS
            || config.inlines == 0
            || config.inlines > Self::HARD_MAX_INLINES
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.identity_bytes == 0
            || config.identity_bytes > Self::HARD_MAX_IDENTITY_BYTES
        {
            return Err(HeaderFooterError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> HeaderFooterLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum PageVariant {
    Both,
    Even,
    Odd,
}

impl PageVariant {
    fn parse(value: &str) -> Result<Self, HeaderFooterError> {
        match value {
            "BOTH" => Ok(Self::Both),
            "EVEN" => Ok(Self::Even),
            "ODD" => Ok(Self::Odd),
            _ => Err(HeaderFooterError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Both => "BOTH",
            Self::Even => "EVEN",
            Self::Odd => "ODD",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum HeaderFooterKind {
    Header,
    Footer,
}

impl HeaderFooterKind {
    const fn local_name(self) -> &'static str {
        match self {
            Self::Header => "header",
            Self::Footer => "footer",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TextDirection {
    Horizontal,
    Vertical,
    VerticalAll,
}

impl TextDirection {
    fn parse(value: &str) -> Result<Self, HeaderFooterError> {
        match value {
            "HORIZONTAL" => Ok(Self::Horizontal),
            "VERTICAL" => Ok(Self::Vertical),
            "VERTICALALL" => Ok(Self::VerticalAll),
            _ => Err(HeaderFooterError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Horizontal => "HORIZONTAL",
            Self::Vertical => "VERTICAL",
            Self::VerticalAll => "VERTICALALL",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LineWrap {
    Break,
    Squeeze,
    Keep,
}

impl LineWrap {
    fn parse(value: &str) -> Result<Self, HeaderFooterError> {
        match value {
            "BREAK" => Ok(Self::Break),
            "SQUEEZE" => Ok(Self::Squeeze),
            "KEEP" => Ok(Self::Keep),
            _ => Err(HeaderFooterError::InvalidEnum),
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum VerticalAlignment {
    Top,
    Center,
    Bottom,
}

impl VerticalAlignment {
    fn parse(value: &str) -> Result<Self, HeaderFooterError> {
        match value {
            "TOP" => Ok(Self::Top),
            "CENTER" => Ok(Self::Center),
            "BOTTOM" => Ok(Self::Bottom),
            _ => Err(HeaderFooterError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Top => "TOP",
            Self::Center => "CENTER",
            Self::Bottom => "BOTTOM",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PageFieldKind {
    Page,
    TotalPage,
}

impl PageFieldKind {
    fn parse(value: &str) -> Result<Self, HeaderFooterError> {
        match value {
            "PAGE" => Ok(Self::Page),
            "TOTAL_PAGE" => Ok(Self::TotalPage),
            _ => Err(HeaderFooterError::InvalidField),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Page => "PAGE",
            Self::TotalPage => "TOTAL_PAGE",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PageNumberPosition {
    None,
    TopLeft,
    TopCenter,
    TopRight,
    BottomLeft,
    BottomCenter,
    BottomRight,
    OutsideTop,
    OutsideBottom,
    InsideTop,
    InsideBottom,
}

impl PageNumberPosition {
    fn parse(value: &str) -> Result<Self, HeaderFooterError> {
        match value {
            "NONE" => Ok(Self::None),
            "TOP_LEFT" => Ok(Self::TopLeft),
            "TOP_CENTER" => Ok(Self::TopCenter),
            "TOP_RIGHT" => Ok(Self::TopRight),
            "BOTTOM_LEFT" => Ok(Self::BottomLeft),
            "BOTTOM_CENTER" => Ok(Self::BottomCenter),
            "BOTTOM_RIGHT" => Ok(Self::BottomRight),
            "OUTSIDE_TOP" => Ok(Self::OutsideTop),
            "OUTSIDE_BOTTOM" => Ok(Self::OutsideBottom),
            "INSIDE_TOP" => Ok(Self::InsideTop),
            "INSIDE_BOTTOM" => Ok(Self::InsideBottom),
            _ => Err(HeaderFooterError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::None => "NONE",
            Self::TopLeft => "TOP_LEFT",
            Self::TopCenter => "TOP_CENTER",
            Self::TopRight => "TOP_RIGHT",
            Self::BottomLeft => "BOTTOM_LEFT",
            Self::BottomCenter => "BOTTOM_CENTER",
            Self::BottomRight => "BOTTOM_RIGHT",
            Self::OutsideTop => "OUTSIDE_TOP",
            Self::OutsideBottom => "OUTSIDE_BOTTOM",
            Self::InsideTop => "INSIDE_TOP",
            Self::InsideBottom => "INSIDE_BOTTOM",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum MasterPageVariant {
    Both,
    Even,
    Odd,
    LastPage,
    OptionalPage,
}

impl MasterPageVariant {
    fn parse(value: &str) -> Result<Self, HeaderFooterError> {
        match value {
            "BOTH" => Ok(Self::Both),
            "EVEN" => Ok(Self::Even),
            "ODD" => Ok(Self::Odd),
            "LAST_PAGE" => Ok(Self::LastPage),
            "OPTIONAL_PAGE" => Ok(Self::OptionalPage),
            _ => Err(HeaderFooterError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Both => "BOTH",
            Self::Even => "EVEN",
            Self::Odd => "ODD",
            Self::LastPage => "LAST_PAGE",
            Self::OptionalPage => "OPTIONAL_PAGE",
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct PageField {
    pub displayed_number: i32,
    pub kind: PageFieldKind,
    pub format: NumberFormat,
    pub user_character: String,
    pub prefix: String,
    pub suffix: String,
    pub superscript: bool,
}

impl fmt::Debug for PageField {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PageField")
            .field("displayed_number", &self.displayed_number)
            .field("kind", &self.kind)
            .field("format", &self.format)
            .field("user_character_bytes", &self.user_character.len())
            .field("prefix_bytes", &self.prefix.len())
            .field("suffix_bytes", &self.suffix.len())
            .field("superscript", &self.superscript)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum HeaderFooterInline {
    Text {
        value: String,
        character_style_id_ref: Option<u32>,
    },
    Tab {
        width: u32,
        leader: u32,
        tab_type: u32,
    },
    LineBreak,
    PageField(PageField),
}

impl fmt::Debug for HeaderFooterInline {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Text {
                value,
                character_style_id_ref,
            } => formatter
                .debug_struct("Text")
                .field("value_bytes", &value.len())
                .field("character_style_id_ref", character_style_id_ref)
                .finish(),
            Self::Tab {
                width,
                leader,
                tab_type,
            } => formatter
                .debug_struct("Tab")
                .field("width", width)
                .field("leader", leader)
                .field("tab_type", tab_type)
                .finish(),
            Self::LineBreak => formatter.write_str("LineBreak"),
            Self::PageField(field) => field.fmt(formatter),
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HeaderFooterRun {
    pub character_style_id_ref: u32,
    pub inlines: Vec<HeaderFooterInline>,
}

#[derive(Clone, Eq, PartialEq)]
pub struct HeaderFooterParagraph {
    pub id: String,
    pub paragraph_property_id_ref: u32,
    pub style_id_ref: u32,
    pub page_break: bool,
    pub column_break: bool,
    pub merged: bool,
    pub runs: Vec<HeaderFooterRun>,
}

impl fmt::Debug for HeaderFooterParagraph {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HeaderFooterParagraph")
            .field("id_bytes", &self.id.len())
            .field("paragraph_property_id_ref", &self.paragraph_property_id_ref)
            .field("style_id_ref", &self.style_id_ref)
            .field("page_break", &self.page_break)
            .field("column_break", &self.column_break)
            .field("merged", &self.merged)
            .field("runs", &self.runs)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct HeaderFooterBody {
    pub id: String,
    pub text_direction: TextDirection,
    pub line_wrap: LineWrap,
    pub vertical_alignment: VerticalAlignment,
    pub link_list_id_ref: u32,
    pub link_list_next_id_ref: u32,
    pub text_width: u32,
    pub text_height: u32,
    pub has_text_reference: bool,
    pub has_number_reference: bool,
    pub paragraphs: Vec<HeaderFooterParagraph>,
}

impl fmt::Debug for HeaderFooterBody {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HeaderFooterBody")
            .field("id_bytes", &self.id.len())
            .field("text_direction", &self.text_direction)
            .field("line_wrap", &self.line_wrap)
            .field("vertical_alignment", &self.vertical_alignment)
            .field("link_list_id_ref", &self.link_list_id_ref)
            .field("link_list_next_id_ref", &self.link_list_next_id_ref)
            .field("text_width", &self.text_width)
            .field("text_height", &self.text_height)
            .field("has_text_reference", &self.has_text_reference)
            .field("has_number_reference", &self.has_number_reference)
            .field("paragraphs", &self.paragraphs)
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HeaderFooterDefinition {
    pub id: u32,
    pub kind: HeaderFooterKind,
    pub applies_to: PageVariant,
    pub body: HeaderFooterBody,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PageNumberRestart {
    pub page_starts_on: PageVariant,
    pub page: u32,
    pub picture: u32,
    pub table: u32,
    pub equation: u32,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum FirstPageDisplay {
    Show,
    Hide,
}

impl FirstPageDisplay {
    #[must_use]
    pub const fn is_hidden(self) -> bool {
        matches!(self, Self::Hide)
    }

    #[must_use]
    pub const fn from_hidden(value: bool) -> Self {
        if value { Self::Hide } else { Self::Show }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FirstPageVisibility {
    pub header: FirstPageDisplay,
    pub footer: FirstPageDisplay,
    pub master_page: FirstPageDisplay,
    pub page_number: FirstPageDisplay,
}

#[derive(Clone, Eq, PartialEq)]
pub struct PageNumberPlacement {
    pub position: PageNumberPosition,
    pub format: NumberFormat,
    pub side_character: String,
}

impl fmt::Debug for PageNumberPlacement {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PageNumberPlacement")
            .field("position", &self.position)
            .field("format", &self.format)
            .field("side_character_bytes", &self.side_character.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct MasterPageDefinition {
    pub id: String,
    pub applies_to: MasterPageVariant,
    pub optional_page_number: Option<u32>,
    pub duplicate_on_page: bool,
    pub in_front: bool,
    pub body: HeaderFooterBody,
}

impl fmt::Debug for MasterPageDefinition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("MasterPageDefinition")
            .field("id_bytes", &self.id.len())
            .field("applies_to", &self.applies_to)
            .field("optional_page_number", &self.optional_page_number)
            .field("duplicate_on_page", &self.duplicate_on_page)
            .field("in_front", &self.in_front)
            .field("body", &self.body)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct SectionPagePolicy {
    pub restart: PageNumberRestart,
    pub first_page: FirstPageVisibility,
    pub page_starts_on: Option<PageVariant>,
    pub page_number: Option<PageNumberPlacement>,
    pub definitions: Vec<HeaderFooterDefinition>,
    pub master_page_references: Vec<String>,
    pub declared_master_page_count: u32,
}

impl fmt::Debug for SectionPagePolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SectionPagePolicy")
            .field("restart", &self.restart)
            .field("first_page", &self.first_page)
            .field("page_starts_on", &self.page_starts_on)
            .field("page_number", &self.page_number)
            .field("definitions", &self.definitions)
            .field(
                "master_page_reference_count",
                &self.master_page_references.len(),
            )
            .field(
                "declared_master_page_count",
                &self.declared_master_page_count,
            )
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HeaderFooterLoweringReceipt {
    pub profile_id: &'static str,
    pub sha256: [u8; 32],
    pub output_bytes: usize,
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum HeaderFooterError {
    #[error("header/footer limits are invalid")]
    InvalidLimit,
    #[error("header/footer input exceeds its finite limit")]
    InputLimit,
    #[error("header/footer element count exceeds its finite limit")]
    ElementLimit,
    #[error("header/footer definition count exceeds its finite limit")]
    DefinitionLimit,
    #[error("master-page count exceeds its finite limit")]
    MasterPageLimit,
    #[error("header/footer paragraph count exceeds its finite limit")]
    ParagraphLimit,
    #[error("header/footer run count exceeds its finite limit")]
    RunLimit,
    #[error("header/footer inline count exceeds its finite limit")]
    InlineLimit,
    #[error("header/footer text exceeds its finite limit")]
    TextLimit,
    #[error("header/footer output exceeds its finite limit")]
    OutputLimit,
    #[error("header/footer XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("header/footer root is not in the current profile")]
    WrongRoot,
    #[error("header/footer element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("header/footer numeric value is invalid")]
    InvalidNumber,
    #[error("header/footer boolean value is invalid")]
    InvalidBoolean,
    #[error("header/footer enum value is invalid")]
    InvalidEnum,
    #[error("header/footer identity is invalid")]
    InvalidIdentity,
    #[error("header/footer text is invalid")]
    InvalidText,
    #[error("header/footer page field is invalid")]
    InvalidField,
    #[error("header/footer variant or identity is duplicated")]
    DuplicateDefinition,
    #[error("master-page relationship is dangling or inconsistent")]
    MasterPageReference,
    #[error("header/footer allocation failed")]
    AllocationFailed,
    #[error("header/footer semantic readback differs")]
    ReadbackMismatch,
}

impl HeaderFooterError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "header_footer_invalid_limit",
            Self::InputLimit => "header_footer_input_limit",
            Self::ElementLimit => "header_footer_element_limit",
            Self::DefinitionLimit => "header_footer_definition_limit",
            Self::MasterPageLimit => "header_footer_master_page_limit",
            Self::ParagraphLimit => "header_footer_paragraph_limit",
            Self::RunLimit => "header_footer_run_limit",
            Self::InlineLimit => "header_footer_inline_limit",
            Self::TextLimit => "header_footer_text_limit",
            Self::OutputLimit => "header_footer_output_limit",
            Self::Preserving(_) => "header_footer_preserving_xml",
            Self::WrongRoot => "header_footer_wrong_root",
            Self::UnsupportedShape => "header_footer_unsupported_shape",
            Self::InvalidNumber => "header_footer_invalid_number",
            Self::InvalidBoolean => "header_footer_invalid_boolean",
            Self::InvalidEnum => "header_footer_invalid_enum",
            Self::InvalidIdentity => "header_footer_invalid_identity",
            Self::InvalidText => "header_footer_invalid_text",
            Self::InvalidField => "header_footer_invalid_field",
            Self::DuplicateDefinition => "header_footer_duplicate_definition",
            Self::MasterPageReference => "header_footer_master_page_reference",
            Self::AllocationFailed => "header_footer_allocation_failed",
            Self::ReadbackMismatch => "header_footer_readback_mismatch",
        }
    }
}

#[derive(Debug)]
pub struct HeaderFooterReader;

impl HeaderFooterReader {
    /// Reads one standalone current-profile `header` or `footer` definition.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, ambiguous, or unbounded content.
    pub fn read_definition(
        bytes: &[u8],
        limits: HeaderFooterLimits,
    ) -> Result<HeaderFooterDefinition, HeaderFooterError> {
        let document = parse_document(bytes, limits)?;
        let root = document.root_element();
        let value = read_definition_at(&document, root, limits)?;
        validate_definition(&value, limits)?;
        Ok(value)
    }

    /// Reads one standalone current-profile master-page part.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, ambiguous, or unbounded content.
    pub fn read_master_page(
        bytes: &[u8],
        limits: HeaderFooterLimits,
    ) -> Result<MasterPageDefinition, HeaderFooterError> {
        let document = parse_document(bytes, limits)?;
        let root = document.root_element();
        let value = read_master_page_at(&document, root, limits)?;
        validate_master_page(&value, limits)?;
        Ok(value)
    }

    /// Reads section-scoped header/footer, restart, page-number, and master-page link policy.
    ///
    /// # Errors
    ///
    /// Requires the current section structure and rejects duplicate controls or inconsistent
    /// master-page counts before returning a partial policy.
    pub fn read_section(
        bytes: &[u8],
        limits: HeaderFooterLimits,
    ) -> Result<SectionPagePolicy, HeaderFooterError> {
        let document = parse_document(bytes, limits)?;
        let root = element(&document, document.root_element())?;
        if !has_name(root, SECTION_NS, "sec") {
            return Err(HeaderFooterError::WrongRoot);
        }
        let properties = read_section_properties(&document, limits)?;
        let controls = read_section_controls(&document, limits)?;
        let policy = SectionPagePolicy {
            restart: properties.restart,
            first_page: properties.first_page,
            page_starts_on: controls.page_starts_on,
            page_number: controls.page_number,
            definitions: controls.definitions,
            master_page_references: properties.master_page_references,
            declared_master_page_count: properties.declared_master_page_count,
        };
        validate_policy(&policy, limits)?;
        Ok(policy)
    }

    /// Validates section references against exact master-page definitions.
    ///
    /// # Errors
    ///
    /// Rejects duplicate definitions, dangling links, count drift, and duplicate page variants.
    pub fn validate_master_pages(
        policy: &SectionPagePolicy,
        master_pages: &[MasterPageDefinition],
        limits: HeaderFooterLimits,
    ) -> Result<(), HeaderFooterError> {
        validate_policy(policy, limits)?;
        if master_pages.len() > limits.config().master_pages
            || master_pages.len() != policy.master_page_references.len()
        {
            return Err(HeaderFooterError::MasterPageReference);
        }
        let mut by_id = BTreeMap::new();
        let mut variants = BTreeSet::new();
        for page in master_pages {
            validate_master_page(page, limits)?;
            if by_id.insert(page.id.as_str(), page).is_some()
                || !variants.insert((page.applies_to, page.optional_page_number))
            {
                return Err(HeaderFooterError::DuplicateDefinition);
            }
        }
        let mut seen = BTreeSet::new();
        for reference in &policy.master_page_references {
            if !seen.insert(reference.as_str()) || !by_id.contains_key(reference.as_str()) {
                return Err(HeaderFooterError::MasterPageReference);
            }
        }
        Ok(())
    }
}

#[derive(Debug)]
pub struct HeaderFooterLowerer;

impl HeaderFooterLowerer {
    /// Lowers one deterministic standalone header/footer and re-lifts it.
    ///
    /// # Errors
    ///
    /// Rejects invalid/unbounded definitions, output overflow, and semantic drift.
    pub fn lower_definition(
        definition: &HeaderFooterDefinition,
        limits: HeaderFooterLimits,
    ) -> Result<(Vec<u8>, HeaderFooterLoweringReceipt), HeaderFooterError> {
        validate_definition(definition, limits)?;
        let mut output = BoundedXml::new(limits.config().output_bytes)?;
        output.push("<hp:")?;
        output.push(definition.kind.local_name())?;
        output.push(" xmlns:hp=\"")?;
        output.push(PARAGRAPH_NS)?;
        output.push("\" id=\"")?;
        output.u32(definition.id)?;
        output.push("\" applyPageType=\"")?;
        output.push(definition.applies_to.as_str())?;
        output.push("\">")?;
        lower_body(&mut output, &definition.body)?;
        output.push("</hp:")?;
        output.push(definition.kind.local_name())?;
        output.push(">")?;
        let bytes = output.finish();
        if HeaderFooterReader::read_definition(&bytes, limits)? != *definition {
            return Err(HeaderFooterError::ReadbackMismatch);
        }
        let receipt = HeaderFooterLoweringReceipt {
            profile_id: HEADER_FOOTER_PROFILE_ID,
            sha256: Sha256::digest(&bytes).into(),
            output_bytes: bytes.len(),
        };
        Ok((bytes, receipt))
    }

    /// Lowers one deterministic standalone master-page and re-lifts it.
    ///
    /// # Errors
    ///
    /// Rejects invalid/unbounded definitions, output overflow, and semantic drift.
    pub fn lower_master_page(
        page: &MasterPageDefinition,
        limits: HeaderFooterLimits,
    ) -> Result<(Vec<u8>, HeaderFooterLoweringReceipt), HeaderFooterError> {
        validate_master_page(page, limits)?;
        let mut output = BoundedXml::new(limits.config().output_bytes)?;
        // Hangul's standalone master-page part uses an unqualified
        // `masterPage` document element. `hm:masterPage` is the section-level
        // reference vocabulary, not the root name used by the external part.
        output.push("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>")?;
        output.push("<masterPage")?;
        output.push(MASTER_PAGE_ROOT_NAMESPACES)?;
        output.push(" id=\"")?;
        output.escaped(&page.id)?;
        output.push("\" type=\"")?;
        output.push(page.applies_to.as_str())?;
        output.push("\" pageNumber=\"")?;
        output.u32(page.optional_page_number.unwrap_or(0))?;
        output.push("\" pageDuplicate=\"")?;
        output.bool01(page.duplicate_on_page)?;
        output.push("\" pageFront=\"")?;
        output.bool01(page.in_front)?;
        output.push("\">")?;
        lower_body(&mut output, &page.body)?;
        output.push("</masterPage>")?;
        let bytes = output.finish();
        if HeaderFooterReader::read_master_page(&bytes, limits)? != *page {
            return Err(HeaderFooterError::ReadbackMismatch);
        }
        let receipt = HeaderFooterLoweringReceipt {
            profile_id: HEADER_FOOTER_PROFILE_ID,
            sha256: Sha256::digest(&bytes).into(),
            output_bytes: bytes.len(),
        };
        Ok((bytes, receipt))
    }

    /// Lowers deterministic control fragments suitable for a current-profile section run.
    ///
    /// # Errors
    ///
    /// Rejects invalid policy and output overflow. Master-page parts are lowered separately.
    pub fn lower_section_controls(
        policy: &SectionPagePolicy,
        limits: HeaderFooterLimits,
    ) -> Result<Vec<u8>, HeaderFooterError> {
        validate_policy(policy, limits)?;
        let mut output = BoundedXml::new(limits.config().output_bytes)?;
        for definition in &policy.definitions {
            output.push("<hp:ctrl><hp:")?;
            output.push(definition.kind.local_name())?;
            output.push(" id=\"")?;
            output.u32(definition.id)?;
            output.push("\" applyPageType=\"")?;
            output.push(definition.applies_to.as_str())?;
            output.push("\">")?;
            lower_body(&mut output, &definition.body)?;
            output.push("</hp:")?;
            output.push(definition.kind.local_name())?;
            output.push("></hp:ctrl>")?;
        }
        if let Some(starts_on) = policy.page_starts_on {
            output.push("<hp:ctrl><hp:pageNumCtrl pageStartsOn=\"")?;
            output.push(starts_on.as_str())?;
            output.push("\"/></hp:ctrl>")?;
        }
        if let Some(page_number) = &policy.page_number {
            output.push("<hp:ctrl>")?;
            lower_page_number(&mut output, page_number)?;
            output.push("</hp:ctrl>")?;
        }
        Ok(output.finish())
    }

    /// Lowers the `startNum`, first-page `visibility`, and master-page link children of `secPr`.
    ///
    /// # Errors
    ///
    /// Rejects invalid policy and output overflow.
    pub fn lower_section_properties(
        policy: &SectionPagePolicy,
        limits: HeaderFooterLimits,
    ) -> Result<Vec<u8>, HeaderFooterError> {
        validate_policy(policy, limits)?;
        let mut output = BoundedXml::new(limits.config().output_bytes)?;
        let restart = policy.restart;
        output.push("<hp:startNum pageStartsOn=\"")?;
        output.push(restart.page_starts_on.as_str())?;
        output.push("\" page=\"")?;
        output.u32(restart.page)?;
        output.push("\" pic=\"")?;
        output.u32(restart.picture)?;
        output.push("\" tbl=\"")?;
        output.u32(restart.table)?;
        output.push("\" equation=\"")?;
        output.u32(restart.equation)?;
        output.push("\"/>")?;
        output.push("<hp:visibility hideFirstHeader=\"")?;
        output.bool01(policy.first_page.header.is_hidden())?;
        output.push("\" hideFirstFooter=\"")?;
        output.bool01(policy.first_page.footer.is_hidden())?;
        output.push("\" hideFirstMasterPage=\"")?;
        output.bool01(policy.first_page.master_page.is_hidden())?;
        output.push("\" hideFirstPageNum=\"")?;
        output.bool01(policy.first_page.page_number.is_hidden())?;
        output.push("\"/>")?;
        for id in &policy.master_page_references {
            output.push("<hp:masterPage idRef=\"")?;
            output.escaped(id)?;
            output.push("\"/>")?;
        }
        Ok(output.finish())
    }
}

fn parse_document(
    bytes: &[u8],
    limits: HeaderFooterLimits,
) -> Result<PreservingXmlDocument, HeaderFooterError> {
    if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
        return Err(HeaderFooterError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.config().elements {
        return Err(HeaderFooterError::ElementLimit);
    }
    validate_document_envelope(&document)?;
    Ok(document)
}

struct ParsedSectionProperties {
    restart: PageNumberRestart,
    first_page: FirstPageVisibility,
    master_page_references: Vec<String>,
    declared_master_page_count: u32,
}

fn read_section_properties(
    document: &PreservingXmlDocument,
    limits: HeaderFooterLimits,
) -> Result<ParsedSectionProperties, HeaderFooterError> {
    let sec_pr = unique_structural_element(document, PARAGRAPH_NS, "secPr", |index| {
        has_parent_chain(
            document,
            index,
            &[
                (PARAGRAPH_NS, "run"),
                (PARAGRAPH_NS, "p"),
                (SECTION_NS, "sec"),
            ],
        )
    })?;
    let sec_pr_value = element(document, sec_pr)?;
    let declared_master_page_count = optional_u32(sec_pr_value, "masterPageCnt")?.unwrap_or(0);
    for value in document.elements() {
        if !matches!(
            value.name().local_name(),
            "startNum" | "visibility" | "masterPage"
        ) {
            continue;
        }
        if value.name().namespace() != Some(PARAGRAPH_NS) || value.parent() != Some(sec_pr) {
            return Err(HeaderFooterError::UnsupportedShape);
        }
    }
    let mut restart = None;
    let mut first_page = None;
    let mut master_page_references = Vec::new();
    for child in child_indexes(document, sec_pr)? {
        let child_value = element(document, child)?;
        if has_name(child_value, PARAGRAPH_NS, "startNum") {
            if restart.replace(read_restart(child_value)?).is_some() {
                return Err(HeaderFooterError::UnsupportedShape);
            }
        } else if has_name(child_value, PARAGRAPH_NS, "visibility") {
            if first_page.replace(read_visibility(child_value)?).is_some() {
                return Err(HeaderFooterError::UnsupportedShape);
            }
        } else if has_name(child_value, PARAGRAPH_NS, "masterPage") {
            validate_attributes(child_value, &["idRef"])?;
            require_empty(child_value)?;
            if master_page_references.len() >= limits.config().master_pages {
                return Err(HeaderFooterError::MasterPageLimit);
            }
            let id = required_attribute(child_value, "idRef")?.to_owned();
            validate_identity(&id, limits, false)?;
            reserve_one(&mut master_page_references)?;
            master_page_references.push(id);
        }
    }
    Ok(ParsedSectionProperties {
        restart: restart.ok_or(HeaderFooterError::UnsupportedShape)?,
        first_page: first_page.ok_or(HeaderFooterError::UnsupportedShape)?,
        master_page_references,
        declared_master_page_count,
    })
}

struct ParsedSectionControls {
    definitions: Vec<HeaderFooterDefinition>,
    page_starts_on: Option<PageVariant>,
    page_number: Option<PageNumberPlacement>,
}

fn read_section_controls(
    document: &PreservingXmlDocument,
    limits: HeaderFooterLimits,
) -> Result<ParsedSectionControls, HeaderFooterError> {
    let mut definitions = Vec::new();
    let mut page_starts_on = None;
    let mut page_number = None;
    for (index, value) in document.elements().iter().enumerate() {
        if !matches!(
            value.name().local_name(),
            "header" | "footer" | "pageNumCtrl" | "pageNum"
        ) {
            continue;
        }
        if value.name().namespace() != Some(PARAGRAPH_NS)
            || !has_parent_chain(
                document,
                index,
                &[
                    (PARAGRAPH_NS, "ctrl"),
                    (PARAGRAPH_NS, "run"),
                    (PARAGRAPH_NS, "p"),
                    (SECTION_NS, "sec"),
                ],
            )?
        {
            return Err(HeaderFooterError::UnsupportedShape);
        }
        match value.name().local_name() {
            "header" | "footer" => {
                if definitions.len() >= limits.config().definitions {
                    return Err(HeaderFooterError::DefinitionLimit);
                }
                reserve_one(&mut definitions)?;
                definitions.push(read_definition_at(document, index, limits)?);
            }
            "pageNumCtrl" => {
                validate_attributes(value, &["pageStartsOn"])?;
                require_empty(value)?;
                let parsed = PageVariant::parse(required_attribute(value, "pageStartsOn")?)?;
                if page_starts_on.replace(parsed).is_some() {
                    return Err(HeaderFooterError::UnsupportedShape);
                }
            }
            "pageNum" => {
                let parsed = read_page_number(value, limits)?;
                if page_number.replace(parsed).is_some() {
                    return Err(HeaderFooterError::UnsupportedShape);
                }
            }
            _ => unreachable!(),
        }
    }
    Ok(ParsedSectionControls {
        definitions,
        page_starts_on,
        page_number,
    })
}

fn read_definition_at(
    document: &PreservingXmlDocument,
    index: usize,
    limits: HeaderFooterLimits,
) -> Result<HeaderFooterDefinition, HeaderFooterError> {
    let root = element(document, index)?;
    let kind = if has_name(root, PARAGRAPH_NS, "header") {
        HeaderFooterKind::Header
    } else if has_name(root, PARAGRAPH_NS, "footer") {
        HeaderFooterKind::Footer
    } else {
        return Err(HeaderFooterError::WrongRoot);
    };
    validate_attributes(root, &["id", "applyPageType"])?;
    let children = child_indexes(document, index)?;
    if children.len() != 1 || !has_name(element(document, children[0])?, PARAGRAPH_NS, "subList") {
        return Err(HeaderFooterError::UnsupportedShape);
    }
    Ok(HeaderFooterDefinition {
        id: required_u32(root, "id")?,
        kind,
        applies_to: PageVariant::parse(required_attribute(root, "applyPageType")?)?,
        body: read_body(document, children[0], limits)?,
    })
}

fn read_master_page_at(
    document: &PreservingXmlDocument,
    index: usize,
    limits: HeaderFooterLimits,
) -> Result<MasterPageDefinition, HeaderFooterError> {
    let root = element(document, index)?;
    if root.name().local_name() != "masterPage"
        || !matches!(root.name().namespace(), None | Some(MASTER_PAGE_NS))
    {
        return Err(HeaderFooterError::WrongRoot);
    }
    validate_attributes(
        root,
        &["id", "type", "pageNumber", "pageDuplicate", "pageFront"],
    )?;
    let children = child_indexes(document, index)?;
    if children.len() != 1 || !has_name(element(document, children[0])?, PARAGRAPH_NS, "subList") {
        return Err(HeaderFooterError::UnsupportedShape);
    }
    let applies_to = MasterPageVariant::parse(required_attribute(root, "type")?)?;
    let page_number = required_u32(root, "pageNumber")?;
    Ok(MasterPageDefinition {
        id: required_attribute(root, "id")?.to_owned(),
        applies_to,
        optional_page_number: if applies_to == MasterPageVariant::OptionalPage {
            Some(page_number)
        } else if page_number == 0 {
            None
        } else {
            return Err(HeaderFooterError::MasterPageReference);
        },
        duplicate_on_page: required_bool01(root, "pageDuplicate")?,
        in_front: required_bool01(root, "pageFront")?,
        body: read_body(document, children[0], limits)?,
    })
}

fn read_body(
    document: &PreservingXmlDocument,
    index: usize,
    limits: HeaderFooterLimits,
) -> Result<HeaderFooterBody, HeaderFooterError> {
    let root = element(document, index)?;
    if !has_name(root, PARAGRAPH_NS, "subList") {
        return Err(HeaderFooterError::UnsupportedShape);
    }
    validate_attributes(
        root,
        &[
            "id",
            "textDirection",
            "lineWrap",
            "vertAlign",
            "linkListIDRef",
            "linkListNextIDRef",
            "textWidth",
            "textHeight",
            "hasTextRef",
            "hasNumRef",
        ],
    )?;
    let children = child_indexes(document, index)?;
    if children.is_empty() || children.len() > limits.config().paragraphs {
        return Err(HeaderFooterError::ParagraphLimit);
    }
    let mut paragraphs = Vec::new();
    paragraphs
        .try_reserve_exact(children.len())
        .map_err(|_| HeaderFooterError::AllocationFailed)?;
    for child in children {
        paragraphs.push(read_paragraph(document, child, limits)?);
    }
    Ok(HeaderFooterBody {
        id: required_attribute(root, "id")?.to_owned(),
        text_direction: TextDirection::parse(required_attribute(root, "textDirection")?)?,
        line_wrap: LineWrap::parse(required_attribute(root, "lineWrap")?)?,
        vertical_alignment: VerticalAlignment::parse(required_attribute(root, "vertAlign")?)?,
        link_list_id_ref: required_u32(root, "linkListIDRef")?,
        link_list_next_id_ref: required_u32(root, "linkListNextIDRef")?,
        text_width: required_u32(root, "textWidth")?,
        text_height: required_u32(root, "textHeight")?,
        has_text_reference: required_bool01(root, "hasTextRef")?,
        has_number_reference: required_bool01(root, "hasNumRef")?,
        paragraphs,
    })
}

fn read_paragraph(
    document: &PreservingXmlDocument,
    index: usize,
    limits: HeaderFooterLimits,
) -> Result<HeaderFooterParagraph, HeaderFooterError> {
    let root = element(document, index)?;
    if !has_name(root, PARAGRAPH_NS, "p") {
        return Err(HeaderFooterError::UnsupportedShape);
    }
    validate_attributes(
        root,
        &[
            "id",
            "paraPrIDRef",
            "styleIDRef",
            "pageBreak",
            "columnBreak",
            "merged",
        ],
    )?;
    let mut runs = Vec::new();
    for child in child_indexes(document, index)? {
        let child_value = element(document, child)?;
        if has_name(child_value, PARAGRAPH_NS, "run") {
            if runs.len() >= limits.config().runs {
                return Err(HeaderFooterError::RunLimit);
            }
            reserve_one(&mut runs)?;
            runs.push(read_run(document, child, limits)?);
        } else if !has_name(child_value, PARAGRAPH_NS, "linesegarray") {
            return Err(HeaderFooterError::UnsupportedShape);
        }
    }
    if runs.is_empty() {
        return Err(HeaderFooterError::UnsupportedShape);
    }
    Ok(HeaderFooterParagraph {
        id: required_attribute(root, "id")?.to_owned(),
        paragraph_property_id_ref: required_u32(root, "paraPrIDRef")?,
        style_id_ref: required_u32(root, "styleIDRef")?,
        page_break: required_bool01(root, "pageBreak")?,
        column_break: required_bool01(root, "columnBreak")?,
        merged: required_bool01(root, "merged")?,
        runs,
    })
}

fn read_run(
    document: &PreservingXmlDocument,
    index: usize,
    limits: HeaderFooterLimits,
) -> Result<HeaderFooterRun, HeaderFooterError> {
    let root = element(document, index)?;
    validate_attributes(root, &["charPrIDRef"])?;
    let mut inlines = Vec::new();
    for child in child_indexes(document, index)? {
        let value = element(document, child)?;
        if has_name(value, PARAGRAPH_NS, "t") {
            read_text_inlines(document, child, &mut inlines, limits)?;
        } else if has_name(value, PARAGRAPH_NS, "ctrl") {
            let controls = child_indexes(document, child)?;
            if controls.len() != 1
                || !has_name(element(document, controls[0])?, PARAGRAPH_NS, "autoNum")
            {
                return Err(HeaderFooterError::InvalidField);
            }
            reserve_inline(&mut inlines, limits)?;
            inlines.push(HeaderFooterInline::PageField(read_page_field(
                document,
                controls[0],
                limits,
            )?));
        } else {
            return Err(HeaderFooterError::UnsupportedShape);
        }
    }
    Ok(HeaderFooterRun {
        character_style_id_ref: required_u32(root, "charPrIDRef")?,
        inlines,
    })
}

fn read_text_inlines(
    document: &PreservingXmlDocument,
    index: usize,
    inlines: &mut Vec<HeaderFooterInline>,
    limits: HeaderFooterLimits,
) -> Result<(), HeaderFooterError> {
    let root = element(document, index)?;
    validate_attributes(root, &["charStyleIDRef"])?;
    let character_style_id_ref = optional_u32(root, "charStyleIDRef")?;
    // Hangul 2020 emits an empty `hp:t` after some field controls. An empty
    // element owns a single token, so its end token is the start token rather
    // than a later closing-tag token. It contributes no semantic inline.
    if root.is_empty() {
        return if root.first_child().is_none() {
            Ok(())
        } else {
            Err(HeaderFooterError::UnsupportedShape)
        };
    }
    let end = root
        .end_token()
        .ok_or(HeaderFooterError::UnsupportedShape)?;
    let mut raw = String::new();
    for token in &document.tokens()[(root.start_token() + 1)..end] {
        if token.element_index() == Some(index)
            && matches!(
                token.kind(),
                XmlTokenKind::Text | XmlTokenKind::Whitespace | XmlTokenKind::Reference
            )
        {
            raw.push_str(document.source_text(token.span())?);
            continue;
        }
        if !matches!(
            token.kind(),
            XmlTokenKind::StartElement | XmlTokenKind::EmptyElement
        ) {
            continue;
        }
        let Some(child_index) = token.element_index() else {
            continue;
        };
        let child = element(document, child_index)?;
        if child.parent() != Some(index) {
            continue;
        }
        flush_text(&mut raw, character_style_id_ref, inlines, limits)?;
        if has_name(child, PARAGRAPH_NS, "tab") {
            validate_attributes(child, &["width", "leader", "type"])?;
            require_empty(child)?;
            reserve_inline(inlines, limits)?;
            inlines.push(HeaderFooterInline::Tab {
                width: required_u32(child, "width")?,
                leader: required_u32(child, "leader")?,
                tab_type: required_u32(child, "type")?,
            });
        } else if has_name(child, PARAGRAPH_NS, "lineBreak") {
            validate_attributes(child, &[])?;
            require_empty(child)?;
            reserve_inline(inlines, limits)?;
            inlines.push(HeaderFooterInline::LineBreak);
        } else {
            return Err(HeaderFooterError::UnsupportedShape);
        }
    }
    flush_text(&mut raw, character_style_id_ref, inlines, limits)
}

fn flush_text(
    raw: &mut String,
    character_style_id_ref: Option<u32>,
    inlines: &mut Vec<HeaderFooterInline>,
    limits: HeaderFooterLimits,
) -> Result<(), HeaderFooterError> {
    if raw.is_empty() {
        return Ok(());
    }
    let decoded = unescape(raw)
        .map_err(|_| HeaderFooterError::InvalidText)?
        .into_owned();
    *raw = String::new();
    validate_text(&decoded, limits)?;
    reserve_inline(inlines, limits)?;
    inlines.push(HeaderFooterInline::Text {
        value: decoded,
        character_style_id_ref,
    });
    Ok(())
}

fn read_page_field(
    document: &PreservingXmlDocument,
    index: usize,
    limits: HeaderFooterLimits,
) -> Result<PageField, HeaderFooterError> {
    let root = element(document, index)?;
    validate_attributes(root, &["num", "numType"])?;
    let children = child_indexes(document, index)?;
    if children.len() != 1
        || !has_name(
            element(document, children[0])?,
            PARAGRAPH_NS,
            "autoNumFormat",
        )
    {
        return Err(HeaderFooterError::InvalidField);
    }
    let format = element(document, children[0])?;
    validate_attributes(
        format,
        &["type", "userChar", "prefixChar", "suffixChar", "supscript"],
    )?;
    require_empty(format)?;
    let value = PageField {
        displayed_number: required_i32(root, "num")?,
        kind: PageFieldKind::parse(required_attribute(root, "numType")?)?,
        format: parse_number_format(required_attribute(format, "type")?)?,
        user_character: required_attribute(format, "userChar")?.to_owned(),
        prefix: required_attribute(format, "prefixChar")?.to_owned(),
        suffix: required_attribute(format, "suffixChar")?.to_owned(),
        superscript: required_bool01(format, "supscript")?,
    };
    validate_field(&value, limits)?;
    Ok(value)
}

fn read_restart(root: &XmlElementToken) -> Result<PageNumberRestart, HeaderFooterError> {
    validate_attributes(root, &["pageStartsOn", "page", "pic", "tbl", "equation"])?;
    require_empty(root)?;
    Ok(PageNumberRestart {
        page_starts_on: PageVariant::parse(required_attribute(root, "pageStartsOn")?)?,
        page: required_u32(root, "page")?,
        picture: required_u32(root, "pic")?,
        table: required_u32(root, "tbl")?,
        equation: required_u32(root, "equation")?,
    })
}

fn read_visibility(root: &XmlElementToken) -> Result<FirstPageVisibility, HeaderFooterError> {
    validate_attributes(
        root,
        &[
            "hideFirstHeader",
            "hideFirstFooter",
            "hideFirstMasterPage",
            "border",
            "fill",
            "hideFirstPageNum",
            "hideFirstEmptyLine",
            "showLineNumber",
        ],
    )?;
    require_empty(root)?;
    Ok(FirstPageVisibility {
        header: FirstPageDisplay::from_hidden(required_bool01(root, "hideFirstHeader")?),
        footer: FirstPageDisplay::from_hidden(required_bool01(root, "hideFirstFooter")?),
        master_page: FirstPageDisplay::from_hidden(required_bool01(root, "hideFirstMasterPage")?),
        page_number: FirstPageDisplay::from_hidden(required_bool01(root, "hideFirstPageNum")?),
    })
}

fn read_page_number(
    root: &XmlElementToken,
    limits: HeaderFooterLimits,
) -> Result<PageNumberPlacement, HeaderFooterError> {
    validate_attributes(root, &["pos", "formatType", "sideChar"])?;
    require_empty(root)?;
    let value = PageNumberPlacement {
        position: PageNumberPosition::parse(required_attribute(root, "pos")?)?,
        format: parse_number_format(required_attribute(root, "formatType")?)?,
        side_character: required_attribute(root, "sideChar")?.to_owned(),
    };
    validate_text(&value.side_character, limits)?;
    Ok(value)
}

fn validate_policy(
    policy: &SectionPagePolicy,
    limits: HeaderFooterLimits,
) -> Result<(), HeaderFooterError> {
    if policy.definitions.len() > limits.config().definitions
        || policy.master_page_references.len() > limits.config().master_pages
    {
        return Err(HeaderFooterError::DefinitionLimit);
    }
    let declared = usize::try_from(policy.declared_master_page_count)
        .map_err(|_| HeaderFooterError::MasterPageReference)?;
    if declared != policy.master_page_references.len() {
        return Err(HeaderFooterError::MasterPageReference);
    }
    let mut ids = BTreeSet::new();
    let mut variants = BTreeSet::new();
    for definition in &policy.definitions {
        validate_definition(definition, limits)?;
        if !ids.insert(definition.id) || !variants.insert((definition.kind, definition.applies_to))
        {
            return Err(HeaderFooterError::DuplicateDefinition);
        }
    }
    let mut references = BTreeSet::new();
    for reference in &policy.master_page_references {
        validate_identity(reference, limits, false)?;
        if !references.insert(reference.as_str()) {
            return Err(HeaderFooterError::MasterPageReference);
        }
    }
    if let Some(page_number) = &policy.page_number {
        validate_text(&page_number.side_character, limits)?;
        if page_number.format == NumberFormat::Image {
            return Err(HeaderFooterError::InvalidField);
        }
    }
    Ok(())
}

fn validate_definition(
    definition: &HeaderFooterDefinition,
    limits: HeaderFooterLimits,
) -> Result<(), HeaderFooterError> {
    validate_body(&definition.body, limits)
}

fn validate_master_page(
    page: &MasterPageDefinition,
    limits: HeaderFooterLimits,
) -> Result<(), HeaderFooterError> {
    validate_identity(&page.id, limits, false)?;
    match (page.applies_to, page.optional_page_number) {
        (MasterPageVariant::OptionalPage, Some(value)) if value > 0 => {}
        (_, None) if page.applies_to != MasterPageVariant::OptionalPage => {}
        _ => return Err(HeaderFooterError::MasterPageReference),
    }
    validate_body(&page.body, limits)
}

fn validate_body(
    body: &HeaderFooterBody,
    limits: HeaderFooterLimits,
) -> Result<(), HeaderFooterError> {
    validate_identity(&body.id, limits, true)?;
    if body.paragraphs.is_empty() || body.paragraphs.len() > limits.config().paragraphs {
        return Err(HeaderFooterError::ParagraphLimit);
    }
    let mut paragraph_ids = BTreeSet::new();
    let mut run_count = 0usize;
    let mut inline_count = 0usize;
    let mut text_bytes = 0usize;
    let mut page_field_count = 0usize;
    for paragraph in &body.paragraphs {
        let paragraph_id = validate_paragraph_identity(&paragraph.id, limits)?;
        if !paragraph_ids.insert(paragraph_id) || paragraph.runs.is_empty() {
            return Err(HeaderFooterError::InvalidIdentity);
        }
        run_count = run_count
            .checked_add(paragraph.runs.len())
            .ok_or(HeaderFooterError::RunLimit)?;
        for run in &paragraph.runs {
            inline_count = inline_count
                .checked_add(run.inlines.len())
                .ok_or(HeaderFooterError::InlineLimit)?;
            for inline in &run.inlines {
                match inline {
                    HeaderFooterInline::Text { value, .. } => {
                        validate_text(value, limits)?;
                        text_bytes = text_bytes
                            .checked_add(value.len())
                            .ok_or(HeaderFooterError::TextLimit)?;
                    }
                    HeaderFooterInline::PageField(field) => {
                        validate_field(field, limits)?;
                        page_field_count = page_field_count
                            .checked_add(1)
                            .ok_or(HeaderFooterError::InlineLimit)?;
                    }
                    HeaderFooterInline::Tab { .. } | HeaderFooterInline::LineBreak => {}
                }
            }
        }
    }
    if run_count > limits.config().runs {
        return Err(HeaderFooterError::RunLimit);
    }
    if inline_count > limits.config().inlines {
        return Err(HeaderFooterError::InlineLimit);
    }
    if text_bytes > limits.config().text_bytes {
        return Err(HeaderFooterError::TextLimit);
    }
    if body.has_number_reference != (page_field_count > 0) {
        return Err(HeaderFooterError::InvalidField);
    }
    Ok(())
}

fn validate_field(field: &PageField, limits: HeaderFooterLimits) -> Result<(), HeaderFooterError> {
    if field.displayed_number < 0 {
        return Err(HeaderFooterError::InvalidField);
    }
    for value in [&field.user_character, &field.prefix, &field.suffix] {
        validate_text(value, limits)?;
    }
    if field.format == NumberFormat::Image {
        return Err(HeaderFooterError::InvalidField);
    }
    if field.format == NumberFormat::UserChar && field.user_character.is_empty() {
        return Err(HeaderFooterError::InvalidField);
    }
    Ok(())
}

fn lower_body(output: &mut BoundedXml, body: &HeaderFooterBody) -> Result<(), HeaderFooterError> {
    output.push("<hp:subList id=\"")?;
    output.escaped(&body.id)?;
    output.push("\" textDirection=\"")?;
    output.push(body.text_direction.as_str())?;
    output.push("\" lineWrap=\"")?;
    output.push(body.line_wrap.as_str())?;
    output.push("\" vertAlign=\"")?;
    output.push(body.vertical_alignment.as_str())?;
    output.push("\" linkListIDRef=\"")?;
    output.u32(body.link_list_id_ref)?;
    output.push("\" linkListNextIDRef=\"")?;
    output.u32(body.link_list_next_id_ref)?;
    output.push("\" textWidth=\"")?;
    output.u32(body.text_width)?;
    output.push("\" textHeight=\"")?;
    output.u32(body.text_height)?;
    output.push("\" hasTextRef=\"")?;
    output.bool01(body.has_text_reference)?;
    output.push("\" hasNumRef=\"")?;
    output.bool01(body.has_number_reference)?;
    output.push("\">")?;
    for (paragraph_index, paragraph) in body.paragraphs.iter().enumerate() {
        output.push("<hp:p id=\"")?;
        output.escaped(&paragraph.id)?;
        output.push("\" paraPrIDRef=\"")?;
        output.u32(paragraph.paragraph_property_id_ref)?;
        output.push("\" styleIDRef=\"")?;
        output.u32(paragraph.style_id_ref)?;
        output.push("\" pageBreak=\"")?;
        output.bool01(paragraph.page_break)?;
        output.push("\" columnBreak=\"")?;
        output.bool01(paragraph.column_break)?;
        output.push("\" merged=\"")?;
        output.bool01(paragraph.merged)?;
        output.push("\">")?;
        for run in &paragraph.runs {
            output.push("<hp:run charPrIDRef=\"")?;
            output.u32(run.character_style_id_ref)?;
            output.push("\">")?;
            for inline in &run.inlines {
                lower_inline(output, inline)?;
            }
            output.push("</hp:run>")?;
        }
        // Hangul 2020 preserves a line-layout cache for paragraphs that live in
        // header, footer, and master-page sublists.  The OWPML model accepts the
        // array as optional, but omitting it produces a package that the exact
        // desktop build refuses to open.  Use the same bounded deterministic
        // 10 pt cache shape as the VS0 body builder; later layout stages may
        // replace these cached metrics without changing the semantic model.
        let vertical_position = u32::try_from(paragraph_index)
            .ok()
            .and_then(|value| value.checked_mul(1_000))
            .ok_or(HeaderFooterError::OutputLimit)?;
        output.push("<hp:linesegarray><hp:lineseg textpos=\"0\" vertpos=\"")?;
        output.u32(vertical_position)?;
        output.push(
            "\" vertsize=\"1000\" textheight=\"1000\" baseline=\"850\" spacing=\"600\" horzpos=\"0\" horzsize=\"",
        )?;
        output.u32(body.text_width)?;
        output.push("\" flags=\"393216\"/></hp:linesegarray>")?;
        output.push("</hp:p>")?;
    }
    output.push("</hp:subList>")
}

fn lower_inline(
    output: &mut BoundedXml,
    inline: &HeaderFooterInline,
) -> Result<(), HeaderFooterError> {
    match inline {
        HeaderFooterInline::Text {
            value,
            character_style_id_ref,
        } => {
            output.push("<hp:t")?;
            if let Some(value) = character_style_id_ref {
                output.push(" charStyleIDRef=\"")?;
                output.u32(*value)?;
                output.push("\"")?;
            }
            output.push(">")?;
            output.escaped(value)?;
            output.push("</hp:t>")
        }
        HeaderFooterInline::Tab {
            width,
            leader,
            tab_type,
        } => write!(
            output,
            "<hp:t><hp:tab width=\"{width}\" leader=\"{leader}\" type=\"{tab_type}\"/></hp:t>"
        )
        .map_err(|_| HeaderFooterError::AllocationFailed),
        HeaderFooterInline::LineBreak => output.push("<hp:t><hp:lineBreak/></hp:t>"),
        HeaderFooterInline::PageField(field) => {
            output.push("<hp:ctrl><hp:autoNum num=\"")?;
            output.i32(field.displayed_number)?;
            output.push("\" numType=\"")?;
            output.push(field.kind.as_str())?;
            output.push("\"><hp:autoNumFormat type=\"")?;
            output.push(field.format.as_str())?;
            output.push("\" userChar=\"")?;
            output.escaped(&field.user_character)?;
            output.push("\" prefixChar=\"")?;
            output.escaped(&field.prefix)?;
            output.push("\" suffixChar=\"")?;
            output.escaped(&field.suffix)?;
            output.push("\" supscript=\"")?;
            output.bool01(field.superscript)?;
            output.push("\"/></hp:autoNum></hp:ctrl>")
        }
    }
}

fn lower_page_number(
    output: &mut BoundedXml,
    page_number: &PageNumberPlacement,
) -> Result<(), HeaderFooterError> {
    output.push("<hp:pageNum pos=\"")?;
    output.push(page_number.position.as_str())?;
    output.push("\" formatType=\"")?;
    output.push(page_number.format.as_str())?;
    output.push("\" sideChar=\"")?;
    output.escaped(&page_number.side_character)?;
    output.push("\"/>")
}

fn parse_number_format(value: &str) -> Result<NumberFormat, HeaderFooterError> {
    NumberFormat::parse(value).map_err(|_| HeaderFooterError::InvalidEnum)
}

fn validate_identity(
    value: &str,
    limits: HeaderFooterLimits,
    allow_empty: bool,
) -> Result<(), HeaderFooterError> {
    if (!allow_empty && value.is_empty())
        || value.len() > limits.config().identity_bytes
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
    {
        return Err(HeaderFooterError::InvalidIdentity);
    }
    Ok(())
}

fn validate_paragraph_identity(
    value: &str,
    limits: HeaderFooterLimits,
) -> Result<u32, HeaderFooterError> {
    validate_identity(value, limits, false)?;
    value
        .parse::<u32>()
        .map_err(|_| HeaderFooterError::InvalidNumber)
}

fn validate_text(value: &str, limits: HeaderFooterLimits) -> Result<(), HeaderFooterError> {
    if value.len() > limits.config().text_bytes
        || value.chars().any(|character| {
            character.is_control() || matches!(character as u32 & 0xffff, 0xfffe | 0xffff)
        })
    {
        return Err(HeaderFooterError::InvalidText);
    }
    Ok(())
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, HeaderFooterError> {
    document
        .elements()
        .get(index)
        .ok_or(HeaderFooterError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, namespace: &str, local_name: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local_name
}

fn has_parent_chain(
    document: &PreservingXmlDocument,
    index: usize,
    expected: &[(&str, &str)],
) -> Result<bool, HeaderFooterError> {
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

fn unique_structural_element<F>(
    document: &PreservingXmlDocument,
    namespace: &str,
    local_name: &str,
    mut valid_position: F,
) -> Result<usize, HeaderFooterError>
where
    F: FnMut(usize) -> Result<bool, HeaderFooterError>,
{
    let mut found = None;
    for (index, value) in document.elements().iter().enumerate() {
        if value.name().local_name() != local_name {
            continue;
        }
        if !has_name(value, namespace, local_name)
            || !valid_position(index)?
            || found.replace(index).is_some()
        {
            return Err(HeaderFooterError::UnsupportedShape);
        }
    }
    found.ok_or(HeaderFooterError::UnsupportedShape)
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, HeaderFooterError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        reserve_one(&mut children)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), HeaderFooterError> {
    let mut seen = BTreeSet::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(HeaderFooterError::UnsupportedShape);
        }
    }
    Ok(())
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, HeaderFooterError> {
    element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == name
        })
        .map(XmlAttributeToken::semantic_value)
        .ok_or(HeaderFooterError::UnsupportedShape)
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

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, HeaderFooterError> {
    parse_u32(required_attribute(element, name)?)
}

fn optional_u32(element: &XmlElementToken, name: &str) -> Result<Option<u32>, HeaderFooterError> {
    optional_attribute(element, name).map(parse_u32).transpose()
}

fn parse_u32(value: &str) -> Result<u32, HeaderFooterError> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(HeaderFooterError::InvalidNumber);
    }
    value.parse().map_err(|_| HeaderFooterError::InvalidNumber)
}

fn required_i32(element: &XmlElementToken, name: &str) -> Result<i32, HeaderFooterError> {
    let value = required_attribute(element, name)?;
    if value.is_empty()
        || !value
            .strip_prefix('-')
            .unwrap_or(value)
            .bytes()
            .all(|byte| byte.is_ascii_digit())
    {
        return Err(HeaderFooterError::InvalidNumber);
    }
    value.parse().map_err(|_| HeaderFooterError::InvalidNumber)
}

fn required_bool01(element: &XmlElementToken, name: &str) -> Result<bool, HeaderFooterError> {
    match required_attribute(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(HeaderFooterError::InvalidBoolean),
    }
}

fn require_empty(element: &XmlElementToken) -> Result<(), HeaderFooterError> {
    if element.is_empty() && element.first_child().is_none() {
        Ok(())
    } else {
        Err(HeaderFooterError::UnsupportedShape)
    }
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), HeaderFooterError> {
    if document
        .tokens()
        .iter()
        .any(|token| token.kind() == XmlTokenKind::Comment)
    {
        return Err(HeaderFooterError::UnsupportedShape);
    }
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(HeaderFooterError::UnsupportedShape);
        }
    }
    Ok(())
}

fn reserve_one<T>(values: &mut Vec<T>) -> Result<(), HeaderFooterError> {
    values
        .try_reserve(1)
        .map_err(|_| HeaderFooterError::AllocationFailed)
}

fn reserve_inline(
    inlines: &mut Vec<HeaderFooterInline>,
    limits: HeaderFooterLimits,
) -> Result<(), HeaderFooterError> {
    if inlines.len() >= limits.config().inlines {
        Err(HeaderFooterError::InlineLimit)
    } else {
        inlines
            .try_reserve(1)
            .map_err(|_| HeaderFooterError::AllocationFailed)
    }
}

struct BoundedXml {
    value: String,
    maximum: usize,
}

impl BoundedXml {
    fn new(maximum: usize) -> Result<Self, HeaderFooterError> {
        let mut value = String::new();
        value
            .try_reserve(maximum.min(64 * 1024))
            .map_err(|_| HeaderFooterError::AllocationFailed)?;
        Ok(Self { value, maximum })
    }

    fn push(&mut self, value: impl AsRef<str>) -> Result<(), HeaderFooterError> {
        let value = value.as_ref();
        let length = self
            .value
            .len()
            .checked_add(value.len())
            .ok_or(HeaderFooterError::OutputLimit)?;
        if length > self.maximum {
            return Err(HeaderFooterError::OutputLimit);
        }
        self.value
            .try_reserve(value.len())
            .map_err(|_| HeaderFooterError::AllocationFailed)?;
        self.value.push_str(value);
        Ok(())
    }

    fn u32(&mut self, value: u32) -> Result<(), HeaderFooterError> {
        self.push(value.to_string())
    }

    fn i32(&mut self, value: i32) -> Result<(), HeaderFooterError> {
        self.push(value.to_string())
    }

    fn bool01(&mut self, value: bool) -> Result<(), HeaderFooterError> {
        self.push(if value { "1" } else { "0" })
    }

    fn escaped(&mut self, value: &str) -> Result<(), HeaderFooterError> {
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

    fn finish(self) -> Vec<u8> {
        self.value.into_bytes()
    }
}

impl std::fmt::Write for BoundedXml {
    fn write_str(&mut self, value: &str) -> std::fmt::Result {
        self.push(value).map_err(|_| std::fmt::Error)
    }
}
