//! Source-backed typed body structure. Unsupported semantics remain explicit
//! exact-source objects, never a claimed complete or execution-ready import.
pub mod bookmarks;
pub mod caption_text;
pub mod caption_text_batch;
pub mod caption_edit_batch;
pub mod caption_style_batch;
pub mod caption_numbering_sequence;
mod caption_edit_map;
pub mod caption_number_topology;
pub mod caption_topology;
pub mod notes;
pub mod note_conversion;
pub mod note_style;
pub mod note_export;
pub mod review;
use std::{collections::BTreeMap, fmt};

use domain_ir::{
    ArtifactRef, DocumentGraph, DocumentGraphDraft, DocumentGraphLimits, EmbeddedObjectNode,
    EmbeddedObjectType, Flow, Inline, LogicalId, Node, NodeCommon, OpaqueExtension,
    OpaquePreservation, ParagraphNode, Properties, PropertyValue, Resource, ResourceKind, Section,
    TableCell, TableNode,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use super::{ImportedSourcePackage, ImportedSourcePart, SourceImportError, hex_digest};
use crate::{
    HANCOM_2020_PARAGRAPH_NAMESPACE, ParagraphChild, PreservingXmlDocument, TableLayoutHwpxLimits,
    TableLayoutHwpxReader, TextAtom, TextFlowLimits, TextFlowReader, TextRunItem, TextSpan,
    XmlElementToken,
};

pub const STRUCTURE_IMPORT_PROFILE: &str = "hwpx-agent.document-import-structure/partial-v1";
pub const STRUCTURE_IMPORT_SCOPE: &str = "source_backed_body_structure_not_complete_typed_document";
const SECTION_NS: &str = "http://www.hancom.co.kr/hwpml/2011/section";

/// Owns the actual source and validated typed graph together. Neither can be
/// replaced by deserialization. Graph serialization is document data, not logs.
pub struct ImportedDocumentStructure {
    source: ImportedSourcePackage,
    graph: DocumentGraph,
    receipt: StructureImportReceipt,
    notes: Vec<notes::ImportedNoteObservation>,
    bookmarks: Vec<bookmarks::ImportedBookmarkObservation>,
    section_flows: Vec<ImportedSectionFlowObservation>,
}

impl fmt::Debug for ImportedDocumentStructure {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedDocumentStructure")
            .field("paragraphs", &self.receipt.paragraphs)
            .field("tables", &self.receipt.tables)
            .field("opaque_nodes", &self.receipt.opaque_nodes)
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StructureImportReceipt {
    pub profile: &'static str,
    pub scope: &'static str,
    pub source_package_sha256: [u8; 32],
    pub source_provenance_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub sections: usize,
    pub paragraphs: usize,
    pub tables: usize,
    pub table_cells: usize,
    pub opaque_nodes: usize,
    pub preserved_parts: usize,
    pub non_section_spine_parts: usize,
}

/// Exact source XML topology, not page layout, protection or complete typed flow.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedSectionFlowObservation {
    profile: &'static str,
    section_id: LogicalId,
    paragraphs: u32,
    runs: usize,
    inline_elements: usize,
    run_topology_sha256: [u8; 32],
    inline_topology_sha256: [u8; 32],
    source_part_fingerprint_sha256: [u8; 32],
    page_assignment_sha256: Option<[u8; 32]>,
    locked: Option<bool>,
    complete_document_flow_qualified: bool,
}
impl fmt::Debug for ImportedSectionFlowObservation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedSectionFlowObservation(<redacted>; source_topology_only)")
    }
}
impl ImportedSectionFlowObservation {
    #[must_use]
    pub const fn section_id(&self) -> &LogicalId { &self.section_id }
    #[must_use]
    pub const fn paragraphs(&self) -> u32 { self.paragraphs }
    #[must_use]
    pub const fn runs(&self) -> usize { self.runs }
    #[must_use]
    pub const fn inline_elements(&self) -> usize { self.inline_elements }
    #[must_use]
    pub const fn run_topology_sha256(&self) -> [u8; 32] { self.run_topology_sha256 }
    #[must_use]
    pub const fn inline_topology_sha256(&self) -> [u8; 32] { self.inline_topology_sha256 }
}

impl ImportedDocumentStructure {
    /// Converts actual source positions without a caller graph or numeric-ID
    /// identity assumptions. Native catalog/security/control semantics remain
    /// unqualified; this profile MUST NOT be used as full-document route input.
    /// # Errors
    /// Rejects bad supported paragraph/table semantics, unrecognized section
    /// roots, incorrect source bindings and domain graph budget/shape failures.
    pub fn import(source: ImportedSourcePackage) -> Result<Self, StructureImportError> {
        let mut mapper = Mapper::new(&source);
        let mut sections = Vec::new();
        let mut non_section_spine_parts = 0;
        for path in source.spine() {
            let part = source
                .parts()
                .iter()
                .find(|part| part.path() == path)
                .ok_or(StructureImportError::Binding)?;
            let xml = part.xml().ok_or(StructureImportError::Section)?;
            let root = element(xml, xml.root_element())?;
            if root.name().namespace() != Some(SECTION_NS) || root.name().local_name() != "sec" {
                // Header/master/other non-section spine entries are retained in
                // the complete source/resources, not invented as body sections.
                non_section_spine_parts += 1;
                continue;
            }
            let mut properties = attributes(root);
            properties.insert(
                "source_part",
                PropertyValue::Id(id("resource", part.anchor())?),
            );
            let section_id = id("section", part.anchor())?;
            mapper.index_section_paragraphs(part, section_id.clone())?;
            sections.push(Section {
                section_id,
                properties,
                master_pages: vec![],
                headers_footers: vec![],
                body: mapper.flow(part, xml.root_element(), 1)?,
            });
        }
        if sections.is_empty() {
            return Err(StructureImportError::Section);
        }
        let mut draft = DocumentGraphDraft::new(source.document_id().clone(), sections);
        draft.source_profile = Some(
            LogicalId::parse(STRUCTURE_IMPORT_PROFILE).map_err(|_| StructureImportError::Graph)?,
        );
        draft
            .metadata
            .insert("scope", PropertyValue::Text(STRUCTURE_IMPORT_SCOPE.into()));
        draft.metadata.insert(
            "source_package_sha256",
            PropertyValue::Text(hex_digest(source.receipt().source_package_sha256)),
        );
        draft.metadata.insert(
            "source_provenance_sha256",
            PropertyValue::Text(hex_digest(source.receipt().provenance_sha256)),
        );
        draft.security_state.properties.insert(
            "qualification",
            PropertyValue::Text("native_security_unqualified_no_unprotected_attestation".into()),
        );
        add_preserved_parts(&source, &mut draft)?;
        notes::finish_notes(&source, &mut draft, &mapper.note_observations)?;
        bookmarks::finish_bookmarks(&source, &mut draft, &mapper.bookmarks)?;
        draft.notes = std::mem::take(&mut mapper.notes);
        let notes = std::mem::take(&mut mapper.note_observations);
        let bookmarks = std::mem::take(&mut mapper.bookmarks);
        let section_flows = std::mem::take(&mut mapper.section_flows);
        let stats = mapper.stats;
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| StructureImportError::Graph)?;
        let receipt = StructureImportReceipt {
            profile: STRUCTURE_IMPORT_PROFILE,
            scope: STRUCTURE_IMPORT_SCOPE,
            source_package_sha256: source.receipt().source_package_sha256,
            source_provenance_sha256: source.receipt().provenance_sha256,
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| StructureImportError::Graph)?,
            sections: graph.sections().len(),
            paragraphs: stats.paragraphs,
            tables: stats.tables,
            table_cells: stats.table_cells,
            opaque_nodes: stats.opaque_nodes,
            preserved_parts: source.parts().len(),
            non_section_spine_parts,
        };
        Ok(Self {
            source,
            graph,
            receipt,
            notes,
            bookmarks,
            section_flows,
        })
    }

    #[must_use]
    pub const fn source(&self) -> &ImportedSourcePackage {
        &self.source
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
    #[must_use]
    pub const fn receipt(&self) -> &StructureImportReceipt {
        &self.receipt
    }

    #[must_use]
    pub fn notes(&self) -> &[notes::ImportedNoteObservation] {
        &self.notes
    }

    #[must_use]
    pub fn bookmarks(&self) -> &[bookmarks::ImportedBookmarkObservation] {
        &self.bookmarks
    }

    #[must_use]
    pub fn section_flows(&self) -> &[ImportedSectionFlowObservation] {
        &self.section_flows
    }

    /// Selects exactly one raw observed source name, not a native jump target.
    /// # Errors
    /// Rejects absent or ambiguous names without normalizing or picking the first.
    pub fn observed_bookmark_by_name(
        &self,
        name: &str,
    ) -> Result<&bookmarks::ImportedBookmarkObservation, StructureImportError> {
        let mut matches = self.bookmarks.iter().filter(|v| v.name == name);
        let found = matches
            .next()
            .ok_or(StructureImportError::BookmarkSelection)?;
        if matches.next().is_some() {
            return Err(StructureImportError::BookmarkSelection);
        }
        Ok(found)
    }

    /// Reimports the whole actual source and reconstructs the typed graph.
    /// # Errors
    /// Rejects any source/graph/state/anchor/count difference, never rebinds it.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<StructureImportReceipt, StructureImportError> {
        let rebuilt_source = ImportedSourcePackage::import(
            fresh,
            self.source.document_id.clone(),
            self.source.source_sha256,
            self.source.limits,
        )?;
        if rebuilt_source != self.source {
            return Err(StructureImportError::Binding);
        }
        let rebuilt = Self::import(rebuilt_source)?;
        if rebuilt.graph != self.graph || rebuilt.receipt != self.receipt
            || rebuilt.section_flows != self.section_flows {
            return Err(StructureImportError::Binding);
        }
        Ok(rebuilt.receipt)
    }
}

#[derive(Default)]
struct Stats {
    paragraphs: usize,
    tables: usize,
    table_cells: usize,
    opaque_nodes: usize,
    nodes: usize,
}

struct Mapper<'a> {
    source: &'a ImportedSourcePackage,
    stats: Stats,
    notes: Vec<domain_ir::Note>,
    note_observations: Vec<notes::ImportedNoteObservation>,
    bookmarks: Vec<bookmarks::ImportedBookmarkObservation>,
    source_section_id: Option<LogicalId>,
    source_paragraph_order: Vec<usize>,
    section_flows: Vec<ImportedSectionFlowObservation>,
}

impl<'a> Mapper<'a> {
    fn new(source: &'a ImportedSourcePackage) -> Self {
        Self {
            source,
            stats: Stats::default(),
            notes: Vec::new(),
            note_observations: Vec::new(),
            bookmarks: Vec::new(),
            source_section_id: None,
            source_paragraph_order: Vec::new(),
            section_flows: Vec::new(),
        }
    }

    // Match the existing bookmark lowerer's XML-element paragraph order. Notes
    // are detached and inline objects are attached later in the typed graph,
    // so traversing that graph cannot supply original paragraph ordinals.
    fn index_section_paragraphs(
        &mut self,
        part: &ImportedSourcePart,
        section_id: LogicalId,
    ) -> Result<(), StructureImportError> {
        self.source_paragraph_order.clear();
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        for (index, native) in xml.elements().iter().enumerate() {
            if named(native, "p") {
                if self.source_paragraph_order.len() >= DocumentGraphLimits::default().max_nodes {
                    return Err(StructureImportError::Limit);
                }
                self.source_paragraph_order.try_reserve(1)
                    .map_err(|_| StructureImportError::Limit)?;
                self.source_paragraph_order.push(index);
            }
        }
        let mut run_hash = Sha256::new();
        let mut inline_hash = Sha256::new();
        topology_frame(&mut run_hash, b"source-section-run-topology/v1");
        topology_frame(&mut inline_hash, b"source-section-inline-topology/v1");
        let (mut runs, mut inline_elements) = (0usize, 0usize);
        for (ordinal, &paragraph) in self.source_paragraph_order.iter().enumerate() {
            let ordinal = u32::try_from(ordinal).map_err(|_| StructureImportError::Limit)?;
            topology_frame(&mut run_hash, &ordinal.to_be_bytes());
            let mut run_count = 0u32;
            let mut child = element(xml, paragraph)?.first_child();
            while let Some(index) = child {
                let native = element(xml, index)?;
                child = native.next_sibling();
                if !named(native, "run") { continue; }
                topology_frame(&mut inline_hash, b"run");
                topology_frame(&mut inline_hash, &ordinal.to_be_bytes());
                topology_frame(&mut inline_hash, &run_count.to_be_bytes());
                run_count = run_count.checked_add(1).ok_or(StructureImportError::Limit)?;
                let mut inline_count = 0u32;
                let mut inline = native.first_child();
                while let Some(index) = inline {
                    let item = element(xml, index)?;
                    inline = item.next_sibling();
                    if transparent_source_bookmark(xml, index)? { continue; }
                    topology_frame(&mut inline_hash, b"item");
                    topology_frame(&mut inline_hash, item.name().namespace().unwrap_or("").as_bytes());
                    topology_frame(&mut inline_hash, item.name().local_name().as_bytes());
                    inline_count = inline_count.checked_add(1).ok_or(StructureImportError::Limit)?;
                }
                topology_frame(&mut inline_hash, b"run_end");
                topology_frame(&mut inline_hash, &inline_count.to_be_bytes());
                inline_elements = inline_elements.checked_add(inline_count as usize)
                    .ok_or(StructureImportError::Limit)?;
            }
            topology_frame(&mut run_hash, &run_count.to_be_bytes());
            runs = runs.checked_add(run_count as usize).ok_or(StructureImportError::Limit)?;
        }
        self.section_flows.try_reserve(1).map_err(|_| StructureImportError::Limit)?;
        self.section_flows.push(ImportedSectionFlowObservation {
            profile: "hwpx-agent.document-import-source-section-topology/partial-v1",
            section_id: section_id.clone(),
            paragraphs: u32::try_from(self.source_paragraph_order.len()).map_err(|_| StructureImportError::Limit)?,
            runs, inline_elements,
            run_topology_sha256: run_hash.finalize().into(),
            inline_topology_sha256: inline_hash.finalize().into(),
            source_part_fingerprint_sha256: part.anchor().fingerprint_sha256,
            page_assignment_sha256: None,
            locked: None,
            complete_document_flow_qualified: false,
        });
        self.source_section_id = Some(section_id);
        Ok(())
    }

    fn flow(
        &mut self,
        part: &ImportedSourcePart,
        parent: usize,
        depth: usize,
    ) -> Result<Flow, StructureImportError> {
        Self::check_depth(depth)?;
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        let mut nodes = Vec::new();
        for index in children(xml, parent)? {
            nodes.extend(self.node(part, index, depth)?);
        }
        Ok(Flow { children: nodes })
    }

    fn node(
        &mut self,
        part: &ImportedSourcePart,
        index: usize,
        depth: usize,
    ) -> Result<Vec<Node>, StructureImportError> {
        Self::check_depth(depth)?;
        self.stats.nodes += 1;
        if self.stats.nodes > DocumentGraphLimits::default().max_nodes {
            return Err(StructureImportError::Limit);
        }
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        let item = element(xml, index)?;
        if named(item, "p") {
            self.paragraph(part, index, depth)
        } else if named(item, "tbl") {
            Ok(vec![self.table(part, index, depth)?])
        } else {
            Ok(vec![self.opaque(part, index)?])
        }
    }

    fn common(
        &self,
        part: &ImportedSourcePart,
        index: usize,
    ) -> Result<NodeCommon, StructureImportError> {
        let anchor = part
            .element_anchor(index)
            .ok_or(StructureImportError::Binding)?;
        self.source.resolve_anchor(anchor)?;
        let mut common = NodeCommon::new(id("node", anchor)?);
        common.source_anchor = Some(anchor.clone());
        common.preserve = OpaquePreservation::PreserveExact;
        common.resource_refs.push(id("resource", part.anchor())?);
        Ok(common)
    }

    fn opaque(
        &mut self,
        part: &ImportedSourcePart,
        index: usize,
    ) -> Result<Node, StructureImportError> {
        self.stats.opaque_nodes += 1;
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        let native = element(xml, index)?;
        let mut properties = Properties::new();
        properties.insert("native_attributes", properties_object(&attributes(native)));
        properties.insert(
            "semantic_qualification",
            PropertyValue::Text("unmapped_exact_source_not_typed_control".into()),
        );
        properties.insert(
            "source_local_name",
            PropertyValue::Text(native.name().local_name().into()),
        );
        if let Some(namespace) = native.name().namespace() {
            properties.insert("source_namespace", PropertyValue::Text(namespace.into()));
        }
        Ok(Node::EmbeddedObject(EmbeddedObjectNode {
            common: self.common(part, index)?,
            object_type: EmbeddedObjectType::Xml,
            resource_id: id("resource", part.anchor())?,
            properties,
        }))
    }

    fn paragraph(
        &mut self,
        part: &ImportedSourcePart,
        index: usize,
        depth: usize,
    ) -> Result<Vec<Node>, StructureImportError> {
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        let read = TextFlowReader::read_preserving_xml_context(xml, index, TextFlowLimits::default())
            .map_err(|error| StructureImportError::Paragraph { code: error.code() })?;
        let indexes = children(xml, index)?;
        if indexes.len() != read.children.len() {
            return Err(StructureImportError::Binding);
        }
        let mut inlines = Vec::new();
        let mut attached = Vec::new();
        let mut segments = Vec::new();
        for (child, child_index) in read.children.iter().zip(indexes) {
            if let ParagraphChild::Run(run) = child {
                let start = inlines.len();
                let mut text_segments = Vec::new();
                let run_indexes = children(xml, child_index)?;
                if run_indexes.len() != run.items.len() {
                    return Err(StructureImportError::Binding);
                }
                for (item, item_index) in run.items.iter().zip(run_indexes) {
                    match item {
                        TextRunItem::Text(text) => {
                            text_segments.push(append_text(part, item_index, text, &mut inlines)?);
                        }
                        _ => self.inline_object(
                            part,
                            item_index,
                            depth,
                            &mut inlines,
                            &mut attached,
                        )?,
                    }
                }
                let mut record = BTreeMap::new();
                record.insert("text_segments".into(), PropertyValue::List(text_segments));
                record.insert(
                    "inline_start".into(),
                    PropertyValue::Integer(
                        i64::try_from(start).map_err(|_| StructureImportError::Limit)?,
                    ),
                );
                record.insert(
                    "inline_end".into(),
                    PropertyValue::Integer(
                        i64::try_from(inlines.len()).map_err(|_| StructureImportError::Limit)?,
                    ),
                );
                record.insert(
                    "native_attributes".into(),
                    properties_object(&attributes(element(xml, child_index)?)),
                );
                record.insert(
                    "source_anchor".into(),
                    PropertyValue::Id(
                        part.element_anchor(child_index)
                            .ok_or(StructureImportError::Binding)?
                            .opaque_handle
                            .clone(),
                    ),
                );
                segments.push(PropertyValue::Object(record));
            } else {
                self.inline_object(part, child_index, depth, &mut inlines, &mut attached)?;
            }
        }
        let mut properties = attributes(element(xml, index)?);
        properties.insert("run_segments", PropertyValue::List(segments));
        self.stats.paragraphs += 1;
        let paragraph = Node::Paragraph(ParagraphNode {
            common: self.common(part, index)?,
            inlines,
            paragraph_properties: properties,
        });
        let mut output = vec![paragraph];
        output.extend(attached);
        Ok(output)
    }

    fn inline_object(
        &mut self,
        part: &ImportedSourcePart,
        index: usize,
        depth: usize,
        inlines: &mut Vec<Inline>,
        attached: &mut Vec<Node>,
    ) -> Result<(), StructureImportError> {
        if self.note_wrapper(part, index, depth, inlines, attached)? {
            return Ok(());
        }
        if self.bookmark_wrapper(part, index, inlines, attached)? {
            return Ok(());
        }
        let nodes = self.node(part, index, depth + 1)?;
        let first = nodes.first().ok_or(StructureImportError::Binding)?;
        inlines.push(Inline::ControlRef {
            node_id: first.common().node_id.clone(),
        });
        attached.extend(nodes);
        Ok(())
    }

    fn table(
        &mut self,
        part: &ImportedSourcePart,
        index: usize,
        depth: usize,
    ) -> Result<Node, StructureImportError> {
        let xml = part.xml().ok_or(StructureImportError::Binding)?;
        // Reuse the actual grid validator on the same immutable native tree,
        // without serializing/reparsing a whole section once per nested table.
        let read =
            TableLayoutHwpxReader::read_from_document(xml, index, TableLayoutHwpxLimits::default())
                .map_err(|error| StructureImportError::Table { code: error.code() })?;
        let mut cells = Vec::new();
        for row in children(xml, index)? {
            if !named(element(xml, row)?, "tr") {
                continue;
            }
            for cell in children(xml, row)? {
                if !named(element(xml, cell)?, "tc") {
                    return Err(StructureImportError::Binding);
                }
                let address = child_named(xml, cell, "cellAddr")?;
                let span = child_named(xml, cell, "cellSpan")?;
                let row = number(element(xml, address)?, "rowAddr")?;
                let column = number(element(xml, address)?, "colAddr")?;
                let row_span = number(element(xml, span)?, "rowSpan")?;
                let column_span = number(element(xml, span)?, "colSpan")?;
                if !read.cells.iter().any(|actual| {
                    actual.row == row
                        && actual.column == column
                        && actual.row_span == row_span
                        && actual.column_span == column_span
                }) {
                    return Err(StructureImportError::Binding);
                }
                cells.push(TableCell {
                    cell_id: id(
                        "cell",
                        part.element_anchor(cell)
                            .ok_or(StructureImportError::Binding)?,
                    )?,
                    row,
                    column,
                    row_span,
                    column_span,
                    body: self.flow(part, child_named(xml, cell, "subList")?, depth + 1)?,
                    properties: attributes(element(xml, cell)?),
                });
            }
        }
        if cells.len() != read.cells.len() {
            return Err(StructureImportError::Binding);
        }
        self.stats.tables += 1;
        self.stats.table_cells += cells.len();
        let mut properties = attributes(element(xml, index)?);
        properties.insert(
            "width_hwpunit",
            PropertyValue::Integer(i64::from(read.table_width_hwpunit)),
        );
        properties.insert(
            "height_hwpunit",
            PropertyValue::Integer(i64::from(read.table_height_hwpunit)),
        );
        Ok(Node::Table(TableNode {
            common: self.common(part, index)?,
            rows: read.rows,
            columns: read.columns,
            cells,
            properties,
        }))
    }

    fn check_depth(depth: usize) -> Result<(), StructureImportError> {
        if depth > DocumentGraphLimits::default().max_depth {
            Err(StructureImportError::Limit)
        } else {
            Ok(())
        }
    }
}

fn topology_frame(hash: &mut Sha256, bytes: &[u8]) {
    // Source-import byte limits are below the platform's u64 length bound.
    hash.update((bytes.len() as u64).to_be_bytes());
    hash.update(bytes);
}

fn transparent_source_bookmark(
    xml: &PreservingXmlDocument,
    index: usize,
) -> Result<bool, StructureImportError> {
    let wrapper = element(xml, index)?;
    if !named(wrapper, "ctrl") { return Ok(false); }
    let Some(child) = wrapper.first_child() else { return Ok(false) };
    let marker = element(xml, child)?;
    Ok(named(marker, "bookmark") && marker.next_sibling().is_none())
}

fn id(
    prefix: &str,
    anchor: &domain_ir::SourceAnchorHandle,
) -> Result<LogicalId, StructureImportError> {
    LogicalId::parse(format!("{prefix}-{}", anchor.opaque_handle.as_str()))
        .map_err(|_| StructureImportError::Graph)
}

fn element(
    xml: &PreservingXmlDocument,
    index: usize,
) -> Result<&XmlElementToken, StructureImportError> {
    xml.elements()
        .get(index)
        .ok_or(StructureImportError::Binding)
}

fn named(node: &XmlElementToken, name: &str) -> bool {
    node.name().namespace() == Some(HANCOM_2020_PARAGRAPH_NAMESPACE)
        && node.name().local_name() == name
}

fn children(xml: &PreservingXmlDocument, index: usize) -> Result<Vec<usize>, StructureImportError> {
    let parent = element(xml, index)?;
    let end = parent.end_token().unwrap_or(parent.start_token());
    if xml.tokens()[parent.start_token()..=end]
        .iter()
        .any(|token| {
            token.element_index() == Some(index)
                && matches!(
                    token.kind(),
                    crate::XmlTokenKind::Text | crate::XmlTokenKind::Reference
                )
        })
    {
        return Err(StructureImportError::Binding);
    }
    let mut child = element(xml, index)?.first_child();
    let mut output = Vec::new();
    while let Some(current) = child {
        let node = element(xml, current)?;
        if node.parent() != Some(index) || output.len() >= xml.elements().len() {
            return Err(StructureImportError::Binding);
        }
        output.push(current);
        child = node.next_sibling();
    }
    Ok(output)
}

fn child_named(
    xml: &PreservingXmlDocument,
    parent: usize,
    name: &str,
) -> Result<usize, StructureImportError> {
    let found = children(xml, parent)?
        .into_iter()
        .filter(|index| {
            xml.elements()
                .get(*index)
                .is_some_and(|node| named(node, name))
        })
        .collect::<Vec<_>>();
    if found.len() != 1 {
        return Err(StructureImportError::Binding);
    }
    Ok(found[0])
}

fn attributes(node: &XmlElementToken) -> Properties {
    let mut values = Properties::new();
    for attribute in node
        .attributes()
        .iter()
        .filter(|attribute| !attribute.is_namespace_declaration())
    {
        values.insert(
            attribute.name().qualified_name(),
            PropertyValue::Text(attribute.semantic_value().into()),
        );
    }
    values
}

fn add_preserved_parts(
    source: &ImportedSourcePackage,
    draft: &mut DocumentGraphDraft,
) -> Result<(), StructureImportError> {
    for part in &source.graph.parts {
        let actual = source
            .parts()
            .iter()
            .find(|item| item.path() == &part.path)
            .ok_or(StructureImportError::Binding)?;
        let mut metadata = Properties::new();
        metadata.insert(
            "source_path",
            PropertyValue::Text(part.path.as_str().into()),
        );
        draft.resources.push(Resource {
            resource_id: id("resource", actual.anchor())?,
            kind: if actual.xml().is_some() {
                ResourceKind::Xml
            } else {
                ResourceKind::Other
            },
            artifact: Some(ArtifactRef {
                sha256: part.raw_sha256,
                byte_length: part.expanded_size,
                media_type: part.media_type.as_str().into(),
            }),
            metadata,
        });
        draft.opaque_preservation_bag.push(OpaqueExtension {
            handle: id("preserved-part", actual.anchor())?,
            sha256: part.raw_sha256,
            byte_length: part.expanded_size,
            preservation: OpaquePreservation::PreserveExact,
        });
    }
    Ok(())
}

fn append_text(
    part: &ImportedSourcePart,
    index: usize,
    text: &TextSpan,
    inlines: &mut Vec<Inline>,
) -> Result<PropertyValue, StructureImportError> {
    let start = inlines.len();
    let mut atom_metadata = Vec::new();
    for atom in &text.atoms {
        let mut metadata = BTreeMap::new();
        let inline = match atom {
            TextAtom::Text(value) => {
                metadata.insert("kind".into(), PropertyValue::Text("text".into()));
                Inline::Text {
                    text: value.clone(),
                }
            }
            TextAtom::Tab {
                width,
                leader,
                tab_type,
            } => {
                metadata.insert("kind".into(), PropertyValue::Text("tab".into()));
                for (key, value) in [("width", width), ("leader", leader), ("type", tab_type)] {
                    metadata.insert(key.into(), PropertyValue::Integer(i64::from(*value)));
                }
                Inline::Tab
            }
            TextAtom::LineBreak => {
                metadata.insert("kind".into(), PropertyValue::Text("line_break".into()));
                Inline::LineBreak
            }
        };
        inlines.push(inline);
        atom_metadata.push(PropertyValue::Object(metadata));
    }
    let xml = part.xml().ok_or(StructureImportError::Binding)?;
    let mut segment = BTreeMap::new();
    for (key, value) in [("inline_start", start), ("inline_end", inlines.len())] {
        segment.insert(
            key.into(),
            PropertyValue::Integer(i64::try_from(value).map_err(|_| StructureImportError::Limit)?),
        );
    }
    segment.insert(
        "native_attributes".into(),
        properties_object(&attributes(element(xml, index)?)),
    );
    segment.insert(
        "source_anchor".into(),
        PropertyValue::Id(
            part.element_anchor(index)
                .ok_or(StructureImportError::Binding)?
                .opaque_handle
                .clone(),
        ),
    );
    segment.insert("atom_metadata".into(), PropertyValue::List(atom_metadata));
    Ok(PropertyValue::Object(segment))
}

fn properties_object(properties: &Properties) -> PropertyValue {
    PropertyValue::Object(
        properties
            .iter()
            .map(|(key, value)| (key.into(), value.clone()))
            .collect(),
    )
}

fn number(node: &XmlElementToken, key: &str) -> Result<u32, StructureImportError> {
    let value = node
        .attributes()
        .iter()
        .find(|attribute| {
            attribute.name().namespace().is_none() && attribute.name().local_name() == key
        })
        .ok_or(StructureImportError::Binding)?;
    value
        .semantic_value()
        .parse()
        .map_err(|_| StructureImportError::Binding)
}

#[derive(Debug, Error)]
pub enum StructureImportError {
    #[error("structure import source validation failed")]
    Source(#[from] SourceImportError),
    #[error("structure import source binding is inconsistent")]
    Binding,
    #[error("structure import has no admitted native section")]
    Section,
    #[error("structure import paragraph semantics rejected: {code}")]
    Paragraph { code: &'static str },
    #[error("structure import table semantics rejected: {code}")]
    Table { code: &'static str },
    #[error("structure import note source envelope rejected: {code}")]
    Note { code: &'static str },
    #[error("structure import point bookmark rejected: {code}")]
    Bookmark { code: &'static str },
    #[error("structure import observed bookmark name is absent or ambiguous")]
    BookmarkSelection,
    #[error("structure import document graph rejected")]
    Graph,
    #[error("structure import finite limit exceeded")]
    Limit,
}

/// Frozen text candidates, not dynamic PATH fields or a full auxiliary route.
pub mod file_literal {
    use super::{ImportedDocumentStructure, attributes, named};
    use crate::{BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact, PackageGraphLimits,
        PatchIntent, PatchLimits, PatchText, PreservationRuleProfile, PreservingPatchEngine,
        PreservingWriter, ValidatedXmlFragment, WriterError, WriterLimits, XmlElementSelector};
    use crate::document_import::ImportedSourcePackage;
    use domain_ir::{DocumentGraphLimits, Flow, LinkPoint, LogicalId, Node, ReferenceAuxiliaryLimits, SourceAnchorHandle};
    use serde::Serialize;
    use sha2::{Digest as _, Sha256};
    use std::{collections::BTreeMap, fmt, io::Cursor};
    use thiserror::Error;

    #[derive(Clone, Debug, Eq, PartialEq, Serialize)]
    pub struct FileLiteralOutputReceipt {
        pub qualification: &'static str,
        pub source_package_sha256: [u8; 32],
        pub output_package_sha256: [u8; 32],
        pub source_run_attributes_sha256: [u8; 32],
        pub source_paragraph_attributes_sha256: [u8; 32],
        pub literal_sha256: [u8; 32],
        pub output_bytes: usize,
        pub outside_selected_run_exact: bool,
        pub source_style_attributes_preserved: bool,
        pub source_file_metadata_authenticated: bool,
        pub complete_auxiliary_state_verified: bool,
        pub execution_publication_authority: bool,
    }
    pub struct FileLiteralOutputCandidate {
        artifact: PackageArtifact,
        receipt: FileLiteralOutputReceipt,
    }
    impl fmt::Debug for FileLiteralOutputCandidate {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("FileLiteralOutputCandidate(<redacted>; candidate_only)") }
    }
    impl FileLiteralOutputCandidate {
        #[must_use]
        pub const fn receipt(&self) -> &FileLiteralOutputReceipt { &self.receipt }
        /// Artifact integrity only, not stored access, commit or execution authority.
        /// # Errors
        /// Does not expose bytes after original writer integrity failure.
        pub fn with_verified_bytes<T>(&self, consume: impl FnOnce(&[u8]) -> T) -> Result<T, WriterError> {
            self.artifact.with_verified_bytes(consume)
        }
    }
    #[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
    pub enum FileLiteralOutputError {
        #[error("FILE_LITERAL_SOURCE_REJECTED")] Source,
        #[error("FILE_LITERAL_SELECTION_REJECTED")] Selection,
        #[error("FILE_LITERAL_VALUE_REJECTED")] Value,
        #[error("FILE_LITERAL_FINITE_LIMIT")] Limit,
        #[error("FILE_LITERAL_PATCH_REJECTED")] Patch,
        #[error("FILE_LITERAL_WRITER_REJECTED")] Writer,
        #[error("FILE_LITERAL_READBACK_REJECTED")] Readback,
        #[error("FILE_LITERAL_PRESERVATION_REJECTED")] Preservation,
    }
    struct Selection<'a> {
        part: &'a super::super::ImportedSourcePart,
        paragraph: usize,
        run: usize,
        children: Vec<usize>,
    }
    impl ImportedDocumentStructure {
        /// Inserts caller-supplied frozen leaf-name text at an actual native run
        /// child boundary. Existing attributes and all bytes outside the run stay
        /// exact. Namespace declarations are copied into the standalone run patch.
        /// No filename lookup, dynamic field, source overwrite or authority occurs.
        /// # Errors
        /// Rejects stale source, unrepresented/foreign/out-of-range positions,
        /// observed protection, invalid leaf names, budgets and original writer/readback failure.
        pub fn lower_file_literal_candidate(
            &self, fresh: &[u8], section: &LogicalId, point: LinkPoint, literal: &str,
            limits: ReferenceAuxiliaryLimits, writer_limits: WriterLimits,
        ) -> Result<FileLiteralOutputCandidate, FileLiteralOutputError> {
            if literal.is_empty() || literal.len() > limits.config().text_bytes {
                return Err(FileLiteralOutputError::Limit);
            }
            if literal.chars().any(|c| c.is_control() || matches!(c, '/' | '\\' | ':')) {
                return Err(FileLiteralOutputError::Value);
            }
            let _ = PatchText::new(literal).map_err(|_| FileLiteralOutputError::Value)?;
            self.verify_source(fresh).map_err(|_| FileLiteralOutputError::Source)?;
            let selected = select(self, section, point)?;
            let xml = selected.part.xml().ok_or(FileLiteralOutputError::Selection)?;
            super::review::cell_body_output::require_no_observed_mutation_protection(xml, selected.run)
                .map_err(|_| FileLiteralOutputError::Selection)?;
            let run = &xml.elements()[selected.run];
            let outer = run.outer_span().ok_or(FileLiteralOutputError::Selection)?;
            let tag = run.start_tag_span();
            let boundary = usize::try_from(point.inline_ordinal).map_err(|_| FileLiteralOutputError::Selection)?;
            let offset = if let Some(&child) = selected.children.get(boundary) {
                xml.elements()[child].outer_span().ok_or(FileLiteralOutputError::Selection)?.start()
            } else { run.content_span().map_or(tag.end(), |span| span.end()) };
            // A plain text node inside an existing field is a cache, not a frozen
            // standalone filename. Reuse the original whole field-pair importer.
            let package = ImportedSourcePackage::import(fresh, self.source().document_id().clone(),
                self.source().receipt().source_package_sha256, self.source().limits).map_err(|_| FileLiteralOutputError::Source)?;
            let forms = crate::document_import::forms::ImportedDocumentForms::import(package).map_err(|_| FileLiteralOutputError::Source)?;
            let fields = crate::document_import::fields::ImportedDocumentFields::import(&forms).map_err(|_| FileLiteralOutputError::Selection)?;
            for field in fields.fields() {
                let begin = forms.source().resolve_anchor(&field.begin_anchor).map_err(|_| FileLiteralOutputError::Selection)?;
                let end = forms.source().resolve_anchor(&field.end_anchor).map_err(|_| FileLiteralOutputError::Selection)?;
                if begin.part().path() != selected.part.path() { continue; }
                let first = begin.element().and_then(crate::XmlElementToken::outer_span).ok_or(FileLiteralOutputError::Selection)?;
                let last = end.element().and_then(crate::XmlElementToken::outer_span).ok_or(FileLiteralOutputError::Selection)?;
                if first.start() <= offset && offset < last.end() { return Err(FileLiteralOutputError::Selection); }
            }
            let mut namespaces = BTreeMap::new();
            let mut current = Some(selected.run);
            while let Some(index) = current {
                let element = &xml.elements()[index];
                for attr in element.attributes().iter().filter(|a| a.is_namespace_declaration()) {
                    namespaces.entry(attr.name().qualified_name().to_owned()).or_insert_with(|| attr.semantic_value().to_owned());
                }
                current = element.parent();
            }
            for attr in run.attributes().iter().filter(|a| a.is_namespace_declaration()) {
                namespaces.remove(attr.name().qualified_name());
            }
            let declarations: String = namespaces.iter().map(|(name, uri)| format!(" {name}=\"{}\"", quick_xml::escape::escape(uri))).collect();
            let text = format!("<hp:t xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\">{}</hp:t>", quick_xml::escape::escape(literal));
            let expected = xml.with_source_bytes(|raw| -> Result<Vec<u8>, FileLiteralOutputError> {
                let closing_extra = if run.is_empty() { run.name().qualified_name().len() + 2 } else { 0 };
                let extra = declarations.len().checked_add(text.len()).and_then(|n| n.checked_add(closing_extra)).ok_or(FileLiteralOutputError::Limit)?;
                let capacity = outer.len().checked_add(extra).filter(|n| *n <= PatchLimits::default().config().max_fragment_bytes)
                    .ok_or(FileLiteralOutputError::Limit)?;
                let mut bytes = Vec::new();
                bytes.try_reserve_exact(capacity).map_err(|_| FileLiteralOutputError::Limit)?;
                let end = tag.end() - if run.is_empty() { 2 } else { 1 };
                bytes.extend_from_slice(&raw[outer.start()..end]);
                bytes.extend_from_slice(declarations.as_bytes()); bytes.extend_from_slice(b">");
                if !run.is_empty() { bytes.extend_from_slice(&raw[tag.end()..offset]); }
                bytes.extend_from_slice(text.as_bytes());
                if run.is_empty() {
                    bytes.extend_from_slice(b"</"); bytes.extend_from_slice(run.name().qualified_name().as_bytes()); bytes.extend_from_slice(b">");
                } else { bytes.extend_from_slice(&raw[offset..outer.end()]); }
                Ok(bytes)
            })?;
            let fragment = ValidatedXmlFragment::parse(&expected, PatchLimits::default()).map_err(|_| FileLiteralOutputError::Patch)?;
            let target = XmlElementSelector::bind(selected.part.path(), xml, selected.run).map_err(|_| FileLiteralOutputError::Selection)?;
            let source = self.source();
            let zip = source.limits.zip().map_err(|_| FileLiteralOutputError::Source)?;
            let mut reader = BoundedZipReader::open(Cursor::new(fresh), zip).map_err(|_| FileLiteralOutputError::Source)?;
            let patch = PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader, &source.graph,
                PackageGraphLimits::default(), IdRuleProfile::current_hancom_2020_formula_v3(), IdIndexLimits::default(),
                PatchLimits::default(), PreservationRuleProfile::Hangul2020PreviewTextV2, &[PatchIntent::ReplaceSubtree { target, fragment }])
                .map_err(|_| FileLiteralOutputError::Patch)?;
            if patch.changed_parts() != 1 || patch.added_parts() != 0 || patch.parts().iter().any(|p|
                p.path() != selected.part.path() && p.source_sha256() != Some(p.output_sha256())) {
                return Err(FileLiteralOutputError::Preservation);
            }
            let artifact = PreservingWriter::build(&patch, zip, PackageGraphLimits::default(), IdIndexLimits::default(), writer_limits)
                .map_err(|_| FileLiteralOutputError::Writer)?;
            artifact.with_verified_bytes(|bytes| -> Result<(), FileLiteralOutputError> {
                let package = ImportedSourcePackage::import(bytes, source.document_id().clone(), Sha256::digest(bytes).into(), source.limits)
                    .map_err(|_| FileLiteralOutputError::Readback)?;
                let rebuilt = Self::import(package).map_err(|_| FileLiteralOutputError::Readback)?;
                // Source-bound section IDs change with package SHA. The selected
                // original part path, not a guessed native numeric ID, locates the output section.
                let part = rebuilt.source().parts().iter().find(|p| p.path() == selected.part.path()).ok_or(FileLiteralOutputError::Readback)?;
                let output_xml = part.xml().ok_or(FileLiteralOutputError::Readback)?;
                let paragraphs: Vec<_> = output_xml.elements().iter().enumerate().filter(|(_,e)| named(e,"p")).map(|(i,_)| i).collect();
                let paragraph = *paragraphs.get(point.paragraph_ordinal as usize).ok_or(FileLiteralOutputError::Readback)?;
                let run_index = child_runs(output_xml, paragraph).get(point.run_ordinal as usize).copied().ok_or(FileLiteralOutputError::Readback)?;
                let output_run = &output_xml.elements()[run_index];
                let span = output_run.outer_span().ok_or(FileLiteralOutputError::Readback)?;
                let exact = output_xml.with_source_bytes(|after| xml.with_source_bytes(|before|
                    before[..outer.start()] == after[..span.start()] && before[outer.end()..] == after[span.end()..]
                    && after[span.start()..span.end()] == expected));
                if !exact || attributes(run) != attributes(output_run) || attributes(&xml.elements()[selected.paragraph]) != attributes(&output_xml.elements()[paragraph]) {
                    return Err(FileLiteralOutputError::Preservation);
                }
                Ok(())
            }).map_err(|_| FileLiteralOutputError::Writer)??;
            self.verify_source(fresh).map_err(|_| FileLiteralOutputError::Source)?;
            let digest = |value: &domain_ir::Properties| -> Result<[u8;32], FileLiteralOutputError> {
                Ok(Sha256::digest(serde_json::to_vec(value).map_err(|_| FileLiteralOutputError::Limit)?).into())
            };
            let receipt = FileLiteralOutputReceipt {
                qualification: "source_bound_frozen_text_candidate_not_authenticated_filename_complete_auxiliary_operation_or_authority",
                source_package_sha256: source.receipt().source_package_sha256,
                output_package_sha256: artifact.sha256(), source_run_attributes_sha256: digest(&attributes(run))?,
                source_paragraph_attributes_sha256: digest(&attributes(&xml.elements()[selected.paragraph]))?,
                literal_sha256: Sha256::digest(literal.as_bytes()).into(), output_bytes: artifact.size_bytes(),
                outside_selected_run_exact: true, source_style_attributes_preserved: true,
                source_file_metadata_authenticated: false, complete_auxiliary_state_verified: false, execution_publication_authority: false,
            };
            Ok(FileLiteralOutputCandidate { artifact, receipt })
        }
    }
    fn child_runs(xml: &crate::PreservingXmlDocument, paragraph: usize) -> Vec<usize> {
        let mut result = Vec::new(); let mut child = xml.elements()[paragraph].first_child();
        while let Some(index) = child { if named(&xml.elements()[index], "run") { result.push(index); } child = xml.elements()[index].next_sibling(); }
        result
    }
    fn represented(flow: &Flow, anchor: &SourceAnchorHandle, depth: usize) -> bool {
        if depth > DocumentGraphLimits::default().max_depth { return false; }
        flow.children.iter().any(|node| match node {
            Node::Paragraph(p) => p.common.source_anchor.as_ref() == Some(anchor),
            Node::Table(t) => t.cells.iter().any(|c| represented(&c.body, anchor, depth+1)),
            Node::Drawing(d) => represented(&d.children, anchor, depth+1), _ => false,
        })
    }
    fn select<'a>(source: &'a ImportedDocumentStructure, section: &LogicalId, point: LinkPoint) -> Result<Selection<'a>, FileLiteralOutputError> {
        let section = source.graph().sections().iter().find(|s| &s.section_id == section).ok_or(FileLiteralOutputError::Selection)?;
        let part_id = section.properties.iter().find(|(key,_)| *key == "source_part")
            .and_then(|(_,v)| if let domain_ir::PropertyValue::Id(id)=v {Some(id)} else {None}).ok_or(FileLiteralOutputError::Selection)?;
        let part = source.source().parts().iter().find(|p| part_id.as_str() == format!("resource-{}", p.anchor().opaque_handle.as_str())).ok_or(FileLiteralOutputError::Selection)?;
        let xml = part.xml().ok_or(FileLiteralOutputError::Selection)?;
        let paragraph = xml.elements().iter().enumerate().filter(|(_,e)| named(e,"p")).nth(point.paragraph_ordinal as usize).map(|(i,_)|i).ok_or(FileLiteralOutputError::Selection)?;
        let anchor = part.element_anchor(paragraph).ok_or(FileLiteralOutputError::Selection)?;
        if !represented(&section.body, anchor, 0) && !source.graph().notes().iter().any(|n| represented(&n.body, anchor, 0)) { return Err(FileLiteralOutputError::Selection); }
        let run = child_runs(xml, paragraph).get(point.run_ordinal as usize).copied().ok_or(FileLiteralOutputError::Selection)?;
        let mut children = Vec::new(); let mut next = xml.elements()[run].first_child();
        while let Some(index) = next { children.push(index); next = xml.elements()[index].next_sibling(); }
        if point.inline_ordinal as usize > children.len() { return Err(FileLiteralOutputError::Selection); }
        Ok(Selection { part, paragraph, run, children })
    }
}

/// Native caption layout only. Numbering/content changes require a separate
/// semantic compiler; this candidate never authorizes a product route.
pub mod caption_layout {
    use super::ImportedDocumentStructure;
    use crate::{BoundedZipReader, IdIndexLimits, IdRuleProfile, PackageArtifact,
        PackageGraphLimits, PatchAttributeValue, PatchIntent, PatchLimits, PatchText,
        PreservationRuleProfile, PreservingPatchEngine, PreservingWriter,
        WriterError, WriterLimits, XmlAttributeSelector, XmlByteSpan};
    use crate::document_import::{ImportedSourcePackage, reference_targets::captions::ImportedReferenceCaptions};
    use domain_ir::{LogicalId, NativeCaptionSide, ReferenceAuxiliaryLimits};
    use serde::Serialize;
    use sha2::{Digest as _, Sha256};
    use std::{fmt, io::Cursor};
    use thiserror::Error;

    #[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
    pub struct CaptionLayout {
        pub side: NativeCaptionSide,
        pub full_size: bool,
        pub width_hwpunit: i32,
        pub gap_hwpunit: u32,
        pub last_width_hwpunit: u32,
    }
    #[derive(Clone, Debug, Eq, PartialEq, Serialize)]
    pub struct CaptionLayoutOutputReceipt {
        pub qualification: &'static str,
        pub source_package_sha256: [u8;32],
        pub output_package_sha256: [u8;32],
        pub source_caption_sha256: String,
        pub output_caption_sha256: String,
        pub preserved_sub_list_sha256: String,
        pub id_rule_profile: &'static str,
        pub changed_attributes: usize,
        pub output_bytes: usize,
        pub outside_selected_attribute_values_exact: bool,
        pub numbering_and_caption_content_preserved: bool,
        pub complete_auxiliary_state_and_protection_verified: bool,
        pub execution_publication_authority: bool,
    }
    pub struct CaptionLayoutOutputCandidate {
        artifact: PackageArtifact,
        receipt: CaptionLayoutOutputReceipt,
    }
    impl fmt::Debug for CaptionLayoutOutputCandidate {
        fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionLayoutOutputCandidate(<redacted>; layout_only)")}
    }
    impl CaptionLayoutOutputCandidate {
        #[must_use] pub const fn receipt(&self)->&CaptionLayoutOutputReceipt {&self.receipt}
        /// Writer integrity only, not service authorization or durable publication.
        /// # Errors
        /// Rejects original writer integrity failures before exposing bytes.
        pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {
            self.artifact.with_verified_bytes(consume)
        }
    }
    #[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
    pub enum CaptionLayoutOutputError {
        #[error("CAPTION_LAYOUT_SOURCE_REJECTED")] Source,
        #[error("CAPTION_LAYOUT_SELECTION_REJECTED")] Selection,
        #[error("CAPTION_LAYOUT_OBSERVED_PROTECTION")] Protection,
        #[error("CAPTION_LAYOUT_VALUE_REJECTED")] Value,
        #[error("CAPTION_LAYOUT_NO_CHANGE")] NoChange,
        #[error("CAPTION_LAYOUT_FINITE_LIMIT")] Limit,
        #[error("CAPTION_LAYOUT_PATCH_REJECTED:{0}")] Patch(&'static str),
        #[error("CAPTION_LAYOUT_WRITER_REJECTED")] Writer,
        #[error("CAPTION_LAYOUT_READBACK_REJECTED")] Readback,
        #[error("CAPTION_LAYOUT_PRESERVATION_REJECTED")] Preservation,
    }
    impl ImportedDocumentStructure {
        /// Changes only the five admitted native layout attribute values on one
        /// source-anchor-selected caption. Native IDs are never selectors.
        /// Original attribute quotes/order, unknown attrs, namespaces, numbering,
        /// text, owner and every other expanded package part remain byte-exact.
        /// Does not overwrite source or qualify complete caption sequencing.
        /// # Errors
        /// Rejects stale/foreign source, unrepresented selection, observed locks,
        /// invalid/bounded layout, no-op, patch/writer and complete readback drift.
        pub fn lower_caption_layout_candidate(&self,fresh:&[u8],caption_id:&LogicalId,
            layout:CaptionLayout,limits:ReferenceAuxiliaryLimits,writer_limits:WriterLimits,
        )->Result<CaptionLayoutOutputCandidate,CaptionLayoutOutputError> {
            self.lower_caption_layout_checked(fresh,caption_id,layout,limits,writer_limits,
                ||self.verify_source(fresh).map(|_|()).map_err(|_|CaptionLayoutOutputError::Source))
        }
        fn lower_caption_layout_checked(&self,fresh:&[u8],caption_id:&LogicalId,
            layout:CaptionLayout,limits:ReferenceAuxiliaryLimits,writer_limits:WriterLimits,
            check_source:impl FnOnce()->Result<(),CaptionLayoutOutputError>,
        )->Result<CaptionLayoutOutputCandidate,CaptionLayoutOutputError> {
            use CaptionLayoutOutputError as E;
            if layout.width_hwpunit < -1 {return Err(E::Value);}
            if layout.width_hwpunit.max(0) as u32>limits.config().extent_hwpunit
                ||layout.gap_hwpunit>limits.config().extent_hwpunit
                ||layout.last_width_hwpunit>limits.config().extent_hwpunit {return Err(E::Limit);}
            check_source()?;
            let captions=ImportedReferenceCaptions::import(self,limits).map_err(|error|match error {
                crate::document_import::reference_targets::captions::ReferenceCaptionImportError::Limit=>E::Limit,_=>E::Source})?;
            let ordinal=captions.envelopes().iter().position(|c|c.logical_caption_id()==caption_id).ok_or(E::Selection)?;
            let before=captions.envelopes()[ordinal].native_envelope();
            let mut selected=None;
            for part in self.source().parts() {
                let Some(xml)=part.xml() else {continue};
                for (index,element) in xml.elements().iter().enumerate() {
                    if !super::named(element,"caption") {continue;}
                    let anchor=part.element_anchor(index).ok_or(E::Selection)?;
                    if caption_id.as_str()==format!("caption-{}",anchor.opaque_handle.as_str()) {
                        if selected.replace((part,xml,index)).is_some() {return Err(E::Selection);}
                    }
                }
            }
            let (part,xml,index)=selected.ok_or(E::Selection)?;
            super::review::cell_body_output::require_no_observed_mutation_protection(xml,index).map_err(|_|E::Protection)?;
            // Object locks apply to layout edits too, including objects inside
            // protected tables. An unknown lexical lock value is not false.
            let mut ancestor=Some(index);
            while let Some(current)=ancestor {
                let node=&xml.elements()[current];
                if node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)
                    && node.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="lock"
                        && !matches!(a.semantic_value(),"0"|"false")) {return Err(E::Protection);}
                ancestor=node.parent();
            }
            let node=&xml.elements()[index];
            let values=[("side",match layout.side {NativeCaptionSide::Left=>"LEFT",NativeCaptionSide::Right=>"RIGHT",NativeCaptionSide::Top=>"TOP",NativeCaptionSide::Bottom=>"BOTTOM"}.to_owned()),
                ("fullSz",if layout.full_size {"1"} else {"0"}.to_owned()),
                ("width",layout.width_hwpunit.to_string()),("gap",layout.gap_hwpunit.to_string()),("lastWidth",layout.last_width_hwpunit.to_string())];
            let mut edits=Vec::with_capacity(5); let mut changes=Vec::with_capacity(5);
            for (name,value) in values {
                let attribute=node.attributes().iter().enumerate().find(|(_,a)|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()==name).ok_or(E::Source)?;
                // Equivalent booleans preserve their original lexical spelling.
                let same=match name {"side"=>before.side==layout.side,"fullSz"=>before.full_size==layout.full_size,
                    "width"=>before.width_hwpunit==layout.width_hwpunit,"gap"=>before.gap_hwpunit==layout.gap_hwpunit,
                    "lastWidth"=>before.last_width_hwpunit==layout.last_width_hwpunit,_=>return Err(E::Value)};
                if same {continue;}
                edits.push(PatchIntent::ReplaceAttribute {target:XmlAttributeSelector::bind(part.path(),xml,index,attribute.0).map_err(|_|E::Selection)?,
                    value:PatchAttributeValue::Text(PatchText::new(&value).map_err(|_|E::Value)?)});
                changes.push((attribute.1.value_span(),value));
            }
            if edits.is_empty() {return Err(E::NoChange);}
            changes.sort_by_key(|(span,_)|span.start());
            let output_len=xml.with_source_bytes(|raw|changes.iter().try_fold(raw.len(),|n,(span,value)|n.checked_sub(span.len()).and_then(|n|n.checked_add(value.len())))).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
            let source=self.source(); let zip=source.limits.zip().map_err(|_|E::Source)?;
            let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;
            let id_profile=IdRuleProfile::hwpml_2011_shape_v6();
            let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,
                PackageGraphLimits::default(),id_profile,IdIndexLimits::default(),PatchLimits::default(),
                PreservationRuleProfile::Hangul2020PreviewTextV2,&edits).map_err(|error| {
                    let code=if let crate::PatchError::IdIndex(ref ids)=error {ids.validation().and_then(|r|r.issues().first()).map_or(error.code(),|issue|issue.code())} else {error.code()};
                    E::Patch(code)
                })?;
            if patch.changed_parts()!=1||patch.added_parts()!=0||patch.parts().iter().any(|p|p.path()!=part.path()&&p.source_sha256()!=Some(p.output_sha256())) {return Err(E::Preservation);}
            let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer_limits).map_err(|_|E::Writer)?;
            let output_caption=artifact.with_verified_bytes(|bytes|->Result<String,E> {
                let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
                let rebuilt=ImportedDocumentStructure::import(output).map_err(|_|E::Readback)?;
                let after=ImportedReferenceCaptions::import(&rebuilt,limits).map_err(|_|E::Readback)?;
                if after.envelopes().len()!=captions.envelopes().len() {return Err(E::Readback);}
                let observed=after.envelopes()[ordinal].native_envelope();
                if observed.side!=layout.side||observed.full_size!=layout.full_size||observed.width_hwpunit!=layout.width_hwpunit
                    ||observed.gap_hwpunit!=layout.gap_hwpunit||observed.last_width_hwpunit!=layout.last_width_hwpunit
                    ||observed.sub_list_sha256!=before.sub_list_sha256||observed.semantic_binding!=before.semantic_binding {return Err(E::Readback);}
                let output_part=rebuilt.source().parts().iter().find(|p|p.path()==part.path()).and_then(|p|p.xml()).ok_or(E::Readback)?;
                if !xml.with_source_bytes(|old|output_part.with_source_bytes(|new|new.len()==output_len&&exact_edits(old,new,&changes))) {return Err(E::Preservation);}
                Ok(observed.opaque_native_state_sha256.clone())
            }).map_err(|_|E::Writer)??;
            let receipt=CaptionLayoutOutputReceipt {qualification:"source_bound_layout_only_candidate_numbering_content_preserved_not_complete_caption_operation_or_authority",
                source_package_sha256:source.receipt().source_package_sha256,output_package_sha256:artifact.sha256(),
                source_caption_sha256:before.opaque_native_state_sha256.clone(),output_caption_sha256:output_caption,
                preserved_sub_list_sha256:before.sub_list_sha256.clone(),id_rule_profile:id_profile.version(),changed_attributes:edits.len(),output_bytes:artifact.size_bytes(),
                outside_selected_attribute_values_exact:true,numbering_and_caption_content_preserved:true,
                complete_auxiliary_state_and_protection_verified:false,execution_publication_authority:false};
            Ok(CaptionLayoutOutputCandidate {artifact,receipt})
        }
    }
    impl crate::document_import::forms::VerifiedFormReconstruction<'_> {
        /// Reuses a complete, operation-local reconstruction of this exact
        /// original form model. No caller graph, verification flag, new parse or
        /// saved service authorization. Output keeps the original full readback.
        /// # Errors
        /// Rejects a foreign original/proof, different fresh bytes and every
        /// original layout, protection, ID, writer or preservation failure.
        pub fn lower_caption_layout_candidate(&self,
            original:&crate::document_import::forms::ImportedDocumentForms,
            fresh:&[u8],caption_id:&LogicalId,layout:CaptionLayout,
            limits:ReferenceAuxiliaryLimits,writer_limits:WriterLimits,
        )->Result<CaptionLayoutOutputCandidate,CaptionLayoutOutputError> {
            original.body_structure().lower_caption_layout_checked(fresh,caption_id,layout,limits,writer_limits,|| {
                let rebuilt=self.for_original(original).map_err(|_|CaptionLayoutOutputError::Source)?;
                if fresh!=rebuilt.source().original.as_ref() {return Err(CaptionLayoutOutputError::Source);}
                Ok(())
            })
        }
    }
    // Streaming comparison of five bounded edits: no full expected-section clone
    // or per-caption XML reparse; both source and output were fully imported.
    fn exact_edits(old:&[u8],new:&[u8],changes:&[(XmlByteSpan,String)])->bool {
        let (mut before,mut after)=(0_usize,0_usize);
        for (span,value) in changes {
            let Some(unchanged)=old.get(before..span.start()) else {return false};
            let Some(end)=after.checked_add(unchanged.len()) else {return false};
            if new.get(after..end)!=Some(unchanged) {return false;}
            after=end; let Some(end)=after.checked_add(value.len()) else {return false};
            if new.get(after..end)!=Some(value.as_bytes()) {return false;}
            before=span.end();after=end;
        }
        new.get(after..)==old.get(before..)
    }
}
