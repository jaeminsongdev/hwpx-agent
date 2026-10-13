//! Complete explicit caller-owned review body Flows bound to original comment state/compiler.
//! Not native metadata reconstruction, source-import admission, HWPX lowering or authority.
use super::{
    CommentInsertionTarget, CommentOperationContext, CommentOperationError,
    CommentOperationPreparation, PreparedCommentOperation, compile, limits, select_and_insert,
    text, validate_views,
};
use domain_ir::{
    CommentBuilder, CommentDocumentState, CommentOperation, CommentRequest, CompiledOperationPlan,
    DocumentGraph, DocumentGraphLimits, Flow, LogicalId, Node, PlanId, Properties, PropertyValue,
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    fmt,
    io::{self, Write},
};
use thiserror::Error;

pub const COMMENT_RICH_BODIES_PROPERTY: &str = "p09_complete_comment_rich_bodies_json";
const MAX_BYTES: usize = 8 * 1024 * 1024;
/// Explicit caller IR body, NOT source XML/native subList/cache or execution authority.
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CommentRichBody {
    pub review_id: LogicalId,
    pub body: Flow,
}
impl fmt::Debug for CommentRichBody {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("CommentRichBody(<redacted>)")
    }
}
/// Bounded deterministic typed Flow fingerprint for this caller-owned body contract only.
/// Native subList/plain-text/cache fingerprints retain their original unqualified meaning.
/// # Errors
/// Rejects serialization/8MiB budget failures, never silently truncates or normalizes a Flow.
pub fn body_sha256(body: &Flow) -> Result<String, CommentRichBodyError> {
    Ok(hex::encode(Sha256::digest(encode(body)?)))
}
/// Exact body snapshot text for explicit caller graph construction, not import authority.
/// # Errors
/// Rejects serialization/aggregate8MiB budget errors. Binding subsequently validates contents.
pub fn bodies_json(bodies: &[CommentRichBody]) -> Result<String, CommentRichBodyError> {
    String::from_utf8(encode(&bodies)?).map_err(|_| CommentRichBodyError::Limit)
}
pub struct CommentRichContext<'a, 'graph> {
    base: &'a CommentOperationContext<'graph>,
    bodies: Vec<CommentRichBody>,
    body_json: String,
}
impl fmt::Debug for CommentRichContext<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("CommentRichContext(<redacted>)")
    }
}
impl<'a, 'graph> CommentRichContext<'a, 'graph> {
    /// Complete hidden-explanation order followed by complete comment presentation order.
    /// All bodies match actual typed Flow digests and the EXACT caller graph body property.
    /// Original whole-IR/protection/partial-import admission and graph validator remain mandatory.
    /// # Errors
    /// Rejects missing/extra/reordered/digest-drift body views, invalid IDs/styles/resources/
    /// table geometry/nested structure or any original full context failure.
    pub fn bind(
        base: &'a CommentOperationContext<'graph>,
        bodies: Vec<CommentRichBody>,
    ) -> Result<Self, CommentRichBodyError> {
        CommentOperationContext::bind(
            base.graph,
            base.state,
            base.graph_sha,
            base.package_sha,
            base.revision.clone(),
        )?;
        let body_json = bodies_json(&bodies)?;
        if text(
            &base.graph.clone().into_draft().metadata,
            COMMENT_RICH_BODIES_PROPERTY,
        ) != Some(body_json.as_str())
        {
            return Err(CommentRichBodyError::Binding);
        }
        validate_bodies(
            base.graph,
            base.state,
            &bodies,
            base.package_sha,
            &base.revision,
        )?;
        Ok(Self {
            base,
            bodies,
            body_json,
        })
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CommentRichReceipt {
    pub qualification: &'static str,
    pub source_graph_sha256: String,
    pub target_graph_sha256: String,
    pub source_body_snapshot_sha256: String,
    pub target_body_snapshot_sha256: String,
    pub original_comment_plan_sha256: String,
    pub final_compiled_operation_sha256: String,
    pub source_bodies: usize,
    pub target_bodies: usize,
    pub native_metadata_verified: bool,
    pub hwpx_lowered: bool,
    pub execution_authority_verified: bool,
}
pub struct PreparedRichCommentOperation {
    original: PreparedCommentOperation,
    inserted_body: Option<CommentRichBody>,
    target: DocumentGraph,
    bodies: Vec<CommentRichBody>,
    compiled: CompiledOperationPlan,
    receipt: CommentRichReceipt,
}
impl fmt::Debug for PreparedRichCommentOperation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedRichCommentOperation(<redacted>)")
    }
}
#[derive(Debug)]
pub struct RichCommentOperationPreparation;
impl RichCommentOperationPreparation {
    /// Reuses the original strict request, CommentBuilder and compiler for all five operations.
    /// New insertion MUST carry its actual explicit Flow; other operations MUST NOT carry one.
    /// The final compiler binds the final rich-body graph hash, never the intermediate hash.
    /// # Errors
    /// Rejects all original errors or incomplete/detached/nonmatching source/target bodies.
    pub fn prepare_json(
        context: &CommentRichContext<'_, '_>,
        plan_id: PlanId,
        json: &[u8],
        insertion: Option<CommentInsertionTarget>,
        inserted_body: Option<CommentRichBody>,
    ) -> Result<PreparedRichCommentOperation, CommentRichBodyError> {
        let _ = CommentRichContext::bind(context.base, context.bodies.clone())?;
        let original = CommentOperationPreparation::prepare_json(
            context.base,
            plan_id.clone(),
            json,
            insertion,
        )?;
        let request =
            CommentRequest::from_json(json, context.base.state, &context.base.flow_sha, limits()?)
                .map_err(|_| CommentRichBodyError::Operation(CommentOperationError::Request))?;
        let result = CommentBuilder::build(
            &original.domain,
            context.base.state,
            &context.base.flow_sha,
            limits()?,
        )
        .map_err(|_| CommentRichBodyError::Binding)?;
        let mut bodies = context.bodies.clone();
        match (request.operation(), &inserted_body) {
            (
                CommentOperation::InsertComment {
                    insertion_index,
                    comment,
                },
                Some(body),
            ) if body.review_id == comment.identity.logical_comment_id => {
                let index = context
                    .base
                    .state
                    .hidden_explanations()
                    .len()
                    .checked_add(*insertion_index)
                    .filter(|i| *i <= bodies.len())
                    .ok_or(CommentRichBodyError::Inventory)?;
                bodies.insert(index, body.clone());
            }
            (CommentOperation::InsertComment { .. }, _) => {
                return Err(CommentRichBodyError::Inventory);
            }
            (_, Some(_)) => return Err(CommentRichBodyError::Inventory),
            (_, None) => {}
        }
        let target_json = bodies_json(&bodies)?;
        let mut draft = original.target.clone().into_draft();
        draft.metadata.insert(
            COMMENT_RICH_BODIES_PROPERTY,
            PropertyValue::Text(target_json.clone()),
        );
        let target = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| CommentRichBodyError::Graph)?;
        validate_views(&target, &result.state)?;
        CommentOperationContext::bind(
            &target,
            &result.state,
            target
                .canonical_sha256()
                .map_err(|_| CommentRichBodyError::Graph)?,
            context.base.package_sha,
            context.base.revision.clone(),
        )?;
        validate_bodies(
            &target,
            &result.state,
            &bodies,
            context.base.package_sha,
            &context.base.revision,
        )?;
        let target_sha = hex::encode(
            target
                .canonical_sha256()
                .map_err(|_| CommentRichBodyError::Graph)?,
        );
        let mut selection = context.base.graph.clone().into_draft();
        let selected = select_and_insert(
            &mut selection,
            context.base,
            request.operation(),
            original.insertion.as_ref(),
        )?;
        let compiled = compile(
            context.base,
            plan_id,
            &original.domain,
            &selected,
            &target_sha,
        )?;
        let receipt = CommentRichReceipt {
            qualification: "caller_complete_review_Flow_body_hash_and_final_original_compiler_binding_NOT_native_import_plain_cache_HWPX_lowering_issuer_execution_publication_or_Gate",
            source_graph_sha256: hex::encode(context.base.graph_sha),
            target_graph_sha256: target_sha,
            source_body_snapshot_sha256: hex::encode(Sha256::digest(context.body_json.as_bytes())),
            target_body_snapshot_sha256: hex::encode(Sha256::digest(target_json.as_bytes())),
            original_comment_plan_sha256: original.domain.plan_sha256().into(),
            final_compiled_operation_sha256: hex::encode(
                compiled
                    .canonical_sha256()
                    .map_err(|_| CommentRichBodyError::Graph)?,
            ),
            source_bodies: context.bodies.len(),
            target_bodies: bodies.len(),
            native_metadata_verified: false,
            hwpx_lowered: false,
            execution_authority_verified: false,
        };
        Ok(PreparedRichCommentOperation {
            original,
            inserted_body,
            target,
            bodies,
            compiled,
            receipt,
        })
    }
}
impl PreparedRichCommentOperation {
    #[must_use]
    pub const fn target_graph(&self) -> &DocumentGraph {
        &self.target
    }
    #[must_use]
    pub fn target_bodies(&self) -> &[CommentRichBody] {
        &self.bodies
    }
    #[must_use]
    pub const fn compiled(&self) -> &CompiledOperationPlan {
        &self.compiled
    }
    #[must_use]
    pub const fn receipt(&self) -> &CommentRichReceipt {
        &self.receipt
    }
    /// Replays original preparation and all rich-body/final compiler bindings on fresh caller IR.
    /// # Errors
    /// Rejects any original context/request or whole source/target Flow/graph/plan/receipt drift.
    pub fn verify(
        &self,
        context: &CommentRichContext<'_, '_>,
    ) -> Result<CommentRichReceipt, CommentRichBodyError> {
        self.original.verify(context.base)?;
        let rebuilt = RichCommentOperationPreparation::prepare_json(
            context,
            self.original.plan_id.clone(),
            &self.original.request,
            self.original.insertion.clone(),
            self.inserted_body.clone(),
        )?;
        if rebuilt.target != self.target
            || rebuilt.bodies != self.bodies
            || rebuilt.compiled != self.compiled
            || rebuilt.receipt != self.receipt
        {
            return Err(CommentRichBodyError::Binding);
        }
        Ok(self.receipt.clone())
    }
    /// Actual native/source/issuer/atomic execution/publication remains unqualified.
    /// # Errors
    /// Always denies after fresh complete caller IR/typed body/compiled plan verification.
    pub fn require_current_product_route(
        &self,
        context: &CommentRichContext<'_, '_>,
    ) -> Result<(), CommentRichBodyError> {
        self.verify(context)?;
        Err(CommentOperationError::RouteUnqualified.into())
    }
}
fn validate_bodies(
    graph: &DocumentGraph,
    state: &CommentDocumentState,
    bodies: &[CommentRichBody],
    package_sha: [u8; 32],
    revision: &domain_ir::RevisionId,
) -> Result<(), CommentRichBodyError> {
    // Count/byte checks precede cloning a potentially large body validation graph.
    let expected = state
        .hidden_explanations()
        .iter()
        .map(|e| {
            (
                &e.identity.logical_explanation_id,
                &e.anchor.section_id,
                &e.body_graph_sha256,
            )
        })
        .chain(state.comments().iter().map(|c| {
            (
                &c.identity.logical_comment_id,
                &c.anchor.section_id,
                &c.body_graph_sha256,
            )
        }))
        .collect::<Vec<_>>();
    if expected.len() != bodies.len() {
        return Err(CommentRichBodyError::Inventory);
    }
    let _ = bodies_json(bodies)?;
    let mut validation = graph.clone().into_draft();
    for (body, (id, section, digest)) in bodies.iter().zip(expected) {
        if &body.review_id != id || body_sha256(&body.body)? != *digest {
            return Err(CommentRichBodyError::Binding);
        }
        let target = validation
            .sections
            .iter_mut()
            .find(|s| &s.section_id == section)
            .ok_or(CommentRichBodyError::Inventory)?;
        target.body.children.extend(body.body.children.clone());
    }
    // Only a disposable graph validates original complete resources/styles/ID/nesting/table
    // limits. Review bodies NEVER become main document content in the returned target.
    let validation = DocumentGraph::from_draft(validation, DocumentGraphLimits::default())
        .map_err(|_| CommentRichBodyError::Graph)?;
    // Reuse the original DOCUMENT protection/partial admission and whole-graph byte budget.
    // It does not interpret nested caller property flags or native protection metadata.
    crate::form_value_operation::full_document::FullDocumentFormContext::bind(
        &validation,
        validation
            .canonical_sha256()
            .map_err(|_| CommentRichBodyError::Graph)?,
        package_sha,
        revision.clone(),
    )
    .map_err(|_| CommentRichBodyError::Graph)?;
    for body in bodies {
        reject_caller_body_protection(&body.body)?;
    }
    Ok(())
}
// Conservative caller-IR convention ONLY. Explicit protected/locked/read_only properties
// must be Boolean(false); other types are unknown, not evidence of an unlocked body.
// This never reconstructs native protection or authorizes an actual source/product route.
fn reject_caller_body_protection(flow: &Flow) -> Result<(), CommentRichBodyError> {
    let mut pending = vec![flow];
    while let Some(flow) = pending.pop() {
        for node in &flow.children {
            reject_property_flags(&node.common().semantics)?;
            reject_property_flags(&node.common().layout_hints)?;
            match node {
                Node::Paragraph(n) => reject_property_flags(&n.paragraph_properties)?,
                Node::Table(n) => {
                    reject_property_flags(&n.properties)?;
                    for cell in &n.cells {
                        reject_property_flags(&cell.properties)?;
                        pending.push(&cell.body);
                    }
                }
                Node::Drawing(n) => {
                    reject_property_flags(&n.properties)?;
                    pending.push(&n.children);
                }
                Node::Equation(n) => reject_property_flags(&n.properties)?,
                Node::Chart(n) => reject_property_flags(&n.properties)?,
                Node::Field(n) => reject_property_flags(&n.properties)?,
                Node::FormControl(n) => reject_property_flags(&n.properties)?,
                Node::EmbeddedObject(n) => reject_property_flags(&n.properties)?,
                Node::Break(_) => {}
            }
        }
    }
    Ok(())
}
fn reject_property_flags(properties: &Properties) -> Result<(), CommentRichBodyError> {
    let mut pending = properties.iter().collect::<Vec<_>>();
    while let Some((key, value)) = pending.pop() {
        if matches!(key, "protected" | "locked" | "read_only")
            && !matches!(value, PropertyValue::Boolean(false))
        {
            return Err(CommentRichBodyError::Protection);
        }
        match value {
            PropertyValue::Object(object) => {
                pending.extend(object.iter().map(|(key, value)| (key.as_str(), value)));
            }
            PropertyValue::List(list) => pending.extend(list.iter().map(|value| ("", value))),
            _ => {}
        }
    }
    Ok(())
}
struct Budget(Vec<u8>);
impl Write for Budget {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        if self
            .0
            .len()
            .checked_add(bytes.len())
            .is_none_or(|n| n > MAX_BYTES)
        {
            return Err(io::Error::other("comment_rich_body_budget"));
        }
        self.0.extend_from_slice(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn encode<T: Serialize>(value: &T) -> Result<Vec<u8>, CommentRichBodyError> {
    let mut budget = Budget(Vec::new());
    serde_json::to_writer(&mut budget, value).map_err(|_| CommentRichBodyError::Limit)?;
    Ok(budget.0)
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum CommentRichBodyError {
    #[error(transparent)]
    Operation(#[from] CommentOperationError),
    #[error("COMMENT_RICH_BODY_BINDING_DRIFT")]
    Binding,
    #[error("COMMENT_RICH_BODY_INVENTORY_REJECTED")]
    Inventory,
    #[error("COMMENT_RICH_BODY_ORIGINAL_GRAPH_VALIDATION_REJECTED")]
    Graph,
    #[error("COMMENT_RICH_BODY_LIMIT")]
    Limit,
    #[error("COMMENT_RICH_BODY_CALLER_PROTECTION_REJECTED")]
    Protection,
}
