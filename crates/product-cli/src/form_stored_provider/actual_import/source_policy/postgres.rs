//! Real source policy SQL20 record -> unchanged strict encrypted payload consumer.
use super::{
    PolicyReadScope, SourcePolicyBinding, SourcePolicyRepository, SourcePolicyVersion,
    StoredSourcePolicyError,
};
use revision_service::{
    RevisionRequestContext,
    postgres::source_form_policy::{LocalPostgresSourcePolicyRepository, SourcePolicyReadRequest},
};
use std::fmt;

pub struct PostgresSourcePolicyProvider {
    repository: LocalPostgresSourcePolicyRepository,
}
impl fmt::Debug for PostgresSourcePolicyProvider {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PostgresSourcePolicyProvider(<redacted>)")
    }
}
impl PostgresSourcePolicyProvider {
    #[must_use]
    pub const fn new(repository: LocalPostgresSourcePolicyRepository) -> Self {
        Self { repository }
    }
}
impl SourcePolicyRepository for PostgresSourcePolicyProvider {
    fn read_current(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredSourcePolicyError> {
        let context = RevisionRequestContext::new(scope.tenant(), scope.subject());
        let request = SourcePolicyReadRequest::new(
            scope.project(),
            scope.branch(),
            scope.document().as_str().to_owned(),
            scope.head(),
        )
        .map_err(|_| StoredSourcePolicyError::Repository)?;
        let row = self
            .repository
            .read_current(&context, &request)
            .map_err(|_| StoredSourcePolicyError::Repository)?;
        Ok(SourcePolicyVersion {
            artifact: row.policy_artifact,
            digest: row.policy_digest,
            binding: SourcePolicyBinding {
                tenant: row.tenant,
                project: row.project,
                branch: row.branch,
                document: scope.document().clone(),
                source_revision: row
                    .source_head
                    .revision_id()
                    .ok_or(StoredSourcePolicyError::Repository)?,
                source_head_generation: row.source_head.generation(),
                source_result_artifact: row.source_result,
                source_package_sha256: row.source_package,
                source_provenance_sha256: row.source_provenance,
                observed_graph_sha256: row.observed_graph,
                policy_version: row.version,
                policy_generation: row.generation,
                creator_subject: row.creator,
            },
        })
    }
}
