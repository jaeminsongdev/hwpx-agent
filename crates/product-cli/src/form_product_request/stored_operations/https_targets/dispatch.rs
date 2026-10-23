//! Server-policy-aware common dispatch. No inferred policy, route grant or alternate executor.
pub mod atomic_sql;
pub mod recovery;
use super::*;
use super::super::{PreparedStoredProductOperation,StoredProductOperationError,StoredProductFormBindings,search_mutations,request};

/// Validated server budgets; no request can supply a policy artifact or replace its repository.
#[derive(Clone,Copy,Debug)]
pub struct PolicyBoundOperationLimits{pub search:search_mutations::SearchMutationLimits,pub https:HttpsTargetProductLimits}
impl PolicyBoundOperationLimits{
    /// # Errors
    /// Reuses both original finite server budget constructors.
    pub fn standard()->Result<Self,StoredProductOperationError>{Ok(Self{search:search_mutations::SearchMutationLimits::standard()?,https:HttpsTargetProductLimits::standard()?})}
}
impl StoredProductRequest{
    /// # Errors
    /// Classifies once, then uses the unchanged family preparation. HTTPS rejects legacy bindings;
    /// all other families retain their original behavior and never consult the HTTPS repository.
    pub fn prepare_json_with_https_policy<R,B,S,V,P>(provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,raw:&[u8],
        bindings:Option<&StoredProductFormBindings<'_>>,limits:PolicyBoundOperationLimits,now:u64)
        ->Result<PreparedStoredProductOperation,StoredProductOperationError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        match request::classify(raw)?{
            request::Kind::HttpsTargets=>{
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(PreparedStoredProductOperation::HttpsTargets(Box::new(Self::prepare_https_targets_json(provider,repository,raw,limits.https,now)?)))
            }
            kind=>Self::prepare_classified(provider,raw,bindings,limits.search,now,kind),
        }
    }
}
impl PreparedStoredProductOperation{
    /// Read-only access to the original compiled HTTPS product and its existing manifest/job bridge.
    /// This is not a policy refresh, claim, registration or execution permission.
    #[must_use]pub fn as_https_targets(&self)->Option<&PreparedHttpsTargetProduct>{match self{Self::HttpsTargets(product)=>Some(product),_=>None}}
    /// # Errors
    /// Rechecks the original current source/policy before delivering HTTPS bytes. The unqualified
    /// no-repository method still refuses this variant; ordinary variants use their original path.
    pub fn with_verified_bytes_with_https_policy<R,B,S,V,P,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,
        bindings:Option<&StoredProductFormBindings<'_>>,now:u64,consume:impl FnOnce(&[u8])->T)->Result<T,StoredProductOperationError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        match self{
            Self::HttpsTargets(product)=>{
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(product.with_verified_bytes(provider,repository,now,consume)?)
            }
            _=>self.with_verified_bytes(provider,bindings,now,consume),
        }
    }
    /// # Errors
    /// Keeps the original product's RouteUnqualified after fresh source/policy checks. Supplying
    /// a repository does not upgrade the historic registry or grant publication authority.
    pub fn require_current_product_route_with_https_policy<R,B,S,V,P>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,
        bindings:Option<&StoredProductFormBindings<'_>>,now:u64)->Result<(),StoredProductOperationError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository,P:HttpsTargetPolicyRepository{
        match self{
            Self::HttpsTargets(product)=>{
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                Ok(product.require_current_product_route(provider,repository,now)?)
            }
            _=>self.require_current_product_route(provider,bindings,now),
        }
    }
}
