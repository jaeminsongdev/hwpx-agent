//! Authenticated projection of one stored plan into the closed plan-review widget contract.
//!
//! Rendering is read-only. It succeeds only when typed route, dry-run, semantic-diff, signature and
//! execution-policy receipts all bind the exact authorized stored plan and each other. The result
//! is review data, not a document mutation permit and not proof of a registered MCP host.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::AuthMiddleware;
use domain_ir::{
    Architecture, BackendKind, CompiledOperationPlan, ExactTargetProfile, RouteDecision,
    SemanticDiffSummary, SemanticSummaryKind,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zeroize::Zeroizing;

use crate::policy::ProjectPolicy;
use crate::stored_plan::{LookupArguments, StoredPlan, parse_arguments};
use crate::{
    AuthorizedStoredPlan, LocalPostgresStoredPlanRegistry, PlanLookupRequest, PlanSourceRepository,
    StoredPlanError, StoredPlanRegistry,
};

pub const PLAN_REVIEW_SNAPSHOT_SCHEMA_VERSION: &str = "hwpx-agent.plan-review/v1";
const CURRENT_TARGET_PROFILE: &str = "hancom-hangul-2020-secondary";
const CURRENT_TARGET_BUILD: &str = "11.0.0.9136";
const ROUTE_SET_SCHEMA_VERSION: &str = "hwpx-agent.plan-review-route-set/v1";
const DRY_RUN_RECEIPT_SCHEMA_VERSION: &str = "hwpx-agent.plan-dry-run-receipt/v1";
const SIGNATURE_RECEIPT_SCHEMA_VERSION: &str = "hwpx-agent.plan-signature-receipt/v1";
const POLICY_RECEIPT_SCHEMA_VERSION: &str = "hwpx-agent.plan-review-policy-receipt/v1";
const MAX_PUBLIC_ROUTES: usize = 12;
const MAX_WARNINGS: usize = 8;
const PLAN_REVIEW_EVIDENCE_STORAGE_SCHEMA_VERSION: &str =
    "hwpx-agent.plan-review-evidence-storage/v1";

/// Store boundary used by the renderer. Implemented by both volatile and `PostgreSQL` registries.
pub trait PlanReviewPlanStore {
    /// Performs the store's complete authentication, authorization, owner, expiry and source check.
    ///
    /// # Errors
    /// Returns the store's stable closed error category.
    fn lookup_for_review<P: ProjectPolicy, R: PlanSourceRepository>(
        &mut self,
        auth: &mut AuthMiddleware,
        policy: &P,
        sources: &R,
        request: PlanLookupRequest,
    ) -> Result<AuthorizedStoredPlan, StoredPlanError>;
}

impl PlanReviewPlanStore for StoredPlanRegistry {
    fn lookup_for_review<P: ProjectPolicy, R: PlanSourceRepository>(
        &mut self,
        auth: &mut AuthMiddleware,
        policy: &P,
        sources: &R,
        request: PlanLookupRequest,
    ) -> Result<AuthorizedStoredPlan, StoredPlanError> {
        Self::lookup(self, auth, policy, sources, request)
    }
}

impl PlanReviewPlanStore for LocalPostgresStoredPlanRegistry {
    fn lookup_for_review<P: ProjectPolicy, R: PlanSourceRepository>(
        &mut self,
        auth: &mut AuthMiddleware,
        policy: &P,
        sources: &R,
        request: PlanLookupRequest,
    ) -> Result<AuthorizedStoredPlan, StoredPlanError> {
        Self::lookup(self, auth, policy, sources, request)
    }
}

/// Secret-bearing server request. Its arguments are the exact six-field widget input.
pub struct PlanReviewRenderRequest {
    authorization_header: Zeroizing<String>,
    arguments_json: Zeroizing<Vec<u8>>,
    now_unix_seconds: u64,
}

impl PlanReviewRenderRequest {
    /// `now_unix_seconds` must come from the server clock, never from public JSON.
    #[must_use]
    pub fn new(
        authorization_header: impl Into<String>,
        arguments_json: impl Into<Vec<u8>>,
        now_unix_seconds: u64,
    ) -> Self {
        Self {
            authorization_header: Zeroizing::new(authorization_header.into()),
            arguments_json: Zeroizing::new(arguments_json.into()),
            now_unix_seconds,
        }
    }
}

impl fmt::Debug for PlanReviewRenderRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanReviewRenderRequest")
            .field("arguments_bytes", &self.arguments_json.len())
            .field("now_unix_seconds", &self.now_unix_seconds)
            .finish_non_exhaustive()
    }
}

/// Exact authorized identity presented to an authoritative evidence repository.
pub struct PlanReviewEvidenceQuery<'a> {
    tenant: TenantId,
    subject: SubjectDigest,
    project_id: &'a str,
    plan: &'a CompiledOperationPlan,
    compiled_plan_sha256: [u8; 32],
}

impl PlanReviewEvidenceQuery<'_> {
    /// Creates the exact evidence-generation query for a freshly authorized stored plan.
    #[must_use]
    pub fn for_authorized(authorized: &AuthorizedStoredPlan) -> PlanReviewEvidenceQuery<'_> {
        let record = &authorized.record;
        PlanReviewEvidenceQuery {
            tenant: record.tenant,
            subject: record.owner,
            project_id: &record.project_id,
            plan: &record.plan,
            compiled_plan_sha256: record.sha256,
        }
    }

    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.tenant
    }
    #[must_use]
    pub const fn subject(&self) -> SubjectDigest {
        self.subject
    }
    #[must_use]
    pub fn project_id(&self) -> &str {
        self.project_id
    }
    #[must_use]
    pub const fn plan(&self) -> &CompiledOperationPlan {
        self.plan
    }
    #[must_use]
    pub const fn compiled_plan_sha256(&self) -> [u8; 32] {
        self.compiled_plan_sha256
    }
}

impl fmt::Debug for PlanReviewEvidenceQuery<'_> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("PlanReviewEvidenceQuery(<redacted>)")
    }
}

/// Server-side source of receipts. Implementations must load them from authoritative state.
pub trait PlanReviewEvidenceRepository: fmt::Debug + Send {
    /// Returns one complete immutable evidence set for the exact authorized query.
    ///
    /// # Errors
    /// Must collapse backend errors to stable renderer categories.
    fn load(
        &mut self,
        query: &PlanReviewEvidenceQuery<'_>,
    ) -> Result<PlanReviewEvidence, PlanReviewError>;
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PlanReviewRisk {
    Low,
    Medium,
    High,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EstimatedPageEffect {
    None,
    Local,
    DocumentWide,
    Unknown,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DryRunState {
    Verified,
    Partial,
    Failed,
    NotRun,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PlanReviewSignatureImpact {
    None,
    Invalidates,
    Unknown,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PlanReviewWarningSeverity {
    Notice,
    Warning,
    Blocking,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PlanReviewWarningKind {
    Validation,
    Preservation,
    Layout,
    Signature,
    Permission,
    Other,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PlanReviewWarning {
    code: String,
    severity: PlanReviewWarningSeverity,
    kind: PlanReviewWarningKind,
}

impl PlanReviewWarning {
    /// Creates a content-free warning classification.
    ///
    /// # Errors
    /// Rejects codes outside the widget's closed bounded grammar.
    pub fn new(
        code: impl Into<String>,
        severity: PlanReviewWarningSeverity,
        kind: PlanReviewWarningKind,
    ) -> Result<Self, PlanReviewError> {
        let code = code.into();
        if !warning_code(&code) {
            return Err(PlanReviewError::InvalidEvidence);
        }
        Ok(Self {
            code,
            severity,
            kind,
        })
    }

    #[must_use]
    pub fn code(&self) -> &str {
        &self.code
    }
    #[must_use]
    pub const fn severity(&self) -> PlanReviewWarningSeverity {
        self.severity
    }
}

impl fmt::Debug for PlanReviewWarning {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanReviewWarning")
            .field("severity", &self.severity)
            .field("kind", &self.kind)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PlanReviewSelectedBackend {
    DirectHwpx,
    #[serde(rename = "hancom_2020")]
    Hancom2020,
    Hybrid,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PlanReviewRoute {
    capability_id: String,
    selected_backend: PlanReviewSelectedBackend,
    support_level: &'static str,
    supported: bool,
}

impl fmt::Debug for PlanReviewRoute {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanReviewRoute")
            .field("selected_backend", &self.selected_backend)
            .finish_non_exhaustive()
    }
}

#[derive(Serialize)]
struct RouteSetDigest<'a> {
    schema_version: &'static str,
    compiled_plan_sha256: [u8; 32],
    exact_target_profile_sha256: [u8; 32],
    ordered_route_sha256: &'a [[u8; 32]],
}

/// Exact per-operation route receipts plus their bounded public capability projection.
#[derive(Clone, Eq, PartialEq)]
pub struct PlanReviewRouteSet {
    compiled_plan_sha256: [u8; 32],
    source_revision: String,
    source_graph_sha256: [u8; 32],
    route_set_sha256: [u8; 32],
    exact_target_profile_sha256: [u8; 32],
    decisions: Vec<RouteDecision>,
    public_routes: Vec<PlanReviewRoute>,
}

impl PlanReviewRouteSet {
    /// Validates a complete one-per-operation route set and builds its public projection.
    ///
    /// # Errors
    /// Rejects missing, duplicate, reordered, mixed-registry, mixed-backend or non-2020 receipts.
    pub fn from_decisions(
        plan: &CompiledOperationPlan,
        exact_target_profile: &ExactTargetProfile,
        decisions: Vec<RouteDecision>,
    ) -> Result<Self, PlanReviewError> {
        if decisions.is_empty() || decisions.len() != plan.operations().len() {
            return Err(PlanReviewError::InvalidEvidence);
        }
        if exact_target_profile.profile_id().as_str() != CURRENT_TARGET_PROFILE
            || exact_target_profile.build() != CURRENT_TARGET_BUILD
            || exact_target_profile.architecture() != Architecture::X86
        {
            return Err(PlanReviewError::InvalidEvidence);
        }
        let mut by_operation = BTreeMap::new();
        for decision in &decisions {
            if by_operation
                .insert(decision.operation_id().clone(), decision)
                .is_some()
            {
                return Err(PlanReviewError::InvalidEvidence);
            }
        }
        let first = decisions.first().ok_or(PlanReviewError::InvalidEvidence)?;
        if first.target_profile_id() != exact_target_profile.profile_id()
            || first.registry_payload_sha256() == [0; 32]
            || first.registry_sequence() == 0
        {
            return Err(PlanReviewError::InvalidEvidence);
        }
        let mut ordered_hashes = Vec::with_capacity(decisions.len());
        let mut public_by_capability = BTreeMap::<String, (&str, BackendKind)>::new();
        let mut public_routes = Vec::new();
        for (operation, supplied_decision) in plan.operations().iter().zip(&decisions) {
            if supplied_decision.operation_id() != operation.operation_id() {
                return Err(PlanReviewError::InvalidEvidence);
            }
            let decision = by_operation
                .get(operation.operation_id())
                .copied()
                .ok_or(PlanReviewError::InvalidEvidence)?;
            if decision.capability_id() != operation.capability_id()
                || decision.target_profile_id() != first.target_profile_id()
                || decision.registry_payload_sha256() != first.registry_payload_sha256()
                || decision.registry_sequence() != first.registry_sequence()
            {
                return Err(PlanReviewError::InvalidEvidence);
            }
            ordered_hashes.push(
                decision
                    .canonical_sha256()
                    .map_err(|_| PlanReviewError::InvalidEvidence)?,
            );
            let capability = decision.capability_id().as_str();
            match public_by_capability.get(capability) {
                Some((backend_id, backend_kind))
                    if *backend_id != decision.backend_id().as_str()
                        || *backend_kind != decision.backend_kind() =>
                {
                    return Err(PlanReviewError::InvalidEvidence);
                }
                Some(_) => {}
                None => {
                    public_by_capability.insert(
                        capability.to_owned(),
                        (decision.backend_id().as_str(), decision.backend_kind()),
                    );
                    public_routes.push(PlanReviewRoute {
                        capability_id: capability.to_owned(),
                        selected_backend: selected_backend(decision.backend_kind()),
                        support_level: "verified",
                        supported: true,
                    });
                }
            }
        }
        if public_routes.len() > MAX_PUBLIC_ROUTES {
            return Err(PlanReviewError::LimitExceeded);
        }
        let compiled_plan_sha256 = plan
            .canonical_sha256()
            .map_err(|_| PlanReviewError::InvalidEvidence)?;
        let exact_target_profile_sha256 = canonical_sha256(exact_target_profile)?;
        let route_set_sha256 = canonical_sha256(&RouteSetDigest {
            schema_version: ROUTE_SET_SCHEMA_VERSION,
            compiled_plan_sha256,
            exact_target_profile_sha256,
            ordered_route_sha256: &ordered_hashes,
        })?;
        Ok(Self {
            compiled_plan_sha256,
            source_revision: plan.base_revision().as_str().to_owned(),
            source_graph_sha256: plan.base_graph_sha256(),
            route_set_sha256,
            exact_target_profile_sha256,
            decisions,
            public_routes,
        })
    }

    #[must_use]
    pub const fn route_set_sha256(&self) -> [u8; 32] {
        self.route_set_sha256
    }
    #[must_use]
    pub fn decisions(&self) -> &[RouteDecision] {
        &self.decisions
    }
}

impl fmt::Debug for PlanReviewRouteSet {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanReviewRouteSet")
            .field("decision_count", &self.decisions.len())
            .field("public_route_count", &self.public_routes.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PlanDryRunReceipt {
    schema_version: &'static str,
    compiled_plan_sha256: [u8; 32],
    source_revision: String,
    source_graph_sha256: [u8; 32],
    result_graph_sha256: [u8; 32],
    route_set_sha256: [u8; 32],
    semantic_diff_sha256: [u8; 32],
    state: DryRunState,
    risk_level: PlanReviewRisk,
    estimated_page_effect: EstimatedPageEffect,
    warnings: Vec<PlanReviewWarning>,
}

impl PlanDryRunReceipt {
    /// Creates a typed dry-run receipt bound to one plan, route set and semantic diff.
    ///
    /// # Errors
    /// Rejects source/result mismatches, duplicate warnings and finite-limit violations.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        plan: &CompiledOperationPlan,
        routes: &PlanReviewRouteSet,
        summary: &SemanticDiffSummary,
        state: DryRunState,
        risk_level: PlanReviewRisk,
        estimated_page_effect: EstimatedPageEffect,
        warnings: Vec<PlanReviewWarning>,
    ) -> Result<Self, PlanReviewError> {
        validate_summary(plan, summary)?;
        validate_warnings(&warnings)?;
        let compiled_plan_sha256 = plan
            .canonical_sha256()
            .map_err(|_| PlanReviewError::InvalidEvidence)?;
        if routes.compiled_plan_sha256 != compiled_plan_sha256 {
            return Err(PlanReviewError::InvalidEvidence);
        }
        Ok(Self {
            schema_version: DRY_RUN_RECEIPT_SCHEMA_VERSION,
            compiled_plan_sha256,
            source_revision: plan.base_revision().as_str().to_owned(),
            source_graph_sha256: plan.base_graph_sha256(),
            result_graph_sha256: summary.after_graph_sha256(),
            route_set_sha256: routes.route_set_sha256,
            semantic_diff_sha256: summary.source_diff_sha256(),
            state,
            risk_level,
            estimated_page_effect,
            warnings,
        })
    }

    /// Hashes the complete immutable dry-run receipt.
    ///
    /// # Errors
    /// Returns a stable evidence error on serialization failure.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], PlanReviewError> {
        canonical_sha256(self)
    }
}

impl fmt::Debug for PlanDryRunReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanDryRunReceipt")
            .field("state", &self.state)
            .field("risk_level", &self.risk_level)
            .field("estimated_page_effect", &self.estimated_page_effect)
            .field("warning_count", &self.warnings.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PlanSignatureReceipt {
    schema_version: &'static str,
    compiled_plan_sha256: [u8; 32],
    source_revision: String,
    source_graph_sha256: [u8; 32],
    result_graph_sha256: [u8; 32],
    route_set_sha256: [u8; 32],
    impact: PlanReviewSignatureImpact,
}

impl PlanSignatureReceipt {
    /// Creates a document-signature impact receipt for the same candidate graph.
    ///
    /// # Errors
    /// Rejects plan, route or graph binding drift.
    pub fn new(
        plan: &CompiledOperationPlan,
        routes: &PlanReviewRouteSet,
        summary: &SemanticDiffSummary,
        impact: PlanReviewSignatureImpact,
    ) -> Result<Self, PlanReviewError> {
        validate_summary(plan, summary)?;
        let compiled_plan_sha256 = plan
            .canonical_sha256()
            .map_err(|_| PlanReviewError::InvalidEvidence)?;
        if routes.compiled_plan_sha256 != compiled_plan_sha256 {
            return Err(PlanReviewError::InvalidEvidence);
        }
        Ok(Self {
            schema_version: SIGNATURE_RECEIPT_SCHEMA_VERSION,
            compiled_plan_sha256,
            source_revision: plan.base_revision().as_str().to_owned(),
            source_graph_sha256: plan.base_graph_sha256(),
            result_graph_sha256: summary.after_graph_sha256(),
            route_set_sha256: routes.route_set_sha256,
            impact,
        })
    }

    /// Hashes the complete immutable signature receipt.
    ///
    /// # Errors
    /// Returns a stable evidence error on serialization failure.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], PlanReviewError> {
        canonical_sha256(self)
    }
}

impl fmt::Debug for PlanSignatureReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanSignatureReceipt")
            .field("impact", &self.impact)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PlanExecutionPolicyReceipt {
    schema_version: &'static str,
    tenant_id: TenantId,
    subject_sha256: [u8; 32],
    project_id: String,
    compiled_plan_sha256: [u8; 32],
    route_set_sha256: [u8; 32],
    dry_run_receipt_sha256: [u8; 32],
    signature_receipt_sha256: [u8; 32],
    allows_execution: bool,
}

impl PlanExecutionPolicyReceipt {
    /// Binds the final server policy decision to this caller and all review receipts.
    ///
    /// # Errors
    /// Returns a stable evidence error if either receipt cannot be hashed.
    pub fn new(
        query: &PlanReviewEvidenceQuery<'_>,
        routes: &PlanReviewRouteSet,
        dry_run: &PlanDryRunReceipt,
        signature: &PlanSignatureReceipt,
        allows_execution: bool,
    ) -> Result<Self, PlanReviewError> {
        Ok(Self {
            schema_version: POLICY_RECEIPT_SCHEMA_VERSION,
            tenant_id: query.tenant,
            subject_sha256: *query.subject.as_bytes(),
            project_id: query.project_id.to_owned(),
            compiled_plan_sha256: query.compiled_plan_sha256,
            route_set_sha256: routes.route_set_sha256,
            dry_run_receipt_sha256: dry_run.canonical_sha256()?,
            signature_receipt_sha256: signature.canonical_sha256()?,
            allows_execution,
        })
    }
}

impl fmt::Debug for PlanExecutionPolicyReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanExecutionPolicyReceipt")
            .field("allows_execution", &self.allows_execution)
            .finish_non_exhaustive()
    }
}

/// Complete authoritative receipt bundle returned by the evidence repository.
pub struct PlanReviewEvidence {
    route_set: PlanReviewRouteSet,
    diff: SemanticDiffSummary,
    dry_run: PlanDryRunReceipt,
    signature: PlanSignatureReceipt,
    policy: PlanExecutionPolicyReceipt,
}

impl PlanReviewEvidence {
    #[must_use]
    pub const fn new(
        route_set: PlanReviewRouteSet,
        diff: SemanticDiffSummary,
        dry_run: PlanDryRunReceipt,
        signature: PlanSignatureReceipt,
        policy: PlanExecutionPolicyReceipt,
    ) -> Self {
        Self {
            route_set,
            diff,
            dry_run,
            signature,
            policy,
        }
    }

    pub(crate) fn canonical_storage_json(
        &self,
        query: &PlanReviewEvidenceQuery<'_>,
    ) -> Result<Vec<u8>, PlanReviewError> {
        validate_evidence(query, self)?;
        let route_decisions = self
            .route_set
            .decisions
            .iter()
            .map(|decision| {
                let bytes = decision
                    .canonical_json()
                    .map_err(|_| PlanReviewError::InvalidEvidence)?;
                String::from_utf8(bytes).map_err(|_| PlanReviewError::InvalidEvidence)
            })
            .collect::<Result<Vec<_>, _>>()?;
        let categories = self
            .diff
            .categories()
            .iter()
            .map(|category| StoredDiffCategory {
                kind: category.kind(),
                count: category.count(),
            })
            .collect();
        let warnings = self
            .dry_run
            .warnings
            .iter()
            .map(|warning| StoredWarning {
                code: warning.code.clone(),
                severity: warning.severity,
                kind: warning.kind,
            })
            .collect();
        serde_json::to_vec(&StoredEvidenceEnvelope {
            schema_version: PLAN_REVIEW_EVIDENCE_STORAGE_SCHEMA_VERSION.to_owned(),
            route_decisions,
            diff: StoredDiffProjection {
                added: self.diff.added(),
                modified: self.diff.modified(),
                removed: self.diff.removed(),
                categories,
                source_diff_sha256: self.diff.source_diff_sha256(),
                before_graph_sha256: self.diff.before_graph_sha256(),
                after_graph_sha256: self.diff.after_graph_sha256(),
            },
            dry_run: StoredDryRunProjection {
                state: self.dry_run.state,
                risk_level: self.dry_run.risk_level,
                estimated_page_effect: self.dry_run.estimated_page_effect,
                warnings,
            },
            signature_impact: self.signature.impact,
            allows_execution: self.policy.allows_execution,
        })
        .map_err(|_| PlanReviewError::SerializationFailed)
    }

    pub(crate) fn from_canonical_storage_json(
        query: &PlanReviewEvidenceQuery<'_>,
        bytes: &[u8],
    ) -> Result<Self, PlanReviewError> {
        if bytes.is_empty() || bytes.len() > 1024 * 1024 {
            return Err(PlanReviewError::LimitExceeded);
        }
        let envelope: StoredEvidenceEnvelope =
            serde_json::from_slice(bytes).map_err(|_| PlanReviewError::InvalidEvidence)?;
        if envelope.schema_version != PLAN_REVIEW_EVIDENCE_STORAGE_SCHEMA_VERSION
            || serde_json::to_vec(&envelope)
                .map_err(|_| PlanReviewError::SerializationFailed)?
                .as_slice()
                != bytes
        {
            return Err(PlanReviewError::InvalidEvidence);
        }
        let decisions = envelope
            .route_decisions
            .iter()
            .map(|receipt| {
                RouteDecision::from_canonical_json(receipt.as_bytes())
                    .map_err(|_| PlanReviewError::InvalidEvidence)
            })
            .collect::<Result<Vec<_>, _>>()?;
        let target = ExactTargetProfile::new(
            domain_ir::TargetProfileId::parse(CURRENT_TARGET_PROFILE)
                .map_err(|_| PlanReviewError::InvalidEvidence)?,
            CURRENT_TARGET_BUILD,
            Architecture::X86,
        )
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
        let routes = PlanReviewRouteSet::from_decisions(query.plan, &target, decisions)?;
        let diff = SemanticDiffSummary::from_authenticated_projection(
            envelope.diff.added,
            envelope.diff.modified,
            envelope.diff.removed,
            envelope
                .diff
                .categories
                .into_iter()
                .map(|category| (category.kind, category.count))
                .collect(),
            envelope.diff.source_diff_sha256,
            envelope.diff.before_graph_sha256,
            envelope.diff.after_graph_sha256,
            domain_ir::SemanticSummaryLimits::default(),
        )
        .map_err(|_| PlanReviewError::InvalidEvidence)?;
        let warnings = envelope
            .dry_run
            .warnings
            .into_iter()
            .map(|warning| PlanReviewWarning::new(warning.code, warning.severity, warning.kind))
            .collect::<Result<Vec<_>, _>>()?;
        let dry_run = PlanDryRunReceipt::new(
            query.plan,
            &routes,
            &diff,
            envelope.dry_run.state,
            envelope.dry_run.risk_level,
            envelope.dry_run.estimated_page_effect,
            warnings,
        )?;
        let signature =
            PlanSignatureReceipt::new(query.plan, &routes, &diff, envelope.signature_impact)?;
        let policy = PlanExecutionPolicyReceipt::new(
            query,
            &routes,
            &dry_run,
            &signature,
            envelope.allows_execution,
        )?;
        let evidence = Self::new(routes, diff, dry_run, signature, policy);
        validate_evidence(query, &evidence)?;
        Ok(evidence)
    }

    pub(crate) const fn storage_binding(&self) -> PlanReviewEvidenceStorageBinding {
        PlanReviewEvidenceStorageBinding {
            route_set: self.route_set.route_set_sha256,
            semantic_diff: self.diff.source_diff_sha256(),
            result_graph: self.diff.after_graph_sha256(),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct PlanReviewEvidenceStorageBinding {
    pub(crate) route_set: [u8; 32],
    pub(crate) semantic_diff: [u8; 32],
    pub(crate) result_graph: [u8; 32],
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredEvidenceEnvelope {
    schema_version: String,
    route_decisions: Vec<String>,
    diff: StoredDiffProjection,
    dry_run: StoredDryRunProjection,
    signature_impact: PlanReviewSignatureImpact,
    allows_execution: bool,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredDiffProjection {
    added: u32,
    modified: u32,
    removed: u32,
    categories: Vec<StoredDiffCategory>,
    source_diff_sha256: [u8; 32],
    before_graph_sha256: [u8; 32],
    after_graph_sha256: [u8; 32],
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredDiffCategory {
    kind: SemanticSummaryKind,
    count: u32,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredDryRunProjection {
    state: DryRunState,
    risk_level: PlanReviewRisk,
    estimated_page_effect: EstimatedPageEffect,
    warnings: Vec<StoredWarning>,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct StoredWarning {
    code: String,
    severity: PlanReviewWarningSeverity,
    kind: PlanReviewWarningKind,
}

impl fmt::Debug for PlanReviewEvidence {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanReviewEvidence")
            .field("route_set", &self.route_set)
            .field("dry_run", &self.dry_run)
            .field("signature", &self.signature)
            .field("policy", &self.policy)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PlanReviewDiff {
    added: u32,
    modified: u32,
    removed: u32,
    categories: Vec<PlanReviewDiffCategory>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PlanReviewDiffCategory {
    kind: SemanticSummaryKind,
    count: u32,
}

/// Closed, content-free structured content consumed by the existing plan-review widget.
#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PlanReviewSnapshot {
    schema_version: &'static str,
    client_surface: String,
    locale: String,
    project_id: String,
    source_revision_id: String,
    plan_id: String,
    risk_level: PlanReviewRisk,
    estimated_page_effect: EstimatedPageEffect,
    route: Vec<PlanReviewRoute>,
    route_digest: String,
    diff: PlanReviewDiff,
    warnings: Vec<PlanReviewWarning>,
    signature_impact: PlanReviewSignatureImpact,
    dry_run_state: DryRunState,
    execution_allowed: bool,
}

impl PlanReviewSnapshot {
    /// Serializes the exact widget structured content.
    ///
    /// # Errors
    /// Returns a stable renderer error on serialization failure.
    pub fn structured_content(&self) -> Result<serde_json::Value, PlanReviewError> {
        serde_json::to_value(self).map_err(|_| PlanReviewError::SerializationFailed)
    }

    #[must_use]
    pub const fn execution_allowed(&self) -> bool {
        self.execution_allowed
    }
}

impl fmt::Debug for PlanReviewSnapshot {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanReviewSnapshot")
            .field("risk_level", &self.risk_level)
            .field("route_count", &self.route.len())
            .field("warning_count", &self.warnings.len())
            .field("dry_run_state", &self.dry_run_state)
            .field("execution_allowed", &self.execution_allowed)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum PlanReviewError {
    #[error("stored plan rejected the review request")]
    StoredPlan(#[source] StoredPlanError),
    #[error("plan review evidence is unavailable")]
    EvidenceUnavailable,
    #[error("plan review evidence is invalid")]
    InvalidEvidence,
    #[error("plan review evidence exceeds a finite limit")]
    LimitExceeded,
    #[error("plan review serialization failed")]
    SerializationFailed,
}

/// Stateless fail-closed binder for the authenticated plan-review endpoint.
#[derive(Clone, Copy, Debug, Default)]
pub struct PlanReviewRenderer;

impl PlanReviewRenderer {
    /// Loads the authorized stored plan before parsing again for presentation, then binds every
    /// authoritative receipt into one closed widget snapshot.
    ///
    /// # Errors
    /// Rejects authentication, input, source, receipt, limit and serialization failures.
    #[allow(clippy::too_many_arguments)]
    pub fn render<P, R, S, E>(
        &self,
        auth: &mut AuthMiddleware,
        policy: &P,
        sources: &R,
        plans: &mut S,
        evidence_repository: &mut E,
        request: PlanReviewRenderRequest,
    ) -> Result<PlanReviewSnapshot, PlanReviewError>
    where
        P: ProjectPolicy,
        R: PlanSourceRepository,
        S: PlanReviewPlanStore,
        E: PlanReviewEvidenceRepository,
    {
        let PlanReviewRenderRequest {
            authorization_header,
            arguments_json,
            now_unix_seconds,
        } = request;
        let authorized = plans
            .lookup_for_review(
                auth,
                policy,
                sources,
                PlanLookupRequest::new(
                    authorization_header.as_str(),
                    arguments_json.as_slice(),
                    now_unix_seconds,
                ),
            )
            .map_err(PlanReviewError::StoredPlan)?;
        drop(authorization_header);
        let arguments = parse_arguments(&arguments_json).map_err(PlanReviewError::StoredPlan)?;
        drop(arguments_json);
        Self::bind(arguments, &authorized, evidence_repository)
    }

    fn bind<E: PlanReviewEvidenceRepository>(
        arguments: LookupArguments,
        authorized: &AuthorizedStoredPlan,
        evidence_repository: &mut E,
    ) -> Result<PlanReviewSnapshot, PlanReviewError> {
        let record: &StoredPlan = &authorized.record;
        if record.project_id != arguments.project_id
            || record.plan.plan_id().as_str() != arguments.plan_id
            || record.plan.base_revision().as_str() != arguments.source_revision_id
            || record.sha256
                != record
                    .plan
                    .canonical_sha256()
                    .map_err(|_| PlanReviewError::InvalidEvidence)?
        {
            return Err(PlanReviewError::InvalidEvidence);
        }
        let query = PlanReviewEvidenceQuery {
            tenant: record.tenant,
            subject: record.owner,
            project_id: &record.project_id,
            plan: &record.plan,
            compiled_plan_sha256: record.sha256,
        };
        let evidence = evidence_repository.load(&query)?;
        validate_evidence(&query, &evidence)?;
        let execution_allowed = evidence.policy.allows_execution
            && evidence.dry_run.state == DryRunState::Verified
            && evidence.signature.impact == PlanReviewSignatureImpact::None
            && evidence
                .dry_run
                .warnings
                .iter()
                .all(|warning| warning.severity != PlanReviewWarningSeverity::Blocking);
        let categories = evidence
            .diff
            .categories()
            .iter()
            .map(|category| PlanReviewDiffCategory {
                kind: category.kind(),
                count: category.count(),
            })
            .collect();
        Ok(PlanReviewSnapshot {
            schema_version: PLAN_REVIEW_SNAPSHOT_SCHEMA_VERSION,
            client_surface: arguments.client_surface,
            locale: arguments.locale,
            project_id: arguments.project_id,
            source_revision_id: arguments.source_revision_id,
            plan_id: arguments.plan_id,
            risk_level: evidence.dry_run.risk_level,
            estimated_page_effect: evidence.dry_run.estimated_page_effect,
            route: evidence.route_set.public_routes,
            route_digest: hex::encode(evidence.route_set.route_set_sha256),
            diff: PlanReviewDiff {
                added: evidence.diff.added(),
                modified: evidence.diff.modified(),
                removed: evidence.diff.removed(),
                categories,
            },
            warnings: evidence.dry_run.warnings,
            signature_impact: evidence.signature.impact,
            dry_run_state: evidence.dry_run.state,
            execution_allowed,
        })
    }
}

fn validate_evidence(
    query: &PlanReviewEvidenceQuery<'_>,
    evidence: &PlanReviewEvidence,
) -> Result<(), PlanReviewError> {
    let route = &evidence.route_set;
    let dry = &evidence.dry_run;
    let signature = &evidence.signature;
    let policy = &evidence.policy;
    validate_summary(query.plan, &evidence.diff)?;
    validate_warnings(&dry.warnings)?;
    if route.compiled_plan_sha256 != query.compiled_plan_sha256
        || route.source_revision != query.plan.base_revision().as_str()
        || route.source_graph_sha256 != query.plan.base_graph_sha256()
        || route.exact_target_profile_sha256 == [0; 32]
        || route.decisions.len() != query.plan.operations().len()
        || dry.compiled_plan_sha256 != query.compiled_plan_sha256
        || dry.source_revision != route.source_revision
        || dry.source_graph_sha256 != route.source_graph_sha256
        || dry.result_graph_sha256 != evidence.diff.after_graph_sha256()
        || dry.route_set_sha256 != route.route_set_sha256
        || dry.semantic_diff_sha256 != evidence.diff.source_diff_sha256()
        || signature.compiled_plan_sha256 != query.compiled_plan_sha256
        || signature.source_revision != route.source_revision
        || signature.source_graph_sha256 != route.source_graph_sha256
        || signature.result_graph_sha256 != dry.result_graph_sha256
        || signature.route_set_sha256 != route.route_set_sha256
        || policy.tenant_id != query.tenant
        || policy.subject_sha256.as_slice() != query.subject.as_bytes()
        || policy.project_id != query.project_id
        || policy.compiled_plan_sha256 != query.compiled_plan_sha256
        || policy.route_set_sha256 != route.route_set_sha256
        || policy.dry_run_receipt_sha256 != dry.canonical_sha256()?
        || policy.signature_receipt_sha256 != signature.canonical_sha256()?
    {
        return Err(PlanReviewError::InvalidEvidence);
    }
    Ok(())
}

fn validate_summary(
    plan: &CompiledOperationPlan,
    summary: &SemanticDiffSummary,
) -> Result<(), PlanReviewError> {
    let total = u64::from(summary.added())
        .checked_add(u64::from(summary.modified()))
        .and_then(|value| value.checked_add(u64::from(summary.removed())))
        .ok_or(PlanReviewError::LimitExceeded)?;
    let categories = summary.categories();
    let category_total = categories.iter().try_fold(0_u64, |total, category| {
        total
            .checked_add(u64::from(category.count()))
            .ok_or(PlanReviewError::LimitExceeded)
    })?;
    if summary.before_graph_sha256() != plan.base_graph_sha256()
        || summary.source_diff_sha256() == [0; 32]
        || summary.after_graph_sha256() == [0; 32]
        || categories.len() > 8
        || total > 100_000
        || total != category_total
    {
        return Err(PlanReviewError::InvalidEvidence);
    }
    Ok(())
}

fn validate_warnings(warnings: &[PlanReviewWarning]) -> Result<(), PlanReviewError> {
    if warnings.len() > MAX_WARNINGS {
        return Err(PlanReviewError::LimitExceeded);
    }
    let mut codes = BTreeSet::new();
    if warnings
        .iter()
        .any(|warning| !warning_code(&warning.code) || !codes.insert(warning.code.as_str()))
    {
        return Err(PlanReviewError::InvalidEvidence);
    }
    Ok(())
}

fn warning_code(value: &str) -> bool {
    (3..=96).contains(&value.len())
        && value.as_bytes()[0].is_ascii_uppercase()
        && value
            .bytes()
            .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_')
}

const fn selected_backend(kind: BackendKind) -> PlanReviewSelectedBackend {
    match kind {
        BackendKind::DirectHwpx => PlanReviewSelectedBackend::DirectHwpx,
        BackendKind::Hybrid => PlanReviewSelectedBackend::Hybrid,
        BackendKind::DesktopAutomation => PlanReviewSelectedBackend::Hancom2020,
    }
}

fn canonical_sha256(value: &impl Serialize) -> Result<[u8; 32], PlanReviewError> {
    let bytes = serde_json::to_vec(value).map_err(|_| PlanReviewError::SerializationFailed)?;
    Ok(Sha256::digest(bytes).into())
}
