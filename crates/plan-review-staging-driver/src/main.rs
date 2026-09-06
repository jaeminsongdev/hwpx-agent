#![forbid(unsafe_code)]

use std::io::{self, BufRead as _, Write as _};

use artifact_service::TenantId;
use auth_middleware::{AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use mcp_control_plane::{
    DurablePlanKeyring, DurablePlanReviewEvidenceKeyring, InMemoryProjectPolicy,
    LocalPostgresPlanReviewEvidenceConfig, LocalPostgresPlanReviewEvidenceRepository,
    LocalPostgresPlanSourceConfig, LocalPostgresPlanSourceRepository,
    LocalPostgresStoredPlanConfig, LocalPostgresStoredPlanRegistry, PlanReviewRenderRequest,
    PlanReviewRenderer, ProjectAccess, ProjectPolicyLimits, StoredPlanLimits,
};
use serde::Deserialize;
use serde_json::{Value, json};
use thiserror::Error;
use uuid::Uuid;
use zeroize::Zeroizing;

const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const KEY_ID: &str = "local-key-01";
const RENDER_TOOL: &str = "render_plan_review_widget";
const MAX_DRIVER_REQUEST_BYTES: usize = 300_000;
const MAX_PUBLIC_VALUE_BYTES: usize = 2_048;

const HMAC_KEY_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_HMAC_KEY_B64";
const TENANT_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_TENANT_ID";
const PROJECT_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PROJECT_ID";
const SUBJECT_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_SUBJECT";
const PG_PORT_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PG_PORT";
const PG_DATABASE_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PG_DATABASE";
const SOURCE_USER_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_SOURCE_PG_USER";
const SOURCE_PASSWORD_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_SOURCE_PG_PASSWORD";
const PLAN_USER_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PLAN_PG_USER";
const PLAN_PASSWORD_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PLAN_PG_PASSWORD";
const REVIEW_USER_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PG_USER";
const REVIEW_PASSWORD_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PG_PASSWORD";
const PLAN_ACTIVE_REF_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PLAN_ACTIVE_KEY_REF";
const PLAN_ACTIVE_KEY_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PLAN_ACTIVE_KEY_B64";
const PLAN_PREVIOUS_REF_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PLAN_PREVIOUS_KEY_REF";
const PLAN_PREVIOUS_KEY_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_PLAN_PREVIOUS_KEY_B64";
const EVIDENCE_ACTIVE_REF_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_ACTIVE_KEY_REF";
const EVIDENCE_ACTIVE_KEY_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_ACTIVE_KEY_B64";
const EVIDENCE_PREVIOUS_REF_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PREVIOUS_KEY_REF";
const EVIDENCE_PREVIOUS_KEY_ENV: &str = "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PREVIOUS_KEY_B64";

#[derive(Clone, Copy, Deserialize)]
#[serde(rename_all = "snake_case")]
enum DriverMode {
    Ready,
    Auth,
    PlanReview,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct DriverRequest {
    #[serde(rename = "driver_request_id")]
    correlation_id: u64,
    mode: DriverMode,
    now_unix_seconds: u64,
    #[serde(default)]
    authorization_header: Option<String>,
    #[serde(default)]
    tool_name: Option<String>,
    #[serde(default)]
    arguments: Option<Value>,
}

#[derive(Error, Debug)]
enum DriverError {
    #[error("request rejected")]
    Request,
    #[error("configuration rejected")]
    Configuration,
    #[error("database admission rejected")]
    Database,
    #[error("renderer rejected")]
    Renderer,
    #[error("response serialization rejected")]
    Serialization,
}

struct KeyMaterial {
    active_reference: String,
    active_key: Zeroizing<[u8; 32]>,
    previous: Option<(String, Zeroizing<[u8; 32]>)>,
}

impl KeyMaterial {
    fn from_environment(
        active_reference_env: &str,
        active_key_env: &str,
        previous_reference_env: &str,
        previous_key_env: &str,
    ) -> Result<Self, DriverError> {
        let active_reference = public_environment(active_reference_env)?;
        let active_key = key_environment(active_key_env)?;
        let previous_reference = optional_public_environment(previous_reference_env)?;
        let previous_key = optional_key_environment(previous_key_env)?;
        let previous = match (previous_reference, previous_key) {
            (None, None) => None,
            (Some(reference), Some(key)) if reference != active_reference => Some((reference, key)),
            _ => return Err(DriverError::Configuration),
        };
        Ok(Self {
            active_reference,
            active_key,
            previous,
        })
    }

    fn entries(&self) -> Vec<(String, [u8; 32])> {
        let mut entries = vec![(self.active_reference.clone(), *self.active_key)];
        if let Some((reference, key)) = &self.previous {
            entries.push((reference.clone(), **key));
        }
        entries
    }
}

struct RuntimeConfig {
    hmac_key: Zeroizing<Vec<u8>>,
    tenant: TenantId,
    project_id: String,
    subject: String,
    port: u16,
    database: String,
    source_user: String,
    source_password: Zeroizing<String>,
    plan_user: String,
    plan_password: Zeroizing<String>,
    evidence_user: String,
    evidence_password: Zeroizing<String>,
    plan_keys: KeyMaterial,
    evidence_keys: KeyMaterial,
}

impl RuntimeConfig {
    fn from_environment() -> Result<Self, DriverError> {
        let hmac_key = decoded_environment(HMAC_KEY_ENV)?;
        if hmac_key.len() != 32 || hmac_key.iter().all(|byte| *byte == 0) {
            return Err(DriverError::Configuration);
        }
        let tenant_uuid = Uuid::parse_str(&public_environment(TENANT_ENV)?)
            .map_err(|_| DriverError::Configuration)?;
        let tenant = TenantId::new(tenant_uuid).map_err(|_| DriverError::Configuration)?;
        let port = public_environment(PG_PORT_ENV)?
            .parse::<u16>()
            .map_err(|_| DriverError::Configuration)?;
        if port == 0 {
            return Err(DriverError::Configuration);
        }
        Ok(Self {
            hmac_key,
            tenant,
            project_id: public_environment(PROJECT_ENV)?,
            subject: public_environment(SUBJECT_ENV)?,
            port,
            database: public_environment(PG_DATABASE_ENV)?,
            source_user: public_environment(SOURCE_USER_ENV)?,
            source_password: secret_environment(SOURCE_PASSWORD_ENV)?,
            plan_user: public_environment(PLAN_USER_ENV)?,
            plan_password: secret_environment(PLAN_PASSWORD_ENV)?,
            evidence_user: public_environment(REVIEW_USER_ENV)?,
            evidence_password: secret_environment(REVIEW_PASSWORD_ENV)?,
            plan_keys: KeyMaterial::from_environment(
                PLAN_ACTIVE_REF_ENV,
                PLAN_ACTIVE_KEY_ENV,
                PLAN_PREVIOUS_REF_ENV,
                PLAN_PREVIOUS_KEY_ENV,
            )?,
            evidence_keys: KeyMaterial::from_environment(
                EVIDENCE_ACTIVE_REF_ENV,
                EVIDENCE_ACTIVE_KEY_ENV,
                EVIDENCE_PREVIOUS_REF_ENV,
                EVIDENCE_PREVIOUS_KEY_ENV,
            )?,
        })
    }
}

struct AuthSetup {
    middleware: AuthMiddleware,
    subject: artifact_service::SubjectDigest,
}

struct DriverState {
    auth_probe: AuthMiddleware,
    render_auth: AuthMiddleware,
    policy: InMemoryProjectPolicy,
    sources: LocalPostgresPlanSourceRepository,
    plans: LocalPostgresStoredPlanRegistry,
    evidence: LocalPostgresPlanReviewEvidenceRepository,
}

fn main() {
    if run().is_err() {
        eprintln!("plan-review-staging-driver: request failed closed");
        std::process::exit(1);
    }
}

fn run() -> Result<(), DriverError> {
    let config = RuntimeConfig::from_environment()?;
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
            None => state.insert(DriverState::new(&config, request.now_unix_seconds)?),
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
    fn new(config: &RuntimeConfig, now_unix_seconds: u64) -> Result<Self, DriverError> {
        let auth_probe = build_auth(config, now_unix_seconds)?.middleware;
        let render_setup = build_auth(config, now_unix_seconds)?;
        let source_config = LocalPostgresPlanSourceConfig::new(
            config.port,
            config.database.clone(),
            config.source_user.clone(),
            config.source_password.to_string(),
        )
        .map_err(|_| DriverError::Configuration)?;
        let plan_config = LocalPostgresStoredPlanConfig::new(
            config.port,
            config.database.clone(),
            config.plan_user.clone(),
            config.plan_password.to_string(),
        )
        .map_err(|_| DriverError::Configuration)?;
        let evidence_config = LocalPostgresPlanReviewEvidenceConfig::new(
            config.port,
            config.database.clone(),
            config.evidence_user.clone(),
            config.evidence_password.to_string(),
        )
        .map_err(|_| DriverError::Configuration)?;
        let sources = LocalPostgresPlanSourceRepository::connect(&source_config, config.tenant)
            .map_err(|_| DriverError::Database)?;
        let plans = LocalPostgresStoredPlanRegistry::connect(
            &plan_config,
            config.tenant,
            DurablePlanKeyring::new(
                config.plan_keys.active_reference.clone(),
                config.plan_keys.entries(),
            )
            .map_err(|_| DriverError::Configuration)?,
            StoredPlanLimits::product_maximums(),
        )
        .map_err(|_| DriverError::Database)?;
        let evidence = LocalPostgresPlanReviewEvidenceRepository::connect(
            &evidence_config,
            config.tenant,
            DurablePlanReviewEvidenceKeyring::new(
                config.evidence_keys.active_reference.clone(),
                config.evidence_keys.entries(),
            )
            .map_err(|_| DriverError::Configuration)?,
        )
        .map_err(|_| DriverError::Database)?;
        let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
        policy
            .register_project(&config.project_id, config.tenant)
            .map_err(|_| DriverError::Configuration)?;
        policy
            .register_membership(
                &config.project_id,
                render_setup.subject,
                ProjectAccess::Owner,
            )
            .map_err(|_| DriverError::Configuration)?;
        Ok(Self {
            auth_probe,
            render_auth: render_setup.middleware,
            policy,
            sources,
            plans,
            evidence,
        })
    }

    fn handle(&mut self, request: DriverRequest) -> Result<Value, DriverError> {
        let authorization_header = request.authorization_header.map(Zeroizing::new);
        match request.mode {
            DriverMode::Ready => {
                if authorization_header.is_some()
                    || request.tool_name.is_some()
                    || request.arguments.is_some()
                {
                    return Err(DriverError::Request);
                }
                Ok(json!({"ready": true}))
            }
            DriverMode::Auth => {
                if request.tool_name.is_some() || request.arguments.is_some() {
                    return Err(DriverError::Request);
                }
                let authorization_header = bounded_authorization(authorization_header)?;
                self.auth_probe
                    .authenticate_public_mcp(
                        &authorization_header,
                        request.now_unix_seconds,
                        [AuthScope::ProjectRead],
                    )
                    .map_err(|_| DriverError::Request)?;
                Ok(json!({"authenticated": true}))
            }
            DriverMode::PlanReview => {
                if request.tool_name.as_deref() != Some(RENDER_TOOL) {
                    return Err(DriverError::Request);
                }
                let authorization_header = bounded_authorization(authorization_header)?;
                let arguments = request.arguments.ok_or(DriverError::Request)?;
                let arguments_json =
                    serde_json::to_vec(&arguments).map_err(|_| DriverError::Serialization)?;
                let snapshot = PlanReviewRenderer
                    .render(
                        &mut self.render_auth,
                        &self.policy,
                        &self.sources,
                        &mut self.plans,
                        &mut self.evidence,
                        PlanReviewRenderRequest::new(
                            authorization_header.to_string(),
                            arguments_json,
                            request.now_unix_seconds,
                        ),
                    )
                    .map_err(|_| DriverError::Renderer)?;
                snapshot
                    .structured_content()
                    .map_err(|_| DriverError::Serialization)
            }
        }
    }
}

fn build_auth(config: &RuntimeConfig, now_unix_seconds: u64) -> Result<AuthSetup, DriverError> {
    let active_until = now_unix_seconds
        .checked_add(3_600)
        .ok_or(DriverError::Configuration)?;
    let active_from = now_unix_seconds.saturating_sub(120);
    let mut middleware = AuthMiddleware::new(
        RESOURCE,
        METADATA,
        60,
        AuthRegistryLimits::product_maximums(),
    )
    .map_err(|_| DriverError::Configuration)?;
    middleware
        .register_local_hmac_key(
            ISSUER,
            KEY_ID,
            config.hmac_key.to_vec(),
            active_from,
            active_until,
        )
        .map_err(|_| DriverError::Configuration)?;
    let grant = PrincipalGrant::new(
        config.tenant,
        TenantRole::Owner,
        [AuthScope::ProjectRead],
        active_from,
        active_until,
    )
    .map_err(|_| DriverError::Configuration)?;
    let subject = middleware
        .register_user(ISSUER, &config.subject, grant)
        .map_err(|_| DriverError::Configuration)?;
    Ok(AuthSetup {
        middleware,
        subject,
    })
}

fn bounded_authorization(
    value: Option<Zeroizing<String>>,
) -> Result<Zeroizing<String>, DriverError> {
    let value = value.ok_or(DriverError::Request)?;
    if value.len() > auth_middleware::MAX_BEARER_TOKEN_BYTES + 7 {
        return Err(DriverError::Request);
    }
    Ok(value)
}

fn public_environment(name: &str) -> Result<String, DriverError> {
    let value = std::env::var(name).map_err(|_| DriverError::Configuration)?;
    if value.is_empty() || value.len() > MAX_PUBLIC_VALUE_BYTES || value.contains('\0') {
        return Err(DriverError::Configuration);
    }
    Ok(value)
}

fn optional_public_environment(name: &str) -> Result<Option<String>, DriverError> {
    match std::env::var(name) {
        Ok(value) => {
            if value.is_empty() || value.len() > MAX_PUBLIC_VALUE_BYTES || value.contains('\0') {
                return Err(DriverError::Configuration);
            }
            Ok(Some(value))
        }
        Err(std::env::VarError::NotPresent) => Ok(None),
        Err(std::env::VarError::NotUnicode(_)) => Err(DriverError::Configuration),
    }
}

fn secret_environment(name: &str) -> Result<Zeroizing<String>, DriverError> {
    let value = Zeroizing::new(std::env::var(name).map_err(|_| DriverError::Configuration)?);
    if value.is_empty() || value.len() > MAX_PUBLIC_VALUE_BYTES || value.contains('\0') {
        return Err(DriverError::Configuration);
    }
    Ok(value)
}

fn decoded_environment(name: &str) -> Result<Zeroizing<Vec<u8>>, DriverError> {
    let encoded = secret_environment(name)?;
    let decoded = URL_SAFE_NO_PAD
        .decode(encoded.as_bytes())
        .map_err(|_| DriverError::Configuration)?;
    Ok(Zeroizing::new(decoded))
}

fn key_environment(name: &str) -> Result<Zeroizing<[u8; 32]>, DriverError> {
    let decoded = decoded_environment(name)?;
    let key: [u8; 32] = decoded
        .as_slice()
        .try_into()
        .map_err(|_| DriverError::Configuration)?;
    if key == [0; 32] {
        return Err(DriverError::Configuration);
    }
    Ok(Zeroizing::new(key))
}

fn optional_key_environment(name: &str) -> Result<Option<Zeroizing<[u8; 32]>>, DriverError> {
    match std::env::var(name) {
        Ok(value) => {
            let encoded = Zeroizing::new(value);
            if encoded.is_empty() || encoded.len() > 128 || encoded.contains('\0') {
                return Err(DriverError::Configuration);
            }
            let decoded = Zeroizing::new(
                URL_SAFE_NO_PAD
                    .decode(encoded.as_bytes())
                    .map_err(|_| DriverError::Configuration)?,
            );
            let key: [u8; 32] = decoded
                .as_slice()
                .try_into()
                .map_err(|_| DriverError::Configuration)?;
            if key == [0; 32] {
                return Err(DriverError::Configuration);
            }
            Ok(Some(Zeroizing::new(key)))
        }
        Err(std::env::VarError::NotPresent) => Ok(None),
        Err(std::env::VarError::NotUnicode(_)) => Err(DriverError::Configuration),
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
    fn request_parser_denies_unknown_fields() {
        let value = br#"{"driver_request_id":1,"mode":"ready","now_unix_seconds":1,"extra":true}"#;
        assert!(serde_json::from_slice::<DriverRequest>(value).is_err());
    }

    #[test]
    fn bounded_reader_requires_one_complete_line() {
        let mut valid = io::Cursor::new(b"{}\n".as_slice());
        assert!(matches!(read_bounded_line(&mut valid), Ok(Some(_))));
        let mut partial = io::Cursor::new(b"{}".as_slice());
        assert!(matches!(
            read_bounded_line(&mut partial),
            Err(DriverError::Request)
        ));
    }
}
