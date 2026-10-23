//! Strict v6 review-aware selector requests; v5 and older meanings remain separate.
use super::*;
use crate::form_stored_provider::actual_import::source_search::review_selector::SourceReviewScopeOperation;
pub const REVIEW_SCOPE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-source-search-request/v6";
pub const REVIEW_SCOPE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-source-search-preparation/v6";
struct ReviewRequest {base:Request,policy:Option<SourceReviewTextPolicy>}
impl ReviewRequest {
    fn parse(raw:&[u8])->Result<Self,E> {
        let mut value=Request::parse_object(raw)?;
        let policy=value.get_mut("operation").and_then(serde_json::Value::as_object_mut).ok_or(E::Request)?.remove("review_policy")
            .map(|v|if v.is_object(){serde_json::from_value(v).map_err(|_|E::Request)}else{Err(E::Request)}).transpose()?;
        let base=Request::parse_value(value,REVIEW_SCOPE_PRODUCT_REQUEST_SCHEMA)?;
        if base.operation.query().is_some()!=policy.is_some(){return Err(E::Request);}
        let request=Self {base,policy};request.canonical_sha()?;Ok(request)
    }
    fn canonical_sha(&self)->Result<String,E> {
        let mut value=serde_json::to_value(&self.base).map_err(|_|E::Request)?;
        if let Some(policy)=self.policy{value.get_mut("operation").and_then(serde_json::Value::as_object_mut).ok_or(E::Request)?
            .insert("review_policy".to_owned(),serde_json::to_value(policy).map_err(|_|E::Request)?);}
        Ok(digest(&bounded(&value,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))
    }
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {Ok(digest(&bounded(&(REVIEW_SCOPE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
}
pub struct PreparedStoredReviewScopeProduct {request:ReviewRequest,candidate:PreparedStoredSourceSearch,receipt:SourceSearchProductReceipt}
impl fmt::Debug for PreparedStoredReviewScopeProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredReviewScopeProduct(<redacted>; source_windows_not_native_flow)")}}
#[derive(Debug)]
pub struct StoredReviewScopeProductRequest;
impl StoredReviewScopeProductRequest {
    /// # Errors
    /// Strict revision-bound selector and explicit search policy before original source access.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,now:u64)->Result<PreparedStoredReviewScopeProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=ReviewRequest::parse(raw)?;let base=&request.base;
        let scope=provider.source_search_product_scope(&base.project_id,&base.document_id)?;
        let source=provider.import_actual_forms(base.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=base.expected_source_package_sha256{return Err(E::Binding);}
        let operation=match(base.operation.query(),request.policy){(Some(query),Some(policy))=>SourceReviewScopeOperation::Find {query,selector:base.selector.native()?,policy},
            (None,None)=>SourceReviewScopeOperation::Inventory,_=>return Err(E::Request)};
        let candidate=source.into_review_source_scope(provider,operation,limits,now)?;
        let receipt=SourceSearchProductReceipt {profile:REVIEW_SCOPE_PRODUCT_PREPARATION_PROFILE,capability_id:base.operation.capability(),raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_search_product_native_cas_execution_publication_authority:false};
        let result=PreparedStoredReviewScopeProduct {request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredReviewScopeProduct {
    /// # Errors
    /// The immutable full Find receipt binds raw request, key/plan, selector and explicit policy.
    pub fn navigation_receipt_sha256(&self)->Result<String,E> {
        if self.request.base.operation.query().is_none(){return Err(E::Request);}
        Ok(hex::encode(super::super::navigation::receipt_context(&self.receipt)?))
    }
    /// # Errors
    /// Keeps fresh source/ACL/AEAD/final-head checks and region labels without rerunning search.
    pub fn with_next_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(request,context)=super::super::navigation::bound_next(raw,&self.receipt)?;
        if self.request.base.operation.query().is_none(){return Err(E::Request);}self.check(provider)?;
        Ok(self.candidate.with_next_verified_json(provider,&request,context,now,consume)?)
    }
    #[must_use] pub const fn receipt(&self)->&SourceSearchProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let base=&self.request.base;let scope=provider.source_search_product_scope(&base.project_id,&base.document_id)?;
        if base.schema_version!=REVIEW_SCOPE_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=REVIEW_SCOPE_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!=base.operation.capability()||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!="hwpx-agent.stored-source-search/v6"||self.receipt.stored.source.head_generation!=base.expected_head_generation
            ||base.selector.revision_id!=base.base_revision||base.operation.query().is_some()!=self.request.policy.is_some()
            ||hex::encode(self.receipt.stored.index.source_package_sha256)!=base.expected_source_package_sha256
            ||self.receipt.idempotency_key_claimed||self.receipt.full_search_product_native_cas_execution_publication_authority{return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Current stored access/source/head verification, without inventory or query replay.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<SourceSearchProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retain the original current access checks and final consumer head before disclosure.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_json(provider,now,consume)?)
    }
    /// # Errors
    /// Neither an executable dispatcher nor an idempotency, commit, CAS or Native grant.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(E::RouteUnqualified)}
}
