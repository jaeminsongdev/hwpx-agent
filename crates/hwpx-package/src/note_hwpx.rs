use std::collections::BTreeSet;
use std::fmt;

use domain_ir::{
    LogicalId, NoteBuilder, NoteDocumentState, NoteEntry, NoteError, NoteKind, NoteLimits,
    NoteNativeTag, NotePlan,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlTokenKind,
};

pub const NOTE_HWPX_PROFILE_ID: &str = "hwpx-agent.note-hwpx.hwpml-2011-inline-note-payload/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NoteHwpxLimitConfig {
    pub section_bytes: usize,
    pub payload_bytes: usize,
    pub elements: usize,
    pub paragraphs: usize,
    pub runs_per_paragraph: usize,
    pub inline_elements_per_run: usize,
    pub notes: usize,
    pub text_bytes: usize,
    pub plan_bytes: usize,
    pub output_bytes: usize,
}

impl Default for NoteHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            payload_bytes: 8 * 1024 * 1024,
            elements: 1_000_000,
            paragraphs: 262_144,
            runs_per_paragraph: 65_536,
            inline_elements_per_run: 262_144,
            notes: 65_536,
            text_bytes: 8 * 1024 * 1024,
            plan_bytes: 32 * 1024 * 1024,
            output_bytes: 40 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NoteHwpxLimits(NoteHwpxLimitConfig);

impl NoteHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_PAYLOAD_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_PLAN_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 160 * 1024 * 1024;

    /// Creates finite limits without silently clamping caller values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: NoteHwpxLimitConfig) -> Result<Self, NoteHwpxError> {
        if config.section_bytes == 0
            || config.section_bytes > Self::HARD_MAX_SECTION_BYTES
            || config.payload_bytes == 0
            || config.payload_bytes > Self::HARD_MAX_PAYLOAD_BYTES
            || config.elements == 0
            || config.elements > Self::HARD_MAX_ELEMENTS
            || config.paragraphs == 0
            || config.paragraphs > Self::HARD_MAX_ITEMS
            || config.runs_per_paragraph == 0
            || config.runs_per_paragraph > Self::HARD_MAX_ITEMS
            || config.inline_elements_per_run == 0
            || config.inline_elements_per_run > Self::HARD_MAX_ITEMS
            || config.notes == 0
            || config.notes > Self::HARD_MAX_ITEMS
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
            || config.payload_bytes > config.output_bytes
        {
            return Err(NoteHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> NoteHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct NoteHwpxPayloadDigests {
    pub body_graph_sha256: String,
    pub plain_text_sha256: Option<String>,
    pub body_style_sha256: String,
}

impl fmt::Debug for NoteHwpxPayloadDigests {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteHwpxPayloadDigests")
            .field("plain_text_available", &self.plain_text_sha256.is_some())
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct NoteHwpxReadback {
    pub state: NoteDocumentState,
    pub section_sha256: [u8; 32],
    pub note_wrapper_sha256: Vec<[u8; 32]>,
    pub note_count: usize,
}

impl fmt::Debug for NoteHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteHwpxReadback")
            .field("note_count", &self.note_count)
            .field("state", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct NoteHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    source_section_sha256: [u8; 32],
    source_note_wrapper_sha256: Vec<[u8; 32]>,
    paragraph_ids: Vec<LogicalId>,
    insert_payload_sha256: [u8; 32],
    insert_payload_bytes: usize,
    source_state: NoteDocumentState,
    source_state_sha256: String,
    source_document_flow_sha256: String,
    domain_plan: NotePlan,
    plan_sha256: String,
}

impl NoteHwpxPlan {
    #[must_use]
    pub const fn domain_plan(&self) -> &NotePlan {
        &self.domain_plan
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Returns deterministic bounded JSON without embedding raw note body XML.
    ///
    /// # Errors
    ///
    /// Returns serialization or output-limit failure.
    pub fn canonical_json(&self, limits: NoteHwpxLimits) -> Result<Vec<u8>, NoteHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for NoteHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.domain_plan.capability_id())
            .field("payload_bytes", &self.insert_payload_bytes)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct NoteHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub inserted_notes: usize,
    pub source_bytes: usize,
    pub payload_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for NoteHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("inserted_notes", &self.inserted_notes)
            .field("source_bytes", &self.source_bytes)
            .field("payload_bytes", &self.payload_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum NoteHwpxError {
    #[error("note HWPX limits are invalid")]
    InvalidLimit,
    #[error("note HWPX input exceeds a finite limit")]
    InputLimit,
    #[error("note HWPX section structure is unsupported")]
    UnsupportedStructure,
    #[error("note HWPX native note is missing, duplicated, or malformed")]
    InvalidNote,
    #[error("note HWPX payload is malformed or not self-contained")]
    InvalidPayload,
    #[error("note HWPX projection differs from the bound typed state")]
    ProjectionMismatch,
    #[error("note operation is not representable by the inline-note profile")]
    NonRepresentable,
    #[error("note HWPX section, state, note, payload, anchor map, or flow drifted")]
    SourceDrift,
    #[error("note HWPX plan was tampered with")]
    PlanTampered,
    #[error("note HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("note HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("note HWPX allocation failed")]
    AllocationFailed,
    #[error("note domain validation failed")]
    Domain(#[from] NoteError),
    #[error("note preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl NoteHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "note_hwpx_invalid_limit",
            Self::InputLimit => "note_hwpx_input_limit",
            Self::UnsupportedStructure => "note_hwpx_unsupported_structure",
            Self::InvalidNote => "note_hwpx_invalid_note",
            Self::InvalidPayload => "note_hwpx_invalid_payload",
            Self::ProjectionMismatch => "note_hwpx_projection_mismatch",
            Self::NonRepresentable => "note_hwpx_non_representable",
            Self::SourceDrift => "note_hwpx_source_drift",
            Self::PlanTampered => "note_hwpx_plan_tampered",
            Self::PreservationMismatch => "note_hwpx_preservation_mismatch",
            Self::OutputLimit => "note_hwpx_output_limit",
            Self::AllocationFailed => "note_hwpx_allocation_failed",
            Self::Domain(_) => "note_hwpx_domain",
            Self::Preserving(_) => "note_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct NoteHwpxReader;

impl NoteHwpxReader {
    /// Inspects an exact, self-contained `subList` payload without exposing its text in Debug.
    ///
    /// # Errors
    ///
    /// Rejects malformed, empty-body, foreign-root, or over-limit payloads.
    pub fn inspect_payload(
        payload: &[u8],
        limits: NoteHwpxLimits,
    ) -> Result<NoteHwpxPayloadDigests, NoteHwpxError> {
        Ok(parse_payload(payload, limits)?.digests)
    }

    /// Returns the exact enclosing-run start-tag digest for a prospective note marker.
    ///
    /// # Errors
    ///
    /// Rejects malformed sections or an out-of-range paragraph/run anchor.
    pub fn marker_style_sha256_at(
        source: &[u8],
        paragraph_ordinal: u32,
        run_ordinal: u32,
        limits: NoteHwpxLimits,
    ) -> Result<String, NoteHwpxError> {
        let structure = parse_section_structure(source, limits)?;
        let run = run_at(
            &structure.document,
            &structure.paragraphs,
            paragraph_ordinal,
            run_ordinal,
            limits,
        )?;
        Ok(hex(digest_span(
            source,
            element(&structure.document, run)?.start_tag_span(),
        )?))
    }

    /// Verifies the complete inline footnote/endnote projection against one typed state.
    ///
    /// `paragraph_ids` is a complete ordered logical-ID map for all top-level section paragraphs.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, stale, non-inline, or over-limit sections and maps.
    pub fn read_section(
        source: &[u8],
        expected: &NoteDocumentState,
        paragraph_ids: &[LogicalId],
        state_limits: NoteLimits,
        hwpx_limits: NoteHwpxLimits,
    ) -> Result<NoteHwpxReadback, NoteHwpxError> {
        let parsed = parse_notes(source, expected, paragraph_ids, state_limits, hwpx_limits)?;
        let mut wrapper_digests = Vec::new();
        wrapper_digests
            .try_reserve_exact(parsed.projections.len())
            .map_err(|_| NoteHwpxError::AllocationFailed)?;
        for projection in &parsed.projections {
            wrapper_digests.push(projection.wrapper_sha256);
        }
        Ok(NoteHwpxReadback {
            state: expected.clone(),
            section_sha256: Sha256::digest(source).into(),
            note_wrapper_sha256: wrapper_digests,
            note_count: parsed.projections.len(),
        })
    }
}

#[derive(Debug)]
pub struct NoteHwpxBuilder;

impl NoteHwpxBuilder {
    /// Binds one exact REF-021 or REF-022 insertion to section, state, flow, anchor map and body.
    ///
    /// # Errors
    ///
    /// Rejects unsupported transitions, source projection, payload, state, flow, plan, or limits.
    #[allow(clippy::too_many_arguments)]
    pub fn plan(
        source: &[u8],
        source_state: &NoteDocumentState,
        domain_plan: &NotePlan,
        current_document_flow_sha256: &str,
        paragraph_ids: &[LogicalId],
        insert_payload: &[u8],
        state_limits: NoteLimits,
        hwpx_limits: NoteHwpxLimits,
    ) -> Result<NoteHwpxPlan, NoteHwpxError> {
        if !matches!(
            domain_plan.capability_id(),
            "ref.footnote_insert" | "ref.endnote_insert"
        ) || domain_plan.source_document_flow_sha256() != current_document_flow_sha256
            || domain_plan.source_state() != source_state
        {
            return Err(NoteHwpxError::NonRepresentable);
        }
        let built = NoteBuilder::build(
            domain_plan,
            source_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let transition = note_transition(source_state, &built.state, state_limits)?;
        let readback = NoteHwpxReader::read_section(
            source,
            source_state,
            paragraph_ids,
            state_limits,
            hwpx_limits,
        )?;
        let payload = parse_payload(insert_payload, hwpx_limits)?;
        validate_inserted_note(
            source,
            &readback,
            paragraph_ids,
            &transition.note,
            &payload,
            hwpx_limits,
        )?;
        let mut plan = NoteHwpxPlan {
            schema_version: "hwpx-agent.note-hwpx-plan/v1",
            profile_id: NOTE_HWPX_PROFILE_ID,
            source_section_sha256: readback.section_sha256,
            source_note_wrapper_sha256: readback.note_wrapper_sha256,
            paragraph_ids: paragraph_ids.to_vec(),
            insert_payload_sha256: Sha256::digest(insert_payload).into(),
            insert_payload_bytes: insert_payload.len(),
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
pub struct NoteHwpxLowerer;

impl NoteHwpxLowerer {
    /// Applies exactly one native inline footnote/endnote insertion.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, state, flow, map, payload, preservation, or limit drift.
    #[allow(clippy::too_many_arguments)]
    pub fn lower_section_with_receipt(
        source: &[u8],
        insert_payload: &[u8],
        plan: &NoteHwpxPlan,
        current_state: &NoteDocumentState,
        current_document_flow_sha256: &str,
        state_limits: NoteLimits,
        hwpx_limits: NoteHwpxLimits,
    ) -> Result<(Vec<u8>, NoteHwpxLoweringReceipt), NoteHwpxError> {
        validate_plan(plan, state_limits, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || Sha256::digest(insert_payload).as_slice() != plan.insert_payload_sha256
            || insert_payload.len() != plan.insert_payload_bytes
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || current_state.canonical_sha256(state_limits)? != plan.source_state_sha256
            || current_state != &plan.source_state
        {
            return Err(NoteHwpxError::SourceDrift);
        }
        let built = NoteBuilder::build(
            &plan.domain_plan,
            current_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let transition = note_transition(current_state, &built.state, state_limits)?;
        let parsed = parse_notes(
            source,
            current_state,
            &plan.paragraph_ids,
            state_limits,
            hwpx_limits,
        )?;
        let current_digests = parsed
            .projections
            .iter()
            .map(|projection| projection.wrapper_sha256)
            .collect::<Vec<_>>();
        if current_digests != plan.source_note_wrapper_sha256 {
            return Err(NoteHwpxError::SourceDrift);
        }
        let payload = parse_payload(insert_payload, hwpx_limits)?;
        validate_inserted_note(
            source,
            &NoteHwpxReadback {
                state: current_state.clone(),
                section_sha256: plan.source_section_sha256,
                note_wrapper_sha256: current_digests,
                note_count: parsed.projections.len(),
            },
            &plan.paragraph_ids,
            &transition.note,
            &payload,
            hwpx_limits,
        )?;
        let edit = build_edit(
            source,
            &parsed,
            &transition,
            &plan.paragraph_ids,
            insert_payload,
            hwpx_limits,
        )?;
        let output = apply_edit(source, &edit, hwpx_limits)?;
        verify_preservation(source, &output, &edit)?;
        let target = NoteHwpxReader::read_section(
            &output,
            &built.state,
            &plan.paragraph_ids,
            state_limits,
            hwpx_limits,
        )?;
        let receipt = NoteHwpxLoweringReceipt {
            profile_id: NOTE_HWPX_PROFILE_ID,
            capability_id: plan.domain_plan.capability_id(),
            source_section_sha256: plan.source_section_sha256,
            output_section_sha256: target.section_sha256,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: built.state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            inserted_notes: 1,
            source_bytes: source.len(),
            payload_bytes: insert_payload.len(),
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
        insert_payload: &[u8],
        plan: &NoteHwpxPlan,
        current_state: &NoteDocumentState,
        current_document_flow_sha256: &str,
        state_limits: NoteLimits,
        hwpx_limits: NoteHwpxLimits,
    ) -> Result<Vec<u8>, NoteHwpxError> {
        Ok(Self::lower_section_with_receipt(
            source,
            insert_payload,
            plan,
            current_state,
            current_document_flow_sha256,
            state_limits,
            hwpx_limits,
        )?
        .0)
    }
}

struct NoteTransition {
    index: usize,
    note: NoteEntry,
}

fn note_transition(
    source: &NoteDocumentState,
    target: &NoteDocumentState,
    limits: NoteLimits,
) -> Result<NoteTransition, NoteHwpxError> {
    if non_note_state(source, limits)? != non_note_state(target, limits)?
        || target.notes().len() != source.notes().len().saturating_add(1)
    {
        return Err(NoteHwpxError::NonRepresentable);
    }
    let mut matched = None;
    for index in 0..target.notes().len() {
        if source.notes()[..index] == target.notes()[..index]
            && source.notes()[index..] == target.notes()[index + 1..]
            && matched.replace(index).is_some()
        {
            return Err(NoteHwpxError::NonRepresentable);
        }
    }
    let index = matched.ok_or(NoteHwpxError::NonRepresentable)?;
    let note = target.notes()[index].clone();
    if !matches!(note.kind, NoteKind::Footnote | NoteKind::Endnote)
        || note.native_tag != native_tag_for(note.kind)
    {
        return Err(NoteHwpxError::NonRepresentable);
    }
    Ok(NoteTransition { index, note })
}

fn non_note_state(
    state: &NoteDocumentState,
    limits: NoteLimits,
) -> Result<serde_json::Value, NoteHwpxError> {
    let mut value: serde_json::Value = serde_json::from_slice(&state.canonical_json(limits)?)
        .map_err(|_| NoteHwpxError::PlanTampered)?;
    value
        .as_object_mut()
        .ok_or(NoteHwpxError::PlanTampered)?
        .remove("notes")
        .ok_or(NoteHwpxError::PlanTampered)?;
    Ok(value)
}

struct NoteProjection {
    wrapper: usize,
    anchor_paragraph_ordinal: u32,
    anchor_run_ordinal: u32,
    anchor_inline_ordinal: u32,
    native_instance_id: u32,
    kind: NoteKind,
    flags: u32,
    number: u16,
    user_character: Option<String>,
    prefix_character: Option<String>,
    suffix_character: Option<String>,
    marker_style_sha256: String,
    payload_digests: NoteHwpxPayloadDigests,
    wrapper_sha256: [u8; 32],
}

struct SectionStructure {
    document: PreservingXmlDocument,
    paragraphs: Vec<usize>,
}

struct ParsedNotes {
    document: PreservingXmlDocument,
    paragraphs: Vec<usize>,
    projections: Vec<NoteProjection>,
}

fn parse_section_structure(
    source: &[u8],
    limits: NoteHwpxLimits,
) -> Result<SectionStructure, NoteHwpxError> {
    if source.is_empty() || source.len() > limits.0.section_bytes {
        return Err(NoteHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(NoteHwpxError::InputLimit);
    }
    let mut roots = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, candidate)| candidate.parent().is_none())
        .map(|(index, _)| index);
    let root = roots.next().ok_or(NoteHwpxError::UnsupportedStructure)?;
    if roots.next().is_some() || !is_section_root(element(&document, root)?) {
        return Err(NoteHwpxError::UnsupportedStructure);
    }
    let paragraphs = direct_children_named(&document, root, "p", limits.0.paragraphs)?;
    if paragraphs.is_empty() {
        return Err(NoteHwpxError::UnsupportedStructure);
    }
    document.verify_untouched_round_trip()?;
    Ok(SectionStructure {
        document,
        paragraphs,
    })
}

fn parse_notes(
    source: &[u8],
    expected: &NoteDocumentState,
    paragraph_ids: &[LogicalId],
    state_limits: NoteLimits,
    limits: NoteHwpxLimits,
) -> Result<ParsedNotes, NoteHwpxError> {
    if expected.sections().len() != 1 || expected.notes().len() > limits.0.notes {
        return Err(NoteHwpxError::InputLimit);
    }
    let _ = expected.canonical_sha256(state_limits)?;
    let structure = parse_section_structure(source, limits)?;
    validate_paragraph_map(paragraph_ids, structure.paragraphs.len(), limits)?;
    let mut projections = Vec::new();
    for (index, candidate) in structure.document.elements().iter().enumerate() {
        if candidate.name().local_name() != "footNote" && candidate.name().local_name() != "endNote"
        {
            continue;
        }
        if !has_name(candidate, candidate.name().local_name()) {
            return Err(NoteHwpxError::InvalidNote);
        }
        if projections.len() >= limits.0.notes {
            return Err(NoteHwpxError::InputLimit);
        }
        projections
            .try_reserve(1)
            .map_err(|_| NoteHwpxError::AllocationFailed)?;
        projections.push(note_projection(
            source,
            &structure.document,
            &structure.paragraphs,
            index,
            limits,
        )?);
    }
    if projections.len() != expected.notes().len() {
        return Err(NoteHwpxError::ProjectionMismatch);
    }
    for (projection, note) in projections.iter().zip(expected.notes()) {
        ensure_closed_note(note)?;
        let paragraph_index = usize::try_from(projection.anchor_paragraph_ordinal)
            .map_err(|_| NoteHwpxError::ProjectionMismatch)?;
        if note.anchor.section_id != expected.sections()[0].section_id
            || paragraph_ids.get(paragraph_index) != Some(&note.anchor.paragraph_id)
            || note.anchor.run_ordinal != projection.anchor_run_ordinal
            || note.anchor.inline_ordinal != projection.anchor_inline_ordinal
            || note.identity.native_instance_id != projection.native_instance_id
            || note.kind != projection.kind
            || note.native_tag != native_tag_for(projection.kind)
            || note.marker.flags != projection.flags
            || note.marker.number != projection.number
            || note.marker.user_character != projection.user_character
            || note.marker.prefix_character != projection.prefix_character
            || note.marker.suffix_character != projection.suffix_character
            || note.marker_style_sha256 != projection.marker_style_sha256
            || note.body_graph_sha256 != projection.payload_digests.body_graph_sha256
            || note.plain_text_sha256 != projection.payload_digests.plain_text_sha256
            || note.body_style_sha256 != projection.payload_digests.body_style_sha256
        {
            return Err(NoteHwpxError::ProjectionMismatch);
        }
    }
    Ok(ParsedNotes {
        document: structure.document,
        paragraphs: structure.paragraphs,
        projections,
    })
}

fn note_projection(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraphs: &[usize],
    note_index: usize,
    limits: NoteHwpxLimits,
) -> Result<NoteProjection, NoteHwpxError> {
    let note = element(document, note_index)?;
    let kind = match note.name().local_name() {
        "footNote" => NoteKind::Footnote,
        "endNote" => NoteKind::Endnote,
        _ => return Err(NoteHwpxError::InvalidNote),
    };
    let attributes = non_namespace_attributes(note)?;
    if !attributes.iter().all(|name| {
        matches!(
            *name,
            "flag" | "number" | "userChar" | "prefixChar" | "suffixChar" | "instId"
        )
    }) || !attributes.contains(&"instId")
    {
        return Err(NoteHwpxError::InvalidNote);
    }
    let children = direct_element_children(document, note_index)?;
    if children.len() != 1 || !has_name(element(document, children[0])?, "subList") {
        return Err(NoteHwpxError::InvalidNote);
    }
    require_whitespace_around_child(source, note, element(document, children[0])?)?;
    let wrapper = note.parent().ok_or(NoteHwpxError::InvalidNote)?;
    let wrapper_element = element(document, wrapper)?;
    if !has_name(wrapper_element, "ctrl")
        || !non_namespace_attributes(wrapper_element)?.is_empty()
        || direct_element_children(document, wrapper)? != vec![note_index]
    {
        return Err(NoteHwpxError::InvalidNote);
    }
    require_whitespace_around_child(source, wrapper_element, note)?;
    let run = wrapper_element.parent().ok_or(NoteHwpxError::InvalidNote)?;
    let run_element = element(document, run)?;
    if !has_name(run_element, "run") {
        return Err(NoteHwpxError::InvalidNote);
    }
    let paragraph = run_element.parent().ok_or(NoteHwpxError::InvalidNote)?;
    let paragraph_ordinal = paragraphs
        .iter()
        .position(|value| *value == paragraph)
        .ok_or(NoteHwpxError::InvalidNote)?;
    let runs = direct_children_named(document, paragraph, "run", limits.0.runs_per_paragraph)?;
    let run_ordinal = runs
        .iter()
        .position(|value| *value == run)
        .ok_or(NoteHwpxError::InvalidNote)?;
    let run_children =
        direct_element_children_bounded(document, run, limits.0.inline_elements_per_run)?;
    let wrapper_position = run_children
        .iter()
        .position(|value| *value == wrapper)
        .ok_or(NoteHwpxError::InvalidNote)?;
    let inline_ordinal = run_children[..wrapper_position]
        .iter()
        .filter(|&&child| !is_note_wrapper(document, child))
        .count();
    let payload_digests = payload_digests_from_document(source, document, children[0], limits)?;
    let native_instance_id = parse_required_u32(source, note, "instId", limits)?;
    if native_instance_id == 0 {
        return Err(NoteHwpxError::InvalidNote);
    }
    Ok(NoteProjection {
        wrapper,
        anchor_paragraph_ordinal: u32::try_from(paragraph_ordinal)
            .map_err(|_| NoteHwpxError::InputLimit)?,
        anchor_run_ordinal: u32::try_from(run_ordinal).map_err(|_| NoteHwpxError::InputLimit)?,
        anchor_inline_ordinal: u32::try_from(inline_ordinal)
            .map_err(|_| NoteHwpxError::InputLimit)?,
        native_instance_id,
        kind,
        flags: parse_optional_u32(source, note, "flag", limits)?.unwrap_or(0),
        number: parse_optional_u32(source, note, "number", limits)?
            .map(|value| u16::try_from(value).map_err(|_| NoteHwpxError::InvalidNote))
            .transpose()?
            .unwrap_or(0),
        user_character: parse_optional_character(source, note, "userChar", limits)?,
        prefix_character: parse_optional_character(source, note, "prefixChar", limits)?,
        suffix_character: parse_optional_character(source, note, "suffixChar", limits)?,
        marker_style_sha256: hex(digest_span(source, run_element.start_tag_span())?),
        payload_digests,
        wrapper_sha256: digest_span(source, outer_span(wrapper_element)?)?,
    })
}

struct ParsedPayload {
    digests: NoteHwpxPayloadDigests,
}

fn parse_payload(payload: &[u8], limits: NoteHwpxLimits) -> Result<ParsedPayload, NoteHwpxError> {
    if payload.is_empty() || payload.len() > limits.0.payload_bytes {
        return Err(NoteHwpxError::InputLimit);
    }
    let document = PreservingXmlDocument::parse(payload).map_err(|error| match error {
        PreservingXmlError::Safe(_) => NoteHwpxError::InvalidPayload,
        other => NoteHwpxError::Preserving(other),
    })?;
    if document.elements().len() > limits.0.elements {
        return Err(NoteHwpxError::InputLimit);
    }
    let mut roots = document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, candidate)| candidate.parent().is_none())
        .map(|(index, _)| index);
    let root = roots.next().ok_or(NoteHwpxError::InvalidPayload)?;
    let root_element = element(&document, root)?;
    let span = outer_span(root_element)?;
    if roots.next().is_some()
        || !has_name(root_element, "subList")
        || span.start() != 0
        || span.end() != payload.len()
        || direct_children_named(&document, root, "p", limits.0.paragraphs)?.is_empty()
    {
        return Err(NoteHwpxError::InvalidPayload);
    }
    let digests = payload_digests_from_document(payload, &document, root, limits)?;
    document.verify_untouched_round_trip()?;
    Ok(ParsedPayload { digests })
}

fn payload_digests_from_document(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    limits: NoteHwpxLimits,
) -> Result<NoteHwpxPayloadDigests, NoteHwpxError> {
    validate_plain_text_payload_document(source, document, root, limits)?;
    let span = outer_span(element(document, root)?)?;
    if span.len() > limits.0.payload_bytes {
        return Err(NoteHwpxError::InputLimit);
    }
    let body = source
        .get(span.start()..span.end())
        .ok_or(NoteHwpxError::InvalidPayload)?;
    Ok(NoteHwpxPayloadDigests {
        body_graph_sha256: hex(Sha256::digest(body).into()),
        plain_text_sha256: strict_plain_text_sha256(source, document, root, limits)?,
        body_style_sha256: style_projection_sha256(source, document, root)?,
    })
}

fn validate_plain_text_payload_document(
    source: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    limits: NoteHwpxLimits,
) -> Result<(), NoteHwpxError> {
    let sub_list = element(document, root)?;
    require_container_whitespace(document, root)?;
    let sub_list_attributes = non_namespace_attributes(sub_list)?;
    let required_sub_list = [
        "hasNumRef",
        "hasTextRef",
        "id",
        "lineWrap",
        "linkListIDRef",
        "linkListNextIDRef",
        "textDirection",
        "textHeight",
        "textWidth",
        "vertAlign",
    ];
    if !required_sub_list
        .iter()
        .all(|name| sub_list_attributes.contains(name))
        || !sub_list_attributes
            .iter()
            .all(|name| required_sub_list.contains(name) || *name == "metatag")
        || decoded_required_attribute(source, sub_list, "textDirection", limits)? != "HORIZONTAL"
        || decoded_required_attribute(source, sub_list, "lineWrap", limits)? != "BREAK"
        || decoded_required_attribute(source, sub_list, "vertAlign", limits)? != "TOP"
    {
        return Err(NoteHwpxError::InvalidPayload);
    }
    for name in [
        "linkListIDRef",
        "linkListNextIDRef",
        "textWidth",
        "textHeight",
    ] {
        let _ = parse_required_u32(source, sub_list, name, limits)
            .map_err(|_| NoteHwpxError::InvalidPayload)?;
    }
    for name in ["hasTextRef", "hasNumRef"] {
        let value = decoded_required_attribute(source, sub_list, name, limits)?;
        if !matches!(value.as_str(), "0" | "1") {
            return Err(NoteHwpxError::InvalidPayload);
        }
    }
    let paragraphs = direct_element_children(document, root)?;
    if paragraphs.is_empty() {
        return Err(NoteHwpxError::InvalidPayload);
    }
    for paragraph_index in paragraphs {
        validate_payload_paragraph(source, document, paragraph_index, limits)?;
    }
    Ok(())
}

fn validate_payload_paragraph(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraph_index: usize,
    limits: NoteHwpxLimits,
) -> Result<(), NoteHwpxError> {
    let paragraph = element(document, paragraph_index)?;
    require_container_whitespace(document, paragraph_index)?;
    let attributes = non_namespace_attributes(paragraph)?;
    let required = [
        "columnBreak",
        "id",
        "merged",
        "pageBreak",
        "paraPrIDRef",
        "styleIDRef",
    ];
    if !has_name(paragraph, "p")
        || attributes.len() != required.len()
        || !required.iter().all(|name| attributes.contains(name))
    {
        return Err(NoteHwpxError::InvalidPayload);
    }
    for name in ["id", "paraPrIDRef", "styleIDRef"] {
        let _ = parse_required_u32(source, paragraph, name, limits)
            .map_err(|_| NoteHwpxError::InvalidPayload)?;
    }
    for name in ["pageBreak", "columnBreak", "merged"] {
        let value = decoded_required_attribute(source, paragraph, name, limits)?;
        if !matches!(value.as_str(), "0" | "1") {
            return Err(NoteHwpxError::InvalidPayload);
        }
    }
    let runs = direct_element_children(document, paragraph_index)?;
    if runs.is_empty() {
        return Err(NoteHwpxError::InvalidPayload);
    }
    for run_index in runs {
        validate_payload_run(source, document, run_index, limits)?;
    }
    Ok(())
}

fn validate_payload_run(
    source: &[u8],
    document: &PreservingXmlDocument,
    run_index: usize,
    limits: NoteHwpxLimits,
) -> Result<(), NoteHwpxError> {
    let run = element(document, run_index)?;
    require_container_whitespace(document, run_index)?;
    if !has_name(run, "run") || non_namespace_attributes(run)? != vec!["charPrIDRef"] {
        return Err(NoteHwpxError::InvalidPayload);
    }
    let _ = parse_required_u32(source, run, "charPrIDRef", limits)
        .map_err(|_| NoteHwpxError::InvalidPayload)?;
    for text_index in direct_element_children(document, run_index)? {
        let text = element(document, text_index)?;
        if !has_name(text, "t") || text.first_child().is_some() {
            return Err(NoteHwpxError::InvalidPayload);
        }
        require_plain_text_tokens(document, text_index)?;
        let attributes = non_namespace_attributes(text)?;
        if attributes.len() > 1
            || attributes
                .first()
                .is_some_and(|name| *name != "charStyleIDRef")
        {
            return Err(NoteHwpxError::InvalidPayload);
        }
        if attributes == vec!["charStyleIDRef"] {
            let _ = parse_required_u32(source, text, "charStyleIDRef", limits)
                .map_err(|_| NoteHwpxError::InvalidPayload)?;
        }
    }
    Ok(())
}

fn require_container_whitespace(
    document: &PreservingXmlDocument,
    element_index: usize,
) -> Result<(), NoteHwpxError> {
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
        return Err(NoteHwpxError::InvalidPayload);
    }
    Ok(())
}

fn require_plain_text_tokens(
    document: &PreservingXmlDocument,
    element_index: usize,
) -> Result<(), NoteHwpxError> {
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
        return Err(NoteHwpxError::InvalidPayload);
    }
    Ok(())
}

fn style_projection_sha256(
    payload: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
) -> Result<String, NoteHwpxError> {
    let root_span = outer_span(element(document, root)?)?;
    let mut hasher = Sha256::new();
    for candidate in document.elements().iter().filter(|candidate| {
        is_within_span(candidate, root_span)
            && candidate.name().namespace() == Some(PARAGRAPH_NS)
            && matches!(candidate.name().local_name(), "subList" | "p" | "run" | "t")
    }) {
        let span = candidate.start_tag_span();
        let bytes = payload
            .get(span.start()..span.end())
            .ok_or(NoteHwpxError::InvalidPayload)?;
        hasher.update(
            u64::try_from(bytes.len())
                .map_err(|_| NoteHwpxError::InputLimit)?
                .to_le_bytes(),
        );
        hasher.update(bytes);
    }
    Ok(hex(hasher.finalize().into()))
}

fn strict_plain_text_sha256(
    payload: &[u8],
    document: &PreservingXmlDocument,
    root: usize,
    limits: NoteHwpxLimits,
) -> Result<Option<String>, NoteHwpxError> {
    let root_depth = element(document, root)?.depth();
    let root_span = outer_span(element(document, root)?)?;
    let mut text = String::new();
    for (index, candidate) in document
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, candidate)| {
            candidate.depth() > root_depth
                && is_within_span(candidate, root_span)
                && has_name(candidate, "t")
        })
    {
        if candidate.first_child().is_some() {
            return Ok(None);
        }
        for token in document.tokens().iter().filter(|token| {
            token.element_index() == Some(index)
                && matches!(
                    token.kind(),
                    XmlTokenKind::Text | XmlTokenKind::Whitespace | XmlTokenKind::Reference
                )
        }) {
            let span = token.span();
            let lexical = std::str::from_utf8(
                payload
                    .get(span.start()..span.end())
                    .ok_or(NoteHwpxError::InvalidPayload)?,
            )
            .map_err(|_| NoteHwpxError::InvalidPayload)?;
            let decoded = unescape(lexical).map_err(|_| NoteHwpxError::InvalidPayload)?;
            if text.len().saturating_add(decoded.len()) > limits.0.text_bytes {
                return Err(NoteHwpxError::InputLimit);
            }
            text.try_reserve(decoded.len())
                .map_err(|_| NoteHwpxError::AllocationFailed)?;
            text.push_str(&decoded);
        }
    }
    Ok(Some(hex(Sha256::digest(text.as_bytes()).into())))
}

fn is_within_span(candidate: &XmlElementToken, root: XmlByteSpan) -> bool {
    candidate
        .outer_span()
        .is_some_and(|span| span.start() >= root.start() && span.end() <= root.end())
}

fn validate_inserted_note(
    source: &[u8],
    readback: &NoteHwpxReadback,
    paragraph_ids: &[LogicalId],
    note: &NoteEntry,
    payload: &ParsedPayload,
    limits: NoteHwpxLimits,
) -> Result<(), NoteHwpxError> {
    ensure_closed_note(note)?;
    let paragraph_ordinal = paragraph_ids
        .iter()
        .position(|paragraph_id| paragraph_id == &note.anchor.paragraph_id)
        .ok_or(NoteHwpxError::NonRepresentable)?;
    if note.anchor.section_id != readback.state.sections()[0].section_id
        || note.body_graph_sha256 != payload.digests.body_graph_sha256
        || note.plain_text_sha256 != payload.digests.plain_text_sha256
        || note.body_style_sha256 != payload.digests.body_style_sha256
    {
        return Err(NoteHwpxError::ProjectionMismatch);
    }
    let marker_style = NoteHwpxReader::marker_style_sha256_at(
        source,
        u32::try_from(paragraph_ordinal).map_err(|_| NoteHwpxError::InputLimit)?,
        note.anchor.run_ordinal,
        limits,
    )?;
    if note.marker_style_sha256 != marker_style {
        return Err(NoteHwpxError::ProjectionMismatch);
    }
    for character in [
        note.marker.user_character.as_deref(),
        note.marker.prefix_character.as_deref(),
        note.marker.suffix_character.as_deref(),
    ]
    .into_iter()
    .flatten()
    {
        if character.chars().count() != 1
            || character.encode_utf16().count() != 1
            || character.chars().any(invalid_xml_character)
        {
            return Err(NoteHwpxError::NonRepresentable);
        }
    }
    Ok(())
}

fn ensure_closed_note(note: &NoteEntry) -> Result<(), NoteHwpxError> {
    if note.locked
        || note.opaque_native_payload_sha256 != EMPTY_SHA256
        || !note.opaque_properties.is_empty()
        || note.identity.native_instance_id == 0
        || note.native_tag != native_tag_for(note.kind)
    {
        return Err(NoteHwpxError::NonRepresentable);
    }
    Ok(())
}

struct ByteEdit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}

fn build_edit(
    source: &[u8],
    parsed: &ParsedNotes,
    transition: &NoteTransition,
    paragraph_ids: &[LogicalId],
    payload: &[u8],
    limits: NoteHwpxLimits,
) -> Result<ByteEdit, NoteHwpxError> {
    let paragraph_ordinal = paragraph_ids
        .iter()
        .position(|value| value == &transition.note.anchor.paragraph_id)
        .ok_or(NoteHwpxError::NonRepresentable)?;
    let paragraph_ordinal_u32 =
        u32::try_from(paragraph_ordinal).map_err(|_| NoteHwpxError::InputLimit)?;
    let run = run_at(
        &parsed.document,
        &parsed.paragraphs,
        paragraph_ordinal_u32,
        transition.note.anchor.run_ordinal,
        limits,
    )?;
    let offset = insertion_offset(
        parsed,
        run,
        paragraph_ordinal_u32,
        transition.note.anchor.run_ordinal,
        transition.note.anchor.inline_ordinal,
        transition.index,
        limits,
    )?;
    let prefix = element_prefix(source, element(&parsed.document, run)?)?;
    let replacement = native_wrapper(&prefix, &transition.note, payload, limits)?;
    Ok(ByteEdit {
        start: offset,
        end: offset,
        replacement,
    })
}

const fn native_tag_for(kind: NoteKind) -> NoteNativeTag {
    match kind {
        NoteKind::Footnote => NoteNativeTag::FootNote,
        NoteKind::Endnote => NoteNativeTag::EndNote,
    }
}

fn run_at(
    document: &PreservingXmlDocument,
    paragraphs: &[usize],
    paragraph_ordinal: u32,
    run_ordinal: u32,
    limits: NoteHwpxLimits,
) -> Result<usize, NoteHwpxError> {
    let paragraph = *paragraphs
        .get(usize::try_from(paragraph_ordinal).map_err(|_| NoteHwpxError::NonRepresentable)?)
        .ok_or(NoteHwpxError::NonRepresentable)?;
    let runs = direct_children_named(document, paragraph, "run", limits.0.runs_per_paragraph)?;
    runs.get(usize::try_from(run_ordinal).map_err(|_| NoteHwpxError::NonRepresentable)?)
        .copied()
        .ok_or(NoteHwpxError::NonRepresentable)
}

fn insertion_offset(
    parsed: &ParsedNotes,
    run: usize,
    paragraph_ordinal: u32,
    run_ordinal: u32,
    inline_ordinal: u32,
    target_index: usize,
    limits: NoteHwpxLimits,
) -> Result<usize, NoteHwpxError> {
    let children =
        direct_element_children_bounded(&parsed.document, run, limits.0.inline_elements_per_run)?;
    let wanted = usize::try_from(inline_ordinal).map_err(|_| NoteHwpxError::NonRepresentable)?;
    let mut non_note = 0_usize;
    let mut after_same_boundary = None;
    for child in children {
        if let Some(source_index) = parsed
            .projections
            .iter()
            .position(|projection| projection.wrapper == child)
        {
            let projection = &parsed.projections[source_index];
            if projection.anchor_paragraph_ordinal == paragraph_ordinal
                && projection.anchor_run_ordinal == run_ordinal
                && projection.anchor_inline_ordinal == inline_ordinal
            {
                let existing_target_index = if source_index < target_index {
                    source_index
                } else {
                    source_index.saturating_add(1)
                };
                let span = outer_span(element(&parsed.document, child)?)?;
                if existing_target_index > target_index {
                    return Ok(span.start());
                }
                after_same_boundary = Some(span.end());
            }
            continue;
        }
        if is_note_wrapper(&parsed.document, child) {
            return Err(NoteHwpxError::ProjectionMismatch);
        }
        if non_note == wanted {
            return Ok(after_same_boundary
                .unwrap_or(element(&parsed.document, child)?.start_tag_span().start()));
        }
        non_note = non_note.checked_add(1).ok_or(NoteHwpxError::InputLimit)?;
    }
    if non_note != wanted {
        return Err(NoteHwpxError::NonRepresentable);
    }
    if let Some(offset) = after_same_boundary {
        return Ok(offset);
    }
    element(&parsed.document, run)?
        .end_tag_span()
        .map(XmlByteSpan::start)
        .ok_or(NoteHwpxError::UnsupportedStructure)
}

fn native_wrapper(
    prefix: &str,
    note: &NoteEntry,
    payload: &[u8],
    limits: NoteHwpxLimits,
) -> Result<Vec<u8>, NoteHwpxError> {
    use std::fmt::Write as _;

    let tag = match note.native_tag {
        NoteNativeTag::FootNote => "footNote",
        NoteNativeTag::EndNote => "endNote",
    };
    let mut start = format!("<{prefix}ctrl><{prefix}{tag}");
    if note.marker.flags > 0 {
        let _ = write!(start, " flag=\"{}\"", note.marker.flags);
    }
    if note.marker.number > 0 {
        let _ = write!(start, " number=\"{}\"", note.marker.number);
    }
    for (name, value) in [
        ("userChar", note.marker.user_character.as_deref()),
        ("prefixChar", note.marker.prefix_character.as_deref()),
        ("suffixChar", note.marker.suffix_character.as_deref()),
    ] {
        if let Some(value) = value {
            let _ = write!(start, " {name}=\"{}\"", escape_attribute(value, limits)?);
        }
    }
    let _ = write!(start, " instId=\"{}\">", note.identity.native_instance_id);
    let end = format!("</{prefix}{tag}></{prefix}ctrl>");
    let output_len = start
        .len()
        .checked_add(payload.len())
        .and_then(|value| value.checked_add(end.len()))
        .ok_or(NoteHwpxError::OutputLimit)?;
    if output_len > limits.0.output_bytes {
        return Err(NoteHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| NoteHwpxError::AllocationFailed)?;
    output.extend_from_slice(start.as_bytes());
    output.extend_from_slice(payload);
    output.extend_from_slice(end.as_bytes());
    Ok(output)
}

fn apply_edit(
    source: &[u8],
    edit: &ByteEdit,
    limits: NoteHwpxLimits,
) -> Result<Vec<u8>, NoteHwpxError> {
    if edit.start > edit.end || edit.end > source.len() {
        return Err(NoteHwpxError::PreservationMismatch);
    }
    let output_len = source
        .len()
        .checked_sub(edit.end - edit.start)
        .and_then(|value| value.checked_add(edit.replacement.len()))
        .ok_or(NoteHwpxError::OutputLimit)?;
    if output_len > limits.0.output_bytes {
        return Err(NoteHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| NoteHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..edit.start]);
    output.extend_from_slice(&edit.replacement);
    output.extend_from_slice(&source[edit.end..]);
    Ok(output)
}

fn verify_preservation(source: &[u8], output: &[u8], edit: &ByteEdit) -> Result<(), NoteHwpxError> {
    let suffix_start = edit
        .start
        .checked_add(edit.replacement.len())
        .ok_or(NoteHwpxError::PreservationMismatch)?;
    if output.get(..edit.start) != source.get(..edit.start)
        || output.get(edit.start..suffix_start) != Some(edit.replacement.as_slice())
        || output.get(suffix_start..) != source.get(edit.end..)
    {
        return Err(NoteHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn validate_plan(
    plan: &NoteHwpxPlan,
    state_limits: NoteLimits,
    limits: NoteHwpxLimits,
) -> Result<(), NoteHwpxError> {
    if plan.schema_version != "hwpx-agent.note-hwpx-plan/v1"
        || plan.profile_id != NOTE_HWPX_PROFILE_ID
        || !matches!(
            plan.domain_plan.capability_id(),
            "ref.footnote_insert" | "ref.endnote_insert"
        )
        || plan.source_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        || plan.source_state_sha256 != plan.domain_plan.source_state_sha256()
        || plan.source_state != *plan.domain_plan.source_state()
        || plan.source_state.canonical_sha256(state_limits)? != plan.source_state_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(NoteHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &NoteHwpxPlan,
    limits: NoteHwpxLimits,
) -> Result<String, NoteHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: NoteHwpxLimits,
) -> Result<Vec<u8>, NoteHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| NoteHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(NoteHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn validate_paragraph_map(
    paragraph_ids: &[LogicalId],
    paragraph_count: usize,
    limits: NoteHwpxLimits,
) -> Result<(), NoteHwpxError> {
    if paragraph_ids.len() != paragraph_count || paragraph_ids.len() > limits.0.paragraphs {
        return Err(NoteHwpxError::ProjectionMismatch);
    }
    let mut unique = BTreeSet::new();
    if paragraph_ids.iter().any(|value| !unique.insert(value)) {
        return Err(NoteHwpxError::ProjectionMismatch);
    }
    Ok(())
}

fn direct_element_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, NoteHwpxError> {
    direct_element_children_bounded(document, parent, usize::MAX)
}

fn direct_element_children_bounded(
    document: &PreservingXmlDocument,
    parent: usize,
    maximum: usize,
) -> Result<Vec<usize>, NoteHwpxError> {
    let mut children = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        if children.len() >= maximum {
            return Err(NoteHwpxError::InputLimit);
        }
        children
            .try_reserve(1)
            .map_err(|_| NoteHwpxError::AllocationFailed)?;
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
) -> Result<Vec<usize>, NoteHwpxError> {
    let mut matches = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        if has_name(element(document, index)?, local_name) {
            if matches.len() >= maximum {
                return Err(NoteHwpxError::InputLimit);
            }
            matches
                .try_reserve(1)
                .map_err(|_| NoteHwpxError::AllocationFailed)?;
            matches.push(index);
        }
        child = element(document, index)?.next_sibling();
    }
    Ok(matches)
}

fn is_note_wrapper(document: &PreservingXmlDocument, index: usize) -> bool {
    element(document, index).is_ok_and(|value| has_name(value, "ctrl"))
        && direct_element_children(document, index).is_ok_and(|children| {
            children.len() == 1
                && element(document, children[0])
                    .is_ok_and(|value| has_name(value, "footNote") || has_name(value, "endNote"))
        })
}

fn require_whitespace_around_child(
    source: &[u8],
    parent: &XmlElementToken,
    child: &XmlElementToken,
) -> Result<(), NoteHwpxError> {
    let content = parent.content_span().ok_or(NoteHwpxError::InvalidNote)?;
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
        return Err(NoteHwpxError::InvalidNote);
    }
    Ok(())
}

fn non_namespace_attributes(element: &XmlElementToken) -> Result<Vec<&str>, NoteHwpxError> {
    let mut names = Vec::new();
    for attribute in element
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
    {
        if attribute.name().namespace().is_some() || names.contains(&attribute.name().local_name())
        {
            return Err(NoteHwpxError::InvalidNote);
        }
        names
            .try_reserve(1)
            .map_err(|_| NoteHwpxError::AllocationFailed)?;
        names.push(attribute.name().local_name());
    }
    names.sort_unstable();
    Ok(names)
}

fn optional_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<Option<&'a XmlAttributeToken>, NoteHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration() && attribute.name().local_name() == name
    });
    let value = matches.next();
    if value.is_some_and(|attribute| attribute.name().namespace().is_some())
        || matches.next().is_some()
    {
        return Err(NoteHwpxError::InvalidNote);
    }
    Ok(value)
}

fn decoded_required_attribute(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    limits: NoteHwpxLimits,
) -> Result<String, NoteHwpxError> {
    let attribute = optional_attribute(element, name)?.ok_or(NoteHwpxError::InvalidPayload)?;
    decoded_attribute(source, attribute, limits)
}

fn parse_required_u32(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    limits: NoteHwpxLimits,
) -> Result<u32, NoteHwpxError> {
    parse_optional_u32(source, element, name, limits)?.ok_or(NoteHwpxError::InvalidNote)
}

fn parse_optional_u32(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    limits: NoteHwpxLimits,
) -> Result<Option<u32>, NoteHwpxError> {
    optional_attribute(element, name)?
        .map(|attribute| {
            let value = decoded_attribute(source, attribute, limits)?;
            if value.is_empty()
                || (value.len() > 1 && value.starts_with('0'))
                || !value.bytes().all(|byte| byte.is_ascii_digit())
            {
                return Err(NoteHwpxError::InvalidNote);
            }
            value.parse().map_err(|_| NoteHwpxError::InvalidNote)
        })
        .transpose()
}

fn parse_optional_character(
    source: &[u8],
    element: &XmlElementToken,
    name: &str,
    limits: NoteHwpxLimits,
) -> Result<Option<String>, NoteHwpxError> {
    optional_attribute(element, name)?
        .map(|attribute| {
            let value = decoded_attribute(source, attribute, limits)?;
            if value.chars().count() != 1
                || value.encode_utf16().count() != 1
                || value.chars().any(invalid_xml_character)
            {
                return Err(NoteHwpxError::InvalidNote);
            }
            Ok(value)
        })
        .transpose()
}

fn decoded_attribute(
    source: &[u8],
    attribute: &XmlAttributeToken,
    limits: NoteHwpxLimits,
) -> Result<String, NoteHwpxError> {
    let lexical = std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(NoteHwpxError::InvalidNote)?,
    )
    .map_err(|_| NoteHwpxError::InvalidNote)?;
    if lexical.len() > limits.0.text_bytes {
        return Err(NoteHwpxError::InputLimit);
    }
    let value = unescape(lexical).map_err(|_| NoteHwpxError::InvalidNote)?;
    if value.len() > limits.0.text_bytes || value.chars().any(invalid_xml_character) {
        return Err(NoteHwpxError::InputLimit);
    }
    Ok(value.into_owned())
}

fn escape_attribute(value: &str, limits: NoteHwpxLimits) -> Result<String, NoteHwpxError> {
    if value.is_empty()
        || value.len() > limits.0.text_bytes
        || value.chars().any(invalid_xml_character)
    {
        return Err(NoteHwpxError::OutputLimit);
    }
    Ok(value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;"))
}

const fn invalid_xml_character(value: char) -> bool {
    !matches!(
        value as u32,
        0x9 | 0xA | 0xD | 0x20..=0xD7FF | 0xE000..=0xFFFD | 0x0001_0000..=0x0010_FFFF
    )
}

fn element_prefix(source: &[u8], element: &XmlElementToken) -> Result<String, NoteHwpxError> {
    let name = std::str::from_utf8(
        source
            .get(element.start_name_span().start()..element.start_name_span().end())
            .ok_or(NoteHwpxError::UnsupportedStructure)?,
    )
    .map_err(|_| NoteHwpxError::UnsupportedStructure)?;
    let Some((prefix, local)) = name.rsplit_once(':') else {
        if name != "run" {
            return Err(NoteHwpxError::UnsupportedStructure);
        }
        return Ok(String::new());
    };
    if local != "run"
        || prefix.is_empty()
        || !prefix
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
    {
        return Err(NoteHwpxError::UnsupportedStructure);
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
) -> Result<&XmlElementToken, NoteHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(NoteHwpxError::UnsupportedStructure)
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, NoteHwpxError> {
    element
        .outer_span()
        .ok_or(NoteHwpxError::UnsupportedStructure)
}

fn digest_span(source: &[u8], span: XmlByteSpan) -> Result<[u8; 32], NoteHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(NoteHwpxError::UnsupportedStructure)?,
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
    #![allow(clippy::expect_used, clippy::too_many_lines)] // Sealed-plan fixture stays local.

    use super::*;
    use domain_ir::{
        NOTE_ENGINE_SCHEMA_VERSION, NoteAnchor, NoteAutoNumberFormat, NoteDocumentStateDraft,
        NoteIdentity, NoteLimitConfig, NoteLineStyle, NoteLineType, NoteLineWidth,
        NoteMarkerProperties, NoteNumberFormat, NoteNumberingRestart, NoteOperation, NotePlacement,
        NoteRequest, NoteRequestDraft, NoteSectionState, NoteSpacing, NoteStyle,
    };

    const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
    const C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
    const D: &str = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";

    fn id(value: &str) -> LogicalId {
        LogicalId::parse(value).expect("valid id")
    }

    fn state_limits() -> NoteLimits {
        NoteLimits::new(NoteLimitConfig::default()).expect("valid state limits")
    }

    fn hwpx_limits() -> NoteHwpxLimits {
        NoteHwpxLimits::new(NoteHwpxLimitConfig::default()).expect("valid HWPX limits")
    }

    fn style(kind: NoteKind) -> NoteStyle {
        NoteStyle {
            kind,
            auto_number_format: NoteAutoNumberFormat {
                format: NoteNumberFormat::Digit,
                user_character: String::new(),
                prefix_character: String::new(),
                suffix_character: ")".to_owned(),
                superscript: false,
            },
            note_line: NoteLineStyle {
                length_hwp_units: -1,
                line_type: NoteLineType::Solid,
                width: NoteLineWidth::Mm0_12,
                color_rgb: 0,
            },
            spacing: NoteSpacing {
                between_notes_hwp_units: 0,
                below_line_hwp_units: 0,
                above_line_hwp_units: 0,
            },
            numbering_restart: NoteNumberingRestart::Continuous,
            new_number: 1,
            placement: match kind {
                NoteKind::Footnote => NotePlacement::EachColumn,
                NoteKind::Endnote => NotePlacement::EndOfDocument,
            },
            beneath_text: false,
            opaque_style_sha256: A.to_owned(),
            locked: false,
        }
    }

    #[test]
    fn tampered_private_plan_binding_is_rejected() {
        let state_limits = state_limits();
        let hwpx_limits = hwpx_limits();
        let section_id = id("section");
        let paragraph_id = id("paragraph");
        let state = NoteDocumentState::from_draft(
            NoteDocumentStateDraft {
                schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
                sections: vec![NoteSectionState {
                    section_id: section_id.clone(),
                    footnote_style: style(NoteKind::Footnote),
                    endnote_style: style(NoteKind::Endnote),
                    opaque_section_state_sha256: B.to_owned(),
                    locked: false,
                }],
                notes: Vec::new(),
                non_note_content_sha256: A.to_owned(),
                style_catalog_sha256: B.to_owned(),
                numbering_inventory_sha256: A.to_owned(),
                reference_inventory_sha256: B.to_owned(),
                resource_inventory_sha256: A.to_owned(),
                document_protection_sha256: B.to_owned(),
                opaque_document_state_sha256: A.to_owned(),
                document_locked: false,
            },
            state_limits,
        )
        .expect("state");
        let source = br#"<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p><hp:run charPrIDRef="7"><hp:t>X</hp:t></hp:run></hp:p></hp:sec>"#;
        let payload = br#"<hp:subList xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="TOP" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0"><hp:p id="1" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:t>PRIVATE</hp:t></hp:run></hp:p></hp:subList>"#;
        let digests = NoteHwpxReader::inspect_payload(payload, hwpx_limits).expect("payload");
        let note = NoteEntry {
            identity: NoteIdentity {
                logical_note_id: id("note"),
                native_instance_id: 1,
            },
            anchor: NoteAnchor {
                section_id,
                paragraph_id: paragraph_id.clone(),
                run_ordinal: 0,
                inline_ordinal: 1,
            },
            kind: NoteKind::Footnote,
            native_tag: NoteNativeTag::FootNote,
            marker: NoteMarkerProperties {
                flags: 0,
                number: 1,
                user_character: None,
                prefix_character: None,
                suffix_character: Some(")".to_owned()),
            },
            body_graph_sha256: digests.body_graph_sha256,
            plain_text_sha256: digests.plain_text_sha256,
            marker_style_sha256: NoteHwpxReader::marker_style_sha256_at(source, 0, 0, hwpx_limits)
                .expect("marker style"),
            body_style_sha256: digests.body_style_sha256,
            opaque_native_payload_sha256: EMPTY_SHA256.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        };
        let request = NoteRequest::from_draft(
            NoteRequestDraft {
                schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
                request_id: id("request"),
                expected_source_state_sha256: state
                    .canonical_sha256(state_limits)
                    .expect("state digest"),
                expected_document_flow_sha256: C.to_owned(),
                target_document_flow_sha256: D.to_owned(),
                operation: NoteOperation::Insert {
                    insertion_index: 0,
                    note,
                },
            },
            &state,
            C,
            state_limits,
        )
        .expect("request");
        let domain = NoteBuilder::plan(&state, &request, C, state_limits).expect("domain plan");
        let mut plan = NoteHwpxBuilder::plan(
            source,
            &state,
            &domain,
            C,
            &[paragraph_id],
            payload,
            state_limits,
            hwpx_limits,
        )
        .expect("adapter plan");
        plan.insert_payload_bytes += 1;
        assert_eq!(
            NoteHwpxLowerer::lower_section(
                source,
                payload,
                &plan,
                &state,
                C,
                state_limits,
                hwpx_limits
            ),
            Err(NoteHwpxError::PlanTampered)
        );
    }
}
