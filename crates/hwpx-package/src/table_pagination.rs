use std::collections::BTreeSet;

use domain_ir::{CaptionSide, TablePageSplitPolicy};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlTokenKind,
};

pub const TABLE_PAGINATION_HWPX_PROFILE_ID: &str = "hwpx-agent.table-pagination-hwpx.hancom-2020/1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TablePaginationHwpxLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub elements: usize,
    pub tables: usize,
    pub rows: usize,
    pub columns: usize,
    pub dimension_hwpunit: u32,
}

impl Default for TablePaginationHwpxLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 2 * 1024 * 1024,
            output_bytes: 2 * 1024 * 1024,
            elements: 100_000,
            tables: 4_096,
            rows: 10_000,
            columns: 1_024,
            dimension_hwpunit: 100_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TablePaginationHwpxLimits(TablePaginationHwpxLimitConfig);

impl TablePaginationHwpxLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 2 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 2 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 100_000;
    pub const HARD_MAX_TABLES: usize = 32_768;
    pub const HARD_MAX_ROWS: usize = 10_000;
    pub const HARD_MAX_COLUMNS: usize = 1_024;
    pub const HARD_MAX_DIMENSION_HWPUNIT: u32 = 1_000_000_000;

    /// Creates finite limits for the current-Hangul-2020 table-pagination adapter.
    ///
    /// # Errors
    ///
    /// Rejects zero values and values above the preserving XML or adapter hard ceilings.
    pub fn new(config: TablePaginationHwpxLimitConfig) -> Result<Self, TablePaginationHwpxError> {
        if config.input_bytes == 0
            || config.input_bytes > Self::HARD_MAX_INPUT_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.tables == 0
            || config.tables > Self::HARD_MAX_TABLES
            || config.rows == 0
            || config.rows > Self::HARD_MAX_ROWS
            || config.columns == 0
            || config.columns > Self::HARD_MAX_COLUMNS
            || config.dimension_hwpunit == 0
            || config.dimension_hwpunit > Self::HARD_MAX_DIMENSION_HWPUNIT
        {
            return Err(TablePaginationHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TablePaginationHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TableCaptionHwpxProperties {
    pub side: CaptionSide,
    pub full_size: bool,
    pub width_hwpunit: u32,
    pub gap_hwpunit: u32,
    pub last_width_hwpunit: u32,
    pub content_sha256: [u8; 32],
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum TableCaptionHwpxTarget {
    Preserve,
    Absent,
    Existing(TableCaptionHwpxProperties),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TablePaginationHwpxTarget {
    pub page_split: TablePageSplitPolicy,
    pub repeat_header_rows: u32,
    pub caption: TableCaptionHwpxTarget,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TablePaginationHwpxReadback {
    pub profile_id: &'static str,
    pub page_split: TablePageSplitPolicy,
    pub repeat_header_rows: u32,
    pub row_count: u32,
    pub column_count: u32,
    pub caption: Option<TableCaptionHwpxProperties>,
    pub table_content_sha256: [u8; 32],
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TablePaginationHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_sha256: [u8; 32],
    pub output_sha256: [u8; 32],
    pub source_bytes: usize,
    pub output_bytes: usize,
    pub modified_attribute_count: usize,
    pub readback: TablePaginationHwpxReadback,
}

#[derive(Debug, Error)]
pub enum TablePaginationHwpxError {
    #[error("table pagination HWPX limits are invalid")]
    InvalidLimit,
    #[error("table pagination HWPX input is empty or oversized")]
    InputLimit,
    #[error("table pagination HWPX output is oversized")]
    OutputLimit,
    #[error("table pagination HWPX element limit was exceeded")]
    ElementLimit,
    #[error("table pagination HWPX table limit was exceeded")]
    TableLimit,
    #[error("table pagination HWPX row or column limit was exceeded")]
    GridLimit,
    #[error("table pagination HWPX root is not the current Hangul 2020 profile")]
    WrongRoot,
    #[error("table pagination HWPX shape is unsupported")]
    UnsupportedShape,
    #[error("table pagination HWPX enum value is unsupported")]
    UnsupportedEnum,
    #[error("table pagination HWPX target policy has no exact native mapping")]
    UnsupportedPolicy,
    #[error("table pagination HWPX numeric attribute is invalid")]
    InvalidNumber,
    #[error("table pagination HWPX boolean attribute is invalid")]
    InvalidBoolean,
    #[error("table pagination HWPX dimension is outside the current profile")]
    OutOfRange,
    #[error("table pagination HWPX caption presence differs from the target")]
    CaptionPresenceMismatch,
    #[error("table pagination HWPX caption content differs from the target binding")]
    CaptionContentMismatch,
    #[error("table pagination HWPX lowered readback differs")]
    ReadbackMismatch,
    #[error("table pagination HWPX allocation failed")]
    AllocationFailed,
    #[error("table pagination preserving XML admission failed: {0}")]
    Xml(#[from] PreservingXmlError),
}

impl TablePaginationHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_pagination_hwpx_invalid_limit",
            Self::InputLimit => "table_pagination_hwpx_input_limit",
            Self::OutputLimit => "table_pagination_hwpx_output_limit",
            Self::ElementLimit => "table_pagination_hwpx_element_limit",
            Self::TableLimit => "table_pagination_hwpx_table_limit",
            Self::GridLimit => "table_pagination_hwpx_grid_limit",
            Self::WrongRoot => "table_pagination_hwpx_wrong_root",
            Self::UnsupportedShape => "table_pagination_hwpx_unsupported_shape",
            Self::UnsupportedEnum => "table_pagination_hwpx_unsupported_enum",
            Self::UnsupportedPolicy => "table_pagination_hwpx_unsupported_policy",
            Self::InvalidNumber => "table_pagination_hwpx_invalid_number",
            Self::InvalidBoolean => "table_pagination_hwpx_invalid_boolean",
            Self::OutOfRange => "table_pagination_hwpx_out_of_range",
            Self::CaptionPresenceMismatch => "table_pagination_hwpx_caption_presence_mismatch",
            Self::CaptionContentMismatch => "table_pagination_hwpx_caption_content_mismatch",
            Self::ReadbackMismatch => "table_pagination_hwpx_readback_mismatch",
            Self::AllocationFailed => "table_pagination_hwpx_allocation_failed",
            Self::Xml(_) => "table_pagination_hwpx_invalid_xml",
        }
    }
}

#[derive(Debug)]
pub struct TablePaginationHwpxReader;

impl TablePaginationHwpxReader {
    /// Reads one standalone current-Hangul-2020 `hp:tbl` fragment.
    ///
    /// # Errors
    ///
    /// Rejects malformed, over-limit, unknown, ambiguous, or unsupported table shapes.
    pub fn read(
        bytes: &[u8],
        limits: TablePaginationHwpxLimits,
    ) -> Result<TablePaginationHwpxReadback, TablePaginationHwpxError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        let root = document.root_element();
        if !has_name(element(&document, root)?, "tbl") {
            return Err(TablePaginationHwpxError::WrongRoot);
        }
        TableShape::read(&document, root, limits).map(|shape| shape.readback)
    }

    /// Reads one table selected by zero-based document order in a section part.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::read`] and rejects an absent selector.
    pub fn read_in_section(
        bytes: &[u8],
        table_ordinal: usize,
        limits: TablePaginationHwpxLimits,
    ) -> Result<TablePaginationHwpxReadback, TablePaginationHwpxError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        validate_section_root(&document)?;
        let root = select_table(&document, table_ordinal, limits)?;
        TableShape::read(&document, root, limits).map(|shape| shape.readback)
    }

    /// Counts tables in a section under the configured finite limit.
    ///
    /// # Errors
    ///
    /// Rejects malformed, wrongly rooted, or over-limit input.
    pub fn count_in_section(
        bytes: &[u8],
        limits: TablePaginationHwpxLimits,
    ) -> Result<usize, TablePaginationHwpxError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        validate_section_root(&document)?;
        Ok(table_indexes(&document, limits)?.len())
    }
}

#[derive(Debug)]
pub struct TablePaginationHwpxLowerer;

impl TablePaginationHwpxLowerer {
    /// Lowers exactly representable pagination attributes in a standalone table fragment.
    ///
    /// Caption creation and removal are intentionally excluded from this preserving V1 profile.
    ///
    /// # Errors
    ///
    /// Rejects unsupported policies, source-shape drift, caption-content drift, and limit failures.
    pub fn lower(
        source: &[u8],
        target: &TablePaginationHwpxTarget,
        limits: TablePaginationHwpxLimits,
    ) -> Result<Vec<u8>, TablePaginationHwpxError> {
        Self::lower_with_receipt(source, target, limits).map(|(bytes, _)| bytes)
    }

    /// Applies [`Self::lower`] and returns exact source/output and readback evidence.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`].
    pub fn lower_with_receipt(
        source: &[u8],
        target: &TablePaginationHwpxTarget,
        limits: TablePaginationHwpxLimits,
    ) -> Result<(Vec<u8>, TablePaginationHwpxLoweringReceipt), TablePaginationHwpxError> {
        lower_selected(source, None, target, limits)
    }

    /// Lowers one table selected by zero-based document order in a section part.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`].
    pub fn lower_in_section(
        source: &[u8],
        table_ordinal: usize,
        target: &TablePaginationHwpxTarget,
        limits: TablePaginationHwpxLimits,
    ) -> Result<Vec<u8>, TablePaginationHwpxError> {
        Self::lower_in_section_with_receipt(source, table_ordinal, target, limits)
            .map(|(bytes, _)| bytes)
    }

    /// Applies [`Self::lower_in_section`] and returns exact integrity evidence.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`].
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        table_ordinal: usize,
        target: &TablePaginationHwpxTarget,
        limits: TablePaginationHwpxLimits,
    ) -> Result<(Vec<u8>, TablePaginationHwpxLoweringReceipt), TablePaginationHwpxError> {
        lower_selected(source, Some(table_ordinal), target, limits)
    }
}

fn lower_selected(
    source: &[u8],
    table_ordinal: Option<usize>,
    target: &TablePaginationHwpxTarget,
    limits: TablePaginationHwpxLimits,
) -> Result<(Vec<u8>, TablePaginationHwpxLoweringReceipt), TablePaginationHwpxError> {
    validate_target(target, limits)?;
    let document = parse_document(source, limits)?;
    validate_document_envelope(&document)?;
    let root = selected_root(&document, table_ordinal, limits)?;
    let source_shape = TableShape::read(&document, root, limits)?;
    let expected = expected_readback(&source_shape.readback, target)?;
    let mut edits = build_edits(&document, &source_shape, target)?;
    let modified_attribute_count = edits.len();
    let output = apply_edits(source, &mut edits, limits)?;

    let output_document = parse_document(&output, limits)?;
    validate_document_envelope(&output_document)?;
    let output_root = selected_root(&output_document, table_ordinal, limits)?;
    let output_readback = TableShape::read(&output_document, output_root, limits)?.readback;
    if output_readback != expected {
        return Err(TablePaginationHwpxError::ReadbackMismatch);
    }
    let receipt = TablePaginationHwpxLoweringReceipt {
        profile_id: TABLE_PAGINATION_HWPX_PROFILE_ID,
        source_sha256: Sha256::digest(source).into(),
        output_sha256: Sha256::digest(&output).into(),
        source_bytes: source.len(),
        output_bytes: output.len(),
        modified_attribute_count,
        readback: output_readback,
    };
    Ok((output, receipt))
}

fn validate_target(
    target: &TablePaginationHwpxTarget,
    limits: TablePaginationHwpxLimits,
) -> Result<(), TablePaginationHwpxError> {
    let _ = native_page_break(target.page_split)?;
    if let TableCaptionHwpxTarget::Existing(caption) = &target.caption {
        for value in [
            caption.width_hwpunit,
            caption.gap_hwpunit,
            caption.last_width_hwpunit,
        ] {
            if value > limits.0.dimension_hwpunit {
                return Err(TablePaginationHwpxError::OutOfRange);
            }
        }
    }
    Ok(())
}

fn expected_readback(
    source: &TablePaginationHwpxReadback,
    target: &TablePaginationHwpxTarget,
) -> Result<TablePaginationHwpxReadback, TablePaginationHwpxError> {
    if target.repeat_header_rows > source.row_count {
        return Err(TablePaginationHwpxError::UnsupportedPolicy);
    }
    let caption = match (&target.caption, &source.caption) {
        (TableCaptionHwpxTarget::Preserve, source) => source.clone(),
        (TableCaptionHwpxTarget::Absent, None) => None,
        (TableCaptionHwpxTarget::Absent, Some(_)) | (TableCaptionHwpxTarget::Existing(_), None) => {
            return Err(TablePaginationHwpxError::CaptionPresenceMismatch);
        }
        (TableCaptionHwpxTarget::Existing(target), Some(source)) => {
            if target.content_sha256 != source.content_sha256 {
                return Err(TablePaginationHwpxError::CaptionContentMismatch);
            }
            Some(target.clone())
        }
    };
    Ok(TablePaginationHwpxReadback {
        profile_id: TABLE_PAGINATION_HWPX_PROFILE_ID,
        page_split: target.page_split,
        repeat_header_rows: target.repeat_header_rows,
        row_count: source.row_count,
        column_count: source.column_count,
        caption,
        table_content_sha256: source.table_content_sha256,
    })
}

#[derive(Debug)]
struct TableShape {
    root: usize,
    caption: Option<usize>,
    row_cells: Vec<Vec<usize>>,
    readback: TablePaginationHwpxReadback,
}

impl TableShape {
    fn read(
        document: &PreservingXmlDocument,
        root: usize,
        limits: TablePaginationHwpxLimits,
    ) -> Result<Self, TablePaginationHwpxError> {
        let root_element = element(document, root)?;
        if !has_name(root_element, "tbl") {
            return Err(TablePaginationHwpxError::UnsupportedShape);
        }
        validate_attributes(
            root_element,
            &[
                "id",
                "zOrder",
                "numberingType",
                "textWrap",
                "textFlow",
                "lock",
                "dropcapstyle",
                "pageBreak",
                "repeatHeader",
                "rowCnt",
                "colCnt",
                "cellSpacing",
                "borderFillIDRef",
                "noAdjust",
            ],
        )?;
        let page_split = parse_page_break(required_attribute(root_element, "pageBreak")?)?;
        let repeat_header_enabled = required_bool01(root_element, "repeatHeader")?;
        let row_count = required_u32(root_element, "rowCnt")?;
        let column_count = required_u32(root_element, "colCnt")?;
        let rows = usize::try_from(row_count).map_err(|_| TablePaginationHwpxError::GridLimit)?;
        let columns =
            usize::try_from(column_count).map_err(|_| TablePaginationHwpxError::GridLimit)?;
        if rows == 0 || rows > limits.0.rows || columns == 0 || columns > limits.0.columns {
            return Err(TablePaginationHwpxError::GridLimit);
        }
        let _ = bounded_u32(root_element, "cellSpacing", limits)?;
        let _ = required_bool01(root_element, "lock")?;
        let _ = required_bool01(root_element, "noAdjust")?;
        let children = validate_table_children(document, root, rows, columns)?;
        let repeat_header_rows =
            read_repeat_header_rows(document, &children.rows, repeat_header_enabled)?;
        let caption = children
            .caption
            .map(|index| read_caption(document, index, limits))
            .transpose()?;
        let readback = TablePaginationHwpxReadback {
            profile_id: TABLE_PAGINATION_HWPX_PROFILE_ID,
            page_split,
            repeat_header_rows,
            row_count,
            column_count,
            caption,
            table_content_sha256: content_sha256(document, root)?,
        };
        Ok(Self {
            root,
            caption: children.caption,
            row_cells: children.row_cells,
            readback,
        })
    }
}

#[derive(Clone, Debug)]
struct TableChildren {
    caption: Option<usize>,
    rows: Vec<usize>,
    row_cells: Vec<Vec<usize>>,
}

fn validate_table_children(
    document: &PreservingXmlDocument,
    root: usize,
    expected_rows: usize,
    maximum_cells_per_row: usize,
) -> Result<TableChildren, TablePaginationHwpxError> {
    #[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
    enum Phase {
        Size,
        Position,
        OuterMargin,
        Caption,
        InnerMargin,
        CellZones,
        Rows,
    }

    let mut phase = Phase::Size;
    let mut caption = None;
    let mut seen_cell_zones = false;
    let mut rows = Vec::new();
    for child in child_indexes(document, root)? {
        let value = element(document, child)?;
        let next = match value.name().local_name() {
            "sz" if has_name(value, "sz") && phase == Phase::Size => Phase::Position,
            "pos" if has_name(value, "pos") && phase == Phase::Position => Phase::OuterMargin,
            "outMargin" if has_name(value, "outMargin") && phase == Phase::OuterMargin => {
                Phase::Caption
            }
            "caption"
                if has_name(value, "caption")
                    && phase == Phase::Caption
                    && caption.replace(child).is_none() =>
            {
                Phase::InnerMargin
            }
            "inMargin"
                if has_name(value, "inMargin")
                    && matches!(phase, Phase::Caption | Phase::InnerMargin) =>
            {
                Phase::CellZones
            }
            "cellzoneList"
                if has_name(value, "cellzoneList")
                    && phase == Phase::CellZones
                    && !seen_cell_zones =>
            {
                seen_cell_zones = true;
                Phase::Rows
            }
            "tr" if has_name(value, "tr") && matches!(phase, Phase::CellZones | Phase::Rows) => {
                rows.try_reserve(1)
                    .map_err(|_| TablePaginationHwpxError::AllocationFailed)?;
                rows.push(child);
                Phase::Rows
            }
            _ => return Err(TablePaginationHwpxError::UnsupportedShape),
        };
        phase = next;
    }
    if rows.len() != expected_rows || !matches!(phase, Phase::Rows) {
        return Err(TablePaginationHwpxError::UnsupportedShape);
    }
    let mut row_cells = Vec::new();
    row_cells
        .try_reserve_exact(rows.len())
        .map_err(|_| TablePaginationHwpxError::AllocationFailed)?;
    for row in &rows {
        validate_attributes(element(document, *row)?, &[])?;
        let cells = child_indexes(document, *row)?;
        if cells.is_empty()
            || cells.len() > maximum_cells_per_row
            || cells
                .iter()
                .any(|cell| !matches!(element(document, *cell), Ok(value) if has_name(value, "tc")))
        {
            return Err(TablePaginationHwpxError::UnsupportedShape);
        }
        for cell in &cells {
            validate_attributes(
                element(document, *cell)?,
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
            let _ = required_bool01(element(document, *cell)?, "header")?;
        }
        row_cells.push(cells);
    }
    Ok(TableChildren {
        caption,
        rows,
        row_cells,
    })
}

fn read_repeat_header_rows(
    document: &PreservingXmlDocument,
    rows: &[usize],
    enabled: bool,
) -> Result<u32, TablePaginationHwpxError> {
    let mut header_rows = 0_usize;
    let mut body_seen = false;
    for row in rows {
        let cells = child_indexes(document, *row)?;
        let first = cells
            .first()
            .copied()
            .ok_or(TablePaginationHwpxError::UnsupportedShape)?;
        let row_is_header = required_bool01(element(document, first)?, "header")?;
        for cell in cells.iter().skip(1) {
            if required_bool01(element(document, *cell)?, "header")? != row_is_header {
                return Err(TablePaginationHwpxError::UnsupportedShape);
            }
        }
        if row_is_header {
            if body_seen {
                return Err(TablePaginationHwpxError::UnsupportedShape);
            }
            header_rows = header_rows
                .checked_add(1)
                .ok_or(TablePaginationHwpxError::GridLimit)?;
        } else {
            body_seen = true;
        }
    }
    if enabled != (header_rows != 0) {
        return Err(TablePaginationHwpxError::UnsupportedShape);
    }
    u32::try_from(header_rows).map_err(|_| TablePaginationHwpxError::GridLimit)
}

fn read_caption(
    document: &PreservingXmlDocument,
    index: usize,
    limits: TablePaginationHwpxLimits,
) -> Result<TableCaptionHwpxProperties, TablePaginationHwpxError> {
    let value = element(document, index)?;
    validate_attributes(value, &["side", "fullSz", "width", "gap", "lastWidth"])?;
    let side = match required_attribute(value, "side")? {
        "TOP" => CaptionSide::Top,
        "BOTTOM" => CaptionSide::Bottom,
        _ => return Err(TablePaginationHwpxError::UnsupportedEnum),
    };
    let children = child_indexes(document, index)?;
    if children.len() != 1 || !has_name(element(document, children[0])?, "subList") {
        return Err(TablePaginationHwpxError::UnsupportedShape);
    }
    Ok(TableCaptionHwpxProperties {
        side,
        full_size: required_bool01(value, "fullSz")?,
        width_hwpunit: bounded_u32(value, "width", limits)?,
        gap_hwpunit: bounded_u32(value, "gap", limits)?,
        last_width_hwpunit: bounded_u32(value, "lastWidth", limits)?,
        content_sha256: content_sha256(document, index)?,
    })
}

fn build_edits(
    document: &PreservingXmlDocument,
    shape: &TableShape,
    target: &TablePaginationHwpxTarget,
) -> Result<Vec<ByteEdit>, TablePaginationHwpxError> {
    let cell_count = shape.row_cells.iter().try_fold(0_usize, |total, cells| {
        total
            .checked_add(cells.len())
            .ok_or(TablePaginationHwpxError::OutputLimit)
    })?;
    let caption_attribute_count = if matches!(target.caption, TableCaptionHwpxTarget::Existing(_)) {
        5
    } else {
        0
    };
    let owned_attribute_count = cell_count
        .checked_add(caption_attribute_count)
        .and_then(|value| value.checked_add(2))
        .ok_or(TablePaginationHwpxError::OutputLimit)?;
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(owned_attribute_count)
        .map_err(|_| TablePaginationHwpxError::AllocationFailed)?;
    push_changed_attribute_edit(
        document,
        shape.root,
        "pageBreak",
        native_page_break(target.page_split)?,
        &mut edits,
    )?;
    push_changed_attribute_edit(
        document,
        shape.root,
        "repeatHeader",
        if target.repeat_header_rows == 0 {
            "0"
        } else {
            "1"
        },
        &mut edits,
    )?;
    let header_rows = usize::try_from(target.repeat_header_rows)
        .map_err(|_| TablePaginationHwpxError::UnsupportedPolicy)?;
    if header_rows > shape.row_cells.len() {
        return Err(TablePaginationHwpxError::UnsupportedPolicy);
    }
    for (row, cells) in shape.row_cells.iter().enumerate() {
        let replacement = if row < header_rows { "1" } else { "0" };
        for cell in cells {
            push_changed_attribute_edit(document, *cell, "header", replacement, &mut edits)?;
        }
    }
    if let TableCaptionHwpxTarget::Existing(caption) = &target.caption {
        let index = shape
            .caption
            .ok_or(TablePaginationHwpxError::CaptionPresenceMismatch)?;
        for (name, replacement) in [
            (
                "side",
                match caption.side {
                    CaptionSide::Top => "TOP".to_owned(),
                    CaptionSide::Bottom => "BOTTOM".to_owned(),
                },
            ),
            (
                "fullSz",
                if caption.full_size { "1" } else { "0" }.to_owned(),
            ),
            ("width", caption.width_hwpunit.to_string()),
            ("gap", caption.gap_hwpunit.to_string()),
            ("lastWidth", caption.last_width_hwpunit.to_string()),
        ] {
            push_changed_attribute_edit(document, index, name, &replacement, &mut edits)?;
        }
    }
    Ok(edits)
}

fn native_page_break(
    policy: TablePageSplitPolicy,
) -> Result<&'static str, TablePaginationHwpxError> {
    match policy {
        TablePageSplitPolicy::Allow => Ok("CELL"),
        TablePageSplitPolicy::AvoidRow => Ok("TABLE"),
        TablePageSplitPolicy::AvoidTable => Ok("NONE"),
        TablePageSplitPolicy::RequiredKeep => Err(TablePaginationHwpxError::UnsupportedPolicy),
    }
}

fn parse_page_break(value: &str) -> Result<TablePageSplitPolicy, TablePaginationHwpxError> {
    match value {
        "CELL" => Ok(TablePageSplitPolicy::Allow),
        "TABLE" => Ok(TablePageSplitPolicy::AvoidRow),
        "NONE" => Ok(TablePageSplitPolicy::AvoidTable),
        _ => Err(TablePaginationHwpxError::UnsupportedEnum),
    }
}

fn selected_root(
    document: &PreservingXmlDocument,
    table_ordinal: Option<usize>,
    limits: TablePaginationHwpxLimits,
) -> Result<usize, TablePaginationHwpxError> {
    if let Some(ordinal) = table_ordinal {
        validate_section_root(document)?;
        select_table(document, ordinal, limits)
    } else {
        let root = document.root_element();
        if !has_name(element(document, root)?, "tbl") {
            return Err(TablePaginationHwpxError::WrongRoot);
        }
        Ok(root)
    }
}

fn select_table(
    document: &PreservingXmlDocument,
    table_ordinal: usize,
    limits: TablePaginationHwpxLimits,
) -> Result<usize, TablePaginationHwpxError> {
    table_indexes(document, limits)?
        .get(table_ordinal)
        .copied()
        .ok_or(TablePaginationHwpxError::UnsupportedShape)
}

fn table_indexes(
    document: &PreservingXmlDocument,
    limits: TablePaginationHwpxLimits,
) -> Result<Vec<usize>, TablePaginationHwpxError> {
    let mut tables = Vec::new();
    for (index, value) in document.elements().iter().enumerate() {
        if has_name(value, "tbl") {
            if tables.len() == limits.0.tables {
                return Err(TablePaginationHwpxError::TableLimit);
            }
            tables
                .try_reserve(1)
                .map_err(|_| TablePaginationHwpxError::AllocationFailed)?;
            tables.push(index);
        }
    }
    Ok(tables)
}

fn parse_document(
    bytes: &[u8],
    limits: TablePaginationHwpxLimits,
) -> Result<PreservingXmlDocument, TablePaginationHwpxError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(TablePaginationHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.0.elements {
        return Err(TablePaginationHwpxError::ElementLimit);
    }
    Ok(document)
}

fn validate_section_root(document: &PreservingXmlDocument) -> Result<(), TablePaginationHwpxError> {
    let root = element(document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(TablePaginationHwpxError::WrongRoot);
    }
    Ok(())
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

fn push_changed_attribute_edit(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    replacement: &str,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TablePaginationHwpxError> {
    let attribute = unique_attribute(element(document, element_index)?, name)?;
    if attribute.semantic_value() != replacement {
        edits.push(ByteEdit {
            span: attribute.value_span(),
            replacement: replacement.as_bytes().to_vec(),
        });
    }
    Ok(())
}

fn apply_edits(
    source: &[u8],
    edits: &mut [ByteEdit],
    limits: TablePaginationHwpxLimits,
) -> Result<Vec<u8>, TablePaginationHwpxError> {
    edits.sort_unstable_by_key(|edit| edit.span.start());
    let mut prior_end = 0;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.span.start() < prior_end || edit.span.end() > source.len() {
            return Err(TablePaginationHwpxError::UnsupportedShape);
        }
        prior_end = edit.span.end();
        output_len = output_len
            .checked_sub(edit.span.len())
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(TablePaginationHwpxError::OutputLimit)?;
    }
    if output_len > limits.0.output_bytes {
        return Err(TablePaginationHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TablePaginationHwpxError::AllocationFailed)?;
    let mut cursor = 0;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.span.start()]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.span.end();
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(TablePaginationHwpxError::OutputLimit);
    }
    Ok(output)
}

fn content_sha256(
    document: &PreservingXmlDocument,
    root: usize,
) -> Result<[u8; 32], TablePaginationHwpxError> {
    let outer = element(document, root)?
        .outer_span()
        .ok_or(TablePaginationHwpxError::UnsupportedShape)?;
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
) -> Result<&XmlElementToken, TablePaginationHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(TablePaginationHwpxError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, TablePaginationHwpxError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| TablePaginationHwpxError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), TablePaginationHwpxError> {
    let mut seen = BTreeSet::<&str>::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(TablePaginationHwpxError::UnsupportedShape);
        }
    }
    Ok(())
}

fn unique_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, TablePaginationHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(TablePaginationHwpxError::UnsupportedShape)?;
    if matches.next().is_some() {
        return Err(TablePaginationHwpxError::UnsupportedShape);
    }
    Ok(value)
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, TablePaginationHwpxError> {
    Ok(unique_attribute(element, name)?.semantic_value())
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, TablePaginationHwpxError> {
    let value = required_attribute(element, name)?;
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(TablePaginationHwpxError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| TablePaginationHwpxError::InvalidNumber)
}

fn bounded_u32(
    element: &XmlElementToken,
    name: &str,
    limits: TablePaginationHwpxLimits,
) -> Result<u32, TablePaginationHwpxError> {
    let value = required_u32(element, name)?;
    if value > limits.0.dimension_hwpunit {
        return Err(TablePaginationHwpxError::OutOfRange);
    }
    Ok(value)
}

fn required_bool01(
    element: &XmlElementToken,
    name: &str,
) -> Result<bool, TablePaginationHwpxError> {
    match required_attribute(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(TablePaginationHwpxError::InvalidBoolean),
    }
}

fn validate_document_envelope(
    document: &PreservingXmlDocument,
) -> Result<(), TablePaginationHwpxError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(TablePaginationHwpxError::UnsupportedShape);
        }
    }
    Ok(())
}
