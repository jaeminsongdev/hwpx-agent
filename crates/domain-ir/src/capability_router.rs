use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{BackendId, CapabilityId, CompiledOperation, OperationId, TargetProfileId};

pub const CAPABILITY_ROUTE_DECISION_SCHEMA_VERSION: &str =
    "hwpx-agent.capability-route-decision/v1";

const HARD_MAX_BINDINGS: usize = 100_000;
const HARD_MAX_HEALTH_ENTRIES: usize = 100_000;
const HARD_MAX_BUILD_BYTES: usize = 512;
const HARD_MAX_HEALTH_TTL_MS: u64 = 31 * 24 * 60 * 60 * 1_000;

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Architecture {
    X86,
    X86_64,
    Arm64,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ExactTargetProfile {
    profile_id: TargetProfileId,
    build: String,
    architecture: Architecture,
}

impl ExactTargetProfile {
    /// Constructs an exact, bounded product target.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized or platform-sensitive build identifiers.
    pub fn new(
        profile_id: TargetProfileId,
        build: impl Into<String>,
        architecture: Architecture,
    ) -> Result<Self, CapabilityRouterError> {
        let build = build.into();
        if build.is_empty()
            || build.len() > HARD_MAX_BUILD_BYTES
            || !build.bytes().all(|byte| {
                byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b'_' | b'+')
            })
        {
            return Err(CapabilityRouterError::InvalidTargetProfile);
        }
        Ok(Self {
            profile_id,
            build,
            architecture,
        })
    }

    #[must_use]
    pub const fn profile_id(&self) -> &TargetProfileId {
        &self.profile_id
    }

    #[must_use]
    pub fn build(&self) -> &str {
        &self.build
    }

    #[must_use]
    pub const fn architecture(&self) -> Architecture {
        self.architecture
    }
}

impl fmt::Debug for ExactTargetProfile {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ExactTargetProfile(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BackendKind {
    DirectHwpx,
    Hybrid,
    DesktopAutomation,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SupportState {
    Verified,
    CandidateUnverified,
    Unavailable,
    Failed,
    RiskBlocked,
    NotRun,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PolicyScope {
    CurrentPcPersonalLocalDevelopment,
    Production,
    ExternalProvider,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RegistryTrustState {
    SignatureVerified,
    Unverified,
    Invalid,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PreservationRequirement {
    Normalized,
    Surgical,
    Exact,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PreservationImpact {
    Normalized,
    Surgical,
    Exact,
    OpaqueLoss,
}

impl PreservationImpact {
    const fn admits(self, requirement: PreservationRequirement) -> bool {
        let impact_rank = match self {
            Self::OpaqueLoss => 0,
            Self::Normalized => 1,
            Self::Surgical => 2,
            Self::Exact => 3,
        };
        let requirement_rank = match requirement {
            PreservationRequirement::Normalized => 1,
            PreservationRequirement::Surgical => 2,
            PreservationRequirement::Exact => 3,
        };
        impact_rank >= requirement_rank
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SignatureImpact {
    Preserved,
    Invalidated,
    Unknown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ProtectionState {
    Unprotected,
    Protected,
    Signed,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RouteRestriction {
    RequiresNetwork,
    RequiresExternalProvider,
    UnsafeAction,
    ConfirmationRequired,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BackendHealthState {
    Healthy,
    Degraded,
    Unhealthy,
    Unknown,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct BackendHealth {
    backend_id: BackendId,
    state: BackendHealthState,
    generation: u64,
    observed_at_unix_ms: u64,
    ttl_ms: u64,
}

impl BackendHealth {
    #[must_use]
    pub const fn new(
        backend_id: BackendId,
        state: BackendHealthState,
        generation: u64,
        observed_at_unix_ms: u64,
        ttl_ms: u64,
    ) -> Self {
        Self {
            backend_id,
            state,
            generation,
            observed_at_unix_ms,
            ttl_ms,
        }
    }

    #[must_use]
    pub const fn backend_id(&self) -> &BackendId {
        &self.backend_id
    }
}

impl fmt::Debug for BackendHealth {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BackendHealth")
            .field("state", &self.state)
            .field("generation", &self.generation)
            .field("observed_at_unix_ms", &self.observed_at_unix_ms)
            .field("ttl_ms", &self.ttl_ms)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RouteBinding {
    capability_id: CapabilityId,
    backend_id: BackendId,
    backend_kind: BackendKind,
    support: SupportState,
    target_profile: ExactTargetProfile,
    registry_payload_sha256: [u8; 32],
    registry_sequence: u64,
    priority: u16,
    cost: u32,
    preservation: PreservationImpact,
    signature_impact: SignatureImpact,
    allows_degraded_health: bool,
    restrictions: BTreeSet<RouteRestriction>,
}

impl RouteBinding {
    #[must_use]
    #[allow(clippy::too_many_arguments)]
    pub const fn new(
        capability_id: CapabilityId,
        backend_id: BackendId,
        backend_kind: BackendKind,
        support: SupportState,
        target_profile: ExactTargetProfile,
        registry_payload_sha256: [u8; 32],
        registry_sequence: u64,
        priority: u16,
        cost: u32,
        preservation: PreservationImpact,
        signature_impact: SignatureImpact,
    ) -> Self {
        Self {
            capability_id,
            backend_id,
            backend_kind,
            support,
            target_profile,
            registry_payload_sha256,
            registry_sequence,
            priority,
            cost,
            preservation,
            signature_impact,
            allows_degraded_health: false,
            restrictions: BTreeSet::new(),
        }
    }

    #[must_use]
    pub const fn with_degraded_health(mut self, allowed: bool) -> Self {
        self.allows_degraded_health = allowed;
        self
    }

    #[must_use]
    pub fn with_restriction(mut self, restriction: RouteRestriction) -> Self {
        let _ = self.restrictions.insert(restriction);
        self
    }
}

impl fmt::Debug for RouteBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RouteBinding")
            .field("backend_kind", &self.backend_kind)
            .field("support", &self.support)
            .field("priority", &self.priority)
            .field("cost", &self.cost)
            .field("preservation", &self.preservation)
            .finish_non_exhaustive()
    }
}

pub struct CapabilityRouteCatalog {
    bindings: Vec<RouteBinding>,
}

impl CapabilityRouteCatalog {
    /// Validates and freezes bounded capability support evidence.
    ///
    /// # Errors
    ///
    /// Rejects oversized catalogs, invalid registry evidence and duplicate exact bindings.
    pub fn from_bindings(bindings: Vec<RouteBinding>) -> Result<Self, CapabilityRouterError> {
        if bindings.len() > HARD_MAX_BINDINGS {
            return Err(CapabilityRouterError::LimitExceeded);
        }
        let mut seen = BTreeSet::new();
        for binding in &bindings {
            if binding.registry_payload_sha256 == [0; 32] || binding.registry_sequence == 0 {
                return Err(CapabilityRouterError::InvalidRegistryEvidence);
            }
            let key = (
                binding.capability_id.clone(),
                binding.backend_id.clone(),
                binding.target_profile.profile_id.clone(),
                binding.target_profile.build.clone(),
                binding.target_profile.architecture,
                binding.registry_payload_sha256,
                binding.registry_sequence,
            );
            if !seen.insert(key) {
                return Err(CapabilityRouterError::DuplicateBinding);
            }
        }
        Ok(Self { bindings })
    }
}

impl fmt::Debug for CapabilityRouteCatalog {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CapabilityRouteCatalog")
            .field("binding_count", &self.bindings.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RouteContext {
    target_profile: ExactTargetProfile,
    registry_payload_sha256: [u8; 32],
    registry_sequence: u64,
    registry_trust: RegistryTrustState,
    policy_scope: PolicyScope,
    preservation_requirement: PreservationRequirement,
    protection_state: ProtectionState,
    now_unix_ms: u64,
    health: BTreeMap<BackendId, BackendHealth>,
}

impl RouteContext {
    /// Builds an immutable routing snapshot from exact registry and backend evidence.
    ///
    /// # Errors
    ///
    /// Rejects missing registry identity or duplicate health observations.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        target_profile: ExactTargetProfile,
        registry_payload_sha256: [u8; 32],
        registry_sequence: u64,
        registry_trust: RegistryTrustState,
        policy_scope: PolicyScope,
        preservation_requirement: PreservationRequirement,
        protection_state: ProtectionState,
        now_unix_ms: u64,
        health: Vec<BackendHealth>,
    ) -> Result<Self, CapabilityRouterError> {
        if registry_payload_sha256 == [0; 32]
            || registry_sequence == 0
            || registry_trust != RegistryTrustState::SignatureVerified
        {
            return Err(CapabilityRouterError::InvalidRegistryEvidence);
        }
        if health.len() > HARD_MAX_HEALTH_ENTRIES {
            return Err(CapabilityRouterError::LimitExceeded);
        }
        let mut by_backend = BTreeMap::new();
        for observation in health {
            if by_backend
                .insert(observation.backend_id.clone(), observation)
                .is_some()
            {
                return Err(CapabilityRouterError::DuplicateHealthEvidence);
            }
        }
        Ok(Self {
            target_profile,
            registry_payload_sha256,
            registry_sequence,
            registry_trust,
            policy_scope,
            preservation_requirement,
            protection_state,
            now_unix_ms,
            health: by_backend,
        })
    }
}

impl fmt::Debug for RouteContext {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RouteContext")
            .field("policy_scope", &self.policy_scope)
            .field("preservation_requirement", &self.preservation_requirement)
            .field("protection_state", &self.protection_state)
            .field("health_count", &self.health.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CapabilityRouterLimits {
    pub max_bindings_considered: usize,
    pub max_health_entries: usize,
    pub max_health_ttl_ms: u64,
}

impl Default for CapabilityRouterLimits {
    fn default() -> Self {
        Self {
            max_bindings_considered: 10_000,
            max_health_entries: 10_000,
            max_health_ttl_ms: 24 * 60 * 60 * 1_000,
        }
    }
}

impl CapabilityRouterLimits {
    fn validate(self) -> Result<(), CapabilityRouterError> {
        if self.max_bindings_considered == 0
            || self.max_bindings_considered > HARD_MAX_BINDINGS
            || self.max_health_entries == 0
            || self.max_health_entries > HARD_MAX_HEALTH_ENTRIES
            || self.max_health_ttl_ms == 0
            || self.max_health_ttl_ms > HARD_MAX_HEALTH_TTL_MS
        {
            return Err(CapabilityRouterError::InvalidLimit);
        }
        Ok(())
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RouteDecision {
    schema_version: String,
    operation_id: OperationId,
    capability_id: CapabilityId,
    backend_id: BackendId,
    backend_kind: BackendKind,
    target_profile_id: TargetProfileId,
    registry_payload_sha256: [u8; 32],
    registry_sequence: u64,
    health_generation: u64,
    preservation: PreservationImpact,
    priority: u16,
    cost: u32,
}

impl RouteDecision {
    #[must_use]
    pub const fn backend_id(&self) -> &BackendId {
        &self.backend_id
    }

    #[must_use]
    pub const fn backend_kind(&self) -> BackendKind {
        self.backend_kind
    }

    #[must_use]
    pub const fn health_generation(&self) -> u64 {
        self.health_generation
    }

    /// Emits deterministic compact JSON for downstream transaction binding.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization failure.
    pub fn canonical_json(&self) -> Result<Vec<u8>, CapabilityRouterError> {
        serde_json::to_vec(self).map_err(|_| CapabilityRouterError::SerializationFailed)
    }

    /// Hashes the deterministic route receipt.
    ///
    /// # Errors
    ///
    /// Propagates a stable serialization failure.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], CapabilityRouterError> {
        Ok(Sha256::digest(self.canonical_json()?).into())
    }
}

impl fmt::Debug for RouteDecision {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RouteDecision")
            .field("backend_kind", &self.backend_kind)
            .field("health_generation", &self.health_generation)
            .field("preservation", &self.preservation)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum CapabilityRouterError {
    #[error("capability-router limit is invalid")]
    InvalidLimit,
    #[error("capability-router input exceeds its finite limit")]
    LimitExceeded,
    #[error("target profile is invalid")]
    InvalidTargetProfile,
    #[error("registry evidence is invalid")]
    InvalidRegistryEvidence,
    #[error("duplicate exact route binding")]
    DuplicateBinding,
    #[error("duplicate backend health evidence")]
    DuplicateHealthEvidence,
    #[error("compiled capability has no route binding")]
    CapabilityNotFound,
    #[error("exact target profile does not match route evidence")]
    TargetProfileMismatch,
    #[error("signed registry snapshot does not match route evidence")]
    RegistryMismatch,
    #[error("capability support is not verified")]
    SupportUnavailable,
    #[error("route policy denied all candidates")]
    PolicyDenied,
    #[error("route requires an explicit confirmation boundary")]
    ConfirmationRequired,
    #[error("route cannot satisfy preservation requirements")]
    PreservationDenied,
    #[error("backend health evidence is unavailable or stale")]
    HealthUnavailable,
    #[error("multiple equally ranked routes remain")]
    AmbiguousRoute,
    #[error("route receipt serialization failed")]
    SerializationFailed,
}

impl CapabilityRouterError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "capability_router_invalid_limit",
            Self::LimitExceeded => "capability_router_limit_exceeded",
            Self::InvalidTargetProfile => "capability_router_invalid_target_profile",
            Self::InvalidRegistryEvidence => "capability_router_invalid_registry_evidence",
            Self::DuplicateBinding => "capability_router_duplicate_binding",
            Self::DuplicateHealthEvidence => "capability_router_duplicate_health_evidence",
            Self::CapabilityNotFound => "capability_router_capability_not_found",
            Self::TargetProfileMismatch => "capability_router_target_profile_mismatch",
            Self::RegistryMismatch => "capability_router_registry_mismatch",
            Self::SupportUnavailable => "capability_router_support_unavailable",
            Self::PolicyDenied => "capability_router_policy_denied",
            Self::ConfirmationRequired => "capability_router_confirmation_required",
            Self::PreservationDenied => "capability_router_preservation_denied",
            Self::HealthUnavailable => "capability_router_health_unavailable",
            Self::AmbiguousRoute => "capability_router_ambiguous_route",
            Self::SerializationFailed => "capability_router_serialization_failed",
        }
    }
}

pub struct CapabilityRouter {
    limits: CapabilityRouterLimits,
}

impl CapabilityRouter {
    /// Constructs a pure router after validating all finite bounds.
    ///
    /// # Errors
    ///
    /// Rejects zero or excessive limits.
    pub fn new(limits: CapabilityRouterLimits) -> Result<Self, CapabilityRouterError> {
        limits.validate()?;
        Ok(Self { limits })
    }

    /// Selects one exact admissible backend or fails closed.
    ///
    /// # Errors
    ///
    /// Rejects mismatched support evidence, disabled policy, preservation loss, stale/unhealthy
    /// backends and equal top-ranked candidates. No failure path widens the candidate policy.
    pub fn route(
        &self,
        operation: &CompiledOperation,
        context: &RouteContext,
        catalog: &CapabilityRouteCatalog,
    ) -> Result<RouteDecision, CapabilityRouterError> {
        if catalog.bindings.len() > self.limits.max_bindings_considered
            || context.health.len() > self.limits.max_health_entries
        {
            return Err(CapabilityRouterError::LimitExceeded);
        }
        if context.policy_scope != PolicyScope::CurrentPcPersonalLocalDevelopment {
            return Err(CapabilityRouterError::PolicyDenied);
        }

        let mut candidates: Vec<_> = catalog
            .bindings
            .iter()
            .filter(|binding| &binding.capability_id == operation.capability_id())
            .collect();
        if candidates.is_empty() {
            return Err(CapabilityRouterError::CapabilityNotFound);
        }

        candidates.retain(|binding| binding.target_profile == context.target_profile);
        if candidates.is_empty() {
            return Err(CapabilityRouterError::TargetProfileMismatch);
        }

        candidates.retain(|binding| {
            binding.registry_payload_sha256 == context.registry_payload_sha256
                && binding.registry_sequence == context.registry_sequence
        });
        if candidates.is_empty() {
            return Err(CapabilityRouterError::RegistryMismatch);
        }

        candidates.retain(|binding| binding.support == SupportState::Verified);
        if candidates.is_empty() {
            return Err(CapabilityRouterError::SupportUnavailable);
        }

        if context.protection_state == ProtectionState::Protected {
            return Err(CapabilityRouterError::ConfirmationRequired);
        }
        let confirmation_only_exists = candidates.iter().any(|binding| {
            binding.restrictions.len() == 1
                && binding
                    .restrictions
                    .contains(&RouteRestriction::ConfirmationRequired)
        });
        candidates.retain(|binding| binding.restrictions.is_empty());
        if candidates.is_empty() {
            return Err(if confirmation_only_exists {
                CapabilityRouterError::ConfirmationRequired
            } else {
                CapabilityRouterError::PolicyDenied
            });
        }

        candidates.retain(|binding| {
            binding
                .preservation
                .admits(context.preservation_requirement)
                && (context.protection_state != ProtectionState::Signed
                    || binding.signature_impact == SignatureImpact::Preserved)
        });
        if candidates.is_empty() {
            return Err(CapabilityRouterError::PreservationDenied);
        }

        let mut healthy = self.healthy_candidates(candidates, context);
        if healthy.is_empty() {
            return Err(CapabilityRouterError::HealthUnavailable);
        }

        healthy.sort_by(|(left, _), (right, _)| {
            right
                .priority
                .cmp(&left.priority)
                .then_with(|| left.cost.cmp(&right.cost))
                .then_with(|| left.backend_id.cmp(&right.backend_id))
        });
        let (selected, observation) = healthy[0];
        if healthy.get(1).is_some_and(|(candidate, _)| {
            candidate.priority == selected.priority && candidate.cost == selected.cost
        }) {
            return Err(CapabilityRouterError::AmbiguousRoute);
        }

        Ok(RouteDecision {
            schema_version: CAPABILITY_ROUTE_DECISION_SCHEMA_VERSION.to_owned(),
            operation_id: operation.operation_id().clone(),
            capability_id: operation.capability_id().clone(),
            backend_id: selected.backend_id.clone(),
            backend_kind: selected.backend_kind,
            target_profile_id: context.target_profile.profile_id.clone(),
            registry_payload_sha256: context.registry_payload_sha256,
            registry_sequence: context.registry_sequence,
            health_generation: observation.generation,
            preservation: selected.preservation,
            priority: selected.priority,
            cost: selected.cost,
        })
    }

    fn healthy_candidates<'a>(
        &self,
        candidates: Vec<&'a RouteBinding>,
        context: &'a RouteContext,
    ) -> Vec<(&'a RouteBinding, &'a BackendHealth)> {
        candidates
            .into_iter()
            .filter_map(|binding| {
                let observation = context.health.get(&binding.backend_id)?;
                let expires_at = observation
                    .observed_at_unix_ms
                    .checked_add(observation.ttl_ms)?;
                let evidence_is_current = observation.generation > 0
                    && observation.ttl_ms > 0
                    && observation.ttl_ms <= self.limits.max_health_ttl_ms
                    && observation.observed_at_unix_ms <= context.now_unix_ms
                    && context.now_unix_ms <= expires_at;
                let state_is_admitted = match observation.state {
                    BackendHealthState::Healthy => true,
                    BackendHealthState::Degraded => binding.allows_degraded_health,
                    BackendHealthState::Unhealthy | BackendHealthState::Unknown => false,
                };
                (evidence_is_current && state_is_admitted).then_some((binding, observation))
            })
            .collect()
    }
}

impl fmt::Debug for CapabilityRouter {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CapabilityRouter")
            .field("limits", &self.limits)
            .finish()
    }
}
