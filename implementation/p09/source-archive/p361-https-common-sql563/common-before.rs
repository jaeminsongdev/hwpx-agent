//! Actual disk AEAD + PostgreSQL23 registered job CAS. Synthetic route/bytes/scanner/validator.
//! Never a P09 route, target qualification or Native execution permit.
#[path="sql23_storage/setup.rs"] mod setup;
#[path="sql23_storage/pipeline.rs"] mod pipeline;
#[path="sql23_storage/catalog.rs"] mod catalog;
#[path="sql23_storage/lookup24.rs"] mod lookup24;
#[path="sql23_storage/archived_recovery.rs"]mod archived_recovery;
#[path="sql23_storage/public_request_recovery.rs"]mod public_request_recovery;
#[path="sql23_storage/search_request_recovery.rs"]mod search_request_recovery;
#[path="sql23_storage/https_target_recovery.rs"]mod https_target_recovery;
#[cfg(windows)]#[path="sql23_storage/windows_custody.rs"]mod windows_custody;
#[path="../tests/support/stored_commit_manifest.rs"] mod manifest_fixture;
use artifact_service::*;
use hwpx_agent_cli::stored_revision_commit::{*,job::*};
use operation_engine::{ExecutionManifest,ValidationOutcome,TransactionState};
use revision_service::{BranchId,CommitId,CommitOutcome,ProjectId,RevisionCommitRequest,RevisionHead,RevisionId,
    RevisionRequestContext,RevisionService,RevisionValidationState,
    postgres::{LocalPostgresRevisionConfig,RevisionLeaseIdentity,
    source_formula_policy::issuer_registry::stored_revision_jobs::{LocalPostgresStoredRevisionJobsRepository,StoredJobLease,
        StoredCommitIntentLookup,StoredRevisionJobRepository,lifecycle::{StoredJobLifecycleRepository,StoredJobOutcome,StoredJobState}}}};
use serde_json::{json,Value};
use sha2::{Digest as _,Sha256};
use std::{env,error::Error,fs,path::PathBuf,time::Duration};
use postgres::{Client,Config,NoTls};
use uuid::Uuid;
type Result<T,E=Box<dyn Error>>=std::result::Result<T,E>;
const ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-storage-298";
const CATALOG_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-catalog-447";
const IDENTITY_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-catalog-identity-450";
const LOOKUP_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-catalog-lookup-457";
const CUSTODY_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-public-request-recovery-472";
const SEARCH_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-search-recovery-519";
const HTTPS_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-target-537";
const HTTPS_POLICY_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-policy-541";
const HTTPS_ATOMIC_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-atomic-543";
const HTTPS_LATE_REVOKE_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-late-revoke-545";
static HTTPS_LATE_REVOKE_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static HTTPS_ATOMIC_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static HTTPS_POLICY_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static HTTPS_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static SEARCH_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static PUBLIC_RECOVERY_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static CUSTODY_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static LOOKUP_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static IDENTITY_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
static CATALOG_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);
const PROFILE:&str="storage-synthetic";
const PRIOR:&[u8]=b"synthetic bootstrap source, not HWPX";
const SOURCE:&[u8]=b"synthetic retained original, not HWPX";
const OUTPUT:&[u8]=b"synthetic deterministic candidate, not HWPX";
struct StoredFixture{head:RevisionHead,result:ArtifactId}
fn id(n:u128)->Uuid{Uuid::from_u128(n)}
fn check(ok:bool,code:&'static str)->Result<()>{if ok{Ok(())}else{Err(code.into())}}
fn value(name:&str)->Result<String>{Ok(env::var(name)?)}
fn tenant()->Result<TenantId>{Ok(TenantId::new(id(1))?)}
fn subject()->Result<SubjectDigest>{Ok(SubjectDigest::parse(&"a".repeat(64))?)}
fn project()->Result<ProjectId>{Ok(ProjectId::parse(&format!("prj_{}",id(2).simple()))?)}
fn branch()->Result<BranchId>{Ok(BranchId::parse(&format!("brn_{}",id(3).simple()))?)}
fn revision(n:u128)->Result<RevisionId>{Ok(RevisionId::parse(&format!("rev_{}",id(n).simple()))?)}
fn commit(n:u128)->Result<CommitId>{Ok(CommitId::parse(&format!("cmt_{}",id(n).simple()))?)}
fn port()->Result<u16>{let p=value("P09_SQL23_PORT")?.parse()?;check(p!=0,"STORAGE_PORT")?;Ok(p)}
fn context()->Result<RevisionRequestContext>{Ok(RevisionRequestContext::new(tenant()?,subject()?))}
fn actor()->Result<RequestContext>{Ok(RequestContext::new(tenant()?,subject()?,[AuthScope::DocumentRead,AuthScope::DocumentWrite]))}
fn raw(user:&str,password:&str)->Result<Client>{Ok(Config::new().host("127.0.0.1").port(port()?).dbname("postgres").user(user).password(password)
    .connect_timeout(Duration::from_secs(3)).options("-c statement_timeout=5000 -c lock_timeout=1000 -c search_path=pg_catalog").connect(NoTls)?)}
fn scoped(c:&mut Client)->Result<()>{c.query_one("SELECT set_config('hwpx_agent.tenant_id',$1,false),set_config('hwpx_agent.subject_sha256',$2,false)",
    &[&id(1).to_string(),&subject()?.hex()])?;Ok(())}
fn owned_root()->Result<PathBuf>{
    let root=PathBuf::from(if HTTPS_LATE_REVOKE_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_LATE_REVOKE_ROOT}else if HTTPS_ATOMIC_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_ATOMIC_ROOT}else if HTTPS_POLICY_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_POLICY_ROOT}else if HTTPS_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_ROOT}else if SEARCH_MODE.load(std::sync::atomic::Ordering::Relaxed){SEARCH_ROOT}else if CUSTODY_MODE.load(std::sync::atomic::Ordering::Relaxed){CUSTODY_ROOT}else if LOOKUP_MODE.load(std::sync::atomic::Ordering::Relaxed){LOOKUP_ROOT}else if IDENTITY_MODE.load(std::sync::atomic::Ordering::Relaxed){IDENTITY_ROOT}else if CATALOG_MODE.load(std::sync::atomic::Ordering::Relaxed){CATALOG_ROOT}else{ROOT});
    for p in root.ancestors(){let m=fs::symlink_metadata(p)?;check(m.is_dir()&&!m.file_type().is_symlink(),"STORAGE_OWNER_PATH")?;
        #[cfg(windows)] {use std::os::windows::fs::MetadataExt;check(m.file_attributes()&0x400==0,"STORAGE_OWNER_REPARSE")?;}}
    Ok(root)
}
fn repository()->Result<LocalPostgresStoredRevisionJobsRepository>{let config=LocalPostgresRevisionConfig::new(port()?,"postgres".into(),"p09_revision_284".into(),value("P09_SQL23_REVISION_PASSWORD")?)?;
    Ok(if HTTPS_ATOMIC_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresStoredRevisionJobsRepository::connect_with_atomic_https_policy(&config,context()?,None)?}
        else if HTTPS_POLICY_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&config,context()?,None)?}
        else if LOOKUP_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresStoredRevisionJobsRepository::connect_with_request_lookup(&config,context()?,None)?}
        else{LocalPostgresStoredRevisionJobsRepository::connect(&config,context()?,None)?})}
#[derive(Debug)]struct SyntheticScanner;
impl ArtifactScanner for SyntheticScanner{fn scan(&self,_:ScanRequest<'_>)->std::result::Result<ScanEvidence,ArtifactError>{
    Ok(ScanEvidence{verdict:ScanVerdict::Clean,engine:ScannerReference::parse("scanner.synthetic-storage")?,signature_version:ScannerSignatureVersion::parse("not-native-v1")?})}}
type Artifacts=ArtifactService<LocalPostgresMetadataRepository,LocalEncryptedBlobStore,SyntheticScanner>;
fn artifact_crypto()->Result<(Aes256GcmKeyring,DownloadSigner)>{
    #[cfg(windows)]if CUSTODY_MODE.load(std::sync::atomic::Ordering::Relaxed){return windows_custody::crypto();}
    let key:[u8;32]=hex::decode(value("P09_STORAGE_AES_HEX")?)?.try_into().map_err(|_|"STORAGE_KEY_LENGTH")?;
    let signing=hex::decode(value("P09_STORAGE_HMAC_HEX")?)?;check(signing.len()==32,"STORAGE_SIGNING_LENGTH")?;
    let reference=KeyReference::parse("fixture.storage-aes")?;
    Ok((Aes256GcmKeyring::new(reference.clone(),[(reference,key)])?,
        DownloadSigner::new("https://fixture.example.test/storage",KeyReference::parse("fixture.storage-hmac")?,&signing,60)?))
}
fn artifacts()->Result<Artifacts>{
    let(keyring,signer)=artifact_crypto()?;
    let config=LocalPostgresConfig::new(port()?,"postgres".into(),"p09_artifact_284".into(),value("P09_SQL23_ARTIFACT_PASSWORD")?)?;
    let metadata=if HTTPS_ATOMIC_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresMetadataRepository::connect_schema26(&config,tenant()?)?}
        else if HTTPS_POLICY_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresMetadataRepository::connect_schema25(&config,tenant()?)?}
        else if LOOKUP_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresMetadataRepository::connect_schema24(&config,tenant()?)?}
        else{LocalPostgresMetadataRepository::connect_schema23(&config,tenant()?)?};
    Ok(ArtifactService::new(metadata,
        LocalEncryptedBlobStore::create(owned_root()?.join("blobs"),32*1024*1024+16)?,SyntheticScanner,
        keyring,signer,ArtifactServiceConfig::new(32*1024*1024,60)?))
}
fn ingest(a:&Artifacts,bytes:&[u8],kind:ArtifactKind,media:&str,name:&str)->Result<ArtifactDescriptor>{Ok(a.ingest(&actor()?,IngestRequest{
    bytes:bytes.to_vec(),kind,media_type:MediaType::parse(media)?,file_name:FileName::parse(name)?},10)?)}
fn state_path()->Result<PathBuf>{Ok(owned_root()?.join("retained-receipts.json"))}
fn state()->Result<Value>{let path=state_path()?;let m=fs::symlink_metadata(&path)?;
    check(m.is_file()&&!m.file_type().is_symlink()&&m.len()<=16384,"STORAGE_STATE_BOUND")?;Ok(serde_json::from_slice(&fs::read(path)?)?)}
fn save(state:&Value)->Result<()>{use std::io::Write;let bytes=serde_json::to_vec(state)?;check(bytes.len()<=16384,"STORAGE_STATE_BOUND")?;
    let mut f=fs::OpenOptions::new().write(true).create_new(true).open(state_path()?)?;f.write_all(&bytes)?;f.sync_all()?;Ok(())}
fn read_id(state:&Value,name:&str)->Result<ArtifactId>{Ok(ArtifactId::parse(state[name].as_str().ok_or("STORAGE_STATE_ID")?)?)}
fn run(mode:&str)->Result<Value>{owned_root()?;match mode{
    "--fixture"=>setup::fixture(),"--seed"=>setup::seed(),"--execute"=>pipeline::execute(),"--restart-observe"=>pipeline::restart(),
    "--restart-registered"=>pipeline::restart_registered(),"--wrong-key"=>pipeline::wrong_key(),_=>Err("STORAGE_CLOSED_MODE".into())}}
fn main(){let mode=env::args().nth(1).unwrap_or_default();finish(run(&mode),&mode)}
pub fn search_request_recovery_main(){SEARCH_MODE.store(true,std::sync::atomic::Ordering::Relaxed);LOOKUP_MODE.store(true,std::sync::atomic::Ordering::Relaxed);
    let mode=env::args().nth(1).unwrap_or_default();finish(search_request_recovery::run(&mode),&mode)}
pub fn https_target_recovery_main(){HTTPS_MODE.store(true,std::sync::atomic::Ordering::Relaxed);LOOKUP_MODE.store(true,std::sync::atomic::Ordering::Relaxed);
    let mode=env::args().nth(1).unwrap_or_default();finish(https_target_recovery::run(&mode),&mode)}
pub fn https_policy_recovery_main(){HTTPS_POLICY_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_target_recovery_main()}
pub fn https_atomic_recovery_main(){HTTPS_ATOMIC_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_policy_recovery_main()}
pub fn https_late_revoke_main(){HTTPS_LATE_REVOKE_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_atomic_recovery_main()}
pub fn catalog_main(){CATALOG_MODE.store(true,std::sync::atomic::Ordering::Relaxed);let mode=env::args().nth(1).unwrap_or_default();finish(catalog::run(&mode),&mode)}
pub fn identity_main(){IDENTITY_MODE.store(true,std::sync::atomic::Ordering::Relaxed);catalog_main()}
pub fn lookup_main(){LOOKUP_MODE.store(true,std::sync::atomic::Ordering::Relaxed);IDENTITY_MODE.store(true,std::sync::atomic::Ordering::Relaxed);
    let mode=env::args().nth(1).unwrap_or_default();finish(lookup24::run(&mode),&mode)}
#[cfg(windows)]pub fn public_request_recovery_main(){PUBLIC_RECOVERY_MODE.store(true,std::sync::atomic::Ordering::Relaxed);windows_custody_main()}
#[cfg(windows)]pub fn windows_custody_main(){CUSTODY_MODE.store(true,std::sync::atomic::Ordering::Relaxed);
    LOOKUP_MODE.store(true,std::sync::atomic::Ordering::Relaxed);IDENTITY_MODE.store(true,std::sync::atomic::Ordering::Relaxed);
    let mode=env::args().nth(1).unwrap_or_default();finish(windows_custody::run(&mode),&mode)}
fn finish(result:Result<Value>,mode:&str){
    let row=match result{Ok(v)=>v,Err(error)=>{let text=error.to_string();let code=if text.len()<=100&&text.bytes().all(|b|b.is_ascii_uppercase()||b.is_ascii_digit()||b==b'_'){text.as_str()}else{"STORAGE_CLOSED_FAILURE"};
        let sql_hint=error.downcast_ref::<postgres::Error>().and_then(postgres::Error::as_db_error).and_then(|e|if e.message()=="artifact ACL must retain at least one manager"{Some("LAST_ARTIFACT_MANAGER_REQUIRED")}else if e.constraint()==Some("project_acl_role_value"){Some("INVALID_PROJECT_ROLE_LITERAL")}else{None});
        json!({"state":"FAILED_SQL23_STORAGE_PROBE","stage":mode,"error_code":code,"sqlstate":error.downcast_ref::<postgres::Error>().and_then(|e|e.code()).map(postgres::error::SqlState::code),
            "sql_hint":sql_hint,"policy_phase":if HTTPS_POLICY_MODE.load(std::sync::atomic::Ordering::Relaxed){Some(https_target_recovery::policy_fixture_phase())}else{None},
            "artifact_error":error.downcast_ref::<ArtifactError>().map(ArtifactError::code),"revision_error":error.downcast_ref::<revision_service::RevisionError>().map(revision_service::RevisionError::code),"raw_details":false})}};
    println!("{row}");if !row["state"].as_str().is_some_and(|s|s.starts_with("PASS_")){std::process::exit(2);}}
