//! Read-only native-form compatibility regression; never creates a native session.
#[allow(dead_code)]
#[path = "p08_19_support/common.rs"]
mod archive;

use domain_ir::{
    FORM_CONTROL_SCHEMA_VERSION, FormCharacterProperties, FormCommonProperties, FormControlAnchor,
    FormControlIdentity, FormControlLimitConfig, FormControlLimits, FormControlPayload,
    FormControlState, FormDocumentState, FormDocumentStateDraft, FormNativeBinding, FormScrollBars,
    FormTabKeyBehavior, FormTextAlignment, FormTextValidation, LogicalId, NativeFormTag,
};
use hwpx_package::{
    FormControlHwpxError, FormControlHwpxLimitConfig, FormControlHwpxLimits, FormControlHwpxReader,
};
use serde_json::json;
use std::{error::Error, fs, path::Path};

type AnyError = Box<dyn Error>;
const SOURCE: &str = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx";
const SHA: &str = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7";
const SECTION_SHA: &str = "89a263eff5d4536cc14223e48847a42e65c7e4f97d5b0c12b5cf73dc4bbba2ff";

fn limits() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
}
fn native_limits() -> Result<FormControlHwpxLimits, AnyError> {
    Ok(FormControlHwpxLimits::new(
        FormControlHwpxLimitConfig::default(),
    )?)
}
fn load_section() -> Result<Vec<u8>, AnyError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(SOURCE);
    for ancestor in path.ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("linked capture rejected".into());
            }
        }
        if metadata.file_type().is_symlink() {
            return Err("linked capture rejected".into());
        }
    }
    let metadata = fs::metadata(&path)?;
    if !metadata.is_file() || metadata.len() != 14_556 {
        return Err("native capture bound changed".into());
    }
    let raw = fs::read(&path)?;
    if raw.len() != 14_556 || archive::sha256(&raw) != SHA {
        return Err("native capture identity changed".into());
    }
    let section = archive::section_from_package(&raw)?;
    if archive::sha256(&section) != SECTION_SHA {
        return Err("native section identity changed".into());
    }
    Ok(section)
}
fn expected_state(anchor: u32, shape: &str) -> Result<FormDocumentState, AnyError> {
    // 8112 is the old insertion contract's expected identity, NOT an observed saved ID.
    let source_binding = SECTION_SHA.to_owned();
    Ok(FormDocumentState::from_draft(
        FormDocumentStateDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
            controls: vec![FormControlState {
                identity: FormControlIdentity {
                    logical_control_id: LogicalId::parse("p08-edit")?,
                    native_object_id: 8112,
                },
                anchor: FormControlAnchor {
                    paragraph_id: LogicalId::parse("paragraph-1")?,
                    run_ordinal: anchor,
                    inline_ordinal: anchor,
                },
                native_binding: FormNativeBinding::Exact {
                    tag: NativeFormTag::Edit,
                },
                common: FormCommonProperties {
                    name: "p08field".into(),
                    fore_color_rgb: 0,
                    back_color_rgb: 0x00ff_ffff,
                    group_name: None,
                    tab_stop: true,
                    tab_order: Some(1),
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
                payload: FormControlPayload::Text {
                    value: "P08 FORM INSERT".into(),
                    default_value: "P08 FORM INSERT".into(),
                    validation: FormTextValidation {
                        required: false,
                        minimum_characters: 0,
                        maximum_characters: Some(64),
                        external_validator_sha256: None,
                    },
                    multi_line: false,
                    password_character: Some("*".into()),
                    native_max_length: Some(64),
                    scroll_bars: FormScrollBars::None,
                    tab_key_behavior: FormTabKeyBehavior::NextObject,
                    number_only: false,
                    read_only: false,
                    alignment: FormTextAlignment::Left,
                },
                shape_locked: false,
                shape_state_sha256: shape.into(),
                opaque_native_payload_sha256: source_binding.clone(),
                opaque_properties: Vec::new(),
            }],
            non_form_content_sha256: source_binding.clone(),
            style_catalog_sha256: source_binding.clone(),
            border_catalog_sha256: source_binding.clone(),
            resource_inventory_sha256: source_binding.clone(),
            reference_inventory_sha256: source_binding.clone(),
            document_protection_sha256: source_binding.clone(),
            opaque_document_state_sha256: source_binding,
        },
        limits()?,
    )?)
}
fn diagnostic_identity_bytes(section: &[u8]) -> Result<Vec<u8>, AnyError> {
    let text = std::str::from_utf8(section)?;
    if text.matches("<hp:edit ").count() != 1 {
        return Err("native control selection ambiguous".into());
    }
    Ok(text
        .replacen("<hp:edit ", "<hp:edit id=\"8112\" ", 1)
        .into_bytes())
}
fn run() -> Result<serde_json::Value, AnyError> {
    let section = load_section()?;
    let expected = expected_state(0, SECTION_SHA)?;
    let native =
        FormControlHwpxReader::read_section(&section, &expected, limits()?, native_limits()?);
    let error = native
        .err()
        .ok_or("v1 unexpectedly admitted missing native identity")?;
    if error != FormControlHwpxError::InvalidAttribute {
        return Err("unexpected native rejection boundary".into());
    }
    // Only a differential diagnostic in memory. Never persist this invented ID or claim target PASS.
    let diagnostic = diagnostic_identity_bytes(&section)?;
    let diagnostic_projection =
        FormControlHwpxReader::read_section(&diagnostic, &expected, limits()?, native_limits()?)
            .is_ok();
    let wrong_mapping = expected_state(999, &archive::sha256(b"deliberately-wrong-shape-binding"))?;
    let legacy_mapping_not_checked = FormControlHwpxReader::read_section(
        &diagnostic,
        &wrong_mapping,
        limits()?,
        native_limits()?,
    )
    .is_ok();
    if !diagnostic_projection || !legacy_mapping_not_checked {
        return Err("native compatibility regression changed".into());
    }
    if load_section()? != section {
        return Err("capture changed during diagnosis".into());
    }
    Ok(
        json!({"schema_version":"hwpx-agent.p09-native-form-compatibility-probe/v1","task":"P09-25",
        "state":"reproduced_native_profile_gap_non_green","capture_package_sha256":SHA,"capture_section_sha256":SECTION_SHA,
        "legacy_actual_capture_error":error.code(),"diagnostic_added_identity_not_native_evidence":true,
        "diagnostic_identity_only_projection_admitted":diagnostic_projection,
        "diagnostic_wrong_anchor_and_shape_binding_admitted":legacy_mapping_not_checked,
        "source_capture_preserved":true,"native_session_started":false,"actual_form_target_pass":false,
        "product_routing_qualified":false,"green_rows":0,"p09_complete":false,"product_complete":false,
        "raw_document_text_present":false,"absolute_private_paths_present":false}),
    )
}
fn main() -> Result<(), AnyError> {
    println!("{}", run()?);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn actual_saved_control_missing_id_remains_rejected() -> Result<(), AnyError> {
        let section = load_section()?;
        assert_eq!(
            FormControlHwpxReader::read_section(
                &section,
                &expected_state(0, SECTION_SHA)?,
                limits()?,
                native_limits()?
            )
            .map(|_| ()),
            Err(FormControlHwpxError::InvalidAttribute)
        );
        Ok(())
    }
    #[test]
    fn identity_diagnostic_is_memory_only_and_exactly_reversible() -> Result<(), AnyError> {
        let section = load_section()?;
        let diagnostic = diagnostic_identity_bytes(&section)?;
        let restored = std::str::from_utf8(&diagnostic)?
            .replacen("<hp:edit id=\"8112\" ", "<hp:edit ", 1)
            .into_bytes();
        assert_eq!(restored, section);
        assert_eq!(load_section()?, section);
        Ok(())
    }
    #[test]
    fn complete_regression_never_promotes_diagnostic_to_native_success() -> Result<(), AnyError> {
        let value = run()?;
        assert_eq!(
            value["diagnostic_wrong_anchor_and_shape_binding_admitted"],
            true
        );
        assert_eq!(value["actual_form_target_pass"], false);
        assert_eq!(value["p09_complete"], false);
        assert_eq!(value["native_session_started"], false);
        Ok(())
    }
}
