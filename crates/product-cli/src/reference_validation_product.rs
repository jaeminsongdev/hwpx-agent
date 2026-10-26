//! Read-only product path for the typed P09 reference validator.
//!
//! This operation does not write an HWPX package, update fields, repair links,
//! or access external data sources. It returns the deterministic report already
//! bound by the reference-auxiliary request and receipt.

pub mod source;
pub mod source_crossref;
pub mod source_field_semantics;
pub mod source_bookmark_results727;

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

// Separate from the original read-only operation above: these are sealed typed
// preparations, never a file mutation, full-source qualification or action permit.
use domain_ir::{DocumentId, ReferenceAuxiliaryPlan, RevisionId};

pub const REFERENCE_AUXILIARY_PREPARATION_PROFILE: &str =
    "hwpx-agent.product.reference-auxiliary-typed-preparation/v1";
pub const REFERENCE_AUXILIARY_PREPARATION_QUALIFICATION: &str =
    "caller_supplied_typed_state_and_identity_pins_only_source_completeness_target_flow_and_native_route_unverified";

/// Caller-supplied identities are bound, not authenticated by this component.
/// Actual-source assessments cannot be implicitly converted to complete state.
pub struct ReferenceAuxiliaryProductContext<'a> {
    state: &'a ReferenceAuxiliaryDocumentState,
    document_id: DocumentId,
    revision: RevisionId,
    package_sha256: [u8; 32],
    document_flow_sha256: &'a str,
}
impl std::fmt::Debug for ReferenceAuxiliaryProductContext<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("ReferenceAuxiliaryProductContext(<redacted>; caller_typed_only)")
    }
}
impl<'a> ReferenceAuxiliaryProductContext<'a> {
    #[must_use]
    pub fn new(
        state: &'a ReferenceAuxiliaryDocumentState,
        document_id: DocumentId,
        revision: RevisionId,
        package_sha256: [u8; 32],
        document_flow_sha256: &'a str,
    ) -> Self {
        Self { state, document_id, revision, package_sha256, document_flow_sha256 }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ReferenceAuxiliaryProductPreparationReceipt {
    profile: &'static str,
    qualification: &'static str,
    context_binding_sha256: String,
    request_sha256: String,
    original_domain_plan_sha256: String,
    domain_receipt: ReferenceAuxiliaryReceipt,
    source_completeness_verified: bool,
    target_document_flow_verified: bool,
    hwpx_lowered: bool,
    execution_authority_verified: bool,
    external_data_access_verified: bool,
}
impl std::fmt::Debug for ReferenceAuxiliaryProductPreparationReceipt {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ReferenceAuxiliaryProductPreparationReceipt")
            .field("capability_id", &self.domain_receipt.capability_id)
            .field("qualification", &self.qualification)
            .finish_non_exhaustive()
    }
}
impl ReferenceAuxiliaryProductPreparationReceipt {
    #[must_use]
    pub const fn domain_receipt(&self) -> &ReferenceAuxiliaryReceipt {
        &self.domain_receipt
    }
    /// # Errors
    /// Rejects oversized output before appending an over-limit JSON chunk.
    pub fn canonical_json(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Vec<u8>, ReferenceAuxiliaryProductPreparationError> {
        let mut writer = PreparationJsonWriter::new(limits, true);
        serde_json::to_writer(&mut writer, self)
            .map_err(|_| ReferenceAuxiliaryProductPreparationError::OutputLimit)?;
        writer.output.ok_or(ReferenceAuxiliaryProductPreparationError::Binding)
    }
}

/// No Deserialize or mutable access to request, plan, target or receipt.
pub struct PreparedReferenceAuxiliaryProductOperation {
    request: Vec<u8>,
    plan: ReferenceAuxiliaryPlan,
    target: ReferenceAuxiliaryDocumentState,
    receipt: ReferenceAuxiliaryProductPreparationReceipt,
    limits: ReferenceAuxiliaryLimits,
}
impl std::fmt::Debug for PreparedReferenceAuxiliaryProductOperation {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("PreparedReferenceAuxiliaryProductOperation(<redacted>; execution_unqualified)")
    }
}
impl PreparedReferenceAuxiliaryProductOperation {
    #[must_use]
    pub const fn target_state(&self) -> &ReferenceAuxiliaryDocumentState { &self.target }
    #[must_use]
    pub const fn receipt(&self) -> &ReferenceAuxiliaryProductPreparationReceipt { &self.receipt }

    /// Reconstructs the original strict request, sealed plan and complete target.
    /// # Errors
    /// Rejects fresh state/flow/document/revision/package or preparation drift.
    pub fn verify(
        &self,
        fresh: &ReferenceAuxiliaryProductContext<'_>,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<ReferenceAuxiliaryProductPreparationReceipt, ReferenceAuxiliaryProductPreparationError> {
        if limits != self.limits {
            return Err(ReferenceAuxiliaryProductPreparationError::Binding);
        }
        let rebuilt = ReferenceAuxiliaryProductPreparation::prepare_json(fresh, &self.request, limits)?;
        if self.plan != rebuilt.plan || self.target != rebuilt.target || self.receipt != rebuilt.receipt {
            return Err(ReferenceAuxiliaryProductPreparationError::Binding);
        }
        Ok(self.receipt.clone())
    }

    /// Typed preparation never supplies native/lowering/issuer authority.
    /// # Errors
    /// Always denies the route after first checking the fresh preparation.
    pub fn require_current_product_route(
        &self,
        fresh: &ReferenceAuxiliaryProductContext<'_>,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<(), ReferenceAuxiliaryProductPreparationError> {
        self.verify(fresh, limits)?;
        Err(ReferenceAuxiliaryProductPreparationError::RouteUnqualified)
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum ReferenceAuxiliaryProductPreparationError {
    #[error("REFERENCE_AUXILIARY_PREPARATION_INPUT_LIMIT")]
    InputLimit,
    #[error("REFERENCE_AUXILIARY_PREPARATION_OUTPUT_LIMIT")]
    OutputLimit,
    #[error("REFERENCE_AUXILIARY_PREPARATION_BINDING_REJECTED")]
    Binding,
    #[error("REFERENCE_AUXILIARY_PREPARATION_DOMAIN_REJECTED")]
    Domain(#[from] ReferenceAuxiliaryError),
    #[error("REFERENCE_AUXILIARY_PREPARATION_CURRENT_PRODUCT_ROUTE_UNQUALIFIED")]
    RouteUnqualified,
}

#[derive(Debug)]
pub struct ReferenceAuxiliaryProductPreparation;
impl ReferenceAuxiliaryProductPreparation {
    /// Prepares all six original auxiliary operations without changing source.
    /// The original read-only execute_json still rejects all mutation operations.
    /// # Errors
    /// Original duplicate-key, lock, identity, cache, inventory and seal checks apply.
    pub fn prepare_json(
        context: &ReferenceAuxiliaryProductContext<'_>,
        json: &[u8],
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<PreparedReferenceAuxiliaryProductOperation, ReferenceAuxiliaryProductPreparationError> {
        if json.is_empty() || json.len() > limits.config().input_bytes {
            return Err(ReferenceAuxiliaryProductPreparationError::InputLimit);
        }
        let request = ReferenceAuxiliaryRequest::from_json(
            json, context.state, context.document_flow_sha256, limits,
        )?;
        let plan = ReferenceAuxiliaryBuilder::plan(
            context.state, &request, context.document_flow_sha256, limits,
        )?;
        let built = ReferenceAuxiliaryBuilder::build(
            &plan, context.state, context.document_flow_sha256, limits,
        )?;
        if built.receipt.capability_id == "ref.reference_validate"
            && (built.receipt.source_state_sha256 != built.receipt.target_state_sha256
                || built.receipt.source_document_flow_sha256 != built.receipt.target_document_flow_sha256)
        {
            return Err(ReferenceAuxiliaryProductPreparationError::Binding);
        }
        #[derive(Serialize)]
        struct ContextBinding<'a> {
            document_id: &'a DocumentId,
            revision: &'a RevisionId,
            package_sha256: [u8; 32],
            source_state_sha256: &'a str,
            document_flow_sha256: &'a str,
            limits: [u64; 8],
        }
        let config = limits.config();
        let receipt = ReferenceAuxiliaryProductPreparationReceipt {
            profile: REFERENCE_AUXILIARY_PREPARATION_PROFILE,
            qualification: REFERENCE_AUXILIARY_PREPARATION_QUALIFICATION,
            context_binding_sha256: preparation_digest(&ContextBinding {
                document_id: &context.document_id, revision: &context.revision,
                package_sha256: context.package_sha256,
                source_state_sha256: &built.receipt.source_state_sha256,
                document_flow_sha256: context.document_flow_sha256,
                limits: [config.input_bytes as u64, config.output_bytes as u64,
                    config.text_bytes as u64, config.sections as u64, config.items_per_kind as u64,
                    config.occupied_native_ids as u64, config.opaque_entries as u64,
                    u64::from(config.extent_hwpunit)],
            }, limits)?,
            request_sha256: hex::encode(Sha256::digest(json)),
            original_domain_plan_sha256: preparation_digest(&plan, limits)?,
            domain_receipt: built.receipt,
            source_completeness_verified: false,
            target_document_flow_verified: false,
            hwpx_lowered: false,
            execution_authority_verified: false,
            external_data_access_verified: false,
        };
        let _ = preparation_digest(&receipt, limits)?;
        let mut retained = Vec::new();
        retained.try_reserve_exact(json.len())
            .map_err(|_| ReferenceAuxiliaryProductPreparationError::InputLimit)?;
        retained.extend_from_slice(json);
        Ok(PreparedReferenceAuxiliaryProductOperation {
            request: retained, plan, target: built.state, receipt, limits,
        })
    }
}

struct PreparationJsonWriter {
    output: Option<Vec<u8>>,
    hash: Sha256,
    written: usize,
    maximum: usize,
}
impl PreparationJsonWriter {
    fn new(limits: ReferenceAuxiliaryLimits, output: bool) -> Self {
        Self { output: output.then(Vec::new), hash: Sha256::new(), written: 0,
            maximum: limits.config().output_bytes }
    }
}
impl std::io::Write for PreparationJsonWriter {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        let next = self.written.checked_add(bytes.len()).filter(|size| *size <= self.maximum)
            .ok_or_else(|| std::io::Error::other("REFERENCE_AUXILIARY_PREPARATION_OUTPUT_LIMIT"))?;
        if let Some(output) = &mut self.output {
            output.try_reserve(bytes.len())
                .map_err(|_| std::io::Error::other("REFERENCE_AUXILIARY_PREPARATION_OUTPUT_LIMIT"))?;
            output.extend_from_slice(bytes);
        } else {
            self.hash.update(bytes);
        }
        self.written = next;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> std::io::Result<()> { Ok(()) }
}
fn preparation_digest(
    value: &impl Serialize,
    limits: ReferenceAuxiliaryLimits,
) -> Result<String, ReferenceAuxiliaryProductPreparationError> {
    let mut writer = PreparationJsonWriter::new(limits, false);
    serde_json::to_writer(&mut writer, value)
        .map_err(|_| ReferenceAuxiliaryProductPreparationError::OutputLimit)?;
    Ok(hex::encode(writer.hash.finalize()))
}

/// Actual preserving HWPX candidate, not promotion of the complete preparation.
pub struct ReferenceFileLiteralProductCandidate {
    preparation: ReferenceAuxiliaryProductPreparationReceipt,
    output: hwpx_package::document_import::structure::file_literal::FileLiteralOutputCandidate,
}
impl std::fmt::Debug for ReferenceFileLiteralProductCandidate {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("ReferenceFileLiteralProductCandidate(<redacted>; route_unqualified)")
    }
}
impl ReferenceFileLiteralProductCandidate {
    #[must_use]
    pub const fn preparation_receipt(&self) -> &ReferenceAuxiliaryProductPreparationReceipt { &self.preparation }
    #[must_use]
    pub const fn output_receipt(&self) -> &hwpx_package::document_import::structure::file_literal::FileLiteralOutputReceipt {
        self.output.receipt()
    }
    /// Package integrity only. Source metadata, full state, ACL/head and Native remain unqualified.
    /// # Errors
    /// Rejects writer integrity failure before invoking the callback.
    pub fn with_verified_bytes<T>(&self, consume: impl FnOnce(&[u8]) -> T) -> Result<T, hwpx_package::WriterError> {
        self.output.with_verified_bytes(consume)
    }
}
#[derive(Debug, Error)]
pub enum ReferenceFileLiteralCandidateError {
    #[error(transparent)] Preparation(#[from] ReferenceAuxiliaryProductPreparationError),
    #[error("REFERENCE_FILE_LITERAL_CANDIDATE_BINDING_REJECTED")] Binding,
    #[error("REFERENCE_FILE_LITERAL_CANDIDATE_NOT_REPRESENTABLE")] NotRepresentable,
    #[error("REFERENCE_FILE_LITERAL_CANDIDATE_LOWERING_REJECTED")] Lowering,
}
impl PreparedReferenceAuxiliaryProductOperation {
    /// Fresh original typed Request/Plan/Build -> source-bound frozen text candidate.
    /// Does not claim full auxiliary lowering or authenticate source filename/style metadata.
    /// # Errors
    /// Rejects drift, another capability, document/package/revision mismatch, ranges,
    /// unrepresented opaque/lock semantics and every original preserving-writer error.
    pub fn lower_file_name_literal_candidate(
        &self, context: &ReferenceAuxiliaryProductContext<'_>,
        source: &hwpx_package::document_import::structure::ImportedDocumentStructure,
        fresh: &[u8], limits: ReferenceAuxiliaryLimits, writer: hwpx_package::WriterLimits,
    ) -> Result<ReferenceFileLiteralProductCandidate, ReferenceFileLiteralCandidateError> {
        let receipt = self.verify(context, limits)?;
        if source.source().document_id() != &context.document_id
            || source.receipt().source_package_sha256 != context.package_sha256 {
            return Err(ReferenceFileLiteralCandidateError::Binding);
        }
        let request: domain_ir::ReferenceAuxiliaryRequestDraft = serde_json::from_slice(&self.request)
            .map_err(|_| ReferenceFileLiteralCandidateError::Binding)?;
        let domain_ir::ReferenceAuxiliaryOperation::InsertFileNameLiteral { literal, .. } = request.operation else {
            return Err(ReferenceFileLiteralCandidateError::NotRepresentable);
        };
        if literal.source_revision_sha256 != hex::encode(Sha256::digest(context.revision.as_str().as_bytes())) {
            return Err(ReferenceFileLiteralCandidateError::Binding);
        }
        if literal.anchor.start != literal.anchor.end || literal.locked || !literal.opaque_properties.is_empty() {
            return Err(ReferenceFileLiteralCandidateError::NotRepresentable);
        }
        let output = source.lower_file_literal_candidate(fresh, &literal.anchor.section_id,
            literal.anchor.start, &literal.literal, limits, writer).map_err(|_| ReferenceFileLiteralCandidateError::Lowering)?;
        Ok(ReferenceFileLiteralProductCandidate { preparation: receipt, output })
    }
}
