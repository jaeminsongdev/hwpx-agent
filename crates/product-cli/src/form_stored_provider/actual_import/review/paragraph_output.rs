//! Source-authenticated paragraph output; no atomic publication or native authority.
use super::StoredImportedReviewBodies;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    TextFlow, WriterLimits,
    document_import::structure::review::paragraph_output::{
        ReviewParagraphOutput, ReviewParagraphOutputReceipt,
    },
};
use revision_service::RevisionRepository;
use std::fmt;
use thiserror::Error;

/// Complete typed replacement intent; no raw XML, offsets or metadata defaults.
pub struct ReviewParagraphReplacement {
    pub marker: SourceAnchorHandle,
    pub paragraph: SourceAnchorHandle,
    pub content: TextFlow,
}
impl fmt::Debug for ReviewParagraphReplacement {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewParagraphReplacement(<redacted>)")
    }
}
pub struct PreparedStoredReviewParagraph<'a, 'source> {
    review: &'a StoredImportedReviewBodies<'source>,
    replacement: ReviewParagraphReplacement,
    limits: WriterLimits,
    output: ReviewParagraphOutput,
}
impl fmt::Debug for PreparedStoredReviewParagraph<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredReviewParagraph(<redacted>)")
    }
}
impl<'source> StoredImportedReviewBodies<'source> {
    /// Original fresh service checks surround typed one-paragraph lowering.
    /// # Errors
    /// Rejects original authorization/source drift or invalid output.
    pub fn prepare_paragraph<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        replacement: ReviewParagraphReplacement,
        limits: WriterLimits,
        now: u64,
    ) -> Result<PreparedStoredReviewParagraph<'a, 'source>, StoredReviewParagraphOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)
            .map_err(|_| StoredReviewParagraphOutputError::Source)?;
        let fresh = self
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewParagraphOutputError::Source)?;
        let output = self
            .imported
            .lower_paragraph(
                &fresh.bytes,
                &replacement.marker,
                &replacement.paragraph,
                &replacement.content,
                limits,
            )
            .map_err(|_| StoredReviewParagraphOutputError::Output)?;
        self.verify(provider, now)
            .map_err(|_| StoredReviewParagraphOutputError::Source)?;
        Ok(PreparedStoredReviewParagraph {
            review: self,
            replacement,
            limits,
            output,
        })
    }
}
impl PreparedStoredReviewParagraph<'_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewParagraphOutputReceipt {
        self.output.receipt()
    }
    /// Fresh source checks and complete deterministic output replay, not a held lease.
    /// # Errors
    /// Rejects original ACL/AEAD/head/scope/whole source or cached output drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<ReviewParagraphOutputReceipt, StoredReviewParagraphOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewParagraphOutputError::Source)?;
        let fresh = self
            .review
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewParagraphOutputError::Source)?;
        let output = self
            .review
            .imported
            .lower_paragraph(
                &fresh.bytes,
                &self.replacement.marker,
                &self.replacement.paragraph,
                &self.replacement.content,
                self.limits,
            )
            .map_err(|_| StoredReviewParagraphOutputError::Output)?;
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewParagraphOutputError::Source)?;
        if output.receipt() != self.output.receipt() {
            return Err(StoredReviewParagraphOutputError::Binding);
        }
        self.output
            .with_verified_bytes(|_| ())
            .map_err(|_| StoredReviewParagraphOutputError::Output)?;
        Ok(self.output.receipt().clone())
    }
    /// No callback after failed fresh authorization/output replay.
    /// # Errors
    /// Rejects source/output drift; bytes do not authorize publication.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, StoredReviewParagraphOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        self.output
            .with_verified_bytes(consume)
            .map_err(|_| StoredReviewParagraphOutputError::Output)
    }
    /// Full comment metadata/protection/compiler/issuer/atomic publication is unqualified.
    /// # Errors
    /// Always denies product execution after the original fresh checks.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredReviewParagraphOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(StoredReviewParagraphOutputError::RouteUnqualified)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredReviewParagraphOutputError {
    #[error("stored_review_paragraph_original_source_rejected")]
    Source,
    #[error("stored_review_paragraph_output_rejected")]
    Output,
    #[error("stored_review_paragraph_output_binding_rejected")]
    Binding,
    #[error("stored_review_paragraph_route_unqualified")]
    RouteUnqualified,
}
