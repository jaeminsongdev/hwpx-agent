//! Authenticated, PostgreSQL-fenced coordinator for the exact local bare-Git mirror effect.
//!
//! The database stores the canonical Git plan before the ref CAS. A later process can acquire a
//! higher fencing token, observe the exact old/result/diverged state and finish without guessing.
//! This is a current-PC local component; remote-network transport and production custody are absent.

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

use crate::git_mirror::{
    GitMirrorEffectError, GitMirrorEffectHost, GitMirrorEffectObservation, GitMirrorPushInput,
    GitMirrorPushPlan,
};
use crate::postgres::LocalPostgresHistoryCheckpointConfig;

const REQUEST_SCHEMA: &str = "hwpx-agent.remote-sync-request/v3";
const RESPONSE_SCHEMA: &str = "hwpx-agent.remote-sync-response/v1";
const EFFECT_RECEIPT_SCHEMA: &str = "hwpx-agent.git-mirror-effect-receipt/v1";
const MAX_REQUEST_BYTES: usize = 16_384;
const MAX_TIMEOUT: Duration = Duration::from_mins(1);
const PUSH_NAMESPACE: Uuid = Uuid::from_u128(0xd637_192a_f765_5e4b_a2b3_0319_6421_2170);
const REVISION_NAMESPACE: Uuid = Uuid::from_u128(0x1274_c807_2f50_58a8_83e5_833a_d385_e23c);

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

const DURABLE_GIT_MIGRATIONS: [&[u8]; 17] = [
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
pub enum GitPushHostFailure {
    #[error("Git push host rejected the exchange")]
    Rejected,
    #[error("Git push host cannot determine the exchange outcome")]
    Unavailable,
}

impl GitPushHostFailure {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::Rejected => "GIT_PUSH_HOST_REJECTED",
            Self::Unavailable => "GIT_PUSH_HOST_UNAVAILABLE",
        }
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum GitPushDispatchError {
    #[error("Git push coordinator rejected the request")]
    Rejected,
    #[error("Git push coordinator outcome is unavailable")]
    Unavailable,
}

impl GitPushDispatchError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::Rejected => "GIT_PUSH_DISPATCH_REJECTED",
            Self::Unavailable => "GIT_PUSH_DISPATCH_UNAVAILABLE",
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum GitPushDispatchOutcome {
    Succeeded {
        revision_id: String,
        generation: u64,
        snapshot_sha256: String,
        replayed: bool,
    },
    Conflict {
        revision_id: Option<String>,
        generation: u64,
    },
    Rejected,
}

impl fmt::Debug for GitPushDispatchOutcome {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Succeeded {
                generation,
                replayed,
                ..
            } => formatter
                .debug_struct("GitPushDispatchOutcome::Succeeded")
                .field("generation", generation)
                .field("replayed", replayed)
                .field("identities", &"<redacted>")
                .finish(),
            Self::Conflict { generation, .. } => formatter
                .debug_struct("GitPushDispatchOutcome::Conflict")
                .field("generation", generation)
                .field("revision_id", &"<redacted>")
                .finish(),
            Self::Rejected => formatter.write_str("GitPushDispatchOutcome::Rejected"),
        }
    }
}

pub struct GitPushDispatchRequest {
    tenant_id: TenantId,
    subject: SubjectDigest,
    request_sha256: String,
    project_id: ProjectId,
    branch_id: BranchId,
    mirror_id: MirrorId,
    expected_revision_id: Option<RevisionId>,
    expected_generation: u64,
    snapshot_sha256: String,
    operation_plan_sha256: String,
    idempotency_key: String,
}

impl GitPushDispatchRequest {
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
    pub const fn expected_revision_id(&self) -> Option<RevisionId> {
        self.expected_revision_id
    }

    #[must_use]
    pub const fn expected_generation(&self) -> u64 {
        self.expected_generation
    }

    #[must_use]
    pub fn snapshot_sha256(&self) -> &str {
        &self.snapshot_sha256
    }

    #[must_use]
    pub fn operation_plan_sha256(&self) -> &str {
        &self.operation_plan_sha256
    }

    #[must_use]
    pub fn idempotency_key(&self) -> &str {
        &self.idempotency_key
    }
}

impl fmt::Debug for GitPushDispatchRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitPushDispatchRequest")
            .field("expected_generation", &self.expected_generation)
            .field("identities", &"<redacted>")
            .finish_non_exhaustive()
    }
}

pub trait GitPushCoordinator: fmt::Debug {
    /// Resolves one authenticated push using a database plan and one exact Git ref CAS.
    ///
    /// # Errors
    ///
    /// Returns unavailable for every uncertain database, lease or Git process outcome.
    fn dispatch(
        &self,
        request: &GitPushDispatchRequest,
    ) -> Result<GitPushDispatchOutcome, GitPushDispatchError>;
}

pub struct GitPushHost<C> {
    authentication: Mutex<AuthMiddleware>,
    coordinator: C,
}

impl<C> GitPushHost<C> {
    #[must_use]
    pub const fn new(authentication: AuthMiddleware, coordinator: C) -> Self {
        Self {
            authentication: Mutex::new(authentication),
            coordinator,
        }
    }
}

impl<C> fmt::Debug for GitPushHost<C> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GitPushHost")
            .field("authentication", &"<redacted>")
            .field("coordinator", &"<redacted>")
            .finish()
    }
}

impl<C: GitPushCoordinator> GitPushHost<C> {
    /// Authenticates and handles exactly one canonical private push request.
    ///
    /// # Errors
    ///
    /// Malformed/auth failures are rejected; uncertain coordinator outcomes are unavailable.
    pub fn handle_push(
        &self,
        authorization_header: &str,
        request_bytes: &[u8],
        now_unix_seconds: u64,
    ) -> Result<Vec<u8>, GitPushHostFailure> {
        if request_bytes.is_empty() || request_bytes.len() > MAX_REQUEST_BYTES {
            return Err(GitPushHostFailure::Rejected);
        }
        let auth = self
            .authentication
            .lock()
            .map_err(|_| GitPushHostFailure::Unavailable)?
            .authenticate_internal_service_once(
                authorization_header,
                now_unix_seconds,
                [AuthScope::MirrorSync],
            )
            .map_err(|_| GitPushHostFailure::Rejected)?;
        let parsed = parse_request(request_bytes, auth.tenant_id(), auth.subject())?;
        let outcome = match self.coordinator.dispatch(&parsed) {
            Ok(value) => value,
            Err(GitPushDispatchError::Rejected) => GitPushDispatchOutcome::Rejected,
            Err(GitPushDispatchError::Unavailable) => {
                return Err(GitPushHostFailure::Unavailable);
            }
        };
        let result = match outcome {
            GitPushDispatchOutcome::Succeeded {
                revision_id,
                generation,
                snapshot_sha256,
                ..
            } => PushWireResult::Succeeded {
                head: OwnedWireHead {
                    revision_id: Some(revision_id),
                    generation,
                },
                snapshot_sha256,
            },
            GitPushDispatchOutcome::Conflict {
                revision_id,
                generation,
            } => PushWireResult::Conflict {
                head: OwnedWireHead {
                    revision_id,
                    generation,
                },
            },
            GitPushDispatchOutcome::Rejected => PushWireResult::Rejected {},
        };
        serde_json::to_vec(&BoundPushResponse {
            schema_version: RESPONSE_SCHEMA,
            request_sha256: parsed.request_sha256(),
            result,
        })
        .map_err(|_| GitPushHostFailure::Unavailable)
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum GitPushServerFailure {
    #[error("Git push server configuration or frame was rejected")]
    Rejected,
    #[error("Git push server outcome is unavailable")]
    Unavailable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GitPushServeOutcome {
    Succeeded,
    Rejected,
    Unavailable,
}

pub struct LoopbackGitPushServer<C> {
    listener: TcpListener,
    host: GitPushHost<C>,
    io_timeout: Duration,
}

impl<C> fmt::Debug for LoopbackGitPushServer<C> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LoopbackGitPushServer")
            .field("local_addr", &self.listener.local_addr().ok())
            .field("host", &"<redacted>")
            .field("io_timeout", &self.io_timeout)
            .finish()
    }
}

impl<C> LoopbackGitPushServer<C> {
    /// Binds only an exact loopback endpoint with a bounded I/O timeout.
    ///
    /// # Errors
    ///
    /// Rejects non-loopback addresses and timeouts outside 1 ms..=60 s.
    pub fn bind(
        endpoint: SocketAddr,
        host: GitPushHost<C>,
        io_timeout: Duration,
    ) -> Result<Self, GitPushServerFailure> {
        if !endpoint.ip().is_loopback()
            || io_timeout < Duration::from_millis(1)
            || io_timeout > MAX_TIMEOUT
        {
            return Err(GitPushServerFailure::Rejected);
        }
        let listener =
            TcpListener::bind(endpoint).map_err(|_| GitPushServerFailure::Unavailable)?;
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
    pub fn local_addr(&self) -> Result<SocketAddr, GitPushServerFailure> {
        self.listener
            .local_addr()
            .map_err(|_| GitPushServerFailure::Unavailable)
    }
}

impl<C: GitPushCoordinator> LoopbackGitPushServer<C> {
    /// Accepts and resolves exactly one bounded framed request.
    ///
    /// # Errors
    ///
    /// Returns unavailable when accept or definitive response delivery is uncertain.
    pub fn serve_one_at(
        &self,
        now_unix_seconds: u64,
    ) -> Result<GitPushServeOutcome, GitPushServerFailure> {
        if now_unix_seconds == 0 {
            return Err(GitPushServerFailure::Rejected);
        }
        let (mut stream, peer) = self
            .listener
            .accept()
            .map_err(|_| GitPushServerFailure::Unavailable)?;
        if !peer.ip().is_loopback() {
            write_server_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
            return Ok(GitPushServeOutcome::Rejected);
        }
        stream
            .set_read_timeout(Some(self.io_timeout))
            .and_then(|()| stream.set_write_timeout(Some(self.io_timeout)))
            .map_err(|_| GitPushServerFailure::Unavailable)?;
        let framed = match read_request(&mut stream) {
            Ok(value) => value,
            Err(FrameError::Rejected) => {
                write_server_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                return Ok(GitPushServeOutcome::Rejected);
            }
            Err(FrameError::Unavailable) => {
                write_server_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                return Ok(GitPushServeOutcome::Unavailable);
            }
        };
        let mut trailing = [0_u8; 1];
        match stream.read(&mut trailing) {
            Ok(0) => {}
            Ok(_) => {
                write_server_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                return Ok(GitPushServeOutcome::Rejected);
            }
            Err(_) => {
                write_server_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                return Ok(GitPushServeOutcome::Unavailable);
            }
        }
        match self.host.handle_push(
            framed.authorization_header(),
            framed.payload(),
            now_unix_seconds,
        ) {
            Ok(payload) => {
                write_server_outcome(&mut stream, ResponseStatus::Succeeded, &payload)?;
                Ok(GitPushServeOutcome::Succeeded)
            }
            Err(GitPushHostFailure::Rejected) => {
                write_server_outcome(&mut stream, ResponseStatus::Rejected, &[])?;
                Ok(GitPushServeOutcome::Rejected)
            }
            Err(GitPushHostFailure::Unavailable) => {
                write_server_outcome(&mut stream, ResponseStatus::Unavailable, &[])?;
                Ok(GitPushServeOutcome::Unavailable)
            }
        }
    }
}

fn write_server_outcome(
    stream: &mut TcpStream,
    status: ResponseStatus,
    payload: &[u8],
) -> Result<(), GitPushServerFailure> {
    write_response(stream, status, payload).map_err(|_| GitPushServerFailure::Unavailable)?;
    stream
        .shutdown(Shutdown::Write)
        .map_err(|_| GitPushServerFailure::Unavailable)
}

pub struct LocalPostgresGitMirrorPushCoordinator {
    tenant_id: TenantId,
    subject: SubjectDigest,
    client: Mutex<Client>,
    git: GitMirrorEffectHost,
    lease_seconds: i32,
}

impl fmt::Debug for LocalPostgresGitMirrorPushCoordinator {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LocalPostgresGitMirrorPushCoordinator")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("client", &"<redacted>")
            .field("git", &"<redacted>")
            .field("lease_seconds", &self.lease_seconds)
            .finish()
    }
}

impl LocalPostgresGitMirrorPushCoordinator {
    /// Connects a tenant/subject-fixed least-privilege v17 database and exact local bare repository.
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
        lease_seconds: u64,
    ) -> Result<Self, GitPushDispatchError> {
        let lease_seconds = i32::try_from(lease_seconds)
            .ok()
            .filter(|value| (1..=300).contains(value))
            .ok_or(GitPushDispatchError::Rejected)?;
        let git = GitMirrorEffectHost::open(bare_repository, git_program)
            .map_err(|_| GitPushDispatchError::Rejected)?;
        let mut settings = Config::new();
        settings
            .host("127.0.0.1")
            .port(config.port)
            .dbname(&config.database)
            .user(&config.user)
            .password(config.password.as_bytes())
            .connect_timeout(Duration::from_secs(3))
            .application_name("hwpx-agent-local-durable-git-push")
            .options(
                "-c statement_timeout=5000 -c lock_timeout=1000 \
                 -c idle_in_transaction_session_timeout=5000 \
                 -c transaction_timeout=10000 -c search_path=pg_catalog",
            );
        let mut client = settings
            .connect(NoTls)
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        verify_database(&mut client)?;
        Ok(Self {
            tenant_id,
            subject,
            client: Mutex::new(client),
            git,
            lease_seconds,
        })
    }
}

impl GitPushCoordinator for LocalPostgresGitMirrorPushCoordinator {
    fn dispatch(
        &self,
        request: &GitPushDispatchRequest,
    ) -> Result<GitPushDispatchOutcome, GitPushDispatchError> {
        if request.tenant_id() != self.tenant_id || request.subject() != self.subject {
            return Err(GitPushDispatchError::Rejected);
        }
        let identities = DerivedIdentities::new(request)?;
        let execution_id = Uuid::new_v4();
        let inspection = self.inspect(request, &identities)?;
        match inspection.outcome.as_str() {
            "conflict" => return conflict_outcome(&inspection),
            "new" => {}
            "existing" => {
                let acquired = self.acquire(request, &identities, execution_id)?;
                return match acquired.outcome.as_str() {
                    "finalized" => success_from_acquired(&acquired, true),
                    "diverged" => Ok(GitPushDispatchOutcome::Rejected),
                    "acquired" => self.run_effect(
                        request,
                        &identities,
                        execution_id,
                        acquired.fencing_token,
                        inspection.expected_snapshot_sha256.as_deref(),
                        acquired
                            .plan_bytes
                            .as_deref()
                            .ok_or(GitPushDispatchError::Unavailable)?,
                    ),
                    _ => Err(GitPushDispatchError::Unavailable),
                };
            }
            _ => return Err(GitPushDispatchError::Unavailable),
        }
        let expected_snapshot = inspection
            .expected_snapshot_sha256
            .as_deref()
            .ok_or(GitPushDispatchError::Unavailable)?;
        let input = git_input(request, &identities, expected_snapshot)?;
        let plan = self
            .git
            .prepare_push(&input)
            .map_err(map_git_prepare_error)?;
        let plan_bytes = plan.encode().map_err(map_git_stored_error)?;
        let plan_sha256 = digest(&plan_bytes);
        let receipts =
            DerivedReceipts::new(request, &identities, &plan_sha256, plan.state_sha256());
        let fencing_token = self.store(
            request,
            &identities,
            execution_id,
            expected_snapshot,
            &plan,
            &plan_sha256,
            &plan_bytes,
            &receipts,
        )?;
        self.run_effect(
            request,
            &identities,
            execution_id,
            fencing_token,
            Some(expected_snapshot),
            &plan_bytes,
        )
    }
}

impl LocalPostgresGitMirrorPushCoordinator {
    fn inspect(
        &self,
        request: &GitPushDispatchRequest,
        identities: &DerivedIdentities,
    ) -> Result<Inspection, GitPushDispatchError> {
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        let mut transaction = serializable(&mut client)?;
        set_context(&mut transaction, request).map_err(|_| GitPushDispatchError::Unavailable)?;
        let row = transaction
            .query_one(
                "SELECT outcome,observed_revision_id,observed_generation,\
                        expected_snapshot_sha256::text,effect_state,git_plan_bytes,\
                        lease_execution_id,lease_fencing_token,lease_expires_at \
                 FROM hwpx_agent.inspect_git_mirror_push_v1(\
                    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                &[
                    &request.tenant_id().as_uuid(),
                    &request.project_id().as_uuid(),
                    &request.subject().hex(),
                    &request.branch_id().as_uuid(),
                    &request.mirror_id().as_uuid(),
                    &identities.push_id,
                    &request.request_sha256(),
                    &identities.idempotency_sha256,
                    &request.expected_revision_id().map(RevisionId::as_uuid),
                    &to_i64(request.expected_generation())?,
                    &identities.result_revision_id,
                    &request.snapshot_sha256(),
                    &request.operation_plan_sha256(),
                ],
            )
            .map_err(map_db_error)?;
        let inspection = Inspection {
            outcome: value(&row, "outcome")?,
            observed_revision_id: value(&row, "observed_revision_id")?,
            observed_generation: value(&row, "observed_generation")?,
            expected_snapshot_sha256: value(&row, "expected_snapshot_sha256")?,
        };
        transaction.commit().map_err(map_db_error)?;
        Ok(inspection)
    }

    #[allow(clippy::too_many_arguments)]
    fn store(
        &self,
        request: &GitPushDispatchRequest,
        identities: &DerivedIdentities,
        execution_id: Uuid,
        expected_snapshot: &str,
        plan: &GitMirrorPushPlan,
        plan_sha256: &str,
        plan_bytes: &[u8],
        receipts: &DerivedReceipts,
    ) -> Result<i64, GitPushDispatchError> {
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        let mut transaction = serializable(&mut client)?;
        set_context(&mut transaction, request).map_err(|_| GitPushDispatchError::Unavailable)?;
        let token: i64 = transaction
            .query_one(
                "SELECT hwpx_agent.store_git_mirror_push_plan_v1(\
                    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,\
                    $17,$18,$19,$20,$21,$22,$23,$24)",
                &[
                    &request.tenant_id().as_uuid(),
                    &request.project_id().as_uuid(),
                    &request.subject().hex(),
                    &request.branch_id().as_uuid(),
                    &request.mirror_id().as_uuid(),
                    &identities.push_id,
                    &request.request_sha256(),
                    &identities.idempotency_sha256,
                    &request.expected_revision_id().map(RevisionId::as_uuid),
                    &to_i64(request.expected_generation())?,
                    &expected_snapshot,
                    &identities.result_revision_id,
                    &request.snapshot_sha256(),
                    &request.operation_plan_sha256(),
                    &plan_sha256,
                    &plan_bytes,
                    &plan.expected_oid(),
                    &plan.result_oid(),
                    &plan.state_sha256(),
                    &receipts.validation_summary,
                    &receipts.transaction_receipt,
                    &receipts.commit_receipt,
                    &execution_id,
                    &self.lease_seconds,
                ],
            )
            .map_err(map_db_error)?
            .try_get(0)
            .map_err(map_db_error)?;
        if token != 1 {
            return Err(GitPushDispatchError::Unavailable);
        }
        transaction.commit().map_err(map_db_error)?;
        Ok(token)
    }

    fn acquire(
        &self,
        request: &GitPushDispatchRequest,
        identities: &DerivedIdentities,
        execution_id: Uuid,
    ) -> Result<Acquired, GitPushDispatchError> {
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        let mut transaction = serializable(&mut client)?;
        set_context(&mut transaction, request)?;
        let row = transaction
            .query_one(
                "SELECT outcome,git_plan_bytes,lease_fencing_token,result_revision_id,\
                        result_generation,result_snapshot_sha256::text \
                 FROM hwpx_agent.acquire_git_mirror_push_lease_v1(\
                    $1,$2,$3,$4,$5,$6,$7)",
                &[
                    &request.tenant_id().as_uuid(),
                    &request.project_id().as_uuid(),
                    &request.subject().hex(),
                    &identities.push_id,
                    &request.request_sha256(),
                    &execution_id,
                    &self.lease_seconds,
                ],
            )
            .map_err(map_db_error)?;
        let acquired = Acquired {
            outcome: value(&row, "outcome")?,
            plan_bytes: value(&row, "git_plan_bytes")?,
            fencing_token: value(&row, "lease_fencing_token")?,
            result_revision_id: value(&row, "result_revision_id")?,
            result_generation: value(&row, "result_generation")?,
            result_snapshot_sha256: value(&row, "result_snapshot_sha256")?,
        };
        transaction.commit().map_err(map_db_error)?;
        Ok(acquired)
    }

    fn run_effect(
        &self,
        request: &GitPushDispatchRequest,
        identities: &DerivedIdentities,
        execution_id: Uuid,
        fencing_token: i64,
        expected_snapshot: Option<&str>,
        plan_bytes: &[u8],
    ) -> Result<GitPushDispatchOutcome, GitPushDispatchError> {
        let expected_snapshot = expected_snapshot.ok_or(GitPushDispatchError::Unavailable)?;
        let input = git_input(request, identities, expected_snapshot)?;
        let plan = GitMirrorPushPlan::decode(plan_bytes).map_err(map_git_stored_error)?;
        let observation = self
            .git
            .observe_push(&input, &plan)
            .map_err(map_git_stored_error)?;
        match observation {
            GitMirrorEffectObservation::Diverged => {
                self.mark_diverged(request, identities, execution_id, fencing_token)?;
                return Ok(GitPushDispatchOutcome::Rejected);
            }
            GitMirrorEffectObservation::NoEffect => match self.git.execute_push(&input, &plan) {
                Ok(_) => {}
                Err(GitMirrorEffectError::ReferenceConflict) => {
                    return match self.git.observe_push(&input, &plan) {
                        Ok(GitMirrorEffectObservation::Committed) => self.finalize(
                            request,
                            identities,
                            execution_id,
                            fencing_token,
                            &plan,
                            true,
                        ),
                        Ok(GitMirrorEffectObservation::Diverged) => {
                            self.mark_diverged(request, identities, execution_id, fencing_token)?;
                            Ok(GitPushDispatchOutcome::Rejected)
                        }
                        Ok(GitMirrorEffectObservation::NoEffect) | Err(_) => {
                            Err(GitPushDispatchError::Unavailable)
                        }
                    };
                }
                Err(_) => return Err(GitPushDispatchError::Unavailable),
            },
            GitMirrorEffectObservation::Committed => {}
        }
        if self
            .git
            .observe_push(&input, &plan)
            .map_err(map_git_stored_error)?
            != GitMirrorEffectObservation::Committed
        {
            return Err(GitPushDispatchError::Unavailable);
        }
        self.finalize(
            request,
            identities,
            execution_id,
            fencing_token,
            &plan,
            observation == GitMirrorEffectObservation::Committed,
        )
    }

    fn mark_diverged(
        &self,
        request: &GitPushDispatchRequest,
        identities: &DerivedIdentities,
        execution_id: Uuid,
        fencing_token: i64,
    ) -> Result<(), GitPushDispatchError> {
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        let mut transaction =
            serializable(&mut client).map_err(|_| GitPushDispatchError::Unavailable)?;
        set_context(&mut transaction, request).map_err(|_| GitPushDispatchError::Unavailable)?;
        transaction
            .query_one(
                "SELECT hwpx_agent.mark_git_mirror_push_diverged_v1(\
                    $1,$2,$3,$4,$5,$6,$7)",
                &[
                    &request.tenant_id().as_uuid(),
                    &request.project_id().as_uuid(),
                    &request.subject().hex(),
                    &identities.push_id,
                    &request.request_sha256(),
                    &execution_id,
                    &fencing_token,
                ],
            )
            // Until the durable divergence transition commits, the caller must retain its replay
            // key even when the observed Git reference is definitively unrelated.
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        transaction
            .commit()
            .map_err(|_| GitPushDispatchError::Unavailable)
    }

    #[allow(clippy::too_many_arguments)]
    fn finalize(
        &self,
        request: &GitPushDispatchRequest,
        identities: &DerivedIdentities,
        execution_id: Uuid,
        fencing_token: i64,
        plan: &GitMirrorPushPlan,
        replayed_effect: bool,
    ) -> Result<GitPushDispatchOutcome, GitPushDispatchError> {
        let plan_bytes = plan.encode().map_err(map_git_stored_error)?;
        let plan_sha256 = digest(&plan_bytes);
        let effect_receipt = digest(
            &serde_json::to_vec(&EffectReceiptWire {
                schema_version: EFFECT_RECEIPT_SCHEMA,
                request_sha256: request.request_sha256(),
                git_plan_sha256: &plan_sha256,
                result_git_oid: plan.result_oid(),
                git_state_sha256: plan.state_sha256(),
                observation: "committed",
            })
            .map_err(|_| GitPushDispatchError::Unavailable)?,
        );
        let mut client = self
            .client
            .try_lock()
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        let mut transaction =
            serializable(&mut client).map_err(|_| GitPushDispatchError::Unavailable)?;
        set_context(&mut transaction, request).map_err(|_| GitPushDispatchError::Unavailable)?;
        let row = transaction
            .query_one(
                "SELECT outcome,revision_id,generation,snapshot_sha256::text \
                 FROM hwpx_agent.finalize_git_mirror_push_v1(\
                    $1,$2,$3,$4,$5,$6,$7,$8,$9)",
                &[
                    &request.tenant_id().as_uuid(),
                    &request.project_id().as_uuid(),
                    &request.subject().hex(),
                    &identities.push_id,
                    &request.request_sha256(),
                    &execution_id,
                    &fencing_token,
                    &plan_sha256,
                    &effect_receipt,
                ],
            )
            // The Git ref is known committed before this transaction begins. Any database
            // failure here is therefore an uncertain cross-system outcome, never a rejection.
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        let outcome: String =
            value(&row, "outcome").map_err(|_| GitPushDispatchError::Unavailable)?;
        let revision_id: Uuid =
            value(&row, "revision_id").map_err(|_| GitPushDispatchError::Unavailable)?;
        let generation: i64 =
            value(&row, "generation").map_err(|_| GitPushDispatchError::Unavailable)?;
        let snapshot_sha256: String =
            value(&row, "snapshot_sha256").map_err(|_| GitPushDispatchError::Unavailable)?;
        if !matches!(outcome.as_str(), "committed" | "replayed")
            || revision_id != identities.result_revision_id
            || generation != to_i64(request.expected_generation())? + 1
            || snapshot_sha256 != request.snapshot_sha256()
        {
            return Err(GitPushDispatchError::Unavailable);
        }
        transaction
            .commit()
            .map_err(|_| GitPushDispatchError::Unavailable)?;
        Ok(GitPushDispatchOutcome::Succeeded {
            revision_id: identities.result_revision.public_id(),
            generation: u64::try_from(generation).map_err(|_| GitPushDispatchError::Unavailable)?,
            snapshot_sha256,
            replayed: replayed_effect || outcome == "replayed",
        })
    }
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct PushWireRequest {
    schema_version: String,
    operation: String,
    project_id: String,
    branch_id: String,
    mirror_id: String,
    expected_head: PushWireHead,
    snapshot_sha256: String,
    operation_plan_sha256: String,
    idempotency_key: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct PushWireHead {
    revision_id: Option<String>,
    generation: u64,
}

#[derive(Serialize)]
struct BoundPushResponse<'a> {
    schema_version: &'static str,
    request_sha256: &'a str,
    result: PushWireResult,
}

#[derive(Serialize)]
#[serde(tag = "outcome", rename_all = "snake_case")]
enum PushWireResult {
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

#[derive(Serialize)]
struct EffectReceiptWire<'a> {
    schema_version: &'static str,
    request_sha256: &'a str,
    git_plan_sha256: &'a str,
    result_git_oid: &'a str,
    git_state_sha256: &'a str,
    observation: &'static str,
}

struct Inspection {
    outcome: String,
    observed_revision_id: Option<Uuid>,
    observed_generation: i64,
    expected_snapshot_sha256: Option<String>,
}

struct Acquired {
    outcome: String,
    plan_bytes: Option<Vec<u8>>,
    fencing_token: i64,
    result_revision_id: Uuid,
    result_generation: i64,
    result_snapshot_sha256: String,
}

struct DerivedIdentities {
    push_id: Uuid,
    result_revision_id: Uuid,
    result_revision: RevisionId,
    idempotency_sha256: String,
}

impl DerivedIdentities {
    fn new(request: &GitPushDispatchRequest) -> Result<Self, GitPushDispatchError> {
        let idempotency_sha256 = digest(request.idempotency_key().as_bytes());
        let mut name = Vec::with_capacity(16 * 3 + 64 + 3);
        for bytes in [
            request.tenant_id().as_uuid().as_bytes(),
            request.project_id().as_uuid().as_bytes(),
            request.mirror_id().as_uuid().as_bytes(),
        ] {
            name.extend_from_slice(bytes);
            name.push(0);
        }
        name.extend_from_slice(idempotency_sha256.as_bytes());
        let push_id = Uuid::new_v5(&PUSH_NAMESPACE, &name);
        let result_revision_id = Uuid::new_v5(&REVISION_NAMESPACE, push_id.as_bytes());
        let result_revision = revision_from_uuid(result_revision_id)?;
        Ok(Self {
            push_id,
            result_revision_id,
            result_revision,
            idempotency_sha256,
        })
    }
}

struct DerivedReceipts {
    validation_summary: String,
    transaction_receipt: String,
    commit_receipt: String,
}

impl DerivedReceipts {
    fn new(
        request: &GitPushDispatchRequest,
        identities: &DerivedIdentities,
        plan_sha256: &str,
        state_sha256: &str,
    ) -> Self {
        let bound = |domain: &[u8]| {
            let mut hasher = Sha256::new();
            hasher.update(domain);
            hasher.update([0]);
            hasher.update(request.request_sha256().as_bytes());
            hasher.update([0]);
            hasher.update(identities.push_id.as_bytes());
            hasher.update([0]);
            hasher.update(plan_sha256.as_bytes());
            hasher.update([0]);
            hasher.update(state_sha256.as_bytes());
            hex::encode(hasher.finalize())
        };
        Self {
            validation_summary: bound(b"hwpx-agent.git-push-validation/v1"),
            transaction_receipt: bound(b"hwpx-agent.git-push-transaction/v1"),
            commit_receipt: bound(b"hwpx-agent.git-push-commit/v1"),
        }
    }
}

fn parse_request(
    bytes: &[u8],
    tenant_id: TenantId,
    subject: SubjectDigest,
) -> Result<GitPushDispatchRequest, GitPushHostFailure> {
    let wire: PushWireRequest =
        serde_json::from_slice(bytes).map_err(|_| GitPushHostFailure::Rejected)?;
    if serde_json::to_vec(&wire).map_err(|_| GitPushHostFailure::Unavailable)? != bytes
        || wire.schema_version != REQUEST_SCHEMA
        || wire.operation != "push"
        || !valid_digest(&wire.snapshot_sha256)
        || !valid_digest(&wire.operation_plan_sha256)
        || !valid_idempotency_key(&wire.idempotency_key)
        || wire.expected_head.revision_id.is_none() != (wire.expected_head.generation == 0)
    {
        return Err(GitPushHostFailure::Rejected);
    }
    let project_id =
        ProjectId::parse(&wire.project_id).map_err(|_| GitPushHostFailure::Rejected)?;
    let branch_id = BranchId::parse(&wire.branch_id).map_err(|_| GitPushHostFailure::Rejected)?;
    let mirror_id =
        MirrorId::parse_public(&wire.mirror_id).map_err(|_| GitPushHostFailure::Rejected)?;
    let expected_revision_id = wire
        .expected_head
        .revision_id
        .as_deref()
        .map(RevisionId::parse)
        .transpose()
        .map_err(|_| GitPushHostFailure::Rejected)?;
    Ok(GitPushDispatchRequest {
        tenant_id,
        subject,
        request_sha256: digest(bytes),
        project_id,
        branch_id,
        mirror_id,
        expected_revision_id,
        expected_generation: wire.expected_head.generation,
        snapshot_sha256: wire.snapshot_sha256,
        operation_plan_sha256: wire.operation_plan_sha256,
        idempotency_key: wire.idempotency_key,
    })
}

fn git_input(
    request: &GitPushDispatchRequest,
    identities: &DerivedIdentities,
    expected_snapshot_sha256: &str,
) -> Result<GitMirrorPushInput, GitPushDispatchError> {
    GitMirrorPushInput::new(
        request.project_id().public_id(),
        request.branch_id().public_id(),
        request.expected_revision_id().map(RevisionId::public_id),
        request.expected_generation(),
        (request.expected_generation() > 0).then(|| expected_snapshot_sha256.to_owned()),
        identities.result_revision.public_id(),
        request.snapshot_sha256().to_owned(),
        request.operation_plan_sha256().to_owned(),
        request.request_sha256().to_owned(),
    )
    .map_err(|_| GitPushDispatchError::Rejected)
}

fn conflict_outcome(
    inspection: &Inspection,
) -> Result<GitPushDispatchOutcome, GitPushDispatchError> {
    let generation = u64::try_from(inspection.observed_generation)
        .map_err(|_| GitPushDispatchError::Unavailable)?;
    let revision_id = inspection
        .observed_revision_id
        .map(revision_from_uuid)
        .transpose()
        .map_err(|_| GitPushDispatchError::Unavailable)?
        .map(RevisionId::public_id);
    if revision_id.is_none() != (generation == 0) {
        return Err(GitPushDispatchError::Unavailable);
    }
    Ok(GitPushDispatchOutcome::Conflict {
        revision_id,
        generation,
    })
}

fn success_from_acquired(
    acquired: &Acquired,
    replayed: bool,
) -> Result<GitPushDispatchOutcome, GitPushDispatchError> {
    let revision = revision_from_uuid(acquired.result_revision_id)?;
    if acquired.result_generation <= 0 || !valid_digest(&acquired.result_snapshot_sha256) {
        return Err(GitPushDispatchError::Unavailable);
    }
    Ok(GitPushDispatchOutcome::Succeeded {
        revision_id: revision.public_id(),
        generation: u64::try_from(acquired.result_generation)
            .map_err(|_| GitPushDispatchError::Unavailable)?,
        snapshot_sha256: acquired.result_snapshot_sha256.clone(),
        replayed,
    })
}

fn serializable(client: &mut Client) -> Result<Transaction<'_>, GitPushDispatchError> {
    client
        .build_transaction()
        .isolation_level(IsolationLevel::Serializable)
        .start()
        .map_err(map_db_error)
}

fn set_context(
    transaction: &mut Transaction<'_>,
    request: &GitPushDispatchRequest,
) -> Result<(), GitPushDispatchError> {
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

fn verify_database(client: &mut Client) -> Result<(), GitPushDispatchError> {
    verify_role(client)?;
    verify_migrations(client)?;
    verify_policies_and_triggers(client)?;
    verify_function_security(client)?;
    verify_privileges(client)
}

fn verify_role(client: &mut Client) -> Result<(), GitPushDispatchError> {
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
            return Err(GitPushDispatchError::Rejected);
        }
    }
    Ok(())
}

fn verify_migrations(client: &mut Client) -> Result<(), GitPushDispatchError> {
    let rows = client
        .query(
            "SELECT version,migration_sha256::text FROM hwpx_agent.schema_versions \
             ORDER BY version LIMIT 17",
            &[],
        )
        .map_err(map_db_error)?;
    if rows.len() != DURABLE_GIT_MIGRATIONS.len() {
        return Err(GitPushDispatchError::Rejected);
    }
    for (index, row) in rows.iter().enumerate() {
        if value::<i64>(row, "version")?
            != i64::try_from(index + 1).map_err(|_| GitPushDispatchError::Rejected)?
            || value::<String>(row, "migration_sha256")?
                != hex::encode(Sha256::digest(DURABLE_GIT_MIGRATIONS[index]))
        {
            return Err(GitPushDispatchError::Rejected);
        }
    }
    Ok(())
}

fn verify_policies_and_triggers(client: &mut Client) -> Result<(), GitPushDispatchError> {
    let rows = client
        .query(
            "SELECT class.relname,class.relrowsecurity,class.relforcerowsecurity, \
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
             WHERE namespace.nspname='hwpx_agent' AND class.relname IN ( \
                'projects','project_acl','branches','project_local_mirrors','artifacts', \
                'revisions','revision_parents','revision_graph_seals', \
                'revision_commit_receipts','audit_events','git_mirror_push_effects')",
            &[],
        )
        .map_err(map_db_error)?;
    if rows.len() != 11 {
        return Err(GitPushDispatchError::Rejected);
    }
    for row in rows {
        if !value::<bool>(&row, "relrowsecurity")?
            || !value::<bool>(&row, "relforcerowsecurity")?
            || value::<bool>(&row, "owner_role")?
            || value::<i64>(&row, "policy_match")? != 1
        {
            return Err(GitPushDispatchError::Rejected);
        }
    }
    let trigger = client
        .query_one(
            "SELECT count(*) AS exact_count FROM pg_trigger trigger \
             JOIN pg_class class ON class.oid=trigger.tgrelid \
             JOIN pg_namespace namespace ON namespace.oid=class.relnamespace \
             WHERE namespace.nspname='hwpx_agent' AND trigger.tgenabled='O' \
               AND ((class.relname='branches' \
                    AND trigger.tgname='branches_git_mirror_push_guard') \
                 OR (class.relname='git_mirror_push_effects' \
                    AND trigger.tgname='git_mirror_push_effect_guard'))",
            &[],
        )
        .map_err(map_db_error)?;
    if value::<i64>(&trigger, "exact_count")? != 2 {
        return Err(GitPushDispatchError::Rejected);
    }
    Ok(())
}

fn verify_function_security(client: &mut Client) -> Result<(), GitPushDispatchError> {
    let row = client
        .query_one(
            "WITH expected(function_oid) AS (VALUES \
                ('hwpx_agent.inspect_git_mirror_push_v1(uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint,uuid,character,character)'::regprocedure), \
                ('hwpx_agent.store_git_mirror_push_plan_v1(uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint,character,uuid,character,character,character,bytea,text,text,character,character,character,character,uuid,integer)'::regprocedure), \
                ('hwpx_agent.acquire_git_mirror_push_lease_v1(uuid,uuid,character,uuid,character,uuid,integer)'::regprocedure), \
                ('hwpx_agent.mark_git_mirror_push_diverged_v1(uuid,uuid,character,uuid,character,uuid,bigint)'::regprocedure), \
                ('hwpx_agent.finalize_git_mirror_push_v1(uuid,uuid,character,uuid,character,uuid,bigint,character,character)'::regprocedure)) \
             SELECT count(*) AS exact_count, bool_and(proc.prosecdef) AS security_definer, \
                bool_and(COALESCE(proc.proconfig= \
                    ARRAY['search_path=pg_catalog, hwpx_agent']::text[],false)) \
                    AS search_path_fixed, \
                bool_or(pg_has_role(proc.proowner,'USAGE') OR pg_has_role(proc.proowner,'SET')) \
                    AS owner_role, \
                bool_or(EXISTS (SELECT 1 FROM \
                    aclexplode(COALESCE(proc.proacl,acldefault('f',proc.proowner))) AS acl \
                    WHERE acl.grantee=0 AND acl.privilege_type='EXECUTE')) AS public_execute \
             FROM expected JOIN pg_proc proc ON proc.oid=expected.function_oid",
            &[],
        )
        .map_err(map_db_error)?;
    if value::<i64>(&row, "exact_count")? != 5
        || !value::<bool>(&row, "security_definer")?
        || !value::<bool>(&row, "search_path_fixed")?
        || value::<bool>(&row, "owner_role")?
        || value::<bool>(&row, "public_execute")?
    {
        return Err(GitPushDispatchError::Rejected);
    }
    Ok(())
}

fn verify_privileges(client: &mut Client) -> Result<(), GitPushDispatchError> {
    let row = client
        .query_one(
            "SELECT \
                has_function_privilege('hwpx_agent.inspect_git_mirror_push_v1(uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint,uuid,character,character)','EXECUTE') AS inspect_execute, \
                has_function_privilege('hwpx_agent.store_git_mirror_push_plan_v1(uuid,uuid,character,uuid,uuid,uuid,character,character,uuid,bigint,character,uuid,character,character,character,bytea,text,text,character,character,character,character,uuid,integer)','EXECUTE') AS store_execute, \
                has_function_privilege('hwpx_agent.acquire_git_mirror_push_lease_v1(uuid,uuid,character,uuid,character,uuid,integer)','EXECUTE') AS acquire_execute, \
                has_function_privilege('hwpx_agent.mark_git_mirror_push_diverged_v1(uuid,uuid,character,uuid,character,uuid,bigint)','EXECUTE') AS diverged_execute, \
                has_function_privilege('hwpx_agent.finalize_git_mirror_push_v1(uuid,uuid,character,uuid,character,uuid,bigint,character,character)','EXECUTE') AS finalize_execute, \
                has_function_privilege('hwpx_agent.commit_revision_cas(uuid,uuid,uuid,character,uuid,uuid,bigint,uuid,uuid[],uuid,uuid,uuid,character,text,character,character,character,character)','EXECUTE') \
                    OR has_function_privilege('hwpx_agent.begin_local_mirror_push_v1(uuid,uuid,character,uuid,uuid,uuid,integer)','EXECUTE') \
                    OR has_function_privilege('hwpx_agent.complete_local_mirror_push_v1(uuid,uuid,character,uuid,uuid,uuid)','EXECUTE') AS legacy_execute, \
                has_schema_privilege('hwpx_agent','CREATE') \
                    OR has_table_privilege('hwpx_agent.git_mirror_push_effects','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.project_local_mirrors','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.branches','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.revisions','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.revision_commit_receipts','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') \
                    OR has_table_privilege('hwpx_agent.schema_versions','INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS excessive",
            &[],
        )
        .map_err(map_db_error)?;
    for required in [
        "inspect_execute",
        "store_execute",
        "acquire_execute",
        "diverged_execute",
        "finalize_execute",
    ] {
        if !value::<bool>(&row, required)? {
            return Err(GitPushDispatchError::Rejected);
        }
    }
    if value::<bool>(&row, "legacy_execute")? || value::<bool>(&row, "excessive")? {
        return Err(GitPushDispatchError::Rejected);
    }
    Ok(())
}

fn map_db_error(error: postgres::Error) -> GitPushDispatchError {
    let mapped = match error.code().map(postgres::error::SqlState::code) {
        Some("22023" | "23503" | "23505" | "23514" | "42501" | "P0002" | "P1702") => {
            GitPushDispatchError::Rejected
        }
        _ => GitPushDispatchError::Unavailable,
    };
    drop(error);
    mapped
}

fn map_git_prepare_error(error: GitMirrorEffectError) -> GitPushDispatchError {
    match error {
        GitMirrorEffectError::ConfigurationRejected
        | GitMirrorEffectError::RequestRejected
        | GitMirrorEffectError::GitStateRejected
        | GitMirrorEffectError::ReferenceConflict => GitPushDispatchError::Rejected,
        GitMirrorEffectError::PlanRejected | GitMirrorEffectError::GitUnavailable => {
            GitPushDispatchError::Unavailable
        }
    }
}

const fn map_git_stored_error(_error: GitMirrorEffectError) -> GitPushDispatchError {
    GitPushDispatchError::Unavailable
}

fn value<T: FromSqlOwned>(row: &Row, column: &str) -> Result<T, GitPushDispatchError> {
    row.try_get(column).map_err(map_db_error)
}

fn to_i64(value: u64) -> Result<i64, GitPushDispatchError> {
    i64::try_from(value).map_err(|_| GitPushDispatchError::Rejected)
}

fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn revision_from_uuid(value: Uuid) -> Result<RevisionId, GitPushDispatchError> {
    RevisionId::parse(&format!("rev_{}", value.simple()))
        .map_err(|_| GitPushDispatchError::Unavailable)
}

fn valid_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn valid_idempotency_key(value: &str) -> bool {
    (12..=120).contains(&value.len())
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}

#[cfg(test)]
mod tests {
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::thread;

    use auth_middleware::{AuthRegistryLimits, PrincipalGrant, TenantRole};
    use base64::Engine as _;
    use base64::engine::general_purpose::URL_SAFE_NO_PAD;
    use hmac::{Hmac, Mac as _};
    use remote_sync_wire::{ResponseStatus, read_response, write_request};
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
    const RESULT_REVISION: &str = "rev_00000000000000000000000000000006";

    #[derive(Clone, Copy, Debug)]
    enum Mode {
        Success,
        Conflict,
        Rejected,
        Unavailable,
    }

    #[derive(Debug)]
    struct RecordingCoordinator {
        calls: AtomicUsize,
        mode: Mode,
    }

    impl RecordingCoordinator {
        const fn new(mode: Mode) -> Self {
            Self {
                calls: AtomicUsize::new(0),
                mode,
            }
        }
    }

    impl GitPushCoordinator for RecordingCoordinator {
        fn dispatch(
            &self,
            request: &GitPushDispatchRequest,
        ) -> Result<GitPushDispatchOutcome, GitPushDispatchError> {
            self.calls.fetch_add(1, Ordering::SeqCst);
            assert_eq!(request.project_id().public_id(), PROJECT);
            assert_eq!(request.branch_id().public_id(), BRANCH);
            assert_eq!(request.mirror_id().public_id(), MIRROR);
            assert_eq!(request.expected_generation(), 1);
            assert_eq!(request.snapshot_sha256(), "a".repeat(64));
            assert_eq!(request.operation_plan_sha256(), "b".repeat(64));
            assert_eq!(request.idempotency_key(), "push-request-0001");
            match self.mode {
                Mode::Success => Ok(GitPushDispatchOutcome::Succeeded {
                    revision_id: RESULT_REVISION.to_owned(),
                    generation: 2,
                    snapshot_sha256: request.snapshot_sha256().to_owned(),
                    replayed: false,
                }),
                Mode::Conflict => Ok(GitPushDispatchOutcome::Conflict {
                    revision_id: Some(REVISION.to_owned()),
                    generation: 1,
                }),
                Mode::Rejected => Ok(GitPushDispatchOutcome::Rejected),
                Mode::Unavailable => Err(GitPushDispatchError::Unavailable),
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

    struct Fixture {
        host: GitPushHost<RecordingCoordinator>,
        tenant_id: TenantId,
    }

    impl Fixture {
        fn new(mode: Mode) -> Self {
            let tenant_id =
                TenantId::new(Uuid::from_u128(1)).unwrap_or_else(|error| panic!("tenant: {error}"));
            let mut authentication = AuthMiddleware::new(
                RESOURCE,
                METADATA,
                60,
                AuthRegistryLimits::product_maximums(),
            )
            .unwrap_or_else(|error| panic!("auth: {error}"));
            authentication
                .register_local_hmac_key(ISSUER, KEY_ID, SECRET, NOW - 600, NOW + 7_200)
                .unwrap_or_else(|error| panic!("key: {error}"));
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
                    .unwrap_or_else(|error| panic!("grant: {error}")),
                )
                .unwrap_or_else(|error| panic!("service: {error}"));
            Self {
                host: GitPushHost::new(authentication, RecordingCoordinator::new(mode)),
                tenant_id,
            }
        }

        fn header(&self, jti: &str) -> String {
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
                tenant_id: self.tenant_id,
                service_id: "worker-01".to_owned(),
            };
            format!("Bearer {}", sign(&claims))
        }

        fn request() -> Vec<u8> {
            serde_json::to_vec(&PushWireRequest {
                schema_version: REQUEST_SCHEMA.to_owned(),
                operation: "push".to_owned(),
                project_id: PROJECT.to_owned(),
                branch_id: BRANCH.to_owned(),
                mirror_id: MIRROR.to_owned(),
                expected_head: PushWireHead {
                    revision_id: Some(REVISION.to_owned()),
                    generation: 1,
                },
                snapshot_sha256: "a".repeat(64),
                operation_plan_sha256: "b".repeat(64),
                idempotency_key: "push-request-0001".to_owned(),
            })
            .unwrap_or_else(|error| panic!("request: {error}"))
        }
    }

    fn sign(claims: &Claims) -> String {
        let header = json!({"alg": "HS256", "kid": KEY_ID, "typ": "hwpx-service+jwt"});
        let header = URL_SAFE_NO_PAD
            .encode(serde_json::to_vec(&header).unwrap_or_else(|error| panic!("header: {error}")));
        let claims = URL_SAFE_NO_PAD
            .encode(serde_json::to_vec(claims).unwrap_or_else(|error| panic!("claims: {error}")));
        let input = format!("{header}.{claims}");
        let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(SECRET)
            .unwrap_or_else(|error| panic!("signer: {error}"));
        signer.update(input.as_bytes());
        format!(
            "{input}.{}",
            URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
        )
    }

    #[test]
    fn canonical_authenticated_push_is_bound_and_single_use() {
        let fixture = Fixture::new(Mode::Success);
        let request = Fixture::request();
        let header = fixture.header("push-service-token-0001");
        let response = fixture
            .host
            .handle_push(&header, &request, NOW)
            .unwrap_or_else(|error| panic!("handle: {error}"));
        let value: Value =
            serde_json::from_slice(&response).unwrap_or_else(|error| panic!("response: {error}"));
        assert_eq!(value["schema_version"], RESPONSE_SCHEMA);
        assert_eq!(value["request_sha256"], digest(&request));
        assert_eq!(value["result"]["outcome"], "succeeded");
        assert_eq!(value["result"]["head"]["revision_id"], RESULT_REVISION);
        assert_eq!(value["result"]["head"]["generation"], 2);
        assert_eq!(fixture.host.coordinator.calls.load(Ordering::SeqCst), 1);
        assert_eq!(
            fixture.host.handle_push(&header, &request, NOW),
            Err(GitPushHostFailure::Rejected)
        );
        assert_eq!(fixture.host.coordinator.calls.load(Ordering::SeqCst), 1);
        for debug in [
            format!("{:?}", fixture.host),
            format!(
                "{:?}",
                GitPushDispatchOutcome::Succeeded {
                    revision_id: RESULT_REVISION.to_owned(),
                    generation: 2,
                    snapshot_sha256: "a".repeat(64),
                    replayed: false,
                }
            ),
        ] {
            assert!(!debug.contains(PROJECT));
            assert!(!debug.contains(RESULT_REVISION));
            assert!(!debug.contains(&"a".repeat(64)));
        }
    }

    #[test]
    fn malformed_noncanonical_and_dispatch_outcomes_fail_closed() {
        let malformed = Fixture::new(Mode::Success);
        let mut whitespace = Fixture::request();
        whitespace.push(b'\n');
        assert_eq!(
            malformed.host.handle_push(
                &malformed.header("push-service-token-0002"),
                &whitespace,
                NOW,
            ),
            Err(GitPushHostFailure::Rejected)
        );
        assert_eq!(malformed.host.coordinator.calls.load(Ordering::SeqCst), 0);

        for (mode, expected) in [
            (Mode::Conflict, Some("conflict")),
            (Mode::Rejected, Some("rejected")),
            (Mode::Unavailable, None),
        ] {
            let fixture = Fixture::new(mode);
            let result = fixture.host.handle_push(
                &fixture.header(&format!("push-service-token-{mode:?}")),
                &Fixture::request(),
                NOW,
            );
            if let Some(expected) = expected {
                let response = result.unwrap_or_else(|error| panic!("outcome: {error}"));
                let value: Value = serde_json::from_slice(&response)
                    .unwrap_or_else(|error| panic!("response: {error}"));
                assert_eq!(value["result"]["outcome"], expected);
            } else {
                assert_eq!(result, Err(GitPushHostFailure::Unavailable));
            }
        }
    }

    #[test]
    fn loopback_server_crosses_the_exact_frame_boundary() {
        let fixture = Fixture::new(Mode::Success);
        let header = fixture.header("push-loopback-token-0001");
        let server = LoopbackGitPushServer::bind(
            "127.0.0.1:0"
                .parse()
                .unwrap_or_else(|error| panic!("endpoint: {error}")),
            fixture.host,
            Duration::from_secs(2),
        )
        .unwrap_or_else(|error| panic!("bind: {error}"));
        let endpoint = server
            .local_addr()
            .unwrap_or_else(|error| panic!("address: {error}"));
        let worker = thread::spawn(move || server.serve_one_at(NOW));
        let mut client =
            TcpStream::connect(endpoint).unwrap_or_else(|error| panic!("connect: {error}"));
        client
            .set_read_timeout(Some(Duration::from_secs(2)))
            .unwrap_or_else(|error| panic!("timeout: {error}"));
        write_request(&mut client, &header, &Fixture::request())
            .unwrap_or_else(|error| panic!("write: {error}"));
        client
            .shutdown(Shutdown::Write)
            .unwrap_or_else(|error| panic!("shutdown: {error}"));
        let response =
            read_response(&mut client).unwrap_or_else(|error| panic!("response frame: {error}"));
        assert_eq!(response.status(), ResponseStatus::Succeeded);
        let value: Value = serde_json::from_slice(response.payload())
            .unwrap_or_else(|error| panic!("response JSON: {error}"));
        assert_eq!(value["result"]["outcome"], "succeeded");
        assert_eq!(
            worker.join().unwrap_or_else(|_| panic!("server thread")),
            Ok(GitPushServeOutcome::Succeeded)
        );

        let invalid = Fixture::new(Mode::Success);
        assert!(matches!(
            LoopbackGitPushServer::bind(
                "0.0.0.0:0"
                    .parse()
                    .unwrap_or_else(|error| panic!("endpoint: {error}")),
                invalid.host,
                Duration::from_secs(2),
            ),
            Err(GitPushServerFailure::Rejected)
        ));
    }
}
