//! One-shot server coordinator, NOT a P09 route, target or Native execution authorization.
//! Requires retained deterministic candidate bytes and an independently qualified validator.
//! Existing jobs are observations only. No automatic replay, retry, rollback or artifact deletion.
use super::*;
pub mod identity;
use operation_engine::{PreparedPrecommitIdentity,TransactionLimits,TransactionReceipt,TransactionFailure,TransactionError,WorkspaceTransaction,OutputValidator,FaultPlan};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::lifecycle::*;
use uuid::Uuid;

/// Worker and request identities retained by the authenticated server. Not deserializable.
pub struct StoredJobOptions{
    pub key:Uuid,pub job:Uuid,pub request:Uuid,pub request_sha:ContentDigest,pub capability_sha:ContentDigest,
    pub max_attempts:i32,pub base_delay_seconds:i32,pub max_delay_seconds:i32,pub ttl_seconds:i32,
}
impl fmt::Debug for StoredJobOptions{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("StoredJobOptions(<redacted>)")}}

#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub enum StoredJobRunStage{Binding,Claim,Replay,Lease,Workspace,Staged,Executing,Validating,Transaction,Completion,UnknownObservation,Completed}

/// Original receipts and failures survive even when completion/registration acknowledgement is lost.
/// Completed here concerns this storage primitive only, never a product/phase acceptance.
pub struct StoredJobRunReport{
    pub stage:StoredJobRunStage,pub claim:Option<StoredJobObservation>,pub lease:Option<StoredJobLease>,
    pub repository_error:Option<RevisionError>,pub binding_error:Option<StoredCommitError>,pub workspace_error:Option<TransactionError>,
    pub transaction:Option<Result<TransactionReceipt,TransactionFailure>>,pub cas_error:Option<StoredCommitError>,
    pub result:Option<ArtifactDescriptor>,pub intent:Option<ArtifactDescriptor>,pub precommit:Option<ArtifactDescriptor>,
    pub request:Option<ServiceRequest>,pub revision_receipt:Option<RevisionReceipt>,pub registered_intent:Option<StoredCommitIntentRecord>,
    pub registration_response:Option<StoredCommitIntentRecord>,pub completion:Option<StoredJobObservation>,pub unknown:Option<StoredJobObservation>,
}
impl StoredJobRunReport{
    fn empty()->Self{Self{stage:StoredJobRunStage::Binding,claim:None,lease:None,repository_error:None,binding_error:None,workspace_error:None,
        transaction:None,cas_error:None,result:None,intent:None,precommit:None,request:None,revision_receipt:None,registered_intent:None,
        registration_response:None,completion:None,unknown:None}}
}
impl fmt::Debug for StoredJobRunReport{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.debug_struct("StoredJobRunReport").field("stage",&self.stage)
    .field("transaction_observed",&self.transaction.is_some()).field("revision_receipt_observed",&self.revision_receipt.is_some()).finish_non_exhaustive()}}

/// Consumed by run_once. Reconstructing with the same key does NOT re-authorize the same job.
pub struct PreparedStoredJob<'a>{binding:StoredCommitBinding<'a>,claim:StoredJobClaim,expected:PreparedPrecommitIdentity,limits:TransactionLimits,
    precommit_guard:Option<Box<dyn StoredPrecommitGuard+'a>>,manifest_archive:operation_engine::ArchivedExecutionManifest}
impl fmt::Debug for PreparedStoredJob<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PreparedStoredJob(<redacted>)")}}
fn digest(bytes:[u8;32])->Result<ContentDigest,StoredCommitError>{ContentDigest::parse(&hex::encode(bytes)).map_err(|_|StoredCommitError::Binding)}
impl<'a> PreparedStoredJob<'a>{
    /// Prepares a reservation expectation, not an actual engine/CAS request or validation success.
    /// # Errors
    /// Applies original engine limits and exact manifest/source/head/target identity; no side effects.
    pub fn prepare(binding:StoredCommitBinding<'a>,options:StoredJobOptions,limits:TransactionLimits)->Result<Self,StoredCommitError>{
        if binding.expected_head.revision_id().is_none_or(|r|r.public_id()!=binding.manifest.base_revision().as_str())
            ||binding.output.len()as u64>MAX_BYTES||binding.manifest.expected_source_size()>MAX_BYTES{
            return Err(StoredCommitError::Binding);
        }
        let manifest_archive=operation_engine::ArchivedExecutionManifest::capture(binding.manifest).map_err(|_|StoredCommitError::Binding)?;
        let expected=binding.manifest.prepare_precommit(binding.output,limits).map_err(|_|StoredCommitError::Binding)?;
        let claim=StoredJobClaim::new(StoredJobClaimInput{project:binding.project,branch:binding.branch,expected_head:binding.expected_head,
            key:options.key,job:options.job,request:options.request,source:artifact_service::ArtifactId::parse(binding.manifest.source_artifact_id().as_str()).map_err(|_|StoredCommitError::Binding)?,
            request_sha:options.request_sha,manifest_sha:digest(binding.manifest.canonical_sha256().map_err(|_|StoredCommitError::Binding)?)?,
            source_sha:digest(binding.manifest.expected_source_sha256())?,effect_sha:digest(expected.expected_result_sha256())?,
            precommit_sha:digest(expected.expected_precommit_sha256().map_err(|_|StoredCommitError::Binding)?)?,plan_sha:digest(binding.manifest.compiled_plan_sha256())?,
            target_profile:binding.manifest.target_profile_id().as_str().into(),capability_sha:options.capability_sha,max_attempts:options.max_attempts,
            base_delay_seconds:options.base_delay_seconds,max_delay_seconds:options.max_delay_seconds,ttl_seconds:options.ttl_seconds}).map_err(|_|StoredCommitError::Binding)?;
        Ok(Self{binding,claim,expected,limits,precommit_guard:None,manifest_archive})
    }
    /// # Errors
    /// Adds a server current-state restriction before claim, pre-ingest and final revision commit.
    /// It never issues a job/route permit or changes replay/unknown-outcome handling.
    pub fn require_precommit_guard(&mut self,guard:Box<dyn StoredPrecommitGuard+'a>)->Result<(),StoredCommitError>{
        if self.precommit_guard.is_some(){return Err(StoredCommitError::CurrentGuard);}
        self.precommit_guard=Some(guard);Ok(())
    }
    #[must_use]pub const fn claim(&self)->&StoredJobClaim{&self.claim}
    fn binding_copy(&self)->StoredCommitBinding<'a>{StoredCommitBinding{manifest:self.binding.manifest,output:self.binding.output,project:self.binding.project,
        branch:self.binding.branch,expected_head:self.binding.expected_head,commit:self.binding.commit,new_revision:self.binding.new_revision,validation_summary:self.binding.validation_summary}}

    /// Executes the existing bytes/validator/storage/CAS pipeline once, with explicit SQL barriers.
    /// This trusted server primitive does not qualify or open any denied product route.
    #[allow(clippy::too_many_arguments)]
    pub fn run_once<R,B,S,V,F,Q>(mut self,artifacts:&ArtifactService<R,B,S>,revisions:&RevisionService<V>,context:&RequestContext,
        rc:&RevisionRequestContext,agent:Uuid,execution:Uuid,lease_seconds:i32,event:ContentDigest,
        workspace:&std::path::Path,source:&[u8],validator:&mut Q,mut clock:F)->StoredJobRunReport
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:StoredJobLifecycleRepository,F:FnMut()->u64,Q:OutputValidator{
        let mut report=StoredJobRunReport::empty();
        // Validate the original storage binding/scopes before the first DB mutation.
        if let Err(e)=StoredResultRevisionCas::bind(artifacts,revisions,context,rc,self.binding_copy(),&mut clock){report.binding_error=Some(e);return report;}
        if agent.is_nil()||execution.is_nil()||!(1..=3600).contains(&lease_seconds)||event.as_bytes()==&[0;32]{report.binding_error=Some(StoredCommitError::Binding);return report;}
        if let Some(guard)=self.precommit_guard.as_mut(){
            if let Err(error)=guard.check(){report.binding_error=Some(error);return report;}
        }
        report.stage=StoredJobRunStage::Claim;
        let claim=match revisions.repository().claim_job(rc,&self.claim,event){Ok(r)=>r,Err(e)=>{report.repository_error=Some(e);return report;}};
        let fresh=claim.outcome()==StoredJobOutcome::New&&claim.state()==StoredJobState::Claimed&&claim.attempt_no()==0;
        let valid=claim.job_id()==self.claim.input().job&&claim.attempt_no()<=self.claim.input().max_attempts
            &&(fresh||claim.outcome()==StoredJobOutcome::Replay);
        report.claim=Some(claim);
        if !valid{report.repository_error=Some(RevisionError::RepositoryFailure);return report;}
        if !fresh{report.stage=StoredJobRunStage::Replay;return report;}
        report.stage=StoredJobRunStage::Lease;
        let lease=match revisions.repository().lease_job(rc,&self.claim,agent,execution,lease_seconds,event){Ok(r)=>r,Err(e)=>{report.repository_error=Some(e);return report;}};
        report.lease=Some(lease);let id=lease.identity();
        if id.job_id!=self.claim.input().job||id.idempotency_key!=self.claim.input().key||id.agent_instance_id!=agent||id.execution_id!=execution||id.attempt_no!=1{
            report.repository_error=Some(RevisionError::RepositoryFailure);return report;
        }
        let leased=RevisionService::new(revisions.repository().with_job_lease(lease));
        report.stage=StoredJobRunStage::Workspace;
        let mut tx=match WorkspaceTransaction::create(workspace,self.binding.manifest.clone(),self.limits){Ok(t)=>t,Err(e)=>{report.workspace_error=Some(e);return report;}};
        for(stage,label,outcome)in[(StoredJobAdvance::Staged,StoredJobRunStage::Staged,StoredJobOutcome::Staged),
            (StoredJobAdvance::Executing,StoredJobRunStage::Executing,StoredJobOutcome::Executing)]{
            report.stage=label;
            match leased.repository().advance_job(rc,self.binding.project,lease,stage,event){
                Ok(r)if response(&r,lease,outcome)=>{},Ok(_)=>{report.repository_error=Some(RevisionError::RepositoryFailure);return report;},
                Err(e)=>{report.repository_error=Some(e);return report;}
            }
        }
        let mut cas=match StoredResultRevisionCas::bind_registered_with_archive(artifacts,&leased,context,rc,self.binding_copy(),self.manifest_archive,lease,&mut clock){
            Ok(c)=>c,Err(e)=>{report.binding_error=Some(e);return report;}};
        if let Some(guard)=self.precommit_guard.take(){
            if let Err(error)=cas.require_precommit_guard(guard){report.binding_error=Some(error);return report;}
        }
        let mut barrier_error=None;
        let mut callback=|request:&RevisionCommitRequest|{
            if !self.expected.matches_executed(request){barrier_error=Some(RevisionError::InvalidRequest);return RevisionCasOutcome::Failed;}
            match leased.repository().advance_job(rc,self.binding.project,lease,StoredJobAdvance::Validating,event){
                Ok(r)if response(&r,lease,StoredJobOutcome::Validating)=>cas.compare_and_swap(request),
                Ok(_)=>{barrier_error=Some(RevisionError::RepositoryFailure);RevisionCasOutcome::Failed},
                Err(e)=>{let ambiguous=e==RevisionError::CommitOutcomeUnknown;barrier_error=Some(e);
                    if ambiguous{RevisionCasOutcome::Unknown}else{RevisionCasOutcome::Failed}}
            }
        };
        report.stage=StoredJobRunStage::Transaction;
        let result=tx.execute_bytes(source,self.binding.output,validator,&mut callback,&mut FaultPlan::none());
        report.repository_error=barrier_error;report.cas_error=cas.error();report.result=cas.retained_result().cloned();report.intent=cas.retained_intent().cloned();
        report.precommit=cas.retained_precommit().cloned();report.request=cas.service_request().cloned();report.revision_receipt=cas.service_receipt().cloned();
        report.registered_intent=cas.registered_job_intent().cloned();report.registration_response=cas.registration_response().cloned();
        let engine_ok=result.is_ok();report.transaction=Some(result);
        if engine_ok{
            report.stage=StoredJobRunStage::Completion;
            let Some(precommit)=report.precommit.as_ref()else{report.binding_error=Some(StoredCommitError::Binding);return report;};
            match leased.repository().complete_job(rc,self.binding.project,lease,self.binding.new_revision,precommit.artifact_id,event){
                Ok(r)if response(&r,lease,StoredJobOutcome::Committed)&&r.result_revision_id()==Some(self.binding.new_revision)
                    &&r.receipt_artifact_id()==Some(precommit.artifact_id)=>{report.completion=Some(r);report.stage=StoredJobRunStage::Completed;},
                Ok(_)=>report.repository_error=Some(RevisionError::RepositoryFailure),Err(e)=>report.repository_error=Some(e),
            }
            // An uncertain completion is NOT followed by a second mutation or execution.
        }else if report.cas_error==Some(StoredCommitError::Unknown)||report.revision_receipt.is_some(){
            if let Some(precommit)=report.precommit.as_ref(){
                report.stage=StoredJobRunStage::UnknownObservation;
                match leased.repository().mark_job_unknown(rc,self.binding.project,lease,precommit.artifact_id,event){
                    Ok(r)if response(&r,lease,StoredJobOutcome::OutcomeUnknown)&&r.receipt_artifact_id()==Some(precommit.artifact_id)=>report.unknown=Some(r),
                    Ok(_)=>report.repository_error=Some(RevisionError::RepositoryFailure),Err(e)=>report.repository_error=Some(e),
                }
            }
        }
        report
    }
}
fn response(row:&StoredJobObservation,lease:StoredJobLease,outcome:StoredJobOutcome)->bool{
    let id=lease.identity();row.job_id()==id.job_id&&row.outcome()==outcome&&row.attempt_no()==id.attempt_no&&row.fencing_token()==id.fencing_token
}
