//! Compile the successor production file without changing the frozen shared exports yet.
mod preserving_xml {
    pub use hwpx_package::{
        PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlElementToken,
    };
}
#[allow(dead_code)]
#[path = "../examples/p08_19_support/common.rs"]
mod archive;
#[path = "../src/native_form_hwpx.rs"]
mod native_form_hwpx;

use domain_ir::*;
use native_form_hwpx::*;
use std::{error::Error, fmt::Write as _, fs, path::Path};

type AnyError = Box<dyn Error>;
const ACTUAL: &str = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx";
const ACTUAL_SHA: &str = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const FLOW: &str = "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1";

fn actual() -> Result<Vec<u8>, AnyError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(ACTUAL);
    for ancestor in path.ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("capture reparse rejected".into());
            }
        }
        if metadata.file_type().is_symlink() {
            return Err("capture link rejected".into());
        }
    }
    let metadata = fs::metadata(&path)?;
    if !metadata.is_file() || metadata.len() != 14_556 {
        return Err("capture bounds changed".into());
    }
    let raw = fs::read(path)?;
    if raw.len() != 14_556 || archive::sha256(&raw) != ACTUAL_SHA {
        return Err("capture identity changed".into());
    }
    let section = archive::section_from_package(&raw)?;
    if archive::sha256(&section)
        != "89a263eff5d4536cc14223e48847a42e65c7e4f97d5b0c12b5cf73dc4bbba2ff"
    {
        return Err("capture section changed".into());
    }
    Ok(section)
}
fn domain_limits() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
}
fn map(paragraphs: usize, count: usize) -> Result<NativeFormHwpxMap, AnyError> {
    Ok(NativeFormHwpxMap {
        paragraph_ids: (0..paragraphs)
            .map(|i| LogicalId::parse(format!("paragraph-{i}").as_str()))
            .collect::<Result<_, _>>()?,
        component_controls: (0..count)
            .map(|i| {
                Ok(FormControlIdentity {
                    logical_control_id: LogicalId::parse(format!("control-{i}").as_str())?,
                    native_object_id: 90_001 + u32::try_from(i)?,
                })
            })
            .collect::<Result<_, AnyError>>()?,
    })
}

// Explicit component test policy defaults; these are not claimed to be native observations.
fn draft(readback: &NativeFormHwpxReadback) -> FormDocumentStateDraft {
    let controls = readback
        .controls()
        .iter()
        .map(|n| FormControlState {
            identity: n.component_identity.clone(),
            anchor: FormControlAnchor {
                paragraph_id: n.anchor.paragraph_id.clone(),
                run_ordinal: n.anchor.run_ordinal,
                inline_ordinal: n.anchor.inline_ordinal,
            },
            native_binding: FormNativeBinding::Exact { tag: n.tag },
            common: n.common.clone(),
            payload: policy_payload(n),
            shape_locked: n.shape_locked,
            shape_state_sha256: n.geometry_sha256.clone(),
            opaque_native_payload_sha256: n.preserved_opaque_sha256.clone(),
            opaque_properties: Vec::new(),
        })
        .collect();
    FormDocumentStateDraft {
        schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
        controls,
        non_form_content_sha256: readback.non_form_content_sha256().into(),
        style_catalog_sha256: FLOW.into(),
        border_catalog_sha256: FLOW.into(),
        resource_inventory_sha256: FLOW.into(),
        reference_inventory_sha256: FLOW.into(),
        document_protection_sha256: FLOW.into(),
        opaque_document_state_sha256: FLOW.into(),
    }
}
fn policy_payload(n: &NativeFormControlObservation) -> FormControlPayload {
    match &n.payload {
        NativeFormObservedPayload::Text {
            value,
            multi_line,
            password_character,
            native_max_length,
            scroll_bars,
            tab_key_behavior,
            number_only,
            read_only,
            alignment,
        } => FormControlPayload::Text {
            value: value.clone(),
            default_value: value.clone(),
            validation: FormTextValidation {
                required: false,
                minimum_characters: 0,
                maximum_characters: *native_max_length,
                external_validator_sha256: None,
            },
            multi_line: *multi_line,
            password_character: password_character.clone(),
            native_max_length: *native_max_length,
            scroll_bars: *scroll_bars,
            tab_key_behavior: *tab_key_behavior,
            number_only: *number_only,
            read_only: *read_only,
            alignment: *alignment,
        },
        NativeFormObservedPayload::Button {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
        } if n.tag == NativeFormTag::RadioBtn => FormControlPayload::Radio {
            caption: caption.clone(),
            value: *value,
            default_value: *value,
            radio_group_name: radio_group_name.clone().unwrap_or_default(),
            group_required: false,
            tri_state: *tri_state,
            back_style: *back_style,
        },
        NativeFormObservedPayload::Button {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
        } => FormControlPayload::Checkbox {
            caption: caption.clone(),
            value: *value,
            default_value: *value,
            must_be_checked: false,
            radio_group_name: radio_group_name.clone(),
            tri_state: *tri_state,
            back_style: *back_style,
        },
        NativeFormObservedPayload::Combo {
            items,
            selected_value,
            list_box_rows,
            list_box_width_hwp_units,
            edit_enable,
        } => FormControlPayload::Combo {
            items: items.clone(),
            selected_value: selected_value.clone(),
            default_selected_value: selected_value.clone(),
            validation: FormSelectionValidation {
                required: false,
                external_validator_sha256: None,
            },
            list_box_rows: *list_box_rows,
            list_box_width_hwp_units: *list_box_width_hwp_units,
            edit_enable: *edit_enable,
        },
        NativeFormObservedPayload::List {
            items,
            selected_value,
            item_height_hwp_units,
            top_index,
        } => FormControlPayload::List {
            items: items.clone(),
            selected_value: selected_value.clone(),
            default_selected_value: selected_value.clone(),
            validation: FormSelectionValidation {
                required: false,
                external_validator_sha256: None,
            },
            item_height_hwp_units: *item_height_hwp_units,
            top_index: *top_index,
        },
    }
}
fn state(readback: &NativeFormHwpxReadback) -> Result<FormDocumentState, AnyError> {
    Ok(FormDocumentState::from_draft(
        draft(readback),
        domain_limits()?,
    )?)
}
fn plan(
    source: &[u8],
    observed: &NativeFormHwpxReadback,
    operation: FormControlOperation,
) -> Result<NativeFormHwpxPlan, AnyError> {
    let state = state(observed)?;
    let request = FormControlRequest::from_draft(
        FormControlRequestDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("native-form-test")?,
            expected_source_state_sha256: state.canonical_sha256(domain_limits()?)?,
            expected_document_flow_sha256: FLOW.into(),
            target_document_flow_sha256: FLOW.into(),
            operation,
        },
        &state,
        FLOW,
        domain_limits()?,
    )?;
    let domain_plan = FormControlBuilder::plan(&state, &request, FLOW, domain_limits()?)?;
    Ok(NativeFormHwpxBuilder::plan(
        source,
        observed,
        &domain_plan,
        FLOW,
        domain_limits()?,
        NativeFormHwpxLimits::default(),
    )?)
}
fn properties(
    observed: &NativeFormHwpxReadback,
    selected: usize,
) -> Result<FormControlOperation, AnyError> {
    let state = state(observed)?;
    let before = &state.controls()[selected];
    let mut common = before.common.clone();
    common.enabled = !common.enabled;
    common.group_name = Some("native group & <한글> 🚀".into());
    common.character.word_wrap = !common.character.word_wrap;
    Ok(FormControlOperation::ReplaceProperties {
        target: before.identity.clone(),
        common,
        payload: before.payload.clone(),
    })
}
fn synthetic(kinds: &[&str], identities: &str) -> Vec<u8> {
    let mut body = String::new();
    for (i, kind) in kinds.iter().enumerate() {
        let (attributes, payload) = match *kind {
            "edit" => (
                "multiLine=\"0\" passwordChar=\"*\" maxLength=\"64\" scrollBars=\"NONE\" tabKeyBehavior=\"NEXT_OBJECT\" numOnly=\"0\" readOnly=\"0\" alignText=\"LEFT\"",
                "<hp:text>literal &amp; &lt;한글&gt; 🚀</hp:text>",
            ),
            "checkBtn" => (
                "caption=\"checkbox\" value=\"CHECKED\" radioGroupName=\"\" triState=\"0\" backStyle=\"OPAQUE\"",
                "",
            ),
            "radioBtn" => (
                "caption=\"radio\" value=\"UNCHECKED\" radioGroupName=\"radio-group\" triState=\"0\" backStyle=\"TRANSPARENT\"",
                "",
            ),
            "comboBox" => (
                "listBoxRows=\"3\" listBoxWidth=\"10800\" editEnable=\"1\" selectedValue=\"a\"",
                "<hp:listItem displayText=\"한글 &amp; a\" value=\"a\"/><hp:listItem displayText=\"b\" value=\"b\"/>",
            ),
            _ => (
                "itemHeight=\"1000\" topIdx=\"0\" selectedValue=\"b\"",
                "<hp:listItem displayText=\"a\" value=\"a\"/><hp:listItem displayText=\"한글 b\" value=\"b\"/>",
            ),
        };
        let _ = write!(
            body,
            "<hp:{kind} {identities} name=\"field{i}\" foreColor=\"#000000\" backColor=\"#FFFFFF\" groupName=\"\" tabStop=\"1\" editable=\"1\" tabOrder=\"{i}\" enabled=\"1\" borderTypeIDRef=\"0\" drawFrame=\"1\" printable=\"1\" command=\"\" {attributes}><hp:formCharPr charPrIDRef=\"0\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/>{payload}<hp:sz width=\"10800\" height=\"5400\" protect=\"0\"/><hp:pos horzOffset=\"0\" vertOffset=\"0\"/><hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/></hp:{kind}>"
        );
    }
    format!("<hs:sec xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" xmlns:hp=\"{HP}\"><hp:p id=\"0\"><hp:run charPrIDRef=\"0\"><hp:t>unchanged main</hp:t>{body}</hp:run></hp:p></hs:sec>").into_bytes()
}

#[test]
fn actual_native_missing_id_observed_without_injection() -> Result<(), AnyError> {
    let source = actual()?;
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(2, 1)?, NativeFormHwpxLimits::default())?;
    assert_eq!(
        observed.controls()[0].native_identity,
        NativeFormObservedIdentity::Missing
    );
    assert_eq!(
        observed.controls()[0].component_identity.native_object_id,
        90_001
    );
    observed.verify_domain_state(&state(&observed)?, domain_limits()?)?;
    NativeFormHwpxReader::verify_section(&source, &observed, NativeFormHwpxLimits::default())?;
    assert_eq!(actual()?, source);
    assert_eq!(observed.section_sha256(), archive::sha256(&source));
    Ok(())
}
#[test]
fn actual_properties_lower_keep_missing_ids_geometry_payload_and_opaque_bytes()
-> Result<(), AnyError> {
    let source = actual()?;
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(2, 1)?, NativeFormHwpxLimits::default())?;
    let plan = plan(&source, &observed, properties(&observed, 0)?)?;
    let (output, receipt) = NativeFormHwpxLowerer::lower_section(
        &source,
        &plan,
        FLOW,
        domain_limits()?,
        NativeFormHwpxLimits::default(),
    )?;
    assert!(receipt.outside_declared_edits_byte_exact);
    assert_eq!(receipt.changed_attribute_count, 3);
    let after = &receipt.target_readback.controls()[0];
    let before = &observed.controls()[0];
    assert_eq!(after.native_identity, NativeFormObservedIdentity::Missing);
    assert_eq!(after.anchor, before.anchor);
    assert_eq!(after.geometry_sha256, before.geometry_sha256);
    assert_eq!(
        after.preserved_opaque_sha256,
        before.preserved_opaque_sha256
    );
    assert_eq!(after.payload, before.payload);
    assert_ne!(receipt.output_section_sha256, receipt.source_section_sha256);
    assert_ne!(output, source);
    assert_eq!(actual()?, source);
    assert_eq!(plan.plan_sha256().len(), 64);
    assert!(
        !plan
            .canonical_json(NativeFormHwpxLimits::default())?
            .is_empty()
    );
    Ok(())
}
#[test]
fn forged_component_anchor_geometry_or_opaque_hash_not_admitted() -> Result<(), AnyError> {
    let source = actual()?;
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(2, 1)?, NativeFormHwpxLimits::default())?;
    for mutation in 0..5 {
        let mut bad = draft(&observed);
        match mutation {
            0 => bad.controls[0].anchor.inline_ordinal = 999,
            1 => bad.controls[0].anchor.run_ordinal = 999,
            2 => bad.controls[0].shape_state_sha256 = FLOW.into(),
            3 => bad.controls[0].opaque_native_payload_sha256 = FLOW.into(),
            _ => bad.non_form_content_sha256 = FLOW.into(),
        }
        let bad = FormDocumentState::from_draft(bad, domain_limits()?)?;
        assert!(matches!(
            observed.verify_domain_state(&bad, domain_limits()?),
            Err(NativeFormHwpxError::ProjectionMismatch)
        ));
    }
    Ok(())
}
#[test]
fn all_five_native_kinds_support_real_typed_properties_without_synthetic_xml_ids()
-> Result<(), AnyError> {
    let source = synthetic(&["edit", "checkBtn", "radioBtn", "comboBox", "listBox"], "");
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(1, 5)?, NativeFormHwpxLimits::default())?;
    for i in 0..5 {
        let plan = plan(&source, &observed, properties(&observed, i)?)?;
        let (_, receipt) = NativeFormHwpxLowerer::lower_section(
            &source,
            &plan,
            FLOW,
            domain_limits()?,
            NativeFormHwpxLimits::default(),
        )?;
        assert!(
            receipt
                .target_readback
                .controls()
                .iter()
                .all(|n| n.native_identity == NativeFormObservedIdentity::Missing)
        );
        assert!(!receipt.target_readback.controls()[i].common.enabled);
        for j in 0..5 {
            if i != j {
                assert_eq!(
                    receipt.target_readback.controls()[j],
                    observed.controls()[j]
                );
            }
        }
    }
    Ok(())
}
#[test]
fn complete_tab_order_updates_all_controls_and_preserves_every_native_identity()
-> Result<(), AnyError> {
    let source = synthetic(&["edit", "checkBtn", "radioBtn", "comboBox", "listBox"], "");
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(1, 5)?, NativeFormHwpxLimits::default())?;
    let state = state(&observed)?;
    let assignments = state
        .controls()
        .iter()
        .enumerate()
        .map(|(i, c)| FormTabAssignment {
            target: c.identity.clone(),
            tab_stop: true,
            tab_order: Some(4 - u32::try_from(i).unwrap_or(4)),
        })
        .collect();
    let plan = plan(
        &source,
        &observed,
        FormControlOperation::SetTabOrder { assignments },
    )?;
    let (_, receipt) = NativeFormHwpxLowerer::lower_section(
        &source,
        &plan,
        FLOW,
        domain_limits()?,
        NativeFormHwpxLimits::default(),
    )?;
    assert_eq!(receipt.changed_attribute_count, 4);
    for (i, c) in receipt.target_readback.controls().iter().enumerate() {
        assert_eq!(c.common.tab_order, Some(4 - u32::try_from(i)?));
        assert_eq!(c.native_identity, NativeFormObservedIdentity::Missing);
    }
    Ok(())
}
#[test]
fn native_optional_id_variants_never_equal_component_reservations() -> Result<(), AnyError> {
    for attributes in [
        "id=\"77\"",
        "instid=\"88\"",
        "instId=\"88\"",
        "id=\"77\" instId=\"88\"",
    ] {
        let source = synthetic(&["edit"], attributes);
        let observed = NativeFormHwpxReader::read_section(
            &source,
            &map(1, 1)?,
            NativeFormHwpxLimits::default(),
        )?;
        assert!(matches!(
            observed.controls()[0].native_identity,
            NativeFormObservedIdentity::Observed { .. }
        ));
        let plan = plan(&source, &observed, properties(&observed, 0)?)?;
        let (_, r) = NativeFormHwpxLowerer::lower_section(
            &source,
            &plan,
            FLOW,
            domain_limits()?,
            NativeFormHwpxLimits::default(),
        )?;
        assert_eq!(
            r.target_readback.controls()[0].native_identity,
            observed.controls()[0].native_identity
        );
    }
    Ok(())
}
#[test]
fn duplicate_native_ids_aliases_or_namespaced_semantic_attributes_fail_closed()
-> Result<(), AnyError> {
    for source in [
        synthetic(&["edit", "checkBtn"], "id=\"77\""),
        synthetic(&["edit"], "instid=\"88\" instId=\"88\""),
        synthetic(&["edit"], "xmlns:x=\"urn:opaque\" x:id=\"77\""),
        synthetic(&["edit"], "id=\"077\""),
    ] {
        let count = if std::str::from_utf8(&source)?.contains("checkBtn") {
            2
        } else {
            1
        };
        assert!(
            NativeFormHwpxReader::read_section(
                &source,
                &map(1, count)?,
                NativeFormHwpxLimits::default()
            )
            .is_err()
        );
    }
    Ok(())
}
#[test]
fn incomplete_duplicate_or_changed_maps_rejected() -> Result<(), AnyError> {
    let source = synthetic(&["edit", "checkBtn"], "");
    let complete = map(1, 2)?;
    for i in 0..4 {
        let mut bad = complete.clone();
        match i {
            0 => bad.component_controls.pop().map(|_| ()),
            1 => {
                bad.component_controls[1] = bad.component_controls[0].clone();
                None
            }
            2 => {
                bad.paragraph_ids.clear();
                None
            }
            _ => {
                bad.component_controls[0].native_object_id = 0;
                None
            }
        };
        assert!(
            NativeFormHwpxReader::read_section(&source, &bad, NativeFormHwpxLimits::default())
                .is_err()
        );
    }
    let observed =
        NativeFormHwpxReader::read_section(&source, &complete, NativeFormHwpxLimits::default())?;
    let changed = source
        .iter()
        .copied()
        .chain(b" ".iter().copied())
        .collect::<Vec<_>>();
    assert!(
        NativeFormHwpxReader::verify_section(&changed, &observed, NativeFormHwpxLimits::default())
            .is_err()
    );
    Ok(())
}
#[test]
fn source_payload_geometry_or_nonselected_drift_aborts_lowering() -> Result<(), AnyError> {
    let source = synthetic(&["edit", "checkBtn"], "");
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(1, 2)?, NativeFormHwpxLimits::default())?;
    let plan = plan(&source, &observed, properties(&observed, 0)?)?;
    let text = std::str::from_utf8(&source)?;
    for changed in [
        text.replace("width=\"10800\"", "width=\"10801\""),
        text.replace("unchanged main", "changed main"),
        text.replace("checkbox", "changed checkbox"),
        text.replace("literal", "tampered"),
    ] {
        assert!(
            NativeFormHwpxLowerer::lower_section(
                changed.as_bytes(),
                &plan,
                FLOW,
                domain_limits()?,
                NativeFormHwpxLimits::default()
            )
            .is_err()
        );
    }
    assert!(
        NativeFormHwpxLowerer::lower_section(
            &source,
            &plan,
            &"b".repeat(64),
            domain_limits()?,
            NativeFormHwpxLimits::default()
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn optional_missing_group_attribute_can_be_added_without_opaque_drift() -> Result<(), AnyError> {
    let source = std::str::from_utf8(&synthetic(&["edit"], ""))?
        .replace(" groupName=\"\"", "")
        .into_bytes();
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(1, 1)?, NativeFormHwpxLimits::default())?;
    let plan = plan(&source, &observed, properties(&observed, 0)?)?;
    let (_, r) = NativeFormHwpxLowerer::lower_section(
        &source,
        &plan,
        FLOW,
        domain_limits()?,
        NativeFormHwpxLimits::default(),
    )?;
    assert_eq!(
        r.target_readback.controls()[0].common.group_name.as_deref(),
        Some("native group & <한글> 🚀")
    );
    assert_eq!(
        r.target_readback.controls()[0].preserved_opaque_sha256,
        observed.controls()[0].preserved_opaque_sha256
    );
    Ok(())
}
#[test]
fn unknown_opaque_attributes_children_and_command_preserved_not_executed() -> Result<(), AnyError> {
    let text = String::from_utf8(synthetic(
        &["edit"],
        "xmlns:opaque=\"urn:opaque\" opaque:tag=\"private\"",
    ))?;
    let source = text
        .replace("command=\"\"", "command=\"opaque &amp; never execute\"")
        .replace(
            "</hp:edit>",
            "<opaque:metadata value=\"private\"/></hp:edit>",
        )
        .into_bytes();
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(1, 1)?, NativeFormHwpxLimits::default())?;
    let plan = plan(&source, &observed, properties(&observed, 0)?)?;
    let (output, r) = NativeFormHwpxLowerer::lower_section(
        &source,
        &plan,
        FLOW,
        domain_limits()?,
        NativeFormHwpxLimits::default(),
    )?;
    assert!(String::from_utf8(output)?.contains("opaque &amp; never execute"));
    assert_eq!(
        r.target_readback.controls()[0].preserved_opaque_sha256,
        observed.controls()[0].preserved_opaque_sha256
    );
    Ok(())
}
#[test]
fn rich_text_wrong_namespace_or_duplicate_geometry_rejected() -> Result<(), AnyError> {
    let text = String::from_utf8(synthetic(&["edit"], ""))?;
    for changed in [
        text.replace("<hp:text>", "<hp:text><hp:t>nested</hp:t>"),
        text.replace("<hp:sz ", "<hp:sz protect=\"0\"/><hp:sz "),
        text.replace(HP, "urn:foreign-paragraph"),
    ] {
        assert!(
            NativeFormHwpxReader::read_section(
                changed.as_bytes(),
                &map(1, 1)?,
                NativeFormHwpxLimits::default()
            )
            .is_err()
        );
    }
    Ok(())
}
#[test]
fn protected_actual_shape_blocks_typed_properties_without_output() -> Result<(), AnyError> {
    let source = String::from_utf8(synthetic(&["edit"], ""))?
        .replace("protect=\"0\"", "protect=\"1\"")
        .into_bytes();
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(1, 1)?, NativeFormHwpxLimits::default())?;
    assert!(observed.controls()[0].shape_locked);
    assert!(plan(&source, &observed, properties(&observed, 0)?).is_err());
    Ok(())
}
#[test]
fn payload_update_or_command_change_not_disguised_as_properties() -> Result<(), AnyError> {
    let source = synthetic(&["edit"], "");
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(1, 1)?, NativeFormHwpxLimits::default())?;
    let state = state(&observed)?;
    let c = &state.controls()[0];
    let mut payload = c.payload.clone();
    if let FormControlPayload::Text { value, .. } = &mut payload {
        *value = "changed value".into();
    }
    let op = FormControlOperation::ReplaceProperties {
        target: c.identity.clone(),
        common: c.common.clone(),
        payload,
    };
    assert!(plan(&source, &observed, op).is_err());
    let mut common = c.common.clone();
    common.command_sha256 = Some(FLOW.into());
    let op = FormControlOperation::ReplaceProperties {
        target: c.identity.clone(),
        common,
        payload: c.payload.clone(),
    };
    assert!(plan(&source, &observed, op).is_err());
    Ok(())
}
#[test]
fn debug_redacts_actual_values_names_maps_paths_and_hashes() -> Result<(), AnyError> {
    let source = actual()?;
    let observed =
        NativeFormHwpxReader::read_section(&source, &map(2, 1)?, NativeFormHwpxLimits::default())?;
    let plan = plan(&source, &observed, properties(&observed, 0)?)?;
    let (_, r) = NativeFormHwpxLowerer::lower_section(
        &source,
        &plan,
        FLOW,
        domain_limits()?,
        NativeFormHwpxLimits::default(),
    )?;
    let debug = format!("{observed:?} {plan:?} {r:?} {:?}", observed.controls());
    for secret in [
        "P08 FORM INSERT",
        "p08field",
        "native group",
        observed.section_sha256(),
        "control-0",
        "paragraph-0",
    ] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}
#[test]
fn finite_limits_refuse_zero_hard_ceilings_and_changed_output_budgets() -> Result<(), AnyError> {
    assert!(NativeFormHwpxLimits::new(0, 1, 1, 1, 1).is_err());
    assert!(NativeFormHwpxLimits::new(3 * 1024 * 1024, 1, 1, 1, 1).is_err());
    let source = synthetic(&["edit"], "");
    let map = map(1, 1)?;
    let small = NativeFormHwpxLimits::new(source.len() - 1, 65536, 1, 65536, 4 * 1024 * 1024)?;
    assert!(NativeFormHwpxReader::read_section(&source, &map, small).is_err());
    let observed =
        NativeFormHwpxReader::read_section(&source, &map, NativeFormHwpxLimits::default())?;
    let plan = plan(&source, &observed, properties(&observed, 0)?)?;
    let exact = NativeFormHwpxLimits::new(source.len(), 65536, 1, 65536, 4 * 1024 * 1024)?;
    assert!(
        NativeFormHwpxLowerer::lower_section(&source, &plan, FLOW, domain_limits()?, exact)
            .is_err()
    );
    Ok(())
}

#[test]
fn opaque_character_contents_and_inter_child_comments_are_independently_bound()
-> Result<(), AnyError> {
    let original_xml = String::from_utf8(synthetic(&["edit"], ""))?;
    let opaque_character = original_xml.replace(
        "wordWrap=\"1\"/>",
        "wordWrap=\"1\"><hp:private>opaque</hp:private></hp:formCharPr>",
    );
    let commented = original_xml.replace("<hp:sz ", "<!--keep opaque--><hp:sz ");
    let base = NativeFormHwpxReader::read_section(
        original_xml.as_bytes(),
        &map(1, 1)?,
        NativeFormHwpxLimits::default(),
    )?;
    let base_state = state(&base)?;
    for changed in [opaque_character, commented] {
        let observed = NativeFormHwpxReader::read_section(
            changed.as_bytes(),
            &map(1, 1)?,
            NativeFormHwpxLimits::default(),
        )?;
        assert_ne!(
            observed.controls()[0].preserved_opaque_sha256,
            base.controls()[0].preserved_opaque_sha256
        );
        assert!(
            observed
                .verify_domain_state(&base_state, domain_limits()?)
                .is_err()
        );
        let plan = plan(changed.as_bytes(), &observed, properties(&observed, 0)?)?;
        let (_, receipt) = NativeFormHwpxLowerer::lower_section(
            changed.as_bytes(),
            &plan,
            FLOW,
            domain_limits()?,
            NativeFormHwpxLimits::default(),
        )?;
        assert_eq!(
            receipt.target_readback.controls()[0].preserved_opaque_sha256,
            observed.controls()[0].preserved_opaque_sha256
        );
    }
    Ok(())
}

#[test]
fn nested_paragraph_path_is_real_and_source_bound_not_only_native_ids() -> Result<(), AnyError> {
    let source = String::from_utf8(synthetic(&["edit"], ""))?;
    let nested = source
        .replace(
            "<hp:p id=\"0\">",
            "<hp:subList id=\"wrapper\"><hp:p id=\"0\">",
        )
        .replace("</hp:p></hs:sec>", "</hp:p></hp:subList></hs:sec>");
    let before = NativeFormHwpxReader::read_section(
        source.as_bytes(),
        &map(1, 1)?,
        NativeFormHwpxLimits::default(),
    )?;
    let after = NativeFormHwpxReader::read_section(
        nested.as_bytes(),
        &map(1, 1)?,
        NativeFormHwpxLimits::default(),
    )?;
    assert_eq!(before.controls()[0].anchor.paragraph_child_path, vec![0]);
    assert_eq!(after.controls()[0].anchor.paragraph_child_path, vec![0, 0]);
    assert!(
        NativeFormHwpxReader::verify_section(
            nested.as_bytes(),
            &before,
            NativeFormHwpxLimits::default()
        )
        .is_err()
    );
    Ok(())
}
