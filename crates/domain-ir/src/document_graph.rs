use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::io;

use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub const DOCUMENT_GRAPH_SCHEMA_VERSION: &str = "hwpx-agent.document-graph/v2";

const MAX_COUNT_LIMIT_CEILING: usize = 1_000_000;
const MAX_DEPTH_CEILING: usize = 256;
const MAX_STRING_BYTES_CEILING: usize = 4 * 1024 * 1024;
const MAX_TOTAL_STRING_BYTES_CEILING: usize = 64 * 1024 * 1024;
const MAX_SERIALIZED_BYTES_CEILING: usize = 256 * 1024 * 1024;

macro_rules! private_debug {
    ($($type:ty => $name:literal),+ $(,)?) => {
        $(
            impl fmt::Debug for $type {
                fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                    formatter.write_str($name)
                }
            }
        )+
    };
}

#[derive(Clone, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(transparent)]
pub struct DocumentId(String);

impl DocumentId {
    /// Parses a backend-neutral document identifier.
    ///
    /// # Errors
    ///
    /// Returns a stable identifier error for an empty value or a value containing control bytes.
    pub fn parse(value: impl Into<String>) -> Result<Self, DocumentGraphError> {
        parse_identifier(value.into()).map(Self)
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl<'de> Deserialize<'de> for DocumentId {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let value = String::deserialize(deserializer)?;
        parse_identifier(value)
            .map(Self)
            .map_err(serde::de::Error::custom)
    }
}

#[derive(Clone, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(transparent)]
pub struct LogicalId(String);

impl LogicalId {
    /// Parses a logical identifier that remains independent from HWPX numeric identifiers.
    ///
    /// # Errors
    ///
    /// Returns a stable identifier error for an empty value or a value containing control bytes.
    pub fn parse(value: impl Into<String>) -> Result<Self, DocumentGraphError> {
        parse_identifier(value.into()).map(Self)
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl<'de> Deserialize<'de> for LogicalId {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let value = String::deserialize(deserializer)?;
        parse_identifier(value)
            .map(Self)
            .map_err(serde::de::Error::custom)
    }
}

fn parse_identifier(value: String) -> Result<String, DocumentGraphError> {
    if value.is_empty() || value.chars().any(char::is_control) {
        return Err(DocumentGraphError::InvalidIdentifier);
    }
    Ok(value)
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "value", rename_all = "snake_case")]
pub enum PropertyValue {
    Text(String),
    Integer(i64),
    Boolean(bool),
    Decimal(String),
    Id(LogicalId),
    List(Vec<Self>),
    Object(BTreeMap<String, Self>),
}

impl fmt::Debug for PropertyValue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Text(_) => "PropertyValue::Text(<redacted>)",
            Self::Integer(_) => "PropertyValue::Integer(<redacted>)",
            Self::Boolean(_) => "PropertyValue::Boolean(<redacted>)",
            Self::Decimal(_) => "PropertyValue::Decimal(<redacted>)",
            Self::Id(_) => "PropertyValue::Id(<redacted>)",
            Self::List(_) => "PropertyValue::List(<redacted>)",
            Self::Object(_) => "PropertyValue::Object(<redacted>)",
        })
    }
}

#[derive(Clone, Default, Eq, PartialEq, Serialize, Deserialize)]
#[serde(transparent)]
pub struct Properties(BTreeMap<String, PropertyValue>);

impl Properties {
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    pub fn insert(&mut self, key: impl Into<String>, value: PropertyValue) {
        let _ = self.0.insert(key.into(), value);
    }

    pub fn iter(&self) -> impl Iterator<Item = (&str, &PropertyValue)> {
        self.0.iter().map(|(key, value)| (key.as_str(), value))
    }

    #[must_use]
    pub fn len(&self) -> usize {
        self.0.len()
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }
}

#[derive(Clone, Default, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SecurityState {
    pub protected: bool,
    pub encrypted: bool,
    pub signed: bool,
    pub properties: Properties,
}

#[derive(Clone, Default, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AccessibilityState {
    pub language: Option<String>,
    pub title_present: bool,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ResourceKind {
    Image,
    Ole,
    Media,
    Font,
    ChartData,
    Xml,
    Other,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArtifactRef {
    pub sha256: [u8; 32],
    pub byte_length: u64,
    pub media_type: String,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Resource {
    pub resource_id: LogicalId,
    pub kind: ResourceKind,
    #[serde(rename = "artifact_ref")]
    pub artifact: Option<ArtifactRef>,
    pub metadata: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Style {
    pub style_id: LogicalId,
    pub based_on: Option<LogicalId>,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceAnchorHandle {
    pub opaque_handle: LogicalId,
    pub fingerprint_sha256: [u8; 32],
}

#[derive(Clone, Default, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Provenance {
    #[default]
    Imported,
    User,
    Automation,
    Generated,
}

#[derive(Clone, Default, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OpaquePreservation {
    #[default]
    None,
    PreserveUnknown,
    PreserveExact,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NodeCommon {
    pub node_id: LogicalId,
    pub source_anchor: Option<SourceAnchorHandle>,
    pub style_refs: Vec<LogicalId>,
    pub resource_refs: Vec<LogicalId>,
    pub layout_hints: Properties,
    pub semantics: Properties,
    pub provenance: Provenance,
    pub preserve: OpaquePreservation,
}

impl NodeCommon {
    #[must_use]
    pub fn new(node_id: LogicalId) -> Self {
        Self {
            node_id,
            source_anchor: None,
            style_refs: Vec::new(),
            resource_refs: Vec::new(),
            layout_hints: Properties::new(),
            semantics: Properties::new(),
            provenance: Provenance::Imported,
            preserve: OpaquePreservation::None,
        }
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "inline_type", rename_all = "snake_case")]
pub enum Inline {
    Text {
        text: String,
    },
    InlineEquation {
        source: String,
    },
    Tab,
    LineBreak,
    FieldRef {
        reference_id: LogicalId,
    },
    BookmarkAnchor {
        reference_id: LogicalId,
    },
    ChangeSpan {
        review_id: LogicalId,
        children: Vec<Self>,
    },
    ControlRef {
        node_id: LogicalId,
    },
}

impl fmt::Debug for Inline {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Text { .. } => "Inline::Text(<redacted>)",
            Self::InlineEquation { .. } => "Inline::InlineEquation(<redacted>)",
            Self::Tab => "Inline::Tab",
            Self::LineBreak => "Inline::LineBreak",
            Self::FieldRef { .. } => "Inline::FieldRef(<redacted>)",
            Self::BookmarkAnchor { .. } => "Inline::BookmarkAnchor(<redacted>)",
            Self::ChangeSpan { .. } => "Inline::ChangeSpan(<redacted>)",
            Self::ControlRef { .. } => "Inline::ControlRef(<redacted>)",
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ParagraphNode {
    pub common: NodeCommon,
    pub inlines: Vec<Inline>,
    pub paragraph_properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TableCell {
    pub cell_id: LogicalId,
    pub row: u32,
    pub column: u32,
    pub row_span: u32,
    pub column_span: u32,
    pub body: Flow,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TableNode {
    pub common: NodeCommon,
    pub rows: u32,
    pub columns: u32,
    pub cells: Vec<TableCell>,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "source", rename_all = "snake_case")]
pub enum EquationSource {
    MathMl(String),
    Formula(String),
    NativeOpaque(LogicalId),
}

impl fmt::Debug for EquationSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::MathMl(_) => "EquationSource::MathMl(<redacted>)",
            Self::Formula(_) => "EquationSource::Formula(<redacted>)",
            Self::NativeOpaque(_) => "EquationSource::NativeOpaque(<redacted>)",
        })
    }
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EquationNode {
    pub common: NodeCommon,
    pub source: EquationSource,
    pub display: bool,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DrawingNode {
    pub common: NodeCommon,
    pub resource_id: Option<LogicalId>,
    pub children: Flow,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ChartNode {
    pub common: NodeCommon,
    pub data_resource_id: LogicalId,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FieldNode {
    pub common: NodeCommon,
    pub reference_id: LogicalId,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FormControlNode {
    pub common: NodeCommon,
    pub control_kind: String,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BreakKind {
    Page,
    Column,
    Section,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BreakNode {
    pub common: NodeCommon,
    pub break_kind: BreakKind,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EmbeddedObjectType {
    Ole,
    Media,
    Xml,
    Other,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EmbeddedObjectNode {
    pub common: NodeCommon,
    pub object_type: EmbeddedObjectType,
    pub resource_id: LogicalId,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(tag = "node_type", rename_all = "snake_case")]
pub enum Node {
    Paragraph(ParagraphNode),
    Table(TableNode),
    Equation(EquationNode),
    Drawing(DrawingNode),
    Chart(ChartNode),
    Field(FieldNode),
    FormControl(FormControlNode),
    Break(BreakNode),
    EmbeddedObject(EmbeddedObjectNode),
}

impl Node {
    #[must_use]
    pub fn common(&self) -> &NodeCommon {
        match self {
            Self::Paragraph(node) => &node.common,
            Self::Table(node) => &node.common,
            Self::Equation(node) => &node.common,
            Self::Drawing(node) => &node.common,
            Self::Chart(node) => &node.common,
            Self::Field(node) => &node.common,
            Self::FormControl(node) => &node.common,
            Self::Break(node) => &node.common,
            Self::EmbeddedObject(node) => &node.common,
        }
    }
}

impl fmt::Debug for Node {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Paragraph(_) => "Node::Paragraph(<redacted>)",
            Self::Table(_) => "Node::Table(<redacted>)",
            Self::Equation(_) => "Node::Equation(<redacted>)",
            Self::Drawing(_) => "Node::Drawing(<redacted>)",
            Self::Chart(_) => "Node::Chart(<redacted>)",
            Self::Field(_) => "Node::Field(<redacted>)",
            Self::FormControl(_) => "Node::FormControl(<redacted>)",
            Self::Break(_) => "Node::Break(<redacted>)",
            Self::EmbeddedObject(_) => "Node::EmbeddedObject(<redacted>)",
        })
    }
}

#[derive(Clone, Default, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Flow {
    pub children: Vec<Node>,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Section {
    pub section_id: LogicalId,
    pub properties: Properties,
    pub master_pages: Vec<LogicalId>,
    pub headers_footers: Vec<LogicalId>,
    pub body: Flow,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Note {
    pub note_id: LogicalId,
    pub body: Flow,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Reference {
    pub reference_id: LogicalId,
    pub target_node_id: Option<LogicalId>,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReviewEntry {
    pub review_id: LogicalId,
    pub target_node_id: LogicalId,
    pub properties: Properties,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OpaqueExtension {
    pub handle: LogicalId,
    pub sha256: [u8; 32],
    pub byte_length: u64,
    pub preservation: OpaquePreservation,
}

#[derive(Clone, Eq, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DocumentGraphDraft {
    pub schema_version: String,
    pub document_id: DocumentId,
    pub source_profile: Option<LogicalId>,
    pub metadata: Properties,
    pub settings: Properties,
    pub security_state: SecurityState,
    pub accessibility: AccessibilityState,
    #[serde(rename = "resource_catalog")]
    pub resources: Vec<Resource>,
    #[serde(rename = "style_catalog")]
    pub styles: Vec<Style>,
    pub sections: Vec<Section>,
    pub notes: Vec<Note>,
    pub references: Vec<Reference>,
    pub review: Vec<ReviewEntry>,
    pub opaque_preservation_bag: Vec<OpaqueExtension>,
}

impl DocumentGraphDraft {
    #[must_use]
    pub fn new(document_id: DocumentId, sections: Vec<Section>) -> Self {
        Self {
            schema_version: DOCUMENT_GRAPH_SCHEMA_VERSION.to_owned(),
            document_id,
            source_profile: None,
            metadata: Properties::new(),
            settings: Properties::new(),
            security_state: SecurityState::default(),
            accessibility: AccessibilityState::default(),
            resources: Vec::new(),
            styles: Vec::new(),
            sections,
            notes: Vec::new(),
            references: Vec::new(),
            review: Vec::new(),
            opaque_preservation_bag: Vec::new(),
        }
    }
}

#[derive(Clone, Serialize)]
#[serde(transparent)]
pub struct DocumentGraph(
    DocumentGraphDraft,
    #[serde(skip)] std::sync::OnceLock<[u8; 32]>,
);

// Memoized derived bytes are not document state. Warm/cold graphs must remain
// equal, and transparent serialization must remain exactly the original draft.
impl PartialEq for DocumentGraph {
    fn eq(&self, other: &Self) -> bool {
        self.0 == other.0
    }
}

impl Eq for DocumentGraph {}

impl DocumentGraph {
    /// Validates and canonicalizes an untrusted graph draft.
    ///
    /// # Errors
    ///
    /// Fails closed on version, limit, identity, reference, shape or privacy-contract violations.
    pub fn from_draft(
        mut draft: DocumentGraphDraft,
        limits: DocumentGraphLimits,
    ) -> Result<Self, DocumentGraphError> {
        limits.validate()?;
        if draft.schema_version != DOCUMENT_GRAPH_SCHEMA_VERSION {
            return Err(DocumentGraphError::UnsupportedVersion);
        }
        preflight_top_level_counts(&draft, limits)?;
        validate_serialized_size(&draft, limits.max_serialized_bytes)?;
        canonicalize_catalogs(&mut draft);
        Validator::new(limits).validate(&draft)?;
        Ok(Self(draft, std::sync::OnceLock::new()))
    }

    /// Deserializes an untrusted JSON graph and runs the same full validation as `from_draft`.
    ///
    /// # Errors
    ///
    /// Returns a stable error without embedding source JSON or document values.
    pub fn from_json(
        bytes: &[u8],
        limits: DocumentGraphLimits,
    ) -> Result<Self, DocumentGraphError> {
        limits.validate()?;
        if bytes.len() > limits.max_serialized_bytes {
            return Err(DocumentGraphError::LimitExceeded);
        }
        let draft = serde_json::from_slice(bytes).map_err(|_| DocumentGraphError::InvalidJson)?;
        Self::from_draft(draft, limits)
    }

    /// Emits stable compact JSON from an already validated immutable graph.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization error if the serializer cannot complete.
    pub fn canonical_json(&self) -> Result<Vec<u8>, DocumentGraphError> {
        let mut writer = Vec::with_capacity(128);
        // Share the serializer's writer type with digest and size checks. This avoids
        // separate large graph serializer monomorphizations for each output sink.
        serde_json::to_writer(&mut writer as &mut dyn io::Write, &self.0)
            .map_err(|_| DocumentGraphError::SerializationFailed)?;
        Ok(writer)
    }

    /// Returns the digest of the canonical serialized graph.
    ///
    /// # Errors
    ///
    /// Propagates a stable serialization error.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], DocumentGraphError> {
        // This graph is immutable after full from_draft validation. Cache ONLY
        // its 32-byte serialization digest, never source/ACL/head/policy/AEAD
        // verification. A newly admitted draft starts with a fresh empty cell.
        if let Some(digest) = self.1.get() {
            return Ok(*digest);
        }
        // Keep the exact canonical JSON byte stream without retaining its full allocation.
        let mut writer = io::BufWriter::with_capacity(32 * 1024, GraphDigestWriter(Sha256::new()));
        serde_json::to_writer(&mut writer as &mut dyn io::Write, &self.0)
            .map_err(|_| DocumentGraphError::SerializationFailed)?;
        let digest = writer
            .into_inner()
            .map_err(|_| DocumentGraphError::SerializationFailed)?;
        let computed: [u8; 32] = digest.0.finalize().into();
        // Concurrent first readers may compute the same immutable byte stream;
        // no fallible serializer is run inside a reentrant cache initializer.
        let _ = self.1.set(computed);
        Ok(computed)
    }

    #[must_use]
    pub fn document_id(&self) -> &DocumentId {
        &self.0.document_id
    }

    #[must_use]
    pub fn sections(&self) -> &[Section] {
        &self.0.sections
    }

    #[must_use]
    pub fn resources(&self) -> &[Resource] {
        &self.0.resources
    }

    #[must_use]
    pub fn styles(&self) -> &[Style] {
        &self.0.styles
    }

    /// Borrows validated notes without copying the document or changing presentation order.
    #[must_use]
    pub fn notes(&self) -> &[Note] {
        &self.0.notes
    }

    /// Read-only metadata; does not bypass full graph admission or authorize mutation.
    #[must_use]
    pub const fn metadata(&self) -> &Properties {
        &self.0.metadata
    }

    /// Borrows the canonical review catalog, not a replacement presentation-order view.
    #[must_use]
    pub fn review_entries(&self) -> &[ReviewEntry] {
        &self.0.review
    }

    #[must_use]
    pub(crate) const fn draft(&self) -> &DocumentGraphDraft {
        &self.0
    }

    #[must_use]
    pub fn into_draft(self) -> DocumentGraphDraft {
        self.0
    }
}

impl fmt::Debug for DocumentGraph {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("DocumentGraph")
            .field("schema_version", &DOCUMENT_GRAPH_SCHEMA_VERSION)
            .field("sections", &self.0.sections.len())
            .field("resources", &self.0.resources.len())
            .field("styles", &self.0.styles.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DocumentGraphLimits {
    pub max_serialized_bytes: usize,
    pub max_sections: usize,
    pub max_nodes: usize,
    pub max_inlines: usize,
    pub max_edges: usize,
    pub max_depth: usize,
    pub max_resources: usize,
    pub max_styles: usize,
    pub max_properties: usize,
    pub max_string_bytes: usize,
    pub max_total_string_bytes: usize,
    pub max_table_cells: usize,
    pub max_notes: usize,
    pub max_references: usize,
    pub max_review_entries: usize,
    pub max_opaque_extensions: usize,
}

impl Default for DocumentGraphLimits {
    fn default() -> Self {
        Self {
            max_serialized_bytes: 32 * 1024 * 1024,
            max_sections: 4_096,
            max_nodes: 250_000,
            max_inlines: 500_000,
            max_edges: 1_000_000,
            max_depth: 128,
            max_resources: 65_536,
            max_styles: 65_536,
            max_properties: 500_000,
            max_string_bytes: MAX_STRING_BYTES_CEILING,
            max_total_string_bytes: MAX_TOTAL_STRING_BYTES_CEILING,
            max_table_cells: 1_000_000,
            max_notes: 100_000,
            max_references: 250_000,
            max_review_entries: 250_000,
            max_opaque_extensions: 250_000,
        }
    }
}

impl DocumentGraphLimits {
    fn validate(self) -> Result<(), DocumentGraphError> {
        let count_limits = [
            self.max_sections,
            self.max_nodes,
            self.max_inlines,
            self.max_edges,
            self.max_resources,
            self.max_styles,
            self.max_properties,
            self.max_table_cells,
            self.max_notes,
            self.max_references,
            self.max_review_entries,
            self.max_opaque_extensions,
        ];
        if self.max_serialized_bytes == 0
            || self.max_serialized_bytes > MAX_SERIALIZED_BYTES_CEILING
            || count_limits
                .iter()
                .any(|value| *value == 0 || *value > MAX_COUNT_LIMIT_CEILING)
            || self.max_depth == 0
            || self.max_depth > MAX_DEPTH_CEILING
            || self.max_string_bytes == 0
            || self.max_string_bytes > MAX_STRING_BYTES_CEILING
            || self.max_total_string_bytes == 0
            || self.max_total_string_bytes > MAX_TOTAL_STRING_BYTES_CEILING
            || self.max_string_bytes > self.max_total_string_bytes
        {
            return Err(DocumentGraphError::InvalidLimit);
        }
        Ok(())
    }
}

fn preflight_top_level_counts(
    draft: &DocumentGraphDraft,
    limits: DocumentGraphLimits,
) -> Result<(), DocumentGraphError> {
    if draft.resources.len() > limits.max_resources
        || draft.styles.len() > limits.max_styles
        || draft.notes.len() > limits.max_notes
        || draft.references.len() > limits.max_references
        || draft.review.len() > limits.max_review_entries
        || draft.opaque_preservation_bag.len() > limits.max_opaque_extensions
        || draft.sections.len() > limits.max_sections
    {
        return Err(DocumentGraphError::LimitExceeded);
    }
    Ok(())
}

struct GraphDigestWriter(Sha256);

impl io::Write for GraphDigestWriter {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        self.0.update(buffer);
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

struct SerializedSizeWriter {
    written: usize,
    limit: usize,
    exceeded: bool,
}

impl io::Write for SerializedSizeWriter {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        let Some(total) = self.written.checked_add(buffer.len()) else {
            self.exceeded = true;
            return Err(io::Error::other(
                "document graph serialized size limit exceeded",
            ));
        };
        if total > self.limit {
            self.exceeded = true;
            return Err(io::Error::other(
                "document graph serialized size limit exceeded",
            ));
        }
        self.written = total;
        Ok(buffer.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

fn validate_serialized_size(
    draft: &DocumentGraphDraft,
    limit: usize,
) -> Result<(), DocumentGraphError> {
    let mut writer = SerializedSizeWriter {
        written: 0,
        limit,
        exceeded: false,
    };
    if serde_json::to_writer(&mut writer as &mut dyn io::Write, draft).is_err() {
        return if writer.exceeded {
            Err(DocumentGraphError::LimitExceeded)
        } else {
            Err(DocumentGraphError::SerializationFailed)
        };
    }
    Ok(())
}

#[derive(Debug, Error, Clone, Copy, Eq, PartialEq)]
pub enum DocumentGraphError {
    #[error("document graph identifier is invalid")]
    InvalidIdentifier,
    #[error("document graph limit configuration is invalid")]
    InvalidLimit,
    #[error("document graph schema version is unsupported")]
    UnsupportedVersion,
    #[error("document graph JSON is invalid")]
    InvalidJson,
    #[error("document graph requires at least one section")]
    MissingSection,
    #[error("document graph limit was exceeded")]
    LimitExceeded,
    #[error("document graph contains a duplicate logical identifier")]
    DuplicateIdentifier,
    #[error("document graph contains a dangling logical reference")]
    DanglingReference,
    #[error("document graph table shape is invalid")]
    InvalidTableShape,
    #[error("document graph property or semantic value is invalid")]
    InvalidValue,
    #[error("document graph serialization failed")]
    SerializationFailed,
}

impl DocumentGraphError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidIdentifier => "document_graph_invalid_identifier",
            Self::InvalidLimit => "document_graph_invalid_limit",
            Self::UnsupportedVersion => "document_graph_unsupported_version",
            Self::InvalidJson => "document_graph_invalid_json",
            Self::MissingSection => "document_graph_missing_section",
            Self::LimitExceeded => "document_graph_limit_exceeded",
            Self::DuplicateIdentifier => "document_graph_duplicate_identifier",
            Self::DanglingReference => "document_graph_dangling_reference",
            Self::InvalidTableShape => "document_graph_invalid_table_shape",
            Self::InvalidValue => "document_graph_invalid_value",
            Self::SerializationFailed => "document_graph_serialization_failed",
        }
    }
}

private_debug!(
    DocumentId => "DocumentId(<redacted>)",
    LogicalId => "LogicalId(<redacted>)",
    Properties => "Properties(<redacted>)",
    SecurityState => "SecurityState(<redacted>)",
    AccessibilityState => "AccessibilityState(<redacted>)",
    ResourceKind => "ResourceKind(<redacted>)",
    ArtifactRef => "ArtifactRef(<redacted>)",
    Resource => "Resource(<redacted>)",
    Style => "Style(<redacted>)",
    SourceAnchorHandle => "SourceAnchorHandle(<redacted>)",
    Provenance => "Provenance(<redacted>)",
    OpaquePreservation => "OpaquePreservation(<redacted>)",
    NodeCommon => "NodeCommon(<redacted>)",
    ParagraphNode => "ParagraphNode(<redacted>)",
    TableCell => "TableCell(<redacted>)",
    TableNode => "TableNode(<redacted>)",
    EquationNode => "EquationNode(<redacted>)",
    DrawingNode => "DrawingNode(<redacted>)",
    ChartNode => "ChartNode(<redacted>)",
    FieldNode => "FieldNode(<redacted>)",
    FormControlNode => "FormControlNode(<redacted>)",
    BreakKind => "BreakKind(<redacted>)",
    BreakNode => "BreakNode(<redacted>)",
    EmbeddedObjectType => "EmbeddedObjectType(<redacted>)",
    EmbeddedObjectNode => "EmbeddedObjectNode(<redacted>)",
    Flow => "Flow(<redacted>)",
    Section => "Section(<redacted>)",
    Note => "Note(<redacted>)",
    Reference => "Reference(<redacted>)",
    ReviewEntry => "ReviewEntry(<redacted>)",
    OpaqueExtension => "OpaqueExtension(<redacted>)",
    DocumentGraphDraft => "DocumentGraphDraft(<redacted>)",
);

fn canonicalize_catalogs(draft: &mut DocumentGraphDraft) {
    draft
        .resources
        .sort_by(|left, right| left.resource_id.cmp(&right.resource_id));
    draft
        .styles
        .sort_by(|left, right| left.style_id.cmp(&right.style_id));
    draft
        .notes
        .sort_by(|left, right| left.note_id.cmp(&right.note_id));
    draft
        .references
        .sort_by(|left, right| left.reference_id.cmp(&right.reference_id));
    draft
        .review
        .sort_by(|left, right| left.review_id.cmp(&right.review_id));
    draft
        .opaque_preservation_bag
        .sort_by(|left, right| left.handle.cmp(&right.handle));
}

#[derive(Clone, Copy)]
enum PendingReferenceKind {
    Node,
    Resource,
    Style,
    Reference,
    Review,
    Opaque,
}

struct Validator {
    limits: DocumentGraphLimits,
    all_ids: BTreeSet<LogicalId>,
    node_ids: BTreeSet<LogicalId>,
    resource_ids: BTreeSet<LogicalId>,
    style_ids: BTreeSet<LogicalId>,
    reference_ids: BTreeSet<LogicalId>,
    review_ids: BTreeSet<LogicalId>,
    opaque_ids: BTreeSet<LogicalId>,
    pending: Vec<(PendingReferenceKind, LogicalId)>,
    node_count: usize,
    inline_count: usize,
    property_count: usize,
    table_cell_count: usize,
    total_string_bytes: usize,
}

impl Validator {
    fn new(limits: DocumentGraphLimits) -> Self {
        Self {
            limits,
            all_ids: BTreeSet::new(),
            node_ids: BTreeSet::new(),
            resource_ids: BTreeSet::new(),
            style_ids: BTreeSet::new(),
            reference_ids: BTreeSet::new(),
            review_ids: BTreeSet::new(),
            opaque_ids: BTreeSet::new(),
            pending: Vec::new(),
            node_count: 0,
            inline_count: 0,
            property_count: 0,
            table_cell_count: 0,
            total_string_bytes: 0,
        }
    }

    fn validate(mut self, draft: &DocumentGraphDraft) -> Result<(), DocumentGraphError> {
        if draft.sections.is_empty() {
            return Err(DocumentGraphError::MissingSection);
        }
        self.check_len(draft.document_id.as_str())?;
        if let Some(profile) = &draft.source_profile {
            self.check_len(profile.as_str())?;
        }
        self.check_properties(&draft.metadata, 1)?;
        self.check_properties(&draft.settings, 1)?;
        self.check_security_accessibility(draft)?;
        self.collect_catalogs(draft)?;
        self.collect_document_content(draft)?;
        self.resolve_pending()?;
        Ok(())
    }

    fn check_security_accessibility(
        &mut self,
        draft: &DocumentGraphDraft,
    ) -> Result<(), DocumentGraphError> {
        self.check_properties(&draft.security_state.properties, 1)?;
        self.check_properties(&draft.accessibility.properties, 1)?;
        if let Some(language) = &draft.accessibility.language {
            self.check_nonempty_text(language)?;
        }
        Ok(())
    }

    fn collect_catalogs(&mut self, draft: &DocumentGraphDraft) -> Result<(), DocumentGraphError> {
        if draft.resources.len() > self.limits.max_resources
            || draft.styles.len() > self.limits.max_styles
            || draft.notes.len() > self.limits.max_notes
            || draft.references.len() > self.limits.max_references
            || draft.review.len() > self.limits.max_review_entries
            || draft.opaque_preservation_bag.len() > self.limits.max_opaque_extensions
            || draft.sections.len() > self.limits.max_sections
        {
            return Err(DocumentGraphError::LimitExceeded);
        }
        for resource in &draft.resources {
            self.insert_global(&resource.resource_id)?;
            let _ = self.resource_ids.insert(resource.resource_id.clone());
            self.check_properties(&resource.metadata, 1)?;
            if let Some(artifact) = &resource.artifact {
                self.check_nonempty_text(&artifact.media_type)?;
            }
        }
        for style in &draft.styles {
            self.insert_global(&style.style_id)?;
            let _ = self.style_ids.insert(style.style_id.clone());
            if let Some(parent) = &style.based_on {
                self.add_pending(PendingReferenceKind::Style, parent)?;
            }
            self.check_properties(&style.properties, 1)?;
        }
        for reference in &draft.references {
            self.insert_global(&reference.reference_id)?;
            let _ = self.reference_ids.insert(reference.reference_id.clone());
            if let Some(target) = &reference.target_node_id {
                self.add_pending(PendingReferenceKind::Node, target)?;
            }
            self.check_properties(&reference.properties, 1)?;
        }
        for review in &draft.review {
            self.insert_global(&review.review_id)?;
            let _ = self.review_ids.insert(review.review_id.clone());
            self.add_pending(PendingReferenceKind::Node, &review.target_node_id)?;
            self.check_properties(&review.properties, 1)?;
        }
        for extension in &draft.opaque_preservation_bag {
            self.insert_global(&extension.handle)?;
            let _ = self.opaque_ids.insert(extension.handle.clone());
            if extension.preservation == OpaquePreservation::None {
                return Err(DocumentGraphError::InvalidValue);
            }
        }
        Ok(())
    }

    fn collect_document_content(
        &mut self,
        draft: &DocumentGraphDraft,
    ) -> Result<(), DocumentGraphError> {
        for section in &draft.sections {
            self.insert_global(&section.section_id)?;
            self.check_properties(&section.properties, 1)?;
            for reference in section
                .master_pages
                .iter()
                .chain(section.headers_footers.iter())
            {
                self.add_pending(PendingReferenceKind::Node, reference)?;
            }
            self.check_flow(&section.body, 1)?;
        }
        for note in &draft.notes {
            self.insert_global(&note.note_id)?;
            self.check_properties(&note.properties, 1)?;
            self.check_flow(&note.body, 1)?;
        }
        Ok(())
    }

    fn check_flow(&mut self, flow: &Flow, depth: usize) -> Result<(), DocumentGraphError> {
        if depth > self.limits.max_depth {
            return Err(DocumentGraphError::LimitExceeded);
        }
        for node in &flow.children {
            self.node_count = self
                .node_count
                .checked_add(1)
                .ok_or(DocumentGraphError::LimitExceeded)?;
            if self.node_count > self.limits.max_nodes {
                return Err(DocumentGraphError::LimitExceeded);
            }
            let common = node.common();
            self.insert_global(&common.node_id)?;
            let _ = self.node_ids.insert(common.node_id.clone());
            if let Some(anchor) = &common.source_anchor {
                self.insert_global(&anchor.opaque_handle)?;
            }
            for style in &common.style_refs {
                self.add_pending(PendingReferenceKind::Style, style)?;
            }
            for resource in &common.resource_refs {
                self.add_pending(PendingReferenceKind::Resource, resource)?;
            }
            self.check_properties(&common.layout_hints, depth)?;
            self.check_properties(&common.semantics, depth)?;
            self.check_node_payload(node, depth)?;
        }
        Ok(())
    }

    fn check_node_payload(&mut self, node: &Node, depth: usize) -> Result<(), DocumentGraphError> {
        match node {
            Node::Paragraph(value) => {
                self.check_inlines(&value.inlines, depth)?;
                self.check_properties(&value.paragraph_properties, depth)?;
            }
            Node::Table(value) => self.check_table(value, depth)?,
            Node::Equation(value) => {
                match &value.source {
                    EquationSource::MathMl(text) | EquationSource::Formula(text) => {
                        self.check_len(text)?;
                    }
                    EquationSource::NativeOpaque(handle) => {
                        self.add_pending(PendingReferenceKind::Opaque, handle)?;
                    }
                }
                self.check_properties(&value.properties, depth)?;
            }
            Node::Drawing(value) => {
                if let Some(resource) = &value.resource_id {
                    self.add_pending(PendingReferenceKind::Resource, resource)?;
                }
                self.check_properties(&value.properties, depth)?;
                self.check_flow(&value.children, depth + 1)?;
            }
            Node::Chart(value) => {
                self.add_pending(PendingReferenceKind::Resource, &value.data_resource_id)?;
                self.check_properties(&value.properties, depth)?;
            }
            Node::Field(value) => {
                self.add_pending(PendingReferenceKind::Reference, &value.reference_id)?;
                self.check_properties(&value.properties, depth)?;
            }
            Node::FormControl(value) => {
                self.check_nonempty_text(&value.control_kind)?;
                self.check_properties(&value.properties, depth)?;
            }
            Node::Break(_) => {}
            Node::EmbeddedObject(value) => {
                self.add_pending(PendingReferenceKind::Resource, &value.resource_id)?;
                self.check_properties(&value.properties, depth)?;
            }
        }
        Ok(())
    }

    fn check_table(&mut self, table: &TableNode, depth: usize) -> Result<(), DocumentGraphError> {
        if table.rows == 0 || table.columns == 0 {
            return Err(DocumentGraphError::InvalidTableShape);
        }
        let capacity = usize::try_from(table.rows)
            .ok()
            .and_then(|rows| {
                usize::try_from(table.columns)
                    .ok()
                    .and_then(|columns| rows.checked_mul(columns))
            })
            .ok_or(DocumentGraphError::InvalidTableShape)?;
        if table.cells.len() > capacity {
            return Err(DocumentGraphError::InvalidTableShape);
        }
        self.table_cell_count = self
            .table_cell_count
            .checked_add(capacity)
            .ok_or(DocumentGraphError::LimitExceeded)?;
        if self.table_cell_count > self.limits.max_table_cells {
            return Err(DocumentGraphError::LimitExceeded);
        }
        let mut occupied = BTreeSet::new();
        for cell in &table.cells {
            self.insert_global(&cell.cell_id)?;
            let row_end = cell.row.checked_add(cell.row_span);
            let column_end = cell.column.checked_add(cell.column_span);
            if cell.row_span == 0
                || cell.column_span == 0
                || cell.row >= table.rows
                || cell.column >= table.columns
                || row_end.is_none_or(|end| end > table.rows)
                || column_end.is_none_or(|end| end > table.columns)
            {
                return Err(DocumentGraphError::InvalidTableShape);
            }
            for row in cell.row..row_end.ok_or(DocumentGraphError::InvalidTableShape)? {
                for column in
                    cell.column..column_end.ok_or(DocumentGraphError::InvalidTableShape)?
                {
                    if !occupied.insert((row, column)) {
                        return Err(DocumentGraphError::InvalidTableShape);
                    }
                }
            }
            self.check_properties(&cell.properties, depth)?;
            self.check_flow(&cell.body, depth + 1)?;
        }
        if occupied.len() != capacity {
            return Err(DocumentGraphError::InvalidTableShape);
        }
        self.check_properties(&table.properties, depth)
    }

    fn check_inlines(
        &mut self,
        inlines: &[Inline],
        depth: usize,
    ) -> Result<(), DocumentGraphError> {
        if depth > self.limits.max_depth {
            return Err(DocumentGraphError::LimitExceeded);
        }
        for inline in inlines {
            self.inline_count = self
                .inline_count
                .checked_add(1)
                .ok_or(DocumentGraphError::LimitExceeded)?;
            if self.inline_count > self.limits.max_inlines {
                return Err(DocumentGraphError::LimitExceeded);
            }
            match inline {
                Inline::Text { text } | Inline::InlineEquation { source: text } => {
                    self.check_len(text)?;
                }
                Inline::FieldRef { reference_id } | Inline::BookmarkAnchor { reference_id } => {
                    self.add_pending(PendingReferenceKind::Reference, reference_id)?;
                }
                Inline::ChangeSpan {
                    review_id,
                    children,
                } => {
                    self.add_pending(PendingReferenceKind::Review, review_id)?;
                    self.check_inlines(children, depth + 1)?;
                }
                Inline::ControlRef { node_id } => {
                    self.add_pending(PendingReferenceKind::Node, node_id)?;
                }
                Inline::Tab | Inline::LineBreak => {}
            }
        }
        Ok(())
    }

    fn check_properties(
        &mut self,
        properties: &Properties,
        depth: usize,
    ) -> Result<(), DocumentGraphError> {
        for (key, value) in properties.iter() {
            self.increment_property_count()?;
            if key.is_empty() || key.chars().any(char::is_control) {
                return Err(DocumentGraphError::InvalidValue);
            }
            self.check_len(key)?;
            self.check_property_value(value, depth + 1)?;
        }
        Ok(())
    }

    fn check_property_value(
        &mut self,
        value: &PropertyValue,
        depth: usize,
    ) -> Result<(), DocumentGraphError> {
        if depth > self.limits.max_depth {
            return Err(DocumentGraphError::LimitExceeded);
        }
        match value {
            PropertyValue::Text(text) | PropertyValue::Decimal(text) => self.check_len(text),
            PropertyValue::Id(id) => self.check_len(id.as_str()),
            PropertyValue::List(values) => {
                for child in values {
                    self.increment_property_count()?;
                    self.check_property_value(child, depth + 1)?;
                }
                Ok(())
            }
            PropertyValue::Object(values) => {
                for (key, child) in values {
                    self.increment_property_count()?;
                    if key.is_empty() || key.chars().any(char::is_control) {
                        return Err(DocumentGraphError::InvalidValue);
                    }
                    self.check_len(key)?;
                    self.check_property_value(child, depth + 1)?;
                }
                Ok(())
            }
            PropertyValue::Integer(_) | PropertyValue::Boolean(_) => Ok(()),
        }
    }

    fn increment_property_count(&mut self) -> Result<(), DocumentGraphError> {
        self.property_count = self
            .property_count
            .checked_add(1)
            .ok_or(DocumentGraphError::LimitExceeded)?;
        if self.property_count > self.limits.max_properties {
            return Err(DocumentGraphError::LimitExceeded);
        }
        Ok(())
    }

    fn check_len(&mut self, value: &str) -> Result<(), DocumentGraphError> {
        if value.len() > self.limits.max_string_bytes {
            return Err(DocumentGraphError::LimitExceeded);
        }
        self.total_string_bytes = self
            .total_string_bytes
            .checked_add(value.len())
            .ok_or(DocumentGraphError::LimitExceeded)?;
        if self.total_string_bytes > self.limits.max_total_string_bytes {
            return Err(DocumentGraphError::LimitExceeded);
        }
        Ok(())
    }

    fn check_nonempty_text(&mut self, value: &str) -> Result<(), DocumentGraphError> {
        if value.is_empty() || value.chars().any(char::is_control) {
            return Err(DocumentGraphError::InvalidValue);
        }
        self.check_len(value)
    }

    fn add_pending(
        &mut self,
        kind: PendingReferenceKind,
        id: &LogicalId,
    ) -> Result<(), DocumentGraphError> {
        if self.pending.len() >= self.limits.max_edges {
            return Err(DocumentGraphError::LimitExceeded);
        }
        self.check_len(id.as_str())?;
        self.pending.push((kind, id.clone()));
        Ok(())
    }

    fn insert_global(&mut self, id: &LogicalId) -> Result<(), DocumentGraphError> {
        self.check_len(id.as_str())?;
        if !self.all_ids.insert(id.clone()) {
            return Err(DocumentGraphError::DuplicateIdentifier);
        }
        Ok(())
    }

    fn resolve_pending(self) -> Result<(), DocumentGraphError> {
        for (kind, id) in self.pending {
            let exists = match kind {
                PendingReferenceKind::Node => self.node_ids.contains(&id),
                PendingReferenceKind::Resource => self.resource_ids.contains(&id),
                PendingReferenceKind::Style => self.style_ids.contains(&id),
                PendingReferenceKind::Reference => self.reference_ids.contains(&id),
                PendingReferenceKind::Review => self.review_ids.contains(&id),
                PendingReferenceKind::Opaque => self.opaque_ids.contains(&id),
            };
            if !exists {
                return Err(DocumentGraphError::DanglingReference);
            }
        }
        Ok(())
    }
}
