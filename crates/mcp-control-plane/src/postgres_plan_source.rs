//! Current-PC `PostgreSQL` adapter for authoritative current revision graph bindings.
//!
//! The adapter is a read-only `PlanSourceRepository`, not a plan store or renderer. It accepts
//! loopback `PostgreSQL` only, fixes one tenant per connection and rechecks project membership,
//! project head, immutable revision/source identity and verified source state in one transaction.

use std::fmt;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use artifact_service::TenantId;
use auth_middleware::AuthContext;
use postgres::types::FromSqlOwned;
use postgres::{Client, Config, IsolationLevel, NoTls, Row, Transaction};
use sha2::{Digest as _, Sha256};
use uuid::Uuid;
use zeroize::Zeroizing;

use crate::{CurrentPlanSource, PlanSourceRepository, StoredPlanError};

macro_rules! migration {
    ($file:literal) => {
        include_bytes!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../migrations/postgres/",
            $file
        ))
        .as_slice()
    };
}

const MIGRATIONS: [&[u8]; 16] = [
    migration!("0001_p14_metadata.up.sql"),
    migration!("0002_p14_artifact_service.up.sql"),
    migration!("0003_p14_revision_cas.up.sql"),
    migration!("0004_p14_history_checkpoints.up.sql"),
    migration!("0005_p14_job_state_machine.up.sql"),
    migration!("0006_p14_worker_lease_fencing.up.sql"),
    migration!("0007_p14_idempotency_reconciliation.up.sql"),
    migration!("0008_p14_cancel_cleanup.up.sql"),
    migration!("0009_p14_retention_local_mirror.up.sql"),
    migration!("0010_p16_artifact_repository.up.sql"),
    migration!("0011_p16_plan_source.up.sql"),
    migration!("0012_p16_durable_plan_store.up.sql"),
    migration!("0013_p16_plan_review_evidence.up.sql"),
    migration!("0014_p17_history_checkpoint_note.up.sql"),
    migration!("0015_p17_atomic_mirror_checkpoint.up.sql"),
    migration!("0016_p17_durable_git_mirror_push.up.sql"),
];

pub struct LocalPostgresPlanSourceConfig {
    port: u16,
    database: String,
    user: String,
    password: Zeroizing<String>,
}

impl LocalPostgresPlanSourceConfig {
    /// Configures one loopback-only development connection.
    ///
    /// # Errors
    /// Rejects empty credentials, unsafe identifiers and an unassigned port.
    pub fn new(
        port: u16,
        database: String,
        user: String,
        password: String,
    ) -> Result<Self, StoredPlanError> {
        let password = Zeroizing::new(password);
        let valid_name = |value: &str| {
            !value.is_empty()
                && value.len() <= 63
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
        };
        if port == 0
            || !valid_name(&database)
            || !valid_name(&user)
            || password.is_empty()
            || password.len() > 1024
            || password.contains('\0')
        {
            return Err(StoredPlanError::InvalidConfiguration);
        }
        Ok(Self {
            port,
            database,
            user,
            password,
        })
    }
}

impl fmt::Debug for LocalPostgresPlanSourceConfig {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresPlanSourceConfig")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PlanSourceConnectStage {
    Transport,
    Role,
    Migrations,
    Policies,
    Privileges,
}

impl PlanSourceConnectStage {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::Transport => "TRANSPORT",
            Self::Role => "ROLE",
            Self::Migrations => "MIGRATIONS",
            Self::Policies => "POLICIES",
            Self::Privileges => "PRIVILEGES",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PlanSourceConnectFailure {
    stage: PlanSourceConnectStage,
    error: StoredPlanError,
}

impl PlanSourceConnectFailure {
    #[must_use]
    pub const fn stage(&self) -> PlanSourceConnectStage {
        self.stage
    }

    #[must_use]
    pub const fn error(&self) -> StoredPlanError {
        self.error
    }

    #[must_use]
    pub const fn into_error(self) -> StoredPlanError {
        self.error
    }
}

impl fmt::Display for PlanSourceConnectFailure {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{}:{}",
            self.stage.code(),
            error_code(self.error)
        )
    }
}

impl std::error::Error for PlanSourceConnectFailure {}

#[derive(Clone)]
pub struct LocalPostgresPlanSourceRepository {
    tenant: TenantId,
    client: Arc<Mutex<Client>>,
}

impl fmt::Debug for LocalPostgresPlanSourceRepository {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresPlanSourceRepository")
            .finish_non_exhaustive()
    }
}

impl LocalPostgresPlanSourceRepository {
    /// Connects a least-privilege reader to the exact v12 schema.
    ///
    /// # Errors
    /// Fails closed for an unsafe role, schema drift, RLS drift, excessive privileges or transport
    /// failure. It does not retry an ambiguous database operation.
    pub fn connect(
        config: &LocalPostgresPlanSourceConfig,
        tenant: TenantId,
    ) -> Result<Self, StoredPlanError> {
        Self::connect_diagnosed(config, tenant).map_err(PlanSourceConnectFailure::into_error)
    }

    /// Performs the same admission while exposing only a closed stage and stable category.
    ///
    /// # Errors
    /// Returns the closed connection stage and stable stored-plan category on any rejection.
    pub fn connect_diagnosed(
        config: &LocalPostgresPlanSourceConfig,
        tenant: TenantId,
    ) -> Result<Self, PlanSourceConnectFailure> {
        let mut settings = Config::new();
        settings
            .host("127.0.0.1")
            .port(config.port)
            .dbname(&config.database)
            .user(&config.user)
            .password(config.password.as_bytes())
            .connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-plan-source-repository")
            .options("-c statement_timeout=5000 -c lock_timeout=1000 -c idle_in_transaction_session_timeout=5000 -c transaction_timeout=10000 -c search_path=pg_catalog");
        let mut client = settings
            .connect(NoTls)
            .map_err(|error| PlanSourceConnectFailure {
                stage: PlanSourceConnectStage::Transport,
                error: db_error(error),
            })?;
        verify_database(&mut client)?;
        Ok(Self {
            tenant,
            client: Arc::new(Mutex::new(client)),
        })
    }

    fn scoped<T>(
        &self,
        tenant: TenantId,
        action: impl FnOnce(&mut Transaction<'_>) -> Result<T, StoredPlanError>,
    ) -> Result<T, StoredPlanError> {
        if tenant != self.tenant {
            return Err(StoredPlanError::NotFound);
        }
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| StoredPlanError::SourceUnavailable)?;
        let mut transaction = client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .map_err(db_error)?;
        transaction
            .query_one(
                "SELECT set_config('hwpx_agent.tenant_id', $1, true)",
                &[&tenant.as_uuid().hyphenated().to_string()],
            )
            .map_err(db_error)?;
        let result = action(&mut transaction)?;
        transaction.commit().map_err(db_error)?;
        Ok(result)
    }
}

impl PlanSourceRepository for LocalPostgresPlanSourceRepository {
    fn current_source(
        &self,
        context: &AuthContext,
        project_id: &str,
    ) -> Result<CurrentPlanSource, StoredPlanError> {
        let project_uuid = database_id(project_id, "prj_")?;
        self.scoped(context.tenant_id(), |transaction| {
            let row = transaction
                .query_opt(
                    "SELECT project.head_revision_id, binding.graph_sha256::text,
                            artifact.artifact_kind, artifact.storage_state,
                            artifact.validation_state, access.role
                     FROM hwpx_agent.projects AS project
                     JOIN hwpx_agent.tenants AS tenant
                       ON tenant.tenant_id=project.tenant_id
                      AND tenant.state='active'
                     JOIN hwpx_agent.branches AS branch
                       ON branch.tenant_id=project.tenant_id
                      AND branch.project_id=project.project_id
                      AND branch.is_default
                      AND branch.head_revision_id=project.head_revision_id
                      AND branch.head_generation=project.head_generation
                     JOIN hwpx_agent.project_acl AS access
                       ON access.tenant_id=project.tenant_id
                      AND access.project_id=project.project_id
                     JOIN hwpx_agent.revisions AS revision
                       ON revision.tenant_id=project.tenant_id
                      AND revision.project_id=project.project_id
                      AND revision.revision_id=project.head_revision_id
                     JOIN hwpx_agent.revision_graph_seals AS seal
                       ON seal.tenant_id=revision.tenant_id
                      AND seal.project_id=revision.project_id
                      AND seal.revision_id=revision.revision_id
                      AND seal.seal_kind='service_v1'
                      AND seal.committed_generation=project.head_generation
                     JOIN hwpx_agent.revision_commit_receipts AS receipt
                       ON receipt.tenant_id=revision.tenant_id
                      AND receipt.project_id=revision.project_id
                      AND receipt.committed_revision_id=revision.revision_id
                      AND receipt.branch_id=branch.branch_id
                      AND receipt.commit_id=seal.commit_id
                      AND receipt.committed_generation=seal.committed_generation
                      AND receipt.commit_request_sha256=seal.commit_request_sha256
                      AND receipt.transaction_receipt_sha256=seal.transaction_receipt_sha256
                     JOIN hwpx_agent.revision_graph_bindings AS binding
                       ON binding.tenant_id=revision.tenant_id
                      AND binding.project_id=revision.project_id
                      AND binding.revision_id=revision.revision_id
                      AND binding.source_artifact_id=revision.source_artifact_id
                     JOIN hwpx_agent.artifacts AS artifact
                       ON artifact.tenant_id=revision.tenant_id
                      AND artifact.artifact_id=revision.source_artifact_id
                     WHERE project.tenant_id=$1 AND project.project_id=$2
                       AND access.subject_sha256=$3 AND project.state='active'
                       AND revision.validation_state='verified'",
                    &[
                        &context.tenant_id().as_uuid(),
                        &project_uuid,
                        &context.subject().hex(),
                    ],
                )
                .map_err(db_error)?
                .ok_or(StoredPlanError::NotFound)?;
            let role: String = value(&row, "role")?;
            let artifact_kind: String = value(&row, "artifact_kind")?;
            let storage_state: String = value(&row, "storage_state")?;
            let validation_state: String = value(&row, "validation_state")?;
            if !matches!(role.as_str(), "reader" | "editor" | "owner")
                || artifact_kind != "source"
                || storage_state != "available"
                || validation_state != "verified"
            {
                return Err(StoredPlanError::SourceUnavailable);
            }
            let revision_id: Uuid = value(&row, "head_revision_id")?;
            let graph_sha256 = digest_bytes(&value::<String>(&row, "graph_sha256")?)?;
            CurrentPlanSource::from_repository_digest(
                context.tenant_id(),
                project_id,
                format!("rev_{}", revision_id.simple()),
                graph_sha256,
            )
        })
    }
}

fn verify_database(client: &mut Client) -> Result<(), PlanSourceConnectFailure> {
    verify_role(client).map_err(|error| PlanSourceConnectFailure {
        stage: PlanSourceConnectStage::Role,
        error,
    })?;
    verify_migrations(client).map_err(|error| PlanSourceConnectFailure {
        stage: PlanSourceConnectStage::Migrations,
        error,
    })?;
    verify_policies(client).map_err(|error| PlanSourceConnectFailure {
        stage: PlanSourceConnectStage::Policies,
        error,
    })?;
    verify_privileges(client).map_err(|error| PlanSourceConnectFailure {
        stage: PlanSourceConnectStage::Privileges,
        error,
    })
}

fn verify_role(client: &mut Client) -> Result<(), StoredPlanError> {
    let row = client
        .query_one(
            "SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication FROM pg_roles WHERE rolname=current_user",
            &[],
        )
        .map_err(db_error)?;
    for field in [
        "rolsuper",
        "rolbypassrls",
        "rolcreaterole",
        "rolcreatedb",
        "rolreplication",
    ] {
        if value::<bool>(&row, field)? {
            return Err(StoredPlanError::AccessDenied);
        }
    }
    Ok(())
}

fn verify_migrations(client: &mut Client) -> Result<(), StoredPlanError> {
    let rows = client
        .query(
            "SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 17",
            &[],
        )
        .map_err(db_error)?;
    if rows.len() != MIGRATIONS.len() {
        return Err(StoredPlanError::SourceUnavailable);
    }
    for (index, row) in rows.iter().enumerate() {
        if value::<i64>(row, "version")?
            != i64::try_from(index + 1).map_err(|_| StoredPlanError::SourceUnavailable)?
            || value::<String>(row, "migration_sha256")?
                != hex::encode(Sha256::digest(MIGRATIONS[index]))
        {
            return Err(StoredPlanError::SourceUnavailable);
        }
    }
    Ok(())
}

fn verify_policies(client: &mut Client) -> Result<(), StoredPlanError> {
    let rows = client
        .query(
            "SELECT class.relname,class.relrowsecurity,class.relforcerowsecurity,
                    (pg_has_role(class.relowner,'USAGE') OR pg_has_role(class.relowner,'SET')) AS owner_role,
                    (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid) AS policy_count,
                    (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid
                      AND policy.polname='tenant_isolation' AND policy.polcmd='*'
                      AND policy.polpermissive AND policy.polroles=ARRAY[0::oid]
                      AND pg_get_expr(policy.polqual,policy.polrelid)='(tenant_id = hwpx_agent.current_tenant_id())'
                      AND pg_get_expr(policy.polwithcheck,policy.polrelid)='(tenant_id = hwpx_agent.current_tenant_id())') AS policy_match
             FROM pg_class AS class
             JOIN pg_namespace AS namespace ON namespace.oid=class.relnamespace
             WHERE namespace.nspname='hwpx_agent'
               AND class.relname IN ('tenants','projects','branches','project_acl','artifacts','revisions','revision_graph_seals','revision_commit_receipts','revision_graph_bindings')",
            &[],
        )
        .map_err(db_error)?;
    if rows.len() != 9 {
        return Err(StoredPlanError::SourceUnavailable);
    }
    for row in rows {
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<i64>(&row, "policy_count")? != 1
            || value::<i64>(&row, "policy_match")? != 1
        {
            return Err(StoredPlanError::AccessDenied);
        }
    }
    Ok(())
}

fn verify_privileges(client: &mut Client) -> Result<(), StoredPlanError> {
    let row = client
        .query_one(
            "SELECT has_schema_privilege('hwpx_agent','CREATE')
                 OR has_table_privilege('hwpx_agent.tenants','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.artifacts','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.projects','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.branches','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.project_acl','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.revisions','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.revision_graph_seals','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.revision_commit_receipts','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR has_table_privilege('hwpx_agent.revision_graph_bindings','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR NOT has_table_privilege('hwpx_agent.schema_versions','SELECT')
                 OR has_table_privilege('hwpx_agent.schema_versions','INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER')
                 OR NOT has_table_privilege('hwpx_agent.tenants','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.projects','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.branches','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.project_acl','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.artifacts','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.revisions','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.revision_graph_seals','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.revision_commit_receipts','SELECT')
                 OR NOT has_table_privilege('hwpx_agent.revision_graph_bindings','SELECT')
                 OR NOT has_function_privilege('hwpx_agent.current_tenant_id()','EXECUTE') AS unsafe",
            &[],
        )
        .map_err(db_error)?;
    if value::<bool>(&row, "unsafe")? {
        return Err(StoredPlanError::AccessDenied);
    }
    Ok(())
}

fn database_id(value: &str, prefix: &str) -> Result<Uuid, StoredPlanError> {
    let tail = value
        .strip_prefix(prefix)
        .filter(|tail| tail.len() == 32)
        .filter(|tail| {
            tail.bytes()
                .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
        })
        .ok_or(StoredPlanError::InvalidRequest)?;
    Uuid::parse_str(tail).map_err(|_| StoredPlanError::InvalidRequest)
}

fn digest_bytes(value: &str) -> Result<[u8; 32], StoredPlanError> {
    let mut bytes = [0_u8; 32];
    hex::decode_to_slice(value, &mut bytes).map_err(|_| StoredPlanError::SourceUnavailable)?;
    Ok(bytes)
}

fn db_error(error: postgres::Error) -> StoredPlanError {
    let mapped = match error.code().map(postgres::error::SqlState::code) {
        Some("42501") => StoredPlanError::AccessDenied,
        _ => StoredPlanError::SourceUnavailable,
    };
    drop(error);
    mapped
}

fn value<T: FromSqlOwned>(row: &Row, name: &str) -> Result<T, StoredPlanError> {
    row.try_get(name).map_err(db_error)
}

const fn error_code(error: StoredPlanError) -> &'static str {
    match error {
        StoredPlanError::Unauthenticated => "UNAUTHENTICATED",
        StoredPlanError::InvalidRequest => "INVALID_REQUEST",
        StoredPlanError::InvalidConfiguration => "INVALID_CONFIGURATION",
        StoredPlanError::NotFound => "NOT_FOUND",
        StoredPlanError::AccessDenied => "ACCESS_DENIED",
        StoredPlanError::StaleSource => "STALE_SOURCE",
        StoredPlanError::Conflict => "CONFLICT",
        StoredPlanError::CapacityExceeded => "CAPACITY_EXCEEDED",
        StoredPlanError::SourceUnavailable => "SOURCE_UNAVAILABLE",
        StoredPlanError::ClockRegression => "CLOCK_REGRESSION",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn local_config_rejects_unsafe_values_and_redacts_debug() {
        for (port, database, user, password) in [
            (
                0,
                "postgres".to_owned(),
                "reader".to_owned(),
                "secret".to_owned(),
            ),
            (1, String::new(), "reader".to_owned(), "secret".to_owned()),
            (
                1,
                "postgres;drop".to_owned(),
                "reader".to_owned(),
                "secret".to_owned(),
            ),
            (
                1,
                "postgres".to_owned(),
                "x".repeat(64),
                "secret".to_owned(),
            ),
            (1, "postgres".to_owned(), "reader".to_owned(), String::new()),
            (
                1,
                "postgres".to_owned(),
                "reader".to_owned(),
                "x".repeat(1025),
            ),
            (
                1,
                "postgres".to_owned(),
                "reader".to_owned(),
                "bad\0secret".to_owned(),
            ),
        ] {
            assert_eq!(
                LocalPostgresPlanSourceConfig::new(port, database, user, password).err(),
                Some(StoredPlanError::InvalidConfiguration)
            );
        }
        let config = LocalPostgresPlanSourceConfig::new(
            5432,
            "postgres".to_owned(),
            "reader".to_owned(),
            "private-secret".to_owned(),
        )
        .unwrap_or_else(|error| panic!("config: {error}"));
        assert_eq!(
            format!("{config:?}"),
            "LocalPostgresPlanSourceConfig { .. }"
        );
    }

    #[test]
    fn database_identifiers_and_digests_are_canonical() {
        let id = "prj_00000000000000000000000000000001";
        assert_eq!(database_id(id, "prj_").map(|value| value.as_u128()), Ok(1));
        for invalid in [
            "prj_example01",
            "prj_0000000000000000000000000000000A",
            "rev_00000000000000000000000000000001",
            "prj_000000000000000000000000000000011",
        ] {
            assert_eq!(
                database_id(invalid, "prj_").err(),
                Some(StoredPlanError::InvalidRequest)
            );
        }
        assert_eq!(digest_bytes(&"a".repeat(64)), Ok([0xaa; 32]));
        assert_eq!(
            digest_bytes("not-a-digest").err(),
            Some(StoredPlanError::SourceUnavailable)
        );
    }

    #[test]
    fn connection_failure_debug_and_display_are_closed() {
        let failure = PlanSourceConnectFailure {
            stage: PlanSourceConnectStage::Policies,
            error: StoredPlanError::AccessDenied,
        };
        assert_eq!(failure.to_string(), "POLICIES:ACCESS_DENIED");
        assert_eq!(failure.stage(), PlanSourceConnectStage::Policies);
        assert_eq!(failure.error(), StoredPlanError::AccessDenied);
        assert_eq!(failure.into_error(), StoredPlanError::AccessDenied);
    }
}
