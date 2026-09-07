use std::collections::{BTreeMap, BTreeSet};
use std::io::{Read, Seek};

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    BoundedZipReader, Compression, GraphError, MediaType, PackageError, PackageGraph,
    PackageGraphLimits, PackagePath, PartRecord, PartRole, PreservingXmlDocument,
    PreservingXmlError,
};

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum PreservationClass {
    ByteExact,
    TokenStable,
    Semantic,
    Regenerated,
    Opaque,
    Rejected,
}

/// Versioned classification rules. The default v1 profile remains fail-closed;
/// exact Hangul-2020 preview text admission is opt-in.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub enum PreservationRuleProfile {
    #[default]
    CoreV1,
    Hangul2020PreviewTextV2,
}

impl PreservationRuleProfile {
    #[must_use]
    pub const fn version(self) -> &'static str {
        match self {
            Self::CoreV1 => "hwpx-agent.preservation/core-v1",
            Self::Hangul2020PreviewTextV2 => "hwpx-agent.preservation/hancom-2020-preview-text-v2",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PreservationReason {
    ExactMimetype,
    SafeXmlTokenModel,
    OpaqueBinarySignature,
    OpaquePreviewText,
    OpaqueUnrecognizedMedia,
    XmlMediaPathMismatch,
    XmlContentMediaMismatch,
    BinarySignatureMismatch,
    XmlRejected(&'static str),
}

impl PreservationReason {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::ExactMimetype => "preservation_byte_exact_mimetype",
            Self::SafeXmlTokenModel => "preservation_token_stable_safe_xml",
            Self::OpaqueBinarySignature => "preservation_opaque_binary_signature",
            Self::OpaquePreviewText => "preservation_opaque_preview_text",
            Self::OpaqueUnrecognizedMedia => "preservation_opaque_unrecognized_media",
            Self::XmlMediaPathMismatch => "preservation_rejected_xml_media_path_mismatch",
            Self::XmlContentMediaMismatch => "preservation_rejected_xml_content_media_mismatch",
            Self::BinarySignatureMismatch => "preservation_rejected_binary_signature_mismatch",
            Self::XmlRejected(code) => code,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TokenPreservationEvidence {
    token_count: usize,
    element_count: usize,
    source_sha256: [u8; 32],
    untouched_verified: bool,
}

impl TokenPreservationEvidence {
    #[must_use]
    pub const fn token_count(&self) -> usize {
        self.token_count
    }

    #[must_use]
    pub const fn element_count(&self) -> usize {
        self.element_count
    }

    #[must_use]
    pub const fn source_sha256(&self) -> [u8; 32] {
        self.source_sha256
    }

    #[must_use]
    pub const fn untouched_verified(&self) -> bool {
        self.untouched_verified
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PartPreservationRecord {
    path: PackagePath,
    media_type: MediaType,
    role: PartRole,
    source_entry_index: usize,
    compression: Compression,
    compressed_size: u64,
    expanded_size: u64,
    crc32: u32,
    raw_sha256: [u8; 32],
    class: PreservationClass,
    reason: PreservationReason,
    token_evidence: Option<TokenPreservationEvidence>,
}

impl PartPreservationRecord {
    #[must_use]
    pub const fn path(&self) -> &PackagePath {
        &self.path
    }

    #[must_use]
    pub const fn media_type(&self) -> &MediaType {
        &self.media_type
    }

    #[must_use]
    pub const fn role(&self) -> PartRole {
        self.role
    }

    #[must_use]
    pub const fn source_entry_index(&self) -> usize {
        self.source_entry_index
    }

    #[must_use]
    pub const fn compression(&self) -> Compression {
        self.compression
    }

    #[must_use]
    pub const fn compressed_size(&self) -> u64 {
        self.compressed_size
    }

    #[must_use]
    pub const fn expanded_size(&self) -> u64 {
        self.expanded_size
    }

    #[must_use]
    pub const fn crc32(&self) -> u32 {
        self.crc32
    }

    #[must_use]
    pub const fn raw_sha256(&self) -> [u8; 32] {
        self.raw_sha256
    }

    #[must_use]
    pub const fn class(&self) -> PreservationClass {
        self.class
    }

    #[must_use]
    pub const fn reason(&self) -> &PreservationReason {
        &self.reason
    }

    #[must_use]
    pub fn reason_code(&self) -> &'static str {
        self.reason.code()
    }

    #[must_use]
    pub const fn token_evidence(&self) -> Option<&TokenPreservationEvidence> {
        self.token_evidence.as_ref()
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct PreservationCounts {
    pub byte_exact: usize,
    pub token_stable: usize,
    pub semantic: usize,
    pub regenerated: usize,
    pub opaque: usize,
    pub rejected: usize,
}

impl PreservationCounts {
    fn increment(&mut self, class: PreservationClass) {
        let counter = match class {
            PreservationClass::ByteExact => &mut self.byte_exact,
            PreservationClass::TokenStable => &mut self.token_stable,
            PreservationClass::Semantic => &mut self.semantic,
            PreservationClass::Regenerated => &mut self.regenerated,
            PreservationClass::Opaque => &mut self.opaque,
            PreservationClass::Rejected => &mut self.rejected,
        };
        *counter += 1;
    }

    #[must_use]
    pub const fn total(self) -> usize {
        self.byte_exact
            + self.token_stable
            + self.semantic
            + self.regenerated
            + self.opaque
            + self.rejected
    }
}

/// Complete, deterministic classification of every closed-graph package part.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PreservationReport {
    parts: Vec<PartPreservationRecord>,
    counts: PreservationCounts,
    direct_preserve_ready: bool,
}

impl PreservationReport {
    /// Re-reads every graph part through the bounded reader, revalidates raw
    /// identity, and assigns only evidence-backed preservation classes.
    ///
    /// # Errors
    ///
    /// Returns a hard error for graph/reader divergence, raw identity drift,
    /// bounded package failure, internal token-model failure, or allocation.
    /// Unsafe XML/media content becomes an explicit `Rejected` record instead.
    pub fn build<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
    ) -> Result<Self, PreservationError> {
        Self::build_with_profile(reader, graph, PreservationRuleProfile::CoreV1)
    }

    /// Rebuilds preservation evidence under one explicit rule profile.
    ///
    /// # Errors
    ///
    /// Returns the same fail-closed errors as [`Self::build`].
    pub fn build_with_profile<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        profile: PreservationRuleProfile,
    ) -> Result<Self, PreservationError> {
        Self::build_with_graph_limits_and_profile(
            reader,
            graph,
            PackageGraphLimits::default(),
            profile,
        )
    }

    /// Same as [`Self::build`] with the caller's already-validated graph limits.
    ///
    /// # Errors
    ///
    /// Returns the same fail-closed errors as [`Self::build`].
    pub fn build_with_graph_limits<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        graph_limits: PackageGraphLimits,
    ) -> Result<Self, PreservationError> {
        Self::build_with_graph_limits_and_profile(
            reader,
            graph,
            graph_limits,
            PreservationRuleProfile::CoreV1,
        )
    }

    /// Same as [`Self::build_with_profile`] with the caller's graph limits.
    ///
    /// # Errors
    ///
    /// Returns the same fail-closed errors as [`Self::build`].
    pub fn build_with_graph_limits_and_profile<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph: &PackageGraph,
        graph_limits: PackageGraphLimits,
        profile: PreservationRuleProfile,
    ) -> Result<Self, PreservationError> {
        let authoritative = PackageGraph::build(reader, graph_limits)?;
        validate_graph_snapshot(graph, &authoritative)?;
        let entry_by_key = indexed_non_directory_entries(reader)?;
        if entry_by_key.len() != graph.parts.len() {
            return Err(PreservationError::GraphShape);
        }
        let mut graph_parts = Vec::new();
        graph_parts
            .try_reserve_exact(graph.parts.len())
            .map_err(|_| PreservationError::AllocationFailed)?;
        graph_parts.extend(graph.parts.iter());
        graph_parts.sort_unstable_by(|left, right| left.path.cmp(&right.path));

        let mut records = Vec::new();
        records
            .try_reserve_exact(graph_parts.len())
            .map_err(|_| PreservationError::AllocationFailed)?;
        let mut seen = BTreeSet::new();
        let mut counts = PreservationCounts::default();
        for part in graph_parts {
            if !seen.insert(part.path.collision_key().to_owned()) {
                return Err(PreservationError::GraphShape);
            }
            let entry = entry_by_key
                .get(part.path.collision_key())
                .ok_or(PreservationError::GraphShape)?;
            validate_entry_identity(entry, part)?;
            let bytes = reader.read_entry(entry.index)?;
            let digest = <[u8; 32]>::from(Sha256::digest(&bytes));
            if bytes.len() as u64 != part.expanded_size || digest != part.raw_sha256 {
                return Err(PreservationError::IdentityMismatch);
            }
            let classification = classify(part, &bytes, profile)?;
            counts.increment(classification.class);
            records.push(PartPreservationRecord {
                path: part.path.clone(),
                media_type: part.media_type.clone(),
                role: part.role,
                source_entry_index: entry.index,
                compression: entry.compression,
                compressed_size: entry.compressed_size,
                expanded_size: part.expanded_size,
                crc32: entry.crc32,
                raw_sha256: part.raw_sha256,
                class: classification.class,
                reason: classification.reason,
                token_evidence: classification.token_evidence,
            });
        }
        if seen.len() != entry_by_key.len() || counts.total() != records.len() {
            return Err(PreservationError::GraphShape);
        }
        Ok(Self {
            direct_preserve_ready: counts.rejected == 0,
            parts: records,
            counts,
        })
    }

    #[must_use]
    pub fn parts(&self) -> &[PartPreservationRecord] {
        &self.parts
    }

    #[must_use]
    pub const fn counts(&self) -> PreservationCounts {
        self.counts
    }

    /// Classification readiness only. It does not claim that the P03-08 writer exists.
    #[must_use]
    pub const fn direct_preserve_ready(&self) -> bool {
        self.direct_preserve_ready
    }
}

fn validate_graph_snapshot(
    supplied: &PackageGraph,
    authoritative: &PackageGraph,
) -> Result<(), PreservationError> {
    if supplied.package_document != authoritative.package_document
        || supplied.relationships != authoritative.relationships
        || supplied.spine != authoritative.spine
        || supplied.parts.len() != authoritative.parts.len()
    {
        return Err(PreservationError::GraphShape);
    }
    let authoritative_parts = authoritative
        .parts
        .iter()
        .map(|part| (part.path.collision_key(), part))
        .collect::<BTreeMap<_, _>>();
    let mut seen = BTreeSet::new();
    for supplied_part in &supplied.parts {
        if !seen.insert(supplied_part.path.collision_key()) {
            return Err(PreservationError::GraphShape);
        }
        let expected = authoritative_parts
            .get(supplied_part.path.collision_key())
            .ok_or(PreservationError::GraphShape)?;
        if supplied_part.path != expected.path
            || supplied_part.media_type != expected.media_type
            || supplied_part.role != expected.role
            || supplied_part.expanded_size != expected.expanded_size
        {
            return Err(PreservationError::GraphShape);
        }
    }
    Ok(())
}

#[derive(Clone, Debug)]
struct IndexedEntry {
    index: usize,
    path: PackagePath,
    compression: Compression,
    compressed_size: u64,
    expanded_size: u64,
    crc32: u32,
}

fn indexed_non_directory_entries<R: Read + Seek>(
    reader: &BoundedZipReader<R>,
) -> Result<BTreeMap<String, IndexedEntry>, PreservationError> {
    let mut entries = BTreeMap::new();
    for entry in reader
        .entries()
        .iter()
        .filter(|entry| !entry.path.is_directory())
    {
        if entries
            .insert(
                entry.path.collision_key().to_owned(),
                IndexedEntry {
                    index: entry.index,
                    path: entry.path.clone(),
                    compression: entry.compression,
                    compressed_size: entry.compressed_size,
                    expanded_size: entry.expanded_size,
                    crc32: entry.crc32,
                },
            )
            .is_some()
        {
            return Err(PreservationError::GraphShape);
        }
    }
    Ok(entries)
}

fn validate_entry_identity(
    entry: &IndexedEntry,
    part: &PartRecord,
) -> Result<(), PreservationError> {
    if entry.path != part.path || entry.expanded_size != part.expanded_size {
        return Err(PreservationError::IdentityMismatch);
    }
    Ok(())
}

struct Classification {
    class: PreservationClass,
    reason: PreservationReason,
    token_evidence: Option<TokenPreservationEvidence>,
}

fn classify(
    part: &PartRecord,
    bytes: &[u8],
    profile: PreservationRuleProfile,
) -> Result<Classification, PreservationError> {
    if part.path.as_str() == "mimetype" {
        return Ok(classification(
            PreservationClass::ByteExact,
            PreservationReason::ExactMimetype,
        ));
    }
    let path_xml = path_is_xml(part.path.as_str());
    let media_xml = media_is_xml(part.media_type.as_str());
    if path_xml != media_xml {
        return Ok(classification(
            PreservationClass::Rejected,
            PreservationReason::XmlMediaPathMismatch,
        ));
    }
    if media_xml {
        return classify_xml(bytes);
    }
    if profile == PreservationRuleProfile::Hangul2020PreviewTextV2
        && part.path.as_str() == "Preview/PrvText.txt"
        && part.media_type.as_str() == "text/plain"
    {
        return Ok(classification(
            PreservationClass::Opaque,
            PreservationReason::OpaquePreviewText,
        ));
    }
    if content_looks_xml(bytes) {
        return Ok(classification(
            PreservationClass::Rejected,
            PreservationReason::XmlContentMediaMismatch,
        ));
    }
    match binary_signature_matches(part.media_type.as_str(), bytes) {
        Some(true) => Ok(classification(
            PreservationClass::Opaque,
            PreservationReason::OpaqueBinarySignature,
        )),
        Some(false) => Ok(classification(
            PreservationClass::Rejected,
            PreservationReason::BinarySignatureMismatch,
        )),
        None => Ok(classification(
            PreservationClass::Opaque,
            PreservationReason::OpaqueUnrecognizedMedia,
        )),
    }
}

fn classification(class: PreservationClass, reason: PreservationReason) -> Classification {
    Classification {
        class,
        reason,
        token_evidence: None,
    }
}

fn classify_xml(bytes: &[u8]) -> Result<Classification, PreservationError> {
    let document = match PreservingXmlDocument::parse(bytes) {
        Ok(document) => document,
        Err(PreservingXmlError::Safe(error)) => {
            return Ok(classification(
                PreservationClass::Rejected,
                PreservationReason::XmlRejected(error.code()),
            ));
        }
        Err(error) => return Err(PreservationError::TokenModel { code: error.code() }),
    };
    document
        .verify_untouched_round_trip()
        .map_err(|error| PreservationError::TokenModel { code: error.code() })?;
    Ok(Classification {
        class: PreservationClass::TokenStable,
        reason: PreservationReason::SafeXmlTokenModel,
        token_evidence: Some(TokenPreservationEvidence {
            token_count: document.tokens().len(),
            element_count: document.elements().len(),
            source_sha256: document.original_sha256(),
            untouched_verified: true,
        }),
    })
}

fn path_is_xml(path: &str) -> bool {
    let lower = path.to_ascii_lowercase();
    [".xml", ".hpf", ".opf", ".rels", ".xsd", ".svg", ".rdf"]
        .iter()
        .any(|extension| lower.ends_with(extension))
}

fn media_is_xml(media_type: &str) -> bool {
    media_type
        .split_once('/')
        .is_some_and(|(_, subtype)| subtype == "xml" || subtype.ends_with("+xml"))
}

fn content_looks_xml(bytes: &[u8]) -> bool {
    let bytes = bytes.strip_prefix(&[0xEF, 0xBB, 0xBF]).unwrap_or(bytes);
    let first = bytes
        .iter()
        .position(|byte| !matches!(byte, b' ' | b'\t' | b'\r' | b'\n'));
    first.is_some_and(|index| bytes[index] == b'<')
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

#[derive(Debug, Error)]
pub enum PreservationError {
    #[error("bounded package read failed while building preservation evidence")]
    Package(#[from] PackageError),
    #[error("authoritative package graph rebuild failed")]
    Graph(#[from] GraphError),
    #[error("package graph and bounded reader part sets differ")]
    GraphShape,
    #[error("package graph raw part identity differs from bounded readback")]
    IdentityMismatch,
    #[error("preserving XML token model failed internally: {code}")]
    TokenModel { code: &'static str },
    #[error("preservation report allocation failed")]
    AllocationFailed,
}

impl PreservationError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::Package(error) => error.code(),
            Self::Graph(error) => error.code(),
            Self::GraphShape => "preservation_graph_shape_mismatch",
            Self::IdentityMismatch => "preservation_identity_mismatch",
            Self::TokenModel { .. } => "preservation_token_model_failed",
            Self::AllocationFailed => "preservation_allocation_failed",
        }
    }
}
