//! Complete caller-owned comment IR preparation on the original model/compiler.
//! Not a native importer, HWPX lowerer, authenticated issuer or execution route.
use std::{collections::{BTreeMap, BTreeSet}, fmt};
use domain_ir::{
    ArgumentDraft, ArgumentKind, ArgumentSpec, CapabilityCatalog, CapabilityDefinitionDraft,
    CapabilityId, CommentAnchor, CommentBuilder, CommentDocumentState, CommentLimitConfig,
    CommentLimits, CommentOperation, CommentPlan, CommentRequest, CompiledOperationPlan,
    DefaultPolicy, DocumentGraph, DocumentGraphLimits, Flow, LogicalId, Node, OperationDraft,
    OperationId, OperationPlanCompiler, OperationPlanDraft, OperationPlanLimits, PlanId,
    Properties, PropertyValue, ReviewEntry, RevisionId, Section, Selector, SelectorDraft, SelectorLimits,
    SelectorSnapshot,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use crate::form_value_operation::full_document::FullDocumentFormContext;

pub const COMMENT_STATE_PROPERTY: &str = "p09_complete_comment_state_json";
pub const COMMENT_ENTRY_PROPERTY: &str = "p09_complete_comment_entry_json";
pub const COMMENT_STYLE_PROPERTY: &str = "p09_complete_comment_style_json";
pub const COMMENT_SECTION_PROPERTY: &str = "p09_complete_comment_section_json";
const PROFILE: &str = "hwpx-agent.product-comment-full-ir-preparation/v1";

/// Explicit caller-owned logical anchor binding; not a mapping of native run coordinates.
#[derive(Clone)]
pub struct CommentInsertionTarget {
    pub anchor: CommentAnchor,
    pub node_id: LogicalId,
}
impl fmt::Debug for CommentInsertionTarget {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("CommentInsertionTarget(<redacted>)")
    }
}

/// Full caller IR and exact complete ordered state; source imports remain unqualified.
pub struct CommentOperationContext<'a> {
    graph: &'a DocumentGraph,
    state: &'a CommentDocumentState,
    graph_sha: [u8; 32],
    package_sha: [u8; 32],
    revision: RevisionId,
    flow_sha: String,
    node_sections: BTreeMap<LogicalId, LogicalId>,
}
impl fmt::Debug for CommentOperationContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("CommentOperationContext(<redacted>)")
    }
}
impl<'a> CommentOperationContext<'a> {
    /// Reuses existing full-IR admission; checks complete section/style/review inventories.
    /// # Errors
    /// Rejects partial imports, protection, drift, missing/extra/misordered or conflicting views.
    pub fn bind(
        graph: &'a DocumentGraph,
        state: &'a CommentDocumentState,
        graph_sha: [u8; 32],
        package_sha: [u8; 32],
        revision: RevisionId,
    ) -> Result<Self, CommentOperationError> {
        FullDocumentFormContext::bind(graph, graph_sha, package_sha, revision.clone())
            .map_err(|_| CommentOperationError::Admission)?;
        let node_sections = validate_views(graph, state)?;
        let draft = graph.clone().into_draft();
        let flow_sha = hex::encode(Sha256::digest(
            serde_json::to_vec(&(&draft.sections, &draft.notes))
                .map_err(|_| CommentOperationError::Limit)?,
        ));
        Ok(Self {graph, state, graph_sha, package_sha, revision, flow_sha, node_sections})
    }
    #[must_use]
    pub fn document_flow_sha256(&self) -> &str { &self.flow_sha }
}

#[derive(Clone, Eq, PartialEq, Serialize, Debug)]
pub struct CommentOperationReceipt {
    pub profile: &'static str,
    pub capability_id: String,
    pub source_graph_sha256: String,
    pub target_graph_sha256: String,
    pub source_package_sha256: String,
    pub source_comment_state_sha256: String,
    pub target_comment_state_sha256: String,
    pub original_comment_plan_sha256: String,
    pub compiled_operation_sha256: String,
    pub selected_nodes: usize,
    pub qualification: &'static str,
    pub native_author_time_state_verified: bool,
    pub hwpx_lowered: bool,
    pub execution_authority_verified: bool,
}

/// No deserializer or mutable plan/receipt access; every verification rebuilds.
pub struct PreparedCommentOperation {
    plan_id: PlanId,
    request: Vec<u8>,
    insertion: Option<CommentInsertionTarget>,
    domain: CommentPlan,
    target: DocumentGraph,
    compiled: CompiledOperationPlan,
    receipt: CommentOperationReceipt,
}
impl fmt::Debug for PreparedCommentOperation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedCommentOperation(<redacted>)")
    }
}
impl PreparedCommentOperation {
    #[must_use]
    pub const fn target_graph(&self) -> &DocumentGraph { &self.target }
    #[must_use]
    pub const fn compiled(&self) -> &CompiledOperationPlan { &self.compiled }
    #[must_use]
    pub const fn receipt(&self) -> &CommentOperationReceipt { &self.receipt }
    /// Replays the original typed request/compiler against the fresh full context.
    /// # Errors
    /// Rejects document, package, revision, graph, ordered state, target or plan drift.
    pub fn verify(&self, context: &CommentOperationContext<'_>)
        -> Result<CommentOperationReceipt, CommentOperationError> {
        let rebuilt = CommentOperationPreparation::prepare_json(
            context, self.plan_id.clone(), &self.request, self.insertion.clone())?;
        if rebuilt.target != self.target || rebuilt.compiled != self.compiled
            || rebuilt.domain != self.domain || rebuilt.receipt != self.receipt {
            return Err(CommentOperationError::Binding);
        }
        Ok(self.receipt.clone())
    }
    /// Preparation is not current native/issuer/execution/publication authority.
    /// # Errors
    /// Always denies the unqualified route after revalidating the complete preparation.
    pub fn require_current_product_route(&self, context: &CommentOperationContext<'_>)
        -> Result<(), CommentOperationError> {
        self.verify(context)?;
        Err(CommentOperationError::RouteUnqualified)
    }
}

#[derive(Debug)]
pub struct CommentOperationPreparation;
impl CommentOperationPreparation {
    /// Connects all five original comment operations to real caller full-IR views and paths.
    /// # Errors
    /// Rejects strict request/flow/state drift, stale anchors, missing views or compiler limits.
    pub fn prepare_json(
        context: &CommentOperationContext<'_>, plan_id: PlanId, json: &[u8],
        insertion: Option<CommentInsertionTarget>,
    ) -> Result<PreparedCommentOperation, CommentOperationError> {
        // Admission/state matching is repeated before retaining the bounded request.
        let _ = CommentOperationContext::bind(context.graph, context.state,
            context.graph_sha, context.package_sha, context.revision.clone())?;
        let limits = limits()?;
        let request = CommentRequest::from_json(json, context.state, &context.flow_sha, limits)
            .map_err(|_| CommentOperationError::Request)?;
        let canonical: serde_json::Value = serde_json::from_slice(
            &request.canonical_json(limits).map_err(|_| CommentOperationError::Limit)?)
            .map_err(|_| CommentOperationError::Request)?;
        // These operations do not rewrite unrelated body flows.
        if canonical["target_document_flow_sha256"].as_str() != Some(&context.flow_sha) {
            return Err(CommentOperationError::Binding);
        }
        let domain = CommentBuilder::plan(context.state, &request, &context.flow_sha, limits)
            .map_err(|_| CommentOperationError::Request)?;
        let result = CommentBuilder::build(&domain, context.state, &context.flow_sha, limits)
            .map_err(|_| CommentOperationError::Binding)?;
        let mut draft = context.graph.clone().into_draft();
        let source_views = views(context.state)?;
        let mut selected = BTreeSet::new();
        match request.operation() {
            CommentOperation::InsertComment {comment, insertion_index} => {
                let binding = insertion.as_ref().ok_or(CommentOperationError::Anchor)?;
                if binding.anchor != comment.anchor
                    || context.node_sections.get(&binding.node_id) != Some(&binding.anchor.section_id) {
                    return Err(CommentOperationError::Anchor);
                }
                let index = if *insertion_index < context.state.comments().len() {
                    let next = &context.state.comments()[*insertion_index].identity.logical_comment_id;
                    draft.review.iter().position(|v| &v.review_id == next)
                        .ok_or(CommentOperationError::Inventory)?
                } else if let Some(last) = context.state.comments().last() {
                    draft.review.iter().position(|v| v.review_id == last.identity.logical_comment_id)
                        .ok_or(CommentOperationError::Inventory)? + 1
                } else { draft.review.len() };
                let mut properties = Properties::new();
                properties.insert(COMMENT_ENTRY_PROPERTY, PropertyValue::Text(
                    serde_json::to_string(comment).map_err(|_| CommentOperationError::Limit)?));
                draft.review.insert(index, ReviewEntry {
                    review_id: comment.identity.logical_comment_id.clone(),
                    target_node_id: binding.node_id.clone(), properties,
                });
                selected.insert(binding.node_id.clone());
            }
            operation => {
                if insertion.is_some() { return Err(CommentOperationError::Anchor); }
                let ids: Vec<_> = match operation {
                    CommentOperation::SetHiddenExplanation {target, ..} =>
                        vec![&target.logical_explanation_id],
                    CommentOperation::SetVisibility {target, ..}
                        | CommentOperation::SetResolution {target, ..} =>
                        vec![&target.logical_comment_id],
                    CommentOperation::ReplaceStyle {style_id, ..} => context.state.comments()
                        .iter().filter(|c| c.style_id == *style_id)
                        .map(|c| &c.identity.logical_comment_id).collect(),
                    CommentOperation::InsertComment {..} => return Err(CommentOperationError::Binding),
                };
                for id in ids {
                    selected.insert(draft.review.iter().find(|v| &v.review_id == id)
                        .ok_or(CommentOperationError::Inventory)?.target_node_id.clone());
                }
                if let CommentOperation::ReplaceStyle {style_id, ..} = operation {
                    // Global style changes include every declaring section, including empty ones.
                    for section in context.state.sections().iter()
                        .filter(|s| s.memo_shape_id_ref == *style_id) {
                        let body = &draft.sections.iter().find(|s| s.section_id == section.section_id)
                            .ok_or(CommentOperationError::Inventory)?.body;
                        selected.insert(body.children.first().ok_or(CommentOperationError::Anchor)?
                            .common().node_id.clone());
                    }
                }
            }
        }
        if selected.is_empty() { return Err(CommentOperationError::Anchor); }
        let target_views = views(&result.state)?;
        for entry in &mut draft.review {
            if source_views.entries.contains_key(&entry.review_id) {
                entry.properties.insert(COMMENT_ENTRY_PROPERTY, PropertyValue::Text(
                    target_views.entries.get(&entry.review_id)
                        .ok_or(CommentOperationError::Inventory)?.1.clone()));
            }
        }
        let style_ids: BTreeMap<_, _> = source_views.styles.iter()
            .map(|(id, value)| (value.as_str(), *id)).collect();
        for style in &mut draft.styles {
            if let Some(value) = text(&style.properties, COMMENT_STYLE_PROPERTY) {
                let before = style_ids.get(value)
                    .ok_or(CommentOperationError::Inventory)?;
                let after = target_views.styles.get(before)
                    .ok_or(CommentOperationError::Inventory)?.clone();
                style.properties.insert(COMMENT_STYLE_PROPERTY, PropertyValue::Text(after));
            }
        }
        draft.metadata.insert(COMMENT_STATE_PROPERTY, PropertyValue::Text(
            state_json(&result.state)?));
        let target = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| CommentOperationError::Inventory)?;
        validate_views(&target, &result.state)?;
        let target_sha = hex::encode(target.canonical_sha256()
            .map_err(|_| CommentOperationError::Limit)?);
        let compiled = compile(context, plan_id.clone(), &domain, &selected, &target_sha)?;
        let receipt = CommentOperationReceipt {
            profile: PROFILE, capability_id: domain.capability_id().into(),
            source_graph_sha256: hex::encode(context.graph_sha), target_graph_sha256: target_sha,
            source_package_sha256: hex::encode(context.package_sha),
            source_comment_state_sha256: context.state.canonical_sha256(limits)
                .map_err(|_| CommentOperationError::Limit)?,
            target_comment_state_sha256: result.state.canonical_sha256(limits)
                .map_err(|_| CommentOperationError::Limit)?,
            original_comment_plan_sha256: domain.plan_sha256().into(),
            compiled_operation_sha256: hex::encode(compiled.canonical_sha256()
                .map_err(|_| CommentOperationError::Compiler)?),
            selected_nodes: selected.len(),
            qualification: "caller_complete_typed_IR_only_native_import_lowering_issuer_execution_publication_gate_unqualified",
            native_author_time_state_verified: false, hwpx_lowered: false,
            execution_authority_verified: false,
        };
        Ok(PreparedCommentOperation {plan_id, request: json.to_vec(), insertion,
            domain, target, compiled, receipt})
    }
}

struct Views {
    entries: BTreeMap<LogicalId, (CommentAnchor, String)>,
    styles: BTreeMap<u32, String>,
}
fn limits() -> Result<CommentLimits, CommentOperationError> {
    CommentLimits::new(CommentLimitConfig::default()).map_err(|_| CommentOperationError::Limit)
}
fn state_json(state: &CommentDocumentState) -> Result<String, CommentOperationError> {
    String::from_utf8(state.canonical_json(limits()?).map_err(|_| CommentOperationError::Limit)?)
        .map_err(|_| CommentOperationError::Limit)
}
fn views(state: &CommentDocumentState) -> Result<Views, CommentOperationError> {
    let mut entries = BTreeMap::new();
    for entry in state.hidden_explanations() {
        if entries.insert(entry.identity.logical_explanation_id.clone(), (entry.anchor.clone(),
            serde_json::to_string(entry).map_err(|_| CommentOperationError::Limit)?)).is_some() {
            return Err(CommentOperationError::Inventory);
        }
    }
    for entry in state.comments() {
        if entries.insert(entry.identity.logical_comment_id.clone(), (entry.anchor.clone(),
            serde_json::to_string(entry).map_err(|_| CommentOperationError::Limit)?)).is_some() {
            return Err(CommentOperationError::Inventory);
        }
    }
    let styles = state.styles().iter().map(|s| Ok((s.style_id,
        serde_json::to_string(s).map_err(|_| CommentOperationError::Limit)?)))
        .collect::<Result<_, CommentOperationError>>()?;
    Ok(Views {entries, styles})
}
fn text<'a>(properties: &'a Properties, key: &str) -> Option<&'a str> {
    properties.iter().find_map(|(k, v)| if k == key {
        if let PropertyValue::Text(text) = v {Some(text.as_str())} else {None}
    } else {None})
}
fn has(properties: &Properties, key: &str) -> bool {
    properties.iter().any(|(k, _)| k == key)
}
fn validate_views(graph: &DocumentGraph, state: &CommentDocumentState)
    -> Result<BTreeMap<LogicalId, LogicalId>, CommentOperationError> {
    let draft = graph.clone().into_draft();
    if text(&draft.metadata, COMMENT_STATE_PROPERTY) != Some(state_json(state)?.as_str())
        || draft.sections.len() != state.sections().len() {
        return Err(CommentOperationError::Inventory);
    }
    for (section, component) in draft.sections.iter().zip(state.sections()) {
        if section.section_id != component.section_id
            || text(&section.properties, COMMENT_SECTION_PROPERTY)
                != Some(serde_json::to_string(component)
                    .map_err(|_| CommentOperationError::Limit)?.as_str()) {
            return Err(CommentOperationError::Inventory);
        }
    }
    let view = views(state)?;
    let node_sections = index_nodes(&draft.sections);
    let comment_ids: BTreeSet<_> = state.comments().iter()
        .map(|c| &c.identity.logical_comment_id).collect();
    let mut seen = BTreeSet::new();
    let mut comment_order = Vec::new();
    let mut explanation_order = Vec::new();
    for entry in &draft.review {
        if let Some((anchor, json)) = view.entries.get(&entry.review_id) {
            if !seen.insert(entry.review_id.clone())
                || text(&entry.properties, COMMENT_ENTRY_PROPERTY) != Some(json.as_str())
                || node_sections.get(&entry.target_node_id) != Some(&anchor.section_id) {
                return Err(CommentOperationError::Inventory);
            }
            if comment_ids.contains(&entry.review_id) {
                comment_order.push(entry.review_id.clone());
            } else {explanation_order.push(entry.review_id.clone());}
        } else if has(&entry.properties, COMMENT_ENTRY_PROPERTY) {
            return Err(CommentOperationError::Inventory);
        }
    }
    if seen.len() != view.entries.len()
        || comment_order != state.comments().iter().map(|c| c.identity.logical_comment_id.clone()).collect::<Vec<_>>()
        || explanation_order != state.hidden_explanations().iter()
            .map(|c| c.identity.logical_explanation_id.clone()).collect::<Vec<_>>() {
        return Err(CommentOperationError::Inventory);
    }
    let mut styles = BTreeSet::new();
    let style_ids: BTreeMap<_, _> = view.styles.iter()
        .map(|(id, value)| (value.as_str(), *id)).collect();
    for style in &draft.styles {
        if has(&style.properties, COMMENT_STYLE_PROPERTY) {
            let json = text(&style.properties, COMMENT_STYLE_PROPERTY)
                .ok_or(CommentOperationError::Inventory)?;
            let id = style_ids.get(json)
                .ok_or(CommentOperationError::Inventory)?;
            if !styles.insert(*id) {return Err(CommentOperationError::Inventory);}
        }
    }
    if styles.len() != view.styles.len() {return Err(CommentOperationError::Inventory);}
    Ok(node_sections)
}
fn index_nodes(sections: &[Section]) -> BTreeMap<LogicalId, LogicalId> {
    fn walk(flow: &Flow, section: &LogicalId, index: &mut BTreeMap<LogicalId, LogicalId>) {
        for node in &flow.children {
            index.insert(node.common().node_id.clone(), section.clone());
            match node {
                Node::Table(table) => for cell in &table.cells {walk(&cell.body, section, index);},
                Node::Drawing(drawing) => walk(&drawing.children, section, index),
                _ => {},
            }
        }
    }
    let mut index = BTreeMap::new();
    for section in sections {walk(&section.body, &section.section_id, &mut index);}
    index
}
fn compile(context: &CommentOperationContext<'_>, plan_id: PlanId, domain: &CommentPlan,
    selected: &BTreeSet<LogicalId>, target_sha: &str)
    -> Result<CompiledOperationPlan, CommentOperationError> {
    let snapshot = SelectorSnapshot::build(context.graph, context.revision.clone(), SelectorLimits::default())
        .map_err(|_| CommentOperationError::Compiler)?;
    let capability = CapabilityId::parse(domain.capability_id())
        .map_err(|_| CommentOperationError::Compiler)?;
    let mut definition = CapabilityDefinitionDraft::new(capability.clone());
    let args = [
        ("source_graph_sha256", hex::encode(context.graph_sha)),
        ("target_graph_sha256", target_sha.into()),
        ("source_package_sha256", hex::encode(context.package_sha)),
        ("comment_plan_sha256", domain.plan_sha256().into()),
    ];
    for (key, _) in &args {
        definition.arguments.insert((*key).into(), ArgumentSpec {
            kind: ArgumentKind::Text {max_bytes: 64}, required: true,
            default: None, default_policy: DefaultPolicy::Locked,
        });
    }
    let catalog = CapabilityCatalog::from_drafts(vec![definition])
        .map_err(|_| CommentOperationError::Compiler)?;
    let arguments = args.into_iter().map(|(key, value)| (key.into(), ArgumentDraft::Text(value)))
        .collect::<BTreeMap<_, _>>();
    let operations = selected.iter().enumerate().map(|(index, id)| Ok(OperationDraft {
        operation_id: OperationId::parse(format!("comment-{index}"))
            .map_err(|_| CommentOperationError::Compiler)?,
        capability_id: capability.clone(),
        selector: SelectorDraft::one(Selector::by_logical_id(id.clone())),
        arguments: arguments.clone(), depends_on: vec![],
    })).collect::<Result<_, CommentOperationError>>()?;
    OperationPlanCompiler::new(OperationPlanLimits::default())
        .map_err(|_| CommentOperationError::Compiler)?
        .compile(OperationPlanDraft::new(plan_id, context.revision.clone(), operations),
            &catalog, &snapshot, &snapshot.expectation())
        .map_err(|_| CommentOperationError::Compiler)
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum CommentOperationError {
    #[error("COMMENT_FULL_IR_ADMISSION_REJECTED")] Admission,
    #[error("COMMENT_FULL_IR_INVENTORY_REJECTED")] Inventory,
    #[error("COMMENT_FULL_IR_ANCHOR_REJECTED")] Anchor,
    #[error("COMMENT_FULL_IR_REQUEST_REJECTED")] Request,
    #[error("COMMENT_FULL_IR_BINDING_DRIFT")] Binding,
    #[error("COMMENT_FULL_IR_LIMIT")] Limit,
    #[error("COMMENT_FULL_IR_COMPILER_REJECTED")] Compiler,
    #[error("COMMENT_CURRENT_PRODUCT_ROUTE_UNQUALIFIED")] RouteUnqualified,
}
