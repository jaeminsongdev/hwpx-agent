use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::{StoredProductRequest as Entry,StoredProductOperationError,
    https_targets::{HttpsTargetProductLimits as Limits,HttpsTargetProductError as PE,HttpsTargetRequestEntry,HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA}};
use revision_service as rev;
use rev::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{request_lookup::*,lifecycle::{StoredJobObservation,StoredJobState,StoredJobOutcome}};
pub(super) fn budget()->Result<Limits,Box<dyn Error>>{Ok(Limits::standard()?)}
pub(super) fn raw(f:&StoredFixture,bytes:&[u8])->Result<serde_json::Value,Box<dyn Error>>{
    let s=selections(bytes)?;Ok(serde_json::json!({"schema_version":HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA,"idempotency_key":"https-request-key",
        "project_id":f.project.public_id(),"document_id":"actual-form-document","base_revision":f.head.revision_id().ok_or("head")?.public_id(),
        "expected_head_generation":f.head.generation(),"expected_source_package_sha256":hex::encode(Sha256::digest(bytes)),"plan_id":"https-public-request",
        "operation":{"kind":"change_https_targets","changes":[{"reference_id":s[0].reference_id,"expected_source_field_sha256":hex::encode(s[0].source_field_sha256),
            "expected_meaning_sha256":hex::encode(s[0].meaning_sha256),"target":{"kind":"https","uri":"https://example.org/public?x=1&y=2"}}]}}))
}
fn wire(v:&serde_json::Value)->Result<Vec<u8>,Box<dyn Error>>{Ok(serde_json::to_vec(v)?)}
fn small()->Result<Vec<u8>,Box<dyn Error>>{fixture::package(&link(1,"https://example.org/old"))}
pub(super) fn allowed(f:&StoredFixture,source:&StoredImportedDocumentForms)->Result<Repository,Box<dyn Error>>{
    repo(f,source,&policy(&[&target("https://example.org/public?x=1&y=2")])?)
}
struct Calls{heads:AtomicUsize,commits:AtomicUsize,lookups:Mutex<Vec<StoredRequestLookup>>}
#[derive(Clone)]struct Model{inner:rev::InMemoryRevisionRepository,context:rev::RevisionRequestContext,calls:Arc<Calls>,mode:u8}
impl Model{fn new(f:&StoredFixture,mode:u8)->Self{Self{inner:f.revisions.repository().clone(),context:f.revision_context.clone(),mode,
    calls:Arc::new(Calls{heads:AtomicUsize::new(0),commits:AtomicUsize::new(0),lookups:Mutex::new(vec![])})}}}
impl rev::RevisionRepository for Model{
    fn authorize_context(&self,c:&rev::RevisionRequestContext)->Result<(),rev::RevisionError>{
        if c.tenant_id()!=self.context.tenant_id()||c.subject()!=self.context.subject(){Err(rev::RevisionError::NotFound)}else{Ok(())}}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{
        self.calls.heads.fetch_add(1,Ordering::SeqCst);if self.mode==0{self.inner.head(t,p,b)}else{Err(rev::RevisionError::RepositoryFailure)}}
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{
        self.calls.heads.fetch_add(1,Ordering::SeqCst);if self.mode==0{self.inner.node(t,p,r)}else{Err(rev::RevisionError::RepositoryFailure)}}
    fn compare_and_swap(&self,_:&rev::RevisionRequestContext,_:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{
        self.calls.commits.fetch_add(1,Ordering::SeqCst);Err(rev::RevisionError::InvalidRequest)}
}
impl StoredRequestLookupRepository for Model{
    fn observe_request(&self,c:&rev::RevisionRequestContext,q:&StoredRequestLookup)->Result<StoredRequestObservation,StoredRequestLookupError>{
        rev::RevisionRepository::authorize_context(self,c)?;self.calls.lookups.lock().map_err(|_|rev::RevisionError::RepositoryFailure)?.push(q.clone());
        match self.mode{0=>Ok(StoredRequestObservation::NotObserved),2=>Err(StoredRequestLookupError::KeyConflict),3=>Err(rev::RevisionError::CommitOutcomeUnknown.into()),
            5=>Err(rev::RevisionError::RepositoryFailure.into()),mode=>Ok(StoredRequestObservation::Existing(StoredJobObservation::observed(StoredJobOutcome::Replay,q.job_id(),
                if mode==4{StoredJobState::InProgress}else{StoredJobState::TerminalSuccess},1,1,None,
                if mode==4{None}else{Some(rev::RevisionId::parse("rev_00000000000000000000000000000901")?)},None,
                if mode==4{None}else{Some(artifact_service::ArtifactId::generate())})?))}
    }
}
#[test]
fn captured_public_request_owns_source_and_delivers_compiled_candidate_without_claim_or_uri_receipt()->TestResult{
    let bytes=fixture::captured()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;
    let source=provider.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;drop(source);
    let raw=wire(&raw(&f,&bytes)?)?;let prepared=Entry::prepare_https_targets_json(&provider,&repository,&raw,budget()?,10)?;
    assert_eq!(prepared.verify(&provider,&repository,11)?,prepared.receipt());
    let q=Entry::prepare_https_targets_lookup_json(&provider,&raw,budget()?)?;
    assert_eq!(hex::encode(q.canonical_request_sha256()),prepared.receipt().canonical_request_sha256);
    assert_eq!(hex::encode(q.scoped_request_sha256()),prepared.receipt().scoped_request_sha256);
    assert_eq!(prepared.receipt().raw_request_sha256,hex::encode(Sha256::digest(&raw)));
    assert_eq!(prepared.compiled().canonical_sha256()?,prepared.receipt().compiled.compiled_plan_sha256);
    let output=prepared.with_verified_bytes(&provider,&repository,12,|b|b.to_vec())?;
    assert_eq!(output_uris(&output,"actual-form-document")?,vec![Some("https://example.org/public?x=1&y=2".into())]);
    for value in [serde_json::to_string(prepared.receipt())?,format!("{prepared:?}"),format!("{q:?}")]{assert!(!value.contains("https://")&&!value.contains("PRIVATE"));}
    assert!(!prepared.receipt().idempotency_key_claimed&&!prepared.receipt().execution_or_publication_authority);
    assert!(prepared.require_current_product_route(&provider,&repository,13).is_err());
    assert_eq!(f.revisions.head(&f.revision_context,f.project,f.branch)?,f.head);
    assert_eq!(f.metadata.audit_events()?.iter().filter(|e|e.event=="artifact.ingested").count(),3);Ok(())
}
#[test]
fn strict_nested_object_shapes_unknown_duplicate_and_unsafe_target_requests_fail_before_reads()->TestResult{
    let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;
    let source=provider.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let original=raw(&f,&bytes)?;let before=f.metadata.audit_events()?.len();
    for i in 0..25{let mut v=original.clone();match i{
        0=>v["unknown"]=true.into(),1=>v["policy"]=serde_json::json!({"allow_https":true}),2=>v["policy_artifact"]="art_00000000000000000000000000000001".into(),
        3=>v["operation"]["kind"]="execute_url".into(),4=>v["operation"]["changes"][0]["target"]=serde_json::json!({"kind":"mailto","address":"nobody@example.org"}),
        5=>v["operation"]["changes"][0]["target"]["uri"]="http://example.org/unsafe".into(),6=>v["operation"]["changes"][0]["expected_meaning_sha256"]="A".repeat(64).into(),
        7=>v["expected_source_package_sha256"]="bad".into(),8=>v["expected_head_generation"]=0.into(),9=>v["expected_head_generation"]=u64::MAX.into(),
        10=>v["operation"]["changes"]=serde_json::json!([]),11=>{let duplicate=v["operation"]["changes"][0].clone();v["operation"]["changes"].as_array_mut().ok_or("changes")?.push(duplicate);},
        12=>v["operation"]["changes"][0]["unknown"]=true.into(),13=>v["operation"]["changes"][0]["target"]["unknown"]=true.into(),
        14=>{v.as_object_mut().ok_or("object")?.remove("idempotency_key");},15=>v["base_revision"]="not-a-service-revision".into(),
        16=>v=serde_json::json!([]),17=>v["operation"]=serde_json::json!(["change_https_targets",v["operation"]["changes"].clone()]),
        18=>v["operation"]["changes"][0]=serde_json::json!(["array-change"]),19=>v["operation"]["changes"][0]["target"]=serde_json::json!(["https","https://example.org"]),
        20=>v["schema_version"]="hwpx-agent.unknown-request/v1".into(),21=>v["operation"]["changes"][0]["expected_source_field_sha256"]="z".repeat(64).into(),
        22=>{v["operation"]["changes"][0].as_object_mut().ok_or("change")?.remove("reference_id");},_=>{}}
        let mut raw=wire(&v)?;if i==23{raw.extend_from_slice(b" {}");}if i==24{let mut duplicate=b"{\"plan_id\":\"duplicate\",".to_vec();duplicate.extend_from_slice(&raw[1..]);raw=duplicate;}
        assert!(Entry::prepare_https_targets_json(&provider,&repository,&raw,budget()?,10).is_err(),"strict matrix {i}");
        assert!(Entry::prepare_https_targets_lookup_json(&provider,&raw,budget()?).is_err(),"lookup matrix {i}");
    }
    assert_eq!(repository.calls.load(Ordering::SeqCst),0);assert_eq!(f.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn wrong_scope_read_only_stale_head_or_source_digest_never_reaches_policy_or_lowering()->TestResult{
    let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;let read=f.provider()?;
    let source=provider.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let original=raw(&f,&bytes)?;
    for i in 0..6{let mut v=original.clone();match i{0=>v["document_id"]="foreign-document".into(),1=>v["project_id"]=rev::ProjectId::generate().public_id().into(),
        2=>v["base_revision"]=rev::RevisionId::generate().public_id().into(),3=>v["expected_head_generation"]=2.into(),4=>v["expected_source_package_sha256"]="0".repeat(64).into(),_=>{}}
        assert!(Entry::prepare_https_targets_json(if i==5{&read}else{&provider},&repository,&wire(&v)?,budget()?,10).is_err(),"binding {i}");
    }assert_eq!(repository.calls.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn canonical_lookup_ignores_json_layout_but_binds_full_changes_and_trusted_scope_without_reads()->TestResult{
    let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;let v=raw(&f,&bytes)?;
    let before=f.metadata.audit_events()?.len();let q=Entry::prepare_https_targets_lookup_json(&provider,&wire(&v)?,budget()?)?;
    let pretty=Entry::prepare_https_targets_lookup_json(&provider,&serde_json::to_vec_pretty(&v)?,budget()?)?;
    assert_eq!(q.canonical_request_sha256(),pretty.canonical_request_sha256());assert_eq!(q.scoped_request_sha256(),pretty.scoped_request_sha256());
    for i in 0..8{let mut changed=v.clone();match i{0=>changed["plan_id"]="different-plan".into(),1=>changed["idempotency_key"]="different-key".into(),
        2=>changed["operation"]["changes"][0]["target"]["uri"]="https://example.org/different".into(),3=>changed["operation"]["changes"][0]["expected_meaning_sha256"]="0".repeat(64).into(),
        4=>changed["operation"]["changes"][0]["expected_source_field_sha256"]="0".repeat(64).into(),5=>changed["expected_source_package_sha256"]="1".repeat(64).into(),
        6=>changed["expected_head_generation"]=2.into(),_=>changed["base_revision"]=rev::RevisionId::generate().public_id().into()}
        let other=Entry::prepare_https_targets_lookup_json(&provider,&wire(&changed)?,budget()?)?;assert_ne!(q.canonical_request_sha256(),other.canonical_request_sha256());assert_ne!(q.scoped_request_sha256(),other.scoped_request_sha256());}
    let mut reserved=v.clone();reserved["expected_source_package_sha256"]="0".repeat(64).into();
    assert!(Entry::prepare_https_targets_lookup_json(&provider,&wire(&reserved)?,budget()?).is_err());
    let branch=StoredFormProvider::bind(&f.artifacts,&f.revisions,&c,&f.revision_context,f.project,BranchId::generate(),DocumentId::parse("actual-form-document")?)?;
    let other=Entry::prepare_https_targets_lookup_json(&branch,&wire(&v)?,budget()?)?;assert_eq!(q.canonical_request_sha256(),other.canonical_request_sha256());assert_ne!(q.scoped_request_sha256(),other.scoped_request_sha256());
    assert_eq!(f.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn existing_or_failed_lookup_never_reads_source_policy_compiler_or_claims_a_key()->TestResult{
    for mode in [1,2,3,4,5]{let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
        let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let revisions=rev::RevisionService::new(Model::new(&f,mode));
        let provider=StoredFormProvider::bind(&f.artifacts,&revisions,&c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
        let before=f.metadata.audit_events()?.len();f.blobs.tamper.store(true,Ordering::SeqCst);
        let outcome=Entry::prepare_https_targets_or_observe_json(&provider,&repository,&wire(&raw(&f,&bytes)?)?,budget()?,10);
        if mode==1||mode==4{let HttpsTargetRequestEntry::Existing(job)=outcome?else{return Err("existing observation required".into())};assert_eq!(job.outcome(),StoredJobOutcome::Replay);}
        else{assert!(matches!(outcome,Err(PE::Lookup(_))));}
        assert_eq!(repository.calls.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.heads.load(Ordering::SeqCst),0);
        assert_eq!(revisions.repository().calls.commits.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.lookups.lock().map_err(|_|"rows")?.len(),1);
        assert_eq!(f.metadata.audit_events()?.len(),before);
    }Ok(())
}
#[test]
fn not_observed_prepares_owned_product_once_and_legacy_dispatchers_cannot_bypass_policy_repository()->TestResult{
    let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let p=writable(&f,&c)?;
    let source=p.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;let revisions=rev::RevisionService::new(Model::new(&f,0));
    let provider=StoredFormProvider::bind(&f.artifacts,&revisions,&c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
    let raw=wire(&raw(&f,&bytes)?)?;
    let HttpsTargetRequestEntry::Prepared(prepared)=Entry::prepare_https_targets_or_observe_json(&provider,&repository,&raw,budget()?,10)?else{return Err("preparation required".into())};
    assert!(!prepared.receipt().idempotency_key_claimed);assert_eq!(revisions.repository().calls.lookups.lock().map_err(|_|"rows")?.len(),1);
    assert_eq!(revisions.repository().calls.commits.load(Ordering::SeqCst),0);assert!(revisions.repository().calls.heads.load(Ordering::SeqCst)>0);
    let before=f.metadata.audit_events()?.len();assert!(matches!(Entry::prepare_json(&provider,&raw,None,11),Err(StoredProductOperationError::PolicyRepositoryRequired)));
    assert!(Entry::prepare_compiled_search_json(&provider,&raw,hwpx_agent_cli::form_product_request::stored_operations::search_mutations::SearchMutationLimits::standard()?,11).is_err());
    assert_eq!(f.metadata.audit_events()?.len(),before);Ok(())
}
#[test]
fn same_key_content_conflicts_keep_job_identity_but_not_full_request_binding()->TestResult{
    let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let revisions=rev::RevisionService::new(Model::new(&f,0));
    let provider=StoredFormProvider::bind(&f.artifacts,&revisions,&c,&f.revision_context,f.project,f.branch,DocumentId::parse("actual-form-document")?)?;
    let mut v=raw(&f,&bytes)?;Entry::prepare_https_targets_lookup_json(&provider,&wire(&v)?,budget()?)?.observe(&provider)?;
    v["plan_id"]="same-key-other-plan".into();Entry::prepare_https_targets_lookup_json(&provider,&wire(&v)?,budget()?)?.observe(&provider)?;
    let rows=revisions.repository().calls.lookups.lock().map_err(|_|"rows")?;assert_eq!(rows.len(),2);assert_eq!(rows[0].job_id(),rows[1].job_id());assert_ne!(rows[0],rows[1]);
    assert_eq!(revisions.repository().calls.heads.load(Ordering::SeqCst),0);assert_eq!(revisions.repository().calls.commits.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn owned_public_product_delivery_rechecks_source_policy_and_provider_before_consumption()->TestResult{
    for i in 0..4{let bytes=small()?;let f=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let c=write_context(&f);let provider=writable(&f,&c)?;let read=f.provider()?;
        let source=provider.import_actual_forms(f.head,9)?;let repository=allowed(&f,&source)?;
        let prepared=Entry::prepare_https_targets_json(&provider,&repository,&wire(&raw(&f,&bytes)?)?,budget()?,10)?;
        match i{0=>{f.artifacts.set_permissions(&f.owner,f.result,f.reader.subject(),BTreeSet::new(),11)?;},
            1=>{f.artifacts.set_permissions(&f.owner,repository.row.lock().map_err(|_|"row")?.artifact,f.reader.subject(),BTreeSet::new(),11)?;},
            2=>repository.deny_after.store(0,Ordering::SeqCst),_=>{}}
        let mut consumed=false;assert!(prepared.with_verified_bytes(if i==3{&read}else{&provider},&repository,12,|_|consumed=true).is_err());assert!(!consumed);
    }Ok(())
}
