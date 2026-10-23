//! Current authorized whole-source proof -> actual HWPX note-file candidate.
//! Retained metadata may contain source data; no ingest/CAS/Native/publication grant.
use super::*;
use hwpx_package::{NoteHwpxLimits,WriterLimits,document_import::structure::note_export::{
    NoteFileExportCandidate,NoteFileExportError,NoteFileExportReceipt,NoteFileSelection,
    note_file_export_request_sha256,
}};

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredNoteFileReceipt {
    pub source:StoredActualFormImportReceipt,
    pub requested_selection:NoteFileSelection,
    pub requested_notes:usize,
    pub requested_sha256:[u8;32],
    pub output:NoteFileExportReceipt,
    pub qualification:&'static str,
    pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredNoteFileCandidate<'a> {
    source:NoteFileSource<'a>,output:NoteFileExportCandidate,receipt:StoredNoteFileReceipt,
}
enum NoteFileSource<'a> {Borrowed(&'a StoredImportedDocumentForms),Owned(Box<StoredImportedDocumentForms>)}
impl std::ops::Deref for NoteFileSource<'_> {
    type Target=StoredImportedDocumentForms;
    fn deref(&self)->&Self::Target {match self {Self::Borrowed(s)=>s,Self::Owned(s)=>s}}
}
impl fmt::Debug for PreparedStoredNoteFileCandidate<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredNoteFileCandidate(<redacted>; not_native_CAS_or_execution_authority)")}
}
#[derive(Debug,Error)]
pub enum StoredNoteFileError {
    #[error("stored note file source access rejected")] Source(#[from] StoredActualFormImportError),
    #[error("stored note file output rejected")] Output(#[from] NoteFileExportError),
    #[error("stored note file source/request/output binding rejected")] Binding,
    #[error("stored note file document.write scope required")] Permission,
    #[error("stored note file executable route unqualified")] RouteUnqualified,
}
type E=StoredNoteFileError;
impl StoredImportedDocumentForms {
    /// Fresh original scope/head/ACL/quarantine/AEAD and whole Form proof. The
    /// same operation-local proof avoids a second full input reconstruction.
    /// # Errors
    /// Rejects current access/source drift and all original file compiler errors.
    pub fn prepare_note_file_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        selection:NoteFileSelection,limits:NoteHwpxLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNoteFileCandidate<'_>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)=self.build_note_file_candidate(provider,selection,limits,writer,now)?;
        Ok(PreparedStoredNoteFileCandidate {source:NoteFileSource::Borrowed(self),output,receipt})
    }
    // Ownership handoff, not a clone/reimport or a new authorization policy.
    pub(crate) fn into_note_file_candidate<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,
        selection:NoteFileSelection,limits:NoteHwpxLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNoteFileCandidate<'static>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(output,receipt)=self.build_note_file_candidate(provider,selection,limits,writer,now)?;
        Ok(PreparedStoredNoteFileCandidate {source:NoteFileSource::Owned(Box::new(self)),output,receipt})
    }
    fn build_note_file_candidate<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,
        selection:NoteFileSelection,limits:NoteHwpxLimits,writer:WriterLimits,now:u64)->Result<(NoteFileExportCandidate,StoredNoteFileReceipt),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let requested_sha256=note_file_export_request_sha256(*fresh.digest.as_bytes(),selection);
        let requested_notes=self.notes().iter().filter(|n|match selection {
            NoteFileSelection::Both=>true,NoteFileSelection::Footnotes=>n.native_kind=="footNote",NoteFileSelection::Endnotes=>n.native_kind=="endNote",
        }).count();
        let output=proof.export_note_file_candidate(&self.imported,&fresh.bytes,selection,limits,writer)?;
        if output.receipt().source_package_sha256!=*fresh.digest.as_bytes()||output.receipt().request_sha256!=requested_sha256
            ||output.receipt().selection!=selection||output.receipt().selected_notes!=requested_notes
            ||output.receipt().note_container_layout_and_native_numbering_qualified||output.receipt().native_save_reopen_render_qualified
            ||output.receipt().complete_protection_qualified||output.receipt().execution_publication_authority
            ||!output.receipt().non_body_metadata_and_resources_may_contain_source_data {return Err(E::Binding);}
        provider.check_head(fresh.head).map_err(StoredActualFormImportError::from)?;
        let receipt=StoredNoteFileReceipt {source:self.receipt.clone(),requested_selection:selection,requested_notes,requested_sha256,
            output:output.receipt().clone(),qualification:"fresh_service_bound_HWPX_note_file_not_redaction_native_container_layout_numbering_full_protection_issuer_CAS_execution_or_publication",
            issuer_execution_publication_authority:false};
        Ok((output,receipt))
    }
}
impl<R,B,S,V> StoredFormProvider<'_,R,B,S,V>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
    // Trusted provider scope only; no artifact read or new ACL/issuer grant.
    pub(crate) fn note_file_product_scope(&self,project:&domain_ir::ProjectId,document:&domain_ir::DocumentId)->Result<[u8;32],E> {
        use artifact_service::AuthScope;
        use sha2::{Digest as _,Sha256};
        if !self.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        if project.as_str()!=self.scope.project.public_id()||document!=&self.scope.document{return Err(E::Binding);}
        let binding=serde_json::to_vec(&("hwpx-agent.note-file-provider-scope/v1",self.scope.tenant.as_uuid(),
            self.scope.subject.hex(),self.scope.project.public_id(),self.scope.branch.public_id(),self.scope.document.as_str())).map_err(|_|E::Binding)?;
        Ok(Sha256::digest(binding).into())
    }
}
impl PreparedStoredNoteFileCandidate<'_> {
    #[must_use] pub const fn receipt(&self)->&StoredNoteFileReceipt {&self.receipt}
    fn fresh<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let fresh=self.source.fresh_source(provider,now)?;
        if self.receipt.source!=self.source.receipt||&self.receipt.output!=self.output.receipt()
            ||self.receipt.output.source_package_sha256!=*fresh.digest.as_bytes()
            ||self.receipt.requested_sha256!=note_file_export_request_sha256(*fresh.digest.as_bytes(),self.receipt.requested_selection)
            ||self.receipt.requested_sha256!=self.receipt.output.request_sha256||self.receipt.requested_selection!=self.receipt.output.selection
            ||self.receipt.requested_notes!=self.receipt.output.selected_notes||self.receipt.issuer_execution_publication_authority
            ||self.receipt.output.execution_publication_authority||self.receipt.output.complete_protection_qualified
            ||self.receipt.output.native_save_reopen_render_qualified||self.receipt.output.note_container_layout_and_native_numbering_qualified
            ||!self.receipt.output.non_body_metadata_and_resources_may_contain_source_data {return Err(E::Binding);}Ok(())
    }
    /// Current authorized original, immutable file integrity and final head only.
    /// # Errors
    /// Rejects source/access/head/integrity drift; no retained receipt is a grant.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredNoteFileReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;self.output.with_verified_bytes(|_|())?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// The final head is checked inside the verified writer callback before
    /// handing bytes to the consumer. These reads are not a lock or atomic CAS.
    /// # Errors
    /// Never invokes the consumer after rejected source/access/head/integrity.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,
        consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh(provider,now)?;
        self.output.with_verified_bytes(|bytes|{
            provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(bytes))
        })?
    }
    /// # Errors
    /// Always denies executable routes, including after successful verification.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
