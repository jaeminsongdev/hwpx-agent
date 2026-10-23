// Common entry tests only. Existing lookup/compiler/SQL bodies are not replayed.
use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::catalog_mask::entry::{CatalogRequestEntry as Entry,CatalogRequestEntryError as EE};

struct FreshModel{lookup:Model,inner:rev::InMemoryRevisionRepository}
impl rev::RevisionRepository for FreshModel{
    fn authorize_context(&self,c:&rev::RevisionRequestContext)->Result<(),rev::RevisionError>{rev::RevisionRepository::authorize_context(&self.lookup,c)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{
        self.lookup.calls.heads.fetch_add(1,Ordering::SeqCst);rev::RevisionRepository::head(&self.inner,t,p,b)}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{
        self.lookup.calls.heads.fetch_add(1,Ordering::SeqCst);rev::RevisionRepository::node(&self.inner,t,p,r)}
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{
        rev::RevisionRepository::compare_and_swap(&self.lookup,c,r)}
}
impl StoredRequestLookupRepository for FreshModel{
    fn observe_request(&self,c:&rev::RevisionRequestContext,q:&StoredRequestLookup)->Result<StoredRequestObservation,StoredRequestLookupError>{
        self.lookup.observe_request(c,q)}
}

#[test]
fn existing_completed_job_skips_source_catalog_and_compiler()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,1));bound!(s,repo,actor,p);
    let raw=wire(&req(&s,&bytes,&f,false)?)?;let events=s.metadata.audit_events()?.len();s.blobs.tamper.store(true,Ordering::SeqCst);
    let out=Dispatch::prepare_catalog_mask_or_observe_json(&p,&f,&raw,Limits::standard()?,4)?;
    let Entry::Existing(ref observed)=out else{return Err("existing".into())};assert_eq!(observed.state(),StoredJobState::TerminalSuccess);
    assert_eq!(f.reads.get(),0);assert_eq!(s.metadata.audit_events()?.len(),events);assert_eq!(repo.repository().calls.heads.load(Ordering::SeqCst),0);
    assert_eq!(repo.repository().calls.requests.lock().map_err(|_|"mutex")?.len(),1);assert_eq!(repo.repository().calls.commits.load(Ordering::SeqCst),0);
    assert_eq!(format!("{out:?}"),"CatalogRequestEntry::Existing(<redacted>; observation_not_authority)");Ok(())
}
#[test]
fn existing_in_progress_is_observed_without_wait_or_retry()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,4));bound!(s,repo,actor,p);
    let Entry::Existing(out)=Dispatch::prepare_catalog_mask_or_observe_json(&p,&f,&wire(&req(&s,&bytes,&f,false)?)?,Limits::standard()?,4)?else{return Err("existing".into())};
    assert_eq!(out.state(),StoredJobState::InProgress);assert_eq!(f.reads.get(),0);assert_eq!(repo.repository().calls.requests.lock().map_err(|_|"mutex")?.len(),1);Ok(())
}
#[test]
fn lookup_conflict_unknown_and_unavailable_never_fall_back_to_preparation()->R{
    for mode in[2,3,5]{let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,mode));bound!(s,repo,actor,p);
        let error=Dispatch::prepare_catalog_mask_or_observe_json(&p,&f,&wire(&req(&s,&bytes,&f,false)?)?,Limits::standard()?,4).expect_err("lookup failed");
        match mode{2=>assert!(matches!(error,EE::Lookup(LE::Repository(StoredRequestLookupError::KeyConflict)))),
            3=>assert!(matches!(error,EE::Lookup(LE::Repository(StoredRequestLookupError::Repository(rev::RevisionError::CommitOutcomeUnknown))))),
            _=>assert!(matches!(error,EE::Lookup(LE::Repository(StoredRequestLookupError::Repository(rev::RevisionError::RepositoryFailure)))))}
        assert_eq!(f.reads.get(),0);assert_eq!(repo.repository().calls.heads.load(Ordering::SeqCst),0);assert_eq!(repo.repository().calls.commits.load(Ordering::SeqCst),0);
    }Ok(())
}
#[test]
fn unobserved_request_uses_original_compiler_and_remains_route_unqualified()->R{
    let bytes=raw("KEEP MARK END")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");
    let repo=rev::RevisionService::new(FreshModel{lookup:Model::new(&s,0),inner:s.revisions.repository().clone()});bound!(s,repo,actor,p);
    let Entry::Prepared(out)=Dispatch::prepare_catalog_mask_or_observe_json(&p,&f,&wire(&req(&s,&bytes,&f,false)?)?,Limits::standard()?,4)?else{return Err("prepared".into())};
    assert!(out.with_verified_bytes(&p,&f,5,section)??.contains("KEEP **** END"));assert!(!out.compiled().operations().is_empty());
    assert!(out.require_current_product_route(&p,&f,5).is_err());assert_eq!(repo.repository().lookup.calls.requests.lock().map_err(|_|"mutex")?.len(),1);
    assert_eq!(repo.repository().lookup.calls.commits.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn unobserved_request_does_not_hide_current_catalog_drift()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let raw=wire(&req(&s,&bytes,&f,false)?)?;
    let other=feed("OTHER");let repo=rev::RevisionService::new(FreshModel{lookup:Model::new(&s,0),inner:s.revisions.repository().clone()});bound!(s,repo,actor,p);
    assert!(matches!(Dispatch::prepare_catalog_mask_or_observe_json(&p,&other,&raw,Limits::standard()?,4),Err(EE::Preparation(_))));
    assert_eq!(repo.repository().lookup.calls.requests.lock().map_err(|_|"mutex")?.len(),1);assert_eq!(repo.repository().lookup.calls.commits.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn unobserved_request_does_not_hide_source_readback_failure()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let raw=wire(&req(&s,&bytes,&f,false)?)?;
    let repo=rev::RevisionService::new(FreshModel{lookup:Model::new(&s,0),inner:s.revisions.repository().clone()});bound!(s,repo,actor,p);s.blobs.tamper.store(true,Ordering::SeqCst);
    assert!(matches!(Dispatch::prepare_catalog_mask_or_observe_json(&p,&f,&raw,Limits::standard()?,4),Err(EE::Preparation(_))));
    assert_eq!(repo.repository().lookup.calls.requests.lock().map_err(|_|"mutex")?.len(),1);assert_eq!(repo.repository().lookup.calls.commits.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn strict_request_or_preview_reject_before_lookup_and_source()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,1));bound!(s,repo,actor,p);
    let mut unknown=req(&s,&bytes,&f,false)?;unknown["claim"]=json!(true);
    for raw in[wire(&unknown)?,wire(&req(&s,&bytes,&f,true)?)?,vec![b' ';16385]]{
        assert!(matches!(Dispatch::prepare_catalog_mask_or_observe_json(&p,&f,&raw,Limits::standard()?,4),Err(EE::Lookup(_))));}
    assert_eq!(f.reads.get(),0);assert!(repo.repository().calls.requests.lock().map_err(|_|"mutex")?.is_empty());Ok(())
}
#[test]
fn current_write_scope_is_required_even_for_existing_job()->R{
    let bytes=raw("MARK")?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let f=feed("MARK");let repo=rev::RevisionService::new(Model::new(&s,1));
    let p=StoredFormProvider::bind(&s.artifacts,&repo,&s.reader,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    assert!(matches!(Dispatch::prepare_catalog_mask_or_observe_json(&p,&f,&wire(&req(&s,&bytes,&f,false)?)?,Limits::standard()?,4),Err(EE::Lookup(_))));
    assert!(repo.repository().calls.requests.lock().map_err(|_|"mutex")?.is_empty());assert_eq!(f.reads.get(),0);Ok(())
}
