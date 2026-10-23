//! All current mutation schemas: observe first, never replay merely to find an existing request.
use super::*;
use domain_ir::{ProjectId,DocumentId,IdempotencyKey};
use artifact_service::ContentDigest;
use crate::form_stored_provider::actual_import::source_search::{StoredSourceSearchError,
    request_recovery::{StoredRequestRecoveryError,StoredRequestRecoveryObservation}};
use revision_service::{RevisionHead,postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    StoredRevisionJobRepository,lifecycle::StoredJobObservation,request_lookup::{StoredRequestLookup,StoredRequestLookupRepository,StoredRequestLookupError,StoredRequestObservation}}};

#[derive(Debug,Error)]
pub enum SearchRequestLookupError {
    #[error("SEARCH_REQUEST_LOOKUP_STRICT_REQUEST_REJECTED")]Request,
    #[error("SEARCH_REQUEST_LOOKUP_KIND_OR_PREVIEW_REJECTED")]Kind,
    #[error("SEARCH_REQUEST_LOOKUP_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("SEARCH_REQUEST_LOOKUP_REPOSITORY_REJECTED")]Repository(#[from]StoredRequestLookupError),
    #[error("SEARCH_REQUEST_LOOKUP_CURRENT_BINDING_REJECTED")]Binding,
    #[error("SEARCH_REQUEST_LOOKUP_RECOVERY_REJECTED")]Recovery(#[from]StoredRequestRecoveryError),
}
/// Owned observation binding only. No public constructor, deserializer, source bytes or execution rights.
pub struct PreparedSearchRequestLookup {lookup:StoredRequestLookup,project:ProjectId,document:DocumentId,scope:[u8;32],canonical:ContentDigest,scoped:ContentDigest}
impl fmt::Debug for PreparedSearchRequestLookup {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedSearchRequestLookup(<redacted>; observation_not_authority)")}}
impl PreparedSearchRequestLookup {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn bind<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,project:&ProjectId,document:&DocumentId,key:&IdempotencyKey,
        canonical:&str,scoped:&str,source:ContentDigest,head:RevisionHead,scope:[u8;32])->Result<Self,SearchRequestLookupError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let lookup=provider.source_search_request_lookup(project,document,key,canonical,scoped,source,head)?;
        let canonical=ContentDigest::parse(canonical).map_err(|_|SearchRequestLookupError::Request)?;
        let scoped=ContentDigest::parse(scoped).map_err(|_|SearchRequestLookupError::Request)?;
        Ok(Self {lookup,project:project.clone(),document:document.clone(),scope,canonical,scoped})
    }
    /// Data identifiers only; neither digest grants execution, observation rights or a key claim.
    #[must_use]pub fn canonical_request_sha256(&self)->[u8;32] {*self.canonical.as_bytes()}
    #[must_use]pub fn scoped_request_sha256(&self)->[u8;32] {*self.scoped.as_bytes()}
    /// # Errors
    /// Current provider binding and repository ACL/request checks; no source/head/mutator fallback.
    pub fn observe<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<StoredRequestObservation,SearchRequestLookupError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository {
        if provider.source_search_product_scope(&self.project,&self.document)?!=self.scope{return Err(SearchRequestLookupError::Binding);}
        Ok(provider.observe_source_request(&self.lookup)?)
    }
    /// # Errors
    /// Explicit existing-effect readback through the original registered archive/ACL/AEAD recovery.
    /// A status observation alone is never independent effect proof or a new-execution/retry permit.
    pub fn recover_registered<R,B,S,V,F>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,clock:F)->Result<StoredRequestRecoveryObservation,SearchRequestLookupError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository+StoredRevisionJobRepository,F:FnMut()->u64 {
        if provider.source_search_product_scope(&self.project,&self.document)?!=self.scope{return Err(SearchRequestLookupError::Binding);}
        Ok(provider.recover_source_request(&self.lookup,clock)?)
    }
}
pub enum SearchRequestEntry {Existing(StoredJobObservation),Prepared(Box<PreparedCompiledSearchMutation>)}
impl fmt::Debug for SearchRequestEntry {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str(match self {
    Self::Existing(_)=>"SearchRequestEntry::Existing(<redacted>; observation_not_authority)",Self::Prepared(_)=>"SearchRequestEntry::Prepared(<redacted>; route_unqualified)"})}}
#[derive(Debug,Error)]
pub enum SearchRequestEntryError {
    #[error("SEARCH_REQUEST_ENTRY_LOOKUP_REJECTED")]Lookup(#[from]SearchRequestLookupError),
    #[error("SEARCH_REQUEST_ENTRY_COMPILATION_REJECTED")]Preparation(#[from]CompiledSearchError),
}
impl StoredProductRequest {
    /// # Errors
    /// The closed dispatcher and EACH original strict parser precede observation. Preview is not a mutation.
    /// Request hashes match the original product, including v2 atoms and review/insertion wrappers.
    pub fn prepare_search_lookup_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8])->Result<PreparedSearchRequestLookup,SearchRequestLookupError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
        let request::Kind::SearchMutation(family)=request::classify(raw).map_err(|_|SearchRequestLookupError::Request)? else{return Err(SearchRequestLookupError::Kind)};
        Ok(super::super::search_mutations::prepare_lookup(family,provider,raw)?)
    }
    /// # Errors
    /// Existing and repository errors never run source preparation. NotObserved is not an absence lease:
    /// the unchanged durable claim must still resolve races and immutable-binding conflicts later.
    pub fn prepare_search_or_observe_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],limits:SearchMutationLimits,now:u64)
        ->Result<SearchRequestEntry,SearchRequestEntryError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository {
        let lookup=Self::prepare_search_lookup_json(provider,raw)?;
        match lookup.observe(provider)? {
            StoredRequestObservation::Existing(job)=>Ok(SearchRequestEntry::Existing(job)),
            StoredRequestObservation::NotObserved=>Ok(SearchRequestEntry::Prepared(Box::new(Self::prepare_compiled_search_json(provider,raw,limits,now)?))),
        }
    }
}
