//! Authenticated pull of one exact local bare-Git mirror state into the durable mirror registry.
//!
//! Git is read without mutation. `PostgreSQL` atomically records the exact observation and either
//! advances a clean mirror or records a conflict without overwriting pending local work.

use std::fmt;
use std::io::Read as _;
use std::net::{Shutdown, SocketAddr, TcpListener, TcpStream};
use std::path::Path;
use std::sync::Mutex;
use std::time::Duration;

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::{AuthMiddleware, AuthScope};
use postgres::types::FromSqlOwned;
use postgres::{Client, Config, IsolationLevel, NoTls, Row, Transaction};
use remote_sync_wire::{FrameError, ResponseStatus, read_request, write_response};
use retention_sync_service::MirrorId;
use revision_service::{BranchId, ProjectId, RevisionId};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use uuid::Uuid;

use crate::git_mirror::{GitMirrorEffectError, GitMirrorEffectHost, GitMirrorSnapshot};
use crate::postgres::LocalPostgresHistoryCheckpointConfig;

const REQUEST_SCHEMA: &str = "hwpx-agent.remote-sync-request/v4";
const RESPONSE_SCHEMA: &str = "hwpx-agent.remote-sync-response/v1";
const MAX_REQUEST_BYTES: usize = 16_384;
const MAX_TIMEOUT: Duration = Duration::from_mins(1);
const OBSERVATION_NAMESPACE: Uuid = Uuid::from_u128(0xc383_661b_ef55_5b22_b5da_4320_f75e_95de);

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

const DURABLE_PULL_MIGRATIONS: [&[u8]; 17] = [
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

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum GitPullHostFailure {
    #[error("Git pull host rejected the exchange")]
    Rejected,
    #[error("Git pull host cannot determine the exchange outcome")]
    Unavailable,
}

impl GitPullHostFailure {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::Rejected => "GIT_PULL_HOST_REJECTED",
            Self::Unavailable => "GIT_PULL_HOST_UNAVAILABLE",
        }
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum GitPullDispatchError {
    #[error("Git pull coordinator rejected the request")]
    Rejected,
    #[error("Git pull coordinator outcome is unavailable")]
    Unavailable,
}

impl GitPullDispatchError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::Rejected => "GIT_PULL_DISPATCH_REJECTED",
            Self::Unavailable => "GIT_PULL_DISPATCH_UNAVAILABLE",
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum GitPullDispatchOutcome {
    Succeeded {
        revision_id: Option<String>,
        generation: u64,
        snapshot_sha256: String,
        replayed: bool,
    },
    Conflict {
        revision_id: String,
        generation: u64,
        replayed: bool,
    },
    Rejected,
}

impl fmt::Debug for GitPullDispatchOutcome {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Succeeded {
                generation,
                replayed,
                ..
            } => formatter
                .debug_struct("GitPullDispatchOutcome::Succeeded")
                .field("generation", generation)
                .field("replayed", replayed)
                .field("identities", &"<redacted>")
                .finish(),
            Self::Conflict {
                generation,
                replayed,
                ..
            } => formatter
                .debug_struct("GitPullDispatchOutcome::Conflict")
                .field("generation", generation)
                .field("replayed", replayed)
                .field("identities", &"<redacted>")
                .finish(),
            Self::Rejected => formatter.write_str("GitPullDispatchOutcome::Rejected"),
        }
    }
}

pub struct GitPullDispatchRequest {
    tenant_id: TenantId,
    subject: SubjectDigest,
    request_sha256: String,
    project_id: ProjectId,
    branch_id: BranchId,
    mirror_id: MirrorId,
    observed_revision_id: Option<RevisionId>,
    observed_generation: u64,
    observed_snapshot_sha256: String,
}

impl GitPullDispatchRequest {
    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.tenant_id
    }

    #[must_use]
    pub const fn subject(&self) -> SubjectDigest {
        self.subject
    }

    #[must_use]
    pub fn request_sha256(&self) -> &str {
        &self.request_sha256
    }

    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    #[must_use]
    pub const fn branch_id(&self) -> BranchId {
        self.branch_id
    }

    #[must_use]
    pub const fn mirror_id(&self) -> MirrorId {
        self.mirror_id
    }

    #[must_use]
    pub const fn observed_revision_id(&self) -> Option<RevisionId> {
        self.observed_revision_id
    }

    #[must_use]
    pub const fn observed_generation(&self) -> u64 {
        self.observed_generation
    }

    #[must_use]
    pub fn observed_snapshot_sha256(&self) -> &str {
        &self.observed_snapshot_sha256
    }
}

impl fmt::Debug for GitPullDispatchRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitPullDispatchRequest")
            .field("observed_generation", &self.observed_generation)
            .field("identities", &"<redacted>")
            .finish_non_exhaustive()
    }
}

pub trait GitPullCoordinator: fmt::Debug {
    /// Reconciles one authenticated, snapshot-bound Git observation.
    ///
    /// # Errors
    ///
    /// Returns unavailable for every uncertain Git or database outcome.
    fn dispatch(
        &self,
        request: &GitPullDispatchRequest,
    ) -> Result<GitPullDispatchOutcome, GitPullDispatchError>;
}

pub struct GitPullHost<C> {
    authentication: Mutex<AuthMiddleware>,
    coordinator: C,
}

impl<C> GitPullHost<C> {
    #[must_use]
    pub const fn new(authentication: AuthMiddleware, coordinator: C) -> Self {
        Self {
            authentication: Mutex::new(authentication),
            coordinator,
        }
    }
}

impl<C> fmt::Debug for GitPullHost<C> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitPullHost")
            .field("authentication", &"<redacted>")
            .field("coordinator", &"<redacted>")
            .finish()
    }
}

impl<C: GitPullCoordinator> GitPullHost<C> {
    /// Authenticates and handles exactly one canonical pull-v4 request.
    ///
    /// # Errors
    ///
    /// Malformed/auth failures are rejected; uncertain coordinator outcomes are unavailable.
    pub fn handle_pull(
        &self,
        authorization_header: &str,
        request_bytes: &[u8],
        now_unix_seconds: u64,
    ) -> Result<Vec<u8>, GitPullHostFailure> {
        if request_bytes.is_empty() || request_bytes.len() > MAX_REQUEST_BYTES {
            return Err(GitPullHostFailure::Rejected);
        }
        let auth = self
            .authentication
            .lock()
            .map_err(|_| GitPullHostFailure::Unavailable)?
            .authenticate_internal_service_once(
                authorization_header,
                now_unix_seconds,
                [AuthScope::MirrorSync],
            )
            .map_err(|_| GitPullHostFailure::Rejected)?;
        let parsed = parse_request(request_bytes, auth.tenant_id(), auth.subject())?;
        let outcome = match self.coordinator.dispatch(&parsed) {
            Ok(value) => value,
            Err(GitPullDispatchError::Rejected) => GitPullDispatchOutcome::Rejected,
            Err(GitPullDispatchError::Unavailable) => {
                return Err(GitPullHostFailure::Unavailable);
            }
        };
        let result = match outcome {
            GitPullDispatchOutcome::Succeeded {
                revision_id,
                generation,
                snapshot_sha256,
                ..
            } => PullWireResult::Succeeded {
                head: OwnedWireHead {
                    revision_id,
                    generation,
                },
                snapshot_sha256,
            },
            GitPullDispatchOutcome::Conflict {
                revision_id,
                generation,
                ..
            } => PullWireResult::Conflict {
                head: OwnedWireHead {
                    revision_id: Some(revision_id),
                    generation,
                },
            },
            GitPullDispatchOutcome::Rejected => PullWireResult::Rejected {},
        };
        serde_json::to_vec(&BoundPullResponse {
            schema_version: RESPONSE_SCHEMA,
            request_sha256: parsed.request_sha256(),
            result,
        })
        .map_err(|_| GitPullHostFailure::Unavailable)
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum GitPullServerFailure {
    #[error("Git pull server configuration or frame was rejected")]
    Rejected,
    #[error("Git pull server outcome is unavailable")]
    Unavailable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GitPullServeOutcome {
    Succeeded,
    Rejected,
    Unavailable,
}

pub struct LoopbackGitPullServer<C> {
    listener: TcpListener,
    host: GitPullHost<C>,
    io_timeout: Duration,
}

impl<C> fmt::Debug for LoopbackGitPullServer<C> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LoopbackGitPullServer")
            .field("local_addr", &self.listener.local_addr().ok())
            .field("host", &"<redacted>")
            .field("io_timeout", &self.io_timeout)
            .finish()
    }
}

impl<C> LoopbackGitPullServer<C> {
    /// Binds only an exact loopback endpoint with a bounded I/O timeout.
    ///
    /// # Errors
    ///
    /// Rejects non-loopback addresses and timeouts outside 1 ms..=60 s.
    pub fn bind(
        endpoint: SocketAddr,
        host: GitPullHost<C>,
        io_timeout: Duration,
    ) -> Result<Self, GitPullServerFailure> {
        if !endpoint.ip().is_loopback()
            || io_timeout < Duration::from_millis(1)
            || io_timeout > MAX_TIMEOUT
        {
            return Err(GitPullServerFailure::Rejected);
        }
        let listener =
            TcpListener::bind(endpoint).map_err(|_| GitPullServerFailure::Unavailable)?;
        Ok(Self {
            listener,
            host,
            io_timeout,
        })
    }

    /// Returns the exact OS-bound loopback endpoint.
    ///
    /// # Errors
    ///
    /// Returns unavailable if the listener no longer exposes its address.
    pub fn local_addr(&self) -> Result<SocketAddr, GitPullServerFailure> {
        self.listener
            .local_addr()
            .map_err(|_| GitPullServerFailure::Unavailable)
    }
}

impl<C: GitPullCoordinator> LoopbackGitPullServer<C> {
    /// Accepts and resolves exactly one bounded framed request.
    ///
    /// # Errors
    ///
    /// Returns unavailable when accept or definitive response delivery is uncertain.
    pub fn serve_one_at(
        &self,
        now_unix_seconds: u64,
    ) -> Result<GitPullServeOutcome, GitPullServerFailure> {
        if now_unix_seconds == 0 {
            return Err(GitPullServerFailure::Rejected);
        }
        let (mut stream, peer) = self
            .listener
            .accept()
            .map_err(|_| GitPullServerFailure::Unavailable)?;
        if !peer.ip().is_loopback() {
            write_server_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
            return Ok(GitPullServeOutcome::Rejected);
        }
        stream
            .set_read_timeout(Some(self.io_timeout))
            .and_then(|()| stream.set_write_timeout(Some(self.io_timeout)))
            .map_err(|_| GitPullServerFailure::Unavailable)?;
        let framed = match read_request(&mut stream) {
            Ok(value) => value,
            Err(FrameError::Rejected) => {
                write_server_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                return Ok(GitPullServeOutcome::Rejected);
            }
            Err(FrameError::Unavailable) => {
                write_server_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                return Ok(GitPullServeOutcome::Unavailable);
            }
        };
        let mut trailing = [0_u8; 1];
        match stream.read(&mut trailing) {
            Ok(0) => {}
            Ok(_) => {
                write_server_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                return Ok(GitPullServeOutcome::Rejected);
            }
            Err(_) => {
                write_server_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                return Ok(GitPullServeOutcome::Unavailable);
            }
        }
        match self.host.handle_pull(
            framed.authorization_header(),
            framed.payload(),
            now_unix_seconds,
        ) {
            Ok(payload) => {
                write_server_outcome(&mut stream, ResponseStatus::Succeeded, &payload)?;
                Ok(GitPullServeOutcome::Succeeded)
            }
            Err(GitPullHostFailure::Rejected) => {
                write_server_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                Ok(GitPullServeOutcome::Rejected)
            }
            Err(GitPullHostFailure::Unavailable) => {
                write_server_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                Ok(GitPullServeOutcome::Unavailable)
            }
        }
    }
}

fn write_server_outcome(
    stream: &mut TcpStream,
    status: ResponseStatus,
    payload: &[u8],
) -> Result<(), GitPullServerFailure> {
    write_response(stream, status, payload).map_err(|_| GitPullServerFailure::Unavailable)?;
    stream
        .shutdown(Shutdown::Write)
        .map_err(|_| GitPullServerFailure::Unavailable)
}

pub struct LocalPostgresGitMirrorPullCoordinator {
    tenant_id: TenantId,
    subject: SubjectDigest,
    client: Mutex<Client>,
    git: GitMirrorEffectHost,
}

impl fmt::Debug for LocalPostgresGitMirrorPullCoordinator {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresGitMirrorPullCoordinator")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("client", &"<redacted>")
            .field("git", &"<redacted>")
            .finish()
    }
}

impl LocalPostgresGitMirrorPullCoordinator {
    /// Connects a tenant/subject-fixed least-privilege v17 database and local bare repository.
    ///
    /// # Errors
    ///
    /// Rejects configuration, schema, RLS, trigger, privilege or Git repository drift.
    pub fn connect(
        config: &LocalPostgresHistoryCheckpointConfig,
        tenant_id: TenantId,
        subject: SubjectDigest,
        bare_repository: &Path,
        git_program: &Path,
    ) -> Result<Self, GitPullDispatchError> {
        let git = GitMirrorEffectHost::open(bare_repository, git_program)
            .map_err(|_| GitPullDispatchError::Rejected)?;
        let mut settings = Config::new();
        settings
            .host("127.0.0.1")
            .port(config.port)
            .dbname(&config.database)
            .user(&config.user)
            .password(config.password.as_bytes())
            .connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-durable-git-pull")
            .options(
                "-c statement_timeout=5000 -c lock_timeout=1000 \
                 -c idle_in_transaction_session_timeout=5000 \
                 -c transaction_timeout=10000 -c search_path=pg_catalog",
            );
        let mut client = settings
            .connect(NoTls)
            .map_err(|_| GitPullDispatchError::Unavailable)?;
        verify_database(&mut client)?;
        Ok(Self {
            tenant_id,
            subject,
            client: Mutex::new(client),
            git,
        })
    }
}

impl GitPullCoordinator for LocalPostgresGitMirrorPullCoordinator {
    fn dispatch(
        &self,
        request: &GitPullDispatchRequest,
    ) -> Result<GitPullDispatchOutcome, GitPullDispatchError> {
        if request.tenant_id() != self.tenant_id || request.subject() != self.subject {
            return Err(GitPullDispatchError::Rejected);
        }
        let observation_id = observation_id(request);
        let remote = self
            .git
            .read_branch(
                &request.project_id().public_id(),
                &request.branch_id().public_id(),
            )
            .map_err(map_git_error)?;
        let remote = RemoteObservation::from_git(remote, request.observed_snapshot_sha256())?;
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| GitPullDispatchError::Unavailable)?;
        let mut transaction = serializable(&mut client)?;
        set_context(&mut transaction, request)?;
        let row = transaction
            .query_one(
                "SELECT outcome,revision_id,generation,snapshot_sha256::text,replayed \
                 FROM hwpx_agent.reconcile_git_mirror_pull_v1(\
                    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)",
                &[
                    &request.tenant_id().as_uuid(),
                    &request.project_id().as_uuid(),
                    &request.subject().hex(),
                    &request.branch_id().as_uuid(),
                    &request.mirror_id().as_uuid(),
                    &observation_id,
                    &request.request_sha256(),
                    &request.observed_revision_id().map(RevisionId::as_uuid),
                    &to_i64(request.observed_generation())?,
                    &request.observed_snapshot_sha256(),
                    &remote.revision_id,
                    &remote.generation,
                    &remote.snapshot_sha256,
                    &remote.git_oid,
                    &remote.git_state_sha256,
                ],
            )
            .map_err(map_db_error)?;
        let outcome: String = value(&row, "outcome")?;
        let revision_id: Option<Uuid> = value(&row, "revision_id")?;
        let generation: i64 = value(&row, "generation")?;
        let snapshot_sha256: String = value(&row, "snapshot_sha256")?;
        let replayed: bool = value(&row, "replayed")?;
        transaction.commit().map_err(map_db_error)?;
        let generation =
            u64::try_from(generation).map_err(|_| GitPullDispatchError::Unavailable)?;
        let revision_id = revision_id.map(revision_public).transpose()?;
        if !valid_head(revision_id.as_deref(), generation) || !valid_digest(&snapshot_sha256) {
            return Err(GitPullDispatchError::Unavailable);
        }
        match outcome.as_str() {
            "unchanged" | "updated" => Ok(GitPullDispatchOutcome::Succeeded {
                revision_id,
                generation,
                snapshot_sha256,
                replayed,
            }),
            "conflict" => Ok(GitPullDispatchOutcome::Conflict {
                revision_id: revision_id.ok_or(GitPullDispatchError::Unavailable)?,
                generation,
                replayed,
            }),
            _ => Err(GitPullDispatchError::Unavailable),
        }
    }
}

struct RemoteObservation {
    revision_id: Option<Uuid>,
    generation: i64,
    snapshot_sha256: String,
    git_oid: Option<String>,
    git_state_sha256: Option<String>,
}

impl RemoteObservation {
    fn from_git(
        snapshot: Option<GitMirrorSnapshot>,
        empty_snapshot_sha256: &str,
    ) -> Result<Self, GitPullDispatchError> {
        match snapshot {
            Some(snapshot) => Ok(Self {
                revision_id: Some(
                    RevisionId::parse(snapshot.revision_id())
                        .map_err(|_| GitPullDispatchError::Rejected)?
                        .as_uuid(),
                ),
                generation: to_i64(snapshot.generation())?,
                snapshot_sha256: snapshot.snapshot_sha256().to_owned(),
                git_oid: Some(snapshot.commit_oid().to_owned()),
                git_state_sha256: Some(snapshot.state_sha256().to_owned()),
            }),
            None => Ok(Self {
                revision_id: None,
                generation: 0,
                snapshot_sha256: empty_snapshot_sha256.to_owned(),
                git_oid: None,
                git_state_sha256: None,
            }),
        }
    }
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct PullWireRequest {
    schema_version: String,
    operation: String,
    project_id: String,
    branch_id: String,
    mirror_id: String,
    observed_head: PullWireHead,
    observed_snapshot_sha256: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct PullWireHead {
    revision_id: Option<String>,
    generation: u64,
}

#[derive(Serialize)]
struct BoundPullResponse<'a> {
    schema_version: &'static str,
    request_sha256: &'a str,
    result: PullWireResult,
}

#[derive(Serialize)]
#[serde(tag = "outcome", rename_all = "snake_case")]
enum PullWireResult {
    Succeeded {
        head: OwnedWireHead,
        snapshot_sha256: String,
    },
    Conflict {
        head: OwnedWireHead,
    },
    Rejected {},
}

#[derive(Serialize)]
struct OwnedWireHead {
    revision_id: Option<String>,
    generation: u64,
}

fn parse_request(
    bytes: &[u8],
    tenant_id: TenantId,
    subject: SubjectDigest,
) -> Result<GitPullDispatchRequest, GitPullHostFailure> {
    let wire: PullWireRequest =
        serde_json::from_slice(bytes).map_err(|_| GitPullHostFailure::Rejected)?;
    if serde_json::to_vec(&wire).map_err(|_| GitPullHostFailure::Unavailable)? != bytes
        || wire.schema_version != REQUEST_SCHEMA
        || wire.operation != "pull"
        || !valid_digest(&wire.observed_snapshot_sha256)
        || wire.observed_head.revision_id.is_none() != (wire.observed_head.generation == 0)
    {
        return Err(GitPullHostFailure::Rejected);
    }
    let project_id =
        ProjectId::parse(&wire.project_id).map_err(|_| GitPullHostFailure::Rejected)?;
    let branch_id = BranchId::parse(&wire.branch_id).map_err(|_| GitPullHostFailure::Rejected)?;
    let mirror_id =
        MirrorId::parse_public(&wire.mirror_id).map_err(|_| GitPullHostFailure::Rejected)?;
    let observed_revision_id = wire
        .observed_head
        .revision_id
        .as_deref()
        .map(RevisionId::parse)
        .transpose()
        .map_err(|_| GitPullHostFailure::Rejected)?;
    Ok(GitPullDispatchRequest {
        tenant_id,
        subject,
        request_sha256: digest(bytes),
        project_id,
        branch_id,
        mirror_id,
        observed_revision_id,
        observed_generation: wire.observed_head.generation,
        observed_snapshot_sha256: wire.observed_snapshot_sha256,
    })
}

fn observation_id(request: &GitPullDispatchRequest) -> Uuid {
    let mut name = Vec::with_capacity(16 * 3 + 64 * 2 + 4);
    for bytes in [
        request.tenant_id().as_uuid().as_bytes(),
        request.project_id().as_uuid().as_bytes(),
        request.mirror_id().as_uuid().as_bytes(),
    ] {
        name.extend_from_slice(bytes);
        name.push(0);
    }
    name.extend_from_slice(request.subject().hex().as_bytes());
    name.push(0);
    name.extend_from_slice(request.request_sha256().as_bytes());
    Uuid::new_v5(&OBSERVATION_NAMESPACE, &name)
}

fn serializable(client: &mut Client) -> Result<Transaction<'_>, GitPullDispatchError> {
    client
        .build_transaction()
        .isolation_level(IsolationLevel::Serializable)
        .start()
        .map_err(map_db_error)
}

fn set_context(
    transaction: &mut Transaction<'_>,
    request: &GitPullDispatchRequest,
) -> Result<(), GitPullDispatchError> {
    transaction
        .query_one(
            "SELECT set_config('hwpx_agent.tenant_id',$1,true), \
                    set_config('hwpx_agent.subject_sha256',$2,true)",
            &[
                &request.tenant_id().as_uuid().hyphenated().to_string(),
                &request.subject().hex(),
            ],
        )
        .map_err(map_db_error)?;
    Ok(())
}

fn verify_database(client: &mut Client) -> Result<(), GitPullDispatchError> {
    verify_role(client)?;
    verify_migrations(client)?;
    verify_rls_and_triggers(client)?;
    verify_function_security(client)?;
    verify_privileges(client)
}

fn verify_role(client: &mut Client) -> Result<(), GitPullDispatchError> {
    let row = client
        .query_one(
            "SELECT rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication \
             FROM pg_roles WHERE rolname=current_user",
            &[],
        )
        .map_err(map_db_error)?;
    for field in [
        "rolsuper",
        "rolbypassrls",
        "rolcreaterole",
        "rolcreatedb",
        "rolreplication",
    ] {
        if value::<bool>(&row, field)? {
            return Err(GitPullDispatchError::Rejected);
        }
    }
    Ok(())
}

fn verify_migrations(client: &mut Client) -> Result<(), GitPullDispatchError> {
    let rows = client
        .query(
            "SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions \
             ORDER BY version LIMIT 18",
            &[],
        )
        .map_err(map_db_error)?;
    if rows.len() != DURABLE_PULL_MIGRATIONS.len() {
        return Err(GitPullDispatchError::Rejected);
    }
    for (index, row) in rows.iter().enumerate() {
        if value::<i64>(row, "version")?
            != i64::try_from(index + 1).map_err(|_| GitPullDispatchError::Rejected)?
            || value::<String>(row, "migration_sha256")?
                != hex::encode(Sha256::digest(DURABLE_PULL_MIGRATIONS[index]))
        {
            return Err(GitPullDispatchError::Rejected);
        }
    }
    Ok(())
}

fn verify_rls_and_triggers(client: &mut Client) -> Result<(), GitPullDispatchError> {
    let table = client
        .query_one(
            "SELECT class.relrowsecurity,class.relforcerowsecurity, \
                (pg_has_role(class.relowner,'USAGE') OR pg_has_role(class.relowner,'SET')) \
                    AS owner_role, \
                (SELECT count(*) FROM pg_policy policy WHERE policy.polrelid=class.oid \
                    AND policy.polname='tenant_isolation' AND policy.polcmd='*' \
                    AND policy.polpermissive AND policy.polroles=ARRAY[0::oid] \
                    AND pg_get_expr(policy.polqual,policy.polrelid)= \
                        '(tenant_id = hwpx_agent.current_tenant_id())' \
                    AND pg_get_expr(policy.polwithcheck,policy.polrelid)= \
                        '(tenant_id = hwpx_agent.current_tenant_id())') AS policy_match \
             FROM pg_class class JOIN pg_namespace namespace ON namespace.oid=class.relnamespace \
             WHERE namespace.nspname='hwpx_agent' \
               AND class.relname='git_mirror_pull_observations'",
            &[],
        )
        .map_err(map_db_error)?;
    if !value::<bool>(&table, "relrowsecurity")?
        || !value::<bool>(&table, "relforcerowsecurity")?
        || value::<bool>(&table, "owner_role")?
        || value::<i64>(&table, "policy_match")? != 1
    {
        return Err(GitPullDispatchError::Rejected);
    }
    let trigger = client
        .query_one(
            "SELECT count(*) AS exact_count FROM pg_trigger trigger \
             JOIN pg_class class ON class.oid=trigger.tgrelid \
             JOIN pg_namespace namespace ON namespace.oid=class.relnamespace \
             WHERE namespace.nspname='hwpx_agent' AND trigger.tgenabled='O' \
               AND ((class.relname='project_local_mirrors' \
                    AND trigger.tgname='local_mirror_observed_snapshot_binding') \
                 OR (class.relname='git_mirror_pull_observations' \
                    AND trigger.tgname='git_mirror_pull_observation_guard'))",
            &[],
        )
        .map_err(map_db_error)?;
    if value::<i64>(&trigger, "exact_count")? != 2 {
        return Err(GitPullDispatchError::Rejected);
    }
    Ok(())
}

fn verify_function_security(client: &mut Client) -> Result<(), GitPullDispatchError> {
    let row = client
        .query_one(
            "SELECT proc.prosecdef AS security_definer, \
                COALESCE(proc.proconfig=ARRAY['search_path=pg_catalog, hwpx_agent']::text[],false) \
                    AS search_path_fixed, \
                (pg_has_role(proc.proowner,'USAGE') OR pg_has_role(proc.proowner,'SET')) \
                    AS owner_role, \
                EXISTS (SELECT 1 FROM \
                    aclexplode(COALESCE(proc.proacl,acldefault('f',proc.proowner))) AS acl \
                    WHERE acl.grantee=0 AND acl.privilege_type='EXECUTE') AS public_execute \
             FROM pg_proc proc \
             WHERE proc.oid='hwpx_agent.reconcile_git_mirror_pull_v1(uuid,uuid,character,uuid,uuid,uuid,character,uuid,bigint,character,uuid,bigint,character,text,character)'::regprocedure",
            &[],
        )
        .map_err(map_db_error)?;
    if !value::<bool>(&row, "security_definer")?
        || !value::<bool>(&row, "search_path_fixed")?
        || value::<bool>(&row, "owner_role")?
        || value::<bool>(&row, "public_execute")?
    {
        return Err(GitPullDispatchError::Rejected);
    }
    Ok(())
}

fn verify_privileges(client: &mut Client) -> Result<(), GitPullDispatchError> {
    let row = client
        .query_one(
            "SELECT \
                has_function_privilege('hwpx_agent.reconcile_git_mirror_pull_v1(uuid,uuid,character,uuid,uuid,uuid,character,uuid,bigint,character,uuid,bigint,character,text,character)','EXECUTE') AS reconcile_execute, \
                has_schema_privilege('hwpx_agent','CREATE') \
                    OR has_table_privilege('hwpx_agent.git_mirror_pull_observations','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.project_local_mirrors','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.branches','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.revisions','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.schema_versions','INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS excessive",
            &[],
        )
        .map_err(map_db_error)?;
    if !value::<bool>(&row, "reconcile_execute")? || value::<bool>(&row, "excessive")? {
        return Err(GitPullDispatchError::Rejected);
    }
    Ok(())
}

fn map_db_error(error: postgres::Error) -> GitPullDispatchError {
    let mapped = match error.code().map(postgres::error::SqlState::code) {
        Some("22023" | "23503" | "23505" | "23514" | "42501" | "P0002") => {
            GitPullDispatchError::Rejected
        }
        _ => GitPullDispatchError::Unavailable,
    };
    drop(error);
    mapped
}

fn map_git_error(error: GitMirrorEffectError) -> GitPullDispatchError {
    match error {
        GitMirrorEffectError::ConfigurationRejected
        | GitMirrorEffectError::RequestRejected
        | GitMirrorEffectError::PlanRejected
        | GitMirrorEffectError::GitStateRejected
        | GitMirrorEffectError::ReferenceConflict => GitPullDispatchError::Rejected,
        GitMirrorEffectError::GitUnavailable => GitPullDispatchError::Unavailable,
    }
}

fn value<T: FromSqlOwned>(row: &Row, column: &str) -> Result<T, GitPullDispatchError> {
    row.try_get(column).map_err(map_db_error)
}

fn to_i64(value: u64) -> Result<i64, GitPullDispatchError> {
    i64::try_from(value).map_err(|_| GitPullDispatchError::Rejected)
}

fn revision_public(value: Uuid) -> Result<String, GitPullDispatchError> {
    RevisionId::parse(&format!("rev_{}", value.simple()))
        .map(revision_service::RevisionId::public_id)
        .map_err(|_| GitPullDispatchError::Unavailable)
}

fn valid_head(revision_id: Option<&str>, generation: u64) -> bool {
    revision_id.is_none() == (generation == 0)
        && revision_id.is_none_or(|value| RevisionId::parse(value).is_ok())
}

fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn valid_digest(value: &str) -> bool {
    value.len() == 64
        && value != "0".repeat(64)
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

#[cfg(test)]
mod tests {
    use std::sync::atomic::{AtomicUsize, Ordering};

    use auth_middleware::{AuthRegistryLimits, PrincipalGrant, TenantRole};
    use base64::Engine as _;
    use base64::engine::general_purpose::URL_SAFE_NO_PAD;
    use hmac::{Hmac, Mac as _};
    use serde_json::{Value, json};

    use super::*;

    type HmacSha256 = Hmac<Sha256>;

    const RESOURCE: &str = "https://mcp.hwpx-agent.example";
    const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
    const ISSUER: &str = "https://identity.hwpx-agent.example";
    const KEY_ID: &str = "local-key-01";
    const SECRET: &[u8] = b"0123456789abcdef0123456789abcdef";
    const NOW: u64 = 2_000_000_000;
    const PROJECT: &str = "prj_00000000000000000000000000000002";
    const BRANCH: &str = "brn_00000000000000000000000000000003";
    const MIRROR: &str = "mir_00000000000000000000000000000004";
    const REVISION: &str = "rev_00000000000000000000000000000005";

    #[derive(Debug)]
    struct RecordingCoordinator {
        calls: AtomicUsize,
        conflict: bool,
    }

    impl GitPullCoordinator for RecordingCoordinator {
        fn dispatch(
            &self,
            request: &GitPullDispatchRequest,
        ) -> Result<GitPullDispatchOutcome, GitPullDispatchError> {
            self.calls.fetch_add(1, Ordering::SeqCst);
            assert_eq!(request.project_id().public_id(), PROJECT);
            assert_eq!(request.branch_id().public_id(), BRANCH);
            assert_eq!(request.mirror_id().public_id(), MIRROR);
            assert_eq!(request.observed_generation(), 1);
            assert_eq!(request.observed_snapshot_sha256(), "a".repeat(64));
            if self.conflict {
                Ok(GitPullDispatchOutcome::Conflict {
                    revision_id: REVISION.to_owned(),
                    generation: 2,
                    replayed: false,
                })
            } else {
                Ok(GitPullDispatchOutcome::Succeeded {
                    revision_id: Some(REVISION.to_owned()),
                    generation: 1,
                    snapshot_sha256: request.observed_snapshot_sha256().to_owned(),
                    replayed: false,
                })
            }
        }
    }

    #[derive(Serialize)]
    struct Claims {
        iss: String,
        sub: String,
        aud: String,
        exp: u64,
        nbf: u64,
        iat: u64,
        jti: String,
        scope: String,
        token_kind: String,
        tenant_id: TenantId,
        service_id: String,
    }

    fn fixture(conflict: bool) -> (GitPullHost<RecordingCoordinator>, TenantId) {
        let tenant_id = TenantId::new(Uuid::from_u128(1)).unwrap_or_else(|error| panic!("{error}"));
        let mut authentication = AuthMiddleware::new(
            RESOURCE,
            METADATA,
            60,
            AuthRegistryLimits::product_maximums(),
        )
        .unwrap_or_else(|error| panic!("{error}"));
        authentication
            .register_local_hmac_key(ISSUER, KEY_ID, SECRET, NOW - 600, NOW + 7_200)
            .unwrap_or_else(|error| panic!("{error}"));
        authentication
            .register_service(
                ISSUER,
                "worker-01",
                PrincipalGrant::new(
                    tenant_id,
                    TenantRole::Worker,
                    [AuthScope::MirrorSync],
                    NOW - 600,
                    NOW + 7_200,
                )
                .unwrap_or_else(|error| panic!("{error}")),
            )
            .unwrap_or_else(|error| panic!("{error}"));
        (
            GitPullHost::new(
                authentication,
                RecordingCoordinator {
                    calls: AtomicUsize::new(0),
                    conflict,
                },
            ),
            tenant_id,
        )
    }

    fn header(tenant_id: TenantId, jti: &str) -> String {
        let claims = Claims {
            iss: ISSUER.to_owned(),
            sub: "worker-01".to_owned(),
            aud: RESOURCE.to_owned(),
            exp: NOW + 120,
            nbf: NOW - 10,
            iat: NOW - 10,
            jti: jti.to_owned(),
            scope: "mirror.sync".to_owned(),
            token_kind: "service".to_owned(),
            tenant_id,
            service_id: "worker-01".to_owned(),
        };
        format!("Bearer {}", sign(&claims))
    }

    fn request() -> Vec<u8> {
        serde_json::to_vec(&PullWireRequest {
            schema_version: REQUEST_SCHEMA.to_owned(),
            operation: "pull".to_owned(),
            project_id: PROJECT.to_owned(),
            branch_id: BRANCH.to_owned(),
            mirror_id: MIRROR.to_owned(),
            observed_head: PullWireHead {
                revision_id: Some(REVISION.to_owned()),
                generation: 1,
            },
            observed_snapshot_sha256: "a".repeat(64),
        })
        .unwrap_or_else(|error| panic!("{error}"))
    }

    fn sign(claims: &Claims) -> String {
        let header = json!({"alg": "HS256", "kid": KEY_ID, "typ": "hwpx-service+jwt"});
        let header = URL_SAFE_NO_PAD
            .encode(serde_json::to_vec(&header).unwrap_or_else(|error| panic!("{error}")));
        let claims = URL_SAFE_NO_PAD
            .encode(serde_json::to_vec(claims).unwrap_or_else(|error| panic!("{error}")));
        let input = format!("{header}.{claims}");
        let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(SECRET)
            .unwrap_or_else(|error| panic!("{error}"));
        signer.update(input.as_bytes());
        format!(
            "{input}.{}",
            URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
        )
    }

    #[test]
    fn canonical_pull_binds_snapshot_and_consumes_token_once() {
        let (host, tenant) = fixture(false);
        let request = request();
        let authorization = header(tenant, "pull-service-token-0001");
        let response = host
            .handle_pull(&authorization, &request, NOW)
            .unwrap_or_else(|error| panic!("{error}"));
        let value: Value =
            serde_json::from_slice(&response).unwrap_or_else(|error| panic!("{error}"));
        assert_eq!(value["schema_version"], RESPONSE_SCHEMA);
        assert_eq!(value["request_sha256"], digest(&request));
        assert_eq!(value["result"]["outcome"], "succeeded");
        assert_eq!(value["result"]["snapshot_sha256"], "a".repeat(64));
        assert_eq!(host.coordinator.calls.load(Ordering::SeqCst), 1);
        assert_eq!(
            host.handle_pull(&authorization, &request, NOW),
            Err(GitPullHostFailure::Rejected)
        );
        assert_eq!(host.coordinator.calls.load(Ordering::SeqCst), 1);
        let debug = format!("{host:?}");
        assert!(!debug.contains(PROJECT));
        assert!(!debug.contains(&"a".repeat(64)));
    }

    #[test]
    fn conflict_is_bound_and_alternate_requests_fail_closed() {
        let (host, tenant) = fixture(true);
        let response = host
            .handle_pull(&header(tenant, "pull-service-token-0002"), &request(), NOW)
            .unwrap_or_else(|error| panic!("{error}"));
        let value: Value =
            serde_json::from_slice(&response).unwrap_or_else(|error| panic!("{error}"));
        assert_eq!(value["result"]["outcome"], "conflict");
        assert_eq!(value["result"]["head"]["generation"], 2);

        for (index, malformed) in [
            serde_json::to_vec(&json!({
                "schema_version": "hwpx-agent.remote-sync-request/v3",
                "operation": "pull",
                "project_id": PROJECT,
                "branch_id": BRANCH,
                "mirror_id": MIRROR,
                "observed_head": {"revision_id": REVISION, "generation": 1},
                "observed_snapshot_sha256": "a".repeat(64)
            }))
            .unwrap_or_default(),
            serde_json::to_vec(&json!({
                "schema_version": REQUEST_SCHEMA,
                "operation": "pull",
                "project_id": PROJECT,
                "branch_id": BRANCH,
                "mirror_id": MIRROR,
                "observed_head": {"revision_id": REVISION, "generation": 1},
                "observed_snapshot_sha256": "0".repeat(64)
            }))
            .unwrap_or_default(),
            [request(), b" ".to_vec()].concat(),
        ]
        .into_iter()
        .enumerate()
        {
            assert_eq!(
                host.handle_pull(
                    &header(tenant, &format!("pull-malformed-token-{index:04}")),
                    &malformed,
                    NOW,
                ),
                Err(GitPullHostFailure::Rejected)
            );
        }
    }
}
