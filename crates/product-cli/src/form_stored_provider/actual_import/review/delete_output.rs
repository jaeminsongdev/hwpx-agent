//! Existing original source-backed deletion; no full comment/atomic publication route.
use super::StoredImportedReviewBodies;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    WriterLimits,
    document_import::structure::review::delete_output::{ReviewDeleteOutput, ReviewDeleteReceipt},
};
use revision_service::RevisionRepository;
use std::fmt;
use thiserror::Error;

pub struct PreparedStoredReviewDelete<'a, 'source> {
    review: &'a StoredImportedReviewBodies<'source>,
    marker: SourceAnchorHandle,
    limits: WriterLimits,
    output: ReviewDeleteOutput,
}
impl fmt::Debug for PreparedStoredReviewDelete<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredReviewDelete(<redacted>)")
    }
}
impl<'source> StoredImportedReviewBodies<'source> {
    /// Original fresh service/source checks around paired original review deletion.
    /// No new ingest/revision, caller XML, metadata defaults or native execution.
    /// # Errors
    /// Rejects original service/source/whole review drift or deletion lowering failures.
    pub fn prepare_delete<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        marker: SourceAnchorHandle,
        limits: WriterLimits,
        now: u64,
    ) -> Result<PreparedStoredReviewDelete<'a, 'source>, StoredReviewDeleteError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)
            .map_err(|_| StoredReviewDeleteError::Source)?;
        let fresh = self
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewDeleteError::Source)?;
        let output = self
            .imported
            .lower_delete(&fresh.bytes, &marker, limits)
            .map_err(|_| StoredReviewDeleteError::Output)?;
        self.verify(provider, now)
            .map_err(|_| StoredReviewDeleteError::Source)?;
        Ok(PreparedStoredReviewDelete {
            review: self,
            marker,
            limits,
            output,
        })
    }
}
impl PreparedStoredReviewDelete<'_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewDeleteReceipt {
        self.output.receipt()
    }
    /// Replays original source authorization, paired deletion output and full artifact verification.
    /// Repeated reads are not a held atomic execution lease.
    /// # Errors
    /// Rejects original access/AEAD/head/scope/source or cached output drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<ReviewDeleteReceipt, StoredReviewDeleteError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewDeleteError::Source)?;
        let fresh = self
            .review
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewDeleteError::Source)?;
        let output = self
            .review
            .imported
            .lower_delete(&fresh.bytes, &self.marker, self.limits)
            .map_err(|_| StoredReviewDeleteError::Output)?;
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewDeleteError::Source)?;
        if output.receipt() != self.output.receipt() {
            return Err(StoredReviewDeleteError::Binding);
        }
        self.output
            .with_verified_bytes(|_| ())
            .map_err(|_| StoredReviewDeleteError::Output)?;
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
    ) -> Result<T, StoredReviewDeleteError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        self.output
            .with_verified_bytes(consume)
            .map_err(|_| StoredReviewDeleteError::Output)
    }
    /// Full comment metadata/protection/compiler/issuer/atomic publication remains unqualified.
    /// # Errors
    /// Always denies the product route after the original fresh checks.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredReviewDeleteError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(StoredReviewDeleteError::RouteUnqualified)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredReviewDeleteError {
    #[error("stored_review_delete_original_source_rejected")]
    Source,
    #[error("stored_review_delete_output_rejected")]
    Output,
    #[error("stored_review_delete_output_binding_rejected")]
    Binding,
    #[error("stored_review_delete_output_route_unqualified")]
    RouteUnqualified,
}
