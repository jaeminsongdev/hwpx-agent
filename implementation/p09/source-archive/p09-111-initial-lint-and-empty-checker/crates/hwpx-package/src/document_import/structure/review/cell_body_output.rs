//! Typed paragraph editing inside an ACTUAL observed review table cell.
//! Original rich structure stays exact; this is not table insertion or comment authority.
use super::{
    ImportedDocumentReviewBodies,
    body_output::{ReviewBodyOutput, ReviewBodyOutputError, ReviewBodyOutputReceipt},
};
use crate::{PreservingXmlDocument, TextFlow, WriterError, WriterLimits};
use domain_ir::SourceAnchorHandle;
use serde::Serialize;
use std::fmt;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewCellBodyOutputReceipt {
    pub qualification: &'static str,
    pub output: ReviewBodyOutputReceipt,
    pub source_cell: SourceAnchorHandle,
    pub containing_table_geometry_and_other_cells_exact: bool,
    pub new_table_inserted: bool,
    pub full_comment_product_acceptance: bool,
}
pub struct ReviewCellBodyOutput {
    output: ReviewBodyOutput,
    receipt: ReviewCellBodyOutputReceipt,
}
impl fmt::Debug for ReviewCellBodyOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewCellBodyOutput(<redacted>)")
    }
}
impl ReviewCellBodyOutput {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewCellBodyOutputReceipt {
        &self.receipt
    }
    /// Original package integrity only, not access, execution or publication authority.
    /// # Errors
    /// Rejects original artifact verification failure before exposing any bytes.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.output.with_verified_bytes(consume)
    }
}
impl ImportedDocumentReviewBodies<'_> {
    /// Replaces typed paragraphs in one actual table cell under the selected review body.
    /// Selection is a source anchor, never caller XML, offsets or a guessed native numeric ID.
    /// Table geometry/style, other cells, main document, metadata and paired markers stay exact.
    /// # Errors
    /// Rejects stale/foreign/non-cell/outside-body selection, unsafe values or original output failure.
    pub fn lower_table_cell_body(
        &self,
        fresh: &[u8],
        marker: &SourceAnchorHandle,
        cell: &SourceAnchorHandle,
        paragraphs: &[TextFlow],
        limits: WriterLimits,
    ) -> Result<ReviewCellBodyOutput, ReviewBodyOutputError> {
        self.verify_source(fresh)
            .map_err(|_| ReviewBodyOutputError::Source)?;
        let observation = self
            .observations
            .iter()
            .find(|o| &o.marker_anchor == marker)
            .ok_or(ReviewBodyOutputError::Selection)?;
        let source = self.forms.source();
        let body = source
            .resolve_anchor(
                observation
                    .body_anchor
                    .as_ref()
                    .ok_or(ReviewBodyOutputError::Selection)?,
            )
            .map_err(|_| ReviewBodyOutputError::Selection)?;
        let selected = source
            .resolve_anchor(cell)
            .map_err(|_| ReviewBodyOutputError::Selection)?;
        if selected.part().path() != body.part().path() {
            return Err(ReviewBodyOutputError::Selection);
        }
        let xml = body.part().xml().ok_or(ReviewBodyOutputError::Selection)?;
        let body_index = body
            .element_index()
            .ok_or(ReviewBodyOutputError::Selection)?;
        let cell_index = selected
            .element_index()
            .ok_or(ReviewBodyOutputError::Selection)?;
        let node = &xml.elements()[cell_index];
        let row = node.parent().ok_or(ReviewBodyOutputError::Selection)?;
        let table = xml.elements()[row]
            .parent()
            .ok_or(ReviewBodyOutputError::Selection)?;
        if !named(node, "tc")
            || !named(&xml.elements()[row], "tr")
            || !named(&xml.elements()[table], "tbl")
        {
            return Err(ReviewBodyOutputError::Selection);
        }
        let mut content = None;
        let mut next = node.first_child();
        while let Some(index) = next {
            if named(&xml.elements()[index], "subList") && content.replace(index).is_some() {
                return Err(ReviewBodyOutputError::Selection);
            }
            next = xml.elements()[index].next_sibling();
        }
        let path = descendant_path(
            xml,
            body_index,
            content.ok_or(ReviewBodyOutputError::Selection)?,
        )?;
        require_no_observed_protection(xml, body_index, cell_index)?;
        let output = self.lower_body_content(fresh, marker, &path, paragraphs, limits)?;
        Ok(ReviewCellBodyOutput {
            receipt: ReviewCellBodyOutputReceipt {
                qualification: "existing_observed_review_table_cell_paragraph_output_NOT_new_table_full_rich_Flow_native_comment_state_execution_or_Gate",
                output: output.receipt().clone(),
                source_cell: cell.clone(),
                containing_table_geometry_and_other_cells_exact: true,
                new_table_inserted: false,
                full_comment_product_acceptance: false,
            },
            output,
        })
    }
}
pub(super) fn require_no_observed_protection(
    xml: &PreservingXmlDocument,
    body: usize,
    mut index: usize,
) -> Result<(), ReviewBodyOutputError> {
    // Missing flags remain unknown; zero flags do NOT prove complete product protection.
    // Do not bypass outer cell/table flags when editing a nested table cell either.
    while index != body {
        let node = &xml.elements()[index];
        if named(node, "tc") {
            reject_observed_flag(node, "protect")?;
        }
        if named(node, "tbl") {
            reject_observed_flag(node, "lock")?;
            let mut next = node.first_child();
            while let Some(child) = next {
                if named(&xml.elements()[child], "sz") {
                    reject_observed_flag(&xml.elements()[child], "protect")?;
                }
                next = xml.elements()[child].next_sibling();
            }
        }
        index = node.parent().ok_or(ReviewBodyOutputError::Selection)?;
    }
    // A review boundary must not hide protection on its containing MAIN table/cell.
    // Keep the original selected-to-body ancestry check above, then scan body-to-root.
    if body != xml.root_element() {
        require_no_observed_protection(xml, xml.root_element(), body)?;
    }
    Ok(())
}
fn reject_observed_flag(
    node: &crate::XmlElementToken,
    name: &str,
) -> Result<(), ReviewBodyOutputError> {
    if node.attributes().iter().any(|a| {
        !a.is_namespace_declaration()
            && a.name().namespace().is_none()
            && a.name().local_name() == name
            && !matches!(a.semantic_value(), "0" | "false")
    }) {
        return Err(ReviewBodyOutputError::Selection);
    }
    Ok(())
}
pub(super) fn require_no_observed_subtree_protection(
    xml: &PreservingXmlDocument,
    index: usize,
) -> Result<(), ReviewBodyOutputError> {
    // Replacing or deleting a container must not erase protected descendants.
    // Source-derived spans only; no caller offsets or guessed protection meanings.
    let selected = xml
        .elements()
        .get(index)
        .and_then(crate::XmlElementToken::outer_span)
        .ok_or(ReviewBodyOutputError::Selection)?;
    for node in xml.elements() {
        let Some(span) = node.outer_span() else {
            return Err(ReviewBodyOutputError::Selection);
        };
        if span.start() < selected.start() || span.end() > selected.end() {
            continue;
        }
        if named(node, "tc")
            || (named(node, "sz")
                && node.parent().is_some_and(|parent| named(&xml.elements()[parent], "tbl")))
        {
            reject_observed_flag(node, "protect")?;
        }
        if named(node, "tbl") {
            reject_observed_flag(node, "lock")?;
        }
    }
    Ok(())
}
pub(super) fn named(node: &crate::XmlElementToken, local: &str) -> bool {
    node.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
        && node.name().local_name() == local
}
pub(super) fn descendant_path(
    xml: &PreservingXmlDocument,
    ancestor: usize,
    mut index: usize,
) -> Result<Vec<usize>, ReviewBodyOutputError> {
    let mut path = Vec::new();
    while index != ancestor {
        let parent = xml.elements()[index]
            .parent()
            .ok_or(ReviewBodyOutputError::Selection)?;
        let mut sibling = xml.elements()[parent].first_child();
        let mut ordinal = 0;
        while sibling != Some(index) {
            sibling = sibling.and_then(|i| xml.elements()[i].next_sibling());
            if sibling.is_none() {
                return Err(ReviewBodyOutputError::Selection);
            }
            ordinal += 1;
        }
        path.push(ordinal);
        index = parent;
    }
    path.reverse();
    Ok(path)
}
