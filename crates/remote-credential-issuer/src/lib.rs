//! Fail-closed credential issuer core with exact lifecycle and replay semantics.

#![forbid(unsafe_code)]

use std::collections::BTreeMap;
use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::net::{IpAddr, Shutdown, SocketAddr, TcpListener};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::Duration;

use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use remote_credential_wire::{FrameError, ResponseStatus, read_request, write_response};
use ring::signature::{ED25519, UnparsedPublicKey};
use rustls::pki_types::{CertificateDer, PrivateKeyDer};
use rustls::{ServerConfig, ServerConnection, StreamOwned, version};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zeroize::Zeroizing;

const LIFECYCLE_REQUEST_SCHEMA: &str = "hwpx-agent.remote-credential-lifecycle-request/v1";
const ISSUER_RESPONSE_SCHEMA: &str = "hwpx-agent.remote-credential-issuer-response/v1";
const RECORD_SCHEMA: &str = "hwpx-agent.remote-credential-issuer-record/v1";
const POLICY_BINDING_SCHEMA: &str = "hwpx-agent.remote-credential-issuer-policy/v1";
const CLIENT_ASSERTION_TYPE: &str = "hwpx-agent-issuer-client+jwt";
const ACCESS_TOKEN_TYPE: &str = "hwpx-agent-service+jwt";
const REVOCATION_TYPE: &str = "hwpx-agent-revocation+jwt";
const CLIENT_SCOPE: &str = "credential.manage";
const SERVICE_SCOPE: &str = "mirror.sync";
const MAX_IDENTIFIER_BYTES: usize = 240;
const MAX_KEY_ID_BYTES: usize = 64;
const MAX_OPERATION_ID_BYTES: usize = 120;
const MIN_OPERATION_ID_BYTES: usize = 16;
const MAX_JTI_BYTES: usize = 120;
const MIN_JTI_BYTES: usize = 16;
const MAX_ASSERTION_BYTES: usize = 8_192;
const MAX_REQUEST_BYTES: usize = 16_384;
const MAX_RESPONSE_BYTES: usize = 8_192;
const MAX_HEADER_BYTES: usize = 1_024;
const MAX_CLAIMS_BYTES: usize = 4_096;
const MAX_RECORD_BYTES: usize = 65_536;
const MAX_LOG_RECORDS: u64 = 65_536;
const MAX_TEMP_FILES: usize = 64;
const MAX_KEYS: usize = 8;
const MAX_CERTIFICATES: usize = 4;
const MAX_CERTIFICATE_BYTES: usize = 32_768;
const MAX_CERTIFICATE_CHAIN_BYTES: usize = 65_536;
const MAX_PRIVATE_KEY_BYTES: usize = 16_384;
const MAX_IO_TIMEOUT: Duration = Duration::from_mins(1);

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum IssuerError {
    #[error("credential issuer request was rejected")]
    Rejected,
    #[error("credential issuer is unavailable")]
    Unavailable,
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum StoreFailure {
    #[error("credential issuer state was rejected")]
    Rejected,
    #[error("credential issuer state conflicted")]
    Conflict,
    #[error("credential issuer state is unavailable")]
    Unavailable,
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum SignerFailure {
    #[error("credential signer rejected the operation")]
    Rejected,
    #[error("credential signer is unavailable")]
    Unavailable,
}

#[derive(Clone, Eq, PartialEq)]
pub struct VerificationKey {
    key_id: String,
    public_key: [u8; 32],
}

impl fmt::Debug for VerificationKey {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("VerificationKey")
            .field("key_id", &"<redacted>")
            .field("public_key", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl VerificationKey {
    /// Creates one exact Ed25519 verification key.
    ///
    /// # Errors
    ///
    /// Rejects malformed key identifiers and an all-zero public key.
    pub fn new(key_id: String, public_key: [u8; 32]) -> Result<Self, IssuerError> {
        validate_token_identifier(&key_id, 1, MAX_KEY_ID_BYTES)?;
        if public_key.iter().all(|byte| *byte == 0) {
            return Err(IssuerError::Rejected);
        }
        Ok(Self { key_id, public_key })
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct IssuerPolicy {
    lifecycle_binding_sha256: String,
    client_issuer: String,
    client_subject: String,
    client_audience: String,
    client_keys: Vec<VerificationKey>,
    signing_key: VerificationKey,
    service_issuer: String,
    service_subject: String,
    service_audience: String,
    access_lifetime_seconds: u64,
    maximum_assertion_lifetime_seconds: u64,
    clock_skew_seconds: u64,
    maximum_request_age_seconds: u64,
}

impl fmt::Debug for IssuerPolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IssuerPolicy")
            .field("identities", &"<redacted>")
            .field("digests", &"<redacted>")
            .field("client_key_count", &self.client_keys.len())
            .field("time_policy", &"<bounded>")
            .finish_non_exhaustive()
    }
}

impl IssuerPolicy {
    /// Creates the exact authentication, signing, lifecycle and time policy for one issuer.
    ///
    /// Client keys must be strictly sorted by key ID so the policy binding is deterministic.
    ///
    /// # Errors
    ///
    /// Rejects malformed identities, keys, digests, duplicate or unsorted keys and unsafe bounds.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        lifecycle_binding_sha256: String,
        client_issuer: String,
        client_subject: String,
        client_audience: String,
        client_keys: Vec<VerificationKey>,
        signing_key: VerificationKey,
        service_issuer: String,
        service_subject: String,
        service_audience: String,
        access_lifetime_seconds: u64,
        maximum_assertion_lifetime_seconds: u64,
        clock_skew_seconds: u64,
        maximum_request_age_seconds: u64,
    ) -> Result<Self, IssuerError> {
        if !is_hex64(&lifecycle_binding_sha256)
            || client_keys.is_empty()
            || client_keys.len() > MAX_KEYS
            || !(60..=86_400).contains(&access_lifetime_seconds)
            || !(30..=600).contains(&maximum_assertion_lifetime_seconds)
            || clock_skew_seconds > 300
            || !(30..=600).contains(&maximum_request_age_seconds)
        {
            return Err(IssuerError::Rejected);
        }
        validate_https_issuer(&client_issuer)?;
        validate_https_issuer(&service_issuer)?;
        for identity in [
            &client_subject,
            &client_audience,
            &service_subject,
            &service_audience,
        ] {
            validate_token_identifier(identity, 1, MAX_IDENTIFIER_BYTES)?;
        }
        for pair in client_keys.windows(2) {
            if pair[0].key_id >= pair[1].key_id {
                return Err(IssuerError::Rejected);
            }
        }
        if client_keys
            .iter()
            .any(|key| key.key_id == signing_key.key_id)
        {
            return Err(IssuerError::Rejected);
        }
        Ok(Self {
            lifecycle_binding_sha256,
            client_issuer,
            client_subject,
            client_audience,
            client_keys,
            signing_key,
            service_issuer,
            service_subject,
            service_audience,
            access_lifetime_seconds,
            maximum_assertion_lifetime_seconds,
            clock_skew_seconds,
            maximum_request_age_seconds,
        })
    }

    /// Returns the canonical SHA-256 binding for every issuer policy field.
    ///
    /// # Errors
    ///
    /// Returns unavailable if bounded canonical serialization fails.
    pub fn binding_sha256(&self) -> Result<String, IssuerError> {
        #[derive(Serialize)]
        struct KeyBinding<'a> {
            key_id: &'a str,
            public_key_sha256: String,
        }
        #[derive(Serialize)]
        struct Binding<'a> {
            schema_version: &'static str,
            lifecycle_binding_sha256: &'a str,
            client_issuer: &'a str,
            client_subject: &'a str,
            client_audience: &'a str,
            client_scope: &'static str,
            client_keys: Vec<KeyBinding<'a>>,
            signing_key: KeyBinding<'a>,
            service_issuer: &'a str,
            service_subject: &'a str,
            service_audience: &'a str,
            service_scope: &'static str,
            access_lifetime_seconds: u64,
            maximum_assertion_lifetime_seconds: u64,
            clock_skew_seconds: u64,
            maximum_request_age_seconds: u64,
        }
        let binding = Binding {
            schema_version: POLICY_BINDING_SCHEMA,
            lifecycle_binding_sha256: &self.lifecycle_binding_sha256,
            client_issuer: &self.client_issuer,
            client_subject: &self.client_subject,
            client_audience: &self.client_audience,
            client_scope: CLIENT_SCOPE,
            client_keys: self
                .client_keys
                .iter()
                .map(|key| KeyBinding {
                    key_id: &key.key_id,
                    public_key_sha256: digest_bytes(&key.public_key),
                })
                .collect(),
            signing_key: KeyBinding {
                key_id: &self.signing_key.key_id,
                public_key_sha256: digest_bytes(&self.signing_key.public_key),
            },
            service_issuer: &self.service_issuer,
            service_subject: &self.service_subject,
            service_audience: &self.service_audience,
            service_scope: SERVICE_SCOPE,
            access_lifetime_seconds: self.access_lifetime_seconds,
            maximum_assertion_lifetime_seconds: self.maximum_assertion_lifetime_seconds,
            clock_skew_seconds: self.clock_skew_seconds,
            maximum_request_age_seconds: self.maximum_request_age_seconds,
        };
        serde_json::to_vec(&binding)
            .map(|bytes| digest_bytes(&bytes))
            .map_err(|_| IssuerError::Unavailable)
    }

    fn client_key(&self, key_id: &str) -> Option<&VerificationKey> {
        self.client_keys.iter().find(|key| key.key_id == key_id)
    }
}

pub trait CredentialTokenSigner: fmt::Debug {
    /// Returns the exact key ID for the pinned signing public key.
    fn key_id(&self) -> &str;

    /// Signs one bounded Ed25519 JWS signing input.
    ///
    /// # Errors
    ///
    /// Distinguishes a rejected request from signer unavailability without exposing key material.
    fn sign(&mut self, signing_input: &[u8]) -> Result<[u8; 64], SignerFailure>;
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct StoredRevision {
    sequence: u64,
    record_sha256: String,
}

impl StoredRevision {
    #[must_use]
    pub const fn sequence(&self) -> u64 {
        self.sequence
    }

    #[must_use]
    pub fn record_sha256(&self) -> &str {
        &self.record_sha256
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct StoredRecord {
    revision: StoredRevision,
    bytes: Vec<u8>,
}

impl StoredRecord {
    /// Creates one store result from already committed bytes.
    ///
    /// # Errors
    ///
    /// Rejects zero sequence and empty or oversized bytes.
    pub fn committed(sequence: u64, bytes: Vec<u8>) -> Result<Self, StoreFailure> {
        if sequence == 0
            || sequence > MAX_LOG_RECORDS
            || bytes.is_empty()
            || bytes.len() > MAX_RECORD_BYTES
        {
            return Err(StoreFailure::Rejected);
        }
        Ok(Self {
            revision: StoredRevision {
                sequence,
                record_sha256: digest_bytes(&bytes),
            },
            bytes,
        })
    }

    #[must_use]
    pub const fn revision(&self) -> &StoredRevision {
        &self.revision
    }

    #[must_use]
    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }
}

pub trait IssuerStateStore: fmt::Debug {
    /// Loads every immutable record in contiguous sequence order.
    ///
    /// # Errors
    ///
    /// Rejects malformed history and distinguishes storage unavailability.
    fn load_all(&mut self) -> Result<Vec<StoredRecord>, StoreFailure>;

    /// Appends one immutable record only if the exact expected revision is still current.
    ///
    /// # Errors
    ///
    /// Returns conflict for concurrent state, rejected for invalid bytes and unavailable for I/O.
    fn append(
        &mut self,
        expected: Option<&StoredRevision>,
        bytes: &[u8],
    ) -> Result<StoredRecord, StoreFailure>;
}

/// Immutable record-per-file state store with no-overwrite publication.
pub struct AppendOnlyIssuerStateStore {
    root: PathBuf,
}

impl fmt::Debug for AppendOnlyIssuerStateStore {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AppendOnlyIssuerStateStore")
            .field("root", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl AppendOnlyIssuerStateStore {
    /// Opens or creates one dedicated non-linked directory for issuer records.
    ///
    /// # Errors
    ///
    /// Rejects an empty, linked or non-directory root and unavailable filesystem operations.
    pub fn new(root: impl AsRef<Path>) -> Result<Self, StoreFailure> {
        let requested = root.as_ref();
        if requested.as_os_str().is_empty() {
            return Err(StoreFailure::Rejected);
        }
        if requested.exists() {
            require_plain_directory(requested)?;
        } else {
            fs::create_dir_all(requested).map_err(|_| StoreFailure::Unavailable)?;
            require_plain_directory(requested)?;
        }
        let root = requested
            .canonicalize()
            .map_err(|_| StoreFailure::Unavailable)?;
        Ok(Self { root })
    }

    fn scan(&self) -> Result<Vec<StoredRecord>, StoreFailure> {
        let mut records = Vec::new();
        let mut temporary_count = 0_usize;
        for entry in fs::read_dir(&self.root).map_err(|_| StoreFailure::Unavailable)? {
            let entry = entry.map_err(|_| StoreFailure::Unavailable)?;
            let file_type = entry.file_type().map_err(|_| StoreFailure::Unavailable)?;
            let name = entry
                .file_name()
                .into_string()
                .map_err(|_| StoreFailure::Rejected)?;
            if name.starts_with(".pending-") {
                if !valid_temporary_name(&name) || !file_type.is_file() {
                    return Err(StoreFailure::Rejected);
                }
                let length = entry
                    .metadata()
                    .map_err(|_| StoreFailure::Unavailable)?
                    .len();
                if length > MAX_RECORD_BYTES as u64 {
                    return Err(StoreFailure::Rejected);
                }
                temporary_count = temporary_count
                    .checked_add(1)
                    .ok_or(StoreFailure::Rejected)?;
                if temporary_count > MAX_TEMP_FILES {
                    return Err(StoreFailure::Rejected);
                }
                continue;
            }
            if !file_type.is_file() {
                return Err(StoreFailure::Rejected);
            }
            let sequence = parse_record_name(&name)?;
            if sequence == 0 || sequence > MAX_LOG_RECORDS {
                return Err(StoreFailure::Rejected);
            }
            let mut file = File::open(entry.path()).map_err(|_| StoreFailure::Unavailable)?;
            let length = file
                .metadata()
                .map_err(|_| StoreFailure::Unavailable)?
                .len();
            if length == 0 || length > MAX_RECORD_BYTES as u64 {
                return Err(StoreFailure::Rejected);
            }
            let mut bytes =
                Vec::with_capacity(usize::try_from(length).map_err(|_| StoreFailure::Rejected)?);
            file.read_to_end(&mut bytes)
                .map_err(|_| StoreFailure::Unavailable)?;
            records.push(StoredRecord::committed(sequence, bytes)?);
            if records.len() > usize::try_from(MAX_LOG_RECORDS).unwrap_or(usize::MAX) {
                return Err(StoreFailure::Rejected);
            }
        }
        records.sort_by_key(|record| record.revision.sequence);
        for (index, record) in records.iter().enumerate() {
            let expected = u64::try_from(index)
                .map_err(|_| StoreFailure::Rejected)?
                .checked_add(1)
                .ok_or(StoreFailure::Rejected)?;
            if record.revision.sequence != expected {
                return Err(StoreFailure::Rejected);
            }
        }
        Ok(records)
    }
}

impl IssuerStateStore for AppendOnlyIssuerStateStore {
    fn load_all(&mut self) -> Result<Vec<StoredRecord>, StoreFailure> {
        self.scan()
    }

    fn append(
        &mut self,
        expected: Option<&StoredRevision>,
        bytes: &[u8],
    ) -> Result<StoredRecord, StoreFailure> {
        if bytes.is_empty() || bytes.len() > MAX_RECORD_BYTES {
            return Err(StoreFailure::Rejected);
        }
        let records = self.load_all()?;
        if records.last().map(StoredRecord::revision) != expected {
            return Err(StoreFailure::Conflict);
        }
        let sequence = expected.map_or(Ok(1), |revision| {
            revision
                .sequence
                .checked_add(1)
                .ok_or(StoreFailure::Rejected)
        })?;
        if sequence > MAX_LOG_RECORDS {
            return Err(StoreFailure::Rejected);
        }
        // The sequence-only publication path is the compare-and-swap slot. Including the
        // content digest in this name would let concurrent writers publish two distinct files
        // for the same sequence after both observed the same predecessor.
        let final_path = self.root.join(format!("{sequence:020}.json"));
        let mut nonce = [0_u8; 16];
        getrandom::fill(&mut nonce).map_err(|_| StoreFailure::Unavailable)?;
        let temporary_path = self.root.join(format!(
            ".pending-{sequence:020}-{}.tmp",
            hex::encode(nonce)
        ));
        let mut temporary = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary_path)
            .map_err(|_| StoreFailure::Unavailable)?;
        if temporary
            .write_all(bytes)
            .and_then(|()| temporary.sync_all())
            .is_err()
        {
            let _ = fs::remove_file(&temporary_path);
            return Err(StoreFailure::Unavailable);
        }
        drop(temporary);
        if fs::hard_link(&temporary_path, &final_path).is_err() {
            let _ = fs::remove_file(&temporary_path);
            return if final_path.exists() {
                Err(StoreFailure::Conflict)
            } else {
                Err(StoreFailure::Unavailable)
            };
        }
        let _ = fs::remove_file(&temporary_path);
        StoredRecord::committed(sequence, bytes.to_vec())
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum CredentialOperation {
    Issue,
    Refresh,
    Rotate,
    Revoke,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct LifecycleRequest {
    schema_version: String,
    operation: CredentialOperation,
    operation_id: String,
    binding_sha256: String,
    expected_generation: u64,
    expected_key_generation: u64,
    prior_credential_sha256: Option<String>,
    requested_at: u64,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "state", rename_all = "snake_case", deny_unknown_fields)]
enum IssuerState {
    Absent,
    Active {
        generation: u64,
        key_generation: u64,
        credential_sha256: String,
    },
    Revoked {
        generation: u64,
        key_generation: u64,
        prior_credential_sha256: String,
        revocation_receipt_sha256: String,
    },
}

impl fmt::Debug for IssuerState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let state = match self {
            Self::Absent => "absent",
            Self::Active { .. } => "active",
            Self::Revoked { .. } => "revoked",
        };
        formatter
            .debug_struct("IssuerState")
            .field("state", &state)
            .field("details", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum RecordKind {
    Transition,
    Replay,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct RequestSummary {
    operation: CredentialOperation,
    operation_id_sha256: String,
    request_sha256: String,
    expected_generation: u64,
    expected_key_generation: u64,
    prior_credential_sha256: Option<String>,
    requested_at: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct DurableRecord {
    schema_version: String,
    sequence: u64,
    previous_record_sha256: Option<String>,
    policy_binding_sha256: String,
    kind: RecordKind,
    client_assertion_jti_sha256: String,
    request: RequestSummary,
    before: IssuerState,
    after: IssuerState,
    response_sha256: String,
    signing_key_id_sha256: String,
}

struct RestoredHistory {
    records: Vec<DurableRecord>,
    latest_revision: Option<StoredRevision>,
    state: IssuerState,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ExchangeStatus {
    Completed,
    DefinitiveRejection,
    Unavailable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum IssuerBindScope {
    ExplicitDeployment,
    LoopbackQualification,
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum IssuerTlsServerFailure {
    #[error("credential issuer TLS server configuration or request was rejected")]
    Rejected,
    #[error("credential issuer TLS server is unavailable")]
    Unavailable,
}

/// Opaque TLS 1.3-only server configuration with one bounded certificate chain.
pub struct IssuerTlsServerConfig {
    inner: Arc<ServerConfig>,
    leaf_certificate_sha256: [u8; 32],
    certificate_count: usize,
}

impl fmt::Debug for IssuerTlsServerConfig {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IssuerTlsServerConfig")
            .field("tls_version", &"TLS1.3")
            .field("certificate_count", &self.certificate_count)
            .field("certificate_chain", &"<redacted>")
            .field("private_key", &"<redacted>")
            .field("leaf_certificate_sha256", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl IssuerTlsServerConfig {
    /// Builds a TLS 1.3-only server configuration without ambient client authentication.
    ///
    /// Client authentication is performed by the request-bound Ed25519 assertion in the issuer
    /// protocol. The exact leaf digest is exposed separately for out-of-band client pinning.
    ///
    /// # Errors
    ///
    /// Rejects empty or oversized certificate/key material and any invalid rustls key pairing.
    pub fn new(
        certificate_chain: Vec<CertificateDer<'static>>,
        private_key: PrivateKeyDer<'static>,
    ) -> Result<Self, IssuerTlsServerFailure> {
        let certificate_count = certificate_chain.len();
        let chain_bytes = certificate_chain
            .iter()
            .try_fold(0_usize, |total, certificate| {
                if certificate.is_empty() || certificate.len() > MAX_CERTIFICATE_BYTES {
                    return Err(IssuerTlsServerFailure::Rejected);
                }
                total
                    .checked_add(certificate.len())
                    .ok_or(IssuerTlsServerFailure::Rejected)
            })?;
        if certificate_count == 0
            || certificate_count > MAX_CERTIFICATES
            || chain_bytes > MAX_CERTIFICATE_CHAIN_BYTES
            || private_key.secret_der().is_empty()
            || private_key.secret_der().len() > MAX_PRIVATE_KEY_BYTES
        {
            return Err(IssuerTlsServerFailure::Rejected);
        }
        let leaf_certificate_sha256: [u8; 32] =
            Sha256::digest(certificate_chain[0].as_ref()).into();
        let provider = Arc::new(rustls::crypto::ring::default_provider());
        let inner = ServerConfig::builder_with_provider(provider)
            .with_protocol_versions(&[&version::TLS13])
            .map_err(|_| IssuerTlsServerFailure::Rejected)?
            .with_no_client_auth()
            .with_single_cert(certificate_chain, private_key)
            .map_err(|_| IssuerTlsServerFailure::Rejected)?;
        Ok(Self {
            inner: Arc::new(inner),
            leaf_certificate_sha256,
            certificate_count,
        })
    }

    #[must_use]
    pub const fn leaf_certificate_sha256(&self) -> [u8; 32] {
        self.leaf_certificate_sha256
    }
}

pub struct IssuerExchange {
    status: ExchangeStatus,
    payload: Option<Zeroizing<Vec<u8>>>,
}

impl fmt::Debug for IssuerExchange {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IssuerExchange")
            .field("status", &self.status)
            .field("payload", &"<redacted>")
            .field(
                "payload_bytes",
                &self.payload.as_ref().map_or(0, |payload| payload.len()),
            )
            .finish_non_exhaustive()
    }
}

impl IssuerExchange {
    #[must_use]
    pub const fn status(&self) -> ExchangeStatus {
        self.status
    }

    pub fn with_payload<R>(&self, operation: impl FnOnce(Option<&[u8]>) -> R) -> R {
        operation(self.payload.as_deref().map(Vec::as_slice))
    }
}

/// One exact issuer state machine. Every accepted assertion is durable before a response returns.
pub struct CredentialIssuer<S, T> {
    policy: IssuerPolicy,
    store: S,
    signer: T,
}

/// Independently bound TLS issuer service that accepts exactly one framed exchange per call.
pub struct CredentialIssuerTlsServer<S, T> {
    listener: TcpListener,
    issuer: CredentialIssuer<S, T>,
    config: IssuerTlsServerConfig,
    bind_scope: IssuerBindScope,
    io_timeout: Duration,
}

impl<S, T> fmt::Debug for CredentialIssuerTlsServer<S, T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CredentialIssuerTlsServer")
            .field("local_addr", &"<redacted>")
            .field("issuer", &"<redacted>")
            .field("config", &self.config)
            .field("bind_scope", &self.bind_scope)
            .field("io_timeout", &self.io_timeout)
            .finish_non_exhaustive()
    }
}

impl<S, T> CredentialIssuerTlsServer<S, T> {
    /// Binds an exact deployment or loopback-qualification endpoint.
    ///
    /// Explicit deployment rejects port zero, loopback, unspecified and multicast addresses.
    /// Loopback qualification permits port zero so the OS can allocate an isolated test port.
    ///
    /// # Errors
    ///
    /// Rejects unsafe endpoint/time settings and reports listener failures as unavailable.
    pub fn bind(
        endpoint: SocketAddr,
        bind_scope: IssuerBindScope,
        issuer: CredentialIssuer<S, T>,
        config: IssuerTlsServerConfig,
        io_timeout: Duration,
    ) -> Result<Self, IssuerTlsServerFailure> {
        validate_bind_endpoint(endpoint, bind_scope)?;
        if io_timeout < Duration::from_millis(1) || io_timeout > MAX_IO_TIMEOUT {
            return Err(IssuerTlsServerFailure::Rejected);
        }
        let listener =
            TcpListener::bind(endpoint).map_err(|_| IssuerTlsServerFailure::Unavailable)?;
        Ok(Self {
            listener,
            issuer,
            config,
            bind_scope,
            io_timeout,
        })
    }

    /// Returns the exact OS-bound endpoint without exposing it through `Debug`.
    ///
    /// # Errors
    ///
    /// Returns unavailable if the listener address cannot be read.
    pub fn local_addr(&self) -> Result<SocketAddr, IssuerTlsServerFailure> {
        self.listener
            .local_addr()
            .map_err(|_| IssuerTlsServerFailure::Unavailable)
    }
}

impl<S, T> fmt::Debug for CredentialIssuer<S, T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CredentialIssuer")
            .field("policy", &self.policy)
            .field("store", &"<redacted>")
            .field("signer", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl<S: IssuerStateStore, T: CredentialTokenSigner> CredentialIssuer<S, T> {
    /// Creates an issuer only when the signer is bound to the exact pinned key ID.
    ///
    /// # Errors
    ///
    /// Rejects signer/policy drift.
    pub fn new(policy: IssuerPolicy, store: S, signer: T) -> Result<Self, IssuerError> {
        if signer.key_id() != policy.signing_key.key_id {
            return Err(IssuerError::Rejected);
        }
        Ok(Self {
            policy,
            store,
            signer,
        })
    }

    /// Handles one issuer exchange with a server-supplied Unix time.
    ///
    /// Client-caused failures become an authenticated request-bound rejection. Storage, signer,
    /// serialization and state-integrity failures remain unavailable and never restore client
    /// pending state.
    #[must_use]
    pub fn exchange(
        &mut self,
        authorization_header: &str,
        request_bytes: &[u8],
        now: u64,
    ) -> IssuerExchange {
        let request_sha256 = digest_bytes(request_bytes);
        match self.process(authorization_header, request_bytes, now) {
            Ok(payload) => IssuerExchange {
                status: ExchangeStatus::Completed,
                payload: Some(payload),
            },
            Err(IssuerError::Rejected) => match rejected_response(&request_sha256) {
                Ok(payload) => IssuerExchange {
                    status: ExchangeStatus::DefinitiveRejection,
                    payload: Some(payload),
                },
                Err(IssuerError::Unavailable | IssuerError::Rejected) => IssuerExchange {
                    status: ExchangeStatus::Unavailable,
                    payload: None,
                },
            },
            Err(IssuerError::Unavailable) => IssuerExchange {
                status: ExchangeStatus::Unavailable,
                payload: None,
            },
        }
    }

    fn process(
        &mut self,
        authorization_header: &str,
        request_bytes: &[u8],
        now: u64,
    ) -> Result<Zeroizing<Vec<u8>>, IssuerError> {
        if now == 0 || request_bytes.is_empty() || request_bytes.len() > MAX_REQUEST_BYTES {
            return Err(IssuerError::Rejected);
        }
        let request_sha256 = digest_bytes(request_bytes);
        let assertion_jti_sha256 =
            verify_client_assertion(&self.policy, authorization_header, &request_sha256, now)?;
        let request = parse_lifecycle_request(&self.policy, request_bytes, now)?;
        let summary = request_summary(&request, &request_sha256);
        let stored = self.store.load_all().map_err(map_store_internal)?;
        let history = restore_history(&self.policy, &stored)?;

        if let Some(record) = history
            .records
            .iter()
            .find(|record| record.client_assertion_jti_sha256 == assertion_jti_sha256)
        {
            if record.request.request_sha256 != request_sha256 {
                return Err(IssuerError::Rejected);
            }
            return self.rebuild_existing_response(&history, &request, &summary);
        }

        if history
            .records
            .iter()
            .any(|record| record.request.request_sha256 == request_sha256)
        {
            let response = self.rebuild_existing_response(&history, &request, &summary)?;
            let response_sha256 = digest_bytes(&response);
            let record = DurableRecord {
                schema_version: RECORD_SCHEMA.to_owned(),
                sequence: next_sequence(history.latest_revision.as_ref())?,
                previous_record_sha256: history
                    .latest_revision
                    .as_ref()
                    .map(|revision| revision.record_sha256.clone()),
                policy_binding_sha256: self.policy.binding_sha256()?,
                kind: RecordKind::Replay,
                client_assertion_jti_sha256: assertion_jti_sha256,
                request: summary,
                before: history.state.clone(),
                after: history.state,
                response_sha256,
                signing_key_id_sha256: digest_bytes(self.policy.signing_key.key_id.as_bytes()),
            };
            append_record(&mut self.store, history.latest_revision.as_ref(), &record)?;
            return Ok(response);
        }

        if !request_admitted(&history.state, &request) {
            return Err(IssuerError::Rejected);
        }
        let response = self.build_response(&request, &request_sha256)?;
        let after = transition_state(&history.state, &request, &response)?;
        let record = DurableRecord {
            schema_version: RECORD_SCHEMA.to_owned(),
            sequence: next_sequence(history.latest_revision.as_ref())?,
            previous_record_sha256: history
                .latest_revision
                .as_ref()
                .map(|revision| revision.record_sha256.clone()),
            policy_binding_sha256: self.policy.binding_sha256()?,
            kind: RecordKind::Transition,
            client_assertion_jti_sha256: assertion_jti_sha256,
            request: summary,
            before: history.state,
            after,
            response_sha256: digest_bytes(&response),
            signing_key_id_sha256: digest_bytes(self.policy.signing_key.key_id.as_bytes()),
        };
        append_record(&mut self.store, history.latest_revision.as_ref(), &record)?;
        Ok(response)
    }

    fn rebuild_existing_response(
        &mut self,
        history: &RestoredHistory,
        request: &LifecycleRequest,
        summary: &RequestSummary,
    ) -> Result<Zeroizing<Vec<u8>>, IssuerError> {
        let transition = history
            .records
            .iter()
            .find(|record| {
                record.kind == RecordKind::Transition
                    && record.request.request_sha256 == summary.request_sha256
            })
            .ok_or(IssuerError::Unavailable)?;
        if transition.request != *summary {
            return Err(IssuerError::Rejected);
        }
        let response = self.build_response(request, &summary.request_sha256)?;
        if digest_bytes(&response) != transition.response_sha256 {
            return Err(IssuerError::Unavailable);
        }
        Ok(response)
    }

    fn build_response(
        &mut self,
        request: &LifecycleRequest,
        request_sha256: &str,
    ) -> Result<Zeroizing<Vec<u8>>, IssuerError> {
        let response = match request.operation {
            CredentialOperation::Issue
            | CredentialOperation::Refresh
            | CredentialOperation::Rotate => {
                let expires_at = request
                    .requested_at
                    .checked_add(self.policy.access_lifetime_seconds)
                    .ok_or(IssuerError::Unavailable)?;
                let claims = AccessClaims {
                    iss: &self.policy.service_issuer,
                    sub: &self.policy.service_subject,
                    aud: &self.policy.service_audience,
                    scope: SERVICE_SCOPE,
                    iat: request.requested_at,
                    nbf: request.requested_at,
                    exp: expires_at,
                    jti: format!("credential-{}", &request_sha256[..32]),
                    operation_id: &request.operation_id,
                    request_sha256,
                    generation: request.expected_generation,
                    key_generation: request.expected_key_generation,
                };
                let token =
                    sign_compact_jws(&self.policy, &mut self.signer, ACCESS_TOKEN_TYPE, &claims)?;
                WireResponse::Access {
                    schema_version: ISSUER_RESPONSE_SCHEMA.to_owned(),
                    request_sha256: request_sha256.to_owned(),
                    token,
                }
            }
            CredentialOperation::Revoke => {
                let prior = request
                    .prior_credential_sha256
                    .as_deref()
                    .ok_or(IssuerError::Rejected)?;
                let claims = RevocationClaims {
                    iss: &self.policy.service_issuer,
                    sub: &self.policy.service_subject,
                    aud: &self.policy.service_audience,
                    iat: request.requested_at,
                    jti: format!("revocation-{}", &request_sha256[..32]),
                    operation_id: &request.operation_id,
                    request_sha256,
                    generation: request.expected_generation,
                    key_generation: request.expected_key_generation,
                    credential_sha256: prior,
                    revoked: true,
                };
                let receipt =
                    sign_compact_jws(&self.policy, &mut self.signer, REVOCATION_TYPE, &claims)?;
                WireResponse::Revocation {
                    schema_version: ISSUER_RESPONSE_SCHEMA.to_owned(),
                    request_sha256: request_sha256.to_owned(),
                    receipt,
                }
            }
        };
        let bytes = serde_json::to_vec(&response).map_err(|_| IssuerError::Unavailable)?;
        if bytes.is_empty() || bytes.len() > MAX_RESPONSE_BYTES {
            return Err(IssuerError::Unavailable);
        }
        Ok(Zeroizing::new(bytes))
    }
}

/// Reads, handles and writes one distinct credential-issuer frame on an already authenticated
/// transport stream.
///
/// # Errors
///
/// Returns only bounded framing failures. Service unavailability is encoded as an empty
/// unavailable response and client-caused rejection as a canonical request-bound payload.
pub fn serve_one<S, T, W>(
    issuer: &mut CredentialIssuer<S, T>,
    stream: &mut W,
    now: u64,
) -> Result<(), FrameError>
where
    S: IssuerStateStore,
    T: CredentialTokenSigner,
    W: Read + Write,
{
    serve_exchange(issuer, stream, now).map(|_| ())
}

fn serve_exchange<S, T, W>(
    issuer: &mut CredentialIssuer<S, T>,
    stream: &mut W,
    now: u64,
) -> Result<ExchangeStatus, FrameError>
where
    S: IssuerStateStore,
    T: CredentialTokenSigner,
    W: Read + Write,
{
    let request = read_request(stream)?;
    let exchange = request
        .with_authorization(|authorization| issuer.exchange(authorization, request.payload(), now));
    let status = exchange.status;
    match status {
        ExchangeStatus::Completed | ExchangeStatus::DefinitiveRejection => {
            exchange.with_payload(|payload| {
                write_response(
                    stream,
                    ResponseStatus::Completed,
                    payload.ok_or(FrameError::Rejected)?,
                )
            })
        }
        ExchangeStatus::Unavailable => write_response(stream, ResponseStatus::Unavailable, &[]),
    }?;
    Ok(status)
}

impl<S, T> CredentialIssuerTlsServer<S, T>
where
    S: IssuerStateStore,
    T: CredentialTokenSigner,
{
    /// Accepts and serves exactly one TLS 1.3 credential exchange.
    ///
    /// # Errors
    ///
    /// Rejects zero time, a non-loopback peer in qualification mode, malformed frames and TLS
    /// protocol failures. Listener, timeout and write failures are unavailable.
    pub fn serve_one_at(&mut self, now: u64) -> Result<ExchangeStatus, IssuerTlsServerFailure> {
        if now == 0 {
            return Err(IssuerTlsServerFailure::Rejected);
        }
        let (socket, peer) = self
            .listener
            .accept()
            .map_err(|_| IssuerTlsServerFailure::Unavailable)?;
        if self.bind_scope == IssuerBindScope::LoopbackQualification && !peer.ip().is_loopback() {
            return Err(IssuerTlsServerFailure::Rejected);
        }
        socket
            .set_read_timeout(Some(self.io_timeout))
            .and_then(|()| socket.set_write_timeout(Some(self.io_timeout)))
            .map_err(|_| IssuerTlsServerFailure::Unavailable)?;
        let connection = ServerConnection::new(Arc::clone(&self.config.inner))
            .map_err(|_| IssuerTlsServerFailure::Unavailable)?;
        let mut stream = StreamOwned::new(connection, socket);
        let status =
            serve_exchange(&mut self.issuer, &mut stream, now).map_err(map_server_frame)?;
        stream.conn.send_close_notify();
        stream
            .flush()
            .and_then(|()| stream.sock.shutdown(Shutdown::Write))
            .map_err(|_| IssuerTlsServerFailure::Unavailable)?;
        Ok(status)
    }
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct JwtHeader {
    alg: String,
    typ: String,
    kid: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ClientAssertionClaims {
    iss: String,
    sub: String,
    aud: String,
    scope: String,
    iat: u64,
    nbf: u64,
    exp: u64,
    jti: String,
    request_sha256: String,
}

#[derive(Serialize)]
struct AccessClaims<'a> {
    iss: &'a str,
    sub: &'a str,
    aud: &'a str,
    scope: &'static str,
    iat: u64,
    nbf: u64,
    exp: u64,
    jti: String,
    operation_id: &'a str,
    request_sha256: &'a str,
    generation: u64,
    key_generation: u64,
}

#[derive(Serialize)]
struct RevocationClaims<'a> {
    iss: &'a str,
    sub: &'a str,
    aud: &'a str,
    iat: u64,
    jti: String,
    operation_id: &'a str,
    request_sha256: &'a str,
    generation: u64,
    key_generation: u64,
    credential_sha256: &'a str,
    revoked: bool,
}

#[derive(Deserialize, Serialize)]
#[serde(tag = "outcome", rename_all = "snake_case", deny_unknown_fields)]
enum WireResponse {
    Access {
        schema_version: String,
        request_sha256: String,
        token: String,
    },
    Revocation {
        schema_version: String,
        request_sha256: String,
        receipt: String,
    },
    Rejected {
        schema_version: String,
        request_sha256: String,
    },
}

fn verify_client_assertion(
    policy: &IssuerPolicy,
    authorization_header: &str,
    request_sha256: &str,
    now: u64,
) -> Result<String, IssuerError> {
    let compact = authorization_header
        .strip_prefix("Bearer ")
        .ok_or(IssuerError::Rejected)?;
    if compact.is_empty()
        || compact.len() > MAX_ASSERTION_BYTES
        || !compact.is_ascii()
        || compact.contains('=')
    {
        return Err(IssuerError::Rejected);
    }
    let mut segments = compact.split('.');
    let header_segment = segments.next().ok_or(IssuerError::Rejected)?;
    let claims_segment = segments.next().ok_or(IssuerError::Rejected)?;
    let signature_segment = segments.next().ok_or(IssuerError::Rejected)?;
    if header_segment.is_empty()
        || claims_segment.is_empty()
        || signature_segment.is_empty()
        || segments.next().is_some()
    {
        return Err(IssuerError::Rejected);
    }
    let header_bytes = decode_segment(header_segment, MAX_HEADER_BYTES)?;
    let claims_bytes = Zeroizing::new(decode_segment(claims_segment, MAX_CLAIMS_BYTES)?);
    let signature = Zeroizing::new(decode_segment(signature_segment, 64)?);
    if signature.len() != 64 {
        return Err(IssuerError::Rejected);
    }
    let header: JwtHeader =
        serde_json::from_slice(&header_bytes).map_err(|_| IssuerError::Rejected)?;
    require_canonical_json(&header_bytes, &header)?;
    if header.alg != "EdDSA" || header.typ != CLIENT_ASSERTION_TYPE {
        return Err(IssuerError::Rejected);
    }
    validate_token_identifier(&header.kid, 1, MAX_KEY_ID_BYTES)?;
    let key = policy
        .client_key(&header.kid)
        .ok_or(IssuerError::Rejected)?;
    let signing_input = format!("{header_segment}.{claims_segment}");
    UnparsedPublicKey::new(&ED25519, key.public_key)
        .verify(signing_input.as_bytes(), &signature)
        .map_err(|_| IssuerError::Rejected)?;
    let claims: ClientAssertionClaims =
        serde_json::from_slice(&claims_bytes).map_err(|_| IssuerError::Rejected)?;
    require_canonical_json(&claims_bytes, &claims)?;
    validate_token_identifier(&claims.jti, MIN_JTI_BYTES, MAX_JTI_BYTES)?;
    let lifetime = claims
        .exp
        .checked_sub(claims.iat)
        .ok_or(IssuerError::Rejected)?;
    let latest = now
        .checked_add(policy.clock_skew_seconds)
        .ok_or(IssuerError::Unavailable)?;
    let expiry_with_skew = claims
        .exp
        .checked_add(policy.clock_skew_seconds)
        .ok_or(IssuerError::Rejected)?;
    if claims.iss != policy.client_issuer
        || claims.sub != policy.client_subject
        || claims.aud != policy.client_audience
        || claims.scope != CLIENT_SCOPE
        || claims.request_sha256 != request_sha256
        || !is_hex64(&claims.request_sha256)
        || claims.iat == 0
        || claims.nbf != claims.iat
        || claims.iat > latest
        || claims.nbf > latest
        || expiry_with_skew <= now
        || lifetime == 0
        || lifetime > policy.maximum_assertion_lifetime_seconds
    {
        return Err(IssuerError::Rejected);
    }
    Ok(digest_bytes(claims.jti.as_bytes()))
}

fn parse_lifecycle_request(
    policy: &IssuerPolicy,
    request_bytes: &[u8],
    now: u64,
) -> Result<LifecycleRequest, IssuerError> {
    let request: LifecycleRequest =
        serde_json::from_slice(request_bytes).map_err(|_| IssuerError::Rejected)?;
    require_canonical_json(request_bytes, &request)?;
    validate_token_identifier(
        &request.operation_id,
        MIN_OPERATION_ID_BYTES,
        MAX_OPERATION_ID_BYTES,
    )?;
    let latest = now
        .checked_add(policy.clock_skew_seconds)
        .ok_or(IssuerError::Unavailable)?;
    let oldest = request
        .requested_at
        .checked_add(policy.maximum_request_age_seconds)
        .and_then(|value| value.checked_add(policy.clock_skew_seconds))
        .ok_or(IssuerError::Rejected)?;
    if request.schema_version != LIFECYCLE_REQUEST_SCHEMA
        || request.binding_sha256 != policy.lifecycle_binding_sha256
        || request.expected_generation == 0
        || request.expected_key_generation == 0
        || request.expected_key_generation > request.expected_generation
        || request.requested_at == 0
        || request.requested_at > latest
        || oldest < now
        || match request.operation {
            CredentialOperation::Issue => request.prior_credential_sha256.is_some(),
            CredentialOperation::Refresh
            | CredentialOperation::Rotate
            | CredentialOperation::Revoke => request
                .prior_credential_sha256
                .as_deref()
                .is_none_or(|digest| !is_hex64(digest)),
        }
    {
        return Err(IssuerError::Rejected);
    }
    Ok(request)
}

fn restore_history(
    policy: &IssuerPolicy,
    stored: &[StoredRecord],
) -> Result<RestoredHistory, IssuerError> {
    if stored.len() > usize::try_from(MAX_LOG_RECORDS).unwrap_or(usize::MAX) {
        return Err(IssuerError::Unavailable);
    }
    let policy_binding_sha256 = policy.binding_sha256()?;
    let signing_key_id_sha256 = digest_bytes(policy.signing_key.key_id.as_bytes());
    let mut state = IssuerState::Absent;
    let mut records = Vec::with_capacity(stored.len());
    let mut previous_sha256: Option<String> = None;
    let mut assertion_jtis = BTreeMap::<String, String>::new();
    let mut transitions = BTreeMap::<String, (RequestSummary, String)>::new();
    for (index, stored_record) in stored.iter().enumerate() {
        let expected_sequence = u64::try_from(index)
            .map_err(|_| IssuerError::Unavailable)?
            .checked_add(1)
            .ok_or(IssuerError::Unavailable)?;
        if stored_record.revision.sequence != expected_sequence
            || digest_bytes(stored_record.bytes()) != stored_record.revision.record_sha256
        {
            return Err(IssuerError::Unavailable);
        }
        let record: DurableRecord =
            serde_json::from_slice(stored_record.bytes()).map_err(|_| IssuerError::Unavailable)?;
        let canonical = serde_json::to_vec(&record).map_err(|_| IssuerError::Unavailable)?;
        if canonical != stored_record.bytes()
            || record.schema_version != RECORD_SCHEMA
            || record.sequence != expected_sequence
            || record.previous_record_sha256 != previous_sha256
            || record.policy_binding_sha256 != policy_binding_sha256
            || record.signing_key_id_sha256 != signing_key_id_sha256
            || record.before != state
            || !is_hex64(&record.client_assertion_jti_sha256)
            || !is_hex64(&record.request.operation_id_sha256)
            || !is_hex64(&record.request.request_sha256)
            || !is_hex64(&record.response_sha256)
            || record.request.requested_at == 0
        {
            return Err(IssuerError::Unavailable);
        }
        if assertion_jtis
            .insert(
                record.client_assertion_jti_sha256.clone(),
                record.request.request_sha256.clone(),
            )
            .is_some()
        {
            return Err(IssuerError::Unavailable);
        }
        match record.kind {
            RecordKind::Transition => {
                if transitions.contains_key(&record.request.request_sha256)
                    || !valid_transition(&record.before, &record.request, &record.after)
                {
                    return Err(IssuerError::Unavailable);
                }
                transitions.insert(
                    record.request.request_sha256.clone(),
                    (record.request.clone(), record.response_sha256.clone()),
                );
            }
            RecordKind::Replay => {
                let Some((summary, response_sha256)) =
                    transitions.get(&record.request.request_sha256)
                else {
                    return Err(IssuerError::Unavailable);
                };
                if summary != &record.request
                    || response_sha256 != &record.response_sha256
                    || record.before != record.after
                {
                    return Err(IssuerError::Unavailable);
                }
            }
        }
        state = record.after.clone();
        previous_sha256 = Some(stored_record.revision.record_sha256.clone());
        records.push(record);
    }
    Ok(RestoredHistory {
        records,
        latest_revision: stored.last().map(|record| record.revision.clone()),
        state,
    })
}

fn valid_transition(before: &IssuerState, request: &RequestSummary, after: &IssuerState) -> bool {
    match (before, request.operation, after) {
        (
            IssuerState::Absent,
            CredentialOperation::Issue,
            IssuerState::Active {
                generation,
                key_generation,
                credential_sha256,
            },
        ) => {
            request.expected_generation == 1
                && request.expected_key_generation == 1
                && request.prior_credential_sha256.is_none()
                && *generation == 1
                && *key_generation == 1
                && is_hex64(credential_sha256)
        }
        (
            IssuerState::Active {
                generation,
                key_generation,
                credential_sha256,
            },
            CredentialOperation::Refresh,
            IssuerState::Active {
                generation: next_generation,
                key_generation: next_key_generation,
                credential_sha256: next_credential_sha256,
            },
        ) => {
            generation.checked_add(1) == Some(request.expected_generation)
                && request.expected_key_generation == *key_generation
                && request.prior_credential_sha256.as_deref() == Some(credential_sha256.as_str())
                && *next_generation == request.expected_generation
                && *next_key_generation == request.expected_key_generation
                && is_hex64(next_credential_sha256)
                && next_credential_sha256 != credential_sha256
        }
        (
            IssuerState::Active {
                generation,
                key_generation,
                credential_sha256,
            },
            CredentialOperation::Rotate,
            IssuerState::Active {
                generation: next_generation,
                key_generation: next_key_generation,
                credential_sha256: next_credential_sha256,
            },
        ) => {
            generation.checked_add(1) == Some(request.expected_generation)
                && key_generation.checked_add(1) == Some(request.expected_key_generation)
                && request.prior_credential_sha256.as_deref() == Some(credential_sha256.as_str())
                && *next_generation == request.expected_generation
                && *next_key_generation == request.expected_key_generation
                && is_hex64(next_credential_sha256)
                && next_credential_sha256 != credential_sha256
        }
        (
            IssuerState::Active {
                generation,
                key_generation,
                credential_sha256,
            },
            CredentialOperation::Revoke,
            IssuerState::Revoked {
                generation: revoked_generation,
                key_generation: revoked_key_generation,
                prior_credential_sha256,
                revocation_receipt_sha256,
            },
        ) => {
            request.expected_generation == *generation
                && request.expected_key_generation == *key_generation
                && request.prior_credential_sha256.as_deref() == Some(credential_sha256.as_str())
                && *revoked_generation == *generation
                && *revoked_key_generation == *key_generation
                && prior_credential_sha256 == credential_sha256
                && is_hex64(revocation_receipt_sha256)
        }
        (IssuerState::Absent | IssuerState::Revoked { .. }, _, _)
        | (IssuerState::Active { .. }, CredentialOperation::Issue, _)
        | (IssuerState::Active { .. }, _, IssuerState::Absent | IssuerState::Revoked { .. })
        | (IssuerState::Active { .. }, _, IssuerState::Active { .. }) => false,
    }
}

fn request_admitted(before: &IssuerState, request: &LifecycleRequest) -> bool {
    match (before, request.operation) {
        (IssuerState::Absent, CredentialOperation::Issue) => {
            request.expected_generation == 1
                && request.expected_key_generation == 1
                && request.prior_credential_sha256.is_none()
        }
        (
            IssuerState::Active {
                generation,
                key_generation,
                credential_sha256,
            },
            CredentialOperation::Refresh,
        ) => {
            generation.checked_add(1) == Some(request.expected_generation)
                && request.expected_key_generation == *key_generation
                && request.prior_credential_sha256.as_deref() == Some(credential_sha256.as_str())
        }
        (
            IssuerState::Active {
                generation,
                key_generation,
                credential_sha256,
            },
            CredentialOperation::Rotate,
        ) => {
            generation.checked_add(1) == Some(request.expected_generation)
                && key_generation.checked_add(1) == Some(request.expected_key_generation)
                && request.prior_credential_sha256.as_deref() == Some(credential_sha256.as_str())
        }
        (
            IssuerState::Active {
                generation,
                key_generation,
                credential_sha256,
            },
            CredentialOperation::Revoke,
        ) => {
            request.expected_generation == *generation
                && request.expected_key_generation == *key_generation
                && request.prior_credential_sha256.as_deref() == Some(credential_sha256.as_str())
        }
        (IssuerState::Absent | IssuerState::Revoked { .. }, _)
        | (IssuerState::Active { .. }, CredentialOperation::Issue) => false,
    }
}

fn transition_state(
    before: &IssuerState,
    request: &LifecycleRequest,
    response: &[u8],
) -> Result<IssuerState, IssuerError> {
    let decoded: WireResponse =
        serde_json::from_slice(response).map_err(|_| IssuerError::Unavailable)?;
    let after = match decoded {
        WireResponse::Access { token, .. } => IssuerState::Active {
            generation: request.expected_generation,
            key_generation: request.expected_key_generation,
            credential_sha256: digest_bytes(token.as_bytes()),
        },
        WireResponse::Revocation { receipt, .. } => IssuerState::Revoked {
            generation: request.expected_generation,
            key_generation: request.expected_key_generation,
            prior_credential_sha256: request
                .prior_credential_sha256
                .clone()
                .ok_or(IssuerError::Rejected)?,
            revocation_receipt_sha256: digest_bytes(receipt.as_bytes()),
        },
        WireResponse::Rejected { .. } => return Err(IssuerError::Unavailable),
    };
    let summary = request_summary(request, &digest_bytes_from_response_binding(response)?);
    if !valid_transition(before, &summary, &after) {
        return Err(IssuerError::Rejected);
    }
    Ok(after)
}

fn digest_bytes_from_response_binding(response: &[u8]) -> Result<String, IssuerError> {
    let decoded: WireResponse =
        serde_json::from_slice(response).map_err(|_| IssuerError::Unavailable)?;
    match decoded {
        WireResponse::Access { request_sha256, .. }
        | WireResponse::Revocation { request_sha256, .. }
        | WireResponse::Rejected { request_sha256, .. } => Ok(request_sha256),
    }
}

fn request_summary(request: &LifecycleRequest, request_sha256: &str) -> RequestSummary {
    RequestSummary {
        operation: request.operation,
        operation_id_sha256: digest_bytes(request.operation_id.as_bytes()),
        request_sha256: request_sha256.to_owned(),
        expected_generation: request.expected_generation,
        expected_key_generation: request.expected_key_generation,
        prior_credential_sha256: request.prior_credential_sha256.clone(),
        requested_at: request.requested_at,
    }
}

fn append_record(
    store: &mut impl IssuerStateStore,
    expected: Option<&StoredRevision>,
    record: &DurableRecord,
) -> Result<(), IssuerError> {
    let bytes = serde_json::to_vec(record).map_err(|_| IssuerError::Unavailable)?;
    if bytes.is_empty() || bytes.len() > MAX_RECORD_BYTES {
        return Err(IssuerError::Unavailable);
    }
    let committed = store.append(expected, &bytes).map_err(map_store_internal)?;
    if committed.bytes() != bytes
        || committed.revision.sequence != record.sequence
        || committed.revision.record_sha256 != digest_bytes(&bytes)
    {
        return Err(IssuerError::Unavailable);
    }
    Ok(())
}

fn sign_compact_jws(
    policy: &IssuerPolicy,
    signer: &mut impl CredentialTokenSigner,
    token_type: &str,
    claims: &impl Serialize,
) -> Result<String, IssuerError> {
    if signer.key_id() != policy.signing_key.key_id {
        return Err(IssuerError::Unavailable);
    }
    let header = serde_json::to_vec(&JwtHeader {
        alg: "EdDSA".to_owned(),
        typ: token_type.to_owned(),
        kid: policy.signing_key.key_id.clone(),
    })
    .map_err(|_| IssuerError::Unavailable)?;
    let claims = Zeroizing::new(serde_json::to_vec(claims).map_err(|_| IssuerError::Unavailable)?);
    if header.len() > MAX_HEADER_BYTES || claims.len() > MAX_CLAIMS_BYTES {
        return Err(IssuerError::Unavailable);
    }
    let signing_input = Zeroizing::new(format!(
        "{}.{}",
        URL_SAFE_NO_PAD.encode(header),
        URL_SAFE_NO_PAD.encode(claims.as_slice())
    ));
    let signature = Zeroizing::new(
        signer
            .sign(signing_input.as_bytes())
            .map_err(|_| IssuerError::Unavailable)?,
    );
    UnparsedPublicKey::new(&ED25519, policy.signing_key.public_key)
        .verify(signing_input.as_bytes(), signature.as_slice())
        .map_err(|_| IssuerError::Unavailable)?;
    let token = format!(
        "{}.{}",
        signing_input.as_str(),
        URL_SAFE_NO_PAD.encode(signature.as_slice())
    );
    if token.is_empty() || token.len() > 2_560 || token.contains('=') || !token.is_ascii() {
        return Err(IssuerError::Unavailable);
    }
    Ok(token)
}

fn rejected_response(request_sha256: &str) -> Result<Zeroizing<Vec<u8>>, IssuerError> {
    let bytes = serde_json::to_vec(&WireResponse::Rejected {
        schema_version: ISSUER_RESPONSE_SCHEMA.to_owned(),
        request_sha256: request_sha256.to_owned(),
    })
    .map_err(|_| IssuerError::Unavailable)?;
    if bytes.is_empty() || bytes.len() > MAX_RESPONSE_BYTES {
        return Err(IssuerError::Unavailable);
    }
    Ok(Zeroizing::new(bytes))
}

fn decode_segment(segment: &str, maximum: usize) -> Result<Vec<u8>, IssuerError> {
    if segment.is_empty()
        || segment.len() > maximum.saturating_mul(2)
        || !segment
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
    {
        return Err(IssuerError::Rejected);
    }
    let decoded = URL_SAFE_NO_PAD
        .decode(segment)
        .map_err(|_| IssuerError::Rejected)?;
    if decoded.is_empty() || decoded.len() > maximum || URL_SAFE_NO_PAD.encode(&decoded) != segment
    {
        return Err(IssuerError::Rejected);
    }
    Ok(decoded)
}

fn require_canonical_json<T: Serialize>(original: &[u8], value: &T) -> Result<(), IssuerError> {
    let canonical = serde_json::to_vec(value).map_err(|_| IssuerError::Unavailable)?;
    if canonical != original {
        return Err(IssuerError::Rejected);
    }
    Ok(())
}

fn next_sequence(revision: Option<&StoredRevision>) -> Result<u64, IssuerError> {
    let next = revision.map_or(Some(1), |revision| revision.sequence.checked_add(1));
    next.filter(|sequence| *sequence <= MAX_LOG_RECORDS)
        .ok_or(IssuerError::Unavailable)
}

const fn map_store_internal(_error: StoreFailure) -> IssuerError {
    IssuerError::Unavailable
}

const fn map_server_frame(error: FrameError) -> IssuerTlsServerFailure {
    match error {
        FrameError::Rejected => IssuerTlsServerFailure::Rejected,
        FrameError::Unavailable => IssuerTlsServerFailure::Unavailable,
    }
}

fn validate_bind_endpoint(
    endpoint: SocketAddr,
    bind_scope: IssuerBindScope,
) -> Result<(), IssuerTlsServerFailure> {
    let rejected = match bind_scope {
        IssuerBindScope::LoopbackQualification => !endpoint.ip().is_loopback(),
        IssuerBindScope::ExplicitDeployment => {
            endpoint.port() == 0 || !is_explicit_deployment_ip(endpoint.ip())
        }
    };
    if rejected {
        return Err(IssuerTlsServerFailure::Rejected);
    }
    Ok(())
}

fn is_explicit_deployment_ip(address: IpAddr) -> bool {
    match address {
        IpAddr::V4(address) => {
            !address.is_unspecified()
                && !address.is_loopback()
                && !address.is_link_local()
                && !address.is_multicast()
                && !address.is_broadcast()
        }
        IpAddr::V6(address) => {
            !address.is_unspecified()
                && !address.is_loopback()
                && !address.is_unicast_link_local()
                && !address.is_multicast()
        }
    }
}

fn digest_bytes(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn is_hex64(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn validate_https_issuer(value: &str) -> Result<(), IssuerError> {
    if value.len() > MAX_IDENTIFIER_BYTES
        || !value.starts_with("https://")
        || value.ends_with('/')
        || value.contains([' ', '\t', '\r', '\n', '#', '?'])
        || !value.is_ascii()
        || !value[8..].contains('.')
    {
        return Err(IssuerError::Rejected);
    }
    Ok(())
}

fn validate_token_identifier(
    value: &str,
    minimum: usize,
    maximum: usize,
) -> Result<(), IssuerError> {
    if value.len() < minimum
        || value.len() > maximum
        || !value.is_ascii()
        || !value.bytes().all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.' | b':' | b'/')
        })
    {
        return Err(IssuerError::Rejected);
    }
    Ok(())
}

fn require_plain_directory(path: &Path) -> Result<(), StoreFailure> {
    let metadata = fs::symlink_metadata(path).map_err(|_| StoreFailure::Unavailable)?;
    if !metadata.is_dir() || metadata.file_type().is_symlink() || is_reparse_point(&metadata) {
        return Err(StoreFailure::Rejected);
    }
    Ok(())
}

#[cfg(windows)]
fn is_reparse_point(metadata: &fs::Metadata) -> bool {
    use std::os::windows::fs::MetadataExt as _;

    const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x0400;
    metadata.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0
}

#[cfg(not(windows))]
const fn is_reparse_point(_metadata: &fs::Metadata) -> bool {
    false
}

fn parse_record_name(value: &str) -> Result<u64, StoreFailure> {
    let Some(sequence) = value.strip_suffix(".json") else {
        return Err(StoreFailure::Rejected);
    };
    if sequence.len() != 20 || !sequence.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(StoreFailure::Rejected);
    }
    sequence.parse::<u64>().map_err(|_| StoreFailure::Rejected)
}

fn valid_temporary_name(value: &str) -> bool {
    let Some(remainder) = value.strip_prefix(".pending-") else {
        return false;
    };
    let Some((sequence, nonce)) = remainder.split_once('-') else {
        return false;
    };
    let Some(nonce) = nonce.strip_suffix(".tmp") else {
        return false;
    };
    sequence.len() == 20
        && sequence.bytes().all(|byte| byte.is_ascii_digit())
        && nonce.len() == 32
        && nonce
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}
