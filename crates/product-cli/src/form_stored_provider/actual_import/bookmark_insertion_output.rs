//! Current authenticated stored source -> owned first-insertion candidate.
//! A private candidate is not a write lease, result ingestion, CAS or Native grant.
pub mod compiled707;
use super::bookmark_command_output::{StoredBookmarkCommandError, final_access};
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
        bookmark_insertion::{
            SourceBookmarkInsertion, SourceBookmarkInsertionError,
            generated::{SourceBookmarkCreationCandidate, SourceBookmarkCreationReceipt},
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
const PROFILE: &str = "hwpx-agent.stored-source-bookmark-first-insertion/v1";
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredBookmarkInsertionReceipt {
    pub profile: &'static str,
    pub source: StoredActualFormImportReceipt,
    pub output: SourceBookmarkCreationReceipt,
    pub qualification: &'static str,
    pub execution_or_publication_authority: bool,
}
pub struct PreparedStoredBookmarkInsertionCandidate {
    source: StoredImportedDocumentForms,
    output: SourceBookmarkCreationCandidate,
    receipt: StoredBookmarkInsertionReceipt,
    denied: AtomicBool,
    // Retain only the exact source selections used by the successful lowerer.
    run: domain_ir::SourceAnchorHandle,
    target_id: domain_ir::LogicalId,
}
impl fmt::Debug for PreparedStoredBookmarkInsertionCandidate {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(
            "PreparedStoredBookmarkInsertionCandidate(<redacted>; no_CAS_or_execution_authority)",
        )
    }
}
#[derive(Debug, Error)]
pub enum StoredBookmarkInsertionError {
    #[error("STORED_BOOKMARK_INSERT_CURRENT_SOURCE_DENIED")]
    Source(#[from] StoredActualFormImportError),
    #[error("STORED_BOOKMARK_INSERT_CURRENT_ACCESS_DENIED")]
    Access(#[from] StoredBookmarkCommandError),
    #[error("STORED_BOOKMARK_INSERT_WRITE_SCOPE_REQUIRED")]
    Permission,
    #[error("STORED_BOOKMARK_INSERT_FIELD_IMPORT_DENIED")]
    Fields,
    #[error("STORED_BOOKMARK_INSERT_LOWER_DENIED")]
    Output(#[from] SourceBookmarkInsertionError),
    #[error("STORED_BOOKMARK_INSERT_BINDING_DENIED")]
    Binding,
    #[error("STORED_BOOKMARK_INSERT_OUTPUT_INTEGRITY_DENIED")]
    Integrity,
    #[error("STORED_BOOKMARK_INSERT_PRIOR_DENIAL_IS_FINAL")]
    PreviouslyDenied,
    #[error("STORED_BOOKMARK_INSERT_ROUTE_UNQUALIFIED")]
    RouteUnqualified,
}
type E = StoredBookmarkInsertionError;
impl StoredImportedDocumentForms {
    /// Consumes the original model; no full graph/output clone or loss of a
    /// previously denied candidate. The new candidate owns its entire lifetime.
    /// # Errors
    /// Requires write scope, current ACL/quarantine/AEAD/head/raw bytes and a
    /// complete fresh reconstruction before the unchanged protected lowerer.
    pub fn into_bookmark_insertion_candidate<R, B, S, V>(
        self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        request: SourceBookmarkInsertion<'_>,
        limits: ReferenceAuxiliaryLimits,
        writer: WriterLimits,
        now: u64,
    ) -> Result<PreparedStoredBookmarkInsertionCandidate, E>
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
        let fields = ImportedDocumentFields::import(&self.imported).map_err(|_| E::Fields)?;
        let run=request.run.clone();
        let target_id=request.target_id.clone();
        let output = fields.create_bookmark_reference(&proof, request, limits, writer)?;
        let r = output.receipt();
        if r.source_package_sha256 != *fresh.digest.as_bytes()
            || r.inserted_fields != 1
            || r.requires_existing_crossref_envelope
            || !r.inserted_parameter_envelope_readback_verified
            || !r.outside_insertions_exact
            || !r.original_selected_run_exact
            || !r.existing_display_text_is_not_evaluated_or_refreshed
            || r.native_currentness_execution_or_publication_qualified
        {
            return Err(E::Binding);
        }
        final_access(&self, provider, now)?;
        let receipt = StoredBookmarkInsertionReceipt {
            profile: PROFILE,
            source: self.receipt.clone(),
            output: output.receipt().clone(),
            qualification: "authenticated_current_source_and_owned_candidate_not_project_membership_lease_CAS_registration_execution_native_or_publication",
            execution_or_publication_authority: false,
        };
        Ok(PreparedStoredBookmarkInsertionCandidate {
            source: self,
            output,
            receipt,
            denied: AtomicBool::new(false),
            run,
            target_id,
        })
    }
}
impl PreparedStoredBookmarkInsertionCandidate {
    #[must_use]
    pub const fn receipt(&self) -> &StoredBookmarkInsertionReceipt {
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
        // Reuse the EXACT original write-scope/provider/head/AEAD/full-byte
        // predicate. Equal authenticated fresh bytes bind the private immutable
        // model already reconstructed at preparation, without another graph
        // import/lowerer/output clone for each delivery/receipt read.
        final_access(&self.source, provider, now)?;
        let r = &self.receipt.output;
        if self.receipt.profile != PROFILE
            || self.receipt.source != self.source.receipt
            || r != self.output.receipt()
            || r.source_package_sha256 != *self.source.source.digest.as_bytes()
            || r.inserted_fields != 1
            || r.requires_existing_crossref_envelope
            || !r.inserted_parameter_envelope_readback_verified
            || !r.outside_insertions_exact
            || !r.original_selected_run_exact
            || !r.existing_display_text_is_not_evaluated_or_refreshed
            || r.native_currentness_execution_or_publication_qualified
            || self.receipt.execution_or_publication_authority
        {
            return Err(E::Binding);
        }
        Ok(())
    }
    /// The sole byte-delivery boundary. Current scope/ACL/quarantine/AEAD/head
    /// and every raw source byte are checked AGAIN inside the writer callback.
    /// These checks do not lock the revision or permit a consumer to commit it.
    /// # Errors
    /// Any observed denial permanently poisons this candidate, even after
    /// ACL regrant or blob restoration. No failed check can invoke the consumer.
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
                    final_access(&self.source, provider, now)?;
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
    /// Fresh verification without re-lowering or exporting candidate bytes.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<&StoredBookmarkInsertionReceipt, E>
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
    /// Current source access remains distinct from a registered execution route.
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
