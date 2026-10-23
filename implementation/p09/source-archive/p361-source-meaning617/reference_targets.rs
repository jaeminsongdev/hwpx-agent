//! Actual source-bound bookmark, note and table targets for the reference validator.
//!
//! This is a target import stage, not a complete auxiliary state, native name
//! resolver, reference-edge import, field update, or execution authorization.
use std::{collections::BTreeMap, fmt, io};

use domain_ir::{
    DocumentGraphLimits, Flow, LogicalId, Node, ReferenceAuxiliaryLimits, ReferenceTargetKind,
    ValidationTarget,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

pub mod caption_object_state;
pub mod caption_frames;
pub mod caption_source_state;
pub mod headings;

use super::structure::ImportedDocumentStructure;
use crate::HANCOM_2020_PARAGRAPH_NAMESPACE;

pub mod sdk;

pub const REFERENCE_TARGET_IMPORT_PROFILE: &str =
    "hwpx-agent.document-import-reference-targets/bookmarks-notes-tables-v3";

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReferenceTargetImportReceipt {
    pub profile: &'static str,
    pub source_package_sha256: [u8; 32],
    pub source_provenance_sha256: [u8; 32],
    pub structure_graph_sha256: [u8; 32],
    pub target_inventory_sha256: [u8; 32],
    pub bookmark_targets: usize,
    pub note_targets: usize,
    pub table_targets: usize,
    pub ambiguous_source_names: usize,
    pub observed_native_fields: usize,
    pub complete_reference_state_qualified: bool,
}

/// Borrows an immutable actual import. No deserialization or caller target list.
pub struct ImportedReferenceTargets<'a> {
    source: &'a ImportedDocumentStructure,
    targets: Vec<ValidationTarget>,
    names: BTreeMap<&'a str, Vec<usize>>,
    receipt: ReferenceTargetImportReceipt,
}

impl fmt::Debug for ImportedReferenceTargets<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedReferenceTargets")
            .field("targets", &self.targets.len())
            .field("scope", &"source_bookmarks_notes_and_tables")
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum ReferenceTargetImportError {
    #[error("REFERENCE_TARGET_IMPORT_LIMIT")]
    Limit,
    #[error("REFERENCE_TARGET_IMPORT_SOURCE_BINDING")]
    Binding,
    #[error("REFERENCE_TARGET_IMPORT_UNCOVERED_TARGET")]
    Coverage,
    #[error("REFERENCE_TARGET_IMPORT_MISSING_NAME")]
    Missing,
    #[error("REFERENCE_TARGET_IMPORT_AMBIGUOUS_NAME")]
    Ambiguous,
}

impl<'a> ImportedReferenceTargets<'a> {
    /// Derives typed target identities from the original source observations.
    ///
    /// # Errors
    /// Rejects budget exhaustion, mismatched source anchors, and any paragraph
    /// bookmark, note or table in ANY imported XML part not covered by the structure importer.
    /// Other target families and field meanings are not silently declared empty.
    pub fn import(
        source: &'a ImportedDocumentStructure,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, ReferenceTargetImportError> {
        let config = limits.config();
        if source.bookmarks().len() > config.items_per_kind
            || source.notes().len() > config.items_per_kind
        {
            return Err(ReferenceTargetImportError::Limit);
        }
        let mut targets = Vec::new();
        let mut names: BTreeMap<&str, Vec<usize>> = BTreeMap::new();
        let mut observed: BTreeMap<&LogicalId, bool> = BTreeMap::new();
        for bookmark in source.bookmarks() {
            if bookmark.name.len() > config.text_bytes {
                return Err(ReferenceTargetImportError::Limit);
            }
            let resolved = source
                .source()
                .resolve_anchor(&bookmark.source_anchor)
                .map_err(|_| ReferenceTargetImportError::Binding)?;
            let element = resolved
                .element()
                .ok_or(ReferenceTargetImportError::Binding)?;
            if element.name().namespace() != Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
                || element.name().local_name() != "bookmark"
                || observed
                    .insert(&bookmark.source_anchor.opaque_handle, false)
                    .is_some()
            {
                return Err(ReferenceTargetImportError::Binding);
            }
            let state_sha256 = hash_json(bookmark, config.output_bytes)?;
            names
                .entry(bookmark.name.as_str())
                .or_default()
                .push(targets.len());
            targets.push(ValidationTarget {
                logical_target_id: bookmark.reference_id.clone(),
                target_kind: ReferenceTargetKind::Bookmark,
                // A source anchor is not a LinkAnchor/page assignment. Do not
                // manufacture typed flow coordinates or native navigability.
                anchor: None,
                active: true, // The exact point marker exists in this source.
                target_state_sha256: super::hex_digest(state_sha256),
            });
        }
        for note in source.notes() {
            let resolved = source
                .source()
                .resolve_anchor(&note.source_anchor)
                .map_err(|_| ReferenceTargetImportError::Binding)?;
            let element = resolved
                .element()
                .ok_or(ReferenceTargetImportError::Binding)?;
            if element.name().namespace() != Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
                || !matches!(element.name().local_name(), "footNote" | "endNote")
                || element.name().local_name() != note.native_kind
                || observed
                    .insert(&note.source_anchor.opaque_handle, false)
                    .is_some()
            {
                return Err(ReferenceTargetImportError::Binding);
            }
            source
                .source()
                .resolve_anchor(&note.body_anchor)
                .map_err(|_| ReferenceTargetImportError::Binding)?;
            targets.push(ValidationTarget {
                // Preserve the source-derived ID, never instId/number as a
                // global identity. Notes do not enter the bookmark-name index.
                logical_target_id: note.note_id.clone(),
                target_kind: ReferenceTargetKind::Note,
                anchor: None,
                active: true, // The exact marker/body was admitted in this source.
                target_state_sha256: super::hex_digest(hash_json(note, config.output_bytes)?),
            });
        }
        let table_targets = {
            let mut collector = TableCollector {
                source,
                targets: &mut targets,
                observed: &mut observed,
                maximum: config.items_per_kind,
                output_bytes: config.output_bytes,
                count: 0,
            };
            for section in source.graph().sections() {
                collector.flow(&section.body, 0)?;
            }
            for note in source.graph().notes() {
                collector.flow(&note.body, 0)?;
            }
            if collector.count != source.receipt().tables {
                return Err(ReferenceTargetImportError::Coverage);
            }
            collector.count
        };
        let mut fields = 0usize;
        for part in source.source().parts() {
            let Some(xml) = part.xml() else { continue };
            for (index, element) in xml.elements().iter().enumerate() {
                if element.name().namespace() != Some(HANCOM_2020_PARAGRAPH_NAMESPACE) {
                    continue;
                }
                match element.name().local_name() {
                    "bookmark" | "footNote" | "endNote" | "tbl" => {
                        let anchor = part
                            .element_anchor(index)
                            .ok_or(ReferenceTargetImportError::Binding)?;
                        let seen = observed
                            .get_mut(&anchor.opaque_handle)
                            .ok_or(ReferenceTargetImportError::Coverage)?;
                        if *seen {
                            return Err(ReferenceTargetImportError::Binding);
                        }
                        *seen = true;
                    }
                    "fieldBegin" => {
                        fields += 1;
                    }
                    _ => {}
                }
            }
        }
        if observed.values().any(|seen| !seen) {
            return Err(ReferenceTargetImportError::Coverage);
        }
        let receipt = ReferenceTargetImportReceipt {
            profile: REFERENCE_TARGET_IMPORT_PROFILE,
            source_package_sha256: source.receipt().source_package_sha256,
            source_provenance_sha256: source.receipt().source_provenance_sha256,
            structure_graph_sha256: source.receipt().graph_sha256,
            target_inventory_sha256: hash_json(&targets, config.output_bytes)?,
            bookmark_targets: source.bookmarks().len(),
            note_targets: source.notes().len(),
            table_targets,
            ambiguous_source_names: names
                .values()
                .filter(|positions| positions.len() > 1)
                .count(),
            observed_native_fields: fields,
            complete_reference_state_qualified: false,
        };
        Ok(Self {
            source,
            targets,
            names,
            receipt,
        })
    }

    #[must_use]
    pub fn targets(&self) -> &[ValidationTarget] {
        &self.targets
    }

    #[must_use]
    pub const fn receipt(&self) -> &ReferenceTargetImportReceipt {
        &self.receipt
    }

    /// Exact decoded source-name matching only, without normalization or a first match.
    ///
    /// # Errors
    /// Distinguishes missing and ambiguous names. It never asks the native application.
    pub fn by_exact_source_name(
        &self,
        name: &str,
    ) -> Result<&ValidationTarget, ReferenceTargetImportError> {
        let positions = self
            .names
            .get(name)
            .ok_or(ReferenceTargetImportError::Missing)?;
        if positions.len() != 1 {
            return Err(ReferenceTargetImportError::Ambiguous);
        }
        self.targets
            .get(positions[0])
            .ok_or(ReferenceTargetImportError::Binding)
    }

    /// Reuses the original complete fresh source/graph verifier, not a hash-only replay.
    ///
    /// # Errors
    /// Rejects changed package bytes, topology, document identity or source anchors.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<ReferenceTargetImportReceipt, ReferenceTargetImportError> {
        let receipt = self
            .source
            .verify_source(fresh)
            .map_err(|_| ReferenceTargetImportError::Binding)?;
        if receipt != *self.source.receipt() {
            return Err(ReferenceTargetImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}

// Walk borrowed flow once. The original anchor already fingerprints the whole
// native table subtree within the source importer's fingerprint budget. Hashing
// every nested table body again would duplicate work and could become quadratic.
struct TableCollector<'a, 'b> {
    source: &'a ImportedDocumentStructure,
    targets: &'b mut Vec<ValidationTarget>,
    observed: &'b mut BTreeMap<&'a LogicalId, bool>,
    maximum: usize,
    output_bytes: usize,
    count: usize,
}

impl<'a> TableCollector<'a, '_> {
    fn flow(&mut self, flow: &'a Flow, depth: usize) -> Result<(), ReferenceTargetImportError> {
        if depth > DocumentGraphLimits::default().max_depth {
            return Err(ReferenceTargetImportError::Limit);
        }
        for node in &flow.children {
            match node {
                Node::Table(table) => {
                    if self.count >= self.maximum {
                        return Err(ReferenceTargetImportError::Limit);
                    }
                    let anchor = table
                        .common
                        .source_anchor
                        .as_ref()
                        .ok_or(ReferenceTargetImportError::Binding)?;
                    let resolved = self
                        .source
                        .source()
                        .resolve_anchor(anchor)
                        .map_err(|_| ReferenceTargetImportError::Binding)?;
                    let element = resolved
                        .element()
                        .ok_or(ReferenceTargetImportError::Binding)?;
                    if element.name().namespace() != Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
                        || element.name().local_name() != "tbl"
                        || self.observed.insert(&anchor.opaque_handle, false).is_some()
                    {
                        return Err(ReferenceTargetImportError::Binding);
                    }
                    self.targets.push(ValidationTarget {
                        logical_target_id: table.common.node_id.clone(),
                        target_kind: ReferenceTargetKind::Table,
                        anchor: None, // Source identity is not a native/typed flow assignment.
                        active: true,
                        target_state_sha256: super::hex_digest(hash_json(
                            &(&table.common.node_id, anchor, table.rows, table.columns),
                            self.output_bytes,
                        )?),
                    });
                    self.count += 1;
                    for cell in &table.cells {
                        self.flow(&cell.body, depth + 1)?;
                    }
                }
                Node::Drawing(drawing) => self.flow(&drawing.children, depth + 1)?,
                _ => {}
            }
        }
        Ok(())
    }
}

// Hash serialized state without allocating another whole-target JSON buffer.
struct HashWriter {
    hash: Sha256,
    bytes: usize,
    maximum: usize,
}
impl io::Write for HashWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let total = self
            .bytes
            .checked_add(bytes.len())
            .filter(|n| *n <= self.maximum)
            .ok_or_else(|| io::Error::other("REFERENCE_TARGET_IMPORT_LIMIT"))?;
        self.hash.update(bytes);
        self.bytes = total;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn hash_json(
    value: &impl Serialize,
    maximum: usize,
) -> Result<[u8; 32], ReferenceTargetImportError> {
    let mut writer = HashWriter {
        hash: Sha256::new(),
        bytes: 0,
        maximum,
    };
    serde_json::to_writer(&mut writer, value).map_err(|_| ReferenceTargetImportError::Limit)?;
    Ok(writer.hash.finalize().into())
}

/// Additional actual-source families; the legacy bookmark SDK inventory stays exact.
pub const REFERENCE_OBJECT_TARGET_IMPORT_PROFILE: &str =
    "hwpx-agent.document-import-reference-object-targets/source-presence-v1";

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ReferenceObjectTargetImportReceipt {
    pub profile: &'static str,
    pub source_package_sha256: [u8; 32],
    pub source_provenance_sha256: [u8; 32],
    pub structure_graph_sha256: [u8; 32],
    pub target_inventory_sha256: [u8; 32],
    pub object_targets: usize,
    pub equation_targets: usize,
    pub native_geometry_or_equation_semantics_qualified: bool,
    pub complete_reference_state_qualified: bool,
}

/// Exact represented native element presence, not object geometry, numbering,
/// equation evaluation, a native target selector or complete auxiliary state.
pub struct ImportedReferenceObjectTargets<'a> {
    source: &'a ImportedDocumentStructure,
    targets: Vec<ValidationTarget>,
    receipt: ReferenceObjectTargetImportReceipt,
}
impl fmt::Debug for ImportedReferenceObjectTargets<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedReferenceObjectTargets")
            .field("object_targets", &self.receipt.object_targets)
            .field("equation_targets", &self.receipt.equation_targets)
            .field("qualification", &"source_presence_only")
            .finish_non_exhaustive()
    }
}
impl<'a> ImportedReferenceObjectTargets<'a> {
    /// Reuses the original immutable structure and its subtree fingerprints.
    /// # Errors
    /// Rejects any supported native object/equation outside represented structure
    /// in ANY admitted XML part, inconsistent anchors or finite output/item limits.
    /// Other native object families remain unqualified, never declared absent.
    pub fn import(
        source: &'a ImportedDocumentStructure,
        limits: ReferenceAuxiliaryLimits,
    ) -> Result<Self, ReferenceTargetImportError> {
        let mut collector = ReferenceObjectCollector {
            source,
            targets: Vec::new(),
            observed: BTreeMap::new(),
            counts: [0; 2],
            limits,
        };
        for section in source.graph().sections() {
            collector.flow(&section.body, 0)?;
        }
        for note in source.graph().notes() {
            collector.flow(&note.body, 0)?;
        }
        // Do not omit header/nonspine objects or native controls hidden below an
        // opaque wrapper. Foreign namespaces with identical local names are not HP.
        for part in source.source().parts() {
            let Some(xml) = part.xml() else { continue };
            for (index, element) in xml.elements().iter().enumerate() {
                if source_object_kind(element).is_none() { continue; }
                let anchor = part.element_anchor(index).ok_or(ReferenceTargetImportError::Binding)?;
                let seen = collector.observed.get_mut(&anchor.opaque_handle)
                    .ok_or(ReferenceTargetImportError::Coverage)?;
                if *seen { return Err(ReferenceTargetImportError::Binding); }
                *seen = true;
            }
        }
        if collector.observed.values().any(|seen| !seen) {
            return Err(ReferenceTargetImportError::Coverage);
        }
        let receipt = ReferenceObjectTargetImportReceipt {
            profile: REFERENCE_OBJECT_TARGET_IMPORT_PROFILE,
            source_package_sha256: source.receipt().source_package_sha256,
            source_provenance_sha256: source.receipt().source_provenance_sha256,
            structure_graph_sha256: source.receipt().graph_sha256,
            target_inventory_sha256: hash_json(&collector.targets, limits.config().output_bytes)?,
            object_targets: collector.counts[0],
            equation_targets: collector.counts[1],
            native_geometry_or_equation_semantics_qualified: false,
            complete_reference_state_qualified: false,
        };
        Ok(Self { source, targets: collector.targets, receipt })
    }
    #[must_use]
    pub fn targets(&self) -> &[ValidationTarget] { &self.targets }
    #[must_use]
    pub const fn receipt(&self) -> &ReferenceObjectTargetImportReceipt { &self.receipt }
    /// # Errors
    /// Uses the original whole-source/graph reconstruction, not only saved hashes.
    pub fn verify_source(&self, fresh: &[u8]) -> Result<ReferenceObjectTargetImportReceipt, ReferenceTargetImportError> {
        let rebuilt = self.source.verify_source(fresh).map_err(|_| ReferenceTargetImportError::Binding)?;
        if rebuilt != *self.source.receipt() { return Err(ReferenceTargetImportError::Binding); }
        Ok(self.receipt.clone())
    }
}

// Same nine paragraph-native object names as the original caption classifier.
// The XML anchor, never numeric id/instId, supplies global source identity.
fn source_object_kind(element: &crate::XmlElementToken) -> Option<ReferenceTargetKind> {
    if element.name().namespace() != Some(HANCOM_2020_PARAGRAPH_NAMESPACE) { return None; }
    match element.name().local_name() {
        "pic" | "rect" | "ellipse" | "line" | "arc" | "polygon" | "curve" | "connectLine" => Some(ReferenceTargetKind::Object),
        "equation" => Some(ReferenceTargetKind::Equation),
        _ => None,
    }
}
struct ReferenceObjectCollector<'a> {
    source: &'a ImportedDocumentStructure,
    targets: Vec<ValidationTarget>,
    observed: BTreeMap<&'a LogicalId, bool>,
    counts: [usize; 2],
    limits: ReferenceAuxiliaryLimits,
}
impl<'a> ReferenceObjectCollector<'a> {
    fn flow(&mut self, flow: &'a Flow, depth: usize) -> Result<(), ReferenceTargetImportError> {
        if depth > DocumentGraphLimits::default().max_depth { return Err(ReferenceTargetImportError::Limit); }
        for node in &flow.children {
            match node {
                Node::EmbeddedObject(object) => {
                    let anchor = object.common.source_anchor.as_ref().ok_or(ReferenceTargetImportError::Binding)?;
                    let resolved = self.source.source().resolve_anchor(anchor).map_err(|_| ReferenceTargetImportError::Binding)?;
                    let element = resolved.element().ok_or(ReferenceTargetImportError::Binding)?;
                    let Some(kind) = source_object_kind(element) else { continue };
                    let count = &mut self.counts[usize::from(kind == ReferenceTargetKind::Equation)];
                    if *count >= self.limits.config().items_per_kind { return Err(ReferenceTargetImportError::Limit); }
                    if self.observed.insert(&anchor.opaque_handle, false).is_some() { return Err(ReferenceTargetImportError::Binding); }
                    self.targets.try_reserve(1).map_err(|_| ReferenceTargetImportError::Limit)?;
                    self.targets.push(ValidationTarget {
                        logical_target_id: object.common.node_id.clone(),
                        target_kind: kind,
                        anchor: None,
                        active: true, // Exact source presence, NOT native navigation or meaning.
                        target_state_sha256: super::hex_digest(hash_json(
                            &(&object.common.node_id, kind, anchor), self.limits.config().output_bytes,
                        )?),
                    });
                    *count += 1;
                }
                Node::Table(table) => { for cell in &table.cells { self.flow(&cell.body, depth + 1)?; } }
                Node::Drawing(drawing) => self.flow(&drawing.children, depth + 1)?,
                _ => {}
            }
        }
        Ok(())
    }
}

/// Source caption envelopes, not inferred label sequences or native numbering.
pub mod captions {
    use super::{ImportedDocumentStructure, source_object_kind, hash_json};
    use domain_ir::{CaptionNativeEnvelope, CaptionNativeSemanticBinding, DocumentGraphLimits,
        Flow, LogicalId, NativeCaptionSide, Node, ReferenceAuxiliaryLimits, ReferenceTargetKind, ValidationTarget};
    use serde::Serialize;
    use std::{collections::{BTreeMap,BTreeSet}, fmt};
    use thiserror::Error;
    const HP: &str = crate::HANCOM_2020_PARAGRAPH_NAMESPACE;
    #[derive(Clone, Debug, Eq, PartialEq, Serialize)]
    pub struct ReferenceCaptionImportReceipt {
        pub profile: &'static str,
        pub source_package_sha256: [u8;32],
        pub source_provenance_sha256: [u8;32],
        pub structure_graph_sha256: [u8;32],
        pub target_inventory_sha256: [u8;32],
        pub envelope_inventory_sha256: [u8;32],
        pub caption_targets: usize,
        pub sub_list_numbering_qualified: bool,
        pub complete_auxiliary_state_qualified: bool,
    }
    #[derive(Clone,Eq,PartialEq,Serialize)]
    pub struct ImportedReferenceCaptionEnvelope {
        logical_caption_id: LogicalId,
        logical_object_id: LogicalId,
        native_envelope: CaptionNativeEnvelope,
    }
    impl fmt::Debug for ImportedReferenceCaptionEnvelope {
        fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("ImportedReferenceCaptionEnvelope(<redacted>; numbering_unverified)")}
    }
    impl ImportedReferenceCaptionEnvelope {
        #[must_use] pub const fn logical_caption_id(&self)->&LogicalId {&self.logical_caption_id}
        #[must_use] pub const fn logical_object_id(&self)->&LogicalId {&self.logical_object_id}
        #[must_use] pub const fn native_envelope(&self)->&CaptionNativeEnvelope {&self.native_envelope}
    }
    pub struct ImportedReferenceCaptions<'a> {
        source: &'a ImportedDocumentStructure,
        targets: Vec<ValidationTarget>,
        envelopes: Vec<ImportedReferenceCaptionEnvelope>,
        receipt: ReferenceCaptionImportReceipt,
    }
    impl fmt::Debug for ImportedReferenceCaptions<'_> {
        fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.debug_struct("ImportedReferenceCaptions").field("captions",&self.targets.len()).field("qualification",&"envelope_only").finish_non_exhaustive()}
    }
    #[derive(Clone,Copy,Debug,Eq,Error,PartialEq)]
    pub enum ReferenceCaptionImportError {
        #[error("REFERENCE_CAPTION_IMPORT_BINDING")] Binding,
        #[error("REFERENCE_CAPTION_IMPORT_COVERAGE")] Coverage,
        #[error("REFERENCE_CAPTION_IMPORT_ENVELOPE")] Envelope,
        #[error("REFERENCE_CAPTION_IMPORT_LIMIT")] Limit,
    }
    impl<'a> ImportedReferenceCaptions<'a> {
        /// Reads admitted XML/graph anchors once; no per-caption ZIP/XML reparse
        /// or subtree serialization. Unknown caption content remains fingerprinted.
        /// # Errors
        /// Rejects unrepresented/header/nonspine/unsupported ownership, multiple
        /// captions per owner, missing/malformed envelope values and finite limits.
        pub fn import(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Self,ReferenceCaptionImportError> {
            let mut owners=BTreeMap::new();
            for section in source.graph().sections() {walk(source,&section.body,&mut owners,0)?;}
            for note in source.graph().notes() {walk(source,&note.body,&mut owners,0)?;}
            let mut seen=BTreeSet::new(); let mut targets=Vec::new(); let mut envelopes=Vec::new();
            for part in source.source().parts() {
                let Some(xml)=part.xml() else {continue};
                for (index,element) in xml.elements().iter().enumerate() {
                    if !named(element,"caption") {continue;}
                    if targets.len()>=limits.config().items_per_kind {return Err(ReferenceCaptionImportError::Limit);}
                    let parent=element.parent().ok_or(ReferenceCaptionImportError::Coverage)?;
                    let anchor=part.element_anchor(parent).ok_or(ReferenceCaptionImportError::Binding)?;
                    let owner=*owners.get(&anchor.opaque_handle).ok_or(ReferenceCaptionImportError::Coverage)?;
                    if !seen.insert(owner) {return Err(ReferenceCaptionImportError::Envelope);}
                    let caption=part.element_anchor(index).ok_or(ReferenceCaptionImportError::Binding)?;
                    let mut sublist=None; let mut child=element.first_child();
                    while let Some(current)=child {
                        let value=&xml.elements()[current]; child=value.next_sibling();
                        if named(value,"subList") {
                            if sublist.replace(current).is_some() {return Err(ReferenceCaptionImportError::Envelope);}
                        }
                    }
                    let sublist=part.element_anchor(sublist.ok_or(ReferenceCaptionImportError::Envelope)?).ok_or(ReferenceCaptionImportError::Binding)?;
                    let side=match attr(element,"side")? {
                        "LEFT"=>NativeCaptionSide::Left,"RIGHT"=>NativeCaptionSide::Right,
                        "TOP"=>NativeCaptionSide::Top,"BOTTOM"=>NativeCaptionSide::Bottom,
                        _=>return Err(ReferenceCaptionImportError::Envelope),
                    };
                    let full_size=match attr(element,"fullSz")? {"0"|"false"=>false,"1"|"true"=>true,_=>return Err(ReferenceCaptionImportError::Envelope)};
                    let width_hwpunit=attr(element,"width")?.parse::<i32>().map_err(|_|ReferenceCaptionImportError::Envelope)?;
                    let gap_hwpunit=attr(element,"gap")?.parse::<u32>().map_err(|_|ReferenceCaptionImportError::Envelope)?;
                    let last_width_hwpunit=attr(element,"lastWidth")?.parse::<u32>().map_err(|_|ReferenceCaptionImportError::Envelope)?;
                    if width_hwpunit < -1 {return Err(ReferenceCaptionImportError::Envelope);}
                    if width_hwpunit.max(0) as u32>limits.config().extent_hwpunit || gap_hwpunit>limits.config().extent_hwpunit || last_width_hwpunit>limits.config().extent_hwpunit {return Err(ReferenceCaptionImportError::Limit);}
                    let logical_caption_id=LogicalId::parse(format!("caption-{}",caption.opaque_handle.as_str())).map_err(|_|ReferenceCaptionImportError::Binding)?;
                    let envelope=ImportedReferenceCaptionEnvelope {logical_caption_id:logical_caption_id.clone(),logical_object_id:owner.clone(),native_envelope:CaptionNativeEnvelope {
                        side,full_size,width_hwpunit,gap_hwpunit,last_width_hwpunit,
                        sub_list_sha256:super::super::hex_digest(sublist.fingerprint_sha256),
                        opaque_native_state_sha256:super::super::hex_digest(caption.fingerprint_sha256),
                        semantic_binding:CaptionNativeSemanticBinding::UnverifiedSubListNumbering,
                    }};
                    targets.try_reserve(1).map_err(|_|ReferenceCaptionImportError::Limit)?;
                    envelopes.try_reserve(1).map_err(|_|ReferenceCaptionImportError::Limit)?;
                    targets.push(ValidationTarget {logical_target_id:logical_caption_id,target_kind:ReferenceTargetKind::Caption,anchor:None,active:true,
                        target_state_sha256:super::super::hex_digest(hash_json(&envelope,limits.config().output_bytes).map_err(|_|ReferenceCaptionImportError::Limit)?)});
                    envelopes.push(envelope);
                }
            }
            let receipt=ReferenceCaptionImportReceipt {profile:"hwpx-agent.document-import-reference-caption-envelopes/source-v1",
                source_package_sha256:source.receipt().source_package_sha256,source_provenance_sha256:source.receipt().source_provenance_sha256,
                structure_graph_sha256:source.receipt().graph_sha256,
                target_inventory_sha256:hash_json(&targets,limits.config().output_bytes).map_err(|_|ReferenceCaptionImportError::Limit)?,
                envelope_inventory_sha256:hash_json(&envelopes,limits.config().output_bytes).map_err(|_|ReferenceCaptionImportError::Limit)?,
                caption_targets:targets.len(),sub_list_numbering_qualified:false,complete_auxiliary_state_qualified:false};
            Ok(Self {source,targets,envelopes,receipt})
        }
        #[must_use] pub fn targets(&self)->&[ValidationTarget] {&self.targets}
        #[must_use] pub fn envelopes(&self)->&[ImportedReferenceCaptionEnvelope] {&self.envelopes}
        #[must_use] pub const fn receipt(&self)->&ReferenceCaptionImportReceipt {&self.receipt}
        /// # Errors
        /// Original whole-source/graph fresh reconstruction; no saved-hash-only acceptance.
        pub fn verify_source(&self,fresh:&[u8])->Result<ReferenceCaptionImportReceipt,ReferenceCaptionImportError> {
            if self.source.verify_source(fresh).map_err(|_|ReferenceCaptionImportError::Binding)?!=*self.source.receipt() {return Err(ReferenceCaptionImportError::Binding);}
            Ok(self.receipt.clone())
        }
        /// Reuses an operation-local whole-source reconstruction without parsing
        /// the package again. This proof is not service access or head authority.
        /// # Errors
        /// Rejects a foreign original/proof or any reconstructed caption drift.
        pub fn verify_reconstructed(
            &self, original:&crate::document_import::forms::ImportedDocumentForms,
            proof:&crate::document_import::forms::VerifiedFormReconstruction<'_>,
            limits:ReferenceAuxiliaryLimits,
        )->Result<ReferenceCaptionImportReceipt,ReferenceCaptionImportError> {
            if !std::ptr::eq(self.source,original.body_structure()) {return Err(ReferenceCaptionImportError::Binding);}
            let fresh=proof.for_original(original).map_err(|_|ReferenceCaptionImportError::Binding)?;
            let rebuilt=ImportedReferenceCaptions::import(fresh.body_structure(),limits)?;
            if rebuilt.receipt!=self.receipt||rebuilt.targets!=self.targets||rebuilt.envelopes!=self.envelopes {return Err(ReferenceCaptionImportError::Binding);}
            Ok(self.receipt.clone())
        }
    }
    fn named(element:&crate::XmlElementToken,name:&str)->bool {element.name().namespace()==Some(HP)&&element.name().local_name()==name}
    fn attr<'a>(element:&'a crate::XmlElementToken,name:&str)->Result<&'a str,ReferenceCaptionImportError> {
        element.attributes().iter().find(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()==name)
            .map(crate::XmlAttributeToken::semantic_value).ok_or(ReferenceCaptionImportError::Envelope)
    }
    fn walk<'a>(source:&'a ImportedDocumentStructure,flow:&'a Flow,owners:&mut BTreeMap<&'a LogicalId,&'a LogicalId>,depth:usize)->Result<(),ReferenceCaptionImportError> {
        if depth>DocumentGraphLimits::default().max_depth {return Err(ReferenceCaptionImportError::Limit);}
        for node in &flow.children {
            if matches!(node,Node::Table(_)|Node::EmbeddedObject(_)) {
                let common=node.common(); let anchor=common.source_anchor.as_ref().ok_or(ReferenceCaptionImportError::Binding)?;
                let resolved=source.source().resolve_anchor(anchor).map_err(|_|ReferenceCaptionImportError::Binding)?;
                let element=resolved.element().ok_or(ReferenceCaptionImportError::Binding)?;
                if (source_object_kind(element).is_some()||named(element,"tbl"))&&owners.insert(&anchor.opaque_handle,&common.node_id).is_some() {return Err(ReferenceCaptionImportError::Binding);}
            }
            match node {
                Node::Table(table)=>for cell in &table.cells {walk(source,&cell.body,owners,depth+1)?;},
                Node::Drawing(drawing)=>walk(source,&drawing.children,owners,depth+1)?,_=>{},
            }
        }
        Ok(())
    }
}

/// Native number controls are source observations, not resolved sequence state.
pub mod numbering {
    use super::*;
    use super::captions::ImportedReferenceCaptions;
    use domain_ir::{CaptionNumberFormat,PropertyValue};
    use std::collections::BTreeSet;
    const HP:&str=crate::HANCOM_2020_PARAGRAPH_NAMESPACE;

    #[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
    #[serde(rename_all="snake_case")]
    pub enum NativeNumberCategory {Page,Footnote,Endnote,Picture,Table,Equation,TotalPage}
    #[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
    #[serde(rename_all="snake_case")]
    pub enum NativeNumberControlKind {AutoNumber,Restart}
    #[derive(Clone,Debug,Eq,PartialEq,Serialize)]
    pub struct NativeNumberFormatObservation {
        pub native_type:&'static str,
        pub typed_format:Option<CaptionNumberFormat>,
        pub user_character_sha256:[u8;32],
        pub prefix_sha256:[u8;32],
        pub suffix_sha256:[u8;32],
        pub affixes_and_user_character_empty:bool,
        pub superscript:bool,
        pub source_fingerprint_sha256:[u8;32],
    }
    #[derive(Clone,Eq,PartialEq,Serialize)]
    pub struct NativeNumberControlObservation {
        pub logical_control_id:LogicalId,
        pub section_id:LogicalId,
        pub logical_caption_id:Option<LogicalId>,
        pub kind:NativeNumberControlKind,
        pub category:NativeNumberCategory,
        /// Raw stored native integer, never relabelled as recalculated/resolved.
        pub stored_number:i32,
        pub format:Option<NativeNumberFormatObservation>,
        pub source_fingerprint_sha256:[u8;32],
    }
    impl fmt::Debug for NativeNumberControlObservation {
        fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("NativeNumberControlObservation(<redacted>; source_stored_only)")}
    }
    #[derive(Clone,Eq,PartialEq,Serialize)]
    pub struct NativeSectionStartObservation {
        pub logical_control_id:LogicalId,
        pub section_id:LogicalId,
        pub page_starts_on:&'static str,
        pub page:u32,
        pub picture:u32,
        pub table:u32,
        pub equation:u32,
        pub source_fingerprint_sha256:[u8;32],
    }
    impl fmt::Debug for NativeSectionStartObservation {
        fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("NativeSectionStartObservation(<redacted>; zero_not_interpreted)")}
    }
    #[derive(Clone,Debug,Eq,PartialEq,Serialize)]
    pub struct CaptionNumberingImportReceipt {
        pub profile:&'static str,
        pub source_package_sha256:[u8;32],
        pub structure_graph_sha256:[u8;32],
        pub control_inventory_sha256:[u8;32],
        pub section_start_inventory_sha256:[u8;32],
        #[serde(skip_serializing_if="Option::is_none")]
        pub review_body_inventory_sha256:Option<[u8;32]>,
        pub auto_numbers:usize,
        pub caption_auto_numbers:usize,
        pub restart_controls:usize,
        pub section_starts:usize,
        pub sequence_interpretation_qualified:bool,
        pub native_recalculation_qualified:bool,
        pub complete_auxiliary_state_qualified:bool,
    }
    pub struct ImportedCaptionNumbering<'a> {
        source:&'a ImportedDocumentStructure,
        captions:ImportedReferenceCaptions<'a>,
        controls:Vec<NativeNumberControlObservation>,
        starts:Vec<NativeSectionStartObservation>,
        paragraphs:BTreeSet<&'a LogicalId>,
        review_paragraphs:BTreeSet<LogicalId>,
        receipt:CaptionNumberingImportReceipt,
    }
    impl fmt::Debug for ImportedCaptionNumbering<'_> {
        fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("ImportedCaptionNumbering(<redacted>; sequence_unverified)")}
    }
    #[derive(Clone,Copy,Debug,Eq,Error,PartialEq)]
    pub enum CaptionNumberingImportError {
        #[error("CAPTION_NUMBERING_BINDING")] Binding,
        #[error("CAPTION_NUMBERING_COVERAGE")] Coverage,
        #[error("CAPTION_NUMBERING_NATIVE_VALUE")] Value,
        #[error("CAPTION_NUMBERING_CAPTION_ENVELOPE")] CaptionEnvelope,
        #[error("CAPTION_NUMBERING_LIMIT")] Limit,
    }
    impl<'a> ImportedCaptionNumbering<'a> {
        /// Scans every admitted XML part once, matching represented paragraphs
        /// or exact caption/subList/p/run/ctrl ancestry. No native-ID aliasing,
        /// per-caption package parse, guessed restart/default or cache refresh.
        /// # Errors
        /// Rejects unrepresented/header/nonspine/opaque controls, invalid native
        /// values, malformed format/control ancestry, duplicate starts and bounds.
        pub fn import(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Self,CaptionNumberingImportError> {
            Self::import_with_review_paragraphs(source,limits,BTreeSet::new(),None)
        }
        /// Exact immutable Form/review identity, not a caller paragraph allowlist or Native visibility claim.
        /// # Errors
        /// Rejects foreign review/model bindings, finite bounds and the original coverage/value failures.
        pub fn import_review_bound(forms:&'a crate::document_import::forms::ImportedDocumentForms,
            review:&crate::document_import::structure::review::ImportedDocumentReviewBodies<'_>,limits:ReferenceAuxiliaryLimits)
            ->Result<Self,CaptionNumberingImportError> {
            use CaptionNumberingImportError as E;
            if !review.is_for_original(forms)||review.receipt().source_package_sha256!=forms.source().receipt().source_package_sha256{return Err(E::Binding);}
            let mut observed=BTreeSet::new();
            for item in review.observations(){if let Some(flow)=&item.body{walk(flow,&mut observed,0)?;
                if observed.len()>limits.config().items_per_kind{return Err(E::Limit);}}}
            let paragraphs=observed.into_iter().cloned().collect();
            Self::import_with_review_paragraphs(forms.body_structure(),limits,paragraphs,Some(review.receipt().body_observations_sha256))
        }
        fn import_with_review_paragraphs(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits,
            review_paragraphs:BTreeSet<LogicalId>,review_body_inventory_sha256:Option<[u8;32]>)->Result<Self,CaptionNumberingImportError> {
            use CaptionNumberingImportError as E;
            if source.graph().sections().len()>limits.config().sections {return Err(E::Limit);}
            let captions=ImportedReferenceCaptions::import(source,limits).map_err(|e|match e {
                super::captions::ReferenceCaptionImportError::Limit=>E::Limit,
                super::captions::ReferenceCaptionImportError::Coverage=>E::Coverage,
                super::captions::ReferenceCaptionImportError::Envelope=>E::CaptionEnvelope,_=>E::Binding})?;
            let caption_ids:BTreeMap<_,_>=captions.envelopes().iter().map(|c|(c.logical_caption_id().as_str(),c.logical_caption_id())).collect();
            let mut paragraphs=BTreeSet::new();let mut sections=BTreeMap::new();
            for section in source.graph().sections() {
                let part=section.properties.iter().find(|(k,_)|*k=="source_part").and_then(|(_,v)|if let PropertyValue::Id(id)=v {Some(id.as_str())} else {None}).ok_or(E::Binding)?;
                if sections.insert(part,&section.section_id).is_some() {return Err(E::Binding);}
                walk(&section.body,&mut paragraphs,0)?;
            }
            for note in source.graph().notes() {walk(&note.body,&mut paragraphs,0)?;}
            let mut controls=Vec::new();let mut starts=Vec::new();let(mut auto_numbers,mut caption_auto_numbers,mut restart_controls)=(0,0,0);
            for part in source.source().parts() {
                let Some(xml)=part.xml() else {continue};
                let resource=format!("resource-{}",part.anchor().opaque_handle.as_str());
                let section=sections.get(resource.as_str()).copied();let mut seen_start=false;
                for (index,node) in xml.elements().iter().enumerate() {
                    if node.name().namespace()!=Some(HP) {continue;}
                    let name=node.name().local_name();if !matches!(name,"autoNum"|"newNum"|"startNum") {continue;}
                    let section=section.ok_or(E::Coverage)?;
                    let anchor=part.element_anchor(index).ok_or(E::Binding)?;
                    let logical_control_id=LogicalId::parse(format!("native-number-{}",anchor.opaque_handle.as_str())).map_err(|_|E::Binding)?;
                    if name=="startNum" {
                        if starts.len()>=limits.config().sections {return Err(E::Limit);}
                        let parent=node.parent().filter(|p|named(&xml.elements()[*p],"secPr")).ok_or(E::Coverage)?;
                        let paragraph=run_paragraph(xml,parent)?;
                        if xml.elements()[paragraph].parent()!=Some(xml.root_element())||seen_start {return Err(E::Coverage);}
                        require_paragraph(part,paragraph,&paragraphs)?;seen_start=true;
                        let page_starts_on=match attr(node,"pageStartsOn")? {"BOTH"=>"BOTH","EVEN"=>"EVEN","ODD"=>"ODD",_=>return Err(E::Value)};
                        starts.try_reserve(1).map_err(|_|E::Limit)?;
                        starts.push(NativeSectionStartObservation {logical_control_id,section_id:section.clone(),page_starts_on,
                            page:unsigned(node,"page")?,picture:unsigned(node,"pic")?,table:unsigned(node,"tbl")?,equation:unsigned(node,"equation")?,source_fingerprint_sha256:anchor.fingerprint_sha256});
                        continue;
                    }
                    if controls.len()>=limits.config().items_per_kind {return Err(E::Limit);}
                    let wrapper=node.parent().filter(|p|named(&xml.elements()[*p],"ctrl")).ok_or(E::Coverage)?;
                    let paragraph=run_paragraph(xml,wrapper)?;
                    let logical_caption_id=if require_paragraph(part,paragraph,&paragraphs).is_ok()
                        ||part.element_anchor(paragraph).is_some_and(|a|review_paragraphs.contains(&a.opaque_handle)) {None} else {
                        let sub=xml.elements()[paragraph].parent().filter(|p|named(&xml.elements()[*p],"subList")).ok_or(E::Coverage)?;
                        let caption=xml.elements()[sub].parent().filter(|p|named(&xml.elements()[*p],"caption")).ok_or(E::Coverage)?;
                        let cap=part.element_anchor(caption).ok_or(E::Binding)?;
                        let id=format!("caption-{}",cap.opaque_handle.as_str());
                        Some((*caption_ids.get(id.as_str()).ok_or(E::Coverage)?).clone())
                    };
                    let category=category(attr(node,"numType")?)?;
                    let stored_number=attr(node,"num")?.parse::<i32>().map_err(|_|E::Value)?;
                    let mut format=None;let mut child=node.first_child();
                    while let Some(i)=child {let e=&xml.elements()[i];child=e.next_sibling();
                        if named(e,"autoNumFormat") {
                            if format.is_some() {return Err(E::Value);}
                            format=Some(read_format(e,part.element_anchor(i).ok_or(E::Binding)?.fingerprint_sha256,limits)?);
                        }
                    }
                    let kind=if name=="autoNum" {if format.is_none(){return Err(E::Value);}auto_numbers+=1;if logical_caption_id.is_some(){caption_auto_numbers+=1;}NativeNumberControlKind::AutoNumber}
                        else {restart_controls+=1;NativeNumberControlKind::Restart};
                    controls.try_reserve(1).map_err(|_|E::Limit)?;
                    controls.push(NativeNumberControlObservation {logical_control_id,section_id:section.clone(),logical_caption_id,kind,category,stored_number,format,source_fingerprint_sha256:anchor.fingerprint_sha256});
                }
            }
            let receipt=CaptionNumberingImportReceipt {profile:if review_body_inventory_sha256.is_some(){"hwpx-agent.document-import-caption-numbering/source-review-observations-v2"}else{"hwpx-agent.document-import-caption-numbering/source-observations-v1"},
                source_package_sha256:source.receipt().source_package_sha256,structure_graph_sha256:source.receipt().graph_sha256,
                control_inventory_sha256:hash_json(&controls,limits.config().output_bytes).map_err(|_|E::Limit)?,
                section_start_inventory_sha256:hash_json(&starts,limits.config().output_bytes).map_err(|_|E::Limit)?,review_body_inventory_sha256,
                auto_numbers,caption_auto_numbers,restart_controls,section_starts:starts.len(),sequence_interpretation_qualified:false,native_recalculation_qualified:false,complete_auxiliary_state_qualified:false};
            Ok(Self {source,captions,controls,starts,paragraphs,review_paragraphs,receipt})
        }
        /// Reads source caption text/style/control frames without inferring
        /// labels, counter values, inherited formatting or execution authority.
        /// # Errors
        /// Rejects inconsistent source bindings, native values and finite limits.
        pub fn import_frames(&self,limits:ReferenceAuxiliaryLimits)
            ->Result<super::caption_frames::ImportedCaptionFrames<'a>,CaptionNumberingImportError> {
            super::caption_frames::ImportedCaptionFrames::import(self.source,&self.captions,&self.controls,&self.receipt,limits)
        }
        pub(super) const fn original_structure(&self)->&'a ImportedDocumentStructure {self.source}
        pub(in crate::document_import) fn admits_number_paragraph(&self,id:&LogicalId)->bool {self.paragraphs.contains(id)||self.review_paragraphs.contains(id)}
        #[must_use] pub const fn caption_import(&self)->&ImportedReferenceCaptions<'a> {&self.captions}
        #[must_use] pub fn controls(&self)->&[NativeNumberControlObservation] {&self.controls}
        #[must_use] pub fn section_starts(&self)->&[NativeSectionStartObservation] {&self.starts}
        #[must_use] pub const fn receipt(&self)->&CaptionNumberingImportReceipt {&self.receipt}
        /// # Errors
        /// Reconstructs the complete original source/graph; never cached authority.
        pub fn verify_source(&self,fresh:&[u8])->Result<CaptionNumberingImportReceipt,CaptionNumberingImportError> {
            if self.source.verify_source(fresh).map_err(|_|CaptionNumberingImportError::Binding)?!=*self.source.receipt() {return Err(CaptionNumberingImportError::Binding);}
            Ok(self.receipt.clone())
        }
    }
    fn named(node:&crate::XmlElementToken,name:&str)->bool {node.name().namespace()==Some(HP)&&node.name().local_name()==name}
    fn attr<'a>(node:&'a crate::XmlElementToken,name:&str)->Result<&'a str,CaptionNumberingImportError> {
        node.attributes().iter().find(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()==name).map(crate::XmlAttributeToken::semantic_value).ok_or(CaptionNumberingImportError::Value)
    }
    fn unsigned(node:&crate::XmlElementToken,name:&str)->Result<u32,CaptionNumberingImportError> {attr(node,name)?.parse().map_err(|_|CaptionNumberingImportError::Value)}
    fn category(value:&str)->Result<NativeNumberCategory,CaptionNumberingImportError> {
        Ok(match value {"PAGE"=>NativeNumberCategory::Page,"FOOTNOTE"=>NativeNumberCategory::Footnote,"ENDNOTE"=>NativeNumberCategory::Endnote,
            "PICTURE"=>NativeNumberCategory::Picture,"TABLE"=>NativeNumberCategory::Table,"EQUATION"=>NativeNumberCategory::Equation,"TOTAL_PAGE"=>NativeNumberCategory::TotalPage,_=>return Err(CaptionNumberingImportError::Value)})
    }
    /// Source context needed by a future complete sequence/state compiler.
    /// No default starts, counter evaluation, mutation or execution authority.
    pub mod context {
        use super::*;
        use domain_ir::{CaptionObjectKind,NodeCommon};
        const HH:&str="http://www.hancom.co.kr/hwpml/2011/head";
        #[derive(Clone,Copy,Debug,Eq,Ord,PartialEq,PartialOrd,Serialize)]
        pub struct NumberingSourcePosition {pub spine_ordinal:usize,pub xml_element_ordinal:usize}
        #[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
        #[serde(rename_all="snake_case")]
        pub enum NativeOwnerNumberingType {None,Picture,Table,Equation}
        #[derive(Clone,Eq,PartialEq,Serialize)]
        pub struct NativeNumberingOwnerObservation {
            pub logical_object_id:LogicalId,
            pub logical_caption_id:Option<LogicalId>,
            pub section_id:LogicalId,
            pub structural_kind:CaptionObjectKind,
            /// None means missing/unknown, not the observed native value NONE.
            pub numbering_type:Option<NativeOwnerNumberingType>,
            pub source_position:NumberingSourcePosition,
            /// Whole original subtree identity, not a mutable typed-state projection.
            pub source_fingerprint_sha256:[u8;32],
        }
        impl fmt::Debug for NativeNumberingOwnerObservation {
            fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("NativeNumberingOwnerObservation(<redacted>; source_context_only)")}
        }
        #[derive(Clone,Eq,PartialEq,Serialize)]
        pub struct NativeDocumentNumberingStart {
            pub logical_control_id:LogicalId,
            pub page:u32,pub footnote:u32,pub endnote:u32,pub picture:u32,pub table:u32,pub equation:u32,
            pub source_fingerprint_sha256:[u8;32],
        }
        impl fmt::Debug for NativeDocumentNumberingStart {
            fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("NativeDocumentNumberingStart(<redacted>; no_defaults)")}
        }
        #[derive(Clone,Eq,PartialEq,Serialize)]
        pub struct OrderedNumberingControl {
            pub logical_control_id:LogicalId,
            pub section_id:LogicalId,
            pub source_position:NumberingSourcePosition,
        }
        impl fmt::Debug for OrderedNumberingControl {
            fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("OrderedNumberingControl(<redacted>; XML_not_render_order)")}
        }
        #[derive(Clone,Debug,Eq,PartialEq,Serialize)]
        pub struct NumberingContextImportReceipt {
            pub profile:&'static str,
            pub numbering:CaptionNumberingImportReceipt,
            pub document_start_sha256:[u8;32],
            pub owner_inventory_sha256:[u8;32],
            pub control_order_sha256:[u8;32],
            pub document_start_observed:bool,
            pub known_owners:usize,
            pub uncaptioned_owners:usize,
            pub missing_owner_numbering_types:usize,
            pub complete_auxiliary_state_and_sequence_interpretation_qualified:bool,
        }
        pub struct ImportedNumberingContext<'a> {
            source:&'a ImportedDocumentStructure,
            beginning:Option<NativeDocumentNumberingStart>,
            owners:Vec<NativeNumberingOwnerObservation>,
            controls:Vec<OrderedNumberingControl>,
            receipt:NumberingContextImportReceipt,
        }
        impl fmt::Debug for ImportedNumberingContext<'_> {
            fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("ImportedNumberingContext(<redacted>; XML_context_not_resolved_sequence)")}
        }
        impl<'a> ImportedCaptionNumbering<'a> {
            /// Reuses this exact original source and caption/number inventories;
            /// one borrowed graph walk/XML scan, never per-caption ZIP/XML parsing.
            /// # Errors
            /// Rejects unrepresented known owners, wrong/duplicate/hidden beginNum,
            /// malformed explicit attrs, missing control matches and finite limits.
            pub fn import_context(&self,limits:ReferenceAuxiliaryLimits)->Result<ImportedNumberingContext<'a>,CaptionNumberingImportError> {
                use CaptionNumberingImportError as E;
                let source=self.source;
                if source.graph().sections().len()>limits.config().sections||self.controls.len()>limits.config().items_per_kind||self.starts.len()>limits.config().sections {return Err(E::Limit);}
                let mut objects=BTreeMap::new();let mut sections=BTreeMap::new();
                for section in source.graph().sections() {
                    let part=section.properties.iter().find(|(k,_)|*k=="source_part").and_then(|(_,v)|if let PropertyValue::Id(id)=v {Some(id.as_str())}else{None}).ok_or(E::Binding)?;
                    if sections.insert(part,&section.section_id).is_some(){return Err(E::Binding);}
                    object_nodes(&section.body,&mut objects,0)?;
                }
                for note in source.graph().notes(){object_nodes(&note.body,&mut objects,0)?;}
                let spine:BTreeMap<_,_>=source.source().spine().iter().enumerate().map(|(i,p)|(p,i)).collect();
                let caption_by_owner:BTreeMap<_,_>=self.captions.envelopes().iter().map(|c|(c.logical_object_id(),c.logical_caption_id())).collect();
                let expected:BTreeMap<_,_>=self.controls.iter().map(|c|(&c.logical_control_id,&c.section_id))
                    .chain(self.starts.iter().map(|c|(&c.logical_control_id,&c.section_id))).collect();
                if expected.len()!=self.controls.len()+self.starts.len(){return Err(E::Binding);}
                let mut matched=BTreeSet::new();let mut owners=Vec::new();let mut controls=Vec::new();let mut beginning=None;
                for part in source.source().parts() {
                    let Some(xml)=part.xml() else {continue};
                    let resource=format!("resource-{}",part.anchor().opaque_handle.as_str());
                    let section=sections.get(resource.as_str()).copied();let ordinal=spine.get(part.path()).copied();
                    for (index,node) in xml.elements().iter().enumerate() {
                        if node.name().namespace()==Some(HH)&&node.name().local_name()=="beginNum" {
                            let root=&xml.elements()[xml.root_element()];
                            if part.path().as_str()!="Contents/header.xml"||node.parent()!=Some(xml.root_element())
                                ||root.name().namespace()!=Some(HH)||root.name().local_name()!="head" {return Err(E::Coverage);}
                            if beginning.is_some(){return Err(E::Value);}
                            let anchor=part.element_anchor(index).ok_or(E::Binding)?;
                            beginning=Some(NativeDocumentNumberingStart {
                                logical_control_id:LogicalId::parse(format!("native-number-{}",anchor.opaque_handle.as_str())).map_err(|_|E::Binding)?,
                                page:unsigned(node,"page")?,footnote:unsigned(node,"footnote")?,endnote:unsigned(node,"endnote")?,
                                picture:unsigned(node,"pic")?,table:unsigned(node,"tbl")?,equation:unsigned(node,"equation")?,
                                source_fingerprint_sha256:anchor.fingerprint_sha256});
                        }
                        if node.name().namespace()!=Some(HP){continue;}
                        let is_owner=super::super::source_object_kind(node).is_some()||named(node,"tbl");
                        let is_control=matches!(node.name().local_name(),"autoNum"|"newNum"|"startNum");
                        if !is_owner&&node.attributes().iter().any(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()=="numberingType"){return Err(E::Coverage);}
                        if !is_owner&&!is_control {continue;}
                        let section=section.ok_or(E::Coverage)?;
                        let source_position=NumberingSourcePosition {spine_ordinal:ordinal.ok_or(E::Coverage)?,xml_element_ordinal:index};
                        let anchor=part.element_anchor(index).ok_or(E::Binding)?;
                        if is_owner {
                            if owners.len()>=limits.config().items_per_kind {return Err(E::Limit);}
                            let common=*objects.get(&anchor.opaque_handle).ok_or(E::Coverage)?;
                            let value=node.attributes().iter().find(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()=="numberingType");
                            let numbering_type=value.map(|v|match v.semantic_value() {
                                "NONE"=>Ok(NativeOwnerNumberingType::None),"PICTURE"=>Ok(NativeOwnerNumberingType::Picture),
                                "TABLE"=>Ok(NativeOwnerNumberingType::Table),"EQUATION"=>Ok(NativeOwnerNumberingType::Equation),_=>Err(E::Value)}).transpose()?;
                            let structural_kind=if named(node,"tbl"){CaptionObjectKind::Table}else if named(node,"equation"){CaptionObjectKind::Equation}else{CaptionObjectKind::Picture};
                            owners.try_reserve(1).map_err(|_|E::Limit)?;
                            owners.push(NativeNumberingOwnerObservation {logical_object_id:common.node_id.clone(),
                                logical_caption_id:caption_by_owner.get(&common.node_id).map(|id|(*id).clone()),section_id:section.clone(),
                                structural_kind,numbering_type,source_position,source_fingerprint_sha256:anchor.fingerprint_sha256});
                        } else {
                            let id=LogicalId::parse(format!("native-number-{}",anchor.opaque_handle.as_str())).map_err(|_|E::Binding)?;
                            if expected.get(&id).copied()!=Some(section)||!matched.insert(id.clone()){return Err(E::Binding);}
                            controls.try_reserve(1).map_err(|_|E::Limit)?;
                            controls.push(OrderedNumberingControl {logical_control_id:id,section_id:section.clone(),source_position});
                        }
                    }
                }
                if matched.len()!=expected.len(){return Err(E::Coverage);}
                owners.sort_by_key(|o|o.source_position);controls.sort_by_key(|c|c.source_position);
                let receipt=NumberingContextImportReceipt {profile:"hwpx-agent.document-import-numbering-context/source-v1",numbering:self.receipt.clone(),
                    document_start_sha256:hash_json(&beginning,limits.config().output_bytes).map_err(|_|E::Limit)?,
                    owner_inventory_sha256:hash_json(&owners,limits.config().output_bytes).map_err(|_|E::Limit)?,
                    control_order_sha256:hash_json(&controls,limits.config().output_bytes).map_err(|_|E::Limit)?,
                    document_start_observed:beginning.is_some(),known_owners:owners.len(),uncaptioned_owners:owners.iter().filter(|o|o.logical_caption_id.is_none()).count(),
                    missing_owner_numbering_types:owners.iter().filter(|o|o.numbering_type.is_none()).count(),
                    complete_auxiliary_state_and_sequence_interpretation_qualified:false};
                Ok(ImportedNumberingContext {source,beginning,owners,controls,receipt})
            }
        }
        impl<'a> ImportedNumberingContext<'a> {
            #[must_use] pub const fn document_start(&self)->Option<&NativeDocumentNumberingStart> {self.beginning.as_ref()}
            #[must_use] pub fn owners(&self)->&[NativeNumberingOwnerObservation] {&self.owners}
            #[must_use] pub fn ordered_controls(&self)->&[OrderedNumberingControl] {&self.controls}
            #[must_use] pub const fn receipt(&self)->&NumberingContextImportReceipt {&self.receipt}
            /// Projects the non-caption object state separately from complete
            /// caption envelopes; does not infer protection or counter semantics.
            /// # Errors
            /// Rejects inconsistent source bindings and finite work/output limits.
            pub fn project_object_states(&self,limits:ReferenceAuxiliaryLimits)
                ->Result<super::super::caption_object_state::ImportedCaptionObjectStates<'a>,CaptionNumberingImportError> {
                super::super::caption_object_state::ImportedCaptionObjectStates::import(self.source,&self.owners,&self.receipt,limits)
            }
            /// Whole original source/graph reconstruction, not service authorization.
            /// # Errors
            /// Rejects stale source/graph, never promotes sequence interpretation.
            pub fn verify_source(&self,fresh:&[u8])->Result<NumberingContextImportReceipt,CaptionNumberingImportError> {
                if self.source.verify_source(fresh).map_err(|_|CaptionNumberingImportError::Binding)?!=*self.source.receipt(){return Err(CaptionNumberingImportError::Binding);}
                Ok(self.receipt.clone())
            }
        }
        fn object_nodes<'a>(flow:&'a Flow,objects:&mut BTreeMap<&'a LogicalId,&'a NodeCommon>,depth:usize)->Result<(),CaptionNumberingImportError> {
            if depth>DocumentGraphLimits::default().max_depth{return Err(CaptionNumberingImportError::Limit);}
            for node in &flow.children {
                if matches!(node,Node::Table(_)|Node::EmbeddedObject(_)) {
                    let common=node.common();let anchor=common.source_anchor.as_ref().ok_or(CaptionNumberingImportError::Binding)?;
                    if objects.insert(&anchor.opaque_handle,common).is_some(){return Err(CaptionNumberingImportError::Binding);}
                }
                match node {Node::Table(t)=>for cell in &t.cells{object_nodes(&cell.body,objects,depth+1)?;},
                    Node::Drawing(d)=>object_nodes(&d.children,objects,depth+1)?,_=>{}}
            }Ok(())
        }
    }

    fn run_paragraph(xml:&crate::PreservingXmlDocument,index:usize)->Result<usize,CaptionNumberingImportError> {
        let run=xml.elements()[index].parent().filter(|p|named(&xml.elements()[*p],"run")).ok_or(CaptionNumberingImportError::Coverage)?;
        xml.elements()[run].parent().filter(|p|named(&xml.elements()[*p],"p")).ok_or(CaptionNumberingImportError::Coverage)
    }
    fn require_paragraph(part:&crate::document_import::ImportedSourcePart,index:usize,paragraphs:&BTreeSet<&LogicalId>)->Result<(),CaptionNumberingImportError> {
        let anchor=part.element_anchor(index).ok_or(CaptionNumberingImportError::Binding)?;
        if !paragraphs.contains(&anchor.opaque_handle) {return Err(CaptionNumberingImportError::Coverage);}Ok(())
    }
    fn walk<'a>(flow:&'a Flow,paragraphs:&mut BTreeSet<&'a LogicalId>,depth:usize)->Result<(),CaptionNumberingImportError> {
        if depth>DocumentGraphLimits::default().max_depth {return Err(CaptionNumberingImportError::Limit);}
        for node in &flow.children {match node {
            Node::Paragraph(p)=>{paragraphs.insert(&p.common.source_anchor.as_ref().ok_or(CaptionNumberingImportError::Binding)?.opaque_handle);},
            Node::Table(t)=>for cell in &t.cells {walk(&cell.body,paragraphs,depth+1)?;},
            Node::Drawing(d)=>walk(&d.children,paragraphs,depth+1)?,_=>{},
        }}Ok(())
    }
    fn read_format(node:&crate::XmlElementToken,fingerprint:[u8;32],limits:ReferenceAuxiliaryLimits)->Result<NativeNumberFormatObservation,CaptionNumberingImportError> {
        use CaptionNumberingImportError as E;
        const TYPES:[&str;22]=["DIGIT","CIRCLED_DIGIT","ROMAN_CAPITAL","ROMAN_SMALL","LATIN_CAPITAL","LATIN_SMALL","CIRCLED_LATIN_CAPITAL","CIRCLED_LATIN_SMALL","HANGUL_SYLLABLE","CIRCLED_HANGUL_SYLLABLE","HANGUL_JAMO","CIRCLED_HANGUL_JAMO","HANGUL_PHONETIC","IDEOGRAPH","CIRCLED_IDEOGRAPH","DECAGON_CIRCLE","DECAGON_CIRCLE_HANJA","SYMBOL","USER_CHAR","SYMBOL2","IMAGE","2DIGIT"];
        let native_name=attr(node,"type")?;
        let native_type=*TYPES.iter().find(|t|**t==native_name).ok_or(E::Value)?;
        let typed_format=match native_type {"DIGIT"=>Some(CaptionNumberFormat::Decimal),"CIRCLED_DIGIT"=>Some(CaptionNumberFormat::CircledDecimal),
            "ROMAN_CAPITAL"=>Some(CaptionNumberFormat::RomanUpper),"ROMAN_SMALL"=>Some(CaptionNumberFormat::RomanLower),"LATIN_CAPITAL"=>Some(CaptionNumberFormat::LatinUpper),"LATIN_SMALL"=>Some(CaptionNumberFormat::LatinLower),"HANGUL_SYLLABLE"=>Some(CaptionNumberFormat::HangulSyllable),_=>None};
        let user=attr(node,"userChar")?;let prefix=attr(node,"prefixChar")?;let suffix=attr(node,"suffixChar")?;
        if [user,prefix,suffix].iter().any(|s|s.len()>limits.config().text_bytes) {return Err(E::Limit);}
        let superscript=match attr(node,"supscript")? {"0"|"false"=>false,"1"|"true"=>true,_=>return Err(E::Value)};
        Ok(NativeNumberFormatObservation {native_type,typed_format,user_character_sha256:Sha256::digest(user.as_bytes()).into(),prefix_sha256:Sha256::digest(prefix.as_bytes()).into(),suffix_sha256:Sha256::digest(suffix.as_bytes()).into(),
            affixes_and_user_character_empty:user.is_empty()&&prefix.is_empty()&&suffix.is_empty(),superscript,source_fingerprint_sha256:fingerprint})
    }
}
