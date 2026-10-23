//! Exact schema21, subject-fixed policy reads and the unchanged leased revision implementation.
pub mod registration;
pub mod revocation;
pub mod issuer_registry;
use super::{
    Arc, ArtifactId, BranchId, Client, Config, ContentDigest, Duration, IsolationLevel,
    LocalPostgresRevisionConfig, LocalPostgresRevisionRepository, MIGRATIONS, Mutex, NoTls,
    ProjectId, READ_TABLES, RevisionCommitLease, RevisionError, RevisionHead, RevisionRepository,
    RevisionRequestContext, Row, SubjectDigest, TenantId, Uuid, admit_guarded_writes,
    admit_read_policies, artifact_id, db_error, fmt, positive_generation, row_digest, row_head,
    value,
};

const MIGRATION20: &[u8] = include_bytes!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../migrations/postgres/0020_p09_source_form_policy.up.sql"
));
const MIGRATION21: &[u8] = include_bytes!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../migrations/postgres/0021_p09_source_formula_policy.up.sql"
));
const READ: &str = "SELECT tenant_id,project_id,branch_id,document_id,policy_version_id,generation,
    source_revision_id,source_head_generation,source_result_artifact_id,source_package_sha256::text,
    source_provenance_sha256::text,observed_graph_sha256::text,policy_artifact_id,
    policy_artifact_sha256::text,created_by_subject_sha256::text
    FROM hwpx_agent.read_source_formula_policy_v1($1,$2,$3,$4::character(64),$5,$6,$7)";

#[derive(Clone)]
pub struct LocalPostgresSourceFormulaPolicyRepository {
    inner: LocalPostgresRevisionRepository,
}
impl fmt::Debug for LocalPostgresSourceFormulaPolicyRepository {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("LocalPostgresSourceFormulaPolicyRepository(<redacted>)")
    }
}
/// Server-scoped request; no public payload/source selection or authorization flags.
pub struct SourceFormulaPolicyReadRequest {
    project: ProjectId,
    branch: BranchId,
    document: String,
    head: RevisionHead,
}
impl fmt::Debug for SourceFormulaPolicyReadRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceFormulaPolicyReadRequest(<redacted>)")
    }
}
impl SourceFormulaPolicyReadRequest {
    /// # Errors
    /// Rejects a non-SQL21 document identity or empty/out-of-range source head.
    pub fn new(
        project: ProjectId,
        branch: BranchId,
        document: String,
        head: RevisionHead,
    ) -> Result<Self, RevisionError> {
        let bytes = document.as_bytes();
        if bytes.is_empty()
            || bytes.len() > 128
            || !bytes[0].is_ascii_alphanumeric()
            || !bytes
                .iter()
                .all(|b| b.is_ascii_alphanumeric() || b"._:-".contains(b))
            || head.revision_id().is_none()
            || head.generation() == 0
            || head.generation() > i64::MAX as u64
        {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self {
            project,
            branch,
            document,
            head,
        })
    }
}
#[derive(Clone, Eq, PartialEq)]
pub struct SourceFormulaPolicyRecord {
    pub tenant: TenantId,
    pub project: ProjectId,
    pub branch: BranchId,
    pub document: String,
    pub version: Uuid,
    pub generation: u64,
    pub source_head: RevisionHead,
    pub source_result: ArtifactId,
    pub source_package: ContentDigest,
    pub source_provenance: ContentDigest,
    pub observed_graph: ContentDigest,
    pub policy_artifact: ArtifactId,
    pub policy_digest: ContentDigest,
    pub creator: SubjectDigest,
}
impl fmt::Debug for SourceFormulaPolicyRecord {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("SourceFormulaPolicyRecord(<redacted>)")
    }
}
impl LocalPostgresSourceFormulaPolicyRepository {
    /// Adds exact schema21 admission without changing the original schema19/schema20 connectors.
    /// All original revision table/RLS/trigger/guarded-write checks still run.
    /// # Errors
    /// No raw DB diagnostics, automatic retry or credential retention.
    pub fn connect(
        config: &LocalPostgresRevisionConfig,
        context: RevisionRequestContext,
        lease: Option<RevisionCommitLease>,
    ) -> Result<Self, RevisionError> {
        let mut client = Config::new().host("127.0.0.1").port(config.port).dbname(&config.database)
            .user(&config.user).password(config.password.as_bytes()).connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-source-policy-schema21")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog")
            .connect(NoTls).map_err(db_error)?;
        admit_schema21(&mut client)?;
        admit_read_policies(&mut client)?;
        admit_guarded_writes(&mut client)?;
        admit_form_policy_security(&mut client)?;
        admit_policy_security(&mut client)?;
        Ok(Self {
            inner: LocalPostgresRevisionRepository {
                context,
                lease,
                client: Arc::new(Mutex::new(client)),
            },
        })
    }
    /// Same source/head/node/real leased commit code; no schema19 guard is bypassed by its old constructor.
    #[must_use]
    pub fn revision_repository(&self) -> LocalPostgresRevisionRepository {
        self.inner.clone()
    }
    /// Rechecks fixed tenant/subject plus actual SQL membership/head/latest/revocation/both ACLs.
    /// # Errors
    /// Closed denial for unauthorized/stale/malformed/absent policy or unavailable DB.
    pub fn read_current(
        &self,
        context: &RevisionRequestContext,
        request: &SourceFormulaPolicyReadRequest,
    ) -> Result<SourceFormulaPolicyRecord, RevisionError> {
        self.inner.authorize_context(context)?;
        self.inner
            .scoped(context.tenant_id(), IsolationLevel::RepeatableRead, |tx| {
                let revision = request
                    .head
                    .revision_id()
                    .ok_or(RevisionError::InvalidHead)?
                    .as_uuid();
                let generation = i64::try_from(request.head.generation())
                    .map_err(|_| RevisionError::InvalidHead)?;
                let row = tx
                    .query_one(
                        READ,
                        &[
                            &context.tenant_id().as_uuid(),
                            &request.project.as_uuid(),
                            &request.branch.as_uuid(),
                            &context.subject().hex(),
                            &request.document,
                            &revision,
                            &generation,
                        ],
                    )
                    .map_err(db_error)?;
                decode_row(&row, context, request)
            })
    }
}
fn admit_schema21(client: &mut Client) -> Result<(), RevisionError> {
    let role=client.query_one("SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication FROM pg_roles WHERE rolname=current_user",&[]).map_err(db_error)?;
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
    let rows=client.query("SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 22",&[]).map_err(db_error)?;
    if rows.len() != 21 {
        return Err(RevisionError::InvalidRequest);
    }
    for (i, (row, migration)) in rows
        .iter()
        .zip(MIGRATIONS.iter().chain([MIGRATION20, MIGRATION21].iter()))
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
fn admit_policy_security(client: &mut Client) -> Result<(), RevisionError> {
    for table in READ_TABLES {
        let r = client
            .query_one(
                "SELECT pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')
            OR has_table_privilege(current_user,c.oid,'TRIGGER') AS unsafe_owner
            FROM pg_class c WHERE c.oid=$1::text::regclass",
                &[&format!("hwpx_agent.{table}")],
            )
            .map_err(db_error)?;
        if value::<bool>(&r, "unsafe_owner")? {
            return Err(RevisionError::InvalidRequest);
        }
    }
    let global=client.query_one("SELECT has_schema_privilege(current_user,'hwpx_agent','CREATE')
        OR has_table_privilege(current_user,'hwpx_agent.schema_versions','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') AS excessive",&[]).map_err(db_error)?;
    if value::<bool>(&global, "excessive")? {
        return Err(RevisionError::InvalidRequest);
    }
    for table in [
        "source_formula_policy_versions",
        "source_formula_policy_revocations",
    ] {
        let q = format!("hwpx_agent.{table}");
        let row=client.query_one("SELECT c.relrowsecurity,c.relforcerowsecurity,
            (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')) AS owner_role,
            has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') AS direct,
            (SELECT count(*)=1 AND bool_and(p.policyname='tenant_isolation' AND p.cmd='ALL'
                AND p.permissive='PERMISSIVE' AND p.qual='(tenant_id = hwpx_agent.current_tenant_id())'
                AND p.with_check='(tenant_id = hwpx_agent.current_tenant_id())')
             FROM pg_policies p WHERE p.schemaname='hwpx_agent' AND p.tablename=$1) AS policy,
            EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=c.oid AND t.tgname=$3
                AND t.tgenabled='O' AND NOT t.tgisinternal) AS immutable
            FROM pg_class c WHERE c.oid=$2::text::regclass",&[&table,&q,&format!("{table}_immutable")]).map_err(db_error)?;
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
            "hwpx_agent.read_source_formula_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint)",
            true,
        ),
        (
            "hwpx_agent.register_source_formula_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character)",
            true,
        ),
        (
            "hwpx_agent.revoke_source_formula_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint)",
            true,
        ),
        (
            "hwpx_agent.require_source_formula_policy_role_v1(uuid,uuid,character,boolean)",
            false,
        ),
        (
            "hwpx_agent.require_source_formula_policy_artifacts_v1(uuid,character,uuid,character,uuid,character,boolean)",
            false,
        ),
    ] {
        let r=client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
            p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,
            NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner)))
                WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
            FROM pg_proc p WHERE p.oid=$1::text::regprocedure",&[&signature]).map_err(db_error)?;
        if value::<bool>(&r, "allowed")? != expected
            || !value::<bool>(&r, "prosecdef")?
            || !value::<bool>(&r, "bounded_path")?
            || !value::<bool>(&r, "no_public")?
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    Ok(())
}
fn admit_form_policy_security(client: &mut Client) -> Result<(), RevisionError> {
    for table in READ_TABLES {
        let r = client
            .query_one(
                "SELECT pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')
            OR has_table_privilege(current_user,c.oid,'TRIGGER') AS unsafe_owner
            FROM pg_class c WHERE c.oid=$1::text::regclass",
                &[&format!("hwpx_agent.{table}")],
            )
            .map_err(db_error)?;
        if value::<bool>(&r, "unsafe_owner")? {
            return Err(RevisionError::InvalidRequest);
        }
    }
    let global=client.query_one("SELECT has_schema_privilege(current_user,'hwpx_agent','CREATE')
        OR has_table_privilege(current_user,'hwpx_agent.schema_versions','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') AS excessive",&[]).map_err(db_error)?;
    if value::<bool>(&global, "excessive")? {
        return Err(RevisionError::InvalidRequest);
    }
    for table in [
        "source_form_policy_versions",
        "source_form_policy_revocations",
    ] {
        let q = format!("hwpx_agent.{table}");
        let row=client.query_one("SELECT c.relrowsecurity,c.relforcerowsecurity,
            (pg_has_role(c.relowner,'USAGE') OR pg_has_role(c.relowner,'SET')) AS owner_role,
            has_table_privilege(current_user,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER') AS direct,
            (SELECT count(*)=1 AND bool_and(p.policyname='tenant_isolation' AND p.cmd='ALL'
                AND p.permissive='PERMISSIVE' AND p.qual='(tenant_id = hwpx_agent.current_tenant_id())'
                AND p.with_check='(tenant_id = hwpx_agent.current_tenant_id())')
             FROM pg_policies p WHERE p.schemaname='hwpx_agent' AND p.tablename=$1) AS policy,
            EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=c.oid AND t.tgname=$3
                AND t.tgenabled='O' AND NOT t.tgisinternal) AS immutable
            FROM pg_class c WHERE c.oid=$2::text::regclass",&[&table,&q,&format!("{table}_immutable")]).map_err(db_error)?;
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
            "hwpx_agent.read_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint)",
            true,
        ),
        (
            "hwpx_agent.register_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint,uuid,bigint,character,character,character,uuid,character)",
            true,
        ),
        (
            "hwpx_agent.revoke_source_form_policy_v1(uuid,uuid,uuid,character,text,uuid,bigint)",
            true,
        ),
        (
            "hwpx_agent.require_source_form_policy_role_v1(uuid,uuid,character,boolean)",
            false,
        ),
        (
            "hwpx_agent.require_source_form_policy_artifacts_v1(uuid,character,uuid,character,uuid,character,boolean)",
            false,
        ),
    ] {
        let r=client.query_one("SELECT has_function_privilege(current_user,p.oid,'EXECUTE') AS allowed,p.prosecdef,
            p.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent'] AS bounded_path,
            NOT EXISTS(SELECT 1 FROM aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner)))
                WHERE grantee=0 AND privilege_type='EXECUTE') AS no_public
            FROM pg_proc p WHERE p.oid=$1::text::regprocedure",&[&signature]).map_err(db_error)?;
        if value::<bool>(&r, "allowed")? != expected
            || !value::<bool>(&r, "prosecdef")?
            || !value::<bool>(&r, "bounded_path")?
            || !value::<bool>(&r, "no_public")?
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    Ok(())
}
fn decode_row(
    row: &Row,
    context: &RevisionRequestContext,
    request: &SourceFormulaPolicyReadRequest,
) -> Result<SourceFormulaPolicyRecord, RevisionError> {
    let record = SourceFormulaPolicyRecord {
        tenant: TenantId::new(value(row, "tenant_id")?)
            .map_err(|_| RevisionError::RepositoryFailure)?,
        project: ProjectId::parse(&format!(
            "prj_{}",
            value::<Uuid>(row, "project_id")?.simple()
        ))?,
        branch: BranchId::parse(&format!(
            "brn_{}",
            value::<Uuid>(row, "branch_id")?.simple()
        ))?,
        document: value(row, "document_id")?,
        version: value(row, "policy_version_id")?,
        generation: positive_generation(value(row, "generation")?)?,
        source_head: row_head(row, "source_revision_id", "source_head_generation")?,
        source_result: artifact_id(value(row, "source_result_artifact_id")?)?,
        source_package: row_digest(row, "source_package_sha256")?,
        source_provenance: row_digest(row, "source_provenance_sha256")?,
        observed_graph: row_digest(row, "observed_graph_sha256")?,
        policy_artifact: artifact_id(value(row, "policy_artifact_id")?)?,
        policy_digest: row_digest(row, "policy_artifact_sha256")?,
        creator: SubjectDigest::parse(&value::<String>(row, "created_by_subject_sha256")?)
            .map_err(|_| RevisionError::RepositoryFailure)?,
    };
    if record.tenant != context.tenant_id()
        || record.project != request.project
        || record.branch != request.branch
        || record.document != request.document
        || record.source_head != request.head
        || record.version.is_nil()
        || record.source_result == record.policy_artifact
    {
        return Err(RevisionError::RepositoryFailure);
    }
    Ok(record)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::RevisionId;
    #[test]
    fn bounded_policy_request_rejects_bad_document_and_empty_or_overflow_head()
    -> Result<(), RevisionError> {
        let project = ProjectId::generate();
        let branch = BranchId::generate();
        let head = RevisionHead::new(Some(RevisionId::generate()), 1)?;
        for document in [
            String::new(),
            ".wrong".into(),
            "has space".into(),
            "../path".into(),
            "한글-id".into(),
            "a".repeat(129),
        ] {
            assert!(SourceFormulaPolicyReadRequest::new(project, branch, document, head).is_err());
        }
        assert!(
            SourceFormulaPolicyReadRequest::new(
                project,
                branch,
                "valid-doc".into(),
                RevisionHead::empty()
            )
            .is_err()
        );
        assert!(
            SourceFormulaPolicyReadRequest::new(
                project,
                branch,
                "valid-doc".into(),
                RevisionHead::new(Some(RevisionId::generate()), u64::MAX)?
            )
            .is_err()
        );
        Ok(())
    }
    #[test]
    fn policy_request_debug_never_exposes_document_identifier() -> Result<(), RevisionError> {
        let r = SourceFormulaPolicyReadRequest::new(
            ProjectId::generate(),
            BranchId::generate(),
            "private-doc".into(),
            RevisionHead::new(Some(RevisionId::generate()), 1)?,
        )?;
        assert_eq!(
            format!("{r:?}"),
            "SourceFormulaPolicyReadRequest(<redacted>)"
        );
        Ok(())
    }
}
