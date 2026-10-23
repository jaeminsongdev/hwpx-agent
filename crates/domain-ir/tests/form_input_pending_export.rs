//! Compile the actual successor production source; frozen shared exports stay unchanged.
//! This is typed component evidence, not a native/HWPX/public-route substitute.
use domain_ir::*;
#[path = "../src/form_input.rs"]
mod form_input;
use form_input::*;
use std::error::Error;
type AnyError = Box<dyn Error>;
const HASH: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

#[test]
fn fresh_caller_access_revocation_rejects_an_earlier_valid_plan() -> Result<(), AnyError> {
    let source = fixture()?;
    let plan = plan(&source, operation()?)?;
    let mut revoked = access();
    revoked.input_allowed = false;
    assert_eq!(
        FormInputBuilder::build(&plan, &source, FLOW, &revoked, limits()?),
        Err(FormInputError::Access)
    );
    let mut changed = access();
    changed.document_protection_sha256 = FLOW.into();
    assert_eq!(
        FormInputBuilder::build(&plan, &source, FLOW, &changed, limits()?),
        Err(FormInputError::Access)
    );
    Ok(())
}

#[test]
fn complete_private_plan_output_limit_returns_no_partial_result() -> Result<(), AnyError> {
    let source = fixture()?;
    let d = draft(&source, operation()?)?;
    let request_bytes = serde_json::to_vec(&d)?.len();
    let source_bytes = source.canonical_json(limits()?)?.len();
    let small = FormControlLimits::new(FormControlLimitConfig {
        input_bytes: request_bytes + 32,
        output_bytes: source_bytes + request_bytes + 128,
        ..FormControlLimitConfig::default()
    })?;
    let request = FormInputRequest::from_draft(d, &source, FLOW, small)?;
    assert_eq!(
        FormInputBuilder::plan(&source, &request, FLOW, small),
        Err(FormInputError::Limit)
    );
    Ok(())
}

fn limits() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
}
fn access() -> FormInputAccessPolicy {
    FormInputAccessPolicy {
        document_protection_sha256: HASH.into(),
        input_allowed: true,
    }
}
fn identity(i: u32) -> Result<FormControlIdentity, AnyError> {
    Ok(FormControlIdentity {
        logical_control_id: LogicalId::parse(format!("input-{i}"))?,
        native_object_id: i + 1,
    })
}
fn items() -> Vec<FormListItem> {
    vec![
        FormListItem {
            display_text: "첫째".into(),
            value: "one".into(),
        },
        FormListItem {
            display_text: "둘째".into(),
            value: "two".into(),
        },
    ]
}
fn text() -> FormControlPayload {
    FormControlPayload::Text {
        value: "before".into(),
        default_value: "기본값".into(),
        validation: FormTextValidation {
            required: true,
            minimum_characters: 1,
            maximum_characters: Some(32),
            external_validator_sha256: None,
        },
        multi_line: true,
        password_character: None,
        native_max_length: Some(32),
        scroll_bars: FormScrollBars::Both,
        tab_key_behavior: FormTabKeyBehavior::InsertTab,
        number_only: false,
        read_only: false,
        alignment: FormTextAlignment::Left,
    }
}
fn button(radio: bool, checked: bool) -> FormControlPayload {
    if radio {
        FormControlPayload::Radio {
            caption: "라디오".into(),
            value: if checked {
                FormButtonValue::Checked
            } else {
                FormButtonValue::Unchecked
            },
            default_value: if checked {
                FormButtonValue::Unchecked
            } else {
                FormButtonValue::Checked
            },
            radio_group_name: "cross-section".into(),
            group_required: true,
            tri_state: false,
            back_style: FormButtonBackStyle::Opaque,
        }
    } else {
        FormControlPayload::Checkbox {
            caption: "확인".into(),
            value: FormButtonValue::Unchecked,
            default_value: FormButtonValue::Checked,
            must_be_checked: false,
            radio_group_name: None,
            tri_state: true,
            back_style: FormButtonBackStyle::Transparent,
        }
    }
}
fn selection(list: bool) -> FormControlPayload {
    let validation = FormSelectionValidation {
        required: true,
        external_validator_sha256: None,
    };
    if list {
        FormControlPayload::List {
            items: items(),
            selected_value: Some("one".into()),
            default_selected_value: Some("two".into()),
            validation,
            item_height_hwp_units: Some(1000),
            top_index: 0,
        }
    } else {
        FormControlPayload::Combo {
            items: items(),
            selected_value: Some("one".into()),
            default_selected_value: Some("two".into()),
            validation,
            list_box_rows: Some(4),
            list_box_width_hwp_units: Some(4000),
            edit_enable: false,
        }
    }
}
fn date() -> FormControlPayload {
    FormControlPayload::Date {
        value: Some("2024-02-29".into()),
        default_value: Some("2024-01-01".into()),
        format: "yyyy-MM-dd".into(),
        locale: "ko-KR".into(),
        validation: FormDateValidation {
            required: true,
            earliest: Some("2024-01-01".into()),
            latest: Some("2024-12-31".into()),
            external_validator_sha256: None,
        },
    }
}
fn fixture() -> Result<FormDocumentState, AnyError> {
    let payloads = vec![
        text(),
        button(false, false),
        button(true, true),
        button(true, false),
        selection(false),
        selection(true),
        date(),
    ];
    let mut controls = Vec::new();
    for (i, payload) in payloads.into_iter().enumerate() {
        let i = u32::try_from(i)?;
        let native_binding = match &payload {
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
        };
        controls.push(FormControlState {
            identity: identity(i)?,
            anchor: FormControlAnchor {
                paragraph_id: LogicalId::parse(format!("section-p-{i}"))?,
                run_ordinal: i,
                inline_ordinal: 0,
            },
            native_binding,
            common: FormCommonProperties {
                name: format!("field-{i}"),
                fore_color_rgb: 0,
                back_color_rgb: 0x00ff_ffff,
                group_name: None,
                tab_stop: true,
                tab_order: Some(i),
                editable: true,
                enabled: true,
                border_type_id_ref: 0,
                draw_frame: true,
                printable: true,
                command_sha256: None,
                character: FormCharacterProperties {
                    char_pr_id_ref: 0,
                    follow_context: false,
                    auto_size: false,
                    word_wrap: true,
                },
            },
            payload,
            shape_locked: false,
            shape_state_sha256: HASH.into(),
            opaque_native_payload_sha256: HASH.into(),
            opaque_properties: vec![OpaqueFormProperty {
                namespace: "hp".into(),
                name: "binding".into(),
                value_sha256: HASH.into(),
            }],
        });
    }
    state(controls)
}
fn state(controls: Vec<FormControlState>) -> Result<FormDocumentState, AnyError> {
    Ok(FormDocumentState::from_draft(
        FormDocumentStateDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
            controls,
            non_form_content_sha256: HASH.into(),
            style_catalog_sha256: HASH.into(),
            border_catalog_sha256: HASH.into(),
            resource_inventory_sha256: HASH.into(),
            reference_inventory_sha256: HASH.into(),
            document_protection_sha256: HASH.into(),
            opaque_document_state_sha256: HASH.into(),
        },
        limits()?,
    )?)
}
fn draft(
    source: &FormDocumentState,
    operation: FormInputOperation,
) -> Result<FormInputRequestDraft, AnyError> {
    Ok(FormInputRequestDraft {
        schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
        request_id: LogicalId::parse("atomic-request")?,
        expected_source_state_sha256: source.canonical_sha256(limits()?)?,
        expected_document_flow_sha256: FLOW.into(),
        access: FormInputAccessPolicy {
            document_protection_sha256: HASH.into(),
            input_allowed: true,
        },
        operation,
    })
}
fn assign(i: u32, value: FormInputValue) -> Result<FormInputAssignment, AnyError> {
    Ok(FormInputAssignment {
        target: identity(i)?,
        value,
    })
}
fn operation() -> Result<FormInputOperation, AnyError> {
    Ok(FormInputOperation::SetValues {
        assignments: vec![
            assign(
                0,
                FormInputValue::Text {
                    value: "입력 & <\"'>\n다음".into(),
                },
            )?,
            assign(
                1,
                FormInputValue::Checkbox {
                    value: FormButtonValue::Indeterminate,
                },
            )?,
            assign(
                2,
                FormInputValue::Radio {
                    value: FormButtonValue::Unchecked,
                },
            )?,
            assign(
                3,
                FormInputValue::Radio {
                    value: FormButtonValue::Checked,
                },
            )?,
            assign(
                4,
                FormInputValue::Combo {
                    selected_value: Some("two".into()),
                },
            )?,
            assign(
                5,
                FormInputValue::List {
                    selected_value: Some("two".into()),
                },
            )?,
            assign(
                6,
                FormInputValue::Date {
                    value: Some("2024-12-31".into()),
                },
            )?,
        ],
    })
}
fn plan(
    source: &FormDocumentState,
    operation: FormInputOperation,
) -> Result<FormInputPlan, AnyError> {
    let request = FormInputRequest::from_draft(draft(source, operation)?, source, FLOW, limits()?)?;
    Ok(FormInputBuilder::plan(source, &request, FLOW, limits()?)?)
}
fn run(
    source: &FormDocumentState,
    operation: FormInputOperation,
) -> Result<FormInputResult, AnyError> {
    Ok(FormInputBuilder::build(
        &plan(source, operation)?,
        source,
        FLOW,
        &access(),
        limits()?,
    )?)
}
fn rejects(
    source: &FormDocumentState,
    operation: FormInputOperation,
    expected: FormInputError,
) -> Result<(), AnyError> {
    assert_eq!(
        FormInputRequest::from_draft(draft(source, operation)?, source, FLOW, limits()?),
        Err(expected)
    );
    Ok(())
}

#[test]
fn all_six_value_kinds_change_only_current_values_in_one_atomic_transition() -> Result<(), AnyError>
{
    let source = fixture()?;
    let result = run(&source, operation()?)?;
    assert_eq!(result.receipt.changed_controls, 7);
    let mut before: serde_json::Value = serde_json::from_slice(&source.canonical_json(limits()?)?)?;
    let mut after: serde_json::Value =
        serde_json::from_slice(&result.state.canonical_json(limits()?)?)?;
    for value in [&mut before, &mut after] {
        for c in value["controls"].as_array_mut().ok_or("controls missing")? {
            let p = c["payload"].as_object_mut().ok_or("payload missing")?;
            p.remove("value");
            p.remove("selected_value");
        }
    }
    assert_eq!(before, after);
    assert_eq!(result.receipt.qualification, FormInputQualification::CallerPolicyOnlyNativeProtectionExternalValidationAndOutputUnqualified);
    assert_eq!(
        result.state.controls()[6].native_binding,
        FormNativeBinding::UnverifiedDateControl
    );
    Ok(())
}

#[test]
fn complete_default_reset_preserves_policies_and_atomically_restores_radio_group()
-> Result<(), AnyError> {
    let source = fixture()?;
    let output = run(
        &source,
        FormInputOperation::ResetDefaults {
            targets: (0..7).map(identity).collect::<Result<_, _>>()?,
        },
    )?;
    assert_eq!(output.receipt.changed_controls, 7);
    assert!(
        matches!(&output.state.controls()[0].payload,FormControlPayload::Text { value,.. } if value == "기본값")
    );
    assert!(matches!(
        &output.state.controls()[2].payload,
        FormControlPayload::Radio {
            value: FormButtonValue::Unchecked,
            ..
        }
    ));
    assert!(matches!(
        &output.state.controls()[3].payload,
        FormControlPayload::Radio {
            value: FormButtonValue::Checked,
            ..
        }
    ));
    assert_eq!(
        output.state.controls()[0].common,
        source.controls()[0].common
    );
    Ok(())
}

#[test]
fn required_radio_switch_accepts_either_assignment_order_but_not_partial_group()
-> Result<(), AnyError> {
    let source = fixture()?;
    let a = assign(
        2,
        FormInputValue::Radio {
            value: FormButtonValue::Unchecked,
        },
    )?;
    let b = assign(
        3,
        FormInputValue::Radio {
            value: FormButtonValue::Checked,
        },
    )?;
    let one = run(
        &source,
        FormInputOperation::SetValues {
            assignments: vec![a.clone(), b.clone()],
        },
    )?;
    let two = run(
        &source,
        FormInputOperation::SetValues {
            assignments: vec![b.clone(), a.clone()],
        },
    )?;
    assert_eq!(one.state, two.state);
    rejects(
        &source,
        FormInputOperation::SetValues {
            assignments: vec![a],
        },
        FormInputError::Validation,
    )?;
    rejects(
        &source,
        FormInputOperation::SetValues {
            assignments: vec![b],
        },
        FormInputError::Validation,
    )?;
    rejects(
        &source,
        FormInputOperation::ResetDefaults {
            targets: vec![identity(3)?],
        },
        FormInputError::Validation,
    )?;
    Ok(())
}

#[test]
fn each_requested_target_enforces_shape_enabled_editable_and_text_read_only() -> Result<(), AnyError>
{
    let source = fixture()?;
    for mode in 0..4 {
        let mut controls = source.controls().to_vec();
        match mode {
            0 => controls[0].shape_locked = true,
            1 => controls[0].common.enabled = false,
            2 => controls[0].common.editable = false,
            _ => {
                if let FormControlPayload::Text { read_only, .. } = &mut controls[0].payload {
                    *read_only = true;
                }
            }
        }
        rejects(&state(controls)?, operation()?, FormInputError::Protected)?;
    }
    // A protected later target also aborts the earlier valid write, with source untouched.
    let mut controls = source.controls().to_vec();
    controls[5].shape_locked = true;
    let protected = state(controls)?;
    let hash = protected.canonical_sha256(limits()?)?;
    rejects(&protected, operation()?, FormInputError::Protected)?;
    assert_eq!(hash, protected.canonical_sha256(limits()?)?);
    Ok(())
}

#[test]
fn caller_access_and_exact_protection_digest_are_mandatory_not_native_proof() -> Result<(), AnyError>
{
    let source = fixture()?;
    for mode in 0..2 {
        let mut d = draft(&source, operation()?)?;
        if mode == 0 {
            d.access.input_allowed = false;
        } else {
            d.access.document_protection_sha256 = "0".repeat(64);
        }
        assert_eq!(
            FormInputRequest::from_draft(d, &source, FLOW, limits()?),
            Err(FormInputError::Access)
        );
    }
    Ok(())
}

#[test]
fn missing_duplicate_cross_kind_and_empty_targets_fail_without_partial_state()
-> Result<(), AnyError> {
    let source = fixture()?;
    rejects(
        &source,
        FormInputOperation::SetValues {
            assignments: vec![],
        },
        FormInputError::Target,
    )?;
    rejects(
        &source,
        FormInputOperation::ResetDefaults {
            targets: vec![identity(0)?, identity(0)?],
        },
        FormInputError::Target,
    )?;
    let a = assign(
        0,
        FormInputValue::Text {
            value: "new".into(),
        },
    )?;
    rejects(
        &source,
        FormInputOperation::SetValues {
            assignments: vec![a.clone(), a],
        },
        FormInputError::Target,
    )?;
    rejects(
        &source,
        FormInputOperation::ResetDefaults {
            targets: vec![identity(100)?],
        },
        FormInputError::Target,
    )?;
    rejects(
        &source,
        FormInputOperation::SetValues {
            assignments: vec![assign(
                1,
                FormInputValue::Text {
                    value: "wrong kind".into(),
                },
            )?],
        },
        FormInputError::Kind,
    )?;
    Ok(())
}

#[test]
fn text_numeric_multiline_length_and_required_rules_reuse_real_domain_validation()
-> Result<(), AnyError> {
    let source = fixture()?;
    for value in [String::new(), "x".repeat(33), "\0".into()] {
        rejects(
            &source,
            FormInputOperation::SetValues {
                assignments: vec![assign(0, FormInputValue::Text { value })?],
            },
            FormInputError::Validation,
        )?;
    }
    for numeric in [false, true] {
        let mut controls = source.controls().to_vec();
        if let FormControlPayload::Text {
            value,
            default_value,
            number_only,
            multi_line,
            scroll_bars,
            tab_key_behavior,
            ..
        } = &mut controls[0].payload
        {
            *number_only = numeric;
            *multi_line = false;
            *scroll_bars = FormScrollBars::None;
            *tab_key_behavior = FormTabKeyBehavior::NextObject;
            *value = "12".into();
            *default_value = "34".into();
        }
        rejects(
            &state(controls)?,
            FormInputOperation::SetValues {
                assignments: vec![assign(
                    0,
                    FormInputValue::Text {
                        value: if numeric {
                            "letters".into()
                        } else {
                            "two\nlines".into()
                        },
                    },
                )?],
            },
            FormInputError::Validation,
        )?;
    }
    Ok(())
}

#[test]
fn selection_membership_checkbox_required_and_date_range_fail_closed() -> Result<(), AnyError> {
    let source = fixture()?;
    for i in [4, 5] {
        for selected_value in [None, Some("not an item".into())] {
            let value = if i == 4 {
                FormInputValue::Combo { selected_value }
            } else {
                FormInputValue::List { selected_value }
            };
            rejects(
                &source,
                FormInputOperation::SetValues {
                    assignments: vec![assign(i, value)?],
                },
                FormInputError::Validation,
            )?;
        }
    }
    for value in [
        None,
        Some("2023-12-31".into()),
        Some("2024-02-30".into()),
        Some("2024-13-01".into()),
    ] {
        rejects(
            &source,
            FormInputOperation::SetValues {
                assignments: vec![assign(6, FormInputValue::Date { value })?],
            },
            FormInputError::Validation,
        )?;
    }
    let mut controls = source.controls().to_vec();
    if let FormControlPayload::Checkbox {
        must_be_checked,
        value,
        ..
    } = &mut controls[1].payload
    {
        *must_be_checked = true;
        *value = FormButtonValue::Checked;
    }
    rejects(
        &state(controls)?,
        FormInputOperation::SetValues {
            assignments: vec![assign(
                1,
                FormInputValue::Checkbox {
                    value: FormButtonValue::Unchecked,
                },
            )?],
        },
        FormInputError::Validation,
    )?;
    Ok(())
}

#[test]
fn external_validator_references_never_count_as_executed_validation() -> Result<(), AnyError> {
    let source = fixture()?;
    for i in [0, 4, 5, 6] {
        let mut controls = source.controls().to_vec();
        let external = match &mut controls[i].payload {
            FormControlPayload::Text { validation, .. } => {
                &mut validation.external_validator_sha256
            }
            FormControlPayload::Combo { validation, .. }
            | FormControlPayload::List { validation, .. } => {
                &mut validation.external_validator_sha256
            }
            FormControlPayload::Date { validation, .. } => {
                &mut validation.external_validator_sha256
            }
            _ => return Err("wrong fixture kind".into()),
        };
        *external = Some(HASH.into());
        rejects(
            &state(controls)?,
            operation()?,
            FormInputError::ExternalValidationUnqualified,
        )?;
    }
    Ok(())
}

#[test]
fn source_flow_and_protection_drift_invalidate_request_plan_and_build() -> Result<(), AnyError> {
    let source = fixture()?;
    let request =
        FormInputRequest::from_draft(draft(&source, operation()?)?, &source, FLOW, limits()?)?;
    assert_eq!(
        FormInputBuilder::plan(&source, &request, HASH, limits()?),
        Err(FormInputError::Drift)
    );
    let plan = FormInputBuilder::plan(&source, &request, FLOW, limits()?)?;
    assert_eq!(
        FormInputBuilder::build(&plan, &source, HASH, &access(), limits()?),
        Err(FormInputError::Drift)
    );
    let mut d: FormDocumentStateDraft = serde_json::from_slice(&source.canonical_json(limits()?)?)?;
    d.document_protection_sha256 = FLOW.into();
    let changed = FormDocumentState::from_draft(d, limits()?)?;
    assert_eq!(
        FormInputBuilder::build(&plan, &changed, FLOW, &access(), limits()?),
        Err(FormInputError::Drift)
    );
    assert_eq!(
        FormInputRequest::from_draft(draft(&source, operation()?)?, &changed, FLOW, limits()?),
        Err(FormInputError::Drift)
    );
    Ok(())
}

#[test]
fn strict_json_duplicate_nested_unknown_coercion_trailing_and_size_reject() -> Result<(), AnyError>
{
    let source = fixture()?;
    let d = draft(&source, operation()?)?;
    let raw = serde_json::to_vec(&d)?;
    let request = FormInputRequest::from_json(&raw, &source, FLOW, limits()?)?;
    assert_eq!(request.canonical_json(limits()?)?, raw);
    let text = String::from_utf8(raw.clone())?;
    for changed in [
        format!("{text}{{}}"),
        text.replacen(
            "\"input_allowed\":true",
            "\"input_allowed\":true,\"input_allowed\":false",
            1,
        ),
        text.replacen("\"input_allowed\":true", "\"input_allowed\":1", 1),
        text.replacen("\"kind\":\"text\"", "\"kind\":\"text\",\"unknown\":1", 1),
        text.replacen(
            "\"native_object_id\":1",
            "\"native_object_id\":1,\"native_object_id\":2",
            1,
        ),
    ] {
        assert_eq!(
            FormInputRequest::from_json(changed.as_bytes(), &source, FLOW, limits()?),
            Err(FormInputError::Json)
        );
    }
    let small = FormControlLimits::new(FormControlLimitConfig {
        input_bytes: 1,
        ..FormControlLimitConfig::default()
    })?;
    assert_eq!(
        FormInputRequest::from_json(&raw, &source, FLOW, small),
        Err(FormInputError::Limit)
    );
    assert_eq!(
        FormInputRequest::from_draft(d, &source, FLOW, small),
        Err(FormInputError::Limit)
    );
    Ok(())
}

#[test]
fn retry_is_byte_exact_and_value_and_reset_noops_reject() -> Result<(), AnyError> {
    let source = fixture()?;
    let one = plan(&source, operation()?)?;
    let two = plan(&source, operation()?)?;
    assert_eq!(one.plan_sha256(), two.plan_sha256());
    assert_eq!(
        one.canonical_json(limits()?)?,
        two.canonical_json(limits()?)?
    );
    let a = FormInputBuilder::build(&one, &source, FLOW, &access(), limits()?)?;
    let b = FormInputBuilder::build(&two, &source, FLOW, &access(), limits()?)?;
    assert_eq!(a, b);
    assert_eq!(one.source_state(), &source);
    assert_eq!(one.target_state(), &a.state);
    rejects(
        &source,
        FormInputOperation::SetValues {
            assignments: vec![assign(
                0,
                FormInputValue::Text {
                    value: "before".into(),
                },
            )?],
        },
        FormInputError::Noop,
    )?;
    let targets = (0..7).map(identity).collect::<Result<Vec<_>, _>>()?;
    let reset = run(
        &source,
        FormInputOperation::ResetDefaults {
            targets: targets.clone(),
        },
    )?;
    rejects(
        &reset.state,
        FormInputOperation::ResetDefaults { targets },
        FormInputError::Noop,
    )?;
    Ok(())
}

#[test]
fn debug_error_and_public_receipt_redact_document_values_and_private_paths() -> Result<(), AnyError>
{
    let source = fixture()?;
    let d = draft(&source, operation()?)?;
    let request = FormInputRequest::from_draft(d.clone(), &source, FLOW, limits()?)?;
    let plan = FormInputBuilder::plan(&source, &request, FLOW, limits()?)?;
    let result = FormInputBuilder::build(&plan, &source, FLOW, &access(), limits()?)?;
    let public = serde_json::to_string(&result.receipt)?;
    let debug = format!(
        "{d:?} {:?} {:?} {request:?} {plan:?} {result:?}",
        d.operation, d.access
    );
    for raw in [public.as_str(), debug.as_str()] {
        for value in [
            "before",
            "기본값",
            "cross-section",
            "라디오",
            "입력 &",
            "field-0",
            "C:\\",
            "D:\\",
        ] {
            assert!(!raw.contains(value));
        }
    }
    assert!(!debug.contains(HASH));
    assert!(!debug.contains(FLOW));
    Ok(())
}
