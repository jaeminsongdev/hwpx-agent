//! Actual disposable SQL leases and policy entry points; no minted product/native authority.
use super::super::{
    ArtifactId, BranchId, ContentDigest, Error, LocalPostgresSourcePolicyRepository, ProjectId,
    Result, RevisionCommitRequest, RevisionHead, RevisionRequestContext, SourcePolicyBinding,
    check, env, id, port, subject,
};
use postgres::{Client, Config, NoTls};
use revision_service::postgres::{
    RevisionLeaseIdentity, source_form_policy::SourcePolicyReadRequest,
};
fn db<T>(r: std::result::Result<T, postgres::Error>) -> Result<T> {
    r.map_err(|e| {
        eprintln!(
            "P84_DB_ERROR code={}",
            e.code()
                .map_or("NON_SERVER", postgres::error::SqlState::code)
        );
        drop(e);
        Box::<dyn Error>::from("P84_DB_DENIED")
    })
}
fn client() -> Result<Client> {
    let mut c = db(Config::new()
        .host("127.0.0.1")
        .port(port()?)
        .dbname("postgres")
        .user("p84_revision_app")
        .password(env::var("P84_REVISION_PASSWORD")?)
        .application_name("hwpx-agent-owned-p84-fixture-worker")
        .options("-c statement_timeout=5000 -c lock_timeout=1000 -c search_path=pg_catalog")
        .connect(NoTls))?;
    db(c.query_one("SELECT set_config('hwpx_agent.tenant_id',$1,false),set_config('hwpx_agent.subject_sha256',$2,false)",
        &[&id(1).hyphenated().to_string(),&subject()?.hex()]))?;
    Ok(c)
}
pub fn receive(
    req: &RevisionCommitRequest,
    i: usize,
    source: ContentDigest,
    effect: ContentDigest,
) -> Result<RevisionLeaseIdentity> {
    let mut c = client()?;
    let subject = subject()?.hex();
    let agent = id(23);
    if i == 0 {
        db(c.query_one("SELECT * FROM hwpx_agent.register_scheduler_worker($1,$2::character(64),$3,$4,$5::character(64),'ready',300,$6::character(64))",
        &[&id(1),&subject,&agent,&"hancom-hangul-2020-secondary",&"c".repeat(64),&"1".repeat(64)]))?;
    }
    let key = id(500 + i as u128);
    let job = id(600 + i as u128);
    let execution = id(700 + i as u128);
    db(c.query_one("SELECT * FROM hwpx_agent.claim_idempotent_job_v2($1,$2,$3,$4::character(64),$5,$6,$7,$8,NULL,0,
        $9::character(64),$10::character(64),$11::character(64),$12::character(64),$13::character(64),$14::character(64),
        $15,$16::character(64),3,1,4,600,$17::character(64))",&[
            &id(1),&req.project_id().as_uuid(),&req.branch_id().as_uuid(),&subject,&key,&job,&id(800+i as u128),&req.source_artifact_id().as_uuid(),
            &req.canonical_sha256()?.hex(),&"2".repeat(64),&source.hex(),&effect.hex(),&req.transaction_receipt_sha256().hex(),
            &req.operation_plan_sha256().hex(),&"hancom-hangul-2020-secondary",&"c".repeat(64),&"4".repeat(64)]))?;
    let row=db(c.query_one("SELECT * FROM hwpx_agent.lease_idempotent_job_v2($1,$2,$3::character(64),$4,$5,$6,$7,60,$8::character(64))",
        &[&id(1),&req.project_id().as_uuid(),&subject,&key,&job,&agent,&execution,&"5".repeat(64)]))?;
    let lease = RevisionLeaseIdentity {
        idempotency_key: key,
        job_id: job,
        agent_instance_id: agent,
        execution_id: execution,
        attempt_no: db(row.try_get("returned_attempt_count"))?,
        fencing_token: db(row.try_get("returned_fencing_token"))?,
        authorization_id: db(row.try_get("returned_commit_authorization_id"))?,
    };
    for (from, to) in [
        ("leased", "staged"),
        ("staged", "executing"),
        ("executing", "validating"),
    ] {
        db(c.query_one("SELECT * FROM hwpx_agent.advance_idempotent_job_v2($1,$2,$3::character(64),$4,$5,$6,$7,$8,$9,$10,$11,$12::character(64))",
            &[&id(1),&req.project_id().as_uuid(),&subject,&key,&job,&agent,&execution,&lease.attempt_no,&lease.fencing_token,&from,&to,&"6".repeat(64)]))?;
    }
    Ok(lease)
}
pub fn complete(
    req: &RevisionCommitRequest,
    l: RevisionLeaseIdentity,
    receipt: ArtifactId,
) -> Result<()> {
    let mut c = client()?;
    let row=db(c.query_one("SELECT * FROM hwpx_agent.complete_idempotent_job_success_v2($1,$2,$3::character(64),$4,$5,$6,$7,$8,$9,$10,$11,$12::character(64))",&[
        &id(1),&req.project_id().as_uuid(),&subject()?.hex(),&l.idempotency_key,&l.job_id,&l.agent_instance_id,&l.execution_id,&l.attempt_no,&l.fencing_token,
        &req.new_revision_id().as_uuid(),&receipt.as_uuid(),&"7".repeat(64)]))?;
    check(db(row.try_get::<_, String>("returned_state"))? == "terminal_success")
}
pub fn register(b: &SourcePolicyBinding, policy: ArtifactId, digest: ContentDigest) -> Result<()> {
    let mut c = client()?;
    let row=db(c.query_one("SELECT hwpx_agent.register_source_form_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,
        $10::character(64),$11::character(64),$12::character(64),$13,$14::character(64)) AS generation",&[
        &b.tenant.as_uuid(),&b.project.as_uuid(),&b.branch.as_uuid(),&subject()?.hex(),&b.document.as_str(),&b.policy_version,
        &0_i64,&b.source_revision.as_uuid(),&1_i64,&b.source_package_sha256.hex(),&b.source_provenance_sha256.hex(),&b.observed_graph_sha256.hex(),
        &policy.as_uuid(),&digest.hex()]))?;
    check(db(row.try_get::<_, i64>("generation"))? == 1)
}
pub fn revoke(
    repo: &LocalPostgresSourcePolicyRepository,
    context: &RevisionRequestContext,
    project: ProjectId,
    branch: BranchId,
    head: RevisionHead,
) -> Result<()> {
    let r = repo.read_current(
        context,
        &SourcePolicyReadRequest::new(project, branch, "p84-policy-document".into(), head)?,
    )?;
    let mut c = client()?;
    db(c.query_one(
        "SELECT hwpx_agent.revoke_source_form_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7)",
        &[
            &r.tenant.as_uuid(),
            &r.project.as_uuid(),
            &r.branch.as_uuid(),
            &subject()?.hex(),
            &r.document,
            &r.version,
            &i64::try_from(r.generation)?,
        ],
    ))?;
    Ok(())
}
