//! Common request recovery uses the original scoped observer before any HTTPS preparation.
//! An existing observation is not a result download, route grant, claim or retry permit.
use super::*;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    lifecycle::StoredJobObservation,request_lookup::StoredRequestLookupRepository};

pub enum PolicyBoundRequestEntry{
    ExistingHttps(StoredJobObservation),
    Prepared(Box<PreparedStoredProductOperation>),
}
impl std::fmt::Debug for PolicyBoundRequestEntry{
    fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result{
        f.write_str(match self{
            Self::ExistingHttps(_)=>"PolicyBoundRequestEntry::ExistingHttps(<redacted>; observation_only; no_retry_permit)",
            Self::Prepared(_)=>"PolicyBoundRequestEntry::Prepared(<redacted>; route_unqualified)",
        })
    }
}
impl StoredProductRequest{
    /// # Errors
    /// Authenticated server entry: classify once, reject legacy HTTPS bindings, then reuse the
    /// strict scoped observer. Existing jobs and lookup errors never fall back to fresh work.
    /// NotObserved only permits candidate preparation, not execution or a claim; original
    /// durable claim/lease/policy/CAS guards still decide races. Other families retain their
    /// original preparation and never query either HTTPS repository or request observer.
    pub fn prepare_json_or_observe_with_https_policy<R,B,S,V,P>(
        provider:&StoredFormProvider<'_,R,B,S,V>,repository:&P,raw:&[u8],
        bindings:Option<&StoredProductFormBindings<'_>>,limits:PolicyBoundOperationLimits,now:u64,
    )->Result<PolicyBoundRequestEntry,StoredProductOperationError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,
        V:StoredRequestLookupRepository,P:HttpsTargetPolicyRepository{
        let product=match request::classify(raw)?{
            request::Kind::HttpsTargets=>{
                if bindings.is_some(){return Err(StoredProductOperationError::Bindings);}
                match Self::prepare_https_targets_or_observe_json(provider,repository,raw,limits.https,now)?{
                    HttpsTargetRequestEntry::Existing(job)=>return Ok(PolicyBoundRequestEntry::ExistingHttps(job)),
                    HttpsTargetRequestEntry::Prepared(product)=>PreparedStoredProductOperation::HttpsTargets(product),
                }
            }
            kind=>Self::prepare_classified(provider,raw,bindings,limits.search,now,kind)?,
        };
        Ok(PolicyBoundRequestEntry::Prepared(Box::new(product)))
    }
}
