//! Actual bounded revision DAG and independent-connection CAS; metadata only, not native.
use super::{Probe, advance, artifact, config, connect, context, db, digest, id, worker_client};
use postgres::{Client, types::ToSql};
use revision_service::{
    BranchId, CommitId, CommitOutcome, FullDocumentIrBinding, ProjectId, RevisionCommitRequest,
    RevisionError, RevisionHead, RevisionId, RevisionRequestContext, RevisionService,
    RevisionValidationState,
    postgres::{LocalPostgresRevisionRepository, RevisionCommitLease, RevisionLeaseIdentity},
};
use std::{sync::Barrier, thread};

type Service = RevisionService<LocalPostgresRevisionRepository>;
const CLAIM: &str = "SELECT * FROM hwpx_agent.claim_idempotent_job_v2(
    $1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10,$11::character(64),
    $12::character(64),$13::character(64),$14::character(64),$15::character(64),
    $16::character(64),$17,$18::character(64),$19,$20,$21,$22,$23::character(64))";
const CLAIM_IR: &str = "SELECT * FROM hwpx_agent.claim_idempotent_job_with_full_ir_v1(
    $1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10,$11::character(64),
    $12::character(64),$13::character(64),$14::character(64),$15::character(64),
    $16::character(64),$17,$18::character(64),$19,$20,$21,$22,$23::character(64),
    $24,$25::character(64),$26::character(64),$27::character(64))";

fn revision(n: u8) -> Result<RevisionId, RevisionError> {
    RevisionId::parse(&format!("rev_{}", id(n).simple()))
}
fn branch(n: u8) -> Result<BranchId, RevisionError> {
    BranchId::parse(&format!("brn_{}", id(n).simple()))
}
fn request(
    base: u8,
    branch_no: u8,
    previous: Option<u8>,
    generation: u64,
    parents: &[u8],
    ir: bool,
) -> Result<RevisionCommitRequest, RevisionError> {
    let request = RevisionCommitRequest::new(
        CommitId::parse(&format!("cmt_{}", id(base + 1).simple()))?,
        ProjectId::parse(&format!("prj_{}", id(2).simple()))?,
        branch(branch_no)?,
        RevisionHead::new(previous.map(revision).transpose()?, generation)?,
        revision(base)?,
        parents
            .iter()
            .copied()
            .map(revision)
            .collect::<Result<Vec<_>, _>>()?,
        artifact(11)?,
        artifact(12)?,
        None,
        digest('4')?,
        RevisionValidationState::Verified,
        digest('5')?,
        digest('6')?,
    )?;
    if ir {
        request.with_full_document_ir(FullDocumentIrBinding {
            artifact_id: artifact(13)?,
            artifact_sha256: digest('3')?,
            result_package_sha256: digest('2')?,
            canonical_graph_sha256: digest('3')?,
        })
    } else {
        Ok(request)
    }
}
fn fixed_requests() -> Result<Vec<RevisionCommitRequest>, RevisionError> {
    Ok(vec![
        request(40, 3, Some(7), 1, &[7], false)?,
        request(50, 3, Some(40), 2, &[40], true)?,
        request(60, 4, None, 0, &[], false)?,
        request(70, 3, Some(50), 3, &[50, 60], true)?,
    ])
}
fn claim(worker: &mut Client, req: &RevisionCommitRequest, base: u8) -> Result<(), RevisionError> {
    let tenant = id(1);
    let project = id(2);
    let branch = req.branch_id().as_uuid();
    let subject = "a".repeat(64);
    let key = id(base + 2);
    let job = id(base + 3);
    let request_id = id(base + 5);
    let source = req.source_artifact_id().as_uuid();
    let previous = req.expected_head().revision_id().map(RevisionId::as_uuid);
    let generation =
        i64::try_from(req.expected_head().generation()).map_err(|_| RevisionError::InvalidHead)?;
    let request_sha = req.canonical_sha256()?.hex();
    let manifest = "2".repeat(64);
    let source_sha = "1".repeat(64);
    let effect = "2".repeat(64);
    let transaction = req.transaction_receipt_sha256().hex();
    let plan = req.operation_plan_sha256().hex();
    let profile = "hancom-hangul-2020-secondary";
    let capability = "c".repeat(64);
    let attempts = 3_i32;
    let delay = 1_i32;
    let max_delay = 4_i32;
    let ttl = 600_i32;
    let event = "4".repeat(64);
    let ir = req.full_document_ir();
    let ir_id = ir.map(|x| x.artifact_id.as_uuid());
    let ir_sha = ir.map(|x| x.artifact_sha256.hex());
    let package = ir.map(|x| x.result_package_sha256.hex());
    let graph = ir.map(|x| x.canonical_graph_sha256.hex());
    let args: [&(dyn ToSql + Sync); 27] = [
        &tenant,
        &project,
        &branch,
        &subject,
        &key,
        &job,
        &request_id,
        &source,
        &previous,
        &generation,
        &request_sha,
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
        &package,
        &graph,
    ];
    if ir.is_some() {
        db(worker.query_one(CLAIM_IR, &args))?;
    } else {
        db(worker.query_one(CLAIM, &args[..23]))?;
    }
    Ok(())
}
fn lease(
    worker: &mut Client,
    req: &RevisionCommitRequest,
    base: u8,
) -> Result<RevisionLeaseIdentity, RevisionError> {
    claim(worker, req, base)?;
    let row = db(worker.query_one(
        "SELECT * FROM hwpx_agent.lease_idempotent_job_v2(
        $1,$2,$3::character(64),$4,$5,$6,$7,60,$8::character(64))",
        &[
            &id(1),
            &id(2),
            &"a".repeat(64),
            &id(base + 2),
            &id(base + 3),
            &id(23),
            &id(base + 4),
            &"5".repeat(64),
        ],
    ))?;
    Ok(RevisionLeaseIdentity {
        idempotency_key: id(base + 2),
        job_id: id(base + 3),
        agent_instance_id: id(23),
        execution_id: id(base + 4),
        attempt_no: db(row.try_get("returned_attempt_count"))?,
        fencing_token: db(row.try_get("returned_fencing_token"))?,
        authorization_id: db(row.try_get("returned_commit_authorization_id"))?,
    })
}
fn complete(
    worker: &mut Client,
    req: &RevisionCommitRequest,
    lease: RevisionLeaseIdentity,
) -> Result<(), RevisionError> {
    let row = db(worker.query_one(
        "SELECT * FROM hwpx_agent.complete_idempotent_job_success_v2(
        $1,$2,$3::character(64),$4,$5,$6,$7,$8,$9,$10,$11,$12::character(64))",
        &[
            &id(1),
            &id(2),
            &"a".repeat(64),
            &lease.idempotency_key,
            &lease.job_id,
            &lease.agent_instance_id,
            &lease.execution_id,
            &lease.attempt_no,
            &lease.fencing_token,
            &req.new_revision_id().as_uuid(),
            &id(15),
            &"7".repeat(64),
        ],
    ))?;
    if db(row.try_get::<_, String>("returned_state"))? != "terminal_success" {
        return Err(RevisionError::RepositoryFailure);
    }
    Ok(())
}
fn writer(
    req: &RevisionCommitRequest,
    identity: RevisionLeaseIdentity,
) -> Result<Service, RevisionError> {
    Ok(RevisionService::new(connect(
        &config()?,
        context()?,
        Some(RevisionCommitLease::bind(identity, req)?),
    )?))
}
fn fixed_commits(p: &mut Probe, worker: &mut Client) -> Result<(), RevisionError> {
    let ctx = context()?;
    for (req, name) in fixed_requests()?.into_iter().zip([
        "legacy_child_commit",
        "full_ir_child_commit",
        "sibling_root_commit",
        "merge_commit",
    ]) {
        let base = u8::try_from(req.new_revision_id().as_uuid().as_u128())
            .map_err(|_| RevisionError::InvalidIdentifier)?;
        let identity = lease(worker, &req, base)?;
        advance(worker, identity)?;
        let outcome = writer(&req, identity)?.commit(&ctx, &req)?;
        p.check(name,matches!(outcome,CommitOutcome::Committed(ref receipt)
            if receipt.committed_head()==RevisionHead::new(Some(req.new_revision_id()),req.expected_head().generation()+1)?
                && receipt.request_sha256()==req.canonical_sha256()?))?;
        complete(worker, &req, identity)?;
    }
    Ok(())
}
fn read_matches(
    service: &Service,
    ctx: &RevisionRequestContext,
    req: &RevisionCommitRequest,
) -> Result<bool, RevisionError> {
    let node = service.node(ctx, req.project_id(), req.new_revision_id())?;
    let wire = serde_json::to_value(&node).map_err(|_| RevisionError::Serialization)?;
    let source =
        serde_json::to_value(req.source_artifact_id()).map_err(|_| RevisionError::Serialization)?;
    Ok(node.sealed()
        && node.revision_id() == req.new_revision_id()
        && node.parents() == req.parents()
        && node.full_document_ir() == req.full_document_ir()
        && node.committed_generation() == req.expected_head().generation() + 1
        && wire.get("source_artifact_id") == Some(&source)
        && node.result_artifact_id() == req.result_artifact_id())
}
fn read_intermediates(p: &mut Probe) -> Result<(), RevisionError> {
    let service = RevisionService::new(connect(&config()?, context()?, None)?);
    let ctx = context()?;
    let requests = fixed_requests()?;
    p.check(
        "legacy_child_read_preserves_no_ir",
        read_matches(&service, &ctx, &requests[0])?,
    )?;
    p.check(
        "full_ir_child_read",
        read_matches(&service, &ctx, &requests[1])?,
    )?;
    p.check(
        "merge_parent_order_preserved",
        read_matches(&service, &ctx, &requests[3])?,
    )?;
    Ok(())
}
fn concurrent(p: &mut Probe, worker: &mut Client) -> Result<(), RevisionError> {
    let first = request(80, 3, Some(70), 4, &[70], true)?;
    let second = request(90, 3, Some(70), 4, &[70], true)?;
    let a = lease(worker, &first, 80)?;
    let b = lease(worker, &second, 90)?;
    advance(worker, a)?;
    advance(worker, b)?;
    p.check(
        "concurrent_genuine_workers_received_fences",
        a.attempt_no == 1
            && b.attempt_no == 1
            && a.fencing_token == 1
            && b.fencing_token == 1
            && a.authorization_id != b.authorization_id,
    )?;
    let wa = writer(&first, a)?;
    let wb = writer(&second, b)?;
    let ctx = context()?;
    let barrier = Barrier::new(2);
    let (oa, ob) = thread::scope(|scope| {
        let ta = scope.spawn(|| {
            barrier.wait();
            wa.commit(&ctx, &first)
        });
        let tb = scope.spawn(|| {
            barrier.wait();
            wb.commit(&ctx, &second)
        });
        Ok::<_, RevisionError>((
            ta.join().map_err(|_| RevisionError::RepositoryFailure)?,
            tb.join().map_err(|_| RevisionError::RepositoryFailure)?,
        ))
    })?;
    let (winner, loser, identity) = match (&oa, &ob) {
        (Ok(CommitOutcome::Committed(_)), Ok(CommitOutcome::Conflict(_))) => (&first, &second, a),
        (Ok(CommitOutcome::Conflict(_)), Ok(CommitOutcome::Committed(_))) => (&second, &first, b),
        _ => {
            for outcome in [&oa, &ob] {
                if let Err(error) = outcome {
                    eprintln!(
                        "P09_POSTGRES_REVISION_UNEXPECTED_OUTCOME code={}",
                        error.code()
                    );
                }
            }
            p.check("concurrent_exactly_one_commit_one_conflict", false)?;
            return Err(RevisionError::RepositoryFailure);
        }
    };
    p.check("concurrent_exactly_one_commit_one_conflict", true)?;
    complete(worker, winner, identity)?;
    p.check("concurrent_winner_completion", true)?;
    let read = RevisionService::new(connect(&config()?, ctx.clone(), None)?);
    p.check(
        "concurrent_loser_node_absent",
        matches!(
            read.node(&ctx, loser.project_id(), loser.new_revision_id()),
            Err(RevisionError::NotFound)
        ),
    )?;
    Ok(())
}
pub(super) fn write(p: &mut Probe) -> Result<(), RevisionError> {
    let mut worker = worker_client()?;
    fixed_commits(p, &mut worker)?;
    read_intermediates(p)?;
    concurrent(p, &mut worker)?;
    verify(p)
}
pub(super) fn verify(p: &mut Probe) -> Result<(), RevisionError> {
    let ctx = context()?;
    let service = RevisionService::new(connect(&config()?, ctx.clone(), None)?);
    let requests = fixed_requests()?;
    let first = request(80, 3, Some(70), 4, &[70], true)?;
    let second = request(90, 3, Some(70), 4, &[70], true)?;
    let head = service.head(&ctx, first.project_id(), branch(3)?)?;
    p.check(
        "graph_main_head_exact",
        head.generation() == 5
            && [first.new_revision_id(), second.new_revision_id()]
                .contains(&head.revision_id().ok_or(RevisionError::InvalidHead)?),
    )?;
    p.check(
        "graph_legacy_child_exact",
        read_matches(&service, &ctx, &requests[0])?,
    )?;
    p.check(
        "graph_full_ir_child_exact",
        read_matches(&service, &ctx, &requests[1])?,
    )?;
    p.check(
        "graph_other_branch_head_exact",
        service.head(&ctx, first.project_id(), branch(4)?)?
            == RevisionHead::new(Some(requests[2].new_revision_id()), 1)?
            && read_matches(&service, &ctx, &requests[2])?,
    )?;
    p.check(
        "graph_merge_exact_order_seal",
        read_matches(&service, &ctx, &requests[3])?,
    )?;
    let (winner, loser) = if head.revision_id() == Some(first.new_revision_id()) {
        (&first, &second)
    } else {
        (&second, &first)
    };
    p.check(
        "graph_winner_exact_loser_absent",
        read_matches(&service, &ctx, winner)?
            && matches!(
                service.node(&ctx, loser.project_id(), loser.new_revision_id()),
                Err(RevisionError::NotFound)
            ),
    )?;
    Ok(())
}
pub(super) fn denied(p: &mut Probe) -> Result<(), RevisionError> {
    let ctx = context()?;
    let service = RevisionService::new(connect(&config()?, ctx.clone(), None)?);
    let request = request(70, 3, Some(50), 3, &[50, 60], true)?;
    p.check(
        "revoked_project_head_denied",
        matches!(
            service.head(&ctx, request.project_id(), branch(3)?),
            Err(RevisionError::NotFound)
        ),
    )?;
    p.check(
        "revoked_project_node_denied",
        matches!(
            service.node(&ctx, request.project_id(), request.new_revision_id()),
            Err(RevisionError::NotFound)
        ),
    )?;
    Ok(())
}
