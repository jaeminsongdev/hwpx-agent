//! New SQL21 registration source + exact readback in one original scoped transaction; actual SQL `NOT_RUN`.
use super::{
    ArtifactId, ContentDigest, IsolationLevel, LocalPostgresSourceFormulaPolicyRepository, READ,
    RevisionError, RevisionRepository, RevisionRequestContext, SourceFormulaPolicyReadRequest,
    SourceFormulaPolicyRecord, Uuid, db_error, decode_row, value,
};
use std::fmt;

/// Trusted server-side source metadata, not a deserializable approval or caller graph.
#[derive(Clone, Copy)]
pub struct FormulaPolicySourceDigests {
    pub result: ArtifactId,
    pub package: ContentDigest,
    pub provenance: ContentDigest,
    pub graph: ContentDigest,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{BranchId, ProjectId, RevisionHead, RevisionId};

    fn request(
        expected: u64,
        version: Uuid,
        alias: bool,
    ) -> Result<SourceFormulaPolicyRegistrationRequest, RevisionError> {
        let source = ArtifactId::generate();
        SourceFormulaPolicyRegistrationRequest::new(
            SourceFormulaPolicyReadRequest::new(
                ProjectId::generate(),
                BranchId::generate(),
                "private-formula-document".into(),
                RevisionHead::new(Some(RevisionId::generate()), 1)?,
            )?,
            expected,
            version,
            if alias {
                source
            } else {
                ArtifactId::generate()
            },
            ContentDigest::of(b"policy"),
            FormulaPolicySourceDigests {
                result: source,
                package: ContentDigest::of(b"package"),
                provenance: ContentDigest::of(b"provenance"),
                graph: ContentDigest::of(b"observed form graph"),
            },
        )
    }
    #[test]
    fn typed_formula_registration_rejects_nil_version_generation_overflow_and_artifact_alias() {
        for (expected, version, alias) in [
            (0, Uuid::nil(), false),
            (i64::MAX as u64, Uuid::new_v4(), false),
            (u64::MAX, Uuid::new_v4(), false),
            (0, Uuid::new_v4(), true),
        ] {
            assert!(matches!(
                request(expected, version, alias),
                Err(RevisionError::InvalidRequest)
            ));
        }
    }
    #[test]
    fn zero_and_last_admissible_generations_are_exact_and_debug_is_redacted()
    -> Result<(), RevisionError> {
        for expected in [0, i64::MAX as u64 - 1] {
            let version = Uuid::new_v4();
            let r = request(expected, version, false)?;
            assert_eq!(
                r.expected_generation,
                i64::try_from(expected).map_err(|_| RevisionError::InvalidRequest)?
            );
            assert_eq!(r.version, version);
            assert_eq!(
                format!("{r:?}"),
                "SourceFormulaPolicyRegistrationRequest(<redacted>)"
            );
            assert_eq!(
                format!("{:?}", r.source),
                "FormulaPolicySourceDigests(<redacted>)"
            );
        }
        Ok(())
    }
}
impl fmt::Debug for FormulaPolicySourceDigests {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaPolicySourceDigests(<redacted>)")
    }
}
pub struct SourceFormulaPolicyRegistrationRequest {
    scope: SourceFormulaPolicyReadRequest,
    expected_generation: i64,
    version: Uuid,
    artifact: ArtifactId,
    digest: ContentDigest,
    source: FormulaPolicySourceDigests,
}
impl fmt::Debug for SourceFormulaPolicyRegistrationRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceFormulaPolicyRegistrationRequest(<redacted>)")
    }
}
impl SourceFormulaPolicyRegistrationRequest {
    /// # Errors
    /// Rejects nil version, exhausted generation or a policy/source artifact alias.
    pub fn new(
        scope: SourceFormulaPolicyReadRequest,
        expected_generation: u64,
        version: Uuid,
        artifact: ArtifactId,
        digest: ContentDigest,
        source: FormulaPolicySourceDigests,
    ) -> Result<Self, RevisionError> {
        if version.is_nil() || expected_generation >= i64::MAX as u64 || artifact == source.result {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self {
            scope,
            expected_generation: i64::try_from(expected_generation)
                .map_err(|_| RevisionError::InvalidRequest)?,
            version,
            artifact,
            digest,
            source,
        })
    }
}
impl LocalPostgresSourceFormulaPolicyRepository {
    /// Writes through the existing named SQL API; readback is checked before commit.
    /// # Errors
    /// Denies source/head/generation/role/ACL drift. Commit acknowledgement loss stays
    /// `CommitOutcomeUnknown`; no automatic retry or permission escalation.
    pub fn register_policy(
        &self,
        context: &RevisionRequestContext,
        request: &SourceFormulaPolicyRegistrationRequest,
    ) -> Result<SourceFormulaPolicyRecord, RevisionError> {
        self.inner.authorize_context(context)?;
        self.inner.scoped(context.tenant_id(), IsolationLevel::ReadCommitted, |tx| {
            let s=&request.scope;
            let tenant=context.tenant_id().as_uuid(); let project=s.project.as_uuid(); let branch=s.branch.as_uuid();
            let subject=context.subject().hex();
            let revision=s.head.revision_id().ok_or(RevisionError::InvalidHead)?.as_uuid();
            let head=i64::try_from(s.head.generation()).map_err(|_|RevisionError::InvalidHead)?;
            let generation=request.expected_generation+1;
            let row=tx.query_one("SELECT hwpx_agent.register_source_formula_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10::character(64),$11::character(64),$12::character(64),$13,$14::character(64)) AS generation",&[
                &tenant,&project,&branch,&subject,&s.document,&request.version,&request.expected_generation,
                &revision,&head,&request.source.package.hex(),&request.source.provenance.hex(),&request.source.graph.hex(),
                &request.artifact.as_uuid(),&request.digest.hex()]).map_err(db_error)?;
            if value::<i64>(&row,"generation")? != generation { return Err(RevisionError::RepositoryFailure); }
            let row=tx.query_one(READ,&[&tenant,&project,&branch,&subject,&s.document,&revision,&head]).map_err(db_error)?;
            let record=decode_row(&row,context,s)?;
            if record.version!=request.version || record.generation!=u64::try_from(generation).map_err(|_|RevisionError::RepositoryFailure)?
                || record.policy_artifact!=request.artifact || record.policy_digest!=request.digest
                || record.source_result!=request.source.result || record.source_package!=request.source.package
                || record.source_provenance!=request.source.provenance || record.observed_graph!=request.source.graph
                || record.creator!=context.subject() { return Err(RevisionError::RepositoryFailure); }
            Ok(record)
        })
    }
}
