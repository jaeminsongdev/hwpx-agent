use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use unicode_normalization::UnicodeNormalization as _;

use crate::{
    DocumentGraph, DocumentGraphDraft, Flow, Inline, LogicalId, Node, Properties, PropertyValue,
    RevisionId,
};

const HARD_MAX_PATH_STEPS: usize = 256;
const HARD_MAX_NAME_BYTES: usize = 4 * 1024;
const HARD_MAX_QUERY_BYTES: usize = 64 * 1024;
const HARD_MAX_CONTEXT_SCALARS: usize = 4 * 1024;
const HARD_MAX_CANDIDATES: usize = 1_000_000;
const HARD_MAX_INDEXED_NODES: usize = 1_000_000;
const HARD_MAX_INDEXED_TEXT_BYTES: usize = 64 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SelectorLimits {
    pub max_path_steps: usize,
    pub max_name_bytes: usize,
    pub max_query_bytes: usize,
    pub max_context_scalars: usize,
    pub max_candidates: usize,
    pub max_indexed_nodes: usize,
    pub max_indexed_text_bytes: usize,
}

impl Default for SelectorLimits {
    fn default() -> Self {
        Self {
            max_path_steps: 64,
            max_name_bytes: 512,
            max_query_bytes: 4 * 1024,
            max_context_scalars: 256,
            max_candidates: 4 * 1024,
            max_indexed_nodes: 250_000,
            max_indexed_text_bytes: 16 * 1024 * 1024,
        }
    }
}

impl SelectorLimits {
    fn validate(self) -> Result<(), SelectorError> {
        let valid = self.max_path_steps > 0
            && self.max_path_steps <= HARD_MAX_PATH_STEPS
            && self.max_name_bytes > 0
            && self.max_name_bytes <= HARD_MAX_NAME_BYTES
            && self.max_query_bytes > 0
            && self.max_query_bytes <= HARD_MAX_QUERY_BYTES
            && self.max_context_scalars > 0
            && self.max_context_scalars <= HARD_MAX_CONTEXT_SCALARS
            && self.max_candidates > 0
            && self.max_candidates <= HARD_MAX_CANDIDATES
            && self.max_indexed_nodes > 0
            && self.max_indexed_nodes <= HARD_MAX_INDEXED_NODES
            && self.max_indexed_text_bytes > 0
            && self.max_indexed_text_bytes <= HARD_MAX_INDEXED_TEXT_BYTES;
        if !valid {
            return Err(SelectorError::InvalidLimit);
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NodeKind {
    Paragraph,
    Table,
    Equation,
    Drawing,
    Chart,
    Field,
    FormControl,
    Break,
    EmbeddedObject,
}

impl NodeKind {
    const fn of(node: &Node) -> Self {
        match node {
            Node::Paragraph(_) => Self::Paragraph,
            Node::Table(_) => Self::Table,
            Node::Equation(_) => Self::Equation,
            Node::Drawing(_) => Self::Drawing,
            Node::Chart(_) => Self::Chart,
            Node::Field(_) => Self::Field,
            Node::FormControl(_) => Self::FormControl,
            Node::Break(_) => Self::Break,
            Node::EmbeddedObject(_) => Self::EmbeddedObject,
        }
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(tag = "step", rename_all = "snake_case")]
pub enum StructuralStep {
    FlowChild { index: u32, expected_kind: NodeKind },
    TableCell { row: u32, column: u32 },
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(tag = "root", rename_all = "snake_case")]
pub enum StructuralRoot {
    Section { index: u32 },
    Note { index: u32 },
}

#[derive(Clone, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct StructuralPath {
    root: StructuralRoot,
    steps: Vec<StructuralStep>,
}

impl StructuralPath {
    /// Creates a finite section/block/table/cell path.
    ///
    /// # Errors
    ///
    /// Rejects an empty path or one beyond the hard selector depth ceiling.
    pub fn new(section_index: u32, steps: Vec<StructuralStep>) -> Result<Self, SelectorError> {
        Self::from_root(
            StructuralRoot::Section {
                index: section_index,
            },
            steps,
        )
    }

    /// Creates a finite path rooted in a note body.
    ///
    /// # Errors
    ///
    /// Rejects an empty path or one beyond the hard selector depth ceiling.
    pub fn new_note(note_index: u32, steps: Vec<StructuralStep>) -> Result<Self, SelectorError> {
        Self::from_root(StructuralRoot::Note { index: note_index }, steps)
    }

    fn from_root(root: StructuralRoot, steps: Vec<StructuralStep>) -> Result<Self, SelectorError> {
        if steps.is_empty() || steps.len() > HARD_MAX_PATH_STEPS {
            return Err(SelectorError::InvalidSelector);
        }
        Ok(Self { root, steps })
    }

    #[must_use]
    pub const fn root(&self) -> StructuralRoot {
        self.root
    }

    #[must_use]
    pub fn steps(&self) -> &[StructuralStep] {
        &self.steps
    }
}

impl fmt::Debug for StructuralPath {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("StructuralPath")
            .field("step_count", &self.steps.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NamedSelectorKind {
    Slot,
    Field,
    Bookmark,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TextContextAnchor {
    scalar_count: u32,
    sha256: [u8; 32],
}

impl TextContextAnchor {
    /// Creates a content-safe anchor over NFC-normalized context text.
    ///
    /// # Errors
    ///
    /// Rejects empty or excessively large context.
    pub fn from_text(value: &str) -> Result<Self, SelectorError> {
        let normalized = normalize(value);
        let scalar_count = normalized.chars().count();
        if scalar_count == 0
            || scalar_count > HARD_MAX_CONTEXT_SCALARS
            || normalized.len() > HARD_MAX_QUERY_BYTES
        {
            return Err(SelectorError::InvalidSelector);
        }
        let scalar_count =
            u32::try_from(scalar_count).map_err(|_| SelectorError::InvalidSelector)?;
        Ok(Self {
            scalar_count,
            sha256: Sha256::digest(normalized.as_bytes()).into(),
        })
    }

    #[must_use]
    pub const fn scalar_count(&self) -> u32 {
        self.scalar_count
    }
}

impl fmt::Debug for TextContextAnchor {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("TextContextAnchor(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "selector_type", rename_all = "snake_case")]
pub enum Selector {
    LogicalId {
        node_id: LogicalId,
    },
    Named {
        name_kind: NamedSelectorKind,
        name: String,
    },
    StructuralPath {
        path: StructuralPath,
        expected_fingerprint_sha256: [u8; 32],
    },
    TextContext {
        query: String,
        before: Option<TextContextAnchor>,
        after: Option<TextContextAnchor>,
    },
}

impl Selector {
    #[must_use]
    pub fn by_logical_id(node_id: LogicalId) -> Self {
        Self::LogicalId { node_id }
    }

    /// Creates an exact, case-sensitive NFC-normalized named selector.
    ///
    /// # Errors
    ///
    /// Rejects empty, control-character or oversized names.
    pub fn by_name(
        name_kind: NamedSelectorKind,
        name: impl AsRef<str>,
    ) -> Result<Self, SelectorError> {
        let name = normalize_selector_text(name.as_ref(), HARD_MAX_NAME_BYTES)?;
        Ok(Self::Named { name_kind, name })
    }

    #[must_use]
    pub fn by_structural_path(path: StructuralPath, expected_fingerprint_sha256: [u8; 32]) -> Self {
        Self::StructuralPath {
            path,
            expected_fingerprint_sha256,
        }
    }

    /// Creates an exact NFC text selector anchored by neighboring context hashes.
    ///
    /// # Errors
    ///
    /// Rejects empty/oversized query text or a selector without either context anchor.
    pub fn by_text_context(
        query: impl AsRef<str>,
        before: Option<TextContextAnchor>,
        after: Option<TextContextAnchor>,
    ) -> Result<Self, SelectorError> {
        if before.is_none() && after.is_none() {
            return Err(SelectorError::InvalidSelector);
        }
        let query = normalize_selector_text(query.as_ref(), HARD_MAX_QUERY_BYTES)?;
        Ok(Self::TextContext {
            query,
            before,
            after,
        })
    }
}

impl fmt::Debug for Selector {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::LogicalId { .. } => "Selector::LogicalId(<redacted>)",
            Self::Named { .. } => "Selector::Named(<redacted>)",
            Self::StructuralPath { .. } => "Selector::StructuralPath(<redacted>)",
            Self::TextContext { .. } => "Selector::TextContext(<redacted>)",
        })
    }
}

#[derive(Clone, Eq, PartialEq)]
pub struct SelectorExpectation {
    revision_id: RevisionId,
    graph_sha256: [u8; 32],
}

impl SelectorExpectation {
    #[must_use]
    pub fn new(revision_id: RevisionId, graph_sha256: [u8; 32]) -> Self {
        Self {
            revision_id,
            graph_sha256,
        }
    }
}

impl fmt::Debug for SelectorExpectation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("SelectorExpectation(<redacted>)")
    }
}

#[derive(Clone, Copy, Eq, PartialEq, Serialize)]
pub struct TextRange {
    start_scalar: u64,
    end_scalar: u64,
}

impl TextRange {
    #[must_use]
    pub const fn start_scalar(self) -> u64 {
        self.start_scalar
    }

    #[must_use]
    pub const fn end_scalar(self) -> u64 {
        self.end_scalar
    }
}

impl fmt::Debug for TextRange {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("TextRange(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ResolvedTarget {
    node_id: LogicalId,
    node_kind: NodeKind,
    structural_path: StructuralPath,
    text_range: Option<TextRange>,
    node_fingerprint_sha256: [u8; 32],
}

impl ResolvedTarget {
    #[must_use]
    pub const fn node_id(&self) -> &LogicalId {
        &self.node_id
    }

    #[must_use]
    pub const fn node_kind(&self) -> NodeKind {
        self.node_kind
    }

    #[must_use]
    pub const fn structural_path(&self) -> &StructuralPath {
        &self.structural_path
    }

    #[must_use]
    pub const fn text_range(&self) -> Option<TextRange> {
        self.text_range
    }

    #[must_use]
    pub const fn node_fingerprint_sha256(&self) -> [u8; 32] {
        self.node_fingerprint_sha256
    }
}

impl fmt::Debug for ResolvedTarget {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("ResolvedTarget(<redacted>)")
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum SelectorError {
    #[error("selector limit is invalid")]
    InvalidLimit,
    #[error("selector is invalid")]
    InvalidSelector,
    #[error("selector snapshot limit exceeded")]
    LimitExceeded,
    #[error("selector metadata is invalid")]
    InvalidGraphMetadata,
    #[error("selector snapshot serialization failed")]
    SerializationFailed,
    #[error("selector snapshot is stale")]
    Stale,
    #[error("selector did not match a target")]
    NotFound,
    #[error("selector matched multiple targets")]
    Ambiguous,
}

impl SelectorError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "selector_invalid_limit",
            Self::InvalidSelector => "selector_invalid",
            Self::LimitExceeded => "selector_limit_exceeded",
            Self::InvalidGraphMetadata => "selector_invalid_graph_metadata",
            Self::SerializationFailed => "selector_serialization_failed",
            Self::Stale => "selector_stale",
            Self::NotFound => "selector_not_found",
            Self::Ambiguous => "selector_ambiguous",
        }
    }
}

struct NodeRecord {
    node_id: LogicalId,
    node_kind: NodeKind,
    path: StructuralPath,
    fingerprint_sha256: [u8; 32],
    text: Option<String>,
}

#[derive(Default)]
struct ReferenceName {
    field: Option<String>,
    bookmark: Option<String>,
}

pub struct SelectorSnapshot {
    revision_id: RevisionId,
    graph_sha256: [u8; 32],
    limits: SelectorLimits,
    records: Vec<NodeRecord>,
    by_id: BTreeMap<LogicalId, usize>,
    by_path: BTreeMap<StructuralPath, usize>,
    by_name: BTreeMap<(NamedSelectorKind, String), BTreeSet<usize>>,
}

impl SelectorSnapshot {
    /// Builds an immutable, bounded selector index from a validated graph revision.
    ///
    /// # Errors
    ///
    /// Fails on invalid limits, reserved selector metadata, serialization failure or index bounds.
    pub fn build(
        graph: &DocumentGraph,
        revision_id: RevisionId,
        limits: SelectorLimits,
    ) -> Result<Self, SelectorError> {
        limits.validate()?;
        let graph_sha256 = graph
            .canonical_sha256()
            .map_err(|_| SelectorError::SerializationFailed)?;
        let reference_names = collect_reference_names(graph.draft(), limits)?;
        let mut snapshot = Self {
            revision_id,
            graph_sha256,
            limits,
            records: Vec::new(),
            by_id: BTreeMap::new(),
            by_path: BTreeMap::new(),
            by_name: BTreeMap::new(),
        };

        let mut indexed_text_bytes = 0_usize;
        for (section_index, section) in graph.sections().iter().enumerate() {
            let section_index =
                u32::try_from(section_index).map_err(|_| SelectorError::LimitExceeded)?;
            snapshot.index_flow(
                &section.body,
                StructuralRoot::Section {
                    index: section_index,
                },
                &mut Vec::new(),
                &reference_names,
                &mut indexed_text_bytes,
            )?;
        }
        for (note_index, note) in graph.draft().notes.iter().enumerate() {
            let note_index = u32::try_from(note_index).map_err(|_| SelectorError::LimitExceeded)?;
            snapshot.index_flow(
                &note.body,
                StructuralRoot::Note { index: note_index },
                &mut Vec::new(),
                &reference_names,
                &mut indexed_text_bytes,
            )?;
        }
        snapshot.index_reference_targets(graph.draft(), &reference_names)?;
        Ok(snapshot)
    }

    #[must_use]
    pub fn expectation(&self) -> SelectorExpectation {
        SelectorExpectation::new(self.revision_id.clone(), self.graph_sha256)
    }

    /// Resolves exactly one target from the pinned snapshot.
    ///
    /// # Errors
    ///
    /// Returns `Stale` before lookup if the revision/digest changed, then fails closed on zero,
    /// multiple or excessive candidates.
    pub fn resolve_one(
        &self,
        expectation: &SelectorExpectation,
        selector: &Selector,
    ) -> Result<ResolvedTarget, SelectorError> {
        if expectation.revision_id != self.revision_id
            || expectation.graph_sha256 != self.graph_sha256
        {
            return Err(SelectorError::Stale);
        }

        let (candidates, stale_hint) = match selector {
            Selector::LogicalId { node_id } => (
                self.by_id
                    .get(node_id)
                    .copied()
                    .map_or_else(Vec::new, |index| vec![self.target(index, None)]),
                false,
            ),
            Selector::Named { name_kind, name } => {
                validate_selector_text(name, self.limits.max_name_bytes)?;
                let candidates =
                    if let Some(indices) = self.by_name.get(&(*name_kind, name.clone())) {
                        if indices.len() > self.limits.max_candidates {
                            return Err(SelectorError::LimitExceeded);
                        }
                        indices
                            .iter()
                            .map(|index| self.target(*index, None))
                            .collect()
                    } else {
                        Vec::new()
                    };
                (candidates, false)
            }
            Selector::StructuralPath {
                path,
                expected_fingerprint_sha256,
            } => {
                if path.steps.is_empty() || path.steps.len() > self.limits.max_path_steps {
                    return Err(SelectorError::InvalidSelector);
                }
                let Some(index) = self.by_path.get(path).copied() else {
                    return Err(SelectorError::Stale);
                };
                if &self.records[index].fingerprint_sha256 != expected_fingerprint_sha256 {
                    return Err(SelectorError::Stale);
                }
                (vec![self.target(index, None)], false)
            }
            Selector::TextContext {
                query,
                before,
                after,
            } => self.resolve_text(query, before.as_ref(), after.as_ref())?,
        };

        if candidates.len() > self.limits.max_candidates {
            return Err(SelectorError::LimitExceeded);
        }
        match candidates.len() {
            0 if stale_hint => Err(SelectorError::Stale),
            0 => Err(SelectorError::NotFound),
            1 => candidates.into_iter().next().ok_or(SelectorError::NotFound),
            _ => Err(SelectorError::Ambiguous),
        }
    }

    /// Returns the canonical node fingerprint needed by a structural selector.
    ///
    /// # Errors
    ///
    /// Returns `NotFound` for an unknown logical node ID.
    pub fn fingerprint_for(&self, node_id: &LogicalId) -> Result<[u8; 32], SelectorError> {
        self.by_id
            .get(node_id)
            .map(|index| self.records[*index].fingerprint_sha256)
            .ok_or(SelectorError::NotFound)
    }

    /// Returns the deterministic structural path for an indexed logical node.
    ///
    /// # Errors
    ///
    /// Returns `NotFound` for an unknown logical node ID.
    pub fn structural_path_for(
        &self,
        node_id: &LogicalId,
    ) -> Result<StructuralPath, SelectorError> {
        self.by_id
            .get(node_id)
            .map(|index| self.records[*index].path.clone())
            .ok_or(SelectorError::NotFound)
    }

    fn index_flow(
        &mut self,
        flow: &Flow,
        root: StructuralRoot,
        prefix: &mut Vec<StructuralStep>,
        reference_names: &BTreeMap<LogicalId, ReferenceName>,
        indexed_text_bytes: &mut usize,
    ) -> Result<(), SelectorError> {
        for (index, node) in flow.children.iter().enumerate() {
            let index = u32::try_from(index).map_err(|_| SelectorError::LimitExceeded)?;
            prefix.push(StructuralStep::FlowChild {
                index,
                expected_kind: NodeKind::of(node),
            });
            let path = StructuralPath::from_root(root, prefix.clone())?;
            let record_index = self.add_node(node, path, indexed_text_bytes)?;
            self.index_node_names(node, record_index, reference_names)?;

            match node {
                Node::Table(table) => {
                    for cell in &table.cells {
                        prefix.push(StructuralStep::TableCell {
                            row: cell.row,
                            column: cell.column,
                        });
                        self.index_flow(
                            &cell.body,
                            root,
                            prefix,
                            reference_names,
                            indexed_text_bytes,
                        )?;
                        let _ = prefix.pop();
                    }
                }
                Node::Drawing(drawing) => self.index_flow(
                    &drawing.children,
                    root,
                    prefix,
                    reference_names,
                    indexed_text_bytes,
                )?,
                Node::Paragraph(_)
                | Node::Equation(_)
                | Node::Chart(_)
                | Node::Field(_)
                | Node::FormControl(_)
                | Node::Break(_)
                | Node::EmbeddedObject(_) => {}
            }
            let _ = prefix.pop();
        }
        Ok(())
    }

    fn add_node(
        &mut self,
        node: &Node,
        path: StructuralPath,
        indexed_text_bytes: &mut usize,
    ) -> Result<usize, SelectorError> {
        if self.records.len() >= self.limits.max_indexed_nodes {
            return Err(SelectorError::LimitExceeded);
        }
        let text = match node {
            Node::Paragraph(paragraph) => {
                let mut text = String::new();
                append_inline_text(&paragraph.inlines, &mut text);
                let text = normalize(&text);
                *indexed_text_bytes = indexed_text_bytes
                    .checked_add(text.len())
                    .ok_or(SelectorError::LimitExceeded)?;
                if *indexed_text_bytes > self.limits.max_indexed_text_bytes {
                    return Err(SelectorError::LimitExceeded);
                }
                Some(text)
            }
            _ => None,
        };
        let fingerprint_sha256 = fingerprint(node)?;
        let record_index = self.records.len();
        let record = NodeRecord {
            node_id: node.common().node_id.clone(),
            node_kind: NodeKind::of(node),
            path: path.clone(),
            fingerprint_sha256,
            text,
        };
        if self
            .by_id
            .insert(record.node_id.clone(), record_index)
            .is_some()
            || self.by_path.insert(path, record_index).is_some()
        {
            return Err(SelectorError::InvalidGraphMetadata);
        }
        self.records.push(record);
        Ok(record_index)
    }

    fn index_node_names(
        &mut self,
        node: &Node,
        record_index: usize,
        reference_names: &BTreeMap<LogicalId, ReferenceName>,
    ) -> Result<(), SelectorError> {
        if let Some(slot) = reserved_name(&node.common().semantics, "slot_name", self.limits)? {
            self.add_name(NamedSelectorKind::Slot, slot, record_index);
        }
        match node {
            Node::Field(field) => {
                let local = reserved_name(&field.properties, "field_name", self.limits)?;
                let referenced = reference_names
                    .get(&field.reference_id)
                    .and_then(|names| names.field.clone());
                if let (Some(left), Some(right)) = (&local, &referenced)
                    && left != right
                {
                    return Err(SelectorError::InvalidGraphMetadata);
                }
                if let Some(name) = local.or(referenced) {
                    self.add_name(NamedSelectorKind::Field, name, record_index);
                }
            }
            Node::Paragraph(paragraph) => {
                let mut bookmark_refs = BTreeSet::new();
                collect_bookmark_references(&paragraph.inlines, &mut bookmark_refs);
                for reference_id in bookmark_refs {
                    if let Some(name) = reference_names
                        .get(reference_id)
                        .and_then(|names| names.bookmark.clone())
                    {
                        self.add_name(NamedSelectorKind::Bookmark, name, record_index);
                    }
                }
            }
            Node::Table(_)
            | Node::Equation(_)
            | Node::Drawing(_)
            | Node::Chart(_)
            | Node::FormControl(_)
            | Node::Break(_)
            | Node::EmbeddedObject(_) => {}
        }
        Ok(())
    }

    fn index_reference_targets(
        &mut self,
        draft: &DocumentGraphDraft,
        reference_names: &BTreeMap<LogicalId, ReferenceName>,
    ) -> Result<(), SelectorError> {
        for reference in &draft.references {
            let Some(target) = &reference.target_node_id else {
                continue;
            };
            let Some(record_index) = self.by_id.get(target).copied() else {
                return Err(SelectorError::InvalidGraphMetadata);
            };
            if let Some(name) = reference_names
                .get(&reference.reference_id)
                .and_then(|names| names.bookmark.clone())
            {
                self.add_name(NamedSelectorKind::Bookmark, name, record_index);
            }
        }
        Ok(())
    }

    fn add_name(&mut self, kind: NamedSelectorKind, name: String, record_index: usize) {
        let _ = self
            .by_name
            .entry((kind, name))
            .or_default()
            .insert(record_index);
    }

    fn resolve_text(
        &self,
        query: &str,
        before: Option<&TextContextAnchor>,
        after: Option<&TextContextAnchor>,
    ) -> Result<(Vec<ResolvedTarget>, bool), SelectorError> {
        validate_selector_text(query, self.limits.max_query_bytes)?;
        if before.is_none() && after.is_none() {
            return Err(SelectorError::InvalidSelector);
        }
        for anchor in before.into_iter().chain(after) {
            if anchor.scalar_count == 0
                || usize::try_from(anchor.scalar_count)
                    .map_err(|_| SelectorError::InvalidSelector)?
                    > self.limits.max_context_scalars
            {
                return Err(SelectorError::InvalidSelector);
            }
        }

        let mut candidates = Vec::new();
        let mut query_seen = false;
        for (record_index, record) in self.records.iter().enumerate() {
            let Some(text) = &record.text else {
                continue;
            };
            for byte_start in overlapping_match_indices(text, query) {
                query_seen = true;
                let byte_end = byte_start
                    .checked_add(query.len())
                    .ok_or(SelectorError::LimitExceeded)?;
                if !context_matches(&text[..byte_start], before, true)
                    || !context_matches(&text[byte_end..], after, false)
                {
                    continue;
                }
                let start_scalar = u64::try_from(text[..byte_start].chars().count())
                    .map_err(|_| SelectorError::LimitExceeded)?;
                let query_scalars = u64::try_from(query.chars().count())
                    .map_err(|_| SelectorError::LimitExceeded)?;
                let end_scalar = start_scalar
                    .checked_add(query_scalars)
                    .ok_or(SelectorError::LimitExceeded)?;
                candidates.push(self.target(
                    record_index,
                    Some(TextRange {
                        start_scalar,
                        end_scalar,
                    }),
                ));
                if candidates.len() > self.limits.max_candidates {
                    return Err(SelectorError::LimitExceeded);
                }
            }
        }
        Ok((candidates, query_seen))
    }

    fn target(&self, index: usize, text_range: Option<TextRange>) -> ResolvedTarget {
        let record = &self.records[index];
        ResolvedTarget {
            node_id: record.node_id.clone(),
            node_kind: record.node_kind,
            structural_path: record.path.clone(),
            text_range,
            node_fingerprint_sha256: record.fingerprint_sha256,
        }
    }
}

impl fmt::Debug for SelectorSnapshot {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SelectorSnapshot")
            .field("node_count", &self.records.len())
            .finish_non_exhaustive()
    }
}

fn collect_reference_names(
    draft: &DocumentGraphDraft,
    limits: SelectorLimits,
) -> Result<BTreeMap<LogicalId, ReferenceName>, SelectorError> {
    let mut names = BTreeMap::new();
    for reference in &draft.references {
        let field = reserved_name(&reference.properties, "field_name", limits)?;
        let bookmark = reserved_name(&reference.properties, "bookmark_name", limits)?;
        let _ = names.insert(
            reference.reference_id.clone(),
            ReferenceName { field, bookmark },
        );
    }
    Ok(names)
}

fn reserved_name(
    properties: &Properties,
    key: &str,
    limits: SelectorLimits,
) -> Result<Option<String>, SelectorError> {
    let value = properties
        .iter()
        .find_map(|(candidate, value)| (candidate == key).then_some(value));
    let Some(value) = value else {
        return Ok(None);
    };
    let PropertyValue::Text(value) = value else {
        return Err(SelectorError::InvalidGraphMetadata);
    };
    let normalized = normalize(value);
    validate_selector_text(&normalized, limits.max_name_bytes)
        .map_err(|_| SelectorError::InvalidGraphMetadata)?;
    Ok(Some(normalized))
}

fn collect_bookmark_references<'a>(inlines: &'a [Inline], output: &mut BTreeSet<&'a LogicalId>) {
    for inline in inlines {
        match inline {
            Inline::BookmarkAnchor { reference_id } => {
                let _ = output.insert(reference_id);
            }
            Inline::ChangeSpan { children, .. } => collect_bookmark_references(children, output),
            Inline::Text { .. }
            | Inline::InlineEquation { .. }
            | Inline::Tab
            | Inline::LineBreak
            | Inline::FieldRef { .. }
            | Inline::ControlRef { .. } => {}
        }
    }
}

fn append_inline_text(inlines: &[Inline], output: &mut String) {
    for inline in inlines {
        match inline {
            Inline::Text { text } => output.push_str(text),
            Inline::Tab => output.push('\t'),
            Inline::LineBreak => output.push('\n'),
            Inline::ChangeSpan { children, .. } => append_inline_text(children, output),
            Inline::InlineEquation { .. }
            | Inline::FieldRef { .. }
            | Inline::BookmarkAnchor { .. }
            | Inline::ControlRef { .. } => output.push('\u{fffc}'),
        }
    }
}

fn normalize(value: &str) -> String {
    value.nfc().collect()
}

fn normalize_selector_text(value: &str, max_bytes: usize) -> Result<String, SelectorError> {
    let normalized = normalize(value);
    validate_selector_text(&normalized, max_bytes)?;
    Ok(normalized)
}

fn validate_selector_text(value: &str, max_bytes: usize) -> Result<(), SelectorError> {
    if value.is_empty() || value.len() > max_bytes || value.chars().any(char::is_control) {
        return Err(SelectorError::InvalidSelector);
    }
    Ok(())
}

fn fingerprint(node: &Node) -> Result<[u8; 32], SelectorError> {
    let bytes = serde_json::to_vec(node).map_err(|_| SelectorError::SerializationFailed)?;
    Ok(Sha256::digest(bytes).into())
}

fn overlapping_match_indices<'a>(
    text: &'a str,
    query: &'a str,
) -> impl Iterator<Item = usize> + 'a {
    text.char_indices()
        .filter_map(move |(index, _)| text[index..].starts_with(query).then_some(index))
}

fn context_matches(context: &str, anchor: Option<&TextContextAnchor>, take_suffix: bool) -> bool {
    let Some(anchor) = anchor else {
        return true;
    };
    let Ok(count) = usize::try_from(anchor.scalar_count) else {
        return false;
    };
    let selected = if take_suffix {
        suffix_chars(context, count)
    } else {
        prefix_chars(context, count)
    };
    selected
        .is_some_and(|value| <[u8; 32]>::from(Sha256::digest(value.as_bytes())) == anchor.sha256)
}

fn suffix_chars(value: &str, count: usize) -> Option<&str> {
    if count == 0 {
        return Some("");
    }
    let mut indices = value.char_indices().rev();
    let (start, _) = indices.nth(count.checked_sub(1)?)?;
    Some(&value[start..])
}

fn prefix_chars(value: &str, count: usize) -> Option<&str> {
    if count == 0 {
        return Some("");
    }
    let mut indices = value.char_indices();
    let _ = indices.nth(count.checked_sub(1)?)?;
    let end = indices.next().map_or(value.len(), |(index, _)| index);
    Some(&value[..end])
}
