//! Actual existing native capture -> real public reader -> new typed input.
//! No native launch/output; old lowering rejection is retained, not bypassed.
use domain_ir::*;
#[path = "../../domain-ir/src/form_input.rs"]
mod form_input;
use form_input::*;
use hwpx_package::*;
use sha2::{Digest as _, Sha256};
use std::{error::Error, fs, io::Cursor, path::Path};
type AnyError = Box<dyn Error>;
const CAPTURE: &str = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx";
const CAPTURE_SHA: &str = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7";
const HP: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
fn hex(raw: &[u8]) -> String {
    hex::encode(raw)
}
fn capture() -> Result<Vec<u8>, AnyError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(CAPTURE);
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
        return Err("capture size rejected".into());
    }
    let raw = fs::read(path)?;
    if raw.len() != 14_556 || hex(&Sha256::digest(&raw)) != CAPTURE_SHA {
        return Err("capture digest rejected".into());
    }
    Ok(raw)
}
fn policy(observed: &NativeFormControlObservation) -> Result<NativeFormPackagePolicy, AnyError> {
    let NativeFormObservedPayload::Text {
        value,
        multi_line,
        password_character,
        native_max_length,
        scroll_bars,
        tab_key_behavior,
        number_only,
        read_only,
        alignment,
    } = &observed.payload
    else {
        return Err("capture kind rejected".into());
    };
    Ok(NativeFormPackagePolicy {
        identity: observed.component_identity.clone(),
        payload: FormControlPayload::Text {
            value: value.clone(),
            default_value: value.clone(),
            validation: FormTextValidation {
                required: false,
                minimum_characters: 0,
                maximum_characters: None,
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
    })
}

fn actual_map(source: &[u8]) -> Result<NativeFormPackageMap, AnyError> {
    let mut zip = BoundedZipReader::open(Cursor::new(source), PackageLimits::default())?;
    let section_index = zip
        .entries()
        .iter()
        .find(|e| e.path.as_str() == "Contents/section0.xml")
        .ok_or("section missing")?
        .index;
    let section = zip.read_entry(section_index)?;
    let xml = PreservingXmlDocument::parse(&section)?;
    let paragraphs = xml
        .elements()
        .iter()
        .filter(|e| e.name().namespace() == Some(HP) && e.name().local_name() == "p")
        .count();
    let identity = FormControlIdentity {
        logical_control_id: LogicalId::parse("actual-input-component")?,
        native_object_id: 90_001,
    };
    Ok(NativeFormPackageMap {
        sections: vec![NativeFormPackageSectionMap {
            part: "Contents/section0.xml".into(),
            map: NativeFormHwpxMap {
                paragraph_ids: (0..paragraphs)
                    .map(|i| LogicalId::parse(format!("actual-p-{i}")))
                    .collect::<Result<_, _>>()?,
                component_controls: vec![identity.clone()],
            },
        }],
    })
}

fn retain_old_failure(
    source: &[u8],
    map: &NativeFormPackageMap,
    policies: &[NativeFormPackagePolicy],
    state: &FormDocumentState,
    changed: &FormControlState,
    flow: &str,
    limits: FormControlLimits,
) -> Result<(), AnyError> {
    let old_request = FormControlRequest::from_draft(
        FormControlRequestDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("old-input-diagnostic")?,
            expected_source_state_sha256: state.canonical_sha256(limits)?,
            expected_document_flow_sha256: flow.into(),
            target_document_flow_sha256: flow.into(),
            operation: FormControlOperation::ReplaceProperties {
                target: changed.identity.clone(),
                common: changed.common.clone(),
                payload: changed.payload.clone(),
            },
        },
        state,
        flow,
        limits,
    )?;
    let old_plan = FormControlBuilder::plan(state, &old_request, flow, limits)?;
    assert!(matches!(
        NativeFormPackageOutputPlan::bind(
            source,
            map,
            policies,
            &old_plan,
            limits,
            NativeFormPackageLimits::default()
        ),
        Err(NativeFormPackageOutputError::NonRepresentable)
    ));
    Ok(())
}

#[test]
fn actual_capture_input_binds_complete_public_readback_and_keeps_old_lowerer_failure()
-> Result<(), AnyError> {
    let source = capture()?;
    let map = actual_map(&source)?;
    let identity = map.sections[0].map.component_controls[0].clone();
    let observed =
        NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
    let control = observed
        .sections()
        .next()
        .ok_or("control missing")?
        .controls()
        .first()
        .ok_or("control missing")?;
    assert_eq!(control.native_identity, NativeFormObservedIdentity::Missing);
    let policies = vec![policy(control)?];
    let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
    let state = observed.bind_policies(&policies, limits)?;
    let typed: FormDocumentStateDraft = serde_json::from_slice(&state.canonical_json(limits)?)?;
    let access = FormInputAccessPolicy {
        document_protection_sha256: typed.document_protection_sha256,
        input_allowed: true,
    };
    let request = FormInputRequest::from_draft(
        FormInputRequestDraft {
            schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("actual-input-request")?,
            expected_source_state_sha256: state.canonical_sha256(limits)?,
            expected_document_flow_sha256: observed.document_flow_sha256().into(),
            access: access.clone(),
            operation: FormInputOperation::SetValues {
                assignments: vec![FormInputAssignment {
                    target: identity.clone(),
                    value: FormInputValue::Text {
                        value: "P09 실제 입력".into(),
                    },
                }],
            },
        },
        &state,
        observed.document_flow_sha256(),
        limits,
    )?;
    let plan = FormInputBuilder::plan(&state, &request, observed.document_flow_sha256(), limits)?;
    assert_eq!(
        FormInputRequest::from_json(
            &request.canonical_json(limits)?,
            &state,
            observed.document_flow_sha256(),
            limits
        )?,
        request
    );
    assert_eq!(plan.source_state(), &state);
    let result = FormInputBuilder::build(
        &plan,
        &state,
        observed.document_flow_sha256(),
        &access,
        limits,
    )?;
    assert_eq!(plan.target_state(), &result.state);
    assert_eq!(plan.plan_sha256(), result.receipt.plan_sha256);
    assert_eq!(result.receipt.changed_controls, 1);
    let changed = &result.state.controls()[0];
    let before = &state.controls()[0];
    let mut preserved = changed.clone();
    preserved.payload = before.payload.clone();
    assert_eq!(&preserved, before);
    let mut before_state: serde_json::Value =
        serde_json::from_slice(&state.canonical_json(limits)?)?;
    let mut after_state: serde_json::Value =
        serde_json::from_slice(&result.state.canonical_json(limits)?)?;
    before_state["controls"][0]["payload"]["value"] = serde_json::Value::Null;
    after_state["controls"][0]["payload"]["value"] = serde_json::Value::Null;
    assert_eq!(before_state, after_state);
    // Exact old API rejection demonstrates the remaining HWPX value/opaque
    // binding implementation gap; no silent state rebinding or synthetic ID.
    retain_old_failure(
        &source,
        &map,
        &policies,
        &state,
        changed,
        observed.document_flow_sha256(),
        limits,
    )?;
    assert_eq!(capture()?, source);
    println!(
        "P09_37_ACTUAL_INPUT_PROBE={}",
        serde_json::json!({
            "schema_version":"hwpx-agent.p09-37-actual-capture-input-component/v1",
            "source_package_sha256":CAPTURE_SHA,"source_state_sha256":result.receipt.source_state_sha256,
            "target_state_sha256":result.receipt.target_state_sha256,"document_flow_sha256":result.receipt.document_flow_sha256,
            "plan_sha256":result.receipt.plan_sha256,"controls":1,"changed_controls":1,
            "requested_value_sha256":hex(&Sha256::digest("P09 실제 입력".as_bytes())),
            "every_other_complete_state_field_exact":true,"observed_native_identity_missing":true,
            "caller_policy_only":true,"old_native_output":"nonrepresentable",
            "native_protection_qualified":false,"native_output_qualified":false,"native_session_started":false,
            "raw_document_text_present":false,"absolute_private_paths_present":false,"green_rows":0,"p09_complete":false
        })
    );
    Ok(())
}
