use std::error::Error;
use std::io::{Cursor, Write};

use hwpx_package::{
    BoundedZipReader, GraphError, PackageGraph, PackageGraphLimitConfig, PackageGraphLimits,
    PackageLimits, PartRole, RelationshipKind,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;

const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;

const OPF: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="2.0">
  <opf:metadata><meta xmlns="urn:test" name="fixture"/></opf:metadata>
  <opf:manifest>
    <opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>
    <opf:item id="image" href="../BinData/image.png" media-type="image/png"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#;

#[test]
fn valid_hwpx_builds_a_closed_typed_graph() -> TestResult {
    let graph = graph_from(valid_archive(CONTAINER, OPF, &[]))?;
    assert_eq!(graph.package_document.as_str(), "Contents/content.hpf");
    assert_eq!(graph.parts.len(), 7);
    assert_eq!(graph.relationships.len(), 4);
    assert_eq!(graph.spine.len(), 1);
    assert_eq!(graph.spine[0].as_str(), "Contents/section0.xml");
    assert!(graph.parts.iter().all(|part| part.raw_sha256 != [0_u8; 32]));
    assert!(graph.parts.iter().any(|part| {
        part.path.as_str() == "Contents/section0.xml" && part.role == PartRole::SpineDocument
    }));
    assert!(graph.relationships.iter().any(|relationship| {
        relationship.kind == RelationshipKind::ManifestItem
            && relationship.target.as_str() == "BinData/image.png"
    }));

    let alternate_prefix = OPF
        .replace("opf:", "pkg:")
        .replace("xmlns:opf", "xmlns:pkg");
    let alternate = graph_from(valid_archive(CONTAINER, &alternate_prefix, &[]))?;
    assert_eq!(alternate.parts.len(), graph.parts.len());
    Ok(())
}

#[test]
fn mimetype_must_be_exact_stored_and_first() -> TestResult {
    let missing = archive(vec![
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
        entry(
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/content.hpf",
            OPF.as_bytes(),
            CompressionMethod::Deflated,
        ),
    ])?;
    expect_code(missing, "mimetype_missing")?;

    let not_first = archive(vec![
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
        entry(
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        entry(
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/content.hpf",
            OPF.as_bytes(),
            CompressionMethod::Deflated,
        ),
    ])?;
    expect_code(not_first, "mimetype_not_first")?;

    let deflated = replace_mimetype(CompressionMethod::Deflated, b"application/hwp+zip")?;
    expect_code(deflated, "mimetype_not_stored")?;
    let malformed = replace_mimetype(CompressionMethod::Stored, b"application/hwp+zip\n")?;
    expect_code(malformed, "mimetype_invalid")?;
    Ok(())
}

#[test]
fn container_requires_one_namespaced_existing_rootfile() -> TestResult {
    let no_container = archive(vec![
        entry(
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
    ])?;
    expect_code(no_container, "required_part_missing")?;

    let missing = CONTAINER.replace(
        "<rootfiles><rootfile full-path=\"Contents/content.hpf\" media-type=\"application/oebps-package+xml\"/></rootfiles>",
        "<rootfiles></rootfiles>",
    );
    expect_code(
        valid_archive(&missing, OPF, &[]),
        "container_rootfile_missing",
    )?;

    let duplicate = CONTAINER.replace(
        "</rootfiles>",
        "<rootfile full-path=\"Contents/other.hpf\" media-type=\"application/oebps-package+xml\"/></rootfiles>",
    );
    expect_code(
        valid_archive(&duplicate, OPF, &[]),
        "container_rootfile_duplicate",
    )?;

    let absent = CONTAINER.replace("Contents/content.hpf", "Contents/absent.hpf");
    expect_code(valid_archive(&absent, OPF, &[]), "package_document_missing")?;

    let wrong_namespace = CONTAINER.replace(CONTAINER_NS, "urn:wrong");
    expect_code(
        valid_archive(&wrong_namespace, OPF, &[]),
        "xml_namespace_invalid",
    )?;

    let missing_media = CONTAINER.replace(" media-type=\"application/oebps-package+xml\"", "");
    expect_code(
        valid_archive(&missing_media, OPF, &[]),
        "container_rootfile_invalid",
    )?;
    Ok(())
}

#[test]
fn manifest_rejects_duplicate_missing_and_orphan_parts() -> TestResult {
    let duplicate_id = OPF.replace("id=\"image\"", "id=\"header\"");
    expect_code(
        valid_archive(CONTAINER, &duplicate_id, &[]),
        "manifest_id_duplicate",
    )?;

    let duplicate_path = OPF.replace("href=\"section0.xml\"", "href=\"header.xml\"");
    expect_code(
        valid_archive(CONTAINER, &duplicate_path, &[]),
        "manifest_path_duplicate",
    )?;

    let normalized_duplicate = OPF.replace(
        "<opf:item id=\"section0\" href=\"section0.xml\" media-type=\"application/xml\"/>",
        "<opf:item id=\"section0\" href=\"section0.xml\" media-type=\"application/xml\"/><opf:item id=\"header-alias\" href=\"./header.xml\" media-type=\"application/xml\"/>",
    );
    expect_code(
        valid_archive(CONTAINER, &normalized_duplicate, &[]),
        "manifest_path_duplicate",
    )?;

    let missing_target = OPF.replace("href=\"header.xml\"", "href=\"absent.xml\"");
    expect_code(
        valid_archive(CONTAINER, &missing_target, &[]),
        "manifest_target_missing",
    )?;

    let orphan = [(
        "Contents/orphan.xml",
        b"<orphan/>".as_slice(),
        CompressionMethod::Stored,
    )];
    expect_code(valid_archive(CONTAINER, OPF, &orphan), "orphan_part")?;

    let invalid_media = OPF.replace("media-type=\"image/png\"", "media-type=\"invalid\"");
    expect_code(
        valid_archive(CONTAINER, &invalid_media, &[]),
        "invalid_media_type",
    )?;

    let wrong_namespace = OPF.replace("http://www.idpf.org/2007/opf", "urn:wrong");
    expect_code(
        valid_archive(CONTAINER, &wrong_namespace, &[]),
        "xml_namespace_invalid",
    )?;

    let rebound_namespace = OPF.replace("<opf:manifest>", "<opf:manifest xmlns:opf=\"urn:wrong\">");
    expect_code(
        valid_archive(CONTAINER, &rebound_namespace, &[]),
        "xml_namespace_invalid",
    )?;
    Ok(())
}

#[test]
fn spine_rejects_missing_duplicate_and_dangling_references() -> TestResult {
    let missing = OPF.replace(
        "<opf:spine><opf:itemref idref=\"section0\" linear=\"yes\"/></opf:spine>",
        "",
    );
    expect_code(valid_archive(CONTAINER, &missing, &[]), "spine_missing")?;

    let duplicate_section = OPF.replace("</opf:package>", "<opf:spine></opf:spine></opf:package>");
    expect_code(
        valid_archive(CONTAINER, &duplicate_section, &[]),
        "spine_duplicate_section",
    )?;

    let dangling = OPF.replace("idref=\"section0\"", "idref=\"absent\"");
    expect_code(valid_archive(CONTAINER, &dangling, &[]), "spine_dangling")?;

    let duplicate = OPF.replace(
        "</opf:spine>",
        "<opf:itemref idref=\"section0\" linear=\"no\"/></opf:spine>",
    );
    expect_code(valid_archive(CONTAINER, &duplicate, &[]), "spine_duplicate")?;
    Ok(())
}

#[test]
fn relationship_targets_are_bounded_internal_and_source_relative() -> TestResult {
    let external = OPF.replace("header.xml", "https://example.invalid/header.xml");
    expect_code(
        valid_archive(CONTAINER, &external, &[]),
        "external_relationship_blocked",
    )?;

    let escape = OPF.replace("header.xml", "../../escape.xml");
    expect_code(
        valid_archive(CONTAINER, &escape, &[]),
        "relationship_escapes_root",
    )?;

    let encoded_escape = OPF.replace("header.xml", "..%2F..%2Fescape.xml");
    expect_code(
        valid_archive(CONTAINER, &encoded_escape, &[]),
        "relationship_escapes_root",
    )?;

    let encoded_target = OPF.replace("header.xml", "%68eader.xml");
    let graph = graph_from(valid_archive(CONTAINER, &encoded_target, &[]))?;
    assert!(graph.relationships.iter().any(|relationship| {
        relationship.kind == RelationshipKind::ManifestItem
            && relationship.target.as_str() == "Contents/header.xml"
    }));
    Ok(())
}

#[test]
fn metadata_rejects_entities_processing_instructions_and_non_utf8_declarations() -> TestResult {
    let dtd = format!("<!DOCTYPE container [<!ENTITY x SYSTEM \"file:///secret\">]>{CONTAINER}");
    expect_code(valid_archive(&dtd, OPF, &[]), "xml_forbidden_construct")?;

    let pi = OPF.replace("<opf:manifest>", "<?target data?><opf:manifest>");
    expect_code(
        valid_archive(CONTAINER, &pi, &[]),
        "xml_forbidden_construct",
    )?;

    let encoding = CONTAINER.replace("UTF-8", "ISO-8859-1");
    expect_code(
        valid_archive(&encoding, OPF, &[]),
        "xml_forbidden_construct",
    )?;

    let unknown_reference = OPF.replace(
        "<opf:metadata>",
        "<opf:metadata><meta xmlns=\"urn:test\">&unknown;</meta>",
    );
    expect_code(
        valid_archive(CONTAINER, &unknown_reference, &[]),
        "xml_forbidden_construct",
    )?;

    let safe_references = OPF.replace(
        "<opf:metadata>",
        "<opf:metadata><meta xmlns=\"urn:test\">A &amp; B &#xAC00;</meta>",
    );
    let graph = graph_from(valid_archive(CONTAINER, &safe_references, &[]))?;
    assert_eq!(graph.spine.len(), 1);
    Ok(())
}

#[test]
fn graph_limits_are_finite_and_enforced() -> TestResult {
    let invalid = PackageGraphLimitConfig {
        max_xml_depth: 0,
        ..PackageGraphLimitConfig::default()
    };
    let Err(error) = PackageGraphLimits::new(invalid) else {
        panic!("zero graph limit was accepted");
    };
    assert_eq!(error.code(), "invalid_graph_limit");

    let depth_config = PackageGraphLimitConfig {
        max_xml_depth: 2,
        ..PackageGraphLimitConfig::default()
    };
    let depth_limits = PackageGraphLimits::new(depth_config)?;
    expect_code_with_limits(
        valid_archive(CONTAINER, OPF, &[]),
        depth_limits,
        "xml_limit_exceeded",
    )?;

    let size_config = PackageGraphLimitConfig {
        max_metadata_bytes: 32,
        ..PackageGraphLimitConfig::default()
    };
    let size_limits = PackageGraphLimits::new(size_config)?;
    expect_code_with_limits(
        valid_archive(CONTAINER, OPF, &[]),
        size_limits,
        "metadata_too_large",
    )?;
    Ok(())
}

const CONTAINER_NS: &str = "urn:oasis:names:tc:opendocument:xmlns:container";

fn valid_archive(
    container: &str,
    opf: &str,
    extra: &[(&str, &[u8], CompressionMethod)],
) -> Vec<u8> {
    let mut entries = vec![
        entry(
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
        entry(
            "META-INF/container.xml",
            container.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/content.hpf",
            opf.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/header.xml",
            b"<header/>",
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/section0.xml",
            b"<section/>",
            CompressionMethod::Deflated,
        ),
        entry(
            "BinData/image.png",
            b"not-a-real-png",
            CompressionMethod::Stored,
        ),
    ];
    entries.extend(
        extra
            .iter()
            .map(|(name, bytes, method)| entry(name, bytes, *method)),
    );
    archive(entries).unwrap_or_else(|error| panic!("in-memory ZIP fixture failed: {error}"))
}

fn replace_mimetype(
    method: CompressionMethod,
    value: &[u8],
) -> Result<Vec<u8>, zip::result::ZipError> {
    archive(vec![
        entry("mimetype", value, method),
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
        entry(
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/content.hpf",
            OPF.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/header.xml",
            b"<header/>",
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/section0.xml",
            b"<section/>",
            CompressionMethod::Deflated,
        ),
        entry(
            "BinData/image.png",
            b"not-a-real-png",
            CompressionMethod::Stored,
        ),
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

fn graph_from(bytes: Vec<u8>) -> Result<PackageGraph, GraphError> {
    let package_limits = PackageLimits::default();
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), package_limits)?;
    PackageGraph::build(&mut reader, PackageGraphLimits::default())
}

fn expect_code(bytes: Vec<u8>, expected: &str) -> TestResult {
    expect_code_with_limits(bytes, PackageGraphLimits::default(), expected)
}

fn expect_code_with_limits(
    bytes: Vec<u8>,
    graph_limits: PackageGraphLimits,
    expected: &str,
) -> TestResult {
    let package_limits = PackageLimits::default();
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), package_limits)?;
    let Err(error) = PackageGraph::build(&mut reader, graph_limits) else {
        panic!("invalid graph fixture was accepted");
    };
    assert_eq!(error.code(), expected);
    Ok(())
}
