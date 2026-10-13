//! Original admitted SQL21 connector; no direct table writes, role escalation or default trust.
use super::{
    FormulaPolicyRevocationError as Error, FormulaPolicyRevocationRecord,
    FormulaPolicyRevocationRepository, PolicyReadScope, SourcePolicyVersion,
};
use revision_service::{
    RevisionError, RevisionRequestContext,
    postgres::source_formula_policy::{
        LocalPostgresSourceFormulaPolicyRepository,
        revocation::SourceFormulaPolicyRevocationRequest,
    },
};
use std::fmt;

pub struct PostgresFormulaPolicyRevoker {
    repository: LocalPostgresSourceFormulaPolicyRepository,
}
impl fmt::Debug for PostgresFormulaPolicyRevoker {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PostgresFormulaPolicyRevoker(<redacted>)")
    }
}
impl PostgresFormulaPolicyRevoker {
    #[must_use]
    pub const fn new(repository: LocalPostgresSourceFormulaPolicyRepository) -> Self {
        Self { repository }
    }
}
impl super::FormulaPolicyRepository for PostgresFormulaPolicyRevoker {
    fn read_current_formula_policy(
        &self,
        scope: &PolicyReadScope,
    ) -> Result<SourcePolicyVersion, super::super::StoredFormulaPolicyError> {
        super::super::postgres::PostgresFormulaPolicyProvider::new(self.repository.clone())
            .read_current_formula_policy(scope)
    }
}
impl FormulaPolicyRevocationRepository for PostgresFormulaPolicyRevoker {
    fn revoke_formula_policy(
        &self,
        scope: &PolicyReadScope,
        record: &FormulaPolicyRevocationRecord,
    ) -> Result<SourcePolicyVersion, Error> {
        let v = record.version();
        let b = &v.binding;
        // The current editor need not be the historical creator of the policy.
        if scope.tenant() != b.tenant
            || scope.project() != b.project
            || scope.branch() != b.branch
            || scope.document() != &b.document
            || scope.head().revision_id() != Some(b.source_revision)
            || scope.head().generation() != b.source_head_generation
        {
            return Err(Error::Binding);
        }
        let request = SourceFormulaPolicyRevocationRequest::new(
            b.project,
            b.branch,
            b.document.as_str().into(),
            b.policy_version,
            b.policy_generation,
        )
        .map_err(|_| Error::Binding)?;
        let row = self
            .repository
            .revoke_policy(
                &RevisionRequestContext::new(scope.tenant(), scope.subject()),
                &request,
            )
            .map_err(map_revision_error)?;
        if row.tenant != b.tenant
            || row.project != b.project
            || row.branch != b.branch
            || row.document != b.document.as_str()
            || row.version != b.policy_version
            || row.generation != b.policy_generation
            || row.revoked_by != scope.subject()
        {
            return Err(Error::OutcomeUnknown);
        }
        Ok(v.clone())
    }
}
fn map_revision_error(error: RevisionError) -> Error {
    if error == RevisionError::CommitOutcomeUnknown {
        Error::OutcomeUnknown
    } else {
        Error::Repository
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn ambiguous_commit_is_never_mapped_to_retryable_denial() {
        assert_eq!(
            map_revision_error(RevisionError::CommitOutcomeUnknown),
            Error::OutcomeUnknown
        );
        for e in [
            RevisionError::InvalidRequest,
            RevisionError::NotFound,
            RevisionError::RepositoryFailure,
        ] {
            assert_eq!(map_revision_error(e), Error::Repository);
        }
    }
}
