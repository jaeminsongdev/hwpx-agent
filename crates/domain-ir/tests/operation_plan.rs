use std::collections::BTreeMap;
use std::error::Error;

use domain_ir::{
    ArgumentDraft, ArgumentKind, ArgumentSource, ArgumentSpec, CanonicalArgumentValue,
    CapabilityCatalog, CapabilityDefinitionDraft, CapabilityId, DefaultPolicy, DocumentGraph,
    DocumentGraphDraft, DocumentGraphLimits, DocumentId, FailurePolicy, Flow, Inline, LogicalId,
    Node, NodeCommon, NumericArgumentDraft, NumericUnit, OperationDraft, OperationId,
    OperationPlanCompiler, OperationPlanDraft, OperationPlanError, OperationPlanLimits,
    ParagraphNode, PlanId, Properties, RationalInput, RevisionId, Section, Selector, SelectorDraft,
    SelectorExpectation, SelectorLimits, SelectorSnapshot, UnsupportedSelectorKind,
};

type TestResult = Result<(), Box<dyn Error>>;

#[test]
fn compiles_units_defaults_and_stable_bytes_without_partial_state() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let catalog = layout_catalog()?;
    let mut arguments = BTreeMap::new();
    let _ = arguments.insert(
        "width".into(),
        numeric(RationalInput::integer(10), Some(NumericUnit::Millimeter)),
    );
    let draft = plan(vec![operation(
        "op-1",
        "layout.box",
        arguments,
        Vec::new(),
    )?])?;
    let compiler = compiler()?;
    let first = compiler.compile(draft.clone(), &catalog, &snapshot, &snapshot.expectation())?;
    let second = compiler.compile(draft, &catalog, &snapshot, &snapshot.expectation())?;
    assert_eq!(first.canonical_json()?, second.canonical_json()?);
    assert_eq!(first.canonical_sha256()?, second.canonical_sha256()?);
    assert_eq!(first.operations().len(), 1);

    let compiled_operation = &first.operations()[0];
    let width = compiled_operation
        .arguments()
        .get("width")
        .ok_or("missing width")?;
    assert_eq!(width.source(), ArgumentSource::Caller);
    assert!(matches!(
        width.value(),
        CanonicalArgumentValue::LengthMicrometers(value) if value.as_i64() == 10_000
    ));
    assert!(width.conversion_receipt().is_some());
    assert_ne!(width.value_sha256(), [0; 32]);

    let opacity = compiled_operation
        .arguments()
        .get("opacity")
        .ok_or("missing default opacity")?;
    assert_eq!(opacity.source(), ArgumentSource::CapabilityDefault);
    assert!(matches!(
        opacity.value(),
        CanonicalArgumentValue::RatioMillionths(value) if value.as_i64() == 500_000
    ));
    Ok(())
}

#[test]
fn canonical_compiled_plan_restore_revalidates_bytes_targets_and_receipts() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let mut arguments = BTreeMap::new();
    let _ = arguments.insert(
        "width".into(),
        numeric(RationalInput::integer(10), Some(NumericUnit::Millimeter)),
    );
    let compiled = compiler()?.compile(
        plan(vec![operation(
            "op-1",
            "layout.box",
            arguments,
            Vec::new(),
        )?])?,
        &layout_catalog()?,
        &snapshot,
        &snapshot.expectation(),
    )?;
    let bytes = compiled.canonical_json()?;
    let restored = domain_ir::CompiledOperationPlan::from_canonical_json(
        &bytes,
        OperationPlanLimits::default(),
    )?;
    assert_eq!(restored, compiled);
    assert_eq!(restored.canonical_json()?, bytes);

    let mut noncanonical = b" ".to_vec();
    noncanonical.extend_from_slice(&bytes);
    assert_error(
        domain_ir::CompiledOperationPlan::from_canonical_json(
            &noncanonical,
            OperationPlanLimits::default(),
        ),
        "operation_plan_invalid_serialized_plan",
    );
    let text = String::from_utf8(bytes.clone())?;
    for (from, to) in [
        (
            "\"failure_policy\":\"atomic\"",
            "\"failure_policy\":\"best_effort\"",
        ),
        (
            "\"expected_kind\":\"paragraph\"",
            "\"expected_kind\":\"drawing\"",
        ),
        (
            "\"value_type\":\"length_micrometers\"",
            "\"value_type\":\"point_milli\"",
        ),
        ("\"normalized_value\":10000", "\"normalized_value\":10001"),
    ] {
        let tampered = text.replacen(from, to, 1);
        assert_ne!(tampered, text);
        assert_error(
            domain_ir::CompiledOperationPlan::from_canonical_json(
                tampered.as_bytes(),
                OperationPlanLimits::default(),
            ),
            "operation_plan_invalid_serialized_plan",
        );
    }
    let too_small = OperationPlanLimits {
        max_serialized_bytes: bytes.len() - 1,
        ..OperationPlanLimits::default()
    };
    assert_error(
        domain_ir::CompiledOperationPlan::from_canonical_json(&bytes, too_small),
        "operation_plan_limit_exceeded",
    );
    Ok(())
}

#[test]
fn mixed_empty_and_unsupported_selectors_never_fall_back() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let catalog = empty_catalog("edit.noop")?;
    let compiler = compiler()?;
    let id_selector = Selector::by_logical_id(logical_id("p-1")?);

    let cases = [
        (
            SelectorDraft {
                variants: Vec::new(),
                unsupported: None,
            },
            "operation_plan_invalid_selector",
        ),
        (
            SelectorDraft {
                variants: vec![id_selector.clone(), id_selector.clone()],
                unsupported: None,
            },
            "operation_plan_invalid_selector",
        ),
        (
            SelectorDraft::unsupported(UnsupportedSelectorKind::BareTextOffset),
            "operation_plan_needs_resolution",
        ),
        (
            SelectorDraft {
                variants: vec![id_selector],
                unsupported: Some(UnsupportedSelectorKind::CursorSession),
            },
            "operation_plan_invalid_selector",
        ),
    ];
    for (selector, expected) in cases {
        let mut operation = operation("op-1", "edit.noop", BTreeMap::new(), Vec::new())?;
        operation.selector = selector;
        assert_error(
            compiler.compile(
                plan(vec![operation])?,
                &catalog,
                &snapshot,
                &snapshot.expectation(),
            ),
            expected,
        );
    }
    Ok(())
}

#[test]
fn base_revision_and_snapshot_digest_must_both_be_current() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let catalog = empty_catalog("edit.noop")?;
    let compiler = compiler()?;
    let operation = operation("op-1", "edit.noop", BTreeMap::new(), Vec::new())?;

    let mut wrong_base = plan(vec![operation.clone()])?;
    wrong_base.base_revision = revision("rev-2")?;
    assert_error(
        compiler.compile(wrong_base, &catalog, &snapshot, &snapshot.expectation()),
        "operation_plan_stale_selector",
    );

    let wrong_digest = SelectorExpectation::new(revision("rev-1")?, [0; 32]);
    assert_error(
        compiler.compile(plan(vec![operation])?, &catalog, &snapshot, &wrong_digest),
        "operation_plan_stale_selector",
    );
    Ok(())
}

#[test]
fn dependency_order_is_deterministic_and_edges_are_canonical() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let catalog = empty_catalog("edit.noop")?;
    let compiler = compiler()?;
    let operations = vec![
        operation(
            "op-c",
            "edit.noop",
            BTreeMap::new(),
            vec![operation_id("op-b")?, operation_id("op-a")?],
        )?,
        operation("op-b", "edit.noop", BTreeMap::new(), Vec::new())?,
        operation("op-a", "edit.noop", BTreeMap::new(), Vec::new())?,
    ];
    let plan_result = compiler.compile(
        plan(operations)?,
        &catalog,
        &snapshot,
        &snapshot.expectation(),
    )?;
    let ids: Vec<_> = plan_result
        .operations()
        .iter()
        .map(|operation| operation.operation_id().as_str())
        .collect();
    assert_eq!(ids, ["op-a", "op-b", "op-c"]);
    let dependencies: Vec<_> = plan_result.operations()[2]
        .depends_on()
        .iter()
        .map(OperationId::as_str)
        .collect();
    assert_eq!(dependencies, ["op-a", "op-b"]);
    Ok(())
}

#[test]
fn missing_self_duplicate_dependencies_and_cycles_are_distinct_failures() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let catalog = empty_catalog("edit.noop")?;
    let compiler = compiler()?;

    for dependencies in [
        vec![operation_id("missing")?],
        vec![operation_id("op-1")?],
        vec![operation_id("op-2")?, operation_id("op-2")?],
    ] {
        let operations = vec![
            operation("op-1", "edit.noop", BTreeMap::new(), dependencies)?,
            operation("op-2", "edit.noop", BTreeMap::new(), Vec::new())?,
        ];
        assert_error(
            compiler.compile(
                plan(operations)?,
                &catalog,
                &snapshot,
                &snapshot.expectation(),
            ),
            "operation_plan_invalid_dependency",
        );
    }

    let cycle = vec![
        operation(
            "op-1",
            "edit.noop",
            BTreeMap::new(),
            vec![operation_id("op-2")?],
        )?,
        operation(
            "op-2",
            "edit.noop",
            BTreeMap::new(),
            vec![operation_id("op-1")?],
        )?,
    ];
    assert_error(
        compiler.compile(plan(cycle)?, &catalog, &snapshot, &snapshot.expectation()),
        "operation_plan_cycle",
    );
    Ok(())
}

#[test]
fn units_must_be_explicit_compatible_bounded_and_checked() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let catalog = length_catalog()?;
    let compiler = compiler()?;
    let cases = [
        (
            numeric(RationalInput::integer(10), None),
            "operation_plan_needs_resolution",
        ),
        (
            numeric(RationalInput::integer(10), Some(NumericUnit::Percent)),
            "operation_plan_invalid_argument",
        ),
        (
            numeric(
                RationalInput::integer(10),
                Some(NumericUnit::Pixel { dpi: 0 }),
            ),
            "operation_plan_unit_conversion",
        ),
        (
            numeric(RationalInput::new(1, 2)?, Some(NumericUnit::HwpUnit)),
            "operation_plan_invalid_argument",
        ),
    ];
    for (argument, expected) in cases {
        let mut arguments = BTreeMap::new();
        let _ = arguments.insert("length".into(), argument);
        assert_error(
            compiler.compile(
                plan(vec![operation(
                    "op-1",
                    "layout.length",
                    arguments,
                    Vec::new(),
                )?])?,
                &catalog,
                &snapshot,
                &snapshot.expectation(),
            ),
            expected,
        );
    }
    Ok(())
}

#[test]
fn required_defaults_locked_conflicts_and_unknown_arguments_need_resolution() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let compiler = compiler()?;
    let catalog = locked_catalog()?;

    let mut locked_conflict = BTreeMap::new();
    let _ = locked_conflict.insert("locked".into(), ArgumentDraft::Integer(8));
    assert_error(
        compiler.compile(
            plan(vec![operation(
                "op-1",
                "edit.locked",
                locked_conflict,
                Vec::new(),
            )?])?,
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        ),
        "operation_plan_needs_resolution",
    );

    assert_error(
        compiler.compile(
            plan(vec![operation(
                "op-1",
                "edit.locked",
                BTreeMap::new(),
                Vec::new(),
            )?])?,
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        ),
        "operation_plan_needs_resolution",
    );

    let mut unknown = BTreeMap::new();
    let _ = unknown.insert("unknown".into(), ArgumentDraft::Boolean(true));
    assert_error(
        compiler.compile(
            plan(vec![operation("op-1", "edit.locked", unknown, Vec::new())?])?,
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        ),
        "operation_plan_invalid_argument",
    );
    Ok(())
}

#[test]
fn versions_duplicates_limits_and_capability_defaults_fail_preflight() -> TestResult {
    assert_error(
        OperationPlanCompiler::new(OperationPlanLimits {
            max_operations: 0,
            ..OperationPlanLimits::default()
        }),
        "operation_plan_invalid_limit",
    );
    let duplicate_definition = CapabilityDefinitionDraft::new(capability_id("dup")?);
    assert_error(
        CapabilityCatalog::from_drafts(vec![duplicate_definition.clone(), duplicate_definition]),
        "operation_plan_duplicate_capability",
    );

    let mut bad_default = CapabilityDefinitionDraft::new(capability_id("bad")?);
    let _ = bad_default.arguments.insert(
        "length".into(),
        ArgumentSpec {
            kind: ArgumentKind::Length,
            required: false,
            default: Some(numeric(RationalInput::integer(1), None)),
            default_policy: DefaultPolicy::Fallback,
        },
    );
    assert_error(
        CapabilityCatalog::from_drafts(vec![bad_default]),
        "operation_plan_invalid_capability_definition",
    );

    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "rev-1")?;
    let catalog = empty_catalog("edit.noop")?;
    let compiler = compiler()?;
    let operation = operation("op-1", "edit.noop", BTreeMap::new(), Vec::new())?;

    let mut wrong_version = plan(vec![operation.clone()])?;
    wrong_version.schema_version = "hwpx-agent.operation-plan/v3".into();
    assert_error(
        compiler.compile(wrong_version, &catalog, &snapshot, &snapshot.expectation()),
        "operation_plan_unsupported_version",
    );
    let mut best_effort = plan(vec![operation.clone()])?;
    best_effort.failure_policy = Some(FailurePolicy::BestEffort);
    assert_error(
        compiler.compile(best_effort, &catalog, &snapshot, &snapshot.expectation()),
        "operation_plan_needs_resolution",
    );
    assert_error(
        compiler.compile(
            plan(Vec::new())?,
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        ),
        "operation_plan_missing_operation",
    );
    assert_error(
        compiler.compile(
            plan(vec![operation.clone(), operation])?,
            &catalog,
            &snapshot,
            &snapshot.expectation(),
        ),
        "operation_plan_duplicate_operation",
    );
    Ok(())
}

#[test]
fn fixed_seed_thousand_operation_dag_is_order_independent_and_private() -> TestResult {
    let graph = fixture_graph()?;
    let snapshot = fixture_snapshot(&graph, "private-revision")?;
    let catalog = empty_catalog("edit.noop")?;
    let compiler = compiler()?;
    let mut operations = Vec::new();
    for index in 0..1_000_usize {
        let dependencies = if index == 0 {
            Vec::new()
        } else {
            vec![operation_id(&format!("op-{:04}", (index - 1) / 2))?]
        };
        operations.push(operation(
            &format!("op-{index:04}"),
            "edit.noop",
            BTreeMap::new(),
            dependencies,
        )?);
    }
    fixed_seed_shuffle(&mut operations);
    let mut first_draft = plan(operations.clone())?;
    first_draft.base_revision = revision("private-revision")?;
    let first = compiler.compile(first_draft, &catalog, &snapshot, &snapshot.expectation())?;
    operations.reverse();
    let mut second_draft = plan(operations)?;
    second_draft.base_revision = revision("private-revision")?;
    let second = compiler.compile(second_draft, &catalog, &snapshot, &snapshot.expectation())?;
    assert_eq!(first.canonical_json()?, second.canonical_json()?);
    assert_eq!(first.operations().len(), 1_000);

    let secret = "private-revision";
    for rendered in [
        format!("{first:?}"),
        format!("{:?}", first.operations()[0]),
        format!("{:?}", snapshot.expectation()),
    ] {
        assert!(!rendered.contains(secret));
        assert!(!rendered.contains("op-0000"));
    }
    Ok(())
}

fn compiler() -> Result<OperationPlanCompiler, OperationPlanError> {
    OperationPlanCompiler::new(OperationPlanLimits::default())
}

fn assert_error<T>(result: Result<T, OperationPlanError>, expected: &str) {
    assert_eq!(result.err().map(OperationPlanError::code), Some(expected));
}

fn plan(operations: Vec<OperationDraft>) -> Result<OperationPlanDraft, Box<dyn Error>> {
    Ok(OperationPlanDraft::new(
        PlanId::parse("plan-1")?,
        revision("rev-1")?,
        operations,
    ))
}

fn operation(
    operation: &str,
    capability: &str,
    arguments: BTreeMap<String, ArgumentDraft>,
    depends_on: Vec<OperationId>,
) -> Result<OperationDraft, Box<dyn Error>> {
    Ok(OperationDraft {
        operation_id: operation_id(operation)?,
        capability_id: capability_id(capability)?,
        selector: SelectorDraft::one(Selector::by_logical_id(logical_id("p-1")?)),
        arguments,
        depends_on,
    })
}

fn layout_catalog() -> Result<CapabilityCatalog, Box<dyn Error>> {
    let mut definition = CapabilityDefinitionDraft::new(capability_id("layout.box")?);
    let _ = definition.arguments.insert(
        "width".into(),
        ArgumentSpec {
            kind: ArgumentKind::Length,
            required: true,
            default: None,
            default_policy: DefaultPolicy::Fallback,
        },
    );
    let _ = definition.arguments.insert(
        "opacity".into(),
        ArgumentSpec {
            kind: ArgumentKind::Ratio,
            required: false,
            default: Some(numeric(
                RationalInput::integer(50),
                Some(NumericUnit::Percent),
            )),
            default_policy: DefaultPolicy::Fallback,
        },
    );
    Ok(CapabilityCatalog::from_drafts(vec![definition])?)
}

fn length_catalog() -> Result<CapabilityCatalog, Box<dyn Error>> {
    let mut definition = CapabilityDefinitionDraft::new(capability_id("layout.length")?);
    let _ = definition.arguments.insert(
        "length".into(),
        ArgumentSpec {
            kind: ArgumentKind::Length,
            required: true,
            default: None,
            default_policy: DefaultPolicy::Fallback,
        },
    );
    Ok(CapabilityCatalog::from_drafts(vec![definition])?)
}

fn locked_catalog() -> Result<CapabilityCatalog, Box<dyn Error>> {
    let mut definition = CapabilityDefinitionDraft::new(capability_id("edit.locked")?);
    let _ = definition.arguments.insert(
        "locked".into(),
        ArgumentSpec {
            kind: ArgumentKind::Integer {
                minimum: 0,
                maximum: 10,
            },
            required: false,
            default: Some(ArgumentDraft::Integer(7)),
            default_policy: DefaultPolicy::Locked,
        },
    );
    let _ = definition.arguments.insert(
        "required".into(),
        ArgumentSpec {
            kind: ArgumentKind::Boolean,
            required: true,
            default: None,
            default_policy: DefaultPolicy::Fallback,
        },
    );
    Ok(CapabilityCatalog::from_drafts(vec![definition])?)
}

fn empty_catalog(capability: &str) -> Result<CapabilityCatalog, Box<dyn Error>> {
    Ok(CapabilityCatalog::from_drafts(vec![
        CapabilityDefinitionDraft::new(capability_id(capability)?),
    ])?)
}

fn numeric(value: RationalInput, unit: Option<NumericUnit>) -> ArgumentDraft {
    ArgumentDraft::Numeric(NumericArgumentDraft { value, unit })
}

fn fixture_graph() -> Result<DocumentGraph, Box<dyn Error>> {
    let draft = DocumentGraphDraft::new(
        DocumentId::parse("doc-plan")?,
        vec![Section {
            section_id: logical_id("section-1")?,
            properties: Properties::new(),
            master_pages: Vec::new(),
            headers_footers: Vec::new(),
            body: Flow {
                children: vec![Node::Paragraph(ParagraphNode {
                    common: NodeCommon::new(logical_id("p-1")?),
                    inlines: vec![Inline::Text {
                        text: "synthetic plan target".into(),
                    }],
                    paragraph_properties: Properties::new(),
                })],
            },
        }],
    );
    Ok(DocumentGraph::from_draft(
        draft,
        DocumentGraphLimits::default(),
    )?)
}

fn fixture_snapshot(
    graph: &DocumentGraph,
    revision_value: &str,
) -> Result<SelectorSnapshot, Box<dyn Error>> {
    Ok(SelectorSnapshot::build(
        graph,
        revision(revision_value)?,
        SelectorLimits::default(),
    )?)
}

fn fixed_seed_shuffle(values: &mut [OperationDraft]) {
    let mut state = 0x9e37_79b9_7f4a_7c15_u64;
    for index in (1..values.len()).rev() {
        state = state
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        let swap = usize::try_from(state % u64::try_from(index + 1).unwrap_or(1)).unwrap_or(0);
        values.swap(index, swap);
    }
}

fn logical_id(value: &str) -> Result<LogicalId, domain_ir::DocumentGraphError> {
    LogicalId::parse(value)
}

fn revision(value: &str) -> Result<RevisionId, domain_ir::IdentityError> {
    RevisionId::parse(value)
}

fn operation_id(value: &str) -> Result<OperationId, domain_ir::IdentityError> {
    OperationId::parse(value)
}

fn capability_id(value: &str) -> Result<CapabilityId, domain_ir::IdentityError> {
    CapabilityId::parse(value)
}
