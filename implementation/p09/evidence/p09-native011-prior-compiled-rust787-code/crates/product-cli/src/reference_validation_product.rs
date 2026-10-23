//! Read-only product path for the typed P09 reference validator.
//!
//! This operation does not write an HWPX package, update fields, repair links,
//! or access external data sources. It returns the deterministic report already
//! bound by the reference-auxiliary request and receipt.

use domain_ir::{
    ReferenceAuxiliaryBuilder, ReferenceAuxiliaryDocumentState, ReferenceAuxiliaryError,
    ReferenceAuxiliaryLimits, ReferenceAuxiliaryReceipt, ReferenceAuxiliaryRequest,
    ReferenceValidationReport,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const REFERENCE_VALIDATION_PRODUCT_PROFILE_ID: &str =
    "hwpx-agent.product.reference-validation-read-only/v1";
pub const REFERENCE_VALIDATION_PRODUCT_RESULT_SCHEMA_VERSION: &str =
    "hwpx-agent.product.reference-validation-result/v1";
pub const REFERENCE_VALIDATION_PRODUCT_QUALIFICATION: &str =
    "caller_supplied_typed_state_only_source_completeness_unverified";

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ReferenceValidationProductResult {
    pub schema_version: &'static str,
    pub profile_id: &'static str,
    pub qualification: &'static str,
    pub request_sha256: String,
    pub domain_receipt: ReferenceAuxiliaryReceipt,
    pub report_sha256: String,
    pub report: ReferenceValidationReport,
}

impl ReferenceValidationProductResult {
    /// Serializes the product response within the same bounded output limit.
    ///
    /// # Errors
    /// Returns a bounded-output error without exposing source data in diagnostics.
    pub fn canonical_json(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Vec<u8>, ReferenceValidationProductError> {
        let bytes =
            serde_json::to_vec(self).map_err(|_| ReferenceValidationProductError::Serialization)?;
        if bytes.len() > limits.config().output_bytes {
            return Err(ReferenceValidationProductError::OutputLimit);
        }
        Ok(bytes)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum ReferenceValidationProductError {
    #[error("REFERENCE_VALIDATION_PRODUCT_INPUT_REJECTED")]
    Request,
    #[error("REFERENCE_VALIDATION_PRODUCT_INPUT_LIMIT")]
    InputLimit,
    #[error("REFERENCE_VALIDATION_PRODUCT_READ_ONLY_CAPABILITY_REQUIRED")]
    UnsupportedCapability,
    #[error("REFERENCE_VALIDATION_PRODUCT_BINDING_REJECTED")]
    Binding,
    #[error("REFERENCE_VALIDATION_PRODUCT_OUTPUT_LIMIT")]
    OutputLimit,
    #[error("REFERENCE_VALIDATION_PRODUCT_SERIALIZATION_FAILED")]
    Serialization,
}

#[derive(Debug)]
pub struct ReferenceValidationProductOperation;

impl ReferenceValidationProductOperation {
    /// Executes only `ref.reference_validate` against the exact typed state and flow.
    ///
    /// The JSON preflight is only a capability filter. Accepted requests are
    /// still parsed by `ReferenceAuxiliaryRequest::from_json`, which performs
    /// the domain's bounded, duplicate-key rejecting validation.
    ///
    /// # Errors
    /// Rejects malformed or drifting requests, mutation capabilities, receipt
    /// mismatches, and bounded serialization failures. No package or external
    /// source is read or written.
    pub fn execute_json(
        source: &ReferenceAuxiliaryDocumentState,
        current_document_flow_sha256: &str,
        request_json: &[u8],
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<ReferenceValidationProductResult, ReferenceValidationProductError> {
        if request_json.is_empty() || request_json.len() > limits.config().input_bytes {
            return Err(ReferenceValidationProductError::InputLimit);
        }
        let preview: serde_json::Value = serde_json::from_slice(request_json)
            .map_err(|_| ReferenceValidationProductError::Request)?;
        let operation = preview
            .get("operation")
            .ok_or(ReferenceValidationProductError::Request)?;
        let capability = operation
            .get("kind")
            .and_then(serde_json::Value::as_str)
            .ok_or(ReferenceValidationProductError::Request)?;
        if capability != "validate_references" {
            return Err(ReferenceValidationProductError::UnsupportedCapability);
        }

        let request = ReferenceAuxiliaryRequest::from_json(
            request_json,
            source,
            current_document_flow_sha256,
            limits,
        )
        .map_err(map_domain_error)?;
        let plan =
            ReferenceAuxiliaryBuilder::plan(source, &request, current_document_flow_sha256, limits)
                .map_err(map_domain_error)?;
        let built =
            ReferenceAuxiliaryBuilder::build(&plan, source, current_document_flow_sha256, limits)
                .map_err(|_| ReferenceValidationProductError::Binding)?;
        let report = built
            .state
            .validate_references(limits)
            .map_err(|_| ReferenceValidationProductError::Binding)?;
        let report_sha256 = report
            .canonical_sha256(limits)
            .map_err(|_| ReferenceValidationProductError::Binding)?;
        if built.receipt.capability_id != "ref.reference_validate"
            || built.receipt.validation_report_sha256.as_deref() != Some(report_sha256.as_str())
            || built.receipt.source_state_sha256 != built.receipt.target_state_sha256
            || built.receipt.source_document_flow_sha256
                != built.receipt.target_document_flow_sha256
        {
            return Err(ReferenceValidationProductError::Binding);
        }

        Ok(ReferenceValidationProductResult {
            schema_version: REFERENCE_VALIDATION_PRODUCT_RESULT_SCHEMA_VERSION,
            profile_id: REFERENCE_VALIDATION_PRODUCT_PROFILE_ID,
            qualification: REFERENCE_VALIDATION_PRODUCT_QUALIFICATION,
            request_sha256: hex::encode(Sha256::digest(request_json)),
            domain_receipt: built.receipt,
            report_sha256,
            report,
        })
    }
}

fn map_domain_error(error: ReferenceAuxiliaryError) -> ReferenceValidationProductError {
    match error {
        ReferenceAuxiliaryError::InputLimit => ReferenceValidationProductError::InputLimit,
        ReferenceAuxiliaryError::OutputLimit => ReferenceValidationProductError::OutputLimit,
        ReferenceAuxiliaryError::SourceStateDrift
        | ReferenceAuxiliaryError::DocumentFlowDrift
        | ReferenceAuxiliaryError::ValidationReportDrift
        | ReferenceAuxiliaryError::PlanTampered => ReferenceValidationProductError::Binding,
        _ => ReferenceValidationProductError::Request,
    }
}
