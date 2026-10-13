//! Fresh authenticated source binding for actual field ranges, not execution.
use super::{
    StoredActualFormImportError, StoredActualFormImportReceipt, StoredImportedDocumentForms,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::DocumentGraph;
use hwpx_package::document_import::fields::{
    FieldRangeImportError, FieldRangeImportReceipt, ImportedDocumentFields, ImportedFieldRange,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFieldRangeImportReceipt {
    pub source: StoredActualFormImportReceipt,
    pub fields: FieldRangeImportReceipt,
    pub qualification: &'static str,
}
pub struct StoredImportedFieldRanges<'a> {
    source: &'a StoredImportedDocumentForms,
    imported: ImportedDocumentFields<'a>,
    receipt: StoredFieldRangeImportReceipt,
}
impl fmt::Debug for StoredImportedFieldRanges<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedFieldRanges(<redacted>)")
    }
}
impl StoredImportedDocumentForms {
    /// Rechecks original ACL/AEAD/head/scope/whole source before deriving actual
    /// paragraph-local field ranges. No caller map, policies or evaluation.
    /// # Errors
    /// Rejects source authorization, stale snapshots, unsupported ranges/graph.
    pub fn import_field_ranges<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredImportedFieldRanges<'a>, StoredFieldRangeImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.fresh_source(provider, now)?;
        let imported = ImportedDocumentFields::import(&self.imported)?;
        provider
            .check_head(self.source.head)
            .map_err(StoredActualFormImportError::from)?;
        let receipt = StoredFieldRangeImportReceipt {
            source: self.receipt.clone(),
            fields: imported.receipt().clone(),
            qualification: "fresh_authenticated_observed_field_ranges_not_policy_issuer_complete_import_or_execution",
        };
        Ok(StoredImportedFieldRanges {
            source: self,
            imported,
            receipt,
        })
    }
}
impl StoredImportedFieldRanges<'_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.imported.graph()
    }
    #[must_use]
    pub fn fields(&self) -> &[ImportedFieldRange] {
        self.imported.fields()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredFieldRangeImportReceipt {
        &self.receipt
    }
    /// Fresh original service read plus full original and derived reconstruction.
    /// # Errors
    /// Rejects revoked access, head/source/scope/whole range/graph drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredFieldRangeImportReceipt, StoredFieldRangeImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let fresh = self.source.fresh_source(provider, now)?;
        let fields = self.imported.verify_source(&fresh.bytes)?;
        provider
            .check_head(fresh.head)
            .map_err(StoredActualFormImportError::from)?;
        if self.receipt.source != self.source.receipt || self.receipt.fields != fields {
            return Err(StoredFieldRangeImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum StoredFieldRangeImportError {
    #[error("stored field range original source service rejected")]
    Source(#[from] StoredActualFormImportError),
    #[error("stored actual field range importer rejected")]
    Fields(#[from] FieldRangeImportError),
    #[error("stored field range source/whole graph receipt binding rejected")]
    Binding,
}
