use super::*;
use revision_service::postgres::{RevisionLeaseIdentity,source_formula_policy::issuer_registry::stored_revision_jobs::*};
use std::sync::{Mutex,atomic::AtomicUsize};
// Trusted repository fixture, NOT an actual SQL lease, SQL23 admission or durable restart proof.
fn lease()->Result<StoredJobLease,RevisionError>{StoredJobLease::new(RevisionLeaseIdentity{
    idempotency_key:Uuid::from_u128(8001),job_id:Uuid::from_u128(8002),agent_instance_id:Uuid::from_u128(8003),
    execution_id:Uuid::from_u128(8004),attempt_no:1,fencing_token:1,authorization_id:Uuid::from_u128(8005)})}
type Key=(revision_service::ProjectId,Uuid,Uuid,i32);
struct Jobs{
    inner:FaultRevision,context:RevisionRequestContext,lease:StoredJobLease,mode:u8,
    registered:AtomicUsize,drift:AtomicBool,events:Mutex<Vec<&'static str>>,records:Mutex<std::collections::BTreeMap<Key,StoredCommitIntentRecord>>,
}
impl Jobs{
    fn service(f:&StoredFixture,mode:u8,cas_mode:u8)->Result<RevisionService<Self>,Box<dyn Error>>{
        Ok(RevisionService::new(Self{inner:FaultRevision::service(f,cas_mode).repository().clone(),context:f.revision_context.clone(),lease:lease()?,mode,
            registered:AtomicUsize::new(0),drift:AtomicBool::new(false),events:Mutex::default(),records:Mutex::default()}))
    }
    fn event(&self,event:&'static str)->Result<(),RevisionError>{self.events.lock().map_err(|_|RevisionError::RepositoryFailure)?.push(event);Ok(())}
}
impl RevisionRepository for Jobs{
    fn authorize_context(&self,c:&RevisionRequestContext)->Result<(),RevisionError>{
        if c.tenant_id()!=self.context.tenant_id()||c.subject()!=self.context.subject(){Err(RevisionError::NotFound)}else{Ok(())}
    }
    fn compare_and_swap(&self,c:&RevisionRequestContext,r:&RevisionCommitRequest)->Result<CommitOutcome,RevisionError>{self.authorize_context(c)?;self.event("cas")?;self.inner.compare_and_swap(c,r)}
    fn head(&self,t:TenantId,p:revision_service::ProjectId,b:BranchId)->Result<RevisionHead,RevisionError>{self.inner.head(t,p,b)}
    fn node(&self,t:TenantId,p:revision_service::ProjectId,r:RevisionId)->Result<RevisionNode,RevisionError>{
        if self.drift.load(Ordering::SeqCst){return Err(RevisionError::NotFound);}self.inner.node(t,p,r)
    }
}
impl StoredRevisionJobRepository for Jobs{
    fn register_commit_intent(&self,c:&RevisionRequestContext,r:&StoredCommitRegistration)->Result<StoredCommitIntentRecord,RevisionError>{
        self.authorize_context(c)?;self.event("register")?;self.registered.fetch_add(1,Ordering::SeqCst);
        if r.lease()!=self.lease||self.mode==1{return Err(RevisionError::RepositoryFailure);}
        if self.mode==2{return Err(RevisionError::CommitOutcomeUnknown);}
        let record=StoredCommitIntentRecord::expected(c,r)?;let id=r.lease().identity();
        self.records.lock().map_err(|_|RevisionError::RepositoryFailure)?.insert((r.request().project_id(),id.idempotency_key,id.job_id,id.attempt_no),record.clone());
        if self.mode==3{return Err(RevisionError::CommitOutcomeUnknown);}
        if self.mode==4{return StoredCommitIntentRecord::expected(&RevisionRequestContext::new(c.tenant_id(),SubjectDigest::from_authenticated_subject("foreign registry reader").map_err(|_|RevisionError::InvalidRequest)?),r);}
        if self.mode==5{self.drift.store(true,Ordering::SeqCst);}
        Ok(record)
    }
    fn read_commit_intent(&self,c:&RevisionRequestContext,l:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,RevisionError>{
        self.authorize_context(c)?;self.event("read")?;
        Ok(self.records.lock().map_err(|_|RevisionError::RepositoryFailure)?.get(&(l.project_id(),l.idempotency_key(),l.job_id(),l.attempt_no())).cloned())
    }
}

#[test]
fn exact_same_repository_registers_both_receipts_before_the_only_cas()->TestResult{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-success")?;let revisions=Jobs::service(&f,0,0)?;
    let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
    let root=tempfile::tempdir()?;execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas)?;
    let record=cas.registered_job_intent().ok_or("registered record")?;
    assert_eq!(record.intent_artifact_id(),cas.retained_intent().ok_or("intent")?.artifact_id);
    assert_eq!(record.precommit_artifact_id(),cas.retained_precommit().ok_or("precommit")?.artifact_id);
    assert_eq!(record.request_sha256(),cas.service_request().ok_or("request")?.canonical_sha256()?);
    assert_eq!(*revisions.repository().events.lock().map_err(|_|"events")?,vec!["register","cas"]);
    assert_eq!(revisions.repository().registered.load(Ordering::SeqCst),1);assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),1);Ok(())
}
#[test]
fn known_registration_failure_prevents_cas_but_retains_service_receipts()->TestResult{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-failed")?;let revisions=Jobs::service(&f,1,0)?;
    let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
    let root=tempfile::tempdir()?;let failure=execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas).expect_err("registration failed");
    assert_eq!(failure.primary(),TransactionError::RevisionCasFailed);assert_eq!(failure.receipt().state(),TransactionState::Quarantined);
    assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),0);assert!(cas.registered_job_intent().is_none());
    for id in[cas.retained_intent().ok_or("intent")?.artifact_id,cas.retained_precommit().ok_or("precommit")?.artifact_id]{assert!(!f.artifacts.download(&c,id,11)?.is_empty());}
    assert_eq!(revisions.head(&f.revision_context,f.project,f.branch)?,f.head);Ok(())
}
#[test]
fn registration_ack_unknown_before_or_after_storage_preserves_outputs_and_never_calls_cas()->TestResult{
    for mode in[2,3]{let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-unknown")?;let revisions=Jobs::service(&f,mode,0)?;
        let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
        let root=tempfile::tempdir()?;let failure=execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas).expect_err("registration unknown");
        assert_eq!(failure.primary(),TransactionError::RevisionOutcomeUnknown);assert_eq!(failure.receipt().artifact_disposition(),ArtifactDisposition::CommittedOutcomeUncertain);
        assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),0);assert!(cas.registered_job_intent().is_none());
        assert_eq!(revisions.repository().records.lock().map_err(|_|"records")?.is_empty(),mode==2);
        assert_eq!(f.artifacts.download(&c,cas.retained_result().ok_or("result")?.artifact_id,11)?,OUTPUT);
        assert_eq!(revisions.head(&f.revision_context,f.project,f.branch)?,f.head);
    }Ok(())
}
#[test]
fn foreign_returned_registration_is_retained_for_diagnosis_but_never_committed()->TestResult{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-foreign")?;let revisions=Jobs::service(&f,4,0)?;
    let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
    let root=tempfile::tempdir()?;execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas).expect_err("foreign record");
    assert_eq!(cas.error(),Some(StoredCommitError::Binding));assert!(cas.registered_job_intent().is_none());assert!(cas.registration_response().is_some());
    assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn source_recheck_after_registration_blocks_cas_on_current_node_loss()->TestResult{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-source-drift")?;let revisions=Jobs::service(&f,5,0)?;
    let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
    let root=tempfile::tempdir()?;execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas).expect_err("source lost");
    assert_eq!(cas.error(),Some(StoredCommitError::Source));assert!(cas.registered_job_intent().is_some());
    assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn registered_commit_ack_loss_keeps_exact_lookup_and_readonly_commit_recovery()->TestResult{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-cas-unknown")?;let revisions=Jobs::service(&f,0,3)?;
    let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
    let root=tempfile::tempdir()?;let failure=execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas).expect_err("CAS unknown");
    assert_eq!(failure.primary(),TransactionError::RevisionOutcomeUnknown);let id=lease()?.identity();
    let record=revisions.repository().read_commit_intent(&f.revision_context,StoredCommitIntentLookup::new(f.project,id.idempotency_key,id.job_id,id.attempt_no)?)?.ok_or("record")?;
    assert_eq!(record,cas.registered_job_intent().ok_or("registered")?.clone());
    let pin=StoredCommitRecoveryBinding{intent:record.intent_artifact_id(),intent_sha256:record.intent_sha256(),manifest:&m,
        request:cas.service_request().ok_or("request")?,result_sha256:ContentDigest::of(OUTPUT),result_size:OUTPUT.len()as u64};
    assert!(matches!(reconcile_stored_commit(&f.artifacts,&revisions,&f.reader,&f.revision_context,&pin,||12)?,StoredCommitRecoveryOutcome::Committed{..}));
    assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),1);Ok(())
}
#[test]
fn single_use_registered_adapter_never_registers_or_commits_twice()->TestResult{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-single-use")?;let revisions=Jobs::service(&f,0,0)?;
    let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),lease()?,||10)?;
    let root=tempfile::tempdir()?;let mut captured=None;execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut |request:&EngineRequest|{captured=Some(request.clone());cas.compare_and_swap(request)})?;
    assert_eq!(cas.compare_and_swap(captured.as_ref().ok_or("request")?),RevisionCasOutcome::Unknown);
    assert_eq!(revisions.repository().registered.load(Ordering::SeqCst),1);assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),1);Ok(())
}
#[test]
fn lease_lookup_bounds_and_redacted_debug_do_not_mint_authority()->TestResult{
    let good=lease()?;for field in 0..8{let mut id=good.identity();match field{0=>id.idempotency_key=Uuid::nil(),1=>id.job_id=Uuid::nil(),2=>id.agent_instance_id=Uuid::nil(),3=>id.execution_id=Uuid::nil(),4=>id.authorization_id=Uuid::nil(),5=>id.attempt_no=0,6=>id.attempt_no=11,_=>id.fencing_token=2};assert!(StoredJobLease::new(id).is_err());}
    assert_eq!(format!("{good:?}"),"StoredJobLease(<redacted>)");assert!(StoredCommitIntentLookup::new(revision_service::ProjectId::generate(),Uuid::nil(),Uuid::new_v4(),1).is_err());
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registered-wrong-lease")?;let revisions=Jobs::service(&f,0,0)?;
    let mut wrong=good.identity();wrong.job_id=Uuid::new_v4();let wrong=StoredJobLease::new(wrong)?;
    let mut cas=StoredResultRevisionCas::bind_registered(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),wrong,||10)?;
    let root=tempfile::tempdir()?;execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas).expect_err("fake lease rejected by repository");assert_eq!(revisions.repository().inner.calls.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn registration_rejects_bad_receipt_hash_alias_size_media_state_and_foreign_result()->TestResult{
    let f=fixture()?;let c=writer(&f);let m=manifest_fixture::manifest(&f,"registration-descriptors")?;let revisions=FaultRevision::service(&f,2);
    let mut cas=StoredResultRevisionCas::bind(&f.artifacts,&revisions,&c,&f.revision_context,binding(&f,&m,OUTPUT),||10)?;let root=tempfile::tempdir()?;
    execute(&root.path().join("workspace"),m.clone(),OUTPUT,&mut cas).expect_err("stage immutable descriptors only");
    let request=cas.service_request().ok_or("request")?.clone();let original_result=cas.retained_result().ok_or("result")?.clone();let original_intent=cas.retained_intent().ok_or("intent")?.clone();let original_precommit=cas.retained_precommit().ok_or("precommit")?.clone();
    for mode in 0..6{let mut result=original_result.clone();let mut intent=original_intent.clone();let mut precommit=original_precommit.clone();
        match mode{0=>precommit.sha256=ContentDigest::of(b"wrong receipt hash"),1=>intent.artifact_id=precommit.artifact_id,2=>precommit.storage_state=artifact_service::StorageState::Quarantined,
            3=>result.artifact_id=artifact_service::ArtifactId::generate(),4=>intent.media_type=MediaType::parse("application/octet-stream")?,_=>intent.size_bytes=65537}
        assert_eq!(StoredCommitRegistration::new(lease()?,request.clone(),&result,&intent,&precommit).expect_err("invalid registration"),RevisionError::InvalidRequest);
    }Ok(())
}
#[path="stored_registered_recovery.rs"] mod recovery_read_v1;
