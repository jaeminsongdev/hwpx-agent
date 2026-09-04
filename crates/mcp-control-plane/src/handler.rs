use std::fmt;

use artifact_service::{ContentDigest, SubjectDigest, TenantId};
use auth_middleware::{AuthContext, AuthMiddleware};
use serde::Serialize;
use serde_json::{Value, json};
use thiserror::Error;
use uuid::Uuid;
use zeroize::{Zeroize, Zeroizing};

use crate::artifact_delivery::ArtifactToolDelivery;
use crate::async_jobs::JobEventPage;
use crate::catalog::{CATALOG_SHA256, CatalogError, ToolCatalog, ToolKind};
use crate::error_catalog::{
    ERROR_CATALOG_SHA256, ErrorCatalogError, PublicErrorCatalog, PublicErrorCode, PublicErrorStage,
    PublicFailure, map_auth_error, map_gateway_error, map_policy_error, map_quota_error,
};
use crate::policy::ToolPolicy;
use crate::quota::{InMemoryQuotaService, QUOTA_POLICY_SHA256, QuotaError, QuotaService};
use crate::strict_json::parse_unique_value;

pub const MAX_TOOL_NAME_BYTES: usize = 64;
pub const MAX_ARGUMENT_JSON_BYTES: usize = 262_144;

pub struct McpToolRequest {
    tool_name: String,
    authorization_header: Zeroizing<String>,
    arguments_json: Zeroizing<Vec<u8>>,
    now_unix_seconds: u64,
    fallback_request_id: String,
}

impl McpToolRequest {
    #[must_use]
    pub fn new(
        tool_name: impl Into<String>,
        authorization_header: impl Into<String>,
        arguments_json: impl Into<Vec<u8>>,
        now_unix_seconds: u64,
    ) -> Self {
        Self {
            tool_name: tool_name.into(),
            authorization_header: Zeroizing::new(authorization_header.into()),
            arguments_json: Zeroizing::new(arguments_json.into()),
            now_unix_seconds,
            fallback_request_id: format!("req_server_{}", Uuid::new_v4().simple()),
        }
    }
}

impl fmt::Debug for McpToolRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("McpToolRequest")
            .field("tool_name", &"<redacted>")
            .field("tool_name_bytes", &self.tool_name.len())
            .field("authorization_header", &"<redacted>")
            .field("arguments_json", &"<redacted>")
            .field("arguments_bytes", &self.arguments_json.len())
            .field("now_unix_seconds", &self.now_unix_seconds)
            .field("fallback_request_id", &"<redacted>")
            .finish()
    }
}

pub struct AuthorizedToolCall {
    tool: ToolKind,
    context: AuthContext,
    request_id: String,
    project_id: Option<String>,
    arguments_sha256: ContentDigest,
    arguments: Value,
    now_unix_seconds: u64,
}

impl AuthorizedToolCall {
    #[must_use]
    pub const fn tool(&self) -> ToolKind {
        self.tool
    }

    #[must_use]
    pub const fn tenant_id(&self) -> TenantId {
        self.context.tenant_id()
    }

    #[must_use]
    pub const fn subject(&self) -> SubjectDigest {
        self.context.subject()
    }

    #[must_use]
    pub fn request_id(&self) -> &str {
        &self.request_id
    }

    #[must_use]
    pub fn project_id(&self) -> Option<&str> {
        self.project_id.as_deref()
    }

    #[must_use]
    pub const fn arguments_sha256(&self) -> ContentDigest {
        self.arguments_sha256
    }

    #[must_use]
    pub const fn arguments(&self) -> &Value {
        &self.arguments
    }

    #[must_use]
    pub const fn now_unix_seconds(&self) -> u64 {
        self.now_unix_seconds
    }
}

impl fmt::Debug for AuthorizedToolCall {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AuthorizedToolCall")
            .field("tool", &self.tool)
            .field("context", &self.context)
            .field("request_id", &"<redacted>")
            .field(
                "project_id",
                &self.project_id.as_ref().map(|_| "<redacted>"),
            )
            .field("arguments_sha256", &"<redacted>")
            .field("arguments", &"<redacted>")
            .field("now_unix_seconds", &self.now_unix_seconds)
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum GatewayError {
    #[error("requested resource was not found")]
    NotFound,
    #[error("service request conflicts with current state")]
    Conflict,
    #[error("service is temporarily unavailable")]
    Unavailable,
    #[error("service rejected the request")]
    Rejected,
}

pub trait ToolServiceGateway: fmt::Debug + Send {
    /// Dispatches one fully authorized, schema-valid call.
    ///
    /// # Errors
    ///
    /// Returns only stable service categories. Implementations must re-check resource ownership at
    /// their own repository boundary and never expose raw backend errors.
    fn dispatch(&mut self, call: AuthorizedToolCall) -> Result<ToolServiceOutput, GatewayError>;
}

pub struct ToolServiceOutput {
    structured_content: Value,
    job_event_page: Option<JobEventPage>,
    artifact_delivery: Option<ArtifactToolDelivery>,
}

impl ToolServiceOutput {
    #[must_use]
    pub const fn new(structured_content: Value) -> Self {
        Self {
            structured_content,
            job_event_page: None,
            artifact_delivery: None,
        }
    }

    #[must_use]
    pub const fn with_job_event_page(
        structured_content: Value,
        job_event_page: JobEventPage,
    ) -> Self {
        Self {
            structured_content,
            job_event_page: Some(job_event_page),
            artifact_delivery: None,
        }
    }

    #[must_use]
    pub(crate) const fn with_artifact_delivery(
        structured_content: Value,
        artifact_delivery: ArtifactToolDelivery,
    ) -> Self {
        Self {
            structured_content,
            job_event_page: None,
            artifact_delivery: Some(artifact_delivery),
        }
    }
}

impl fmt::Debug for ToolServiceOutput {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ToolServiceOutput")
            .field("structured_content", &"<redacted>")
            .field("has_job_event_page", &self.job_event_page.is_some())
            .field("has_artifact_delivery", &self.artifact_delivery.is_some())
            .finish()
    }
}

pub struct McpControlPlane<P, G, Q = InMemoryQuotaService> {
    auth: AuthMiddleware,
    catalog: ToolCatalog,
    error_catalog: PublicErrorCatalog,
    policy: P,
    quota: Q,
    gateway: G,
}

impl<P, G> McpControlPlane<P, G, InMemoryQuotaService>
where
    P: ToolPolicy,
    G: ToolServiceGateway,
{
    /// Creates a control plane only when the embedded, digest-pinned catalog compiles.
    ///
    /// # Errors
    ///
    /// Fails closed on tool/error/quota catalog digest, shape, scope or JSON Schema drift.
    pub fn new(auth: AuthMiddleware, policy: P, gateway: G) -> Result<Self, InitializationError> {
        let quota = InMemoryQuotaService::new().map_err(InitializationError::Quota)?;
        Self::with_quota(auth, policy, quota, gateway)
    }
}

impl<P, G, Q> McpControlPlane<P, G, Q>
where
    P: ToolPolicy,
    G: ToolServiceGateway,
    Q: QuotaService,
{
    /// Creates a control plane with one explicitly bounded quota service.
    ///
    /// # Errors
    ///
    /// Fails closed on tool or public-error catalog drift.
    pub fn with_quota(
        auth: AuthMiddleware,
        policy: P,
        quota: Q,
        gateway: G,
    ) -> Result<Self, InitializationError> {
        Ok(Self {
            auth,
            catalog: ToolCatalog::load().map_err(InitializationError::Catalog)?,
            error_catalog: PublicErrorCatalog::load().map_err(InitializationError::ErrorCatalog)?,
            policy,
            quota,
            gateway,
        })
    }

    #[must_use]
    pub fn tool_count(&self) -> usize {
        self.catalog.len()
    }

    #[must_use]
    pub const fn gateway(&self) -> &G {
        &self.gateway
    }

    #[must_use]
    pub const fn quota(&self) -> &Q {
        &self.quota
    }

    #[must_use]
    #[allow(clippy::too_many_lines)]
    pub fn handle(&mut self, request: McpToolRequest) -> McpToolResult {
        let McpToolRequest {
            tool_name,
            authorization_header,
            arguments_json,
            now_unix_seconds,
            fallback_request_id,
        } = request;
        if tool_name.is_empty() || tool_name.len() > MAX_TOOL_NAME_BYTES {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(PublicErrorCode::ToolUnknown, PublicErrorStage::Admission),
                &fallback_request_id,
                None,
            );
        }
        let Some(tool) = ToolKind::parse(&tool_name) else {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(PublicErrorCode::ToolUnknown, PublicErrorStage::Admission),
                &fallback_request_id,
                None,
            );
        };
        if arguments_json.is_empty() || arguments_json.len() > MAX_ARGUMENT_JSON_BYTES {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolRequestTooLarge,
                    PublicErrorStage::Admission,
                ),
                &fallback_request_id,
                None,
            );
        }
        let descriptor = self.catalog.get(tool);
        let scopes = descriptor.scopes().to_vec();
        let context = match self.auth.authenticate_public_mcp(
            &authorization_header,
            now_unix_seconds,
            scopes.iter().copied(),
        ) {
            Ok(context) => context,
            Err(error) => {
                let challenge = self
                    .auth
                    .challenge(scopes.iter().copied())
                    .ok()
                    .map(|value| value.www_authenticate());
                return McpToolResult::error(
                    &self.error_catalog,
                    map_auth_error(error),
                    &fallback_request_id,
                    challenge,
                );
            }
        };
        let Ok(arguments) = parse_unique_value(&arguments_json) else {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolArgumentsMalformed,
                    PublicErrorStage::Parse,
                ),
                &fallback_request_id,
                None,
            );
        };
        if !descriptor.input_is_valid(&arguments) {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolInputSchemaInvalid,
                    PublicErrorStage::InputValidation,
                ),
                &fallback_request_id,
                None,
            );
        }
        let request_id = arguments
            .get("request_id")
            .and_then(Value::as_str)
            .map(str::to_owned);
        let Some(request_id) = request_id else {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolInputSchemaInvalid,
                    PublicErrorStage::InputValidation,
                ),
                &fallback_request_id,
                None,
            );
        };
        if let Err(error) = self.policy.authorize(&context, tool, &arguments) {
            return McpToolResult::error(
                &self.error_catalog,
                map_policy_error(error),
                &request_id,
                None,
            );
        }
        if let Err(error) = self
            .quota
            .admit(&context, tool, &arguments, now_unix_seconds)
        {
            let retry_after_seconds = error.retry_after_seconds();
            return McpToolResult::error_with_retry_after(
                &self.error_catalog,
                map_quota_error(error),
                &request_id,
                retry_after_seconds,
            );
        }
        let Ok(canonical_arguments) = serde_json::to_vec(&arguments) else {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolArgumentsMalformed,
                    PublicErrorStage::Parse,
                ),
                &request_id,
                None,
            );
        };
        let canonical_arguments = Zeroizing::new(canonical_arguments);
        let project_id = arguments
            .get("project_id")
            .and_then(Value::as_str)
            .map(str::to_owned);
        let correlation = ResultCorrelation::from_arguments(&arguments, &request_id);
        let call = AuthorizedToolCall {
            tool,
            context,
            request_id: request_id.clone(),
            project_id,
            arguments_sha256: ContentDigest::of(&canonical_arguments),
            arguments,
            now_unix_seconds,
        };
        let service_output = match self.gateway.dispatch(call) {
            Ok(output) => output,
            Err(error) => {
                return McpToolResult::error(
                    &self.error_catalog,
                    map_gateway_error(error),
                    &request_id,
                    None,
                );
            }
        };
        let ToolServiceOutput {
            structured_content: output,
            job_event_page,
            artifact_delivery,
        } = service_output;
        if job_event_page.is_some() && tool != ToolKind::JobGet {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolOutputSchemaInvalid,
                    PublicErrorStage::OutputValidation,
                ),
                &request_id,
                None,
            );
        }
        if artifact_delivery.is_some() && tool != ToolKind::ArtifactGet {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolOutputSchemaInvalid,
                    PublicErrorStage::OutputValidation,
                ),
                &request_id,
                None,
            );
        }
        if !descriptor.output_is_valid(&output) {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolOutputSchemaInvalid,
                    PublicErrorStage::OutputValidation,
                ),
                &request_id,
                None,
            );
        }
        if !correlation.matches(&output) {
            return McpToolResult::error(
                &self.error_catalog,
                PublicFailure::new(
                    PublicErrorCode::ToolResultCorrelationMismatch,
                    PublicErrorStage::OutputValidation,
                ),
                &request_id,
                None,
            );
        }
        McpToolResult::success(tool, &request_id, output, job_event_page, artifact_delivery)
    }
}

impl<P, G, Q> fmt::Debug for McpControlPlane<P, G, Q>
where
    P: ToolPolicy,
    G: ToolServiceGateway,
    Q: QuotaService,
{
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("McpControlPlane")
            .field("auth", &self.auth)
            .field("catalog", &self.catalog)
            .field("error_catalog", &self.error_catalog)
            .field("policy", &self.policy)
            .field("quota", &self.quota)
            .field("gateway", &self.gateway)
            .finish()
    }
}

#[derive(Debug, Error)]
pub enum InitializationError {
    #[error("public tool catalog initialization failed")]
    Catalog(#[source] CatalogError),
    #[error("public error catalog initialization failed")]
    ErrorCatalog(#[source] ErrorCatalogError),
    #[error("quota service initialization failed")]
    Quota(#[source] QuotaError),
}

#[derive(Serialize)]
pub struct McpToolResult {
    #[serde(rename = "structuredContent")]
    structured_content: Value,
    content: Vec<Value>,
    #[serde(rename = "_meta")]
    meta: Value,
    #[serde(rename = "isError")]
    is_error: bool,
}

impl McpToolResult {
    fn success(
        tool: ToolKind,
        request_id: &str,
        output: Value,
        job_event_page: Option<JobEventPage>,
        artifact_delivery: Option<ArtifactToolDelivery>,
    ) -> Self {
        let mut meta = serde_json::Map::new();
        meta.insert(
            "hwpx/catalogSha256".to_owned(),
            Value::String(CATALOG_SHA256.to_owned()),
        );
        meta.insert(
            "hwpx/errorCatalogSha256".to_owned(),
            Value::String(ERROR_CATALOG_SHA256.to_owned()),
        );
        meta.insert(
            "hwpx/quotaPolicySha256".to_owned(),
            Value::String(QUOTA_POLICY_SHA256.to_owned()),
        );
        meta.insert(
            "hwpx/requestId".to_owned(),
            Value::String(request_id.to_owned()),
        );
        if let Some(page) = job_event_page {
            page.append_to_meta(&mut meta);
        }
        let mut content = vec![json!({
            "type": "text",
            "text": format!(
                "{} completed with a validated structured result.",
                tool.name()
            ),
        })];
        if let Some(delivery) = artifact_delivery {
            delivery.append_to_result(&mut content, &mut meta);
        }
        Self {
            structured_content: output,
            content,
            meta: Value::Object(meta),
            is_error: false,
        }
    }

    fn error(
        catalog: &PublicErrorCatalog,
        failure: PublicFailure,
        request_id: &str,
        authentication_challenge: Option<String>,
    ) -> Self {
        Self::error_with_metadata(catalog, failure, request_id, authentication_challenge, None)
    }

    fn error_with_retry_after(
        catalog: &PublicErrorCatalog,
        failure: PublicFailure,
        request_id: &str,
        retry_after_seconds: Option<u64>,
    ) -> Self {
        Self::error_with_metadata(catalog, failure, request_id, None, retry_after_seconds)
    }

    fn error_with_metadata(
        catalog: &PublicErrorCatalog,
        failure: PublicFailure,
        request_id: &str,
        authentication_challenge: Option<String>,
        retry_after_seconds: Option<u64>,
    ) -> Self {
        let descriptor = catalog.descriptor(failure);
        let mut meta = serde_json::Map::new();
        meta.insert(
            "hwpx/catalogSha256".to_owned(),
            Value::String(CATALOG_SHA256.to_owned()),
        );
        meta.insert(
            "hwpx/errorCatalogSha256".to_owned(),
            Value::String(ERROR_CATALOG_SHA256.to_owned()),
        );
        meta.insert(
            "hwpx/quotaPolicySha256".to_owned(),
            Value::String(QUOTA_POLICY_SHA256.to_owned()),
        );
        meta.insert(
            "hwpx/requestId".to_owned(),
            Value::String(request_id.to_owned()),
        );
        if let Some(challenge) = authentication_challenge {
            meta.insert("mcp/www_authenticate".to_owned(), json!([challenge]));
        }
        if let Some(retry_after_seconds) = retry_after_seconds {
            meta.insert(
                "hwpx/retryAfterSeconds".to_owned(),
                Value::from(retry_after_seconds),
            );
        }
        let safe_message = descriptor.safe_message();
        Self {
            structured_content: json!({
                "schema_version": "hwpx-agent.error/v2",
                "request_id": request_id,
                "error_code": descriptor.error_code().as_str(),
                "category": descriptor.category().as_str(),
                "safe_message": safe_message,
                "retryable": descriptor.retryable(),
                "stage": failure.stage().as_str(),
                "details": {},
                "recovery": [{"action": descriptor.recovery_action().as_str()}],
            }),
            content: vec![json!({"type": "text", "text": safe_message})],
            meta: Value::Object(meta),
            is_error: true,
        }
    }

    #[must_use]
    pub const fn structured_content(&self) -> &Value {
        &self.structured_content
    }

    #[must_use]
    pub fn content_text(&self) -> &str {
        self.content[0]
            .get("text")
            .and_then(Value::as_str)
            .unwrap_or_default()
    }

    #[must_use]
    pub const fn meta(&self) -> &Value {
        &self.meta
    }

    #[must_use]
    pub const fn is_error(&self) -> bool {
        self.is_error
    }

    #[must_use]
    pub fn error_code(&self) -> Option<&str> {
        self.structured_content
            .get("error_code")
            .and_then(Value::as_str)
    }
}

impl Drop for McpToolResult {
    fn drop(&mut self) {
        if let Some(Value::String(signed_url)) = self
            .meta
            .get_mut("hwpx/artifactDelivery")
            .and_then(|delivery| delivery.get_mut("signedUrl"))
        {
            signed_url.zeroize();
        }
    }
}

impl fmt::Debug for McpToolResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("McpToolResult")
            .field("is_error", &self.is_error)
            .field("error_code", &self.error_code())
            .field("structured_content", &"<redacted>")
            .field("content", &"<redacted>")
            .field("meta", &"<redacted>")
            .finish()
    }
}

struct ResultCorrelation {
    required_equal_fields: Vec<(&'static str, String)>,
}

impl ResultCorrelation {
    fn from_arguments(arguments: &Value, request_id: &str) -> Self {
        let mut required_equal_fields = vec![("request_id", request_id.to_owned())];
        for field in ["project_id", "job_id", "revision_id", "release_label"] {
            if let Some(value) = arguments.get(field).and_then(Value::as_str) {
                required_equal_fields.push((field, value.to_owned()));
            }
        }
        Self {
            required_equal_fields,
        }
    }

    fn matches(&self, output: &Value) -> bool {
        self.required_equal_fields.iter().all(|(field, expected)| {
            output
                .get(*field)
                .is_none_or(|actual| actual.as_str().is_some_and(|actual| actual == expected))
        })
    }
}
