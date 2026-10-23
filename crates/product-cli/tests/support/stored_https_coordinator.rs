//! Real original coordinator/crypto/CAS; synthetic lifecycle repository and routes, not SQL or worker authority.
use super::*;
use super::requests::{raw,budget,allowed};
use super::storage::routing;
use revision_service as rev;
use rev::postgres::{RevisionLeaseIdentity,source_formula_policy::issuer_registry::stored_revision_jobs::*};
use rev::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::lifecycle::*;
use hwpx_agent_cli::{form_product_request::stored_operations::{StoredProductRequest as Entry,https_targets::{
    routing::PreparedHttpsTargetExecutionManifest as Manifest,admission::RegistryBoundHttpsTargetError}},
    stored_revision_commit::{StoredCommitError,job::{StoredJobRunReport,StoredJobRunStage,identity::StoredJobPolicy}}};
use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::p02_registry::{PinnedP02RegistryEvidence,PinnedP02RegistryBytes,PinnedRegistryError};
use domain_ir::TransactionId;
#[path="pinned_p02_registry_fixture.rs"]mod pinned;
struct Shared{events:Mutex<Vec<&'static str>>,registered:AtomicUsize,revoked:AtomicBool}
#[derive(Clone)]struct Jobs{inner:rev::InMemoryRevisionRepository,context:rev::RevisionRequestContext,shared:Arc<Shared>,mode:u8,lease:Option<StoredJobLease>}
impl Jobs{
    fn service(f:&StoredFixture,mode:u8)->rev::RevisionService<Self>{rev::RevisionService::new(Self{inner:f.revisions.repository().clone(),context:f.revision_context.clone(),
        shared:Arc::new(Shared{events:Mutex::new(vec![]),registered:AtomicUsize::new(0),revoked:AtomicBool::new(false)}),mode,lease:None})}
    fn event(&self,event:&'static str)->Result<(),rev::RevisionError>{self.shared.events.lock().map_err(|_|rev::RevisionError::RepositoryFailure)?.push(event);Ok(())}
    fn events(&self)->Result<Vec<&'static str>,rev::RevisionError>{Ok(self.shared.events.lock().map_err(|_|rev::RevisionError::RepositoryFailure)?.clone())}
}
fn observed(outcome:StoredJobOutcome,job:Uuid,attempt:i32,revision:Option<rev::RevisionId>,receipt:Option<artifact_service::ArtifactId>)->Result<StoredJobObservation,rev::RevisionError>{
    let state=match outcome{StoredJobOutcome::New=>StoredJobState::Claimed,StoredJobOutcome::Committed=>StoredJobState::TerminalSuccess,
        StoredJobOutcome::OutcomeUnknown=>StoredJobState::OutcomeUnknown,_=>StoredJobState::InProgress};
    StoredJobObservation::observed(outcome,job,state,attempt,i64::from(attempt),None,revision,(outcome==StoredJobOutcome::OutcomeUnknown).then(||"OUTCOME_UNKNOWN".into()),receipt)
}
impl rev::RevisionRepository for Jobs{
    fn authorize_context(&self,c:&rev::RevisionRequestContext)->Result<(),rev::RevisionError>{if c.tenant_id()!=self.context.tenant_id()||c.subject()!=self.context.subject(){Err(rev::RevisionError::NotFound)}else{Ok(())}}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.inner.node(t,p,r)}
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{
        self.authorize_context(c)?;if self.lease.is_none()||self.shared.registered.load(Ordering::SeqCst)!=1{return Err(rev::RevisionError::InvalidRequest);}
        self.event("cas")?;self.inner.compare_and_swap(c,r)
    }
}
impl StoredRevisionJobRepository for Jobs{
    fn register_commit_intent(&self,c:&rev::RevisionRequestContext,r:&StoredCommitRegistration)->Result<StoredCommitIntentRecord,rev::RevisionError>{
        rev::RevisionRepository::authorize_context(self,c)?;if self.lease!=Some(r.lease()){return Err(rev::RevisionError::InvalidRequest);}self.event("register")?;
        if self.mode==7{return Err(rev::RevisionError::RepositoryFailure);}
        let record=StoredCommitIntentRecord::expected(c,r)?;self.shared.registered.fetch_add(1,Ordering::SeqCst);
        if self.mode==8{return Err(rev::RevisionError::CommitOutcomeUnknown);}Ok(record)
    }
    fn read_commit_intent(&self,_:&rev::RevisionRequestContext,_:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,rev::RevisionError>{Err(rev::RevisionError::InvalidRequest)}
}
impl StoredJobLifecycleRepository for Jobs{
    fn with_job_lease(&self,lease:StoredJobLease)->Self{let mut next=self.clone();next.lease=Some(lease);next}
    fn claim_job(&self,c:&rev::RevisionRequestContext,r:&StoredJobClaim,_:ContentDigest)->Result<StoredJobObservation,rev::RevisionError>{
        rev::RevisionRepository::authorize_context(self,c)?;self.event("claim")?;
        match self.mode{1=>observed(StoredJobOutcome::Replay,r.input().job,1,None,None),2=>Err(rev::RevisionError::CommitOutcomeUnknown),_=>observed(StoredJobOutcome::New,r.input().job,0,None,None)}
    }
    fn lease_job(&self,c:&rev::RevisionRequestContext,r:&StoredJobClaim,agent:Uuid,execution:Uuid,_:i32,_:ContentDigest)->Result<StoredJobLease,rev::RevisionError>{
        rev::RevisionRepository::authorize_context(self,c)?;self.event("lease")?;StoredJobLease::new(RevisionLeaseIdentity{idempotency_key:r.input().key,job_id:r.input().job,
            agent_instance_id:if self.mode==3{Uuid::from_u128(999)}else{agent},execution_id:execution,attempt_no:1,fencing_token:1,authorization_id:Uuid::from_u128(5363)})
    }
    fn advance_job(&self,c:&rev::RevisionRequestContext,_:rev::ProjectId,l:StoredJobLease,s:StoredJobAdvance,_:ContentDigest)->Result<StoredJobObservation,rev::RevisionError>{
        rev::RevisionRepository::authorize_context(self,c)?;let(event,outcome)=match s{StoredJobAdvance::Staged=>("staged",StoredJobOutcome::Staged),StoredJobAdvance::Executing=>("executing",StoredJobOutcome::Executing),
            StoredJobAdvance::Validating=>("validating",StoredJobOutcome::Validating)};self.event(event)?;
        if self.mode==4&&s==StoredJobAdvance::Validating{return Err(rev::RevisionError::CommitOutcomeUnknown);}
        if self.mode==5&&s==StoredJobAdvance::Executing{self.shared.revoked.store(true,Ordering::SeqCst);}
        observed(outcome,l.identity().job_id,l.identity().attempt_no,None,None)
    }
    fn complete_job(&self,c:&rev::RevisionRequestContext,_:rev::ProjectId,l:StoredJobLease,r:rev::RevisionId,p:artifact_service::ArtifactId,_:ContentDigest)->Result<StoredJobObservation,rev::RevisionError>{
        rev::RevisionRepository::authorize_context(self,c)?;self.event("complete")?;if self.mode==6{return Err(rev::RevisionError::CommitOutcomeUnknown);}
        observed(StoredJobOutcome::Committed,l.identity().job_id,l.identity().attempt_no,Some(r),Some(p))
    }
    fn mark_job_unknown(&self,c:&rev::RevisionRequestContext,_:rev::ProjectId,l:StoredJobLease,p:artifact_service::ArtifactId,_:ContentDigest)->Result<StoredJobObservation,rev::RevisionError>{
        rev::RevisionRepository::authorize_context(self,c)?;self.event("unknown")?;observed(StoredJobOutcome::OutcomeUnknown,l.identity().job_id,l.identity().attempt_no,None,Some(p))
    }
    fn reconcile_job_committed(&self,_:&rev::RevisionRequestContext,_:StoredCommitIntentLookup,_:rev::RevisionId,_:artifact_service::ArtifactId,_:ContentDigest)->Result<StoredJobObservation,rev::RevisionError>{Err(rev::RevisionError::InvalidRequest)}
}
struct CurrentPolicy<'a>{inner:&'a Repository,revoked:&'a AtomicBool}
impl HttpsTargetPolicyRepository for CurrentPolicy<'_>{
    fn read_current(&self,s:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,E>{
        if self.revoked.load(Ordering::SeqCst){return Err(E::Repository);}self.inner.read_current(s)
    }
}
fn execute(mode:u8,preclaim_revoke:bool)->Result<(StoredJobRunReport,Vec<&'static str>,rev::RevisionHead,rev::RevisionHead,Vec<u8>),Box<dyn Error>>{
    let bytes=fixture::captured()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let original=writable(&f,&actor)?;
    let source=original.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let revisions=Jobs::service(&f,mode);
    let p=StoredFormProvider::bind(&f.artifacts,&revisions,&actor,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
    let policy=CurrentPolicy{inner:&repository,revoked:&revisions.repository().shared.revoked};
    let product=Entry::prepare_https_targets_json(&p,&policy,&serde_json::to_vec(&raw(&f,&bytes)?)?,budget()?,10)?;
    let(c,r)=routing("ref.hyperlink_edit",11,0)?;let out:Manifest=product.prepare_execution_manifest(&p,&policy,&c,&r,TransactionId::parse("https-registered-job")?,11)?;
    assert!(out.require_current_product_route(&p,&policy,&c,&r,11).is_err());let root=tempfile::tempdir()?;let path=root.path().join("registered-job");
    let new_revision=rev::RevisionId::generate();
    let report=out.with_verified_guarded_job_preparation(&p,&policy,StoredJobPolicy::default(),rev::CommitId::generate(),new_revision,Default::default(),
        ||{let(c,r)=routing("ref.hyperlink_edit",12,0).map_err(|_|())?;Ok((c,r,12))},|mut job,source,mut validator|{
            // The automatically attached guard cannot be replaced by a caller's permissive closure.
            assert_eq!(job.require_precommit_guard(Box::new(||Ok(()))),Err(StoredCommitError::CurrentGuard));
            if preclaim_revoke{revisions.repository().shared.revoked.store(true,Ordering::SeqCst);}
            job.run_once(&f.artifacts,&revisions,&actor,&f.revision_context,Uuid::from_u128(5361),Uuid::from_u128(5362),30,
                ContentDigest::of(b"synthetic https job event"),&path,source,&mut validator,||12)
        })?;
    let after=revisions.head(&f.revision_context,f.project,f.branch)?;let events=revisions.repository().events()?;
    let saved=if let Some(result)=&report.result{f.artifacts.download(&actor,result.artifact_id,13)?}else{vec![]};
    assert_eq!(f.artifacts.download(&f.reader,f.result,13)?,bytes);
    if mode==0&&!preclaim_revoke{assert_eq!(after.revision_id(),Some(new_revision));}
    if matches!(mode,1|2|3)||preclaim_revoke{assert!(!path.exists());}
    Ok((report,events,f.head,after,saved))
}
#[test]
fn real_pinned_registry_denies_https_before_source_policy_or_claim_without_upgrading_signed_claims()->TestResult{
    let material=pinned::load()?;let registry=PinnedP02RegistryEvidence::verify_pinned_snapshot(material.input())?;
    assert!(registry.receipt().signature_verified);assert!(!registry.receipt().routing_enabled&&!registry.receipt().execution_authority);
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;
    let source=p.import_actual_forms(f.head,9)?;let repo=allowed(&f,&source)?;let raw=serde_json::to_vec(&raw(&f,&bytes)?)?;let before=f.metadata.audit_events()?.len();
    f.blobs.tamper.store(true,Ordering::SeqCst);
    assert!(matches!(Entry::prepare_https_targets_json_with_pinned_registry(&p,&repo,&raw,budget()?,&registry,10),Err(RegistryBoundHttpsTargetError::Registry(PinnedRegistryError::RoutingDisabled))));
    assert!(matches!(Entry::prepare_https_targets_json_with_pinned_registry(&p,&repo,b"{}",budget()?,&registry,10),Err(RegistryBoundHttpsTargetError::Product(_))));
    assert_eq!(repo.calls.load(Ordering::SeqCst),0);assert_eq!(f.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn original_coordinator_registers_archived_receipts_then_one_cas_and_completion_with_guard_attached()->TestResult{
    let(report,events,before,after,saved)=execute(0,false)?;
    assert_eq!(report.stage,StoredJobRunStage::Completed);assert!(report.transaction.as_ref().is_some_and(Result::is_ok));
    assert!(report.registered_intent.is_some()&&report.intent.is_some()&&report.precommit.is_some()&&report.revision_receipt.is_some());
    assert_eq!(report.completion.as_ref().ok_or("completion")?.outcome(),StoredJobOutcome::Committed);
    assert_eq!(events,vec!["claim","lease","staged","executing","validating","register","cas","complete"]);assert_ne!(before,after);
    assert_eq!(output_uris(&saved,"actual-form-document")?,vec![Some("https://example.org/public?x=1&y=2".into())]);Ok(())
}
#[test]
fn mandatory_guard_blocks_policy_revocation_before_first_claim_and_cannot_be_replaced()->TestResult{
    let(report,events,before,after,_)=execute(0,true)?;assert_eq!(report.binding_error,Some(StoredCommitError::CurrentGuard));
    assert!(report.claim.is_none()&&report.transaction.is_none());assert!(events.is_empty());assert_eq!(before,after);Ok(())
}
#[test]
fn unavailable_fresh_route_snapshot_stops_before_storage_or_job_callback()->TestResult{
    let bytes=fixture::package(&link(1,"https://example.org/old"))?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let actor=write_context(&f);let p=writable(&f,&actor)?;
    let source=p.import_actual_forms(f.head,9)?;let repo=allowed(&f,&source)?;
    let product=Entry::prepare_https_targets_json(&p,&repo,&serde_json::to_vec(&raw(&f,&bytes)?)?,budget()?,10)?;
    let(c,r)=routing("ref.hyperlink_edit",11,0)?;let out=product.prepare_execution_manifest(&p,&repo,&c,&r,TransactionId::parse("https-no-fresh-snapshot")?,11)?;
    let before=f.metadata.audit_events()?.len();let policy_reads=repo.calls.load(Ordering::SeqCst);let mut consumed=false;
    assert!(out.with_verified_guarded_job_preparation(&p,&repo,StoredJobPolicy::default(),rev::CommitId::generate(),rev::RevisionId::generate(),Default::default(),
        ||Err(()),|_,_,_|consumed=true).is_err());
    assert!(!consumed);assert_eq!(f.metadata.audit_events()?.len(),before);assert_eq!(repo.calls.load(Ordering::SeqCst),policy_reads);Ok(())
}
#[test]
fn replay_ambiguous_claim_and_foreign_lease_never_reach_workspace_validation_registration_or_cas()->TestResult{
    for mode in [1,2,3]{let(report,events,before,after,_)=execute(mode,false)?;
        assert_eq!(before,after);assert!(report.transaction.is_none()&&report.registered_intent.is_none());
        assert_eq!(events,if mode==3{vec!["claim","lease"]}else{vec!["claim"]});
        if mode==1{assert_eq!(report.stage,StoredJobRunStage::Replay);}else{assert!(report.repository_error.is_some());}
    }Ok(())
}
#[test]
fn unknown_validation_barrier_and_revocation_after_lease_preserve_head_without_registration_or_retry()->TestResult{
    for mode in [4,5]{let(report,events,before,after,_)=execute(mode,false)?;assert_eq!(before,after);
        assert!(report.transaction.as_ref().is_some_and(Result::is_err));assert!(report.registered_intent.is_none()&&report.revision_receipt.is_none());
        assert!(!events.contains(&"register")&&!events.contains(&"cas")&&!events.contains(&"complete"));
        assert_eq!(events.iter().filter(|&&s|s=="claim").count(),1);
        if mode==4{assert_eq!(report.repository_error,Some(rev::RevisionError::CommitOutcomeUnknown));}else{assert_eq!(report.cas_error,Some(StoredCommitError::CurrentGuard));}
    }Ok(())
}
#[test]
fn lost_completion_ack_retains_committed_effect_and_does_not_reexecute_or_reclaim()->TestResult{
    let(report,events,before,after,saved)=execute(6,false)?;assert_ne!(before,after);assert!(report.revision_receipt.is_some());
    assert_eq!(report.repository_error,Some(rev::RevisionError::CommitOutcomeUnknown));assert!(report.completion.is_none());
    for event in ["claim","lease","register","cas","complete"]{assert_eq!(events.iter().filter(|&&s|s==event).count(),1);}
    assert_eq!(output_uris(&saved,"actual-form-document")?,vec![Some("https://example.org/public?x=1&y=2".into())]);Ok(())
}
#[test]
fn rejected_or_uncertain_registration_keeps_receipts_and_blocks_revision_cas_without_retry()->TestResult{
    for mode in [7,8]{let(report,events,before,after,saved)=execute(mode,false)?;assert_eq!(before,after);assert!(!saved.is_empty());
        assert!(report.intent.is_some()&&report.precommit.is_some()&&report.registered_intent.is_none());
        assert!(events.contains(&"register")&&!events.contains(&"cas")&&!events.contains(&"complete"));
        assert_eq!(events.iter().filter(|&&s|s=="claim").count(),1);assert!(report.transaction.as_ref().is_some_and(Result::is_err));
    }Ok(())
}
