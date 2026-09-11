#![allow(clippy::expect_used)] // Test fixtures use expectations to keep failures local and legible.

use domain_ir::{
    CHART_AUTOMATION_SCHEMA_VERSION, ChartAutomationBinding, ChartAutomationBuilder,
    ChartAutomationError, ChartAutomationLimitConfig, ChartAutomationLimits,
    ChartAutomationObservation, ChartAutomationObservationDraft, ChartAutomationProfile,
    ChartAutomationProfileDraft, ChartAutomationRequest, ChartAutomationRequestDraft,
    ChartAxisKind, ChartAxisScale, ChartAxisState, ChartDataOrientation, ChartDataProvenance,
    ChartDataState, ChartDimension, ChartDocumentState, ChartDocumentStateDraft, ChartFamily,
    ChartIdentity, ChartIdentityReservation, ChartLabelPosition, ChartLabelsState,
    ChartLegendPosition, ChartLegendState, ChartMarkerKind, ChartOperation, ChartSeriesAxis,
    ChartSeriesState, ChartStacking, ChartState, ChartStyleBinding, ChartTitlePosition,
    ChartTitleState, ChartTypeBinding, ChartTypeSelection, ChartValue, FormulaDecimal, LogicalId,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

fn limits() -> ChartAutomationLimits {
    ChartAutomationLimits::new(ChartAutomationLimitConfig::default()).expect("limits")
}

fn id(value: &str) -> LogicalId {
    LogicalId::parse(value).expect("logical id")
}

fn digest(character: char) -> String {
    character.to_string().repeat(64)
}

fn binding(capability: &str, index: usize) -> ChartAutomationBinding {
    ChartAutomationBinding {
        capability_id: capability.to_owned(),
        binding_id: id(&format!("binding-{index}")),
        parameter_schema_sha256: format!("{index:064x}"),
        readback_schema_sha256: format!("{:064x}", index + 20),
    }
}

fn profile_draft() -> ChartAutomationProfileDraft {
    ChartAutomationProfileDraft {
        schema_version: CHART_AUTOMATION_SCHEMA_VERSION.to_owned(),
        profile_id: id("hangul-2020-x86-ko-kr"),
        product: "Hancom Hangul".to_owned(),
        version: "11.0.0.9136".to_owned(),
        architecture: "x86".to_owned(),
        locale: "ko-KR".to_owned(),
        executable_sha256: digest('1'),
        catalog_sha256: digest('2'),
        readback_adapter_sha256: digest('3'),
        type_bindings: vec![
            ChartTypeBinding {
                binding_id: id("type-horizontal"),
                family: ChartFamily::HorizontalBar,
                dimension: ChartDimension::TwoDimensional,
                allowed_stacking: vec![
                    ChartStacking::None,
                    ChartStacking::Stacked,
                    ChartStacking::Percent,
                ],
                semantic_profile_sha256: digest('4'),
            },
            ChartTypeBinding {
                binding_id: id("type-vertical"),
                family: ChartFamily::VerticalBar,
                dimension: ChartDimension::TwoDimensional,
                allowed_stacking: vec![ChartStacking::None, ChartStacking::Stacked],
                semantic_profile_sha256: digest('5'),
            },
        ],
        style_bindings: vec![
            ChartStyleBinding {
                style_id: id("style-a"),
                binding_id: id("style-binding-a"),
                semantic_profile_sha256: digest('6'),
            },
            ChartStyleBinding {
                style_id: id("style-b"),
                binding_id: id("style-binding-b"),
                semantic_profile_sha256: digest('7'),
            },
        ],
        automation_bindings: [
            "obj.chart_axis",
            "obj.chart_data",
            "obj.chart_insert",
            "obj.chart_labels",
            "obj.chart_legend",
            "obj.chart_series",
            "obj.chart_style",
            "obj.chart_title",
            "obj.chart_type",
        ]
        .into_iter()
        .enumerate()
        .map(|(index, capability)| binding(capability, index + 1))
        .collect(),
    }
}

fn profile() -> ChartAutomationProfile {
    ChartAutomationProfile::from_draft(profile_draft(), limits()).expect("profile")
}

fn data(resource: &str) -> ChartDataState {
    ChartDataState {
        orientation: ChartDataOrientation::SeriesByColumns,
        row_labels: vec!["Q1".to_owned(), "Q2".to_owned()],
        column_labels: vec!["Sales".to_owned(), "Cost".to_owned()],
        values: vec![
            ChartValue::Number(FormulaDecimal::new(10, 0)),
            ChartValue::Number(FormulaDecimal::new(2, 0)),
            ChartValue::Blank,
            ChartValue::Number(FormulaDecimal::new(3, 0)),
        ],
        provenance: ChartDataProvenance::AutomationEditor {
            resource_id: id(resource),
        },
    }
}

fn series() -> Vec<ChartSeriesState> {
    ["Sales", "Cost"]
        .into_iter()
        .enumerate()
        .map(|(index, label)| ChartSeriesState {
            order: u32::try_from(index).expect("order"),
            label: label.to_owned(),
            hidden: false,
            excluded: false,
            axis: ChartSeriesAxis::Primary,
            stacked_with_previous: false,
            line_visible: true,
            marker: ChartMarkerKind::Automatic,
            style_sha256: format!("{:064x}", index + 40),
        })
        .collect()
}

fn axis(kind: ChartAxisKind) -> ChartAxisState {
    ChartAxisState {
        kind,
        visible: true,
        reverse_order: false,
        logarithmic: false,
        scale: ChartAxisScale::Automatic,
        title: None,
        number_format: String::new(),
        major_gridlines: kind != ChartAxisKind::CategoryX,
        minor_gridlines: false,
        style_sha256: digest('8'),
    }
}

fn chart(name: &str, native: u32) -> ChartState {
    let resource = format!("{name}-data");
    ChartState {
        identity: ChartIdentity {
            chart_id: id(name),
            native_object_id: native,
            native_instance_id: native + 100,
            data_resource_id: id(&resource),
            chart_part_id: id(&format!("{name}-part")),
        },
        chart_type: ChartTypeSelection {
            binding_id: id("type-horizontal"),
            family: ChartFamily::HorizontalBar,
            dimension: ChartDimension::TwoDimensional,
            stacking: ChartStacking::None,
        },
        data: data(&resource),
        series: series(),
        axes: vec![axis(ChartAxisKind::CategoryX), axis(ChartAxisKind::ValueY)],
        legend: ChartLegendState {
            visible: true,
            position: ChartLegendPosition::RightCenter,
            overlay: false,
            style_sha256: digest('9'),
        },
        labels: ChartLabelsState {
            visible: false,
            show_series_name: false,
            show_category_name: false,
            show_value: false,
            show_percentage: false,
            position: ChartLabelPosition::Automatic,
            number_format: String::new(),
            style_sha256: digest('a'),
        },
        title: ChartTitleState {
            visible: true,
            position: ChartTitlePosition::Above,
            text: Some("Quarterly".to_owned()),
            style_sha256: digest('b'),
        },
        style_id: id("style-a"),
        style_binding_id: id("style-binding-a"),
        geometry_sha256: digest('c'),
        composition_sha256: digest('d'),
        appearance_sha256: digest('e'),
        opaque_semantics_sha256: digest('f'),
        opaque_semantics_bytes: 128,
    }
}

fn state_with(charts: Vec<ChartState>) -> ChartDocumentState {
    ChartDocumentState::from_draft(
        ChartDocumentStateDraft {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION.to_owned(),
            target_profile_id: id("hangul-2020-x86-ko-kr"),
            external_object_inventory_sha256: digest('9'),
            charts,
        },
        &profile(),
        limits(),
    )
    .expect("state")
}

fn request(
    source: &ChartDocumentState,
    operation: ChartOperation,
) -> Result<ChartAutomationRequest, ChartAutomationError> {
    let profile = profile();
    ChartAutomationRequest::from_draft(
        ChartAutomationRequestDraft {
            schema_version: CHART_AUTOMATION_SCHEMA_VERSION.to_owned(),
            request_id: id("request"),
            expected_profile_sha256: profile.canonical_sha256(limits())?,
            expected_source_state_sha256: source.canonical_sha256(limits())?,
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        &profile,
        source,
        FLOW_A,
        limits(),
    )
}

fn execute(
    source: &ChartDocumentState,
    operation: ChartOperation,
) -> Result<ChartDocumentState, ChartAutomationError> {
    let profile = profile();
    let request = request(source, operation)?;
    let plan = ChartAutomationBuilder::plan(&profile, source, &request, FLOW_A, limits())?;
    ChartAutomationBuilder::build(&plan, &profile, source, FLOW_A, limits())
        .map(|result| result.state)
}

#[test]
fn profile_requires_exact_nine_capabilities_and_canonical_target_mappings() {
    let valid = profile();
    assert_eq!(
        valid.canonical_json(limits()).expect("json"),
        valid.canonical_json(limits()).expect("json")
    );

    let mut missing = profile_draft();
    missing.automation_bindings.pop();
    assert_eq!(
        ChartAutomationProfile::from_draft(missing, limits()),
        Err(ChartAutomationError::InvalidProfile)
    );
    let mut duplicate = profile_draft();
    duplicate.style_bindings[1].binding_id = duplicate.style_bindings[0].binding_id.clone();
    assert_eq!(
        ChartAutomationProfile::from_draft(duplicate, limits()),
        Err(ChartAutomationError::InvalidProfile)
    );
    let mut unordered = profile_draft();
    unordered.type_bindings.reverse();
    assert_eq!(
        ChartAutomationProfile::from_draft(unordered, limits()),
        Err(ChartAutomationError::InvalidProfile)
    );
}

#[test]
fn complete_grid_labels_series_axes_and_opaque_state_are_bound() {
    let profile = profile();
    let state = state_with(vec![chart("chart-a", 1)]);
    let roundtrip = ChartDocumentState::from_json(
        &state.canonical_json(limits()).expect("json"),
        &profile,
        limits(),
    )
    .expect("roundtrip");
    assert_eq!(roundtrip, state);

    let mut wrong_grid = chart("chart-a", 1);
    wrong_grid.data.values.pop();
    assert_eq!(
        ChartDocumentState::from_draft(
            ChartDocumentStateDraft {
                schema_version: CHART_AUTOMATION_SCHEMA_VERSION.to_owned(),
                target_profile_id: id("hangul-2020-x86-ko-kr"),
                external_object_inventory_sha256: digest('9'),
                charts: vec![wrong_grid],
            },
            &profile,
            limits(),
        ),
        Err(ChartAutomationError::InvalidData)
    );

    let mut linked_collision = chart("chart-a", 1);
    linked_collision.data.provenance = ChartDataProvenance::LinkedTable {
        table_id: id("chart-a"),
        table_state_sha256: digest('1'),
        range_sha256: digest('2'),
    };
    assert_eq!(
        ChartDocumentState::from_draft(
            ChartDocumentStateDraft {
                schema_version: CHART_AUTOMATION_SCHEMA_VERSION.to_owned(),
                target_profile_id: id("hangul-2020-x86-ko-kr"),
                external_object_inventory_sha256: digest('9'),
                charts: vec![linked_collision],
            },
            &profile,
            limits(),
        ),
        Err(ChartAutomationError::InvalidIdentity)
    );
}

#[test]
fn insertion_requires_exact_fresh_identity_and_allocator_inventory_transition() {
    let source = state_with(Vec::new());
    let inserted = chart("chart-a", 1);
    let reservation = ChartIdentityReservation {
        chart_id: inserted.identity.chart_id.clone(),
        native_object_id: inserted.identity.native_object_id,
        native_instance_id: inserted.identity.native_instance_id,
        data_resource_id: inserted.identity.data_resource_id.clone(),
        chart_part_id: inserted.identity.chart_part_id.clone(),
        before_external_object_inventory_sha256: digest('9'),
        after_external_object_inventory_sha256: digest('8'),
        allocator_proof_sha256: digest('7'),
    };
    let target = execute(
        &source,
        ChartOperation::Insert {
            chart: Box::new(inserted.clone()),
            reservation: reservation.clone(),
        },
    )
    .expect("insert");
    assert_eq!(target.charts(), &[inserted]);

    let mut stale = reservation;
    stale.before_external_object_inventory_sha256 = digest('0');
    assert_eq!(
        execute(
            &source,
            ChartOperation::Insert {
                chart: Box::new(chart("chart-a", 1)),
                reservation: stale,
            },
        ),
        Err(ChartAutomationError::InvalidReservation)
    );
}

#[test]
fn every_edit_capability_changes_only_its_complete_chart_component() {
    let source = state_with(vec![chart("chart-a", 1), chart("chart-z", 2)]);
    let stable_other = source.chart(&id("chart-z")).expect("other").clone();
    let mut replacement = data("chart-a-data");
    replacement.row_labels = vec!["2025".to_owned(), "2026".to_owned()];
    replacement.values[0] = ChartValue::Number(FormulaDecimal::new(99, 0));
    let mut replacement_series = series();
    replacement_series[1].marker = ChartMarkerKind::Diamond;
    let operations = vec![
        ChartOperation::SetType {
            chart_id: id("chart-a"),
            chart_type: ChartTypeSelection {
                binding_id: id("type-vertical"),
                family: ChartFamily::VerticalBar,
                dimension: ChartDimension::TwoDimensional,
                stacking: ChartStacking::Stacked,
            },
        },
        ChartOperation::ReplaceData {
            chart_id: id("chart-a"),
            data: replacement,
            series: replacement_series,
        },
        ChartOperation::UpdateSeries {
            chart_id: id("chart-a"),
            series: ChartSeriesState {
                hidden: true,
                ..series()[0].clone()
            },
        },
        ChartOperation::UpdateAxis {
            chart_id: id("chart-a"),
            axis: ChartAxisState {
                reverse_order: true,
                ..axis(ChartAxisKind::ValueY)
            },
        },
        ChartOperation::SetLegend {
            chart_id: id("chart-a"),
            legend: ChartLegendState {
                visible: false,
                position: ChartLegendPosition::Bottom,
                overlay: false,
                style_sha256: digest('1'),
            },
        },
        ChartOperation::SetLabels {
            chart_id: id("chart-a"),
            labels: ChartLabelsState {
                visible: true,
                show_series_name: false,
                show_category_name: true,
                show_value: true,
                show_percentage: false,
                position: ChartLabelPosition::OutsideEnd,
                number_format: "#,##0".to_owned(),
                style_sha256: digest('2'),
            },
        },
        ChartOperation::SetTitle {
            chart_id: id("chart-a"),
            title: ChartTitleState {
                visible: true,
                position: ChartTitlePosition::CenterOverlay,
                text: Some("Updated".to_owned()),
                style_sha256: digest('3'),
            },
        },
        ChartOperation::SetStyle {
            chart_id: id("chart-a"),
            style_id: id("style-b"),
            style_binding_id: id("style-binding-b"),
            appearance_sha256: digest('4'),
        },
    ];
    let expected = [
        "obj.chart_type",
        "obj.chart_data",
        "obj.chart_series",
        "obj.chart_axis",
        "obj.chart_legend",
        "obj.chart_labels",
        "obj.chart_title",
        "obj.chart_style",
    ];
    for (operation, capability) in operations.into_iter().zip(expected) {
        assert_eq!(operation.capability_id(), capability);
        let target = execute(&source, operation).expect("edit");
        assert_ne!(target.chart(&id("chart-a")), source.chart(&id("chart-a")));
        assert_eq!(target.chart(&id("chart-z")), Some(&stable_other));
    }
}

#[test]
fn invalid_series_axis_and_presentation_states_fail_closed() {
    let profile = profile();
    let build = |chart: ChartState| {
        ChartDocumentState::from_draft(
            ChartDocumentStateDraft {
                schema_version: CHART_AUTOMATION_SCHEMA_VERSION.to_owned(),
                target_profile_id: id("hangul-2020-x86-ko-kr"),
                external_object_inventory_sha256: digest('9'),
                charts: vec![chart],
            },
            &profile,
            limits(),
        )
    };
    let mut wrong_label = chart("chart-a", 1);
    wrong_label.series[0].label = "drift".to_owned();
    assert_eq!(build(wrong_label), Err(ChartAutomationError::InvalidSeries));

    let mut missing_secondary = chart("chart-a", 1);
    missing_secondary.series[0].axis = ChartSeriesAxis::Secondary;
    assert_eq!(
        build(missing_secondary),
        Err(ChartAutomationError::InvalidAxis)
    );

    let mut invalid_scale = chart("chart-a", 1);
    invalid_scale.axes[1].scale = ChartAxisScale::Manual {
        minimum: FormulaDecimal::new(10, 0),
        maximum: FormulaDecimal::new(1, 0),
        major_unit: FormulaDecimal::new(1, 0),
        minor_unit: FormulaDecimal::new(1, 0),
    };
    assert_eq!(build(invalid_scale), Err(ChartAutomationError::InvalidAxis));

    let mut hidden_labels = chart("chart-a", 1);
    hidden_labels.labels.show_value = true;
    assert_eq!(
        build(hidden_labels),
        Err(ChartAutomationError::InvalidPresentation)
    );
}

#[test]
fn strict_json_rejects_duplicate_unknown_and_bounded_input() {
    let profile = profile();
    let source = state_with(vec![chart("chart-a", 1)]);
    let request = request(
        &source,
        ChartOperation::SetTitle {
            chart_id: id("chart-a"),
            title: ChartTitleState {
                visible: false,
                position: ChartTitlePosition::Above,
                text: None,
                style_sha256: digest('b'),
            },
        },
    )
    .expect("request");
    let json = String::from_utf8(request.canonical_json(limits()).expect("json")).expect("utf8");
    let duplicate = json.replacen(
        "\"schema_version\":",
        "\"schema_version\":\"hwpx-agent.chart-automation/v1\",\"schema_version\":",
        1,
    );
    assert_eq!(
        ChartAutomationRequest::from_json(
            duplicate.as_bytes(),
            &profile,
            &source,
            FLOW_A,
            limits(),
        ),
        Err(ChartAutomationError::InvalidJson)
    );
    let unknown = json.replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        ChartAutomationRequest::from_json(unknown.as_bytes(), &profile, &source, FLOW_A, limits(),),
        Err(ChartAutomationError::InvalidJson)
    );
    let tiny = ChartAutomationLimits::new(ChartAutomationLimitConfig {
        input_bytes: 1,
        serialized_bytes: 2,
        ..ChartAutomationLimitConfig::default()
    })
    .expect("tiny limits");
    assert_eq!(
        ChartAutomationRequest::from_json(json.as_bytes(), &profile, &source, FLOW_A, tiny,),
        Err(ChartAutomationError::InputLimit)
    );
}

#[test]
fn request_plan_and_build_recheck_profile_state_flow_and_noop() {
    let profile = profile();
    let source = state_with(vec![chart("chart-a", 1)]);
    let operation = ChartOperation::SetTitle {
        chart_id: id("chart-a"),
        title: ChartTitleState {
            visible: false,
            position: ChartTitlePosition::Above,
            text: None,
            style_sha256: digest('b'),
        },
    };
    let request = request(&source, operation.clone()).expect("request");
    assert_eq!(
        ChartAutomationBuilder::plan(&profile, &source, &request, FLOW_B, limits()),
        Err(ChartAutomationError::DocumentFlowDrift)
    );
    let plan =
        ChartAutomationBuilder::plan(&profile, &source, &request, FLOW_A, limits()).expect("plan");
    let drifted = state_with(vec![chart("chart-a", 10)]);
    assert_eq!(
        ChartAutomationBuilder::build(&plan, &profile, &drifted, FLOW_A, limits()),
        Err(ChartAutomationError::SourceStateDrift)
    );
    assert_eq!(
        ChartAutomationBuilder::build(&plan, &profile, &source, FLOW_B, limits()),
        Err(ChartAutomationError::DocumentFlowDrift)
    );
    assert!(!plan.canonical_json(limits()).expect("plan json").is_empty());
    assert_eq!(plan.target_chart_id(), &id("chart-a"));
    assert_eq!(plan.binding_id(), &id("binding-8"));
    assert_eq!(plan.operation().capability_id(), "obj.chart_title");
    let result =
        ChartAutomationBuilder::build(&plan, &profile, &source, FLOW_A, limits()).expect("build");
    assert_eq!(result.receipt.capability_id(), "obj.chart_title");
    assert_eq!(result.receipt.target_document_flow_sha256(), FLOW_B);
    assert_eq!(
        result.receipt.target_state_sha256(),
        plan.target_state_sha256()
    );
    assert!(
        !result
            .receipt
            .canonical_json(limits())
            .expect("receipt json")
            .is_empty()
    );
    let target = result.state;
    assert_eq!(
        execute(&target, operation),
        Err(ChartAutomationError::NoChange)
    );
}

#[test]
fn execution_observation_requires_one_complete_exact_readback_and_nonempty_export() {
    let profile = profile();
    let source = state_with(vec![chart("chart-a", 1)]);
    let request = request(
        &source,
        ChartOperation::SetTitle {
            chart_id: id("chart-a"),
            title: ChartTitleState {
                visible: false,
                position: ChartTitlePosition::Above,
                text: None,
                style_sha256: digest('b'),
            },
        },
    )
    .expect("request");
    let plan =
        ChartAutomationBuilder::plan(&profile, &source, &request, FLOW_A, limits()).expect("plan");
    let complete = ChartAutomationObservationDraft {
        schema_version: CHART_AUTOMATION_SCHEMA_VERSION.to_owned(),
        plan_sha256: plan.plan_sha256().to_owned(),
        profile_sha256: profile.canonical_sha256(limits()).expect("profile digest"),
        capability_id: "obj.chart_title".to_owned(),
        binding_id: id("binding-8"),
        parameter_schema_sha256: format!("{:064x}", 8),
        readback_schema_sha256: format!("{:064x}", 28),
        source_state_sha256: source.canonical_sha256(limits()).expect("source digest"),
        target_state_sha256: plan.target_state_sha256().to_owned(),
        source_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        execution_attempts: 1,
        opened: true,
        saved: true,
        reopened: true,
        full_property_readback: true,
        reopened_state_sha256: plan.target_state_sha256().to_owned(),
        export_sha256: digest('6'),
        export_byte_length: 100,
    };
    let receipt = ChartAutomationObservation::from_draft(complete.clone(), &plan, limits())
        .expect("observation");
    assert!(!receipt.canonical_json(limits()).expect("json").is_empty());

    let mut partial = complete.clone();
    partial.reopened = false;
    assert_eq!(
        ChartAutomationObservation::from_draft(partial, &plan, limits()),
        Err(ChartAutomationError::IncompleteObservation)
    );
    let mut drifted = complete;
    drifted.reopened_state_sha256 = digest('0');
    assert_eq!(
        ChartAutomationObservation::from_draft(drifted, &plan, limits()),
        Err(ChartAutomationError::ObservationDrift)
    );
}

#[test]
fn debug_redacts_target_identity_content_and_digest_material() {
    let profile = profile();
    let source = state_with(vec![chart("secret-chart", 1)]);
    let request = request(
        &source,
        ChartOperation::SetTitle {
            chart_id: id("secret-chart"),
            title: ChartTitleState {
                visible: true,
                position: ChartTitlePosition::Above,
                text: Some("secret-title".to_owned()),
                style_sha256: digest('1'),
            },
        },
    )
    .expect("request");
    let plan =
        ChartAutomationBuilder::plan(&profile, &source, &request, FLOW_A, limits()).expect("plan");
    let debug = format!("{profile:?} {source:?} {request:?} {plan:?}");
    assert!(!debug.contains("secret-chart"));
    assert!(!debug.contains("secret-title"));
    assert!(!debug.contains(FLOW_A));
    assert!(!debug.contains(&digest('1')));
}
