//! Owned fixture only. The actual recovery API receives no original manifest/request/state file.
use super::*;
use serde::{Serialize,Deserialize};
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::StoredCommitIntentLookup;
#[derive(Serialize,Deserialize)]#[serde(deny_unknown_fields)]
struct Locator{schema:String,key:Uuid,job:Uuid,attempt:i32}
const SCHEMA:&str="p09.archived-registered-locator/v1";
const ORIGINALS:[&str;3]=["catalog-completed-handles.json","retained-receipts.json","public-fixture-request.json"];
fn regular(path:&std::path::Path)->Result<()>{
    let meta=fs::symlink_metadata(path)?;check(meta.is_file()&&!meta.file_type().is_symlink()&&meta.len()>0&&meta.len()<=16384,"ARCHIVE_FIXTURE_REGULAR_BOUNDED_FILE")?;
    #[cfg(windows)]{use std::os::windows::fs::MetadataExt;check(meta.file_attributes()&0x400==0,"ARCHIVE_FIXTURE_FILE_REPARSE")?;}Ok(())
}
pub(super) fn save_locator()->Result<()>{
    use std::io::Write;let root=owned_root()?;let path=root.join(ORIGINALS[0]);regular(&path)?;let data:Value=serde_json::from_slice(&fs::read(path)?)?;
    let locator=Locator{schema:SCHEMA.into(),key:serde_json::from_value(data["job_key"].clone())?,job:serde_json::from_value(data["job_id"].clone())?,attempt:1};
    StoredCommitIntentLookup::new(project()?,locator.key,locator.job,locator.attempt)?;
    let mut file=fs::OpenOptions::new().write(true).create_new(true).open(root.join("archived-registered-locator.json"))?;
    file.write_all(&serde_json::to_vec(&locator)?)?;file.sync_all()?;Ok(())
}
pub(super) fn cold()->Result<Value>{
    let root=owned_root()?;let mut moved=Vec::new();
    let outcome=(||->Result<Value>{
        // Exact newly generated fixture files only, no glob/user path/overwrite. Preserve and restore all bytes.
        for name in ORIGINALS{
            let source=root.join(name);let preserved=root.join(format!("{name}.preserved-for-archived-recovery"));
            check(source.parent()==Some(root.as_path())&&preserved.parent()==Some(root.as_path())&&!preserved.exists(),"ARCHIVE_FIXTURE_EXACT_MOVE_SCOPE")?;
            regular(&source)?;let before=ContentDigest::of(&fs::read(&source)?);fs::rename(&source,&preserved)?;moved.push((source,preserved,before));
        }
        check(ORIGINALS.iter().all(|name|!root.join(name).exists()),"ARCHIVE_FIXTURE_ORIGINAL_FILES_MUST_BE_ABSENT")?;
        let path=root.join("archived-registered-locator.json");regular(&path)?;let locator:Locator=serde_json::from_slice(&fs::read(path)?)?;
        check(locator.schema==SCHEMA,"ARCHIVE_FIXTURE_LOCATOR_SCHEMA")?;
        let lookup=StoredCommitIntentLookup::new(project()?,locator.key,locator.job,locator.attempt)?;
        let artifacts=artifacts()?;let rc=context()?;let ctx=actor()?;let revisions=RevisionService::new(repository()?);
        let recovered=reconcile_archived_registered_stored_commit(&artifacts,&revisions,&ctx,&rc,lookup,||20)?;
        let ArchivedRegisteredStoredCommitRecoveryOutcome::Registered(StoredCommitRecoveryOutcome::Committed{receipt,result:RecoveredResult::VerifiedAvailable(result)})=recovered
            else{return Err("ARCHIVE_FIXTURE_EXPECTED_COMMITTED_AVAILABLE".into())};
        check(receipt.committed_head()==RevisionHead::new(Some(revision(200)?),2)?&&result.kind==ArtifactKind::Result,"ARCHIVE_FIXTURE_EXACT_HISTORICAL_REVISION")?;
        Ok(json!({"state":"PASS_ARCHIVED_REGISTERED_COMMIT_WITHOUT_ORIGINAL_FILES_OR_RAM","original_files_absent":3,
            "original_manifest_or_ServiceRequest_supplied":false,"current_SQL_ACL_AEAD_and_sealed_commit_verified":true,
            "committed_result_currently_available":true,"engine_claim_lease_CAS_or_job_transition_executed":false}))
    })();
    let mut restored=true;
    for(source,preserved,expected)in moved.into_iter().rev(){
        let result=(||->Result<()>{
            check(source.parent()==Some(root.as_path())&&preserved.parent()==Some(root.as_path())&&!source.exists(),"ARCHIVE_FIXTURE_EXACT_RESTORE_SCOPE")?;
            regular(&preserved)?;fs::rename(&preserved,&source)?;check(ContentDigest::of(&fs::read(source)?)==expected,"ARCHIVE_FIXTURE_ORIGINAL_BYTES_RESTORED")?;Ok(())
        })();if result.is_err(){restored=false;}
    }
    check(restored,"ARCHIVE_FIXTURE_RESTORE_FAILED_ORIGINALS_PRESERVED")?;let mut row=outcome?;row["all_original_files_restored_byte_exact"]=json!(true);Ok(row)
}
