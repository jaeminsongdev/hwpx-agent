//! Fresh service source + original whole-source proof + note-kind candidate.
//! No ingest, commit, execution route, cached authority or native recalculation.
use super::*;
use hwpx_package::{NoteHwpxLimits, WriterLimits, document_import::structure::note_conversion::{
    NoteKindConversion, NoteKindConversionCandidate, NoteKindConversionError,
    NoteKindConversionReceipt, note_kind_conversion_request_sha256,
}};

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredNoteKindConversionReceipt {
    pub source: StoredActualFormImportReceipt,
    pub requested_batch_sha256: [u8; 32],
    pub requested_notes: usize,
    pub output: NoteKindConversionReceipt,
    pub qualification: &'static str,
    pub issuer_execution_publication_authority: bool,
}
pub struct PreparedStoredNoteKindCandidate<'a> {
    source: &'a StoredImportedDocumentForms,
    output: NoteKindConversionCandidate,
    receipt: StoredNoteKindConversionReceipt,
}
impl fmt::Debug for PreparedStoredNoteKindCandidate<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredNoteKindCandidate(<redacted>; not_native_CAS_or_execution_authority)")
    }
}
#[derive(Debug, Error)]
pub enum StoredNoteKindConversionError {
    #[error("stored note conversion source access rejected")]
    Source(#[from] StoredActualFormImportError),
    #[error("stored note conversion output rejected")]
    Output(#[from] NoteKindConversionError),
    #[error("stored note conversion source/request/output binding rejected")]
    Binding,
    #[error("stored note conversion artifact integrity rejected")]
    Integrity,
    #[error("stored note conversion executable route unqualified")]
    RouteUnqualified,
}
type E = StoredNoteKindConversionError;
impl StoredImportedDocumentForms {
    /// Fresh original scope/head/ACL/quarantine/AEAD and whole Form proof are
    /// required before lowering. Only normal source-read audits are emitted.
    /// # Errors
    /// Rejects current source/access drift and every original compiler rejection.
    pub fn prepare_note_kind_candidate<R, B, S, V>(
        &self, provider: &StoredFormProvider<'_, R, B, S, V>,
        requests: &[NoteKindConversion<'_>], limits: NoteHwpxLimits, writer: WriterLimits, now: u64,
    ) -> Result<PreparedStoredNoteKindCandidate<'_>, E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        let (fresh, proof) = self.fresh_source_reconstructed(provider, now)?;
        let request_sha256 = note_kind_conversion_request_sha256(*fresh.digest.as_bytes(), requests, limits)?;
        let output = proof.lower_note_kind_batch_candidate(&self.imported, &fresh.bytes, requests, limits, writer)?;
        if output.receipt().source_package_sha256 != *fresh.digest.as_bytes()
            || output.receipt().request_sha256 != request_sha256
            || output.receipt().converted_notes != requests.len()
            || output.receipt().execution_publication_authority
            || output.receipt().native_number_recalculation_qualified
            || output.receipt().complete_protection_qualified { return Err(E::Binding); }
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        let receipt = StoredNoteKindConversionReceipt {
            source: self.receipt.clone(), requested_batch_sha256: request_sha256, requested_notes: requests.len(),
            output: output.receipt().clone(),
            qualification: "fresh_service_bound_source_note_kind_candidate_not_native_numbering_full_protection_issuer_CAS_execution_or_publication",
            issuer_execution_publication_authority: false,
        };
        Ok(PreparedStoredNoteKindCandidate { source: self, output, receipt })
    }
}
impl PreparedStoredNoteKindCandidate<'_> {
    #[must_use]
    pub const fn receipt(&self) -> &StoredNoteKindConversionReceipt { &self.receipt }

    fn fresh<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64) -> Result<(), E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        // Every exposure reconstructs current authorized source; the retained
        // candidate, receipt or source observation is never a retained grant.
        let fresh = self.source.fresh_source(provider, now)?;
        if self.receipt.source != self.source.receipt || &self.receipt.output != self.output.receipt()
            || self.receipt.output.source_package_sha256 != *fresh.digest.as_bytes()
            || self.receipt.requested_batch_sha256 != self.receipt.output.request_sha256
            || self.receipt.requested_notes != self.receipt.output.converted_notes
            || self.receipt.issuer_execution_publication_authority
            || self.receipt.output.execution_publication_authority
            || self.receipt.output.native_number_recalculation_qualified
            || self.receipt.output.complete_protection_qualified { return Err(E::Binding); }
        Ok(())
    }
    /// Fresh source access, writer integrity and final head verification only.
    /// # Errors
    /// Rejects access/source/head/integrity drift without granting execution.
    pub fn verify<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64)
        -> Result<StoredNoteKindConversionReceipt, E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        self.fresh(provider, now)?;
        self.output.with_verified_bytes(|_| ()).map_err(|_| E::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
        Ok(self.receipt.clone())
    }
    /// Checks the final head inside the writer callback, before the consumer.
    /// Source reads are not a held lock, atomic CAS or publication authority.
    /// # Errors
    /// Never calls the consumer after a failed source/head/integrity check.
    pub fn with_verified_bytes<R, B, S, V, T>(
        &self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64, consume: impl FnOnce(&[u8]) -> T,
    ) -> Result<T, E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        self.fresh(provider, now)?;
        self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
            Ok(consume(bytes))
        }).map_err(|_| E::Integrity)?
    }
    /// # Errors
    /// Always refuses executable routes, even after successful verification.
    pub fn require_current_product_route<R, B, S, V>(
        &self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64,
    ) -> Result<(), E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        self.verify(provider, now)?;
        Err(E::RouteUnqualified)
    }
}
