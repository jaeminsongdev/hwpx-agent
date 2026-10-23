use std::{collections::BTreeSet, fmt};

use domain_ir::{
    HyperlinkEntry, HyperlinkSemanticBinding, HyperlinkTarget, LinkAnchor, LinkPoint,
    LinkReferenceBuilder, LinkReferenceDocumentState, LinkReferenceError, LinkReferenceLimits,
    LinkReferencePlan,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlTokenKind,
};

pub const HYPERLINK_HWPX_PROFILE_ID: &str =
    "hwpx-agent.hyperlink-hwpx.hangul-2020-https-current-tab/v1";

const PLAN_SCHEMA_VERSION: &str = "hwpx-agent.hyperlink-hwpx-plan/v1";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
const CATEGORY: &str = "HWPHYPERLINK_TYPE_URL";
const TARGET_TYPE: &str = "HWPHYPERLINK_TARGET_BOOKMARK";
const DOC_OPEN_TYPE: &str = "HWPHYPERLINK_JUMP_CURRENTTAB";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct HyperlinkHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub paragraphs: usize,
    pub runs_per_paragraph: usize,
    pub hyperlinks: usize,
    pub text_bytes: usize,
    pub plan_bytes: usize,
    pub output_bytes: usize,
}

impl Default for HyperlinkHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            paragraphs: 262_144,
            runs_per_paragraph: 65_536,
            hyperlinks: 65_536,
            text_bytes: 1024 * 1024,
            plan_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct HyperlinkHwpxLimits(HyperlinkHwpxLimitConfig);

impl HyperlinkHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 4 * 1024 * 1024;
    pub const HARD_MAX_PLAN_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;

    /// Creates finite adapter limits without silently clamping caller input.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding limits.
    pub fn new(config: HyperlinkHwpxLimitConfig) -> Result<Self, HyperlinkHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.paragraphs == 0
            || config.paragraphs > Self::HARD_MAX_ITEMS
            || config.runs_per_paragraph == 0
            || config.runs_per_paragraph > Self::HARD_MAX_ITEMS
            || config.hyperlinks == 0
            || config.hyperlinks > Self::HARD_MAX_ITEMS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
        {
            return Err(HyperlinkHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> HyperlinkHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct HyperlinkHwpxReadback {
    pub state: LinkReferenceDocumentState,
    pub section_sha256: [u8; 32],
    pub hyperlink_wrapper_sha256: Vec<[u8; 32]>,
    pub hyperlink_count: usize,
}

impl fmt::Debug for HyperlinkHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HyperlinkHwpxReadback")
            .field("hyperlink_count", &self.hyperlink_count)
            .field("state", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct HyperlinkHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    source_section_sha256: [u8; 32],
    source_hyperlink_wrapper_sha256: Vec<[u8; 32]>,
    source_state: LinkReferenceDocumentState,
    source_state_sha256: String,
    source_document_flow_sha256: String,
    domain_plan: LinkReferencePlan,
    plan_sha256: String,
}

impl HyperlinkHwpxPlan {
    #[must_use]
    pub const fn domain_plan(&self) -> &LinkReferencePlan {
        &self.domain_plan
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Returns deterministic bounded JSON for the sealed adapter plan.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: HyperlinkHwpxLimits,
    ) -> Result<Vec<u8>, HyperlinkHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for HyperlinkHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HyperlinkHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.domain_plan.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct HyperlinkHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub inserted_hyperlinks: usize,
    pub edited_hyperlinks: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for HyperlinkHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HyperlinkHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("inserted_hyperlinks", &self.inserted_hyperlinks)
            .field("edited_hyperlinks", &self.edited_hyperlinks)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum HyperlinkHwpxError {
    #[error("hyperlink HWPX limits are invalid")]
    InvalidLimit,
    #[error("hyperlink HWPX input exceeds a finite limit")]
    InputLimit,
    #[error("hyperlink HWPX section structure is unsupported")]
    UnsupportedStructure,
    #[error("hyperlink HWPX native field is missing, duplicated, or malformed")]
    InvalidHyperlink,
    #[error("hyperlink HWPX projection differs from the bound typed state")]
    ProjectionMismatch,
    #[error("hyperlink operation is not representable by the Hangul 2020 HTTPS profile")]
    NonRepresentable,
    #[error("hyperlink HWPX section, state, field, or flow drifted")]
    SourceDrift,
    #[error("hyperlink HWPX plan was tampered with")]
    PlanTampered,
    #[error("hyperlink HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("hyperlink HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("hyperlink HWPX allocation failed")]
    AllocationFailed,
    #[error("hyperlink link/reference domain validation failed")]
    Domain(#[from] LinkReferenceError),
    #[error("hyperlink preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl HyperlinkHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "hyperlink_hwpx_invalid_limit",
            Self::InputLimit => "hyperlink_hwpx_input_limit",
            Self::UnsupportedStructure => "hyperlink_hwpx_unsupported_structure",
            Self::InvalidHyperlink => "hyperlink_hwpx_invalid_hyperlink",
            Self::ProjectionMismatch => "hyperlink_hwpx_projection_mismatch",
            Self::NonRepresentable => "hyperlink_hwpx_non_representable",
            Self::SourceDrift => "hyperlink_hwpx_source_drift",
            Self::PlanTampered => "hyperlink_hwpx_plan_tampered",
            Self::PreservationMismatch => "hyperlink_hwpx_preservation_mismatch",
            Self::OutputLimit => "hyperlink_hwpx_output_limit",
            Self::AllocationFailed => "hyperlink_hwpx_allocation_failed",
            Self::Domain(_) => "hyperlink_hwpx_domain",
            Self::Preserving(_) => "hyperlink_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct HyperlinkHwpxReader;

impl HyperlinkHwpxReader {
    /// Returns the canonical semantic digest for the exact discovered HTTPS parameter tuple.
    ///
    /// # Errors
    ///
    /// Rejects non-HTTPS or malformed targets and bounded serialization failures.
    pub fn parameters_sha256(
        target: &HyperlinkTarget,
        state_limits: LinkReferenceLimits,
        hwpx_limits: HyperlinkHwpxLimits,
    ) -> Result<String, HyperlinkHwpxError> {
        let HyperlinkTarget::Https { uri } = target else {
            return Err(HyperlinkHwpxError::NonRepresentable);
        };
        let _ = target.external_approval_sha256(state_limits)?;
        semantic_parameters_sha256(uri, hwpx_limits)
    }

    /// Verifies the complete native HTTPS hyperlink projection against one typed state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, stale, non-profile, or over-limit sections.
    pub fn read_section(
        source: &[u8],
        expected: &LinkReferenceDocumentState,
        state_limits: LinkReferenceLimits,
        hwpx_limits: HyperlinkHwpxLimits,
    ) -> Result<HyperlinkHwpxReadback, HyperlinkHwpxError> {
        let parsed = parse_hyperlinks(source, expected, state_limits, hwpx_limits)?;
        let mut wrapper_digests = Vec::new();
        wrapper_digests
            .try_reserve_exact(parsed.projections.len())
            .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
        for projection in &parsed.projections {
            wrapper_digests.push(projection.wrapper_sha256);
        }
        Ok(HyperlinkHwpxReadback {
            state: expected.clone(),
            section_sha256: Sha256::digest(source).into(),
            hyperlink_wrapper_sha256: wrapper_digests,
            hyperlink_count: parsed.projections.len(),
        })
    }
}

#[derive(Debug)]
pub struct HyperlinkHwpxBuilder;

impl HyperlinkHwpxBuilder {
    /// Binds one exact REF-033 or REF-034 plan to a complete section snapshot.
    ///
    /// # Errors
    ///
    /// Rejects unsupported transitions, source projection, state, flow, plan, or limits.
    pub fn plan(
        source: &[u8],
        source_state: &LinkReferenceDocumentState,
        domain_plan: &LinkReferencePlan,
        current_document_flow_sha256: &str,
        state_limits: LinkReferenceLimits,
        hwpx_limits: HyperlinkHwpxLimits,
    ) -> Result<HyperlinkHwpxPlan, HyperlinkHwpxError> {
        if !matches!(
            domain_plan.capability_id(),
            "ref.hyperlink_insert" | "ref.hyperlink_edit"
        ) || domain_plan.source_document_flow_sha256() != current_document_flow_sha256
        {
            return Err(HyperlinkHwpxError::NonRepresentable);
        }
        let built = LinkReferenceBuilder::build(
            domain_plan,
            source_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let _ = hyperlink_transition(
            source_state,
            &built.state,
            domain_plan.capability_id(),
            state_limits,
            hwpx_limits,
        )?;
        let readback =
            HyperlinkHwpxReader::read_section(source, source_state, state_limits, hwpx_limits)?;
        let mut plan = HyperlinkHwpxPlan {
            schema_version: PLAN_SCHEMA_VERSION,
            profile_id: HYPERLINK_HWPX_PROFILE_ID,
            source_section_sha256: readback.section_sha256,
            source_hyperlink_wrapper_sha256: readback.hyperlink_wrapper_sha256,
            source_state: source_state.clone(),
            source_state_sha256: source_state.canonical_sha256(state_limits)?,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            domain_plan: domain_plan.clone(),
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, hwpx_limits)?;
        let _ = plan.canonical_json(hwpx_limits)?;
        Ok(plan)
    }
}

#[derive(Debug)]
pub struct HyperlinkHwpxLowerer;

impl HyperlinkHwpxLowerer {
    /// Applies exactly one native HTTPS hyperlink insertion or target edit.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, state, flow, projection, preservation, or limit drift.
    pub fn lower_section_with_receipt(
        source: &[u8],
        plan: &HyperlinkHwpxPlan,
        current_state: &LinkReferenceDocumentState,
        current_document_flow_sha256: &str,
        state_limits: LinkReferenceLimits,
        hwpx_limits: HyperlinkHwpxLimits,
    ) -> Result<(Vec<u8>, HyperlinkHwpxLoweringReceipt), HyperlinkHwpxError> {
        validate_plan(plan, state_limits, hwpx_limits)?;
        if <[u8; 32]>::from(Sha256::digest(source)) != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || current_state.canonical_sha256(state_limits)? != plan.source_state_sha256
            || current_state != &plan.source_state
        {
            return Err(HyperlinkHwpxError::SourceDrift);
        }
        let built = LinkReferenceBuilder::build(
            &plan.domain_plan,
            current_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let transition = hyperlink_transition(
            current_state,
            &built.state,
            plan.domain_plan.capability_id(),
            state_limits,
            hwpx_limits,
        )?;
        let parsed = parse_hyperlinks(source, current_state, state_limits, hwpx_limits)?;
        let current_digests = parsed
            .projections
            .iter()
            .map(|projection| projection.wrapper_sha256)
            .collect::<Vec<_>>();
        if current_digests != plan.source_hyperlink_wrapper_sha256 {
            return Err(HyperlinkHwpxError::SourceDrift);
        }
        let edit = build_edit(source, &parsed, &transition, state_limits, hwpx_limits)?;
        let output = apply_edit(source, &edit, hwpx_limits)?;
        verify_preservation(source, &output, &edit)?;
        let target =
            HyperlinkHwpxReader::read_section(&output, &built.state, state_limits, hwpx_limits)?;
        let (inserted_hyperlinks, edited_hyperlinks) = match transition {
            HyperlinkTransition::Insert { .. } => (1, 0),
            HyperlinkTransition::Edit { .. } => (0, 1),
        };
        let receipt = HyperlinkHwpxLoweringReceipt {
            profile_id: HYPERLINK_HWPX_PROFILE_ID,
            capability_id: plan.domain_plan.capability_id(),
            source_section_sha256: plan.source_section_sha256,
            output_section_sha256: target.section_sha256,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: built.state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            inserted_hyperlinks,
            edited_hyperlinks,
            source_bytes: source.len(),
            output_bytes: output.len(),
        };
        Ok((output, receipt))
    }

    /// Returns preserving section bytes after the same fail-closed checks.
    ///
    /// # Errors
    ///
    /// Applies the same validation as [`Self::lower_section_with_receipt`].
    pub fn lower_section(
        source: &[u8],
        plan: &HyperlinkHwpxPlan,
        current_state: &LinkReferenceDocumentState,
        current_document_flow_sha256: &str,
        state_limits: LinkReferenceLimits,
        hwpx_limits: HyperlinkHwpxLimits,
    ) -> Result<Vec<u8>, HyperlinkHwpxError> {
        Ok(Self::lower_section_with_receipt(
            source,
            plan,
            current_state,
            current_document_flow_sha256,
            state_limits,
            hwpx_limits,
        )?
        .0)
    }
}

#[derive(Clone)]
enum HyperlinkTransition {
    Insert {
        hyperlink: HyperlinkEntry,
    },
    Edit {
        index: usize,
        before: HyperlinkEntry,
        after: Box<HyperlinkEntry>,
    },
}

fn hyperlink_transition(
    source: &LinkReferenceDocumentState,
    target: &LinkReferenceDocumentState,
    capability_id: &str,
    state_limits: LinkReferenceLimits,
    hwpx_limits: HyperlinkHwpxLimits,
) -> Result<HyperlinkTransition, HyperlinkHwpxError> {
    if non_hyperlink_state(source, state_limits)? != non_hyperlink_state(target, state_limits)? {
        return Err(HyperlinkHwpxError::NonRepresentable);
    }
    let before = source.hyperlinks();
    let after = target.hyperlinks();
    match capability_id {
        "ref.hyperlink_insert" if after.len() == before.len().saturating_add(1) => {
            let mut matched = None;
            for index in 0..after.len() {
                if before[..index] == after[..index]
                    && before[index..] == after[index + 1..]
                    && matched.replace(index).is_some()
                {
                    return Err(HyperlinkHwpxError::NonRepresentable);
                }
            }
            let index = matched.ok_or(HyperlinkHwpxError::NonRepresentable)?;
            ensure_profile(&after[index], state_limits, hwpx_limits)?;
            Ok(HyperlinkTransition::Insert {
                hyperlink: after[index].clone(),
            })
        }
        "ref.hyperlink_edit" if before.len() == after.len() => {
            let changed = before
                .iter()
                .zip(after)
                .enumerate()
                .filter(|(_, (left, right))| left != right)
                .collect::<Vec<_>>();
            if changed.len() != 1 {
                return Err(HyperlinkHwpxError::NonRepresentable);
            }
            let (index, (old, new)) = changed[0];
            ensure_profile(old, state_limits, hwpx_limits)?;
            ensure_profile(new, state_limits, hwpx_limits)?;
            if old.identity != new.identity
                || old.anchor != new.anchor
                || old.display_text_sha256 != new.display_text_sha256
                || old.locked != new.locked
                || old.opaque_native_payload_sha256 != new.opaque_native_payload_sha256
                || old.opaque_properties != new.opaque_properties
            {
                return Err(HyperlinkHwpxError::NonRepresentable);
            }
            let mut native = old.native_pair.clone();
            native
                .parameters_sha256
                .clone_from(&new.native_pair.parameters_sha256);
            if native != new.native_pair || old.target == new.target {
                return Err(HyperlinkHwpxError::NonRepresentable);
            }
            Ok(HyperlinkTransition::Edit {
                index,
                before: old.clone(),
                after: Box::new(new.clone()),
            })
        }
        _ => Err(HyperlinkHwpxError::NonRepresentable),
    }
}

fn non_hyperlink_state(
    state: &LinkReferenceDocumentState,
    limits: LinkReferenceLimits,
) -> Result<serde_json::Value, HyperlinkHwpxError> {
    let mut value: serde_json::Value = serde_json::from_slice(&state.canonical_json(limits)?)
        .map_err(|_| HyperlinkHwpxError::PlanTampered)?;
    value
        .as_object_mut()
        .ok_or(HyperlinkHwpxError::PlanTampered)?
        .remove("hyperlinks")
        .ok_or(HyperlinkHwpxError::PlanTampered)?;
    Ok(value)
}

fn ensure_profile(
    hyperlink: &HyperlinkEntry,
    state_limits: LinkReferenceLimits,
    limits: HyperlinkHwpxLimits,
) -> Result<(), HyperlinkHwpxError> {
    let expected_parameters =
        HyperlinkHwpxReader::parameters_sha256(&hyperlink.target, state_limits, limits)?;
    if hyperlink.native_pair.semantic_binding
        != HyperlinkSemanticBinding::Hangul2020HttpsCurrentTabV1
        || hyperlink.native_pair.field_name_sha256.as_deref() != Some(EMPTY_SHA256)
        || hyperlink.native_pair.editable
        || !hyperlink.native_pair.dirty
        || hyperlink.native_pair.z_order != -1
        || hyperlink.native_pair.parameters_sha256 != expected_parameters
        || hyperlink.native_pair.sub_list_sha256.is_some()
        || hyperlink.native_pair.meta_tag_sha256.is_some()
        || hyperlink.native_pair.opaque_begin_state_sha256 != EMPTY_SHA256
        || hyperlink.native_pair.opaque_end_state_sha256 != EMPTY_SHA256
        || hyperlink.opaque_native_payload_sha256 != EMPTY_SHA256
        || !hyperlink.opaque_properties.is_empty()
        || hyperlink.locked
        || hyperlink.anchor.start.paragraph_ordinal != hyperlink.anchor.end.paragraph_ordinal
        || hyperlink.anchor.start.run_ordinal != hyperlink.anchor.end.run_ordinal
        || hyperlink.anchor.start.inline_ordinal != 0
        || hyperlink.anchor.end.inline_ordinal != 1
    {
        return Err(HyperlinkHwpxError::NonRepresentable);
    }
    Ok(())
}

struct HyperlinkProjection {
    parameters: usize,
    anchor: LinkAnchor,
    uri: String,
    begin_control_id: u32,
    field_id: u32,
    display_text_sha256: String,
    parameters_sha256: String,
    wrapper_sha256: [u8; 32],
}

struct ParsedHyperlinks {
    document: PreservingXmlDocument,
    paragraphs: Vec<usize>,
    projections: Vec<HyperlinkProjection>,
    boundary_runs: BTreeSet<usize>,
}

#[allow(clippy::too_many_lines)] // Complete projection admission remains visible as one audit unit.
fn parse_hyperlinks(
    source: &[u8],
    expected: &LinkReferenceDocumentState,
    state_limits: LinkReferenceLimits,
    limits: HyperlinkHwpxLimits,
) -> Result<ParsedHyperlinks, HyperlinkHwpxError> {
    if source.is_empty()
        || source.len() > limits.0.section_bytes
        || expected.sections().len() != 1
        || expected.hyperlinks().len() > limits.0.hyperlinks
    {
        return Err(HyperlinkHwpxError::InputLimit);
    }
    let _ = expected.canonical_sha256(state_limits)?;
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(HyperlinkHwpxError::InputLimit);
    }
    let root = document.root_element();
    if !is_section_root(element(&document, root)?) {
        return Err(HyperlinkHwpxError::UnsupportedStructure);
    }
    let mut paragraphs = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if has_name(candidate, "p") {
            if paragraphs.len() >= limits.0.paragraphs {
                return Err(HyperlinkHwpxError::InputLimit);
            }
            paragraphs
                .try_reserve(1)
                .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
            paragraphs.push(index);
        }
    }
    if usize::try_from(expected.sections()[0].paragraph_count).ok() != Some(paragraphs.len()) {
        return Err(HyperlinkHwpxError::ProjectionMismatch);
    }

    let mut raw = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if !has_name(candidate, "fieldBegin") {
            continue;
        }
        let Some(field_type) = optional_attribute(candidate, "type")? else {
            continue;
        };
        if decoded_attribute(source, field_type, limits)? != "HYPERLINK" {
            continue;
        }
        if raw.len() >= limits.0.hyperlinks {
            return Err(HyperlinkHwpxError::InputLimit);
        }
        raw.push(parse_projection_structure(
            source,
            &document,
            &paragraphs,
            index,
            limits,
        )?);
    }
    if raw.len() != expected.hyperlinks().len() {
        return Err(HyperlinkHwpxError::ProjectionMismatch);
    }

    let mut boundary_runs = BTreeSet::new();
    let mut display_runs = BTreeSet::new();
    for projection in &raw {
        if !boundary_runs.insert(projection.begin_run)
            || !boundary_runs.insert(projection.end_run)
            || !display_runs.insert(projection.display_run)
            || boundary_runs.contains(&projection.display_run)
        {
            return Err(HyperlinkHwpxError::InvalidHyperlink);
        }
    }
    if display_runs.iter().any(|run| boundary_runs.contains(run)) {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }

    let mut projections = Vec::new();
    projections
        .try_reserve_exact(raw.len())
        .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
    for (raw_projection, expected_link) in raw.into_iter().zip(expected.hyperlinks()) {
        ensure_profile(expected_link, state_limits, limits)?;
        let paragraph_ordinal = paragraphs
            .iter()
            .position(|value| *value == raw_projection.paragraph)
            .ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
        let runs = direct_children_named(
            &document,
            raw_projection.paragraph,
            "run",
            limits.0.runs_per_paragraph,
        )?;
        let normalized = runs
            .iter()
            .filter(|run| !boundary_runs.contains(run))
            .position(|run| *run == raw_projection.display_run)
            .ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
        let anchor = LinkAnchor {
            section_id: expected.sections()[0].section_id.clone(),
            start: LinkPoint {
                paragraph_ordinal: u32::try_from(paragraph_ordinal)
                    .map_err(|_| HyperlinkHwpxError::InputLimit)?,
                run_ordinal: u32::try_from(normalized)
                    .map_err(|_| HyperlinkHwpxError::InputLimit)?,
                inline_ordinal: 0,
            },
            end: LinkPoint {
                paragraph_ordinal: u32::try_from(paragraph_ordinal)
                    .map_err(|_| HyperlinkHwpxError::InputLimit)?,
                run_ordinal: u32::try_from(normalized)
                    .map_err(|_| HyperlinkHwpxError::InputLimit)?,
                inline_ordinal: 1,
            },
        };
        let projection = HyperlinkProjection {
            parameters: raw_projection.parameters,
            anchor,
            uri: raw_projection.uri,
            begin_control_id: raw_projection.begin_control_id,
            field_id: raw_projection.field_id,
            display_text_sha256: raw_projection.display_text_sha256,
            parameters_sha256: raw_projection.parameters_sha256,
            wrapper_sha256: raw_projection.wrapper_sha256,
        };
        if projection.anchor != expected_link.anchor
            || projection.begin_control_id != expected_link.identity.begin_control_id
            || projection.field_id != expected_link.identity.field_id
            || (HyperlinkTarget::Https {
                uri: projection.uri.clone(),
            }) != expected_link.target
            || projection.display_text_sha256 != expected_link.display_text_sha256
            || projection.parameters_sha256 != expected_link.native_pair.parameters_sha256
        {
            return Err(HyperlinkHwpxError::ProjectionMismatch);
        }
        projections.push(projection);
    }
    document.verify_untouched_round_trip()?;
    Ok(ParsedHyperlinks {
        document,
        paragraphs,
        projections,
        boundary_runs,
    })
}

struct RawHyperlinkProjection {
    paragraph: usize,
    begin_run: usize,
    display_run: usize,
    end_run: usize,
    parameters: usize,
    uri: String,
    begin_control_id: u32,
    field_id: u32,
    display_text_sha256: String,
    parameters_sha256: String,
    wrapper_sha256: [u8; 32],
}

#[allow(clippy::too_many_lines)] // Exact native field grammar is easier to audit contiguously.
fn parse_projection_structure(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraphs: &[usize],
    field_begin_index: usize,
    limits: HyperlinkHwpxLimits,
) -> Result<RawHyperlinkProjection, HyperlinkHwpxError> {
    let field_begin = element(document, field_begin_index)?;
    require_container_whitespace(document, field_begin_index)?;
    if field_begin.is_empty()
        || non_namespace_attributes(field_begin)?
            != vec![
                "dirty", "editable", "fieldid", "id", "name", "type", "zorder",
            ]
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let begin_control_id = parse_required_u32(source, field_begin, "id", limits)?;
    let field_id = parse_required_u32(source, field_begin, "fieldid", limits)?;
    if begin_control_id == 0 || field_id == 0 {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    for (name, expected) in [
        ("type", "HYPERLINK"),
        ("name", ""),
        ("editable", "0"),
        ("dirty", "1"),
        ("zorder", "-1"),
    ] {
        if decoded_required_attribute(source, field_begin, name, limits)? != expected {
            return Err(HyperlinkHwpxError::InvalidHyperlink);
        }
    }
    let begin_children = direct_element_children(document, field_begin_index)?;
    if begin_children.len() != 1 || !has_name(element(document, begin_children[0])?, "parameters") {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let parameters = begin_children[0];
    let uri = validate_parameters(source, document, parameters, limits)?;
    let parameters_sha256 = semantic_parameters_sha256(&uri, limits)?;

    let begin_ctrl = field_begin
        .parent()
        .ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
    validate_single_child_container(document, begin_ctrl, "ctrl", field_begin_index)?;
    let begin_run = element(document, begin_ctrl)?
        .parent()
        .ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
    validate_boundary_run(source, document, begin_run, &[begin_ctrl], limits)?;
    let paragraph = element(document, begin_run)?
        .parent()
        .ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
    if !has_name(element(document, paragraph)?, "p") || !paragraphs.contains(&paragraph) {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let display_run = element(document, begin_run)?
        .next_sibling()
        .ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
    let end_run = element(document, display_run)?
        .next_sibling()
        .ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
    if element(document, display_run)?.parent() != Some(paragraph)
        || element(document, end_run)?.parent() != Some(paragraph)
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let display_text_sha256 = validate_display_run(source, document, display_run, limits)?;
    let end_children = direct_element_children(document, end_run)?;
    if end_children.len() != 2
        || !has_name(element(document, end_children[0])?, "ctrl")
        || !has_name(element(document, end_children[1])?, "t")
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    validate_boundary_run(source, document, end_run, &end_children, limits)?;
    let end_ctrl = end_children[0];
    let field_end_children = direct_element_children(document, end_ctrl)?;
    if field_end_children.len() != 1
        || !has_name(element(document, field_end_children[0])?, "fieldEnd")
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    validate_single_child_container(document, end_ctrl, "ctrl", field_end_children[0])?;
    let field_end = element(document, field_end_children[0])?;
    if !field_end.is_empty()
        || field_end.first_child().is_some()
        || non_namespace_attributes(field_end)? != vec!["beginIDRef", "fieldid"]
        || parse_required_u32(source, field_end, "beginIDRef", limits)? != begin_control_id
        || parse_required_u32(source, field_end, "fieldid", limits)? != field_id
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let empty_text = element(document, end_children[1])?;
    if !empty_text.is_empty()
        || empty_text.first_child().is_some()
        || !non_namespace_attributes(empty_text)?.is_empty()
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let begin_span = outer_span(element(document, begin_run)?)?;
    let end_span = outer_span(element(document, end_run)?)?;
    if begin_span.end() > end_span.end() {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(RawHyperlinkProjection {
        paragraph,
        begin_run,
        display_run,
        end_run,
        parameters,
        uri,
        begin_control_id,
        field_id,
        display_text_sha256,
        parameters_sha256,
        wrapper_sha256: digest_bytes(
            source
                .get(begin_span.start()..end_span.end())
                .ok_or(HyperlinkHwpxError::InvalidHyperlink)?,
        ),
    })
}

/// Source-only importer bridge. Reuses the original exact six-parameter
/// profile; it does not grant external approval, open a URL or use caller IR.
pub(crate) fn read_imported_parameter_target(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<HyperlinkTarget, HyperlinkHwpxError> {
    let parameters = element(document, index)?;
    if parameters.name().namespace() != Some(PARAGRAPH_NS)
        || parameters.name().local_name() != "parameters"
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    for child in direct_element_children(document, index)? {
        if element(document, child)?.name().namespace() != Some(PARAGRAPH_NS) {
            return Err(HyperlinkHwpxError::InvalidHyperlink);
        }
    }
    let limits = HyperlinkHwpxLimits::new(HyperlinkHwpxLimitConfig::default())?;
    let uri = document
        .with_source_bytes(|source| validate_parameters(source, document, index, limits))?;
    let target = HyperlinkTarget::Https { uri };
    let _ = target.external_approval_sha256(LinkReferenceLimits::new(
        domain_ir::LinkReferenceLimitConfig::default(),
    )?)?;
    Ok(target)
}

fn validate_parameters(
    source: &[u8],
    document: &PreservingXmlDocument,
    index: usize,
    limits: HyperlinkHwpxLimits,
) -> Result<String, HyperlinkHwpxError> {
    let parameters = element(document, index)?;
    require_container_whitespace(document, index)?;
    if parameters.is_empty()
        || has_namespace_declaration(parameters)
        || non_namespace_attributes(parameters)? != vec!["cnt", "name"]
        || decoded_required_attribute(source, parameters, "cnt", limits)? != "6"
        || !decoded_required_attribute(source, parameters, "name", limits)?.is_empty()
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let children = direct_element_children(document, index)?;
    if children.len() != 6 {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let expected = [
        ("integerParam", "Prop"),
        ("stringParam", "Command"),
        ("stringParam", "Path"),
        ("stringParam", "Category"),
        ("stringParam", "TargetType"),
        ("stringParam", "DocOpenType"),
    ];
    let mut values = Vec::new();
    values
        .try_reserve_exact(children.len())
        .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
    for (child, (tag, name)) in children.iter().zip(expected) {
        let value = element(document, *child)?;
        if !has_name(value, tag)
            || value.first_child().is_some()
            || non_namespace_attributes(value)? != vec!["name"]
            || decoded_required_attribute(source, value, "name", limits)? != name
        {
            return Err(HyperlinkHwpxError::InvalidHyperlink);
        }
        values.push(decoded_text(source, document, *child, limits)?);
    }
    let uri = values[2].clone();
    let command = hyperlink_command(&uri, limits)?;
    if values
        != [
            "0".to_owned(),
            command,
            uri.clone(),
            CATEGORY.to_owned(),
            TARGET_TYPE.to_owned(),
            DOC_OPEN_TYPE.to_owned(),
        ]
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(uri)
}

fn validate_single_child_container(
    document: &PreservingXmlDocument,
    index: usize,
    name: &str,
    child: usize,
) -> Result<(), HyperlinkHwpxError> {
    let value = element(document, index)?;
    require_container_whitespace(document, index)?;
    if !has_name(value, name)
        || !non_namespace_attributes(value)?.is_empty()
        || direct_element_children(document, index)? != vec![child]
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(())
}

fn validate_boundary_run(
    source: &[u8],
    document: &PreservingXmlDocument,
    index: usize,
    expected_children: &[usize],
    limits: HyperlinkHwpxLimits,
) -> Result<(), HyperlinkHwpxError> {
    let run = element(document, index)?;
    require_container_whitespace(document, index)?;
    if !has_name(run, "run")
        || non_namespace_attributes(run)? != vec!["charPrIDRef"]
        || decoded_required_attribute(source, run, "charPrIDRef", limits)? != "0"
        || direct_element_children(document, index)? != expected_children
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(())
}

fn validate_display_run(
    source: &[u8],
    document: &PreservingXmlDocument,
    index: usize,
    limits: HyperlinkHwpxLimits,
) -> Result<String, HyperlinkHwpxError> {
    let run = element(document, index)?;
    require_container_whitespace(document, index)?;
    let attributes = non_namespace_attributes(run)?;
    if !has_name(run, "run")
        || has_namespace_declaration(run)
        || attributes != vec!["charPrIDRef"]
        || parse_required_u32(source, run, "charPrIDRef", limits).is_err()
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let children = direct_element_children(document, index)?;
    if children.len() != 1 || !has_name(element(document, children[0])?, "t") {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let text = element(document, children[0])?;
    if text.first_child().is_some() || !non_namespace_attributes(text)?.is_empty() {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    let decoded = decoded_text(source, document, children[0], limits)?;
    if decoded.is_empty() {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(hex(Sha256::digest(decoded.as_bytes()).into()))
}

struct ByteEdit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}

fn build_edit(
    source: &[u8],
    parsed: &ParsedHyperlinks,
    transition: &HyperlinkTransition,
    state_limits: LinkReferenceLimits,
    limits: HyperlinkHwpxLimits,
) -> Result<ByteEdit, HyperlinkHwpxError> {
    match transition {
        HyperlinkTransition::Insert { hyperlink, .. } => {
            let display_run = run_at_anchor(parsed, &hyperlink.anchor, limits)?;
            if parsed.boundary_runs.contains(&display_run) {
                return Err(HyperlinkHwpxError::NonRepresentable);
            }
            let display_digest =
                validate_display_run(source, &parsed.document, display_run, limits)?;
            if display_digest != hyperlink.display_text_sha256 {
                return Err(HyperlinkHwpxError::ProjectionMismatch);
            }
            ensure_profile(hyperlink, state_limits, limits)?;
            let run = element(&parsed.document, display_run)?;
            let run_span = outer_span(run)?;
            let display_bytes = source
                .get(run_span.start()..run_span.end())
                .ok_or(HyperlinkHwpxError::UnsupportedStructure)?;
            let prefix = element_prefix(source, run, "run")?;
            let HyperlinkTarget::Https { uri } = &hyperlink.target else {
                return Err(HyperlinkHwpxError::NonRepresentable);
            };
            let begin = render_begin(&prefix, hyperlink, uri, limits)?;
            let end = render_end(&prefix, hyperlink);
            let replacement_len = begin
                .len()
                .checked_add(display_bytes.len())
                .and_then(|value| value.checked_add(end.len()))
                .ok_or(HyperlinkHwpxError::OutputLimit)?;
            let mut replacement = Vec::new();
            replacement
                .try_reserve_exact(replacement_len)
                .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
            replacement.extend_from_slice(&begin);
            replacement.extend_from_slice(display_bytes);
            replacement.extend_from_slice(&end);
            Ok(ByteEdit {
                start: run_span.start(),
                end: run_span.end(),
                replacement,
            })
        }
        HyperlinkTransition::Edit {
            index,
            before,
            after,
        } => {
            let projection = parsed
                .projections
                .get(*index)
                .ok_or(HyperlinkHwpxError::ProjectionMismatch)?;
            if projection.anchor != before.anchor
                || before.display_text_sha256 != after.display_text_sha256
            {
                return Err(HyperlinkHwpxError::ProjectionMismatch);
            }
            let parameters = element(&parsed.document, projection.parameters)?;
            let span = outer_span(parameters)?;
            let prefix = element_prefix(source, parameters, "parameters")?;
            let HyperlinkTarget::Https { uri } = &after.target else {
                return Err(HyperlinkHwpxError::NonRepresentable);
            };
            Ok(ByteEdit {
                start: span.start(),
                end: span.end(),
                replacement: render_parameters(&prefix, uri, limits)?.into_bytes(),
            })
        }
    }
}

fn run_at_anchor(
    parsed: &ParsedHyperlinks,
    anchor: &LinkAnchor,
    limits: HyperlinkHwpxLimits,
) -> Result<usize, HyperlinkHwpxError> {
    if anchor.start.paragraph_ordinal != anchor.end.paragraph_ordinal
        || anchor.start.run_ordinal != anchor.end.run_ordinal
        || anchor.start.inline_ordinal != 0
        || anchor.end.inline_ordinal != 1
    {
        return Err(HyperlinkHwpxError::NonRepresentable);
    }
    let paragraph = *parsed
        .paragraphs
        .get(
            usize::try_from(anchor.start.paragraph_ordinal)
                .map_err(|_| HyperlinkHwpxError::NonRepresentable)?,
        )
        .ok_or(HyperlinkHwpxError::NonRepresentable)?;
    let runs = direct_children_named(
        &parsed.document,
        paragraph,
        "run",
        limits.0.runs_per_paragraph,
    )?;
    runs.into_iter()
        .filter(|run| !parsed.boundary_runs.contains(run))
        .nth(
            usize::try_from(anchor.start.run_ordinal)
                .map_err(|_| HyperlinkHwpxError::NonRepresentable)?,
        )
        .ok_or(HyperlinkHwpxError::NonRepresentable)
}

fn render_begin(
    prefix: &str,
    hyperlink: &HyperlinkEntry,
    uri: &str,
    limits: HyperlinkHwpxLimits,
) -> Result<Vec<u8>, HyperlinkHwpxError> {
    let parameters = render_parameters(prefix, uri, limits)?;
    Ok(format!(
        "<{prefix}run charPrIDRef=\"0\"><{prefix}ctrl><{prefix}fieldBegin id=\"{}\" type=\"HYPERLINK\" name=\"\" editable=\"0\" dirty=\"1\" zorder=\"-1\" fieldid=\"{}\">{parameters}</{prefix}fieldBegin></{prefix}ctrl></{prefix}run>",
        hyperlink.identity.begin_control_id, hyperlink.identity.field_id
    )
    .into_bytes())
}

fn render_end(prefix: &str, hyperlink: &HyperlinkEntry) -> Vec<u8> {
    format!(
        "<{prefix}run charPrIDRef=\"0\"><{prefix}ctrl><{prefix}fieldEnd beginIDRef=\"{}\" fieldid=\"{}\"/></{prefix}ctrl><{prefix}t/></{prefix}run>",
        hyperlink.identity.begin_control_id, hyperlink.identity.field_id
    )
    .into_bytes()
}

fn render_parameters(
    prefix: &str,
    uri: &str,
    limits: HyperlinkHwpxLimits,
) -> Result<String, HyperlinkHwpxError> {
    let command = hyperlink_command(uri, limits)?;
    let command = escape_text(&command, limits)?;
    let path = escape_text(uri, limits)?;
    Ok(format!(
        "<{prefix}parameters cnt=\"6\" name=\"\"><{prefix}integerParam name=\"Prop\">0</{prefix}integerParam><{prefix}stringParam name=\"Command\">{command}</{prefix}stringParam><{prefix}stringParam name=\"Path\">{path}</{prefix}stringParam><{prefix}stringParam name=\"Category\">{CATEGORY}</{prefix}stringParam><{prefix}stringParam name=\"TargetType\">{TARGET_TYPE}</{prefix}stringParam><{prefix}stringParam name=\"DocOpenType\">{DOC_OPEN_TYPE}</{prefix}stringParam></{prefix}parameters>"
    ))
}

fn hyperlink_command(uri: &str, limits: HyperlinkHwpxLimits) -> Result<String, HyperlinkHwpxError> {
    let suffix = uri
        .strip_prefix("https://")
        .ok_or(HyperlinkHwpxError::NonRepresentable)?;
    let command = format!("https\\://{suffix};1;0;0;");
    if command.len() > limits.0.text_bytes {
        return Err(HyperlinkHwpxError::OutputLimit);
    }
    Ok(command)
}

fn semantic_parameters_sha256(
    uri: &str,
    limits: HyperlinkHwpxLimits,
) -> Result<String, HyperlinkHwpxError> {
    #[derive(Serialize)]
    struct Parameters<'a> {
        profile_id: &'static str,
        prop: u32,
        command: String,
        path: &'a str,
        category: &'static str,
        target_type: &'static str,
        doc_open_type: &'static str,
    }
    if uri.len() > limits.0.text_bytes {
        return Err(HyperlinkHwpxError::InputLimit);
    }
    let value = Parameters {
        profile_id: HYPERLINK_HWPX_PROFILE_ID,
        prop: 0,
        command: hyperlink_command(uri, limits)?,
        path: uri,
        category: CATEGORY,
        target_type: TARGET_TYPE,
        doc_open_type: DOC_OPEN_TYPE,
    };
    let bytes = serde_json::to_vec(&value).map_err(|_| HyperlinkHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(HyperlinkHwpxError::OutputLimit);
    }
    Ok(hex(Sha256::digest(bytes).into()))
}

fn apply_edit(
    source: &[u8],
    edit: &ByteEdit,
    limits: HyperlinkHwpxLimits,
) -> Result<Vec<u8>, HyperlinkHwpxError> {
    if edit.start > edit.end || edit.end > source.len() {
        return Err(HyperlinkHwpxError::PreservationMismatch);
    }
    let output_len = source
        .len()
        .checked_sub(edit.end - edit.start)
        .and_then(|value| value.checked_add(edit.replacement.len()))
        .ok_or(HyperlinkHwpxError::OutputLimit)?;
    if output_len > limits.0.output_bytes {
        return Err(HyperlinkHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..edit.start]);
    output.extend_from_slice(&edit.replacement);
    output.extend_from_slice(&source[edit.end..]);
    Ok(output)
}

fn verify_preservation(
    source: &[u8],
    output: &[u8],
    edit: &ByteEdit,
) -> Result<(), HyperlinkHwpxError> {
    let suffix_start = edit
        .start
        .checked_add(edit.replacement.len())
        .ok_or(HyperlinkHwpxError::PreservationMismatch)?;
    if output.get(..edit.start) != source.get(..edit.start)
        || output.get(edit.start..suffix_start) != Some(edit.replacement.as_slice())
        || output.get(suffix_start..) != source.get(edit.end..)
    {
        return Err(HyperlinkHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn validate_plan(
    plan: &HyperlinkHwpxPlan,
    state_limits: LinkReferenceLimits,
    limits: HyperlinkHwpxLimits,
) -> Result<(), HyperlinkHwpxError> {
    if plan.schema_version != PLAN_SCHEMA_VERSION
        || plan.profile_id != HYPERLINK_HWPX_PROFILE_ID
        || !matches!(
            plan.domain_plan.capability_id(),
            "ref.hyperlink_insert" | "ref.hyperlink_edit"
        )
        || plan.source_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        || plan.source_state_sha256 != plan.domain_plan.source_state_sha256()
        || plan.source_state.canonical_sha256(state_limits)? != plan.source_state_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(HyperlinkHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &HyperlinkHwpxPlan,
    limits: HyperlinkHwpxLimits,
) -> Result<String, HyperlinkHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: HyperlinkHwpxLimits,
) -> Result<Vec<u8>, HyperlinkHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| HyperlinkHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(HyperlinkHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn direct_element_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, HyperlinkHwpxError> {
    direct_element_children_bounded(document, parent, usize::MAX)
}

fn direct_element_children_bounded(
    document: &PreservingXmlDocument,
    parent: usize,
    maximum: usize,
) -> Result<Vec<usize>, HyperlinkHwpxError> {
    let mut children = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        if children.len() >= maximum {
            return Err(HyperlinkHwpxError::InputLimit);
        }
        children
            .try_reserve(1)
            .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
        children.push(index);
        child = element(document, index)?.next_sibling();
    }
    Ok(children)
}

fn direct_children_named(
    document: &PreservingXmlDocument,
    parent: usize,
    local_name: &str,
    maximum: usize,
) -> Result<Vec<usize>, HyperlinkHwpxError> {
    let mut matches = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        if has_name(element(document, index)?, local_name) {
            if matches.len() >= maximum {
                return Err(HyperlinkHwpxError::InputLimit);
            }
            matches
                .try_reserve(1)
                .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
            matches.push(index);
        }
        child = element(document, index)?.next_sibling();
    }
    Ok(matches)
}

fn require_container_whitespace(
    document: &PreservingXmlDocument,
    element_index: usize,
) -> Result<(), HyperlinkHwpxError> {
    if document.tokens().iter().any(|token| {
        token.element_index() == Some(element_index)
            && matches!(
                token.kind(),
                XmlTokenKind::ByteOrderMark
                    | XmlTokenKind::Declaration
                    | XmlTokenKind::Text
                    | XmlTokenKind::Reference
                    | XmlTokenKind::Comment
            )
    }) {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(())
}

fn require_plain_text_tokens(
    document: &PreservingXmlDocument,
    element_index: usize,
) -> Result<(), HyperlinkHwpxError> {
    if document.tokens().iter().any(|token| {
        token.element_index() == Some(element_index)
            && !matches!(
                token.kind(),
                XmlTokenKind::StartElement
                    | XmlTokenKind::EmptyElement
                    | XmlTokenKind::EndElement
                    | XmlTokenKind::Text
                    | XmlTokenKind::Whitespace
                    | XmlTokenKind::Reference
            )
    }) {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(())
}

fn non_namespace_attributes(element: &XmlElementToken) -> Result<Vec<&str>, HyperlinkHwpxError> {
    let mut names = Vec::new();
    for attribute in element
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
    {
        if attribute.name().namespace().is_some() || names.contains(&attribute.name().local_name())
        {
            return Err(HyperlinkHwpxError::InvalidHyperlink);
        }
        names
            .try_reserve(1)
            .map_err(|_| HyperlinkHwpxError::AllocationFailed)?;
        names.push(attribute.name().local_name());
    }
    names.sort_unstable();
    Ok(names)
}

fn optional_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<Option<&'a XmlAttributeToken>, HyperlinkHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration() && attribute.name().local_name() == name
    });
    let value = matches.next();
    if value.is_some_and(|attribute| attribute.name().namespace().is_some())
        || matches.next().is_some()
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    Ok(value)
}

fn decoded_required_attribute(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    limits: HyperlinkHwpxLimits,
) -> Result<String, HyperlinkHwpxError> {
    let attribute =
        optional_attribute(element, name)?.ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
    decoded_attribute(source, attribute, limits)
}

fn parse_required_u32(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    limits: HyperlinkHwpxLimits,
) -> Result<u32, HyperlinkHwpxError> {
    let value = decoded_required_attribute(source, element, name, limits)?;
    if value.is_empty()
        || (value.len() > 1 && value.starts_with('0'))
        || !value.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(HyperlinkHwpxError::InvalidHyperlink);
    }
    value
        .parse::<u32>()
        .map_err(|_| HyperlinkHwpxError::InvalidHyperlink)
}

fn has_namespace_declaration(element: &XmlElementToken) -> bool {
    element
        .attributes()
        .iter()
        .any(XmlAttributeToken::is_namespace_declaration)
}

fn decoded_attribute(
    source: &[u8],
    attribute: &XmlAttributeToken,
    limits: HyperlinkHwpxLimits,
) -> Result<String, HyperlinkHwpxError> {
    let lexical = std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(HyperlinkHwpxError::InvalidHyperlink)?,
    )
    .map_err(|_| HyperlinkHwpxError::InvalidHyperlink)?;
    if lexical.len() > limits.0.text_bytes {
        return Err(HyperlinkHwpxError::InputLimit);
    }
    let value = unescape(lexical).map_err(|_| HyperlinkHwpxError::InvalidHyperlink)?;
    if value.len() > limits.0.text_bytes || value.chars().any(invalid_xml_character) {
        return Err(HyperlinkHwpxError::InputLimit);
    }
    Ok(value.into_owned())
}

fn decoded_text(
    source: &[u8],
    document: &PreservingXmlDocument,
    index: usize,
    limits: HyperlinkHwpxLimits,
) -> Result<String, HyperlinkHwpxError> {
    let value = element(document, index)?;
    require_plain_text_tokens(document, index)?;
    let span = value
        .content_span()
        .ok_or(HyperlinkHwpxError::InvalidHyperlink)?;
    let lexical = std::str::from_utf8(
        source
            .get(span.start()..span.end())
            .ok_or(HyperlinkHwpxError::InvalidHyperlink)?,
    )
    .map_err(|_| HyperlinkHwpxError::InvalidHyperlink)?;
    if lexical.len() > limits.0.text_bytes {
        return Err(HyperlinkHwpxError::InputLimit);
    }
    let decoded = unescape(lexical).map_err(|_| HyperlinkHwpxError::InvalidHyperlink)?;
    if decoded.len() > limits.0.text_bytes || decoded.chars().any(invalid_xml_character) {
        return Err(HyperlinkHwpxError::InputLimit);
    }
    Ok(decoded.into_owned())
}

fn escape_text(value: &str, limits: HyperlinkHwpxLimits) -> Result<String, HyperlinkHwpxError> {
    if value.len() > limits.0.text_bytes || value.chars().any(invalid_xml_character) {
        return Err(HyperlinkHwpxError::OutputLimit);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;"))
}

const fn invalid_xml_character(value: char) -> bool {
    !matches!(
        value as u32,
        0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF
    )
}

fn element_prefix(
    source: &[u8],
    element: &XmlElementToken,
    expected_local: &str,
) -> Result<String, HyperlinkHwpxError> {
    let name = std::str::from_utf8(
        source
            .get(element.start_name_span().start()..element.start_name_span().end())
            .ok_or(HyperlinkHwpxError::UnsupportedStructure)?,
    )
    .map_err(|_| HyperlinkHwpxError::UnsupportedStructure)?;
    let Some((prefix, local)) = name.rsplit_once(':') else {
        if name != expected_local {
            return Err(HyperlinkHwpxError::UnsupportedStructure);
        }
        return Ok(String::new());
    };
    if local != expected_local
        || prefix.is_empty()
        || !prefix
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
    {
        return Err(HyperlinkHwpxError::UnsupportedStructure);
    }
    Ok(format!("{prefix}:"))
}

fn is_section_root(element: &XmlElementToken) -> bool {
    element.name().local_name() == "sec"
        && matches!(element.name().namespace(), Some(PARAGRAPH_NS | SECTION_NS))
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, HyperlinkHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(HyperlinkHwpxError::UnsupportedStructure)
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, HyperlinkHwpxError> {
    element
        .outer_span()
        .ok_or(HyperlinkHwpxError::UnsupportedStructure)
}

fn digest_bytes(bytes: &[u8]) -> [u8; 32] {
    Sha256::digest(bytes).into()
}

fn hex(bytes: [u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(output, "{byte:02x}");
    }
    output
}

#[cfg(test)]
mod private_tests {
    #![allow(clippy::expect_used, clippy::too_many_lines)]

    use domain_ir::{
        ExternalLinkPolicy, ExternalTargetApproval, HyperlinkFieldType, HyperlinkIdentity,
        HyperlinkNativeBeginTag, HyperlinkNativeEndTag, HyperlinkNativePair,
        LINK_REFERENCE_SCHEMA_VERSION, LinkReferenceDocumentStateDraft, LinkReferenceLimitConfig,
        LinkReferenceOperation, LinkReferenceRequest, LinkReferenceRequestDraft,
        LinkReferenceSectionState, LogicalId,
    };

    use super::*;

    const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

    fn id(value: &str) -> LogicalId {
        LogicalId::parse(value).expect("id")
    }

    #[test]
    fn recomputed_private_plan_tamper_is_rejected() {
        let state_limits =
            LinkReferenceLimits::new(LinkReferenceLimitConfig::default()).expect("limits");
        let hwpx_limits =
            HyperlinkHwpxLimits::new(HyperlinkHwpxLimitConfig::default()).expect("limits");
        let target = HyperlinkTarget::Https {
            uri: "https://example.test/private".to_owned(),
        };
        let approval = ExternalTargetApproval {
            kind: target.external_kind().expect("external"),
            target_sha256: target
                .external_approval_sha256(state_limits)
                .expect("digest"),
        };
        let state = LinkReferenceDocumentState::from_draft(
            LinkReferenceDocumentStateDraft {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
                sections: vec![LinkReferenceSectionState {
                    section_id: id("section"),
                    paragraph_count: 1,
                    run_topology_sha256: A.to_owned(),
                    inline_topology_sha256: A.to_owned(),
                    opaque_section_state_sha256: A.to_owned(),
                    locked: false,
                }],
                bookmarks: Vec::new(),
                hyperlinks: Vec::new(),
                occupied_non_hyperlink_begin_control_ids: Vec::new(),
                occupied_non_hyperlink_field_ids: Vec::new(),
                external_link_policy: ExternalLinkPolicy {
                    allow_https: true,
                    allow_mailto: false,
                    allow_managed_documents: false,
                    approvals: vec![approval],
                    policy_revision_sha256: A.to_owned(),
                },
                non_reference_content_sha256: A.to_owned(),
                unrelated_field_inventory_sha256: A.to_owned(),
                style_catalog_sha256: A.to_owned(),
                object_inventory_sha256: A.to_owned(),
                relationship_inventory_sha256: A.to_owned(),
                resource_inventory_sha256: A.to_owned(),
                document_protection_sha256: A.to_owned(),
                opaque_document_state_sha256: A.to_owned(),
                document_locked: false,
            },
            state_limits,
        )
        .expect("state");
        let display = "private-display";
        let hyperlink = HyperlinkEntry {
            identity: HyperlinkIdentity {
                logical_hyperlink_id: id("link"),
                begin_control_id: 11,
                field_id: 12,
            },
            anchor: LinkAnchor {
                section_id: id("section"),
                start: LinkPoint {
                    paragraph_ordinal: 0,
                    run_ordinal: 0,
                    inline_ordinal: 0,
                },
                end: LinkPoint {
                    paragraph_ordinal: 0,
                    run_ordinal: 0,
                    inline_ordinal: 1,
                },
            },
            target: target.clone(),
            display_text_sha256: hex(Sha256::digest(display.as_bytes()).into()),
            native_pair: HyperlinkNativePair {
                begin_tag: HyperlinkNativeBeginTag::FieldBegin,
                end_tag: HyperlinkNativeEndTag::FieldEnd,
                field_type: HyperlinkFieldType::Hyperlink,
                semantic_binding: HyperlinkSemanticBinding::Hangul2020HttpsCurrentTabV1,
                end_begin_control_id_ref: 11,
                end_field_id: 12,
                field_name_sha256: Some(EMPTY_SHA256.to_owned()),
                editable: false,
                dirty: true,
                z_order: -1,
                parameters_sha256: HyperlinkHwpxReader::parameters_sha256(
                    &target,
                    state_limits,
                    hwpx_limits,
                )
                .expect("parameters"),
                sub_list_sha256: None,
                meta_tag_sha256: None,
                opaque_begin_state_sha256: EMPTY_SHA256.to_owned(),
                opaque_end_state_sha256: EMPTY_SHA256.to_owned(),
            },
            opaque_native_payload_sha256: EMPTY_SHA256.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        };
        let request = LinkReferenceRequest::from_draft(
            LinkReferenceRequestDraft {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
                request_id: id("request"),
                expected_source_state_sha256: state
                    .canonical_sha256(state_limits)
                    .expect("state digest"),
                expected_document_flow_sha256: A.to_owned(),
                target_document_flow_sha256: B.to_owned(),
                operation: LinkReferenceOperation::InsertHyperlink {
                    insertion_index: 0,
                    hyperlink: Box::new(hyperlink),
                },
            },
            &state,
            A,
            state_limits,
        )
        .expect("request");
        let domain = LinkReferenceBuilder::plan(&state, &request, A, state_limits).expect("plan");
        let source = format!(
            "<hp:sec xmlns:hp=\"{PARAGRAPH_NS}\"><hp:p><hp:run charPrIDRef=\"7\"><hp:t>{display}</hp:t></hp:run></hp:p></hp:sec>"
        );
        let mut plan = HyperlinkHwpxBuilder::plan(
            source.as_bytes(),
            &state,
            &domain,
            A,
            state_limits,
            hwpx_limits,
        )
        .expect("adapter plan");
        plan.source_section_sha256[0] ^= 1;
        plan.plan_sha256 = plan_binding_sha256(&plan, hwpx_limits).expect("recomputed seal");
        assert_eq!(
            HyperlinkHwpxLowerer::lower_section(
                source.as_bytes(),
                &plan,
                &state,
                A,
                state_limits,
                hwpx_limits,
            ),
            Err(HyperlinkHwpxError::SourceDrift)
        );
    }
}
