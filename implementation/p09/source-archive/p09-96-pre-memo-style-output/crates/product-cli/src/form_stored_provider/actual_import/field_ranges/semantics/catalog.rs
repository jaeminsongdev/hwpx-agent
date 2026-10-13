//! Fresh original authenticated read before/after complete source catalog binding.
pub mod security;
pub mod fonts;
pub mod assembly;
use super::{
    StoredFieldSemanticImportError, StoredFieldSemanticImportReceipt, StoredImportedFieldSemantics,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::DocumentGraph;
use hwpx_package::document_import::fields::semantics::catalog::{
    CatalogImportError, CatalogImportReceipt, ImportedCatalogDefinition, ImportedDocumentCatalog,
    ImportedParagraphCatalogUse,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredCatalogImportReceipt {
    pub source: StoredFieldSemanticImportReceipt,
    pub catalog: CatalogImportReceipt,
    pub qualification: &'static str,
}
pub struct StoredImportedCatalog<'a, 'fields, 'source> {
    meanings: &'a StoredImportedFieldSemantics<'fields, 'source>,
    imported: ImportedDocumentCatalog<'a, 'fields, 'source>,
    receipt: StoredCatalogImportReceipt,
}
impl fmt::Debug for StoredImportedCatalog<'_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedCatalog(<redacted>)")
    }
}
impl<'fields, 'source> StoredImportedFieldSemantics<'fields, 'source> {
    /// Derives header/body catalog relationships only after original fresh checks.
    /// # Errors
    /// Rejects service scope/ACL/AEAD/head or original typed reader/graph failures.
    pub fn import_catalog<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredImportedCatalog<'a, 'fields, 'source>, StoredCatalogImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        let imported = ImportedDocumentCatalog::import(&self.imported)?;
        // Reuse whole authorization/reconstruction, not a held lock or CAS claim.
        self.verify(provider, now)?;
        let receipt = StoredCatalogImportReceipt {
            source: self.receipt.clone(),
            catalog: imported.receipt().clone(),
            qualification: "fresh_authenticated_original_typed_header_and_source_uses_not_cascade_security_issuer_persistence_publication_native_or_gate",
        };
        Ok(StoredImportedCatalog {
            meanings: self,
            imported,
            receipt,
        })
    }
}
impl StoredImportedCatalog<'_, '_, '_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.imported.graph()
    }
    #[must_use]
    pub fn definitions(&self) -> &[ImportedCatalogDefinition] {
        self.imported.definitions()
    }
    #[must_use]
    pub fn uses(&self) -> &[ImportedParagraphCatalogUse] {
        self.imported.uses()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredCatalogImportReceipt {
        &self.receipt
    }
    /// Original fresh service read plus complete source/body/header reconstruction.
    /// # Errors
    /// Rejects scope/access/head/source or cached graph/reader/receipt drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredCatalogImportReceipt, StoredCatalogImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let meanings = self.meanings.verify(provider, now)?;
        let fresh = self
            .meanings
            .ranges
            .source
            .fresh_source(provider, now)
            .map_err(super::super::StoredFieldRangeImportError::from)
            .map_err(StoredFieldSemanticImportError::from)?;
        let catalog = self.imported.verify_source(&fresh.bytes)?;
        self.meanings.verify(provider, now)?;
        if self.receipt.source != meanings || self.receipt.catalog != catalog {
            return Err(StoredCatalogImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum StoredCatalogImportError {
    #[error("stored catalog original authenticated meaning/source rejected")]
    Source(#[from] StoredFieldSemanticImportError),
    #[error("stored catalog original typed header/body rejected")]
    Catalog(#[from] CatalogImportError),
    #[error("stored catalog whole source/graph receipt binding rejected")]
    Binding,
}
