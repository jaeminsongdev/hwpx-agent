//! Source-backed typed body structure. Unsupported semantics remain explicit
//! exact-source objects, never a claimed complete or execution-ready import.
use std::{collections::BTreeMap, fmt};

use domain_ir::{
    ArtifactRef, DocumentGraph, DocumentGraphDraft, DocumentGraphLimits, EmbeddedObjectNode,
    EmbeddedObjectType, Flow, Inline, LogicalId, Node, NodeCommon, OpaqueExtension,
    OpaquePreservation, ParagraphNode, Properties, PropertyValue, Resource, ResourceKind, Section,
    TableCell, TableNode,
};
use serde::Serialize;
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
            sections.push(Section {
                section_id: id("section", part.anchor())?,
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
        if rebuilt.graph != self.graph || rebuilt.receipt != self.receipt {
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
}

impl<'a> Mapper<'a> {
    fn new(source: &'a ImportedSourcePackage) -> Self {
        Self {
            source,
            stats: Stats::default(),
        }
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
        let read = TextFlowReader::read_from_document(xml, index, TextFlowLimits::default())
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
    #[error("structure import document graph rejected")]
    Graph,
    #[error("structure import finite limit exceeded")]
    Limit,
}
