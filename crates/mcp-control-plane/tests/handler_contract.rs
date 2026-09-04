use std::collections::BTreeMap;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};

use artifact_service::TenantId;
use auth_middleware::{
    AuthContext, AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole,
};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use mcp_control_plane::{
    AuthorizedToolCall, GatewayError, InMemoryProjectPolicy, McpControlPlane, McpToolRequest,
    ProjectAccess, ProjectPolicyLimits, ToolKind, ToolPolicy, ToolServiceGateway,
    ToolServiceOutput,
};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value, json};
use sha2::Sha256;
use uuid::Uuid;

type HmacSha256 = Hmac<Sha256>;

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

#[derive(Clone, Copy, Debug)]
enum GatewayMode {
    Valid,
    Unavailable,
    InvalidOutput,
    WrongRequestCorrelation,
    WrongProjectCorrelation,
}

#[derive(Debug)]
struct FixtureGateway {
    outputs: BTreeMap<ToolKind, Value>,
    calls: Arc<AtomicUsize>,
    mode: GatewayMode,
}

impl ToolServiceGateway for FixtureGateway {
    fn dispatch(&mut self, call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        if matches!(self.mode, GatewayMode::Unavailable) {
            return Err(GatewayError::Unavailable);
        }
        let mut output = self
            .outputs
            .get(&call.tool())
            .cloned()
            .unwrap_or_else(|| panic!("missing fixture output for {}", call.tool().name()));
        match self.mode {
            GatewayMode::Valid | GatewayMode::Unavailable => {}
            GatewayMode::InvalidOutput => {
                output
                    .as_object_mut()
                    .unwrap_or_else(|| panic!("fixture output is not an object"))
                    .insert(
                        "unexpected_property".to_owned(),
                        Value::String("SENSITIVE_BACKEND_VALUE".to_owned()),
                    );
            }
            GatewayMode::WrongRequestCorrelation => {
                output
                    .as_object_mut()
                    .unwrap_or_else(|| panic!("fixture output is not an object"))
                    .insert(
                        "request_id".to_owned(),
                        Value::String("req_different01".to_owned()),
                    );
            }
            GatewayMode::WrongProjectCorrelation => {
                output
                    .as_object_mut()
                    .unwrap_or_else(|| panic!("fixture output is not an object"))
                    .insert(
                        "project_id".to_owned(),
                        Value::String("prj_different01".to_owned()),
                    );
            }
        }
        Ok(ToolServiceOutput::new(output))
    }
}

#[derive(Debug)]
struct CountingPolicy {
    inner: InMemoryProjectPolicy,
    calls: Arc<AtomicUsize>,
}

impl ToolPolicy for CountingPolicy {
    fn authorize(
        &self,
        context: &AuthContext,
        tool: ToolKind,
        arguments: &Value,
    ) -> Result<(), mcp_control_plane::PolicyError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        self.inner.authorize(context, tool, arguments)
    }
}

#[derive(Clone, Copy)]
enum PolicyBinding {
    SameTenantOwner,
    SameTenantReader,
    CrossTenant,
}

struct Fixture {
    control: McpControlPlane<CountingPolicy, FixtureGateway>,
    bearer: String,
    inputs: BTreeMap<ToolKind, Value>,
    policy_calls: Arc<AtomicUsize>,
    gateway_calls: Arc<AtomicUsize>,
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
    #[serde(skip_serializing_if = "Option::is_none")]
    service_id: Option<String>,
}

fn tenant(value: u128) -> TenantId {
    TenantId::new(Uuid::from_u128(value)).unwrap_or_else(|error| panic!("tenant fixture: {error}"))
}

fn fixture(
    gateway_mode: GatewayMode,
    token_scopes: &[AuthScope],
    policy_binding: PolicyBinding,
) -> Fixture {
    let tenant_id = tenant(1);
    let mut middleware = AuthMiddleware::new(
        RESOURCE,
        METADATA,
        60,
        AuthRegistryLimits::product_maximums(),
    )
    .unwrap_or_else(|error| panic!("middleware fixture: {error}"));
    middleware
        .register_local_hmac_key(ISSUER, KEY_ID, SECRET, NOW - 600, NOW + 7_200)
        .unwrap_or_else(|error| panic!("key fixture: {error}"));
    let subject = middleware
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
        jti: "user-token-0001".to_owned(),
        scope: token_scopes
            .iter()
            .map(|scope| scope.as_str())
            .collect::<Vec<_>>()
            .join(" "),
        token_kind: "user".to_owned(),
        tenant_id,
        service_id: None,
    };
    let token = sign(&claims, "at+jwt");

    let mut project_policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
    let policy_tenant = match policy_binding {
        PolicyBinding::SameTenantOwner | PolicyBinding::SameTenantReader => tenant_id,
        PolicyBinding::CrossTenant => tenant(2),
    };
    project_policy
        .register_project(PROJECT_ID, policy_tenant)
        .unwrap_or_else(|error| panic!("project fixture: {error}"));
    let access = match policy_binding {
        PolicyBinding::SameTenantReader => ProjectAccess::Reader,
        PolicyBinding::SameTenantOwner | PolicyBinding::CrossTenant => ProjectAccess::Owner,
    };
    project_policy
        .register_membership(PROJECT_ID, subject, access)
        .unwrap_or_else(|error| panic!("membership fixture: {error}"));

    let (inputs, outputs) = catalog_fixtures();
    let policy_calls = Arc::new(AtomicUsize::new(0));
    let gateway_calls = Arc::new(AtomicUsize::new(0));
    let control = McpControlPlane::new(
        middleware,
        CountingPolicy {
            inner: project_policy,
            calls: Arc::clone(&policy_calls),
        },
        FixtureGateway {
            outputs,
            calls: Arc::clone(&gateway_calls),
            mode: gateway_mode,
        },
    )
    .unwrap_or_else(|error| panic!("control-plane fixture: {error}"));
    Fixture {
        control,
        bearer: format!("Bearer {token}"),
        inputs,
        policy_calls,
        gateway_calls,
    }
}

fn request(fixture: &Fixture, tool: ToolKind) -> McpToolRequest {
    let arguments = fixture
        .inputs
        .get(&tool)
        .unwrap_or_else(|| panic!("missing fixture input for {}", tool.name()));
    McpToolRequest::new(
        tool.name(),
        fixture.bearer.clone(),
        serde_json::to_vec(arguments)
            .unwrap_or_else(|error| panic!("serialize fixture input: {error}")),
        NOW,
    )
}

fn sign(claims: &Claims, token_type: &str) -> String {
    let header = URL_SAFE_NO_PAD.encode(
        serde_json::to_vec(&json!({"alg": "HS256", "kid": KEY_ID, "typ": token_type}))
            .unwrap_or_else(|error| panic!("serialize token header: {error}")),
    );
    let claims = URL_SAFE_NO_PAD.encode(
        serde_json::to_vec(claims)
            .unwrap_or_else(|error| panic!("serialize token claims: {error}")),
    );
    let signing_input = format!("{header}.{claims}");
    let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(SECRET)
        .unwrap_or_else(|error| panic!("signing fixture: {error}"));
    signer.update(signing_input.as_bytes());
    format!(
        "{signing_input}.{}",
        URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
    )
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

fn catalog_fixtures() -> (BTreeMap<ToolKind, Value>, BTreeMap<ToolKind, Value>) {
    let catalog: FixtureCatalog = serde_json::from_str(include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../protocol/mcp/p15-public-tools-v1.json"
    )))
    .unwrap_or_else(|error| panic!("parse fixture catalog: {error}"));
    let mut inputs = BTreeMap::new();
    let mut outputs = BTreeMap::new();
    for descriptor in catalog.tools {
        let tool = ToolKind::parse(&descriptor.name)
            .unwrap_or_else(|| panic!("unknown fixture tool: {}", descriptor.name));
        inputs.insert(
            tool,
            synthesize(&descriptor.input_schema, &descriptor.input_schema),
        );
        outputs.insert(
            tool,
            synthesize(&descriptor.output_schema, &descriptor.output_schema),
        );
    }
    (inputs, outputs)
}

fn synthesize(node: &Value, root: &Value) -> Value {
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
            .unwrap_or_else(|| panic!("empty enum fixture"));
    }
    if let Some(branches) = node.get("oneOf").and_then(Value::as_array) {
        return synthesize(
            branches
                .first()
                .unwrap_or_else(|| panic!("empty oneOf fixture")),
            root,
        );
    }
    match node.get("type").and_then(Value::as_str) {
        Some("object") => {
            let properties = node
                .get("properties")
                .and_then(Value::as_object)
                .unwrap_or_else(|| panic!("object schema without properties"));
            let required = node
                .get("required")
                .and_then(Value::as_array)
                .unwrap_or_else(|| panic!("object schema without required"));
            let mut result = Map::new();
            for key in required {
                let key = key
                    .as_str()
                    .unwrap_or_else(|| panic!("non-string required property"));
                let schema = properties
                    .get(key)
                    .unwrap_or_else(|| panic!("missing required property schema: {key}"));
                result.insert(key.to_owned(), synthesize(schema, root));
            }
            Value::Object(result)
        }
        Some("array") => {
            let count = node.get("minItems").and_then(Value::as_u64).unwrap_or(0);
            let item = node
                .get("items")
                .unwrap_or_else(|| panic!("array schema without items"));
            Value::Array((0..count).map(|_| synthesize(item, root)).collect())
        }
        Some("boolean") => Value::Bool(false),
        Some("integer") => node.get("minimum").cloned().unwrap_or_else(|| json!(0)),
        Some("number") => node.get("minimum").cloned().unwrap_or_else(|| json!(0)),
        Some("null") => Value::Null,
        Some("string") => string_sample(node),
        other => panic!("unsupported fixture schema node: {other:?}; root={root}"),
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
        _ => panic!("unsupported fixture reference: {reference}"),
    };
    Value::String(value.to_owned())
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
    Value::String(value)
}

#[test]
fn all_eighteen_tools_follow_the_full_success_boundary() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    assert_eq!(fixture.control.tool_count(), 18);
    for tool in ToolKind::ALL {
        let request = request(&fixture, tool);
        let result = fixture.control.handle(request);
        assert!(!result.is_error(), "{}: {:?}", tool.name(), result);
        assert_eq!(
            result
                .structured_content()
                .get("request_id")
                .and_then(Value::as_str),
            Some("req_example01")
        );
    }
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 18);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 18);
}

#[test]
fn authentication_precedes_json_parsing_and_returns_discovery_challenge() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let result = fixture.control.handle(McpToolRequest::new(
        "project_open",
        "Bearer invalid.token.value",
        b"not-json".to_vec(),
        NOW,
    ));
    assert_eq!(result.error_code(), Some("AUTHENTICATION_FAILED"));
    let fallback_request_id = result
        .structured_content()
        .get("request_id")
        .and_then(Value::as_str)
        .unwrap_or_else(|| panic!("missing server correlation id"));
    assert!(fallback_request_id.starts_with("req_server_"));
    assert_eq!(fallback_request_id.len(), 43);
    assert_eq!(
        result.structured_content(),
        &json!({
            "schema_version": "hwpx-agent.error/v2",
            "request_id": fallback_request_id,
            "error_code": "AUTHENTICATION_FAILED",
            "category": "security",
            "safe_message": "Authentication is required for this tool.",
            "retryable": false,
            "stage": "authenticate",
            "details": {},
            "recovery": [{"action": "reauthenticate"}],
        })
    );
    assert_eq!(
        result.meta().get("hwpx/requestId").and_then(Value::as_str),
        Some(fallback_request_id)
    );
    assert_eq!(
        result
            .meta()
            .get("hwpx/errorCatalogSha256")
            .and_then(Value::as_str),
        Some(mcp_control_plane::ERROR_CATALOG_SHA256)
    );
    assert!(result.meta().get("mcp/www_authenticate").is_some());
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 0);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 0);
}

#[test]
fn duplicate_json_keys_fail_before_policy_or_dispatch() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let result = fixture.control.handle(McpToolRequest::new(
        "project_open",
        fixture.bearer.clone(),
        br#"{"request_id":"req_example01","request_id":"req_example01"}"#.to_vec(),
        NOW,
    ));
    assert_eq!(result.error_code(), Some("TOOL_ARGUMENTS_MALFORMED"));
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 0);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 0);
}

#[test]
fn schema_unknown_fields_fail_before_policy_or_dispatch() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let mut arguments = fixture.inputs[&ToolKind::ProjectOpen].clone();
    arguments
        .as_object_mut()
        .unwrap_or_else(|| panic!("fixture input is not an object"))
        .insert("unexpected_property".to_owned(), Value::Bool(true));
    let result = fixture.control.handle(McpToolRequest::new(
        "project_open",
        fixture.bearer.clone(),
        serde_json::to_vec(&arguments)
            .unwrap_or_else(|error| panic!("serialize invalid fixture: {error}")),
        NOW,
    ));
    assert_eq!(result.error_code(), Some("TOOL_INPUT_SCHEMA_INVALID"));
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 0);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 0);
}

#[test]
fn descriptor_scopes_are_enforced_before_policy() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &[AuthScope::ProjectRead],
        PolicyBinding::SameTenantOwner,
    );
    let request = request(&fixture, ToolKind::DocumentCreate);
    let result = fixture.control.handle(request);
    assert_eq!(result.error_code(), Some("AUTHENTICATION_FAILED"));
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 0);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 0);
}

#[test]
fn cross_tenant_project_is_indistinguishable_from_missing() {
    let mut fixture = fixture(GatewayMode::Valid, &ALL_SCOPES, PolicyBinding::CrossTenant);
    let request = request(&fixture, ToolKind::ProjectOpen);
    let result = fixture.control.handle(request);
    assert_eq!(result.error_code(), Some("RESOURCE_NOT_FOUND"));
    assert_eq!(
        result
            .structured_content()
            .get("request_id")
            .and_then(Value::as_str),
        Some("req_example01")
    );
    assert_eq!(
        result
            .structured_content()
            .get("stage")
            .and_then(Value::as_str),
        Some("policy")
    );
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 1);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 0);
}

#[test]
fn project_reader_cannot_call_a_state_creating_tool() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantReader,
    );
    let request = request(&fixture, ToolKind::DocumentInspect);
    let result = fixture.control.handle(request);
    assert_eq!(result.error_code(), Some("POLICY_DENIED"));
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 1);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 0);
}

#[test]
fn gateway_is_called_once_and_unavailability_is_safely_mapped() {
    let mut fixture = fixture(
        GatewayMode::Unavailable,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let request = request(&fixture, ToolKind::ProjectOpen);
    let result = fixture.control.handle(request);
    assert_eq!(result.error_code(), Some("SERVICE_UNAVAILABLE"));
    assert_eq!(
        result
            .structured_content()
            .get("retryable")
            .and_then(Value::as_bool),
        Some(true)
    );
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 1);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 1);
}

#[test]
fn invalid_gateway_output_is_never_exposed() {
    let mut fixture = fixture(
        GatewayMode::InvalidOutput,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let request = request(&fixture, ToolKind::ProjectOpen);
    let result = fixture.control.handle(request);
    assert_eq!(result.error_code(), Some("TOOL_OUTPUT_SCHEMA_INVALID"));
    let serialized =
        serde_json::to_string(&result).unwrap_or_else(|error| panic!("serialize result: {error}"));
    assert!(!serialized.contains("SENSITIVE_BACKEND_VALUE"));
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 1);
}

#[test]
fn output_request_correlation_is_mandatory() {
    let mut fixture = fixture(
        GatewayMode::WrongRequestCorrelation,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let request = request(&fixture, ToolKind::ProjectOpen);
    let result = fixture.control.handle(request);
    assert_eq!(
        result.error_code(),
        Some("TOOL_RESULT_CORRELATION_MISMATCH")
    );
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 1);
}

#[test]
fn output_project_correlation_is_mandatory_when_both_sides_name_it() {
    let mut fixture = fixture(
        GatewayMode::WrongProjectCorrelation,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let request = request(&fixture, ToolKind::ProjectOpen);
    let result = fixture.control.handle(request);
    assert_eq!(
        result.error_code(),
        Some("TOOL_RESULT_CORRELATION_MISMATCH")
    );
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 1);
}

#[test]
fn service_token_shape_is_rejected_at_the_public_user_boundary() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let service_shaped = Claims {
        iss: ISSUER.to_owned(),
        sub: "oidc-user-42".to_owned(),
        aud: RESOURCE.to_owned(),
        exp: NOW + 120,
        nbf: NOW - 10,
        iat: NOW - 10,
        jti: "service-token-0001".to_owned(),
        scope: "project.read".to_owned(),
        token_kind: "service".to_owned(),
        tenant_id: tenant(1),
        service_id: Some("oidc-user-42".to_owned()),
    };
    fixture.bearer = format!("Bearer {}", sign(&service_shaped, "hwpx-service+jwt"));
    let request = request(&fixture, ToolKind::ProjectOpen);
    let result = fixture.control.handle(request);
    assert_eq!(result.error_code(), Some("AUTHENTICATION_FAILED"));
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 0);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 0);
}

#[test]
fn success_result_has_bounded_mcp_shape_and_no_bearer() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let request = request(&fixture, ToolKind::ProjectOpen);
    let result = fixture.control.handle(request);
    assert!(!result.is_error());
    assert_eq!(
        result
            .meta()
            .get("hwpx/catalogSha256")
            .and_then(Value::as_str),
        Some(mcp_control_plane::CATALOG_SHA256)
    );
    assert_eq!(
        result
            .meta()
            .get("hwpx/errorCatalogSha256")
            .and_then(Value::as_str),
        Some(mcp_control_plane::ERROR_CATALOG_SHA256)
    );
    assert!(result.content_text().len() < 128);
    let serialized = serde_json::to_string(&result)
        .unwrap_or_else(|error| panic!("serialize success result: {error}"));
    assert!(serialized.contains("structuredContent"));
    assert!(serialized.contains("\"isError\":false"));
    assert!(!serialized.contains(&fixture.bearer));
}

#[test]
fn request_size_and_unknown_tools_have_no_downstream_effect() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let oversized = fixture.control.handle(McpToolRequest::new(
        "project_open",
        fixture.bearer.clone(),
        vec![b' '; 262_145],
        NOW,
    ));
    assert_eq!(oversized.error_code(), Some("TOOL_REQUEST_TOO_LARGE"));
    let unknown = fixture.control.handle(McpToolRequest::new(
        "raw_com_action",
        fixture.bearer.clone(),
        b"{}".to_vec(),
        NOW,
    ));
    assert_eq!(unknown.error_code(), Some("TOOL_UNKNOWN"));
    assert_eq!(fixture.policy_calls.load(Ordering::SeqCst), 0);
    assert_eq!(fixture.gateway_calls.load(Ordering::SeqCst), 0);
}

#[test]
fn request_and_result_debug_output_redacts_bearer_and_arguments() {
    let mut fixture = fixture(
        GatewayMode::Valid,
        &ALL_SCOPES,
        PolicyBinding::SameTenantOwner,
    );
    let private_request = McpToolRequest::new(
        "TOP_SECRET_TOOL_NAME",
        "Bearer TOP_SECRET_TOKEN",
        br#"{"intent":"PRIVATE_DOCUMENT_TEXT"}"#.to_vec(),
        NOW,
    );
    let request_debug = format!("{private_request:?}");
    assert!(!request_debug.contains("TOP_SECRET_TOOL_NAME"));
    assert!(!request_debug.contains("TOP_SECRET_TOKEN"));
    assert!(!request_debug.contains("PRIVATE_DOCUMENT_TEXT"));
    let valid_request = request(&fixture, ToolKind::ProjectOpen);
    let result = fixture.control.handle(valid_request);
    let result_debug = format!("{result:?}");
    assert!(!result_debug.contains("req_example01"));
    assert!(!result_debug.contains("prj_example01"));
}

#[test]
fn policy_registration_is_bounded_and_conflict_safe() {
    let limits =
        ProjectPolicyLimits::new(1, 1).unwrap_or_else(|error| panic!("policy limits: {error}"));
    let mut policy = InMemoryProjectPolicy::new(limits);
    policy
        .register_project(PROJECT_ID, tenant(1))
        .unwrap_or_else(|error| panic!("register project: {error}"));
    assert!(policy.register_project(PROJECT_ID, tenant(1)).is_err());
    assert!(policy.register_project("prj_another01", tenant(1)).is_err());
}
