//! Authenticated unified source graph and typed sidecars; no full import/publication authority.
use super::{StoredCatalogImportError, StoredCatalogImportReceipt, StoredImportedCatalog};
use crate::form_stored_provider::{StoredFormProvider, actual_import::StoredActualFormImportError};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::DocumentGraph;
use hwpx_package::document_import::fields::semantics::catalog::assembly::{
    DocumentAssemblyError, DocumentAssemblyReceipt, ImportedDocumentAssembly,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredDocumentAssemblyReceipt {
    pub source: StoredCatalogImportReceipt,
    pub assembly: DocumentAssemblyReceipt,
    pub qualification: &'static str,
}
pub struct StoredImportedDocumentAssembly<'a, 'catalog, 'fields, 'source> {
    catalog: &'a StoredImportedCatalog<'catalog, 'fields, 'source>,
    imported: ImportedDocumentAssembly<'a, 'catalog, 'fields, 'source>,
    receipt: StoredDocumentAssemblyReceipt,
}
impl fmt::Debug for StoredImportedDocumentAssembly<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedDocumentAssembly(<redacted>)")
    }
}
impl<'catalog, 'fields, 'source> StoredImportedCatalog<'catalog, 'fields, 'source> {
    /// Performs original fresh catalog access checks before construction and source checks afterwards.
    /// # Errors
    /// Rejects revoked access, stale source/head or any original component/assembly failure.
    pub fn import_document_assembly<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<
        StoredImportedDocumentAssembly<'a, 'catalog, 'fields, 'source>,
        StoredDocumentAssemblyError,
    >
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        let imported = ImportedDocumentAssembly::import(&self.imported)?;
        self.meanings.ranges.source.verify(provider, now)?;
        let receipt = StoredDocumentAssemblyReceipt {
            source: self.receipt.clone(),
            assembly: imported.receipt().clone(),
            qualification: "fresh_authenticated_single_source_graph_and_typed_sidecars_not_full_import_policy_issuer_atomic_cas_persistence_publication_native_or_gate",
        };
        Ok(StoredImportedDocumentAssembly {
            catalog: self,
            imported,
            receipt,
        })
    }
}
impl<'a, 'catalog, 'fields, 'source>
    StoredImportedDocumentAssembly<'a, 'catalog, 'fields, 'source>
{
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.imported.graph()
    }
    #[must_use]
    pub const fn imported(&self) -> &ImportedDocumentAssembly<'a, 'catalog, 'fields, 'source> {
        &self.imported
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredDocumentAssemblyReceipt {
        &self.receipt
    }
    /// Authenticated fresh bytes, full whole-model reconstruction, and final original service checks.
    /// # Errors
    /// Rejects scope/access/head/AEAD/quarantine/source or any cached graph/sidecar/receipt drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredDocumentAssemblyReceipt, StoredDocumentAssemblyError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let source = self.catalog.verify(provider, now)?;
        let fresh = self
            .catalog
            .meanings
            .ranges
            .source
            .fresh_source(provider, now)?;
        let assembly = self.imported.verify_source(&fresh.bytes)?;
        self.catalog.meanings.ranges.source.verify(provider, now)?;
        if self.receipt.source != source || self.receipt.assembly != assembly {
            return Err(StoredDocumentAssemblyError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum StoredDocumentAssemblyError {
    #[error("stored assembly original authenticated source checkpoint rejected")]
    SourceCheckpoint(#[from] StoredActualFormImportError),
    #[error("stored assembly original fresh catalog rejected")]
    Catalog(#[from] StoredCatalogImportError),
    #[error("stored assembly original component or whole-model binding rejected")]
    Assembly(#[from] DocumentAssemblyError),
    #[error("stored assembly whole receipt/source binding rejected")]
    Binding,
}
