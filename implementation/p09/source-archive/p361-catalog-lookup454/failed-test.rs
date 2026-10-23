// Strict request/scope with synthetic observation repository. No SQL or executed effect proof.
use super::*;
use std::sync::{Arc,Mutex};
use hwpx_agent_cli::form_product_request::stored_literal_replacement::personal_info::catalog::request_lookup::CatalogRequestLookupError as LE;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{request_lookup::*,lifecycle::{StoredJobObservation,StoredJobState,StoredJobOutcome}};
struct Calls{heads:AtomicUsize,commits:AtomicUsize,requests:Mutex<Vec<StoredRequestLookup>>}
#[derive(Clone)]struct Model{context:rev::RevisionRequestContext,calls:Arc<Calls>,mode:u8}
impl Model{fn new(s:&StoredFixture,mode:u8)->Self{Self{context:s.revision_context.clone(),calls:Arc::new(Calls{heads:AtomicUsize::new(0),commits:AtomicUsize::new(0),requests:Mutex::new(vec![])}),mode}}}
impl rev::RevisionRepository for Model{
    fn authorize_context(&self,c:&rev::RevisionRequestContext)->Result<(),rev::RevisionError>{
        if c.tenant_id()!=self.context.tenant_id()||c.subject()!=self.context.subject(){Err(rev::RevisionError::NotFound)}else{Ok(())}}
    fn head(&self,_:TenantId,_:rev::ProjectId,_:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{self.calls.heads.fetch_add(1,Ordering::SeqCst);Err(rev::RevisionError::RepositoryFailure)}
    fn node(&self,_:TenantId,_:rev::ProjectId,_:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{self.calls.heads.fetch_add(1,Ordering::SeqCst);Err(rev::RevisionError::RepositoryFailure)}
    fn compare_and_swap(&self,_:&rev::RevisionRequestContext,_:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{self.calls.commits.fetch_add(1,Ordering::SeqCst);Err(rev::RevisionError::InvalidRequest)}
}
impl StoredRequestLookupRepository for Model{
    fn observe_request(&self,c:&rev::RevisionRequestContext,q:&StoredRequestLookup)->Result<StoredRequestObservation,StoredRequestLookupError>{
        self.authorize_context(c)?;self.calls.requests.lock().map_err(|_|rev::RevisionError::RepositoryFailure)?.push(q.clone());
        match self.mode{0=>Ok(StoredRequestObservation::NotObserved),2=>Err(StoredRequestLookupError::KeyConflict),3=>Err(rev::RevisionError::CommitOutcomeUnknown.into()),
            5=>Err(rev::RevisionError::RepositoryFailure.into()),mode=>Ok(StoredRequestObservation::Existing(StoredJobObservation::observed(StoredJobOutcome::Replay,q.job_id(),
                if mode==4{StoredJobState::InProgress}else{StoredJobState::TerminalSuccess},1,1,None,
                if mode==4{None}else{Some(rev::RevisionId::parse("rev_00000000000000000000000000000901")?)},None,
                if mode==4{None}else{Some(artifact_service::ArtifactId::generate())})?))}
    }
}
macro_rules! bound{($s:ident,$repo:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$repo,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
#[test]
fn cold_preparation_and_observation_never_read_source_head_catalog_or_compile()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,0));bound!(s,repo,actor,p);
    let events=s.metadata.audit_events()?.len();s.blobs.tamper.store(true,Ordering::SeqCst);let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;
    assert_eq!(q.observe(&p)?,StoredRequestObservation::NotObserved);assert_eq!(f.reads.get(),0);assert_eq!(s.metadata.audit_events()?.len(),events);
    assert_eq!(repo.repository().calls.heads.load(Ordering::SeqCst),0);assert_eq!(repo.repository().calls.commits.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn strict_request_and_preview_reject_before_repository_or_source_access()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,0));bound!(s,repo,actor,p);let v=req(&s,&bytes,&f,false)?;
    let mut unknown=v.clone();unknown["claim"]=json!(true);let mut preview=v.clone();preview["operation"]["preview_only"]=json!(true);
    for raw in[wire(&unknown)?,wire(&preview)?,b"null".to_vec(),vec![b' ';16385]]{assert!(CP::prepare_lookup_json(&p,&raw).is_err());}
    assert!(repo.repository().calls.requests.lock().map_err(|_|"mutex")?.is_empty());assert_eq!(repo.repository().calls.heads.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn current_read_write_and_external_document_scope_remain_mandatory()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,0));bound!(s,repo,actor,p);
    let raw=wire(&req(&s,&bytes,&f,false)?)?;let prepared=CP::prepare_lookup_json(&p,&raw)?;
    for scopes in[vec![AuthScope::DocumentRead],vec![AuthScope::DocumentWrite]]{let actor=RequestContext::new(s.reader.tenant_id(),s.reader.subject(),scopes);
        let bad=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
        assert!(CP::prepare_lookup_json(&bad,&raw).is_err());assert!(prepared.observe(&bad).is_err());}
    let bad=StoredFormProvider::bind(&s.artifacts,&repo,&actor,&s.revision_context,s.project,s.branch,DocumentId::parse("foreign")?)?;
    assert!(prepared.observe(&bad).is_err());assert!(repo.repository().calls.requests.lock().map_err(|_|"mutex")?.is_empty());Ok(())
}
#[test]
fn existing_pending_or_complete_state_is_only_an_observation_without_executor_calls()->R{
    for mode in[1,4]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,mode));bound!(s,repo,actor,p);
        let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;let StoredRequestObservation::Existing(observed)=q.observe(&p)?else{return Err("existing observation".into())};
        assert_eq!(observed.outcome(),StoredJobOutcome::Replay);assert_eq!(observed.attempt_no(),1);assert_eq!(repo.repository().calls.commits.load(Ordering::SeqCst),0);
        assert_eq!(format!("{q:?}"),"PreparedCatalogRequestLookup(<redacted>; observation_not_authority)");}Ok(())
}
#[test]
fn key_conflict_unknown_or_unavailable_never_falls_back_to_claim_or_retry()->R{
    for mode in[2,3,5]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,mode));bound!(s,repo,actor,p);
        let q=CP::prepare_lookup_json(&p,&wire(&req(&s,&bytes,&f,false)?)?)?;let failure=q.observe(&p).expect_err("lookup error");
        match mode{2=>assert!(matches!(failure,LE::Repository(StoredRequestLookupError::KeyConflict))),3=>assert!(matches!(failure,LE::Repository(StoredRequestLookupError::Repository(rev::RevisionError::CommitOutcomeUnknown)))),_=>assert!(matches!(failure,LE::Repository(StoredRequestLookupError::Repository(rev::RevisionError::RepositoryFailure))))}
        assert_eq!(repo.repository().calls.requests.lock().map_err(|_|"mutex")?.len(),1);assert_eq!(repo.repository().calls.heads.load(Ordering::SeqCst),0);assert_eq!(repo.repository().calls.commits.load(Ordering::SeqCst),0);}Ok(())
}
#[test]
fn changed_content_keeps_job_id_but_binds_different_full_lookup_request()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,0));bound!(s,repo,actor,p);let mut v=req(&s,&bytes,&f,false)?;
    CP::prepare_lookup_json(&p,&wire(&v)?)?.observe(&p)?;v["plan_id"]=json!("another-request-plan");CP::prepare_lookup_json(&p,&wire(&v)?)?.observe(&p)?;
    let rows=repo.repository().calls.requests.lock().map_err(|_|"mutex")?;assert_eq!(rows.len(),2);assert_eq!(rows[0].job_id(),rows[1].job_id());assert_ne!(rows[0],rows[1]);Ok(())
}
