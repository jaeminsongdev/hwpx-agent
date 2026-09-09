use std::collections::BTreeMap;

use domain_ir::{
    CellCoordinate, FormulaAstDraft, FormulaCellDraft, FormulaLimits, LogicalId,
    TABLE_FORMULA_SCHEMA_VERSION, TABLE_RULING_SCHEMA_VERSION, TableCellSpan, TableGrid,
    TableGridError, TableGridLimits, TableRulingAxis, TableRulingCellDraft,
    TableRulingCellProperties, TableRulingEdge, TableRulingError, TableRulingFrame,
    TableRulingLimits, TableRulingPayloadBlock, TableRulingPlan, TableRulingPlanKind,
    TableRulingState, TableRulingStateDraft,
};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{PreservingXmlDocument, PreservingXmlError, XmlElementToken};
use crate::{
    BorderFill, BorderLine, BorderWidth, CenterLine, Color, FillBrush, HANCOM_2020_HEAD_NAMESPACE,
    HatchStyle, LineType2, ParagraphStyleCatalogReader, ParagraphStyleError, ParagraphStyleLimits,
    Slash, SlashType, TableFormulaHwpxError, TableFormulaHwpxLimits, TableFormulaHwpxReader,
    TableLayoutHwpxError, TableLayoutHwpxLimits, TableLayoutHwpxReader,
};

mod aggregate_hwpx;
mod auto_fill_hwpx;
mod create_hwpx;
mod merge_split_hwpx;
mod partition_hwpx;
mod properties_hwpx;
mod sort_hwpx;
mod structure_hwpx;
mod style_hwpx;
mod table_to_text_hwpx;
mod text_conversion_hwpx;
mod transpose_hwpx;

pub use aggregate_hwpx::{
    TABLE_AGGREGATE_HWPX_PROFILE_ID, TABLE_AGGREGATE_HWPX_SCHEMA_VERSION,
    TableAggregateHwpxBuilder, TableAggregateHwpxError, TableAggregateHwpxLimits,
    TableAggregateHwpxLoweredParts, TableAggregateHwpxLowerer, TableAggregateHwpxLoweringReceipt,
    TableAggregateHwpxPlan, TableAggregateHwpxReadback, TableAggregateHwpxReader,
    TableAggregateHwpxRequest, TableAggregateHwpxRequestDraft,
};
pub use auto_fill_hwpx::{
    TABLE_AUTO_FILL_HWPX_PROFILE_ID, TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION, TableAutoFillHwpxBuilder,
    TableAutoFillHwpxError, TableAutoFillHwpxLimits, TableAutoFillHwpxLoweredParts,
    TableAutoFillHwpxLowerer, TableAutoFillHwpxLoweringReceipt, TableAutoFillHwpxPlan,
    TableAutoFillHwpxReadback, TableAutoFillHwpxReader, TableAutoFillHwpxRequest,
    TableAutoFillHwpxRequestDraft,
};
pub use create_hwpx::{
    TABLE_CREATE_HWPX_PROFILE_ID, TABLE_CREATE_HWPX_SCHEMA_VERSION, TableCreateHwpxBuilder,
    TableCreateHwpxError, TableCreateHwpxLimits, TableCreateHwpxLoweredParts,
    TableCreateHwpxLowerer, TableCreateHwpxLoweringReceipt, TableCreateHwpxPlan,
    TableCreateHwpxReadback, TableCreateHwpxReader, TableCreateHwpxRequest,
    TableCreateHwpxRequestDraft,
};
pub use merge_split_hwpx::{
    TABLE_MERGE_SPLIT_HWPX_PROFILE_ID, TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION,
    TableMergeSplitHwpxBuilder, TableMergeSplitHwpxError, TableMergeSplitHwpxLimits,
    TableMergeSplitHwpxLoweredParts, TableMergeSplitHwpxLowerer,
    TableMergeSplitHwpxLoweringReceipt, TableMergeSplitHwpxOperation,
    TableMergeSplitHwpxPartBinding, TableMergeSplitHwpxPlan, TableMergeSplitHwpxReadback,
    TableMergeSplitHwpxReader, TableMergeSplitHwpxRequest, TableMergeSplitHwpxRequestDraft,
};
pub use partition_hwpx::{
    TABLE_JOIN_HWPX_PROFILE_ID, TABLE_JOIN_HWPX_SCHEMA_VERSION, TABLE_SPLIT_HWPX_PROFILE_ID,
    TABLE_SPLIT_HWPX_SCHEMA_VERSION, TableJoinHwpxBuilder, TableJoinHwpxError, TableJoinHwpxLimits,
    TableJoinHwpxLoweredParts, TableJoinHwpxLowerer, TableJoinHwpxLoweringReceipt,
    TableJoinHwpxPlan, TableJoinHwpxReadback, TableJoinHwpxReader, TableJoinHwpxRequest,
    TableJoinHwpxRequestDraft, TableSplitHwpxBuilder, TableSplitHwpxError, TableSplitHwpxLimits,
    TableSplitHwpxLoweredParts, TableSplitHwpxLowerer, TableSplitHwpxLoweringReceipt,
    TableSplitHwpxPlan, TableSplitHwpxReadback, TableSplitHwpxReader, TableSplitHwpxRequest,
    TableSplitHwpxRequestDraft,
};
pub use properties_hwpx::{
    TABLE_PROPERTIES_HWPX_PROFILE_ID, TablePropertiesHwpxBinding, TablePropertiesHwpxCellValue,
    TablePropertiesHwpxDiagonalBinding, TablePropertiesHwpxError, TablePropertiesHwpxLimits,
    TablePropertiesHwpxLoweredParts, TablePropertiesHwpxLowerer,
    TablePropertiesHwpxLoweringReceipt, TablePropertiesHwpxPartBinding,
    TablePropertiesHwpxReadback, TablePropertiesHwpxReader, TablePropertiesHwpxTableValue,
    TablePropertiesHwpxValueCatalog,
};
pub use sort_hwpx::{
    TABLE_SORT_HWPX_PROFILE_ID, TABLE_SORT_HWPX_SCHEMA_VERSION, TableSortHwpxBuilder,
    TableSortHwpxError, TableSortHwpxLimits, TableSortHwpxLoweredParts, TableSortHwpxLowerer,
    TableSortHwpxLoweringReceipt, TableSortHwpxPlan, TableSortHwpxReadback, TableSortHwpxReader,
    TableSortHwpxRequest, TableSortHwpxRequestDraft,
};
pub use structure_hwpx::{
    TABLE_STRUCTURE_HWPX_PROFILE_ID, TABLE_STRUCTURE_HWPX_SCHEMA_VERSION,
    TableStructureHwpxBuilder, TableStructureHwpxError, TableStructureHwpxLimits,
    TableStructureHwpxLoweredParts, TableStructureHwpxLowerer, TableStructureHwpxLoweringReceipt,
    TableStructureHwpxPlan, TableStructureHwpxReadback, TableStructureHwpxReader,
    TableStructureHwpxRequest, TableStructureHwpxRequestDraft,
};
pub use style_hwpx::{
    TABLE_STYLE_HWPX_PROFILE_ID, TableStyleHwpxCellValue, TableStyleHwpxError,
    TableStyleHwpxLimits, TableStyleHwpxLoweredParts, TableStyleHwpxLowerer,
    TableStyleHwpxLoweringReceipt, TableStyleHwpxPartBinding, TableStyleHwpxReadback,
    TableStyleHwpxReader, TableStyleHwpxValueCatalog,
};
pub use table_to_text_hwpx::{
    TABLE_TABLE_TO_TEXT_HWPX_PROFILE_ID, TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION,
    TableTableToTextHwpxBuilder, TableTableToTextHwpxError, TableTableToTextHwpxLimits,
    TableTableToTextHwpxLoweredParts, TableTableToTextHwpxLowerer,
    TableTableToTextHwpxLoweringReceipt, TableTableToTextHwpxPlan, TableTableToTextHwpxReadback,
    TableTableToTextHwpxReader, TableTableToTextHwpxRequest, TableTableToTextHwpxRequestDraft,
};
pub use text_conversion_hwpx::{
    TABLE_TEXT_TO_TABLE_HWPX_PROFILE_ID, TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION,
    TableTextToTableHwpxBuilder, TableTextToTableHwpxError, TableTextToTableHwpxLimits,
    TableTextToTableHwpxLoweredParts, TableTextToTableHwpxLowerer,
    TableTextToTableHwpxLoweringReceipt, TableTextToTableHwpxPlan, TableTextToTableHwpxReadback,
    TableTextToTableHwpxReader, TableTextToTableHwpxRequest, TableTextToTableHwpxRequestDraft,
};
pub use transpose_hwpx::{
    TABLE_TRANSPOSE_HWPX_PROFILE_ID, TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION,
    TableTransposeHwpxBuilder, TableTransposeHwpxError, TableTransposeHwpxLimits,
    TableTransposeHwpxLoweredParts, TableTransposeHwpxLowerer, TableTransposeHwpxLoweringReceipt,
    TableTransposeHwpxPlan, TableTransposeHwpxReadback, TableTransposeHwpxReader,
    TableTransposeHwpxRequest, TableTransposeHwpxRequestDraft,
};

pub const TABLE_RULING_HWPX_PROFILE_ID: &str = "hwpx-agent.table-ruling-hwpx.hancom-2020/1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TableRulingHwpxLimits {
    pub layout: TableLayoutHwpxLimits,
    pub paragraph_style: ParagraphStyleLimits,
    pub formula_hwpx: TableFormulaHwpxLimits,
    pub formula: FormulaLimits,
    pub grid: TableGridLimits,
    pub ruling: TableRulingLimits,
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableRulingHwpxCellBinding {
    pub master_cell_id: LogicalId,
    pub payload_block_ids: Vec<LogicalId>,
}

impl std::fmt::Debug for TableRulingHwpxCellBinding {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableRulingHwpxCellBinding")
            .field("master_cell_id", &"<redacted>")
            .field("payload_block_count", &self.payload_block_ids.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableRulingHwpxBinding {
    pub table_id: LogicalId,
    pub row_boundaries_hwpunit: Vec<u32>,
    pub column_boundaries_hwpunit: Vec<u32>,
    pub cells: Vec<TableRulingHwpxCellBinding>,
}

impl std::fmt::Debug for TableRulingHwpxBinding {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableRulingHwpxBinding")
            .field("table_id", &"<redacted>")
            .field("row_boundary_count", &self.row_boundaries_hwpunit.len())
            .field(
                "column_boundary_count",
                &self.column_boundaries_hwpunit.len(),
            )
            .field("cell_count", &self.cells.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableRulingHwpxStyleCatalog {
    pub edge_line_sha256: Vec<String>,
    pub slash_diagonal_sha256: Vec<String>,
    pub back_slash_diagonal_sha256: Vec<String>,
}

impl std::fmt::Debug for TableRulingHwpxStyleCatalog {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableRulingHwpxStyleCatalog")
            .field("edge_line_count", &self.edge_line_sha256.len())
            .field("slash_diagonal_count", &self.slash_diagonal_sha256.len())
            .field(
                "back_slash_diagonal_count",
                &self.back_slash_diagonal_sha256.len(),
            )
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableRulingHwpxReadback {
    pub profile_id: &'static str,
    pub grid: TableGrid,
    pub state: TableRulingState,
    pub header_sha256: [u8; 32],
    pub section_sha256: [u8; 32],
    pub table_content_sha256: [u8; 32],
    pub style_catalog: TableRulingHwpxStyleCatalog,
    pub border_fill_count: usize,
    pub payload_block_count: usize,
    pub formula_count: usize,
}

impl std::fmt::Debug for TableRulingHwpxReadback {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableRulingHwpxReadback")
            .field("profile_id", &self.profile_id)
            .field("rows", &self.grid.rows())
            .field("columns", &self.grid.columns())
            .field("cell_count", &self.grid.master_cell_count())
            .field("border_fill_count", &self.border_fill_count)
            .field("style_catalog", &self.style_catalog)
            .field("payload_block_count", &self.payload_block_count)
            .field("formula_count", &self.formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableRulingHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub source_header_sha256: [u8; 32],
    pub output_header_sha256: [u8; 32],
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub template_section_sha256: Option<[u8; 32]>,
    pub source_state_sha256: Option<[u8; 32]>,
    pub target_state_sha256: [u8; 32],
    pub source_grid_sha256: Option<[u8; 32]>,
    pub target_grid_sha256: [u8; 32],
    pub document_flow_sha256: [u8; 32],
    pub insertion_context_sha256: Option<[u8; 32]>,
    pub added_border_fill_count: usize,
    pub target_cell_count: usize,
    pub payload_block_count: usize,
    pub formula_count: usize,
}

impl std::fmt::Debug for TableRulingHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableRulingHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("added_border_fill_count", &self.added_border_fill_count)
            .field("target_cell_count", &self.target_cell_count)
            .field("payload_block_count", &self.payload_block_count)
            .field("formula_count", &self.formula_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct TableRulingHwpxLoweredParts {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub receipt: TableRulingHwpxLoweringReceipt,
}

impl std::fmt::Debug for TableRulingHwpxLoweredParts {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("TableRulingHwpxLoweredParts")
            .field("header_bytes", &self.header.len())
            .field("section_bytes", &self.section.len())
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error)]
pub enum TableRulingHwpxError {
    #[error("table-ruling HWPX identity or physical-boundary binding is invalid")]
    InvalidBinding,
    #[error("table-ruling HWPX native cell shape is unsupported")]
    UnsupportedCellShape,
    #[error("table-ruling HWPX native formula shape is unsupported")]
    UnsupportedFormulaShape,
    #[error("table-ruling HWPX cell border references an absent border/fill")]
    DanglingBorderFill,
    #[error("table-ruling HWPX shared-edge border definitions disagree")]
    SharedEdgeMismatch,
    #[error("table-ruling HWPX physical cell extent differs from the bound lattice")]
    PhysicalExtentMismatch,
    #[error("table-ruling HWPX payload binding count differs from native payload blocks")]
    PayloadBindingMismatch,
    #[error("table-ruling HWPX allocation failed")]
    AllocationFailed,
    #[error("table-ruling HWPX numeric attribute is invalid")]
    InvalidNumber,
    #[error("table-ruling HWPX source state or grid differs from native readback")]
    SourceStateMismatch,
    #[error("table-ruling HWPX plan receipt or target state is inconsistent")]
    PlanBindingMismatch,
    #[error("table-ruling HWPX document-flow binding drifted")]
    FlowBindingMismatch,
    #[error("table-ruling HWPX outer-rectangle insertion context is invalid")]
    InvalidInsertionContext,
    #[error("table-ruling HWPX outer-rectangle template is not exact and empty")]
    InvalidOuterTemplate,
    #[error("table-ruling HWPX native table identifier collides with the destination section")]
    NativeTableIdCollision,
    #[error("table-ruling HWPX outer rectangle requires the separate creation path")]
    UnsupportedPlanKind,
    #[error("table-ruling HWPX target names a line identity absent from the header catalog")]
    MissingLineIdentity,
    #[error("table-ruling HWPX target cell side cannot be represented by one native line")]
    NonUniformCellSide,
    #[error("table-ruling HWPX structural formula mutation is outside the reviewed native profile")]
    UnsupportedFormulaMutation,
    #[error("table-ruling HWPX target cell properties have no preserving source template")]
    MissingCellTemplate,
    #[error("table-ruling HWPX border/fill identifier space or finite catalog is exhausted")]
    BorderFillLimit,
    #[error("table-ruling HWPX output exceeds its finite bound")]
    OutputLimit,
    #[error("table-ruling HWPX semantic readback differs from the target")]
    ReadbackMismatch,
    #[error("table-ruling HWPX strict table admission failed")]
    Layout(#[from] TableLayoutHwpxError),
    #[error("table-ruling HWPX strict border/fill catalog admission failed")]
    ParagraphStyle(#[from] ParagraphStyleError),
    #[error("table-ruling HWPX formula admission failed")]
    FormulaHwpx(#[from] TableFormulaHwpxError),
    #[error("table-ruling HWPX preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
    #[error("table-ruling HWPX logical grid admission failed")]
    Grid(#[from] TableGridError),
    #[error("table-ruling HWPX exact state admission failed")]
    Ruling(#[from] TableRulingError),
}

impl TableRulingHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidBinding => "table_ruling_hwpx_invalid_binding",
            Self::UnsupportedCellShape => "table_ruling_hwpx_unsupported_cell_shape",
            Self::UnsupportedFormulaShape => "table_ruling_hwpx_unsupported_formula_shape",
            Self::DanglingBorderFill => "table_ruling_hwpx_dangling_border_fill",
            Self::SharedEdgeMismatch => "table_ruling_hwpx_shared_edge_mismatch",
            Self::PhysicalExtentMismatch => "table_ruling_hwpx_physical_extent_mismatch",
            Self::PayloadBindingMismatch => "table_ruling_hwpx_payload_binding_mismatch",
            Self::AllocationFailed => "table_ruling_hwpx_allocation_failed",
            Self::InvalidNumber => "table_ruling_hwpx_invalid_number",
            Self::SourceStateMismatch => "table_ruling_hwpx_source_state_mismatch",
            Self::PlanBindingMismatch => "table_ruling_hwpx_plan_binding_mismatch",
            Self::FlowBindingMismatch => "table_ruling_hwpx_flow_binding_mismatch",
            Self::InvalidInsertionContext => "table_ruling_hwpx_invalid_insertion_context",
            Self::InvalidOuterTemplate => "table_ruling_hwpx_invalid_outer_template",
            Self::NativeTableIdCollision => "table_ruling_hwpx_native_table_id_collision",
            Self::UnsupportedPlanKind => "table_ruling_hwpx_unsupported_plan_kind",
            Self::MissingLineIdentity => "table_ruling_hwpx_missing_line_identity",
            Self::NonUniformCellSide => "table_ruling_hwpx_non_uniform_cell_side",
            Self::UnsupportedFormulaMutation => "table_ruling_hwpx_unsupported_formula_mutation",
            Self::MissingCellTemplate => "table_ruling_hwpx_missing_cell_template",
            Self::BorderFillLimit => "table_ruling_hwpx_border_fill_limit",
            Self::OutputLimit => "table_ruling_hwpx_output_limit",
            Self::ReadbackMismatch => "table_ruling_hwpx_readback_mismatch",
            Self::Layout(_) => "table_ruling_hwpx_table_admission",
            Self::ParagraphStyle(_) => "table_ruling_hwpx_border_fill_admission",
            Self::FormulaHwpx(_) => "table_ruling_hwpx_formula_admission",
            Self::Preserving(_) => "table_ruling_hwpx_preserving_xml",
            Self::Grid(_) => "table_ruling_hwpx_grid_admission",
            Self::Ruling(_) => "table_ruling_hwpx_state_admission",
        }
    }
}

#[derive(Debug)]
pub struct TableRulingHwpxReader;

impl TableRulingHwpxReader {
    /// Lifts one selected table into the exact ruling state using explicit logical identities and
    /// physical boundaries. HWPX does not retain every internal boundary of a merged cell, so the
    /// binding is verified against every native cell extent rather than guessed.
    ///
    /// # Errors
    ///
    /// Rejects malformed or incomplete HWPX, ambiguous formulas, dangling styles, inconsistent
    /// shared edges, invalid bindings, physical drift, and every domain-state invariant failure.
    pub fn read_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: TableRulingHwpxLimits,
    ) -> Result<TableRulingHwpxReadback, TableRulingHwpxError> {
        read_existing(
            header,
            section,
            table_ordinal,
            binding,
            &limits,
            false,
            false,
        )
    }

    pub(crate) fn read_existing_preserving_caption(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: &TableRulingHwpxLimits,
    ) -> Result<TableRulingHwpxReadback, TableRulingHwpxError> {
        read_existing(header, section, table_ordinal, binding, limits, true, false)
    }

    pub(crate) fn read_existing_aggregate_preserving_caption(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        limits: &TableRulingHwpxLimits,
    ) -> Result<TableRulingHwpxReadback, TableRulingHwpxError> {
        read_existing(header, section, table_ordinal, binding, limits, true, true)
    }
}

#[derive(Debug)]
pub struct TableRulingHwpxLowerer;

impl TableRulingHwpxLowerer {
    /// Returns the exact insertion-context identity for one empty top-level paragraph.
    ///
    /// The digest binds the complete source section, the selected paragraph ordinal, and the
    /// paragraph bytes. It is suitable for `DrawOuterRectangle.insertion_context_sha256` and is
    /// checked again immediately before lowering.
    ///
    /// # Errors
    ///
    /// Rejects malformed HWPX, a missing/non-top-level paragraph, or any non-empty placeholder.
    pub fn outer_insertion_context_sha256(
        section: &[u8],
        placeholder_paragraph_ordinal: usize,
    ) -> Result<String, TableRulingHwpxError> {
        let document = PreservingXmlDocument::parse(section)?;
        let paragraph =
            selected_empty_top_level_paragraph(section, &document, placeholder_paragraph_ordinal)?;
        insertion_context_digest(section, &document, paragraph, placeholder_paragraph_ordinal)
    }

    /// Lowers an outer-rectangle plan by replacing one exact empty top-level paragraph with a
    /// reviewed native 1x1 table template.
    ///
    /// The template must contain one empty, formula-free table with the requested physical frame,
    /// table properties, cell properties and logical boundaries. Its line definitions may be
    /// rewritten through the reviewed header catalog. The source insertion context, plan receipt,
    /// document flow, native table identifier uniqueness and final semantic readback are all
    /// checked before output is returned.
    ///
    /// # Errors
    ///
    /// Rejects source, template, plan, insertion, identity, catalog, finite-bound, or semantic
    /// readback drift without returning partial parts.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_outer_rectangle(
        header: &[u8],
        section: &[u8],
        placeholder_paragraph_ordinal: usize,
        template_section: &[u8],
        template_table_ordinal: usize,
        plan: &TableRulingPlan,
        current_document_flow_sha256: &str,
        limits: TableRulingHwpxLimits,
    ) -> Result<TableRulingHwpxLoweredParts, TableRulingHwpxError> {
        let document = PreservingXmlDocument::parse(section)?;
        let placeholder =
            selected_empty_top_level_paragraph(section, &document, placeholder_paragraph_ordinal)?;
        let insertion_context = insertion_context_digest(
            section,
            &document,
            placeholder,
            placeholder_paragraph_ordinal,
        )?;
        let target_grid = validate_outer_plan(
            plan,
            current_document_flow_sha256,
            &insertion_context,
            &limits,
        )?;
        let target_binding = binding_from_state(plan.after_state(), &target_grid)?;
        let template = TableRulingHwpxReader::read_existing(
            header,
            template_section,
            template_table_ordinal,
            &target_binding,
            limits,
        )?;
        validate_outer_template(&template, plan.after_state(), &target_grid)?;
        let rendered = render_existing(
            header,
            template_section,
            template_table_ordinal,
            &target_binding,
            &template.state,
            plan.after_state(),
            &target_grid,
            true,
            &limits,
        )?;
        let wrapper = insertion_wrapper(&rendered.section, template_table_ordinal)?;
        ensure_native_table_id_available(section, &rendered.section, template_table_ordinal)?;
        let placeholder_span = element(&document, placeholder)?
            .outer_span()
            .ok_or(TableRulingHwpxError::InvalidInsertionContext)?;
        let target_table_ordinal = tables_before_offset(&document, placeholder_span.start());
        let mut edits = vec![RawEdit {
            start: placeholder_span.start(),
            end: placeholder_span.end(),
            replacement: wrapper,
        }];
        let output_section = apply_edits(section, &mut edits, limits.layout.config().output_bytes)?;
        let readback = TableRulingHwpxReader::read_existing(
            &rendered.header,
            &output_section,
            target_table_ordinal,
            &target_binding,
            limits,
        )?;
        if readback.state != *plan.after_state() || readback.grid != target_grid {
            return Err(TableRulingHwpxError::ReadbackMismatch);
        }
        let receipt = TableRulingHwpxLoweringReceipt {
            profile_id: TABLE_RULING_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&rendered.header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&output_section).into(),
            template_section_sha256: Some(Sha256::digest(template_section).into()),
            source_state_sha256: None,
            target_state_sha256: plan.after_state().canonical_sha256(limits.ruling)?,
            source_grid_sha256: None,
            target_grid_sha256: target_grid.canonical_sha256()?,
            document_flow_sha256: parse_digest(current_document_flow_sha256)?,
            insertion_context_sha256: Some(parse_digest(&insertion_context)?),
            added_border_fill_count: rendered.added_border_fill_count,
            target_cell_count: target_grid.master_cell_count(),
            payload_block_count: readback.payload_block_count,
            formula_count: readback.formula_count,
        };
        Ok(TableRulingHwpxLoweredParts {
            header: rendered.header,
            section: output_section,
            receipt,
        })
    }

    /// Lowers one exact existing-table ruling plan into coordinated header and section parts.
    ///
    /// The source is lifted again immediately before mutation, the domain plan receipt is checked
    /// against both source and target states/grids plus current document flow, and the two output
    /// parts are reparsed into the target state before they are returned.
    ///
    /// # Errors
    ///
    /// Rejects source/plan/flow drift, unrepresentable native border combinations, unsupported
    /// structural formula mutation, finite limits, or post-lowering semantic mismatch.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_existing(
        header: &[u8],
        section: &[u8],
        table_ordinal: usize,
        binding: &TableRulingHwpxBinding,
        source_state: &TableRulingState,
        source_grid: &TableGrid,
        plan: &TableRulingPlan,
        current_document_flow_sha256: &str,
        limits: TableRulingHwpxLimits,
    ) -> Result<TableRulingHwpxLoweredParts, TableRulingHwpxError> {
        let source =
            TableRulingHwpxReader::read_existing(header, section, table_ordinal, binding, limits)?;
        if source.state != *source_state || source.grid != *source_grid {
            return Err(TableRulingHwpxError::SourceStateMismatch);
        }
        let target_grid = validate_plan(
            source_state,
            source_grid,
            plan,
            current_document_flow_sha256,
            &limits,
        )?;
        let rendered = render_existing(
            header,
            section,
            table_ordinal,
            binding,
            source_state,
            plan.after_state(),
            &target_grid,
            plan.receipt().topology_changed(),
            &limits,
        )?;
        let target_binding = binding_from_state(plan.after_state(), &target_grid)?;
        let readback = TableRulingHwpxReader::read_existing(
            &rendered.header,
            &rendered.section,
            table_ordinal,
            &target_binding,
            limits,
        )?;
        if readback.state != *plan.after_state() || readback.grid != target_grid {
            return Err(TableRulingHwpxError::ReadbackMismatch);
        }
        let receipt = TableRulingHwpxLoweringReceipt {
            profile_id: TABLE_RULING_HWPX_PROFILE_ID,
            source_header_sha256: Sha256::digest(header).into(),
            output_header_sha256: Sha256::digest(&rendered.header).into(),
            source_section_sha256: Sha256::digest(section).into(),
            output_section_sha256: Sha256::digest(&rendered.section).into(),
            template_section_sha256: None,
            source_state_sha256: Some(source_state.canonical_sha256(limits.ruling)?),
            target_state_sha256: plan.after_state().canonical_sha256(limits.ruling)?,
            source_grid_sha256: Some(source_grid.canonical_sha256()?),
            target_grid_sha256: target_grid.canonical_sha256()?,
            document_flow_sha256: parse_digest(current_document_flow_sha256)?,
            insertion_context_sha256: None,
            added_border_fill_count: rendered.added_border_fill_count,
            target_cell_count: target_grid.master_cell_count(),
            payload_block_count: readback.payload_block_count,
            formula_count: readback.formula_count,
        };
        Ok(TableRulingHwpxLoweredParts {
            header: rendered.header,
            section: rendered.section,
            receipt,
        })
    }
}

fn validate_plan(
    source_state: &TableRulingState,
    source_grid: &TableGrid,
    plan: &TableRulingPlan,
    current_document_flow_sha256: &str,
    limits: &TableRulingHwpxLimits,
) -> Result<TableGrid, TableRulingHwpxError> {
    if plan.plan_kind() == TableRulingPlanKind::OuterRectangle {
        return Err(TableRulingHwpxError::UnsupportedPlanKind);
    }
    if plan.receipt().document_flow_sha256() != current_document_flow_sha256 {
        return Err(TableRulingHwpxError::FlowBindingMismatch);
    }
    let source_state_sha256 = hex(source_state.canonical_sha256(limits.ruling)?);
    let source_grid_sha256 = hex(source_grid.canonical_sha256()?);
    if plan.receipt().before_state_sha256() != Some(source_state_sha256.as_str())
        || plan.receipt().before_grid_sha256() != Some(source_grid_sha256.as_str())
    {
        return Err(TableRulingHwpxError::PlanBindingMismatch);
    }
    let target_grid = TableGrid::new(
        plan.after_grid().rows(),
        plan.after_grid().columns(),
        plan.after_grid().master_cells().to_vec(),
        limits.grid,
    )?;
    let target_state_sha256 = hex(plan.after_state().canonical_sha256(limits.ruling)?);
    let target_grid_sha256 = hex(target_grid.canonical_sha256()?);
    if plan.receipt().after_state_sha256() != target_state_sha256
        || plan.receipt().after_grid_sha256() != target_grid_sha256
        || plan.after_grid().grid_sha256() != target_grid_sha256
        || plan.after_state().grid_sha256() != target_grid_sha256
        || plan.after_state().table_id() != source_state.table_id()
    {
        return Err(TableRulingHwpxError::PlanBindingMismatch);
    }
    let reopened = TableRulingState::from_json(
        &plan.after_state().canonical_json(limits.ruling)?,
        &target_grid,
        limits.formula,
        limits.ruling,
    )?;
    if reopened != *plan.after_state() {
        return Err(TableRulingHwpxError::PlanBindingMismatch);
    }
    Ok(target_grid)
}

fn validate_outer_plan(
    plan: &TableRulingPlan,
    current_document_flow_sha256: &str,
    insertion_context_sha256: &str,
    limits: &TableRulingHwpxLimits,
) -> Result<TableGrid, TableRulingHwpxError> {
    if plan.plan_kind() != TableRulingPlanKind::OuterRectangle {
        return Err(TableRulingHwpxError::UnsupportedPlanKind);
    }
    if plan.receipt().document_flow_sha256() != current_document_flow_sha256 {
        return Err(TableRulingHwpxError::FlowBindingMismatch);
    }
    if plan.receipt().before_state_sha256().is_some()
        || plan.receipt().before_grid_sha256().is_some()
        || plan.receipt().insertion_context_sha256() != Some(insertion_context_sha256)
        || !plan.receipt().topology_changed()
        || plan.receipt().created_master_cell_count() != 1
        || plan.receipt().retired_master_cell_count() != 0
    {
        return Err(TableRulingHwpxError::PlanBindingMismatch);
    }
    let target_grid = TableGrid::new(
        plan.after_grid().rows(),
        plan.after_grid().columns(),
        plan.after_grid().master_cells().to_vec(),
        limits.grid,
    )?;
    let target_state_sha256 = hex(plan.after_state().canonical_sha256(limits.ruling)?);
    let target_grid_sha256 = hex(target_grid.canonical_sha256()?);
    if plan.receipt().after_state_sha256() != target_state_sha256
        || plan.receipt().after_grid_sha256() != target_grid_sha256
        || plan.after_grid().grid_sha256() != target_grid_sha256
        || plan.after_state().grid_sha256() != target_grid_sha256
    {
        return Err(TableRulingHwpxError::PlanBindingMismatch);
    }
    let reopened = TableRulingState::from_json(
        &plan.after_state().canonical_json(limits.ruling)?,
        &target_grid,
        limits.formula,
        limits.ruling,
    )?;
    if reopened != *plan.after_state()
        || target_grid.rows() != 1
        || target_grid.columns() != 1
        || target_grid.master_cell_count() != 1
    {
        return Err(TableRulingHwpxError::PlanBindingMismatch);
    }
    Ok(target_grid)
}

fn validate_outer_template(
    template: &TableRulingHwpxReadback,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
) -> Result<(), TableRulingHwpxError> {
    let template_cell = template
        .state
        .cells()
        .first()
        .ok_or(TableRulingHwpxError::InvalidOuterTemplate)?;
    let target_cell = target_state
        .cells()
        .first()
        .ok_or(TableRulingHwpxError::InvalidOuterTemplate)?;
    if template.grid.rows() != 1
        || template.grid.columns() != 1
        || template.grid.master_cell_count() != 1
        || template.grid != *target_grid
        || template.state.frame() != target_state.frame()
        || template.state.table_properties_sha256() != target_state.table_properties_sha256()
        || template_cell.properties() != target_cell.properties()
        || !template_cell.payload().is_empty()
        || template_cell.formula().is_some()
        || template.payload_block_count != 0
        || template.formula_count != 0
    {
        return Err(TableRulingHwpxError::InvalidOuterTemplate);
    }
    Ok(())
}

pub(super) fn binding_from_state(
    state: &TableRulingState,
    grid: &TableGrid,
) -> Result<TableRulingHwpxBinding, TableRulingHwpxError> {
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(grid.master_cell_count())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    for span in grid.master_cells() {
        let cell = state
            .cell(&span.master_cell_id)
            .ok_or(TableRulingHwpxError::PlanBindingMismatch)?;
        if cell.coordinate().row != span.row || cell.coordinate().column != span.column {
            return Err(TableRulingHwpxError::PlanBindingMismatch);
        }
        let mut payload_block_ids = Vec::new();
        payload_block_ids
            .try_reserve_exact(cell.payload().len())
            .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
        for block in cell.payload() {
            payload_block_ids.push(block.block_id.clone());
        }
        cells.push(TableRulingHwpxCellBinding {
            master_cell_id: span.master_cell_id.clone(),
            payload_block_ids,
        });
    }
    Ok(TableRulingHwpxBinding {
        table_id: state.table_id().clone(),
        row_boundaries_hwpunit: state.row_boundaries_hwpunit().to_vec(),
        column_boundaries_hwpunit: state.column_boundaries_hwpunit().to_vec(),
        cells,
    })
}

fn parse_digest(value: &str) -> Result<[u8; 32], TableRulingHwpxError> {
    if value.len() != 64
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return Err(TableRulingHwpxError::FlowBindingMismatch);
    }
    let mut output = [0_u8; 32];
    for (index, chunk) in value.as_bytes().chunks_exact(2).enumerate() {
        let text =
            std::str::from_utf8(chunk).map_err(|_| TableRulingHwpxError::FlowBindingMismatch)?;
        output[index] =
            u8::from_str_radix(text, 16).map_err(|_| TableRulingHwpxError::FlowBindingMismatch)?;
    }
    Ok(output)
}

#[derive(Debug)]
struct NativeCell {
    coordinate: CellCoordinate,
    row_span: u32,
    column_span: u32,
    border: BorderFill,
    payload_sha256: Vec<String>,
    properties: TableRulingCellProperties,
}

#[derive(Debug)]
struct SourceRenderCell {
    master_cell_id: LogicalId,
    element: usize,
    sub_list: usize,
    border: BorderFill,
    properties: TableRulingCellProperties,
    content: Vec<u8>,
}

#[derive(Debug)]
struct SourcePayload {
    bytes: Vec<u8>,
}

#[derive(Clone, Copy, Debug)]
struct DiagonalStyle {
    slash: Slash,
    line: BorderLine,
}

#[derive(Debug)]
struct StyleResolver {
    borders: Vec<BorderFill>,
    edge_lines: BTreeMap<String, BorderLine>,
    slash_diagonals: BTreeMap<String, DiagonalStyle>,
    back_slash_diagonals: BTreeMap<String, DiagonalStyle>,
    original_count: usize,
}

#[derive(Debug)]
pub(super) struct RenderedParts {
    pub(super) header: Vec<u8>,
    pub(super) section: Vec<u8>,
    pub(super) added_border_fill_count: usize,
}

#[derive(Debug)]
struct RawEdit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}

#[derive(Clone, Copy, Debug)]
enum ExistingRenderProfile {
    Existing { topology_changed: bool },
    Split,
    Partition,
    Structure,
    Transpose,
    Create,
}

impl ExistingRenderProfile {
    const fn topology_changed(self) -> bool {
        match self {
            Self::Existing { topology_changed } => topology_changed,
            Self::Split | Self::Partition | Self::Structure | Self::Transpose | Self::Create => {
                true
            }
        }
    }

    const fn permits_split_geometry(self) -> bool {
        matches!(self, Self::Split | Self::Partition | Self::Structure)
    }

    const fn permits_partition_geometry(self) -> bool {
        matches!(self, Self::Partition | Self::Structure)
    }

    const fn reuses_formula_content(self) -> bool {
        matches!(self, Self::Structure)
    }

    const fn preserves_caption(self) -> bool {
        matches!(self, Self::Structure | Self::Transpose)
    }

    const fn permits_transposed_geometry(self) -> bool {
        matches!(self, Self::Transpose)
    }

    const fn permits_created_geometry(self) -> bool {
        matches!(self, Self::Create)
    }
}

#[allow(clippy::too_many_arguments)]
pub(super) fn render_existing(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    source_state: &TableRulingState,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    topology_changed: bool,
    limits: &TableRulingHwpxLimits,
) -> Result<RenderedParts, TableRulingHwpxError> {
    render_existing_profile(
        header,
        section,
        table_ordinal,
        binding,
        source_state,
        target_state,
        target_grid,
        ExistingRenderProfile::Existing { topology_changed },
        limits,
    )
}

#[allow(clippy::too_many_arguments)]
pub(super) fn render_split_existing(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    source_state: &TableRulingState,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    limits: &TableRulingHwpxLimits,
) -> Result<RenderedParts, TableRulingHwpxError> {
    render_existing_profile(
        header,
        section,
        table_ordinal,
        binding,
        source_state,
        target_state,
        target_grid,
        ExistingRenderProfile::Split,
        limits,
    )
}

#[allow(clippy::too_many_arguments)]
pub(super) fn render_partition_existing(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    source_state: &TableRulingState,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    limits: &TableRulingHwpxLimits,
) -> Result<RenderedParts, TableRulingHwpxError> {
    render_existing_profile(
        header,
        section,
        table_ordinal,
        binding,
        source_state,
        target_state,
        target_grid,
        ExistingRenderProfile::Partition,
        limits,
    )
}

#[allow(clippy::too_many_arguments)]
pub(super) fn render_structure_existing(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    source_state: &TableRulingState,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    limits: &TableRulingHwpxLimits,
) -> Result<RenderedParts, TableRulingHwpxError> {
    render_existing_profile(
        header,
        section,
        table_ordinal,
        binding,
        source_state,
        target_state,
        target_grid,
        ExistingRenderProfile::Structure,
        limits,
    )
}

#[allow(clippy::too_many_arguments)]
pub(super) fn render_transpose_existing(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    source_state: &TableRulingState,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    limits: &TableRulingHwpxLimits,
) -> Result<RenderedParts, TableRulingHwpxError> {
    render_existing_profile(
        header,
        section,
        table_ordinal,
        binding,
        source_state,
        target_state,
        target_grid,
        ExistingRenderProfile::Transpose,
        limits,
    )
}

#[allow(clippy::too_many_arguments)]
pub(super) fn render_create_from_template(
    header: &[u8],
    template_section: &[u8],
    template_table_ordinal: usize,
    template_binding: &TableRulingHwpxBinding,
    template_state: &TableRulingState,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    limits: &TableRulingHwpxLimits,
) -> Result<RenderedParts, TableRulingHwpxError> {
    render_existing_profile(
        header,
        template_section,
        template_table_ordinal,
        template_binding,
        template_state,
        target_state,
        target_grid,
        ExistingRenderProfile::Create,
        limits,
    )
}

#[allow(clippy::too_many_arguments)]
fn render_existing_profile(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    source_state: &TableRulingState,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    profile: ExistingRenderProfile,
    limits: &TableRulingHwpxLimits,
) -> Result<RenderedParts, TableRulingHwpxError> {
    let source_frame = source_state.frame();
    let target_frame = target_state.frame();
    let frame_matches = source_frame == target_frame
        || profile.permits_partition_geometry()
            && source_frame.left_hwpunit == target_frame.left_hwpunit
            && source_frame.top_hwpunit == target_frame.top_hwpunit
        || profile.permits_split_geometry()
            && source_frame.left_hwpunit == target_frame.left_hwpunit
            && source_frame.top_hwpunit == target_frame.top_hwpunit
            && source_frame.width_hwpunit == target_frame.width_hwpunit
        || profile.permits_transposed_geometry()
            && source_frame.left_hwpunit == target_frame.left_hwpunit
            && source_frame.top_hwpunit == target_frame.top_hwpunit
            && source_frame.width_hwpunit == target_frame.height_hwpunit
            && source_frame.height_hwpunit == target_frame.width_hwpunit
        || profile.permits_created_geometry()
            && source_frame.left_hwpunit == target_frame.left_hwpunit
            && source_frame.top_hwpunit == target_frame.top_hwpunit;
    if !frame_matches
        || source_state.table_properties_sha256() != target_state.table_properties_sha256()
    {
        return Err(TableRulingHwpxError::PlanBindingMismatch);
    }
    if profile.topology_changed()
        && !profile.reuses_formula_content()
        && !topology_formulas_are_exactly_preserved(source_state, target_state)
    {
        return Err(TableRulingHwpxError::UnsupportedFormulaMutation);
    }
    let catalog = ParagraphStyleCatalogReader::read(header, limits.paragraph_style)?;
    let mut resolver = StyleResolver::new(catalog.border_fills)?;
    let document = PreservingXmlDocument::parse(section)?;
    let root = selected_table(&document, table_ordinal)?;
    let layout = if profile.preserves_caption() {
        TableLayoutHwpxReader::read_in_section_preserving_caption(
            section,
            table_ordinal,
            limits.layout,
        )?
    } else {
        TableLayoutHwpxReader::read_in_section(section, table_ordinal, limits.layout)?
    };
    let cells = selected_cells(&document, root, layout.cells.len())?;
    let (source_cells, payloads) =
        source_render_cells(section, &document, &cells, binding, source_state, &resolver)?;
    let rows = render_rows(
        section,
        &document,
        &source_cells,
        &payloads,
        source_state,
        target_state,
        target_grid,
        profile.topology_changed(),
        profile.reuses_formula_content(),
        &mut resolver,
        limits.layout.config().output_bytes,
    )?;
    let section = patch_table(
        section,
        &document,
        root,
        target_state,
        target_grid,
        rows,
        limits.layout.config().output_bytes,
    )?;
    let new_borders = resolver
        .borders
        .get(resolver.original_count..)
        .ok_or(TableRulingHwpxError::BorderFillLimit)?;
    let header = patch_header(
        header,
        new_borders,
        resolver.borders.len(),
        limits.paragraph_style.config().input_bytes,
    )?;
    let _ = ParagraphStyleCatalogReader::read(&header, limits.paragraph_style)?;
    Ok(RenderedParts {
        header,
        section,
        added_border_fill_count: new_borders.len(),
    })
}

fn topology_formulas_are_exactly_preserved(
    source: &TableRulingState,
    target: &TableRulingState,
) -> bool {
    source.cells().iter().all(|source_cell| {
        source_cell.formula().is_none()
            || target
                .cell(source_cell.master_cell_id())
                .is_some_and(|target_cell| target_cell.formula() == source_cell.formula())
    }) && target.cells().iter().all(|target_cell| {
        target_cell.formula().is_none()
            || source
                .cell(target_cell.master_cell_id())
                .is_some_and(|source_cell| source_cell.formula() == target_cell.formula())
    })
}

impl StyleResolver {
    fn new(borders: Vec<BorderFill>) -> Result<Self, TableRulingHwpxError> {
        let mut edge_lines = BTreeMap::new();
        let mut slash_diagonals = BTreeMap::new();
        let mut back_slash_diagonals = BTreeMap::new();
        for border in &borders {
            for line in [border.left, border.right, border.top, border.bottom] {
                if let Some(digest) = line_digest(line) {
                    insert_exact(&mut edge_lines, &digest, line)?;
                }
            }
            if let Some(digest) = diagonal_digest("slash", border.slash, border.diagonal) {
                insert_diagonal(
                    &mut slash_diagonals,
                    digest,
                    DiagonalStyle {
                        slash: border.slash,
                        line: border.diagonal,
                    },
                )?;
            }
            if let Some(digest) = diagonal_digest("back_slash", border.back_slash, border.diagonal)
            {
                insert_diagonal(
                    &mut back_slash_diagonals,
                    digest,
                    DiagonalStyle {
                        slash: border.back_slash,
                        line: border.diagonal,
                    },
                )?;
            }
        }
        let original_count = borders.len();
        Ok(Self {
            borders,
            edge_lines,
            slash_diagonals,
            back_slash_diagonals,
            original_count,
        })
    }

    fn border(&self, id: u32) -> Result<BorderFill, TableRulingHwpxError> {
        self.borders
            .iter()
            .find(|border| border.id == id)
            .cloned()
            .ok_or(TableRulingHwpxError::DanglingBorderFill)
    }

    fn intern(&mut self, mut target: BorderFill) -> Result<u32, TableRulingHwpxError> {
        if let Some(existing) = self
            .borders
            .iter()
            .find(|candidate| same_border_semantics(candidate, &target))
        {
            return Ok(existing.id);
        }
        let id = match self.borders.last() {
            Some(border) => border
                .id
                .checked_add(1)
                .ok_or(TableRulingHwpxError::BorderFillLimit)?,
            None => 1,
        };
        if id > u32::from(u16::MAX) {
            return Err(TableRulingHwpxError::BorderFillLimit);
        }
        target.id = id;
        self.borders
            .try_reserve(1)
            .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
        self.borders.push(target);
        Ok(id)
    }
}

fn insert_exact(
    values: &mut BTreeMap<String, BorderLine>,
    digest: &str,
    value: BorderLine,
) -> Result<(), TableRulingHwpxError> {
    if values
        .insert(digest.to_owned(), value)
        .is_some_and(|previous| previous != value)
    {
        return Err(TableRulingHwpxError::MissingLineIdentity);
    }
    Ok(())
}

fn insert_diagonal(
    values: &mut BTreeMap<String, DiagonalStyle>,
    digest: String,
    value: DiagonalStyle,
) -> Result<(), TableRulingHwpxError> {
    if values
        .get(&digest)
        .is_some_and(|previous| previous.slash != value.slash || previous.line != value.line)
    {
        return Err(TableRulingHwpxError::MissingLineIdentity);
    }
    values.insert(digest, value);
    Ok(())
}

fn same_border_semantics(left: &BorderFill, right: &BorderFill) -> bool {
    left.three_d == right.three_d
        && left.shadow == right.shadow
        && left.center_line == right.center_line
        && left.break_cell_separate_line == right.break_cell_separate_line
        && left.slash == right.slash
        && left.back_slash == right.back_slash
        && left.left == right.left
        && left.right == right.right
        && left.top == right.top
        && left.bottom == right.bottom
        && left.diagonal == right.diagonal
        && left.fill_brush == right.fill_brush
}

fn source_render_cells(
    section: &[u8],
    document: &PreservingXmlDocument,
    cells: &[(usize, CellCoordinate)],
    binding: &TableRulingHwpxBinding,
    source_state: &TableRulingState,
    resolver: &StyleResolver,
) -> Result<(Vec<SourceRenderCell>, BTreeMap<LogicalId, SourcePayload>), TableRulingHwpxError> {
    if cells.len() != binding.cells.len() {
        return Err(TableRulingHwpxError::InvalidBinding);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(cells.len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    let mut payloads = BTreeMap::new();
    for ((cell_index, coordinate), identity) in cells.iter().zip(&binding.cells) {
        let state_cell = source_state
            .cell(&identity.master_cell_id)
            .ok_or(TableRulingHwpxError::SourceStateMismatch)?;
        if state_cell.coordinate() != *coordinate {
            return Err(TableRulingHwpxError::SourceStateMismatch);
        }
        let sub_list = unique_child(document, *cell_index, "subList")?;
        let content_span = element(document, sub_list)?
            .content_span()
            .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
        let content = section
            .get(content_span.start()..content_span.end())
            .ok_or(TableRulingHwpxError::UnsupportedCellShape)?
            .to_vec();
        let paragraphs = payload_paragraphs(section, document, sub_list)?;
        if paragraphs.len() != identity.payload_block_ids.len()
            || paragraphs.len() != state_cell.payload().len()
        {
            return Err(TableRulingHwpxError::PayloadBindingMismatch);
        }
        for ((block_id, (digest, bytes)), state_block) in identity
            .payload_block_ids
            .iter()
            .zip(paragraphs)
            .zip(state_cell.payload())
        {
            if state_block.block_id != *block_id || state_block.payload_sha256 != digest {
                return Err(TableRulingHwpxError::SourceStateMismatch);
            }
            if payloads
                .insert(block_id.clone(), SourcePayload { bytes })
                .is_some()
            {
                return Err(TableRulingHwpxError::InvalidBinding);
            }
        }
        let border_id = required_u32(element(document, *cell_index)?, "borderFillIDRef")?;
        output.push(SourceRenderCell {
            master_cell_id: identity.master_cell_id.clone(),
            element: *cell_index,
            sub_list,
            border: resolver.border(border_id)?,
            properties: state_cell.properties().clone(),
            content,
        });
    }
    Ok((output, payloads))
}

fn payload_paragraphs(
    source: &[u8],
    document: &PreservingXmlDocument,
    sub_list: usize,
) -> Result<Vec<(String, Vec<u8>)>, TableRulingHwpxError> {
    let mut output = Vec::new();
    let mut child = element(document, sub_list)?.first_child();
    while let Some(index) = child {
        let value = element(document, index)?;
        if !has_name(value, "p") {
            return Err(TableRulingHwpxError::UnsupportedCellShape);
        }
        if !has_formula_descendant(document, index)? && !is_empty_scaffold(source, document, index)?
        {
            let bytes = element_bytes(source, value)?.to_vec();
            output
                .try_reserve(1)
                .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
            output.push((hex(Sha256::digest(&bytes)), bytes));
        }
        child = value.next_sibling();
    }
    Ok(output)
}

#[allow(clippy::too_many_arguments)]
fn render_rows(
    section: &[u8],
    document: &PreservingXmlDocument,
    source_cells: &[SourceRenderCell],
    payloads: &BTreeMap<LogicalId, SourcePayload>,
    source_state: &TableRulingState,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    topology_changed: bool,
    reuse_formula_content: bool,
    resolver: &mut StyleResolver,
    output_limit: usize,
) -> Result<Vec<u8>, TableRulingHwpxError> {
    let mut output = Vec::new();
    for row in 0..target_grid.rows() {
        extend_bounded(&mut output, b"<hp:tr>", output_limit)?;
        for span in target_grid
            .master_cells()
            .iter()
            .filter(|span| span.row == row)
        {
            let target_cell = target_state
                .cell(&span.master_cell_id)
                .ok_or(TableRulingHwpxError::PlanBindingMismatch)?;
            let template = source_template(source_cells, target_cell)?;
            let source_cell = source_state.cell(&span.master_cell_id);
            let content = target_content(
                template,
                source_cell,
                target_cell,
                payloads,
                topology_changed,
                reuse_formula_content,
                output_limit,
            )?;
            let desired_border = desired_border(
                template,
                target_cell.properties(),
                target_state,
                span,
                resolver,
            )?;
            let border_id = resolver.intern(desired_border)?;
            let bytes = render_cell(
                section,
                document,
                template,
                span,
                target_state,
                border_id,
                content,
                output_limit,
            )?;
            extend_bounded(&mut output, &bytes, output_limit)?;
        }
        extend_bounded(&mut output, b"</hp:tr>", output_limit)?;
    }
    Ok(output)
}

fn source_template<'a>(
    source_cells: &'a [SourceRenderCell],
    target: &domain_ir::TableRulingCell,
) -> Result<&'a SourceRenderCell, TableRulingHwpxError> {
    source_cells
        .iter()
        .find(|cell| cell.master_cell_id == *target.master_cell_id())
        .or_else(|| {
            source_cells.iter().find(|cell| {
                same_property_core(&cell.properties, target.properties())
                    && cell.properties.slash_diagonal_sha256
                        == target.properties().slash_diagonal_sha256
                    && cell.properties.back_slash_diagonal_sha256
                        == target.properties().back_slash_diagonal_sha256
            })
        })
        .ok_or(TableRulingHwpxError::MissingCellTemplate)
}

fn same_property_core(left: &TableRulingCellProperties, right: &TableRulingCellProperties) -> bool {
    left.non_ruling_properties_sha256 == right.non_ruling_properties_sha256
        && left.background_sha256 == right.background_sha256
}

fn target_content(
    template: &SourceRenderCell,
    source_cell: Option<&domain_ir::TableRulingCell>,
    target_cell: &domain_ir::TableRulingCell,
    payloads: &BTreeMap<LogicalId, SourcePayload>,
    topology_changed: bool,
    reuse_formula_content: bool,
    output_limit: usize,
) -> Result<Vec<u8>, TableRulingHwpxError> {
    if source_cell.is_some_and(|source_cell| {
        source_cell.payload() == target_cell.payload()
            && source_cell.formula() == target_cell.formula()
            && template.master_cell_id == *target_cell.master_cell_id()
    }) {
        return Ok(template.content.clone());
    }
    if reuse_formula_content
        && source_cell.is_some_and(|source_cell| {
            source_cell.payload() == target_cell.payload()
                && source_cell.formula().is_some()
                && target_cell.formula().is_some()
                && template.master_cell_id == *target_cell.master_cell_id()
        })
    {
        return Ok(template.content.clone());
    }
    if !topology_changed {
        return Err(TableRulingHwpxError::PlanBindingMismatch);
    }
    if target_cell.formula().is_some() {
        return Err(TableRulingHwpxError::UnsupportedFormulaMutation);
    }
    let mut output = Vec::new();
    for block in target_cell.payload() {
        let source = payloads
            .get(&block.block_id)
            .ok_or(TableRulingHwpxError::SourceStateMismatch)?;
        if hex(Sha256::digest(&source.bytes)) != block.payload_sha256 {
            return Err(TableRulingHwpxError::SourceStateMismatch);
        }
        extend_bounded(&mut output, &source.bytes, output_limit)?;
    }
    if output.is_empty() {
        extend_bounded(&mut output, empty_cell_paragraph(), output_limit)?;
    }
    Ok(output)
}

fn desired_border(
    template: &SourceRenderCell,
    properties: &TableRulingCellProperties,
    state: &TableRulingState,
    span: &TableCellSpan,
    resolver: &StyleResolver,
) -> Result<BorderFill, TableRulingHwpxError> {
    if !same_property_core(&template.properties, properties) {
        return Err(TableRulingHwpxError::MissingCellTemplate);
    }
    let mut border = template.border.clone();
    border.left = resolve_edge_line(
        uniform_side(
            state,
            TableRulingAxis::Vertical,
            span.column,
            span.row,
            span.row_span,
        )?,
        border.left,
        resolver,
    )?;
    border.right = resolve_edge_line(
        uniform_side(
            state,
            TableRulingAxis::Vertical,
            span.column
                .checked_add(span.column_span)
                .ok_or(TableRulingHwpxError::PlanBindingMismatch)?,
            span.row,
            span.row_span,
        )?,
        border.right,
        resolver,
    )?;
    border.top = resolve_edge_line(
        uniform_side(
            state,
            TableRulingAxis::Horizontal,
            span.row,
            span.column,
            span.column_span,
        )?,
        border.top,
        resolver,
    )?;
    border.bottom = resolve_edge_line(
        uniform_side(
            state,
            TableRulingAxis::Horizontal,
            span.row
                .checked_add(span.row_span)
                .ok_or(TableRulingHwpxError::PlanBindingMismatch)?,
            span.column,
            span.column_span,
        )?,
        border.bottom,
        resolver,
    )?;
    apply_diagonals(&mut border, properties, resolver)?;
    Ok(border)
}

fn uniform_side(
    state: &TableRulingState,
    axis: TableRulingAxis,
    boundary: u32,
    offset: u32,
    span: u32,
) -> Result<Option<&str>, TableRulingHwpxError> {
    let end = offset
        .checked_add(span)
        .ok_or(TableRulingHwpxError::PlanBindingMismatch)?;
    let mut selected = None;
    for current in offset..end {
        let value = state
            .edge(axis, boundary, current)
            .ok_or(TableRulingHwpxError::PlanBindingMismatch)?
            .line_sha256
            .as_deref();
        match selected {
            None => selected = Some(value),
            Some(previous) if previous == value => {}
            Some(_) => return Err(TableRulingHwpxError::NonUniformCellSide),
        }
    }
    selected.ok_or(TableRulingHwpxError::PlanBindingMismatch)
}

fn resolve_edge_line(
    digest: Option<&str>,
    fallback: BorderLine,
    resolver: &StyleResolver,
) -> Result<BorderLine, TableRulingHwpxError> {
    match digest {
        Some(value) => resolver
            .edge_lines
            .get(value)
            .copied()
            .ok_or(TableRulingHwpxError::MissingLineIdentity),
        None => Ok(BorderLine {
            line_type: LineType2::None,
            width: fallback.width,
            color: fallback.color,
        }),
    }
}

fn apply_diagonals(
    border: &mut BorderFill,
    properties: &TableRulingCellProperties,
    resolver: &StyleResolver,
) -> Result<(), TableRulingHwpxError> {
    let slash = properties
        .slash_diagonal_sha256
        .as_deref()
        .map(|digest| {
            resolver
                .slash_diagonals
                .get(digest)
                .copied()
                .ok_or(TableRulingHwpxError::MissingLineIdentity)
        })
        .transpose()?;
    let back_slash = properties
        .back_slash_diagonal_sha256
        .as_deref()
        .map(|digest| {
            resolver
                .back_slash_diagonals
                .get(digest)
                .copied()
                .ok_or(TableRulingHwpxError::MissingLineIdentity)
        })
        .transpose()?;
    if slash
        .zip(back_slash)
        .is_some_and(|(left, right)| left.line != right.line)
    {
        return Err(TableRulingHwpxError::NonUniformCellSide);
    }
    border.slash = slash.map_or(
        Slash {
            slash_type: SlashType::None,
            crooked: false,
            is_counter: false,
        },
        |value| value.slash,
    );
    border.back_slash = back_slash.map_or(
        Slash {
            slash_type: SlashType::None,
            crooked: false,
            is_counter: false,
        },
        |value| value.slash,
    );
    if let Some(value) = slash.or(back_slash) {
        border.diagonal = value.line;
    }
    Ok(())
}

fn empty_cell_paragraph() -> &'static [u8] {
    br#"<hp:p id="0" paraPrIDRef="0" styleIDRef="0"><hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>"#
}

fn extend_bounded(
    output: &mut Vec<u8>,
    bytes: &[u8],
    limit: usize,
) -> Result<(), TableRulingHwpxError> {
    let target = output
        .len()
        .checked_add(bytes.len())
        .ok_or(TableRulingHwpxError::OutputLimit)?;
    if target > limit {
        return Err(TableRulingHwpxError::OutputLimit);
    }
    output
        .try_reserve(bytes.len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    output.extend_from_slice(bytes);
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn render_cell(
    section: &[u8],
    document: &PreservingXmlDocument,
    template: &SourceRenderCell,
    span: &TableCellSpan,
    target_state: &TableRulingState,
    border_id: u32,
    content: Vec<u8>,
    output_limit: usize,
) -> Result<Vec<u8>, TableRulingHwpxError> {
    let row_start =
        usize::try_from(span.row).map_err(|_| TableRulingHwpxError::PlanBindingMismatch)?;
    let row_end = checked_boundary_index(span.row, span.row_span)?;
    let column_start =
        usize::try_from(span.column).map_err(|_| TableRulingHwpxError::PlanBindingMismatch)?;
    let column_end = checked_boundary_index(span.column, span.column_span)?;
    let height = boundary_difference(target_state.row_boundaries_hwpunit(), row_start, row_end)?;
    let width = boundary_difference(
        target_state.column_boundaries_hwpunit(),
        column_start,
        column_end,
    )?;
    let address = unique_child(document, template.element, "cellAddr")?;
    let cell_span = unique_child(document, template.element, "cellSpan")?;
    let size = unique_child(document, template.element, "cellSz")?;
    let mut edits = Vec::new();
    push_attribute_edit(
        document,
        template.element,
        "borderFillIDRef",
        border_id,
        &mut edits,
    )?;
    push_attribute_edit(document, address, "colAddr", span.column, &mut edits)?;
    push_attribute_edit(document, address, "rowAddr", span.row, &mut edits)?;
    push_attribute_edit(document, cell_span, "colSpan", span.column_span, &mut edits)?;
    push_attribute_edit(document, cell_span, "rowSpan", span.row_span, &mut edits)?;
    push_attribute_edit(document, size, "width", width, &mut edits)?;
    push_attribute_edit(document, size, "height", height, &mut edits)?;
    let content_span = element(document, template.sub_list)?
        .content_span()
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    edits.push(RawEdit {
        start: content_span.start(),
        end: content_span.end(),
        replacement: content,
    });
    let outer = element(document, template.element)?
        .outer_span()
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    apply_range_edits(
        section,
        outer.start(),
        outer.end(),
        &mut edits,
        output_limit,
    )
}

fn patch_table(
    section: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    target_state: &TableRulingState,
    target_grid: &TableGrid,
    rows: Vec<u8>,
    output_limit: usize,
) -> Result<Vec<u8>, TableRulingHwpxError> {
    let mut edits = Vec::new();
    push_attribute_edit(document, root, "rowCnt", target_grid.rows(), &mut edits)?;
    push_attribute_edit(document, root, "colCnt", target_grid.columns(), &mut edits)?;
    let size = unique_child(document, root, "sz")?;
    push_attribute_edit(
        document,
        size,
        "width",
        target_state.frame().width_hwpunit,
        &mut edits,
    )?;
    push_attribute_edit(
        document,
        size,
        "height",
        target_state.frame().height_hwpunit,
        &mut edits,
    )?;
    let position = unique_child(document, root, "pos")?;
    push_attribute_edit(
        document,
        position,
        "horzOffset",
        target_state.frame().left_hwpunit,
        &mut edits,
    )?;
    push_attribute_edit(
        document,
        position,
        "vertOffset",
        target_state.frame().top_hwpunit,
        &mut edits,
    )?;
    let table_rows = direct_children_named(document, root, "tr")?;
    let first = table_rows
        .first()
        .and_then(|index| element(document, *index).ok())
        .and_then(XmlElementToken::outer_span)
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    let last = table_rows
        .last()
        .and_then(|index| element(document, *index).ok())
        .and_then(XmlElementToken::outer_span)
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    edits.push(RawEdit {
        start: first.start(),
        end: last.end(),
        replacement: rows,
    });
    apply_edits(section, &mut edits, output_limit)
}

fn patch_header(
    header: &[u8],
    new_borders: &[BorderFill],
    total_count: usize,
    output_limit: usize,
) -> Result<Vec<u8>, TableRulingHwpxError> {
    if new_borders.is_empty() {
        return copy_bounded(header, output_limit);
    }
    let document = PreservingXmlDocument::parse(header)?;
    let mut border_fills = None;
    for (index, value) in document.elements().iter().enumerate() {
        if value.name().namespace() == Some(HANCOM_2020_HEAD_NAMESPACE)
            && value.name().local_name() == "borderFills"
            && border_fills.replace(index).is_some()
        {
            return Err(TableRulingHwpxError::BorderFillLimit);
        }
    }
    let border_fills = border_fills.ok_or(TableRulingHwpxError::BorderFillLimit)?;
    let content = element(&document, border_fills)?
        .content_span()
        .ok_or(TableRulingHwpxError::BorderFillLimit)?;
    let mut inserted = Vec::new();
    for border in new_borders {
        extend_bounded(
            &mut inserted,
            serialize_border(border).as_bytes(),
            output_limit,
        )?;
    }
    let mut edits = Vec::new();
    push_attribute_edit_usize(&document, border_fills, "itemCnt", total_count, &mut edits)?;
    edits.push(RawEdit {
        start: content.end(),
        end: content.end(),
        replacement: inserted,
    });
    apply_edits(header, &mut edits, output_limit)
}

fn serialize_border(border: &BorderFill) -> String {
    use std::fmt::Write as _;

    let mut output = String::new();
    let _ = write!(
        output,
        "<hh:borderFill id=\"{}\" threeD=\"{}\" shadow=\"{}\" centerLine=\"{}\" breakCellSeparateLine=\"{}\">",
        border.id,
        u8::from(border.three_d),
        u8::from(border.shadow),
        center_line(border.center_line),
        u8::from(border.break_cell_separate_line),
    );
    write_slash_xml(&mut output, "slash", border.slash);
    write_slash_xml(&mut output, "backSlash", border.back_slash);
    write_line_xml(&mut output, "leftBorder", border.left);
    write_line_xml(&mut output, "rightBorder", border.right);
    write_line_xml(&mut output, "topBorder", border.top);
    write_line_xml(&mut output, "bottomBorder", border.bottom);
    write_line_xml(&mut output, "diagonal", border.diagonal);
    if let Some(fill) = border.fill_brush {
        let _ = write!(
            output,
            "<hc:fillBrush><hc:winBrush faceColor=\"{}\"",
            color(fill.window.face_color)
        );
        if let Some(value) = fill.window.hatch_color {
            let _ = write!(output, " hatchColor=\"{}\"", color(value));
        }
        if let Some(value) = fill.window.hatch_style {
            let _ = write!(output, " hatchStyle=\"{}\"", hatch_style(value));
        }
        let _ = write!(output, " alpha=\"{}\"/></hc:fillBrush>", fill.window.alpha);
    }
    output.push_str("</hh:borderFill>");
    output
}

fn write_slash_xml(output: &mut String, name: &str, slash: Slash) {
    use std::fmt::Write as _;

    let _ = write!(
        output,
        "<hh:{name} type=\"{}\" Crooked=\"{}\" isCounter=\"{}\"/>",
        slash_type(slash.slash_type),
        u8::from(slash.crooked),
        u8::from(slash.is_counter),
    );
}

fn write_line_xml(output: &mut String, name: &str, line: BorderLine) {
    use std::fmt::Write as _;

    let _ = write!(
        output,
        "<hh:{name} type=\"{}\" width=\"{}\" color=\"{}\"/>",
        line_type(line.line_type),
        border_width(line.width),
        color(line.color),
    );
}

fn push_attribute_edit(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    value: u32,
    edits: &mut Vec<RawEdit>,
) -> Result<(), TableRulingHwpxError> {
    push_attribute_edit_text(document, element_index, name, value.to_string(), edits)
}

fn push_attribute_edit_usize(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    value: usize,
    edits: &mut Vec<RawEdit>,
) -> Result<(), TableRulingHwpxError> {
    push_attribute_edit_text(document, element_index, name, value.to_string(), edits)
}

fn push_attribute_edit_text(
    document: &PreservingXmlDocument,
    element_index: usize,
    name: &str,
    value: String,
    edits: &mut Vec<RawEdit>,
) -> Result<(), TableRulingHwpxError> {
    let attribute = attribute_token(element(document, element_index)?, name)?;
    if attribute.semantic_value() != value {
        let span = attribute.value_span();
        edits
            .try_reserve(1)
            .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
        edits.push(RawEdit {
            start: span.start(),
            end: span.end(),
            replacement: value.into_bytes(),
        });
    }
    Ok(())
}

fn apply_range_edits(
    source: &[u8],
    start: usize,
    end: usize,
    edits: &mut [RawEdit],
    output_limit: usize,
) -> Result<Vec<u8>, TableRulingHwpxError> {
    let range = source
        .get(start..end)
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    for edit in edits.iter_mut() {
        edit.start = edit
            .start
            .checked_sub(start)
            .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
        edit.end = edit
            .end
            .checked_sub(start)
            .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    }
    apply_edits(range, edits, output_limit)
}

fn apply_edits(
    source: &[u8],
    edits: &mut [RawEdit],
    output_limit: usize,
) -> Result<Vec<u8>, TableRulingHwpxError> {
    edits.sort_unstable_by_key(|edit| (edit.start, edit.end));
    let mut previous_end = 0_usize;
    let mut output_len = source.len();
    for edit in edits.iter() {
        if edit.start < previous_end || edit.end < edit.start || edit.end > source.len() {
            return Err(TableRulingHwpxError::UnsupportedCellShape);
        }
        previous_end = edit.end;
        output_len = output_len
            .checked_sub(edit.end - edit.start)
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(TableRulingHwpxError::OutputLimit)?;
    }
    if output_len > output_limit {
        return Err(TableRulingHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    let mut cursor = 0_usize;
    for edit in edits.iter() {
        output.extend_from_slice(&source[cursor..edit.start]);
        output.extend_from_slice(&edit.replacement);
        cursor = edit.end;
    }
    output.extend_from_slice(&source[cursor..]);
    if output.len() != output_len {
        return Err(TableRulingHwpxError::OutputLimit);
    }
    Ok(output)
}

fn copy_bounded(source: &[u8], output_limit: usize) -> Result<Vec<u8>, TableRulingHwpxError> {
    if source.len() > output_limit {
        return Err(TableRulingHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(source.len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    output.extend_from_slice(source);
    Ok(output)
}

fn read_existing(
    header: &[u8],
    section: &[u8],
    table_ordinal: usize,
    binding: &TableRulingHwpxBinding,
    limits: &TableRulingHwpxLimits,
    allow_caption: bool,
    aggregate_formula: bool,
) -> Result<TableRulingHwpxReadback, TableRulingHwpxError> {
    let layout = if allow_caption {
        TableLayoutHwpxReader::read_in_section_preserving_caption(
            section,
            table_ordinal,
            limits.layout,
        )?
    } else {
        TableLayoutHwpxReader::read_in_section(section, table_ordinal, limits.layout)?
    };
    let grid = validated_grid(&layout, binding, limits.grid)?;

    let catalog = ParagraphStyleCatalogReader::read(header, limits.paragraph_style)?;
    let style_catalog = style_catalog(&catalog.border_fills)?;
    let borders = catalog
        .border_fills
        .iter()
        .map(|border| (border.id, border))
        .collect::<BTreeMap<_, _>>();
    let document = PreservingXmlDocument::parse(section)?;
    let root = selected_table(&document, table_ordinal)?;
    let cells = selected_cells(&document, root, layout.cells.len())?;
    let formula_count = formula_field_count(&document, root)?;
    let formula = match formula_count {
        0 => None,
        1 => Some(if aggregate_formula {
            TableFormulaHwpxReader::read_aggregate_in_section(
                section,
                table_ordinal,
                limits.formula_hwpx,
                limits.formula,
            )?
            .formula
        } else {
            TableFormulaHwpxReader::read_in_section_preserving_merged_topology(
                section,
                table_ordinal,
                limits.formula_hwpx,
                limits.formula,
            )?
            .formula
        }),
        _ => return Err(TableRulingHwpxError::UnsupportedFormulaShape),
    };

    let (native_cells, payload_block_count) =
        read_native_cells(section, &document, &cells, &layout.cells, &borders)?;

    let slot_owners = slot_owners(layout.rows, layout.columns, &native_cells)?;
    let edges = native_edges(layout.rows, layout.columns, &native_cells, &slot_owners)?;
    let cell_drafts = build_cell_drafts(&native_cells, &binding.cells, formula.as_ref(), &grid)?;

    let state = build_state(
        section,
        &document,
        root,
        binding,
        &grid,
        &layout,
        edges,
        cell_drafts,
        limits,
    )?;
    Ok(TableRulingHwpxReadback {
        profile_id: TABLE_RULING_HWPX_PROFILE_ID,
        grid,
        state,
        header_sha256: Sha256::digest(header).into(),
        section_sha256: Sha256::digest(section).into(),
        table_content_sha256: layout.content_sha256,
        style_catalog,
        border_fill_count: catalog.border_fills.len(),
        payload_block_count,
        formula_count,
    })
}

fn validated_grid(
    layout: &crate::TableLayoutHwpxReadback,
    binding: &TableRulingHwpxBinding,
    limits: TableGridLimits,
) -> Result<TableGrid, TableRulingHwpxError> {
    let row_boundary_count = usize::try_from(layout.rows)
        .ok()
        .and_then(|value| value.checked_add(1))
        .ok_or(TableRulingHwpxError::InvalidBinding)?;
    let column_boundary_count = usize::try_from(layout.columns)
        .ok()
        .and_then(|value| value.checked_add(1))
        .ok_or(TableRulingHwpxError::InvalidBinding)?;
    if binding.cells.len() != layout.cells.len()
        || binding.row_boundaries_hwpunit.len() != row_boundary_count
        || binding.column_boundaries_hwpunit.len() != column_boundary_count
    {
        return Err(TableRulingHwpxError::InvalidBinding);
    }
    let mut spans = Vec::new();
    spans
        .try_reserve_exact(layout.cells.len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    for (cell, identity) in layout.cells.iter().zip(&binding.cells) {
        spans.push(TableCellSpan {
            master_cell_id: identity.master_cell_id.clone(),
            row: cell.row,
            column: cell.column,
            row_span: cell.row_span,
            column_span: cell.column_span,
        });
    }
    let grid = TableGrid::new(layout.rows, layout.columns, spans, limits)?;
    validate_boundary_extent(&binding.row_boundaries_hwpunit, layout.table_height_hwpunit)?;
    validate_boundary_extent(
        &binding.column_boundaries_hwpunit,
        layout.table_width_hwpunit,
    )?;
    for cell in &layout.cells {
        validate_cell_extent(cell, binding)?;
    }
    Ok(grid)
}

fn validate_cell_extent(
    cell: &crate::TableCellSizeReadback,
    binding: &TableRulingHwpxBinding,
) -> Result<(), TableRulingHwpxError> {
    let row_end = checked_boundary_index(cell.row, cell.row_span)?;
    let column_end = checked_boundary_index(cell.column, cell.column_span)?;
    let height = boundary_difference(
        &binding.row_boundaries_hwpunit,
        usize::try_from(cell.row).map_err(|_| TableRulingHwpxError::InvalidBinding)?,
        row_end,
    )?;
    let width = boundary_difference(
        &binding.column_boundaries_hwpunit,
        usize::try_from(cell.column).map_err(|_| TableRulingHwpxError::InvalidBinding)?,
        column_end,
    )?;
    if height != cell.height_hwpunit || width != cell.width_hwpunit {
        return Err(TableRulingHwpxError::PhysicalExtentMismatch);
    }
    Ok(())
}

fn read_native_cells(
    section: &[u8],
    document: &PreservingXmlDocument,
    cells: &[(usize, CellCoordinate)],
    layout_cells: &[crate::TableCellSizeReadback],
    borders: &BTreeMap<u32, &BorderFill>,
) -> Result<(Vec<NativeCell>, usize), TableRulingHwpxError> {
    let mut native_cells = Vec::new();
    native_cells
        .try_reserve_exact(cells.len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    let mut payload_block_count = 0_usize;
    for ((cell_index, address), layout_cell) in cells.iter().zip(layout_cells) {
        if address.row != layout_cell.row || address.column != layout_cell.column {
            return Err(TableRulingHwpxError::UnsupportedCellShape);
        }
        let root_element = element(document, *cell_index)?;
        let border_id = required_u32(root_element, "borderFillIDRef")?;
        let border = (*borders
            .get(&border_id)
            .ok_or(TableRulingHwpxError::DanglingBorderFill)?)
        .clone();
        let sub_list = unique_child(document, *cell_index, "subList")?;
        let payload_sha256 = payload_digests(section, document, sub_list)?;
        payload_block_count = payload_block_count
            .checked_add(payload_sha256.len())
            .ok_or(TableRulingHwpxError::AllocationFailed)?;
        native_cells.push(NativeCell {
            coordinate: *address,
            row_span: layout_cell.row_span,
            column_span: layout_cell.column_span,
            properties: cell_properties(document, *cell_index, sub_list, &border)?,
            border,
            payload_sha256,
        });
    }
    Ok((native_cells, payload_block_count))
}

fn build_cell_drafts(
    native_cells: &[NativeCell],
    bindings: &[TableRulingHwpxCellBinding],
    formula: Option<&domain_ir::FormulaCell>,
    grid: &TableGrid,
) -> Result<Vec<TableRulingCellDraft>, TableRulingHwpxError> {
    let mut drafts = Vec::new();
    drafts
        .try_reserve_exact(native_cells.len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    for (index, (native, identity)) in native_cells.iter().zip(bindings).enumerate() {
        if identity.payload_block_ids.len() != native.payload_sha256.len() {
            return Err(TableRulingHwpxError::PayloadBindingMismatch);
        }
        let mut payload = Vec::new();
        payload
            .try_reserve_exact(identity.payload_block_ids.len())
            .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
        for (block_id, payload_sha256) in identity
            .payload_block_ids
            .iter()
            .zip(&native.payload_sha256)
        {
            payload.push(TableRulingPayloadBlock {
                block_id: block_id.clone(),
                payload_sha256: payload_sha256.clone(),
            });
        }
        let native_formula = formula
            .filter(|value| value.owner() == native.coordinate)
            .map(formula_draft);
        if formula.is_some_and(|value| {
            value.owner() == native.coordinate
                && grid.master_cells().get(index).is_none_or(|span| {
                    span.row != native.coordinate.row || span.column != native.coordinate.column
                })
        }) {
            return Err(TableRulingHwpxError::UnsupportedFormulaShape);
        }
        drafts.push(TableRulingCellDraft {
            master_cell_id: identity.master_cell_id.clone(),
            coordinate: native.coordinate,
            payload,
            properties: native.properties.clone(),
            formula: native_formula,
        });
    }
    if formula.is_some_and(|value| {
        !native_cells
            .iter()
            .any(|cell| cell.coordinate == value.owner())
    }) {
        return Err(TableRulingHwpxError::UnsupportedFormulaShape);
    }
    Ok(drafts)
}

#[allow(clippy::too_many_arguments)]
fn build_state(
    section: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    binding: &TableRulingHwpxBinding,
    grid: &TableGrid,
    layout: &crate::TableLayoutHwpxReadback,
    edges: Vec<TableRulingEdge>,
    cells: Vec<TableRulingCellDraft>,
    limits: &TableRulingHwpxLimits,
) -> Result<TableRulingState, TableRulingHwpxError> {
    let position = unique_child(document, root, "pos")?;
    let left_hwpunit = required_u32(element(document, position)?, "horzOffset")?;
    let top_hwpunit = required_u32(element(document, position)?, "vertOffset")?;
    Ok(TableRulingState::from_draft(
        TableRulingStateDraft {
            schema_version: TABLE_RULING_SCHEMA_VERSION.to_owned(),
            table_id: binding.table_id.clone(),
            frame: TableRulingFrame {
                left_hwpunit,
                top_hwpunit,
                width_hwpunit: layout.table_width_hwpunit,
                height_hwpunit: layout.table_height_hwpunit,
            },
            grid_sha256: hex(grid.canonical_sha256()?),
            table_properties_sha256: table_properties_digest(section, document, root)?,
            row_boundaries_hwpunit: binding.row_boundaries_hwpunit.clone(),
            column_boundaries_hwpunit: binding.column_boundaries_hwpunit.clone(),
            edges,
            cells,
        },
        grid,
        limits.formula,
        limits.ruling,
    )?)
}

fn formula_draft(formula: &domain_ir::FormulaCell) -> FormulaCellDraft {
    FormulaCellDraft {
        schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
        owner: formula.owner(),
        ast: FormulaAstDraft {
            schema_version: TABLE_FORMULA_SCHEMA_VERSION.to_owned(),
            expression: formula.ast().expression().clone(),
        },
        cache: formula.cache().clone(),
        number_format: formula.number_format(),
    }
}

fn checked_boundary_index(start: u32, span: u32) -> Result<usize, TableRulingHwpxError> {
    usize::try_from(
        start
            .checked_add(span)
            .ok_or(TableRulingHwpxError::InvalidBinding)?,
    )
    .map_err(|_| TableRulingHwpxError::InvalidBinding)
}

fn validate_boundary_extent(
    boundaries: &[u32],
    expected_extent: u32,
) -> Result<(), TableRulingHwpxError> {
    if boundaries.first() != Some(&0)
        || boundaries.last() != Some(&expected_extent)
        || boundaries.windows(2).any(|pair| pair[0] >= pair[1])
    {
        return Err(TableRulingHwpxError::InvalidBinding);
    }
    Ok(())
}

fn boundary_difference(
    boundaries: &[u32],
    start: usize,
    end: usize,
) -> Result<u32, TableRulingHwpxError> {
    boundaries
        .get(end)
        .zip(boundaries.get(start))
        .and_then(|(end, start)| end.checked_sub(*start))
        .ok_or(TableRulingHwpxError::InvalidBinding)
}

fn selected_empty_top_level_paragraph(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraph_ordinal: usize,
) -> Result<usize, TableRulingHwpxError> {
    let root = document.root_element();
    let paragraph = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, value)| value.parent() == Some(root) && has_name(value, "p"))
        .nth(paragraph_ordinal)
        .map(|(index, _)| index)
        .ok_or(TableRulingHwpxError::InvalidInsertionContext)?;
    if !is_empty_scaffold(source, document, paragraph)? {
        return Err(TableRulingHwpxError::InvalidInsertionContext);
    }
    Ok(paragraph)
}

fn insertion_context_digest(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraph: usize,
    paragraph_ordinal: usize,
) -> Result<String, TableRulingHwpxError> {
    let paragraph_bytes = element_bytes(source, element(document, paragraph)?)?;
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-ruling-hwpx-insertion-context/v1\0");
    digest.update(Sha256::digest(source));
    digest.update(paragraph_ordinal.to_le_bytes());
    digest.update(Sha256::digest(paragraph_bytes));
    Ok(hex(digest.finalize()))
}

pub(super) fn insertion_wrapper(
    template_section: &[u8],
    table_ordinal: usize,
) -> Result<Vec<u8>, TableRulingHwpxError> {
    let document = PreservingXmlDocument::parse(template_section)?;
    let table = selected_table(&document, table_ordinal)?;
    let root = document.root_element();
    let mut wrapper = table;
    while element(&document, wrapper)?.parent() != Some(root) {
        wrapper = element(&document, wrapper)?
            .parent()
            .ok_or(TableRulingHwpxError::InvalidOuterTemplate)?;
    }
    if !has_name(element(&document, wrapper)?, "p") {
        return Err(TableRulingHwpxError::InvalidOuterTemplate);
    }
    let mut table_count = 0_usize;
    for (index, value) in document.elements().iter().enumerate() {
        if has_name(value, "tbl") && (index == table || is_descendant(&document, index, wrapper)?) {
            table_count = table_count
                .checked_add(1)
                .ok_or(TableRulingHwpxError::AllocationFailed)?;
        }
    }
    if table_count != 1 {
        return Err(TableRulingHwpxError::InvalidOuterTemplate);
    }
    for (index, value) in document.elements().iter().enumerate() {
        if index == wrapper
            || index == table
            || !is_descendant(&document, index, wrapper)?
            || is_descendant(&document, index, table)?
        {
            continue;
        }
        if !matches!(value.name().local_name(), "run" | "ctrl" | "t")
            || value.name().namespace() != Some(PARAGRAPH_NS)
        {
            return Err(TableRulingHwpxError::InvalidOuterTemplate);
        }
        if value.name().local_name() == "t" {
            let span = value
                .content_span()
                .ok_or(TableRulingHwpxError::InvalidOuterTemplate)?;
            if template_section
                .get(span.start()..span.end())
                .is_none_or(|bytes| !bytes.is_empty())
            {
                return Err(TableRulingHwpxError::InvalidOuterTemplate);
            }
        }
    }
    Ok(element_bytes(template_section, element(&document, wrapper)?)?.to_vec())
}

fn ensure_native_table_id_available(
    destination_section: &[u8],
    template_section: &[u8],
    template_table_ordinal: usize,
) -> Result<(), TableRulingHwpxError> {
    let template = PreservingXmlDocument::parse(template_section)?;
    let template_table = selected_table(&template, template_table_ordinal)?;
    let template_id = attribute(element(&template, template_table)?, "id")?;
    let destination = PreservingXmlDocument::parse(destination_section)?;
    for value in destination.elements() {
        if has_name(value, "tbl") && attribute(value, "id")? == template_id {
            return Err(TableRulingHwpxError::NativeTableIdCollision);
        }
    }
    Ok(())
}

fn tables_before_offset(document: &PreservingXmlDocument, offset: usize) -> usize {
    document
        .elements()
        .iter()
        .filter(|value| {
            has_name(value, "tbl") && value.outer_span().is_some_and(|span| span.start() < offset)
        })
        .count()
}

fn selected_table(
    document: &PreservingXmlDocument,
    table_ordinal: usize,
) -> Result<usize, TableRulingHwpxError> {
    document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, value)| has_name(value, "tbl"))
        .nth(table_ordinal)
        .map(|(index, _)| index)
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)
}

fn selected_cells(
    document: &PreservingXmlDocument,
    table: usize,
    expected: usize,
) -> Result<Vec<(usize, CellCoordinate)>, TableRulingHwpxError> {
    let mut cells = Vec::new();
    cells
        .try_reserve_exact(expected)
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    for (index, value) in document.elements().iter().enumerate() {
        if !has_name(value, "tc") || !is_descendant(document, index, table)? {
            continue;
        }
        let parent = value
            .parent()
            .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
        if !has_name(element(document, parent)?, "tr")
            || element(document, parent)?.parent() != Some(table)
        {
            continue;
        }
        let address = unique_child(document, index, "cellAddr")?;
        cells.push((
            index,
            CellCoordinate {
                row: required_u32(element(document, address)?, "rowAddr")?,
                column: required_u32(element(document, address)?, "colAddr")?,
            },
        ));
    }
    cells.sort_unstable_by_key(|(_, coordinate)| *coordinate);
    if cells.len() != expected || cells.windows(2).any(|pair| pair[0].1 == pair[1].1) {
        return Err(TableRulingHwpxError::UnsupportedCellShape);
    }
    Ok(cells)
}

fn payload_digests(
    source: &[u8],
    document: &PreservingXmlDocument,
    sub_list: usize,
) -> Result<Vec<String>, TableRulingHwpxError> {
    let mut output = Vec::new();
    let mut child = element(document, sub_list)?.first_child();
    while let Some(index) = child {
        let value = element(document, index)?;
        if !has_name(value, "p") {
            return Err(TableRulingHwpxError::UnsupportedCellShape);
        }
        if !has_formula_descendant(document, index)? && !is_empty_scaffold(source, document, index)?
        {
            output
                .try_reserve(1)
                .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
            output.push(hex(Sha256::digest(element_bytes(source, value)?)));
        }
        child = value.next_sibling();
    }
    Ok(output)
}

fn is_empty_scaffold(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraph: usize,
) -> Result<bool, TableRulingHwpxError> {
    let mut saw_text = false;
    for (index, value) in document.elements().iter().enumerate() {
        if index == paragraph || !is_descendant(document, index, paragraph)? {
            continue;
        }
        match value.name().local_name() {
            "run" => {}
            "t" if has_name(value, "t") => {
                saw_text = true;
                let span = value
                    .content_span()
                    .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
                if source
                    .get(span.start()..span.end())
                    .is_none_or(|bytes| !bytes.is_empty())
                {
                    return Ok(false);
                }
            }
            _ => return Ok(false),
        }
    }
    Ok(saw_text)
}

fn has_formula_descendant(
    document: &PreservingXmlDocument,
    ancestor: usize,
) -> Result<bool, TableRulingHwpxError> {
    for (index, value) in document.elements().iter().enumerate() {
        if has_name(value, "fieldBegin")
            && is_descendant(document, index, ancestor)?
            && attribute(value, "type")? == "FORMULA"
        {
            return Ok(true);
        }
    }
    Ok(false)
}

fn formula_field_count(
    document: &PreservingXmlDocument,
    table: usize,
) -> Result<usize, TableRulingHwpxError> {
    let mut count = 0_usize;
    for (index, value) in document.elements().iter().enumerate() {
        if has_name(value, "fieldBegin")
            && is_descendant(document, index, table)?
            && attribute(value, "type")? == "FORMULA"
        {
            count = count
                .checked_add(1)
                .ok_or(TableRulingHwpxError::AllocationFailed)?;
        }
    }
    Ok(count)
}

fn cell_properties(
    document: &PreservingXmlDocument,
    cell: usize,
    sub_list: usize,
    border: &BorderFill,
) -> Result<TableRulingCellProperties, TableRulingHwpxError> {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-ruling-cell-non-ruling/v1\0");
    hash_attributes(&mut digest, element(document, cell)?, &["borderFillIDRef"])?;
    hash_attributes(&mut digest, element(document, sub_list)?, &["id"])?;
    let margin = unique_child(document, cell, "cellMargin")?;
    hash_attributes(&mut digest, element(document, margin)?, &[])?;
    hash_bool(&mut digest, border.three_d);
    hash_bool(&mut digest, border.shadow);
    hash_part(&mut digest, center_line(border.center_line));
    hash_bool(&mut digest, border.break_cell_separate_line);
    Ok(TableRulingCellProperties {
        non_ruling_properties_sha256: hex(digest.finalize()),
        background_sha256: border.fill_brush.as_ref().map(background_digest),
        slash_diagonal_sha256: diagonal_digest("slash", border.slash, border.diagonal),
        back_slash_diagonal_sha256: diagonal_digest(
            "back_slash",
            border.back_slash,
            border.diagonal,
        ),
    })
}

fn table_properties_digest(
    source: &[u8],
    document: &PreservingXmlDocument,
    table: usize,
) -> Result<String, TableRulingHwpxError> {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-ruling-table-properties/v1\0");
    hash_attributes(
        &mut digest,
        element(document, table)?,
        &["id", "rowCnt", "colCnt"],
    )?;
    let mut child = element(document, table)?.first_child();
    while let Some(index) = child {
        let value = element(document, index)?;
        match value.name().local_name() {
            "pos" if has_name(value, "pos") => {
                hash_attributes(&mut digest, value, &["horzOffset", "vertOffset"])?;
            }
            "sz" | "tr" if value.name().namespace() == Some(PARAGRAPH_NS) => {}
            _ => hash_part(
                &mut digest,
                &hex(Sha256::digest(element_bytes(source, value)?)),
            ),
        }
        child = value.next_sibling();
    }
    Ok(hex(digest.finalize()))
}

fn slot_owners(
    rows: u32,
    columns: u32,
    cells: &[NativeCell],
) -> Result<Vec<usize>, TableRulingHwpxError> {
    let slots = usize::try_from(rows)
        .ok()
        .and_then(|rows| {
            usize::try_from(columns)
                .ok()
                .and_then(|columns| rows.checked_mul(columns))
        })
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    let mut owners = vec![usize::MAX; slots];
    let columns_usize =
        usize::try_from(columns).map_err(|_| TableRulingHwpxError::UnsupportedCellShape)?;
    for (index, cell) in cells.iter().enumerate() {
        let row_end = cell
            .coordinate
            .row
            .checked_add(cell.row_span)
            .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
        let column_end = cell
            .coordinate
            .column
            .checked_add(cell.column_span)
            .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
        for row in cell.coordinate.row..row_end {
            for column in cell.coordinate.column..column_end {
                let slot = usize::try_from(row)
                    .ok()
                    .and_then(|row| row.checked_mul(columns_usize))
                    .and_then(|base| {
                        usize::try_from(column)
                            .ok()
                            .and_then(|column| base.checked_add(column))
                    })
                    .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
                let owner = owners
                    .get_mut(slot)
                    .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
                if *owner != usize::MAX {
                    return Err(TableRulingHwpxError::UnsupportedCellShape);
                }
                *owner = index;
            }
        }
    }
    if owners.contains(&usize::MAX) {
        return Err(TableRulingHwpxError::UnsupportedCellShape);
    }
    Ok(owners)
}

fn native_edges(
    rows: u32,
    columns: u32,
    cells: &[NativeCell],
    owners: &[usize],
) -> Result<Vec<TableRulingEdge>, TableRulingHwpxError> {
    let mut edges = Vec::new();
    let expected = usize::try_from(rows)
        .ok()
        .and_then(|rows| {
            usize::try_from(columns).ok().and_then(|columns| {
                rows.checked_add(1)
                    .and_then(|row_boundaries| row_boundaries.checked_mul(columns))
                    .and_then(|horizontal| {
                        columns.checked_add(1).and_then(|column_boundaries| {
                            column_boundaries
                                .checked_mul(rows)
                                .and_then(|vertical| horizontal.checked_add(vertical))
                        })
                    })
            })
        })
        .ok_or(TableRulingHwpxError::AllocationFailed)?;
    edges
        .try_reserve_exact(expected)
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    for boundary in 0..=rows {
        for offset in 0..columns {
            let line_sha256 = if boundary == 0 {
                line_digest(cells[owner(owners, rows, columns, 0, offset)?].border.top)
            } else if boundary == rows {
                line_digest(
                    cells[owner(owners, rows, columns, rows - 1, offset)?]
                        .border
                        .bottom,
                )
            } else {
                let above = owner(owners, rows, columns, boundary - 1, offset)?;
                let below = owner(owners, rows, columns, boundary, offset)?;
                if above == below {
                    None
                } else {
                    shared_line(cells[above].border.bottom, cells[below].border.top)?
                }
            };
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Horizontal,
                boundary,
                offset,
                line_sha256,
            });
        }
    }
    for boundary in 0..=columns {
        for offset in 0..rows {
            let line_sha256 = if boundary == 0 {
                line_digest(cells[owner(owners, rows, columns, offset, 0)?].border.left)
            } else if boundary == columns {
                line_digest(
                    cells[owner(owners, rows, columns, offset, columns - 1)?]
                        .border
                        .right,
                )
            } else {
                let left = owner(owners, rows, columns, offset, boundary - 1)?;
                let right = owner(owners, rows, columns, offset, boundary)?;
                if left == right {
                    None
                } else {
                    shared_line(cells[left].border.right, cells[right].border.left)?
                }
            };
            edges.push(TableRulingEdge {
                axis: TableRulingAxis::Vertical,
                boundary,
                offset,
                line_sha256,
            });
        }
    }
    Ok(edges)
}

fn owner(
    owners: &[usize],
    rows: u32,
    columns: u32,
    row: u32,
    column: u32,
) -> Result<usize, TableRulingHwpxError> {
    if row >= rows || column >= columns {
        return Err(TableRulingHwpxError::UnsupportedCellShape);
    }
    let index = usize::try_from(row)
        .ok()
        .and_then(|row| {
            usize::try_from(columns)
                .ok()
                .and_then(|columns| row.checked_mul(columns))
        })
        .and_then(|base| {
            usize::try_from(column)
                .ok()
                .and_then(|column| base.checked_add(column))
        })
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    owners
        .get(index)
        .copied()
        .filter(|owner| *owner != usize::MAX)
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)
}

fn shared_line(
    first: BorderLine,
    second: BorderLine,
) -> Result<Option<String>, TableRulingHwpxError> {
    let first = line_digest(first);
    let second = line_digest(second);
    if first != second {
        return Err(TableRulingHwpxError::SharedEdgeMismatch);
    }
    Ok(first)
}

fn style_catalog(
    borders: &[BorderFill],
) -> Result<TableRulingHwpxStyleCatalog, TableRulingHwpxError> {
    let edge_capacity = borders
        .len()
        .checked_mul(4)
        .ok_or(TableRulingHwpxError::AllocationFailed)?;
    let mut edge_lines = Vec::new();
    edge_lines
        .try_reserve_exact(edge_capacity)
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    let mut slash_diagonals = Vec::new();
    slash_diagonals
        .try_reserve_exact(borders.len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    let mut back_slash_diagonals = Vec::new();
    back_slash_diagonals
        .try_reserve_exact(borders.len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    for border in borders {
        for line in [border.left, border.right, border.top, border.bottom] {
            if let Some(value) = line_digest(line) {
                edge_lines.push(value);
            }
        }
        if let Some(value) = diagonal_digest("slash", border.slash, border.diagonal) {
            slash_diagonals.push(value);
        }
        if let Some(value) = diagonal_digest("back_slash", border.back_slash, border.diagonal) {
            back_slash_diagonals.push(value);
        }
    }
    edge_lines.sort_unstable();
    edge_lines.dedup();
    slash_diagonals.sort_unstable();
    slash_diagonals.dedup();
    back_slash_diagonals.sort_unstable();
    back_slash_diagonals.dedup();
    Ok(TableRulingHwpxStyleCatalog {
        edge_line_sha256: edge_lines,
        slash_diagonal_sha256: slash_diagonals,
        back_slash_diagonal_sha256: back_slash_diagonals,
    })
}

fn line_digest(line: BorderLine) -> Option<String> {
    if line.line_type == LineType2::None {
        return None;
    }
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-ruling-line/v1\0");
    hash_line(&mut digest, line);
    Some(hex(digest.finalize()))
}

fn diagonal_digest(direction: &str, slash: Slash, line: BorderLine) -> Option<String> {
    if slash.slash_type == SlashType::None {
        return None;
    }
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-ruling-diagonal/v1\0");
    hash_part(&mut digest, direction);
    hash_part(&mut digest, slash_type(slash.slash_type));
    hash_bool(&mut digest, slash.crooked);
    hash_bool(&mut digest, slash.is_counter);
    hash_line(&mut digest, line);
    Some(hex(digest.finalize()))
}

fn background_digest(fill: &FillBrush) -> String {
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.table-ruling-background/v1\0");
    hash_part(&mut digest, color(fill.window.face_color).as_str());
    hash_part(
        &mut digest,
        fill.window
            .hatch_color
            .map_or_else(|| "none".to_owned(), color)
            .as_str(),
    );
    hash_part(
        &mut digest,
        fill.window.hatch_style.map_or("NONE", hatch_style),
    );
    hash_part(&mut digest, &fill.window.alpha.to_string());
    hex(digest.finalize())
}

fn hash_line(digest: &mut Sha256, line: BorderLine) {
    hash_part(digest, line_type(line.line_type));
    hash_part(digest, border_width(line.width));
    hash_part(digest, &color(line.color));
}

fn hash_attributes(
    digest: &mut Sha256,
    element: &XmlElementToken,
    excluded: &[&str],
) -> Result<(), TableRulingHwpxError> {
    let mut attributes = Vec::new();
    attributes
        .try_reserve_exact(element.attributes().len())
        .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
    for attribute in element.attributes() {
        if !attribute.is_namespace_declaration()
            && !excluded.contains(&attribute.name().local_name())
        {
            attributes.push(attribute);
        }
    }
    attributes.sort_unstable_by(|left, right| {
        (left.name().namespace(), left.name().local_name())
            .cmp(&(right.name().namespace(), right.name().local_name()))
    });
    for attribute in attributes {
        hash_part(
            digest,
            attribute.name().namespace().map_or("", |value| value),
        );
        hash_part(digest, attribute.name().local_name());
        hash_part(digest, attribute.semantic_value());
    }
    Ok(())
}

fn hash_part(digest: &mut Sha256, value: &str) {
    digest.update(value.as_bytes());
    digest.update([0]);
}

fn hash_bool(digest: &mut Sha256, value: bool) {
    hash_part(digest, if value { "1" } else { "0" });
}

fn line_type(value: LineType2) -> &'static str {
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

fn border_width(value: BorderWidth) -> &'static str {
    match value {
        BorderWidth::Mm0_1 => "0.1 mm",
        BorderWidth::Mm0_12 => "0.12 mm",
        BorderWidth::Mm0_15 => "0.15 mm",
        BorderWidth::Mm0_2 => "0.2 mm",
        BorderWidth::Mm0_25 => "0.25 mm",
        BorderWidth::Mm0_3 => "0.3 mm",
        BorderWidth::Mm0_4 => "0.4 mm",
        BorderWidth::Mm0_5 => "0.5 mm",
        BorderWidth::Mm0_6 => "0.6 mm",
        BorderWidth::Mm0_7 => "0.7 mm",
        BorderWidth::Mm1_0 => "1.0 mm",
        BorderWidth::Mm1_5 => "1.5 mm",
        BorderWidth::Mm2_0 => "2.0 mm",
        BorderWidth::Mm3_0 => "3.0 mm",
        BorderWidth::Mm4_0 => "4.0 mm",
        BorderWidth::Mm5_0 => "5.0 mm",
    }
}

fn slash_type(value: SlashType) -> &'static str {
    match value {
        SlashType::None => "NONE",
        SlashType::Center => "CENTER",
        SlashType::CenterBelow => "CENTER_BELOW",
        SlashType::CenterAbove => "CENTER_ABOVE",
        SlashType::All => "ALL",
    }
}

fn center_line(value: CenterLine) -> &'static str {
    match value {
        CenterLine::None => "NONE",
        CenterLine::Vertical => "VERTICAL",
        CenterLine::Horizontal => "HORIZONTAL",
        CenterLine::Cross => "CROSS",
    }
}

fn hatch_style(value: HatchStyle) -> &'static str {
    match value {
        HatchStyle::Horizontal => "HORIZONTAL",
        HatchStyle::Vertical => "VERTICAL",
        HatchStyle::BackSlash => "BACK_SLASH",
        HatchStyle::Slash => "SLASH",
        HatchStyle::Cross => "CROSS",
        HatchStyle::CrossDiagonal => "CROSS_DIAGONAL",
    }
}

fn color(value: Color) -> String {
    match value {
        Color::None => "none".to_owned(),
        Color::Rgb(red, green, blue) => format!("#{red:02X}{green:02X}{blue:02X}"),
    }
}

fn element_bytes<'a>(
    source: &'a [u8],
    element: &XmlElementToken,
) -> Result<&'a [u8], TableRulingHwpxError> {
    let span = element
        .outer_span()
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    source
        .get(span.start()..span.end())
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)
}

fn unique_child(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<usize, TableRulingHwpxError> {
    let mut found = None;
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let value = element(document, index)?;
        if has_name(value, local_name) && found.replace(index).is_some() {
            return Err(TableRulingHwpxError::UnsupportedCellShape);
        }
        child = value.next_sibling();
    }
    found.ok_or(TableRulingHwpxError::UnsupportedCellShape)
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
) -> Result<Vec<usize>, TableRulingHwpxError> {
    let mut output = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        let value = element(document, index)?;
        if has_name(value, local_name) {
            output
                .try_reserve(1)
                .map_err(|_| TableRulingHwpxError::AllocationFailed)?;
            output.push(index);
        }
        child = value.next_sibling();
    }
    Ok(output)
}

fn is_descendant(
    document: &PreservingXmlDocument,
    descendant: usize,
    ancestor: usize,
) -> Result<bool, TableRulingHwpxError> {
    let mut parent = element(document, descendant)?.parent();
    while let Some(index) = parent {
        if index == ancestor {
            return Ok(true);
        }
        parent = element(document, index)?.parent();
    }
    Ok(false)
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, TableRulingHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a str, TableRulingHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    if matches.next().is_some() {
        return Err(TableRulingHwpxError::UnsupportedCellShape);
    }
    Ok(value.semantic_value())
}

fn attribute_token<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a crate::XmlAttributeToken, TableRulingHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration()
            && attribute.name().namespace().is_none()
            && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(TableRulingHwpxError::UnsupportedCellShape)?;
    if matches.next().is_some() {
        return Err(TableRulingHwpxError::UnsupportedCellShape);
    }
    Ok(value)
}

fn required_u32(element: &XmlElementToken, name: &str) -> Result<u32, TableRulingHwpxError> {
    let value = attribute(element, name)?;
    if value.is_empty()
        || !value.bytes().all(|byte| byte.is_ascii_digit())
        || (value != "0" && value.starts_with('0'))
    {
        return Err(TableRulingHwpxError::InvalidNumber);
    }
    value
        .parse()
        .map_err(|_| TableRulingHwpxError::InvalidNumber)
}

fn hex(bytes: impl AsRef<[u8]>) -> String {
    use std::fmt::Write as _;

    bytes
        .as_ref()
        .iter()
        .fold(String::new(), |mut output, byte| {
            let _ = write!(output, "{byte:02x}");
            output
        })
}
