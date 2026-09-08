use std::collections::BTreeMap;

use domain_ir::{
    FormulaCell, TABLE_PROPERTIES_SCHEMA_VERSION, TableCellBorderState, TableCellPropertyDraft,
    TableCellPropertyValue, TableDiagonalApplyMode, TableDiagonalCenterLine, TableDiagonalPatch,
    TableDiagonalSlash, TableDiagonalSlashType, TableDiagonalValue, TablePropertiesError,
    TablePropertiesLimits, TablePropertiesOperation, TablePropertiesPlan, TablePropertiesState,
    TablePropertiesStateDraft, TablePropertyRegion, table_diagonal_identity_sha256,
};
use thiserror::Error;

use crate::{
    CellMargins, CellProtection, CellTextDirection, CellVerticalAlignment, HorizontalAlignment,
    TableCellStyleLimits, TableCellStyleProfile,
};

use super::*;

pub const TABLE_PROPERTIES_HWPX_PROFILE_ID: &str = "hwpx-agent.table-properties-hwpx.hancom-2020/1";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TablePropertiesHwpxLimits {
    pub native: TableRulingHwpxLimits,
    pub cell_style: TableCellStyleLimits,
    pub properties: TablePropertiesLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePropertiesHwpxTableValue {
    pub lock: bool,
    pub border_fill_sha256: String,
    pub no_adjust: bool,
}

impl std::fmt::Debug for TablePropertiesHwpxTableValue {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxTableValue")
            .field("lock", &self.lock)
            .field("border_fill_sha256", &"<redacted>")
            .field("no_adjust", &self.no_adjust)
            .finish()
    }
}

impl TablePropertiesHwpxTableValue {
    /// Returns the exact typed identity used by `table.properties`.
    ///
    /// # Errors
    ///
    /// Rejects a non-canonical border/fill digest.
    pub fn canonical_sha256(&self) -> Result<String, TablePropertiesHwpxError> {
        require_digest(&self.border_fill_sha256)?;
        let mut digest = Sha256::new();
        digest.update(b"hwpx-agent.table-properties-hwpx-table-value/v1\0");
        hash_bool(&mut digest, self.lock);
        hash_part(&mut digest, &self.border_fill_sha256);
        hash_bool(&mut digest, self.no_adjust);
        Ok(hex(digest.finalize()))
    }
}

#[derive(Clone, Copy, Eq, PartialEq)]
pub struct TablePropertiesHwpxCellValue {
    pub margins: Option<CellMargins>,
    pub paragraph_property_id_ref: u32,
    pub horizontal_alignment: HorizontalAlignment,
    pub vertical_alignment: CellVerticalAlignment,
    pub text_direction: CellTextDirection,
    pub protection: CellProtection,
}

impl std::fmt::Debug for TablePropertiesHwpxCellValue {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxCellValue")
            .field("margins", &self.margins)
            .field("paragraph_property_id_ref", &"<redacted>")
            .field("horizontal_alignment", &self.horizontal_alignment)
            .field("vertical_alignment", &self.vertical_alignment)
            .field("text_direction", &self.text_direction)
            .field("protection", &self.protection)
            .finish()
    }
}

impl TablePropertiesHwpxCellValue {
    #[must_use]
    pub fn canonical_sha256(self) -> String {
        let mut digest = Sha256::new();
        digest.update(b"hwpx-agent.table-properties-hwpx-cell-value/v1\0");
        match self.margins {
            Some(value) => {
                hash_part(&mut digest, "explicit");
                for number in [value.left, value.right, value.top, value.bottom] {
                    hash_part(&mut digest, &number.to_string());
                }
            }
            None => hash_part(&mut digest, "inherited"),
        }
        hash_part(&mut digest, &self.paragraph_property_id_ref.to_string());
        hash_part(&mut digest, horizontal_alignment(self.horizontal_alignment));
        hash_part(&mut digest, vertical_alignment(self.vertical_alignment));
        hash_part(&mut digest, text_direction(self.text_direction));
        hash_part(&mut digest, protection(self.protection));
        hex(digest.finalize())
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePropertiesHwpxDiagonalBinding {
    pub master_cell_id: LogicalId,
    pub apply_mode: TableDiagonalApplyMode,
    pub region: Option<TablePropertyRegion>,
    pub value: TableDiagonalValue,
}

impl std::fmt::Debug for TablePropertiesHwpxDiagonalBinding {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxDiagonalBinding")
            .field("master_cell_id", &"<redacted>")
            .field("apply_mode", &self.apply_mode)
            .field("region", &self.region)
            .field("value", &self.value)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePropertiesHwpxBinding {
    pub table: TableRulingHwpxBinding,
    pub diagonals: Vec<TablePropertiesHwpxDiagonalBinding>,
}

impl std::fmt::Debug for TablePropertiesHwpxBinding {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxBinding")
            .field("table", &self.table)
            .field("diagonal_binding_count", &self.diagonals.len())
            .finish()
    }
}

#[derive(Clone, Default, Eq, PartialEq)]
pub struct TablePropertiesHwpxValueCatalog {
    pub table_values: Vec<TablePropertiesHwpxTableValue>,
    pub cell_values: Vec<TablePropertiesHwpxCellValue>,
    pub lines: Vec<BorderLine>,
    pub backgrounds: Vec<FillBrush>,
    pub border_fills: Vec<BorderFill>,
}

impl std::fmt::Debug for TablePropertiesHwpxValueCatalog {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxValueCatalog")
            .field("table_value_count", &self.table_values.len())
            .field("cell_value_count", &self.cell_values.len())
            .field("line_count", &self.lines.len())
            .field("background_count", &self.backgrounds.len())
            .field("border_fill_count", &self.border_fills.len())
            .finish()
    }
}

impl TablePropertiesHwpxValueCatalog {
    /// Returns the exact identity accepted by border and diagonal line patches.
    ///
    /// # Errors
    ///
    /// Rejects an invisible `NONE` line, which must be represented by the planner's `Clear` form.
    pub fn line_sha256(value: BorderLine) -> Result<String, TablePropertiesHwpxError> {
        line_digest(value).ok_or(TablePropertiesHwpxError::MissingCatalogValue)
    }

    #[must_use]
    pub fn background_sha256(value: &FillBrush) -> String {
        background_digest(value)
    }

    #[must_use]
    pub fn border_fill_sha256(value: &BorderFill) -> String {
        border_fill_digest(value)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePropertiesHwpxReadback {
    pub profile_id: &'static str,
    pub grid: TableGrid,
    pub state: TablePropertiesState,
    pub table_value: TablePropertiesHwpxTableValue,
    pub cell_values: Vec<TablePropertiesHwpxCellValue>,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub table_content_sha256: [u8; 32],
    pub border_fill_count: usize,
    pub payload_block_count: usize,
    pub formula_count: usize,
}

impl std::fmt::Debug for TablePropertiesHwpxReadback {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("rows", &self.grid.rows())
            .field("columns", &self.grid.columns())
            .field("cell_count", &self.grid.master_cell_count())
            .field("border_fill_count", &self.border_fill_count)
            .field("payload_block_count", &self.payload_block_count)
            .field("formula_count", &self.formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePropertiesHwpxPartBinding {
    pub header_sha256: String,
    pub section_sha256: String,
    pub document_flow_sha256: String,
}

impl TablePropertiesHwpxPartBinding {
    /// Binds the exact source parts and the caller's current document-flow identity.
    ///
    /// # Errors
    ///
    /// Rejects a malformed flow digest.
    pub fn from_readback(
        readback: &TablePropertiesHwpxReadback,
        document_flow_sha256: String,
    ) -> Result<Self, TablePropertiesHwpxError> {
        require_digest(&document_flow_sha256)?;
        Ok(Self {
            header_sha256: hex(readback.header_sha256),
            section_sha256: hex(readback.section_sha256),
            document_flow_sha256,
        })
    }
}

impl std::fmt::Debug for TablePropertiesHwpxPartBinding {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxPartBinding")
            .field("header_sha256", &"<redacted>")
            .field("section_sha256", &"<redacted>")
            .field("document_flow_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePropertiesHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: [u8; 32],
    pub target_state_sha256: [u8; 32],
    pub grid_sha256: [u8; 32],
    pub plan_sha256: [u8; 32],
    pub document_flow_sha256: [u8; 32],
    pub added_border_fill_count: usize,
    pub changed_master_cell_count: usize,
    pub preserved_formula_count: usize,
}

impl std::fmt::Debug for TablePropertiesHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("added_border_fill_count", &self.added_border_fill_count)
            .field("changed_master_cell_count", &self.changed_master_cell_count)
            .field("preserved_formula_count", &self.preserved_formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TablePropertiesHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TablePropertiesHwpxBinding,
    pub receipt: TablePropertiesHwpxLoweringReceipt,
}

impl std::fmt::Debug for TablePropertiesHwpxLoweredParts {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TablePropertiesHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("binding", &self.binding)
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error)]
pub enum TablePropertiesHwpxError {
    #[error("table-properties HWPX binding is invalid")]
    InvalidBinding,
    #[error("table-properties HWPX part or document-flow binding drifted")]
    PartBindingMismatch,
    #[error("table-properties HWPX source state or grid drifted")]
    SourceStateMismatch,
    #[error("table-properties HWPX plan receipt is inconsistent")]
    PlanBindingMismatch,
    #[error("table-properties HWPX typed value is absent from the supplied catalog")]
    MissingCatalogValue,
    #[error("table-properties HWPX typed catalog contains an ambiguous identity")]
    AmbiguousCatalogValue,
    #[error("table-properties HWPX native diagonal needs an exact logical binding")]
    MissingDiagonalBinding,
    #[error("table-properties HWPX native diagonal differs from its logical binding")]
    DiagonalBindingMismatch,
    #[error("table-properties HWPX native property shape is unsupported")]
    UnsupportedPropertyShape,
    #[error("table-properties HWPX header border/fill capacity was exceeded")]
    BorderFillLimit,
    #[error("table-properties HWPX allocation failed")]
    AllocationFailed,
    #[error("table-properties HWPX output exceeded its finite bound")]
    OutputLimit,
    #[error("table-properties HWPX exact semantic readback differs from the target")]
    ReadbackMismatch,
    #[error("table-properties HWPX ruling/native admission failed")]
    Native(#[from] TableRulingHwpxError),
    #[error("table-properties HWPX logical planner rejected state")]
    Properties(#[from] TablePropertiesError),
    #[error("table-properties HWPX formula admission failed")]
    Formula(#[from] TableFormulaHwpxError),
    #[error("table-properties HWPX formula core admission failed")]
    FormulaCore(#[from] domain_ir::FormulaError),
    #[error("table-properties HWPX XML admission failed")]
    Xml(#[from] PreservingXmlError),
    #[error("table-properties HWPX header catalog admission failed")]
    Header(#[from] ParagraphStyleError),
    #[error("table-properties HWPX cell-style admission failed")]
    CellStyle(#[from] crate::TableCellStyleError),
    #[error("table-properties HWPX grid admission failed")]
    Grid(#[from] TableGridError),
}

impl TablePropertiesHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidBinding => "table_properties_hwpx_invalid_binding",
            Self::PartBindingMismatch => "table_properties_hwpx_part_binding_mismatch",
            Self::SourceStateMismatch => "table_properties_hwpx_source_state_mismatch",
            Self::PlanBindingMismatch => "table_properties_hwpx_plan_binding_mismatch",
            Self::MissingCatalogValue => "table_properties_hwpx_missing_catalog_value",
            Self::AmbiguousCatalogValue => "table_properties_hwpx_ambiguous_catalog_value",
            Self::MissingDiagonalBinding => "table_properties_hwpx_missing_diagonal_binding",
            Self::DiagonalBindingMismatch => "table_properties_hwpx_diagonal_binding_mismatch",
            Self::UnsupportedPropertyShape => "table_properties_hwpx_unsupported_property_shape",
            Self::BorderFillLimit => "table_properties_hwpx_border_fill_limit",
            Self::AllocationFailed => "table_properties_hwpx_allocation",
            Self::OutputLimit => "table_properties_hwpx_output_limit",
            Self::ReadbackMismatch => "table_properties_hwpx_readback_mismatch",
            Self::Native(_) => "table_properties_hwpx_native_admission",
            Self::Properties(_) => "table_properties_hwpx_properties_core",
            Self::Formula(_) => "table_properties_hwpx_formula_admission",
            Self::FormulaCore(_) => "table_properties_hwpx_formula_core",
            Self::Xml(_) => "table_properties_hwpx_xml_admission",
            Self::Header(_) => "table_properties_hwpx_header_admission",
            Self::CellStyle(_) => "table_properties_hwpx_cell_style_admission",
            Self::Grid(_) => "table_properties_hwpx_grid_admission",
        }
    }
}

#[derive(Debug)]
pub struct TablePropertiesHwpxReader;

impl TablePropertiesHwpxReader {
    /// Lifts one selected table into a complete property state.
    ///
    /// HWPX does not persist each-cell versus unified diagonal intent, so every visible native
    /// diagonal must have one exact logical binding whose value is checked against the borderFill.
    ///
    /// # Errors
    ///
    /// Rejects malformed package parts, identity/grid drift, unsupported formula or property
    /// shapes, dangling styles, missing/extra diagonal bindings, and finite-bound failures.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TablePropertiesHwpxBinding,
        limits: TablePropertiesHwpxLimits,
    ) -> Result<TablePropertiesHwpxReadback, TablePropertiesHwpxError> {
        read_existing(header, section, table_ordinal, binding, &limits)
    }
}

#[derive(Debug)]
pub struct TablePropertiesHwpxLowerer;

impl TablePropertiesHwpxLowerer {
    /// Lowers one exact property plan into coordinated header and section parts.
    ///
    /// Table/cell opaque identities resolve only through typed values. Line, fill, and table-frame
    /// border identities resolve only through typed native catalog entries, never raw XML.
    ///
    /// # Errors
    ///
    /// Rejects part/state/grid/plan drift, unresolved or ambiguous catalog identities, diagonal
    /// binding mismatch, header capacity, unsupported native shapes, or semantic readback drift.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TablePropertiesHwpxBinding,
        part_binding: &TablePropertiesHwpxPartBinding,
        current_document_flow_sha256: &str,
        source_state: &TablePropertiesState,
        source_grid: &TableGrid,
        plan: &TablePropertiesPlan,
        values: &TablePropertiesHwpxValueCatalog,
        limits: TablePropertiesHwpxLimits,
    ) -> Result<TablePropertiesHwpxLoweredParts, TablePropertiesHwpxError> {
        validate_part_binding(header, section, part_binding, current_document_flow_sha256)?;
        let source = read_existing(header, section, table_ordinal, binding, &limits)?;
        if source.state != *source_state || source.grid != *source_grid {
            return Err(TablePropertiesHwpxError::SourceStateMismatch);
        }
        let target_state = validate_plan(source_state, source_grid, plan, &limits)?;
        let target_binding = target_diagonal_binding(binding, plan, source_grid, &limits)?;
        let rendered = render(
            header,
            section,
            table_ordinal,
            binding,
            &source,
            &target_state,
            &target_binding,
            plan,
            values,
            &limits,
        )?;
        let reopened = read_existing(
            &rendered.header,
            &rendered.section,
            table_ordinal,
            &target_binding,
            &limits,
        )?;
        if reopened.grid != *source_grid || reopened.state != target_state {
            return Err(TablePropertiesHwpxError::ReadbackMismatch);
        }
        let receipt = TablePropertiesHwpxLoweringReceipt {
            profile_id: TABLE_PROPERTIES_HWPX_PROFILE_ID,
            capability_id: plan.capability_id(),
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&rendered.header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&rendered.section).into(),
            source_state_sha256: source_state.canonical_sha256(limits.properties)?,
            target_state_sha256: target_state.canonical_sha256(limits.properties)?,
            grid_sha256: source_grid.canonical_sha256()?,
            plan_sha256: plan.canonical_sha256(limits.properties)?,
            document_flow_sha256: parse_properties_digest(current_document_flow_sha256)?,
            added_border_fill_count: rendered.added_border_fill_count,
            changed_master_cell_count: plan.receipt().changed_master_cell_count,
            preserved_formula_count: plan.receipt().formula_preserved_count,
        };
        Ok(TablePropertiesHwpxLoweredParts {
            header: rendered.header,
            section: rendered.section,
            binding: target_binding,
            receipt,
        })
    }
}

fn read_existing(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TablePropertiesHwpxBinding,
    limits: &TablePropertiesHwpxLimits,
) -> Result<TablePropertiesHwpxReadback, TablePropertiesHwpxError> {
    let layout =
        TableLayoutHwpxReader::read_in_section(section, table_ordinal, limits.native.layout)
            .map_err(TableRulingHwpxError::from)?;
    let grid = validated_grid(&layout, &binding.table, limits.native.grid)?;
    let catalog = ParagraphStyleCatalogReader::read(header, limits.native.paragraph_style)?;
    let borders = border_map(&catalog.border_fills)?;
    let document = PreservingXmlDocument::parse(section)?;
    let root = selected_table(&document, table_ordinal)?;
    let cells = selected_cells(&document, root, layout.cells.len())?;
    let (formula, formula_count) =
        read_supported_formula(section, table_ordinal, root, &document, limits)?;
    let (native_cells, payload_block_count) =
        read_native_cells(section, &document, &cells, &layout.cells, &borders)?;
    let grid_sha256 = hex(grid.canonical_sha256()?);
    validate_diagonal_binding_topology(
        &binding.diagonals,
        &binding.table.table_id,
        &grid_sha256,
        &grid,
        limits.properties,
    )?;
    let diagonal_map = diagonal_binding_map(&binding.diagonals)?;
    let table_value = read_table_value(&document, root, &borders)?;
    let (state, cell_values) = build_property_state(
        &document,
        &cells,
        &native_cells,
        &grid,
        &grid_sha256,
        &catalog,
        binding,
        &diagonal_map,
        formula.as_ref(),
        limits,
        &table_value,
    )?;
    Ok(TablePropertiesHwpxReadback {
        profile_id: TABLE_PROPERTIES_HWPX_PROFILE_ID,
        grid,
        state,
        table_value,
        cell_values,
        header_sha256: Sha256::digest(header).into(),
        section_sha256: Sha256::digest(section).into(),
        table_content_sha256: layout.content_sha256,
        border_fill_count: catalog.border_fills.len(),
        payload_block_count,
        formula_count,
    })
}

fn read_supported_formula(
    section: &[u8],
    table_ordinal: usize,
    root: usize,
    document: &PreservingXmlDocument,
    limits: &TablePropertiesHwpxLimits,
) -> Result<(Option<FormulaCell>, usize), TablePropertiesHwpxError> {
    let count = formula_field_count(document, root)?;
    let formula = match count {
        0 => None,
        1 => Some(
            TableFormulaHwpxReader::read_in_section(
                section,
                table_ordinal,
                limits.native.formula_hwpx,
                limits.native.formula,
            )?
            .formula,
        ),
        _ => return Err(TablePropertiesHwpxError::UnsupportedPropertyShape),
    };
    Ok((formula, count))
}

#[allow(clippy::too_many_arguments)]
fn build_property_state(
    document: &PreservingXmlDocument,
    cells: &[(usize, CellCoordinate)],
    native_cells: &[NativeCell],
    grid: &TableGrid,
    grid_sha256: &str,
    catalog: &crate::ParagraphStyleCatalog,
    binding: &TablePropertiesHwpxBinding,
    diagonal_map: &BTreeMap<LogicalId, &TablePropertiesHwpxDiagonalBinding>,
    formula: Option<&FormulaCell>,
    limits: &TablePropertiesHwpxLimits,
    table_value: &TablePropertiesHwpxTableValue,
) -> Result<(TablePropertiesState, Vec<TablePropertiesHwpxCellValue>), TablePropertiesHwpxError> {
    let mut cell_values = Vec::new();
    cell_values
        .try_reserve_exact(native_cells.len())
        .map_err(|_| TablePropertiesHwpxError::AllocationFailed)?;
    let mut drafts = Vec::new();
    drafts
        .try_reserve_exact(native_cells.len())
        .map_err(|_| TablePropertiesHwpxError::AllocationFailed)?;
    let mut consumed_diagonals = 0_usize;
    for (index, ((native, identity), (cell_element, coordinate))) in native_cells
        .iter()
        .zip(&binding.table.cells)
        .zip(cells)
        .enumerate()
    {
        if native.coordinate != *coordinate
            || grid
                .master_cells()
                .get(index)
                .is_none_or(|span| span.master_cell_id != identity.master_cell_id)
        {
            return Err(TablePropertiesHwpxError::InvalidBinding);
        }
        let cell_value = read_cell_value(document, *cell_element, catalog, limits.cell_style)?;
        let diagonal_sha256 = read_diagonal_identity(
            native,
            &identity.master_cell_id,
            &binding.table.table_id,
            grid_sha256,
            diagonal_map.get(&identity.master_cell_id).copied(),
            limits.properties,
        )?;
        if diagonal_sha256.is_some() {
            consumed_diagonals = consumed_diagonals
                .checked_add(1)
                .ok_or(TablePropertiesHwpxError::AllocationFailed)?;
        }
        let formula_sha256 = formula
            .filter(|value| value.owner() == native.coordinate)
            .map(|value| value.canonical_sha256(limits.native.formula))
            .transpose()?
            .map(hex);
        drafts.push(TableCellPropertyDraft {
            master_cell_id: identity.master_cell_id.clone(),
            coordinate: native.coordinate,
            payload_sha256: aggregate_payload_digest(&native.payload_sha256),
            formula_sha256,
            properties: TableCellPropertyValue {
                non_border_properties_sha256: cell_value.canonical_sha256(),
                borders: TableCellBorderState {
                    top_sha256: line_digest(native.border.top),
                    right_sha256: line_digest(native.border.right),
                    bottom_sha256: line_digest(native.border.bottom),
                    left_sha256: line_digest(native.border.left),
                },
                background_sha256: native.border.fill_brush.as_ref().map(background_digest),
                diagonal_sha256,
            },
        });
        cell_values.push(cell_value);
    }
    if consumed_diagonals != diagonal_map.len()
        || formula.is_some_and(|value| {
            !native_cells
                .iter()
                .any(|cell| cell.coordinate == value.owner())
        })
    {
        return Err(TablePropertiesHwpxError::InvalidBinding);
    }
    let state = TablePropertiesState::from_draft(
        TablePropertiesStateDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: binding.table.table_id.clone(),
            grid_sha256: grid_sha256.to_owned(),
            table_properties_sha256: table_value.canonical_sha256()?,
            cells: drafts,
        },
        grid,
        limits.properties,
    )?;
    Ok((state, cell_values))
}

fn validate_part_binding(
    header: &[u8],
    section: &[u8],
    binding: &TablePropertiesHwpxPartBinding,
    current_document_flow_sha256: &str,
) -> Result<(), TablePropertiesHwpxError> {
    require_digest(&binding.header_sha256)?;
    require_digest(&binding.section_sha256)?;
    require_digest(&binding.document_flow_sha256)?;
    require_digest(current_document_flow_sha256)?;
    if binding.header_sha256 != hex(Sha256::digest(header))
        || binding.section_sha256 != hex(Sha256::digest(section))
        || binding.document_flow_sha256 != current_document_flow_sha256
    {
        return Err(TablePropertiesHwpxError::PartBindingMismatch);
    }
    Ok(())
}

fn validate_plan(
    source: &TablePropertiesState,
    grid: &TableGrid,
    plan: &TablePropertiesPlan,
    limits: &TablePropertiesHwpxLimits,
) -> Result<TablePropertiesState, TablePropertiesHwpxError> {
    let before = hex(source.canonical_sha256(limits.properties)?);
    let grid_sha256 = hex(grid.canonical_sha256()?);
    let receipt = plan.receipt();
    if receipt.schema_version != TABLE_PROPERTIES_SCHEMA_VERSION
        || receipt.capability_id != plan.capability_id()
        || receipt.table_id != *source.table_id()
        || receipt.grid_sha256 != grid_sha256
        || receipt.before_state_sha256 != before
        || receipt.before_table_properties_sha256 != source.table_properties_sha256()
        || receipt.after_table_properties_sha256 != plan.table_properties_sha256()
        || plan.operation().capability_id() != plan.capability_id()
    {
        return Err(TablePropertiesHwpxError::PlanBindingMismatch);
    }
    let mut mutations = BTreeMap::new();
    for mutation in plan.mutations() {
        if mutations
            .insert(mutation.master_cell_id.clone(), mutation)
            .is_some()
        {
            return Err(TablePropertiesHwpxError::PlanBindingMismatch);
        }
    }
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(source.cells().len())
        .map_err(|_| TablePropertiesHwpxError::AllocationFailed)?;
    for cell in source.cells() {
        let properties = if let Some(mutation) = mutations.remove(&cell.master_cell_id) {
            if mutation.coordinate != cell.coordinate
                || mutation.before != cell.properties
                || mutation.payload_sha256 != cell.payload_sha256
                || mutation.formula_sha256 != cell.formula_sha256
            {
                return Err(TablePropertiesHwpxError::PlanBindingMismatch);
            }
            mutation.after.clone()
        } else {
            cell.properties.clone()
        };
        cells.push(TableCellPropertyDraft {
            master_cell_id: cell.master_cell_id.clone(),
            coordinate: cell.coordinate,
            payload_sha256: cell.payload_sha256.clone(),
            formula_sha256: cell.formula_sha256.clone(),
            properties,
        });
    }
    if !mutations.is_empty() {
        return Err(TablePropertiesHwpxError::PlanBindingMismatch);
    }
    let target = TablePropertiesState::from_draft(
        TablePropertiesStateDraft {
            schema_version: TABLE_PROPERTIES_SCHEMA_VERSION.to_owned(),
            table_id: source.table_id().clone(),
            grid_sha256,
            table_properties_sha256: plan.table_properties_sha256().to_owned(),
            cells,
        },
        grid,
        limits.properties,
    )?;
    if receipt.after_state_sha256 != hex(target.canonical_sha256(limits.properties)?) {
        return Err(TablePropertiesHwpxError::PlanBindingMismatch);
    }
    Ok(target)
}

#[derive(Debug)]
struct PropertiesRenderedParts {
    header: Vec<u8>,
    section: Vec<u8>,
    added_border_fill_count: usize,
}

#[allow(clippy::too_many_arguments)]
fn render(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    source_binding: &TablePropertiesHwpxBinding,
    source: &TablePropertiesHwpxReadback,
    target_state: &TablePropertiesState,
    target_binding: &TablePropertiesHwpxBinding,
    plan: &TablePropertiesPlan,
    values: &TablePropertiesHwpxValueCatalog,
    limits: &TablePropertiesHwpxLimits,
) -> Result<PropertiesRenderedParts, TablePropertiesHwpxError> {
    validate_catalog_bounds(values, limits)?;
    let catalog = ParagraphStyleCatalogReader::read(header, limits.native.paragraph_style)?;
    let mut resolver = StyleResolver::new(catalog.border_fills.clone())?;
    let maps = ValueMaps::new(&catalog, values, &mut resolver, limits.cell_style)?;
    let document = PreservingXmlDocument::parse(section)?;
    let root = selected_table(&document, table_ordinal)?;
    let layout =
        TableLayoutHwpxReader::read_in_section(section, table_ordinal, limits.native.layout)
            .map_err(TableRulingHwpxError::from)?;
    let cells = selected_cells(&document, root, layout.cells.len())?;
    let borders = border_map(&catalog.border_fills)?;
    let (native_cells, _) = read_native_cells(section, &document, &cells, &layout.cells, &borders)?;
    if native_cells.len() != source_binding.table.cells.len()
        || source.cell_values.len() != native_cells.len()
    {
        return Err(TablePropertiesHwpxError::InvalidBinding);
    }

    let table_value = resolve_table_value(source, target_state, &maps)?;
    let table_border = maps
        .border_fills
        .get(&table_value.border_fill_sha256)
        .cloned()
        .ok_or(TablePropertiesHwpxError::MissingCatalogValue)?;
    let table_border_id = resolver.intern(table_border)?;
    let target_diagonals = diagonal_binding_map(&target_binding.diagonals)?;
    let mutation_map = plan
        .mutations()
        .iter()
        .map(|value| (value.master_cell_id.clone(), value))
        .collect::<BTreeMap<_, _>>();
    if mutation_map.len() != plan.mutations().len() {
        return Err(TablePropertiesHwpxError::PlanBindingMismatch);
    }
    let mut edits = Vec::new();
    edits
        .try_reserve_exact(
            4_usize
                .checked_add(
                    plan.mutations()
                        .len()
                        .checked_mul(16)
                        .ok_or(TablePropertiesHwpxError::AllocationFailed)?,
                )
                .ok_or(TablePropertiesHwpxError::AllocationFailed)?,
        )
        .map_err(|_| TablePropertiesHwpxError::AllocationFailed)?;
    append_table_edits(&document, root, &table_value, table_border_id, &mut edits)?;
    append_mutated_cell_edits(
        &document,
        &cells,
        &native_cells,
        source_binding,
        source,
        target_state,
        &target_diagonals,
        &mutation_map,
        &maps,
        &mut resolver,
        &catalog,
        limits,
        &mut edits,
    )?;
    if resolver.borders.len() > limits.native.paragraph_style.config().border_fills {
        return Err(TablePropertiesHwpxError::BorderFillLimit);
    }
    let section = apply_edits(
        section,
        &mut edits,
        limits.native.layout.config().output_bytes,
    )?;
    let new_borders = resolver
        .borders
        .get(resolver.original_count..)
        .ok_or(TablePropertiesHwpxError::BorderFillLimit)?;
    let header = patch_header(
        header,
        new_borders,
        resolver.borders.len(),
        limits.native.paragraph_style.config().input_bytes,
    )?;
    Ok(PropertiesRenderedParts {
        header,
        section,
        added_border_fill_count: new_borders.len(),
    })
}

fn append_table_edits(
    document: &PreservingXmlDocument,
    root: usize,
    value: &TablePropertiesHwpxTableValue,
    border_fill_id: u32,
    edits: &mut Vec<RawEdit>,
) -> Result<(), TablePropertiesHwpxError> {
    push_attribute_edit_text(document, root, "lock", bool01(value.lock).to_owned(), edits)?;
    push_attribute_edit(document, root, "borderFillIDRef", border_fill_id, edits)?;
    push_attribute_edit_text(
        document,
        root,
        "noAdjust",
        bool01(value.no_adjust).to_owned(),
        edits,
    )?;
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn append_mutated_cell_edits(
    document: &PreservingXmlDocument,
    cells: &[(usize, CellCoordinate)],
    native_cells: &[NativeCell],
    source_binding: &TablePropertiesHwpxBinding,
    source: &TablePropertiesHwpxReadback,
    target_state: &TablePropertiesState,
    target_diagonals: &BTreeMap<LogicalId, &TablePropertiesHwpxDiagonalBinding>,
    mutation_map: &BTreeMap<LogicalId, &domain_ir::TableCellPropertyMutation>,
    maps: &ValueMaps,
    resolver: &mut StyleResolver,
    catalog: &crate::ParagraphStyleCatalog,
    limits: &TablePropertiesHwpxLimits,
    edits: &mut Vec<RawEdit>,
) -> Result<(), TablePropertiesHwpxError> {
    for (index, (((native, identity), (cell_element, coordinate)), source_cell_value)) in
        native_cells
            .iter()
            .zip(&source_binding.table.cells)
            .zip(cells)
            .zip(&source.cell_values)
            .enumerate()
    {
        if native.coordinate != *coordinate {
            return Err(TablePropertiesHwpxError::InvalidBinding);
        }
        let Some(mutation) = mutation_map.get(&identity.master_cell_id) else {
            continue;
        };
        let target_cell = target_state
            .cells()
            .get(index)
            .filter(|cell| cell.master_cell_id == identity.master_cell_id)
            .ok_or(TablePropertiesHwpxError::PlanBindingMismatch)?;
        if mutation.after != target_cell.properties {
            return Err(TablePropertiesHwpxError::PlanBindingMismatch);
        }
        let cell_value = resolve_cell_value(source_cell_value, mutation, maps)?;
        let mut border = native.border.clone();
        border.top = resolve_line(
            mutation.after.borders.top_sha256.as_deref(),
            border.top,
            &maps.lines,
        )?;
        border.right = resolve_line(
            mutation.after.borders.right_sha256.as_deref(),
            border.right,
            &maps.lines,
        )?;
        border.bottom = resolve_line(
            mutation.after.borders.bottom_sha256.as_deref(),
            border.bottom,
            &maps.lines,
        )?;
        border.left = resolve_line(
            mutation.after.borders.left_sha256.as_deref(),
            border.left,
            &maps.lines,
        )?;
        border.fill_brush = mutation
            .after
            .background_sha256
            .as_ref()
            .map(|digest| {
                maps.backgrounds
                    .get(digest)
                    .copied()
                    .ok_or(TablePropertiesHwpxError::MissingCatalogValue)
            })
            .transpose()?;
        apply_native_diagonal(
            &mut border,
            mutation.after.diagonal_sha256.as_deref(),
            target_diagonals.get(&identity.master_cell_id).copied(),
            &maps.lines,
            target_state.table_id(),
            target_state.grid_sha256(),
            limits.properties,
        )?;
        let border_id = resolver.intern(border)?;
        append_cell_edits(
            document,
            *cell_element,
            cell_value,
            border_id,
            catalog,
            limits.cell_style,
            edits,
        )?;
    }
    Ok(())
}

fn resolve_cell_value(
    source: &TablePropertiesHwpxCellValue,
    mutation: &domain_ir::TableCellPropertyMutation,
    maps: &ValueMaps,
) -> Result<TablePropertiesHwpxCellValue, TablePropertiesHwpxError> {
    if mutation.after.non_border_properties_sha256 == source.canonical_sha256() {
        Ok(*source)
    } else {
        maps.cell_values
            .get(&mutation.after.non_border_properties_sha256)
            .copied()
            .ok_or(TablePropertiesHwpxError::MissingCatalogValue)
    }
}

fn resolve_table_value<'a>(
    source: &'a TablePropertiesHwpxReadback,
    target_state: &TablePropertiesState,
    maps: &'a ValueMaps,
) -> Result<TablePropertiesHwpxTableValue, TablePropertiesHwpxError> {
    if target_state.table_properties_sha256() == source.state.table_properties_sha256() {
        Ok(source.table_value.clone())
    } else {
        maps.table_values
            .get(target_state.table_properties_sha256())
            .cloned()
            .ok_or(TablePropertiesHwpxError::MissingCatalogValue)
    }
}

struct ValueMaps {
    table_values: BTreeMap<String, TablePropertiesHwpxTableValue>,
    cell_values: BTreeMap<String, TablePropertiesHwpxCellValue>,
    lines: BTreeMap<String, BorderLine>,
    backgrounds: BTreeMap<String, FillBrush>,
    border_fills: BTreeMap<String, BorderFill>,
}

impl ValueMaps {
    fn new(
        catalog: &crate::ParagraphStyleCatalog,
        values: &TablePropertiesHwpxValueCatalog,
        resolver: &mut StyleResolver,
        cell_limits: TableCellStyleLimits,
    ) -> Result<Self, TablePropertiesHwpxError> {
        let mut table_values = BTreeMap::new();
        for value in &values.table_values {
            insert_unique(&mut table_values, value.canonical_sha256()?, value.clone())?;
        }
        let mut cell_values = BTreeMap::new();
        for value in &values.cell_values {
            insert_unique(&mut cell_values, value.canonical_sha256(), *value)?;
        }
        for value in &values.lines {
            let digest =
                line_digest(*value).ok_or(TablePropertiesHwpxError::MissingCatalogValue)?;
            insert_line(&mut resolver.edge_lines, digest, *value)?;
        }
        let mut backgrounds = BTreeMap::new();
        let mut border_fills = BTreeMap::new();
        for value in catalog.border_fills.iter().chain(&values.border_fills) {
            insert_unique(&mut border_fills, border_fill_digest(value), value.clone())?;
            if let Some(background) = value.fill_brush {
                insert_unique(&mut backgrounds, background_digest(&background), background)?;
            }
        }
        for value in &values.backgrounds {
            insert_unique(&mut backgrounds, background_digest(value), *value)?;
        }
        let output = Self {
            table_values,
            cell_values,
            lines: resolver.edge_lines.clone(),
            backgrounds,
            border_fills,
        };
        for value in output.table_values.values() {
            if !output.border_fills.contains_key(&value.border_fill_sha256) {
                return Err(TablePropertiesHwpxError::MissingCatalogValue);
            }
        }
        for value in output.cell_values.values() {
            validate_cell_value(catalog, *value, cell_limits)?;
        }
        Ok(output)
    }
}

fn insert_unique<T: Eq>(
    output: &mut BTreeMap<String, T>,
    digest: String,
    value: T,
) -> Result<(), TablePropertiesHwpxError> {
    if let Some(previous) = output.get(&digest) {
        if previous != &value {
            return Err(TablePropertiesHwpxError::AmbiguousCatalogValue);
        }
        return Ok(());
    }
    output.insert(digest, value);
    Ok(())
}

fn insert_line(
    output: &mut BTreeMap<String, BorderLine>,
    digest: String,
    value: BorderLine,
) -> Result<(), TablePropertiesHwpxError> {
    if output
        .get(&digest)
        .is_some_and(|previous| *previous != value)
    {
        return Err(TablePropertiesHwpxError::AmbiguousCatalogValue);
    }
    output.insert(digest, value);
    Ok(())
}

fn validate_catalog_bounds(
    values: &TablePropertiesHwpxValueCatalog,
    limits: &TablePropertiesHwpxLimits,
) -> Result<(), TablePropertiesHwpxError> {
    let maximum = limits.native.paragraph_style.config().border_fills;
    if [
        values.table_values.len(),
        values.cell_values.len(),
        values.lines.len(),
        values.backgrounds.len(),
        values.border_fills.len(),
    ]
    .into_iter()
    .any(|count| count > maximum)
    {
        return Err(TablePropertiesHwpxError::BorderFillLimit);
    }
    Ok(())
}

fn append_cell_edits(
    document: &PreservingXmlDocument,
    cell: usize,
    value: TablePropertiesHwpxCellValue,
    border_id: u32,
    catalog: &crate::ParagraphStyleCatalog,
    limits: TableCellStyleLimits,
    edits: &mut Vec<RawEdit>,
) -> Result<(), TablePropertiesHwpxError> {
    if border_id > u32::from(u16::MAX) {
        return Err(TablePropertiesHwpxError::MissingCatalogValue);
    }
    validate_cell_value(catalog, value, limits)?;
    let (protect, editable) = protection_flags(value.protection);
    push_attribute_edit_text(
        document,
        cell,
        "hasMargin",
        bool01(value.margins.is_some()).to_owned(),
        edits,
    )?;
    push_attribute_edit(document, cell, "borderFillIDRef", border_id, edits)?;
    push_attribute_edit_text(document, cell, "protect", bool01(protect).to_owned(), edits)?;
    push_attribute_edit_text(
        document,
        cell,
        "editable",
        bool01(editable).to_owned(),
        edits,
    )?;
    let margin = unique_child(document, cell, "cellMargin")?;
    if let Some(margins) = value.margins {
        for (name, number) in [
            ("left", margins.left),
            ("right", margins.right),
            ("top", margins.top),
            ("bottom", margins.bottom),
        ] {
            push_attribute_edit(document, margin, name, number, edits)?;
        }
    }
    let sub_list = unique_child(document, cell, "subList")?;
    push_attribute_edit_text(
        document,
        sub_list,
        "textDirection",
        native_text_direction(value.text_direction).to_owned(),
        edits,
    )?;
    push_attribute_edit_text(
        document,
        sub_list,
        "vertAlign",
        native_vertical_alignment(value.vertical_alignment).to_owned(),
        edits,
    )?;
    let paragraphs = direct_children_named(document, sub_list, "p")?;
    if paragraphs.is_empty() {
        return Err(TablePropertiesHwpxError::UnsupportedPropertyShape);
    }
    for paragraph in paragraphs {
        push_attribute_edit(
            document,
            paragraph,
            "paraPrIDRef",
            value.paragraph_property_id_ref,
            edits,
        )?;
    }
    Ok(())
}

fn validate_cell_value(
    catalog: &crate::ParagraphStyleCatalog,
    value: TablePropertiesHwpxCellValue,
    limits: TableCellStyleLimits,
) -> Result<(), TablePropertiesHwpxError> {
    if value.margins.is_some_and(|margins| {
        [margins.left, margins.right, margins.top, margins.bottom]
            .into_iter()
            .any(|number| number > limits.config().margin_hwpunit)
    }) {
        return Err(TablePropertiesHwpxError::MissingCatalogValue);
    }
    require_paragraph_alignment(
        catalog,
        value.paragraph_property_id_ref,
        value.horizontal_alignment,
    )
}

fn read_table_value(
    document: &PreservingXmlDocument,
    root: usize,
    borders: &BTreeMap<u32, &BorderFill>,
) -> Result<TablePropertiesHwpxTableValue, TablePropertiesHwpxError> {
    let border_id = required_u32(element(document, root)?, "borderFillIDRef")?;
    let border = borders
        .get(&border_id)
        .ok_or(TablePropertiesHwpxError::MissingCatalogValue)?;
    Ok(TablePropertiesHwpxTableValue {
        lock: required_bool(element(document, root)?, "lock")?,
        border_fill_sha256: border_fill_digest(border),
        no_adjust: required_bool(element(document, root)?, "noAdjust")?,
    })
}

fn read_cell_value(
    document: &PreservingXmlDocument,
    cell: usize,
    catalog: &crate::ParagraphStyleCatalog,
    limits: TableCellStyleLimits,
) -> Result<TablePropertiesHwpxCellValue, TablePropertiesHwpxError> {
    let readback = crate::table_cell_style::read_from_document(
        document,
        cell,
        TableCellStyleProfile::Hangul2020V2,
        catalog,
        limits,
    )?;
    let style = readback.style;
    Ok(TablePropertiesHwpxCellValue {
        margins: style.margins,
        paragraph_property_id_ref: style.paragraph_property_id_ref,
        horizontal_alignment: style.horizontal_alignment,
        vertical_alignment: style.vertical_alignment,
        text_direction: style.text_direction,
        protection: style.protection,
    })
}

fn read_diagonal_identity(
    native: &NativeCell,
    master_cell_id: &LogicalId,
    table_id: &LogicalId,
    grid_sha256: &str,
    binding: Option<&TablePropertiesHwpxDiagonalBinding>,
    limits: TablePropertiesLimits,
) -> Result<Option<String>, TablePropertiesHwpxError> {
    let visible = native.border.slash.slash_type != SlashType::None
        || native.border.back_slash.slash_type != SlashType::None
        || native.border.center_line != CenterLine::None;
    match (visible, binding) {
        (false, None) => Ok(None),
        (true, None) => Err(TablePropertiesHwpxError::MissingDiagonalBinding),
        (false, Some(_)) => Err(TablePropertiesHwpxError::DiagonalBindingMismatch),
        (true, Some(binding)) => {
            if binding.master_cell_id != *master_cell_id
                || !native_diagonal_matches(&native.border, &binding.value)
            {
                return Err(TablePropertiesHwpxError::DiagonalBindingMismatch);
            }
            Ok(Some(table_diagonal_identity_sha256(
                table_id,
                grid_sha256,
                binding.apply_mode,
                binding.region,
                &binding.value,
                limits,
            )?))
        }
    }
}

fn apply_native_diagonal(
    border: &mut BorderFill,
    expected_identity: Option<&str>,
    binding: Option<&TablePropertiesHwpxDiagonalBinding>,
    lines: &BTreeMap<String, BorderLine>,
    table_id: &LogicalId,
    grid_sha256: &str,
    limits: TablePropertiesLimits,
) -> Result<(), TablePropertiesHwpxError> {
    match (expected_identity, binding) {
        (None, None) => {
            border.slash = empty_slash();
            border.back_slash = empty_slash();
            border.center_line = CenterLine::None;
        }
        (Some(expected), Some(binding)) => {
            let actual = table_diagonal_identity_sha256(
                table_id,
                grid_sha256,
                binding.apply_mode,
                binding.region,
                &binding.value,
                limits,
            )?;
            if actual != expected {
                return Err(TablePropertiesHwpxError::DiagonalBindingMismatch);
            }
            border.slash = native_slash(binding.value.slash);
            border.back_slash = native_slash(binding.value.back_slash);
            border.center_line = native_center(binding.value.center_line);
            border.diagonal = *lines
                .get(&binding.value.line_sha256)
                .ok_or(TablePropertiesHwpxError::MissingCatalogValue)?;
        }
        _ => return Err(TablePropertiesHwpxError::DiagonalBindingMismatch),
    }
    Ok(())
}

fn target_diagonal_binding(
    source: &TablePropertiesHwpxBinding,
    plan: &TablePropertiesPlan,
    grid: &TableGrid,
    limits: &TablePropertiesHwpxLimits,
) -> Result<TablePropertiesHwpxBinding, TablePropertiesHwpxError> {
    let mut output = diagonal_binding_map(&source.diagonals)?
        .into_iter()
        .map(|(key, value)| (key, value.clone()))
        .collect::<BTreeMap<_, _>>();
    if let TablePropertiesOperation::CellDiagonal { apply_mode, patch } = plan.operation() {
        for mutation in plan.mutations() {
            match patch {
                TableDiagonalPatch::Clear => {
                    output.remove(&mutation.master_cell_id);
                }
                TableDiagonalPatch::Set { value } => {
                    let region = match apply_mode {
                        TableDiagonalApplyMode::EachCell => None,
                        TableDiagonalApplyMode::Unified => plan_region(plan, grid)?,
                    };
                    let expected = table_diagonal_identity_sha256(
                        &plan.receipt().table_id,
                        &plan.receipt().grid_sha256,
                        *apply_mode,
                        region,
                        value,
                        limits.properties,
                    )?;
                    if mutation.after.diagonal_sha256.as_deref() != Some(expected.as_str()) {
                        return Err(TablePropertiesHwpxError::PlanBindingMismatch);
                    }
                    output.insert(
                        mutation.master_cell_id.clone(),
                        TablePropertiesHwpxDiagonalBinding {
                            master_cell_id: mutation.master_cell_id.clone(),
                            apply_mode: *apply_mode,
                            region,
                            value: value.clone(),
                        },
                    );
                }
            }
        }
    }
    Ok(TablePropertiesHwpxBinding {
        table: source.table.clone(),
        diagonals: output.into_values().collect(),
    })
}

fn plan_region(
    plan: &TablePropertiesPlan,
    grid: &TableGrid,
) -> Result<Option<TablePropertyRegion>, TablePropertiesHwpxError> {
    let mut first_row = u32::MAX;
    let mut first_column = u32::MAX;
    let mut last_row = 0_u32;
    let mut last_column = 0_u32;
    for mutation in plan.mutations() {
        let span = grid
            .master_cells()
            .iter()
            .find(|span| span.master_cell_id == mutation.master_cell_id)
            .ok_or(TablePropertiesHwpxError::PlanBindingMismatch)?;
        first_row = first_row.min(span.row);
        first_column = first_column.min(span.column);
        last_row = last_row.max(
            span.row
                .checked_add(span.row_span)
                .ok_or(TablePropertiesHwpxError::PlanBindingMismatch)?,
        );
        last_column = last_column.max(
            span.column
                .checked_add(span.column_span)
                .ok_or(TablePropertiesHwpxError::PlanBindingMismatch)?,
        );
    }
    if first_row == u32::MAX {
        return Err(TablePropertiesHwpxError::PlanBindingMismatch);
    }
    Ok(Some(TablePropertyRegion::new(
        first_row,
        first_column,
        last_row
            .checked_sub(first_row)
            .ok_or(TablePropertiesHwpxError::PlanBindingMismatch)?,
        last_column
            .checked_sub(first_column)
            .ok_or(TablePropertiesHwpxError::PlanBindingMismatch)?,
    )?))
}

fn diagonal_binding_map(
    values: &[TablePropertiesHwpxDiagonalBinding],
) -> Result<BTreeMap<LogicalId, &TablePropertiesHwpxDiagonalBinding>, TablePropertiesHwpxError> {
    let mut output = BTreeMap::new();
    for value in values {
        if output.insert(value.master_cell_id.clone(), value).is_some() {
            return Err(TablePropertiesHwpxError::InvalidBinding);
        }
    }
    Ok(output)
}

fn validate_diagonal_binding_topology(
    values: &[TablePropertiesHwpxDiagonalBinding],
    table_id: &LogicalId,
    grid_sha256: &str,
    grid: &TableGrid,
    limits: TablePropertiesLimits,
) -> Result<(), TablePropertiesHwpxError> {
    if values.len() > limits.config().master_cells {
        return Err(TablePropertiesHwpxError::InvalidBinding);
    }
    let bindings = diagonal_binding_map(values)?;
    let mut unified_groups = BTreeMap::new();
    for value in values {
        let span = grid
            .master_cells()
            .iter()
            .find(|span| span.master_cell_id == value.master_cell_id)
            .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
        match (value.apply_mode, value.region) {
            (TableDiagonalApplyMode::EachCell, None) => {
                table_diagonal_identity_sha256(
                    table_id,
                    grid_sha256,
                    value.apply_mode,
                    None,
                    &value.value,
                    limits,
                )?;
            }
            (TableDiagonalApplyMode::Unified, Some(region)) => {
                if !span_is_contained(span, region, grid)? {
                    return Err(TablePropertiesHwpxError::DiagonalBindingMismatch);
                }
                let identity = table_diagonal_identity_sha256(
                    table_id,
                    grid_sha256,
                    value.apply_mode,
                    Some(region),
                    &value.value,
                    limits,
                )?;
                unified_groups.insert(identity, region);
            }
            _ => return Err(TablePropertiesHwpxError::DiagonalBindingMismatch),
        }
    }
    for (identity, region) in unified_groups {
        let mut contained = 0_usize;
        for span in grid.master_cells() {
            if !span_intersects(span, region)? {
                continue;
            }
            if !span_is_contained(span, region, grid)? {
                return Err(TablePropertiesHwpxError::DiagonalBindingMismatch);
            }
            contained = contained
                .checked_add(1)
                .ok_or(TablePropertiesHwpxError::AllocationFailed)?;
            let binding = bindings
                .get(&span.master_cell_id)
                .copied()
                .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
            let actual = table_diagonal_identity_sha256(
                table_id,
                grid_sha256,
                binding.apply_mode,
                binding.region,
                &binding.value,
                limits,
            )?;
            if actual != identity {
                return Err(TablePropertiesHwpxError::DiagonalBindingMismatch);
            }
        }
        if contained == 0 {
            return Err(TablePropertiesHwpxError::DiagonalBindingMismatch);
        }
    }
    Ok(())
}

fn span_is_contained(
    span: &domain_ir::TableCellSpan,
    region: TablePropertyRegion,
    grid: &TableGrid,
) -> Result<bool, TablePropertiesHwpxError> {
    let region_bottom = region
        .row()
        .checked_add(region.row_span())
        .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
    let region_right = region
        .column()
        .checked_add(region.column_span())
        .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
    let span_bottom = span
        .row
        .checked_add(span.row_span)
        .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
    let span_right = span
        .column
        .checked_add(span.column_span)
        .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
    Ok(region_bottom <= grid.rows()
        && region_right <= grid.columns()
        && span.row >= region.row()
        && span.column >= region.column()
        && span_bottom <= region_bottom
        && span_right <= region_right)
}

fn span_intersects(
    span: &domain_ir::TableCellSpan,
    region: TablePropertyRegion,
) -> Result<bool, TablePropertiesHwpxError> {
    let region_bottom = region
        .row()
        .checked_add(region.row_span())
        .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
    let region_right = region
        .column()
        .checked_add(region.column_span())
        .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
    let span_bottom = span
        .row
        .checked_add(span.row_span)
        .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
    let span_right = span
        .column
        .checked_add(span.column_span)
        .ok_or(TablePropertiesHwpxError::DiagonalBindingMismatch)?;
    Ok(span.row < region_bottom
        && span_bottom > region.row()
        && span.column < region_right
        && span_right > region.column())
}

fn native_diagonal_matches(border: &BorderFill, value: &TableDiagonalValue) -> bool {
    border.slash == native_slash(value.slash)
        && border.back_slash == native_slash(value.back_slash)
        && border.center_line == native_center(value.center_line)
        && line_digest(border.diagonal).as_deref() == Some(value.line_sha256.as_str())
}

fn native_slash(value: TableDiagonalSlash) -> Slash {
    Slash {
        slash_type: match value.slash_type {
            TableDiagonalSlashType::None => SlashType::None,
            TableDiagonalSlashType::Center => SlashType::Center,
            TableDiagonalSlashType::CenterBelow => SlashType::CenterBelow,
            TableDiagonalSlashType::CenterAbove => SlashType::CenterAbove,
            TableDiagonalSlashType::All => SlashType::All,
        },
        crooked: value.crooked,
        is_counter: value.is_counter,
    }
}

const fn native_center(value: TableDiagonalCenterLine) -> CenterLine {
    match value {
        TableDiagonalCenterLine::None => CenterLine::None,
        TableDiagonalCenterLine::Horizontal => CenterLine::Horizontal,
        TableDiagonalCenterLine::Vertical => CenterLine::Vertical,
        TableDiagonalCenterLine::Cross => CenterLine::Cross,
    }
}

const fn empty_slash() -> Slash {
    Slash {
        slash_type: SlashType::None,
        crooked: false,
        is_counter: false,
    }
}

fn resolve_line(
    digest: Option<&str>,
    fallback: BorderLine,
    lines: &BTreeMap<String, BorderLine>,
) -> Result<BorderLine, TablePropertiesHwpxError> {
    match digest {
        Some(value) => lines
            .get(value)
            .copied()
            .ok_or(TablePropertiesHwpxError::MissingCatalogValue),
        None => Ok(BorderLine {
            line_type: LineType2::None,
            width: fallback.width,
            color: fallback.color,
        }),
    }
}

fn border_map(
    values: &[BorderFill],
) -> Result<BTreeMap<u32, &BorderFill>, TablePropertiesHwpxError> {
    let mut output = BTreeMap::new();
    for value in values {
        if output.insert(value.id, value).is_some() {
            return Err(TablePropertiesHwpxError::AmbiguousCatalogValue);
        }
    }
    Ok(output)
}

fn border_fill_digest(value: &BorderFill) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-properties-hwpx-border-fill/v1\0");
    hash_bool(&mut digest, value.three_d);
    hash_bool(&mut digest, value.shadow);
    hash_part(&mut digest, center_line(value.center_line));
    hash_bool(&mut digest, value.break_cell_separate_line);
    hash_slash(&mut digest, value.slash);
    hash_slash(&mut digest, value.back_slash);
    for line in [
        value.left,
        value.right,
        value.top,
        value.bottom,
        value.diagonal,
    ] {
        hash_line(&mut digest, line);
    }
    match value.fill_brush.as_ref() {
        Some(fill) => hash_part(&mut digest, &background_digest(fill)),
        None => hash_part(&mut digest, "none"),
    }
    hex(digest.finalize())
}

fn hash_slash(digest: &mut Sha256, value: Slash) {
    hash_part(digest, slash_type(value.slash_type));
    hash_bool(digest, value.crooked);
    hash_bool(digest, value.is_counter);
}

fn aggregate_payload_digest(values: &[String]) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-properties-hwpx-payload/v1\0");
    hash_part(&mut digest, &values.len().to_string());
    for value in values {
        hash_part(&mut digest, value);
    }
    hex(digest.finalize())
}

fn required_bool(element: &XmlElementToken, name: &str) -> Result<bool, TablePropertiesHwpxError> {
    match attribute(element, name)? {
        "0" => Ok(false),
        "1" => Ok(true),
        _ => Err(TablePropertiesHwpxError::UnsupportedPropertyShape),
    }
}

fn require_paragraph_alignment(
    catalog: &crate::ParagraphStyleCatalog,
    identifier: u32,
    expected: HorizontalAlignment,
) -> Result<(), TablePropertiesHwpxError> {
    if resolve_paragraph_alignment(catalog, identifier)? != expected {
        return Err(TablePropertiesHwpxError::MissingCatalogValue);
    }
    Ok(())
}

fn resolve_paragraph_alignment(
    catalog: &crate::ParagraphStyleCatalog,
    identifier: u32,
) -> Result<HorizontalAlignment, TablePropertiesHwpxError> {
    let mut matches = catalog.styles.iter().filter(|style| style.id == identifier);
    let first = matches
        .next()
        .ok_or(TablePropertiesHwpxError::MissingCatalogValue)?;
    if matches.next().is_some() {
        return Err(TablePropertiesHwpxError::AmbiguousCatalogValue);
    }
    Ok(first.horizontal_alignment)
}

const fn horizontal_alignment(value: HorizontalAlignment) -> &'static str {
    match value {
        HorizontalAlignment::Justify => "justify",
        HorizontalAlignment::Left => "left",
        HorizontalAlignment::Right => "right",
        HorizontalAlignment::Center => "center",
        HorizontalAlignment::Distribute => "distribute",
        HorizontalAlignment::DistributeSpace => "distribute_space",
    }
}

const fn vertical_alignment(value: CellVerticalAlignment) -> &'static str {
    match value {
        CellVerticalAlignment::Top => "top",
        CellVerticalAlignment::Center => "center",
        CellVerticalAlignment::Bottom => "bottom",
    }
}

const fn native_vertical_alignment(value: CellVerticalAlignment) -> &'static str {
    match value {
        CellVerticalAlignment::Top => "TOP",
        CellVerticalAlignment::Center => "CENTER",
        CellVerticalAlignment::Bottom => "BOTTOM",
    }
}

const fn text_direction(value: CellTextDirection) -> &'static str {
    match value {
        CellTextDirection::Horizontal => "horizontal",
        CellTextDirection::Vertical => "vertical",
        CellTextDirection::VerticalAll => "vertical_all",
    }
}

const fn native_text_direction(value: CellTextDirection) -> &'static str {
    match value {
        CellTextDirection::Horizontal => "HORIZONTAL",
        CellTextDirection::Vertical => "VERTICAL",
        CellTextDirection::VerticalAll => "VERTICALALL",
    }
}

const fn protection(value: CellProtection) -> &'static str {
    match value {
        CellProtection::Open => "open",
        CellProtection::Editable => "editable",
        CellProtection::Protected => "protected",
        CellProtection::ProtectedEditable => "protected_editable",
    }
}

const fn protection_flags(value: CellProtection) -> (bool, bool) {
    match value {
        CellProtection::Open => (false, false),
        CellProtection::Editable => (false, true),
        CellProtection::Protected => (true, false),
        CellProtection::ProtectedEditable => (true, true),
    }
}

const fn bool01(value: bool) -> &'static str {
    if value { "1" } else { "0" }
}

fn require_digest(value: &str) -> Result<(), TablePropertiesHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TablePropertiesHwpxError::InvalidBinding);
    }
    Ok(())
}

fn parse_properties_digest(value: &str) -> Result<[u8; 32], TablePropertiesHwpxError> {
    require_digest(value)?;
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text =
            std::str::from_utf8(chunk).map_err(|_| TablePropertiesHwpxError::InvalidBinding)?;
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| TablePropertiesHwpxError::InvalidBinding)?;
    }
    Ok(output)
}
