//! Actual SQL23 lifecycle against an owned DB. Synthetic metadata, not blob/Native qualification.
#[path = "p09_sql23_jobs/setup.rs"]
mod setup;
#[path = "p09_sql23_jobs/negative.rs"]
mod negative;
use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use postgres::{Client, Config, NoTls};
use revision_service::{BranchId, ProjectId, RevisionError, RevisionId, RevisionRepository, RevisionRequestContext,
    postgres::{LocalPostgresRevisionConfig, source_formula_policy::issuer_registry::stored_revision_jobs::{
        LocalPostgresStoredRevisionJobsRepository, StoredJobLease,
        lifecycle::{StoredJobAdvance, StoredJobClaim, StoredJobClaimInput, StoredJobLifecycleRepository, StoredJobOutcome, StoredJobState}}}};
use serde_json::{json, Value};
use std::{env, time::Duration};
use uuid::Uuid;
type Result<T> = std::result::Result<T, &'static str>;
const PROFILE: &str = "p09-storage-synthetic";
fn id(n: u128) -> Uuid { Uuid::from_u128(n) }
fn value(name: &str) -> Result<String> { env::var(name).map_err(|_| "JOB_ENV_MISSING") }
fn check(ok: bool, code: &'static str) -> Result<()> { if ok { Ok(()) } else { Err(code) } }
fn port() -> Result<u16> { let p = value("P09_SQL23_PORT")?.parse().map_err(|_| "JOB_PORT")?; check(p != 0, "JOB_PORT")?; Ok(p) }
fn raw(user: &str, password: &str) -> Result<Client> {
    Config::new().host("127.0.0.1").port(port()?).dbname("postgres").user(user).password(password)
        .connect_timeout(Duration::from_secs(3)).options("-c statement_timeout=5000 -c lock_timeout=1000 -c search_path=pg_catalog")
        .connect(NoTls).map_err(|_| "JOB_CONNECT")
}
fn context() -> Result<RevisionRequestContext> {
    Ok(RevisionRequestContext::new(TenantId::new(id(1)).map_err(|_| "JOB_TENANT")?,
        SubjectDigest::parse(&"a".repeat(64)).map_err(|_| "JOB_SUBJECT")?))
}
fn scoped(client: &mut Client) -> Result<()> {
    client.query_one("SELECT set_config('hwpx_agent.tenant_id',$1,false),set_config('hwpx_agent.subject_sha256',$2,false)",
        &[&id(1).to_string(), &"a".repeat(64)]).map_err(|_| "JOB_SCOPE")?; Ok(())
}
fn app_raw() -> Result<Client> { let mut c = raw("p09_revision_284", &value("P09_SQL23_REVISION_PASSWORD")?)?; scoped(&mut c)?; Ok(c) }
fn repository() -> Result<LocalPostgresStoredRevisionJobsRepository> {
    let c = LocalPostgresRevisionConfig::new(port()?, "postgres".into(), "p09_revision_284".into(), value("P09_SQL23_REVISION_PASSWORD")?)
        .map_err(|_| "JOB_CONFIG")?;
    LocalPostgresStoredRevisionJobsRepository::connect(&c, context()?, None).map_err(|_| "JOB_ADMISSION")
}
fn project() -> Result<ProjectId> { ProjectId::parse(&format!("prj_{}", id(2).simple())).map_err(|_| "JOB_PROJECT") }
fn branch() -> Result<BranchId> { BranchId::parse(&format!("brn_{}", id(3).simple())).map_err(|_| "JOB_BRANCH") }
fn artifact(n: u128) -> Result<ArtifactId> { ArtifactId::parse(&format!("art_{}", id(n).simple())).map_err(|_| "JOB_ARTIFACT") }
fn claim(repo: &LocalPostgresStoredRevisionJobsRepository) -> Result<StoredJobClaim> {
    let head = repo.head(context()?.tenant_id(), project()?, branch()?).map_err(|_| "JOB_HEAD")?;
    check(head.generation() == 1 && head.revision_id().map(RevisionId::as_uuid) == Some(id(20)), "JOB_SEALED_INITIAL_HEAD")?;
    StoredJobClaim::new(StoredJobClaimInput { project: project()?, branch: branch()?, expected_head: head,
        key: id(101), job: id(102), request: id(103), source: artifact(12)?,
        request_sha: ContentDigest::of(b"sql23-job-request"), manifest_sha: ContentDigest::of(b"sql23-job-manifest"),
        source_sha: ContentDigest::parse(&"2".repeat(64)).map_err(|_| "JOB_DIGEST")?, effect_sha: ContentDigest::of(b"synthetic-effect"),
        precommit_sha: ContentDigest::of(b"synthetic-precommit"), plan_sha: ContentDigest::of(b"synthetic-plan"),
        target_profile: PROFILE.into(), capability_sha: ContentDigest::of(b"synthetic-capability"),
        max_attempts: 3, base_delay_seconds: 1, max_delay_seconds: 4, ttl_seconds: 600 }).map_err(|_| "JOB_CLAIM_INPUT")
}
fn deny<T>(r: std::result::Result<T, RevisionError>, code: &'static str) -> Result<()> {
    // The adapter intentionally closes many backend codes to RepositoryFailure. Every case also
    // invokes the identical rejected request through negative.rs and requires its exact SQLSTATE.
    match r { Err(RevisionError::InvalidRequest | RevisionError::RepositoryFailure) => Ok(()),
        _ => Err(code) }
}
fn register(c: &mut Client, agent: u128, profile: &str, cap: &str, state: &str) -> Result<()> {
    let row = c.query_one("SELECT * FROM hwpx_agent.register_scheduler_worker($1,$2::character(64),$3,$4,$5::character(64),$6,300,$7::character(64))",
        &[&id(1), &"a".repeat(64), &id(agent), &profile, &cap, &state, &ContentDigest::of(b"register-event").hex()])
        .map_err(|_| "JOB_REGISTER_SQL")?;
    check(row.try_get::<_, Uuid>("returned_agent_instance_id").map_err(|_| "JOB_REGISTER_ROW")? == id(agent)
        && row.try_get::<_, String>("returned_state").map_err(|_| "JOB_REGISTER_ROW")? == state, "JOB_REGISTER_IDENTITY")
}
fn exercise() -> Result<Value> {
    let r = repository()?; let c = context()?; let input = claim(&r)?; let event = ContentDigest::of(b"job-event");
    let new = r.claim_job(&c, &input, event).map_err(|_| "JOB_CLAIM_SQL")?;
    check(new.outcome() == StoredJobOutcome::New && new.state() == StoredJobState::Claimed && new.attempt_no() == 0, "JOB_NEW_SHAPE")?;
    let mut checks = vec!["actual_new_claim"]; let mut sql = app_raw()?;
    let replay = r.claim_job(&c, &input, event).map_err(|_| "JOB_REPLAY_SQL")?;
    check(replay.outcome() == StoredJobOutcome::Replay && replay.attempt_no() == 0, "JOB_REPLAY_SHAPE")?; checks.push("exact_replay_without_attempt");
    let mut changed = input.input().clone(); changed.request_sha = ContentDigest::of(b"changed-request");
    let bad = StoredJobClaim::new(changed).map_err(|_| "JOB_CHANGED_INPUT")?;
    deny(r.claim_job(&c, &bad, event), "JOB_CHANGED_KEY_NOT_DENIED")?; negative::claim(&mut sql, &bad, event, "23505")?;
    checks.push("same_key_changed_request_denied");
    let mut changed = input.input().clone(); changed.key = id(151); changed.job = id(152); changed.request = id(153);
    changed.source = artifact(11)?; changed.source_sha = ContentDigest::parse(&"1".repeat(64)).map_err(|_| "JOB_DIGEST")?;
    let bad = StoredJobClaim::new(changed).map_err(|_| "JOB_CHANGED_INPUT")?;
    deny(r.claim_job(&c, &bad, event), "JOB_SOURCE_NOT_RESULT_NOT_DENIED")?; negative::claim(&mut sql, &bad, event, "23503")?;
    checks.push("unsealed_source_kind_denied");
    deny(r.lease_job(&c, &input, id(130), id(120), 120, event), "JOB_MISSING_WORKER_NOT_DENIED")?;
    negative::lease(&mut sql, &input, 130, 120, event, "42501")?; checks.push("unregistered_worker_denied");
    let cap = input.input().capability_sha.hex();
    for (agent, profile, capability, state, label) in [
        (131, "wrong-profile", cap.as_str(), "ready", "wrong_worker_profile_denied"),
        (132, PROFILE, "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "ready", "wrong_worker_capability_denied"),
        (133, PROFILE, cap.as_str(), "draining", "draining_worker_denied")] {
        register(&mut sql, agent, profile, capability, state)?;
        deny(r.lease_job(&c, &input, id(agent), id(120), 120, event), "JOB_BAD_WORKER_NOT_DENIED")?;
        negative::lease(&mut sql, &input, agent, 120, event, "42501")?; checks.push(label);
    }
    register(&mut sql, 130, PROFILE, &cap, "ready")?;
    let lease = r.lease_job(&c, &input, id(130), id(120), 120, event).map_err(|_| "JOB_LEASE_SQL")?;
    let l = lease.identity(); check(l.attempt_no == 1 && l.fencing_token == 1 && !l.authorization_id.is_nil(), "JOB_LEASE_IDENTITY")?;
    checks.push("actual_worker_lease_authorization");
    deny(r.lease_job(&c, &input, id(130), id(121), 120, event), "JOB_DUPLICATE_LEASE_NOT_DENIED")?;
    negative::lease(&mut sql, &input, 130, 121, event, "55000")?; checks.push("duplicate_lease_denied");
    let mut foreign = l; foreign.execution_id = id(199);
    deny(r.advance_job(&c, project()?, StoredJobLease::new(foreign).map_err(|_| "JOB_FOREIGN_LEASE")?, StoredJobAdvance::Staged, event), "JOB_FOREIGN_EXECUTION_NOT_DENIED")?;
    negative::advance(&mut sql, foreign, "leased", "staged", event)?;
    checks.push("foreign_execution_denied");
    deny(r.advance_job(&c, project()?, lease, StoredJobAdvance::Validating, event), "JOB_SKIPPED_STAGE_NOT_DENIED")?; checks.push("skipped_stage_denied");
    negative::advance(&mut sql, l, "executing", "validating", event)?;
    for (stage, outcome) in [(StoredJobAdvance::Staged, StoredJobOutcome::Staged), (StoredJobAdvance::Executing, StoredJobOutcome::Executing),
        (StoredJobAdvance::Validating, StoredJobOutcome::Validating)] {
        let observed = r.advance_job(&c, project()?, lease, stage, event).map_err(|_| "JOB_ADVANCE_SQL")?;
        check(observed.outcome() == outcome && observed.attempt_no() == 1 && observed.fencing_token() == 1, "JOB_ADVANCE_SHAPE")?;
    }
    checks.push("three_actual_ordered_transitions");
    let absent = RevisionId::parse(&format!("rev_{}", id(200).simple())).map_err(|_| "JOB_REVISION")?;
    deny(r.complete_job(&c, project()?, lease, absent, artifact(15)?, event), "JOB_UNCOMMITTED_COMPLETION_NOT_DENIED")?;
    negative::complete(&mut sql, l, absent, event)?;
    checks.push("uncommitted_effect_completion_denied");
    let replay = r.claim_job(&c, &input, event).map_err(|_| "JOB_FINAL_REPLAY")?;
    check(replay.outcome() == StoredJobOutcome::Replay && replay.state() == StoredJobState::InProgress && replay.attempt_no() == 1,
        "JOB_REJECTIONS_DID_NOT_CONSUME_ATTEMPTS")?; checks.push("final_replay_one_attempt");
    Ok(json!({"state":"PASS_ACTUAL_SQL23_CLAIM_LEASE_AND_STAGE_GUARDS_NOT_STORAGE_CAS_OR_PRODUCT", "checks":checks,
        "synthetic_metadata":true,"actual_blob_AEAD_or_product_execution":false,"SQL23_result_CAS_or_completion":false}))
}
fn restart() -> Result<Value> {
    let r = repository()?; let c = context()?; let input = claim(&r)?;
    let seen = r.claim_job(&c, &input, ContentDigest::of(b"restart-observe")).map_err(|_| "JOB_RESTART_REPLAY")?;
    check(seen.outcome() == StoredJobOutcome::Replay && seen.state() == StoredJobState::InProgress && seen.attempt_no() == 1
        && seen.fencing_token() == 1 && seen.result_revision_id().is_none(), "JOB_RESTART_STATE_CHANGED")?;
    Ok(json!({"state":"PASS_ACTUAL_JOB_REPLAY_AFTER_DATABASE_RESTART_NOT_EXECUTION_RETRY", "new_worker_or_execution":false}))
}
fn main() {
    let r = env::args().nth(1).ok_or("JOB_MODE").and_then(|mode| match mode.as_str() {
        "--fixture" => setup::fixture(), "--exercise" => exercise(), "--restart-observe" => restart(), _ => Err("JOB_CLOSED_MODE") });
    let value = match r { Ok(v) => v, Err(code) => json!({"state":"FAILED_ACTUAL_SQL23_JOB_PROBE","error_code":code,"raw_details":false}) };
    println!("{value}"); if !value["state"].as_str().is_some_and(|s| s.starts_with("PASS_")) { std::process::exit(2); }
}
