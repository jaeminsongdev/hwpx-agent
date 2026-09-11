use std::error::Error;

use domain_ir::{
    MATH_AST_NORMALIZATION_VERSION, MATH_AST_SCHEMA_VERSION, MathAstDraft, MathAstLimits,
    MathExpression, MathNode, MathSourceSpan,
};
use equation_engine::{
    EQUATION_AUTOMATION_PROFILE_VERSION, EQUATION_AUTOMATION_RECEIPT_SCHEMA_VERSION,
    EQUATION_AUTOMATION_SCHEMA_VERSION, EqEditLimits, EquationAutomationError,
    EquationAutomationLimitConfig, EquationAutomationLimits, EquationAutomationOperationDraft,
    EquationAutomationPlanner, EquationAutomationReceiptDraft, EquationAutomationReceiptState,
    EquationAutomationSelection, EquationAutomationSourceState, EquationAutomationTarget,
};

type TestResult = Result<(), Box<dyn Error>>;

const GRAPH: &str = "1111111111111111111111111111111111111111111111111111111111111111";
const FLOW: &str = "2222222222222222222222222222222222222222222222222222222222222222";
const ANCHOR: &str = "3333333333333333333333333333333333333333333333333333333333333333";
const BINDING: &str = "4444444444444444444444444444444444444444444444444444444444444444";
const OLD_SEMANTIC: &str = "5555555555555555555555555555555555555555555555555555555555555555";
const OUTPUT_GRAPH: &str = "6666666666666666666666666666666666666666666666666666666666666666";
const OUTPUT_FLOW: &str = "7777777777777777777777777777777777777777777777777777777777777777";

fn planner() -> EquationAutomationPlanner {
    EquationAutomationPlanner::new(
        EquationAutomationLimits::default(),
        MathAstLimits::default(),
        EqEditLimits::default(),
    )
}

fn ast(value: &str) -> MathAstDraft {
    let length = value
        .bytes()
        .fold(0_u32, |length, _| length.saturating_add(1));
    MathAstDraft {
        schema_version: MATH_AST_SCHEMA_VERSION.to_owned(),
        normalization_version: MATH_AST_NORMALIZATION_VERSION.to_owned(),
        source_length_bytes: length,
        root: MathNode {
            span: MathSourceSpan {
                start_byte: 0,
                end_byte: length,
            },
            style: None,
            expression: MathExpression::Identifier {
                name: value.to_owned(),
            },
        },
    }
}

fn source(selection: bool) -> EquationAutomationSourceState {
    EquationAutomationSourceState {
        revision: "revision-7".to_owned(),
        package_graph_sha256: GRAPH.to_owned(),
        document_flow_sha256: FLOW.to_owned(),
        anchor_fingerprint_sha256: ANCHOR.to_owned(),
        selected_equation: selection.then(|| EquationAutomationSelection {
            object_id: 91,
            semantic_sha256: OLD_SEMANTIC.to_owned(),
        }),
    }
}

fn target(
    source: EquationAutomationSourceState,
    operation: EquationAutomationOperationDraft,
) -> EquationAutomationTarget {
    EquationAutomationTarget {
        schema_version: EQUATION_AUTOMATION_SCHEMA_VERSION.to_owned(),
        profile_version: EQUATION_AUTOMATION_PROFILE_VERSION.to_owned(),
        binding_set_sha256: BINDING.to_owned(),
        source,
        operation,
    }
}

fn success_receipt(
    plan: &equation_engine::EquationAutomationPlan,
    object_id: u32,
    graph: &str,
    flow: &str,
) -> EquationAutomationReceiptDraft {
    EquationAutomationReceiptDraft {
        schema_version: EQUATION_AUTOMATION_RECEIPT_SCHEMA_VERSION.to_owned(),
        plan_sha256: plan.plan_sha256().to_owned(),
        binding_set_sha256: plan.binding_set_sha256().to_owned(),
        source_state_sha256: plan.source_state_sha256().to_owned(),
        state: EquationAutomationReceiptState::Succeeded,
        output_object_id: object_id,
        output_semantic_sha256: plan.expected_output_semantic_sha256().to_owned(),
        output_package_graph_sha256: graph.to_owned(),
        output_document_flow_sha256: flow.to_owned(),
        native_object_count: 1,
    }
}

#[test]
fn insert_builds_typed_plan_and_requires_mutation_receipt() -> TestResult {
    let observed = source(false);
    let plan = planner().build(
        target(
            observed.clone(),
            EquationAutomationOperationDraft::InsertNative { math_ast: ast("x") },
        ),
        &observed,
    )?;
    assert_eq!(plan.capability_id(), "eq.insert_native");
    assert_eq!(plan.plan_sha256().len(), 64);
    let json = String::from_utf8(plan.canonical_json(EquationAutomationLimits::default())?)?;
    assert!(json.contains("\"kind\":\"insert_native\""));
    assert!(json.contains("\"script\":\"x\""));
    assert!(!json.to_ascii_lowercase().contains("haction"));
    assert!(!json.to_ascii_lowercase().contains("parameterset"));

    let receipt = success_receipt(&plan, 101, OUTPUT_GRAPH, OUTPUT_FLOW);
    planner().verify_receipt(&plan, &receipt)?;
    let unchanged = success_receipt(&plan, 101, GRAPH, FLOW);
    assert_eq!(
        planner().verify_receipt(&plan, &unchanged),
        Err(EquationAutomationError::MutationMismatch)
    );
    Ok(())
}

#[test]
fn edit_requires_exact_selected_object_and_semantic_state() -> TestResult {
    let observed = source(true);
    let plan = planner().build(
        target(
            observed.clone(),
            EquationAutomationOperationDraft::EditNative {
                object_id: 91,
                expected_semantic_sha256: OLD_SEMANTIC.to_owned(),
                math_ast: ast("y"),
            },
        ),
        &observed,
    )?;
    assert_eq!(plan.capability_id(), "eq.edit_native");
    planner().verify_receipt(
        &plan,
        &success_receipt(&plan, 91, OUTPUT_GRAPH, OUTPUT_FLOW),
    )?;

    for (object_id, semantic) in [(92, OLD_SEMANTIC), (91, GRAPH)] {
        let attempt = planner().build(
            target(
                observed.clone(),
                EquationAutomationOperationDraft::EditNative {
                    object_id,
                    expected_semantic_sha256: semantic.to_owned(),
                    math_ast: ast("y"),
                },
            ),
            &observed,
        );
        assert_eq!(attempt, Err(EquationAutomationError::SelectionMismatch));
    }
    Ok(())
}

#[test]
fn readback_requires_complete_nonmutating_state() -> TestResult {
    let observed = source(true);
    let plan = planner().build(
        target(
            observed.clone(),
            EquationAutomationOperationDraft::ReadbackNative {
                object_id: 91,
                expected_semantic_sha256: OLD_SEMANTIC.to_owned(),
            },
        ),
        &observed,
    )?;
    assert_eq!(plan.capability_id(), "eq.roundtrip_readback");
    planner().verify_receipt(&plan, &success_receipt(&plan, 91, GRAPH, FLOW))?;
    let changed = success_receipt(&plan, 91, OUTPUT_GRAPH, OUTPUT_FLOW);
    assert_eq!(
        planner().verify_receipt(&plan, &changed),
        Err(EquationAutomationError::MutationMismatch)
    );
    Ok(())
}

#[test]
fn request_and_build_both_reject_source_or_selection_drift() {
    let requested = source(false);
    let mut observed = requested.clone();
    observed.document_flow_sha256 = OUTPUT_FLOW.to_owned();
    let draft = target(
        requested,
        EquationAutomationOperationDraft::InsertNative { math_ast: ast("x") },
    );
    assert_eq!(
        planner().build(draft, &observed),
        Err(EquationAutomationError::SourceStateDrift)
    );

    let selected = source(true);
    let insert = target(
        selected.clone(),
        EquationAutomationOperationDraft::InsertNative { math_ast: ast("x") },
    );
    assert_eq!(
        planner().build(insert, &selected),
        Err(EquationAutomationError::SelectionMismatch)
    );
}

#[test]
fn malformed_duplicate_unknown_and_oversized_json_fail_closed() -> TestResult {
    let observed = source(false);
    for json in [
        Vec::new(),
        br#"{"schema_version":"a","schema_version":"b"}"#.to_vec(),
        br#"{"schema_version":"a","unknown":true}"#.to_vec(),
    ] {
        assert_eq!(
            planner().build_json(&json, &observed),
            Err(EquationAutomationError::InvalidJson)
        );
    }
    let limits = EquationAutomationLimits::new(EquationAutomationLimitConfig {
        request_bytes: 8,
        revision_bytes: 8,
        serialized_bytes: 8,
    })?;
    let strict =
        EquationAutomationPlanner::new(limits, MathAstLimits::default(), EqEditLimits::default());
    assert_eq!(
        strict.build_json(b"123456789", &observed),
        Err(EquationAutomationError::InvalidJson)
    );
    Ok(())
}

#[test]
fn invalid_limits_identities_and_ast_are_rejected() {
    assert_eq!(
        EquationAutomationLimits::new(EquationAutomationLimitConfig {
            request_bytes: 10,
            revision_bytes: 0,
            serialized_bytes: 9,
        }),
        Err(EquationAutomationError::InvalidLimit)
    );
    let mut invalid = source(false);
    invalid.package_graph_sha256 = "A".repeat(64);
    assert_eq!(
        planner().build(
            target(
                invalid.clone(),
                EquationAutomationOperationDraft::InsertNative { math_ast: ast("x") },
            ),
            &invalid,
        ),
        Err(EquationAutomationError::InvalidIdentity)
    );
    let observed = source(false);
    let mut invalid_ast = ast("x");
    invalid_ast.root.span.end_byte = 2;
    assert_eq!(
        planner().build(
            target(
                observed.clone(),
                EquationAutomationOperationDraft::InsertNative {
                    math_ast: invalid_ast,
                },
            ),
            &observed,
        ),
        Err(EquationAutomationError::MathAst)
    );
}

#[test]
fn receipt_tamper_failure_unknown_effect_and_wrong_object_fail() -> TestResult {
    let observed = source(true);
    let plan = planner().build(
        target(
            observed.clone(),
            EquationAutomationOperationDraft::ReadbackNative {
                object_id: 91,
                expected_semantic_sha256: OLD_SEMANTIC.to_owned(),
            },
        ),
        &observed,
    )?;
    let mut receipt = success_receipt(&plan, 91, GRAPH, FLOW);
    receipt.plan_sha256 = OUTPUT_GRAPH.to_owned();
    assert_eq!(
        planner().verify_receipt(&plan, &receipt),
        Err(EquationAutomationError::ReceiptMismatch)
    );
    for state in [
        EquationAutomationReceiptState::FailedBeforeEffect,
        EquationAutomationReceiptState::EffectUnknown,
    ] {
        let mut failed = success_receipt(&plan, 91, GRAPH, FLOW);
        failed.state = state;
        assert_eq!(
            planner().verify_receipt(&plan, &failed),
            Err(EquationAutomationError::EffectNotProven)
        );
    }
    let wrong_object = success_receipt(&plan, 92, GRAPH, FLOW);
    assert_eq!(
        planner().verify_receipt(&plan, &wrong_object),
        Err(EquationAutomationError::MutationMismatch)
    );
    Ok(())
}

#[test]
fn debug_redacts_source_binding_object_semantic_and_script() -> TestResult {
    let observed = source(true);
    let target = target(
        observed.clone(),
        EquationAutomationOperationDraft::EditNative {
            object_id: 91,
            expected_semantic_sha256: OLD_SEMANTIC.to_owned(),
            math_ast: ast("secretx"),
        },
    );
    let target_debug = format!("{target:?}");
    let plan = planner().build(target, &observed)?;
    let plan_debug = format!("{plan:?}");
    for debug in [&target_debug, &plan_debug] {
        for secret in [
            "revision-7",
            GRAPH,
            FLOW,
            ANCHOR,
            BINDING,
            OLD_SEMANTIC,
            "secretx",
        ] {
            assert!(!debug.contains(secret), "debug leaked {secret}: {debug}");
        }
        assert!(
            !debug.contains("object_id"),
            "debug leaked an object identifier field: {debug}"
        );
    }
    Ok(())
}
