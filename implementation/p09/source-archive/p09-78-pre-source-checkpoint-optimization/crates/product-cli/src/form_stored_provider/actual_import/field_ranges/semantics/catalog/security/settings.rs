//! Original fresh authenticated inspection with actual section/page/columns bindings.
use super::{
    StoredActiveSecurityImportError, StoredActiveSecurityImportReceipt,
    StoredImportedActiveSecurity,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::DocumentGraph;
use hwpx_package::document_import::fields::semantics::catalog::security::settings::{
    ImportedDocumentSectionSettings, ImportedSectionSettings, SectionSettingsImportError,
    SectionSettingsImportReceipt,
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::fmt;
use thiserror::Error;
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredSectionSettingsImportReceipt {
    pub source: StoredActiveSecurityImportReceipt,
    pub settings: SectionSettingsImportReceipt,
    pub qualification: &'static str,
}
pub struct StoredImportedSectionSettings<'a, 'security, 'catalog, 'fields, 'source> {
    security: &'a StoredImportedActiveSecurity<'security, 'catalog, 'fields, 'source>,
    imported: ImportedDocumentSectionSettings<'a, 'security, 'catalog, 'fields, 'source>,
    receipt: StoredSectionSettingsImportReceipt,
}
impl fmt::Debug for StoredImportedSectionSettings<'_, '_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredImportedSectionSettings(<redacted>)")
    }
}
impl<'security, 'catalog, 'fields, 'source>
    StoredImportedActiveSecurity<'security, 'catalog, 'fields, 'source>
{
    /// Verifies fresh service access and original whole source before and after import.
    /// # Errors
    /// Rejects original authentication/security/source/page/columns/bindings.
    pub fn import_section_settings<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<
        StoredImportedSectionSettings<'a, 'security, 'catalog, 'fields, 'source>,
        StoredSectionSettingsImportError,
    >
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        let imported = ImportedDocumentSectionSettings::import(&self.imported)?;
        self.verify(provider, now)?;
        let receipt = StoredSectionSettingsImportReceipt {
            source: self.receipt.clone(),
            settings: imported.receipt().clone(),
            qualification: "fresh_authenticated_actual_page_columns_source_binding_not_full_settings_native_layout_render_issuer_persistence_publication_or_product",
        };
        Ok(StoredImportedSectionSettings {
            security: self,
            imported,
            receipt,
        })
    }
}
impl StoredImportedSectionSettings<'_, '_, '_, '_, '_> {
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        self.imported.graph()
    }
    #[must_use]
    pub fn settings(&self) -> &[ImportedSectionSettings] {
        self.imported.settings()
    }
    #[must_use]
    pub const fn receipt(&self) -> &StoredSectionSettingsImportReceipt {
        &self.receipt
    }
    /// Full original fresh authorization/source/security plus deterministic settings replay.
    /// # Errors
    /// Rejects stale scope/head/revoked ACL/AEAD or source/settings/receipt drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredSectionSettingsImportReceipt, StoredSectionSettingsImportError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let source = self.security.verify(provider, now)?;
        let settings = ImportedDocumentSectionSettings::import(&self.security.imported)?;
        self.security.verify(provider, now)?;
        if self.receipt.source != source
            || self.imported.graph() != settings.graph()
            || self.imported.settings() != settings.settings()
            || self.receipt.settings != *settings.receipt()
        {
            return Err(StoredSectionSettingsImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum StoredSectionSettingsImportError {
    #[error("stored settings original fresh authenticated security/source rejected")]
    Security(#[from] StoredActiveSecurityImportError),
    #[error("stored settings original source page/column bindings rejected")]
    Settings(#[from] SectionSettingsImportError),
    #[error("stored settings whole graph/receipt/source binding rejected")]
    Binding,
}
