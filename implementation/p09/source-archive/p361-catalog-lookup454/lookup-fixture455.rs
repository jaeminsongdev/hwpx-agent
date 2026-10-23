//! Fresh-schema24 cold lookup after one preauthorized fixture execution, never public execution routing.
use super::*;
use hwpx_agent_cli::{form_stored_provider::StoredFormProvider,form_product_request::stored_literal_replacement::personal_info::catalog::StoredPersonalInfoCatalogMaskProductRequest as Product};
use hwpx_agent_cli::form_product_request::stored_literal_replacement::personal_info::catalog::request_lookup::CatalogRequestLookupError;
use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::request_lookup::{StoredRequestObservation,StoredRequestLookupError};
const MIGRATION:&[u8]=include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../migrations/postgres/0024_p09_stored_request_lookup.up.sql"));
const SIGNATURE:&str="hwpx_agent.read_stored_revision_request_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint)";
fn request_path()->Result<PathBuf>{Ok(owned_root()?.join("public-fixture-request.json"))}
pub(super) fn save_fixture_request(bytes:&[u8])->Result<()>{
    // Deliberately public synthetic nonce and hashes only, no document text, passwords, AES/HMAC keys or full claim.
    use std::io::Write;check(!bytes.is_empty()&&bytes.len()<=16384,"LOOKUP_PUBLIC_FIXTURE_REQUEST_BOUND")?;
    let mut file=fs::OpenOptions::new().write(true).create_new(true).open(request_path()?)?;file.write_all(bytes)?;file.sync_all()?;Ok(())
}
fn request()->Result<Vec<u8>>{let path=request_path()?;let meta=fs::symlink_metadata(&path)?;
    check(meta.is_file()&&!meta.file_type().is_symlink()&&meta.len()>0&&meta.len()<=16384,"LOOKUP_PUBLIC_FIXTURE_REQUEST_BOUND")?;Ok(fs::read(path)?)}
fn install()->Result<Value>{let mut row=setup::fixture()?;let mut client=setup::admin()?;
    let sql=std::str::from_utf8(MIGRATION)?;client.batch_execute(&format!("SELECT set_config('hwpx_agent.migration_sha256','{}',false);\n{sql}",ContentDigest::of(MIGRATION).hex()))?;
    client.batch_execute(&format!("GRANT EXECUTE ON FUNCTION {SIGNATURE} TO p09_revision_284"))?;
    let cfg=LocalPostgresRevisionConfig::new(port()?,"postgres".into(),"p09_revision_284".into(),value("P09_SQL23_REVISION_PASSWORD")?)?;
    check(matches!(LocalPostgresStoredRevisionJobsRepository::connect(&cfg,context()?,None),Err(revision_service::RevisionError::InvalidRequest)),"LOOKUP_LEGACY23_REVISION_MUST_REJECT24")?;
    let cfg=LocalPostgresConfig::new(port()?,"postgres".into(),"p09_artifact_284".into(),value("P09_SQL23_ARTIFACT_PASSWORD")?)?;
    check(matches!(LocalPostgresMetadataRepository::connect_schema23(&cfg,tenant()?),Err(ArtifactError::InvalidState)),"LOOKUP_LEGACY23_ARTIFACT_MUST_REJECT24")?;
    row["state"]=json!("PASS_OWNED_EXACT_SCHEMA24_READONLY_LOOKUP_LEGACY23_DENIAL");row["migrations"]=json!(24);
    row["legacy23_constructors_reject24"]=json!(true);Ok(row)
}
fn cold_observation(negative_checks:bool)->Result<Value>{
    // No saved server state()/catalog handles()/full claim is read to perform this lookup.
    let wire=request()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,domain_ir::DocumentId::parse("actual-form-document")?)?;
    let prepared=Product::prepare_lookup_json(&provider,&wire)?;
    let StoredRequestObservation::Existing(observed)=prepared.observe(&provider)?else{return Err("LOOKUP_EXPECTED_EXISTING_JOB".into())};
    check(observed.outcome()==StoredJobOutcome::Replay&&observed.state()==StoredJobState::TerminalSuccess&&observed.attempt_no()==1
        &&observed.result_revision_id()==Some(revision(200)?),"LOOKUP_COLD_TERMINAL_OBSERVATION")?;
    check(revisions.head(&rc,project()?,branch()?)?==RevisionHead::new(Some(revision(200)?),2)?,"LOOKUP_PROVES_OLD_REQUEST_AFTER_HEAD_ADVANCE")?;
    if negative_checks{
        let mut changed:Value=serde_json::from_slice(&wire)?;changed["plan_id"]=json!("different-cold-request-plan");
        let changed=Product::prepare_lookup_json(&provider,&serde_json::to_vec(&changed)?)?;
        check(matches!(changed.observe(&provider),Err(CatalogRequestLookupError::Repository(StoredRequestLookupError::KeyConflict))),"LOOKUP_CHANGED_REQUEST_NOT_TYPED_CONFLICT")?;
        let mut missing:Value=serde_json::from_slice(&wire)?;missing["idempotency_key"]=json!("unclaimed-public-lookup-fixture");
        check(Product::prepare_lookup_json(&provider,&serde_json::to_vec(&missing)?)?.observe(&provider)?==StoredRequestObservation::NotObserved,"LOOKUP_MISSING_NOT_OBSERVED")?;
        check(prepared.observe(&provider)?==StoredRequestObservation::Existing(observed.clone()),"LOOKUP_RESTORE_PRESERVES_OBSERVATION")?;
    }
    Ok(json!({"state":"PASS_COLD_PUBLIC_REQUEST_LOOKUP_WITHOUT_IMPORT_COMPILER_OR_SAVED_CLAIM","old_request_head":1,"current_head":2,
        "cold_lookup":true,"typed_changed_request_conflict":negative_checks,"missing_is_not_observed":negative_checks,
        "lookup_grants_execution_or_full_readback_qualification":false,"claim_or_lease_or_retry_or_CAS_called_by_lookup":false}))
}
fn denied()->Result<Value>{let wire=request()?;let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);
    let provider=StoredFormProvider::bind(&a,&revisions,&ctx,&rc,project()?,branch()?,domain_ir::DocumentId::parse("actual-form-document")?)?;
    let prepared=Product::prepare_lookup_json(&provider,&wire)?;
    check(matches!(prepared.observe(&provider),Err(CatalogRequestLookupError::Repository(StoredRequestLookupError::Repository(revision_service::RevisionError::InvalidRequest)))),"LOOKUP_CURRENT_SQL_ACL_NOT_DENIED")?;
    Ok(json!({"state":"PASS_COLD_LOOKUP_CURRENT_SQL_ACL_DENIAL","claim_or_execution_attempted":false,"raw_backend_values":false}))}
pub(super) fn run(mode:&str)->Result<Value>{owned_root()?;match mode{
    "--fixture"=>install(),
    "--execute"=>{let mut result=catalog::run(mode)?;check(result["state"].as_str().is_some_and(|s|s.starts_with("PASS_")),"LOOKUP_FIXTURE_EXECUTION_FAILED")?;
        let observation=cold_observation(true)?;result["cold_request_lookup"]=observation;Ok(result)},
    "--restart-registered"=>{let observation=cold_observation(false)?;let mut readback=catalog::run(mode)?;readback["cold_request_lookup"]=observation;Ok(readback)},
    "--lookup-denied"=>denied(),"--lookup-restored"=>cold_observation(false),
    _=>catalog::run(mode)}}
