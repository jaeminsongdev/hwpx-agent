//! Source-bound, content-free summaries of real semantic-diff records.
//!
//! Counts describe semantic records, not unique objects or user operations. A table can have
//! separate node, table and cell records. Moves count once as modified. This projection supplies
//! the plan-review `diff` field; it does not grant access, verify a dry run or authorize execution.

use std::collections::BTreeMap;
use std::fmt;
use std::io::{self, Write};

use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::semantic_diff::subject_ref;
use crate::{
    BreakKind, ChangeKind, DocumentGraph, EntityKind, Node, ResourceKind, SemanticChange,
    SemanticDiff,
};

const MAX_CHANGES: usize = 100_000;
const MAX_INDEX_ENTRIES: usize = 200_000;
const MAX_DEPTH: usize = 128;
const MAX_SERIALIZED_BYTES: usize = 64 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SemanticSummaryLimits {
    pub max_changes: usize,
    /// Limit per source graph, including resource and specialized-node classification entries.
    pub max_index_entries: usize,
    pub max_depth: usize,
    /// Applied independently to each graph and to the semantic diff, with streaming hashing.
    pub max_serialized_bytes: usize,
}

impl Default for SemanticSummaryLimits {
    fn default() -> Self {
        Self {
            max_changes: MAX_CHANGES,
            max_index_entries: MAX_INDEX_ENTRIES,
            max_depth: MAX_DEPTH,
            max_serialized_bytes: MAX_SERIALIZED_BYTES,
        }
    }
}

impl SemanticSummaryLimits {
    fn validate(self) -> Result<(), SemanticSummaryError> {
        if !(1..=MAX_CHANGES).contains(&self.max_changes)
            || !(1..=MAX_INDEX_ENTRIES).contains(&self.max_index_entries)
            || !(1..=MAX_DEPTH).contains(&self.max_depth)
            || !(1..=MAX_SERIALIZED_BYTES).contains(&self.max_serialized_bytes)
        {
            return Err(SemanticSummaryError::InvalidLimit);
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SemanticSummaryKind {
    Paragraph,
    Table,
    Style,
    Image,
    Field,
    Section,
    Metadata,
    Other,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct SemanticSummaryCategory {
    kind: SemanticSummaryKind,
    count: u32,
}

impl SemanticSummaryCategory {
    #[must_use]
    pub const fn kind(&self) -> SemanticSummaryKind {
        self.kind
    }
    #[must_use]
    pub const fn count(&self) -> u32 {
        self.count
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct SemanticDiffSummary {
    added: u32,
    modified: u32,
    removed: u32,
    categories: Vec<SemanticSummaryCategory>,
    #[serde(skip)]
    source_diff_sha256: [u8; 32],
    #[serde(skip)]
    before_graph_sha256: [u8; 32],
    #[serde(skip)]
    after_graph_sha256: [u8; 32],
}

impl fmt::Debug for SemanticDiffSummary {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SemanticDiffSummary")
            .field("added", &self.added)
            .field("modified", &self.modified)
            .field("removed", &self.removed)
            .field("categories", &self.categories)
            .finish_non_exhaustive()
    }
}

impl SemanticDiffSummary {
    /// Projects immutable diff records only after verifying both exact source graphs.
    ///
    /// # Errors
    /// Rejects mismatched graphs, invalid/oversized inputs and missing or ambiguous source indexes.
    /// Counts are never truncated or clamped to fit the consumer. Callers must separately authorize
    /// the project/revisions and bind this evidence to the compiled plan before publishing it.
    pub fn from_diff(
        diff: &SemanticDiff,
        before: &DocumentGraph,
        after: &DocumentGraph,
        limits: SemanticSummaryLimits,
    ) -> Result<Self, SemanticSummaryError> {
        limits.validate()?;
        if diff.changes().len() > limits.max_changes {
            return Err(SemanticSummaryError::LimitExceeded);
        }
        let before_digest = bounded_digest(before, limits.max_serialized_bytes)?;
        let after_digest = bounded_digest(after, limits.max_serialized_bytes)?;
        if before_digest != diff.before_graph_sha256() || after_digest != diff.after_graph_sha256()
        {
            return Err(SemanticSummaryError::GraphMismatch);
        }
        let source_diff_sha256 = bounded_digest(diff, limits.max_serialized_bytes)?;
        let before_index = ClassificationIndex::new(before, limits)?;
        let after_index = ClassificationIndex::new(after, limits)?;
        let mut summary = Self {
            added: 0,
            modified: 0,
            removed: 0,
            categories: vec![],
            source_diff_sha256,
            before_graph_sha256: before_digest,
            after_graph_sha256: after_digest,
        };
        let mut categories = BTreeMap::<SemanticSummaryKind, u32>::new();
        for change in diff.changes() {
            match change.change_kind() {
                ChangeKind::Added => summary.added += 1,
                ChangeKind::Removed => summary.removed += 1,
                ChangeKind::Modified | ChangeKind::Moved | ChangeKind::ModifiedAndMoved => {
                    summary.modified += 1;
                }
            }
            let kind = classify(change, &before_index, &after_index)?;
            *categories.entry(kind).or_default() += 1;
        }
        summary.categories = categories
            .into_iter()
            .map(|(kind, count)| SemanticSummaryCategory { kind, count })
            .collect();
        Ok(summary)
    }

    #[must_use]
    pub const fn source_diff_sha256(&self) -> [u8; 32] {
        self.source_diff_sha256
    }
    #[must_use]
    pub const fn before_graph_sha256(&self) -> [u8; 32] {
        self.before_graph_sha256
    }
    #[must_use]
    pub const fn after_graph_sha256(&self) -> [u8; 32] {
        self.after_graph_sha256
    }
    #[must_use]
    pub const fn added(&self) -> u32 {
        self.added
    }
    #[must_use]
    pub const fn modified(&self) -> u32 {
        self.modified
    }
    #[must_use]
    pub const fn removed(&self) -> u32 {
        self.removed
    }
    #[must_use]
    pub fn categories(&self) -> &[SemanticSummaryCategory] {
        &self.categories
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum SemanticSummaryError {
    #[error("semantic-summary limit is invalid")]
    InvalidLimit,
    #[error("semantic-summary input exceeds its finite limit")]
    LimitExceeded,
    #[error("semantic-summary source graph does not match the diff")]
    GraphMismatch,
    #[error("semantic-summary source classification is missing or ambiguous")]
    InvalidSourceIndex,
    #[error("semantic-summary source serialization failed")]
    SerializationFailed,
}

impl SemanticSummaryError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "semantic_summary_invalid_limit",
            Self::LimitExceeded => "semantic_summary_limit_exceeded",
            Self::GraphMismatch => "semantic_summary_graph_mismatch",
            Self::InvalidSourceIndex => "semantic_summary_invalid_source_index",
            Self::SerializationFailed => "semantic_summary_serialization_failed",
        }
    }
}

struct ClassificationIndex {
    by_reference: BTreeMap<[u8; 32], SemanticSummaryKind>,
    limits: SemanticSummaryLimits,
}

impl ClassificationIndex {
    fn new(
        graph: &DocumentGraph,
        limits: SemanticSummaryLimits,
    ) -> Result<Self, SemanticSummaryError> {
        let mut index = Self {
            by_reference: BTreeMap::new(),
            limits,
        };
        for resource in &graph.draft().resources {
            let kind = if resource.kind == ResourceKind::Image {
                SemanticSummaryKind::Image
            } else {
                SemanticSummaryKind::Other
            };
            index.insert(EntityKind::Resource, resource.resource_id.as_str(), kind)?;
        }
        for section in &graph.draft().sections {
            index.add_nodes(&section.body.children, 1)?;
        }
        for note in &graph.draft().notes {
            index.add_nodes(&note.body.children, 1)?;
        }
        Ok(index)
    }

    fn insert(
        &mut self,
        entity: EntityKind,
        id: &str,
        kind: SemanticSummaryKind,
    ) -> Result<(), SemanticSummaryError> {
        if self.by_reference.len() >= self.limits.max_index_entries {
            return Err(SemanticSummaryError::LimitExceeded);
        }
        if self
            .by_reference
            .insert(subject_ref(entity, id), kind)
            .is_some()
        {
            return Err(SemanticSummaryError::InvalidSourceIndex);
        }
        Ok(())
    }

    fn add_nodes(&mut self, nodes: &[Node], depth: usize) -> Result<(), SemanticSummaryError> {
        if depth > self.limits.max_depth {
            return Err(SemanticSummaryError::LimitExceeded);
        }
        for node in nodes {
            let kind = match node {
                Node::Paragraph(_) => SemanticSummaryKind::Paragraph,
                Node::Table(_) => SemanticSummaryKind::Table,
                Node::Field(_) | Node::FormControl(_) => SemanticSummaryKind::Field,
                Node::Break(value) if value.break_kind == BreakKind::Section => {
                    SemanticSummaryKind::Section
                }
                Node::Drawing(value) => match &value.resource_id {
                    Some(id) => *self
                        .by_reference
                        .get(&subject_ref(EntityKind::Resource, id.as_str()))
                        .ok_or(SemanticSummaryError::InvalidSourceIndex)?,
                    None => SemanticSummaryKind::Other,
                },
                Node::Break(_) | Node::Equation(_) | Node::Chart(_) | Node::EmbeddedObject(_) => {
                    SemanticSummaryKind::Other
                }
            };
            self.insert(EntityKind::Node, node.common().node_id.as_str(), kind)?;
            match node {
                Node::Table(table) => {
                    for cell in &table.cells {
                        self.add_nodes(&cell.body.children, depth + 1)?;
                    }
                }
                Node::Drawing(drawing) => {
                    self.insert(EntityKind::Drawing, node.common().node_id.as_str(), kind)?;
                    self.add_nodes(&drawing.children.children, depth + 1)?;
                }
                Node::Break(_) => {
                    self.insert(EntityKind::Break, node.common().node_id.as_str(), kind)?;
                }
                _ => {}
            }
        }
        Ok(())
    }
}

fn classify(
    change: &SemanticChange,
    before: &ClassificationIndex,
    after: &ClassificationIndex,
) -> Result<SemanticSummaryKind, SemanticSummaryError> {
    Ok(match change.entity_kind() {
        EntityKind::Node | EntityKind::Resource | EntityKind::Drawing | EntityKind::Break => {
            let key = change.subject_ref_sha256();
            let left = before.by_reference.get(&key).copied();
            let right = after.by_reference.get(&key).copied();
            match change.change_kind() {
                ChangeKind::Added => right.ok_or(SemanticSummaryError::InvalidSourceIndex)?,
                ChangeKind::Removed => left.ok_or(SemanticSummaryError::InvalidSourceIndex)?,
                ChangeKind::Modified | ChangeKind::Moved | ChangeKind::ModifiedAndMoved => {
                    let left = left.ok_or(SemanticSummaryError::InvalidSourceIndex)?;
                    let right = right.ok_or(SemanticSummaryError::InvalidSourceIndex)?;
                    if left == right {
                        left
                    } else {
                        SemanticSummaryKind::Other
                    }
                }
            }
        }
        EntityKind::Table | EntityKind::TableCell => SemanticSummaryKind::Table,
        EntityKind::Style => SemanticSummaryKind::Style,
        EntityKind::Section => SemanticSummaryKind::Section,
        EntityKind::Field | EntityKind::FormControl => SemanticSummaryKind::Field,
        EntityKind::Document | EntityKind::Note | EntityKind::Reference | EntityKind::Review => {
            SemanticSummaryKind::Metadata
        }
        EntityKind::Equation
        | EntityKind::Chart
        | EntityKind::EmbeddedObject
        | EntityKind::OpaqueExtension => SemanticSummaryKind::Other,
    })
}

struct DigestWriter {
    hasher: Sha256,
    bytes: usize,
    maximum: usize,
    exceeded: bool,
}

impl Write for DigestWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let Some(total) = self
            .bytes
            .checked_add(bytes.len())
            .filter(|total| *total <= self.maximum)
        else {
            self.exceeded = true;
            return Err(io::Error::other(
                "semantic-summary serialization bound exceeded",
            ));
        };
        self.hasher.update(bytes);
        self.bytes = total;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

fn bounded_digest(
    value: &impl Serialize,
    maximum: usize,
) -> Result<[u8; 32], SemanticSummaryError> {
    let mut writer = DigestWriter {
        hasher: Sha256::new(),
        bytes: 0,
        maximum,
        exceeded: false,
    };
    if serde_json::to_writer(&mut writer, value).is_err() {
        return Err(if writer.exceeded {
            SemanticSummaryError::LimitExceeded
        } else {
            SemanticSummaryError::SerializationFailed
        });
    }
    Ok(writer.hasher.finalize().into())
}
