use std::error::Error;
use std::io::{Cursor, Write};

use hwpx_package::{
    BoundedZipReader, Compression, PackageGraph, PackageGraphLimits, PackageLimits,
    PartPreservationRecord, PreservationClass, PreservationReport, PreservationRuleProfile,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;
type TestReader = BoundedZipReader<Cursor<Vec<u8>>>;
type OpenedGraph = (TestReader, PackageGraph);

const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;

#[test]
fn known_fixture_has_complete_evidence_ranked_map() -> TestResult {
    let bytes = valid_archive(
        b"<header/>",
        "../BinData/image.png",
        "BinData/image.png",
        "image/png",
        png(),
    )?;
    let (mut reader, mut graph) = open_graph(bytes)?;
    graph.parts.reverse();
    let report = PreservationReport::build(&mut reader, &graph)?;

    assert_eq!(report.parts().len(), 7);
    assert_eq!(report.counts().byte_exact, 1);
    assert_eq!(report.counts().token_stable, 5);
    assert_eq!(report.counts().semantic, 0);
    assert_eq!(report.counts().regenerated, 0);
    assert_eq!(report.counts().opaque, 1);
    assert_eq!(report.counts().rejected, 0);
    assert!(report.direct_preserve_ready());
    assert!(
        report
            .parts()
            .windows(2)
            .all(|pair| pair[0].path() < pair[1].path())
    );

    let mimetype = record(&report, "mimetype");
    assert_eq!(mimetype.class(), PreservationClass::ByteExact);
    assert_eq!(mimetype.source_entry_index(), 0);
    assert_eq!(mimetype.compression(), Compression::Stored);
    assert!(mimetype.compressed_size() > 0);
    assert!(mimetype.crc32() > 0);
    assert_eq!(
        record(&report, "Contents/section0.xml").class(),
        PreservationClass::TokenStable
    );
    assert_eq!(
        record(&report, "BinData/image.png").class(),
        PreservationClass::Opaque
    );
    let token = record(&report, "Contents/header.xml")
        .token_evidence()
        .ok_or_else(|| std::io::Error::other("token evidence missing"))?;
    assert!(token.untouched_verified());
    assert!(token.token_count() > 0);
    assert!(token.element_count() > 0);
    assert_eq!(
        token.source_sha256(),
        record(&report, "Contents/header.xml").raw_sha256()
    );
    Ok(())
}

#[test]
fn unsafe_xml_is_explicitly_rejected_without_hiding_other_parts() -> TestResult {
    let header = br#"<!DOCTYPE header [<!ENTITY leak SYSTEM "file:///TOPSECRET">]><header/>"#;
    let bytes = valid_archive(
        header,
        "../BinData/image.png",
        "BinData/image.png",
        "image/png",
        png(),
    )?;
    let (mut reader, graph) = open_graph(bytes)?;
    let report = PreservationReport::build(&mut reader, &graph)?;
    let rejected = record(&report, "Contents/header.xml");

    assert_eq!(rejected.class(), PreservationClass::Rejected);
    assert_eq!(rejected.reason_code(), "safe_xml_dtd_forbidden");
    assert_eq!(report.counts().rejected, 1);
    assert_eq!(report.counts().total(), report.parts().len());
    assert!(!report.direct_preserve_ready());
    let debug = format!("{report:?}");
    assert!(!debug.contains("TOPSECRET"));
    assert!(!debug.contains("file:///"));
    Ok(())
}

#[test]
fn media_and_magic_mismatches_never_downgrade_to_opaque() -> TestResult {
    let cases = [
        (
            valid_archive(
                b"<header/>",
                "asset.xml",
                "Contents/asset.xml",
                "image/png",
                png(),
            )?,
            "Contents/asset.xml",
            "preservation_rejected_xml_media_path_mismatch",
        ),
        (
            valid_archive(
                b"<header/>",
                "../BinData/image.png",
                "BinData/image.png",
                "image/png",
                b"<svg/>",
            )?,
            "BinData/image.png",
            "preservation_rejected_xml_content_media_mismatch",
        ),
        (
            valid_archive(
                b"<header/>",
                "../BinData/image.png",
                "BinData/image.png",
                "image/png",
                b"not-a-png",
            )?,
            "BinData/image.png",
            "preservation_rejected_binary_signature_mismatch",
        ),
    ];
    for (bytes, path, reason) in cases {
        let (mut reader, graph) = open_graph(bytes)?;
        let report = PreservationReport::build(&mut reader, &graph)?;
        let part = record(&report, path);
        assert_eq!(part.class(), PreservationClass::Rejected);
        assert_eq!(part.reason_code(), reason);
        assert!(!report.direct_preserve_ready());
    }
    Ok(())
}

#[test]
fn unknown_non_xml_part_stays_opaque_without_semantic_promotion() -> TestResult {
    let bytes = valid_archive(
        b"<header/>",
        "../BinData/blob.bin",
        "BinData/blob.bin",
        "application/octet-stream",
        b"opaque-fixture-bytes",
    )?;
    let (mut reader, graph) = open_graph(bytes)?;
    let report = PreservationReport::build(&mut reader, &graph)?;
    let part = record(&report, "BinData/blob.bin");

    assert_eq!(part.class(), PreservationClass::Opaque);
    assert_eq!(part.reason_code(), "preservation_opaque_unrecognized_media");
    assert_eq!(report.counts().semantic, 0);
    assert_eq!(report.counts().regenerated, 0);
    assert!(report.direct_preserve_ready());
    Ok(())
}

#[test]
fn exact_plain_text_preview_may_start_with_table_angle_brackets() -> TestResult {
    let bytes = valid_archive(
        b"<header/>",
        "../Preview/PrvText.txt",
        "Preview/PrvText.txt",
        "text/plain",
        b"<first-cell><second-cell>\r\n",
    )?;
    let (mut reader, graph) = open_graph(bytes.clone())?;
    let v1_report = PreservationReport::build(&mut reader, &graph)?;
    let v1_preview = record(&v1_report, "Preview/PrvText.txt");
    assert_eq!(v1_preview.class(), PreservationClass::Rejected);
    assert_eq!(
        v1_preview.reason_code(),
        "preservation_rejected_xml_content_media_mismatch"
    );

    let (mut reader, graph) = open_graph(bytes)?;
    let report = PreservationReport::build_with_profile(
        &mut reader,
        &graph,
        PreservationRuleProfile::Hangul2020PreviewTextV2,
    )?;
    let preview = record(&report, "Preview/PrvText.txt");

    assert_eq!(preview.class(), PreservationClass::Opaque);
    assert_eq!(preview.reason_code(), "preservation_opaque_preview_text");
    assert_eq!(report.counts().rejected, 0);
    assert!(report.direct_preserve_ready());
    Ok(())
}

#[test]
fn angle_bracket_text_outside_exact_preview_path_stays_rejected() -> TestResult {
    let bytes = valid_archive(
        b"<header/>",
        "../Other/notes.txt",
        "Other/notes.txt",
        "text/plain",
        b"<not-the-preview/>",
    )?;
    let (mut reader, graph) = open_graph(bytes)?;
    let report = PreservationReport::build(&mut reader, &graph)?;
    let notes = record(&report, "Other/notes.txt");

    assert_eq!(notes.class(), PreservationClass::Rejected);
    assert_eq!(
        notes.reason_code(),
        "preservation_rejected_xml_content_media_mismatch"
    );
    assert!(!report.direct_preserve_ready());
    Ok(())
}

#[test]
fn graph_shape_and_raw_identity_drift_fail_closed() -> TestResult {
    let bytes = valid_archive(
        b"<header/>",
        "../BinData/image.png",
        "BinData/image.png",
        "image/png",
        png(),
    )?;
    let (mut reader, mut graph) = open_graph(bytes)?;
    graph.parts[0].raw_sha256 = [0_u8; 32];
    let Err(error) = PreservationReport::build(&mut reader, &graph) else {
        panic!("raw identity drift was accepted");
    };
    assert_eq!(error.code(), "preservation_identity_mismatch");

    let bytes = valid_archive(
        b"<header/>",
        "../BinData/image.png",
        "BinData/image.png",
        "image/png",
        png(),
    )?;
    let (mut reader, mut graph) = open_graph(bytes)?;
    graph.parts.pop();
    let Err(error) = PreservationReport::build(&mut reader, &graph) else {
        panic!("missing graph part was accepted");
    };
    assert_eq!(error.code(), "preservation_graph_shape_mismatch");

    let bytes = valid_archive(
        b"<header/>",
        "../BinData/image.png",
        "BinData/image.png",
        "image/png",
        png(),
    )?;
    let (mut reader, mut graph) = open_graph(bytes)?;
    graph.parts.push(graph.parts[0].clone());
    let Err(error) = PreservationReport::build(&mut reader, &graph) else {
        panic!("extra graph part was accepted");
    };
    assert_eq!(error.code(), "preservation_graph_shape_mismatch");

    let bytes = valid_archive(
        b"<header/>",
        "../BinData/image.png",
        "BinData/image.png",
        "image/png",
        png(),
    )?;
    let (mut reader, mut graph) = open_graph(bytes)?;
    let Some(xml_index) = graph
        .parts
        .iter()
        .position(|part| part.path.as_str() == "Contents/header.xml")
    else {
        panic!("XML graph part missing");
    };
    let Some(image_index) = graph
        .parts
        .iter()
        .position(|part| part.path.as_str() == "BinData/image.png")
    else {
        panic!("image graph part missing");
    };
    graph.parts[image_index].media_type = graph.parts[xml_index].media_type.clone();
    let Err(error) = PreservationReport::build(&mut reader, &graph) else {
        panic!("mutated graph media type was accepted");
    };
    assert_eq!(error.code(), "preservation_graph_shape_mismatch");
    Ok(())
}

fn record<'a>(report: &'a PreservationReport, path: &str) -> &'a PartPreservationRecord {
    let Some(record) = report
        .parts()
        .iter()
        .find(|record| record.path().as_str() == path)
    else {
        panic!("expected preservation record missing");
    };
    record
}

fn png() -> &'static [u8] {
    b"\x89PNG\r\n\x1a\nfixture"
}

fn valid_archive(
    header: &[u8],
    asset_href: &str,
    asset_entry: &str,
    asset_media: &str,
    asset_bytes: &[u8],
) -> Result<Vec<u8>, zip::result::ZipError> {
    let opf = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="2.0">
  <opf:manifest>
    <opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>
    <opf:item id="asset" href="{asset_href}" media-type="{asset_media}"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#
    );
    archive(vec![
        entry(
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
        entry(
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/content.hpf",
            opf.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry("Contents/header.xml", header, CompressionMethod::Deflated),
        entry(
            "Contents/section0.xml",
            b"<section/>",
            CompressionMethod::Deflated,
        ),
        entry(asset_entry, asset_bytes, CompressionMethod::Stored),
    ])
}

fn entry(
    name: &str,
    bytes: &[u8],
    method: CompressionMethod,
) -> (String, Vec<u8>, CompressionMethod) {
    (name.to_owned(), bytes.to_vec(), method)
}

fn archive(
    entries: Vec<(String, Vec<u8>, CompressionMethod)>,
) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, bytes, method) in entries {
        let options = SimpleFileOptions::default().compression_method(method);
        writer.start_file(name, options)?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn open_graph(bytes: Vec<u8>) -> Result<OpenedGraph, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok((reader, graph))
}
