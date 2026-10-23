//! Real production API against all fifteen immutable complete fixture identities.
use domain_ir::{
    FormControlIdentity, FormControlLimitConfig, FormControlLimits, FormControlPayload,
    FormTextValidation, LogicalId,
};
use hwpx_package::{
    BoundedZipReader, CharacterStyleCatalogReader, CharacterStyleLimits, Color, NativeFormHwpxMap,
    NativeFormHwpxReadback, NativeFormObservedPayload, NativeFormPackageLimits,
    NativeFormPackageMap, NativeFormPackagePolicy, NativeFormPackageReadback,
    NativeFormPackageReader, NativeFormPackageSectionMap, PackageLimits,
    native_form_color::{
        NativeFormColorError, NativeFormColorLimits, NativeFormColorPlan, NativeFormColorPreparer,
        NativeFormColorRequest,
    },
};
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    fs,
    io::{Cursor, Read as _, Write as _},
    path::Path,
};
use zip::{ZipArchive, ZipWriter, write::SimpleFileOptions};
type AnyError = Box<dyn Error>;
const MANIFEST: &str =
    "fixtures/target-build/p09-35-native-form-diagnostics-01/output/fixture-manifest.json";
const MANIFEST_SHA: &str = "ef1bdad32cf06b07725a17888b7378e9720b2111539675c20178ab850f1d9750";
fn sha(raw: &[u8]) -> String {
    hex::encode(Sha256::digest(raw))
}
fn checked(path: &Path, digest: &str) -> Result<Vec<u8>, AnyError> {
    for p in path.ancestors() {
        let m = fs::symlink_metadata(p)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("linked fixture".into());
            }
        }
        if m.file_type().is_symlink() {
            return Err("linked fixture".into());
        }
    }
    let m = fs::metadata(path)?;
    if !m.is_file() || m.len() == 0 || m.len() > 4 * 1024 * 1024 {
        return Err("fixture bound".into());
    }
    let raw = fs::read(path)?;
    if sha(&raw) != digest {
        return Err("fixture changed".into());
    }
    Ok(raw)
}
fn domain() -> Result<FormControlLimits, AnyError> {
    Ok(FormControlLimits::new(FormControlLimitConfig::default())?)
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
// Original explicit fixture caller policy; hash checked, not native-inferred defaults.
fn policies(
    observed: &NativeFormPackageReadback,
) -> Result<Vec<NativeFormPackagePolicy>, AnyError> {
    observed
        .sections()
        .flat_map(NativeFormHwpxReadback::controls)
        .map(|c| {
            let payload = match &c.payload {
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
                } => FormControlPayload::Radio {
                    caption: caption.clone(),
                    value: *value,
                    default_value: *value,
                    radio_group_name: radio_group_name.clone().ok_or("group missing")?,
                    group_required: true,
                    tri_state: *tri_state,
                    back_style: *back_style,
                },
                _ => return Err("fixture policy unsupported".into()),
            };
            Ok(NativeFormPackagePolicy {
                identity: c.component_identity.clone(),
                payload,
            })
        })
        .collect()
}
struct Fixture {
    raw: Vec<u8>,
    map: NativeFormPackageMap,
    policies: Vec<NativeFormPackagePolicy>,
}
fn fixture(index: usize) -> Result<Fixture, AnyError> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let manifest: Value = serde_json::from_slice(&checked(&root.join(MANIFEST), MANIFEST_SHA)?)?;
    let case = &manifest["cases"][index];
    let mapping = map(if index < 2 { 2 } else { 1 })?;
    if serde_json::to_value(&mapping)? != case["complete_map"] {
        return Err("map changed".into());
    }
    let parent = root
        .join(MANIFEST)
        .parent()
        .ok_or("manifest parent")?
        .to_owned();
    let raw = checked(
        &parent.join(case["file"].as_str().ok_or("input name")?),
        case["package_sha256"].as_str().ok_or("input sha")?,
    )?;
    let observed =
        NativeFormPackageReader::read(&raw, &mapping, NativeFormPackageLimits::default())?;
    let policy = policies(&observed)?;
    if sha(&serde_json::to_vec(&policy)?) != case["policy_sha256"].as_str().ok_or("policy sha")?
        || observed
            .bind_policies(&policy, domain()?)?
            .canonical_sha256(domain()?)?
            != case["target_state_sha256"].as_str().ok_or("state sha")?
    {
        return Err("fixture intent changed".into());
    }
    Ok(Fixture {
        raw,
        map: mapping,
        policies: policy,
    })
}
fn intent(f: &Fixture, rgb: u32) -> NativeFormColorRequest {
    NativeFormColorRequest {
        target: f.map.sections[0].map.component_controls[0].clone(),
        foreground_rgb: rgb,
    }
}
fn plan(f: &Fixture, rgb: u32) -> Result<NativeFormColorPlan, AnyError> {
    Ok(NativeFormColorPlan::bind(
        &f.raw,
        &f.map,
        &f.policies,
        &[intent(f, rgb)],
        domain()?,
        NativeFormPackageLimits::default(),
    )?)
}
fn entry(raw: &[u8], path: &str) -> Result<Vec<u8>, AnyError> {
    let mut zip = BoundedZipReader::open(Cursor::new(raw), PackageLimits::default())?;
    let i = zip
        .entries()
        .iter()
        .position(|e| e.path.as_str() == path)
        .ok_or("entry missing")?;
    Ok(zip.read_entry(i)?)
}
// Mutation helper is test-only: real external verifier must reject substituted parts.
fn substitute(raw: &[u8], path: &str, replacement: &[u8]) -> Result<Vec<u8>, AnyError> {
    let mut zip = ZipArchive::new(Cursor::new(raw))?;
    let mut out = ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..zip.len() {
        let mut part = zip.by_index(i)?;
        let mut value = Vec::new();
        part.read_to_end(&mut value)?;
        out.start_file(
            part.name(),
            SimpleFileOptions::default().compression_method(part.compression()),
        )?;
        out.write_all(if part.name() == path {
            replacement
        } else {
            &value
        })?;
    }
    Ok(out.finish()?.into_inner())
}

#[test]
fn all_fifteen_complete_inputs_and_arbitrary_exact_colors_preserve_full_other_control_state()
-> Result<(), AnyError> {
    for index in 0..15 {
        let f = fixture(index)?;
        let before =
            NativeFormPackageReader::read(&f.raw, &f.map, NativeFormPackageLimits::default())?
                .bind_policies(&f.policies, domain()?)?;
        for rgb in [0, 1, 0x00CC_1100, 0x002E_74B5, 0x00AB_CDEF, 0x00FF_FFFF] {
            let p = plan(&f, rgb)?;
            let output = NativeFormColorPreparer::prepare(
                &f.raw,
                &p,
                domain()?,
                NativeFormPackageLimits::default(),
                NativeFormColorLimits::default(),
            )?;
            let observed = NativeFormPackageReader::read(
                output.bytes(),
                &f.map,
                NativeFormPackageLimits::default(),
            )?;
            let after = observed.bind_policies(&f.policies, domain()?)?;
            let mut expected = before.controls()[0].clone();
            expected.common.fore_color_rgb = rgb;
            expected.common.character.char_pr_id_ref =
                after.controls()[0].common.character.char_pr_id_ref;
            assert!(expected == after.controls()[0]);
            assert!(before.controls()[1..] == after.controls()[1..]);
            let catalog = CharacterStyleCatalogReader::read(
                &entry(output.bytes(), "Contents/header.xml")?,
                CharacterStyleLimits::default(),
            )?;
            let style = catalog
                .styles
                .iter()
                .find(|s| s.id == expected.common.character.char_pr_id_ref)
                .ok_or("style missing")?;
            assert_eq!(
                style.text_color,
                Color::Rgb(
                    ((rgb >> 16) & 255) as u8,
                    ((rgb >> 8) & 255) as u8,
                    (rgb & 255) as u8
                )
            );
            assert_eq!(output.receipt().actual_native_validation, "not_run");
            assert!(
                output
                    .receipt()
                    .preservation
                    .existing_styles_and_fonts_preserved
            );
        }
    }
    Ok(())
}
#[test]
fn cloned_styles_keep_every_font_metric_effect_and_existing_catalog_semantic_field()
-> Result<(), AnyError> {
    let f = fixture(2)?;
    let p = plan(&f, 0x0012_3456)?;
    let before = CharacterStyleCatalogReader::read(
        &entry(&f.raw, "Contents/header.xml")?,
        CharacterStyleLimits::default(),
    )?;
    let output = NativeFormColorPreparer::prepare(
        &f.raw,
        &p,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    let after = CharacterStyleCatalogReader::read(
        &entry(output.bytes(), "Contents/header.xml")?,
        CharacterStyleLimits::default(),
    )?;
    assert!(before.font_faces == after.font_faces);
    assert!(before.styles == after.styles[..before.styles.len()]);
    let read = NativeFormPackageReader::read(&f.raw, &f.map, NativeFormPackageLimits::default())?;
    let base_id = read.sections().next().ok_or("section")?.controls()[0]
        .common
        .character
        .char_pr_id_ref;
    let mut wanted = before
        .styles
        .iter()
        .find(|s| s.id == base_id)
        .ok_or("base style")?
        .clone();
    let new = after.styles.last().ok_or("new style")?;
    wanted.id = new.id;
    wanted.text_color = Color::Rgb(0x12, 0x34, 0x56);
    assert!(wanted == *new);
    assert_eq!(output.receipt().appended_styles, 1);
    Ok(())
}
#[test]
fn exact_style_reuse_and_repeated_preparation_do_not_duplicate_catalogs() -> Result<(), AnyError> {
    let mut f = fixture(2)?;
    let p = plan(&f, 0x0012_3456)?;
    let a = NativeFormColorPreparer::prepare(
        &f.raw,
        &p,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    let retry = NativeFormColorPreparer::prepare(
        &f.raw,
        &p,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    assert!(a.bytes() == retry.bytes());
    assert_eq!(a.receipt(), retry.receipt());
    f.raw = a.bytes().to_vec();
    let p2 = plan(&f, 0x0012_3456)?;
    let b = NativeFormColorPreparer::prepare(
        &f.raw,
        &p2,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    assert_eq!(b.receipt().appended_styles, 0);
    assert_eq!(b.receipt().reused_styles, 1);
    assert_eq!(b.receipt().changed_sections, 0);
    assert!(entry(a.bytes(), "Contents/header.xml")? == entry(b.bytes(), "Contents/header.xml")?);
    Ok(())
}
#[test]
fn external_verification_rejects_changed_foreground_header_and_unrelated_metadata()
-> Result<(), AnyError> {
    let f = fixture(2)?;
    let p = plan(&f, 0x0012_3456)?;
    let out = NativeFormColorPreparer::prepare(
        &f.raw,
        &p,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    assert_eq!(
        out.receipt(),
        &NativeFormColorPreparer::verify_output(
            &f.raw,
            &p,
            out.bytes(),
            domain()?,
            NativeFormPackageLimits::default(),
            NativeFormColorLimits::default()
        )?
    );
    for path in [
        "Contents/header.xml",
        "Contents/section0.xml",
        "version.xml",
    ] {
        let mut changed = entry(out.bytes(), path)?;
        changed.push(b' ');
        let bad = substitute(out.bytes(), path, &changed)?;
        assert!(
            NativeFormColorPreparer::verify_output(
                &f.raw,
                &p,
                &bad,
                domain()?,
                NativeFormPackageLimits::default(),
                NativeFormColorLimits::default()
            )
            .is_err()
        );
    }
    Ok(())
}
#[test]
fn duplicate_missing_oversized_color_and_empty_requests_are_rejected() -> Result<(), AnyError> {
    let f = fixture(2)?;
    let one = intent(&f, 1);
    let mut unknown = one.clone();
    unknown.target.native_object_id += 1;
    for requests in [
        Vec::new(),
        vec![one.clone(), one],
        vec![unknown],
        vec![intent(&f, 0x0100_0000)],
    ] {
        assert!(
            NativeFormColorPlan::bind(
                &f.raw,
                &f.map,
                &f.policies,
                &requests,
                domain()?,
                NativeFormPackageLimits::default()
            )
            .is_err()
        );
    }
    Ok(())
}
#[test]
fn stale_source_and_swapped_policies_maps_fail_before_output() -> Result<(), AnyError> {
    let f = fixture(2)?;
    let p = plan(&f, 1)?;
    let mut changed = f.raw.clone();
    changed.push(0);
    assert!(
        NativeFormColorPreparer::prepare(
            &changed,
            &p,
            domain()?,
            NativeFormPackageLimits::default(),
            NativeFormColorLimits::default()
        )
        .is_err()
    );
    let mut policy = f.policies.clone();
    policy[0].identity.native_object_id += 1;
    assert!(
        NativeFormColorPlan::bind(
            &f.raw,
            &f.map,
            &policy,
            &[intent(&f, 1)],
            domain()?,
            NativeFormPackageLimits::default()
        )
        .is_err()
    );
    assert!(
        NativeFormColorPlan::bind(
            &f.raw,
            &map(2)?,
            &f.policies,
            &[intent(&f, 1)],
            domain()?,
            NativeFormPackageLimits::default()
        )
        .is_err()
    );
    Ok(())
}
#[test]
fn finite_limits_and_debug_output_do_not_disclose_private_controls() -> Result<(), AnyError> {
    for (a, p, t) in [
        (0, 1, 1),
        (1, 0, 1),
        (1, 2, 1),
        (33 * 1024 * 1024, 1, 1),
        (1, 1, 17 * 1024 * 1024),
    ] {
        assert!(NativeFormColorLimits::new(a, p, t).is_err());
    }
    let f = fixture(2)?;
    let p = plan(&f, 1)?;
    assert_eq!(
        NativeFormColorPreparer::prepare(
            &f.raw,
            &p,
            domain()?,
            NativeFormPackageLimits::default(),
            NativeFormColorLimits::new(1, 1, 1)?
        )
        .err(),
        Some(NativeFormColorError::Zip)
    );
    let text = format!("{p:?} {:?}", intent(&f, 1));
    assert!(!text.contains("section-0-control"));
    assert!(!text.contains("P08FORMINSERT"));
    Ok(())
}

#[test]
fn document_protection_signal_is_not_bypassed_by_catalog_color_preparation() -> Result<(), AnyError>
{
    let f = fixture(2)?;
    let header = String::from_utf8(entry(&f.raw, "Contents/header.xml")?)?;
    let protected = header.replacen("<hh:head ", "<hh:head passwordProtected=\"1\" ", 1);
    assert!(protected != header);
    let source = substitute(&f.raw, "Contents/header.xml", protected.as_bytes())?;
    assert_eq!(
        NativeFormColorPlan::bind(
            &source,
            &f.map,
            &f.policies,
            &[intent(&f, 1)],
            domain()?,
            NativeFormPackageLimits::default()
        )
        .err(),
        Some(NativeFormColorError::Protection)
    );
    Ok(())
}

#[test]
fn nonform_section_before_target_is_preserved_without_section_iterator_misalignment()
-> Result<(), AnyError> {
    let mut f = fixture(0)?;
    let raw = entry(&f.raw, "Contents/section0.xml")?;
    let doc = hwpx_package::PreservingXmlDocument::parse(&raw)?;
    let node = doc
        .elements()
        .iter()
        .find(|n| n.name().local_name() == "edit")
        .ok_or("edit missing")?;
    let span = node.outer_span().ok_or("edit span")?;
    let mut without = raw[..span.start()].to_vec();
    without.extend_from_slice(&raw[span.end()..]);
    f.raw = substitute(&f.raw, "Contents/section0.xml", &without)?;
    f.map.sections[0].map.component_controls.clear();
    f.policies.remove(0);
    let request = NativeFormColorRequest {
        target: f.map.sections[1].map.component_controls[0].clone(),
        foreground_rgb: 1,
    };
    let p = NativeFormColorPlan::bind(
        &f.raw,
        &f.map,
        &f.policies,
        &[request],
        domain()?,
        NativeFormPackageLimits::default(),
    )?;
    let out = NativeFormColorPreparer::prepare(
        &f.raw,
        &p,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    assert!(entry(out.bytes(), "Contents/section0.xml")? == without);
    assert_eq!(out.receipt().changed_sections, 1);
    Ok(())
}

#[test]
fn two_global_targets_share_one_semantically_exact_style_without_font_approximation()
-> Result<(), AnyError> {
    let f = fixture(0)?;
    let requests: Vec<_> = f
        .map
        .sections
        .iter()
        .flat_map(|s| s.map.component_controls.iter())
        .map(|c| NativeFormColorRequest {
            target: c.clone(),
            foreground_rgb: 0x0012_3456,
        })
        .collect();
    let p = NativeFormColorPlan::bind(
        &f.raw,
        &f.map,
        &f.policies,
        &requests,
        domain()?,
        NativeFormPackageLimits::default(),
    )?;
    let out = NativeFormColorPreparer::prepare(
        &f.raw,
        &p,
        domain()?,
        NativeFormPackageLimits::default(),
        NativeFormColorLimits::default(),
    )?;
    assert_eq!(out.receipt().requested_controls, 2);
    assert_eq!(out.receipt().appended_styles, 1);
    assert_eq!(out.receipt().reused_styles, 1);
    let state =
        NativeFormPackageReader::read(out.bytes(), &f.map, NativeFormPackageLimits::default())?
            .bind_policies(&f.policies, domain()?)?;
    assert_eq!(
        state.controls()[0].common.character.char_pr_id_ref,
        state.controls()[1].common.character.char_pr_id_ref
    );
    assert!(
        state
            .controls()
            .iter()
            .all(|c| c.common.fore_color_rgb == 0x0012_3456)
    );
    Ok(())
}
