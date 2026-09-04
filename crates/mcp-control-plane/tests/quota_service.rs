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
    AuthorizedToolCall, GatewayError, InMemoryQuotaService, McpControlPlane, McpToolRequest,
    QUOTA_POLICY_SHA256, QuotaAdmission, QuotaError, QuotaService, QuotaStateLimits, ToolKind,
    ToolPolicy, ToolServiceGateway, ToolServiceOutput, map_quota_error,
};
use serde::Serialize;
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use uuid::Uuid;

type HmacSha256 = Hmac<Sha256>;

const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const KEY_ID: &str = "local-key-01";
const SECRET: &[u8] = b"0123456789abcdef0123456789abcdef";
const NOW: u64 = 2_000_000_000;

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
}

fn tenant(value: u128) -> TenantId {
    TenantId::new(Uuid::from_u128(value)).unwrap_or_else(|error| panic!("tenant fixture: {error}"))
}

fn auth_and_bearer(tenant_id: TenantId, subject: &str) -> (AuthMiddleware, String) {
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
    middleware
        .register_user(
            ISSUER,
            subject,
            PrincipalGrant::new(
                tenant_id,
                TenantRole::Owner,
                [AuthScope::ProjectRead],
                NOW - 600,
                NOW + 7_200,
            )
            .unwrap_or_else(|error| panic!("grant fixture: {error}")),
        )
        .unwrap_or_else(|error| panic!("user fixture: {error}"));
    let claims = Claims {
        iss: ISSUER.to_owned(),
        sub: subject.to_owned(),
        aud: RESOURCE.to_owned(),
        exp: NOW + 600,
        nbf: NOW - 60,
        iat: NOW - 60,
        jti: format!("token-{subject}"),
        scope: AuthScope::ProjectRead.as_str().to_owned(),
        token_kind: "user".to_owned(),
        tenant_id,
    };
    let header = URL_SAFE_NO_PAD.encode(
        serde_json::to_vec(&json!({"alg": "HS256", "kid": KEY_ID, "typ": "at+jwt"}))
            .unwrap_or_else(|error| panic!("serialize token header: {error}")),
    );
    let claims = URL_SAFE_NO_PAD.encode(
        serde_json::to_vec(&claims)
            .unwrap_or_else(|error| panic!("serialize token claims: {error}")),
    );
    let signing_input = format!("{header}.{claims}");
    let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(SECRET)
        .unwrap_or_else(|error| panic!("signing fixture: {error}"));
    signer.update(signing_input.as_bytes());
    let token = format!(
        "{signing_input}.{}",
        URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
    );
    (middleware, format!("Bearer {token}"))
}

fn context(tenant_id: TenantId, subject: &str) -> AuthContext {
    let (mut middleware, bearer) = auth_and_bearer(tenant_id, subject);
    middleware
        .authenticate_public_mcp(&bearer, NOW, [AuthScope::ProjectRead])
        .unwrap_or_else(|error| panic!("authenticate fixture: {error}"))
}

fn idempotent_arguments(key: &str, payload: &str) -> Value {
    json!({
        "request_id": "req_quota001",
        "idempotency_key": key,
        "payload": payload,
    })
}

#[test]
fn pinned_policy_digest_and_limits_load() {
    let bytes = include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../protocol/mcp/p15-quota-policy-v1.json"
    ));
    assert_eq!(
        hex::encode(sha2::Sha256::digest(bytes)),
        QUOTA_POLICY_SHA256
    );
    assert!(InMemoryQuotaService::new().is_ok());
    assert!(QuotaStateLimits::new(0, 1).is_err());
    assert!(QuotaStateLimits::new(1, 0).is_err());
}

#[test]
fn render_job_class_enforces_burst_and_exact_retry_guidance() {
    let service = InMemoryQuotaService::new().unwrap_or_else(|error| panic!("quota: {error}"));
    let context = context(tenant(1), "render-user");
    for index in 0..2 {
        let admission = service
            .admit(
                &context,
                ToolKind::DocumentRender,
                &idempotent_arguments(&format!("render-{index}"), "same"),
                NOW,
            )
            .unwrap_or_else(|error| panic!("render admission: {error}"));
        assert!(!admission.replayed());
    }
    assert_eq!(
        service.admit(
            &context,
            ToolKind::DocumentRender,
            &idempotent_arguments("render-2", "same"),
            NOW,
        ),
        Err(QuotaError::Exhausted {
            retry_after_seconds: 30
        })
    );
    for index in 3..103 {
        assert!(matches!(
            service.admit(
                &context,
                ToolKind::DocumentRender,
                &idempotent_arguments(&format!("render-{index}"), "same"),
                NOW,
            ),
            Err(QuotaError::Exhausted { .. })
        ));
    }
    assert!(
        service
            .admit(
                &context,
                ToolKind::DocumentValidate,
                &idempotent_arguments("standard-after-rejections", "same"),
                NOW,
            )
            .is_ok()
    );
    assert!(
        service
            .admit(
                &context,
                ToolKind::DocumentRender,
                &idempotent_arguments("render-3", "same"),
                NOW + 30,
            )
            .is_ok()
    );
}

#[test]
fn standard_job_class_is_independent_from_render() {
    let service = InMemoryQuotaService::new().unwrap_or_else(|error| panic!("quota: {error}"));
    let context = context(tenant(2), "standard-user");
    for index in 0..8 {
        service
            .admit(
                &context,
                ToolKind::DocumentValidate,
                &idempotent_arguments(&format!("standard-{index}"), "same"),
                NOW,
            )
            .unwrap_or_else(|error| panic!("standard admission: {error}"));
    }
    assert_eq!(
        service.admit(
            &context,
            ToolKind::DocumentValidate,
            &idempotent_arguments("standard-8", "same"),
            NOW,
        ),
        Err(QuotaError::Exhausted {
            retry_after_seconds: 8
        })
    );
    assert!(
        service
            .admit(
                &context,
                ToolKind::DocumentRender,
                &idempotent_arguments("render-independent", "same"),
                NOW,
            )
            .is_ok()
    );
}

#[test]
fn capability_burst_is_bounded_without_cross_tenant_or_user_starvation() {
    let service = InMemoryQuotaService::new().unwrap_or_else(|error| panic!("quota: {error}"));
    let first = context(tenant(3), "noisy-user");
    for _ in 0..30 {
        assert!(
            service
                .admit(&first, ToolKind::ProjectOpen, &json!({}), NOW)
                .is_ok()
        );
    }
    assert!(matches!(
        service.admit(&first, ToolKind::ProjectOpen, &json!({}), NOW),
        Err(QuotaError::Exhausted { .. })
    ));
    let capability_user = context(tenant(10), "capability-user");
    for _ in 0..30 {
        assert!(
            service
                .admit(
                    &capability_user,
                    ToolKind::CapabilityCheck,
                    &json!({"capability_id": "page.paper_preset"}),
                    NOW,
                )
                .is_ok()
        );
    }
    assert!(matches!(
        service.admit(
            &capability_user,
            ToolKind::CapabilityCheck,
            &json!({"capability_id": "page.paper_preset"}),
            NOW,
        ),
        Err(QuotaError::Exhausted { .. })
    ));
    assert!(
        service
            .admit(
                &capability_user,
                ToolKind::CapabilityCheck,
                &json!({"capability_id": "paragraph.style"}),
                NOW,
            )
            .is_ok()
    );
    for _ in 0..30 {
        assert!(
            service
                .admit(&first, ToolKind::ProjectHistory, &json!({}), NOW)
                .is_ok()
        );
    }
    let second_user = context(tenant(3), "fair-user");
    assert!(
        service
            .admit(&second_user, ToolKind::ProjectCheckpoint, &json!({}), NOW)
            .is_ok()
    );
    let second_tenant = context(tenant(4), "noisy-user");
    assert!(
        service
            .admit(&second_tenant, ToolKind::ProjectOpen, &json!({}), NOW)
            .is_ok()
    );
}

#[test]
fn idempotent_replay_is_not_recharged_and_payload_reuse_conflicts() {
    let service = InMemoryQuotaService::new().unwrap_or_else(|error| panic!("quota: {error}"));
    let context = context(tenant(5), "replay-user");
    let first = idempotent_arguments("stable-key", "payload-a");
    let admission = service
        .admit(&context, ToolKind::DocumentRender, &first, NOW)
        .unwrap_or_else(|error| panic!("first admission: {error}"));
    assert!(!admission.replayed());
    assert_eq!(
        service.admit(&context, ToolKind::DocumentRender, &first, NOW - 1),
        Err(QuotaError::StateUnavailable)
    );
    let mut replay = first.clone();
    replay["request_id"] = Value::String("req_quota002".to_owned());
    let admission = service
        .admit(&context, ToolKind::DocumentRender, &replay, NOW)
        .unwrap_or_else(|error| panic!("replay admission: {error}"));
    assert!(admission.replayed());
    assert_eq!(
        service.admit(
            &context,
            ToolKind::DocumentRender,
            &idempotent_arguments("stable-key", "payload-b"),
            NOW,
        ),
        Err(QuotaError::IdempotencyConflict)
    );
    assert!(
        service
            .admit(
                &context,
                ToolKind::DocumentRender,
                &idempotent_arguments("second-key", "payload-a"),
                NOW,
            )
            .is_ok()
    );
    assert!(matches!(
        service.admit(
            &context,
            ToolKind::DocumentRender,
            &idempotent_arguments("third-key", "payload-a"),
            NOW,
        ),
        Err(QuotaError::Exhausted { .. })
    ));
}

#[test]
fn state_capacity_and_clock_regression_fail_closed_without_global_starvation() {
    let limits =
        QuotaStateLimits::new(3, 8).unwrap_or_else(|error| panic!("state limits: {error}"));
    let service = InMemoryQuotaService::with_state_limits(limits)
        .unwrap_or_else(|error| panic!("quota: {error}"));
    let first = context(tenant(6), "capacity-user");
    assert!(
        service
            .admit(&first, ToolKind::ProjectOpen, &json!({}), NOW)
            .is_ok()
    );
    assert_eq!(
        service.admit(&first, ToolKind::ProjectHistory, &json!({}), NOW),
        Err(QuotaError::StateCapacityExceeded)
    );

    let service = InMemoryQuotaService::new().unwrap_or_else(|error| panic!("quota: {error}"));
    assert!(
        service
            .admit(&first, ToolKind::ProjectOpen, &json!({}), NOW)
            .is_ok()
    );
    assert_eq!(
        service.admit(&first, ToolKind::ProjectOpen, &json!({}), NOW - 1),
        Err(QuotaError::StateUnavailable)
    );
    let independent = context(tenant(7), "independent-user");
    assert!(
        service
            .admit(&independent, ToolKind::ProjectOpen, &json!({}), NOW - 1)
            .is_ok()
    );
}

#[test]
fn concurrent_burst_has_exactly_two_render_winners() {
    let service = Arc::new(
        InMemoryQuotaService::new().unwrap_or_else(|error| panic!("quota fixture: {error}")),
    );
    let context = context(tenant(8), "concurrent-user");
    let mut workers = Vec::new();
    for index in 0..16 {
        let service = Arc::clone(&service);
        let context = context.clone();
        workers.push(std::thread::spawn(move || {
            service.admit(
                &context,
                ToolKind::DocumentRender,
                &idempotent_arguments(&format!("concurrent-{index}"), "same"),
                NOW,
            )
        }));
    }
    let results = workers
        .into_iter()
        .map(|worker| worker.join().unwrap_or(Err(QuotaError::StateUnavailable)))
        .collect::<Vec<_>>();
    assert_eq!(results.iter().filter(|result| result.is_ok()).count(), 2);
    assert_eq!(
        results
            .iter()
            .filter(|result| matches!(result, Err(QuotaError::Exhausted { .. })))
            .count(),
        14
    );
}

#[derive(Debug)]
struct AllowPolicy;

impl ToolPolicy for AllowPolicy {
    fn authorize(
        &self,
        _context: &AuthContext,
        _tool: ToolKind,
        _arguments: &Value,
    ) -> Result<(), mcp_control_plane::PolicyError> {
        Ok(())
    }
}

#[derive(Debug)]
struct AlwaysExhaustedQuota;

impl QuotaService for AlwaysExhaustedQuota {
    fn admit(
        &self,
        _context: &AuthContext,
        _tool: ToolKind,
        _arguments: &Value,
        _now_unix_seconds: u64,
    ) -> Result<QuotaAdmission, QuotaError> {
        Err(QuotaError::Exhausted {
            retry_after_seconds: 17,
        })
    }
}

#[derive(Debug)]
struct CountingGateway(Arc<AtomicUsize>);

impl ToolServiceGateway for CountingGateway {
    fn dispatch(&mut self, call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError> {
        self.0.fetch_add(1, Ordering::SeqCst);
        Ok(ToolServiceOutput::new(json!({
            "schema_version": "hwpx-agent.tool-result/v1",
            "request_id": call.request_id(),
            "outcome": "succeeded",
            "safe_summary": "Project opened.",
            "warnings": [],
            "project_id": "prj_quota001",
            "head_revision_id": null,
            "warning_count": 0,
            "conflict_state": "none",
            "recommended_actions": [],
        })))
    }
}

#[test]
fn handler_returns_bounded_retry_metadata_without_dispatch() {
    let (middleware, bearer) = auth_and_bearer(tenant(9), "handler-user");
    let gateway_calls = Arc::new(AtomicUsize::new(0));
    let mut control = McpControlPlane::with_quota(
        middleware,
        AllowPolicy,
        AlwaysExhaustedQuota,
        CountingGateway(Arc::clone(&gateway_calls)),
    )
    .unwrap_or_else(|error| panic!("control plane: {error}"));
    let arguments = json!({
        "client_surface": "codex_local",
        "locale": "ko-KR",
        "request_id": "req_quota001",
        "project_id": "prj_quota001",
        "include": ["head"]
    });
    let result = control.handle(McpToolRequest::new(
        "project_open",
        bearer,
        serde_json::to_vec(&arguments).unwrap_or_else(|error| panic!("serialize request: {error}")),
        NOW,
    ));
    assert_eq!(result.error_code(), Some("QUOTA_EXCEEDED"));
    assert_eq!(result.structured_content()["stage"], "quota");
    assert_eq!(result.structured_content()["retryable"], true);
    assert_eq!(result.meta()["hwpx/retryAfterSeconds"], 17);
    assert_eq!(result.meta()["hwpx/quotaPolicySha256"], QUOTA_POLICY_SHA256);
    assert_eq!(gateway_calls.load(Ordering::SeqCst), 0);
    assert_eq!(
        map_quota_error(QuotaError::IdempotencyConflict)
            .code()
            .as_str(),
        "REQUEST_CONFLICT"
    );
    for error in [
        QuotaError::InvalidConfiguration,
        QuotaError::StateUnavailable,
        QuotaError::StateCapacityExceeded,
    ] {
        assert_eq!(map_quota_error(error).code().as_str(), "QUOTA_UNAVAILABLE");
    }
    assert_eq!(
        map_quota_error(QuotaError::Exhausted {
            retry_after_seconds: 17,
        })
        .code()
        .as_str(),
        "QUOTA_EXCEEDED"
    );
}
