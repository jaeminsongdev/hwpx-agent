//! Source-only native creation primitives. No invented full-document Flow or compiler permit.
use super::{
    ReviewCreateContextInput, TableCreateHwpxError, TableCreateHwpxReadback, TableCreateHwpxReader,
    TableGrid, TableRulingHwpxBinding, TableRulingHwpxReadback, TableRulingHwpxReader,
    TableRulingState, build_created_state, hex, native_created_table_wrapper,
};
use crate::{PreservingXmlDocument, TablePaginationHwpxReader};
use domain_ir::LogicalId;
use sha2::{Digest as _, Sha256};

pub(crate) struct ReviewTableRenderInput<'a> {
    pub context: ReviewCreateContextInput<'a>,
    pub expected: &'a TableCreateHwpxReadback,
    pub row_heights: &'a [u32],
    pub column_widths: &'a [u32],
}
pub(crate) struct ReviewNativeTableOutput {
    pub header: Vec<u8>,
    pub section: Vec<u8>,
    pub binding: TableRulingHwpxBinding,
    pub table_ordinal: usize,
    pub grid: TableGrid,
    pub state: TableRulingState,
    pub reopened: TableRulingHwpxReadback,
    pub target_table_count: usize,
    pub added_border_fills: usize,
}

pub(crate) fn render_review_table(
    input: &ReviewTableRenderInput<'_>,
) -> Result<ReviewNativeTableOutput, TableCreateHwpxError> {
    let source = TableCreateHwpxReader::read_review_context(&input.context)?;
    if source != *input.expected {
        return Err(TableCreateHwpxError::SourceBindingMismatch);
    }
    let limits = input.context.limits;
    let (grid, state) = create_target(input, &source)?;
    let rows = grid.rows();
    let columns = grid.columns();
    let rendered = super::super::render_create_from_template(
        input.context.header,
        input.context.template_section,
        input.context.template_table_ordinal,
        input.context.template_binding,
        &source.template.state,
        &state,
        &grid,
        &limits.ruling,
    )?;
    let wrapper = native_created_table_wrapper(
        input.context.section,
        &rendered.section,
        input.context.template_table_ordinal,
        grid.master_cell_count(),
        limits.ruling.layout.config().output_bytes,
    )?;
    let document = PreservingXmlDocument::parse(input.context.section)?;
    let wrapper = retain_selected_paragraph_identity(
        &document,
        input.context.paragraph,
        &rendered.section,
        input.context.template_table_ordinal,
        &wrapper,
        limits.ruling.layout.config().output_bytes,
    )?;
    let span = super::super::element(&document, input.context.paragraph)?
        .outer_span()
        .ok_or(TableCreateHwpxError::ReadbackMismatch)?;
    let table_ordinal = super::super::tables_before_offset(&document, span.start());
    let section = super::super::apply_edits(
        input.context.section,
        &mut [super::RawEdit {
            start: span.start(),
            end: span.end(),
            replacement: wrapper,
        }],
        limits.ruling.layout.config().output_bytes,
    )?;
    let binding = super::super::binding_from_state(&state, &grid)?;
    let reopened = TableRulingHwpxReader::read_existing(
        &rendered.header,
        &section,
        table_ordinal,
        &binding,
        limits.ruling,
    )?;
    let pagination =
        TablePaginationHwpxReader::read_in_section(&section, table_ordinal, limits.pagination)?;
    let target_table_count =
        TablePaginationHwpxReader::count_in_section(&section, limits.pagination)?;
    if reopened.grid != grid
        || reopened.state != state
        || reopened.payload_block_count != 0
        || reopened.formula_count != 0
        || pagination.row_count != rows
        || pagination.column_count != columns
        || pagination.page_split != source.template_pagination.page_split
        || pagination.repeat_header_rows != 0
        || pagination.caption.is_some()
        || Some(target_table_count) != source.source_table_count.checked_add(1)
    {
        return Err(TableCreateHwpxError::ReadbackMismatch);
    }
    Ok(ReviewNativeTableOutput {
        header: rendered.header,
        section,
        binding,
        table_ordinal,
        grid,
        state,
        reopened,
        target_table_count,
        added_border_fills: rendered.added_border_fill_count,
    })
}

/// A template wrapper is new content, not a new paragraph identity. Keep the identity of
/// the actual paragraph replaced, including the native zero sentinel. Original package
/// ID validation remains mandatory and rejects source collisions/dangling references.
fn retain_selected_paragraph_identity(
    source: &PreservingXmlDocument,
    paragraph: usize,
    rendered: &[u8],
    table_ordinal: usize,
    wrapper: &[u8],
    limit: usize,
) -> Result<Vec<u8>, TableCreateHwpxError> {
    let source_id = super::super::element(source, paragraph)?
        .attributes()
        .iter()
        .find(|a| a.name().namespace().is_none() && a.name().local_name() == "id")
        .ok_or(TableCreateHwpxError::InvalidBinding)?
        .semantic_value();
    if source_id.is_empty() || !source_id.bytes().all(|b| b.is_ascii_digit()) {
        return Err(TableCreateHwpxError::InvalidBinding);
    }
    // A wrapper fragment inherits namespace bindings. Parse the admitted whole template,
    // never an unbound fragment or an invented namespace envelope.
    let xml = PreservingXmlDocument::parse(rendered)?;
    let index = super::super::insertion_wrapper_element(rendered, &xml, table_ordinal)?;
    let root = super::super::element(&xml, index)?;
    if !super::super::has_name(root, "p") {
        return Err(TableCreateHwpxError::ReadbackMismatch);
    }
    let span = root
        .attributes()
        .iter()
        .find(|a| a.name().namespace().is_none() && a.name().local_name() == "id")
        .ok_or(TableCreateHwpxError::InvalidBinding)?
        .value_span();
    let start = root
        .outer_span()
        .ok_or(TableCreateHwpxError::ReadbackMismatch)?
        .start();
    let left = span
        .start()
        .checked_sub(start)
        .ok_or(TableCreateHwpxError::ReadbackMismatch)?;
    let right = span
        .end()
        .checked_sub(start)
        .ok_or(TableCreateHwpxError::ReadbackMismatch)?;
    if wrapper.get(left..right) != rendered.get(span.start()..span.end()) {
        return Err(TableCreateHwpxError::ReadbackMismatch);
    }
    Ok(super::super::apply_edits(
        wrapper,
        &mut [super::RawEdit {
            start: left,
            end: right,
            replacement: source_id.as_bytes().to_vec(),
        }],
        limit,
    )?)
}

fn create_target(
    input: &ReviewTableRenderInput<'_>,
    source: &TableCreateHwpxReadback,
) -> Result<(TableGrid, TableRulingState), TableCreateHwpxError> {
    let limits = input.context.limits;
    let rows =
        u32::try_from(input.row_heights.len()).map_err(|_| TableCreateHwpxError::InvalidTracks)?;
    let columns = u32::try_from(input.column_widths.len())
        .map_err(|_| TableCreateHwpxError::InvalidTracks)?;
    let config = limits.ruling.grid.config();
    let count = input
        .row_heights
        .len()
        .checked_mul(input.column_widths.len())
        .filter(|n| *n <= config.slots && *n <= config.master_cells)
        .ok_or(TableCreateHwpxError::InputLimit)?;
    if rows == 0
        || columns == 0
        || rows > config.rows
        || columns > config.columns
        || input
            .row_heights
            .iter()
            .chain(input.column_widths)
            .any(|n| *n == 0)
    {
        return Err(TableCreateHwpxError::InvalidTracks);
    }
    // New logical IDs are deterministic transient builder identities, NOT native IDs,
    // source anchors or replacement full-Flow hashes. Native identity comes from the template.
    let mut digest = Sha256::new();
    digest.update(b"hwpx-agent.review-new-table-logical-identity/v1\0");
    digest.update(source.insertion_context_sha256.as_bytes());
    digest.update(rows.to_le_bytes());
    digest.update(columns.to_le_bytes());
    for n in input.row_heights.iter().chain(input.column_widths) {
        digest.update(n.to_le_bytes());
    }
    let identity = hex(digest.finalize());
    let table_id = LogicalId::parse(format!("review-new-table-{identity}"))
        .map_err(|_| TableCreateHwpxError::InvalidBinding)?;
    let mut ids = Vec::new();
    ids.try_reserve_exact(count)
        .map_err(|_| TableCreateHwpxError::OutputLimit)?;
    for cell in 0..count {
        ids.push(
            LogicalId::parse(format!("review-new-cell-{identity}-{cell}"))
                .map_err(|_| TableCreateHwpxError::InvalidBinding)?,
        );
    }
    let (grid, _) =
        TableGrid::create_unmerged(rows, columns, ids, limits.ruling.grid)?.into_parts();
    let state = build_created_state(
        &table_id,
        &grid,
        input.row_heights,
        input.column_widths,
        &source.template,
        &limits,
    )?;
    Ok((grid, state))
}
