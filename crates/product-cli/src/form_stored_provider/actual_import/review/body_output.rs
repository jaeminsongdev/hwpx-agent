//! Existing original source-backed body output; no full comment/atomic publication route.
use super::StoredImportedReviewBodies;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    TextFlow, WriterLimits,
    document_import::structure::review::body_output::{ReviewBodyOutput, ReviewBodyOutputReceipt},
};
use revision_service::RevisionRepository;
use std::fmt;
use thiserror::Error;

pub struct PreparedStoredReviewBody<'a, 'source> {
    review: &'a StoredImportedReviewBodies<'source>,
    marker: SourceAnchorHandle,
    paragraphs: Vec<TextFlow>,
    limits: WriterLimits,
    output: ReviewBodyOutput,
}
impl fmt::Debug for PreparedStoredReviewBody<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredReviewBody(<redacted>)")
    }
}
impl<'source> StoredImportedReviewBodies<'source> {
    /// Original fresh service/source checks around complete typed existing-body output.
    /// No new ingest/revision, caller XML, metadata defaults or native execution.
    /// # Errors
    /// Rejects original service/source/whole review drift or body lowering failures.
    pub fn prepare_body<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        marker: SourceAnchorHandle,
        paragraphs: Vec<TextFlow>,
        limits: WriterLimits,
        now: u64,
    ) -> Result<PreparedStoredReviewBody<'a, 'source>, StoredReviewBodyOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)
            .map_err(|_| StoredReviewBodyOutputError::Source)?;
        let fresh = self
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewBodyOutputError::Source)?;
        let output = self
            .imported
            .lower_body(&fresh.bytes, &marker, &paragraphs, limits)
            .map_err(|_| StoredReviewBodyOutputError::Output)?;
        self.verify(provider, now)
            .map_err(|_| StoredReviewBodyOutputError::Source)?;
        Ok(PreparedStoredReviewBody {
            review: self,
            marker,
            paragraphs,
            limits,
            output,
        })
    }
}
impl PreparedStoredReviewBody<'_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewBodyOutputReceipt {
        self.output.receipt()
    }
    /// Replays original source authorization, complete body output and full artifact verification.
    /// Repeated reads are not a held atomic execution lease.
    /// # Errors
    /// Rejects original access/AEAD/head/scope/source or cached output drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<ReviewBodyOutputReceipt, StoredReviewBodyOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewBodyOutputError::Source)?;
        let fresh = self
            .review
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewBodyOutputError::Source)?;
        let output = self
            .review
            .imported
            .lower_body(&fresh.bytes, &self.marker, &self.paragraphs, self.limits)
            .map_err(|_| StoredReviewBodyOutputError::Output)?;
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewBodyOutputError::Source)?;
        if output.receipt() != self.output.receipt() {
            return Err(StoredReviewBodyOutputError::Binding);
        }
        self.output
            .with_verified_bytes(|_| ())
            .map_err(|_| StoredReviewBodyOutputError::Output)?;
        Ok(self.output.receipt().clone())
    }
    /// Never invokes the callback after failed fresh stored-source/output verification.
    /// # Errors
    /// Rejects source or output drift; successful bytes still do not authorize publication.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, StoredReviewBodyOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        self.output
            .with_verified_bytes(consume)
            .map_err(|_| StoredReviewBodyOutputError::Output)
    }
    /// Full comment metadata/protection/compiler/issuer/atomic publication remains unqualified.
    /// # Errors
    /// Always denies the product route after the original fresh checks.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredReviewBodyOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(StoredReviewBodyOutputError::RouteUnqualified)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredReviewBodyOutputError {
    #[error("stored_review_body_original_source_rejected")]
    Source,
    #[error("stored_review_body_output_rejected")]
    Output,
    #[error("stored_review_body_output_binding_rejected")]
    Binding,
    #[error("stored_review_body_output_route_unqualified")]
    RouteUnqualified,
}
