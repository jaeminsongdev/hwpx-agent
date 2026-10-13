//! Fresh service-bound source meanings. No policy/approval/publication capability.
pub mod catalog;
use super::{
    StoredFieldRangeImportError, StoredFieldRangeImportReceipt, StoredImportedFieldRanges,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::DocumentGraph;
use hwpx_package::document_import::fields::semantics::{
    FieldSemanticImportError, FieldSemanticImportReceipt, ImportedDocumentFieldSemantics,
    ImportedFieldSemantic,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFieldSemanticImportReceipt {
    pub source: StoredFieldRangeImportReceipt,
    pub semantics: FieldSemanticImportReceipt,
    pub qualification: &'static str,
}
pub struct StoredImportedFieldSemantics<'a, 'source> {
    ranges: &'a StoredImportedFieldRanges<'source>,
    imported: ImportedDocumentFieldSemantics<'a, 'source>,
    receipt: StoredFieldSemanticImportReceipt,
}
impl fmt::Debug for StoredImportedFieldSemantics<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedFieldSemantics(<redacted>)")
    }
}
impl<'source> StoredImportedFieldRanges<'source> {
    /// Original fresh authenticated read/range verification before typed meaning.
    /// # Errors
    /// Rejects source authorization/head/scope, malformed meanings and binding.
    pub fn import_semantics<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredImportedFieldSemantics<'a, 'source>, StoredFieldSemanticImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        let imported = ImportedDocumentFieldSemantics::import(&self.imported)?;
        provider
            .check_head(self.source.source.head)
            .map_err(super::super::StoredActualFormImportError::from)
            .map_err(StoredFieldRangeImportError::from)?;
        let receipt = StoredFieldSemanticImportReceipt {
            source: self.receipt.clone(),
            semantics: imported.receipt().clone(),
            qualification: "fresh_authenticated_source_meaning_not_external_approval_evaluation_or_execution",
        };
        Ok(StoredImportedFieldSemantics {
            ranges: self,
            imported,
            receipt,
        })
    }
}
impl StoredImportedFieldSemantics<'_, '_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.imported.graph()
    }
    #[must_use]
    pub fn observations(&self) -> &[ImportedFieldSemantic] {
        self.imported.observations()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredFieldSemanticImportReceipt {
        &self.receipt
    }
    /// Rechecks original service and full source/body/forms/ranges/meanings.
    /// Two checked head reads are not an atomic lock/CAS or idempotency claim.
    /// # Errors
    /// Rejects access/source/head/scope or whole cached graph/receipt drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredFieldSemanticImportReceipt, StoredFieldSemanticImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let ranges = self.ranges.verify(provider, now)?;
        let fresh = self
            .ranges
            .source
            .fresh_source(provider, now)
            .map_err(StoredFieldRangeImportError::from)?;
        let semantics = self.imported.verify_source(&fresh.bytes)?;
        provider
            .check_head(fresh.head)
            .map_err(super::super::StoredActualFormImportError::from)
            .map_err(StoredFieldRangeImportError::from)?;
        if self.receipt.source != ranges || self.receipt.semantics != semantics {
            return Err(StoredFieldSemanticImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum StoredFieldSemanticImportError {
    #[error("stored field semantics original authenticated source rejected")]
    Source(#[from] StoredFieldRangeImportError),
    #[error("stored actual field meaning rejected")]
    Semantics(#[from] FieldSemanticImportError),
    #[error("stored field semantics whole binding rejected")]
    Binding,
}
