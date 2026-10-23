//! Strict current-source preparation for named declarations, not a body-replacement request.
use super::{UniqueJson,bounded,digest};
use crate::form_stored_provider::{StoredFormProvider,actual_import::{StoredActualFormImportError,named_style_declarations::{
    PreparedStoredNamedStyleDeclarations,StoredNamedStyleDeclarationsReceipt,StoredNamedStyleDeclarationsError}}};
use artifact_service::{ArtifactMetadataRepository,ArtifactScanner,EncryptedBlobStore};
use domain_ir::{DocumentId,IdempotencyKey,PlanId,ProjectId,RevisionId};
use hwpx_package::document_import::fields::semantics::catalog::named_styles::{SourceNamedStyleNameQuery,SourceNamedStyleKind,SourceNamedStyleNameAxis,SourceNamedStyleNameLimits};
use revision_service::{RevisionHead,RevisionRepository};
use serde::{Deserialize,Serialize};
use std::fmt;
use thiserror::Error;
pub const NAMED_DECLARATIONS_PRODUCT_SCHEMA:&str="hwpx-agent.product-named-style-declarations-request/v1";
pub const NAMED_DECLARATIONS_MAX_REQUEST_BYTES:usize=16*1024;
#[derive(Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
enum Kind{ResolveNamedStyleDeclarations}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Operation{kind:Kind,query:String,replacement:String,regex:bool,case_sensitive:bool,whole_word:bool,
    style_kind:SourceNamedStyleKind,name_axis:SourceNamedStyleNameAxis}
#[derive(Deserialize,Serialize)]
#[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,operation:Operation}
impl Request{
    fn query(&self)->SourceNamedStyleNameQuery<'_>{let o=&self.operation;SourceNamedStyleNameQuery{query:&o.query,replacement:&o.replacement,regex:o.regex,
        case_sensitive:o.case_sensitive,whole_word:o.whole_word,kind:o.style_kind,name_axis:o.name_axis}}
    fn head(&self)->Result<RevisionHead,E>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|E::Request)?),self.expected_head_generation).map_err(|_|E::Request)}
    fn parse(raw:&[u8],limits:SourceNamedStyleNameLimits)->Result<Self,E>{
        if raw.is_empty()||raw.len()>NAMED_DECLARATIONS_MAX_REQUEST_BYTES{return Err(E::Limit);}
        let mut parser=serde_json::Deserializer::from_slice(raw);let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;
        // Derived externally tagged unit enums can accept object representations; this profile requires strings.
        let v:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;
        if !v.is_object()||!v.get("operation").is_some_and(serde_json::Value::is_object)
            ||!["kind","style_kind","name_axis"].iter().all(|k|v["operation"].get(k).is_some_and(serde_json::Value::is_string)){return Err(E::Request);}
        let request:Self=serde_json::from_value(v).map_err(|_|E::Request)?;
        if request.schema_version!=NAMED_DECLARATIONS_PRODUCT_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||request.expected_source_package_sha256.len()!=64||!request.expected_source_package_sha256.bytes().all(|b|b.is_ascii_digit()||(b'a'..=b'f').contains(&b)){return Err(E::Request);}
        request.query().validate(limits).map_err(|_|E::Request)?;request.head()?;Ok(request)
    }
    fn canonical_sha(&self)->Result<String,E>{Ok(digest(&bounded(self,NAMED_DECLARATIONS_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,E>{Ok(digest(&bounded(&(&self.schema_version,scope,self.canonical_sha()?),NAMED_DECLARATIONS_MAX_REQUEST_BYTES).map_err(|_|E::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NamedStyleDeclarationsProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredNamedStyleDeclarationsReceipt,
    pub idempotency_key_claimed:bool,pub body_mapping_mutation_native_or_execution_qualified:bool}
pub struct PreparedNamedStyleDeclarationsProduct{request:Request,candidate:PreparedStoredNamedStyleDeclarations,receipt:NamedStyleDeclarationsProductReceipt,maximum_bytes:usize}
impl fmt::Debug for PreparedNamedStyleDeclarationsProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedNamedStyleDeclarationsProduct(<redacted>; declaration_metadata_only)")}}
#[derive(Debug,Error)]
pub enum NamedStyleDeclarationsProductError{
    #[error("NAMED_DECLARATIONS_PRODUCT_REQUEST_REJECTED")]Request,
    #[error("NAMED_DECLARATIONS_PRODUCT_LIMIT")]Limit,
    #[error("NAMED_DECLARATIONS_PRODUCT_BINDING_REJECTED")]Binding,
    #[error("NAMED_DECLARATIONS_PRODUCT_IMPORT_REJECTED")]Import(#[from]StoredActualFormImportError),
    #[error("NAMED_DECLARATIONS_PRODUCT_SCOPE_REJECTED")]Scope(#[from]crate::form_stored_provider::actual_import::source_search::StoredSourceSearchError),
    #[error("NAMED_DECLARATIONS_PRODUCT_SERVICE_REJECTED")]Stored(#[from]StoredNamedStyleDeclarationsError),
    #[error("NAMED_DECLARATIONS_PRODUCT_ROUTE_UNQUALIFIED")]RouteUnqualified,
}
type E=NamedStyleDeclarationsProductError;
#[derive(Debug)]pub struct NamedStyleDeclarationsProductRequest;
impl NamedStyleDeclarationsProductRequest{
    /// # Errors
    /// Rejects malformed/foreign requests before reading the sealed current Result; no caller graph or approval bits.
    pub fn prepare_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SourceNamedStyleNameLimits,now:u64)->Result<PreparedNamedStyleDeclarationsProduct,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw,limits)?;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(E::Binding);}
        let candidate=source.into_named_style_declarations(provider,request.query(),limits,now)?;
        let receipt=NamedStyleDeclarationsProductReceipt{profile:"hwpx-agent.product-named-style-declarations-preparation/v1",capability_id:"search.replace_styles",
            raw_request_sha256:digest(raw),canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,
            stored:candidate.receipt().clone(),idempotency_key_claimed:false,body_mapping_mutation_native_or_execution_qualified:false};
        let product=PreparedNamedStyleDeclarationsProduct{request,candidate,receipt,maximum_bytes:limits.maximum_result_bytes()};product.check(provider)?;
        let _=bounded(&product.receipt,product.maximum_bytes).map_err(|_|E::Limit)?;product.candidate.check_head(provider)?;Ok(product)
    }
}
impl PreparedNamedStyleDeclarationsProduct{
    #[must_use]pub const fn receipt(&self)->&NamedStyleDeclarationsProductReceipt{&self.receipt}
    fn check<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let scope=provider.source_search_product_scope(&self.request.project_id,&self.request.document_id)?;
        if self.receipt.profile!="hwpx-agent.product-named-style-declarations-preparation/v1"||self.receipt.capability_id!="search.replace_styles"
            ||self.receipt.canonical_request_sha256!=self.request.canonical_sha()?||self.receipt.scoped_request_sha256!=self.request.scoped_sha(scope)?
            ||&self.receipt.stored!=self.candidate.receipt()||self.receipt.stored.source.head_generation!=self.request.expected_head_generation
            ||hex::encode(self.receipt.stored.resolution.source_package_sha256)!=self.request.expected_source_package_sha256
            ||self.receipt.stored.resolution.kind!=self.request.operation.style_kind||self.receipt.stored.resolution.name_axis!=self.request.operation.name_axis
            ||self.receipt.idempotency_key_claimed||self.receipt.body_mapping_mutation_native_or_execution_qualified{return Err(E::Binding);}Ok(())
    }
    /// # Errors
    /// Revalidates current service access; retained request/receipt digests never confer authority.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<NamedStyleDeclarationsProductReceipt,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Entire envelope is bounded before current verification and the consumer-final head check.
    pub fn with_verified_json<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;let bytes=bounded(&self.receipt,self.maximum_bytes).map_err(|_|E::Limit)?;
        Ok(self.candidate.with_verified_metadata(provider,now,|_|consume(&bytes))?)
    }
    /// # Errors
    /// No body mapping, mutation artifact, compiler owner, ingest, CAS, key claim or Native execution is exposed.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64)->Result<(),E>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(E::RouteUnqualified)}
}
