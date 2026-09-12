use std::fmt;

use domain_ir::{MathAst, MathAstDraft, MathAstLimits};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditLimits,
    EqEditParseRequestDraft,
};

pub const EQUATION_EDITOR_SMOKE_SCHEMA_VERSION: &str = "hwpx-agent.equation-editor-smoke/v3";
pub const EQUATION_EDITOR_SMOKE_EVIDENCE_SCHEMA_VERSION: &str =
    "hwpx-agent.equation-editor-smoke-evidence/v3";
pub const EQUATION_EDITOR_SMOKE_RECEIPT_SCHEMA_VERSION: &str =
    "hwpx-agent.equation-editor-smoke-receipt/v3";
pub const EQUATION_EDITOR_SMOKE_PROFILE_VERSION: &str =
    "hwpx-agent.equation-editor-smoke.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
pub const EQUATION_EDITOR_TARGET_EXECUTABLE_SHA256: &str =
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce";

const TARGET_PRODUCT: &str = "Hangul 2020";
const TARGET_PROG_ID: &str = "HWPFrame.HwpObject.2";
const TARGET_BUILD: &str = "11.0.0.9136";
const TARGET_ARCHITECTURE: &str = "x86";
const TARGET_LOCALE: &str = "ko-KR";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EquationEditorSmokeLimitConfig {
    pub request_bytes: usize,
    pub evidence_bytes: usize,
    pub revision_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for EquationEditorSmokeLimitConfig {
    fn default() -> Self {
        Self {
            request_bytes: 8 * 1024 * 1024,
            evidence_bytes: 8 * 1024 * 1024,
            revision_bytes: 512,
            serialized_bytes: 16 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct EquationEditorSmokeLimits(EquationEditorSmokeLimitConfig);

impl EquationEditorSmokeLimits {
    pub const HARD_MAX_REQUEST_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_EVIDENCE_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_REVISION_BYTES: usize = 4 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;

    /// Creates finite P07-09 request, evidence and receipt limits.
    ///
    /// # Errors
    ///
    /// Rejects zero, hard-ceiling, and inconsistent serialized-output limits.
    pub fn new(config: EquationEditorSmokeLimitConfig) -> Result<Self, EquationEditorSmokeError> {
        if config.request_bytes == 0
            || config.request_bytes > Self::HARD_MAX_REQUEST_BYTES
            || config.evidence_bytes == 0
            || config.evidence_bytes > Self::HARD_MAX_EVIDENCE_BYTES
            || config.revision_bytes == 0
            || config.revision_bytes > Self::HARD_MAX_REVISION_BYTES
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
            || config.serialized_bytes < config.request_bytes
            || config.serialized_bytes < config.evidence_bytes
        {
            return Err(EquationEditorSmokeError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> EquationEditorSmokeLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationEditorSmokeSourceState {
    pub revision: String,
    pub artifact_sha256: String,
    pub package_graph_sha256: String,
    pub document_flow_sha256: String,
    pub anchor_fingerprint_sha256: String,
    pub object_id: u32,
    pub semantic_sha256: String,
    pub script_sha256: String,
    pub native_object_count: u32,
}

impl fmt::Debug for EquationEditorSmokeSourceState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorSmokeSourceState")
            .field("revision", &"<redacted>")
            .field("artifact", &"<redacted>")
            .field("package_graph", &"<redacted>")
            .field("document_flow", &"<redacted>")
            .field("anchor", &"<redacted>")
            .field("object", &"<redacted>")
            .field("semantic", &"<redacted>")
            .field("script", &"<redacted>")
            .field("native_object_count", &self.native_object_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationEditorSmokeRequestDraft {
    pub schema_version: String,
    pub profile_version: String,
    pub harness_sha256: String,
    pub oracle_contract_sha256: String,
    pub source: EquationEditorSmokeSourceState,
    pub before_math_ast: MathAstDraft,
    pub after_math_ast: MathAstDraft,
    pub saved_after_script: String,
}

impl fmt::Debug for EquationEditorSmokeRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorSmokeRequestDraft")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("bindings", &"<redacted>")
            .field("source", &"<redacted>")
            .field("math", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationEditorSmokePlan {
    schema_version: &'static str,
    profile_version: &'static str,
    harness_sha256: String,
    oracle_contract_sha256: String,
    source_state_sha256: String,
    source: EquationEditorSmokeSourceState,
    before_semantic_sha256: String,
    before_script_sha256: String,
    before_script: String,
    after_semantic_sha256: String,
    after_script_sha256: String,
    after_script: String,
    saved_after_script_sha256: String,
    saved_after_script: String,
    changed_token_index: usize,
    before_token_sha256: String,
    after_token_sha256: String,
    plan_sha256: String,
}

impl EquationEditorSmokePlan {
    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    #[must_use]
    pub fn source_state_sha256(&self) -> &str {
        &self.source_state_sha256
    }

    #[must_use]
    pub fn before_script(&self) -> &str {
        &self.before_script
    }

    #[must_use]
    pub fn after_script(&self) -> &str {
        &self.after_script
    }

    #[must_use]
    pub fn saved_after_script(&self) -> &str {
        &self.saved_after_script
    }

    #[must_use]
    pub fn before_semantic_sha256(&self) -> &str {
        &self.before_semantic_sha256
    }

    #[must_use]
    pub fn after_semantic_sha256(&self) -> &str {
        &self.after_semantic_sha256
    }

    #[must_use]
    pub fn before_script_sha256(&self) -> &str {
        &self.before_script_sha256
    }

    #[must_use]
    pub fn after_script_sha256(&self) -> &str {
        &self.after_script_sha256
    }

    #[must_use]
    pub fn saved_after_script_sha256(&self) -> &str {
        &self.saved_after_script_sha256
    }

    #[must_use]
    pub const fn changed_token_index(&self) -> usize {
        self.changed_token_index
    }

    /// Serializes the private bounded plan deterministically.
    ///
    /// # Errors
    ///
    /// Returns an error when serialization fails or exceeds its finite bound.
    pub fn canonical_json(
        &self,
        limits: EquationEditorSmokeLimits,
    ) -> Result<Vec<u8>, EquationEditorSmokeError> {
        bounded_json(self, limits)
    }
}

impl fmt::Debug for EquationEditorSmokePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorSmokePlan")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("bindings", &"<redacted>")
            .field("source", &"<redacted>")
            .field("programs", &"<redacted>")
            .field("token_change", &"<redacted>")
            .field("plan_sha256", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Serialize)]
struct EquationEditorSmokePlanSeed<'a> {
    schema_version: &'static str,
    profile_version: &'static str,
    harness_sha256: &'a str,
    oracle_contract_sha256: &'a str,
    source_state_sha256: &'a str,
    source: &'a EquationEditorSmokeSourceState,
    before_semantic_sha256: &'a str,
    before_script_sha256: &'a str,
    before_script: &'a str,
    after_semantic_sha256: &'a str,
    after_script_sha256: &'a str,
    after_script: &'a str,
    saved_after_script_sha256: &'a str,
    saved_after_script: &'a str,
    changed_token_index: usize,
    before_token_sha256: &'a str,
    after_token_sha256: &'a str,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct EquationEditorSmokePlanDraft {
    schema_version: String,
    profile_version: String,
    harness_sha256: String,
    oracle_contract_sha256: String,
    source_state_sha256: String,
    source: EquationEditorSmokeSourceState,
    before_semantic_sha256: String,
    before_script_sha256: String,
    before_script: String,
    after_semantic_sha256: String,
    after_script_sha256: String,
    after_script: String,
    saved_after_script_sha256: String,
    saved_after_script: String,
    changed_token_index: usize,
    before_token_sha256: String,
    after_token_sha256: String,
    plan_sha256: String,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationEditorTargetIdentity {
    pub product: String,
    pub prog_id: String,
    pub build: String,
    pub executable_sha256: String,
    pub architecture: String,
    pub locale: String,
}

impl fmt::Debug for EquationEditorTargetIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorTargetIdentity")
            .field("product", &self.product)
            .field("prog_id", &self.prog_id)
            .field("build", &self.build)
            .field("executable_sha256", &"<redacted>")
            .field("architecture", &self.architecture)
            .field("locale", &self.locale)
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationEditorSmokeSnapshot {
    pub artifact_sha256: String,
    pub package_graph_sha256: String,
    pub document_flow_sha256: String,
    pub object_id: u32,
    pub semantic_sha256: String,
    pub script_sha256: String,
    pub native_object_count: u32,
}

impl fmt::Debug for EquationEditorSmokeSnapshot {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorSmokeSnapshot")
            .field("identities", &"<redacted>")
            .field("native_object_count", &self.native_object_count)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EquationEditorVerificationState {
    Passed,
    Failed,
    NotRun,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EquationEditorManualAttestationState {
    UserAttested,
    Failed,
    NotRun,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationEditorManualProof {
    pub before_equation_matches_plan: EquationEditorManualAttestationState,
    pub double_click: EquationEditorManualAttestationState,
    pub editor_visible: EquationEditorManualAttestationState,
    pub one_token_change: EquationEditorManualAttestationState,
    pub editor_closed_after_commit: EquationEditorManualAttestationState,
    pub post_commit_equation_matches_plan: EquationEditorManualAttestationState,
    pub saved_as_after_hwpx: EquationEditorManualAttestationState,
    pub user_performed_all_clicks_and_typing: EquationEditorManualAttestationState,
    pub anomaly_reported: bool,
    pub computer_use_click_or_type_invoked: bool,
    pub operator_checklist_sha256: String,
}

impl fmt::Debug for EquationEditorManualProof {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorManualProof")
            .field("states", &"<redacted>")
            .field("evidence", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationEditorAutomationProof {
    pub exact_target_preflight: EquationEditorVerificationState,
    pub immutable_input: EquationEditorVerificationState,
    pub initial_native_readback: EquationEditorVerificationState,
    pub saved_native_readback: EquationEditorVerificationState,
    pub reopen_native_readback: EquationEditorVerificationState,
    pub save: EquationEditorVerificationState,
    pub close: EquationEditorVerificationState,
    pub reopen: EquationEditorVerificationState,
    pub all_phases: EquationEditorVerificationState,
    pub trace_sha256: String,
    pub oracle_receipt_sha256: String,
}

impl fmt::Debug for EquationEditorAutomationProof {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorAutomationProof")
            .field("states", &"<redacted>")
            .field("evidence", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EquationEditorSmokeEvidenceState {
    Succeeded,
    FailedBeforeEffect,
    EffectUnknown,
}

impl fmt::Debug for EquationEditorSmokeEvidenceState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Succeeded => "Succeeded",
            Self::FailedBeforeEffect => "FailedBeforeEffect",
            Self::EffectUnknown => "EffectUnknown",
        })
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct EquationEditorSmokeEvidenceDraft {
    pub schema_version: String,
    pub profile_version: String,
    pub plan_sha256: String,
    pub source_state_sha256: String,
    pub harness_sha256: String,
    pub oracle_contract_sha256: String,
    pub target: EquationEditorTargetIdentity,
    pub state: EquationEditorSmokeEvidenceState,
    pub manual: EquationEditorManualProof,
    pub automation: EquationEditorAutomationProof,
    pub before: EquationEditorSmokeSnapshot,
    pub after_save: EquationEditorSmokeSnapshot,
    pub after_reopen: EquationEditorSmokeSnapshot,
    pub silent_fallback_count: u32,
    pub text_fallback_count: u32,
    pub image_fallback_count: u32,
    pub object_replacement_count: u32,
}

impl fmt::Debug for EquationEditorSmokeEvidenceDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorSmokeEvidenceDraft")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("target", &self.target)
            .field("state", &self.state)
            .field("manual", &self.manual)
            .field("automation", &self.automation)
            .field("snapshots", &"<redacted>")
            .field("fallbacks", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationEditorSmokeReceipt {
    schema_version: &'static str,
    profile_version: &'static str,
    plan_sha256: String,
    evidence_sha256: String,
    target_build: &'static str,
    target_architecture: &'static str,
    target_locale: &'static str,
    changed_token_count: u32,
    native_object_count: u32,
    silent_fallback_count: u32,
    manual_double_click_state: &'static str,
    automated_save_reopen_state: &'static str,
    semantic_change_state: &'static str,
    object_identity_state: &'static str,
    actual_hangul: bool,
    render_state: &'static str,
    p07_state: &'static str,
    product_complete: bool,
}

impl EquationEditorSmokeReceipt {
    #[must_use]
    pub fn evidence_sha256(&self) -> &str {
        &self.evidence_sha256
    }

    #[must_use]
    pub const fn manual_double_click_user_attested(&self) -> bool {
        matches!(self.manual_double_click_state.as_bytes(), b"user_attested")
    }

    #[must_use]
    pub const fn automated_save_reopen_verified(&self) -> bool {
        matches!(self.automated_save_reopen_state.as_bytes(), b"verified")
    }

    #[must_use]
    pub const fn actual_hangul(&self) -> bool {
        self.actual_hangul
    }

    /// Serializes the content-free verified receipt within its finite bound.
    ///
    /// # Errors
    ///
    /// Returns an error when serialization fails or exceeds its finite bound.
    pub fn canonical_json(
        &self,
        limits: EquationEditorSmokeLimits,
    ) -> Result<Vec<u8>, EquationEditorSmokeError> {
        bounded_json(self, limits)
    }
}

impl fmt::Debug for EquationEditorSmokeReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationEditorSmokeReceipt")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("identities", &"<redacted>")
            .field("target_build", &self.target_build)
            .field("target_architecture", &self.target_architecture)
            .field("target_locale", &self.target_locale)
            .field("changed_token_count", &self.changed_token_count)
            .field("native_object_count", &self.native_object_count)
            .field("silent_fallback_count", &self.silent_fallback_count)
            .field("manual_double_click_state", &self.manual_double_click_state)
            .field(
                "automated_save_reopen_state",
                &self.automated_save_reopen_state,
            )
            .field("semantic_change_state", &self.semantic_change_state)
            .field("object_identity_state", &self.object_identity_state)
            .field("actual_hangul", &self.actual_hangul)
            .field("render_state", &self.render_state)
            .field("p07_state", &self.p07_state)
            .field("product_complete", &self.product_complete)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug)]
pub struct EquationEditorSmokePlanner {
    limits: EquationEditorSmokeLimits,
    math_limits: MathAstLimits,
    eqedit_limits: EqEditLimits,
}

impl EquationEditorSmokePlanner {
    #[must_use]
    pub const fn new(
        limits: EquationEditorSmokeLimits,
        math_limits: MathAstLimits,
        eqedit_limits: EqEditLimits,
    ) -> Self {
        Self {
            limits,
            math_limits,
            eqedit_limits,
        }
    }

    /// Builds an exact single-token editor plan from strict bounded JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, unknown, duplicate, oversized or stale input.
    pub fn build_json(
        &self,
        request: &[u8],
        observed_source: &EquationEditorSmokeSourceState,
    ) -> Result<EquationEditorSmokePlan, EquationEditorSmokeError> {
        if request.is_empty() || request.len() > self.limits.0.request_bytes {
            return Err(EquationEditorSmokeError::InvalidJson);
        }
        let draft =
            serde_json::from_slice(request).map_err(|_| EquationEditorSmokeError::InvalidJson)?;
        self.build(draft, observed_source)
    }

    /// Loads a hash-pinned private plan and recomputes every source, semantic and token binding.
    ///
    /// # Errors
    ///
    /// Rejects untrusted or malformed bytes and any plan/source/semantic/token/hash drift.
    pub fn load_plan_json(
        &self,
        plan_bytes: &[u8],
        trusted_plan_file_sha256: &str,
        observed_source: &EquationEditorSmokeSourceState,
    ) -> Result<EquationEditorSmokePlan, EquationEditorSmokeError> {
        if plan_bytes.is_empty() || plan_bytes.len() > self.limits.0.request_bytes {
            return Err(EquationEditorSmokeError::InvalidJson);
        }
        validate_digest(trusted_plan_file_sha256)?;
        if hex::encode(Sha256::digest(plan_bytes)) != trusted_plan_file_sha256 {
            return Err(EquationEditorSmokeError::UntrustedPlan);
        }
        let draft: EquationEditorSmokePlanDraft = serde_json::from_slice(plan_bytes)
            .map_err(|_| EquationEditorSmokeError::InvalidJson)?;
        if draft.schema_version != EQUATION_EDITOR_SMOKE_SCHEMA_VERSION {
            return Err(EquationEditorSmokeError::UnsupportedVersion);
        }
        if draft.profile_version != EQUATION_EDITOR_SMOKE_PROFILE_VERSION {
            return Err(EquationEditorSmokeError::UnsupportedProfile);
        }
        validate_source(&draft.source, self.limits)?;
        validate_source(observed_source, self.limits)?;
        if &draft.source != observed_source {
            return Err(EquationEditorSmokeError::SourceStateDrift);
        }
        validate_plan_draft_digests(&draft)?;
        if hash_json(&draft.source)? != draft.source_state_sha256 {
            return Err(EquationEditorSmokeError::PlanMismatch);
        }
        let engine = EqEditEngine::new(self.eqedit_limits, self.math_limits)
            .map_err(|_| EquationEditorSmokeError::EqEdit)?;
        let before = compile_canonical_script(&engine, &draft.before_script)?;
        let after = compile_canonical_script(&engine, &draft.after_script)?;
        let (saved_after_script_sha256, saved_after_semantic_sha256) =
            parse_editor_script(&engine, &draft.saved_after_script)?;
        if before.semantic_sha256() != draft.before_semantic_sha256
            || before.script_sha256() != draft.before_script_sha256
            || after.semantic_sha256() != draft.after_semantic_sha256
            || after.script_sha256() != draft.after_script_sha256
            || saved_after_semantic_sha256 != draft.after_semantic_sha256
            || saved_after_script_sha256 != draft.saved_after_script_sha256
            || draft.source.semantic_sha256 != draft.before_semantic_sha256
            || draft.source.script_sha256 != draft.before_script_sha256
        {
            return Err(EquationEditorSmokeError::PlanMismatch);
        }
        let (changed_token_index, before_token_sha256, after_token_sha256) = single_token_change(
            &draft.before_script,
            &draft.after_script,
            self.eqedit_limits,
        )?;
        if changed_token_index != draft.changed_token_index
            || before_token_sha256 != draft.before_token_sha256
            || after_token_sha256 != draft.after_token_sha256
        {
            return Err(EquationEditorSmokeError::PlanMismatch);
        }
        let seed = EquationEditorSmokePlanSeed {
            schema_version: EQUATION_EDITOR_SMOKE_SCHEMA_VERSION,
            profile_version: EQUATION_EDITOR_SMOKE_PROFILE_VERSION,
            harness_sha256: &draft.harness_sha256,
            oracle_contract_sha256: &draft.oracle_contract_sha256,
            source_state_sha256: &draft.source_state_sha256,
            source: &draft.source,
            before_semantic_sha256: &draft.before_semantic_sha256,
            before_script_sha256: &draft.before_script_sha256,
            before_script: &draft.before_script,
            after_semantic_sha256: &draft.after_semantic_sha256,
            after_script_sha256: &draft.after_script_sha256,
            after_script: &draft.after_script,
            saved_after_script_sha256: &draft.saved_after_script_sha256,
            saved_after_script: &draft.saved_after_script,
            changed_token_index,
            before_token_sha256: &before_token_sha256,
            after_token_sha256: &after_token_sha256,
        };
        if hash_json(&seed)? != draft.plan_sha256 {
            return Err(EquationEditorSmokeError::PlanMismatch);
        }
        Ok(EquationEditorSmokePlan {
            schema_version: EQUATION_EDITOR_SMOKE_SCHEMA_VERSION,
            profile_version: EQUATION_EDITOR_SMOKE_PROFILE_VERSION,
            harness_sha256: draft.harness_sha256,
            oracle_contract_sha256: draft.oracle_contract_sha256,
            source_state_sha256: draft.source_state_sha256,
            source: draft.source,
            before_semantic_sha256: draft.before_semantic_sha256,
            before_script_sha256: draft.before_script_sha256,
            before_script: draft.before_script,
            after_semantic_sha256: draft.after_semantic_sha256,
            after_script_sha256: draft.after_script_sha256,
            after_script: draft.after_script,
            saved_after_script_sha256,
            saved_after_script: draft.saved_after_script,
            changed_token_index,
            before_token_sha256,
            after_token_sha256,
            plan_sha256: draft.plan_sha256,
        })
    }

    /// Builds the private editor plan while checking complete source state and exact token change.
    ///
    /// # Errors
    ///
    /// Rejects identity/source drift, non-round-tripping ASTs, no-op edits and edits that alter
    /// anything other than exactly one canonical `EqEdit` token.
    pub fn build(
        &self,
        draft: EquationEditorSmokeRequestDraft,
        observed_source: &EquationEditorSmokeSourceState,
    ) -> Result<EquationEditorSmokePlan, EquationEditorSmokeError> {
        if draft.schema_version != EQUATION_EDITOR_SMOKE_SCHEMA_VERSION {
            return Err(EquationEditorSmokeError::UnsupportedVersion);
        }
        if draft.profile_version != EQUATION_EDITOR_SMOKE_PROFILE_VERSION {
            return Err(EquationEditorSmokeError::UnsupportedProfile);
        }
        validate_digest(&draft.harness_sha256)?;
        validate_digest(&draft.oracle_contract_sha256)?;
        validate_source(&draft.source, self.limits)?;
        validate_source(observed_source, self.limits)?;
        if &draft.source != observed_source {
            return Err(EquationEditorSmokeError::SourceStateDrift);
        }
        let engine = EqEditEngine::new(self.eqedit_limits, self.math_limits)
            .map_err(|_| EquationEditorSmokeError::EqEdit)?;
        let before = compile_roundtrip(&engine, draft.before_math_ast, self.math_limits)?;
        let after = compile_roundtrip(&engine, draft.after_math_ast, self.math_limits)?;
        if before.semantic_sha256() != draft.source.semantic_sha256
            || before.script_sha256() != draft.source.script_sha256
        {
            return Err(EquationEditorSmokeError::SourceSemanticDrift);
        }
        if before.semantic_sha256() == after.semantic_sha256()
            || before.script_sha256() == after.script_sha256()
        {
            return Err(EquationEditorSmokeError::NoSemanticChange);
        }
        let (saved_after_script_sha256, saved_after_semantic_sha256) =
            parse_editor_script(&engine, &draft.saved_after_script)?;
        if saved_after_semantic_sha256 != after.semantic_sha256() {
            return Err(EquationEditorSmokeError::EditorCanonicalizationMismatch);
        }
        let (changed_token_index, before_token_sha256, after_token_sha256) =
            single_token_change(before.script(), after.script(), self.eqedit_limits)?;
        let source_state_sha256 = hash_json(&draft.source)?;
        let seed = EquationEditorSmokePlanSeed {
            schema_version: EQUATION_EDITOR_SMOKE_SCHEMA_VERSION,
            profile_version: EQUATION_EDITOR_SMOKE_PROFILE_VERSION,
            harness_sha256: &draft.harness_sha256,
            oracle_contract_sha256: &draft.oracle_contract_sha256,
            source_state_sha256: &source_state_sha256,
            source: &draft.source,
            before_semantic_sha256: before.semantic_sha256(),
            before_script_sha256: before.script_sha256(),
            before_script: before.script(),
            after_semantic_sha256: after.semantic_sha256(),
            after_script_sha256: after.script_sha256(),
            after_script: after.script(),
            saved_after_script_sha256: &saved_after_script_sha256,
            saved_after_script: &draft.saved_after_script,
            changed_token_index,
            before_token_sha256: &before_token_sha256,
            after_token_sha256: &after_token_sha256,
        };
        let plan_sha256 = hash_json(&seed)?;
        let plan = EquationEditorSmokePlan {
            schema_version: EQUATION_EDITOR_SMOKE_SCHEMA_VERSION,
            profile_version: EQUATION_EDITOR_SMOKE_PROFILE_VERSION,
            harness_sha256: draft.harness_sha256,
            oracle_contract_sha256: draft.oracle_contract_sha256,
            source_state_sha256,
            source: draft.source,
            before_semantic_sha256: before.semantic_sha256().to_owned(),
            before_script_sha256: before.script_sha256().to_owned(),
            before_script: before.script().to_owned(),
            after_semantic_sha256: after.semantic_sha256().to_owned(),
            after_script_sha256: after.script_sha256().to_owned(),
            after_script: after.script().to_owned(),
            saved_after_script_sha256,
            saved_after_script: draft.saved_after_script,
            changed_token_index,
            before_token_sha256,
            after_token_sha256,
            plan_sha256,
        };
        let _ = plan.canonical_json(self.limits)?;
        Ok(plan)
    }

    /// Verifies exact hash-pinned combined manual and automated target evidence.
    ///
    /// # Errors
    ///
    /// Rejects untrusted bytes, target drift, unknown effect, incomplete manual proof, missing
    /// native save/reopen proof, object/semantic/state drift and any fallback.
    pub fn verify_evidence_json(
        &self,
        plan: &EquationEditorSmokePlan,
        evidence: &[u8],
        trusted_evidence_sha256: &str,
    ) -> Result<EquationEditorSmokeReceipt, EquationEditorSmokeError> {
        if evidence.is_empty() || evidence.len() > self.limits.0.evidence_bytes {
            return Err(EquationEditorSmokeError::InvalidJson);
        }
        validate_digest(trusted_evidence_sha256)?;
        let evidence_sha256 = hex::encode(Sha256::digest(evidence));
        if evidence_sha256 != trusted_evidence_sha256 {
            return Err(EquationEditorSmokeError::UntrustedEvidence);
        }
        let draft: EquationEditorSmokeEvidenceDraft =
            serde_json::from_slice(evidence).map_err(|_| EquationEditorSmokeError::InvalidJson)?;
        self.verify_evidence(plan, &draft, evidence_sha256)
    }

    fn verify_evidence(
        &self,
        plan: &EquationEditorSmokePlan,
        draft: &EquationEditorSmokeEvidenceDraft,
        evidence_sha256: String,
    ) -> Result<EquationEditorSmokeReceipt, EquationEditorSmokeError> {
        if draft.schema_version != EQUATION_EDITOR_SMOKE_EVIDENCE_SCHEMA_VERSION
            || draft.profile_version != EQUATION_EDITOR_SMOKE_PROFILE_VERSION
        {
            return Err(EquationEditorSmokeError::UnsupportedVersion);
        }
        if draft.plan_sha256 != plan.plan_sha256
            || draft.source_state_sha256 != plan.source_state_sha256
            || draft.harness_sha256 != plan.harness_sha256
            || draft.oracle_contract_sha256 != plan.oracle_contract_sha256
        {
            return Err(EquationEditorSmokeError::EvidenceMismatch);
        }
        validate_target(&draft.target)?;
        if draft.state != EquationEditorSmokeEvidenceState::Succeeded {
            return Err(EquationEditorSmokeError::EffectNotProven);
        }
        validate_manual(&draft.manual)?;
        validate_automation(&draft.automation)?;
        validate_snapshot(&draft.before)?;
        validate_snapshot(&draft.after_save)?;
        validate_snapshot(&draft.after_reopen)?;
        let before = &draft.before;
        if before.artifact_sha256 != plan.source.artifact_sha256
            || before.package_graph_sha256 != plan.source.package_graph_sha256
            || before.document_flow_sha256 != plan.source.document_flow_sha256
            || before.object_id != plan.source.object_id
            || before.semantic_sha256 != plan.before_semantic_sha256
            || before.script_sha256 != plan.before_script_sha256
            || before.native_object_count != plan.source.native_object_count
        {
            return Err(EquationEditorSmokeError::EvidenceMismatch);
        }
        let after = &draft.after_save;
        if after.object_id != before.object_id
            || after.native_object_count != before.native_object_count
            || after.semantic_sha256 != plan.after_semantic_sha256
            || after.script_sha256 != plan.saved_after_script_sha256
            || after.artifact_sha256 == before.artifact_sha256
            || after.package_graph_sha256 == before.package_graph_sha256
            || after.document_flow_sha256 == before.document_flow_sha256
            || draft.after_reopen != *after
        {
            return Err(EquationEditorSmokeError::MutationMismatch);
        }
        if draft.silent_fallback_count != 0
            || draft.text_fallback_count != 0
            || draft.image_fallback_count != 0
            || draft.object_replacement_count != 0
        {
            return Err(EquationEditorSmokeError::FallbackDetected);
        }
        let receipt = EquationEditorSmokeReceipt {
            schema_version: EQUATION_EDITOR_SMOKE_RECEIPT_SCHEMA_VERSION,
            profile_version: EQUATION_EDITOR_SMOKE_PROFILE_VERSION,
            plan_sha256: plan.plan_sha256.clone(),
            evidence_sha256,
            target_build: TARGET_BUILD,
            target_architecture: TARGET_ARCHITECTURE,
            target_locale: TARGET_LOCALE,
            changed_token_count: 1,
            native_object_count: after.native_object_count,
            silent_fallback_count: 0,
            manual_double_click_state: "user_attested",
            automated_save_reopen_state: "verified",
            semantic_change_state: "verified",
            object_identity_state: "preserved",
            actual_hangul: true,
            render_state: "not_run",
            p07_state: "in_progress",
            product_complete: false,
        };
        let _ = receipt.canonical_json(self.limits)?;
        Ok(receipt)
    }
}

fn compile_roundtrip(
    engine: &EqEditEngine,
    draft: MathAstDraft,
    limits: MathAstLimits,
) -> Result<crate::EqEditCompileResult, EquationEditorSmokeError> {
    let ast = MathAst::from_draft(draft, limits).map_err(|_| EquationEditorSmokeError::MathAst)?;
    let compiled = engine
        .compile(&ast)
        .map_err(|_| EquationEditorSmokeError::EqEdit)?;
    let reparsed = engine
        .parse(EqEditParseRequestDraft {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
            profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
            source: compiled.script().to_owned(),
        })
        .map_err(|_| EquationEditorSmokeError::EqEdit)?;
    if !ast.semantically_eq(reparsed.ast()) {
        return Err(EquationEditorSmokeError::SemanticRoundtrip);
    }
    Ok(compiled)
}

fn compile_canonical_script(
    engine: &EqEditEngine,
    source: &str,
) -> Result<crate::EqEditCompileResult, EquationEditorSmokeError> {
    let parsed = engine
        .parse(EqEditParseRequestDraft {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
            profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
            source: source.to_owned(),
        })
        .map_err(|_| EquationEditorSmokeError::EqEdit)?;
    let compiled = engine
        .compile(parsed.ast())
        .map_err(|_| EquationEditorSmokeError::EqEdit)?;
    if compiled.script() != source {
        return Err(EquationEditorSmokeError::PlanMismatch);
    }
    Ok(compiled)
}

fn parse_editor_script(
    engine: &EqEditEngine,
    source: &str,
) -> Result<(String, String), EquationEditorSmokeError> {
    let parsed = engine
        .parse(EqEditParseRequestDraft {
            schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
            profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
            source: source.to_owned(),
        })
        .map_err(|_| EquationEditorSmokeError::EqEdit)?;
    let source_sha256 = parsed.source_sha256().to_owned();
    let compiled = engine
        .compile(parsed.ast())
        .map_err(|_| EquationEditorSmokeError::EqEdit)?;
    Ok((source_sha256, compiled.semantic_sha256().to_owned()))
}

fn single_token_change(
    before_script: &str,
    after_script: &str,
    limits: EqEditLimits,
) -> Result<(usize, String, String), EquationEditorSmokeError> {
    let before_tokens = crate::eqedit::token_fingerprints(before_script, limits)
        .map_err(|_| EquationEditorSmokeError::EqEdit)?;
    let after_tokens = crate::eqedit::token_fingerprints(after_script, limits)
        .map_err(|_| EquationEditorSmokeError::EqEdit)?;
    if before_tokens.is_empty() || before_tokens.len() != after_tokens.len() {
        return Err(EquationEditorSmokeError::TokenChangeMismatch);
    }
    let changed: Vec<usize> = before_tokens
        .iter()
        .zip(&after_tokens)
        .enumerate()
        .filter_map(|(index, (before, after))| (before != after).then_some(index))
        .collect();
    if changed.len() != 1 {
        return Err(EquationEditorSmokeError::TokenChangeMismatch);
    }
    let index = changed[0];
    Ok((
        index,
        hex::encode(before_tokens[index]),
        hex::encode(after_tokens[index]),
    ))
}

fn validate_source(
    source: &EquationEditorSmokeSourceState,
    limits: EquationEditorSmokeLimits,
) -> Result<(), EquationEditorSmokeError> {
    if source.revision.is_empty()
        || source.revision.len() > limits.0.revision_bytes
        || source.revision.chars().any(char::is_control)
        || source.object_id == 0
        || source.native_object_count == 0
    {
        return Err(EquationEditorSmokeError::InvalidIdentity);
    }
    for digest in [
        &source.artifact_sha256,
        &source.package_graph_sha256,
        &source.document_flow_sha256,
        &source.anchor_fingerprint_sha256,
        &source.semantic_sha256,
        &source.script_sha256,
    ] {
        validate_digest(digest)?;
    }
    Ok(())
}

fn validate_plan_draft_digests(
    draft: &EquationEditorSmokePlanDraft,
) -> Result<(), EquationEditorSmokeError> {
    for digest in [
        &draft.harness_sha256,
        &draft.oracle_contract_sha256,
        &draft.source_state_sha256,
        &draft.before_semantic_sha256,
        &draft.before_script_sha256,
        &draft.after_semantic_sha256,
        &draft.after_script_sha256,
        &draft.saved_after_script_sha256,
        &draft.before_token_sha256,
        &draft.after_token_sha256,
        &draft.plan_sha256,
    ] {
        validate_digest(digest)?;
    }
    Ok(())
}

fn validate_target(target: &EquationEditorTargetIdentity) -> Result<(), EquationEditorSmokeError> {
    if target.product != TARGET_PRODUCT
        || target.prog_id != TARGET_PROG_ID
        || target.build != TARGET_BUILD
        || target.executable_sha256 != EQUATION_EDITOR_TARGET_EXECUTABLE_SHA256
        || target.architecture != TARGET_ARCHITECTURE
        || target.locale != TARGET_LOCALE
    {
        return Err(EquationEditorSmokeError::TargetMismatch);
    }
    Ok(())
}

fn validate_manual(proof: &EquationEditorManualProof) -> Result<(), EquationEditorSmokeError> {
    if proof.before_equation_matches_plan != EquationEditorManualAttestationState::UserAttested
        || proof.double_click != EquationEditorManualAttestationState::UserAttested
        || proof.editor_visible != EquationEditorManualAttestationState::UserAttested
        || proof.one_token_change != EquationEditorManualAttestationState::UserAttested
        || proof.editor_closed_after_commit != EquationEditorManualAttestationState::UserAttested
        || proof.post_commit_equation_matches_plan
            != EquationEditorManualAttestationState::UserAttested
        || proof.saved_as_after_hwpx != EquationEditorManualAttestationState::UserAttested
        || proof.user_performed_all_clicks_and_typing
            != EquationEditorManualAttestationState::UserAttested
        || proof.anomaly_reported
        || proof.computer_use_click_or_type_invoked
    {
        return Err(EquationEditorSmokeError::ManualEvidenceIncomplete);
    }
    validate_digest(&proof.operator_checklist_sha256)?;
    Ok(())
}

fn validate_automation(
    proof: &EquationEditorAutomationProof,
) -> Result<(), EquationEditorSmokeError> {
    if proof.exact_target_preflight != EquationEditorVerificationState::Passed
        || proof.immutable_input != EquationEditorVerificationState::Passed
        || proof.initial_native_readback != EquationEditorVerificationState::Passed
        || proof.saved_native_readback != EquationEditorVerificationState::Passed
        || proof.reopen_native_readback != EquationEditorVerificationState::Passed
        || proof.save != EquationEditorVerificationState::Passed
        || proof.close != EquationEditorVerificationState::Passed
        || proof.reopen != EquationEditorVerificationState::Passed
        || proof.all_phases != EquationEditorVerificationState::Passed
    {
        return Err(EquationEditorSmokeError::AutomationEvidenceIncomplete);
    }
    validate_digest(&proof.trace_sha256)?;
    validate_digest(&proof.oracle_receipt_sha256)?;
    if proof.trace_sha256 == proof.oracle_receipt_sha256 {
        return Err(EquationEditorSmokeError::AutomationEvidenceIncomplete);
    }
    Ok(())
}

fn validate_snapshot(
    snapshot: &EquationEditorSmokeSnapshot,
) -> Result<(), EquationEditorSmokeError> {
    if snapshot.object_id == 0 || snapshot.native_object_count == 0 {
        return Err(EquationEditorSmokeError::InvalidIdentity);
    }
    for digest in [
        &snapshot.artifact_sha256,
        &snapshot.package_graph_sha256,
        &snapshot.document_flow_sha256,
        &snapshot.semantic_sha256,
        &snapshot.script_sha256,
    ] {
        validate_digest(digest)?;
    }
    Ok(())
}

fn validate_digest(value: &str) -> Result<(), EquationEditorSmokeError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(EquationEditorSmokeError::InvalidIdentity);
    }
    Ok(())
}

fn hash_json(value: &impl Serialize) -> Result<String, EquationEditorSmokeError> {
    let bytes = serde_json::to_vec(value).map_err(|_| EquationEditorSmokeError::Serialization)?;
    Ok(hex::encode(Sha256::digest(bytes)))
}

fn bounded_json(
    value: &impl Serialize,
    limits: EquationEditorSmokeLimits,
) -> Result<Vec<u8>, EquationEditorSmokeError> {
    let bytes = serde_json::to_vec(value).map_err(|_| EquationEditorSmokeError::Serialization)?;
    if bytes.len() > limits.0.serialized_bytes {
        return Err(EquationEditorSmokeError::OutputLimit);
    }
    Ok(bytes)
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum EquationEditorSmokeError {
    #[error("equation editor smoke limit configuration is invalid")]
    InvalidLimit,
    #[error("equation editor smoke JSON is malformed, duplicated, unknown or oversized")]
    InvalidJson,
    #[error("equation editor smoke schema version is unsupported")]
    UnsupportedVersion,
    #[error("equation editor smoke target profile is unsupported")]
    UnsupportedProfile,
    #[error("equation editor smoke identity is invalid")]
    InvalidIdentity,
    #[error("equation editor smoke source state drifted")]
    SourceStateDrift,
    #[error("equation editor smoke source semantic state drifted")]
    SourceSemanticDrift,
    #[error("equation editor smoke MathAst admission failed")]
    MathAst,
    #[error("equation editor smoke EqEdit compilation failed")]
    EqEdit,
    #[error("equation editor smoke EqEdit semantic round-trip drifted")]
    SemanticRoundtrip,
    #[error("equation editor smoke requested no semantic change")]
    NoSemanticChange,
    #[error("equation editor smoke native editor canonicalization mismatched the requested math")]
    EditorCanonicalizationMismatch,
    #[error("equation editor smoke must change exactly one canonical token")]
    TokenChangeMismatch,
    #[error("equation editor smoke evidence digest is untrusted")]
    UntrustedEvidence,
    #[error("equation editor smoke plan digest is untrusted")]
    UntrustedPlan,
    #[error("equation editor smoke plan content mismatched its bindings")]
    PlanMismatch,
    #[error("equation editor smoke evidence does not match the plan")]
    EvidenceMismatch,
    #[error("equation editor smoke exact target identity mismatched")]
    TargetMismatch,
    #[error("equation editor smoke effect failed or is unknown")]
    EffectNotProven,
    #[error("equation editor smoke manual evidence is incomplete")]
    ManualEvidenceIncomplete,
    #[error("equation editor smoke automation evidence is incomplete")]
    AutomationEvidenceIncomplete,
    #[error("equation editor smoke mutation or reopen state mismatched")]
    MutationMismatch,
    #[error("equation editor smoke fallback or native-object replacement was detected")]
    FallbackDetected,
    #[error("equation editor smoke output exceeds its finite bound")]
    OutputLimit,
    #[error("equation editor smoke serialization failed")]
    Serialization,
}

impl EquationEditorSmokeError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "equation_editor_smoke_invalid_limit",
            Self::InvalidJson => "equation_editor_smoke_invalid_json",
            Self::UnsupportedVersion => "equation_editor_smoke_unsupported_version",
            Self::UnsupportedProfile => "equation_editor_smoke_unsupported_profile",
            Self::InvalidIdentity => "equation_editor_smoke_invalid_identity",
            Self::SourceStateDrift => "equation_editor_smoke_source_state_drift",
            Self::SourceSemanticDrift => "equation_editor_smoke_source_semantic_drift",
            Self::MathAst => "equation_editor_smoke_math_ast",
            Self::EqEdit => "equation_editor_smoke_eqedit",
            Self::SemanticRoundtrip => "equation_editor_smoke_semantic_roundtrip",
            Self::NoSemanticChange => "equation_editor_smoke_no_semantic_change",
            Self::EditorCanonicalizationMismatch => {
                "equation_editor_smoke_editor_canonicalization_mismatch"
            }
            Self::TokenChangeMismatch => "equation_editor_smoke_token_change_mismatch",
            Self::UntrustedEvidence => "equation_editor_smoke_untrusted_evidence",
            Self::UntrustedPlan => "equation_editor_smoke_untrusted_plan",
            Self::PlanMismatch => "equation_editor_smoke_plan_mismatch",
            Self::EvidenceMismatch => "equation_editor_smoke_evidence_mismatch",
            Self::TargetMismatch => "equation_editor_smoke_target_mismatch",
            Self::EffectNotProven => "equation_editor_smoke_effect_not_proven",
            Self::ManualEvidenceIncomplete => "equation_editor_smoke_manual_evidence_incomplete",
            Self::AutomationEvidenceIncomplete => {
                "equation_editor_smoke_automation_evidence_incomplete"
            }
            Self::MutationMismatch => "equation_editor_smoke_mutation_mismatch",
            Self::FallbackDetected => "equation_editor_smoke_fallback_detected",
            Self::OutputLimit => "equation_editor_smoke_output_limit",
            Self::Serialization => "equation_editor_smoke_serialization",
        }
    }
}
