use std::collections::BTreeSet;

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::paragraph_style::{
    HorizontalAlignment, ParagraphStyleCatalog, ParagraphStyleCatalogWriter, ParagraphStyleLimits,
};
use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlTokenKind,
};

pub const TABLE_CELL_STYLE_PROFILE_ID: &str = "hwpx-agent.table-cell-style.hancom-2020/1";
pub const TABLE_CELL_STYLE_HANCOM_2020_PROFILE_ID: &str =
    "hwpx-agent.table-cell-style.hancom-2020/2";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub enum TableCellStyleProfile {
    #[default]
    ContractV1,
    Hangul2020V2,
}

impl TableCellStyleProfile {
    #[must_use]
    pub const fn profile_id(self) -> &'static str {
        match self {
            Self::ContractV1 => TABLE_CELL_STYLE_PROFILE_ID,
            Self::Hangul2020V2 => TABLE_CELL_STYLE_HANCOM_2020_PROFILE_ID,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableCellStyleLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub elements: usize,
    pub cells: usize,
    pub paragraphs: usize,
    pub margin_hwpunit: u32,
}

impl Default for TableCellStyleLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 2 * 1024 * 1024,
            output_bytes: 2 * 1024 * 1024,
            elements: 32_768,
            cells: 4_096,
            paragraphs: 4_096,
            margin_hwpunit: 10_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableCellStyleLimits(TableCellStyleLimitConfig);

impl TableCellStyleLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 131_072;
    pub const HARD_MAX_CELLS: usize = 32_768;
    pub const HARD_MAX_PARAGRAPHS: usize = 32_768;
    pub const HARD_MAX_MARGIN_HWPUNIT: u32 = 100_000_000;

    /// Creates a finite current-Hangul-2020 table-cell style limit set.
    ///
    /// # Errors
    ///
    /// Rejects zero limits and values above their hard ceilings.
    pub fn new(config: TableCellStyleLimitConfig) -> Result<Self, TableCellStyleError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.cells == 0
            || config.cells > Self::HARD_MAX_CELLS
            || config.paragraphs == 0
            || config.paragraphs > Self::HARD_MAX_PARAGRAPHS
            || config.margin_hwpunit == 0
            || config.margin_hwpunit > Self::HARD_MAX_MARGIN_HWPUNIT
        {
            return Err(TableCellStyleError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableCellStyleLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct CellMargins {
    pub left: u32,
    pub right: u32,
    pub top: u32,
    pub bottom: u32,
}

impl CellMargins {
    #[must_use]
    pub const fn zero() -> Self {
        Self {
            left: 0,
            right: 0,
            top: 0,
            bottom: 0,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum CellTextDirection {
    Horizontal,
    Vertical,
    VerticalAll,
}

impl CellTextDirection {
    fn parse(value: &str) -> Result<Self, TableCellStyleError> {
        match value {
            "HORIZONTAL" => Ok(Self::Horizontal),
            "VERTICAL" => Ok(Self::Vertical),
            "VERTICALALL" => Ok(Self::VerticalAll),
            _ => Err(TableCellStyleError::InvalidEnum),
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

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum CellVerticalAlignment {
    Top,
    Center,
    Bottom,
}

impl CellVerticalAlignment {
    fn parse(value: &str) -> Result<Self, TableCellStyleError> {
        match value {
            "TOP" => Ok(Self::Top),
            "CENTER" => Ok(Self::Center),
            "BOTTOM" => Ok(Self::Bottom),
            _ => Err(TableCellStyleError::InvalidEnum),
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

/// Exact pair of the independent `protect` and `editable` OWPML flags.
#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum CellProtection {
    Open,
    Editable,
    Protected,
    ProtectedEditable,
}

impl CellProtection {
    const fn from_flags(protect: bool, editable: bool) -> Self {
        match (protect, editable) {
            (false, false) => Self::Open,
            (false, true) => Self::Editable,
            (true, false) => Self::Protected,
            (true, true) => Self::ProtectedEditable,
        }
    }

    const fn flags(self) -> (bool, bool) {
        match self {
            Self::Open => (false, false),
            Self::Editable => (false, true),
            Self::Protected => (true, false),
            Self::ProtectedEditable => (true, true),
        }
    }
}

/// Complete P06-04 cell-style value plus the exact validated header references it needs.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableCellStyle {
    pub margins: Option<CellMargins>,
    pub border_fill_id_ref: u32,
    pub paragraph_property_id_ref: u32,
    pub horizontal_alignment: HorizontalAlignment,
    pub vertical_alignment: CellVerticalAlignment,
    pub text_direction: CellTextDirection,
    pub protection: CellProtection,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TableCellStyleReadback {
    pub style: TableCellStyle,
    pub paragraph_count: usize,
    pub content_sha256: [u8; 32],
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TableCellStyleLoweringReceipt {
    pub profile_id: &'static str,
    pub source_sha256: [u8; 32],
    pub output_sha256: [u8; 32],
    pub source_bytes: usize,
    pub output_bytes: usize,
    pub paragraph_count: usize,
    pub content_sha256: [u8; 32],
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum TableCellStyleError {
    #[error("table-cell style limits are invalid")]
    InvalidLimit,
    #[error("table-cell style input exceeds its finite limit")]
    InputLimit,
    #[error("table-cell style element count exceeds its finite limit")]
    ElementLimit,
    #[error("table-cell style cell count exceeds its finite limit")]
    CellLimit,
    #[error("table-cell style output exceeds its finite limit")]
    OutputLimit,
    #[error("table-cell style XML failed preserving admission")]
    Preserving(#[from] PreservingXmlError),
    #[error("table-cell style root is not the current Hangul 2020 tc profile")]
    WrongRoot,
    #[error("table-cell style element or attribute shape is unsupported")]
    UnsupportedShape,
    #[error("table-cell style numeric attribute is invalid")]
    InvalidNumber,
    #[error("table-cell style boolean attribute is invalid")]
    InvalidBoolean,
    #[error("table-cell style enum attribute is invalid")]
    InvalidEnum,
    #[error("table-cell style value is outside the current-2020 range")]
    OutOfRange,
    #[error("table-cell style paragraph count exceeds its finite limit")]
    ParagraphLimit,
    #[error("table-cell style reference is missing or ambiguous")]
    DanglingReference,
    #[error("table-cell style reference resolves to different semantics")]
    ReferenceMismatch,
    #[error("table-cell style header catalog is invalid")]
    CatalogInvalid,
    #[error("table-cell style allocation failed")]
    AllocationFailed,
    #[error("table-cell style lowered readback differs")]
    ReadbackMismatch,
}

impl TableCellStyleError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_cell_style_invalid_limit",
            Self::InputLimit => "table_cell_style_input_limit",
            Self::ElementLimit => "table_cell_style_element_limit",
            Self::CellLimit => "table_cell_style_cell_limit",
            Self::OutputLimit => "table_cell_style_output_limit",
            Self::Preserving(_) => "table_cell_style_preserving_xml",
            Self::WrongRoot => "table_cell_style_wrong_root",
            Self::UnsupportedShape => "table_cell_style_unsupported_shape",
            Self::InvalidNumber => "table_cell_style_invalid_number",
            Self::InvalidBoolean => "table_cell_style_invalid_boolean",
            Self::InvalidEnum => "table_cell_style_invalid_enum",
            Self::OutOfRange => "table_cell_style_out_of_range",
            Self::ParagraphLimit => "table_cell_style_paragraph_limit",
            Self::DanglingReference => "table_cell_style_dangling_reference",
            Self::ReferenceMismatch => "table_cell_style_reference_mismatch",
            Self::CatalogInvalid => "table_cell_style_catalog_invalid",
            Self::AllocationFailed => "table_cell_style_allocation_failed",
            Self::ReadbackMismatch => "table_cell_style_readback_mismatch",
        }
    }
}

#[derive(Debug)]
pub struct TableCellStyleReader;

impl TableCellStyleReader {
    /// Lifts one standalone current-Hangul-2020 `hp:tc` fragment.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unsupported, unbounded, non-canonical, dangling, or semantically
    /// inconsistent content.
    pub fn read(
        bytes: &[u8],
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<TableCellStyleReadback, TableCellStyleError> {
        Self::read_with_profile(bytes, TableCellStyleProfile::ContractV1, catalog, limits)
    }

    /// Lifts a standalone cell under one exact, explicitly selected shape profile.
    ///
    /// # Errors
    ///
    /// Applies the same fail-closed checks as [`Self::read`] without profile auto-detection.
    pub fn read_with_profile(
        bytes: &[u8],
        profile: TableCellStyleProfile,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<TableCellStyleReadback, TableCellStyleError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        let root = document.root_element();
        if !has_name(element(&document, root)?, "tc") {
            return Err(TableCellStyleError::WrongRoot);
        }
        validate_catalog(catalog)?;
        read_from_document(&document, root, profile, catalog, limits)
    }

    /// Lifts one cell selected by zero-based document order from a full section XML part.
    ///
    /// # Errors
    ///
    /// Applies the same structural and reference checks as [`Self::read`] and rejects a missing or
    /// out-of-range cell selector.
    pub fn read_in_section(
        bytes: &[u8],
        cell_ordinal: usize,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<TableCellStyleReadback, TableCellStyleError> {
        Self::read_in_section_with_profile(
            bytes,
            cell_ordinal,
            TableCellStyleProfile::ContractV1,
            catalog,
            limits,
        )
    }

    /// Lifts one section cell under one exact, explicitly selected shape profile.
    ///
    /// # Errors
    ///
    /// Applies the same fail-closed checks as [`Self::read_in_section`] without profile
    /// auto-detection.
    pub fn read_in_section_with_profile(
        bytes: &[u8],
        cell_ordinal: usize,
        profile: TableCellStyleProfile,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<TableCellStyleReadback, TableCellStyleError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        validate_section_root(&document)?;
        validate_catalog(catalog)?;
        let root = select_cell(&document, cell_ordinal, limits)?;
        read_from_document(&document, root, profile, catalog, limits)
    }

    /// Counts every admitted `hp:tc` element in one exact current-Hangul-2020 section part.
    ///
    /// # Errors
    ///
    /// Rejects malformed, wrongly rooted, or over-limit section content before returning a count.
    pub fn count_in_section(
        bytes: &[u8],
        limits: TableCellStyleLimits,
    ) -> Result<usize, TableCellStyleError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        validate_section_root(&document)?;
        Ok(cell_indexes(&document, limits)?.len())
    }
}

pub(crate) fn read_from_document(
    document: &PreservingXmlDocument,
    root_index: usize,
    profile: TableCellStyleProfile,
    catalog: &ParagraphStyleCatalog,
    limits: TableCellStyleLimits,
) -> Result<TableCellStyleReadback, TableCellStyleError> {
    let shape = CellShape::read(document, root_index, profile, limits)?;
    let root = element(document, shape.root)?;
    let margin_element = element(document, shape.margin)?;
    let sub_list = element(document, shape.sub_list)?;

    let has_margin = required_bool01(root, "hasMargin")?;
    let raw_margins = CellMargins {
        left: required_u32(margin_element, "left")?,
        right: required_u32(margin_element, "right")?,
        top: required_u32(margin_element, "top")?,
        bottom: required_u32(margin_element, "bottom")?,
    };
    validate_margins(raw_margins, limits)?;
    let margins = if has_margin {
        Some(raw_margins)
    } else if raw_margins == CellMargins::zero() || profile == TableCellStyleProfile::Hangul2020V2 {
        // Hangul 2020 keeps its inherited/default margin numbers in `hp:cellMargin`
        // even while `hasMargin="0"` makes those numbers semantically inactive.  The
        // v1 contract deliberately retains its stricter canonical-zero rule.
        None
    } else {
        return Err(TableCellStyleError::UnsupportedShape);
    };

    let paragraph_property_id_ref = uniform_paragraph_reference(document, &shape.paragraphs)?;
    let horizontal_alignment = resolve_horizontal_alignment(catalog, paragraph_property_id_ref)?;
    let border_fill_id_ref = required_u32(root, "borderFillIDRef")?;
    if border_fill_id_ref > u32::from(u16::MAX) {
        return Err(TableCellStyleError::OutOfRange);
    }
    validate_border_reference(catalog, border_fill_id_ref)?;
    let protection = CellProtection::from_flags(
        required_bool01(root, "protect")?,
        required_bool01(root, "editable")?,
    );
    let style = TableCellStyle {
        margins,
        border_fill_id_ref,
        paragraph_property_id_ref,
        horizontal_alignment,
        vertical_alignment: CellVerticalAlignment::parse(required_attribute(
            sub_list,
            "vertAlign",
        )?)?,
        text_direction: CellTextDirection::parse(required_attribute(sub_list, "textDirection")?)?,
        protection,
    };
    Ok(TableCellStyleReadback {
        style,
        paragraph_count: shape.paragraphs.len(),
        content_sha256: content_sha256(document, shape.root)?,
    })
}

#[derive(Debug)]
pub struct TableCellStyleLowerer;

impl TableCellStyleLowerer {
    /// Rewrites only the P06-04 style attribute value spans of one admitted `hp:tc` fragment.
    ///
    /// # Errors
    ///
    /// Rejects invalid source or target values, dangling/mismatched references, limit overflow,
    /// content drift, or semantic readback drift.
    pub fn lower(
        source: &[u8],
        style: &TableCellStyle,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<Vec<u8>, TableCellStyleError> {
        Self::lower_with_profile(
            source,
            TableCellStyleProfile::ContractV1,
            style,
            catalog,
            limits,
        )
    }

    /// Rewrites a standalone cell under one exact, explicitly selected shape profile.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`] without profile auto-detection.
    pub fn lower_with_profile(
        source: &[u8],
        profile: TableCellStyleProfile,
        style: &TableCellStyle,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<Vec<u8>, TableCellStyleError> {
        Self::lower_with_profile_and_receipt(source, profile, style, catalog, limits)
            .map(|(bytes, _)| bytes)
    }

    /// Lowers a cell style and returns exact input/output and preserved-content evidence.
    ///
    /// # Errors
    ///
    /// Applies the same validation as [`Self::lower`].
    pub fn lower_with_receipt(
        source: &[u8],
        style: &TableCellStyle,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<(Vec<u8>, TableCellStyleLoweringReceipt), TableCellStyleError> {
        Self::lower_with_profile_and_receipt(
            source,
            TableCellStyleProfile::ContractV1,
            style,
            catalog,
            limits,
        )
    }

    /// Rewrites a standalone cell and returns evidence bound to the selected shape profile.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower_with_receipt`] without profile auto-detection.
    pub fn lower_with_profile_and_receipt(
        source: &[u8],
        profile: TableCellStyleProfile,
        style: &TableCellStyle,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<(Vec<u8>, TableCellStyleLoweringReceipt), TableCellStyleError> {
        lower_selected(source, None, profile, style, catalog, limits)
    }

    /// Rewrites one cell selected by zero-based document order inside a full section XML part.
    ///
    /// # Errors
    ///
    /// Applies the same closed reference, preservation, limit, and readback checks as
    /// [`Self::lower`].
    pub fn lower_in_section(
        source: &[u8],
        cell_ordinal: usize,
        style: &TableCellStyle,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<Vec<u8>, TableCellStyleError> {
        Self::lower_in_section_with_profile(
            source,
            cell_ordinal,
            TableCellStyleProfile::ContractV1,
            style,
            catalog,
            limits,
        )
    }

    /// Rewrites one section cell under one exact, explicitly selected shape profile.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower_in_section`] without profile auto-detection.
    pub fn lower_in_section_with_profile(
        source: &[u8],
        cell_ordinal: usize,
        profile: TableCellStyleProfile,
        style: &TableCellStyle,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<Vec<u8>, TableCellStyleError> {
        Self::lower_in_section_with_profile_and_receipt(
            source,
            cell_ordinal,
            profile,
            style,
            catalog,
            limits,
        )
        .map(|(bytes, _)| bytes)
    }

    /// Rewrites one selected section cell and returns exact integrity evidence.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower_in_section`].
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        cell_ordinal: usize,
        style: &TableCellStyle,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<(Vec<u8>, TableCellStyleLoweringReceipt), TableCellStyleError> {
        Self::lower_in_section_with_profile_and_receipt(
            source,
            cell_ordinal,
            TableCellStyleProfile::ContractV1,
            style,
            catalog,
            limits,
        )
    }

    /// Rewrites one section cell and returns evidence bound to the selected shape profile.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower_in_section_with_receipt`] without profile
    /// auto-detection.
    pub fn lower_in_section_with_profile_and_receipt(
        source: &[u8],
        cell_ordinal: usize,
        profile: TableCellStyleProfile,
        style: &TableCellStyle,
        catalog: &ParagraphStyleCatalog,
        limits: TableCellStyleLimits,
    ) -> Result<(Vec<u8>, TableCellStyleLoweringReceipt), TableCellStyleError> {
        lower_selected(source, Some(cell_ordinal), profile, style, catalog, limits)
    }
}

fn lower_selected(
    source: &[u8],
    cell_ordinal: Option<usize>,
    profile: TableCellStyleProfile,
    style: &TableCellStyle,
    catalog: &ParagraphStyleCatalog,
    limits: TableCellStyleLimits,
) -> Result<(Vec<u8>, TableCellStyleLoweringReceipt), TableCellStyleError> {
    let document = parse_document(source, limits)?;
    validate_document_envelope(&document)?;
    let root = if let Some(ordinal) = cell_ordinal {
        validate_section_root(&document)?;
        select_cell(&document, ordinal, limits)?
    } else {
        let root = document.root_element();
        if !has_name(element(&document, root)?, "tc") {
            return Err(TableCellStyleError::WrongRoot);
        }
        root
    };
    validate_catalog(catalog)?;
    let source_readback = read_from_document(&document, root, profile, catalog, limits)?;
    validate_target_style(style, catalog, limits)?;
    let shape = CellShape::read(&document, root, profile, limits)?;
    let mut edits = style_edits(&document, &shape, profile, style)?;
    let output = apply_edits(source, &mut edits, limits)?;
    let output_document = parse_document(&output, limits)?;
    validate_document_envelope(&output_document)?;
    let output_root = if let Some(ordinal) = cell_ordinal {
        validate_section_root(&output_document)?;
        select_cell(&output_document, ordinal, limits)?
    } else {
        let root = output_document.root_element();
        if !has_name(element(&output_document, root)?, "tc") {
            return Err(TableCellStyleError::WrongRoot);
        }
        root
    };
    let output_readback =
        read_from_document(&output_document, output_root, profile, catalog, limits)?;
    if output_readback.style != *style
        || output_readback.paragraph_count != source_readback.paragraph_count
        || output_readback.content_sha256 != source_readback.content_sha256
    {
        return Err(TableCellStyleError::ReadbackMismatch);
    }
    let receipt = TableCellStyleLoweringReceipt {
        profile_id: profile.profile_id(),
        source_sha256: Sha256::digest(source).into(),
        output_sha256: Sha256::digest(&output).into(),
        source_bytes: source.len(),
        output_bytes: output.len(),
        paragraph_count: output_readback.paragraph_count,
        content_sha256: output_readback.content_sha256,
    };
    Ok((output, receipt))
}

fn style_edits(
    document: &PreservingXmlDocument,
    shape: &CellShape,
    profile: TableCellStyleProfile,
    style: &TableCellStyle,
) -> Result<Vec<ByteEdit>, TableCellStyleError> {
    let (protect, editable) = style.protection.flags();
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(10 + shape.paragraphs.len())
        .map_err(|_| TableCellStyleError::AllocationFailed)?;
    push_attribute_edit(
        document,
        shape.root,
        "hasMargin",
        bool01(style.margins.is_some()),
        &mut edits,
    )?;
    push_attribute_edit(
        document,
        shape.root,
        "borderFillIDRef",
        &style.border_fill_id_ref.to_string(),
        &mut edits,
    )?;
    push_attribute_edit(document, shape.root, "protect", bool01(protect), &mut edits)?;
    push_attribute_edit(
        document,
        shape.root,
        "editable",
        bool01(editable),
        &mut edits,
    )?;
    // With the Hangul-2020 profile, inactive margin numbers are inherited/default
    // serialization state. Preserve those exact spans instead of normalizing them.
    if let Some(margin_values) = style
        .margins
        .or_else(|| (profile == TableCellStyleProfile::ContractV1).then_some(CellMargins::zero()))
    {
        for (name, value) in [
            ("left", margin_values.left),
            ("right", margin_values.right),
            ("top", margin_values.top),
            ("bottom", margin_values.bottom),
        ] {
            push_attribute_edit(document, shape.margin, name, &value.to_string(), &mut edits)?;
        }
    }
    push_attribute_edit(
        document,
        shape.sub_list,
        "textDirection",
        style.text_direction.as_str(),
        &mut edits,
    )?;
    push_attribute_edit(
        document,
        shape.sub_list,
        "vertAlign",
        style.vertical_alignment.as_str(),
        &mut edits,
    )?;
    let paragraph_reference = style.paragraph_property_id_ref.to_string();
    for paragraph in &shape.paragraphs {
        push_attribute_edit(
            document,
            *paragraph,
            "paraPrIDRef",
            &paragraph_reference,
            &mut edits,
        )?;
    }
    Ok(edits)
}

#[derive(Debug)]
struct CellShape {
    root: usize,
    margin: usize,
    sub_list: usize,
    paragraphs: Vec<usize>,
}

impl CellShape {
    fn read(
        document: &PreservingXmlDocument,
        root: usize,
        profile: TableCellStyleProfile,
        limits: TableCellStyleLimits,
    ) -> Result<Self, TableCellStyleError> {
        let root_element = element(document, root)?;
        if !has_name(root_element, "tc") {
            return Err(TableCellStyleError::UnsupportedShape);
        }
        validate_attributes(
            root_element,
            &[
                "name",
                "header",
                "hasMargin",
                "protect",
                "editable",
                "dirty",
                "borderFillIDRef",
            ],
        )?;
        let children = child_indexes(document, root)?;
        let (expected, margin_offset, sub_list_offset) = match profile {
            TableCellStyleProfile::ContractV1 => (
                ["cellAddr", "cellSpan", "cellSz", "cellMargin", "subList"],
                3,
                4,
            ),
            TableCellStyleProfile::Hangul2020V2 => (
                ["subList", "cellAddr", "cellSpan", "cellSz", "cellMargin"],
                4,
                0,
            ),
        };
        if children.len() != expected.len()
            || children
                .iter()
                .zip(expected)
                .any(|(index, name)| !has_name(&document.elements()[*index], name))
        {
            return Err(TableCellStyleError::UnsupportedShape);
        }
        let margin = children[margin_offset];
        validate_attributes(
            element(document, margin)?,
            &["left", "right", "top", "bottom"],
        )?;
        require_no_children(document, margin)?;
        let sub_list = children[sub_list_offset];
        validate_attributes(
            element(document, sub_list)?,
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
                "metatag",
            ],
        )?;
        let paragraphs = child_indexes(document, sub_list)?;
        if paragraphs.is_empty() || paragraphs.len() > limits.config().paragraphs {
            return Err(TableCellStyleError::ParagraphLimit);
        }
        if paragraphs
            .iter()
            .any(|index| !has_name(&document.elements()[*index], "p"))
        {
            return Err(TableCellStyleError::UnsupportedShape);
        }
        for paragraph in &paragraphs {
            let _ = unique_attribute(element(document, *paragraph)?, "paraPrIDRef")?;
        }
        Ok(Self {
            root,
            margin,
            sub_list,
            paragraphs,
        })
    }
}

fn select_cell(
    document: &PreservingXmlDocument,
    cell_ordinal: usize,
    limits: TableCellStyleLimits,
) -> Result<usize, TableCellStyleError> {
    cell_indexes(document, limits)?
        .get(cell_ordinal)
        .copied()
        .ok_or(TableCellStyleError::UnsupportedShape)
}

fn cell_indexes(
    document: &PreservingXmlDocument,
    limits: TableCellStyleLimits,
) -> Result<Vec<usize>, TableCellStyleError> {
    let mut cells = Vec::new();
    for (index, value) in document.elements().iter().enumerate() {
        if has_name(value, "tc") {
            if cells.len() == limits.config().cells {
                return Err(TableCellStyleError::CellLimit);
            }
            cells
                .try_reserve(1)
                .map_err(|_| TableCellStyleError::AllocationFailed)?;
            cells.push(index);
        }
    }
    Ok(cells)
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

fn parse_document(
    bytes: &[u8],
    limits: TableCellStyleLimits,
) -> Result<PreservingXmlDocument, TableCellStyleError> {
    if bytes.is_empty() || bytes.len() > limits.config().input_bytes {
        return Err(TableCellStyleError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.config().elements {
        return Err(TableCellStyleError::ElementLimit);
    }
    Ok(document)
}

fn validate_catalog(catalog: &ParagraphStyleCatalog) -> Result<(), TableCellStyleError> {
    ParagraphStyleCatalogWriter::lower(catalog, ParagraphStyleLimits::default())
        .map(|_| ())
        .map_err(|_| TableCellStyleError::CatalogInvalid)
}

fn validate_section_root(document: &PreservingXmlDocument) -> Result<(), TableCellStyleError> {
    let root = element(document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(TableCellStyleError::WrongRoot);
    }
    Ok(())
}

fn validate_target_style(
    style: &TableCellStyle,
    catalog: &ParagraphStyleCatalog,
    limits: TableCellStyleLimits,
) -> Result<(), TableCellStyleError> {
    if style.border_fill_id_ref > u32::from(u16::MAX)
        || style
            .margins
            .is_some_and(|margins| validate_margins(margins, limits).is_err())
    {
        return Err(TableCellStyleError::OutOfRange);
    }
    validate_border_reference(catalog, style.border_fill_id_ref)?;
    let actual = resolve_horizontal_alignment(catalog, style.paragraph_property_id_ref)?;
    if actual != style.horizontal_alignment {
        return Err(TableCellStyleError::ReferenceMismatch);
    }
    Ok(())
}

fn validate_margins(
    margins: CellMargins,
    limits: TableCellStyleLimits,
) -> Result<(), TableCellStyleError> {
    if [margins.left, margins.right, margins.top, margins.bottom]
        .into_iter()
        .any(|value| value > limits.config().margin_hwpunit)
    {
        return Err(TableCellStyleError::OutOfRange);
    }
    Ok(())
}

fn validate_border_reference(
    catalog: &ParagraphStyleCatalog,
    id: u32,
) -> Result<(), TableCellStyleError> {
    if catalog
        .border_fills
        .iter()
        .filter(|border| border.id == id)
        .count()
        != 1
    {
        return Err(TableCellStyleError::DanglingReference);
    }
    Ok(())
}

fn resolve_horizontal_alignment(
    catalog: &ParagraphStyleCatalog,
    id: u32,
) -> Result<HorizontalAlignment, TableCellStyleError> {
    let mut matches = catalog.styles.iter().filter(|style| style.id == id);
    let value = matches
        .next()
        .ok_or(TableCellStyleError::DanglingReference)?;
    if matches.next().is_some() {
        return Err(TableCellStyleError::DanglingReference);
    }
    Ok(value.horizontal_alignment)
}

fn uniform_paragraph_reference(
    document: &PreservingXmlDocument,
    paragraphs: &[usize],
) -> Result<u32, TableCellStyleError> {
    let mut expected = None;
    for paragraph in paragraphs {
        let value = required_u32(element(document, *paragraph)?, "paraPrIDRef")?;
        if expected.is_some_and(|prior| prior != value) {
            return Err(TableCellStyleError::UnsupportedShape);
        }
        expected = Some(value);
    }
    expected.ok_or(TableCellStyleError::ParagraphLimit)
}

fn push_attribute_edit(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    replacement: &str,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TableCellStyleError> {
    let attribute = unique_attribute(element(document, element_index)?, name)?;
    edits.push(ByteEdit {
        span: attribute.value_span(),
        replacement: replacement.as_bytes().to_vec(),
    });
    Ok(())
}

fn apply_edits(
    source: &[u8],
    edits: &mut [ByteEdit],
    limits: TableCellStyleLimits,
) -> Result<Vec<u8>, TableCellStyleError> {
    edits.sort_unstable_by_key(|edit| edit.span.start());
    let mut prior_end = 0;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.span.start() < prior_end || edit.span.end() > source.len() {
            return Err(TableCellStyleError::UnsupportedShape);
        }
        prior_end = edit.span.end();
        output_len = output_len
            .checked_sub(edit.span.len())
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(TableCellStyleError::OutputLimit)?;
    }
    if output_len > limits.config().output_bytes {
        return Err(TableCellStyleError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TableCellStyleError::AllocationFailed)?;
    let mut cursor = 0;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.span.start()]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.span.end();
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(TableCellStyleError::OutputLimit);
    }
    Ok(output)
}

fn content_sha256(
    document: &PreservingXmlDocument,
    root: usize,
) -> Result<[u8; 32], TableCellStyleError> {
    let outer = element(document, root)?
        .outer_span()
        .ok_or(TableCellStyleError::UnsupportedShape)?;
    let mut digest = Sha256::new();
    for token in document.tokens() {
        if token.span().start() >= outer.start()
            && token.span().end() <= outer.end()
            && matches!(
                token.kind(),
                XmlTokenKind::Text | XmlTokenKind::Reference | XmlTokenKind::Comment
            )
        {
            digest.update([token.kind() as u8]);
            digest.update(document.source_text(token.span())?.as_bytes());
        }
    }
    Ok(digest.finalize().into())
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, TableCellStyleError> {
    document
        .elements()
        .get(index)
        .ok_or(TableCellStyleError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, TableCellStyleError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| TableCellStyleError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), TableCellStyleError> {
    let mut seen = BTreeSet::<&str>::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(TableCellStyleError::UnsupportedShape);
        }
    }
    Ok(())
}

fn unique_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, TableCellStyleError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(TableCellStyleError::UnsupportedShape)?;
    if matches.next().is_some() {
        return Err(TableCellStyleError::UnsupportedShape);
    }
    Ok(value)
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, TableCellStyleError> {
    Ok(unique_attribute(element, name)?.semantic_value())
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, TableCellStyleError> {
    let value = required_attribute(element, name)?;
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(TableCellStyleError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| TableCellStyleError::InvalidNumber)
}

fn required_bool01(element: &XmlElementToken, name: &str) -> Result<bool, TableCellStyleError> {
    match required_attribute(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(TableCellStyleError::InvalidBoolean),
    }
}

const fn bool01(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}

fn require_no_children(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), TableCellStyleError> {
    if element(document, index)?.first_child().is_some() {
        return Err(TableCellStyleError::UnsupportedShape);
    }
    Ok(())
}

fn validate_document_envelope(document: &PreservingXmlDocument) -> Result<(), TableCellStyleError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(TableCellStyleError::UnsupportedShape);
        }
    }
    Ok(())
}
