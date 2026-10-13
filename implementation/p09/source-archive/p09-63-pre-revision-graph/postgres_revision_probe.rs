//! Actual disposable `PostgreSQL` driver probe, SQL metadata only; no Hwp/blob/import/oracle.
use ::postgres::{Client, Config, NoTls};
use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use revision_service::{
    BranchId, CommitId, CommitOutcome, FullDocumentIrBinding, ProjectId, RevisionCommitRequest,
    RevisionError, RevisionHead, RevisionId, RevisionRequestContext, RevisionService,
    RevisionValidationState,
    postgres::{
        LocalPostgresRevisionConfig, LocalPostgresRevisionRepository, RevisionCommitLease,
        RevisionLeaseIdentity,
    },
};
use uuid::Uuid;

fn env(key: &str) -> Result<String, RevisionError> {
    std::env::var(key).map_err(|_| RevisionError::InvalidRequest)
}
fn db<T>(r: Result<T, ::postgres::Error>) -> Result<T, RevisionError> {
    r.map_err(|_| RevisionError::RepositoryFailure)
}
fn id(n: u8) -> Uuid {
    Uuid::from_u128(u128::from(n))
}
fn artifact(n: u8) -> Result<ArtifactId, RevisionError> {
    ArtifactId::parse(&format!("art_{}", id(n).simple()))
        .map_err(|_| RevisionError::InvalidIdentifier)
}
fn digest(c: char) -> Result<ContentDigest, RevisionError> {
    ContentDigest::parse(&c.to_string().repeat(64)).map_err(|_| RevisionError::InvalidRequest)
}
fn request() -> Result<RevisionCommitRequest, RevisionError> {
    RevisionCommitRequest::new(
        CommitId::parse(&format!("cmt_{}", id(6).simple()))?,
        ProjectId::parse(&format!("prj_{}", id(2).simple()))?,
        BranchId::parse(&format!("brn_{}", id(3).simple()))?,
        RevisionHead::empty(),
        RevisionId::parse(&format!("rev_{}", id(7).simple()))?,
        Vec::new(),
        artifact(11)?,
        artifact(12)?,
        None,
        digest('4')?,
        RevisionValidationState::Verified,
        digest('5')?,
        digest('6')?,
    )?
    .with_full_document_ir(FullDocumentIrBinding {
        artifact_id: artifact(13)?,
        artifact_sha256: digest('3')?,
        result_package_sha256: digest('2')?,
        canonical_graph_sha256: digest('3')?,
    })
}
fn connect(
    cfg: &LocalPostgresRevisionConfig,
    ctx: RevisionRequestContext,
    lease: Option<RevisionCommitLease>,
) -> Result<LocalPostgresRevisionRepository, RevisionError> {
    LocalPostgresRevisionRepository::connect_diagnosed(cfg, ctx, lease).map_err(|failure| {
        eprintln!(
            "P09_POSTGRES_REVISION_CONNECT_FAILED stage={}",
            failure.stage().code()
        );
        failure.into_error()
    })
}
fn context() -> Result<RevisionRequestContext, RevisionError> {
    Ok(RevisionRequestContext::new(
        TenantId::new(id(1)).map_err(|_| RevisionError::InvalidIdentifier)?,
        SubjectDigest::parse(&"a".repeat(64)).map_err(|_| RevisionError::InvalidIdentifier)?,
    ))
}
fn config() -> Result<LocalPostgresRevisionConfig, RevisionError> {
    LocalPostgresRevisionConfig::new(
        env("P09_REVISION_DB_PORT")?
            .parse()
            .map_err(|_| RevisionError::InvalidRequest)?,
        "postgres".into(),
        "p09_revision_app".into(),
        env("P09_REVISION_DB_PASSWORD")?,
    )
}
#[derive(Default)]
struct Probe {
    checks: Vec<&'static str>,
}
impl Probe {
    fn check(&mut self, name: &'static str, ok: bool) -> Result<(), RevisionError> {
        if !ok {
            eprintln!("P09_POSTGRES_REVISION_CHECK_FAILED check={name}");
            return Err(RevisionError::InvalidRequest);
        }
        self.checks.push(name);
        Ok(())
    }
}
fn worker_client() -> Result<Client, RevisionError> {
    let mut c = db(Config::new()
        .host("127.0.0.1")
        .port(
            env("P09_REVISION_DB_PORT")?
                .parse()
                .map_err(|_| RevisionError::InvalidRequest)?,
        )
        .dbname("postgres")
        .user("p09_revision_app")
        .password(env("P09_REVISION_DB_PASSWORD")?)
        .application_name("hwpx-agent-disposable-revision-worker")
        .options("-c statement_timeout=5000 -c lock_timeout=1000 -c search_path=pg_catalog")
        .connect(NoTls))?;
    db(c.query_one("SELECT set_config('hwpx_agent.tenant_id',$1,false),set_config('hwpx_agent.subject_sha256',$2,false)",
        &[&id(1).hyphenated().to_string(),&"a".repeat(64)]))?;
    Ok(c)
}
fn receive_lease(
    c: &mut Client,
    req: &RevisionCommitRequest,
) -> Result<RevisionLeaseIdentity, RevisionError> {
    db(c.query_one("SELECT * FROM hwpx_agent.register_scheduler_worker($1,$2::character(64),$3,$4,$5::character(64),'ready',300,$6::character(64))",
        &[&id(1),&"a".repeat(64),&id(23),&"hancom-hangul-2020-secondary",&"c".repeat(64),&"1".repeat(64)]))?;
    let ir = req
        .full_document_ir()
        .ok_or(RevisionError::InvalidRequest)?;
    db(c.query_one(
        "SELECT * FROM hwpx_agent.claim_idempotent_job_with_full_ir_v1(
        $1,$2,$3,$4::character(64),$5,$6,$7,$8,NULL,0,
        $9::character(64),$10::character(64),$11::character(64),$12::character(64),
        $13::character(64),$14::character(64),$15,$16::character(64),3,1,4,600,
        $17::character(64),$18,$19::character(64),$20::character(64),$21::character(64))",
        &[
            &id(1),
            &id(2),
            &id(3),
            &"a".repeat(64),
            &id(20),
            &id(21),
            &id(22),
            &id(11),
            &req.canonical_sha256()?.hex(),
            &"2".repeat(64),
            &"1".repeat(64),
            &"2".repeat(64),
            &req.transaction_receipt_sha256().hex(),
            &req.operation_plan_sha256().hex(),
            &"hancom-hangul-2020-secondary",
            &"c".repeat(64),
            &"4".repeat(64),
            &ir.artifact_id.as_uuid(),
            &ir.artifact_sha256.hex(),
            &ir.result_package_sha256.hex(),
            &ir.canonical_graph_sha256.hex(),
        ],
    ))?;
    let row=db(c.query_one("SELECT * FROM hwpx_agent.lease_idempotent_job_v2($1,$2,$3::character(64),$4,$5,$6,$7,60,$8::character(64))",
        &[&id(1),&id(2),&"a".repeat(64),&id(20),&id(21),&id(23),&id(24),&"5".repeat(64)]))?;
    Ok(RevisionLeaseIdentity {
        idempotency_key: id(20),
        job_id: id(21),
        agent_instance_id: id(23),
        execution_id: id(24),
        attempt_no: db(row.try_get("returned_attempt_count"))?,
        fencing_token: db(row.try_get("returned_fencing_token"))?,
        authorization_id: db(row.try_get("returned_commit_authorization_id"))?,
    })
}
fn advance(c: &mut Client, identity: RevisionLeaseIdentity) -> Result<(), RevisionError> {
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
                &id(2),
                &"a".repeat(64),
                &identity.idempotency_key,
                &identity.job_id,
                &identity.agent_instance_id,
                &identity.execution_id,
                &identity.attempt_no,
                &identity.fencing_token,
                &from,
                &to,
                &"6".repeat(64),
            ],
        ))?;
    }
    Ok(())
}
fn verify(p: &mut Probe) -> Result<(), RevisionError> {
    let ctx = context()?;
    let req = request()?;
    let service = RevisionService::new(connect(&config()?, ctx.clone(), None)?);
    let head = service.head(&ctx, req.project_id(), req.branch_id())?;
    p.check(
        "durable_exact_head",
        head == RevisionHead::new(Some(req.new_revision_id()), 1)?,
    )?;
    let node = service.node(&ctx, req.project_id(), req.new_revision_id())?;
    p.check(
        "durable_sealed_full_ir_link",
        node.sealed()
            && node.full_document_ir() == req.full_document_ir()
            && node.result_artifact_id() == req.result_artifact_id()
            && node.parents().is_empty(),
    )?;
    p.check(
        "read_only_repository_cannot_commit",
        matches!(
            service.commit(&ctx, &req),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    let other = RevisionRequestContext::new(
        ctx.tenant_id(),
        SubjectDigest::parse(&"b".repeat(64)).map_err(|_| RevisionError::InvalidRequest)?,
    );
    p.check(
        "different_subject_service_read_denied",
        matches!(
            service.head(&other, req.project_id(), req.branch_id()),
            Err(RevisionError::NotFound)
        ) && matches!(
            service.node(&other, req.project_id(), req.new_revision_id()),
            Err(RevisionError::NotFound)
        ),
    )?;
    Ok(())
}
fn write(p: &mut Probe) -> Result<(), RevisionError> {
    let ctx = context()?;
    let req = request()?;
    let cfg = config()?;
    let read = RevisionService::new(connect(&cfg, ctx.clone(), None)?);
    p.check(
        "empty_real_db_head",
        read.head(&ctx, req.project_id(), req.branch_id())? == RevisionHead::empty(),
    )?;
    p.check(
        "no_lease_write_denied",
        matches!(read.commit(&ctx, &req), Err(RevisionError::InvalidRequest)),
    )?;
    let fake = RevisionLeaseIdentity {
        idempotency_key: id(20),
        job_id: id(21),
        agent_instance_id: id(23),
        execution_id: id(24),
        attempt_no: 1,
        fencing_token: 1,
        authorization_id: id(25),
    };
    let fake_service = RevisionService::new(connect(
        &cfg,
        ctx.clone(),
        Some(RevisionCommitLease::bind(fake, &req)?),
    )?);
    p.check(
        "fake_uuid_is_not_real_authority",
        matches!(
            fake_service.commit(&ctx, &req),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    let mut worker = worker_client()?;
    let identity = receive_lease(&mut worker, &req)?;
    p.check(
        "received_real_first_lease",
        identity.attempt_no == 1
            && identity.fencing_token == 1
            && !identity.authorization_id.is_nil(),
    )?;
    let writer = RevisionService::new(connect(
        &cfg,
        ctx.clone(),
        Some(RevisionCommitLease::bind(identity, &req)?),
    )?);
    let prevalidation = writer.commit(&ctx, &req);
    diagnose_prevalidation(&prevalidation);
    p.check(
        "prevalidation_commit_denied",
        matches!(prevalidation, Err(RevisionError::InvalidRequest)),
    )?;
    p.check(
        "denied_attempts_preserve_head",
        read.head(&ctx, req.project_id(), req.branch_id())? == RevisionHead::empty(),
    )?;
    check_request_drift(p, &writer, &ctx, &req)?;
    advance(&mut worker, identity)?;
    let CommitOutcome::Committed(receipt) = writer.commit(&ctx, &req)? else {
        return Err(RevisionError::RepositoryFailure);
    };
    p.check(
        "actual_authorized_rust_ir_commit",
        receipt.committed_head() == RevisionHead::new(Some(req.new_revision_id()), 1)?
            && receipt.request_sha256() == req.canonical_sha256()?,
    )?;
    p.check(
        "consumed_real_token_cannot_commit_again",
        matches!(
            writer.commit(&ctx, &req),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    let completed = db(worker.query_one(
        "SELECT * FROM hwpx_agent.complete_idempotent_job_success_v2(
        $1,$2,$3::character(64),$4,$5,$6,$7,$8,$9,$10,$11,$12::character(64))",
        &[
            &id(1),
            &id(2),
            &"a".repeat(64),
            &id(20),
            &id(21),
            &id(23),
            &id(24),
            &1_i32,
            &1_i64,
            &req.new_revision_id().as_uuid(),
            &id(15),
            &"7".repeat(64),
        ],
    ))?;
    p.check(
        "real_success_completion",
        db(completed.try_get::<_, String>("returned_state"))? == "terminal_success",
    )?;
    verify(p)
}
fn diagnose_prevalidation(outcome: &Result<CommitOutcome, RevisionError>) {
    if !matches!(outcome, Err(RevisionError::InvalidRequest)) {
        let code = match outcome {
            Err(error) => error.code(),
            Ok(CommitOutcome::Committed(_)) => "UNEXPECTED_COMMITTED",
            Ok(CommitOutcome::Conflict(_)) => "UNEXPECTED_CONFLICT",
        };
        eprintln!("P09_POSTGRES_REVISION_UNEXPECTED_OUTCOME code={code}");
    }
}
fn check_request_drift(
    p: &mut Probe,
    writer: &RevisionService<LocalPostgresRevisionRepository>,
    ctx: &RevisionRequestContext,
    req: &RevisionCommitRequest,
) -> Result<(), RevisionError> {
    let different = RevisionCommitRequest::new(
        CommitId::parse(&format!("cmt_{}", id(26).simple()))?,
        req.project_id(),
        req.branch_id(),
        req.expected_head(),
        req.new_revision_id(),
        Vec::new(),
        req.source_artifact_id(),
        req.result_artifact_id(),
        None,
        req.operation_plan_sha256(),
        RevisionValidationState::Verified,
        req.validation_summary_sha256(),
        req.transaction_receipt_sha256(),
    )?
    .with_full_document_ir(
        req.full_document_ir()
            .ok_or(RevisionError::InvalidRequest)?,
    )?;
    p.check(
        "lease_bound_to_whole_typed_request",
        matches!(
            writer.commit(ctx, &different),
            Err(RevisionError::InvalidRequest)
        ),
    )?;
    Ok(())
}
fn main() {
    let mut p = Probe::default();
    let result = (|| -> Result<String, RevisionError> {
        let mode = env("P09_REVISION_PROBE_MODE")?;
        match mode.as_str() {
            "write" => write(&mut p)?,
            "verify" => verify(&mut p)?,
            "reject-admission" => {
                p.check(
                    "unsafe_database_admission_denied",
                    matches!(
                        connect(&config()?, context()?, None),
                        Err(RevisionError::InvalidRequest)
                    ),
                )?;
            }
            _ => return Err(RevisionError::InvalidRequest),
        }
        Ok(mode)
    })();
    match result {
        Ok(mode) => println!(
            "{}",
            serde_json::json!({"schema":"hwpx-agent.p09-rust-postgres-revision-probe/v1",
            "state":"pass","mode":mode,"checks":p.checks,"actual_assertions":p.checks.len(),
            "scope":"actual_disposable_sql_metadata_not_native_import_or_product","native_activated":false,"p09_complete":false})
        ),
        Err(error) => {
            eprintln!("P09_POSTGRES_REVISION_PROBE_FAILED code={}", error.code());
            std::process::exit(2);
        }
    }
}
