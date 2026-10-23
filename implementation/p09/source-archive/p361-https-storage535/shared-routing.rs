//! Original router and execution manifest bound to the actual source candidate, not execution authority.
pub mod storage;
use super::*;
use domain_ir::{BackendKind,CapabilityRouteCatalog,CapabilityRouter,CapabilityRouterError,CapabilityRouterLimits,
    RouteContext,RouteDecision,TransactionId};
use operation_engine::{ExecutionManifest,ExecutionManifestError};
use hwpx_package::document_import::protection::{SourceProtectionObservation,SourceProtectionObservationError};

/// No public constructor or data deserialization. Manifest and routes are data for the later trusted executor.
/// The caller supplies server-owned routing evidence; this adapter does not attest its provenance.
pub struct PreparedSearchExecutionManifest{
    compiled:PreparedCompiledSearchMutation,
    manifest:ExecutionManifest,
    manifest_sha256:[u8;32],
    target_profile_sha256:[u8;32],
    routes:Vec<RouteDecision>,
    source_protection:SourceProtectionObservation,
}
impl fmt::Debug for PreparedSearchExecutionManifest{
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedSearchExecutionManifest(<redacted>; execution_unqualified)")}
}
impl PreparedCompiledSearchMutation{
    /// # Errors
    /// Fresh original source checks, all original routing guards and exact source/plan manifest binding.
    /// Moves this candidate; accepts no caller-selected source artifact, bytes, plan or route receipts.
    pub fn prepare_execution_manifest<R,B,S,V>(self,provider:&StoredFormProvider<'_,R,B,S,V>,context:&RouteContext,
        catalog:&CapabilityRouteCatalog,transaction:TransactionId,now:u64)->Result<PreparedSearchExecutionManifest,SearchManifestError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let((routes,manifest,target_profile_sha256),source_protection)=self.with_verified_bytes(provider,now,|_|{
            let source_protection=self.candidate.compiler_view().source.imported().source().observe_protection_signals()?;
            let value=make(&self,&source_protection,context,catalog,transaction,now)?;
            self.candidate.compiler_view().source.check_compiler_head(provider).map_err(CompiledSearchError::from)?;
            Ok::<_,SearchManifestError>((value,source_protection))
        })??;
        let manifest_sha256=manifest.canonical_sha256()?;
        Ok(PreparedSearchExecutionManifest{compiled:self,manifest,manifest_sha256,target_profile_sha256,routes,source_protection})
    }
}
impl PreparedSearchExecutionManifest{
    #[must_use] pub const fn manifest(&self)->&ExecutionManifest{&self.manifest}
    #[must_use] pub fn routes(&self)->&[RouteDecision]{&self.routes}
    #[must_use] pub const fn compiled_receipt(&self)->&CompiledSearchReceipt{self.compiled.receipt()}
    #[must_use] pub const fn source_protection_observation(&self)->&SourceProtectionObservation{&self.source_protection}
    /// # Errors
    /// A held manifest retains no source access or backend-health lease. Current routing is replayed,
    /// not source import/search/operation compilation, and every selected route must remain identical.
    pub fn verify<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,context:&RouteContext,catalog:&CapabilityRouteCatalog,now:u64)
        ->Result<&ExecutionManifest,SearchManifestError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.with_verified_bytes(provider,context,catalog,now,|_|())?;Ok(&self.manifest)
    }
    /// # Errors
    /// Rechecks the whole route set and actual source immediately before the sole original byte callback.
    /// Does not claim a key, ingest, commit, publish, execute a backend or authorize Native.
    pub fn with_verified_bytes<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,context:&RouteContext,
        catalog:&CapabilityRouteCatalog,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,SearchManifestError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.compiled.with_verified_bytes(provider,now,|bytes|{
            let(routes,manifest,target)=make(&self.compiled,&self.source_protection,context,catalog,self.manifest.transaction_id().clone(),now)?;
            if routes!=self.routes||target!=self.target_profile_sha256||manifest.canonical_sha256()?!=self.manifest_sha256
                ||self.manifest.canonical_sha256()?!=self.manifest_sha256{return Err(SearchManifestError::Drift);}
            self.compiled.candidate.compiler_view().source.check_compiler_head(provider).map_err(CompiledSearchError::from)?;
            Ok(consume(bytes))
        })?
    }
    /// # Errors
    /// Preserves the original product route denial even if pure router/manifest data checks pass.
    pub fn require_current_product_route<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,context:&RouteContext,
        catalog:&CapabilityRouteCatalog,now:u64)->Result<(),SearchManifestError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        self.verify(provider,context,catalog,now)?;Ok(self.compiled.require_current_product_route(provider,now)?)
    }
}
fn make(compiled:&PreparedCompiledSearchMutation,protection:&SourceProtectionObservation,context:&RouteContext,catalog:&CapabilityRouteCatalog,transaction:TransactionId,now:u64)
    ->Result<(Vec<RouteDecision>,ExecutionManifest,[u8;32]),SearchManifestError>{
    make_for_view(&compiled.candidate.compiler_view(),compiled.compiled(),compiled.receipt(),protection,context,catalog,transaction,now)
}
pub(super) fn make_for_view(v:&CompilationView<'_>,plan:&CompiledOperationPlan,receipt:&CompiledSearchReceipt,
    protection:&SourceProtectionObservation,context:&RouteContext,catalog:&CapabilityRouteCatalog,transaction:TransactionId,now:u64)
    ->Result<(Vec<RouteDecision>,ExecutionManifest,[u8;32]),SearchManifestError>{
    // Artifact service time is seconds; router health time is milliseconds. Never reuse an old clock snapshot.
    if now.checked_mul(1000)!=Some(context.now_unix_ms()){return Err(SearchManifestError::Time);}
    protection.verify_binding(v.source.imported().source())?;
    protection.require_no_observed_document_signals()?;
    let routes=CapabilityRouter::new(CapabilityRouterLimits::default())?.route_plan(plan,context,catalog)?;
    // This retained candidate is a DirectHwpx result. Automation/hybrid needs its own qualified executor.
    if routes.iter().any(|route|route.backend_kind()!=BackendKind::DirectHwpx){return Err(SearchManifestError::Backend);}
    let source=v.source.receipt();
    let artifact=domain_ir::ArtifactId::parse(source.source_artifact.public_id()).map_err(|_|SearchManifestError::Identity)?;
    let source_size=u64::try_from(source.source_bytes).map_err(|_|SearchManifestError::Identity)?;
    let manifest=ExecutionManifest::from_receipts(transaction,artifact,receipt.source_package_sha256,source_size,plan,&routes)?;
    let target=bounded_hash(context.target_profile(),4096)?;
    Ok((routes,manifest,target))
}
#[derive(Debug,Error)]
pub enum SearchManifestError{
    #[error("search_manifest_original_source_protection_rejected")] SourceProtection(#[from]SourceProtectionObservationError),
    #[error("search_manifest_original_candidate_rejected")] Candidate(#[from]CompiledSearchError),
    #[error("search_manifest_original_router_rejected")] Route(#[from]CapabilityRouterError),
    #[error("search_manifest_original_manifest_rejected")] Manifest(#[from]ExecutionManifestError),
    #[error("search_manifest_routing_snapshot_time_rejected")] Time,
    #[error("search_manifest_current_binding_drift")] Drift,
    #[error("search_manifest_direct_candidate_backend_mismatch")] Backend,
    #[error("search_manifest_source_identity_rejected")] Identity,
}
