//! Own fixture only; real legacy worker lease + registered service CAS bootstrap, no direct seals.
use super::*;
macro_rules! migration{($file:literal)=>{include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/",$file)).as_slice()};}
const MIGRATIONS:[&[u8];23]=[
 migration!("0001_p14_metadata.up.sql"),migration!("0002_p14_artifact_service.up.sql"),migration!("0003_p14_revision_cas.up.sql"),
 migration!("0004_p14_history_checkpoints.up.sql"),migration!("0005_p14_job_state_machine.up.sql"),migration!("0006_p14_worker_lease_fencing.up.sql"),
 migration!("0007_p14_idempotency_reconciliation.up.sql"),migration!("0008_p14_cancel_cleanup.up.sql"),migration!("0009_p14_retention_local_mirror.up.sql"),
 migration!("0010_p16_artifact_repository.up.sql"),migration!("0011_p16_plan_source.up.sql"),migration!("0012_p16_durable_plan_store.up.sql"),
 migration!("0013_p16_plan_review_evidence.up.sql"),migration!("0014_p17_history_checkpoint_note.up.sql"),migration!("0015_p17_atomic_mirror_checkpoint.up.sql"),
 migration!("0016_p17_durable_git_mirror_push.up.sql"),migration!("0017_p17_durable_git_mirror_pull.up.sql"),migration!("0018_p09_full_document_ir.up.sql"),
 migration!("0019_p09_authorized_full_ir_intent.up.sql"),migration!("0020_p09_source_form_policy.up.sql"),migration!("0021_p09_source_formula_policy.up.sql"),
 migration!("0022_p09_formula_issuer_registry.up.sql"),migration!("0023_p09_stored_revision_jobs.up.sql")];
const SEED:&str=include_str!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../tools/p09/fixtures/postgres_revision_adapter.sql"));
const ROLES:&str=include_str!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../tools/p09/fixtures/sql23_service_roles.sql"));
pub(super) fn admin()->Result<Client>{let mut c=raw(&value("P09_SQL23_ADMIN_USER")?,&value("P09_SQL23_ADMIN_PASSWORD")?)?;
    let actual:String=c.query_one("SELECT current_setting('data_directory')",&[])?.try_get(0)?;
    check(fs::canonicalize(actual)?==fs::canonicalize(owned_root()?.join("cluster/data"))?,"STORAGE_DATABASE_NOT_OWNED")?;scoped(&mut c)?;Ok(c)}
pub fn fixture()->Result<Value>{let mut c=admin()?;
    for source in MIGRATIONS{let sql=std::str::from_utf8(source)?;c.batch_execute(&format!("SELECT set_config('hwpx_agent.migration_sha256','{}',false);\n{sql}",ContentDigest::of(source).hex()))?;}
    c.batch_execute(ROLES)?;
    check(SEED.matches("WITH seed AS (").count()==1,"STORAGE_METADATA_SEED_BOUNDARY")?;
    let header=SEED.split("WITH seed AS (").next().ok_or("STORAGE_METADATA_HEADER")?.replace("hancom-hangul-2020-secondary",PROFILE);
    c.batch_execute(&format!("{header}\nCOMMIT;"))?;
    Ok(json!({"state":"PASS_OWNED_SCHEMA23_ROLES_WITHOUT_SYNTHETIC_ARTIFACT_ROWS","migrations":23,"metadata_artifacts_seeded":0}))}
pub fn register(c:&mut Client,agent:u128,cap:ContentDigest)->Result<()>{
    let row=c.query_one("SELECT * FROM hwpx_agent.register_scheduler_worker($1,$2::character(64),$3,$4,$5::character(64),'ready',300,$6::character(64))",
        &[&id(1),&subject()?.hex(),&id(agent),&PROFILE,&cap.hex(),&ContentDigest::of(b"storage-register").hex()])?;
    check(row.try_get::<_,Uuid>("returned_agent_instance_id")?==id(agent),"STORAGE_WORKER_ID")}
pub fn seed()->Result<Value>{seed_source(SOURCE)}
pub fn seed_source(source:&[u8])->Result<Value>{let a=artifacts()?;let ctx=actor()?;let rc=context()?;
    let prior=ingest(&a,PRIOR,ArtifactKind::Source,"application/octet-stream","prior.bin")?;
    let original=ingest(&a,source,ArtifactKind::Result,"application/vnd.hancom.hwpx+zip","synthetic-original.hwpx")?;
    let receipt_bytes=br#"{"scope":"synthetic bootstrap, not Native"}"#;
    let receipt=ingest(&a,receipt_bytes,ArtifactKind::Receipt,"application/json","bootstrap-receipt.json")?;
    let req=RevisionCommitRequest::new(commit(21)?,project()?,branch()?,RevisionHead::empty(),revision(20)?,vec![],prior.artifact_id,original.artifact_id,None,
        ContentDigest::of(b"bootstrap-plan"),RevisionValidationState::Verified,ContentDigest::of(b"synthetic-validator"),receipt.sha256)?;
    let mut c=admin()?;let cap=ContentDigest::of(b"bootstrap-capability");register(&mut c,23,cap)?;
    c.query_one("SELECT * FROM hwpx_agent.claim_idempotent_job_v2($1,$2,$3,$4::character(64),$5,$6,$7,$8,NULL,0,
        $9::character(64),$10::character(64),$11::character(64),$12::character(64),$13::character(64),$14::character(64),$15,$16::character(64),3,1,4,600,$17::character(64))",
        &[&id(1),&id(2),&id(3),&subject()?.hex(),&id(50),&id(51),&id(52),&prior.artifact_id.as_uuid(),&req.canonical_sha256()?.hex(),
        &ContentDigest::of(b"bootstrap-manifest").hex(),&prior.sha256.hex(),&original.sha256.hex(),&receipt.sha256.hex(),&req.operation_plan_sha256().hex(),&PROFILE,&cap.hex(),&ContentDigest::of(b"bootstrap-claim").hex()])?;
    let row=c.query_one("SELECT * FROM hwpx_agent.lease_idempotent_job_v2($1,$2,$3::character(64),$4,$5,$6,$7,120,$8::character(64))",
        &[&id(1),&id(2),&subject()?.hex(),&id(50),&id(51),&id(23),&id(53),&ContentDigest::of(b"bootstrap-lease").hex()])?;
    let lease=StoredJobLease::new(RevisionLeaseIdentity{idempotency_key:id(50),job_id:id(51),agent_instance_id:id(23),execution_id:id(53),
        attempt_no:row.try_get("returned_attempt_count")?,fencing_token:row.try_get("returned_fencing_token")?,authorization_id:row.try_get("returned_commit_authorization_id")?})?;
    for(from,to)in[("leased","staged"),("staged","executing"),("executing","validating")]{c.query_one(
        "SELECT * FROM hwpx_agent.advance_idempotent_job_v2($1,$2,$3::character(64),$4,$5,$6,$7,1,1,$8,$9,$10::character(64))",
        &[&id(1),&id(2),&subject()?.hex(),&id(50),&id(51),&id(23),&id(53),&from,&to,&ContentDigest::of(b"bootstrap-stage").hex()])?;}
    let revisions=RevisionService::new(repository()?.with_received_lease(lease));
    check(matches!(revisions.commit(&rc,&req)?,CommitOutcome::Committed(_)),"STORAGE_BOOTSTRAP_CAS")?;
    let row=c.query_one("SELECT * FROM hwpx_agent.complete_idempotent_job_success_v2($1,$2,$3::character(64),$4,$5,$6,$7,1,1,$8,$9,$10::character(64))",
        &[&id(1),&id(2),&subject()?.hex(),&id(50),&id(51),&id(23),&id(53),&revision(20)?.as_uuid(),&receipt.artifact_id.as_uuid(),&ContentDigest::of(b"bootstrap-complete").hex()])?;
    check(row.try_get::<_,String>("returned_state")?=="terminal_success"&&a.download(&ctx,original.artifact_id,11)?==source,"STORAGE_BOOTSTRAP_COMPLETE_READBACK")?;
    save(&json!({"schema":"p09.storage-retained-handles/v1","source":original.artifact_id.public_id(),"prior":prior.artifact_id.public_id(),"bootstrap_receipt":receipt.artifact_id.public_id()}))?;
    Ok(json!({"state":"PASS_REAL_AEAD_SQL_SOURCE_BOOTSTRAP_CAS_AND_COMPLETION","artifact_count":3,"direct_seal_insertion":false,"actual_product_execution":false}))}
