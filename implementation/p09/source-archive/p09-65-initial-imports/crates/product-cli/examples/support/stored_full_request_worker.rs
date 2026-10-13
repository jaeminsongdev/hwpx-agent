//! Genuine disposable schema19 worker/lease/authorization wrappers, NOT signed form authority.
use super::{Failure, Result, config_port, context, db, env, id, revision_config};
use postgres::{Client, Config, NoTls, types::ToSql};
use revision_service::{
    CommitOutcome, RevisionCommitRequest, RevisionHead, RevisionService,
    postgres::{LocalPostgresRevisionRepository, RevisionCommitLease, RevisionLeaseIdentity},
};

pub(super) fn client() -> Result<Client> {
    let mut c = db(Config::new()
        .host("127.0.0.1")
        .port(config_port()?)
        .dbname("postgres")
        .user("p09_revision_app")
        .password(env("P65_REVISION_PASSWORD")?)
        .application_name("hwpx-agent-disposable-full-ir-worker")
        .options("-c statement_timeout=5000 -c lock_timeout=1000 -c search_path=pg_catalog")
        .connect(NoTls))?;
    db(c.query_one("SELECT set_config('hwpx_agent.tenant_id',$1,false),set_config('hwpx_agent.subject_sha256',$2,false)",
        &[&id(1).hyphenated().to_string(), &"a".repeat(64)]))?;
    Ok(c)
}

fn receive(
    c: &mut Client,
    req: &RevisionCommitRequest,
    case: u8,
    source_sha: &str,
) -> Result<RevisionLeaseIdentity> {
    let tenant = id(1);
    let subject = "a".repeat(64);
    let agent = id(23);
    let profile = "hancom-hangul-2020-secondary";
    let capability = "c".repeat(64);
    db(c.query_one("SELECT * FROM hwpx_agent.register_scheduler_worker($1,$2::character(64),$3,$4,$5::character(64),'ready',300,$6::character(64))",
        &[&tenant,&subject,&agent,&profile,&capability,&"1".repeat(64)]))?;
    let project = req.project_id().as_uuid();
    let branch = req.branch_id().as_uuid();
    let key = id(300 + u128::from(case));
    let job = id(310 + u128::from(case));
    let request = id(320 + u128::from(case));
    let source = req.source_artifact_id().as_uuid();
    let expected: Option<uuid::Uuid> = None;
    let generation = 0_i64;
    let sha = req.canonical_sha256()?.hex();
    let manifest = "2".repeat(64);
    let effect = req
        .full_document_ir()
        .ok_or(Failure::Fixture)?
        .result_package_sha256
        .hex();
    let transaction = req.transaction_receipt_sha256().hex();
    let plan = req.operation_plan_sha256().hex();
    let attempts = 3_i32;
    let delay = 1_i32;
    let max_delay = 4_i32;
    let ttl = 600_i32;
    let event = "4".repeat(64);
    let ir = req.full_document_ir().ok_or(Failure::Fixture)?;
    let ir_id = ir.artifact_id.as_uuid();
    let ir_sha = ir.artifact_sha256.hex();
    let graph = ir.canonical_graph_sha256.hex();
    let args: [&(dyn ToSql + Sync); 27] = [
        &tenant,
        &project,
        &branch,
        &subject,
        &key,
        &job,
        &request,
        &source,
        &expected,
        &generation,
        &sha,
        &manifest,
        &source_sha,
        &effect,
        &transaction,
        &plan,
        &profile,
        &capability,
        &attempts,
        &delay,
        &max_delay,
        &ttl,
        &event,
        &ir_id,
        &ir_sha,
        &effect,
        &graph,
    ];
    db(c.query_one(
        "SELECT * FROM hwpx_agent.claim_idempotent_job_with_full_ir_v1(
        $1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10,
        $11::character(64),$12::character(64),$13::character(64),$14::character(64),
        $15::character(64),$16::character(64),$17,$18::character(64),$19,$20,$21,$22,
        $23::character(64),$24,$25::character(64),$26::character(64),$27::character(64))",
        &args,
    ))?;
    let execution = id(330 + u128::from(case));
    let row=db(c.query_one("SELECT * FROM hwpx_agent.lease_idempotent_job_v2($1,$2,$3::character(64),$4,$5,$6,$7,60,$8::character(64))",
        &[&tenant,&project,&subject,&key,&job,&agent,&execution,&"5".repeat(64)]))?;
    Ok(RevisionLeaseIdentity {
        idempotency_key: key,
        job_id: job,
        agent_instance_id: agent,
        execution_id: execution,
        attempt_no: db(row.try_get("returned_attempt_count"))?,
        fencing_token: db(row.try_get("returned_fencing_token"))?,
        authorization_id: db(row.try_get("returned_commit_authorization_id"))?,
    })
}

fn advance(
    c: &mut Client,
    req: &RevisionCommitRequest,
    lease: RevisionLeaseIdentity,
) -> Result<()> {
    for (from, to) in [
        ("leased", "staged"),
        ("staged", "executing"),
        ("executing", "validating"),
    ] {
        db(c.query_one(
            "SELECT * FROM hwpx_agent.advance_idempotent_job_v2(
        $1,$2,$3::character(64),$4,$5,$6,$7,$8,$9,$10,$11,$12::character(64))",
            &[
                &id(1),
                &req.project_id().as_uuid(),
                &"a".repeat(64),
                &lease.idempotency_key,
                &lease.job_id,
                &lease.agent_instance_id,
                &lease.execution_id,
                &lease.attempt_no,
                &lease.fencing_token,
                &from,
                &to,
                &"6".repeat(64),
            ],
        ))?;
    }
    Ok(())
}

pub(super) fn commit(
    req: &RevisionCommitRequest,
    case: u8,
    source_sha: &str,
    receipt: artifact_service::ArtifactId,
) -> Result<()> {
    let mut c = client()?;
    let lease = receive(&mut c, req, case, source_sha)?;
    advance(&mut c, req, lease)?;
    let ctx = context()?;
    let repo = LocalPostgresRevisionRepository::connect_diagnosed(
        &revision_config()?,
        ctx.clone(),
        Some(RevisionCommitLease::bind(lease, req)?),
    )
    .map_err(|e| {
        eprintln!("P65_CONNECT_FAILED stage={}", e.stage().code());
        Failure::Revision(e.into_error())
    })?;
    match RevisionService::new(repo).commit(&ctx, req)? {
        CommitOutcome::Committed(value)
            if value.committed_head() == RevisionHead::new(Some(req.new_revision_id()), 1)?
                && value.request_sha256() == req.canonical_sha256()? => {}
        _ => return Err(Failure::Fixture),
    }
    let row = db(c.query_one(
        "SELECT * FROM hwpx_agent.complete_idempotent_job_success_v2(
        $1,$2,$3::character(64),$4,$5,$6,$7,$8,$9,$10,$11,$12::character(64))",
        &[
            &id(1),
            &req.project_id().as_uuid(),
            &"a".repeat(64),
            &lease.idempotency_key,
            &lease.job_id,
            &lease.agent_instance_id,
            &lease.execution_id,
            &lease.attempt_no,
            &lease.fencing_token,
            &req.new_revision_id().as_uuid(),
            &receipt.as_uuid(),
            &"7".repeat(64),
        ],
    ))?;
    if db(row.try_get::<_, String>("returned_state"))? != "terminal_success" {
        return Err(Failure::Fixture);
    }
    Ok(())
}
