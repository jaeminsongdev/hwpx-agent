//! Actual paragraph-local field ranges. Destinations, evaluations and policy
//! are not inferred from cached text, numeric native IDs or opaque parameters.
use std::{collections::BTreeMap, fmt};

use domain_ir::{
    DocumentGraph, DocumentGraphLimits, FieldNode, Flow, Inline, LogicalId, Node, ParagraphNode,
    Properties, PropertyValue, Reference, SourceAnchorHandle,
};
use serde::Serialize;
use thiserror::Error;

use super::{
    ImportedSourcePackage, ImportedSourcePart,
    forms::{FormImportError, ImportedDocumentForms},
};
use crate::{PreservingXmlDocument, XmlAttributeToken, XmlElementToken};

const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const HS: &str = "http://www.hancom.co.kr/hwpml/2011/section";
const PROFILE: &str = "hwpx-agent.document-import-field-ranges/partial-v1";
const SCOPE: &str =
    "observed_source_field_ranges_not_resolved_destinations_evaluation_or_execution";
const MAX_FIELDS: usize = 65_536;
pub const FIELD_RANGE_IMPORT_PROFILE: &str = PROFILE;
pub const FIELD_RANGE_IMPORT_SCOPE: &str = SCOPE;

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedFieldRange {
    pub reference_id: LogicalId,
    pub paragraph_id: LogicalId,
    pub begin_node_id: LogicalId,
    pub end_node_id: LogicalId,
    pub begin_anchor: SourceAnchorHandle,
    pub end_anchor: SourceAnchorHandle,
    pub parameter_anchor: Option<SourceAnchorHandle>,
    pub native_kind: String,
    pub native_begin_id: u32,
    pub parent_reference_id: Option<LogicalId>,
    /// Positions in the original paragraph's unchanged inline sequence. No
    /// nested cached-content copies or invented cached calculation results.
    pub inline_start: usize,
    pub inline_end: usize,
    pub native_header_attributes: Properties,
    pub native_end_attributes: Properties,
}
impl fmt::Debug for ImportedFieldRange {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedFieldRange(<redacted>)")
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FieldRangeImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub source_provenance_sha256: [u8; 32],
    pub original_form_graph_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub field_ranges: usize,
    pub nested_ranges: usize,
    pub parameterized_ranges: usize,
}

/// Borrows the immutable source-backed form/body model. No caller graph/map,
/// deserialization, policy, artifact selector or publication capability.
pub struct ImportedDocumentFields<'a> {
    forms: &'a ImportedDocumentForms,
    graph: DocumentGraph,
    fields: Vec<ImportedFieldRange>,
    receipt: FieldRangeImportReceipt,
}
impl fmt::Debug for ImportedDocumentFields<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedDocumentFields")
            .field("field_ranges", &self.fields.len())
            .finish_non_exhaustive()
    }
}
impl<'a> ImportedDocumentFields<'a> {
    /// Reuses the validated original body/form graph and field header/stack/
    /// parameter-envelope admission. Unrepresented source fields are rejected.
    /// # Errors
    /// Rejects range/source/namespace/wrapper/graph/finite-budget inconsistency.
    pub fn import(forms: &'a ImportedDocumentForms) -> Result<Self, FieldRangeImportError> {
        let mut collected = Collector::new(forms.source());
        for section in forms.graph().sections() {
            collected.flow(&section.body)?;
        }
        let fields = collected.finish()?;
        let mut draft = forms.graph().clone().into_draft();
        let mut replacements = BTreeMap::new();
        for field in &fields {
            let properties = field_properties(field)?;
            draft.references.push(Reference {
                reference_id: field.reference_id.clone(),
                // The field's source start is NOT a resolved hyperlink/crossref
                // destination. Native parameters remain exact uninterpreted.
                target_node_id: None,
                properties: properties.clone(),
            });
            if replacements
                .insert(
                    field.begin_node_id.clone(),
                    (field.reference_id.clone(), properties),
                )
                .is_some()
            {
                return Err(FieldRangeImportError::Binding);
            }
        }
        for section in &mut draft.sections {
            replace_fields(&mut section.body, &mut replacements)?;
        }
        if !replacements.is_empty() {
            return Err(FieldRangeImportError::Binding);
        }
        draft.metadata.insert(
            "field_range_import_profile",
            PropertyValue::Text(PROFILE.into()),
        );
        draft.metadata.insert(
            "field_range_import_scope",
            PropertyValue::Text(SCOPE.into()),
        );
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| FieldRangeImportError::Graph)?;
        let receipt = FieldRangeImportReceipt {
            profile: PROFILE,
            qualification: SCOPE,
            source_package_sha256: forms.receipt().source_package_sha256,
            source_provenance_sha256: forms.receipt().source_provenance_sha256,
            original_form_graph_sha256: forms.receipt().graph_sha256,
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| FieldRangeImportError::Graph)?,
            field_ranges: fields.len(),
            nested_ranges: fields
                .iter()
                .filter(|v| v.parent_reference_id.is_some())
                .count(),
            parameterized_ranges: fields
                .iter()
                .filter(|v| v.parameter_anchor.is_some())
                .count(),
        };
        Ok(Self {
            forms,
            graph,
            fields,
            receipt,
        })
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
    #[must_use]
    pub fn fields(&self) -> &[ImportedFieldRange] {
        &self.fields
    }
    #[must_use]
    pub const fn receipt(&self) -> &FieldRangeImportReceipt {
        &self.receipt
    }
    /// Rebuilds the WHOLE original form/body and derived field graph from fresh
    /// bytes, not just a receipt digest or caller-provided range projection.
    /// # Errors
    /// Rejects source/whole graph/observations/range/receipt drift.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<FieldRangeImportReceipt, FieldRangeImportError> {
        let source = self.forms.source();
        let rebuilt_forms = ImportedDocumentForms::import(
            ImportedSourcePackage::import(
                fresh,
                source.document_id.clone(),
                source.source_sha256,
                source.limits,
            )
            .map_err(FormImportError::from)?,
        )?;
        self.forms.verify_source(fresh)?;
        let rebuilt = ImportedDocumentFields::import(&rebuilt_forms)?;
        if self.graph != rebuilt.graph
            || self.fields != rebuilt.fields
            || self.receipt != rebuilt.receipt
        {
            return Err(FieldRangeImportError::Binding);
        }
        Ok(rebuilt.receipt)
    }
}

struct Collector<'a> {
    source: &'a ImportedSourcePackage,
    fields: Vec<(usize, ImportedFieldRange)>,
    started: usize,
}
struct Pending {
    ordinal: usize,
    node_id: LogicalId,
    reference_id: LogicalId,
    anchor: SourceAnchorHandle,
    parameters: Option<SourceAnchorHandle>,
    kind: String,
    native_id: u32,
    parent: Option<LogicalId>,
    start: usize,
    attributes: Properties,
}
impl<'a> Collector<'a> {
    fn new(source: &'a ImportedSourcePackage) -> Self {
        Self {
            source,
            fields: Vec::new(),
            started: 0,
        }
    }
    fn flow(&mut self, flow: &Flow) -> Result<(), FieldRangeImportError> {
        let nodes: BTreeMap<_, _> = flow
            .children
            .iter()
            .map(|node| (node.common().node_id.clone(), node))
            .collect();
        for node in &flow.children {
            match node {
                Node::Paragraph(p) => self.paragraph(p, &nodes)?,
                Node::Table(t) => {
                    for cell in &t.cells {
                        self.flow(&cell.body)?;
                    }
                }
                Node::Drawing(d) => self.flow(&d.children)?,
                _ => (),
            }
        }
        Ok(())
    }
    fn paragraph(
        &mut self,
        p: &ParagraphNode,
        nodes: &BTreeMap<LogicalId, &Node>,
    ) -> Result<(), FieldRangeImportError> {
        let mut stack: Vec<Pending> = Vec::new();
        for (position, inline) in p.inlines.iter().enumerate() {
            let Inline::ControlRef { node_id } = inline else {
                continue;
            };
            let node = nodes.get(node_id).ok_or(FieldRangeImportError::Binding)?;
            let Some((part, index)) = field_marker(self.source, node)? else {
                continue;
            };
            let xml = part.xml().ok_or(FieldRangeImportError::Binding)?;
            let marker = &xml.elements()[index];
            let marker_anchor = part
                .element_anchor(index)
                .ok_or(FieldRangeImportError::Binding)?;
            if named(marker, "fieldBegin") {
                if self.started >= MAX_FIELDS
                    || stack.len() >= DocumentGraphLimits::default().max_depth
                {
                    return Err(FieldRangeImportError::Limit);
                }
                let parameters = marker
                    .first_child()
                    .map(|i| {
                        part.element_anchor(i)
                            .cloned()
                            .ok_or(FieldRangeImportError::Binding)
                    })
                    .transpose()?;
                let reference = LogicalId::parse(format!(
                    "field-reference-{}",
                    marker_anchor.opaque_handle.as_str()
                ))
                .map_err(|_| FieldRangeImportError::Graph)?;
                stack.push(Pending {
                    ordinal: self.started,
                    node_id: node_id.clone(),
                    reference_id: reference,
                    anchor: marker_anchor.clone(),
                    parameters,
                    kind: attribute(marker, "type")?.into(),
                    native_id: number(marker, "id")?,
                    parent: stack.last().map(|v| v.reference_id.clone()),
                    start: position + 1,
                    attributes: attributes(marker),
                });
                self.started += 1;
            } else {
                let begin = stack.pop().ok_or(FieldRangeImportError::Binding)?;
                if begin.native_id != number(marker, "beginIDRef")? {
                    return Err(FieldRangeImportError::Binding);
                }
                self.fields.push((
                    begin.ordinal,
                    ImportedFieldRange {
                        reference_id: begin.reference_id,
                        paragraph_id: p.common.node_id.clone(),
                        begin_node_id: begin.node_id,
                        end_node_id: node_id.clone(),
                        begin_anchor: begin.anchor,
                        end_anchor: marker_anchor.clone(),
                        parameter_anchor: begin.parameters,
                        native_kind: begin.kind,
                        native_begin_id: begin.native_id,
                        parent_reference_id: begin.parent,
                        inline_start: begin.start,
                        inline_end: position,
                        native_header_attributes: begin.attributes,
                        native_end_attributes: attributes(marker),
                    },
                ));
            }
        }
        if !stack.is_empty() {
            return Err(FieldRangeImportError::Binding);
        }
        Ok(())
    }
    fn finish(mut self) -> Result<Vec<ImportedFieldRange>, FieldRangeImportError> {
        let mut native_begins = 0;
        let mut native_ends = 0;
        for path in self.source.spine() {
            let part = self
                .source
                .parts()
                .iter()
                .find(|p| p.path() == path)
                .ok_or(FieldRangeImportError::Binding)?;
            let Some(xml) = part.xml() else {
                continue;
            };
            let root = &xml.elements()[xml.root_element()];
            if root.name().namespace() != Some(HS) || root.name().local_name() != "sec" {
                continue;
            }
            native_begins += xml
                .elements()
                .iter()
                .filter(|v| named(v, "fieldBegin"))
                .count();
            native_ends += xml
                .elements()
                .iter()
                .filter(|v| named(v, "fieldEnd"))
                .count();
        }
        if native_begins != self.started
            || native_ends != self.fields.len()
            || self.started != self.fields.len()
        {
            return Err(FieldRangeImportError::Unrepresented);
        }
        // The body graph stores a paragraph before its attached tables. Sort
        // by actual spine/element position, not that normalized graph traversal:
        // a table's inner field may precede a later field in the outer paragraph.
        let part_order: BTreeMap<_, _> = self
            .source
            .spine()
            .iter()
            .enumerate()
            .map(|(i, p)| (p.as_str(), i))
            .collect();
        let mut ordered = Vec::new();
        for (_, field) in self.fields {
            let resolved = self
                .source
                .resolve_anchor(&field.begin_anchor)
                .map_err(|_| FieldRangeImportError::Binding)?;
            let part = *part_order
                .get(resolved.part().path().as_str())
                .ok_or(FieldRangeImportError::Binding)?;
            let element = resolved
                .element_index()
                .ok_or(FieldRangeImportError::Binding)?;
            ordered.push(((part, element), field));
        }
        ordered.sort_by_key(|v| v.0);
        Ok(ordered.into_iter().map(|v| v.1).collect())
    }
}

fn field_marker<'a>(
    source: &'a ImportedSourcePackage,
    node: &Node,
) -> Result<Option<(&'a ImportedSourcePart, usize)>, FieldRangeImportError> {
    let anchor = node
        .common()
        .source_anchor
        .as_ref()
        .ok_or(FieldRangeImportError::Binding)?;
    let resolved = source
        .resolve_anchor(anchor)
        .map_err(|_| FieldRangeImportError::Binding)?;
    let wrapper = resolved.element().ok_or(FieldRangeImportError::Binding)?;
    if !named(wrapper, "ctrl") {
        return Ok(None);
    }
    let part = resolved.part();
    let xml = part.xml().ok_or(FieldRangeImportError::Binding)?;
    let children = child_indexes(
        xml,
        resolved
            .element_index()
            .ok_or(FieldRangeImportError::Binding)?,
    )?;
    if !children
        .iter()
        .any(|i| named(&xml.elements()[*i], "fieldBegin") || named(&xml.elements()[*i], "fieldEnd"))
    {
        return Ok(None);
    }
    if children.len() != 1
        || wrapper
            .attributes()
            .iter()
            .any(|v| !v.is_namespace_declaration())
    {
        return Err(FieldRangeImportError::Binding);
    }
    Ok(Some((part, children[0])))
}

fn field_properties(v: &ImportedFieldRange) -> Result<Properties, FieldRangeImportError> {
    let mut properties = Properties::new();
    properties.insert("semantic_qualification", PropertyValue::Text(SCOPE.into()));
    properties.insert("native_kind", PropertyValue::Text(v.native_kind.clone()));
    properties.insert("paragraph_id", PropertyValue::Id(v.paragraph_id.clone()));
    properties.insert("end_node_id", PropertyValue::Id(v.end_node_id.clone()));
    for (key, value) in [
        ("inline_start", v.inline_start),
        ("inline_end", v.inline_end),
    ] {
        properties.insert(
            key,
            PropertyValue::Integer(i64::try_from(value).map_err(|_| FieldRangeImportError::Limit)?),
        );
    }
    properties.insert(
        "native_header_attributes",
        properties_object(&v.native_header_attributes),
    );
    properties.insert(
        "native_end_attributes",
        properties_object(&v.native_end_attributes),
    );
    if let Some(parent) = &v.parent_reference_id {
        properties.insert("parent_reference_id", PropertyValue::Id(parent.clone()));
    }
    if let Some(anchor) = &v.parameter_anchor {
        properties.insert(
            "exact_uninterpreted_parameters_anchor",
            PropertyValue::Id(anchor.opaque_handle.clone()),
        );
    }
    Ok(properties)
}
type Replacements = BTreeMap<LogicalId, (LogicalId, Properties)>;
fn replace_fields(
    flow: &mut Flow,
    replacements: &mut Replacements,
) -> Result<(), FieldRangeImportError> {
    for node in &mut flow.children {
        if let Some((reference_id, properties)) = replacements.remove(&node.common().node_id) {
            if !matches!(node, Node::EmbeddedObject(_)) {
                return Err(FieldRangeImportError::Binding);
            }
            *node = Node::Field(FieldNode {
                common: node.common().clone(),
                reference_id,
                properties,
            });
        }
        match node {
            Node::Table(t) => {
                for cell in &mut t.cells {
                    replace_fields(&mut cell.body, replacements)?;
                }
            }
            Node::Drawing(d) => replace_fields(&mut d.children, replacements)?,
            _ => (),
        }
    }
    Ok(())
}
fn named(v: &XmlElementToken, name: &str) -> bool {
    v.name().namespace() == Some(HP) && v.name().local_name() == name
}
fn attribute<'a>(v: &'a XmlElementToken, name: &str) -> Result<&'a str, FieldRangeImportError> {
    v.attributes()
        .iter()
        .find(|a| a.name().namespace().is_none() && a.name().local_name() == name)
        .map(XmlAttributeToken::semantic_value)
        .ok_or(FieldRangeImportError::Binding)
}
fn number(v: &XmlElementToken, name: &str) -> Result<u32, FieldRangeImportError> {
    attribute(v, name)?
        .parse()
        .map_err(|_| FieldRangeImportError::Binding)
}
fn attributes(v: &XmlElementToken) -> Properties {
    let mut p = Properties::new();
    for a in v
        .attributes()
        .iter()
        .filter(|a| !a.is_namespace_declaration())
    {
        p.insert(
            a.name().qualified_name(),
            PropertyValue::Text(a.semantic_value().into()),
        );
    }
    p
}
fn properties_object(p: &Properties) -> PropertyValue {
    PropertyValue::Object(p.iter().map(|(k, v)| (k.into(), v.clone())).collect())
}
fn child_indexes(
    xml: &PreservingXmlDocument,
    parent: usize,
) -> Result<Vec<usize>, FieldRangeImportError> {
    let mut output = Vec::new();
    let mut child = xml
        .elements()
        .get(parent)
        .ok_or(FieldRangeImportError::Binding)?
        .first_child();
    while let Some(index) = child {
        let v = xml
            .elements()
            .get(index)
            .ok_or(FieldRangeImportError::Binding)?;
        if v.parent() != Some(parent) || output.len() >= xml.elements().len() {
            return Err(FieldRangeImportError::Binding);
        }
        output.push(index);
        child = v.next_sibling();
    }
    Ok(output)
}

#[derive(Debug, Error)]
pub enum FieldRangeImportError {
    #[error("field range original source/form import rejected")]
    Source(#[from] FormImportError),
    #[error("field range source/range binding rejected")]
    Binding,
    #[error("field range source has unrepresented native fields")]
    Unrepresented,
    #[error("field range finite limit exceeded")]
    Limit,
    #[error("field range document graph rejected")]
    Graph,
}
