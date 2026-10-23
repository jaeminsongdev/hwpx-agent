//! Independent exact SQLSTATE oracle; transport/timeout/permission failures cannot masquerade as a guard.
use super::*;
use postgres::types::ToSql;
fn rejected(c: &mut Client, name: &str, casts: &[&str], args: &[&(dyn ToSql + Sync)], expected: &str) -> Result<()> {
    check(matches!(name, "claim_stored_revision_job_v1" | "lease_stored_revision_job_v1" | "advance_idempotent_job_v2" | "complete_stored_revision_job_success_v1")
        && casts.len() == args.len(), "JOB_NEGATIVE_CLOSED_FUNCTION")?;
    let parameters = casts.iter().enumerate().map(|(i,t)| format!("${}::{t}",i+1)).collect::<Vec<_>>().join(",");
    let result = c.query_one(&format!("SELECT * FROM hwpx_agent.{name}({parameters})"), args);
    match result { Err(error) if error.code().is_some_and(|code| code.code() == expected) => Ok(()),
        _ => Err("JOB_NEGATIVE_EXACT_SQLSTATE_REQUIRED") }
}
pub fn claim(c: &mut Client, claim: &StoredJobClaim, event: ContentDigest, code: &str) -> Result<()> {
    let i = claim.input(); let generation = i.expected_head.generation() as i64;
    rejected(c,"claim_stored_revision_job_v1", &["uuid","uuid","uuid","character(64)","uuid","uuid","uuid","uuid","uuid","bigint","character(64)","character(64)","character(64)","character(64)","character(64)","character(64)","text","character(64)","integer","integer","integer","integer","character(64)"],
        &[&id(1), &i.project.as_uuid(), &i.branch.as_uuid(), &"a".repeat(64), &i.key, &i.job, &i.request, &i.source.as_uuid(),
        &i.expected_head.revision_id().map(RevisionId::as_uuid), &generation, &i.request_sha.hex(), &i.manifest_sha.hex(), &i.source_sha.hex(),
        &i.effect_sha.hex(), &i.precommit_sha.hex(), &i.plan_sha.hex(), &i.target_profile, &i.capability_sha.hex(), &i.max_attempts, &i.base_delay_seconds,
        &i.max_delay_seconds, &i.ttl_seconds, &event.hex()], code)
}
pub fn lease(c: &mut Client, claim: &StoredJobClaim, agent: u128, execution: u128, event: ContentDigest, code: &str) -> Result<()> {
    let i = claim.input();
    rejected(c,"lease_stored_revision_job_v1", &["uuid","uuid","character(64)","uuid","uuid","uuid","uuid","integer","character(64)"],
        &[&id(1), &i.project.as_uuid(), &"a".repeat(64), &i.key, &i.job, &id(agent), &id(execution), &120_i32, &event.hex()], code)
}
pub fn advance(c: &mut Client, l: revision_service::postgres::RevisionLeaseIdentity, from: &str, to: &str, event: ContentDigest) -> Result<()> {
    rejected(c,"advance_idempotent_job_v2", &["uuid","uuid","character(64)","uuid","uuid","uuid","uuid","integer","bigint","text","text","character(64)"],
        &[&id(1), &id(2), &"a".repeat(64), &l.idempotency_key, &l.job_id, &l.agent_instance_id, &l.execution_id, &l.attempt_no, &l.fencing_token,
        &from, &to, &event.hex()], "40001")
}
pub fn complete(c: &mut Client, l: revision_service::postgres::RevisionLeaseIdentity, revision: RevisionId, event: ContentDigest) -> Result<()> {
    rejected(c,"complete_stored_revision_job_success_v1", &["uuid","uuid","character(64)","uuid","uuid","uuid","uuid","integer","bigint","uuid","uuid","character(64)"],
        &[&id(1), &id(2), &"a".repeat(64), &l.idempotency_key, &l.job_id, &l.agent_instance_id, &l.execution_id, &l.attempt_no, &l.fencing_token,
        &revision.as_uuid(), &id(15), &event.hex()], "55000")
}
