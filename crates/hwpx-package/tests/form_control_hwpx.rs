#![allow(clippy::expect_used)] // Fixtures keep failures local and readable.

use domain_ir::{
    FORM_CONTROL_SCHEMA_VERSION, FormButtonBackStyle, FormButtonValue, FormCharacterProperties,
    FormCommonProperties, FormControlAnchor, FormControlBuilder, FormControlIdentity,
    FormControlLimitConfig, FormControlLimits, FormControlOperation, FormControlPayload,
    FormControlRequest, FormControlRequestDraft, FormControlState, FormDateValidation,
    FormDocumentState, FormDocumentStateDraft, FormListItem, FormNativeBinding, FormScrollBars,
    FormSelectionValidation, FormTabAssignment, FormTabKeyBehavior, FormTextAlignment,
    FormTextValidation, LogicalId, NativeFormTag,
};
use hwpx_package::{
    FORM_CONTROL_HWPX_PROFILE_ID, FormControlHwpxBuilder, FormControlHwpxError,
    FormControlHwpxLimitConfig, FormControlHwpxLimits, FormControlHwpxLowerer,
    FormControlHwpxReader,
};

const FLOW_A: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
const FLOW_B: &str = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const STATE_C: &str = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";

fn state_limits() -> FormControlLimits {
    FormControlLimits::new(FormControlLimitConfig::default()).expect("state limits")
}

fn hwpx_limits() -> FormControlHwpxLimits {
    FormControlHwpxLimits::new(FormControlHwpxLimitConfig::default()).expect("HWPX limits")
}

fn identity(index: u32) -> FormControlIdentity {
    FormControlIdentity {
        logical_control_id: LogicalId::parse(format!("form-{index}")).expect("logical id"),
        native_object_id: 100 + index,
    }
}

fn common(index: u32) -> FormCommonProperties {
    FormCommonProperties {
        name: format!("control-{index}"),
        fore_color_rgb: 0x0011_2233,
        back_color_rgb: 0x00ee_ddcc,
        group_name: Some("group-a".to_owned()),
        tab_stop: true,
        tab_order: Some(index - 1),
        editable: true,
        enabled: true,
        border_type_id_ref: index,
        draw_frame: true,
        printable: true,
        command_sha256: None,
        character: FormCharacterProperties {
            char_pr_id_ref: index,
            follow_context: false,
            auto_size: false,
            word_wrap: true,
        },
    }
}

fn items() -> Vec<FormListItem> {
    vec![
        FormListItem {
            display_text: "One".to_owned(),
            value: "one".to_owned(),
        },
        FormListItem {
            display_text: "Two".to_owned(),
            value: "two".to_owned(),
        },
    ]
}

fn text_payload() -> FormControlPayload {
    FormControlPayload::Text {
        value: "alpha".to_owned(),
        default_value: "alpha".to_owned(),
        validation: FormTextValidation {
            required: true,
            minimum_characters: 1,
            maximum_characters: Some(64),
            external_validator_sha256: Some(FLOW_A.to_owned()),
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

fn payloads() -> Vec<FormControlPayload> {
    vec![
        text_payload(),
        FormControlPayload::Checkbox {
            caption: "Agree".to_owned(),
            value: FormButtonValue::Checked,
            default_value: FormButtonValue::Unchecked,
            must_be_checked: true,
            radio_group_name: None,
            tri_state: false,
            back_style: FormButtonBackStyle::Transparent,
        },
        FormControlPayload::Radio {
            caption: "Choice".to_owned(),
            value: FormButtonValue::Unchecked,
            default_value: FormButtonValue::Unchecked,
            radio_group_name: "radio-a".to_owned(),
            group_required: false,
            tri_state: false,
            back_style: FormButtonBackStyle::Opaque,
        },
        FormControlPayload::Combo {
            items: items(),
            selected_value: Some("one".to_owned()),
            default_selected_value: Some("two".to_owned()),
            validation: FormSelectionValidation {
                required: true,
                external_validator_sha256: None,
            },
            list_box_rows: Some(4),
            list_box_width_hwp_units: Some(7200),
            edit_enable: false,
        },
        FormControlPayload::List {
            items: items(),
            selected_value: Some("two".to_owned()),
            default_selected_value: Some("one".to_owned()),
            validation: FormSelectionValidation {
                required: true,
                external_validator_sha256: None,
            },
            item_height_hwp_units: Some(1000),
            top_index: 0,
        },
    ]
}

fn binding(payload: &FormControlPayload) -> FormNativeBinding {
    let tag = match payload {
        FormControlPayload::Text { .. } => NativeFormTag::Edit,
        FormControlPayload::Checkbox { .. } => NativeFormTag::CheckBtn,
        FormControlPayload::Radio { .. } => NativeFormTag::RadioBtn,
        FormControlPayload::Combo { .. } => NativeFormTag::ComboBox,
        FormControlPayload::List { .. } => NativeFormTag::ListBox,
        FormControlPayload::Date { .. } => return FormNativeBinding::UnverifiedDateControl,
    };
    FormNativeBinding::Exact { tag }
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
        opaque_properties: Vec::new(),
    }
}

fn state(controls: Vec<FormControlState>) -> FormDocumentState {
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
        state_limits(),
    )
    .expect("document state")
}

fn all_controls() -> FormDocumentState {
    state(
        payloads()
            .into_iter()
            .enumerate()
            .map(|(offset, payload)| control(u32::try_from(offset + 1).expect("small"), payload))
            .collect(),
    )
}

fn common_attributes(index: u32) -> String {
    format!(
        "id=\"{}\" instid=\"{}\" name=\"control-{index}\" foreColor=\"#112233\" backColor=\"#EEDDCC\" groupName=\"group-a\" tabStop=\"1\" editable=\"1\" tabOrder=\"{}\" enabled=\"1\" borderTypeIDRef=\"{index}\" drawFrame=\"1\" printable=\"1\"",
        100 + index,
        1000 + index,
        index - 1,
    )
}

fn character(index: u32) -> String {
    format!(
        "<hp:formCharPr charPrIDRef=\"{index}\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/>"
    )
}

fn section_xml() -> Vec<u8> {
    format!(
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<hp:sec xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\"><hp:p id=\"1\"><hp:run charPrIDRef=\"0\">PREFIX<!--preserve--><hp:edit {} multiLine=\"0\" maxLength=\"64\" scrollBars=\"HORIZONTAL\" tabKeyBehavior=\"NEXT_OBJECT\" numOnly=\"0\" readOnly=\"0\" alignText=\"LEFT\">{}<hp:text>alpha</hp:text></hp:edit><hp:checkBtn {} caption=\"Agree\" value=\"CHECKED\" triState=\"0\" backStyle=\"TRANSPARENT\">{}</hp:checkBtn><hp:radioBtn {} caption=\"Choice\" value=\"UNCHECKED\" radioGroupName=\"radio-a\" triState=\"0\" backStyle=\"OPAQUE\">{}</hp:radioBtn><hp:comboBox {} listBoxRows=\"4\" listBoxWidth=\"7200\" editEnable=\"0\" selectedValue=\"one\">{}<hp:listItem displayText=\"One\" value=\"one\"/><hp:listItem displayText=\"Two\" value=\"two\"/></hp:comboBox><hp:listBox {} itemHeight=\"1000\" topIdx=\"0\" selectedValue=\"two\">{}<hp:listItem displayText=\"One\" value=\"one\"/><hp:listItem displayText=\"Two\" value=\"two\"/></hp:listBox>SUFFIX</hp:run></hp:p></hp:sec>",
        common_attributes(1),
        character(1),
        common_attributes(2),
        character(2),
        common_attributes(3),
        character(3),
        common_attributes(4),
        character(4),
        common_attributes(5),
        character(5),
    )
    .into_bytes()
}

fn domain_plan(
    source: &FormDocumentState,
    operation: FormControlOperation,
) -> domain_ir::FormControlPlan {
    let request = FormControlRequest::from_draft(
        FormControlRequestDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.to_owned(),
            request_id: LogicalId::parse("request-hwpx").expect("request id"),
            expected_source_state_sha256: source
                .canonical_sha256(state_limits())
                .expect("state digest"),
            expected_document_flow_sha256: FLOW_A.to_owned(),
            target_document_flow_sha256: FLOW_B.to_owned(),
            operation,
        },
        source,
        FLOW_A,
        state_limits(),
    )
    .expect("request");
    FormControlBuilder::plan(source, &request, FLOW_A, state_limits()).expect("domain plan")
}

#[test]
fn reads_all_five_official_native_form_tags_with_exact_lexicals() {
    let expected = all_controls();
    let readback = FormControlHwpxReader::read_section(
        &section_xml(),
        &expected,
        state_limits(),
        hwpx_limits(),
    )
    .expect("readback");
    assert_eq!(readback.control_count, 5);
    assert_eq!(readback.object_sha256.len(), 5);
    assert_eq!(readback.state, expected);
}

#[test]
fn ref_018_patches_only_common_attributes_and_preserves_payload_bytes() {
    let source_state = all_controls();
    let mut replacement = source_state.controls()[0].common.clone();
    replacement.name = "renamed & safe".to_owned();
    replacement.fore_color_rgb = 0x00ab_cdef;
    replacement.group_name = None;
    replacement.editable = false;
    replacement.border_type_id_ref = 77;
    replacement.character.auto_size = true;
    let domain = domain_plan(
        &source_state,
        FormControlOperation::ReplaceProperties {
            target: identity(1),
            common: replacement,
            payload: source_state.controls()[0].payload.clone(),
        },
    );
    let source = section_xml();
    let plan =
        FormControlHwpxBuilder::plan(&source, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("HWPX plan");
    let repeated =
        FormControlHwpxBuilder::plan(&source, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("repeated HWPX plan");
    assert_eq!(
        plan.canonical_json(hwpx_limits()).expect("plan JSON"),
        repeated
            .canonical_json(hwpx_limits())
            .expect("repeated plan JSON")
    );
    let (output, receipt) = FormControlHwpxLowerer::lower_section_with_receipt(
        &source,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lowering");
    assert_eq!(receipt.profile_id, FORM_CONTROL_HWPX_PROFILE_ID);
    assert_eq!(receipt.capability_id, "ref.form_properties");
    let output_text = String::from_utf8(output).expect("UTF-8");
    assert!(output_text.contains("name=\"renamed &amp; safe\""));
    assert!(output_text.contains("foreColor=\"#ABCDEF\""));
    assert!(output_text.contains("editable=\"0\""));
    assert!(output_text.contains("borderTypeIDRef=\"77\""));
    assert!(output_text.contains("autoSz=\"1\""));
    assert!(!output_text.contains("groupName=\"group-a\" tabStop=\"1\" editable=\"0\""));
    assert!(output_text.contains("<hp:text>alpha</hp:text>"));
    assert!(output_text.contains("PREFIX<!--preserve-->"));
    assert!(output_text.contains("SUFFIX</hp:run>"));

    let exact_source_limit = FormControlHwpxLimits::new(FormControlHwpxLimitConfig {
        section_bytes: source.len(),
        output_bytes: source.len(),
        ..FormControlHwpxLimitConfig::default()
    })
    .expect("exact source limit");
    let limited_plan =
        FormControlHwpxBuilder::plan(&source, &domain, FLOW_A, state_limits(), exact_source_limit)
            .expect("limited plan");
    assert_eq!(
        FormControlHwpxLowerer::lower_section(
            &source,
            &limited_plan,
            FLOW_A,
            state_limits(),
            exact_source_limit,
        ),
        Err(FormControlHwpxError::OutputLimit)
    );
}

#[test]
fn ref_019_replaces_complete_tab_order_without_touching_other_properties() {
    let source_state = all_controls();
    let assignments = [Some(2), Some(3), None, Some(0), Some(1)]
        .into_iter()
        .enumerate()
        .map(|(offset, tab_order)| FormTabAssignment {
            target: identity(u32::try_from(offset + 1).expect("small")),
            tab_stop: tab_order.is_some(),
            tab_order,
        })
        .collect();
    let domain = domain_plan(
        &source_state,
        FormControlOperation::SetTabOrder { assignments },
    );
    let source = section_xml();
    let plan =
        FormControlHwpxBuilder::plan(&source, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("HWPX plan");
    let output = FormControlHwpxLowerer::lower_section(
        &source,
        &plan,
        FLOW_A,
        state_limits(),
        hwpx_limits(),
    )
    .expect("lowering");
    let text = String::from_utf8(output).expect("UTF-8");
    assert!(text.contains("name=\"control-1\" foreColor=\"#112233\""));
    assert!(text.contains("tabStop=\"0\" editable=\"1\" tabOrder=\"-1\""));
}

#[test]
fn source_state_flow_and_projection_drift_fail_closed() {
    let source_state = all_controls();
    let mut replacement = source_state.controls()[0].common.clone();
    replacement.enabled = false;
    let domain = domain_plan(
        &source_state,
        FormControlOperation::ReplaceProperties {
            target: identity(1),
            common: replacement,
            payload: source_state.controls()[0].payload.clone(),
        },
    );
    let source = section_xml();
    let plan =
        FormControlHwpxBuilder::plan(&source, &domain, FLOW_A, state_limits(), hwpx_limits())
            .expect("plan");
    assert_eq!(
        FormControlHwpxLowerer::lower_section(
            &source,
            &plan,
            FLOW_B,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FormControlHwpxError::SourceDrift)
    );
    let mut changed = source.clone();
    changed.extend_from_slice(b" ");
    assert_eq!(
        FormControlHwpxLowerer::lower_section(
            &changed,
            &plan,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FormControlHwpxError::SourceDrift)
    );
    let malformed = String::from_utf8(source).expect("UTF-8").replacen(
        "foreColor=\"#112233\"",
        "foreColor=\"#11223g\"",
        1,
    );
    assert_eq!(
        FormControlHwpxReader::read_section(
            malformed.as_bytes(),
            &source_state,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FormControlHwpxError::ProjectionMismatch)
    );
}

#[test]
fn payload_mutation_insertion_and_unverified_date_are_not_representable() {
    let source_state = all_controls();
    let mut changed_payload = source_state.controls()[0].payload.clone();
    match &mut changed_payload {
        FormControlPayload::Text { value, .. } => *value = "changed".to_owned(),
        _ => unreachable!("text fixture"),
    }
    let domain = domain_plan(
        &source_state,
        FormControlOperation::ReplaceProperties {
            target: identity(1),
            common: source_state.controls()[0].common.clone(),
            payload: changed_payload,
        },
    );
    assert!(matches!(
        FormControlHwpxBuilder::plan(
            &section_xml(),
            &domain,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FormControlHwpxError::NonRepresentable)
    ));

    let inserted = control(6, text_payload());
    let insertion = domain_plan(
        &source_state,
        FormControlOperation::Insert {
            insertion_index: 5,
            control: inserted,
        },
    );
    assert!(matches!(
        FormControlHwpxBuilder::plan(
            &section_xml(),
            &insertion,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FormControlHwpxError::NonRepresentable)
    ));

    let date_payload = FormControlPayload::Date {
        value: Some("2026-09-12".to_owned()),
        default_value: Some("2026-09-12".to_owned()),
        format: "yyyy-MM-dd".to_owned(),
        locale: "ko-KR".to_owned(),
        validation: FormDateValidation {
            required: true,
            earliest: None,
            latest: None,
            external_validator_sha256: None,
        },
    };
    let date_state = state(vec![control(1, date_payload)]);
    let mut date_common = date_state.controls()[0].common.clone();
    date_common.enabled = false;
    let date_plan = domain_plan(
        &date_state,
        FormControlOperation::ReplaceProperties {
            target: identity(1),
            common: date_common,
            payload: date_state.controls()[0].payload.clone(),
        },
    );
    assert!(matches!(
        FormControlHwpxBuilder::plan(
            &section_xml(),
            &date_plan,
            FLOW_A,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FormControlHwpxError::NonRepresentable)
    ));
}

#[test]
fn malformed_structure_finite_limits_and_debug_output_are_safe() {
    let source_state = all_controls();
    let duplicate = String::from_utf8(section_xml()).expect("UTF-8").replacen(
        "name=\"control-1\"",
        "name=\"control-1\" name=\"again\"",
        1,
    );
    assert!(
        FormControlHwpxReader::read_section(
            duplicate.as_bytes(),
            &source_state,
            state_limits(),
            hwpx_limits(),
        )
        .is_err()
    );
    let missing_character =
        String::from_utf8(section_xml())
            .expect("UTF-8")
            .replacen(&character(1), "", 1);
    assert_eq!(
        FormControlHwpxReader::read_section(
            missing_character.as_bytes(),
            &source_state,
            state_limits(),
            hwpx_limits(),
        ),
        Err(FormControlHwpxError::UnsupportedControl)
    );
    let tiny = FormControlHwpxLimits::new(FormControlHwpxLimitConfig {
        section_bytes: 64,
        output_bytes: 64,
        ..FormControlHwpxLimitConfig::default()
    })
    .expect("tiny limits");
    assert_eq!(
        FormControlHwpxReader::read_section(&section_xml(), &source_state, state_limits(), tiny,),
        Err(FormControlHwpxError::InputLimit)
    );
    let debug = format!(
        "{:?}",
        FormControlHwpxReader::read_section(
            &section_xml(),
            &source_state,
            state_limits(),
            hwpx_limits(),
        )
        .expect("readback")
    );
    assert!(!debug.contains("alpha"));
    assert!(!debug.contains("control-1"));
}
