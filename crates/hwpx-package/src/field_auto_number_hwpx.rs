use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    FieldCacheStatus, FieldCachedResult, FieldDefinition, FieldDocumentState, FieldEngineBuilder,
    FieldEngineError, FieldEngineLimits, FieldNumberFormat, FieldPlan, FieldState,
    FieldUpdatePolicy, LogicalId, ObjectNumberKind,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};

pub const FIELD_AUTO_NUMBER_HWPX_PROFILE_ID: &str =
    "hwpx-agent.field-auto-number-hwpx.hwpml-2011-digit/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FieldAutoNumberHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub paragraphs: usize,
    pub runs_per_paragraph: usize,
    pub inline_elements_per_run: usize,
    pub auto_numbers: usize,
    pub plan_bytes: usize,
    pub output_bytes: usize,
}

impl Default for FieldAutoNumberHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            paragraphs: 262_144,
            runs_per_paragraph: 65_536,
            inline_elements_per_run: 262_144,
            auto_numbers: 65_536,
            plan_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct FieldAutoNumberHwpxLimits(FieldAutoNumberHwpxLimitConfig);

impl FieldAutoNumberHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_PLAN_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;

    /// Creates finite limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: FieldAutoNumberHwpxLimitConfig) -> Result<Self, FieldAutoNumberHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.paragraphs == 0
            || config.paragraphs > Self::HARD_MAX_ITEMS
            || config.runs_per_paragraph == 0
            || config.runs_per_paragraph > Self::HARD_MAX_ITEMS
            || config.inline_elements_per_run == 0
            || config.inline_elements_per_run > Self::HARD_MAX_ITEMS
            || config.auto_numbers == 0
            || config.auto_numbers > Self::HARD_MAX_ITEMS
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
        {
            return Err(FieldAutoNumberHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> FieldAutoNumberHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FieldAutoNumberHwpxReadback {
    pub state: FieldDocumentState,
    pub section_sha256: [u8; 32],
    pub auto_number_wrapper_sha256: Vec<[u8; 32]>,
    pub auto_number_count: usize,
}

impl fmt::Debug for FieldAutoNumberHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldAutoNumberHwpxReadback")
            .field("auto_number_count", &self.auto_number_count)
            .field("state", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct FieldAutoNumberHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    source_section_sha256: [u8; 32],
    source_wrapper_sha256: Vec<[u8; 32]>,
    paragraph_ids: Vec<LogicalId>,
    source_state: FieldDocumentState,
    source_state_sha256: String,
    source_document_flow_sha256: String,
    domain_plan: FieldPlan,
    plan_sha256: String,
}

impl FieldAutoNumberHwpxPlan {
    #[must_use]
    pub const fn domain_plan(&self) -> &FieldPlan {
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
    /// Returns serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: FieldAutoNumberHwpxLimits,
    ) -> Result<Vec<u8>, FieldAutoNumberHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for FieldAutoNumberHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldAutoNumberHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.domain_plan.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct FieldAutoNumberHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub inserted_auto_numbers: usize,
    pub updated_auto_numbers: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for FieldAutoNumberHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FieldAutoNumberHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("inserted_auto_numbers", &self.inserted_auto_numbers)
            .field("updated_auto_numbers", &self.updated_auto_numbers)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FieldAutoNumberHwpxError {
    #[error("field auto-number HWPX limits are invalid")]
    InvalidLimit,
    #[error("field auto-number HWPX input exceeds a finite limit")]
    InputLimit,
    #[error("field auto-number HWPX section structure is unsupported")]
    UnsupportedStructure,
    #[error("field auto-number HWPX control is missing, duplicated, or malformed")]
    InvalidAutoNumber,
    #[error("field auto-number HWPX projection differs from the bound typed state")]
    ProjectionMismatch,
    #[error("field operation is not representable by the digit auto-number profile")]
    NonRepresentable,
    #[error("field auto-number HWPX section, state, map, wrapper, or flow drifted")]
    SourceDrift,
    #[error("field auto-number HWPX plan was tampered with")]
    PlanTampered,
    #[error("field auto-number HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("field auto-number HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("field auto-number HWPX allocation failed")]
    AllocationFailed,
    #[error("field domain validation failed")]
    Domain(#[from] FieldEngineError),
    #[error("field auto-number preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl FieldAutoNumberHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "field_auto_number_hwpx_invalid_limit",
            Self::InputLimit => "field_auto_number_hwpx_input_limit",
            Self::UnsupportedStructure => "field_auto_number_hwpx_unsupported_structure",
            Self::InvalidAutoNumber => "field_auto_number_hwpx_invalid_auto_number",
            Self::ProjectionMismatch => "field_auto_number_hwpx_projection_mismatch",
            Self::NonRepresentable => "field_auto_number_hwpx_non_representable",
            Self::SourceDrift => "field_auto_number_hwpx_source_drift",
            Self::PlanTampered => "field_auto_number_hwpx_plan_tampered",
            Self::PreservationMismatch => "field_auto_number_hwpx_preservation_mismatch",
            Self::OutputLimit => "field_auto_number_hwpx_output_limit",
            Self::AllocationFailed => "field_auto_number_hwpx_allocation_failed",
            Self::Domain(_) => "field_auto_number_hwpx_domain",
            Self::Preserving(_) => "field_auto_number_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct FieldAutoNumberHwpxReader;

impl FieldAutoNumberHwpxReader {
    /// Returns paragraph/run start-tag digests for a prospective auto-number anchor.
    ///
    /// # Errors
    ///
    /// Rejects malformed sections and out-of-range paragraph or run ordinals.
    pub fn style_sha256_at(
        source: &[u8],
        paragraph_ordinal: u32,
        run_ordinal: u32,
        limits: FieldAutoNumberHwpxLimits,
    ) -> Result<(String, String), FieldAutoNumberHwpxError> {
        let structure = parse_section_structure(source, limits)?;
        let paragraph = *structure
            .paragraphs
            .get(
                usize::try_from(paragraph_ordinal)
                    .map_err(|_| FieldAutoNumberHwpxError::InputLimit)?,
            )
            .ok_or(FieldAutoNumberHwpxError::NonRepresentable)?;
        let runs = direct_children_named(
            &structure.document,
            paragraph,
            "run",
            limits.0.runs_per_paragraph,
        )?;
        let run = *runs
            .get(usize::try_from(run_ordinal).map_err(|_| FieldAutoNumberHwpxError::InputLimit)?)
            .ok_or(FieldAutoNumberHwpxError::NonRepresentable)?;
        Ok((
            hex(digest_span(
                source,
                element(&structure.document, paragraph)?.start_tag_span(),
            )?),
            hex(digest_span(
                source,
                element(&structure.document, run)?.start_tag_span(),
            )?),
        ))
    }

    /// Verifies every direct digit auto-number projection against a complete typed state.
    ///
    /// `paragraph_ids` is a complete ordered logical-ID map for all top-level section paragraphs.
    /// The domain field-pair IDs remain component reservations and are not interpreted as native
    /// identity because HWPML `autoNum` carries no begin/end IDs.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, stale, non-digit, or over-limit sections and maps.
    pub fn read_section(
        source: &[u8],
        expected: &FieldDocumentState,
        paragraph_ids: &[LogicalId],
        state_limits: FieldEngineLimits,
        hwpx_limits: FieldAutoNumberHwpxLimits,
    ) -> Result<FieldAutoNumberHwpxReadback, FieldAutoNumberHwpxError> {
        let parsed =
            parse_auto_numbers(source, expected, paragraph_ids, state_limits, hwpx_limits)?;
        let mut wrapper_digests = Vec::new();
        wrapper_digests
            .try_reserve_exact(parsed.projections.len())
            .map_err(|_| FieldAutoNumberHwpxError::AllocationFailed)?;
        for projection in &parsed.projections {
            wrapper_digests.push(projection.wrapper_sha256);
        }
        Ok(FieldAutoNumberHwpxReadback {
            state: expected.clone(),
            section_sha256: Sha256::digest(source).into(),
            auto_number_wrapper_sha256: wrapper_digests,
            auto_number_count: parsed.projections.len(),
        })
    }
}

#[derive(Debug)]
pub struct FieldAutoNumberHwpxBuilder;

impl FieldAutoNumberHwpxBuilder {
    /// Binds one exact REF-006, REF-008, or auto-number REF-009 transition to a section.
    ///
    /// # Errors
    ///
    /// Rejects unsupported transitions, source projection, state, flow, map, plan, or limits.
    #[allow(clippy::too_many_arguments)]
    pub fn plan(
        source: &[u8],
        source_state: &FieldDocumentState,
        domain_plan: &FieldPlan,
        current_document_flow_sha256: &str,
        paragraph_ids: &[LogicalId],
        state_limits: FieldEngineLimits,
        hwpx_limits: FieldAutoNumberHwpxLimits,
    ) -> Result<FieldAutoNumberHwpxPlan, FieldAutoNumberHwpxError> {
        if !matches!(
            domain_plan.capability_id(),
            "ref.field_page_number" | "ref.field_object_number" | "ref.field_update"
        ) || domain_plan.source_document_flow_sha256() != current_document_flow_sha256
            || domain_plan.source_state() != source_state
        {
            return Err(FieldAutoNumberHwpxError::NonRepresentable);
        }
        let built = FieldEngineBuilder::build(
            domain_plan,
            source_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let _ = field_transition(
            source_state,
            &built.state,
            domain_plan.capability_id(),
            state_limits,
        )?;
        let readback = FieldAutoNumberHwpxReader::read_section(
            source,
            source_state,
            paragraph_ids,
            state_limits,
            hwpx_limits,
        )?;
        let mut plan = FieldAutoNumberHwpxPlan {
            schema_version: "hwpx-agent.field-auto-number-hwpx-plan/v1",
            profile_id: FIELD_AUTO_NUMBER_HWPX_PROFILE_ID,
            source_section_sha256: readback.section_sha256,
            source_wrapper_sha256: readback.auto_number_wrapper_sha256,
            paragraph_ids: paragraph_ids.to_vec(),
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
pub struct FieldAutoNumberHwpxLowerer;

impl FieldAutoNumberHwpxLowerer {
    /// Applies exactly one native digit auto-number insertion or numeric-cache update.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, state, flow, map, projection, preservation, or limit drift.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_section_with_receipt(
        source: &[u8],
        plan: &FieldAutoNumberHwpxPlan,
        current_state: &FieldDocumentState,
        current_document_flow_sha256: &str,
        paragraph_ids: &[LogicalId],
        state_limits: FieldEngineLimits,
        hwpx_limits: FieldAutoNumberHwpxLimits,
    ) -> Result<(Vec<u8>, FieldAutoNumberHwpxLoweringReceipt), FieldAutoNumberHwpxError> {
        validate_plan(plan, state_limits, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || current_state.canonical_sha256(state_limits)? != plan.source_state_sha256
            || current_state != &plan.source_state
            || paragraph_ids != plan.paragraph_ids
        {
            return Err(FieldAutoNumberHwpxError::SourceDrift);
        }
        let built = FieldEngineBuilder::build(
            &plan.domain_plan,
            current_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let transition = field_transition(
            current_state,
            &built.state,
            plan.domain_plan.capability_id(),
            state_limits,
        )?;
        let parsed = parse_auto_numbers(
            source,
            current_state,
            paragraph_ids,
            state_limits,
            hwpx_limits,
        )?;
        let current_digests: Vec<[u8; 32]> = parsed
            .projections
            .iter()
            .map(|projection| projection.wrapper_sha256)
            .collect();
        if current_digests != plan.source_wrapper_sha256 {
            return Err(FieldAutoNumberHwpxError::SourceDrift);
        }
        let edit = build_edit(source, &parsed, &transition, paragraph_ids, hwpx_limits)?;
        let output = apply_edit(source, &edit, hwpx_limits)?;
        verify_preservation(source, &output, &edit)?;
        let target = FieldAutoNumberHwpxReader::read_section(
            &output,
            &built.state,
            paragraph_ids,
            state_limits,
            hwpx_limits,
        )?;
        let (inserted_auto_numbers, updated_auto_numbers) = match transition {
            FieldTransition::Insert { .. } => (1, 0),
            FieldTransition::Update { .. } => (0, 1),
        };
        let receipt = FieldAutoNumberHwpxLoweringReceipt {
            profile_id: FIELD_AUTO_NUMBER_HWPX_PROFILE_ID,
            capability_id: plan.domain_plan.capability_id(),
            source_section_sha256: plan.source_section_sha256,
            output_section_sha256: target.section_sha256,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: built.state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            inserted_auto_numbers,
            updated_auto_numbers,
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
    #[allow(clippy::too_many_arguments)]
    pub fn lower_section(
        source: &[u8],
        plan: &FieldAutoNumberHwpxPlan,
        current_state: &FieldDocumentState,
        current_document_flow_sha256: &str,
        paragraph_ids: &[LogicalId],
        state_limits: FieldEngineLimits,
        hwpx_limits: FieldAutoNumberHwpxLimits,
    ) -> Result<Vec<u8>, FieldAutoNumberHwpxError> {
        Ok(Self::lower_section_with_receipt(
            source,
            plan,
            current_state,
            current_document_flow_sha256,
            paragraph_ids,
            state_limits,
            hwpx_limits,
        )?
        .0)
    }
}

#[derive(Clone)]
enum FieldTransition {
    Insert { index: usize, field: FieldState },
    Update { index: usize, field: FieldState },
}

fn field_transition(
    source: &FieldDocumentState,
    target: &FieldDocumentState,
    capability_id: &str,
    limits: FieldEngineLimits,
) -> Result<FieldTransition, FieldAutoNumberHwpxError> {
    if non_field_inventory(source, limits)? != non_field_inventory(target, limits)? {
        return Err(FieldAutoNumberHwpxError::NonRepresentable);
    }
    let before = source.fields();
    let after = target.fields();
    match capability_id {
        "ref.field_page_number" | "ref.field_object_number"
            if before.len().checked_add(1) == Some(after.len()) =>
        {
            let mut matched = None;
            for index in 0..after.len() {
                if before[..index] == after[..index]
                    && before[index..] == after[index + 1..]
                    && matched.replace(index).is_some()
                {
                    return Err(FieldAutoNumberHwpxError::NonRepresentable);
                }
            }
            let index = matched.ok_or(FieldAutoNumberHwpxError::NonRepresentable)?;
            ensure_profile_field(&after[index])?;
            if after[index].definition.capability_id() != capability_id {
                return Err(FieldAutoNumberHwpxError::NonRepresentable);
            }
            Ok(FieldTransition::Insert {
                index,
                field: after[index].clone(),
            })
        }
        "ref.field_update" if before.len() == after.len() => {
            let changed: Vec<usize> = before
                .iter()
                .zip(after)
                .enumerate()
                .filter_map(|(index, (left, right))| (left != right).then_some(index))
                .collect();
            if changed.len() != 1 {
                return Err(FieldAutoNumberHwpxError::NonRepresentable);
            }
            let index = changed[0];
            ensure_profile_field(&before[index])?;
            ensure_profile_field(&after[index])?;
            if !same_non_result_field(&before[index], &after[index]) {
                return Err(FieldAutoNumberHwpxError::NonRepresentable);
            }
            Ok(FieldTransition::Update {
                index,
                field: after[index].clone(),
            })
        }
        _ => Err(FieldAutoNumberHwpxError::NonRepresentable),
    }
}

fn non_field_inventory(
    state: &FieldDocumentState,
    limits: FieldEngineLimits,
) -> Result<serde_json::Value, FieldAutoNumberHwpxError> {
    let mut value: serde_json::Value = serde_json::from_slice(&state.canonical_json(limits)?)
        .map_err(|_| FieldAutoNumberHwpxError::PlanTampered)?;
    value
        .as_object_mut()
        .ok_or(FieldAutoNumberHwpxError::PlanTampered)?
        .remove("fields")
        .ok_or(FieldAutoNumberHwpxError::PlanTampered)?;
    Ok(value)
}

fn same_non_result_field(before: &FieldState, after: &FieldState) -> bool {
    before.identity == after.identity
        && before.anchor == after.anchor
        && before.definition == after.definition
        && before.update_policy == after.update_policy
        && before.locked == after.locked
        && before.character_style_sha256 == after.character_style_sha256
        && before.paragraph_style_sha256 == after.paragraph_style_sha256
        && before.field_payload_sha256 == after.field_payload_sha256
        && before.opaque_properties == after.opaque_properties
}

#[derive(Clone, Copy, Eq, PartialEq)]
enum NativeAutoNumberKind {
    Page,
    Picture,
    Table,
    Equation,
}

impl NativeAutoNumberKind {
    const fn lexical(self) -> &'static str {
        match self {
            Self::Page => "PAGE",
            Self::Picture => "PICTURE",
            Self::Table => "TABLE",
            Self::Equation => "EQUATION",
        }
    }

    fn parse(value: &str) -> Result<Self, FieldAutoNumberHwpxError> {
        match value {
            "PAGE" => Ok(Self::Page),
            "PICTURE" => Ok(Self::Picture),
            "TABLE" => Ok(Self::Table),
            "EQUATION" => Ok(Self::Equation),
            _ => Err(FieldAutoNumberHwpxError::InvalidAutoNumber),
        }
    }
}

fn expected_native_kind(
    field: &FieldState,
) -> Result<NativeAutoNumberKind, FieldAutoNumberHwpxError> {
    match &field.definition {
        FieldDefinition::PageNumber {
            format: FieldNumberFormat::Digit,
        } => Ok(NativeAutoNumberKind::Page),
        FieldDefinition::ObjectNumber {
            object_kind,
            format: FieldNumberFormat::Digit,
        } => Ok(match object_kind {
            ObjectNumberKind::Picture => NativeAutoNumberKind::Picture,
            ObjectNumberKind::Table => NativeAutoNumberKind::Table,
            ObjectNumberKind::Equation => NativeAutoNumberKind::Equation,
        }),
        _ => Err(FieldAutoNumberHwpxError::NonRepresentable),
    }
}

fn expected_number(field: &FieldState) -> Result<i64, FieldAutoNumberHwpxError> {
    let FieldCachedResult::Number { value, display } = &field.cached_result else {
        return Err(FieldAutoNumberHwpxError::NonRepresentable);
    };
    if !(0..=i64::from(i32::MAX)).contains(value) || display != &value.to_string() {
        return Err(FieldAutoNumberHwpxError::NonRepresentable);
    }
    Ok(*value)
}

fn ensure_profile_field(field: &FieldState) -> Result<(), FieldAutoNumberHwpxError> {
    let _ = expected_native_kind(field)?;
    let _ = expected_number(field)?;
    if field.locked
        || field.update_policy != FieldUpdatePolicy::RecomputeDirect
        || field.cache_status != FieldCacheStatus::Current
        || field.field_payload_sha256 != EMPTY_SHA256
        || !field.opaque_properties.is_empty()
    {
        return Err(FieldAutoNumberHwpxError::NonRepresentable);
    }
    Ok(())
}

struct AutoNumberProjection {
    wrapper: usize,
    anchor_paragraph_id: LogicalId,
    run_ordinal: u32,
    inline_ordinal: u32,
    kind: NativeAutoNumberKind,
    number: i64,
    number_value_span: XmlByteSpan,
    paragraph_style_sha256: String,
    character_style_sha256: String,
    wrapper_sha256: [u8; 32],
}

struct ParsedAutoNumbers {
    document: PreservingXmlDocument,
    paragraphs: Vec<usize>,
    projections: Vec<AutoNumberProjection>,
}

struct SectionStructure {
    document: PreservingXmlDocument,
    paragraphs: Vec<usize>,
}

fn parse_section_structure(
    source: &[u8],
    limits: FieldAutoNumberHwpxLimits,
) -> Result<SectionStructure, FieldAutoNumberHwpxError> {
    if source.is_empty() || source.len() > limits.0.section_bytes {
        return Err(FieldAutoNumberHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(FieldAutoNumberHwpxError::InputLimit);
    }
    let root = document.root_element();
    if !has_section_name(element(&document, root)?, "sec") {
        return Err(FieldAutoNumberHwpxError::UnsupportedStructure);
    }
    let paragraphs = direct_children_named(&document, root, "p", limits.0.paragraphs)?;
    document.verify_untouched_round_trip()?;
    Ok(SectionStructure {
        document,
        paragraphs,
    })
}

fn parse_auto_numbers(
    source: &[u8],
    expected: &FieldDocumentState,
    paragraph_ids: &[LogicalId],
    state_limits: FieldEngineLimits,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<ParsedAutoNumbers, FieldAutoNumberHwpxError> {
    if expected.fields().len() > limits.0.auto_numbers {
        return Err(FieldAutoNumberHwpxError::InputLimit);
    }
    let _ = expected.canonical_sha256(state_limits)?;
    for field in expected.fields() {
        ensure_profile_field(field)?;
    }
    let structure = parse_section_structure(source, limits)?;
    validate_paragraph_map(paragraph_ids, structure.paragraphs.len(), limits)?;
    let mut projections = Vec::new();
    for (index, candidate) in structure.document.elements().iter().enumerate() {
        if !has_paragraph_name(candidate, "autoNum") {
            continue;
        }
        if projections.len() >= limits.0.auto_numbers {
            return Err(FieldAutoNumberHwpxError::InputLimit);
        }
        projections
            .try_reserve(1)
            .map_err(|_| FieldAutoNumberHwpxError::AllocationFailed)?;
        projections.push(auto_number_projection(
            source,
            &structure.document,
            &structure.paragraphs,
            paragraph_ids,
            index,
            limits,
        )?);
    }
    if projections.len() != expected.fields().len() {
        return Err(FieldAutoNumberHwpxError::ProjectionMismatch);
    }
    for (projection, field) in projections.iter().zip(expected.fields()) {
        if projection.anchor_paragraph_id != field.anchor.paragraph_id
            || projection.run_ordinal != field.anchor.run_ordinal
            || projection.inline_ordinal != field.anchor.inline_ordinal
            || projection.kind != expected_native_kind(field)?
            || projection.number != expected_number(field)?
            || projection.paragraph_style_sha256 != field.paragraph_style_sha256
            || projection.character_style_sha256 != field.character_style_sha256
        {
            return Err(FieldAutoNumberHwpxError::ProjectionMismatch);
        }
    }
    Ok(ParsedAutoNumbers {
        document: structure.document,
        paragraphs: structure.paragraphs,
        projections,
    })
}

fn auto_number_projection(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraphs: &[usize],
    paragraph_ids: &[LogicalId],
    auto_number: usize,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<AutoNumberProjection, FieldAutoNumberHwpxError> {
    let value = element(document, auto_number)?;
    if value.is_empty()
        || non_namespace_attributes(value)? != vec!["num", "numType"]
        || direct_element_children(document, auto_number)?.len() != 1
    {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    let format = direct_element_children(document, auto_number)?[0];
    let format_element = element(document, format)?;
    if !has_paragraph_name(format_element, "autoNumFormat")
        || !format_element.is_empty()
        || format_element.first_child().is_some()
        || non_namespace_attributes(format_element)?
            != vec!["prefixChar", "suffixChar", "supscript", "type", "userChar"]
    {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    require_whitespace_around_child(source, value, format_element)?;
    if decoded_attribute(source, strict_attribute(format_element, "type")?)? != "DIGIT"
        || !decoded_attribute(source, strict_attribute(format_element, "userChar")?)?.is_empty()
        || !decoded_attribute(source, strict_attribute(format_element, "prefixChar")?)?.is_empty()
        || !decoded_attribute(source, strict_attribute(format_element, "suffixChar")?)?.is_empty()
        || decoded_attribute(source, strict_attribute(format_element, "supscript")?)? != "0"
    {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    let number_attribute = strict_attribute(value, "num")?;
    let number_lexical = decoded_attribute(source, number_attribute)?;
    let number = parse_canonical_number(&number_lexical)?;
    let kind = NativeAutoNumberKind::parse(&decoded_attribute(
        source,
        strict_attribute(value, "numType")?,
    )?)?;
    let wrapper = value
        .parent()
        .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    let wrapper_element = element(document, wrapper)?;
    if !has_paragraph_name(wrapper_element, "ctrl")
        || !non_namespace_attributes(wrapper_element)?.is_empty()
        || direct_element_children(document, wrapper)? != vec![auto_number]
    {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    require_whitespace_around_child(source, wrapper_element, value)?;
    let run = wrapper_element
        .parent()
        .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    if !has_paragraph_name(element(document, run)?, "run") {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    let paragraph = element(document, run)?
        .parent()
        .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    if !has_paragraph_name(element(document, paragraph)?, "p") {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    let paragraph_ordinal = paragraphs
        .iter()
        .position(|candidate| *candidate == paragraph)
        .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    let runs = direct_children_named(document, paragraph, "run", limits.0.runs_per_paragraph)?;
    let run_ordinal = runs
        .iter()
        .position(|candidate| *candidate == run)
        .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    let children =
        direct_element_children_bounded(document, run, limits.0.inline_elements_per_run)?;
    let wrapper_position = children
        .iter()
        .position(|candidate| *candidate == wrapper)
        .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    let inline_ordinal = children[..wrapper_position]
        .iter()
        .filter(|&&child| !is_auto_number_wrapper(document, child))
        .count();
    Ok(AutoNumberProjection {
        wrapper,
        anchor_paragraph_id: paragraph_ids[paragraph_ordinal].clone(),
        run_ordinal: u32::try_from(run_ordinal)
            .map_err(|_| FieldAutoNumberHwpxError::InputLimit)?,
        inline_ordinal: u32::try_from(inline_ordinal)
            .map_err(|_| FieldAutoNumberHwpxError::InputLimit)?,
        kind,
        number,
        number_value_span: number_attribute.value_span(),
        paragraph_style_sha256: hex(digest_span(
            source,
            element(document, paragraph)?.start_tag_span(),
        )?),
        character_style_sha256: hex(digest_span(
            source,
            element(document, run)?.start_tag_span(),
        )?),
        wrapper_sha256: digest_span(source, outer_span(wrapper_element)?)?,
    })
}

struct ByteEdit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}

fn build_edit(
    source: &[u8],
    parsed: &ParsedAutoNumbers,
    transition: &FieldTransition,
    paragraph_ids: &[LogicalId],
    limits: FieldAutoNumberHwpxLimits,
) -> Result<ByteEdit, FieldAutoNumberHwpxError> {
    match transition {
        FieldTransition::Update { index, field } => {
            let projection = parsed
                .projections
                .get(*index)
                .ok_or(FieldAutoNumberHwpxError::ProjectionMismatch)?;
            if projection.anchor_paragraph_id != field.anchor.paragraph_id
                || projection.run_ordinal != field.anchor.run_ordinal
                || projection.inline_ordinal != field.anchor.inline_ordinal
                || projection.kind != expected_native_kind(field)?
            {
                return Err(FieldAutoNumberHwpxError::ProjectionMismatch);
            }
            Ok(ByteEdit {
                start: projection.number_value_span.start(),
                end: projection.number_value_span.end(),
                replacement: expected_number(field)?.to_string().into_bytes(),
            })
        }
        FieldTransition::Insert { index, field } => {
            let paragraph_ordinal = paragraph_ids
                .iter()
                .position(|value| *value == field.anchor.paragraph_id)
                .ok_or(FieldAutoNumberHwpxError::NonRepresentable)?;
            let paragraph = *parsed
                .paragraphs
                .get(paragraph_ordinal)
                .ok_or(FieldAutoNumberHwpxError::NonRepresentable)?;
            let runs = direct_children_named(
                &parsed.document,
                paragraph,
                "run",
                limits.0.runs_per_paragraph,
            )?;
            let run = *runs
                .get(
                    usize::try_from(field.anchor.run_ordinal)
                        .map_err(|_| FieldAutoNumberHwpxError::NonRepresentable)?,
                )
                .ok_or(FieldAutoNumberHwpxError::NonRepresentable)?;
            let offset =
                insertion_offset(parsed, run, field.anchor.inline_ordinal, *index, limits)?;
            let prefix = element_prefix(source, element(&parsed.document, run)?)?;
            let kind = expected_native_kind(field)?.lexical();
            let number = expected_number(field)?;
            let replacement = format!(
                "<{prefix}ctrl><{prefix}autoNum num=\"{number}\" numType=\"{kind}\"><{prefix}autoNumFormat type=\"DIGIT\" userChar=\"\" prefixChar=\"\" suffixChar=\"\" supscript=\"0\"/></{prefix}autoNum></{prefix}ctrl>"
            )
            .into_bytes();
            Ok(ByteEdit {
                start: offset,
                end: offset,
                replacement,
            })
        }
    }
}

fn insertion_offset(
    parsed: &ParsedAutoNumbers,
    run: usize,
    inline_ordinal: u32,
    insertion_index: usize,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<usize, FieldAutoNumberHwpxError> {
    let candidate = normalized_insertion_offset(parsed, run, inline_ordinal, limits)?;
    let mut preceding = 0_usize;
    for projection in &parsed.projections {
        if outer_span(element(&parsed.document, projection.wrapper)?)?.start() < candidate {
            preceding = preceding
                .checked_add(1)
                .ok_or(FieldAutoNumberHwpxError::InputLimit)?;
        }
    }
    if preceding != insertion_index {
        return Err(FieldAutoNumberHwpxError::NonRepresentable);
    }
    Ok(candidate)
}

fn normalized_insertion_offset(
    parsed: &ParsedAutoNumbers,
    run: usize,
    inline_ordinal: u32,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<usize, FieldAutoNumberHwpxError> {
    let children =
        direct_element_children_bounded(&parsed.document, run, limits.0.inline_elements_per_run)?;
    let wanted =
        usize::try_from(inline_ordinal).map_err(|_| FieldAutoNumberHwpxError::NonRepresentable)?;
    let mut non_auto_number = 0_usize;
    for child in children {
        if parsed
            .projections
            .iter()
            .any(|projection| projection.wrapper == child)
        {
            continue;
        }
        if is_auto_number_wrapper(&parsed.document, child) {
            return Err(FieldAutoNumberHwpxError::ProjectionMismatch);
        }
        if non_auto_number == wanted {
            return Ok(element(&parsed.document, child)?.start_tag_span().start());
        }
        non_auto_number = non_auto_number
            .checked_add(1)
            .ok_or(FieldAutoNumberHwpxError::InputLimit)?;
    }
    if non_auto_number != wanted {
        return Err(FieldAutoNumberHwpxError::NonRepresentable);
    }
    element(&parsed.document, run)?
        .end_tag_span()
        .map(XmlByteSpan::start)
        .ok_or(FieldAutoNumberHwpxError::UnsupportedStructure)
}

fn apply_edit(
    source: &[u8],
    edit: &ByteEdit,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<Vec<u8>, FieldAutoNumberHwpxError> {
    if edit.start > edit.end || edit.end > source.len() {
        return Err(FieldAutoNumberHwpxError::PreservationMismatch);
    }
    let output_len = source
        .len()
        .checked_sub(edit.end - edit.start)
        .and_then(|value| value.checked_add(edit.replacement.len()))
        .ok_or(FieldAutoNumberHwpxError::OutputLimit)?;
    if output_len > limits.0.output_bytes {
        return Err(FieldAutoNumberHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| FieldAutoNumberHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..edit.start]);
    output.extend_from_slice(&edit.replacement);
    output.extend_from_slice(&source[edit.end..]);
    if output.len() != output_len {
        return Err(FieldAutoNumberHwpxError::OutputLimit);
    }
    Ok(output)
}

fn verify_preservation(
    source: &[u8],
    output: &[u8],
    edit: &ByteEdit,
) -> Result<(), FieldAutoNumberHwpxError> {
    let suffix_start = edit
        .start
        .checked_add(edit.replacement.len())
        .ok_or(FieldAutoNumberHwpxError::PreservationMismatch)?;
    if output.get(..edit.start) != source.get(..edit.start)
        || output.get(edit.start..suffix_start) != Some(edit.replacement.as_slice())
        || output.get(suffix_start..) != source.get(edit.end..)
    {
        return Err(FieldAutoNumberHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn validate_plan(
    plan: &FieldAutoNumberHwpxPlan,
    state_limits: FieldEngineLimits,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<(), FieldAutoNumberHwpxError> {
    if plan.schema_version != "hwpx-agent.field-auto-number-hwpx-plan/v1"
        || plan.profile_id != FIELD_AUTO_NUMBER_HWPX_PROFILE_ID
        || !matches!(
            plan.domain_plan.capability_id(),
            "ref.field_page_number" | "ref.field_object_number" | "ref.field_update"
        )
        || plan.source_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        || plan.source_state.canonical_sha256(state_limits)? != plan.source_state_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(FieldAutoNumberHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &FieldAutoNumberHwpxPlan,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<String, FieldAutoNumberHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<Vec<u8>, FieldAutoNumberHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| FieldAutoNumberHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(FieldAutoNumberHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn validate_paragraph_map(
    paragraph_ids: &[LogicalId],
    expected_len: usize,
    limits: FieldAutoNumberHwpxLimits,
) -> Result<(), FieldAutoNumberHwpxError> {
    if paragraph_ids.len() != expected_len || paragraph_ids.len() > limits.0.paragraphs {
        return Err(FieldAutoNumberHwpxError::ProjectionMismatch);
    }
    let mut unique = BTreeSet::new();
    if paragraph_ids.iter().any(|value| !unique.insert(value)) {
        return Err(FieldAutoNumberHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn parse_canonical_number(value: &str) -> Result<i64, FieldAutoNumberHwpxError> {
    if value.is_empty()
        || (value.len() > 1 && value.starts_with('0'))
        || !value.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    let parsed = value
        .parse::<i64>()
        .map_err(|_| FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    if parsed > i64::from(i32::MAX) {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    Ok(parsed)
}

fn direct_element_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, FieldAutoNumberHwpxError> {
    direct_element_children_bounded(document, parent, usize::MAX)
}

fn direct_element_children_bounded(
    document: &PreservingXmlDocument,
    parent: usize,
    maximum: usize,
) -> Result<Vec<usize>, FieldAutoNumberHwpxError> {
    let mut children = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        if children.len() >= maximum {
            return Err(FieldAutoNumberHwpxError::InputLimit);
        }
        children
            .try_reserve(1)
            .map_err(|_| FieldAutoNumberHwpxError::AllocationFailed)?;
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
) -> Result<Vec<usize>, FieldAutoNumberHwpxError> {
    let mut matches = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        if has_paragraph_name(element(document, index)?, local_name) {
            if matches.len() >= maximum {
                return Err(FieldAutoNumberHwpxError::InputLimit);
            }
            matches
                .try_reserve(1)
                .map_err(|_| FieldAutoNumberHwpxError::AllocationFailed)?;
            matches.push(index);
        }
        child = element(document, index)?.next_sibling();
    }
    Ok(matches)
}

fn is_auto_number_wrapper(document: &PreservingXmlDocument, index: usize) -> bool {
    element(document, index).is_ok_and(|value| has_paragraph_name(value, "ctrl"))
        && direct_element_children(document, index).is_ok_and(|children| {
            children.len() == 1
                && element(document, children[0])
                    .is_ok_and(|value| has_paragraph_name(value, "autoNum"))
        })
}

fn require_whitespace_around_child(
    source: &[u8],
    parent: &XmlElementToken,
    child: &XmlElementToken,
) -> Result<(), FieldAutoNumberHwpxError> {
    let content = parent
        .content_span()
        .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    let child = outer_span(child)?;
    if child.start() < content.start()
        || child.end() > content.end()
        || !source
            .get(content.start()..child.start())
            .is_some_and(|value| value.iter().all(u8::is_ascii_whitespace))
        || !source
            .get(child.end()..content.end())
            .is_some_and(|value| value.iter().all(u8::is_ascii_whitespace))
    {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    Ok(())
}

fn non_namespace_attributes(
    element: &XmlElementToken,
) -> Result<Vec<&str>, FieldAutoNumberHwpxError> {
    let mut names = Vec::new();
    for attribute in element
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
    {
        if attribute.name().namespace().is_some() || names.contains(&attribute.name().local_name())
        {
            return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
        }
        names
            .try_reserve(1)
            .map_err(|_| FieldAutoNumberHwpxError::AllocationFailed)?;
        names.push(attribute.name().local_name());
    }
    names.sort_unstable();
    Ok(names)
}

fn strict_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, FieldAutoNumberHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration() && attribute.name().local_name() == name
    });
    let value = matches
        .next()
        .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    if value.name().namespace().is_some() || matches.next().is_some() {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    Ok(value)
}

fn decoded_attribute(
    source: &[u8],
    attribute: &XmlAttributeToken,
) -> Result<String, FieldAutoNumberHwpxError> {
    let lexical = std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(FieldAutoNumberHwpxError::InvalidAutoNumber)?,
    )
    .map_err(|_| FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    if lexical.len() > 1024 {
        return Err(FieldAutoNumberHwpxError::InputLimit);
    }
    let value = unescape(lexical).map_err(|_| FieldAutoNumberHwpxError::InvalidAutoNumber)?;
    if value.as_ref() != lexical {
        return Err(FieldAutoNumberHwpxError::InvalidAutoNumber);
    }
    if value.len() > 1024 || value.chars().any(invalid_xml_character) {
        return Err(FieldAutoNumberHwpxError::InputLimit);
    }
    Ok(value.into_owned())
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
) -> Result<String, FieldAutoNumberHwpxError> {
    let name = std::str::from_utf8(
        source
            .get(element.start_name_span().start()..element.start_name_span().end())
            .ok_or(FieldAutoNumberHwpxError::UnsupportedStructure)?,
    )
    .map_err(|_| FieldAutoNumberHwpxError::UnsupportedStructure)?;
    let Some((prefix, local)) = name.rsplit_once(':') else {
        if name != "run" {
            return Err(FieldAutoNumberHwpxError::UnsupportedStructure);
        }
        return Ok(String::new());
    };
    if local != "run"
        || prefix.is_empty()
        || !prefix
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
    {
        return Err(FieldAutoNumberHwpxError::UnsupportedStructure);
    }
    Ok(format!("{prefix}:"))
}

fn has_paragraph_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn has_section_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(SECTION_NS) && element.name().local_name() == local_name
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, FieldAutoNumberHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(FieldAutoNumberHwpxError::UnsupportedStructure)
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, FieldAutoNumberHwpxError> {
    element
        .outer_span()
        .ok_or(FieldAutoNumberHwpxError::UnsupportedStructure)
}

fn digest_span(source: &[u8], span: XmlByteSpan) -> Result<[u8; 32], FieldAutoNumberHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(FieldAutoNumberHwpxError::UnsupportedStructure)?,
    )
    .into())
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
    #![allow(clippy::expect_used)]

    use super::*;
    use domain_ir::{
        FIELD_ENGINE_SCHEMA_VERSION, FieldAnchor, FieldDocumentStateDraft, FieldEngineLimitConfig,
        FieldIdentity, FieldOperation, FieldRequest, FieldRequestDraft,
    };

    const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

    fn logical_id(value: &str) -> LogicalId {
        LogicalId::parse(value).expect("logical id")
    }

    #[test]
    fn sealed_plan_tampering_is_rejected() {
        let source = br#"<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p><hp:run><hp:t>A</hp:t></hp:run></hp:p></hs:sec>"#;
        let state_limits =
            FieldEngineLimits::new(FieldEngineLimitConfig::default()).expect("state limits");
        let hwpx_limits = FieldAutoNumberHwpxLimits::new(FieldAutoNumberHwpxLimitConfig::default())
            .expect("hwpx limits");
        let (paragraph_style, character_style) =
            FieldAutoNumberHwpxReader::style_sha256_at(source, 0, 0, hwpx_limits)
                .expect("style digests");
        let state = FieldDocumentState::from_draft(
            FieldDocumentStateDraft {
                schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
                fields: Vec::new(),
                non_field_content_sha256: A.to_owned(),
                style_catalog_sha256: B.to_owned(),
                reference_inventory_sha256: A.to_owned(),
                resource_inventory_sha256: B.to_owned(),
                opaque_document_state_sha256: A.to_owned(),
            },
            state_limits,
        )
        .expect("state");
        let field = FieldState {
            identity: FieldIdentity {
                logical_field_id: logical_id("field-1"),
                native_begin_id: 1,
                native_end_id: 2,
            },
            anchor: FieldAnchor {
                paragraph_id: logical_id("paragraph-1"),
                run_ordinal: 0,
                inline_ordinal: 0,
            },
            definition: FieldDefinition::PageNumber {
                format: FieldNumberFormat::Digit,
            },
            cached_result: FieldCachedResult::Number {
                value: 1,
                display: "1".to_owned(),
            },
            update_policy: FieldUpdatePolicy::RecomputeDirect,
            cache_status: FieldCacheStatus::Current,
            locked: false,
            evaluation_context_sha256: None,
            character_style_sha256: character_style,
            paragraph_style_sha256: paragraph_style,
            field_payload_sha256: EMPTY_SHA256.to_owned(),
            opaque_properties: Vec::new(),
        };
        let request = FieldRequest::from_draft(
            FieldRequestDraft {
                schema_version: FIELD_ENGINE_SCHEMA_VERSION.to_owned(),
                request_id: logical_id("request-1"),
                expected_source_state_sha256: state
                    .canonical_sha256(state_limits)
                    .expect("state digest"),
                expected_document_flow_sha256: A.to_owned(),
                target_document_flow_sha256: B.to_owned(),
                operation: FieldOperation::Insert {
                    insertion_index: 0,
                    field,
                },
            },
            &state,
            A,
            state_limits,
        )
        .expect("request");
        let domain =
            FieldEngineBuilder::plan(&state, &request, A, state_limits).expect("domain plan");
        let mut plan = FieldAutoNumberHwpxBuilder::plan(
            source,
            &state,
            &domain,
            A,
            &[logical_id("paragraph-1")],
            state_limits,
            hwpx_limits,
        )
        .expect("adapter plan");
        plan.profile_id = "tampered";
        assert_eq!(
            FieldAutoNumberHwpxLowerer::lower_section(
                source,
                &plan,
                &state,
                A,
                &[logical_id("paragraph-1")],
                state_limits,
                hwpx_limits,
            ),
            Err(FieldAutoNumberHwpxError::PlanTampered)
        );
    }
}
