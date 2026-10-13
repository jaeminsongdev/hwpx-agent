//! Faithful full-form inventory selection and compiled atomic value operations.
//! Selection projection is NOT a full document graph, native structure or signed route.
use crate::form_value_preparation::{
    FormValueContext, FormValuePreparation, FormValuePreparationLimits,
    FormValuePreparationReceipt, PreparedFormValues,
};
use domain_ir::{
    ArgumentDraft, ArgumentKind, ArgumentSpec, CapabilityCatalog, CapabilityDefinitionDraft,
    CapabilityId, CompiledOperationPlan, DefaultPolicy, DocumentGraph, DocumentGraphDraft,
    DocumentGraphLimits, DocumentId, Flow, FormControlLimitConfig, FormControlLimits,
    FormControlNode, FormDocumentState, LogicalId, Node, NodeCommon, OperationDraft, OperationId,
    OperationPlanCompiler, OperationPlanDraft, OperationPlanLimits, PlanId, Properties,
    PropertyValue, RevisionId, Section, Selector, SelectorDraft, SelectorLimits, SelectorSnapshot,
    form_input::{FormInputAccessPolicy, FormInputBuilder, FormInputPlan, FormInputRequest},
};
use hwpx_package::{
    NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackagePolicy,
    native_form_value_output::{NativeFormValueReadback, NativeFormValueReader},
};
use serde::Serialize;
use std::{collections::BTreeMap, fmt};
use thiserror::Error;

pub const FORM_OPERATION_PROFILE: &str = "hwpx-agent.product-form-compiled-values/v1";
const MAX_ID_BYTES: usize = 1024;
const MAX_PLAN_BYTES: usize = 8 * 1024 * 1024;

/// Provider-owned identities, not XML/COM IDs, arbitrary paths or route authorization.
#[derive(Clone)]
pub struct FormOperationIdentity {
    document: DocumentId,
    revision: RevisionId,
    plan: PlanId,
}
impl fmt::Debug for FormOperationIdentity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormOperationIdentity(<redacted>)")
    }
}
impl FormOperationIdentity {
    /// Binds finite validated product identities.
    /// # Errors
    /// Rejects identifier strings outside the preparation envelope.
    pub fn new(
        document: DocumentId,
        revision: RevisionId,
        plan: PlanId,
    ) -> Result<Self, FormOperationError> {
        if [document.as_str(), revision.as_str(), plan.as_str()]
            .iter()
            .any(|s| s.len() > MAX_ID_BYTES)
        {
            return Err(FormOperationError::Limit);
        }
        Ok(Self {
            document,
            revision,
            plan,
        })
    }
}

/// Fresh immutable provider snapshot. Domain/package/output limits stay SDK/product bounded.
pub struct FormOperationContext<'a> {
    source: &'a [u8],
    map: &'a NativeFormPackageMap,
    policies: &'a [NativeFormPackagePolicy],
    prepared_context: FormValueContext<'a>,
}
impl fmt::Debug for FormOperationContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormOperationContext(<redacted>)")
    }
}
impl<'a> FormOperationContext<'a> {
    /// Uses the actual public complete-package binder; caller data cannot authorize a route.
    /// # Errors
    /// Rejects source/map/policy/finite-limit/unsupported-profile failures.
    pub fn bind(
        source: &'a [u8],
        map: &'a NativeFormPackageMap,
        policies: &'a [NativeFormPackagePolicy],
    ) -> Result<Self, FormOperationError> {
        let limits =
            FormValuePreparationLimits::bounded_default().map_err(|_| FormOperationError::Limit)?;
        let prepared_context = FormValueContext::bind(source, map, policies, limits)
            .map_err(|_| FormOperationError::Source)?;
        Ok(Self {
            source,
            map,
            policies,
            prepared_context,
        })
    }
    fn read(&self) -> Result<NativeFormValueReadback, FormOperationError> {
        NativeFormValueReader::read(
            self.source,
            self.map,
            self.policies,
            domain_limits()?,
            NativeFormPackageLimits::default(),
        )
        .map_err(|_| FormOperationError::Source)
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FormOperationReceipt {
    pub profile: &'static str,
    pub selection_projection_sha256: String,
    pub compiled_operation_plan_sha256: String,
    pub typed_input_plan_sha256: String,
    pub source_inventory_controls: usize,
    pub changed_controls: usize,
    pub compiled_operations: usize,
    pub preparation: FormValuePreparationReceipt,
    pub qualification: FormOperationQualification,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormOperationQualification {
    FormInventoryCompilationOnlyFullDocumentImportRoutePublicationNativeAndGateUnqualified,
}

/// Private non-deserializable binding of real typed/compiled plans and whole output.
pub struct PreparedFormOperation {
    identity: FormOperationIdentity,
    typed: FormInputPlan,
    graph: DocumentGraph,
    compiled: CompiledOperationPlan,
    values: PreparedFormValues,
    receipt: FormOperationReceipt,
}
impl fmt::Debug for PreparedFormOperation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedFormOperation(<redacted>)")
    }
}
impl PreparedFormOperation {
    #[must_use]
    pub const fn receipt(&self) -> &FormOperationReceipt {
        &self.receipt
    }
    /// Actual immutable compiler output. It is not a route/manifest or native structure proof.
    #[must_use]
    pub const fn compiled_plan(&self) -> &CompiledOperationPlan {
        &self.compiled
    }
    /// Explicit form inventory projection ONLY. Structural indices here are not native positions.
    #[must_use]
    pub const fn selection_projection(&self) -> &DocumentGraph {
        &self.graph
    }
    /// Complete source-qualified memory candidate, NOT an authorized/published artifact.
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.values.candidate_bytes()
    }
    /// Rereads and rebuilds the real typed result, entire form graph and complete compiler plan.
    /// # Errors
    /// Rejects fresh provider/access drift, altered state/plan/receipt or output mismatch.
    pub fn verify(
        &self,
        fresh: &FormOperationContext<'_>,
        access: &FormInputAccessPolicy,
    ) -> Result<FormOperationReceipt, FormOperationError> {
        let value_receipt = self
            .values
            .verify(&fresh.prepared_context, access)
            .map_err(|_| FormOperationError::Drift)?;
        let observed = fresh.read()?;
        let result = FormInputBuilder::build(
            &self.typed,
            observed.state(),
            observed.native_v1().document_flow_sha256(),
            access,
            domain_limits()?,
        )
        .map_err(|_| FormOperationError::Drift)?;
        if result.receipt.plan_sha256 != value_receipt.component.typed_input_plan_sha256
            || result.receipt.target_state_sha256 != value_receipt.component.target_v2_state_sha256
        {
            return Err(FormOperationError::Drift);
        }
        let (graph, compiled) = compile_real(&self.identity, &self.typed, &value_receipt)?;
        let receipt = make_receipt(&graph, &compiled, &self.typed, value_receipt)?;
        if graph != self.graph || compiled != self.compiled || receipt != self.receipt {
            return Err(FormOperationError::Drift);
        }
        Ok(receipt)
    }
    /// Actual existing VS0 authority cannot authorize these form operations.
    /// # Errors
    /// Rejects changed preparation first, then always denies the unsupported signed form scope.
    pub fn require_current_product_route(
        &self,
        fresh: &FormOperationContext<'_>,
        access: &FormInputAccessPolicy,
    ) -> Result<(), FormOperationError> {
        self.verify(fresh, access)?;
        self.values
            .require_current_product_route(&fresh.prepared_context, access)
            .map_err(|_| FormOperationError::RouteUnqualified)
    }
}

#[derive(Debug)]
pub struct FormOperationPreparation;
impl FormOperationPreparation {
    /// Compiles exactly all changed controls from one real full-document atomic typed operation.
    /// # Errors
    /// Rejects request/access/package/plan drift, unsupported profiles and finite-limit failures.
    pub fn prepare_json(
        context: &FormOperationContext<'_>,
        identity: FormOperationIdentity,
        json: &[u8],
        access: &FormInputAccessPolicy,
    ) -> Result<PreparedFormOperation, FormOperationError> {
        let observed = context.read()?;
        let request = FormInputRequest::from_json(
            json,
            observed.state(),
            observed.native_v1().document_flow_sha256(),
            domain_limits()?,
        )
        .map_err(|_| FormOperationError::Request)?;
        let typed = FormInputBuilder::plan(
            observed.state(),
            &request,
            observed.native_v1().document_flow_sha256(),
            domain_limits()?,
        )
        .map_err(|_| FormOperationError::Request)?;
        let values = FormValuePreparation::prepare_json(&context.prepared_context, json, access)
            .map_err(|_| FormOperationError::Output)?;
        let (graph, compiled) = compile_real(&identity, &typed, values.receipt())?;
        let receipt = make_receipt(&graph, &compiled, &typed, values.receipt().clone())?;
        let prepared = PreparedFormOperation {
            identity,
            typed,
            graph,
            compiled,
            values,
            receipt,
        };
        prepared.verify(context, access)?;
        Ok(prepared)
    }
}

fn domain_limits() -> Result<FormControlLimits, FormOperationError> {
    FormControlLimits::new(FormControlLimitConfig::default()).map_err(|_| FormOperationError::Limit)
}
fn selection_graph(
    identity: &FormOperationIdentity,
    source: &FormDocumentState,
    receipt: &FormValuePreparationReceipt,
) -> Result<DocumentGraph, FormOperationError> {
    let raw = source
        .canonical_json(domain_limits()?)
        .map_err(|_| FormOperationError::Limit)?;
    let mut nodes = Vec::with_capacity(source.controls().len());
    for control in source.controls() {
        let mut properties = Properties::new();
        properties.insert(
            "complete_control_state_json",
            PropertyValue::Text(
                serde_json::to_string(control).map_err(|_| FormOperationError::Plan)?,
            ),
        );
        nodes.push(Node::FormControl(FormControlNode {
            common: NodeCommon::new(control.identity.logical_control_id.clone()),
            control_kind: control.payload.capability_id().into(),
            properties,
        }));
    }
    // This root is explicitly a global ordered inventory projection, not a fake native section.
    let section_id = LogicalId::parse(format!(
        "form-inventory-{}",
        receipt.provider_context_sha256
    ))
    .map_err(|_| FormOperationError::Plan)?;
    let mut draft = DocumentGraphDraft::new(
        identity.document.clone(),
        vec![Section {
            section_id,
            properties: Properties::new(),
            master_pages: vec![],
            headers_footers: vec![],
            body: Flow { children: nodes },
        }],
    );
    draft.source_profile =
        Some(LogicalId::parse(FORM_OPERATION_PROFILE).map_err(|_| FormOperationError::Plan)?);
    draft.metadata.insert(
        "scope",
        PropertyValue::Text("complete_form_inventory_projection_not_full_document_graph".into()),
    );
    draft.metadata.insert(
        "complete_form_state_json",
        PropertyValue::Text(String::from_utf8(raw).map_err(|_| FormOperationError::Plan)?),
    );
    draft.metadata.insert(
        "source_package_sha256",
        PropertyValue::Text(receipt.component.source_package_sha256.clone()),
    );
    draft.metadata.insert(
        "provider_context_sha256",
        PropertyValue::Text(receipt.provider_context_sha256.clone()),
    );
    draft.security_state.properties.insert(
        "qualification",
        PropertyValue::Text("caller_policy_only_not_native_security_attestation".into()),
    );
    DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits {
            max_serialized_bytes: MAX_PLAN_BYTES,
            max_total_string_bytes: MAX_PLAN_BYTES,
            ..DocumentGraphLimits::default()
        },
    )
    .map_err(|_| FormOperationError::Plan)
}

fn plan_limits() -> OperationPlanLimits {
    OperationPlanLimits {
        max_serialized_bytes: MAX_PLAN_BYTES,
        max_total_argument_bytes: MAX_PLAN_BYTES,
        max_string_bytes: 1024 * 1024,
        ..OperationPlanLimits::default()
    }
}
fn compile_real(
    identity: &FormOperationIdentity,
    typed: &FormInputPlan,
    receipt: &FormValuePreparationReceipt,
) -> Result<(DocumentGraph, CompiledOperationPlan), FormOperationError> {
    if typed.plan_sha256() != receipt.component.typed_input_plan_sha256
        || typed
            .source_state()
            .canonical_sha256(domain_limits()?)
            .map_err(|_| FormOperationError::Plan)?
            != receipt.component.source_v2_state_sha256
        || typed
            .target_state()
            .canonical_sha256(domain_limits()?)
            .map_err(|_| FormOperationError::Plan)?
            != receipt.component.target_v2_state_sha256
    {
        return Err(FormOperationError::Drift);
    }
    let graph = selection_graph(identity, typed.source_state(), receipt)?;
    let snapshot =
        SelectorSnapshot::build(&graph, identity.revision.clone(), SelectorLimits::default())
            .map_err(|_| FormOperationError::Plan)?;
    let mut definitions = BTreeMap::new();
    let mut operations = vec![];
    for (index, (source, target)) in typed
        .source_state()
        .controls()
        .iter()
        .zip(typed.target_state().controls())
        .enumerate()
    {
        if source == target {
            continue;
        }
        if source.identity != target.identity
            || source.payload.capability_id() != target.payload.capability_id()
        {
            return Err(FormOperationError::Drift);
        }
        let capability = CapabilityId::parse(source.payload.capability_id())
            .map_err(|_| FormOperationError::Plan)?;
        let args: BTreeMap<String, ArgumentDraft> = BTreeMap::from([
            (
                "atomic_input_plan_sha256".into(),
                ArgumentDraft::Text(typed.plan_sha256().into()),
            ),
            (
                "native_package_plan_sha256".into(),
                ArgumentDraft::Text(receipt.component.package_plan_sha256.clone()),
            ),
            (
                "provider_context_sha256".into(),
                ArgumentDraft::Text(receipt.provider_context_sha256.clone()),
            ),
            (
                "target_control_state_json".into(),
                ArgumentDraft::Text(
                    serde_json::to_string(target).map_err(|_| FormOperationError::Plan)?,
                ),
            ),
        ]);
        let mut definition = CapabilityDefinitionDraft::new(capability.clone());
        for key in args.keys() {
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
        definitions.insert(capability.clone(), definition);
        operations.push(OperationDraft {
            operation_id: OperationId::parse(format!("form-value-change-{index:06}"))
                .map_err(|_| FormOperationError::Plan)?,
            capability_id: capability,
            selector: SelectorDraft::one(Selector::by_logical_id(
                source.identity.logical_control_id.clone(),
            )),
            arguments: args,
            depends_on: vec![],
        });
    }
    if operations.len() != receipt.component.changed_controls || operations.is_empty() {
        return Err(FormOperationError::Drift);
    }
    let catalog = CapabilityCatalog::from_drafts(definitions.into_values().collect())
        .map_err(|_| FormOperationError::Plan)?;
    let compiled = OperationPlanCompiler::new(plan_limits())
        .map_err(|_| FormOperationError::Limit)?
        .compile(
            OperationPlanDraft::new(identity.plan.clone(), identity.revision.clone(), operations),
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        )
        .map_err(|_| FormOperationError::Plan)?;
    Ok((graph, compiled))
}
fn make_receipt(
    graph: &DocumentGraph,
    compiled: &CompiledOperationPlan,
    typed: &FormInputPlan,
    preparation: FormValuePreparationReceipt,
) -> Result<FormOperationReceipt, FormOperationError> {
    Ok(FormOperationReceipt {
        profile:FORM_OPERATION_PROFILE,
        selection_projection_sha256:hex::encode(graph.canonical_sha256().map_err(|_|FormOperationError::Plan)?),
        compiled_operation_plan_sha256:hex::encode(compiled.canonical_sha256().map_err(|_|FormOperationError::Plan)?),
        typed_input_plan_sha256:typed.plan_sha256().into(),
        source_inventory_controls:typed.source_state().controls().len(),
        changed_controls:preparation.component.changed_controls,
        compiled_operations:compiled.operations().len(),preparation,
        qualification:FormOperationQualification::FormInventoryCompilationOnlyFullDocumentImportRoutePublicationNativeAndGateUnqualified,
    })
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormOperationError {
    #[error("FORM_OPERATION_LIMIT")]
    Limit,
    #[error("FORM_OPERATION_SOURCE_REJECTED")]
    Source,
    #[error("FORM_OPERATION_REQUEST_REJECTED")]
    Request,
    #[error("FORM_OPERATION_OUTPUT_REJECTED")]
    Output,
    #[error("FORM_OPERATION_COMPILER_REJECTED")]
    Plan,
    #[error("FORM_OPERATION_FRESH_BINDING_DRIFT")]
    Drift,
    #[error("FORM_OPERATION_SIGNED_ROUTE_UNQUALIFIED")]
    RouteUnqualified,
}
