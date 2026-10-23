//! Actual storage transport and retained HWPX validator; no public product route or Native authorization.
use super::*;
use std::cell::Cell;
use domain_ir::{Architecture,BackendHealth,BackendHealthState,BackendId,BackendKind,CapabilityId,CapabilityRouteCatalog,
    DocumentId,ExactTargetProfile,PolicyScope,PreservationImpact,PreservationRequirement,ProtectionState,
    RegistryTrustState,RouteBinding,RouteContext,SignatureImpact,SupportState,TargetProfileId,TransactionId};
use hwpx_agent_cli::{form_stored_provider::{StoredFormProvider,actual_import::source_search::personal_info_catalog::{CurrentPersonalInfoCatalogSource,InstalledPersonalInfoCatalogSource}},
    form_product_request::{stored_operations::{StoredProductRequest,search_mutations::SearchMutationLimits},
        stored_literal_replacement::personal_info::catalog::PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA}};
use hwpx_package::document_import::{ImportedSourcePackage,SourceImportLimits,forms::ImportedDocumentForms,structure::review::ImportedDocumentReviewBodies};
#[path="../../../hwpx-package/tests/support/search_definition_fixture.rs"]#[allow(dead_code)]mod definition;
fn routes()->Result<(RouteContext,CapabilityRouteCatalog)>{
    let target=ExactTargetProfile::new(TargetProfileId::parse(PROFILE)?,"synthetic-only",Architecture::X86)?;let backend=BackendId::parse("storage-direct")?;
    Ok((RouteContext::new(target.clone(),[9;32],7,RegistryTrustState::SignatureVerified,PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,ProtectionState::Unprotected,10000,vec![BackendHealth::new(backend.clone(),BackendHealthState::Healthy,3,9000,10000)])?,
        CapabilityRouteCatalog::from_bindings(vec![RouteBinding::new(CapabilityId::parse("search.personal_info_find_replace")?,backend,BackendKind::DirectHwpx,
            SupportState::Verified,target,[9;32],7,10,10,PreservationImpact::Exact,SignatureImpact::Preserved)])?))
}
fn handles_path()->Result<PathBuf>{Ok(owned_root()?.join("catalog-completed-handles.json"))}
fn handles()->Result<Value>{let p=handles_path()?;let m=fs::symlink_metadata(&p)?;check(m.is_file()&&!m.file_type().is_symlink()&&m.len()<=16384,"CATALOG_HANDLES_BOUND")?;Ok(serde_json::from_slice(&fs::read(p)?)?)}
fn save_handles(v:&Value)->Result<()>{use std::io::Write;let bytes=serde_json::to_vec(v)?;check(bytes.len()<=16384,"CATALOG_HANDLES_BOUND")?;
    let mut file=fs::OpenOptions::new().write(true).create_new(true).open(handles_path()?)?;file.write_all(&bytes)?;file.sync_all()?;Ok(())}
fn source()->Result<Vec<u8>>{definition::package("<hp:p id='1' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>KEEP 010-1234-5678 END</hp:t></hp:run></hp:p>")}
fn execute()->Result<Value>{
    let s=state()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let bytes=a.download(&ctx,read_id(&s,"source")?,10)?;let head=revisions.head(&rc,project()?,branch()?)?;
    check(head==RevisionHead::new(Some(revision(20)?),1)?,"CATALOG_INITIAL_HEAD")?;
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let formats=InstalledPersonalInfoCatalogSource;let raw_catalog=formats.read_current_catalog()?;
    check(raw_catalog.len()==17020&&ContentDigest::of(&raw_catalog).hex()=="fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434","CATALOG_FIXED_INSTALLED_INPUT")?;
    let wire=serde_json::to_vec(&json!({"schema_version":PERSONAL_INFO_CATALOG_MASK_PRODUCT_SCHEMA,"idempotency_key":"catalog-sql-fixture-only","plan_id":"catalog-sql-plan",
        "project_id":project()?.public_id(),"document_id":"actual-form-document","base_revision":revision(20)?.public_id(),"expected_head_generation":1,
        "expected_source_package_sha256":ContentDigest::of(&bytes).hex(),"expected_catalog_sha256":ContentDigest::of(&raw_catalog).hex(),
        "selector":{"scope":"document","revision_id":revision(20)?.public_id()},
        "operation":{"kind":"mask_personal_info_catalog","families":["telephone"],"mask_policy":"per_original_scalar_preserve_slots","max_matches":10000,"max_changed_components":10000,
            "review_policy":{"include_hidden_explanations":false,"include_memo_bodies":false},"preview_only":false}}))?;
    let compiled=StoredProductRequest::prepare_compiled_catalog_mask_json(&provider,&formats,&wire,SearchMutationLimits::standard()?,10)?;
    let(c,r)=routes()?;let prepared=compiled.prepare_execution_manifest(&provider,&formats,&c,&r,TransactionId::parse("catalog-sql-transaction")?,10)?;
    let checks=Cell::new(0);
    prepared.with_verified_storage_preparation(&provider,&formats,&c,&r,10,|input|->Result<Value>{
        check(input.source_bytes()==bytes&&input.output_bytes()!=bytes,"CATALOG_ORIGINAL_CANDIDATE")?;
        let bound=IDENTITY_MODE.load(std::sync::atomic::Ordering::Relaxed);
        let mut job=if bound{input.prepare_bound_job(identity::StoredJobPolicy{max_delay_seconds:4,..Default::default()},commit(201)?,revision(200)?,Default::default())?}
            else{input.prepare_job(StoredJobOptions{key:id(101),job:id(102),request:id(103),request_sha:ContentDigest::parse(&prepared.compiled_receipt().canonical_request_sha256)?,
            capability_sha:ContentDigest::parse(&hex::encode(input.manifest().route_set_sha256()))?,max_attempts:3,base_delay_seconds:1,max_delay_seconds:4,ttl_seconds:600},commit(201)?,revision(200)?,Default::default())?};
        let original_claim=job.claim().clone();let(key,job_id)=(original_claim.input().key,original_claim.input().job);
        job.require_precommit_guard(Box::new(prepared.current_commit_guard(&provider,&formats,||{checks.set(checks.get()+1);let(c,r)=routes().map_err(|_|())?;Ok((c,r,10))})))?;
        let mut client=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD")?)?;scoped(&mut client)?;
        setup::register(&mut client,130,job.claim().input().capability_sha)?;
        let mut validator=input.output_validator();let report=job.run_once(&a,&revisions,&ctx,&rc,id(130),id(120),120,ContentDigest::of(b"catalog-storage-event"),
            &owned_root()?.join("catalog-workspace"),input.source_bytes(),&mut validator,||10);
        if report.stage!=StoredJobRunStage::Completed{return Ok(json!({"state":"FAILED_CATALOG_ACTUAL_SQL_COORDINATOR","stage":format!("{:?}",report.stage),
            "repository_error":report.repository_error.as_ref().map(revision_service::RevisionError::code),"binding_error":report.binding_error.map(|e|format!("{e:?}")),
            "cas_error":report.cas_error.map(|e|format!("{e:?}")),"guard_checks":checks.get(),"result_retained":report.result.is_some(),"intent_retained":report.intent.is_some()}));}
        check(checks.get()==3&&report.repository_error.is_none()&&report.cas_error.is_none()&&report.completion.is_some(),"CATALOG_THREE_CURRENT_CHECKS_AND_COMPLETION")?;
        let result=report.result.as_ref().ok_or("CATALOG_NO_RESULT")?;let intent=report.intent.as_ref().ok_or("CATALOG_NO_INTENT")?;let precommit=report.precommit.as_ref().ok_or("CATALOG_NO_PRECOMMIT")?;
        let registered=report.registered_intent.as_ref().ok_or("CATALOG_NO_REGISTERED")?;let request=report.request.as_ref().ok_or("CATALOG_NO_REQUEST")?;
        check(a.download(&ctx,result.artifact_id,11)?==input.output_bytes()&&a.download(&ctx,read_id(&s,"source")?,11)?==bytes,"CATALOG_OUTPUT_SOURCE_AEAD_READBACK")?;
        check(registered.intent_artifact_id()==intent.artifact_id&&registered.precommit_artifact_id()==precommit.artifact_id&&request.transaction_receipt_sha256()==precommit.sha256,"CATALOG_REGISTERED_BINDINGS")?;
        check(revisions.repository().read_commit_intent(&rc,StoredCommitIntentLookup::new(project()?,key,job_id,1)?)?.as_ref()==Some(registered),"CATALOG_DB_REGISTERED_BINDING")?;
        check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(200)?),2)?,"CATALOG_FINAL_HEAD")?;
        if bound{
            check((key,job_id,original_claim.input().request)==(input.job_identity().key(),input.job_identity().job(),input.job_identity().request()),"CATALOG_REQUEST_IDENTITY_NOT_CALLER_UUIDS")?;
            let replay=revisions.repository().claim_job(&rc,&original_claim,ContentDigest::of(b"retained-claim-observation-only"))?;
            check(replay.outcome()==StoredJobOutcome::Replay&&replay.state()==StoredJobState::TerminalSuccess&&replay.attempt_no()==1&&replay.result_revision_id()==Some(revision(200)?),"CATALOG_BOUND_REPLAY_NO_EXECUTION")?;
            let mut different=original_claim.input().clone();different.request_sha=ContentDigest::of(b"changed same-key request");
            let conflict=revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::lifecycle::StoredJobClaim::new(different)?;
            check(matches!(revisions.repository().claim_job(&rc,&conflict,ContentDigest::of(b"same-key-conflict")),Err(revision_service::RevisionError::RepositoryFailure)),"CATALOG_CHANGED_REQUEST_NOT_REJECTED")?;
            let unchanged=revisions.repository().claim_job(&rc,&original_claim,ContentDigest::of(b"after-conflict-read-only-observation"))?;
            check(unchanged==replay,"CATALOG_CONFLICT_CHANGED_ORIGINAL_OBSERVATION")?;
        }
        save_handles(&json!({"schema":"p09.catalog-sql-observation/v1","result":result.artifact_id.public_id(),"intent":intent.artifact_id.public_id(),"precommit":precommit.artifact_id.public_id(),
            "job_key":key,"job_id":job_id,
            "intent_sha":intent.sha256.hex(),"precommit_sha":precommit.sha256.hex(),"request_sha":request.canonical_sha256()?.hex(),"storage":input.receipt()}))?;
        Ok(json!({"state":"PASS_REAL_CATALOG_HWPX_SQL23_GUARDED_JOB_CAS_COMPLETION","guard_checks":checks.get(),"actual_staged_hwpx_validator":true,"original_source_preserved":true,
            "request_key_bound":bound,"retained_claim_replay_observed":bound,"changed_request_rejected":bound,
            "synthetic_route_and_scanner":true,"trusted_product_or_native_qualified":false}))
    })?
}
fn restart()->Result<Value>{
    let s=state()?;let h=handles()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let stored=a.download(&ctx,read_id(&h,"result")?,20)?;let expected_sha:[u8;32]=serde_json::from_value(h["storage"]["output_package_sha256"].clone())?;
    check(ContentDigest::of(&stored).as_bytes()==&expected_sha&&h["storage"]["output_bytes"].as_u64()==Some(stored.len()as u64),"CATALOG_RESTART_OUTPUT_BINDING")?;
    let package=ImportedSourcePackage::import(&stored,DocumentId::parse("actual-form-document")?,expected_sha,SourceImportLimits::default())?;
    package.observe_protection_signals()?.require_no_observed_document_signals()?;
    let forms=ImportedDocumentForms::import(package)?;let review=ImportedDocumentReviewBodies::import(&forms)?;
    check(serde_json::to_value(review.receipt())?==h["storage"]["expected_output_review_import"],"CATALOG_RESTART_ACTUAL_HWPX_READBACK")?;
    let original=a.download(&ctx,read_id(&s,"source")?,20)?;let original_sha:[u8;32]=serde_json::from_value(h["storage"]["source_package_sha256"].clone())?;
    check(ContentDigest::of(&original).as_bytes()==&original_sha&&original!=stored,"CATALOG_RESTART_ORIGINAL_PRESERVED")?;
    let(key,job_id)=if IDENTITY_MODE.load(std::sync::atomic::Ordering::Relaxed){(serde_json::from_value(h["job_key"].clone())?,serde_json::from_value(h["job_id"].clone())?)}else{(id(101),id(102))};
    let lookup=StoredCommitIntentLookup::new(project()?,key,job_id,1)?;let row=revisions.repository().read_commit_intent(&rc,lookup)?.ok_or("CATALOG_RESTART_REGISTERED_ROW")?;
    check(row.intent_artifact_id()==read_id(&h,"intent")?&&row.precommit_artifact_id()==read_id(&h,"precommit")?&&row.intent_sha256().hex()==h["intent_sha"].as_str().ok_or("CATALOG_INTENT_SHA")?
        &&row.request_sha256().hex()==h["request_sha"].as_str().ok_or("CATALOG_REQUEST_SHA")?,"CATALOG_RESTART_REGISTERED_RECEIPTS")?;
    for(key,digest)in[("intent","intent_sha"),("precommit","precommit_sha")]{check(ContentDigest::of(&a.download(&ctx,read_id(&h,key)?,20)?).hex()==h[digest].as_str().ok_or("CATALOG_RECEIPT_SHA")?,"CATALOG_RESTART_RECEIPT_AEAD")?;}
    check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(200)?),2)?,"CATALOG_RESTART_COMMITTED_HEAD")?;
    Ok(json!({"state":"PASS_RESTART_CATALOG_SQL_REGISTERED_ROW_HEAD_AND_ACTUAL_HWPX_AEAD_READBACK","execution_retried":false,"domain_mutations":false,
        "full_manifest_reconciliation_qualified":false,"trusted_product_or_native_qualified":false}))
}
pub fn run(mode:&str)->Result<Value>{owned_root()?;match mode{
    "--fixture"=>setup::fixture(),"--seed"=>setup::seed_source(&source()?),"--execute"=>execute(),"--restart-registered"=>restart(),
    "--wrong-key"=>{check(matches!(artifacts()?.download(&actor()?,read_id(&handles()?,"result")?,20),Err(ArtifactError::CryptoFailure)),"CATALOG_WRONG_KEY_DENIAL")?;
        Ok(json!({"state":"PASS_CATALOG_REAL_DISK_WRONG_KEY_DENIED","raw_values":false}))},_=>Err("CATALOG_STORAGE_CLOSED_MODE".into())}}
