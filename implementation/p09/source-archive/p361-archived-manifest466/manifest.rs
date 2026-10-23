use std::collections::BTreeMap;
use std::fmt;

use domain_ir::{
    ArtifactId, CompiledOperationPlan, PlanId, RevisionId, RouteDecision, TargetProfileId,
    TransactionId,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const EXECUTION_MANIFEST_SCHEMA_VERSION: &str = "hwpx-agent.execution-manifest/v1";

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ExecutionManifest {
    schema_version: String,
    transaction_id: TransactionId,
    plan_id: PlanId,
    source_artifact_id: ArtifactId,
    base_revision: RevisionId,
    expected_source_sha256: [u8; 32],
    expected_source_size: u64,
    compiled_plan_sha256: [u8; 32],
    route_set_sha256: [u8; 32],
    route_count: usize,
    target_profile_id: TargetProfileId,
    registry_payload_sha256: [u8; 32],
    registry_sequence: u64,
}

impl ExecutionManifest {
    /// Binds one complete compiled plan to one exact set of route receipts and source artifact.
    ///
    /// # Errors
    ///
    /// Rejects empty/invalid source identity, missing/duplicate/mismatched routes, mixed target or
    /// registry snapshots and serialization failure.
    pub fn from_receipts(
        transaction_id: TransactionId,
        source_artifact_id: ArtifactId,
        expected_source_sha256: [u8; 32],
        expected_source_size: u64,
        plan: &CompiledOperationPlan,
        routes: &[RouteDecision],
    ) -> Result<Self, ExecutionManifestError> {
        if expected_source_sha256 == [0; 32] || expected_source_size == 0 {
            return Err(ExecutionManifestError::InvalidSourceIdentity);
        }
        if routes.len() != plan.operations().len() || routes.is_empty() {
            return Err(ExecutionManifestError::RouteSetMismatch);
        }
        let mut by_operation = BTreeMap::new();
        for route in routes {
            if by_operation
                .insert(route.operation_id().clone(), route)
                .is_some()
            {
                return Err(ExecutionManifestError::DuplicateRoute);
            }
        }

        let first = routes
            .first()
            .ok_or(ExecutionManifestError::RouteSetMismatch)?;
        let target_profile_id = first.target_profile_id().clone();
        let registry_payload_sha256 = first.registry_payload_sha256();
        let registry_sequence = first.registry_sequence();
        if registry_payload_sha256 == [0; 32] || registry_sequence == 0 {
            return Err(ExecutionManifestError::InvalidRegistryIdentity);
        }

        let mut ordered_route_hashes = Vec::with_capacity(routes.len());
        for operation in plan.operations() {
            let route = by_operation
                .get(operation.operation_id())
                .copied()
                .ok_or(ExecutionManifestError::RouteSetMismatch)?;
            if route.capability_id() != operation.capability_id()
                || route.target_profile_id() != &target_profile_id
                || route.registry_payload_sha256() != registry_payload_sha256
                || route.registry_sequence() != registry_sequence
            {
                return Err(ExecutionManifestError::RouteSetMismatch);
            }
            ordered_route_hashes.push(
                route
                    .canonical_sha256()
                    .map_err(|_| ExecutionManifestError::SerializationFailed)?,
            );
        }
        let route_set_sha256 = Sha256::digest(
            serde_json::to_vec(&ordered_route_hashes)
                .map_err(|_| ExecutionManifestError::SerializationFailed)?,
        )
        .into();
        let compiled_plan_sha256 = plan
            .canonical_sha256()
            .map_err(|_| ExecutionManifestError::SerializationFailed)?;
        Ok(Self {
            schema_version: EXECUTION_MANIFEST_SCHEMA_VERSION.to_owned(),
            transaction_id,
            plan_id: plan.plan_id().clone(),
            source_artifact_id,
            base_revision: plan.base_revision().clone(),
            expected_source_sha256,
            expected_source_size,
            compiled_plan_sha256,
            route_set_sha256,
            route_count: routes.len(),
            target_profile_id,
            registry_payload_sha256,
            registry_sequence,
        })
    }

    #[must_use]
    pub const fn transaction_id(&self) -> &TransactionId {
        &self.transaction_id
    }

    #[must_use]
    pub const fn source_artifact_id(&self) -> &ArtifactId {
        &self.source_artifact_id
    }

    #[must_use]
    pub const fn base_revision(&self) -> &RevisionId {
        &self.base_revision
    }

    #[must_use]
    pub const fn expected_source_sha256(&self) -> [u8; 32] {
        self.expected_source_sha256
    }

    #[must_use]
    pub const fn expected_source_size(&self) -> u64 {
        self.expected_source_size
    }

    #[must_use]
    pub const fn compiled_plan_sha256(&self) -> [u8; 32] {
        self.compiled_plan_sha256
    }

    #[must_use]
    pub const fn route_set_sha256(&self) -> [u8; 32] {
        self.route_set_sha256
    }

    #[must_use]
    pub const fn route_count(&self) -> usize {
        self.route_count
    }

    #[must_use]
    pub const fn target_profile_id(&self) -> &TargetProfileId { &self.target_profile_id }

    /// Emits deterministic compact manifest bytes.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization error.
    pub fn canonical_json(&self) -> Result<Vec<u8>, ExecutionManifestError> {
        serde_json::to_vec(self).map_err(|_| ExecutionManifestError::SerializationFailed)
    }

    /// Hashes the exact immutable execution manifest.
    ///
    /// # Errors
    ///
    /// Propagates a stable serialization error.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], ExecutionManifestError> {
        Ok(Sha256::digest(self.canonical_json()?).into())
    }
}

impl fmt::Debug for ExecutionManifest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ExecutionManifest")
            .field("route_count", &self.route_count)
            .field("expected_source_size", &self.expected_source_size)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum ExecutionManifestError {
    #[error("execution manifest source identity is invalid")]
    InvalidSourceIdentity,
    #[error("execution manifest registry identity is invalid")]
    InvalidRegistryIdentity,
    #[error("execution manifest route set does not match the compiled plan")]
    RouteSetMismatch,
    #[error("execution manifest contains a duplicate operation route")]
    DuplicateRoute,
    #[error("execution manifest serialization failed")]
    SerializationFailed,
}

impl ExecutionManifestError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidSourceIdentity => "execution_manifest_invalid_source_identity",
            Self::InvalidRegistryIdentity => "execution_manifest_invalid_registry_identity",
            Self::RouteSetMismatch => "execution_manifest_route_set_mismatch",
            Self::DuplicateRoute => "execution_manifest_duplicate_route",
            Self::SerializationFailed => "execution_manifest_serialization_failed",
        }
    }
}
