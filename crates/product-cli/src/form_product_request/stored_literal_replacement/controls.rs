//! Strict typed text-control replacement from one current sealed source, not a full transaction.
use super::*;
compiler_product!(PreparedStoredControlProduct, request, plain);
search_lookup_product!(StoredControlProductRequest,|raw|Request::parse(raw),root,normal,no_preview);
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::controls::{PreparedStoredControlCandidate,StoredControlReceipt,StoredControlError,
    STORED_CONTROL_PROFILE,control_receipt_matches};
use hwpx_package::{TextAtom,document_import::search::{inspection::SourceControlKind,reviews::SourceReviewTextPolicy,
    replacement::atoms::controls::{ValidatedTextControlOutput,SourceControlReplacementError}}};
pub const CONTROL_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-text-control-replacement-request/v1";
pub const CONTROL_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-text-control-replacement-preparation/v1";
mod atom_wire{
    use super::*;
    use serde::{Deserializer,Serializer,ser::SerializeSeq};
    #[derive(Deserialize)] #[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
    enum Owned{Text{value:String},Tab{width:u32,leader:u32,tab_type:u32},LineBreak{}}
    #[derive(Serialize)] #[serde(tag="kind",rename_all="snake_case")]
    enum Borrowed<'a>{Text{value:&'a str},Tab{width:u32,leader:u32,tab_type:u32},LineBreak}
    pub(super) fn deserialize<'de,D:Deserializer<'de>>(d:D)->Result<Vec<TextAtom>,D::Error>{
        // Move each deserialized String instead of cloning the whole JSON/native output vector.
        Ok(Vec::<Owned>::deserialize(d)?.into_iter().map(|a|match a{Owned::Text{value}=>TextAtom::Text(value),
            Owned::Tab{width,leader,tab_type}=>TextAtom::Tab{width,leader,tab_type},Owned::LineBreak{}=>TextAtom::LineBreak}).collect())
    }
    pub(super) fn serialize<S:Serializer>(atoms:&[TextAtom],s:S)->Result<S::Ok,S::Error>{
        let mut seq=s.serialize_seq(Some(atoms.len()))?;for a in atoms{match a{
            TextAtom::Text(value)=>seq.serialize_element(&Borrowed::Text{value})?,TextAtom::Tab{width,leader,tab_type}=>
                seq.serialize_element(&Borrowed::Tab{width:*width,leader:*leader,tab_type:*tab_type})?,
            TextAtom::LineBreak=>seq.serialize_element(&Borrowed::LineBreak)?}}
        seq.end()
    }
}
#[derive(Deserialize,Serialize)] #[serde(rename_all="snake_case")]
enum Kind{ReplaceTextControls}
#[derive(Deserialize,Serialize)] #[serde(deny_unknown_fields)]
struct Operation{kind:Kind,control_kind:SourceControlKind,max_replacements:usize,#[serde(with="atom_wire")] output:Vec<TextAtom>,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)] #[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum ControlProductError{
    #[error("CONTROL_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("CONTROL_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("CONTROL_PRODUCT_KIND_UNQUALIFIED")] UnsupportedKind,
    #[error("CONTROL_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("CONTROL_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("CONTROL_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("CONTROL_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredControlError),
    #[error("CONTROL_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=ControlProductError;
impl Request{
    fn parse(raw:&[u8])->Result<Self,C>{
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){C::Limit}else{C::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(C::Request)?).map_err(|_|C::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|C::Request)?;
        if request.schema_version!=CONTROL_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision
            ||request.operation.max_replacements==0||request.operation.max_replacements>4096{return Err(C::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|C::Request)?;request.head()?;request.canonical_sha()?;Ok(request)
    }
    fn head(&self)->Result<RevisionHead,C>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|C::Request)?),self.expected_head_generation).map_err(|_|C::Request)}
    fn canonical_sha(&self)->Result<String,C>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
    fn scoped_sha(&self,scope:[u8;32])->Result<String,C>{Ok(digest(&bounded(&(CONTROL_PRODUCT_REQUEST_SCHEMA,scope,self.canonical_sha()?),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ControlProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredControlReceipt,
    pub idempotency_key_claimed:bool,pub full_control_native_cas_execution_publication_authority:bool}
pub struct PreparedStoredControlProduct{request:Request,candidate:PreparedStoredControlCandidate<'static>,receipt:ControlProductReceipt,
    replacement_sha256:[u8;32],replacement_text_bytes:usize}
impl fmt::Debug for PreparedStoredControlProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredControlProduct(<redacted>; exact_text_controls_not_full_control_or_transaction)")}}
#[derive(Debug)] pub struct StoredControlProductRequest;
impl StoredControlProductRequest{
    /// # Errors
    /// Unique bounded JSON, selector, qualified kind and output values before source access.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],limits:SourceSearchLimits,writer:WriterLimits,now:u64)->Result<PreparedStoredControlProduct,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;
        let input=ValidatedTextControlOutput::new(request.operation.control_kind,&request.operation.output,limits)
            .map_err(|e|if e==SourceControlReplacementError::UnsupportedKind{C::UnsupportedKind}else{C::Request})?;
        let replacement_sha256=input.replacement_sha256();let replacement_text_bytes=input.text_bytes();
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(C::Binding);}
        let candidate=source.into_control_input(provider,request.selector.native().map_err(|_|C::Request)?,request.operation.review_policy,request.operation.max_replacements,&input,writer,now)?;
        drop(input);
        let receipt=ControlProductReceipt{profile:CONTROL_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_control",raw_request_sha256:digest(raw),
            canonical_request_sha256:request.canonical_sha()?,scoped_request_sha256:request.scoped_sha(scope)?,stored:candidate.receipt().clone(),
            idempotency_key_claimed:false,full_control_native_cas_execution_publication_authority:false};
        let result=PreparedStoredControlProduct{request,candidate,receipt,replacement_sha256,replacement_text_bytes};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredControlProduct{
    #[must_use] pub const fn receipt(&self)->&ControlProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        if request.schema_version!=CONTROL_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=CONTROL_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.replace_control"||self.receipt.canonical_request_sha256!=request.canonical_sha()?
            ||self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_CONTROL_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.kind!=request.operation.control_kind||output.body_policy!=request.operation.review_policy
            ||output.replacement_atoms!=request.operation.output.len()||output.replacement_sha256!=self.replacement_sha256||output.replacement_text_bytes!=self.replacement_text_bytes
            ||output.selected_controls>request.operation.max_replacements||!control_receipt_matches(output,output.source_package_sha256)
            ||self.receipt.stored.issuer_execution_publication_authority||self.receipt.idempotency_key_claimed||self.receipt.full_control_native_cas_execution_publication_authority{return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Current access/source/writer/final head without another input validation, search or compiler.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<ControlProductReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(C::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Retained metadata cannot replace current access or the final consumer head check.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// No dispatcher, durable key claim, revision CAS, Native execution or publication authority.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
