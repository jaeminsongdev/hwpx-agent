use std::collections::{BTreeMap, BTreeSet};
use std::io::{Read, Seek};

use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::safe_xml::{
    SafeXmlDocument, SafeXmlElement, SafeXmlError, SafeXmlEvent, SafeXmlLimitConfig, SafeXmlLimits,
};
use crate::{BoundedZipReader, Compression, PackageError, PackageLimits, PackagePath};

pub const HWPX_MEDIA_TYPE: &str = "application/hwp+zip";
const CONTAINER_PATH: &str = "META-INF/container.xml";
const CONTAINER_NS: &str = "urn:oasis:names:tc:opendocument:xmlns:container";
const OPF_NS: &str = "http://www.idpf.org/2007/opf";
const OPF_NS_HANCOM_2020: &str = "http://www.idpf.org/2007/opf/";
const HWPML_PACKAGE_MEDIA_TYPE: &str = "application/hwpml-package+xml";
const OEBPS_PACKAGE_MEDIA_TYPE: &str = "application/oebps-package+xml";

/// Finite limits for the narrow container/OPF metadata parser used by P03-02.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PackageGraphLimitConfig {
    pub max_metadata_bytes: usize,
    pub max_xml_events: usize,
    pub max_xml_depth: usize,
    pub max_attributes_per_element: usize,
    pub max_attribute_bytes: usize,
    pub max_relationships: usize,
    pub max_media_type_bytes: usize,
}

impl Default for PackageGraphLimitConfig {
    fn default() -> Self {
        Self {
            max_metadata_bytes: 2 * 1024 * 1024,
            max_xml_events: 100_000,
            max_xml_depth: 64,
            max_attributes_per_element: 32,
            max_attribute_bytes: 8 * 1024,
            max_relationships: 16_384,
            max_media_type_bytes: 255,
        }
    }
}

/// Validated package-graph limits. Values are rejected rather than clamped.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct PackageGraphLimits(PackageGraphLimitConfig);

impl PackageGraphLimits {
    pub const HARD_MAX_METADATA_BYTES: usize = 16 * 1024 * 1024;
    pub const HARD_MAX_XML_EVENTS: usize = 1_000_000;
    pub const HARD_MAX_XML_DEPTH: usize = 256;
    pub const HARD_MAX_ATTRIBUTES_PER_ELEMENT: usize = 256;
    pub const HARD_MAX_ATTRIBUTE_BYTES: usize = 64 * 1024;
    pub const HARD_MAX_RELATIONSHIPS: usize = PackageLimits::HARD_MAX_ENTRIES;
    pub const HARD_MAX_MEDIA_TYPE_BYTES: usize = 1_024;

    /// Validates graph limits against immutable product ceilings.
    ///
    /// # Errors
    ///
    /// Returns [`GraphError::InvalidLimit`] for a zero or over-ceiling value.
    pub fn new(config: PackageGraphLimitConfig) -> Result<Self, GraphError> {
        let values = [
            (
                "max_metadata_bytes",
                config.max_metadata_bytes,
                Self::HARD_MAX_METADATA_BYTES,
            ),
            (
                "max_xml_events",
                config.max_xml_events,
                Self::HARD_MAX_XML_EVENTS,
            ),
            (
                "max_xml_depth",
                config.max_xml_depth,
                Self::HARD_MAX_XML_DEPTH,
            ),
            (
                "max_attributes_per_element",
                config.max_attributes_per_element,
                Self::HARD_MAX_ATTRIBUTES_PER_ELEMENT,
            ),
            (
                "max_attribute_bytes",
                config.max_attribute_bytes,
                Self::HARD_MAX_ATTRIBUTE_BYTES,
            ),
            (
                "max_relationships",
                config.max_relationships,
                Self::HARD_MAX_RELATIONSHIPS,
            ),
            (
                "max_media_type_bytes",
                config.max_media_type_bytes,
                Self::HARD_MAX_MEDIA_TYPE_BYTES,
            ),
        ];
        for (field, value, ceiling) in values {
            if value == 0 || value > ceiling {
                return Err(GraphError::InvalidLimit {
                    field,
                    value: value as u64,
                    ceiling: ceiling as u64,
                });
            }
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> PackageGraphLimitConfig {
        self.0
    }
}

/// A validated, canonical lower-case Internet media type without parameters.
#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct MediaType(String);

impl MediaType {
    fn parse(raw: &str, limits: PackageGraphLimits) -> Result<Self, GraphError> {
        if raw.is_empty()
            || raw.len() > limits.config().max_media_type_bytes
            || !raw.is_ascii()
            || raw.bytes().filter(|byte| *byte == b'/').count() != 1
            || raw
                .split('/')
                .any(|part| part.is_empty() || part == "*" || !part.bytes().all(is_media_token))
        {
            return Err(GraphError::InvalidMediaType);
        }
        Ok(Self(raw.to_ascii_lowercase()))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

fn is_media_token(byte: u8) -> bool {
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
                | b'.'
                | b'^'
                | b'_'
                | b'`'
                | b'|'
                | b'~'
        )
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PartRole {
    Infrastructure,
    ManifestListed,
    SpineDocument,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RelationshipKind {
    ManifestItem,
    SpineItem,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Relationship {
    pub id: String,
    pub source: PackagePath,
    pub target: PackagePath,
    pub media_type: MediaType,
    pub kind: RelationshipKind,
    pub linear: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PartRecord {
    pub path: PackagePath,
    pub media_type: MediaType,
    pub role: PartRole,
    pub expanded_size: u64,
    pub raw_sha256: [u8; 32],
}

/// A closed, read-only HWPX package part graph.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PackageGraph {
    pub package_document: PackagePath,
    pub parts: Vec<PartRecord>,
    pub relationships: Vec<Relationship>,
    pub spine: Vec<PackagePath>,
}

impl PackageGraph {
    /// Builds and validates a complete graph from a previously bounded ZIP.
    /// Every non-directory part is integrity-read and hashed; no bytes are
    /// extracted or written to the filesystem.
    ///
    /// # Errors
    ///
    /// Returns a stable [`GraphError`] for malformed HWPX metadata, an open
    /// graph, an unsafe relationship, or an underlying bounded ZIP failure.
    pub fn build<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        graph_limits: PackageGraphLimits,
    ) -> Result<Self, GraphError> {
        let package_limits = reader.package_limits();
        let mut entries = Vec::new();
        entries
            .try_reserve_exact(reader.entries().len())
            .map_err(|_| GraphError::AllocationFailed)?;
        entries.extend_from_slice(reader.entries());
        validate_mimetype(reader, &entries)?;
        let by_key = entries
            .iter()
            .map(|entry| (entry.path.collision_key().to_owned(), entry.index))
            .collect::<BTreeMap<_, _>>();
        let container_index = exact_index(&entries, CONTAINER_PATH)
            .ok_or(GraphError::RequiredPartMissing { part: "container" })?;
        if exact_index(&entries, "version.xml").is_none() {
            return Err(GraphError::RequiredPartMissing { part: "version" });
        }
        let container_bytes = reader.read_entry(container_index)?;
        let roots = parse_container(&container_bytes, package_limits, graph_limits)?;
        validate_rootfile_targets(&roots, &entries, &by_key)?;
        let root = &roots.package;
        let root_index = by_key
            .get(root.path.collision_key())
            .copied()
            .ok_or(GraphError::PackageDocumentMissing)?;
        if entries[root_index].path.is_directory() {
            return Err(GraphError::PackageDocumentMissing);
        }
        let package_document = entries[root_index].path.clone();
        let hashed = read_and_hash_parts(reader, &entries, root_index)?;
        let parsed = parse_opf(
            &hashed.package_bytes,
            &package_document,
            &by_key,
            package_limits,
            graph_limits,
        )?;
        let links = build_links(parsed, &entries, &by_key, &package_document, graph_limits)?;
        let infrastructure = infrastructure_keys(&package_document, &roots.all, package_limits)?;
        validate_closure(&entries, &infrastructure, &links.manifest_targets)?;
        let root_media_by_target = roots
            .all
            .iter()
            .map(|root| {
                (
                    root.path.collision_key().to_owned(),
                    root.media_type.clone(),
                )
            })
            .collect::<BTreeMap<_, _>>();
        let parts = build_parts(
            &entries,
            &hashed.raw_hashes,
            &links,
            &package_document,
            &root.media_type,
            &root_media_by_target,
            graph_limits,
        )?;
        Ok(Self {
            package_document,
            parts,
            relationships: links.relationships,
            spine: links.spine,
        })
    }
}

#[derive(Debug, Error)]
pub enum GraphError {
    #[error("invalid finite graph limit for {field}: {value} (ceiling {ceiling})")]
    InvalidLimit {
        field: &'static str,
        value: u64,
        ceiling: u64,
    },
    #[error("bounded package validation failed")]
    Package(#[from] PackageError),
    #[error("root mimetype entry is missing")]
    MimetypeMissing,
    #[error("root mimetype entry is not first")]
    MimetypeNotFirst,
    #[error("root mimetype entry is not stored")]
    MimetypeNotStored,
    #[error("root mimetype value is invalid")]
    MimetypeInvalid,
    #[error("required package infrastructure part is missing: {part}")]
    RequiredPartMissing { part: &'static str },
    #[error("bounded package metadata is too large: {kind}")]
    MetadataTooLarge { kind: &'static str },
    #[error("package metadata XML is malformed")]
    XmlMalformed,
    #[error("package metadata XML uses a forbidden construct")]
    XmlForbiddenConstruct,
    #[error("package metadata XML exceeds the {limit} limit")]
    XmlLimitExceeded { limit: &'static str },
    #[error("package metadata XML namespace is invalid")]
    XmlNamespaceInvalid,
    #[error("container rootfile is missing")]
    ContainerRootfileMissing,
    #[error("container has more than one rootfile")]
    ContainerRootfileDuplicate,
    #[error("container rootfile is invalid")]
    ContainerRootfileInvalid,
    #[error("container rootfile target is missing")]
    ContainerRootfileTargetMissing,
    #[error("package document target is missing")]
    PackageDocumentMissing,
    #[error("OPF manifest is missing")]
    ManifestMissing,
    #[error("OPF manifest is duplicated")]
    ManifestDuplicate,
    #[error("OPF spine is missing")]
    SpineMissing,
    #[error("OPF spine is duplicated")]
    SpineDuplicateSection,
    #[error("OPF manifest item is invalid")]
    ManifestItemInvalid,
    #[error("OPF manifest item identifier is duplicated")]
    ManifestIdDuplicate,
    #[error("OPF manifest target path is duplicated")]
    ManifestPathDuplicate,
    #[error("OPF manifest target is missing from the package")]
    ManifestTargetMissing,
    #[error("OPF manifest target is ambiguous between root and source-relative paths")]
    ManifestTargetAmbiguous,
    #[error("package contains an unlisted non-infrastructure part")]
    OrphanPart,
    #[error("OPF spine contains a dangling reference")]
    SpineDangling,
    #[error("OPF spine target is duplicated")]
    SpineDuplicate,
    #[error("external package relationship is blocked")]
    ExternalRelationshipBlocked,
    #[error("package relationship escapes the package root")]
    RelationshipEscapesRoot,
    #[error("package relationship path is invalid")]
    InvalidRelationshipPath,
    #[error("package media type is invalid")]
    InvalidMediaType,
    #[error("bounded package graph allocation failed")]
    AllocationFailed,
}

impl GraphError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit { .. } => "invalid_graph_limit",
            Self::Package(error) => error.code(),
            Self::MimetypeMissing => "mimetype_missing",
            Self::MimetypeNotFirst => "mimetype_not_first",
            Self::MimetypeNotStored => "mimetype_not_stored",
            Self::MimetypeInvalid => "mimetype_invalid",
            Self::RequiredPartMissing { .. } => "required_part_missing",
            Self::MetadataTooLarge { .. } => "metadata_too_large",
            Self::XmlMalformed => "xml_malformed",
            Self::XmlForbiddenConstruct => "xml_forbidden_construct",
            Self::XmlLimitExceeded { .. } => "xml_limit_exceeded",
            Self::XmlNamespaceInvalid => "xml_namespace_invalid",
            Self::ContainerRootfileMissing => "container_rootfile_missing",
            Self::ContainerRootfileDuplicate => "container_rootfile_duplicate",
            Self::ContainerRootfileInvalid => "container_rootfile_invalid",
            Self::ContainerRootfileTargetMissing => "container_rootfile_target_missing",
            Self::PackageDocumentMissing => "package_document_missing",
            Self::ManifestMissing => "manifest_missing",
            Self::ManifestDuplicate => "manifest_duplicate",
            Self::SpineMissing => "spine_missing",
            Self::SpineDuplicateSection => "spine_duplicate_section",
            Self::ManifestItemInvalid => "manifest_item_invalid",
            Self::ManifestIdDuplicate => "manifest_id_duplicate",
            Self::ManifestPathDuplicate => "manifest_path_duplicate",
            Self::ManifestTargetMissing => "manifest_target_missing",
            Self::ManifestTargetAmbiguous => "manifest_target_ambiguous",
            Self::OrphanPart => "orphan_part",
            Self::SpineDangling => "spine_dangling",
            Self::SpineDuplicate => "spine_duplicate",
            Self::ExternalRelationshipBlocked => "external_relationship_blocked",
            Self::RelationshipEscapesRoot => "relationship_escapes_root",
            Self::InvalidRelationshipPath => "invalid_relationship_path",
            Self::InvalidMediaType => "invalid_media_type",
            Self::AllocationFailed => "graph_allocation_failed",
        }
    }
}

#[derive(Debug)]
struct ManifestItem {
    id: String,
    target: PackagePath,
    media_type: MediaType,
}

#[derive(Debug)]
struct SpineItem {
    idref: String,
    linear: bool,
}

#[derive(Debug)]
struct ParsedOpf {
    items: Vec<ManifestItem>,
    spine: Vec<SpineItem>,
}

#[derive(Clone, Debug)]
struct RootfileRecord {
    path: PackagePath,
    media_type: MediaType,
}

#[derive(Debug)]
struct ContainerRoots {
    package: RootfileRecord,
    all: Vec<RootfileRecord>,
}

#[derive(Debug)]
struct GraphLinks {
    relationships: Vec<Relationship>,
    spine: Vec<PackagePath>,
    manifest_targets: BTreeSet<String>,
    spine_targets: BTreeSet<String>,
    media_by_target: BTreeMap<String, MediaType>,
}

#[derive(Debug)]
struct HashedParts {
    raw_hashes: BTreeMap<usize, [u8; 32]>,
    package_bytes: Vec<u8>,
}

fn validate_mimetype<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    entries: &[crate::EntryMetadata],
) -> Result<(), GraphError> {
    let first = entries.first().ok_or(GraphError::MimetypeMissing)?;
    if first.path.as_str() != "mimetype" {
        return Err(
            if entries
                .iter()
                .any(|entry| entry.path.as_str() == "mimetype")
            {
                GraphError::MimetypeNotFirst
            } else {
                GraphError::MimetypeMissing
            },
        );
    }
    if first.compression != Compression::Stored {
        return Err(GraphError::MimetypeNotStored);
    }
    if reader.read_entry(first.index)?.as_slice() != HWPX_MEDIA_TYPE.as_bytes() {
        return Err(GraphError::MimetypeInvalid);
    }
    Ok(())
}

fn read_and_hash_parts<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    entries: &[crate::EntryMetadata],
    root_index: usize,
) -> Result<HashedParts, GraphError> {
    let mut raw_hashes = BTreeMap::new();
    let mut package_bytes = None;
    for entry in entries.iter().filter(|entry| !entry.path.is_directory()) {
        let bytes = reader.read_entry(entry.index)?;
        raw_hashes.insert(entry.index, Sha256::digest(&bytes).into());
        if entry.index == root_index {
            package_bytes = Some(bytes);
        }
    }
    package_bytes
        .map(|bytes| HashedParts {
            raw_hashes,
            package_bytes: bytes,
        })
        .ok_or(GraphError::PackageDocumentMissing)
}

fn build_links(
    parsed: ParsedOpf,
    entries: &[crate::EntryMetadata],
    by_key: &BTreeMap<String, usize>,
    package_document: &PackagePath,
    limits: PackageGraphLimits,
) -> Result<GraphLinks, GraphError> {
    let relationship_count =
        parsed
            .items
            .len()
            .checked_add(parsed.spine.len())
            .ok_or(GraphError::XmlLimitExceeded {
                limit: "relationships",
            })?;
    if relationship_count > limits.config().max_relationships {
        return Err(GraphError::XmlLimitExceeded {
            limit: "relationships",
        });
    }
    let mut links = GraphLinks {
        relationships: Vec::new(),
        spine: Vec::new(),
        manifest_targets: BTreeSet::new(),
        spine_targets: BTreeSet::new(),
        media_by_target: BTreeMap::new(),
    };
    links
        .relationships
        .try_reserve_exact(relationship_count)
        .map_err(|_| GraphError::AllocationFailed)?;
    links
        .spine
        .try_reserve_exact(parsed.spine.len())
        .map_err(|_| GraphError::AllocationFailed)?;
    let mut id_to_target = BTreeMap::new();
    for item in parsed.items {
        let target_index = by_key
            .get(item.target.collision_key())
            .copied()
            .ok_or(GraphError::ManifestTargetMissing)?;
        if entries[target_index].path.is_directory() {
            return Err(GraphError::ManifestTargetMissing);
        }
        if !links
            .manifest_targets
            .insert(item.target.collision_key().to_owned())
        {
            return Err(GraphError::ManifestPathDuplicate);
        }
        let target = entries[target_index].path.clone();
        links
            .media_by_target
            .insert(target.collision_key().to_owned(), item.media_type.clone());
        id_to_target.insert(item.id.clone(), target.clone());
        links.relationships.push(Relationship {
            id: item.id,
            source: package_document.clone(),
            target,
            media_type: item.media_type,
            kind: RelationshipKind::ManifestItem,
            linear: true,
        });
    }
    for itemref in parsed.spine {
        let target = id_to_target
            .get(&itemref.idref)
            .cloned()
            .ok_or(GraphError::SpineDangling)?;
        if !links
            .spine_targets
            .insert(target.collision_key().to_owned())
        {
            return Err(GraphError::SpineDuplicate);
        }
        let media_type = links
            .media_by_target
            .get(target.collision_key())
            .cloned()
            .ok_or(GraphError::SpineDangling)?;
        links.relationships.push(Relationship {
            id: itemref.idref,
            source: package_document.clone(),
            target: target.clone(),
            media_type,
            kind: RelationshipKind::SpineItem,
            linear: itemref.linear,
        });
        links.spine.push(target);
    }
    Ok(links)
}

fn validate_closure(
    entries: &[crate::EntryMetadata],
    infrastructure: &BTreeSet<String>,
    manifest_targets: &BTreeSet<String>,
) -> Result<(), GraphError> {
    if entries.iter().any(|entry| {
        !entry.path.is_directory()
            && !infrastructure.contains(entry.path.collision_key())
            && !manifest_targets.contains(entry.path.collision_key())
    }) {
        return Err(GraphError::OrphanPart);
    }
    Ok(())
}

fn build_parts(
    entries: &[crate::EntryMetadata],
    raw_hashes: &BTreeMap<usize, [u8; 32]>,
    links: &GraphLinks,
    package_document: &PackagePath,
    package_document_media_type: &MediaType,
    root_media_by_target: &BTreeMap<String, MediaType>,
    limits: PackageGraphLimits,
) -> Result<Vec<PartRecord>, GraphError> {
    let mut parts = Vec::new();
    parts
        .try_reserve_exact(raw_hashes.len())
        .map_err(|_| GraphError::AllocationFailed)?;
    for entry in entries.iter().filter(|entry| !entry.path.is_directory()) {
        let key = entry.path.collision_key();
        let (media_type, role) = if let Some(media_type) = links.media_by_target.get(key) {
            let role = if links.spine_targets.contains(key) {
                PartRole::SpineDocument
            } else {
                PartRole::ManifestListed
            };
            (media_type.clone(), role)
        } else if let Some(media_type) = root_media_by_target.get(key) {
            (media_type.clone(), PartRole::Infrastructure)
        } else {
            (
                infrastructure_media_type(
                    entry.path.as_str(),
                    package_document,
                    package_document_media_type,
                    limits,
                )?,
                PartRole::Infrastructure,
            )
        };
        parts.push(PartRecord {
            path: entry.path.clone(),
            media_type,
            role,
            expanded_size: entry.expanded_size,
            raw_sha256: raw_hashes
                .get(&entry.index)
                .copied()
                .ok_or(GraphError::AllocationFailed)?,
        });
    }
    Ok(parts)
}

fn exact_index(entries: &[crate::EntryMetadata], path: &str) -> Option<usize> {
    entries
        .iter()
        .find(|entry| entry.path.as_str() == path)
        .map(|entry| entry.index)
}

fn parse_safe_xml(bytes: &[u8], limits: PackageGraphLimits) -> Result<SafeXmlDocument, GraphError> {
    let config = limits.config();
    let namespace_bindings = config
        .max_attributes_per_element
        .saturating_mul(config.max_xml_depth)
        .clamp(1, SafeXmlLimits::HARD_MAX_NAMESPACE_BINDINGS);
    let safe_limits = SafeXmlLimits::new(SafeXmlLimitConfig {
        input_bytes: config.max_metadata_bytes,
        events: config.max_xml_events,
        nodes: config.max_xml_events,
        depth: config.max_xml_depth,
        text_bytes: config.max_metadata_bytes.min(1024 * 1024),
        total_text_bytes: config.max_metadata_bytes,
        attributes_per_element: config.max_attributes_per_element,
        attribute_bytes: config.max_attribute_bytes,
        namespace_bindings,
    })
    .map_err(|error| map_safe_xml_error(&error))?;
    SafeXmlDocument::parse(bytes, safe_limits).map_err(|error| map_safe_xml_error(&error))
}

fn map_safe_xml_error(error: &SafeXmlError) -> GraphError {
    match error {
        SafeXmlError::InputLimit => GraphError::MetadataTooLarge { kind: "xml" },
        SafeXmlError::EventLimit => GraphError::XmlLimitExceeded { limit: "events" },
        SafeXmlError::NodeLimit => GraphError::XmlLimitExceeded { limit: "nodes" },
        SafeXmlError::DepthLimit => GraphError::XmlLimitExceeded { limit: "depth" },
        SafeXmlError::TextLimit => GraphError::XmlLimitExceeded { limit: "text" },
        SafeXmlError::AttributeLimit => GraphError::XmlLimitExceeded {
            limit: "attributes",
        },
        SafeXmlError::AttributeBytesLimit => GraphError::XmlLimitExceeded {
            limit: "attribute_bytes",
        },
        SafeXmlError::NamespaceLimit => GraphError::XmlLimitExceeded {
            limit: "namespace_bindings",
        },
        SafeXmlError::NamespaceInvalid => GraphError::XmlNamespaceInvalid,
        SafeXmlError::DtdForbidden
        | SafeXmlError::CustomEntityForbidden
        | SafeXmlError::ProcessingInstructionForbidden
        | SafeXmlError::CdataForbidden
        | SafeXmlError::EncodingForbidden => GraphError::XmlForbiddenConstruct,
        SafeXmlError::AllocationFailed => GraphError::AllocationFailed,
        SafeXmlError::InvalidLimit { .. }
        | SafeXmlError::InvalidLimitRelation
        | SafeXmlError::DuplicateAttribute
        | SafeXmlError::Malformed => GraphError::XmlMalformed,
    }
}

fn parse_container(
    bytes: &[u8],
    package_limits: PackageLimits,
    limits: PackageGraphLimits,
) -> Result<ContainerRoots, GraphError> {
    let document = parse_safe_xml(bytes, limits)?;
    let mut stack = Vec::<String>::new();
    stack
        .try_reserve_exact(limits.config().max_xml_depth)
        .map_err(|_| GraphError::AllocationFailed)?;
    let mut state = ContainerState {
        root_seen: false,
        package_root: None,
        rootfiles: Vec::new(),
        rootfile_keys: BTreeSet::new(),
    };
    state
        .rootfiles
        .try_reserve(limits.config().max_relationships.min(16))
        .map_err(|_| GraphError::AllocationFailed)?;
    for event in document.events {
        match event {
            SafeXmlEvent::Start(element) => {
                handle_container_element(
                    &element,
                    stack.last().map(String::as_str),
                    &mut state,
                    package_limits,
                    limits,
                )?;
                stack.push(element.qualified_name);
            }
            SafeXmlEvent::Empty(element) => {
                handle_container_element(
                    &element,
                    stack.last().map(String::as_str),
                    &mut state,
                    package_limits,
                    limits,
                )?;
            }
            SafeXmlEvent::End => {
                stack.pop().ok_or(GraphError::XmlMalformed)?;
            }
            SafeXmlEvent::Declaration
            | SafeXmlEvent::Text { .. }
            | SafeXmlEvent::Reference
            | SafeXmlEvent::Comment => {}
        }
    }
    if !stack.is_empty() || !state.root_seen {
        return Err(GraphError::XmlMalformed);
    }
    if state.rootfiles.is_empty() {
        return Err(GraphError::ContainerRootfileMissing);
    }
    let package = state
        .package_root
        .ok_or(GraphError::ContainerRootfileMissing)?;
    Ok(ContainerRoots {
        package,
        all: state.rootfiles,
    })
}

#[derive(Debug)]
struct ContainerState {
    root_seen: bool,
    package_root: Option<RootfileRecord>,
    rootfiles: Vec<RootfileRecord>,
    rootfile_keys: BTreeSet<String>,
}

fn handle_container_element(
    element: &SafeXmlElement,
    parent: Option<&str>,
    state: &mut ContainerState,
    package_limits: PackageLimits,
    limits: PackageGraphLimits,
) -> Result<(), GraphError> {
    let local = element.local_name.as_str();
    let attributes = &element.attributes;
    let depth = element.depth;
    if depth == 1 {
        if local != "container" || state.root_seen {
            return Err(GraphError::XmlMalformed);
        }
        require_namespace(element.namespace.as_deref(), CONTAINER_NS)?;
        state.root_seen = true;
        return Ok(());
    }
    require_namespace(element.namespace.as_deref(), CONTAINER_NS)?;
    match (depth, local) {
        (2, "rootfiles") if parent.is_some_and(|value| qname_local(value) == "container") => Ok(()),
        (3, "rootfile") if parent.is_some_and(|value| qname_local(value) == "rootfiles") => {
            let raw = attributes
                .get("full-path")
                .ok_or(GraphError::ContainerRootfileInvalid)?;
            let media_type = attributes
                .get("media-type")
                .ok_or(GraphError::ContainerRootfileInvalid)?;
            if state.rootfiles.len() >= limits.config().max_relationships {
                return Err(GraphError::XmlLimitExceeded {
                    limit: "relationships",
                });
            }
            let rootfile = RootfileRecord {
                path: resolve_reference(None, raw, package_limits)?,
                media_type: MediaType::parse(media_type, limits)?,
            };
            if !state
                .rootfile_keys
                .insert(rootfile.path.collision_key().to_owned())
            {
                return Err(GraphError::ContainerRootfileDuplicate);
            }
            if is_package_root_media(rootfile.media_type.as_str())
                && state.package_root.replace(rootfile.clone()).is_some()
            {
                return Err(GraphError::ContainerRootfileDuplicate);
            }
            state
                .rootfiles
                .try_reserve(1)
                .map_err(|_| GraphError::AllocationFailed)?;
            state.rootfiles.push(rootfile);
            Ok(())
        }
        _ => Err(GraphError::XmlMalformed),
    }
}

fn parse_opf(
    bytes: &[u8],
    package_document: &PackagePath,
    by_key: &BTreeMap<String, usize>,
    package_limits: PackageLimits,
    limits: PackageGraphLimits,
) -> Result<ParsedOpf, GraphError> {
    let document = parse_safe_xml(bytes, limits)?;
    let mut stack = Vec::<String>::new();
    stack
        .try_reserve_exact(limits.config().max_xml_depth)
        .map_err(|_| GraphError::AllocationFailed)?;
    let mut root_seen = false;
    let mut manifest_seen = false;
    let mut spine_seen = false;
    let mut ids = BTreeSet::new();
    let mut items = Vec::new();
    let mut spine = Vec::new();
    items
        .try_reserve_exact(limits.config().max_relationships)
        .map_err(|_| GraphError::AllocationFailed)?;
    spine
        .try_reserve_exact(limits.config().max_relationships)
        .map_err(|_| GraphError::AllocationFailed)?;
    for event in document.events {
        match event {
            SafeXmlEvent::Start(element) => {
                handle_opf_element(
                    &element,
                    stack.last().map(String::as_str),
                    &mut root_seen,
                    &mut manifest_seen,
                    &mut spine_seen,
                    &mut ids,
                    &mut items,
                    &mut spine,
                    package_document,
                    by_key,
                    package_limits,
                    limits,
                )?;
                stack.push(element.qualified_name);
            }
            SafeXmlEvent::Empty(element) => {
                handle_opf_element(
                    &element,
                    stack.last().map(String::as_str),
                    &mut root_seen,
                    &mut manifest_seen,
                    &mut spine_seen,
                    &mut ids,
                    &mut items,
                    &mut spine,
                    package_document,
                    by_key,
                    package_limits,
                    limits,
                )?;
            }
            SafeXmlEvent::End => {
                stack.pop().ok_or(GraphError::XmlMalformed)?;
            }
            SafeXmlEvent::Declaration
            | SafeXmlEvent::Text { .. }
            | SafeXmlEvent::Reference
            | SafeXmlEvent::Comment => {}
        }
    }
    if !stack.is_empty() || !root_seen {
        return Err(GraphError::XmlMalformed);
    }
    if !manifest_seen {
        return Err(GraphError::ManifestMissing);
    }
    if !spine_seen {
        return Err(GraphError::SpineMissing);
    }
    Ok(ParsedOpf { items, spine })
}

#[allow(clippy::too_many_arguments)]
fn handle_opf_element(
    element: &SafeXmlElement,
    parent: Option<&str>,
    root_seen: &mut bool,
    manifest_seen: &mut bool,
    spine_seen: &mut bool,
    ids: &mut BTreeSet<String>,
    items: &mut Vec<ManifestItem>,
    spine: &mut Vec<SpineItem>,
    package_document: &PackagePath,
    by_key: &BTreeMap<String, usize>,
    package_limits: PackageLimits,
    limits: PackageGraphLimits,
) -> Result<(), GraphError> {
    let local = element.local_name.as_str();
    let attributes = &element.attributes;
    let depth = element.depth;
    if depth == 1 {
        if local != "package" || *root_seen {
            return Err(GraphError::XmlMalformed);
        }
        require_namespace(element.namespace.as_deref(), OPF_NS)?;
        *root_seen = true;
        return Ok(());
    }
    let structural = namespace_matches(element.namespace.as_deref(), OPF_NS);
    let expected_structural_position = (depth == 2 && matches!(local, "manifest" | "spine"))
        || (depth == 3
            && matches!(local, "item" | "itemref")
            && parent.is_some_and(|value| matches!(qname_local(value), "manifest" | "spine")));
    if expected_structural_position && !structural {
        return Err(GraphError::XmlNamespaceInvalid);
    }
    if depth == 2 && structural && local == "manifest" {
        if *manifest_seen {
            return Err(GraphError::ManifestDuplicate);
        }
        *manifest_seen = true;
        return Ok(());
    }
    if depth == 2 && structural && local == "spine" {
        if *spine_seen {
            return Err(GraphError::SpineDuplicateSection);
        }
        *spine_seen = true;
        return Ok(());
    }
    if depth == 3
        && structural
        && local == "item"
        && parent.is_some_and(|value| qname_local(value) == "manifest")
    {
        let id = attributes
            .get("id")
            .filter(|value| !value.is_empty())
            .cloned()
            .ok_or(GraphError::ManifestItemInvalid)?;
        let href = attributes
            .get("href")
            .filter(|value| !value.is_empty())
            .ok_or(GraphError::ManifestItemInvalid)?;
        let media_type = attributes
            .get("media-type")
            .ok_or(GraphError::ManifestItemInvalid)?;
        if !ids.insert(id.clone()) {
            return Err(GraphError::ManifestIdDuplicate);
        }
        if items.len() >= limits.config().max_relationships {
            return Err(GraphError::XmlLimitExceeded {
                limit: "relationships",
            });
        }
        items.push(ManifestItem {
            id,
            target: resolve_manifest_reference(package_document, href, by_key, package_limits)?,
            media_type: MediaType::parse(media_type, limits)?,
        });
        return Ok(());
    }
    if depth == 3
        && structural
        && local == "itemref"
        && parent.is_some_and(|value| qname_local(value) == "spine")
    {
        let idref = attributes
            .get("idref")
            .filter(|value| !value.is_empty())
            .cloned()
            .ok_or(GraphError::ManifestItemInvalid)?;
        let linear = match attributes.get("linear").map(String::as_str) {
            None | Some("yes") => true,
            Some("no") => false,
            Some(_) => return Err(GraphError::ManifestItemInvalid),
        };
        if spine.len() >= limits.config().max_relationships {
            return Err(GraphError::XmlLimitExceeded {
                limit: "relationships",
            });
        }
        spine.push(SpineItem { idref, linear });
        return Ok(());
    }
    if structural && matches!(local, "manifest" | "spine" | "item" | "itemref") {
        return Err(GraphError::XmlMalformed);
    }
    Ok(())
}

fn namespace_matches(namespace: Option<&str>, expected: &str) -> bool {
    namespace == Some(expected) || (expected == OPF_NS && namespace == Some(OPF_NS_HANCOM_2020))
}

fn require_namespace(namespace: Option<&str>, expected: &str) -> Result<(), GraphError> {
    if !namespace_matches(namespace, expected) {
        return Err(GraphError::XmlNamespaceInvalid);
    }
    Ok(())
}

fn split_qname(name: &str) -> (&str, &str) {
    name.find(':')
        .map_or(("", name), |index| (&name[..index], &name[index + 1..]))
}

fn qname_local(name: &str) -> &str {
    split_qname(name).1
}

fn resolve_reference(
    base: Option<&PackagePath>,
    raw: &str,
    limits: PackageLimits,
) -> Result<PackagePath, GraphError> {
    if raw.is_empty()
        || raw.starts_with('/')
        || raw.starts_with("//")
        || raw.contains('\\')
        || raw.contains('?')
        || raw.contains('#')
    {
        return Err(GraphError::InvalidRelationshipPath);
    }
    if raw
        .split('/')
        .next()
        .is_some_and(|first| first.bytes().position(|byte| byte == b':').is_some())
    {
        return Err(GraphError::ExternalRelationshipBlocked);
    }
    let decoded = percent_decode(raw)?;
    let decoded = std::str::from_utf8(&decoded).map_err(|_| GraphError::InvalidRelationshipPath)?;
    if decoded.contains(['?', '#']) {
        return Err(GraphError::InvalidRelationshipPath);
    }
    let mut segments = Vec::<&str>::new();
    segments
        .try_reserve_exact(limits.config().max_path_depth)
        .map_err(|_| GraphError::AllocationFailed)?;
    if let Some(base) = base {
        let mut base_segments = base.as_str().split('/').collect::<Vec<_>>();
        base_segments.pop();
        segments.extend(base_segments);
    }
    for segment in decoded.split('/') {
        match segment {
            "" => return Err(GraphError::InvalidRelationshipPath),
            "." => {}
            ".." => {
                segments.pop().ok_or(GraphError::RelationshipEscapesRoot)?;
            }
            _ => {
                if segments.len() >= limits.config().max_path_depth {
                    return Err(GraphError::InvalidRelationshipPath);
                }
                segments.push(segment);
            }
        }
    }
    let joined = segments.join("/");
    PackagePath::parse(joined.as_bytes(), usize::MAX, limits)
        .map_err(|_| GraphError::InvalidRelationshipPath)
}

fn resolve_manifest_reference(
    package_document: &PackagePath,
    raw: &str,
    by_key: &BTreeMap<String, usize>,
    limits: PackageLimits,
) -> Result<PackagePath, GraphError> {
    let relative = resolve_reference(Some(package_document), raw, limits);
    let root = resolve_reference(None, raw, limits);
    let mut existing = Vec::new();
    existing
        .try_reserve_exact(2)
        .map_err(|_| GraphError::AllocationFailed)?;
    for candidate in [relative.as_ref().ok(), root.as_ref().ok()]
        .into_iter()
        .flatten()
    {
        if by_key.contains_key(candidate.collision_key())
            && !existing
                .iter()
                .any(|path: &PackagePath| path.collision_key() == candidate.collision_key())
        {
            existing.push(candidate.clone());
        }
    }
    match existing.len() {
        1 => Ok(existing.remove(0)),
        2 => Err(GraphError::ManifestTargetAmbiguous),
        _ => relative.or(root),
    }
}

fn percent_decode(raw: &str) -> Result<Vec<u8>, GraphError> {
    let bytes = raw.as_bytes();
    let mut output = Vec::new();
    output
        .try_reserve_exact(bytes.len())
        .map_err(|_| GraphError::AllocationFailed)?;
    let mut index = 0_usize;
    while index < bytes.len() {
        if bytes[index] == b'%' {
            if index + 2 >= bytes.len() {
                return Err(GraphError::InvalidRelationshipPath);
            }
            let high = hex_value(bytes[index + 1]).ok_or(GraphError::InvalidRelationshipPath)?;
            let low = hex_value(bytes[index + 2]).ok_or(GraphError::InvalidRelationshipPath)?;
            output.push((high << 4) | low);
            index += 3;
        } else {
            output.push(bytes[index]);
            index += 1;
        }
    }
    Ok(output)
}

fn hex_value(byte: u8) -> Option<u8> {
    match byte {
        b'0'..=b'9' => Some(byte - b'0'),
        b'a'..=b'f' => Some(byte - b'a' + 10),
        b'A'..=b'F' => Some(byte - b'A' + 10),
        _ => None,
    }
}

fn infrastructure_keys(
    package_document: &PackagePath,
    rootfiles: &[RootfileRecord],
    limits: PackageLimits,
) -> Result<BTreeSet<String>, GraphError> {
    let mut result = BTreeSet::new();
    for path in [
        "mimetype",
        "version.xml",
        CONTAINER_PATH,
        "META-INF/manifest.xml",
        "META-INF/metadata.xml",
        "META-INF/signatures.xml",
        "META-INF/encryption.xml",
        "META-INF/rights.xml",
        "Preview/PrvImage.png",
        package_document.as_str(),
    ] {
        let parsed = PackagePath::parse(path.as_bytes(), usize::MAX, limits)
            .map_err(|_| GraphError::InvalidRelationshipPath)?;
        result.insert(parsed.collision_key().to_owned());
    }
    for rootfile in rootfiles {
        result.insert(rootfile.path.collision_key().to_owned());
    }
    Ok(result)
}

fn validate_rootfile_targets(
    roots: &ContainerRoots,
    entries: &[crate::EntryMetadata],
    by_key: &BTreeMap<String, usize>,
) -> Result<(), GraphError> {
    for rootfile in &roots.all {
        let missing_error = if rootfile.path == roots.package.path {
            GraphError::PackageDocumentMissing
        } else {
            GraphError::ContainerRootfileTargetMissing
        };
        let index = by_key
            .get(rootfile.path.collision_key())
            .copied()
            .ok_or(missing_error)?;
        if entries[index].path.is_directory() {
            return Err(if rootfile.path == roots.package.path {
                GraphError::PackageDocumentMissing
            } else {
                GraphError::ContainerRootfileTargetMissing
            });
        }
    }
    Ok(())
}

fn is_package_root_media(media_type: &str) -> bool {
    matches!(
        media_type,
        HWPML_PACKAGE_MEDIA_TYPE | OEBPS_PACKAGE_MEDIA_TYPE
    )
}

fn infrastructure_media_type(
    path: &str,
    package_document: &PackagePath,
    package_document_media_type: &MediaType,
    limits: PackageGraphLimits,
) -> Result<MediaType, GraphError> {
    if path == "mimetype" {
        MediaType::parse(HWPX_MEDIA_TYPE, limits)
    } else if path == "Preview/PrvImage.png" {
        MediaType::parse("image/png", limits)
    } else if path == package_document.as_str() {
        Ok(package_document_media_type.clone())
    } else {
        MediaType::parse("application/xml", limits)
    }
}
