//! Actual newly created review table populated through original typed cell body outputs.
//! Intermediate blank creation and final filled output are distinct integrity observations.
use super::{
    ReviewTableCreationContext,
    cell_body_output::named,
    output::{ReviewTableDimensions, ReviewTableOutputError, ReviewTableOutputReceipt},
};
use crate::{
    PackagePath, TextFlow, TextFlowLimits, TextFlowWriter, WriterError, WriterLimits,
    document_import::{
        ImportedSourcePackage,
        forms::ImportedDocumentForms,
        structure::review::{
            ImportedDocumentReviewBodies, body_output::ReviewBodyOutputError,
            cell_body_output::ReviewCellBodyOutput,
        },
    },
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeSet, fmt};
use thiserror::Error;

/// Coordinates of the requested NEW table only, never arbitrary source cell identities.
pub struct ReviewNewTableCell {
    pub row: u32,
    pub column: u32,
    pub paragraphs: Vec<TextFlow>,
}
impl fmt::Debug for ReviewNewTableCell {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewNewTableCell(<redacted>)")
    }
}
pub struct ReviewNewTableCells {
    cells: Vec<ReviewNewTableCell>,
    paragraphs: usize,
}
impl fmt::Debug for ReviewNewTableCells {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ReviewNewTableCells")
            .field("cells", &self.cells.len())
            .finish_non_exhaustive()
    }
}
impl ReviewNewTableCells {
    /// A finite complete edit set in canonical coordinate order.
    /// # Errors
    /// Rejects empty/duplicate edits, empty cells, over128 edits/512 paragraphs/8MiB lowered
    /// contents, or original typed writer failures. Actual geometry/styles/IDs are checked later.
    pub fn new(mut cells: Vec<ReviewNewTableCell>) -> Result<Self, ReviewFilledTableError> {
        if cells.is_empty() || cells.len() > 128 {
            return Err(ReviewFilledTableError::Values);
        }
        let mut seen = BTreeSet::new();
        let mut paragraphs = 0usize;
        let mut bytes = 0usize;
        for cell in &cells {
            if cell.paragraphs.is_empty() || !seen.insert((cell.row, cell.column)) {
                return Err(ReviewFilledTableError::Values);
            }
            paragraphs = paragraphs
                .checked_add(cell.paragraphs.len())
                .filter(|n| *n <= 512)
                .ok_or(ReviewFilledTableError::Values)?;
            for p in &cell.paragraphs {
                let xml = TextFlowWriter::lower(p, TextFlowLimits::default())
                    .map_err(|_| ReviewFilledTableError::Values)?;
                bytes = bytes
                    .checked_add(xml.len())
                    .filter(|n| *n <= 8 * 1024 * 1024)
                    .ok_or(ReviewFilledTableError::Values)?;
            }
        }
        cells.sort_by_key(|c| (c.row, c.column));
        Ok(Self { cells, paragraphs })
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewFilledTableReceipt {
    pub qualification: &'static str,
    /// This digest is the intermediate BLANK native package, not the final filled artifact.
    pub blank_creation: ReviewTableOutputReceipt,
    pub final_package_sha256: [u8; 32],
    pub final_bytes: usize,
    pub cell_output_chain_sha256: [u8; 32],
    pub populated_cells: usize,
    pub populated_paragraphs: usize,
    pub geometry_and_unselected_content_exact: bool,
    pub full_document_flow_bound: bool,
    pub full_comment_product_acceptance: bool,
}
pub struct ReviewFilledTableOutput {
    output: ReviewCellBodyOutput,
    receipt: ReviewFilledTableReceipt,
}
impl fmt::Debug for ReviewFilledTableOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewFilledTableOutput(<redacted>)")
    }
}
impl ReviewFilledTableOutput {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewFilledTableReceipt {
        &self.receipt
    }
    /// Final immutable artifact integrity only, not original-source access or publication.
    /// # Errors
    /// Rejects original artifact corruption before exposing final bytes.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.output.with_verified_bytes(consume)
    }
}
impl ReviewTableCreationContext<'_, '_> {
    /// Compose original blank native creation and original actual-cell typed body lowering.
    /// Each successive cell uses fresh anchors reimported from the preceding actual artifact.
    /// # Errors
    /// Rejects old source/template drift, out-of-grid edits, all original context/cell/ID/style/
    /// protection/writer/readback limits and preservation errors without returning partial output.
    pub fn lower_table_with_cells(
        &self,
        fresh: &[u8],
        template: &[u8],
        dimensions: &ReviewTableDimensions,
        cells: &ReviewNewTableCells,
        limits: WriterLimits,
    ) -> Result<ReviewFilledTableOutput, ReviewFilledTableError> {
        let blank = self.lower_table(fresh, template, dimensions, limits)?;
        let creation = blank.receipt().clone();
        if cells
            .cells
            .iter()
            .any(|c| c.row >= creation.target_rows || c.column >= creation.target_columns)
        {
            return Err(ReviewFilledTableError::Values);
        }
        let source = self.review.forms.source();
        let selected = source
            .resolve_anchor(&self.paragraph)
            .map_err(|_| ReviewFilledTableError::Selection)?;
        let start = selected
            .element()
            .and_then(crate::XmlElementToken::outer_span)
            .ok_or(ReviewFilledTableError::Selection)?
            .start();
        let ordinal = self
            .review
            .observations
            .iter()
            .position(|o| o.marker_anchor == self.marker)
            .ok_or(ReviewFilledTableError::Selection)?;
        let mut bytes = blank
            .with_verified_bytes(<[u8]>::to_vec)
            .map_err(|_| ReviewFilledTableError::Integrity)?;
        let mut chain = Sha256::new();
        chain.update(b"hwpx-agent.review-new-table-cell-output-chain/v1\0");
        chain.update(creation.output_package_sha256);
        let mut last = None;
        for cell in &cells.cells {
            let forms = ImportedDocumentForms::import(
                ImportedSourcePackage::import(
                    &bytes,
                    source.document_id.clone(),
                    Sha256::digest(&bytes).into(),
                    source.limits,
                )
                .map_err(|_| ReviewFilledTableError::Selection)?,
            )
            .map_err(|_| ReviewFilledTableError::Selection)?;
            let review = ImportedDocumentReviewBodies::import(&forms)
                .map_err(|_| ReviewFilledTableError::Selection)?;
            let anchor =
                created_cell(&forms, selected.part().path(), start, cell.row, cell.column)?;
            let marker = &review
                .observations()
                .get(ordinal)
                .ok_or(ReviewFilledTableError::Selection)?
                .marker_anchor;
            let output =
                review.lower_table_cell_body(&bytes, marker, &anchor, &cell.paragraphs, limits)?;
            if !output
                .receipt()
                .containing_table_geometry_and_other_cells_exact
            {
                return Err(ReviewFilledTableError::Selection);
            }
            chain.update(cell.row.to_le_bytes());
            chain.update(cell.column.to_le_bytes());
            chain.update(output.receipt().output.output_package_sha256);
            bytes = output
                .with_verified_bytes(<[u8]>::to_vec)
                .map_err(|_| ReviewFilledTableError::Integrity)?;
            last = Some(output);
        }
        self.verify_source(fresh, template)
            .map_err(ReviewTableOutputError::from)?;
        let output = last.ok_or(ReviewFilledTableError::Values)?;
        let receipt = ReviewFilledTableReceipt {
            qualification: "actual_new_review_table_with_typed_cell_paragraphs_original_create_and_cell_body_reimport_NOT_full_rich_Flow_comment_compiler_native_execution_publication_or_Gate",
            blank_creation: creation,
            final_package_sha256: Sha256::digest(&bytes).into(),
            final_bytes: bytes.len(),
            cell_output_chain_sha256: chain.finalize().into(),
            populated_cells: cells.cells.len(),
            populated_paragraphs: cells.paragraphs,
            geometry_and_unselected_content_exact: true,
            full_document_flow_bound: false,
            full_comment_product_acceptance: false,
        };
        Ok(ReviewFilledTableOutput { output, receipt })
    }
}
fn created_cell(
    forms: &ImportedDocumentForms,
    path: &PackagePath,
    start: usize,
    row: u32,
    column: u32,
) -> Result<domain_ir::SourceAnchorHandle, ReviewFilledTableError> {
    let part = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path() == path)
        .ok_or(ReviewFilledTableError::Selection)?;
    let xml = part.xml().ok_or(ReviewFilledTableError::Selection)?;
    let mut tables = xml.elements().iter().enumerate().filter(|(_, e)| {
        if !named(e, "tbl") {
            return false;
        }
        e.parent()
            .and_then(|r| xml.elements()[r].parent())
            .is_some_and(|p| {
                named(&xml.elements()[p], "p")
                    && xml.elements()[p]
                        .outer_span()
                        .is_some_and(|s| s.start() == start)
            })
    });
    let (table, _) = tables.next().ok_or(ReviewFilledTableError::Selection)?;
    if tables.next().is_some() {
        return Err(ReviewFilledTableError::Selection);
    }
    let mut cells = xml.elements().iter().enumerate().filter(|(i, e)| {
        named(e, "tc")
            && e.parent().and_then(|r| xml.elements()[r].parent()) == Some(table)
            && xml.elements().iter().any(|a| {
                a.parent() == Some(*i)
                    && named(a, "cellAddr")
                    && value(a, "rowAddr") == Some(row)
                    && value(a, "colAddr") == Some(column)
            })
    });
    let (index, _) = cells.next().ok_or(ReviewFilledTableError::Selection)?;
    if cells.next().is_some() {
        return Err(ReviewFilledTableError::Selection);
    }
    part.element_anchor(index)
        .cloned()
        .ok_or(ReviewFilledTableError::Selection)
}
fn value(e: &crate::XmlElementToken, name: &str) -> Option<u32> {
    e.attributes()
        .iter()
        .find(|a| a.name().namespace().is_none() && a.name().local_name() == name)
        .and_then(|a| a.semantic_value().parse().ok())
}
#[derive(Debug, Error)]
pub enum ReviewFilledTableError {
    #[error(transparent)]
    Creation(#[from] ReviewTableOutputError),
    #[error(transparent)]
    Cell(#[from] ReviewBodyOutputError),
    #[error("review_new_table_cell_contents_invalid_or_over_limit")]
    Values,
    #[error("review_new_table_created_cell_selection_rejected")]
    Selection,
    #[error("review_new_table_artifact_integrity_rejected")]
    Integrity,
}
