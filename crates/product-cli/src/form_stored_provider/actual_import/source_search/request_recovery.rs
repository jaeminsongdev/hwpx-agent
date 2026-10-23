//! Explicit read-only recovery after exact public-request observation. Never a claim/retry path.
use super::*;
use crate::stored_revision_commit::{ArchivedRegisteredStoredCommitRecoveryOutcome as Archive,
    StoredCommitRecoveryOutcome,StoredCommitError,reconcile_archived_registered_stored_commit};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    StoredRevisionJobRepository,StoredCommitIntentLookup,lifecycle::{StoredJobObservation,StoredJobOutcome},
    request_lookup::{StoredRequestLookup,StoredRequestLookupRepository,StoredRequestLookupError,StoredRequestObservation}};

#[derive(Debug,Error)]
pub enum StoredRequestRecoveryError{
    #[error("REQUEST_RECOVERY_LOOKUP_REJECTED")]Lookup(#[from]StoredRequestLookupError),
    #[error("REQUEST_RECOVERY_EFFECT_REJECTED")]Recovery(#[from]StoredCommitError),
    #[error("REQUEST_RECOVERY_BINDING_REJECTED")]Binding,
    #[error("REQUEST_RECOVERY_OBSERVATION_CHANGED")]ObservationChanged,
}
/// Missing request, no attempt, and archived recovery outcomes are never no-effect/retry permits.
#[derive(Clone,Debug,Eq,PartialEq)]
pub enum StoredRequestRecoveryObservation{
    NotObserved,
    AttemptNotStarted(StoredJobObservation),
    Existing{job:StoredJobObservation,effect:Archive},
}
impl<R,B,S,V> StoredFormProvider<'_,R,B,S,V>
where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,
    V:StoredRequestLookupRepository+StoredRevisionJobRepository{
    pub(crate) fn recover_source_request<F:FnMut()->u64>(&self,lookup:&StoredRequestLookup,clock:F)
        ->Result<StoredRequestRecoveryObservation,StoredRequestRecoveryError>{
        use StoredRequestRecoveryError as E;use StoredRequestRecoveryObservation as O;
        // The unchanged SQL lookup checks the complete immutable request/current project/source ACL.
        let StoredRequestObservation::Existing(job)=self.observe_source_request(lookup)? else{return Ok(O::NotObserved)};
        if job.outcome()!=StoredJobOutcome::Replay||job.job_id()!=lookup.job_id(){return Err(E::Binding);}
        if job.attempt_no()==0{return Ok(O::AttemptNotStarted(job));}
        let locator=StoredCommitIntentLookup::new(lookup.project_id(),lookup.idempotency_key(),lookup.job_id(),job.attempt_no()).map_err(|_|E::Binding)?;
        let effect=reconcile_archived_registered_stored_commit(self.artifacts,self.revisions,self.artifact_context,self.revision_context,locator,clock)?;
        if let Archive::Registered(StoredCommitRecoveryOutcome::Committed{receipt,..})=&effect{
            if job.result_revision_id().is_some_and(|revision|receipt.committed_head().revision_id()!=Some(revision)){return Err(E::Binding);}
        }
        // Bounded second lookup: do not return content obtained across a source-ACL/state/attempt change.
        // A race is reported, never retried, reconciled into a job transition, or converted to a new job.
        if self.observe_source_request(lookup)?!=StoredRequestObservation::Existing(job.clone()){return Err(E::ObservationChanged);}
        Ok(O::Existing{job,effect})
    }
}
