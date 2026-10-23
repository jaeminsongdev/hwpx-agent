//! Strict product note-file preparation, not a CLI route, key claim or publication.
use super::{UniqueJson,bounded,digest};
use crate::form_stored_provider::{StoredFormProvider,actual_import::{StoredActualFormImportError,
    note_export_output::{PreparedStoredNoteFileCandidate,StoredNoteFileError,StoredNoteFileReceipt}}};
use artifact_service::{ArtifactMetadataRepository,ArtifactScanner,EncryptedBlobStore};
use domain_ir::{DocumentId,IdempotencyKey,PlanId,ProjectId,RevisionId};
use hwpx_package::{NoteHwpxLimits,WriterLimits,document_import::structure::note_export::NoteFileSelection};
use revision_service::{RevisionHead,RevisionRepository};
use serde::{Deserialize,Serialize};
use std::fmt;
use thiserror::Error;

pub const NOTE_FILE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-note-file-request/v1";
pub const NOTE_FILE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-note-file-preparation/v1";
pub const NOTE_FILE_PRODUCT_MAX_REQUEST_BYTES:usize=16*1024;
#[derive(Clone,Copy,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Selection {Footnotes,Endnotes,Both}
impl Selection {fn pick(self)->NoteFileSelection {match self {Self::Footnotes=>NoteFileSelection::Footnotes,Self::Endnotes=>NoteFileSelection::Endnotes,Self::Both=>NoteFileSelection::Both}}}
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind {ExportNoteFile}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation {kind:Kind,selection:Selection}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {
    schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,
    base_revision:RevisionId,expected_head_generation:u64,expected_source_package_sha256:String,
    plan_id:PlanId,operation:Operation,
}
impl Request {
    fn parse(raw:&[u8])->Result<Self,E> {
        if raw.is_empty()||raw.len()>NOTE_FILE_PRODUCT_MAX_REQUEST_BYTES{return Err(E::Limit);}
        let mut parser=serde_json::Deserializer::from_slice(raw);
        let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;
        let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
        if !value.is_object()||!value.get("operation").is_some_and(serde_json::Value::is_object){return Err(E::Request);}
        let request:Self=serde_json::from_value(value).map_err(|_|E::Request)?;
        if request.schema_version!=NOTE_FILE_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0
            ||request.document_id.as_str().len()>1024||request.expected_source_package_sha256.len()!=64
            ||!request.expected_source_package_sha256.bytes().all(|c|c.is_ascii_digit()||(b'a'..=b'f').contains(&c)) {return Err(E::Request);}
        request.head()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,E> {
        RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),self.expected_head_generation).map_err(|_|E::Request)
    }
    fn canonical_sha(&self)->Result<String,E> {Ok(digest(&bounded(self,NOTE_FILE_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {
        Ok(digest(&bounded(&(NOTE_FILE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),NOTE_FILE_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NoteFileProductReceipt {
    pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,
    pub stored:StoredNoteFileReceipt,pub idempotency_key_claimed:bool,
    pub issuer_native_cas_execution_publication_authority:bool,
}
pub struct PreparedStoredNoteFileProduct {request:Request,candidate:PreparedStoredNoteFileCandidate<'static>,receipt:NoteFileProductReceipt}
impl fmt::Debug for PreparedStoredNoteFileProduct {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredNoteFileProduct(<redacted>; preparation_only)")}
}
#[derive(Debug,Error)]
pub enum NoteFileProductError {
    #[error("NOTE_FILE_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("NOTE_FILE_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("NOTE_FILE_PRODUCT_SOURCE_OR_RECEIPT_BINDING_REJECTED")] Binding,
    #[error("NOTE_FILE_PRODUCT_SOURCE_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("NOTE_FILE_PRODUCT_STORED_CANDIDATE_REJECTED")] Stored(#[from] StoredNoteFileError),
    #[error("NOTE_FILE_PRODUCT_EXECUTABLE_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type E=NoteFileProductError;
#[derive(Debug)]
pub struct StoredNoteFileProductRequest;
impl StoredNoteFileProductRequest {
    /// Source is selected only by the authenticated provider's sealed current head.
    /// # Errors
    /// Rejects malformed JSON before reads, absent write scope and stale/foreign source.
    /// No caller Form graph, artifact/path, validator verdict or approval bit is accepted.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:NoteHwpxLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNoteFileProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;let scope=provider.note_file_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
        let candidate=source.into_note_file_candidate(provider,request.operation.selection.pick(),limits,writer,now)?;
        let receipt=NoteFileProductReceipt {profile:NOTE_FILE_PRODUCT_PREPARATION_PROFILE,capability_id:"ref.note_export",
            raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,
            stored:candidate.receipt().clone(),idempotency_key_claimed:false,issuer_native_cas_execution_publication_authority:false};
        let result=PreparedStoredNoteFileProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredNoteFileProduct {
    #[must_use] pub const fn receipt(&self)->&NoteFileProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let scope=provider.note_file_product_scope(&self.request.project_id,&self.request.document_id)?;
        if self.receipt.profile!=NOTE_FILE_PRODUCT_PREPARATION_PROFILE||self.receipt.capability_id!="ref.note_export"
            ||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?
            ||&self.receipt.stored!=self.candidate.receipt()||self.receipt.stored.requested_selection!=self.request.operation.selection.pick()
            ||hex::encode(self.receipt.stored.output.source_package_sha256)!=self.request.expected_source_package_sha256
            ||self.receipt.stored.source.head_generation!=self.request.expected_head_generation||self.receipt.idempotency_key_claimed
            ||self.receipt.issuer_native_cas_execution_publication_authority{return Err(E::Binding);}Ok(())
    }
    /// Reauthorizes write scope and all original stored source/output checks.
    /// # Errors
    /// Retained envelopes and receipt clones never bypass fresh access/head checks.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<NoteFileProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// No raw bytes getter: current authorization and final head precede consumption.
    /// # Errors
    /// Rejects write/read/source/head/output drift without calling the consumer.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// Always denies executable routes even after successful fresh preparation.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
