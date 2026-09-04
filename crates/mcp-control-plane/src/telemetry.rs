use std::collections::{BTreeMap, BTreeSet, VecDeque};
use std::fmt;
use std::time::Instant;

use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use uuid::Uuid;
use zeroize::Zeroize;

use crate::catalog::ToolKind;
use crate::error_catalog::{PublicErrorCode, PublicErrorStage, PublicFailure};

const POLICY_BYTES: &[u8] = include_bytes!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../protocol/mcp/p15-telemetry-policy-v1.json"
));
const POLICY_SCHEMA_VERSION: &str = "hwpx-agent.telemetry-policy/v1";
const TRACE_SCHEMA_VERSION: &str = "hwpx-agent.telemetry-trace/v1";
const DASHBOARD_SCHEMA_VERSION: &str = "hwpx-agent.telemetry-dashboard/v1";
pub const TELEMETRY_POLICY_SHA256: &str =
    "052607176a31b5bedda3210e27ddb35d92df1b5126d881219606fb8a960274d1";
pub const MAX_TELEMETRY_TRACES: usize = 2_048;
pub const MAX_CAPABILITY_ROUTES_PER_TRACE: usize = 128;

const CORRELATION_FIELDS: [&str; 5] = [
    "request_id",
    "job_id",
    "execution_id",
    "revision_id",
    "evidence_id",
];
const DASHBOARD_DIMENSIONS: [&str; 6] = [
    "tool",
    "tenant_class",
    "job",
    "backend",
    "capability",
    "validation_state",
];
const TENANT_CLASSES: [&str; 2] = ["unattributed", "local_reference"];

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TelemetryStage {
    McpRequest,
    CapabilityPlan,
    Job,
    BackendExecution,
    ValidationStep,
    ArtifactCommit,
}

impl TelemetryStage {
    pub const ALL: [Self; 6] = [
        Self::McpRequest,
        Self::CapabilityPlan,
        Self::Job,
        Self::BackendExecution,
        Self::ValidationStep,
        Self::ArtifactCommit,
    ];

    const fn as_str(self) -> &'static str {
        match self {
            Self::McpRequest => "mcp_request",
            Self::CapabilityPlan => "capability_plan",
            Self::Job => "job",
            Self::BackendExecution => "backend_execution",
            Self::ValidationStep => "validation_step",
            Self::ArtifactCommit => "artifact_commit",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TelemetrySpanState {
    Completed,
    Failed,
    NotApplicable,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TelemetryStatus {
    Success,
    Error,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TenantClass {
    LocalReference,
    Unattributed,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BackendClass {
    ControlPlane,
    Auto,
    DirectHwpx,
    Hancom2020,
    Hybrid,
    InternalPreview,
    LibreOffice,
    None,
}

impl BackendClass {
    fn parse(value: &str) -> Option<Self> {
        match value {
            "auto" => Some(Self::Auto),
            "direct_hwpx" => Some(Self::DirectHwpx),
            "hancom_2020" => Some(Self::Hancom2020),
            "hybrid" => Some(Self::Hybrid),
            "internal_preview" => Some(Self::InternalPreview),
            "libreoffice" => Some(Self::LibreOffice),
            "none" => Some(Self::None),
            _ => None,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TelemetryValidationState {
    Failed,
    NotReported,
    Partial,
    Unverified,
    Verified,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TelemetryJobState {
    Accepted,
    Cancelled,
    Cancelling,
    Failed,
    NotApplicable,
    Observed,
    Partial,
    Queued,
    Running,
    Succeeded,
    Unverified,
}

impl TelemetryJobState {
    fn parse(value: &str) -> Option<Self> {
        match value {
            "accepted" => Some(Self::Accepted),
            "cancelled" => Some(Self::Cancelled),
            "cancelling" => Some(Self::Cancelling),
            "failed" => Some(Self::Failed),
            "partial" => Some(Self::Partial),
            "queued" => Some(Self::Queued),
            "running" => Some(Self::Running),
            "succeeded" => Some(Self::Succeeded),
            "unverified" => Some(Self::Unverified),
            _ => None,
        }
    }
}

impl TelemetryValidationState {
    fn parse(value: &str) -> Option<Self> {
        match value {
            "failed" => Some(Self::Failed),
            "not_run" | "queued" | "running" | "unverified" => Some(Self::Unverified),
            "partial" => Some(Self::Partial),
            "verified" => Some(Self::Verified),
            _ => None,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct TelemetrySpan {
    stage: TelemetryStage,
    state: TelemetrySpanState,
}

#[derive(Clone, Debug, Default, Eq, PartialEq, Serialize)]
pub struct CorrelationDigests {
    #[serde(rename = "request_id")]
    request: Option<String>,
    #[serde(rename = "job_id")]
    job: Option<String>,
    #[serde(rename = "execution_id")]
    execution: Option<String>,
    #[serde(rename = "revision_id")]
    revision: Option<String>,
    #[serde(rename = "evidence_id")]
    evidence: Option<String>,
}

impl CorrelationDigests {
    fn set(&mut self, field: &str, digest: String) {
        match field {
            "request_id" => self.request = Some(digest),
            "job_id" => self.job = Some(digest),
            "execution_id" => self.execution = Some(digest),
            "revision_id" => self.revision = Some(digest),
            "evidence_id" => self.evidence = Some(digest),
            _ => {}
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CapabilityRoute {
    capability_digest: String,
    backend: Option<BackendClass>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct TelemetryTrace {
    schema_version: &'static str,
    trace_id: String,
    observed_at_unix_seconds: u64,
    tool: Option<String>,
    tenant_class: TenantClass,
    status: TelemetryStatus,
    error_code: Option<PublicErrorCode>,
    latency_ms: u64,
    correlation: CorrelationDigests,
    backends: Vec<BackendClass>,
    capabilities: Vec<CapabilityRoute>,
    job_state: TelemetryJobState,
    validation_state: TelemetryValidationState,
    spans: Vec<TelemetrySpan>,
}

impl TelemetryTrace {
    #[must_use]
    pub fn trace_id(&self) -> &str {
        &self.trace_id
    }

    #[must_use]
    pub fn to_json_value(&self) -> Value {
        serde_json::to_value(self).unwrap_or(Value::Null)
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ToolSliRow {
    tool: String,
    tenant_class: TenantClass,
    status: TelemetryStatus,
    count: u64,
    total_latency_ms: u64,
    maximum_latency_ms: u64,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct JobSliRow {
    job_state: TelemetryJobState,
    status: TelemetryStatus,
    count: u64,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct BackendSliRow {
    backend: BackendClass,
    status: TelemetryStatus,
    count: u64,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CapabilitySliRow {
    capability_digest: String,
    backend: Option<BackendClass>,
    status: TelemetryStatus,
    count: u64,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ValidationSliRow {
    validation_state: TelemetryValidationState,
    status: TelemetryStatus,
    count: u64,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct TelemetryDashboard {
    schema_version: &'static str,
    telemetry_policy_sha256: &'static str,
    trace_capacity: usize,
    retained_traces: usize,
    evicted_traces: u64,
    tool_sli: Vec<ToolSliRow>,
    job_sli: Vec<JobSliRow>,
    backend_sli: Vec<BackendSliRow>,
    capability_sli: Vec<CapabilitySliRow>,
    validation_sli: Vec<ValidationSliRow>,
}

impl TelemetryDashboard {
    #[must_use]
    pub fn to_json_value(&self) -> Value {
        serde_json::to_value(self).unwrap_or(Value::Null)
    }
}

pub struct InMemoryTelemetry {
    trace_capacity: usize,
    salt: [u8; 32],
    traces: VecDeque<TelemetryTrace>,
    evicted_traces: u64,
}

impl InMemoryTelemetry {
    /// Loads the digest-pinned telemetry policy and allocates its bounded trace ring.
    ///
    /// # Errors
    ///
    /// Fails when the embedded policy digest or closed shape has drifted.
    pub fn new() -> Result<Self, TelemetryError> {
        Self::with_trace_capacity(MAX_TELEMETRY_TRACES)
    }

    /// Creates a smaller bounded ring for local tests or constrained deployments.
    ///
    /// # Errors
    ///
    /// Rejects zero or policy-exceeding capacities and any embedded policy drift.
    pub fn with_trace_capacity(trace_capacity: usize) -> Result<Self, TelemetryError> {
        validate_policy()?;
        if !(1..=MAX_TELEMETRY_TRACES).contains(&trace_capacity) {
            return Err(TelemetryError::InvalidCapacity);
        }
        let first = Uuid::new_v4();
        let second = Uuid::new_v4();
        let mut salt = [0_u8; 32];
        salt[..16].copy_from_slice(first.as_bytes());
        salt[16..].copy_from_slice(second.as_bytes());
        Ok(Self {
            trace_capacity,
            salt,
            traces: VecDeque::with_capacity(trace_capacity),
            evicted_traces: 0,
        })
    }

    pub(crate) fn begin_trace(
        &self,
        fallback_request_id: &str,
        observed_at_unix_seconds: u64,
    ) -> TraceObservation {
        TraceObservation::new(self.salt, fallback_request_id, observed_at_unix_seconds)
    }

    pub(crate) fn commit(&mut self, trace: TelemetryTrace) {
        if self.traces.len() == self.trace_capacity {
            self.traces.pop_front();
            self.evicted_traces = self.evicted_traces.saturating_add(1);
        }
        self.traces.push_back(trace);
    }

    #[must_use]
    pub fn trace_count(&self) -> usize {
        self.traces.len()
    }

    #[must_use]
    pub fn evicted_trace_count(&self) -> u64 {
        self.evicted_traces
    }

    #[must_use]
    pub fn latest_trace(&self) -> Option<TelemetryTrace> {
        self.traces.back().cloned()
    }

    #[must_use]
    pub fn dashboard(&self) -> TelemetryDashboard {
        let mut tools = BTreeMap::<(String, TenantClass, TelemetryStatus), (u64, u64, u64)>::new();
        let mut jobs = BTreeMap::<(TelemetryJobState, TelemetryStatus), u64>::new();
        let mut backends = BTreeMap::<(BackendClass, TelemetryStatus), u64>::new();
        let mut capabilities =
            BTreeMap::<(String, Option<BackendClass>, TelemetryStatus), u64>::new();
        let mut validation = BTreeMap::<(TelemetryValidationState, TelemetryStatus), u64>::new();
        for trace in &self.traces {
            let tool_key = (
                trace.tool.clone().unwrap_or_else(|| "unknown".to_owned()),
                trace.tenant_class,
                trace.status,
            );
            let tool = tools.entry(tool_key).or_default();
            tool.0 = tool.0.saturating_add(1);
            tool.1 = tool.1.saturating_add(trace.latency_ms);
            tool.2 = tool.2.max(trace.latency_ms);
            *jobs.entry((trace.job_state, trace.status)).or_default() += 1;
            for backend in &trace.backends {
                *backends.entry((*backend, trace.status)).or_default() += 1;
            }
            for route in &trace.capabilities {
                *capabilities
                    .entry((route.capability_digest.clone(), route.backend, trace.status))
                    .or_default() += 1;
            }
            *validation
                .entry((trace.validation_state, trace.status))
                .or_default() += 1;
        }
        TelemetryDashboard {
            schema_version: DASHBOARD_SCHEMA_VERSION,
            telemetry_policy_sha256: TELEMETRY_POLICY_SHA256,
            trace_capacity: self.trace_capacity,
            retained_traces: self.traces.len(),
            evicted_traces: self.evicted_traces,
            tool_sli: tools
                .into_iter()
                .map(
                    |((tool, tenant_class, status), (count, total, maximum))| ToolSliRow {
                        tool,
                        tenant_class,
                        status,
                        count,
                        total_latency_ms: total,
                        maximum_latency_ms: maximum,
                    },
                )
                .collect(),
            job_sli: jobs
                .into_iter()
                .map(|((job_state, status), count)| JobSliRow {
                    job_state,
                    status,
                    count,
                })
                .collect(),
            backend_sli: backends
                .into_iter()
                .map(|((backend, status), count)| BackendSliRow {
                    backend,
                    status,
                    count,
                })
                .collect(),
            capability_sli: capabilities
                .into_iter()
                .map(
                    |((capability_digest, backend, status), count)| CapabilitySliRow {
                        capability_digest,
                        backend,
                        status,
                        count,
                    },
                )
                .collect(),
            validation_sli: validation
                .into_iter()
                .map(|((validation_state, status), count)| ValidationSliRow {
                    validation_state,
                    status,
                    count,
                })
                .collect(),
        }
    }
}

impl fmt::Debug for InMemoryTelemetry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("InMemoryTelemetry")
            .field("telemetry_policy_sha256", &TELEMETRY_POLICY_SHA256)
            .field("trace_capacity", &self.trace_capacity)
            .field("retained_traces", &self.traces.len())
            .field("evicted_traces", &self.evicted_traces)
            .field("salt", &"<redacted>")
            .finish()
    }
}

impl Drop for InMemoryTelemetry {
    fn drop(&mut self) {
        self.salt.zeroize();
    }
}

#[derive(Debug, Error)]
pub enum TelemetryError {
    #[error("the embedded telemetry policy does not match its pinned digest")]
    DigestMismatch,
    #[error("the embedded telemetry policy has an invalid closed shape")]
    InvalidPolicy,
    #[error("telemetry trace capacity is outside the policy bound")]
    InvalidCapacity,
}

pub(crate) struct TraceObservation {
    salt: [u8; 32],
    started_at: Instant,
    trace_id: String,
    observed_at_unix_seconds: u64,
    tool: Option<ToolKind>,
    tenant_class: TenantClass,
    correlation: CorrelationDigests,
    backends: BTreeSet<BackendClass>,
    capabilities: Vec<CapabilityRoute>,
    policy_completed: bool,
    dispatch_state: DispatchObservation,
    output_validated: bool,
    artifact_committed: bool,
    job_state: TelemetryJobState,
    validation_state: TelemetryValidationState,
}

#[derive(Clone, Copy)]
enum DispatchObservation {
    NotAttempted,
    Attempted,
    Returned,
}

impl TraceObservation {
    fn new(salt: [u8; 32], fallback_request_id: &str, observed_at_unix_seconds: u64) -> Self {
        let trace_id = format!("trc_{}", Uuid::new_v4().simple());
        let mut correlation = CorrelationDigests::default();
        correlation.set(
            "request_id",
            digest_identifier(&salt, "request_id", fallback_request_id),
        );
        Self {
            salt,
            started_at: Instant::now(),
            trace_id,
            observed_at_unix_seconds,
            tool: None,
            tenant_class: TenantClass::Unattributed,
            correlation,
            backends: BTreeSet::new(),
            capabilities: Vec::new(),
            policy_completed: false,
            dispatch_state: DispatchObservation::NotAttempted,
            output_validated: false,
            artifact_committed: false,
            job_state: TelemetryJobState::NotApplicable,
            validation_state: TelemetryValidationState::NotReported,
        }
    }

    pub(crate) fn set_tool(&mut self, tool: ToolKind) {
        self.tool = Some(tool);
    }

    pub(crate) fn mark_authenticated(&mut self) {
        self.tenant_class = TenantClass::LocalReference;
    }

    pub(crate) fn observe_validated_input(&mut self, arguments: &Value, request_id: &str) {
        self.set_correlation("request_id", request_id);
        for field in ["job_id", "revision_id"] {
            if let Some(value) = arguments.get(field).and_then(Value::as_str) {
                self.set_correlation(field, value);
            }
        }
        if let Some(backend) = arguments
            .get("backend")
            .and_then(Value::as_str)
            .and_then(BackendClass::parse)
        {
            self.backends.insert(backend);
        }
        if let Some(capabilities) = arguments.get("capabilities").and_then(Value::as_array) {
            for capability in capabilities
                .iter()
                .filter_map(Value::as_str)
                .take(MAX_CAPABILITY_ROUTES_PER_TRACE)
            {
                self.capabilities.push(CapabilityRoute {
                    capability_digest: digest_identifier(&self.salt, "capability_id", capability),
                    backend: None,
                });
            }
        }
    }

    pub(crate) fn mark_policy_completed(&mut self) {
        self.policy_completed = true;
    }

    pub(crate) fn mark_dispatch_attempted(&mut self) {
        self.dispatch_state = DispatchObservation::Attempted;
        let trace_id = self.trace_id.clone();
        self.set_correlation("execution_id", &trace_id);
        if self.backends.is_empty() {
            self.backends.insert(BackendClass::ControlPlane);
        }
    }

    pub(crate) fn mark_dispatch_returned(&mut self) {
        self.dispatch_state = DispatchObservation::Returned;
    }

    pub(crate) fn observe_validated_output(&mut self, output: &Value) {
        for field in ["job_id", "revision_id"] {
            if let Some(value) = output.get(field).and_then(Value::as_str) {
                self.set_correlation(field, value);
            }
        }
        if let Some(evidence) = output
            .get("artifact")
            .and_then(Value::as_object)
            .and_then(|artifact| artifact.get("sha256"))
            .and_then(Value::as_str)
            .or_else(|| output.get("preview_artifact_id").and_then(Value::as_str))
        {
            self.set_correlation("evidence_id", evidence);
        }
        if output.get("commit_state").and_then(Value::as_str) == Some("committed") {
            self.artifact_committed = true;
        }
        if let Some(state) = output
            .get("validation_state")
            .and_then(Value::as_str)
            .and_then(TelemetryValidationState::parse)
        {
            self.validation_state = state;
        }
        self.job_state = ["state", "render_state", "outcome"]
            .into_iter()
            .filter_map(|field| output.get(field).and_then(Value::as_str))
            .find_map(TelemetryJobState::parse)
            .unwrap_or(self.job_state);
        if let Some(capabilities) = output.get("capabilities").and_then(Value::as_array) {
            for capability in capabilities.iter().take(MAX_CAPABILITY_ROUTES_PER_TRACE) {
                let Some(identifier) = capability.get("capability_id").and_then(Value::as_str)
                else {
                    continue;
                };
                let digest = digest_identifier(&self.salt, "capability_id", identifier);
                let backend = capability
                    .get("selected_backend")
                    .and_then(Value::as_str)
                    .and_then(BackendClass::parse);
                if let Some(existing) = self
                    .capabilities
                    .iter_mut()
                    .find(|route| route.capability_digest == digest)
                {
                    existing.backend = backend;
                } else if self.capabilities.len() < MAX_CAPABILITY_ROUTES_PER_TRACE {
                    self.capabilities.push(CapabilityRoute {
                        capability_digest: digest,
                        backend,
                    });
                }
                if let Some(backend) = backend {
                    self.backends.insert(backend);
                }
            }
        }
        self.output_validated = true;
    }

    pub(crate) fn finish(mut self, failure: Option<PublicFailure>) -> TelemetryTrace {
        let status = if failure.is_some() {
            TelemetryStatus::Error
        } else {
            TelemetryStatus::Success
        };
        let failure_stage = failure.map(PublicFailure::stage);
        let job_state = if self.correlation.job.is_some()
            && self.job_state == TelemetryJobState::NotApplicable
        {
            TelemetryJobState::Observed
        } else {
            self.job_state
        };
        let spans = vec![
            TelemetrySpan {
                stage: TelemetryStage::McpRequest,
                state: if matches!(
                    failure_stage,
                    Some(
                        PublicErrorStage::Admission
                            | PublicErrorStage::Authenticate
                            | PublicErrorStage::Parse
                            | PublicErrorStage::InputValidation
                    )
                ) {
                    TelemetrySpanState::Failed
                } else {
                    TelemetrySpanState::Completed
                },
            },
            TelemetrySpan {
                stage: TelemetryStage::CapabilityPlan,
                state: if self.policy_completed {
                    TelemetrySpanState::Completed
                } else if matches!(failure_stage, Some(PublicErrorStage::Policy)) {
                    TelemetrySpanState::Failed
                } else {
                    TelemetrySpanState::NotApplicable
                },
            },
            TelemetrySpan {
                stage: TelemetryStage::Job,
                state: if job_state == TelemetryJobState::NotApplicable {
                    TelemetrySpanState::NotApplicable
                } else {
                    TelemetrySpanState::Completed
                },
            },
            TelemetrySpan {
                stage: TelemetryStage::BackendExecution,
                state: if matches!(self.dispatch_state, DispatchObservation::Returned) {
                    TelemetrySpanState::Completed
                } else if matches!(self.dispatch_state, DispatchObservation::Attempted) {
                    TelemetrySpanState::Failed
                } else {
                    TelemetrySpanState::NotApplicable
                },
            },
            TelemetrySpan {
                stage: TelemetryStage::ValidationStep,
                state: if self.output_validated {
                    TelemetrySpanState::Completed
                } else if matches!(self.dispatch_state, DispatchObservation::Returned) {
                    TelemetrySpanState::Failed
                } else {
                    TelemetrySpanState::NotApplicable
                },
            },
            TelemetrySpan {
                stage: TelemetryStage::ArtifactCommit,
                state: if self.artifact_committed {
                    TelemetrySpanState::Completed
                } else {
                    TelemetrySpanState::NotApplicable
                },
            },
        ];
        TelemetryTrace {
            schema_version: TRACE_SCHEMA_VERSION,
            trace_id: std::mem::take(&mut self.trace_id),
            observed_at_unix_seconds: self.observed_at_unix_seconds,
            tool: self.tool.map(|tool| tool.name().to_owned()),
            tenant_class: self.tenant_class,
            status,
            error_code: failure.map(PublicFailure::code),
            latency_ms: u64::try_from(self.started_at.elapsed().as_millis()).unwrap_or(u64::MAX),
            correlation: std::mem::take(&mut self.correlation),
            backends: std::mem::take(&mut self.backends).into_iter().collect(),
            capabilities: std::mem::take(&mut self.capabilities),
            job_state,
            validation_state: self.validation_state,
            spans,
        }
    }

    fn set_correlation(&mut self, field: &str, value: &str) {
        self.correlation
            .set(field, digest_identifier(&self.salt, field, value));
    }
}

impl Drop for TraceObservation {
    fn drop(&mut self) {
        self.salt.zeroize();
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RawPolicy {
    correlation_fields: Vec<String>,
    dashboard_dimensions: Vec<String>,
    max_capability_routes_per_trace: usize,
    schema_version: String,
    tenant_classes: Vec<String>,
    trace_capacity: usize,
    trace_stages: Vec<String>,
}

fn validate_policy() -> Result<(), TelemetryError> {
    if hex::encode(Sha256::digest(POLICY_BYTES)) != TELEMETRY_POLICY_SHA256 {
        return Err(TelemetryError::DigestMismatch);
    }
    let policy: RawPolicy =
        serde_json::from_slice(POLICY_BYTES).map_err(|_| TelemetryError::InvalidPolicy)?;
    let stages = TelemetryStage::ALL
        .into_iter()
        .map(TelemetryStage::as_str)
        .collect::<Vec<_>>();
    if policy.schema_version != POLICY_SCHEMA_VERSION
        || policy.trace_capacity != MAX_TELEMETRY_TRACES
        || policy.max_capability_routes_per_trace != MAX_CAPABILITY_ROUTES_PER_TRACE
        || policy.correlation_fields != CORRELATION_FIELDS
        || policy.dashboard_dimensions != DASHBOARD_DIMENSIONS
        || policy.tenant_classes != TENANT_CLASSES
        || policy.trace_stages != stages
    {
        return Err(TelemetryError::InvalidPolicy);
    }
    Ok(())
}

fn digest_identifier(salt: &[u8; 32], label: &str, value: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(salt);
    hasher.update(label.len().to_le_bytes());
    hasher.update(label.as_bytes());
    hasher.update(value.len().to_le_bytes());
    hasher.update(value.as_bytes());
    hex::encode(hasher.finalize())
}
