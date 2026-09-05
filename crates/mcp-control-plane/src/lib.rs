//! Fail-closed MCP handler boundary for the P15 public tool surface.
//!
//! Transport and backend implementations are deliberately outside this crate. Every call follows
//! the same boundary: authenticate, validate input, authorize the tenant/project, dispatch once,
//! validate output, and return a bounded MCP result.

mod artifact_delivery;
mod async_jobs;
mod catalog;
mod error_catalog;
mod handler;
mod plan_review;
mod policy;
mod postgres_plan_source;
mod postgres_stored_plan;
mod quota;
mod stored_plan;
mod strict_json;
mod telemetry;

pub use artifact_delivery::{
    ArtifactDeliveryConfig, ArtifactDeliveryError, ArtifactDeliveryGateway, ArtifactDeliverySigner,
    ArtifactDeliverySource, ArtifactProjectRegistry, ArtifactRangeResponse, SignedArtifactUrl,
};
pub use async_jobs::{
    AsyncJobError, DurableAsyncJobGateway, DurableJobStore, JobEventPage, JobLocator,
    JobProgressStage,
};
pub use catalog::{CATALOG_SHA256, ToolKind};
pub use error_catalog::{
    ERROR_CATALOG_SHA256, ErrorCatalogError, P15_06_ERROR_CATALOG_SHA256, PublicErrorCategory,
    PublicErrorCode, PublicErrorDescriptor, PublicErrorStage, PublicFailure, RecoveryAction,
    map_artifact_delivery_error, map_async_job_error, map_auth_error, map_gateway_error,
    map_policy_error, map_quota_error,
};
pub use handler::{
    AuthorizedToolCall, GatewayError, McpControlPlane, McpToolRequest, McpToolResult,
    ToolServiceGateway, ToolServiceOutput,
};
pub use plan_review::{
    DryRunState, EstimatedPageEffect, PlanDryRunReceipt, PlanExecutionPolicyReceipt,
    PlanReviewError, PlanReviewEvidence, PlanReviewEvidenceQuery, PlanReviewEvidenceRepository,
    PlanReviewPlanStore, PlanReviewRenderRequest, PlanReviewRenderer, PlanReviewRisk,
    PlanReviewRouteSet, PlanReviewSelectedBackend, PlanReviewSignatureImpact, PlanReviewSnapshot,
    PlanReviewWarning, PlanReviewWarningKind, PlanReviewWarningSeverity, PlanSignatureReceipt,
};
pub use policy::{
    InMemoryProjectPolicy, PolicyError, ProjectAccess, ProjectPolicy, ProjectPolicyLimits,
    ToolPolicy,
};
pub use postgres_plan_source::{
    LocalPostgresPlanSourceConfig, LocalPostgresPlanSourceRepository, PlanSourceConnectFailure,
    PlanSourceConnectStage,
};
pub use postgres_stored_plan::{
    DurablePlanConnectFailure, DurablePlanConnectStage, DurablePlanKeyring,
    LocalPostgresStoredPlanConfig, LocalPostgresStoredPlanRegistry,
};
pub use quota::{
    InMemoryQuotaService, JobClass, MAX_QUOTA_BUCKET_ENTRIES, MAX_QUOTA_REPLAY_ENTRIES,
    QUOTA_POLICY_SHA256, QuotaAdmission, QuotaError, QuotaService, QuotaStateLimits,
};
pub use stored_plan::{
    AuthorizedStoredPlan, CompiledPlanSubmission, CurrentPlanSource, PlanLookupRequest,
    PlanSourceRepository, StoredPlanError, StoredPlanLimits, StoredPlanRegistry,
};
pub use telemetry::{
    BackendClass, CapabilityRoute, CorrelationDigests, InMemoryTelemetry,
    MAX_CAPABILITY_ROUTES_PER_TRACE, MAX_TELEMETRY_TRACES, TELEMETRY_POLICY_SHA256,
    TelemetryDashboard, TelemetryError, TelemetryJobState, TelemetrySpan, TelemetrySpanState,
    TelemetryStage, TelemetryStatus, TelemetryTrace, TelemetryValidationState, TenantClass,
};
