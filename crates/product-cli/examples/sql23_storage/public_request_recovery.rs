//! Owned newly generated fixture files only; no operational job/DB and no original manifest/locator.
use super::*;
use hwpx_agent_cli::{form_stored_provider::{StoredFormProvider,actual_import::source_search::request_recovery::{StoredRequestRecoveryObservation as O,StoredRequestRecoveryError as E}},
    form_product_request::stored_literal_replacement::personal_info::catalog::{StoredPersonalInfoCatalogMaskProductRequest as Product,request_lookup::CatalogRequestLookupError as LE}};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::StoredRequestLookupError;
const ORIGINALS:[&str;4]=["catalog-completed-handles.json","retained-receipts.json","public-fixture-request.json","archived-registered-locator.json"];
fn regular(path:&std::path::Path)->Result<()>{
    let m=fs::symlink_metadata(path)?;check(m.is_file()&&!m.file_type().is_symlink()&&m.len()>0&&m.len()<=16384,"PUBLIC_RECOVERY_BOUNDED_OWNED_FILE")?;
    #[cfg(windows)]{use std::os::windows::fs::MetadataExt;check(m.file_attributes()&0x400==0,"PUBLIC_RECOVERY_FILE_REPARSE")?;}Ok(())
}
pub(super) fn cold()->Result<Value>{
    let root=owned_root()?;let request=root.join("public-fixture-request.json");regular(&request)?;let wire=fs::read(request)?;
    let mut moved=Vec::new();
    let outcome=(||->Result<Value>{
        for name in ORIGINALS{
            let source=root.join(name);let preserved=root.join(format!("{name}.preserved-for-public-recovery"));
            check(source.parent()==Some(root.as_path())&&preserved.parent()==Some(root.as_path())&&!preserved.exists(),"PUBLIC_RECOVERY_EXACT_PRESERVE_SCOPE")?;
            regular(&source)?;let sha=ContentDigest::of(&fs::read(&source)?);fs::rename(&source,&preserved)?;moved.push((source,preserved,sha));
        }
        check(ORIGINALS.iter().all(|name|!root.join(name).exists()),"PUBLIC_RECOVERY_ORIGINAL_PATHS_MUST_BE_ABSENT")?;
        let artifacts=artifacts()?;let rc=context()?;let actor=actor()?;let revisions=RevisionService::new(repository()?);
        let provider=StoredFormProvider::bind(&artifacts,&revisions,&actor,&rc,project()?,branch()?,domain_ir::DocumentId::parse("actual-form-document")?)?;
        let prepared=Product::prepare_lookup_json(&provider,&wire)?;
        let O::Existing{job,effect:ArchivedRegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{receipt,result:RecoveredResult::VerifiedAvailable(result)})}=prepared.recover_registered(&provider,||20)?
            else{return Err("PUBLIC_RECOVERY_EXPECTED_COMMITTED_CURRENT_RESULT".into())};
        check(job.outcome()==StoredJobOutcome::Replay&&job.state()==StoredJobState::TerminalSuccess&&job.attempt_no()==1&&job.result_revision_id()==Some(revision(200)?)
            &&receipt.committed_head()==RevisionHead::new(Some(revision(200)?),2)?&&result.kind==ArtifactKind::Result,"PUBLIC_RECOVERY_EXACT_JOB_REVISION_BINDING")?;
        let mut changed:Value=serde_json::from_slice(&wire)?;changed["plan_id"]=json!("different-public-recovery-plan");
        let changed=Product::prepare_lookup_json(&provider,&serde_json::to_vec(&changed)?)?;
        check(matches!(changed.recover_registered(&provider,||20),Err(LE::Recovery(E::Lookup(StoredRequestLookupError::KeyConflict)))),"PUBLIC_RECOVERY_CHANGED_REQUEST_MUST_CONFLICT")?;
        let mut missing:Value=serde_json::from_slice(&wire)?;missing["idempotency_key"]=json!("unclaimed-public-effect-recovery-fixture");
        check(Product::prepare_lookup_json(&provider,&serde_json::to_vec(&missing)?)?.recover_registered(&provider,||20)?==O::NotObserved,"PUBLIC_RECOVERY_MISSING_REQUEST_NOT_NO_EFFECT")?;
        Ok(json!({"state":"PASS_PUBLIC_STRICT_REQUEST_TO_REGISTERED_EFFECT_WITHOUT_MANIFEST_CLAIM_OR_LOCATOR",
            "original_paths_absent":4,"only_original_public_request_supplied":true,"original_manifest_claim_locator_or_ServiceRequest_supplied":false,
            "current_SQL_request_ACL_registered_AEAD_and_sealed_commit_verified":true,"same_job_attempt_and_result_revision":true,
            "typed_changed_request_conflict":true,"missing_request_is_not_observed":true,"result_currently_available":true,
            "engine_claim_lease_CAS_job_transition_or_retry_executed":false}))
    })();
    let mut restored=true;
    for(source,preserved,expected)in moved.into_iter().rev(){
        let result=(||->Result<()>{
            check(source.parent()==Some(root.as_path())&&preserved.parent()==Some(root.as_path())&&!source.exists(),"PUBLIC_RECOVERY_EXACT_RESTORE_SCOPE")?;
            regular(&preserved)?;fs::rename(&preserved,&source)?;check(ContentDigest::of(&fs::read(source)?)==expected,"PUBLIC_RECOVERY_ORIGINAL_BYTES_RESTORED")?;Ok(())
        })();if result.is_err(){restored=false;}
    }
    check(restored,"PUBLIC_RECOVERY_RESTORE_FAILED_PRESERVED_FILES_RETAINED")?;let mut row=outcome?;row["all_original_files_restored_byte_exact"]=json!(true);Ok(row)
}
