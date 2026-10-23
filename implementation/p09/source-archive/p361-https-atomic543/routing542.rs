//! HTTPS actual source/policy + original common manifest/storage. No operating registry/route permit.
pub mod job;
pub mod atomic_sql;
use super::*;
use crate::form_product_request::stored_operations::compiled_search::{bounded_hash,routing::{make_for_source,SearchManifestError,
    storage::{PreparedSearchStorage,SearchStorageReceipt,SearchStorageError}}};
use crate::stored_revision_commit::{StoredCommitError,StoredPrecommitGuard};
use domain_ir::{CapabilityRouteCatalog,RouteContext,RouteDecision,TransactionId};
use hwpx_package::document_import::protection::{SourceProtectionObservation,SourceProtectionObservationError};
use operation_engine::{ExecutionManifest,ExecutionManifestError};
pub const HTTPS_TARGET_STORAGE_PROFILE:&str="hwpx-agent.https-target-storage-preparation/v1";
/// Same common job/CAS/one-shot validator primitives; this alias does not confer route authority.
pub type PreparedHttpsTargetStorage<'a>=PreparedSearchStorage<'a>;
pub struct PreparedHttpsTargetExecutionManifest{product:PreparedHttpsTargetProduct,manifest:ExecutionManifest,manifest_sha256:[u8;32],
    routes:Vec<RouteDecision>,target_sha256:[u8;32],protection:SourceProtectionObservation}
impl fmt::Debug for PreparedHttpsTargetExecutionManifest{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.write_str("PreparedHttpsTargetExecutionManifest(<redacted>; unregistered_no_execution_authority)")}}
#[derive(Debug,Error)]
pub enum HttpsTargetManifestError{
    #[error("HTTPS_TARGET_MANIFEST_PRODUCT_DENIED")]Product(#[from]HttpsTargetProductError),
    #[error("HTTPS_TARGET_MANIFEST_PROTECTION_DENIED")]Protection(#[from]SourceProtectionObservationError),
    #[error("HTTPS_TARGET_MANIFEST_COMMON_ROUTE_DENIED")]Route(#[from]SearchManifestError),
    #[error("HTTPS_TARGET_MANIFEST_CANONICAL_DENIED")]Manifest(#[from]ExecutionManifestError),
    #[error("HTTPS_TARGET_MANIFEST_SOURCE_DENIED")]Source(#[from]StoredActualFormImportError),
    #[error("HTTPS_TARGET_MANIFEST_IDENTITY_DENIED")]Identity(#[from]StoredSourceSearchError),
    #[error("HTTPS_TARGET_MANIFEST_STORAGE_DENIED")]Storage(#[from]SearchStorageError),
    #[error("HTTPS_TARGET_MANIFEST_CURRENT_BINDING_CHANGED")]Drift,
    #[error("HTTPS_TARGET_MANIFEST_ATOMIC_POLICY_BINDING_DENIED")]AtomicPolicy,
}
type M=HttpsTargetManifestError;
fn make(product:&PreparedHttpsTargetProduct,protection:&SourceProtectionObservation,context:&RouteContext,catalog:&CapabilityRouteCatalog,transaction:TransactionId,now:u64)
    ->Result<(Vec<RouteDecision>,ExecutionManifest,[u8;32]),M>{
    Ok(make_for_source(product.candidate.source(),product.compiled(),product.receipt.compiled.source_package_sha256,protection,context,catalog,transaction,now)?)
}
impl PreparedHttpsTargetProduct{
    /// # Errors
    /// Current policy/source plus unchanged common source protection, router and manifest validation.
    /// Trusted server routing inputs are data here, not independently attested execution authority.
    pub fn prepare_execution_manifest<R,B,S,V,P>(self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,context:&RouteContext,catalog:&CapabilityRouteCatalog,
        transaction:TransactionId,now:u64)->Result<PreparedHttpsTargetExecutionManifest,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        let((routes,manifest,target_sha256),protection)=self.with_verified_bytes(provider,repository,now,|_|{
            let protection=self.candidate.source().imported().source().observe_protection_signals()?;
            let value=make(&self,&protection,context,catalog,transaction,now)?;
            self.candidate.source().check_compiler_head(provider)?;Ok::<_,M>((value,protection))
        })??;
        let manifest_sha256=manifest.canonical_sha256()?;
        Ok(PreparedHttpsTargetExecutionManifest{product:self,manifest,manifest_sha256,routes,target_sha256,protection})
    }
}
impl PreparedHttpsTargetExecutionManifest{
    #[must_use]pub const fn manifest(&self)->&ExecutionManifest{&self.manifest}
    #[must_use]pub fn routes(&self)->&[RouteDecision]{&self.routes}
    #[must_use]pub const fn product_receipt(&self)->&HttpsTargetProductReceipt{&self.product.receipt}
    /// # Errors
    /// Replays only current routing checks, not source mutation/compilation, and keeps policy mandatory.
    pub fn verify<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,context:&RouteContext,catalog:&CapabilityRouteCatalog,now:u64)->Result<&ExecutionManifest,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.with_verified_bytes(provider,repository,context,catalog,now,|_|())?;Ok(&self.manifest)
    }
    /// # Errors
    /// Sole candidate callback includes original current policy/source/AEAD and whole current route-set checks.
    pub fn with_verified_bytes<R,B,S,V,P,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,context:&RouteContext,catalog:&CapabilityRouteCatalog,now:u64,
        consume:impl FnOnce(&[u8])->T)->Result<T,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.product.with_verified_bytes(provider,repository,now,|bytes|{
            let(routes,manifest,target)=make(&self.product,&self.protection,context,catalog,self.manifest.transaction_id().clone(),now)?;
            if routes!=self.routes||target!=self.target_sha256||manifest.canonical_sha256()?!=self.manifest_sha256
                ||self.manifest.canonical_sha256()?!=self.manifest_sha256{return Err(M::Drift);}
            self.product.candidate.source().check_compiler_head(provider)?;Ok(consume(bytes))
        })?
    }
    /// # Errors
    /// Manifest data never changes the original product route denial.
    pub fn require_current_product_route<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,context:&RouteContext,catalog:&CapabilityRouteCatalog,now:u64)->Result<(),M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.verify(provider,repository,context,catalog,now)?;Ok(self.product.require_current_product_route(provider,repository,now)?)
    }
    /// # Errors
    /// Borrows the sole current source/output into shared storage primitives; no caller replacement bytes or verdict.
    pub fn with_verified_storage_preparation<R,B,S,V,P,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,context:&RouteContext,catalog:&CapabilityRouteCatalog,
        now:u64,consume:impl FnOnce(PreparedHttpsTargetStorage<'_>)->T)->Result<T,M>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        self.with_verified_bytes(provider,repository,context,catalog,now,|output|->Result<T,M>{
            let product=&self.product;let r=&product.receipt;let compiled=&r.compiled;
            let validation=bounded_hash(&(HTTPS_TARGET_STORAGE_PROFILE,r,self.manifest_sha256,output.len()),8*1024*1024).map_err(|_|M::Drift)?;
            let receipt=SearchStorageReceipt{profile:HTTPS_TARGET_STORAGE_PROFILE,request_schema:HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA,
                source_package_sha256:compiled.source_package_sha256,output_package_sha256:compiled.output_package_sha256,output_bytes:output.len(),
                compiled_plan_sha256:compiled.compiled_plan_sha256,manifest_sha256:self.manifest_sha256,validation_contract_sha256:validation,
                validation_executed:false,execution_or_native_authority:false};
            product.candidate.source().with_verified_compiler_source(provider,now,|source,project,branch,head|->Result<T,M>{
                if head.generation()!=compiled.head_generation{return Err(M::Drift);}
                let request=&product.request;
                let identity=provider.source_search_job_identity(&request.project_id,&request.document_id,&request.idempotency_key,&r.canonical_request_sha256,&r.scoped_request_sha256)?;
                product.candidate.source().check_compiler_head(provider)?;
                let prepared=PreparedSearchStorage::bind_verified(source,output,&self.manifest,&request.document_id,(project,branch,head),receipt,identity,
                    (&r.canonical_request_sha256,&r.scoped_request_sha256))?;
                Ok(consume(prepared))
            })?
        })?
    }
    /// Additional current restriction at each ingest/final-CAS boundary; first failure latches.
    /// Server supplies fresh route/time data; this guard is neither a registry permit nor atomic policy lease.
    pub fn current_commit_guard<'a,R,B,S,V,P,F>(&'a self,provider:&'a StoredFormProvider<'_,R,B,S,V>,repository:&'a P,mut current:F)->impl StoredPrecommitGuard+'a
    where R:ArtifactMetadataRepository+'a,B:EncryptedBlobStore+'a,S:ArtifactScanner+'a,V:RevisionRepository+'a,P:HttpsTargetPolicyRepository+'a,
        F:FnMut()->Result<(RouteContext,CapabilityRouteCatalog,u64),()>+'a{
        let mut stopped=false;
        move||{
            if stopped{return Err(StoredCommitError::CurrentGuard);}
            if current().and_then(|(context,routes,now)|self.verify(provider,repository,&context,&routes,now).map(|_|()).map_err(|_|())).is_err(){
                stopped=true;return Err(StoredCommitError::CurrentGuard);
            }Ok(())
        }
    }
}
