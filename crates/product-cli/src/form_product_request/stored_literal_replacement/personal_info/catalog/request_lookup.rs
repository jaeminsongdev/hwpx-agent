//! Parse/auth-scope only before observation. No ZIP/import/catalog/regex/compiler or claim.
use super::*;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::{
    StoredRequestLookup,StoredRequestLookupRepository,StoredRequestLookupError,StoredRequestObservation};
#[derive(Debug,Error)]
pub enum CatalogRequestLookupError{
    #[error("CATALOG_REQUEST_LOOKUP_PREPARATION_REJECTED")]Preparation(#[from]PersonalInfoCatalogMaskProductError),
    #[error("CATALOG_REQUEST_LOOKUP_SCOPE_REJECTED")]Scope(#[from]StoredSourceSearchError),
    #[error("CATALOG_REQUEST_LOOKUP_REPOSITORY_REJECTED")]Repository(#[from]StoredRequestLookupError),
    #[error("CATALOG_REQUEST_RECOVERY_REJECTED")]Recovery(#[from]crate::form_stored_provider::actual_import::source_search::request_recovery::StoredRequestRecoveryError),
}
pub struct PreparedCatalogRequestLookup{lookup:StoredRequestLookup,project:ProjectId,document:DocumentId,scope:[u8;32]}
impl fmt::Debug for PreparedCatalogRequestLookup{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedCatalogRequestLookup(<redacted>; observation_not_authority)")}}
impl StoredPersonalInfoCatalogMaskProductRequest{
    /// # Errors
    /// Original strict16KiB request and current authenticated write/five-scope only.
    /// A stale head/current catalog must NOT force recompilation merely to observe an existing job.
    pub fn prepare_lookup_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8])->Result<PreparedCatalogRequestLookup,CatalogRequestLookupError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let request=Request::parse(raw)?;if request.operation.preview_only{return Err(P::PreviewOnly.into());}
        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;
        let lookup=provider.source_search_request_lookup(&request.project_id,&request.document_id,&request.idempotency_key,&request.canonical_sha()?,
            &request.scoped_sha(scope)?,artifact_service::ContentDigest::parse(&request.expected_source_package_sha256).map_err(|_|P::Request)?,request.head()?)?;
        Ok(PreparedCatalogRequestLookup{lookup,project:request.project_id,document:request.document_id,scope})
    }
}
impl PreparedCatalogRequestLookup{
    /// # Errors
    /// Explicit effect readback; the existing observe() metadata fast path is unchanged.
    /// Current strict provider scope and SQL ACL/request checks precede registered ACL/AEAD recovery.
    /// No original manifest, saved claim, caller locator, catalog/compiler or execution authority.
    pub fn recover_registered<R,B,S,V,F>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,clock:F)
        ->Result<crate::form_stored_provider::actual_import::source_search::request_recovery::StoredRequestRecoveryObservation,CatalogRequestLookupError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,
        V:StoredRequestLookupRepository+revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::StoredRevisionJobRepository,F:FnMut()->u64{
        if provider.source_search_product_scope(&self.project,&self.document)?!=self.scope{return Err(P::Binding.into());}
        Ok(provider.recover_source_request(&self.lookup,clock)?)
    }
    /// # Errors
    /// Refreshes authenticated provider scope; repository independently enforces ACL/source/request binding.
    /// Both NotObserved and Existing are observations only, never lease/retry/commit or Native permits.
    pub fn observe<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>)->Result<StoredRequestObservation,CatalogRequestLookupError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredRequestLookupRepository{
        if provider.source_search_product_scope(&self.project,&self.document)?!=self.scope{return Err(P::Binding.into());}
        Ok(provider.observe_source_request(&self.lookup)?)
    }
}
