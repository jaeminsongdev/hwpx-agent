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
mod policy;
mod quota;
mod strict_json;

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
pub use policy::{
    InMemoryProjectPolicy, PolicyError, ProjectAccess, ProjectPolicyLimits, ToolPolicy,
};
pub use quota::{
    InMemoryQuotaService, JobClass, MAX_QUOTA_BUCKET_ENTRIES, MAX_QUOTA_REPLAY_ENTRIES,
    QUOTA_POLICY_SHA256, QuotaAdmission, QuotaError, QuotaService, QuotaStateLimits,
};
