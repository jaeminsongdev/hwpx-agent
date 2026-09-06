#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zeroize::Zeroizing;

mod replay;

pub use replay::DurableReplayLedger;

type HmacSha256 = Hmac<Sha256>;

const TOKEN_PREFIX: &str = "confirm_v1";
const TOKEN_SCHEMA: &str = "hwpx-agent.confirmation/v1";
const RECEIPT_SCHEMA: &str = "hwpx-agent.approval-receipt/v1";
const MIN_KEY_BYTES: usize = 32;
const MAX_KEY_BYTES: usize = 128;
const MAX_TOKEN_BYTES: usize = 4_096;
const MAX_PAYLOAD_BYTES: usize = 2_048;
const MAX_TOKEN_TTL_SECONDS: u64 = 300;
const MAX_CONSUMED_TOKENS: usize = 4_096;

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EffectKind {
    GitCommit,
    AutomationExecute,
    ExternalInvoke,
    PrintExecute,
    SecurityModify,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ApprovalScope {
    WorkstationControl,
    AutomationUse,
    ExternalServiceUse,
    PrintExecute,
    SecurityModify,
}

impl EffectKind {
    #[must_use]
    pub const fn required_scope(self) -> ApprovalScope {
        match self {
            Self::GitCommit => ApprovalScope::WorkstationControl,
            Self::AutomationExecute => ApprovalScope::AutomationUse,
            Self::ExternalInvoke => ApprovalScope::ExternalServiceUse,
            Self::PrintExecute => ApprovalScope::PrintExecute,
            Self::SecurityModify => ApprovalScope::SecurityModify,
        }
    }
}

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum ApprovalError {
    #[error("approval configuration is invalid")]
    InvalidConfiguration,
    #[error("approval request is invalid")]
    InvalidRequest,
    #[error("effect is denied by policy")]
    DeniedByPolicy,
    #[error("required capability scope is absent")]
    MissingScope,
    #[error("fresh explicit confirmation is required")]
    ConfirmationRequired,
    #[error("confirmation token is malformed or has an invalid signature")]
    InvalidConfirmation,
    #[error("confirmation token does not match the exact request")]
    ConfirmationMismatch,
    #[error("confirmation token is outside its valid time window")]
    ConfirmationExpired,
    #[error("confirmation token was already consumed")]
    ConfirmationReplay,
    #[error("approval replay registry reached its bound")]
    CapacityExceeded,
    #[error("approval replay ledger is unavailable")]
    LedgerUnavailable,
    #[error("approval replay ledger is corrupt")]
    LedgerCorrupt,
    #[error("approval replay ledger changed concurrently")]
    LedgerConflict,
}

impl ApprovalError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidConfiguration => "APPROVAL_CONFIGURATION_INVALID",
            Self::InvalidRequest => "APPROVAL_REQUEST_INVALID",
            Self::DeniedByPolicy => "APPROVAL_DENIED_BY_POLICY",
            Self::MissingScope => "APPROVAL_SCOPE_MISSING",
            Self::ConfirmationRequired => "APPROVAL_CONFIRMATION_REQUIRED",
            Self::InvalidConfirmation => "APPROVAL_CONFIRMATION_INVALID",
            Self::ConfirmationMismatch => "APPROVAL_CONFIRMATION_MISMATCH",
            Self::ConfirmationExpired => "APPROVAL_CONFIRMATION_EXPIRED",
            Self::ConfirmationReplay => "APPROVAL_CONFIRMATION_REPLAY",
            Self::CapacityExceeded => "APPROVAL_CAPACITY_EXCEEDED",
            Self::LedgerUnavailable => "APPROVAL_LEDGER_UNAVAILABLE",
            Self::LedgerCorrupt => "APPROVAL_LEDGER_CORRUPT",
            Self::LedgerConflict => "APPROVAL_LEDGER_CONFLICT",
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct EffectRequest {
    operation_id: String,
    actor_sha256: String,
    tenant_sha256: String,
    effect: EffectKind,
    target_sha256: String,
    plan_sha256: String,
    requested_at_unix_seconds: u64,
}

impl fmt::Debug for EffectRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EffectRequest")
            .field("operation_id", &"<redacted>")
            .field("actor_sha256", &"<redacted>")
            .field("tenant_sha256", &"<redacted>")
            .field("effect", &self.effect)
            .field("target_sha256", &"<redacted>")
            .field("plan_sha256", &"<redacted>")
            .field("requested_at_unix_seconds", &self.requested_at_unix_seconds)
            .finish()
    }
}

impl EffectRequest {
    /// Creates one digest-bound request for a predefined side-effect class.
    ///
    /// # Errors
    ///
    /// Rejects malformed identifiers, digests and zero timestamps.
    pub fn new(
        operation_id: String,
        actor_sha256: String,
        tenant_sha256: String,
        effect: EffectKind,
        target_sha256: String,
        plan_sha256: String,
        requested_at_unix_seconds: u64,
    ) -> Result<Self, ApprovalError> {
        if !valid_identifier(&operation_id, "op_")
            || !valid_digest(&actor_sha256)
            || !valid_digest(&tenant_sha256)
            || !valid_digest(&target_sha256)
            || !valid_digest(&plan_sha256)
            || requested_at_unix_seconds == 0
        {
            return Err(ApprovalError::InvalidRequest);
        }
        Ok(Self {
            operation_id,
            actor_sha256,
            tenant_sha256,
            effect,
            target_sha256,
            plan_sha256,
            requested_at_unix_seconds,
        })
    }

    #[must_use]
    pub const fn effect(&self) -> EffectKind {
        self.effect
    }
}

#[derive(Clone)]
pub struct ApprovalPolicy {
    allowed_effects: BTreeSet<EffectKind>,
    max_confirmation_ttl_seconds: u64,
    max_consumed_tokens: usize,
}

impl fmt::Debug for ApprovalPolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ApprovalPolicy")
            .field("allowed_effect_count", &self.allowed_effects.len())
            .field(
                "max_confirmation_ttl_seconds",
                &self.max_confirmation_ttl_seconds,
            )
            .field("max_consumed_tokens", &self.max_consumed_tokens)
            .finish()
    }
}

impl ApprovalPolicy {
    /// Creates a bounded effect allowlist. An empty allowlist is the default-deny policy.
    ///
    /// # Errors
    ///
    /// Rejects zero or above-maximum confirmation/replay bounds.
    pub fn new(
        allowed_effects: impl IntoIterator<Item = EffectKind>,
        max_confirmation_ttl_seconds: u64,
        max_consumed_tokens: usize,
    ) -> Result<Self, ApprovalError> {
        if !(1..=MAX_TOKEN_TTL_SECONDS).contains(&max_confirmation_ttl_seconds)
            || !(1..=MAX_CONSUMED_TOKENS).contains(&max_consumed_tokens)
        {
            return Err(ApprovalError::InvalidConfiguration);
        }
        Ok(Self {
            allowed_effects: allowed_effects.into_iter().collect(),
            max_confirmation_ttl_seconds,
            max_consumed_tokens,
        })
    }

    /// Returns a policy that authorizes no side effects even when a token is presented.
    ///
    /// # Errors
    ///
    /// Returns only if the fixed product bounds become invalid.
    pub fn deny_all() -> Result<Self, ApprovalError> {
        Self::new([], MAX_TOKEN_TTL_SECONDS, MAX_CONSUMED_TOKENS)
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ConfirmationToken(Zeroizing<String>);

impl fmt::Debug for ConfirmationToken {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("<redacted-confirmation-token>")
    }
}

impl ConfirmationToken {
    /// Parses the bounded transport wrapper. Signature and request binding are checked only by an
    /// [`ApprovalEvaluator`].
    ///
    /// # Errors
    ///
    /// Rejects oversized or structurally malformed token strings.
    pub fn parse(encoded: String) -> Result<Self, ApprovalError> {
        if encoded.len() > MAX_TOKEN_BYTES
            || !encoded.is_ascii()
            || !encoded.starts_with("confirm_v1.")
            || encoded.split('.').count() != 3
        {
            return Err(ApprovalError::InvalidConfirmation);
        }
        Ok(Self(Zeroizing::new(encoded)))
    }

    #[must_use]
    pub fn encoded(&self) -> &str {
        &self.0
    }
}

pub struct ConfirmationAuthority {
    secret: Zeroizing<Vec<u8>>,
}

impl fmt::Debug for ConfirmationAuthority {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ConfirmationAuthority")
            .field("secret", &"<redacted>")
            .finish()
    }
}

impl ConfirmationAuthority {
    /// Creates the local reference confirmation signer.
    ///
    /// Production deployments must replace this HMAC boundary with the host confirmation service.
    ///
    /// # Errors
    ///
    /// Rejects keys outside the bounded 32..=128-byte range.
    pub fn new(secret: &[u8]) -> Result<Self, ApprovalError> {
        if !(MIN_KEY_BYTES..=MAX_KEY_BYTES).contains(&secret.len()) {
            return Err(ApprovalError::InvalidConfiguration);
        }
        Ok(Self {
            secret: Zeroizing::new(secret.to_vec()),
        })
    }

    /// Mints one exact-request, short-lived confirmation after a trusted UI reports explicit user
    /// confirmation. The caller supplies a unique bounded token ID.
    ///
    /// # Errors
    ///
    /// Rejects missing confirmation, invalid IDs, time windows and serialization/signing failures.
    pub fn mint(
        &self,
        token_id: String,
        request: &EffectRequest,
        user_confirmed: bool,
        issued_at_unix_seconds: u64,
        expires_at_unix_seconds: u64,
    ) -> Result<ConfirmationToken, ApprovalError> {
        if !user_confirmed
            || !valid_identifier(&token_id, "cnf_")
            || issued_at_unix_seconds < request.requested_at_unix_seconds
            || issued_at_unix_seconds - request.requested_at_unix_seconds > MAX_TOKEN_TTL_SECONDS
            || expires_at_unix_seconds <= issued_at_unix_seconds
            || expires_at_unix_seconds - issued_at_unix_seconds > MAX_TOKEN_TTL_SECONDS
        {
            return Err(ApprovalError::InvalidRequest);
        }
        let payload = ConfirmationPayload {
            schema_version: TOKEN_SCHEMA.to_owned(),
            token_id,
            operation_id: request.operation_id.clone(),
            actor_sha256: request.actor_sha256.clone(),
            tenant_sha256: request.tenant_sha256.clone(),
            effect: request.effect,
            target_sha256: request.target_sha256.clone(),
            plan_sha256: request.plan_sha256.clone(),
            issued_at_unix_seconds,
            expires_at_unix_seconds,
            user_confirmed: true,
        };
        let encoded = serde_json::to_vec(&payload).map_err(|_| ApprovalError::InvalidRequest)?;
        if encoded.len() > MAX_PAYLOAD_BYTES {
            return Err(ApprovalError::InvalidRequest);
        }
        let signature = sign(&self.secret, &encoded)?;
        Ok(ConfirmationToken(Zeroizing::new(format!(
            "{TOKEN_PREFIX}.{}.{}",
            URL_SAFE_NO_PAD.encode(encoded),
            URL_SAFE_NO_PAD.encode(signature)
        ))))
    }
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ConfirmationPayload {
    schema_version: String,
    token_id: String,
    operation_id: String,
    actor_sha256: String,
    tenant_sha256: String,
    effect: EffectKind,
    target_sha256: String,
    plan_sha256: String,
    issued_at_unix_seconds: u64,
    expires_at_unix_seconds: u64,
    user_confirmed: bool,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ApprovalReceipt {
    pub schema_version: &'static str,
    pub effect: EffectKind,
    pub required_scope: ApprovalScope,
    pub operation_sha256: String,
    pub actor_sha256: String,
    pub tenant_sha256: String,
    pub target_sha256: String,
    pub plan_sha256: String,
    pub confirmation_token_sha256: String,
    pub approved_at_unix_seconds: u64,
}

impl fmt::Debug for ApprovalReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ApprovalReceipt")
            .field("schema_version", &self.schema_version)
            .field("effect", &self.effect)
            .field("required_scope", &self.required_scope)
            .field("operation_sha256", &"<redacted>")
            .field("actor_sha256", &"<redacted>")
            .field("tenant_sha256", &"<redacted>")
            .field("target_sha256", &"<redacted>")
            .field("plan_sha256", &"<redacted>")
            .field("confirmation_token_sha256", &"<redacted>")
            .field("approved_at_unix_seconds", &self.approved_at_unix_seconds)
            .finish()
    }
}

#[derive(Eq, PartialEq)]
pub struct AuthorizedEffect {
    effect: EffectKind,
    receipt: ApprovalReceipt,
}

impl fmt::Debug for AuthorizedEffect {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AuthorizedEffect")
            .field("effect", &self.effect)
            .field(
                "approved_at_unix_seconds",
                &self.receipt.approved_at_unix_seconds,
            )
            .finish_non_exhaustive()
    }
}

impl AuthorizedEffect {
    #[must_use]
    pub const fn effect(&self) -> EffectKind {
        self.effect
    }

    #[must_use]
    pub const fn receipt(&self) -> &ApprovalReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn into_receipt(self) -> ApprovalReceipt {
        self.receipt
    }
}

pub trait ConfirmationReplayLedger: fmt::Debug + Send {
    /// Atomically consumes one hashed confirmation identity.
    ///
    /// # Errors
    ///
    /// Rejects replay, capacity, corruption, concurrent changes and storage failure.
    fn consume(
        &mut self,
        token_id_sha256: &str,
        expires_at_unix_seconds: u64,
        now_unix_seconds: u64,
        capacity: usize,
    ) -> Result<(), ApprovalError>;
}

#[derive(Default)]
struct ProcessLocalReplayLedger {
    consumed: BTreeMap<String, u64>,
}

impl fmt::Debug for ProcessLocalReplayLedger {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ProcessLocalReplayLedger")
            .field("consumed_count", &self.consumed.len())
            .finish()
    }
}

impl ConfirmationReplayLedger for ProcessLocalReplayLedger {
    fn consume(
        &mut self,
        token_id_sha256: &str,
        expires_at_unix_seconds: u64,
        now_unix_seconds: u64,
        capacity: usize,
    ) -> Result<(), ApprovalError> {
        self.consumed
            .retain(|_, expires_at| *expires_at > now_unix_seconds);
        if self.consumed.contains_key(token_id_sha256) {
            return Err(ApprovalError::ConfirmationReplay);
        }
        if self.consumed.len() >= capacity {
            return Err(ApprovalError::CapacityExceeded);
        }
        self.consumed
            .insert(token_id_sha256.to_owned(), expires_at_unix_seconds);
        Ok(())
    }
}

pub struct ApprovalEvaluator {
    policy: ApprovalPolicy,
    secret: Zeroizing<Vec<u8>>,
    replay_ledger: Box<dyn ConfirmationReplayLedger>,
}

impl fmt::Debug for ApprovalEvaluator {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ApprovalEvaluator")
            .field("policy", &self.policy)
            .field("secret", &"<redacted>")
            .field("replay_ledger", &self.replay_ledger)
            .finish()
    }
}

impl ApprovalEvaluator {
    /// Creates a local reference evaluator sharing the trusted confirmation key.
    ///
    /// # Errors
    ///
    /// Rejects keys outside the bounded 32..=128-byte range.
    pub fn new(policy: ApprovalPolicy, secret: &[u8]) -> Result<Self, ApprovalError> {
        Self::with_replay_ledger(policy, secret, Box::<ProcessLocalReplayLedger>::default())
    }

    /// Creates an evaluator with an injected replay ledger, including the durable implementation.
    ///
    /// # Errors
    ///
    /// Rejects keys outside the bounded 32..=128-byte range.
    pub fn with_replay_ledger(
        policy: ApprovalPolicy,
        secret: &[u8],
        replay_ledger: Box<dyn ConfirmationReplayLedger>,
    ) -> Result<Self, ApprovalError> {
        if !(MIN_KEY_BYTES..=MAX_KEY_BYTES).contains(&secret.len()) {
            return Err(ApprovalError::InvalidConfiguration);
        }
        Ok(Self {
            policy,
            secret: Zeroizing::new(secret.to_vec()),
            replay_ledger,
        })
    }

    /// Authorizes one predefined effect only after policy, scope, signature, exact binding, time
    /// and single-use checks all pass.
    ///
    /// # Errors
    ///
    /// Returns a stable denial class and consumes no token unless every check passes.
    pub fn authorize(
        &mut self,
        request: &EffectRequest,
        scopes: &BTreeSet<ApprovalScope>,
        confirmation: Option<&ConfirmationToken>,
        now_unix_seconds: u64,
    ) -> Result<AuthorizedEffect, ApprovalError> {
        if !self.policy.allowed_effects.contains(&request.effect) {
            return Err(ApprovalError::DeniedByPolicy);
        }
        let required_scope = request.effect.required_scope();
        if !scopes.contains(&required_scope) {
            return Err(ApprovalError::MissingScope);
        }
        let confirmation = confirmation.ok_or(ApprovalError::ConfirmationRequired)?;
        let payload = verify(&self.secret, confirmation)?;
        if payload.schema_version != TOKEN_SCHEMA || !payload.user_confirmed {
            return Err(ApprovalError::InvalidConfirmation);
        }
        if !valid_identifier(&payload.token_id, "cnf_")
            || payload.operation_id != request.operation_id
            || payload.actor_sha256 != request.actor_sha256
            || payload.tenant_sha256 != request.tenant_sha256
            || payload.effect != request.effect
            || payload.target_sha256 != request.target_sha256
            || payload.plan_sha256 != request.plan_sha256
        {
            return Err(ApprovalError::ConfirmationMismatch);
        }
        if payload.issued_at_unix_seconds < request.requested_at_unix_seconds
            || payload.issued_at_unix_seconds > now_unix_seconds
            || payload.expires_at_unix_seconds <= now_unix_seconds
            || payload.issued_at_unix_seconds - request.requested_at_unix_seconds
                > self.policy.max_confirmation_ttl_seconds
            || payload
                .expires_at_unix_seconds
                .checked_sub(payload.issued_at_unix_seconds)
                .is_none_or(|ttl| ttl > self.policy.max_confirmation_ttl_seconds)
        {
            return Err(ApprovalError::ConfirmationExpired);
        }
        let token_id_sha256 = digest(payload.token_id.as_bytes());
        self.replay_ledger.consume(
            &token_id_sha256,
            payload.expires_at_unix_seconds,
            now_unix_seconds,
            self.policy.max_consumed_tokens,
        )?;
        let receipt = ApprovalReceipt {
            schema_version: RECEIPT_SCHEMA,
            effect: request.effect,
            required_scope,
            operation_sha256: digest(request.operation_id.as_bytes()),
            actor_sha256: request.actor_sha256.clone(),
            tenant_sha256: request.tenant_sha256.clone(),
            target_sha256: request.target_sha256.clone(),
            plan_sha256: request.plan_sha256.clone(),
            confirmation_token_sha256: digest(confirmation.encoded().as_bytes()),
            approved_at_unix_seconds: now_unix_seconds,
        };
        Ok(AuthorizedEffect {
            effect: request.effect,
            receipt,
        })
    }
}

fn sign(secret: &[u8], payload: &[u8]) -> Result<Vec<u8>, ApprovalError> {
    let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(secret)
        .map_err(|_| ApprovalError::InvalidConfiguration)?;
    signer.update(payload);
    Ok(signer.finalize().into_bytes().to_vec())
}

fn verify(secret: &[u8], token: &ConfirmationToken) -> Result<ConfirmationPayload, ApprovalError> {
    if token.0.len() > MAX_TOKEN_BYTES {
        return Err(ApprovalError::InvalidConfirmation);
    }
    let mut parts = token.0.split('.');
    if parts.next() != Some(TOKEN_PREFIX) {
        return Err(ApprovalError::InvalidConfirmation);
    }
    let encoded_payload = parts.next().ok_or(ApprovalError::InvalidConfirmation)?;
    let encoded_signature = parts.next().ok_or(ApprovalError::InvalidConfirmation)?;
    if parts.next().is_some() {
        return Err(ApprovalError::InvalidConfirmation);
    }
    let payload = URL_SAFE_NO_PAD
        .decode(encoded_payload)
        .map_err(|_| ApprovalError::InvalidConfirmation)?;
    if payload.len() > MAX_PAYLOAD_BYTES {
        return Err(ApprovalError::InvalidConfirmation);
    }
    let signature = URL_SAFE_NO_PAD
        .decode(encoded_signature)
        .map_err(|_| ApprovalError::InvalidConfirmation)?;
    let mut verifier = <HmacSha256 as hmac::KeyInit>::new_from_slice(secret)
        .map_err(|_| ApprovalError::InvalidConfiguration)?;
    verifier.update(&payload);
    verifier
        .verify_slice(&signature)
        .map_err(|_| ApprovalError::InvalidConfirmation)?;
    serde_json::from_slice(&payload).map_err(|_| ApprovalError::InvalidConfirmation)
}

fn valid_identifier(value: &str, prefix: &str) -> bool {
    (prefix.len() + 8..=120).contains(&value.len())
        && value.starts_with(prefix)
        && value[prefix.len()..]
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}

fn valid_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
        && value != "0".repeat(64)
}

fn digest(value: &[u8]) -> String {
    hex::encode(Sha256::digest(value))
}
