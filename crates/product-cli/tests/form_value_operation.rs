use domain_ir::{form_input::*, *};
use hwpx_agent_cli::form_value_preparation::*;
use hwpx_package::{native_form_value_output::*, *};
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use std::{error::Error, fs, io::Cursor, path::Path};
type TestResult = Result<(), Box<dyn Error>>;
#[path = "form_value_operation/full_document.rs"]
mod full_document;
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

use hwpx_agent_cli::form_value_operation::*;

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
fn identity(plan: &str, revision: &str) -> Result<FormOperationIdentity, Box<dyn Error>> {
    Ok(FormOperationIdentity::new(
        DocumentId::parse("actual-form-document")?,
        RevisionId::parse(revision)?,
        PlanId::parse(plan)?,
    )?)
}
fn operation_context(f: &Fixture) -> Result<FormOperationContext<'_>, Box<dyn Error>> {
    Ok(FormOperationContext::bind(&f.source, &f.map, &f.policies)?)
}
fn matrix_request(
    label: &str,
    f: &Fixture,
) -> Result<(Vec<u8>, FormInputAccessPolicy), Box<dyn Error>> {
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
    let (request, access) = product_request(f, operation)?;

    Ok((request, access))
}
fn arg_text<'a>(op: &'a CompiledOperation, key: &str) -> Result<&'a str, Box<dyn Error>> {
    match op.arguments().get(key).ok_or("argument")?.value() {
        CanonicalArgumentValue::Text(s) => Ok(s),
        _ => Err("argument kind".into()),
    }
}
#[test]
fn actual_captured_control_compiles_real_form_selector_and_matches_whole_product_candidate()
-> TestResult {
    let f = fixture()?;
    let (request, access) = f.request("P40 값 & <한글> \" ' 🚀")?;
    let request = serde_json::to_vec(&request)?;
    let ctx = operation_context(&f)?;
    let prepared = FormOperationPreparation::prepare_json(
        &ctx,
        identity("form-plan", "revision-1")?,
        &request,
        &access,
    )?;
    let old = FormValuePreparation::prepare_json(&f.context()?, &request, &access)?;
    assert!(prepared.candidate_bytes() == old.candidate_bytes());
    assert_eq!(prepared.receipt().compiled_operations, 1);
    assert_eq!(
        prepared.compiled_plan().operations()[0]
            .target()
            .node_kind(),
        NodeKind::FormControl
    );
    assert_eq!(
        prepared.compiled_plan().operations()[0].target().node_id(),
        &f.policies[0].identity.logical_control_id
    );
    assert_eq!(prepared.verify(&ctx, &access)?, *prepared.receipt());
    assert_eq!(
        prepared.require_current_product_route(&ctx, &access),
        Err(FormOperationError::RouteUnqualified)
    );
    let graph = prepared.selection_projection();
    assert_eq!(
        prepared.compiled_plan().base_graph_sha256(),
        graph.canonical_sha256()?
    );
    assert_eq!(graph.sections()[0].body.children.len(), 1);
    assert!(matches!(
        graph.sections()[0].body.children[0],
        Node::FormControl(_)
    ));
    let bytes = prepared.compiled_plan().canonical_json()?;
    let restored =
        CompiledOperationPlan::from_canonical_json(&bytes, OperationPlanLimits::default())?;
    assert_eq!(restored, *prepared.compiled_plan());
    let value: Value = serde_json::from_slice(&bytes)?;
    assert_eq!(value["failure_policy"], "atomic");
    Ok(())
}
#[test]
fn all_five_kinds_required_radio_defaults_empty_and_clear_keep_complete_output_and_atomic_group()
-> TestResult {
    for (label, count) in [
        ("five-kinds", 6),
        ("empty-text", 1),
        ("reset-defaults", 4),
        ("clear-selections", 2),
    ] {
        let (f, expected) = matrix(label)?;
        let (request, access) = matrix_request(label, &f)?;
        let ctx = operation_context(&f)?;
        let prepared = FormOperationPreparation::prepare_json(
            &ctx,
            identity("form-plan", "revision-1")?,
            &request,
            &access,
        )?;
        assert!(
            prepared.candidate_bytes() == expected,
            "whole candidate mismatch"
        );
        assert_eq!(prepared.receipt().compiled_operations, count);
        assert_eq!(prepared.receipt().changed_controls, count);
        assert_eq!(prepared.receipt().source_inventory_controls, 6);
        for operation in prepared.compiled_plan().operations() {
            assert_eq!(operation.target().node_kind(), NodeKind::FormControl);
            assert_eq!(
                arg_text(operation, "atomic_input_plan_sha256")?,
                prepared.receipt().typed_input_plan_sha256
            );
            assert_eq!(
                arg_text(operation, "native_package_plan_sha256")?,
                prepared.receipt().preparation.component.package_plan_sha256
            );
            assert_eq!(
                arg_text(operation, "provider_context_sha256")?,
                prepared.receipt().preparation.provider_context_sha256
            );
        }
        assert_eq!(prepared.verify(&ctx, &access)?, *prepared.receipt());
        assert_eq!(
            prepared.require_current_product_route(&ctx, &access),
            Err(FormOperationError::RouteUnqualified)
        );
    }
    Ok(())
}
#[test]
fn every_inventory_node_and_compiled_target_carries_complete_original_or_target_control_state()
-> TestResult {
    let (f, _) = matrix("five-kinds")?;
    let (request, access) = matrix_request("five-kinds", &f)?;
    let ctx = operation_context(&f)?;
    let prepared = FormOperationPreparation::prepare_json(
        &ctx,
        identity("form-plan", "revision-1")?,
        &request,
        &access,
    )?;
    let limits = FormControlLimits::new(FormControlLimitConfig::default())?;
    let read = NativeFormValueReader::read(
        &f.source,
        &f.map,
        &f.policies,
        limits,
        NativeFormPackageLimits::default(),
    )?;
    let typed_request = FormInputRequest::from_json(
        &request,
        read.state(),
        read.native_v1().document_flow_sha256(),
        limits,
    )?;
    let typed = FormInputBuilder::plan(
        read.state(),
        &typed_request,
        read.native_v1().document_flow_sha256(),
        limits,
    )?;
    let nodes = &prepared.selection_projection().sections()[0].body.children;
    for ((node, source), target) in nodes
        .iter()
        .zip(typed.source_state().controls())
        .zip(typed.target_state().controls())
    {
        let Node::FormControl(node) = node else {
            return Err("not form node".into());
        };
        assert_eq!(&node.common.node_id, &source.identity.logical_control_id);
        let encoded = node
            .properties
            .iter()
            .find(|(key, _)| *key == "complete_control_state_json")
            .ok_or("state property")?
            .1;
        let PropertyValue::Text(encoded) = encoded else {
            return Err("state property kind".into());
        };
        let restored: FormControlState = serde_json::from_str(encoded)?;
        assert!(restored == *source, "complete source state mismatch");
        let op = prepared
            .compiled_plan()
            .operations()
            .iter()
            .find(|o| o.target().node_id() == &source.identity.logical_control_id)
            .ok_or("missing changed control")?;
        let restored: FormControlState =
            serde_json::from_str(arg_text(op, "target_control_state_json")?)?;
        assert!(restored == *target, "complete target state mismatch");
        assert_eq!(op.capability_id().as_str(), source.payload.capability_id());
    }
    Ok(())
}
#[test]
fn exact_retry_and_json_formatting_retain_same_semantic_compiler_plan_not_publication_idempotency()
-> TestResult {
    let f = fixture()?;
    let ctx = operation_context(&f)?;
    let (request, access) = f.request("retry")?;
    let raw = serde_json::to_vec(&request)?;
    let pretty = serde_json::to_vec_pretty(&request)?;
    let prepare = |raw: &[u8]| {
        FormOperationPreparation::prepare_json(
            &ctx,
            identity("form-plan", "revision-1").map_err(|_| FormOperationError::Plan)?,
            raw,
            &access,
        )
    };
    let a = prepare(&raw)?;
    let b = prepare(&raw)?;
    let c = prepare(&pretty)?;
    assert_eq!(a.receipt(), b.receipt());
    assert_eq!(a.compiled_plan(), c.compiled_plan());
    assert!(a.candidate_bytes() == c.candidate_bytes());
    assert_ne!(
        a.receipt().preparation.raw_request_sha256,
        c.receipt().preparation.raw_request_sha256
    );
    Ok(())
}
#[test]
fn provider_revision_plan_and_document_identities_are_not_interchangeable() -> TestResult {
    let f = fixture()?;
    let ctx = operation_context(&f)?;
    let (request, access) = f.request("identity")?;
    let raw = serde_json::to_vec(&request)?;
    let a = FormOperationPreparation::prepare_json(
        &ctx,
        identity("plan-a", "revision-1")?,
        &raw,
        &access,
    )?;
    for id in [
        identity("plan-b", "revision-1")?,
        identity("plan-a", "revision-2")?,
        FormOperationIdentity::new(
            DocumentId::parse("other-document")?,
            RevisionId::parse("revision-1")?,
            PlanId::parse("plan-a")?,
        )?,
    ] {
        let b = FormOperationPreparation::prepare_json(&ctx, id, &raw, &access)?;
        assert_ne!(
            a.receipt().compiled_operation_plan_sha256,
            b.receipt().compiled_operation_plan_sha256
        );
        assert!(a.candidate_bytes() == b.candidate_bytes());
    }
    Ok(())
}
#[test]
fn fresh_access_revocation_or_protection_digest_change_blocks_verification_and_route_first()
-> TestResult {
    let f = fixture()?;
    let ctx = operation_context(&f)?;
    let (request, access) = f.request("access")?;
    let a = FormOperationPreparation::prepare_json(
        &ctx,
        identity("plan", "revision-1")?,
        &serde_json::to_vec(&request)?,
        &access,
    )?;
    let mut revoked = access.clone();
    revoked.input_allowed = false;
    let mut changed = access.clone();
    changed.document_protection_sha256 = "a".repeat(64);
    for current in [revoked, changed] {
        assert_eq!(a.verify(&ctx, &current), Err(FormOperationError::Drift));
        assert_eq!(
            a.require_current_product_route(&ctx, &current),
            Err(FormOperationError::Drift)
        );
    }
    Ok(())
}
#[test]
fn fresh_policy_map_and_source_drift_never_rebind_an_old_compiled_plan() -> TestResult {
    let f = fixture()?;
    let ctx = operation_context(&f)?;
    let (request, access) = f.request("context")?;
    let a = FormOperationPreparation::prepare_json(
        &ctx,
        identity("plan", "revision-1")?,
        &serde_json::to_vec(&request)?,
        &access,
    )?;
    let mut policies = f.policies.clone();
    if let FormControlPayload::Text { default_value, .. } = &mut policies[0].payload {
        *default_value = "changed".into();
    }
    let fresh = FormOperationContext::bind(&f.source, &f.map, &policies)?;
    assert_eq!(a.verify(&fresh, &access), Err(FormOperationError::Drift));
    let mut map = f.map.clone();
    map.sections[0].map.paragraph_ids[0] = LogicalId::parse("changed-paragraph")?;
    let fresh = FormOperationContext::bind(&f.source, &map, &f.policies)?;
    assert_eq!(a.verify(&fresh, &access), Err(FormOperationError::Drift));
    let mut source = f.source.clone();
    source[0] ^= 1;
    assert!(FormOperationContext::bind(&source, &f.map, &f.policies).is_err());
    Ok(())
}
#[test]
fn malformed_unknown_native_date_external_validator_and_partial_radio_never_compile() -> TestResult
{
    let (mut f, _) = matrix("five-kinds")?;
    let (raw, access) = matrix_request("five-kinds", &f)?;
    {
        let ctx = operation_context(&f)?;
        let mut unknown: Value = serde_json::from_slice(&raw)?;
        unknown["raw_xml"] = json!("<edit/>");
        let (partial, _) = product_request(
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
        let mut date: Value = serde_json::from_slice(&raw)?;
        date["operation"]["assignments"][0]["value"] = json!({"kind":"date","value":"2026-10-03"});
        for bad in [
            b"{".to_vec(),
            serde_json::to_vec(&unknown)?,
            partial,
            serde_json::to_vec(&date)?,
        ] {
            assert!(
                FormOperationPreparation::prepare_json(
                    &ctx,
                    identity("plan", "revision-1")?,
                    &bad,
                    &access
                )
                .is_err()
            );
        }
    }
    if let FormControlPayload::Text { validation, .. } = &mut f.policies[0].payload {
        validation.external_validator_sha256 = Some("a".repeat(64));
    }
    let ctx = operation_context(&f)?;
    assert!(
        FormOperationPreparation::prepare_json(
            &ctx,
            identity("plan", "revision-1")?,
            &raw,
            &access
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn finite_identity_limits_and_public_receipts_debug_errors_never_expose_values_or_paths()
-> TestResult {
    assert!(matches!(
        FormOperationIdentity::new(
            DocumentId::parse("x".repeat(1025))?,
            RevisionId::parse("revision")?,
            PlanId::parse("plan")?
        ),
        Err(FormOperationError::Limit)
    ));
    let f = fixture()?;
    let ctx = operation_context(&f)?;
    let (request, access) = f.request("private-unique-form-value")?;
    let id = identity("plan", "revision-1")?;
    assert!(!format!("{id:?}").contains("revision-1"));
    let a =
        FormOperationPreparation::prepare_json(&ctx, id, &serde_json::to_vec(&request)?, &access)?;
    for public in [
        serde_json::to_string(a.receipt())?,
        format!("{a:?}"),
        format!("{ctx:?}"),
        format!("{:?}", a.compiled_plan()),
        format!("{}", FormOperationError::Plan),
    ] {
        assert!(!public.contains("private-unique-form-value"));
        assert!(!public.contains(CAPTURE));
        assert!(!public.contains("90001"));
    }
    Ok(())
}
