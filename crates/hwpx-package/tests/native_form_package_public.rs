//! Complete predecessor cases through the real public `hwpx_package` API only.
use domain_ir::*;
use hwpx_package::*;
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

#[test]
fn legacy_shape_index_actual_failure_and_non_linear_header_spine_are_preserved()
-> Result<(), AnyError> {
    let raw = capture()?;
    let mut reader = BoundedZipReader::open(Cursor::new(&raw), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    assert_eq!(
        graph
            .spine
            .iter()
            .map(PackagePath::as_str)
            .collect::<Vec<_>>(),
        ["Contents/header.xml", "Contents/section0.xml"]
    );
    match IdIndex::build(
        &mut reader,
        &graph,
        IdRuleProfile::hwpml_2011_shape_v6(),
        IdIndexLimits::default(),
    ) {
        Ok(_) => return Err("legacy reference failure unexpectedly disappeared".into()),
        Err(error) => {
            assert_eq!(error.code(), "id_index_validation_failed");
            let report = error.validation().ok_or("legacy validation report")?;
            assert_eq!(report.issues().len(), 2);
            for issue in report.issues() {
                assert_eq!(issue.kind(), IdIssueKind::UnknownIdLikeAttribute);
            }
        }
    }
    Ok(())
}
#[test]
fn actual_complete_capture_bindings_and_missing_identity_are_read_without_injection()
-> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    assert_eq!(seen.package_sha256(), CAPTURE_SHA);
    assert_eq!(seen.sections().count(), 1);
    assert_eq!(
        seen.sections().next().ok_or("section")?.controls()[0].native_identity,
        NativeFormObservedIdentity::Missing
    );
    assert!(!seen.bindings().protection_signal_observed());
    let bindings: serde_json::Value = serde_json::from_slice(&seen.bindings().canonical_json()?)?;
    assert_eq!(
        bindings["style_catalog_sha256"],
        sha(parts(&raw)?.get("Contents/header.xml").ok_or("header")?)
    );
    assert_ne!(seen.document_flow_sha256(), "a1".repeat(32));
    assert_eq!(
        seen.reference_overlay_status(),
        ("id_index_validation_failed", 2)
    );
    println!(
        "p09_29_probe_json={}",
        serde_json::json!({
            "package_sha256": seen.package_sha256(), "document_flow_sha256": seen.document_flow_sha256(),
            "section_count": seen.section_count(), "bindings": bindings,
            "legacy_index_state": seen.reference_overlay_status().0, "verified_overlay_issues": seen.reference_overlay_status().1,
        })
    );
    NativeFormPackageReader::verify(&raw, &seen, NativeFormPackageLimits::default())?;
    assert_eq!(sha(&capture()?), CAPTURE_SHA);
    Ok(())
}
#[test]
fn complete_global_state_and_real_property_plan_bind_actual_metadata() -> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let policies = policies(&seen)?;
    let state = seen.bind_policies(&policies, limits()?)?;
    seen.verify_domain_state(&state, &policies, limits()?)?;
    let plan = domain_plan(&seen, property(&seen)?, seen.document_flow_sha256())?;
    let bound = NativeFormPackagePlan::bind(
        &raw,
        &seen,
        &policies,
        &plan,
        limits()?,
        NativeFormPackageLimits::default(),
    )?;
    assert_eq!(bound.plan_sha256()?.len(), 64);
    assert_eq!(bound.plan_sha256()?, bound.clone().plan_sha256()?);
    Ok(())
}
#[test]
fn forged_external_metadata_and_non_form_hashes_are_rejected() -> Result<(), AnyError> {
    let seen = observe(&capture()?, 1)?;
    let policies = policies(&seen)?;
    let state = seen.bind_policies(&policies, limits()?)?;
    let original: serde_json::Value = serde_json::from_slice(&state.canonical_json(limits()?)?)?;
    for field in [
        "non_form_content_sha256",
        "style_catalog_sha256",
        "border_catalog_sha256",
        "resource_inventory_sha256",
        "reference_inventory_sha256",
        "document_protection_sha256",
        "opaque_document_state_sha256",
    ] {
        let mut changed = original.clone();
        changed[field] = serde_json::Value::String("d2".repeat(32));
        let forged = FormDocumentState::from_draft(serde_json::from_value(changed)?, limits()?)?;
        assert!(matches!(
            seen.verify_domain_state(&forged, &policies, limits()?),
            Err(NativeFormPackageError::State)
        ));
    }
    Ok(())
}
#[test]
fn derived_multi_section_complete_global_tab_plan_not_a_native_receipt() -> Result<(), AnyError> {
    let raw = multi()?;
    let seen = observe(&raw, 2)?;
    let policies = policies(&seen)?;
    let state = seen.bind_policies(&policies, limits()?)?;
    assert_eq!(state.controls().len(), 2);
    let assignments = state
        .controls()
        .iter()
        .enumerate()
        .map(|(i, c)| {
            Ok(FormTabAssignment {
                target: c.identity.clone(),
                tab_stop: true,
                tab_order: Some(u32::try_from(1 - i)?),
            })
        })
        .collect::<Result<_, AnyError>>()?;
    let domain = domain_plan(
        &seen,
        FormControlOperation::SetTabOrder { assignments },
        seen.document_flow_sha256(),
    )?;
    let _ = NativeFormPackagePlan::bind(
        &raw,
        &seen,
        &policies,
        &domain,
        limits()?,
        NativeFormPackageLimits::default(),
    )?;
    // Required radio groups are global, not independently required in each section.
    let mut p = parts(&multi()?)?;
    for i in 0..2 {
        let part = format!("Contents/section{i}.xml");
        let raw = String::from_utf8(p.get(&part).ok_or("section")?.clone())?;
        let start = raw.find("<hp:edit ").ok_or("edit")?;
        let end = raw.find("</hp:edit>").ok_or("edit end")? + "</hp:edit>".len();
        let edit = &raw[start..end];
        let geometry =
            &edit[edit.find("<hp:sz ").ok_or("geometry")?..edit.len() - "</hp:edit>".len()];
        let value = if i == 0 { "CHECKED" } else { "UNCHECKED" };
        let replacement = format!(
            "<hp:radioBtn name=\"cross-section-radio-{i}\" foreColor=\"#000000\" backColor=\"#FFFFFF\" groupName=\"\" tabStop=\"1\" editable=\"1\" tabOrder=\"{}\" enabled=\"1\" borderTypeIDRef=\"0\" drawFrame=\"1\" printable=\"1\" command=\"\" caption=\"cross section radio\" value=\"{value}\" radioGroupName=\"global-radio-group\" triState=\"0\" backStyle=\"TRANSPARENT\"><hp:formCharPr charPrIDRef=\"0\" followContext=\"0\" autoSz=\"0\" wordWrap=\"1\"/>{geometry}</hp:radioBtn>",
            i + 1
        );
        p.insert(
            part,
            format!("{}{replacement}{}", &raw[..start], &raw[end..]).into_bytes(),
        );
    }
    let raw = package(&p)?;
    let seen = observe(&raw, 2)?;
    let policies = seen
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
                return Err("radio source".into());
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload: FormControlPayload::Radio {
                    caption: caption.clone(),
                    value: *value,
                    default_value: *value,
                    radio_group_name: radio_group_name.clone().ok_or("radio group")?,
                    group_required: true,
                    tri_state: *tri_state,
                    back_style: *back_style,
                },
            })
        })
        .collect::<Result<Vec<_>, AnyError>>()?;
    let state = seen.bind_policies(&policies, limits()?)?;
    assert_eq!(state.controls().len(), 2);
    seen.verify_domain_state(&state, &policies, limits()?)?;
    Ok(())
}
#[test]
fn missing_reordered_extra_or_cross_section_duplicate_maps_rejected() -> Result<(), AnyError> {
    let raw = multi()?;
    let original = map(2)?;
    let mut missing = original.clone();
    missing.sections.pop();
    let mut reversed = original.clone();
    reversed.sections.reverse();
    let mut extra = original.clone();
    extra.sections.push(original.sections[0].clone());
    let mut duplicate = original.clone();
    duplicate.sections[1].map.component_controls =
        duplicate.sections[0].map.component_controls.clone();
    let mut paragraph = original.clone();
    paragraph.sections[1].map.paragraph_ids = paragraph.sections[0].map.paragraph_ids.clone();
    for changed in [missing, reversed, extra, duplicate, paragraph] {
        assert!(matches!(
            NativeFormPackageReader::read(&raw, &changed, NativeFormPackageLimits::default()),
            Err(NativeFormPackageError::Map)
        ));
    }
    Ok(())
}
#[test]
fn source_metadata_change_cannot_reuse_sealed_readback_or_plan() -> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    for path in ["Contents/header.xml", "settings.xml", "Preview/PrvText.txt"] {
        let mut p = parts(&raw)?;
        p.get_mut(path).ok_or("part")?.extend_from_slice(b" ");
        let changed = package(&p)?;
        assert!(
            NativeFormPackageReader::verify(&changed, &seen, NativeFormPackageLimits::default())
                .is_err()
        );
    }
    Ok(())
}
#[test]
fn actual_form_character_and_border_catalog_dangling_refs_fail_closed() -> Result<(), AnyError> {
    for (from, to) in [
        (
            "<hp:formCharPr charPrIDRef=\"0\"",
            "<hp:formCharPr charPrIDRef=\"999\"",
        ),
        ("borderTypeIDRef=\"0\"", "borderTypeIDRef=\"999\""),
    ] {
        let mut p = parts(&capture()?)?;
        let s = String::from_utf8(p.get("Contents/section0.xml").ok_or("section")?.clone())?;
        let changed = s.replace(from, to);
        assert_ne!(s, changed);
        p.insert("Contents/section0.xml".into(), changed.into_bytes());
        assert!(
            NativeFormPackageReader::read(
                &package(&p)?,
                &map(1)?,
                NativeFormPackageLimits::default()
            )
            .is_err()
        );
    }
    Ok(())
}
#[test]
fn explicit_policy_is_complete_and_native_value_not_caller_fabricated() -> Result<(), AnyError> {
    let seen = observe(&capture()?, 1)?;
    let mut p = policies(&seen)?;
    assert!(seen.bind_policies(&[], limits()?).is_err());
    let FormControlPayload::Text { value, .. } = &mut p[0].payload else {
        return Err("text".into());
    };
    *value = "caller invented value".into();
    assert!(seen.bind_policies(&p, limits()?).is_err());
    let mut p = policies(&seen)?;
    p[0].identity.native_object_id += 1;
    assert!(seen.bind_policies(&p, limits()?).is_err());
    Ok(())
}
#[test]
fn observed_protection_signal_blocks_plan_without_claiming_unlocked_absence() -> Result<(), AnyError>
{
    let mut p = parts(&capture()?)?;
    let s = String::from_utf8(p.get("settings.xml").ok_or("settings")?.clone())?;
    let changed = s.replace(
        "<ha:HWPApplicationSetting",
        "<ha:HWPApplicationSetting protection=\"1\"",
    );
    assert_ne!(s, changed);
    p.insert("settings.xml".into(), changed.into_bytes());
    let raw = package(&p)?;
    let seen = observe(&raw, 1)?;
    assert!(seen.bindings().protection_signal_observed());
    let domain = domain_plan(&seen, property(&seen)?, seen.document_flow_sha256())?;
    assert!(matches!(
        NativeFormPackagePlan::bind(
            &raw,
            &seen,
            &policies(&seen)?,
            &domain,
            limits()?,
            NativeFormPackageLimits::default()
        ),
        Err(NativeFormPackageError::Protection)
    ));
    Ok(())
}
#[test]
fn actual_flow_not_constant_component_flow_and_wrong_plan_rejected() -> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let domain = domain_plan(&seen, property(&seen)?, &"a1".repeat(32))?;
    assert!(matches!(
        NativeFormPackagePlan::bind(
            &raw,
            &seen,
            &policies(&seen)?,
            &domain,
            limits()?,
            NativeFormPackageLimits::default()
        ),
        Err(NativeFormPackageError::Binding)
    ));
    Ok(())
}
#[test]
fn extra_unknown_or_dangling_non_form_refs_are_not_ignored_by_native_overlay()
-> Result<(), AnyError> {
    for (from, to) in [
        ("paraPrIDRef=\"0\"", "paraPrIDRef=\"999\""),
        (
            "<hp:run charPrIDRef=\"0\"",
            "<hp:run unexpectedIDRef=\"0\" charPrIDRef=\"0\"",
        ),
    ] {
        let mut p = parts(&capture()?)?;
        let raw = String::from_utf8(p.get("Contents/section0.xml").ok_or("section")?.clone())?;
        let changed = raw.replace(from, to);
        assert_ne!(raw, changed);
        p.insert("Contents/section0.xml".into(), changed.into_bytes());
        assert!(matches!(
            NativeFormPackageReader::read(
                &package(&p)?,
                &map(1)?,
                NativeFormPackageLimits::default()
            ),
            Err(NativeFormPackageError::Reference)
        ));
    }
    Ok(())
}
#[test]
fn duplicate_observed_native_ids_across_sections_are_rejected() -> Result<(), AnyError> {
    let mut p = parts(&multi()?)?;
    for part in ["Contents/section0.xml", "Contents/section1.xml"] {
        let raw = String::from_utf8(p.get(part).ok_or("section")?.clone())?;
        p.insert(
            part.into(),
            raw.replace("<hp:edit ", "<hp:edit id=\"777\" ")
                .into_bytes(),
        );
    }
    assert!(matches!(
        NativeFormPackageReader::read(&package(&p)?, &map(2)?, NativeFormPackageLimits::default()),
        Err(NativeFormPackageError::Map)
    ));
    Ok(())
}
#[test]
fn empty_form_section_still_has_complete_map_flow_and_package_binding() -> Result<(), AnyError> {
    let mut p = parts(&multi()?)?;
    let raw = String::from_utf8(p.get("Contents/section1.xml").ok_or("section")?.clone())?;
    let start = raw.find("<hp:edit ").ok_or("edit")?;
    let end = raw.find("</hp:edit>").ok_or("edit end")? + "</hp:edit>".len();
    p.insert(
        "Contents/section1.xml".into(),
        format!(
            "{}<hp:t>derived empty section</hp:t>{}",
            &raw[..start],
            &raw[end..]
        )
        .into_bytes(),
    );
    let mut complete = map(2)?;
    complete.sections[1].map.component_controls.clear();
    let seen = NativeFormPackageReader::read(
        &package(&p)?,
        &complete,
        NativeFormPackageLimits::default(),
    )?;
    assert_eq!(seen.section_count(), 2);
    assert_eq!(
        seen.bind_policies(&policies(&seen)?, limits()?)?
            .controls()
            .len(),
        1
    );
    Ok(())
}
#[test]
fn target_property_reference_catalogs_are_checked_before_plan_binding() -> Result<(), AnyError> {
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    let source = seen.bind_policies(&policies(&seen)?, limits()?)?;
    for border in [false, true] {
        let c = &source.controls()[0];
        let mut common = c.common.clone();
        if border {
            common.border_type_id_ref = 1;
        } else {
            common.character.char_pr_id_ref = 999;
        }
        let operation = FormControlOperation::ReplaceProperties {
            target: c.identity.clone(),
            common,
            payload: c.payload.clone(),
        };
        let plan = domain_plan(&seen, operation, seen.document_flow_sha256())?;
        assert!(matches!(
            NativeFormPackagePlan::bind(
                &raw,
                &seen,
                &policies(&seen)?,
                &plan,
                limits()?,
                NativeFormPackageLimits::default()
            ),
            Err(NativeFormPackageError::Catalog)
        ));
    }
    Ok(())
}
#[test]
fn all_declared_binary_resource_paths_bind_bytes_not_only_bin_data_prefix() -> Result<(), AnyError>
{
    for resource in ["BinData/bound.png", "Assets/bound.png"] {
        let mut p = parts(&capture()?)?;
        let image = p.get("Preview/PrvImage.png").ok_or("image")?.clone();
        p.insert(resource.into(), image);
        let opf = String::from_utf8(p.get("Contents/content.hpf").ok_or("opf")?.clone())?;
        let changed = opf.replace("</opf:manifest>", &format!("<opf:item id=\"bound_resource\" href=\"../{resource}\" media-type=\"image/png\"/></opf:manifest>"));
        assert_ne!(opf, changed);
        p.insert("Contents/content.hpf".into(), changed.into_bytes());
        let first = package(&p)?;
        let seen = observe(&first, 1)?;
        p.get_mut(resource)
            .ok_or("resource")?
            .extend_from_slice(b"changed-binary-fingerprint");
        let changed = package(&p)?;
        let next = observe(&changed, 1)?;
        let left: serde_json::Value = serde_json::from_slice(&seen.bindings().canonical_json()?)?;
        let right: serde_json::Value = serde_json::from_slice(&next.bindings().canonical_json()?)?;
        assert_ne!(
            left["resource_inventory_sha256"],
            right["resource_inventory_sha256"]
        );
        assert!(
            NativeFormPackageReader::verify(&changed, &seen, NativeFormPackageLimits::default())
                .is_err()
        );
    }
    Ok(())
}
#[test]
fn finite_bounds_and_debug_errors_never_expose_private_values() -> Result<(), AnyError> {
    assert!(NativeFormPackageLimits::new(0, 1, 1, 1, 1).is_err());
    assert!(NativeFormPackageLimits::new(1, 1, 2, 1, 1).is_err());
    assert!(NativeFormPackageLimits::new(1, 1, 1, 1, 65).is_err());
    let raw = capture()?;
    let seen = observe(&raw, 1)?;
    assert!(
        NativeFormPackageReader::read(
            &raw,
            &map(1)?,
            NativeFormPackageLimits::new(1, 256, 2 * 1024 * 1024, 16 * 1024 * 1024, 64)?
        )
        .is_err()
    );
    let p = policies(&seen)?;
    let domain = domain_plan(&seen, property(&seen)?, seen.document_flow_sha256())?;
    let plan = NativeFormPackagePlan::bind(
        &raw,
        &seen,
        &p,
        &domain,
        limits()?,
        NativeFormPackageLimits::default(),
    )?;
    let debug = format!(
        "{seen:?} {:?} {p:?} {plan:?} {:?}",
        seen.bindings(),
        map(1)?
    );
    for value in [CAPTURE_SHA, CAPTURE, "Contents/header.xml", "P08FORMINSERT"] {
        assert!(!debug.contains(value));
    }
    assert_eq!(
        NATIVE_FORM_PACKAGE_BINDING_PROFILE_ID,
        "hwpx-agent.native-form-package.complete-observed-bindings/v1"
    );
    Ok(())
}
