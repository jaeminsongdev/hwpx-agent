//! Fresh authenticated security inspection; normal-tier activation remains denied.
use super::{StoredCatalogImportError, StoredCatalogImportReceipt, StoredImportedCatalog};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::DocumentGraph;
use hwpx_package::{
    ActivationKind,
    document_import::fields::semantics::catalog::security::{
        ActiveSecurityImportError, ActiveSecurityImportReceipt, ImportedActiveControlBinding,
        ImportedActiveResourceBinding, ImportedDocumentActiveSecurity,
        ImportedNativeFormSecurityBinding,
    },
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredActiveSecurityImportReceipt {
    pub source: StoredCatalogImportReceipt,
    pub security: ActiveSecurityImportReceipt,
    pub qualification: &'static str,
}
pub struct StoredImportedActiveSecurity<'a, 'catalog, 'fields, 'source> {
    catalog: &'a StoredImportedCatalog<'catalog, 'fields, 'source>,
    imported: ImportedDocumentActiveSecurity<'a, 'catalog, 'fields, 'source>,
    receipt: StoredActiveSecurityImportReceipt,
}
impl fmt::Debug for StoredImportedActiveSecurity<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedActiveSecurity(<redacted>)")
    }
}
impl<'catalog, 'fields, 'source> StoredImportedCatalog<'catalog, 'fields, 'source> {
    /// Original full fresh service/source/catalog checks precede passive inspection.
    /// # Errors
    /// Rejects access/head/scope/AEAD/source, original inventory or graph failures.
    pub fn import_active_security<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<
        StoredImportedActiveSecurity<'a, 'catalog, 'fields, 'source>,
        StoredActiveSecurityImportError,
    >
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        let imported = ImportedDocumentActiveSecurity::import(&self.imported)?;
        self.verify(provider, now)?;
        let receipt = StoredActiveSecurityImportReceipt {
            source: self.receipt.clone(),
            security: imported.receipt().clone(),
            qualification: "fresh_authenticated_passive_source_inventory_execution_denied_not_native_protection_encryption_document_signature_issuer_persistence_or_product",
        };
        Ok(StoredImportedActiveSecurity {
            catalog: self,
            imported,
            receipt,
        })
    }
}
impl StoredImportedActiveSecurity<'_, '_, '_, '_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.imported.graph()
    }
    #[must_use]
    pub fn controls(&self) -> &[ImportedActiveControlBinding] {
        self.imported.controls()
    }
    #[must_use]
    pub fn resources(&self) -> &[ImportedActiveResourceBinding] {
        self.imported.resources()
    }
    #[must_use]
    pub fn native_forms(&self) -> &[ImportedNativeFormSecurityBinding] {
        self.imported.native_forms()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredActiveSecurityImportReceipt {
        &self.receipt
    }
    /// Fresh original service authorization plus whole source/scanner reconstruction.
    /// # Errors
    /// Rejects revoked access/stale head/scope or whole inventory/source/graph drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredActiveSecurityImportReceipt, StoredActiveSecurityImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let catalog = self.catalog.verify(provider, now)?;
        let fresh = self
            .catalog
            .meanings
            .ranges
            .source
            .fresh_source(provider, now)
            .map_err(super::super::super::StoredFieldRangeImportError::from)
            .map_err(super::super::StoredFieldSemanticImportError::from)
            .map_err(StoredCatalogImportError::from)?;
        let security = self.imported.verify_source(&fresh.bytes)?;
        self.catalog.verify(provider, now)?;
        if self.receipt.source != catalog || self.receipt.security != security {
            return Err(StoredActiveSecurityImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
    /// No activation is performed. A fresh access failure precedes policy denial.
    /// # Errors
    /// Denies all normal-tier actions after original fresh authenticated inspection.
    pub fn require_activation<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        action: ActivationKind,
        now: u64,
    ) -> Result<(), StoredActiveSecurityImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        self.imported.require_activation(action)?;
        Err(StoredActiveSecurityImportError::Binding)
    }
}
#[derive(Debug, Error)]
pub enum StoredActiveSecurityImportError {
    #[error("stored security original authenticated catalog/source rejected")]
    Source(#[from] StoredCatalogImportError),
    #[error("stored security original active inventory/binding rejected")]
    Security(#[from] ActiveSecurityImportError),
    #[error("stored security whole inventory/source/graph receipt binding rejected")]
    Binding,
}
