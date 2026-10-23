//! Fresh SQL lifecycle + disk AEAD, with explicitly isolated policy selector/routes/scanner.
use super::*;
use std::sync::atomic::{AtomicUsize,Ordering};
use hwpx_agent_cli::{form_stored_provider::{StoredFormProvider,actual_import::{https_target_output::*,source_policy::SourcePolicyBinding,
    source_search::request_recovery::{StoredRequestRecoveryObservation,StoredRequestRecoveryError}}},
    form_product_request::stored_operations::{StoredProductRequest as Product,https_targets::{HttpsTargetProductLimits as Limits,HttpsTargetRequestEntry,HttpsTargetProductError}},
    form_product_request::stored_operations::compiled_search::request_lookup::SearchRequestLookupError,
    reference_validation_product::ReferenceValidationProductOperation as Meaning};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookupError;
use domain_ir::{Architecture,BackendHealth,BackendHealthState,BackendId,BackendKind,CapabilityId,CapabilityRouteCatalog,DocumentId,ExactTargetProfile,
    PolicyScope,PreservationImpact,PreservationRequirement,ProtectionState,RegistryTrustState,RouteBinding,RouteContext,SignatureImpact,SupportState,TargetProfileId,
    ExternalLinkPolicy,ExternalTargetApproval,HyperlinkTarget};
use hwpx_package::document_import::{SourceImportLimits,fields::{ImportedDocumentFields,semantics::{ImportedFieldMeaning,source_index::SourceFieldMeaningIndex}}};
#[path="../../../hwpx-package/tests/support/document_import_field_fixture.rs"]mod fixture;
#[path="https_policy_fixture.rs"]mod policy_fixture;
#[path="https_late_revoke.rs"]mod late_revoke;
pub(super) fn policy_fixture_phase()->&'static str{policy_fixture::phase()}
const FILES:[&str;4]=["retained-receipts.json","https-public-request.json","https-policy-version.json","https-completed.json"];
const NEW_URI:&str="https://example.org/sql537?x=1&y=2";
fn path(name:&str)->Result<PathBuf>{check(FILES.contains(&name),"HTTPS_SQL_CLOSED_FILE")?;Ok(owned_root()?.join(name))}
fn save_value(name:&str,value:&Value)->Result<()>{use std::io::Write;let bytes=serde_json::to_vec(value)?;
    check(!bytes.is_empty()&&bytes.len()<=16384,"HTTPS_SQL_FILE_BOUND")?;let mut f=fs::OpenOptions::new().write(true).create_new(true).open(path(name)?)?;
    f.write_all(&bytes)?;f.sync_all()?;Ok(())}
fn regular(path:&std::path::Path)->Result<()>{let m=fs::symlink_metadata(path)?;
    check(m.is_file()&&!m.file_type().is_symlink()&&m.len()>0&&m.len()<=16384,"HTTPS_SQL_REGULAR_FILE")?;
    #[cfg(windows)]{use std::os::windows::fs::MetadataExt;check(m.file_attributes()&0x400==0,"HTTPS_SQL_NO_REPARSE")?;}Ok(())}
fn load(name:&str)->Result<Value>{let path=path(name)?;regular(&path)?;Ok(serde_json::from_slice(&fs::read(path)?)?)}
fn limits()->Result<Limits>{Ok(Limits::standard()?)}
struct IsolatedPolicy{version:HttpsTargetPolicyVersion,reads:AtomicUsize,sql:Option<postgres::PostgresHttpsTargetPolicyProvider>}
impl HttpsTargetPolicyRepository for IsolatedPolicy{
    fn read_current(&self,s:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,StoredHttpsTargetError>{
        if let Some(sql)=&self.sql{self.reads.fetch_add(1,Ordering::SeqCst);return sql.read_current(s);}
        let b=&self.version.binding;
        if s.tenant()!=b.tenant||s.subject()!=b.creator_subject||s.project()!=b.project||s.branch()!=b.branch||s.document()!=&b.document
            ||s.head().revision_id()!=Some(b.source_revision)||s.head().generation()!=b.source_head_generation
            ||s.source_artifact()!=b.source_result_artifact||s.source_sha256()!=b.source_package_sha256{return Err(StoredHttpsTargetError::Repository);}
        self.reads.fetch_add(1,Ordering::SeqCst);Ok(self.version.clone())
    }
}
struct NoPolicyReads;
impl HttpsTargetPolicyRepository for NoPolicyReads{
    fn read_current(&self,_:&HttpsTargetPolicyScope)->Result<HttpsTargetPolicyVersion,StoredHttpsTargetError>{Err(StoredHttpsTargetError::Repository)}
}
fn routes()->Result<(RouteContext,CapabilityRouteCatalog)>{
    let target=ExactTargetProfile::new(TargetProfileId::parse(PROFILE)?,"synthetic-only",Architecture::X86)?;let backend=BackendId::parse("storage-direct")?;
    Ok((RouteContext::new(target.clone(),[9;32],7,RegistryTrustState::SignatureVerified,PolicyScope::CurrentPcPersonalLocalDevelopment,
        PreservationRequirement::Exact,ProtectionState::Unprotected,10000,vec![BackendHealth::new(backend.clone(),BackendHealthState::Healthy,3,9000,10000)])?,
        CapabilityRouteCatalog::from_bindings(vec![RouteBinding::new(CapabilityId::parse("ref.hyperlink_edit")?,backend,BackendKind::DirectHwpx,SupportState::Verified,
            target,[9;32],7,10,10,PreservationImpact::Exact,SignatureImpact::Preserved)])?))
}
fn verify_output(bytes:&[u8])->Result<()>{let forms=fixture::forms(bytes,"actual-form-document")?;let fields=ImportedDocumentFields::import(&forms)?;
    let index=SourceFieldMeaningIndex::import(&fields,limits()?.auxiliary)?;let all=index.observations();
    check(all.len()==1&&matches!(&all[0].meaning,ImportedFieldMeaning::HttpsTarget{target:HyperlinkTarget::Https{uri}}if uri==NEW_URI),"HTTPS_SQL_EXACT_TARGET_READBACK")
}
fn seed()->Result<Value>{let bytes=fixture::captured()?;let mut row=setup::seed_source(&bytes)?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;
    let revisions=RevisionService::new(repository()?);let p=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let s=state()?;let source=p.import_actual_forms(RevisionHead::new(Some(revision(20)?),1)?,10)?;let r=&source.receipt().imported;
    let b=SourcePolicyBinding{tenant:tenant()?,project:project()?,branch:branch()?,document:DocumentId::parse("actual-form-document")?,source_revision:revision(20)?,
        source_head_generation:1,source_result_artifact:read_id(&s,"source")?,source_package_sha256:ContentDigest::of(&bytes),
        source_provenance_sha256:ContentDigest::parse(&hex::encode(r.source_provenance_sha256))?,observed_graph_sha256:ContentDigest::parse(&hex::encode(r.graph_sha256))?,
        policy_version:id(537),policy_generation:1,creator_subject:subject()?};
    let target=HyperlinkTarget::Https{uri:NEW_URI.into()};let policy=ExternalLinkPolicy{allow_https:true,allow_mailto:false,allow_managed_documents:false,
        approvals:vec![ExternalTargetApproval{kind:target.external_kind().ok_or("HTTPS_SQL_TARGET_KIND")?,target_sha256:target.external_approval_sha256(limits()?.targets)?}],policy_revision_sha256:"a".repeat(64)};
    let version=if HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed){source.prepare_https_policy_registration(&p,&policy,0,limits()?.targets,10)?
        .register(&p,&postgres::PostgresHttpsTargetPolicyProvider::new(repository()?),10)?}
        else if HTTPS_POLICY_MODE.load(Ordering::Relaxed){policy_fixture::publish_and_check(&a,&revisions,&p,&source,&policy)?}
        else{let d=ingest(&a,&serde_json::to_vec(&json!({"schema_version":HTTPS_TARGET_POLICY_SCHEMA,"binding":b,"policy":policy}))?,ArtifactKind::Evidence,
            HTTPS_TARGET_POLICY_MEDIA_TYPE,"isolated-https-policy.json")?;HttpsTargetPolicyVersion{binding:b,artifact:d.artifact_id,digest:d.sha256}};
    save_value("https-policy-version.json",&json!({"binding":version.binding,"artifact":version.artifact.public_id(),"digest":version.digest.hex()}))?;
    let assessment=Meaning::assess_package_field_semantics(&bytes,DocumentId::parse("actual-form-document")?,*ContentDigest::of(&bytes).as_bytes(),SourceImportLimits::default(),limits()?.auxiliary)?;
    let selection=assessment.selections().first().ok_or("HTTPS_SQL_SOURCE_SELECTION")?;
    save_value("https-public-request.json",&json!({"schema_version":"hwpx-agent.product-https-target-request/v1","idempotency_key":"owned-https-sql537-only",
        "project_id":project()?.public_id(),"document_id":"actual-form-document","base_revision":revision(20)?.public_id(),"expected_head_generation":1,
        "expected_source_package_sha256":ContentDigest::of(&bytes).hex(),"plan_id":"https-sql537-plan","operation":{"kind":"change_https_targets","changes":[{
        "reference_id":selection.reference_id,"expected_source_field_sha256":hex::encode(selection.source_field_sha256),"expected_meaning_sha256":hex::encode(selection.meaning_sha256),
        "target":{"kind":"https","uri":NEW_URI}}]}}))?;
    row["actual_policy_AEAD_artifact"]=json!(true);row["policy_selector_isolated_not_operational"]=json!(!HTTPS_POLICY_MODE.load(Ordering::Relaxed));
    if HTTPS_POLICY_MODE.load(Ordering::Relaxed){row["actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives"]=json!(!HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed));}
    if HTTPS_ATOMIC_MODE.load(Ordering::Relaxed){row["actual_atomic_policy_lock_and_binding_checks"]=json!(!HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed));}Ok(row)
}
fn execute()->Result<Value>{
    if HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed){return late_revoke::execute();}
    if HTTPS_ATOMIC_MODE.load(Ordering::Relaxed){return policy_fixture::atomic_execute();}
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
    let stored=load("https-policy-version.json")?;let policy=IsolatedPolicy{version:HttpsTargetPolicyVersion{binding:serde_json::from_value(stored["binding"].clone())?,
        artifact:ArtifactId::parse(stored["artifact"].as_str().ok_or("HTTPS_SQL_POLICY_ID")?)?,digest:ContentDigest::parse(stored["digest"].as_str().ok_or("HTTPS_SQL_POLICY_DIGEST")?)?},reads:AtomicUsize::new(0),
        sql:if HTTPS_POLICY_MODE.load(Ordering::Relaxed){Some(postgres::PostgresHttpsTargetPolicyProvider::new(repository()?))}else{None}};
    let wire=serde_json::to_vec(&load("https-public-request.json")?)?;
    let HttpsTargetRequestEntry::Prepared(product)=Product::prepare_https_targets_or_observe_json(&provider,&policy,&wire,limits()?,10)?else{return Err("HTTPS_SQL_FRESH_REQUEST_REQUIRED".into())};
    let(c,r)=routes()?;let prepared=product.prepare_execution_manifest(&provider,&policy,&c,&r,domain_ir::TransactionId::parse("https-sql537")?,10)?;
    check(prepared.require_current_product_route(&provider,&policy,&c,&r,10).is_err(),"HTTPS_SQL_ROUTE_STAYS_UNQUALIFIED")?;
    let checks=AtomicUsize::new(0);let workspace=owned_root()?.join("https-workspace");let s=state()?;let original=a.download(&ctx,read_id(&s,"source")?,10)?;
    let result=prepared.with_verified_guarded_job_preparation(&provider,&policy,identity::StoredJobPolicy{max_delay_seconds:4,..Default::default()},commit(5371)?,revision(5372)?,Default::default(),
        ||{checks.fetch_add(1,Ordering::SeqCst);let(c,r)=routes().map_err(|_|())?;Ok((c,r,10))},|job,source,mut validator|->Result<Value>{
            let claim=job.claim().clone();let mut client=raw("p09_revision_284",&value("P09_SQL23_REVISION_PASSWORD")?)?;scoped(&mut client)?;
            setup::register(&mut client,130,claim.input().capability_sha)?;
            let report=job.run_once(&a,&revisions,&ctx,&rc,id(130),id(5373),120,ContentDigest::of(b"isolated-https-sql537-event"),&workspace,source,&mut validator,||10);
            check(report.stage==StoredJobRunStage::Completed,"HTTPS_SQL_JOB_COMPLETED")?;
            check(report.repository_error.is_none()&&report.cas_error.is_none()&&report.binding_error.is_none()&&report.completion.is_some(),"HTTPS_SQL_NO_JOB_ERRORS")?;
            let result=report.result.as_ref().ok_or("HTTPS_SQL_RESULT")?;let intent=report.intent.as_ref().ok_or("HTTPS_SQL_INTENT")?;
            let precommit=report.precommit.as_ref().ok_or("HTTPS_SQL_PRECOMMIT")?;let registered=report.registered_intent.as_ref().ok_or("HTTPS_SQL_REGISTERED")?;
            check(registered.intent_artifact_id()==intent.artifact_id&&registered.precommit_artifact_id()==precommit.artifact_id
                &&revisions.repository().read_commit_intent(&rc,StoredCommitIntentLookup::new(project()?,claim.input().key,claim.input().job,1)?)?.as_ref()==Some(registered),"HTTPS_SQL_EXACT_REGISTERED_ROW")?;
            verify_output(&a.download(&ctx,result.artifact_id,11)?)?;check(a.download(&ctx,read_id(&s,"source")?,11)?==original,"HTTPS_SQL_SOURCE_PRESERVED")?;
            check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(5372)?),2)?,"HTTPS_SQL_ONE_NEW_HEAD")?;
            save_value("https-completed.json",&json!({"result":result.artifact_id.public_id()}))?;
            Ok(json!({"state":if HTTPS_POLICY_MODE.load(Ordering::Relaxed){"PASS_HTTPS_REAL_SQL25_GUARDED_JOB_REGISTERED_CAS_COMPLETION_NOT_ADMISSION"}else{"PASS_HTTPS_REAL_SQL24_GUARDED_JOB_REGISTERED_CAS_COMPLETION_NOT_ADMISSION"},"guard_attached_automatically":true,
                "actual_registered_row_and_AEAD_readback":true,"source_preserved":true,"route_unqualified":true}))
        })??;
    check(checks.load(Ordering::SeqCst)==4&&policy.reads.load(Ordering::SeqCst)>0,"HTTPS_SQL_PREPARATION_AND_THREE_CURRENT_GUARDS")?;Ok(result)
}
fn cold()->Result<Value>{let wire=serde_json::to_vec(&load("https-public-request.json")?)?;let root=owned_root()?;let mut moved=Vec::new();
    let outcome=(||->Result<Value>{
        for name in FILES{let original=path(name)?;let preserved=root.join(format!("{name}.preserved-for-https-recovery"));
            check(original.parent()==Some(root.as_path())&&preserved.parent()==Some(root.as_path())&&!preserved.exists(),"HTTPS_SQL_EXACT_PRESERVE_SCOPE")?;
            regular(&original)?;let digest=ContentDigest::of(&fs::read(&original)?);fs::rename(&original,&preserved)?;moved.push((original,preserved,digest));}
        check(FILES.iter().all(|name|!root.join(name).exists()),"HTTPS_SQL_NO_SAVED_ORIGINAL_PATHS")?;
        let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
        let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,DocumentId::parse("actual-form-document")?)?;
        let HttpsTargetRequestEntry::Existing(job)=Product::prepare_https_targets_or_observe_json(&provider,&NoPolicyReads,&wire,limits()?,20)?else{return Err("HTTPS_SQL_NO_PREPARATION_ON_REPLAY".into())};
        check(job.state()==revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::lifecycle::StoredJobState::TerminalSuccess&&job.attempt_no()==1,"HTTPS_SQL_ONE_COMPLETED_ATTEMPT")?;
        let lookup=Product::prepare_https_targets_lookup_json(&provider,&wire,limits()?)?;
        let StoredRequestRecoveryObservation::Existing{job,effect:ArchivedRegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{receipt,result:RecoveredResult::VerifiedAvailable(result)})}=lookup.recover_registered(&provider,||20)?
            else{return Err("HTTPS_SQL_REGISTERED_EFFECT_REQUIRED".into())};
        check(job.result_revision_id()==Some(revision(5372)?)&&job.attempt_no()==1&&receipt.committed_head()==RevisionHead::new(Some(revision(5372)?),2)?,"HTTPS_SQL_SAME_EFFECT_AND_ATTEMPT")?;
        verify_output(&a.download(&ctx,result.artifact_id,20)?)?;
        let mut changed:Value=serde_json::from_slice(&wire)?;changed["plan_id"]=json!("different-https-plan");
        check(matches!(Product::prepare_https_targets_lookup_json(&provider,&serde_json::to_vec(&changed)?,limits()?)?.recover_registered(&provider,||20),
            Err(HttpsTargetProductError::Lookup(SearchRequestLookupError::Recovery(StoredRequestRecoveryError::Lookup(StoredRequestLookupError::KeyConflict))))),"HTTPS_SQL_CHANGED_REQUEST_CONFLICT")?;
        let mut missing:Value=serde_json::from_slice(&wire)?;missing["idempotency_key"]=json!("missing-https-request");
        check(Product::prepare_https_targets_lookup_json(&provider,&serde_json::to_vec(&missing)?,limits()?)?.recover_registered(&provider,||20)?==StoredRequestRecoveryObservation::NotObserved,"HTTPS_SQL_MISSING_NOT_OBSERVED")?;
        Ok(json!({"state":"PASS_HTTPS_PUBLIC_REQUEST_REGISTERED_EFFECT_RECOVERY_NO_LOCAL_HANDLES","original_paths_absent":4,"actual_HWPX_and_AEAD_readback":true,
            "same_job_attempt_and_revision":true,"changed_request_conflict":true,"missing_is_not_observed":true,"claim_lease_CAS_or_execution_retried":false}))
    })();let mut restored=true;
    for(original,preserved,digest)in moved.into_iter().rev(){let result=(||->Result<()>{
        check(original.parent()==Some(root.as_path())&&preserved.parent()==Some(root.as_path())&&!original.exists(),"HTTPS_SQL_RESTORE_SCOPE")?;
        regular(&preserved)?;fs::rename(&preserved,&original)?;check(ContentDigest::of(&fs::read(original)?)==digest,"HTTPS_SQL_RESTORED_EXACT_BYTES")?;Ok(())})();if result.is_err(){restored=false;}}
    check(restored,"HTTPS_SQL_RESTORE_FAILED_PRESERVED_FILES_RETAINED")?;let mut row=outcome?;row["all_original_files_restored_byte_exact"]=json!(true);Ok(row)
}
pub fn run(mode:&str)->Result<Value>{owned_root()?;if HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed)&&matches!(mode,"--restart-registered"|"--cold-recover"){return late_revoke::observe();}match mode{
    "--fixture"=>if HTTPS_POLICY_MODE.load(Ordering::Relaxed){policy_fixture::install()}else{lookup24::run("--fixture")},"--seed"=>seed(),"--execute"=>execute(),"--cold-recover"|"--restart-registered"=>cold(),
    "--wrong-key"=>{let a=artifacts()?;let row=load("https-completed.json")?;
        check(matches!(a.download(&actor()?,ArtifactId::parse(row["result"].as_str().ok_or("HTTPS_SQL_RESULT_ID")?)?,20),Err(ArtifactError::CryptoFailure)),"HTTPS_SQL_WRONG_KEY_DENIED")?;
        Ok(json!({"state":"PASS_HTTPS_WRONG_AES_KEY_DENIED"}))},_=>Err("HTTPS_SQL_CLOSED_MODE".into())}}
