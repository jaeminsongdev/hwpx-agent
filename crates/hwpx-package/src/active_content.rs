use std::collections::{BTreeMap, BTreeSet};
use std::fmt::{self, Debug};
use std::io::{self, Read, Seek};

use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    BoundedZipReader, GraphError, PackageError, PackageGraph, PackageGraphLimits,
    PreservingXmlDocument, PreservingXmlError,
};

pub const ACTIVE_CONTENT_SCHEMA_VERSION: &str = "hwpx-agent.active-content-inventory/v1";
pub const ACTIVE_CONTENT_PROFILE_ID: &str =
    "hwpx-agent.active-content.hwpml-2011-opaque-preserve-blocked/v1";

const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ActiveContentLimitConfig {
    pub max_inventory_items: usize,
    pub max_identifier_bytes: usize,
    pub max_json_bytes: usize,
}

impl Default for ActiveContentLimitConfig {
    fn default() -> Self {
        Self {
            max_inventory_items: 65_536,
            max_identifier_bytes: 1_024,
            max_json_bytes: 8 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ActiveContentLimits(ActiveContentLimitConfig);

impl ActiveContentLimits {
    pub const HARD_MAX_INVENTORY_ITEMS: usize = 262_144;
    pub const HARD_MAX_IDENTIFIER_BYTES: usize = 16 * 1024;
    pub const HARD_MAX_JSON_BYTES: usize = 64 * 1024 * 1024;

    /// Creates finite package active-content limits.
    ///
    /// # Errors
    ///
    /// Rejects zero values and values above the hard ceilings.
    pub fn new(config: ActiveContentLimitConfig) -> Result<Self, ActiveContentError> {
        if config.max_inventory_items == 0
            || config.max_inventory_items > Self::HARD_MAX_INVENTORY_ITEMS
            || config.max_identifier_bytes == 0
            || config.max_identifier_bytes > Self::HARD_MAX_IDENTIFIER_BYTES
            || config.max_json_bytes == 0
            || config.max_json_bytes > Self::HARD_MAX_JSON_BYTES
        {
            return Err(ActiveContentError::InvalidLimit);
        }
        Ok(Self(config))
    }

    #[must_use]
    pub const fn config(self) -> ActiveContentLimitConfig {
        self.0
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ActiveContentResourceKind {
    OpaqueOle,
    Audio,
    Video,
    Executable,
    ScriptMacro,
    OpaqueBinary,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ActiveContentControlKind {
    Ole,
    Video,
    FormButton,
    FormComboBox,
    FormListBox,
    FormEdit,
    ScriptMacro,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ActiveContentDisposition {
    PreservePassive,
    PreserveBlocked,
    Quarantine,
    ReviewRequired,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ActiveContentSignature {
    Verified,
    Unverified,
    NotApplicable,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ActivationKind {
    Ole,
    Multimedia,
    EmbeddedExecutable,
    ScriptMacro,
    FormCommand,
    ExternalLink,
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ActiveContentResource {
    path: String,
    relationship_ids: Vec<String>,
    media_type: String,
    kind: ActiveContentResourceKind,
    disposition: ActiveContentDisposition,
    signature: ActiveContentSignature,
    expanded_size: u64,
    raw_sha256: String,
}

impl ActiveContentResource {
    #[must_use]
    pub fn path(&self) -> &str {
        &self.path
    }

    #[must_use]
    pub fn relationship_ids(&self) -> &[String] {
        &self.relationship_ids
    }

    #[must_use]
    pub fn media_type(&self) -> &str {
        &self.media_type
    }

    #[must_use]
    pub const fn kind(&self) -> ActiveContentResourceKind {
        self.kind
    }

    #[must_use]
    pub const fn disposition(&self) -> ActiveContentDisposition {
        self.disposition
    }

    #[must_use]
    pub const fn signature(&self) -> ActiveContentSignature {
        self.signature
    }

    #[must_use]
    pub const fn expanded_size(&self) -> u64 {
        self.expanded_size
    }

    #[must_use]
    pub fn raw_sha256(&self) -> &str {
        &self.raw_sha256
    }
}

impl Debug for ActiveContentResource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ActiveContentResource")
            .field("kind", &self.kind)
            .field("disposition", &self.disposition)
            .field("signature", &self.signature)
            .field("expanded_size", &self.expanded_size)
            .field("identity", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ActiveContentControl {
    document_part: String,
    element_ordinal: usize,
    kind: ActiveContentControlKind,
    disposition: ActiveContentDisposition,
    relationship_id: Option<String>,
    resource_path: Option<String>,
    external: bool,
    command_present: bool,
    element_sha256: String,
}

impl ActiveContentControl {
    #[must_use]
    pub fn document_part(&self) -> &str {
        &self.document_part
    }

    #[must_use]
    pub const fn element_ordinal(&self) -> usize {
        self.element_ordinal
    }

    #[must_use]
    pub const fn kind(&self) -> ActiveContentControlKind {
        self.kind
    }

    #[must_use]
    pub const fn disposition(&self) -> ActiveContentDisposition {
        self.disposition
    }

    #[must_use]
    pub fn relationship_id(&self) -> Option<&str> {
        self.relationship_id.as_deref()
    }

    #[must_use]
    pub fn resource_path(&self) -> Option<&str> {
        self.resource_path.as_deref()
    }

    #[must_use]
    pub const fn external(&self) -> bool {
        self.external
    }

    #[must_use]
    pub const fn command_present(&self) -> bool {
        self.command_present
    }

    #[must_use]
    pub fn element_sha256(&self) -> &str {
        &self.element_sha256
    }
}

impl Debug for ActiveContentControl {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ActiveContentControl")
            .field("element_ordinal", &self.element_ordinal)
            .field("kind", &self.kind)
            .field("disposition", &self.disposition)
            .field("external", &self.external)
            .field("command_present", &self.command_present)
            .field("identity", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, Serialize)]
pub struct ActiveContentCounts {
    pub resources: usize,
    pub controls: usize,
    pub blocked: usize,
    pub quarantined: usize,
    pub review_required: usize,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ActiveContentInventory {
    schema_version: &'static str,
    profile_id: &'static str,
    source_graph_sha256: String,
    state_sha256: String,
    resources: Vec<ActiveContentResource>,
    controls: Vec<ActiveContentControl>,
    counts: ActiveContentCounts,
    activation_allowed: bool,
}

impl ActiveContentInventory {
    /// Builds a complete bounded inventory after rebuilding the authoritative package graph.
    /// Every active resource is integrity-read and bound to its manifest relationship and digest.
    ///
    /// # Errors
    ///
    /// Fails closed for graph drift, unsafe XML, namespace spoofing, dangling references,
    /// conflicting resource roles, signature mismatch, or a finite-limit violation.
    pub fn scan<R: Read + Seek>(
        reader: &mut BoundedZipReader<R>,
        supplied_graph: &PackageGraph,
        graph_limits: PackageGraphLimits,
        limits: ActiveContentLimits,
    ) -> Result<Self, ActiveContentError> {
        let authoritative = PackageGraph::build(reader, graph_limits)?;
        if &authoritative != supplied_graph {
            return Err(ActiveContentError::SourceGraphDrift);
        }

        let relationship_by_id = authoritative
            .relationships
            .iter()
            .map(|relationship| (relationship.id.as_str(), relationship))
            .collect::<BTreeMap<_, _>>();
        let part_by_key = authoritative
            .parts
            .iter()
            .map(|part| (part.path.collision_key(), part))
            .collect::<BTreeMap<_, _>>();
        let entry_by_key = reader
            .entries()
            .iter()
            .filter(|entry| !entry.path.is_directory())
            .map(|entry| (entry.path.collision_key().to_owned(), entry.index))
            .collect::<BTreeMap<_, _>>();

        let (mut controls, referenced_kinds) = scan_controls(
            reader,
            &authoritative,
            &entry_by_key,
            &relationship_by_id,
            &part_by_key,
            limits,
        )?;
        let mut resources = scan_resources(
            reader,
            &authoritative,
            &entry_by_key,
            &referenced_kinds,
            limits,
        )?;
        if controls
            .len()
            .checked_add(resources.len())
            .is_none_or(|total| total > limits.0.max_inventory_items)
        {
            return Err(ActiveContentError::InventoryLimit);
        }
        resources.sort_unstable();
        controls.sort_unstable();
        ensure_unique_resources(&resources)?;

        let counts = counts(&resources, &controls);
        let state_sha256 = active_state_sha256(&resources, &controls, limits)?;
        let inventory = Self {
            schema_version: ACTIVE_CONTENT_SCHEMA_VERSION,
            profile_id: ACTIVE_CONTENT_PROFILE_ID,
            source_graph_sha256: graph_sha256(&authoritative),
            state_sha256,
            resources,
            controls,
            counts,
            activation_allowed: false,
        };
        // Validate the exact same JSON size without materializing and discarding
        // the whole inventory on every scan. No check or limit is skipped.
        let mut count = InventoryJsonWriter::new(InventoryJsonSink::Count, limits);
        serde_json::to_writer(&mut count, &inventory).map_err(|_| ActiveContentError::OutputLimit)?;
        Ok(inventory)
    }

    #[must_use]
    pub fn resources(&self) -> &[ActiveContentResource] {
        &self.resources
    }

    #[must_use]
    pub fn controls(&self) -> &[ActiveContentControl] {
        &self.controls
    }

    #[must_use]
    pub const fn counts(&self) -> ActiveContentCounts {
        self.counts
    }

    #[must_use]
    pub fn source_graph_sha256(&self) -> &str {
        &self.source_graph_sha256
    }

    #[must_use]
    pub fn state_sha256(&self) -> &str {
        &self.state_sha256
    }

    #[must_use]
    pub const fn activation_allowed(&self) -> bool {
        self.activation_allowed
    }

    /// Serializes the deterministic inventory without embedded payload bytes or XML text.
    ///
    /// # Errors
    ///
    /// Returns an output-limit failure when the bounded JSON cannot be produced.
    pub fn canonical_json(
        &self,
        limits: ActiveContentLimits,
    ) -> Result<Vec<u8>, ActiveContentError> {
        let mut writer = InventoryJsonWriter::new(InventoryJsonSink::Bytes(Vec::new()), limits);
        serde_json::to_writer(&mut writer, self).map_err(|_| ActiveContentError::OutputLimit)?;
        match writer.sink {
            InventoryJsonSink::Bytes(bytes) => Ok(bytes),
            _ => Err(ActiveContentError::OutputLimit),
        }
    }

    /// The normal product tier never authorizes active-content execution.
    ///
    /// # Errors
    ///
    /// Always returns `ActivationDenied`; the action is accepted only for typed diagnostics.
    pub const fn authorize(&self, action: ActivationKind) -> Result<(), ActiveContentError> {
        Err(ActiveContentError::ActivationDenied { action })
    }

    /// Proves that every inventoried resource and control is unchanged across a package edit.
    /// Unrelated package parts may change, but active content may not be added, removed, retargeted,
    /// or rewritten in the opaque-preservation tier.
    ///
    /// # Errors
    ///
    /// Returns a typed preservation failure for any active-content state drift.
    pub fn verify_preserved(
        &self,
        target: &Self,
    ) -> Result<ActiveContentPreservationReceipt, ActiveContentError> {
        if self.resources != target.resources
            || control_states(&self.controls) != control_states(&target.controls)
        {
            return Err(ActiveContentError::ActiveStateDrift);
        }
        Ok(ActiveContentPreservationReceipt {
            profile_id: ACTIVE_CONTENT_PROFILE_ID,
            source_state_sha256: self.state_sha256.clone(),
            target_state_sha256: target.state_sha256.clone(),
            resources: self.resources.len(),
            controls: self.controls.len(),
            byte_exact_resources: self.resources.len(),
            activation_allowed: false,
        })
    }
}

impl Debug for ActiveContentInventory {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ActiveContentInventory")
            .field("profile_id", &self.profile_id)
            .field("counts", &self.counts)
            .field("activation_allowed", &self.activation_allowed)
            .field("identities", &"<redacted>")
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct ActiveContentPreservationReceipt {
    pub profile_id: &'static str,
    pub source_state_sha256: String,
    pub target_state_sha256: String,
    pub resources: usize,
    pub controls: usize,
    pub byte_exact_resources: usize,
    pub activation_allowed: bool,
}

impl Debug for ActiveContentPreservationReceipt {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ActiveContentPreservationReceipt")
            .field("profile_id", &self.profile_id)
            .field("resources", &self.resources)
            .field("controls", &self.controls)
            .field("byte_exact_resources", &self.byte_exact_resources)
            .field("activation_allowed", &self.activation_allowed)
            .field("digests", &"<redacted>")
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Error)]
pub enum ActiveContentError {
    #[error("active-content limits are invalid")]
    InvalidLimit,
    #[error("active-content inventory exceeds a finite limit")]
    InventoryLimit,
    #[error("active-content JSON exceeds a finite limit")]
    OutputLimit,
    #[error("active-content package graph drifted")]
    SourceGraphDrift,
    #[error("active-content XML uses a spoofed namespace")]
    NamespaceSpoof,
    #[error("active-content XML attribute is missing, duplicated, or oversized")]
    InvalidAttribute,
    #[error("active-content reference is dangling or targets an XML part")]
    DanglingReference,
    #[error("one resource has conflicting active-content roles")]
    ConflictingResourceRole,
    #[error("known multimedia declaration does not match its signature")]
    SignatureMismatch,
    #[error("active-content state was added, removed, retargeted, or rewritten")]
    ActiveStateDrift,
    #[error("active-content activation is denied in the normal product tier")]
    ActivationDenied { action: ActivationKind },
    #[error("active-content allocation failed")]
    AllocationFailed,
    #[error("active-content package graph validation failed")]
    Graph(#[from] GraphError),
    #[error("active-content package read failed")]
    Package(#[from] PackageError),
    #[error("active-content preserving XML admission failed")]
    Xml(#[from] PreservingXmlError),
}

impl ActiveContentError {
    #[must_use]
    pub fn code(&self) -> &'static str {
        match self {
            Self::InvalidLimit => "active_content_invalid_limit",
            Self::InventoryLimit => "active_content_inventory_limit",
            Self::OutputLimit => "active_content_output_limit",
            Self::SourceGraphDrift => "active_content_source_graph_drift",
            Self::NamespaceSpoof => "active_content_namespace_spoof",
            Self::InvalidAttribute => "active_content_invalid_attribute",
            Self::DanglingReference => "active_content_dangling_reference",
            Self::ConflictingResourceRole => "active_content_conflicting_resource_role",
            Self::SignatureMismatch => "active_content_signature_mismatch",
            Self::ActiveStateDrift => "active_content_state_drift",
            Self::ActivationDenied { .. } => "active_content_activation_denied",
            Self::AllocationFailed => "active_content_allocation_failed",
            Self::Graph(error) => error.code(),
            Self::Package(error) => error.code(),
            Self::Xml(error) => error.code(),
        }
    }
}

struct ResourceClassification {
    kind: ActiveContentResourceKind,
    disposition: ActiveContentDisposition,
    signature: ActiveContentSignature,
}

fn scan_controls<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    entry_by_key: &BTreeMap<String, usize>,
    relationships: &BTreeMap<&str, &crate::Relationship>,
    parts: &BTreeMap<&str, &crate::PartRecord>,
    limits: ActiveContentLimits,
) -> Result<
    (
        Vec<ActiveContentControl>,
        BTreeMap<String, ActiveContentResourceKind>,
    ),
    ActiveContentError,
> {
    let mut controls = Vec::new();
    let mut referenced = BTreeMap::new();
    for part in &graph.parts {
        if !is_xml_part(part.path.as_str(), part.media_type.as_str()) {
            continue;
        }
        let entry_index = *entry_by_key
            .get(part.path.collision_key())
            .ok_or(ActiveContentError::SourceGraphDrift)?;
        let bytes = reader.read_entry(entry_index)?;
        validate_part_identity(part, &bytes)?;
        scan_xml_part(
            &PreservingXmlDocument::parse(&bytes)?,
            part.path.as_str(),
            relationships,
            parts,
            limits,
            &mut controls,
            &mut referenced,
        )?;
    }
    Ok((controls, referenced))
}

fn scan_resources<R: Read + Seek>(
    reader: &mut BoundedZipReader<R>,
    graph: &PackageGraph,
    entry_by_key: &BTreeMap<String, usize>,
    referenced: &BTreeMap<String, ActiveContentResourceKind>,
    limits: ActiveContentLimits,
) -> Result<Vec<ActiveContentResource>, ActiveContentError> {
    let mut relationship_ids = BTreeMap::<String, Vec<String>>::new();
    for relationship in &graph.relationships {
        if relationship.id.is_empty() || relationship.id.len() > limits.0.max_identifier_bytes {
            return Err(ActiveContentError::InvalidAttribute);
        }
        relationship_ids
            .entry(relationship.target.collision_key().to_owned())
            .or_default()
            .push(relationship.id.clone());
    }
    for ids in relationship_ids.values_mut() {
        ids.sort_unstable();
    }
    let mut resources = Vec::new();
    for part in &graph.parts {
        let referenced_kind = referenced.get(part.path.collision_key()).copied();
        if referenced_kind.is_none()
            && !is_inventory_resource(part.path.as_str(), part.media_type.as_str())
        {
            continue;
        }
        ensure_capacity(resources.len(), limits)?;
        let entry_index = *entry_by_key
            .get(part.path.collision_key())
            .ok_or(ActiveContentError::SourceGraphDrift)?;
        let bytes = reader.read_entry(entry_index)?;
        validate_part_identity(part, &bytes)?;
        let classified = classify_resource(
            part.path.as_str(),
            part.media_type.as_str(),
            &bytes,
            referenced_kind,
        )?;
        resources.push(ActiveContentResource {
            path: part.path.as_str().to_owned(),
            relationship_ids: relationship_ids
                .get(part.path.collision_key())
                .cloned()
                .unwrap_or_default(),
            media_type: part.media_type.as_str().to_owned(),
            kind: classified.kind,
            disposition: classified.disposition,
            signature: classified.signature,
            expanded_size: part.expanded_size,
            raw_sha256: hex(part.raw_sha256),
        });
    }
    Ok(resources)
}

fn validate_part_identity(
    part: &crate::PartRecord,
    bytes: &[u8],
) -> Result<(), ActiveContentError> {
    if bytes.len() as u64 != part.expanded_size
        || <[u8; 32]>::from(Sha256::digest(bytes)) != part.raw_sha256
    {
        return Err(ActiveContentError::SourceGraphDrift);
    }
    Ok(())
}

fn scan_xml_part(
    document: &PreservingXmlDocument,
    document_part: &str,
    relationships: &BTreeMap<&str, &crate::Relationship>,
    parts: &BTreeMap<&str, &crate::PartRecord>,
    limits: ActiveContentLimits,
    controls: &mut Vec<ActiveContentControl>,
    referenced_kinds: &mut BTreeMap<String, ActiveContentResourceKind>,
) -> Result<(), ActiveContentError> {
    for (ordinal, element) in document.elements().iter().enumerate() {
        let local = element.name().local_name();
        if !matches!(
            local,
            "ole" | "video" | "btn" | "comboBox" | "listBox" | "edit" | "script"
        ) {
            continue;
        }
        if element.name().namespace() != Some(PARAGRAPH_NS) {
            return Err(ActiveContentError::NamespaceSpoof);
        }
        if local == "script"
            && element.parent().is_some_and(|parent| {
                document.elements()[parent].name().namespace() == Some(PARAGRAPH_NS)
                    && document.elements()[parent].name().local_name() == "equation"
            })
        {
            continue;
        }
        ensure_capacity(controls.len(), limits)?;
        controls
            .try_reserve(1)
            .map_err(|_| ActiveContentError::AllocationFailed)?;
        controls.push(scan_active_element(
            document,
            document_part,
            ordinal,
            element,
            relationships,
            parts,
            limits,
            referenced_kinds,
        )?);
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn scan_active_element(
    document: &PreservingXmlDocument,
    document_part: &str,
    ordinal: usize,
    element: &crate::XmlElementToken,
    relationships: &BTreeMap<&str, &crate::Relationship>,
    parts: &BTreeMap<&str, &crate::PartRecord>,
    limits: ActiveContentLimits,
    referenced_kinds: &mut BTreeMap<String, ActiveContentResourceKind>,
) -> Result<ActiveContentControl, ActiveContentError> {
    let local = element.name().local_name();
    let mut control = ActiveContentControl {
        document_part: document_part.to_owned(),
        element_ordinal: ordinal,
        kind: control_kind(local),
        disposition: ActiveContentDisposition::PreserveBlocked,
        relationship_id: None,
        resource_path: None,
        external: false,
        command_present: false,
        element_sha256: String::new(),
    };
    match local {
        "ole" => scan_ole_control(
            element,
            relationships,
            parts,
            limits,
            referenced_kinds,
            &mut control,
        )?,
        "video" => scan_video_control(
            element,
            relationships,
            parts,
            limits,
            referenced_kinds,
            &mut control,
        )?,
        "btn" | "comboBox" | "listBox" | "edit" => {
            control.command_present = optional_attribute_allow_empty(element, "command", limits)?
                .is_some_and(|value| !value.is_empty());
            if control.command_present {
                control.disposition = ActiveContentDisposition::Quarantine;
            }
        }
        "script" => control.disposition = ActiveContentDisposition::Quarantine,
        _ => unreachable!("active element was filtered above"),
    }
    let outer = element
        .outer_span()
        .ok_or(ActiveContentError::InvalidAttribute)?;
    control.element_sha256 = hex(Sha256::digest(document.source_text(outer)?.as_bytes()).into());
    Ok(control)
}

fn scan_ole_control(
    element: &crate::XmlElementToken,
    relationships: &BTreeMap<&str, &crate::Relationship>,
    parts: &BTreeMap<&str, &crate::PartRecord>,
    limits: ActiveContentLimits,
    referenced_kinds: &mut BTreeMap<String, ActiveContentResourceKind>,
    control: &mut ActiveContentControl,
) -> Result<(), ActiveContentError> {
    let relationship_id = required_attribute(element, "binaryItemIDRef", limits)?;
    let relationship = resolve_resource(relationship_id, relationships, parts)?;
    bind_resource_kind(
        relationship.target.collision_key(),
        ActiveContentResourceKind::OpaqueOle,
        referenced_kinds,
    )?;
    let object_type = required_attribute(element, "objectType", limits)?;
    if !matches!(
        object_type,
        "UNKNOWN" | "EMBEDDED" | "LINK" | "STATIC" | "EQUATION"
    ) {
        return Err(ActiveContentError::InvalidAttribute);
    }
    let has_moniker = optional_attribute(element, "hasMoniker", limits)?
        .map(parse_bool)
        .transpose()?
        .unwrap_or(false);
    control.external = object_type == "LINK" || has_moniker;
    if control.external {
        control.disposition = ActiveContentDisposition::Quarantine;
    }
    control.relationship_id = Some(relationship_id.to_owned());
    control.resource_path = Some(relationship.target.as_str().to_owned());
    Ok(())
}

fn scan_video_control(
    element: &crate::XmlElementToken,
    relationships: &BTreeMap<&str, &crate::Relationship>,
    parts: &BTreeMap<&str, &crate::PartRecord>,
    limits: ActiveContentLimits,
    referenced_kinds: &mut BTreeMap<String, ActiveContentResourceKind>,
    control: &mut ActiveContentControl,
) -> Result<(), ActiveContentError> {
    match required_attribute(element, "videotype", limits)? {
        "Local" | "0" => {
            let relationship_id = required_attribute(element, "fileIDRef", limits)?;
            let relationship = resolve_resource(relationship_id, relationships, parts)?;
            bind_resource_kind(
                relationship.target.collision_key(),
                ActiveContentResourceKind::Video,
                referenced_kinds,
            )?;
            control.relationship_id = Some(relationship_id.to_owned());
            control.resource_path = Some(relationship.target.as_str().to_owned());
        }
        "Web" | "1" => {
            let tag = required_attribute(element, "tag", limits)?;
            if tag.trim().is_empty() {
                return Err(ActiveContentError::InvalidAttribute);
            }
            control.external = true;
            control.disposition = ActiveContentDisposition::Quarantine;
        }
        _ => return Err(ActiveContentError::InvalidAttribute),
    }
    if let Some(poster_id) = optional_attribute(element, "imageIDRef", limits)? {
        let _ = resolve_resource(poster_id, relationships, parts)?;
    }
    Ok(())
}

fn control_kind(local: &str) -> ActiveContentControlKind {
    match local {
        "ole" => ActiveContentControlKind::Ole,
        "video" => ActiveContentControlKind::Video,
        "btn" => ActiveContentControlKind::FormButton,
        "comboBox" => ActiveContentControlKind::FormComboBox,
        "listBox" => ActiveContentControlKind::FormListBox,
        "edit" => ActiveContentControlKind::FormEdit,
        "script" => ActiveContentControlKind::ScriptMacro,
        _ => unreachable!("caller admits exact reviewed names"),
    }
}

fn required_attribute<'a>(
    element: &'a crate::XmlElementToken,
    name: &str,
    limits: ActiveContentLimits,
) -> Result<&'a str, ActiveContentError> {
    optional_attribute(element, name, limits)?.ok_or(ActiveContentError::InvalidAttribute)
}

fn optional_attribute<'a>(
    element: &'a crate::XmlElementToken,
    name: &str,
    limits: ActiveContentLimits,
) -> Result<Option<&'a str>, ActiveContentError> {
    optional_attribute_inner(element, name, limits, false)
}

fn optional_attribute_allow_empty<'a>(
    element: &'a crate::XmlElementToken,
    name: &str,
    limits: ActiveContentLimits,
) -> Result<Option<&'a str>, ActiveContentError> {
    optional_attribute_inner(element, name, limits, true)
}

fn optional_attribute_inner<'a>(
    element: &'a crate::XmlElementToken,
    name: &str,
    limits: ActiveContentLimits,
    allow_empty: bool,
) -> Result<Option<&'a str>, ActiveContentError> {
    let mut found = None;
    for attribute in element.attributes() {
        if attribute.name().local_name() != name {
            continue;
        }
        if attribute.name().namespace().is_some() || found.is_some() {
            return Err(ActiveContentError::InvalidAttribute);
        }
        let value = attribute.semantic_value();
        if (!allow_empty && value.is_empty()) || value.len() > limits.0.max_identifier_bytes {
            return Err(ActiveContentError::InvalidAttribute);
        }
        found = Some(value);
    }
    Ok(found)
}

fn parse_bool(value: &str) -> Result<bool, ActiveContentError> {
    match value {
        "0" | "false" => Ok(false),
        "1" | "true" => Ok(true),
        _ => Err(ActiveContentError::InvalidAttribute),
    }
}

fn resolve_resource<'a>(
    id: &str,
    relationships: &BTreeMap<&str, &'a crate::Relationship>,
    parts: &BTreeMap<&str, &crate::PartRecord>,
) -> Result<&'a crate::Relationship, ActiveContentError> {
    let relationship = relationships
        .get(id)
        .copied()
        .ok_or(ActiveContentError::DanglingReference)?;
    let part = parts
        .get(relationship.target.collision_key())
        .copied()
        .ok_or(ActiveContentError::DanglingReference)?;
    if is_xml_part(part.path.as_str(), part.media_type.as_str()) {
        return Err(ActiveContentError::DanglingReference);
    }
    Ok(relationship)
}

fn bind_resource_kind(
    target_key: &str,
    kind: ActiveContentResourceKind,
    referenced: &mut BTreeMap<String, ActiveContentResourceKind>,
) -> Result<(), ActiveContentError> {
    if let Some(previous) = referenced.insert(target_key.to_owned(), kind)
        && previous != kind
    {
        return Err(ActiveContentError::ConflictingResourceRole);
    }
    Ok(())
}

fn classify_resource(
    path: &str,
    media_type: &str,
    bytes: &[u8],
    referenced_kind: Option<ActiveContentResourceKind>,
) -> Result<ResourceClassification, ActiveContentError> {
    if executable_signature(bytes) || executable_path(path) || executable_media(media_type) {
        return Ok(ResourceClassification {
            kind: ActiveContentResourceKind::Executable,
            disposition: ActiveContentDisposition::Quarantine,
            signature: if executable_signature(bytes) {
                ActiveContentSignature::Verified
            } else {
                ActiveContentSignature::Unverified
            },
        });
    }
    if script_path(path) || script_media(media_type) {
        return Ok(ResourceClassification {
            kind: ActiveContentResourceKind::ScriptMacro,
            disposition: ActiveContentDisposition::Quarantine,
            signature: ActiveContentSignature::NotApplicable,
        });
    }
    if let Some(kind) = referenced_kind {
        return match kind {
            ActiveContentResourceKind::OpaqueOle => {
                if media_type.starts_with("image/")
                    || media_type.starts_with("audio/")
                    || media_type.starts_with("video/")
                    || media_type.starts_with("text/")
                {
                    return Err(ActiveContentError::ConflictingResourceRole);
                }
                Ok(ResourceClassification {
                    kind,
                    disposition: ActiveContentDisposition::PreserveBlocked,
                    signature: if compound_file_signature(bytes) {
                        ActiveContentSignature::Verified
                    } else {
                        ActiveContentSignature::Unverified
                    },
                })
            }
            ActiveContentResourceKind::Video => {
                if !media_type.starts_with("video/")
                    && media_type != "application/octet-stream"
                    && media_type != "application/ogg"
                {
                    return Err(ActiveContentError::ConflictingResourceRole);
                }
                multimedia_classification(kind, media_type, bytes)
            }
            _ => Err(ActiveContentError::ConflictingResourceRole),
        };
    }
    if media_type.starts_with("audio/") {
        return multimedia_classification(ActiveContentResourceKind::Audio, media_type, bytes);
    }
    if media_type.starts_with("video/") {
        return multimedia_classification(ActiveContentResourceKind::Video, media_type, bytes);
    }
    Ok(ResourceClassification {
        kind: ActiveContentResourceKind::OpaqueBinary,
        disposition: ActiveContentDisposition::ReviewRequired,
        signature: if compound_file_signature(bytes) {
            ActiveContentSignature::Verified
        } else {
            ActiveContentSignature::Unverified
        },
    })
}

fn multimedia_classification(
    kind: ActiveContentResourceKind,
    media_type: &str,
    bytes: &[u8],
) -> Result<ResourceClassification, ActiveContentError> {
    let signature = match known_multimedia_signature(media_type, bytes) {
        Some(true) => ActiveContentSignature::Verified,
        Some(false) => return Err(ActiveContentError::SignatureMismatch),
        None => ActiveContentSignature::Unverified,
    };
    Ok(ResourceClassification {
        kind,
        disposition: ActiveContentDisposition::PreservePassive,
        signature,
    })
}

fn known_multimedia_signature(media_type: &str, bytes: &[u8]) -> Option<bool> {
    match media_type {
        "video/mp4" | "audio/mp4" => Some(bytes.len() >= 12 && &bytes[4..8] == b"ftyp"),
        "audio/mpeg" => Some(
            bytes.starts_with(b"ID3")
                || (bytes.len() >= 2 && bytes[0] == 0xff && bytes[1] & 0xe0 == 0xe0),
        ),
        "audio/wav" | "audio/x-wav" => Some(riff_kind(bytes, *b"WAVE")),
        "video/x-msvideo" | "video/avi" => Some(riff_kind(bytes, *b"AVI ")),
        "application/ogg" | "audio/ogg" | "video/ogg" => Some(bytes.starts_with(b"OggS")),
        "audio/webm" | "video/webm" => Some(bytes.starts_with(&[0x1a, 0x45, 0xdf, 0xa3])),
        _ => None,
    }
}

fn riff_kind(bytes: &[u8], kind: [u8; 4]) -> bool {
    bytes.len() >= 12 && bytes.starts_with(b"RIFF") && bytes[8..12] == kind
}

fn compound_file_signature(bytes: &[u8]) -> bool {
    bytes.starts_with(&[0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1])
}

fn executable_signature(bytes: &[u8]) -> bool {
    bytes.starts_with(b"MZ")
        || bytes.starts_with(b"\x7fELF")
        || bytes.starts_with(&[0xcf, 0xfa, 0xed, 0xfe])
        || bytes.starts_with(&[0xfe, 0xed, 0xfa, 0xcf])
}

fn extension(path: &str) -> &str {
    path.rsplit_once('.').map_or("", |(_, value)| value)
}

fn executable_path(path: &str) -> bool {
    matches!(
        extension(path).to_ascii_lowercase().as_str(),
        "exe" | "dll" | "com" | "scr" | "msi" | "cpl" | "elf" | "dylib"
    )
}

fn script_path(path: &str) -> bool {
    let lower = path.to_ascii_lowercase();
    lower.starts_with("scripts/")
        || lower.starts_with("macros/")
        || matches!(
            extension(&lower),
            "js" | "vbs" | "ps1" | "bat" | "cmd" | "sh" | "py" | "pl"
        )
}

fn executable_media(media_type: &str) -> bool {
    matches!(
        media_type,
        "application/x-msdownload"
            | "application/vnd.microsoft.portable-executable"
            | "application/x-executable"
            | "application/x-dosexec"
    )
}

fn script_media(media_type: &str) -> bool {
    matches!(
        media_type,
        "application/javascript"
            | "text/javascript"
            | "application/ecmascript"
            | "text/ecmascript"
            | "application/x-sh"
            | "text/x-python"
            | "application/x-powershell"
    )
}

fn is_xml_part(path: &str, media_type: &str) -> bool {
    matches!(extension(path).to_ascii_lowercase().as_str(), "xml" | "hpf")
        || media_type == "application/xml"
        || media_type == "text/xml"
        || media_type.ends_with("+xml")
}

fn is_inventory_resource(path: &str, media_type: &str) -> bool {
    if is_xml_part(path, media_type)
        || matches!(path, "mimetype" | "META-INF/container.xml")
        || media_type.starts_with("image/")
        || media_type.starts_with("font/")
        || media_type == "text/plain"
    {
        return false;
    }
    media_type.starts_with("audio/")
        || media_type.starts_with("video/")
        || media_type == "application/octet-stream"
        || executable_media(media_type)
        || script_media(media_type)
        || executable_path(path)
        || script_path(path)
}

fn ensure_capacity(current: usize, limits: ActiveContentLimits) -> Result<(), ActiveContentError> {
    if current >= limits.0.max_inventory_items {
        Err(ActiveContentError::InventoryLimit)
    } else {
        Ok(())
    }
}

fn ensure_unique_resources(resources: &[ActiveContentResource]) -> Result<(), ActiveContentError> {
    let mut paths = BTreeSet::new();
    let mut relationships = BTreeSet::new();
    for resource in resources {
        if !paths.insert(resource.path.as_str()) {
            return Err(ActiveContentError::SourceGraphDrift);
        }
        for id in &resource.relationship_ids {
            if !relationships.insert(id) {
                return Err(ActiveContentError::SourceGraphDrift);
            }
        }
    }
    Ok(())
}

fn counts(
    resources: &[ActiveContentResource],
    controls: &[ActiveContentControl],
) -> ActiveContentCounts {
    let dispositions = resources
        .iter()
        .map(|item| item.disposition)
        .chain(controls.iter().map(|item| item.disposition));
    let mut counts = ActiveContentCounts {
        resources: resources.len(),
        controls: controls.len(),
        ..ActiveContentCounts::default()
    };
    for disposition in dispositions {
        match disposition {
            ActiveContentDisposition::PreservePassive => {}
            ActiveContentDisposition::PreserveBlocked => counts.blocked += 1,
            ActiveContentDisposition::Quarantine => counts.quarantined += 1,
            ActiveContentDisposition::ReviewRequired => counts.review_required += 1,
        }
    }
    counts
}

#[derive(Serialize)]
struct ActiveState<'a> {
    schema_version: &'static str,
    profile_id: &'static str,
    resources: &'a [ActiveContentResource],
    controls: Vec<ActiveControlState<'a>>,
}

#[derive(Eq, Ord, PartialEq, PartialOrd, Serialize)]
struct ActiveControlState<'a> {
    document_part: &'a str,
    kind: ActiveContentControlKind,
    disposition: ActiveContentDisposition,
    relationship_id: Option<&'a str>,
    resource_path: Option<&'a str>,
    external: bool,
    command_present: bool,
    element_sha256: &'a str,
}

fn control_states(controls: &[ActiveContentControl]) -> Vec<ActiveControlState<'_>> {
    let mut states = controls
        .iter()
        .map(|control| ActiveControlState {
            document_part: &control.document_part,
            kind: control.kind,
            disposition: control.disposition,
            relationship_id: control.relationship_id.as_deref(),
            resource_path: control.resource_path.as_deref(),
            external: control.external,
            command_present: control.command_present,
            element_sha256: &control.element_sha256,
        })
        .collect::<Vec<_>>();
    states.sort_unstable();
    states
}

fn active_state_sha256(
    resources: &[ActiveContentResource],
    controls: &[ActiveContentControl],
    limits: ActiveContentLimits,
) -> Result<String, ActiveContentError> {
    let mut writer = InventoryJsonWriter::new(InventoryJsonSink::Digest(Sha256::new()), limits);
    serde_json::to_writer(&mut writer, &ActiveState {
        schema_version: ACTIVE_CONTENT_SCHEMA_VERSION,
        profile_id: ACTIVE_CONTENT_PROFILE_ID,
        resources,
        controls: control_states(controls),
    })
    .map_err(|_| ActiveContentError::OutputLimit)?;
    match writer.sink {
        InventoryJsonSink::Digest(hash) => Ok(hex(hash.finalize().into())),
        _ => Err(ActiveContentError::OutputLimit),
    }
}

// Count and Digest retain no serialized JSON. Only an explicit canonical_json
// request owns an output buffer, and its limit is checked before each append.
enum InventoryJsonSink {
    Count,
    Bytes(Vec<u8>),
    Digest(Sha256),
}
struct InventoryJsonWriter {
    sink: InventoryJsonSink,
    written: usize,
    maximum: usize,
}
impl InventoryJsonWriter {
    fn new(sink: InventoryJsonSink, limits: ActiveContentLimits) -> Self {
        Self { sink, written: 0, maximum: limits.0.max_json_bytes }
    }
}
impl io::Write for InventoryJsonWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let next = self.written.checked_add(bytes.len())
            .filter(|size| *size <= self.maximum)
            .ok_or_else(|| io::Error::other("ACTIVE_CONTENT_JSON_LIMIT"))?;
        match &mut self.sink {
            InventoryJsonSink::Count => {}
            InventoryJsonSink::Digest(hash) => hash.update(bytes),
            InventoryJsonSink::Bytes(output) => {
                output.try_reserve(bytes.len())
                    .map_err(|_| io::Error::other("ACTIVE_CONTENT_JSON_LIMIT"))?;
                output.extend_from_slice(bytes);
            }
        }
        self.written = next;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> { Ok(()) }
}

fn graph_sha256(graph: &PackageGraph) -> String {
    let mut digest = Sha256::new();
    hash_text(&mut digest, graph.package_document.as_str());
    for part in &graph.parts {
        hash_text(&mut digest, part.path.as_str());
        hash_text(&mut digest, part.media_type.as_str());
        digest.update([match part.role {
            crate::PartRole::Infrastructure => 0,
            crate::PartRole::ManifestListed => 1,
            crate::PartRole::SpineDocument => 2,
        }]);
        digest.update(part.expanded_size.to_be_bytes());
        digest.update(part.raw_sha256);
    }
    for relationship in &graph.relationships {
        hash_text(&mut digest, &relationship.id);
        hash_text(&mut digest, relationship.source.as_str());
        hash_text(&mut digest, relationship.target.as_str());
        hash_text(&mut digest, relationship.media_type.as_str());
        digest.update([
            match relationship.kind {
                crate::RelationshipKind::ManifestItem => 0,
                crate::RelationshipKind::SpineItem => 1,
            },
            u8::from(relationship.linear),
        ]);
    }
    for path in &graph.spine {
        hash_text(&mut digest, path.as_str());
    }
    hex(digest.finalize().into())
}

fn hash_text(digest: &mut Sha256, value: &str) {
    digest.update((value.len() as u64).to_be_bytes());
    digest.update(value.as_bytes());
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
