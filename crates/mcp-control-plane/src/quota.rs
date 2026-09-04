use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::sync::Mutex;

use artifact_service::{ContentDigest, SubjectDigest, TenantId};
use auth_middleware::AuthContext;
use serde::Deserialize;
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::catalog::ToolKind;
use crate::strict_json::parse_unique_value;

const POLICY_BYTES: &[u8] = include_bytes!("../../../protocol/mcp/p15-quota-policy-v1.json");
const POLICY_SCHEMA_VERSION: &str = "hwpx-agent.quota-policy/v1";
const MAX_WINDOW_SECONDS: u64 = 3_600;
const MAX_TOKENS: u64 = 1_000_000;
const MAX_REPLAY_TTL_SECONDS: u64 = 86_400;

pub const QUOTA_POLICY_SHA256: &str =
    "aec54a5fa7f25c91ffa86d1d3a677c41ee68b1d3c974d21c734bad59ac19fd95";
pub const MAX_QUOTA_BUCKET_ENTRIES: usize = 65_536;
pub const MAX_QUOTA_REPLAY_ENTRIES: usize = 65_536;

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
struct BucketSpec {
    capacity: u64,
    refill_tokens_per_window: u64,
}

impl BucketSpec {
    const fn valid(self) -> bool {
        self.capacity > 0
            && self.capacity <= MAX_TOKENS
            && self.refill_tokens_per_window > 0
            && self.refill_tokens_per_window <= MAX_TOKENS
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct RawBuckets {
    capability: BucketSpec,
    tenant: BucketSpec,
    user: BucketSpec,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct RawJobClass {
    capacity: u64,
    job_class: String,
    refill_tokens_per_window: u64,
    tools: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct RawStateLimits {
    bucket_entries: usize,
    replay_entries: usize,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct RawQuotaPolicy {
    buckets: RawBuckets,
    job_classes: Vec<RawJobClass>,
    replay_ttl_seconds: u64,
    schema_version: String,
    state_limits: RawStateLimits,
    window_seconds: u64,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum JobClass {
    Standard,
    Render,
}

impl JobClass {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Standard => "standard",
            Self::Render => "render",
        }
    }

    fn parse(value: &str) -> Option<Self> {
        match value {
            "standard" => Some(Self::Standard),
            "render" => Some(Self::Render),
            _ => None,
        }
    }
}

#[derive(Clone)]
struct QuotaPolicy {
    tenant: BucketSpec,
    user: BucketSpec,
    capability: BucketSpec,
    job_classes: BTreeMap<JobClass, BucketSpec>,
    tool_job_classes: BTreeMap<ToolKind, JobClass>,
    window_seconds: u64,
    replay_ttl_seconds: u64,
    state_limits: QuotaStateLimits,
}

impl QuotaPolicy {
    fn load() -> Result<Self, QuotaError> {
        if hex::encode(Sha256::digest(POLICY_BYTES)) != QUOTA_POLICY_SHA256 {
            return Err(QuotaError::InvalidConfiguration);
        }
        let value =
            parse_unique_value(POLICY_BYTES).map_err(|()| QuotaError::InvalidConfiguration)?;
        let raw: RawQuotaPolicy =
            serde_json::from_value(value).map_err(|_| QuotaError::InvalidConfiguration)?;
        if raw.schema_version != POLICY_SCHEMA_VERSION
            || !(1..=MAX_WINDOW_SECONDS).contains(&raw.window_seconds)
            || !(1..=MAX_REPLAY_TTL_SECONDS).contains(&raw.replay_ttl_seconds)
            || !raw.buckets.tenant.valid()
            || !raw.buckets.user.valid()
            || !raw.buckets.capability.valid()
        {
            return Err(QuotaError::InvalidConfiguration);
        }
        let state_limits = QuotaStateLimits::new(
            raw.state_limits.bucket_entries,
            raw.state_limits.replay_entries,
        )?;
        let mut job_classes = BTreeMap::new();
        let mut tool_job_classes = BTreeMap::new();
        let mut previous_class = None;
        for raw_class in raw.job_classes {
            let Some(job_class) = JobClass::parse(&raw_class.job_class) else {
                return Err(QuotaError::InvalidConfiguration);
            };
            let spec = BucketSpec {
                capacity: raw_class.capacity,
                refill_tokens_per_window: raw_class.refill_tokens_per_window,
            };
            if previous_class.is_some_and(|previous| previous >= job_class)
                || !spec.valid()
                || raw_class.tools.is_empty()
                || job_classes.insert(job_class, spec).is_some()
            {
                return Err(QuotaError::InvalidConfiguration);
            }
            let mut previous_tool = None;
            for tool_name in raw_class.tools {
                let Some(tool) = ToolKind::parse(&tool_name) else {
                    return Err(QuotaError::InvalidConfiguration);
                };
                if previous_tool.is_some_and(|previous: ToolKind| previous.name() >= tool.name())
                    || expected_job_class(tool) != Some(job_class)
                    || tool_job_classes.insert(tool, job_class).is_some()
                {
                    return Err(QuotaError::InvalidConfiguration);
                }
                previous_tool = Some(tool);
            }
            previous_class = Some(job_class);
        }
        if job_classes.keys().copied().collect::<Vec<_>>() != [JobClass::Standard, JobClass::Render]
            || ToolKind::ALL
                .into_iter()
                .any(|tool| tool_job_classes.get(&tool).copied() != expected_job_class(tool))
        {
            return Err(QuotaError::InvalidConfiguration);
        }
        Ok(Self {
            tenant: raw.buckets.tenant,
            user: raw.buckets.user,
            capability: raw.buckets.capability,
            job_classes,
            tool_job_classes,
            window_seconds: raw.window_seconds,
            replay_ttl_seconds: raw.replay_ttl_seconds,
            state_limits,
        })
    }
}

impl fmt::Debug for QuotaPolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("QuotaPolicy")
            .field("tenant", &self.tenant)
            .field("user", &self.user)
            .field("capability", &self.capability)
            .field("job_classes", &self.job_classes)
            .field("window_seconds", &self.window_seconds)
            .field("replay_ttl_seconds", &self.replay_ttl_seconds)
            .field("state_limits", &self.state_limits)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct QuotaStateLimits {
    bucket_entries: usize,
    replay_entries: usize,
}

impl QuotaStateLimits {
    /// Creates bounded in-memory quota state limits.
    ///
    /// # Errors
    ///
    /// Rejects zero or above-product-maximum capacities.
    pub fn new(bucket_entries: usize, replay_entries: usize) -> Result<Self, QuotaError> {
        if !(1..=MAX_QUOTA_BUCKET_ENTRIES).contains(&bucket_entries)
            || !(1..=MAX_QUOTA_REPLAY_ENTRIES).contains(&replay_entries)
        {
            return Err(QuotaError::InvalidConfiguration);
        }
        Ok(Self {
            bucket_entries,
            replay_entries,
        })
    }

    #[must_use]
    pub const fn product_maximums() -> Self {
        Self {
            bucket_entries: MAX_QUOTA_BUCKET_ENTRIES,
            replay_entries: MAX_QUOTA_REPLAY_ENTRIES,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct QuotaAdmission {
    replayed: bool,
}

impl QuotaAdmission {
    #[must_use]
    pub const fn replayed(self) -> bool {
        self.replayed
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum QuotaError {
    #[error("quota service configuration is invalid")]
    InvalidConfiguration,
    #[error("quota state is temporarily unavailable")]
    StateUnavailable,
    #[error("quota state capacity is exhausted")]
    StateCapacityExceeded,
    #[error("quota is temporarily exhausted")]
    Exhausted { retry_after_seconds: u64 },
    #[error("idempotency key conflicts with an earlier quota admission")]
    IdempotencyConflict,
}

impl QuotaError {
    #[must_use]
    pub const fn retry_after_seconds(self) -> Option<u64> {
        match self {
            Self::Exhausted {
                retry_after_seconds,
            } => Some(retry_after_seconds),
            Self::InvalidConfiguration
            | Self::StateUnavailable
            | Self::StateCapacityExceeded
            | Self::IdempotencyConflict => None,
        }
    }
}

pub trait QuotaService: fmt::Debug + Send + Sync {
    /// Atomically admits one authorized, schema-valid request across every applicable dimension.
    ///
    /// # Errors
    ///
    /// Fails closed on exhausted buckets, clock regression, state capacity, poisoned state or an
    /// idempotency-key payload conflict.
    fn admit(
        &self,
        context: &AuthContext,
        tool: ToolKind,
        arguments: &Value,
        now_unix_seconds: u64,
    ) -> Result<QuotaAdmission, QuotaError>;
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
enum BucketKey {
    Tenant(TenantId),
    User(TenantId, SubjectDigest),
    Capability(TenantId, ContentDigest),
    JobClass(TenantId, JobClass),
}

#[derive(Clone, Copy, Debug)]
struct Bucket {
    spec: BucketSpec,
    tokens: u64,
    refill_remainder: u64,
    last_refill_unix_seconds: u64,
}

impl Bucket {
    const fn full(spec: BucketSpec, now_unix_seconds: u64) -> Self {
        Self {
            spec,
            tokens: spec.capacity,
            refill_remainder: 0,
            last_refill_unix_seconds: now_unix_seconds,
        }
    }

    fn refilled(mut self, window_seconds: u64, now_unix_seconds: u64) -> Result<Self, QuotaError> {
        let elapsed = now_unix_seconds
            .checked_sub(self.last_refill_unix_seconds)
            .ok_or(QuotaError::StateUnavailable)?;
        if elapsed == 0 || self.tokens == self.spec.capacity {
            self.last_refill_unix_seconds = now_unix_seconds;
            if self.tokens == self.spec.capacity {
                self.refill_remainder = 0;
            }
            return Ok(self);
        }
        let numerator = u128::from(elapsed)
            .saturating_mul(u128::from(self.spec.refill_tokens_per_window))
            .saturating_add(u128::from(self.refill_remainder));
        let added = numerator / u128::from(window_seconds);
        let missing = u128::from(self.spec.capacity.saturating_sub(self.tokens));
        if added >= missing {
            self.tokens = self.spec.capacity;
            self.refill_remainder = 0;
        } else {
            let added = u64::try_from(added).map_err(|_| QuotaError::StateUnavailable)?;
            let remainder = u64::try_from(numerator % u128::from(window_seconds))
                .map_err(|_| QuotaError::StateUnavailable)?;
            self.tokens = self.tokens.saturating_add(added);
            self.refill_remainder = remainder;
        }
        self.last_refill_unix_seconds = now_unix_seconds;
        Ok(self)
    }

    fn retry_after_seconds(self, window_seconds: u64) -> u64 {
        let numerator_needed = window_seconds.saturating_sub(self.refill_remainder);
        numerator_needed
            .saturating_add(self.spec.refill_tokens_per_window.saturating_sub(1))
            .checked_div(self.spec.refill_tokens_per_window)
            .unwrap_or(1)
            .max(1)
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct ReplayKey {
    tenant_id: TenantId,
    subject: SubjectDigest,
    tool: ToolKind,
    idempotency_key: String,
}

#[derive(Clone, Copy, Debug)]
struct ReplayEntry {
    fingerprint: ContentDigest,
    admitted_at_unix_seconds: u64,
    expires_at_unix_seconds: u64,
}

#[derive(Default)]
struct QuotaState {
    buckets: BTreeMap<BucketKey, Bucket>,
    replays: BTreeMap<ReplayKey, ReplayEntry>,
}

pub struct InMemoryQuotaService {
    policy: QuotaPolicy,
    limits: QuotaStateLimits,
    state: Mutex<QuotaState>,
}

impl InMemoryQuotaService {
    /// Loads the digest-pinned product quota policy.
    ///
    /// # Errors
    ///
    /// Fails closed when the embedded policy or its state limits are invalid.
    pub fn new() -> Result<Self, QuotaError> {
        let policy = QuotaPolicy::load()?;
        let limits = policy.state_limits;
        Ok(Self {
            policy,
            limits,
            state: Mutex::new(QuotaState::default()),
        })
    }

    /// Loads the pinned policy with smaller bounded state limits for an isolated deployment.
    ///
    /// # Errors
    ///
    /// Rejects limits larger than the digest-pinned product policy.
    pub fn with_state_limits(limits: QuotaStateLimits) -> Result<Self, QuotaError> {
        let policy = QuotaPolicy::load()?;
        if limits.bucket_entries > policy.state_limits.bucket_entries
            || limits.replay_entries > policy.state_limits.replay_entries
        {
            return Err(QuotaError::InvalidConfiguration);
        }
        Ok(Self {
            policy,
            limits,
            state: Mutex::new(QuotaState::default()),
        })
    }

    fn bucket_requests(
        &self,
        tenant_id: TenantId,
        subject: SubjectDigest,
        tool: ToolKind,
        arguments: &Value,
    ) -> Result<Vec<(BucketKey, BucketSpec)>, QuotaError> {
        let capability = arguments
            .get("capability_id")
            .and_then(Value::as_str)
            .map_or_else(
                || ContentDigest::of(tool.name().as_bytes()),
                |value| ContentDigest::of(value.as_bytes()),
            );
        let mut requests = vec![
            (BucketKey::Tenant(tenant_id), self.policy.tenant),
            (BucketKey::User(tenant_id, subject), self.policy.user),
            (
                BucketKey::Capability(tenant_id, capability),
                self.policy.capability,
            ),
        ];
        if let Some(job_class) = self.policy.tool_job_classes.get(&tool).copied() {
            let spec = self
                .policy
                .job_classes
                .get(&job_class)
                .copied()
                .ok_or(QuotaError::InvalidConfiguration)?;
            requests.push((BucketKey::JobClass(tenant_id, job_class), spec));
        }
        Ok(requests)
    }
}

impl QuotaService for InMemoryQuotaService {
    fn admit(
        &self,
        context: &AuthContext,
        tool: ToolKind,
        arguments: &Value,
        now_unix_seconds: u64,
    ) -> Result<QuotaAdmission, QuotaError> {
        let replay = replay_material(
            context,
            tool,
            arguments,
            self.policy.replay_ttl_seconds,
            now_unix_seconds,
        )?;
        let mut state = self
            .state
            .lock()
            .map_err(|_| QuotaError::StateUnavailable)?;
        state
            .replays
            .retain(|_, entry| entry.expires_at_unix_seconds > now_unix_seconds);
        if let Some((key, candidate)) = &replay {
            if let Some(existing) = state.replays.get(key) {
                if now_unix_seconds < existing.admitted_at_unix_seconds {
                    return Err(QuotaError::StateUnavailable);
                }
                return if existing.fingerprint == candidate.fingerprint {
                    Ok(QuotaAdmission { replayed: true })
                } else {
                    Err(QuotaError::IdempotencyConflict)
                };
            }
            if state.replays.len() >= self.limits.replay_entries {
                return Err(QuotaError::StateCapacityExceeded);
            }
        }

        let requests =
            self.bucket_requests(context.tenant_id(), context.subject(), tool, arguments)?;
        let unique = requests.iter().map(|(key, _)| key).collect::<BTreeSet<_>>();
        if unique.len() != requests.len() {
            return Err(QuotaError::InvalidConfiguration);
        }
        let missing = requests
            .iter()
            .filter(|(key, _)| !state.buckets.contains_key(key))
            .count();
        if state.buckets.len().saturating_add(missing) > self.limits.bucket_entries {
            return Err(QuotaError::StateCapacityExceeded);
        }

        let mut candidates = Vec::with_capacity(requests.len());
        let mut retry_after_seconds = 0;
        for (key, spec) in requests {
            let existed = state.buckets.contains_key(&key);
            let bucket = state
                .buckets
                .get(&key)
                .copied()
                .unwrap_or_else(|| Bucket::full(spec, now_unix_seconds))
                .refilled(self.policy.window_seconds, now_unix_seconds)?;
            if bucket.spec != spec {
                return Err(QuotaError::StateUnavailable);
            }
            if bucket.tokens == 0 {
                retry_after_seconds =
                    retry_after_seconds.max(bucket.retry_after_seconds(self.policy.window_seconds));
            }
            candidates.push((key, bucket, existed));
        }
        if retry_after_seconds > 0 {
            for (key, bucket, existed) in candidates {
                if existed {
                    state.buckets.insert(key, bucket);
                }
            }
            return Err(QuotaError::Exhausted {
                retry_after_seconds,
            });
        }
        for (key, mut bucket, _) in candidates {
            bucket.tokens = bucket.tokens.saturating_sub(1);
            state.buckets.insert(key, bucket);
        }
        if let Some((key, entry)) = replay {
            state.replays.insert(key, entry);
        }
        Ok(QuotaAdmission { replayed: false })
    }
}

impl fmt::Debug for InMemoryQuotaService {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let (bucket_count, replay_count) = self
            .state
            .lock()
            .map_or((0, 0), |state| (state.buckets.len(), state.replays.len()));
        formatter
            .debug_struct("InMemoryQuotaService")
            .field("policy", &self.policy)
            .field("policy_sha256", &QUOTA_POLICY_SHA256)
            .field("limits", &self.limits)
            .field("bucket_count", &bucket_count)
            .field("replay_count", &replay_count)
            .finish()
    }
}

fn replay_material(
    context: &AuthContext,
    tool: ToolKind,
    arguments: &Value,
    replay_ttl_seconds: u64,
    now_unix_seconds: u64,
) -> Result<Option<(ReplayKey, ReplayEntry)>, QuotaError> {
    if expected_job_class(tool).is_none() {
        return Ok(None);
    }
    let Some(idempotency_key) = arguments.get("idempotency_key") else {
        return Ok(None);
    };
    let idempotency_key = idempotency_key
        .as_str()
        .ok_or(QuotaError::InvalidConfiguration)?;
    let mut normalized = arguments.clone();
    normalized
        .as_object_mut()
        .ok_or(QuotaError::InvalidConfiguration)?
        .remove("request_id");
    let encoded = serde_json::to_vec(&normalized).map_err(|_| QuotaError::StateUnavailable)?;
    let expires_at_unix_seconds = now_unix_seconds
        .checked_add(replay_ttl_seconds)
        .ok_or(QuotaError::StateUnavailable)?;
    Ok(Some((
        ReplayKey {
            tenant_id: context.tenant_id(),
            subject: context.subject(),
            tool,
            idempotency_key: idempotency_key.to_owned(),
        },
        ReplayEntry {
            fingerprint: ContentDigest::of(&encoded),
            admitted_at_unix_seconds: now_unix_seconds,
            expires_at_unix_seconds,
        },
    )))
}

const fn expected_job_class(tool: ToolKind) -> Option<JobClass> {
    match tool {
        ToolKind::DocumentCreate
        | ToolKind::DocumentEdit
        | ToolKind::DocumentTransform
        | ToolKind::DocumentValidate => Some(JobClass::Standard),
        ToolKind::DocumentRender | ToolKind::DocumentExport => Some(JobClass::Render),
        ToolKind::CapabilityCheck
        | ToolKind::DocumentPlan
        | ToolKind::DocumentInspect
        | ToolKind::TemplateAnalyze
        | ToolKind::ProjectCreate
        | ToolKind::ProjectOpen
        | ToolKind::ProjectHistory
        | ToolKind::ProjectCheckpoint
        | ToolKind::ProjectPublish
        | ToolKind::JobGet
        | ToolKind::JobCancel
        | ToolKind::ArtifactGet => None,
    }
}
