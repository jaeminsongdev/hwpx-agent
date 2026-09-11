//! Crash-recoverable broker between an authenticated issuer, a secret vault and stable metadata.

#![forbid(unsafe_code)]

use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};

use remote_credential_lifecycle::{
    ActiveCredential, CredentialState, LifecycleError, LifecycleOperation, LifecyclePolicy,
    PendingTransition, RevokedCredential, VerifiedCredential, apply_definitive_rejection,
    begin_transition, validate_prepared_access, validate_prepared_revocation, verify_access_token,
    verify_revocation,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use zeroize::Zeroizing;

const RECORD_SCHEMA_VERSION: &str = "hwpx-agent.remote-credential-broker-record/v1";
const RESPONSE_SCHEMA_VERSION: &str = "hwpx-agent.remote-credential-issuer-response/v1";
const MAX_RECORD_BYTES: usize = 65_536;
const MAX_LOG_RECORDS: u64 = 65_536;
const MAX_TEMP_FILES: usize = 64;
const MAX_AUTHORIZATION_BYTES: usize = 8_199;
const MAX_SECRET_BYTES: usize = 2_560;
const MAX_ISSUER_RESPONSE_BYTES: usize = 8_192;

#[derive(Clone, Copy, Debug, Eq, PartialEq, thiserror::Error)]
pub enum BrokerError {
    #[error("credential broker state is invalid")]
    InvalidState,
    #[error("credential broker storage is unavailable")]
    StoreUnavailable,
    #[error("credential broker storage compare-and-append conflicted")]
    StoreConflict,
    #[error("credential vault is unavailable")]
    VaultUnavailable,
    #[error("credential vault state was rejected")]
    VaultRejected,
    #[error("issuer authorization is unavailable")]
    AuthorizationUnavailable,
    #[error("issuer authorization was rejected")]
    AuthorizationRejected,
    #[error("credential issuer transport is unavailable")]
    TransportUnavailable,
    #[error("credential issuer peer identity was rejected")]
    PeerRejected,
    #[error("credential issuer transport configuration was rejected")]
    TransportConfigurationRejected,
    #[error("credential issuer response was invalid")]
    InvalidResponse,
    #[error("credential lifecycle operation failed: {0}")]
    Lifecycle(#[from] LifecycleError),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, thiserror::Error)]
pub enum StoreFailure {
    #[error("credential state store is unavailable")]
    Unavailable,
    #[error("credential state store compare-and-append conflicted")]
    Conflict,
    #[error("credential state store rejected its input")]
    Rejected,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, thiserror::Error)]
pub enum VaultFailure {
    #[error("credential vault is unavailable")]
    Unavailable,
    #[error("credential vault rejected its input or state")]
    Rejected,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, thiserror::Error)]
pub enum AuthorizationFailure {
    #[error("issuer authorization is unavailable")]
    Unavailable,
    #[error("issuer authorization was rejected")]
    Rejected,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, thiserror::Error)]
pub enum IssuerTransportFailure {
    #[error("credential issuer transport configuration was rejected")]
    ConfigurationRejected,
    #[error("credential issuer transport is unavailable")]
    Unavailable,
    #[error("credential issuer peer identity was rejected")]
    PeerRejected,
    #[error("credential issuer response was invalid")]
    InvalidResponse,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum VaultObservation {
    Absent,
    Present { credential_sha256: String },
}

pub trait CredentialVault: fmt::Debug {
    /// Observes only absence or the digest of the exact configured credential.
    ///
    /// # Errors
    ///
    /// Distinguishes unavailable custody from rejected secret shape or platform state.
    fn observe(&mut self) -> Result<VaultObservation, VaultFailure>;
    /// Replaces the exact configured credential without enumerating any other target.
    ///
    /// # Errors
    ///
    /// Distinguishes unavailable custody from rejected secret shape or platform state.
    fn store(&mut self, credential: &str) -> Result<(), VaultFailure>;
    /// Idempotently removes the exact configured credential without enumeration.
    ///
    /// # Errors
    ///
    /// Distinguishes unavailable custody from rejected platform state.
    fn delete(&mut self) -> Result<(), VaultFailure>;
}

pub struct IssuerAuthorization(Zeroizing<String>);

impl fmt::Debug for IssuerAuthorization {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("IssuerAuthorization(<redacted>)")
    }
}

impl IssuerAuthorization {
    /// Creates one exact bounded compact-JWS bearer used only to authenticate the issuer client.
    ///
    /// # Errors
    ///
    /// Rejects alternate casing, controls, whitespace and malformed compact-JWS segments.
    pub fn new(value: String) -> Result<Self, AuthorizationFailure> {
        let value = Zeroizing::new(value);
        if value.is_empty()
            || value.len() > MAX_AUTHORIZATION_BYTES
            || value.as_bytes().iter().any(u8::is_ascii_control)
        {
            return Err(AuthorizationFailure::Rejected);
        }
        let token = value
            .strip_prefix("Bearer ")
            .ok_or(AuthorizationFailure::Rejected)?;
        if !valid_compact_jws(token) {
            return Err(AuthorizationFailure::Rejected);
        }
        Ok(Self(value))
    }

    pub fn with_secret<R>(&self, operation: impl FnOnce(&str) -> R) -> R {
        operation(self.0.as_str())
    }
}

pub trait IssuerAuthorizationProvider: fmt::Debug {
    /// Returns a fresh short-lived client assertion for exactly one issuer exchange.
    ///
    /// # Errors
    ///
    /// Distinguishes unavailable assertion custody from rejected assertion shape.
    fn authorization(&mut self) -> Result<IssuerAuthorization, AuthorizationFailure>;
}

pub struct SingleUseIssuerAuthorizationProvider {
    authorization: Option<IssuerAuthorization>,
}

impl fmt::Debug for SingleUseIssuerAuthorizationProvider {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SingleUseIssuerAuthorizationProvider")
            .field("available", &self.authorization.is_some())
            .finish_non_exhaustive()
    }
}

impl SingleUseIssuerAuthorizationProvider {
    /// Creates a provider that consumes one already-issued issuer-client assertion.
    ///
    /// # Errors
    ///
    /// Rejects a malformed bearer assertion.
    pub fn new(value: String) -> Result<Self, AuthorizationFailure> {
        Ok(Self {
            authorization: Some(IssuerAuthorization::new(value)?),
        })
    }
}

impl IssuerAuthorizationProvider for SingleUseIssuerAuthorizationProvider {
    fn authorization(&mut self) -> Result<IssuerAuthorization, AuthorizationFailure> {
        self.authorization
            .take()
            .ok_or(AuthorizationFailure::Unavailable)
    }
}

pub struct IssuerSecret(Zeroizing<String>);

impl fmt::Debug for IssuerSecret {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("IssuerSecret(<redacted>)")
    }
}

impl IssuerSecret {
    /// Wraps a bounded canonical compact JWS returned by the authenticated issuer.
    ///
    /// # Errors
    ///
    /// Rejects malformed token shape before lifecycle signature validation.
    pub fn new(value: String) -> Result<Self, IssuerTransportFailure> {
        let value = Zeroizing::new(value);
        if value.is_empty() || value.len() > MAX_SECRET_BYTES || !valid_compact_jws(&value) {
            return Err(IssuerTransportFailure::InvalidResponse);
        }
        Ok(Self(value))
    }

    pub fn with_secret<R>(&self, operation: impl FnOnce(&str) -> R) -> R {
        operation(self.0.as_str())
    }
}

#[derive(Debug)]
pub enum IssuerReply {
    Access(IssuerSecret),
    Revocation(IssuerSecret),
    DefinitiveRejection,
}

pub trait CredentialIssuerTransport: fmt::Debug {
    /// Sends exact pending request bytes over an authenticated issuer channel.
    ///
    /// `DefinitiveRejection` must only be returned for an authenticated, request-digest-bound
    /// denial. All ambiguous transport and protocol failures remain errors and retain pending state.
    ///
    /// # Errors
    ///
    /// Distinguishes configuration, availability, peer-identity and authenticated-protocol errors.
    fn exchange(
        &mut self,
        authorization: &IssuerAuthorization,
        request: &[u8],
    ) -> Result<IssuerReply, IssuerTransportFailure>;
}

#[derive(Clone, Eq, PartialEq)]
pub struct StoredRevision {
    sequence: u64,
    record_sha256: String,
}

impl fmt::Debug for StoredRevision {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("StoredRevision")
            .field("sequence", &self.sequence)
            .field("record_sha256", &"<redacted>")
            .finish_non_exhaustive()
    }
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

#[derive(Clone)]
pub struct StoredRecord {
    revision: StoredRevision,
    previous: Option<StoredRevision>,
    bytes: Vec<u8>,
}

impl fmt::Debug for StoredRecord {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("StoredRecord")
            .field("revision", &self.revision)
            .field("has_previous", &self.previous.is_some())
            .field("bytes", &self.bytes.len())
            .finish_non_exhaustive()
    }
}

impl StoredRecord {
    /// Constructs a store result while deriving its digest from the exact record bytes.
    ///
    /// # Errors
    ///
    /// Rejects zero/out-of-range sequences, malformed previous revisions and boundedness drift.
    pub fn new(
        sequence: u64,
        previous: Option<StoredRevision>,
        bytes: Vec<u8>,
    ) -> Result<Self, StoreFailure> {
        if sequence == 0
            || sequence > MAX_LOG_RECORDS
            || bytes.is_empty()
            || bytes.len() > MAX_RECORD_BYTES
            || previous.as_ref().is_some_and(|value| {
                value.sequence.checked_add(1) != Some(sequence) || !is_hex64(&value.record_sha256)
            })
            || (sequence == 1) != previous.is_none()
        {
            return Err(StoreFailure::Rejected);
        }
        let record_sha256 = digest_bytes(&bytes);
        Ok(Self {
            revision: StoredRevision {
                sequence,
                record_sha256,
            },
            previous,
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

pub trait CredentialStateStore: fmt::Debug {
    /// Loads the newest immutable state record and its exact predecessor revision.
    ///
    /// # Errors
    ///
    /// Rejects malformed history and distinguishes unavailable storage.
    fn load_latest(&mut self) -> Result<Option<StoredRecord>, StoreFailure>;
    /// Atomically appends bytes only when the expected revision is still current.
    ///
    /// # Errors
    ///
    /// Returns conflict for a concurrent append, rejected for invalid bytes and unavailable for
    /// ambiguous storage failure.
    fn append(
        &mut self,
        expected: Option<&StoredRevision>,
        bytes: &[u8],
    ) -> Result<StoredRecord, StoreFailure>;
}

/// Immutable append-only state log. A synced temp file is linked into the sequence namespace with
/// no-overwrite semantics, so a concurrent writer cannot replace an accepted record.
pub struct AppendOnlyCredentialStateStore {
    root: PathBuf,
}

impl fmt::Debug for AppendOnlyCredentialStateStore {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AppendOnlyCredentialStateStore")
            .field("root", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl AppendOnlyCredentialStateStore {
    /// Opens or creates one dedicated plain directory for credential state records.
    ///
    /// # Errors
    ///
    /// Rejects empty, symlinked or non-directory roots and unavailable filesystem operations.
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
        let entries = fs::read_dir(&self.root).map_err(|_| StoreFailure::Unavailable)?;
        for entry in entries {
            let entry = entry.map_err(|_| StoreFailure::Unavailable)?;
            let file_type = entry.file_type().map_err(|_| StoreFailure::Unavailable)?;
            let name = entry
                .file_name()
                .into_string()
                .map_err(|_| StoreFailure::Rejected)?;
            if name.starts_with(".pending-") {
                if !valid_temporary_name(&name) {
                    return Err(StoreFailure::Rejected);
                }
                if !file_type.is_file() {
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
            let (sequence, expected_sha256) = parse_record_name(&name)?;
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
            let actual_sha256 = digest_bytes(&bytes);
            if actual_sha256 != expected_sha256 {
                return Err(StoreFailure::Rejected);
            }
            records.push(StoredRecord {
                revision: StoredRevision {
                    sequence,
                    record_sha256: actual_sha256,
                },
                previous: None,
                bytes,
            });
            if records.len() > usize::try_from(MAX_LOG_RECORDS).unwrap_or(usize::MAX) {
                return Err(StoreFailure::Rejected);
            }
        }
        records.sort_by_key(|record| record.revision.sequence);
        let mut previous = None;
        for (index, record) in records.iter_mut().enumerate() {
            let expected = u64::try_from(index)
                .map_err(|_| StoreFailure::Rejected)?
                .checked_add(1)
                .ok_or(StoreFailure::Rejected)?;
            if record.revision.sequence != expected {
                return Err(StoreFailure::Rejected);
            }
            record.previous = previous;
            previous = Some(record.revision.clone());
        }
        validate_stored_history(&records)?;
        Ok(records)
    }
}

impl CredentialStateStore for AppendOnlyCredentialStateStore {
    fn load_latest(&mut self) -> Result<Option<StoredRecord>, StoreFailure> {
        Ok(self.scan()?.pop())
    }

    fn append(
        &mut self,
        expected: Option<&StoredRevision>,
        bytes: &[u8],
    ) -> Result<StoredRecord, StoreFailure> {
        if bytes.is_empty() || bytes.len() > MAX_RECORD_BYTES {
            return Err(StoreFailure::Rejected);
        }
        let current = self.load_latest()?;
        if current.as_ref().map(|record| &record.revision) != expected {
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
        let record_sha256 = digest_bytes(bytes);
        let final_name = format!("{sequence:020}-{record_sha256}.json");
        let final_path = self.root.join(final_name);
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
        Ok(StoredRecord {
            revision: StoredRevision {
                sequence,
                record_sha256,
            },
            previous: expected.cloned(),
            bytes: bytes.to_vec(),
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(tag = "phase", rename_all = "snake_case", deny_unknown_fields)]
enum DurablePhase {
    Stable {
        credential: CredentialState,
    },
    AwaitingIssuer {
        pending: PendingTransition,
    },
    PreparedAccess {
        pending: PendingTransition,
        credential: ActiveCredential,
    },
    PreparedRevocation {
        pending: PendingTransition,
        credential: RevokedCredential,
    },
}

#[derive(Clone, Debug, Eq, PartialEq, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct DurableRecord {
    schema_version: String,
    sequence: u64,
    previous_record_sha256: Option<String>,
    policy_binding_sha256: String,
    state: DurablePhase,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum BrokerPhase {
    Stable(CredentialState),
    AwaitingIssuer,
    PreparedAccess,
    PreparedRevocation,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum DriveOutcome {
    Idle(CredentialState),
    Pending,
    Completed(CredentialState),
    DefinitivelyRejected(CredentialState),
}

pub struct CredentialBroker<S, V, A, T> {
    policy: LifecyclePolicy,
    store: S,
    vault: V,
    authorization: A,
    transport: T,
}

impl<S, V, A, T> fmt::Debug for CredentialBroker<S, V, A, T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CredentialBroker")
            .field("policy", &"<redacted>")
            .field("store", &"<redacted>")
            .field("vault", &"<redacted>")
            .field("authorization", &"<redacted>")
            .field("transport", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl<S, V, A, T> CredentialBroker<S, V, A, T>
where
    S: CredentialStateStore,
    V: CredentialVault,
    A: IssuerAuthorizationProvider,
    T: CredentialIssuerTransport,
{
    /// Opens a broker and initializes an absent state only when both log and vault are empty.
    ///
    /// # Errors
    ///
    /// Rejects state/policy drift or an orphaned vault credential and preserves all existing data.
    pub fn open(
        policy: LifecyclePolicy,
        mut store: S,
        mut vault: V,
        authorization: A,
        transport: T,
    ) -> Result<Self, BrokerError> {
        if let Some(stored) = store.load_latest().map_err(map_store_failure)? {
            decode_record(&policy, &stored)?;
        } else {
            if vault.observe().map_err(map_vault_failure)? != VaultObservation::Absent {
                return Err(BrokerError::InvalidState);
            }
            let record = build_record(
                &policy,
                None,
                DurablePhase::Stable {
                    credential: CredentialState::Absent,
                },
            )?;
            let encoded = encode_record(&record)?;
            store.append(None, &encoded).map_err(map_store_failure)?;
        }
        Ok(Self {
            policy,
            store,
            vault,
            authorization,
            transport,
        })
    }

    /// Returns the validated durable phase without exposing pending identifiers or secret material.
    ///
    /// # Errors
    ///
    /// Rejects malformed, non-canonical, discontinuous or policy-drifted state.
    pub fn phase(&mut self) -> Result<BrokerPhase, BrokerError> {
        let (_, record) = self.load()?;
        Ok(match record.state {
            DurablePhase::Stable { credential } => BrokerPhase::Stable(credential),
            DurablePhase::AwaitingIssuer { .. } => BrokerPhase::AwaitingIssuer,
            DurablePhase::PreparedAccess { .. } => BrokerPhase::PreparedAccess,
            DurablePhase::PreparedRevocation { .. } => BrokerPhase::PreparedRevocation,
        })
    }

    /// Persists one exact pending intent before any issuer exchange.
    ///
    /// # Errors
    ///
    /// Requires a stable state whose vault observation exactly matches its non-secret metadata.
    pub fn begin(
        &mut self,
        operation: LifecycleOperation,
        operation_id: String,
        now: u64,
    ) -> Result<(), BrokerError> {
        let (stored, record) = self.load()?;
        let DurablePhase::Stable { credential } = record.state else {
            return Err(BrokerError::InvalidState);
        };
        self.require_vault_matches_state(&credential)?;
        let pending = begin_transition(&self.policy, &credential, operation, operation_id, now)?;
        self.append(&stored, DurablePhase::AwaitingIssuer { pending })?;
        Ok(())
    }

    /// Reconciles or advances one pending lifecycle transition.
    ///
    /// Prepared stages make vault publication/deletion restart-safe. Only the exact authenticated
    /// `DefinitiveRejection` response restores the prior stable state.
    ///
    /// # Errors
    ///
    /// Leaves the latest durable stage intact on issuer, authorization, vault or store failure.
    pub fn drive(&mut self, now: u64) -> Result<DriveOutcome, BrokerError> {
        let (stored, record) = self.load()?;
        match record.state {
            DurablePhase::Stable { credential } => {
                self.require_vault_matches_state(&credential)?;
                Ok(DriveOutcome::Idle(credential))
            }
            DurablePhase::AwaitingIssuer { pending } => self.drive_awaiting(&stored, pending, now),
            DurablePhase::PreparedAccess {
                pending,
                credential,
            } => self.drive_prepared_access(&stored, &pending, credential, None, now),
            DurablePhase::PreparedRevocation {
                pending,
                credential,
            } => self.drive_prepared_revocation(&stored, &pending, credential),
        }
    }

    #[must_use]
    pub fn into_parts(self) -> (S, V, A, T) {
        (self.store, self.vault, self.authorization, self.transport)
    }

    fn drive_awaiting(
        &mut self,
        stored: &StoredRecord,
        pending: PendingTransition,
        now: u64,
    ) -> Result<DriveOutcome, BrokerError> {
        self.require_vault_matches_state(pending.previous_state())?;
        let request = pending.retry_request(&self.policy, now)?;
        let authorization = self
            .authorization
            .authorization()
            .map_err(map_authorization_failure)?;
        let reply = self
            .transport
            .exchange(&authorization, &request)
            .map_err(map_transport_failure)?;
        match reply {
            IssuerReply::DefinitiveRejection => {
                let restored = apply_definitive_rejection(&self.policy, pending, now)?;
                self.require_vault_matches_state(&restored)?;
                self.append(
                    stored,
                    DurablePhase::Stable {
                        credential: restored.clone(),
                    },
                )?;
                Ok(DriveOutcome::DefinitivelyRejected(restored))
            }
            IssuerReply::Access(token) => {
                if pending.operation() == LifecycleOperation::Revoke {
                    return Err(BrokerError::InvalidResponse);
                }
                let verified = token.with_secret(|secret| {
                    verify_access_token(&self.policy, &pending, secret.to_owned(), now)
                })?;
                let metadata = verified.metadata().clone();
                let prepared = self.append(
                    stored,
                    DurablePhase::PreparedAccess {
                        pending: pending.clone(),
                        credential: metadata.clone(),
                    },
                )?;
                self.drive_prepared_access(&prepared, &pending, metadata, Some(&verified), now)
            }
            IssuerReply::Revocation(receipt) => {
                if pending.operation() != LifecycleOperation::Revoke {
                    return Err(BrokerError::InvalidResponse);
                }
                let revoked = receipt
                    .with_secret(|secret| verify_revocation(&self.policy, &pending, secret, now))?;
                let prepared = self.append(
                    stored,
                    DurablePhase::PreparedRevocation {
                        pending: pending.clone(),
                        credential: revoked.clone(),
                    },
                )?;
                self.drive_prepared_revocation(&prepared, &pending, revoked)
            }
        }
    }

    fn drive_prepared_access(
        &mut self,
        stored: &StoredRecord,
        pending: &PendingTransition,
        credential: ActiveCredential,
        verified: Option<&VerifiedCredential>,
        now: u64,
    ) -> Result<DriveOutcome, BrokerError> {
        validate_prepared_access(&self.policy, pending, &credential)?;
        match self.vault.observe().map_err(map_vault_failure)? {
            VaultObservation::Present { credential_sha256 }
                if credential_sha256 == credential.credential_sha256() =>
            {
                return self.commit_active(stored, credential);
            }
            observation if vault_matches_state(&observation, pending.previous_state()) => {}
            _ => return Err(BrokerError::InvalidState),
        }
        if let Some(verified) = verified {
            if verified.metadata() != &credential {
                return Err(BrokerError::InvalidState);
            }
            verified
                .with_secret(|secret| self.vault.store(secret))
                .map_err(map_vault_failure)?;
        } else {
            let request = pending.retry_request(&self.policy, now)?;
            let authorization = self
                .authorization
                .authorization()
                .map_err(map_authorization_failure)?;
            let reply = self
                .transport
                .exchange(&authorization, &request)
                .map_err(map_transport_failure)?;
            let IssuerReply::Access(token) = reply else {
                return Err(BrokerError::InvalidResponse);
            };
            let recovered = token.with_secret(|secret| {
                verify_access_token(&self.policy, pending, secret.to_owned(), now)
            })?;
            if recovered.metadata() != &credential {
                return Err(BrokerError::InvalidResponse);
            }
            recovered
                .with_secret(|secret| self.vault.store(secret))
                .map_err(map_vault_failure)?;
        }
        match self.vault.observe().map_err(map_vault_failure)? {
            VaultObservation::Present { credential_sha256 }
                if credential_sha256 == credential.credential_sha256() =>
            {
                self.commit_active(stored, credential)
            }
            VaultObservation::Present { .. } | VaultObservation::Absent => {
                Err(BrokerError::VaultRejected)
            }
        }
    }

    fn commit_active(
        &mut self,
        stored: &StoredRecord,
        credential: ActiveCredential,
    ) -> Result<DriveOutcome, BrokerError> {
        let state = CredentialState::Active { credential };
        self.append(
            stored,
            DurablePhase::Stable {
                credential: state.clone(),
            },
        )?;
        Ok(DriveOutcome::Completed(state))
    }

    fn drive_prepared_revocation(
        &mut self,
        stored: &StoredRecord,
        pending: &PendingTransition,
        credential: RevokedCredential,
    ) -> Result<DriveOutcome, BrokerError> {
        validate_prepared_revocation(&self.policy, pending, &credential)?;
        match self.vault.observe().map_err(map_vault_failure)? {
            VaultObservation::Absent => {}
            observation if vault_matches_state(&observation, pending.previous_state()) => {
                self.vault.delete().map_err(map_vault_failure)?;
                if self.vault.observe().map_err(map_vault_failure)? != VaultObservation::Absent {
                    return Err(BrokerError::VaultRejected);
                }
            }
            VaultObservation::Present { .. } => return Err(BrokerError::InvalidState),
        }
        let state = CredentialState::Revoked { credential };
        self.append(
            stored,
            DurablePhase::Stable {
                credential: state.clone(),
            },
        )?;
        Ok(DriveOutcome::Completed(state))
    }

    fn require_vault_matches_state(&mut self, state: &CredentialState) -> Result<(), BrokerError> {
        let observation = self.vault.observe().map_err(map_vault_failure)?;
        if vault_matches_state(&observation, state) {
            Ok(())
        } else {
            Err(BrokerError::InvalidState)
        }
    }

    fn load(&mut self) -> Result<(StoredRecord, DurableRecord), BrokerError> {
        let stored = self
            .store
            .load_latest()
            .map_err(map_store_failure)?
            .ok_or(BrokerError::InvalidState)?;
        let record = decode_record(&self.policy, &stored)?;
        Ok((stored, record))
    }

    fn append(
        &mut self,
        previous: &StoredRecord,
        state: DurablePhase,
    ) -> Result<StoredRecord, BrokerError> {
        validate_phase(&self.policy, &state)?;
        let record = build_record(&self.policy, Some(&previous.revision), state)?;
        let encoded = encode_record(&record)?;
        self.store
            .append(Some(&previous.revision), &encoded)
            .map_err(map_store_failure)
    }
}

fn build_record(
    policy: &LifecyclePolicy,
    previous: Option<&StoredRevision>,
    state: DurablePhase,
) -> Result<DurableRecord, BrokerError> {
    let sequence = previous.map_or(Ok(1), |revision| {
        revision
            .sequence
            .checked_add(1)
            .ok_or(BrokerError::InvalidState)
    })?;
    Ok(DurableRecord {
        schema_version: RECORD_SCHEMA_VERSION.to_owned(),
        sequence,
        previous_record_sha256: previous.map(|revision| revision.record_sha256.clone()),
        policy_binding_sha256: policy.binding_sha256()?,
        state,
    })
}

fn encode_record(record: &DurableRecord) -> Result<Vec<u8>, BrokerError> {
    let encoded = serde_json::to_vec(record).map_err(|_| BrokerError::InvalidState)?;
    if encoded.is_empty() || encoded.len() > MAX_RECORD_BYTES {
        return Err(BrokerError::InvalidState);
    }
    Ok(encoded)
}

fn decode_record(
    policy: &LifecyclePolicy,
    stored: &StoredRecord,
) -> Result<DurableRecord, BrokerError> {
    if stored.bytes.is_empty() || stored.bytes.len() > MAX_RECORD_BYTES {
        return Err(BrokerError::InvalidState);
    }
    if digest_bytes(&stored.bytes) != stored.revision.record_sha256 {
        return Err(BrokerError::InvalidState);
    }
    let record: DurableRecord =
        serde_json::from_slice(&stored.bytes).map_err(|_| BrokerError::InvalidState)?;
    if encode_record(&record)? != stored.bytes
        || record.schema_version != RECORD_SCHEMA_VERSION
        || record.sequence != stored.revision.sequence
        || record.policy_binding_sha256 != policy.binding_sha256()?
        || record.previous_record_sha256
            != stored
                .previous
                .as_ref()
                .map(|revision| revision.record_sha256.clone())
    {
        return Err(BrokerError::InvalidState);
    }
    validate_phase(policy, &record.state)?;
    Ok(record)
}

fn validate_stored_history(records: &[StoredRecord]) -> Result<(), StoreFailure> {
    let mut policy_binding = None;
    for stored in records {
        let record: DurableRecord =
            serde_json::from_slice(&stored.bytes).map_err(|_| StoreFailure::Rejected)?;
        let canonical = serde_json::to_vec(&record).map_err(|_| StoreFailure::Rejected)?;
        let expected_previous = stored
            .previous
            .as_ref()
            .map(|revision| revision.record_sha256.as_str());
        if canonical != stored.bytes
            || record.schema_version != RECORD_SCHEMA_VERSION
            || record.sequence != stored.revision.sequence
            || record.previous_record_sha256.as_deref() != expected_previous
            || !is_hex64(&record.policy_binding_sha256)
        {
            return Err(StoreFailure::Rejected);
        }
        match policy_binding.as_deref() {
            None => policy_binding = Some(record.policy_binding_sha256.clone()),
            Some(expected) if expected == record.policy_binding_sha256 => {}
            Some(_) => return Err(StoreFailure::Rejected),
        }
    }
    Ok(())
}

fn validate_phase(policy: &LifecyclePolicy, phase: &DurablePhase) -> Result<(), BrokerError> {
    match phase {
        DurablePhase::Stable { credential } => credential.validate(policy)?,
        DurablePhase::AwaitingIssuer { pending } => {
            pending.to_canonical_json(policy)?;
        }
        DurablePhase::PreparedAccess {
            pending,
            credential,
        } => validate_prepared_access(policy, pending, credential)?,
        DurablePhase::PreparedRevocation {
            pending,
            credential,
        } => validate_prepared_revocation(policy, pending, credential)?,
    }
    Ok(())
}

fn vault_matches_state(observation: &VaultObservation, state: &CredentialState) -> bool {
    match (observation, state) {
        (VaultObservation::Absent, CredentialState::Absent | CredentialState::Revoked { .. }) => {
            true
        }
        (
            VaultObservation::Present { credential_sha256 },
            CredentialState::Active { credential },
        ) => credential_sha256 == credential.credential_sha256(),
        _ => false,
    }
}

fn valid_compact_jws(value: &str) -> bool {
    let mut segments = value.split('.');
    let valid_segment = |segment: &str| {
        !segment.is_empty()
            && segment
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
    };
    matches!(
        (segments.next(), segments.next(), segments.next()),
        (Some(first), Some(second), Some(third))
            if valid_segment(first) && valid_segment(second) && valid_segment(third)
    ) && segments.next().is_none()
}

fn parse_record_name(value: &str) -> Result<(u64, String), StoreFailure> {
    if value.len() != 20 + 1 + 64 + 5
        || Path::new(value)
            .extension()
            .is_none_or(|extension| extension != "json")
    {
        return Err(StoreFailure::Rejected);
    }
    let sequence = &value[..20];
    let separator = value.as_bytes().get(20).copied();
    let sha256 = &value[21..85];
    if separator != Some(b'-')
        || !sequence.bytes().all(|byte| byte.is_ascii_digit())
        || !is_hex64(sha256)
    {
        return Err(StoreFailure::Rejected);
    }
    Ok((
        sequence.parse().map_err(|_| StoreFailure::Rejected)?,
        sha256.to_owned(),
    ))
}

fn valid_temporary_name(value: &str) -> bool {
    const PREFIX: &[u8] = b".pending-";
    const SEQUENCE_END: usize = PREFIX.len() + 20;
    const NONCE_START: usize = SEQUENCE_END + 1;
    const NONCE_END: usize = NONCE_START + 32;
    let bytes = value.as_bytes();
    bytes.len() == NONCE_END + 4
        && bytes.starts_with(PREFIX)
        && bytes.get(SEQUENCE_END) == Some(&b'-')
        && bytes.get(NONCE_END..) == Some(b".tmp")
        && bytes[PREFIX.len()..SEQUENCE_END]
            .iter()
            .all(u8::is_ascii_digit)
        && bytes[NONCE_START..NONCE_END]
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
        && std::str::from_utf8(&bytes[PREFIX.len()..SEQUENCE_END])
            .ok()
            .and_then(|sequence| sequence.parse::<u64>().ok())
            .is_some_and(|sequence| sequence > 0 && sequence <= MAX_LOG_RECORDS)
}

fn require_plain_directory(path: &Path) -> Result<(), StoreFailure> {
    let metadata = fs::symlink_metadata(path).map_err(|_| StoreFailure::Unavailable)?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(StoreFailure::Rejected);
    }
    Ok(())
}

fn is_hex64(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn digest_bytes(value: &[u8]) -> String {
    hex::encode(Sha256::digest(value))
}

const fn map_store_failure(error: StoreFailure) -> BrokerError {
    match error {
        StoreFailure::Unavailable => BrokerError::StoreUnavailable,
        StoreFailure::Conflict => BrokerError::StoreConflict,
        StoreFailure::Rejected => BrokerError::InvalidState,
    }
}

const fn map_vault_failure(error: VaultFailure) -> BrokerError {
    match error {
        VaultFailure::Unavailable => BrokerError::VaultUnavailable,
        VaultFailure::Rejected => BrokerError::VaultRejected,
    }
}

const fn map_authorization_failure(error: AuthorizationFailure) -> BrokerError {
    match error {
        AuthorizationFailure::Unavailable => BrokerError::AuthorizationUnavailable,
        AuthorizationFailure::Rejected => BrokerError::AuthorizationRejected,
    }
}

const fn map_transport_failure(error: IssuerTransportFailure) -> BrokerError {
    match error {
        IssuerTransportFailure::ConfigurationRejected => {
            BrokerError::TransportConfigurationRejected
        }
        IssuerTransportFailure::Unavailable => BrokerError::TransportUnavailable,
        IssuerTransportFailure::PeerRejected => BrokerError::PeerRejected,
        IssuerTransportFailure::InvalidResponse => BrokerError::InvalidResponse,
    }
}

/// Parses the exact canonical issuer response and binds it to the request digest.
///
/// # Errors
///
/// Rejects unknown/duplicate/non-canonical fields, wrong request binding and malformed secrets.
pub fn parse_issuer_response(
    request: &[u8],
    response: &[u8],
) -> Result<IssuerReply, IssuerTransportFailure> {
    if request.is_empty() || response.is_empty() || response.len() > MAX_ISSUER_RESPONSE_BYTES {
        return Err(IssuerTransportFailure::InvalidResponse);
    }
    let response_copy = Zeroizing::new(response.to_vec());
    let decoded: WireResponse = serde_json::from_slice(&response_copy)
        .map_err(|_| IssuerTransportFailure::InvalidResponse)?;
    let canonical = Zeroizing::new(
        serde_json::to_vec(&decoded).map_err(|_| IssuerTransportFailure::InvalidResponse)?,
    );
    let (schema_version, request_sha256) = match &decoded {
        WireResponse::Access {
            schema_version,
            request_sha256,
            ..
        }
        | WireResponse::Revocation {
            schema_version,
            request_sha256,
            ..
        }
        | WireResponse::Rejected {
            schema_version,
            request_sha256,
        } => (schema_version, request_sha256),
    };
    if canonical.as_slice() != response_copy.as_slice()
        || schema_version != RESPONSE_SCHEMA_VERSION
        || request_sha256 != &digest_bytes(request)
    {
        return Err(IssuerTransportFailure::InvalidResponse);
    }
    match decoded {
        WireResponse::Access { token, .. } => Ok(IssuerReply::Access(IssuerSecret::new(token)?)),
        WireResponse::Revocation { receipt, .. } => {
            Ok(IssuerReply::Revocation(IssuerSecret::new(receipt)?))
        }
        WireResponse::Rejected { .. } => Ok(IssuerReply::DefinitiveRejection),
    }
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

#[cfg(test)]
mod tests {
    use std::collections::VecDeque;

    use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
    use remote_credential_lifecycle::IssuerKey;
    use ring::{
        rand::SystemRandom,
        signature::{Ed25519KeyPair, KeyPair as _},
    };
    use serde::Serialize;
    use tempfile::tempdir;

    use super::*;

    const NOW: u64 = 1_800_000_000;
    const ISSUER: &str = "https://issuer.example";
    const SUBJECT: &str = "service-account-0001";
    const AUDIENCE: &str = "hwpx-agent-remote-sync";
    const KEY_ID: &str = "issuer-key-0001";

    fn must_ok<T, E: fmt::Debug>(result: Result<T, E>) -> T {
        match result {
            Ok(value) => value,
            Err(error) => panic!("unexpected error: {error:?}"),
        }
    }

    fn signing_key() -> Ed25519KeyPair {
        let random = SystemRandom::new();
        let document = must_ok(Ed25519KeyPair::generate_pkcs8(&random));
        must_ok(Ed25519KeyPair::from_pkcs8(document.as_ref()))
    }

    fn policy(pair: &Ed25519KeyPair) -> LifecyclePolicy {
        let mut public_key = [0_u8; 32];
        public_key.copy_from_slice(pair.public_key().as_ref());
        must_ok(LifecyclePolicy::new(
            ISSUER.to_owned(),
            SUBJECT.to_owned(),
            AUDIENCE.to_owned(),
            vec![must_ok(IssuerKey::new(KEY_ID.to_owned(), public_key))],
            300,
            900,
            120,
            30,
            120,
        ))
    }

    #[derive(Clone, Serialize)]
    struct Header<'a> {
        alg: &'a str,
        typ: &'a str,
        kid: &'a str,
    }

    #[derive(Serialize)]
    struct AccessClaims<'a> {
        iss: &'a str,
        sub: &'a str,
        aud: &'a str,
        scope: &'a str,
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

    fn signed_jwt(pair: &Ed25519KeyPair, token_type: &str, claims: &impl Serialize) -> String {
        let header = must_ok(serde_json::to_vec(&Header {
            alg: "EdDSA",
            typ: token_type,
            kid: KEY_ID,
        }));
        let payload = must_ok(serde_json::to_vec(claims));
        let signing_input = format!(
            "{}.{}",
            URL_SAFE_NO_PAD.encode(header),
            URL_SAFE_NO_PAD.encode(payload)
        );
        let signature = pair.sign(signing_input.as_bytes());
        format!(
            "{signing_input}.{}",
            URL_SAFE_NO_PAD.encode(signature.as_ref())
        )
    }

    #[derive(Deserialize, Serialize)]
    #[serde(deny_unknown_fields)]
    struct TestRequest {
        schema_version: String,
        operation: LifecycleOperation,
        operation_id: String,
        binding_sha256: String,
        expected_generation: u64,
        expected_key_generation: u64,
        prior_credential_sha256: Option<String>,
        requested_at: u64,
    }

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum TestReply {
        Sign,
        DefinitiveRejection,
        Unavailable,
        PeerRejected,
        InvalidResponse,
    }

    struct TestIssuer {
        pair: Ed25519KeyPair,
        replies: VecDeque<TestReply>,
        calls: usize,
    }

    impl fmt::Debug for TestIssuer {
        fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter
                .debug_struct("TestIssuer")
                .field("pair", &"<redacted>")
                .field("queued_replies", &self.replies.len())
                .field("calls", &self.calls)
                .finish_non_exhaustive()
        }
    }

    impl TestIssuer {
        fn new(pair: Ed25519KeyPair, replies: impl IntoIterator<Item = TestReply>) -> Self {
            Self {
                pair,
                replies: replies.into_iter().collect(),
                calls: 0,
            }
        }

        fn signed_reply(&self, request: &TestRequest) -> IssuerReply {
            assert_eq!(
                request.schema_version,
                "hwpx-agent.remote-credential-lifecycle-request/v1"
            );
            assert!(is_hex64(&request.binding_sha256));
            let request_bytes = must_ok(serde_json::to_vec(request));
            let request_sha256 = digest_bytes(&request_bytes);
            match request.operation {
                LifecycleOperation::Issue
                | LifecycleOperation::Refresh
                | LifecycleOperation::Rotate => {
                    let claims = AccessClaims {
                        iss: ISSUER,
                        sub: SUBJECT,
                        aud: AUDIENCE,
                        scope: "mirror.sync",
                        iat: request.requested_at,
                        nbf: request.requested_at,
                        exp: request.requested_at + 600,
                        jti: format!(
                            "credential-jti-{:08}-{}",
                            request.expected_generation, request.expected_key_generation
                        ),
                        operation_id: &request.operation_id,
                        request_sha256: &request_sha256,
                        generation: request.expected_generation,
                        key_generation: request.expected_key_generation,
                    };
                    let token = signed_jwt(&self.pair, "hwpx-agent-service+jwt", &claims);
                    IssuerReply::Access(must_ok(IssuerSecret::new(token)))
                }
                LifecycleOperation::Revoke => {
                    let prior = request
                        .prior_credential_sha256
                        .as_deref()
                        .unwrap_or_else(|| panic!("revocation prior digest missing"));
                    let claims = RevocationClaims {
                        iss: ISSUER,
                        sub: SUBJECT,
                        aud: AUDIENCE,
                        iat: request.requested_at,
                        jti: format!("revocation-jti-{:08}", request.expected_generation),
                        operation_id: &request.operation_id,
                        request_sha256: &request_sha256,
                        generation: request.expected_generation,
                        key_generation: request.expected_key_generation,
                        credential_sha256: prior,
                        revoked: true,
                    };
                    let token = signed_jwt(&self.pair, "hwpx-agent-revocation+jwt", &claims);
                    IssuerReply::Revocation(must_ok(IssuerSecret::new(token)))
                }
            }
        }
    }

    impl CredentialIssuerTransport for TestIssuer {
        fn exchange(
            &mut self,
            authorization: &IssuerAuthorization,
            request: &[u8],
        ) -> Result<IssuerReply, IssuerTransportFailure> {
            self.calls += 1;
            assert_eq!(
                authorization.with_secret(str::to_owned),
                "Bearer aaa.bbb.ccc"
            );
            let parsed: TestRequest = must_ok(serde_json::from_slice(request));
            let canonical = must_ok(serde_json::to_vec(&parsed));
            assert_eq!(canonical, request);
            match self.replies.pop_front().unwrap_or(TestReply::Sign) {
                TestReply::Sign => Ok(self.signed_reply(&parsed)),
                TestReply::DefinitiveRejection => Ok(IssuerReply::DefinitiveRejection),
                TestReply::Unavailable => Err(IssuerTransportFailure::Unavailable),
                TestReply::PeerRejected => Err(IssuerTransportFailure::PeerRejected),
                TestReply::InvalidResponse => Err(IssuerTransportFailure::InvalidResponse),
            }
        }
    }

    #[derive(Debug, Default)]
    struct StaticAuthorization {
        calls: usize,
    }

    impl IssuerAuthorizationProvider for StaticAuthorization {
        fn authorization(&mut self) -> Result<IssuerAuthorization, AuthorizationFailure> {
            self.calls += 1;
            IssuerAuthorization::new("Bearer aaa.bbb.ccc".to_owned())
        }
    }

    #[derive(Default)]
    struct TestVault {
        secret: Option<Zeroizing<String>>,
        fail_store_before_write: bool,
        fail_store_after_write: bool,
        fail_delete_after_delete: bool,
        writes: usize,
        deletes: usize,
    }

    impl fmt::Debug for TestVault {
        fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter
                .debug_struct("TestVault")
                .field("present", &self.secret.is_some())
                .field("secret", &"<redacted>")
                .field("writes", &self.writes)
                .field("deletes", &self.deletes)
                .finish_non_exhaustive()
        }
    }

    impl CredentialVault for TestVault {
        fn observe(&mut self) -> Result<VaultObservation, VaultFailure> {
            Ok(self
                .secret
                .as_ref()
                .map_or(VaultObservation::Absent, |secret| {
                    VaultObservation::Present {
                        credential_sha256: digest_bytes(secret.as_bytes()),
                    }
                }))
        }

        fn store(&mut self, credential: &str) -> Result<(), VaultFailure> {
            self.writes += 1;
            if std::mem::take(&mut self.fail_store_before_write) {
                return Err(VaultFailure::Unavailable);
            }
            self.secret = Some(Zeroizing::new(credential.to_owned()));
            if std::mem::take(&mut self.fail_store_after_write) {
                return Err(VaultFailure::Unavailable);
            }
            Ok(())
        }

        fn delete(&mut self) -> Result<(), VaultFailure> {
            self.deletes += 1;
            self.secret = None;
            if std::mem::take(&mut self.fail_delete_after_delete) {
                return Err(VaultFailure::Unavailable);
            }
            Ok(())
        }
    }

    #[derive(Debug, Default)]
    struct MemoryStore {
        records: Vec<StoredRecord>,
        fail_before_sequence: Option<u64>,
        fail_after_sequence: Option<u64>,
    }

    impl CredentialStateStore for MemoryStore {
        fn load_latest(&mut self) -> Result<Option<StoredRecord>, StoreFailure> {
            Ok(self.records.last().cloned())
        }

        fn append(
            &mut self,
            expected: Option<&StoredRevision>,
            bytes: &[u8],
        ) -> Result<StoredRecord, StoreFailure> {
            if self.records.last().map(StoredRecord::revision) != expected {
                return Err(StoreFailure::Conflict);
            }
            let sequence = expected.map_or(1, |revision| revision.sequence() + 1);
            if self.fail_before_sequence == Some(sequence) {
                self.fail_before_sequence = None;
                return Err(StoreFailure::Unavailable);
            }
            let record = StoredRecord::new(sequence, expected.cloned(), bytes.to_vec())?;
            self.records.push(record.clone());
            if self.fail_after_sequence == Some(sequence) {
                self.fail_after_sequence = None;
                return Err(StoreFailure::Unavailable);
            }
            Ok(record)
        }
    }

    type TestBroker = CredentialBroker<MemoryStore, TestVault, StaticAuthorization, TestIssuer>;

    fn new_broker(
        replies: impl IntoIterator<Item = TestReply>,
        store: MemoryStore,
        vault: TestVault,
    ) -> (LifecyclePolicy, TestBroker) {
        let pair = signing_key();
        let exact_policy = policy(&pair);
        let broker = must_ok(CredentialBroker::open(
            exact_policy.clone(),
            store,
            vault,
            StaticAuthorization::default(),
            TestIssuer::new(pair, replies),
        ));
        (exact_policy, broker)
    }

    fn begin_issue(broker: &mut TestBroker) {
        must_ok(broker.begin(
            LifecycleOperation::Issue,
            "operation-issue-0001".to_owned(),
            NOW,
        ));
    }

    fn issue(broker: &mut TestBroker) -> CredentialState {
        begin_issue(broker);
        match must_ok(broker.drive(NOW)) {
            DriveOutcome::Completed(state @ CredentialState::Active { .. }) => state,
            outcome => panic!("unexpected issue outcome: {outcome:?}"),
        }
    }

    #[test]
    fn issue_persists_pending_and_prepared_before_stable_vault_state() {
        let (_, mut broker) = new_broker([], MemoryStore::default(), TestVault::default());
        begin_issue(&mut broker);
        assert_eq!(must_ok(broker.phase()), BrokerPhase::AwaitingIssuer);
        let state = match must_ok(broker.drive(NOW)) {
            DriveOutcome::Completed(state) => state,
            outcome => panic!("unexpected outcome: {outcome:?}"),
        };
        let CredentialState::Active { credential } = state else {
            panic!("active state expected");
        };
        let (store, mut vault, authorization, transport) = broker.into_parts();
        assert_eq!(store.records.len(), 4);
        assert_eq!(authorization.calls, 1);
        assert_eq!(transport.calls, 1);
        assert_eq!(vault.writes, 1);
        assert_eq!(
            must_ok(vault.observe()),
            VaultObservation::Present {
                credential_sha256: credential.credential_sha256().to_owned()
            }
        );
    }

    #[test]
    fn unavailable_peer_and_invalid_responses_never_restore_pending() {
        for (reply, error) in [
            (TestReply::Unavailable, BrokerError::TransportUnavailable),
            (TestReply::PeerRejected, BrokerError::PeerRejected),
            (TestReply::InvalidResponse, BrokerError::InvalidResponse),
        ] {
            let (_, mut broker) = new_broker([reply], MemoryStore::default(), TestVault::default());
            begin_issue(&mut broker);
            assert_eq!(broker.drive(NOW).err(), Some(error));
            assert_eq!(must_ok(broker.phase()), BrokerPhase::AwaitingIssuer);
            let (store, mut vault, _, _) = broker.into_parts();
            assert_eq!(store.records.len(), 2);
            assert_eq!(must_ok(vault.observe()), VaultObservation::Absent);
        }
    }

    #[test]
    fn authenticated_definitive_rejection_alone_restores_prior_state() {
        let (_, mut broker) = new_broker(
            [TestReply::DefinitiveRejection],
            MemoryStore::default(),
            TestVault::default(),
        );
        begin_issue(&mut broker);
        assert_eq!(
            must_ok(broker.drive(NOW)),
            DriveOutcome::DefinitivelyRejected(CredentialState::Absent)
        );
        assert_eq!(
            must_ok(broker.phase()),
            BrokerPhase::Stable(CredentialState::Absent)
        );
        let (store, _, _, _) = broker.into_parts();
        assert_eq!(store.records.len(), 3);
    }

    #[test]
    fn refresh_rejection_preserves_exact_active_state_and_vault() {
        let (_, mut broker) = new_broker(
            [TestReply::Sign, TestReply::DefinitiveRejection],
            MemoryStore::default(),
            TestVault::default(),
        );
        let active = issue(&mut broker);
        must_ok(broker.begin(
            LifecycleOperation::Refresh,
            "operation-refresh-0001".to_owned(),
            NOW + 480,
        ));
        assert_eq!(
            must_ok(broker.drive(NOW + 480)),
            DriveOutcome::DefinitivelyRejected(active.clone())
        );
        assert_eq!(must_ok(broker.phase()), BrokerPhase::Stable(active.clone()));
        let (_, mut vault, _, transport) = broker.into_parts();
        let CredentialState::Active { credential } = active else {
            panic!("active state expected");
        };
        assert_eq!(
            must_ok(vault.observe()),
            VaultObservation::Present {
                credential_sha256: credential.credential_sha256().to_owned()
            }
        );
        assert_eq!(transport.calls, 2);
    }

    #[test]
    fn issue_refresh_rotate_and_revoke_share_one_exact_recovery_model() {
        let (_, mut broker) = new_broker([], MemoryStore::default(), TestVault::default());
        issue(&mut broker);
        must_ok(broker.begin(
            LifecycleOperation::Refresh,
            "operation-refresh-0001".to_owned(),
            NOW + 480,
        ));
        assert!(matches!(
            must_ok(broker.drive(NOW + 480)),
            DriveOutcome::Completed(CredentialState::Active { .. })
        ));
        must_ok(broker.begin(
            LifecycleOperation::Rotate,
            "operation-rotate-0001".to_owned(),
            NOW + 481,
        ));
        assert!(matches!(
            must_ok(broker.drive(NOW + 481)),
            DriveOutcome::Completed(CredentialState::Active { .. })
        ));
        must_ok(broker.begin(
            LifecycleOperation::Revoke,
            "operation-revoke-0001".to_owned(),
            NOW + 482,
        ));
        assert!(matches!(
            must_ok(broker.drive(NOW + 482)),
            DriveOutcome::Completed(CredentialState::Revoked { .. })
        ));
        let (store, mut vault, authorization, transport) = broker.into_parts();
        assert_eq!(store.records.len(), 13);
        assert_eq!(must_ok(vault.observe()), VaultObservation::Absent);
        assert_eq!(authorization.calls, 4);
        assert_eq!(transport.calls, 4);
    }

    #[test]
    fn prepared_access_recovers_before_and_after_ambiguous_vault_write() {
        for after_write in [false, true] {
            let vault = TestVault {
                fail_store_before_write: !after_write,
                fail_store_after_write: after_write,
                ..TestVault::default()
            };
            let (_, mut broker) = new_broker([], MemoryStore::default(), vault);
            begin_issue(&mut broker);
            assert_eq!(broker.drive(NOW).err(), Some(BrokerError::VaultUnavailable));
            assert_eq!(must_ok(broker.phase()), BrokerPhase::PreparedAccess);
            assert!(matches!(
                must_ok(broker.drive(NOW + 1)),
                DriveOutcome::Completed(CredentialState::Active { .. })
            ));
            let (store, mut vault, authorization, transport) = broker.into_parts();
            assert_eq!(store.records.len(), 4);
            assert!(matches!(
                must_ok(vault.observe()),
                VaultObservation::Present { .. }
            ));
            assert_eq!(
                transport.calls,
                if after_write { 1 } else { 2 },
                "a confirmed vault write must avoid a second issuer call"
            );
            assert_eq!(authorization.calls, transport.calls);
        }
    }

    #[test]
    fn vault_write_then_stable_append_failure_recovers_without_reissue() {
        let store = MemoryStore {
            fail_before_sequence: Some(4),
            ..MemoryStore::default()
        };
        let (_, mut broker) = new_broker([], store, TestVault::default());
        begin_issue(&mut broker);
        assert_eq!(broker.drive(NOW).err(), Some(BrokerError::StoreUnavailable));
        assert_eq!(must_ok(broker.phase()), BrokerPhase::PreparedAccess);
        assert!(matches!(
            must_ok(broker.drive(NOW + 1)),
            DriveOutcome::Completed(CredentialState::Active { .. })
        ));
        let (store, _, authorization, transport) = broker.into_parts();
        assert_eq!(store.records.len(), 4);
        assert_eq!(authorization.calls, 1);
        assert_eq!(transport.calls, 1);
    }

    #[test]
    fn revocation_delete_ambiguity_recovers_to_terminal_state() {
        let (policy, mut broker) = new_broker([], MemoryStore::default(), TestVault::default());
        issue(&mut broker);
        let (store, mut vault, authorization, transport) = broker.into_parts();
        vault.fail_delete_after_delete = true;
        let mut broker = must_ok(CredentialBroker::open(
            policy,
            store,
            vault,
            authorization,
            transport,
        ));
        must_ok(broker.begin(
            LifecycleOperation::Revoke,
            "operation-revoke-0001".to_owned(),
            NOW + 1,
        ));
        assert_eq!(
            broker.drive(NOW + 1).err(),
            Some(BrokerError::VaultUnavailable)
        );
        assert_eq!(must_ok(broker.phase()), BrokerPhase::PreparedRevocation);
        assert!(matches!(
            must_ok(broker.drive(NOW + 2)),
            DriveOutcome::Completed(CredentialState::Revoked { .. })
        ));
        let (store, mut vault, _, transport) = broker.into_parts();
        assert_eq!(store.records.len(), 7);
        assert_eq!(must_ok(vault.observe()), VaultObservation::Absent);
        assert_eq!(transport.calls, 2);
    }

    #[test]
    fn append_only_file_store_reopens_and_detects_record_tamper() {
        let directory = must_ok(tempdir());
        let malformed_temporary = directory.path().join(".pending-garbage.tmp");
        must_ok(fs::write(&malformed_temporary, []));
        let mut malformed_store = must_ok(AppendOnlyCredentialStateStore::new(directory.path()));
        assert_eq!(
            malformed_store.load_latest().err(),
            Some(StoreFailure::Rejected)
        );
        must_ok(fs::remove_file(&malformed_temporary));

        let oversized_temporary =
            directory
                .path()
                .join(format!(".pending-{:020}-{}.tmp", 1, "0".repeat(32)));
        must_ok(fs::write(
            &oversized_temporary,
            vec![0_u8; MAX_RECORD_BYTES + 1],
        ));
        let mut oversized_store = must_ok(AppendOnlyCredentialStateStore::new(directory.path()));
        assert_eq!(
            oversized_store.load_latest().err(),
            Some(StoreFailure::Rejected)
        );
        must_ok(fs::remove_file(&oversized_temporary));

        let store = must_ok(AppendOnlyCredentialStateStore::new(directory.path()));
        let pair = signing_key();
        let policy = policy(&pair);
        let mut broker = must_ok(CredentialBroker::open(
            policy,
            store,
            TestVault::default(),
            StaticAuthorization::default(),
            TestIssuer::new(pair, []),
        ));
        must_ok(broker.begin(
            LifecycleOperation::Issue,
            "operation-issue-0001".to_owned(),
            NOW,
        ));
        assert!(matches!(
            must_ok(broker.drive(NOW)),
            DriveOutcome::Completed(CredentialState::Active { .. })
        ));
        let (_, _, _, _) = broker.into_parts();
        let mut records: Vec<_> = must_ok(fs::read_dir(directory.path()))
            .map(|entry| must_ok(entry).path())
            .filter(|path| path.extension().is_some_and(|value| value == "json"))
            .collect();
        records.sort();
        assert_eq!(records.len(), 4);

        let history_directory = must_ok(tempdir());
        for record in &records {
            let file_name = record
                .file_name()
                .unwrap_or_else(|| panic!("record file name missing"));
            must_ok(fs::copy(record, history_directory.path().join(file_name)));
        }
        let first = records
            .first()
            .unwrap_or_else(|| panic!("first record missing"));
        let first_name = first
            .file_name()
            .unwrap_or_else(|| panic!("first record file name missing"));
        let copied_first = history_directory.path().join(first_name);
        let mut earlier_tamper = vec![b' '];
        earlier_tamper.extend(must_ok(fs::read(&copied_first)));
        let tampered_first = history_directory.path().join(format!(
            "{:020}-{}.json",
            1,
            digest_bytes(&earlier_tamper)
        ));
        must_ok(fs::rename(&copied_first, &tampered_first));
        must_ok(fs::write(&tampered_first, earlier_tamper));
        let mut history_store = must_ok(AppendOnlyCredentialStateStore::new(
            history_directory.path(),
        ));
        assert_eq!(
            history_store.load_latest().err(),
            Some(StoreFailure::Rejected)
        );

        let latest = records
            .last()
            .unwrap_or_else(|| panic!("latest record missing"));
        let mut tampered = must_ok(fs::read(latest));
        tampered[0] ^= 1;
        must_ok(fs::write(latest, tampered));
        let mut store = must_ok(AppendOnlyCredentialStateStore::new(directory.path()));
        assert_eq!(store.load_latest().err(), Some(StoreFailure::Rejected));
    }

    #[test]
    fn policy_drift_or_orphaned_vault_fails_closed_without_overwrite() {
        let pair = signing_key();
        let original = policy(&pair);
        let broker = must_ok(CredentialBroker::open(
            original,
            MemoryStore::default(),
            TestVault::default(),
            StaticAuthorization::default(),
            TestIssuer::new(pair, []),
        ));
        let (store, vault, authorization, transport) = broker.into_parts();
        let other_pair = signing_key();
        let drifted = policy(&other_pair);
        assert_eq!(
            CredentialBroker::open(drifted, store, vault, authorization, transport).err(),
            Some(BrokerError::InvalidState)
        );

        let orphaned = TestVault {
            secret: Some(Zeroizing::new("aaa.bbb.ccc".to_owned())),
            ..TestVault::default()
        };
        let pair = signing_key();
        assert_eq!(
            CredentialBroker::open(
                policy(&pair),
                MemoryStore::default(),
                orphaned,
                StaticAuthorization::default(),
                TestIssuer::new(pair, []),
            )
            .err(),
            Some(BrokerError::InvalidState)
        );
    }

    #[test]
    fn durable_record_unknown_duplicate_noncanonical_and_chain_drift_are_rejected() {
        let pair = signing_key();
        let exact_policy = policy(&pair);
        let broker = must_ok(CredentialBroker::open(
            exact_policy.clone(),
            MemoryStore::default(),
            TestVault::default(),
            StaticAuthorization::default(),
            TestIssuer::new(pair, []),
        ));
        let (store, vault, authorization, transport) = broker.into_parts();
        let valid = store
            .records
            .last()
            .cloned()
            .unwrap_or_else(|| panic!("initial state record missing"));
        let text = String::from_utf8(valid.bytes.clone())
            .unwrap_or_else(|error| panic!("record UTF-8: {error}"));
        let unknown = text.replacen(
            "\"schema_version\":",
            "\"unknown\":0,\"schema_version\":",
            1,
        );
        let duplicate = text.replacen(
            "\"schema_version\":",
            &format!("\"schema_version\":\"{RECORD_SCHEMA_VERSION}\",\"schema_version\":"),
            1,
        );
        for invalid in [format!(" {text}"), unknown, duplicate] {
            let mut invalid_store = MemoryStore::default();
            invalid_store
                .records
                .push(must_ok(StoredRecord::new(1, None, invalid.into_bytes())));
            let pair = signing_key();
            assert_eq!(
                CredentialBroker::open(
                    policy(&pair),
                    invalid_store,
                    TestVault::default(),
                    StaticAuthorization::default(),
                    TestIssuer::new(pair, []),
                )
                .err(),
                Some(BrokerError::InvalidState)
            );
        }

        let wrong_previous = StoredRevision {
            sequence: 1,
            record_sha256: "0".repeat(64),
        };
        let chained = must_ok(StoredRecord::new(
            2,
            Some(wrong_previous),
            valid.bytes.clone(),
        ));
        let mut invalid_store = MemoryStore::default();
        invalid_store.records.push(chained);
        assert_eq!(
            CredentialBroker::open(exact_policy, invalid_store, vault, authorization, transport,)
                .err(),
            Some(BrokerError::InvalidState)
        );
    }

    #[test]
    fn issuer_response_is_canonical_request_bound_and_redacted() {
        let request = br#"{"operation":"issue"}"#;
        let request_sha256 = digest_bytes(request);
        let access = format!(
            "{{\"outcome\":\"access\",\"schema_version\":\"{RESPONSE_SCHEMA_VERSION}\",\"request_sha256\":\"{request_sha256}\",\"token\":\"aaa.bbb.ccc\"}}"
        );
        let reply = must_ok(parse_issuer_response(request, access.as_bytes()));
        assert!(!format!("{reply:?}").contains("aaa"));
        assert!(matches!(reply, IssuerReply::Access(_)));

        let rejected = format!(
            "{{\"outcome\":\"rejected\",\"schema_version\":\"{RESPONSE_SCHEMA_VERSION}\",\"request_sha256\":\"{request_sha256}\"}}"
        );
        assert!(matches!(
            must_ok(parse_issuer_response(request, rejected.as_bytes())),
            IssuerReply::DefinitiveRejection
        ));

        let duplicate = access.replacen(
            "\"outcome\":\"access\"",
            "\"outcome\":\"access\",\"outcome\":\"access\"",
            1,
        );
        for invalid in [
            duplicate,
            access.replace(&request_sha256, &"0".repeat(64)),
            format!(" {access}"),
            access.replace("\"token\":", "\"unknown\":0,\"token\":"),
        ] {
            assert_eq!(
                parse_issuer_response(request, invalid.as_bytes()).err(),
                Some(IssuerTransportFailure::InvalidResponse)
            );
        }
    }

    #[test]
    fn authorization_and_all_debug_outputs_are_bounded_and_redacted() {
        for invalid in [
            "",
            "bearer aaa.bbb.ccc",
            "Bearer aaa.bbb",
            "Bearer aaa.bbb.ccc.ddd",
            "Bearer aa=.bbb.ccc",
            "Bearer aaa.비ASCII.ccc",
        ] {
            assert_eq!(
                IssuerAuthorization::new(invalid.to_owned()).err(),
                Some(AuthorizationFailure::Rejected)
            );
        }
        let authorization = must_ok(IssuerAuthorization::new(
            "Bearer secret.header.signature".to_owned(),
        ));
        let secret = must_ok(IssuerSecret::new("secret.header.signature".to_owned()));
        assert!(!format!("{authorization:?}").contains("secret"));
        assert!(!format!("{secret:?}").contains("secret"));
        let (_, broker) = new_broker([], MemoryStore::default(), TestVault::default());
        let debug = format!("{broker:?}");
        assert!(debug.contains("<redacted>"));
        assert!(!debug.contains(ISSUER));
        assert!(!debug.contains(SUBJECT));
    }
}
