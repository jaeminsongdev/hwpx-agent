use std::collections::HashSet;
use std::fmt;

use domain_ir::{MathAst, MathAstLimits};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    EQEDIT_ADAPTER_SCHEMA_VERSION, EQEDIT_PROFILE_VERSION, EqEditEngine, EqEditLimits,
    EqEditParseRequestDraft, LATEX_ADAPTER_SCHEMA_VERSION, LatexAdapter, LatexAdapterLimits,
    LatexParseOutcome, LatexParseRequestDraft, MATHML_ADAPTER_SCHEMA_VERSION, MathMlAdapter,
    MathMlAdapterLimits, MathMlParseRequestDraft,
};

pub const EQUATION_CORPUS_SCHEMA_VERSION: &str = "hwpx-agent.equation-corpus/v1";
pub const EQUATION_CORPUS_PROFILE_VERSION: &str =
    "hwpx-agent.equation-corpus.hangul-2020-11.0.0.9136-x86-ko-KR/v1";
pub const EQUATION_CORPUS_RECEIPT_SCHEMA_VERSION: &str = "hwpx-agent.equation-corpus-receipt/v1";

const MIN_TIER_A: usize = 40;
const MIN_TIER_B: usize = 10;
const MIN_TIER_C_PRESERVE: usize = 2;
const MIN_TIER_C_REJECT: usize = 2;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EquationCorpusLimitConfig {
    pub manifest_bytes: usize,
    pub cases: usize,
    pub case_id_bytes: usize,
    pub source_bytes: usize,
    pub legacy_bytes: usize,
    pub serialized_bytes: usize,
}

impl Default for EquationCorpusLimitConfig {
    fn default() -> Self {
        Self {
            manifest_bytes: 8 * 1024 * 1024,
            cases: 8_192,
            case_id_bytes: 128,
            source_bytes: 1024 * 1024,
            legacy_bytes: 4 * 1024 * 1024,
            serialized_bytes: 4 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct EquationCorpusLimits(EquationCorpusLimitConfig);

impl EquationCorpusLimits {
    pub const HARD_MAX_MANIFEST_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_CASES: usize = 65_536;
    pub const HARD_MAX_CASE_ID_BYTES: usize = 512;
    pub const HARD_MAX_SOURCE_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_LEGACY_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_SERIALIZED_BYTES: usize = 32 * 1024 * 1024;

    /// Creates finite P07-08 corpus limits.
    ///
    /// # Errors
    ///
    /// Rejects zero, hard-ceiling, and subordinate-limit mismatches.
    pub fn new(config: EquationCorpusLimitConfig) -> Result<Self, EquationCorpusError> {
        if config.manifest_bytes == 0
            || config.manifest_bytes > Self::HARD_MAX_MANIFEST_BYTES
            || config.cases < MIN_TIER_A + MIN_TIER_B + MIN_TIER_C_PRESERVE + MIN_TIER_C_REJECT
            || config.cases > Self::HARD_MAX_CASES
            || config.case_id_bytes == 0
            || config.case_id_bytes > Self::HARD_MAX_CASE_ID_BYTES
            || config.source_bytes == 0
            || config.source_bytes > Self::HARD_MAX_SOURCE_BYTES
            || config.legacy_bytes == 0
            || config.legacy_bytes > Self::HARD_MAX_LEGACY_BYTES
            || config.legacy_bytes < config.source_bytes
            || config.serialized_bytes == 0
            || config.serialized_bytes > Self::HARD_MAX_SERIALIZED_BYTES
        {
            return Err(EquationCorpusError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> EquationCorpusLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum CorpusTier {
    A,
    B,
    C,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum CorpusSourceKind {
    Latex,
    Mathml,
    Eqedit,
    LegacyEqedit,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum CorpusExpectation {
    SemanticRoundtrip,
    PreserveExact,
    Reject,
}

#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CorpusManifestDraft {
    schema_version: String,
    profile_version: String,
    cases: Vec<CorpusCaseDraft>,
}

impl fmt::Debug for CorpusManifestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CorpusManifestDraft")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("case_count", &self.cases.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CorpusCaseDraft {
    id: String,
    tier: CorpusTier,
    source_kind: CorpusSourceKind,
    source: String,
    expectation: CorpusExpectation,
    expected_error_code: Option<String>,
}

impl fmt::Debug for CorpusCaseDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CorpusCaseDraft")
            .field("id", &"<redacted>")
            .field("tier", &self.tier)
            .field("source_kind", &self.source_kind)
            .field("source", &"<redacted>")
            .field("expectation", &self.expectation)
            .field("expected_error_code", &self.expected_error_code)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct LegacyEquationScript {
    sha256: String,
    bytes: Vec<u8>,
}

impl LegacyEquationScript {
    /// Admits one opaque legacy script for byte-exact preservation only.
    ///
    /// # Errors
    ///
    /// Rejects empty, oversized, digest-mismatched, NUL-containing, or non-UTF-8 bytes.
    pub fn new(
        bytes: Vec<u8>,
        expected_sha256: &str,
        limits: EquationCorpusLimits,
    ) -> Result<Self, EquationCorpusError> {
        require_digest(expected_sha256)?;
        if bytes.is_empty()
            || bytes.len() > limits.0.legacy_bytes
            || bytes.contains(&0)
            || std::str::from_utf8(&bytes).is_err()
            || hex::encode(Sha256::digest(&bytes)) != expected_sha256
        {
            return Err(EquationCorpusError::LegacyBoundary);
        }
        Ok(Self {
            sha256: expected_sha256.to_owned(),
            bytes,
        })
    }

    #[must_use]
    pub fn sha256(&self) -> &str {
        &self.sha256
    }

    /// Returns the unchanged bytes for a preserving package writer.
    #[must_use]
    pub fn preserved_bytes(&self) -> &[u8] {
        &self.bytes
    }
}

impl fmt::Debug for LegacyEquationScript {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LegacyEquationScript")
            .field("sha256", &"<redacted>")
            .field("bytes", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct EquationCorpusReceipt {
    schema_version: &'static str,
    profile_version: &'static str,
    manifest_sha256: String,
    total_cases: usize,
    tier_a_semantic_passed: usize,
    tier_b_semantic_passed: usize,
    tier_c_preserve_passed: usize,
    tier_c_negative_passed: usize,
    semantic_roundtrip_failures: usize,
    legacy_preservation_failures: usize,
    negative_failures: usize,
    silent_approximation_count: usize,
    tier_a_pass_millionths: u32,
    tier_b_component_pass_millionths: u32,
    tier_b_target_state: &'static str,
    actual_hangul: bool,
    product_complete: bool,
}

impl EquationCorpusReceipt {
    #[must_use]
    pub const fn total_cases(&self) -> usize {
        self.total_cases
    }

    #[must_use]
    pub const fn tier_a_semantic_passed(&self) -> usize {
        self.tier_a_semantic_passed
    }

    #[must_use]
    pub const fn tier_b_semantic_passed(&self) -> usize {
        self.tier_b_semantic_passed
    }

    #[must_use]
    pub const fn tier_c_preserve_passed(&self) -> usize {
        self.tier_c_preserve_passed
    }

    #[must_use]
    pub const fn tier_c_negative_passed(&self) -> usize {
        self.tier_c_negative_passed
    }

    #[must_use]
    pub const fn silent_approximation_count(&self) -> usize {
        self.silent_approximation_count
    }

    #[must_use]
    pub const fn tier_b_target_state(&self) -> &'static str {
        self.tier_b_target_state
    }

    /// Serializes the content-free receipt within its finite output bound.
    ///
    /// # Errors
    ///
    /// Returns an error when serialization fails or exceeds the configured bound.
    pub fn canonical_json(
        &self,
        limits: EquationCorpusLimits,
    ) -> Result<Vec<u8>, EquationCorpusError> {
        let bytes = serde_json::to_vec(self).map_err(|_| EquationCorpusError::Serialization)?;
        if bytes.len() > limits.0.serialized_bytes {
            return Err(EquationCorpusError::OutputLimit);
        }
        Ok(bytes)
    }
}

impl fmt::Debug for EquationCorpusReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("EquationCorpusReceipt")
            .field("schema_version", &self.schema_version)
            .field("profile_version", &self.profile_version)
            .field("manifest_sha256", &"<redacted>")
            .field("total_cases", &self.total_cases)
            .field("tier_a_semantic_passed", &self.tier_a_semantic_passed)
            .field("tier_b_semantic_passed", &self.tier_b_semantic_passed)
            .field("tier_c_preserve_passed", &self.tier_c_preserve_passed)
            .field("tier_c_negative_passed", &self.tier_c_negative_passed)
            .field("failures", &"<redacted>")
            .field(
                "silent_approximation_count",
                &self.silent_approximation_count,
            )
            .field("tier_a_pass_millionths", &self.tier_a_pass_millionths)
            .field(
                "tier_b_component_pass_millionths",
                &self.tier_b_component_pass_millionths,
            )
            .field("tier_b_target_state", &self.tier_b_target_state)
            .field("actual_hangul", &self.actual_hangul)
            .field("product_complete", &self.product_complete)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug)]
pub struct EquationCorpusRunner {
    limits: EquationCorpusLimits,
    math_limits: MathAstLimits,
    latex_limits: LatexAdapterLimits,
    mathml_limits: MathMlAdapterLimits,
    eqedit_limits: EqEditLimits,
}

impl EquationCorpusRunner {
    /// Creates a finite multi-adapter corpus runner.
    ///
    /// # Errors
    ///
    /// Rejects subordinate source limits that exceed the corpus boundary.
    pub fn new(
        limits: EquationCorpusLimits,
        math_limits: MathAstLimits,
        latex_limits: LatexAdapterLimits,
        mathml_limits: MathMlAdapterLimits,
        eqedit_limits: EqEditLimits,
    ) -> Result<Self, EquationCorpusError> {
        if latex_limits.config().source_bytes > limits.0.source_bytes
            || mathml_limits.config().source_bytes > limits.0.source_bytes
            || eqedit_limits.config().source_bytes > limits.0.source_bytes
        {
            return Err(EquationCorpusError::InvalidLimit);
        }
        Ok(Self {
            limits,
            math_limits,
            latex_limits,
            mathml_limits,
            eqedit_limits,
        })
    }

    /// Runs one exact hash-pinned P07-08 manifest without choosing ambiguity or approximation.
    ///
    /// # Errors
    ///
    /// Rejects untrusted/invalid manifests, incomplete tiers, semantic drift, preservation drift,
    /// wrong negative errors, and all finite-limit failures.
    pub fn run_json(
        &self,
        bytes: &[u8],
        trusted_sha256: &str,
    ) -> Result<EquationCorpusReceipt, EquationCorpusError> {
        if bytes.is_empty() || bytes.len() > self.limits.0.manifest_bytes {
            return Err(EquationCorpusError::ManifestLimit);
        }
        require_digest(trusted_sha256)?;
        let manifest_sha256 = hex::encode(Sha256::digest(bytes));
        if manifest_sha256 != trusted_sha256 {
            return Err(EquationCorpusError::UntrustedManifest);
        }
        let manifest: CorpusManifestDraft =
            serde_json::from_slice(bytes).map_err(|_| EquationCorpusError::InvalidManifest)?;
        if manifest.schema_version != EQUATION_CORPUS_SCHEMA_VERSION
            || manifest.profile_version != EQUATION_CORPUS_PROFILE_VERSION
        {
            return Err(EquationCorpusError::UnsupportedProfile);
        }
        if manifest.cases.len() > self.limits.0.cases {
            return Err(EquationCorpusError::ManifestLimit);
        }
        self.run_manifest(&manifest, manifest_sha256)
    }

    fn run_manifest(
        &self,
        manifest: &CorpusManifestDraft,
        manifest_sha256: String,
    ) -> Result<EquationCorpusReceipt, EquationCorpusError> {
        let mut ids = HashSet::with_capacity(manifest.cases.len());
        let mut a_total = 0;
        let mut b_total = 0;
        let mut c_preserve_total = 0;
        let mut c_reject_total = 0;
        let mut a_pass = 0;
        let mut b_pass = 0;
        let mut c_preserve_pass = 0;
        let mut c_reject_pass = 0;
        for case in &manifest.cases {
            validate_case_shape(case, self.limits, &mut ids)?;
            match (case.tier, case.expectation) {
                (CorpusTier::A, CorpusExpectation::SemanticRoundtrip) => {
                    a_total += 1;
                    self.semantic_roundtrip(case)?;
                    a_pass += 1;
                }
                (CorpusTier::B, CorpusExpectation::SemanticRoundtrip) => {
                    b_total += 1;
                    self.semantic_roundtrip(case)?;
                    b_pass += 1;
                }
                (CorpusTier::C, CorpusExpectation::PreserveExact) => {
                    c_preserve_total += 1;
                    self.preserve_exact(case)?;
                    c_preserve_pass += 1;
                }
                (CorpusTier::C, CorpusExpectation::Reject) => {
                    c_reject_total += 1;
                    self.reject_exact(case)?;
                    c_reject_pass += 1;
                }
                _ => return Err(EquationCorpusError::TierPolicy),
            }
        }
        if a_total < MIN_TIER_A
            || b_total < MIN_TIER_B
            || c_preserve_total < MIN_TIER_C_PRESERVE
            || c_reject_total < MIN_TIER_C_REJECT
        {
            return Err(EquationCorpusError::IncompleteTier);
        }
        let receipt = EquationCorpusReceipt {
            schema_version: EQUATION_CORPUS_RECEIPT_SCHEMA_VERSION,
            profile_version: EQUATION_CORPUS_PROFILE_VERSION,
            manifest_sha256,
            total_cases: manifest.cases.len(),
            tier_a_semantic_passed: a_pass,
            tier_b_semantic_passed: b_pass,
            tier_c_preserve_passed: c_preserve_pass,
            tier_c_negative_passed: c_reject_pass,
            semantic_roundtrip_failures: 0,
            legacy_preservation_failures: 0,
            negative_failures: 0,
            silent_approximation_count: 0,
            tier_a_pass_millionths: ratio_millionths(a_pass, a_total)?,
            tier_b_component_pass_millionths: ratio_millionths(b_pass, b_total)?,
            tier_b_target_state: "not_run",
            actual_hangul: false,
            product_complete: false,
        };
        let _ = receipt.canonical_json(self.limits)?;
        Ok(receipt)
    }

    fn semantic_roundtrip(&self, case: &CorpusCaseDraft) -> Result<(), EquationCorpusError> {
        if case.expected_error_code.is_some() || case.source_kind == CorpusSourceKind::LegacyEqedit
        {
            return Err(EquationCorpusError::TierPolicy);
        }
        let ast = self.parse_ast(case)?;
        let engine = EqEditEngine::new(self.eqedit_limits, self.math_limits)
            .map_err(|_| EquationCorpusError::Adapter)?;
        let compiled = engine
            .compile(&ast)
            .map_err(|_| EquationCorpusError::SemanticRoundtrip)?;
        let reparsed = engine
            .parse(EqEditParseRequestDraft {
                schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
                profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
                source: compiled.script().to_owned(),
            })
            .map_err(|_| EquationCorpusError::SemanticRoundtrip)?;
        if !ast.semantically_eq(reparsed.ast()) {
            return Err(EquationCorpusError::SemanticRoundtrip);
        }
        Ok(())
    }

    fn parse_ast(&self, case: &CorpusCaseDraft) -> Result<MathAst, EquationCorpusError> {
        match case.source_kind {
            CorpusSourceKind::Latex => {
                let result = LatexAdapter::new(self.latex_limits, self.math_limits)
                    .map_err(|_| EquationCorpusError::Adapter)?
                    .parse(LatexParseRequestDraft {
                        schema_version: LATEX_ADAPTER_SCHEMA_VERSION.to_owned(),
                        source: case.source.clone(),
                        macros: Vec::new(),
                    })
                    .map_err(|_| EquationCorpusError::Adapter)?;
                match result.outcome() {
                    LatexParseOutcome::Parsed { ast } => Ok(ast.clone()),
                    LatexParseOutcome::Ambiguous { .. } => {
                        Err(EquationCorpusError::SilentApproximation)
                    }
                }
            }
            CorpusSourceKind::Mathml => MathMlAdapter::new(self.mathml_limits, self.math_limits)
                .map_err(|_| EquationCorpusError::Adapter)?
                .parse(MathMlParseRequestDraft {
                    schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
                    source: case.source.clone(),
                })
                .map(|value| value.ast().clone())
                .map_err(|_| EquationCorpusError::Adapter),
            CorpusSourceKind::Eqedit => EqEditEngine::new(self.eqedit_limits, self.math_limits)
                .map_err(|_| EquationCorpusError::Adapter)?
                .parse(EqEditParseRequestDraft {
                    schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
                    profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
                    source: case.source.clone(),
                })
                .map(|value| value.ast().clone())
                .map_err(|_| EquationCorpusError::Adapter),
            CorpusSourceKind::LegacyEqedit => Err(EquationCorpusError::TierPolicy),
        }
    }

    fn preserve_exact(&self, case: &CorpusCaseDraft) -> Result<(), EquationCorpusError> {
        if case.source_kind != CorpusSourceKind::LegacyEqedit || case.expected_error_code.is_some()
        {
            return Err(EquationCorpusError::TierPolicy);
        }
        let bytes = case.source.as_bytes().to_vec();
        let digest = hex::encode(Sha256::digest(&bytes));
        let preserved = LegacyEquationScript::new(bytes.clone(), &digest, self.limits)?;
        if preserved.preserved_bytes() != bytes || preserved.sha256() != digest {
            return Err(EquationCorpusError::Preservation);
        }
        Ok(())
    }

    fn reject_exact(&self, case: &CorpusCaseDraft) -> Result<(), EquationCorpusError> {
        let expected = case
            .expected_error_code
            .as_deref()
            .ok_or(EquationCorpusError::TierPolicy)?;
        let actual = match case.source_kind {
            CorpusSourceKind::Latex => LatexAdapter::new(self.latex_limits, self.math_limits)
                .map_err(|_| EquationCorpusError::Adapter)?
                .parse(LatexParseRequestDraft {
                    schema_version: LATEX_ADAPTER_SCHEMA_VERSION.to_owned(),
                    source: case.source.clone(),
                    macros: Vec::new(),
                })
                .err()
                .map(crate::LatexAdapterError::code),
            CorpusSourceKind::Mathml => MathMlAdapter::new(self.mathml_limits, self.math_limits)
                .map_err(|_| EquationCorpusError::Adapter)?
                .parse(MathMlParseRequestDraft {
                    schema_version: MATHML_ADAPTER_SCHEMA_VERSION.to_owned(),
                    source: case.source.clone(),
                })
                .err()
                .map(crate::MathMlAdapterError::code),
            CorpusSourceKind::Eqedit => EqEditEngine::new(self.eqedit_limits, self.math_limits)
                .map_err(|_| EquationCorpusError::Adapter)?
                .parse(EqEditParseRequestDraft {
                    schema_version: EQEDIT_ADAPTER_SCHEMA_VERSION.to_owned(),
                    profile_version: EQEDIT_PROFILE_VERSION.to_owned(),
                    source: case.source.clone(),
                })
                .err()
                .map(crate::EqEditError::code),
            CorpusSourceKind::LegacyEqedit => return Err(EquationCorpusError::TierPolicy),
        };
        let Some(actual) = actual else {
            return Err(EquationCorpusError::SilentApproximation);
        };
        if actual != expected {
            return Err(EquationCorpusError::NegativeMismatch);
        }
        Ok(())
    }
}

fn validate_case_shape(
    case: &CorpusCaseDraft,
    limits: EquationCorpusLimits,
    ids: &mut HashSet<String>,
) -> Result<(), EquationCorpusError> {
    if case.id.is_empty()
        || case.id.len() > limits.0.case_id_bytes
        || !case
            .id
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-')
        || !ids.insert(case.id.clone())
        || case.source.is_empty()
        || case.source.len() > limits.0.source_bytes
        || case.source.contains('\0')
    {
        return Err(EquationCorpusError::InvalidCase);
    }
    if let Some(code) = &case.expected_error_code
        && (code.is_empty()
            || code.len() > 128
            || !code
                .bytes()
                .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_'))
    {
        return Err(EquationCorpusError::InvalidCase);
    }
    Ok(())
}

fn ratio_millionths(passed: usize, total: usize) -> Result<u32, EquationCorpusError> {
    let passed = u64::try_from(passed).map_err(|_| EquationCorpusError::CountOverflow)?;
    let total = u64::try_from(total).map_err(|_| EquationCorpusError::CountOverflow)?;
    let scaled = passed
        .checked_mul(1_000_000)
        .ok_or(EquationCorpusError::CountOverflow)?;
    u32::try_from(scaled / total).map_err(|_| EquationCorpusError::CountOverflow)
}

fn require_digest(value: &str) -> Result<(), EquationCorpusError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(EquationCorpusError::InvalidDigest);
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum EquationCorpusError {
    #[error("equation corpus limit configuration is invalid")]
    InvalidLimit,
    #[error("equation corpus manifest is empty or oversized")]
    ManifestLimit,
    #[error("equation corpus manifest digest is invalid")]
    InvalidDigest,
    #[error("equation corpus manifest digest is untrusted")]
    UntrustedManifest,
    #[error("equation corpus manifest is malformed, duplicated or unknown")]
    InvalidManifest,
    #[error("equation corpus profile is unsupported")]
    UnsupportedProfile,
    #[error("equation corpus case identity or source is invalid")]
    InvalidCase,
    #[error("equation corpus tier is incomplete")]
    IncompleteTier,
    #[error("equation corpus case violates its tier policy")]
    TierPolicy,
    #[error("equation corpus adapter rejected a positive case")]
    Adapter,
    #[error("equation corpus semantic round-trip mismatched")]
    SemanticRoundtrip,
    #[error("equation corpus legacy boundary is invalid")]
    LegacyBoundary,
    #[error("equation corpus legacy preservation mismatched")]
    Preservation,
    #[error("equation corpus negative error mismatched")]
    NegativeMismatch,
    #[error("equation corpus input was silently accepted or approximated")]
    SilentApproximation,
    #[error("equation corpus count arithmetic overflowed")]
    CountOverflow,
    #[error("equation corpus receipt exceeds its output bound")]
    OutputLimit,
    #[error("equation corpus receipt serialization failed")]
    Serialization,
}

impl EquationCorpusError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "equation_corpus_invalid_limit",
            Self::ManifestLimit => "equation_corpus_manifest_limit",
            Self::InvalidDigest => "equation_corpus_invalid_digest",
            Self::UntrustedManifest => "equation_corpus_untrusted_manifest",
            Self::InvalidManifest => "equation_corpus_invalid_manifest",
            Self::UnsupportedProfile => "equation_corpus_unsupported_profile",
            Self::InvalidCase => "equation_corpus_invalid_case",
            Self::IncompleteTier => "equation_corpus_incomplete_tier",
            Self::TierPolicy => "equation_corpus_tier_policy",
            Self::Adapter => "equation_corpus_adapter",
            Self::SemanticRoundtrip => "equation_corpus_semantic_roundtrip",
            Self::LegacyBoundary => "equation_corpus_legacy_boundary",
            Self::Preservation => "equation_corpus_preservation",
            Self::NegativeMismatch => "equation_corpus_negative_mismatch",
            Self::SilentApproximation => "equation_corpus_silent_approximation",
            Self::CountOverflow => "equation_corpus_count_overflow",
            Self::OutputLimit => "equation_corpus_output_limit",
            Self::Serialization => "equation_corpus_serialization",
        }
    }
}
