//! Original fresh stored-source checks around pure native style output; no publication route.
use super::StoredImportedCatalog;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::SourceAnchorHandle;
use hwpx_package::{
    WriterLimits,
    document_import::fields::semantics::catalog::memo_style::{
        MemoStyleLoweringReceipt, MemoStyleOutput, MemoStyleValues,
    },
};
use revision_service::RevisionRepository;
use std::fmt;
use thiserror::Error;

pub struct PreparedStoredMemoStyle<'a, 'catalog, 'fields, 'source> {
    catalog: &'a StoredImportedCatalog<'catalog, 'fields, 'source>,
    selector: SourceAnchorHandle,
    values: MemoStyleValues,
    limits: WriterLimits,
    output: MemoStyleOutput,
}
impl fmt::Debug for PreparedStoredMemoStyle<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredMemoStyle(<redacted>)")
    }
}
impl<'catalog, 'fields, 'source> StoredImportedCatalog<'catalog, 'fields, 'source> {
    /// Pure style artifact preparation, using only the ORIGINAL revision-selected source.
    /// # Errors
    /// Rejects fresh service/catalog drift or native style/output validation failures.
    pub fn prepare_memo_style<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        selector: SourceAnchorHandle,
        values: MemoStyleValues,
        limits: WriterLimits,
        now: u64,
    ) -> Result<PreparedStoredMemoStyle<'a, 'catalog, 'fields, 'source>, StoredMemoStyleError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)
            .map_err(|_| StoredMemoStyleError::Source)?;
        let fresh = self
            .meanings
            .ranges
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredMemoStyleError::Source)?;
        let output = self
            .imported
            .lower_memo_style(&fresh.bytes, &selector, &values, limits)
            .map_err(|_| StoredMemoStyleError::Output)?;
        self.verify(provider, now)
            .map_err(|_| StoredMemoStyleError::Source)?;
        Ok(PreparedStoredMemoStyle {
            catalog: self,
            selector,
            values,
            limits,
            output,
        })
    }
}
impl PreparedStoredMemoStyle<'_, '_, '_, '_> {
    #[must_use]
    pub const fn receipt(&self) -> &MemoStyleLoweringReceipt {
        self.output.receipt()
    }
    /// Fresh original scope/ACL/AEAD/head checks and full deterministic style lowering replay.
    /// # Errors
    /// Rejects any cached source, output or service-state drift. Not an atomic execution lease.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<MemoStyleLoweringReceipt, StoredMemoStyleError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.catalog
            .verify(provider, now)
            .map_err(|_| StoredMemoStyleError::Source)?;
        let fresh = self
            .catalog
            .meanings
            .ranges
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredMemoStyleError::Source)?;
        let output = self
            .catalog
            .imported
            .lower_memo_style(&fresh.bytes, &self.selector, &self.values, self.limits)
            .map_err(|_| StoredMemoStyleError::Output)?;
        self.catalog
            .verify(provider, now)
            .map_err(|_| StoredMemoStyleError::Source)?;
        if output.receipt() != self.output.receipt() {
            return Err(StoredMemoStyleError::Binding);
        }
        self.output
            .with_verified_bytes(|_| ())
            .map_err(|_| StoredMemoStyleError::Output)?;
        Ok(self.output.receipt().clone())
    }
    /// Callback sees bytes only after fresh stored-source verification. No ingest/commit/publish.
    /// # Errors
    /// Does not invoke the callback after permission, head, source or artifact drift.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, StoredMemoStyleError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        self.output
            .with_verified_bytes(consume)
            .map_err(|_| StoredMemoStyleError::Output)
    }
    /// Full native comment policy/execution/publication remains denied after fresh verification.
    /// # Errors
    /// Reports source drift first; otherwise always returns `RouteUnqualified`.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredMemoStyleError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(StoredMemoStyleError::RouteUnqualified)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredMemoStyleError {
    #[error("stored_memo_style_original_source_rejected")]
    Source,
    #[error("stored_memo_style_output_rejected")]
    Output,
    #[error("stored_memo_style_binding_rejected")]
    Binding,
    #[error("stored_memo_style_route_unqualified")]
    RouteUnqualified,
}
