use std::collections::BTreeMap;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};

use artifact_service::TenantId;
use auth_middleware::{AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use mcp_control_plane::{
    AuthorizedToolCall, GatewayError, InMemoryProjectPolicy, InMemoryQuotaService,
    InMemoryTelemetry, McpControlPlane, McpToolRequest, ProjectAccess, ProjectPolicyLimits,
    TELEMETRY_POLICY_SHA256, ToolKind, ToolServiceGateway, ToolServiceOutput,
};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value, json};
use sha2::Sha256;
use uuid::Uuid;

type HmacSha256 = Hmac<Sha256>;
type Control = McpControlPlane<InMemoryProjectPolicy, FixtureGateway>;

const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const KEY_ID: &str = "local-key-01";
const SECRET: &[u8] = b"0123456789abcdef0123456789abcdef";
const NOW: u64 = 2_000_000_000;
const PROJECT_ID: &str = "prj_example01";

const ALL_SCOPES: [AuthScope; 8] = [
    AuthScope::ArtifactRead,
    AuthScope::ArtifactWrite,
    AuthScope::JobCancel,
    AuthScope::JobSubmit,
    AuthScope::MirrorSync,
    AuthScope::ProjectRead,
    AuthScope::ProjectWrite,
    AuthScope::RetentionManage,
];

#[derive(Debug)]
struct FixtureGateway {
    outputs: BTreeMap<ToolKind, Value>,
    calls: Arc<AtomicUsize>,
    invalid_output: Arc<AtomicBool>,
}

impl ToolServiceGateway for FixtureGateway {
    fn dispatch(&mut self, call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        let mut output = self
            .outputs
            .get(&call.tool())
            .cloned()
            .unwrap_or_else(|| panic!("missing output for {}", call.tool().name()));
        if self.invalid_output.load(Ordering::SeqCst) {
            output
                .as_object_mut()
                .unwrap_or_else(|| panic!("fixture output object"))
                .insert("private_backend_error".to_owned(), json!("must-not-leak"));
        }
        Ok(ToolServiceOutput::new(output))
    }
}

struct Fixture {
    control: Control,
    bearer: String,
    inputs: BTreeMap<ToolKind, Value>,
    calls: Arc<AtomicUsize>,
    invalid_output: Arc<AtomicBool>,
}

#[derive(Serialize)]
struct Claims {
    iss: String,
    sub: String,
    aud: String,
    exp: u64,
    nbf: u64,
    iat: u64,
    jti: String,
    scope: String,
    token_kind: String,
    tenant_id: TenantId,
    service_id: Option<String>,
}

#[derive(Deserialize)]
struct FixtureCatalog {
    tools: Vec<FixtureTool>,
}

#[derive(Deserialize)]
struct FixtureTool {
    name: String,
    #[serde(rename = "inputSchema")]
    input_schema: Value,
    #[serde(rename = "outputSchema")]
    output_schema: Value,
}

fn fixture(trace_capacity: usize) -> Fixture {
    let tenant_id =
        TenantId::new(Uuid::from_u128(1)).unwrap_or_else(|error| panic!("tenant fixture: {error}"));
    let mut auth = AuthMiddleware::new(
        RESOURCE,
        METADATA,
        60,
        AuthRegistryLimits::product_maximums(),
    )
    .unwrap_or_else(|error| panic!("auth fixture: {error}"));
    auth.register_local_hmac_key(ISSUER, KEY_ID, SECRET, NOW - 600, NOW + 7_200)
        .unwrap_or_else(|error| panic!("key fixture: {error}"));
    let subject = auth
        .register_user(
            ISSUER,
            "oidc-user-42",
            PrincipalGrant::new(
                tenant_id,
                TenantRole::Owner,
                ALL_SCOPES,
                NOW - 600,
                NOW + 7_200,
            )
            .unwrap_or_else(|error| panic!("grant fixture: {error}")),
        )
        .unwrap_or_else(|error| panic!("user fixture: {error}"));
    let claims = Claims {
        iss: ISSUER.to_owned(),
        sub: "oidc-user-42".to_owned(),
        aud: RESOURCE.to_owned(),
        exp: NOW + 600,
        nbf: NOW - 60,
        iat: NOW - 60,
        jti: "telemetry-token-0001".to_owned(),
        scope: ALL_SCOPES
            .iter()
            .map(|scope| scope.as_str())
            .collect::<Vec<_>>()
            .join(" "),
        token_kind: "user".to_owned(),
        tenant_id,
        service_id: None,
    };
    let bearer = format!("Bearer {}", sign(&claims));
    let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
    policy
        .register_project(PROJECT_ID, tenant_id)
        .unwrap_or_else(|error| panic!("project fixture: {error}"));
    policy
        .register_membership(PROJECT_ID, subject, ProjectAccess::Owner)
        .unwrap_or_else(|error| panic!("membership fixture: {error}"));
    let (inputs, mut outputs) = catalog_fixtures();
    let create = outputs
        .get_mut(&ToolKind::DocumentCreate)
        .and_then(Value::as_object_mut)
        .unwrap_or_else(|| panic!("document_create output"));
    create.insert("commit_state".to_owned(), json!("committed"));
    create.insert("validation_state".to_owned(), json!("verified"));
    let calls = Arc::new(AtomicUsize::new(0));
    let invalid_output = Arc::new(AtomicBool::new(false));
    let control = McpControlPlane::with_quota_and_telemetry(
        auth,
        policy,
        InMemoryQuotaService::new().unwrap_or_else(|error| panic!("quota fixture: {error}")),
        InMemoryTelemetry::with_trace_capacity(trace_capacity)
            .unwrap_or_else(|error| panic!("telemetry fixture: {error}")),
        FixtureGateway {
            outputs,
            calls: Arc::clone(&calls),
            invalid_output: Arc::clone(&invalid_output),
        },
    )
    .unwrap_or_else(|error| panic!("control fixture: {error}"));
    Fixture {
        control,
        bearer,
        inputs,
        calls,
        invalid_output,
    }
}

impl Fixture {
    fn call(&mut self, tool: ToolKind, now: u64) -> mcp_control_plane::McpToolResult {
        let arguments = self
            .inputs
            .get(&tool)
            .unwrap_or_else(|| panic!("missing input for {}", tool.name()));
        self.control.handle(McpToolRequest::new(
            tool.name(),
            self.bearer.clone(),
            serde_json::to_vec(arguments)
                .unwrap_or_else(|error| panic!("serialize input: {error}")),
            now,
        ))
    }
}

fn sign(claims: &Claims) -> String {
    let header = URL_SAFE_NO_PAD.encode(
        serde_json::to_vec(&json!({"alg": "HS256", "kid": KEY_ID, "typ": "at+jwt"}))
            .unwrap_or_else(|error| panic!("header: {error}")),
    );
    let claims = URL_SAFE_NO_PAD
        .encode(serde_json::to_vec(claims).unwrap_or_else(|error| panic!("claims: {error}")));
    let signing_input = format!("{header}.{claims}");
    let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(SECRET)
        .unwrap_or_else(|error| panic!("signer: {error}"));
    signer.update(signing_input.as_bytes());
    format!(
        "{signing_input}.{}",
        URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
    )
}

fn catalog_fixtures() -> (BTreeMap<ToolKind, Value>, BTreeMap<ToolKind, Value>) {
    let catalog: FixtureCatalog = serde_json::from_str(include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../protocol/mcp/p15-public-tools-v1.json"
    )))
    .unwrap_or_else(|error| panic!("catalog: {error}"));
    let mut inputs = BTreeMap::new();
    let mut outputs = BTreeMap::new();
    for descriptor in catalog.tools {
        let tool = ToolKind::parse(&descriptor.name)
            .unwrap_or_else(|| panic!("unknown tool: {}", descriptor.name));
        inputs.insert(tool, synthesize(&descriptor.input_schema));
        outputs.insert(tool, synthesize(&descriptor.output_schema));
    }
    (inputs, outputs)
}

fn synthesize(node: &Value) -> Value {
    if let Some(reference) = node.get("$ref").and_then(Value::as_str) {
        return reference_sample(reference);
    }
    if let Some(value) = node.get("const") {
        return value.clone();
    }
    if let Some(values) = node.get("enum").and_then(Value::as_array) {
        return values
            .first()
            .cloned()
            .unwrap_or_else(|| panic!("empty enum"));
    }
    if let Some(branches) = node.get("oneOf").and_then(Value::as_array) {
        return synthesize(branches.first().unwrap_or_else(|| panic!("empty oneOf")));
    }
    match node.get("type").and_then(Value::as_str) {
        Some("object") => {
            let properties = node
                .get("properties")
                .and_then(Value::as_object)
                .unwrap_or_else(|| panic!("object properties"));
            let required = node
                .get("required")
                .and_then(Value::as_array)
                .unwrap_or_else(|| panic!("object required"));
            let mut result = Map::new();
            for key in required {
                let key = key.as_str().unwrap_or_else(|| panic!("required key"));
                result.insert(
                    key.to_owned(),
                    synthesize(
                        properties
                            .get(key)
                            .unwrap_or_else(|| panic!("property schema: {key}")),
                    ),
                );
            }
            Value::Object(result)
        }
        Some("array") => {
            let count = node.get("minItems").and_then(Value::as_u64).unwrap_or(0);
            let item = node.get("items").unwrap_or_else(|| panic!("array items"));
            Value::Array((0..count).map(|_| synthesize(item)).collect())
        }
        Some("boolean") => Value::Bool(false),
        Some("integer" | "number") => node.get("minimum").cloned().unwrap_or_else(|| json!(0)),
        Some("null") => Value::Null,
        Some("string") => string_sample(node),
        other => panic!("unsupported schema node: {other:?}"),
    }
}

fn reference_sample(reference: &str) -> Value {
    let value = match reference {
        "#/$defs/artifact_id" => "art_example01",
        "#/$defs/capability_id" => "page.paper_preset",
        "#/$defs/checkpoint_id" => "chk_example01",
        "#/$defs/cursor" => "Y3Vyc29y",
        "#/$defs/idempotency_key" => "123e4567-e89b-12d3-a456-426614174000",
        "#/$defs/job_id" => "job_example01",
        "#/$defs/locale" => "ko-KR",
        "#/$defs/media_type" => "application/hwp+zip",
        "#/$defs/plan_id" => "plan_example01",
        "#/$defs/project_id" => PROJECT_ID,
        "#/$defs/request_id" => "req_example01",
        "#/$defs/revision_id" => "rev_example01",
        "#/$defs/target_profile" => "hancom-hangul-2020-secondary",
        "#/$defs/template_contract_id" => "tpl_example01",
        "#/$defs/timestamp" => "2026-09-04T00:00:00Z",
        _ => panic!("unsupported reference: {reference}"),
    };
    json!(value)
}

fn string_sample(node: &Value) -> Value {
    let pattern = node.get("pattern").and_then(Value::as_str).unwrap_or("");
    let value = if pattern == "^[0-9a-f]{64}$" {
        "a".repeat(64)
    } else if pattern.starts_with("^snp_") {
        "snp_example01".to_owned()
    } else if pattern.starts_with("^rcp_") {
        "rcp_example01".to_owned()
    } else if pattern.starts_with("^[A-Z]") {
        "TEST_CODE".to_owned()
    } else if pattern.starts_with("^[a-z][a-z0-9_]*(?:\\.") {
        "page.paper".to_owned()
    } else if pattern.starts_with("^[a-z][a-z0-9_]") {
        "stage".to_owned()
    } else {
        "value".to_owned()
    };
    json!(value)
}

#[test]
fn successful_document_trace_has_complete_ordered_hierarchy_and_correlations() {
    let mut fixture = fixture(16);
    let result = fixture.call(ToolKind::DocumentCreate, NOW);
    assert!(!result.is_error(), "{result:?}");
    let trace = fixture
        .control
        .telemetry()
        .latest_trace()
        .unwrap_or_else(|| panic!("latest trace"))
        .to_json_value();
    assert_eq!(
        trace["spans"],
        json!([
            {"stage": "mcp_request", "state": "completed"},
            {"stage": "capability_plan", "state": "completed"},
            {"stage": "job", "state": "completed"},
            {"stage": "backend_execution", "state": "completed"},
            {"stage": "validation_step", "state": "completed"},
            {"stage": "artifact_commit", "state": "completed"}
        ])
    );
    assert_eq!(trace["job_state"], "accepted");
    assert_eq!(trace["tenant_class"], "local_reference");
    for field in [
        "request_id",
        "job_id",
        "execution_id",
        "revision_id",
        "evidence_id",
    ] {
        let digest = trace["correlation"][field]
            .as_str()
            .unwrap_or_else(|| panic!("correlation {field}"));
        assert_eq!(digest.len(), 64);
        assert!(digest.bytes().all(|byte| byte.is_ascii_hexdigit()));
    }
}

#[test]
fn public_result_exposes_policy_digest_but_never_internal_trace_id() {
    let mut fixture = fixture(16);
    let result = fixture.call(ToolKind::ProjectOpen, NOW);
    assert_eq!(
        result.meta()["hwpx/telemetryPolicySha256"],
        TELEMETRY_POLICY_SHA256
    );
    let serialized =
        serde_json::to_string(&result).unwrap_or_else(|error| panic!("result: {error}"));
    assert!(!serialized.contains("trace_id"));
    assert!(!serialized.contains("trc_"));
    let error = fixture.control.handle(McpToolRequest::new(
        "unknown_tool",
        "Bearer not-recorded",
        b"{}".to_vec(),
        NOW,
    ));
    assert!(error.is_error());
    assert_eq!(
        error.meta()["hwpx/telemetryPolicySha256"],
        TELEMETRY_POLICY_SHA256
    );
}

#[test]
fn dashboard_aggregates_success_and_pre_dispatch_error_without_identifiers() {
    let mut fixture = fixture(16);
    assert!(!fixture.call(ToolKind::ProjectOpen, NOW).is_error());
    let failed = fixture.control.handle(McpToolRequest::new(
        "project_open",
        fixture.bearer.clone(),
        br#"{"request_id":"req_invalid01","private":"value"}"#.to_vec(),
        NOW + 1,
    ));
    assert_eq!(failed.error_code(), Some("TOOL_INPUT_SCHEMA_INVALID"));
    let dashboard = fixture.control.telemetry().dashboard().to_json_value();
    assert_eq!(dashboard["retained_traces"], 2);
    assert_eq!(dashboard["tool_sli"].as_array().map(Vec::len), Some(2));
    let text = dashboard.to_string();
    assert!(!text.contains("req_invalid01"));
    assert!(!text.contains(PROJECT_ID));
}

#[test]
fn telemetry_never_retains_bearer_arguments_or_backend_error_text() {
    let mut primary = fixture(16);
    primary.invalid_output.store(true, Ordering::SeqCst);
    let result = primary.call(ToolKind::ProjectOpen, NOW);
    assert_eq!(result.error_code(), Some("TOOL_OUTPUT_SCHEMA_INVALID"));
    let trace = primary
        .control
        .telemetry()
        .latest_trace()
        .unwrap_or_else(|| panic!("trace"))
        .to_json_value()
        .to_string();
    for forbidden in [
        "oidc-user-42",
        "telemetry-token-0001",
        "0123456789abcdef",
        "must-not-leak",
        PROJECT_ID,
        "req_example01",
    ] {
        assert!(!trace.contains(forbidden), "retained {forbidden}");
    }

    let mut invalid = fixture(16);
    let result = invalid.control.handle(McpToolRequest::new(
        "project_open",
        invalid.bearer.clone(),
        br#"{"request_id":"req_private01","document_body":"TOP SECRET BODY"}"#.to_vec(),
        NOW,
    ));
    assert_eq!(result.error_code(), Some("TOOL_INPUT_SCHEMA_INVALID"));
    let invalid_trace = invalid
        .control
        .telemetry()
        .latest_trace()
        .unwrap_or_else(|| panic!("invalid trace"))
        .to_json_value()
        .to_string();
    assert!(!invalid_trace.contains("TOP SECRET BODY"));
    assert!(!invalid_trace.contains("document_body"));

    let mut other_process = fixture(16);
    assert!(!other_process.call(ToolKind::ProjectOpen, NOW).is_error());
    let other_trace = other_process
        .control
        .telemetry()
        .latest_trace()
        .unwrap_or_else(|| panic!("other trace"))
        .to_json_value();
    let first_request_digest = trace
        .parse::<Value>()
        .unwrap_or_else(|error| panic!("first trace JSON: {error}"))["correlation"]["request_id"]
        .clone();
    assert_ne!(
        first_request_digest,
        other_trace["correlation"]["request_id"]
    );
}

#[test]
fn capability_routes_are_digest_keyed_and_backend_aggregated() {
    let mut fixture = fixture(16);
    let result = fixture.call(ToolKind::CapabilityCheck, NOW);
    assert!(!result.is_error(), "{result:?}");
    let dashboard = fixture.control.telemetry().dashboard().to_json_value();
    let routes = dashboard["capability_sli"]
        .as_array()
        .unwrap_or_else(|| panic!("capability SLI"));
    assert_eq!(routes.len(), 1);
    assert_eq!(routes[0]["backend"], "direct_hwpx");
    assert_eq!(
        routes[0]["capability_digest"].as_str().map(str::len),
        Some(64)
    );
    assert!(!dashboard.to_string().contains("page.paper_preset"));
}

#[test]
fn bounded_ring_evicts_only_whole_oldest_traces() {
    let mut fixture = fixture(2);
    for offset in 0..3 {
        let result = fixture.call(ToolKind::ProjectOpen, NOW + offset);
        assert!(!result.is_error(), "{result:?}");
    }
    assert_eq!(fixture.control.telemetry().trace_count(), 2);
    assert_eq!(fixture.control.telemetry().evicted_trace_count(), 1);
    let dashboard = fixture.control.telemetry().dashboard().to_json_value();
    assert_eq!(dashboard["retained_traces"], 2);
    assert_eq!(dashboard["evicted_traces"], 1);
    assert_eq!(dashboard["tool_sli"][0]["count"], 2);
}

#[test]
fn telemetry_capacity_is_strictly_bounded_by_embedded_policy() {
    assert!(InMemoryTelemetry::with_trace_capacity(0).is_err());
    assert!(InMemoryTelemetry::with_trace_capacity(2_049).is_err());
    assert!(InMemoryTelemetry::with_trace_capacity(2_048).is_ok());
}

#[test]
fn invalid_backend_output_records_failed_validation_after_one_dispatch() {
    let mut fixture = fixture(16);
    fixture.invalid_output.store(true, Ordering::SeqCst);
    let result = fixture.call(ToolKind::ProjectOpen, NOW);
    assert_eq!(result.error_code(), Some("TOOL_OUTPUT_SCHEMA_INVALID"));
    assert_eq!(fixture.calls.load(Ordering::SeqCst), 1);
    let trace = fixture
        .control
        .telemetry()
        .latest_trace()
        .unwrap_or_else(|| panic!("trace"))
        .to_json_value();
    assert_eq!(trace["status"], "error");
    assert_eq!(trace["error_code"], "TOOL_OUTPUT_SCHEMA_INVALID");
    assert_eq!(trace["spans"][3]["state"], "completed");
    assert_eq!(trace["spans"][4]["state"], "failed");
}
