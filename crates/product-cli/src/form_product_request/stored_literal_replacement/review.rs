//! Strict v3 review-body policy; existing v1/v2 requests stay separate.
use super::*;
compiler_product!(PreparedStoredReviewLiteralProduct, request.base, plain);
search_lookup_product!(StoredReviewLiteralProductRequest,|raw|ReviewRequest::parse(raw),base,normal,no_preview);
use crate::form_stored_provider::actual_import::literal_search_output::atoms::review::{PreparedStoredReviewLiteralCandidate,StoredReviewLiteralReceipt};
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,
    replacement::atoms::review::SOURCE_REVIEW_LITERAL_PROFILE};
pub const REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-literal-replacement-request/v3";
pub const REVIEW_LITERAL_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-literal-replacement-preparation/v3";
pub const REVIEW_LITERAL_PRODUCT_MAX_REQUEST_BYTES:usize=LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES;
struct ReviewRequest {base:Request,policy:SourceReviewTextPolicy}
impl ReviewRequest {
    fn parse(raw:&[u8])->Result<Self,E> {
        let mut value=Request::parse_object(raw)?;
        let policy=value.get_mut("operation").and_then(serde_json::Value::as_object_mut)
            .and_then(|operation|operation.remove("review_policy")).ok_or(E::Request)?;
        if !policy.is_object(){return Err(E::Request);}
        let policy=serde_json::from_value(policy).map_err(|_|E::Request)?;
        let base=Request::parse_value(value,REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA)?;
        let request=Self {base,policy};request.canonical_sha()?;Ok(request)
    }
    fn canonical_sha(&self)->Result<String,E> {
        // Rebuild only the bounded request value; never duplicate source packages or output.
        let mut value=serde_json::to_value(&self.base).map_err(|_|E::Request)?;
        value.get_mut("operation").and_then(serde_json::Value::as_object_mut).ok_or(E::Request)?
            .insert("review_policy".to_owned(),serde_json::to_value(self.policy).map_err(|_|E::Request)?);
        Ok(digest(&bounded(&value,REVIEW_LITERAL_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))
    }
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {
        Ok(digest(&bounded(&(REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),REVIEW_LITERAL_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))
    }
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ReviewLiteralProductReceipt {pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredReviewLiteralReceipt,
    pub idempotency_key_claimed:bool,pub full_search_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredReviewLiteralProduct {request:ReviewRequest,candidate:PreparedStoredReviewLiteralCandidate<'static>,receipt:ReviewLiteralProductReceipt}
impl fmt::Debug for PreparedStoredReviewLiteralProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredReviewLiteralProduct(<redacted>; candidate_only)")}}
#[derive(Debug)]
pub struct StoredReviewLiteralProductRequest;
impl StoredReviewLiteralProductRequest {
    /// # Errors
    /// Strict original envelope/value checks and both policy Booleans before source reads.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredReviewLiteralProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=ReviewRequest::parse(raw)?;let base=&request.base;
        let scope=provider.source_search_product_scope(&base.project_id,&base.document_id)?;
        let source=provider.import_actual_forms(base.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=base.expected_source_package_sha256{return Err(E::Binding);}
        let candidate=source.into_review_literal_candidate(provider,base.query(),base.scope(),request.policy,&base.operation.replacement,base.operation.run_policy.native(),limits,writer,now)?;
        let receipt=ReviewLiteralProductReceipt {profile:REVIEW_LITERAL_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_literal",
            raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,
            stored:candidate.receipt().clone(),idempotency_key_claimed:false,full_search_native_cas_execution_publication_authority:false};
        let result=PreparedStoredReviewLiteralProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredReviewLiteralProduct {
    #[must_use] pub const fn receipt(&self)->&ReviewLiteralProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let base=&self.request.base;let source=&self.receipt.stored.output;let output=&source.output;
        let scope=provider.source_search_product_scope(&base.project_id,&base.document_id)?;
        if base.schema_version!=REVIEW_LITERAL_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=REVIEW_LITERAL_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.replace_literal"||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.source.head_generation!=base.expected_head_generation
            ||hex::encode(output.source_package_sha256)!=base.expected_source_package_sha256
            ||output.replacement_bytes!=base.operation.replacement.len()||hex::encode(output.replacement_sha256)!=digest(base.operation.replacement.as_bytes())
            ||output.run_policy!=base.operation.run_policy.native()||output.matched_occurrences>base.operation.max_replacements
            ||source.body_policy!=self.request.policy||source.profile!=SOURCE_REVIEW_LITERAL_PROFILE||output.profile!=SOURCE_REVIEW_LITERAL_PROFILE
            ||!source.memo_payload_not_cached_result_verified||source.native_author_visibility_resolution_or_execution_qualified
            ||output.field_cached_content_edit_qualified||output.full_protection_native_or_execution_authority
            ||output.control_atom_replacement_qualified||!output.original_control_bytes_preserved
            ||self.receipt.idempotency_key_claimed||self.receipt.full_search_native_cas_execution_publication_authority {return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/head checks, without repeating query or lowering.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<ReviewLiteralProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// The original stored final consumer head boundary remains inside the writer callback.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// A prepared candidate is not a dispatcher, durable key claim, revision CAS or execution grant.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.verify(provider,now)?;Err(E::RouteUnqualified)
    }
}
