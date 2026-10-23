use super::*;
mod guard{include!("stored_job_commit_guard.rs");}
mod archived_default{include!("stored_job_archived_default.rs");}
use hwpx_agent_cli::stored_revision_commit::job::*;
use revision_service::postgres::{RevisionLeaseIdentity,source_formula_policy::issuer_registry::stored_revision_jobs::*};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::lifecycle::*;
use std::sync::{Mutex,atomic::AtomicUsize};
// Trusted repository model, synthetic manifest/validator/scanner; NOT real SQL/worker/Native authority.
struct Shared{events:Mutex<Vec<&'static str>>,registered:AtomicUsize}
#[derive(Clone)]struct LifecycleJobs{inner:FaultRevision,context:RevisionRequestContext,shared:Arc<Shared>,mode:u8,lease:Option<StoredJobLease>}
impl LifecycleJobs{
    fn service(f:&StoredFixture,mode:u8)->RevisionService<Self>{RevisionService::new(Self{inner:FaultRevision::service(f,if mode==5{3}else{0}).repository().clone(),
        context:f.revision_context.clone(),shared:Arc::new(Shared{events:Mutex::default(),registered:AtomicUsize::new(0)}),mode,lease:None})}
    fn event(&self,e:&'static str)->Result<(),RevisionError>{self.shared.events.lock().map_err(|_|RevisionError::RepositoryFailure)?.push(e);Ok(())}
    fn events(&self)->Result<Vec<&'static str>,RevisionError>{Ok(self.shared.events.lock().map_err(|_|RevisionError::RepositoryFailure)?.clone())}
}
fn observation(outcome:StoredJobOutcome,job:Uuid,attempt:i32,revision:Option<RevisionId>,receipt:Option<artifact_service::ArtifactId>)->Result<StoredJobObservation,RevisionError>{
    let state=match outcome{StoredJobOutcome::New=>StoredJobState::Claimed,StoredJobOutcome::Replay=>StoredJobState::InProgress,
        StoredJobOutcome::Committed=>StoredJobState::TerminalSuccess,StoredJobOutcome::OutcomeUnknown=>StoredJobState::OutcomeUnknown,_=>StoredJobState::InProgress};
    StoredJobObservation::observed(outcome,job,state,attempt,i64::from(attempt),None,revision,
        (outcome==StoredJobOutcome::OutcomeUnknown).then(||"OUTCOME_UNKNOWN".into()),receipt)
}
impl RevisionRepository for LifecycleJobs{
    fn authorize_context(&self,c:&RevisionRequestContext)->Result<(),RevisionError>{if c.tenant_id()!=self.context.tenant_id()||c.subject()!=self.context.subject(){Err(RevisionError::NotFound)}else{Ok(())}}
    fn compare_and_swap(&self,c:&RevisionRequestContext,r:&RevisionCommitRequest)->Result<CommitOutcome,RevisionError>{
        self.authorize_context(c)?;if self.lease.is_none()||self.shared.registered.load(Ordering::SeqCst)!=1{return Err(RevisionError::InvalidRequest);}
        self.event("cas")?;self.inner.compare_and_swap(c,r)
    }
    fn head(&self,t:TenantId,p:revision_service::ProjectId,b:BranchId)->Result<RevisionHead,RevisionError>{self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:revision_service::ProjectId,r:RevisionId)->Result<RevisionNode,RevisionError>{self.inner.node(t,p,r)}
}
impl StoredRevisionJobRepository for LifecycleJobs{
    fn register_commit_intent(&self,c:&RevisionRequestContext,r:&StoredCommitRegistration)->Result<StoredCommitIntentRecord,RevisionError>{
        self.authorize_context(c)?;if self.lease!=Some(r.lease()){return Err(RevisionError::InvalidRequest);}
        self.event("register")?;self.shared.registered.fetch_add(1,Ordering::SeqCst);StoredCommitIntentRecord::expected(c,r)
    }
    fn read_commit_intent(&self,_:&RevisionRequestContext,_:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,RevisionError>{Err(RevisionError::InvalidRequest)}
}
impl StoredJobLifecycleRepository for LifecycleJobs{
    fn with_job_lease(&self,lease:StoredJobLease)->Self{let mut r=self.clone();r.lease=Some(lease);r}
    fn claim_job(&self,c:&RevisionRequestContext,r:&StoredJobClaim,_:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        self.authorize_context(c)?;self.event("claim")?;if self.mode==2{return Err(RevisionError::CommitOutcomeUnknown);}
        if self.mode==1{return observation(StoredJobOutcome::Replay,r.input().job,1,None,None);}
        observation(StoredJobOutcome::New,if self.mode==8{Uuid::new_v4()}else{r.input().job},0,None,None)
    }
    fn lease_job(&self,c:&RevisionRequestContext,r:&StoredJobClaim,agent:Uuid,execution:Uuid,_:i32,_:ContentDigest)->Result<StoredJobLease,RevisionError>{
        self.authorize_context(c)?;self.event("lease")?;StoredJobLease::new(RevisionLeaseIdentity{idempotency_key:r.input().key,job_id:r.input().job,
            agent_instance_id:if self.mode==3{Uuid::new_v4()}else{agent},execution_id:execution,attempt_no:1,fencing_token:1,authorization_id:Uuid::new_v4()})
    }
    fn advance_job(&self,c:&RevisionRequestContext,_:revision_service::ProjectId,l:StoredJobLease,s:StoredJobAdvance,_:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        self.authorize_context(c)?;let(event,outcome)=match s{StoredJobAdvance::Staged=>("staged",StoredJobOutcome::Staged),StoredJobAdvance::Executing=>("executing",StoredJobOutcome::Executing),StoredJobAdvance::Validating=>("validating",StoredJobOutcome::Validating)};
        self.event(event)?;if self.mode==4&&s==StoredJobAdvance::Validating{return Err(RevisionError::CommitOutcomeUnknown);}
        observation(outcome,l.identity().job_id,l.identity().attempt_no,None,None)
    }
    fn complete_job(&self,c:&RevisionRequestContext,_:revision_service::ProjectId,l:StoredJobLease,r:RevisionId,p:artifact_service::ArtifactId,_:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        self.authorize_context(c)?;self.event("complete")?;if self.mode==6{return Err(RevisionError::CommitOutcomeUnknown);}
        observation(StoredJobOutcome::Committed,l.identity().job_id,l.identity().attempt_no,Some(if self.mode==7{RevisionId::generate()}else{r}),Some(p))
    }
    fn mark_job_unknown(&self,c:&RevisionRequestContext,_:revision_service::ProjectId,l:StoredJobLease,p:artifact_service::ArtifactId,_:ContentDigest)->Result<StoredJobObservation,RevisionError>{
        self.authorize_context(c)?;self.event("unknown")?;observation(StoredJobOutcome::OutcomeUnknown,l.identity().job_id,l.identity().attempt_no,None,Some(p))
    }
    fn reconcile_job_committed(&self,_:&RevisionRequestContext,_:StoredCommitIntentLookup,_:RevisionId,_:artifact_service::ArtifactId,_:ContentDigest)->Result<StoredJobObservation,RevisionError>{Err(RevisionError::InvalidRequest)}
}
fn options()->StoredJobOptions{StoredJobOptions{key:Uuid::from_u128(9101),job:Uuid::from_u128(9102),request:Uuid::from_u128(9103),request_sha:ContentDigest::of(b"server canonical request"),
    capability_sha:ContentDigest::of(b"server retained worker capability snapshot"),max_attempts:3,base_delay_seconds:1,max_delay_seconds:60,ttl_seconds:600}}
fn run(f:&StoredFixture,m:&ExecutionManifest,revisions:&RevisionService<LifecycleJobs>,context:&RequestContext,workspace:&std::path::Path,source:&[u8],valid:bool)->Result<StoredJobRunReport,Box<dyn Error>>{
    Ok(PreparedStoredJob::prepare(binding(f,m,OUTPUT),options(),Default::default())?.run_once(&f.artifacts,revisions,context,&f.revision_context,Uuid::from_u128(9201),Uuid::from_u128(9202),30,
        ContentDigest::of(b"server transition event"),workspace,source,&mut |_:&[u8]|if valid{ValidationOutcome::Valid}else{ValidationOutcome::Rejected},||10))
}
#[test]fn expected_claim_is_derived_from_retained_manifest_and_candidate_without_execution()->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-plan")?;let p=PreparedStoredJob::prepare(binding(&f,&m,OUTPUT),options(),Default::default())?;
    let i=p.claim().input();assert_eq!(i.source,f.result);assert_eq!(i.expected_head,f.head);assert_eq!(i.project,f.project);assert_eq!(i.branch,f.branch);
    assert_eq!(i.manifest_sha.as_bytes(),&m.canonical_sha256()?);assert_eq!(i.source_sha,ContentDigest::of(SOURCE));assert_eq!(i.effect_sha,ContentDigest::of(OUTPUT));
    assert_eq!(i.precommit_sha.as_bytes(),&m.prepare_precommit(OUTPUT,Default::default())?.expected_precommit_sha256()?);assert_eq!(i.plan_sha.as_bytes(),&m.compiled_plan_sha256());
    assert_eq!(i.target_profile,m.target_profile_id().as_str());assert_eq!(format!("{p:?}"),"PreparedStoredJob(<redacted>)");Ok(())
}
#[test]fn actual_pipeline_claims_leases_validates_registers_commits_and_completes_in_order()->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-success")?;let revisions=LifecycleJobs::service(&f,0);let c=writer(&f);let root=tempfile::tempdir()?;
    let r=run(&f,&m,&revisions,&c,&root.path().join("workspace"),SOURCE,true)?;
    assert_eq!(r.stage,StoredJobRunStage::Completed);assert!(r.transaction.as_ref().ok_or("tx")?.is_ok());assert!(r.completion.is_some());assert!(r.repository_error.is_none());
    assert_eq!(revisions.repository().events()?,["claim","lease","staged","executing","validating","register","cas","complete"]);
    let req=r.request.as_ref().ok_or("request")?;let precommit=r.precommit.as_ref().ok_or("precommit")?;let intent=r.intent.as_ref().ok_or("intent")?;
    assert_eq!(req.transaction_receipt_sha256(),precommit.sha256);assert_ne!(precommit.sha256,intent.sha256);
    assert_eq!(r.completion.as_ref().ok_or("completion")?.receipt_artifact_id(),Some(precommit.artifact_id));
    assert_eq!(f.artifacts.download(&c,r.result.as_ref().ok_or("result")?.artifact_id,11)?,OUTPUT);
    assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),1);assert_eq!(f.artifacts.download(&f.reader,f.result,11)?,SOURCE);Ok(())
}
#[test]fn replay_and_unknown_claim_never_lease_or_create_workspace()->TestResult{
    for mode in[1,2,8]{let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-no-replay")?;let revisions=LifecycleJobs::service(&f,mode);let root=tempfile::tempdir()?;let path=root.path().join("workspace");
        let r=run(&f,&m,&revisions,&writer(&f),&path,SOURCE,true)?;assert!(!path.exists());assert!(r.transaction.is_none());assert!(r.lease.is_none());assert_eq!(revisions.repository().events()?,["claim"]);
        if mode==1{assert_eq!(r.stage,StoredJobRunStage::Replay);}else{assert!(r.repository_error.is_some());}}
    Ok(())
}
#[test]fn wrong_lease_stops_before_workspace_and_any_product_callbacks()->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-foreign-lease")?;let revisions=LifecycleJobs::service(&f,3);let root=tempfile::tempdir()?;let path=root.path().join("workspace");
    let r=run(&f,&m,&revisions,&writer(&f),&path,SOURCE,true)?;assert!(!path.exists());assert!(r.transaction.is_none());assert_eq!(r.repository_error,Some(RevisionError::RepositoryFailure));
    assert_eq!(revisions.repository().events()?,["claim","lease"]);Ok(())
}
#[test]fn validating_ack_loss_preserves_unknown_engine_result_without_ingest_or_cas()->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-stage-unknown")?;let revisions=LifecycleJobs::service(&f,4);let root=tempfile::tempdir()?;
    let r=run(&f,&m,&revisions,&writer(&f),&root.path().join("workspace"),SOURCE,true)?;assert_eq!(r.repository_error,Some(RevisionError::CommitOutcomeUnknown));
    assert_eq!(r.transaction.as_ref().ok_or("tx")?.as_ref().expect_err("unknown barrier").primary(),TransactionError::RevisionOutcomeUnknown);
    assert!(r.result.is_none());assert!(r.request.is_none());assert!(r.completion.is_none());assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),0);Ok(())
}
#[test]fn cas_ack_loss_retains_original_receipts_and_marks_unknown_without_completing_or_reexecuting()->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-cas-unknown")?;let revisions=LifecycleJobs::service(&f,5);let c=writer(&f);let root=tempfile::tempdir()?;
    let r=run(&f,&m,&revisions,&c,&root.path().join("workspace"),SOURCE,true)?;assert_eq!(r.stage,StoredJobRunStage::UnknownObservation);assert_eq!(r.cas_error,Some(StoredCommitError::Unknown));
    assert!(r.transaction.as_ref().ok_or("tx")?.is_err());assert!(r.unknown.is_some());assert!(r.registered_intent.is_some());assert!(r.completion.is_none());
    assert_eq!(revisions.repository().events()?,["claim","lease","staged","executing","validating","register","cas","unknown"]);
    assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),1);assert_eq!(f.artifacts.download(&c,r.result.as_ref().ok_or("result")?.artifact_id,11)?,OUTPUT);Ok(())
}
#[test]fn completion_ack_loss_or_foreign_success_does_not_trigger_another_mutation()->TestResult{
    for mode in[6,7]{let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-complete-uncertain")?;let revisions=LifecycleJobs::service(&f,mode);let root=tempfile::tempdir()?;
        let r=run(&f,&m,&revisions,&writer(&f),&root.path().join("workspace"),SOURCE,true)?;assert_eq!(r.stage,StoredJobRunStage::Completion);
        assert!(r.transaction.as_ref().ok_or("tx")?.is_ok());assert!(r.revision_receipt.is_some());assert!(r.completion.is_none());assert!(r.unknown.is_none());assert!(r.repository_error.is_some());
        assert_eq!(revisions.repository().events()?,["claim","lease","staged","executing","validating","register","cas","complete"]);assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),1);}
    Ok(())
}
#[test]fn validator_rejection_or_source_drift_never_enters_validating_or_storage_cas()->TestResult{
    for(source,valid)in[(SOURCE,false),(&b"changed live source"[..],true)]{let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-source-validator")?;let revisions=LifecycleJobs::service(&f,0);let root=tempfile::tempdir()?;
        let r=run(&f,&m,&revisions,&writer(&f),&root.path().join("workspace"),source,valid)?;assert!(r.transaction.as_ref().ok_or("tx")?.is_err());
        assert!(r.result.is_none());assert!(r.precommit.is_none());assert!(r.completion.is_none());assert_eq!(revisions.repository().events()?,["claim","lease","staged","executing"]);}
    Ok(())
}
#[test]fn original_scope_validation_precedes_claim_and_every_side_effect()->TestResult{
    let f=fixture()?;let m=manifest_fixture::manifest(&f,"job-scope")?;let revisions=LifecycleJobs::service(&f,0);let root=tempfile::tempdir()?;let path=root.path().join("workspace");
    let r=run(&f,&m,&revisions,&f.reader,&path,SOURCE,true)?;assert_eq!(r.stage,StoredJobRunStage::Binding);assert_eq!(r.binding_error,Some(StoredCommitError::Scope));
    assert!(revisions.repository().events()?.is_empty());assert!(!path.exists());Ok(())
}
