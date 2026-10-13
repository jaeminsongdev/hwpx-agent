use std::collections::BTreeMap;
use std::fmt::{self, Debug};
use std::io::{Cursor, Read, Seek, Write};

use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

use crate::id_index::allocation_declaration_kind;
use crate::{
    BoundedZipReader, Compression, GraphError, IdIndex, IdIndexError, IdIndexLimits, IdKind,
    IdRuleProfile, MediaType, PackageError, PackageGraph, PackageGraphLimits, PackageLimits,
    PackagePath, PartPreservationRecord, PreservationClass, PreservationError, PreservationReport,
    PreservationRuleProfile, PreservingXmlDocument, PreservingXmlError, XmlName, XmlQuoteStyle,
    XmlTokenKind,
};

const OPF_NAMESPACE: &str = "http://www.idpf.org/2007/opf";
const OPF_NAMESPACE_HANCOM_2020: &str = "http://www.idpf.org/2007/opf/";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PatchLimitConfig {
    pub max_intents: usize,
    pub max_changed_parts: usize,
    pub max_value_bytes: usize,
    pub max_fragment_bytes: usize,
    pub max_added_part_bytes: usize,
    pub max_total_output_growth: usize,
}

impl Default for PatchLimitConfig {
    fn default() -> Self {
        Self {
            max_intents: 4_096,
            max_changed_parts: 1_024,
            max_value_bytes: 1024 * 1024,
            max_fragment_bytes: 8 * 1024 * 1024,
            max_added_part_bytes: 64 * 1024 * 1024,
            max_total_output_growth: 128 * 1024 * 1024,
        }
    }
}

/// Validated, finite limits for a pure in-memory preserving patch transaction.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct PatchLimits(PatchLimitConfig);

impl PatchLimits {
    pub const HARD_MAX_INTENTS: usize = 65_536;
    pub const HARD_MAX_CHANGED_PARTS: usize = 16_384;
    pub const HARD_MAX_VALUE_BYTES: usize = 8 * 1024 * 1024;
    pub const HARD_MAX_FRAGMENT_BYTES: usize = 32 * 1024 * 1024;
    pub const HARD_MAX_ADDED_PART_BYTES: usize = 256 * 1024 * 1024;
    pub const HARD_MAX_TOTAL_OUTPUT_GROWTH: usize = 512 * 1024 * 1024;

    /// Validates caller limits without clamping.
    ///
    /// # Errors
    ///
    /// Returns a stable error for zero or over-ceiling values.
    pub fn new(config: PatchLimitConfig) -> Result<Self, PatchError> {
        let values = [
            ("max_intents", config.max_intents, Self::HARD_MAX_INTENTS),
            (
                "max_changed_parts",
                config.max_changed_parts,
                Self::HARD_MAX_CHANGED_PARTS,
            ),
            (
                "max_value_bytes",
                config.max_value_bytes,
                Self::HARD_MAX_VALUE_BYTES,
            ),
            (
                "max_fragment_bytes",
                config.max_fragment_bytes,
                Self::HARD_MAX_FRAGMENT_BYTES,
            ),
            (
                "max_added_part_bytes",
                config.max_added_part_bytes,
                Self::HARD_MAX_ADDED_PART_BYTES,
            ),
            (
                "max_total_output_growth",
                config.max_total_output_growth,
                Self::HARD_MAX_TOTAL_OUTPUT_GROWTH,
            ),
        ];
        for (field, value, ceiling) in values {
            if value == 0 || value > ceiling {
                return Err(PatchError::InvalidLimit {
                    field,
                    value,
                    ceiling,
                });
            }
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> PatchLimitConfig {
        self.0
    }
}

/// An XML 1.0 semantic string. Its value is intentionally absent from `Debug`.
#[derive(Clone, Eq, Ord, PartialEq, PartialOrd)]
pub struct PatchText(String);

impl Debug for PatchText {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PatchText")
            .field("utf8_bytes", &self.0.len())
            .finish()
    }
}

impl PatchText {
    /// Validates a semantic XML 1.0 value. Transaction limits are rechecked at apply time.
    ///
    /// # Errors
    ///
    /// Returns `patch_value_invalid` for a forbidden XML character.
    pub fn new(value: &str) -> Result<Self, PatchError> {
        if value.len() > PatchLimits::HARD_MAX_VALUE_BYTES || !value.chars().all(xml10_character) {
            return Err(PatchError::ValueInvalid);
        }
        Ok(Self(value.to_owned()))
    }

    fn value(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct AllocationHandle(u32);

impl AllocationHandle {
    #[must_use]
    pub const fn new(value: u32) -> Self {
        Self(value)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PatchAttributeValue {
    Text(PatchText),
    Allocated(AllocationHandle),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct XmlElementSelector {
    part: PackagePath,
    source_sha256: [u8; 32],
    element_index: usize,
    expected_name: XmlName,
}

impl XmlElementSelector {
    /// Binds a selector to an already validated immutable token document.
    ///
    /// # Errors
    ///
    /// Returns a stable range error if `element_index` does not exist.
    pub fn bind(
        part: &PackagePath,
        document: &PreservingXmlDocument,
        element_index: usize,
    ) -> Result<Self, PatchError> {
        let expected_name = document
            .elements()
            .get(element_index)
            .ok_or(PatchError::SelectorOutOfRange)?
            .name()
            .clone();
        Ok(Self {
            part: part.clone(),
            source_sha256: document.original_sha256(),
            element_index,
            expected_name,
        })
    }

    #[must_use]
    pub const fn part(&self) -> &PackagePath {
        &self.part
    }

    #[must_use]
    pub const fn element_index(&self) -> usize {
        self.element_index
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct XmlAttributeSelector {
    element: XmlElementSelector,
    attribute_index: usize,
    expected_name: XmlName,
}

impl XmlAttributeSelector {
    /// Binds an attribute selector without accepting a byte offset.
    ///
    /// # Errors
    ///
    /// Returns a stable range error if either index does not exist.
    pub fn bind(
        part: &PackagePath,
        document: &PreservingXmlDocument,
        element_index: usize,
        attribute_index: usize,
    ) -> Result<Self, PatchError> {
        let element = XmlElementSelector::bind(part, document, element_index)?;
        let expected_name = document
            .elements()
            .get(element_index)
            .and_then(|value| value.attributes().get(attribute_index))
            .ok_or(PatchError::SelectorOutOfRange)?
            .name()
            .clone();
        Ok(Self {
            element,
            attribute_index,
            expected_name,
        })
    }

    #[must_use]
    pub const fn element(&self) -> &XmlElementSelector {
        &self.element
    }

    #[must_use]
    pub const fn attribute_index(&self) -> usize {
        self.attribute_index
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct XmlTextSelector {
    part: PackagePath,
    source_sha256: [u8; 32],
    token_index: usize,
    expected_element_index: Option<usize>,
    expected_kind: XmlTokenKind,
}

impl XmlTextSelector {
    /// Binds only an existing `Text` or `Whitespace` token.
    ///
    /// # Errors
    ///
    /// Returns a stable selector-kind/range error for markup, references, or absent tokens.
    pub fn bind(
        part: &PackagePath,
        document: &PreservingXmlDocument,
        token_index: usize,
    ) -> Result<Self, PatchError> {
        let token = document
            .tokens()
            .get(token_index)
            .ok_or(PatchError::SelectorOutOfRange)?;
        if !matches!(token.kind(), XmlTokenKind::Text | XmlTokenKind::Whitespace) {
            return Err(PatchError::SelectorKind);
        }
        Ok(Self {
            part: part.clone(),
            source_sha256: document.original_sha256(),
            token_index,
            expected_element_index: token.element_index(),
            expected_kind: token.kind(),
        })
    }

    #[must_use]
    pub const fn part(&self) -> &PackagePath {
        &self.part
    }

    #[must_use]
    pub const fn token_index(&self) -> usize {
        self.token_index
    }
}

/// A single-root, declaration-free XML fragment validated by P03-03/P03-04.
#[derive(Clone, Eq, PartialEq)]
pub struct ValidatedXmlFragment {
    bytes: Box<[u8]>,
    sha256: [u8; 32],
}

impl Debug for ValidatedXmlFragment {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ValidatedXmlFragment")
            .field("bytes", &self.bytes.len())
            .field("sha256", &self.sha256)
            .finish()
    }
}

impl ValidatedXmlFragment {
    /// Parses a bounded standalone element fragment. XML declarations, BOMs and surrounding
    /// bytes are rejected so insertion cannot smuggle a document-level construct.
    ///
    /// # Errors
    ///
    /// Returns a stable fragment error when the value is unsafe or not exactly one element.
    pub fn parse(bytes: &[u8], limits: PatchLimits) -> Result<Self, PatchError> {
        if bytes.is_empty() || bytes.len() > limits.config().max_fragment_bytes {
            return Err(PatchError::LimitExceeded {
                limit: "fragment_bytes",
            });
        }
        let document = PreservingXmlDocument::parse(bytes)?;
        if document.tokens().iter().any(|token| {
            matches!(
                token.kind(),
                XmlTokenKind::ByteOrderMark | XmlTokenKind::Declaration
            )
        }) {
            return Err(PatchError::FragmentInvalid);
        }
        let root = document
            .elements()
            .get(document.root_element())
            .and_then(crate::XmlElementToken::outer_span)
            .ok_or(PatchError::FragmentInvalid)?;
        if root.start() != 0 || root.end() != bytes.len() {
            return Err(PatchError::FragmentInvalid);
        }
        Ok(Self {
            bytes: bytes.to_vec().into_boxed_slice(),
            sha256: document.original_sha256(),
        })
    }

    fn bytes(&self) -> &[u8] {
        &self.bytes
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SiblingPosition {
    Before,
    After,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RelationshipSpine {
    NotInSpine,
    Linear,
    NonLinear,
}

#[derive(Clone, Eq, PartialEq)]
pub struct RelationshipAddition {
    id: PatchText,
    target: PackagePath,
    media_type: MediaType,
    spine: RelationshipSpine,
}

impl Debug for RelationshipAddition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("RelationshipAddition")
            .field("id_bytes", &self.id.0.len())
            .field("target", &self.target)
            .field("media_type", &self.media_type)
            .field("spine", &self.spine)
            .finish()
    }
}

impl RelationshipAddition {
    /// Creates one typed OPF manifest relationship for an internal package target.
    ///
    /// # Errors
    ///
    /// Returns a stable path/media/value/limit error for invalid input.
    pub fn new(
        id: &str,
        target: &str,
        media_type: &str,
        spine: RelationshipSpine,
        package_limits: PackageLimits,
        graph_limits: PackageGraphLimits,
        patch_limits: PatchLimits,
    ) -> Result<Self, PatchError> {
        if id.len() > patch_limits.config().max_value_bytes || !valid_text_id(id) {
            return Err(PatchError::ValueInvalid);
        }
        let target = PackagePath::parse(target.as_bytes(), 0, package_limits)?;
        if target.is_directory() {
            return Err(PatchError::PartPathInvalid);
        }
        Ok(Self {
            id: PatchText::new(id)?,
            target,
            media_type: MediaType::parse(media_type, graph_limits)?,
            spine,
        })
    }

    #[must_use]
    pub const fn target(&self) -> &PackagePath {
        &self.target
    }

    #[must_use]
    pub const fn media_type(&self) -> &MediaType {
        &self.media_type
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct AddedPart {
    path: PackagePath,
    media_type: MediaType,
    bytes: Box<[u8]>,
}

impl Debug for AddedPart {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AddedPart")
            .field("path", &self.path)
            .field("media_type", &self.media_type)
            .field("bytes", &self.bytes.len())
            .finish()
    }
}

impl AddedPart {
    /// Creates a bounded, fully safe XML part without exposing its bytes later.
    ///
    /// # Errors
    ///
    /// Returns a stable path/media/XML/limit error.
    pub fn xml(
        path: &str,
        media_type: &str,
        bytes: &[u8],
        package_limits: PackageLimits,
        graph_limits: PackageGraphLimits,
        patch_limits: PatchLimits,
    ) -> Result<Self, PatchError> {
        if bytes.is_empty() || bytes.len() > patch_limits.config().max_added_part_bytes {
            return Err(PatchError::LimitExceeded {
                limit: "added_part_bytes",
            });
        }
        let media_type = MediaType::parse(media_type, graph_limits)?;
        if !media_is_xml(media_type.as_str()) {
            return Err(PatchError::PartContentInvalid);
        }
        let document = PreservingXmlDocument::parse(bytes)?;
        document.verify_untouched_round_trip()?;
        let path = PackagePath::parse(path.as_bytes(), 0, package_limits)?;
        if path.is_directory() {
            return Err(PatchError::PartPathInvalid);
        }
        Ok(Self {
            path,
            media_type,
            bytes: bytes.to_vec().into_boxed_slice(),
        })
    }

    /// Creates a bounded opaque part. XML-looking bytes and known signature mismatches fail closed.
    ///
    /// # Errors
    ///
    /// Returns a stable path/media/content/limit error.
    pub fn opaque(
        path: &str,
        media_type: &str,
        bytes: &[u8],
        package_limits: PackageLimits,
        graph_limits: PackageGraphLimits,
        patch_limits: PatchLimits,
    ) -> Result<Self, PatchError> {
        if bytes.is_empty() || bytes.len() > patch_limits.config().max_added_part_bytes {
            return Err(PatchError::LimitExceeded {
                limit: "added_part_bytes",
            });
        }
        let media_type = MediaType::parse(media_type, graph_limits)?;
        if media_is_xml(media_type.as_str())
            || content_looks_xml(bytes)
            || binary_signature_matches(media_type.as_str(), bytes) == Some(false)
        {
            return Err(PatchError::PartContentInvalid);
        }
        let path = PackagePath::parse(path.as_bytes(), 0, package_limits)?;
        if path.is_directory() {
            return Err(PatchError::PartPathInvalid);
        }
        Ok(Self {
            path,
            media_type,
            bytes: bytes.to_vec().into_boxed_slice(),
        })
    }

    #[must_use]
    pub const fn path(&self) -> &PackagePath {
        &self.path
    }

    #[must_use]
    pub const fn media_type(&self) -> &MediaType {
        &self.media_type
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum PatchIntent {
    ReplaceAttribute {
        target: XmlAttributeSelector,
        value: PatchAttributeValue,
    },
    ReplaceText {
        target: XmlTextSelector,
        value: PatchText,
    },
    InsertSibling {
        target: XmlElementSelector,
        position: SiblingPosition,
        fragment: ValidatedXmlFragment,
    },
    DeleteSubtree {
        target: XmlElementSelector,
    },
    ReplaceSubtree {
        target: XmlElementSelector,
        fragment: ValidatedXmlFragment,
    },
    /// Replace only element content; retain its original start/end tags and attributes.
    /// Children remain independently safe, namespace-complete validated elements.
    ReplaceElementContent {
        target: XmlElementSelector,
        children: Vec<ValidatedXmlFragment>,
    },
    AllocateId {
        target: XmlAttributeSelector,
        kind: IdKind,
        handle: AllocationHandle,
    },
    AddRelationship {
        relationship: RelationshipAddition,
    },
    AddPart {
        part: AddedPart,
    },
}

impl Debug for PatchIntent {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ReplaceAttribute { target, value } => formatter
                .debug_struct("ReplaceAttribute")
                .field("target", target)
                .field("value", value)
                .finish(),
            Self::ReplaceText { target, value } => formatter
                .debug_struct("ReplaceText")
                .field("target", target)
                .field("value", value)
                .finish(),
            Self::InsertSibling {
                target,
                position,
                fragment,
            } => formatter
                .debug_struct("InsertSibling")
                .field("target", target)
                .field("position", position)
                .field("fragment", fragment)
                .finish(),
            Self::DeleteSubtree { target } => formatter
                .debug_struct("DeleteSubtree")
                .field("target", target)
                .finish(),
            Self::ReplaceSubtree { target, fragment } => formatter
                .debug_struct("ReplaceSubtree")
                .field("target", target)
                .field("fragment", fragment)
                .finish(),
            Self::ReplaceElementContent { target, children } => formatter
                .debug_struct("ReplaceElementContent")
                .field("target", target)
                .field("child_count", &children.len())
                .finish(),
            Self::AllocateId {
                target,
                kind,
                handle,
            } => formatter
                .debug_struct("AllocateId")
                .field("target", target)
                .field("kind", kind)
                .field("handle", handle)
                .finish(),
            Self::AddRelationship { relationship } => formatter
                .debug_struct("AddRelationship")
                .field("relationship", relationship)
                .finish(),
            Self::AddPart { part } => formatter
                .debug_struct("AddPart")
                .field("part", part)
                .finish(),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PatchPartDisposition {
    Untouched,
    Changed,
    Added,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PatchPartRecord {
    path: PackagePath,
    disposition: PatchPartDisposition,
    source_sha256: Option<[u8; 32]>,
    output_sha256: [u8; 32],
    output_bytes: usize,
}

impl PatchPartRecord {
    #[must_use]
    pub const fn path(&self) -> &PackagePath {
        &self.path
    }

    #[must_use]
    pub const fn disposition(&self) -> PatchPartDisposition {
        self.disposition
    }

    #[must_use]
    pub const fn source_sha256(&self) -> Option<[u8; 32]> {
        self.source_sha256
    }

    #[must_use]
    pub const fn output_sha256(&self) -> [u8; 32] {
        self.output_sha256
    }

    #[must_use]
    pub const fn output_bytes(&self) -> usize {
        self.output_bytes
    }
}

pub struct PatchResult {
    pub(crate) profile: IdRuleProfile,
    pub(crate) preservation_profile: PreservationRuleProfile,
    profile_version: &'static str,
    intent_count: usize,
    records: Vec<PatchPartRecord>,
    untouched_parts: usize,
    changed_parts: usize,
    added_parts: usize,
    allocation_count: usize,
    relationship_count: usize,
    declaration_count: usize,
    reference_count: usize,
    pub(crate) parts: Vec<VirtualPart>,
}

impl Debug for PatchResult {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PatchResult")
            .field("profile_version", &self.profile_version)
            .field("preservation_profile", &self.preservation_profile)
            .field("intent_count", &self.intent_count)
            .field("records", &self.records)
            .field("untouched_parts", &self.untouched_parts)
            .field("changed_parts", &self.changed_parts)
            .field("added_parts", &self.added_parts)
            .field("allocation_count", &self.allocation_count)
            .field("relationship_count", &self.relationship_count)
            .field("declaration_count", &self.declaration_count)
            .field("reference_count", &self.reference_count)
            .finish_non_exhaustive()
    }
}

impl PatchResult {
    #[must_use]
    pub const fn profile_version(&self) -> &'static str {
        self.profile_version
    }

    #[must_use]
    pub const fn intent_count(&self) -> usize {
        self.intent_count
    }

    #[must_use]
    pub fn parts(&self) -> &[PatchPartRecord] {
        &self.records
    }

    #[must_use]
    pub const fn untouched_parts(&self) -> usize {
        self.untouched_parts
    }

    #[must_use]
    pub const fn changed_parts(&self) -> usize {
        self.changed_parts
    }

    #[must_use]
    pub const fn added_parts(&self) -> usize {
        self.added_parts
    }

    #[must_use]
    pub const fn allocation_count(&self) -> usize {
        self.allocation_count
    }

    #[must_use]
    pub const fn relationship_count(&self) -> usize {
        self.relationship_count
    }

    #[must_use]
    pub const fn declaration_count(&self) -> usize {
        self.declaration_count
    }

    #[must_use]
    pub const fn reference_count(&self) -> usize {
        self.reference_count
    }

    /// Recomputes non-sensitive path/size/hash records over the private in-memory artifact.
    /// It never publishes the underlying part bytes.
    ///
    /// # Errors
    ///
    /// Returns a stable mismatch if any private output part diverges from its public record.
    pub fn verify_artifact_integrity(&self) -> Result<(), PatchError> {
        if self.parts.len() != self.records.len() {
            return Err(PatchError::ValidationMismatch);
        }
        for (part, record) in self.parts.iter().zip(&self.records) {
            if part.path != record.path
                || part.bytes.len() != record.output_bytes
                || <[u8; 32]>::from(Sha256::digest(&part.bytes)) != record.output_sha256
            {
                return Err(PatchError::ValidationMismatch);
            }
        }
        Ok(())
    }
}

#[derive(Debug)]
pub struct PreservingPatchEngine;

impl PreservingPatchEngine {
    /// Applies a pure in-memory transaction with all default finite limits.
    ///
    /// # Errors
    ///
    /// Returns no partial result when admission, planning, conflict, reparse, graph,
    /// preservation or ID validation fails.
    pub fn apply<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        intents: &[PatchIntent],
    ) -> Result<PatchResult, PatchError> {
        Self::apply_with_limits(
            reader,
            graph,
            PackageGraphLimits::default(),
            IdRuleProfile::current_hancom_2020_core_v1(),
            IdIndexLimits::default(),
            PatchLimits::default(),
            intents,
        )
    }

    /// Applies a pure in-memory transaction with explicit validated limits and profile.
    ///
    /// # Errors
    ///
    /// Returns the same fail-closed errors as [`Self::apply`].
    pub fn apply_with_limits<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        graph_limits: PackageGraphLimits,
        id_profile: IdRuleProfile,
        id_limits: IdIndexLimits,
        patch_limits: PatchLimits,
        intents: &[PatchIntent],
    ) -> Result<PatchResult, PatchError> {
        Self::apply_with_limits_and_preservation_profile(
            reader,
            graph,
            graph_limits,
            id_profile,
            id_limits,
            patch_limits,
            PreservationRuleProfile::CoreV1,
            intents,
        )
    }

    /// Applies a pure in-memory transaction under an explicit source-preservation profile.
    ///
    /// # Errors
    ///
    /// Returns the same fail-closed errors as [`Self::apply`].
    #[allow(clippy::too_many_arguments)]
    pub fn apply_with_limits_and_preservation_profile<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        graph_limits: PackageGraphLimits,
        id_profile: IdRuleProfile,
        id_limits: IdIndexLimits,
        patch_limits: PatchLimits,
        preservation_profile: PreservationRuleProfile,
        intents: &[PatchIntent],
    ) -> Result<PatchResult, PatchError> {
        if intents.len() > patch_limits.config().max_intents {
            return Err(PatchError::LimitExceeded { limit: "intents" });
        }
        let package_limits = reader.package_limits();
        let preservation = PreservationReport::build_with_graph_limits_and_profile(
            reader,
            graph,
            graph_limits,
            preservation_profile,
        )?;
        if !preservation.direct_preserve_ready() {
            return Err(PatchError::PreservationRejected);
        }
        let id_index =
            IdIndex::build_with_graph_limits(reader, graph, graph_limits, id_profile, id_limits)?;
        Transaction::new(
            reader,
            graph,
            &preservation,
            &id_index,
            graph_limits,
            id_profile,
            id_limits,
            patch_limits,
            preservation_profile,
            package_limits,
            intents,
        )?
        .execute()
    }
}

#[derive(Debug, Error)]
pub enum PatchError {
    #[error("bounded package read failed while patching")]
    Package(#[from] PackageError),
    #[error("package graph validation failed while patching")]
    Graph(#[from] GraphError),
    #[error("preservation validation failed while patching")]
    Preservation(#[from] PreservationError),
    #[error("preserving XML validation failed while patching")]
    Token(#[from] PreservingXmlError),
    #[error("ID/reference validation failed while patching")]
    IdIndex(#[from] IdIndexError),
    #[error("invalid patch limit {field}: {value} (ceiling {ceiling})")]
    InvalidLimit {
        field: &'static str,
        value: usize,
        ceiling: usize,
    },
    #[error("patch transaction exceeded the {limit} limit")]
    LimitExceeded { limit: &'static str },
    #[error("patch selector is out of range")]
    SelectorOutOfRange,
    #[error("patch selector is bound to an unsupported token kind")]
    SelectorKind,
    #[error("patch selector is stale or belongs to another source")]
    SelectorStale,
    #[error("patch target is missing")]
    TargetMissing,
    #[error("patch target is not a token-stable XML part")]
    TargetNotTokenStable,
    #[error("root/sibling mutation would violate the XML document boundary")]
    RootMutation,
    #[error("patch intents conflict at checked source ranges")]
    Conflict,
    #[error("patch semantic value is invalid")]
    ValueInvalid,
    #[error("validated XML fragment is invalid")]
    FragmentInvalid,
    #[error("new part content is invalid for its media type")]
    PartContentInvalid,
    #[error("new part or relationship target must be a non-directory package path")]
    PartPathInvalid,
    #[error("new part path already exists or is duplicated")]
    PartCollision,
    #[error("new part is not paired with exactly one relationship")]
    PartRelationshipMismatch,
    #[error("relationship target is missing")]
    RelationshipTargetMissing,
    #[error("relationship and new part media types differ")]
    RelationshipMediaMismatch,
    #[error("relationship container is missing, duplicated, or empty")]
    RelationshipContainerInvalid,
    #[error("ID allocation handle is duplicated or missing")]
    AllocationHandleInvalid,
    #[error("ID allocation target/kind is unsupported")]
    AllocationTargetInvalid,
    #[error("patch allocation failed")]
    AllocationFailed,
    #[error("in-memory validation archive construction failed")]
    ValidationArchive,
    #[error("post-patch validation changed the planned part set")]
    ValidationMismatch,
    #[error("package contains a rejected preservation part")]
    PreservationRejected,
}

impl PatchError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::Package(error) => error.code(),
            Self::Graph(error) => error.code(),
            Self::Preservation(error) => error.code(),
            Self::Token(error) => error.code(),
            Self::IdIndex(error) => error.code(),
            Self::InvalidLimit { .. } => "patch_invalid_limit",
            Self::LimitExceeded { .. } => "patch_limit_exceeded",
            Self::SelectorOutOfRange => "patch_selector_out_of_range",
            Self::SelectorKind => "patch_selector_kind",
            Self::SelectorStale => "patch_selector_stale",
            Self::TargetMissing => "patch_target_missing",
            Self::TargetNotTokenStable => "patch_target_not_token_stable",
            Self::RootMutation => "patch_root_mutation",
            Self::Conflict => "patch_conflict",
            Self::ValueInvalid => "patch_value_invalid",
            Self::FragmentInvalid => "patch_fragment_invalid",
            Self::PartContentInvalid => "patch_part_content_invalid",
            Self::PartPathInvalid => "patch_part_path_invalid",
            Self::PartCollision => "patch_part_collision",
            Self::PartRelationshipMismatch => "patch_part_relationship_mismatch",
            Self::RelationshipTargetMissing => "patch_relationship_target_missing",
            Self::RelationshipMediaMismatch => "patch_relationship_media_mismatch",
            Self::RelationshipContainerInvalid => "patch_relationship_container_invalid",
            Self::AllocationHandleInvalid => "patch_allocation_handle_invalid",
            Self::AllocationTargetInvalid => "patch_allocation_target_invalid",
            Self::AllocationFailed => "patch_allocation_failed",
            Self::ValidationArchive => "patch_validation_archive_failed",
            Self::ValidationMismatch => "patch_validation_mismatch",
            Self::PreservationRejected => "patch_preservation_rejected",
        }
    }
}

struct Transaction<'a> {
    graph: &'a PackageGraph,
    preservation: &'a PreservationReport,
    id_index: &'a IdIndex,
    graph_limits: PackageGraphLimits,
    id_profile: IdRuleProfile,
    id_limits: IdIndexLimits,
    patch_limits: PatchLimits,
    preservation_profile: PreservationRuleProfile,
    package_limits: PackageLimits,
    intents: &'a [PatchIntent],
    parts: BTreeMap<String, VirtualPart>,
    documents: BTreeMap<String, PreservingXmlDocument>,
    output_growth: usize,
}

impl<'a> Transaction<'a> {
    #[allow(clippy::too_many_arguments)]
    fn new<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &'a PackageGraph,
        preservation: &'a PreservationReport,
        id_index: &'a IdIndex,
        graph_limits: PackageGraphLimits,
        id_profile: IdRuleProfile,
        id_limits: IdIndexLimits,
        patch_limits: PatchLimits,
        preservation_profile: PreservationRuleProfile,
        package_limits: PackageLimits,
        intents: &'a [PatchIntent],
    ) -> Result<Self, PatchError> {
        let mut parts = BTreeMap::new();
        let mut documents = BTreeMap::new();
        for record in preservation.parts() {
            let bytes = reader.read_entry(record.source_entry_index())?;
            if <[u8; 32]>::from(Sha256::digest(&bytes)) != record.raw_sha256() {
                return Err(PatchError::SelectorStale);
            }
            if record.class() == PreservationClass::TokenStable {
                let document = PreservingXmlDocument::parse(&bytes)?;
                if document.original_sha256() != record.raw_sha256() {
                    return Err(PatchError::SelectorStale);
                }
                documents.insert(record.path().collision_key().to_owned(), document);
            }
            let graph_part = graph
                .parts
                .iter()
                .find(|part| part.path == *record.path())
                .ok_or(PatchError::ValidationMismatch)?;
            if parts
                .insert(
                    record.path().collision_key().to_owned(),
                    VirtualPart {
                        path: record.path().clone(),
                        media_type: graph_part.media_type.clone(),
                        compression: record.compression(),
                        source_order: record.source_entry_index(),
                        source_sha256: Some(record.raw_sha256()),
                        bytes,
                    },
                )
                .is_some()
            {
                return Err(PatchError::ValidationMismatch);
            }
        }
        Ok(Self {
            graph,
            preservation,
            id_index,
            graph_limits,
            id_profile,
            id_limits,
            patch_limits,
            preservation_profile,
            package_limits,
            intents,
            parts,
            documents,
            output_growth: 0,
        })
    }

    fn execute(mut self) -> Result<PatchResult, PatchError> {
        let additions = self.validate_additions()?;
        let allocations = self.plan_allocations()?;
        let mut edits = self.plan_edits(&allocations)?;
        validate_conflicts(&mut edits)?;
        self.apply_edits(edits)?;
        self.install_added_parts(additions)?;
        self.reparse_changed_xml()?;
        self.finish_validation(allocations.len())
    }

    fn validate_additions(&self) -> Result<Vec<AddedPart>, PatchError> {
        let mut additions = BTreeMap::new();
        let mut relationship_counts = BTreeMap::<String, usize>::new();
        let mut relationship_media = BTreeMap::<String, &MediaType>::new();
        for intent in self.intents {
            match intent {
                PatchIntent::AddPart { part } => {
                    self.validate_added_part_limits(part)?;
                    let key = part.path.collision_key().to_owned();
                    if self.parts.contains_key(&key) || additions.insert(key, part).is_some() {
                        return Err(PatchError::PartCollision);
                    }
                }
                PatchIntent::AddRelationship { relationship } => {
                    self.validate_relationship_limits(relationship)?;
                    let key = relationship.target.collision_key().to_owned();
                    *relationship_counts.entry(key.clone()).or_default() += 1;
                    relationship_media.insert(key, &relationship.media_type);
                }
                _ => {}
            }
        }
        for (key, part) in &additions {
            if relationship_counts.get(key) != Some(&1) {
                return Err(PatchError::PartRelationshipMismatch);
            }
            if relationship_media.get(key).copied() != Some(&part.media_type) {
                return Err(PatchError::RelationshipMediaMismatch);
            }
        }
        for intent in self.intents {
            if let PatchIntent::AddRelationship { relationship } = intent {
                let key = relationship.target.collision_key();
                if !self.parts.contains_key(key) && !additions.contains_key(key) {
                    return Err(PatchError::RelationshipTargetMissing);
                }
            }
        }
        Ok(additions.into_values().cloned().collect())
    }

    fn validate_added_part_limits(&self, part: &AddedPart) -> Result<(), PatchError> {
        if part.bytes.len() > self.patch_limits.config().max_added_part_bytes {
            return Err(PatchError::LimitExceeded {
                limit: "added_part_bytes",
            });
        }
        let path = PackagePath::parse(part.path.as_str().as_bytes(), 0, self.package_limits)?;
        let media_type = MediaType::parse(part.media_type.as_str(), self.graph_limits)?;
        if path != part.path || path.is_directory() || media_type != part.media_type {
            return Err(PatchError::PartPathInvalid);
        }
        Ok(())
    }

    fn validate_relationship_limits(
        &self,
        relationship: &RelationshipAddition,
    ) -> Result<(), PatchError> {
        self.check_value_limit(relationship.id.0.len())?;
        let target = PackagePath::parse(
            relationship.target.as_str().as_bytes(),
            0,
            self.package_limits,
        )?;
        let media_type = MediaType::parse(relationship.media_type.as_str(), self.graph_limits)?;
        if target != relationship.target
            || target.is_directory()
            || media_type != relationship.media_type
        {
            return Err(PatchError::PartPathInvalid);
        }
        Ok(())
    }

    fn plan_allocations(&self) -> Result<BTreeMap<AllocationHandle, u64>, PatchError> {
        let mut requests = Vec::new();
        for intent in self.intents {
            if let PatchIntent::AllocateId {
                target,
                kind,
                handle,
            } = intent
            {
                let (record, document) = self.attribute_context(target)?;
                let matched = allocation_declaration_kind(
                    self.graph,
                    record,
                    document,
                    target.element.element_index,
                    target.attribute_index,
                    self.id_profile,
                )?;
                if matched != Some((*kind, true)) {
                    return Err(PatchError::AllocationTargetInvalid);
                }
                requests.push((
                    target.element.part.collision_key().to_owned(),
                    target.element.part.clone(),
                    *kind,
                    *handle,
                ));
            }
        }
        requests
            .sort_by(|left, right| (&left.0, left.2, left.3).cmp(&(&right.0, right.2, right.3)));
        let mut next_by_namespace = BTreeMap::<(String, IdKind), u64>::new();
        let mut allocations = BTreeMap::new();
        for (key, part, kind, handle) in requests {
            if allocations.contains_key(&handle) {
                return Err(PatchError::AllocationHandleInvalid);
            }
            let next = match next_by_namespace.get(&(key.clone(), kind)).copied() {
                Some(value) => value,
                None => self.id_index.next_decimal_value(&part, kind)?,
            };
            allocations.insert(handle, next);
            let following = next.checked_add(1).ok_or(PatchError::AllocationFailed)?;
            next_by_namespace.insert((key, kind), following);
        }
        Ok(allocations)
    }

    fn plan_edits(
        &self,
        allocations: &BTreeMap<AllocationHandle, u64>,
    ) -> Result<Vec<ByteEdit>, PatchError> {
        let mut edits = Vec::new();
        edits
            .try_reserve_exact(self.intents.len())
            .map_err(|_| PatchError::AllocationFailed)?;
        for (origin, intent) in self.intents.iter().enumerate() {
            match intent {
                PatchIntent::ReplaceAttribute { target, value } => {
                    self.plan_attribute_edit(target, value, allocations, origin, &mut edits)?;
                }
                PatchIntent::ReplaceText { target, value } => {
                    self.plan_text_edit(target, value, origin, &mut edits)?;
                }
                PatchIntent::InsertSibling {
                    target,
                    position,
                    fragment,
                } => {
                    self.plan_sibling_edit(target, *position, fragment, origin, &mut edits)?;
                }
                PatchIntent::DeleteSubtree { target } => {
                    self.plan_delete_edit(target, origin, &mut edits)?;
                }
                PatchIntent::ReplaceSubtree { target, fragment } => {
                    self.plan_subtree_edit(target, fragment, origin, &mut edits)?;
                }
                PatchIntent::ReplaceElementContent { target, children } => {
                    self.plan_content_edit(target, children, origin, &mut edits)?;
                }
                PatchIntent::AllocateId { target, handle, .. } => {
                    self.plan_allocation_edit(target, *handle, allocations, origin, &mut edits)?;
                }
                PatchIntent::AddRelationship { relationship } => {
                    self.plan_relationship_edits(relationship, origin, &mut edits)?;
                }
                PatchIntent::AddPart { .. } => {}
            }
        }
        Ok(edits)
    }

    fn plan_attribute_edit(
        &self,
        target: &XmlAttributeSelector,
        value: &PatchAttributeValue,
        allocations: &BTreeMap<AllocationHandle, u64>,
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        let (_, document) = self.attribute_context(target)?;
        let attribute =
            &document.elements()[target.element.element_index].attributes()[target.attribute_index];
        let raw = match value {
            PatchAttributeValue::Text(text) => text.value().to_owned(),
            PatchAttributeValue::Allocated(handle) => allocations
                .get(handle)
                .ok_or(PatchError::AllocationHandleInvalid)?
                .to_string(),
        };
        self.check_value_limit(raw.len())?;
        edits.push(ByteEdit::new(
            target.element.part.collision_key(),
            attribute.value_span().start(),
            attribute.value_span().end(),
            escape_attribute(&raw, attribute.quote_style())?.into_bytes(),
            origin,
        ));
        Ok(())
    }

    fn plan_text_edit(
        &self,
        target: &XmlTextSelector,
        value: &PatchText,
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        self.check_value_limit(value.0.len())?;
        let document = self.text_context(target)?;
        let token = &document.tokens()[target.token_index];
        edits.push(ByteEdit::new(
            target.part.collision_key(),
            token.span().start(),
            token.span().end(),
            escape_text(value.value())?.into_bytes(),
            origin,
        ));
        Ok(())
    }

    fn plan_sibling_edit(
        &self,
        target: &XmlElementSelector,
        position: SiblingPosition,
        fragment: &ValidatedXmlFragment,
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        self.check_fragment_limit(fragment)?;
        let document = self.element_context(target)?;
        let element = &document.elements()[target.element_index];
        if element.parent().is_none() {
            return Err(PatchError::RootMutation);
        }
        let outer = element.outer_span().ok_or(PatchError::SelectorStale)?;
        let at = match position {
            SiblingPosition::Before => outer.start(),
            SiblingPosition::After => outer.end(),
        };
        edits.push(ByteEdit::new(
            target.part.collision_key(),
            at,
            at,
            fragment.bytes().to_vec(),
            origin,
        ));
        Ok(())
    }

    fn plan_delete_edit(
        &self,
        target: &XmlElementSelector,
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        let document = self.element_context(target)?;
        let element = &document.elements()[target.element_index];
        if element.parent().is_none() {
            return Err(PatchError::RootMutation);
        }
        let outer = element.outer_span().ok_or(PatchError::SelectorStale)?;
        edits.push(ByteEdit::new(
            target.part.collision_key(),
            outer.start(),
            outer.end(),
            Vec::new(),
            origin,
        ));
        Ok(())
    }

    fn plan_subtree_edit(
        &self,
        target: &XmlElementSelector,
        fragment: &ValidatedXmlFragment,
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        self.check_fragment_limit(fragment)?;
        let document = self.element_context(target)?;
        let outer = document.elements()[target.element_index]
            .outer_span()
            .ok_or(PatchError::SelectorStale)?;
        edits.push(ByteEdit::new(
            target.part.collision_key(),
            outer.start(),
            outer.end(),
            fragment.bytes().to_vec(),
            origin,
        ));
        Ok(())
    }

    fn plan_content_edit(
        &self,
        target: &XmlElementSelector,
        children: &[ValidatedXmlFragment],
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        if children.len() > self.limits.config().max_intents {
            return Err(PatchError::LimitExceeded { limit: "content_children" });
        }
        let document = self.element_context(target)?;
        let content = document.elements()[target.element_index]
            .content_span()
            .ok_or(PatchError::SelectorStale)?;
        let mut size = 0_usize;
        for child in children {
            self.check_fragment_limit(child)?;
            size = size.checked_add(child.bytes().len()).ok_or(PatchError::AllocationFailed)?;
            if size > self.limits.config().max_fragment_bytes {
                return Err(PatchError::LimitExceeded { limit: "content_fragment_bytes" });
            }
        }
        let mut bytes = Vec::new();
        bytes.try_reserve_exact(size).map_err(|_| PatchError::AllocationFailed)?;
        for child in children {
            bytes.extend_from_slice(child.bytes());
        }
        edits.push(ByteEdit::new(
            target.part.collision_key(), content.start(), content.end(), bytes, origin,
        ));
        Ok(())
    }

    fn plan_allocation_edit(
        &self,
        target: &XmlAttributeSelector,
        handle: AllocationHandle,
        allocations: &BTreeMap<AllocationHandle, u64>,
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        let (_, document) = self.attribute_context(target)?;
        let attribute =
            &document.elements()[target.element.element_index].attributes()[target.attribute_index];
        let value = allocations
            .get(&handle)
            .ok_or(PatchError::AllocationHandleInvalid)?
            .to_string();
        edits.push(ByteEdit::new(
            target.element.part.collision_key(),
            attribute.value_span().start(),
            attribute.value_span().end(),
            escape_attribute(&value, attribute.quote_style())?.into_bytes(),
            origin,
        ));
        Ok(())
    }

    fn plan_relationship_edits(
        &self,
        relationship: &RelationshipAddition,
        origin: usize,
        edits: &mut Vec<ByteEdit>,
    ) -> Result<(), PatchError> {
        let key = self.graph.package_document.collision_key();
        let document = self
            .documents
            .get(key)
            .ok_or(PatchError::TargetNotTokenStable)?;
        let manifest = unique_opf_container(document, "manifest")?;
        let manifest_position = document.elements()[manifest]
            .end_tag_span()
            .ok_or(PatchError::RelationshipContainerInvalid)?
            .start();
        let namespace = document.elements()[manifest]
            .name()
            .namespace()
            .ok_or(PatchError::RelationshipContainerInvalid)?;
        let embedded = if relationship.target.as_str().starts_with("BinData/") {
            " isEmbeded=\"1\""
        } else {
            ""
        };
        let item = format!(
            "<item xmlns=\"{}\" id=\"{}\" href=\"{}\" media-type=\"{}\"{embedded}/>",
            escape_attribute(namespace, XmlQuoteStyle::Double)?,
            escape_attribute(relationship.id.value(), XmlQuoteStyle::Double)?,
            escape_attribute(relationship.target.as_str(), XmlQuoteStyle::Double)?,
            escape_attribute(relationship.media_type.as_str(), XmlQuoteStyle::Double)?,
        );
        edits.push(ByteEdit::new(
            key,
            manifest_position,
            manifest_position,
            item.into_bytes(),
            origin,
        ));
        if relationship.spine != RelationshipSpine::NotInSpine {
            let spine = unique_opf_container(document, "spine")?;
            let spine_position = document.elements()[spine]
                .end_tag_span()
                .ok_or(PatchError::RelationshipContainerInvalid)?
                .start();
            let linear = match relationship.spine {
                RelationshipSpine::Linear => "yes",
                RelationshipSpine::NonLinear => "no",
                RelationshipSpine::NotInSpine => unreachable!(),
            };
            let itemref = format!(
                "<itemref xmlns=\"{}\" idref=\"{}\" linear=\"{}\"/>",
                escape_attribute(namespace, XmlQuoteStyle::Double)?,
                escape_attribute(relationship.id.value(), XmlQuoteStyle::Double)?,
                linear,
            );
            edits.push(ByteEdit::new(
                key,
                spine_position,
                spine_position,
                itemref.into_bytes(),
                origin,
            ));
        }
        Ok(())
    }

    fn apply_edits(&mut self, edits: Vec<ByteEdit>) -> Result<(), PatchError> {
        let mut by_part = BTreeMap::<String, Vec<ByteEdit>>::new();
        for edit in edits {
            by_part.entry(edit.part_key.clone()).or_default().push(edit);
        }
        if by_part.len() > self.patch_limits.config().max_changed_parts {
            return Err(PatchError::LimitExceeded {
                limit: "changed_parts",
            });
        }
        for (key, mut part_edits) in by_part {
            let part = self.parts.get_mut(&key).ok_or(PatchError::TargetMissing)?;
            part_edits.sort_by_key(|edit| (edit.start, edit.end, edit.origin));
            let output = apply_byte_edits(&part.bytes, &part_edits)?;
            if output.len() > part.bytes.len() {
                self.output_growth = self
                    .output_growth
                    .checked_add(output.len() - part.bytes.len())
                    .ok_or(PatchError::LimitExceeded {
                        limit: "output_growth",
                    })?;
                if self.output_growth > self.patch_limits.config().max_total_output_growth {
                    return Err(PatchError::LimitExceeded {
                        limit: "output_growth",
                    });
                }
            }
            part.bytes = output;
        }
        Ok(())
    }

    fn install_added_parts(&mut self, additions: Vec<AddedPart>) -> Result<(), PatchError> {
        let changed_existing = self
            .parts
            .values()
            .filter(|part| {
                part.source_sha256 != Some(<[u8; 32]>::from(Sha256::digest(&part.bytes)))
            })
            .count();
        if changed_existing
            .checked_add(additions.len())
            .is_none_or(|count| count > self.patch_limits.config().max_changed_parts)
        {
            return Err(PatchError::LimitExceeded {
                limit: "changed_parts",
            });
        }
        for part in additions {
            self.output_growth = self.output_growth.checked_add(part.bytes.len()).ok_or(
                PatchError::LimitExceeded {
                    limit: "output_growth",
                },
            )?;
            if self.output_growth > self.patch_limits.config().max_total_output_growth {
                return Err(PatchError::LimitExceeded {
                    limit: "output_growth",
                });
            }
            if self
                .parts
                .insert(
                    part.path.collision_key().to_owned(),
                    VirtualPart {
                        path: part.path.clone(),
                        media_type: part.media_type.clone(),
                        compression: Compression::Deflated,
                        source_order: usize::MAX,
                        source_sha256: None,
                        bytes: part.bytes.to_vec(),
                    },
                )
                .is_some()
            {
                return Err(PatchError::PartCollision);
            }
        }
        Ok(())
    }

    fn reparse_changed_xml(&self) -> Result<(), PatchError> {
        for part in self.parts.values() {
            if media_is_xml(part.media_type.as_str())
                && (part.source_sha256.is_none()
                    || part.source_sha256 != Some(<[u8; 32]>::from(Sha256::digest(&part.bytes))))
            {
                PreservingXmlDocument::parse(&part.bytes)?;
            }
        }
        Ok(())
    }

    fn finish_validation(self, allocation_count: usize) -> Result<PatchResult, PatchError> {
        let archive = validation_archive(self.parts.values())?;
        let mut reader = BoundedZipReader::open(Cursor::new(archive), self.package_limits)?;
        let graph = PackageGraph::build(&mut reader, self.graph_limits)?;
        let preservation = PreservationReport::build_with_graph_limits_and_profile(
            &mut reader,
            &graph,
            self.graph_limits,
            self.preservation_profile,
        )?;
        if !preservation.direct_preserve_ready() || preservation.parts().len() != self.parts.len() {
            return Err(PatchError::ValidationMismatch);
        }
        let id_index = IdIndex::build_with_graph_limits(
            &mut reader,
            &graph,
            self.graph_limits,
            self.id_profile,
            self.id_limits,
        )?;

        let mut records = Vec::new();
        records
            .try_reserve_exact(self.parts.len())
            .map_err(|_| PatchError::AllocationFailed)?;
        let mut parts = self.parts.into_values().collect::<Vec<_>>();
        parts.sort_by(|left, right| left.path.cmp(&right.path));
        let mut untouched_parts = 0usize;
        let mut changed_parts = 0usize;
        let mut added_parts = 0usize;
        for part in &parts {
            let output_sha256 = <[u8; 32]>::from(Sha256::digest(&part.bytes));
            let disposition = match part.source_sha256 {
                None => {
                    added_parts += 1;
                    PatchPartDisposition::Added
                }
                Some(source) if source == output_sha256 => {
                    untouched_parts += 1;
                    PatchPartDisposition::Untouched
                }
                Some(_) => {
                    changed_parts += 1;
                    PatchPartDisposition::Changed
                }
            };
            records.push(PatchPartRecord {
                path: part.path.clone(),
                disposition,
                source_sha256: part.source_sha256,
                output_sha256,
                output_bytes: part.bytes.len(),
            });
        }
        let relationship_count = self
            .intents
            .iter()
            .filter(|intent| matches!(intent, PatchIntent::AddRelationship { .. }))
            .count();
        Ok(PatchResult {
            profile: self.id_profile,
            preservation_profile: self.preservation_profile,
            profile_version: id_index.profile_version(),
            intent_count: self.intents.len(),
            records,
            untouched_parts,
            changed_parts,
            added_parts,
            allocation_count,
            relationship_count,
            declaration_count: id_index.declarations().len(),
            reference_count: id_index.references().len(),
            parts,
        })
    }

    fn element_context(
        &self,
        selector: &XmlElementSelector,
    ) -> Result<&PreservingXmlDocument, PatchError> {
        let key = selector.part.collision_key();
        let record = self.preservation_record(key)?;
        if record.class() != PreservationClass::TokenStable {
            return Err(PatchError::TargetNotTokenStable);
        }
        let document = self
            .documents
            .get(key)
            .ok_or(PatchError::TargetNotTokenStable)?;
        let element = document
            .elements()
            .get(selector.element_index)
            .ok_or(PatchError::SelectorOutOfRange)?;
        if document.original_sha256() != selector.source_sha256
            || record.raw_sha256() != selector.source_sha256
            || element.name() != &selector.expected_name
        {
            return Err(PatchError::SelectorStale);
        }
        Ok(document)
    }

    fn attribute_context(
        &self,
        selector: &XmlAttributeSelector,
    ) -> Result<(&PartPreservationRecord, &PreservingXmlDocument), PatchError> {
        let document = self.element_context(&selector.element)?;
        let attribute = document.elements()[selector.element.element_index]
            .attributes()
            .get(selector.attribute_index)
            .ok_or(PatchError::SelectorOutOfRange)?;
        if attribute.name() != &selector.expected_name || attribute.is_namespace_declaration() {
            return Err(PatchError::SelectorStale);
        }
        Ok((
            self.preservation_record(selector.element.part.collision_key())?,
            document,
        ))
    }

    fn text_context(
        &self,
        selector: &XmlTextSelector,
    ) -> Result<&PreservingXmlDocument, PatchError> {
        let record = self.preservation_record(selector.part.collision_key())?;
        if record.class() != PreservationClass::TokenStable {
            return Err(PatchError::TargetNotTokenStable);
        }
        let document = self
            .documents
            .get(selector.part.collision_key())
            .ok_or(PatchError::TargetNotTokenStable)?;
        let token = document
            .tokens()
            .get(selector.token_index)
            .ok_or(PatchError::SelectorOutOfRange)?;
        if document.original_sha256() != selector.source_sha256
            || record.raw_sha256() != selector.source_sha256
            || token.kind() != selector.expected_kind
            || token.element_index() != selector.expected_element_index
        {
            return Err(PatchError::SelectorStale);
        }
        Ok(document)
    }

    fn preservation_record(&self, key: &str) -> Result<&PartPreservationRecord, PatchError> {
        self.preservation
            .parts()
            .iter()
            .find(|record| record.path().collision_key() == key)
            .ok_or(PatchError::TargetMissing)
    }

    fn check_value_limit(&self, bytes: usize) -> Result<(), PatchError> {
        if bytes > self.patch_limits.config().max_value_bytes {
            Err(PatchError::LimitExceeded {
                limit: "value_bytes",
            })
        } else {
            Ok(())
        }
    }

    fn check_fragment_limit(&self, fragment: &ValidatedXmlFragment) -> Result<(), PatchError> {
        if fragment.bytes.len() > self.patch_limits.config().max_fragment_bytes {
            Err(PatchError::LimitExceeded {
                limit: "fragment_bytes",
            })
        } else {
            Ok(())
        }
    }
}

#[derive(Clone)]
pub(crate) struct VirtualPart {
    pub(crate) path: PackagePath,
    pub(crate) media_type: MediaType,
    pub(crate) compression: Compression,
    pub(crate) source_order: usize,
    pub(crate) source_sha256: Option<[u8; 32]>,
    pub(crate) bytes: Vec<u8>,
}

#[cfg_attr(test, derive(Clone))]
struct ByteEdit {
    part_key: String,
    start: usize,
    end: usize,
    replacement: Vec<u8>,
    origin: usize,
}

impl ByteEdit {
    fn new(part_key: &str, start: usize, end: usize, replacement: Vec<u8>, origin: usize) -> Self {
        Self {
            part_key: part_key.to_owned(),
            start,
            end,
            replacement,
            origin,
        }
    }
}

fn validate_conflicts(edits: &mut [ByteEdit]) -> Result<(), PatchError> {
    edits.sort_by(|left, right| {
        (&left.part_key, left.start, left.end, left.origin).cmp(&(
            &right.part_key,
            right.start,
            right.end,
            right.origin,
        ))
    });
    let mut part_key: Option<&str> = None;
    let mut active_replacement_end: Option<usize> = None;
    let mut last_insert_position: Option<usize> = None;
    for edit in edits {
        if part_key != Some(edit.part_key.as_str()) {
            part_key = Some(edit.part_key.as_str());
            active_replacement_end = None;
            last_insert_position = None;
        }
        let is_insert = edit.start == edit.end;
        let replacement_conflict = active_replacement_end.is_some_and(|end| {
            if is_insert {
                end >= edit.start
            } else {
                end > edit.start
            }
        });
        if replacement_conflict || last_insert_position == Some(edit.start) {
            return Err(PatchError::Conflict);
        }
        if is_insert {
            last_insert_position = Some(edit.start);
        } else {
            active_replacement_end =
                Some(active_replacement_end.map_or(edit.end, |end| end.max(edit.end)));
        }
    }
    Ok(())
}

#[cfg(test)]
fn ranges_conflict(
    left_start: usize,
    left_end: usize,
    right_start: usize,
    right_end: usize,
) -> bool {
    let left_insert = left_start == left_end;
    let right_insert = right_start == right_end;
    match (left_insert, right_insert) {
        (true, true) => left_start == right_start,
        (true, false) => left_start >= right_start && left_start <= right_end,
        (false, true) => right_start >= left_start && right_start <= left_end,
        (false, false) => left_start < right_end && right_start < left_end,
    }
}

fn apply_byte_edits(source: &[u8], edits: &[ByteEdit]) -> Result<Vec<u8>, PatchError> {
    let mut output_len = source.len();
    for edit in edits {
        if edit.start > edit.end || edit.end > source.len() {
            return Err(PatchError::SelectorStale);
        }
        output_len = output_len
            .checked_sub(edit.end - edit.start)
            .and_then(|value| value.checked_add(edit.replacement.len()))
            .ok_or(PatchError::AllocationFailed)?;
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(output_len)
        .map_err(|_| PatchError::AllocationFailed)?;
    let mut cursor = 0usize;
    for edit in edits {
        if edit.start < cursor {
            return Err(PatchError::Conflict);
        }
        output.extend_from_slice(
            source
                .get(cursor..edit.start)
                .ok_or(PatchError::SelectorStale)?,
        );
        output.extend_from_slice(&edit.replacement);
        cursor = edit.end;
    }
    output.extend_from_slice(source.get(cursor..).ok_or(PatchError::SelectorStale)?);
    if output.len() != output_len {
        return Err(PatchError::ValidationMismatch);
    }
    Ok(output)
}

fn unique_opf_container(
    document: &PreservingXmlDocument,
    local_name: &str,
) -> Result<usize, PatchError> {
    let mut matches = document
        .elements()
        .iter()
        .enumerate()
        .filter_map(|(index, element)| {
            (matches!(
                element.name().namespace(),
                Some(OPF_NAMESPACE | OPF_NAMESPACE_HANCOM_2020)
            ) && element.name().local_name() == local_name)
                .then_some(index)
        });
    let first = matches
        .next()
        .ok_or(PatchError::RelationshipContainerInvalid)?;
    if matches.next().is_some() {
        return Err(PatchError::RelationshipContainerInvalid);
    }
    Ok(first)
}

fn validation_archive<'a>(
    parts: impl Iterator<Item = &'a VirtualPart>,
) -> Result<Vec<u8>, PatchError> {
    let mut ordered = parts.collect::<Vec<_>>();
    ordered.sort_by(|left, right| {
        let left_mimetype = left.path.as_str() == "mimetype";
        let right_mimetype = right.path.as_str() == "mimetype";
        right_mimetype
            .cmp(&left_mimetype)
            .then_with(|| left.source_order.cmp(&right.source_order))
            .then_with(|| left.path.cmp(&right.path))
    });
    let cursor = Cursor::new(Vec::new());
    let mut writer = ZipWriter::new(cursor);
    for part in ordered {
        let method = match part.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        writer
            .start_file(
                part.path.as_str(),
                SimpleFileOptions::default().compression_method(method),
            )
            .map_err(|_| PatchError::ValidationArchive)?;
        writer
            .write_all(&part.bytes)
            .map_err(|_| PatchError::ValidationArchive)?;
    }
    writer
        .finish()
        .map(Cursor::into_inner)
        .map_err(|_| PatchError::ValidationArchive)
}

fn escape_text(value: &str) -> Result<String, PatchError> {
    escape_xml(value, None)
}

fn escape_attribute(value: &str, quote: XmlQuoteStyle) -> Result<String, PatchError> {
    escape_xml(value, Some(quote))
}

fn escape_xml(value: &str, quote: Option<XmlQuoteStyle>) -> Result<String, PatchError> {
    if !value.chars().all(xml10_character) {
        return Err(PatchError::ValueInvalid);
    }
    let mut output = String::new();
    output
        .try_reserve(value.len())
        .map_err(|_| PatchError::AllocationFailed)?;
    for character in value.chars() {
        match character {
            '&' => output.push_str("&amp;"),
            '<' => output.push_str("&lt;"),
            '>' => output.push_str("&gt;"),
            '"' if quote == Some(XmlQuoteStyle::Double) => output.push_str("&quot;"),
            '\'' if quote == Some(XmlQuoteStyle::Single) => output.push_str("&apos;"),
            _ => output.push(character),
        }
    }
    Ok(output)
}

fn xml10_character(character: char) -> bool {
    matches!(
        character,
        '\u{9}' | '\u{A}' | '\u{D}' | '\u{20}'..='\u{D7FF}' | '\u{E000}'..='\u{FFFD}' | '\u{10000}'..='\u{10FFFF}'
    )
}

fn valid_text_id(raw: &str) -> bool {
    !raw.is_empty()
        && !raw
            .chars()
            .any(|character| character.is_control() || character.is_whitespace())
        && !raw.contains([':', '/', '\\', '?', '#', '&'])
}

fn media_is_xml(media_type: &str) -> bool {
    media_type
        .split_once('/')
        .is_some_and(|(_, subtype)| subtype == "xml" || subtype.ends_with("+xml"))
}

fn content_looks_xml(bytes: &[u8]) -> bool {
    let bytes = bytes.strip_prefix(&[0xEF, 0xBB, 0xBF]).unwrap_or(bytes);
    bytes
        .iter()
        .find(|byte| !matches!(byte, b' ' | b'\t' | b'\r' | b'\n'))
        == Some(&b'<')
}

fn binary_signature_matches(media_type: &str, bytes: &[u8]) -> Option<bool> {
    match media_type {
        "image/png" => Some(bytes.starts_with(b"\x89PNG\r\n\x1a\n")),
        "image/jpeg" => Some(bytes.starts_with(&[0xFF, 0xD8, 0xFF])),
        "image/gif" => Some(bytes.starts_with(b"GIF87a") || bytes.starts_with(b"GIF89a")),
        "image/webp" => Some(
            bytes.starts_with(b"RIFF")
                && bytes
                    .get(8..12)
                    .is_some_and(|signature| signature == b"WEBP"),
        ),
        "image/bmp" => Some(bytes.starts_with(b"BM")),
        "application/pdf" => Some(bytes.starts_with(b"%PDF-")),
        "font/ttf" | "application/x-font-ttf" => {
            Some(bytes.starts_with(&[0x00, 0x01, 0x00, 0x00]) || bytes.starts_with(b"true"))
        }
        "font/otf" | "application/vnd.ms-opentype" => Some(bytes.starts_with(b"OTTO")),
        _ => None,
    }
}

#[cfg(test)]
mod conflict_validation_tests {
    use super::{ByteEdit, PatchError, ranges_conflict, validate_conflicts};

    fn edit(part: &str, start: usize, end: usize, origin: usize) -> ByteEdit {
        ByteEdit::new(part, start, end, Vec::new(), origin)
    }

    fn quadratic_conflict(mut edits: Vec<ByteEdit>) -> bool {
        edits.sort_by(|left, right| {
            (&left.part_key, left.start, left.end, left.origin).cmp(&(
                &right.part_key,
                right.start,
                right.end,
                right.origin,
            ))
        });
        for (index, left) in edits.iter().enumerate() {
            for right in &edits[index + 1..] {
                if left.part_key != right.part_key {
                    break;
                }
                if ranges_conflict(left.start, left.end, right.start, right.end) {
                    return true;
                }
            }
        }
        false
    }

    #[test]
    fn sweep_matches_quadratic_reference_for_small_exhaustive_ranges() {
        let mut candidates = Vec::new();
        for part in ["a", "b"] {
            for start in 0..=3 {
                for end in start..=3 {
                    candidates.push((part, start, end));
                }
            }
        }
        for left in &candidates {
            for middle in &candidates {
                for right in &candidates {
                    let edits = vec![
                        edit(left.0, left.1, left.2, 0),
                        edit(middle.0, middle.1, middle.2, 1),
                        edit(right.0, right.1, right.2, 2),
                    ];
                    let expected = quadratic_conflict(edits.clone());
                    let mut observed = edits;
                    assert_eq!(validate_conflicts(&mut observed).is_err(), expected);
                }
            }
        }
    }

    #[test]
    fn fifty_thousand_distinct_insertions_are_admitted_without_quadratic_scan() {
        let mut edits = (0..50_000)
            .map(|position| edit("part", position * 2, position * 2, position))
            .rev()
            .collect::<Vec<_>>();
        assert!(validate_conflicts(&mut edits).is_ok());
        edits.push(edit("part", 99_998, 99_998, 50_000));
        assert!(matches!(
            validate_conflicts(&mut edits),
            Err(PatchError::Conflict)
        ));
    }

    #[test]
    fn insertion_boundaries_conflict_but_adjacent_replacements_do_not() {
        for position in [2, 5] {
            let mut edits = vec![edit("part", 2, 5, 0), edit("part", position, position, 1)];
            assert!(matches!(
                validate_conflicts(&mut edits),
                Err(PatchError::Conflict)
            ));
        }
        let mut adjacent = vec![edit("part", 2, 5, 0), edit("part", 5, 8, 1)];
        assert!(validate_conflicts(&mut adjacent).is_ok());
    }
}
