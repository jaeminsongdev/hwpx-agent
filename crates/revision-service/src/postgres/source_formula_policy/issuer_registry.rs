//! Explicit SQL22 read admission; does not grant rights, provision keys or install a writer.
pub mod management;
pub mod stored_revision_jobs;
use super::{
    Arc, ArtifactId, BranchId, Client, Config, ContentDigest, Duration, IsolationLevel,
    LocalPostgresRevisionConfig, LocalPostgresRevisionRepository,
    LocalPostgresSourceFormulaPolicyRepository, MIGRATION20, MIGRATION21, MIGRATIONS, Mutex, NoTls,
    ProjectId, RevisionCommitLease, RevisionError, RevisionHead, RevisionRepository,
    RevisionRequestContext, Row, SourceFormulaPolicyReadRequest, SubjectDigest, TenantId, Uuid,
    admit_form_policy_security, admit_guarded_writes, admit_policy_security, admit_read_policies,
    artifact_id, db_error, fmt, positive_generation, row_digest, value,
};

const MIGRATION22: &[u8] = include_bytes!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../migrations/postgres/0022_p09_formula_issuer_registry.up.sql"
));
const READ_TRUST: &str = "SELECT tenant_id,project_id,trust_version_id,generation,issuer,
    valid_from,valid_until,max_approval_lifetime,trust_artifact_id,
    trust_artifact_sha256::text,created_by_subject_sha256::text
    FROM hwpx_agent.read_formula_issuer_trust_v1($1,$2,$3::character(64))";
const READ_APPROVAL: &str = "SELECT tenant_id,project_id,branch_id,document_id,
    approval_version_id,generation,policy_version_id,policy_generation,trust_version_id,
    trust_generation,approval_artifact_id,approval_artifact_sha256::text,
    created_by_subject_sha256::text FROM hwpx_agent.read_formula_approval_v1(
    $1,$2,$3,$4::character(64),$5,$6,$7,$8,$9)";

/// Trusted repository interface; caller payloads cannot supply an approval or a trust key.
pub trait FormulaIssuerRegistryRepository: Send + Sync {
    /// # Errors
    /// Must deny foreign subjects, unavailable/revoked/latest roots and unauthorized artifacts.
    fn read_trust(
        &self,
        context: &RevisionRequestContext,
        project: ProjectId,
    ) -> Result<FormulaIssuerTrustRecord, RevisionError>;
    /// # Errors
    /// Must revalidate current policy/head/root and deny revoked/absent/latest approval.
    fn read_approval(
        &self,
        context: &RevisionRequestContext,
        request: &FormulaApprovalReadRequest,
    ) -> Result<FormulaApprovalRecord, RevisionError>;
}

/// Non-deserializable fixed source/policy request, not authority conferred by an artifact ID.
pub struct FormulaApprovalReadRequest {
    source: SourceFormulaPolicyReadRequest,
    policy_version: Uuid,
    policy_generation: u64,
}
impl FormulaApprovalReadRequest {
    /// # Errors
    /// Rejects nil policy versions and zero/SQL-bigint-overflow generations.
    pub fn new(
        source: SourceFormulaPolicyReadRequest,
        policy_version: Uuid,
        policy_generation: u64,
    ) -> Result<Self, RevisionError> {
        if policy_version.is_nil() || !generation(policy_generation) {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self {
            source,
            policy_version,
            policy_generation,
        })
    }
    #[must_use]
    pub const fn project(&self) -> ProjectId {
        self.source.project
    }
    #[must_use]
    pub const fn branch(&self) -> BranchId {
        self.source.branch
    }
    #[must_use]
    pub fn document(&self) -> &str {
        &self.source.document
    }
    #[must_use]
    pub const fn head(&self) -> RevisionHead {
        self.source.head
    }
    #[must_use]
    pub const fn policy_version(&self) -> Uuid {
        self.policy_version
    }
    #[must_use]
    pub const fn policy_generation(&self) -> u64 {
        self.policy_generation
    }
}
impl fmt::Debug for FormulaApprovalReadRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaApprovalReadRequest(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FormulaIssuerTrustRecord {
    pub tenant: TenantId,
    pub project: ProjectId,
    pub version: Uuid,
    pub generation: u64,
    pub issuer: String,
    pub valid_from: u64,
    pub valid_until: u64,
    pub max_approval_lifetime: u64,
    pub artifact: ArtifactId,
    pub digest: ContentDigest,
    pub creator: SubjectDigest,
}
impl FormulaIssuerTrustRecord {
    /// # Errors
    /// Validates typed row shape and scope, not artifact bytes, trust authority or current time.
    pub fn validate_for(
        &self,
        context: &RevisionRequestContext,
        project: ProjectId,
    ) -> Result<(), RevisionError> {
        if self.tenant != context.tenant_id()
            || self.project != project
            || self.version.is_nil()
            || !generation(self.generation)
            || self.issuer.is_empty()
            || self.issuer.len() > 64
            || !self
                .issuer
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b"._-".contains(&b))
            || self.valid_from > i64::MAX as u64
            || self.valid_until > i64::MAX as u64
            || self.valid_until <= self.valid_from
            || self.max_approval_lifetime == 0
            || self.max_approval_lifetime > 86400
        {
            return Err(RevisionError::RepositoryFailure);
        }
        Ok(())
    }
}
impl fmt::Debug for FormulaIssuerTrustRecord {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaIssuerTrustRecord(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq)]
pub struct FormulaApprovalRecord {
    pub tenant: TenantId,
    pub project: ProjectId,
    pub branch: BranchId,
    pub document: String,
    pub version: Uuid,
    pub generation: u64,
    pub policy_version: Uuid,
    pub policy_generation: u64,
    pub trust_version: Uuid,
    pub trust_generation: u64,
    pub artifact: ArtifactId,
    pub digest: ContentDigest,
    pub creator: SubjectDigest,
}
impl FormulaApprovalRecord {
    /// # Errors
    /// Rejects foreign/malformed metadata; historical creator need not equal the current reader.
    pub fn validate_for(
        &self,
        context: &RevisionRequestContext,
        request: &FormulaApprovalReadRequest,
    ) -> Result<(), RevisionError> {
        if self.tenant != context.tenant_id()
            || self.project != request.project()
            || self.branch != request.branch()
            || self.document != request.document()
            || self.version.is_nil()
            || !generation(self.generation)
            || self.policy_version != request.policy_version()
            || self.policy_generation != request.policy_generation()
            || self.trust_version.is_nil()
            || !generation(self.trust_generation)
        {
            return Err(RevisionError::RepositoryFailure);
        }
        Ok(())
    }
}
impl fmt::Debug for FormulaApprovalRecord {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormulaApprovalRecord(<redacted>)")
    }
}
fn generation(n: u64) -> bool {
    n > 0 && i64::try_from(n).is_ok()
}

#[derive(Clone)]
pub struct LocalPostgresFormulaIssuerRegistryRepository {
    policy: LocalPostgresSourceFormulaPolicyRepository,
}
impl fmt::Debug for LocalPostgresFormulaIssuerRegistryRepository {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("LocalPostgresFormulaIssuerRegistryRepository(<redacted>)")
    }
}
impl LocalPostgresFormulaIssuerRegistryRepository {
    /// Separately admits schema1..22 and read-only SQL22 rights. SQL19/20/21 constructors stay exact.
    /// # Errors
    /// Rejects unsafe roles/schema/table/function rights, changed fingerprints or transport failure.
    pub fn connect(
        config: &LocalPostgresRevisionConfig,
        context: RevisionRequestContext,
        lease: Option<RevisionCommitLease>,
    ) -> Result<Self, RevisionError> {
        let mut client = Config::new().host("127.0.0.1").port(config.port).dbname(&config.database)
            .user(&config.user).password(config.password.as_bytes()).connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-formula-registry-read-schema22")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog")
            .connect(NoTls).map_err(db_error)?;
        admit_schema22(&mut client)?;
        admit_read_policies(&mut client)?;
        admit_guarded_writes(&mut client)?;
        admit_form_policy_security(&mut client)?;
        admit_policy_security(&mut client)?;
        admit_registry_security(&mut client)?;
        Ok(Self {
            policy: LocalPostgresSourceFormulaPolicyRepository {
                inner: LocalPostgresRevisionRepository {
                    context,
                    lease,
                    client: Arc::new(Mutex::new(client)),
                },
            },
        })
    }
    /// Reuses unchanged SQL21 policy methods through the admitted SQL22 connection.
    #[must_use]
    pub fn policy_repository(&self) -> LocalPostgresSourceFormulaPolicyRepository {
        self.policy.clone()
    }
}
impl FormulaIssuerRegistryRepository for LocalPostgresFormulaIssuerRegistryRepository {
    fn read_trust(
        &self,
        context: &RevisionRequestContext,
        project: ProjectId,
    ) -> Result<FormulaIssuerTrustRecord, RevisionError> {
        self.policy.inner.authorize_context(context)?;
        self.policy
            .inner
            .scoped(context.tenant_id(), IsolationLevel::RepeatableRead, |tx| {
                let row = tx
                    .query_one(
                        READ_TRUST,
                        &[
                            &context.tenant_id().as_uuid(),
                            &project.as_uuid(),
                            &context.subject().hex(),
                        ],
                    )
                    .map_err(db_error)?;
                if row.len() != 11 {
                    return Err(RevisionError::RepositoryFailure);
                }
                let record = FormulaIssuerTrustRecord {
                    tenant: TenantId::new(value(&row, "tenant_id")?)
                        .map_err(|_| RevisionError::RepositoryFailure)?,
                    project: ProjectId::parse(&format!(
                        "prj_{}",
                        value::<Uuid>(&row, "project_id")?.simple()
                    ))?,
                    version: value(&row, "trust_version_id")?,
                    generation: positive_generation(value(&row, "generation")?)?,
                    issuer: value(&row, "issuer")?,
                    valid_from: epoch(&row, "valid_from")?,
                    valid_until: epoch(&row, "valid_until")?,
                    max_approval_lifetime: positive_generation(value(
                        &row,
                        "max_approval_lifetime",
                    )?)?,
                    artifact: artifact_id(value(&row, "trust_artifact_id")?)?,
                    digest: row_digest(&row, "trust_artifact_sha256")?,
                    creator: subject(&row)?,
                };
                record.validate_for(context, project)?;
                Ok(record)
            })
    }
    fn read_approval(
        &self,
        context: &RevisionRequestContext,
        request: &FormulaApprovalReadRequest,
    ) -> Result<FormulaApprovalRecord, RevisionError> {
        self.policy.inner.authorize_context(context)?;
        self.policy
            .inner
            .scoped(context.tenant_id(), IsolationLevel::RepeatableRead, |tx| {
                let revision = request
                    .head()
                    .revision_id()
                    .ok_or(RevisionError::InvalidHead)?
                    .as_uuid();
                let head_generation = i64::try_from(request.head().generation())
                    .map_err(|_| RevisionError::InvalidHead)?;
                let policy_generation = i64::try_from(request.policy_generation())
                    .map_err(|_| RevisionError::InvalidRequest)?;
                let row = tx
                    .query_one(
                        READ_APPROVAL,
                        &[
                            &context.tenant_id().as_uuid(),
                            &request.project().as_uuid(),
                            &request.branch().as_uuid(),
                            &context.subject().hex(),
                            &request.document(),
                            &revision,
                            &head_generation,
                            &request.policy_version(),
                            &policy_generation,
                        ],
                    )
                    .map_err(db_error)?;
                if row.len() != 13 {
                    return Err(RevisionError::RepositoryFailure);
                }
                let record = FormulaApprovalRecord {
                    tenant: TenantId::new(value(&row, "tenant_id")?)
                        .map_err(|_| RevisionError::RepositoryFailure)?,
                    project: ProjectId::parse(&format!(
                        "prj_{}",
                        value::<Uuid>(&row, "project_id")?.simple()
                    ))?,
                    branch: BranchId::parse(&format!(
                        "brn_{}",
                        value::<Uuid>(&row, "branch_id")?.simple()
                    ))?,
                    document: value(&row, "document_id")?,
                    version: value(&row, "approval_version_id")?,
                    generation: positive_generation(value(&row, "generation")?)?,
                    policy_version: value(&row, "policy_version_id")?,
                    policy_generation: positive_generation(value(&row, "policy_generation")?)?,
                    trust_version: value(&row, "trust_version_id")?,
                    trust_generation: positive_generation(value(&row, "trust_generation")?)?,
                    artifact: artifact_id(value(&row, "approval_artifact_id")?)?,
                    digest: row_digest(&row, "approval_artifact_sha256")?,
                    creator: subject(&row)?,
                };
                record.validate_for(context, request)?;
                Ok(record)
            })
    }
}
fn epoch(row: &Row, key: &str) -> Result<u64, RevisionError> {
    u64::try_from(value::<i64>(row, key)?).map_err(|_| RevisionError::RepositoryFailure)
}
fn subject(row: &Row) -> Result<SubjectDigest, RevisionError> {
    SubjectDigest::parse(&value::<String>(row, "created_by_subject_sha256")?)
        .map_err(|_| RevisionError::RepositoryFailure)
}
fn admit_schema22(client: &mut Client) -> Result<(), RevisionError> {
    let role = client.query_one("SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication FROM pg_roles WHERE rolname=current_user", &[]).map_err(db_error)?;
    for key in [
        "rolsuper",
        "rolbypassrls",
        "rolcreaterole",
        "rolcreatedb",
        "rolreplication",
    ] {
        if value::<bool>(&role, key)? {
            return Err(RevisionError::InvalidRequest);
        }
    }
    let rows = client.query("SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 23", &[]).map_err(db_error)?;
    if rows.len() != 22 {
        return Err(RevisionError::InvalidRequest);
    }
    for (i, (row, migration)) in rows
        .iter()
        .zip(
            MIGRATIONS
                .iter()
                .chain([MIGRATION20, MIGRATION21, MIGRATION22].iter()),
        )
        .enumerate()
    {
        if value::<i64>(row, "version")?
            != i64::try_from(i + 1).map_err(|_| RevisionError::InvalidRequest)?
            || value::<String>(row, "migration_sha256")? != ContentDigest::of(migration).hex()
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    Ok(())
}
fn admit_registry_security(client: &mut Client) -> Result<(), RevisionError> {
    for table in [
        "formula_issuer_trust_versions",
        "formula_issuer_trust_revocations",
        "formula_approval_versions",
        "formula_approval_revocations",
    ] {
        let row = client.query_one("SELECT c.relrowsecurity,c.relforcerowsecurity,
            (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')) AS owner_role,
            has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') AS direct,
            (SELECT count(*)=1 AND bool_and(p.policyname='tenant_isolation' AND p.cmd='ALL'
                AND p.permissive='PERMISSIVE' AND p.qual='(tenant_id = hwpx_agent.current_tenant_id())'
                AND p.with_check='(tenant_id = hwpx_agent.current_tenant_id())')
             FROM pg_policies p WHERE p.schemaname='hwpx_agent' AND p.tablename=$1) AS policy,
            EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=c.oid AND t.tgname=$3
                AND t.tgenabled='O' AND NOT t.tgisinternal) AS immutable
            FROM pg_class c WHERE c.oid=$2::text::regclass",
            &[&table,&format!("hwpx_agent.{table}"),&format!("{table}_immutable")]).map_err(db_error)?;
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<bool>(&row, "direct")?
            || !value::<bool>(&row, "policy")?
            || !value::<bool>(&row, "immutable")?
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    for (signature, expected) in [
        (
            "hwpx_agent.read_formula_issuer_trust_v1(uuid,uuid,character)",
            true,
        ),
        (
            "hwpx_agent.read_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint)",
            true,
        ),
        (
            "hwpx_agent.lock_formula_issuer_scope_v1(uuid,uuid,character,boolean)",
            false,
        ),
        (
            "hwpx_agent.require_formula_issuer_owner_v1(uuid,uuid,character)",
            false,
        ),
        (
            "hwpx_agent.require_formula_issuer_artifact_v1(uuid,character,uuid,character,boolean,boolean)",
            false,
        ),
        (
            "hwpx_agent.register_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint,text,bigint,bigint,bigint,uuid,character)",
            false,
        ),
        (
            "hwpx_agent.revoke_formula_issuer_trust_v1(uuid,uuid,character,uuid,bigint)",
            false,
        ),
        (
            "hwpx_agent.register_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,uuid,bigint,uuid,bigint,uuid,character)",
            false,
        ),
        (
            "hwpx_agent.revoke_formula_approval_v1(uuid,uuid,uuid,character,text,uuid,uuid,bigint)",
            false,
        ),
    ] {
        let row = client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
            p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,
            (pg_has_role(p.proowner,'USAGE') OR pg_has_role(p.proowner,'SET')) AS owner_role,
            NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner)))
                WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
            FROM pg_proc p WHERE p.oid=$1::text::regprocedure", &[&signature]).map_err(db_error)?;
        if value::<bool>(&row, "allowed")? != expected
            || !value::<bool>(&row, "prosecdef")?
            || !value::<bool>(&row, "bounded_path")?
            || value::<bool>(&row, "owner_role")?
            || !value::<bool>(&row, "no_public")?
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::RevisionId;
    fn source() -> Result<SourceFormulaPolicyReadRequest, RevisionError> {
        SourceFormulaPolicyReadRequest::new(
            ProjectId::generate(),
            BranchId::generate(),
            "private-doc".into(),
            RevisionHead::new(Some(RevisionId::generate()), 1)?,
        )
    }
    #[test]
    fn approval_request_bounds_and_redacted_debug() -> Result<(), RevisionError> {
        for n in [0, u64::MAX] {
            assert!(FormulaApprovalReadRequest::new(source()?, Uuid::new_v4(), n).is_err());
        }
        assert!(FormulaApprovalReadRequest::new(source()?, Uuid::nil(), 1).is_err());
        let req = FormulaApprovalReadRequest::new(source()?, Uuid::new_v4(), i64::MAX as u64)?;
        assert_eq!(format!("{req:?}"), "FormulaApprovalReadRequest(<redacted>)");
        assert_eq!(req.policy_generation(), i64::MAX as u64);
        Ok(())
    }
    #[test]
    fn root_row_bounds_scope_and_historical_creator() -> Result<(), Box<dyn std::error::Error>> {
        let tenant = TenantId::new(Uuid::new_v4())?;
        let context = RevisionRequestContext::new(
            tenant,
            SubjectDigest::from_authenticated_subject("reader")?,
        );
        let mut row = FormulaIssuerTrustRecord {
            tenant,
            project: ProjectId::generate(),
            version: Uuid::new_v4(),
            generation: 1,
            issuer: "issuer-test".into(),
            valid_from: 0,
            valid_until: 100,
            max_approval_lifetime: 60,
            artifact: ArtifactId::generate(),
            digest: ContentDigest::of(b"synthetic"),
            creator: SubjectDigest::from_authenticated_subject("historical-owner")?,
        };
        row.validate_for(&context, row.project)?;
        assert_eq!(format!("{row:?}"), "FormulaIssuerTrustRecord(<redacted>)");
        assert!(row.validate_for(&context, ProjectId::generate()).is_err());
        for n in [0, u64::MAX] {
            row.generation = n;
            assert!(row.validate_for(&context, row.project).is_err());
        }
        row.generation = 1;
        row.valid_until = i64::MAX as u64 + 1;
        assert!(row.validate_for(&context, row.project).is_err());
        row.valid_until = 100;
        row.issuer = "bad issuer".into();
        assert!(row.validate_for(&context, row.project).is_err());
        row.issuer = "issuer-test".into();
        row.max_approval_lifetime = 86401;
        assert!(row.validate_for(&context, row.project).is_err());
        Ok(())
    }
}
