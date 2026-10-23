// Public-request adapter boundary. Synthetic repository only; actual recovery/SQL are separate evidence.
use super::*;
use revision_service::RevisionRepository;
use hwpx_agent_cli::form_stored_provider::actual_import::source_search::request_recovery::{StoredRequestRecoveryError as RE,StoredRequestRecoveryObservation as O};
use hwpx_agent_cli::stored_revision_commit::{ArchivedRegisteredStoredCommitRecoveryOutcome as AO,StoredCommitError};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{StoredRevisionJobRepository,StoredCommitRegistration,StoredCommitIntentRecord,StoredCommitIntentLookup};
struct Adapter{base:Model,mode:u8,reads:AtomicUsize,writes:AtomicUsize}
impl Adapter{fn new(s:&StoredFixture,mode:u8)->Self{Self{base:Model::new(s,if mode<=5{mode}else{4}),mode,reads:AtomicUsize::new(0),writes:AtomicUsize::new(0)}}}
impl rev::RevisionRepository for Adapter{
    fn authorize_context(&self,c:&rev::RevisionRequestContext)->Result<(),rev::RevisionError>{self.base.authorize_context(c)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{self.base.head(t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.base.node(t,p,r)}
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.base.compare_and_swap(c,r)}
}
impl StoredRequestLookupRepository for Adapter{
    fn observe_request(&self,c:&rev::RevisionRequestContext,q:&StoredRequestLookup)->Result<StoredRequestObservation,StoredRequestLookupError>{
        let out=self.base.observe_request(c,q)?;let count=self.base.calls.requests.lock().map_err(|_|rev::RevisionError::RepositoryFailure)?.len();
        if self.mode==6{return Ok(StoredRequestObservation::Existing(StoredJobObservation::observed(StoredJobOutcome::Replay,q.job_id(),StoredJobState::Claimed,0,0,None,None,None,None)?));}
        if self.mode==7{return Ok(StoredRequestObservation::Existing(StoredJobObservation::observed(StoredJobOutcome::Replay,uuid::Uuid::from_u128(777),StoredJobState::InProgress,1,1,None,None,None,None)?));}
        if self.mode==8&&count==2{return Ok(StoredRequestObservation::NotObserved);}
        if self.mode==9&&count==2{return Err(rev::RevisionError::InvalidRequest.into());}Ok(out)
    }
}
impl StoredRevisionJobRepository for Adapter{
    fn register_commit_intent(&self,_:&rev::RevisionRequestContext,_:&StoredCommitRegistration)->Result<StoredCommitIntentRecord,rev::RevisionError>{self.writes.fetch_add(1,Ordering::SeqCst);Err(rev::RevisionError::InvalidRequest)}
    fn read_commit_intent(&self,c:&rev::RevisionRequestContext,l:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,rev::RevisionError>{
        self.authorize_context(c)?;self.reads.fetch_add(1,Ordering::SeqCst);
        let requests=self.base.calls.requests.lock().map_err(|_|rev::RevisionError::RepositoryFailure)?;let q=requests.first().ok_or(rev::RevisionError::InvalidRequest)?;
        if l.project_id()!=q.project_id()||l.job_id()!=q.job_id()||l.idempotency_key()!=q.idempotency_key()||l.attempt_no()!=1{return Err(rev::RevisionError::InvalidRequest);}
        if self.mode==10{return Err(rev::RevisionError::CommitOutcomeUnknown);}Ok(None)
    }
}
fn assertions(repo:&rev::RevisionService<Adapter>,requests:usize,reads:usize)->R{
    assert_eq!(repo.repository().base.calls.requests.lock().map_err(|_|"mutex")?.len(),requests);
    assert_eq!(repo.repository().reads.load(Ordering::SeqCst),reads);assert_eq!(repo.repository().writes.load(Ordering::SeqCst),0);
    assert_eq!(repo.repository().base.calls.commits.load(Ordering::SeqCst),0);assert_eq!(repo.repository().base.calls.heads.load(Ordering::SeqCst),0);Ok(())
}
#[test]fn absent_request_never_reads_intent_or_content_or_starts_a_job()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,0));bound!(s,repo,actor,p);
    s.blobs.tamper.store(true,Ordering::SeqCst);let n=s.metadata.audit_events()?.len();let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;
    assert_eq!(q.recover_registered(&p,||20)?,O::NotObserved);assert_eq!(s.metadata.audit_events()?.len(),n);assert_eq!(f.reads.get(),0);assertions(&repo,1,0)
}
#[test]fn unstarted_attempt_remains_metadata_without_registered_lookup()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,6));bound!(s,repo,actor,p);
    let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;assert!(matches!(q.recover_registered(&p,||20)?,O::AttemptNotStarted(_)));assertions(&repo,1,0)
}
#[test]fn pending_and_terminal_metadata_derive_exact_same_registered_locator_not_completion()->R{
    for mode in[1,4]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,mode));bound!(s,repo,actor,p);
        let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;
        assert!(matches!(q.recover_registered(&p,||20)?,O::Existing{effect:AO::RegistrationNotObserved,..}));assertions(&repo,2,1)?;}Ok(())
}
#[test]fn foreign_job_observation_fails_before_registered_lookup()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,7));bound!(s,repo,actor,p);
    let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;assert!(matches!(q.recover_registered(&p,||20),Err(LE::Recovery(RE::Binding))));assertions(&repo,1,0)
}
#[test]fn lookup_conflict_unknown_and_unavailable_never_fall_back_to_recovery_or_execution()->R{
    for mode in[2,3,5]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,mode));bound!(s,repo,actor,p);
        let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;assert!(matches!(q.recover_registered(&p,||20),Err(LE::Recovery(RE::Lookup(_)))));assertions(&repo,1,0)?;}Ok(())
}
#[test]fn unknown_registered_read_is_reported_without_second_lookup_or_job_write()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,10));bound!(s,repo,actor,p);
    let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;assert!(matches!(q.recover_registered(&p,||20),Err(LE::Recovery(RE::Recovery(StoredCommitError::Unknown)))));assertions(&repo,1,1)
}
#[test]fn observation_change_during_recovery_is_explicit_not_retried()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,8));bound!(s,repo,actor,p);
    let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;assert!(matches!(q.recover_registered(&p,||20),Err(LE::Recovery(RE::ObservationChanged))));assertions(&repo,2,1)
}
#[test]fn current_acl_denial_on_final_lookup_does_not_return_prior_observation()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,9));bound!(s,repo,actor,p);
    let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;assert!(matches!(q.recover_registered(&p,||20),Err(LE::Recovery(RE::Lookup(_)))));assertions(&repo,2,1)
}
#[test]fn fresh_provider_scope_is_required_before_any_recovery_read()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,1));bound!(s,repo,actor,p);
    let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;
    let other=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign")?)?;
    assert!(q.recover_registered(&other,||20).is_err());assertions(&repo,0,0)
}
#[test]fn strict_preview_unknown_and_oversize_requests_do_not_enter_recovery()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Adapter::new(&s,1));bound!(s,repo,actor,p);
    let mut v=req(&s,&bytes,&f,false)?;v["locator"]=json!({"job":"caller-selected"});assert!(CP::prepare_lookup_json(&p,&wire(&v)?).is_err());
    v.as_object_mut().ok_or("object")?.remove("locator");v["operation"]["preview_only"]=json!(true);assert!(CP::prepare_lookup_json(&p,&wire(&v)?).is_err());
    assert!(CP::prepare_lookup_json(&p,&vec![b' ';16385]).is_err());assertions(&repo,0,0)
}
