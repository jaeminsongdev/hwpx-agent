use std::collections::BTreeSet;

use domain_ir::{
    LengthMicrometers, TableGrid, TableGridError, TableLayoutError, TableLayoutLimits,
    TableLayoutPlan, UnitError,
};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlTokenKind,
};

pub const TABLE_LAYOUT_HWPX_PROFILE_ID_V1: &str = "hwpx-agent.table-layout-hwpx.hancom-2020/1";
pub const TABLE_LAYOUT_HWPX_PROFILE_ID: &str = "hwpx-agent.table-layout-hwpx.hancom-2020/2";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableLayoutHwpxLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub elements: usize,
    pub tables: usize,
    pub cells: usize,
    pub rows: usize,
    pub columns: usize,
    pub slots: usize,
    pub dimension_hwpunit: u32,
}

impl Default for TableLayoutHwpxLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 8 * 1024 * 1024,
            output_bytes: 8 * 1024 * 1024,
            elements: 131_072,
            tables: 4_096,
            cells: 32_768,
            rows: 10_000,
            columns: 1_024,
            slots: 1_000_000,
            dimension_hwpunit: 100_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableLayoutHwpxLimits(TableLayoutHwpxLimitConfig);

impl TableLayoutHwpxLimits {
    pub const HARD_MAX_INPUT_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 1_000_000;
    pub const HARD_MAX_TABLES: usize = 32_768;
    pub const HARD_MAX_CELLS: usize = 1_000_000;
    pub const HARD_MAX_ROWS: usize = 10_000;
    pub const HARD_MAX_COLUMNS: usize = 1_024;
    pub const HARD_MAX_SLOTS: usize = 10_000_000;
    pub const HARD_MAX_DIMENSION_HWPUNIT: u32 = 1_000_000_000;

    /// Creates finite limits for current-Hangul-2020 table layout lowering.
    ///
    /// # Errors
    ///
    /// Rejects zero values and values above their hard ceilings.
    pub fn new(config: TableLayoutHwpxLimitConfig) -> Result<Self, TableLayoutHwpxError> {
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
            || config.rows == 0
            || config.rows > Self::HARD_MAX_ROWS
            || config.columns == 0
            || config.columns > Self::HARD_MAX_COLUMNS
            || config.slots == 0
            || config.slots > Self::HARD_MAX_SLOTS
            || config.dimension_hwpunit == 0
            || config.dimension_hwpunit > Self::HARD_MAX_DIMENSION_HWPUNIT
        {
            return Err(TableLayoutHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> TableLayoutHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct TableCellSizeReadback {
    pub row: u32,
    pub column: u32,
    pub row_span: u32,
    pub column_span: u32,
    pub width_hwpunit: u32,
    pub height_hwpunit: u32,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TableInnerMarginReadback {
    pub left_hwpunit: u32,
    pub right_hwpunit: u32,
    pub top_hwpunit: u32,
    pub bottom_hwpunit: u32,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TableLayoutHwpxReadback {
    pub rows: u32,
    pub columns: u32,
    pub table_width_hwpunit: u32,
    pub table_height_hwpunit: u32,
    pub inner_margin: TableInnerMarginReadback,
    pub cells: Vec<TableCellSizeReadback>,
    pub content_sha256: [u8; 32],
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TableLayoutHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_sha256: [u8; 32],
    pub output_sha256: [u8; 32],
    pub grid_sha256: [u8; 32],
    pub layout_plan_sha256: [u8; 32],
    pub source_bytes: usize,
    pub output_bytes: usize,
    pub rows: u32,
    pub columns: u32,
    pub cells: usize,
    pub modified_attribute_count: usize,
    pub table_width_hwpunit: u32,
    pub table_height_hwpunit: u32,
    pub content_sha256: [u8; 32],
}

#[derive(Debug, Eq, Error, PartialEq)]
pub enum TableLayoutHwpxError {
    #[error("table layout HWPX limits are invalid")]
    InvalidLimit,
    #[error("table layout HWPX input exceeds its finite limit")]
    InputLimit,
    #[error("table layout HWPX output exceeds its finite limit")]
    OutputLimit,
    #[error("table layout HWPX element count exceeds its finite limit")]
    ElementLimit,
    #[error("table layout HWPX table count exceeds its finite limit")]
    TableLimit,
    #[error("table layout HWPX cell count exceeds its finite limit")]
    CellLimit,
    #[error("table layout HWPX row, column, or slot count exceeds its finite limit")]
    GridLimit,
    #[error("table layout HWPX root is not the current Hangul 2020 profile")]
    WrongRoot,
    #[error("table layout HWPX shape is unsupported")]
    UnsupportedShape,
    #[error("table layout HWPX numeric attribute is invalid")]
    InvalidNumber,
    #[error("table layout HWPX boolean attribute is invalid")]
    InvalidBoolean,
    #[error("table layout HWPX dimension is outside the current profile")]
    OutOfRange,
    #[error("table layout plan is not verified for publication")]
    UnverifiedPlan,
    #[error("table layout plan is bound to a different grid")]
    PlanGridMismatch,
    #[error("table layout plan shape is inconsistent")]
    PlanShapeMismatch,
    #[error("table layout HWPX grid differs from the requested grid")]
    GridShapeMismatch,
    #[error("table layout HWPX allocation failed")]
    AllocationFailed,
    #[error("table layout HWPX lowered readback differs")]
    ReadbackMismatch,
    #[error("table layout HWPX preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
    #[error("table layout unit conversion failed")]
    Unit(#[from] UnitError),
    #[error("table layout plan serialization failed")]
    Layout(#[from] TableLayoutError),
    #[error("table layout grid serialization failed")]
    Grid(#[from] TableGridError),
}

impl TableLayoutHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "table_layout_hwpx_invalid_limit",
            Self::InputLimit => "table_layout_hwpx_input_limit",
            Self::OutputLimit => "table_layout_hwpx_output_limit",
            Self::ElementLimit => "table_layout_hwpx_element_limit",
            Self::TableLimit => "table_layout_hwpx_table_limit",
            Self::CellLimit => "table_layout_hwpx_cell_limit",
            Self::GridLimit => "table_layout_hwpx_grid_limit",
            Self::WrongRoot => "table_layout_hwpx_wrong_root",
            Self::UnsupportedShape => "table_layout_hwpx_unsupported_shape",
            Self::InvalidNumber => "table_layout_hwpx_invalid_number",
            Self::InvalidBoolean => "table_layout_hwpx_invalid_boolean",
            Self::OutOfRange => "table_layout_hwpx_out_of_range",
            Self::UnverifiedPlan => "table_layout_hwpx_unverified_plan",
            Self::PlanGridMismatch => "table_layout_hwpx_plan_grid_mismatch",
            Self::PlanShapeMismatch => "table_layout_hwpx_plan_shape_mismatch",
            Self::GridShapeMismatch => "table_layout_hwpx_grid_shape_mismatch",
            Self::AllocationFailed => "table_layout_hwpx_allocation_failed",
            Self::ReadbackMismatch => "table_layout_hwpx_readback_mismatch",
            Self::Preserving(_) => "table_layout_hwpx_preserving_xml",
            Self::Unit(_) => "table_layout_hwpx_unit_conversion",
            Self::Layout(_) => "table_layout_hwpx_plan_serialization",
            Self::Grid(_) => "table_layout_hwpx_grid_serialization",
        }
    }
}

#[derive(Debug)]
pub struct TableLayoutHwpxReader;

impl TableLayoutHwpxReader {
    /// Reads one standalone current-Hangul-2020 `hp:tbl` fragment.
    ///
    /// # Errors
    ///
    /// Rejects malformed, over-limit, structurally incomplete, overlapping, or uncovered grids.
    pub fn read(
        bytes: &[u8],
        limits: TableLayoutHwpxLimits,
    ) -> Result<TableLayoutHwpxReadback, TableLayoutHwpxError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        let root = document.root_element();
        if !has_name(element(&document, root)?, "tbl") {
            return Err(TableLayoutHwpxError::WrongRoot);
        }
        TableShape::read(&document, root, limits).map(|shape| shape.readback)
    }

    /// Reads one table selected by zero-based document order from a full section part.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::read`] and rejects an absent selector.
    pub fn read_in_section(
        bytes: &[u8],
        table_ordinal: usize,
        limits: TableLayoutHwpxLimits,
    ) -> Result<TableLayoutHwpxReadback, TableLayoutHwpxError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        validate_section_root(&document)?;
        let root = select_table(&document, table_ordinal, limits)?;
        TableShape::read(&document, root, limits).map(|shape| shape.readback)
    }

    /// Counts current-profile tables in one section under a separate finite table limit.
    ///
    /// # Errors
    ///
    /// Rejects malformed, wrongly rooted, or over-limit input.
    pub fn count_in_section(
        bytes: &[u8],
        limits: TableLayoutHwpxLimits,
    ) -> Result<usize, TableLayoutHwpxError> {
        let document = parse_document(bytes, limits)?;
        validate_document_envelope(&document)?;
        validate_section_root(&document)?;
        Ok(table_indexes(&document, limits)?.len())
    }
}

#[derive(Debug)]
pub struct TableLayoutHwpxLowerer;

impl TableLayoutHwpxLowerer {
    /// Lowers one verified layout plan into a standalone current-profile table fragment.
    ///
    /// # Errors
    ///
    /// Rejects unverified plans, grid drift, unsupported source shape, unit/limit failures, content
    /// drift, or semantic readback drift.
    pub fn lower(
        source: &[u8],
        grid: &TableGrid,
        plan: &TableLayoutPlan,
        limits: TableLayoutHwpxLimits,
    ) -> Result<Vec<u8>, TableLayoutHwpxError> {
        Self::lower_with_receipt(source, grid, plan, limits).map(|(bytes, _)| bytes)
    }

    /// Lowers a standalone table and returns exact integrity and plan-binding evidence.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower`].
    pub fn lower_with_receipt(
        source: &[u8],
        grid: &TableGrid,
        plan: &TableLayoutPlan,
        limits: TableLayoutHwpxLimits,
    ) -> Result<(Vec<u8>, TableLayoutHwpxLoweringReceipt), TableLayoutHwpxError> {
        lower_selected(source, None, grid, plan, limits)
    }

    /// Lowers one table selected by zero-based document order inside a section part.
    ///
    /// # Errors
    ///
    /// Applies the same plan, structure, preservation, and readback checks as [`Self::lower`].
    pub fn lower_in_section(
        source: &[u8],
        table_ordinal: usize,
        grid: &TableGrid,
        plan: &TableLayoutPlan,
        limits: TableLayoutHwpxLimits,
    ) -> Result<Vec<u8>, TableLayoutHwpxError> {
        Self::lower_in_section_with_receipt(source, table_ordinal, grid, plan, limits)
            .map(|(bytes, _)| bytes)
    }

    /// Lowers one selected section table and returns exact integrity evidence.
    ///
    /// # Errors
    ///
    /// Applies the same checks as [`Self::lower_in_section`].
    pub fn lower_in_section_with_receipt(
        source: &[u8],
        table_ordinal: usize,
        grid: &TableGrid,
        plan: &TableLayoutPlan,
        limits: TableLayoutHwpxLimits,
    ) -> Result<(Vec<u8>, TableLayoutHwpxLoweringReceipt), TableLayoutHwpxError> {
        lower_selected(source, Some(table_ordinal), grid, plan, limits)
    }
}

fn lower_selected(
    source: &[u8],
    table_ordinal: Option<usize>,
    grid: &TableGrid,
    plan: &TableLayoutPlan,
    limits: TableLayoutHwpxLimits,
) -> Result<(Vec<u8>, TableLayoutHwpxLoweringReceipt), TableLayoutHwpxError> {
    let target = TargetLayout::from_plan(grid, plan, limits)?;
    let document = parse_document(source, limits)?;
    validate_document_envelope(&document)?;
    let root = selected_root(&document, table_ordinal, limits)?;
    let source_shape = TableShape::read(&document, root, limits)?;
    validate_source_grid(&source_shape.readback, &target)?;

    let mut edits = layout_edits(&document, &source_shape, &target)?;
    let modified_attribute_count = edits.len();
    let output = apply_edits(source, &mut edits, limits)?;

    let output_document = parse_document(&output, limits)?;
    validate_document_envelope(&output_document)?;
    let output_root = selected_root(&output_document, table_ordinal, limits)?;
    let output_shape = TableShape::read(&output_document, output_root, limits)?;
    let expected = target.readback(
        source_shape.readback.inner_margin,
        source_shape.readback.content_sha256,
    )?;
    if output_shape.readback != expected {
        return Err(TableLayoutHwpxError::ReadbackMismatch);
    }

    let receipt = TableLayoutHwpxLoweringReceipt {
        profile_id: TABLE_LAYOUT_HWPX_PROFILE_ID,
        source_sha256: Sha256::digest(source).into(),
        output_sha256: Sha256::digest(&output).into(),
        grid_sha256: target.grid_sha256,
        layout_plan_sha256: target.plan_sha256,
        source_bytes: source.len(),
        output_bytes: output.len(),
        rows: target.rows,
        columns: target.columns,
        cells: target.cells.len(),
        modified_attribute_count,
        table_width_hwpunit: target.table_width,
        table_height_hwpunit: target.table_height,
        content_sha256: expected.content_sha256,
    };
    Ok((output, receipt))
}

#[derive(Debug)]
struct TargetLayout {
    rows: u32,
    columns: u32,
    table_width: u32,
    table_height: u32,
    cells: Vec<TableCellSizeReadback>,
    grid_sha256: [u8; 32],
    plan_sha256: [u8; 32],
}

impl TargetLayout {
    fn from_plan(
        grid: &TableGrid,
        plan: &TableLayoutPlan,
        limits: TableLayoutHwpxLimits,
    ) -> Result<Self, TableLayoutHwpxError> {
        plan.require_verified()
            .map_err(|_| TableLayoutHwpxError::UnverifiedPlan)?;
        let grid_sha256 = grid.canonical_sha256()?;
        if plan.grid_sha256() != hex_digest(grid_sha256) {
            return Err(TableLayoutHwpxError::PlanGridMismatch);
        }
        let rows = usize::try_from(grid.rows()).map_err(|_| TableLayoutHwpxError::GridLimit)?;
        let columns =
            usize::try_from(grid.columns()).map_err(|_| TableLayoutHwpxError::GridLimit)?;
        if rows == 0
            || rows > limits.0.rows
            || columns == 0
            || columns > limits.0.columns
            || plan.column_widths().len() != columns
            || plan.estimated_row_heights().len() != rows
            || grid.master_cell_count() > limits.0.cells
        {
            return Err(TableLayoutHwpxError::PlanShapeMismatch);
        }
        let columns_hwpunit = quantize_dimensions(plan.column_widths(), limits)?;
        let rows_hwpunit = quantize_dimensions(plan.estimated_row_heights(), limits)?;
        let table_width = checked_hwpunit_sum(&columns_hwpunit, limits)?;
        let table_height = checked_hwpunit_sum(&rows_hwpunit, limits)?;
        validate_plan_totals(plan, &columns_hwpunit, &rows_hwpunit)?;

        let mut cells = Vec::new();
        cells
            .try_reserve_exact(grid.master_cell_count())
            .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
        for cell in grid.master_cells() {
            let column_start =
                usize::try_from(cell.column).map_err(|_| TableLayoutHwpxError::GridLimit)?;
            let column_count =
                usize::try_from(cell.column_span).map_err(|_| TableLayoutHwpxError::GridLimit)?;
            let row_start =
                usize::try_from(cell.row).map_err(|_| TableLayoutHwpxError::GridLimit)?;
            let row_count =
                usize::try_from(cell.row_span).map_err(|_| TableLayoutHwpxError::GridLimit)?;
            let width_hwpunit =
                checked_range_sum(&columns_hwpunit, column_start, column_count, limits)?;
            let height_hwpunit = checked_range_sum(&rows_hwpunit, row_start, row_count, limits)?;
            cells.push(TableCellSizeReadback {
                row: cell.row,
                column: cell.column,
                row_span: cell.row_span,
                column_span: cell.column_span,
                width_hwpunit,
                height_hwpunit,
            });
        }
        cells.sort_unstable();
        let plan_sha256 = plan.canonical_sha256(TableLayoutLimits::default())?;
        Ok(Self {
            rows: grid.rows(),
            columns: grid.columns(),
            table_width,
            table_height,
            cells,
            grid_sha256,
            plan_sha256,
        })
    }

    fn readback(
        &self,
        inner_margin: TableInnerMarginReadback,
        content_sha256: [u8; 32],
    ) -> Result<TableLayoutHwpxReadback, TableLayoutHwpxError> {
        let mut cells = Vec::new();
        cells
            .try_reserve_exact(self.cells.len())
            .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
        cells.extend(self.cells.iter().cloned());
        Ok(TableLayoutHwpxReadback {
            rows: self.rows,
            columns: self.columns,
            table_width_hwpunit: self.table_width,
            table_height_hwpunit: self.table_height,
            inner_margin,
            cells,
            content_sha256,
        })
    }
}

fn validate_plan_totals(
    plan: &TableLayoutPlan,
    columns_hwpunit: &[u32],
    rows_hwpunit: &[u32],
) -> Result<(), TableLayoutHwpxError> {
    let column_micrometers = checked_micrometer_sum(plan.column_widths())?;
    let row_micrometers = checked_micrometer_sum(plan.estimated_row_heights())?;
    if column_micrometers != plan.total_width().as_i64()
        || row_micrometers != plan.objective().estimated_total_row_height.as_i64()
        || columns_hwpunit.is_empty()
        || rows_hwpunit.is_empty()
    {
        return Err(TableLayoutHwpxError::PlanShapeMismatch);
    }
    Ok(())
}

fn checked_micrometer_sum(values: &[LengthMicrometers]) -> Result<i64, TableLayoutHwpxError> {
    values.iter().try_fold(0_i64, |total, value| {
        total
            .checked_add(value.as_i64())
            .ok_or(TableLayoutHwpxError::PlanShapeMismatch)
    })
}

fn quantize_dimensions(
    values: &[LengthMicrometers],
    limits: TableLayoutHwpxLimits,
) -> Result<Vec<u32>, TableLayoutHwpxError> {
    let mut output = Vec::new();
    output
        .try_reserve_exact(values.len())
        .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
    for value in values {
        let raw = value.to_hwp_unit()?.value().as_i64();
        let value = u32::try_from(raw).map_err(|_| TableLayoutHwpxError::OutOfRange)?;
        if value == 0 || value > limits.0.dimension_hwpunit {
            return Err(TableLayoutHwpxError::OutOfRange);
        }
        output.push(value);
    }
    Ok(output)
}

fn checked_hwpunit_sum(
    values: &[u32],
    limits: TableLayoutHwpxLimits,
) -> Result<u32, TableLayoutHwpxError> {
    let sum = values.iter().try_fold(0_u64, |total, value| {
        total
            .checked_add(u64::from(*value))
            .ok_or(TableLayoutHwpxError::OutOfRange)
    })?;
    u32::try_from(sum)
        .ok()
        .filter(|value| *value != 0 && *value <= limits.0.dimension_hwpunit)
        .ok_or(TableLayoutHwpxError::OutOfRange)
}

fn checked_range_sum(
    values: &[u32],
    start: usize,
    count: usize,
    limits: TableLayoutHwpxLimits,
) -> Result<u32, TableLayoutHwpxError> {
    let end = start
        .checked_add(count)
        .ok_or(TableLayoutHwpxError::GridLimit)?;
    let range = values
        .get(start..end)
        .ok_or(TableLayoutHwpxError::GridLimit)?;
    checked_hwpunit_sum(range, limits)
}

#[derive(Debug)]
struct TableShape {
    root: usize,
    size: usize,
    cells: Vec<CellShape>,
    readback: TableLayoutHwpxReadback,
}

#[derive(Debug)]
struct CellShape {
    size: usize,
    readback: TableCellSizeReadback,
}

impl TableShape {
    fn read(
        document: &PreservingXmlDocument,
        root: usize,
        limits: TableLayoutHwpxLimits,
    ) -> Result<Self, TableLayoutHwpxError> {
        let dimensions = read_table_dimensions(document, root, limits)?;
        let children = read_table_children(document, root, dimensions.row_count, limits)?;
        let size_element = element(document, children.size)?;
        let table_width_hwpunit = bounded_positive_u32(size_element, "width", limits)?;
        let table_height_hwpunit = bounded_positive_u32(size_element, "height", limits)?;
        let mut cells = read_table_cells(document, children.rows, limits)?;
        cells.sort_unstable_by(|left, right| left.readback.cmp(&right.readback));
        validate_cell_coverage(
            &cells,
            dimensions.row_count,
            dimensions.column_count,
            dimensions.slots,
        )?;
        let mut readback_cells = Vec::new();
        readback_cells
            .try_reserve_exact(cells.len())
            .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
        readback_cells.extend(cells.iter().map(|cell| cell.readback.clone()));
        let readback = TableLayoutHwpxReadback {
            rows: dimensions.rows,
            columns: dimensions.columns,
            table_width_hwpunit,
            table_height_hwpunit,
            inner_margin: read_margin(document, children.inner_margin, limits)?,
            cells: readback_cells,
            content_sha256: content_sha256(document, root)?,
        };
        Ok(Self {
            root,
            size: children.size,
            cells,
            readback,
        })
    }
}

#[derive(Clone, Copy, Debug)]
struct TableDimensions {
    rows: u32,
    columns: u32,
    row_count: usize,
    column_count: usize,
    slots: usize,
}

fn read_table_dimensions(
    document: &PreservingXmlDocument,
    root: usize,
    limits: TableLayoutHwpxLimits,
) -> Result<TableDimensions, TableLayoutHwpxError> {
    let root_element = element(document, root)?;
    if !has_name(root_element, "tbl") {
        return Err(TableLayoutHwpxError::UnsupportedShape);
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
    let rows = required_u32(root_element, "rowCnt")?;
    let columns = required_u32(root_element, "colCnt")?;
    let row_count = usize::try_from(rows).map_err(|_| TableLayoutHwpxError::GridLimit)?;
    let column_count = usize::try_from(columns).map_err(|_| TableLayoutHwpxError::GridLimit)?;
    let slots = row_count
        .checked_mul(column_count)
        .ok_or(TableLayoutHwpxError::GridLimit)?;
    if row_count == 0
        || row_count > limits.0.rows
        || column_count == 0
        || column_count > limits.0.columns
        || slots == 0
        || slots > limits.0.slots
        || required_u32(root_element, "cellSpacing")? != 0
    {
        return Err(TableLayoutHwpxError::GridLimit);
    }
    let _ = required_bool01(root_element, "noAdjust")?;
    Ok(TableDimensions {
        rows,
        columns,
        row_count,
        column_count,
        slots,
    })
}

#[derive(Debug)]
struct TableChildren {
    size: usize,
    inner_margin: usize,
    rows: Vec<usize>,
}

fn read_table_children(
    document: &PreservingXmlDocument,
    root: usize,
    expected_rows: usize,
    limits: TableLayoutHwpxLimits,
) -> Result<TableChildren, TableLayoutHwpxError> {
    let children = child_indexes(document, root)?;
    let mut size = None;
    let mut position = None;
    let mut outer_margin = None;
    let mut inner_margin = None;
    let mut rows = Vec::new();
    for child in children {
        let value = element(document, child)?;
        match value.name().local_name() {
            "sz" if has_name(value, "sz") && size.replace(child).is_none() => {}
            "pos" if has_name(value, "pos") && position.replace(child).is_none() => {}
            "outMargin"
                if has_name(value, "outMargin") && outer_margin.replace(child).is_none() => {}
            "inMargin" if has_name(value, "inMargin") && inner_margin.replace(child).is_none() => {}
            "tr" if has_name(value, "tr") => {
                rows.try_reserve(1)
                    .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
                rows.push(child);
            }
            _ => return Err(TableLayoutHwpxError::UnsupportedShape),
        }
    }
    let size = size.ok_or(TableLayoutHwpxError::UnsupportedShape)?;
    let position = position.ok_or(TableLayoutHwpxError::UnsupportedShape)?;
    let outer_margin = outer_margin.ok_or(TableLayoutHwpxError::UnsupportedShape)?;
    let inner_margin = inner_margin.ok_or(TableLayoutHwpxError::UnsupportedShape)?;
    if rows.len() != expected_rows {
        return Err(TableLayoutHwpxError::GridShapeMismatch);
    }
    validate_size(document, size, limits)?;
    validate_position(document, position)?;
    validate_margin(document, outer_margin)?;
    validate_margin(document, inner_margin)?;
    Ok(TableChildren {
        size,
        inner_margin,
        rows,
    })
}

fn read_table_cells(
    document: &PreservingXmlDocument,
    rows: Vec<usize>,
    limits: TableLayoutHwpxLimits,
) -> Result<Vec<CellShape>, TableLayoutHwpxError> {
    let mut cells = Vec::new();
    for (row_ordinal, row) in rows.into_iter().enumerate() {
        validate_attributes(element(document, row)?, &[])?;
        for cell in child_indexes(document, row)? {
            if !has_name(element(document, cell)?, "tc") {
                return Err(TableLayoutHwpxError::UnsupportedShape);
            }
            if cells.len() == limits.0.cells {
                return Err(TableLayoutHwpxError::CellLimit);
            }
            cells
                .try_reserve(1)
                .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
            let cell = CellShape::read(document, cell, limits)?;
            if usize::try_from(cell.readback.row).map_err(|_| TableLayoutHwpxError::GridLimit)?
                != row_ordinal
            {
                return Err(TableLayoutHwpxError::GridShapeMismatch);
            }
            cells.push(cell);
        }
    }
    Ok(cells)
}

impl CellShape {
    fn read(
        document: &PreservingXmlDocument,
        root: usize,
        limits: TableLayoutHwpxLimits,
    ) -> Result<Self, TableLayoutHwpxError> {
        validate_attributes(
            element(document, root)?,
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
        if children.len() != 5 {
            return Err(TableLayoutHwpxError::UnsupportedShape);
        }
        let address = unique_child(document, &children, "cellAddr")?;
        let span = unique_child(document, &children, "cellSpan")?;
        let size = unique_child(document, &children, "cellSz")?;
        let _margin = unique_child(document, &children, "cellMargin")?;
        let _content = unique_child(document, &children, "subList")?;
        validate_attributes(element(document, address)?, &["colAddr", "rowAddr"])?;
        validate_attributes(element(document, span)?, &["colSpan", "rowSpan"])?;
        validate_attributes(element(document, size)?, &["width", "height"])?;
        require_no_children(document, address)?;
        require_no_children(document, span)?;
        require_no_children(document, size)?;
        let size_element = element(document, size)?;
        let readback = TableCellSizeReadback {
            row: required_u32(element(document, address)?, "rowAddr")?,
            column: required_u32(element(document, address)?, "colAddr")?,
            row_span: required_u32(element(document, span)?, "rowSpan")?,
            column_span: required_u32(element(document, span)?, "colSpan")?,
            width_hwpunit: bounded_positive_u32(size_element, "width", limits)?,
            height_hwpunit: bounded_positive_u32(size_element, "height", limits)?,
        };
        if readback.row_span == 0 || readback.column_span == 0 {
            return Err(TableLayoutHwpxError::GridShapeMismatch);
        }
        Ok(Self { size, readback })
    }
}

fn validate_cell_coverage(
    cells: &[CellShape],
    rows: usize,
    columns: usize,
    slots: usize,
) -> Result<(), TableLayoutHwpxError> {
    let mut coverage = Vec::new();
    coverage
        .try_reserve_exact(slots)
        .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
    coverage.resize(slots, false);
    for cell in cells {
        let first_row =
            usize::try_from(cell.readback.row).map_err(|_| TableLayoutHwpxError::GridLimit)?;
        let first_column =
            usize::try_from(cell.readback.column).map_err(|_| TableLayoutHwpxError::GridLimit)?;
        let row_span =
            usize::try_from(cell.readback.row_span).map_err(|_| TableLayoutHwpxError::GridLimit)?;
        let column_span = usize::try_from(cell.readback.column_span)
            .map_err(|_| TableLayoutHwpxError::GridLimit)?;
        let row_end = first_row
            .checked_add(row_span)
            .filter(|value| *value <= rows)
            .ok_or(TableLayoutHwpxError::GridShapeMismatch)?;
        let column_end = first_column
            .checked_add(column_span)
            .filter(|value| *value <= columns)
            .ok_or(TableLayoutHwpxError::GridShapeMismatch)?;
        for row in first_row..row_end {
            for column in first_column..column_end {
                let slot = row
                    .checked_mul(columns)
                    .and_then(|value| value.checked_add(column))
                    .ok_or(TableLayoutHwpxError::GridLimit)?;
                let occupied = coverage
                    .get_mut(slot)
                    .ok_or(TableLayoutHwpxError::GridLimit)?;
                if *occupied {
                    return Err(TableLayoutHwpxError::GridShapeMismatch);
                }
                *occupied = true;
            }
        }
    }
    if coverage.iter().any(|occupied| !occupied) {
        return Err(TableLayoutHwpxError::GridShapeMismatch);
    }
    Ok(())
}

fn validate_source_grid(
    source: &TableLayoutHwpxReadback,
    target: &TargetLayout,
) -> Result<(), TableLayoutHwpxError> {
    if source.rows != target.rows
        || source.columns != target.columns
        || source.cells.len() != target.cells.len()
        || source.cells.iter().zip(&target.cells).any(|(left, right)| {
            (left.row, left.column, left.row_span, left.column_span)
                != (right.row, right.column, right.row_span, right.column_span)
        })
    {
        return Err(TableLayoutHwpxError::GridShapeMismatch);
    }
    Ok(())
}

fn layout_edits(
    document: &PreservingXmlDocument,
    shape: &TableShape,
    target: &TargetLayout,
) -> Result<Vec<ByteEdit>, TableLayoutHwpxError> {
    if shape.root >= document.elements().len() || shape.cells.len() != target.cells.len() {
        return Err(TableLayoutHwpxError::UnsupportedShape);
    }
    let mut edits = Vec::new();
    let count = target
        .cells
        .len()
        .checked_mul(2)
        .and_then(|value| value.checked_add(2))
        .ok_or(TableLayoutHwpxError::OutputLimit)?;
    edits
        .try_reserve_exact(count)
        .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
    push_attribute_edit(
        document,
        shape.size,
        "width",
        &target.table_width.to_string(),
        &mut edits,
    )?;
    push_attribute_edit(
        document,
        shape.size,
        "height",
        &target.table_height.to_string(),
        &mut edits,
    )?;
    for (source, expected) in shape.cells.iter().zip(&target.cells) {
        if (source.readback.row, source.readback.column) != (expected.row, expected.column) {
            return Err(TableLayoutHwpxError::GridShapeMismatch);
        }
        push_attribute_edit(
            document,
            source.size,
            "width",
            &expected.width_hwpunit.to_string(),
            &mut edits,
        )?;
        push_attribute_edit(
            document,
            source.size,
            "height",
            &expected.height_hwpunit.to_string(),
            &mut edits,
        )?;
    }
    Ok(edits)
}

fn validate_size(
    document: &PreservingXmlDocument,
    index: usize,
    limits: TableLayoutHwpxLimits,
) -> Result<(), TableLayoutHwpxError> {
    let value = element(document, index)?;
    validate_attributes(
        value,
        &["width", "widthRelTo", "height", "heightRelTo", "protect"],
    )?;
    let _ = bounded_positive_u32(value, "width", limits)?;
    let _ = bounded_positive_u32(value, "height", limits)?;
    if required_attribute(value, "widthRelTo")? != "ABSOLUTE"
        || required_attribute(value, "heightRelTo")? != "ABSOLUTE"
    {
        return Err(TableLayoutHwpxError::UnsupportedShape);
    }
    let _ = required_bool01(value, "protect")?;
    require_no_children(document, index)
}

fn validate_position(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), TableLayoutHwpxError> {
    validate_attributes(
        element(document, index)?,
        &[
            "treatAsChar",
            "affectLSpacing",
            "flowWithText",
            "allowOverlap",
            "holdAnchorAndSO",
            "vertRelTo",
            "horzRelTo",
            "vertAlign",
            "horzAlign",
            "vertOffset",
            "horzOffset",
        ],
    )?;
    require_no_children(document, index)
}

fn validate_margin(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), TableLayoutHwpxError> {
    let value = element(document, index)?;
    validate_attributes(value, &["left", "right", "top", "bottom"])?;
    for name in ["left", "right", "top", "bottom"] {
        let _ = required_u32(value, name)?;
    }
    require_no_children(document, index)
}

fn read_margin(
    document: &PreservingXmlDocument,
    index: usize,
    limits: TableLayoutHwpxLimits,
) -> Result<TableInnerMarginReadback, TableLayoutHwpxError> {
    let value = element(document, index)?;
    Ok(TableInnerMarginReadback {
        left_hwpunit: bounded_u32(value, "left", limits)?,
        right_hwpunit: bounded_u32(value, "right", limits)?,
        top_hwpunit: bounded_u32(value, "top", limits)?,
        bottom_hwpunit: bounded_u32(value, "bottom", limits)?,
    })
}

fn selected_root(
    document: &PreservingXmlDocument,
    table_ordinal: Option<usize>,
    limits: TableLayoutHwpxLimits,
) -> Result<usize, TableLayoutHwpxError> {
    if let Some(ordinal) = table_ordinal {
        validate_section_root(document)?;
        select_table(document, ordinal, limits)
    } else {
        let root = document.root_element();
        if !has_name(element(document, root)?, "tbl") {
            return Err(TableLayoutHwpxError::WrongRoot);
        }
        Ok(root)
    }
}

fn select_table(
    document: &PreservingXmlDocument,
    table_ordinal: usize,
    limits: TableLayoutHwpxLimits,
) -> Result<usize, TableLayoutHwpxError> {
    table_indexes(document, limits)?
        .get(table_ordinal)
        .copied()
        .ok_or(TableLayoutHwpxError::UnsupportedShape)
}

fn table_indexes(
    document: &PreservingXmlDocument,
    limits: TableLayoutHwpxLimits,
) -> Result<Vec<usize>, TableLayoutHwpxError> {
    let mut tables = Vec::new();
    for (index, value) in document.elements().iter().enumerate() {
        if has_name(value, "tbl") {
            if tables.len() == limits.0.tables {
                return Err(TableLayoutHwpxError::TableLimit);
            }
            tables
                .try_reserve(1)
                .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
            tables.push(index);
        }
    }
    Ok(tables)
}

fn parse_document(
    bytes: &[u8],
    limits: TableLayoutHwpxLimits,
) -> Result<PreservingXmlDocument, TableLayoutHwpxError> {
    if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
        return Err(TableLayoutHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(bytes)?;
    if document.elements().len() > limits.0.elements {
        return Err(TableLayoutHwpxError::ElementLimit);
    }
    Ok(document)
}

fn validate_section_root(document: &PreservingXmlDocument) -> Result<(), TableLayoutHwpxError> {
    let root = element(document, document.root_element())?;
    if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
        return Err(TableLayoutHwpxError::WrongRoot);
    }
    Ok(())
}

#[derive(Debug)]
struct ByteEdit {
    span: XmlByteSpan,
    replacement: Vec<u8>,
}

fn push_attribute_edit(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    replacement: &str,
    edits: &mut Vec<ByteEdit>,
) -> Result<(), TableLayoutHwpxError> {
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
    limits: TableLayoutHwpxLimits,
) -> Result<Vec<u8>, TableLayoutHwpxError> {
    edits.sort_unstable_by_key(|edit| edit.span.start());
    let mut prior_end = 0;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.span.start() < prior_end || edit.span.end() > source.len() {
            return Err(TableLayoutHwpxError::UnsupportedShape);
        }
        prior_end = edit.span.end();
        output_len = output_len
            .checked_sub(edit.span.len())
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(TableLayoutHwpxError::OutputLimit)?;
    }
    if output_len > limits.0.output_bytes {
        return Err(TableLayoutHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
    let mut cursor = 0;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.span.start()]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.span.end();
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(TableLayoutHwpxError::OutputLimit);
    }
    Ok(output)
}

fn content_sha256(
    document: &PreservingXmlDocument,
    root: usize,
) -> Result<[u8; 32], TableLayoutHwpxError> {
    let outer = element(document, root)?
        .outer_span()
        .ok_or(TableLayoutHwpxError::UnsupportedShape)?;
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
) -> Result<&XmlElementToken, TableLayoutHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(TableLayoutHwpxError::UnsupportedShape)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn child_indexes(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, TableLayoutHwpxError> {
    let mut children = Vec::new();
    let mut current = element(document, parent)?.first_child();
    while let Some(index) = current {
        children
            .try_reserve(1)
            .map_err(|_| TableLayoutHwpxError::AllocationFailed)?;
        children.push(index);
        current = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn unique_child(
    document: &PreservingXmlDocument,
    children: &[usize],
    name: &str,
) -> Result<usize, TableLayoutHwpxError> {
    let mut matches = children
        .iter()
        .copied()
        .filter(|index| element(document, *index).is_ok_and(|value| has_name(value, name)));
    let value = matches
        .next()
        .ok_or(TableLayoutHwpxError::UnsupportedShape)?;
    if matches.next().is_some() {
        return Err(TableLayoutHwpxError::UnsupportedShape);
    }
    Ok(value)
}

fn validate_attributes(
    element: &XmlElementToken,
    allowed: &[&str],
) -> Result<(), TableLayoutHwpxError> {
    let mut seen = BTreeSet::<&str>::new();
    for attribute in element.attributes() {
        if attribute.is_namespace_declaration() {
            continue;
        }
        let name = attribute.name().local_name();
        if attribute.name().namespace().is_some() || !allowed.contains(&name) || !seen.insert(name)
        {
            return Err(TableLayoutHwpxError::UnsupportedShape);
        }
    }
    Ok(())
}

fn unique_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, TableLayoutHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(TableLayoutHwpxError::UnsupportedShape)?;
    if matches.next().is_some() {
        return Err(TableLayoutHwpxError::UnsupportedShape);
    }
    Ok(value)
}

fn required_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, TableLayoutHwpxError> {
    Ok(unique_attribute(element, name)?.semantic_value())
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, TableLayoutHwpxError> {
    let value = required_attribute(element, name)?;
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(TableLayoutHwpxError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| TableLayoutHwpxError::InvalidNumber)
}

fn bounded_positive_u32(
    element: &XmlElementToken,
    name: &str,
    limits: TableLayoutHwpxLimits,
) -> Result<u32, TableLayoutHwpxError> {
    let value = required_u32(element, name)?;
    if value == 0 || value > limits.0.dimension_hwpunit {
        return Err(TableLayoutHwpxError::OutOfRange);
    }
    Ok(value)
}

fn bounded_u32(
    element: &XmlElementToken,
    name: &str,
    limits: TableLayoutHwpxLimits,
) -> Result<u32, TableLayoutHwpxError> {
    let value = required_u32(element, name)?;
    if value > limits.0.dimension_hwpunit {
        return Err(TableLayoutHwpxError::OutOfRange);
    }
    Ok(value)
}

fn required_bool01(element: &XmlElementToken, name: &str) -> Result<bool, TableLayoutHwpxError> {
    match required_attribute(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(TableLayoutHwpxError::InvalidBoolean),
    }
}

fn require_no_children(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<(), TableLayoutHwpxError> {
    if element(document, index)?.first_child().is_some() {
        return Err(TableLayoutHwpxError::UnsupportedShape);
    }
    Ok(())
}

fn validate_document_envelope(
    document: &PreservingXmlDocument,
) -> Result<(), TableLayoutHwpxError> {
    for token in document
        .tokens()
        .iter()
        .filter(|token| token.element_index().is_none())
    {
        if !matches!(
            token.kind(),
            XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration | XmlTokenKind::Whitespace
        ) {
            return Err(TableLayoutHwpxError::UnsupportedShape);
        }
    }
    Ok(())
}

fn hex_digest(value: [u8; 32]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in value {
        output.push(char::from(HEX[usize::from(byte >> 4)]));
        output.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    output
}
