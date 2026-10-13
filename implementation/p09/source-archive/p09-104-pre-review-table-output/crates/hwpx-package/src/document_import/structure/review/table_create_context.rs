//! Immutable actual review insertion selection and original blank native table template.
//! This is a precursor to lowering, NOT a whole-document Flow or execution permit.
use super::{
    ImportedDocumentReviewBodies,
    cell_body_output::{descendant_path, named, require_no_observed_protection},
};
use crate::{
    PreservingXmlDocument, TableCreateHwpxError, TableCreateHwpxLimits, TableCreateHwpxReadback,
    TableCreateHwpxReader, TableLayoutHwpxLimits, TableLayoutHwpxReader, TableRulingHwpxBinding,
    TableRulingHwpxCellBinding, document_import::forms::ImportedDocumentForms,
    table_ruling_hwpx::ReviewCreateContextInput,
};
use domain_ir::{Node, SourceAnchorHandle, TableNode};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

/// Only an immutable original importer, fresh package and ACTUAL table anchor are accepted.
/// No caller XML, physical tracks, grid, logical IDs or fabricated Flow hashes.
#[derive(Clone, Copy)]
pub struct ReviewTableTemplate<'a> {
    pub forms: &'a ImportedDocumentForms,
    pub fresh: &'a [u8],
    pub table: &'a SourceAnchorHandle,
}
impl fmt::Debug for ReviewTableTemplate<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewTableTemplate(<redacted>)")
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewTableContextReceipt {
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub template_package_sha256: [u8; 32],
    /// Observed partial graphs, explicitly NOT complete document Flow bindings.
    pub observed_review_graph_sha256: [u8; 32],
    pub observed_template_graph_sha256: [u8; 32],
    pub header_binding: ReviewTableHeaderBinding,
    pub template_rows: u32,
    pub template_columns: u32,
    pub source_table_count_in_selected_part: usize,
    pub new_table_inserted: bool,
    pub full_document_flow_bound: bool,
    pub full_comment_product_acceptance: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewTableHeaderBinding {
    ExactSharedOriginalHeader,
}

/// Fresh replayable selection. Never deserializable; never grants access/publication authority.
pub struct ReviewTableCreationContext<'a, 'b> {
    review: &'a ImportedDocumentReviewBodies<'a>,
    template_forms: &'b ImportedDocumentForms,
    marker: SourceAnchorHandle,
    paragraph: SourceAnchorHandle,
    table: SourceAnchorHandle,
    limits: TableCreateHwpxLimits,
    native: TableCreateHwpxReadback,
    receipt: ReviewTableContextReceipt,
}
impl fmt::Debug for ReviewTableCreationContext<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewTableCreationContext(<redacted>)")
    }
}
impl ReviewTableCreationContext<'_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewTableContextReceipt {
        &self.receipt
    }
    /// Cached immutable observation, not a fresh service read or a create request.
    #[must_use]
    pub const fn native_context(&self) -> &TableCreateHwpxReadback {
        &self.native
    }
    /// Recheck both whole packages, actual selections and original native template guards.
    /// # Errors
    /// Rejects any whole-source/template drift or mismatch before a future lowering step.
    pub fn verify_source(
        &self,
        fresh: &[u8],
        fresh_template: &[u8],
    ) -> Result<(), ReviewTableContextError> {
        let repeated = self.review.prepare_table_creation(
            fresh,
            &self.marker,
            &self.paragraph,
            ReviewTableTemplate {
                forms: self.template_forms,
                fresh: fresh_template,
                table: &self.table,
            },
            self.limits,
        )?;
        if repeated.receipt != self.receipt || repeated.native != self.native {
            return Err(ReviewTableContextError::Readback);
        }
        Ok(())
    }
}

impl<'a> ImportedDocumentReviewBodies<'a> {
    /// Prepare a native table template at an ACTUAL empty paragraph within this review.
    /// This neither outputs a table nor invents the full Flow required by the original compiler.
    /// Header reconciliation and whole-package ID closure remain future lowering requirements.
    /// # Errors
    /// Rejects stale, foreign, other-review, nonempty, protected, header-mismatched,
    /// nonuniform, nonblank, merged or unsupported original template inputs.
    pub fn prepare_table_creation<'b>(
        &'a self,
        fresh: &[u8],
        marker: &SourceAnchorHandle,
        paragraph: &SourceAnchorHandle,
        template: ReviewTableTemplate<'b>,
        limits: TableCreateHwpxLimits,
    ) -> Result<ReviewTableCreationContext<'a, 'b>, ReviewTableContextError> {
        self.verify_source(fresh)
            .map_err(|_| ReviewTableContextError::Source)?;
        template
            .forms
            .source()
            .verify_source(template.fresh)
            .map_err(|_| ReviewTableContextError::Source)?;
        let (xml, body, selected) = select_paragraph(self, marker, paragraph)?;
        let template_header = header(template.forms)?;
        let header = header(self.forms)?;
        if header != template_header {
            return Err(ReviewTableContextError::Header);
        }
        let (template_xml, ordinal, binding) = template_binding(template.forms, template.table)?;
        let native = xml.with_source_bytes(|section| {
            template_xml.with_source_bytes(|template_section| {
                TableCreateHwpxReader::read_review_context(&ReviewCreateContextInput {
                    header: &header,
                    section,
                    body,
                    paragraph: selected,
                    template_section,
                    template_table_ordinal: ordinal,
                    template_binding: &binding,
                    limits,
                })
            })
        })?;
        let receipt = ReviewTableContextReceipt {
            qualification: "source_bound_review_empty_paragraph_and_original_native_2x2_template_NOT_table_output_full_Flow_native_comment_protection_execution_or_Gate",
            source_package_sha256: self.receipt.source_package_sha256,
            template_package_sha256: template.forms.receipt().source_package_sha256,
            observed_review_graph_sha256: self.receipt.graph_sha256,
            observed_template_graph_sha256: template.forms.receipt().graph_sha256,
            header_binding: ReviewTableHeaderBinding::ExactSharedOriginalHeader,
            template_rows: native.template.grid.rows(),
            template_columns: native.template.grid.columns(),
            source_table_count_in_selected_part: native.source_table_count,
            new_table_inserted: false,
            full_document_flow_bound: false,
            full_comment_product_acceptance: false,
        };
        Ok(ReviewTableCreationContext {
            review: self,
            template_forms: template.forms,
            marker: marker.clone(),
            paragraph: paragraph.clone(),
            table: template.table.clone(),
            limits,
            native,
            receipt,
        })
    }
}

fn select_paragraph<'a>(
    review: &'a ImportedDocumentReviewBodies<'_>,
    marker: &SourceAnchorHandle,
    paragraph: &SourceAnchorHandle,
) -> Result<(&'a PreservingXmlDocument, usize, usize), ReviewTableContextError> {
    let observation = review
        .observations
        .iter()
        .find(|o| &o.marker_anchor == marker)
        .ok_or(ReviewTableContextError::Selection)?;
    let body_anchor = observation
        .body_anchor
        .as_ref()
        .ok_or(ReviewTableContextError::Selection)?;
    let source = review.forms.source();
    let body = source
        .resolve_anchor(body_anchor)
        .map_err(|_| ReviewTableContextError::Selection)?;
    let selected = source
        .resolve_anchor(paragraph)
        .map_err(|_| ReviewTableContextError::Selection)?;
    if body.part().path() != selected.part().path() {
        return Err(ReviewTableContextError::Selection);
    }
    let xml = body
        .part()
        .xml()
        .ok_or(ReviewTableContextError::Selection)?;
    let body_index = body
        .element_index()
        .ok_or(ReviewTableContextError::Selection)?;
    let index = selected
        .element_index()
        .ok_or(ReviewTableContextError::Selection)?;
    let node = &xml.elements()[index];
    if !named(node, "p")
        || node
            .parent()
            .is_none_or(|p| !named(&xml.elements()[p], "subList"))
        || descendant_path(xml, body_index, index).is_err()
        || require_no_observed_protection(xml, body_index, index).is_err()
    {
        return Err(ReviewTableContextError::Selection);
    }
    // The unchanged original importer forbids nested reviews. Keep ownership explicit
    // as well, so a future importer extension cannot silently cross review boundaries.
    for other in &review.observations {
        let Some(anchor) = &other.body_anchor else {
            continue;
        };
        if anchor == body_anchor {
            continue;
        }
        let resolved = source
            .resolve_anchor(anchor)
            .map_err(|_| ReviewTableContextError::Selection)?;
        if resolved.part().path() == body.part().path() {
            let other_index = resolved
                .element_index()
                .ok_or(ReviewTableContextError::Selection)?;
            if descendant_path(xml, other_index, index).is_ok() {
                return Err(ReviewTableContextError::Selection);
            }
        }
    }
    Ok((xml, body_index, index))
}

fn header(forms: &ImportedDocumentForms) -> Result<Vec<u8>, ReviewTableContextError> {
    let mut headers = forms
        .source()
        .parts()
        .iter()
        .filter(|p| p.path().as_str() == "Contents/header.xml");
    let selected = headers.next().ok_or(ReviewTableContextError::Header)?;
    if headers.next().is_some() {
        return Err(ReviewTableContextError::Header);
    }
    selected
        .xml()
        .map(|xml| xml.with_source_bytes(<[u8]>::to_vec))
        .ok_or(ReviewTableContextError::Header)
}

fn template_binding<'a>(
    forms: &'a ImportedDocumentForms,
    anchor: &SourceAnchorHandle,
) -> Result<(&'a PreservingXmlDocument, usize, TableRulingHwpxBinding), ReviewTableContextError> {
    let resolved = forms
        .source()
        .resolve_anchor(anchor)
        .map_err(|_| ReviewTableContextError::Template)?;
    let xml = resolved
        .part()
        .xml()
        .ok_or(ReviewTableContextError::Template)?;
    let index = resolved
        .element_index()
        .ok_or(ReviewTableContextError::Template)?;
    if !named(&xml.elements()[index], "tbl") {
        return Err(ReviewTableContextError::Template);
    }
    let table = forms
        .graph()
        .sections()
        .iter()
        .flat_map(|section| &section.body.children)
        .find_map(|n| {
            if let Node::Table(t) = n {
                (t.common.source_anchor.as_ref() == Some(anchor)).then_some(t)
            } else {
                None
            }
        })
        .ok_or(ReviewTableContextError::Template)?;
    let layout =
        TableLayoutHwpxReader::read_from_document(xml, index, TableLayoutHwpxLimits::default())
            .map_err(|_| ReviewTableContextError::Template)?;
    if table.rows != 2
        || table.columns != 2
        || table.cells.len() != 4
        || layout.rows != 2
        || layout.columns != 2
        || layout.cells.len() != 4
        || layout
            .cells
            .iter()
            .any(|c| c.row_span != 1 || c.column_span != 1)
    {
        return Err(ReviewTableContextError::Template);
    }
    let mut widths = [None; 2];
    let mut heights = [None; 2];
    for cell in &layout.cells {
        let column = usize::try_from(cell.column).map_err(|_| ReviewTableContextError::Template)?;
        let row = usize::try_from(cell.row).map_err(|_| ReviewTableContextError::Template)?;
        observe_track(&mut widths, column, cell.width_hwpunit)?;
        observe_track(&mut heights, row, cell.height_hwpunit)?;
    }
    let row_boundaries = boundaries(heights, layout.table_height_hwpunit)?;
    let column_boundaries = boundaries(widths, layout.table_width_hwpunit)?;
    let cells = bound_cells(table, &layout)?;
    let ordinal = xml.elements()[..index]
        .iter()
        .filter(|e| named(e, "tbl"))
        .count();
    Ok((
        xml,
        ordinal,
        TableRulingHwpxBinding {
            table_id: table.common.node_id.clone(),
            row_boundaries_hwpunit: row_boundaries,
            column_boundaries_hwpunit: column_boundaries,
            cells,
        },
    ))
}
fn observe_track(
    tracks: &mut [Option<u32>; 2],
    index: usize,
    value: u32,
) -> Result<(), ReviewTableContextError> {
    let track = tracks
        .get_mut(index)
        .ok_or(ReviewTableContextError::Template)?;
    if value == 0 || track.is_some_and(|old| old != value) {
        return Err(ReviewTableContextError::Template);
    }
    *track = Some(value);
    Ok(())
}
fn boundaries(tracks: [Option<u32>; 2], total: u32) -> Result<Vec<u32>, ReviewTableContextError> {
    let first = tracks[0].ok_or(ReviewTableContextError::Template)?;
    let last = first
        .checked_add(tracks[1].ok_or(ReviewTableContextError::Template)?)
        .ok_or(ReviewTableContextError::Template)?;
    if last != total {
        return Err(ReviewTableContextError::Template);
    }
    Ok(vec![0, first, last])
}
fn bound_cells(
    table: &TableNode,
    layout: &crate::TableLayoutHwpxReadback,
) -> Result<Vec<TableRulingHwpxCellBinding>, ReviewTableContextError> {
    table
        .cells
        .iter()
        .map(|cell| {
            if cell.row_span != 1
                || cell.column_span != 1
                || !layout
                    .cells
                    .iter()
                    .any(|c| c.row == cell.row && c.column == cell.column)
            {
                return Err(ReviewTableContextError::Template);
            }
            // Empty scaffold paragraphs do have graph IDs. They are NOT payload blocks.
            // The unchanged native ruling reader subsequently proves payload/formula count zero.
            Ok(TableRulingHwpxCellBinding {
                master_cell_id: cell.cell_id.clone(),
                payload_block_ids: Vec::new(),
            })
        })
        .collect()
}

#[derive(Debug, Error)]
pub enum ReviewTableContextError {
    #[error("review table context whole source or template drifted")]
    Source,
    #[error("review table context selection is not owned or is protected")]
    Selection,
    #[error("review table context requires an exactly shared original header")]
    Header,
    #[error("review table context requires an actual supported native template")]
    Template,
    #[error("review table context fresh replay mismatched")]
    Readback,
    #[error(transparent)]
    Native(#[from] TableCreateHwpxError),
}
