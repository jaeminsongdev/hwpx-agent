//! Current authorized sealed source -> immutable mapped-source search result.
pub mod navigation;
pub mod selector;
pub mod review_selector;
pub mod review_styles;
pub mod review_controls;
pub mod resolved_styles;
pub mod personal_info;
pub mod personal_info_catalog;
pub mod request_recovery;
use super::*;
use artifact_service::AuthScope;
use domain_ir::{DocumentId,ProjectId};
use hwpx_package::document_import::search::{SourceSearchError,SourceSearchLimits,SourceSearchQuery,
    SourceSearchIndexReceipt,scope::{SourceSearchScope,ScopedSourceSearchResult,SourceSearchScopeReceipt}};
use hwpx_package::document_import::search::inspection::{SourceInspectionResult,SourceDeclaredStyleFilter,SourceControlKind};
use hwpx_package::document_import::search::inspection::definitions::{SourceDefinitionStyleResult,SourceDefinitionStyleFilter};
use hwpx_package::document_import::search::reviews::{SourceReviewTextResult,SourceReviewTextPolicy};
use sha2::{Digest as _,Sha256};

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct StoredSourceSearchReceipt {
    pub profile:&'static str,pub source:StoredActualFormImportReceipt,pub index:SourceSearchIndexReceipt,
    pub scope:SourceSearchScopeReceipt,pub query_sha256:[u8;32],pub result_sha256:[u8;32],
    pub full_search_product_or_native_qualified:bool,pub issuer_execution_publication_authority:bool,
}
pub struct PreparedStoredSourceSearch {source:StoredImportedDocumentForms,result:SearchResult,receipt:StoredSourceSearchReceipt}
enum SearchResult {Text(ScopedSourceSearchResult),Inspection(SourceInspectionResult),Definitions(SourceDefinitionStyleResult),Reviews(SourceReviewTextResult),Scope(selector::ScopeResult),ReviewScope(review_selector::ReviewScopeResult),ReviewStyle(review_styles::ReviewStyleResult),ReviewControl(review_controls::ReviewControlResult),ResolvedStyle(resolved_styles::ResolvedStyleResult)}
impl SearchResult {
    fn index(&self)->&SourceSearchIndexReceipt {match self {Self::Text(r)=>r.result().index_receipt(),Self::Inspection(r)=>r.index_receipt(),Self::Definitions(r)=>r.index_receipt(),Self::Reviews(r)=>r.index_receipt(),Self::Scope(r)=>r.index(),Self::ReviewScope(r)=>r.index(),Self::ReviewStyle(r)=>r.index(),Self::ReviewControl(r)=>r.index(),Self::ResolvedStyle(r)=>r.index()}}
    fn scope(&self)->&SourceSearchScopeReceipt {match self {Self::Text(r)=>r.scope_receipt(),Self::Inspection(r)=>r.scope_receipt(),Self::Definitions(r)=>r.scope_receipt(),Self::Reviews(r)=>r.scope_receipt(),Self::Scope(r)=>&r.scope,Self::ReviewScope(r)=>&r.scope,Self::ReviewStyle(r)=>&r.scope,Self::ReviewControl(r)=>&r.scope,Self::ResolvedStyle(r)=>&r.scope}}
    fn request_sha(&self)->[u8;32] {match self {Self::Text(r)=>r.result().query_sha256(),Self::Inspection(r)=>r.request_sha256(),Self::Definitions(r)=>r.request_sha256(),Self::Reviews(r)=>r.request_sha256(),Self::Scope(r)=>r.request_sha,Self::ReviewScope(r)=>r.request_sha,Self::ReviewStyle(r)=>r.request_sha(),Self::ReviewControl(r)=>r.request_sha(),Self::ResolvedStyle(r)=>r.request_sha()}}
    fn json(&self)->Result<Vec<u8>,SourceSearchError> {match self {Self::Text(r)=>r.canonical_json(),Self::Inspection(r)=>r.canonical_json(),Self::Definitions(r)=>r.canonical_json(),Self::Reviews(r)=>r.canonical_json(),Self::Scope(r)=>r.json(),Self::ReviewScope(r)=>r.json(),Self::ReviewStyle(r)=>r.json(),Self::ReviewControl(r)=>r.json(),Self::ResolvedStyle(r)=>r.json()}}
    fn profile(&self)->&'static str {match self {Self::Text(_)=>"hwpx-agent.stored-source-search/v1",Self::Inspection(_)=>"hwpx-agent.stored-source-search/v2",Self::Definitions(_)=>"hwpx-agent.stored-source-search/v3",Self::Reviews(_)=>"hwpx-agent.stored-source-search/v4",Self::Scope(_)=>"hwpx-agent.stored-source-search/v5",Self::ReviewScope(_)=>"hwpx-agent.stored-source-search/v6",Self::ReviewStyle(_)=>"hwpx-agent.stored-source-search/v7",Self::ReviewControl(_)=>"hwpx-agent.stored-source-search/v8",Self::ResolvedStyle(_)=>"hwpx-agent.stored-source-search/v9"}}
}
#[derive(Clone,Copy,Debug)]
pub enum SourceInspectionOperation<'a> {DeclaredStyle {query:SourceSearchQuery<'a>,filter:SourceDeclaredStyleFilter},Control {kind:SourceControlKind,max_results:usize},
    DefinitionStyle {query:SourceSearchQuery<'a>,filter:SourceDefinitionStyleFilter}}
impl fmt::Debug for PreparedStoredSourceSearch {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredSourceSearch(<redacted>; mapped_source_only)")}
}
#[derive(Debug,Error)]
pub enum StoredSourceSearchError {
    #[error("STORED_SOURCE_STYLE_RESOLUTION_REJECTED")] Resolution(#[from] hwpx_package::document_import::search::reviews::selector::resolved_styles::SourceResolvedStyleSearchError),
    #[error("STORED_SOURCE_SEARCH_ACCESS_REJECTED")] Source(#[from] StoredActualFormImportError),
    #[error("STORED_SOURCE_SEARCH_REJECTED")] Search(#[from] SourceSearchError),
    #[error("STORED_SOURCE_SEARCH_BINDING_REJECTED")] Binding,
    #[error("STORED_SOURCE_SEARCH_DOCUMENT_WRITE_REQUIRED")] Permission,
    #[error("STORED_SOURCE_SEARCH_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type E=StoredSourceSearchError;
impl<R,B,S,V> StoredFormProvider<'_,R,B,S,V>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
    pub(crate) fn source_search_request_lookup(&self,project:&ProjectId,document:&DocumentId,key:&domain_ir::IdempotencyKey,canonical:&str,scoped:&str,source:artifact_service::ContentDigest,head:RevisionHead)
        ->Result<revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookup,E>{
        if !self.artifact_context.has_scope(AuthScope::DocumentRead){return Err(E::Permission);}
        self.source_search_job_identity(project,document,key,canonical,scoped)?.lookup(self.scope.branch,source,head).map_err(|_|E::Binding)
    }
    pub(crate) fn source_search_job_identity(&self,project:&ProjectId,document:&DocumentId,key:&domain_ir::IdempotencyKey,canonical:&str,scoped:&str)
        ->Result<crate::stored_revision_commit::job::identity::StoredRequestJobIdentity,E>{
        self.source_search_product_scope(project,document)?;
        crate::stored_revision_commit::job::identity::StoredRequestJobIdentity::bind(self.scope.tenant,self.scope.project,key,canonical,scoped).map_err(|_|E::Binding)
    }
    pub(crate) fn source_search_product_scope(&self,project:&ProjectId,document:&DocumentId)->Result<[u8;32],E> {
        if !self.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        if project.as_str()!=self.scope.project.public_id()||document!=&self.scope.document{return Err(E::Binding);}
        let bytes=serde_json::to_vec(&("hwpx-agent.source-search-provider-scope/v1",self.scope.tenant.as_uuid(),
            self.scope.subject.hex(),self.scope.project.public_id(),self.scope.branch.public_id(),self.scope.document.as_str())).map_err(|_|E::Binding)?;
        Ok(Sha256::digest(bytes).into())
    }
}
impl<R,B,S,V> StoredFormProvider<'_,R,B,S,V>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,
    V:revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookupRepository{
    pub(crate) fn observe_source_request(&self,lookup:&revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookup)
        ->Result<revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestObservation,
            revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookupError>{
        if !self.artifact_context.has_scope(AuthScope::DocumentRead)||!self.artifact_context.has_scope(AuthScope::DocumentWrite)
            ||lookup.project_id()!=self.scope.project||lookup.branch_id()!=self.scope.branch{return Err(revision_service::RevisionError::InvalidRequest.into());}
        self.revisions.repository().observe_request(self.revision_context,lookup)
    }
}
impl StoredImportedDocumentForms {
    /// # Errors
    /// Requires current document.write and the unchanged scope/head/ACL/AEAD reconstruction.
    pub fn into_source_search<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,
        scope:SourceSearchScope<'_>,limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceSearch,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let (fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let index=proof.source_text_index(&self.imported,limits)?;
        let result=SearchResult::Text(index.find_scoped(query,scope)?);
        if result.index().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        self.finish_search(provider,result,fresh.head)
    }
    /// # Errors
    /// Same current authorization/reconstruction, with only declared source semantics.
    pub fn into_source_inspection<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,operation:SourceInspectionOperation<'_>,
        scope:SourceSearchScope<'_>,limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceSearch,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let index=proof.source_text_index(&self.imported,limits)?;let inspection=index.inspection()?;
        let result=match operation {
            SourceInspectionOperation::DeclaredStyle {query,filter}=>SearchResult::Inspection(inspection.find_style(query,scope,filter)?),
            SourceInspectionOperation::Control {kind,max_results}=>SearchResult::Inspection(inspection.find_control(scope,kind,max_results)?),
            SourceInspectionOperation::DefinitionStyle {query,filter}=>SearchResult::Definitions(inspection.resolve_style_definitions()?.find(query,scope,filter)?),
        };
        if result.index().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        self.finish_search(provider,result,fresh.head)
    }
    /// # Errors
    /// Shares current whole-source proof and final head without building an unused style index.
    pub fn into_review_text_search<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,query:SourceSearchQuery<'_>,
        scope:SourceSearchScope<'_>,policy:SourceReviewTextPolicy,limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceSearch,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let(fresh,proof)=self.fresh_source_reconstructed(provider,now)?;
        let index=proof.source_review_text_index(&self.imported,limits)?;
        let result=SearchResult::Reviews(index.find(query,scope,policy)?);
        if result.index().source_package_sha256!=*fresh.digest.as_bytes(){return Err(E::Binding);}
        self.finish_search(provider,result,fresh.head)
    }
    fn finish_search<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,result:SearchResult,head:RevisionHead)->Result<PreparedStoredSourceSearch,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let bytes=result.json()?;
        let receipt=StoredSourceSearchReceipt {profile:result.profile(),source:self.receipt.clone(),
            index:result.index().clone(),scope:result.scope().clone(),
            query_sha256:result.request_sha(),result_sha256:Sha256::digest(&bytes).into(),
            full_search_product_or_native_qualified:false,issuer_execution_publication_authority:false};
        provider.check_head(head).map_err(StoredActualFormImportError::from)?;
        Ok(PreparedStoredSourceSearch {source:self,result,receipt})
    }
}
impl PreparedStoredSourceSearch {
    #[must_use] pub const fn receipt(&self)->&StoredSourceSearchReceipt {&self.receipt}
    fn fresh_json<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<Vec<u8>,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        if !provider.artifact_context.has_scope(AuthScope::DocumentWrite){return Err(E::Permission);}
        let fresh=self.source.fresh_source(provider,now)?;
        let bytes=self.result.json()?;
        if self.receipt.profile!=self.result.profile()||self.receipt.source!=self.source.receipt
            ||&self.receipt.index!=self.result.index()||&self.receipt.scope!=self.result.scope()
            ||self.receipt.query_sha256!=self.result.request_sha()
            ||self.receipt.index.source_package_sha256!=*fresh.digest.as_bytes()
            ||self.receipt.index.graph_sha256!=self.source.imported.receipt().body_graph_sha256
            ||self.receipt.result_sha256!=<[u8;32]>::from(Sha256::digest(&bytes))
            ||self.receipt.full_search_product_or_native_qualified||self.receipt.issuer_execution_publication_authority
            ||self.receipt.index.whole_document_visibility_and_search_qualified||self.receipt.scope.whole_document_visibility_qualified
            ||self.receipt.index.edit_or_service_access_authority{return Err(E::Binding);}Ok(bytes)
    }
    /// # Errors
    /// Rechecks current access/source/head; retained receipts never authorize results.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<StoredSourceSearchReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.fresh_json(provider,now)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(self.receipt.clone())
    }
    /// # Errors
    /// Final head check precedes the consumer; no unchecked match/bytes accessor.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let bytes=self.fresh_json(provider,now)?;
        provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(consume(&bytes))
    }
}
