#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use domain_ir::{
    FORM_CONTROL_SCHEMA_VERSION, FormButtonBackStyle, FormButtonValue, FormCharacterProperties,
    FormCommonProperties, FormControlAnchor, FormControlBuilder, FormControlError,
    FormControlIdentity, FormControlLimitConfig, FormControlLimits, FormControlOperation,
    FormControlPayload, FormControlRequest, FormControlRequestDraft, FormControlState,
    FormDateValidation, FormDocumentState, FormDocumentStateDraft, FormListItem, FormNativeBinding,
    FormScrollBars, FormSelectionValidation, FormTabAssignment, FormTabKeyBehavior,
    FormTextAlignment, FormTextValidation, LogicalId, NativeFormTag, OpaqueFormProperty,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";

fn limits() -> FormControlLimits {
    FormControlLimits::new(FormControlLimitConfig::default()).expect("limits")
}

fn identity(index: u32) -> FormControlIdentity {
    FormControlIdentity {
        logical_control_id: LogicalId::parse(format!("form-{index}")).expect("form id"),
        native_object_id: index + 1,
    }
}

fn common(index: u32) -> FormCommonProperties {
    FormCommonProperties {
        name: format!("private-control-{index}"),
        fore_color_rgb: 0x0011_2233,
        back_color_rgb: 0x00ee_ddcc,
        group_name: Some("private-group".to_owned()),
        tab_stop: true,
        tab_order: None,
        editable: true,
        enabled: true,
        border_type_id_ref: index,
        draw_frame: true,
        printable: true,
        command_sha256: Some(STATE_C.to_owned()),
        character: FormCharacterProperties {
            char_pr_id_ref: index,
            follow_context: false,
            auto_size: false,
            word_wrap: true,
        },
    }
}

fn text_payload(value: &str) -> FormControlPayload {
    FormControlPayload::Text {
        value: value.to_owned(),
        default_value: value.to_owned(),
        validation: FormTextValidation {
            required: !value.is_empty(),
            minimum_characters: u32::from(!value.is_empty()),
            maximum_characters: Some(64),
            external_validator_sha256: Some(FLOW_B.to_owned()),
        },
        multi_line: false,
        password_character: None,
        native_max_length: Some(64),
        scroll_bars: FormScrollBars::Horizontal,
        tab_key_behavior: FormTabKeyBehavior::NextObject,
        number_only: false,
        read_only: false,
        alignment: FormTextAlignment::Left,
    }
}

fn selection_items() -> Vec<FormListItem> {
    vec![
        FormListItem {
            display_text: "private-one".to_owned(),
            value: "one".to_owned(),
        },
        FormListItem {
            display_text: "private-two".to_owned(),
            value: "two".to_owned(),
        },
    ]
}

fn payloads() -> Vec<FormControlPayload> {
    vec![
        text_payload("private-value"),
        FormControlPayload::Checkbox {
            caption: "private-checkbox".to_owned(),
            value: FormButtonValue::Checked,
            default_value: FormButtonValue::Unchecked,
            must_be_checked: true,
            radio_group_name: None,
            tri_state: false,
            back_style: FormButtonBackStyle::Transparent,
        },
        FormControlPayload::Radio {
            caption: "private-radio".to_owned(),
            value: FormButtonValue::Checked,
            default_value: FormButtonValue::Unchecked,
            radio_group_name: "private-radio-group".to_owned(),
            group_required: true,
            tri_state: false,
            back_style: FormButtonBackStyle::Opaque,
        },
        FormControlPayload::Combo {
            items: selection_items(),
            selected_value: Some("one".to_owned()),
            default_selected_value: Some("two".to_owned()),
            validation: FormSelectionValidation {
                required: true,
                external_validator_sha256: Some(FLOW_A.to_owned()),
            },
            list_box_rows: Some(4),
            list_box_width_hwp_units: Some(7200),
            edit_enable: false,
        },
        FormControlPayload::List {
            items: selection_items(),
            selected_value: Some("two".to_owned()),
            default_selected_value: Some("one".to_owned()),
            validation: FormSelectionValidation {
                required: true,
                external_validator_sha256: None,
            },
            item_height_hwp_units: Some(1000),
            top_index: 0,
        },
        FormControlPayload::Date {
            value: Some("2024-02-29".to_owned()),
            default_value: Some("2024-01-01".to_owned()),
            format: "yyyy-MM-dd".to_owned(),
            locale: "ko-KR".to_owned(),
            validation: FormDateValidation {
                required: true,
                earliest: Some("2024-01-01".to_owned()),
                latest: Some("2024-12-31".to_owned()),
                external_validator_sha256: None,
            },
        },
    ]
}

fn binding(payload: &FormControlPayload) -> FormNativeBinding {
    match payload {
        FormControlPayload::Text { .. } => FormNativeBinding::Exact {
            tag: NativeFormTag::Edit,
        },
        FormControlPayload::Checkbox { .. } => FormNativeBinding::Exact {
            tag: NativeFormTag::CheckBtn,
        },
        FormControlPayload::Radio { .. } => FormNativeBinding::Exact {
            tag: NativeFormTag::RadioBtn,
        },
        FormControlPayload::Combo { .. } => FormNativeBinding::Exact {
            tag: NativeFormTag::ComboBox,
        },
        FormControlPayload::List { .. } => FormNativeBinding::Exact {
            tag: NativeFormTag::ListBox,
        },
        FormControlPayload::Date { .. } => FormNativeBinding::UnverifiedDateControl,
    }
}

fn control(index: u32, payload: FormControlPayload) -> FormControlState {
    FormControlState {
        identity: identity(index),
        anchor: FormControlAnchor {
            paragraph_id: LogicalId::parse(format!("paragraph-{index}")).expect("paragraph id"),
            run_ordinal: index,
            inline_ordinal: index,
        },
        native_binding: binding(&payload),
        common: common(index),
        payload,
        shape_locked: false,
        shape_state_sha256: FLOW_A.to_owned(),
        opaque_native_payload_sha256: FLOW_B.to_owned(),
        opaque_properties: vec![OpaqueFormProperty {
            namespace: "hp".to_owned(),
            name: format!("opaque-{index}"),
            value_sha256: STATE_C.to_owned(),
        }],
    }
}

fn state(controls: Vec<FormControlState>) -> Result<FormDocumentState, FormControlError> {
    FormDocumentState::from_draft(
        FormDocumentStateDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.to_owned(),
            controls,
            non_form_content_sha256: FLOW_A.to_owned(),
            style_catalog_sha256: FLOW_B.to_owned(),
            border_catalog_sha256: STATE_C.to_owned(),
            resource_inventory_sha256: FLOW_A.to_owned(),
            reference_inventory_sha256: FLOW_B.to_owned(),
            document_protection_sha256: STATE_C.to_owned(),
            opaque_document_state_sha256: FLOW_A.to_owned(),
        },
        limits(),
    )
}

fn request(
    source: &FormDocumentState,
    operation: FormControlOperation,
) -> Result<FormControlRequest, FormControlError> {
    FormControlRequest::from_draft(
        FormControlRequestDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("request-private").expect("request id"),
            expected_source_state_sha256: source.canonical_sha256(limits()).expect("digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        limits(),
    )
}

fn build(source: &FormDocumentState, operation: FormControlOperation) -> FormDocumentState {
    let request = request(source, operation).expect("request");
    let plan = FormControlBuilder::plan(source, &request, FLOW_A, limits()).expect("plan");
    FormControlBuilder::build(&plan, source, FLOW_A, limits())
        .expect("result")
        .state
}

#[test]
fn inserts_six_controls_with_exact_capabilities_and_explicit_date_nonbinding() {
    let expected = [
        "ref.form_text",
        "ref.form_checkbox",
        "ref.form_radio",
        "ref.form_combo",
        "ref.form_list",
        "ref.form_date",
    ];
    let mut current = state(Vec::new()).expect("empty state");
    for (index, payload) in payloads().into_iter().enumerate() {
        let control = control(u32::try_from(index).expect("small index"), payload);
        let operation = FormControlOperation::Insert {
            insertion_index: index,
            control,
        };
        assert_eq!(operation.capability_id(), expected[index]);
        current = build(&current, operation);
    }
    assert_eq!(current.controls().len(), 6);
    assert_eq!(
        current.controls()[5].native_binding,
        FormNativeBinding::UnverifiedDateControl
    );
}

#[test]
fn replaces_complete_properties_and_preserves_identity_shape_and_document_bindings() {
    let source = state(vec![control(1, text_payload("before"))]).expect("state");
    let before: serde_json::Value =
        serde_json::from_slice(&source.canonical_json(limits()).expect("json")).expect("value");
    let mut replacement_common = common(1);
    replacement_common.name = "private-renamed".to_owned();
    replacement_common.editable = false;
    let replacement_payload = text_payload("after");
    let target = build(
        &source,
        FormControlOperation::ReplaceProperties {
            target: identity(1),
            common: replacement_common,
            payload: replacement_payload,
        },
    );
    let after: serde_json::Value =
        serde_json::from_slice(&target.canonical_json(limits()).expect("json")).expect("value");
    assert_eq!(after["controls"][0]["common"]["name"], "private-renamed");
    assert_eq!(after["controls"][0]["common"]["editable"], false);
    for field in [
        "identity",
        "anchor",
        "native_binding",
        "shape_locked",
        "shape_state_sha256",
        "opaque_native_payload_sha256",
        "opaque_properties",
    ] {
        assert_eq!(before["controls"][0][field], after["controls"][0][field]);
    }
    for field in [
        "non_form_content_sha256",
        "style_catalog_sha256",
        "border_catalog_sha256",
        "resource_inventory_sha256",
        "reference_inventory_sha256",
        "document_protection_sha256",
        "opaque_document_state_sha256",
    ] {
        assert_eq!(before[field], after[field]);
    }
}

#[test]
fn protection_kind_change_and_noop_fail_without_partial_state() {
    let mut locked_control = control(1, text_payload("private"));
    locked_control.shape_locked = true;
    let locked = state(vec![locked_control]).expect("locked state");
    assert_eq!(
        request(
            &locked,
            FormControlOperation::ReplaceProperties {
                target: identity(1),
                common: common(1),
                payload: text_payload("changed"),
            },
        ),
        Err(FormControlError::Protected)
    );

    let source = state(vec![control(1, text_payload("private"))]).expect("state");
    assert_eq!(
        request(
            &source,
            FormControlOperation::ReplaceProperties {
                target: identity(1),
                common: common(1),
                payload: text_payload("private"),
            },
        ),
        Err(FormControlError::Noop)
    );
    assert_eq!(
        request(
            &source,
            FormControlOperation::ReplaceProperties {
                target: identity(1),
                common: common(1),
                payload: FormControlPayload::Checkbox {
                    caption: String::new(),
                    value: FormButtonValue::Unchecked,
                    default_value: FormButtonValue::Unchecked,
                    must_be_checked: false,
                    radio_group_name: None,
                    tri_state: false,
                    back_style: FormButtonBackStyle::Transparent,
                },
            },
        ),
        Err(FormControlError::InvalidNativeBinding)
    );
}

#[test]
fn complete_tab_order_is_atomic_contiguous_and_preserves_every_non_tab_property() {
    let source = state(vec![
        control(1, text_payload("one")),
        control(
            2,
            FormControlPayload::Checkbox {
                caption: "two".to_owned(),
                value: FormButtonValue::Unchecked,
                default_value: FormButtonValue::Unchecked,
                must_be_checked: false,
                radio_group_name: None,
                tri_state: false,
                back_style: FormButtonBackStyle::Transparent,
            },
        ),
        control(
            3,
            FormControlPayload::List {
                items: selection_items(),
                selected_value: Some("one".to_owned()),
                default_selected_value: None,
                validation: FormSelectionValidation {
                    required: true,
                    external_validator_sha256: None,
                },
                item_height_hwp_units: None,
                top_index: 0,
            },
        ),
    ])
    .expect("state");
    let before: serde_json::Value =
        serde_json::from_slice(&source.canonical_json(limits()).expect("json")).expect("value");
    let assignments = vec![
        FormTabAssignment {
            target: identity(1),
            tab_stop: true,
            tab_order: Some(1),
        },
        FormTabAssignment {
            target: identity(2),
            tab_stop: false,
            tab_order: None,
        },
        FormTabAssignment {
            target: identity(3),
            tab_stop: true,
            tab_order: Some(0),
        },
    ];
    let target = build(
        &source,
        FormControlOperation::SetTabOrder {
            assignments: assignments.clone(),
        },
    );
    let after: serde_json::Value =
        serde_json::from_slice(&target.canonical_json(limits()).expect("json")).expect("value");
    assert_eq!(after["controls"][0]["common"]["tab_order"], 1);
    assert_eq!(after["controls"][1]["common"]["tab_stop"], false);
    assert_eq!(after["controls"][2]["common"]["tab_order"], 0);
    for index in 0..3 {
        for field in [
            "identity",
            "anchor",
            "native_binding",
            "payload",
            "shape_state_sha256",
        ] {
            assert_eq!(
                before["controls"][index][field],
                after["controls"][index][field]
            );
        }
    }

    assert_eq!(
        request(
            &source,
            FormControlOperation::SetTabOrder {
                assignments: assignments[..2].to_vec(),
            },
        ),
        Err(FormControlError::InvalidTabOrder)
    );
    let mut non_contiguous = assignments;
    non_contiguous[0].tab_order = Some(2);
    assert_eq!(
        request(
            &source,
            FormControlOperation::SetTabOrder {
                assignments: non_contiguous,
            },
        ),
        Err(FormControlError::InvalidTabOrder)
    );
}

#[test]
fn input_selection_radio_and_date_boundaries_fail_closed() {
    let mut invalid_text = control(1, text_payload("12a"));
    if let FormControlPayload::Text { number_only, .. } = &mut invalid_text.payload {
        *number_only = true;
    }
    assert_eq!(
        state(vec![invalid_text]),
        Err(FormControlError::InvalidInput)
    );

    let mut invalid_selection = control(
        2,
        FormControlPayload::List {
            items: selection_items(),
            selected_value: Some("missing".to_owned()),
            default_selected_value: None,
            validation: FormSelectionValidation {
                required: true,
                external_validator_sha256: None,
            },
            item_height_hwp_units: None,
            top_index: 0,
        },
    );
    invalid_selection.native_binding = FormNativeBinding::Exact {
        tag: NativeFormTag::ListBox,
    };
    assert_eq!(
        state(vec![invalid_selection]),
        Err(FormControlError::InvalidSelection)
    );

    let mut radio_a = control(3, payloads().remove(2));
    radio_a.common.name = "radio-a".to_owned();
    let mut radio_b = radio_a.clone();
    radio_b.identity = identity(4);
    radio_b.anchor.paragraph_id = LogicalId::parse("paragraph-4").expect("id");
    radio_b.common.name = "radio-b".to_owned();
    assert_eq!(
        state(vec![radio_a, radio_b]),
        Err(FormControlError::InvalidRadioGroup)
    );

    let mut invalid_date = control(5, payloads().pop().expect("date"));
    if let FormControlPayload::Date { value, .. } = &mut invalid_date.payload {
        *value = Some("2023-02-29".to_owned());
    }
    assert_eq!(
        state(vec![invalid_date]),
        Err(FormControlError::InvalidInput)
    );
}

#[test]
fn identity_name_anchor_and_native_binding_collisions_are_rejected() {
    let first = control(1, text_payload("one"));
    let mut second = control(2, text_payload("two"));
    second.identity.native_object_id = first.identity.native_object_id;
    assert_eq!(
        state(vec![first.clone(), second]),
        Err(FormControlError::InvalidIdentity)
    );

    let mut wrong_binding = first.clone();
    wrong_binding.native_binding = FormNativeBinding::Exact {
        tag: NativeFormTag::ComboBox,
    };
    assert_eq!(
        state(vec![wrong_binding]),
        Err(FormControlError::InvalidNativeBinding)
    );

    let source = state(vec![first]).expect("state");
    let mut duplicate_name = control(3, text_payload("three"));
    duplicate_name.common.name = source.controls()[0].common.name.clone();
    assert_eq!(
        request(
            &source,
            FormControlOperation::Insert {
                insertion_index: 1,
                control: duplicate_name,
            },
        ),
        Err(FormControlError::InvalidIdentity)
    );
}

#[test]
fn request_plan_and_build_recheck_exact_state_and_document_flow() {
    let source = state(vec![control(1, text_payload("before"))]).expect("state");
    let operation = FormControlOperation::ReplaceProperties {
        target: identity(1),
        common: common(1),
        payload: text_payload("after"),
    };
    let stale_request = FormControlRequestDraft {
        schema_version: FORM_CONTROL_SCHEMA_VERSION.to_owned(),
        request_id: LogicalId::parse("request-stale").expect("id"),
        expected_source_state_sha256: FLOW_B.to_owned(),
        expected_document_flow_sha256: FLOW_A.to_owned(),
        target_document_flow_sha256: FLOW_B.to_owned(),
        operation: operation.clone(),
    };
    assert_eq!(
        FormControlRequest::from_draft(stale_request, &source, FLOW_A, limits()),
        Err(FormControlError::SourceStateDrift)
    );

    let valid = request(&source, operation).expect("request");
    assert_eq!(
        FormControlBuilder::plan(&source, &valid, FLOW_B, limits()),
        Err(FormControlError::DocumentFlowDrift)
    );
    let plan = FormControlBuilder::plan(&source, &valid, FLOW_A, limits()).expect("plan");
    assert_eq!(
        FormControlBuilder::build(&plan, &source, FLOW_B, limits()),
        Err(FormControlError::DocumentFlowDrift)
    );
    let changed = build(
        &source,
        FormControlOperation::ReplaceProperties {
            target: identity(1),
            common: {
                let mut value = common(1);
                value.enabled = false;
                value
            },
            payload: text_payload("before"),
        },
    );
    assert_eq!(
        FormControlBuilder::build(&plan, &changed, FLOW_A, limits()),
        Err(FormControlError::SourceStateDrift)
    );
}

#[test]
fn strict_json_limits_and_debug_redaction_are_enforced() {
    let source = state(vec![control(1, text_payload("private-secret"))]).expect("state");
    let valid = request(
        &source,
        FormControlOperation::ReplaceProperties {
            target: identity(1),
            common: {
                let mut value = common(1);
                value.name = "private-replacement".to_owned();
                value
            },
            payload: text_payload("private-secret-2"),
        },
    )
    .expect("request");
    let json = valid.canonical_json(limits()).expect("json");
    let parsed = FormControlRequest::from_json(&json, &source, FLOW_A, limits()).expect("parse");
    assert_eq!(parsed.operation().capability_id(), "ref.form_properties");

    let duplicate = String::from_utf8(json.clone())
        .expect("utf8")
        .replacen(
            "\"schema_version\":\"hwpx-agent.form-control/v1\",",
            "\"schema_version\":\"hwpx-agent.form-control/v1\",\"schema_version\":\"hwpx-agent.form-control/v1\",",
            1,
        );
    assert_eq!(
        FormControlRequest::from_json(duplicate.as_bytes(), &source, FLOW_A, limits()),
        Err(FormControlError::InvalidJson)
    );
    let unknown = String::from_utf8(json)
        .expect("utf8")
        .replacen('{', "{\"unknown\":true,", 1);
    assert_eq!(
        FormControlRequest::from_json(unknown.as_bytes(), &source, FLOW_A, limits()),
        Err(FormControlError::InvalidJson)
    );

    let small = FormControlLimits::new(FormControlLimitConfig {
        input_bytes: 1,
        output_bytes: 1,
        ..FormControlLimitConfig::default()
    })
    .expect("small limits");
    assert_eq!(
        FormControlRequest::from_json(b"{}", &source, FLOW_A, small),
        Err(FormControlError::InputLimit)
    );

    let debug = format!("{source:?} {valid:?} {:?}", source.controls()[0]);
    for secret in [
        "private-secret",
        "private-control-1",
        FLOW_A,
        FLOW_B,
        STATE_C,
        "paragraph-1",
        "form-1",
    ] {
        assert!(!debug.contains(secret), "debug leaked {secret}");
    }
    assert!(debug.contains("<redacted>"));
}
