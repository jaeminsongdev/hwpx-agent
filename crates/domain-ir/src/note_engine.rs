use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::LogicalId;

pub const NOTE_ENGINE_SCHEMA_VERSION: &str = "hwpx-agent.note-engine/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NoteLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub sections: usize,
    pub notes: usize,
    pub selection: usize,
    pub text_bytes: usize,
    pub opaque_entries: usize,
}

impl Default for NoteLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            sections: 4096,
            notes: 65_536,
            selection: 65_536,
            text_bytes: 64 * 1024,
            opaque_entries: 4096,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct NoteLimits(NoteLimitConfig);

impl NoteLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_SECTIONS: usize = 65_536;
    pub const HARD_MAX_NOTES: usize = 1_000_000;
    pub const HARD_MAX_SELECTION: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 65_536;

    /// Creates finite note-engine limits without silently clamping values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: NoteLimitConfig) -> Result<Self, NoteError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.sections == 0
            || config.sections > Self::HARD_MAX_SECTIONS
            || config.notes == 0
            || config.notes > Self::HARD_MAX_NOTES
            || config.selection == 0
            || config.selection > Self::HARD_MAX_SELECTION
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
        {
            return Err(NoteError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> NoteLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NoteKind {
    Footnote,
    Endnote,
}

impl NoteKind {
    #[must_use]
    pub const fn insert_capability_id(self) -> &'static str {
        match self {
            Self::Footnote => "ref.footnote_insert",
            Self::Endnote => "ref.endnote_insert",
        }
    }

    const fn native_tag(self) -> NoteNativeTag {
        match self {
            Self::Footnote => NoteNativeTag::FootNote,
            Self::Endnote => NoteNativeTag::EndNote,
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NoteNativeTag {
    FootNote,
    EndNote,
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteIdentity {
    pub logical_note_id: LogicalId,
    pub native_instance_id: u32,
}

impl fmt::Debug for NoteIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NoteIdentity(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteAnchor {
    pub section_id: LogicalId,
    pub paragraph_id: LogicalId,
    pub run_ordinal: u32,
    pub inline_ordinal: u32,
}

impl fmt::Debug for NoteAnchor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NoteAnchor(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteMarkerProperties {
    pub flags: u32,
    pub number: u16,
    pub user_character: Option<String>,
    pub prefix_character: Option<String>,
    pub suffix_character: Option<String>,
}

impl fmt::Debug for NoteMarkerProperties {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NoteMarkerProperties(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OpaqueNoteProperty {
    pub namespace: String,
    pub name: String,
    pub value_sha256: String,
}

impl fmt::Debug for OpaqueNoteProperty {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("OpaqueNoteProperty(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteEntry {
    pub identity: NoteIdentity,
    pub anchor: NoteAnchor,
    pub kind: NoteKind,
    pub native_tag: NoteNativeTag,
    pub marker: NoteMarkerProperties,
    pub body_graph_sha256: String,
    pub plain_text_sha256: Option<String>,
    pub marker_style_sha256: String,
    pub body_style_sha256: String,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueNoteProperty>,
    pub locked: bool,
}

impl fmt::Debug for NoteEntry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteEntry")
            .field("kind", &self.kind)
            .field("locked", &self.locked)
            .field("payload", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NoteNumberFormat {
    Digit,
    CircledDigit,
    RomanCapital,
    RomanSmall,
    LatinCapital,
    LatinSmall,
    CircledLatinCapital,
    CircledLatinSmall,
    HangulSyllable,
    CircledHangulSyllable,
    HangulJamo,
    CircledHangulJamo,
    HangulPhonetic,
    Ideograph,
    CircledIdeograph,
    DecagonCircle,
    DecagonCircleHanja,
    Symbol,
    UserChar,
    Symbol2,
    Image,
    TwoDigit,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteAutoNumberFormat {
    pub format: NoteNumberFormat,
    pub user_character: String,
    pub prefix_character: String,
    pub suffix_character: String,
    pub superscript: bool,
}

impl fmt::Debug for NoteAutoNumberFormat {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NoteAutoNumberFormat(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NoteLineType {
    None,
    Solid,
    Dot,
    Dash,
    DashDot,
    DashDotDot,
    LongDash,
    Circle,
    DoubleSlim,
    SlimThick,
    ThickSlim,
    SlimThickSlim,
    Wave,
    DoubleWave,
    Thick3d,
    ThickReverse3d,
    ThreeDimensional,
    Reverse3d,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NoteLineWidth {
    Mm0_1,
    Mm0_12,
    Mm0_15,
    Mm0_2,
    Mm0_25,
    Mm0_3,
    Mm0_4,
    Mm0_5,
    Mm0_6,
    Mm0_7,
    Mm1_0,
    Mm1_5,
    Mm2_0,
    Mm3_0,
    Mm4_0,
    Mm5_0,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteLineStyle {
    pub length_hwp_units: i32,
    pub line_type: NoteLineType,
    pub width: NoteLineWidth,
    pub color_rgb: u32,
}

impl fmt::Debug for NoteLineStyle {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NoteLineStyle(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteSpacing {
    pub between_notes_hwp_units: u32,
    pub below_line_hwp_units: u32,
    pub above_line_hwp_units: u32,
}

impl fmt::Debug for NoteSpacing {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NoteSpacing(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NoteNumberingRestart {
    Continuous,
    PerSection,
    PerPage,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NotePlacement {
    EachColumn,
    MergedColumn,
    RightMostColumn,
    EndOfDocument,
    EndOfSection,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteStyle {
    pub kind: NoteKind,
    pub auto_number_format: NoteAutoNumberFormat,
    pub note_line: NoteLineStyle,
    pub spacing: NoteSpacing,
    pub numbering_restart: NoteNumberingRestart,
    pub new_number: u32,
    pub placement: NotePlacement,
    pub beneath_text: bool,
    pub opaque_style_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for NoteStyle {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteStyle")
            .field("kind", &self.kind)
            .field("locked", &self.locked)
            .field("style", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteSectionState {
    pub section_id: LogicalId,
    pub footnote_style: NoteStyle,
    pub endnote_style: NoteStyle,
    pub opaque_section_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for NoteSectionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteSectionState")
            .field("locked", &self.locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteDocumentStateDraft {
    pub schema_version: String,
    pub sections: Vec<NoteSectionState>,
    pub notes: Vec<NoteEntry>,
    pub non_note_content_sha256: String,
    pub style_catalog_sha256: String,
    pub numbering_inventory_sha256: String,
    pub reference_inventory_sha256: String,
    pub resource_inventory_sha256: String,
    pub document_protection_sha256: String,
    pub opaque_document_state_sha256: String,
    pub document_locked: bool,
}

impl fmt::Debug for NoteDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NoteDocumentStateDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NoteDocumentState {
    schema_version: &'static str,
    sections: Vec<NoteSectionState>,
    notes: Vec<NoteEntry>,
    non_note_content_sha256: String,
    style_catalog_sha256: String,
    numbering_inventory_sha256: String,
    reference_inventory_sha256: String,
    resource_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
    document_locked: bool,
}

impl NoteDocumentState {
    /// Validates and seals complete ordered section and note state.
    ///
    /// # Errors
    ///
    /// Rejects version, identity, native-shape, style, protection, digest, or limit failures.
    pub fn from_draft(
        draft: NoteDocumentStateDraft,
        limits: NoteLimits,
    ) -> Result<Self, NoteError> {
        if draft.schema_version != NOTE_ENGINE_SCHEMA_VERSION {
            return Err(NoteError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION,
            sections: draft.sections,
            notes: draft.notes,
            non_note_content_sha256: draft.non_note_content_sha256,
            style_catalog_sha256: draft.style_catalog_sha256,
            numbering_inventory_sha256: draft.numbering_inventory_sha256,
            reference_inventory_sha256: draft.reference_inventory_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            document_protection_sha256: draft.document_protection_sha256,
            opaque_document_state_sha256: draft.opaque_document_state_sha256,
            document_locked: draft.document_locked,
        };
        validate_document_state(&state, limits)?;
        let _ = state.canonical_json(limits)?;
        Ok(state)
    }

    #[must_use]
    pub fn sections(&self) -> &[NoteSectionState] {
        &self.sections
    }

    #[must_use]
    pub fn notes(&self) -> &[NoteEntry] {
        &self.notes
    }

    /// Serializes the complete state deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: NoteLimits) -> Result<Vec<u8>, NoteError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical note state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_sha256(&self, limits: NoteLimits) -> Result<String, NoteError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for NoteDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteDocumentState")
            .field("section_count", &self.sections.len())
            .field("note_count", &self.notes.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum NoteExportSelection {
    All,
    Exact { notes: Vec<NoteIdentity> },
}

impl fmt::Debug for NoteExportSelection {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let kind = match self {
            Self::All => "all",
            Self::Exact { .. } => "exact",
        };
        formatter
            .debug_struct("NoteExportSelection")
            .field("kind", &kind)
            .field("selection", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NoteExportFormat {
    DigestManifestV1,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum NoteOperation {
    Insert {
        insertion_index: usize,
        note: NoteEntry,
    },
    ReplaceStyle {
        section_id: LogicalId,
        note_kind: NoteKind,
        style: NoteStyle,
    },
    Convert {
        target: NoteIdentity,
        target_kind: NoteKind,
    },
    PrepareExport {
        selection: NoteExportSelection,
        format: NoteExportFormat,
    },
}

impl NoteOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::Insert { note, .. } => note.kind.insert_capability_id(),
            Self::ReplaceStyle { .. } => "ref.note_style",
            Self::Convert { .. } => "ref.note_convert",
            Self::PrepareExport { .. } => "ref.note_export",
        }
    }

    const fn mutates_document(&self) -> bool {
        !matches!(self, Self::PrepareExport { .. })
    }
}

impl fmt::Debug for NoteOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NoteRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: NoteOperation,
}

impl fmt::Debug for NoteRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NoteRequestDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NoteRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: NoteOperation,
}

impl NoteRequest {
    /// Validates an exact note transition against current state and document flow.
    ///
    /// # Errors
    ///
    /// Rejects schema, state, flow, operation, protection, selection, or limit failures.
    pub fn from_draft(
        draft: NoteRequestDraft,
        current: &NoteDocumentState,
        current_document_flow_sha256: &str,
        limits: NoteLimits,
    ) -> Result<Self, NoteError> {
        if draft.schema_version != NOTE_ENGINE_SCHEMA_VERSION {
            return Err(NoteError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        require_digest(current_document_flow_sha256)?;
        if current.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(NoteError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(NoteError::DocumentFlowDrift);
        }
        if !draft.operation.mutates_document()
            && draft.target_document_flow_sha256 != draft.expected_document_flow_sha256
        {
            return Err(NoteError::DocumentFlowDrift);
        }
        let _ = apply_operation(current, &draft.operation, limits)?;
        let request = Self {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = request.canonical_json(limits)?;
        Ok(request)
    }

    /// Parses strict, bounded, duplicate-key-free request JSON.
    ///
    /// # Errors
    ///
    /// Rejects malformed, duplicated, unknown, oversized, stale, or invalid input.
    pub fn from_json(
        bytes: &[u8],
        current: &NoteDocumentState,
        current_document_flow_sha256: &str,
        limits: NoteLimits,
    ) -> Result<Self, NoteError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(NoteError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft = serde_json::from_slice(bytes).map_err(|_| NoteError::InvalidJson)?;
        Self::from_draft(draft, current, current_document_flow_sha256, limits)
    }

    #[must_use]
    pub fn operation(&self) -> &NoteOperation {
        &self.operation
    }

    /// Serializes the request deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: NoteLimits) -> Result<Vec<u8>, NoteError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for NoteRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NoteExportEntry {
    document_ordinal: usize,
    identity: NoteIdentity,
    kind: NoteKind,
    body_graph_sha256: String,
    plain_text_sha256: Option<String>,
}

impl NoteExportEntry {
    #[must_use]
    pub const fn document_ordinal(&self) -> usize {
        self.document_ordinal
    }

    #[must_use]
    pub const fn identity(&self) -> &NoteIdentity {
        &self.identity
    }

    #[must_use]
    pub const fn kind(&self) -> NoteKind {
        self.kind
    }

    #[must_use]
    pub fn body_graph_sha256(&self) -> &str {
        &self.body_graph_sha256
    }

    #[must_use]
    pub fn plain_text_sha256(&self) -> Option<&str> {
        self.plain_text_sha256.as_deref()
    }
}

impl fmt::Debug for NoteExportEntry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteExportEntry")
            .field("kind", &self.kind)
            .field("entry", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NoteExportManifest {
    schema_version: &'static str,
    format: NoteExportFormat,
    entries: Vec<NoteExportEntry>,
}

impl NoteExportManifest {
    #[must_use]
    pub fn entries(&self) -> &[NoteExportEntry] {
        &self.entries
    }

    /// Serializes the digest-only export manifest deterministically.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: NoteLimits) -> Result<Vec<u8>, NoteError> {
        serialize_bounded(self, limits)
    }

    /// Returns the manifest SHA-256.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_sha256(&self, limits: NoteLimits) -> Result<String, NoteError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for NoteExportManifest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteExportManifest")
            .field("entry_count", &self.entries.len())
            .field("entries", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NotePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state: NoteDocumentState,
    source_state_sha256: String,
    target_state: NoteDocumentState,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: NoteOperation,
    export_manifest: Option<NoteExportManifest>,
    export_manifest_sha256: Option<String>,
    plan_sha256: String,
}

impl NotePlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn target_state(&self) -> &NoteDocumentState {
        &self.target_state
    }

    #[must_use]
    pub const fn export_manifest(&self) -> Option<&NoteExportManifest> {
        self.export_manifest.as_ref()
    }

    #[must_use]
    pub fn plan_sha256(&self) -> &str {
        &self.plan_sha256
    }

    /// Serializes the sealed plan deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(&self, limits: NoteLimits) -> Result<Vec<u8>, NoteError> {
        serialize_bounded(self, limits)
    }
}

impl fmt::Debug for NotePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NotePlan")
            .field("capability_id", &self.capability_id)
            .field("has_export_manifest", &self.export_manifest.is_some())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct NoteBuilder;

impl NoteBuilder {
    /// Builds and seals an immutable plan from current state and a validated request.
    ///
    /// # Errors
    ///
    /// Rejects state, flow, operation, protection, selection, or output drift.
    pub fn plan(
        current: &NoteDocumentState,
        request: &NoteRequest,
        current_document_flow_sha256: &str,
        limits: NoteLimits,
    ) -> Result<NotePlan, NoteError> {
        require_digest(current_document_flow_sha256)?;
        let source_state_sha256 = current.canonical_sha256(limits)?;
        if source_state_sha256 != request.expected_source_state_sha256 {
            return Err(NoteError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(NoteError::DocumentFlowDrift);
        }
        let applied = apply_operation(current, &request.operation, limits)?;
        let target_state_sha256 = applied.state.canonical_sha256(limits)?;
        let export_manifest_sha256 = applied
            .export_manifest
            .as_ref()
            .map(|manifest| manifest.canonical_sha256(limits))
            .transpose()?;
        let mut plan = NotePlan {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: request.request_id.clone(),
            source_state: current.clone(),
            source_state_sha256,
            target_state: applied.state,
            target_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            export_manifest: applied.export_manifest,
            export_manifest_sha256,
            plan_sha256: String::new(),
        };
        plan.plan_sha256 = plan_binding_sha256(&plan, limits)?;
        let _ = plan.canonical_json(limits)?;
        Ok(plan)
    }

    /// Revalidates a sealed plan against current state and flow before returning a result.
    ///
    /// # Errors
    ///
    /// Rejects state, flow, plan binding, operation, protection, selection, or output drift.
    pub fn build(
        plan: &NotePlan,
        current: &NoteDocumentState,
        current_document_flow_sha256: &str,
        limits: NoteLimits,
    ) -> Result<NoteResult, NoteError> {
        validate_document_state(current, limits)?;
        if plan.schema_version != NOTE_ENGINE_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan.plan_sha256 != plan_binding_sha256(plan, limits)?
        {
            return Err(NoteError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256
            || current != &plan.source_state
        {
            return Err(NoteError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(NoteError::DocumentFlowDrift);
        }
        let recomputed = apply_operation(&plan.source_state, &plan.operation, limits)?;
        let recomputed_manifest_sha256 = recomputed
            .export_manifest
            .as_ref()
            .map(|manifest| manifest.canonical_sha256(limits))
            .transpose()?;
        if recomputed.state != plan.target_state
            || recomputed.state.canonical_sha256(limits)? != plan.target_state_sha256
            || recomputed.export_manifest != plan.export_manifest
            || recomputed_manifest_sha256 != plan.export_manifest_sha256
        {
            return Err(NoteError::PlanTampered);
        }
        let receipt = NoteReceipt {
            schema_version: NOTE_ENGINE_SCHEMA_VERSION,
            capability_id: plan.capability_id,
            source_state_sha256: plan.source_state_sha256.clone(),
            target_state_sha256: plan.target_state_sha256.clone(),
            source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
            target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
            export_manifest_sha256: plan.export_manifest_sha256.clone(),
            plan_sha256: plan.plan_sha256.clone(),
        };
        let _ = serialize_bounded(&receipt, limits)?;
        Ok(NoteResult {
            state: plan.target_state.clone(),
            export_manifest: plan.export_manifest.clone(),
            receipt,
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct NoteReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    export_manifest_sha256: Option<String>,
    plan_sha256: String,
}

impl fmt::Debug for NoteReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteReceipt")
            .field("capability_id", &self.capability_id)
            .field(
                "has_export_manifest",
                &self.export_manifest_sha256.is_some(),
            )
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct NoteResult {
    pub state: NoteDocumentState,
    pub export_manifest: Option<NoteExportManifest>,
    pub receipt: NoteReceipt,
}

impl fmt::Debug for NoteResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("NoteResult")
            .field("has_export_manifest", &self.export_manifest.is_some())
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum NoteError {
    #[error("note-engine limits are invalid")]
    InvalidLimit,
    #[error("note-engine input exceeds a finite limit")]
    InputLimit,
    #[error("note-engine JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("note-engine schema version is unsupported")]
    UnsupportedVersion,
    #[error("note identity, native identity, anchor, or section identity is invalid")]
    InvalidIdentity,
    #[error("note digest is malformed")]
    InvalidDigest,
    #[error("note marker or opaque property is invalid")]
    InvalidNote,
    #[error("note native tag does not match its semantic kind")]
    InvalidNativeTag,
    #[error("note style is invalid or incompatible with its kind")]
    InvalidStyle,
    #[error("note insertion index is invalid")]
    InvalidInsertionIndex,
    #[error("note or section target does not exist or is ambiguous")]
    TargetNotFound,
    #[error("note export selection is empty, duplicated, excessive, or missing")]
    InvalidExportSelection,
    #[error("note, note style, section, or document is protected")]
    Protected,
    #[error("note operation is a no-op")]
    Noop,
    #[error("note source state drifted")]
    SourceStateDrift,
    #[error("note document flow drifted")]
    DocumentFlowDrift,
    #[error("note plan was tampered with")]
    PlanTampered,
    #[error("note serialization failed")]
    Serialization,
    #[error("note serialized output exceeds a finite limit")]
    OutputLimit,
}

impl NoteError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "note_invalid_limit",
            Self::InputLimit => "note_input_limit",
            Self::InvalidJson => "note_invalid_json",
            Self::UnsupportedVersion => "note_unsupported_version",
            Self::InvalidIdentity => "note_invalid_identity",
            Self::InvalidDigest => "note_invalid_digest",
            Self::InvalidNote => "note_invalid_note",
            Self::InvalidNativeTag => "note_invalid_native_tag",
            Self::InvalidStyle => "note_invalid_style",
            Self::InvalidInsertionIndex => "note_invalid_insertion_index",
            Self::TargetNotFound => "note_target_not_found",
            Self::InvalidExportSelection => "note_invalid_export_selection",
            Self::Protected => "note_protected",
            Self::Noop => "note_noop",
            Self::SourceStateDrift => "note_source_state_drift",
            Self::DocumentFlowDrift => "note_document_flow_drift",
            Self::PlanTampered => "note_plan_tampered",
            Self::Serialization => "note_serialization",
            Self::OutputLimit => "note_output_limit",
        }
    }
}

struct AppliedOperation {
    state: NoteDocumentState,
    export_manifest: Option<NoteExportManifest>,
}

fn apply_operation(
    source: &NoteDocumentState,
    operation: &NoteOperation,
    limits: NoteLimits,
) -> Result<AppliedOperation, NoteError> {
    validate_document_state(source, limits)?;
    if operation.mutates_document() && source.document_locked {
        return Err(NoteError::Protected);
    }
    let mut target = source.clone();
    let export_manifest = match operation {
        NoteOperation::Insert {
            insertion_index,
            note,
        } => {
            if *insertion_index > source.notes.len() {
                return Err(NoteError::InvalidInsertionIndex);
            }
            validate_note(note, limits)?;
            let section_index = exact_section_index(&source.sections, &note.anchor.section_id)?;
            if source.sections[section_index].locked {
                return Err(NoteError::Protected);
            }
            if source.notes.iter().any(|existing| {
                existing.identity.logical_note_id == note.identity.logical_note_id
                    || existing.identity.native_instance_id == note.identity.native_instance_id
                    || existing.anchor == note.anchor
            }) {
                return Err(NoteError::InvalidIdentity);
            }
            target.notes.insert(*insertion_index, note.clone());
            None
        }
        NoteOperation::ReplaceStyle {
            section_id,
            note_kind,
            style,
        } => {
            let section_index = exact_section_index(&target.sections, section_id)?;
            if target.sections[section_index].locked {
                return Err(NoteError::Protected);
            }
            validate_style(style, limits)?;
            if style.kind != *note_kind {
                return Err(NoteError::InvalidStyle);
            }
            let current_style = match note_kind {
                NoteKind::Footnote => &mut target.sections[section_index].footnote_style,
                NoteKind::Endnote => &mut target.sections[section_index].endnote_style,
            };
            if current_style.locked {
                return Err(NoteError::Protected);
            }
            if current_style == style {
                return Err(NoteError::Noop);
            }
            current_style.clone_from(style);
            None
        }
        NoteOperation::Convert {
            target: identity,
            target_kind,
        } => {
            let note_index = exact_note_index(&target.notes, identity)?;
            let section_index = exact_section_index(
                &target.sections,
                &target.notes[note_index].anchor.section_id,
            )?;
            if target.notes[note_index].locked || target.sections[section_index].locked {
                return Err(NoteError::Protected);
            }
            if target.notes[note_index].kind == *target_kind {
                return Err(NoteError::Noop);
            }
            target.notes[note_index].kind = *target_kind;
            target.notes[note_index].native_tag = target_kind.native_tag();
            None
        }
        NoteOperation::PrepareExport { selection, format } => {
            return Ok(AppliedOperation {
                state: target,
                export_manifest: Some(build_export_manifest(source, selection, *format, limits)?),
            });
        }
    };
    validate_document_state(&target, limits)?;
    if &target == source {
        return Err(NoteError::Noop);
    }
    Ok(AppliedOperation {
        state: target,
        export_manifest,
    })
}

fn build_export_manifest(
    source: &NoteDocumentState,
    selection: &NoteExportSelection,
    format: NoteExportFormat,
    limits: NoteLimits,
) -> Result<NoteExportManifest, NoteError> {
    let selected = match selection {
        NoteExportSelection::All => {
            if source.notes.is_empty() || source.notes.len() > limits.0.selection {
                return Err(NoteError::InvalidExportSelection);
            }
            None
        }
        NoteExportSelection::Exact { notes } => {
            if notes.is_empty() || notes.len() > limits.0.selection {
                return Err(NoteError::InvalidExportSelection);
            }
            let mut selected = BTreeSet::new();
            for identity in notes {
                if !selected.insert(identity) || exact_note_index(&source.notes, identity).is_err()
                {
                    return Err(NoteError::InvalidExportSelection);
                }
            }
            Some(selected)
        }
    };
    let entries = source
        .notes
        .iter()
        .enumerate()
        .filter(|(_, note)| {
            selected
                .as_ref()
                .is_none_or(|identities| identities.contains(&note.identity))
        })
        .map(|(document_ordinal, note)| NoteExportEntry {
            document_ordinal,
            identity: note.identity.clone(),
            kind: note.kind,
            body_graph_sha256: note.body_graph_sha256.clone(),
            plain_text_sha256: note.plain_text_sha256.clone(),
        })
        .collect::<Vec<_>>();
    if entries.is_empty() {
        return Err(NoteError::InvalidExportSelection);
    }
    let manifest = NoteExportManifest {
        schema_version: NOTE_ENGINE_SCHEMA_VERSION,
        format,
        entries,
    };
    let _ = manifest.canonical_json(limits)?;
    Ok(manifest)
}

fn exact_note_index(notes: &[NoteEntry], identity: &NoteIdentity) -> Result<usize, NoteError> {
    let mut matches = notes
        .iter()
        .enumerate()
        .filter(|(_, note)| note.identity == *identity)
        .map(|(index, _)| index);
    let index = matches.next().ok_or(NoteError::TargetNotFound)?;
    if matches.next().is_some() {
        return Err(NoteError::TargetNotFound);
    }
    Ok(index)
}

fn exact_section_index(
    sections: &[NoteSectionState],
    identity: &LogicalId,
) -> Result<usize, NoteError> {
    let mut matches = sections
        .iter()
        .enumerate()
        .filter(|(_, section)| section.section_id == *identity)
        .map(|(index, _)| index);
    let index = matches.next().ok_or(NoteError::TargetNotFound)?;
    if matches.next().is_some() {
        return Err(NoteError::TargetNotFound);
    }
    Ok(index)
}

fn validate_document_state(state: &NoteDocumentState, limits: NoteLimits) -> Result<(), NoteError> {
    if state.schema_version != NOTE_ENGINE_SCHEMA_VERSION
        || state.sections.is_empty()
        || state.sections.len() > limits.0.sections
        || state.notes.len() > limits.0.notes
    {
        return Err(NoteError::InvalidIdentity);
    }
    for digest in [
        &state.non_note_content_sha256,
        &state.style_catalog_sha256,
        &state.numbering_inventory_sha256,
        &state.reference_inventory_sha256,
        &state.resource_inventory_sha256,
        &state.document_protection_sha256,
        &state.opaque_document_state_sha256,
    ] {
        require_digest(digest)?;
    }
    let mut section_ids = BTreeSet::new();
    for section in &state.sections {
        if !section_ids.insert(&section.section_id) {
            return Err(NoteError::InvalidIdentity);
        }
        if section.footnote_style.kind != NoteKind::Footnote
            || section.endnote_style.kind != NoteKind::Endnote
        {
            return Err(NoteError::InvalidStyle);
        }
        validate_style(&section.footnote_style, limits)?;
        validate_style(&section.endnote_style, limits)?;
        require_digest(&section.opaque_section_state_sha256)?;
    }
    let mut logical_ids = BTreeSet::new();
    let mut native_ids = BTreeSet::new();
    let mut anchors = BTreeSet::new();
    for note in &state.notes {
        validate_note(note, limits)?;
        if !section_ids.contains(&note.anchor.section_id)
            || !logical_ids.insert(&note.identity.logical_note_id)
            || !native_ids.insert(note.identity.native_instance_id)
            || !anchors.insert(&note.anchor)
        {
            return Err(NoteError::InvalidIdentity);
        }
    }
    Ok(())
}

fn validate_note(note: &NoteEntry, limits: NoteLimits) -> Result<(), NoteError> {
    if note.identity.native_instance_id == 0 {
        return Err(NoteError::InvalidIdentity);
    }
    if note.native_tag != note.kind.native_tag() {
        return Err(NoteError::InvalidNativeTag);
    }
    for value in [
        note.marker.user_character.as_deref(),
        note.marker.prefix_character.as_deref(),
        note.marker.suffix_character.as_deref(),
    ]
    .into_iter()
    .flatten()
    {
        if !valid_text(value, limits.0.text_bytes, false) || value.chars().count() != 1 {
            return Err(NoteError::InvalidNote);
        }
    }
    for digest in [
        &note.body_graph_sha256,
        &note.marker_style_sha256,
        &note.body_style_sha256,
        &note.opaque_native_payload_sha256,
    ] {
        require_digest(digest)?;
    }
    if note
        .plain_text_sha256
        .as_deref()
        .is_some_and(|value| require_digest(value).is_err())
        || note.opaque_properties.len() > limits.0.opaque_entries
    {
        return Err(NoteError::InvalidNote);
    }
    let mut keys = BTreeSet::new();
    for property in &note.opaque_properties {
        if !valid_token(&property.namespace, limits.0.text_bytes)
            || !valid_token(&property.name, limits.0.text_bytes)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(NoteError::InvalidNote);
        }
    }
    Ok(())
}

fn validate_style(style: &NoteStyle, limits: NoteLimits) -> Result<(), NoteError> {
    let format = &style.auto_number_format;
    for value in [
        &format.user_character,
        &format.prefix_character,
        &format.suffix_character,
    ] {
        if !valid_text(value, limits.0.text_bytes, true) {
            return Err(NoteError::InvalidStyle);
        }
    }
    if matches!(format.format, NoteNumberFormat::UserChar) && format.user_character.is_empty() {
        return Err(NoteError::InvalidStyle);
    }
    if style.note_line.color_rgb > 0x00ff_ffff
        || style.new_number == 0
        || require_digest(&style.opaque_style_sha256).is_err()
    {
        return Err(NoteError::InvalidStyle);
    }
    match style.kind {
        NoteKind::Footnote => {
            if !matches!(
                style.placement,
                NotePlacement::EachColumn
                    | NotePlacement::MergedColumn
                    | NotePlacement::RightMostColumn
            ) {
                return Err(NoteError::InvalidStyle);
            }
        }
        NoteKind::Endnote => {
            if matches!(style.numbering_restart, NoteNumberingRestart::PerPage)
                || !matches!(
                    style.placement,
                    NotePlacement::EndOfDocument | NotePlacement::EndOfSection
                )
            {
                return Err(NoteError::InvalidStyle);
            }
        }
    }
    Ok(())
}

fn valid_token(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
}

fn valid_text(value: &str, max_bytes: usize, allow_empty: bool) -> bool {
    (allow_empty || !value.is_empty())
        && value.len() <= max_bytes
        && !value.chars().any(|character| {
            character == '\0'
                || (character.is_control() && !matches!(character, '\n' | '\r' | '\t'))
        })
}

fn require_digest(value: &str) -> Result<(), NoteError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(NoteError::InvalidDigest);
    }
    Ok(())
}

fn plan_binding_sha256(plan: &NotePlan, limits: NoteLimits) -> Result<String, NoteError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a NoteOperation,
        export_manifest_sha256: Option<&'a str>,
    }
    let binding = Binding {
        schema_version: plan.schema_version,
        capability_id: plan.capability_id,
        request_id: &plan.request_id,
        source_state_sha256: &plan.source_state_sha256,
        target_state_sha256: &plan.target_state_sha256,
        source_document_flow_sha256: &plan.source_document_flow_sha256,
        target_document_flow_sha256: &plan.target_document_flow_sha256,
        operation: &plan.operation,
        export_manifest_sha256: plan.export_manifest_sha256.as_deref(),
    };
    Ok(hex(
        Sha256::digest(serialize_bounded(&binding, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(value: &T, limits: NoteLimits) -> Result<Vec<u8>, NoteError> {
    let bytes = serde_json::to_vec(value).map_err(|_| NoteError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(NoteError::OutputLimit);
    }
    Ok(bytes)
}

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(64);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), NoteError> {
    struct DuplicateVisitor;
    impl<'de> Visitor<'de> for DuplicateVisitor {
        type Value = ();

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }

        fn visit_bool<E>(self, _: bool) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_i64<E>(self, _: i64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_u64<E>(self, _: u64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_f64<E>(self, _: f64) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_str<E>(self, _: &str) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }

        fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }

        fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
        where
            A: de::SeqAccess<'de>,
        {
            while sequence.next_element_seed(DuplicateSeed)?.is_some() {}
            Ok(())
        }

        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            let mut keys = BTreeSet::new();
            while let Some(key) = map.next_key::<String>()? {
                if !keys.insert(key) {
                    return Err(de::Error::custom("duplicate JSON key"));
                }
                map.next_value_seed(DuplicateSeed)?;
            }
            Ok(())
        }
    }

    struct DuplicateSeed;
    impl<'de> de::DeserializeSeed<'de> for DuplicateSeed {
        type Value = ();

        fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }
    }

    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    de::DeserializeSeed::deserialize(DuplicateSeed, &mut deserializer)
        .map_err(|_| NoteError::InvalidJson)?;
    deserializer.end().map_err(|_| NoteError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Private setup keeps sealed-plan tampering local.
mod private_tests {
    use super::*;

    const DIGEST: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> NoteLimits {
        NoteLimits::new(NoteLimitConfig::default()).expect("limits")
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
                between_notes_hwp_units: 283,
                below_line_hwp_units: 567,
                above_line_hwp_units: 850,
            },
            numbering_restart: NoteNumberingRestart::Continuous,
            new_number: 1,
            placement: match kind {
                NoteKind::Footnote => NotePlacement::EachColumn,
                NoteKind::Endnote => NotePlacement::EndOfDocument,
            },
            beneath_text: false,
            opaque_style_sha256: DIGEST.to_owned(),
            locked: false,
        }
    }

    fn state() -> NoteDocumentState {
        NoteDocumentState::from_draft(
            NoteDocumentStateDraft {
                schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
                sections: vec![NoteSectionState {
                    section_id: LogicalId::parse("section-1").expect("id"),
                    footnote_style: style(NoteKind::Footnote),
                    endnote_style: style(NoteKind::Endnote),
                    opaque_section_state_sha256: DIGEST.to_owned(),
                    locked: false,
                }],
                notes: Vec::new(),
                non_note_content_sha256: DIGEST.to_owned(),
                style_catalog_sha256: DIGEST.to_owned(),
                numbering_inventory_sha256: DIGEST.to_owned(),
                reference_inventory_sha256: DIGEST.to_owned(),
                resource_inventory_sha256: DIGEST.to_owned(),
                document_protection_sha256: DIGEST.to_owned(),
                opaque_document_state_sha256: DIGEST.to_owned(),
                document_locked: false,
            },
            limits(),
        )
        .expect("state")
    }

    fn note() -> NoteEntry {
        NoteEntry {
            identity: NoteIdentity {
                logical_note_id: LogicalId::parse("note-1").expect("id"),
                native_instance_id: 1,
            },
            anchor: NoteAnchor {
                section_id: LogicalId::parse("section-1").expect("id"),
                paragraph_id: LogicalId::parse("paragraph-1").expect("id"),
                run_ordinal: 0,
                inline_ordinal: 0,
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
            body_graph_sha256: DIGEST.to_owned(),
            plain_text_sha256: Some(DIGEST.to_owned()),
            marker_style_sha256: DIGEST.to_owned(),
            body_style_sha256: DIGEST.to_owned(),
            opaque_native_payload_sha256: DIGEST.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    #[test]
    fn private_plan_tampering_is_rejected() {
        let source = state();
        let request = NoteRequest::from_draft(
            NoteRequestDraft {
                schema_version: NOTE_ENGINE_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: DIGEST.to_owned(),
                target_document_flow_sha256: DIGEST.to_owned(),
                operation: NoteOperation::Insert {
                    insertion_index: 0,
                    note: note(),
                },
            },
            &source,
            DIGEST,
            limits(),
        )
        .expect("request");
        let mut plan = NoteBuilder::plan(&source, &request, DIGEST, limits()).expect("plan");
        plan.capability_id = "ref.note_style";
        assert_eq!(
            NoteBuilder::build(&plan, &source, DIGEST, limits()),
            Err(NoteError::PlanTampered)
        );
    }
}
