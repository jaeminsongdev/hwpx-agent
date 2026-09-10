use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use zeroize::Zeroizing;

use crate::{
    CheckpointRequest, PullRequest, PushRequest, REMOTE_SYNC_PULL_REQUEST_SCHEMA_VERSION,
    REMOTE_SYNC_REQUEST_SCHEMA_VERSION, RemoteCheckpointReceipt, RemoteFailure, RemoteHead,
    RemotePushReceipt, RemoteSnapshot, RemoteSyncPort,
};

const RESPONSE_SCHEMA_VERSION: &str = "hwpx-agent.remote-sync-response/v1";
const MAX_AUTHORIZATION_BYTES: usize = 8_199;
const MAX_REQUEST_BYTES: usize = 16_384;
const MAX_RESPONSE_BYTES: usize = 65_536;

#[derive(Clone, Copy, Debug, Eq, PartialEq, thiserror::Error)]
pub enum CredentialFailure {
    #[error("remote sync credential provider is unavailable")]
    Unavailable,
    #[error("remote sync credential request was rejected")]
    Rejected,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, thiserror::Error)]
pub enum TransportFailure {
    #[error("remote sync transport is unavailable")]
    Unavailable,
    #[error("remote sync transport rejected the request")]
    Rejected,
}

pub struct AuthorizationHeader(Zeroizing<String>);

impl fmt::Debug for AuthorizationHeader {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("AuthorizationHeader(<redacted>)")
    }
}

impl AuthorizationHeader {
    /// Wraps one exact bounded JWT bearer header and zeroizes its owned bytes on drop.
    ///
    /// # Errors
    ///
    /// Rejects non-canonical casing, whitespace, control bytes, non-base64url token bytes and
    /// anything other than three non-empty JWT segments.
    pub fn new(value: String) -> Result<Self, CredentialFailure> {
        let value = Zeroizing::new(value);
        if value.is_empty()
            || value.len() > MAX_AUTHORIZATION_BYTES
            || value.as_bytes().iter().any(u8::is_ascii_control)
        {
            return Err(CredentialFailure::Rejected);
        }
        let token = value
            .strip_prefix("Bearer ")
            .ok_or(CredentialFailure::Rejected)?;
        let mut segments = token.split('.');
        let valid_segment = |segment: &str| {
            !segment.is_empty()
                && segment
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
        };
        let first = segments.next();
        let second = segments.next();
        let third = segments.next();
        if !matches!((first, second, third), (Some(a), Some(b), Some(c)) if valid_segment(a) && valid_segment(b) && valid_segment(c))
            || segments.next().is_some()
        {
            return Err(CredentialFailure::Rejected);
        }
        Ok(Self(value))
    }

    fn expose(&self) -> &str {
        self.0.as_str()
    }
}

pub trait RemoteCredentialProvider: fmt::Debug {
    /// Returns a fresh short-lived `mirror.sync` service bearer for exactly one remote exchange.
    ///
    /// # Errors
    ///
    /// Distinguishes unavailable credential custody from a rejected credential request.
    fn authorization_header(&mut self) -> Result<AuthorizationHeader, CredentialFailure>;
}

/// Process-local single-use credential handoff for a trusted launcher or broker.
///
/// The provider never persists or logs the credential. A second request fails closed, so callers
/// must inject a newly issued short-lived header for every exchange.
pub struct SingleUseCredentialProvider {
    authorization_header: Option<AuthorizationHeader>,
}

impl fmt::Debug for SingleUseCredentialProvider {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SingleUseCredentialProvider")
            .field("available", &self.authorization_header.is_some())
            .finish()
    }
}

impl SingleUseCredentialProvider {
    /// Accepts one already-issued, bounded bearer header without storing it outside this process.
    ///
    /// # Errors
    ///
    /// Rejects a malformed authorization header.
    pub fn new(authorization_header: String) -> Result<Self, CredentialFailure> {
        Ok(Self {
            authorization_header: Some(AuthorizationHeader::new(authorization_header)?),
        })
    }
}

impl RemoteCredentialProvider for SingleUseCredentialProvider {
    fn authorization_header(&mut self) -> Result<AuthorizationHeader, CredentialFailure> {
        self.authorization_header
            .take()
            .ok_or(CredentialFailure::Unavailable)
    }
}

pub trait RemoteTransport: fmt::Debug {
    /// Exchanges one bounded private request using the provided short-lived authorization header.
    ///
    /// # Errors
    ///
    /// Returns unavailable for uncertain transport outcomes and rejected for definitive denial.
    fn exchange(
        &mut self,
        authorization_header: &str,
        request: &[u8],
    ) -> Result<Vec<u8>, TransportFailure>;
}

pub struct AuthenticatedRemoteSyncAdapter<P, T> {
    credentials: P,
    transport: T,
}

impl<P, T> fmt::Debug for AuthenticatedRemoteSyncAdapter<P, T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AuthenticatedRemoteSyncAdapter")
            .field("credentials", &"<redacted>")
            .field("transport", &"<redacted>")
            .finish()
    }
}

impl<P, T> AuthenticatedRemoteSyncAdapter<P, T> {
    #[must_use]
    pub const fn new(credentials: P, transport: T) -> Self {
        Self {
            credentials,
            transport,
        }
    }

    #[must_use]
    pub fn into_parts(self) -> (P, T) {
        (self.credentials, self.transport)
    }
}

impl<P, T> AuthenticatedRemoteSyncAdapter<P, T>
where
    P: RemoteCredentialProvider,
    T: RemoteTransport,
{
    fn exchange<R: for<'de> Deserialize<'de>>(
        &mut self,
        request: &impl Serialize,
    ) -> Result<R, RemoteFailure> {
        let encoded = serde_json::to_vec(request).map_err(|_| RemoteFailure::InvalidResponse)?;
        self.exchange_encoded(&encoded)
    }

    fn exchange_encoded<R: for<'de> Deserialize<'de>>(
        &mut self,
        encoded: &[u8],
    ) -> Result<R, RemoteFailure> {
        if encoded.is_empty() || encoded.len() > MAX_REQUEST_BYTES {
            return Err(RemoteFailure::InvalidResponse);
        }
        let request_sha256 = hex::encode(Sha256::digest(encoded));
        let authorization = self
            .credentials
            .authorization_header()
            .map_err(map_credential_failure)?;
        let response = self
            .transport
            .exchange(authorization.expose(), encoded)
            .map_err(map_transport_failure)?;
        if response.is_empty() || response.len() > MAX_RESPONSE_BYTES {
            return Err(RemoteFailure::InvalidResponse);
        }
        let decoded: BoundResponse<R> =
            serde_json::from_slice(&response).map_err(|_| RemoteFailure::InvalidResponse)?;
        if decoded.schema_version != RESPONSE_SCHEMA_VERSION
            || decoded.request_sha256 != request_sha256
        {
            return Err(RemoteFailure::InvalidResponse);
        }
        Ok(decoded.result)
    }
}

impl<P, T> RemoteSyncPort for AuthenticatedRemoteSyncAdapter<P, T>
where
    P: RemoteCredentialProvider,
    T: RemoteTransport,
{
    fn pull(&mut self, request: &PullRequest) -> Result<RemoteSnapshot, RemoteFailure> {
        let wire = PullWireRequest {
            schema_version: REMOTE_SYNC_PULL_REQUEST_SCHEMA_VERSION,
            operation: "pull",
            project_id: request.project_id(),
            branch_id: request.branch_id(),
            mirror_id: request.mirror_id(),
            observed_head: WireHead::from(request.observed_head()),
            observed_snapshot_sha256: request.observed_snapshot_sha256(),
        };
        match self.exchange::<PullWireResult>(&wire)? {
            PullWireResult::Succeeded {
                head,
                snapshot_sha256,
            } => Ok(RemoteSnapshot {
                head: head.parse()?,
                snapshot_sha256,
            }),
            PullWireResult::Conflict { head } => Err(RemoteFailure::Conflict(head.parse()?)),
            PullWireResult::Rejected {} => Err(RemoteFailure::Rejected),
        }
    }

    fn push(&mut self, request: &PushRequest) -> Result<RemotePushReceipt, RemoteFailure> {
        let wire = PushWireRequest {
            schema_version: REMOTE_SYNC_REQUEST_SCHEMA_VERSION,
            operation: "push",
            project_id: request.project_id(),
            branch_id: request.branch_id(),
            mirror_id: request.mirror_id(),
            expected_head: WireHead::from(request.expected_head()),
            snapshot_sha256: request.snapshot_sha256(),
            operation_plan_sha256: request.operation_plan_sha256(),
            idempotency_key: request.idempotency_key(),
        };
        match self.exchange::<PushWireResult>(&wire)? {
            PushWireResult::Succeeded {
                head,
                snapshot_sha256,
            } => Ok(RemotePushReceipt {
                head: head.parse()?,
                snapshot_sha256,
            }),
            PushWireResult::Conflict { head } => Err(RemoteFailure::Conflict(head.parse()?)),
            PushWireResult::Rejected {} => Err(RemoteFailure::Rejected),
        }
    }

    fn checkpoint(
        &mut self,
        request: &CheckpointRequest,
    ) -> Result<RemoteCheckpointReceipt, RemoteFailure> {
        let encoded = request
            .encoded_wire_request()
            .map_err(|_| RemoteFailure::InvalidResponse)?;
        match self.exchange_encoded::<CheckpointWireResult>(&encoded)? {
            CheckpointWireResult::Succeeded {
                checkpoint_id,
                revision_id,
                replayed,
            } => Ok(RemoteCheckpointReceipt {
                checkpoint_id,
                revision_id,
                replayed,
            }),
            CheckpointWireResult::Conflict { head } => Err(RemoteFailure::Conflict(head.parse()?)),
            CheckpointWireResult::Rejected {} => Err(RemoteFailure::Rejected),
        }
    }
}

#[derive(Serialize)]
struct PullWireRequest<'a> {
    schema_version: &'static str,
    operation: &'static str,
    project_id: &'a str,
    branch_id: &'a str,
    mirror_id: &'a str,
    observed_head: WireHead<'a>,
    observed_snapshot_sha256: &'a str,
}

#[derive(Serialize)]
struct PushWireRequest<'a> {
    schema_version: &'static str,
    operation: &'static str,
    project_id: &'a str,
    branch_id: &'a str,
    mirror_id: &'a str,
    expected_head: WireHead<'a>,
    snapshot_sha256: &'a str,
    operation_plan_sha256: &'a str,
    idempotency_key: &'a str,
}

#[derive(Serialize)]
struct WireHead<'a> {
    revision_id: Option<&'a str>,
    generation: u64,
}

impl<'a> From<&'a RemoteHead> for WireHead<'a> {
    fn from(head: &'a RemoteHead) -> Self {
        Self {
            revision_id: head.revision_id(),
            generation: head.generation(),
        }
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct BoundResponse<R> {
    schema_version: String,
    request_sha256: String,
    result: R,
}

#[derive(Deserialize)]
#[serde(tag = "outcome", rename_all = "snake_case", deny_unknown_fields)]
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

#[derive(Deserialize)]
#[serde(tag = "outcome", rename_all = "snake_case", deny_unknown_fields)]
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

#[derive(Deserialize)]
#[serde(tag = "outcome", rename_all = "snake_case", deny_unknown_fields)]
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

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct OwnedWireHead {
    revision_id: Option<String>,
    generation: u64,
}

impl OwnedWireHead {
    fn parse(self) -> Result<RemoteHead, RemoteFailure> {
        RemoteHead::new(self.revision_id, self.generation)
            .map_err(|_| RemoteFailure::InvalidResponse)
    }
}

const fn map_credential_failure(error: CredentialFailure) -> RemoteFailure {
    match error {
        CredentialFailure::Unavailable => RemoteFailure::Unavailable,
        CredentialFailure::Rejected => RemoteFailure::Rejected,
    }
}

const fn map_transport_failure(error: TransportFailure) -> RemoteFailure {
    match error {
        TransportFailure::Unavailable => RemoteFailure::Unavailable,
        TransportFailure::Rejected => RemoteFailure::Rejected,
    }
}
