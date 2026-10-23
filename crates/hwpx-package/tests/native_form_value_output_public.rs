//! Complete predecessor cases through the actual public versioned value API only.
use domain_ir::form_input::*;
use domain_ir::*;
use hwpx_package::native_form_value_output::*;
pub use hwpx_package::*;
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    fs,
    io::{Cursor, Write as _},
    path::Path,
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
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

fn domain_limits() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
}
fn access(observed: &NativeFormValueReadback) -> Result<FormInputAccessPolicy, AnyError> {
    let draft: FormDocumentStateDraft =
        serde_json::from_slice(&observed.state().canonical_json(domain_limits()?)?)?;
    Ok(FormInputAccessPolicy {
        document_protection_sha256: draft.document_protection_sha256,
        input_allowed: true,
    })
}
fn input(
    source: &[u8],
    map: &NativeFormPackageMap,
    policies: &[NativeFormPackagePolicy],
    operation: FormInputOperation,
) -> Result<(NativeFormValuePlan, FormInputAccessPolicy, FormInputPlan), AnyError> {
    let observed = NativeFormValueReader::read(
        source,
        map,
        policies,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let access = access(&observed)?;
    let request = FormInputRequest::from_draft(
        FormInputRequestDraft {
            schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("native-value-request")?,
            expected_source_state_sha256: observed.state().canonical_sha256(domain_limits()?)?,
            expected_document_flow_sha256: observed.native_v1().document_flow_sha256().into(),
            access: access.clone(),
            operation,
        },
        observed.state(),
        observed.native_v1().document_flow_sha256(),
        domain_limits()?,
    )?;
    let domain = FormInputBuilder::plan(
        observed.state(),
        &request,
        observed.native_v1().document_flow_sha256(),
        domain_limits()?,
    )?;
    Ok((
        NativeFormValuePlan::bind(
            source,
            map,
            policies,
            &domain,
            &access,
            domain_limits()?,
            NativeFormPackageLimits::default(),
        )?,
        access,
        domain,
    ))
}
fn lower(
    source: &[u8],
    plan: &NativeFormValuePlan,
    access: &FormInputAccessPolicy,
) -> Result<NativeFormValueOutput, AnyError> {
    Ok(NativeFormValueLowerer::lower(
        source,
        plan,
        access,
        domain_limits()?,
        NativeFormPackageLimits::default(),
        NativeFormValueLimits::default(),
    )?)
}
fn output_policies(state: &FormDocumentState) -> Vec<NativeFormPackagePolicy> {
    state
        .controls()
        .iter()
        .map(|c| NativeFormPackagePolicy {
            identity: c.identity.clone(),
            payload: c.payload.clone(),
        })
        .collect()
}
fn assert_complete(
    source: &[u8],
    output: &NativeFormValueOutput,
    plan: &NativeFormValuePlan,
    access: &FormInputAccessPolicy,
) -> Result<(), AnyError> {
    assert_eq!(
        &NativeFormValueLowerer::verify_output(
            source,
            plan,
            output.bytes(),
            access,
            domain_limits()?,
            NativeFormPackageLimits::default(),
            NativeFormValueLimits::default()
        )?,
        output.receipt()
    );
    assert_ne!(source, output.bytes());
    assert_eq!(output.bytes(), lower(source, plan, access)?.bytes());
    assert_eq!(output.receipt().qualification,NativeFormValueQualification::CompletePackageComponentOnlyNativeExecutionProtectionDateExternalValidationAndRoutingUnqualified);
    Ok(())
}
#[test]
fn actual_capture_value_output_reopens_complete_package_with_distinct_v2_opaque_profile_and_preserves_old_failure()
-> Result<(), AnyError> {
    let source = capture()?;
    let map = actual_map(&source)?;
    let old = NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
    let c = &old.sections().next().ok_or("section")?.controls()[0];
    let policies = vec![policy(c)?];
    let observed = NativeFormValueReader::read(
        &source,
        &map,
        &policies,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let old_state = old.bind_policies(&policies, domain_limits()?)?;
    assert_eq!(
        observed.v1_state_sha256(),
        old_state.canonical_sha256(domain_limits()?)?
    );
    let mut projected: FormDocumentStateDraft =
        serde_json::from_slice(&old_state.canonical_json(domain_limits()?)?)?;
    assert_ne!(
        observed.state().controls()[0].opaque_native_payload_sha256,
        projected.controls[0].opaque_native_payload_sha256
    );
    projected.controls[0].opaque_native_payload_sha256 = observed.state().controls()[0]
        .opaque_native_payload_sha256
        .clone();
    assert_eq!(
        FormDocumentState::from_draft(projected, domain_limits()?)?,
        *observed.state()
    );
    let operation = FormInputOperation::SetValues {
        assignments: vec![FormInputAssignment {
            target: c.component_identity.clone(),
            value: FormInputValue::Text {
                value: "P40 값 & <한글> \" ' 🚀".into(),
            },
        }],
    };
    let (plan, access, domain) = input(&source, &map, &policies, operation)?;
    retain_old_failure(
        &source,
        &map,
        &policies,
        &old_state,
        &domain.target_state().controls()[0],
        old.document_flow_sha256(),
        domain_limits()?,
    )?;
    let output = lower(&source, &plan, &access)?;
    assert_complete(&source, &output, &plan, &access)?;
    let fresh = NativeFormValueReader::read(
        output.bytes(),
        &map,
        &output_policies(domain.target_state()),
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    assert_eq!(fresh.state(), domain.target_state());
    assert_eq!(
        fresh
            .native_v1()
            .sections()
            .next()
            .ok_or("section")?
            .controls()[0]
            .native_identity,
        NativeFormObservedIdentity::Missing
    );
    assert_eq!(capture()?, source);
    println!(
        "P09_40_ACTUAL_VALUE_PROBE={}",
        serde_json::to_string(output.receipt())?
    );
    Ok(())
}

// Fixtures are declared capture-derived component specimens, never target-build proof.
#[derive(Clone)]
struct TestPart {
    name: String,
    compression: Compression,
    bytes: Vec<u8>,
}
fn parts(raw: &[u8]) -> Result<Vec<TestPart>, AnyError> {
    let mut zip = BoundedZipReader::open(Cursor::new(raw), PackageLimits::default())?;
    let entries = zip.entries().to_vec();
    entries
        .into_iter()
        .map(|e| {
            Ok(TestPart {
                name: e.path.as_str().into(),
                compression: e.compression,
                bytes: zip.read_entry(e.index)?,
            })
        })
        .collect()
}
fn package(parts: &[TestPart]) -> Result<Vec<u8>, AnyError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for part in parts {
        let compression = match part.compression {
            Compression::Stored => CompressionMethod::Stored,
            Compression::Deflated => CompressionMethod::Deflated,
        };
        writer.start_file(
            &part.name,
            SimpleFileOptions::default().compression_method(compression),
        )?;
        writer.write_all(&part.bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}
fn part_mut<'a>(parts: &'a mut [TestPart], name: &str) -> Result<&'a mut Vec<u8>, AnyError> {
    Ok(&mut parts
        .iter_mut()
        .find(|p| p.name == name)
        .ok_or("part missing")?
        .bytes)
}
fn replace_part(parts: &mut [TestPart], name: &str, from: &str, to: &str) -> Result<(), AnyError> {
    let bytes = part_mut(parts, name)?;
    let text = String::from_utf8(bytes.clone())?;
    if text.matches(from).count() != 1 {
        return Err("test substitution not unique".into());
    }
    *bytes = text.replace(from, to).into_bytes();
    Ok(())
}
fn control(kind: &str, i: usize, checked: bool, empty: bool) -> String {
    let (attributes, payload): (String, String) = match kind {
        "edit" => (
            "multiLine=\"1\" passwordChar=\"*\" maxLength=\"64\" scrollBars=\"NONE\" tabKeyBehavior=\"NEXT_OBJECT\" numOnly=\"0\" readOnly=\"0\" alignText=\"LEFT\"".into(),
            if empty { "<hp:text u:keep='literal &amp; preserved' />" } else { "<hp:text u:keep='literal &amp; preserved'>initial &amp; 한글</hp:text>" }.into(),
        ),
        "checkBtn" => ("caption=\"checkbox\" value=\"CHECKED\" radioGroupName=\"\" triState=\"1\" backStyle=\"OPAQUE\"".into(), String::new()),
        "radioBtn" => (format!("caption=\"radio\" value=\"{}\" radioGroupName=\"cross-section-radio\" triState=\"0\" backStyle=\"TRANSPARENT\"", if checked { "CHECKED" } else { "UNCHECKED" }), String::new()),
        "comboBox" => ("listBoxRows=\"3\" listBoxWidth=\"10800\" editEnable=\"1\" selectedValue='a'".into(), "<hp:listItem displayText=\"한글 &amp; a\" value=\"a\"/><hp:listItem displayText=\"b\" value=\"b\"/>".into()),
        _ => ("itemHeight=\"1000\" topIdx=\"0\" selectedValue=\"b\"".into(), "<hp:listItem displayText=\"a\" value=\"a\"/><hp:listItem displayText=\"한글 b\" value=\"b\"/>".into()),
    };
    format!(
        "<hp:{kind} xmlns:u=\"urn:p09:40:unknown\" u:flag='opaque &amp; fixed' name=\"component{i}\" foreColor=\"#000000\" backColor=\"#FFFFFF\" groupName=\"\" tabStop=\"1\" editable=\"1\" tabOrder=\"{i}\" enabled=\"1\" borderTypeIDRef=\"0\" drawFrame=\"1\" printable=\"1\" command=\"\" {attributes}><hp:formCharPr charPrIDRef=\"0\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/>{payload}<u:payload keep=\"same\">opaque-bytes</u:payload><hp:sz width=\"10800\" height=\"5400\" protect=\"0\"/><hp:pos horzOffset=\"0\" vertOffset=\"0\"/><hp:outMargin left=\"0\" right=\"0\" top=\"0\" bottom=\"0\"/></hp:{kind}>"
    )
}
fn generic_policy(c: &NativeFormControlObservation) -> Result<NativeFormPackagePolicy, AnyError> {
    let payload = match &c.payload {
        NativeFormObservedPayload::Text { .. } => {
            let mut payload = policy(c)?.payload;
            if let FormControlPayload::Text { default_value, .. } = &mut payload {
                *default_value = "caller-default".into();
            }
            payload
        }
        NativeFormObservedPayload::Button {
            caption,
            value,
            radio_group_name,
            tri_state,
            back_style,
        } if c.tag == NativeFormTag::RadioBtn => FormControlPayload::Radio {
            caption: caption.clone(),
            value: *value,
            default_value: *value,
            radio_group_name: radio_group_name.clone().ok_or("radio group")?,
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
            default_selected_value: Some("a".into()),
            validation: FormSelectionValidation {
                required: false,
                external_validator_sha256: None,
            },
            item_height_hwp_units: *item_height_hwp_units,
            top_index: *top_index,
        },
    };
    Ok(NativeFormPackagePolicy {
        identity: c.component_identity.clone(),
        payload,
    })
}
struct Specimen {
    source: Vec<u8>,
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
}
fn extend_spine(p: &mut [TestPart]) -> Result<(), AnyError> {
    replace_part(p, "Contents/header.xml", "secCnt=\"1\"", "secCnt=\"2\"")?;
    let opf = String::from_utf8(part_mut(p, "Contents/content.hpf")?.clone())?;
    let prefix = if opf.contains("</opf:manifest>") {
        "opf:"
    } else {
        ""
    };
    replace_part(
        p,
        "Contents/content.hpf",
        &format!("</{prefix}manifest>"),
        &format!(
            "<{prefix}item id=\"section1\" href=\"section1.xml\" media-type=\"application/xml\"/></{prefix}manifest>"
        ),
    )?;
    replace_part(
        p,
        "Contents/content.hpf",
        &format!("</{prefix}spine>"),
        &format!("<{prefix}itemref idref=\"section1\" linear=\"yes\"/></{prefix}spine>"),
    )?;
    Ok(())
}
fn specimen(empty: bool) -> Result<Specimen, AnyError> {
    let original = capture()?;
    let mut p = parts(&original)?;
    let original_section = part_mut(&mut p, "Contents/section0.xml")?.clone();
    let parsed = PreservingXmlDocument::parse(&original_section)?;
    let root = parsed
        .elements()
        .iter()
        .find(|e| e.name().namespace() == Some(HP) && e.name().local_name() == "edit")
        .ok_or("edit")?
        .outer_span()
        .ok_or("span")?;
    let old = String::from_utf8(original_section.clone())?;
    let kinds = ["edit", "checkBtn", "radioBtn", "comboBox", "listBox"];
    let replacement: String = kinds
        .iter()
        .enumerate()
        .map(|(i, kind)| control(kind, i, true, empty))
        .collect();
    let mut first = old.clone();
    first.replace_range(root.start()..root.end(), &replacement);
    *part_mut(&mut p, "Contents/section0.xml")? = first.into_bytes();
    let mut second = old;
    second.replace_range(
        root.start()..root.end(),
        &control("radioBtn", 5, false, false),
    );
    second = second
        .replace("<hp:p id=\"0\"", "<hp:p id=\"10\"")
        .replace("<hp:p id=\"1\"", "<hp:p id=\"11\"");
    p.push(TestPart {
        name: "Contents/section1.xml".into(),
        compression: Compression::Deflated,
        bytes: second.into_bytes(),
    });
    extend_spine(&mut p)?;
    let map = NativeFormPackageMap {
        sections: (0..2)
            .map(|section| {
                let indexes: Vec<usize> = if section == 0 {
                    (0..5).collect()
                } else {
                    vec![5]
                };
                Ok(NativeFormPackageSectionMap {
                    part: format!("Contents/section{section}.xml"),
                    map: NativeFormHwpxMap {
                        paragraph_ids: (0..2)
                            .map(|i| LogicalId::parse(format!("p40-section{section}-p{i}")))
                            .collect::<Result<_, _>>()?,
                        component_controls: indexes
                            .into_iter()
                            .map(|i| {
                                Ok(FormControlIdentity {
                                    logical_control_id: LogicalId::parse(format!(
                                        "p40-control{i}"
                                    ))?,
                                    native_object_id: 90001 + u32::try_from(i)?,
                                })
                            })
                            .collect::<Result<_, AnyError>>()?,
                    },
                })
            })
            .collect::<Result<_, AnyError>>()?,
    };
    let source = package(&p)?;
    let observed =
        NativeFormPackageReader::read(&source, &map, NativeFormPackageLimits::default())?;
    let policies = observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(generic_policy)
        .collect::<Result<_, _>>()?;
    Ok(Specimen {
        source,
        map,
        policies,
    })
}
fn set(s: &Specimen, assignments: &[(usize, FormInputValue)]) -> FormInputOperation {
    FormInputOperation::SetValues {
        assignments: assignments
            .iter()
            .map(|(i, value)| FormInputAssignment {
                target: s.policies[*i].identity.clone(),
                value: value.clone(),
            })
            .collect(),
    }
}
fn all_values(s: &Specimen) -> FormInputOperation {
    set(
        s,
        &[
            (
                0,
                FormInputValue::Text {
                    value: "新 & <\"'> 🚀\r\n\tline".into(),
                },
            ),
            (
                1,
                FormInputValue::Checkbox {
                    value: FormButtonValue::Indeterminate,
                },
            ),
            (
                2,
                FormInputValue::Radio {
                    value: FormButtonValue::Unchecked,
                },
            ),
            (
                3,
                FormInputValue::Combo {
                    selected_value: Some("b".into()),
                },
            ),
            (
                4,
                FormInputValue::List {
                    selected_value: Some("a".into()),
                },
            ),
            (
                5,
                FormInputValue::Radio {
                    value: FormButtonValue::Checked,
                },
            ),
        ],
    )
}
fn verify(
    s: &Specimen,
    plan: &NativeFormValuePlan,
    access: &FormInputAccessPolicy,
    bytes: &[u8],
) -> Result<NativeFormValueReceipt, NativeFormValueError> {
    NativeFormValueLowerer::verify_output(
        &s.source,
        plan,
        bytes,
        access,
        domain_limits().map_err(|_| NativeFormValueError::Limit)?,
        NativeFormPackageLimits::default(),
        NativeFormValueLimits::default(),
    )
}
#[test]
fn five_native_kinds_cross_section_required_radio_and_all_unknown_bytes_are_preserved()
-> Result<(), AnyError> {
    let s = specimen(false)?;
    let original = s.source.clone();
    let (plan, access, domain) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    let output = lower(&s.source, &plan, &access)?;
    assert_complete(&s.source, &output, &plan, &access)?;
    assert_eq!(
        (
            output.receipt().changed_controls,
            output.receipt().changed_sections,
            output.receipt().managed_value_edits
        ),
        (6, 2, 6)
    );
    let fresh = NativeFormValueReader::read(
        output.bytes(),
        &s.map,
        &output_policies(domain.target_state()),
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    assert_eq!(fresh.state(), domain.target_state());
    for section in fresh.native_v1().sections() {
        for c in section.controls() {
            assert_eq!(c.native_identity, NativeFormObservedIdentity::Missing);
        }
    }
    let before = parts(&s.source)?;
    let after = parts(output.bytes())?;
    assert_eq!(before.len(), after.len());
    for (b, a) in before.iter().zip(&after) {
        assert_eq!((&b.name, b.compression), (&a.name, a.compression));
        if b.name.starts_with("Contents/section") {
            let text = std::str::from_utf8(&a.bytes)?;
            let count = if b.name == "Contents/section0.xml" {
                5
            } else {
                1
            };
            assert_eq!(text.matches("u:flag='opaque &amp; fixed'").count(), count);
            assert_eq!(
                text.matches("<u:payload keep=\"same\">opaque-bytes</u:payload>")
                    .count(),
                count
            );
            if count == 5 {
                assert!(text.contains("<hp:text u:keep='literal &amp; preserved'>新 &amp; &lt;&quot;&apos;&gt; 🚀&#13;&#10;&#9;line</hp:text>"));
            }
        } else {
            assert_eq!(a.bytes, b.bytes);
        }
    }
    assert_eq!(s.source, original);
    Ok(())
}
#[test]
fn reset_all_explicit_caller_defaults_roundtrips_atomically_without_claiming_native_defaults()
-> Result<(), AnyError> {
    let s = specimen(false)?;
    let (plan, access, domain) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    let changed = lower(&s.source, &plan, &access)?;
    let policies = output_policies(domain.target_state());
    let reset = FormInputOperation::ResetDefaults {
        targets: policies.iter().map(|p| p.identity.clone()).collect(),
    };
    let (plan, access, target) = input(changed.bytes(), &s.map, &policies, reset)?;
    let output = lower(changed.bytes(), &plan, &access)?;
    assert_complete(changed.bytes(), &output, &plan, &access)?;
    let fresh = NativeFormValueReader::read(
        output.bytes(),
        &s.map,
        &output_policies(target.target_state()),
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    assert_eq!(fresh.state(), target.target_state());
    for c in fresh.state().controls() {
        match &c.payload {
            FormControlPayload::Text {
                value,
                default_value,
                ..
            } => assert_eq!(value, default_value),
            FormControlPayload::Checkbox {
                value,
                default_value,
                ..
            }
            | FormControlPayload::Radio {
                value,
                default_value,
                ..
            } => assert_eq!(value, default_value),
            FormControlPayload::Combo {
                selected_value,
                default_selected_value,
                ..
            }
            | FormControlPayload::List {
                selected_value,
                default_selected_value,
                ..
            } => assert_eq!(selected_value, default_selected_value),
            FormControlPayload::Date { .. } => {
                return Err("native date unexpectedly admitted".into());
            }
        }
    }
    Ok(())
}
#[test]
fn empty_text_expansion_preserves_raw_head_attributes_and_v2_fingerprint() -> Result<(), AnyError> {
    let s = specimen(true)?;
    let observed = NativeFormValueReader::read(
        &s.source,
        &s.map,
        &s.policies,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let operation = set(
        &s,
        &[(
            0,
            FormInputValue::Text {
                value: "value & 🚀".into(),
            },
        )],
    );
    let (plan, access, domain) = input(&s.source, &s.map, &s.policies, operation)?;
    let output = lower(&s.source, &plan, &access)?;
    assert_complete(&s.source, &output, &plan, &access)?;
    let fresh = NativeFormValueReader::read(
        output.bytes(),
        &s.map,
        &output_policies(domain.target_state()),
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    assert_eq!(
        observed.state().controls()[0].opaque_native_payload_sha256,
        fresh.state().controls()[0].opaque_native_payload_sha256
    );
    let p = parts(output.bytes())?;
    assert!(
        std::str::from_utf8(
            &p[p.iter()
                .position(|p| p.name == "Contents/section0.xml")
                .ok_or("section")?]
            .bytes
        )?
        .contains("<hp:text u:keep='literal &amp; preserved' >value &amp; 🚀</hp:text>")
    );
    Ok(())
}
#[test]
fn both_selection_clear_values_remain_none_not_invented_items_or_empty_literal()
-> Result<(), AnyError> {
    let s = specimen(false)?;
    let operation = set(
        &s,
        &[
            (
                3,
                FormInputValue::Combo {
                    selected_value: None,
                },
            ),
            (
                4,
                FormInputValue::List {
                    selected_value: None,
                },
            ),
        ],
    );
    let (plan, access, domain) = input(&s.source, &s.map, &s.policies, operation)?;
    let output = lower(&s.source, &plan, &access)?;
    assert_complete(&s.source, &output, &plan, &access)?;
    let fresh = NativeFormValueReader::read(
        output.bytes(),
        &s.map,
        &output_policies(domain.target_state()),
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    assert_eq!(fresh.state(), domain.target_state());
    let p = parts(output.bytes())?;
    let text = std::str::from_utf8(
        &p.iter()
            .find(|p| p.name == "Contents/section0.xml")
            .ok_or("section")?
            .bytes,
    )?;
    assert!(text.contains("selectedValue=''"));
    assert!(text.contains("selectedValue=\"\""));
    Ok(())
}
#[test]
fn required_radio_intermediate_invalid_transition_is_rejected_before_any_output()
-> Result<(), AnyError> {
    let s = specimen(false)?;
    for (i, v) in [
        (2, FormButtonValue::Unchecked),
        (5, FormButtonValue::Checked),
    ] {
        assert!(
            input(
                &s.source,
                &s.map,
                &s.policies,
                set(&s, &[(i, FormInputValue::Radio { value: v })])
            )
            .is_err()
        );
    }
    assert!(
        input(
            &s.source,
            &s.map,
            &s.policies,
            set(
                &s,
                &[
                    (
                        2,
                        FormInputValue::Radio {
                            value: FormButtonValue::Unchecked
                        }
                    ),
                    (
                        5,
                        FormInputValue::Radio {
                            value: FormButtonValue::Checked
                        }
                    )
                ]
            )
        )
        .is_ok()
    );
    Ok(())
}
#[test]
fn fresh_access_revocation_and_protection_digest_drift_fail_both_output_and_external_verification()
-> Result<(), AnyError> {
    let s = specimen(false)?;
    let (plan, access, _) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    let output = lower(&s.source, &plan, &access)?;
    let mut denied = access.clone();
    denied.input_allowed = false;
    let mut drift = access.clone();
    drift.document_protection_sha256 = "0".repeat(64);
    for stale in [denied, drift] {
        assert!(matches!(
            NativeFormValueLowerer::lower(
                &s.source,
                &plan,
                &stale,
                domain_limits()?,
                NativeFormPackageLimits::default(),
                NativeFormValueLimits::default()
            ),
            Err(NativeFormValueError::Access)
        ));
        assert_eq!(
            verify(&s, &plan, &stale, output.bytes()),
            Err(NativeFormValueError::Access)
        );
    }
    Ok(())
}
#[test]
fn external_output_tampering_rejects_unknown_control_attributes_children_nonform_and_nonsection_bytes()
-> Result<(), AnyError> {
    let s = specimen(false)?;
    let (plan, access, _) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    let output = lower(&s.source, &plan, &access)?;
    for (part, from, to) in [
        (
            "Contents/section0.xml",
            "u:keep='literal &amp; preserved'",
            "u:keep='changed'",
        ),
        ("Contents/section1.xml", "opaque-bytes", "changed-bytes"),
        (
            "Contents/section1.xml",
            "name=\"component5\"",
            "name=\"changed\"",
        ),
        ("Contents/header.xml", "secCnt=\"2\"", "secCnt=\"3\""),
    ] {
        let mut p = parts(output.bytes())?;
        replace_part(&mut p, part, from, to)?;
        assert_eq!(
            verify(&s, &plan, &access, &package(&p)?),
            Err(NativeFormValueError::Preservation)
        );
    }
    let mut p = parts(output.bytes())?;
    part_mut(&mut p, "Contents/section0.xml")?.extend_from_slice(b" ");
    assert_eq!(
        verify(&s, &plan, &access, &package(&p)?),
        Err(NativeFormValueError::Preservation)
    );
    Ok(())
}
#[test]
fn external_output_inventory_order_compression_extra_missing_and_wrong_values_fail()
-> Result<(), AnyError> {
    let s = specimen(false)?;
    let (plan, access, _) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    let output = lower(&s.source, &plan, &access)?;
    let baseline = parts(output.bytes())?;
    let mut changed = baseline.clone();
    changed.swap(1, 2);
    let mut compressed = baseline.clone();
    compressed[1].compression = if compressed[1].compression == Compression::Stored {
        Compression::Deflated
    } else {
        Compression::Stored
    };
    let mut missing = baseline.clone();
    missing.pop();
    let mut extra = baseline.clone();
    extra.push(TestPart {
        name: "unclaimed.bin".into(),
        compression: Compression::Stored,
        bytes: b"extra".to_vec(),
    });
    for p in [changed, compressed, missing, extra] {
        assert!(verify(&s, &plan, &access, &package(&p)?).is_err());
    }
    assert_eq!(
        verify(&s, &plan, &access, &s.source),
        Err(NativeFormValueError::Preservation)
    );
    Ok(())
}
#[test]
fn original_source_package_drift_is_not_rebound_or_accepted_by_output() -> Result<(), AnyError> {
    let s = specimen(false)?;
    let (plan, access, _) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    let mut p = parts(&s.source)?;
    replace_part(
        &mut p,
        "Contents/section1.xml",
        "opaque-bytes",
        "drift-bytes",
    )?;
    assert!(lower(&package(&p)?, &plan, &access).is_err());
    Ok(())
}
#[test]
fn complete_v1_plan_is_not_silently_substituted_for_versioned_v2_source() -> Result<(), AnyError> {
    let s = specimen(false)?;
    let native =
        NativeFormPackageReader::read(&s.source, &s.map, NativeFormPackageLimits::default())?;
    let state = native.bind_policies(&s.policies, domain_limits()?)?;
    let observed = NativeFormValueReader::read(
        &s.source,
        &s.map,
        &s.policies,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let access = access(&observed)?;
    let request = FormInputRequest::from_draft(
        FormInputRequestDraft {
            schema_version: FORM_INPUT_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("v1-not-v2")?,
            expected_source_state_sha256: state.canonical_sha256(domain_limits()?)?,
            expected_document_flow_sha256: native.document_flow_sha256().into(),
            access: access.clone(),
            operation: all_values(&s),
        },
        &state,
        native.document_flow_sha256(),
        domain_limits()?,
    )?;
    let domain = FormInputBuilder::plan(
        &state,
        &request,
        native.document_flow_sha256(),
        domain_limits()?,
    )?;
    assert!(matches!(
        NativeFormValuePlan::bind(
            &s.source,
            &s.map,
            &s.policies,
            &domain,
            &access,
            domain_limits()?,
            NativeFormPackageLimits::default()
        ),
        Err(NativeFormValueError::Binding)
    ));
    Ok(())
}
#[test]
fn output_limits_fail_without_clamping_or_partial_package() -> Result<(), AnyError> {
    let s = specimen(false)?;
    let (plan, access, _) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    for (a, p, t) in [
        (0, 1, 1),
        (1, 0, 1),
        (1, 1, 0),
        (1, 2, 1),
        (32 * 1024 * 1024 + 1, 1, 1),
        (1, 2 * 1024 * 1024 + 1, 16 * 1024 * 1024),
        (1, 1, 16 * 1024 * 1024 + 1),
    ] {
        assert_eq!(
            NativeFormValueLimits::new(a, p, t),
            Err(NativeFormValueError::Limit)
        );
    }
    for limits in [
        NativeFormValueLimits::new(32 * 1024 * 1024, 1, 16 * 1024 * 1024)?,
        NativeFormValueLimits::new(32 * 1024 * 1024, 2048, 2048)?,
        NativeFormValueLimits::new(1, 2 * 1024 * 1024, 16 * 1024 * 1024)?,
    ] {
        assert!(matches!(
            NativeFormValueLowerer::lower(
                &s.source,
                &plan,
                &access,
                domain_limits()?,
                NativeFormPackageLimits::default(),
                limits
            ),
            Err(NativeFormValueError::Limit)
        ));
    }
    Ok(())
}
#[test]
fn invalid_xml_values_and_unqualified_date_kind_fail_closed() -> Result<(), AnyError> {
    let s = specimen(false)?;
    for value in [
        "nul\0",
        "control\u{1f}",
        "not-xml\u{fffe}",
        "not-xml\u{ffff}",
    ] {
        if let Ok((plan, access, _)) = input(
            &s.source,
            &s.map,
            &s.policies,
            set(
                &s,
                &[(
                    0,
                    FormInputValue::Text {
                        value: value.into(),
                    },
                )],
            ),
        ) {
            assert!(lower(&s.source, &plan, &access).is_err());
        }
    }
    assert!(
        input(
            &s.source,
            &s.map,
            &s.policies,
            set(
                &s,
                &[(
                    0,
                    FormInputValue::Date {
                        value: Some("2026-10-03".into())
                    }
                )]
            )
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn debug_and_hash_receipts_do_not_expose_values_or_unknown_text() -> Result<(), AnyError> {
    let s = specimen(false)?;
    let observed = NativeFormValueReader::read(
        &s.source,
        &s.map,
        &s.policies,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let (plan, access, _) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    let output = lower(&s.source, &plan, &access)?;
    let serialized = serde_json::to_string(output.receipt())?;
    let debug = format!("{observed:?}{plan:?}{output:?}");
    for raw in [
        "initial",
        "caller-default",
        "opaque-bytes",
        "literal",
        "新",
        "🚀",
    ] {
        assert!(!serialized.contains(raw));
        assert!(!debug.contains(raw));
    }
    assert!(serialized.contains(NATIVE_FORM_VALUE_PROFILE));
    Ok(())
}

#[test]
fn missing_selection_attribute_is_unqualified_even_when_v1_can_observe_none() -> Result<(), AnyError>
{
    let mut s = specimen(false)?;
    let mut p = parts(&s.source)?;
    replace_part(&mut p, "Contents/section0.xml", "selectedValue='a'", "")?;
    s.source = package(&p)?;
    let native =
        NativeFormPackageReader::read(&s.source, &s.map, NativeFormPackageLimits::default())?;
    s.policies = native
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(generic_policy)
        .collect::<Result<_, _>>()?;
    native.bind_policies(&s.policies, domain_limits()?)?;
    assert!(matches!(
        NativeFormValueReader::read(
            &s.source,
            &s.map,
            &s.policies,
            domain_limits()?,
            NativeFormPackageLimits::default()
        ),
        Err(NativeFormValueError::Unsupported)
    ));
    Ok(())
}
#[test]
fn map_policy_and_package_source_bindings_are_fresh_not_receipt_claims() -> Result<(), AnyError> {
    let s = specimen(false)?;
    let (plan, access, domain) = input(&s.source, &s.map, &s.policies, all_values(&s))?;
    let mut map = s.map.clone();
    map.sections[0].map.component_controls[0].native_object_id += 100;
    let mut coherent = s.policies.clone();
    coherent[0].identity = map.sections[0].map.component_controls[0].clone();
    // This separately valid caller map must not satisfy the earlier complete plan.
    NativeFormValueReader::read(
        &s.source,
        &map,
        &coherent,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    assert!(matches!(
        NativeFormValuePlan::bind(
            &s.source,
            &map,
            &coherent,
            &domain,
            &access,
            domain_limits()?,
            NativeFormPackageLimits::default()
        ),
        Err(NativeFormValueError::Binding)
    ));
    let mut mismatched = s.policies.clone();
    if let FormControlPayload::Combo { selected_value, .. } = &mut mismatched[3].payload {
        *selected_value = Some("b".into());
    }
    assert!(
        NativeFormValueReader::read(
            &s.source,
            &s.map,
            &mismatched,
            domain_limits()?,
            NativeFormPackageLimits::default()
        )
        .is_err()
    );
    let mut missing = s.map.clone();
    missing.sections[0].map.component_controls.pop();
    assert!(
        NativeFormValueReader::read(
            &s.source,
            &missing,
            &s.policies,
            domain_limits()?,
            NativeFormPackageLimits::default()
        )
        .is_err()
    );
    assert!(lower(&s.source, &plan, &access).is_ok());
    Ok(())
}
#[test]
fn observed_protection_signal_is_rejected_even_if_caller_says_allowed() -> Result<(), AnyError> {
    let mut s = specimen(false)?;
    let mut p = parts(&s.source)?;
    replace_part(
        &mut p,
        "Contents/header.xml",
        "secCnt=\"2\"",
        "secCnt=\"2\" p09Protect=\"0\"",
    )?;
    s.source = package(&p)?;
    let observed = NativeFormValueReader::read(
        &s.source,
        &s.map,
        &s.policies,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    assert!(observed.native_v1().bindings().protection_signal_observed());
    let error = input(&s.source, &s.map, &s.policies, all_values(&s))
        .err()
        .ok_or("protection unexpectedly accepted")?;
    assert_eq!(
        error.downcast_ref::<NativeFormValueError>(),
        Some(&NativeFormValueError::Access)
    );
    Ok(())
}
#[test]
fn locked_disabled_noneditable_readonly_requested_targets_reject_even_if_one_value_is_a_noop()
-> Result<(), AnyError> {
    for (from, to) in [
        ("enabled=\"1\"", "enabled=\"0\""),
        ("editable=\"1\"", "editable=\"0\""),
        ("readOnly=\"0\"", "readOnly=\"1\""),
        ("protect=\"0\"", "protect=\"1\""),
    ] {
        let mut s = specimen(false)?;
        let mut p = parts(&s.source)?;
        let bytes = part_mut(&mut p, "Contents/section0.xml")?;
        let parsed = PreservingXmlDocument::parse(bytes)?;
        let root = parsed
            .elements()
            .iter()
            .find(|e| e.name().namespace() == Some(HP) && e.name().local_name() == "edit")
            .ok_or("edit")?
            .outer_span()
            .ok_or("span")?;
        let mut text = String::from_utf8(bytes.clone())?;
        let control = text.get(root.start()..root.end()).ok_or("root")?;
        if control.matches(from).count() != 1 {
            return Err("flag source missing".into());
        }
        let changed = control.replace(from, to);
        text.replace_range(root.start()..root.end(), &changed);
        *bytes = text.into_bytes();
        s.source = package(&p)?;
        let native =
            NativeFormPackageReader::read(&s.source, &s.map, NativeFormPackageLimits::default())?;
        s.policies = native
            .sections()
            .flat_map(NativeFormHwpxReadback::controls)
            .map(generic_policy)
            .collect::<Result<_, _>>()?;
        let observed = NativeFormValueReader::read(
            &s.source,
            &s.map,
            &s.policies,
            domain_limits()?,
            NativeFormPackageLimits::default(),
        )?;
        let FormControlPayload::Text { value, .. } = &observed.state().controls()[0].payload else {
            return Err("text kind".into());
        };
        let c = &observed.state().controls()[0];
        match from {
            "enabled=\"1\"" => assert!(!c.common.enabled),
            "editable=\"1\"" => assert!(!c.common.editable),
            "protect=\"0\"" => assert!(c.shape_locked),
            _ => assert!(matches!(
                c.payload,
                FormControlPayload::Text {
                    read_only: true,
                    ..
                }
            )),
        }
        let operation = set(
            &s,
            &[
                (
                    0,
                    FormInputValue::Text {
                        value: value.clone(),
                    },
                ),
                (
                    1,
                    FormInputValue::Checkbox {
                        value: FormButtonValue::Unchecked,
                    },
                ),
            ],
        );
        assert!(input(&s.source, &s.map, &s.policies, operation).is_err());
    }
    Ok(())
}
#[test]
fn external_validator_is_not_executed_or_promoted_and_value_noop_stays_rejected()
-> Result<(), AnyError> {
    let mut s = specimen(false)?;
    let observed = NativeFormValueReader::read(
        &s.source,
        &s.map,
        &s.policies,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let FormControlPayload::Text { value, .. } = &observed.state().controls()[0].payload else {
        return Err("text".into());
    };
    assert!(
        input(
            &s.source,
            &s.map,
            &s.policies,
            set(
                &s,
                &[(
                    0,
                    FormInputValue::Text {
                        value: value.clone()
                    }
                )]
            )
        )
        .is_err()
    );
    if let FormControlPayload::Text { validation, .. } = &mut s.policies[0].payload {
        validation.external_validator_sha256 = Some("a".repeat(64));
    }
    NativeFormValueReader::read(
        &s.source,
        &s.map,
        &s.policies,
        domain_limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let error = input(&s.source, &s.map, &s.policies, all_values(&s))
        .err()
        .ok_or("external validator unexpectedly accepted")?;
    assert_eq!(
        error.downcast_ref::<FormInputError>(),
        Some(&FormInputError::ExternalValidationUnqualified)
    );
    Ok(())
}

#[test]
fn ambiguous_unknown_namespace_text_keeps_original_v1_profile_rejection() -> Result<(), AnyError> {
    let mut s = specimen(false)?;
    let mut p = parts(&s.source)?;
    let raw = part_mut(&mut p, "Contents/section0.xml")?;
    let text = String::from_utf8(raw.clone())?;
    if text
        .matches("<u:payload keep=\"same\">opaque-bytes</u:payload>")
        .count()
        != 5
    {
        return Err("unknown children".into());
    }
    *raw = text
        .replace(
            "<u:payload keep=\"same\">opaque-bytes</u:payload>",
            "<u:text keep=\"same\">opaque-bytes</u:text>",
        )
        .into_bytes();
    s.source = package(&p)?;
    // The immutable v1 reader rejects local-name ambiguity before v2 spans run.
    // Do not normalize/drop the unknown element to manufacture accepted input.
    let p = parts(&s.source)?;
    let section = &p
        .iter()
        .find(|p| p.name == "Contents/section0.xml")
        .ok_or("section")?
        .bytes;
    assert!(matches!(
        NativeFormHwpxReader::read_section(
            section,
            &s.map.sections[0].map,
            NativeFormHwpxLimits::default()
        ),
        Err(NativeFormHwpxError::UnsupportedProfile)
    ));
    assert!(matches!(
        NativeFormValueReader::read(
            &s.source,
            &s.map,
            &s.policies,
            domain_limits()?,
            NativeFormPackageLimits::default()
        ),
        Err(NativeFormValueError::Binding)
    ));
    Ok(())
}

fn artifact_directory(path: &Path) -> Result<std::path::PathBuf, AnyError> {
    use std::path::Component;
    if !path.is_absolute()
        || path
            .components()
            .any(|c| matches!(c, Component::ParentDir | Component::CurDir))
    {
        return Err("component artifact path rejected".into());
    }
    for ancestor in path.ancestors() {
        let m = fs::symlink_metadata(ancestor)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("component artifact reparse rejected".into());
            }
        }
        if m.file_type().is_symlink() {
            return Err("component artifact link rejected".into());
        }
    }
    let base = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?
        .join("fixtures/target-build")
        .canonicalize()?;
    let resolved = path.canonicalize()?;
    let name = resolved
        .file_name()
        .and_then(|n| n.to_str())
        .ok_or("component directory name")?;
    if resolved.parent() != Some(base.as_path())
        || !name.starts_with("p09-40-component-")
        || !name
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
        || !resolved.is_dir()
    {
        return Err("component artifact boundary rejected".into());
    }
    Ok(resolved)
}
fn emit_component_bundle(rows: &[(&str, Vec<u8>, NativeFormValueOutput)]) -> Result<(), AnyError> {
    let Some(raw) = std::env::var_os("HWPX_P09_40_COMPONENT_ARTIFACT_DIR") else {
        return Ok(());
    };
    let dir = artifact_directory(Path::new(&raw))?;
    if fs::read_dir(&dir)?.next().is_some() {
        return Err("component directory not empty".into());
    }
    let mut records = Vec::new();
    let mut total = 0usize;
    for (case, source, output) in rows {
        let mut files = Vec::new();
        for (label, bytes) in [("source", source.as_slice()), ("output", output.bytes())] {
            total = total
                .checked_add(bytes.len())
                .filter(|n| *n <= 1024 * 1024)
                .ok_or("component bundle limit")?;
            let name = format!("{case}-{label}.hwpx");
            fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(dir.join(&name))?
                .write_all(bytes)?;
            files.push(serde_json::json!({"path":name,"sha256":hex(&Sha256::digest(bytes)),"bytes":bytes.len()}));
        }
        records.push(serde_json::json!({"case":case,"source":files[0],"output":files[1],"receipt":output.receipt()}));
    }
    let manifest = serde_json::to_vec(&serde_json::json!({
        "schema_version":"hwpx-agent.p09-40-managed-value-component-bundle/v1", "profile":NATIVE_FORM_VALUE_PROFILE, "cases":records
    }))?;
    if manifest.len() > 64 * 1024 {
        return Err("component manifest limit".into());
    }
    fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(dir.join("fixture-manifest.json"))?
        .write_all(&manifest)?;
    println!(
        "P09_40_COMPONENT_BUNDLE_PROBE={}",
        serde_json::json!({"cases":rows.len(),"files":rows.len()*2+1,"manifest_sha256":hex(&Sha256::digest(&manifest)),"artifact_bytes":total+manifest.len(),"native_session_started":false})
    );
    Ok(())
}
type ComponentFixtureRow = (&'static str, Vec<u8>, NativeFormValueOutput);
fn component_bundle() -> Result<Vec<ComponentFixtureRow>, AnyError> {
    let actual = capture()?;
    let map = actual_map(&actual)?;
    let native = NativeFormPackageReader::read(&actual, &map, NativeFormPackageLimits::default())?;
    let policies = vec![policy(
        &native.sections().next().ok_or("section")?.controls()[0],
    )?];
    let operation = FormInputOperation::SetValues {
        assignments: vec![FormInputAssignment {
            target: policies[0].identity.clone(),
            value: FormInputValue::Text {
                value: "P40 값 & <한글> \" ' 🚀".into(),
            },
        }],
    };
    let (plan, access, _) = input(&actual, &map, &policies, operation)?;
    let output = lower(&actual, &plan, &access)?;
    assert_complete(&actual, &output, &plan, &access)?;
    let matrix = specimen(false)?;
    let (plan, access, target) = input(
        &matrix.source,
        &matrix.map,
        &matrix.policies,
        all_values(&matrix),
    )?;
    let changed = lower(&matrix.source, &plan, &access)?;
    assert_complete(&matrix.source, &changed, &plan, &access)?;
    let empty = specimen(true)?;
    let (plan, access, _) = input(
        &empty.source,
        &empty.map,
        &empty.policies,
        set(
            &empty,
            &[(
                0,
                FormInputValue::Text {
                    value: "value & 🚀".into(),
                },
            )],
        ),
    )?;
    let expanded = lower(&empty.source, &plan, &access)?;
    assert_complete(&empty.source, &expanded, &plan, &access)?;
    let reset_source = changed.bytes().to_vec();
    let policies = output_policies(target.target_state());
    let reset_operation = FormInputOperation::ResetDefaults {
        targets: policies.iter().map(|p| p.identity.clone()).collect(),
    };
    let (plan, access, _) = input(&reset_source, &matrix.map, &policies, reset_operation)?;
    let reset = lower(&reset_source, &plan, &access)?;
    assert_complete(&reset_source, &reset, &plan, &access)?;
    let (plan, access, _) = input(
        &matrix.source,
        &matrix.map,
        &matrix.policies,
        set(
            &matrix,
            &[
                (
                    3,
                    FormInputValue::Combo {
                        selected_value: None,
                    },
                ),
                (
                    4,
                    FormInputValue::List {
                        selected_value: None,
                    },
                ),
            ],
        ),
    )?;
    let cleared = lower(&matrix.source, &plan, &access)?;
    assert_complete(&matrix.source, &cleared, &plan, &access)?;
    Ok(vec![
        ("actual", actual, output),
        ("five-kinds", matrix.source.clone(), changed),
        ("empty-text", empty.source, expanded),
        ("reset-defaults", reset_source, reset),
        ("clear-selections", matrix.source, cleared),
    ])
}
#[test]
fn five_complete_component_fixture_pairs_are_real_retry_verified_and_not_native_candidates()
-> Result<(), AnyError> {
    let rows = component_bundle()?;
    assert_eq!(rows.len(), 5);
    for (_, source, output) in &rows {
        assert_ne!(source, output.bytes());
    }
    emit_component_bundle(&rows)?;
    Ok(())
}
#[test]
fn component_artifact_directory_rejects_relative_nested_traversal_and_wrong_prefix()
-> Result<(), AnyError> {
    let base = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()?
        .join("fixtures/target-build")
        .canonicalize()?;
    let temporary = tempfile::Builder::new()
        .prefix("p09-40-component-")
        .tempdir_in(&base)?;
    assert_eq!(
        artifact_directory(temporary.path())?,
        temporary.path().canonicalize()?
    );
    assert!(artifact_directory(Path::new("relative")).is_err());
    assert!(artifact_directory(&base).is_err());
    let wrong = tempfile::Builder::new()
        .prefix("p09-40-wrong-")
        .tempdir_in(&base)?;
    assert!(artifact_directory(wrong.path()).is_err());
    let nested = tempfile::Builder::new()
        .prefix("p09-40-component-")
        .tempdir_in(temporary.path())?;
    assert!(artifact_directory(nested.path()).is_err());
    assert!(
        artifact_directory(Path::new(&format!(
            "{}{sep}..{sep}{}",
            temporary.path().display(),
            temporary
                .path()
                .file_name()
                .ok_or("name")?
                .to_str()
                .ok_or("name")?,
            sep = std::path::MAIN_SEPARATOR
        )))
        .is_err()
    );
    Ok(())
}
