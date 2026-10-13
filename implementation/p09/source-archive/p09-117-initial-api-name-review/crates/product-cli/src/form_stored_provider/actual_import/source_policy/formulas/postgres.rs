//! Field-specific SQL21 repository bridge to the original P116 source/artifact/target consumer.
use super::super::{PolicyReadScope, SourcePolicyBinding, SourcePolicyVersion};
use super::{FormulaPolicyRepository, StoredFormulaPolicyError};
use revision_service::{
    RevisionRequestContext,
    postgres::source_formula_policy::{
        LocalPostgresSourceFormulaPolicyRepository, SourceFormulaPolicyReadRequest,
    },
};
use std::fmt;
pub struct PostgresFormulaPolicyProvider {
    repository: LocalPostgresSourceFormulaPolicyRepository,
}
impl fmt::Debug for PostgresFormulaPolicyProvider {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PostgresFormulaPolicyProvider(<redacted>)")
    }
}
impl PostgresFormulaPolicyProvider {
    #[must_use]
    pub const fn new(repository: LocalPostgresSourceFormulaPolicyRepository) -> Self {
        Self { repository }
    }
}
impl FormulaPolicyRepository for PostgresFormulaPolicyProvider {
    fn read_current_formula_policy(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, StoredFormulaPolicyError> {
        let context = RevisionRequestContext::new(scope.tenant(), scope.subject());
        let request = SourceFormulaPolicyReadRequest::new(
            scope.project(),
            scope.branch(),
            scope.document().as_str().to_owned(),
            scope.head(),
        )
        .map_err(|_| StoredFormulaPolicyError::Repository)?;
        let row = self
            .repository
            .read_current(&context, &request)
            .map_err(|_| StoredFormulaPolicyError::Repository)?;
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
                    .ok_or(StoredFormulaPolicyError::Repository)?,
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
