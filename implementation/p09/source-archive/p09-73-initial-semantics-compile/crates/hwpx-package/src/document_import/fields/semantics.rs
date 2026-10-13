//! Source-derived typed meanings, not cached evaluation or execution authority.
use std::{collections::BTreeMap, fmt};
use domain_ir::{
    DocumentGraph, DocumentGraphLimits, Flow, FormulaCell, FormulaGridDimensions,
    HyperlinkTarget, LogicalId, Node, PropertyValue,
};
use serde::Serialize;
use thiserror::Error;
use super::{FieldRangeImportError, ImportedDocumentFields, ImportedFieldRange};
use crate::document_import::{ImportedSourcePackage, forms::{FormImportError, ImportedDocumentForms}};

pub const FIELD_SEMANTICS_PROFILE: &str = "hwpx-agent.document-import-field-semantics/partial-v1";
pub const FIELD_SEMANTICS_SCOPE: &str = "source_https_target_and_table_formula_ast_not_approval_evaluation_full_import_or_execution";
const MAX_WORK_ELEMENTS: usize = 8_000_000;

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "meaning", rename_all = "snake_case")]
pub enum ImportedFieldMeaning {
    HttpsTarget { target: HyperlinkTarget },
    TableFormula { dimensions: FormulaGridDimensions, formula: FormulaCell },
    /// The range and exact parameters survive; no claimed complete meaning.
    Unsupported { native_kind: String },
}
impl fmt::Debug for ImportedFieldMeaning {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedFieldMeaning(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedFieldSemantic {
    pub reference_id: LogicalId,
    pub meaning: ImportedFieldMeaning,
}
impl fmt::Debug for ImportedFieldSemantic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedFieldSemantic(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FieldSemanticImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub field_graph_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub ranges: usize,
    pub https_targets: usize,
    pub table_formula_asts: usize,
    pub unsupported_meanings: usize,
}
/// Immutable, non-deserializable source-derived model. No graph/URI/formula
/// supplied by the caller. Existing partial and security qualifiers survive.
pub struct ImportedDocumentFieldSemantics<'a, 'source> {
    fields: &'a ImportedDocumentFields<'source>,
    graph: DocumentGraph,
    observations: Vec<ImportedFieldSemantic>,
    receipt: FieldSemanticImportReceipt,
}
impl fmt::Debug for ImportedDocumentFieldSemantics<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedDocumentFieldSemantics")
            .field("ranges", &self.observations.len()).finish_non_exhaustive()
    }
}
impl<'a, 'source> ImportedDocumentFieldSemantics<'a, 'source> {
    /// # Errors
    /// Rejects malformed supported meanings, source binding, budget or graph
    /// inconsistency. Unknown kinds remain explicit, never omitted or approved.
    pub fn import(fields: &'a ImportedDocumentFields<'source>) -> Result<Self, FieldSemanticImportError> {
        let mut observations = Vec::new();
        let mut work = 0usize;
        let mut replacements = BTreeMap::new();
        for range in fields.fields() {
            let meaning = read_meaning(fields, range, &mut work)?;
            let value = serde_json::to_value(&meaning).map_err(|_| FieldSemanticImportError::Graph)?;
            let property = property_value(value)?;
            replacements.insert(range.begin_node_id.clone(), property);
            observations.push(ImportedFieldSemantic { reference_id: range.reference_id.clone(), meaning });
        }
        let mut draft = fields.graph().clone().into_draft();
        for (reference, observation) in draft.references.iter_mut().zip(&observations) {
            if reference.reference_id != observation.reference_id {
                return Err(FieldSemanticImportError::Binding);
            }
            reference.properties.insert("source_derived_meaning", property_value(
                serde_json::to_value(&observation.meaning).map_err(|_| FieldSemanticImportError::Graph)?
            )?);
        }
        if draft.references.len() != observations.len() { return Err(FieldSemanticImportError::Binding); }
        for section in &mut draft.sections { attach_meanings(&mut section.body, &mut replacements)?; }
        if !replacements.is_empty() { return Err(FieldSemanticImportError::Binding); }
        draft.metadata.insert("field_semantics_import_profile", PropertyValue::Text(FIELD_SEMANTICS_PROFILE.into()));
        draft.metadata.insert("field_semantics_import_scope", PropertyValue::Text(FIELD_SEMANTICS_SCOPE.into()));
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| FieldSemanticImportError::Graph)?;
        let receipt = FieldSemanticImportReceipt {
            profile: FIELD_SEMANTICS_PROFILE, qualification: FIELD_SEMANTICS_SCOPE,
            source_package_sha256: fields.receipt().source_package_sha256,
            field_graph_sha256: fields.receipt().graph_sha256,
            graph_sha256: graph.canonical_sha256().map_err(|_| FieldSemanticImportError::Graph)?,
            ranges: observations.len(),
            https_targets: observations.iter().filter(|v| matches!(v.meaning, ImportedFieldMeaning::HttpsTarget { .. })).count(),
            table_formula_asts: observations.iter().filter(|v| matches!(v.meaning, ImportedFieldMeaning::TableFormula { .. })).count(),
            unsupported_meanings: observations.iter().filter(|v| matches!(v.meaning, ImportedFieldMeaning::Unsupported { .. })).count(),
        };
        Ok(Self { fields, graph, observations, receipt })
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph { &self.graph }
    #[must_use]
    pub fn observations(&self) -> &[ImportedFieldSemantic] { &self.observations }
    #[must_use]
    pub const fn receipt(&self) -> &FieldSemanticImportReceipt { &self.receipt }
    /// Fresh full original source/body/form/range/meaning reconstruction.
    /// # Errors
    /// Rejects whole source, original range, meaning, graph or receipt drift.
    pub fn verify_source(&self, fresh: &[u8]) -> Result<FieldSemanticImportReceipt, FieldSemanticImportError> {
        self.fields.verify_source(fresh)?;
        let source = self.fields.forms.source();
        let forms = ImportedDocumentForms::import(ImportedSourcePackage::import(
            fresh, source.document_id.clone(), source.source_sha256, source.limits,
        ).map_err(FormImportError::from)?).map_err(FieldRangeImportError::from)?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let rebuilt = ImportedDocumentFieldSemantics::import(&fields)?;
        if self.graph != rebuilt.graph || self.observations != rebuilt.observations || self.receipt != rebuilt.receipt {
            return Err(FieldSemanticImportError::Binding);
        }
        Ok(rebuilt.receipt)
    }
}
fn read_meaning(fields: &ImportedDocumentFields<'_>, range: &ImportedFieldRange, work: &mut usize)
    -> Result<ImportedFieldMeaning, FieldSemanticImportError> {
    if !matches!(range.native_kind.as_str(), "HYPERLINK" | "FORMULA") {
        return Ok(ImportedFieldMeaning::Unsupported { native_kind: range.native_kind.clone() });
    }
    let source = fields.forms.source();
    let begin = source.resolve_anchor(&range.begin_anchor).map_err(|_| FieldSemanticImportError::Binding)?;
    let xml = begin.part().xml().ok_or(FieldSemanticImportError::Binding)?;
    *work = work.checked_add(xml.elements().len()).ok_or(FieldSemanticImportError::Limit)?;
    if *work > MAX_WORK_ELEMENTS { return Err(FieldSemanticImportError::Limit); }
    if range.native_kind == "FORMULA" {
        let (dimensions, formula) = crate::table_formula::read_imported_field(xml,
            begin.element_index().ok_or(FieldSemanticImportError::Binding)?)
            .map_err(|error| FieldSemanticImportError::Formula { code: error.code() })?;
        return Ok(ImportedFieldMeaning::TableFormula { dimensions, formula });
    }
    let parameters = source.resolve_anchor(range.parameter_anchor.as_ref()
        .ok_or(FieldSemanticImportError::Binding)?).map_err(|_| FieldSemanticImportError::Binding)?;
    if parameters.part().anchor() != begin.part().anchor()
        || parameters.element().and_then(crate::XmlElementToken::parent) != begin.element_index() {
        return Err(FieldSemanticImportError::Binding);
    }
    let target = crate::hyperlink_hwpx::read_imported_parameter_target(xml,
        parameters.element_index().ok_or(FieldSemanticImportError::Binding)?)
        .map_err(|error| FieldSemanticImportError::Hyperlink { code: error.code() })?;
    Ok(ImportedFieldMeaning::HttpsTarget { target })
}
fn attach_meanings(flow: &mut Flow, meanings: &mut BTreeMap<LogicalId, PropertyValue>) -> Result<(), FieldSemanticImportError> {
    for node in &mut flow.children {
        if let Some(value) = meanings.remove(&node.common().node_id) {
            let Node::Field(field) = node else { return Err(FieldSemanticImportError::Binding); };
            field.properties.insert("source_derived_meaning", value);
        }
        match node {
            Node::Table(table) => for cell in &mut table.cells { attach_meanings(&mut cell.body, meanings)?; },
            Node::Drawing(drawing) => attach_meanings(&mut drawing.children, meanings)?,
            _ => (),
        }
    }
    Ok(())
}
fn property_value(value: serde_json::Value) -> Result<PropertyValue, FieldSemanticImportError> {
    Ok(match value {
        serde_json::Value::String(v) => PropertyValue::Text(v),
        serde_json::Value::Bool(v) => PropertyValue::Bool(v),
        serde_json::Value::Number(v) => PropertyValue::Integer(v.as_i64().ok_or(FieldSemanticImportError::Graph)?),
        serde_json::Value::Array(v) => PropertyValue::List(v.into_iter().map(property_value).collect::<Result<_,_>>()?),
        serde_json::Value::Object(v) => PropertyValue::Object(v.into_iter().map(|(k,v)| Ok((k,property_value(v)?))).collect::<Result<_,FieldSemanticImportError>>()?),
        serde_json::Value::Null => return Err(FieldSemanticImportError::Graph),
    })
}
#[derive(Debug, Error)]
pub enum FieldSemanticImportError {
    #[error("field semantics original source/ranges rejected")]
    Source(#[from] FieldRangeImportError),
    #[error("source HTTPS parameter profile rejected: {code}")]
    Hyperlink { code: &'static str },
    #[error("source table formula profile rejected: {code}")]
    Formula { code: &'static str },
    #[error("field semantics source binding rejected")]
    Binding,
    #[error("field semantics finite work limit exceeded")]
    Limit,
    #[error("field semantics graph rejected")]
    Graph,
}
