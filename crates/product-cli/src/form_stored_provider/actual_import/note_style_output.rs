//! Fresh authorized whole-source proof -> source note style output candidate.
//! Not ingest, CAS, execution, publication, complete protection or native layout.
use super::*;
use hwpx_package::{NoteHwpxLimits, WriterLimits, document_import::structure::note_style::{
    NoteStyleCandidate, NoteStyleError, NoteStyleReceipt, NoteStyleReplacement, note_style_request_sha256,
}};

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StoredNoteStyleReceipt {
    pub source: StoredActualFormImportReceipt,
    pub requested_batch_sha256: [u8; 32],
    pub requested_styles: usize,
    pub output: NoteStyleReceipt,
    pub qualification: &'static str,
    pub issuer_execution_publication_authority: bool,
}
pub struct PreparedStoredNoteStyleCandidate<'a> {
    source: &'a StoredImportedDocumentForms,
    output: NoteStyleCandidate,
    receipt: StoredNoteStyleReceipt,
}
impl fmt::Debug for PreparedStoredNoteStyleCandidate<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedStoredNoteStyleCandidate(<redacted>; not_native_CAS_or_execution_authority)")
    }
}
#[derive(Debug, Error)]
pub enum StoredNoteStyleError {
    #[error("stored note style source access rejected")] Source(#[from] StoredActualFormImportError),
    #[error("stored note style output rejected")] Output(#[from] NoteStyleError),
    #[error("stored note style source/request/output binding rejected")] Binding,
    #[error("stored note style artifact integrity rejected")] Integrity,
    #[error("stored note style executable route unqualified")] RouteUnqualified,
}
type E = StoredNoteStyleError;
impl StoredImportedDocumentForms {
    /// Requires current scope/head/ACL/quarantine/AEAD and original whole Form
    /// reconstruction. Reuses that operation-local proof; no second input import.
    /// # Errors
    /// Rejects current source/access drift and every original compiler failure.
    pub fn prepare_note_style_candidate<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>,
        requests: &[NoteStyleReplacement<'_>], limits: NoteHwpxLimits, writer: WriterLimits, now: u64,
    ) -> Result<PreparedStoredNoteStyleCandidate<'_>, E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        let (fresh, proof) = self.fresh_source_reconstructed(provider, now)?;
        let request_sha256 = note_style_request_sha256(*fresh.digest.as_bytes(), requests, limits)?;
        let output = proof.lower_note_style_batch_candidate(&self.imported, &fresh.bytes, requests, limits, writer)?;
        if output.receipt().source_package_sha256 != *fresh.digest.as_bytes()
            || output.receipt().request_sha256 != request_sha256
            || output.receipt().replaced_styles != requests.len()
            || output.receipt().execution_publication_authority
            || output.receipt().native_layout_and_numbering_qualified
            || output.receipt().complete_protection_qualified { return Err(E::Binding); }
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        let receipt = StoredNoteStyleReceipt {
            source: self.receipt.clone(), requested_batch_sha256: request_sha256, requested_styles: requests.len(),
            output: output.receipt().clone(),
            qualification: "fresh_service_bound_source_note_style_candidate_not_native_layout_numbering_full_protection_issuer_CAS_execution_or_publication",
            issuer_execution_publication_authority: false,
        };
        Ok(PreparedStoredNoteStyleCandidate { source: self, output, receipt })
    }
}
impl PreparedStoredNoteStyleCandidate<'_> {
    #[must_use] pub const fn receipt(&self) -> &StoredNoteStyleReceipt { &self.receipt }
    fn fresh<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64) -> Result<(), E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        let fresh = self.source.fresh_source(provider, now)?;
        if self.receipt.source != self.source.receipt || &self.receipt.output != self.output.receipt()
            || self.receipt.output.source_package_sha256 != *fresh.digest.as_bytes()
            || self.receipt.requested_batch_sha256 != self.receipt.output.request_sha256
            || self.receipt.requested_styles != self.receipt.output.replaced_styles
            || self.receipt.issuer_execution_publication_authority
            || self.receipt.output.execution_publication_authority
            || self.receipt.output.native_layout_and_numbering_qualified
            || self.receipt.output.complete_protection_qualified { return Err(E::Binding); }
        Ok(())
    }
    /// Fresh source access, writer integrity and final head only, not authority.
    /// # Errors
    /// Rejects access/source/head/integrity drift before returning a receipt.
    pub fn verify<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64) -> Result<StoredNoteStyleReceipt, E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        self.fresh(provider, now)?;
        self.output.with_verified_bytes(|_| ()).map_err(|_| E::Integrity)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
        Ok(self.receipt.clone())
    }
    /// Final head is checked inside the writer callback, before the consumer.
    /// Read checks are not a held lock or atomic compare-and-swap publication.
    /// # Errors
    /// Never calls the consumer after source/access/head/integrity rejection.
    pub fn with_verified_bytes<R, B, S, V, T>(&self, provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64, consume: impl FnOnce(&[u8]) -> T) -> Result<T, E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        self.fresh(provider, now)?;
        self.output.with_verified_bytes(|bytes| {
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;
            Ok(consume(bytes))
        }).map_err(|_| E::Integrity)?
    }
    /// # Errors
    /// Always refuses executable routes, including after successful verification.
    pub fn require_current_product_route<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>, now: u64) -> Result<(), E>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        self.verify(provider, now)?;
        Err(E::RouteUnqualified)
    }
}
