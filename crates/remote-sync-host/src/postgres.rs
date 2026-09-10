//! Current-PC `PostgreSQL` checkpoint dispatcher.
//!
//! The connection is loopback-only, tenant/subject-fixed and admitted only against the exact
//! migration set and least-privilege function surface. No retry is attempted after an uncertain
//! database outcome.

use std::fmt;
use std::sync::Mutex;
use std::time::Duration;

use artifact_service::{SubjectDigest, TenantId};
use postgres::types::FromSqlOwned;
use postgres::{Client, Config, IsolationLevel, NoTls, Row};
use retention_sync_service::MirrorId;
use revision_service::BranchId;
use sha2::{Digest as _, Sha256};
use zeroize::Zeroizing;

use crate::{
    CheckpointDispatchError, CheckpointDispatchOutcome, CheckpointDispatchRequest,
    CheckpointDispatcher, map_history_checkpoint_request,
};

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

const MIGRATIONS: [&[u8]; 14] = [
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
];

const ATOMIC_MIGRATIONS: [&[u8]; 15] = [
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
];

const CURRENT_ATOMIC_MIGRATIONS: [&[u8]; 17] = [
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
    migration!("0017_p17_durable_git_mirror_pull.up.sql"),
];

/// Bounded local connection settings. The password is zeroized and never exposed by `Debug`.
pub struct LocalPostgresHistoryCheckpointConfig {
    pub(crate) port: u16,
    pub(crate) database: String,
    pub(crate) user: String,
    pub(crate) password: Zeroizing<String>,
}

impl LocalPostgresHistoryCheckpointConfig {
    /// Creates one exact loopback database configuration.
    ///
    /// # Errors
    ///
    /// Rejects an unassigned port, unsafe database/user identifiers or an invalid password shape.
    pub fn new(
        port: u16,
        database: String,
        user: String,
        password: String,
    ) -> Result<Self, CheckpointDispatchError> {
        let password = Zeroizing::new(password);
        let valid_identifier = |value: &str| {
            !value.is_empty()
                && value.len() <= 63
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
        };
        if port == 0
            || !valid_identifier(&database)
            || !valid_identifier(&user)
            || password.is_empty()
            || password.len() > 1_024
            || password.contains('\0')
        {
            return Err(CheckpointDispatchError::Rejected);
        }
        Ok(Self {
            port,
            database,
            user,
            password,
        })
    }
}

impl fmt::Debug for LocalPostgresHistoryCheckpointConfig {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresHistoryCheckpointConfig")
            .finish_non_exhaustive()
    }
}

/// Closed admission stage suitable for support evidence without database or credential content.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PostgresCheckpointConnectStage {
    Transport,
    Role,
    Migrations,
    Policies,
    Privileges,
}

impl PostgresCheckpointConnectStage {
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

/// Stable diagnosed connection failure. `PostgreSQL` diagnostics are discarded before construction.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PostgresCheckpointConnectFailure {
    stage: PostgresCheckpointConnectStage,
    error: CheckpointDispatchError,
}

impl PostgresCheckpointConnectFailure {
    #[must_use]
    pub const fn stage(self) -> PostgresCheckpointConnectStage {
        self.stage
    }

    #[must_use]
    pub const fn error(self) -> CheckpointDispatchError {
        self.error
    }

    #[must_use]
    pub const fn into_error(self) -> CheckpointDispatchError {
        self.error
    }
}

impl fmt::Display for PostgresCheckpointConnectFailure {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}:{}", self.stage.code(), self.error.code())
    }
}

impl std::error::Error for PostgresCheckpointConnectFailure {}

/// One live `PostgreSQL` connection fixed to an authenticated tenant and subject.
pub struct LocalPostgresHistoryCheckpointDispatcher {
    tenant_id: TenantId,
    subject: SubjectDigest,
    client: Mutex<Client>,
}

impl fmt::Debug for LocalPostgresHistoryCheckpointDispatcher {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresHistoryCheckpointDispatcher")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("client", &"<redacted>")
            .finish()
    }
}

impl LocalPostgresHistoryCheckpointDispatcher {
    /// Connects to the exact local schema with a non-owner, non-privileged execution role.
    ///
    /// # Errors
    ///
    /// Fails closed for transport, role, migration, RLS or privilege drift.
    pub fn connect(
        config: &LocalPostgresHistoryCheckpointConfig,
        tenant_id: TenantId,
        subject: SubjectDigest,
    ) -> Result<Self, CheckpointDispatchError> {
        Self::connect_diagnosed(config, tenant_id, subject)
            .map_err(PostgresCheckpointConnectFailure::into_error)
    }

    /// Performs the same admission while retaining only a closed stage and public error category.
    ///
    /// # Errors
    ///
    /// Returns the first failed admission stage without retaining backend diagnostics.
    pub fn connect_diagnosed(
        config: &LocalPostgresHistoryCheckpointConfig,
        tenant_id: TenantId,
        subject: SubjectDigest,
    ) -> Result<Self, PostgresCheckpointConnectFailure> {
        let mut settings = Config::new();
        settings
            .host("127.0.0.1")
            .port(config.port)
            .dbname(&config.database)
            .user(&config.user)
            .password(config.password.as_bytes())
            .connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-history-checkpoint")
            .options(
                "-c statement_timeout=5000 -c lock_timeout=1000 \
                 -c idle_in_transaction_session_timeout=5000 \
                 -c transaction_timeout=10000 -c search_path=pg_catalog",
            );
        let mut client =
            settings
                .connect(NoTls)
                .map_err(|error| PostgresCheckpointConnectFailure {
                    stage: PostgresCheckpointConnectStage::Transport,
                    error: db_dispatch_error(error),
                })?;
        verify_database(&mut client)?;
        Ok(Self {
            tenant_id,
            subject,
            client: Mutex::new(client),
        })
    }
}

/// `PostgreSQL` dispatcher whose role, mirror, branch-head and checkpoint decisions share one
/// serializable database transaction.
pub struct LocalPostgresAtomicMirrorCheckpointDispatcher {
    tenant_id: TenantId,
    subject: SubjectDigest,
    client: Mutex<Client>,
}

impl fmt::Debug for LocalPostgresAtomicMirrorCheckpointDispatcher {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresAtomicMirrorCheckpointDispatcher")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("client", &"<redacted>")
            .finish()
    }
}

impl LocalPostgresAtomicMirrorCheckpointDispatcher {
    /// Connects only when the exact v15 schema and v3-only least-privilege surface are present.
    ///
    /// # Errors
    ///
    /// Fails closed for transport, role, migration, RLS or privilege drift.
    pub fn connect(
        config: &LocalPostgresHistoryCheckpointConfig,
        tenant_id: TenantId,
        subject: SubjectDigest,
    ) -> Result<Self, CheckpointDispatchError> {
        Self::connect_diagnosed(config, tenant_id, subject)
            .map_err(PostgresCheckpointConnectFailure::into_error)
    }

    /// Performs v15 admission while retaining only a closed stage and public error category.
    ///
    /// # Errors
    ///
    /// Returns the first failed admission stage without retaining backend diagnostics.
    pub fn connect_diagnosed(
        config: &LocalPostgresHistoryCheckpointConfig,
        tenant_id: TenantId,
        subject: SubjectDigest,
    ) -> Result<Self, PostgresCheckpointConnectFailure> {
        let mut settings = Config::new();
        settings
            .host("127.0.0.1")
            .port(config.port)
            .dbname(&config.database)
            .user(&config.user)
            .password(config.password.as_bytes())
            .connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-atomic-mirror-checkpoint")
            .options(
                "-c statement_timeout=5000 -c lock_timeout=1000 \
                 -c idle_in_transaction_session_timeout=5000 \
                 -c transaction_timeout=10000 -c search_path=pg_catalog",
            );
        let mut client =
            settings
                .connect(NoTls)
                .map_err(|error| PostgresCheckpointConnectFailure {
                    stage: PostgresCheckpointConnectStage::Transport,
                    error: db_dispatch_error(error),
                })?;
        verify_atomic_database(&mut client)?;
        Ok(Self {
            tenant_id,
            subject,
            client: Mutex::new(client),
        })
    }
}

impl CheckpointDispatcher for LocalPostgresHistoryCheckpointDispatcher {
    fn dispatch(
        &self,
        request: &CheckpointDispatchRequest<'_>,
    ) -> Result<CheckpointDispatchOutcome, CheckpointDispatchError> {
        if request.tenant_id() != self.tenant_id || request.subject() != self.subject {
            return Err(CheckpointDispatchError::Rejected);
        }
        let (context, checkpoint) = map_history_checkpoint_request(request)?;
        let request_sha256 = checkpoint
            .canonical_sha256()
            .map_err(|_| CheckpointDispatchError::Unavailable)?;
        let tenant_id = context.tenant_id().as_uuid();
        let subject = context.subject().hex();
        let project_id = checkpoint.project_id().as_uuid();
        let request_id = checkpoint.request_id().as_uuid();
        let checkpoint_id = checkpoint.checkpoint_id().as_uuid();
        let revision_id = checkpoint.revision_id().as_uuid();
        let label = checkpoint.label().as_str().to_owned();
        let note = checkpoint.note().map(|value| value.as_str().to_owned());
        let request_sha256 = request_sha256.hex();

        let mut client = self
            .client
            .try_lock()
            .map_err(|_| CheckpointDispatchError::Unavailable)?;
        let mut transaction = client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()
            .map_err(db_dispatch_error)?;
        transaction
            .query_one(
                "SELECT set_config('hwpx_agent.tenant_id',$1,true), \
                        set_config('hwpx_agent.subject_sha256',$2,true)",
                &[&tenant_id.hyphenated().to_string(), &subject],
            )
            .map_err(db_dispatch_error)?;
        let row = transaction
            .query_one(
                "SELECT outcome,checkpoint_id,revision_id,label,note,request_sha256::text \
                 FROM hwpx_agent.create_history_checkpoint_v2( \
                    $1,$2,$3,$4,$5,$6,$7,$8,$9)",
                &[
                    &tenant_id,
                    &project_id,
                    &subject,
                    &request_id,
                    &request_sha256,
                    &checkpoint_id,
                    &revision_id,
                    &label,
                    &note,
                ],
            )
            .map_err(db_dispatch_error)?;
        let outcome: String = value(&row, "outcome")?;
        let replayed = match outcome.as_str() {
            "created" => false,
            "replayed" => true,
            _ => return Err(CheckpointDispatchError::Unavailable),
        };
        if value::<uuid::Uuid>(&row, "checkpoint_id")? != checkpoint_id
            || value::<uuid::Uuid>(&row, "revision_id")? != revision_id
            || value::<String>(&row, "label")? != label
            || value::<Option<String>>(&row, "note")? != note
            || value::<String>(&row, "request_sha256")? != request_sha256
        {
            return Err(CheckpointDispatchError::Unavailable);
        }
        transaction.commit().map_err(db_dispatch_error)?;
        Ok(CheckpointDispatchOutcome::new(
            checkpoint.checkpoint_id().public_id(),
            checkpoint.revision_id().public_id(),
            replayed,
        ))
    }
}

impl CheckpointDispatcher for LocalPostgresAtomicMirrorCheckpointDispatcher {
    fn dispatch(
        &self,
        request: &CheckpointDispatchRequest<'_>,
    ) -> Result<CheckpointDispatchOutcome, CheckpointDispatchError> {
        if request.tenant_id() != self.tenant_id || request.subject() != self.subject {
            return Err(CheckpointDispatchError::Rejected);
        }
        let (context, checkpoint) = map_history_checkpoint_request(request)?;
        let branch_id =
            BranchId::parse(request.branch_id()).map_err(|_| CheckpointDispatchError::Rejected)?;
        let mirror_id = MirrorId::parse_public(request.mirror_id())
            .map_err(|_| CheckpointDispatchError::Rejected)?;
        let expected_generation = i64::try_from(request.expected_generation())
            .map_err(|_| CheckpointDispatchError::Rejected)?;
        let request_sha256 = checkpoint
            .canonical_sha256()
            .map_err(|_| CheckpointDispatchError::Unavailable)?;
        let tenant_id = context.tenant_id().as_uuid();
        let subject = context.subject().hex();
        let project_id = checkpoint.project_id().as_uuid();
        let request_id = checkpoint.request_id().as_uuid();
        let checkpoint_id = checkpoint.checkpoint_id().as_uuid();
        let revision_id = checkpoint.revision_id().as_uuid();
        let label = checkpoint.label().as_str().to_owned();
        let note = checkpoint.note().map(|value| value.as_str().to_owned());
        let request_sha256 = request_sha256.hex();

        let mut client = self
            .client
            .try_lock()
            .map_err(|_| CheckpointDispatchError::Unavailable)?;
        let mut transaction = client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()
            .map_err(db_dispatch_error)?;
        transaction
            .query_one(
                "SELECT set_config('hwpx_agent.tenant_id',$1,true), \
                        set_config('hwpx_agent.subject_sha256',$2,true)",
                &[&tenant_id.hyphenated().to_string(), &subject],
            )
            .map_err(db_dispatch_error)?;
        let row = transaction
            .query_one(
                "SELECT outcome,checkpoint_id,revision_id,label,note,request_sha256::text \
                 FROM hwpx_agent.create_mirror_history_checkpoint_v3( \
                    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                &[
                    &tenant_id,
                    &project_id,
                    &subject,
                    &branch_id.as_uuid(),
                    &mirror_id.as_uuid(),
                    &revision_id,
                    &expected_generation,
                    &request_id,
                    &request_sha256,
                    &checkpoint_id,
                    &revision_id,
                    &label,
                    &note,
                ],
            )
            .map_err(db_dispatch_error)?;
        let outcome: String = value(&row, "outcome")?;
        let replayed = match outcome.as_str() {
            "created" => false,
            "replayed" => true,
            _ => return Err(CheckpointDispatchError::Unavailable),
        };
        if value::<uuid::Uuid>(&row, "checkpoint_id")? != checkpoint_id
            || value::<uuid::Uuid>(&row, "revision_id")? != revision_id
            || value::<String>(&row, "label")? != label
            || value::<Option<String>>(&row, "note")? != note
            || value::<String>(&row, "request_sha256")? != request_sha256
        {
            return Err(CheckpointDispatchError::Unavailable);
        }
        transaction.commit().map_err(db_dispatch_error)?;
        Ok(CheckpointDispatchOutcome::new(
            checkpoint.checkpoint_id().public_id(),
            checkpoint.revision_id().public_id(),
            replayed,
        ))
    }
}

fn verify_database(client: &mut Client) -> Result<(), PostgresCheckpointConnectFailure> {
    for (stage, check) in [
        (
            PostgresCheckpointConnectStage::Role,
            verify_role as fn(&mut Client) -> Result<(), CheckpointDispatchError>,
        ),
        (
            PostgresCheckpointConnectStage::Migrations,
            verify_migrations,
        ),
        (PostgresCheckpointConnectStage::Policies, verify_policies),
        (
            PostgresCheckpointConnectStage::Privileges,
            verify_privileges,
        ),
    ] {
        check(client).map_err(|error| PostgresCheckpointConnectFailure { stage, error })?;
    }
    Ok(())
}

fn verify_atomic_database(client: &mut Client) -> Result<(), PostgresCheckpointConnectFailure> {
    for (stage, check) in [
        (
            PostgresCheckpointConnectStage::Role,
            verify_role as fn(&mut Client) -> Result<(), CheckpointDispatchError>,
        ),
        (
            PostgresCheckpointConnectStage::Migrations,
            verify_atomic_migrations,
        ),
        (
            PostgresCheckpointConnectStage::Policies,
            verify_atomic_policies,
        ),
        (
            PostgresCheckpointConnectStage::Privileges,
            verify_atomic_privileges,
        ),
    ] {
        check(client).map_err(|error| PostgresCheckpointConnectFailure { stage, error })?;
    }
    Ok(())
}

fn verify_role(client: &mut Client) -> Result<(), CheckpointDispatchError> {
    let row = client
        .query_one(
            "SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication \
             FROM pg_roles WHERE rolname=current_user",
            &[],
        )
        .map_err(db_dispatch_error)?;
    for field in [
        "rolsuper",
        "rolbypassrls",
        "rolcreaterole",
        "rolcreatedb",
        "rolreplication",
    ] {
        if value::<bool>(&row, field)? {
            return Err(CheckpointDispatchError::Rejected);
        }
    }
    Ok(())
}

fn verify_migrations(client: &mut Client) -> Result<(), CheckpointDispatchError> {
    verify_migration_set(
        client,
        &MIGRATIONS,
        "SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions \
         ORDER BY version LIMIT 15",
    )
}

fn verify_atomic_migrations(client: &mut Client) -> Result<(), CheckpointDispatchError> {
    let query = "SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions \
                 ORDER BY version LIMIT 17";
    let rows = client.query(query, &[]).map_err(db_dispatch_error)?;
    match rows.len() {
        15 => verify_migration_rows(&rows, &ATOMIC_MIGRATIONS),
        required_version @ (16 | 17) => {
            verify_migration_rows(&rows, &CURRENT_ATOMIC_MIGRATIONS[..required_version])
        }
        _ => Err(CheckpointDispatchError::Rejected),
    }
}

fn verify_migration_set(
    client: &mut Client,
    migrations: &[&[u8]],
    query: &str,
) -> Result<(), CheckpointDispatchError> {
    let rows = client.query(query, &[]).map_err(db_dispatch_error)?;
    verify_migration_rows(&rows, migrations)
}

fn verify_migration_rows(
    rows: &[Row],
    migrations: &[&[u8]],
) -> Result<(), CheckpointDispatchError> {
    if rows.len() != migrations.len() {
        return Err(CheckpointDispatchError::Rejected);
    }
    for (index, row) in rows.iter().enumerate() {
        if value::<i64>(row, "version")?
            != i64::try_from(index + 1).map_err(|_| CheckpointDispatchError::Rejected)?
            || value::<String>(row, "migration_sha256")?
                != hex::encode(Sha256::digest(migrations[index]))
        {
            return Err(CheckpointDispatchError::Rejected);
        }
    }
    Ok(())
}

fn verify_policies(client: &mut Client) -> Result<(), CheckpointDispatchError> {
    let rows = client
        .query(
            "SELECT class.relname,class.relrowsecurity,class.relforcerowsecurity, \
                (pg_has_role(class.relowner,'USAGE') OR pg_has_role(class.relowner,'SET')) \
                    AS owner_role, \
                (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid) \
                    AS policy_count, \
                (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid \
                    AND policy.polname='tenant_isolation' AND policy.polcmd='*' \
                    AND policy.polpermissive AND policy.polroles=ARRAY[0::oid] \
                    AND pg_get_expr(policy.polqual,policy.polrelid)= \
                        '(tenant_id = hwpx_agent.current_tenant_id())' \
                    AND pg_get_expr(policy.polwithcheck,policy.polrelid)= \
                        '(tenant_id = hwpx_agent.current_tenant_id())') AS policy_match \
             FROM pg_class class JOIN pg_namespace namespace ON namespace.oid=class.relnamespace \
             WHERE namespace.nspname='hwpx_agent' \
               AND class.relname IN ('checkpoints','history_checkpoint_requests')",
            &[],
        )
        .map_err(db_dispatch_error)?;
    if rows.len() != 2 {
        return Err(CheckpointDispatchError::Rejected);
    }
    for row in rows {
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<i64>(&row, "policy_count")? != 1
            || value::<i64>(&row, "policy_match")? != 1
        {
            return Err(CheckpointDispatchError::Rejected);
        }
    }
    Ok(())
}

fn verify_atomic_policies(client: &mut Client) -> Result<(), CheckpointDispatchError> {
    let rows = client
        .query(
            "SELECT class.relname,class.relrowsecurity,class.relforcerowsecurity, \
                (pg_has_role(class.relowner,'USAGE') OR pg_has_role(class.relowner,'SET')) \
                    AS owner_role, \
                (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid) \
                    AS policy_count, \
                (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid \
                    AND policy.polname='tenant_isolation' AND policy.polcmd='*' \
                    AND policy.polpermissive AND policy.polroles=ARRAY[0::oid] \
                    AND pg_get_expr(policy.polqual,policy.polrelid)= \
                        '(tenant_id = hwpx_agent.current_tenant_id())' \
                    AND pg_get_expr(policy.polwithcheck,policy.polrelid)= \
                        '(tenant_id = hwpx_agent.current_tenant_id())') AS policy_match \
             FROM pg_class class JOIN pg_namespace namespace ON namespace.oid=class.relnamespace \
             WHERE namespace.nspname='hwpx_agent' \
               AND class.relname IN ( \
                    'projects','project_acl','branches','project_local_mirrors','revisions', \
                    'revision_graph_seals','checkpoints','history_checkpoint_requests', \
                    'audit_events')",
            &[],
        )
        .map_err(db_dispatch_error)?;
    if rows.len() != 9 {
        return Err(CheckpointDispatchError::Rejected);
    }
    for row in rows {
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<i64>(&row, "policy_count")? != 1
            || value::<i64>(&row, "policy_match")? != 1
        {
            return Err(CheckpointDispatchError::Rejected);
        }
    }
    Ok(())
}

fn verify_privileges(client: &mut Client) -> Result<(), CheckpointDispatchError> {
    let row = client
        .query_one(
            "SELECT \
                has_function_privilege( \
                    'hwpx_agent.create_history_checkpoint_v2(uuid,uuid,character,uuid,character,uuid,uuid,text,text)', \
                    'EXECUTE') AS exact_execute, \
                has_function_privilege( \
                    'hwpx_agent.create_history_checkpoint(uuid,uuid,character,uuid,character,uuid,uuid,text)', \
                    'EXECUTE') AS legacy_execute, \
                has_schema_privilege('hwpx_agent','CREATE') \
                OR has_table_privilege('hwpx_agent.history_checkpoint_requests', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.checkpoints', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.audit_events', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.schema_versions', \
                    'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS excessive, \
                (pg_has_role(procedure.proowner,'USAGE') \
                    OR pg_has_role(procedure.proowner,'SET')) AS owner_role \
             FROM pg_proc procedure \
             JOIN pg_namespace namespace ON namespace.oid=procedure.pronamespace \
             WHERE namespace.nspname='hwpx_agent' \
               AND procedure.oid=to_regprocedure( \
                    'hwpx_agent.create_history_checkpoint_v2(uuid,uuid,character,uuid,character,uuid,uuid,text,text)')",
            &[],
        )
        .map_err(db_dispatch_error)?;
    if !value::<bool>(&row, "exact_execute")?
        || value::<bool>(&row, "legacy_execute")?
        || value::<bool>(&row, "excessive")?
        || value::<bool>(&row, "owner_role")?
    {
        return Err(CheckpointDispatchError::Rejected);
    }
    Ok(())
}

fn verify_atomic_privileges(client: &mut Client) -> Result<(), CheckpointDispatchError> {
    let row = client
        .query_one(
            "SELECT \
                has_function_privilege( \
                    'hwpx_agent.create_mirror_history_checkpoint_v3(uuid,uuid,character,uuid,uuid,uuid,bigint,uuid,character,uuid,uuid,text,text)', \
                    'EXECUTE') AS exact_execute, \
                has_function_privilege( \
                    'hwpx_agent.create_history_checkpoint_v2(uuid,uuid,character,uuid,character,uuid,uuid,text,text)', \
                    'EXECUTE') AS v2_execute, \
                has_function_privilege( \
                    'hwpx_agent.create_history_checkpoint(uuid,uuid,character,uuid,character,uuid,uuid,text)', \
                    'EXECUTE') AS legacy_execute, \
                has_schema_privilege('hwpx_agent','CREATE') \
                OR has_table_privilege('hwpx_agent.projects', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.project_acl', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.branches', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.project_local_mirrors', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.revisions', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.revision_graph_seals', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.history_checkpoint_requests', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.checkpoints', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.audit_events', \
                    'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                OR has_table_privilege('hwpx_agent.schema_versions', \
                    'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS excessive, \
                (pg_has_role(procedure.proowner,'USAGE') \
                    OR pg_has_role(procedure.proowner,'SET')) AS owner_role \
             FROM pg_proc procedure \
             JOIN pg_namespace namespace ON namespace.oid=procedure.pronamespace \
             WHERE namespace.nspname='hwpx_agent' \
               AND procedure.oid=to_regprocedure( \
                    'hwpx_agent.create_mirror_history_checkpoint_v3(uuid,uuid,character,uuid,uuid,uuid,bigint,uuid,character,uuid,uuid,text,text)')",
            &[],
        )
        .map_err(db_dispatch_error)?;
    if !value::<bool>(&row, "exact_execute")?
        || value::<bool>(&row, "v2_execute")?
        || value::<bool>(&row, "legacy_execute")?
        || value::<bool>(&row, "excessive")?
        || value::<bool>(&row, "owner_role")?
    {
        return Err(CheckpointDispatchError::Rejected);
    }
    Ok(())
}

fn db_dispatch_error(error: postgres::Error) -> CheckpointDispatchError {
    let mapped = match error.code().map(postgres::error::SqlState::code) {
        Some("22023" | "23503" | "23505" | "23514" | "42501" | "P0002" | "P1701" | "P1702") => {
            CheckpointDispatchError::Rejected
        }
        _ => CheckpointDispatchError::Unavailable,
    };
    drop(error);
    mapped
}

fn value<T: FromSqlOwned>(row: &Row, column: &str) -> Result<T, CheckpointDispatchError> {
    row.try_get(column).map_err(db_dispatch_error)
}

#[cfg(test)]
mod tests {
    use artifact_service::{SubjectDigest, TenantId};
    use local_sync::{CheckpointServiceContext, decode_checkpoint_to_service};
    use uuid::Uuid;

    use super::*;

    const ACTUAL_TENANT: &str = "d1000000-0000-0000-0000-000000000001";
    const ACTUAL_SUBJECT: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn configured_value(name: &str) -> String {
        std::env::var(name).unwrap_or_else(|_| panic!("missing isolated test setting: {name}"))
    }

    fn actual_binding(note: &str) -> local_sync::CheckpointServiceBinding {
        let request = concat!(
            "{\"schema_version\":\"hwpx-agent.remote-sync-request/v3\",",
            "\"operation\":\"checkpoint\",",
            "\"project_id\":\"prj_d2000000000000000000000000000001\",",
            "\"branch_id\":\"brn_branch001\",",
            "\"mirror_id\":\"mir_mirror001\",",
            "\"expected_head\":{\"revision_id\":",
            "\"rev_d5000000000000000000000000000004\",\"generation\":3},",
            "\"idempotency_key\":\"checkpoint-postgres-0001\",",
            "\"label\":\"P17 durable checkpoint\",\"note\":\"__NOTE__\"}"
        )
        .replace("__NOTE__", note);
        let context = CheckpointServiceContext::new(
            "req_postgres_actual_00000001".to_owned(),
            "ko-KR".to_owned(),
        )
        .unwrap_or_else(|error| panic!("test context: {error}"));
        decode_checkpoint_to_service(request.as_bytes(), &context)
            .unwrap_or_else(|error| panic!("test binding: {error}"))
    }

    #[test]
    fn local_config_rejects_unsafe_or_unbounded_values() {
        for (port, database, user, password) in [
            (
                0,
                "postgres".to_owned(),
                "app".to_owned(),
                "secret".to_owned(),
            ),
            (1, String::new(), "app".to_owned(), "secret".to_owned()),
            (
                1,
                "postgres;drop".to_owned(),
                "app".to_owned(),
                "secret".to_owned(),
            ),
            (
                1,
                "postgres".to_owned(),
                "x".repeat(64),
                "secret".to_owned(),
            ),
            (1, "postgres".to_owned(), "app".to_owned(), String::new()),
            (
                1,
                "postgres".to_owned(),
                "app".to_owned(),
                "x".repeat(1_025),
            ),
            (
                1,
                "postgres".to_owned(),
                "app".to_owned(),
                "bad\0secret".to_owned(),
            ),
        ] {
            assert_eq!(
                LocalPostgresHistoryCheckpointConfig::new(port, database, user, password).err(),
                Some(CheckpointDispatchError::Rejected)
            );
        }
        assert!(
            LocalPostgresHistoryCheckpointConfig::new(
                u16::MAX,
                "x".repeat(63),
                "x".repeat(63),
                "x".repeat(1_024),
            )
            .is_ok()
        );
    }

    #[test]
    fn debug_and_diagnostics_do_not_retain_private_values() {
        let config = LocalPostgresHistoryCheckpointConfig::new(
            54_321,
            "private_database".to_owned(),
            "private_user".to_owned(),
            "private_secret".to_owned(),
        )
        .unwrap_or_else(|error| panic!("synthetic config: {error}"));
        assert_eq!(
            format!("{config:?}"),
            "LocalPostgresHistoryCheckpointConfig { .. }"
        );
        for (stage, code) in [
            (PostgresCheckpointConnectStage::Transport, "TRANSPORT"),
            (PostgresCheckpointConnectStage::Role, "ROLE"),
            (PostgresCheckpointConnectStage::Migrations, "MIGRATIONS"),
            (PostgresCheckpointConnectStage::Policies, "POLICIES"),
            (PostgresCheckpointConnectStage::Privileges, "PRIVILEGES"),
        ] {
            let failure = PostgresCheckpointConnectFailure {
                stage,
                error: CheckpointDispatchError::Rejected,
            };
            assert_eq!(failure.stage(), stage);
            assert_eq!(failure.error(), CheckpointDispatchError::Rejected);
            assert_eq!(
                failure.to_string(),
                format!("{code}:CHECKPOINT_DISPATCH_REJECTED")
            );
            assert_eq!(failure.into_error(), CheckpointDispatchError::Rejected);
        }
    }

    #[test]
    #[ignore = "requires the isolated P17 PostgreSQL qualification database"]
    fn actual_postgres_checkpoint_creates_replays_and_rejects_drift() {
        let port = configured_value("HWPX_P17_PG_PORT")
            .parse::<u16>()
            .unwrap_or_else(|_| panic!("invalid isolated test port"));
        let config = LocalPostgresHistoryCheckpointConfig::new(
            port,
            configured_value("HWPX_P17_PG_DATABASE"),
            configured_value("HWPX_P17_PG_USER"),
            configured_value("HWPX_P17_PG_PASSWORD"),
        )
        .unwrap_or_else(|error| panic!("isolated test config: {error}"));
        let tenant_id = TenantId::new(
            Uuid::parse_str(ACTUAL_TENANT)
                .unwrap_or_else(|error| panic!("isolated tenant fixture: {error}")),
        )
        .unwrap_or_else(|error| panic!("isolated tenant identity: {error}"));
        let subject = SubjectDigest::parse(ACTUAL_SUBJECT)
            .unwrap_or_else(|error| panic!("isolated subject fixture: {error}"));
        let dispatcher =
            LocalPostgresHistoryCheckpointDispatcher::connect(&config, tenant_id, subject)
                .unwrap_or_else(|error| panic!("isolated database admission: {error}"));
        let binding = actual_binding("한글 2020 PostgreSQL checkpoint note");
        let request = CheckpointDispatchRequest {
            tenant_id,
            subject,
            now_unix_seconds: 2_000_000_000,
            binding: &binding,
        };
        let created = dispatcher
            .dispatch(&request)
            .unwrap_or_else(|error| panic!("create checkpoint: {error}"));
        let replayed = dispatcher
            .dispatch(&request)
            .unwrap_or_else(|error| panic!("replay checkpoint: {error}"));
        assert!(!created.replayed());
        assert!(replayed.replayed());
        assert_eq!(created.checkpoint_id(), replayed.checkpoint_id());
        assert_eq!(created.revision_id(), replayed.revision_id());

        let drifted_binding = actual_binding("changed PostgreSQL checkpoint note");
        let drifted = CheckpointDispatchRequest {
            tenant_id,
            subject,
            now_unix_seconds: 2_000_000_001,
            binding: &drifted_binding,
        };
        assert_eq!(
            dispatcher.dispatch(&drifted),
            Err(CheckpointDispatchError::Rejected)
        );
    }
}
