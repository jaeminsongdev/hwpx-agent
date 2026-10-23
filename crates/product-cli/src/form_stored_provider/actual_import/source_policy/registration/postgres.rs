//! Typed generated policy registration -> admitted original SQL20 CAS.
use super::{
    PolicyReadScope, PolicyRegistrationError, PolicyRegistrationRecord,
    SourcePolicyRegistrationRepository, SourcePolicyVersion,
};
use revision_service::{
    RevisionError, RevisionRequestContext,
    postgres::source_form_policy::{
        LocalPostgresSourcePolicyRepository, SourcePolicyReadRequest,
        registration::{PolicySourceDigests, SourcePolicyRegistrationRequest},
    },
};
use std::fmt;
pub struct PostgresSourcePolicyRegistrar {
    repository: LocalPostgresSourcePolicyRepository,
}
impl fmt::Debug for PostgresSourcePolicyRegistrar {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PostgresSourcePolicyRegistrar(<redacted>)")
    }
}
impl PostgresSourcePolicyRegistrar {
    #[must_use]
    pub const fn new(repository: LocalPostgresSourcePolicyRepository) -> Self {
        Self { repository }
    }
}
impl SourcePolicyRegistrationRepository for PostgresSourcePolicyRegistrar {
    fn register(
        &self,
        scope: &PolicyReadScope,
        r: &PolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, PolicyRegistrationError> {
        let b = &r.binding;
        if scope.tenant() != b.tenant
            || scope.subject() != b.creator_subject
            || scope.project() != b.project
            || scope.branch() != b.branch
            || scope.document() != &b.document
            || scope.head().revision_id() != Some(b.source_revision)
            || scope.head().generation() != b.source_head_generation
            || b.policy_generation != r.expected_generation + 1
        {
            return Err(PolicyRegistrationError::Binding);
        }
        let request = SourcePolicyRegistrationRequest::new(
            SourcePolicyReadRequest::new(
                b.project,
                b.branch,
                b.document.as_str().into(),
                scope.head(),
            )
            .map_err(|_| PolicyRegistrationError::Binding)?,
            r.expected_generation,
            b.policy_version,
            r.version.artifact,
            r.version.digest,
            PolicySourceDigests {
                result: b.source_result_artifact,
                package: b.source_package_sha256,
                provenance: b.source_provenance_sha256,
                graph: b.observed_graph_sha256,
            },
        )
        .map_err(|_| PolicyRegistrationError::Binding)?;
        let row = self
            .repository
            .register_policy(
                &RevisionRequestContext::new(scope.tenant(), scope.subject()),
                &request,
            )
            .map_err(|e| {
                if e == RevisionError::CommitOutcomeUnknown {
                    PolicyRegistrationError::OutcomeUnknown
                } else {
                    PolicyRegistrationError::Repository
                }
            })?;
        if row.version != b.policy_version
            || row.generation != b.policy_generation
            || row.policy_artifact != r.version.artifact
            || row.policy_digest != r.version.digest
        {
            return Err(PolicyRegistrationError::OutcomeUnknown);
        }
        Ok(r.version.clone())
    }
}
