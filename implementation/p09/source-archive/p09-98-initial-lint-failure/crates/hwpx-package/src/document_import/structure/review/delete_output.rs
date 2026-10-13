//! Existing observed review deletion; NOT native protection/state or execution authority.
use super::{ImportedDocumentReviewBodies, ReviewBodyKind};
use crate::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
    PatchIntent, PatchLimits, PreservationRuleProfile, PreservingPatchEngine, PreservingWriter,
    WriterError, WriterLimits, XmlByteSpan, XmlElementSelector,
    document_import::{
        ImportedSourcePackage, fields::ImportedDocumentFields, forms::ImportedDocumentForms,
    },
};
use domain_ir::SourceAnchorHandle;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{fmt, io::Cursor};
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewDeleteReceipt {
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub source_observations_sha256: [u8; 32],
    pub output_observations_sha256: [u8; 32],
    pub output_bytes: usize,
    pub kind: ReviewBodyKind,
    pub deleted_subtrees: usize,
    pub changed_parts: usize,
    pub outside_deleted_subtrees_exact: bool,
    pub native_author_time_state_verified: bool,
    pub protection_execution_publication_authority: bool,
}
pub struct ReviewDeleteOutput {
    artifact: PackageArtifact,
    receipt: ReviewDeleteReceipt,
}
impl fmt::Debug for ReviewDeleteOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewDeleteOutput(<redacted>)")
    }
}
impl ReviewDeleteOutput {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewDeleteReceipt {
        &self.receipt
    }
    /// Integrity only. A stored-source caller must separately recheck original access.
    /// # Errors
    /// Rejects original artifact integrity failure without invoking the callback.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}
impl ImportedDocumentReviewBodies<'_> {
    /// Remove an EXISTING observed hidden explanation, or both original MEMO ctrl wrappers.
    /// Does not remove the selected visible text, runs, paragraphs, style or author catalogs.
    /// No raw XML/offsets, caller metadata, input overwrite or P11 capability claim.
    /// # Errors
    /// Rejects stale/foreign source/selection, non-singleton wrappers, another review inside
    /// the deleted payload, original patch/writer failure or exact whole-part readback drift.
    pub fn lower_delete(
        &self,
        fresh: &[u8],
        marker: &SourceAnchorHandle,
        writer_limits: WriterLimits,
    ) -> Result<ReviewDeleteOutput, ReviewDeleteError> {
        self.verify_source(fresh)
            .map_err(|_| ReviewDeleteError::Source)?;
        let selected = self
            .observations
            .iter()
            .find(|o| &o.marker_anchor == marker)
            .ok_or(ReviewDeleteError::Selection)?;
        let source = self.forms.source();
        let first = deletion_target(source, marker, selected.kind == ReviewBodyKind::MemoField)?;
        let mut indices = vec![first.1];
        if selected.kind == ReviewBodyKind::MemoField {
            let end = deletion_target(
                source,
                selected
                    .end_anchor
                    .as_ref()
                    .ok_or(ReviewDeleteError::Selection)?,
                true,
            )?;
            if end.0 != first.0 {
                return Err(ReviewDeleteError::Selection);
            }
            indices.push(end.1);
        }
        let part = source
            .parts()
            .iter()
            .find(|p| p.path() == first.0)
            .ok_or(ReviewDeleteError::Selection)?;
        let xml = part.xml().ok_or(ReviewDeleteError::Selection)?;
        let mut spans: Vec<_> = indices
            .iter()
            .map(|i| {
                xml.elements()[*i]
                    .outer_span()
                    .ok_or(ReviewDeleteError::Selection)
            })
            .collect::<Result<_, _>>()?;
        spans.sort_by_key(|s| s.start());
        if spans.windows(2).any(|w| w[0].end() > w[1].start()) {
            return Err(ReviewDeleteError::Selection);
        }
        // Removing one body must not silently remove a second nested review.
        for observation in &self.observations {
            if observation.marker_anchor == *marker {
                continue;
            }
            let resolved = source
                .resolve_anchor(&observation.marker_anchor)
                .map_err(|_| ReviewDeleteError::Selection)?;
            let span = resolved
                .element()
                .and_then(crate::XmlElementToken::outer_span)
                .ok_or(ReviewDeleteError::Selection)?;
            if resolved.part().path() == part.path()
                && spans
                    .iter()
                    .any(|s| s.start() <= span.start() && span.end() <= s.end())
            {
                return Err(ReviewDeleteError::NestedReview);
            }
        }
        let intents = indices
            .into_iter()
            .map(|index| {
                Ok(PatchIntent::DeleteSubtree {
                    target: XmlElementSelector::bind(part.path(), xml, index)
                        .map_err(|_| ReviewDeleteError::Selection)?,
                })
            })
            .collect::<Result<Vec<_>, ReviewDeleteError>>()?;
        let limits = source.limits.zip().map_err(|_| ReviewDeleteError::Source)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), limits)
            .map_err(|_| ReviewDeleteError::Source)?;
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader,
            &source.graph,
            PackageGraphLimits::default(),
            IdRuleProfile::current_hancom_2020_formula_v3(),
            IdIndexLimits::default(),
            PatchLimits::default(),
            PreservationRuleProfile::Hangul2020PreviewTextV2,
            &intents,
        )
        .map_err(|_| ReviewDeleteError::Patch)?;
        if patch.changed_parts() != 1
            || patch.added_parts() != 0
            || patch
                .parts()
                .iter()
                .any(|p| p.path() != part.path() && p.source_sha256() != Some(p.output_sha256()))
        {
            return Err(ReviewDeleteError::Preservation);
        }
        let artifact = PreservingWriter::build(
            &patch,
            limits,
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            writer_limits,
        )
        .map_err(|_| ReviewDeleteError::Writer)?;
        let original_field_count = ImportedDocumentFields::import(self.forms)
            .map_err(|_| ReviewDeleteError::Source)?
            .fields()
            .len();
        let output_observations = artifact
            .with_verified_bytes(|bytes| {
                let forms = ImportedDocumentForms::import(
                    ImportedSourcePackage::import(
                        bytes,
                        source.document_id.clone(),
                        Sha256::digest(bytes).into(),
                        source.limits,
                    )
                    .map_err(|_| ReviewDeleteError::Readback)?,
                )
                .map_err(|_| ReviewDeleteError::Readback)?;
                let output_part = forms
                    .source()
                    .parts()
                    .iter()
                    .find(|p| p.path() == part.path())
                    .ok_or(ReviewDeleteError::Readback)?;
                let output_xml = output_part.xml().ok_or(ReviewDeleteError::Readback)?;
                let exact = xml.with_source_bytes(|old| {
                    output_xml.with_source_bytes(|new| outside_deleted_exact(old, &spans, new))
                });
                if !exact {
                    return Err(ReviewDeleteError::Preservation);
                }
                let fields = ImportedDocumentFields::import(&forms)
                    .map_err(|_| ReviewDeleteError::Readback)?;
                let expected_fields = original_field_count
                    .checked_sub(usize::from(selected.kind == ReviewBodyKind::MemoField))
                    .ok_or(ReviewDeleteError::Readback)?;
                if fields.fields().len() != expected_fields {
                    return Err(ReviewDeleteError::Readback);
                }
                let output = ImportedDocumentReviewBodies::import(&forms)
                    .map_err(|_| ReviewDeleteError::Readback)?;
                if output.observations.len() + 1 != self.observations.len()
                    || output.receipt.memo_fields
                        + usize::from(selected.kind == ReviewBodyKind::MemoField)
                        != self.receipt.memo_fields
                    || output.receipt.hidden_explanations
                        + usize::from(selected.kind == ReviewBodyKind::HiddenExplanation)
                        != self.receipt.hidden_explanations
                {
                    return Err(ReviewDeleteError::Readback);
                }
                Ok(output.receipt.body_observations_sha256)
            })
            .map_err(|_| ReviewDeleteError::Writer)??;
        self.verify_source(fresh)
            .map_err(|_| ReviewDeleteError::Source)?;
        Ok(ReviewDeleteOutput {
            receipt: ReviewDeleteReceipt {
                qualification: "existing_observed_review_structural_deletion_NOT_full_native_state_protection_compiler_execution_publication_P11_or_Gate",
                source_package_sha256: self.receipt.source_package_sha256,
                output_package_sha256: artifact.sha256(),
                source_observations_sha256: self.receipt.body_observations_sha256,
                output_observations_sha256: output_observations,
                output_bytes: artifact.size_bytes(),
                kind: selected.kind,
                deleted_subtrees: spans.len(),
                changed_parts: 1,
                outside_deleted_subtrees_exact: true,
                native_author_time_state_verified: false,
                protection_execution_publication_authority: false,
            },
            artifact,
        })
    }
}
fn deletion_target<'a>(
    source: &'a ImportedSourcePackage,
    anchor: &SourceAnchorHandle,
    require_ctrl: bool,
) -> Result<(&'a crate::PackagePath, usize), ReviewDeleteError> {
    let resolved = source
        .resolve_anchor(anchor)
        .map_err(|_| ReviewDeleteError::Selection)?;
    let index = resolved
        .element_index()
        .ok_or(ReviewDeleteError::Selection)?;
    let xml = resolved.part().xml().ok_or(ReviewDeleteError::Selection)?;
    let parent = xml.elements()[index]
        .parent()
        .ok_or(ReviewDeleteError::Selection)?;
    let owner = &xml.elements()[parent];
    let target = if super::named(owner, "ctrl") {
        if owner.first_child() != Some(index) || xml.elements()[index].next_sibling().is_some() {
            return Err(ReviewDeleteError::Selection);
        }
        parent
    } else if !require_ctrl && super::named(owner, "run") {
        index
    } else {
        return Err(ReviewDeleteError::Selection);
    };
    Ok((resolved.part().path(), target))
}
fn outside_deleted_exact(old: &[u8], spans: &[XmlByteSpan], new: &[u8]) -> bool {
    let mut old_offset = 0;
    let mut new_offset = 0_usize;
    for span in spans {
        let size = span.start() - old_offset;
        let Some(end) = new_offset.checked_add(size) else {
            return false;
        };
        if new.get(new_offset..end) != Some(&old[old_offset..span.start()]) {
            return false;
        }
        old_offset = span.end();
        new_offset = end;
    }
    new.get(new_offset..) == Some(&old[old_offset..])
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum ReviewDeleteError {
    #[error("review_delete_source_rejected")]
    Source,
    #[error("review_delete_selection_rejected")]
    Selection,
    #[error("review_delete_nested_review_rejected")]
    NestedReview,
    #[error("review_delete_original_patch_rejected")]
    Patch,
    #[error("review_delete_original_writer_rejected")]
    Writer,
    #[error("review_delete_original_readback_rejected")]
    Readback,
    #[error("review_delete_preservation_rejected")]
    Preservation,
}
