use std::collections::BTreeSet;

use artifact_service::{
    Aes256GcmKeyring, ArtifactError, ArtifactId, ArtifactKind, ArtifactPermission, ArtifactScanner,
    ArtifactService, ArtifactServiceConfig, AuthScope as ArtifactAuthScope, DownloadSigner,
    FileName, InMemoryBlobStore, InMemoryMetadataRepository, IngestRequest, KeyReference,
    MediaType, QuarantineReason, RequestContext, ScanEvidence, ScanRequest, ScanVerdict,
    ScannerReference, ScannerSignatureVersion, SubjectDigest, TenantId,
};
use auth_middleware::{AuthMiddleware, AuthRegistryLimits, AuthScope, PrincipalGrant, TenantRole};
use base64::Engine as _;
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use hmac::{Hmac, Mac as _};
use mcp_control_plane::{
    ArtifactDeliveryConfig, ArtifactDeliveryError, ArtifactDeliveryGateway, ArtifactDeliverySigner,
    ArtifactProjectRegistry, AuthorizedToolCall, GatewayError, InMemoryProjectPolicy,
    McpControlPlane, McpToolRequest, ProjectAccess, ProjectPolicyLimits, SignedArtifactUrl,
    ToolServiceGateway, ToolServiceOutput,
};
use serde::Serialize;
use serde_json::{Value, json};
use sha2::Sha256;
use uuid::Uuid;

type HmacSha256 = Hmac<Sha256>;
type Source = ArtifactService<InMemoryMetadataRepository, InMemoryBlobStore, CleanScanner>;
type DeliveryGateway = ArtifactDeliveryGateway<RejectingDelegate, Source>;
type Control = McpControlPlane<InMemoryProjectPolicy, DeliveryGateway>;

const RESOURCE: &str = "https://mcp.hwpx-agent.example";
const METADATA: &str = "https://mcp.hwpx-agent.example/.well-known/oauth-protected-resource";
const ISSUER: &str = "https://identity.hwpx-agent.example";
const KEY_ID: &str = "local-key-01";
const AUTH_SECRET: &[u8] = b"0123456789abcdef0123456789abcdef";
const DELIVERY_SECRET: &[u8] = b"delivery-key-0123456789abcdef-01";
const NOW: u64 = 2_100_000_000;
const PROJECT_ID: &str = "prj_delivery01";
const OTHER_PROJECT_ID: &str = "prj_delivery02";
const PAYLOAD: &[u8] = b"0123456789abcdef";

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
struct CleanScanner;

impl ArtifactScanner for CleanScanner {
    fn scan(&self, _request: ScanRequest<'_>) -> Result<ScanEvidence, ArtifactError> {
        Ok(ScanEvidence {
            engine: ScannerReference::parse("scanner.p15-test")?,
            signature_version: ScannerSignatureVersion::parse("2026.09")?,
            verdict: ScanVerdict::Clean,
        })
    }
}

#[derive(Debug)]
struct RejectingDelegate;

impl ToolServiceGateway for RejectingDelegate {
    fn dispatch(&mut self, _call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError> {
        Err(GatewayError::Rejected)
    }
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
}

struct Fixture {
    control: Control,
    bearer: String,
    tenant_id: TenantId,
    subject: SubjectDigest,
    artifact_id: ArtifactId,
    owner_context: RequestContext,
    bindings: ArtifactProjectRegistry,
}

impl Fixture {
    #[allow(clippy::too_many_lines)]
    fn new(max_range_bytes: u64) -> Self {
        let tenant_id = tenant(501);
        let mut middleware = AuthMiddleware::new(
            RESOURCE,
            METADATA,
            60,
            AuthRegistryLimits::product_maximums(),
        )
        .unwrap_or_else(|error| panic!("middleware: {error}"));
        middleware
            .register_local_hmac_key(ISSUER, KEY_ID, AUTH_SECRET, NOW - 600, NOW + 7_200)
            .unwrap_or_else(|error| panic!("auth key: {error}"));
        let subject = middleware
            .register_user(
                ISSUER,
                "oidc-artifact-user",
                PrincipalGrant::new(
                    tenant_id,
                    TenantRole::Owner,
                    ALL_SCOPES,
                    NOW - 600,
                    NOW + 7_200,
                )
                .unwrap_or_else(|error| panic!("grant: {error}")),
            )
            .unwrap_or_else(|error| panic!("user: {error}"));
        let claims = Claims {
            iss: ISSUER.to_owned(),
            sub: "oidc-artifact-user".to_owned(),
            aud: RESOURCE.to_owned(),
            exp: NOW + 1_800,
            nbf: NOW - 60,
            iat: NOW - 60,
            jti: "artifact-token-0001".to_owned(),
            scope: ALL_SCOPES
                .iter()
                .map(|scope| scope.as_str())
                .collect::<Vec<_>>()
                .join(" "),
            token_kind: "user".to_owned(),
            tenant_id,
        };
        let owner_context = RequestContext::new(
            tenant_id,
            subject,
            [
                ArtifactAuthScope::DocumentRead,
                ArtifactAuthScope::DocumentWrite,
                ArtifactAuthScope::ArtifactShare,
                ArtifactAuthScope::SecurityModify,
            ],
        );
        let source = artifact_service();
        let descriptor = source
            .ingest(
                &owner_context,
                IngestRequest {
                    bytes: PAYLOAD.to_vec(),
                    media_type: MediaType::parse("application/octet-stream")
                        .unwrap_or_else(|error| panic!("media type: {error}")),
                    file_name: FileName::parse("result.hwpx")
                        .unwrap_or_else(|error| panic!("file name: {error}")),
                    kind: ArtifactKind::Result,
                },
                NOW - 10,
            )
            .unwrap_or_else(|error| panic!("ingest: {error}"));
        let bindings =
            ArtifactProjectRegistry::new(16).unwrap_or_else(|error| panic!("bindings: {error}"));
        bindings
            .register(tenant_id, PROJECT_ID, descriptor.artifact_id)
            .unwrap_or_else(|error| panic!("binding: {error}"));
        let signer = ArtifactDeliverySigner::new(
            "https://downloads.hwpx-agent.example/v1/artifacts",
            "p15-delivery-01",
            DELIVERY_SECRET,
            900,
        )
        .unwrap_or_else(|error| panic!("delivery signer: {error}"));
        let config = ArtifactDeliveryConfig::new(120, 900, max_range_bytes)
            .unwrap_or_else(|error| panic!("delivery config: {error}"));
        let gateway = ArtifactDeliveryGateway::new(
            RejectingDelegate,
            source,
            bindings.clone(),
            signer,
            config,
        )
        .unwrap_or_else(|error| panic!("delivery gateway: {error}"));
        let mut policy = InMemoryProjectPolicy::new(ProjectPolicyLimits::product_maximums());
        for project in [PROJECT_ID, OTHER_PROJECT_ID] {
            policy
                .register_project(project, tenant_id)
                .unwrap_or_else(|error| panic!("project: {error}"));
            policy
                .register_membership(project, subject, ProjectAccess::Owner)
                .unwrap_or_else(|error| panic!("membership: {error}"));
        }
        let control = McpControlPlane::new(middleware, policy, gateway)
            .unwrap_or_else(|error| panic!("control plane: {error}"));
        Self {
            control,
            bearer: format!("Bearer {}", sign(&claims)),
            tenant_id,
            subject,
            artifact_id: descriptor.artifact_id,
            owner_context,
            bindings,
        }
    }

    fn call(
        &mut self,
        disposition: &str,
        project_id: &str,
        ttl: Option<u64>,
    ) -> mcp_control_plane::McpToolResult {
        let mut arguments = json!({
            "client_surface": "codex_local",
            "locale": "ko-KR",
            "request_id": "req_delivery01",
            "project_id": project_id,
            "idempotency_key": "123e4567-e89b-12d3-a456-426614174000",
            "artifact_id": self.artifact_id.public_id(),
            "disposition": disposition,
        });
        if let Some(ttl) = ttl {
            arguments
                .as_object_mut()
                .unwrap_or_else(|| panic!("arguments object"))
                .insert("delivery_ttl_seconds".to_owned(), Value::from(ttl));
        }
        self.control.handle(McpToolRequest::new(
            "artifact_get",
            self.bearer.clone(),
            serde_json::to_vec(&arguments)
                .unwrap_or_else(|error| panic!("serialize input: {error}")),
            NOW,
        ))
    }

    fn signed_url(result: &mcp_control_plane::McpToolResult) -> SignedArtifactUrl {
        SignedArtifactUrl::parse(
            result.meta()["hwpx/artifactDelivery"]["signedUrl"]
                .as_str()
                .unwrap_or_else(|| panic!("signed URL")),
        )
        .unwrap_or_else(|error| panic!("parse signed URL: {error}"))
    }
}

fn tenant(value: u128) -> TenantId {
    TenantId::new(Uuid::from_u128(value)).unwrap_or_else(|error| panic!("tenant: {error}"))
}

fn artifact_service() -> Source {
    let key_ref =
        KeyReference::parse("aes.p15-test").unwrap_or_else(|error| panic!("key ref: {error}"));
    let keyring = Aes256GcmKeyring::new(key_ref.clone(), [(key_ref, [7_u8; 32])])
        .unwrap_or_else(|error| panic!("keyring: {error}"));
    let signer = DownloadSigner::new(
        "https://p14-artifacts.example/v1/download",
        KeyReference::parse("hmac.p15-test")
            .unwrap_or_else(|error| panic!("signer key ref: {error}")),
        b"p14-reference-signing-key-0000001",
        300,
    )
    .unwrap_or_else(|error| panic!("p14 signer: {error}"));
    ArtifactService::new(
        InMemoryMetadataRepository::default(),
        InMemoryBlobStore::default(),
        CleanScanner,
        keyring,
        signer,
        ArtifactServiceConfig::new(1_048_576, 300)
            .unwrap_or_else(|error| panic!("artifact config: {error}")),
    )
}

fn sign(claims: &Claims) -> String {
    let header = URL_SAFE_NO_PAD.encode(
        serde_json::to_vec(&json!({"alg": "HS256", "kid": KEY_ID, "typ": "at+jwt"}))
            .unwrap_or_else(|error| panic!("header: {error}")),
    );
    let body = URL_SAFE_NO_PAD
        .encode(serde_json::to_vec(claims).unwrap_or_else(|error| panic!("claims: {error}")));
    let signing_input = format!("{header}.{body}");
    let mut signer = <HmacSha256 as hmac::KeyInit>::new_from_slice(AUTH_SECRET)
        .unwrap_or_else(|error| panic!("auth signer: {error}"));
    signer.update(signing_input.as_bytes());
    format!(
        "{signing_input}.{}",
        URL_SAFE_NO_PAD.encode(signer.finalize().into_bytes())
    )
}

#[test]
fn metadata_returns_only_acl_checked_frozen_structured_output() {
    let mut fixture = Fixture::new(8);
    let result = fixture.call("metadata", PROJECT_ID, None);
    assert!(!result.is_error(), "{:?}", result.error_code());
    assert_eq!(result.structured_content()["delivery"], "metadata");
    assert_eq!(result.structured_content()["expires_at"], Value::Null);
    assert_eq!(
        result.structured_content()["artifact"]["artifact_id"],
        fixture.artifact_id.public_id()
    );
    assert!(result.meta().get("hwpx/artifactDelivery").is_none());
}

#[test]
fn preview_keeps_signed_url_in_client_only_meta() {
    let mut fixture = Fixture::new(8);
    let result = fixture.call("preview", PROJECT_ID, Some(60));
    assert!(!result.is_error(), "{:?}", result.error_code());
    assert_eq!(result.structured_content()["delivery"], "preview_in_meta");
    assert_eq!(
        result.structured_content()["expires_at"],
        result.meta()["hwpx/artifactDelivery"]["expiresAt"]
    );
    let serialized =
        serde_json::to_value(&result).unwrap_or_else(|error| panic!("serialize result: {error}"));
    let content = serde_json::to_string(&serialized["content"])
        .unwrap_or_else(|error| panic!("serialize content: {error}"));
    assert!(!content.contains("sig="));
    assert!(
        result.meta()["hwpx/artifactDelivery"]["signedUrl"]
            .as_str()
            .is_some_and(|url| url.contains("sig="))
    );
    assert!(!format!("{result:?}").contains("sig="));
}

#[test]
fn attachment_uses_resource_link_without_leaking_token_into_content() {
    let mut fixture = Fixture::new(8);
    let result = fixture.call("attachment", PROJECT_ID, Some(900));
    assert!(!result.is_error(), "{:?}", result.error_code());
    assert_eq!(
        result.structured_content()["delivery"],
        "attachment_in_content"
    );
    let serialized =
        serde_json::to_value(&result).unwrap_or_else(|error| panic!("serialize result: {error}"));
    assert_eq!(serialized["content"][1]["type"], "resource_link");
    assert_eq!(serialized["content"][1]["name"], "result.hwpx");
    assert!(
        serialized["content"][1]["uri"]
            .as_str()
            .is_some_and(|uri| uri.starts_with("hwpx-artifact://download/art_"))
    );
    assert!(
        !serialized["content"][1]["uri"]
            .as_str()
            .unwrap_or_default()
            .contains("sig=")
    );
}

#[test]
fn project_binding_and_metadata_ttl_fail_closed() {
    let mut fixture = Fixture::new(8);
    let wrong_project = fixture.call("preview", OTHER_PROJECT_ID, Some(60));
    assert!(wrong_project.is_error());
    assert_eq!(wrong_project.error_code(), Some("RESOURCE_NOT_FOUND"));

    let metadata_ttl = fixture.call("metadata", PROJECT_ID, Some(60));
    assert!(metadata_ttl.is_error());
    assert_eq!(metadata_ttl.error_code(), Some("SERVICE_REJECTED"));
}

#[test]
fn closed_open_suffix_and_clamped_ranges_are_exact() {
    let mut fixture = Fixture::new(8);
    let result = fixture.call("preview", PROJECT_ID, Some(60));
    let url = Fixture::signed_url(&result);
    let gateway = fixture.control.gateway();

    let closed = gateway
        .redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            Some("bytes=2-5"),
            NOW + 1,
        )
        .unwrap_or_else(|error| panic!("closed range: {error}"));
    assert_eq!(closed.status_code(), 206);
    assert_eq!(closed.content_range(), Some("bytes 2-5/16"));
    assert_eq!(closed.bytes(), b"2345");

    let open = gateway
        .redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            Some("bytes=12-"),
            NOW + 1,
        )
        .unwrap_or_else(|error| panic!("open range: {error}"));
    assert_eq!(open.bytes(), b"cdef");

    let suffix = gateway
        .redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            Some("bytes=-4"),
            NOW + 1,
        )
        .unwrap_or_else(|error| panic!("suffix range: {error}"));
    assert_eq!(suffix.start(), 12);
    assert_eq!(suffix.end_inclusive(), Some(15));
    assert_eq!(suffix.bytes(), b"cdef");

    let clamped = gateway
        .redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            Some("bytes=14-99"),
            NOW + 1,
        )
        .unwrap_or_else(|error| panic!("clamped range: {error}"));
    assert_eq!(clamped.content_range(), Some("bytes 14-15/16"));
    assert_eq!(clamped.bytes(), b"ef");
}

#[test]
fn full_multiple_unsatisfiable_and_oversized_ranges_are_bounded() {
    let mut fixture = Fixture::new(8);
    let result = fixture.call("preview", PROJECT_ID, Some(60));
    let url = Fixture::signed_url(&result);
    let gateway = fixture.control.gateway();

    assert_eq!(
        gateway.redeem_range(fixture.tenant_id, fixture.subject, &url, None, NOW + 1),
        Err(ArtifactDeliveryError::RangeTooLarge)
    );
    assert_eq!(
        gateway.redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            Some("bytes=0-1,3-4"),
            NOW + 1,
        ),
        Err(ArtifactDeliveryError::InvalidRange)
    );
    assert_eq!(
        gateway.redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            Some("bytes=99-"),
            NOW + 1,
        ),
        Err(ArtifactDeliveryError::RangeNotSatisfiable { total_bytes: 16 })
    );
    assert_eq!(
        gateway.redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            Some("bytes=0-8"),
            NOW + 1,
        ),
        Err(ArtifactDeliveryError::RangeTooLarge)
    );
}

#[test]
fn token_is_valid_through_expiry_then_rejected() {
    let mut fixture = Fixture::new(32);
    let result = fixture.call("preview", PROJECT_ID, Some(30));
    let url = Fixture::signed_url(&result);
    assert!(
        fixture
            .control
            .gateway()
            .redeem_range(fixture.tenant_id, fixture.subject, &url, None, NOW + 30,)
            .is_ok()
    );
    assert_eq!(
        fixture.control.gateway().redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            None,
            NOW + 31,
        ),
        Err(ArtifactDeliveryError::ExpiredToken)
    );
}

#[test]
fn token_tamper_and_subject_confusion_are_rejected() {
    let mut fixture = Fixture::new(32);
    let result = fixture.call("preview", PROJECT_ID, Some(60));
    let url = Fixture::signed_url(&result);
    let tampered = SignedArtifactUrl::parse(url.expose().replace("op=download", "op=upload"))
        .unwrap_or_else(|error| panic!("tampered token shape: {error}"));
    assert_eq!(
        fixture.control.gateway().redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &tampered,
            None,
            NOW + 1,
        ),
        Err(ArtifactDeliveryError::InvalidToken)
    );
    let other_subject = SubjectDigest::from_authenticated_subject("different subject")
        .unwrap_or_else(|error| panic!("other subject: {error}"));
    assert_eq!(
        fixture.control.gateway().redeem_range(
            fixture.tenant_id,
            other_subject,
            &url,
            None,
            NOW + 1,
        ),
        Err(ArtifactDeliveryError::AccessDenied)
    );
}

#[test]
fn current_acl_is_rechecked_when_token_is_redeemed() {
    let mut fixture = Fixture::new(32);
    let result = fixture.call("preview", PROJECT_ID, Some(60));
    let url = Fixture::signed_url(&result);
    let other_subject = SubjectDigest::from_authenticated_subject("replacement manager")
        .unwrap_or_else(|error| panic!("replacement subject: {error}"));
    fixture
        .control
        .gateway()
        .source()
        .set_permissions(
            &fixture.owner_context,
            fixture.artifact_id,
            other_subject,
            BTreeSet::from([ArtifactPermission::Manage]),
            NOW + 1,
        )
        .unwrap_or_else(|error| panic!("add manager: {error}"));
    fixture
        .control
        .gateway()
        .source()
        .set_permissions(
            &fixture.owner_context,
            fixture.artifact_id,
            fixture.subject,
            BTreeSet::new(),
            NOW + 2,
        )
        .unwrap_or_else(|error| panic!("remove old reader: {error}"));
    assert_eq!(
        fixture.control.gateway().redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            None,
            NOW + 3,
        ),
        Err(ArtifactDeliveryError::AccessDenied)
    );
}

#[test]
fn quarantine_after_issue_blocks_redemption() {
    let mut fixture = Fixture::new(32);
    let result = fixture.call("preview", PROJECT_ID, Some(60));
    let url = Fixture::signed_url(&result);
    fixture
        .control
        .gateway()
        .source()
        .quarantine(
            &fixture.owner_context,
            fixture.artifact_id,
            QuarantineReason::parse("POST_ISSUE_QUARANTINE")
                .unwrap_or_else(|error| panic!("reason: {error}")),
            NOW + 1,
        )
        .unwrap_or_else(|error| panic!("quarantine: {error}"));
    assert_eq!(
        fixture.control.gateway().redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            None,
            NOW + 2,
        ),
        Err(ArtifactDeliveryError::NotDeliverable)
    );
}

#[test]
fn project_binding_revocation_invalidates_an_issued_token() {
    let mut fixture = Fixture::new(32);
    let result = fixture.call("preview", PROJECT_ID, Some(60));
    let url = Fixture::signed_url(&result);
    fixture
        .bindings
        .revoke(fixture.tenant_id, PROJECT_ID, fixture.artifact_id)
        .unwrap_or_else(|error| panic!("revoke binding: {error}"));
    assert_eq!(
        fixture.control.gateway().redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            None,
            NOW + 1,
        ),
        Err(ArtifactDeliveryError::NotFound)
    );
    fixture
        .bindings
        .register(fixture.tenant_id, PROJECT_ID, fixture.artifact_id)
        .unwrap_or_else(|error| panic!("re-register binding: {error}"));
    assert_eq!(
        fixture.control.gateway().redeem_range(
            fixture.tenant_id,
            fixture.subject,
            &url,
            None,
            NOW + 2,
        ),
        Err(ArtifactDeliveryError::NotFound)
    );
}

#[test]
fn registry_and_config_limits_fail_closed() {
    assert!(ArtifactProjectRegistry::new(0).is_err());
    assert!(ArtifactDeliveryConfig::new(29, 900, 1).is_err());
    assert!(ArtifactDeliveryConfig::new(30, 901, 1).is_err());
    assert!(ArtifactDeliveryConfig::new(30, 900, 0).is_err());
    assert!(
        ArtifactDeliverySigner::new(
            "http://downloads.example/v1/artifacts",
            "p15-delivery-01",
            DELIVERY_SECRET,
            900,
        )
        .is_err()
    );
    for malformed in [
        "https://user@downloads.example/v1/artifacts",
        "https://downloads.example:bad/v1/artifacts",
        "https://downloads.example/v1/artifacts?token=x",
        "https://downloads.example/v1/artifacts#fragment",
    ] {
        assert!(
            ArtifactDeliverySigner::new(malformed, "p15-delivery-01", DELIVERY_SECRET, 900,)
                .is_err(),
            "accepted malformed base URL: {malformed}"
        );
    }
}

#[test]
fn non_artifact_tools_are_delegated_without_delivery_data() {
    let mut fixture = Fixture::new(32);
    let arguments = json!({
        "client_surface": "codex_local",
        "locale": "ko-KR",
        "request_id": "req_delegate01",
        "project_id": PROJECT_ID,
        "capabilities": ["page.paper_preset"],
        "target_profile": "hancom-hangul-2020-secondary"
    });
    let result = fixture.control.handle(McpToolRequest::new(
        "capability_check",
        fixture.bearer.clone(),
        serde_json::to_vec(&arguments)
            .unwrap_or_else(|error| panic!("serialize delegate input: {error}")),
        NOW,
    ));
    assert!(result.is_error());
    assert_eq!(result.error_code(), Some("SERVICE_REJECTED"));
    assert!(result.meta().get("hwpx/artifactDelivery").is_none());
}
