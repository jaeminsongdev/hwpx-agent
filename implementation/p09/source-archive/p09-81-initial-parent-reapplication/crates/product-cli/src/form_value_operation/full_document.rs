//! Caller-supplied full-IR preparation, never an importer, persisted binding or route authority.
//! Preserves every field except the complete state property of actually changed form nodes.
use super::{FORM_OPERATION_PROFILE, FormOperationContext, PreparedFormOperation, plan_limits};
use domain_ir::{
    ArgumentDraft, ArgumentKind, ArgumentSpec, CanonicalArgumentValue, CapabilityCatalog,
    CapabilityDefinitionDraft, CompiledOperationPlan, DefaultPolicy, DocumentGraph,
    DocumentGraphLimits, Flow, LogicalId, Node, OperationDraft, OperationPlanCompiler,
    OperationPlanDraft, PropertyValue, RevisionId, Selector, SelectorDraft, SelectorLimits,
    SelectorSnapshot, form_input::FormInputAccessPolicy,
};
use serde::Serialize;
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
};
use thiserror::Error;

const PROFILE: &str = "hwpx-agent.product-form-full-document-preparation/v1";
const STATE: &str = "complete_control_state_json";

/// Explicit caller-qualified snapshot; hashes do not establish native import provenance.
pub struct FullDocumentFormContext<'a> {
    graph: &'a DocumentGraph,
    graph_sha256: [u8; 32],
    package_sha256: [u8; 32],
    revision: RevisionId,
}
impl fmt::Debug for FullDocumentFormContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FullDocumentFormContext(<redacted>)")
    }
}
impl<'a> FullDocumentFormContext<'a> {
    /// Binds a bounded full IR under caller-owned identities, not a revision/artifact lookup.
    /// # Errors
    /// Rejects digest drift, inventory projection and protected/encrypted/signed graphs.
    pub fn bind(
        graph: &'a DocumentGraph,
        expected_graph_sha256: [u8; 32],
        source_package_sha256: [u8; 32],
        revision: RevisionId,
    ) -> Result<Self, FullDocumentFormError> {
        // Bound serialization before cloning a graph admitted under wider domain limits.
        serde_json::to_writer(GraphBudget(0), graph).map_err(|_| FullDocumentFormError::Graph)?;
        let draft = graph.clone().into_draft();
        let validated = DocumentGraph::from_draft(draft.clone(), DocumentGraphLimits::default())
            .map_err(|_| FullDocumentFormError::Graph)?;
        if &validated != graph
            || graph
                .canonical_sha256()
                .map_err(|_| FullDocumentFormError::Graph)?
                != expected_graph_sha256
        {
            return Err(FullDocumentFormError::Binding);
        }
        if draft.source_profile.as_ref().is_some_and(|p| p.as_str() == FORM_OPERATION_PROFILE)
            || draft.metadata.iter().any(|(key, value)| key == "scope" && matches!(value,
                PropertyValue::Text(text) if text == "complete_form_inventory_projection_not_full_document_graph"))
        {
            return Err(FullDocumentFormError::Projection);
        }
        // An actual source-backed but still partial typed importer is not a
        // caller-qualified full-document IR. Never silently promote its scope.
        if draft.source_profile.as_ref().is_some_and(|profile| {
            profile.as_str() == hwpx_package::document_import::structure::STRUCTURE_IMPORT_PROFILE
        }) || draft.metadata.iter().any(|(key, value)| {
            key == "scope"
                && matches!(value, PropertyValue::Text(text)
                    if text == hwpx_package::document_import::structure::STRUCTURE_IMPORT_SCOPE)
        }) {
            return Err(FullDocumentFormError::Projection);
        }
        // Observed native values do not include caller-default/validation policy
        // or complete document semantics, even if older partial markers vanish.
        if draft.metadata.iter().any(|(key, value)| {
            matches!((key, value),
                ("native_form_import_profile", PropertyValue::Text(text))
                    if text == hwpx_package::document_import::forms::FORM_IMPORT_PROFILE)
                || matches!((key, value),
                    ("native_form_import_scope", PropertyValue::Text(text))
                        if text == hwpx_package::document_import::forms::FORM_OBSERVATION_SCOPE)
        }) {
            return Err(FullDocumentFormError::Projection);
        }
        // Explicit policy binding completes only the form COMPONENT, not the
        // importer/provider authority or other document/security semantics.
        if draft.metadata.iter().any(|(key, value)| {
            matches!((key, value),
                ("native_form_policy_profile", PropertyValue::Text(text))
                    if text == hwpx_package::document_import::forms::policies::FORM_POLICY_PROFILE)
                || matches!((key, value),
                    ("native_form_policy_scope", PropertyValue::Text(text))
                        if text == hwpx_package::document_import::forms::policies::FORM_POLICY_SCOPE)
        }) {
            return Err(FullDocumentFormError::Projection);
        }
        // Source field pairing still does not resolve destinations/evaluations
        // or establish complete document/security/issuer semantics.
        if draft.metadata.iter().any(|(key, value)| {
            matches!((key, value), ("field_range_import_profile", PropertyValue::Text(text))
                if text == hwpx_package::document_import::fields::FIELD_RANGE_IMPORT_PROFILE)
                || matches!((key, value), ("field_range_import_scope", PropertyValue::Text(text))
                if text == hwpx_package::document_import::fields::FIELD_RANGE_IMPORT_SCOPE)
        }) {
            return Err(FullDocumentFormError::Projection);
        }
        if draft.metadata.iter().any(|(key, value)| {
            matches!((key, value), ("field_semantics_import_profile", PropertyValue::Text(text))
                if text == hwpx_package::document_import::fields::semantics::FIELD_SEMANTICS_PROFILE)
                || matches!((key, value), ("field_semantics_import_scope", PropertyValue::Text(text))
                    if text == hwpx_package::document_import::fields::semantics::FIELD_SEMANTICS_SCOPE)
        }) {
            return Err(FullDocumentFormError::Projection);
        }
        if draft.metadata.iter().any(|(key, value)| {
            matches!((key, value), ("note_import_profile", PropertyValue::Text(text))
                if text == hwpx_package::document_import::structure::notes::NOTE_IMPORT_PROFILE)
                || matches!((key, value), ("note_import_scope", PropertyValue::Text(text))
                    if text == hwpx_package::document_import::structure::notes::NOTE_IMPORT_SCOPE)
        }) {
            return Err(FullDocumentFormError::Projection);
        }
        if draft.metadata.iter().any(|(key, value)| {
            matches!((key, value), ("bookmark_import_profile", PropertyValue::Text(text))
                if text == hwpx_package::document_import::structure::bookmarks::BOOKMARK_IMPORT_PROFILE)
                || matches!((key, value), ("bookmark_import_scope", PropertyValue::Text(text))
                    if text == hwpx_package::document_import::structure::bookmarks::BOOKMARK_IMPORT_SCOPE)
        }) {
            return Err(FullDocumentFormError::Projection);
        }
        if draft.metadata.iter().any(|(key, value)| {
            matches!((key, value), ("style_catalog_import_profile", PropertyValue::Text(text))
                if text == hwpx_package::document_import::fields::semantics::catalog::CATALOG_IMPORT_PROFILE)
                || matches!((key, value), ("style_catalog_import_scope", PropertyValue::Text(text))
                    if text == hwpx_package::document_import::fields::semantics::catalog::CATALOG_IMPORT_SCOPE)
        }) {
            return Err(FullDocumentFormError::Projection);
        }
        reject_partial_section_settings(&draft.metadata)?;
        if draft.security_state.protected
            || draft.security_state.encrypted
            || draft.security_state.signed
        {
            return Err(FullDocumentFormError::Security);
        }
        Ok(Self {
            graph,
            graph_sha256: expected_graph_sha256,
            package_sha256: source_package_sha256,
            revision,
        })
    }
}

fn reject_partial_section_settings(
    metadata: &domain_ir::Properties,
) -> Result<(), FullDocumentFormError> {
    reject_partial_font_catalog(metadata)?;
    reject_partial_active_security(metadata)?;
    if metadata.iter().any(|(key, value)| {
        matches!((key, value), ("section_settings_import_profile", PropertyValue::Text(text))
            if text == hwpx_package::document_import::fields::semantics::catalog::security::settings::SETTINGS_IMPORT_PROFILE)
            || matches!((key, value), ("section_settings_import_scope", PropertyValue::Text(text))
                if text == hwpx_package::document_import::fields::semantics::catalog::security::settings::SETTINGS_IMPORT_SCOPE)
    }) { return Err(FullDocumentFormError::Projection); }
    Ok(())
}
fn reject_partial_font_catalog(
    metadata: &domain_ir::Properties,
) -> Result<(), FullDocumentFormError> {
    use hwpx_package::document_import::fields::semantics::catalog::fonts::{
        FONT_IMPORT_PROFILE, FONT_IMPORT_SCOPE,
    };
    if metadata.iter().any(|(key, value)| {
        matches!((key, value), ("font_catalog_import_profile", PropertyValue::Text(text))
            if text == FONT_IMPORT_PROFILE)
            || matches!((key, value), ("font_catalog_import_scope", PropertyValue::Text(text))
                if text == FONT_IMPORT_SCOPE)
    }) { return Err(FullDocumentFormError::Projection); }
    Ok(())
}
fn reject_partial_document_assembly(
    metadata: &domain_ir::Properties,
) -> Result<(), FullDocumentFormError> {
    use hwpx_package::document_import::fields::semantics::catalog::assembly::{
        DOCUMENT_ASSEMBLY_PROFILE, DOCUMENT_ASSEMBLY_SCOPE,
    };
    if metadata.iter().any(|(key, value)| {
        matches!((key, value), ("document_assembly_profile", PropertyValue::Text(text))
            if text == DOCUMENT_ASSEMBLY_PROFILE)
            || matches!((key, value), ("document_assembly_scope", PropertyValue::Text(text))
                if text == DOCUMENT_ASSEMBLY_SCOPE)
    }) { return Err(FullDocumentFormError::Projection); }
    Ok(())
}
fn reject_partial_active_security(
    metadata: &domain_ir::Properties,
) -> Result<(), FullDocumentFormError> {
    if metadata.iter().any(|(key, value)| {
        matches!((key, value), ("active_security_import_profile", PropertyValue::Text(text))
            if text == hwpx_package::document_import::fields::semantics::catalog::security::SECURITY_IMPORT_PROFILE)
            || matches!((key, value), ("active_security_import_scope", PropertyValue::Text(text))
                if text == hwpx_package::document_import::fields::semantics::catalog::security::SECURITY_IMPORT_SCOPE)
    }) { return Err(FullDocumentFormError::Projection); }
    Ok(())
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FullDocumentFormReceipt {
    pub profile: &'static str,
    pub source_graph_sha256: String,
    pub target_graph_sha256: String,
    pub source_package_sha256: String,
    pub candidate_package_sha256: String,
    pub inventory_operation_sha256: String,
    pub full_graph_operation_sha256: String,
    pub matched_controls: usize,
    pub changed_controls: usize,
    pub qualification: FullDocumentFormQualification,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FullDocumentFormQualification {
    CallerSuppliedIrOnlyImportPersistenceRoutePublicationNativeAndGateUnqualified,
}

/// Non-deserializable full graph/compiled-plan binding, with no publication or CAS capability.
pub struct PreparedFullDocumentForms {
    target: DocumentGraph,
    compiled: CompiledOperationPlan,
    receipt: FullDocumentFormReceipt,
}
impl fmt::Debug for PreparedFullDocumentForms {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedFullDocumentForms(<redacted>)")
    }
}
impl PreparedFullDocumentForms {
    #[must_use]
    pub const fn target_graph(&self) -> &DocumentGraph {
        &self.target
    }
    #[must_use]
    pub const fn compiled_plan(&self) -> &CompiledOperationPlan {
        &self.compiled
    }
    #[must_use]
    pub const fn receipt(&self) -> &FullDocumentFormReceipt {
        &self.receipt
    }
    /// Rechecks the actual package/access operation and the entire fresh IR, then rebuilds.
    /// # Errors
    /// Rejects source/revision/document/graph/candidate/plan/state/access drift.
    pub fn verify(
        &self,
        full: &FullDocumentFormContext<'_>,
        operation: &PreparedFormOperation,
        native: &FormOperationContext<'_>,
        access: &FormInputAccessPolicy,
    ) -> Result<FullDocumentFormReceipt, FullDocumentFormError> {
        let rebuilt = FullDocumentFormPreparation::prepare(full, operation, native, access)?;
        if rebuilt.target != self.target
            || rebuilt.compiled != self.compiled
            || rebuilt.receipt != self.receipt
        {
            return Err(FullDocumentFormError::Binding);
        }
        Ok(self.receipt.clone())
    }
    /// Still requires real signed form authority; the unrelated VS0 attestation cannot supply it.
    /// # Errors
    /// Denies the current unsupported route after all preparation checks succeed.
    pub fn require_current_product_route(
        &self,
        full: &FullDocumentFormContext<'_>,
        operation: &PreparedFormOperation,
        native: &FormOperationContext<'_>,
        access: &FormInputAccessPolicy,
    ) -> Result<(), FullDocumentFormError> {
        self.verify(full, operation, native, access)?;
        operation
            .require_current_product_route(native, access)
            .map_err(|_| FullDocumentFormError::RouteUnqualified)
    }
}

#[derive(Debug)]
pub struct FullDocumentFormPreparation;
impl FullDocumentFormPreparation {
    /// Recompiles on real IR paths and updates exactly the typed target control states.
    /// # Errors
    /// Rejects missing/extra/mismatched controls, wrong identities and any underlying drift.
    pub fn prepare(
        full: &FullDocumentFormContext<'_>,
        operation: &PreparedFormOperation,
        native: &FormOperationContext<'_>,
        access: &FormInputAccessPolicy,
    ) -> Result<PreparedFullDocumentForms, FullDocumentFormError> {
        let receipt = operation
            .verify(native, access)
            .map_err(|_| FullDocumentFormError::Operation)?;
        if full.graph.document_id() != &operation.identity.document
            || full.revision != operation.identity.revision
            || hex::encode(full.package_sha256)
                != receipt.preparation.component.source_package_sha256
            || full
                .graph
                .canonical_sha256()
                .map_err(|_| FullDocumentFormError::Graph)?
                != full.graph_sha256
        {
            return Err(FullDocumentFormError::Binding);
        }
        let mut draft = full.graph.clone().into_draft();
        let mut states = BTreeMap::new();
        for (source, target) in operation
            .typed
            .source_state()
            .controls()
            .iter()
            .zip(operation.typed.target_state().controls())
        {
            let source_json =
                serde_json::to_string(source).map_err(|_| FullDocumentFormError::Graph)?;
            let target_json =
                serde_json::to_string(target).map_err(|_| FullDocumentFormError::Graph)?;
            states.insert(
                source.identity.logical_control_id.clone(),
                (source.payload.capability_id(), source_json, target_json),
            );
        }
        let mut seen = BTreeSet::new();
        for section in &mut draft.sections {
            apply(&mut section.body, &states, &mut seen)?;
        }
        for note in &mut draft.notes {
            apply(&mut note.body, &states, &mut seen)?;
        }
        if seen.len() != states.len() {
            return Err(FullDocumentFormError::Inventory);
        }
        let target = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| FullDocumentFormError::Graph)?;
        let target_sha = hex::encode(
            target
                .canonical_sha256()
                .map_err(|_| FullDocumentFormError::Graph)?,
        );
        let compiled = compile_full(full, operation, &target_sha)?;
        let receipt = FullDocumentFormReceipt {
            profile: PROFILE, source_graph_sha256: hex::encode(full.graph_sha256),
            target_graph_sha256: target_sha, source_package_sha256: hex::encode(full.package_sha256),
            candidate_package_sha256: receipt.preparation.component.output_package_sha256,
            inventory_operation_sha256: receipt.compiled_operation_plan_sha256,
            full_graph_operation_sha256: hex::encode(compiled.canonical_sha256().map_err(|_| FullDocumentFormError::Operation)?),
            matched_controls: seen.len(), changed_controls: receipt.changed_controls,
            qualification: FullDocumentFormQualification::CallerSuppliedIrOnlyImportPersistenceRoutePublicationNativeAndGateUnqualified,
        };
        Ok(PreparedFullDocumentForms {
            target,
            compiled,
            receipt,
        })
    }
}

fn compile_full(
    full: &FullDocumentFormContext<'_>,
    operation: &PreparedFormOperation,
    target_sha: &str,
) -> Result<CompiledOperationPlan, FullDocumentFormError> {
    let snapshot =
        SelectorSnapshot::build(full.graph, full.revision.clone(), SelectorLimits::default())
            .map_err(|_| FullDocumentFormError::Graph)?;
    let mut definitions = BTreeMap::new();
    let mut operations = Vec::new();
    for original in operation.compiled.operations() {
        let mut arguments = BTreeMap::new();
        for (key, argument) in original.arguments() {
            let CanonicalArgumentValue::Text(value) = argument.value() else {
                return Err(FullDocumentFormError::Operation);
            };
            arguments.insert(key.clone(), ArgumentDraft::Text(value.clone()));
        }
        arguments.insert(
            "source_full_graph_sha256".into(),
            ArgumentDraft::Text(hex::encode(full.graph_sha256)),
        );
        arguments.insert(
            "target_full_graph_sha256".into(),
            ArgumentDraft::Text(target_sha.to_owned()),
        );
        let mut definition = CapabilityDefinitionDraft::new(original.capability_id().clone());
        for key in arguments.keys() {
            definition.arguments.insert(
                key.clone(),
                ArgumentSpec {
                    kind: ArgumentKind::Text {
                        max_bytes: 1024 * 1024,
                    },
                    required: true,
                    default: None,
                    default_policy: DefaultPolicy::Locked,
                },
            );
        }
        definitions.insert(original.capability_id().clone(), definition);
        operations.push(OperationDraft {
            operation_id: original.operation_id().clone(),
            capability_id: original.capability_id().clone(),
            selector: SelectorDraft::one(Selector::by_logical_id(
                original.target().node_id().clone(),
            )),
            arguments,
            depends_on: original.depends_on().to_vec(),
        });
    }
    let catalog = CapabilityCatalog::from_drafts(definitions.into_values().collect())
        .map_err(|_| FullDocumentFormError::Operation)?;
    let compiled = OperationPlanCompiler::new(plan_limits())
        .map_err(|_| FullDocumentFormError::Operation)?
        .compile(
            OperationPlanDraft::new(
                operation.identity.plan.clone(),
                full.revision.clone(),
                operations,
            ),
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        )
        .map_err(|_| FullDocumentFormError::Operation)?;
    Ok(compiled)
}

type States<'a> = BTreeMap<LogicalId, (&'a str, String, String)>;
struct GraphBudget(usize);
impl std::io::Write for GraphBudget {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        self.0 = self
            .0
            .checked_add(bytes.len())
            .filter(|size| *size <= 32 * 1024 * 1024)
            .ok_or_else(|| std::io::Error::other("FULL_DOCUMENT_FORM_GRAPH_BUDGET"))?;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}
fn apply(
    flow: &mut Flow,
    states: &States<'_>,
    seen: &mut BTreeSet<LogicalId>,
) -> Result<(), FullDocumentFormError> {
    for node in &mut flow.children {
        match node {
            Node::FormControl(node) => {
                let (kind, source, target) = states
                    .get(&node.common.node_id)
                    .ok_or(FullDocumentFormError::Inventory)?;
                if !seen.insert(node.common.node_id.clone())
                    || node.control_kind != *kind
                    || !node.properties.iter().any(|(key, value)| {
                        key == STATE
                            && matches!(value,
                        PropertyValue::Text(text) if text == source)
                    })
                {
                    return Err(FullDocumentFormError::Inventory);
                }
                if source != target {
                    node.properties
                        .insert(STATE, PropertyValue::Text(target.clone()));
                }
            }
            Node::Table(table) => {
                for cell in &mut table.cells {
                    apply(&mut cell.body, states, seen)?;
                }
            }
            Node::Drawing(drawing) => apply(&mut drawing.children, states, seen)?,
            _ => {}
        }
    }
    Ok(())
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FullDocumentFormError {
    #[error("FULL_DOCUMENT_FORM_GRAPH_REJECTED")]
    Graph,
    #[error("FULL_DOCUMENT_FORM_BINDING_DRIFT")]
    Binding,
    #[error("FULL_DOCUMENT_FORM_INVENTORY_PROJECTION_REJECTED")]
    Projection,
    #[error("FULL_DOCUMENT_FORM_PROTECTED_GRAPH_REJECTED")]
    Security,
    #[error("FULL_DOCUMENT_FORM_INVENTORY_STATE_REJECTED")]
    Inventory,
    #[error("FULL_DOCUMENT_FORM_OPERATION_REJECTED")]
    Operation,
    #[error("FULL_DOCUMENT_FORM_SIGNED_ROUTE_UNQUALIFIED")]
    RouteUnqualified,
}
