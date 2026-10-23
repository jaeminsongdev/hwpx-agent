//! Complete replacement of ONE actual review paragraph; rich siblings stay exact.
use super::{
    ImportedDocumentReviewBodies,
    body_output::{
        ReviewBodyOutput, ReviewBodyOutputError, ReviewBodyOutputReceipt, ReviewBodyTarget,
    },
    cell_body_output::{descendant_path, named, require_no_observed_protection},
};
use crate::{TextFlow, WriterError, WriterLimits};
use domain_ir::SourceAnchorHandle;
use serde::Serialize;
use std::fmt;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewParagraphOutputReceipt {
    pub qualification: &'static str,
    pub output: ReviewBodyOutputReceipt,
    pub source_paragraph: SourceAnchorHandle,
    pub outside_selected_paragraph_exact: bool,
    pub rich_siblings_preserved_exact: bool,
    pub full_comment_product_acceptance: bool,
}
pub struct ReviewParagraphOutput {
    output: ReviewBodyOutput,
    receipt: ReviewParagraphOutputReceipt,
}
impl fmt::Debug for ReviewParagraphOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewParagraphOutput(<redacted>)")
    }
}
impl ReviewParagraphOutput {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewParagraphOutputReceipt {
        &self.receipt
    }
    /// Original package integrity only, not stored access or execution authority.
    /// # Errors
    /// Rejects original artifact verification failure before exposing bytes.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.output.with_verified_bytes(consume)
    }
}
impl ImportedDocumentReviewBodies<'_> {
    /// Replace one complete typed paragraph selected from the ACTUAL review source.
    /// Selection never uses caller XML, positions or a guessed native numeric identity.
    /// This is complete replacement inside the selected paragraph, not preservation of
    /// its old contents. Every sibling, marker and other part stays byte-exact.
    /// # Errors
    /// Rejects drift, foreign/main/other-review/non-paragraph selection, observed ancestor
    /// protection, unsupported target content, no-op and original patch/writer/readback failure.
    pub fn lower_paragraph(
        &self,
        fresh: &[u8],
        marker: &SourceAnchorHandle,
        paragraph: &SourceAnchorHandle,
        content: &TextFlow,
        limits: WriterLimits,
    ) -> Result<ReviewParagraphOutput, ReviewBodyOutputError> {
        self.verify_source(fresh)
            .map_err(|_| ReviewBodyOutputError::Source)?;
        let observation = self
            .observations
            .iter()
            .find(|o| &o.marker_anchor == marker)
            .ok_or(ReviewBodyOutputError::Selection)?;
        let source = self.forms.source();
        let body_anchor = observation
            .body_anchor
            .as_ref()
            .ok_or(ReviewBodyOutputError::Selection)?;
        let body = source
            .resolve_anchor(body_anchor)
            .map_err(|_| ReviewBodyOutputError::Selection)?;
        let selected = source
            .resolve_anchor(paragraph)
            .map_err(|_| ReviewBodyOutputError::Selection)?;
        if body.part().path() != selected.part().path() {
            return Err(ReviewBodyOutputError::Selection);
        }
        let xml = body.part().xml().ok_or(ReviewBodyOutputError::Selection)?;
        let body_index = body
            .element_index()
            .ok_or(ReviewBodyOutputError::Selection)?;
        let index = selected
            .element_index()
            .ok_or(ReviewBodyOutputError::Selection)?;
        let node = &xml.elements()[index];
        if !named(node, "p")
            || node
                .parent()
                .is_none_or(|parent| !named(&xml.elements()[parent], "subList"))
        {
            return Err(ReviewBodyOutputError::Selection);
        }
        let path = descendant_path(xml, body_index, index)?;
        // An outer review does not own a paragraph inside another observed review body.
        for other in &self.observations {
            let Some(anchor) = &other.body_anchor else {
                continue;
            };
            if anchor == body_anchor {
                continue;
            }
            let resolved = source
                .resolve_anchor(anchor)
                .map_err(|_| ReviewBodyOutputError::Selection)?;
            if resolved.part().path() == body.part().path() {
                let other_index = resolved
                    .element_index()
                    .ok_or(ReviewBodyOutputError::Selection)?;
                let mut ancestor = node.parent();
                while let Some(current) = ancestor {
                    if current == body_index {
                        break;
                    }
                    if current == other_index {
                        return Err(ReviewBodyOutputError::Selection);
                    }
                    ancestor = xml.elements()[current].parent();
                }
            }
        }
        require_no_observed_protection(xml, body_index, index)?;
        let output = self.lower_body_target(
            fresh,
            marker,
            &path,
            std::slice::from_ref(content),
            limits,
            ReviewBodyTarget::Paragraph,
        )?;
        Ok(ReviewParagraphOutput {
            receipt: ReviewParagraphOutputReceipt {
                qualification: "one_actual_review_paragraph_complete_replacement_rich_siblings_exact_NOT_new_rich_objects_native_comment_state_protection_execution_or_Gate",
                output: output.receipt().clone(),
                source_paragraph: paragraph.clone(),
                outside_selected_paragraph_exact: true,
                rich_siblings_preserved_exact: true,
                full_comment_product_acceptance: false,
            },
            output,
        })
    }
}
