//! Owned PG18 SQL23 fixture/admission probe, NOT product/Native/worker or CAS qualification.
//! Secrets enter via process-local environment and never appear in JSON/errors/arguments/files.
use artifact_service::{ArtifactError,ArtifactId,ArtifactMetadataRepository,ContentDigest,LocalPostgresConfig,
    LocalPostgresMetadataRepository,SubjectDigest,TenantId};
use revision_service::{BranchId,ProjectId,RevisionError,RevisionRepository,RevisionRequestContext,
    postgres::{LocalPostgresRevisionConfig,source_formula_policy::issuer_registry::stored_revision_jobs::LocalPostgresStoredRevisionJobsRepository}};
use postgres::{Client,Config,NoTls};
use serde_json::{json,Value};
use std::{env,path::Path,time::Duration};
use uuid::Uuid;
type Result<T>=std::result::Result<T,&'static str>;
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
const ROLES:&str=include_str!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../tools/p09/fixtures/sql23_service_roles.sql"));
const SEED:&str=include_str!(concat!(env!("CARGO_MANIFEST_DIR"),"/../../tools/p09/fixtures/postgres_revision_adapter.sql"));
fn value(name:&str)->Result<String>{env::var(name).map_err(|_|"PROBE_ENV_MISSING")}
fn port()->Result<u16>{let p=value("P09_SQL23_PORT")?.parse::<u16>().map_err(|_|"PROBE_PORT")?;if p==0{return Err("PROBE_PORT");}Ok(p)}
fn tenant(n:u128)->Result<TenantId>{TenantId::new(Uuid::from_u128(n)).map_err(|_|"PROBE_TENANT")}
fn raw(user:&str,password:&str)->Result<Client>{Config::new().host("127.0.0.1").port(port()?).dbname("postgres").user(user).password(password)
    .connect_timeout(Duration::from_secs(3)).options("-c statement_timeout=5000 -c lock_timeout=1000 -c search_path=pg_catalog")
    .connect(NoTls).map_err(|_|"PROBE_TRANSPORT")}
fn owned_admin()->Result<Client>{
    let mut client=raw(&value("P09_SQL23_ADMIN_USER")?,&value("P09_SQL23_ADMIN_PASSWORD")?)?;
    let current:String=client.query_one("SELECT current_setting('data_directory')",&[]).map_err(|_|"FIXTURE_IDENTITY_QUERY")?.try_get(0).map_err(|_|"FIXTURE_IDENTITY_DECODE")?;
    let expected=value("P09_SQL23_OWNED_DATA")?;
    let allowed=Path::new("D:/devdata/hwpx-agent-p09-pg18-role-284/cluster/data");
    if !expected.is_ascii()||!Path::new(&expected).is_absolute()||std::fs::canonicalize(current).map_err(|_|"FIXTURE_CURRENT_PATH")?
        !=std::fs::canonicalize(&expected).map_err(|_|"FIXTURE_EXPECTED_PATH")?
        ||std::fs::canonicalize(expected).map_err(|_|"FIXTURE_EXPECTED_PATH")?!=std::fs::canonicalize(allowed).map_err(|_|"FIXTURE_ALLOWED_PATH")?{return Err("FIXTURE_NOT_OWNED_DATABASE");}
    Ok(client)
}
fn claim_body(fault:bool)->Result<Value>{
    let mut client=owned_admin()?;let source=std::str::from_utf8(MIGRATIONS[22]).map_err(|_|"FIXTURE_UTF8")?;
    let start=source.find("CREATE FUNCTION hwpx_agent.claim_stored_revision_job_v1(").ok_or("FIXTURE_CLAIM_SOURCE")?;
    let tail=&source[start..];let end=tail.find("$$;").ok_or("FIXTURE_CLAIM_END")?+3;
    let mut sql=tail[..end].replacen("CREATE FUNCTION","CREATE OR REPLACE FUNCTION",1);
    if fault{sql=sql.replacen("AS $$","AS $$\n-- owned body hash negative case\n",1);}
    client.batch_execute(&sql).map_err(|_|"FIXTURE_CLAIM_BODY_MUTATION")?;
    Ok(json!({"state":"PASS_OWNED_CLAIM_BODY_MUTATION","fault":fault,"actual_product_worker_or_CAS":false}))
}
fn fixture()->Result<Value>{
    let mut client=owned_admin()?;
    for(index,source)in MIGRATIONS.into_iter().enumerate(){
        let sql=std::str::from_utf8(source).map_err(|_|"FIXTURE_UTF8")?;
        // Simple-query transport preserves the exact compiled SQL body bytes, including CRLF.
        if let Err(error)=client.batch_execute(&format!("SELECT set_config('hwpx_agent.migration_sha256','{}',false);\n{sql}",ContentDigest::of(source).hex())){
            return Ok(json!({"state":"FAILED_OWNED_FIXTURE_MIGRATION","migration":index+1,"sqlstate":error.code().map(postgres::error::SqlState::code),"raw_backend_details":false}));
        }
    }
    client.batch_execute(ROLES).map_err(|_|"FIXTURE_ROLES")?;
    client.batch_execute(SEED).map_err(|_|"FIXTURE_SEED_A")?;
    let other=SEED.replace("00000000-0000-0000-0000-000000000001","00000000-0000-0000-0000-000000000101")
        .replace("00000000000000000000000000000001","00000000000000000000000000000101")
        .replace("p09-revision-probe","p09-revision-probe-b");
    client.batch_execute(&other).map_err(|_|"FIXTURE_SEED_B")?;
    Ok(json!({"state":"PASS_OWNED_SQL23_FIXTURE_LOADED","migrations":23,"synthetic_tenants":2,"application_role_passwords_set":false,
        "actual_product_worker_or_CAS":false}))
}
fn behavior(artifacts:&LocalPostgresMetadataRepository,revisions:&LocalPostgresStoredRevisionJobsRepository)->Result<usize>{
    let t=tenant(1)?;let other=tenant(0x101)?;let source=ArtifactId::parse(&format!("art_{}",Uuid::from_u128(11).simple())).map_err(|_|"READ_ARTIFACT_ID")?;
    if artifacts.find(t,source).map_err(|_|"READ_OWN_ARTIFACT")?.is_none(){return Err("READ_OWN_ARTIFACT_ABSENT");}
    if !matches!(artifacts.find(other,source),Err(ArtifactError::NotFound)){return Err("READ_FOREIGN_TENANT_NOT_DENIED");}
    let project=ProjectId::parse(&format!("prj_{}",Uuid::from_u128(2).simple())).map_err(|_|"READ_PROJECT")?;
    let branch=BranchId::parse(&format!("brn_{}",Uuid::from_u128(3).simple())).map_err(|_|"READ_BRANCH")?;
    let head=revisions.head(t,project,branch).map_err(|_|"READ_OWN_HEAD")?;
    if head.generation()!=0||head.revision_id().is_some(){return Err("READ_OWN_HEAD_MISMATCH");}
    if !matches!(revisions.head(other,project,branch),Err(RevisionError::NotFound)){return Err("READ_FOREIGN_REVISION_TENANT_NOT_DENIED");}
    let foreign=RevisionRequestContext::new(t,SubjectDigest::parse(&"b".repeat(64)).map_err(|_|"READ_SUBJECT")?);
    if !matches!(revisions.authorize_context(&foreign),Err(RevisionError::NotFound)){return Err("READ_FOREIGN_SUBJECT_NOT_DENIED");}
    let mut direct=raw("p09_artifact_284",&value("P09_SQL23_ARTIFACT_PASSWORD")?)?;
    direct.batch_execute("BEGIN; SET LOCAL hwpx_agent.tenant_id='00000000-0000-0000-0000-000000000001';").map_err(|_|"RLS_BEGIN")?;
    let counts=direct.query_one("SELECT count(*)::bigint AS own,count(*) FILTER(WHERE tenant_id='00000000-0000-0000-0000-000000000101')::bigint AS foreign FROM hwpx_agent.artifacts",&[]).map_err(|_|"RLS_QUERY")?;
    let own:i64=counts.try_get("own").map_err(|_|"RLS_DECODE")?;let foreign:i64=counts.try_get("foreign").map_err(|_|"RLS_DECODE")?;
    if own!=5||foreign!=0{return Err("RLS_REAL_FOREIGN_ROWS_NOT_HIDDEN");}
    direct.batch_execute("ROLLBACK").map_err(|_|"RLS_ROLLBACK")?;
    Ok(6)
}
fn run(mode:&str)->Result<Value>{
    if mode=="--fixture-load"{return fixture();}
    if mode=="--claim-body-fault"{return claim_body(true);}
    if mode=="--claim-body-restore"{return claim_body(false);}
    if !matches!(mode,"--baseline"|"--artifact-denied"|"--revision-denied"|"--both-denied"|"--behavior"){return Err("PROBE_CLOSED_MODE");}
    let t=tenant(1)?;let subject=SubjectDigest::parse(&"a".repeat(64)).map_err(|_|"PROBE_SUBJECT")?;
    let ac=LocalPostgresConfig::new(port()?,"postgres".into(),"p09_artifact_284".into(),value("P09_SQL23_ARTIFACT_PASSWORD")?).map_err(|_|"ARTIFACT_CONFIG")?;
    let rc=LocalPostgresRevisionConfig::new(port()?,"postgres".into(),"p09_revision_284".into(),value("P09_SQL23_REVISION_PASSWORD")?).map_err(|_|"REVISION_CONFIG")?;
    let artifact=LocalPostgresMetadataRepository::connect_schema23_diagnosed(&ac,t);
    let revision=LocalPostgresStoredRevisionJobsRepository::connect(&rc,RevisionRequestContext::new(t,subject),None);
    let a=artifact.is_ok();let r=revision.is_ok();let expected=match mode{"--artifact-denied"=>(false,true),"--revision-denied"=>(true,false),"--both-denied"=>(false,false),_=>(true,true)};
    let mut result=json!({"state":if(a,r)==expected{"PASS_SQL23_PROFILE_EXPECTATION"}else{"FAILED_SQL23_PROFILE_EXPECTATION"},"mode":mode,
        "artifact_admitted":a,"revision_admitted":r,"artifact_failure_stage":artifact.as_ref().err().map(|e|e.stage().code()),
        "artifact_error_code":artifact.as_ref().err().map(|e|e.error().code()),"revision_error_code":revision.as_ref().err().map(RevisionError::code),
        "actual_product_worker_or_CAS":false});
    if mode=="--behavior"&&a&&r{result["actual_metadata_scope_checks"]=json!(behavior(artifact.as_ref().map_err(|_|"ARTIFACT_ADMISSION")?,revision.as_ref().map_err(|_|"REVISION_ADMISSION")?)?);}
    Ok(result)
}
fn main(){
    let result=env::args().nth(1).ok_or("PROBE_MODE_MISSING").and_then(|mode|run(&mode));
    let value=match result{Ok(v)=>v,Err(code)=>json!({"state":"FAILED_SQL23_PROBE","error_code":code,"raw_backend_details":false})};
    println!("{value}");if !value["state"].as_str().is_some_and(|s|s.starts_with("PASS_")){std::process::exit(2);}
}
