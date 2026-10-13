//! Original typed header readers plus actual paragraph/run source relationships.
//! No formatting cascade, rendering, defaults, security or execution authority.
use super::{FieldSemanticImportError, ImportedDocumentFieldSemantics};
use crate::{
    CharacterStyleCatalog, CharacterStyleCatalogReader, CharacterStyleLimits,
    HANCOM_2020_HEAD_NAMESPACE, HANCOM_2020_PARAGRAPH_NAMESPACE, ParagraphStyleCatalog,
    ParagraphStyleCatalogReader, ParagraphStyleLimits, PreservingXmlDocument, XmlElementToken,
    document_import::{
        ImportedSourcePackage, ImportedSourcePart,
        fields::ImportedDocumentFields,
        forms::{FormImportError, ImportedDocumentForms},
    },
};
use domain_ir::{
    DocumentGraph, DocumentGraphLimits, Flow, LogicalId, Node, Properties, PropertyValue,
    SourceAnchorHandle, Style,
};
use serde::Serialize;
use std::{collections::BTreeMap, fmt};
use thiserror::Error;

pub const CATALOG_IMPORT_PROFILE: &str = "hwpx-agent.document-import-style-catalog/partial-v1";
pub const CATALOG_IMPORT_SCOPE: &str =
    "original_typed_header_and_source_style_relationships_not_cascade_render_security_full_import_or_execution";

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ImportedCatalogKind {
    NamedStyle,
    ParagraphProperty,
    CharacterProperty,
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedCatalogDefinition {
    pub catalog_id: LogicalId,
    pub kind: ImportedCatalogKind,
    pub native_id: u32,
    pub source_anchor: SourceAnchorHandle,
    pub native_attributes: Properties,
    /// Native nextStyle is a source relationship, NOT based-on inheritance.
    pub relationships: Properties,
}
impl fmt::Debug for ImportedCatalogDefinition {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedCatalogDefinition(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedRunCatalogUse {
    pub source_anchor: SourceAnchorHandle,
    pub character_property: Option<LogicalId>,
}
impl fmt::Debug for ImportedRunCatalogUse {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedRunCatalogUse(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedParagraphCatalogUse {
    pub paragraph_id: LogicalId,
    pub source_anchor: SourceAnchorHandle,
    pub named_style: Option<LogicalId>,
    pub paragraph_property: Option<LogicalId>,
    pub runs: Vec<ImportedRunCatalogUse>,
}
impl fmt::Debug for ImportedParagraphCatalogUse {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedParagraphCatalogUse(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CatalogImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub original_meaning_graph_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub header_anchor_sha256: [u8; 32],
    pub named_styles: usize,
    pub paragraph_properties: usize,
    pub character_properties: usize,
    pub paragraphs: usize,
    pub runs: usize,
    pub explicit_named_style_uses: usize,
    pub explicit_paragraph_property_uses: usize,
    pub explicit_character_property_uses: usize,
}
/// Non-deserializable full source/graph binding. Original typed readers stay exact.
pub struct ImportedDocumentCatalog<'a, 'fields, 'source> {
    meanings: &'a ImportedDocumentFieldSemantics<'fields, 'source>,
    graph: DocumentGraph,
    definitions: Vec<ImportedCatalogDefinition>,
    uses: Vec<ImportedParagraphCatalogUse>,
    characters: CharacterStyleCatalog,
    paragraphs: ParagraphStyleCatalog,
    receipt: CatalogImportReceipt,
}
impl fmt::Debug for ImportedDocumentCatalog<'_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedDocumentCatalog")
            .field("definitions", &self.definitions.len())
            .field("paragraphs", &self.uses.len())
            .finish_non_exhaustive()
    }
}
type DefinitionIndex = BTreeMap<(ImportedCatalogKind, u32), LogicalId>;
struct HeaderCatalog {
    definitions: Vec<ImportedCatalogDefinition>,
    index: DefinitionIndex,
    characters: CharacterStyleCatalog,
    paragraphs: ParagraphStyleCatalog,
    fingerprint: [u8; 32],
}
impl<'a, 'fields, 'source> ImportedDocumentCatalog<'a, 'fields, 'source> {
    /// Reuses whole immutable body/forms/fields/meanings and original P05 readers.
    /// # Errors
    /// Rejects malformed typed header, duplicates/dangling references, source/run
    /// topology or finite graph limits. Missing attributes do not invent defaults.
    pub fn import(
        meanings: &'a ImportedDocumentFieldSemantics<'fields, 'source>,
    ) -> Result<Self, CatalogImportError> {
        let source = meanings.fields.forms.source();
        let header = read_header(source)?;
        let mut draft = meanings.graph().clone().into_draft();
        if !draft.styles.is_empty() {
            return Err(CatalogImportError::Binding);
        }
        for definition in &header.definitions {
            let mut properties = Properties::new();
            properties.insert(
                "source_catalog_kind",
                PropertyValue::Text(match definition.kind {
                    ImportedCatalogKind::NamedStyle => "named_style",
                    ImportedCatalogKind::ParagraphProperty => "paragraph_property",
                    ImportedCatalogKind::CharacterProperty => "character_property",
                }.into()),
            );
            properties.insert("source_anchor", PropertyValue::Id(definition.source_anchor.opaque_handle.clone()));
            properties.insert("native_attributes", object(&definition.native_attributes));
            properties.insert("source_relationships", object(&definition.relationships));
            draft.styles.push(Style {
                style_id: definition.catalog_id.clone(),
                based_on: None,
                properties,
            });
        }
        let mut uses = Vec::new();
        for section in &mut draft.sections {
            attach(source, &header.index, &mut section.body, &mut uses)?;
        }
        for note in &mut draft.notes {
            attach(source, &header.index, &mut note.body, &mut uses)?;
        }
        draft.metadata.insert("style_catalog_import_profile", PropertyValue::Text(CATALOG_IMPORT_PROFILE.into()));
        draft.metadata.insert("style_catalog_import_scope", PropertyValue::Text(CATALOG_IMPORT_SCOPE.into()));
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| CatalogImportError::Graph)?;
        let count = |kind| header.definitions.iter().filter(|v| v.kind == kind).count();
        let receipt = CatalogImportReceipt {
            profile: CATALOG_IMPORT_PROFILE,
            qualification: CATALOG_IMPORT_SCOPE,
            source_package_sha256: meanings.receipt().source_package_sha256,
            original_meaning_graph_sha256: meanings.receipt().graph_sha256,
            graph_sha256: graph.canonical_sha256().map_err(|_| CatalogImportError::Graph)?,
            header_anchor_sha256: header.fingerprint,
            named_styles: count(ImportedCatalogKind::NamedStyle),
            paragraph_properties: count(ImportedCatalogKind::ParagraphProperty),
            character_properties: count(ImportedCatalogKind::CharacterProperty),
            paragraphs: uses.len(),
            runs: uses.iter().map(|v| v.runs.len()).sum(),
            explicit_named_style_uses: uses.iter().filter(|v| v.named_style.is_some()).count(),
            explicit_paragraph_property_uses: uses.iter().filter(|v| v.paragraph_property.is_some()).count(),
            explicit_character_property_uses: uses.iter().flat_map(|v| &v.runs).filter(|v| v.character_property.is_some()).count(),
        };
        Ok(Self {
            meanings, graph, definitions: header.definitions, uses,
            characters: header.characters, paragraphs: header.paragraphs, receipt,
        })
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph { &self.graph }
    #[must_use]
    pub fn definitions(&self) -> &[ImportedCatalogDefinition] { &self.definitions }
    #[must_use]
    pub fn uses(&self) -> &[ImportedParagraphCatalogUse] { &self.uses }
    #[must_use]
    pub const fn character_catalog(&self) -> &CharacterStyleCatalog { &self.characters }
    #[must_use]
    pub const fn paragraph_catalog(&self) -> &ParagraphStyleCatalog { &self.paragraphs }
    #[must_use]
    pub const fn receipt(&self) -> &CatalogImportReceipt { &self.receipt }
    /// Fresh whole source/body/forms/ranges/meanings/header/run graph reconstruction.
    /// # Errors
    /// Rejects source, original reader state, complete graph, uses or receipt drift.
    pub fn verify_source(&self, fresh: &[u8]) -> Result<CatalogImportReceipt, CatalogImportError> {
        self.meanings.verify_source(fresh)?;
        let source = self.meanings.fields.forms.source();
        let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(
            fresh, source.document_id.clone(), source.source_sha256, source.limits,
        ).map_err(FormImportError::from)? )?;
        let fields = ImportedDocumentFields::import(&forms).map_err(FieldSemanticImportError::from)?;
        let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
        let rebuilt = ImportedDocumentCatalog::import(&meanings)?;
        if self.graph != rebuilt.graph || self.definitions != rebuilt.definitions
            || self.uses != rebuilt.uses || self.characters != rebuilt.characters
            || self.paragraphs != rebuilt.paragraphs || self.receipt != rebuilt.receipt {
            return Err(CatalogImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
fn read_header(source: &ImportedSourcePackage) -> Result<HeaderCatalog, CatalogImportError> {
    let part = source.parts().iter().find(|p| p.path().as_str() == "Contents/header.xml")
        .ok_or(CatalogImportError::Header)?;
    let xml = part.xml().ok_or(CatalogImportError::Header)?;
    if !named(element(xml, xml.root_element())?, HANCOM_2020_HEAD_NAMESPACE, "head") {
        return Err(CatalogImportError::Header);
    }
    let (characters, paragraphs) = xml.with_source_bytes(|bytes| {
        let characters = CharacterStyleCatalogReader::read(bytes, CharacterStyleLimits::default())
            .map_err(|e| CatalogImportError::Character { code: e.code() })?;
        let paragraphs = ParagraphStyleCatalogReader::read(bytes, ParagraphStyleLimits::default())
            .map_err(|e| CatalogImportError::Paragraph { code: e.code() })?;
        paragraphs.validate_character_style_references(&characters)
            .map_err(|e| CatalogImportError::Paragraph { code: e.code() })?;
        Ok::<_, CatalogImportError>((characters, paragraphs))
    })?;
    let ref_list = one_child(xml, xml.root_element(), "refList")?;
    let mut definitions = Vec::new();
    let mut index = BTreeMap::new();
    for (kind, container, tag) in [
        (ImportedCatalogKind::NamedStyle, "styles", "style"),
        (ImportedCatalogKind::ParagraphProperty, "paraProperties", "paraPr"),
        (ImportedCatalogKind::CharacterProperty, "charProperties", "charPr"),
    ] {
        let container = one_child(xml, ref_list, container)?;
        let nodes = children(xml, container)?;
        if number(element(xml, container)?, "itemCnt")? as usize != nodes.len() { return Err(CatalogImportError::Count); }
        for node in nodes {
            let element = element(xml, node)?;
            if !named(element, HANCOM_2020_HEAD_NAMESPACE, tag) { return Err(CatalogImportError::Header); }
            if definitions.len() >= DocumentGraphLimits::default().max_styles { return Err(CatalogImportError::Limit); }
            let native_id = number(element, "id")?;
            let source_anchor = part.element_anchor(node).ok_or(CatalogImportError::Binding)?.clone();
            source.resolve_anchor(&source_anchor).map_err(|_| CatalogImportError::Binding)?;
            let catalog_id = LogicalId::parse(format!("catalog-{}", source_anchor.opaque_handle.as_str()))
                .map_err(|_| CatalogImportError::Graph)?;
            if index.insert((kind, native_id), catalog_id.clone()).is_some() { return Err(CatalogImportError::Duplicate); }
            definitions.push(ImportedCatalogDefinition {
                catalog_id, kind, native_id, source_anchor,
                native_attributes: attributes(element), relationships: Properties::new(),
            });
        }
    }
    for definition in &mut definitions {
        match definition.kind {
            ImportedCatalogKind::CharacterProperty => {
                if !characters.styles.iter().any(|v| v.id == definition.native_id) { return Err(CatalogImportError::Binding); }
            }
            ImportedCatalogKind::ParagraphProperty => {
                if !paragraphs.styles.iter().any(|v| v.id == definition.native_id) { return Err(CatalogImportError::Binding); }
            }
            ImportedCatalogKind::NamedStyle => {
                let resolved = source.resolve_anchor(&definition.source_anchor).map_err(|_| CatalogImportError::Binding)?;
                let element = resolved.element().ok_or(CatalogImportError::Binding)?;
                for (key, kind) in [
                    ("charPrIDRef", ImportedCatalogKind::CharacterProperty),
                    ("paraPrIDRef", ImportedCatalogKind::ParagraphProperty),
                    ("nextStyleIDRef", ImportedCatalogKind::NamedStyle),
                ] {
                    let target = lookup(&index, kind, number(element, key)?)?;
                    definition.relationships.insert(key, PropertyValue::Id(target));
                }
            }
        }
    }
    if definitions.iter().filter(|v| v.kind == ImportedCatalogKind::CharacterProperty).count() != characters.styles.len()
        || definitions.iter().filter(|v| v.kind == ImportedCatalogKind::ParagraphProperty).count() != paragraphs.styles.len() {
        return Err(CatalogImportError::Binding);
    }
    Ok(HeaderCatalog { definitions, index, characters, paragraphs, fingerprint: part.anchor().fingerprint_sha256 })
}
fn attach(
    source: &ImportedSourcePackage, index: &DefinitionIndex, flow: &mut Flow,
    uses: &mut Vec<ImportedParagraphCatalogUse>,
) -> Result<(), CatalogImportError> {
    for node in &mut flow.nodes {
        match node {
            Node::Paragraph(paragraph) => {
                if uses.len() >= DocumentGraphLimits::default().max_nodes { return Err(CatalogImportError::Limit); }
                let anchor = paragraph.common.source_anchor.as_ref().ok_or(CatalogImportError::Binding)?;
                let resolved = source.resolve_anchor(anchor).map_err(|_| CatalogImportError::Binding)?;
                let element = resolved.element().ok_or(CatalogImportError::Binding)?;
                if !named(element, HANCOM_2020_PARAGRAPH_NAMESPACE, "p") { return Err(CatalogImportError::Binding); }
                let named_style = optional_lookup(index, ImportedCatalogKind::NamedStyle, element, "styleIDRef")?;
                let paragraph_property = optional_lookup(index, ImportedCatalogKind::ParagraphProperty, element, "paraPrIDRef")?;
                if !paragraph.common.style_refs.is_empty() { return Err(CatalogImportError::Binding); }
                if let Some(style) = &named_style { paragraph.common.style_refs.push(style.clone()); }
                if let Some(property) = &paragraph_property {
                    paragraph.paragraph_properties.insert("source_paragraph_property_catalog", PropertyValue::Id(property.clone()));
                }
                let mut records = paragraph.paragraph_properties.iter().find(|(key, _)| *key == "run_segments")
                    .map(|(_, value)| value.clone()).ok_or(CatalogImportError::Binding)?;
                let PropertyValue::List(ref mut records) = records else { return Err(CatalogImportError::Binding); };
                let xml = resolved.part().xml().ok_or(CatalogImportError::Binding)?;
                let run_indexes = children(xml, resolved.element_index().ok_or(CatalogImportError::Binding)?)?
                    .into_iter().filter(|i| xml.elements().get(*i).is_some_and(|e| named(e, HANCOM_2020_PARAGRAPH_NAMESPACE, "run"))).collect::<Vec<_>>();
                if records.len() != run_indexes.len() { return Err(CatalogImportError::Binding); }
                let mut runs = Vec::new();
                for (record, run) in records.iter_mut().zip(run_indexes) {
                    let PropertyValue::Object(record) = record else { return Err(CatalogImportError::Binding); };
                    let run_anchor = resolved.part().element_anchor(run).ok_or(CatalogImportError::Binding)?.clone();
                    if record.get("source_anchor") != Some(&PropertyValue::Id(run_anchor.opaque_handle.clone())) { return Err(CatalogImportError::Binding); }
                    let character_property = optional_lookup(index, ImportedCatalogKind::CharacterProperty, element_at(xml, run)?, "charPrIDRef")?;
                    if let Some(property) = &character_property {
                        record.insert("source_character_property_catalog".into(), PropertyValue::Id(property.clone()));
                    }
                    runs.push(ImportedRunCatalogUse { source_anchor: run_anchor, character_property });
                }
                paragraph.paragraph_properties.insert("run_segments", PropertyValue::List(records.clone()));
                uses.push(ImportedParagraphCatalogUse {
                    paragraph_id: paragraph.common.node_id.clone(), source_anchor: anchor.clone(), named_style, paragraph_property, runs,
                });
            }
            Node::Table(table) => { for cell in &mut table.cells { attach(source, index, &mut cell.body, uses)?; } }
            Node::Drawing(drawing) => attach(source, index, &mut drawing.children, uses)?,
            _ => (),
        }
    }
    Ok(())
}
fn lookup(index: &DefinitionIndex, kind: ImportedCatalogKind, id: u32) -> Result<LogicalId, CatalogImportError> {
    index.get(&(kind, id)).cloned().ok_or(CatalogImportError::Dangling)
}
fn optional_lookup(index: &DefinitionIndex, kind: ImportedCatalogKind, element: &XmlElementToken, key: &str) -> Result<Option<LogicalId>, CatalogImportError> {
    attribute(element, key).map(|value| {
        let value = parse_number(value)?;
        lookup(index, kind, value)
    }).transpose()
}
fn attribute<'a>(element: &'a XmlElementToken, key: &str) -> Option<&'a str> {
    element.attributes().iter().find(|a| a.name().namespace().is_none() && a.name().local_name() == key)
        .map(crate::XmlAttributeToken::semantic_value)
}
fn parse_number(value: &str) -> Result<u32, CatalogImportError> {
    if value.is_empty() || !value.bytes().all(|b| b.is_ascii_digit()) { return Err(CatalogImportError::Id); }
    value.parse().map_err(|_| CatalogImportError::Id)
}
fn number(element: &XmlElementToken, key: &str) -> Result<u32, CatalogImportError> {
    parse_number(attribute(element, key).ok_or(CatalogImportError::Id)?)
}
fn attributes(element: &XmlElementToken) -> Properties {
    let mut properties = Properties::new();
    for attribute in element.attributes().iter().filter(|a| !a.is_namespace_declaration()) {
        properties.insert(attribute.name().qualified_name(), PropertyValue::Text(attribute.semantic_value().into()));
    }
    properties
}
fn object(properties: &Properties) -> PropertyValue {
    PropertyValue::Object(properties.iter().map(|(key, value)| (key.into(), value.clone())).collect())
}
fn named(element: &XmlElementToken, namespace: &str, local: &str) -> bool {
    element.name().namespace() == Some(namespace) && element.name().local_name() == local
}
fn element(xml: &PreservingXmlDocument, index: usize) -> Result<&XmlElementToken, CatalogImportError> {
    xml.elements().get(index).ok_or(CatalogImportError::Binding)
}
fn element_at(xml: &PreservingXmlDocument, index: usize) -> Result<&XmlElementToken, CatalogImportError> { element(xml, index) }
fn children(xml: &PreservingXmlDocument, parent: usize) -> Result<Vec<usize>, CatalogImportError> {
    let mut next = element(xml, parent)?.first_child();
    let mut children = Vec::new();
    while let Some(index) = next {
        let child = element(xml, index)?;
        if child.parent() != Some(parent) || children.len() >= xml.elements().len() { return Err(CatalogImportError::Binding); }
        children.push(index); next = child.next_sibling();
    }
    Ok(children)
}
fn one_child(xml: &PreservingXmlDocument, parent: usize, tag: &str) -> Result<usize, CatalogImportError> {
    let matches = children(xml, parent)?.into_iter().filter(|i| xml.elements().get(*i).is_some_and(|v| named(v, HANCOM_2020_HEAD_NAMESPACE, tag))).collect::<Vec<_>>();
    if matches.len() != 1 { return Err(CatalogImportError::Header); }
    Ok(matches[0])
}
#[derive(Debug, Error)]
pub enum CatalogImportError {
    #[error("catalog original whole source/form import rejected")]
    Forms(#[from] FormImportError),
    #[error("catalog original field meaning import rejected")]
    Meanings(#[from] FieldSemanticImportError),
    #[error("catalog original character reader rejected: {code}")]
    Character { code: &'static str },
    #[error("catalog original paragraph reader rejected: {code}")]
    Paragraph { code: &'static str },
    #[error("catalog native header shape rejected")]
    Header,
    #[error("catalog declared count mismatch")]
    Count,
    #[error("catalog native numeric identifier rejected")]
    Id,
    #[error("catalog native identifier is duplicated")]
    Duplicate,
    #[error("catalog source relationship is dangling")]
    Dangling,
    #[error("catalog source/graph topology binding rejected")]
    Binding,
    #[error("catalog finite limit exceeded")]
    Limit,
    #[error("catalog domain graph rejected")]
    Graph,
}
