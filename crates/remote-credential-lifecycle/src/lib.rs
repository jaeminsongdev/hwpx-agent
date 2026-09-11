//! Exact, fail-closed lifecycle model for externally issued remote-sync credentials.
//!
//! The model is intentionally transport- and vault-independent. A trusted broker persists the
//! non-secret pending state before an issuer call, retries the exact request after an uncertain
//! outcome, and atomically installs or removes the returned secret together with the stable state.

#![forbid(unsafe_code)]

use std::fmt;

use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use ring::signature::{ED25519, UnparsedPublicKey};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use zeroize::Zeroizing;

const REQUEST_SCHEMA_VERSION: &str = "hwpx-agent.remote-credential-lifecycle-request/v1";
const PENDING_SCHEMA_VERSION: &str = "hwpx-agent.remote-credential-pending/v1";
const POLICY_BINDING_SCHEMA_VERSION: &str = "hwpx-agent.remote-credential-policy-binding/v1";
const ACCESS_TOKEN_TYPE: &str = "hwpx-agent-service+jwt";
const REVOCATION_TYPE: &str = "hwpx-agent-revocation+jwt";
const REQUIRED_SCOPE: &str = "mirror.sync";
const MAX_IDENTIFIER_BYTES: usize = 240;
const MAX_KEY_ID_BYTES: usize = 64;
const MAX_OPERATION_ID_BYTES: usize = 120;
const MIN_OPERATION_ID_BYTES: usize = 16;
const MAX_JTI_BYTES: usize = 120;
const MIN_JTI_BYTES: usize = 16;
const MAX_TOKEN_BYTES: usize = 2_560;
const MAX_HEADER_BYTES: usize = 1_024;
const MAX_CLAIMS_BYTES: usize = 4_096;
const MAX_PENDING_JSON_BYTES: usize = 16_384;
const MAX_KEYS: usize = 8;

/// Closed lifecycle failure vocabulary. No variant carries issuer, credential or identifier data.
#[derive(Clone, Copy, Debug, Eq, PartialEq, thiserror::Error)]
pub enum LifecycleError {
    #[error("credential lifecycle policy is invalid")]
    InvalidPolicy,
    #[error("credential lifecycle state is invalid")]
    InvalidState,
    #[error("credential lifecycle operation is invalid")]
    InvalidOperation,
    #[error("credential refresh is not due")]
    NotDue,
    #[error("credential has expired")]
    Expired,
    #[error("credential lifecycle arithmetic overflow")]
    Overflow,
    #[error("issuer response is invalid")]
    InvalidResponse,
    #[error("issuer signature was rejected")]
    SignatureRejected,
    #[error("pending credential operation has expired")]
    PendingExpired,
    #[error("credential lifecycle serialization failed")]
    Serialization,
}

/// One pinned Ed25519 issuer verification key.
#[derive(Clone, Eq, PartialEq)]
pub struct IssuerKey {
    key_id: String,
    public_key: [u8; 32],
}

impl fmt::Debug for IssuerKey {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IssuerKey")
            .field("key_id", &"<redacted>")
            .field("public_key", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl IssuerKey {
    /// Creates one exact Ed25519 key binding.
    ///
    /// # Errors
    ///
    /// Rejects malformed key identifiers or an all-zero public key.
    pub fn new(key_id: String, public_key: [u8; 32]) -> Result<Self, LifecycleError> {
        validate_token_identifier(&key_id, 1, MAX_KEY_ID_BYTES)
            .map_err(|()| LifecycleError::InvalidPolicy)?;
        if public_key.iter().all(|byte| *byte == 0) {
            return Err(LifecycleError::InvalidPolicy);
        }
        Ok(Self { key_id, public_key })
    }
}

/// Immutable verification and lifetime policy for one remote-sync identity.
#[derive(Clone, Eq, PartialEq)]
pub struct LifecyclePolicy {
    issuer: String,
    subject: String,
    audience: String,
    keys: Vec<IssuerKey>,
    minimum_lifetime_seconds: u64,
    maximum_lifetime_seconds: u64,
    refresh_before_seconds: u64,
    clock_skew_seconds: u64,
    pending_timeout_seconds: u64,
}

impl fmt::Debug for LifecyclePolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LifecyclePolicy")
            .field("identity", &"<redacted>")
            .field("key_count", &self.keys.len())
            .field("lifetime_policy", &"<bounded>")
            .finish_non_exhaustive()
    }
}

impl LifecyclePolicy {
    /// Creates one exact issuer/subject/audience binding and bounded lifetime policy.
    ///
    /// # Errors
    ///
    /// Rejects non-canonical identities, duplicate keys, unsafe bounds and empty key sets.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        issuer: String,
        subject: String,
        audience: String,
        keys: Vec<IssuerKey>,
        minimum_lifetime_seconds: u64,
        maximum_lifetime_seconds: u64,
        refresh_before_seconds: u64,
        clock_skew_seconds: u64,
        pending_timeout_seconds: u64,
    ) -> Result<Self, LifecycleError> {
        validate_issuer(&issuer)?;
        validate_token_identifier(&subject, 1, MAX_IDENTIFIER_BYTES)
            .map_err(|()| LifecycleError::InvalidPolicy)?;
        validate_token_identifier(&audience, 1, MAX_IDENTIFIER_BYTES)
            .map_err(|()| LifecycleError::InvalidPolicy)?;
        if keys.is_empty()
            || keys.len() > MAX_KEYS
            || minimum_lifetime_seconds < 60
            || maximum_lifetime_seconds < minimum_lifetime_seconds
            || maximum_lifetime_seconds > 86_400
            || refresh_before_seconds < 30
            || refresh_before_seconds >= minimum_lifetime_seconds
            || clock_skew_seconds > 300
            || refresh_before_seconds
                .checked_add(clock_skew_seconds)
                .is_none_or(|value| value >= minimum_lifetime_seconds)
            || !(30..=600).contains(&pending_timeout_seconds)
        {
            return Err(LifecycleError::InvalidPolicy);
        }
        for (index, key) in keys.iter().enumerate() {
            if keys[..index].iter().any(|other| other.key_id == key.key_id) {
                return Err(LifecycleError::InvalidPolicy);
            }
        }
        Ok(Self {
            issuer,
            subject,
            audience,
            keys,
            minimum_lifetime_seconds,
            maximum_lifetime_seconds,
            refresh_before_seconds,
            clock_skew_seconds,
            pending_timeout_seconds,
        })
    }

    fn binding_sha256(&self) -> Result<String, LifecycleError> {
        #[derive(Serialize)]
        struct KeyBinding<'a> {
            key_id: &'a str,
            public_key_sha256: String,
        }

        #[derive(Serialize)]
        struct Binding<'a> {
            schema_version: &'static str,
            issuer: &'a str,
            subject: &'a str,
            audience: &'a str,
            scope: &'static str,
            keys: Vec<KeyBinding<'a>>,
            minimum_lifetime_seconds: u64,
            maximum_lifetime_seconds: u64,
            refresh_before_seconds: u64,
            clock_skew_seconds: u64,
            pending_timeout_seconds: u64,
        }
        canonical_digest(&Binding {
            schema_version: POLICY_BINDING_SCHEMA_VERSION,
            issuer: &self.issuer,
            subject: &self.subject,
            audience: &self.audience,
            scope: REQUIRED_SCOPE,
            keys: self
                .keys
                .iter()
                .map(|key| KeyBinding {
                    key_id: &key.key_id,
                    public_key_sha256: digest_bytes(&key.public_key),
                })
                .collect(),
            minimum_lifetime_seconds: self.minimum_lifetime_seconds,
            maximum_lifetime_seconds: self.maximum_lifetime_seconds,
            refresh_before_seconds: self.refresh_before_seconds,
            clock_skew_seconds: self.clock_skew_seconds,
            pending_timeout_seconds: self.pending_timeout_seconds,
        })
    }

    fn key(&self, key_id: &str) -> Option<&IssuerKey> {
        self.keys.iter().find(|key| key.key_id == key_id)
    }
}

/// Exact transition requested from the issuer.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum LifecycleOperation {
    Issue,
    Refresh,
    Rotate,
    Revoke,
}

/// Stable metadata for one active access token. The raw token is never serialized here.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ActiveCredential {
    generation: u64,
    key_generation: u64,
    credential_sha256: String,
    credential_id_sha256: String,
    issuer_key_id_sha256: String,
    issued_at: u64,
    not_before: u64,
    refresh_at: u64,
    expires_at: u64,
    last_operation_id_sha256: String,
}

impl fmt::Debug for ActiveCredential {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ActiveCredential")
            .field("generation", &self.generation)
            .field("key_generation", &self.key_generation)
            .field("digests", &"<redacted>")
            .field("lifetime", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl ActiveCredential {
    #[must_use]
    pub const fn generation(&self) -> u64 {
        self.generation
    }

    #[must_use]
    pub const fn key_generation(&self) -> u64 {
        self.key_generation
    }

    #[must_use]
    pub const fn refresh_at(&self) -> u64 {
        self.refresh_at
    }

    #[must_use]
    pub const fn expires_at(&self) -> u64 {
        self.expires_at
    }

    #[must_use]
    pub fn credential_sha256(&self) -> &str {
        &self.credential_sha256
    }
}

/// Terminal non-secret revocation metadata for one binding.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RevokedCredential {
    generation: u64,
    key_generation: u64,
    prior_credential_sha256: String,
    revocation_receipt_sha256: String,
    revoked_at: u64,
    operation_id_sha256: String,
}

impl fmt::Debug for RevokedCredential {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RevokedCredential")
            .field("generation", &self.generation)
            .field("key_generation", &self.key_generation)
            .field("details", &"<redacted>")
            .finish_non_exhaustive()
    }
}

/// One stable lifecycle state. Revoked is terminal for the same binding.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "state", rename_all = "snake_case", deny_unknown_fields)]
pub enum CredentialState {
    Absent,
    Active { credential: ActiveCredential },
    Revoked { credential: RevokedCredential },
}

impl CredentialState {
    #[must_use]
    pub const fn active(&self) -> Option<&ActiveCredential> {
        match self {
            Self::Active { credential } => Some(credential),
            Self::Absent | Self::Revoked { .. } => None,
        }
    }
}

/// Persisted non-secret pending transition. Its canonical request is replayable byte-for-byte.
#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PendingTransition {
    schema_version: String,
    operation: LifecycleOperation,
    operation_id: String,
    binding_sha256: String,
    request_sha256: String,
    expected_generation: u64,
    expected_key_generation: u64,
    prior_credential_sha256: Option<String>,
    requested_at: u64,
    deadline: u64,
    before: CredentialState,
}

impl fmt::Debug for PendingTransition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PendingTransition")
            .field("operation", &self.operation)
            .field("identity", &"<redacted>")
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl PendingTransition {
    #[must_use]
    pub const fn operation(&self) -> LifecycleOperation {
        self.operation
    }

    #[must_use]
    pub fn request_sha256(&self) -> &str {
        &self.request_sha256
    }

    /// Returns the exact issuer request bytes for first dispatch or retry.
    ///
    /// # Errors
    ///
    /// Rejects policy/state drift or an expired pending window.
    pub fn retry_request(
        &self,
        policy: &LifecyclePolicy,
        now: u64,
    ) -> Result<Vec<u8>, LifecycleError> {
        self.validate(policy)?;
        if now > self.deadline {
            return Err(LifecycleError::PendingExpired);
        }
        self.request_bytes()
    }

    /// Encodes the complete non-secret pending state in one canonical bounded JSON value.
    ///
    /// # Errors
    ///
    /// Rejects policy/state drift or serialization failure.
    pub fn to_canonical_json(&self, policy: &LifecyclePolicy) -> Result<Vec<u8>, LifecycleError> {
        self.validate(policy)?;
        let encoded = serde_json::to_vec(self).map_err(|_| LifecycleError::Serialization)?;
        if encoded.is_empty() || encoded.len() > MAX_PENDING_JSON_BYTES {
            return Err(LifecycleError::Serialization);
        }
        Ok(encoded)
    }

    /// Restores only the exact canonical JSON representation.
    ///
    /// # Errors
    ///
    /// Rejects oversized, unknown, duplicate, non-canonical or policy-drifted input.
    pub fn from_canonical_json(
        policy: &LifecyclePolicy,
        encoded: &[u8],
    ) -> Result<Self, LifecycleError> {
        if encoded.is_empty() || encoded.len() > MAX_PENDING_JSON_BYTES {
            return Err(LifecycleError::Serialization);
        }
        let value: Self =
            serde_json::from_slice(encoded).map_err(|_| LifecycleError::Serialization)?;
        value.validate(policy)?;
        if value.to_canonical_json(policy)? != encoded {
            return Err(LifecycleError::Serialization);
        }
        Ok(value)
    }

    fn validate(&self, policy: &LifecyclePolicy) -> Result<(), LifecycleError> {
        let expected = build_pending(
            policy,
            &self.before,
            self.operation,
            self.operation_id.clone(),
            self.requested_at,
        )?;
        if *self != expected {
            return Err(LifecycleError::InvalidState);
        }
        Ok(())
    }

    fn request(&self) -> WireRequest<'_> {
        WireRequest {
            schema_version: REQUEST_SCHEMA_VERSION,
            operation: self.operation,
            operation_id: &self.operation_id,
            binding_sha256: &self.binding_sha256,
            expected_generation: self.expected_generation,
            expected_key_generation: self.expected_key_generation,
            prior_credential_sha256: self.prior_credential_sha256.as_deref(),
            requested_at: self.requested_at,
        }
    }

    fn request_bytes(&self) -> Result<Vec<u8>, LifecycleError> {
        serde_json::to_vec(&self.request()).map_err(|_| LifecycleError::Serialization)
    }
}

/// Verified access-token output. Only this object contains the raw token and zeroizes it on drop.
pub struct VerifiedCredential {
    secret: Zeroizing<String>,
    metadata: ActiveCredential,
}

impl fmt::Debug for VerifiedCredential {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("VerifiedCredential")
            .field("secret", &"<redacted>")
            .field("metadata", &self.metadata)
            .finish()
    }
}

impl VerifiedCredential {
    #[must_use]
    pub const fn metadata(&self) -> &ActiveCredential {
        &self.metadata
    }

    /// Provides short lexical access for a trusted vault adapter without cloning the secret.
    pub fn with_secret<R>(&self, operation: impl FnOnce(&str) -> R) -> R {
        operation(self.secret.as_str())
    }
}

#[derive(Serialize)]
struct WireRequest<'a> {
    schema_version: &'static str,
    operation: LifecycleOperation,
    operation_id: &'a str,
    binding_sha256: &'a str,
    expected_generation: u64,
    expected_key_generation: u64,
    prior_credential_sha256: Option<&'a str>,
    requested_at: u64,
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
struct AccessClaims {
    iss: String,
    sub: String,
    aud: String,
    scope: String,
    iat: u64,
    nbf: u64,
    exp: u64,
    jti: String,
    operation_id: String,
    request_sha256: String,
    generation: u64,
    key_generation: u64,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct RevocationClaims {
    iss: String,
    sub: String,
    aud: String,
    iat: u64,
    jti: String,
    operation_id: String,
    request_sha256: String,
    generation: u64,
    key_generation: u64,
    credential_sha256: String,
    revoked: bool,
}

/// Starts one exact transition without changing the caller's stable state.
///
/// The caller must durably persist the returned pending value before dispatching its canonical
/// request. Retrying uses the same operation ID and request digest.
///
/// # Errors
///
/// Rejects invalid state, terminal revocation, premature refresh, expiry and arithmetic overflow.
pub fn begin_transition(
    policy: &LifecyclePolicy,
    state: &CredentialState,
    operation: LifecycleOperation,
    operation_id: String,
    now: u64,
) -> Result<PendingTransition, LifecycleError> {
    build_pending(policy, state, operation, operation_id, now)
}

fn build_pending(
    policy: &LifecyclePolicy,
    state: &CredentialState,
    operation: LifecycleOperation,
    operation_id: String,
    now: u64,
) -> Result<PendingTransition, LifecycleError> {
    if now == 0 {
        return Err(LifecycleError::InvalidState);
    }
    validate_token_identifier(
        &operation_id,
        MIN_OPERATION_ID_BYTES,
        MAX_OPERATION_ID_BYTES,
    )
    .map_err(|()| LifecycleError::InvalidOperation)?;
    validate_state(policy, state)?;
    if state.active().is_some_and(|credential| {
        credential.last_operation_id_sha256 == digest_bytes(operation_id.as_bytes())
    }) {
        return Err(LifecycleError::InvalidOperation);
    }
    let (expected_generation, expected_key_generation, prior_credential_sha256) =
        transition_numbers(state, operation, now)?;
    let binding_sha256 = policy.binding_sha256()?;
    let deadline = now
        .checked_add(policy.pending_timeout_seconds)
        .ok_or(LifecycleError::Overflow)?;
    let provisional = PendingTransition {
        schema_version: PENDING_SCHEMA_VERSION.to_owned(),
        operation,
        operation_id,
        binding_sha256,
        request_sha256: String::new(),
        expected_generation,
        expected_key_generation,
        prior_credential_sha256,
        requested_at: now,
        deadline,
        before: state.clone(),
    };
    let request_sha256 = digest_bytes(&provisional.request_bytes()?);
    Ok(PendingTransition {
        request_sha256,
        ..provisional
    })
}

fn transition_numbers(
    state: &CredentialState,
    operation: LifecycleOperation,
    now: u64,
) -> Result<(u64, u64, Option<String>), LifecycleError> {
    match (state, operation) {
        (CredentialState::Absent, LifecycleOperation::Issue) => Ok((1, 1, None)),
        (CredentialState::Active { credential }, LifecycleOperation::Refresh) => {
            if now < credential.refresh_at {
                return Err(LifecycleError::NotDue);
            }
            if now >= credential.expires_at {
                return Err(LifecycleError::Expired);
            }
            Ok((
                credential
                    .generation
                    .checked_add(1)
                    .ok_or(LifecycleError::Overflow)?,
                credential.key_generation,
                Some(credential.credential_sha256.clone()),
            ))
        }
        (CredentialState::Active { credential }, LifecycleOperation::Rotate) => {
            if now >= credential.expires_at {
                return Err(LifecycleError::Expired);
            }
            Ok((
                credential
                    .generation
                    .checked_add(1)
                    .ok_or(LifecycleError::Overflow)?,
                credential
                    .key_generation
                    .checked_add(1)
                    .ok_or(LifecycleError::Overflow)?,
                Some(credential.credential_sha256.clone()),
            ))
        }
        (CredentialState::Active { credential }, LifecycleOperation::Revoke) => Ok((
            credential.generation,
            credential.key_generation,
            Some(credential.credential_sha256.clone()),
        )),
        (CredentialState::Revoked { .. } | CredentialState::Absent, _)
        | (CredentialState::Active { .. }, LifecycleOperation::Issue) => {
            Err(LifecycleError::InvalidOperation)
        }
    }
}

/// Verifies an exact Ed25519 access JWT and returns zeroizing secret material plus stable metadata.
///
/// # Errors
///
/// Rejects wrong type/algorithm/key/signature, claim drift, replayed token material, lifetime drift,
/// wrong transition numbers and pending expiry.
pub fn verify_access_token(
    policy: &LifecyclePolicy,
    pending: &PendingTransition,
    token: String,
    now: u64,
) -> Result<VerifiedCredential, LifecycleError> {
    pending.validate(policy)?;
    if pending.operation == LifecycleOperation::Revoke {
        return Err(LifecycleError::InvalidOperation);
    }
    if now > pending.deadline {
        return Err(LifecycleError::PendingExpired);
    }
    let token = Zeroizing::new(token);
    let (header, claims_bytes) = verify_compact_jws(policy, token.as_str(), ACCESS_TOKEN_TYPE)?;
    let claims: AccessClaims =
        serde_json::from_slice(&claims_bytes).map_err(|_| LifecycleError::InvalidResponse)?;
    require_canonical_json(&claims_bytes, &claims)?;
    validate_token_identifier(&claims.jti, MIN_JTI_BYTES, MAX_JTI_BYTES)
        .map_err(|()| LifecycleError::InvalidResponse)?;
    if claims.iss != policy.issuer
        || claims.sub != policy.subject
        || claims.aud != policy.audience
        || claims.scope != REQUIRED_SCOPE
        || claims.operation_id != pending.operation_id
        || claims.request_sha256 != pending.request_sha256
        || claims.generation != pending.expected_generation
        || claims.key_generation != pending.expected_key_generation
    {
        return Err(LifecycleError::InvalidResponse);
    }
    validate_access_times(policy, &claims, pending, now)?;
    let credential_sha256 = digest_bytes(token.as_bytes());
    if pending.prior_credential_sha256.as_deref() == Some(credential_sha256.as_str()) {
        return Err(LifecycleError::InvalidResponse);
    }
    let refresh_at = claims
        .exp
        .checked_sub(policy.refresh_before_seconds)
        .ok_or(LifecycleError::InvalidResponse)?;
    let credential_id_sha256 = digest_bytes(claims.jti.as_bytes());
    if pending
        .before
        .active()
        .is_some_and(|prior| prior.credential_id_sha256 == credential_id_sha256)
    {
        return Err(LifecycleError::InvalidResponse);
    }
    let metadata = ActiveCredential {
        generation: claims.generation,
        key_generation: claims.key_generation,
        credential_sha256,
        credential_id_sha256,
        issuer_key_id_sha256: digest_bytes(header.kid.as_bytes()),
        issued_at: claims.iat,
        not_before: claims.nbf,
        refresh_at,
        expires_at: claims.exp,
        last_operation_id_sha256: digest_bytes(claims.operation_id.as_bytes()),
    };
    validate_active(policy, &metadata)?;
    Ok(VerifiedCredential {
        secret: token,
        metadata,
    })
}

/// Verifies a distinct signed revocation JWT and returns terminal non-secret state.
///
/// # Errors
///
/// Rejects wrong transition, type/algorithm/key/signature, claim drift or pending expiry.
pub fn verify_revocation(
    policy: &LifecyclePolicy,
    pending: &PendingTransition,
    receipt_jwt: &str,
    now: u64,
) -> Result<RevokedCredential, LifecycleError> {
    pending.validate(policy)?;
    if pending.operation != LifecycleOperation::Revoke {
        return Err(LifecycleError::InvalidOperation);
    }
    if now > pending.deadline {
        return Err(LifecycleError::PendingExpired);
    }
    let (_, claims_bytes) = verify_compact_jws(policy, receipt_jwt, REVOCATION_TYPE)?;
    let claims: RevocationClaims =
        serde_json::from_slice(&claims_bytes).map_err(|_| LifecycleError::InvalidResponse)?;
    require_canonical_json(&claims_bytes, &claims)?;
    validate_token_identifier(&claims.jti, MIN_JTI_BYTES, MAX_JTI_BYTES)
        .map_err(|()| LifecycleError::InvalidResponse)?;
    let prior = pending
        .prior_credential_sha256
        .as_deref()
        .ok_or(LifecycleError::InvalidState)?;
    let receipt_id_sha256 = digest_bytes(claims.jti.as_bytes());
    if pending
        .before
        .active()
        .is_none_or(|credential| credential.credential_id_sha256 == receipt_id_sha256)
    {
        return Err(LifecycleError::InvalidResponse);
    }
    let latest_allowed = now
        .checked_add(policy.clock_skew_seconds)
        .ok_or(LifecycleError::Overflow)?;
    let requested_with_skew = pending
        .requested_at
        .checked_add(policy.clock_skew_seconds)
        .ok_or(LifecycleError::Overflow)?;
    let issued_with_skew = claims
        .iat
        .checked_add(policy.clock_skew_seconds)
        .ok_or(LifecycleError::Overflow)?;
    if claims.iss != policy.issuer
        || claims.sub != policy.subject
        || claims.aud != policy.audience
        || claims.operation_id != pending.operation_id
        || claims.request_sha256 != pending.request_sha256
        || claims.generation != pending.expected_generation
        || claims.key_generation != pending.expected_key_generation
        || claims.credential_sha256 != prior
        || !claims.revoked
        || claims.iat > latest_allowed
        || requested_with_skew < claims.iat
        || issued_with_skew < pending.requested_at
    {
        return Err(LifecycleError::InvalidResponse);
    }
    Ok(RevokedCredential {
        generation: claims.generation,
        key_generation: claims.key_generation,
        prior_credential_sha256: prior.to_owned(),
        revocation_receipt_sha256: digest_bytes(receipt_jwt.as_bytes()),
        revoked_at: claims.iat,
        operation_id_sha256: digest_bytes(claims.operation_id.as_bytes()),
    })
}

/// Restores the exact previous stable state after an authenticated definitive rejection.
///
/// An unavailable or ambiguous issuer outcome must retain the pending transition and retry it.
///
/// # Errors
///
/// Rejects policy drift and rejection after the reconciliation deadline.
pub fn apply_definitive_rejection(
    policy: &LifecyclePolicy,
    pending: PendingTransition,
    now: u64,
) -> Result<CredentialState, LifecycleError> {
    pending.validate(policy)?;
    if now > pending.deadline {
        return Err(LifecycleError::PendingExpired);
    }
    Ok(pending.before)
}

fn validate_access_times(
    policy: &LifecyclePolicy,
    claims: &AccessClaims,
    pending: &PendingTransition,
    now: u64,
) -> Result<(), LifecycleError> {
    let lifetime = claims
        .exp
        .checked_sub(claims.iat)
        .ok_or(LifecycleError::InvalidResponse)?;
    let latest_allowed = now
        .checked_add(policy.clock_skew_seconds)
        .ok_or(LifecycleError::Overflow)?;
    let requested_with_skew = pending
        .requested_at
        .checked_add(policy.clock_skew_seconds)
        .ok_or(LifecycleError::Overflow)?;
    let iat_with_skew = claims
        .iat
        .checked_add(policy.clock_skew_seconds)
        .ok_or(LifecycleError::Overflow)?;
    let refresh_at = claims
        .exp
        .checked_sub(policy.refresh_before_seconds)
        .ok_or(LifecycleError::InvalidResponse)?;
    if lifetime < policy.minimum_lifetime_seconds
        || lifetime > policy.maximum_lifetime_seconds
        || claims.iat > latest_allowed
        || requested_with_skew < claims.iat
        || iat_with_skew < pending.requested_at
        || claims.nbf > latest_allowed
        || claims.nbf > iat_with_skew
        || now >= claims.exp
        || refresh_at <= claims.nbf
    {
        return Err(LifecycleError::InvalidResponse);
    }
    Ok(())
}

fn verify_compact_jws(
    policy: &LifecyclePolicy,
    compact: &str,
    expected_type: &str,
) -> Result<(JwtHeader, Vec<u8>), LifecycleError> {
    if compact.is_empty()
        || compact.len() > MAX_TOKEN_BYTES
        || !compact.is_ascii()
        || compact.contains('=')
    {
        return Err(LifecycleError::InvalidResponse);
    }
    let mut segments = compact.split('.');
    let header_segment = segments.next().ok_or(LifecycleError::InvalidResponse)?;
    let claims_segment = segments.next().ok_or(LifecycleError::InvalidResponse)?;
    let signature_segment = segments.next().ok_or(LifecycleError::InvalidResponse)?;
    if header_segment.is_empty()
        || claims_segment.is_empty()
        || signature_segment.is_empty()
        || segments.next().is_some()
    {
        return Err(LifecycleError::InvalidResponse);
    }
    let header_bytes = decode_segment(header_segment, MAX_HEADER_BYTES)?;
    let claims_bytes = decode_segment(claims_segment, MAX_CLAIMS_BYTES)?;
    let signature = decode_segment(signature_segment, 64)?;
    if signature.len() != 64 {
        return Err(LifecycleError::InvalidResponse);
    }
    let header: JwtHeader =
        serde_json::from_slice(&header_bytes).map_err(|_| LifecycleError::InvalidResponse)?;
    require_canonical_json(&header_bytes, &header)?;
    validate_token_identifier(&header.kid, 1, MAX_KEY_ID_BYTES)
        .map_err(|()| LifecycleError::InvalidResponse)?;
    if header.alg != "EdDSA" || header.typ != expected_type {
        return Err(LifecycleError::InvalidResponse);
    }
    let key = policy
        .key(&header.kid)
        .ok_or(LifecycleError::SignatureRejected)?;
    let signing_input = format!("{header_segment}.{claims_segment}");
    UnparsedPublicKey::new(&ED25519, key.public_key)
        .verify(signing_input.as_bytes(), &signature)
        .map_err(|_| LifecycleError::SignatureRejected)?;
    Ok((header, claims_bytes))
}

fn decode_segment(segment: &str, maximum: usize) -> Result<Vec<u8>, LifecycleError> {
    if segment.is_empty()
        || segment.len() > maximum.saturating_mul(2)
        || !segment
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
    {
        return Err(LifecycleError::InvalidResponse);
    }
    let decoded = URL_SAFE_NO_PAD
        .decode(segment)
        .map_err(|_| LifecycleError::InvalidResponse)?;
    if decoded.is_empty() || decoded.len() > maximum || URL_SAFE_NO_PAD.encode(&decoded) != segment
    {
        return Err(LifecycleError::InvalidResponse);
    }
    Ok(decoded)
}

fn require_canonical_json<T: Serialize>(original: &[u8], value: &T) -> Result<(), LifecycleError> {
    let canonical = serde_json::to_vec(value).map_err(|_| LifecycleError::Serialization)?;
    if canonical != original {
        return Err(LifecycleError::InvalidResponse);
    }
    Ok(())
}

fn validate_state(policy: &LifecyclePolicy, state: &CredentialState) -> Result<(), LifecycleError> {
    match state {
        CredentialState::Absent => Ok(()),
        CredentialState::Active { credential } => validate_active(policy, credential),
        CredentialState::Revoked { credential } => validate_revoked(credential),
    }
}

fn validate_active(
    policy: &LifecyclePolicy,
    credential: &ActiveCredential,
) -> Result<(), LifecycleError> {
    let Some(lifetime) = credential.expires_at.checked_sub(credential.issued_at) else {
        return Err(LifecycleError::InvalidState);
    };
    let Some(expected_refresh_at) = credential
        .expires_at
        .checked_sub(policy.refresh_before_seconds)
    else {
        return Err(LifecycleError::InvalidState);
    };
    let Some(latest_not_before) = credential.issued_at.checked_add(policy.clock_skew_seconds)
    else {
        return Err(LifecycleError::InvalidState);
    };
    let known_issuer_key = policy
        .keys
        .iter()
        .any(|key| digest_bytes(key.key_id.as_bytes()) == credential.issuer_key_id_sha256);
    if credential.generation == 0
        || credential.key_generation == 0
        || credential.key_generation > credential.generation
        || !is_hex64(&credential.credential_sha256)
        || !is_hex64(&credential.credential_id_sha256)
        || !is_hex64(&credential.issuer_key_id_sha256)
        || !is_hex64(&credential.last_operation_id_sha256)
        || credential.issued_at == 0
        || credential.not_before < credential.issued_at
        || credential.not_before > latest_not_before
        || credential.refresh_at <= credential.not_before
        || credential.expires_at <= credential.refresh_at
        || credential.refresh_at != expected_refresh_at
        || lifetime < policy.minimum_lifetime_seconds
        || lifetime > policy.maximum_lifetime_seconds
        || !known_issuer_key
    {
        return Err(LifecycleError::InvalidState);
    }
    Ok(())
}

fn validate_revoked(credential: &RevokedCredential) -> Result<(), LifecycleError> {
    if credential.generation == 0
        || credential.key_generation == 0
        || credential.key_generation > credential.generation
        || credential.revoked_at == 0
        || !is_hex64(&credential.prior_credential_sha256)
        || !is_hex64(&credential.revocation_receipt_sha256)
        || !is_hex64(&credential.operation_id_sha256)
    {
        return Err(LifecycleError::InvalidState);
    }
    Ok(())
}

fn validate_issuer(value: &str) -> Result<(), LifecycleError> {
    if value.len() <= "https://".len()
        || value.len() > MAX_IDENTIFIER_BYTES
        || !value.starts_with("https://")
        || value.ends_with('/')
        || value.contains('?')
        || value.contains('#')
        || !value.is_ascii()
        || value
            .bytes()
            .any(|byte| byte.is_ascii_control() || byte.is_ascii_whitespace())
    {
        return Err(LifecycleError::InvalidPolicy);
    }
    Ok(())
}

fn validate_token_identifier(value: &str, minimum: usize, maximum: usize) -> Result<(), ()> {
    if value.len() < minimum
        || value.len() > maximum
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-' | b':'))
    {
        return Err(());
    }
    Ok(())
}

fn is_hex64(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
}

fn digest_bytes(value: &[u8]) -> String {
    hex::encode(Sha256::digest(value))
}

fn canonical_digest(value: &impl Serialize) -> Result<String, LifecycleError> {
    let encoded = serde_json::to_vec(value).map_err(|_| LifecycleError::Serialization)?;
    Ok(digest_bytes(&encoded))
}
