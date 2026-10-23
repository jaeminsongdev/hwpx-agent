//! Strict v5 source selector discovery/search with current revision binding, not execution.
pub mod review;
pub mod styles;
pub mod controls;
pub mod resolved_styles;
use super::*;
use crate::form_stored_provider::actual_import::source_search::selector::SourceScopeOperation;
use hwpx_package::document_import::search::selector::{SourceIndexScopeSelector,SourceIndexBoundary};
use std::collections::BTreeSet;
pub const SOURCE_SCOPE_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-source-search-request/v5";
pub const SOURCE_SCOPE_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-source-search-preparation/v5";
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum ScopeKind {Document,Section,Selection,NodeSet}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct SelectionRange {coordinate_space:String,index_sha256:String,start:SourceIndexBoundary,end:SourceIndexBoundary}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct NodeRange {node_ids:Vec<LogicalId>}
#[derive(Deserialize,Serialize)]
#[serde(untagged)]
enum Range {Selection(SelectionRange),Nodes(NodeRange)}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Scope {pub(crate) revision_id:RevisionId,scope:ScopeKind,
    #[serde(default,skip_serializing_if="Vec::is_empty")] section_ids:Vec<LogicalId>,
    #[serde(default,skip_serializing_if="Option::is_none")] range:Option<Range>}
impl Scope {
    pub(crate) fn native(&self)->Result<SourceIndexScopeSelector<'_>,E> {match self.scope {
        ScopeKind::Document=>Ok(SourceIndexScopeSelector::Document),ScopeKind::Section=>Ok(SourceIndexScopeSelector::Section(&self.section_ids)),
        ScopeKind::Selection=>{let Some(Range::Selection(r))=&self.range else{return Err(E::Request)};
            let hash=hex::decode(&r.index_sha256).map_err(|_|E::Request)?.try_into().map_err(|_|E::Request)?;
            Ok(SourceIndexScopeSelector::Selection {index_sha256:hash,start:&r.start,end:&r.end})},
        ScopeKind::NodeSet=>{let Some(Range::Nodes(r))=&self.range else{return Err(E::Request)};Ok(SourceIndexScopeSelector::NodeSet(&r.node_ids))},
    }}
    pub(crate) fn shape(selector:&serde_json::Value)->Result<(bool,bool),E> {
        let has_sections=selector.get("section_ids").is_some();let has_range=selector.get("range").is_some();
        if has_sections&&!selector["section_ids"].is_array()||has_range&&!selector["range"].is_object(){return Err(E::Request);}Ok((has_sections,has_range))
    }
    pub(crate) fn validate_shape(&self,has_sections:bool,has_range:bool)->Result<(),E> {
        match self.scope {
            ScopeKind::Document=>if has_sections||has_range{return Err(E::Request);},
            ScopeKind::Section=>if !has_sections||has_range||!valid_ids(&self.section_ids){return Err(E::Request);},
            ScopeKind::NodeSet=>{let Some(Range::Nodes(r))=&self.range else{return Err(E::Request)};
                if has_sections||!valid_ids(&r.node_ids){return Err(E::Request);}},
            ScopeKind::Selection=>{let Some(Range::Selection(r))=&self.range else{return Err(E::Request)};
                if has_sections||r.coordinate_space!="index_nfc_unicode_scalars"||!valid_sha(&r.index_sha256){return Err(E::Request);}},
        }Ok(())
    }
}
#[derive(Deserialize,Serialize)]
#[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
enum Operation {ScopeInventory {},FindLiteral {query:String,case_sensitive:bool,whole_word:bool,max_results:usize},
    FindRegex {query:String,case_sensitive:bool,whole_word:bool,max_results:usize}}
impl Operation {
    fn query(&self)->Option<SourceSearchQuery<'_>> {match self {
        Self::ScopeInventory {}=>None,Self::FindLiteral {query,case_sensitive,whole_word,max_results}|Self::FindRegex {query,case_sensitive,whole_word,max_results}=>Some(SourceSearchQuery {
            query,mode:if matches!(self,Self::FindRegex {..}){SourceSearchMode::Regex}else{SourceSearchMode::Literal},
            case_sensitive:*case_sensitive,whole_word:*whole_word,max_results:*max_results})}}
    fn capability(&self)->&'static str {if matches!(self,Self::FindRegex {..}){"search.find_regex"}else{"search.find_literal"}}
}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request {schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
impl Request {
    fn parse(raw:&[u8])->Result<Self,E> {
        Self::parse_value(Self::parse_object(raw)?,SOURCE_SCOPE_PRODUCT_REQUEST_SCHEMA)
    }
    fn parse_object(raw:&[u8])->Result<serde_json::Value,E> {
        if raw.is_empty()||raw.len()>SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES{return Err(E::Limit);}
        let mut parser=serde_json::Deserializer::from_slice(raw);let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;
        let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
        if !value.is_object()||!["selector","operation"].iter().all(|key|value.get(key).is_some_and(serde_json::Value::is_object)){return Err(E::Request);}
        Ok(value)
    }
    fn parse_value(value:serde_json::Value,schema:&str)->Result<Self,E> {
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(E::Request)?)?;
        let request:Self=serde_json::from_value(value).map_err(|_|E::Request)?;
        if request.schema_version!=schema||request.expected_head_generation==0
            ||request.selector.revision_id!=request.base_revision||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256){return Err(E::Request);}
        request.selector.validate_shape(has_sections,has_range)?;
        if let Some(query)=request.operation.query() {
            if query.query.is_empty()||query.query.len()>4096||query.max_results==0||query.max_results>10_000{return Err(E::Request);}
        }else if !matches!(request.selector.scope,ScopeKind::Document){return Err(E::Request);}
        request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,E> {RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),self.expected_head_generation).map_err(|_|E::Request)}
    fn canonical_sha(&self)->Result<String,E> {Ok(digest(&bounded(self,SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E> {Ok(digest(&bounded(&(SOURCE_SCOPE_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),SOURCE_SEARCH_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
}
pub(crate) fn valid_sha(value:&str)->bool {value.len()==64&&value.bytes().all(|c|c.is_ascii_digit()||(b'a'..=b'f').contains(&c))}
fn valid_ids(ids:&[LogicalId])->bool {!ids.is_empty()&&ids.len()<=50_000&&ids.iter().collect::<BTreeSet<_>>().len()==ids.len()}
pub struct PreparedStoredSourceScopeProduct {request:Request,candidate:PreparedStoredSourceSearch,receipt:SourceSearchProductReceipt}
impl fmt::Debug for PreparedStoredSourceScopeProduct {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("PreparedStoredSourceScopeProduct(<redacted>; index_scope_not_full_search)")}}
#[derive(Debug)]
pub struct StoredSourceScopeProductRequest;
impl StoredSourceScopeProductRequest {
    /// # Errors
    /// Strict v5 request and explicit selector revision before current sealed-source reads.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceSearchLimits,now:u64)->Result<PreparedStoredSourceScopeProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request=Request::parse(raw)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
        let operation=if let Some(query)=request.operation.query(){SourceScopeOperation::Find {query,selector:request.selector.native()?}}else{SourceScopeOperation::Inventory};
        let candidate=source.into_source_scope(provider,operation,limits,now)?;
        let receipt=SourceSearchProductReceipt {profile:SOURCE_SCOPE_PRODUCT_PREPARATION_PROFILE,capability_id:request.operation.capability(),raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_search_product_native_cas_execution_publication_authority:false};
        let product=PreparedStoredSourceScopeProduct {request,candidate,receipt};product.check(provider)?;Ok(product)
    }
}
impl PreparedStoredSourceScopeProduct {
    /// # Errors
    /// Identifies a retained Find, including original raw/key/plan/selector context; not an access grant.
    pub fn navigation_receipt_sha256(&self)->Result<String,E> {
        if self.request.operation.query().is_none(){return Err(E::Request);}
        Ok(hex::encode(super::navigation::receipt_context(&self.receipt)?))
    }
    /// # Errors
    /// Strict bound next request, current stored source/access and final head without a new query.
    pub fn with_next_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let(request,context)=super::navigation::bound_next(raw,&self.receipt)?;
        if self.request.operation.query().is_none(){return Err(E::Request);}self.check(provider)?;
        Ok(self.candidate.with_next_verified_json(provider,&request,context,now,consume)?)
    }
    #[must_use] pub const fn receipt(&self)->&SourceSearchProductReceipt {&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let scope=provider.source_search_product_scope(&self.request.project_id,&self.request.document_id)?;
        if self.receipt.profile!=SOURCE_SCOPE_PRODUCT_PREPARATION_PROFILE||self.receipt.capability_id!=self.request.operation.capability()
            ||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?
            ||&self.receipt.stored!=self.candidate.receipt()||self.receipt.stored.profile!="hwpx-agent.stored-source-search/v5"
            ||self.receipt.stored.source.head_generation!=self.request.expected_head_generation
            ||self.request.selector.revision_id!=self.request.base_revision
            ||hex::encode(self.receipt.stored.index.source_package_sha256)!=self.request.expected_source_package_sha256
            ||self.receipt.idempotency_key_claimed||self.receipt.full_search_product_native_cas_execution_publication_authority{return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Reuses original current ACL/source/head checks without rebuilding inventory or query results.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<SourceSearchProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Original final consumer head check precedes JSON exposure.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        self.check(provider)?;Ok(self.candidate.with_verified_json(provider,now,consume)?)
    }
    /// # Errors
    /// Discovery/search is not a dispatcher, durable key claim, commit, CAS or execution grant.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {self.verify(provider,now)?;Err(E::RouteUnqualified)}
}
