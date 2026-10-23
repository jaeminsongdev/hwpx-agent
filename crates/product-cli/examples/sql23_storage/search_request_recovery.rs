//! Fresh owned PostgreSQL and real disk AEAD for the common search APIs. Synthetic route/scanner/keys.
use super::*;
use std::cell::Cell;
use hwpx_agent_cli::{form_stored_provider::StoredFormProvider,form_product_request::stored_operations::{StoredProductRequest as Product,
    search_mutations::SearchMutationLimits,compiled_search::request_lookup::{SearchRequestEntry,SearchRequestLookupError}}};
use hwpx_agent_cli::form_stored_provider::actual_import::source_search::request_recovery::{StoredRequestRecoveryObservation,StoredRequestRecoveryError};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookupError;
use domain_ir::{Architecture,BackendHealth,BackendHealthState,BackendId,BackendKind,CapabilityId,CapabilityRouteCatalog,DocumentId,ExactTargetProfile,
    PolicyScope,PreservationImpact,PreservationRequirement,ProtectionState,RegistryTrustState,RouteBinding,RouteContext,SignatureImpact,SupportState,TargetProfileId};
use hwpx_package::document_import::{ImportedSourcePackage,forms::ImportedDocumentForms};
#[path="../../../hwpx-package/tests/support/search_definition_fixture.rs"]mod definition;
const ORIGINALS:[&str;4]=["search-completed-handles.json","retained-receipts.json","public-search-request.json","archived-search-locator.json"];
fn source()->Result<Vec<u8>>{definition::package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>KEEP K END</hp:t></hp:run></hp:p>")}
fn path(name:&str)->Result<PathBuf>{check(ORIGINALS.contains(&name),"SEARCH_SQL_CLOSED_FIXTURE_NAME")?;Ok(owned_root()?.join(name))}
fn save_value(name:&str,row:&Value)->Result<()>{use std::io::Write;let bytes=serde_json::to_vec(row)?;check(!bytes.is_empty()&&bytes.len()<=16384,"SEARCH_SQL_OWNED_FILE_BOUND")?;
    let mut file=fs::OpenOptions::new().write(true).create_new(true).open(path(name)?)?;file.write_all(&bytes)?;file.sync_all()?;Ok(())}
fn regular(p:&std::path::Path)->Result<()>{let m=fs::symlink_metadata(p)?;check(m.is_file()&&!m.file_type().is_symlink()&&m.len()>0&&m.len()<=16384,"SEARCH_SQL_REGULAR_OWNED_FILE")?;
    #[cfg(windows)]{use std::os::windows::fs::MetadataExt;check(m.file_attributes()&0x400==0,"SEARCH_SQL_NO_FILE_REPARSE")?;}Ok(())}
fn load(name:&str)->Result<Value>{let p=path(name)?;regular(&p)?;Ok(serde_json::from_slice(&fs::read(p)?)?)}
fn routes(cap:&str)->Result<(RouteContext,CapabilityRouteCatalog)>{
    let target=ExactTargetProfile::new(TargetProfileId::parse(PROFILE)?,"synthetic-only",Architecture::X86)?;let backend=BackendId::parse("storage-direct")?;
    Ok((RouteContext::new(target.clone(),[9;32],7,RegistryTrustState::SignatureVerified,PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,ProtectionState::Unprotected,10000,vec![BackendHealth::new(backend.clone(),BackendHealthState::Healthy,3,9000,10000)])?,
        CapabilityRouteCatalog::from_bindings(vec![RouteBinding::new(CapabilityId::parse(cap)?,backend,BackendKind::DirectHwpx,SupportState::Verified,target,[9;32],7,10,10,
            PreservationImpact::Exact,SignatureImpact::Preserved)])?))
}
fn verify_text(bytes:&[u8])->Result<()>{
    let parsed=ImportedSourcePackage::import(bytes,DocumentId::parse("actual-form-document")?,*ContentDigest::of(bytes).as_bytes(),Default::default())?;
    let _forms=ImportedDocumentForms::import(parsed)?;
    let mut zip=hwpx_package::BoundedZipReader::open(std::io::Cursor::new(bytes),Default::default())?;
    let i=zip.entries().iter().position(|p|p.path.as_str()=="Contents/section0.xml").ok_or("SEARCH_SQL_SECTION_REQUIRED")?;
    check(String::from_utf8(zip.read_entry(i)?)?.contains("KEEP k END"),"SEARCH_SQL_EXACT_CASE_OUTPUT")
}
fn seed()->Result<Value>{
    let cfg=LocalPostgresRevisionConfig::new(port()?,"postgres".into(),"p09_revision_284".into(),value("P09_SQL23_REVISION_PASSWORD")?)?;
    check(matches!(LocalPostgresStoredRevisionJobsRepository::connect(&cfg,context()?,None),Err(revision_service::RevisionError::InvalidRequest)),"SEARCH_SQL_LEGACY23_DENIES24")?;
    let mut row=setup::seed_source(&source()?)?;row["legacy23_constructors_reject24"]=json!(true);Ok(row)
}
fn execute()->Result<Value>{
    let s=state()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let bytes=a.download(&ctx,read_id(&s,"source")?,10)?;
    check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(20)?),1)?,"SEARCH_SQL_FRESH_SOURCE_HEAD")?;
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let request=json!({"schema_version":"hwpx-agent.product-case-conversion-request/v1","idempotency_key":"owned-search-sql-516-only","plan_id":"owned-search-sql-plan",
        "project_id":project()?.public_id(),"document_id":"actual-form-document","base_revision":revision(20)?.public_id(),"expected_head_generation":1,
        "expected_source_package_sha256":ContentDigest::of(&bytes).hex(),"selector":{"scope":"document","revision_id":revision(20)?.public_id()},
        "operation":{"kind":"convert_case_matches","query":"K","regex":false,"case_sensitive":true,"whole_word":true,"max_matches":1,"mode":"lowercase",
            "case_policy":"unicode_default_each_matched_text_group","review_policy":{"include_hidden_explanations":false,"include_memo_bodies":false}}});
    save_value("public-search-request.json",&request)?;let wire=serde_json::to_vec(&request)?;
    let SearchRequestEntry::Prepared(compiled)=Product::prepare_search_or_observe_json(&provider,&wire,SearchMutationLimits::standard()?,10)?else{return Err("SEARCH_SQL_UNOBSERVED_PREPARATION_REQUIRED".into())};
    let cap=compiled.receipt().capability_id;let(c,r)=routes(cap)?;let prepared=compiled.prepare_execution_manifest(&provider,&c,&r,domain_ir::TransactionId::parse("search-sql-516")?,10)?;
    check(prepared.require_current_product_route(&provider,&c,&r,10).is_err(),"SEARCH_SQL_ROUTE_MUST_REMAIN_UNQUALIFIED")?;
    let checks=Cell::new(0);
    prepared.with_verified_storage_preparation(&provider,&c,&r,10,|input|->Result<Value>{
        check(input.source_bytes()==bytes&&input.output_bytes()!=bytes,"SEARCH_SQL_ACTUAL_SOURCE_OWNED_OUTPUT")?;verify_text(input.output_bytes())?;
        let mut job=input.prepare_bound_job(identity::StoredJobPolicy{max_delay_seconds:4,..Default::default()},commit(201)?,revision(200)?,Default::default())?;
        let claim=job.claim().clone();let(key,job_id)=(claim.input().key,claim.input().job);
        check((key,job_id,claim.input().request)==(input.job_identity().key(),input.job_identity().job(),input.job_identity().request()),"SEARCH_SQL_STRICT_KEY_DERIVED_JOB_IDS")?;
        job.require_precommit_guard(Box::new(prepared.current_commit_guard(&provider,||{checks.set(checks.get()+1);let(c,r)=routes(cap).map_err(|_|())?;Ok((c,r,10))})))?;
        let mut client=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD")?)?;scoped(&mut client)?;setup::register(&mut client,130,job.claim().input().capability_sha)?;
        let mut validator=input.output_validator();let report=job.run_once(&a,&revisions,&ctx,&rc,id(130),id(120),120,ContentDigest::of(b"owned-search-storage-event"),
            &owned_root()?.join("search-workspace"),input.source_bytes(),&mut validator,||10);
        if report.stage!=StoredJobRunStage::Completed{return Ok(json!({"state":"FAILED_SEARCH_ACTUAL_SQL_COORDINATOR","stage":format!("{:?}",report.stage),
            "repository_error":report.repository_error.as_ref().map(revision_service::RevisionError::code),"binding_error":report.binding_error.map(|e|format!("{e:?}")),
            "cas_error":report.cas_error.map(|e|format!("{e:?}")),"guard_checks":checks.get(),"result_retained":report.result.is_some(),"intent_retained":report.intent.is_some()}));}
        check(checks.get()==3&&report.repository_error.is_none()&&report.cas_error.is_none()&&report.completion.is_some(),"SEARCH_SQL_THREE_CURRENT_GUARDS_AND_COMPLETION")?;
        let result=report.result.as_ref().ok_or("SEARCH_SQL_RESULT_REQUIRED")?;let intent=report.intent.as_ref().ok_or("SEARCH_SQL_INTENT_REQUIRED")?;
        let precommit=report.precommit.as_ref().ok_or("SEARCH_SQL_PRECOMMIT_REQUIRED")?;let registered=report.registered_intent.as_ref().ok_or("SEARCH_SQL_REGISTRATION_REQUIRED")?;
        check(a.download(&ctx,result.artifact_id,11)?==input.output_bytes()&&a.download(&ctx,read_id(&s,"source")?,11)?==bytes,"SEARCH_SQL_SOURCE_AND_RESULT_AEAD")?;
        check(registered.intent_artifact_id()==intent.artifact_id&&registered.precommit_artifact_id()==precommit.artifact_id
            &&revisions.repository().read_commit_intent(&rc,StoredCommitIntentLookup::new(project()?,key,job_id,1)?)?.as_ref()==Some(registered),"SEARCH_SQL_REGISTERED_ROW_MATCH")?;
        check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(200)?),2)?,"SEARCH_SQL_EXACT_NEW_HEAD")?;
        save_value("search-completed-handles.json",&json!({"result":result.artifact_id.public_id(),"intent":intent.artifact_id.public_id(),"precommit":precommit.artifact_id.public_id(),
            "output_sha256":result.sha256.hex(),"source_sha256":ContentDigest::of(&bytes).hex()}))?;
        save_value("archived-search-locator.json",&json!({"project":project()?.public_id(),"key":key,"job":job_id,"attempt":1}))?;
        Ok(json!({"state":"PASS_COMMON_SEARCH_HWPX_REAL_SQL24_REGISTERED_JOB_AND_CAS_NOT_PRODUCT","guard_checks":checks.get(),"actual_staged_hwpx_validator":true,
            "source_preserved":true,"one_product_job_attempt":true,"route_unqualified":true,"synthetic_route_and_scanner":true}))
    })?
}
fn cold()->Result<Value>{
    let wire=serde_json::to_vec(&load("public-search-request.json")?)?;let root=owned_root()?;let mut moved=Vec::new();
    let outcome=(||->Result<Value>{
        for name in ORIGINALS {let original=path(name)?;let preserved=root.join(format!("{name}.preserved-for-public-search"));
            check(original.parent()==Some(root.as_path())&&preserved.parent()==Some(root.as_path())&&!preserved.exists(),"SEARCH_SQL_EXACT_PRESERVE_SCOPE")?;
            regular(&original)?;let digest=ContentDigest::of(&fs::read(&original)?);fs::rename(&original,&preserved)?;moved.push((original,preserved,digest));}
        check(ORIGINALS.iter().all(|n|!root.join(n).exists()),"SEARCH_SQL_NO_SAVED_FILES_AT_ORIGINAL_PATHS")?;
        let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
        let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
        let entry=Product::prepare_search_or_observe_json(&provider,&wire,SearchMutationLimits::standard()?,20)?;
        check(matches!(entry,SearchRequestEntry::Existing(ref job)if job.state()==StoredJobState::TerminalSuccess&&job.attempt_no()==1),"SEARCH_SQL_EXISTING_WITHOUT_PREPARATION")?;
        let lookup=Product::prepare_search_lookup_json(&provider,&wire)?;
        let StoredRequestRecoveryObservation::Existing{job,effect:ArchivedRegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{receipt,result:RecoveredResult::VerifiedAvailable(result)})}=lookup.recover_registered(&provider,||20)?
            else{return Err("SEARCH_SQL_COMMITTED_RECOVERY_REQUIRED".into())};
        check(job.outcome()==StoredJobOutcome::Replay&&job.result_revision_id()==Some(revision(200)?)&&job.attempt_no()==1
            &&receipt.committed_head()==RevisionHead::new(Some(revision(200)?),2)?,"SEARCH_SQL_SAME_JOB_ATTEMPT_AND_SEALED_HEAD")?;
        verify_text(&a.download(&ctx,result.artifact_id,20)?)?;
        let mut changed:Value=serde_json::from_slice(&wire)?;changed["plan_id"]=json!("different-search-plan");
        let changed=Product::prepare_search_lookup_json(&provider,&serde_json::to_vec(&changed)?)?;
        check(matches!(changed.recover_registered(&provider,||20),Err(SearchRequestLookupError::Recovery(StoredRequestRecoveryError::Lookup(StoredRequestLookupError::KeyConflict)))),"SEARCH_SQL_TYPED_CHANGED_REQUEST_CONFLICT")?;
        let mut missing:Value=serde_json::from_slice(&wire)?;missing["idempotency_key"]=json!("missing-search-sql-fixture");
        check(Product::prepare_search_lookup_json(&provider,&serde_json::to_vec(&missing)?)?.recover_registered(&provider,||20)?==StoredRequestRecoveryObservation::NotObserved,"SEARCH_SQL_MISSING_IS_NOT_OBSERVED")?;
        Ok(json!({"state":"PASS_COMMON_PUBLIC_SEARCH_REQUEST_TO_SQL24_COMMITTED_EFFECT_WITHOUT_MANIFEST_OR_LOCATOR","original_paths_absent":4,
            "same_job_attempt_and_result_revision":true,"typed_changed_request_conflict":true,"missing_request_is_not_observed":true,"actual_hwpx_and_AEAD_readback":true,
            "engine_claim_lease_CAS_job_transition_or_retry_executed":false,"only_original_public_request_supplied":true}))
    })();
    let mut restored=true;
    for(original,preserved,digest)in moved.into_iter().rev(){let result=(||->Result<()>{
        check(original.parent()==Some(root.as_path())&&preserved.parent()==Some(root.as_path())&&!original.exists(),"SEARCH_SQL_EXACT_RESTORE_SCOPE")?;
        regular(&preserved)?;fs::rename(&preserved,&original)?;check(ContentDigest::of(&fs::read(original)?)==digest,"SEARCH_SQL_RESTORED_EXACT_BYTES")?;Ok(())})();if result.is_err(){restored=false;}}
    check(restored,"SEARCH_SQL_RESTORE_FAILED_PRESERVED_FILES_RETAINED")?;let mut result=outcome?;result["all_original_files_restored_byte_exact"]=json!(true);Ok(result)
}
pub(super) fn run(mode:&str)->Result<Value>{owned_root()?;match mode {
    "--fixture"=>lookup24::run(mode),"--seed"=>seed(),"--execute"=>execute(),"--cold-recover"=>cold(),
    "--restart-registered"=>{let mut row=cold()?;row["execution_retried"]=json!(false);Ok(row)},
    "--wrong-key"=>{let handles=load("search-completed-handles.json")?;
        check(matches!(artifacts()?.download(&actor()?,read_id(&handles,"result")?,20),Err(ArtifactError::CryptoFailure)),"SEARCH_SQL_WRONG_AES_KEY_REJECTED")?;
        Ok(json!({"state":"PASS_SEARCH_REAL_DISK_WRONG_KEY_REJECTED","raw_values":false}))},_=>Err("SEARCH_SQL_CLOSED_MODE".into())}}
