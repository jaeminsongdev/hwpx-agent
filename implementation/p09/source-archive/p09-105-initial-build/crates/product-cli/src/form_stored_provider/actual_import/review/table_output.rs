//! Dual authenticated source/template table candidate. NOT an atomic execution lease.
use super::StoredImportedReviewBodies;
use crate::form_stored_provider::{StoredFormProvider, actual_import::StoredImportedDocumentForms};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    TableCreateHwpxLimits, WriterLimits,
    document_import::structure::review::table_create_context::{
        ReviewTableTemplate,
        output::{ReviewTableDimensions, ReviewTableOutput, ReviewTableOutputReceipt},
    },
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

/// Source-derived selectors and explicit new geometry, never raw XML/offsets/Flow hashes.
/// The template is another actual stored import, not caller bytes or a cached permission.
pub struct StoredReviewTableRequest<'template> {
    pub template: &'template StoredImportedDocumentForms,
    pub marker: SourceAnchorHandle,
    pub paragraph: SourceAnchorHandle,
    pub table: SourceAnchorHandle,
    pub dimensions: ReviewTableDimensions,
}
impl fmt::Debug for StoredReviewTableRequest<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredReviewTableRequest(<redacted>)")
    }
}
#[derive(Clone, Copy, Debug, Default)]
pub struct StoredReviewTableLimits {
    pub create: TableCreateHwpxLimits,
    pub writer: WriterLimits,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StoredReviewTableQualification {
    FreshSameActorSourceAndTemplateReadOnlyNotAtomicLeaseCompilerOrPublication,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredReviewTableOutputReceipt {
    pub qualification: StoredReviewTableQualification,
    pub source_head_generation: u64,
    pub template_head_generation: u64,
    pub output: ReviewTableOutputReceipt,
}
pub struct PreparedStoredReviewTable<'a, 'source, 'template> {
    review: &'a StoredImportedReviewBodies<'source>,
    request: StoredReviewTableRequest<'template>,
    limits: StoredReviewTableLimits,
    output: ReviewTableOutput,
    receipt: StoredReviewTableOutputReceipt,
}
impl fmt::Debug for PreparedStoredReviewTable<'_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredReviewTable(<redacted>)")
    }
}
impl StoredReviewTableRequest<'_> {
    fn lower<R, B, S, V>(
        &self,
        review: &StoredImportedReviewBodies<'_>,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        template_provider: &StoredFormProvider<'_, R, B, S, V>,
        limits: StoredReviewTableLimits,
        now: u64,
    ) -> Result<ReviewTableOutput, StoredReviewTableOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        // A caller must be the same authenticated principal on both independently scoped
        // providers. Different documents/branches are permitted only after their own reads.
        if provider.scope.tenant != template_provider.scope.tenant
            || provider.scope.subject != template_provider.scope.subject
        {
            return Err(StoredReviewTableOutputError::Actor);
        }
        review
            .verify(provider, now)
            .map_err(|_| StoredReviewTableOutputError::Source)?;
        let fresh = review
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewTableOutputError::Source)?;
        let template = self
            .template
            .fresh_source(template_provider, now)
            .map_err(|_| StoredReviewTableOutputError::Template)?;
        let context = review
            .imported
            .prepare_table_creation(
                &fresh.bytes,
                &self.marker,
                &self.paragraph,
                ReviewTableTemplate {
                    forms: self.template.imported(),
                    fresh: &template.bytes,
                    table: &self.table,
                },
                limits.create,
            )
            .map_err(|_| StoredReviewTableOutputError::Output)?;
        let output = context
            .lower_table(
                &fresh.bytes,
                &template.bytes,
                &self.dimensions,
                limits.writer,
            )
            .map_err(|_| StoredReviewTableOutputError::Output)?;
        review
            .verify(provider, now)
            .map_err(|_| StoredReviewTableOutputError::Source)?;
        self.template
            .fresh_source(template_provider, now)
            .map_err(|_| StoredReviewTableOutputError::Template)?;
        Ok(output)
    }
}
impl<'source> StoredImportedReviewBodies<'source> {
    /// Fresh original authorization of both independently stored whole sources surrounds output.
    /// No ingest/revision/CAS/publication, caller template bytes or full-Flow defaults.
    /// # Errors
    /// Rejects principal mismatch, original source/template scope/ACL/AEAD/head or output failure.
    pub fn prepare_table<'a, 'template, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        template_provider: &StoredFormProvider<'_, R, B, S, V>,
        request: StoredReviewTableRequest<'template>,
        limits: StoredReviewTableLimits,
        now: u64,
    ) -> Result<PreparedStoredReviewTable<'a, 'source, 'template>, StoredReviewTableOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let output = request.lower(self, provider, template_provider, limits, now)?;
        let receipt = StoredReviewTableOutputReceipt {
            qualification: StoredReviewTableQualification::FreshSameActorSourceAndTemplateReadOnlyNotAtomicLeaseCompilerOrPublication,
            source_head_generation: self.source.receipt().head_generation,
            template_head_generation: request.template.receipt().head_generation,
            output: output.receipt().clone(),
        };
        Ok(PreparedStoredReviewTable {
            review: self,
            request,
            limits,
            output,
            receipt,
        })
    }
}
impl PreparedStoredReviewTable<'_, '_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &StoredReviewTableOutputReceipt {
        &self.receipt
    }
    /// Both original services and complete deterministic source output are replayed.
    /// Repeated reads do not hold an atomic authorization or publication lease.
    /// # Errors
    /// Rejects either provider's scope/ACL/AEAD/head/source or cached output drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        template_provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredReviewTableOutputReceipt, StoredReviewTableOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let output =
            self.request
                .lower(self.review, provider, template_provider, self.limits, now)?;
        if output.receipt() != &self.receipt.output
            || self.output.receipt() != &self.receipt.output
            || self.receipt.source_head_generation != self.review.source.receipt().head_generation
            || self.receipt.template_head_generation != self.request.template.receipt().head_generation
            || self.receipt.qualification != StoredReviewTableQualification::FreshSameActorSourceAndTemplateReadOnlyNotAtomicLeaseCompilerOrPublication
        {
            return Err(StoredReviewTableOutputError::Binding);
        }
        self.output
            .with_verified_bytes(|_| ())
            .map_err(|_| StoredReviewTableOutputError::Output)?;
        Ok(self.receipt.clone())
    }
    /// Does not invoke the consumer after failed authorization of either whole source.
    /// # Errors
    /// Rejects source/output drift; successful bytes never authorize publication.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        template_provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, StoredReviewTableOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, template_provider, now)?;
        self.output
            .with_verified_bytes(consume)
            .map_err(|_| StoredReviewTableOutputError::Output)
    }
    /// Full metadata/Flow/compiler/protection/issuer/atomic publication remains unqualified.
    /// # Errors
    /// Always denies product execution after fresh checks of both inputs and actual output.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        template_provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredReviewTableOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, template_provider, now)?;
        Err(StoredReviewTableOutputError::RouteUnqualified)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredReviewTableOutputError {
    #[error("stored_review_table_principal_mismatch")]
    Actor,
    #[error("stored_review_table_original_source_rejected")]
    Source,
    #[error("stored_review_table_original_template_rejected")]
    Template,
    #[error("stored_review_table_output_rejected")]
    Output,
    #[error("stored_review_table_output_binding_rejected")]
    Binding,
    #[error("stored_review_table_route_unqualified")]
    RouteUnqualified,
}
