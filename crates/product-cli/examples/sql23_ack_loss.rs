//! Real DB/AEAD effects with synthetic application acknowledgement loss, not a network fault.
//! Original storage/engine/SQL code is unchanged. No qualified P09/Native route is opened.
#[path="sql23_ack_loss/setup.rs"] mod setup;
#[path="sql23_ack_loss/repository.rs"] mod fault_repository;
#[path="sql23_ack_loss/campaign.rs"] mod campaign;
#[path="../tests/support/stored_commit_manifest.rs"] mod manifest_fixture;
use artifact_service::*;
use hwpx_agent_cli::stored_revision_commit::{*,job::*};
use operation_engine::{ExecutionManifest,ValidationOutcome,TransactionState,ArtifactDisposition};
use revision_service::{BranchId,CommitId,CommitOutcome,ProjectId,RevisionCommitRequest,RevisionHead,RevisionId,RevisionNode,RevisionRepository,
    RevisionRequestContext,RevisionService,RevisionValidationState,RevisionError,
    postgres::{LocalPostgresRevisionConfig,RevisionLeaseIdentity,
    source_formula_policy::issuer_registry::stored_revision_jobs::{LocalPostgresStoredRevisionJobsRepository,StoredJobLease,
        StoredCommitRegistration,StoredCommitIntentRecord,StoredCommitIntentLookup,StoredRevisionJobRepository,
        lifecycle::{StoredJobLifecycleRepository,StoredJobClaim,StoredJobObservation,StoredJobAdvance,StoredJobOutcome,StoredJobState}}}};
use serde_json::{json,Value};
use sha2::{Digest as _,Sha256};
use std::{env,error::Error,fs,path::PathBuf,time::Duration,sync::{Arc,atomic::{AtomicBool,AtomicUsize,Ordering}}};
use postgres::{Client,Config,NoTls};
use uuid::Uuid;
type Result<T,E=Box<dyn Error>>=std::result::Result<T,E>;
const ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-ack-295";
const PROFILE:&str="storage-synthetic";
const PRIOR:&[u8]=b"synthetic bootstrap source, not HWPX";
const SOURCE:&[u8]=b"synthetic retained original, not HWPX";
const OUTPUT:&[u8]=b"synthetic deterministic candidate, not HWPX";
struct StoredFixture{head:RevisionHead,result:ArtifactId}
fn id(n:u128)->Uuid{Uuid::from_u128(if n!=1{n}else{match env::var("P09_ACK_CASE").as_deref(){Ok("register_after")=>1,Ok("cas_before")=>0x101,
    Ok("cas_after")=>0x201,Ok("complete_after")=>0x301,_=>0}})}
fn check(ok:bool,code:&'static str)->Result<()>{if ok{Ok(())}else{Err(code.into())}}
fn value(name:&str)->Result<String>{Ok(env::var(name)?)}
fn case()->Result<String>{let s=value("P09_ACK_CASE")?;check(matches!(s.as_str(),"register_after"|"cas_before"|"cas_after"|"complete_after"),"ACK_CLOSED_CASE")?;Ok(s)}
fn tenant()->Result<TenantId>{Ok(TenantId::new(id(1))?)}
fn subject()->Result<SubjectDigest>{Ok(SubjectDigest::parse(&"a".repeat(64))?)}
fn project()->Result<ProjectId>{Ok(ProjectId::parse(&format!("prj_{}",id(2).simple()))?)}
fn branch()->Result<BranchId>{Ok(BranchId::parse(&format!("brn_{}",id(3).simple()))?)}
fn revision(n:u128)->Result<RevisionId>{Ok(RevisionId::parse(&format!("rev_{}",id(n).simple()))?)}
fn commit(n:u128)->Result<CommitId>{Ok(CommitId::parse(&format!("cmt_{}",id(n).simple()))?)}
fn port()->Result<u16>{let p=value("P09_SQL23_PORT")?.parse()?;check(p!=0,"ACK_PORT")?;Ok(p)}
fn context()->Result<RevisionRequestContext>{Ok(RevisionRequestContext::new(tenant()?,subject()?))}
fn actor()->Result<RequestContext>{Ok(RequestContext::new(tenant()?,subject()?,[AuthScope::DocumentRead,AuthScope::DocumentWrite]))}
fn raw(user:&str,password:&str)->Result<Client>{Ok(Config::new().host("127.0.0.1").port(port()?).dbname("postgres").user(user).password(password)
    .connect_timeout(Duration::from_secs(3)).options("-c statement_timeout=5000 -c lock_timeout=1000 -c search_path=pg_catalog").connect(NoTls)?)}
fn scoped(c:&mut Client)->Result<()>{c.query_one("SELECT set_config('hwpx_agent.tenant_id',$1,false),set_config('hwpx_agent.subject_sha256',$2,false)",
    &[&id(1).to_string(),&subject()?.hex()])?;Ok(())}
fn common_root()->Result<PathBuf>{let root=PathBuf::from(ROOT);
    for p in root.ancestors(){let m=fs::symlink_metadata(p)?;check(m.is_dir()&&!m.file_type().is_symlink(),"ACK_OWNER_PATH")?;
        #[cfg(windows)]{use std::os::windows::fs::MetadataExt;check(m.file_attributes()&0x400==0,"ACK_OWNER_REPARSE")?;}}
    Ok(root)}
fn owned_root()->Result<PathBuf>{let root=common_root()?.join(case()?);let m=fs::symlink_metadata(&root)?;
    check(m.is_dir()&&!m.file_type().is_symlink(),"ACK_CASE_OWNER")?;
    #[cfg(windows)]{use std::os::windows::fs::MetadataExt;check(m.file_attributes()&0x400==0,"ACK_CASE_OWNER_REPARSE")?;}Ok(root)}
fn repository()->Result<LocalPostgresStoredRevisionJobsRepository>{Ok(LocalPostgresStoredRevisionJobsRepository::connect(
    &LocalPostgresRevisionConfig::new(port()?,"postgres".into(),"p09_revision_284".into(),value("P09_SQL23_REVISION_PASSWORD")?)?,context()?,None)?)}
#[derive(Debug)]struct SyntheticScanner;
impl ArtifactScanner for SyntheticScanner{fn scan(&self,_:ScanRequest<'_>)->std::result::Result<ScanEvidence,ArtifactError>{
    Ok(ScanEvidence{verdict:ScanVerdict::Clean,engine:ScannerReference::parse("scanner.synthetic-storage")?,signature_version:ScannerSignatureVersion::parse("not-native-v1")?})}}
type Artifacts=ArtifactService<LocalPostgresMetadataRepository,LocalEncryptedBlobStore,SyntheticScanner>;
fn artifacts()->Result<Artifacts>{let key:[u8;32]=hex::decode(value("P09_STORAGE_AES_HEX")?)?.try_into().map_err(|_|"ACK_KEY_LENGTH")?;
    let signing=hex::decode(value("P09_STORAGE_HMAC_HEX")?)?;check(signing.len()==32,"ACK_SIGNING_LENGTH")?;let reference=KeyReference::parse("fixture.storage-aes")?;
    Ok(ArtifactService::new(LocalPostgresMetadataRepository::connect_schema23(&LocalPostgresConfig::new(port()?,"postgres".into(),"p09_artifact_284".into(),value("P09_SQL23_ARTIFACT_PASSWORD")?)?,tenant()?)?,
        LocalEncryptedBlobStore::create(owned_root()?.join("blobs"),32*1024*1024+16)?,SyntheticScanner,Aes256GcmKeyring::new(reference.clone(),[(reference,key)])?,
        DownloadSigner::new("https://fixture.example.test/storage",KeyReference::parse("fixture.storage-hmac")?,&signing,60)?,ArtifactServiceConfig::new(32*1024*1024,60)?))}
fn ingest(a:&Artifacts,bytes:&[u8],kind:ArtifactKind,media:&str,name:&str)->Result<ArtifactDescriptor>{Ok(a.ingest(&actor()?,IngestRequest{
    bytes:bytes.to_vec(),kind,media_type:MediaType::parse(media)?,file_name:FileName::parse(name)?},10)?)}
fn state_path()->Result<PathBuf>{Ok(owned_root()?.join("retained-receipts.json"))}
fn state()->Result<Value>{let path=state_path()?;let m=fs::symlink_metadata(&path)?;check(m.is_file()&&!m.file_type().is_symlink()&&m.len()<=16384,"ACK_STATE_BOUND")?;
    Ok(serde_json::from_slice(&fs::read(path)?)?)}
fn save(s:&Value)->Result<()>{use std::io::Write;let bytes=serde_json::to_vec(s)?;check(bytes.len()<=16384,"ACK_STATE_BOUND")?;
    let mut f=fs::OpenOptions::new().write(true).create_new(true).open(state_path()?)?;f.write_all(&bytes)?;f.sync_all()?;Ok(())}
fn read_id(s:&Value,name:&str)->Result<ArtifactId>{Ok(ArtifactId::parse(s[name].as_str().ok_or("ACK_STATE_ID")?)?)}
fn run(mode:&str)->Result<Value>{owned_root()?;match mode{"--fixture"=>setup::fixture(),"--provision"=>setup::provision(),"--seed"=>setup::seed(),"--execute-loss"=>campaign::execute(),
    "--recover"=>campaign::recover(),_=>Err("ACK_CLOSED_MODE".into())}}
fn main(){let mode=env::args().nth(1).unwrap_or_default();let result=run(&mode);
    let row=match result{Ok(v)=>v,Err(error)=>{let text=error.to_string();let code=if text.len()<=100&&text.bytes().all(|b|b.is_ascii_uppercase()||b.is_ascii_digit()||b==b'_'){text.as_str()}else{"ACK_CLOSED_FAILURE"};
        json!({"state":"FAILED_SQL23_ACK_PROBE","mode":mode,"error_code":code,"sqlstate":error.downcast_ref::<postgres::Error>().and_then(|e|e.code()).map(postgres::error::SqlState::code),
            "artifact_error":error.downcast_ref::<ArtifactError>().map(ArtifactError::code),"revision_error":error.downcast_ref::<RevisionError>().map(RevisionError::code),"raw_details":false})}};
    println!("{row}");if !row["state"].as_str().is_some_and(|s|s.starts_with("PASS_")){std::process::exit(2);}}
