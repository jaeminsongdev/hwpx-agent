//! Current service source -> owned CROSSREF command candidate. Never a write grant.
use super::{
    StoredActualFormImportError, StoredActualFormImportReceipt, StoredImportedDocumentForms,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactMetadataRepository, ArtifactScanner, AuthScope, EncryptedBlobStore,
};
use domain_ir::ReferenceAuxiliaryLimits;
use hwpx_package::{
    WriterLimits,
    document_import::fields::{
        ImportedDocumentFields,
        semantics::source_index::{
            SourceFieldMeaningIndex,
            bookmark_updates::{
                SourceBookmarkCommandCandidate, SourceBookmarkCommandChange,
                SourceBookmarkCommandError, SourceBookmarkCommandReceipt,
            },
        },
    },
};
use revision_service::RevisionRepository;
use serde::Serialize;
use std::{
    fmt,
    sync::atomic::{AtomicBool, Ordering},
};
use thiserror::Error;
const PROFILE: &str = "hwpx-agent.stored-source-bookmark-command-candidate/v1";
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredBookmarkCommandReceipt {
    pub profile: &'static str,
    pub source: StoredActualFormImportReceipt,
    pub output: SourceBookmarkCommandReceipt,
    pub qualification: &'static str,
    pub execution_or_publication_authority: bool,
}
pub struct PreparedStoredBookmarkCommandCandidate<'a> {
    source: &'a StoredImportedDocumentForms,
    output: SourceBookmarkCommandCandidate,
    receipt: StoredBookmarkCommandReceipt,
    denied: AtomicBool,
}
impl fmt::Debug for PreparedStoredBookmarkCommandCandidate<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(
            "PreparedStoredBookmarkCommandCandidate(<redacted>; no_CAS_or_execution_authority)",
        )
    }
}
#[derive(Debug, Error)]
pub enum StoredBookmarkCommandError {
    #[error("STORED_BOOKMARK_COMMAND_CURRENT_SOURCE_DENIED")]
    Source(#[from] StoredActualFormImportError),
    #[error("STORED_BOOKMARK_COMMAND_WRITE_SCOPE_REQUIRED")]
    Permission,
    #[error("STORED_BOOKMARK_COMMAND_MEANINGS_DENIED")]
    Meanings,
    #[error("STORED_BOOKMARK_COMMAND_LOWER_DENIED")]
    Output(#[from] SourceBookmarkCommandError),
    #[error("STORED_BOOKMARK_COMMAND_BINDING_DENIED")]
    Binding,
    #[error("STORED_BOOKMARK_COMMAND_OUTPUT_INTEGRITY_DENIED")]
    Integrity,
    #[error("STORED_BOOKMARK_COMMAND_PRIOR_DENIAL_IS_FINAL")]
    PreviouslyDenied,
    #[error("STORED_BOOKMARK_COMMAND_ROUTE_UNQUALIFIED")]
    RouteUnqualified,
}
type E = StoredBookmarkCommandError;

/// Fresh service authorization + complete raw snapshot equality. A full source
/// reconstruction already established this immutable import; identical bytes
/// at the final boundary need not be re-imported or lowered a second time.
fn final_access<R, B, S, V>(
    source: &StoredImportedDocumentForms,
    provider: &StoredFormProvider<'_, R, B, S, V>,
    now: u64,
) -> Result<(), E>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    if !provider
        .artifact_context
        .has_scope(AuthScope::DocumentWrite)
    {
        return Err(E::Permission);
    }
    if source.source.scope != provider.scope {
        return Err(E::Binding);
    }
    let fresh = provider
        .source(source.source.head, now)
        .map_err(StoredActualFormImportError::from)?;
    if fresh.scope != source.source.scope
        || fresh.head != source.source.head
        || fresh.artifact != source.source.artifact
        || fresh.digest != source.source.digest
        || fresh.bytes != source.source.bytes
    {
        return Err(E::Binding);
    }
    provider
        .check_head(source.source.head)
        .map_err(StoredActualFormImportError::from)?;
    Ok(())
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Requires current write token scope, authenticated source ACL/AEAD/head,
    /// a fresh whole-source proof and all original selection/protection checks.
    /// Candidate preparation does not authorize project mutation or publishing.
    pub fn prepare_bookmark_command_candidate<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        requests: &[SourceBookmarkCommandChange<'_>],
        limits: ReferenceAuxiliaryLimits,
        writer: WriterLimits,
        now: u64,
    ) -> Result<PreparedStoredBookmarkCommandCandidate<'_>, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        if !provider
            .artifact_context
            .has_scope(AuthScope::DocumentWrite)
        {
            return Err(E::Permission);
        }
        let (fresh, proof) = self.fresh_source_reconstructed(provider, now)?;
        let fields = ImportedDocumentFields::import(&self.imported).map_err(|_| E::Meanings)?;
        let index = SourceFieldMeaningIndex::import(&fields, limits).map_err(|_| E::Meanings)?;
        let output = index.lower_bookmark_command_changes(&proof, requests, writer)?;
        if output.receipt().source_package_sha256 != *fresh.digest.as_bytes()
            || output.receipt().changes.len() != requests.len()
            || !output.receipt().outside_selected_command_contents_exact
            || !output.receipt().cached_values_preserved_not_refreshed
            || output
                .receipt()
                .native_protection_currentness_execution_or_publication_qualified
        {
            return Err(E::Binding);
        }
        final_access(self, provider, now)?;
        let receipt = StoredBookmarkCommandReceipt {
            profile: PROFILE,
            source: self.receipt.clone(),
            output: output.receipt().clone(),
            qualification: "authenticated_current_source_candidate_not_atomic_write_membership_lease_CAS_registration_execution_native_or_publication",
            execution_or_publication_authority: false,
        };
        Ok(PreparedStoredBookmarkCommandCandidate {
            source: self,
            output,
            receipt,
            denied: AtomicBool::new(false),
        })
    }
}
impl PreparedStoredBookmarkCommandCandidate<'_> {
    #[must_use]
    pub const fn receipt(&self) -> &StoredBookmarkCommandReceipt {
        &self.receipt
    }
    fn fresh<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        if self.denied.load(Ordering::Acquire) {
            return Err(E::PreviouslyDenied);
        }
        if !provider
            .artifact_context
            .has_scope(AuthScope::DocumentWrite)
        {
            return Err(E::Permission);
        }
        self.source.fresh_source(provider, now)?;
        if self.receipt.profile != PROFILE
            || self.receipt.source != self.source.receipt
            || self.receipt.output != *self.output.receipt()
            || self.receipt.output.source_package_sha256 != *self.source.source.digest.as_bytes()
            || self.receipt.execution_or_publication_authority
            || self
                .receipt
                .output
                .native_protection_currentness_execution_or_publication_qualified
            || !self.receipt.output.outside_selected_command_contents_exact
            || !self.receipt.output.cached_values_preserved_not_refreshed
        {
            return Err(E::Binding);
        }
        Ok(())
    }
    /// Sole byte delivery boundary. Every access checks current source and
    /// writer integrity; fresh ACL/AEAD/raw bytes/head are checked again inside
    /// the writer callback. These observations are NOT an atomic lease/CAS.
    /// # Errors
    /// No consumer runs after failed checks. Any observed denial poisons this
    /// candidate permanently, including after ACL regrant or blob restoration.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        let result = (|| {
            self.fresh(provider, now)?;
            self.output
                .with_verified_bytes(|bytes| {
                    final_access(self.source, provider, now)?;
                    if self.denied.load(Ordering::Acquire) {
                        return Err(E::PreviouslyDenied);
                    }
                    Ok(consume(bytes))
                })
                .map_err(|_| E::Integrity)?
        })();
        if result.is_err() {
            self.denied.store(true, Ordering::Release);
        }
        result
    }
    /// # Errors
    /// Fresh delivery checks with no bytes exported or re-lowering performed.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<&StoredBookmarkCommandReceipt, E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.with_verified_bytes(provider, now, |_| ())?;
        Ok(&self.receipt)
    }
    /// # Errors
    /// Successful source verification is never a registered executable route.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), E>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(E::RouteUnqualified)
    }
}
