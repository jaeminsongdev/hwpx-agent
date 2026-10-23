use std::collections::BTreeSet;
use std::fmt;

use serde::de::{self, MapAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization as _;

use crate::LogicalId;

pub const LINK_REFERENCE_SCHEMA_VERSION: &str = "hwpx-agent.link-reference/v2";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct LinkReferenceLimitConfig {
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub sections: usize,
    pub bookmarks: usize,
    pub hyperlinks: usize,
    pub occupied_native_ids: usize,
    pub approvals: usize,
    pub name_bytes: usize,
    pub target_bytes: usize,
    pub opaque_entries: usize,
}

impl Default for LinkReferenceLimitConfig {
    fn default() -> Self {
        Self {
            input_bytes: 1024 * 1024,
            output_bytes: 1024 * 1024,
            sections: 4096,
            bookmarks: 1_000_000,
            hyperlinks: 1_000_000,
            occupied_native_ids: 1_000_000,
            approvals: 65_536,
            name_bytes: 1024,
            target_bytes: 16 * 1024,
            opaque_entries: 4096,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct LinkReferenceLimits(LinkReferenceLimitConfig);

impl LinkReferenceLimits {
    pub const HARD_MAX_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_ITEMS: usize = 1_000_000;
    pub const HARD_MAX_TEXT_BYTES: usize = 1024 * 1024;
    pub const HARD_MAX_OPAQUE_ENTRIES: usize = 65_536;

    /// Creates finite link/reference limits without silently clamping values.
    ///
    /// # Errors
    ///
    /// Rejects zero, inconsistent, or hard-ceiling-exceeding values.
    pub fn new(config: LinkReferenceLimitConfig) -> Result<Self, LinkReferenceError> {
        if config.input_bytes == 0
            || config.output_bytes == 0
            || config.input_bytes > config.output_bytes
            || config.output_bytes > Self::HARD_MAX_BYTES
            || config.sections == 0
            || config.sections > Self::HARD_MAX_ITEMS
            || config.bookmarks == 0
            || config.bookmarks > Self::HARD_MAX_ITEMS
            || config.hyperlinks == 0
            || config.hyperlinks > Self::HARD_MAX_ITEMS
            || config.occupied_native_ids == 0
            || config.occupied_native_ids > Self::HARD_MAX_ITEMS
            || config.approvals == 0
            || config.approvals > Self::HARD_MAX_ITEMS
            || config.name_bytes == 0
            || config.name_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.target_bytes == 0
            || config.target_bytes > Self::HARD_MAX_TEXT_BYTES
            || config.opaque_entries == 0
            || config.opaque_entries > Self::HARD_MAX_OPAQUE_ENTRIES
        {
            return Err(LinkReferenceError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> LinkReferenceLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LinkPoint {
    pub paragraph_ordinal: u32,
    pub run_ordinal: u32,
    pub inline_ordinal: u32,
}

impl fmt::Debug for LinkPoint {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("LinkPoint(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LinkAnchor {
    pub section_id: LogicalId,
    pub start: LinkPoint,
    pub end: LinkPoint,
}

impl fmt::Debug for LinkAnchor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("LinkAnchor(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OpaqueLinkProperty {
    pub namespace: String,
    pub name: String,
    pub value_sha256: String,
}

impl fmt::Debug for OpaqueLinkProperty {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("OpaqueLinkProperty(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BookmarkNativeTag {
    Bookmark,
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct BookmarkIdentity {
    pub logical_bookmark_id: LogicalId,
}

impl fmt::Debug for BookmarkIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("BookmarkIdentity(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct BookmarkEntry {
    pub identity: BookmarkIdentity,
    pub name: String,
    pub anchor: LinkAnchor,
    pub native_tag: BookmarkNativeTag,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for BookmarkEntry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("BookmarkEntry")
            .field("locked", &self.locked)
            .field("bookmark", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HyperlinkNativeBeginTag {
    FieldBegin,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HyperlinkNativeEndTag {
    FieldEnd,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HyperlinkFieldType {
    Hyperlink,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HyperlinkSemanticBinding {
    UnverifiedFieldParameters,
    Hangul2020HttpsCurrentTabV1,
}

#[derive(Clone, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HyperlinkIdentity {
    pub logical_hyperlink_id: LogicalId,
    pub begin_control_id: u32,
    pub field_id: u32,
}

impl fmt::Debug for HyperlinkIdentity {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("HyperlinkIdentity(<redacted>)")
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HyperlinkNativePair {
    pub begin_tag: HyperlinkNativeBeginTag,
    pub end_tag: HyperlinkNativeEndTag,
    pub field_type: HyperlinkFieldType,
    pub semantic_binding: HyperlinkSemanticBinding,
    pub end_begin_control_id_ref: u32,
    pub end_field_id: u32,
    pub field_name_sha256: Option<String>,
    pub editable: bool,
    pub dirty: bool,
    pub z_order: i32,
    pub parameters_sha256: String,
    pub sub_list_sha256: Option<String>,
    pub meta_tag_sha256: Option<String>,
    pub opaque_begin_state_sha256: String,
    pub opaque_end_state_sha256: String,
}

impl fmt::Debug for HyperlinkNativePair {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HyperlinkNativePair")
            .field("editable", &self.editable)
            .field("dirty", &self.dirty)
            .field("native", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum HyperlinkTarget {
    InternalBookmark {
        bookmark_id: LogicalId,
    },
    Https {
        uri: String,
    },
    Mailto {
        address: String,
    },
    ManagedDocument {
        artifact_id: LogicalId,
        bookmark_name: Option<String>,
    },
}

impl HyperlinkTarget {
    /// Returns the exact approval digest for an external target.
    ///
    /// Internal bookmark links do not require or expose an external approval digest.
    ///
    /// # Errors
    ///
    /// Rejects an invalid target or a target that is not external.
    pub fn external_approval_sha256(
        &self,
        limits: LinkReferenceLimits,
    ) -> Result<String, LinkReferenceError> {
        validate_target_shape(self, limits)?;
        if matches!(self, Self::InternalBookmark { .. }) {
            return Err(LinkReferenceError::InvalidTarget);
        }
        let bytes = serde_json::to_vec(self).map_err(|_| LinkReferenceError::Serialization)?;
        Ok(hex(Sha256::digest(bytes).into()))
    }

    #[must_use]
    pub const fn external_kind(&self) -> Option<ExternalTargetKind> {
        match self {
            Self::InternalBookmark { .. } => None,
            Self::Https { .. } => Some(ExternalTargetKind::Https),
            Self::Mailto { .. } => Some(ExternalTargetKind::Mailto),
            Self::ManagedDocument { .. } => Some(ExternalTargetKind::ManagedDocument),
        }
    }
}

impl fmt::Debug for HyperlinkTarget {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let kind = match self {
            Self::InternalBookmark { .. } => "internal_bookmark",
            Self::Https { .. } => "https",
            Self::Mailto { .. } => "mailto",
            Self::ManagedDocument { .. } => "managed_document",
        };
        formatter
            .debug_struct("HyperlinkTarget")
            .field("kind", &kind)
            .field("target", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExternalTargetKind {
    Https,
    Mailto,
    ManagedDocument,
}

#[derive(Clone, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ExternalTargetApproval {
    pub kind: ExternalTargetKind,
    pub target_sha256: String,
}

impl fmt::Debug for ExternalTargetApproval {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ExternalTargetApproval")
            .field("kind", &self.kind)
            .field("target", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ExternalLinkPolicy {
    pub allow_https: bool,
    pub allow_mailto: bool,
    pub allow_managed_documents: bool,
    pub approvals: Vec<ExternalTargetApproval>,
    pub policy_revision_sha256: String,
}

impl fmt::Debug for ExternalLinkPolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ExternalLinkPolicy")
            .field("allow_https", &self.allow_https)
            .field("allow_mailto", &self.allow_mailto)
            .field("allow_managed_documents", &self.allow_managed_documents)
            .field("approval_count", &self.approvals.len())
            .field("policy", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl ExternalLinkPolicy {
    /// Validates this finite policy and the exact external target using the original rules.
    /// Pure policy data is not an issuer attestation or permission to open a destination.
    /// # Errors
    /// Rejects internal targets, invalid/disabled policies and absent or mismatched approval digests.
    pub fn require_external_target(&self,target:&HyperlinkTarget,limits:LinkReferenceLimits)->Result<(),LinkReferenceError>{
        validate_policy(self,limits)?;
        if target.external_kind().is_none(){return Err(LinkReferenceError::InvalidTarget);}
        validate_target(target,&[],self,limits)
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HyperlinkEntry {
    pub identity: HyperlinkIdentity,
    pub anchor: LinkAnchor,
    pub target: HyperlinkTarget,
    pub display_text_sha256: String,
    pub native_pair: HyperlinkNativePair,
    pub opaque_native_payload_sha256: String,
    pub opaque_properties: Vec<OpaqueLinkProperty>,
    pub locked: bool,
}

impl fmt::Debug for HyperlinkEntry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("HyperlinkEntry")
            .field("target_kind", &self.target.external_kind())
            .field("locked", &self.locked)
            .field("hyperlink", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LinkReferenceSectionState {
    pub section_id: LogicalId,
    pub paragraph_count: u32,
    pub run_topology_sha256: String,
    pub inline_topology_sha256: String,
    pub opaque_section_state_sha256: String,
    pub locked: bool,
}

impl fmt::Debug for LinkReferenceSectionState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LinkReferenceSectionState")
            .field("paragraph_count", &self.paragraph_count)
            .field("locked", &self.locked)
            .field("section", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LinkReferenceDocumentStateDraft {
    pub schema_version: String,
    pub sections: Vec<LinkReferenceSectionState>,
    pub bookmarks: Vec<BookmarkEntry>,
    pub hyperlinks: Vec<HyperlinkEntry>,
    pub occupied_non_hyperlink_begin_control_ids: Vec<u32>,
    pub occupied_non_hyperlink_field_ids: Vec<u32>,
    pub external_link_policy: ExternalLinkPolicy,
    pub non_reference_content_sha256: String,
    pub unrelated_field_inventory_sha256: String,
    pub style_catalog_sha256: String,
    pub object_inventory_sha256: String,
    pub relationship_inventory_sha256: String,
    pub resource_inventory_sha256: String,
    pub document_protection_sha256: String,
    pub opaque_document_state_sha256: String,
    pub document_locked: bool,
}

impl fmt::Debug for LinkReferenceDocumentStateDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("LinkReferenceDocumentStateDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct LinkReferenceDocumentState {
    schema_version: &'static str,
    sections: Vec<LinkReferenceSectionState>,
    bookmarks: Vec<BookmarkEntry>,
    hyperlinks: Vec<HyperlinkEntry>,
    occupied_non_hyperlink_begin_control_ids: Vec<u32>,
    occupied_non_hyperlink_field_ids: Vec<u32>,
    external_link_policy: ExternalLinkPolicy,
    non_reference_content_sha256: String,
    unrelated_field_inventory_sha256: String,
    style_catalog_sha256: String,
    object_inventory_sha256: String,
    relationship_inventory_sha256: String,
    resource_inventory_sha256: String,
    document_protection_sha256: String,
    opaque_document_state_sha256: String,
    document_locked: bool,
}

impl LinkReferenceDocumentState {
    /// Validates and seals the complete ordered bookmark/hyperlink state.
    ///
    /// # Errors
    ///
    /// Rejects version, identity, target, native, approval, protection, digest, or limit failures.
    pub fn from_draft(
        draft: LinkReferenceDocumentStateDraft,
        limits: LinkReferenceLimits,
    ) -> Result<Self, LinkReferenceError> {
        if draft.schema_version != LINK_REFERENCE_SCHEMA_VERSION {
            return Err(LinkReferenceError::UnsupportedVersion);
        }
        let state = Self {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION,
            sections: draft.sections,
            bookmarks: draft.bookmarks,
            hyperlinks: draft.hyperlinks,
            occupied_non_hyperlink_begin_control_ids: draft
                .occupied_non_hyperlink_begin_control_ids,
            occupied_non_hyperlink_field_ids: draft.occupied_non_hyperlink_field_ids,
            external_link_policy: draft.external_link_policy,
            non_reference_content_sha256: draft.non_reference_content_sha256,
            unrelated_field_inventory_sha256: draft.unrelated_field_inventory_sha256,
            style_catalog_sha256: draft.style_catalog_sha256,
            object_inventory_sha256: draft.object_inventory_sha256,
            relationship_inventory_sha256: draft.relationship_inventory_sha256,
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
    pub fn sections(&self) -> &[LinkReferenceSectionState] {
        &self.sections
    }

    #[must_use]
    pub fn bookmarks(&self) -> &[BookmarkEntry] {
        &self.bookmarks
    }

    #[must_use]
    pub fn hyperlinks(&self) -> &[HyperlinkEntry] {
        &self.hyperlinks
    }

    #[must_use]
    pub const fn external_link_policy(&self) -> &ExternalLinkPolicy {
        &self.external_link_policy
    }

    /// Serializes the complete state deterministically within the configured bound.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_json(
        &self,
        limits: LinkReferenceLimits,
    ) -> Result<Vec<u8>, LinkReferenceError> {
        serialize_bounded(self, limits)
    }

    /// Returns the SHA-256 of the complete canonical state.
    ///
    /// # Errors
    ///
    /// Returns a serialization or output-limit failure.
    pub fn canonical_sha256(
        &self,
        limits: LinkReferenceLimits,
    ) -> Result<String, LinkReferenceError> {
        Ok(hex(Sha256::digest(self.canonical_json(limits)?).into()))
    }
}

impl fmt::Debug for LinkReferenceDocumentState {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LinkReferenceDocumentState")
            .field("section_count", &self.sections.len())
            .field("bookmark_count", &self.bookmarks.len())
            .field("hyperlink_count", &self.hyperlinks.len())
            .field(
                "occupied_native_id_count",
                &(self.occupied_non_hyperlink_begin_control_ids.len()
                    + self.occupied_non_hyperlink_field_ids.len()),
            )
            .field("document_locked", &self.document_locked)
            .field("state", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum LinkReferenceOperation {
    InsertBookmark {
        insertion_index: usize,
        bookmark: BookmarkEntry,
    },
    DeleteBookmark {
        target: BookmarkIdentity,
    },
    InsertHyperlink {
        insertion_index: usize,
        hyperlink: Box<HyperlinkEntry>,
    },
    EditHyperlink {
        target: HyperlinkIdentity,
        new_target: HyperlinkTarget,
        new_display_text_sha256: String,
        new_parameters_sha256: String,
    },
}

impl LinkReferenceOperation {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        match self {
            Self::InsertBookmark { .. } => "ref.bookmark_insert",
            Self::DeleteBookmark { .. } => "ref.bookmark_delete",
            Self::InsertHyperlink { .. } => "ref.hyperlink_insert",
            Self::EditHyperlink { .. } => "ref.hyperlink_edit",
        }
    }
}

impl fmt::Debug for LinkReferenceOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LinkReferenceOperation")
            .field("capability_id", &self.capability_id())
            .field("payload", &"<redacted>")
            .finish()
    }
}

#[derive(Clone, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct LinkReferenceRequestDraft {
    pub schema_version: String,
    pub request_id: LogicalId,
    pub expected_source_state_sha256: String,
    pub expected_document_flow_sha256: String,
    pub target_document_flow_sha256: String,
    pub operation: LinkReferenceOperation,
}

impl fmt::Debug for LinkReferenceRequestDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("LinkReferenceRequestDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct LinkReferenceRequest {
    schema_version: &'static str,
    request_id: LogicalId,
    expected_source_state_sha256: String,
    expected_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: LinkReferenceOperation,
}

impl LinkReferenceRequest {
    /// Strictly parses and validates a bounded request against current state and flow.
    ///
    /// # Errors
    ///
    /// Rejects duplicate/unknown JSON keys, limits, state drift, flow drift, or invalid operations.
    pub fn from_json(
        bytes: &[u8],
        source: &LinkReferenceDocumentState,
        current_document_flow_sha256: &str,
        limits: LinkReferenceLimits,
    ) -> Result<Self, LinkReferenceError> {
        if bytes.is_empty() || bytes.len() > limits.0.input_bytes {
            return Err(LinkReferenceError::InputLimit);
        }
        reject_duplicate_json_keys(bytes)?;
        let draft: LinkReferenceRequestDraft =
            serde_json::from_slice(bytes).map_err(|_| LinkReferenceError::InvalidJson)?;
        Self::from_draft(draft, source, current_document_flow_sha256, limits)
    }

    /// Validates a typed request against current state and flow.
    ///
    /// # Errors
    ///
    /// Rejects version, state/flow drift, invalid digests, or an invalid operation.
    pub fn from_draft(
        draft: LinkReferenceRequestDraft,
        source: &LinkReferenceDocumentState,
        current_document_flow_sha256: &str,
        limits: LinkReferenceLimits,
    ) -> Result<Self, LinkReferenceError> {
        if draft.schema_version != LINK_REFERENCE_SCHEMA_VERSION {
            return Err(LinkReferenceError::UnsupportedVersion);
        }
        require_digest(&draft.expected_source_state_sha256)?;
        require_digest(&draft.expected_document_flow_sha256)?;
        require_digest(&draft.target_document_flow_sha256)?;
        if source.canonical_sha256(limits)? != draft.expected_source_state_sha256 {
            return Err(LinkReferenceError::SourceStateDrift);
        }
        if current_document_flow_sha256 != draft.expected_document_flow_sha256 {
            return Err(LinkReferenceError::DocumentFlowDrift);
        }
        let request = Self {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION,
            request_id: draft.request_id,
            expected_source_state_sha256: draft.expected_source_state_sha256,
            expected_document_flow_sha256: draft.expected_document_flow_sha256,
            target_document_flow_sha256: draft.target_document_flow_sha256,
            operation: draft.operation,
        };
        let _ = apply_operation(source, &request.operation, limits)?;
        Ok(request)
    }

    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.operation.capability_id()
    }
}

impl fmt::Debug for LinkReferenceRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LinkReferenceRequest")
            .field("capability_id", &self.capability_id())
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct LinkReferencePlan {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    operation: LinkReferenceOperation,
    target_state: LinkReferenceDocumentState,
    seal_sha256: String,
}

impl LinkReferencePlan {
    #[must_use]
    pub const fn capability_id(&self) -> &'static str {
        self.capability_id
    }

    #[must_use]
    pub const fn target_state(&self) -> &LinkReferenceDocumentState {
        &self.target_state
    }

    #[must_use]
    pub fn target_state_sha256(&self) -> &str {
        &self.target_state_sha256
    }

    #[must_use]
    pub fn source_state_sha256(&self) -> &str {
        &self.source_state_sha256
    }

    #[must_use]
    pub fn source_document_flow_sha256(&self) -> &str {
        &self.source_document_flow_sha256
    }

    #[must_use]
    pub fn target_document_flow_sha256(&self) -> &str {
        &self.target_document_flow_sha256
    }
}

impl fmt::Debug for LinkReferencePlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LinkReferencePlan")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug)]
pub struct LinkReferenceBuilder;

impl LinkReferenceBuilder {
    /// Builds a sealed exact-state plan.
    ///
    /// # Errors
    ///
    /// Rechecks source/flow drift and rejects invalid, protected, dangling, or no-op transitions.
    pub fn plan(
        source: &LinkReferenceDocumentState,
        request: &LinkReferenceRequest,
        current_document_flow_sha256: &str,
        limits: LinkReferenceLimits,
    ) -> Result<LinkReferencePlan, LinkReferenceError> {
        if source.canonical_sha256(limits)? != request.expected_source_state_sha256 {
            return Err(LinkReferenceError::SourceStateDrift);
        }
        if current_document_flow_sha256 != request.expected_document_flow_sha256 {
            return Err(LinkReferenceError::DocumentFlowDrift);
        }
        let target_state = apply_operation(source, &request.operation, limits)?;
        let target_state_sha256 = target_state.canonical_sha256(limits)?;
        let mut plan = LinkReferencePlan {
            schema_version: LINK_REFERENCE_SCHEMA_VERSION,
            capability_id: request.capability_id(),
            request_id: request.request_id.clone(),
            source_state_sha256: request.expected_source_state_sha256.clone(),
            target_state_sha256,
            source_document_flow_sha256: request.expected_document_flow_sha256.clone(),
            target_document_flow_sha256: request.target_document_flow_sha256.clone(),
            operation: request.operation.clone(),
            target_state,
            seal_sha256: String::new(),
        };
        plan.seal_sha256 = plan_binding_sha256(&plan, limits)?;
        Ok(plan)
    }

    /// Rechecks a sealed plan against the exact current state and flow.
    ///
    /// # Errors
    ///
    /// Rejects tampering, drift, or a target-state mismatch.
    pub fn build(
        plan: &LinkReferencePlan,
        current: &LinkReferenceDocumentState,
        current_document_flow_sha256: &str,
        limits: LinkReferenceLimits,
    ) -> Result<LinkReferenceResult, LinkReferenceError> {
        if plan.schema_version != LINK_REFERENCE_SCHEMA_VERSION
            || plan.capability_id != plan.operation.capability_id()
            || plan.seal_sha256 != plan_binding_sha256(plan, limits)?
        {
            return Err(LinkReferenceError::PlanTampered);
        }
        if current.canonical_sha256(limits)? != plan.source_state_sha256 {
            return Err(LinkReferenceError::SourceStateDrift);
        }
        if current_document_flow_sha256 != plan.source_document_flow_sha256 {
            return Err(LinkReferenceError::DocumentFlowDrift);
        }
        let rebuilt = apply_operation(current, &plan.operation, limits)?;
        if rebuilt != plan.target_state
            || rebuilt.canonical_sha256(limits)? != plan.target_state_sha256
        {
            return Err(LinkReferenceError::PlanTampered);
        }
        Ok(LinkReferenceResult {
            state: rebuilt,
            receipt: LinkReferenceReceipt {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION,
                capability_id: plan.capability_id,
                request_id: plan.request_id.clone(),
                source_state_sha256: plan.source_state_sha256.clone(),
                target_state_sha256: plan.target_state_sha256.clone(),
                source_document_flow_sha256: plan.source_document_flow_sha256.clone(),
                target_document_flow_sha256: plan.target_document_flow_sha256.clone(),
                plan_sha256: plan.seal_sha256.clone(),
            },
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct LinkReferenceReceipt {
    schema_version: &'static str,
    capability_id: &'static str,
    request_id: LogicalId,
    source_state_sha256: String,
    target_state_sha256: String,
    source_document_flow_sha256: String,
    target_document_flow_sha256: String,
    plan_sha256: String,
}

impl fmt::Debug for LinkReferenceReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LinkReferenceReceipt")
            .field("capability_id", &self.capability_id)
            .field("bindings", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct LinkReferenceResult {
    pub state: LinkReferenceDocumentState,
    pub receipt: LinkReferenceReceipt,
}

impl fmt::Debug for LinkReferenceResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("LinkReferenceResult")
            .field("state", &"<redacted>")
            .field("receipt", &self.receipt)
            .finish()
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum LinkReferenceError {
    #[error("link/reference limits are invalid")]
    InvalidLimit,
    #[error("link/reference input exceeds a finite limit")]
    InputLimit,
    #[error("link/reference JSON is malformed, duplicated, or not strict")]
    InvalidJson,
    #[error("link/reference schema version is unsupported")]
    UnsupportedVersion,
    #[error("link/reference identity or anchor is invalid")]
    InvalidIdentity,
    #[error("bookmark name is invalid or duplicated")]
    InvalidBookmarkName,
    #[error("hyperlink target is invalid or unsafe")]
    InvalidTarget,
    #[error("external hyperlink target lacks an exact policy approval")]
    ExternalTargetDenied,
    #[error("hyperlink native binding is unsupported or inconsistent")]
    InvalidNativeBinding,
    #[error("link/reference digest or opaque property is invalid")]
    InvalidPayload,
    #[error("link/reference insertion index is invalid")]
    InvalidInsertionIndex,
    #[error("link/reference target does not exist or is ambiguous")]
    TargetNotFound,
    #[error("bookmark deletion would create a dangling reference")]
    DanglingReference,
    #[error("link/reference target, section, or document is protected")]
    Protected,
    #[error("link/reference operation is a no-op")]
    Noop,
    #[error("link/reference source state drifted")]
    SourceStateDrift,
    #[error("link/reference document flow drifted")]
    DocumentFlowDrift,
    #[error("link/reference plan was tampered with")]
    PlanTampered,
    #[error("link/reference serialization failed")]
    Serialization,
    #[error("link/reference serialized output exceeds a finite limit")]
    OutputLimit,
}

impl LinkReferenceError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "link_reference_invalid_limit",
            Self::InputLimit => "link_reference_input_limit",
            Self::InvalidJson => "link_reference_invalid_json",
            Self::UnsupportedVersion => "link_reference_unsupported_version",
            Self::InvalidIdentity => "link_reference_invalid_identity",
            Self::InvalidBookmarkName => "link_reference_invalid_bookmark_name",
            Self::InvalidTarget => "link_reference_invalid_target",
            Self::ExternalTargetDenied => "link_reference_external_target_denied",
            Self::InvalidNativeBinding => "link_reference_invalid_native_binding",
            Self::InvalidPayload => "link_reference_invalid_payload",
            Self::InvalidInsertionIndex => "link_reference_invalid_insertion_index",
            Self::TargetNotFound => "link_reference_target_not_found",
            Self::DanglingReference => "link_reference_dangling_reference",
            Self::Protected => "link_reference_protected",
            Self::Noop => "link_reference_noop",
            Self::SourceStateDrift => "link_reference_source_state_drift",
            Self::DocumentFlowDrift => "link_reference_document_flow_drift",
            Self::PlanTampered => "link_reference_plan_tampered",
            Self::Serialization => "link_reference_serialization",
            Self::OutputLimit => "link_reference_output_limit",
        }
    }
}

fn apply_operation(
    source: &LinkReferenceDocumentState,
    operation: &LinkReferenceOperation,
    limits: LinkReferenceLimits,
) -> Result<LinkReferenceDocumentState, LinkReferenceError> {
    validate_document_state(source, limits)?;
    if source.document_locked {
        return Err(LinkReferenceError::Protected);
    }
    let mut target = source.clone();
    match operation {
        LinkReferenceOperation::InsertBookmark {
            insertion_index,
            bookmark,
        } => apply_insert_bookmark(&mut target, *insertion_index, bookmark, limits)?,
        LinkReferenceOperation::DeleteBookmark { target: identity } => {
            apply_delete_bookmark(&mut target, identity)?;
        }
        LinkReferenceOperation::InsertHyperlink {
            insertion_index,
            hyperlink,
        } => apply_insert_hyperlink(&mut target, *insertion_index, hyperlink, limits)?,
        LinkReferenceOperation::EditHyperlink {
            target: identity,
            new_target,
            new_display_text_sha256,
            new_parameters_sha256,
        } => apply_edit_hyperlink(
            &mut target,
            identity,
            new_target,
            new_display_text_sha256,
            new_parameters_sha256,
            limits,
        )?,
    }
    validate_document_state(&target, limits)?;
    if &target == source {
        return Err(LinkReferenceError::Noop);
    }
    Ok(target)
}

fn apply_insert_bookmark(
    target: &mut LinkReferenceDocumentState,
    insertion_index: usize,
    bookmark: &BookmarkEntry,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    if insertion_index > target.bookmarks.len() {
        return Err(LinkReferenceError::InvalidInsertionIndex);
    }
    let section_index = exact_section_index(&target.sections, &bookmark.anchor.section_id)?;
    if target.sections[section_index].locked {
        return Err(LinkReferenceError::Protected);
    }
    validate_bookmark(bookmark, &target.sections[section_index], limits)?;
    if target
        .bookmarks
        .iter()
        .any(|existing| existing.identity == bookmark.identity)
    {
        return Err(LinkReferenceError::InvalidIdentity);
    }
    if target
        .bookmarks
        .iter()
        .any(|existing| existing.name == bookmark.name)
    {
        return Err(LinkReferenceError::InvalidBookmarkName);
    }
    target.bookmarks.insert(insertion_index, bookmark.clone());
    Ok(())
}

fn apply_delete_bookmark(
    target: &mut LinkReferenceDocumentState,
    identity: &BookmarkIdentity,
) -> Result<(), LinkReferenceError> {
    let index = exact_bookmark_index(&target.bookmarks, identity)?;
    let section_index =
        exact_section_index(&target.sections, &target.bookmarks[index].anchor.section_id)?;
    if target.bookmarks[index].locked || target.sections[section_index].locked {
        return Err(LinkReferenceError::Protected);
    }
    if target.hyperlinks.iter().any(|hyperlink| {
        matches!(
            &hyperlink.target,
            HyperlinkTarget::InternalBookmark { bookmark_id }
                if bookmark_id == &target.bookmarks[index].identity.logical_bookmark_id
        )
    }) {
        return Err(LinkReferenceError::DanglingReference);
    }
    target.bookmarks.remove(index);
    Ok(())
}

fn apply_insert_hyperlink(
    target: &mut LinkReferenceDocumentState,
    insertion_index: usize,
    hyperlink: &HyperlinkEntry,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    if insertion_index > target.hyperlinks.len() {
        return Err(LinkReferenceError::InvalidInsertionIndex);
    }
    let section_index = exact_section_index(&target.sections, &hyperlink.anchor.section_id)?;
    if target.sections[section_index].locked {
        return Err(LinkReferenceError::Protected);
    }
    validate_hyperlink(
        hyperlink,
        &target.sections[section_index],
        &target.bookmarks,
        &target.external_link_policy,
        limits,
    )?;
    if target.hyperlinks.iter().any(|existing| {
        existing.identity.logical_hyperlink_id == hyperlink.identity.logical_hyperlink_id
            || existing.identity.begin_control_id == hyperlink.identity.begin_control_id
            || existing.identity.field_id == hyperlink.identity.field_id
            || existing.anchor == hyperlink.anchor
    }) {
        return Err(LinkReferenceError::InvalidIdentity);
    }
    target.hyperlinks.insert(insertion_index, hyperlink.clone());
    Ok(())
}

fn apply_edit_hyperlink(
    target: &mut LinkReferenceDocumentState,
    identity: &HyperlinkIdentity,
    new_target: &HyperlinkTarget,
    new_display_text_sha256: &str,
    new_parameters_sha256: &str,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    let index = exact_hyperlink_index(&target.hyperlinks, identity)?;
    let section_index = exact_section_index(
        &target.sections,
        &target.hyperlinks[index].anchor.section_id,
    )?;
    if target.hyperlinks[index].locked || target.sections[section_index].locked {
        return Err(LinkReferenceError::Protected);
    }
    require_digest(new_display_text_sha256)?;
    require_digest(new_parameters_sha256)?;
    validate_target(
        new_target,
        &target.bookmarks,
        &target.external_link_policy,
        limits,
    )?;
    if target.hyperlinks[index].target == *new_target
        && target.hyperlinks[index].display_text_sha256 == new_display_text_sha256
        && target.hyperlinks[index].native_pair.parameters_sha256 == new_parameters_sha256
    {
        return Err(LinkReferenceError::Noop);
    }
    target.hyperlinks[index].target.clone_from(new_target);
    target.hyperlinks[index]
        .display_text_sha256
        .clone_from(&new_display_text_sha256.to_owned());
    target.hyperlinks[index]
        .native_pair
        .parameters_sha256
        .clone_from(&new_parameters_sha256.to_owned());
    Ok(())
}

fn exact_bookmark_index(
    bookmarks: &[BookmarkEntry],
    identity: &BookmarkIdentity,
) -> Result<usize, LinkReferenceError> {
    exact_index(bookmarks, |entry| entry.identity == *identity)
}

fn exact_hyperlink_index(
    hyperlinks: &[HyperlinkEntry],
    identity: &HyperlinkIdentity,
) -> Result<usize, LinkReferenceError> {
    exact_index(hyperlinks, |entry| entry.identity == *identity)
}

fn exact_section_index(
    sections: &[LinkReferenceSectionState],
    section_id: &LogicalId,
) -> Result<usize, LinkReferenceError> {
    exact_index(sections, |section| section.section_id == *section_id)
}

fn exact_index<T>(
    items: &[T],
    predicate: impl Fn(&T) -> bool,
) -> Result<usize, LinkReferenceError> {
    let mut matches = items
        .iter()
        .enumerate()
        .filter(|(_, item)| predicate(item))
        .map(|(index, _)| index);
    let index = matches.next().ok_or(LinkReferenceError::TargetNotFound)?;
    if matches.next().is_some() {
        return Err(LinkReferenceError::TargetNotFound);
    }
    Ok(index)
}

fn validate_document_state(
    state: &LinkReferenceDocumentState,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    if state.schema_version != LINK_REFERENCE_SCHEMA_VERSION
        || state.sections.is_empty()
        || state.sections.len() > limits.0.sections
        || state.bookmarks.len() > limits.0.bookmarks
        || state.hyperlinks.len() > limits.0.hyperlinks
        || state.occupied_non_hyperlink_begin_control_ids.len() > limits.0.occupied_native_ids
        || state.occupied_non_hyperlink_field_ids.len() > limits.0.occupied_native_ids
    {
        return Err(LinkReferenceError::InvalidIdentity);
    }
    for digest in [
        &state.non_reference_content_sha256,
        &state.unrelated_field_inventory_sha256,
        &state.style_catalog_sha256,
        &state.object_inventory_sha256,
        &state.relationship_inventory_sha256,
        &state.resource_inventory_sha256,
        &state.document_protection_sha256,
        &state.opaque_document_state_sha256,
    ] {
        require_digest(digest)?;
    }
    validate_policy(&state.external_link_policy, limits)?;
    if invalid_native_id_inventory(&state.occupied_non_hyperlink_begin_control_ids)
        || invalid_native_id_inventory(&state.occupied_non_hyperlink_field_ids)
    {
        return Err(LinkReferenceError::InvalidIdentity);
    }

    let mut section_ids = BTreeSet::new();
    for section in &state.sections {
        if section.paragraph_count == 0 || !section_ids.insert(&section.section_id) {
            return Err(LinkReferenceError::InvalidIdentity);
        }
        for digest in [
            &section.run_topology_sha256,
            &section.inline_topology_sha256,
            &section.opaque_section_state_sha256,
        ] {
            require_digest(digest)?;
        }
    }

    let mut bookmark_ids = BTreeSet::new();
    let mut bookmark_names = BTreeSet::new();
    for bookmark in &state.bookmarks {
        let section_index = exact_section_index(&state.sections, &bookmark.anchor.section_id)?;
        validate_bookmark(bookmark, &state.sections[section_index], limits)?;
        if !bookmark_ids.insert(&bookmark.identity.logical_bookmark_id) {
            return Err(LinkReferenceError::InvalidIdentity);
        }
        if !bookmark_names.insert(&bookmark.name) {
            return Err(LinkReferenceError::InvalidBookmarkName);
        }
    }

    let mut logical_ids = BTreeSet::new();
    let mut begin_ids = BTreeSet::new();
    let mut field_ids = BTreeSet::new();
    let mut anchors = BTreeSet::new();
    for hyperlink in &state.hyperlinks {
        let section_index = exact_section_index(&state.sections, &hyperlink.anchor.section_id)?;
        validate_hyperlink(
            hyperlink,
            &state.sections[section_index],
            &state.bookmarks,
            &state.external_link_policy,
            limits,
        )?;
        if !logical_ids.insert(&hyperlink.identity.logical_hyperlink_id)
            || !begin_ids.insert(hyperlink.identity.begin_control_id)
            || !field_ids.insert(hyperlink.identity.field_id)
            || state
                .occupied_non_hyperlink_begin_control_ids
                .binary_search(&hyperlink.identity.begin_control_id)
                .is_ok()
            || state
                .occupied_non_hyperlink_field_ids
                .binary_search(&hyperlink.identity.field_id)
                .is_ok()
            || !anchors.insert(&hyperlink.anchor)
        {
            return Err(LinkReferenceError::InvalidIdentity);
        }
    }
    Ok(())
}

fn invalid_native_id_inventory(ids: &[u32]) -> bool {
    ids.first().is_some_and(|identifier| *identifier == 0)
        || ids.windows(2).any(|pair| pair[0] >= pair[1])
}

fn validate_policy(
    policy: &ExternalLinkPolicy,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    require_digest(&policy.policy_revision_sha256)?;
    if policy.approvals.len() > limits.0.approvals
        || policy.approvals.windows(2).any(|pair| pair[0] >= pair[1])
    {
        return Err(LinkReferenceError::ExternalTargetDenied);
    }
    for approval in &policy.approvals {
        require_digest(&approval.target_sha256)?;
        let enabled = match approval.kind {
            ExternalTargetKind::Https => policy.allow_https,
            ExternalTargetKind::Mailto => policy.allow_mailto,
            ExternalTargetKind::ManagedDocument => policy.allow_managed_documents,
        };
        if !enabled {
            return Err(LinkReferenceError::ExternalTargetDenied);
        }
    }
    Ok(())
}

fn validate_bookmark(
    bookmark: &BookmarkEntry,
    section: &LinkReferenceSectionState,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    if !valid_bookmark_name(&bookmark.name, limits.0.name_bytes) {
        return Err(LinkReferenceError::InvalidBookmarkName);
    }
    validate_anchor(&bookmark.anchor, section)?;
    require_digest(&bookmark.opaque_native_payload_sha256)?;
    validate_opaque(&bookmark.opaque_properties, limits)
}

fn validate_hyperlink(
    hyperlink: &HyperlinkEntry,
    section: &LinkReferenceSectionState,
    bookmarks: &[BookmarkEntry],
    policy: &ExternalLinkPolicy,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    if hyperlink.identity.begin_control_id == 0
        || hyperlink.identity.field_id == 0
        || hyperlink.native_pair.begin_tag != HyperlinkNativeBeginTag::FieldBegin
        || hyperlink.native_pair.end_tag != HyperlinkNativeEndTag::FieldEnd
        || hyperlink.native_pair.field_type != HyperlinkFieldType::Hyperlink
        || !matches!(
            hyperlink.native_pair.semantic_binding,
            HyperlinkSemanticBinding::UnverifiedFieldParameters
                | HyperlinkSemanticBinding::Hangul2020HttpsCurrentTabV1
        )
        || hyperlink.native_pair.end_begin_control_id_ref != hyperlink.identity.begin_control_id
        || hyperlink.native_pair.end_field_id != hyperlink.identity.field_id
        || hyperlink.native_pair.z_order < -1
    {
        return Err(LinkReferenceError::InvalidNativeBinding);
    }
    if hyperlink.native_pair.semantic_binding
        == HyperlinkSemanticBinding::Hangul2020HttpsCurrentTabV1
        && !matches!(hyperlink.target, HyperlinkTarget::Https { .. })
    {
        return Err(LinkReferenceError::InvalidNativeBinding);
    }
    validate_anchor(&hyperlink.anchor, section)?;
    validate_target(&hyperlink.target, bookmarks, policy, limits)?;
    for digest in [
        Some(hyperlink.display_text_sha256.as_str()),
        hyperlink.native_pair.field_name_sha256.as_deref(),
        Some(hyperlink.native_pair.parameters_sha256.as_str()),
        hyperlink.native_pair.sub_list_sha256.as_deref(),
        hyperlink.native_pair.meta_tag_sha256.as_deref(),
        Some(hyperlink.native_pair.opaque_begin_state_sha256.as_str()),
        Some(hyperlink.native_pair.opaque_end_state_sha256.as_str()),
        Some(hyperlink.opaque_native_payload_sha256.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        require_digest(digest)?;
    }
    validate_opaque(&hyperlink.opaque_properties, limits)
}

fn validate_anchor(
    anchor: &LinkAnchor,
    section: &LinkReferenceSectionState,
) -> Result<(), LinkReferenceError> {
    if anchor.section_id != section.section_id
        || anchor.start > anchor.end
        || anchor.start.paragraph_ordinal >= section.paragraph_count
        || anchor.end.paragraph_ordinal >= section.paragraph_count
    {
        return Err(LinkReferenceError::InvalidIdentity);
    }
    Ok(())
}

fn validate_target(
    target: &HyperlinkTarget,
    bookmarks: &[BookmarkEntry],
    policy: &ExternalLinkPolicy,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    validate_target_shape(target, limits)?;
    if let HyperlinkTarget::InternalBookmark { bookmark_id } = target {
        if !bookmarks
            .iter()
            .any(|bookmark| &bookmark.identity.logical_bookmark_id == bookmark_id)
        {
            return Err(LinkReferenceError::DanglingReference);
        }
        return Ok(());
    }
    let kind = target
        .external_kind()
        .ok_or(LinkReferenceError::InvalidTarget)?;
    let enabled = match kind {
        ExternalTargetKind::Https => policy.allow_https,
        ExternalTargetKind::Mailto => policy.allow_mailto,
        ExternalTargetKind::ManagedDocument => policy.allow_managed_documents,
    };
    if !enabled {
        return Err(LinkReferenceError::ExternalTargetDenied);
    }
    let target_sha256 = target.external_approval_sha256(limits)?;
    if !policy
        .approvals
        .iter()
        .any(|approval| approval.kind == kind && approval.target_sha256 == target_sha256)
    {
        return Err(LinkReferenceError::ExternalTargetDenied);
    }
    Ok(())
}

fn validate_target_shape(
    target: &HyperlinkTarget,
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    let valid = match target {
        HyperlinkTarget::InternalBookmark { .. } => true,
        HyperlinkTarget::Https { uri } => valid_https(uri, limits.0.target_bytes),
        HyperlinkTarget::Mailto { address } => valid_mailto(address, limits.0.target_bytes),
        HyperlinkTarget::ManagedDocument {
            artifact_id,
            bookmark_name,
        } => {
            valid_token(artifact_id.as_str(), limits.0.target_bytes)
                && bookmark_name
                    .as_deref()
                    .is_none_or(|name| valid_bookmark_name(name, limits.0.name_bytes))
        }
    };
    if !valid {
        return Err(LinkReferenceError::InvalidTarget);
    }
    Ok(())
}

fn valid_https(value: &str, maximum: usize) -> bool {
    if value.len() > maximum
        || !value.is_ascii()
        || !value.starts_with("https://")
        || !valid_link_text(value, maximum)
    {
        return false;
    }
    let rest = &value[8..];
    let authority_end = rest.find(['/', '?', '#']).unwrap_or(rest.len());
    let (authority, suffix) = rest.split_at(authority_end);
    valid_https_authority(authority) && valid_uri_suffix(suffix)
}

fn valid_https_authority(authority: &str) -> bool {
    if authority.is_empty() || authority.contains('@') || authority.matches(':').count() > 1 {
        return false;
    }
    let (host, port) = authority
        .rsplit_once(':')
        .map_or((authority, None), |(host, port)| (host, Some(port)));
    if !valid_dns_name(host) {
        return false;
    }
    port.is_none_or(|value| {
        !value.is_empty()
            && value.bytes().all(|byte| byte.is_ascii_digit())
            && value.parse::<u16>().is_ok_and(|number| number != 0)
    })
}

fn valid_dns_name(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 253
        && value.split('.').all(|label| {
            !label.is_empty()
                && label.len() <= 63
                && label
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
                && label
                    .as_bytes()
                    .first()
                    .is_some_and(u8::is_ascii_alphanumeric)
                && label
                    .as_bytes()
                    .last()
                    .is_some_and(u8::is_ascii_alphanumeric)
        })
}

fn valid_uri_suffix(value: &str) -> bool {
    if value.matches('#').count() > 1 {
        return false;
    }
    let bytes = value.as_bytes();
    let mut index = 0;
    while index < bytes.len() {
        let byte = bytes[index];
        if byte == b'%' {
            if index + 2 >= bytes.len()
                || !bytes[index + 1].is_ascii_hexdigit()
                || !bytes[index + 2].is_ascii_hexdigit()
            {
                return false;
            }
            index += 3;
            continue;
        }
        if !(byte.is_ascii_alphanumeric()
            || matches!(
                byte,
                b'-' | b'.'
                    | b'_'
                    | b'~'
                    | b':'
                    | b'/'
                    | b'?'
                    | b'#'
                    | b'@'
                    | b'!'
                    | b'$'
                    | b'&'
                    | b'\''
                    | b'('
                    | b')'
                    | b'*'
                    | b'+'
                    | b','
                    | b';'
                    | b'='
            ))
        {
            return false;
        }
        index += 1;
    }
    true
}

fn valid_mailto(value: &str, maximum: usize) -> bool {
    if value.len() > maximum || !value.is_ascii() || !valid_link_text(value, maximum) {
        return false;
    }
    let mut parts = value.split('@');
    let local = parts.next().unwrap_or_default();
    let domain = parts.next().unwrap_or_default();
    !local.is_empty()
        && local.len() <= 64
        && !local.starts_with('.')
        && !local.ends_with('.')
        && !local.contains("..")
        && local.bytes().all(|byte| {
            byte.is_ascii_alphanumeric()
                || matches!(
                    byte,
                    b'!' | b'#'
                        | b'$'
                        | b'%'
                        | b'&'
                        | b'\''
                        | b'*'
                        | b'+'
                        | b'-'
                        | b'/'
                        | b'='
                        | b'?'
                        | b'^'
                        | b'_'
                        | b'`'
                        | b'{'
                        | b'|'
                        | b'}'
                        | b'~'
                        | b'.'
                )
        })
        && valid_dns_name(domain)
        && parts.next().is_none()
        && domain.contains('.')
        && !value.contains(':')
        && !value.contains('?')
        && !value.contains('#')
}

fn valid_link_text(value: &str, maximum: usize) -> bool {
    !value.is_empty()
        && value.len() <= maximum
        && !value.chars().any(char::is_whitespace)
        && !value.chars().any(char::is_control)
        && !value.contains('\\')
}

fn valid_bookmark_name(value: &str, maximum: usize) -> bool {
    !value.is_empty()
        && value.len() <= maximum
        && value.trim() == value
        && value.nfc().eq(value.chars())
        && !value
            .chars()
            .any(|character| character.is_control() || matches!(character, '#' | '/' | '\\' | '?'))
}

fn validate_opaque(
    properties: &[OpaqueLinkProperty],
    limits: LinkReferenceLimits,
) -> Result<(), LinkReferenceError> {
    if properties.len() > limits.0.opaque_entries {
        return Err(LinkReferenceError::InvalidPayload);
    }
    let mut keys = BTreeSet::new();
    for property in properties {
        if !valid_token(&property.namespace, limits.0.name_bytes)
            || !valid_token(&property.name, limits.0.name_bytes)
            || require_digest(&property.value_sha256).is_err()
            || !keys.insert((&property.namespace, &property.name))
        {
            return Err(LinkReferenceError::InvalidPayload);
        }
    }
    Ok(())
}

fn valid_token(value: &str, maximum: usize) -> bool {
    !value.is_empty()
        && value.len() <= maximum
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
}

fn require_digest(value: &str) -> Result<(), LinkReferenceError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(LinkReferenceError::InvalidPayload);
    }
    Ok(())
}

fn plan_binding_sha256(
    plan: &LinkReferencePlan,
    limits: LinkReferenceLimits,
) -> Result<String, LinkReferenceError> {
    #[derive(Serialize)]
    struct Binding<'a> {
        schema_version: &'static str,
        capability_id: &'static str,
        request_id: &'a LogicalId,
        source_state_sha256: &'a str,
        target_state_sha256: &'a str,
        source_document_flow_sha256: &'a str,
        target_document_flow_sha256: &'a str,
        operation: &'a LinkReferenceOperation,
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
    };
    Ok(hex(
        Sha256::digest(serialize_bounded(&binding, limits)?).into()
    ))
}

fn serialize_bounded<T: Serialize>(
    value: &T,
    limits: LinkReferenceLimits,
) -> Result<Vec<u8>, LinkReferenceError> {
    let bytes = serde_json::to_vec(value).map_err(|_| LinkReferenceError::Serialization)?;
    if bytes.len() > limits.0.output_bytes {
        return Err(LinkReferenceError::OutputLimit);
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

fn reject_duplicate_json_keys(bytes: &[u8]) -> Result<(), LinkReferenceError> {
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
        .map_err(|_| LinkReferenceError::InvalidJson)?;
    deserializer
        .end()
        .map_err(|_| LinkReferenceError::InvalidJson)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Private setup keeps sealed-plan tampering local.
mod private_tests {
    use super::*;

    const DIGEST: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    fn limits() -> LinkReferenceLimits {
        LinkReferenceLimits::new(LinkReferenceLimitConfig::default()).expect("limits")
    }

    fn section() -> LinkReferenceSectionState {
        LinkReferenceSectionState {
            section_id: LogicalId::parse("section-1").expect("id"),
            paragraph_count: 1,
            run_topology_sha256: DIGEST.to_owned(),
            inline_topology_sha256: DIGEST.to_owned(),
            opaque_section_state_sha256: DIGEST.to_owned(),
            locked: false,
        }
    }

    fn anchor() -> LinkAnchor {
        LinkAnchor {
            section_id: LogicalId::parse("section-1").expect("id"),
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
        }
    }

    fn bookmark() -> BookmarkEntry {
        BookmarkEntry {
            identity: BookmarkIdentity {
                logical_bookmark_id: LogicalId::parse("bookmark-1").expect("id"),
            },
            name: "chapter-one".to_owned(),
            anchor: anchor(),
            native_tag: BookmarkNativeTag::Bookmark,
            opaque_native_payload_sha256: DIGEST.to_owned(),
            opaque_properties: Vec::new(),
            locked: false,
        }
    }

    fn state() -> LinkReferenceDocumentState {
        LinkReferenceDocumentState::from_draft(
            LinkReferenceDocumentStateDraft {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
                sections: vec![section()],
                bookmarks: Vec::new(),
                hyperlinks: Vec::new(),
                occupied_non_hyperlink_begin_control_ids: Vec::new(),
                occupied_non_hyperlink_field_ids: Vec::new(),
                external_link_policy: ExternalLinkPolicy {
                    allow_https: false,
                    allow_mailto: false,
                    allow_managed_documents: false,
                    approvals: Vec::new(),
                    policy_revision_sha256: DIGEST.to_owned(),
                },
                non_reference_content_sha256: DIGEST.to_owned(),
                unrelated_field_inventory_sha256: DIGEST.to_owned(),
                style_catalog_sha256: DIGEST.to_owned(),
                object_inventory_sha256: DIGEST.to_owned(),
                relationship_inventory_sha256: DIGEST.to_owned(),
                resource_inventory_sha256: DIGEST.to_owned(),
                document_protection_sha256: DIGEST.to_owned(),
                opaque_document_state_sha256: DIGEST.to_owned(),
                document_locked: false,
            },
            limits(),
        )
        .expect("state")
    }

    #[test]
    fn private_plan_tampering_is_rejected() {
        let source = state();
        let request = LinkReferenceRequest::from_draft(
            LinkReferenceRequestDraft {
                schema_version: LINK_REFERENCE_SCHEMA_VERSION.to_owned(),
                request_id: LogicalId::parse("request-1").expect("id"),
                expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
                expected_document_flow_sha256: DIGEST.to_owned(),
                target_document_flow_sha256: DIGEST.to_owned(),
                operation: LinkReferenceOperation::InsertBookmark {
                    insertion_index: 0,
                    bookmark: bookmark(),
                },
            },
            &source,
            DIGEST,
            limits(),
        )
        .expect("request");
        let mut plan =
            LinkReferenceBuilder::plan(&source, &request, DIGEST, limits()).expect("plan");
        plan.capability_id = "ref.hyperlink_edit";
        assert_eq!(
            LinkReferenceBuilder::build(&plan, &source, DIGEST, limits()),
            Err(LinkReferenceError::PlanTampered)
        );
    }
}
