//! Strict v2 optional-filter/preview product request. v1 remains closed to these options.
mod mutation;
pub use mutation::{PreparedStoredFontOptionsMutation,StoredFontOptionsMutationRequest};
pub(crate) use mutation::preview_mode;
use super::*;
use crate::form_stored_provider::actual_import::literal_search_output::fonts::options::{PreparedStoredFontOptionsCandidate,
    PreparedStoredFontPreview,StoredFontOptionsReceipt,FONT_PREVIEW_MAX_JSON_BYTES};
use hwpx_package::document_import::search::reviews::selector::styles::SourceReviewStyleFilter;
pub const FONT_OPTIONS_REQUEST_SCHEMA:&str="hwpx-agent.product-scoped-font-replacement-request/v2";
pub const FONT_OPTIONS_PREPARATION_PROFILE:&str="hwpx-agent.product-scoped-font-options-preparation/v1";
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,query:String,replacement:String,regex:bool,case_sensitive:bool,whole_word:bool,languages:Vec<ImportedFontLanguage>,
    axis:SourceFontStyleAxis,max_changed_scalars:usize,review_policy:SourceReviewTextPolicy,
    #[serde(skip_serializing_if="Option::is_none")]style_filter:Option<SourceReviewStyleFilter>,preview_only:bool}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum FontOptionsProductError{
    #[error("FONT_OPTIONS_REQUEST_REJECTED")]Request,#[error("FONT_OPTIONS_LIMIT")]Limit,#[error("FONT_OPTIONS_BINDING_REJECTED")]Binding,
    #[error("FONT_OPTIONS_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("FONT_OPTIONS_IMPORT_REJECTED")]Import(#[from]StoredActualFormImportError),
    #[error("FONT_OPTIONS_STORED_REJECTED")]Stored(#[from]StoredFontError),
    #[error("FONT_OPTIONS_PREVIEW_HAS_NO_OUTPUT")]PreviewOnly,#[error("FONT_OPTIONS_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type X=FontOptionsProductError;
impl Request{
    fn parse(raw:&[u8])->Result<Self,X>{
        let value=super::super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){X::Limit}else{X::Request})?;
        let operation=value.get("operation").ok_or(X::Request)?;
        if !operation.get("kind").is_some_and(serde_json::Value::is_string)||!operation.get("axis").is_some_and(serde_json::Value::is_string)
            ||!operation.get("languages").and_then(serde_json::Value::as_array).is_some_and(|a|a.iter().all(serde_json::Value::is_string))
            ||!value.get("selector").and_then(|s|s.get("scope")).is_some_and(serde_json::Value::is_string)
            ||operation.get("style_filter").is_some_and(|f|!f.is_object()||!f.get("kind").is_some_and(serde_json::Value::is_string)){return Err(X::Request);}
        let(sections,range)=Scope::shape(value.get("selector").ok_or(X::Request)?).map_err(|_|X::Request)?;
        let r:Self=serde_json::from_value(value).map_err(|_|X::Request)?;
        if r.schema_version!=FONT_OPTIONS_REQUEST_SCHEMA||r.expected_head_generation==0||r.document_id.as_str().len()>1024
            ||!valid_sha(&r.expected_source_package_sha256)||r.selector.revision_id!=r.base_revision
            ||r.operation.max_changed_scalars==0||r.operation.max_changed_scalars>10_000{return Err(X::Request);}
        r.selector.validate_shape(sections,range).map_err(|_|X::Request)?;r.query().validate(128).map_err(|_|X::Request)?;
        if let Some(f)=&r.operation.style_filter{f.validate().map_err(|_|X::Request)?;}r.head()?;r.canonical_sha()?;Ok(r)
    }
    fn query(&self)->FontNameReplacementQuery<'_>{FontNameReplacementQuery{query:&self.operation.query,replacement:&self.operation.replacement,
        regex:self.operation.regex,case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,languages:&self.operation.languages}}
    fn head(&self)->Result<RevisionHead,X>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|X::Request)?),self.expected_head_generation).map_err(|_|X::Request)}
    fn canonical_sha(&self)->Result<String,X>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|X::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,X>{Ok(digest(&bounded(&(FONT_OPTIONS_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|X::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct FontOptionsProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,pub canonical_request_sha256:String,
    pub scoped_request_sha256:String,pub stored:StoredFontOptionsReceipt,pub preview_only:bool,pub idempotency_key_claimed:bool,
    pub full_font_native_cas_execution_publication_authority:bool}
enum Prepared{Candidate(PreparedStoredFontOptionsCandidate<'static>),Preview(PreparedStoredFontPreview<'static>)}
pub struct PreparedStoredFontOptionsProduct{request:Request,prepared:Prepared,receipt:FontOptionsProductReceipt}
impl fmt::Debug for PreparedStoredFontOptionsProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredFontOptionsProduct(<redacted>; not_execution_or_commit)")}}
#[derive(Debug)]pub struct StoredFontOptionsProductRequest;
impl StoredFontOptionsProductRequest{
    /// # Errors
    /// Bounded duplicate-free strict v2 JSON before reads. Preview discards the generated artifact.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredFontOptionsProduct,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;
        Self::prepare_parsed(provider,raw,request,limits,writer,now)
    }
    fn prepare_parsed<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],request:Request,limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredFontOptionsProduct,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if request.operation.query.len()>limits.maximum_query_bytes()||request.operation.replacement.len()>limits.maximum_query_bytes(){return Err(X::Limit);}
        let limits=limits.restrict_match_limit(request.operation.max_changed_scalars).map_err(|_|X::Limit)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(X::Binding);}
        let candidate=source.into_font_options_candidate(provider,request.query(),request.selector.native().map_err(|_|X::Request)?,request.operation.review_policy,
            request.operation.axis,request.operation.style_filter.clone(),limits,writer,now)?;
        let prepared=if request.operation.preview_only{Prepared::Preview(candidate.into_preview())}else{Prepared::Candidate(candidate)};
        let stored=match &prepared{Prepared::Candidate(c)=>c.receipt(),Prepared::Preview(p)=>p.receipt()}.clone();
        let receipt=FontOptionsProductReceipt{profile:FONT_OPTIONS_PREPARATION_PROFILE,capability_id:"search.replace_fonts",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored,preview_only:request.operation.preview_only,
            idempotency_key_claimed:false,full_font_native_cas_execution_publication_authority:false};
        bounded(&receipt,FONT_PREVIEW_MAX_JSON_BYTES).map_err(|_|X::Limit)?;
        let out=PreparedStoredFontOptionsProduct{request,prepared,receipt};out.check(provider)?;Ok(out)
    }
}
impl PreparedStoredFontOptionsProduct{
    #[must_use]pub const fn receipt(&self)->&FontOptionsProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let r=&self.request;
        let expected=match &self.prepared{Prepared::Candidate(c)=>{if r.operation.preview_only{return Err(X::Binding);}c.receipt()},
            Prepared::Preview(c)=>{if !r.operation.preview_only{return Err(X::Binding);}c.receipt()}};
        check_binding(&self.request,&self.receipt,expected,provider)
    }
    /// # Errors
    /// Retained current source checks without repeating matching or compiling output.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<FontOptionsProductReceipt,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let stored=match &self.prepared{Prepared::Candidate(c)=>c.verify(provider,now)?,Prepared::Preview(p)=>p.verify(provider,now)?};
        if stored!=self.receipt.stored{return Err(X::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Preview is rejected before invoking any output consumer. No empty or fake output is returned.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        match &self.prepared{Prepared::Preview(_)=>Err(X::PreviewOnly),Prepared::Candidate(c)=>{self.check(provider)?;Ok(c.with_verified_bytes(provider,now,consume)?)}}
    }
    /// # Errors
    /// Bounded predicted metadata with current ACL/source and consumer-final head on every delivery.
    pub fn with_verified_json<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let bytes=bounded(&self.receipt,FONT_PREVIEW_MAX_JSON_BYTES).map_err(|_|X::Limit)?;
        match &self.prepared{Prepared::Candidate(c)=>Ok(c.with_verified_bytes(provider,now,|_|consume(&bytes))?),
            Prepared::Preview(p)=>Ok(p.with_verified_metadata(provider,now,|_|consume(&bytes))?)}
    }
    /// # Errors
    /// Neither preview nor a retained candidate grants common execution, CAS or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),X>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(X::RouteUnqualified)}
}
fn check_binding<Rp,B,S,V>(r:&Request,p:&FontOptionsProductReceipt,expected:&StoredFontOptionsReceipt,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),X>
where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
    let s=&p.stored;let output=s.output.source();let scope=provider.source_search_product_scope(&r.project_id,&r.document_id)?;
    if r.schema_version!=FONT_OPTIONS_REQUEST_SCHEMA||p.profile!=FONT_OPTIONS_PREPARATION_PROFILE||p.capability_id!="search.replace_fonts"
        ||p.canonical_request_sha256!=r.canonical_sha()?||p.scoped_request_sha256!=r.scoped_sha(scope)?||s!=expected||p.preview_only!=r.operation.preview_only
        ||s.preview_only!=r.operation.preview_only||s.candidate_output_retained==r.operation.preview_only||s.issuer_execution_publication_authority
        ||s.source.head_generation!=r.expected_head_generation||r.selector.revision_id!=r.base_revision
        ||hex::encode(output.names.source_package_sha256)!=r.expected_source_package_sha256||output.axis!=r.operation.axis||output.body_policy!=r.operation.review_policy
        ||s.output.style_filter_ref()!=r.operation.style_filter.as_ref()||output.changed_source_scalars>r.operation.max_changed_scalars
        ||p.idempotency_key_claimed||p.full_font_native_cas_execution_publication_authority{return Err(X::Binding);}Ok(())
}
