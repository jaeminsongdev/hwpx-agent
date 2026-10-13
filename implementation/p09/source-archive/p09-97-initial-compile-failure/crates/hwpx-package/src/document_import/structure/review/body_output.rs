//! Complete typed paragraph content for an EXISTING observed review body.
//! Source metadata, coordinates, protection and full comment execution remain unqualified.
use super::{ImportedDocumentReviewBodies, MAX_BYTES, ReviewBodyImportReceipt, ReviewBodyKind};
use crate::{
    BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
    PatchIntent, PatchLimits, PreservationRuleProfile, PreservingPatchEngine, PreservingWriter,
    PreservingXmlDocument, TextFlow, TextFlowLimits, TextFlowReader, TextFlowWriter,
    ValidatedXmlFragment, WriterError, WriterLimits, XmlElementSelector,
    document_import::{ImportedSourcePackage, forms::ImportedDocumentForms},
};
use domain_ir::SourceAnchorHandle;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{fmt, io::Cursor};
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewBodyOutputReceipt {
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub output_package_sha256: [u8; 32],
    pub source_observations_sha256: [u8; 32],
    pub output_observations_sha256: [u8; 32],
    pub output_bytes: usize,
    pub kind: ReviewBodyKind,
    pub target_paragraphs: usize,
    pub changed_parts: usize,
    pub outside_selected_content_exact: bool,
    pub native_author_time_state_verified: bool,
    pub execution_publication_authority: bool,
}
pub struct ReviewBodyOutput {
    artifact: PackageArtifact,
    receipt: ReviewBodyOutputReceipt,
}
impl fmt::Debug for ReviewBodyOutput {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewBodyOutput(<redacted>)")
    }
}
impl ReviewBodyOutput {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewBodyOutputReceipt {
        &self.receipt
    }
    /// Artifact integrity only; stored source callers must also recheck their original access.
    /// # Errors
    /// Does not expose bytes after original package writer verification failure.
    pub fn with_verified_bytes<T>(
        &self,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, WriterError> {
        self.artifact.with_verified_bytes(consume)
    }
}

impl ImportedDocumentReviewBodies<'_> {
    /// Replace all paragraphs inside one ACTUAL existing MEMO/hiddenComment body.
    /// Original wrapper, parameters, metadata, paired markers and every other byte stay exact.
    /// This does not insert a comment, fabricate native values or authorize execution.
    /// # Errors
    /// Rejects stale source/marker, missing body, no-op, unsafe/opaque/oversized target,
    /// original patch/ID/writer failure or complete original body readback mismatch.
    pub fn lower_body(
        &self,
        fresh: &[u8],
        marker: &SourceAnchorHandle,
        paragraphs: &[TextFlow],
        writer_limits: WriterLimits,
    ) -> Result<ReviewBodyOutput, ReviewBodyOutputError> {
        self.verify_source(fresh)
            .map_err(|_| ReviewBodyOutputError::Source)?;
        let ordinal = self
            .observations
            .iter()
            .position(|o| &o.marker_anchor == marker)
            .ok_or(ReviewBodyOutputError::Selection)?;
        let observation = &self.observations[ordinal];
        let source = self.forms.source();
        let body = source
            .resolve_anchor(
                observation
                    .body_anchor
                    .as_ref()
                    .ok_or(ReviewBodyOutputError::Selection)?,
            )
            .map_err(|_| ReviewBodyOutputError::Selection)?;
        let xml = body.part().xml().ok_or(ReviewBodyOutputError::Selection)?;
        let index = body
            .element_index()
            .ok_or(ReviewBodyOutputError::Selection)?;
        let content = body
            .element()
            .and_then(crate::XmlElementToken::content_span)
            .ok_or(ReviewBodyOutputError::Selection)?;
        if read_paragraphs(xml, index)? == paragraphs {
            return Err(ReviewBodyOutputError::NoChange);
        }
        let children = lower_paragraphs(paragraphs)?;
        let intent = PatchIntent::ReplaceElementContent {
            target: XmlElementSelector::bind(body.part().path(), xml, index)
                .map_err(|_| ReviewBodyOutputError::Selection)?,
            children,
        };
        let limits = source
            .limits
            .zip()
            .map_err(|_| ReviewBodyOutputError::Source)?;
        let mut reader = BoundedZipReader::open(Cursor::new(fresh), limits)
            .map_err(|_| ReviewBodyOutputError::Source)?;
        let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(
            &mut reader,
            &source.graph,
            PackageGraphLimits::default(),
            IdRuleProfile::current_hancom_2020_formula_v3(),
            IdIndexLimits::default(),
            PatchLimits::default(),
            PreservationRuleProfile::Hangul2020PreviewTextV2,
            &[intent],
        )
        .map_err(|_| ReviewBodyOutputError::Patch)?;
        if patch.changed_parts() != 1
            || patch.added_parts() != 0
            || patch.parts().iter().any(|p| {
                p.path() != body.part().path() && p.source_sha256() != Some(p.output_sha256())
            })
        {
            return Err(ReviewBodyOutputError::Preservation);
        }
        let artifact = PreservingWriter::build(
            &patch,
            limits,
            PackageGraphLimits::default(),
            IdIndexLimits::default(),
            writer_limits,
        )
        .map_err(|_| ReviewBodyOutputError::Writer)?;
        let original_part = xml.with_source_bytes(<[u8]>::to_vec);
        let output_receipt = artifact
            .with_verified_bytes(|bytes| {
                let forms = reimport(source, bytes)?;
                let result = ImportedDocumentReviewBodies::import(&forms)
                    .map_err(|_| ReviewBodyOutputError::Readback)?;
                let after = result
                    .observations
                    .get(ordinal)
                    .ok_or(ReviewBodyOutputError::Readback)?;
                if result.observations.len() != self.observations.len()
                    || after.kind != observation.kind
                    || after.native_attributes != observation.native_attributes
                    || after.body_attributes != observation.body_attributes
                {
                    return Err(ReviewBodyOutputError::Readback);
                }
                let resolved = forms
                    .source()
                    .resolve_anchor(
                        after
                            .body_anchor
                            .as_ref()
                            .ok_or(ReviewBodyOutputError::Readback)?,
                    )
                    .map_err(|_| ReviewBodyOutputError::Readback)?;
                let output_xml = resolved
                    .part()
                    .xml()
                    .ok_or(ReviewBodyOutputError::Readback)?;
                let output_index = resolved
                    .element_index()
                    .ok_or(ReviewBodyOutputError::Readback)?;
                if read_paragraphs(output_xml, output_index)? != paragraphs {
                    return Err(ReviewBodyOutputError::Readback);
                }
                check_outside(&original_part, content, output_xml, output_index)?;
                Ok(result.receipt.clone())
            })
            .map_err(|_| ReviewBodyOutputError::Writer)??;
        self.verify_source(fresh)
            .map_err(|_| ReviewBodyOutputError::Source)?;
        Ok(ReviewBodyOutput {
            receipt: output_receipt_for(
                self.receipt(),
                &output_receipt,
                &artifact,
                observation.kind,
                paragraphs.len(),
            ),
            artifact,
        })
    }
}
fn read_paragraphs(
    xml: &PreservingXmlDocument,
    body: usize,
) -> Result<Vec<TextFlow>, ReviewBodyOutputError> {
    let mut result = Vec::new();
    let mut next = xml.elements()[body].first_child();
    while let Some(index) = next {
        result.push(
            TextFlowReader::read_preserving_source(xml, index, TextFlowLimits::default())
                .map_err(|_| ReviewBodyOutputError::Readback)?,
        );
        next = xml.elements()[index].next_sibling();
    }
    Ok(result)
}
fn lower_paragraphs(
    paragraphs: &[TextFlow],
) -> Result<Vec<ValidatedXmlFragment>, ReviewBodyOutputError> {
    if paragraphs.is_empty() || paragraphs.len() > PatchLimits::default().config().max_intents {
        return Err(ReviewBodyOutputError::Values);
    }
    let mut result = Vec::new();
    let mut size = 0_usize;
    for paragraph in paragraphs {
        let bytes = TextFlowWriter::lower(paragraph, TextFlowLimits::default())
            .map_err(|_| ReviewBodyOutputError::Values)?;
        let xml =
            PreservingXmlDocument::parse(&bytes).map_err(|_| ReviewBodyOutputError::Values)?;
        let span = xml.elements()[xml.root_element()]
            .outer_span()
            .ok_or(ReviewBodyOutputError::Values)?;
        size = size
            .checked_add(span.len())
            .ok_or(ReviewBodyOutputError::Values)?;
        if size > MAX_BYTES {
            return Err(ReviewBodyOutputError::Values);
        }
        result.push(
            ValidatedXmlFragment::parse(&bytes[span.start()..span.end()], PatchLimits::default())
                .map_err(|_| ReviewBodyOutputError::Values)?,
        );
    }
    Ok(result)
}
fn reimport(
    source: &ImportedSourcePackage,
    bytes: &[u8],
) -> Result<ImportedDocumentForms, ReviewBodyOutputError> {
    ImportedDocumentForms::import(
        ImportedSourcePackage::import(
            bytes,
            source.document_id.clone(),
            Sha256::digest(bytes).into(),
            source.limits,
        )
        .map_err(|_| ReviewBodyOutputError::Readback)?,
    )
    .map_err(|_| ReviewBodyOutputError::Readback)
}
fn check_outside(
    original: &[u8],
    old: crate::XmlByteSpan,
    xml: &PreservingXmlDocument,
    index: usize,
) -> Result<(), ReviewBodyOutputError> {
    let new = xml.elements()[index]
        .content_span()
        .ok_or(ReviewBodyOutputError::Readback)?;
    if !xml.with_source_bytes(|bytes| {
        original[..old.start()] == bytes[..new.start()]
            && original[old.end()..] == bytes[new.end()..]
    }) {
        return Err(ReviewBodyOutputError::Preservation);
    }
    Ok(())
}
fn output_receipt_for(
    source: &ReviewBodyImportReceipt,
    output: &ReviewBodyImportReceipt,
    artifact: &PackageArtifact,
    kind: ReviewBodyKind,
    paragraphs: usize,
) -> ReviewBodyOutputReceipt {
    ReviewBodyOutputReceipt {
        qualification: "existing_observed_review_body_paragraph_output_NOT_comment_metadata_state_policy_compiler_native_execution_publication_or_Gate",
        source_package_sha256: source.source_package_sha256,
        output_package_sha256: artifact.sha256(),
        source_observations_sha256: source.body_observations_sha256,
        output_observations_sha256: output.body_observations_sha256,
        output_bytes: artifact.size_bytes(),
        kind,
        target_paragraphs: paragraphs,
        changed_parts: 1,
        outside_selected_content_exact: true,
        native_author_time_state_verified: false,
        execution_publication_authority: false,
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum ReviewBodyOutputError {
    #[error("review_body_output_source_rejected")]
    Source,
    #[error("review_body_output_selection_rejected")]
    Selection,
    #[error("review_body_output_values_rejected")]
    Values,
    #[error("review_body_output_no_change")]
    NoChange,
    #[error("review_body_output_original_patch_rejected")]
    Patch,
    #[error("review_body_output_original_writer_rejected")]
    Writer,
    #[error("review_body_output_original_readback_rejected")]
    Readback,
    #[error("review_body_output_preservation_rejected")]
    Preservation,
}
