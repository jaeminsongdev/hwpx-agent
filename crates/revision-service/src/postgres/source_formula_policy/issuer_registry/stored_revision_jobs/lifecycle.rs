//! Typed SQL23 job boundary. Observations are not execution permits or Native qualification.
//! No automatic retry, lease recovery, migrations, grants or no-effect inference.
use super::*;
use artifact_service::ArtifactId;
mod sql;
pub(super) fn admit_controls(client:&mut Client)->Result<(),RevisionError>{sql::admit_controls(client)}
pub(super) fn decode_observation(row:&Row)->Result<StoredJobObservation,RevisionError>{sql::decode(row)}
#[cfg(test)]mod tests;

/// Authenticated server-owned claim inputs, not an executable request deserialized from a client.
#[derive(Clone)]
pub struct StoredJobClaimInput {
    pub project:ProjectId,pub branch:BranchId,pub expected_head:RevisionHead,
    pub key:Uuid,pub job:Uuid,pub request:Uuid,pub source:ArtifactId,
    pub request_sha:ContentDigest,pub manifest_sha:ContentDigest,pub source_sha:ContentDigest,
    pub effect_sha:ContentDigest,pub precommit_sha:ContentDigest,pub plan_sha:ContentDigest,
    pub target_profile:String,pub capability_sha:ContentDigest,
    pub max_attempts:i32,pub base_delay_seconds:i32,pub max_delay_seconds:i32,pub ttl_seconds:i32,
}
impl fmt::Debug for StoredJobClaimInput {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("StoredJobClaimInput(<redacted>)")}}

#[derive(Clone)]
pub struct StoredJobClaim(StoredJobClaimInput);
impl StoredJobClaim {
    /// # Errors
    /// Rejects invalid bounded SQL23 inputs. Does not attest source/head, worker or output.
    pub fn new(input:StoredJobClaimInput)->Result<Self,RevisionError>{
        let p=input.target_profile.as_bytes();
        if [input.key,input.job,input.request].iter().any(Uuid::is_nil)
            ||input.expected_head.revision_id().is_none()||input.expected_head.generation()==0
            ||i64::try_from(input.expected_head.generation()).is_err()
            ||!(1..=10).contains(&input.max_attempts)||!(1..=86400).contains(&input.base_delay_seconds)
            ||!(input.base_delay_seconds..=86400).contains(&input.max_delay_seconds)
            ||!(60..=604800).contains(&input.ttl_seconds)||!(2..=127).contains(&p.len())
            ||!p[0].is_ascii_alphanumeric()||!p[1..].iter().all(|v|v.is_ascii_alphanumeric()||matches!(v,b'.'|b'_'|b'-'))
            ||[input.request_sha,input.manifest_sha,input.source_sha,input.effect_sha,input.precommit_sha,input.plan_sha,input.capability_sha]
                .iter().any(|d|d.as_bytes()==&[0;32])||input.source_sha==input.effect_sha {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self(input))
    }
    #[must_use]pub const fn input(&self)->&StoredJobClaimInput{&self.0}
}
impl fmt::Debug for StoredJobClaim{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("StoredJobClaim(<redacted>)")}}

#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub enum StoredJobState{Claimed,InProgress,RetryPending,OutcomeUnknown,TerminalSuccess,TerminalFailure}
#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub enum StoredJobOutcome{New,Replay,Leased,Staged,Executing,Validating,Committed,OutcomeUnknown}

/// Validated repository observation, not proof that a caller holds a live DB capability.
#[derive(Clone,Eq,PartialEq)]
pub struct StoredJobObservation{
    outcome:StoredJobOutcome,job:Uuid,state:StoredJobState,attempt:i32,fence:i64,
    retry_micros:Option<i64>,revision:Option<RevisionId>,error:Option<String>,receipt:Option<ArtifactId>,
}
impl StoredJobObservation{
    /// Trusted repository adapter constructor; DB state/authority must still be checked by SQL.
    /// # Errors
    /// Rejects unknown shapes, nil job, invalid attempt/fence, terminal or retry contradictions.
    #[allow(clippy::too_many_arguments)]
    pub fn observed(outcome:StoredJobOutcome,job:Uuid,state:StoredJobState,attempt:i32,fence:i64,
        retry_micros:Option<i64>,revision:Option<RevisionId>,error:Option<String>,receipt:Option<ArtifactId>)->Result<Self,RevisionError>{
        use StoredJobState as S;use StoredJobOutcome as O;
        let valid_error=error.as_ref().is_none_or(|v|{let b=v.as_bytes();(3..=64).contains(&b.len())&&b[0].is_ascii_uppercase()
            &&b[1..].iter().all(|v|v.is_ascii_uppercase()||v.is_ascii_digit()||*v==b'_')});
        let shape=match state{
            S::Claimed=>attempt==0&&retry_micros.is_none()&&revision.is_none()&&error.is_none()&&receipt.is_none(),
            S::InProgress=>attempt>0&&retry_micros.is_none()&&revision.is_none()&&error.is_none()&&receipt.is_none(),
            S::RetryPending=>attempt>0&&retry_micros.is_some_and(|v|v>0)&&revision.is_none()&&error.is_none()&&receipt.is_some(),
            S::OutcomeUnknown=>attempt>0&&retry_micros.is_none()&&revision.is_none()&&error.as_deref()==Some("OUTCOME_UNKNOWN")&&receipt.is_some(),
            S::TerminalSuccess=>attempt>0&&retry_micros.is_none()&&revision.is_some()&&error.is_none()&&receipt.is_some(),
            S::TerminalFailure=>attempt>0&&retry_micros.is_none()&&revision.is_none()&&error.is_some()&&receipt.is_some(),
        };
        let compatible=match outcome{O::Replay=>true,O::New=>state==S::Claimed,
            O::Leased|O::Staged|O::Executing|O::Validating=>state==S::InProgress,
            O::Committed=>state==S::TerminalSuccess,O::OutcomeUnknown=>state==S::OutcomeUnknown};
        if job.is_nil()||!(0..=10).contains(&attempt)||fence!=i64::from(attempt)||!valid_error||!shape||!compatible{
            return Err(RevisionError::RepositoryFailure);
        }
        Ok(Self{outcome,job,state,attempt,fence,retry_micros,revision,error,receipt})
    }
    #[must_use]pub const fn outcome(&self)->StoredJobOutcome{self.outcome}
    #[must_use]pub const fn job_id(&self)->Uuid{self.job}
    #[must_use]pub const fn state(&self)->StoredJobState{self.state}
    #[must_use]pub const fn attempt_no(&self)->i32{self.attempt}
    #[must_use]pub const fn fencing_token(&self)->i64{self.fence}
    #[must_use]pub const fn retry_not_before_micros(&self)->Option<i64>{self.retry_micros}
    #[must_use]pub const fn result_revision_id(&self)->Option<RevisionId>{self.revision}
    #[must_use]pub const fn receipt_artifact_id(&self)->Option<ArtifactId>{self.receipt}
    #[must_use]pub fn terminal_error_code(&self)->Option<&str>{self.error.as_deref()}
    pub(super) fn expect(&self,job:Uuid,outcome:StoredJobOutcome,attempt:Option<i32>)->Result<(),RevisionError>{
        if self.job!=job||self.outcome!=outcome||attempt.is_some_and(|a|a!=self.attempt){return Err(RevisionError::RepositoryFailure);}Ok(())
    }
}
impl fmt::Debug for StoredJobObservation{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.debug_struct("StoredJobObservation").field("outcome",&self.outcome).field("state",&self.state).finish_non_exhaustive()}}

#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub enum StoredJobAdvance{Staged,Executing,Validating}
impl StoredJobAdvance{
    fn states(self)->(&'static str,&'static str,StoredJobOutcome){match self{
        Self::Staged=>("leased","staged",StoredJobOutcome::Staged),Self::Executing=>("staged","executing",StoredJobOutcome::Executing),
        Self::Validating=>("executing","validating",StoredJobOutcome::Validating)}}
}

/// The same admitted repository owns the registration/CAS and all job transitions.
/// Callers must not replay any operation on error; commit acknowledgement loss is ambiguous.
pub trait StoredJobLifecycleRepository:StoredRevisionJobRepository{
    /// Same admitted backend/context with the received capability, never a new authority issuer.
    fn with_job_lease(&self,lease:StoredJobLease)->Self where Self:Sized;
    /// # Errors
    /// SQL checks exact request binding, current source for new jobs and source access on replay.
    fn claim_job(&self,context:&RevisionRequestContext,claim:&StoredJobClaim,event:ContentDigest)->Result<StoredJobObservation,RevisionError>;
    /// # Errors
    /// SQL verifies worker registration, state, attempt budget, time and current source/head.
    fn lease_job(&self,context:&RevisionRequestContext,claim:&StoredJobClaim,agent:Uuid,execution:Uuid,seconds:i32,event:ContentDigest)->Result<StoredJobLease,RevisionError>;
    /// # Errors
    /// Requires a live matching fenced lease and the exact preceding job state.
    fn advance_job(&self,context:&RevisionRequestContext,project:ProjectId,lease:StoredJobLease,stage:StoredJobAdvance,event:ContentDigest)->Result<StoredJobObservation,RevisionError>;
    /// # Errors
    /// Requires actual sealed committed effect and exact precommit receipt, not an intent receipt.
    fn complete_job(&self,context:&RevisionRequestContext,project:ProjectId,lease:StoredJobLease,revision:RevisionId,precommit:ArtifactId,event:ContentDigest)->Result<StoredJobObservation,RevisionError>;
    /// # Errors
    /// Requires a retained verified receipt; consumes authority without allowing an execution retry.
    fn mark_job_unknown(&self,context:&RevisionRequestContext,project:ProjectId,lease:StoredJobLease,receipt:ArtifactId,event:ContentDigest)->Result<StoredJobObservation,RevisionError>;
    /// # Errors
    /// Resolves unknown to committed only if the DB's full committed-effect oracle verifies it.
    fn reconcile_job_committed(&self,context:&RevisionRequestContext,lookup:StoredCommitIntentLookup,revision:RevisionId,precommit:ArtifactId,event:ContentDigest)->Result<StoredJobObservation,RevisionError>;
}
