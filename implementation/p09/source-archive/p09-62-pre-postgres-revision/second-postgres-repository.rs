//! Subject-fixed loopback `PostgreSQL` revision repository with genuine v2 lease authority.
//! SQL metadata/seals are not full importer/native/issuer or product-route evidence.
use crate::{
    BranchId, CommitId, CommitOutcome, FullDocumentIrBinding, ProjectId, RevisionCommitRequest,
    RevisionConflict, RevisionError, RevisionHead, RevisionId, RevisionNode, RevisionReceipt,
    RevisionRepository, RevisionRequestContext, RevisionValidationState,
};
use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use postgres::types::{FromSqlOwned, ToSql};
use postgres::{Client, Config, IsolationLevel, NoTls, Row, Transaction};
use std::{
    fmt,
    sync::{Arc, Mutex},
    time::Duration,
};
use uuid::Uuid;
use zeroize::Zeroizing;

const MIGRATIONS: [&[u8]; 19] = [
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0001_p14_metadata.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0002_p14_artifact_service.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0003_p14_revision_cas.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0004_p14_history_checkpoints.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0005_p14_job_state_machine.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0006_p14_worker_lease_fencing.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0007_p14_idempotency_reconciliation.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0008_p14_cancel_cleanup.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0009_p14_retention_local_mirror.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0010_p16_artifact_repository.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0011_p16_plan_source.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0012_p16_durable_plan_store.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0013_p16_plan_review_evidence.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0014_p17_history_checkpoint_note.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0015_p17_atomic_mirror_checkpoint.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0016_p17_durable_git_mirror_push.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0017_p17_durable_git_mirror_pull.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0018_p09_full_document_ir.up.sql"
    )),
    include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../migrations/postgres/0019_p09_authorized_full_ir_intent.up.sql"
    )),
];
const COMMIT: &str = "SELECT * FROM hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(
    $1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,
    $17,$18,$19,$20::character(64),$21,$22::character(64),$23::character(64),
    $24::character(64),$25::character(64),$26,$27::character(64),
    $28::character(64),$29::character(64))";
const LEGACY_COMMIT: &str = "SELECT * FROM hwpx_agent.commit_idempotent_revision_cas_v2(
    $1,$2,$3,$4::character(64),$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,
    $17,$18,$19,$20::character(64),$21,$22::character(64),$23::character(64),
    $24::character(64),$25::character(64))";
const READ_TABLES: [&str; 7] = [
    "branches",
    "project_acl",
    "revisions",
    "revision_parents",
    "revision_graph_seals",
    "revision_commit_receipts",
    "full_document_ir_intents",
];

pub struct LocalPostgresRevisionConfig {
    port: u16,
    database: String,
    user: String,
    password: Zeroizing<String>,
}
impl fmt::Debug for LocalPostgresRevisionConfig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("LocalPostgresRevisionConfig(<redacted>)")
    }
}
impl LocalPostgresRevisionConfig {
    /// Loopback-only credentials, with no arbitrary DSN/host/options or retained retry secret.
    /// # Errors
    /// Rejects unsafe DB/user names, empty credentials and port0.
    pub fn new(
        port: u16,
        database: String,
        user: String,
        password: String,
    ) -> Result<Self, RevisionError> {
        let password = Zeroizing::new(password);
        let name = |s: &str| {
            !s.is_empty()
                && s.len() <= 63
                && s.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_')
        };
        if port == 0
            || !name(&database)
            || !name(&user)
            || password.is_empty()
            || password.len() > 1024
            || password.contains('\0')
        {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self {
            port,
            database,
            user,
            password,
        })
    }
}

/// Internal service lease inputs; these are not a public product envelope or approval.
#[derive(Clone, Copy)]
pub struct RevisionLeaseIdentity {
    pub idempotency_key: Uuid,
    pub job_id: Uuid,
    pub agent_instance_id: Uuid,
    pub execution_id: Uuid,
    pub attempt_no: i32,
    pub fencing_token: i64,
    pub authorization_id: Uuid,
}
impl fmt::Debug for RevisionLeaseIdentity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("RevisionLeaseIdentity(<redacted>)")
    }
}
#[derive(Clone)]
pub struct RevisionCommitLease {
    identity: RevisionLeaseIdentity,
    request_sha256: ContentDigest,
}
impl fmt::Debug for RevisionCommitLease {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("RevisionCommitLease(<redacted>)")
    }
}
impl RevisionCommitLease {
    /// Binds an exact immutable request to a received lease; SQL still checks real authority.
    /// # Errors
    /// Rejects malformed/nil lease IDs or a mismatched attempt/fence. Does not mint authorization.
    pub fn bind(
        identity: RevisionLeaseIdentity,
        request: &RevisionCommitRequest,
    ) -> Result<Self, RevisionError> {
        if [
            identity.idempotency_key,
            identity.job_id,
            identity.agent_instance_id,
            identity.execution_id,
            identity.authorization_id,
        ]
        .iter()
        .any(Uuid::is_nil)
            || !(1..=10).contains(&identity.attempt_no)
            || identity.fencing_token != i64::from(identity.attempt_no)
        {
            return Err(RevisionError::InvalidRequest);
        }
        Ok(Self {
            identity,
            request_sha256: request.canonical_sha256()?,
        })
    }
}

#[derive(Clone)]
pub struct LocalPostgresRevisionRepository {
    context: RevisionRequestContext,
    lease: Option<RevisionCommitLease>,
    client: Arc<Mutex<Client>>,
}
impl fmt::Debug for LocalPostgresRevisionRepository {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("LocalPostgresRevisionRepository(<redacted>)")
    }
}
impl LocalPostgresRevisionRepository {
    /// Admits exact schema1~19, forced tenant RLS and least-privilege read/function rights.
    /// # Errors
    /// Discards raw DB diagnostics; unsupported role/schema/privileges/transport reject.
    pub fn connect(
        config: &LocalPostgresRevisionConfig,
        context: RevisionRequestContext,
        lease: Option<RevisionCommitLease>,
    ) -> Result<Self, RevisionError> {
        let mut client = Config::new().host("127.0.0.1").port(config.port)
            .dbname(&config.database).user(&config.user).password(config.password.as_bytes())
            .connect_timeout(Duration::from_secs(3)).application_name("hwpx-agent-local-revision")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog")
            .connect(NoTls).map_err(db_error)?;
        admit(&mut client)?;
        Ok(Self {
            context,
            lease,
            client: Arc::new(Mutex::new(client)),
        })
    }
    fn scoped<T>(
        &self,
        tenant: TenantId,
        action: impl FnOnce(&mut Transaction<'_>) -> Result<T, RevisionError>,
    ) -> Result<T, RevisionError> {
        if tenant != self.context.tenant_id() {
            return Err(RevisionError::NotFound);
        }
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| RevisionError::RepositoryFailure)?;
        let mut tx = client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .start()
            .map_err(db_error)?;
        tx.query_one("SELECT set_config('hwpx_agent.tenant_id',$1,true),set_config('hwpx_agent.subject_sha256',$2,true)",
            &[&tenant.as_uuid().hyphenated().to_string(), &self.context.subject().hex()]).map_err(db_error)?;
        let result = action(&mut tx)?;
        // No automatic retry/reconnect; commit acknowledgement loss is explicitly ambiguous.
        tx.commit()
            .map_err(|_| RevisionError::CommitOutcomeUnknown)?;
        Ok(result)
    }
}

impl RevisionRepository for LocalPostgresRevisionRepository {
    fn authorize_context(&self, context: &RevisionRequestContext) -> Result<(), RevisionError> {
        if context.tenant_id() != self.context.tenant_id()
            || context.subject() != self.context.subject()
        {
            Err(RevisionError::NotFound)
        } else {
            Ok(())
        }
    }
    fn compare_and_swap(
        &self,
        context: &RevisionRequestContext,
        request: &RevisionCommitRequest,
    ) -> Result<CommitOutcome, RevisionError> {
        self.authorize_context(context)?;
        let lease = self.lease.as_ref().ok_or(RevisionError::InvalidRequest)?;
        if lease.request_sha256 != request.canonical_sha256()? {
            return Err(RevisionError::InvalidRequest);
        }
        let parameters = SqlCommit::new(context, request)?;
        self.scoped(context.tenant_id(), |tx| {
            let args = parameters.arguments(&lease.identity);
            let row = if request.full_document_ir().is_some() {
                tx.query_one(COMMIT, &args).map_err(db_error)?
            } else {
                tx.query_one(LEGACY_COMMIT, &args[..25]).map_err(db_error)?
            };
            commit_outcome(&row, context, request)
        })
    }
    fn head(
        &self,
        tenant: TenantId,
        project: ProjectId,
        branch: BranchId,
    ) -> Result<RevisionHead, RevisionError> {
        self.scoped(tenant, |tx| {
            let row = tx.query_opt("SELECT branch.head_revision_id,branch.head_generation
                FROM hwpx_agent.branches AS branch JOIN hwpx_agent.project_acl AS acl USING(tenant_id,project_id)
                WHERE branch.tenant_id=$1 AND branch.project_id=$2 AND branch.branch_id=$3
                    AND acl.subject_sha256=$4::character(64)", &[&tenant.as_uuid(), &project.as_uuid(),
                        &branch.as_uuid(), &self.context.subject().hex()]).map_err(db_error)?
                .ok_or(RevisionError::NotFound)?;
            row_head(&row, "head_revision_id", "head_generation")
        })
    }
    fn node(
        &self,
        tenant: TenantId,
        project: ProjectId,
        revision: RevisionId,
    ) -> Result<RevisionNode, RevisionError> {
        self.scoped(tenant, |tx| {
            read_node(tx, tenant, project, revision, self.context.subject())
        })
    }
}

struct SqlCommit {
    tenant: Uuid,
    project: Uuid,
    branch: Uuid,
    subject: String,
    commit: Uuid,
    previous: Option<Uuid>,
    generation: i64,
    revision: Uuid,
    parents: Vec<Uuid>,
    source: Uuid,
    result: Uuid,
    diff: Option<Uuid>,
    plan: String,
    validation: &'static str,
    summary: String,
    transaction: String,
    request: String,
    receipt: String,
    ir: Option<Uuid>,
    ir_sha: Option<String>,
    package_sha: Option<String>,
    graph_sha: Option<String>,
}
impl SqlCommit {
    fn new(
        context: &RevisionRequestContext,
        request: &RevisionCommitRequest,
    ) -> Result<Self, RevisionError> {
        let expected = request.expected_head();
        let committed = RevisionHead::new(
            Some(request.new_revision_id()),
            expected
                .generation()
                .checked_add(1)
                .ok_or(RevisionError::InvalidHead)?,
        )?;
        let digest = request.canonical_sha256()?;
        let receipt =
            RevisionReceipt::from_commit(request, expected, committed, digest, context.subject())?;
        let ir = request.full_document_ir();
        Ok(Self {
            tenant: context.tenant_id().as_uuid(),
            project: request.project_id().as_uuid(),
            branch: request.branch_id().as_uuid(),
            subject: context.subject().hex(),
            commit: request.commit_id().as_uuid(),
            previous: expected.revision_id().map(RevisionId::as_uuid),
            generation: i64::try_from(expected.generation())
                .map_err(|_| RevisionError::InvalidHead)?,
            revision: request.new_revision_id().as_uuid(),
            parents: request.parents().iter().map(|p| p.as_uuid()).collect(),
            source: request.source_artifact_id().as_uuid(),
            result: request.result_artifact_id().as_uuid(),
            diff: request.semantic_diff_artifact_id().map(ArtifactId::as_uuid),
            plan: request.operation_plan_sha256().hex(),
            validation: "verified",
            summary: request.validation_summary_sha256().hex(),
            transaction: request.transaction_receipt_sha256().hex(),
            request: digest.hex(),
            receipt: receipt.receipt_sha256().hex(),
            ir: ir.map(|b| b.artifact_id.as_uuid()),
            ir_sha: ir.map(|b| b.artifact_sha256.hex()),
            package_sha: ir.map(|b| b.result_package_sha256.hex()),
            graph_sha: ir.map(|b| b.canonical_graph_sha256.hex()),
        })
    }
    fn arguments<'a>(&'a self, lease: &'a RevisionLeaseIdentity) -> [&'a (dyn ToSql + Sync); 29] {
        [
            &self.tenant,
            &self.project,
            &self.branch,
            &self.subject,
            &lease.idempotency_key,
            &lease.job_id,
            &lease.agent_instance_id,
            &lease.execution_id,
            &lease.attempt_no,
            &lease.fencing_token,
            &lease.authorization_id,
            &self.commit,
            &self.previous,
            &self.generation,
            &self.revision,
            &self.parents,
            &self.source,
            &self.result,
            &self.diff,
            &self.plan,
            &self.validation,
            &self.summary,
            &self.transaction,
            &self.request,
            &self.receipt,
            &self.ir,
            &self.ir_sha,
            &self.package_sha,
            &self.graph_sha,
        ]
    }
}

fn commit_outcome(
    row: &Row,
    context: &RevisionRequestContext,
    request: &RevisionCommitRequest,
) -> Result<CommitOutcome, RevisionError> {
    let observed = row_head(row, "observed_revision_id", "observed_generation")?;
    let digest = request.canonical_sha256()?;
    match value::<String>(row, "outcome")?.as_str() {
        "conflict"
            if observed != request.expected_head()
                && value::<Option<Uuid>>(row, "committed_revision_id")?.is_none()
                && value::<Option<i64>>(row, "committed_generation")?.is_none()
                && value::<Option<String>>(row, "receipt_sha256")?.is_none() =>
        {
            Ok(CommitOutcome::Conflict(RevisionConflict::new(
                request, observed, digest,
            )))
        }
        "committed" => {
            let committed = row_head(row, "committed_revision_id", "committed_generation")?;
            if observed != committed
                || committed.revision_id() != Some(request.new_revision_id())
                || Some(committed.generation())
                    != request.expected_head().generation().checked_add(1)
            {
                return Err(RevisionError::InvalidHead);
            }
            let receipt = RevisionReceipt::from_commit(
                request,
                request.expected_head(),
                committed,
                digest,
                context.subject(),
            )?;
            if value::<String>(row, "receipt_sha256")? != receipt.receipt_sha256().hex() {
                return Err(RevisionError::RepositoryFailure);
            }
            Ok(CommitOutcome::Committed(receipt))
        }
        _ => Err(RevisionError::RepositoryFailure),
    }
}

fn read_node(
    tx: &mut Transaction<'_>,
    tenant: TenantId,
    project: ProjectId,
    revision: RevisionId,
    subject: SubjectDigest,
) -> Result<RevisionNode, RevisionError> {
    let row = tx.query_opt("SELECT r.source_artifact_id,r.result_artifact_id,r.semantic_diff_artifact_id,
        r.operation_plan_sha256::text,r.validation_state,r.validation_summary_sha256::text,
        r.created_by_subject_sha256::text,r.full_document_ir_artifact_id,
        r.full_document_ir_artifact_sha256::text,r.full_document_ir_result_package_sha256::text,
        r.full_document_ir_graph_sha256::text,s.seal_kind,s.parent_count,s.committed_generation,
        s.commit_id,s.commit_request_sha256::text,s.transaction_receipt_sha256::text,
        c.branch_id,c.previous_revision_id,c.expected_generation,c.commit_receipt_sha256::text,
        c.subject_sha256::text,
        (s.commit_id=c.commit_id AND s.commit_request_sha256=c.commit_request_sha256
        AND s.transaction_receipt_sha256=c.transaction_receipt_sha256
        AND s.committed_generation=c.committed_generation) AS seal_matches
        FROM hwpx_agent.revisions r JOIN hwpx_agent.revision_graph_seals s USING(tenant_id,project_id,revision_id)
        JOIN hwpx_agent.revision_commit_receipts c ON c.tenant_id=r.tenant_id
            AND c.project_id=r.project_id AND c.committed_revision_id=r.revision_id
        JOIN hwpx_agent.project_acl acl ON acl.tenant_id=r.tenant_id AND acl.project_id=r.project_id
        WHERE r.tenant_id=$1 AND r.project_id=$2 AND r.revision_id=$3 AND acl.subject_sha256=$4::character(64)",
        &[&tenant.as_uuid(),&project.as_uuid(),&revision.as_uuid(),&subject.hex()]).map_err(db_error)?
        .ok_or(RevisionError::NotFound)?;
    if value::<String>(&row, "seal_kind")? != "service_v1"
        || !value::<bool>(&row, "seal_matches")?
        || value::<String>(&row, "validation_state")? != "verified"
        || value::<String>(&row, "created_by_subject_sha256")?
            != value::<String>(&row, "subject_sha256")?
    {
        return Err(RevisionError::RepositoryFailure);
    }
    let parents = read_parents(tx, tenant, project, revision)?;
    if usize::try_from(value::<i16>(&row, "parent_count")?).ok() != Some(parents.len()) {
        return Err(RevisionError::RepositoryFailure);
    }
    let request = decoded_request(&row, project, revision, parents)?;
    let digest = request.canonical_sha256()?;
    if digest != row_digest(&row, "commit_request_sha256")? {
        return Err(RevisionError::RepositoryFailure);
    }
    let generation = positive_generation(value(&row, "committed_generation")?)?;
    let creator = SubjectDigest::parse(&value::<String>(&row, "created_by_subject_sha256")?)
        .map_err(|_| RevisionError::RepositoryFailure)?;
    let committed = RevisionHead::new(Some(revision), generation)?;
    if Some(generation) != request.expected_head().generation().checked_add(1)
        || RevisionReceipt::from_commit(
            &request,
            request.expected_head(),
            committed,
            digest,
            creator,
        )?
        .receipt_sha256()
            != row_digest(&row, "commit_receipt_sha256")?
    {
        return Err(RevisionError::RepositoryFailure);
    }
    Ok(RevisionNode::sealed_from(
        &request, generation, digest, creator,
    ))
}
fn read_parents(
    tx: &mut Transaction<'_>,
    tenant: TenantId,
    project: ProjectId,
    revision: RevisionId,
) -> Result<Vec<RevisionId>, RevisionError> {
    let rows = tx
        .query(
            "SELECT parent_revision_id,parent_ordinal FROM hwpx_agent.revision_parents
        WHERE tenant_id=$1 AND project_id=$2 AND revision_id=$3 ORDER BY parent_ordinal LIMIT 33",
            &[&tenant.as_uuid(), &project.as_uuid(), &revision.as_uuid()],
        )
        .map_err(db_error)?;
    if rows.len() > 32 {
        return Err(RevisionError::ParentUnavailable);
    }
    rows.iter()
        .enumerate()
        .map(|(ordinal, row)| {
            if usize::try_from(value::<i16>(row, "parent_ordinal")?).ok() != Some(ordinal) {
                return Err(RevisionError::ParentUnavailable);
            }
            revision_id(value(row, "parent_revision_id")?)
        })
        .collect()
}
fn decoded_request(
    row: &Row,
    project: ProjectId,
    revision: RevisionId,
    parents: Vec<RevisionId>,
) -> Result<RevisionCommitRequest, RevisionError> {
    let request = RevisionCommitRequest::new(
        CommitId::parse(&format!(
            "cmt_{}",
            value::<Uuid>(row, "commit_id")?.simple()
        ))?,
        project,
        BranchId::parse(&format!(
            "brn_{}",
            value::<Uuid>(row, "branch_id")?.simple()
        ))?,
        row_head(row, "previous_revision_id", "expected_generation")?,
        revision,
        parents,
        artifact_id(value(row, "source_artifact_id")?)?,
        artifact_id(value(row, "result_artifact_id")?)?,
        value::<Option<Uuid>>(row, "semantic_diff_artifact_id")?
            .map(artifact_id)
            .transpose()?,
        row_digest(row, "operation_plan_sha256")?,
        RevisionValidationState::Verified,
        row_digest(row, "validation_summary_sha256")?,
        row_digest(row, "transaction_receipt_sha256")?,
    )?;
    let id: Option<Uuid> = value(row, "full_document_ir_artifact_id")?;
    let digests: [Option<String>; 3] = [
        value(row, "full_document_ir_artifact_sha256")?,
        value(row, "full_document_ir_result_package_sha256")?,
        value(row, "full_document_ir_graph_sha256")?,
    ];
    match (id, digests) {
        (None, [None, None, None]) => Ok(request),
        (Some(id), [Some(raw), Some(package), Some(graph)]) if raw == graph => request
            .with_full_document_ir(FullDocumentIrBinding {
                artifact_id: artifact_id(id)?,
                artifact_sha256: parse_digest(&raw)?,
                result_package_sha256: parse_digest(&package)?,
                canonical_graph_sha256: parse_digest(&graph)?,
            }),
        _ => Err(RevisionError::RepositoryFailure),
    }
}

fn admit(client: &mut Client) -> Result<(), RevisionError> {
    let row = client
        .query_one(
            "SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication
        FROM pg_roles WHERE rolname=current_user",
            &[],
        )
        .map_err(db_error)?;
    for name in [
        "rolsuper",
        "rolbypassrls",
        "rolcreaterole",
        "rolcreatedb",
        "rolreplication",
    ] {
        if value::<bool>(&row, name)? {
            return Err(RevisionError::InvalidRequest);
        }
    }
    let rows = client
        .query(
            "SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions
        ORDER BY version LIMIT 20",
            &[],
        )
        .map_err(db_error)?;
    if rows.len() != 19 {
        return Err(RevisionError::InvalidRequest);
    }
    for (i, row) in rows.iter().enumerate() {
        if value::<i64>(row, "version")?
            != i64::try_from(i + 1).map_err(|_| RevisionError::InvalidRequest)?
            || value::<String>(row, "migration_sha256")? != ContentDigest::of(MIGRATIONS[i]).hex()
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    for table in READ_TABLES {
        let qualified = format!("hwpx_agent.{table}");
        let row = client
            .query_one(
                "SELECT c.relrowsecurity,c.relforcerowsecurity,
            has_table_privilege(current_user,c.oid,'SELECT') AS can_read,
            has_table_privilege(current_user,c.oid,'INSERT,UPDATE,DELETE,TRUNCATE') AS can_write,
            (SELECT count(*)=1 AND bool_and(p.policyname='tenant_isolation'
                AND p.cmd='ALL' AND p.permissive='PERMISSIVE'
                AND p.qual='(tenant_id = hwpx_agent.current_tenant_id())'
                AND p.with_check='(tenant_id = hwpx_agent.current_tenant_id())')
                FROM pg_policies p WHERE p.schemaname='hwpx_agent' AND p.tablename=$1) AS policy
            FROM pg_class c WHERE c.oid=$2::regclass",
                &[&table, &qualified],
            )
            .map_err(db_error)?;
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || !value::<bool>(&row, "can_read")?
            || value::<bool>(&row, "can_write")?
            || !value::<bool>(&row, "policy")?
        {
            return Err(RevisionError::InvalidRequest);
        }
    }
    for table in [
        "jobs",
        "job_attempts",
        "idempotency_records",
        "idempotency_commit_authorizations",
    ] {
        let row=client.query_one("SELECT has_table_privilege(current_user,$1,'INSERT,UPDATE,DELETE,TRUNCATE') AS writable",
            &[&format!("hwpx_agent.{table}")]).map_err(db_error)?;
        if value::<bool>(&row, "writable")? {
            return Err(RevisionError::InvalidRequest);
        }
    }
    for (table, trigger) in [
        ("revisions", "revisions_immutable"),
        ("revision_parents", "revision_parents_immutable"),
        ("revision_graph_seals", "revision_graph_seals_immutable"),
        (
            "revision_commit_receipts",
            "revision_commit_receipts_immutable",
        ),
        (
            "revision_commit_receipts",
            "revision_commit_receipts_idempotency_v2_guard",
        ),
        (
            "revision_commit_receipts",
            "revision_commit_receipts_full_ir_intent_guard",
        ),
        ("revisions", "revisions_full_document_ir_guard"),
        (
            "full_document_ir_intents",
            "full_document_ir_intents_immutable",
        ),
    ] {
        let row=client.query_one("SELECT EXISTS(SELECT 1 FROM pg_trigger WHERE tgrelid=$1::regclass AND tgname=$2 AND tgenabled='O' AND NOT tgisinternal) AS active",
            &[&format!("hwpx_agent.{table}"),&trigger]).map_err(db_error)?;
        if !value::<bool>(&row, "active")? {
            return Err(RevisionError::InvalidRequest);
        }
    }
    for (signature, expected) in [
        (
            "hwpx_agent.commit_idempotent_revision_cas_with_full_ir_v1(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character,uuid,character,character,character)",
            true,
        ),
        (
            "hwpx_agent.commit_idempotent_revision_cas_v2(uuid,uuid,uuid,character,uuid,uuid,uuid,uuid,integer,bigint,uuid,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character)",
            true,
        ),
        (
            "hwpx_agent.commit_revision_cas_with_full_ir_v1(uuid,uuid,uuid,character,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character,uuid,character,character,character)",
            false,
        ),
        (
            "hwpx_agent.commit_revision_cas(uuid,uuid,uuid,character,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character)",
            false,
        ),
        (
            "hwpx_agent.require_full_ir_intent_artifact_v1(uuid,character,uuid,character,character)",
            false,
        ),
    ] {
        let row = client
            .query_one(
                "SELECT has_function_privilege(current_user,$1,'EXECUTE') AS allowed",
                &[&signature],
            )
            .map_err(db_error)?;
        if value::<bool>(&row, "allowed")? != expected {
            return Err(RevisionError::InvalidRequest);
        }
    }
    Ok(())
}
fn row_head(row: &Row, id: &str, generation: &str) -> Result<RevisionHead, RevisionError> {
    let id = value::<Option<Uuid>>(row, id)?
        .map(revision_id)
        .transpose()?;
    let generation =
        u64::try_from(value::<i64>(row, generation)?).map_err(|_| RevisionError::InvalidHead)?;
    RevisionHead::new(id, generation)
}
fn positive_generation(value: i64) -> Result<u64, RevisionError> {
    u64::try_from(value)
        .ok()
        .filter(|n| *n > 0)
        .ok_or(RevisionError::InvalidHead)
}
fn revision_id(id: Uuid) -> Result<RevisionId, RevisionError> {
    RevisionId::parse(&format!("rev_{}", id.simple()))
}
fn artifact_id(id: Uuid) -> Result<ArtifactId, RevisionError> {
    ArtifactId::parse(&format!("art_{}", id.simple())).map_err(|_| RevisionError::RepositoryFailure)
}
fn parse_digest(value: &str) -> Result<ContentDigest, RevisionError> {
    ContentDigest::parse(value).map_err(|_| RevisionError::RepositoryFailure)
}
fn row_digest(row: &Row, name: &str) -> Result<ContentDigest, RevisionError> {
    parse_digest(&value::<String>(row, name)?)
}
fn value<T: FromSqlOwned>(row: &Row, name: &str) -> Result<T, RevisionError> {
    row.try_get(name)
        .map_err(|_| RevisionError::RepositoryFailure)
}
fn db_error(_error: postgres::Error) -> RevisionError {
    RevisionError::RepositoryFailure
}
