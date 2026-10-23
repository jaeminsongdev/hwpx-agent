use domain_ir::{form_input::*, *};
use hwpx_agent_cli::form_value_preparation::*;
use hwpx_package::{native_form_value_output::*, *};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{error::Error, fs, io::Cursor, path::Path};
type TestResult = Result<(), Box<dyn Error>>;
const CAPTURE: &str = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx";
const CAPTURE_SHA: &str = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7";

struct Fixture {
    source: Vec<u8>,
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
}
impl Fixture {
    fn context(&self) -> Result<FormValueContext<'_>, FormValuePreparationError> {
        FormValueContext::bind(
            &self.source,
            &self.map,
            &self.policies,
            FormValuePreparationLimits::bounded_default()?,
        )
    }
    fn request(&self, value: &str) -> Result<(Value, FormInputAccessPolicy), Box<dyn Error>> {
        let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
        let observed = NativeFormValueReader::read(
            &self.source,
            &self.map,
            &self.policies,
            limits,
            NativeFormPackageLimits::default(),
        )?;
        let draft: FormDocumentStateDraft =
            serde_json::from_slice(&observed.state().canonical_json(limits)?)?;
        let access = FormInputAccessPolicy {
            document_protection_sha256: draft.document_protection_sha256,
            input_allowed: true,
        };
        let req = FormInputRequestDraft {
            schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("product-form-request")?,
            expected_source_state_sha256: observed.state().canonical_sha256(limits)?,
            expected_document_flow_sha256: observed.native_v1().document_flow_sha256().into(),
            access: access.clone(),
            operation: FormInputOperation::SetValues {
                assignments: vec![FormInputAssignment {
                    target: self.policies[0].identity.clone(),
                    value: FormInputValue::Text {
                        value: value.into(),
                    },
                }],
            },
        };
        Ok((serde_json::to_value(req)?, access))
    }
}
fn fixture() -> Result<Fixture, Box<dyn Error>> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let path = root.join(CAPTURE);
    for ancestor in path.ancestors() {
        let m = fs::symlink_metadata(ancestor)?;
        if m.file_type().is_symlink() {
            return Err("fixture link".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("fixture reparse".into());
            }
        }
    }
    if fs::metadata(&path)?.len() != 14_556 {
        return Err("fixture size".into());
    }
    let source = fs::read(&path)?;
    if source.len() != 14_556 || hex::encode(Sha256::digest(&source)) != CAPTURE_SHA {
        return Err("fixture digest".into());
    }
    let mut zip = BoundedZipReader::open(Cursor::new(&source), PackageLimits::default())?;
    let entry = zip
        .entries()
        .iter()
        .find(|p| p.path.as_str() == "Contents/section0.xml")
        .ok_or("section")?
        .index;
    let section = zip.read_entry(entry)?;
    let xml = PreservingXmlDocument::parse(&section)?;
    let paragraphs = xml
        .elements()
        .iter()
        .filter(|e| {
            e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                && e.name().local_name() == "p"
        })
        .count();
    let map = NativeFormPackageMap {
        sections: vec![NativeFormPackageSectionMap {
            part: "Contents/section0.xml".into(),
            map: NativeFormHwpxMap {
                paragraph_ids: (0..paragraphs)
                    .map(|i| LogicalId::parse(format!("actual-p-{i}")))
                    .collect::<Result<_, _>>()?,
                component_controls: vec![FormControlIdentity {
                    logical_control_id: LogicalId::parse("actual-input-component")?,
                    native_object_id: 90001,
                }],
            },
        }],
    };
    let observed =
        NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
    let c = observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .next()
        .ok_or("control")?;
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
    } = &c.payload
    else {
        return Err("text".into());
    };
    let policies = vec![NativeFormPackagePolicy {
        identity: c.component_identity.clone(),
        payload: FormControlPayload::Text {
            value: value.clone(),
            default_value: "caller-default".into(),
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
    }];
    Ok(Fixture {
        source,
        map,
        policies,
    })
}

#[test]
fn actual_product_preparation_runs_public_sdk_and_rereads_complete_candidate_but_denies_route()
-> TestResult {
    let f = fixture()?;
    let original = f.source.clone();
    let ctx = f.context()?;
    let (request, access) = f.request("P40 값 & <한글> \" ' 🚀")?;
    let bytes = serde_json::to_vec(&request)?;
    let p = FormValuePreparation::prepare_json(&ctx, &bytes, &access)?;
    assert_eq!(p.verify(&ctx, &access)?, *p.receipt());
    assert_eq!(p.receipt().component.changed_controls, 1);
    assert_eq!(
        p.receipt().component.output_package_sha256,
        hex::encode(Sha256::digest(p.candidate_bytes()))
    );
    assert_eq!(
        p.receipt().component.output_package_sha256,
        "bb0a1b43fa83d6f88dbabdb63324fb7cd95546d982562d73ce76d5b54c2dca4f"
    );
    assert_eq!(p.receipt().qualification,FormValuePreparationQualification::ProductPreparationOnlyRoutePublicationNativeAndGateUnqualified);
    assert_eq!(
        p.require_current_product_route(&ctx, &access),
        Err(FormValuePreparationError::RouteUnqualified)
    );
    let out = NativeFormValueReader::read(
        p.candidate_bytes(),
        &f.map,
        &[NativeFormPackagePolicy {
            identity: f.policies[0].identity.clone(),
            payload: match &f.policies[0].payload {
                FormControlPayload::Text { .. } => {
                    let mut payload = f.policies[0].payload.clone();
                    if let FormControlPayload::Text { value, .. } = &mut payload {
                        *value = "P40 값 & <한글> \" ' 🚀".into();
                    }
                    payload
                }
                _ => return Err("text".into()),
            },
        }],
        FormControlLimits::new(FormControlLimitConfig::default())?,
        NativeFormPackageLimits::default(),
    )?;
    assert_ne!(
        out.state()
            .canonical_sha256(FormControlLimits::new(FormControlLimitConfig::default())?)?,
        request["expected_source_state_sha256"]
            .as_str()
            .ok_or("source")?
    );
    assert!(f.source == original, "source bytes changed");
    Ok(())
}
#[test]
fn exact_retry_is_deterministic_and_canonical_request_is_distinct_from_raw_json() -> TestResult {
    let f = fixture()?;
    let ctx = f.context()?;
    let (request, access) = f.request("retry")?;
    let raw = serde_json::to_vec(&request)?;
    let a = FormValuePreparation::prepare_json(&ctx, &raw, &access)?;
    let b = FormValuePreparation::prepare_json(&ctx, &raw, &access)?;
    assert!(
        a.candidate_bytes() == b.candidate_bytes(),
        "retry bytes differ"
    );
    assert_eq!(a.receipt(), b.receipt());
    let spaced = serde_json::to_vec_pretty(&request)?;
    let c = FormValuePreparation::prepare_json(&ctx, &spaced, &access)?;
    assert!(
        a.candidate_bytes() == c.candidate_bytes(),
        "canonical bytes differ"
    );
    assert_eq!(
        a.receipt().canonical_request_sha256,
        c.receipt().canonical_request_sha256
    );
    assert_ne!(
        a.receipt().raw_request_sha256,
        c.receipt().raw_request_sha256
    );
    Ok(())
}
#[test]
fn fresh_access_revocation_and_digest_drift_reject_preparation_verification_and_route() -> TestResult
{
    let f = fixture()?;
    let ctx = f.context()?;
    let (request, access) = f.request("access")?;
    let raw = serde_json::to_vec(&request)?;
    let prepared = FormValuePreparation::prepare_json(&ctx, &raw, &access)?;
    for altered in [
        FormInputAccessPolicy {
            input_allowed: false,
            ..access.clone()
        },
        FormInputAccessPolicy {
            document_protection_sha256: "0".repeat(64),
            ..access.clone()
        },
    ] {
        assert!(prepared.verify(&ctx, &altered).is_err());
        assert!(
            prepared
                .require_current_product_route(&ctx, &altered)
                .is_err()
        );
        assert!(FormValuePreparation::prepare_json(&ctx, &raw, &altered).is_err());
    }
    let changed = FormInputAccessPolicy {
        document_protection_sha256: "0".repeat(64),
        input_allowed: true,
    };
    assert!(prepared.verify(&ctx, &changed).is_err());
    assert!(
        prepared
            .require_current_product_route(&ctx, &changed)
            .is_err()
    );
    Ok(())
}
#[test]
fn changed_caller_policy_map_source_and_limits_are_not_substituted_for_provider_snapshot()
-> TestResult {
    let f = fixture()?;
    let ctx = f.context()?;
    let (request, access) = f.request("fresh")?;
    let prepared =
        FormValuePreparation::prepare_json(&ctx, &serde_json::to_vec(&request)?, &access)?;
    let mut policies = f.policies.clone();
    if let FormControlPayload::Text { default_value, .. } = &mut policies[0].payload {
        *default_value = "changed-default".into();
    }
    let fresh = FormValueContext::bind(
        &f.source,
        &f.map,
        &policies,
        FormValuePreparationLimits::bounded_default()?,
    )?;
    assert_eq!(
        prepared.verify(&fresh, &access),
        Err(FormValuePreparationError::Drift)
    );
    let mut map = f.map.clone();
    map.sections[0].map.paragraph_ids[0] = LogicalId::parse("changed-paragraph")?;
    let fresh = FormValueContext::bind(
        &f.source,
        &map,
        &f.policies,
        FormValuePreparationLimits::bounded_default()?,
    )?;
    assert_eq!(
        prepared.verify(&fresh, &access),
        Err(FormValuePreparationError::Drift)
    );
    let limited = FormValuePreparationLimits::new(
        FormControlLimits::new(FormControlLimitConfig::default())?,
        NativeFormPackageLimits::default(),
        NativeFormValueLimits::new(1024, 1024, 2048)?,
    )?;
    let fresh = FormValueContext::bind(&f.source, &f.map, &f.policies, limited)?;
    assert_eq!(
        prepared.verify(&fresh, &access),
        Err(FormValuePreparationError::Drift)
    );
    let mut source = f.source.clone();
    source[0] ^= 1;
    assert!(
        FormValueContext::bind(
            &source,
            &f.map,
            &f.policies,
            FormValuePreparationLimits::bounded_default()?
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn malformed_duplicate_unknown_raw_path_coercion_and_stale_request_fail_closed() -> TestResult {
    let f = fixture()?;
    let ctx = f.context()?;
    let (request, access) = f.request("json")?;
    let good = serde_json::to_string(&request)?;
    for bad in &[
        format!("{{\"request_id\":\"duplicate\",{}", &good[1..]),
        format!("{{\"raw_xml\":\"<hp:edit/>\",{}", &good[1..]),
        format!("{{\"output_path\":\"../outside\",{}", &good[1..]),
        format!("{good}{{}}"),
    ] {
        assert_eq!(
            FormValuePreparation::prepare_json(&ctx, bad.as_bytes(), &access).err(),
            Some(FormValuePreparationError::Request)
        );
    }
    for (key, value) in [
        ("expected_source_state_sha256", json!("0".repeat(64))),
        ("expected_document_flow_sha256", json!("0".repeat(64))),
        (
            "access",
            json!({"input_allowed":"true","document_protection_sha256":access.document_protection_sha256}),
        ),
    ] {
        let mut bad = request.clone();
        bad[key] = value;
        assert!(
            FormValuePreparation::prepare_json(&ctx, &serde_json::to_vec(&bad)?, &access).is_err()
        );
    }
    assert!(
        FormValuePreparation::prepare_json(&ctx, &vec![b' '; 1024 * 1024 + 1], &access).is_err()
    );
    Ok(())
}
#[test]
fn request_limits_debug_and_public_receipts_never_leak_values_or_paths() -> TestResult {
    let f = fixture()?;
    let ctx = f.context()?;
    let (request, access) = f.request("product-private-value")?;
    let p = FormValuePreparation::prepare_json(&ctx, &serde_json::to_vec(&request)?, &access)?;
    let public = serde_json::to_string(p.receipt())?;
    let debug = format!("{ctx:?} {p:?}");
    for value in [
        "product-private-value",
        "caller-default",
        CAPTURE,
        "product-form-request",
    ] {
        assert!(!public.contains(value));
        assert!(!debug.contains(value));
    }
    let config = FormControlLimitConfig {
        output_bytes: 2 * 1024 * 1024,
        ..FormControlLimitConfig::default()
    };
    assert_eq!(
        FormValuePreparationLimits::new(
            FormControlLimits::new(config)?,
            NativeFormPackageLimits::default(),
            NativeFormValueLimits::default()
        ),
        Err(FormValuePreparationError::Limit)
    );
    Ok(())
}
#[test]
fn caller_default_reset_is_real_output_not_native_default_attestation() -> TestResult {
    let f = fixture()?;
    let ctx = f.context()?;
    let (mut request, access) = f.request("ignored")?;
    request["operation"] = serde_json::to_value(FormInputOperation::ResetDefaults {
        targets: vec![f.policies[0].identity.clone()],
    })?;
    let p = FormValuePreparation::prepare_json(&ctx, &serde_json::to_vec(&request)?, &access)?;
    assert_eq!(p.receipt().component.changed_controls, 1);
    assert_eq!(
        p.require_current_product_route(&ctx, &access),
        Err(FormValuePreparationError::RouteUnqualified)
    );
    Ok(())
}
#[test]
fn no_op_wrong_kind_and_unqualified_date_do_not_return_partial_preparation() -> TestResult {
    let f = fixture()?;
    let ctx = f.context()?;
    let (mut request, access) = f.request("wrong")?;
    for value in [
        FormInputValue::Text {
            value: match &f.policies[0].payload {
                FormControlPayload::Text { value, .. } => value.clone(),
                _ => return Err("text".into()),
            },
        },
        FormInputValue::Checkbox {
            value: FormButtonValue::Checked,
        },
        FormInputValue::Date {
            value: Some("2026-10-03".into()),
        },
    ] {
        request["operation"] = serde_json::to_value(FormInputOperation::SetValues {
            assignments: vec![FormInputAssignment {
                target: f.policies[0].identity.clone(),
                value,
            }],
        })?;
        assert!(
            FormValuePreparation::prepare_json(&ctx, &serde_json::to_vec(&request)?, &access)
                .is_err()
        );
    }
    Ok(())
}

fn checked_fixture(name: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let path = root.join(name);
    for ancestor in path.ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        if metadata.file_type().is_symlink() {
            return Err("fixture link".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("fixture reparse".into());
            }
        }
    }
    if !fs::metadata(&path)?.is_file() || fs::metadata(&path)?.len() > 1024 * 1024 {
        return Err("fixture bound".into());
    }
    Ok(fs::read(path)?)
}
fn matrix(label: &str) -> Result<(Fixture, Vec<u8>), Box<dyn Error>> {
    let manifest = checked_fixture("fixture-manifest.json")?;
    if hex::encode(Sha256::digest(&manifest))
        != "8208bff3f87a4e56ec68caecaf41b00c3fdccc5b3f083289f3c13ccede19466e"
    {
        return Err("manifest identity".into());
    }
    let manifest: Value = serde_json::from_slice(&manifest)?;
    let row = manifest["cases"]
        .as_array()
        .ok_or("cases")?
        .iter()
        .find(|r| r["case"] == label)
        .ok_or("case")?;
    let source = checked_fixture(row["source"]["path"].as_str().ok_or("source")?)?;
    let output = checked_fixture(row["output"]["path"].as_str().ok_or("output")?)?;
    for (value, key) in [(&source, "source"), (&output, "output")] {
        if hex::encode(Sha256::digest(value)) != row[key]["sha256"].as_str().ok_or("sha")?
            || u64::try_from(value.len())? != row[key]["bytes"].as_u64().ok_or("bytes")?
        {
            return Err("fixture identity".into());
        }
    }
    let map = NativeFormPackageMap {
        sections: (0..2)
            .map(|section| -> Result<_, Box<dyn Error>> {
                Ok(NativeFormPackageSectionMap {
                    part: format!("Contents/section{section}.xml"),
                    map: NativeFormHwpxMap {
                        paragraph_ids: (0..2)
                            .map(|i| LogicalId::parse(format!("p40-section{section}-p{i}")))
                            .collect::<Result<_, _>>()?,
                        component_controls: (if section == 0 {
                            vec![0, 1, 2, 3, 4]
                        } else {
                            vec![5]
                        })
                        .into_iter()
                        .map(|i| -> Result<_, Box<dyn Error>> {
                            Ok(FormControlIdentity {
                                logical_control_id: LogicalId::parse(format!("p40-control{i}"))?,
                                native_object_id: 90001 + i,
                            })
                        })
                        .collect::<Result<_, _>>()?,
                    },
                })
            })
            .collect::<Result<_, _>>()?,
    };
    let native = NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
    let policies = native
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(matrix_policy)
        .collect::<Result<Vec<_>, _>>()?;
    Ok((
        Fixture {
            source,
            map,
            policies,
        },
        output,
    ))
}
fn text_payload(c: &NativeFormControlObservation) -> Result<FormControlPayload, Box<dyn Error>> {
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
    } = &c.payload
    else {
        return Err("text".into());
    };
    Ok(FormControlPayload::Text {
        value: value.clone(),
        default_value: "caller-default".into(),
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
    })
}
fn matrix_policy(
    c: &NativeFormControlObservation,
) -> Result<NativeFormPackagePolicy, Box<dyn Error>> {
    let selection_validation = || FormSelectionValidation {
        required: false,
        external_validator_sha256: None,
    };
    let payload = match &c.payload {
        NativeFormObservedPayload::Text { .. } => text_payload(c)?,
        NativeFormObservedPayload::Button {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
        } if c.tag == NativeFormTag::RadioBtn => FormControlPayload::Radio {
            caption: caption.clone(),
            value: *value,
            default_value: if c.component_identity.native_object_id == 90003 {
                FormButtonValue::Checked
            } else {
                FormButtonValue::Unchecked
            },
            radio_group_name: radio_group_name.clone().ok_or("radio")?,
            group_required: true,
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
            default_value: FormButtonValue::Unchecked,
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
            default_selected_value: Some("b".into()),
            validation: selection_validation(),
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
            default_selected_value: Some("a".into()),
            validation: selection_validation(),
            item_height_hwp_units: *item_height_hwp_units,
            top_index: *top_index,
        },
    };
    Ok(NativeFormPackagePolicy {
        identity: c.component_identity.clone(),
        payload,
    })
}
fn product_request(
    f: &Fixture,
    operation: FormInputOperation,
) -> Result<(Vec<u8>, FormInputAccessPolicy), Box<dyn Error>> {
    let (mut value, access) = f.request("temporary")?;
    value["operation"] = serde_json::to_value(operation)?;
    Ok((serde_json::to_vec(&value)?, access))
}
#[test]
fn all_five_types_required_radio_empty_text_defaults_and_clear_match_independent_predecessor_bytes()
-> TestResult {
    for label in [
        "five-kinds",
        "empty-text",
        "reset-defaults",
        "clear-selections",
    ] {
        let (f, expected) = matrix(label)?;
        let ctx = f.context()?;
        let assignment = |index: usize, value| FormInputAssignment {
            target: f.policies[index].identity.clone(),
            value,
        };
        let operation = match label {
            "five-kinds" => FormInputOperation::SetValues {
                assignments: vec![
                    assignment(
                        0,
                        FormInputValue::Text {
                            value: "新 & <\"'> 🚀\r\n\tline".into(),
                        },
                    ),
                    assignment(
                        1,
                        FormInputValue::Checkbox {
                            value: FormButtonValue::Indeterminate,
                        },
                    ),
                    assignment(
                        2,
                        FormInputValue::Radio {
                            value: FormButtonValue::Unchecked,
                        },
                    ),
                    assignment(
                        3,
                        FormInputValue::Combo {
                            selected_value: Some("b".into()),
                        },
                    ),
                    assignment(
                        4,
                        FormInputValue::List {
                            selected_value: Some("a".into()),
                        },
                    ),
                    assignment(
                        5,
                        FormInputValue::Radio {
                            value: FormButtonValue::Checked,
                        },
                    ),
                ],
            },
            "empty-text" => FormInputOperation::SetValues {
                assignments: vec![assignment(
                    0,
                    FormInputValue::Text {
                        value: "value & 🚀".into(),
                    },
                )],
            },
            "reset-defaults" => FormInputOperation::ResetDefaults {
                targets: f.policies.iter().map(|p| p.identity.clone()).collect(),
            },
            _ => FormInputOperation::SetValues {
                assignments: vec![
                    assignment(
                        3,
                        FormInputValue::Combo {
                            selected_value: None,
                        },
                    ),
                    assignment(
                        4,
                        FormInputValue::List {
                            selected_value: None,
                        },
                    ),
                ],
            },
        };
        let (request, access) = product_request(&f, operation)?;
        let prepared = FormValuePreparation::prepare_json(&ctx, &request, &access)?;
        assert!(
            prepared.candidate_bytes() == expected,
            "candidate bytes differ: {label}"
        );
        assert_eq!(prepared.verify(&ctx, &access)?, *prepared.receipt());
        assert_eq!(
            prepared.require_current_product_route(&ctx, &access),
            Err(FormValuePreparationError::RouteUnqualified)
        );
    }
    Ok(())
}
#[test]
fn partial_radio_and_external_validator_never_count_as_product_preparation() -> TestResult {
    let (f, _) = matrix("five-kinds")?;
    let ctx = f.context()?;
    let (request, access) = product_request(
        &f,
        FormInputOperation::SetValues {
            assignments: vec![FormInputAssignment {
                target: f.policies[2].identity.clone(),
                value: FormInputValue::Radio {
                    value: FormButtonValue::Unchecked,
                },
            }],
        },
    )?;
    assert!(FormValuePreparation::prepare_json(&ctx, &request, &access).is_err());
    let mut policies = f.policies.clone();
    if let FormControlPayload::Text { validation, .. } = &mut policies[0].payload {
        validation.external_validator_sha256 = Some("1".repeat(64));
    }
    let changed = Fixture {
        source: f.source.clone(),
        map: f.map.clone(),
        policies,
    };
    let ctx = changed.context()?;
    let (request, access) = changed.request("external")?;
    assert!(
        FormValuePreparation::prepare_json(&ctx, &serde_json::to_vec(&request)?, &access).is_err()
    );
    Ok(())
}
