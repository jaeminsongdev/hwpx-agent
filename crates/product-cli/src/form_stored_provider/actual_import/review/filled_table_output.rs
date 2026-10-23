//! Filled table candidate over two independently authenticated immutable stored sources.
//! No atomic lease, durable commit, native metadata/compiler or publication authority.
use super::{
    StoredImportedReviewBodies,
    table_output::{
        StoredReviewTableLimits, StoredReviewTableOutputError, StoredReviewTableRequest,
    },
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use hwpx_package::document_import::structure::review::table_create_context::{
    ReviewTableTemplate,
    filled_output::{ReviewFilledTableOutput, ReviewFilledTableReceipt, ReviewNewTableCells},
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;

/// Actual stored template/anchors/new geometry plus explicit typed NEW cell contents.
/// Not caller XML, raw source offsets, cached permissions or native metadata defaults.
pub struct StoredReviewFilledTableRequest<'template> {
    pub selection: StoredReviewTableRequest<'template>,
    pub cells: ReviewNewTableCells,
}
impl fmt::Debug for StoredReviewFilledTableRequest<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredReviewFilledTableRequest(<redacted>)")
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StoredReviewFilledTableQualification {
    FreshSameActorSourceAndTemplateTypedCellsReadOnlyNotAtomicLeaseCompilerOrPublication,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredReviewFilledTableReceipt {
    pub qualification: StoredReviewFilledTableQualification,
    pub source_head_generation: u64,
    pub template_head_generation: u64,
    pub output: ReviewFilledTableReceipt,
}
pub struct PreparedStoredReviewFilledTable<'a, 'source, 'template> {
    review: &'a StoredImportedReviewBodies<'source>,
    request: StoredReviewFilledTableRequest<'template>,
    limits: StoredReviewTableLimits,
    output: ReviewFilledTableOutput,
    receipt: StoredReviewFilledTableReceipt,
}
impl fmt::Debug for PreparedStoredReviewFilledTable<'_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredReviewFilledTable(<redacted>)")
    }
}
impl StoredReviewFilledTableRequest<'_> {
    fn lower<R, B, S, V>(
        &self,
        review: &StoredImportedReviewBodies<'_>,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        template_provider: &StoredFormProvider<'_, R, B, S, V>,
        limits: &StoredReviewTableLimits,
        now: u64,
    ) -> Result<ReviewFilledTableOutput, StoredReviewTableOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
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
            .selection
            .template
            .fresh_source(template_provider, now)
            .map_err(|_| StoredReviewTableOutputError::Template)?;
        let context = review
            .imported
            .prepare_table_creation(
                &fresh.bytes,
                &self.selection.marker,
                &self.selection.paragraph,
                ReviewTableTemplate {
                    forms: self.selection.template.imported(),
                    fresh: &template.bytes,
                    table: &self.selection.table,
                },
                limits.create,
            )
            .map_err(|_| StoredReviewTableOutputError::Output)?;
        let output = context
            .lower_table_with_cells(
                &fresh.bytes,
                &template.bytes,
                &self.selection.dimensions,
                &self.cells,
                limits.writer,
            )
            .map_err(|_| StoredReviewTableOutputError::Output)?;
        // A fresh permission/digest/head check of BOTH original services follows actual output.
        // These observations are not an atomic lease across a subsequent consumer callback.
        review
            .verify(provider, now)
            .map_err(|_| StoredReviewTableOutputError::Source)?;
        self.selection
            .template
            .fresh_source(template_provider, now)
            .map_err(|_| StoredReviewTableOutputError::Template)?;
        Ok(output)
    }
}
impl<'source> StoredImportedReviewBodies<'source> {
    /// Derive actual filled native-package candidate between fresh reads of both inputs.
    /// No ingest/revision/CAS/publication or raw source/template bytes are accepted.
    /// # Errors
    /// Rejects both original scope/ACL/AEAD/head/source checks or original package output.
    pub fn prepare_filled_table<'a, 'template, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        template_provider: &StoredFormProvider<'_, R, B, S, V>,
        request: StoredReviewFilledTableRequest<'template>,
        limits: StoredReviewTableLimits,
        now: u64,
    ) -> Result<PreparedStoredReviewFilledTable<'a, 'source, 'template>, StoredReviewTableOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let output = request.lower(self, provider, template_provider, &limits, now)?;
        let receipt = StoredReviewFilledTableReceipt {
            qualification:StoredReviewFilledTableQualification::FreshSameActorSourceAndTemplateTypedCellsReadOnlyNotAtomicLeaseCompilerOrPublication,
            source_head_generation:self.source.receipt().head_generation,
            template_head_generation:request.selection.template.receipt().head_generation,
            output:output.receipt().clone(),
        };
        Ok(PreparedStoredReviewFilledTable {
            review: self,
            request,
            limits,
            output,
            receipt,
        })
    }
}
impl PreparedStoredReviewFilledTable<'_, '_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &StoredReviewFilledTableReceipt {
        &self.receipt
    }
    /// Replays both original fresh services and deterministic whole filled output/chain.
    /// # Errors
    /// Rejects source/template scope/ACL/AEAD/head drift, cached receipt/output/generation drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        template_provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredReviewFilledTableReceipt, StoredReviewTableOutputError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let output =
            self.request
                .lower(self.review, provider, template_provider, &self.limits, now)?;
        if output.receipt() != &self.receipt.output || self.output.receipt() != &self.receipt.output
            || self.receipt.source_head_generation != self.review.source.receipt().head_generation
            || self.receipt.template_head_generation != self.request.selection.template.receipt().head_generation
            || self.receipt.qualification != StoredReviewFilledTableQualification::FreshSameActorSourceAndTemplateTypedCellsReadOnlyNotAtomicLeaseCompilerOrPublication {
            return Err(StoredReviewTableOutputError::Binding);
        }
        self.output
            .with_verified_bytes(|_| ())
            .map_err(|_| StoredReviewTableOutputError::Output)?;
        Ok(self.receipt.clone())
    }
    /// Does not call the consumer after failed fresh checks of either original stored input.
    /// Repeated reads do not create an atomic lease for a subsequent callback/publication.
    /// # Errors
    /// Rejects original service and deterministic output replay/integrity failures.
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
    /// Full metadata/Flow/compiler/protection/issuer/atomic publication is unqualified.
    /// # Errors
    /// Always denies execution, but exposes original fresh service failures first.
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
