//! Authenticated server-side checkpoint boundary for the P17 private sync protocol.
//!
//! This crate is a bounded local host component. It does not provide a network listener, credential
//! issuer, production identity provider or concrete P15 service implementation.

#![forbid(unsafe_code)]

use std::fmt;
use std::sync::Mutex;

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::{AuthMiddleware, AuthScope};
use history_service::{
    CheckpointId, CheckpointLabel, CheckpointNote, CheckpointOutcome as HistoryCheckpointOutcome,
    CheckpointRequest as HistoryCheckpointRequest, HistoryError, HistoryRepository,
    HistoryRequestContext, HistoryService, RequestId,
};
use local_sync::{
    CheckpointServiceArguments, CheckpointServiceBinding, CheckpointServiceContext,
    decode_checkpoint_to_service,
};
use retention_sync_service::{
    MirrorCheckpointDecision, MirrorId, RemoteHead, RequestContext, RetentionSyncError,
    RetentionSyncService,
};
use revision_service::{BranchId, ProjectId, RevisionId};
use serde::Serialize;
use thiserror::Error;
use uuid::Uuid;

mod postgres;
mod socket;

pub use postgres::{
    LocalPostgresAtomicMirrorCheckpointDispatcher, LocalPostgresHistoryCheckpointConfig,
    LocalPostgresHistoryCheckpointDispatcher, PostgresCheckpointConnectFailure,
    PostgresCheckpointConnectStage,
};
pub use socket::{CheckpointServeOutcome, CheckpointServerFailure, LoopbackCheckpointServer};

const RESPONSE_SCHEMA_VERSION: &str = "hwpx-agent.remote-sync-response/v1";
const MAX_REQUEST_BYTES: usize = 16_384;
const MAX_CHECKPOINT_ID_BYTES: usize = 120;
const HISTORY_CHECKPOINT_NAMESPACE: Uuid =
    Uuid::from_u128(0xa995_0b64_8833_5e26_88e7_53c2_2c08_2535);

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum CheckpointHostFailure {
    #[error("checkpoint host rejected the exchange")]
    Rejected,
    #[error("checkpoint host cannot determine the exchange outcome")]
    Unavailable,
}

impl CheckpointHostFailure {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::Rejected => "CHECKPOINT_HOST_REJECTED",
            Self::Unavailable => "CHECKPOINT_HOST_UNAVAILABLE",
        }
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum CheckpointDispatchError {
    #[error("checkpoint service rejected the request")]
    Rejected,
    #[error("checkpoint service outcome is unavailable")]
    Unavailable,
}

impl CheckpointDispatchError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::Rejected => "CHECKPOINT_DISPATCH_REJECTED",
            Self::Unavailable => "CHECKPOINT_DISPATCH_UNAVAILABLE",
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct CheckpointDispatchOutcome {
    checkpoint_id: String,
    revision_id: String,
    replayed: bool,
}

impl CheckpointDispatchOutcome {
    #[must_use]
    pub const fn new(checkpoint_id: String, revision_id: String, replayed: bool) -> Self {
        Self {
            checkpoint_id,
            revision_id,
            replayed,
        }
    }

    #[must_use]
    pub fn checkpoint_id(&self) -> &str {
        &self.checkpoint_id
    }

    #[must_use]
    pub fn revision_id(&self) -> &str {
        &self.revision_id
    }

    #[must_use]
    pub const fn replayed(&self) -> bool {
        self.replayed
    }
}

impl fmt::Debug for CheckpointDispatchOutcome {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointDispatchOutcome")
            .field("checkpoint_id", &"<redacted>")
            .field("revision_id", &"<redacted>")
            .field("replayed", &self.replayed)
            .finish()
    }
}

pub struct CheckpointDispatchRequest<'a> {
    tenant_id: TenantId,
    subject: SubjectDigest,
    now_unix_seconds: u64,
    binding: &'a CheckpointServiceBinding,
}

impl CheckpointDispatchRequest<'_> {
    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.tenant_id
    }

    #[must_use]
    pub const fn subject(&self) -> SubjectDigest {
        self.subject
    }

    #[must_use]
    pub const fn now_unix_seconds(&self) -> u64 {
        self.now_unix_seconds
    }

    #[must_use]
    pub const fn arguments(&self) -> &CheckpointServiceArguments {
        self.binding.arguments()
    }

    #[must_use]
    pub fn branch_id(&self) -> &str {
        self.binding.branch_id()
    }

    #[must_use]
    pub fn mirror_id(&self) -> &str {
        self.binding.mirror_id()
    }

    #[must_use]
    pub const fn expected_generation(&self) -> u64 {
        self.binding.expected_generation()
    }

    #[must_use]
    pub fn service_intent_sha256(&self) -> &str {
        self.binding.service_intent_sha256()
    }

    #[must_use]
    pub fn service_arguments_sha256(&self) -> &str {
        self.binding.service_arguments_sha256()
    }
}

impl fmt::Debug for CheckpointDispatchRequest<'_> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointDispatchRequest")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("now_unix_seconds", &self.now_unix_seconds)
            .field("arguments", &self.binding.arguments())
            .field("service_intent_sha256", &"<redacted>")
            .field("service_arguments_sha256", &"<redacted>")
            .finish()
    }
}

pub trait CheckpointDispatcher: fmt::Debug {
    /// Dispatches exact P15 checkpoint arguments after authentication and mirror admission.
    ///
    /// # Errors
    ///
    /// Returns rejected for a definitive service denial and unavailable for any uncertain outcome.
    fn dispatch(
        &self,
        request: &CheckpointDispatchRequest<'_>,
    ) -> Result<CheckpointDispatchOutcome, CheckpointDispatchError>;
}

pub struct HistoryCheckpointDispatcher<R: HistoryRepository> {
    service: HistoryService<R>,
}

impl<R: HistoryRepository> HistoryCheckpointDispatcher<R> {
    #[must_use]
    pub const fn new(service: HistoryService<R>) -> Self {
        Self { service }
    }
}

impl<R: HistoryRepository> fmt::Debug for HistoryCheckpointDispatcher<R> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HistoryCheckpointDispatcher")
            .field("service", &"<redacted>")
            .finish()
    }
}

impl<R: HistoryRepository> CheckpointDispatcher for HistoryCheckpointDispatcher<R> {
    fn dispatch(
        &self,
        request: &CheckpointDispatchRequest<'_>,
    ) -> Result<CheckpointDispatchOutcome, CheckpointDispatchError> {
        let (history_context, history_request) = map_history_checkpoint_request(request)?;
        let project_id = history_request.project_id();
        let revision_id = history_request.revision_id();
        let (record, replayed) = match self.service.checkpoint(&history_context, &history_request) {
            Ok(HistoryCheckpointOutcome::Created(record)) => (record, false),
            Ok(HistoryCheckpointOutcome::Replayed(record)) => (record, true),
            Err(error) => return Err(map_history_error(&error)),
        };
        if record.project_id() != project_id || record.revision_id() != revision_id {
            return Err(CheckpointDispatchError::Unavailable);
        }
        Ok(CheckpointDispatchOutcome::new(
            record.checkpoint_id().public_id(),
            record.revision_id().public_id(),
            replayed,
        ))
    }
}

fn map_history_checkpoint_request(
    request: &CheckpointDispatchRequest<'_>,
) -> Result<(HistoryRequestContext, HistoryCheckpointRequest), CheckpointDispatchError> {
    let arguments = request.arguments();
    let project_id =
        ProjectId::parse(arguments.project_id()).map_err(|_| CheckpointDispatchError::Rejected)?;
    let revision_id = RevisionId::parse(arguments.revision_id())
        .map_err(|_| CheckpointDispatchError::Rejected)?;
    if arguments.expected_revision() != arguments.revision_id() {
        return Err(CheckpointDispatchError::Rejected);
    }
    let idempotency_uuid = Uuid::parse_str(arguments.idempotency_key())
        .map_err(|_| CheckpointDispatchError::Rejected)?;
    if idempotency_uuid.is_nil()
        || idempotency_uuid.hyphenated().to_string() != arguments.idempotency_key()
    {
        return Err(CheckpointDispatchError::Rejected);
    }
    let request_id = RequestId::parse(&format!("req_{}", idempotency_uuid.simple()))
        .map_err(|_| CheckpointDispatchError::Rejected)?;
    let mut checkpoint_name = Vec::with_capacity(48);
    checkpoint_name.extend_from_slice(request.tenant_id().as_uuid().as_bytes());
    checkpoint_name.extend_from_slice(project_id.as_uuid().as_bytes());
    checkpoint_name.extend_from_slice(idempotency_uuid.as_bytes());
    let checkpoint_id = CheckpointId::parse(&format!(
        "chk_{}",
        Uuid::new_v5(&HISTORY_CHECKPOINT_NAMESPACE, &checkpoint_name).simple()
    ))
    .map_err(|_| CheckpointDispatchError::Rejected)?;
    let label = CheckpointLabel::parse(arguments.label().to_owned())
        .map_err(|_| CheckpointDispatchError::Rejected)?;
    if label.as_str() != arguments.label() {
        return Err(CheckpointDispatchError::Rejected);
    }
    let note = arguments
        .note()
        .map(|value| {
            if value.contains('\0') {
                return Err(HistoryError::InvalidRequest);
            }
            CheckpointNote::parse(value.to_owned())
        })
        .transpose()
        .map_err(|_| CheckpointDispatchError::Rejected)?;
    Ok((
        HistoryRequestContext::new(
            request.tenant_id(),
            request.subject(),
            request.now_unix_seconds(),
        ),
        HistoryCheckpointRequest::new_with_note(
            request_id,
            project_id,
            checkpoint_id,
            revision_id,
            label,
            note,
        ),
    ))
}

pub struct CheckpointHost<D> {
    authentication: Mutex<AuthMiddleware>,
    registry: RetentionSyncService,
    dispatcher: D,
}

impl<D> CheckpointHost<D> {
    #[must_use]
    pub const fn new(
        authentication: AuthMiddleware,
        registry: RetentionSyncService,
        dispatcher: D,
    ) -> Self {
        Self {
            authentication: Mutex::new(authentication),
            registry,
            dispatcher,
        }
    }
}

impl<D> fmt::Debug for CheckpointHost<D> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CheckpointHost")
            .field("authentication", &"<redacted>")
            .field("registry", &"<redacted>")
            .field("dispatcher", &"<redacted>")
            .finish()
    }
}

impl<D> CheckpointHost<D>
where
    D: CheckpointDispatcher,
{
    /// Handles one exact private checkpoint request using a single-use service credential.
    ///
    /// # Errors
    ///
    /// Returns rejected for malformed or unauthorized exchanges. Returns unavailable for poisoned
    /// host state, repository failure, uncertain dispatch or an invalid post-dispatch receipt.
    pub fn handle_checkpoint(
        &self,
        authorization_header: &str,
        request_bytes: &[u8],
        request_id: String,
        locale: String,
        now_unix_seconds: u64,
    ) -> Result<Vec<u8>, CheckpointHostFailure> {
        if request_bytes.is_empty() || request_bytes.len() > MAX_REQUEST_BYTES {
            return Err(CheckpointHostFailure::Rejected);
        }
        let service_context = CheckpointServiceContext::new(request_id, locale)
            .map_err(|_| CheckpointHostFailure::Rejected)?;
        let auth_context = self
            .authentication
            .lock()
            .map_err(|_| CheckpointHostFailure::Unavailable)?
            .authenticate_internal_service_once(
                authorization_header,
                now_unix_seconds,
                [AuthScope::MirrorSync],
            )
            .map_err(|_| CheckpointHostFailure::Rejected)?;
        let binding = decode_checkpoint_to_service(request_bytes, &service_context)
            .map_err(|_| CheckpointHostFailure::Rejected)?;

        let project_id = ProjectId::parse(binding.arguments().project_id())
            .map_err(|_| CheckpointHostFailure::Rejected)?;
        let branch_id =
            BranchId::parse(binding.branch_id()).map_err(|_| CheckpointHostFailure::Rejected)?;
        let mirror_id = MirrorId::parse_public(binding.mirror_id())
            .map_err(|_| CheckpointHostFailure::Rejected)?;
        let revision_id = RevisionId::parse(binding.arguments().expected_revision())
            .map_err(|_| CheckpointHostFailure::Rejected)?;
        if binding.arguments().revision_id() != binding.arguments().expected_revision() {
            return Err(CheckpointHostFailure::Rejected);
        }
        let expected_head = RemoteHead {
            revision_id: Some(revision_id),
            generation: binding.expected_generation(),
        };
        let registry_context = RequestContext::new(
            auth_context.tenant_id(),
            auth_context.subject(),
            now_unix_seconds,
        );
        match self.registry.authorize_mirror_checkpoint(
            &registry_context,
            project_id,
            branch_id,
            mirror_id,
            expected_head,
        ) {
            Ok(MirrorCheckpointDecision::Authorized) => {}
            Ok(MirrorCheckpointDecision::Conflict(current)) => {
                return encode_response(
                    binding.private_request_sha256(),
                    CheckpointWireResult::Conflict {
                        head: OwnedWireHead::from(current),
                    },
                );
            }
            Err(RetentionSyncError::RepositoryFailure) => {
                return Err(CheckpointHostFailure::Unavailable);
            }
            Err(_) => {
                return encode_response(
                    binding.private_request_sha256(),
                    CheckpointWireResult::Rejected {},
                );
            }
        }

        let dispatch_request = CheckpointDispatchRequest {
            tenant_id: auth_context.tenant_id(),
            subject: auth_context.subject(),
            now_unix_seconds,
            binding: &binding,
        };
        let outcome = match self.dispatcher.dispatch(&dispatch_request) {
            Ok(outcome) => outcome,
            Err(CheckpointDispatchError::Rejected) => {
                return encode_response(
                    binding.private_request_sha256(),
                    CheckpointWireResult::Rejected {},
                );
            }
            Err(CheckpointDispatchError::Unavailable) => {
                return Err(CheckpointHostFailure::Unavailable);
            }
        };
        if !valid_checkpoint_id(outcome.checkpoint_id())
            || outcome.revision_id() != binding.arguments().expected_revision()
        {
            return Err(CheckpointHostFailure::Unavailable);
        }
        encode_response(
            binding.private_request_sha256(),
            CheckpointWireResult::Succeeded {
                checkpoint_id: outcome.checkpoint_id,
                revision_id: outcome.revision_id,
                replayed: outcome.replayed,
            },
        )
    }
}

#[derive(Serialize)]
struct BoundCheckpointResponse<'a> {
    schema_version: &'static str,
    request_sha256: &'a str,
    result: CheckpointWireResult,
}

#[derive(Serialize)]
#[serde(tag = "outcome", rename_all = "snake_case")]
enum CheckpointWireResult {
    Succeeded {
        checkpoint_id: String,
        revision_id: String,
        replayed: bool,
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

impl From<RemoteHead> for OwnedWireHead {
    fn from(value: RemoteHead) -> Self {
        Self {
            revision_id: value.revision_id.map(RevisionId::public_id),
            generation: value.generation,
        }
    }
}

fn encode_response(
    request_sha256: &str,
    result: CheckpointWireResult,
) -> Result<Vec<u8>, CheckpointHostFailure> {
    serde_json::to_vec(&BoundCheckpointResponse {
        schema_version: RESPONSE_SCHEMA_VERSION,
        request_sha256,
        result,
    })
    .map_err(|_| CheckpointHostFailure::Unavailable)
}

fn valid_checkpoint_id(value: &str) -> bool {
    (12..=MAX_CHECKPOINT_ID_BYTES).contains(&value.len())
        && value.starts_with("chk_")
        && value[4..]
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}

const fn map_history_error(error: &HistoryError) -> CheckpointDispatchError {
    match error {
        HistoryError::InvalidIdentifier
        | HistoryError::InvalidRequest
        | HistoryError::NotFound
        | HistoryError::AccessDenied
        | HistoryError::DuplicateIdentity
        | HistoryError::IdempotencyConflict => CheckpointDispatchError::Rejected,
        HistoryError::InvalidCursor
        | HistoryError::CursorExpired
        | HistoryError::InvalidGraph
        | HistoryError::GraphLimitExceeded
        | HistoryError::Serialization
        | HistoryError::CryptoFailure
        | HistoryError::RepositoryFailure => CheckpointDispatchError::Unavailable,
    }
}

#[cfg(test)]
mod tests {
    use std::collections::VecDeque;
    use std::fmt;
    use std::io::Write;
    use std::net::{Ipv4Addr, Ipv6Addr, Shutdown, SocketAddr, TcpStream};
    use std::sync::Arc;
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::thread;
    use std::time::Duration;

    use artifact_service::{ArtifactId, ContentDigest};
    use auth_middleware::{AuthRegistryLimits, PrincipalGrant, TenantRole};
    use base64::Engine as _;
    use base64::engine::general_purpose::URL_SAFE_NO_PAD;
    use history_service::{
        CommittedRevisionProjection, CursorCodec, InMemoryHistoryRepository,
        ProjectRole as HistoryProjectRole,
    };
    use hmac::{Hmac, Mac as _};
    use local_sync::{
        AuthenticatedRemoteSyncAdapter, AuthorizationHeader, Connectivity, CredentialFailure,
        LocalMirror, LoopbackTcpTransport, RemoteCredentialProvider, RemoteHead as LocalRemoteHead,
        RemoteTransport, SingleUseCredentialProvider, TransportFailure,
    };
    use remote_sync_wire::{ResponseStatus, read_response, write_request};
    use retention_sync_service::{
        MirrorRegistration, ProjectRole, RetentionClass, RetentionPolicy,
    };
    use serde::Serialize;
    use serde_json::{Value, json};
    use sha2::{Digest as _, Sha256};
    use uuid::Uuid;

    use super::*;

    type HmacSha256 = Hmac<Sha256>;

    const RESOURCE: &str = "https://mcp.hwpx-agent.example";
    const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
    const ISSUER: &str = "https://identity.hwpx-agent.example";
    const KEY_ID: &str = "local-key-01";
    const SECRET: &[u8] = b"0123456789abcdef0123456789abcdef";
    const NOW: u64 = 2_000_000_000;

    #[derive(Clone, Copy, Debug)]
    enum DispatchMode {
        Success,
        Rejected,
        Unavailable,
        InvalidCheckpoint,
        InvalidRevision,
    }

    #[derive(Debug)]
    struct RecordingDispatcher {
        calls: AtomicUsize,
        mode: DispatchMode,
    }

    impl RecordingDispatcher {
        const fn new(mode: DispatchMode) -> Self {
            Self {
                calls: AtomicUsize::new(0),
                mode,
            }
        }
    }

    impl CheckpointDispatcher for RecordingDispatcher {
        fn dispatch(
            &self,
            request: &CheckpointDispatchRequest<'_>,
        ) -> Result<CheckpointDispatchOutcome, CheckpointDispatchError> {
            self.calls.fetch_add(1, Ordering::SeqCst);
            assert_eq!(request.arguments().client_surface(), "codex_local");
            assert_eq!(request.arguments().label(), "release-candidate");
            assert_eq!(request.arguments().note(), Some("reviewed locally"));
            assert_eq!(request.service_intent_sha256().len(), 64);
            assert_eq!(request.service_arguments_sha256().len(), 64);
            match self.mode {
                DispatchMode::Success => Ok(CheckpointDispatchOutcome::new(
                    "chk_00000000000000000000000000000020".to_owned(),
                    request.arguments().revision_id().to_owned(),
                    false,
                )),
                DispatchMode::Rejected => Err(CheckpointDispatchError::Rejected),
                DispatchMode::Unavailable => Err(CheckpointDispatchError::Unavailable),
                DispatchMode::InvalidCheckpoint => Ok(CheckpointDispatchOutcome::new(
                    "bad".to_owned(),
                    request.arguments().revision_id().to_owned(),
                    false,
                )),
                DispatchMode::InvalidRevision => Ok(CheckpointDispatchOutcome::new(
                    "chk_00000000000000000000000000000020".to_owned(),
                    "rev_00000000000000000000000000000099".to_owned(),
                    false,
                )),
            }
        }
    }

    struct TestCredentials {
        headers: VecDeque<String>,
    }

    impl fmt::Debug for TestCredentials {
        fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter
                .debug_struct("TestCredentials")
                .field("remaining", &self.headers.len())
                .finish()
        }
    }

    impl RemoteCredentialProvider for TestCredentials {
        fn authorization_header(&mut self) -> Result<AuthorizationHeader, CredentialFailure> {
            self.headers
                .pop_front()
                .ok_or(CredentialFailure::Unavailable)
                .and_then(AuthorizationHeader::new)
        }
    }

    struct HistoryLoopbackTransport {
        host: CheckpointHost<HistoryCheckpointDispatcher<InMemoryHistoryRepository>>,
        exchanges: usize,
    }

    impl fmt::Debug for HistoryLoopbackTransport {
        fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter
                .debug_struct("HistoryLoopbackTransport")
                .field("host", &"<redacted>")
                .field("exchanges", &self.exchanges)
                .finish()
        }
    }

    impl RemoteTransport for HistoryLoopbackTransport {
        fn exchange(
            &mut self,
            authorization_header: &str,
            request: &[u8],
        ) -> Result<Vec<u8>, TransportFailure> {
            self.exchanges = self.exchanges.saturating_add(1);
            self.host
                .handle_checkpoint(
                    authorization_header,
                    request,
                    format!("req_loopback{:08}", self.exchanges),
                    "ko-KR".to_owned(),
                    NOW,
                )
                .map_err(|failure| match failure {
                    CheckpointHostFailure::Rejected => TransportFailure::Rejected,
                    CheckpointHostFailure::Unavailable => TransportFailure::Unavailable,
                })
        }
    }

    #[derive(Serialize)]
    struct TestClaims {
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

    #[derive(Serialize)]
    struct TestCheckpointRequest<'a> {
        schema_version: &'static str,
        operation: &'static str,
        project_id: &'a str,
        branch_id: &'a str,
        mirror_id: &'a str,
        expected_head: TestHead<'a>,
        idempotency_key: &'static str,
        label: &'static str,
        note: &'static str,
    }

    #[derive(Serialize)]
    struct TestHead<'a> {
        revision_id: &'a str,
        generation: u64,
    }

    struct Fixture {
        host: CheckpointHost<RecordingDispatcher>,
        tenant_id: TenantId,
        project_id: ProjectId,
        branch_id: BranchId,
        mirror_id: MirrorId,
        revision_id: RevisionId,
        service_subject: SubjectDigest,
    }

    impl Fixture {
        fn new(mode: DispatchMode) -> Self {
            let tenant_id =
                TenantId::new(Uuid::from_u128(1)).unwrap_or_else(|error| panic!("tenant: {error}"));
            let project_id = ProjectId::parse("prj_00000000000000000000000000000002")
                .unwrap_or_else(|error| panic!("project: {error}"));
            let branch_id = BranchId::parse("brn_00000000000000000000000000000003")
                .unwrap_or_else(|error| panic!("branch: {error}"));
            let mirror_id = MirrorId::parse_public("mir_00000000000000000000000000000004")
                .unwrap_or_else(|error| panic!("mirror: {error}"));
            let revision_id = RevisionId::parse("rev_00000000000000000000000000000005")
                .unwrap_or_else(|error| panic!("revision: {error}"));
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
            let service_subject = authentication
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
            let registry = RetentionSyncService::default();
            registry
                .put_policy(tenant_id, "sync.local", policy())
                .and_then(|()| {
                    registry.provision_project(
                        tenant_id,
                        project_id,
                        "sync.local",
                        [(service_subject, ProjectRole::Owner)],
                    )
                })
                .and_then(|()| {
                    registry.register_branch(
                        tenant_id,
                        project_id,
                        branch_id,
                        RemoteHead {
                            revision_id: Some(revision_id),
                            generation: 1,
                        },
                    )
                })
                .and_then(|()| {
                    registry.register_mirror(
                        &RequestContext::new(tenant_id, service_subject, NOW),
                        &MirrorRegistration {
                            project_id,
                            branch_id,
                            mirror_id,
                            device_sha256: ContentDigest::of(b"device"),
                            observed_head: RemoteHead {
                                revision_id: Some(revision_id),
                                generation: 1,
                            },
                            snapshot_sha256: ContentDigest::of(b"snapshot"),
                        },
                    )
                })
                .unwrap_or_else(|error| panic!("registry: {error}"));
            Self {
                host: CheckpointHost::new(authentication, registry, RecordingDispatcher::new(mode)),
                tenant_id,
                project_id,
                branch_id,
                mirror_id,
                revision_id,
                service_subject,
            }
        }

        fn header(&self, jti: &str) -> String {
            let claims = TestClaims {
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

        fn request(&self, mirror_id: &str, revision_id: &str, generation: u64) -> Vec<u8> {
            serde_json::to_vec(&TestCheckpointRequest {
                schema_version: "hwpx-agent.remote-sync-request/v3",
                operation: "checkpoint",
                project_id: &self.project_id.public_id(),
                branch_id: &self.branch_id.public_id(),
                mirror_id,
                expected_head: TestHead {
                    revision_id,
                    generation,
                },
                idempotency_key: "checkpoint-request-0001",
                label: "release-candidate",
                note: "reviewed locally",
            })
            .unwrap_or_else(|error| panic!("request: {error}"))
        }

        fn exact_request(&self) -> Vec<u8> {
            self.request(
                &self.mirror_id.public_id(),
                &self.revision_id.public_id(),
                1,
            )
        }

        fn handle(&self, jti: &str, request: &[u8]) -> Result<Vec<u8>, CheckpointHostFailure> {
            self.host.handle_checkpoint(
                &self.header(jti),
                request,
                "req_checkpoint0001".to_owned(),
                "ko-KR".to_owned(),
                NOW,
            )
        }
    }

    fn policy() -> RetentionPolicy {
        RetentionPolicy::new(
            [
                (RetentionClass::Source, 100),
                (RetentionClass::Result, 100),
                (RetentionClass::Preview, 100),
                (RetentionClass::Evidence, 100),
                (RetentionClass::Trace, 100),
                (RetentionClass::Diff, 100),
                (RetentionClass::Receipt, 100),
            ],
            0,
        )
        .unwrap_or_else(|error| panic!("policy: {error}"))
    }

    fn sign(claims: &TestClaims) -> String {
        let header = json!({"alg": "HS256", "kid": KEY_ID, "typ": "hwpx-service+jwt"});
        let header = URL_SAFE_NO_PAD.encode(
            serde_json::to_vec(&header).unwrap_or_else(|error| panic!("header encoding: {error}")),
        );
        let claims = URL_SAFE_NO_PAD.encode(
            serde_json::to_vec(claims).unwrap_or_else(|error| panic!("claims encoding: {error}")),
        );
        let input = format!("{header}.{claims}");
        let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(SECRET)
            .unwrap_or_else(|error| panic!("signer: {error}"));
        signer.update(input.as_bytes());
        format!(
            "{input}.{}",
            URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
        )
    }

    fn decode(response: &[u8]) -> Value {
        serde_json::from_slice(response).unwrap_or_else(|error| panic!("response: {error}"))
    }

    #[test]
    fn exact_service_token_mirror_and_head_dispatch_once() {
        let fixture = Fixture::new(DispatchMode::Success);
        let request = fixture.exact_request();
        let response = fixture
            .handle("service-token-0001", &request)
            .unwrap_or_else(|error| panic!("handle: {error}"));
        let value = decode(&response);
        assert_eq!(value["schema_version"], RESPONSE_SCHEMA_VERSION);
        assert_eq!(
            value["request_sha256"],
            hex::encode(Sha256::digest(&request))
        );
        assert_eq!(value["result"]["outcome"], "succeeded");
        assert_eq!(
            value["result"]["revision_id"],
            fixture.revision_id.public_id()
        );
        assert_eq!(fixture.host.dispatcher.calls.load(Ordering::SeqCst), 1);
        assert_eq!(
            fixture.handle("service-token-0001", &request),
            Err(CheckpointHostFailure::Rejected)
        );
        assert_eq!(fixture.host.dispatcher.calls.load(Ordering::SeqCst), 1);
    }

    #[test]
    fn stale_head_returns_current_head_without_dispatch() {
        let fixture = Fixture::new(DispatchMode::Success);
        let request = fixture.request(
            &fixture.mirror_id.public_id(),
            "rev_00000000000000000000000000000006",
            2,
        );
        let response = fixture
            .handle("service-token-0002", &request)
            .unwrap_or_else(|error| panic!("handle: {error}"));
        let value = decode(&response);
        assert_eq!(value["result"]["outcome"], "conflict");
        assert_eq!(value["result"]["head"]["generation"], 1);
        assert_eq!(
            value["result"]["head"]["revision_id"],
            fixture.revision_id.public_id()
        );
        assert_eq!(fixture.host.dispatcher.calls.load(Ordering::SeqCst), 0);
    }

    #[test]
    fn cross_mirror_and_dispatch_rejection_are_bound_rejections() {
        let cross = Fixture::new(DispatchMode::Success);
        let request = cross.request(
            "mir_00000000000000000000000000000099",
            &cross.revision_id.public_id(),
            1,
        );
        let response = cross
            .handle("service-token-0003", &request)
            .unwrap_or_else(|error| panic!("cross mirror: {error}"));
        assert_eq!(decode(&response)["result"]["outcome"], "rejected");
        assert_eq!(cross.host.dispatcher.calls.load(Ordering::SeqCst), 0);

        let denied = Fixture::new(DispatchMode::Rejected);
        let response = denied
            .handle("service-token-0004", &denied.exact_request())
            .unwrap_or_else(|error| panic!("dispatch reject: {error}"));
        assert_eq!(decode(&response)["result"]["outcome"], "rejected");
        assert_eq!(denied.host.dispatcher.calls.load(Ordering::SeqCst), 1);
    }

    #[test]
    fn malformed_request_consumes_one_shot_token_before_zero_dispatch() {
        let fixture = Fixture::new(DispatchMode::Success);
        let mut request = fixture.exact_request();
        request.push(b' ');
        let header = fixture.header("service-token-0005");
        assert_eq!(
            fixture.host.handle_checkpoint(
                &header,
                &request,
                "req_checkpoint0001".to_owned(),
                "ko-KR".to_owned(),
                NOW,
            ),
            Err(CheckpointHostFailure::Rejected)
        );
        assert_eq!(
            fixture.host.handle_checkpoint(
                &header,
                &fixture.exact_request(),
                "req_checkpoint0001".to_owned(),
                "ko-KR".to_owned(),
                NOW,
            ),
            Err(CheckpointHostFailure::Rejected)
        );
        assert_eq!(fixture.host.dispatcher.calls.load(Ordering::SeqCst), 0);
    }

    #[test]
    fn uncertain_or_invalid_dispatch_receipts_are_unavailable() {
        for (index, mode) in [
            DispatchMode::Unavailable,
            DispatchMode::InvalidCheckpoint,
            DispatchMode::InvalidRevision,
        ]
        .into_iter()
        .enumerate()
        {
            let fixture = Fixture::new(mode);
            assert_eq!(
                fixture.handle(
                    &format!("service-token-invalid-{index:04}"),
                    &fixture.exact_request()
                ),
                Err(CheckpointHostFailure::Unavailable)
            );
            assert_eq!(fixture.host.dispatcher.calls.load(Ordering::SeqCst), 1);
        }
    }

    #[test]
    fn exact_local_adapter_and_history_host_create_then_replay_same_checkpoint() {
        let fixture = Fixture::new(DispatchMode::Success);
        let first_header = fixture.header("service-token-history-0001");
        let second_header = fixture.header("service-token-history-0002");
        let tenant_id = fixture.tenant_id;
        let project_id = fixture.project_id;
        let revision_id = fixture.revision_id;
        let service_subject = fixture.service_subject;
        let CheckpointHost {
            authentication,
            registry,
            dispatcher: _,
        } = fixture.host;
        let authentication = authentication
            .into_inner()
            .unwrap_or_else(|error| panic!("authentication mutex: {error}"));

        let repository = Arc::new(InMemoryHistoryRepository::default());
        repository
            .provision_project(
                tenant_id,
                project_id,
                [(service_subject, HistoryProjectRole::Owner)],
            )
            .and_then(|()| {
                repository.record_committed_revision(
                    tenant_id,
                    CommittedRevisionProjection::new(
                        project_id,
                        revision_id,
                        Vec::new(),
                        ArtifactId::generate(),
                        None,
                        1,
                    )?,
                )
            })
            .unwrap_or_else(|error| panic!("history repository: {error}"));
        let history = HistoryService::new(
            repository,
            CursorCodec::new(b"history-cursor-key-0123456789abcdef".to_vec(), 300)
                .unwrap_or_else(|error| panic!("cursor: {error}")),
        );
        let transport = HistoryLoopbackTransport {
            host: CheckpointHost::new(
                authentication,
                registry,
                HistoryCheckpointDispatcher::new(history),
            ),
            exchanges: 0,
        };
        let credentials = TestCredentials {
            headers: VecDeque::from([first_header, second_header]),
        };
        let mut adapter = AuthenticatedRemoteSyncAdapter::new(credentials, transport);
        let mut mirror = LocalMirror::new(
            project_id.public_id(),
            fixture.branch_id.public_id(),
            fixture.mirror_id.public_id(),
            LocalRemoteHead::new(Some(revision_id.public_id()), 1)
                .unwrap_or_else(|error| panic!("local head: {error}")),
            "1".repeat(64),
            Connectivity::Online,
        )
        .unwrap_or_else(|error| panic!("local mirror: {error}"));
        let first = mirror
            .checkpoint(
                &mut adapter,
                "checkpoint-request-0001".to_owned(),
                "release-candidate".to_owned(),
                Some("reviewed locally".to_owned()),
            )
            .unwrap_or_else(|error| panic!("first: {error}"));
        let second = mirror
            .checkpoint(
                &mut adapter,
                "checkpoint-request-0001".to_owned(),
                "release-candidate".to_owned(),
                Some("reviewed locally".to_owned()),
            )
            .unwrap_or_else(|error| panic!("second: {error}"));
        assert!(!first.replayed);
        assert!(second.replayed);
        assert_eq!(first.checkpoint_id, second.checkpoint_id);
        assert_eq!(first.revision_id, revision_id.public_id());
        assert_eq!(
            mirror.snapshot().last_checkpoint_id,
            Some(first.checkpoint_id)
        );
        let (credentials, transport) = adapter.into_parts();
        assert!(credentials.headers.is_empty());
        assert_eq!(transport.exchanges, 2);
    }

    #[test]
    fn history_mapping_rejects_nul_note_before_repository_dispatch() {
        let fixture = Fixture::new(DispatchMode::Success);
        let request_bytes = serde_json::to_vec(&TestCheckpointRequest {
            schema_version: "hwpx-agent.remote-sync-request/v3",
            operation: "checkpoint",
            project_id: &fixture.project_id.public_id(),
            branch_id: &fixture.branch_id.public_id(),
            mirror_id: &fixture.mirror_id.public_id(),
            expected_head: TestHead {
                revision_id: &fixture.revision_id.public_id(),
                generation: 1,
            },
            idempotency_key: "checkpoint-request-0001",
            label: "release-candidate",
            note: "invalid\0postgres-note",
        })
        .unwrap_or_else(|error| panic!("request: {error}"));
        let context =
            CheckpointServiceContext::new("req_checkpoint0001".to_owned(), "ko-KR".to_owned())
                .unwrap_or_else(|error| panic!("context: {error}"));
        let binding = decode_checkpoint_to_service(&request_bytes, &context)
            .unwrap_or_else(|error| panic!("binding: {error}"));
        let request = CheckpointDispatchRequest {
            tenant_id: fixture.tenant_id,
            subject: fixture.service_subject,
            now_unix_seconds: NOW,
            binding: &binding,
        };
        let repository = Arc::new(InMemoryHistoryRepository::default());
        let service = HistoryService::new(
            repository,
            CursorCodec::new(b"history-cursor-key-0123456789abcdef".to_vec(), 300)
                .unwrap_or_else(|error| panic!("cursor: {error}")),
        );
        let dispatcher = HistoryCheckpointDispatcher::new(service);
        assert_eq!(
            dispatcher.dispatch(&request),
            Err(CheckpointDispatchError::Rejected)
        );
    }

    #[test]
    fn actual_loopback_tcp_checkpoint_crosses_the_framed_host_boundary() {
        let fixture = Fixture::new(DispatchMode::Success);
        let header = fixture.header("service-token-tcp-0001");
        let project_id = fixture.project_id.public_id();
        let branch_id = fixture.branch_id.public_id();
        let mirror_id = fixture.mirror_id.public_id();
        let revision_id = fixture.revision_id.public_id();
        let server = LoopbackCheckpointServer::bind(
            SocketAddr::from((Ipv4Addr::LOCALHOST, 0)),
            fixture.host,
            "ko-KR".to_owned(),
            Duration::from_secs(5),
        )
        .unwrap_or_else(|error| panic!("bind: {error}"));
        let endpoint = server
            .local_addr()
            .unwrap_or_else(|error| panic!("local address: {error}"));
        let serving = thread::spawn(move || server.serve_one_at(NOW));

        let credentials = SingleUseCredentialProvider::new(header)
            .unwrap_or_else(|error| panic!("credentials: {error}"));
        let transport = LoopbackTcpTransport::new(endpoint, Duration::from_secs(5))
            .unwrap_or_else(|error| panic!("transport: {error}"));
        let mut adapter = AuthenticatedRemoteSyncAdapter::new(credentials, transport);
        let mut mirror = LocalMirror::new(
            project_id,
            branch_id,
            mirror_id,
            LocalRemoteHead::new(Some(revision_id.clone()), 1)
                .unwrap_or_else(|error| panic!("head: {error}")),
            "1".repeat(64),
            Connectivity::Online,
        )
        .unwrap_or_else(|error| panic!("mirror: {error}"));
        let receipt = mirror
            .checkpoint(
                &mut adapter,
                "checkpoint-request-0001".to_owned(),
                "release-candidate".to_owned(),
                Some("reviewed locally".to_owned()),
            )
            .unwrap_or_else(|error| panic!("checkpoint: {error}"));
        assert_eq!(receipt.revision_id, revision_id);
        assert!(!receipt.replayed);
        assert_eq!(
            serving
                .join()
                .unwrap_or_else(|_| panic!("server thread panicked"))
                .unwrap_or_else(|error| panic!("server: {error}")),
            CheckpointServeOutcome::Succeeded
        );
        let (mut credentials, transport) = adapter.into_parts();
        assert!(matches!(
            credentials.authorization_header(),
            Err(CredentialFailure::Unavailable)
        ));
        assert_eq!(transport.endpoint(), endpoint);
    }

    #[test]
    fn loopback_server_rejects_public_locale_and_timeout_drift() {
        let public = SocketAddr::from((Ipv4Addr::new(192, 0, 2, 1), 0));
        let fixture = Fixture::new(DispatchMode::Success);
        assert!(matches!(
            LoopbackCheckpointServer::bind(
                public,
                fixture.host,
                "ko-KR".to_owned(),
                Duration::from_secs(1)
            ),
            Err(CheckpointServerFailure::Rejected)
        ));

        let fixture = Fixture::new(DispatchMode::Success);
        assert!(matches!(
            LoopbackCheckpointServer::bind(
                SocketAddr::from((Ipv6Addr::LOCALHOST, 0)),
                fixture.host,
                "ko_KR".to_owned(),
                Duration::from_secs(1)
            ),
            Err(CheckpointServerFailure::Rejected)
        ));

        let fixture = Fixture::new(DispatchMode::Success);
        assert!(matches!(
            LoopbackCheckpointServer::bind(
                SocketAddr::from((Ipv4Addr::LOCALHOST, 0)),
                fixture.host,
                "ko-KR".to_owned(),
                Duration::from_secs(61)
            ),
            Err(CheckpointServerFailure::Rejected)
        ));
    }

    #[test]
    fn loopback_server_rejects_trailing_request_bytes_before_dispatch() {
        let fixture = Fixture::new(DispatchMode::Success);
        let header = fixture.header("service-token-trailing-0001");
        let request = fixture.exact_request();
        let server = LoopbackCheckpointServer::bind(
            SocketAddr::from((Ipv4Addr::LOCALHOST, 0)),
            fixture.host,
            "ko-KR".to_owned(),
            Duration::from_secs(5),
        )
        .unwrap_or_else(|error| panic!("bind: {error}"));
        let endpoint = server
            .local_addr()
            .unwrap_or_else(|error| panic!("address: {error}"));
        let serving = thread::spawn(move || server.serve_one_at(NOW));
        let mut stream =
            TcpStream::connect(endpoint).unwrap_or_else(|error| panic!("connect: {error}"));
        write_request(&mut stream, &header, &request)
            .unwrap_or_else(|error| panic!("request: {error}"));
        stream
            .write_all(b"x")
            .and_then(|()| stream.shutdown(Shutdown::Write))
            .unwrap_or_else(|error| panic!("trailing request: {error}"));
        let response =
            read_response(&mut stream).unwrap_or_else(|error| panic!("response: {error}"));
        assert_eq!(response.status(), ResponseStatus::Rejected);
        assert_eq!(
            serving
                .join()
                .unwrap_or_else(|_| panic!("server thread panicked"))
                .unwrap_or_else(|error| panic!("server: {error}")),
            CheckpointServeOutcome::Rejected
        );
    }

    #[test]
    fn authentication_and_debug_fail_closed_without_identity_disclosure() {
        let fixture = Fixture::new(DispatchMode::Success);
        assert_eq!(
            fixture.host.handle_checkpoint(
                "Bearer a.b.c",
                &fixture.exact_request(),
                "req_checkpoint0001".to_owned(),
                "ko-KR".to_owned(),
                NOW,
            ),
            Err(CheckpointHostFailure::Rejected)
        );
        let debug = format!("{:?}", fixture.host);
        assert!(!debug.contains("worker-01"));
        assert!(!debug.contains(&fixture.project_id.public_id()));
        assert!(!debug.contains(&fixture.mirror_id.public_id()));
        assert_eq!(fixture.host.dispatcher.calls.load(Ordering::SeqCst), 0);
    }
}
