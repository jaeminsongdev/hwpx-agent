//! Strict v2 mixed-TextSpan preparation; v1 remains a separate plain-only request.
use super::*;
compiler_product!(PreparedStoredLiteralTextAtomProduct, request, plain);
use crate::form_stored_provider::actual_import::literal_search_output::atoms::{PreparedStoredLiteralTextAtomCandidate,StoredLiteralTextAtomReceipt};
use hwpx_package::document_import::search::replacement::atoms::SOURCE_LITERAL_TEXT_ATOM_PROFILE;
pub const LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-literal-replacement-request/v2";
pub const LITERAL_TEXT_ATOM_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-literal-replacement-preparation/v2";
pub const LITERAL_TEXT_ATOM_PRODUCT_MAX_REQUEST_BYTES:usize=LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct LiteralTextAtomProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredLiteralTextAtomReceipt,
    pub idempotency_key_claimed:bool,pub full_search_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredLiteralTextAtomProduct {request:Request,candidate:PreparedStoredLiteralTextAtomCandidate<'static>,receipt:LiteralTextAtomProductReceipt}
impl fmt::Debug for PreparedStoredLiteralTextAtomProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredLiteralTextAtomProduct(<redacted>; candidate_only)")}}
#[derive(Debug)]
pub struct StoredLiteralTextAtomProductRequest;
impl StoredLiteralTextAtomProductRequest {
    /// # Errors
    /// The original strict parser/value policy, with explicit v2 identity before source reads.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredLiteralTextAtomProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse_profile(raw,LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
        let candidate=source.into_literal_text_atom_candidate(provider,request.query(),request.scope(),&request.operation.replacement,request.operation.run_policy.native(),limits,writer,now)?;
        let receipt=LiteralTextAtomProductReceipt {profile:LITERAL_TEXT_ATOM_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_literal",
            raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,
            scoped_request_sha256:request.scoped_sha_profile(scope,LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_search_native_cas_execution_publication_authority:false};
        let result=PreparedStoredLiteralTextAtomProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredLiteralTextAtomProduct {
    #[must_use] pub const fn receipt(&self)->&LiteralTextAtomProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let scope=provider.source_search_product_scope(&self.request.project_id,&self.request.document_id)?;
        if self.request.schema_version!=LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=LITERAL_TEXT_ATOM_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.replace_literal"||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=self.request.scoped_sha_profile(scope,LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA)?
            ||&self.receipt.stored!=self.candidate.receipt()||self.receipt.stored.source.head_generation!=self.request.expected_head_generation
            ||hex::encode(self.receipt.stored.output.source_package_sha256)!=self.request.expected_source_package_sha256
            ||self.receipt.stored.output.replacement_bytes!=self.request.operation.replacement.len()
            ||hex::encode(self.receipt.stored.output.replacement_sha256)!=digest(self.request.operation.replacement.as_bytes())
            ||self.receipt.stored.output.run_policy!=self.request.operation.run_policy.native()
            ||self.receipt.stored.output.matched_occurrences>self.request.operation.max_replacements||self.receipt.idempotency_key_claimed
            ||self.receipt.stored.output.profile!=SOURCE_LITERAL_TEXT_ATOM_PROFILE||self.receipt.stored.output.control_atom_replacement_qualified
            ||!self.receipt.stored.output.original_control_bytes_preserved||self.receipt.full_search_native_cas_execution_publication_authority {return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Current source/access/writer/head checks, not query replay or a commit grant.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<LiteralTextAtomProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final stored consumer check is retained; saved receipts never authorize access.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// No dispatcher, durable key claim, CAS, Native execution or publication grant.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
