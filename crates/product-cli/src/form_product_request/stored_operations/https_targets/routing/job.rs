//! Original server job coordinator with mandatory current guards, never a product admission permit.
use super::*;
use crate::stored_revision_commit::job::{PreparedStoredJob,identity::StoredJobPolicy};
use crate::form_product_request::stored_operations::compiled_search::routing::storage::SearchOutputValidator;
use operation_engine::TransactionLimits;
use revision_service::{CommitId,RevisionId};
impl PreparedHttpsTargetExecutionManifest{
    /// Trusted server primitive only: registration/claim/lease/execution remain the original coordinator's responsibility.
    /// This callback cannot retain source/output borrows or replace the automatically attached guard.
    /// # Errors
    /// Refreshes source/policy/routes, binds common deterministic job inputs and attaches the same guard
    /// before the first claim and both mutation boundaries. No replay/unknown-outcome policy is changed.
    #[allow(clippy::too_many_arguments)]
    pub fn with_verified_guarded_job_preparation<'a,R,B,S,V,P,F,T>(&'a self,provider:&'a StoredFormProvider<'_,R,B,S,V>,repository:&'a P,
        policy:StoredJobPolicy,commit:CommitId,new_revision:RevisionId,limits:TransactionLimits,mut current:F,
        consume:impl FnOnce(PreparedStoredJob<'_>,&[u8],SearchOutputValidator<'_>)->T)->Result<T,HttpsTargetManifestError>
    where R:ArtifactMetadataRepository+'a,B:EncryptedBlobStore+'a,S:ArtifactScanner+'a,V:RevisionRepository+'a,P:HttpsTargetPolicyRepository+'a,
        F:FnMut()->Result<(RouteContext,CapabilityRouteCatalog,u64),()>+'a{
        let(context,routes,now)=current().map_err(|_|HttpsTargetManifestError::Drift)?;
        self.with_verified_storage_preparation(provider,repository,&context,&routes,now,|input|{
            let mut job=input.prepare_bound_job(policy,commit,new_revision,limits)?;
            job.require_precommit_guard(Box::new(self.current_commit_guard(provider,repository,current))).map_err(SearchStorageError::from)?;
            Ok::<_,HttpsTargetManifestError>(consume(job,input.source_bytes(),input.output_validator()))
        })?
    }
}
