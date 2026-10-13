//! Actual source-backed review body reader over the original authenticated service.
//! Cached getters are memory, not current access or execution authority.
pub mod body_output;
pub mod delete_output;
pub mod locations;
use super::{
    StoredActualFormImportError, StoredActualFormImportReceipt, StoredImportedDocumentForms,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::DocumentGraph;
use hwpx_package::document_import::structure::review::{
    ImportedDocumentReviewBodies, ImportedReviewBodyObservation, ReviewBodyImportError,
    ReviewBodyImportReceipt,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredReviewBodyImportReceipt {
    pub source: StoredActualFormImportReceipt,
    pub review: ReviewBodyImportReceipt,
    pub qualification: &'static str,
}
pub struct StoredImportedReviewBodies<'a> {
    source: &'a StoredImportedDocumentForms,
    imported: ImportedDocumentReviewBodies<'a>,
    receipt: StoredReviewBodyImportReceipt,
}
impl fmt::Debug for StoredImportedReviewBodies<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedReviewBodies(<redacted>)")
    }
}
impl StoredImportedDocumentForms {
    /// Fresh original ACL/AEAD/head/scope/whole-source checks surround body derivation.
    /// No caller graph/XML/author/time/defaults or evidence writes are accepted.
    /// # Errors
    /// Rejects authorization/source drift and malformed body/field/graph bindings.
    pub fn import_review_bodies<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredImportedReviewBodies<'a>, StoredReviewBodyImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.fresh_source(provider, now)?;
        let imported = ImportedDocumentReviewBodies::import(&self.imported)?;
        self.fresh_source(provider, now)?;
        let receipt = StoredReviewBodyImportReceipt {
            source: self.receipt.clone(),
            review: imported.receipt().clone(),
            qualification: "fresh_authenticated_source_review_body_not_author_time_state_issuer_atomic_lease_full_comment_execution_or_native_gate",
        };
        Ok(StoredImportedReviewBodies {
            source: self,
            imported,
            receipt,
        })
    }
}
impl StoredImportedReviewBodies<'_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.imported.graph()
    }
    #[must_use]
    pub fn observations(&self) -> &[ImportedReviewBodyObservation] {
        self.imported.observations()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredReviewBodyImportReceipt {
        &self.receipt
    }
    /// Reconstructs the whole original + derived source graph between fresh reads.
    /// Repeated reads are NOT a held execution lease or native metadata qualification.
    /// # Errors
    /// Rejects revoked access, AEAD/source/head/scope/body/graph/receipt drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredReviewBodyImportReceipt, StoredReviewBodyImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let fresh = self.source.fresh_source(provider, now)?;
        let review = self.imported.verify_source(&fresh.bytes)?;
        self.source.fresh_source(provider, now)?;
        if self.receipt.source != self.source.receipt || self.receipt.review != review {
            return Err(StoredReviewBodyImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum StoredReviewBodyImportError {
    #[error("stored review original source service rejected")]
    Source(#[from] StoredActualFormImportError),
    #[error("stored review actual body importer rejected")]
    Review(#[from] ReviewBodyImportError),
    #[error("stored review whole source/body/graph/receipt binding rejected")]
    Binding,
}
