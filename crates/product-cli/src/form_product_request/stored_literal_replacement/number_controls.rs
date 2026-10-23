//! Strict current-source number-control candidate preparation, not counter evaluation or a transaction.
use super::*;
compiler_product!(PreparedStoredNumberControlProduct, request, plain);
impl StoredNumberControlProductRequest {
    pub(crate) fn prepare_request_lookup_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8])
        ->Result<crate::form_product_request::stored_operations::compiled_search::request_lookup::PreparedSearchRequestLookup,
            crate::form_product_request::stored_operations::compiled_search::request_lookup::SearchRequestLookupError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        use crate::form_product_request::stored_operations::compiled_search::request_lookup::{PreparedSearchRequestLookup,SearchRequestLookupError as LE};
        let(request,canonical)=Request::parse(raw).map_err(|_|LE::Request)?;
        let limits=crate::form_product_request::stored_operations::search_mutations::SearchMutationLimits::standard().map_err(|_|LE::Request)?;
        let _values=ValidatedNumberControlValues::new(request.operation.control_kind,request.operation.stored_number,request.operation.format.native(),limits.search,limits.auxiliary)
            .map_err(|_|LE::Request)?;
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let scoped=Request::scoped_sha(scope,&canonical).map_err(|_|LE::Request)?;
        let source=artifact_service::ContentDigest::parse(&request.expected_source_package_sha256).map_err(|_|LE::Request)?;
        let head=request.head().map_err(|_|LE::Request)?;
        PreparedSearchRequestLookup::bind(provider,&request.project_id,&request.document_id,&request.idempotency_key,&canonical,&scoped,source,head,scope)
    }
}
use super::super::stored_source_search::selector::{Scope,valid_sha};
use crate::form_stored_provider::actual_import::literal_search_output::number_controls::{PreparedStoredNumberControlCandidate,StoredNumberControlReceipt,
    StoredNumberControlError,STORED_NUMBER_CONTROL_PROFILE,number_control_receipt_matches};
use hwpx_package::{NumberFormat,document_import::{search::{inspection::SourceControlKind,reviews::SourceReviewTextPolicy,
    replacement::atoms::number_controls::{ValidatedNumberControlValues,SourceNumberControlError}},structure::caption_numbering_sequence::NativeNumberFormatReplacement}};
use domain_ir::ReferenceAuxiliaryLimits;
pub const NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA:&str="hwpx-agent.product-number-control-replacement-request/v1";
pub const NUMBER_CONTROL_PRODUCT_PREPARATION_PROFILE:&str="hwpx-agent.product-number-control-replacement-preparation/v1";
macro_rules! formats{($(($variant:ident,$wire:literal)),+$(,)?)=>{
    #[derive(Clone,Copy,Deserialize,Serialize)] enum FormatName{$(#[serde(rename=$wire)] $variant),+}
    impl FormatName{fn native(self)->NumberFormat{match self{$(Self::$variant=>NumberFormat::$variant),+}}}
}}
formats!((Digit,"DIGIT"),(CircledDigit,"CIRCLED_DIGIT"),(RomanCapital,"ROMAN_CAPITAL"),(RomanSmall,"ROMAN_SMALL"),
    (LatinCapital,"LATIN_CAPITAL"),(LatinSmall,"LATIN_SMALL"),(CircledLatinCapital,"CIRCLED_LATIN_CAPITAL"),(CircledLatinSmall,"CIRCLED_LATIN_SMALL"),
    (HangulSyllable,"HANGUL_SYLLABLE"),(CircledHangulSyllable,"CIRCLED_HANGUL_SYLLABLE"),(HangulJamo,"HANGUL_JAMO"),(CircledHangulJamo,"CIRCLED_HANGUL_JAMO"),
    (HangulPhonetic,"HANGUL_PHONETIC"),(Ideograph,"IDEOGRAPH"),(CircledIdeograph,"CIRCLED_IDEOGRAPH"),(DecagonCircle,"DECAGON_CIRCLE"),
    (DecagonCircleHanja,"DECAGON_CIRCLE_HANJA"),(Symbol,"SYMBOL"),(UserChar,"USER_CHAR"),(Symbol2,"SYMBOL2"),(Image,"IMAGE"),(TwoDigit,"2DIGIT"));
#[derive(Deserialize,Serialize)] #[serde(tag="kind",rename_all="snake_case",deny_unknown_fields)]
enum Format{Preserve{},Replace{format:FormatName,user_character:String,prefix:String,suffix:String,superscript:bool}}
impl Format{fn native(&self)->NativeNumberFormatReplacement<'_>{match self{Self::Preserve{}=>NativeNumberFormatReplacement::Preserve,
    Self::Replace{format,user_character,prefix,suffix,superscript}=>NativeNumberFormatReplacement::Replace{format:format.native(),user_character,prefix,suffix,superscript:*superscript}}}}
#[derive(Deserialize,Serialize)] #[serde(rename_all="snake_case")] enum Kind{ReplaceNumberControls}
#[derive(Deserialize,Serialize)] #[serde(deny_unknown_fields)]
struct Operation{kind:Kind,control_kind:SourceControlKind,max_replacements:usize,stored_number:i32,format:Format,review_policy:SourceReviewTextPolicy}
#[derive(Deserialize,Serialize)] #[serde(deny_unknown_fields)]
struct Request{schema_version:String,idempotency_key:IdempotencyKey,project_id:ProjectId,document_id:DocumentId,base_revision:RevisionId,
    expected_head_generation:u64,expected_source_package_sha256:String,plan_id:PlanId,selector:Scope,operation:Operation}
#[derive(Debug,Error)]
pub enum NumberControlProductError{
    #[error("NUMBER_CONTROL_PRODUCT_REQUEST_REJECTED")] Request,
    #[error("NUMBER_CONTROL_PRODUCT_REQUEST_LIMIT")] Limit,
    #[error("NUMBER_CONTROL_PRODUCT_KIND_UNQUALIFIED")] UnsupportedKind,
    #[error("NUMBER_CONTROL_PRODUCT_BINDING_REJECTED")] Binding,
    #[error("NUMBER_CONTROL_PRODUCT_SCOPE_REJECTED")] Scope(#[from] StoredSourceSearchError),
    #[error("NUMBER_CONTROL_PRODUCT_IMPORT_REJECTED")] Import(#[from] StoredActualFormImportError),
    #[error("NUMBER_CONTROL_PRODUCT_CANDIDATE_REJECTED")] Stored(#[from] StoredNumberControlError),
    #[error("NUMBER_CONTROL_FULL_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
type C=NumberControlProductError;
impl Request{
    fn parse(raw:&[u8])->Result<(Self,String),C>{
        let value=super::selector::parse_selector_object(raw).map_err(|e|if matches!(e,LiteralReplacementProductError::Limit){C::Limit}else{C::Request})?;
        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(C::Request)?).map_err(|_|C::Request)?;
        let request:Self=serde_json::from_value(value).map_err(|_|C::Request)?;
        if request.schema_version!=NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA||request.expected_head_generation==0||request.document_id.as_str().len()>1024
            ||!valid_sha(&request.expected_source_package_sha256)||request.selector.revision_id!=request.base_revision
            ||request.operation.max_replacements==0||request.operation.max_replacements>4096{return Err(C::Request);}
        request.selector.validate_shape(has_sections,has_range).map_err(|_|C::Request)?;request.head()?;let canonical=request.canonical_sha()?;Ok((request,canonical))
    }
    fn head(&self)->Result<RevisionHead,C>{RevisionHead::new(Some(revision_service::RevisionId::parse(self.base_revision.as_str()).map_err(|_|C::Request)?),self.expected_head_generation).map_err(|_|C::Request)}
    fn canonical_sha(&self)->Result<String,C>{Ok(digest(&bounded(self,LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
    fn scoped_sha(scope:[u8;32],canonical:&str)->Result<String,C>{Ok(digest(&bounded(&(NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA,scope,canonical),LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES).map_err(|_|C::Limit)?))}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NumberControlProductReceipt{pub profile:&'static str,pub capability_id:&'static str,pub raw_request_sha256:String,
    pub canonical_request_sha256:String,pub scoped_request_sha256:String,pub stored:StoredNumberControlReceipt,
    pub idempotency_key_claimed:bool,pub native_counter_cas_execution_publication_authority:bool}
pub struct PreparedStoredNumberControlProduct{request:Request,candidate:PreparedStoredNumberControlCandidate<'static>,receipt:NumberControlProductReceipt,
    values_sha256:[u8;32],complete_request_sha256:[u8;32]}
impl fmt::Debug for PreparedStoredNumberControlProduct{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedStoredNumberControlProduct(<redacted>; stored_values_not_native_counter_or_transaction)")}}
#[derive(Debug)] pub struct StoredNumberControlProductRequest;
impl StoredNumberControlProductRequest{
    /// # Errors
    /// Unique bounded JSON, exact selectors, kind and immutable typed values before source access.
    pub fn prepare_json<Rp,B,S,V>(provider:&StoredFormProvider<'_,Rp,B,S,V>,raw:&[u8],search_limits:SourceSearchLimits,limits:ReferenceAuxiliaryLimits,writer:WriterLimits,now:u64)
        ->Result<PreparedStoredNumberControlProduct,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let(request,canonical)=Request::parse(raw)?;
        let input=ValidatedNumberControlValues::new(request.operation.control_kind,request.operation.stored_number,request.operation.format.native(),search_limits,limits)
            .map_err(|e|if matches!(e,SourceNumberControlError::UnsupportedKind){C::UnsupportedKind}else{C::Request})?;
        let values_sha256=input.values_sha256();let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let source=provider.import_actual_forms(request.head()?,now)?;
        if hex::encode(source.imported().source().receipt().source_package_sha256)!=request.expected_source_package_sha256{return Err(C::Binding);}
        let candidate=source.into_number_control_candidate(provider,request.selector.native().map_err(|_|C::Request)?,request.operation.review_policy,request.operation.max_replacements,&input,writer,now)?;
        let complete_request_sha256=input.request_sha256(candidate.receipt().output.search.request_sha256()).map_err(|_|C::Binding)?;drop(input);
        let scoped=Request::scoped_sha(scope,&canonical)?;
        let receipt=NumberControlProductReceipt{profile:NUMBER_CONTROL_PRODUCT_PREPARATION_PROFILE,capability_id:"search.replace_control",raw_request_sha256:digest(raw),
            canonical_request_sha256:canonical,scoped_request_sha256:scoped,stored:candidate.receipt().clone(),idempotency_key_claimed:false,native_counter_cas_execution_publication_authority:false};
        let result=PreparedStoredNumberControlProduct{request,candidate,receipt,values_sha256,complete_request_sha256};result.check(provider)?;Ok(result)
    }
}
impl PreparedStoredNumberControlProduct{
    #[must_use] pub const fn receipt(&self)->&NumberControlProductReceipt{&self.receipt}
    fn check<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=&self.request;let output=&self.receipt.stored.output;let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;let canonical=request.canonical_sha()?;
        if request.schema_version!=NUMBER_CONTROL_PRODUCT_REQUEST_SCHEMA||self.receipt.profile!=NUMBER_CONTROL_PRODUCT_PREPARATION_PROFILE
            ||self.receipt.capability_id!="search.replace_control"||self.receipt.canonical_request_sha256!=canonical
            ||self.receipt.scoped_request_sha256!=Request::scoped_sha(scope,&canonical)?||&self.receipt.stored!=self.candidate.receipt()
            ||self.receipt.stored.profile!=STORED_NUMBER_CONTROL_PROFILE||self.receipt.stored.source.head_generation!=request.expected_head_generation
            ||request.selector.revision_id!=request.base_revision||hex::encode(output.source_package_sha256)!=request.expected_source_package_sha256
            ||output.search.kind()!=request.operation.control_kind||output.search.policy()!=request.operation.review_policy||output.search.max_results()!=request.operation.max_replacements
            ||self.receipt.stored.values_sha256!=self.values_sha256||output.request_sha256!=self.complete_request_sha256||!number_control_receipt_matches(output,output.source_package_sha256)
            ||self.receipt.stored.issuer_execution_publication_authority||self.receipt.idempotency_key_claimed||self.receipt.native_counter_cas_execution_publication_authority{return Err(C::Binding);}Ok(())
    }
    /// # Errors
    /// Fresh source/access, writer integrity and final head without replaying the search/compiler.
    pub fn verify<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<NumberControlProductReceipt,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.check(provider)?;if self.candidate.verify(provider,now)?!=self.receipt.stored{return Err(C::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Current access and consumer-final head are independent of retained request digests.
    pub fn with_verified_bytes<Rp,B,S,V,T>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.check(provider)?;Ok(self.candidate.with_verified_bytes(provider,now,consume)?)}
    /// # Errors
    /// No Native evaluation, revision commit/CAS, durable key claim, dispatcher or publication.
    pub fn require_current_product_route<Rp,B,S,V>(&self,provider:&StoredFormProvider<'_,Rp,B,S,V>,now:u64)->Result<(),C>
    where Rp:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{self.verify(provider,now)?;Err(C::RouteUnqualified)}
}
