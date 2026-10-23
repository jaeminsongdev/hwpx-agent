use std::fmt;

use domain_ir::{
    BookmarkEntry, BookmarkNativeTag, LinkPoint, LinkReferenceBuilder, LinkReferenceDocumentState,
    LinkReferenceError, LinkReferenceLimits, LinkReferencePlan,
};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
};

pub const BOOKMARK_HWPX_PROFILE_ID: &str = "hwpx-agent.bookmark-hwpx.hwpml-2011-point-marker/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BookmarkHwpxLimitConfig {
    pub section_bytes: usize,
    pub elements: usize,
    pub paragraphs: usize,
    pub runs_per_paragraph: usize,
    pub inline_elements_per_run: usize,
    pub bookmarks: usize,
    pub name_bytes: usize,
    pub plan_bytes: usize,
    pub output_bytes: usize,
}

impl Default for BookmarkHwpxLimitConfig {
    fn default() -> Self {
        Self {
            section_bytes: 32 * 1024 * 1024,
            elements: 1_000_000,
            paragraphs: 262_144,
            runs_per_paragraph: 65_536,
            inline_elements_per_run: 262_144,
            bookmarks: 65_536,
            name_bytes: 64 * 1024,
            plan_bytes: 32 * 1024 * 1024,
            output_bytes: 32 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BookmarkHwpxLimits(BookmarkHwpxLimitConfig);

impl BookmarkHwpxLimits {
    pub const HARD_MAX_SECTION_BYTES: usize = 128 * 1024 * 1024;
    pub const HARD_MAX_ELEMENTS: usize = 2_000_000;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_NAME_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_PLAN_BYTES: usize = 64 * 1024 * 1024;
    pub const HARD_MAX_OUTPUT_BYTES: usize = 128 * 1024 * 1024;

    /// Creates finite limits without silently clamping a caller value.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: BookmarkHwpxLimitConfig) -> Result<Self, BookmarkHwpxError> {
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
            || config.bookmarks == 0
            || config.bookmarks > Self::HARD_MAX_ITEMS
            || config.name_bytes == 0
            || config.name_bytes > Self::HARD_MAX_NAME_BYTES
            || config.plan_bytes == 0
            || config.plan_bytes > Self::HARD_MAX_PLAN_BYTES
            || config.output_bytes == 0
            || config.output_bytes > Self::HARD_MAX_OUTPUT_BYTES
            || config.section_bytes > config.output_bytes
        {
            return Err(BookmarkHwpxError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> BookmarkHwpxLimitConfig {
        self.0
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct BookmarkHwpxReadback {
    pub state: LinkReferenceDocumentState,
    pub section_sha256: [u8; 32],
    pub bookmark_wrapper_sha256: Vec<[u8; 32]>,
    pub bookmark_count: usize,
}

impl fmt::Debug for BookmarkHwpxReadback {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BookmarkHwpxReadback")
            .field("bookmark_count", &self.bookmark_count)
            .field("state", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Serialize)]
pub struct BookmarkHwpxPlan {
    schema_version: &'static str,
    profile_id: &'static str,
    source_section_sha256: [u8; 32],
    source_bookmark_wrapper_sha256: Vec<[u8; 32]>,
    source_state: LinkReferenceDocumentState,
    source_state_sha256: String,
    source_document_flow_sha256: String,
    domain_plan: LinkReferencePlan,
    plan_sha256: String,
}

impl BookmarkHwpxPlan {
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
    /// Returns serialization or output-limit failure.
    pub fn canonical_json(&self, limits: BookmarkHwpxLimits) -> Result<Vec<u8>, BookmarkHwpxError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for BookmarkHwpxPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BookmarkHwpxPlan")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.domain_plan.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct BookmarkHwpxLoweringReceipt {
    pub profile_id: &'static str,
    pub capability_id: &'static str,
    pub source_section_sha256: [u8; 32],
    pub output_section_sha256: [u8; 32],
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub plan_sha256: String,
    pub target_document_flow_sha256: String,
    pub inserted_bookmarks: usize,
    pub deleted_bookmarks: usize,
    pub source_bytes: usize,
    pub output_bytes: usize,
}

impl fmt::Debug for BookmarkHwpxLoweringReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BookmarkHwpxLoweringReceipt")
            .field("profile_id", &self.profile_id)
            .field("capability_id", &self.capability_id)
            .field("inserted_bookmarks", &self.inserted_bookmarks)
            .field("deleted_bookmarks", &self.deleted_bookmarks)
            .field("source_bytes", &self.source_bytes)
            .field("output_bytes", &self.output_bytes)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum BookmarkHwpxError {
    #[error("bookmark HWPX limits are invalid")]
    InvalidLimit,
    #[error("bookmark HWPX input exceeds a finite limit")]
    InputLimit,
    #[error("bookmark HWPX section structure is unsupported")]
    UnsupportedStructure,
    #[error("bookmark HWPX native marker is missing, duplicated, or malformed")]
    InvalidBookmark,
    #[error("bookmark HWPX projection differs from the bound typed state")]
    ProjectionMismatch,
    #[error("bookmark operation is not representable by the point-marker profile")]
    NonRepresentable,
    #[error("bookmark HWPX section, state, marker, or flow drifted")]
    SourceDrift,
    #[error("bookmark HWPX plan was tampered with")]
    PlanTampered,
    #[error("bookmark HWPX preservation proof failed")]
    PreservationMismatch,
    #[error("bookmark HWPX output exceeds a finite limit")]
    OutputLimit,
    #[error("bookmark HWPX allocation failed")]
    AllocationFailed,
    #[error("bookmark link/reference domain validation failed")]
    Domain(#[from] LinkReferenceError),
    #[error("bookmark preserving XML admission failed")]
    Preserving(#[from] PreservingXmlError),
}

impl BookmarkHwpxError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "bookmark_hwpx_invalid_limit",
            Self::InputLimit => "bookmark_hwpx_input_limit",
            Self::UnsupportedStructure => "bookmark_hwpx_unsupported_structure",
            Self::InvalidBookmark => "bookmark_hwpx_invalid_bookmark",
            Self::ProjectionMismatch => "bookmark_hwpx_projection_mismatch",
            Self::NonRepresentable => "bookmark_hwpx_non_representable",
            Self::SourceDrift => "bookmark_hwpx_source_drift",
            Self::PlanTampered => "bookmark_hwpx_plan_tampered",
            Self::PreservationMismatch => "bookmark_hwpx_preservation_mismatch",
            Self::OutputLimit => "bookmark_hwpx_output_limit",
            Self::AllocationFailed => "bookmark_hwpx_allocation_failed",
            Self::Domain(_) => "bookmark_hwpx_domain",
            Self::Preserving(_) => "bookmark_hwpx_preserving_xml",
        }
    }
}

#[derive(Debug)]
pub struct BookmarkHwpxReader;

impl BookmarkHwpxReader {
    /// Verifies the complete point-bookmark projection against one typed state.
    ///
    /// # Errors
    ///
    /// Rejects malformed, ambiguous, stale, non-point, or over-limit sections.
    pub fn read_section(
        source: &[u8],
        expected: &LinkReferenceDocumentState,
        state_limits: LinkReferenceLimits,
        hwpx_limits: BookmarkHwpxLimits,
    ) -> Result<BookmarkHwpxReadback, BookmarkHwpxError> {
        let parsed = parse_bookmarks(source, expected, state_limits, hwpx_limits)?;
        let mut wrapper_digests = Vec::new();
        wrapper_digests
            .try_reserve_exact(parsed.projections.len())
            .map_err(|_| BookmarkHwpxError::AllocationFailed)?;
        for projection in &parsed.projections {
            wrapper_digests.push(projection.wrapper_sha256);
        }
        Ok(BookmarkHwpxReadback {
            state: expected.clone(),
            section_sha256: Sha256::digest(source).into(),
            bookmark_wrapper_sha256: wrapper_digests,
            bookmark_count: parsed.projections.len(),
        })
    }
}

#[derive(Debug)]
pub struct BookmarkHwpxBuilder;

impl BookmarkHwpxBuilder {
    /// Binds one exact REF-031 or REF-032 plan to a complete section snapshot.
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
        hwpx_limits: BookmarkHwpxLimits,
    ) -> Result<BookmarkHwpxPlan, BookmarkHwpxError> {
        if !matches!(
            domain_plan.capability_id(),
            "ref.bookmark_insert" | "ref.bookmark_delete"
        ) || domain_plan.source_document_flow_sha256() != current_document_flow_sha256
        {
            return Err(BookmarkHwpxError::NonRepresentable);
        }
        let built = LinkReferenceBuilder::build(
            domain_plan,
            source_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let _ = bookmark_transition(
            source_state,
            &built.state,
            domain_plan.capability_id(),
            state_limits,
        )?;
        let readback =
            BookmarkHwpxReader::read_section(source, source_state, state_limits, hwpx_limits)?;
        let mut plan = BookmarkHwpxPlan {
            schema_version: "hwpx-agent.bookmark-hwpx-plan/v1",
            profile_id: BOOKMARK_HWPX_PROFILE_ID,
            source_section_sha256: readback.section_sha256,
            source_bookmark_wrapper_sha256: readback.bookmark_wrapper_sha256,
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
pub struct BookmarkHwpxLowerer;

impl BookmarkHwpxLowerer {
    /// Applies exactly one native point-bookmark insertion or deletion.
    ///
    /// # Errors
    ///
    /// Returns no bytes on plan, source, state, flow, projection, preservation, or limit drift.
    pub fn lower_section_with_receipt(
        source: &[u8],
        plan: &BookmarkHwpxPlan,
        current_state: &LinkReferenceDocumentState,
        current_document_flow_sha256: &str,
        state_limits: LinkReferenceLimits,
        hwpx_limits: BookmarkHwpxLimits,
    ) -> Result<(Vec<u8>, BookmarkHwpxLoweringReceipt), BookmarkHwpxError> {
        validate_plan(plan, state_limits, hwpx_limits)?;
        if Sha256::digest(source).as_slice() != plan.source_section_sha256
            || current_document_flow_sha256 != plan.source_document_flow_sha256
            || current_state.canonical_sha256(state_limits)? != plan.source_state_sha256
            || current_state != &plan.source_state
        {
            return Err(BookmarkHwpxError::SourceDrift);
        }
        let built = LinkReferenceBuilder::build(
            &plan.domain_plan,
            current_state,
            current_document_flow_sha256,
            state_limits,
        )?;
        let transition = bookmark_transition(
            current_state,
            &built.state,
            plan.domain_plan.capability_id(),
            state_limits,
        )?;
        let parsed = parse_bookmarks(source, current_state, state_limits, hwpx_limits)?;
        let mut current_digests = Vec::new();
        current_digests
            .try_reserve_exact(parsed.projections.len())
            .map_err(|_| BookmarkHwpxError::AllocationFailed)?;
        for projection in &parsed.projections {
            current_digests.push(projection.wrapper_sha256);
        }
        if current_digests != plan.source_bookmark_wrapper_sha256 {
            return Err(BookmarkHwpxError::SourceDrift);
        }
        let edit = build_edit(source, &parsed, &transition, &built.state, hwpx_limits)?;
        let output = apply_edit(source, &edit, hwpx_limits)?;
        verify_preservation(source, &output, &edit)?;
        let target =
            BookmarkHwpxReader::read_section(&output, &built.state, state_limits, hwpx_limits)?;
        let (inserted_bookmarks, deleted_bookmarks) = match transition {
            BookmarkTransition::Insert { .. } => (1, 0),
            BookmarkTransition::Delete { .. } => (0, 1),
        };
        let receipt = BookmarkHwpxLoweringReceipt {
            profile_id: BOOKMARK_HWPX_PROFILE_ID,
            capability_id: plan.domain_plan.capability_id(),
            source_section_sha256: plan.source_section_sha256,
            output_section_sha256: target.section_sha256,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: built.state.canonical_sha256(state_limits)?,
            plan_sha256: plan.plan_sha256.clone(),
            target_document_flow_sha256: plan.domain_plan.target_document_flow_sha256().to_owned(),
            inserted_bookmarks,
            deleted_bookmarks,
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
        plan: &BookmarkHwpxPlan,
        current_state: &LinkReferenceDocumentState,
        current_document_flow_sha256: &str,
        state_limits: LinkReferenceLimits,
        hwpx_limits: BookmarkHwpxLimits,
    ) -> Result<Vec<u8>, BookmarkHwpxError> {
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
enum BookmarkTransition {
    Insert {
        index: usize,
        bookmark: BookmarkEntry,
    },
    Delete {
        index: usize,
        bookmark: BookmarkEntry,
    },
}

fn bookmark_transition(
    source: &LinkReferenceDocumentState,
    target: &LinkReferenceDocumentState,
    capability_id: &str,
    state_limits: LinkReferenceLimits,
) -> Result<BookmarkTransition, BookmarkHwpxError> {
    if non_bookmark_state(source, state_limits)? != non_bookmark_state(target, state_limits)? {
        return Err(BookmarkHwpxError::NonRepresentable);
    }
    let before = source.bookmarks();
    let after = target.bookmarks();
    match capability_id {
        "ref.bookmark_insert" if after.len() == before.len().saturating_add(1) => {
            let mut matched = None;
            for index in 0..after.len() {
                if before[..index] == after[..index]
                    && before[index..] == after[index + 1..]
                    && matched.replace(index).is_some()
                {
                    return Err(BookmarkHwpxError::NonRepresentable);
                }
            }
            let index = matched.ok_or(BookmarkHwpxError::NonRepresentable)?;
            ensure_point_bookmark(&after[index])?;
            Ok(BookmarkTransition::Insert {
                index,
                bookmark: after[index].clone(),
            })
        }
        "ref.bookmark_delete" if before.len() == after.len().saturating_add(1) => {
            let mut matched = None;
            for index in 0..before.len() {
                if after[..index] == before[..index]
                    && after[index..] == before[index + 1..]
                    && matched.replace(index).is_some()
                {
                    return Err(BookmarkHwpxError::NonRepresentable);
                }
            }
            let index = matched.ok_or(BookmarkHwpxError::NonRepresentable)?;
            ensure_point_bookmark(&before[index])?;
            Ok(BookmarkTransition::Delete {
                index,
                bookmark: before[index].clone(),
            })
        }
        _ => Err(BookmarkHwpxError::NonRepresentable),
    }
}

fn non_bookmark_state(
    state: &LinkReferenceDocumentState,
    limits: LinkReferenceLimits,
) -> Result<serde_json::Value, BookmarkHwpxError> {
    let mut value: serde_json::Value = serde_json::from_slice(&state.canonical_json(limits)?)
        .map_err(|_| BookmarkHwpxError::PlanTampered)?;
    value
        .as_object_mut()
        .ok_or(BookmarkHwpxError::PlanTampered)?
        .remove("bookmarks")
        .ok_or(BookmarkHwpxError::PlanTampered)?;
    Ok(value)
}

fn ensure_point_bookmark(bookmark: &BookmarkEntry) -> Result<(), BookmarkHwpxError> {
    if bookmark.native_tag != BookmarkNativeTag::Bookmark
        || bookmark.anchor.start != bookmark.anchor.end
        || bookmark.locked
        || bookmark.opaque_native_payload_sha256 != EMPTY_SHA256
        || !bookmark.opaque_properties.is_empty()
    {
        return Err(BookmarkHwpxError::NonRepresentable);
    }
    Ok(())
}

struct BookmarkProjection {
    root: usize,
    wrapper: usize,
    anchor: LinkPoint,
    wrapper_sha256: [u8; 32],
}

struct ParsedBookmarks {
    document: PreservingXmlDocument,
    paragraphs: Vec<usize>,
    projections: Vec<BookmarkProjection>,
}

fn parse_bookmarks(
    source: &[u8],
    expected: &LinkReferenceDocumentState,
    state_limits: LinkReferenceLimits,
    limits: BookmarkHwpxLimits,
) -> Result<ParsedBookmarks, BookmarkHwpxError> {
    if source.is_empty()
        || source.len() > limits.0.section_bytes
        || expected.sections().len() != 1
        || expected.bookmarks().len() > limits.0.bookmarks
    {
        return Err(BookmarkHwpxError::InputLimit);
    }
    let _ = expected.canonical_sha256(state_limits)?;
    let document = PreservingXmlDocument::parse(source)?;
    if document.elements().len() > limits.0.elements {
        return Err(BookmarkHwpxError::InputLimit);
    }
    let mut root = None;
    for (index, candidate) in document.elements().iter().enumerate() {
        if candidate.parent().is_none() && root.replace(index).is_some() {
            return Err(BookmarkHwpxError::UnsupportedStructure);
        }
    }
    let root = root.ok_or(BookmarkHwpxError::UnsupportedStructure)?;
    if !has_name(element(&document, root)?, "sec") {
        return Err(BookmarkHwpxError::UnsupportedStructure);
    }
    let mut paragraphs = Vec::new();
    for (index, candidate) in document.elements().iter().enumerate() {
        if !has_name(candidate, "p") {
            continue;
        }
        if paragraphs.len() >= limits.0.paragraphs {
            return Err(BookmarkHwpxError::InputLimit);
        }
        paragraphs
            .try_reserve(1)
            .map_err(|_| BookmarkHwpxError::AllocationFailed)?;
        paragraphs.push(index);
    }
    if usize::try_from(expected.sections()[0].paragraph_count).ok() != Some(paragraphs.len()) {
        return Err(BookmarkHwpxError::ProjectionMismatch);
    }

    let mut projections = Vec::new();
    for (root, bookmark_element) in document.elements().iter().enumerate() {
        if !has_name(bookmark_element, "bookmark") {
            continue;
        }
        if projections.len() >= limits.0.bookmarks {
            return Err(BookmarkHwpxError::InputLimit);
        }
        let projection = bookmark_projection(source, &document, &paragraphs, root, limits)?;
        projections
            .try_reserve(1)
            .map_err(|_| BookmarkHwpxError::AllocationFailed)?;
        projections.push(projection);
    }
    if projections.len() != expected.bookmarks().len() {
        return Err(BookmarkHwpxError::ProjectionMismatch);
    }
    for (projection, bookmark) in projections.iter().zip(expected.bookmarks()) {
        ensure_point_bookmark(bookmark)?;
        let root = element(&document, projection.root)?;
        let name = decoded_attribute(source, strict_attribute(root, "name")?, limits)?;
        if name != bookmark.name
            || bookmark.anchor.section_id != expected.sections()[0].section_id
            || bookmark.anchor.start != projection.anchor
            || bookmark.anchor.end != projection.anchor
        {
            return Err(BookmarkHwpxError::ProjectionMismatch);
        }
    }
    document.verify_untouched_round_trip()?;
    Ok(ParsedBookmarks {
        document,
        paragraphs,
        projections,
    })
}

/// Source-only point marker envelope using the original exact projection.
/// No native paragraph ordinal, name normalization or jump authority is exposed.
pub(crate) struct ImportedBookmarkEnvelope {
    pub name: String,
    pub wrapper_element: usize,
    pub paragraph_element: usize,
    pub source_run_ordinal: u32,
    pub source_inline_ordinal: u32,
}

pub(crate) fn read_imported_point_bookmark(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<ImportedBookmarkEnvelope, BookmarkHwpxError> {
    let marker = element(document, index)?;
    if !has_name(marker, "bookmark") {
        return Err(BookmarkHwpxError::InvalidBookmark);
    }
    let wrapper = marker.parent().ok_or(BookmarkHwpxError::InvalidBookmark)?;
    let run = element(document, wrapper)?
        .parent()
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
    let paragraph = element(document, run)?
        .parent()
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
    let limits = BookmarkHwpxLimits::new(BookmarkHwpxLimitConfig::default())?;
    let projection = document.with_source_bytes(|source| {
        bookmark_projection(source, document, &[paragraph], index, limits)
    })?;
    let name = document.with_source_bytes(|source| {
        decoded_attribute(source, strict_attribute(marker, "name")?, limits)
    })?;
    Ok(ImportedBookmarkEnvelope {
        name,
        wrapper_element: projection.wrapper,
        paragraph_element: paragraph,
        source_run_ordinal: projection.anchor.run_ordinal,
        source_inline_ordinal: projection.anchor.inline_ordinal,
    })
}

fn bookmark_projection(
    source: &[u8],
    document: &PreservingXmlDocument,
    paragraphs: &[usize],
    root: usize,
    limits: BookmarkHwpxLimits,
) -> Result<BookmarkProjection, BookmarkHwpxError> {
    let bookmark = element(document, root)?;
    if !bookmark.is_empty()
        || bookmark.first_child().is_some()
        || non_namespace_attributes(bookmark)? != vec!["name"]
    {
        return Err(BookmarkHwpxError::InvalidBookmark);
    }
    let name = decoded_attribute(source, strict_attribute(bookmark, "name")?, limits)?;
    if name.is_empty() {
        return Err(BookmarkHwpxError::InvalidBookmark);
    }
    let wrapper = bookmark
        .parent()
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
    let wrapper_element = element(document, wrapper)?;
    if !has_name(wrapper_element, "ctrl")
        || !non_namespace_attributes(wrapper_element)?.is_empty()
        || direct_element_children(document, wrapper)? != vec![root]
    {
        return Err(BookmarkHwpxError::InvalidBookmark);
    }
    require_whitespace_around_child(source, wrapper_element, bookmark)?;
    let run = wrapper_element
        .parent()
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
    let run_element = element(document, run)?;
    if !has_name(run_element, "run") {
        return Err(BookmarkHwpxError::InvalidBookmark);
    }
    let paragraph = run_element
        .parent()
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
    if !has_name(element(document, paragraph)?, "p") {
        return Err(BookmarkHwpxError::InvalidBookmark);
    }
    let paragraph_ordinal = paragraphs
        .iter()
        .position(|value| *value == paragraph)
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
    let runs = direct_children_named(document, paragraph, "run", limits.0.runs_per_paragraph)?;
    let run_ordinal = runs
        .iter()
        .position(|value| *value == run)
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
    let children =
        direct_element_children_bounded(document, run, limits.0.inline_elements_per_run)?;
    let wrapper_position = children
        .iter()
        .position(|value| *value == wrapper)
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
    let inline_ordinal = children[..wrapper_position]
        .iter()
        .filter(|&&child| !is_bookmark_wrapper(document, child))
        .count();
    let anchor = LinkPoint {
        paragraph_ordinal: u32::try_from(paragraph_ordinal)
            .map_err(|_| BookmarkHwpxError::InputLimit)?,
        run_ordinal: u32::try_from(run_ordinal).map_err(|_| BookmarkHwpxError::InputLimit)?,
        inline_ordinal: u32::try_from(inline_ordinal).map_err(|_| BookmarkHwpxError::InputLimit)?,
    };
    let wrapper_sha256 = digest_span(source, outer_span(wrapper_element)?)?;
    Ok(BookmarkProjection {
        root,
        wrapper,
        anchor,
        wrapper_sha256,
    })
}

struct ByteEdit {
    start: usize,
    end: usize,
    replacement: Vec<u8>,
}

fn build_edit(
    source: &[u8],
    parsed: &ParsedBookmarks,
    transition: &BookmarkTransition,
    target: &LinkReferenceDocumentState,
    limits: BookmarkHwpxLimits,
) -> Result<ByteEdit, BookmarkHwpxError> {
    match transition {
        BookmarkTransition::Delete { index, bookmark } => {
            let projection = parsed
                .projections
                .get(*index)
                .ok_or(BookmarkHwpxError::ProjectionMismatch)?;
            if projection.anchor != bookmark.anchor.start {
                return Err(BookmarkHwpxError::ProjectionMismatch);
            }
            let span = outer_span(element(&parsed.document, projection.wrapper)?)?;
            Ok(ByteEdit {
                start: span.start(),
                end: span.end(),
                replacement: Vec::new(),
            })
        }
        BookmarkTransition::Insert { index, bookmark } => {
            if bookmark.anchor.section_id != target.sections()[0].section_id {
                return Err(BookmarkHwpxError::ProjectionMismatch);
            }
            let paragraph = *parsed
                .paragraphs
                .get(
                    usize::try_from(bookmark.anchor.start.paragraph_ordinal)
                        .map_err(|_| BookmarkHwpxError::NonRepresentable)?,
                )
                .ok_or(BookmarkHwpxError::NonRepresentable)?;
            let runs = direct_children_named(
                &parsed.document,
                paragraph,
                "run",
                limits.0.runs_per_paragraph,
            )?;
            let run = *runs
                .get(
                    usize::try_from(bookmark.anchor.start.run_ordinal)
                        .map_err(|_| BookmarkHwpxError::NonRepresentable)?,
                )
                .ok_or(BookmarkHwpxError::NonRepresentable)?;
            let offset = insertion_offset(parsed, run, bookmark.anchor.start, *index, limits)?;
            let prefix = element_prefix(source, element(&parsed.document, run)?)?;
            let escaped = escape_attribute(&bookmark.name, limits)?;
            let replacement =
                format!("<{prefix}ctrl><{prefix}bookmark name=\"{escaped}\"/></{prefix}ctrl>")
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
    parsed: &ParsedBookmarks,
    run: usize,
    anchor: LinkPoint,
    target_index: usize,
    limits: BookmarkHwpxLimits,
) -> Result<usize, BookmarkHwpxError> {
    let children =
        direct_element_children_bounded(&parsed.document, run, limits.0.inline_elements_per_run)?;
    let wanted =
        usize::try_from(anchor.inline_ordinal).map_err(|_| BookmarkHwpxError::NonRepresentable)?;
    let mut non_bookmark = 0_usize;
    let mut after_same_boundary = None;
    for child in children {
        if let Some(source_index) = parsed
            .projections
            .iter()
            .position(|projection| projection.wrapper == child)
        {
            let projection = &parsed.projections[source_index];
            if projection.anchor.paragraph_ordinal == anchor.paragraph_ordinal
                && projection.anchor.run_ordinal == anchor.run_ordinal
                && projection.anchor.inline_ordinal == anchor.inline_ordinal
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
        if is_bookmark_wrapper(&parsed.document, child) {
            return Err(BookmarkHwpxError::ProjectionMismatch);
        }
        if non_bookmark == wanted {
            return Ok(after_same_boundary
                .unwrap_or(element(&parsed.document, child)?.start_tag_span().start()));
        }
        non_bookmark = non_bookmark
            .checked_add(1)
            .ok_or(BookmarkHwpxError::InputLimit)?;
    }
    if non_bookmark != wanted {
        return Err(BookmarkHwpxError::NonRepresentable);
    }
    if let Some(offset) = after_same_boundary {
        return Ok(offset);
    }
    element(&parsed.document, run)?
        .end_tag_span()
        .map(XmlByteSpan::start)
        .ok_or(BookmarkHwpxError::UnsupportedStructure)
}

fn apply_edit(
    source: &[u8],
    edit: &ByteEdit,
    limits: BookmarkHwpxLimits,
) -> Result<Vec<u8>, BookmarkHwpxError> {
    if edit.start > edit.end || edit.end > source.len() {
        return Err(BookmarkHwpxError::PreservationMismatch);
    }
    let output_len = source
        .len()
        .checked_sub(edit.end - edit.start)
        .and_then(|value| value.checked_add(edit.replacement.len()))
        .ok_or(BookmarkHwpxError::OutputLimit)?;
    if output_len > limits.0.output_bytes {
        return Err(BookmarkHwpxError::OutputLimit);
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| BookmarkHwpxError::AllocationFailed)?;
    output.extend_from_slice(&source[..edit.start]);
    output.extend_from_slice(&edit.replacement);
    output.extend_from_slice(&source[edit.end..]);
    if output.len() != output_len {
        return Err(BookmarkHwpxError::OutputLimit);
    }
    Ok(output)
}

fn verify_preservation(
    source: &[u8],
    output: &[u8],
    edit: &ByteEdit,
) -> Result<(), BookmarkHwpxError> {
    let suffix_start = edit
        .start
        .checked_add(edit.replacement.len())
        .ok_or(BookmarkHwpxError::PreservationMismatch)?;
    if output.get(..edit.start) != source.get(..edit.start)
        || output.get(edit.start..suffix_start) != Some(edit.replacement.as_slice())
        || output.get(suffix_start..) != source.get(edit.end..)
    {
        return Err(BookmarkHwpxError::PreservationMismatch);
    }
    Ok(())
}

fn validate_plan(
    plan: &BookmarkHwpxPlan,
    state_limits: LinkReferenceLimits,
    limits: BookmarkHwpxLimits,
) -> Result<(), BookmarkHwpxError> {
    if plan.schema_version != "hwpx-agent.bookmark-hwpx-plan/v1"
        || plan.profile_id != BOOKMARK_HWPX_PROFILE_ID
        || !matches!(
            plan.domain_plan.capability_id(),
            "ref.bookmark_insert" | "ref.bookmark_delete"
        )
        || plan.source_document_flow_sha256 != plan.domain_plan.source_document_flow_sha256()
        || plan.source_state_sha256 != plan.domain_plan.source_state_sha256()
        || plan.source_state.canonical_sha256(state_limits)? != plan.source_state_sha256
        || plan_binding_sha256(plan, limits)? != plan.plan_sha256
    {
        return Err(BookmarkHwpxError::PlanTampered);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &BookmarkHwpxPlan,
    limits: BookmarkHwpxLimits,
) -> Result<String, BookmarkHwpxError> {
    let mut unsigned = plan.clone();
    unsigned.plan_sha256.clear();
    Ok(hex(
        Sha256::digest(serialize_bounded(&unsigned, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: BookmarkHwpxLimits,
) -> Result<Vec<u8>, BookmarkHwpxError> {
    let bytes = serde_json::to_vec(value).map_err(|_| BookmarkHwpxError::PlanTampered)?;
    if bytes.len() > limits.0.plan_bytes {
        return Err(BookmarkHwpxError::OutputLimit);
    }
    Ok(bytes)
}

fn direct_element_children(
    document: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, BookmarkHwpxError> {
    direct_element_children_bounded(document, parent, usize::MAX)
}

fn direct_element_children_bounded(
    document: &PreservingXmlDocument,
    parent: usize,
    maximum: usize,
) -> Result<Vec<usize>, BookmarkHwpxError> {
    let mut children = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        if children.len() >= maximum {
            return Err(BookmarkHwpxError::InputLimit);
        }
        children
            .try_reserve(1)
            .map_err(|_| BookmarkHwpxError::AllocationFailed)?;
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
) -> Result<Vec<usize>, BookmarkHwpxError> {
    let mut matches = Vec::new();
    let mut child = element(document, parent)?.first_child();
    while let Some(index) = child {
        if has_name(element(document, index)?, local_name) {
            if matches.len() >= maximum {
                return Err(BookmarkHwpxError::InputLimit);
            }
            matches
                .try_reserve(1)
                .map_err(|_| BookmarkHwpxError::AllocationFailed)?;
            matches.push(index);
        }
        child = element(document, index)?.next_sibling();
    }
    Ok(matches)
}

fn is_bookmark_wrapper(document: &PreservingXmlDocument, index: usize) -> bool {
    element(document, index).is_ok_and(|value| has_name(value, "ctrl"))
        && direct_element_children(document, index).is_ok_and(|children| {
            children.len() == 1
                && element(document, children[0]).is_ok_and(|value| has_name(value, "bookmark"))
        })
}

fn require_whitespace_around_child(
    source: &[u8],
    parent: &XmlElementToken,
    child: &XmlElementToken,
) -> Result<(), BookmarkHwpxError> {
    let content = parent
        .content_span()
        .ok_or(BookmarkHwpxError::InvalidBookmark)?;
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
        return Err(BookmarkHwpxError::InvalidBookmark);
    }
    Ok(())
}

fn non_namespace_attributes(element: &XmlElementToken) -> Result<Vec<&str>, BookmarkHwpxError> {
    let mut names = Vec::new();
    for attribute in element
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
    {
        if attribute.name().namespace().is_some() || names.contains(&attribute.name().local_name())
        {
            return Err(BookmarkHwpxError::InvalidBookmark);
        }
        names
            .try_reserve(1)
            .map_err(|_| BookmarkHwpxError::AllocationFailed)?;
        names.push(attribute.name().local_name());
    }
    names.sort_unstable();
    Ok(names)
}

fn strict_attribute<'a>(
    element: &'a XmlElementToken,
    name: &str,
) -> Result<&'a XmlAttributeToken, BookmarkHwpxError> {
    let mut matches = element.attributes().iter().filter(|attribute| {
        !attribute.is_namespace_declaration() && attribute.name().local_name() == name
    });
    let value = matches.next().ok_or(BookmarkHwpxError::InvalidBookmark)?;
    if value.name().namespace().is_some() || matches.next().is_some() {
        return Err(BookmarkHwpxError::InvalidBookmark);
    }
    Ok(value)
}

fn decoded_attribute(
    source: &[u8],
    attribute: &XmlAttributeToken,
    limits: BookmarkHwpxLimits,
) -> Result<String, BookmarkHwpxError> {
    let lexical = std::str::from_utf8(
        source
            .get(attribute.value_span().start()..attribute.value_span().end())
            .ok_or(BookmarkHwpxError::InvalidBookmark)?,
    )
    .map_err(|_| BookmarkHwpxError::InvalidBookmark)?;
    if lexical.len() > limits.0.name_bytes {
        return Err(BookmarkHwpxError::InputLimit);
    }
    let value = unescape(lexical).map_err(|_| BookmarkHwpxError::InvalidBookmark)?;
    if value.len() > limits.0.name_bytes || value.chars().any(invalid_xml_character) {
        return Err(BookmarkHwpxError::InputLimit);
    }
    Ok(value.into_owned())
}

fn escape_attribute(value: &str, limits: BookmarkHwpxLimits) -> Result<String, BookmarkHwpxError> {
    if value.is_empty()
        || value.len() > limits.0.name_bytes
        || value.chars().any(invalid_xml_character)
    {
        return Err(BookmarkHwpxError::OutputLimit);
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

fn element_prefix(source: &[u8], element: &XmlElementToken) -> Result<String, BookmarkHwpxError> {
    let name = std::str::from_utf8(
        source
            .get(element.start_name_span().start()..element.start_name_span().end())
            .ok_or(BookmarkHwpxError::UnsupportedStructure)?,
    )
    .map_err(|_| BookmarkHwpxError::UnsupportedStructure)?;
    let Some((prefix, local)) = name.rsplit_once(':') else {
        if name != "run" {
            return Err(BookmarkHwpxError::UnsupportedStructure);
        }
        return Ok(String::new());
    };
    if local != "run"
        || prefix.is_empty()
        || !prefix
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
    {
        return Err(BookmarkHwpxError::UnsupportedStructure);
    }
    Ok(format!("{prefix}:"))
}

fn has_name(element: &XmlElementToken, local_name: &str) -> bool {
    element.name().namespace() == Some(PARAGRAPH_NS) && element.name().local_name() == local_name
}

fn element(
    document: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, BookmarkHwpxError> {
    document
        .elements()
        .get(index)
        .ok_or(BookmarkHwpxError::UnsupportedStructure)
}

fn outer_span(element: &XmlElementToken) -> Result<XmlByteSpan, BookmarkHwpxError> {
    element
        .outer_span()
        .ok_or(BookmarkHwpxError::UnsupportedStructure)
}

fn digest_span(source: &[u8], span: XmlByteSpan) -> Result<[u8; 32], BookmarkHwpxError> {
    Ok(Sha256::digest(
        source
            .get(span.start()..span.end())
            .ok_or(BookmarkHwpxError::UnsupportedStructure)?,
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
    #![allow(clippy::expect_used, clippy::too_many_lines)] // Exact fixture construction stays local.

    use super::*;
    use domain_ir::{
        BookmarkIdentity, ExternalLinkPolicy, LINK_REFERENCE_SCHEMA_VERSION, LinkAnchor,
        LinkReferenceDocumentStateDraft, LinkReferenceLimitConfig, LinkReferenceOperation,
        LinkReferenceRequest, LinkReferenceRequestDraft, LinkReferenceSectionState, LogicalId,
    };

    const A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
    const C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";

    fn logical_id(value: &str) -> LogicalId {
        LogicalId::parse(value).expect("logical id")
    }

    fn sealed_plan() -> BookmarkHwpxPlan {
        let state_limits =
            LinkReferenceLimits::new(LinkReferenceLimitConfig::default()).expect("state limits");
        let source_state = LinkReferenceDocumentState::from_draft(
            LinkReferenceDocumentStateDraft {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
                sections: vec![LinkReferenceSectionState {
                    section_id: logical_id("section-1"),
                    paragraph_count: 1,
                    run_topology_sha256: A.to_owned(),
                    inline_topology_sha256: B.to_owned(),
                    opaque_section_state_sha256: C.to_owned(),
                    locked: false,
                }],
                bookmarks: Vec::new(),
                hyperlinks: Vec::new(),
                occupied_non_hyperlink_begin_control_ids: Vec::new(),
                occupied_non_hyperlink_field_ids: Vec::new(),
                external_link_policy: ExternalLinkPolicy {
                    allow_https: false,
                    allow_mailto: false,
                    allow_managed_documents: false,
                    approvals: Vec::new(),
                    policy_revision_sha256: A.to_owned(),
                },
                non_reference_content_sha256: A.to_owned(),
                unrelated_field_inventory_sha256: B.to_owned(),
                style_catalog_sha256: C.to_owned(),
                object_inventory_sha256: A.to_owned(),
                relationship_inventory_sha256: B.to_owned(),
                resource_inventory_sha256: C.to_owned(),
                document_protection_sha256: A.to_owned(),
                opaque_document_state_sha256: B.to_owned(),
                document_locked: false,
            },
            state_limits,
        )
        .expect("source state");
        let point = LinkPoint {
            paragraph_ordinal: 0,
            run_ordinal: 0,
            inline_ordinal: 1,
        };
        let request = LinkReferenceRequest::from_draft(
            LinkReferenceRequestDraft {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
                request_id: logical_id("request-bookmark"),
                expected_source_state_sha256: source_state
                    .canonical_sha256(state_limits)
                    .expect("state digest"),
                expected_document_flow_sha256: A.to_owned(),
                target_document_flow_sha256: B.to_owned(),
                operation: LinkReferenceOperation::InsertBookmark {
                    insertion_index: 0,
                    bookmark: BookmarkEntry {
                        identity: BookmarkIdentity {
                            logical_bookmark_id: logical_id("bookmark-1"),
                        },
                        name: "point".to_owned(),
                        anchor: LinkAnchor {
                            section_id: logical_id("section-1"),
                            start: point,
                            end: point,
                        },
                        native_tag: BookmarkNativeTag::Bookmark,
                        opaque_native_payload_sha256: EMPTY_SHA256.to_owned(),
                        opaque_properties: Vec::new(),
                        locked: false,
                    },
                },
            },
            &source_state,
            A,
            state_limits,
        )
        .expect("request");
        let domain = LinkReferenceBuilder::plan(&source_state, &request, A, state_limits)
            .expect("domain plan");
        let source = b"<hp:sec xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\"><hp:p><hp:run><hp:t>A</hp:t></hp:run></hp:p></hp:sec>";
        BookmarkHwpxBuilder::plan(
            source,
            &source_state,
            &domain,
            A,
            state_limits,
            BookmarkHwpxLimits::new(BookmarkHwpxLimitConfig::default()).expect("HWPX limits"),
        )
        .expect("HWPX plan")
    }

    #[test]
    fn tampered_private_plan_binding_is_rejected() {
        let mut plan = sealed_plan();
        plan.profile_id = "tampered-profile";
        assert_eq!(
            validate_plan(
                &plan,
                LinkReferenceLimits::new(LinkReferenceLimitConfig::default())
                    .expect("state limits"),
                BookmarkHwpxLimits::new(BookmarkHwpxLimitConfig::default()).expect("HWPX limits"),
            ),
            Err(BookmarkHwpxError::PlanTampered)
        );
    }
}
