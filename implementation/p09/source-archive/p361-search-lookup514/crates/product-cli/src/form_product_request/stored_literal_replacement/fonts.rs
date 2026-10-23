//! Strict scoped-font preparation request. Does not open the common compiler/dispatcher route.
pub mod options;
use super::*;
compiler_product!(PreparedStoredFontProduct, request, plain);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::fonts::{PreparedStoredFontCandidate,StoredFontReceipt,StoredFontError,
    font_receipt_matches,STORED_FONT_PROFILE};
use hwpx_package::document_import::{fields::semantics::catalog::fonts::{ImportedFontLanguage,
    names::FontNameReplacementQuery},search::{reviews::SourceReviewTextPolicy,replacement::atoms::styles::fonts::SourceFontStyleAxis}};
pub const FONT_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-scoped-font-replacement-request/v1";
pub const FONT_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-scoped-font-replacement-preparation/v1";
#[derive(Deserialize,Serialize)]#[serde(rename_all="snake_case")]enum Kind{ReplaceFonts}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,query:String,replacement:String,regex:bool,case_sensitive:bool,whole_word:bool,languages:Vec<ImportedFontLanguage>,
    axis:SourceFontStyleAxis,max_changed_scalars:usize,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)]#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum FontProductError{
    #[error("FONT_PRODUCT_REQUEST_REJECTED")]Request,
    #[error("FONT_PRODUCT_LIMIT")]Limit,
    #[error("FONT_PRODUCT_BINDING_REJECTED")]Binding,
    #[error("FONT_PRODUCT_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("FONT_PRODUCT_IMPORT_REJECTED")]Import(#[from]StoredActualFormImportError),
    #[error("FONT_PRODUCT_STORED_REJECTED")]Stored(#[from]StoredFontError),
    #[error("FONT_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type C=FontProductError;
impl Request{
    fn parse(raw:&[u8])->Result<Self,C>{
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){C::Limit}else{C::Request})?;
        let operation=value.get("operation").ok_or(C::Request)?;
        if !operation.get("kind").is_some_and(serde_json::Value::is_string)||!operation.get("axis").is_some_and(serde_json::Value::is_string)
            ||!operation.get("languages").and_then(serde_json::Value::as_array).is_some_and(|a|a.iter().all(serde_json::Value::is_string))
            ||!value.get("selector").and_then(|s|s.get("scope")).is_some_and(serde_json::Value::is_string){return Err(C::Request);}
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(C::Request)?).map_err(|_|C::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|C::Request)?;
        if request.schema_version!=FONT_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision
            ||request.operation.max_changed_scalars==0||request.operation.max_changed_scalars>10_000{return Err(C::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|C::Request)?;
        request.query().validate(128).map_err(|_|C::Request)?;request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn query(&self)->FontNameReplacementQuery<'_>{FontNameReplacementQuery{query:&self.operation.query,replacement:&self.operation.replacement,
        regex:self.operation.regex,case_sensitive:self.operation.case_sensitive,whole_word:self.operation.whole_word,languages:&self.operation.languages}}
    fn head(&self)->Result<RevisionHead,C>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|C::Request)?),self.expected_head_generation).map_err(|_|C::Request)}
    fn canonical_sha(&self)->Result<String,C>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,C>{Ok(digest(&bounded(&(FONT_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct FontProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,pub canonical_request_sha256:String,
    pub scoped_request_sha256:String,pub stored:StoredFontReceipt,pub idempotency_key_claimed:bool,pub full_font_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredFontProduct{request:Request,candidate:PreparedStoredFontCandidate<'static>,receipt:FontProductReceipt}
impl fmt::Debug for PreparedStoredFontProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredFontProduct(<redacted>; scoped_candidate_not_common_dispatch_or_commit)")}}
#[derive(Debug)]pub struct StoredFontProductRequest;
impl StoredFontProductRequest{
    /// # Errors
    /// Closed duplicate-free bounded JSON and revision selector before any authorized source read.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredFontProduct,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;
        if request.operation.query.len()>limits.maximum_query_bytes()||request.operation.replacement.len()>limits.maximum_query_bytes(){return Err(C::Limit);}
        let limits=limits.restrict_match_limit(request.operation.max_changed_scalars).map_err(|_|C::Limit)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(C::Binding);}
        let candidate=source.into_font_candidate(provider,request.query(),request.selector.native().map_err(|_|C::Request)?,request.operation.review_policy,request.operation.axis,limits,writer,now)?;
        let receipt=FontProductReceipt{profile:FONT_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_fonts",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),idempotency_key_claimed:false,
            full_font_native_cas_execution_publication_authority:false};
        let out=PreparedStoredFontProduct{request,candidate,receipt};out.check(provider)?;Ok(out)
    }
}
impl PreparedStoredFontProduct{
    pub(crate) fn compiler_font_inventory(&self)->&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory{self.candidate.compiler_font_inventory()}
    /// # Errors
    /// Exact header resource effects and body splices, never an unchecked byte/authority path.
    pub fn with_verified_edit_inventory<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,
        consume:impl FnOnce(&hwpx_package::document_import::search::replacement::atoms::styles::fonts::inventory::SourceFontEditInventory)->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;Ok(self.candidate.with_verified_edit_inventory(provider,now,consume)?)
    }
    #[must_use]pub const fn receipt(&self)->&FontProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=FONT_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=FONT_PRODUCT_PREPARATION_PROFILE||self.receipt.capability_id!="search.replace_fonts"
            ||self.receipt.canonical_request_sha256!=request.canonical_sha()?||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?
            ||&self.receipt.stored!=self.candidate.receipt()||self.receipt.stored.profile!=STORED_FONT_PROFILE||self.receipt.stored.issuer_execution_publication_authority
            ||self.receipt.stored.source.head_generation!=request.expected_head_generation||request.selector.revision_id!=request.base_revision
            ||hex::encode(output.names.source_package_sha256)!=request.expected_source_package_sha256||output.axis!=request.operation.axis||output.body_policy!=request.operation.review_policy
            ||output.changed_source_scalars>request.operation.max_changed_scalars||!font_receipt_matches(output,output.names.source_package_sha256)
            ||self.receipt.idempotency_key_claimed||self.receipt.full_font_native_cas_execution_publication_authority{return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current provider/source and retained candidate integrity; no font matcher/compiler replay.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<FontProductReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(C::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Original current authority and final-head callback remain mandatory for every delivery.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)
    }
    /// # Errors
    /// Common compiler/dispatcher, durable key, CAS, Native and publication are still unqualified.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
