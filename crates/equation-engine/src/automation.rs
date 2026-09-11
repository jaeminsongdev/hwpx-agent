use std::fmt;

use domain_ir::{MathAst, MathAstDraft, MathAstLimits};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{EqEditEngine, EqEditError, EqEditLimits};

pub const EQUATION_AUTOMATION_SCHEMA_VERSION: &str = "hwpx-agent.equation-automation/v1";
pub const EQUATION_AUTOMATION_PROFILE_VERSION: &str =
    "hwpx-agent.equation-automation.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
pub const EQUATION_AUTOMATION_RECEIPT_SCHEMA_VERSION: &str =
    "hwpx-agent.equation-automation-receipt/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EquationAutomationLimitConfig {
    pub request_bytes: usize,
    pub revision_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for EquationAutomationLimitConfig {
    fn default() -> Self {
        Self {
            request_bytes: 8 * 1024 * 1024,
            revision_bytes: 512,
            serialized_bytes: 16 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct EquationAutomationLimits(EquationAutomationLimitConfig);

impl EquationAutomationLimits {
    pub const HARD_MAX_REQUEST_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_REVISION_BYTES: usize = 4 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;

    /// Creates finite request and receipt limits for the P07-06 boundary.
    ///
    /// # Errors
    ///
    /// Returns [`EquationAutomationError::InvalidLimit`] for zero, inconsistent, or hard-ceiling
    /// exceeding values.
    pub fn new(config: EquationAutomationLimitConfig) -> Result<Self, EquationAutomationError> {
        if config.request_bytes == 0
            || config.request_bytes > Self::HARD_MAX_REQUEST_BYTES
            || config.revision_bytes == 0
            || config.revision_bytes > Self::HARD_MAX_REVISION_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.serialized_bytes < config.request_bytes
        {
            return Err(EquationAutomationError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> EquationAutomationLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationAutomationSelection {
    pub object_id: u32,
    pub semantic_sha256: String,
}

impl fmt::Debug for EquationAutomationSelection {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationAutomationSelection")
            .field("object_id", &"<redacted>")
            .field("semantic_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationAutomationSourceState {
    pub revision: String,
    pub package_graph_sha256: String,
    pub document_flow_sha256: String,
    pub anchor_fingerprint_sha256: String,
    pub selected_equation: Option<EquationAutomationSelection>,
}

impl fmt::Debug for EquationAutomationSourceState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationAutomationSourceState")
            .field("revision", &"<redacted>")
            .field("package_graph_sha256", &"<redacted>")
            .field("document_flow_sha256", &"<redacted>")
            .field("anchor_fingerprint_sha256", &"<redacted>")
            .field(
                "selected_equation",
                &self.selected_equation.as_ref().map(|_| "<redacted>"),
            )
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum EquationAutomationOperationDraft {
    InsertNative {
        math_ast: MathAstDraft,
    },
    EditNative {
        object_id: u32,
        expected_semantic_sha256: String,
        math_ast: MathAstDraft,
    },
    ReadbackNative {
        object_id: u32,
        expected_semantic_sha256: String,
    },
}

impl fmt::Debug for EquationAutomationOperationDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let kind = match self {
            Self::InsertNative { .. } => "insert_native",
            Self::EditNative { .. } => "edit_native",
            Self::ReadbackNative { .. } => "readback_native",
        };
        formatter
            .debug_struct("EquationAutomationOperationDraft")
            .field("kind", &kind)
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EquationAutomationTarget {
    pub schema_version: String,
    pub profile_version: String,
    pub binding_set_sha256: String,
    pub source: EquationAutomationSourceState,
    pub operation: EquationAutomationOperationDraft,
}

impl fmt::Debug for EquationAutomationTarget {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationAutomationTarget")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("binding_set_sha256", &"<redacted>")
            .field("source", &"<redacted>")
            .field("operation", &self.operation)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum EquationAutomationOperation {
    #[serde(rename = "insert_native")]
    Insert {
        capability_id: &'static str,
        semantic_sha256: String,
        script_sha256: String,
        script: String,
    },
    #[serde(rename = "edit_native")]
    Edit {
        capability_id: &'static str,
        object_id: u32,
        expected_semantic_sha256: String,
        semantic_sha256: String,
        script_sha256: String,
        script: String,
    },
    #[serde(rename = "readback_native")]
    Readback {
        capability_id: &'static str,
        object_id: u32,
        expected_semantic_sha256: String,
    },
}

impl fmt::Debug for EquationAutomationOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let (kind, capability_id) = match self {
            Self::Insert { capability_id, .. } => ("insert_native", capability_id),
            Self::Edit { capability_id, .. } => ("edit_native", capability_id),
            Self::Readback { capability_id, .. } => ("readback_native", capability_id),
        };
        formatter
            .debug_struct("EquationAutomationOperation")
            .field("kind", &kind)
            .field("capability_id", capability_id)
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationAutomationPlan {
    schema_version: &'static str,
    profile_version: &'static str,
    binding_set_sha256: String,
    source_state_sha256: String,
    source: EquationAutomationSourceState,
    operation: EquationAutomationOperation,
    plan_sha256: String,
}

impl EquationAutomationPlan {
    #[must_use]
    pub const fn schema_version(&self) -> &'static str {
        self.schema_version
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    #[must_use]
    pub fn binding_set_sha256(&self) -> &str {
        &self.binding_set_sha256
    }

    #[must_use]
    pub fn source_state_sha256(&self) -> &str {
        &self.source_state_sha256
    }

    #[must_use]
    pub fn capability_id(&self) -> &'static str {
        match &self.operation {
            EquationAutomationOperation::Insert { capability_id, .. }
            | EquationAutomationOperation::Edit { capability_id, .. }
            | EquationAutomationOperation::Readback { capability_id, .. } => capability_id,
        }
    }

    #[must_use]
    pub fn expected_output_semantic_sha256(&self) -> &str {
        match &self.operation {
            EquationAutomationOperation::Insert {
                semantic_sha256, ..
            }
            | EquationAutomationOperation::Edit {
                semantic_sha256, ..
            } => semantic_sha256,
            EquationAutomationOperation::Readback {
                expected_semantic_sha256,
                ..
            } => expected_semantic_sha256,
        }
    }

    /// Serializes the complete bounded internal plan. It contains no Action, `ParameterSet`, item
    /// identifier, XML, path, or fallback payload.
    ///
    /// # Errors
    ///
    /// Returns an output error if serialization exceeds the configured finite bound.
    pub fn canonical_json(
        &self,
        limits: EquationAutomationLimits,
    ) -> Result<Vec<u8>, EquationAutomationError> {
        bounded_json(self, limits)
    }
}

impl fmt::Debug for EquationAutomationPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationAutomationPlan")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("binding_set_sha256", &"<redacted>")
            .field("source_state_sha256", &"<redacted>")
            .field("source", &"<redacted>")
            .field("operation", &self.operation)
            .field("plan_sha256", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EquationAutomationReceiptState {
    Succeeded,
    FailedBeforeEffect,
    EffectUnknown,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationAutomationReceiptDraft {
    pub schema_version: String,
    pub plan_sha256: String,
    pub binding_set_sha256: String,
    pub source_state_sha256: String,
    pub state: EquationAutomationReceiptState,
    pub output_object_id: u32,
    pub output_semantic_sha256: String,
    pub output_package_graph_sha256: String,
    pub output_document_flow_sha256: String,
    pub native_object_count: u32,
}

impl fmt::Debug for EquationAutomationReceiptDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationAutomationReceiptDraft")
            .field("schema_version", &self.schema_version)
            .field("state", &self.state)
            .field("identities", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl fmt::Debug for EquationAutomationReceiptState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Succeeded => "Succeeded",
            Self::FailedBeforeEffect => "FailedBeforeEffect",
            Self::EffectUnknown => "EffectUnknown",
        })
    }
}

#[derive(Clone, Copy, Debug)]
pub struct EquationAutomationPlanner {
    limits: EquationAutomationLimits,
    math_limits: MathAstLimits,
    eqedit_limits: EqEditLimits,
}

impl EquationAutomationPlanner {
    #[must_use]
    pub const fn new(
        limits: EquationAutomationLimits,
        math_limits: MathAstLimits,
        eqedit_limits: EqEditLimits,
    ) -> Self {
        Self {
            limits,
            math_limits,
            eqedit_limits,
        }
    }

    /// Parses and builds a strict request while independently checking the complete source state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicate, unknown, oversized, stale, or unsupported input before a plan
    /// can reach an automation binding.
    pub fn build_json(
        &self,
        request: &[u8],
        observed_source: &EquationAutomationSourceState,
    ) -> Result<EquationAutomationPlan, EquationAutomationError> {
        if request.is_empty() || request.len() > self.limits.0.request_bytes {
            return Err(EquationAutomationError::InvalidJson);
        }
        let draft =
            serde_json::from_slice(request).map_err(|_| EquationAutomationError::InvalidJson)?;
        self.build(draft, observed_source)
    }

    /// Builds an exact-target semantic automation plan. The caller cannot provide raw automation
    /// identifiers, and request/build both require byte-equivalent typed source state.
    ///
    /// # Errors
    ///
    /// Rejects target/profile drift, invalid identities, selection mismatch, stale source state,
    /// unrepresentable ASTs, and any `EqEdit` semantic round-trip mismatch.
    pub fn build(
        &self,
        draft: EquationAutomationTarget,
        observed_source: &EquationAutomationSourceState,
    ) -> Result<EquationAutomationPlan, EquationAutomationError> {
        if draft.schema_version != EQUATION_AUTOMATION_SCHEMA_VERSION {
            return Err(EquationAutomationError::UnsupportedVersion);
        }
        if draft.profile_version != EQUATION_AUTOMATION_PROFILE_VERSION {
            return Err(EquationAutomationError::UnsupportedProfile);
        }
        validate_digest(&draft.binding_set_sha256)?;
        validate_source(&draft.source, self.limits)?;
        validate_source(observed_source, self.limits)?;
        if &draft.source != observed_source {
            return Err(EquationAutomationError::SourceStateDrift);
        }
        let engine = EqEditEngine::new(self.eqedit_limits, self.math_limits)
            .map_err(|_| EquationAutomationError::EqEdit)?;
        let operation = match draft.operation {
            EquationAutomationOperationDraft::InsertNative { math_ast } => {
                if draft.source.selected_equation.is_some() {
                    return Err(EquationAutomationError::SelectionMismatch);
                }
                let compiled = compile(&engine, math_ast, self.math_limits)?;
                EquationAutomationOperation::Insert {
                    capability_id: "eq.insert_native",
                    semantic_sha256: compiled.semantic_sha256().to_owned(),
                    script_sha256: compiled.script_sha256().to_owned(),
                    script: compiled.script().to_owned(),
                }
            }
            EquationAutomationOperationDraft::EditNative {
                object_id,
                expected_semantic_sha256,
                math_ast,
            } => {
                require_selected(&draft.source, object_id, &expected_semantic_sha256)?;
                let compiled = compile(&engine, math_ast, self.math_limits)?;
                EquationAutomationOperation::Edit {
                    capability_id: "eq.edit_native",
                    object_id,
                    expected_semantic_sha256,
                    semantic_sha256: compiled.semantic_sha256().to_owned(),
                    script_sha256: compiled.script_sha256().to_owned(),
                    script: compiled.script().to_owned(),
                }
            }
            EquationAutomationOperationDraft::ReadbackNative {
                object_id,
                expected_semantic_sha256,
            } => {
                require_selected(&draft.source, object_id, &expected_semantic_sha256)?;
                EquationAutomationOperation::Readback {
                    capability_id: "eq.roundtrip_readback",
                    object_id,
                    expected_semantic_sha256,
                }
            }
        };
        let source_state_sha256 = hash_json(&draft.source)?;
        let seed = EquationAutomationPlanSeed {
            schema_version: EQUATION_AUTOMATION_SCHEMA_VERSION,
            profile_version: EQUATION_AUTOMATION_PROFILE_VERSION,
            binding_set_sha256: &draft.binding_set_sha256,
            source_state_sha256: &source_state_sha256,
            source: &draft.source,
            operation: &operation,
        };
        let plan_sha256 = hash_json(&seed)?;
        let plan = EquationAutomationPlan {
            schema_version: EQUATION_AUTOMATION_SCHEMA_VERSION,
            profile_version: EQUATION_AUTOMATION_PROFILE_VERSION,
            binding_set_sha256: draft.binding_set_sha256,
            source_state_sha256,
            source: draft.source,
            operation,
            plan_sha256,
        };
        let _ = plan.canonical_json(self.limits)?;
        Ok(plan)
    }

    /// Verifies a runtime receipt against the exact immutable plan and its operation-specific
    /// mutation semantics.
    ///
    /// # Errors
    ///
    /// Rejects unknown-effect or failed receipts, identity drift, object/semantic mismatch, and
    /// unexpected mutation or non-mutation.
    pub fn verify_receipt(
        &self,
        plan: &EquationAutomationPlan,
        receipt: &EquationAutomationReceiptDraft,
    ) -> Result<(), EquationAutomationError> {
        if receipt.schema_version != EQUATION_AUTOMATION_RECEIPT_SCHEMA_VERSION
            || receipt.plan_sha256 != plan.plan_sha256
            || receipt.binding_set_sha256 != plan.binding_set_sha256
            || receipt.source_state_sha256 != plan.source_state_sha256
        {
            return Err(EquationAutomationError::ReceiptMismatch);
        }
        if receipt.state != EquationAutomationReceiptState::Succeeded {
            return Err(EquationAutomationError::EffectNotProven);
        }
        validate_digest(&receipt.output_semantic_sha256)?;
        validate_digest(&receipt.output_package_graph_sha256)?;
        validate_digest(&receipt.output_document_flow_sha256)?;
        if receipt.output_object_id == 0
            || receipt.native_object_count == 0
            || receipt.output_semantic_sha256 != plan.expected_output_semantic_sha256()
        {
            return Err(EquationAutomationError::ReceiptMismatch);
        }
        match &plan.operation {
            EquationAutomationOperation::Insert { .. } => {
                if receipt.output_package_graph_sha256 == plan.source.package_graph_sha256
                    || receipt.output_document_flow_sha256 == plan.source.document_flow_sha256
                {
                    return Err(EquationAutomationError::MutationMismatch);
                }
            }
            EquationAutomationOperation::Edit { object_id, .. } => {
                if receipt.output_object_id != *object_id
                    || receipt.output_package_graph_sha256 == plan.source.package_graph_sha256
                    || receipt.output_document_flow_sha256 == plan.source.document_flow_sha256
                {
                    return Err(EquationAutomationError::MutationMismatch);
                }
            }
            EquationAutomationOperation::Readback { object_id, .. } => {
                if receipt.output_object_id != *object_id
                    || receipt.output_package_graph_sha256 != plan.source.package_graph_sha256
                    || receipt.output_document_flow_sha256 != plan.source.document_flow_sha256
                {
                    return Err(EquationAutomationError::MutationMismatch);
                }
            }
        }
        Ok(())
    }
}

#[derive(Serialize)]
struct EquationAutomationPlanSeed<'a> {
    schema_version: &'static str,
    profile_version: &'static str,
    binding_set_sha256: &'a str,
    source_state_sha256: &'a str,
    source: &'a EquationAutomationSourceState,
    operation: &'a EquationAutomationOperation,
}

#[derive(Debug, Error, Clone, Copy, Eq, PartialEq)]
pub enum EquationAutomationError {
    #[error("equation automation limit configuration is invalid")]
    InvalidLimit,
    #[error("equation automation JSON is malformed, duplicated, unknown or oversized")]
    InvalidJson,
    #[error("equation automation schema version is unsupported")]
    UnsupportedVersion,
    #[error("equation automation target profile is unsupported")]
    UnsupportedProfile,
    #[error("equation automation identity is invalid")]
    InvalidIdentity,
    #[error("equation automation source state drifted")]
    SourceStateDrift,
    #[error("equation automation selection does not match the operation")]
    SelectionMismatch,
    #[error("equation automation MathAst admission failed")]
    MathAst,
    #[error("equation automation EqEdit compilation failed")]
    EqEdit,
    #[error("equation automation output exceeds its finite bound")]
    OutputLimit,
    #[error("equation automation serialization failed")]
    Serialization,
    #[error("equation automation receipt identity or semantic state mismatched")]
    ReceiptMismatch,
    #[error("equation automation effect is failed or unknown")]
    EffectNotProven,
    #[error("equation automation mutation semantics mismatched")]
    MutationMismatch,
}

impl EquationAutomationError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "equation_automation_invalid_limit",
            Self::InvalidJson => "equation_automation_invalid_json",
            Self::UnsupportedVersion => "equation_automation_unsupported_version",
            Self::UnsupportedProfile => "equation_automation_unsupported_profile",
            Self::InvalidIdentity => "equation_automation_invalid_identity",
            Self::SourceStateDrift => "equation_automation_source_state_drift",
            Self::SelectionMismatch => "equation_automation_selection_mismatch",
            Self::MathAst => "equation_automation_math_ast",
            Self::EqEdit => "equation_automation_eqedit",
            Self::OutputLimit => "equation_automation_output_limit",
            Self::Serialization => "equation_automation_serialization",
            Self::ReceiptMismatch => "equation_automation_receipt_mismatch",
            Self::EffectNotProven => "equation_automation_effect_not_proven",
            Self::MutationMismatch => "equation_automation_mutation_mismatch",
        }
    }
}

fn compile(
    engine: &EqEditEngine,
    draft: MathAstDraft,
    limits: MathAstLimits,
) -> Result<crate::EqEditCompileResult, EquationAutomationError> {
    let ast = MathAst::from_draft(draft, limits).map_err(|_| EquationAutomationError::MathAst)?;
    engine.compile(&ast).map_err(|error| match error {
        EqEditError::MathAst => EquationAutomationError::MathAst,
        _ => EquationAutomationError::EqEdit,
    })
}

fn validate_source(
    source: &EquationAutomationSourceState,
    limits: EquationAutomationLimits,
) -> Result<(), EquationAutomationError> {
    if source.revision.is_empty()
        || source.revision.len() > limits.0.revision_bytes
        || source.revision.chars().any(char::is_control)
    {
        return Err(EquationAutomationError::InvalidIdentity);
    }
    for digest in [
        &source.package_graph_sha256,
        &source.document_flow_sha256,
        &source.anchor_fingerprint_sha256,
    ] {
        validate_digest(digest)?;
    }
    if let Some(selection) = &source.selected_equation {
        if selection.object_id == 0 {
            return Err(EquationAutomationError::InvalidIdentity);
        }
        validate_digest(&selection.semantic_sha256)?;
    }
    Ok(())
}

fn require_selected(
    source: &EquationAutomationSourceState,
    object_id: u32,
    semantic_sha256: &str,
) -> Result<(), EquationAutomationError> {
    validate_digest(semantic_sha256)?;
    let selected = source
        .selected_equation
        .as_ref()
        .ok_or(EquationAutomationError::SelectionMismatch)?;
    if object_id == 0
        || selected.object_id != object_id
        || selected.semantic_sha256 != semantic_sha256
    {
        return Err(EquationAutomationError::SelectionMismatch);
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), EquationAutomationError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(EquationAutomationError::InvalidIdentity);
    }
    Ok(())
}

fn hash_json(value: &impl Serialize) -> Result<String, EquationAutomationError> {
    let bytes = serde_json::to_vec(value).map_err(|_| EquationAutomationError::Serialization)?;
    Ok(hex::encode(Sha256::digest(bytes)))
}

fn bounded_json(
    value: &impl Serialize,
    limits: EquationAutomationLimits,
) -> Result<Vec<u8>, EquationAutomationError> {
    let bytes = serde_json::to_vec(value).map_err(|_| EquationAutomationError::Serialization)?;
    if bytes.len() > limits.0.serialized_bytes {
        return Err(EquationAutomationError::OutputLimit);
    }
    Ok(bytes)
}
