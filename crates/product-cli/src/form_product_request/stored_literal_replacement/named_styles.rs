//! Strict named PARA reference product request with a separate output-discarded preview result.
pub mod options;
mod mutation;
pub use mutation::{PreparedStoredNamedStyleMutation,StoredNamedStyleMutationRequest,PreparedStoredNamedStylePreviewProduct};
pub(crate) use mutation::preview_mode;
use super::*;
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::named_styles::{PreparedStoredNamedStyleCandidate,PreparedStoredNamedStylePreview,
    StoredNamedStyleReceipt,StoredNamedStyleError,named_receipt_matches};
use hwpx_package::document_import::search::{reviews::SourceReviewTextPolicy,replacement::atoms::styles::paragraphs::named::{SourceNamedParagraphStyleQuery,SourceStyleNameAxis}};
pub const NAMED_STYLE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-named-paragraph-style-replacement-request/v1";
pub const NAMED_STYLE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-named-paragraph-style-preparation/v1";
pub const NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES:usize=4*1024*1024;
#[derive(Deserialize,Serialize)]#[serde(rename_all="snake_case")]enum Kind{ReplaceNamedParagraphStyles}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,query:String,replacement:String,regex:bool,case_sensitive:bool,whole_word:bool,name_axis:SourceStyleNameAxis,
    max_changed_paragraphs:usize,review_policy:SourceReviewTextPolicy,preview_only:bool}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum NamedStyleProductError{
    #[error("NAMED_STYLE_PRODUCT_REQUEST_REJECTED")]Request,#[error("NAMED_STYLE_PRODUCT_LIMIT")]Limit,#[error("NAMED_STYLE_PRODUCT_BINDING_REJECTED")]Binding,
    #[error("NAMED_STYLE_PRODUCT_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("NAMED_STYLE_PRODUCT_IMPORT_REJECTED")]Import(#[from]StoredActualFormImportError),
    #[error("NAMED_STYLE_PRODUCT_STORED_REJECTED")]Stored(#[from]StoredNamedStyleError),
    #[error("NAMED_STYLE_PRODUCT_PREVIEW_HAS_NO_OUTPUT")]PreviewOnly,#[error("NAMED_STYLE_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type N=NamedStyleProductError;
impl Request{
    fn parse(raw:&[u8])->Result<Self,N>{
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){N::Limit}else{N::Request})?;
        let operation=value.get("operation").ok_or(N::Request)?;
        if !operation.get("kind").is_some_and(serde_json::Value::is_string)||!operation.get("name_axis").is_some_and(serde_json::Value::is_string)
            ||!value.get("selector").and_then(|s|s.get("scope")).is_some_and(serde_json::Value::is_string){return Err(N::Request);}
        let(sections,range)=Scope::shape(value.get("selector").ok_or(N::Request)?).map_err(|_|N::Request)?;
        let r:Self=serde_json::from_value(value).map_err(|_|N::Request)?;
        if r.schema_version!=NAMED_STYLE_PRODUCT_REQUEST_SCHEMA||r.expected_head_generation==0||r.document_id.as_str().len()>1024
            ||!valid_sha(&r.expected_source_package_sha256)||r.selector.revision_id!=r.base_revision
            ||r.operation.max_changed_paragraphs==0||r.operation.max_changed_paragraphs>10_000{return Err(N::Request);}
        r.selector.validate_shape(sections,range).map_err(|_|N::Request)?;r.query().validate().map_err(|_|N::Request)?;r.head()?;r.canonical_sha()?;Ok(r)
    }
    fn query(&self)->SourceNamedParagraphStyleQuery<'_>{SourceNamedParagraphStyleQuery{query:&self.operation.query,replacement:&self.operation.replacement,
        regex:self.operation.regex,case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,name_axis:self.operation.name_axis}}
    fn head(&self)->Result<RevisionHead,N>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|N::Request)?),self.expected_head_generation).map_err(|_|N::Request)}
    fn canonical_sha(&self)->Result<String,N>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|N::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,N>{Ok(digest(&bounded(&(NAMED_STYLE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|N::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NamedStyleProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,pub canonical_request_sha256:String,
    pub scoped_request_sha256:String,pub stored:StoredNamedStyleReceipt,pub preview_only:bool,pub idempotency_key_claimed:bool,
    pub full_style_native_cas_execution_publication_authority:bool}
enum Prepared{Candidate(PreparedStoredNamedStyleCandidate<'static>),Preview(PreparedStoredNamedStylePreview<'static>)}
pub struct PreparedStoredNamedStyleProduct{request:Request,prepared:Prepared,receipt:NamedStyleProductReceipt,maximum_metadata_bytes:usize}
impl fmt::Debug for PreparedStoredNamedStyleProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredNamedStyleProduct(<redacted>; not_full_styles_or_execution)")}}
#[derive(Debug)]pub struct StoredNamedStyleProductRequest;
impl StoredNamedStyleProductRequest{
    /// # Errors
    /// Closed typed16KiB JSON and server budgets before authorized source reads. No caller IR.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleProduct,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;
        Self::prepare_parsed(provider,raw,request,limits,writer,now)
    }
    fn prepare_parsed<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],request:Request,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredNamedStyleProduct,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let maximum_metadata_bytes=limits.maximum_result_bytes().min(NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES);
        if request.operation.query.len()>limits.maximum_query_bytes()||request.operation.replacement.len()>limits.maximum_query_bytes(){return Err(N::Limit);}
        let limits=limits.restrict_match_limit(request.operation.max_changed_paragraphs).map_err(|_|N::Limit)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(N::Binding);}
        let candidate=source.into_named_style_candidate(provider,request.query(),request.selector.native().map_err(|_|N::Request)?,request.operation.review_policy,limits,writer,now)?;
        let prepared=if request.operation.preview_only{Prepared::Preview(candidate.into_preview())}else{Prepared::Candidate(candidate)};
        let stored=match &prepared{Prepared::Candidate(c)=>c.receipt(),Prepared::Preview(c)=>c.receipt()}.clone();
        let receipt=NamedStyleProductReceipt{profile:NAMED_STYLE_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_styles",raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,
            scoped_request_sha256:request.scoped_sha(scope)?,stored,preview_only:request.operation.preview_only,idempotency_key_claimed:false,full_style_native_cas_execution_publication_authority:false};
        bounded(&receipt,maximum_metadata_bytes).map_err(|_|N::Limit)?;let out=PreparedStoredNamedStyleProduct{request,prepared,receipt,maximum_metadata_bytes};out.check(provider)?;Ok(out)
    }
}
impl PreparedStoredNamedStyleProduct{
    #[must_use]pub const fn receipt(&self)->&NamedStyleProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=&self.request;
        let expected=match &self.prepared{Prepared::Candidate(c)=>{if r.operation.preview_only{return Err(N::Binding);}c.receipt()},Prepared::Preview(c)=>{if !r.operation.preview_only{return Err(N::Binding);}c.receipt()}};
        check_binding(r,&self.receipt,expected,self.maximum_metadata_bytes,provider)
    }
    /// # Errors
    /// Retained current source, ACL/head and candidate integrity; no matching or lowering replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<NamedStyleProductReceipt,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let stored=match &self.prepared{Prepared::Candidate(c)=>c.verify(provider,now)?,Prepared::Preview(c)=>c.verify(provider,now)?};
        if stored!=self.receipt.stored{return Err(N::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// A preview has no output and never invokes the byte consumer, even with a foreign provider.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        match &self.prepared{Prepared::Preview(_)=>Err(N::PreviewOnly),Prepared::Candidate(c)=>{self.check(provider)?;Ok(c.with_verified_bytes(provider,now,consume)?)}}
    }
    /// # Errors
    /// Bounded metadata only, with source integrity and the original consumer-final head check.
    pub fn with_verified_json<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let bytes=bounded(&self.receipt,self.maximum_metadata_bytes).map_err(|_|N::Limit)?;
        match &self.prepared{Prepared::Candidate(c)=>Ok(c.with_verified_bytes(provider,now,|_|consume(&bytes))?),Prepared::Preview(c)=>Ok(c.with_verified_metadata(provider,now,|_|consume(&bytes))?)}
    }
    /// # Errors
    /// Preparation is not issuer, durable claim, CAS, Native execution or publication authority.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),N>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(N::RouteUnqualified)}
}
fn check_binding<Rp,B,S,V>(r:&Request,p:&NamedStyleProductReceipt,expected:&StoredNamedStyleReceipt,maximum_metadata_bytes:usize,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),N>
where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let s=&p.stored;let output=&s.output;let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;
        if maximum_metadata_bytes==0||maximum_metadata_bytes>NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES{return Err(N::Binding);}
        if r.schema_version!=NAMED_STYLE_PRODUCT_REQUEST_SCHEMA||p.profile!=NAMED_STYLE_PRODUCT_PREPARATION_PROFILE||p.capability_id!="search.replace_styles"
            ||p.canonical_request_sha256!=r.canonical_sha()?||p.scoped_request_sha256!=r.scoped_sha(scope)?||s!=expected||p.preview_only!=r.operation.preview_only
            ||s.preview_only!=r.operation.preview_only||s.candidate_output_retained==r.operation.preview_only||s.issuer_execution_publication_authority
            ||s.source.head_generation!=r.expected_head_generation||r.selector.revision_id!=r.base_revision||hex::encode(output.source_package_sha256)!=r.expected_source_package_sha256
            ||output.name_axis!=r.operation.name_axis||output.body_policy!=r.operation.review_policy||output.matched_paragraphs>r.operation.max_changed_paragraphs
            ||!named_receipt_matches(output,output.source_package_sha256)||p.idempotency_key_claimed||p.full_style_native_cas_execution_publication_authority{return Err(N::Binding);}Ok(())
}
