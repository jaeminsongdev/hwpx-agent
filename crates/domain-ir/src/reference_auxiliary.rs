use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{LinkAnchor, LogicalId, OpaqueLinkProperty};
pub mod sequence_program;

pub const REFERENCE_AUXILIARY_SCHEMA_VERSION: &str = "hwpx-agent.reference-auxiliary/v1";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReferenceAuxiliaryLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub text_bytes: usize,
    pub sections: usize,
    pub items_per_kind: usize,
    pub occupied_native_ids: usize,
    pub opaque_entries: usize,
    pub extent_hwpunit: u32,
}

impl Default for ReferenceAuxiliaryLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            text_bytes: 65_536,
            sections: 4096,
            items_per_kind: 1_000_000,
            occupied_native_ids: 1_000_000,
            opaque_entries: 4096,
            extent_hwpunit: 1_000_000_000,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReferenceAuxiliaryLimits(ReferenceAuxiliaryLimitConfig);

impl ReferenceAuxiliaryLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 65_536;
    pub const HARD_MAX_EXTENT_HWPUNIT: u32 = 2_000_000_000;

    /// Creates finite auxiliary-reference limits without clamping.
    ///
    /// # Errors
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: ReferenceAuxiliaryLimitConfig) -> Result<Self, ReferenceAuxiliaryError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.text_bytes == 0
            || config.text_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.sections == 0
            || config.sections > Self::HARD_MAX_ITEMS
            || config.items_per_kind == 0
            || config.items_per_kind > Self::HARD_MAX_ITEMS
            || config.occupied_native_ids == 0
            || config.occupied_native_ids > Self::HARD_MAX_ITEMS
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
            || config.extent_hwpunit == 0
            || config.extent_hwpunit > Self::HARD_MAX_EXTENT_HWPUNIT
        {
            return Err(ReferenceAuxiliaryError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ReferenceAuxiliaryLimitConfig {
        self.0
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct AuxiliarySectionState {
    pub section_id: LogicalId,
    pub paragraph_count: u32,
    pub run_topology_sha256: String,
    pub inline_topology_sha256: String,
    pub page_assignment_sha256: String,
    pub opaque_section_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for AuxiliarySectionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AuxiliarySectionState")
            .field("paragraph_count", &self.paragraph_count)
            .field("locked", &self.locked)
            .field("section", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptionObjectKind {
    Picture,
    Table,
    Equation,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CaptionObjectTarget {
    pub logical_object_id: LogicalId,
    pub object_kind: CaptionObjectKind,
    pub section_id: LogicalId,
    pub object_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for CaptionObjectTarget {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CaptionObjectTarget")
            .field("object_kind", &self.object_kind)
            .field("locked", &self.locked)
            .field("object", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptionNumberFormat {
    Decimal,
    CircledDecimal,
    RomanUpper,
    RomanLower,
    LatinUpper,
    LatinLower,
    HangulSyllable,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptionRestartPolicy {
    Continuous,
    PerSection,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CaptionSequenceDefinition {
    pub logical_sequence_id: LogicalId,
    pub object_kind: CaptionObjectKind,
    pub label: String,
    pub separator: String,
    pub number_format: CaptionNumberFormat,
    pub restart_policy: CaptionRestartPolicy,
    pub start_at: u32,
    pub number_style_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for CaptionSequenceDefinition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CaptionSequenceDefinition")
            .field("object_kind", &self.object_kind)
            .field("number_format", &self.number_format)
            .field("restart_policy", &self.restart_policy)
            .field("start_at", &self.start_at)
            .field("locked", &self.locked)
            .field("sequence", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NativeCaptionSide {
    Left,
    Right,
    Top,
    Bottom,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptionNativeSemanticBinding {
    UnverifiedSubListNumbering,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CaptionNativeEnvelope {
    pub side: NativeCaptionSide,
    pub full_size: bool,
    pub width_hwpunit: i32,
    pub gap_hwpunit: u32,
    pub last_width_hwpunit: u32,
    pub sub_list_sha256: String,
    pub opaque_native_state_sha256: String,
    pub semantic_binding: CaptionNativeSemanticBinding,
}

impl fmt::Debug for CaptionNativeEnvelope {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CaptionNativeEnvelope")
            .field("side", &self.side)
            .field("full_size", &self.full_size)
            .field("semantic_binding", &self.semantic_binding)
            .field("native", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AuxiliaryCacheStatus {
    Current,
    Stale,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CaptionSequenceCache {
    pub sequence_projection_sha256: String,
    pub rendered_number_sha256: String,
    pub resolved_number: u32,
    pub status: AuxiliaryCacheStatus,
}

impl fmt::Debug for CaptionSequenceCache {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CaptionSequenceCache")
            .field("resolved_number", &self.resolved_number)
            .field("status", &self.status)
            .field("cache", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CaptionBinding {
    pub logical_caption_id: LogicalId,
    pub logical_object_id: LogicalId,
    pub logical_sequence_id: LogicalId,
    pub document_order: u64,
    pub caption_content_sha256: String,
    pub cache: CaptionSequenceCache,
    pub native_envelope: CaptionNativeEnvelope,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl CaptionBinding {
    /// Computes the exact sequence/object/order/number projection without rendering text.
    ///
    /// # Errors
    /// Returns a validation, serialization, or output-limit error.
    pub fn projection_sha256(
        sequence: &CaptionSequenceDefinition,
        target: &CaptionObjectTarget,
        binding: &Self,
        resolved_number: u32,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<String, ReferenceAuxiliaryError> {
        #[derive(Serialize)]
        struct Projection<'a> {
            sequence: &'a CaptionSequenceDefinition,
            target: &'a CaptionObjectTarget,
            logical_caption_id: &'a LogicalId,
            document_order: u64,
            caption_content_sha256: &'a str,
            native_envelope: &'a CaptionNativeEnvelope,
            resolved_number: u32,
        }
        require_digest(&binding.caption_content_sha256)?;
        serialized_sha256(
            &Projection {
                sequence,
                target,
                logical_caption_id: &binding.logical_caption_id,
                document_order: binding.document_order,
                caption_content_sha256: &binding.caption_content_sha256,
                native_envelope: &binding.native_envelope,
                resolved_number,
            },
            limits,
        )
    }
}

impl fmt::Debug for CaptionBinding {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CaptionBinding")
            .field("document_order", &self.document_order)
            .field("cache_status", &self.cache.status)
            .field("locked", &self.locked)
            .field("caption", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NativeDateFieldType {
    Date,
    DocDate,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DateTimeCalendar {
    Gregorian,
    LocaleDefault,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DateTimeFormatDefinition {
    pub pattern: String,
    pub locale: String,
    pub timezone_offset_minutes: i16,
    pub calendar: DateTimeCalendar,
}

impl fmt::Debug for DateTimeFormatDefinition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DateTimeFormatDefinition")
            .field("timezone_offset_minutes", &self.timezone_offset_minutes)
            .field("calendar", &self.calendar)
            .field("format", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DateTimeFieldCache {
    pub format_projection_sha256: String,
    pub display_text_sha256: String,
    pub status: AuxiliaryCacheStatus,
}

impl fmt::Debug for DateTimeFieldCache {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DateTimeFieldCache")
            .field("status", &self.status)
            .field("cache", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DateTimeFieldNode {
    pub logical_field_id: LogicalId,
    pub anchor: LinkAnchor,
    pub begin_control_id: u32,
    pub field_id: u32,
    pub end_begin_control_id_ref: u32,
    pub end_field_id: u32,
    pub native_field_type: NativeDateFieldType,
    pub format: DateTimeFormatDefinition,
    pub cache: DateTimeFieldCache,
    pub native_parameters_sha256: String,
    pub opaque_field_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl DateTimeFieldNode {
    /// Computes a format projection while keeping native parameters opaque.
    ///
    /// # Errors
    /// Returns a serialization or output-limit error.
    pub fn format_projection_sha256(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<String, ReferenceAuxiliaryError> {
        #[derive(Serialize)]
        struct Projection<'a> {
            logical_field_id: &'a LogicalId,
            anchor: &'a LinkAnchor,
            native_field_type: NativeDateFieldType,
            format: &'a DateTimeFormatDefinition,
            native_parameters_sha256: &'a str,
        }
        serialized_sha256(
            &Projection {
                logical_field_id: &self.logical_field_id,
                anchor: &self.anchor,
                native_field_type: self.native_field_type,
                format: &self.format,
                native_parameters_sha256: &self.native_parameters_sha256,
            },
            limits,
        )
    }
}

impl fmt::Debug for DateTimeFieldNode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DateTimeFieldNode")
            .field("native_field_type", &self.native_field_type)
            .field("cache_status", &self.cache.status)
            .field("locked", &self.locked)
            .field("field", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FileNameLiteralNode {
    pub logical_literal_id: LogicalId,
    pub anchor: LinkAnchor,
    pub literal: String,
    pub source_leaf_name_sha256: String,
    pub source_revision_sha256: String,
    pub include_extension: bool,
    pub character_style_sha256: String,
    pub paragraph_style_sha256: String,
    pub opaque_text_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for FileNameLiteralNode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("FileNameLiteralNode")
            .field("include_extension", &self.include_extension)
            .field("locked", &self.locked)
            .field("literal", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CorrectionMarkKind {
    Change,
    Sign,
    Delete,
    Attach,
    Clipping,
    Sawtooth,
    Thinking,
    Praise,
    Line,
    SimpleChange,
    Hyperlink,
    LineAttach,
    LineLink,
    LineTransfer,
    RightMove,
    LeftMove,
    Transfer,
    Split,
    SimpleInsert,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CorrectionMarkNode {
    pub logical_mark_id: LogicalId,
    pub anchor: LinkAnchor,
    pub kind: CorrectionMarkKind,
    pub begin_control_id: u32,
    pub field_id: u32,
    pub end_begin_control_id_ref: u32,
    pub end_field_id: u32,
    pub author_identity_sha256: String,
    pub created_at_epoch_millis: i64,
    pub mark_content_sha256: String,
    pub native_parameters_sha256: String,
    pub opaque_field_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for CorrectionMarkNode {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CorrectionMarkNode")
            .field("kind", &self.kind)
            .field("locked", &self.locked)
            .field("mark", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DataLinkAvailability {
    Available,
    Unavailable,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DataLinkInheritance {
    None,
    Page,
    Footnote,
    PageAndFootnote,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DataLinkArtifactProtection {
    Encrypted,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DataLinkState {
    pub logical_link_id: LogicalId,
    pub logical_artifact_id: LogicalId,
    pub encrypted_artifact_sha256: String,
    pub encryption_envelope_sha256: String,
    pub allowlisted_location_sha256: String,
    pub source_revision_sha256: String,
    pub relationship_state_sha256: String,
    pub inheritance: DataLinkInheritance,
    pub availability: DataLinkAvailability,
    pub artifact_protection: DataLinkArtifactProtection,
    pub opaque_native_state_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for DataLinkState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DataLinkState")
            .field("inheritance", &self.inheritance)
            .field("availability", &self.availability)
            .field("artifact_protection", &self.artifact_protection)
            .field("locked", &self.locked)
            .field("link", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReferenceTargetKind {
    Bookmark,
    Caption,
    Note,
    Heading,
    Object,
    Table,
    Equation,
    Citation,
    ExternalData,
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ValidationTarget {
    pub logical_target_id: LogicalId,
    pub target_kind: ReferenceTargetKind,
    pub anchor: Option<LinkAnchor>,
    pub active: bool,
    pub target_state_sha256: String,
}

impl fmt::Debug for ValidationTarget {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ValidationTarget")
            .field("target_kind", &self.target_kind)
            .field("active", &self.active)
            .field("target", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ValidationReferenceEdge {
    pub logical_reference_id: LogicalId,
    pub source_node_id: LogicalId,
    pub expected_target_id: LogicalId,
    pub expected_target_kind: ReferenceTargetKind,
    pub source_anchor: LinkAnchor,
    pub cached_display_sha256: String,
    pub cache_status: AuxiliaryCacheStatus,
    pub edge_state_sha256: String,
}

impl fmt::Debug for ValidationReferenceEdge {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ValidationReferenceEdge")
            .field("expected_target_kind", &self.expected_target_kind)
            .field("cache_status", &self.cache_status)
            .field("edge", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BrokenReferenceKind {
    MissingTarget,
    InactiveTarget,
    TargetKindMismatch,
    ReferenceCycle,
    StaleCache,
    DataLinkUnavailable,
}

#[derive(Clone, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct BrokenReferenceIssue {
    pub logical_reference_id: LogicalId,
    pub kind: BrokenReferenceKind,
}

impl fmt::Debug for BrokenReferenceIssue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BrokenReferenceIssue")
            .field("kind", &self.kind)
            .field("reference", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ReferenceValidationReport {
    pub schema_version: String,
    pub checked_references: usize,
    pub valid_references: usize,
    pub issues: Vec<BrokenReferenceIssue>,
    pub source_reference_inventory_sha256: String,
}

impl ReferenceValidationReport {
    /// Serializes the deterministic report within the configured output bound.
    ///
    /// # Errors
    /// Returns a serialization or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Vec<u8>, ReferenceAuxiliaryError> {
        serialize_bounded(self, limits)
    }

    /// Computes the canonical report digest.
    ///
    /// # Errors
    /// Returns a serialization or output-limit error.
    pub fn canonical_sha256(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<String, ReferenceAuxiliaryError> {
        serialized_sha256(self, limits)
    }
}

impl fmt::Debug for ReferenceValidationReport {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceValidationReport")
            .field("checked_references", &self.checked_references)
            .field("valid_references", &self.valid_references)
            .field("issue_count", &self.issues.len())
            .field("report", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ReferenceAuxiliaryDocumentStateDraft {
    pub schema_version: String,
    pub sections: Vec<AuxiliarySectionState>,
    pub caption_objects: Vec<CaptionObjectTarget>,
    pub caption_sequences: Vec<CaptionSequenceDefinition>,
    pub captions: Vec<CaptionBinding>,
    pub date_time_fields: Vec<DateTimeFieldNode>,
    pub file_name_literals: Vec<FileNameLiteralNode>,
    pub correction_marks: Vec<CorrectionMarkNode>,
    pub data_link: Option<DataLinkState>,
    pub validation_targets: Vec<ValidationTarget>,
    pub validation_edges: Vec<ValidationReferenceEdge>,
    pub occupied_non_aux_control_ids: Vec<u32>,
    pub occupied_non_aux_field_ids: Vec<u32>,
    pub non_auxiliary_content_sha256: String,
    pub field_inventory_sha256: String,
    pub form_inventory_sha256: String,
    pub note_inventory_sha256: String,
    pub comment_inventory_sha256: String,
    pub link_inventory_sha256: String,
    pub cross_reference_inventory_sha256: String,
    pub toc_index_inventory_sha256: String,
    pub citation_inventory_sha256: String,
    pub mail_merge_inventory_sha256: String,
    pub object_inventory_sha256: String,
    pub numbering_inventory_sha256: String,
    pub style_catalog_sha256: String,
    pub relationship_inventory_sha256: String,
    pub resource_inventory_sha256: String,
    pub document_protection_sha256: String,
    pub opaque_document_state_sha256: String,
    pub document_locked: bool,
}

impl fmt::Debug for ReferenceAuxiliaryDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceAuxiliaryDocumentStateDraft")
            .field("caption_count", &self.captions.len())
            .field("date_field_count", &self.date_time_fields.len())
            .field("literal_count", &self.file_name_literals.len())
            .field("correction_mark_count", &self.correction_marks.len())
            .field("has_data_link", &self.data_link.is_some())
            .field("reference_count", &self.validation_edges.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq)]
#[serde(try_from = "ReferenceAuxiliaryDocumentStateDraft")]
pub struct ReferenceAuxiliaryDocumentState {
    schema_version: String,
    sections: Vec<AuxiliarySectionState>,
    caption_objects: Vec<CaptionObjectTarget>,
    caption_sequences: Vec<CaptionSequenceDefinition>,
    captions: Vec<CaptionBinding>,
    date_time_fields: Vec<DateTimeFieldNode>,
    file_name_literals: Vec<FileNameLiteralNode>,
    correction_marks: Vec<CorrectionMarkNode>,
    data_link: Option<DataLinkState>,
    validation_targets: Vec<ValidationTarget>,
    validation_edges: Vec<ValidationReferenceEdge>,
    occupied_non_aux_control_ids: Vec<u32>,
    occupied_non_aux_field_ids: Vec<u32>,
    non_auxiliary_content_sha256: String,
    field_inventory_sha256: String,
    form_inventory_sha256: String,
    note_inventory_sha256: String,
    comment_inventory_sha256: String,
    link_inventory_sha256: String,
    cross_reference_inventory_sha256: String,
    toc_index_inventory_sha256: String,
    citation_inventory_sha256: String,
    mail_merge_inventory_sha256: String,
    object_inventory_sha256: String,
    numbering_inventory_sha256: String,
    style_catalog_sha256: String,
    relationship_inventory_sha256: String,
    resource_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
    document_locked: bool,
}

// Preserve Draft's exact field order without serde(into)'s full self.clone().
impl Serialize for ReferenceAuxiliaryDocumentState {
    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        use serde::ser::SerializeStruct as _;
        let mut output = serializer.serialize_struct("ReferenceAuxiliaryDocumentStateDraft", 31)?;
        macro_rules! fields {
            ($($field:ident),+ $(,)?) => { $(output.serialize_field(stringify!($field), &self.$field)?;)+ };
        }
        fields!(schema_version, sections, caption_objects, caption_sequences, captions,
            date_time_fields, file_name_literals, correction_marks, data_link,
            validation_targets, validation_edges, occupied_non_aux_control_ids, occupied_non_aux_field_ids,
            non_auxiliary_content_sha256, field_inventory_sha256, form_inventory_sha256,
            note_inventory_sha256, comment_inventory_sha256, link_inventory_sha256,
            cross_reference_inventory_sha256, toc_index_inventory_sha256, citation_inventory_sha256,
            mail_merge_inventory_sha256, object_inventory_sha256, numbering_inventory_sha256,
            style_catalog_sha256, relationship_inventory_sha256, resource_inventory_sha256,
            document_protection_sha256, opaque_document_state_sha256, document_locked);
        output.end()
    }
}

impl ReferenceAuxiliaryDocumentState {
    /// Validates and constructs a complete auxiliary-reference state.
    ///
    /// # Errors
    /// Returns a typed error for incomplete, unsafe, or inconsistent state.
    pub fn from_draft(
        draft: ReferenceAuxiliaryDocumentStateDraft,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, ReferenceAuxiliaryError> {
        let state = Self {
            schema_version: draft.schema_version,
            sections: draft.sections,
            caption_objects: draft.caption_objects,
            caption_sequences: draft.caption_sequences,
            captions: draft.captions,
            date_time_fields: draft.date_time_fields,
            file_name_literals: draft.file_name_literals,
            correction_marks: draft.correction_marks,
            data_link: draft.data_link,
            validation_targets: draft.validation_targets,
            validation_edges: draft.validation_edges,
            occupied_non_aux_control_ids: draft.occupied_non_aux_control_ids,
            occupied_non_aux_field_ids: draft.occupied_non_aux_field_ids,
            non_auxiliary_content_sha256: draft.non_auxiliary_content_sha256,
            field_inventory_sha256: draft.field_inventory_sha256,
            form_inventory_sha256: draft.form_inventory_sha256,
            note_inventory_sha256: draft.note_inventory_sha256,
            comment_inventory_sha256: draft.comment_inventory_sha256,
            link_inventory_sha256: draft.link_inventory_sha256,
            cross_reference_inventory_sha256: draft.cross_reference_inventory_sha256,
            toc_index_inventory_sha256: draft.toc_index_inventory_sha256,
            citation_inventory_sha256: draft.citation_inventory_sha256,
            mail_merge_inventory_sha256: draft.mail_merge_inventory_sha256,
            object_inventory_sha256: draft.object_inventory_sha256,
            numbering_inventory_sha256: draft.numbering_inventory_sha256,
            style_catalog_sha256: draft.style_catalog_sha256,
            relationship_inventory_sha256: draft.relationship_inventory_sha256,
            resource_inventory_sha256: draft.resource_inventory_sha256,
            document_protection_sha256: draft.document_protection_sha256,
            opaque_document_state_sha256: draft.opaque_document_state_sha256,
            document_locked: draft.document_locked,
        };
        validate_state(&state, limits)?;
        Ok(state)
    }

    #[must_use]
    pub fn captions(&self) -> &[CaptionBinding] {
        &self.captions
    }

    #[must_use]
    pub fn date_time_fields(&self) -> &[DateTimeFieldNode] {
        &self.date_time_fields
    }

    #[must_use]
    pub fn file_name_literals(&self) -> &[FileNameLiteralNode] {
        &self.file_name_literals
    }

    #[must_use]
    pub fn correction_marks(&self) -> &[CorrectionMarkNode] {
        &self.correction_marks
    }

    #[must_use]
    pub const fn data_link(&self) -> Option<&DataLinkState> {
        self.data_link.as_ref()
    }

    /// Produces a deterministic typed broken-reference report without mutating the state.
    ///
    /// # Errors
    /// Returns a state, serialization, or output-limit error.
    pub fn validate_references(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<ReferenceValidationReport, ReferenceAuxiliaryError> {
        validate_state(self, limits)?;
        build_reference_report(self, limits)
    }

    /// Serializes the canonical validated state within the configured bound.
    ///
    /// # Errors
    /// Returns a validation, serialization, or output-limit error.
    pub fn canonical_json(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Vec<u8>, ReferenceAuxiliaryError> {
        validate_state(self, limits)?;
        serialize_bounded(self, limits)
    }

    /// Computes the canonical state digest.
    ///
    /// # Errors
    /// Returns a validation, serialization, or output-limit error.
    pub fn canonical_sha256(
        &self,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<String, ReferenceAuxiliaryError> {
        validate_state(self, limits)?;
        serialized_sha256(self, limits)
    }
}

impl TryFrom<ReferenceAuxiliaryDocumentStateDraft> for ReferenceAuxiliaryDocumentState {
    type Error = ReferenceAuxiliaryError;

    fn try_from(draft: ReferenceAuxiliaryDocumentStateDraft) -> Result<Self, Self::Error> {
        let limits = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default())?;
        Self::from_draft(draft, limits)
    }
}

impl From<ReferenceAuxiliaryDocumentState> for ReferenceAuxiliaryDocumentStateDraft {
    fn from(state: ReferenceAuxiliaryDocumentState) -> Self {
        Self {
            schema_version: state.schema_version,
            sections: state.sections,
            caption_objects: state.caption_objects,
            caption_sequences: state.caption_sequences,
            captions: state.captions,
            date_time_fields: state.date_time_fields,
            file_name_literals: state.file_name_literals,
            correction_marks: state.correction_marks,
            data_link: state.data_link,
            validation_targets: state.validation_targets,
            validation_edges: state.validation_edges,
            occupied_non_aux_control_ids: state.occupied_non_aux_control_ids,
            occupied_non_aux_field_ids: state.occupied_non_aux_field_ids,
            non_auxiliary_content_sha256: state.non_auxiliary_content_sha256,
            field_inventory_sha256: state.field_inventory_sha256,
            form_inventory_sha256: state.form_inventory_sha256,
            note_inventory_sha256: state.note_inventory_sha256,
            comment_inventory_sha256: state.comment_inventory_sha256,
            link_inventory_sha256: state.link_inventory_sha256,
            cross_reference_inventory_sha256: state.cross_reference_inventory_sha256,
            toc_index_inventory_sha256: state.toc_index_inventory_sha256,
            citation_inventory_sha256: state.citation_inventory_sha256,
            mail_merge_inventory_sha256: state.mail_merge_inventory_sha256,
            object_inventory_sha256: state.object_inventory_sha256,
            numbering_inventory_sha256: state.numbering_inventory_sha256,
            style_catalog_sha256: state.style_catalog_sha256,
            relationship_inventory_sha256: state.relationship_inventory_sha256,
            resource_inventory_sha256: state.resource_inventory_sha256,
            document_protection_sha256: state.document_protection_sha256,
            opaque_document_state_sha256: state.opaque_document_state_sha256,
            document_locked: state.document_locked,
        }
    }
}

impl fmt::Debug for ReferenceAuxiliaryDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceAuxiliaryDocumentState")
            .field("caption_count", &self.captions.len())
            .field("date_field_count", &self.date_time_fields.len())
            .field("literal_count", &self.file_name_literals.len())
            .field("correction_mark_count", &self.correction_marks.len())
            .field("has_data_link", &self.data_link.is_some())
            .field("reference_count", &self.validation_edges.len())
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ReferenceAuxiliaryOperation {
    SetCaptionState {
        caption_sequences: Vec<CaptionSequenceDefinition>,
        captions: Vec<CaptionBinding>,
    },
    SetDateTimeFormat {
        logical_field_id: LogicalId,
        format: DateTimeFormatDefinition,
    },
    InsertFileNameLiteral {
        insertion_index: usize,
        literal: Box<FileNameLiteralNode>,
    },
    InsertCorrectionMark {
        insertion_index: usize,
        mark: Box<CorrectionMarkNode>,
    },
    SetDataLink {
        data_link: Option<Box<DataLinkState>>,
    },
    ValidateReferences {
        expected_report_sha256: String,
    },
}

impl ReferenceAuxiliaryOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::SetCaptionState { .. } => "ref.caption_sequence",
            Self::SetDateTimeFormat { .. } => "ref.date_time_format",
            Self::InsertFileNameLiteral { .. } => "ref.file_name_literal",
            Self::InsertCorrectionMark { .. } => "ref.correction_mark",
            Self::SetDataLink { .. } => "ref.data_link",
            Self::ValidateReferences { .. } => "ref.reference_validate",
        }
    }
}

impl fmt::Debug for ReferenceAuxiliaryOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceAuxiliaryOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ReferenceAuxiliaryRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: ReferenceAuxiliaryOperation,
}

impl fmt::Debug for ReferenceAuxiliaryRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceAuxiliaryRequestDraft")
            .field("capability_id", &self.operation.capability_id())
            .field("request", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ReferenceAuxiliaryRequest {
    schema_version: String,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ReferenceAuxiliaryOperation,
}

impl ReferenceAuxiliaryRequest {
    /// Validates a request against the exact current state and document flow.
    ///
    /// # Errors
    /// Returns a typed validation or drift error before a plan exists.
    pub fn from_draft(
        draft: ReferenceAuxiliaryRequestDraft,
        source: &ReferenceAuxiliaryDocumentState,
        current_document_flow_sha256: &str,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, ReferenceAuxiliaryError> {
        validate_state(source, limits)?;
        if draft.schema_version != REFERENCE_AUXILIARY_SCHEMA_VERSION {
            return Err(ReferenceAuxiliaryError::InvalidSchema);
        }
        for digest in [
            &draft.expected_source_state_sha256,
            &draft.expected_document_flow_sha256,
            &draft.target_document_flow_sha256,
            current_document_flow_sha256,
        ] {
            require_digest(digest)?;
        }
        if draft.expected_source_state_sha256 != source.canonical_sha256(limits)? {
            return Err(ReferenceAuxiliaryError::SourceStateDrift);
        }
        if draft.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(ReferenceAuxiliaryError::DocumentFlowDrift);
        }
        let _ = apply_operation(source, &draft.operation, limits)?;
        Ok(Self {
            schema_version: draft.schema_version,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        })
    }

    /// Parses strict bounded JSON and validates it against the source.
    ///
    /// # Errors
    /// Rejects empty, oversized, duplicate-key, unknown-field, invalid, or drifted input.
    pub fn from_json(
        bytes: &[u8],
        source: &ReferenceAuxiliaryDocumentState,
        current_document_flow_sha256: &str,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, ReferenceAuxiliaryError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(ReferenceAuxiliaryError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft: ReferenceAuxiliaryRequestDraft =
            serde_json::from_slice(bytes).map_err(|_| ReferenceAuxiliaryError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }
}

impl fmt::Debug for ReferenceAuxiliaryRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceAuxiliaryRequest")
            .field("capability_id", &self.operation.capability_id())
            .field("request", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ReferenceAuxiliaryPlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: ReferenceAuxiliaryOperation,
    seal_sha256: String,
}

impl fmt::Debug for ReferenceAuxiliaryPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceAuxiliaryPlan")
            .field("capability_id", &self.capability_id)
            .field("plan", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ReferenceAuxiliaryReceipt {
    pub schema_version: &'static str,
    pub capability_id: &'static str,
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub source_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub validation_report_sha256: Option<String>,
}

impl fmt::Debug for ReferenceAuxiliaryReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceAuxiliaryReceipt")
            .field("capability_id", &self.capability_id)
            .field(
                "has_validation_report",
                &self.validation_report_sha256.is_some(),
            )
            .field("receipt", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ReferenceAuxiliaryResult {
    pub state: ReferenceAuxiliaryDocumentState,
    pub receipt: ReferenceAuxiliaryReceipt,
}

impl fmt::Debug for ReferenceAuxiliaryResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ReferenceAuxiliaryResult")
            .field("capability_id", &self.receipt.capability_id)
            .field("result", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ReferenceAuxiliaryBuilder;

impl ReferenceAuxiliaryBuilder {
    /// Plans one exact auxiliary-reference operation.
    ///
    /// # Errors
    /// Returns a validation or drift error when the request is not exact.
    pub fn plan(
        source: &ReferenceAuxiliaryDocumentState,
        request: &ReferenceAuxiliaryRequest,
        current_document_flow_sha256: &str,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<ReferenceAuxiliaryPlan, ReferenceAuxiliaryError> {
        validate_state(source, limits)?;
        require_digest(current_document_flow_sha256)?;
        if request.schema_version != REFERENCE_AUXILIARY_SCHEMA_VERSION {
            return Err(ReferenceAuxiliaryError::InvalidSchema);
        }
        let source_state_sha256 = source.canonical_sha256(limits)?;
        if request.expected_source_state_sha256 != source_state_sha256 {
            return Err(ReferenceAuxiliaryError::SourceStateDrift);
        }
        if request.expected_document_flow_sha256 != current_document_flow_sha256 {
            return Err(ReferenceAuxiliaryError::DocumentFlowDrift);
        }
        let target = apply_operation(source, &request.operation, limits)?;
        let mut plan = ReferenceAuxiliaryPlan {
            schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION,
            capability_id: request.operation.capability_id(),
            request_id: request.request_id.clone(),
            source_state_sha256,
            target_state_sha256: target.canonical_sha256(limits)?,
            source_document_flow_sha256: current_document_flow_sha256.to_owned(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            seal_sha256: String::new(),
        };
        plan.seal_sha256 = plan_binding_sha256(&plan, limits)?;
        Ok(plan)
    }

    /// Builds the target after rechecking the sealed plan, source state, and flow.
    ///
    /// # Errors
    /// Returns a tamper, validation, or drift error without partial state.
    pub fn build(
        plan: &ReferenceAuxiliaryPlan,
        source: &ReferenceAuxiliaryDocumentState,
        current_document_flow_sha256: &str,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<ReferenceAuxiliaryResult, ReferenceAuxiliaryError> {
        validate_state(source, limits)?;
        require_digest(current_document_flow_sha256)?;
        if plan.schema_version != REFERENCE_AUXILIARY_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || require_digest(&plan.source_state_sha256).is_err()
            || require_digest(&plan.target_state_sha256).is_err()
            || require_digest(&plan.source_document_flow_sha256).is_err()
            || require_digest(&plan.target_document_flow_sha256).is_err()
            || require_digest(&plan.seal_sha256).is_err()
            || plan_binding_sha256(plan, limits)? != plan.seal_sha256
        {
            return Err(ReferenceAuxiliaryError::PlanTampered);
        }
        if source.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(ReferenceAuxiliaryError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(ReferenceAuxiliaryError::DocumentFlowDrift);
        }
        let state = apply_operation(source, &plan.operation, limits)?;
        if state.canonical_sha256(limits)? != plan.target_state_sha256 {
            return Err(ReferenceAuxiliaryError::PlanTampered);
        }
        let validation_report_sha256 = match &plan.operation {
            ReferenceAuxiliaryOperation::ValidateReferences { .. } => Some(
                state
                    .validate_references(limits)?
                    .canonical_sha256(limits)?,
            ),
            _ => None,
        };
        Ok(ReferenceAuxiliaryResult {
            state,
            receipt: ReferenceAuxiliaryReceipt {
                schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                source_state_sha256: plan.source_state_sha256.clone(),
                target_state_sha256: plan.target_state_sha256.clone(),
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                validation_report_sha256,
            },
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum ReferenceAuxiliaryError {
    #[error("invalid auxiliary-reference limit")]
    InvalidLimit,
    #[error("auxiliary-reference input exceeds limit")]
    InputLimit,
    #[error("invalid auxiliary-reference JSON")]
    InvalidJson,
    #[error("invalid auxiliary-reference schema")]
    InvalidSchema,
    #[error("invalid auxiliary-reference identity")]
    InvalidIdentity,
    #[error("invalid caption sequence or binding")]
    InvalidCaption,
    #[error("caption target is missing or ambiguous")]
    CaptionTargetMissing,
    #[error("date/time field is missing or ambiguous")]
    DateTimeFieldMissing,
    #[error("invalid date/time field or format")]
    InvalidDateTime,
    #[error("invalid file-name literal")]
    InvalidFileNameLiteral,
    #[error("invalid correction mark")]
    InvalidCorrectionMark,
    #[error("invalid data link")]
    InvalidDataLink,
    #[error("invalid reference-validation graph")]
    InvalidReferenceGraph,
    #[error("reference-validation report differs")]
    ValidationReportDrift,
    #[error("auxiliary-reference mutation is protected")]
    Protected,
    #[error("auxiliary-reference operation has no effect")]
    NoChange,
    #[error("auxiliary-reference source state drifted")]
    SourceStateDrift,
    #[error("auxiliary-reference document flow drifted")]
    DocumentFlowDrift,
    #[error("auxiliary-reference plan was tampered")]
    PlanTampered,
    #[error("auxiliary-reference serialization failed")]
    Serialization,
    #[error("auxiliary-reference output exceeds limit")]
    OutputLimit,
}

impl ReferenceAuxiliaryError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "reference_auxiliary_invalid_limit",
            Self::InputLimit => "reference_auxiliary_input_limit",
            Self::InvalidJson => "reference_auxiliary_invalid_json",
            Self::InvalidSchema => "reference_auxiliary_invalid_schema",
            Self::InvalidIdentity => "reference_auxiliary_invalid_identity",
            Self::InvalidCaption => "reference_auxiliary_invalid_caption",
            Self::CaptionTargetMissing => "reference_auxiliary_caption_target_missing",
            Self::DateTimeFieldMissing => "reference_auxiliary_date_time_field_missing",
            Self::InvalidDateTime => "reference_auxiliary_invalid_date_time",
            Self::InvalidFileNameLiteral => "reference_auxiliary_invalid_file_name_literal",
            Self::InvalidCorrectionMark => "reference_auxiliary_invalid_correction_mark",
            Self::InvalidDataLink => "reference_auxiliary_invalid_data_link",
            Self::InvalidReferenceGraph => "reference_auxiliary_invalid_reference_graph",
            Self::ValidationReportDrift => "reference_auxiliary_validation_report_drift",
            Self::Protected => "reference_auxiliary_protected",
            Self::NoChange => "reference_auxiliary_no_change",
            Self::SourceStateDrift => "reference_auxiliary_source_state_drift",
            Self::DocumentFlowDrift => "reference_auxiliary_document_flow_drift",
            Self::PlanTampered => "reference_auxiliary_plan_tampered",
            Self::Serialization => "reference_auxiliary_serialization",
            Self::OutputLimit => "reference_auxiliary_output_limit",
        }
    }
}

fn apply_operation(
    source: &ReferenceAuxiliaryDocumentState,
    operation: &ReferenceAuxiliaryOperation,
    limits: ReferenceAuxiliaryLimits,
) -> Result<ReferenceAuxiliaryDocumentState, ReferenceAuxiliaryError> {
    validate_state(source, limits)?;
    if source.document_locked
        && !matches!(
            operation,
            ReferenceAuxiliaryOperation::ValidateReferences { .. }
        )
    {
        return Err(ReferenceAuxiliaryError::Protected);
    }
    let mut target = source.clone();
    match operation {
        ReferenceAuxiliaryOperation::SetCaptionState {
            caption_sequences,
            captions,
        } => {
            if target.caption_sequences == *caption_sequences && target.captions == *captions {
                return Err(ReferenceAuxiliaryError::NoChange);
            }
            enforce_caption_locks(source, caption_sequences, captions)?;
            target.caption_sequences.clone_from(caption_sequences);
            target.captions.clone_from(captions);
            validate_state(&target, limits)?;
            if target
                .captions
                .iter()
                .any(|caption| caption.cache.status != AuxiliaryCacheStatus::Current)
            {
                return Err(ReferenceAuxiliaryError::InvalidCaption);
            }
        }
        ReferenceAuxiliaryOperation::SetDateTimeFormat {
            logical_field_id,
            format,
        } => {
            validate_date_format(format, limits)?;
            let index = select_date_field_index(&target.date_time_fields, logical_field_id)?;
            let section_id = target.date_time_fields[index].anchor.section_id.clone();
            if target.date_time_fields[index].locked {
                return Err(ReferenceAuxiliaryError::Protected);
            }
            ensure_section_unlocked(&target.sections, &section_id)?;
            if target.date_time_fields[index].format == *format {
                return Err(ReferenceAuxiliaryError::NoChange);
            }
            target.date_time_fields[index].format = format.clone();
            target.date_time_fields[index].cache.status = AuxiliaryCacheStatus::Stale;
            validate_state(&target, limits)?;
        }
        ReferenceAuxiliaryOperation::InsertFileNameLiteral {
            insertion_index,
            literal,
        } => {
            if *insertion_index > target.file_name_literals.len() {
                return Err(ReferenceAuxiliaryError::InvalidIdentity);
            }
            ensure_section_unlocked(&target.sections, &literal.anchor.section_id)?;
            validate_file_name_literal(literal, &target.sections, limits)?;
            target
                .file_name_literals
                .insert(*insertion_index, literal.as_ref().clone());
            validate_state(&target, limits)?;
        }
        ReferenceAuxiliaryOperation::InsertCorrectionMark {
            insertion_index,
            mark,
        } => {
            if *insertion_index > target.correction_marks.len() {
                return Err(ReferenceAuxiliaryError::InvalidIdentity);
            }
            ensure_section_unlocked(&target.sections, &mark.anchor.section_id)?;
            validate_correction_mark(mark, &target.sections, limits)?;
            target
                .correction_marks
                .insert(*insertion_index, mark.as_ref().clone());
            validate_state(&target, limits)?;
        }
        ReferenceAuxiliaryOperation::SetDataLink { data_link } => {
            if target.data_link.as_ref() == data_link.as_deref() {
                return Err(ReferenceAuxiliaryError::NoChange);
            }
            if target.data_link.as_ref().is_some_and(|link| link.locked) {
                return Err(ReferenceAuxiliaryError::Protected);
            }
            if let Some(link) = data_link {
                validate_data_link(link, limits)?;
            }
            target.data_link = data_link.as_deref().cloned();
            validate_state(&target, limits)?;
        }
        ReferenceAuxiliaryOperation::ValidateReferences {
            expected_report_sha256,
        } => {
            validate_expected_reference_report(source, expected_report_sha256, limits)?;
        }
    }
    Ok(target)
}

fn validate_state(
    state: &ReferenceAuxiliaryDocumentState,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    if state.schema_version != REFERENCE_AUXILIARY_SCHEMA_VERSION
        || state.sections.is_empty()
        || state.sections.len() > limits.0.sections
        || state.caption_objects.len() > limits.0.items_per_kind
        || state.caption_sequences.len() > limits.0.items_per_kind
        || state.captions.len() > limits.0.items_per_kind
        || state.date_time_fields.len() > limits.0.items_per_kind
        || state.file_name_literals.len() > limits.0.items_per_kind
        || state.correction_marks.len() > limits.0.items_per_kind
        || state.validation_targets.len() > limits.0.items_per_kind
        || state.validation_edges.len() > limits.0.items_per_kind
        || state.occupied_non_aux_control_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_aux_field_ids.len() > limits.0.occupied_native_ids
    {
        return Err(ReferenceAuxiliaryError::InvalidIdentity);
    }
    validate_sorted_ids(&state.occupied_non_aux_control_ids)?;
    validate_sorted_ids(&state.occupied_non_aux_field_ids)?;
    for digest in [
        &state.non_auxiliary_content_sha256,
        &state.field_inventory_sha256,
        &state.form_inventory_sha256,
        &state.note_inventory_sha256,
        &state.comment_inventory_sha256,
        &state.link_inventory_sha256,
        &state.cross_reference_inventory_sha256,
        &state.toc_index_inventory_sha256,
        &state.citation_inventory_sha256,
        &state.mail_merge_inventory_sha256,
        &state.object_inventory_sha256,
        &state.numbering_inventory_sha256,
        &state.style_catalog_sha256,
        &state.relationship_inventory_sha256,
        &state.resource_inventory_sha256,
        &state.document_protection_sha256,
        &state.opaque_document_state_sha256,
    ] {
        require_digest(digest)?;
    }
    let mut section_ids = BTreeSet::new();
    for section in &state.sections {
        if section.paragraph_count == 0 || !section_ids.insert(&section.section_id) {
            return Err(ReferenceAuxiliaryError::InvalidIdentity);
        }
        for digest in [
            &section.run_topology_sha256,
            &section.inline_topology_sha256,
            &section.page_assignment_sha256,
            &section.opaque_section_state_sha256,
        ] {
            require_digest(digest)?;
        }
    }
    validate_caption_state(state, limits)?;
    let mut logical_field_ids = BTreeSet::new();
    let mut control_ids = state
        .occupied_non_aux_control_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let mut field_ids = state
        .occupied_non_aux_field_ids
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    for field in &state.date_time_fields {
        validate_date_time_field(field, &state.sections, limits)?;
        if !logical_field_ids.insert(&field.logical_field_id)
            || !control_ids.insert(field.begin_control_id)
            || !field_ids.insert(field.field_id)
        {
            return Err(ReferenceAuxiliaryError::InvalidIdentity);
        }
    }
    let mut literal_ids = BTreeSet::new();
    for literal in &state.file_name_literals {
        validate_file_name_literal(literal, &state.sections, limits)?;
        if !literal_ids.insert(&literal.logical_literal_id) {
            return Err(ReferenceAuxiliaryError::InvalidFileNameLiteral);
        }
    }
    let mut mark_ids = BTreeSet::new();
    for mark in &state.correction_marks {
        validate_correction_mark(mark, &state.sections, limits)?;
        if !mark_ids.insert(&mark.logical_mark_id)
            || !control_ids.insert(mark.begin_control_id)
            || !field_ids.insert(mark.field_id)
        {
            return Err(ReferenceAuxiliaryError::InvalidCorrectionMark);
        }
    }
    if let Some(link) = &state.data_link {
        validate_data_link(link, limits)?;
    }
    validate_reference_graph(state, limits)
}

#[cfg(test)]
fn legacy_validate_caption_state(
    state: &ReferenceAuxiliaryDocumentState,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    let mut object_ids = BTreeSet::new();
    for object in &state.caption_objects {
        if !object_ids.insert(&object.logical_object_id)
            || !state
                .sections
                .iter()
                .any(|section| section.section_id == object.section_id)
        {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
        require_digest(&object.object_state_sha256)?;
    }
    let mut sequence_ids = BTreeSet::new();
    for sequence in &state.caption_sequences {
        if !sequence_ids.insert(&sequence.logical_sequence_id)
            || sequence.start_at == 0
            || !valid_text(&sequence.label, limits.0.text_bytes, false)
            || !valid_text(&sequence.separator, limits.0.text_bytes, true)
        {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
        require_digest(&sequence.number_style_sha256)?;
        validate_opaque(&sequence.opaque_properties, limits)?;
    }
    let mut caption_ids = BTreeSet::new();
    let mut captioned_objects = BTreeSet::new();
    let mut document_orders = BTreeSet::new();
    for caption in &state.captions {
        if !caption_ids.insert(&caption.logical_caption_id)
            || !captioned_objects.insert(&caption.logical_object_id)
            || !document_orders.insert(caption.document_order)
        {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
        require_digest(&caption.caption_content_sha256)?;
        require_digest(&caption.cache.sequence_projection_sha256)?;
        require_digest(&caption.cache.rendered_number_sha256)?;
        validate_caption_native(&caption.native_envelope, limits)?;
        validate_opaque(&caption.opaque_properties, limits)?;
        let target = select_caption_object(&state.caption_objects, &caption.logical_object_id)?;
        let sequence =
            select_caption_sequence(&state.caption_sequences, &caption.logical_sequence_id)?;
        if target.object_kind != sequence.object_kind {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
    }
    let expected_numbers = legacy_expected_caption_numbers(state)?;
    for caption in &state.captions {
        let expected_number = *expected_numbers
            .get(&caption.logical_caption_id)
            .ok_or(ReferenceAuxiliaryError::InvalidCaption)?;
        if caption.cache.resolved_number != expected_number {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
        let target = select_caption_object(&state.caption_objects, &caption.logical_object_id)?;
        let sequence =
            select_caption_sequence(&state.caption_sequences, &caption.logical_sequence_id)?;
        let projection =
            CaptionBinding::projection_sha256(sequence, target, caption, expected_number, limits)?;
        let expected_status = if projection == caption.cache.sequence_projection_sha256 {
            AuxiliaryCacheStatus::Current
        } else {
            AuxiliaryCacheStatus::Stale
        };
        if caption.cache.status != expected_status {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
    }
    Ok(())
}

#[cfg(test)]
fn legacy_expected_caption_numbers(
    state: &ReferenceAuxiliaryDocumentState,
) -> Result<BTreeMap<LogicalId, u32>, ReferenceAuxiliaryError> {
    let section_positions = state
        .sections
        .iter()
        .enumerate()
        .map(|(index, section)| (&section.section_id, index))
        .collect::<BTreeMap<_, _>>();
    let mut ordered = state.captions.iter().collect::<Vec<_>>();
    ordered.sort_by_key(|caption| caption.document_order);
    let mut counters = BTreeMap::<(LogicalId, Option<usize>), u32>::new();
    let mut result = BTreeMap::new();
    for caption in ordered {
        let target = select_caption_object(&state.caption_objects, &caption.logical_object_id)?;
        let sequence =
            select_caption_sequence(&state.caption_sequences, &caption.logical_sequence_id)?;
        let section = match sequence.restart_policy {
            CaptionRestartPolicy::Continuous => None,
            CaptionRestartPolicy::PerSection => Some(
                *section_positions
                    .get(&target.section_id)
                    .ok_or(ReferenceAuxiliaryError::InvalidCaption)?,
            ),
        };
        let counter = counters
            .entry((sequence.logical_sequence_id.clone(), section))
            .or_insert(sequence.start_at);
        result.insert(caption.logical_caption_id.clone(), *counter);
        *counter = counter
            .checked_add(1)
            .ok_or(ReferenceAuxiliaryError::InvalidCaption)?;
    }
    Ok(result)
}

fn validate_caption_native(
    native: &CaptionNativeEnvelope,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    if native.width_hwpunit < -1
        || u32::try_from(native.width_hwpunit.max(0))
            .map_or(true, |width| width > limits.0.extent_hwpunit)
        || native.gap_hwpunit > limits.0.extent_hwpunit
        || native.last_width_hwpunit > limits.0.extent_hwpunit
        || native.semantic_binding != CaptionNativeSemanticBinding::UnverifiedSubListNumbering
    {
        return Err(ReferenceAuxiliaryError::InvalidCaption);
    }
    require_digest(&native.sub_list_sha256)?;
    require_digest(&native.opaque_native_state_sha256)
}

fn validate_date_time_field(
    field: &DateTimeFieldNode,
    sections: &[AuxiliarySectionState],
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    if field.begin_control_id == 0
        || field.field_id == 0
        || field.end_begin_control_id_ref != field.begin_control_id
        || field.end_field_id != field.field_id
    {
        return Err(ReferenceAuxiliaryError::InvalidDateTime);
    }
    validate_anchor(&field.anchor, sections)?;
    validate_date_format(&field.format, limits)?;
    for digest in [
        &field.cache.format_projection_sha256,
        &field.cache.display_text_sha256,
        &field.native_parameters_sha256,
        &field.opaque_field_state_sha256,
    ] {
        require_digest(digest)?;
    }
    validate_opaque(&field.opaque_properties, limits)?;
    let projection = field.format_projection_sha256(limits)?;
    let expected_status = if projection == field.cache.format_projection_sha256 {
        AuxiliaryCacheStatus::Current
    } else {
        AuxiliaryCacheStatus::Stale
    };
    if field.cache.status != expected_status {
        return Err(ReferenceAuxiliaryError::InvalidDateTime);
    }
    Ok(())
}

fn validate_date_format(
    format: &DateTimeFormatDefinition,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    if !valid_text(&format.pattern, limits.0.text_bytes, false)
        || !valid_locale(&format.locale)
        || !(-1_080..=1_080).contains(&format.timezone_offset_minutes)
    {
        return Err(ReferenceAuxiliaryError::InvalidDateTime);
    }
    Ok(())
}

fn validate_file_name_literal(
    literal: &FileNameLiteralNode,
    sections: &[AuxiliarySectionState],
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    validate_anchor(&literal.anchor, sections)?;
    if !valid_text(&literal.literal, limits.0.text_bytes, false)
        || literal
            .literal
            .chars()
            .any(|character| matches!(character, '/' | '\\' | ':'))
        || hex(Sha256::digest(literal.literal.as_bytes()).into()) != literal.source_leaf_name_sha256
    {
        return Err(ReferenceAuxiliaryError::InvalidFileNameLiteral);
    }
    for digest in [
        &literal.source_leaf_name_sha256,
        &literal.source_revision_sha256,
        &literal.character_style_sha256,
        &literal.paragraph_style_sha256,
        &literal.opaque_text_state_sha256,
    ] {
        require_digest(digest)?;
    }
    validate_opaque(&literal.opaque_properties, limits)
        .map_err(|_| ReferenceAuxiliaryError::InvalidFileNameLiteral)
}

fn validate_correction_mark(
    mark: &CorrectionMarkNode,
    sections: &[AuxiliarySectionState],
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    validate_anchor(&mark.anchor, sections)?;
    if mark.begin_control_id == 0
        || mark.field_id == 0
        || mark.end_begin_control_id_ref != mark.begin_control_id
        || mark.end_field_id != mark.field_id
        || mark.created_at_epoch_millis < 0
    {
        return Err(ReferenceAuxiliaryError::InvalidCorrectionMark);
    }
    for digest in [
        &mark.author_identity_sha256,
        &mark.mark_content_sha256,
        &mark.native_parameters_sha256,
        &mark.opaque_field_state_sha256,
    ] {
        require_digest(digest).map_err(|_| ReferenceAuxiliaryError::InvalidCorrectionMark)?;
    }
    validate_opaque(&mark.opaque_properties, limits)
        .map_err(|_| ReferenceAuxiliaryError::InvalidCorrectionMark)
}

fn validate_data_link(
    link: &DataLinkState,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    for digest in [
        &link.encrypted_artifact_sha256,
        &link.encryption_envelope_sha256,
        &link.allowlisted_location_sha256,
        &link.source_revision_sha256,
        &link.relationship_state_sha256,
        &link.opaque_native_state_sha256,
    ] {
        require_digest(digest).map_err(|_| ReferenceAuxiliaryError::InvalidDataLink)?;
    }
    validate_opaque(&link.opaque_properties, limits)
        .map_err(|_| ReferenceAuxiliaryError::InvalidDataLink)
}

fn validate_expected_reference_report(
    source: &ReferenceAuxiliaryDocumentState,
    expected_report_sha256: &str,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    require_digest(expected_report_sha256)?;
    let actual = source
        .validate_references(limits)?
        .canonical_sha256(limits)?;
    if actual != expected_report_sha256 {
        return Err(ReferenceAuxiliaryError::ValidationReportDrift);
    }
    Ok(())
}

fn validate_reference_graph(
    state: &ReferenceAuxiliaryDocumentState,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    let mut target_ids = BTreeSet::new();
    for target in &state.validation_targets {
        if !target_ids.insert(&target.logical_target_id) {
            return Err(ReferenceAuxiliaryError::InvalidReferenceGraph);
        }
        if let Some(anchor) = &target.anchor {
            validate_anchor(anchor, &state.sections)
                .map_err(|_| ReferenceAuxiliaryError::InvalidReferenceGraph)?;
        }
        require_digest(&target.target_state_sha256)
            .map_err(|_| ReferenceAuxiliaryError::InvalidReferenceGraph)?;
    }
    let mut reference_ids = BTreeSet::new();
    let mut source_ids = BTreeSet::new();
    for edge in &state.validation_edges {
        if !reference_ids.insert(&edge.logical_reference_id)
            || !source_ids.insert(&edge.source_node_id)
        {
            return Err(ReferenceAuxiliaryError::InvalidReferenceGraph);
        }
        validate_anchor(&edge.source_anchor, &state.sections)
            .map_err(|_| ReferenceAuxiliaryError::InvalidReferenceGraph)?;
        require_digest(&edge.cached_display_sha256)
            .map_err(|_| ReferenceAuxiliaryError::InvalidReferenceGraph)?;
        require_digest(&edge.edge_state_sha256)
            .map_err(|_| ReferenceAuxiliaryError::InvalidReferenceGraph)?;
    }
    let _ = build_reference_report(state, limits)?;
    Ok(())
}

fn build_reference_report(
    state: &ReferenceAuxiliaryDocumentState,
    limits: ReferenceAuxiliaryLimits,
) -> Result<ReferenceValidationReport, ReferenceAuxiliaryError> {
    let targets = state
        .validation_targets
        .iter()
        .map(|target| (&target.logical_target_id, target))
        .collect::<BTreeMap<_, _>>();
    let cyclic_sources = find_cyclic_sources(&state.validation_edges);
    let mut issues = Vec::new();
    let mut invalid_references = BTreeSet::new();
    for edge in &state.validation_edges {
        let mut add_issue = |kind| {
            invalid_references.insert(&edge.logical_reference_id);
            issues.push(BrokenReferenceIssue {
                logical_reference_id: edge.logical_reference_id.clone(),
                kind,
            });
        };
        match targets.get(&edge.expected_target_id) {
            None => add_issue(BrokenReferenceKind::MissingTarget),
            Some(target) => {
                if !target.active {
                    add_issue(BrokenReferenceKind::InactiveTarget);
                }
                if target.target_kind != edge.expected_target_kind {
                    add_issue(BrokenReferenceKind::TargetKindMismatch);
                }
                if edge.expected_target_kind == ReferenceTargetKind::ExternalData
                    && state.data_link.as_ref().map(|link| link.availability)
                        != Some(DataLinkAvailability::Available)
                {
                    add_issue(BrokenReferenceKind::DataLinkUnavailable);
                }
            }
        }
        if edge.cache_status == AuxiliaryCacheStatus::Stale {
            add_issue(BrokenReferenceKind::StaleCache);
        }
        if cyclic_sources.contains(&edge.source_node_id) {
            add_issue(BrokenReferenceKind::ReferenceCycle);
        }
    }
    issues.sort();
    let source_reference_inventory_sha256 = serialized_sha256(&state.validation_edges, limits)?;
    Ok(ReferenceValidationReport {
        schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.to_owned(),
        checked_references: state.validation_edges.len(),
        valid_references: state
            .validation_edges
            .len()
            .saturating_sub(invalid_references.len()),
        issues,
        source_reference_inventory_sha256,
    })
}

fn find_cyclic_sources(edges: &[ValidationReferenceEdge]) -> BTreeSet<LogicalId> {
    find_cyclic_sources_with_step(edges, || {})
}

// A source has at most one successor. Once a walk is classified, its entire
// prefix is complete: another source cannot create a new cycle through it.
// The private step hook permits deterministic complexity tests, not a caller
// work limit, skipped validation, cached document result or runtime authority.
fn find_cyclic_sources_with_step(
    edges: &[ValidationReferenceEdge],
    mut step: impl FnMut(),
) -> BTreeSet<LogicalId> {
    let next = edges
        .iter()
        .map(|edge| (&edge.source_node_id, &edge.expected_target_id))
        .collect::<BTreeMap<_, _>>();
    let mut cyclic = BTreeSet::new();
    let mut complete = BTreeSet::new();
    for start in next.keys() {
        if complete.contains(start) {
            continue;
        }
        let mut visited = BTreeMap::<&LogicalId, usize>::new();
        let mut path: Vec<&LogicalId> = Vec::new();
        let mut current = *start;
        while let Some(target) = next.get(current) {
            step();
            if complete.contains(&current) {
                break;
            }
            if let Some(cycle_start) = visited.get(current).copied() {
                for node in &path[cycle_start..] {
                    cyclic.insert((*node).clone());
                }
                break;
            }
            visited.insert(current, path.len());
            path.push(current);
            current = target;
        }
        complete.extend(path);
    }
    cyclic
}

#[cfg(test)]
fn legacy_enforce_caption_locks(
    source: &ReferenceAuxiliaryDocumentState,
    target_sequences: &[CaptionSequenceDefinition],
    target_captions: &[CaptionBinding],
) -> Result<(), ReferenceAuxiliaryError> {
    for sequence in &source.caption_sequences {
        if sequence.locked
            && target_sequences
                .iter()
                .find(|target| target.logical_sequence_id == sequence.logical_sequence_id)
                != Some(sequence)
        {
            return Err(ReferenceAuxiliaryError::Protected);
        }
    }
    for caption in &source.captions {
        if caption.locked
            && target_captions
                .iter()
                .find(|target| target.logical_caption_id == caption.logical_caption_id)
                != Some(caption)
        {
            return Err(ReferenceAuxiliaryError::Protected);
        }
    }
    let source_by_object = source
        .captions
        .iter()
        .map(|caption| (&caption.logical_object_id, caption))
        .collect::<BTreeMap<_, _>>();
    let target_by_object = target_captions
        .iter()
        .map(|caption| (&caption.logical_object_id, caption))
        .collect::<BTreeMap<_, _>>();
    for object in &source.caption_objects {
        if object.locked
            && source_by_object.get(&object.logical_object_id)
                != target_by_object.get(&object.logical_object_id)
        {
            return Err(ReferenceAuxiliaryError::Protected);
        }
    }
    for section in &source.sections {
        if section.locked {
            let changed = source.caption_objects.iter().any(|object| {
                object.section_id == section.section_id
                    && source_by_object.get(&object.logical_object_id)
                        != target_by_object.get(&object.logical_object_id)
            });
            if changed {
                return Err(ReferenceAuxiliaryError::Protected);
            }
        }
    }
    Ok(())
}

#[cfg(test)]
fn select_caption_object<'a>(
    objects: &'a [CaptionObjectTarget],
    object_id: &LogicalId,
) -> Result<&'a CaptionObjectTarget, ReferenceAuxiliaryError> {
    let mut matches = objects
        .iter()
        .filter(|object| object.logical_object_id == *object_id);
    let object = matches
        .next()
        .ok_or(ReferenceAuxiliaryError::CaptionTargetMissing)?;
    if matches.next().is_some() {
        return Err(ReferenceAuxiliaryError::CaptionTargetMissing);
    }
    Ok(object)
}

#[cfg(test)]
fn select_caption_sequence<'a>(
    sequences: &'a [CaptionSequenceDefinition],
    sequence_id: &LogicalId,
) -> Result<&'a CaptionSequenceDefinition, ReferenceAuxiliaryError> {
    let mut matches = sequences
        .iter()
        .filter(|sequence| sequence.logical_sequence_id == *sequence_id);
    let sequence = matches
        .next()
        .ok_or(ReferenceAuxiliaryError::InvalidCaption)?;
    if matches.next().is_some() {
        return Err(ReferenceAuxiliaryError::InvalidCaption);
    }
    Ok(sequence)
}

// Call-local borrowed indexes only. Ambiguous source selectors keep the exact
// legacy errors; target lock maps separately preserve find-first semantics.
struct CaptionIndex<'a> {
    sections: BTreeMap<&'a LogicalId, usize>,
    objects: BTreeMap<&'a LogicalId, Option<&'a CaptionObjectTarget>>,
    sequences: BTreeMap<&'a LogicalId, Option<&'a CaptionSequenceDefinition>>,
}
impl<'a> CaptionIndex<'a> {
    fn new(state: &'a ReferenceAuxiliaryDocumentState) -> Self {
        Self::with_step(state, || {})
    }
    fn with_step(state: &'a ReferenceAuxiliaryDocumentState, mut step: impl FnMut()) -> Self {
        let mut sections = BTreeMap::new();
        for (position, section) in state.sections.iter().enumerate() {
            step();
            sections.insert(&section.section_id, position);
        }
        let mut objects = BTreeMap::<&LogicalId, Option<&CaptionObjectTarget>>::new();
        for object in &state.caption_objects {
            step();
            objects.entry(&object.logical_object_id).and_modify(|value| *value = None).or_insert(Some(object));
        }
        let mut sequences = BTreeMap::<&LogicalId, Option<&CaptionSequenceDefinition>>::new();
        for sequence in &state.caption_sequences {
            step();
            sequences.entry(&sequence.logical_sequence_id).and_modify(|value| *value = None).or_insert(Some(sequence));
        }
        Self { sections, objects, sequences }
    }
    fn object(&self, id: &LogicalId) -> Result<&'a CaptionObjectTarget, ReferenceAuxiliaryError> {
        self.objects.get(id).copied().flatten().ok_or(ReferenceAuxiliaryError::CaptionTargetMissing)
    }
    fn sequence(&self, id: &LogicalId) -> Result<&'a CaptionSequenceDefinition, ReferenceAuxiliaryError> {
        self.sequences.get(id).copied().flatten().ok_or(ReferenceAuxiliaryError::InvalidCaption)
    }
}

fn validate_caption_state(
    state: &ReferenceAuxiliaryDocumentState,
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    let index = CaptionIndex::new(state);
    let mut object_ids = BTreeSet::new();
    for object in &state.caption_objects {
        if !object_ids.insert(&object.logical_object_id)
            || !index.sections.contains_key(&object.section_id)
        {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
        require_digest(&object.object_state_sha256)?;
    }
    let mut sequence_ids = BTreeSet::new();
    for sequence in &state.caption_sequences {
        if !sequence_ids.insert(&sequence.logical_sequence_id)
            || sequence.start_at == 0
            || !valid_text(&sequence.label, limits.0.text_bytes, false)
            || !valid_text(&sequence.separator, limits.0.text_bytes, true)
        {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
        require_digest(&sequence.number_style_sha256)?;
        validate_opaque(&sequence.opaque_properties, limits)?;
    }
    let mut caption_ids = BTreeSet::new();
    let mut captioned_objects = BTreeSet::new();
    let mut document_orders = BTreeSet::new();
    for caption in &state.captions {
        if !caption_ids.insert(&caption.logical_caption_id)
            || !captioned_objects.insert(&caption.logical_object_id)
            || !document_orders.insert(caption.document_order)
        {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
        require_digest(&caption.caption_content_sha256)?;
        require_digest(&caption.cache.sequence_projection_sha256)?;
        require_digest(&caption.cache.rendered_number_sha256)?;
        validate_caption_native(&caption.native_envelope, limits)?;
        validate_opaque(&caption.opaque_properties, limits)?;
        let target = index.object(&caption.logical_object_id)?;
        let sequence =
            index.sequence(&caption.logical_sequence_id)?;
        if target.object_kind != sequence.object_kind {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
    }
    let expected_numbers = expected_caption_numbers_indexed(state, &index, || {})?;
    for caption in &state.captions {
        let expected_number = *expected_numbers
            .get(&caption.logical_caption_id)
            .ok_or(ReferenceAuxiliaryError::InvalidCaption)?;
        if caption.cache.resolved_number != expected_number {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
        let target = index.object(&caption.logical_object_id)?;
        let sequence =
            index.sequence(&caption.logical_sequence_id)?;
        let projection =
            CaptionBinding::projection_sha256(sequence, target, caption, expected_number, limits)?;
        let expected_status = if projection == caption.cache.sequence_projection_sha256 {
            AuxiliaryCacheStatus::Current
        } else {
            AuxiliaryCacheStatus::Stale
        };
        if caption.cache.status != expected_status {
            return Err(ReferenceAuxiliaryError::InvalidCaption);
        }
    }
    Ok(())
}

fn expected_caption_numbers_indexed(
    state: &ReferenceAuxiliaryDocumentState,
    index: &CaptionIndex<'_>,
    mut step: impl FnMut(),
) -> Result<BTreeMap<LogicalId, u32>, ReferenceAuxiliaryError> {
    let mut ordered = state.captions.iter().collect::<Vec<_>>();
    ordered.sort_by_key(|caption| caption.document_order);
    let mut counters = sequence_program::Counters::new();
    let mut result = BTreeMap::new();
    for caption in ordered {
        step();
        let target = index.object(&caption.logical_object_id)?;
        let sequence =
            index.sequence(&caption.logical_sequence_id)?;
        let section = match sequence.restart_policy {
            CaptionRestartPolicy::Continuous => None,
            CaptionRestartPolicy::PerSection => Some(
                *index.sections
                    .get(&target.section_id)
                    .ok_or(ReferenceAuxiliaryError::InvalidCaption)?,
            ),
        };
        result.insert(caption.logical_caption_id.clone(), counters.next(sequence,section)?);
    }
    Ok(result)
}

fn enforce_caption_locks(
    source: &ReferenceAuxiliaryDocumentState,
    target_sequences: &[CaptionSequenceDefinition],
    target_captions: &[CaptionBinding],
) -> Result<(), ReferenceAuxiliaryError> {
    // Preserve the original find-first behavior, even for invalid duplicate targets.
    let mut sequences_by_id = BTreeMap::new();
    for sequence in target_sequences { sequences_by_id.entry(&sequence.logical_sequence_id).or_insert(sequence); }
    let mut captions_by_id = BTreeMap::new();
    for caption in target_captions { captions_by_id.entry(&caption.logical_caption_id).or_insert(caption); }
    for sequence in &source.caption_sequences {
        if sequence.locked
            && sequences_by_id.get(&sequence.logical_sequence_id).copied()
                != Some(sequence)
        {
            return Err(ReferenceAuxiliaryError::Protected);
        }
    }
    for caption in &source.captions {
        if caption.locked
            && captions_by_id.get(&caption.logical_caption_id).copied()
                != Some(caption)
        {
            return Err(ReferenceAuxiliaryError::Protected);
        }
    }
    let source_by_object = source
        .captions
        .iter()
        .map(|caption| (&caption.logical_object_id, caption))
        .collect::<BTreeMap<_, _>>();
    let target_by_object = target_captions
        .iter()
        .map(|caption| (&caption.logical_object_id, caption))
        .collect::<BTreeMap<_, _>>();
    for object in &source.caption_objects {
        if object.locked
            && source_by_object.get(&object.logical_object_id)
                != target_by_object.get(&object.logical_object_id)
        {
            return Err(ReferenceAuxiliaryError::Protected);
        }
    }
    let mut changed_sections = BTreeSet::new();
    for object in &source.caption_objects {
        if source_by_object.get(&object.logical_object_id) != target_by_object.get(&object.logical_object_id) {
            changed_sections.insert(&object.section_id);
        }
    }
    for section in &source.sections {
        if section.locked && changed_sections.contains(&section.section_id) {
            return Err(ReferenceAuxiliaryError::Protected);
        }
    }
    Ok(())
}

fn select_date_field_index(
    fields: &[DateTimeFieldNode],
    field_id: &LogicalId,
) -> Result<usize, ReferenceAuxiliaryError> {
    let mut matches = fields
        .iter()
        .enumerate()
        .filter(|(_, field)| field.logical_field_id == *field_id);
    let (index, _) = matches
        .next()
        .ok_or(ReferenceAuxiliaryError::DateTimeFieldMissing)?;
    if matches.next().is_some() {
        return Err(ReferenceAuxiliaryError::DateTimeFieldMissing);
    }
    Ok(index)
}

fn validate_anchor(
    anchor: &LinkAnchor,
    sections: &[AuxiliarySectionState],
) -> Result<(), ReferenceAuxiliaryError> {
    let mut matches = sections
        .iter()
        .filter(|section| section.section_id == anchor.section_id);
    let section = matches
        .next()
        .ok_or(ReferenceAuxiliaryError::InvalidIdentity)?;
    if matches.next().is_some()
        || anchor.start > anchor.end
        || anchor.start.paragraph_ordinal >= section.paragraph_count
        || anchor.end.paragraph_ordinal >= section.paragraph_count
    {
        return Err(ReferenceAuxiliaryError::InvalidIdentity);
    }
    Ok(())
}

fn ensure_section_unlocked(
    sections: &[AuxiliarySectionState],
    section_id: &LogicalId,
) -> Result<(), ReferenceAuxiliaryError> {
    let mut matches = sections
        .iter()
        .filter(|section| section.section_id == *section_id);
    let section = matches
        .next()
        .ok_or(ReferenceAuxiliaryError::InvalidIdentity)?;
    if matches.next().is_some() {
        return Err(ReferenceAuxiliaryError::InvalidIdentity);
    }
    if section.locked {
        return Err(ReferenceAuxiliaryError::Protected);
    }
    Ok(())
}

fn validate_sorted_ids(ids: &[u32]) -> Result<(), ReferenceAuxiliaryError> {
    if ids.first().is_some_and(|id| *id == 0) || ids.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(ReferenceAuxiliaryError::InvalidIdentity);
    }
    Ok(())
}

fn validate_opaque(
    properties: &[OpaqueLinkProperty],
    limits: ReferenceAuxiliaryLimits,
) -> Result<(), ReferenceAuxiliaryError> {
    if properties.len() > limits.0.opaque_entries {
        return Err(ReferenceAuxiliaryError::InvalidIdentity);
    }
    let mut keys = BTreeSet::new();
    for property in properties {
        if !valid_token(&property.namespace)
            || !valid_token(&property.name)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(ReferenceAuxiliaryError::InvalidIdentity);
        }
    }
    Ok(())
}

fn valid_token(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 1024
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
}

fn valid_locale(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 35
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
}

fn valid_text(value: &str, max_bytes: usize, allow_empty: bool) -> bool {
    (allow_empty || !value.is_empty())
        && value.len() <= max_bytes
        && !value.chars().any(|character| {
            character == '\0' || character == '\r' || character == '\n' || character.is_control()
        })
}

fn require_digest(value: &str) -> Result<(), ReferenceAuxiliaryError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(ReferenceAuxiliaryError::InvalidIdentity);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &ReferenceAuxiliaryPlan,
    limits: ReferenceAuxiliaryLimits,
) -> Result<String, ReferenceAuxiliaryError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a ReferenceAuxiliaryOperation,
    }
    serialized_sha256(
        &Binding {
            schema_version: plan.schema_version,
            capability_id: plan.capability_id,
            request_id: &plan.request_id,
            source_state_sha256: &plan.source_state_sha256,
            target_state_sha256: &plan.target_state_sha256,
            source_document_flow_sha256: &plan.source_document_flow_sha256,
            target_document_flow_sha256: &plan.target_document_flow_sha256,
            operation: &plan.operation,
        },
        limits,
    )
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: ReferenceAuxiliaryLimits,
) -> Result<Vec<u8>, ReferenceAuxiliaryError> {
    let mut writer = AuxiliaryJsonWriter::new(limits, true);
    serde_json::to_writer(&mut writer, value)
        .map_err(|_| writer.failure.unwrap_or(ReferenceAuxiliaryError::Serialization))?;
    writer.output.ok_or(ReferenceAuxiliaryError::Serialization)
}

// Canonical JSON is identical; hashing no longer builds a discarded whole JSON
// buffer. Both sinks reject a crossing chunk BEFORE appending or hashing it.
fn serialized_sha256<T: Serialize>(value: &T, limits: ReferenceAuxiliaryLimits) -> Result<String, ReferenceAuxiliaryError> {
    let mut writer = AuxiliaryJsonWriter::new(limits, false);
    serde_json::to_writer(&mut writer, value)
        .map_err(|_| writer.failure.unwrap_or(ReferenceAuxiliaryError::Serialization))?;
    Ok(hex(writer.digest.finalize().into()))
}
struct AuxiliaryJsonWriter {
    output: Option<Vec<u8>>,
    digest: Sha256,
    written: usize,
    maximum: usize,
    failure: Option<ReferenceAuxiliaryError>,
}
impl AuxiliaryJsonWriter {
    fn new(limits: ReferenceAuxiliaryLimits, output: bool) -> Self {
        Self { output: output.then(Vec::new), digest: Sha256::new(), written: 0,
            maximum: limits.0.output_bytes, failure: None }
    }
}
impl std::io::Write for AuxiliaryJsonWriter {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        if self.failure.is_some() { return Err(std::io::Error::other("REFERENCE_AUXILIARY_JSON_REJECTED")); }
        let Some(total) = self.written.checked_add(bytes.len()).filter(|n| *n <= self.maximum) else {
            self.failure = Some(ReferenceAuxiliaryError::OutputLimit);
            return Err(std::io::Error::other("REFERENCE_AUXILIARY_JSON_LIMIT"));
        };
        if let Some(output) = &mut self.output {
            if output.try_reserve(bytes.len()).is_err() {
                self.failure = Some(ReferenceAuxiliaryError::Serialization);
                return Err(std::io::Error::other("REFERENCE_AUXILIARY_JSON_ALLOCATION"));
            }
            output.extend_from_slice(bytes);
        } else { self.digest.update(bytes); }
        self.written = total;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> std::io::Result<()> { Ok(()) }
}

fn hex(bytes: [u8; 32]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut value = String::with_capacity(64);
    for byte in bytes {
        value.push(char::from(DIGITS[usize::from(byte >> 4)]));
        value.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    value
}

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), ReferenceAuxiliaryError> {
    struct DuplicateVisitor;
    impl<'de> Visitor<'de> for DuplicateVisitor {
        type Value = ();
        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("JSON without duplicate object keys")
        }
        fn visit_bool<E>(self, _value: bool) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_i64<E>(self, _value: i64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_u64<E>(self, _value: u64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_f64<E>(self, _value: f64) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_str<E>(self, _value: &str) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_string<E>(self, _value: String) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_none<E>(self) -> Result<Self::Value, E> {
            Ok(())
        }
        fn visit_some<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
        where
            D: serde::Deserializer<'de>,
        {
            deserializer.deserialize_any(DuplicateVisitor)
        }
        fn visit_unit<E>(self) -> Result<Self::Value, E> {
            Ok(())
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
        .map_err(|_| ReferenceAuxiliaryError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| ReferenceAuxiliaryError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod private_tests {
    use super::*;
    use crate::LinkPoint;

    const D: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn id(value: &str) -> LogicalId {
        LogicalId::parse(value).expect("id")
    }

    fn limits() -> ReferenceAuxiliaryLimits {
        ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default()).expect("limits")
    }

    fn anchor() -> LinkAnchor {
        LinkAnchor {
            section_id: id("section"),
            start: LinkPoint {
                paragraph_ordinal: 0,
                run_ordinal: 0,
                inline_ordinal: 0,
            },
            end: LinkPoint {
                paragraph_ordinal: 0,
                run_ordinal: 0,
                inline_ordinal: 0,
            },
        }
    }

    fn state() -> ReferenceAuxiliaryDocumentState {
        ReferenceAuxiliaryDocumentState::from_draft(
            ReferenceAuxiliaryDocumentStateDraft {
                schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.to_owned(),
                sections: vec![AuxiliarySectionState {
                    section_id: id("section"),
                    paragraph_count: 1,
                    run_topology_sha256: D.to_owned(),
                    inline_topology_sha256: D.to_owned(),
                    page_assignment_sha256: D.to_owned(),
                    opaque_section_state_sha256: D.to_owned(),
                    locked: false,
                }],
                caption_objects: Vec::new(),
                caption_sequences: Vec::new(),
                captions: Vec::new(),
                date_time_fields: Vec::new(),
                file_name_literals: Vec::new(),
                correction_marks: Vec::new(),
                data_link: None,
                validation_targets: Vec::new(),
                validation_edges: Vec::new(),
                occupied_non_aux_control_ids: Vec::new(),
                occupied_non_aux_field_ids: Vec::new(),
                non_auxiliary_content_sha256: D.to_owned(),
                field_inventory_sha256: D.to_owned(),
                form_inventory_sha256: D.to_owned(),
                note_inventory_sha256: D.to_owned(),
                comment_inventory_sha256: D.to_owned(),
                link_inventory_sha256: D.to_owned(),
                cross_reference_inventory_sha256: D.to_owned(),
                toc_index_inventory_sha256: D.to_owned(),
                citation_inventory_sha256: D.to_owned(),
                mail_merge_inventory_sha256: D.to_owned(),
                object_inventory_sha256: D.to_owned(),
                numbering_inventory_sha256: D.to_owned(),
                style_catalog_sha256: D.to_owned(),
                relationship_inventory_sha256: D.to_owned(),
                resource_inventory_sha256: D.to_owned(),
                document_protection_sha256: D.to_owned(),
                opaque_document_state_sha256: D.to_owned(),
                document_locked: false,
            },
            limits(),
        )
        .expect("state")
    }

    #[test]
    fn sealed_plan_rejects_private_operation_tampering() {
        let source = state();
        let literal = FileNameLiteralNode {
            logical_literal_id: id("literal"),
            anchor: anchor(),
            literal: "document.hwpx".to_owned(),
            source_leaf_name_sha256: hex(Sha256::digest(b"document.hwpx").into()),
            source_revision_sha256: D.to_owned(),
            include_extension: true,
            character_style_sha256: D.to_owned(),
            paragraph_style_sha256: D.to_owned(),
            opaque_text_state_sha256: D.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        };
        let request = ReferenceAuxiliaryRequest::from_draft(
            ReferenceAuxiliaryRequestDraft {
                schema_version: REFERENCE_AUXILIARY_SCHEMA_VERSION.to_owned(),
                request_id: id("request"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: D.to_owned(),
                target_document_flow_sha256: D.to_owned(),
                operation: ReferenceAuxiliaryOperation::InsertFileNameLiteral {
                    insertion_index: 0,
                    literal: Box::new(literal),
                },
            },
            &source,
            D,
            limits(),
        )
        .expect("request");
        let mut plan =
            ReferenceAuxiliaryBuilder::plan(&source, &request, D, limits()).expect("plan");
        plan.capability_id = "ref.data_link";
        assert_eq!(
            ReferenceAuxiliaryBuilder::build(&plan, &source, D, limits()),
            Err(ReferenceAuxiliaryError::PlanTampered)
        );
    }

    #[test]
    fn auxiliary_bounded_state_matches_original_draft_json_sha_and_deserialization() {
        let mut draft: ReferenceAuxiliaryDocumentStateDraft = state().into();
        let name = "한글&<frozen>.hwpx";
        draft.file_name_literals.push(FileNameLiteralNode {
            logical_literal_id: id("borrowed-literal"), anchor: anchor(), literal: name.into(),
            source_leaf_name_sha256: hex(Sha256::digest(name.as_bytes()).into()), source_revision_sha256: D.into(),
            include_extension: true, character_style_sha256: D.into(), paragraph_style_sha256: D.into(),
            opaque_text_state_sha256: D.into(), opaque_properties: Vec::new(), locked: false,
        });
        let original = serde_json::to_vec(&draft).expect("independent original Draft serialization");
        let value = ReferenceAuxiliaryDocumentState::from_draft(draft,limits()).expect("state");
        assert_eq!(serde_json::to_vec(&value).expect("borrowed Serialize"),original);
        assert_eq!(value.canonical_json(limits()).expect("canonical bytes"),original);
        assert_eq!(value.canonical_sha256(limits()).expect("stream digest"),hex(Sha256::digest(&original).into()));
        let decoded: ReferenceAuxiliaryDocumentState = serde_json::from_slice(&original).expect("original strict Deserialize");
        assert_eq!(decoded,value);
        let report = value.validate_references(limits()).expect("report");
        assert_eq!(report.canonical_json(limits()).expect("report bytes"),serde_json::to_vec(&report).expect("original report"));
        assert_eq!(report.canonical_sha256(limits()).expect("report digest"),hex(Sha256::digest(serde_json::to_vec(&report).expect("original report")).into()));
    }

    #[test]
    fn auxiliary_bounded_json_and_digest_share_exact_budget_without_discarded_buffers() {
        let value = (vec!["한글<&>\"\n";4096], "tail");
        let original = serde_json::to_vec(&value).expect("independent serde bytes");
        let exact = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
            input_bytes: original.len(), output_bytes: original.len(), ..Default::default()
        }).expect("exact limits");
        assert_eq!(serialize_bounded(&value,exact).expect("exact buffer"),original);
        assert_eq!(serialized_sha256(&value,exact).expect("exact stream"),hex(Sha256::digest(&original).into()));
        let short = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
            input_bytes: original.len()-1, output_bytes: original.len()-1, ..Default::default()
        }).expect("short limits");
        assert_eq!(serialize_bounded(&value,short),Err(ReferenceAuxiliaryError::OutputLimit));
        assert_eq!(serialized_sha256(&value,short),Err(ReferenceAuxiliaryError::OutputLimit));
        let mut writer = AuxiliaryJsonWriter::new(exact,false);
        serde_json::to_writer(&mut writer,&value).expect("hash-only writer");
        assert!(writer.output.is_none());
        assert_eq!(writer.written,original.len());
        assert_eq!(hex(writer.digest.finalize().into()),hex(Sha256::digest(&original).into()));
    }

    #[test]
    fn auxiliary_bounded_serialization_errors_and_early_limit_stay_fail_closed() {
        struct Failing;
        impl Serialize for Failing {
            fn serialize<S: serde::Serializer>(&self,_:S)->Result<S::Ok,S::Error> {
                Err(serde::ser::Error::custom("synthetic serialization failure"))
            }
        }
        assert_eq!(serialize_bounded(&Failing,limits()),Err(ReferenceAuxiliaryError::Serialization));
        assert_eq!(serialized_sha256(&Failing,limits()),Err(ReferenceAuxiliaryError::Serialization));
        let tight = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {input_bytes:31,output_bytes:31,..Default::default()}).expect("tight");
        for output in [true,false] {
            let mut writer = AuxiliaryJsonWriter::new(tight,output);
            assert!(serde_json::to_writer(&mut writer,&"한글\"".repeat(8192)).is_err());
            assert_eq!(writer.failure,Some(ReferenceAuxiliaryError::OutputLimit));
            assert!(writer.written<=31);
            assert!(writer.output.as_ref().is_none_or(|bytes| bytes.len()<=31));
            let before = writer.written;
            assert!(std::io::Write::write(&mut writer,b"x").is_err());
            assert_eq!(writer.written,before); // A failed writer cannot resume with a later short chunk.
        }
    }
    mod caption_index_regressions {
        use super::*;
        use std::cell::Cell;
        type TestResult = Result<(), Box<dyn std::error::Error>>;

        // Synthetic private counter/validation fixtures, not imported/native state.
        fn fixture(objects: usize, choices: &[usize]) -> ReferenceAuxiliaryDocumentState {
            let mut source = state();
            let section = source.sections[0].clone();
            source.sections = (0..2).map(|i| AuxiliarySectionState { section_id: id(&format!("index-section-{i}")), ..section.clone() }).collect();
            source.caption_objects = (0..objects).map(|i| CaptionObjectTarget {
                logical_object_id: id(&format!("index-object-{i:05}")), object_kind: CaptionObjectKind::Picture,
                section_id: source.sections[i % 2].section_id.clone(), object_state_sha256: D.into(), locked: false,
            }).collect();
            source.caption_sequences = (0..2).map(|i| CaptionSequenceDefinition {
                logical_sequence_id: id(&format!("index-sequence-{i}")), object_kind: CaptionObjectKind::Picture,
                label: "그림".into(), separator: " ".into(), number_format: CaptionNumberFormat::Decimal,
                restart_policy: if i == 0 { CaptionRestartPolicy::Continuous } else { CaptionRestartPolicy::PerSection },
                start_at: if i == 0 { 1 } else { 7 }, number_style_sha256: D.into(), opaque_properties: Vec::new(), locked: false,
            }).collect();
            source.captions = choices.iter().enumerate().map(|(i, choice)| CaptionBinding {
                logical_caption_id: id(&format!("index-caption-{i:05}")),
                logical_object_id: source.caption_objects[(choice / 2) % objects].logical_object_id.clone(),
                logical_sequence_id: source.caption_sequences[choice % 2].logical_sequence_id.clone(),
                document_order: i as u64 * 10, caption_content_sha256: D.into(),
                cache: CaptionSequenceCache { sequence_projection_sha256: D.into(), rendered_number_sha256: D.into(), resolved_number: 1, status: AuxiliaryCacheStatus::Stale },
                native_envelope: CaptionNativeEnvelope { side: NativeCaptionSide::Bottom, full_size: false, width_hwpunit: -1,
                    gap_hwpunit: 0, last_width_hwpunit: 0, sub_list_sha256: D.into(), opaque_native_state_sha256: D.into(),
                    semantic_binding: CaptionNativeSemanticBinding::UnverifiedSubListNumbering },
                opaque_properties: Vec::new(), locked: false,
            }).collect();
            source
        }
        fn fill_cache(source: &mut ReferenceAuxiliaryDocumentState) -> TestResult {
            let numbers = legacy_expected_caption_numbers(source)?;
            for caption in &mut source.captions {
                let number = numbers[&caption.logical_caption_id];
                let object = select_caption_object(&source.caption_objects, &caption.logical_object_id)?;
                let sequence = select_caption_sequence(&source.caption_sequences, &caption.logical_sequence_id)?;
                caption.cache.resolved_number = number;
                caption.cache.rendered_number_sha256 = hex(Sha256::digest(number.to_string().as_bytes()).into());
                caption.cache.sequence_projection_sha256 = CaptionBinding::projection_sha256(sequence, object, caption, number, limits())?;
                caption.cache.status = AuxiliaryCacheStatus::Current;
            }
            Ok(())
        }
        fn compare(source: &ReferenceAuxiliaryDocumentState) -> TestResult {
            let before = serde_json::to_vec(source)?;
            let index = CaptionIndex::new(source);
            assert_eq!(expected_caption_numbers_indexed(source, &index, || {}), legacy_expected_caption_numbers(source));
            assert_eq!(validate_caption_state(source, limits()), legacy_validate_caption_state(source, limits()));
            assert_eq!(serde_json::to_vec(source)?, before);
            Ok(())
        }
        #[test]
        fn caption_index_exhaustive1555_variants_keep_numbers_errors_projections_and_input_bytes() -> TestResult {
            let mut cases = 0;
            for count in 0..=4_u32 {
                for mut encoded in 0..6_usize.pow(count) {
                    let choices: Vec<_> = (0..count).map(|_| { let choice = encoded % 6; encoded /= 6; choice }).collect();
                    let mut source = fixture(3, &choices);
                    fill_cache(&mut source)?;
                    compare(&source)?;
                    source.captions.reverse();
                    source.caption_objects.reverse();
                    source.caption_sequences.reverse();
                    source.sections.reverse();
                    compare(&source)?;
                    cases += 1;
                }
            }
            assert_eq!(cases, 1555);
            Ok(())
        }
        #[test]
        fn caption_index_protection512_masks_keep_first_target_and_last_object_map_behavior() -> TestResult {
            let mut source = fixture(3, &[0, 3]);
            fill_cache(&mut source)?;
            for mask in 0..512_u16 {
                let mut current = source.clone();
                for (i, sequence) in current.caption_sequences.iter_mut().enumerate() { sequence.locked = mask & (1 << i) != 0; }
                for (i, caption) in current.captions.iter_mut().enumerate() { caption.locked = mask & (1 << (i + 2)) != 0; }
                for (i, object) in current.caption_objects.iter_mut().enumerate() { object.locked = mask & (1 << (i + 4)) != 0; }
                for (i, section) in current.sections.iter_mut().enumerate() { section.locked = mask & (1 << (i + 7)) != 0; }
                for variant in 0..8 {
                    let mut sequences = current.caption_sequences.clone();
                    let mut captions = current.captions.clone();
                    match variant {
                        0 => {},
                        1 => { sequences[0].label = "표".into(); },
                        2 => { captions[0].caption_content_sha256 = "b".repeat(64); },
                        3 => { captions.remove(0); },
                        4 => { sequences.remove(0); },
                        5 => { let mut duplicate = sequences[0].clone(); duplicate.label = "changed".into(); sequences.push(duplicate); },
                        6 => { let mut duplicate = captions[0].clone(); duplicate.caption_content_sha256 = "b".repeat(64); captions.push(duplicate); },
                        _ => { let mut duplicate = captions[0].clone(); duplicate.caption_content_sha256 = "b".repeat(64); captions.insert(0, duplicate); },
                    }
                    assert_eq!(enforce_caption_locks(&current, &sequences, &captions), legacy_enforce_caption_locks(&current, &sequences, &captions));
                }
            }
            Ok(())
        }
        #[test]
        fn caption_index_missing_ambiguous_stale_and_existing_overflow_errors_remain_exact() -> TestResult {
            let mut source = fixture(3, &[0, 3]);
            fill_cache(&mut source)?;
            for variant in 0..12 {
                let mut changed = source.clone();
                match variant {
                    0 => changed.captions[0].logical_object_id = id("index-absent-object"),
                    1 => changed.captions[0].logical_sequence_id = id("index-absent-sequence"),
                    2 => changed.caption_objects.push(changed.caption_objects[0].clone()),
                    3 => changed.caption_sequences.push(changed.caption_sequences[0].clone()),
                    4 => changed.caption_objects.push(changed.caption_objects[2].clone()),
                    5 => changed.captions[1].logical_caption_id = changed.captions[0].logical_caption_id.clone(),
                    6 => changed.captions[1].document_order = changed.captions[0].document_order,
                    7 => changed.caption_sequences[0].object_kind = CaptionObjectKind::Table,
                    8 => changed.captions[0].cache.status = AuxiliaryCacheStatus::Stale,
                    9 => changed.captions[0].caption_content_sha256 = "invalid".into(),
                    10 => changed.caption_sequences[0].start_at = u32::MAX,
                    _ => changed.caption_objects[0].section_id = id("index-absent-section"),
                }
                compare(&changed)?;
            }
            Ok(())
        }
        #[test]
        fn caption_index_8192_private_counter_records_and_visits_are_linear_not_native_acceptance() -> TestResult {
            const COUNT: usize = 8192;
            let choices: Vec<_> = (0..COUNT).map(|i| i * 2 + i % 2).collect();
            let mut source = fixture(COUNT, &choices);
            let visits = Cell::new(0_usize);
            let index = CaptionIndex::with_step(&source, || visits.set(visits.get() + 1));
            let numbers = expected_caption_numbers_indexed(&source, &index, || visits.set(visits.get() + 1))?;
            assert_eq!(visits.get(), COUNT * 2 + 4); // Two sections, two sequences, objects + captions.
            assert_eq!(numbers.len(), COUNT);
            assert_eq!(numbers[&id("index-caption-08190")], 4096);
            assert_eq!(numbers[&id("index-caption-08191")], 4102);
            drop(index);
            // Only the private lock helper is exercised at scale. These placeholder
            // caches are not claimed as a validated full typed or native state.
            for sequence in &mut source.caption_sequences { sequence.locked = true; }
            for caption in &mut source.captions { caption.locked = true; }
            for object in &mut source.caption_objects { object.locked = true; }
            for section in &mut source.sections { section.locked = true; }
            assert_eq!(enforce_caption_locks(&source, &source.caption_sequences, &source.captions), Ok(()));
            Ok(())
        }
    }
}

#[cfg(test)]
mod cycle_scan_regressions {
    use super::*;
    use crate::{LinkAnchor, LinkPoint};

    type TestResult = Result<(), Box<dyn std::error::Error>>;

    fn node(index: usize) -> Result<LogicalId, Box<dyn std::error::Error>> {
        Ok(LogicalId::parse(format!("cycle-node-{index:05}"))?)
    }

    fn graph(successors: &[usize]) -> Result<Vec<ValidationReferenceEdge>, Box<dyn std::error::Error>> {
        let point = LinkPoint { paragraph_ordinal: 0, run_ordinal: 0, inline_ordinal: 0 };
        successors.iter().enumerate().map(|(index, target)| Ok(ValidationReferenceEdge {
            logical_reference_id: LogicalId::parse(format!("cycle-reference-{index:05}"))?,
            source_node_id: node(index)?,
            expected_target_id: node(*target)?,
            expected_target_kind: ReferenceTargetKind::Bookmark,
            source_anchor: LinkAnchor { section_id: LogicalId::parse("cycle-section")?, start: point, end: point },
            cached_display_sha256: "a".repeat(64),
            cache_status: AuxiliaryCacheStatus::Current,
            edge_state_sha256: "b".repeat(64),
        })).collect()
    }

    // Exact pre-optimization algorithm. Keep it deliberately independent of the
    // completed-path implementation, and use it only for bounded small graphs.
    fn legacy_scan(edges: &[ValidationReferenceEdge]) -> BTreeSet<LogicalId> {
        let next = edges.iter().map(|edge| (&edge.source_node_id, &edge.expected_target_id))
            .collect::<BTreeMap<_, _>>();
        let mut cyclic = BTreeSet::new();
        for start in next.keys() {
            let mut visited = BTreeMap::<&LogicalId, usize>::new();
            let mut path: Vec<&LogicalId> = Vec::new();
            let mut current = *start;
            while let Some(target) = next.get(current) {
                if let Some(cycle_start) = visited.get(current).copied() {
                    for node in &path[cycle_start..] { cyclic.insert((*node).clone()); }
                    break;
                }
                visited.insert(current, path.len());
                path.push(current);
                current = target;
            }
        }
        cyclic
    }

    fn bounded_scan(edges: &[ValidationReferenceEdge]) -> (BTreeSet<LogicalId>, usize) {
        let mut steps = 0usize;
        let result = find_cyclic_sources_with_step(edges, || {
            steps += 1;
            assert!(steps <= edges.len() * 2, "cycle traversal exceeded linear step budget");
        });
        (result, steps)
    }

    #[test]
    fn exhaustive_701_functional_graphs_match_original_cycle_members_and_input_order() -> TestResult {
        let mut compared = 0;
        for count in 0usize..=4 {
            // Each source chooses any source or the same absent terminal node.
            // Includes self/disjoint cycles, fan-in, tails and missing terminals.
            let radix = count + 1;
            for mut encoded in 0..radix.pow(count as u32) {
                let successors: Vec<_> = (0..count).map(|_| {
                    let target = encoded % radix;
                    encoded /= radix;
                    target
                }).collect();
                let mut edges = graph(&successors)?;
                let expected = legacy_scan(&edges);
                assert_eq!(bounded_scan(&edges).0, expected);
                assert_eq!(find_cyclic_sources(&edges), expected);
                edges.reverse();
                assert_eq!(bounded_scan(&edges).0, expected);
                compared += 1;
            }
        }
        assert_eq!(compared, 701);
        Ok(())
    }

    #[test]
    fn sixteen_thousand_source_chains_cycles_and_tails_have_linear_walk_steps() -> TestResult {
        const COUNT: usize = 16_384;
        let mut successors: Vec<_> = (1..=COUNT).collect();
        let (cycle, steps) = bounded_scan(&graph(&successors)?);
        assert!(cycle.is_empty());
        assert_eq!(steps, COUNT);

        successors[COUNT - 1] = 0;
        let (cycle, steps) = bounded_scan(&graph(&successors)?);
        assert_eq!(cycle.len(), COUNT);
        assert_eq!(steps, COUNT + 1);

        successors[COUNT - 1] = COUNT - 64;
        let (cycle, steps) = bounded_scan(&graph(&successors)?);
        let expected = (COUNT - 64..COUNT).map(node).collect::<Result<BTreeSet<_>, _>>()?;
        assert_eq!(cycle, expected); // Reaching a cycle does not make its tail cyclic.
        assert_eq!(steps, COUNT + 1);
        Ok(())
    }

    #[test]
    fn completed_components_and_legacy_duplicate_source_map_behavior_are_preserved() -> TestResult {
        for successors in [vec![0, 1, 2, 3], vec![1, 0, 1, 2], vec![4, 0, 0, 2]] {
            let mut edges = graph(&successors)?;
            assert_eq!(bounded_scan(&edges).0, legacy_scan(&edges));
            // Duplicate sources are rejected by original state validation. The
            // private scanner still keeps the original map's last-entry behavior.
            let mut duplicate = edges[0].clone();
            duplicate.expected_target_id = node(4)?;
            edges.push(duplicate);
            assert_eq!(bounded_scan(&edges).0, legacy_scan(&edges));
            edges.reverse();
            assert_eq!(bounded_scan(&edges).0, legacy_scan(&edges));
        }
        Ok(())
    }
}
