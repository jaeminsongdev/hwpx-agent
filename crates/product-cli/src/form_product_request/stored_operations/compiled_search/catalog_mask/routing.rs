//! Current catalog and original shared routing/protection/manifest checks. Data, not execution authority.
pub mod storage;
use super::*;
use super::super::routing::{make_for_view,SearchManifestError};
use domain_ir::{CapabilityRouteCatalog,RouteContext,RouteDecision,TransactionId};
use operation_engine::ExecutionManifest;
use hwpx_package::document_import::protection::SourceProtectionObservation;

#[derive(Debug,Error)]
pub enum CatalogMaskManifestError{
    #[error("CATALOG_MASK_MANIFEST_CANDIDATE_REJECTED")]Candidate(#[from]CatalogMaskCompilationError),
    #[error("CATALOG_MASK_MANIFEST_PRODUCT_REJECTED")]Product(#[from]PersonalInfoCatalogMaskProductError),
    #[error("CATALOG_MASK_MANIFEST_ORIGINAL_ROUTING_REJECTED")]Routing(#[from]SearchManifestError),
}
type M=CatalogMaskManifestError;
/// No public constructor, caller bytes, source, plan, routes or deserialization.
pub struct PreparedCatalogMaskExecutionManifest{
    compiled:PreparedCompiledCatalogMask,manifest:ExecutionManifest,manifest_sha256:[u8;32],
    target_profile_sha256:[u8;32],routes:Vec<RouteDecision>,protection:SourceProtectionObservation,
}
impl fmt::Debug for PreparedCatalogMaskExecutionManifest{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedCatalogMaskExecutionManifest(<redacted>; current_catalog_required_execution_unqualified)")}
}
impl PreparedCompiledCatalogMask{
    /// # Errors
    /// Moves the retained source owner. Both route evidence and current format catalog are mandatory.
    pub fn prepare_execution_manifest<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,formats:&dyn CurrentPersonalInfoCatalogSource,
        context:&RouteContext,routes:&CapabilityRouteCatalog,transaction:TransactionId,now:u64)->Result<PreparedCatalogMaskExecutionManifest,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let((decisions,manifest,target),protection,manifest_sha256)=self.with_verified_bytes(provider,formats,now,|_|->Result<_,M>{
            let view=self.candidate.compiler_view()?;
            let protection=view.source.imported().source().observe_protection_signals().map_err(SearchManifestError::from)?;
            let result=make_for_view(&view,&self.plan,&self.receipt,&protection,context,routes,transaction,now)?;
            let hash=result.1.canonical_sha256().map_err(SearchManifestError::from)?;
            self.candidate.check_final_inputs(provider,formats)?;Ok((result,protection,hash))
        })??;
        Ok(PreparedCatalogMaskExecutionManifest{compiled:self,manifest,manifest_sha256,target_profile_sha256:target,routes:decisions,protection})
    }
}
impl PreparedCatalogMaskExecutionManifest{
    #[must_use]pub const fn manifest(&self)->&ExecutionManifest{&self.manifest}
    #[must_use]pub fn routes(&self)->&[RouteDecision]{&self.routes}
    #[must_use]pub const fn compiled_receipt(&self)->&CompiledSearchReceipt{self.compiled.receipt()}
    #[must_use]pub const fn source_protection_observation(&self)->&SourceProtectionObservation{&self.protection}
    /// # Errors
    /// Refreshes current access/config/route health before delivery; never reruns the matcher/compiler.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,formats:&dyn CurrentPersonalInfoCatalogSource,
        context:&RouteContext,routes:&CapabilityRouteCatalog,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.compiled.with_verified_bytes(provider,formats,now,|bytes|->Result<T,M>{
            let view=self.compiled.candidate.compiler_view()?;
            let(current,manifest,target)=make_for_view(&view,&self.compiled.plan,&self.compiled.receipt,&self.protection,
                context,routes,self.manifest.transaction_id().clone(),now)?;
            if current!=self.routes||target!=self.target_profile_sha256
                ||manifest.canonical_sha256().map_err(SearchManifestError::from)?!=self.manifest_sha256
                ||self.manifest.canonical_sha256().map_err(SearchManifestError::from)?!=self.manifest_sha256{
                return Err(SearchManifestError::Drift.into());}
            self.compiled.candidate.check_final_inputs(provider,formats)?;Ok(consume(bytes))
        })?
    }
    /// # Errors
    /// Manifest data is not a retained access, configuration or backend-health lease.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,formats:&dyn CurrentPersonalInfoCatalogSource,
        context:&RouteContext,routes:&CapabilityRouteCatalog,now:u64)->Result<&ExecutionManifest,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_bytes(provider,formats,context,routes,now,|_|())?;Ok(&self.manifest)
    }
    /// # Errors
    /// Keeps original route denial; no key claim, executor, ingest, CAS, publication or Native permission.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,formats:&dyn CurrentPersonalInfoCatalogSource,
        context:&RouteContext,routes:&CapabilityRouteCatalog,now:u64)->Result<(),M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.verify(provider,formats,context,routes,now)?;Ok(self.compiled.require_current_product_route(provider,formats,now)?)
    }
}
