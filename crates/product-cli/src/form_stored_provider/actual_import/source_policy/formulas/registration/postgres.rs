//! Generated validated formula DATA -> original SQL21 metadata CAS, not an issuer.
use super::{
    FormulaPolicyRegistrationError as Error, FormulaPolicyRegistrationRecord,
    FormulaPolicyRegistrationRepository, PolicyReadScope, SourcePolicyVersion,
};
use revision_service::{
    RevisionError, RevisionRequestContext,
    postgres::source_formula_policy::{
        LocalPostgresSourceFormulaPolicyRepository, SourceFormulaPolicyReadRequest,
        registration::{FormulaPolicySourceDigests, SourceFormulaPolicyRegistrationRequest},
    },
};
use std::fmt;

pub struct PostgresFormulaPolicyRegistrar {
    repository: LocalPostgresSourceFormulaPolicyRepository,
}
impl fmt::Debug for PostgresFormulaPolicyRegistrar {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PostgresFormulaPolicyRegistrar(<redacted>)")
    }
}
impl PostgresFormulaPolicyRegistrar {
    #[must_use]
    pub const fn new(repository: LocalPostgresSourceFormulaPolicyRepository) -> Self {
        Self { repository }
    }
}
impl FormulaPolicyRegistrationRepository for PostgresFormulaPolicyRegistrar {
    fn register_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRegistrationRecord,
    ) -> Result<SourcePolicyVersion, Error> {
        let v = record.version();
        let b = &v.binding;
        if scope.tenant() != b.tenant
            || scope.subject() != b.creator_subject
            || scope.project() != b.project
            || scope.branch() != b.branch
            || scope.document() != &b.document
            || scope.head().revision_id() != Some(b.source_revision)
            || scope.head().generation() != b.source_head_generation
            || record.expected_generation() >= i64::MAX as u64
            || b.policy_generation != record.expected_generation() + 1
        {
            return Err(Error::Binding);
        }
        let request = SourceFormulaPolicyRegistrationRequest::new(
            SourceFormulaPolicyReadRequest::new(
                b.project,
                b.branch,
                b.document.as_str().into(),
                scope.head(),
            )
            .map_err(|_| Error::Binding)?,
            record.expected_generation(),
            b.policy_version,
            v.artifact,
            v.digest,
            FormulaPolicySourceDigests {
                result: b.source_result_artifact,
                package: b.source_package_sha256,
                provenance: b.source_provenance_sha256,
                graph: b.observed_graph_sha256,
            },
        )
        .map_err(|_| Error::Binding)?;
        let row = self
            .repository
            .register_policy(
                &RevisionRequestContext::new(scope.tenant(), scope.subject()),
                &request,
            )
            .map_err(|e| {
                if e == RevisionError::CommitOutcomeUnknown {
                    Error::OutcomeUnknown
                } else {
                    Error::Repository
                }
            })?;
        if row.tenant != b.tenant
            || row.project != b.project
            || row.branch != b.branch
            || row.document != b.document.as_str()
            || row.source_head != scope.head()
            || row.source_result != b.source_result_artifact
            || row.source_package != b.source_package_sha256
            || row.source_provenance != b.source_provenance_sha256
            || row.observed_graph != b.observed_graph_sha256
            || row.version != b.policy_version
            || row.generation != b.policy_generation
            || row.creator != b.creator_subject
            || row.policy_artifact != v.artifact
            || row.policy_digest != v.digest
        {
            return Err(Error::OutcomeUnknown);
        }
        Ok(v.clone())
    }
}
