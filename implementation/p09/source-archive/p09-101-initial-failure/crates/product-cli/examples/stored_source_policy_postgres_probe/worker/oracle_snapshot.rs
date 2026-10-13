//! Failure context for the OWNED synthetic fixture only. No DB read or permission expansion.
use super::super::{ArtifactId, RevisionCommitRequest};
use revision_service::postgres::RevisionLeaseIdentity;

#[cfg(test)]
const SQL: &str = include_str!("oracle_snapshot.sql");
#[cfg(test)]
const CHECKS: [&str; 40] = [
    "head_revision",
    "head_generation",
    "head_generation_nonnegative",
    "source_metadata",
    "source_available",
    "source_verified",
    "source_kind",
    "source_digest",
    "source_acl",
    "receipt_metadata",
    "receipt_available",
    "receipt_verified",
    "receipt_kind",
    "receipt_digest",
    "receipt_acl",
    "revision_source",
    "revision_plan",
    "revision_verified",
    "revision_subject",
    "result_metadata",
    "result_available",
    "result_verified",
    "result_kind",
    "result_digest",
    "result_acl",
    "seal_kind",
    "seal_generation",
    "seal_receipt",
    "seal_commit_id",
    "seal_request",
    "commit_branch",
    "commit_previous",
    "commit_expected_generation",
    "commit_generation",
    "commit_receipt",
    "commit_subject",
    "record_job_binding",
    "record_in_progress",
    "job_validating",
    "lease_current_at_observation",
];

/// Emit only an admitted owned case ordinal and its opaque temporary receipt ID.
/// The runner consumes that ID privately to bind a read-only query, never stores it in its receipt.
/// Original DB error handling stays unchanged. No new query executes with the application role.
pub(super) fn observe(
    req: &RevisionCommitRequest,
    lease: RevisionLeaseIdentity,
    receipt: ArtifactId,
) {
    let case = owned_case(
        req.project_id().as_uuid().as_u128(),
        req.branch_id().as_uuid().as_u128(),
        req.new_revision_id().as_uuid().as_u128(),
        lease.idempotency_key.as_u128(),
        lease.job_id.as_u128(),
    );
    if let Some(case) = case {
        eprintln!(
            "P84_ORACLE_CONTEXT case={case} receipt={}",
            receipt.as_uuid().simple()
        );
    } else {
        eprintln!("P84_ORACLE_CONTEXT_STATE code=unavailable");
    }
}

fn owned_case(project: u128, branch: u128, revision: u128, key: u128, job: u128) -> Option<u8> {
    let case = key
        .checked_sub(500)
        .and_then(|i| u8::try_from(i).ok())
        .filter(|i| *i < 10)?;
    let offset = u128::from(case);
    (project == 2 && branch == 100 + offset && revision == 200 + offset && job == 600 + offset)
        .then_some(case)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn only_ten_original_owned_call_contexts_are_admitted() {
        for case in 0..10 {
            assert_eq!(
                owned_case(2, 100 + case, 200 + case, 500 + case, 600 + case),
                Some(case as u8)
            );
        }
        for key in [0, 499, 510, u128::MAX] {
            assert_eq!(owned_case(2, 100, 200, key, 600), None);
        }
    }
    #[test]
    fn project_branch_result_revision_and_job_substitutions_are_not_defaulted() {
        for (project, branch, revision, job) in [
            (3, 100, 200, 600),
            (2, 101, 200, 600),
            (2, 100, 201, 600),
            (2, 100, 200, 601),
        ] {
            assert_eq!(owned_case(project, branch, revision, 500, job), None);
        }
    }
    #[test]
    fn every_fixed_boolean_column_is_unique_and_in_the_bound_query() {
        let unique: std::collections::BTreeSet<_> = CHECKS.into_iter().collect();
        assert_eq!(unique.len(), CHECKS.len());
        for name in CHECKS {
            assert_eq!(
                SQL.matches(&format!(" AS {name}\n")).count()
                    + SQL.matches(&format!(" AS {name},\n")).count(),
                1
            );
        }
    }
    #[test]
    fn query_has_no_legacy_defaults_or_mutating_or_locking_commands() {
        let text: String = SQL
            .lines()
            .filter(|line| !line.trim_start().starts_with("--"))
            .collect::<Vec<_>>()
            .join("\n");
        assert!(text.trim_start().starts_with("SELECT"));
        for command in [
            "UPDATE ",
            "DELETE ",
            "INSERT ",
            "ALTER ",
            "GRANT ",
            "REVOKE ",
            "FOR SHARE",
            "FOR UPDATE",
            "set_config(",
            "idempotency_v2_head_matches(",
        ] {
            assert!(!text.contains(command));
        }
        assert!(text.contains("v.revision_id=$6"));
        assert!(text.contains("ra.artifact_id=$7"));
        assert!(text.contains("r.idempotency_key=$4"));
        assert!(!text.contains("coalesce("));
    }
}
