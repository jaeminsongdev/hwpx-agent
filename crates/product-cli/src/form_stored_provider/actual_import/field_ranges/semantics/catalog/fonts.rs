//! Authenticated source font definitions; no font loading or substitution.
use super::{StoredCatalogImportError, StoredCatalogImportReceipt, StoredImportedCatalog};
use crate::form_stored_provider::{StoredFormProvider, actual_import::StoredActualFormImportError};
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::DocumentGraph;
use hwpx_package::document_import::fields::semantics::catalog::fonts::{
    FontCatalogImportError, FontCatalogImportReceipt, ImportedCharacterFontLink,
    ImportedDocumentFonts, ImportedFontDefinition,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredFontCatalogImportReceipt {
    pub source: StoredCatalogImportReceipt,
    pub fonts: FontCatalogImportReceipt,
    pub qualification: &'static str,
}
pub struct StoredImportedFonts<'a, 'catalog, 'fields, 'source> {
    catalog: &'a StoredImportedCatalog<'catalog, 'fields, 'source>,
    imported: ImportedDocumentFonts<'a, 'catalog, 'fields, 'source>,
    receipt: StoredFontCatalogImportReceipt,
}
impl fmt::Debug for StoredImportedFonts<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedFonts(<redacted>)")
    }
}
impl<'catalog, 'fields, 'source> StoredImportedCatalog<'catalog, 'fields, 'source> {
    /// Retains original fresh authenticated source checks before and after font binding.
    /// # Errors
    /// Rejects original access/source/catalog errors and font declaration/link failures.
    pub fn import_fonts<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredImportedFonts<'a, 'catalog, 'fields, 'source>, StoredFontCatalogImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        let imported = ImportedDocumentFonts::import(&self.imported)?;
        self.meanings.ranges.source.verify(provider, now)?;
        let receipt = StoredFontCatalogImportReceipt {
            source: self.receipt.clone(),
            fonts: imported.receipt().clone(),
            qualification: "fresh_authenticated_source_declared_fonts_and_language_links_not_platform_fonts_embedding_resolution_substitution_render_atomic_cas_issuer_persistence_publication_native_or_gate",
        };
        Ok(StoredImportedFonts {
            catalog: self,
            imported,
            receipt,
        })
    }
}
impl StoredImportedFonts<'_, '_, '_, '_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.imported.graph()
    }
    #[must_use]
    pub fn definitions(&self) -> &[ImportedFontDefinition] {
        self.imported.definitions()
    }
    #[must_use]
    pub fn links(&self) -> &[ImportedCharacterFontLink] {
        self.imported.links()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredFontCatalogImportReceipt {
        &self.receipt
    }
    /// Rechecks original whole authorization/source and reconstructs complete font bindings.
    /// # Errors
    /// Rejects revoked access, tampering, stale head/scope and any cached graph/link drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredFontCatalogImportReceipt, StoredFontCatalogImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let source = self.catalog.verify(provider, now)?;
        let fonts = ImportedDocumentFonts::import(&self.catalog.imported)?;
        self.catalog.meanings.ranges.source.verify(provider, now)?;
        if self.receipt.source != source
            || self.imported.graph() != fonts.graph()
            || self.imported.definitions() != fonts.definitions()
            || self.imported.links() != fonts.links()
            || self.receipt.fonts != *fonts.receipt()
        {
            return Err(StoredFontCatalogImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum StoredFontCatalogImportError {
    #[error("stored fonts original authenticated source checkpoint rejected")]
    SourceCheckpoint(#[from] StoredActualFormImportError),
    #[error("stored fonts original fresh catalog/source rejected")]
    Catalog(#[from] StoredCatalogImportError),
    #[error("stored fonts original source font declarations/references rejected")]
    Fonts(#[from] FontCatalogImportError),
    #[error("stored fonts whole graph/receipt/source binding rejected")]
    Binding,
}
