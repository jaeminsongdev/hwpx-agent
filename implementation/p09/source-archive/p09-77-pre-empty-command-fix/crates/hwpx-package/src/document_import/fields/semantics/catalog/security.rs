//! Whole original active-content inventory bound to actual source/body/resources.
//! Passive inspection never attests native protection, encryption or signatures.
mod native_forms;
use super::{CatalogImportError, ImportedDocumentCatalog};
use crate::{
    ActivationKind, ActiveContentControlKind, ActiveContentDisposition, ActiveContentError,
    ActiveContentInventory, ActiveContentLimits, ActiveContentResourceKind, ActiveContentSignature,
    BoundedZipReader, PackageGraphLimits,
    document_import::{
        ImportedSourcePackage,
        fields::{ImportedDocumentFields, semantics::ImportedDocumentFieldSemantics},
        forms::{FormImportError, ImportedDocumentForms},
        hex_digest,
    },
};
use domain_ir::{
    DocumentGraph, DocumentGraphLimits, Flow, LogicalId, Node, PropertyValue, SourceAnchorHandle,
};
pub use native_forms::ImportedNativeFormSecurityBinding;
use serde::Serialize;
use std::{collections::BTreeMap, fmt, io::Cursor};
use thiserror::Error;

pub const SECURITY_IMPORT_PROFILE: &str = "hwpx-agent.document-import-active-security/partial-v1";
pub const SECURITY_IMPORT_SCOPE: &str = "whole_original_active_inventory_and_source_binding_execution_blocked_native_protection_encryption_signature_full_import_unqualified";

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedActiveControlBinding {
    pub source_anchor: SourceAnchorHandle,
    pub represented_node_id: Option<LogicalId>,
    pub kind: ActiveContentControlKind,
    pub disposition: ActiveContentDisposition,
}
impl fmt::Debug for ImportedActiveControlBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedActiveControlBinding(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedActiveResourceBinding {
    pub source_anchor: SourceAnchorHandle,
    pub resource_id: LogicalId,
    pub kind: ActiveContentResourceKind,
    pub disposition: ActiveContentDisposition,
    /// Original binary magic/signature check, NOT a cryptographic document signature.
    pub payload_signature: ActiveContentSignature,
}
impl fmt::Debug for ImportedActiveResourceBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedActiveResourceBinding(<redacted>)")
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NativeSecurityQualification {
    NotAssessedByActiveContentInventory,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct ImportedActiveCounts {
    pub resources: usize,
    pub controls: usize,
    pub blocked: usize,
    pub quarantined: usize,
    pub review_required: usize,
}
impl From<crate::active_content::ActiveContentCounts> for ImportedActiveCounts {
    fn from(value: crate::active_content::ActiveContentCounts) -> Self {
        Self {
            resources: value.resources,
            controls: value.controls,
            blocked: value.blocked,
            quarantined: value.quarantined,
            review_required: value.review_required,
        }
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ActiveSecurityImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub original_catalog_graph_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub original_inventory_graph_sha256: String,
    pub original_inventory_state_sha256: String,
    pub counts: ImportedActiveCounts,
    pub source_control_bindings: usize,
    pub represented_control_bindings: usize,
    pub source_resource_bindings: usize,
    pub native_form_bindings: usize,
    pub native_forms_not_in_original_inventory: usize,
    pub activation_allowed: bool,
    pub native_security: NativeSecurityQualification,
}
/// No deserialization, caller graph/inventory, activation or publication capability.
pub struct ImportedDocumentActiveSecurity<'a, 'catalog, 'fields, 'source> {
    catalog: &'a ImportedDocumentCatalog<'catalog, 'fields, 'source>,
    graph: DocumentGraph,
    inventory: ActiveContentInventory,
    controls: Vec<ImportedActiveControlBinding>,
    resources: Vec<ImportedActiveResourceBinding>,
    native_forms: Vec<ImportedNativeFormSecurityBinding>,
    receipt: ActiveSecurityImportReceipt,
}
impl fmt::Debug for ImportedDocumentActiveSecurity<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ImportedDocumentActiveSecurity")
            .field("controls", &self.controls.len())
            .field("resources", &self.resources.len())
            .finish_non_exhaustive()
    }
}
impl<'a, 'catalog, 'fields, 'source>
    ImportedDocumentActiveSecurity<'a, 'catalog, 'fields, 'source>
{
    /// Original bounded whole-package scanner; unknown native security stays unknown.
    /// # Errors
    /// Rejects original scanner errors, graph/source/resource/anchor drift or budgets.
    pub fn import(
        catalog: &'a ImportedDocumentCatalog<'catalog, 'fields, 'source>,
    ) -> Result<Self, ActiveSecurityImportError> {
        let source = catalog.meanings.fields.forms.source();
        let mut reader = BoundedZipReader::open(
            Cursor::new(&source.original),
            source
                .limits
                .zip()
                .map_err(|_| ActiveSecurityImportError::Binding)?,
        )
        .map_err(|_| ActiveSecurityImportError::Binding)?;
        let inventory = ActiveContentInventory::scan(
            &mut reader,
            &source.graph,
            PackageGraphLimits::default(),
            ActiveContentLimits::default(),
        )?;
        if inventory.activation_allowed() {
            return Err(ActiveSecurityImportError::Binding);
        }
        let mut draft = catalog.graph().clone().into_draft();
        let mut nodes = BTreeMap::new();
        for section in &draft.sections {
            collect_nodes(&section.body, &mut nodes)?;
        }
        for note in &draft.notes {
            collect_nodes(&note.body, &mut nodes)?;
        }
        let controls = bind_controls(source, &inventory, &nodes)?;
        let resources = bind_resources(source, &inventory, &mut draft.resources)?;
        let native_forms = native_forms::bind(catalog.meanings.fields.forms, &nodes, &controls)?;
        let mut dispositions: BTreeMap<_, _> = controls
            .iter()
            .filter_map(|v| {
                v.represented_node_id
                    .as_ref()
                    .map(|id| (id.clone(), v.disposition))
            })
            .collect();
        for form in &native_forms {
            if let Some(previous) = dispositions.insert(form.node_id.clone(), form.disposition)
                && previous != form.disposition
            {
                return Err(ActiveSecurityImportError::Binding);
            }
        }
        for section in &mut draft.sections {
            attach_control_state(&mut section.body, &dispositions)?;
        }
        for note in &mut draft.notes {
            attach_control_state(&mut note.body, &dispositions)?;
        }
        draft.security_state.properties.insert(
            "source_active_inventory_state_sha256",
            PropertyValue::Text(inventory.state_sha256().into()),
        );
        draft
            .security_state
            .properties
            .insert("active_execution_allowed", PropertyValue::Boolean(false));
        draft.security_state.properties.insert(
            "native_security_assessment",
            PropertyValue::Text("not_assessed_by_active_content_inventory".into()),
        );
        draft.metadata.insert(
            "active_security_import_profile",
            PropertyValue::Text(SECURITY_IMPORT_PROFILE.into()),
        );
        draft.metadata.insert(
            "active_security_import_scope",
            PropertyValue::Text(SECURITY_IMPORT_SCOPE.into()),
        );
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| ActiveSecurityImportError::Graph)?;
        let receipt = ActiveSecurityImportReceipt {
            profile: SECURITY_IMPORT_PROFILE,
            qualification: SECURITY_IMPORT_SCOPE,
            source_package_sha256: catalog.receipt().source_package_sha256,
            original_catalog_graph_sha256: catalog.receipt().graph_sha256,
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| ActiveSecurityImportError::Graph)?,
            original_inventory_graph_sha256: inventory.source_graph_sha256().into(),
            original_inventory_state_sha256: inventory.state_sha256().into(),
            counts: inventory.counts().into(),
            source_control_bindings: controls.len(),
            represented_control_bindings: controls
                .iter()
                .filter(|v| v.represented_node_id.is_some())
                .count(),
            source_resource_bindings: resources.len(),
            activation_allowed: false,
            native_form_bindings: native_forms.len(),
            native_forms_not_in_original_inventory: native_forms
                .iter()
                .filter(|v| !v.in_original_inventory)
                .count(),
            native_security: NativeSecurityQualification::NotAssessedByActiveContentInventory,
        };
        Ok(Self {
            catalog,
            graph,
            inventory,
            controls,
            resources,
            native_forms,
            receipt,
        })
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
    #[must_use]
    pub const fn inventory(&self) -> &ActiveContentInventory {
        &self.inventory
    }
    #[must_use]
    pub fn controls(&self) -> &[ImportedActiveControlBinding] {
        &self.controls
    }
    #[must_use]
    pub fn resources(&self) -> &[ImportedActiveResourceBinding] {
        &self.resources
    }
    #[must_use]
    pub fn native_forms(&self) -> &[ImportedNativeFormSecurityBinding] {
        &self.native_forms
    }
    #[must_use]
    pub const fn receipt(&self) -> &ActiveSecurityImportReceipt {
        &self.receipt
    }
    /// Delegates to the original unconditional normal-tier denial, never activates.
    /// # Errors
    /// All six typed activation kinds are denied by the original authority.
    pub fn require_activation(
        &self,
        action: ActivationKind,
    ) -> Result<(), ActiveSecurityImportError> {
        self.inventory.authorize(action)?;
        Err(ActiveSecurityImportError::Binding)
    }
    /// Complete fresh source/forms/fields/meanings/header/scanner/bindings rebuild.
    /// # Errors
    /// Rejects whole source, original inventory, node/resource/graph or receipt drift.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<ActiveSecurityImportReceipt, ActiveSecurityImportError> {
        self.catalog.verify_source(fresh)?;
        let source = self.catalog.meanings.fields.forms.source();
        let forms = ImportedDocumentForms::import(
            ImportedSourcePackage::import(
                fresh,
                source.document_id.clone(),
                source.source_sha256,
                source.limits,
            )
            .map_err(FormImportError::from)?,
        )?;
        let fields = ImportedDocumentFields::import(&forms)
            .map_err(super::super::FieldSemanticImportError::from)
            .map_err(CatalogImportError::from)?;
        let meanings =
            ImportedDocumentFieldSemantics::import(&fields).map_err(CatalogImportError::from)?;
        let catalog = ImportedDocumentCatalog::import(&meanings)?;
        let rebuilt = ImportedDocumentActiveSecurity::import(&catalog)?;
        if self.graph != rebuilt.graph
            || self.inventory != rebuilt.inventory
            || self.controls != rebuilt.controls
            || self.resources != rebuilt.resources
            || self.native_forms != rebuilt.native_forms
            || self.receipt != rebuilt.receipt
        {
            return Err(ActiveSecurityImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
fn collect_nodes(
    flow: &Flow,
    nodes: &mut BTreeMap<LogicalId, LogicalId>,
) -> Result<(), ActiveSecurityImportError> {
    for node in &flow.children {
        if let Some(anchor) = &node.common().source_anchor {
            if nodes
                .insert(anchor.opaque_handle.clone(), node.common().node_id.clone())
                .is_some()
            {
                return Err(ActiveSecurityImportError::Binding);
            }
        }
        match node {
            Node::Table(table) => {
                for cell in &table.cells {
                    collect_nodes(&cell.body, nodes)?;
                }
            }
            Node::Drawing(drawing) => collect_nodes(&drawing.children, nodes)?,
            _ => (),
        }
    }
    Ok(())
}
fn bind_controls(
    source: &ImportedSourcePackage,
    inventory: &ActiveContentInventory,
    nodes: &BTreeMap<LogicalId, LogicalId>,
) -> Result<Vec<ImportedActiveControlBinding>, ActiveSecurityImportError> {
    let parts: BTreeMap<_, _> = source
        .parts()
        .iter()
        .map(|part| (part.path().as_str(), part))
        .collect();
    let mut controls = Vec::new();
    for control in inventory.controls() {
        let part = parts
            .get(control.document_part())
            .ok_or(ActiveSecurityImportError::Binding)?;
        let anchor = part
            .element_anchor(control.element_ordinal())
            .ok_or(ActiveSecurityImportError::Binding)?;
        source
            .resolve_anchor(anchor)
            .map_err(|_| ActiveSecurityImportError::Binding)?;
        if hex_digest(anchor.fingerprint_sha256) != control.element_sha256() {
            return Err(ActiveSecurityImportError::Binding);
        }
        controls.push(ImportedActiveControlBinding {
            source_anchor: anchor.clone(),
            represented_node_id: nodes.get(&anchor.opaque_handle).cloned(),
            kind: control.kind(),
            disposition: control.disposition(),
        });
    }
    Ok(controls)
}
fn bind_resources(
    source: &ImportedSourcePackage,
    inventory: &ActiveContentInventory,
    resources: &mut [domain_ir::Resource],
) -> Result<Vec<ImportedActiveResourceBinding>, ActiveSecurityImportError> {
    let parts: BTreeMap<_, _> = source
        .parts()
        .iter()
        .map(|part| (part.path().as_str(), part))
        .collect();
    let indexes: BTreeMap<_, _> = resources
        .iter()
        .enumerate()
        .map(|(i, value)| (value.resource_id.clone(), i))
        .collect();
    let mut bindings = Vec::new();
    for observed in inventory.resources() {
        let part = parts
            .get(observed.path())
            .ok_or(ActiveSecurityImportError::Binding)?;
        let anchor = part.anchor();
        source
            .resolve_anchor(anchor)
            .map_err(|_| ActiveSecurityImportError::Binding)?;
        let resource_id = LogicalId::parse(format!("resource-{}", anchor.opaque_handle.as_str()))
            .map_err(|_| ActiveSecurityImportError::Graph)?;
        let resource = &mut resources[*indexes
            .get(&resource_id)
            .ok_or(ActiveSecurityImportError::Binding)?];
        let artifact = resource
            .artifact
            .as_ref()
            .ok_or(ActiveSecurityImportError::Binding)?;
        if artifact.sha256 != anchor.fingerprint_sha256
            || hex_digest(artifact.sha256) != observed.raw_sha256()
            || artifact.byte_length != observed.expanded_size()
        {
            return Err(ActiveSecurityImportError::Binding);
        }
        resource
            .metadata
            .insert("source_active_content_kind", label(&observed.kind())?);
        resource.metadata.insert(
            "source_active_content_disposition",
            label(&observed.disposition())?,
        );
        resource.metadata.insert(
            "source_active_binary_signature_check_not_document_signature",
            label(&observed.signature())?,
        );
        bindings.push(ImportedActiveResourceBinding {
            source_anchor: anchor.clone(),
            resource_id,
            kind: observed.kind(),
            disposition: observed.disposition(),
            payload_signature: observed.signature(),
        });
    }
    Ok(bindings)
}
fn attach_control_state(
    flow: &mut Flow,
    dispositions: &BTreeMap<LogicalId, ActiveContentDisposition>,
) -> Result<(), ActiveSecurityImportError> {
    for node in &mut flow.children {
        if let Some(disposition) = dispositions.get(&node.common().node_id) {
            common_mut(node)
                .semantics
                .insert("source_active_content_disposition", label(disposition)?);
        }
        match node {
            Node::Table(table) => {
                for cell in &mut table.cells {
                    attach_control_state(&mut cell.body, dispositions)?;
                }
            }
            Node::Drawing(drawing) => attach_control_state(&mut drawing.children, dispositions)?,
            _ => (),
        }
    }
    Ok(())
}
fn label(value: &impl Serialize) -> Result<PropertyValue, ActiveSecurityImportError> {
    let serde_json::Value::String(value) =
        serde_json::to_value(value).map_err(|_| ActiveSecurityImportError::Graph)?
    else {
        return Err(ActiveSecurityImportError::Graph);
    };
    Ok(PropertyValue::Text(value))
}
fn common_mut(node: &mut Node) -> &mut domain_ir::NodeCommon {
    match node {
        Node::Paragraph(v) => &mut v.common,
        Node::Table(v) => &mut v.common,
        Node::Equation(v) => &mut v.common,
        Node::Drawing(v) => &mut v.common,
        Node::Chart(v) => &mut v.common,
        Node::Field(v) => &mut v.common,
        Node::FormControl(v) => &mut v.common,
        Node::Break(v) => &mut v.common,
        Node::EmbeddedObject(v) => &mut v.common,
    }
}
#[derive(Debug, Error)]
pub enum ActiveSecurityImportError {
    #[error("security original source forms rejected")]
    Forms(#[from] FormImportError),
    #[error("security original header/meaning source rejected")]
    Catalog(#[from] CatalogImportError),
    #[error("security original active inventory rejected")]
    Inventory(#[from] ActiveContentError),
    #[error("security original source/node/resource/inventory binding rejected")]
    Binding,
    #[error("security document graph rejected")]
    Graph,
}
