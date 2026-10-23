//! Real production component pending explicit public export/source successor.
use domain_ir::{FormControlIdentity, LogicalId};
use hwpx_package::{
    BoundedZipReader, Compression, EntryMetadata, NativeFormHwpxMap, NativeFormPackageLimits,
    NativeFormPackageMap, NativeFormPackageReader, NativeFormPackageSectionMap, PackageGraph,
    PackageGraphLimits, PackageLimitConfig, PackageLimits, PreservingXmlDocument, RelationshipKind,
    XmlAttributeToken, XmlElementToken,
};
#[path = "../src/native_root_manifest.rs"]
mod native_root_manifest;
use native_root_manifest::{
    NativeRootManifestError as E, NativeRootManifestLimits as L, NativeRootManifestPlan as Plan,
    NativeRootManifestPreparer as Prepare,
};
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
const BUNDLE: &str = "fixtures/target-build/p09-32-native-form-target-20261002-01/output";
fn sha(raw: &[u8]) -> String {
    hex::encode(Sha256::digest(raw))
}
fn checked(relative: &str, expected: &str) -> Result<Vec<u8>, AnyError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(relative);
    for parent in path.ancestors() {
        let metadata = fs::symlink_metadata(parent)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("linked source rejected".into());
            }
        }
        if metadata.file_type().is_symlink() {
            return Err("linked source rejected".into());
        }
    }
    if fs::metadata(&path)?.len() > 4 * 1024 * 1024 {
        return Err("source bound".into());
    }
    let raw = fs::read(path)?;
    if sha(&raw) != expected {
        return Err("source identity changed".into());
    }
    Ok(raw)
}
fn original() -> Result<Vec<u8>, AnyError> {
    checked(
        "implementation/p08/evidence/private/p08-20-object-target-20260915-18/obj-012-form-insert.hancom-2020-readback.hwpx",
        "02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7",
    )
}
fn case(radio: bool) -> Result<Vec<u8>, AnyError> {
    let (file, expected) = if radio {
        (
            "p09-32-c06-cross-section-radio-tab.hwpx",
            "2525a8da465b257a9171a46a7d95a7a5d2ba6da68ac1449764e208b374fe06e9",
        )
    } else {
        (
            "p09-32-c05-global-tab.hwpx",
            "98f6c41d1ca3a10da2d8754ad2d73e71acb3d1a28e33ac0f573a8f654301aacc",
        )
    };
    checked(&format!("{BUNDLE}/{file}"), expected)
}
fn parts(raw: &[u8]) -> Result<BTreeMap<String, Vec<u8>>, AnyError> {
    let mut archive = ZipArchive::new(Cursor::new(raw))?;
    let mut result = BTreeMap::new();
    for i in 0..archive.len() {
        let mut entry = archive.by_index(i)?;
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes)?;
        result.insert(entry.name().to_owned(), bytes);
    }
    Ok(result)
}
fn package(parts: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>, AnyError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for name in std::iter::once("mimetype").chain(
        parts
            .keys()
            .filter(|n| n.as_str() != "mimetype")
            .map(String::as_str),
    ) {
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(if name == "mimetype" {
                CompressionMethod::Stored
            } else {
                CompressionMethod::Deflated
            }),
        )?;
        writer.write_all(parts.get(name).ok_or("part missing")?)?;
    }
    Ok(writer.finish()?.into_inner())
}
fn replace_manifest(source: &[u8], old: &str, new: &str) -> Result<Vec<u8>, AnyError> {
    let mut p = parts(source)?;
    let xml = String::from_utf8(p.get("Contents/content.hpf").ok_or("manifest")?.clone())?;
    if !xml.contains(old) {
        return Err("replacement not applied".into());
    }
    p.insert(
        "Contents/content.hpf".into(),
        xml.replace(old, new).into_bytes(),
    );
    package(&p)
}
fn output(source: &[u8]) -> Result<native_root_manifest::NativeRootManifestOutput, AnyError> {
    Ok(Prepare::prepare(
        source,
        &Plan::bind(source, L::default())?,
        L::default(),
    )?)
}

#[test]
fn actual_original_root_manifest_is_full_raw_byte_exact_noop() -> Result<(), AnyError> {
    let raw = original()?;
    let out = output(&raw)?;
    assert_eq!(out.bytes(), raw);
    assert_eq!(out.receipt().changed_href_attributes, 0);
    assert_eq!(out.receipt().zip_header_policy, "original_raw_byte_exact");
    assert_eq!(out.receipt().qualification,native_root_manifest::NativeRootManifestQualification::PackagePreparationOnlyNativeAndTypedReferenceUnqualified);
    Ok(())
}
#[test]
fn real_failed_two_section_text_changes_only_one_href_value_and_preserves_all_parts()
-> Result<(), AnyError> {
    let raw = case(false)?;
    let out = output(&raw)?;
    let before = parts(&raw)?;
    let mut expected = before.clone();
    expected.insert(
        "Contents/content.hpf".into(),
        String::from_utf8(before["Contents/content.hpf"].clone())?
            .replace("href=\"section1.xml\"", "href=\"Contents/section1.xml\"")
            .into_bytes(),
    );
    assert_eq!(parts(out.bytes())?, expected);
    assert_eq!(out.receipt().changed_href_attributes, 1);
    assert!(out.receipt().graph_relationships_and_spine_preserved);
    assert_eq!(out.receipt().entry_count, 12);
    assert_eq!(out.receipt().zip_header_policy, "rewritten_not_byte_exact");
    println!(
        "p09_33_root_manifest_probe_json={}",
        serde_json::to_string(out.receipt())?
    );
    emit_oracle_artifacts()?;
    Ok(())
}
fn emit_oracle_artifacts() -> Result<(), AnyError> {
    let Some(directory) = std::env::var_os("HWPX_AGENT_P09_33_ORACLE_DIRECTORY") else {
        return Ok(());
    };
    let directory = std::path::PathBuf::from(directory);
    if !directory.is_absolute() || !directory.is_dir() || fs::read_dir(&directory)?.next().is_some()
    {
        return Err("new empty oracle directory required".into());
    }
    for ancestor in directory.ancestors() {
        let metadata = fs::symlink_metadata(ancestor)?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("linked oracle boundary".into());
            }
        }
        if metadata.file_type().is_symlink() {
            return Err("linked oracle boundary".into());
        }
    }
    for (name, source) in [
        ("actual-native", original()?),
        ("two-section-text", case(false)?),
        ("two-section-radio", case(true)?),
    ] {
        let out = output(&source)?;
        for (stage, bytes) in [("source", source.as_slice()), ("output", out.bytes())] {
            let mut file = fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(directory.join(format!("{name}-{stage}.hwpx")))?;
            file.write_all(bytes)?;
            file.sync_all()?;
        }
    }
    Ok(())
}
#[test]
fn complete_public_form_reader_still_observes_both_text_and_required_radio_sections()
-> Result<(), AnyError> {
    let raw_manifest = checked(
        &format!("{BUNDLE}/fixture-manifest.json"),
        "f07a8a73dbead998db253050d011ebe58ac331c42060b31c0c7a617a23ad8ef8",
    )?;
    let manifest: serde_json::Value = serde_json::from_slice(&raw_manifest)?;
    for (index, radio) in [(4, false), (5, true)] {
        let raw = case(radio)?;
        let out = output(&raw)?;
        let map = NativeFormPackageMap {
            sections: (0..2)
                .map(|i| {
                    Ok(NativeFormPackageSectionMap {
                        part: format!("Contents/section{i}.xml"),
                        map: NativeFormHwpxMap {
                            paragraph_ids: (0..2)
                                .map(|j| LogicalId::parse(format!("section-{i}-paragraph-{j}")))
                                .collect::<Result<_, _>>()?,
                            component_controls: vec![FormControlIdentity {
                                logical_control_id: LogicalId::parse(format!(
                                    "section-{i}-control"
                                ))?,
                                native_object_id: 90001 + i,
                            }],
                        },
                    })
                })
                .collect::<Result<Vec<_>, AnyError>>()?,
        };
        assert_eq!(
            serde_json::to_value(&map)?,
            manifest["cases"][index]["complete_map"]
        );
        let before = NativeFormPackageReader::read(&raw, &map, NativeFormPackageLimits::default())?;
        let after =
            NativeFormPackageReader::read(out.bytes(), &map, NativeFormPackageLimits::default())?;
        assert_eq!(before.document_flow_sha256(), after.document_flow_sha256());
        assert_eq!(before.sections().count(), 2);
        assert_eq!(after.sections().count(), 2);
        for (a, b) in before.sections().zip(after.sections()) {
            assert_eq!(a.controls(), b.controls());
        }
    }
    Ok(())
}
#[test]
fn deterministic_retry_external_verification_and_prepared_noop_are_exact() -> Result<(), AnyError> {
    let raw = case(true)?;
    let plan = Plan::bind(&raw, L::default())?;
    let a = Prepare::prepare(&raw, &plan, L::default())?;
    let b = Prepare::prepare(&raw, &plan, L::default())?;
    assert_eq!(a.bytes(), b.bytes());
    assert_eq!(a.receipt(), b.receipt());
    assert_eq!(
        &Prepare::verify_output(&raw, &plan, a.bytes(), L::default())?,
        a.receipt()
    );
    assert_eq!(output(a.bytes())?.bytes(), a.bytes());
    Ok(())
}
#[test]
fn stale_body_header_preview_and_archive_tail_cannot_reuse_plan() -> Result<(), AnyError> {
    let raw = case(false)?;
    let plan = Plan::bind(&raw, L::default())?;
    for name in [
        "Contents/header.xml",
        "Contents/section0.xml",
        "Preview/PrvImage.png",
    ] {
        let mut p = parts(&raw)?;
        p.get_mut(name).ok_or("part")?.push(b' ');
        assert!(matches!(
            Prepare::prepare(&package(&p)?, &plan, L::default()),
            Err(E::Source)
        ));
    }
    let mut trailing = raw;
    trailing.push(0);
    assert!(matches!(
        Prepare::prepare(&trailing, &plan, L::default()),
        Err(E::Source)
    ));
    Ok(())
}
#[test]
fn externally_rehashed_nonselected_part_or_manifest_damage_is_rejected() -> Result<(), AnyError> {
    let raw = case(false)?;
    let plan = Plan::bind(&raw, L::default())?;
    let out = output(&raw)?;
    for name in [
        "Contents/header.xml",
        "Contents/section0.xml",
        "Preview/PrvImage.png",
        "settings.xml",
    ] {
        let mut p = parts(out.bytes())?;
        p.get_mut(name).ok_or("part")?.push(b' ');
        assert!(matches!(
            Prepare::verify_output(&raw, &plan, &package(&p)?, L::default()),
            Err(E::Output)
        ));
    }
    let changed = replace_manifest(out.bytes(), "application/xml", "application/changed")?;
    assert!(Prepare::verify_output(&raw, &plan, &changed, L::default()).is_err());
    Ok(())
}
#[test]
fn all_relative_items_not_just_section_one_are_prepared_without_other_lexical_edits()
-> Result<(), AnyError> {
    let raw = replace_manifest(
        &case(false)?,
        "href=\"Contents/header.xml\"",
        "href='header.xml'",
    )?;
    let raw = replace_manifest(
        &raw,
        "href=\"Contents/section0.xml\"",
        "href='section0.xml'",
    )?;
    let raw = replace_manifest(&raw, "id=\"header\"", "id='he&#97;der'")?;
    let before = parts(&raw)?;
    let out = output(&raw)?;
    let expected = String::from_utf8(before["Contents/content.hpf"].clone())?
        .replace("href='header.xml'", "href='Contents/header.xml'")
        .replace("href='section0.xml'", "href='Contents/section0.xml'")
        .replace("href=\"section1.xml\"", "href=\"Contents/section1.xml\"");
    assert_eq!(
        parts(out.bytes())?["Contents/content.hpf"],
        expected.as_bytes()
    );
    assert_eq!(out.receipt().changed_href_attributes, 3);
    Ok(())
}
#[test]
fn declared_unicode_entity_and_percent_resources_keep_exact_targets_and_bytes()
-> Result<(), AnyError> {
    let mut p = parts(&case(false)?)?;
    p.insert(
        "Assets/한글 & 'x.bin".into(),
        b"original opaque resource".to_vec(),
    );
    p.insert(
        "Assets/100% label.bin".into(),
        b"original percent resource".to_vec(),
    );
    let xml=String::from_utf8(p["Contents/content.hpf"].clone())?.replace("</opf:manifest>",
        "<opf:item id=\"opaque1\" href=\"../Assets/한글 &amp; &apos;x.bin\" media-type=\"application/octet-stream\"/><opf:item id=\"opaque2\" href=\"../Assets/100%25%20label.bin\" media-type=\"application/octet-stream\"/></opf:manifest>");
    p.insert("Contents/content.hpf".into(), xml.into_bytes());
    let out = output(&package(&p)?)?;
    let actual = parts(out.bytes())?;
    assert_eq!(actual["Assets/한글 & 'x.bin"], p["Assets/한글 & 'x.bin"]);
    assert_eq!(actual["Assets/100% label.bin"], p["Assets/100% label.bin"]);
    assert_eq!(out.receipt().changed_href_attributes, 3);
    assert_eq!(output(out.bytes())?.bytes(), out.bytes());
    Ok(())
}
#[test]
fn external_escape_duplicate_spine_and_ambiguous_root_relative_sources_fail_closed()
-> Result<(), AnyError> {
    let source = case(false)?;
    for href in [
        "https://example.invalid/section1.xml",
        "file:///private/secret",
        "../../outside.xml",
        "section1.xml?query=private",
        "%2e%2e/%2e%2e/outside.xml",
    ] {
        let raw = replace_manifest(&source, "section1.xml", href)?;
        assert!(Plan::bind(&raw, L::default()).is_err());
    }
    let raw = replace_manifest(
        &source,
        "</opf:spine>",
        "<opf:itemref idref=\"section1\" linear=\"yes\"/></opf:spine>",
    )?;
    assert!(Plan::bind(&raw, L::default()).is_err());
    let mut p = parts(&source)?;
    p.insert("section1.xml".into(), p["Contents/section1.xml"].clone());
    assert!(Plan::bind(&package(&p)?, L::default()).is_err());
    Ok(())
}
#[test]
fn altered_entry_order_compression_missing_extra_parts_and_malformed_xml_rejected()
-> Result<(), AnyError> {
    let raw = case(false)?;
    let plan = Plan::bind(&raw, L::default())?;
    let out = output(&raw)?;
    let mut zip = ZipArchive::new(Cursor::new(out.bytes()))?;
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for i in 0..zip.len() {
        let mut e = zip.by_index(i)?;
        let name = e.name().to_owned();
        let mut b = Vec::new();
        e.read_to_end(&mut b)?;
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(&b)?;
    }
    assert!(matches!(
        Prepare::verify_output(&raw, &plan, &writer.finish()?.into_inner(), L::default()),
        Err(E::Output)
    ));
    let mut original_zip = ZipArchive::new(Cursor::new(out.bytes()))?;
    let mut reordered = ZipWriter::new(Cursor::new(Vec::new()));
    let mut order: Vec<_> = (0..original_zip.len()).collect();
    order.swap(1, 2);
    for i in order {
        let mut entry = original_zip.by_index(i)?;
        let name = entry.name().to_owned();
        let method = entry.compression();
        let mut bytes = Vec::new();
        entry.read_to_end(&mut bytes)?;
        reordered.start_file(
            name,
            SimpleFileOptions::default().compression_method(method),
        )?;
        reordered.write_all(&bytes)?;
    }
    assert!(matches!(
        Prepare::verify_output(&raw, &plan, &reordered.finish()?.into_inner(), L::default()),
        Err(E::Output)
    ));
    let mut p = parts(out.bytes())?;
    p.insert("unlisted.bin".into(), b"extra".to_vec());
    assert!(Prepare::verify_output(&raw, &plan, &package(&p)?, L::default()).is_err());
    p.remove("unlisted.bin");
    p.remove("Contents/section1.xml");
    assert!(Prepare::verify_output(&raw, &plan, &package(&p)?, L::default()).is_err());
    let bad = replace_manifest(&raw, "</opf:manifest>", "</opf:broken>")?;
    assert!(Plan::bind(&bad, L::default()).is_err());
    Ok(())
}
#[test]
fn finite_limits_and_reduced_verifier_ceiling_do_not_clamp_or_publish_artifacts()
-> Result<(), AnyError> {
    for args in [
        (0, 1, 1, 1),
        (1, 0, 1, 1),
        (1, 2, 1, 1),
        (1, 1, 1, 0),
        (33 * 1024 * 1024, 1, 1, 1),
        (1, 1, 1, 257),
    ] {
        assert!(L::new(args.0, args.1, args.2, args.3).is_err());
    }
    let raw = case(false)?;
    let plan = Plan::bind(&raw, L::default())?;
    assert!(Prepare::prepare(&raw, &plan, L::new(1024, 1024, 1024, 12)?).is_err());
    assert!(Plan::bind(&raw, L::new(32 * 1024 * 1024, 16, 1024, 12)?).is_err());
    Ok(())
}
#[test]
fn errors_plan_output_and_receipt_never_expose_document_values_or_absolute_paths()
-> Result<(), AnyError> {
    let raw = case(false)?;
    let plan = Plan::bind(&raw, L::default())?;
    let out = output(&raw)?;
    let debug = format!("{plan:?} {out:?} {} {:?}", E::Graph, E::Source);
    let receipt = serde_json::to_string(out.receipt())?;
    for value in [
        "second-native-derived-field",
        "complete-group",
        "private",
        "D:\\개발",
    ] {
        assert!(!debug.contains(value));
        assert!(!receipt.contains(value));
    }
    assert_eq!(out.receipt().qualification,native_root_manifest::NativeRootManifestQualification::PackagePreparationOnlyNativeAndTypedReferenceUnqualified);
    Ok(())
}
