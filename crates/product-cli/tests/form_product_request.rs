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
use hwpx_agent_cli::form_product_request::*;
use operation_engine::{
    ClaimOutcome, IdempotencyBinding, IdempotencyLimits, IdempotencyService, OwnerToken,
    RevisionCommit, RevisionStreamKey,
};
fn stream() -> Result<RevisionStreamKey, Box<dyn Error>> {
    Ok(RevisionStreamKey::new(
        ProjectId::parse("product-project")?,
        DocumentId::parse("actual-form-document")?,
    ))
}
fn service() -> Result<IdempotencyService, Box<dyn Error>> {
    let service = IdempotencyService::new(IdempotencyLimits::default())?;
    service.initialize_stream(stream()?, RevisionId::parse("revision-1")?)?;
    Ok(service)
}
fn context(f: &Fixture) -> Result<FormProductContext<'_>, Box<dyn Error>> {
    Ok(FormProductContext::bind(
        ProjectId::parse("product-project")?,
        DocumentId::parse("actual-form-document")?,
        &f.source,
        &f.map,
        &f.policies,
    )?)
}
fn envelope(f: &Fixture, input: &Value) -> Value {
    json!({"schema_version":FORM_PRODUCT_REQUEST_SCHEMA,"idempotency_key":"private-envelope-key","project_id":"product-project","document_id":"actual-form-document","base_revision":"revision-1","expected_head_generation":1,"expected_source_package_sha256":hex::encode(Sha256::digest(&f.source)),"plan_id":"form-plan","form_input":input})
}
#[test]
fn actual_product_envelope_uses_real_head_and_compiler_without_claim_commit_or_publish()
-> TestResult {
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let (input, access) = f.request("P44 private value & <한글> 🚀")?;
    let raw = serde_json::to_vec(&envelope(&f, &input))?;
    let prepared = FormProductPreflight::prepare_json(&ctx, &service, &raw, &access)?;
    let expected = FormOperationPreparation::prepare_json(
        &operation_context(&f)?,
        identity("form-plan", "revision-1")?,
        &serde_json::to_vec(&input)?,
        &access,
    )?;
    let original =
        FormValuePreparation::prepare_json(&f.context()?, &serde_json::to_vec(&input)?, &access)?;
    assert!(prepared.candidate_bytes() == expected.candidate_bytes());
    assert!(prepared.candidate_bytes() == original.candidate_bytes());
    assert_eq!(prepared.receipt().operation, *expected.receipt());
    assert_eq!(
        arg_text(
            &expected.compiled_plan().operations()[0],
            "atomic_input_plan_sha256"
        )?,
        prepared.receipt().operation.typed_input_plan_sha256
    );
    assert_eq!(
        prepared.verify(&ctx, &service, &access)?,
        *prepared.receipt()
    );
    assert_eq!(
        prepared.require_current_product_route(&ctx, &service, &access),
        Err(FormProductRequestError::RouteUnqualified)
    );
    assert_eq!(service.record_count()?, 0);
    assert_eq!(service.head(&stream()?)?.generation(), 1);
    Ok(())
}
#[test]
fn five_kinds_required_radio_defaults_empty_clear_and_complete_bytes_match_predecessor()
-> TestResult {
    let service = service()?;
    for label in [
        "five-kinds",
        "empty-text",
        "reset-defaults",
        "clear-selections",
    ] {
        let (f, expected) = matrix(label)?;
        let (input, access) = matrix_request(label, &f)?;
        let raw = serde_json::to_vec(&envelope(&f, &serde_json::from_slice(&input)?))?;
        let ctx = context(&f)?;
        let prepared = FormProductPreflight::prepare_json(&ctx, &service, &raw, &access)?;
        assert!(
            prepared.candidate_bytes() == expected,
            "whole output mismatch"
        );
        assert_eq!(
            prepared.verify(&ctx, &service, &access)?,
            *prepared.receipt()
        );
        assert_eq!(
            prepared.require_current_product_route(&ctx, &service, &access),
            Err(FormProductRequestError::RouteUnqualified)
        );
    }
    assert_eq!(service.record_count()?, 0);
    Ok(())
}
#[test]
fn duplicate_escaped_nested_unknown_coerced_and_trailing_json_never_prepares() -> TestResult {
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let (input, access) = f.request("parse")?;
    let value = envelope(&f, &input);
    let raw = serde_json::to_string(&value)?;
    let mut unknown = value.clone();
    unknown["workspace_path"] = json!("C:\\private\\output");
    let mut coerced = value.clone();
    coerced["expected_head_generation"] = json!("1");
    let mut nested = value.clone();
    nested["form_input"]["xml"] = json!("<edit/>");
    let duplicate = raw.replace(
        "\"project_id\":\"product-project\"",
        "\"project_id\":\"product-project\",\"project_id\":\"other\"",
    );
    let escaped = raw.replace(
        "\"project_id\":\"product-project\"",
        "\"project_id\":\"product-project\",\"project\\u005fid\":\"other\"",
    );
    let nested_duplicate = raw.replace("\"kind\":\"text\"", "\"kind\":\"text\",\"kind\":\"text\"");
    assert_ne!(raw, duplicate);
    assert_ne!(raw, escaped);
    assert_ne!(raw, nested_duplicate);
    for bad in [
        duplicate.into_bytes(),
        escaped.into_bytes(),
        nested_duplicate.into_bytes(),
        serde_json::to_vec(&unknown)?,
        serde_json::to_vec(&coerced)?,
        serde_json::to_vec(&nested)?,
        format!("{raw} {{}}").into_bytes(),
        b"{".to_vec(),
    ] {
        assert!(FormProductPreflight::prepare_json(&ctx, &service, &bad, &access).is_err());
    }
    assert_eq!(service.record_count()?, 0);
    Ok(())
}
#[test]
fn wrong_provider_project_document_or_full_raw_source_is_rejected_before_compilation() -> TestResult
{
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let (input, access) = f.request("scope")?;
    let value = envelope(&f, &input);
    for (field, bad) in [
        ("project_id", json!("other-project")),
        ("document_id", json!("other-document")),
        ("expected_source_package_sha256", json!("a".repeat(64))),
    ] {
        let mut wrong = value.clone();
        wrong[field] = bad;
        assert!(matches!(
            FormProductPreflight::prepare_json(
                &ctx,
                &service,
                &serde_json::to_vec(&wrong)?,
                &access
            ),
            Err(FormProductRequestError::ProviderScope)
        ));
    }
    assert_eq!(service.record_count()?, 0);
    Ok(())
}
#[test]
fn missing_stream_wrong_revision_zero_or_wrong_generation_never_initializes_or_claims() -> TestResult
{
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let missing = IdempotencyService::new(IdempotencyLimits::default())?;
    let (input, access) = f.request("head")?;
    let value = envelope(&f, &input);
    assert!(matches!(
        FormProductPreflight::prepare_json(&ctx, &missing, &serde_json::to_vec(&value)?, &access),
        Err(FormProductRequestError::Head)
    ));
    assert!(missing.head(&stream()?).is_err());
    assert_eq!(missing.record_count()?, 0);
    for (field, bad) in [
        ("base_revision", json!("revision-other")),
        ("expected_head_generation", json!(0)),
        ("expected_head_generation", json!(2)),
    ] {
        let mut wrong = value.clone();
        wrong[field] = bad;
        assert!(
            FormProductPreflight::prepare_json(
                &ctx,
                &service,
                &serde_json::to_vec(&wrong)?,
                &access
            )
            .is_err()
        );
    }
    assert_eq!(service.record_count()?, 0);
    Ok(())
}
#[test]
fn actual_revision_service_cas_advancement_invalidates_prepared_old_head_even_with_same_source()
-> TestResult {
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let (input, access) = f.request("head-change")?;
    let raw = serde_json::to_vec(&envelope(&f, &input))?;
    let prepared = FormProductPreflight::prepare_json(&ctx, &service, &raw, &access)?;
    assert_eq!(service.record_count()?, 0);
    // Separate in-memory revision-service fixture: opaque test digests are NOT
    // a real form manifest, signature, native evidence or product publication.
    let binding = IdempotencyBinding::new(
        IdempotencyKey::parse("unrelated-revision-fixture")?,
        [1; 32],
        [2; 32],
        stream()?,
        RevisionId::parse("revision-1")?,
        1,
        TransactionId::parse("revision-fixture")?,
    )?;
    let ClaimOutcome::Acquired(lease) = service.claim(binding, &OwnerToken::new([3; 32])?)? else {
        return Err("fixture lease".into());
    };
    service.start(&lease)?;
    let commit = RevisionCommit::new(
        RevisionId::parse("revision-2")?,
        ArtifactId::parse(format!("sha256-{}", hex::encode([4; 32])))?,
        [4; 32],
        1,
        [5; 32],
        IdempotencyLimits::default(),
    )?;
    service.commit_success(&lease, &commit)?;
    assert_eq!(service.head(&stream()?)?.generation(), 2);
    assert_eq!(
        prepared.verify(&ctx, &service, &access),
        Err(FormProductRequestError::Head)
    );
    assert_eq!(
        prepared.require_current_product_route(&ctx, &service, &access),
        Err(FormProductRequestError::Head)
    );
    assert_eq!(service.record_count()?, 1);
    Ok(())
}
#[test]
fn same_source_in_other_provider_scope_cannot_verify_or_authorize_old_preparation() -> TestResult {
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let (input, access) = f.request("scope-change")?;
    let prepared = FormProductPreflight::prepare_json(
        &ctx,
        &service,
        &serde_json::to_vec(&envelope(&f, &input))?,
        &access,
    )?;
    for (project, document) in [
        ("other-project", "actual-form-document"),
        ("product-project", "other-document"),
    ] {
        let fresh = FormProductContext::bind(
            ProjectId::parse(project)?,
            DocumentId::parse(document)?,
            &f.source,
            &f.map,
            &f.policies,
        )?;
        assert_eq!(
            prepared.verify(&fresh, &service, &access),
            Err(FormProductRequestError::ProviderScope)
        );
    }
    assert_eq!(service.record_count()?, 0);
    Ok(())
}
#[test]
fn fresh_access_and_policy_revocation_propagate_before_route_and_do_not_reserve_key() -> TestResult
{
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let (input, access) = f.request("fresh")?;
    let prepared = FormProductPreflight::prepare_json(
        &ctx,
        &service,
        &serde_json::to_vec(&envelope(&f, &input))?,
        &access,
    )?;
    let mut revoked = access.clone();
    revoked.input_allowed = false;
    assert_eq!(
        prepared.verify(&ctx, &service, &revoked),
        Err(FormProductRequestError::Drift)
    );
    assert_eq!(
        prepared.require_current_product_route(&ctx, &service, &revoked),
        Err(FormProductRequestError::Drift)
    );
    let mut policies = f.policies.clone();
    if let FormControlPayload::Text { default_value, .. } = &mut policies[0].payload {
        *default_value = "changed".into();
    }
    let fresh = FormProductContext::bind(
        ProjectId::parse("product-project")?,
        DocumentId::parse("actual-form-document")?,
        &f.source,
        &f.map,
        &policies,
    )?;
    assert_eq!(
        prepared.verify(&fresh, &service, &access),
        Err(FormProductRequestError::Drift)
    );
    assert_eq!(service.record_count()?, 0);
    Ok(())
}
#[test]
fn exact_retry_semantic_formatting_and_key_binding_are_not_execution_idempotency() -> TestResult {
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let (input, access) = f.request("retry")?;
    let value = envelope(&f, &input);
    let raw = serde_json::to_vec(&value)?;
    let first = FormProductPreflight::prepare_json(&ctx, &service, &raw, &access)?;
    let retry = FormProductPreflight::prepare_json(&ctx, &service, &raw, &access)?;
    let formatted = FormProductPreflight::prepare_json(
        &ctx,
        &service,
        &serde_json::to_vec_pretty(&value)?,
        &access,
    )?;
    assert_eq!(first.receipt(), retry.receipt());
    assert_eq!(
        first.receipt().canonical_request_sha256,
        formatted.receipt().canonical_request_sha256
    );
    assert_eq!(
        first.receipt().scoped_request_sha256,
        formatted.receipt().scoped_request_sha256
    );
    assert_ne!(
        first.receipt().raw_request_sha256,
        formatted.receipt().raw_request_sha256
    );
    let mut other = value;
    other["idempotency_key"] = json!("other-private-key");
    let new_key =
        FormProductPreflight::prepare_json(&ctx, &service, &serde_json::to_vec(&other)?, &access)?;
    assert_ne!(
        first.receipt().scoped_request_sha256,
        new_key.receipt().scoped_request_sha256
    );
    assert!(first.candidate_bytes() == new_key.candidate_bytes());
    assert_eq!(service.record_count()?, 0);
    Ok(())
}
#[test]
fn bounded_request_provider_ids_and_redacted_output_do_not_leak_private_values_or_keys()
-> TestResult {
    let f = fixture()?;
    let ctx = context(&f)?;
    let service = service()?;
    let (input, access) = f.request("unique-private-p44-value")?;
    let raw = serde_json::to_vec(&envelope(&f, &input))?;
    let a = FormProductPreflight::prepare_json(&ctx, &service, &raw, &access)?;
    for public in [
        serde_json::to_string(a.receipt())?,
        format!("{a:?}"),
        format!("{ctx:?}"),
        format!("{}", FormProductRequestError::Request),
    ] {
        for private in [
            "unique-private-p44-value",
            "private-envelope-key",
            CAPTURE,
            "actual-form-document",
            "product-project",
        ] {
            assert!(!public.contains(private));
        }
    }
    assert!(matches!(
        FormProductPreflight::prepare_json(
            &ctx,
            &service,
            &vec![b' '; 2 * 1024 * 1024 + 1],
            &access
        ),
        Err(FormProductRequestError::Limit)
    ));
    assert!(matches!(
        FormProductContext::bind(
            ProjectId::parse("product-project")?,
            DocumentId::parse("x".repeat(1025))?,
            &f.source,
            &f.map,
            &f.policies
        ),
        Err(FormProductRequestError::Limit)
    ));
    assert_eq!(service.record_count()?, 0);
    Ok(())
}
