//! Common request entry: observe first, compile only a genuinely unobserved request.
//! Neither branch grants execution, retry, claim, publication or completed-effect authority.
use super::*;
use crate::form_product_request::stored_literal_replacement::personal_info::catalog::request_lookup::CatalogRequestLookupError;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    lifecycle::StoredJobObservation,
    request_lookup::{StoredRequestLookupRepository,StoredRequestObservation},
};

#[derive(Debug,Error)]
pub enum CatalogRequestEntryError{
    #[error("CATALOG_REQUEST_ENTRY_LOOKUP_REJECTED")]
    Lookup(#[from]CatalogRequestLookupError),
    #[error("CATALOG_REQUEST_ENTRY_PREPARATION_REJECTED")]
    Preparation(#[from]CatalogMaskCompilationError),
}

/// Existing is metadata only; Prepared still requires current manifest/route/storage guards.
pub enum CatalogRequestEntry{
    Existing(StoredJobObservation),
    Prepared(Box<PreparedCompiledCatalogMask>),
}
impl fmt::Debug for CatalogRequestEntry{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
        f.write_str(match self{Self::Existing(_)=>"CatalogRequestEntry::Existing(<redacted>; observation_not_authority)",
            Self::Prepared(_)=>"CatalogRequestEntry::Prepared(<redacted>; route_unqualified)"})
    }
}

impl StoredProductRequest{
    /// # Errors
    /// Strict parse/current scope/SQL observation precede any document/catalog/compiler I/O.
    /// Lookup conflicts, denial and unknown outcomes propagate without a preparation fallback.
    /// NotObserved is not an absence lease: the original job claim still resolves later races.
    pub fn prepare_catalog_mask_or_observe_json<R,B,S,V>(
        provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&dyn CurrentPersonalInfoCatalogSource,
        raw:&[u8],limits:SearchMutationLimits,now:u64,
    )->Result<CatalogRequestEntry,CatalogRequestEntryError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository{
        let lookup=StoredPersonalInfoCatalogMaskProductRequest::prepare_lookup_json(provider,raw)?;
        match lookup.observe(provider)?{
            StoredRequestObservation::Existing(observation)=>Ok(CatalogRequestEntry::Existing(observation)),
            StoredRequestObservation::NotObserved=>Ok(CatalogRequestEntry::Prepared(Box::new(
                Self::prepare_compiled_catalog_mask_json(provider,catalog,raw,limits,now)?))),
        }
    }
}
