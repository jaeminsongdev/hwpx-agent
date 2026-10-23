//! Strict explicit independent-parent sort request; current access and immutable retained output.
use super::*;
compiler_product!(PreparedStoredParagraphSortGroupsProduct, request, plain);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::sort_groups::{PreparedStoredParagraphSortGroupsCandidate,
    StoredParagraphSortGroupsReceipt,STORED_PARAGRAPH_SORT_GROUPS_PROFILE,sort_groups_receipt_matches};
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,replacement::atoms::sort::SourceParagraphSortSpec};
pub use super::sort::ParagraphSortProductError as ParagraphSortGroupsProductError;
pub const PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-paragraph-sort-groups-request/v1";
pub const PARAGRAPH_SORT_GROUPS_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-paragraph-sort-groups-preparation/v1";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind{SortParagraphGroups}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,sort_spec:SourceParagraphSortSpec,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
type C=ParagraphSortGroupsProductError;
impl Request {
    fn parse(raw:&[u8])->Result<Self,C>{
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){C::Limit}else{C::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(C::Request)?).map_err(|_|C::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|C::Request)?;
        if request.schema_version!=PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision
            ||request.operation.sort_spec.max_comparison_bytes==0||request.operation.sort_spec.max_comparison_bytes>32*1024*1024{return Err(C::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|C::Request)?;request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,C>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|C::Request)?),self.expected_head_generation).map_err(|_|C::Request)}
    fn canonical_sha(&self)->Result<String,C>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,C>{Ok(digest(&bounded(&(PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ParagraphSortGroupsProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredParagraphSortGroupsReceipt,
    pub idempotency_key_claimed:bool,pub full_sort_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredParagraphSortGroupsProduct{request:Request,candidate:PreparedStoredParagraphSortGroupsCandidate<'static>,receipt:ParagraphSortGroupsProductReceipt}
impl fmt::Debug for PreparedStoredParagraphSortGroupsProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredParagraphSortGroupsProduct(<redacted>; current_source_candidate_not_transaction)")}}
#[derive(Debug)]
pub struct StoredParagraphSortGroupsProductRequest;
impl StoredParagraphSortGroupsProductRequest {
    /// # Errors
    /// Closed duplicate-free JSON and explicit grouping/spec/policy before reading the source.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredParagraphSortGroupsProduct,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(C::Binding);}
        let candidate=source.into_paragraph_sort_groups_candidate(provider,request.selector.native().map_err(|_|C::Request)?,request.operation.review_policy,request.operation.sort_spec,limits,writer,now)?;
        let receipt=ParagraphSortGroupsProductReceipt{profile:PARAGRAPH_SORT_GROUPS_PRODUCT_PREPARATION_PROFILE,capability_id:"search.sort_text",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_sort_native_cas_execution_publication_authority:false};
        let result=PreparedStoredParagraphSortGroupsProduct{request,candidate,receipt};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredParagraphSortGroupsProduct {
    pub(crate) fn compiler_sort_splices(&self)->&hwpx_package::document_import::search::replacement::atoms::sort::intents::SourceParagraphSortSpliceInventory{self.candidate.compiler_sort_splices()}
    #[must_use] pub const fn receipt(&self)->&ParagraphSortGroupsProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=PARAGRAPH_SORT_GROUPS_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=PARAGRAPH_SORT_GROUPS_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.sort_text"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_PARAGRAPH_SORT_GROUPS_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.spec!=request.operation.sort_spec||output.body_policy!=request.operation.review_policy
            ||!sort_groups_receipt_matches(output,output.source_package_sha256)||self.receipt.stored.issuer_execution_publication_authority
            ||self.receipt.idempotency_key_claimed||self.receipt.full_sort_native_cas_execution_publication_authority{return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Fresh current access/source/writer/head, never a repeated sort.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<ParagraphSortGroupsProductReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(C::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Current source and final head checks precede the consumer.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// No common execution/commit/CAS/idempotency/Native/publication qualification.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
