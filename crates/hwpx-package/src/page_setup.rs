use std::collections::BTreeSet;

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken, XmlTokenKind,
};

pub const PAGE_SETUP_PROFILE_ID: &str = "hwpx-agent.page-setup/1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PageSetupLimitConfig {
    pub input_bytes: usize,
    pub elements: usize,
    pub output_bytes: usize,
    pub max_hwpunit: u32,
}

impl Default for PageSetupLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 4 * 1024 * 1024,
            elements: 131_072,
            output_bytes: 4 * 1024 * 1024,
            max_hwpunit: 566_930,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct PageSetupLimits(PageSetupLimitConfig);

impl PageSetupLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 262_144;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_HWPUNIT: u32 = 5_669_292;

    /// Creates a finite page-setup limit set.
    ///
    /// # Errors
    ///
    /// Rejects zero values and values above the hard ceilings.
    pub fn new(config: PageSetupLimitConfig) -> Result<Self, PageSetupError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.max_hwpunit == 0
            || config.max_hwpunit > Self::HARD_MAX_HWPUNIT
        {
            return Err(PageSetupError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> PageSetupLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PageOrientation {
    Landscape,
    Portrait,
}

impl PageOrientation {
    fn parse(value: &str) -> Result<Self, PageSetupError> {
        match value {
            "WIDELY" => Ok(Self::Landscape),
            "NARROWLY" => Ok(Self::Portrait),
            _ => Err(PageSetupError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::Landscape => "WIDELY",
            Self::Portrait => "NARROWLY",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PageGutterType {
    LeftOnly,
    LeftRight,
    TopBottom,
}

impl PageGutterType {
    fn parse(value: &str) -> Result<Self, PageSetupError> {
        match value {
            "LEFT_ONLY" => Ok(Self::LeftOnly),
            "LEFT_RIGHT" => Ok(Self::LeftRight),
            "TOP_BOTTOM" => Ok(Self::TopBottom),
            _ => Err(PageSetupError::InvalidEnum),
        }
    }

    const fn as_str(self) -> &'static str {
        match self {
            Self::LeftOnly => "LEFT_ONLY",
            Self::LeftRight => "LEFT_RIGHT",
            Self::TopBottom => "TOP_BOTTOM",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PagePreset {
    A3,
    A4,
    A5,
    B4Iso,
    B4Jis,
    B5Iso,
    B5Jis,
    Letter,
    Legal,
    Tabloid,
}

impl PagePreset {
    /// Returns the deterministic unrotated standard sheet dimensions.
    ///
    /// # Errors
    ///
    /// Returns an arithmetic error if a locked conversion cannot fit HWPUNIT.
    pub fn dimensions(self) -> Result<PageDimensions, PageSetupError> {
        let (width, height) = match self {
            Self::A3 => (297_000, 420_000),
            Self::A4 => (210_000, 297_000),
            Self::A5 => (148_000, 210_000),
            Self::B4Iso => (250_000, 353_000),
            Self::B4Jis => (257_000, 364_000),
            Self::B5Iso => (176_000, 250_000),
            Self::B5Jis => (182_000, 257_000),
            Self::Letter => (215_900, 279_400),
            Self::Legal => (215_900, 355_600),
            Self::Tabloid => (279_400, 431_800),
        };
        PageDimensions::from_milli_mm(width, height)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PageDimensions {
    pub width: u32,
    pub height: u32,
}

impl PageDimensions {
    /// Converts thousandths of a millimetre to HWPUNIT with checked half-up rounding.
    ///
    /// # Errors
    ///
    /// Rejects zero, non-portrait-basis dimensions, and arithmetic overflow.
    pub fn from_milli_mm(width: u32, height: u32) -> Result<Self, PageSetupError> {
        let width = milli_mm_to_hwpunit(width)?;
        let height = milli_mm_to_hwpunit(height)?;
        if width == 0 || height == 0 || width > height {
            return Err(PageSetupError::PaperSizeInvalid);
        }
        Ok(Self { width, height })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PageMargins {
    pub header: u32,
    pub footer: u32,
    pub gutter: u32,
    pub left: u32,
    pub right: u32,
    pub top: u32,
    pub bottom: u32,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PageSetup {
    pub orientation: PageOrientation,
    pub dimensions: PageDimensions,
    pub gutter_type: PageGutterType,
    pub margins: PageMargins,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PageSetupMetrics {
    pub effective_width: u32,
    pub effective_height: u32,
    pub body_width: u32,
    pub body_height: u32,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PageSetupLoweringReceipt {
    pub profile_id: &'static str,
    pub sha256: [u8; 32],
    pub output_bytes: usize,
    pub metrics: PageSetupMetrics,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PageSetupPatchReceipt {
    pub profile_id: &'static str,
    pub source_sha256: [u8; 32],
    pub output_sha256: [u8; 32],
    pub output_bytes: usize,
    pub replaced_start: usize,
    pub replaced_end: usize,
    pub metrics: PageSetupMetrics,
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum PageSetupError {
    #[error("page-setup limits are invalid")]
    InvalidLimit,
    #[error("page-setup input exceeds its finite limit")]
    InputLimit,
    #[error("page-setup element count exceeds its finite limit")]
    ElementLimit,
    #[error("page-setup XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("page-setup root is not the current Hangul 2020 profile")]
    WrongRoot,
    #[error("page-setup element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("page-setup numeric attribute is invalid")]
    InvalidNumber,
    #[error("page-setup enum attribute is invalid")]
    InvalidEnum,
    #[error("page paper size is invalid")]
    PaperSizeInvalid,
    #[error("page margins leave no printable body")]
    MarginExceedsPaper,
    #[error("header or footer distance exceeds its page margin")]
    HeaderFooterInvalid,
    #[error("page-setup output exceeds its finite limit")]
    OutputLimit,
    #[error("page-setup arithmetic overflowed")]
    ArithmeticOverflow,
    #[error("page-setup allocation failed")]
    AllocationFailed,
    #[error("page-setup semantic readback differs")]
    ReadbackMismatch,
}

impl PageSetupError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "page_setup_invalid_limit",
            Self::InputLimit => "page_setup_input_limit",
            Self::ElementLimit => "page_setup_element_limit",
            Self::Preserving(_) => "page_setup_preserving_xml",
            Self::WrongRoot => "page_setup_wrong_root",
            Self::UnsupportedShape => "page_setup_unsupported_shape",
            Self::InvalidNumber => "page_setup_invalid_number",
            Self::InvalidEnum => "page_setup_invalid_enum",
            Self::PaperSizeInvalid => "page_setup_paper_size_invalid",
            Self::MarginExceedsPaper => "page_setup_margin_exceeds_paper",
            Self::HeaderFooterInvalid => "page_setup_header_footer_invalid",
            Self::OutputLimit => "page_setup_output_limit",
            Self::ArithmeticOverflow => "page_setup_arithmetic_overflow",
            Self::AllocationFailed => "page_setup_allocation_failed",
            Self::ReadbackMismatch => "page_setup_readback_mismatch",
        }
    }
}

#[derive(Debug)]
pub struct PageSetupReader;

impl PageSetupReader {
    /// Reads exactly one current-Hangul-2020 pagePr from a section or pagePr fragment.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, unsupported, unbounded, or impossible layouts.
    pub fn read(bytes: &[u8], limits: PageSetupLimits) -> Result<PageSetup, PageSetupError> {
        let (document, page_index) = parse_and_find(bytes, limits)?;
        read_page_setup(&document, page_index, limits)
    }
}

#[derive(Debug)]
pub struct PageSetupLowerer;

impl PageSetupLowerer {
    /// Lowers a deterministic standalone pagePr fragment and re-lifts it for equality.
    ///
    /// # Errors
    ///
    /// Rejects impossible or unbounded models and output/readback failures.
    pub fn lower_with_receipt(
        setup: &PageSetup,
        limits: PageSetupLimits,
    ) -> Result<(Vec<u8>, PageSetupLoweringReceipt), PageSetupError> {
        let metrics = validate_setup(setup, limits)?;
        let bytes = lower_element(setup, true, limits.config().output_bytes)?;
        if PageSetupReader::read(&bytes, limits)? != *setup {
            return Err(PageSetupError::ReadbackMismatch);
        }
        let sha256 = Sha256::digest(&bytes).into();
        let output_bytes = bytes.len();
        Ok((
            bytes,
            PageSetupLoweringReceipt {
                profile_id: PAGE_SETUP_PROFILE_ID,
                sha256,
                output_bytes,
                metrics,
            },
        ))
    }

    /// Lowers a deterministic standalone pagePr fragment.
    ///
    /// # Errors
    ///
    /// Rejects impossible or unbounded models and output/readback failures.
    pub fn lower(setup: &PageSetup, limits: PageSetupLimits) -> Result<Vec<u8>, PageSetupError> {
        Self::lower_with_receipt(setup, limits).map(|(bytes, _)| bytes)
    }

    /// Replaces only the exact pagePr byte span in a section and verifies semantic readback.
    ///
    /// # Errors
    ///
    /// Rejects fragments, malformed sections, limits, impossible layouts, or readback drift.
    pub fn replace_in_section(
        section: &[u8],
        setup: &PageSetup,
        limits: PageSetupLimits,
    ) -> Result<(Vec<u8>, PageSetupPatchReceipt), PageSetupError> {
        let metrics = validate_setup(setup, limits)?;
        let (document, page_index) = parse_and_find(section, limits)?;
        let root = element(&document, document.root_element())?;
        if !has_name(root, SECTION_NS, "sec") {
            return Err(PageSetupError::WrongRoot);
        }
        let span = element(&document, page_index)?
            .outer_span()
            .ok_or(PageSetupError::UnsupportedShape)?;
        let replacement = lower_element(setup, false, limits.config().output_bytes)?;
        let output_len = section
            .len()
            .checked_sub(span.len())
            .and_then(|value| value.checked_add(replacement.len()))
            .ok_or(PageSetupError::OutputLimit)?;
        if output_len > limits.config().output_bytes {
            return Err(PageSetupError::OutputLimit);
        }
        let mut output = Vec::new();
        output
            .try_reserve_exact(output_len)
            .map_err(|_| PageSetupError::AllocationFailed)?;
        output.extend_from_slice(&section[..span.start()]);
        output.extend_from_slice(&replacement);
        output.extend_from_slice(&section[span.end()..]);
        if PageSetupReader::read(&output, limits)? != *setup {
            return Err(PageSetupError::ReadbackMismatch);
        }
        let receipt = PageSetupPatchReceipt {
            profile_id: PAGE_SETUP_PROFILE_ID,
            source_sha256: Sha256::digest(section).into(),
            output_sha256: Sha256::digest(&output).into(),
            output_bytes: output.len(),
            replaced_start: span.start(),
            replaced_end: span.end(),
            metrics,
        };
        Ok((output, receipt))
    }
}

impl PageSetup {
    /// Creates a setup from a named standard and validates it against the supplied limits.
    ///
    /// # Errors
    ///
    /// Rejects conversion, limit, or impossible-layout failures.
    pub fn from_preset(
        preset: PagePreset,
        orientation: PageOrientation,
        gutter_type: PageGutterType,
        margins: PageMargins,
        limits: PageSetupLimits,
    ) -> Result<Self, PageSetupError> {
        let setup = Self {
            orientation,
            dimensions: preset.dimensions()?,
            gutter_type,
            margins,
        };
        validate_setup(&setup, limits)?;
        Ok(setup)
    }

    /// Returns checked effective page and printable-body metrics.
    ///
    /// # Errors
    ///
    /// Rejects dimensions, margins, header/footer distances, or configured limits.
    pub fn metrics(self, limits: PageSetupLimits) -> Result<PageSetupMetrics, PageSetupError> {
        validate_setup(&self, limits)
    }
}

fn milli_mm_to_hwpunit(value: u32) -> Result<u32, PageSetupError> {
    if value == 0 {
        return Err(PageSetupError::PaperSizeInvalid);
    }
    let numerator = u64::from(value)
        .checked_mul(7_200)
        .ok_or(PageSetupError::ArithmeticOverflow)?;
    let rounded = numerator
        .checked_add(12_700)
        .ok_or(PageSetupError::ArithmeticOverflow)?
        / 25_400;
    u32::try_from(rounded).map_err(|_| PageSetupError::ArithmeticOverflow)
}

fn validate_setup(
    setup: &PageSetup,
    limits: PageSetupLimits,
) -> Result<PageSetupMetrics, PageSetupError> {
    let maximum = limits.config().max_hwpunit;
    if setup.dimensions.width == 0
        || setup.dimensions.height == 0
        || setup.dimensions.width > setup.dimensions.height
        || setup.dimensions.width > maximum
        || setup.dimensions.height > maximum
    {
        return Err(PageSetupError::PaperSizeInvalid);
    }
    let values = [
        setup.margins.header,
        setup.margins.footer,
        setup.margins.gutter,
        setup.margins.left,
        setup.margins.right,
        setup.margins.top,
        setup.margins.bottom,
    ];
    if values.into_iter().any(|value| value > maximum) {
        return Err(PageSetupError::MarginExceedsPaper);
    }
    if setup.margins.header > setup.margins.top || setup.margins.footer > setup.margins.bottom {
        return Err(PageSetupError::HeaderFooterInvalid);
    }
    let (effective_width, effective_height) = match setup.orientation {
        PageOrientation::Landscape => (setup.dimensions.height, setup.dimensions.width),
        PageOrientation::Portrait => (setup.dimensions.width, setup.dimensions.height),
    };
    let horizontal_gutter = if setup.gutter_type == PageGutterType::TopBottom {
        0
    } else {
        setup.margins.gutter
    };
    let vertical_gutter = if setup.gutter_type == PageGutterType::TopBottom {
        setup.margins.gutter
    } else {
        0
    };
    let body_width = effective_width
        .checked_sub(setup.margins.left)
        .and_then(|value| value.checked_sub(setup.margins.right))
        .and_then(|value| value.checked_sub(horizontal_gutter))
        .filter(|value| *value > 0)
        .ok_or(PageSetupError::MarginExceedsPaper)?;
    let body_height = effective_height
        .checked_sub(setup.margins.top)
        .and_then(|value| value.checked_sub(setup.margins.bottom))
        .and_then(|value| value.checked_sub(vertical_gutter))
        .filter(|value| *value > 0)
        .ok_or(PageSetupError::MarginExceedsPaper)?;
    Ok(PageSetupMetrics {
        effective_width,
        effective_height,
        body_width,
        body_height,
    })
}

fn parse_and_find(
    bytes: &[u8],
    limits: PageSetupLimits,
) -> Result<(PreservingXmlDocument, usize), PageSetupError> {
    if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
        return Err(PageSetupError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.config().elements {
        return Err(PageSetupError::ElementLimit);
    }
    validate_document_envelope(&document)?;
    let root_index = document.root_element();
    let root = element(&document, root_index)?;
    let page_index = if has_name(root, PARAGRAPH_NS, "pagePr") {
        root_index
    } else if has_name(root, SECTION_NS, "sec") {
        let mut found = None;
        let mut section_properties = None;
        for (index, value) in document.elements().iter().enumerate() {
            if value.name().local_name() == "pagePr" {
                if !has_name(value, PARAGRAPH_NS, "pagePr") || found.replace(index).is_some() {
                    return Err(PageSetupError::UnsupportedShape);
                }
            } else if value.name().local_name() == "secPr"
                && (!has_name(value, PARAGRAPH_NS, "secPr")
                    || section_properties.replace(index).is_some())
            {
                return Err(PageSetupError::UnsupportedShape);
            }
        }
        let index = found.ok_or(PageSetupError::UnsupportedShape)?;
        let parent = element(&document, index)?
            .parent()
            .ok_or(PageSetupError::UnsupportedShape)?;
        if section_properties != Some(parent) {
            return Err(PageSetupError::UnsupportedShape);
        }
        index
    } else {
        return Err(PageSetupError::WrongRoot);
    };
    Ok((document, page_index))
}

fn read_page_setup(
    document: &PreservingXmlDocument,
    page_index: usize,
    limits: PageSetupLimits,
) -> Result<PageSetup, PageSetupError> {
    let page = element(document, page_index)?;
    validate_attributes(page, &["landscape", "width", "height", "gutterType"])?;
    require_only_whitespace_content(document, page_index)?;
    let children = child_indexes(document, page_index)?;
    if children.len() != 1 {
        return Err(PageSetupError::UnsupportedShape);
    }
    let margin = element(document, children[0])?;
    if !has_name(margin, PARAGRAPH_NS, "margin") {
        return Err(PageSetupError::UnsupportedShape);
    }
    validate_attributes(
        margin,
        &[
            "header", "footer", "gutter", "left", "right", "top", "bottom",
        ],
    )?;
    if !margin.is_empty() || margin.first_child().is_some() {
        return Err(PageSetupError::UnsupportedShape);
    }
    let setup = PageSetup {
        orientation: PageOrientation::parse(required_attribute(page, "landscape")?)?,
        dimensions: PageDimensions {
            width: required_u32(page, "width")?,
            height: required_u32(page, "height")?,
        },
        gutter_type: PageGutterType::parse(required_attribute(page, "gutterType")?)?,
        margins: PageMargins {
            header: required_u32(margin, "header")?,
            footer: required_u32(margin, "footer")?,
            gutter: required_u32(margin, "gutter")?,
            left: required_u32(margin, "left")?,
            right: required_u32(margin, "right")?,
            top: required_u32(margin, "top")?,
            bottom: required_u32(margin, "bottom")?,
        },
    };
    validate_setup(&setup, limits)?;
    Ok(setup)
}

fn lower_element(
    setup: &PageSetup,
    include_namespace: bool,
    output_limit: usize,
) -> Result<Vec<u8>, PageSetupError> {
    let namespace = if include_namespace {
        " xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\""
    } else {
        ""
    };
    let xml = format!(
        "<hp:pagePr{namespace} landscape=\"{}\" width=\"{}\" height=\"{}\" gutterType=\"{}\"><hp:margin header=\"{}\" footer=\"{}\" gutter=\"{}\" left=\"{}\" right=\"{}\" top=\"{}\" bottom=\"{}\"/></hp:pagePr>",
        setup.orientation.as_str(),
        setup.dimensions.width,
        setup.dimensions.height,
        setup.gutter_type.as_str(),
        setup.margins.header,
        setup.margins.footer,
        setup.margins.gutter,
        setup.margins.left,
        setup.margins.right,
        setup.margins.top,
        setup.margins.bottom,
    );
    if xml.len() > output_limit {
        return Err(PageSetupError::OutputLimit);
    }
    Ok(xml.into_bytes())
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, PageSetupError> {
    document
        .elements()
        .get(index)
        .ok_or(PageSetupError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, namespace: &str, local_name: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local_name
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, PageSetupError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| PageSetupError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn validate_attributes(element: &XmlElementToken, allowed: &[&str]) -> Result<(), PageSetupError> {
    let mut seen = BTreeSet::<&str>::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(PageSetupError::UnsupportedShape);
        }
    }
    Ok(())
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, PageSetupError> {
    element
        .attributes()
        .iter()
        .find(|attribute| {
            !attribute.is_namespace_declaration()
                && attribute.name().namespace().is_none()
                && attribute.name().local_name() == name
        })
        .map(XmlAttributeToken::semantic_value)
        .ok_or(PageSetupError::UnsupportedShape)
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, PageSetupError> {
    let value = required_attribute(element, name)?;
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(PageSetupError::InvalidNumber);
    }
    value.parse().map_err(|_| PageSetupError::InvalidNumber)
}

fn require_only_whitespace_content(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), PageSetupError> {
    let value = element(document, index)?;
    if value.is_empty() {
        return Ok(());
    }
    let end = value.end_token().ok_or(PageSetupError::UnsupportedShape)?;
    for token in &document.tokens()[(value.start_token() + 1)..end] {
        if token.element_index() != Some(index) {
            continue;
        }
        match token.kind() {
            XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment => {
                return Err(PageSetupError::UnsupportedShape);
            }
            XmlTokenKind::Whitespace if !document.source_text(token.span())?.trim().is_empty() => {
                return Err(PageSetupError::UnsupportedShape);
            }
            _ => {}
        }
    }
    Ok(())
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), PageSetupError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(PageSetupError::UnsupportedShape);
        }
    }
    Ok(())
}
