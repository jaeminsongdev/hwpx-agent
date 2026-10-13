//! Actual production global package lowerer through unchanged frozen public dependencies.
pub use hwpx_package::*;
#[path = "../src/native_form_package.rs"]
mod native_form_package;
use domain_ir::*;
use native_form_package::*;
#[path = "../src/native_form_package_lowering.rs"]
mod native_form_package_lowering;
use native_form_package_lowering::*;
use sha2::{Digest as _, Sha256};
use std::{
    collections::BTreeMap,
    error::Error,
    fs,
    io::{Cursor, Read as _, Write as _},
    path::Path,
};
use zip::{CompressionMethod, ZipArchive, ZipWriter, write::SimpleFileOptions};

type AnyError = Box<dyn Error>;
const CAPTURE: &str = "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx";
const CAPTURE_SHA: &str = "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7";
fn sha(raw: &[u8]) -> String {
    hex::encode(Sha256::digest(raw))
}
fn capture() -> Result<Vec<u8>, AnyError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(CAPTURE);
    for ancestor in path.ancestors() {
        let m = fs::symlink_metadata(ancestor)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("capture reparse refused".into());
            }
        }
        if m.file_type().is_symlink() {
            return Err("capture link refused".into());
        }
    }
    if fs::metadata(&path)?.len() != 14556 {
        return Err("capture size changed".into());
    }
    let raw = fs::read(path)?;
    if raw.len() != 14556 || sha(&raw) != CAPTURE_SHA {
        return Err("capture source identity changed".into());
    }
    Ok(raw)
}
fn parts(raw: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, AnyError> {
    let mut zip = ZipArchive::new(Cursor::new(raw))?;
    let mut out = BTreeMap::new();
    for i in 0..zip.len() {
        let mut entry = zip.by_index(i)?;
        let mut value = Vec::new();
        entry.read_to_end(&mut value)?;
        out.insert(entry.name().into(), value);
    }
    Ok(out)
}
fn package(parts: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>, AnyError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    writer.start_file(
        "mimetype",
        SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
    )?;
    writer.write_all(parts.get("mimetype").ok_or("mimetype")?)?;
    for (path, raw) in parts {
        if path != "mimetype" {
            writer.start_file(
                path,
                SimpleFileOptions::default().compression_method(CompressionMethod::Deflated),
            )?;
            writer.write_all(raw)?;
        }
    }
    Ok(writer.finish()?.into_inner())
}
fn map(count: usize) -> Result<NativeFormPackageMap, AnyError> {
    Ok(NativeFormPackageMap {
        sections: (0..count)
            .map(|i| {
                Ok(NativeFormPackageSectionMap {
                    part: format!("Contents/section{i}.xml"),
                    map: NativeFormHwpxMap {
                        paragraph_ids: (0..2)
                            .map(|j| LogicalId::parse(format!("section-{i}-paragraph-{j}")))
                            .collect::<Result<_, _>>()?,
                        component_controls: vec![FormControlIdentity {
                            logical_control_id: LogicalId::parse(format!("section-{i}-control"))?,
                            native_object_id: 90001 + u32::try_from(i)?,
                        }],
                    },
                })
            })
            .collect::<Result<_, AnyError>>()?,
    })
}
fn limits() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
}
fn observe(raw: &[u8], count: usize) -> Result<NativeFormPackageReadback, AnyError> {
    Ok(NativeFormPackageReader::read(
        raw,
        &map(count)?,
        NativeFormPackageLimits::default(),
    )?)
}
// Explicit test policy. Native XML has not established defaults or validation behavior.
fn policies(
    observed: &NativeFormPackageReadback,
) -> Result<Vec<NativeFormPackagePolicy>, AnyError> {
    observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| {
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
                return Err("test policy supports captured edits only".into());
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload: FormControlPayload::Text {
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
            })
        })
        .collect()
}
fn domain_plan(
    observed: &NativeFormPackageReadback,
    operation: FormControlOperation,
    flow: &str,
) -> Result<FormControlPlan, AnyError> {
    let state = observed.bind_policies(&policies(observed)?, limits()?)?;
    let request = FormControlRequest::from_draft(
        FormControlRequestDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("package-test-request")?,
            expected_source_state_sha256: state.canonical_sha256(limits()?)?,
            expected_document_flow_sha256: flow.into(),
            target_document_flow_sha256: flow.into(),
            operation,
        },
        &state,
        flow,
        limits()?,
    )?;
    Ok(FormControlBuilder::plan(&state, &request, flow, limits()?)?)
}
fn property(observed: &NativeFormPackageReadback) -> Result<FormControlOperation, AnyError> {
    let state = observed.bind_policies(&policies(observed)?, limits()?)?;
    let c = &state.controls()[0];
    let mut common = c.common.clone();
    common.enabled = !common.enabled;
    Ok(FormControlOperation::ReplaceProperties {
        target: c.identity.clone(),
        common,
        payload: c.payload.clone(),
    })
}
fn multi() -> Result<Vec<u8>, AnyError> {
    let original = capture()?;
    let observed = observe(&original, 1)?;
    let mut p = parts(&original)?;
    let section = String::from_utf8(p.get("Contents/section0.xml").ok_or("section")?.clone())?;
    let field = &observed.sections().next().ok_or("section")?.controls()[0]
        .common
        .name;
    let second = section
        .replace("<hp:p id=\"0\"", "<hp:p id=\"10\"")
        .replace("<hp:p id=\"1\"", "<hp:p id=\"11\"")
        .replace(
            &format!("name=\"{field}\""),
            "name=\"second-native-derived-field\"",
        )
        .replace("tabOrder=\"1\"", "tabOrder=\"2\"");
    p.insert("Contents/section1.xml".into(), second.into_bytes());
    let header = String::from_utf8(p.get("Contents/header.xml").ok_or("header")?.clone())?
        .replace("secCnt=\"1\"", "secCnt=\"2\"");
    p.insert("Contents/header.xml".into(), header.into_bytes());
    let opf = String::from_utf8(p.get("Contents/content.hpf").ok_or("opf")?.clone())?;
    let prefix = if opf.contains("</opf:manifest>") {
        "opf:"
    } else {
        ""
    };
    let changed = opf.replace(&format!("</{prefix}manifest>"), &format!("<{prefix}item id=\"section1\" href=\"section1.xml\" media-type=\"application/xml\"/></{prefix}manifest>"))
        .replace(&format!("</{prefix}spine>"), &format!("<{prefix}itemref idref=\"section1\" linear=\"yes\"/></{prefix}spine>"));
    if changed == opf {
        return Err("derived section manifest not changed".into());
    }
    p.insert("Contents/content.hpf".into(), changed.into_bytes());
    package(&p)
}

fn output_plan(
    raw: &[u8],
    count: usize,
    operation: FormControlOperation,
) -> Result<NativeFormPackageOutputPlan, AnyError> {
    let observed = observe(raw, count)?;
    let domain = domain_plan(&observed, operation, observed.document_flow_sha256())?;
    Ok(NativeFormPackageOutputPlan::bind(
        raw,
        &map(count)?,
        &policies(&observed)?,
        &domain,
        limits()?,
        NativeFormPackageLimits::default(),
    )?)
}
fn lower(
    raw: &[u8],
    plan: &NativeFormPackageOutputPlan,
) -> Result<NativeFormPackageOutput, AnyError> {
    Ok(NativeFormPackageLowerer::lower(
        raw,
        plan,
        limits()?,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )?)
}
fn checked(raw: &[u8], plan: &NativeFormPackageOutputPlan, output: &[u8]) -> bool {
    let Ok(domain_limits) = limits() else {
        return false;
    };
    NativeFormPackageLowerer::verify_output(
        raw,
        plan,
        output,
        domain_limits,
        NativeFormPackageLimits::default(),
        NativeFormPackageOutputLimits::default(),
    )
    .is_ok()
}
fn tab(
    observed: &NativeFormPackageReadback,
    disable_first: bool,
) -> Result<FormControlOperation, AnyError> {
    let state = observed.bind_policies(&policies(observed)?, limits()?)?;
    Ok(FormControlOperation::SetTabOrder {
        assignments: state
            .controls()
            .iter()
            .enumerate()
            .map(|(i, c)| {
                Ok(FormTabAssignment {
                    target: c.identity.clone(),
                    tab_stop: !(disable_first && i == 0),
                    tab_order: if disable_first && i == 0 {
                        None
                    } else {
                        Some(if disable_first {
                            0
                        } else {
                            u32::try_from(state.controls().len() - 1 - i)?
                        })
                    },
                })
            })
            .collect::<Result<Vec<_>, AnyError>>()?,
    })
}
fn changed_part(raw: &[u8], path: &str, from: &str, to: &str) -> Result<Vec<u8>, AnyError> {
    let mut p = parts(raw)?;
    let before = String::from_utf8(p.get(path).ok_or("part")?.clone())?;
    let after = before.replace(from, to);
    if before == after {
        return Err("fixture mutation did not occur".into());
    }
    p.insert(path.into(), after.into_bytes());
    package(&p)
}
fn state_plan(
    observed: &NativeFormPackageReadback,
    policies: &[NativeFormPackagePolicy],
    operation: FormControlOperation,
    target_flow: &str,
) -> Result<FormControlPlan, AnyError> {
    let state = observed.bind_policies(policies, limits()?)?;
    let request = FormControlRequest::from_draft(
        FormControlRequestDraft {
            schema_version: FORM_CONTROL_SCHEMA_VERSION.into(),
            request_id: LogicalId::parse("global-output-test")?,
            expected_source_state_sha256: state.canonical_sha256(limits()?)?,
            expected_document_flow_sha256: observed.document_flow_sha256().into(),
            target_document_flow_sha256: target_flow.into(),
            operation,
        },
        &state,
        observed.document_flow_sha256(),
        limits()?,
    )?;
    Ok(FormControlBuilder::plan(
        &state,
        &request,
        observed.document_flow_sha256(),
        limits()?,
    )?)
}

// Optional exclusive temporary artifacts for the independent Python package oracle.
// No output or private directory is printed; ordinary tests remain memory-only.
fn oracle_artifact(name: &str, bytes: &[u8]) -> Result<(), AnyError> {
    let Some(directory) = std::env::var_os("HWPX_AGENT_P09_30_ORACLE_DIRECTORY") else {
        return Ok(());
    };
    let directory = Path::new(&directory);
    if !directory.is_absolute() || !directory.is_dir() || bytes.len() > 32 * 1024 * 1024 {
        return Err("oracle artifact boundary invalid".into());
    }
    for ancestor in directory.ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("oracle artifact reparse refused".into());
            }
        }
        if metadata.file_type().is_symlink() {
            return Err("oracle artifact link refused".into());
        }
    }
    let mut handle = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(directory.join(name))?;
    handle.write_all(bytes)?;
    handle.sync_all()?;
    Ok(())
}

#[test]
fn actual_property_output_reopens_complete_package_and_changes_only_declared_attribute()
-> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let plan = output_plan(&raw, 1, property(&seen)?)?;
    let output = lower(&raw, &plan)?;
    assert_eq!(seen.section_count(), 1);
    assert!(!seen.bindings().protection_signal_observed());
    assert!(!seen.bindings().canonical_json()?.is_empty());
    let before = parts(&raw)?;
    let after = parts(output.bytes())?;
    assert_eq!(before.len(), after.len());
    for (part, bytes) in &before {
        if part == "Contents/section0.xml" {
            let expected =
                String::from_utf8(bytes.clone())?.replace("enabled=\"1\"", "enabled=\"0\"");
            assert_eq!(
                after.get(part).ok_or("output section")?,
                expected.as_bytes()
            );
        } else {
            assert_eq!(after.get(part).ok_or("output part")?, bytes);
        }
    }
    let receipt = output.receipt();
    assert_eq!(receipt.changed_sections, 1);
    assert_eq!(receipt.changed_attributes, 1);
    assert!(receipt.outside_declared_edits_byte_exact);
    assert!(receipt.non_section_parts_expanded_byte_exact);
    assert!(receipt.entry_order_and_compression_preserved);
    assert_eq!(receipt.zip_header_policy, "rewritten_not_byte_exact");
    assert_eq!(receipt.legacy_reference_state, "id_index_validation_failed");
    assert_eq!(receipt.verified_native_reference_overlay_issues, 2);
    assert!(checked(&raw, &plan, output.bytes()));
    assert_eq!(sha(&capture()?), CAPTURE_SHA);
    oracle_artifact("actual-property-source.hwpx", &raw)?;
    oracle_artifact("actual-property-output.hwpx", output.bytes())?;
    // Hashes/counts only, for a separate independent actual package oracle.
    println!(
        "p09_30_probe_json={}",
        serde_json::json!({ "profile": receipt.profile, "source_package_sha256": receipt.source_package_sha256,
            "output_package_sha256": receipt.output_package_sha256, "document_flow_sha256": receipt.document_flow_sha256,
            "changed_sections": receipt.changed_sections, "changed_attributes": receipt.changed_attributes,
            "non_section_parts_expanded_byte_exact": receipt.non_section_parts_expanded_byte_exact,
            "outside_declared_edits_byte_exact": receipt.outside_declared_edits_byte_exact,
            "entry_order_and_compression_preserved": receipt.entry_order_and_compression_preserved,
            "zip_header_policy": receipt.zip_header_policy, "legacy_reference_state": receipt.legacy_reference_state,
            "verified_native_reference_overlay_issues": receipt.verified_native_reference_overlay_issues,
            "output_section_sha256": sha(after.get("Contents/section0.xml").ok_or("section")?) })
    );
    Ok(())
}
#[test]
fn global_tab_reordering_respects_document_order_without_local_contiguity_assumption()
-> Result<(), AnyError> {
    let raw = multi()?;
    let seen = observe(&raw, 2)?;
    let plan = output_plan(&raw, 2, tab(&seen, false)?)?;
    let output = lower(&raw, &plan)?;
    let observed = observe(output.bytes(), 2)?;
    let actual: Vec<_> = observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| c.common.tab_order)
        .collect();
    assert_eq!(actual, vec![Some(1), Some(0)]);
    assert_eq!(output.receipt().changed_sections, 1); // First source order was already 1.
    assert_eq!(output.receipt().changed_attributes, 1);
    assert!(checked(&raw, &plan, output.bytes()));
    oracle_artifact("global-tab-source.hwpx", &raw)?;
    oracle_artifact("global-tab-output.hwpx", output.bytes())?;
    Ok(())
}
#[test]
fn global_tab_can_disable_one_section_while_enabling_other_global_zero() -> Result<(), AnyError> {
    let raw = multi()?;
    let seen = observe(&raw, 2)?;
    let plan = output_plan(&raw, 2, tab(&seen, true)?)?;
    let output = lower(&raw, &plan)?;
    let observed = observe(output.bytes(), 2)?;
    let actual: Vec<_> = observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| (c.common.tab_stop, c.common.tab_order))
        .collect();
    assert_eq!(actual, vec![(false, None), (true, Some(0))]);
    assert_eq!(output.receipt().changed_sections, 2);
    assert_eq!(output.receipt().changed_attributes, 3);
    oracle_artifact("disabled-tab-source.hwpx", &raw)?;
    oracle_artifact("disabled-tab-output.hwpx", output.bytes())?;
    Ok(())
}
#[test]
fn properties_change_all_supported_common_and_character_values_with_literal_escaping()
-> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let state = seen.bind_policies(&policies(&seen)?, limits()?)?;
    let control = &state.controls()[0];
    let mut common = control.common.clone();
    common.name = "새 폼 & <\"'>".into();
    common.group_name = Some("글로벌 & <\"'>".into());
    common.fore_color_rgb = 0x0012_3456;
    common.back_color_rgb = 0x0065_4321;
    common.editable = false;
    common.enabled = false;
    common.draw_frame = false;
    common.printable = false;
    common.tab_stop = false;
    common.tab_order = None;
    common.character.follow_context = !common.character.follow_context;
    common.character.auto_size = !common.character.auto_size;
    common.character.word_wrap = !common.character.word_wrap;
    let plan = output_plan(
        &raw,
        1,
        FormControlOperation::ReplaceProperties {
            target: control.identity.clone(),
            common: common.clone(),
            payload: control.payload.clone(),
        },
    )?;
    let output = lower(&raw, &plan)?;
    let output_observed = observe(output.bytes(), 1)?;
    let c = &output_observed
        .sections()
        .next()
        .ok_or("section")?
        .controls()[0];
    assert_eq!(c.common, common);
    assert_eq!(c.native_identity, NativeFormObservedIdentity::Missing);
    assert_eq!(output.receipt().changed_attributes, 13);
    let changed = parts(output.bytes())?;
    let section = std::str::from_utf8(changed.get("Contents/section0.xml").ok_or("section")?)?;
    assert!(section.contains("&amp; &lt;&quot;&apos;&gt;"));
    assert!(!section.contains("id=\"90001\""));
    Ok(())
}
#[test]
fn optional_missing_group_attribute_is_inserted_without_other_start_tag_normalization()
-> Result<(), AnyError> {
    let mut p = parts(&capture()?)?;
    let original = String::from_utf8(p.get("Contents/section0.xml").ok_or("section")?.clone())?;
    let no_group = original.replace(" groupName=\"\"", "");
    p.insert(
        "Contents/section0.xml".into(),
        no_group.clone().into_bytes(),
    );
    let raw = package(&p)?;
    let seen = observe(&raw, 1)?;
    let state = seen.bind_policies(&policies(&seen)?, limits()?)?;
    let c = &state.controls()[0];
    let mut common = c.common.clone();
    common.group_name = Some("group&literal".into());
    let plan = output_plan(
        &raw,
        1,
        FormControlOperation::ReplaceProperties {
            target: c.identity.clone(),
            common,
            payload: c.payload.clone(),
        },
    )?;
    let output = lower(&raw, &plan)?;
    let output_parts = parts(output.bytes())?;
    let changed = String::from_utf8(
        output_parts
            .get("Contents/section0.xml")
            .ok_or("section")?
            .clone(),
    )?;
    assert_eq!(
        changed.replace(" groupName=\"group&amp;literal\"", ""),
        no_group
    );
    assert_eq!(output.receipt().changed_attributes, 1);
    Ok(())
}
#[test]
fn unchanged_noncanonical_lexical_attributes_and_single_quotes_remain_byte_exact()
-> Result<(), AnyError> {
    let raw = changed_part(
        &capture()?,
        "Contents/section0.xml",
        "foreColor=\"#000000\"",
        "foreColor='#000000'",
    )?;
    let raw = changed_part(
        &raw,
        "Contents/section0.xml",
        "borderTypeIDRef=\"0\"",
        "borderTypeIDRef='&#48;'",
    )?;
    let seen = observe(&raw, 1)?;
    let plan = output_plan(&raw, 1, property(&seen)?)?;
    let output = lower(&raw, &plan)?;
    let source_parts = parts(&raw)?;
    let target_parts = parts(output.bytes())?;
    let expected = String::from_utf8(
        source_parts
            .get("Contents/section0.xml")
            .ok_or("section")?
            .clone(),
    )?
    .replace("enabled=\"1\"", "enabled=\"0\"");
    assert_eq!(
        target_parts.get("Contents/section0.xml").ok_or("section")?,
        expected.as_bytes()
    );
    assert_eq!(output.receipt().changed_attributes, 1);
    Ok(())
}
#[test]
fn stale_source_header_preview_or_body_cannot_reuse_output_plan() -> Result<(), AnyError> {
    let raw = capture()?;
    let plan = output_plan(&raw, 1, property(&observe(&raw, 1)?)?)?;
    let mut source_parts = parts(&raw)?;
    for part in [
        "Contents/header.xml",
        "Preview/PrvText.txt",
        "Contents/section0.xml",
    ] {
        let original = source_parts.get(part).ok_or("part")?.clone();
        let mut altered = original.clone();
        altered.extend_from_slice(b" ");
        source_parts.insert(part.into(), altered);
        let mutated = package(&source_parts)?;
        assert!(matches!(
            NativeFormPackageLowerer::lower(
                &mutated,
                &plan,
                limits()?,
                NativeFormPackageLimits::default(),
                NativeFormPackageOutputLimits::default()
            ),
            Err(NativeFormPackageOutputError::Binding)
        ));
        source_parts.insert(part.into(), original);
    }
    Ok(())
}
#[test]
fn external_output_verifier_rejects_each_changed_nonsection_part_and_target_substitution()
-> Result<(), AnyError> {
    let raw = capture()?;
    let plan = output_plan(&raw, 1, property(&observe(&raw, 1)?)?)?;
    let output = lower(&raw, &plan)?;
    let p = parts(output.bytes())?;
    for part in p.keys() {
        let mut changed = p.clone();
        let bytes = changed.get_mut(part).ok_or("part")?;
        bytes.push(b' ');
        assert!(!checked(&raw, &plan, &package(&changed)?));
    }
    assert!(!checked(&raw, &plan, &raw)); // Original state is not the requested output.
    let replaced = changed_part(
        output.bytes(),
        "Contents/section0.xml",
        "enabled=\"0\"",
        "enabled=\"1\"",
    )?;
    assert!(!checked(&raw, &plan, &replaced));
    Ok(())
}
#[test]
fn external_output_verifier_rejects_extra_missing_order_and_compression_changes()
-> Result<(), AnyError> {
    let raw = capture()?;
    let plan = output_plan(&raw, 1, property(&observe(&raw, 1)?)?)?;
    let output = lower(&raw, &plan)?;
    let p = parts(output.bytes())?;
    let mut extra = p.clone();
    extra.insert("Unlisted/new.bin".into(), b"not approved".to_vec());
    assert!(!checked(&raw, &plan, &package(&extra)?));
    let mut missing = p.clone();
    missing.remove("Preview/PrvImage.png");
    assert!(!checked(&raw, &plan, &package(&missing)?));
    // Same expanded bytes but sorted order (different from preserved original) is not admitted.
    assert!(!checked(&raw, &plan, &package(&p)?));
    let mut source_zip = ZipArchive::new(Cursor::new(output.bytes()))?;
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..source_zip.len() {
        let entry = source_zip.by_index(i)?;
        let name = entry.name().to_owned();
        let original = entry.compression();
        writer.start_file(
            &name,
            SimpleFileOptions::default().compression_method(if name == "Preview/PrvText.txt" {
                CompressionMethod::Stored
            } else {
                original
            }),
        )?;
        writer.write_all(p.get(&name).ok_or("part")?)?;
    }
    assert!(!checked(&raw, &plan, &writer.finish()?.into_inner()));
    Ok(())
}
#[test]
fn payload_default_validation_and_command_changes_are_not_silently_dropped() -> Result<(), AnyError>
{
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let state = seen.bind_policies(&policies(&seen)?, limits()?)?;
    let c = &state.controls()[0];
    let mut payload_value = c.payload.clone();
    if let FormControlPayload::Text { value, .. } = &mut payload_value {
        *value = "different-native-value".into();
    }
    let mut payload_default = c.payload.clone();
    if let FormControlPayload::Text { default_value, .. } = &mut payload_default {
        *default_value = "different-explicit-default".into();
    }
    let mut payload_validation = c.payload.clone();
    if let FormControlPayload::Text { validation, .. } = &mut payload_validation {
        validation.minimum_characters = 1;
    }
    for payload in [payload_value, payload_default, payload_validation] {
        let mut common = c.common.clone();
        common.enabled = false;
        let operation = FormControlOperation::ReplaceProperties {
            target: c.identity.clone(),
            common,
            payload,
        };
        let Err(error) = output_plan(&raw, 1, operation) else {
            return Err("unsupported payload change accepted".into());
        };
        assert!(matches!(
            error.downcast_ref::<NativeFormPackageOutputError>(),
            Some(NativeFormPackageOutputError::NonRepresentable)
        ));
    }
    let mut common = c.common.clone();
    common.command_sha256 = Some("a1".repeat(32));
    let operation = FormControlOperation::ReplaceProperties {
        target: c.identity.clone(),
        common,
        payload: c.payload.clone(),
    };
    assert!(output_plan(&raw, 1, operation).is_err());
    Ok(())
}
#[test]
fn changed_target_flow_and_insertion_are_rejected_not_reinterpreted() -> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let domain = state_plan(&seen, &policies(&seen)?, property(&seen)?, &"a1".repeat(32))?;
    assert!(matches!(
        NativeFormPackageOutputPlan::bind(
            &raw,
            &map(1)?,
            &policies(&seen)?,
            &domain,
            limits()?,
            NativeFormPackageLimits::default()
        ),
        Err(NativeFormPackageOutputError::NonRepresentable)
    ));
    let state = seen.bind_policies(&policies(&seen)?, limits()?)?;
    let c = &state.controls()[0];
    let mut inserted = c.clone();
    inserted.identity = FormControlIdentity {
        logical_control_id: LogicalId::parse("unimplemented-insert")?,
        native_object_id: 90002,
    };
    inserted.common.name = "unimplemented insert".into();
    inserted.common.tab_stop = false;
    inserted.common.tab_order = None;
    inserted.anchor.inline_ordinal += 1;
    let operation = FormControlOperation::Insert {
        insertion_index: 1,
        control: inserted,
    };
    assert!(output_plan(&raw, 1, operation).is_err());
    Ok(())
}
#[test]
fn complete_map_policy_character_border_and_protection_admission_still_fail_closed()
-> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let domain = domain_plan(&seen, property(&seen)?, seen.document_flow_sha256())?;
    let mut missing = map(1)?;
    missing.sections[0].map.paragraph_ids.pop();
    assert!(
        NativeFormPackageOutputPlan::bind(
            &raw,
            &missing,
            &policies(&seen)?,
            &domain,
            limits()?,
            NativeFormPackageLimits::default()
        )
        .is_err()
    );
    assert!(
        NativeFormPackageOutputPlan::bind(
            &raw,
            &map(1)?,
            &[],
            &domain,
            limits()?,
            NativeFormPackageLimits::default()
        )
        .is_err()
    );
    let state = seen.bind_policies(&policies(&seen)?, limits()?)?;
    let c = &state.controls()[0];
    for border in [false, true] {
        let mut common = c.common.clone();
        if border {
            common.border_type_id_ref = 1;
        } else {
            common.character.char_pr_id_ref = 900_000;
        }
        assert!(
            output_plan(
                &raw,
                1,
                FormControlOperation::ReplaceProperties {
                    target: c.identity.clone(),
                    common,
                    payload: c.payload.clone()
                }
            )
            .is_err()
        );
    }
    let protected = changed_part(
        &raw,
        "settings.xml",
        "</ha:HWPApplicationSetting>",
        "<ha:passwordProtect/></ha:HWPApplicationSetting>",
    )?;
    assert!(
        NativeFormPackageOutputPlan::bind(
            &protected,
            &map(1)?,
            &policies(&seen)?,
            &domain,
            limits()?,
            NativeFormPackageLimits::default()
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn finite_archive_part_total_bounds_fail_without_returning_partial_artifacts()
-> Result<(), AnyError> {
    let raw = capture()?;
    let plan = output_plan(&raw, 1, property(&observe(&raw, 1)?)?)?;
    assert_eq!(
        NativeFormPackageLimits::new(32 * 1024 * 1024, 256, 2 * 1024 * 1024, 16 * 1024 * 1024, 64)?,
        NativeFormPackageLimits::default()
    );
    for bounded in [
        NativeFormPackageOutputLimits::new(64, 2 * 1024 * 1024, 16 * 1024 * 1024)?,
        NativeFormPackageOutputLimits::new(32 * 1024 * 1024, 100, 16 * 1024 * 1024)?,
        NativeFormPackageOutputLimits::new(32 * 1024 * 1024, 42000, 42000)?,
    ] {
        assert!(matches!(
            NativeFormPackageLowerer::lower(
                &raw,
                &plan,
                limits()?,
                NativeFormPackageLimits::default(),
                bounded
            ),
            Err(NativeFormPackageOutputError::Limit)
        ));
    }
    for values in [
        (0, 1, 1),
        (1, 0, 1),
        (1, 2, 1),
        (MAX_TEST_ARCHIVE + 1, 1, 1),
        (1, 2 * 1024 * 1024 + 1, 16 * 1024 * 1024),
        (1, 1, 16 * 1024 * 1024 + 1),
    ] {
        assert!(NativeFormPackageOutputLimits::new(values.0, values.1, values.2).is_err());
    }
    let output = lower(&raw, &plan)?;
    let exact = NativeFormPackageOutputLimits::new(
        output.bytes().len(),
        2 * 1024 * 1024,
        16 * 1024 * 1024,
    )?;
    assert_eq!(
        NativeFormPackageLowerer::lower(
            &raw,
            &plan,
            limits()?,
            NativeFormPackageLimits::default(),
            exact
        )?
        .bytes(),
        output.bytes()
    );
    Ok(())
}
const MAX_TEST_ARCHIVE: usize = 32 * 1024 * 1024;
#[test]
fn debug_errors_and_public_receipt_expose_no_document_text_or_private_paths() -> Result<(), AnyError>
{
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let private_name = seen.sections().next().ok_or("section")?.controls()[0]
        .common
        .name
        .clone();
    let plan = output_plan(&raw, 1, property(&seen)?)?;
    let output = lower(&raw, &plan)?;
    let public = format!(
        "{plan:?} {output:?} {}",
        serde_json::to_string(output.receipt())?
    );
    for private in [private_name.as_str(), CAPTURE, "P08FORMINSERT", "D:\\"] {
        assert!(!public.contains(private));
    }
    assert_eq!(
        NativeFormPackageOutputError::Binding.to_string(),
        "NATIVE_FORM_OUTPUT_BINDING_REJECTED"
    );
    Ok(())
}
#[test]
fn cross_section_required_radio_group_is_validated_globally_during_actual_output()
-> Result<(), AnyError> {
    let mut p = parts(&multi()?)?;
    for i in 0..2 {
        let part = format!("Contents/section{i}.xml");
        let source = String::from_utf8(p.get(&part).ok_or("section")?.clone())?;
        let start = source.find("<hp:edit ").ok_or("edit")?;
        let end = source.find("</hp:edit>").ok_or("end")? + "</hp:edit>".len();
        let edit = &source[start..end];
        let geometry =
            &edit[edit.find("<hp:sz ").ok_or("geometry")?..edit.len() - "</hp:edit>".len()];
        let value = if i == 0 { "CHECKED" } else { "UNCHECKED" };
        let radio = format!(
            "<hp:radioBtn name=\"radio-{i}\" foreColor=\"#000000\" backColor=\"#FFFFFF\" groupName=\"\" tabStop=\"1\" editable=\"1\" tabOrder=\"{}\" enabled=\"1\" borderTypeIDRef=\"0\" drawFrame=\"1\" printable=\"1\" command=\"\" caption=\"radio\" value=\"{value}\" radioGroupName=\"complete-group\" triState=\"0\" backStyle=\"TRANSPARENT\"><hp:formCharPr charPrIDRef=\"0\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/>{geometry}</hp:radioBtn>",
            i + 1
        );
        p.insert(
            part,
            format!("{}{radio}{}", &source[..start], &source[end..]).into_bytes(),
        );
    }
    let raw = package(&p)?;
    let observed = observe(&raw, 2)?;
    let policies = observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| {
            let NativeFormObservedPayload::Button {
                caption,
                value,
                radio_group_name,
                tri_state,
                back_style,
            } = &c.payload
            else {
                return Err("radio observation".into());
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload: FormControlPayload::Radio {
                    caption: caption.clone(),
                    value: *value,
                    default_value: *value,
                    radio_group_name: radio_group_name.clone().ok_or("group")?,
                    group_required: true,
                    tri_state: *tri_state,
                    back_style: *back_style,
                },
            })
        })
        .collect::<Result<Vec<_>, AnyError>>()?;
    let state = observed.bind_policies(&policies, limits()?)?;
    let assignments = state
        .controls()
        .iter()
        .enumerate()
        .map(|(i, c)| {
            Ok(FormTabAssignment {
                target: c.identity.clone(),
                tab_stop: true,
                tab_order: Some(u32::try_from(i)?),
            })
        })
        .collect::<Result<Vec<_>, AnyError>>()?;
    // Avoid a partial local domain: section 1 alone is unchecked but global group is valid.
    let domain = state_plan(
        &observed,
        &policies,
        FormControlOperation::SetTabOrder { assignments },
        observed.document_flow_sha256(),
    )?;
    let plan = NativeFormPackageOutputPlan::bind(
        &raw,
        &map(2)?,
        &policies,
        &domain,
        limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let output = lower(&raw, &plan)?;
    assert_eq!(output.receipt().changed_sections, 2);
    let reread = observe(output.bytes(), 2)?;
    let result = reread.bind_policies(&policies, limits()?)?;
    assert_eq!(result.controls()[0].common.tab_order, Some(0));
    assert_eq!(result.controls()[1].common.tab_order, Some(1));
    assert!(checked(&raw, &plan, output.bytes()));
    oracle_artifact("radio-tab-source.hwpx", &raw)?;
    oracle_artifact("radio-tab-output.hwpx", output.bytes())?;
    Ok(())
}

#[test]
fn form_free_section_is_preserved_with_complete_global_map_and_flow() -> Result<(), AnyError> {
    let mut p = parts(&multi()?)?;
    let source = String::from_utf8(p.get("Contents/section1.xml").ok_or("section")?.clone())?;
    let start = source.find("<hp:edit ").ok_or("edit")?;
    let end = source.find("</hp:edit>").ok_or("edit end")? + "</hp:edit>".len();
    p.insert(
        "Contents/section1.xml".into(),
        format!(
            "{}<hp:t>form-free body remains unchanged</hp:t>{}",
            &source[..start],
            &source[end..]
        )
        .into_bytes(),
    );
    let raw = package(&p)?;
    let mut complete = map(2)?;
    complete.sections[1].map.component_controls.clear();
    let observed =
        NativeFormPackageReader::read(&raw, &complete, NativeFormPackageLimits::default())?;
    let domain = domain_plan(
        &observed,
        property(&observed)?,
        observed.document_flow_sha256(),
    )?;
    let plan = NativeFormPackageOutputPlan::bind(
        &raw,
        &complete,
        &policies(&observed)?,
        &domain,
        limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let output = lower(&raw, &plan)?;
    let result = parts(output.bytes())?;
    assert_eq!(
        result.get("Contents/section1.xml"),
        p.get("Contents/section1.xml")
    );
    assert_eq!(output.receipt().changed_sections, 1);
    assert!(checked(&raw, &plan, output.bytes()));
    let mut omitted = complete;
    omitted.sections[1].map.paragraph_ids.pop();
    assert!(
        NativeFormPackageOutputPlan::bind(
            &raw,
            &omitted,
            &policies(&observed)?,
            &domain,
            limits()?,
            NativeFormPackageLimits::default()
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn declared_binary_resources_are_byte_exact_and_external_resource_drift_rejected()
-> Result<(), AnyError> {
    for resource in ["BinData/form-bound.png", "Assets/form-bound.png"] {
        let mut p = parts(&capture()?)?;
        p.insert(
            resource.into(),
            p.get("Preview/PrvImage.png")
                .ok_or("resource seed")?
                .clone(),
        );
        let opf = String::from_utf8(p.get("Contents/content.hpf").ok_or("opf")?.clone())?;
        let changed = opf.replace("</opf:manifest>",&format!("<opf:item id=\"form_resource\" href=\"../{resource}\" media-type=\"image/png\"/></opf:manifest>"));
        assert_ne!(opf, changed);
        p.insert("Contents/content.hpf".into(), changed.into_bytes());
        let raw = package(&p)?;
        let seen = observe(&raw, 1)?;
        let plan = output_plan(&raw, 1, property(&seen)?)?;
        let output = lower(&raw, &plan)?;
        let mut result = parts(output.bytes())?;
        assert_eq!(result.get(resource), p.get(resource));
        result.get_mut(resource).ok_or("resource")?.push(1);
        assert!(!checked(&raw, &plan, &package(&result)?));
    }
    Ok(())
}
#[test]
fn observed_native_ids_are_preserved_and_never_replaced_with_component_reservations()
-> Result<(), AnyError> {
    let raw = changed_part(
        &capture()?,
        "Contents/section0.xml",
        "<hp:edit ",
        "<hp:edit id=\"12345\" instid=\"54321\" ",
    )?;
    let seen = observe(&raw, 1)?;
    let plan = output_plan(&raw, 1, property(&seen)?)?;
    let output = lower(&raw, &plan)?;
    let readback = observe(output.bytes(), 1)?;
    assert_eq!(
        seen.sections().next().ok_or("section")?.controls()[0].native_identity,
        readback.sections().next().ok_or("section")?.controls()[0].native_identity
    );
    let source_parts = parts(&raw)?;
    let output_parts = parts(output.bytes())?;
    let expected = String::from_utf8(
        source_parts
            .get("Contents/section0.xml")
            .ok_or("section")?
            .clone(),
    )?
    .replace("enabled=\"1\"", "enabled=\"0\"");
    assert_eq!(
        output_parts.get("Contents/section0.xml").ok_or("section")?,
        expected.as_bytes()
    );
    Ok(())
}
#[test]
fn character_reference_change_is_bound_to_real_header_catalog_and_header_bytes_preserved()
-> Result<(), AnyError> {
    let raw = capture()?;
    let p = parts(&raw)?;
    let catalog = CharacterStyleCatalogReader::read(
        p.get("Contents/header.xml").ok_or("header")?,
        CharacterStyleLimits::default(),
    )?;
    let seen = observe(&raw, 1)?;
    let state = seen.bind_policies(&policies(&seen)?, limits()?)?;
    let c = &state.controls()[0];
    let alternative = catalog
        .styles
        .iter()
        .find(|s| s.id != c.common.character.char_pr_id_ref)
        .ok_or("real alternative character style")?
        .id;
    let mut common = c.common.clone();
    common.character.char_pr_id_ref = alternative;
    let plan = output_plan(
        &raw,
        1,
        FormControlOperation::ReplaceProperties {
            target: c.identity.clone(),
            common,
            payload: c.payload.clone(),
        },
    )?;
    let output = lower(&raw, &plan)?;
    let observed = observe(output.bytes(), 1)?;
    assert_eq!(
        observed.sections().next().ok_or("section")?.controls()[0]
            .common
            .character
            .char_pr_id_ref,
        alternative
    );
    assert_eq!(
        parts(output.bytes())?.get("Contents/header.xml"),
        p.get("Contents/header.xml")
    );
    assert_eq!(output.receipt().changed_attributes, 1);
    Ok(())
}
