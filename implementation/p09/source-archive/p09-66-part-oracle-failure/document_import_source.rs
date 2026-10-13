use std::{
    error::Error,
    io::{Cursor, Write},
    path::PathBuf,
};

use domain_ir::{DocumentId, LogicalId, SourceAnchorHandle};
use hwpx_package::{
    PartRole,
    document_import::{
        ImportedSourcePackage, SourceImportError, SourceImportLimitConfig, SourceImportLimits,
    },
};
use sha2::{Digest as _, Sha256};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

type TestResult = Result<(), Box<dyn Error>>;
const NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";
const SECTION: &str = r#"<s:sec xmlns:s="http://www.hancom.co.kr/hwpml/2011/section" xmlns:p="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:u="urn:unknown"><p:p id="7"><p:run charPrIDRef="0"><p:t>한글&#x20;A&amp;B</p:t><p:checkBtn id="7"/><u:future value="TOPSECRET"><u:nested/></u:future></p:run></p:p><p:p id="7"><p:run><p:t>&lt;secret&gt;</p:t></p:run></p:p><!-- preserved --></s:sec>"#;

fn digest(source: &[u8]) -> [u8; 32] {
    Sha256::digest(source).into()
}
fn import(source: &[u8]) -> Result<ImportedSourcePackage, Box<dyn Error>> {
    Ok(ImportedSourcePackage::import(
        source,
        DocumentId::parse("source-test-document")?,
        digest(source),
        SourceImportLimits::default(),
    )?)
}

fn archive(section: &[u8], asset_media: &str, asset: &[u8]) -> Result<Vec<u8>, Box<dyn Error>> {
    let container = br#"<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/></rootfiles></container>"#;
    let opf = format!(
        r#"<o:package xmlns:o="http://www.idpf.org/2007/opf/"><o:manifest><o:item id="header" href="Contents/header.xml" media-type="application/xml"/><o:item id="section" href="Contents/section0.xml" media-type="application/xml"/><o:item id="asset" href="BinData/private.dat" media-type="{asset_media}"/></o:manifest><o:spine><o:itemref idref="section"/></o:spine></o:package>"#
    );
    let entries = [
        ("mimetype", b"application/hwp+zip".as_slice()),
        ("version.xml", b"<version/>".as_slice()),
        ("META-INF/container.xml", container.as_slice()),
        ("Contents/content.hpf", opf.as_bytes()),
        (
            "Contents/header.xml",
            b"<header private='TOPSECRET'/>".as_slice(),
        ),
        ("Contents/section0.xml", section),
        ("BinData/private.dat", asset),
    ];
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (path, bytes) in entries {
        writer.start_file(
            path,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

#[test]
fn complete_source_has_all_parts_elements_topology_and_exact_subtree_fingerprints() -> TestResult {
    let bytes = archive(
        SECTION.as_bytes(),
        "application/octet-stream",
        b"PRIVATE_BINARY",
    )?;
    let source = import(&bytes)?;
    assert_eq!(source.receipt().parts, 7);
    assert_eq!(source.receipt().xml_parts, 5);
    assert_eq!(source.spine()[0].as_str(), "Contents/section0.xml");
    let mut elements = 0;
    let mut tokens = 0;
    let mut binary = false;
    for part in source.parts() {
        let whole = source.resolve_anchor(part.anchor())?;
        assert!(whole.element().is_none());
        assert!(whole.element_index().is_none());
        assert_eq!(whole.part().path(), part.path());
        if part.path().as_str() == "BinData/private.dat" {
            assert!(part.xml().is_none());
            assert_eq!(part.anchor().fingerprint_sha256, digest(b"PRIVATE_BINARY"));
            binary = true;
        }
        if let Some(xml) = part.xml() {
            xml.verify_untouched_round_trip()?;
            elements += xml.elements().len();
            tokens += xml.tokens().len();
            for (index, element) in xml.elements().iter().enumerate() {
                let anchor = part.element_anchor(index).ok_or("missing real anchor")?;
                let resolved = source.resolve_anchor(anchor)?;
                assert_eq!(resolved.element(), Some(element));
                assert_eq!(resolved.element_index(), Some(index));
                if part.role() == PartRole::SpineDocument {
                    let span = element.outer_span().ok_or("missing span")?;
                    assert_eq!(
                        anchor.fingerprint_sha256,
                        digest(&SECTION.as_bytes()[span.start()..span.end()])
                    );
                }
            }
            assert!(part.element_anchor(xml.elements().len()).is_none());
        }
    }
    assert!(binary);
    assert_eq!(elements, source.receipt().xml_elements);
    assert_eq!(tokens, source.receipt().xml_tokens);
    let section = source
        .parts()
        .iter()
        .find(|p| p.role() == PartRole::SpineDocument)
        .ok_or("section")?;
    let xml = section.xml().ok_or("XML section")?;
    let p_ids: Vec<_> = xml
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, e)| e.name().namespace() == Some(NS) && e.name().local_name() == "p")
        .map(|(index, _)| index)
        .collect();
    assert_eq!(p_ids.len(), 2);
    assert!(section.element_anchor(p_ids[0]) != section.element_anchor(p_ids[1]));
    assert!(
        xml.elements()
            .iter()
            .any(|e| e.name().namespace() == Some("urn:unknown")
                && e.name().local_name() == "nested")
    );
    assert_eq!(source.verify_source(&bytes)?, *source.receipt());
    Ok(())
}

#[test]
fn same_source_fresh_import_reproduces_every_anchor_and_receipt() -> TestResult {
    let bytes = archive(SECTION.as_bytes(), "application/octet-stream", b"asset")?;
    let first = import(&bytes)?;
    let second = import(&bytes)?;
    assert!(first == second);
    assert_eq!(first.receipt(), second.receipt());
    for (left, right) in first.parts().iter().zip(second.parts()) {
        assert!(left.anchor() == right.anchor());
        if let Some(xml) = left.xml() {
            for index in 0..xml.elements().len() {
                assert!(left.element_anchor(index) == right.element_anchor(index));
                second.resolve_anchor(left.element_anchor(index).ok_or("anchor")?)?;
            }
        }
    }
    Ok(())
}

#[test]
fn document_and_package_version_are_in_identity_not_just_subtree_content() -> TestResult {
    let bytes = archive(SECTION.as_bytes(), "application/octet-stream", b"asset")?;
    let first = import(&bytes)?;
    let other_doc = ImportedSourcePackage::import(
        &bytes,
        DocumentId::parse("other-document")?,
        digest(&bytes),
        SourceImportLimits::default(),
    )?;
    assert_eq!(
        other_doc.resolve_anchor(first.parts()[0].anchor()).err(),
        Some(SourceImportError::Anchor)
    );
    let changed = archive(SECTION.as_bytes(), "application/octet-stream", b"changed")?;
    let new_version = import(&changed)?;
    assert_eq!(
        first.verify_source(&changed).err(),
        Some(SourceImportError::SourceChanged)
    );
    assert_eq!(
        new_version.resolve_anchor(first.parts()[0].anchor()).err(),
        Some(SourceImportError::Anchor)
    );
    assert_ne!(
        first.receipt().provenance_sha256,
        new_version.receipt().provenance_sha256
    );
    assert!(first.parts()[0].anchor() != other_doc.parts()[0].anchor());
    Ok(())
}

#[test]
fn forged_unknown_part_or_fingerprint_cannot_resolve() -> TestResult {
    let bytes = archive(SECTION.as_bytes(), "application/octet-stream", b"asset")?;
    let source = import(&bytes)?;
    let original = source.parts()[0].anchor();
    let forged = SourceAnchorHandle {
        opaque_handle: original.opaque_handle.clone(),
        fingerprint_sha256: [0; 32],
    };
    assert_eq!(
        source.resolve_anchor(&forged).err(),
        Some(SourceImportError::Anchor)
    );
    let unknown = SourceAnchorHandle {
        opaque_handle: LogicalId::parse("source-unknown")?,
        fingerprint_sha256: original.fingerprint_sha256,
    };
    assert_eq!(
        source.resolve_anchor(&unknown).err(),
        Some(SourceImportError::Anchor)
    );
    let other_part = SourceAnchorHandle {
        opaque_handle: original.opaque_handle.clone(),
        fingerprint_sha256: digest(b"asset"),
    };
    assert_eq!(
        source.resolve_anchor(&other_part).err(),
        Some(SourceImportError::Anchor)
    );
    Ok(())
}

#[test]
fn expected_digest_is_required_before_zip_or_xml_admission() -> TestResult {
    assert_eq!(
        ImportedSourcePackage::import(
            b"not a zip",
            DocumentId::parse("doc")?,
            [0; 32],
            SourceImportLimits::default()
        )
        .err(),
        Some(SourceImportError::SourceChanged)
    );
    let bytes = archive(SECTION.as_bytes(), "application/octet-stream", b"asset")?;
    assert_eq!(
        ImportedSourcePackage::import(
            &bytes,
            DocumentId::parse("doc")?,
            [0; 32],
            SourceImportLimits::default()
        )
        .err(),
        Some(SourceImportError::SourceChanged)
    );
    Ok(())
}

#[test]
fn unsafe_xml_and_media_mismatch_never_become_opaque() -> TestResult {
    for section in [
        br#"<!DOCTYPE sec [<!ENTITY e SYSTEM "file:///TOPSECRET">]><sec/>"#.as_slice(),
        b"<sec><unclosed></sec>".as_slice(),
        b"<sec>&undeclared;</sec>".as_slice(),
        b"<sec><![CDATA[unsupported]]></sec>".as_slice(),
    ] {
        let bytes = archive(section, "application/octet-stream", b"asset")?;
        assert_eq!(
            import(&bytes)
                .err()
                .and_then(|e| e.downcast::<SourceImportError>().ok())
                .map(|e| *e),
            Some(SourceImportError::RejectedPart)
        );
    }
    let bytes = archive(SECTION.as_bytes(), "image/png", b"not-png")?;
    assert_eq!(
        import(&bytes)
            .err()
            .and_then(|e| e.downcast::<SourceImportError>().ok())
            .map(|e| *e),
        Some(SourceImportError::RejectedPart)
    );
    Ok(())
}

#[test]
fn incomplete_package_closure_is_rejected() -> TestResult {
    let bytes = archive(SECTION.as_bytes(), "application/octet-stream", b"asset")?;
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    let mut zip = zip::ZipArchive::new(Cursor::new(&bytes))?;
    for index in 0..zip.len() {
        let mut entry = zip.by_index(index)?;
        writer.start_file(
            entry.name(),
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        std::io::copy(&mut entry, &mut writer)?;
    }
    writer.start_file("unlisted.private", SimpleFileOptions::default())?;
    writer.write_all(b"TOPSECRET")?;
    let opened = writer.finish()?.into_inner();
    assert_eq!(
        ImportedSourcePackage::import(
            &opened,
            DocumentId::parse("doc")?,
            digest(&opened),
            SourceImportLimits::default()
        )
        .err(),
        Some(SourceImportError::Graph)
    );
    Ok(())
}

#[test]
fn aggregate_and_input_limits_are_enforced_without_partial_return() -> TestResult {
    let bytes = archive(SECTION.as_bytes(), "application/octet-stream", b"asset")?;
    let configs = [
        SourceImportLimitConfig {
            archive_bytes: bytes.len() - 1,
            ..SourceImportLimitConfig::default()
        },
        SourceImportLimitConfig {
            xml_elements: 1,
            ..SourceImportLimitConfig::default()
        },
        SourceImportLimitConfig {
            xml_tokens: 1,
            ..SourceImportLimitConfig::default()
        },
        SourceImportLimitConfig {
            fingerprint_bytes: 1,
            ..SourceImportLimitConfig::default()
        },
    ];
    for config in configs {
        let result = ImportedSourcePackage::import(
            &bytes,
            DocumentId::parse("doc")?,
            digest(&bytes),
            SourceImportLimits::new(config)?,
        );
        assert_eq!(result.err(), Some(SourceImportError::Limit));
    }
    assert!(
        SourceImportLimits::new(SourceImportLimitConfig {
            parts: 0,
            ..SourceImportLimitConfig::default()
        })
        .is_err()
    );
    assert!(
        SourceImportLimits::new(SourceImportLimitConfig {
            xml_elements: 100_001,
            ..SourceImportLimitConfig::default()
        })
        .is_err()
    );
    Ok(())
}

#[test]
fn debug_errors_and_receipts_do_not_emit_document_values_or_private_paths() -> TestResult {
    let bytes = archive(
        SECTION.as_bytes(),
        "application/octet-stream",
        b"PRIVATE_BINARY",
    )?;
    let source = import(&bytes)?;
    let debug = format!(
        "{source:?} {:?} {:?}",
        source.parts(),
        source.resolve_anchor(source.parts()[0].anchor())?
    );
    let receipt = serde_json::to_string(source.receipt())?;
    for text in [debug, receipt, SourceImportError::Anchor.to_string()] {
        for forbidden in [
            "TOPSECRET",
            "PRIVATE_BINARY",
            "private.dat",
            "<p:",
            "한글",
            "file:///",
        ] {
            assert!(!text.contains(forbidden));
        }
    }
    assert!(
        source
            .receipt()
            .qualification
            .contains("typed_ir_security_lineage_route_native_gate_unqualified")
    );
    Ok(())
}

#[test]
fn all_ten_locked_form_packages_import_and_fresh_verify_without_native_execution() -> TestResult {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../fixtures/target-build/p09-42-product-form-values-01/output");
    let manifest: serde_json::Value =
        serde_json::from_slice(&std::fs::read(root.join("fixture-manifest.json"))?)?;
    let cases = manifest["cases"].as_array().ok_or("cases")?;
    assert_eq!(cases.len(), 5);
    let mut checked = 0;
    for row in cases {
        for kind in ["source", "output"] {
            let name = row[kind]["path"].as_str().ok_or("fixture path")?;
            assert!(!name.contains(['/', '\\', ':']));
            let path = root.join(name);
            let metadata = std::fs::symlink_metadata(&path)?;
            assert!(metadata.is_file() && !metadata.file_type().is_symlink());
            let bytes = std::fs::read(path)?;
            assert_eq!(
                bytes.len() as u64,
                row[kind]["bytes"].as_u64().ok_or("length")?
            );
            assert_eq!(
                hex::encode(digest(&bytes)),
                row[kind]["sha256"].as_str().ok_or("digest")?
            );
            let source = import(&bytes)?;
            assert_eq!(source.verify_source(&bytes)?, *source.receipt());
            assert!(!source.spine().is_empty());
            for part in source.parts() {
                source.resolve_anchor(part.anchor())?;
                if let Some(xml) = part.xml() {
                    for index in 0..xml.elements().len() {
                        source.resolve_anchor(
                            part.element_anchor(index).ok_or("real element anchor")?,
                        )?;
                    }
                }
            }
            checked += 1;
        }
    }
    assert_eq!(checked, 10);
    Ok(())
}
