use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use auth_middleware::AuthError;
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::artifact_delivery::ArtifactDeliveryError;
use crate::async_jobs::AsyncJobError;
use crate::handler::GatewayError;
use crate::policy::PolicyError;
use crate::quota::QuotaError;
use crate::strict_json::parse_unique_value;

const CATALOG_BYTES: &[u8] =
    include_bytes!("../../../protocol/mcp/p15-public-error-catalog-v2.json");
const CATALOG_SCHEMA_VERSION: &str = "hwpx-agent.public-error-catalog/v2";
const MAX_SAFE_MESSAGE_BYTES: usize = 200;

pub const ERROR_CATALOG_SHA256: &str =
    "ac1eaf53e79f70a7bf35ba8aafa5e8f3e684a2a0df378a02fa1194384e31e849";
pub const P15_06_ERROR_CATALOG_SHA256: &str =
    "7f85fb7a5c116ba6a262a5595906ccf3abf23df28ab5a567551f6904121ee2b7";

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PublicErrorCode {
    AuthenticationFailed,
    AuthenticationUnavailable,
    PolicyDenied,
    PolicyUnavailable,
    QuotaExceeded,
    QuotaUnavailable,
    RequestConflict,
    ResourceNotFound,
    ServiceRejected,
    ServiceUnavailable,
    ToolArgumentsMalformed,
    ToolInputSchemaInvalid,
    ToolOutputSchemaInvalid,
    ToolRequestTooLarge,
    ToolResultCorrelationMismatch,
    ToolUnknown,
}

impl PublicErrorCode {
    pub const ALL: [Self; 16] = [
        Self::AuthenticationFailed,
        Self::AuthenticationUnavailable,
        Self::PolicyDenied,
        Self::PolicyUnavailable,
        Self::QuotaExceeded,
        Self::QuotaUnavailable,
        Self::RequestConflict,
        Self::ResourceNotFound,
        Self::ServiceRejected,
        Self::ServiceUnavailable,
        Self::ToolArgumentsMalformed,
        Self::ToolInputSchemaInvalid,
        Self::ToolOutputSchemaInvalid,
        Self::ToolRequestTooLarge,
        Self::ToolResultCorrelationMismatch,
        Self::ToolUnknown,
    ];

    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::AuthenticationFailed => "AUTHENTICATION_FAILED",
            Self::AuthenticationUnavailable => "AUTHENTICATION_UNAVAILABLE",
            Self::PolicyDenied => "POLICY_DENIED",
            Self::PolicyUnavailable => "POLICY_UNAVAILABLE",
            Self::QuotaExceeded => "QUOTA_EXCEEDED",
            Self::QuotaUnavailable => "QUOTA_UNAVAILABLE",
            Self::RequestConflict => "REQUEST_CONFLICT",
            Self::ResourceNotFound => "RESOURCE_NOT_FOUND",
            Self::ServiceRejected => "SERVICE_REJECTED",
            Self::ServiceUnavailable => "SERVICE_UNAVAILABLE",
            Self::ToolArgumentsMalformed => "TOOL_ARGUMENTS_MALFORMED",
            Self::ToolInputSchemaInvalid => "TOOL_INPUT_SCHEMA_INVALID",
            Self::ToolOutputSchemaInvalid => "TOOL_OUTPUT_SCHEMA_INVALID",
            Self::ToolRequestTooLarge => "TOOL_REQUEST_TOO_LARGE",
            Self::ToolResultCorrelationMismatch => "TOOL_RESULT_CORRELATION_MISMATCH",
            Self::ToolUnknown => "TOOL_UNKNOWN",
        }
    }

    const fn expected_category(self) -> PublicErrorCategory {
        match self {
            Self::AuthenticationFailed
            | Self::AuthenticationUnavailable
            | Self::PolicyDenied
            | Self::PolicyUnavailable => PublicErrorCategory::Security,
            Self::QuotaExceeded => PublicErrorCategory::Storage,
            Self::RequestConflict => PublicErrorCategory::Conflict,
            Self::ResourceNotFound => PublicErrorCategory::Document,
            Self::QuotaUnavailable | Self::ServiceRejected | Self::ServiceUnavailable => {
                PublicErrorCategory::Backend
            }
            Self::ToolArgumentsMalformed
            | Self::ToolInputSchemaInvalid
            | Self::ToolRequestTooLarge
            | Self::ToolUnknown => PublicErrorCategory::Input,
            Self::ToolOutputSchemaInvalid | Self::ToolResultCorrelationMismatch => {
                PublicErrorCategory::Internal
            }
        }
    }

    const fn expected_stages(self) -> &'static [PublicErrorStage] {
        match self {
            Self::AuthenticationFailed | Self::AuthenticationUnavailable => {
                &[PublicErrorStage::Authenticate]
            }
            Self::PolicyDenied | Self::PolicyUnavailable => &[PublicErrorStage::Policy],
            Self::QuotaExceeded | Self::QuotaUnavailable => &[PublicErrorStage::Quota],
            Self::RequestConflict => &[PublicErrorStage::Quota, PublicErrorStage::Dispatch],
            Self::ServiceRejected | Self::ServiceUnavailable => &[PublicErrorStage::Dispatch],
            Self::ResourceNotFound => &[PublicErrorStage::Policy, PublicErrorStage::Dispatch],
            Self::ToolArgumentsMalformed => &[PublicErrorStage::Parse],
            Self::ToolInputSchemaInvalid => &[PublicErrorStage::InputValidation],
            Self::ToolOutputSchemaInvalid | Self::ToolResultCorrelationMismatch => {
                &[PublicErrorStage::OutputValidation]
            }
            Self::ToolRequestTooLarge | Self::ToolUnknown => &[PublicErrorStage::Admission],
        }
    }

    const fn expected_retryable(self) -> bool {
        matches!(
            self,
            Self::AuthenticationUnavailable
                | Self::PolicyUnavailable
                | Self::QuotaExceeded
                | Self::QuotaUnavailable
                | Self::ServiceUnavailable
        )
    }

    const fn expected_recovery(self) -> RecoveryAction {
        match self {
            Self::AuthenticationFailed => RecoveryAction::Reauthenticate,
            Self::AuthenticationUnavailable
            | Self::PolicyUnavailable
            | Self::QuotaExceeded
            | Self::QuotaUnavailable
            | Self::ServiceUnavailable => RecoveryAction::RetryLater,
            Self::PolicyDenied => RecoveryAction::RequestAccess,
            Self::RequestConflict | Self::ResourceNotFound => RecoveryAction::RefreshResource,
            Self::ServiceRejected => RecoveryAction::InspectRequest,
            Self::ToolArgumentsMalformed | Self::ToolInputSchemaInvalid => {
                RecoveryAction::FixRequest
            }
            Self::ToolOutputSchemaInvalid | Self::ToolResultCorrelationMismatch => {
                RecoveryAction::ContactSupport
            }
            Self::ToolRequestTooLarge => RecoveryAction::ReduceRequest,
            Self::ToolUnknown => RecoveryAction::UseSupportedTool,
        }
    }

    const fn expected_safe_message(self) -> &'static str {
        match self {
            Self::AuthenticationFailed => "Authentication is required for this tool.",
            Self::AuthenticationUnavailable => {
                "The authentication service is temporarily unavailable."
            }
            Self::PolicyDenied => "The requested operation is not allowed.",
            Self::PolicyUnavailable => "The authorization policy could not approve the request.",
            Self::QuotaExceeded => "The request quota is temporarily exhausted.",
            Self::QuotaUnavailable => "The quota service is temporarily unavailable.",
            Self::RequestConflict => "The request conflicts with the current resource state.",
            Self::ResourceNotFound => "The requested resource was not found.",
            Self::ServiceRejected => "The service rejected the request.",
            Self::ServiceUnavailable => "The service is temporarily unavailable.",
            Self::ToolArgumentsMalformed => "The tool arguments are not valid JSON.",
            Self::ToolInputSchemaInvalid => "The tool arguments do not match the public contract.",
            Self::ToolOutputSchemaInvalid => "The service returned an invalid result.",
            Self::ToolRequestTooLarge => "The tool request exceeds the allowed size.",
            Self::ToolResultCorrelationMismatch => "The service result did not match the request.",
            Self::ToolUnknown => "The requested tool is not available.",
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PublicErrorCategory {
    Input,
    Capability,
    Conflict,
    Document,
    Security,
    Backend,
    Validation,
    Storage,
    External,
    Internal,
}

impl PublicErrorCategory {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Input => "input",
            Self::Capability => "capability",
            Self::Conflict => "conflict",
            Self::Document => "document",
            Self::Security => "security",
            Self::Backend => "backend",
            Self::Validation => "validation",
            Self::Storage => "storage",
            Self::External => "external",
            Self::Internal => "internal",
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PublicErrorStage {
    Admission,
    Authenticate,
    Parse,
    InputValidation,
    Policy,
    Quota,
    Dispatch,
    OutputValidation,
}

impl PublicErrorStage {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Admission => "admission",
            Self::Authenticate => "authenticate",
            Self::Parse => "parse",
            Self::InputValidation => "input_validation",
            Self::Policy => "policy",
            Self::Quota => "quota",
            Self::Dispatch => "dispatch",
            Self::OutputValidation => "output_validation",
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RecoveryAction {
    ContactSupport,
    FixRequest,
    InspectRequest,
    Reauthenticate,
    ReduceRequest,
    RefreshResource,
    RequestAccess,
    RetryLater,
    UseSupportedTool,
}

impl RecoveryAction {
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ContactSupport => "contact_support",
            Self::FixRequest => "fix_request",
            Self::InspectRequest => "inspect_request",
            Self::Reauthenticate => "reauthenticate",
            Self::ReduceRequest => "reduce_request",
            Self::RefreshResource => "refresh_resource",
            Self::RequestAccess => "request_access",
            Self::RetryLater => "retry_later",
            Self::UseSupportedTool => "use_supported_tool",
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PublicErrorDescriptor {
    error_code: PublicErrorCode,
    category: PublicErrorCategory,
    allowed_stages: Vec<PublicErrorStage>,
    retryable: bool,
    safe_message: String,
    recovery_action: RecoveryAction,
}

impl PublicErrorDescriptor {
    #[must_use]
    pub const fn error_code(&self) -> PublicErrorCode {
        self.error_code
    }

    #[must_use]
    pub const fn category(&self) -> PublicErrorCategory {
        self.category
    }

    #[must_use]
    pub fn allowed_stages(&self) -> &[PublicErrorStage] {
        &self.allowed_stages
    }

    #[must_use]
    pub const fn retryable(&self) -> bool {
        self.retryable
    }

    #[must_use]
    pub fn safe_message(&self) -> &str {
        &self.safe_message
    }

    #[must_use]
    pub const fn recovery_action(&self) -> RecoveryAction {
        self.recovery_action
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PublicFailure {
    code: PublicErrorCode,
    stage: PublicErrorStage,
}

impl PublicFailure {
    #[must_use]
    pub(crate) const fn new(code: PublicErrorCode, stage: PublicErrorStage) -> Self {
        Self { code, stage }
    }

    #[must_use]
    pub const fn code(self) -> PublicErrorCode {
        self.code
    }

    #[must_use]
    pub const fn stage(self) -> PublicErrorStage {
        self.stage
    }
}

#[derive(Debug, Error)]
pub enum ErrorCatalogError {
    #[error("embedded public error catalog is invalid")]
    InvalidEmbeddedCatalog,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CatalogDocument {
    schema_version: String,
    errors: Vec<PublicErrorDescriptor>,
}

pub(crate) struct PublicErrorCatalog {
    descriptors: BTreeMap<PublicErrorCode, PublicErrorDescriptor>,
}

impl PublicErrorCatalog {
    pub(crate) fn load() -> Result<Self, ErrorCatalogError> {
        if hex::encode(Sha256::digest(CATALOG_BYTES)) != ERROR_CATALOG_SHA256 {
            return Err(ErrorCatalogError::InvalidEmbeddedCatalog);
        }
        let value = parse_unique_value(CATALOG_BYTES)
            .map_err(|()| ErrorCatalogError::InvalidEmbeddedCatalog)?;
        let document: CatalogDocument =
            serde_json::from_value(value).map_err(|_| ErrorCatalogError::InvalidEmbeddedCatalog)?;
        if document.schema_version != CATALOG_SCHEMA_VERSION
            || document.errors.len() != PublicErrorCode::ALL.len()
        {
            return Err(ErrorCatalogError::InvalidEmbeddedCatalog);
        }
        let mut descriptors = BTreeMap::new();
        let mut previous_code = None;
        for descriptor in document.errors {
            let code = descriptor.error_code;
            if previous_code.is_some_and(|previous| previous >= code)
                || descriptor.category != code.expected_category()
                || descriptor.allowed_stages != code.expected_stages()
                || descriptor.retryable != code.expected_retryable()
                || descriptor.recovery_action != code.expected_recovery()
                || descriptor.safe_message != code.expected_safe_message()
                || descriptor.safe_message.is_empty()
                || descriptor.safe_message.len() > MAX_SAFE_MESSAGE_BYTES
                || !descriptor
                    .safe_message
                    .bytes()
                    .all(|byte| (0x20..=0x7e).contains(&byte))
                || descriptors.insert(code, descriptor).is_some()
            {
                return Err(ErrorCatalogError::InvalidEmbeddedCatalog);
            }
            previous_code = Some(code);
        }
        if descriptors.keys().copied().collect::<BTreeSet<_>>()
            != PublicErrorCode::ALL.into_iter().collect()
        {
            return Err(ErrorCatalogError::InvalidEmbeddedCatalog);
        }
        Ok(Self { descriptors })
    }

    pub(crate) fn descriptor(&self, failure: PublicFailure) -> &PublicErrorDescriptor {
        let descriptor = &self.descriptors[&failure.code];
        debug_assert!(descriptor.allowed_stages.contains(&failure.stage));
        descriptor
    }
}

impl fmt::Debug for PublicErrorCatalog {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PublicErrorCatalog")
            .field("schema_version", &CATALOG_SCHEMA_VERSION)
            .field("sha256", &ERROR_CATALOG_SHA256)
            .field("entries", &self.descriptors.len())
            .finish()
    }
}

#[must_use]
pub const fn map_auth_error(error: AuthError) -> PublicFailure {
    let code = match error {
        AuthError::InvalidConfiguration | AuthError::CapacityExceeded | AuthError::Conflict => {
            PublicErrorCode::AuthenticationUnavailable
        }
        AuthError::InvalidAuthorizationHeader
        | AuthError::TokenTooLarge
        | AuthError::MalformedToken
        | AuthError::UnsupportedAlgorithm
        | AuthError::UnknownKey
        | AuthError::InvalidSignature
        | AuthError::IssuerMismatch
        | AuthError::AudienceMismatch
        | AuthError::TokenExpired
        | AuthError::TokenNotYetValid
        | AuthError::TokenIssuedInFuture
        | AuthError::TokenLifetimeInvalid
        | AuthError::TokenRevoked
        | AuthError::TokenReplay
        | AuthError::UnknownPrincipal
        | AuthError::PrincipalInactive
        | AuthError::PrincipalKindDenied
        | AuthError::TenantMismatch
        | AuthError::InvalidScope
        | AuthError::ScopeDenied => PublicErrorCode::AuthenticationFailed,
    };
    PublicFailure::new(code, PublicErrorStage::Authenticate)
}

#[must_use]
pub const fn map_policy_error(error: PolicyError) -> PublicFailure {
    let code = match error {
        PolicyError::NotFound => PublicErrorCode::ResourceNotFound,
        PolicyError::AccessDenied => PublicErrorCode::PolicyDenied,
        PolicyError::InvalidConfiguration
        | PolicyError::Conflict
        | PolicyError::CapacityExceeded => PublicErrorCode::PolicyUnavailable,
    };
    PublicFailure::new(code, PublicErrorStage::Policy)
}

#[must_use]
pub const fn map_gateway_error(error: GatewayError) -> PublicFailure {
    let code = match error {
        GatewayError::NotFound => PublicErrorCode::ResourceNotFound,
        GatewayError::Conflict => PublicErrorCode::RequestConflict,
        GatewayError::Unavailable => PublicErrorCode::ServiceUnavailable,
        GatewayError::Rejected => PublicErrorCode::ServiceRejected,
    };
    PublicFailure::new(code, PublicErrorStage::Dispatch)
}

#[must_use]
pub const fn map_quota_error(error: QuotaError) -> PublicFailure {
    let code = match error {
        QuotaError::Exhausted { .. } => PublicErrorCode::QuotaExceeded,
        QuotaError::IdempotencyConflict => PublicErrorCode::RequestConflict,
        QuotaError::InvalidConfiguration
        | QuotaError::StateUnavailable
        | QuotaError::StateCapacityExceeded => PublicErrorCode::QuotaUnavailable,
    };
    PublicFailure::new(code, PublicErrorStage::Quota)
}

#[must_use]
pub fn map_async_job_error(error: AsyncJobError) -> PublicFailure {
    map_gateway_error(error.into())
}

#[must_use]
pub fn map_artifact_delivery_error(error: ArtifactDeliveryError) -> PublicFailure {
    map_gateway_error(error.into())
}
