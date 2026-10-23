//! Exact original XML/IR positions, NOT Hangul caret/visual coordinates or complete comment state.
use super::{ImportedDocumentReviewBodies, ReviewBodyKind, bounded_digest};
use crate::document_import::{ImportedSourcePackage, ImportedSourcePart};
use domain_ir::{CommentAnchor, CommentPoint, Flow, Inline, LogicalId, Node, SourceAnchorHandle};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
};
use thiserror::Error;

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ReviewSourcePoint {
    pub source_part: SourceAnchorHandle,
    pub paragraph_anchor: SourceAnchorHandle,
    pub run_anchor: SourceAnchorHandle,
    pub item_anchor: SourceAnchorHandle,
    /// Complete root-to-container XML ancestry; never flattened across nested flow scopes.
    pub container_path: Vec<SourceAnchorHandle>,
    /// Zero-based sibling paragraph/run/item ordinals, NOT native character offsets.
    pub point: CommentPoint,
}
impl fmt::Debug for ReviewSourcePoint {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewSourcePoint(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ReviewSourceLocation {
    pub review_id: LogicalId,
    pub target_node_id: LogicalId,
    pub kind: ReviewBodyKind,
    pub paragraph_node_id: LogicalId,
    pub start: ReviewSourcePoint,
    pub end: ReviewSourcePoint,
    /// Original simple typed anchor only for direct section-body XML item coordinates.
    /// None for nested flows; no claim of native author/time/state or cursor compatibility.
    pub direct_section_item_anchor: Option<CommentAnchor>,
}
impl fmt::Debug for ReviewSourceLocation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ReviewSourceLocation(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReviewLocationReceipt {
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub original_review_graph_sha256: [u8; 32],
    pub original_observations_sha256: [u8; 32],
    pub locations_sha256: [u8; 32],
    pub locations: usize,
    pub direct_section_item_anchors: usize,
    pub nested_source_paths: usize,
    pub native_caret_or_visual_coordinates_verified: bool,
    pub native_author_time_state_verified: bool,
    pub execution_publication_authority: bool,
}
pub struct ImportedReviewLocations<'a, 'source> {
    review: &'a ImportedDocumentReviewBodies<'source>,
    locations: Vec<ReviewSourceLocation>,
    receipt: ReviewLocationReceipt,
}
impl fmt::Debug for ImportedReviewLocations<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedReviewLocations(<redacted>)")
    }
}
impl<'source> ImportedDocumentReviewBodies<'source> {
    /// Bind exact native XML positions to actual original IR paragraphs and control refs.
    /// No caller positions/XML/metadata, graph rewrite or complete-state admission.
    /// # Errors
    /// Rejects stale source, original paragraph/run/field binding, order or byte budget drift.
    pub fn locate<'a>(
        &'a self,
        fresh: &[u8],
    ) -> Result<ImportedReviewLocations<'a, 'source>, ReviewLocationError> {
        self.verify_source(fresh)
            .map_err(|_| ReviewLocationError::Source)?;
        let mut paragraphs = BTreeMap::new();
        for section in self.graph.sections() {
            index_paragraphs(&section.body, &mut paragraphs)?;
        }
        for note in self.graph.notes() {
            index_paragraphs(&note.body, &mut paragraphs)?;
        }
        let sections: BTreeSet<_> = self
            .graph
            .sections()
            .iter()
            .map(|s| &s.section_id)
            .collect();
        let ordinals = index_ordinals(self.forms.source())?;
        let mut locations = Vec::new();
        locations
            .try_reserve_exact(self.observations.len())
            .map_err(|_| ReviewLocationError::Budget)?;
        let mut budget = super::DigestBudget {
            seen: 0,
            sha: Sha256::new(),
        };
        for observation in &self.observations {
            let start = source_point(self.forms.source(), &observation.marker_anchor, &ordinals)?;
            let end = observation.end_anchor.as_ref().map_or_else(
                || Ok(start.clone()),
                |anchor| source_point(self.forms.source(), anchor, &ordinals),
            )?;
            if start.source_part != end.source_part
                || start.paragraph_anchor != end.paragraph_anchor
                || start.container_path != end.container_path
                || start.point > end.point
            {
                return Err(ReviewLocationError::Binding);
            }
            let paragraph_node_id = super::super::id("node", &start.paragraph_anchor)
                .map_err(|_| ReviewLocationError::Binding)?;
            let binding = paragraphs
                .get(&paragraph_node_id)
                .ok_or(ReviewLocationError::Binding)?;
            if binding.0 != start.paragraph_anchor
                || !binding.1.contains(&observation.target_node_id)
            {
                return Err(ReviewLocationError::Binding);
            }
            let section_id = super::super::id("section", &start.source_part)
                .map_err(|_| ReviewLocationError::Binding)?;
            if !sections.contains(&section_id) {
                return Err(ReviewLocationError::Binding);
            }
            let direct = start.container_path.len() == 1;
            let location = ReviewSourceLocation {
                review_id: observation.review_id.clone(),
                target_node_id: observation.target_node_id.clone(),
                kind: observation.kind,
                paragraph_node_id,
                start: start.clone(),
                end: end.clone(),
                direct_section_item_anchor: direct.then_some(CommentAnchor {
                    section_id,
                    start: start.point,
                    end: end.point,
                }),
            };
            serde_json::to_writer(&mut budget, &location)
                .map_err(|_| ReviewLocationError::Budget)?;
            locations.push(location);
        }
        let direct = locations
            .iter()
            .filter(|v| v.direct_section_item_anchor.is_some())
            .count();
        let receipt = ReviewLocationReceipt {
            qualification: "original_source_XML_item_positions_bound_to_original_IR_NOT_native_caret_visual_author_time_state_protection_compiler_execution_or_Gate",
            source_package_sha256: self.receipt.source_package_sha256,
            original_review_graph_sha256: self.receipt.graph_sha256,
            original_observations_sha256: self.receipt.body_observations_sha256,
            locations_sha256: bounded_digest(&locations)
                .map_err(|_| ReviewLocationError::Budget)?,
            locations: locations.len(),
            direct_section_item_anchors: direct,
            nested_source_paths: locations.len() - direct,
            native_caret_or_visual_coordinates_verified: false,
            native_author_time_state_verified: false,
            execution_publication_authority: false,
        };
        self.verify_source(fresh)
            .map_err(|_| ReviewLocationError::Source)?;
        Ok(ImportedReviewLocations {
            review: self,
            locations,
            receipt,
        })
    }
}
impl ImportedReviewLocations<'_, '_> {
    #[must_use]
    pub fn locations(&self) -> &[ReviewSourceLocation] {
        &self.locations
    }
    #[must_use]
    pub const fn receipt(&self) -> &ReviewLocationReceipt {
        &self.receipt
    }
    /// Rebuild the entire original review/source mapping; no partial positional rebind.
    /// # Errors
    /// Rejects fresh source or cached full locations/receipt drift.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<ReviewLocationReceipt, ReviewLocationError> {
        let rebuilt = self.review.locate(fresh)?;
        if rebuilt.locations != self.locations || rebuilt.receipt != self.receipt {
            return Err(ReviewLocationError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
type ParagraphBindings = BTreeMap<LogicalId, (SourceAnchorHandle, BTreeSet<LogicalId>)>;
fn index_paragraphs(flow: &Flow, out: &mut ParagraphBindings) -> Result<(), ReviewLocationError> {
    for node in &flow.children {
        match node {
            Node::Paragraph(p) => {
                let anchor = p
                    .common
                    .source_anchor
                    .as_ref()
                    .ok_or(ReviewLocationError::Binding)?;
                let refs = p
                    .inlines
                    .iter()
                    .filter_map(|i| match i {
                        Inline::ControlRef { node_id } => Some(node_id.clone()),
                        _ => None,
                    })
                    .collect();
                if out
                    .insert(p.common.node_id.clone(), (anchor.clone(), refs))
                    .is_some()
                {
                    return Err(ReviewLocationError::Binding);
                }
            }
            Node::Table(t) => {
                for cell in &t.cells {
                    index_paragraphs(&cell.body, out)?;
                }
            }
            Node::Drawing(d) => index_paragraphs(&d.children, out)?,
            _ => (),
        }
    }
    Ok(())
}
type OrdinalIndex = BTreeMap<LogicalId, Vec<[u32; 3]>>;
fn index_ordinals(source: &ImportedSourcePackage) -> Result<OrdinalIndex, ReviewLocationError> {
    let mut result = BTreeMap::new();
    for part in source.parts() {
        let Some(xml) = part.xml() else {
            continue;
        };
        let mut positions = vec![[0_u32; 3]; xml.elements().len()];
        for parent in xml.elements() {
            let mut next = parent.first_child();
            let mut counts = [0_u32; 3];
            while let Some(child) = next {
                positions[child] = counts;
                counts[0] = counts[0]
                    .checked_add(1)
                    .ok_or(ReviewLocationError::Budget)?;
                if super::named(&xml.elements()[child], "p") {
                    counts[1] = counts[1]
                        .checked_add(1)
                        .ok_or(ReviewLocationError::Budget)?;
                }
                if super::named(&xml.elements()[child], "run") {
                    counts[2] = counts[2]
                        .checked_add(1)
                        .ok_or(ReviewLocationError::Budget)?;
                }
                next = xml.elements()[child].next_sibling();
            }
        }
        if result
            .insert(part.anchor().opaque_handle.clone(), positions)
            .is_some()
        {
            return Err(ReviewLocationError::Binding);
        }
    }
    Ok(result)
}
fn source_point(
    source: &ImportedSourcePackage,
    anchor: &SourceAnchorHandle,
    ordinals: &OrdinalIndex,
) -> Result<ReviewSourcePoint, ReviewLocationError> {
    let resolved = source
        .resolve_anchor(anchor)
        .map_err(|_| ReviewLocationError::Binding)?;
    let part = resolved.part();
    let xml = part.xml().ok_or(ReviewLocationError::Binding)?;
    let marker = resolved
        .element_index()
        .ok_or(ReviewLocationError::Binding)?;
    let parent = xml.elements()[marker]
        .parent()
        .ok_or(ReviewLocationError::Binding)?;
    let item = if super::named(&xml.elements()[parent], "ctrl") {
        parent
    } else {
        marker
    };
    let run = xml.elements()[item]
        .parent()
        .ok_or(ReviewLocationError::Binding)?;
    let paragraph = xml.elements()[run]
        .parent()
        .ok_or(ReviewLocationError::Binding)?;
    if !super::named(&xml.elements()[run], "run") || !super::named(&xml.elements()[paragraph], "p")
    {
        return Err(ReviewLocationError::Binding);
    }
    let mut path = Vec::new();
    let mut current = xml.elements()[paragraph].parent();
    while let Some(index) = current {
        path.push(
            part.element_anchor(index)
                .cloned()
                .ok_or(ReviewLocationError::Binding)?,
        );
        current = xml.elements()[index].parent();
    }
    path.reverse();
    let positions = ordinals
        .get(&part.anchor().opaque_handle)
        .ok_or(ReviewLocationError::Binding)?;
    Ok(ReviewSourcePoint {
        source_part: part.anchor().clone(),
        paragraph_anchor: checked_anchor(part, paragraph)?,
        run_anchor: checked_anchor(part, run)?,
        item_anchor: checked_anchor(part, item)?,
        container_path: path,
        point: CommentPoint {
            paragraph_ordinal: positions[paragraph][1],
            run_ordinal: positions[run][2],
            inline_ordinal: positions[item][0],
        },
    })
}
fn checked_anchor(
    part: &ImportedSourcePart,
    index: usize,
) -> Result<SourceAnchorHandle, ReviewLocationError> {
    part.element_anchor(index)
        .cloned()
        .ok_or(ReviewLocationError::Binding)
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum ReviewLocationError {
    #[error("review_location_source_rejected")]
    Source,
    #[error("review_location_original_binding_rejected")]
    Binding,
    #[error("review_location_original_budget_rejected")]
    Budget,
}
