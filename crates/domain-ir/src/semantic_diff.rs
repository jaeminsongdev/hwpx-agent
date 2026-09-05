use std::collections::BTreeMap;
use std::fmt;

use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    DocumentGraph, DocumentGraphDraft, LogicalId, Node, NodeCommon, Properties, RevisionId,
};

pub const SEMANTIC_DIFF_SCHEMA_VERSION: &str = "hwpx-agent.semantic-diff/v1";

const MAX_ENTITY_LIMIT_CEILING: usize = 1_000_000;
const MAX_CHANGE_LIMIT_CEILING: usize = 1_000_000;
const MAX_DEPTH_LIMIT_CEILING: usize = 256;
const MAX_SERIALIZED_LIMIT_CEILING: usize = 256 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SemanticDiffLimits {
    pub max_entities: usize,
    pub max_changes: usize,
    pub max_depth: usize,
    pub max_serialized_bytes: usize,
}

impl Default for SemanticDiffLimits {
    fn default() -> Self {
        Self {
            max_entities: 200_000,
            max_changes: 200_000,
            max_depth: 128,
            max_serialized_bytes: 64 * 1024 * 1024,
        }
    }
}

impl SemanticDiffLimits {
    fn validate(self) -> Result<(), SemanticDiffError> {
        if self.max_entities == 0
            || self.max_entities > MAX_ENTITY_LIMIT_CEILING
            || self.max_changes == 0
            || self.max_changes > MAX_CHANGE_LIMIT_CEILING
            || self.max_depth == 0
            || self.max_depth > MAX_DEPTH_LIMIT_CEILING
            || self.max_serialized_bytes == 0
            || self.max_serialized_bytes > MAX_SERIALIZED_LIMIT_CEILING
        {
            return Err(SemanticDiffError::InvalidLimit);
        }
        Ok(())
    }
}

#[derive(Clone, Copy)]
pub struct SemanticDiffSnapshot<'a> {
    revision_id: &'a RevisionId,
    expected_graph_sha256: [u8; 32],
    graph: &'a DocumentGraph,
}

impl<'a> SemanticDiffSnapshot<'a> {
    /// Creates a revision-pinned immutable graph view.
    ///
    /// # Errors
    ///
    /// Rejects an all-zero declared graph digest.
    pub fn new(
        revision_id: &'a RevisionId,
        expected_graph_sha256: [u8; 32],
        graph: &'a DocumentGraph,
    ) -> Result<Self, SemanticDiffError> {
        if expected_graph_sha256 == [0; 32] {
            return Err(SemanticDiffError::InvalidSnapshot);
        }
        Ok(Self {
            revision_id,
            expected_graph_sha256,
            graph,
        })
    }
}

impl fmt::Debug for SemanticDiffSnapshot<'_> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("SemanticDiffSnapshot(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChangeCategory {
    Document,
    Node,
    Style,
    Resource,
    Table,
    Equation,
    Object,
    Reference,
    Opaque,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EntityKind {
    Document,
    Section,
    Node,
    Style,
    Resource,
    Table,
    TableCell,
    Equation,
    Drawing,
    Chart,
    Field,
    FormControl,
    Break,
    EmbeddedObject,
    Note,
    Reference,
    Review,
    OpaqueExtension,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChangeKind {
    Added,
    Removed,
    Modified,
    Moved,
    ModifiedAndMoved,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PathScope {
    Document,
    SectionBody,
    TableCellBody,
    DrawingChildren,
    NoteBody,
    Catalog,
    ReferenceCatalog,
    PreservationBag,
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticPath {
    scope: PathScope,
    parent_ref_sha256: Option<[u8; 32]>,
    ordinal: Option<u32>,
    row: Option<u32>,
    column: Option<u32>,
    depth: u16,
}

impl SemanticPath {
    fn root(scope: PathScope) -> Self {
        Self {
            scope,
            parent_ref_sha256: None,
            ordinal: None,
            row: None,
            column: None,
            depth: 0,
        }
    }

    fn ordered(scope: PathScope, parent_ref_sha256: [u8; 32], ordinal: u32, depth: u16) -> Self {
        Self {
            scope,
            parent_ref_sha256: Some(parent_ref_sha256),
            ordinal: Some(ordinal),
            row: None,
            column: None,
            depth,
        }
    }

    fn table_cell(parent_ref_sha256: [u8; 32], row: u32, column: u32, depth: u16) -> Self {
        Self {
            scope: PathScope::TableCellBody,
            parent_ref_sha256: Some(parent_ref_sha256),
            ordinal: None,
            row: Some(row),
            column: Some(column),
            depth,
        }
    }

    #[must_use]
    pub const fn scope(&self) -> PathScope {
        self.scope
    }

    #[must_use]
    pub const fn parent_ref_sha256(&self) -> Option<[u8; 32]> {
        self.parent_ref_sha256
    }

    #[must_use]
    pub const fn ordinal(&self) -> Option<u32> {
        self.ordinal
    }

    #[must_use]
    pub const fn row(&self) -> Option<u32> {
        self.row
    }

    #[must_use]
    pub const fn column(&self) -> Option<u32> {
        self.column
    }

    #[must_use]
    pub const fn depth(&self) -> u16 {
        self.depth
    }
}

impl fmt::Debug for SemanticPath {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SemanticPath")
            .field("scope", &self.scope)
            .field("ordinal", &self.ordinal)
            .field("row", &self.row)
            .field("column", &self.column)
            .field("depth", &self.depth)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticChange {
    category: ChangeCategory,
    entity_kind: EntityKind,
    change_kind: ChangeKind,
    subject_ref_sha256: [u8; 32],
    before_path: Option<SemanticPath>,
    after_path: Option<SemanticPath>,
    before_value_sha256: Option<[u8; 32]>,
    after_value_sha256: Option<[u8; 32]>,
    before_reference_count: Option<u64>,
    after_reference_count: Option<u64>,
}

impl SemanticChange {
    #[must_use]
    pub const fn category(&self) -> ChangeCategory {
        self.category
    }

    #[must_use]
    pub const fn entity_kind(&self) -> EntityKind {
        self.entity_kind
    }

    #[must_use]
    pub const fn change_kind(&self) -> ChangeKind {
        self.change_kind
    }

    #[must_use]
    pub const fn subject_ref_sha256(&self) -> [u8; 32] {
        self.subject_ref_sha256
    }

    #[must_use]
    pub const fn before_path(&self) -> Option<&SemanticPath> {
        self.before_path.as_ref()
    }

    #[must_use]
    pub const fn after_path(&self) -> Option<&SemanticPath> {
        self.after_path.as_ref()
    }

    #[must_use]
    pub const fn before_reference_count(&self) -> Option<u64> {
        self.before_reference_count
    }

    #[must_use]
    pub const fn after_reference_count(&self) -> Option<u64> {
        self.after_reference_count
    }

    #[must_use]
    pub const fn before_value_sha256(&self) -> Option<[u8; 32]> {
        self.before_value_sha256
    }

    #[must_use]
    pub const fn after_value_sha256(&self) -> Option<[u8; 32]> {
        self.after_value_sha256
    }
}

impl fmt::Debug for SemanticChange {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SemanticChange")
            .field("category", &self.category)
            .field("entity_kind", &self.entity_kind)
            .field("change_kind", &self.change_kind)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticDiff {
    schema_version: String,
    document_ref_sha256: [u8; 32],
    before_revision_ref_sha256: [u8; 32],
    after_revision_ref_sha256: [u8; 32],
    before_graph_sha256: [u8; 32],
    after_graph_sha256: [u8; 32],
    changes: Vec<SemanticChange>,
}

impl SemanticDiff {
    /// Compares two exact validated graph snapshots without mutating either graph.
    ///
    /// # Errors
    ///
    /// Fails closed on document/revision/digest mismatch, duplicate subjects, finite limits or
    /// deterministic serialization failure.
    pub fn between(
        before: SemanticDiffSnapshot<'_>,
        after: SemanticDiffSnapshot<'_>,
        limits: SemanticDiffLimits,
    ) -> Result<Self, SemanticDiffError> {
        limits.validate()?;
        if before.graph.document_id() != after.graph.document_id() {
            return Err(SemanticDiffError::DocumentMismatch);
        }
        let before_actual = before
            .graph
            .canonical_sha256()
            .map_err(|_| SemanticDiffError::SerializationFailed)?;
        let after_actual = after
            .graph
            .canonical_sha256()
            .map_err(|_| SemanticDiffError::SerializationFailed)?;
        if before_actual != before.expected_graph_sha256
            || after_actual != after.expected_graph_sha256
        {
            return Err(SemanticDiffError::SnapshotDigestMismatch);
        }
        if before.revision_id == after.revision_id && before_actual != after_actual {
            return Err(SemanticDiffError::RevisionDigestConflict);
        }

        let before_index = EntityIndex::build(before.graph.draft(), limits)?;
        let after_index = EntityIndex::build(after.graph.draft(), limits)?;
        let mut changes = compare_indices(&before_index, &after_index, limits.max_changes)?;
        changes.sort();

        let diff = Self {
            schema_version: SEMANTIC_DIFF_SCHEMA_VERSION.to_owned(),
            document_ref_sha256: subject_ref(
                EntityKind::Document,
                before.graph.document_id().as_str(),
            ),
            before_revision_ref_sha256: typed_ref("revision", before.revision_id.as_str()),
            after_revision_ref_sha256: typed_ref("revision", after.revision_id.as_str()),
            before_graph_sha256: before_actual,
            after_graph_sha256: after_actual,
            changes,
        };
        if diff.canonical_json()?.len() > limits.max_serialized_bytes {
            return Err(SemanticDiffError::LimitExceeded);
        }
        Ok(diff)
    }

    #[must_use]
    pub fn changes(&self) -> &[SemanticChange] {
        &self.changes
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.changes.is_empty()
    }

    #[must_use]
    pub const fn before_graph_sha256(&self) -> [u8; 32] {
        self.before_graph_sha256
    }

    #[must_use]
    pub const fn after_graph_sha256(&self) -> [u8; 32] {
        self.after_graph_sha256
    }

    /// Emits deterministic compact diff bytes containing hashes and typed paths, never raw values.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization error.
    pub fn canonical_json(&self) -> Result<Vec<u8>, SemanticDiffError> {
        serde_json::to_vec(self).map_err(|_| SemanticDiffError::SerializationFailed)
    }

    /// Hashes the canonical semantic diff.
    ///
    /// # Errors
    ///
    /// Propagates a stable serialization error.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], SemanticDiffError> {
        Ok(Sha256::digest(self.canonical_json()?).into())
    }
}

impl fmt::Debug for SemanticDiff {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SemanticDiff")
            .field("change_count", &self.changes.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum SemanticDiffError {
    #[error("semantic diff limit is invalid")]
    InvalidLimit,
    #[error("semantic diff snapshot is invalid")]
    InvalidSnapshot,
    #[error("semantic diff documents do not match")]
    DocumentMismatch,
    #[error("semantic diff snapshot digest does not match")]
    SnapshotDigestMismatch,
    #[error("semantic diff revision has conflicting graph digests")]
    RevisionDigestConflict,
    #[error("semantic diff subject is duplicated")]
    DuplicateSubject,
    #[error("semantic diff finite limit exceeded")]
    LimitExceeded,
    #[error("semantic diff serialization failed")]
    SerializationFailed,
}

impl SemanticDiffError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "semantic_diff_invalid_limit",
            Self::InvalidSnapshot => "semantic_diff_invalid_snapshot",
            Self::DocumentMismatch => "semantic_diff_document_mismatch",
            Self::SnapshotDigestMismatch => "semantic_diff_snapshot_digest_mismatch",
            Self::RevisionDigestConflict => "semantic_diff_revision_digest_conflict",
            Self::DuplicateSubject => "semantic_diff_duplicate_subject",
            Self::LimitExceeded => "semantic_diff_limit_exceeded",
            Self::SerializationFailed => "semantic_diff_serialization_failed",
        }
    }
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd)]
struct EntityKey {
    kind: EntityKind,
    raw_id: String,
}

#[derive(Clone, Eq, PartialEq)]
struct EntitySnapshot {
    category: ChangeCategory,
    key: EntityKey,
    path: SemanticPath,
    value_sha256: [u8; 32],
    reference_count: u64,
}

struct EntityIndex {
    entities: BTreeMap<EntityKey, EntitySnapshot>,
    reference_counts: BTreeMap<EntityKey, u64>,
}

impl EntityIndex {
    fn build(
        draft: &DocumentGraphDraft,
        limits: SemanticDiffLimits,
    ) -> Result<Self, SemanticDiffError> {
        let mut builder = IndexBuilder {
            entities: BTreeMap::new(),
            reference_counts: BTreeMap::new(),
            limits,
        };
        builder.add_document(draft)?;
        builder.add_sections(draft)?;
        builder.add_catalogs(draft)?;
        builder.add_reference_catalogs(draft)?;
        builder.apply_reference_counts();
        Ok(Self {
            entities: builder.entities,
            reference_counts: builder.reference_counts,
        })
    }
}

struct IndexBuilder {
    entities: BTreeMap<EntityKey, EntitySnapshot>,
    reference_counts: BTreeMap<EntityKey, u64>,
    limits: SemanticDiffLimits,
}

impl IndexBuilder {
    fn add_document(&mut self, draft: &DocumentGraphDraft) -> Result<(), SemanticDiffError> {
        self.add_serialized(
            ChangeCategory::Document,
            EntityKind::Document,
            draft.document_id.as_str(),
            SemanticPath::root(PathScope::Document),
            &DocumentSignature {
                source_profile: &draft.source_profile,
                metadata: &draft.metadata,
                settings: &draft.settings,
                security_state: &draft.security_state,
                accessibility: &draft.accessibility,
            },
        )
    }

    fn add_sections(&mut self, draft: &DocumentGraphDraft) -> Result<(), SemanticDiffError> {
        for (ordinal, section) in draft.sections.iter().enumerate() {
            let section_ref = subject_ref(EntityKind::Section, section.section_id.as_str());
            self.add_serialized(
                ChangeCategory::Document,
                EntityKind::Section,
                section.section_id.as_str(),
                SemanticPath::ordered(
                    PathScope::Document,
                    subject_ref(EntityKind::Document, draft.document_id.as_str()),
                    checked_u32(ordinal)?,
                    0,
                ),
                &SectionSignature {
                    properties: &section.properties,
                    master_pages: &section.master_pages,
                    headers_footers: &section.headers_footers,
                },
            )?;
            self.add_references(EntityKind::Node, &section.master_pages)?;
            self.add_references(EntityKind::Node, &section.headers_footers)?;
            self.add_flow(
                &section.body.children,
                PathScope::SectionBody,
                section_ref,
                1,
            )?;
        }
        Ok(())
    }

    fn add_catalogs(&mut self, draft: &DocumentGraphDraft) -> Result<(), SemanticDiffError> {
        for resource in &draft.resources {
            self.add_serialized(
                ChangeCategory::Resource,
                EntityKind::Resource,
                resource.resource_id.as_str(),
                SemanticPath::root(PathScope::Catalog),
                resource,
            )?;
        }
        for style in &draft.styles {
            self.add_serialized(
                ChangeCategory::Style,
                EntityKind::Style,
                style.style_id.as_str(),
                SemanticPath::root(PathScope::Catalog),
                style,
            )?;
            if let Some(based_on) = &style.based_on {
                self.add_reference(EntityKind::Style, based_on.as_str())?;
            }
        }
        Ok(())
    }

    fn add_reference_catalogs(
        &mut self,
        draft: &DocumentGraphDraft,
    ) -> Result<(), SemanticDiffError> {
        for note in &draft.notes {
            let note_ref = subject_ref(EntityKind::Note, note.note_id.as_str());
            self.add_serialized(
                ChangeCategory::Reference,
                EntityKind::Note,
                note.note_id.as_str(),
                SemanticPath::root(PathScope::ReferenceCatalog),
                &note.properties,
            )?;
            self.add_flow(&note.body.children, PathScope::NoteBody, note_ref, 1)?;
        }
        for reference in &draft.references {
            self.add_serialized(
                ChangeCategory::Reference,
                EntityKind::Reference,
                reference.reference_id.as_str(),
                SemanticPath::root(PathScope::ReferenceCatalog),
                reference,
            )?;
            if let Some(target) = &reference.target_node_id {
                self.add_reference(EntityKind::Node, target.as_str())?;
            }
        }
        for review in &draft.review {
            self.add_serialized(
                ChangeCategory::Reference,
                EntityKind::Review,
                review.review_id.as_str(),
                SemanticPath::root(PathScope::ReferenceCatalog),
                review,
            )?;
            self.add_reference(EntityKind::Node, review.target_node_id.as_str())?;
        }
        for opaque in &draft.opaque_preservation_bag {
            self.add_serialized(
                ChangeCategory::Opaque,
                EntityKind::OpaqueExtension,
                opaque.handle.as_str(),
                SemanticPath::root(PathScope::PreservationBag),
                opaque,
            )?;
        }
        Ok(())
    }

    fn apply_reference_counts(&mut self) {
        for (key, count) in &self.reference_counts {
            if let Some(entity) = self.entities.get_mut(key) {
                entity.reference_count = *count;
            }
        }
    }

    fn add_serialized<T: Serialize + ?Sized>(
        &mut self,
        category: ChangeCategory,
        kind: EntityKind,
        raw_id: &str,
        path: SemanticPath,
        value: &T,
    ) -> Result<(), SemanticDiffError> {
        if self.entities.len() >= self.limits.max_entities {
            return Err(SemanticDiffError::LimitExceeded);
        }
        let key = EntityKey {
            kind,
            raw_id: raw_id.to_owned(),
        };
        let snapshot = EntitySnapshot {
            category,
            key: key.clone(),
            path,
            value_sha256: canonical_sha256(value)?,
            reference_count: 0,
        };
        if self.entities.insert(key, snapshot).is_some() {
            return Err(SemanticDiffError::DuplicateSubject);
        }
        Ok(())
    }

    fn add_flow(
        &mut self,
        nodes: &[Node],
        scope: PathScope,
        parent_ref_sha256: [u8; 32],
        depth: usize,
    ) -> Result<(), SemanticDiffError> {
        if depth > self.limits.max_depth {
            return Err(SemanticDiffError::LimitExceeded);
        }
        let depth_u16 = u16::try_from(depth).map_err(|_| SemanticDiffError::LimitExceeded)?;
        for (ordinal, node) in nodes.iter().enumerate() {
            let common = node.common();
            let node_id = common.node_id.as_str();
            let path =
                SemanticPath::ordered(scope, parent_ref_sha256, checked_u32(ordinal)?, depth_u16);
            self.add_serialized(
                ChangeCategory::Node,
                EntityKind::Node,
                node_id,
                path.clone(),
                &NodeCore::from(node),
            )?;
            self.add_common_references(common)?;
            self.add_node_details(node, node_id, &path, depth)?;
        }
        Ok(())
    }

    fn add_node_details(
        &mut self,
        node: &Node,
        node_id: &str,
        path: &SemanticPath,
        depth: usize,
    ) -> Result<(), SemanticDiffError> {
        match node {
            Node::Paragraph(paragraph) => self.add_inline_references(&paragraph.inlines),
            Node::Table(table) => self.add_table(table, node_id, path, depth),
            Node::Equation(equation) => self.add_equation(equation, node_id, path),
            Node::Drawing(drawing) => self.add_drawing(drawing, node_id, path, depth),
            Node::Chart(_)
            | Node::Field(_)
            | Node::FormControl(_)
            | Node::Break(_)
            | Node::EmbeddedObject(_) => self.add_leaf_object(node, node_id, path),
        }
    }

    fn add_table(
        &mut self,
        table: &crate::TableNode,
        node_id: &str,
        path: &SemanticPath,
        depth: usize,
    ) -> Result<(), SemanticDiffError> {
        self.add_serialized(
            ChangeCategory::Table,
            EntityKind::Table,
            node_id,
            path.clone(),
            &TableSignature {
                rows: table.rows,
                columns: table.columns,
                properties: &table.properties,
            },
        )?;
        let table_ref = subject_ref(EntityKind::Table, node_id);
        let depth_u16 = u16::try_from(depth).map_err(|_| SemanticDiffError::LimitExceeded)?;
        for cell in &table.cells {
            self.add_serialized(
                ChangeCategory::Table,
                EntityKind::TableCell,
                cell.cell_id.as_str(),
                SemanticPath::table_cell(table_ref, cell.row, cell.column, depth_u16),
                &TableCellSignature {
                    row_span: cell.row_span,
                    column_span: cell.column_span,
                    properties: &cell.properties,
                },
            )?;
            self.add_flow(
                &cell.body.children,
                PathScope::TableCellBody,
                subject_ref(EntityKind::TableCell, cell.cell_id.as_str()),
                depth + 1,
            )?;
        }
        Ok(())
    }

    fn add_equation(
        &mut self,
        equation: &crate::EquationNode,
        node_id: &str,
        path: &SemanticPath,
    ) -> Result<(), SemanticDiffError> {
        self.add_serialized(
            ChangeCategory::Equation,
            EntityKind::Equation,
            node_id,
            path.clone(),
            &EquationSignature {
                source: &equation.source,
                display: equation.display,
                properties: &equation.properties,
            },
        )
    }

    fn add_drawing(
        &mut self,
        drawing: &crate::DrawingNode,
        node_id: &str,
        path: &SemanticPath,
        depth: usize,
    ) -> Result<(), SemanticDiffError> {
        self.add_serialized(
            ChangeCategory::Object,
            EntityKind::Drawing,
            node_id,
            path.clone(),
            &ObjectSignature::Drawing {
                resource_id: &drawing.resource_id,
                properties: &drawing.properties,
            },
        )?;
        if let Some(resource) = &drawing.resource_id
            && !drawing.common.resource_refs.contains(resource)
        {
            self.add_reference(EntityKind::Resource, resource.as_str())?;
        }
        self.add_flow(
            &drawing.children.children,
            PathScope::DrawingChildren,
            subject_ref(EntityKind::Drawing, node_id),
            depth + 1,
        )
    }

    fn add_leaf_object(
        &mut self,
        node: &Node,
        node_id: &str,
        path: &SemanticPath,
    ) -> Result<(), SemanticDiffError> {
        match node {
            Node::Chart(chart) => {
                self.add_serialized(
                    ChangeCategory::Object,
                    EntityKind::Chart,
                    node_id,
                    path.clone(),
                    &ObjectSignature::Chart {
                        resource_id: &chart.data_resource_id,
                        properties: &chart.properties,
                    },
                )?;
                if chart.common.resource_refs.contains(&chart.data_resource_id) {
                    Ok(())
                } else {
                    self.add_reference(EntityKind::Resource, chart.data_resource_id.as_str())
                }
            }
            Node::Field(field) => {
                self.add_serialized(
                    ChangeCategory::Object,
                    EntityKind::Field,
                    node_id,
                    path.clone(),
                    &ObjectSignature::Field {
                        reference_id: &field.reference_id,
                        properties: &field.properties,
                    },
                )?;
                self.add_reference(EntityKind::Reference, field.reference_id.as_str())
            }
            Node::FormControl(form) => self.add_serialized(
                ChangeCategory::Object,
                EntityKind::FormControl,
                node_id,
                path.clone(),
                &ObjectSignature::FormControl {
                    control_kind: &form.control_kind,
                    properties: &form.properties,
                },
            ),
            Node::Break(break_node) => self.add_serialized(
                ChangeCategory::Object,
                EntityKind::Break,
                node_id,
                path.clone(),
                &break_node.break_kind,
            ),
            Node::EmbeddedObject(embedded) => {
                self.add_serialized(
                    ChangeCategory::Object,
                    EntityKind::EmbeddedObject,
                    node_id,
                    path.clone(),
                    &ObjectSignature::Embedded {
                        object_type: &embedded.object_type,
                        resource_id: &embedded.resource_id,
                        properties: &embedded.properties,
                    },
                )?;
                if embedded
                    .common
                    .resource_refs
                    .contains(&embedded.resource_id)
                {
                    Ok(())
                } else {
                    self.add_reference(EntityKind::Resource, embedded.resource_id.as_str())
                }
            }
            Node::Paragraph(_) | Node::Table(_) | Node::Equation(_) | Node::Drawing(_) => Ok(()),
        }
    }

    fn add_common_references(&mut self, common: &NodeCommon) -> Result<(), SemanticDiffError> {
        self.add_references(EntityKind::Style, &common.style_refs)?;
        self.add_references(EntityKind::Resource, &common.resource_refs)
    }

    fn add_inline_references(
        &mut self,
        inlines: &[crate::Inline],
    ) -> Result<(), SemanticDiffError> {
        for inline in inlines {
            match inline {
                crate::Inline::FieldRef { reference_id }
                | crate::Inline::BookmarkAnchor { reference_id } => {
                    self.add_reference(EntityKind::Reference, reference_id.as_str())?;
                }
                crate::Inline::ChangeSpan {
                    review_id,
                    children,
                } => {
                    self.add_reference(EntityKind::Review, review_id.as_str())?;
                    self.add_inline_references(children)?;
                }
                crate::Inline::ControlRef { node_id } => {
                    self.add_reference(EntityKind::Node, node_id.as_str())?;
                }
                crate::Inline::Text { .. }
                | crate::Inline::InlineEquation { .. }
                | crate::Inline::Tab
                | crate::Inline::LineBreak => {}
            }
        }
        Ok(())
    }

    fn add_references(
        &mut self,
        kind: EntityKind,
        values: &[LogicalId],
    ) -> Result<(), SemanticDiffError> {
        for value in values {
            self.add_reference(kind, value.as_str())?;
        }
        Ok(())
    }

    fn add_reference(&mut self, kind: EntityKind, raw_id: &str) -> Result<(), SemanticDiffError> {
        let count = self
            .reference_counts
            .entry(EntityKey {
                kind,
                raw_id: raw_id.to_owned(),
            })
            .or_default();
        *count = count
            .checked_add(1)
            .ok_or(SemanticDiffError::LimitExceeded)?;
        Ok(())
    }
}

fn compare_indices(
    before: &EntityIndex,
    after: &EntityIndex,
    max_changes: usize,
) -> Result<Vec<SemanticChange>, SemanticDiffError> {
    let mut changes = Vec::new();
    let mut keys = before
        .entities
        .keys()
        .chain(after.entities.keys())
        .cloned()
        .collect::<Vec<_>>();
    keys.sort();
    keys.dedup();
    for key in keys {
        let left = before.entities.get(&key);
        let right = after.entities.get(&key);
        let (category, change_kind) = match (left, right) {
            (Some(entity), None) => (entity.category, ChangeKind::Removed),
            (None, Some(entity)) => (entity.category, ChangeKind::Added),
            (Some(left), Some(right)) => {
                let modified = left.value_sha256 != right.value_sha256;
                let moved = path_changed_semantically(&key, left, right, before, after);
                let kind = match (modified, moved) {
                    (false, false) => continue,
                    (true, false) => ChangeKind::Modified,
                    (false, true) => ChangeKind::Moved,
                    (true, true) => ChangeKind::ModifiedAndMoved,
                };
                (left.category, kind)
            }
            (None, None) => continue,
        };
        if changes.len() >= max_changes {
            return Err(SemanticDiffError::LimitExceeded);
        }
        changes.push(SemanticChange {
            category,
            entity_kind: key.kind,
            change_kind,
            subject_ref_sha256: subject_ref(key.kind, &key.raw_id),
            before_path: left.map(|entity| entity.path.clone()),
            after_path: right.map(|entity| entity.path.clone()),
            before_value_sha256: left.map(|entity| entity.value_sha256),
            after_value_sha256: right.map(|entity| entity.value_sha256),
            before_reference_count: left.map(|entity| {
                before
                    .reference_counts
                    .get(&entity.key)
                    .copied()
                    .unwrap_or(entity.reference_count)
            }),
            after_reference_count: right.map(|entity| {
                after
                    .reference_counts
                    .get(&entity.key)
                    .copied()
                    .unwrap_or(entity.reference_count)
            }),
        });
    }
    Ok(changes)
}

fn path_changed_semantically(
    key: &EntityKey,
    before_entity: &EntitySnapshot,
    after_entity: &EntitySnapshot,
    before: &EntityIndex,
    after: &EntityIndex,
) -> bool {
    let left = &before_entity.path;
    let right = &after_entity.path;
    if !same_container(left, right) {
        return true;
    }
    if !matches!(key.kind, EntityKind::Node | EntityKind::Section) || left.ordinal == right.ordinal
    {
        return false;
    }
    relative_rank(before, after, key, left, right) != relative_rank(after, before, key, right, left)
}

fn same_container(left: &SemanticPath, right: &SemanticPath) -> bool {
    left.scope == right.scope
        && left.parent_ref_sha256 == right.parent_ref_sha256
        && left.row == right.row
        && left.column == right.column
        && left.depth == right.depth
}

fn relative_rank(
    primary: &EntityIndex,
    secondary: &EntityIndex,
    key: &EntityKey,
    primary_path: &SemanticPath,
    secondary_path: &SemanticPath,
) -> usize {
    primary
        .entities
        .iter()
        .filter(|(candidate_key, candidate)| {
            if candidate_key.kind != key.kind
                || !same_container(&candidate.path, primary_path)
                || candidate.path.ordinal >= primary_path.ordinal
            {
                return false;
            }
            let Some(counterpart) = secondary.entities.get(*candidate_key) else {
                return false;
            };
            same_container(&counterpart.path, secondary_path)
        })
        .count()
}

#[derive(Serialize)]
struct DocumentSignature<'a> {
    source_profile: &'a Option<LogicalId>,
    metadata: &'a Properties,
    settings: &'a Properties,
    security_state: &'a crate::SecurityState,
    accessibility: &'a crate::AccessibilityState,
}

#[derive(Serialize)]
struct SectionSignature<'a> {
    properties: &'a Properties,
    master_pages: &'a [LogicalId],
    headers_footers: &'a [LogicalId],
}

#[derive(Serialize)]
#[serde(tag = "node_type", rename_all = "snake_case")]
enum NodeCore<'a> {
    Paragraph {
        common: &'a NodeCommon,
        inlines: &'a [crate::Inline],
        properties: &'a Properties,
    },
    Table {
        common: &'a NodeCommon,
    },
    Equation {
        common: &'a NodeCommon,
    },
    Drawing {
        common: &'a NodeCommon,
    },
    Chart {
        common: &'a NodeCommon,
    },
    Field {
        common: &'a NodeCommon,
    },
    FormControl {
        common: &'a NodeCommon,
    },
    Break {
        common: &'a NodeCommon,
    },
    EmbeddedObject {
        common: &'a NodeCommon,
    },
}

impl<'a> From<&'a Node> for NodeCore<'a> {
    fn from(node: &'a Node) -> Self {
        match node {
            Node::Paragraph(value) => Self::Paragraph {
                common: &value.common,
                inlines: &value.inlines,
                properties: &value.paragraph_properties,
            },
            Node::Table(value) => Self::Table {
                common: &value.common,
            },
            Node::Equation(value) => Self::Equation {
                common: &value.common,
            },
            Node::Drawing(value) => Self::Drawing {
                common: &value.common,
            },
            Node::Chart(value) => Self::Chart {
                common: &value.common,
            },
            Node::Field(value) => Self::Field {
                common: &value.common,
            },
            Node::FormControl(value) => Self::FormControl {
                common: &value.common,
            },
            Node::Break(value) => Self::Break {
                common: &value.common,
            },
            Node::EmbeddedObject(value) => Self::EmbeddedObject {
                common: &value.common,
            },
        }
    }
}

#[derive(Serialize)]
struct TableSignature<'a> {
    rows: u32,
    columns: u32,
    properties: &'a Properties,
}

#[derive(Serialize)]
struct TableCellSignature<'a> {
    row_span: u32,
    column_span: u32,
    properties: &'a Properties,
}

#[derive(Serialize)]
struct EquationSignature<'a> {
    source: &'a crate::EquationSource,
    display: bool,
    properties: &'a Properties,
}

#[derive(Serialize)]
#[serde(tag = "object_kind", rename_all = "snake_case")]
enum ObjectSignature<'a> {
    Drawing {
        resource_id: &'a Option<LogicalId>,
        properties: &'a Properties,
    },
    Chart {
        resource_id: &'a LogicalId,
        properties: &'a Properties,
    },
    Field {
        reference_id: &'a LogicalId,
        properties: &'a Properties,
    },
    FormControl {
        control_kind: &'a str,
        properties: &'a Properties,
    },
    Embedded {
        object_type: &'a crate::EmbeddedObjectType,
        resource_id: &'a LogicalId,
        properties: &'a Properties,
    },
}

fn canonical_sha256<T: Serialize + ?Sized>(value: &T) -> Result<[u8; 32], SemanticDiffError> {
    let bytes = serde_json::to_vec(value).map_err(|_| SemanticDiffError::SerializationFailed)?;
    Ok(Sha256::digest(bytes).into())
}

pub(crate) fn subject_ref(kind: EntityKind, raw_id: &str) -> [u8; 32] {
    typed_ref(entity_kind_name(kind), raw_id)
}

fn typed_ref(prefix: &str, raw_id: &str) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(prefix.as_bytes());
    hasher.update([0]);
    hasher.update(raw_id.as_bytes());
    hasher.finalize().into()
}

const fn entity_kind_name(kind: EntityKind) -> &'static str {
    match kind {
        EntityKind::Document => "document",
        EntityKind::Section => "section",
        EntityKind::Node => "node",
        EntityKind::Style => "style",
        EntityKind::Resource => "resource",
        EntityKind::Table => "table",
        EntityKind::TableCell => "table_cell",
        EntityKind::Equation => "equation",
        EntityKind::Drawing => "drawing",
        EntityKind::Chart => "chart",
        EntityKind::Field => "field",
        EntityKind::FormControl => "form_control",
        EntityKind::Break => "break",
        EntityKind::EmbeddedObject => "embedded_object",
        EntityKind::Note => "note",
        EntityKind::Reference => "reference",
        EntityKind::Review => "review",
        EntityKind::OpaqueExtension => "opaque_extension",
    }
}

fn checked_u32(value: usize) -> Result<u32, SemanticDiffError> {
    u32::try_from(value).map_err(|_| SemanticDiffError::LimitExceeded)
}
