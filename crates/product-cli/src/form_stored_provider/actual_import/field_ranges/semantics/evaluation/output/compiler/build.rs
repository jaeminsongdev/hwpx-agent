use super::{
    PreparedStoredFormulaResults, StoredFormulaCompilerError as Error, StoredFormulaCompilerReceipt,
};
use domain_ir::{
    ArgumentDraft, ArgumentKind, ArgumentSpec, CapabilityCatalog, CapabilityDefinitionDraft,
    CapabilityId, CompiledOperationPlan, DefaultPolicy, FormulaCache, FormulaValue, OperationDraft,
    OperationId, OperationPlanCompiler, OperationPlanDraft, OperationPlanLimits, PlanId,
    RevisionId, Selector, SelectorDraft, SelectorLimits, SelectorSnapshot,
};
use hwpx_package::document_import::fields::semantics::ImportedFieldMeaning;
use std::collections::BTreeMap;

pub(super) fn compile(
    results: &PreparedStoredFormulaResults<'_, '_, '_, '_>,
    plan_id: PlanId,
) -> Result<CompiledOperationPlan, Error> {
    let evaluation = results.evaluation;
    let source = &evaluation.meanings.ranges.source.source;
    let revision = RevisionId::parse(source.head.revision_id().ok_or(Error::Binding)?.public_id())
        .map_err(|_| Error::Binding)?;
    let graph = evaluation.meanings.graph();
    let snapshot = SelectorSnapshot::build(graph, revision.clone(), SelectorLimits::default())
        .map_err(|_| Error::Compilation)?;
    let capability = CapabilityId::parse("table.formula").map_err(|_| Error::Compilation)?;
    let catalog = catalog(&capability)?;
    let values: BTreeMap<_, _> = evaluation
        .values()
        .iter()
        .map(|v| (&v.reference_id, v))
        .collect();
    let meanings: BTreeMap<_, _> = evaluation
        .meanings
        .imported
        .observations()
        .iter()
        .map(|m| (&m.reference_id, m))
        .collect();
    if values.len() != evaluation.values().len()
        || meanings.len() != evaluation.meanings.imported.observations().len()
    {
        return Err(Error::Binding);
    }
    let mut operations = Vec::new();
    for (index, field) in evaluation
        .meanings
        .ranges
        .imported
        .fields()
        .iter()
        .enumerate()
    {
        let Some(value) = values.get(&field.reference_id) else {
            continue;
        };
        let meaning = meanings.get(&field.reference_id).ok_or(Error::Binding)?;
        let ImportedFieldMeaning::TableFormula { formula, .. } = &meaning.meaning else {
            return Err(Error::Binding);
        };
        if value.begin_anchor != field.begin_anchor || value.coordinate != formula.owner() {
            return Err(Error::Binding);
        }
        if matches!(formula.cache(), FormulaCache::Unverified { value:FormulaValue::Decimal { value:cached } } if cached == &value.value)
        {
            continue;
        }
        operations.push(OperationDraft {
            operation_id: OperationId::parse(format!("formula-result-{index:06}"))
                .map_err(|_| Error::Compilation)?,
            capability_id: capability.clone(),
            selector: SelectorDraft::one(Selector::by_logical_id(field.begin_node_id.clone())),
            arguments: arguments(results, &value.value)?,
            depends_on: vec![],
        });
    }
    if operations.is_empty() || operations.len() != results.receipt().changed_formula_results {
        return Err(Error::Binding);
    }
    // Original batch's finite4096 leaf-intent budget permits at most1365 changed formulas.
    let limits = OperationPlanLimits {
        max_operations: 1365,
        max_dependencies: 4096,
        max_arguments_per_operation: 16,
        max_string_bytes: 4096,
        max_total_argument_bytes: 2 * 1024 * 1024,
        max_serialized_bytes: 8 * 1024 * 1024,
    };
    OperationPlanCompiler::new(limits)
        .map_err(|_| Error::Compilation)?
        .compile(
            OperationPlanDraft::new(plan_id, revision, operations),
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        )
        .map_err(|_| Error::Compilation)
}

fn catalog(capability: &CapabilityId) -> Result<CapabilityCatalog, Error> {
    let mut definition = CapabilityDefinitionDraft::new(capability.clone());
    for name in [
        "source_package_sha256",
        "candidate_package_sha256",
        "computed_values_sha256",
        "target_decimal_json",
    ] {
        definition.arguments.insert(
            name.into(),
            ArgumentSpec {
                kind: ArgumentKind::Text { max_bytes: 4096 },
                required: true,
                default: None,
                default_policy: DefaultPolicy::Locked,
            },
        );
    }
    CapabilityCatalog::from_drafts(vec![definition]).map_err(|_| Error::Compilation)
}

fn arguments(
    results: &PreparedStoredFormulaResults<'_, '_, '_, '_>,
    value: &domain_ir::FormulaDecimal,
) -> Result<BTreeMap<String, ArgumentDraft>, Error> {
    let output = results.receipt();
    Ok(BTreeMap::from([
        (
            "source_package_sha256".into(),
            ArgumentDraft::Text(hex::encode(output.source_package_sha256)),
        ),
        (
            "candidate_package_sha256".into(),
            ArgumentDraft::Text(hex::encode(output.output_package_sha256)),
        ),
        (
            "computed_values_sha256".into(),
            ArgumentDraft::Text(hex::encode(output.evaluated_values_sha256)),
        ),
        (
            "target_decimal_json".into(),
            ArgumentDraft::Text(serde_json::to_string(value).map_err(|_| Error::Compilation)?),
        ),
    ]))
}
pub(super) fn receipt(
    results: &PreparedStoredFormulaResults<'_, '_, '_, '_>,
    plan: &CompiledOperationPlan,
) -> Result<StoredFormulaCompilerReceipt, Error> {
    Ok(StoredFormulaCompilerReceipt {
        qualification: "actual_source_field_original_compiler_and_preserving_candidate_only_NOT_full_import_field_policy_signed_registry_issuer_ExecutionManifest_atomic_publication_native_SQL_or_Gate",
        output: results.receipt().clone(),
        compiled_plan_sha256: plan.canonical_sha256().map_err(|_| Error::Compilation)?,
        actual_meaning_graph_sha256: results
            .evaluation
            .meanings
            .graph()
            .canonical_sha256()
            .map_err(|_| Error::Compilation)?,
        head_generation: results
            .evaluation
            .meanings
            .ranges
            .source
            .source
            .head
            .generation(),
        changed_field_operations: plan.operations().len(),
    })
}
