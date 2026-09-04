use std::fs;
use std::path::Path;

use auth_middleware::AuthError;
use mcp_control_plane::{
    ArtifactDeliveryError, AsyncJobError, ERROR_CATALOG_SHA256, GatewayError, PolicyError,
    PublicErrorCode, PublicErrorStage, PublicFailure, map_artifact_delivery_error,
    map_async_job_error, map_auth_error, map_gateway_error, map_policy_error,
};
use serde_json::Value;
use sha2::{Digest as _, Sha256};

fn assert_failure(
    actual: PublicFailure,
    expected_code: PublicErrorCode,
    expected_stage: PublicErrorStage,
) {
    assert_eq!(actual.code(), expected_code);
    assert_eq!(actual.stage(), expected_stage);
}

#[test]
fn embedded_catalog_is_digest_pinned_complete_and_sorted() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let bytes = fs::read(root.join("protocol/mcp/p15-public-error-catalog-v1.json"))
        .unwrap_or_else(|error| panic!("read catalog: {error}"));
    assert_eq!(hex::encode(Sha256::digest(&bytes)), ERROR_CATALOG_SHA256);
    let document: Value =
        serde_json::from_slice(&bytes).unwrap_or_else(|error| panic!("parse catalog: {error}"));
    assert_eq!(
        document.get("schema_version").and_then(Value::as_str),
        Some("hwpx-agent.public-error-catalog/v1")
    );
    let codes = document["errors"]
        .as_array()
        .unwrap_or_else(|| panic!("errors is not an array"))
        .iter()
        .map(|entry| {
            entry["error_code"]
                .as_str()
                .unwrap_or_else(|| panic!("error_code is not a string"))
        })
        .collect::<Vec<_>>();
    assert_eq!(codes.len(), PublicErrorCode::ALL.len());
    assert!(codes.windows(2).all(|pair| pair[0] < pair[1]));
    assert_eq!(
        codes,
        PublicErrorCode::ALL
            .iter()
            .map(|code| code.as_str())
            .collect::<Vec<_>>()
    );
}

#[test]
fn every_auth_error_maps_without_revealing_an_authentication_oracle() {
    let unavailable = [
        AuthError::InvalidConfiguration,
        AuthError::CapacityExceeded,
        AuthError::Conflict,
    ];
    for error in unavailable {
        assert_failure(
            map_auth_error(error),
            PublicErrorCode::AuthenticationUnavailable,
            PublicErrorStage::Authenticate,
        );
    }
    let failed = [
        AuthError::InvalidAuthorizationHeader,
        AuthError::TokenTooLarge,
        AuthError::MalformedToken,
        AuthError::UnsupportedAlgorithm,
        AuthError::UnknownKey,
        AuthError::InvalidSignature,
        AuthError::IssuerMismatch,
        AuthError::AudienceMismatch,
        AuthError::TokenExpired,
        AuthError::TokenNotYetValid,
        AuthError::TokenIssuedInFuture,
        AuthError::TokenLifetimeInvalid,
        AuthError::TokenRevoked,
        AuthError::TokenReplay,
        AuthError::UnknownPrincipal,
        AuthError::PrincipalInactive,
        AuthError::PrincipalKindDenied,
        AuthError::TenantMismatch,
        AuthError::InvalidScope,
        AuthError::ScopeDenied,
    ];
    for error in failed {
        assert_failure(
            map_auth_error(error),
            PublicErrorCode::AuthenticationFailed,
            PublicErrorStage::Authenticate,
        );
    }
}

#[test]
fn every_policy_and_gateway_error_has_one_stable_public_mapping() {
    for (error, code) in [
        (PolicyError::NotFound, PublicErrorCode::ResourceNotFound),
        (PolicyError::AccessDenied, PublicErrorCode::PolicyDenied),
        (
            PolicyError::InvalidConfiguration,
            PublicErrorCode::PolicyUnavailable,
        ),
        (PolicyError::Conflict, PublicErrorCode::PolicyUnavailable),
        (
            PolicyError::CapacityExceeded,
            PublicErrorCode::PolicyUnavailable,
        ),
    ] {
        assert_failure(map_policy_error(error), code, PublicErrorStage::Policy);
    }
    for (error, code) in [
        (GatewayError::NotFound, PublicErrorCode::ResourceNotFound),
        (GatewayError::Conflict, PublicErrorCode::RequestConflict),
        (
            GatewayError::Unavailable,
            PublicErrorCode::ServiceUnavailable,
        ),
        (GatewayError::Rejected, PublicErrorCode::ServiceRejected),
    ] {
        assert_failure(map_gateway_error(error), code, PublicErrorStage::Dispatch);
    }
}

#[test]
fn every_async_job_error_collapses_to_the_bounded_gateway_vocabulary() {
    for (error, code) in [
        (
            AsyncJobError::InvalidConfiguration,
            PublicErrorCode::ServiceRejected,
        ),
        (
            AsyncJobError::StoreCorrupt,
            PublicErrorCode::ServiceRejected,
        ),
        (
            AsyncJobError::CapacityExceeded,
            PublicErrorCode::ServiceUnavailable,
        ),
        (AsyncJobError::NotFound, PublicErrorCode::ResourceNotFound),
        (AsyncJobError::Conflict, PublicErrorCode::RequestConflict),
        (
            AsyncJobError::InvalidTransition,
            PublicErrorCode::RequestConflict,
        ),
        (
            AsyncJobError::CancellationPending,
            PublicErrorCode::RequestConflict,
        ),
        (
            AsyncJobError::StorageUnavailable,
            PublicErrorCode::ServiceUnavailable,
        ),
    ] {
        assert_failure(map_async_job_error(error), code, PublicErrorStage::Dispatch);
    }
}

#[test]
fn every_artifact_delivery_error_collapses_without_paths_tokens_or_sizes() {
    let mappings = [
        (
            ArtifactDeliveryError::InvalidConfiguration,
            PublicErrorCode::ServiceRejected,
        ),
        (
            ArtifactDeliveryError::InvalidRequest,
            PublicErrorCode::ServiceRejected,
        ),
        (
            ArtifactDeliveryError::NotFound,
            PublicErrorCode::ResourceNotFound,
        ),
        (
            ArtifactDeliveryError::AccessDenied,
            PublicErrorCode::ResourceNotFound,
        ),
        (
            ArtifactDeliveryError::NotDeliverable,
            PublicErrorCode::ResourceNotFound,
        ),
        (
            ArtifactDeliveryError::SourceUnavailable,
            PublicErrorCode::ServiceUnavailable,
        ),
        (
            ArtifactDeliveryError::IntegrityMismatch,
            PublicErrorCode::ServiceRejected,
        ),
        (
            ArtifactDeliveryError::InvalidToken,
            PublicErrorCode::ServiceRejected,
        ),
        (
            ArtifactDeliveryError::ExpiredToken,
            PublicErrorCode::ServiceRejected,
        ),
        (
            ArtifactDeliveryError::InvalidRange,
            PublicErrorCode::ServiceRejected,
        ),
        (
            ArtifactDeliveryError::RangeNotSatisfiable {
                total_bytes: 9_876_543,
            },
            PublicErrorCode::ServiceRejected,
        ),
        (
            ArtifactDeliveryError::RangeTooLarge,
            PublicErrorCode::ServiceRejected,
        ),
        (
            ArtifactDeliveryError::CapacityExceeded,
            PublicErrorCode::ServiceUnavailable,
        ),
    ];
    for (error, code) in mappings {
        assert_failure(
            map_artifact_delivery_error(error),
            code,
            PublicErrorStage::Dispatch,
        );
    }
}
