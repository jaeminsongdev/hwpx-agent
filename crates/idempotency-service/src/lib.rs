#![forbid(unsafe_code)]

use std::collections::BTreeMap;
use std::collections::btree_map::Entry;
use std::fmt;
use std::sync::{Arc, Mutex};

use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
use job_service::{JobId, JobRequestContext, LeaseGrant, TerminalErrorCode};
use revision_service::{ProjectId, RevisionId};
use serde::de::Error as _;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use thiserror::Error;
use uuid::Uuid;

const MAX_ATTEMPTS: u16 = 10;
const MAX_RETRY_DELAY_SECONDS: u64 = 86_400;
const MAX_RECORD_TTL_SECONDS: u64 = 604_800;

#[derive(Clone, Debug, Error, Eq, PartialEq)]
pub enum IdempotencyError {
    #[error("idempotency identifier is invalid")]
    InvalidIdentifier,
    #[error("idempotency request is invalid")]
    InvalidRequest,
    #[error("idempotency record was not found")]
    NotFound,
    #[error("idempotency action is forbidden")]
    AccessDenied,
    #[error("idempotency key is already bound to a different request")]
    KeyReuseConflict,
    #[error("idempotency transition is invalid")]
    InvalidTransition,
    #[error("idempotency attempt lease is stale or mismatched")]
    StaleAttempt,
    #[error("idempotency attempt lease has expired")]
    LeaseExpired,
    #[error("idempotency retry budget is exhausted")]
    RetryExhausted,
    #[error("idempotency reconciliation observation does not match the request")]
    ReconciliationMismatch,
    #[error("idempotency repository failed")]
    RepositoryFailure,
}

impl IdempotencyError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidIdentifier => "IDEMPOTENCY_IDENTIFIER_INVALID",
            Self::InvalidRequest => "IDEMPOTENCY_REQUEST_INVALID",
            Self::NotFound => "IDEMPOTENCY_NOT_FOUND",
            Self::AccessDenied => "IDEMPOTENCY_ACCESS_DENIED",
            Self::KeyReuseConflict => "IDEMPOTENCY_KEY_REUSED",
            Self::InvalidTransition => "IDEMPOTENCY_TRANSITION_INVALID",
            Self::StaleAttempt => "IDEMPOTENCY_STALE_ATTEMPT",
            Self::LeaseExpired => "IDEMPOTENCY_LEASE_EXPIRED",
            Self::RetryExhausted => "IDEMPOTENCY_RETRY_EXHAUSTED",
            Self::ReconciliationMismatch => "IDEMPOTENCY_RECONCILIATION_MISMATCH",
            Self::RepositoryFailure => "IDEMPOTENCY_REPOSITORY_FAILED",
        }
    }
}

#[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct IdempotencyKey(Uuid);

impl IdempotencyKey {
    #[must_use]
    pub fn generate() -> Self {
        Self(Uuid::new_v4())
    }

    /// Parses one exact lowercase public identifier.
    ///
    /// # Errors
    ///
    /// Rejects malformed, noncanonical and nil UUIDs.
    pub fn parse(value: &str) -> Result<Self, IdempotencyError> {
        let encoded = value
            .strip_prefix("idem_")
            .ok_or(IdempotencyError::InvalidIdentifier)?;
        if encoded.len() != 32
            || !encoded
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err(IdempotencyError::InvalidIdentifier);
        }
        let uuid = Uuid::parse_str(encoded).map_err(|_| IdempotencyError::InvalidIdentifier)?;
        if uuid.is_nil() {
            return Err(IdempotencyError::InvalidIdentifier);
        }
        Ok(Self(uuid))
    }

    #[must_use]
    pub const fn as_uuid(self) -> Uuid {
        self.0
    }

    #[must_use]
    pub fn public_id(self) -> String {
        format!("idem_{}", self.0.simple())
    }
}

impl fmt::Debug for IdempotencyKey {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("<redacted-idempotency-key>")
    }
}

impl fmt::Display for IdempotencyKey {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.public_id())
    }
}

impl Serialize for IdempotencyKey {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.public_id())
    }
}

impl<'de> Deserialize<'de> for IdempotencyKey {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        Self::parse(&String::deserialize(deserializer)?).map_err(D::Error::custom)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum IdempotencyState {
    Claimed,
    InProgress,
    RetryPending,
    OutcomeUnknown,
    Succeeded,
    FailedTerminal,
}

impl IdempotencyState {
    #[must_use]
    pub const fn is_terminal(self) -> bool {
        matches!(self, Self::Succeeded | Self::FailedTerminal)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RetryClass {
    TransientStorage,
    TransientNetwork,
    AutomationNoEffect,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RetryPolicy {
    max_attempts: u16,
    base_delay_seconds: u64,
    max_delay_seconds: u64,
}

impl RetryPolicy {
    /// Creates one finite deterministic retry policy.
    ///
    /// # Errors
    ///
    /// Rejects zero or oversized attempt and delay bounds.
    pub fn new(
        max_attempts: u16,
        base_delay_seconds: u64,
        max_delay_seconds: u64,
    ) -> Result<Self, IdempotencyError> {
        if !(1..=MAX_ATTEMPTS).contains(&max_attempts)
            || base_delay_seconds == 0
            || base_delay_seconds > max_delay_seconds
            || max_delay_seconds > MAX_RETRY_DELAY_SECONDS
        {
            return Err(IdempotencyError::InvalidRequest);
        }
        Ok(Self {
            max_attempts,
            base_delay_seconds,
            max_delay_seconds,
        })
    }

    #[must_use]
    pub const fn max_attempts(self) -> u16 {
        self.max_attempts
    }

    fn retry_at(self, attempt_no: u16, now: u64) -> Result<u64, IdempotencyError> {
        if attempt_no == 0 || attempt_no >= self.max_attempts {
            return Err(IdempotencyError::RetryExhausted);
        }
        let shift = u32::from(attempt_no.saturating_sub(1)).min(63);
        let multiplier = 1_u64.checked_shl(shift).unwrap_or(u64::MAX);
        let delay = self
            .base_delay_seconds
            .saturating_mul(multiplier)
            .min(self.max_delay_seconds);
        now.checked_add(delay)
            .ok_or(IdempotencyError::InvalidRequest)
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RequestBinding {
    project_id: ProjectId,
    job_id: JobId,
    idempotency_key: IdempotencyKey,
    request_sha256: ContentDigest,
    execution_manifest_sha256: ContentDigest,
    source_artifact_sha256: ContentDigest,
    expected_effect_sha256: ContentDigest,
    expected_revision_id: Option<RevisionId>,
}

impl RequestBinding {
    #[must_use]
    #[allow(clippy::too_many_arguments)]
    pub const fn new(
        project_id: ProjectId,
        job_id: JobId,
        idempotency_key: IdempotencyKey,
        request_sha256: ContentDigest,
        execution_manifest_sha256: ContentDigest,
        source_artifact_sha256: ContentDigest,
        expected_effect_sha256: ContentDigest,
        expected_revision_id: Option<RevisionId>,
    ) -> Self {
        Self {
            project_id,
            job_id,
            idempotency_key,
            request_sha256,
            execution_manifest_sha256,
            source_artifact_sha256,
            expected_effect_sha256,
            expected_revision_id,
        }
    }

    #[must_use]
    pub const fn project_id(&self) -> ProjectId {
        self.project_id
    }

    #[must_use]
    pub const fn job_id(&self) -> JobId {
        self.job_id
    }

    #[must_use]
    pub const fn idempotency_key(&self) -> IdempotencyKey {
        self.idempotency_key
    }
}

impl fmt::Debug for RequestBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RequestBinding")
            .field("project_id", &"<redacted>")
            .field("job_id", &"<redacted>")
            .field("idempotency_key", &"<redacted>")
            .field("request_sha256", &"<redacted>")
            .field("execution_manifest_sha256", &"<redacted>")
            .field("source_artifact_sha256", &"<redacted>")
            .field("expected_effect_sha256", &"<redacted>")
            .field("expected_revision_id", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct IdempotencyRecord {
    tenant_id: TenantId,
    subject: SubjectDigest,
    binding: RequestBinding,
    retry_policy: RetryPolicy,
    state: IdempotencyState,
    attempt_count: u16,
    last_fencing_token: u64,
    active_lease: Option<LeaseGrant>,
    reconciliation_lease: Option<LeaseGrant>,
    retry_not_before_unix_seconds: Option<u64>,
    last_retry_class: Option<RetryClass>,
    result_revision_id: Option<RevisionId>,
    receipt_artifact_id: Option<ArtifactId>,
    terminal_error_code: Option<TerminalErrorCode>,
    created_at_unix_seconds: u64,
    updated_at_unix_seconds: u64,
    expires_at_unix_seconds: u64,
}

impl fmt::Debug for IdempotencyRecord {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IdempotencyRecord")
            .field("tenant_id", &"<redacted>")
            .field("subject", &"<redacted>")
            .field("binding", &self.binding)
            .field("retry_policy", &self.retry_policy)
            .field("state", &self.state)
            .field("attempt_count", &self.attempt_count)
            .field("last_fencing_token", &self.last_fencing_token)
            .field("active_lease", &self.active_lease)
            .field("reconciliation_lease", &self.reconciliation_lease)
            .field(
                "retry_not_before_unix_seconds",
                &self.retry_not_before_unix_seconds,
            )
            .field("last_retry_class", &self.last_retry_class)
            .field("result_revision_id", &self.result_revision_id)
            .field("receipt_artifact_id", &self.receipt_artifact_id)
            .field("terminal_error_code", &self.terminal_error_code)
            .field("created_at_unix_seconds", &self.created_at_unix_seconds)
            .field("updated_at_unix_seconds", &self.updated_at_unix_seconds)
            .field("expires_at_unix_seconds", &self.expires_at_unix_seconds)
            .finish()
    }
}

impl IdempotencyRecord {
    #[must_use]
    pub const fn binding(&self) -> &RequestBinding {
        &self.binding
    }

    #[must_use]
    pub const fn state(&self) -> IdempotencyState {
        self.state
    }

    #[must_use]
    pub const fn attempt_count(&self) -> u16 {
        self.attempt_count
    }

    #[must_use]
    pub const fn retry_not_before_unix_seconds(&self) -> Option<u64> {
        self.retry_not_before_unix_seconds
    }

    #[must_use]
    pub const fn last_retry_class(&self) -> Option<RetryClass> {
        self.last_retry_class
    }

    #[must_use]
    pub const fn result_revision_id(&self) -> Option<RevisionId> {
        self.result_revision_id
    }

    #[must_use]
    pub const fn receipt_artifact_id(&self) -> Option<ArtifactId> {
        self.receipt_artifact_id
    }

    #[must_use]
    pub const fn terminal_error_code(&self) -> Option<&TerminalErrorCode> {
        self.terminal_error_code.as_ref()
    }

    fn require_owner(&self, context: &JobRequestContext) -> Result<(), IdempotencyError> {
        if self.tenant_id != context.tenant_id() || self.subject != context.subject() {
            return Err(IdempotencyError::AccessDenied);
        }
        if context.now_unix_seconds() < self.updated_at_unix_seconds
            || context.now_unix_seconds() >= self.expires_at_unix_seconds
        {
            return Err(IdempotencyError::InvalidRequest);
        }
        Ok(())
    }

    fn require_attempt(
        &self,
        context: &JobRequestContext,
        lease: &LeaseGrant,
        allow_expired: bool,
    ) -> Result<(), IdempotencyError> {
        self.require_owner(context)?;
        if self.active_lease.as_ref() != Some(lease) {
            return Err(IdempotencyError::StaleAttempt);
        }
        if !allow_expired && context.now_unix_seconds() >= lease.expires_at_unix_seconds() {
            return Err(IdempotencyError::LeaseExpired);
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Eq, PartialEq)]
pub struct NoEffectProof {
    receipt_artifact_id: ArtifactId,
    source_artifact_sha256: ContentDigest,
    observed_head_revision_id: Option<RevisionId>,
}

impl fmt::Debug for NoEffectProof {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoEffectProof")
            .field("receipt_artifact_id", &"<redacted>")
            .field("source_artifact_sha256", &"<redacted>")
            .field("observed_head_revision_id", &"<redacted>")
            .finish()
    }
}

impl NoEffectProof {
    #[must_use]
    pub const fn new(
        receipt_artifact_id: ArtifactId,
        source_artifact_sha256: ContentDigest,
        observed_head_revision_id: Option<RevisionId>,
    ) -> Self {
        Self {
            receipt_artifact_id,
            source_artifact_sha256,
            observed_head_revision_id,
        }
    }

    fn validate(&self, binding: &RequestBinding) -> Result<(), IdempotencyError> {
        if self.source_artifact_sha256 != binding.source_artifact_sha256
            || self.observed_head_revision_id != binding.expected_revision_id
        {
            return Err(IdempotencyError::ReconciliationMismatch);
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ClaimOutcome {
    New(IdempotencyRecord),
    Replay(IdempotencyRecord),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReconciliationObservation {
    Committed {
        result_revision_id: RevisionId,
        receipt_artifact_id: ArtifactId,
        effect_sha256: ContentDigest,
        observed_parent_revision_id: Option<RevisionId>,
    },
    NoEffect(NoEffectProof),
    StillUnknown,
}

type RecordKey = (TenantId, ProjectId, IdempotencyKey);

#[derive(Default)]
struct State {
    records: BTreeMap<RecordKey, IdempotencyRecord>,
}

#[derive(Clone, Default)]
pub struct IdempotencyService {
    state: Arc<Mutex<State>>,
}

impl fmt::Debug for IdempotencyService {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("IdempotencyService")
            .finish_non_exhaustive()
    }
}

impl IdempotencyService {
    /// Atomically binds a key to one exact request and retry policy.
    ///
    /// # Errors
    ///
    /// Rejects request drift, cross-subject replay and invalid expiry.
    pub fn claim(
        &self,
        context: &JobRequestContext,
        binding: RequestBinding,
        retry_policy: RetryPolicy,
        expires_at_unix_seconds: u64,
    ) -> Result<ClaimOutcome, IdempotencyError> {
        let ttl = expires_at_unix_seconds
            .checked_sub(context.now_unix_seconds())
            .ok_or(IdempotencyError::InvalidRequest)?;
        if !(1..=MAX_RECORD_TTL_SECONDS).contains(&ttl) {
            return Err(IdempotencyError::InvalidRequest);
        }
        let key = (
            context.tenant_id(),
            binding.project_id,
            binding.idempotency_key,
        );
        let mut state = self.lock()?;
        match state.records.entry(key) {
            Entry::Vacant(entry) => {
                let record = IdempotencyRecord {
                    tenant_id: context.tenant_id(),
                    subject: context.subject(),
                    binding,
                    retry_policy,
                    state: IdempotencyState::Claimed,
                    attempt_count: 0,
                    last_fencing_token: 0,
                    active_lease: None,
                    reconciliation_lease: None,
                    retry_not_before_unix_seconds: None,
                    last_retry_class: None,
                    result_revision_id: None,
                    receipt_artifact_id: None,
                    terminal_error_code: None,
                    created_at_unix_seconds: context.now_unix_seconds(),
                    updated_at_unix_seconds: context.now_unix_seconds(),
                    expires_at_unix_seconds,
                };
                entry.insert(record.clone());
                Ok(ClaimOutcome::New(record))
            }
            Entry::Occupied(entry) => {
                let record = entry.get();
                record.require_owner(context)?;
                if record.binding != binding || record.retry_policy != retry_policy {
                    return Err(IdempotencyError::KeyReuseConflict);
                }
                Ok(ClaimOutcome::Replay(record.clone()))
            }
        }
    }

    /// Starts exactly the next scheduler-fenced attempt when its delay has elapsed.
    ///
    /// # Errors
    ///
    /// Rejects skipped attempts, stale fences, early retry and terminal records.
    pub fn begin_attempt(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        key: IdempotencyKey,
        job_id: JobId,
        lease: &LeaseGrant,
    ) -> Result<IdempotencyRecord, IdempotencyError> {
        let mut state = self.lock()?;
        let record = get_record_mut(&mut state, context, project_id, key)?;
        record.require_owner(context)?;
        if !matches!(
            record.state,
            IdempotencyState::Claimed | IdempotencyState::RetryPending
        ) || job_id != record.binding.job_id
            || lease.attempt_no() != record.attempt_count.saturating_add(1)
            || lease.fencing_token() <= record.last_fencing_token
            || lease.issued_at_unix_seconds() > context.now_unix_seconds()
            || context.now_unix_seconds() >= lease.expires_at_unix_seconds()
            || lease.expires_at_unix_seconds() > record.expires_at_unix_seconds
            || record
                .retry_not_before_unix_seconds
                .is_some_and(|retry_at| context.now_unix_seconds() < retry_at)
        {
            return Err(IdempotencyError::InvalidTransition);
        }
        record.state = IdempotencyState::InProgress;
        record.attempt_count = lease.attempt_no();
        record.last_fencing_token = lease.fencing_token();
        record.active_lease = Some(lease.clone());
        record.reconciliation_lease = None;
        record.retry_not_before_unix_seconds = None;
        record.receipt_artifact_id = None;
        record.terminal_error_code = None;
        record.updated_at_unix_seconds = context.now_unix_seconds();
        Ok(record.clone())
    }

    /// Commits one live attempt to immutable success.
    ///
    /// # Errors
    ///
    /// Rejects stale/expired attempts and effect-digest mismatch without mutation.
    #[allow(clippy::too_many_arguments)]
    pub fn succeed(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        key: IdempotencyKey,
        lease: &LeaseGrant,
        result_revision_id: RevisionId,
        receipt_artifact_id: ArtifactId,
        effect_sha256: ContentDigest,
        observed_parent_revision_id: Option<RevisionId>,
    ) -> Result<IdempotencyRecord, IdempotencyError> {
        let mut state = self.lock()?;
        let record = get_record_mut(&mut state, context, project_id, key)?;
        if record.state != IdempotencyState::InProgress {
            return Err(IdempotencyError::InvalidTransition);
        }
        record.require_attempt(context, lease, false)?;
        if effect_sha256 != record.binding.expected_effect_sha256
            || observed_parent_revision_id != record.binding.expected_revision_id
        {
            return Err(IdempotencyError::ReconciliationMismatch);
        }
        record.state = IdempotencyState::Succeeded;
        record.active_lease = None;
        record.result_revision_id = Some(result_revision_id);
        record.receipt_artifact_id = Some(receipt_artifact_id);
        record.updated_at_unix_seconds = context.now_unix_seconds();
        Ok(record.clone())
    }

    /// Schedules a bounded retry after a proven transient no-effect failure.
    ///
    /// # Errors
    ///
    /// Rejects stale attempts and exhausted retry budgets without mutation.
    #[allow(clippy::too_many_arguments)]
    pub fn retry_transient(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        key: IdempotencyKey,
        lease: &LeaseGrant,
        class: RetryClass,
        error_code: TerminalErrorCode,
        no_effect: NoEffectProof,
    ) -> Result<IdempotencyRecord, IdempotencyError> {
        let mut state = self.lock()?;
        let record = get_record_mut(&mut state, context, project_id, key)?;
        if record.state != IdempotencyState::InProgress {
            return Err(IdempotencyError::InvalidTransition);
        }
        if class == RetryClass::AutomationNoEffect {
            return Err(IdempotencyError::InvalidRequest);
        }
        record.require_attempt(context, lease, false)?;
        no_effect.validate(&record.binding)?;
        let retry_at = record
            .retry_policy
            .retry_at(record.attempt_count, context.now_unix_seconds())?;
        record.state = IdempotencyState::RetryPending;
        record.active_lease = None;
        record.retry_not_before_unix_seconds = Some(retry_at);
        record.last_retry_class = Some(class);
        record.receipt_artifact_id = Some(no_effect.receipt_artifact_id);
        record.terminal_error_code = Some(error_code);
        record.updated_at_unix_seconds = context.now_unix_seconds();
        Ok(record.clone())
    }

    /// Freezes an uncertain attempt until an exact reconciliation observation exists.
    ///
    /// # Errors
    ///
    /// Rejects stale attempt identity and time regression.
    pub fn mark_outcome_unknown(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        key: IdempotencyKey,
        lease: &LeaseGrant,
        receipt_artifact_id: ArtifactId,
        error_code: TerminalErrorCode,
    ) -> Result<IdempotencyRecord, IdempotencyError> {
        let mut state = self.lock()?;
        let record = get_record_mut(&mut state, context, project_id, key)?;
        if record.state != IdempotencyState::InProgress {
            return Err(IdempotencyError::InvalidTransition);
        }
        record.require_attempt(context, lease, true)?;
        record.state = IdempotencyState::OutcomeUnknown;
        record.active_lease = None;
        record.reconciliation_lease = Some(lease.clone());
        record.receipt_artifact_id = Some(receipt_artifact_id);
        record.terminal_error_code = Some(error_code);
        record.updated_at_unix_seconds = context.now_unix_seconds();
        Ok(record.clone())
    }

    /// Resolves an uncertain attempt without permitting a second effect first.
    ///
    /// # Errors
    ///
    /// Rejects mismatched observations, stale attempt identity and exhausted retry budgets.
    pub fn reconcile(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        key: IdempotencyKey,
        lease: &LeaseGrant,
        observation: ReconciliationObservation,
    ) -> Result<IdempotencyRecord, IdempotencyError> {
        let mut state = self.lock()?;
        let record = get_record_mut(&mut state, context, project_id, key)?;
        record.require_owner(context)?;
        if record.state != IdempotencyState::OutcomeUnknown
            || record.reconciliation_lease.as_ref() != Some(lease)
        {
            return Err(IdempotencyError::StaleAttempt);
        }
        match observation {
            ReconciliationObservation::Committed {
                result_revision_id,
                receipt_artifact_id,
                effect_sha256,
                observed_parent_revision_id,
            } => {
                if effect_sha256 != record.binding.expected_effect_sha256
                    || observed_parent_revision_id != record.binding.expected_revision_id
                {
                    return Err(IdempotencyError::ReconciliationMismatch);
                }
                record.state = IdempotencyState::Succeeded;
                record.reconciliation_lease = None;
                record.result_revision_id = Some(result_revision_id);
                record.receipt_artifact_id = Some(receipt_artifact_id);
                record.terminal_error_code = None;
            }
            ReconciliationObservation::NoEffect(no_effect) => {
                no_effect.validate(&record.binding)?;
                let retry_at = record
                    .retry_policy
                    .retry_at(record.attempt_count, context.now_unix_seconds())?;
                record.state = IdempotencyState::RetryPending;
                record.reconciliation_lease = None;
                record.retry_not_before_unix_seconds = Some(retry_at);
                record.last_retry_class = Some(RetryClass::AutomationNoEffect);
                record.receipt_artifact_id = Some(no_effect.receipt_artifact_id);
            }
            ReconciliationObservation::StillUnknown => return Ok(record.clone()),
        }
        record.updated_at_unix_seconds = context.now_unix_seconds();
        Ok(record.clone())
    }

    /// Commits one deterministic non-retryable failure.
    ///
    /// # Errors
    ///
    /// Rejects stale or expired attempts and terminal rewrites.
    pub fn fail_terminal(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        key: IdempotencyKey,
        lease: &LeaseGrant,
        error_code: TerminalErrorCode,
        receipt_artifact_id: ArtifactId,
    ) -> Result<IdempotencyRecord, IdempotencyError> {
        let mut state = self.lock()?;
        let record = get_record_mut(&mut state, context, project_id, key)?;
        if record.state != IdempotencyState::InProgress {
            return Err(IdempotencyError::InvalidTransition);
        }
        record.require_attempt(context, lease, false)?;
        record.state = IdempotencyState::FailedTerminal;
        record.active_lease = None;
        record.receipt_artifact_id = Some(receipt_artifact_id);
        record.terminal_error_code = Some(error_code);
        record.updated_at_unix_seconds = context.now_unix_seconds();
        Ok(record.clone())
    }

    /// Reads one exact subject-owned record.
    ///
    /// # Errors
    ///
    /// Masks cross-tenant records and rejects subject drift.
    pub fn get(
        &self,
        context: &JobRequestContext,
        project_id: ProjectId,
        key: IdempotencyKey,
    ) -> Result<IdempotencyRecord, IdempotencyError> {
        let state = self.lock()?;
        let record = state
            .records
            .get(&(context.tenant_id(), project_id, key))
            .ok_or(IdempotencyError::NotFound)?;
        record.require_owner(context)?;
        Ok(record.clone())
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, State>, IdempotencyError> {
        self.state
            .lock()
            .map_err(|_| IdempotencyError::RepositoryFailure)
    }
}

fn get_record_mut<'a>(
    state: &'a mut State,
    context: &JobRequestContext,
    project_id: ProjectId,
    key: IdempotencyKey,
) -> Result<&'a mut IdempotencyRecord, IdempotencyError> {
    state
        .records
        .get_mut(&(context.tenant_id(), project_id, key))
        .ok_or(IdempotencyError::NotFound)
}

#[cfg(test)]
mod tests {
    use std::fmt::Debug;
    use std::sync::{Arc, Barrier};
    use std::thread;

    use artifact_service::{ArtifactId, ContentDigest, SubjectDigest, TenantId};
    use job_service::{
        AgentInstanceId, ExecutionId, JobId, JobRequestContext, LeaseGrant, TerminalErrorCode,
    };
    use revision_service::{ProjectId, RevisionId};
    use uuid::Uuid;

    use super::{
        ClaimOutcome, IdempotencyError, IdempotencyKey, IdempotencyService, IdempotencyState,
        NoEffectProof, ReconciliationObservation, RequestBinding, RetryClass, RetryPolicy,
    };

    fn uuid(value: u128) -> Uuid {
        Uuid::from_u128(value)
    }

    fn id<T, E: Debug>(prefix: &str, value: u128, parse: impl FnOnce(&str) -> Result<T, E>) -> T {
        parse(&format!("{prefix}{}", uuid(value).simple()))
            .unwrap_or_else(|error| panic!("identifier: {error:?}"))
    }

    fn tenant(value: u128) -> TenantId {
        TenantId::new(uuid(value)).unwrap_or_else(|error| panic!("tenant: {error}"))
    }

    fn artifact(value: u128) -> ArtifactId {
        id("art_", value, ArtifactId::parse)
    }

    struct Fixture {
        service: IdempotencyService,
        tenant: TenantId,
        other_tenant: TenantId,
        owner: SubjectDigest,
        other: SubjectDigest,
        project: ProjectId,
        job: JobId,
        key: IdempotencyKey,
        binding: RequestBinding,
        policy: RetryPolicy,
    }

    impl Fixture {
        fn new() -> Self {
            let project = id("prj_", 3, ProjectId::parse);
            let job = id("job_", 4, JobId::parse);
            let key = id("idem_", 5, IdempotencyKey::parse);
            Self {
                service: IdempotencyService::default(),
                tenant: tenant(1),
                other_tenant: tenant(2),
                owner: SubjectDigest::from_authenticated_subject("idempotency-owner")
                    .unwrap_or_else(|error| panic!("owner: {error}")),
                other: SubjectDigest::from_authenticated_subject("idempotency-other")
                    .unwrap_or_else(|error| panic!("other: {error}")),
                project,
                job,
                key,
                binding: RequestBinding::new(
                    project,
                    job,
                    key,
                    ContentDigest::of(b"request"),
                    ContentDigest::of(b"manifest"),
                    ContentDigest::of(b"source"),
                    ContentDigest::of(b"effect"),
                    Some(id("rev_", 6, RevisionId::parse)),
                ),
                policy: RetryPolicy::new(3, 10, 30)
                    .unwrap_or_else(|error| panic!("policy: {error}")),
            }
        }

        fn context(&self, subject: SubjectDigest, now: u64) -> JobRequestContext {
            JobRequestContext::new(self.tenant, subject, now)
        }

        fn claim(&self) {
            let outcome = self
                .service
                .claim(
                    &self.context(self.owner, 100),
                    self.binding.clone(),
                    self.policy,
                    1_000,
                )
                .unwrap_or_else(|error| panic!("claim: {error}"));
            assert!(matches!(outcome, ClaimOutcome::New(_)));
        }

        fn lease(attempt: u16, fence: u64, now: u64, expires: u64) -> LeaseGrant {
            LeaseGrant::new(
                id("agt_", u128::from(attempt) + 20, AgentInstanceId::parse),
                id("exe_", u128::from(attempt) + 30, ExecutionId::parse),
                attempt,
                fence,
                now,
                expires,
            )
            .unwrap_or_else(|error| panic!("lease: {error}"))
        }
    }

    #[test]
    fn exact_duplicate_claim_replays_without_second_record() {
        let fixture = Fixture::new();
        fixture.claim();
        let replay = fixture
            .service
            .claim(
                &fixture.context(fixture.owner, 101),
                fixture.binding.clone(),
                fixture.policy,
                1_001,
            )
            .unwrap_or_else(|error| panic!("replay: {error}"));
        assert!(matches!(replay, ClaimOutcome::Replay(_)));
    }

    #[test]
    fn request_or_policy_drift_is_side_effect_free() {
        for policy_drift in [false, true] {
            let fixture = Fixture::new();
            fixture.claim();
            let binding = if policy_drift {
                fixture.binding.clone()
            } else {
                RequestBinding::new(
                    fixture.project,
                    fixture.job,
                    fixture.key,
                    ContentDigest::of(b"drifted-request"),
                    ContentDigest::of(b"manifest"),
                    ContentDigest::of(b"source"),
                    ContentDigest::of(b"effect"),
                    Some(id("rev_", 6, RevisionId::parse)),
                )
            };
            let policy = if policy_drift {
                RetryPolicy::new(2, 10, 30).unwrap_or_else(|error| panic!("policy: {error}"))
            } else {
                fixture.policy
            };
            assert_eq!(
                fixture
                    .service
                    .claim(&fixture.context(fixture.owner, 101), binding, policy, 1_001,),
                Err(IdempotencyError::KeyReuseConflict)
            );
            let unchanged = fixture
                .service
                .get(
                    &fixture.context(fixture.owner, 101),
                    fixture.project,
                    fixture.key,
                )
                .unwrap_or_else(|error| panic!("get: {error}"));
            assert_eq!(unchanged.state(), IdempotencyState::Claimed);
            assert_eq!(unchanged.attempt_count(), 0);
        }
    }

    #[test]
    fn concurrent_claim_has_one_new_owner_and_exact_replays() {
        let fixture = Fixture::new();
        let service = Arc::new(fixture.service.clone());
        let barrier = Arc::new(Barrier::new(16));
        let mut handles = Vec::new();
        for _ in 0..16 {
            let service = Arc::clone(&service);
            let barrier = Arc::clone(&barrier);
            let context = fixture.context(fixture.owner, 100);
            let binding = fixture.binding.clone();
            let policy = fixture.policy;
            handles.push(thread::spawn(move || {
                barrier.wait();
                service.claim(&context, binding, policy, 1_000)
            }));
        }
        let mut fresh = 0;
        let mut replay = 0;
        for handle in handles {
            match handle
                .join()
                .unwrap_or_else(|_| panic!("claim thread panicked"))
                .unwrap_or_else(|error| panic!("claim: {error}"))
            {
                ClaimOutcome::New(_) => fresh += 1,
                ClaimOutcome::Replay(_) => replay += 1,
            }
        }
        assert_eq!((fresh, replay), (1, 15));
    }

    #[test]
    fn one_live_attempt_commits_one_terminal_effect() {
        let fixture = Fixture::new();
        fixture.claim();
        let lease = Fixture::lease(1, 10, 101, 150);
        assert_eq!(
            fixture.service.begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                fixture.job,
                &Fixture::lease(1, 10, 102, 150),
            ),
            Err(IdempotencyError::InvalidTransition)
        );
        assert_eq!(
            fixture.service.begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                fixture.job,
                &Fixture::lease(1, 10, 101, 1_001),
            ),
            Err(IdempotencyError::InvalidTransition)
        );
        assert_eq!(
            fixture.service.begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                id("job_", 999, JobId::parse),
                &lease,
            ),
            Err(IdempotencyError::InvalidTransition)
        );
        fixture
            .service
            .begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                fixture.job,
                &lease,
            )
            .unwrap_or_else(|error| panic!("begin: {error}"));
        let revision = id("rev_", 40, RevisionId::parse);
        let receipt = artifact(41);
        assert_eq!(
            fixture.service.succeed(
                &fixture.context(fixture.owner, 109),
                fixture.project,
                fixture.key,
                &lease,
                revision,
                receipt,
                ContentDigest::of(b"effect"),
                Some(id("rev_", 999, RevisionId::parse)),
            ),
            Err(IdempotencyError::ReconciliationMismatch)
        );
        let succeeded = fixture
            .service
            .succeed(
                &fixture.context(fixture.owner, 110),
                fixture.project,
                fixture.key,
                &lease,
                revision,
                receipt,
                ContentDigest::of(b"effect"),
                Some(id("rev_", 6, RevisionId::parse)),
            )
            .unwrap_or_else(|error| panic!("success: {error}"));
        assert_eq!(succeeded.state(), IdempotencyState::Succeeded);
        assert_eq!(succeeded.result_revision_id(), Some(revision));
        assert_eq!(succeeded.receipt_artifact_id(), Some(receipt));
        assert_eq!(
            fixture.service.succeed(
                &fixture.context(fixture.owner, 111),
                fixture.project,
                fixture.key,
                &lease,
                revision,
                receipt,
                ContentDigest::of(b"effect"),
                Some(id("rev_", 6, RevisionId::parse)),
            ),
            Err(IdempotencyError::InvalidTransition)
        );
    }

    #[test]
    fn transient_retry_is_delayed_bounded_and_fenced() {
        let fixture = Fixture::new();
        fixture.claim();
        let first = Fixture::lease(1, 10, 101, 150);
        fixture
            .service
            .begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                fixture.job,
                &first,
            )
            .unwrap_or_else(|error| panic!("begin: {error}"));
        let expected_head = Some(id("rev_", 6, RevisionId::parse));
        assert_eq!(
            fixture.service.retry_transient(
                &fixture.context(fixture.owner, 109),
                fixture.project,
                fixture.key,
                &first,
                RetryClass::AutomationNoEffect,
                TerminalErrorCode::parse("AUTOMATION_TIMEOUT")
                    .unwrap_or_else(|error| panic!("code: {error}")),
                NoEffectProof::new(artifact(50), ContentDigest::of(b"source"), expected_head,),
            ),
            Err(IdempotencyError::InvalidRequest)
        );
        let mismatched_proof = NoEffectProof::new(
            artifact(50),
            ContentDigest::of(b"wrong-source"),
            expected_head,
        );
        assert_eq!(
            fixture.service.retry_transient(
                &fixture.context(fixture.owner, 109),
                fixture.project,
                fixture.key,
                &first,
                RetryClass::TransientNetwork,
                TerminalErrorCode::parse("NETWORK_TRANSIENT")
                    .unwrap_or_else(|error| panic!("code: {error}")),
                mismatched_proof,
            ),
            Err(IdempotencyError::ReconciliationMismatch)
        );
        let retry = fixture
            .service
            .retry_transient(
                &fixture.context(fixture.owner, 110),
                fixture.project,
                fixture.key,
                &first,
                RetryClass::TransientNetwork,
                TerminalErrorCode::parse("NETWORK_TRANSIENT")
                    .unwrap_or_else(|error| panic!("code: {error}")),
                NoEffectProof::new(artifact(50), ContentDigest::of(b"source"), expected_head),
            )
            .unwrap_or_else(|error| panic!("retry: {error}"));
        assert_eq!(retry.state(), IdempotencyState::RetryPending);
        assert_eq!(retry.retry_not_before_unix_seconds(), Some(120));
        assert_eq!(retry.last_retry_class(), Some(RetryClass::TransientNetwork));
        let second = Fixture::lease(2, 11, 120, 160);
        assert_eq!(
            fixture.service.begin_attempt(
                &fixture.context(fixture.owner, 119),
                fixture.project,
                fixture.key,
                fixture.job,
                &Fixture::lease(2, 11, 119, 160),
            ),
            Err(IdempotencyError::InvalidTransition)
        );
        let started = fixture
            .service
            .begin_attempt(
                &fixture.context(fixture.owner, 120),
                fixture.project,
                fixture.key,
                fixture.job,
                &second,
            )
            .unwrap_or_else(|error| panic!("retry begin: {error}"));
        assert_eq!(started.attempt_count(), 2);
        assert_eq!(started.state(), IdempotencyState::InProgress);
    }

    #[test]
    fn unknown_commit_requires_exact_effect_before_terminal_replay() {
        let fixture = Fixture::new();
        fixture.claim();
        let lease = Fixture::lease(1, 10, 101, 110);
        fixture
            .service
            .begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                fixture.job,
                &lease,
            )
            .unwrap_or_else(|error| panic!("begin: {error}"));
        fixture
            .service
            .mark_outcome_unknown(
                &fixture.context(fixture.owner, 110),
                fixture.project,
                fixture.key,
                &lease,
                artifact(60),
                TerminalErrorCode::parse("AUTOMATION_TIMEOUT")
                    .unwrap_or_else(|error| panic!("code: {error}")),
            )
            .unwrap_or_else(|error| panic!("unknown: {error}"));
        let revision = id("rev_", 61, RevisionId::parse);
        let mismatch = ReconciliationObservation::Committed {
            result_revision_id: revision,
            receipt_artifact_id: artifact(62),
            effect_sha256: ContentDigest::of(b"wrong-effect"),
            observed_parent_revision_id: Some(id("rev_", 6, RevisionId::parse)),
        };
        assert_eq!(
            fixture.service.reconcile(
                &fixture.context(fixture.owner, 111),
                fixture.project,
                fixture.key,
                &lease,
                mismatch,
            ),
            Err(IdempotencyError::ReconciliationMismatch)
        );
        assert_eq!(
            fixture.service.reconcile(
                &fixture.context(fixture.owner, 112),
                fixture.project,
                fixture.key,
                &lease,
                ReconciliationObservation::Committed {
                    result_revision_id: revision,
                    receipt_artifact_id: artifact(62),
                    effect_sha256: ContentDigest::of(b"effect"),
                    observed_parent_revision_id: Some(id("rev_", 999, RevisionId::parse)),
                },
            ),
            Err(IdempotencyError::ReconciliationMismatch)
        );
        let committed = fixture
            .service
            .reconcile(
                &fixture.context(fixture.owner, 113),
                fixture.project,
                fixture.key,
                &lease,
                ReconciliationObservation::Committed {
                    result_revision_id: revision,
                    receipt_artifact_id: artifact(62),
                    effect_sha256: ContentDigest::of(b"effect"),
                    observed_parent_revision_id: Some(id("rev_", 6, RevisionId::parse)),
                },
            )
            .unwrap_or_else(|error| panic!("reconcile: {error}"));
        assert_eq!(committed.state(), IdempotencyState::Succeeded);
        assert_eq!(committed.result_revision_id(), Some(revision));
    }

    #[test]
    fn exact_no_effect_reconciliation_is_the_only_unknown_retry_path() {
        let fixture = Fixture::new();
        fixture.claim();
        let lease = Fixture::lease(1, 10, 101, 110);
        fixture
            .service
            .begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                fixture.job,
                &lease,
            )
            .unwrap_or_else(|error| panic!("begin: {error}"));
        fixture
            .service
            .mark_outcome_unknown(
                &fixture.context(fixture.owner, 110),
                fixture.project,
                fixture.key,
                &lease,
                artifact(70),
                TerminalErrorCode::parse("AUTOMATION_TIMEOUT")
                    .unwrap_or_else(|error| panic!("code: {error}")),
            )
            .unwrap_or_else(|error| panic!("unknown: {error}"));
        let still_unknown = fixture
            .service
            .reconcile(
                &fixture.context(fixture.owner, 111),
                fixture.project,
                fixture.key,
                &lease,
                ReconciliationObservation::StillUnknown,
            )
            .unwrap_or_else(|error| panic!("still unknown: {error}"));
        assert_eq!(still_unknown.state(), IdempotencyState::OutcomeUnknown);
        assert_eq!(
            fixture.service.reconcile(
                &fixture.context(fixture.owner, 112),
                fixture.project,
                fixture.key,
                &lease,
                ReconciliationObservation::NoEffect(NoEffectProof::new(
                    artifact(71),
                    ContentDigest::of(b"wrong-source"),
                    Some(id("rev_", 6, RevisionId::parse)),
                )),
            ),
            Err(IdempotencyError::ReconciliationMismatch)
        );
        let retry = fixture
            .service
            .reconcile(
                &fixture.context(fixture.owner, 113),
                fixture.project,
                fixture.key,
                &lease,
                ReconciliationObservation::NoEffect(NoEffectProof::new(
                    artifact(71),
                    ContentDigest::of(b"source"),
                    Some(id("rev_", 6, RevisionId::parse)),
                )),
            )
            .unwrap_or_else(|error| panic!("no effect: {error}"));
        assert_eq!(retry.state(), IdempotencyState::RetryPending);
        assert_eq!(retry.retry_not_before_unix_seconds(), Some(123));
        assert_eq!(
            retry.last_retry_class(),
            Some(RetryClass::AutomationNoEffect)
        );
    }

    #[test]
    fn retry_budget_exhaustion_and_terminal_failure_are_fail_closed() {
        let fixture = Fixture::new();
        let policy = RetryPolicy::new(1, 10, 10).unwrap_or_else(|error| panic!("policy: {error}"));
        fixture
            .service
            .claim(
                &fixture.context(fixture.owner, 100),
                fixture.binding.clone(),
                policy,
                1_000,
            )
            .unwrap_or_else(|error| panic!("claim: {error}"));
        let lease = Fixture::lease(1, 10, 101, 150);
        fixture
            .service
            .begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                fixture.job,
                &lease,
            )
            .unwrap_or_else(|error| panic!("begin: {error}"));
        assert_eq!(
            fixture.service.retry_transient(
                &fixture.context(fixture.owner, 110),
                fixture.project,
                fixture.key,
                &lease,
                RetryClass::TransientStorage,
                TerminalErrorCode::parse("STORAGE_TRANSIENT")
                    .unwrap_or_else(|error| panic!("code: {error}")),
                NoEffectProof::new(
                    artifact(80),
                    ContentDigest::of(b"source"),
                    Some(id("rev_", 6, RevisionId::parse)),
                ),
            ),
            Err(IdempotencyError::RetryExhausted)
        );
        let failed = fixture
            .service
            .fail_terminal(
                &fixture.context(fixture.owner, 111),
                fixture.project,
                fixture.key,
                &lease,
                TerminalErrorCode::parse("SCHEMA_INVALID")
                    .unwrap_or_else(|error| panic!("code: {error}")),
                artifact(81),
            )
            .unwrap_or_else(|error| panic!("terminal: {error}"));
        assert_eq!(failed.state(), IdempotencyState::FailedTerminal);
        assert_eq!(
            failed.terminal_error_code().map(TerminalErrorCode::as_str),
            Some("SCHEMA_INVALID")
        );
    }

    #[test]
    fn cross_subject_tenant_stale_lease_and_expired_effect_are_rejected() {
        let fixture = Fixture::new();
        fixture.claim();
        assert_eq!(
            fixture.service.get(
                &fixture.context(fixture.other, 101),
                fixture.project,
                fixture.key,
            ),
            Err(IdempotencyError::AccessDenied)
        );
        let other_context = JobRequestContext::new(fixture.other_tenant, fixture.owner, 101);
        assert_eq!(
            fixture
                .service
                .get(&other_context, fixture.project, fixture.key),
            Err(IdempotencyError::NotFound)
        );
        let lease = Fixture::lease(1, 10, 101, 110);
        fixture
            .service
            .begin_attempt(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
                fixture.job,
                &lease,
            )
            .unwrap_or_else(|error| panic!("begin: {error}"));
        let stale = Fixture::lease(1, 11, 101, 110);
        assert_eq!(
            fixture.service.fail_terminal(
                &fixture.context(fixture.owner, 105),
                fixture.project,
                fixture.key,
                &stale,
                TerminalErrorCode::parse("SCHEMA_INVALID")
                    .unwrap_or_else(|error| panic!("code: {error}")),
                artifact(90),
            ),
            Err(IdempotencyError::StaleAttempt)
        );
        assert_eq!(
            fixture.service.succeed(
                &fixture.context(fixture.owner, 110),
                fixture.project,
                fixture.key,
                &lease,
                id("rev_", 91, RevisionId::parse),
                artifact(92),
                ContentDigest::of(b"effect"),
                Some(id("rev_", 6, RevisionId::parse)),
            ),
            Err(IdempotencyError::LeaseExpired)
        );
    }

    #[test]
    fn invalid_bounds_and_debug_output_do_not_leak_identity_or_digests() {
        assert_eq!(
            RetryPolicy::new(0, 1, 1),
            Err(IdempotencyError::InvalidRequest)
        );
        assert_eq!(
            RetryPolicy::new(2, 20, 10),
            Err(IdempotencyError::InvalidRequest)
        );
        let fixture = Fixture::new();
        fixture.claim();
        let record = fixture
            .service
            .get(
                &fixture.context(fixture.owner, 101),
                fixture.project,
                fixture.key,
            )
            .unwrap_or_else(|error| panic!("get: {error}"));
        let debug = format!("{record:?}");
        assert!(!debug.contains(&fixture.tenant.canonical()));
        assert!(!debug.contains(&fixture.project.public_id()));
        assert!(!debug.contains(&fixture.job.public_id()));
        assert!(!debug.contains(&fixture.key.public_id()));
        assert!(!debug.contains(&fixture.owner.hex()));
        assert!(!debug.contains(&ContentDigest::of(b"request").hex()));
        assert!(!debug.contains(&id("rev_", 6, RevisionId::parse).public_id()));
        let proof = NoEffectProof::new(
            artifact(99),
            ContentDigest::of(b"source"),
            Some(id("rev_", 6, RevisionId::parse)),
        );
        let proof_debug = format!("{proof:?}");
        assert!(!proof_debug.contains(&artifact(99).public_id()));
        assert!(!proof_debug.contains(&ContentDigest::of(b"source").hex()));
        assert!(!proof_debug.contains(&id("rev_", 6, RevisionId::parse).public_id()));
    }
}
