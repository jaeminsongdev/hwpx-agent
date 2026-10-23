//! Existing original source-backed body output; no full comment/atomic publication route.
use super::StoredImportedReviewBodies;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    TextFlow, WriterLimits,
    document_import::structure::review::cell_body_output::{
        ReviewCellBodyOutput, ReviewCellBodyOutputReceipt,
    },
};
use revision_service::RevisionRepository;
use std::fmt;
use thiserror::Error;

pub struct PreparedStoredReviewCellBody<'a, 'source> {
    review: &'a StoredImportedReviewBodies<'source>,
    marker: SourceAnchorHandle,
    cell: SourceAnchorHandle,
    paragraphs: Vec<TextFlow>,
    limits: WriterLimits,
    output: ReviewCellBodyOutput,
}
impl fmt::Debug for PreparedStoredReviewCellBody<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredReviewCellBody(<redacted>)")
    }
}
impl<'source> StoredImportedReviewBodies<'source> {
    /// Original fresh service/source checks around complete typed existing-cell output.
    /// No new ingest/revision, caller XML, metadata defaults or native execution.
    /// # Errors
    /// Rejects original service/source/whole review drift or body lowering failures.
    #[allow(clippy::too_many_arguments)]
    pub fn prepare_table_cell_body<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        marker: SourceAnchorHandle,
        cell: SourceAnchorHandle,
        paragraphs: Vec<TextFlow>,
        limits: WriterLimits,
        now: u64,
    ) -> Result<PreparedStoredReviewCellBody<'a, 'source>, StoredReviewCellBodyOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)
            .map_err(|_| StoredReviewCellBodyOutputError::Source)?;
        let fresh = self
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewCellBodyOutputError::Source)?;
        let output = self
            .imported
            .lower_table_cell_body(&fresh.bytes, &marker, &cell, &paragraphs, limits)
            .map_err(|_| StoredReviewCellBodyOutputError::Output)?;
        self.verify(provider, now)
            .map_err(|_| StoredReviewCellBodyOutputError::Source)?;
        Ok(PreparedStoredReviewCellBody {
            review: self,
            marker,
            cell,
            paragraphs,
            limits,
            output,
        })
    }
}
impl PreparedStoredReviewCellBody<'_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &ReviewCellBodyOutputReceipt {
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
    ) -> Result<ReviewCellBodyOutputReceipt, StoredReviewCellBodyOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewCellBodyOutputError::Source)?;
        let fresh = self
            .review
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewCellBodyOutputError::Source)?;
        let output = self
            .review
            .imported
            .lower_table_cell_body(
                &fresh.bytes,
                &self.marker,
                &self.cell,
                &self.paragraphs,
                self.limits,
            )
            .map_err(|_| StoredReviewCellBodyOutputError::Output)?;
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewCellBodyOutputError::Source)?;
        if output.receipt() != self.output.receipt() {
            return Err(StoredReviewCellBodyOutputError::Binding);
        }
        self.output
            .with_verified_bytes(|_| ())
            .map_err(|_| StoredReviewCellBodyOutputError::Output)?;
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
    ) -> Result<T, StoredReviewCellBodyOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        self.output
            .with_verified_bytes(consume)
            .map_err(|_| StoredReviewCellBodyOutputError::Output)
    }
    /// Full comment metadata/protection/compiler/issuer/atomic publication remains unqualified.
    /// # Errors
    /// Always denies the product route after the original fresh checks.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredReviewCellBodyOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(StoredReviewCellBodyOutputError::RouteUnqualified)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredReviewCellBodyOutputError {
    #[error("stored_review_cell_body_original_source_rejected")]
    Source,
    #[error("stored_review_cell_body_output_rejected")]
    Output,
    #[error("stored_review_cell_body_output_binding_rejected")]
    Binding,
    #[error("stored_review_cell_body_output_route_unqualified")]
    RouteUnqualified,
}
