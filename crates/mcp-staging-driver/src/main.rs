#![forbid(unsafe_code)]

use std::collections::BTreeMap;
use std::io::{self, BufRead as _, Write as _};

use artifact_service::TenantId;
use auth_middleware::{AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use mcp_control_plane::{
    AuthorizedToolCall, GatewayError, InMemoryProjectPolicy, McpControlPlane, McpToolRequest,
    ProjectAccess, ProjectPolicyLimits, ToolKind, ToolServiceGateway, ToolServiceOutput,
};
use serde::Deserialize;
use serde_json::{Map, Value, json};
use thiserror::Error;
use uuid::Uuid;
use zeroize::Zeroizing;

const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const KEY_ID: &str = "local-key-01";
const SUBJECT: &str = "p15-inspector-user";
const PROJECT_ID: &str = "prj_example01";
const SECRET_ENV: &str = "HWPX_AGENT_STAGING_HMAC_KEY_B64";
const MAX_DRIVER_REQUEST_BYTES: usize = 300_000;
const MAX_SYNTHESIS_DEPTH: usize = 64;

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

#[derive(Clone, Copy, Deserialize)]
#[serde(rename_all = "snake_case")]
enum DriverMode {
    Auth,
    Tool,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct DriverRequest {
    #[serde(rename = "driver_request_id")]
    correlation_id: u64,
    mode: DriverMode,
    authorization_header: String,
    now_unix_seconds: u64,
    #[serde(default)]
    tool_name: Option<String>,
    #[serde(default)]
    arguments: Option<Value>,
}

#[derive(Deserialize)]
struct FixtureCatalog {
    tools: Vec<FixtureTool>,
}

#[derive(Deserialize)]
struct FixtureTool {
    name: String,
    #[serde(rename = "outputSchema")]
    output_schema: Value,
}

#[derive(Error, Debug)]
enum DriverError {
    #[error("request rejected")]
    Request,
    #[error("configuration rejected")]
    Configuration,
    #[error("control-plane initialization rejected")]
    ControlPlane,
    #[error("gateway fixture rejected")]
    Gateway,
    #[error("response serialization rejected")]
    Serialization,
}

struct AuthSetup {
    middleware: AuthMiddleware,
    tenant_id: TenantId,
    subject: artifact_service::SubjectDigest,
}

struct StagingGateway {
    outputs: BTreeMap<ToolKind, Value>,
}

struct DriverState {
    auth_probe: AuthMiddleware,
    control: McpControlPlane<InMemoryProjectPolicy, StagingGateway>,
}

impl std::fmt::Debug for StagingGateway {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("StagingGateway")
            .field("output_count", &self.outputs.len())
            .finish()
    }
}

impl ToolServiceGateway for StagingGateway {
    fn dispatch(&mut self, call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError> {
        let mut output = self
            .outputs
            .get(&call.tool())
            .cloned()
            .ok_or(GatewayError::Unavailable)?;
        let object = output.as_object_mut().ok_or(GatewayError::Unavailable)?;
        for field in [
            "request_id",
            "project_id",
            "job_id",
            "revision_id",
            "release_label",
        ] {
            if object.contains_key(field) {
                if field == "request_id" {
                    object.insert(
                        field.to_owned(),
                        Value::String(call.request_id().to_owned()),
                    );
                } else if let Some(value) = call.arguments().get(field).and_then(Value::as_str) {
                    object.insert(field.to_owned(), Value::String(value.to_owned()));
                }
            }
        }
        Ok(ToolServiceOutput::new(output))
    }
}

fn main() {
    if run().is_err() {
        eprintln!("mcp-staging-driver: request failed closed");
        std::process::exit(1);
    }
}

fn run() -> Result<(), DriverError> {
    let secret = read_secret()?;
    let stdin = io::stdin();
    let mut reader = io::BufReader::new(stdin.lock());
    let mut state: Option<DriverState> = None;
    loop {
        let Some(request_bytes) = read_bounded_line(&mut reader)? else {
            return Ok(());
        };
        let request: DriverRequest =
            serde_json::from_slice(&request_bytes).map_err(|_| DriverError::Request)?;
        let request_id = request.correlation_id;
        let state = match &mut state {
            Some(state) => state,
            None => state.insert(DriverState::new(&secret, request.now_unix_seconds)?),
        };
        let response = match state.handle(request) {
            Ok(result) => json!({
                "driver_request_id": request_id,
                "ok": true,
                "result": result,
            }),
            Err(_) => json!({
                "driver_request_id": request_id,
                "ok": false,
                "error": "request_rejected",
            }),
        };
        write_json(&response)?;
    }
}

impl DriverState {
    fn new(secret: &[u8], now_unix_seconds: u64) -> Result<Self, DriverError> {
        let auth_probe = build_auth(secret.to_vec(), now_unix_seconds)?.middleware;
        let setup = build_auth(secret.to_vec(), now_unix_seconds)?;
        let gateway = StagingGateway {
            outputs: catalog_outputs()?,
        };
        let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
        policy
            .register_project(PROJECT_ID, setup.tenant_id)
            .map_err(|_| DriverError::ControlPlane)?;
        policy
            .register_membership(PROJECT_ID, setup.subject, ProjectAccess::Owner)
            .map_err(|_| DriverError::ControlPlane)?;
        let control = McpControlPlane::new(setup.middleware, policy, gateway)
            .map_err(|_| DriverError::ControlPlane)?;
        Ok(Self {
            auth_probe,
            control,
        })
    }

    fn handle(&mut self, request: DriverRequest) -> Result<Value, DriverError> {
        if request.authorization_header.len() > auth_middleware::MAX_BEARER_TOKEN_BYTES + 7 {
            return Err(DriverError::Request);
        }
        let authorization_header = Zeroizing::new(request.authorization_header);
        match request.mode {
            DriverMode::Auth => {
                if request.tool_name.is_some() || request.arguments.is_some() {
                    return Err(DriverError::Request);
                }
                self.auth_probe
                    .authenticate_public_mcp(
                        &authorization_header,
                        request.now_unix_seconds,
                        ALL_SCOPES,
                    )
                    .map_err(|_| DriverError::Request)?;
                Ok(json!({"authenticated": true}))
            }
            DriverMode::Tool => {
                let tool_name = request.tool_name.ok_or(DriverError::Request)?;
                let arguments = request.arguments.ok_or(DriverError::Request)?;
                let arguments_json =
                    serde_json::to_vec(&arguments).map_err(|_| DriverError::Serialization)?;
                let result = self.control.handle(McpToolRequest::new(
                    tool_name,
                    authorization_header.to_string(),
                    arguments_json,
                    request.now_unix_seconds,
                ));
                serde_json::to_value(result).map_err(|_| DriverError::Serialization)
            }
        }
    }
}

fn read_bounded_line(
    reader: &mut impl io::BufRead,
) -> Result<Option<Zeroizing<Vec<u8>>>, DriverError> {
    let mut bytes = Zeroizing::new(Vec::with_capacity(16_384));
    let mut limited = io::Read::take(&mut *reader, (MAX_DRIVER_REQUEST_BYTES + 1) as u64);
    let count = limited
        .read_until(b'\n', &mut bytes)
        .map_err(|_| DriverError::Request)?;
    if count == 0 {
        return Ok(None);
    }
    if bytes.len() > MAX_DRIVER_REQUEST_BYTES || bytes.last() != Some(&b'\n') {
        return Err(DriverError::Request);
    }
    bytes.pop();
    if bytes.last() == Some(&b'\r') {
        bytes.pop();
    }
    if bytes.is_empty() {
        return Err(DriverError::Request);
    }
    Ok(Some(bytes))
}

fn read_secret() -> Result<Zeroizing<Vec<u8>>, DriverError> {
    let encoded =
        Zeroizing::new(std::env::var(SECRET_ENV).map_err(|_| DriverError::Configuration)?);
    let secret = URL_SAFE_NO_PAD
        .decode(encoded.as_bytes())
        .map_err(|_| DriverError::Configuration)?;
    if secret.len() != 32 {
        return Err(DriverError::Configuration);
    }
    Ok(Zeroizing::new(secret))
}

fn build_auth(secret: Vec<u8>, now_unix_seconds: u64) -> Result<AuthSetup, DriverError> {
    let active_until = now_unix_seconds
        .checked_add(3_600)
        .ok_or(DriverError::Configuration)?;
    let active_from = now_unix_seconds.saturating_sub(120);
    let tenant_id = TenantId::new(Uuid::from_u128(1)).map_err(|_| DriverError::Configuration)?;
    let mut middleware = AuthMiddleware::new(
        RESOURCE,
        METADATA,
        60,
        AuthRegistryLimits::product_maximums(),
    )
    .map_err(|_| DriverError::Configuration)?;
    middleware
        .register_local_hmac_key(ISSUER, KEY_ID, secret, active_from, active_until)
        .map_err(|_| DriverError::Configuration)?;
    let grant = PrincipalGrant::new(
        tenant_id,
        TenantRole::Owner,
        ALL_SCOPES,
        active_from,
        active_until,
    )
    .map_err(|_| DriverError::Configuration)?;
    let subject = middleware
        .register_user(ISSUER, SUBJECT, grant)
        .map_err(|_| DriverError::Configuration)?;
    Ok(AuthSetup {
        middleware,
        tenant_id,
        subject,
    })
}

fn catalog_outputs() -> Result<BTreeMap<ToolKind, Value>, DriverError> {
    let catalog: FixtureCatalog = serde_json::from_str(include_str!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../protocol/mcp/p15-public-tools-v1.json"
    )))
    .map_err(|_| DriverError::Gateway)?;
    let mut outputs = BTreeMap::new();
    for descriptor in catalog.tools {
        let tool = ToolKind::parse(&descriptor.name).ok_or(DriverError::Gateway)?;
        let output = synthesize(&descriptor.output_schema, 0)?;
        if outputs.insert(tool, output).is_some() {
            return Err(DriverError::Gateway);
        }
    }
    if outputs.len() != ToolKind::ALL.len() {
        return Err(DriverError::Gateway);
    }
    Ok(outputs)
}

fn synthesize(node: &Value, depth: usize) -> Result<Value, DriverError> {
    if depth > MAX_SYNTHESIS_DEPTH {
        return Err(DriverError::Gateway);
    }
    if let Some(reference) = node.get("$ref").and_then(Value::as_str) {
        return reference_sample(reference);
    }
    if let Some(value) = node.get("const") {
        return Ok(value.clone());
    }
    if let Some(values) = node.get("enum").and_then(Value::as_array) {
        return values.first().cloned().ok_or(DriverError::Gateway);
    }
    if let Some(branches) = node.get("oneOf").and_then(Value::as_array) {
        let first = branches.first().ok_or(DriverError::Gateway)?;
        return synthesize(first, depth + 1);
    }
    match node.get("type").and_then(Value::as_str) {
        Some("object") => {
            let properties = node
                .get("properties")
                .and_then(Value::as_object)
                .ok_or(DriverError::Gateway)?;
            let required = node
                .get("required")
                .and_then(Value::as_array)
                .ok_or(DriverError::Gateway)?;
            let mut result = Map::new();
            for key in required {
                let key = key.as_str().ok_or(DriverError::Gateway)?;
                let schema = properties.get(key).ok_or(DriverError::Gateway)?;
                result.insert(key.to_owned(), synthesize(schema, depth + 1)?);
            }
            Ok(Value::Object(result))
        }
        Some("array") => {
            let count = node.get("minItems").and_then(Value::as_u64).unwrap_or(0);
            let count = usize::try_from(count).map_err(|_| DriverError::Gateway)?;
            if count > 128 {
                return Err(DriverError::Gateway);
            }
            let item = node.get("items").ok_or(DriverError::Gateway)?;
            (0..count)
                .map(|_| synthesize(item, depth + 1))
                .collect::<Result<Vec<_>, _>>()
                .map(Value::Array)
        }
        Some("boolean") => Ok(Value::Bool(false)),
        Some("integer" | "number") => Ok(node.get("minimum").cloned().unwrap_or_else(|| json!(0))),
        Some("null") => Ok(Value::Null),
        Some("string") => Ok(string_sample(node)),
        _ => Err(DriverError::Gateway),
    }
}

fn reference_sample(reference: &str) -> Result<Value, DriverError> {
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
        _ => return Err(DriverError::Gateway),
    };
    Ok(Value::String(value.to_owned()))
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

fn write_json(value: &impl serde::Serialize) -> Result<(), DriverError> {
    let bytes = serde_json::to_vec(value).map_err(|_| DriverError::Serialization)?;
    let mut stdout = io::stdout().lock();
    stdout
        .write_all(&bytes)
        .and_then(|()| stdout.write_all(b"\n"))
        .and_then(|()| stdout.flush())
        .map_err(|_| DriverError::Serialization)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn catalog_synthesizes_one_output_for_every_public_tool() {
        let outputs = catalog_outputs().unwrap_or_else(|error| panic!("catalog: {error}"));
        assert_eq!(outputs.len(), 18);
        for tool in ToolKind::ALL {
            let output = outputs
                .get(&tool)
                .unwrap_or_else(|| panic!("missing output for {}", tool.name()));
            assert!(output.is_object(), "{}", tool.name());
        }
    }

    #[test]
    fn unknown_reference_fails_closed() {
        let schema = json!({"$ref": "#/$defs/not_allowed"});
        assert!(synthesize(&schema, 0).is_err());
    }

    #[test]
    fn excessive_synthesis_depth_fails_closed() {
        assert!(synthesize(&json!({"type": "null"}), MAX_SYNTHESIS_DEPTH + 1).is_err());
    }
}
