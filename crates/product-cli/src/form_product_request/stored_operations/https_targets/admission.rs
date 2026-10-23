//! Exact historic signature evidence retains routing_disabled; never an authority upgrade.
use super::*;
use crate::form_product_request::stored_operations::compiled_search::p02_registry::{PinnedP02RegistryEvidence,PinnedRegistryError};
#[derive(Debug,Error)]
pub enum RegistryBoundHttpsTargetError{
    #[error("HTTPS_TARGET_PINNED_REGISTRY_DENIED")]Registry(#[from]PinnedRegistryError),
    #[error("HTTPS_TARGET_PINNED_REQUEST_DENIED")]Product(#[from]HttpsTargetProductError),
}
impl StoredProductRequest{
    /// # Errors
    /// Strict request values, then authenticated preserved policy, BEFORE any source/policy preparation.
    /// The current pinned snapshot denies routing. No caller support flag, fallback or registry mutation.
    pub fn prepare_https_targets_json_with_pinned_registry<R,B,S,V,P>(provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,raw:&[u8],
        limits:HttpsTargetProductLimits,registry:&PinnedP02RegistryEvidence,now:u64)->Result<PreparedHttpsTargetProduct,RegistryBoundHttpsTargetError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        let request=Request::parse(raw,limits)?;registry.require_routing()?;
        Ok(prepare(provider,repository,request,raw,limits,now)?)
    }
}
