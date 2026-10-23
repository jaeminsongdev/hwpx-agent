//! Cold request observation + original preparation, synthetic repository only; no operational SQL or Native.
use super::*;
use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::request_lookup::{SearchRequestEntry as Entry,SearchRequestEntryError as EE,SearchRequestLookupError as LE};
use hwpx_agent_cli::form_stored_provider::actual_import::source_search::request_recovery::{StoredRequestRecoveryObservation as Recovery,StoredRequestRecoveryError as RE};
use hwpx_agent_cli::stored_revision_commit::ArchivedRegisteredStoredCommitRecoveryOutcome as Archived;
use revision_service::{RevisionRepository,postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{
    StoredRevisionJobRepository,StoredCommitRegistration,StoredCommitIntentRecord,StoredCommitIntentLookup,
    request_lookup::{StoredRequestLookup,StoredRequestLookupRepository,StoredRequestLookupError,StoredRequestObservation},
    lifecycle::{StoredJobObservation,StoredJobState,StoredJobOutcome}}};
use std::sync::{Arc,Mutex};

struct Counters {heads:AtomicUsize,commits:AtomicUsize,intents:AtomicUsize,writes:AtomicUsize,queries:Mutex<Vec<StoredRequestLookup>>}
#[derive(Clone)]struct Model {inner:rev::InMemoryRevisionRepository,mode:Arc<AtomicUsize>,calls:Arc<Counters>}
impl Model {fn new(s:&StoredFixture,mode:usize)->Self {Self {inner:s.revisions.repository().clone(),mode:Arc::new(AtomicUsize::new(mode)),calls:Arc::new(Counters {
    heads:AtomicUsize::new(0),commits:AtomicUsize::new(0),intents:AtomicUsize::new(0),writes:AtomicUsize::new(0),queries:Mutex::new(Vec::new())})}}}
impl RevisionRepository for Model {
    fn authorize_context(&self,c:&rev::RevisionRequestContext)->Result<(),rev::RevisionError>{self.inner.authorize_context(c)}
    fn head(&self,t:TenantId,p:rev::ProjectId,b:rev::BranchId)->Result<rev::RevisionHead,rev::RevisionError>{
        self.calls.heads.fetch_add(1,Ordering::SeqCst);if self.mode.load(Ordering::SeqCst)!=0{return Err(rev::RevisionError::RepositoryFailure);}self.inner.head(t,p,b)
    }
    fn node(&self,t:TenantId,p:rev::ProjectId,r:rev::RevisionId)->Result<rev::RevisionNode,rev::RevisionError>{
        self.calls.heads.fetch_add(1,Ordering::SeqCst);if self.mode.load(Ordering::SeqCst)!=0{return Err(rev::RevisionError::RepositoryFailure);}self.inner.node(t,p,r)
    }
    fn compare_and_swap(&self,c:&rev::RevisionRequestContext,r:&rev::RevisionCommitRequest)->Result<rev::CommitOutcome,rev::RevisionError>{
        self.calls.commits.fetch_add(1,Ordering::SeqCst);self.inner.compare_and_swap(c,r)
    }
}
impl StoredRequestLookupRepository for Model {
    fn observe_request(&self,c:&rev::RevisionRequestContext,q:&StoredRequestLookup)->Result<StoredRequestObservation,StoredRequestLookupError> {
        self.authorize_context(c)?;let mut queries=self.calls.queries.lock().map_err(|_|rev::RevisionError::RepositoryFailure)?;queries.push(q.clone());let n=queries.len();
        let mode=self.mode.load(Ordering::SeqCst);
        match mode {
            0=>Ok(StoredRequestObservation::NotObserved),2=>Err(StoredRequestLookupError::KeyConflict),3=>Err(rev::RevisionError::CommitOutcomeUnknown.into()),
            5=>Err(rev::RevisionError::RepositoryFailure.into()),8 if n==2=>Ok(StoredRequestObservation::NotObserved),
            9 if n==2=>Err(rev::RevisionError::InvalidRequest.into()),_=>{
                let initial=mode==6;let success=mode==1;
                Ok(StoredRequestObservation::Existing(StoredJobObservation::observed(StoredJobOutcome::Replay,
                    if mode==7{uuid::Uuid::from_u128(777)}else{q.job_id()},if initial{StoredJobState::Claimed}else if success{StoredJobState::TerminalSuccess}else{StoredJobState::InProgress},
                    if initial{0}else{1},if initial{0}else{1},None,
                    if success{Some(rev::RevisionId::parse("rev_00000000000000000000000000000901")?)}else{None},None,
                    if success{Some(artifact_service::ArtifactId::parse("art_00000000000000000000000000000771").map_err(|_|rev::RevisionError::InvalidRequest)?)}else{None})?))
            }
        }
    }
}
impl StoredRevisionJobRepository for Model {
    fn register_commit_intent(&self,_:&rev::RevisionRequestContext,_:&StoredCommitRegistration)->Result<StoredCommitIntentRecord,rev::RevisionError>{
        self.calls.writes.fetch_add(1,Ordering::SeqCst);Err(rev::RevisionError::InvalidRequest)
    }
    fn read_commit_intent(&self,c:&rev::RevisionRequestContext,l:StoredCommitIntentLookup)->Result<Option<StoredCommitIntentRecord>,rev::RevisionError>{
        self.authorize_context(c)?;self.calls.intents.fetch_add(1,Ordering::SeqCst);
        let queries=self.calls.queries.lock().map_err(|_|rev::RevisionError::RepositoryFailure)?;let q=queries.first().ok_or(rev::RevisionError::InvalidRequest)?;
        if l.project_id()!=q.project_id()||l.job_id()!=q.job_id()||l.idempotency_key()!=q.idempotency_key()||l.attempt_no()!=1{return Err(rev::RevisionError::InvalidRequest);}
        if self.mode.load(Ordering::SeqCst)==10{return Err(rev::RevisionError::CommitOutcomeUnknown);}Ok(None)
    }
}
macro_rules! provider {($s:ident,$repo:ident,$actor:ident,$p:ident)=>{
    let $actor=RequestContext::new($s.reader.tenant_id(),$s.reader.subject(),[AuthScope::DocumentRead,AuthScope::DocumentWrite]);
    let $p=StoredFormProvider::bind(&$s.artifacts,&$repo,&$actor,&$s.revision_context,$s.project,$s.branch,DocumentId::parse("actual-form-document")?)?;
}}
fn unchanged(c:&Counters,heads:usize,intents:usize)->TestResult {
    assert_eq!(c.heads.load(Ordering::SeqCst),heads);assert_eq!(c.intents.load(Ordering::SeqCst),intents);
    assert_eq!(c.commits.load(Ordering::SeqCst),0);assert_eq!(c.writes.load(Ordering::SeqCst),0);Ok(())
}
fn exercise_family(i:usize)->TestResult {
    assert_eq!(SCHEMAS.len(),23);let bytes=cases::source(i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
    let model=Model::new(&s,1);let repo=rev::RevisionService::new(model.clone());provider!(s,repo,actor,p);
    let request=cases::request(i,&s,&bytes)?;let raw=wire(&request)?;let before=s.metadata.audit_events()?.len();s.blobs.tamper.store(true,Ordering::SeqCst);
    let initial=Dispatch::prepare_search_lookup_json(&p,&raw)?;
    let entry=Dispatch::prepare_search_or_observe_json(&p,&raw,Limits::standard()?,4)?;
    let Entry::Existing(job)=&entry else{return Err("cold existing entry".into())};assert_eq!(job.state(),StoredJobState::TerminalSuccess);
    assert_eq!(format!("{entry:?}"),"SearchRequestEntry::Existing(<redacted>; observation_not_authority)");
    unchanged(&model.calls,0,0)?;assert_eq!(s.metadata.audit_events()?.len(),before);
    s.blobs.tamper.store(false,Ordering::SeqCst);model.mode.store(0,Ordering::SeqCst);
    let Entry::Prepared(compiled)=Dispatch::prepare_search_or_observe_json(&p,&raw,Limits::standard()?,4)? else{return Err("new preparation".into())};
    assert_eq!(compiled.receipt().request_schema,SCHEMAS[i]);assert!(compiled.require_current_product_route(&p,5).is_err());
    let receipt=compiled.receipt().clone();let(c,r)=routing(receipt.capability_id,6,0)?;
    assert_eq!(initial.canonical_request_sha256(),*ContentDigest::parse(&receipt.canonical_request_sha256)?.as_bytes());
    assert_eq!(initial.scoped_request_sha256(),*ContentDigest::parse(&receipt.scoped_request_sha256)?.as_bytes());
    let manifest=compiled.prepare_execution_manifest(&p,&c,&r,TransactionId::parse("lookup-binding")?,6)?;
    let id=manifest.with_verified_storage_preparation(&p,&c,&r,6,|input|input.job_identity().clone())?;
    let expected=StoredRequestLookup::new(s.project,s.branch,id.key(),id.job(),id.request(),ContentDigest::parse(&receipt.canonical_request_sha256)?,ContentDigest::of(&bytes),s.head)?;
    let queries=model.calls.queries.lock().map_err(|_|"queries")?;assert_eq!(queries.len(),2);assert_eq!(queries[0],expected);assert_eq!(queries[1],expected);drop(queries);
    let heads=model.calls.heads.load(Ordering::SeqCst);assert!(heads>0);model.mode.store(4,Ordering::SeqCst);s.blobs.tamper.store(true,Ordering::SeqCst);
    let pretty=serde_json::to_vec_pretty(&request)?;let prepared=Dispatch::prepare_search_lookup_json(&p,&pretty)?;
    assert!(matches!(prepared.observe(&p)?,StoredRequestObservation::Existing(job)if job.state()==StoredJobState::InProgress));
    assert_eq!(model.calls.queries.lock().map_err(|_|"queries")?[2],expected);unchanged(&model.calls,heads,0)?;Ok(())
}
#[test]fn family_00_literal()->TestResult {exercise_family(0)}
#[test]fn family_01_atoms()->TestResult {exercise_family(1)}
#[test]fn family_02_review()->TestResult {exercise_family(2)}
#[test]fn family_03_selector()->TestResult {exercise_family(3)}
#[test]fn family_04_regex()->TestResult {exercise_family(4)}
#[test]fn family_05_insertion()->TestResult {exercise_family(5)}
#[test]fn family_06_character()->TestResult {exercise_family(6)}
#[test]fn family_07_text_style()->TestResult {exercise_family(7)}
#[test]fn family_08_paragraph()->TestResult {exercise_family(8)}
#[test]fn family_09_unicode_scope()->TestResult {exercise_family(9)}
#[test]fn family_10_unicode_match()->TestResult {exercise_family(10)}
#[test]fn family_11_case()->TestResult {exercise_family(11)}
#[test]fn family_12_width()->TestResult {exercise_family(12)}
#[test]fn family_13_whitespace()->TestResult {exercise_family(13)}
#[test]fn family_14_text_control()->TestResult {exercise_family(14)}
#[test]fn family_15_number_control()->TestResult {exercise_family(15)}
#[test]fn family_16_sort()->TestResult {exercise_family(16)}
#[test]fn family_17_sort_groups()->TestResult {exercise_family(17)}
#[test]fn family_18_fonts()->TestResult {exercise_family(18)}
#[test]fn family_19_font_options()->TestResult {exercise_family(19)}
#[test]fn family_20_named_styles()->TestResult {exercise_family(20)}
#[test]fn family_21_named_options()->TestResult {exercise_family(21)}
#[test]fn family_22_personal_mask()->TestResult {exercise_family(22)}
#[test]
fn every_schema_keeps_strict_unknown_duplicate_and_preview_rejection_before_observation()->TestResult {
    for i in 0..SCHEMAS.len(){let bytes=cases::source(i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
        let model=Model::new(&s,1);let repo=rev::RevisionService::new(model.clone());provider!(s,repo,actor,p);
        let value=cases::request(i,&s,&bytes)?;let mut unknown=value.clone();unknown["operation"]["permit"]=json!(true);
        let text=serde_json::to_string(&value)?;let duplicate=text.replace("\"idempotency_key\":","\"idempotency_key\":\"DIFFERENT\",\"idempotency_ke\\u0079\":");assert_ne!(text,duplicate);
        for raw in[wire(&unknown)?,duplicate.into_bytes(),vec![b' ';16385]] {assert!(Dispatch::prepare_search_lookup_json(&p,&raw).is_err());}
        if i>=19{let mut preview=value;preview["operation"]["preview_only"]=json!(true);assert!(Dispatch::prepare_search_lookup_json(&p,&wire(&preview)?).is_err());}
        assert!(model.calls.queries.lock().map_err(|_|"queries")?.is_empty());unchanged(&model.calls,0,0)?;
    }Ok(())
}
#[test]
fn lookup_conflict_uncertainty_and_unavailable_never_prepare_or_read_source()->TestResult {
    for i in[0,5,19] {for mode in[2,3,5] {let bytes=cases::source(i)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;
        let model=Model::new(&s,mode);let repo=rev::RevisionService::new(model.clone());provider!(s,repo,actor,p);s.blobs.tamper.store(true,Ordering::SeqCst);
        let error=Dispatch::prepare_search_or_observe_json(&p,&wire(&cases::request(i,&s,&bytes)?)?,Limits::standard()?,4).expect_err("lookup must stop");
        match mode{2=>assert!(matches!(error,EE::Lookup(LE::Repository(StoredRequestLookupError::KeyConflict)))),
            3=>assert!(matches!(error,EE::Lookup(LE::Repository(StoredRequestLookupError::Repository(rev::RevisionError::CommitOutcomeUnknown))))),
            _=>assert!(matches!(error,EE::Lookup(LE::Repository(StoredRequestLookupError::Repository(rev::RevisionError::RepositoryFailure)))))}
        assert_eq!(model.calls.queries.lock().map_err(|_|"queries")?.len(),1);unchanged(&model.calls,0,0)?;
    }}Ok(())
}
#[test]
fn unobserved_request_does_not_hide_current_source_aead_failure()->TestResult {
    let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let model=Model::new(&s,0);let repo=rev::RevisionService::new(model.clone());provider!(s,repo,actor,p);
    s.blobs.tamper.store(true,Ordering::SeqCst);
    assert!(matches!(Dispatch::prepare_search_or_observe_json(&p,&wire(&cases::request(0,&s,&bytes)?)?,Limits::standard()?,4),Err(EE::Preparation(_))));
    assert_eq!(model.calls.queries.lock().map_err(|_|"queries")?.len(),1);assert_eq!(model.calls.commits.load(Ordering::SeqCst),0);Ok(())
}
#[test]
fn existing_lookup_still_requires_current_write_and_exact_provider_scope()->TestResult {
    let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let model=Model::new(&s,1);let repo=rev::RevisionService::new(model.clone());provider!(s,repo,actor,p);
    let raw=wire(&cases::request(0,&s,&bytes)?)?;let lookup=Dispatch::prepare_search_lookup_json(&p,&raw)?;
    let reader=StoredFormProvider::bind(&s.artifacts,&repo,&s.reader,&s.revision_context,s.project,s.branch,DocumentId::parse("actual-form-document")?)?;
    assert!(lookup.observe(&reader).is_err());assert!(Dispatch::prepare_search_lookup_json(&reader,&raw).is_err());
    let mut wrong=cases::request(0,&s,&bytes)?;wrong["document_id"]=json!("other-document");assert!(Dispatch::prepare_search_lookup_json(&p,&wire(&wrong)?).is_err());
    assert!(model.calls.queries.lock().map_err(|_|"queries")?.is_empty());unchanged(&model.calls,0,0)
}
#[test]
fn missing_or_unstarted_recovery_never_reads_intent_or_starts_a_job()->TestResult {
    for mode in[0,6]{let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let model=Model::new(&s,mode);let repo=rev::RevisionService::new(model.clone());provider!(s,repo,actor,p);
        let lookup=Dispatch::prepare_search_lookup_json(&p,&wire(&cases::request(0,&s,&bytes)?)?)?;let result=lookup.recover_registered(&p,||20)?;
        if mode==0{assert!(matches!(result,Recovery::NotObserved));}else{assert!(matches!(result,Recovery::AttemptNotStarted(_)));}
        assert_eq!(model.calls.queries.lock().map_err(|_|"queries")?.len(),1);unchanged(&model.calls,0,0)?;
    }Ok(())
}
#[test]
fn recovery_derives_exact_registered_locator_and_does_not_promote_missing_effect()->TestResult {
    for mode in[1,4]{let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let model=Model::new(&s,mode);let repo=rev::RevisionService::new(model.clone());provider!(s,repo,actor,p);
        let lookup=Dispatch::prepare_search_lookup_json(&p,&wire(&cases::request(0,&s,&bytes)?)?)?;
        assert!(matches!(lookup.recover_registered(&p,||20)?,Recovery::Existing{effect:Archived::RegistrationNotObserved,..}));
        assert_eq!(model.calls.queries.lock().map_err(|_|"queries")?.len(),2);unchanged(&model.calls,0,1)?;
    }Ok(())
}
#[test]
fn foreign_job_changed_observation_and_uncertain_intent_never_retry_or_write()->TestResult {
    for mode in[7,8,9,10]{let bytes=cases::source(0)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;let model=Model::new(&s,mode);let repo=rev::RevisionService::new(model.clone());provider!(s,repo,actor,p);
        let lookup=Dispatch::prepare_search_lookup_json(&p,&wire(&cases::request(0,&s,&bytes)?)?)?;let result=lookup.recover_registered(&p,||20);
        match mode{7=>assert!(matches!(result,Err(LE::Recovery(RE::Binding)))),8=>assert!(matches!(result,Err(LE::Recovery(RE::ObservationChanged)))),
            9=>assert!(matches!(result,Err(LE::Recovery(RE::Lookup(_))))),_=>assert!(matches!(result,Err(LE::Recovery(RE::Recovery(_)))))}
        unchanged(&model.calls,0,if mode==7{0}else{1})?;
    }Ok(())
}
