//! Exact SQL21 policy revocation; no new schema, retry, source deletion or native authority.
use super::{
    BranchId, IsolationLevel, LocalPostgresSourceFormulaPolicyRepository, ProjectId, RevisionError,
    RevisionRepository, RevisionRequestContext, SubjectDigest, TenantId, Uuid, db_error,
};
use std::fmt;

const REVOKE: &str = "SELECT hwpx_agent.revoke_source_formula_policy_v1(
    $1,$2,$3,$4::character(64),$5,$6,$7)";

/// Explicit server metadata identity, never a deserialized authorization flag.
/// No source-head prerequisite: administrators can revoke a latest policy after its source moves.
pub struct SourceFormulaPolicyRevocationRequest {
    project: ProjectId,
    branch: BranchId,
    document: String,
    version: Uuid,
    generation: i64,
}
impl fmt::Debug for SourceFormulaPolicyRevocationRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceFormulaPolicyRevocationRequest(<redacted>)")
    }
}
impl SourceFormulaPolicyRevocationRequest {
    /// # Errors
    /// Rejects malformed SQL21 document IDs, nil versions and zero/overflow generations.
    pub fn new(
        project: ProjectId,
        branch: BranchId,
        document: String,
        version: Uuid,
        generation: u64,
    ) -> Result<Self, RevisionError> {
        let bytes = document.as_bytes();
        if bytes.is_empty()
            || bytes.len() > 128
            || !bytes[0].is_ascii_alphanumeric()
            || !bytes
                .iter()
                .all(|b| b.is_ascii_alphanumeric() || b"._:-".contains(b))
            || version.is_nil()
            || generation == 0
            || generation > i64::MAX as u64
        {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self {
            project,
            branch,
            document,
            version,
            generation: i64::try_from(generation).map_err(|_| RevisionError::InvalidRequest)?,
        })
    }
}

/// Returned only after the scoped transaction's commit acknowledgement, not a native/issuer grant.
#[derive(Clone, Eq, PartialEq)]
pub struct SourceFormulaPolicyRevocationReceipt {
    pub tenant: TenantId,
    pub project: ProjectId,
    pub branch: BranchId,
    pub document: String,
    pub version: Uuid,
    pub generation: u64,
    pub revoked_by: SubjectDigest,
}
impl fmt::Debug for SourceFormulaPolicyRevocationReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceFormulaPolicyRevocationReceipt(<redacted>)")
    }
}
impl LocalPostgresSourceFormulaPolicyRepository {
    /// Uses the admitted SQL21 function's current editor role, branch lock and latest version CAS.
    /// It neither deletes the policy artifact nor retries duplicate or ambiguous writes.
    /// # Errors
    /// Fixed subject/tenant, SQL role/CAS/duplicate failures deny. A lost commit acknowledgement
    /// remains `CommitOutcomeUnknown`; callers must not blindly retry.
    pub fn revoke_policy(
        &self,
        context: &RevisionRequestContext,
        request: &SourceFormulaPolicyRevocationRequest,
    ) -> Result<SourceFormulaPolicyRevocationReceipt, RevisionError> {
        self.inner.authorize_context(context)?;
        self.inner
            .scoped(context.tenant_id(), IsolationLevel::ReadCommitted, |tx| {
                let row = tx
                    .query_one(
                        REVOKE,
                        &[
                            &context.tenant_id().as_uuid(),
                            &request.project.as_uuid(),
                            &request.branch.as_uuid(),
                            &context.subject().hex(),
                            &request.document,
                            &request.version,
                            &request.generation,
                        ],
                    )
                    .map_err(db_error)?;
                if row.columns().len() != 1
                    || row.columns()[0].type_() != &postgres::types::Type::VOID
                {
                    return Err(RevisionError::RepositoryFailure);
                }
                Ok(SourceFormulaPolicyRevocationReceipt {
                    tenant: context.tenant_id(),
                    project: request.project,
                    branch: request.branch,
                    document: request.document.clone(),
                    version: request.version,
                    generation: u64::try_from(request.generation)
                        .map_err(|_| RevisionError::InvalidRequest)?,
                    revoked_by: context.subject(),
                })
            })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn request_rejects_nil_zero_overflow_and_malformed_documents() {
        let project = ProjectId::generate();
        let branch = BranchId::generate();
        for document in [
            "".into(),
            ".bad".into(),
            "has space".into(),
            "../path".into(),
            "한글".into(),
            "a".repeat(129),
        ] {
            assert!(
                SourceFormulaPolicyRevocationRequest::new(
                    project,
                    branch,
                    document,
                    Uuid::new_v4(),
                    1
                )
                .is_err()
            );
        }
        for (version, generation) in [
            (Uuid::nil(), 1),
            (Uuid::new_v4(), 0),
            (Uuid::new_v4(), i64::MAX as u64 + 1),
            (Uuid::new_v4(), u64::MAX),
        ] {
            assert!(
                SourceFormulaPolicyRevocationRequest::new(
                    project,
                    branch,
                    "valid-doc".into(),
                    version,
                    generation
                )
                .is_err()
            );
        }
    }
    #[test]
    fn last_generation_and_document_boundaries_are_exact_and_redacted() -> Result<(), RevisionError>
    {
        for (document, generation) in [("a".into(), 1), ("a".repeat(128), i64::MAX as u64)] {
            let version = Uuid::new_v4();
            let request = SourceFormulaPolicyRevocationRequest::new(
                ProjectId::generate(),
                BranchId::generate(),
                document.clone(),
                version,
                generation,
            )?;
            assert_eq!(request.document, document);
            assert_eq!(request.version, version);
            assert_eq!(
                u64::try_from(request.generation).map_err(|_| RevisionError::InvalidRequest)?,
                generation
            );
            assert_eq!(
                format!("{request:?}"),
                "SourceFormulaPolicyRevocationRequest(<redacted>)"
            );
        }
        Ok(())
    }
}
