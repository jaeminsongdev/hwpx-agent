use std::error::Error;
use std::fmt::Write as _;
use std::io::{Cursor, Write};
use std::path::Path;

use hwpx_package::{
    AssetDisposition, AssetLimitConfig, AssetLimits, AssetMedia, AssetStoreAdapter,
    BoundedZipReader, IdIndexLimits, PackageGraph, PackageGraphLimits, PackageLimits, PatchLimits,
    PatchPartDisposition, PreservingPatchEngine, PreservingWriter, WriterLimits,
};
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;

const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;

const HEADER: &str = r#"<h:head xmlns:h="http://www.hancom.co.kr/hwpml/2011/head">
  <h:fontface lang="HANGUL"><h:font id="1"/></h:fontface>
  <h:fontface lang="LATIN"><h:font id="1"/></h:fontface>
  <h:fontface lang="HANJA"><h:font id="1"/></h:fontface>
  <h:fontface lang="JAPANESE"><h:font id="1"/></h:fontface>
  <h:fontface lang="OTHER"><h:font id="1"/></h:fontface>
  <h:fontface lang="SYMBOL"><h:font id="1"/></h:fontface>
  <h:fontface lang="USER"><h:font id="1"/></h:fontface>
  <h:borderFill id="1"/><h:charPr id="1" borderFillIDRef="1"><h:fontRef hangul="1" latin="1" hanja="1" japanese="1" other="1" symbol="1" user="1"/></h:charPr>
  <h:tabPr id="1"/><h:numbering id="1"/><h:bullet id="1"/>
  <h:paraPr id="1" tabPrIDRef="1"><h:heading type="OUTLINE" idRef="0"/><h:paraHead charPrIDRef="1"/></h:paraPr>
  <h:style id="1" charPrIDRef="1" paraPrIDRef="1" nextStyleIDRef="1"/><h:memoShape id="1"/>
</h:head>"#;

const SECTION: &str = r#"<q:section xmlns:q="http://www.hancom.co.kr/hwpml/2011/paragraph">
  <q:p id="1" paraPrIDRef="1" styleIDRef="1"><q:run charPrIDRef="1"><q:t>asset base</q:t></q:run></q:p>
</q:section>"#;

#[test]
fn new_png_plan_is_deterministic_strict_and_redacted() -> TestResult {
    let graph = minimal_graph()?;
    let payload = png(2, 3);
    let adapter = AssetStoreAdapter::default();
    let first = adapter.build("image/png", &payload, &graph)?;
    let second = adapter.build("image/png", &payload, &graph)?;
    assert_eq!(first, second);
    assert_eq!(first.disposition(), AssetDisposition::AddNew);
    assert_eq!(first.media(), AssetMedia::Png);
    assert_eq!((first.width_px(), first.height_px()), (2, 3));
    assert_eq!(first.content_bytes(), payload.len());
    assert!(first.target_path().as_str().starts_with("BinData/p08-"));
    assert!(
        Path::new(first.target_path().as_str())
            .extension()
            .is_some_and(|extension| extension.eq_ignore_ascii_case("png"))
    );
    assert!(first.relationship_id().starts_with("p08-"));
    assert_eq!(first.content_sha256().len(), 64);
    assert_eq!(first.source_graph_sha256().len(), 64);
    assert_eq!(first.plan_sha256().len(), 64);

    let json = adapter.to_private_plan_json(&first)?;
    assert!(!String::from_utf8_lossy(&json).contains("IDAT"));
    let raw_sha256 = hex::encode(Sha256::digest(&json));
    let loaded = adapter.load_private_plan_json(&json, &raw_sha256, &payload, &graph)?;
    assert_eq!(loaded, first);

    let debug = format!("{first:?}");
    for secret in [
        first.relationship_id(),
        first.target_path().as_str(),
        first.content_sha256(),
        first.source_graph_sha256(),
        first.plan_sha256(),
    ] {
        assert!(!debug.contains(secret));
    }
    Ok(())
}

#[test]
fn all_five_profile_media_are_structurally_sniffed() -> TestResult {
    let graph = minimal_graph()?;
    let adapter = AssetStoreAdapter::default();
    for (declared, payload, media, dimensions) in [
        ("image/png", png(2, 3), AssetMedia::Png, (2, 3)),
        ("image/jpeg", jpeg(4, 5), AssetMedia::Jpeg, (4, 5)),
        ("image/gif", gif(6, 7), AssetMedia::Gif, (6, 7)),
        ("image/webp", webp_lossless(8, 9), AssetMedia::Webp, (8, 9)),
        ("image/bmp", bmp(10, 11), AssetMedia::Bmp, (10, 11)),
    ] {
        let plan = adapter.build(declared, &payload, &graph)?;
        assert_eq!(plan.media(), media);
        assert_eq!((plan.width_px(), plan.height_px()), dimensions);
    }
    Ok(())
}

#[test]
fn malformed_truncated_and_mismatched_media_fail_closed() -> TestResult {
    let graph = minimal_graph()?;
    let adapter = AssetStoreAdapter::default();
    assert_code(
        adapter.build("image/jpeg", &png(1, 1), &graph),
        "asset_declared_media_mismatch",
    );
    assert_code(
        adapter.build("image/tiff", &png(1, 1), &graph),
        "asset_unsupported_media",
    );
    assert_code(
        adapter.build("image/png", b"\x89PNG", &graph),
        "asset_malformed_media",
    );
    assert_code(
        adapter.build("image/png", b"not an image", &graph),
        "asset_unsupported_media",
    );
    assert_code(adapter.build("image/png", &[], &graph), "asset_empty");

    let mut bad_crc = png(1, 1);
    bad_crc[29] ^= 1;
    assert_code(
        adapter.build("image/png", &bad_crc, &graph),
        "asset_malformed_media",
    );
    let mut trailing = gif(1, 1);
    trailing.push(0);
    assert_code(
        adapter.build("image/gif", &trailing, &graph),
        "asset_malformed_media",
    );
    let mut bad_riff = webp_lossless(1, 1);
    bad_riff[4] = 0;
    assert_code(
        adapter.build("image/webp", &bad_riff, &graph),
        "asset_malformed_media",
    );
    let mut no_eoi = jpeg(1, 1);
    no_eoi.truncate(no_eoi.len() - 2);
    assert_code(
        adapter.build("image/jpeg", &no_eoi, &graph),
        "asset_malformed_media",
    );
    let mut bad_bmp = bmp(1, 1);
    bad_bmp[28] = 0;
    bad_bmp[29] = 0;
    assert_code(
        adapter.build("image/bmp", &bad_bmp, &graph),
        "asset_malformed_media",
    );
    Ok(())
}

#[test]
fn byte_dimension_pixel_and_inventory_limits_are_enforced() -> TestResult {
    let graph = minimal_graph()?;
    let tight_bytes = adapter(AssetLimitConfig {
        max_asset_bytes: 8,
        ..AssetLimitConfig::default()
    })?;
    assert_code(
        tight_bytes.build("image/png", &png(1, 1), &graph),
        "asset_too_large",
    );
    let tight_patch = AssetStoreAdapter::new(
        AssetLimits::default(),
        PackageLimits::default(),
        PackageGraphLimits::default(),
        PatchLimits::new(hwpx_package::PatchLimitConfig {
            max_added_part_bytes: 8,
            ..hwpx_package::PatchLimitConfig::default()
        })?,
    );
    assert_code(
        tight_patch.build("image/png", &png(1, 1), &graph),
        "asset_too_large",
    );

    let tight_dimension = adapter(AssetLimitConfig {
        max_dimension_px: 1,
        ..AssetLimitConfig::default()
    })?;
    assert_code(
        tight_dimension.build("image/png", &png(2, 1), &graph),
        "asset_dimension_limit",
    );
    let tight_pixels = adapter(AssetLimitConfig {
        max_pixels: 3,
        ..AssetLimitConfig::default()
    })?;
    assert_code(
        tight_pixels.build("image/png", &png(2, 2), &graph),
        "asset_dimension_limit",
    );

    let payload = png(1, 1);
    let graph = graph_with_assets(&payload, 2, false)?;
    let tight_inventory = adapter(AssetLimitConfig {
        max_existing_assets: 1,
        ..AssetLimitConfig::default()
    })?;
    assert_code(
        tight_inventory.build("image/png", &png(2, 2), &graph),
        "asset_existing_inventory_limit",
    );
    Ok(())
}

#[test]
fn existing_content_is_reused_without_duplicate_patch_intents() -> TestResult {
    let payload = png(2, 2);
    let graph = graph_with_assets(&payload, 1, false)?;
    let adapter = AssetStoreAdapter::default();
    let plan = adapter.build("image/png", &payload, &graph)?;
    assert_eq!(plan.disposition(), AssetDisposition::ReusedExisting);
    assert_eq!(plan.relationship_id(), "existing-0");
    assert_eq!(plan.target_path().as_str(), "BinData/existing-0.png");
    assert!(adapter.build_patch_intents(&plan, &graph)?.is_empty());
    Ok(())
}

#[test]
fn ambiguous_relationships_and_digest_media_conflicts_fail_closed() -> TestResult {
    let payload = png(1, 1);
    let mut ambiguous = graph_with_assets(&payload, 1, false)?;
    let asset_relationship = ambiguous
        .relationships
        .iter()
        .find(|relationship| relationship.id == "existing-0")
        .ok_or("missing asset relationship")?
        .clone();
    ambiguous.relationships.push(asset_relationship);
    ambiguous
        .relationships
        .last_mut()
        .ok_or("missing alias")?
        .id = "alias".to_owned();
    assert_code(
        AssetStoreAdapter::default().build("image/png", &payload, &ambiguous),
        "asset_relationship_broken",
    );

    let conflicting = graph_with_assets(&payload, 1, true)?;
    assert_code(
        AssetStoreAdapter::default().build("image/png", &payload, &conflicting),
        "asset_existing_media_mismatch",
    );
    Ok(())
}

#[test]
fn source_graph_and_private_plan_tampering_are_rejected() -> TestResult {
    let graph = minimal_graph()?;
    let payload = png(1, 1);
    let adapter = AssetStoreAdapter::default();
    let plan = adapter.build("image/png", &payload, &graph)?;
    let mut drifted = graph.clone();
    drifted.parts[0].expanded_size += 1;
    assert_code(
        adapter.build_patch_intents(&plan, &drifted),
        "asset_source_graph_drift",
    );

    let json = adapter.to_private_plan_json(&plan)?;
    let raw_sha256 = hex::encode(Sha256::digest(&json));
    let mut value: Value = serde_json::from_slice(&json)?;
    value["width_px"] = Value::from(2);
    let tampered = serde_json::to_vec(&value)?;
    let tampered_sha256 = hex::encode(Sha256::digest(&tampered));
    assert_code(
        adapter.load_private_plan_json(&tampered, &tampered_sha256, &payload, &graph),
        "asset_plan_mismatch",
    );
    assert_code(
        adapter.load_private_plan_json(&json, &"0".repeat(64), &payload, &graph),
        "asset_untrusted_plan",
    );
    assert_code(
        adapter.load_private_plan_json(&json, &raw_sha256, &png(2, 2), &graph),
        "asset_plan_mismatch",
    );

    let mut duplicate = String::from_utf8(json)?;
    duplicate.insert_str(1, "\"schema_version\":\"hwpx-agent.asset-pipeline/v1\",");
    let duplicate_sha256 = hex::encode(Sha256::digest(duplicate.as_bytes()));
    assert_code(
        adapter.load_private_plan_json(duplicate.as_bytes(), &duplicate_sha256, &payload, &graph),
        "asset_invalid_json",
    );
    Ok(())
}

#[test]
fn deterministic_relationship_and_part_collisions_fail_closed() -> TestResult {
    let graph = minimal_graph()?;
    let payload = png(1, 1);
    let adapter = AssetStoreAdapter::default();
    let plan = adapter.build("image/png", &payload, &graph)?;

    let mut id_collision = graph.clone();
    let manifest = id_collision
        .relationships
        .iter_mut()
        .find(|relationship| relationship.id == "header")
        .ok_or("missing header relationship")?;
    manifest.id = plan.relationship_id().to_owned();
    assert_code(
        adapter.build("image/png", &payload, &id_collision),
        "asset_relationship_id_collision",
    );

    let mut part_collision = graph;
    part_collision.parts[0].path = plan.target_path().clone();
    assert_code(
        adapter.build("image/png", &payload, &part_collision),
        "asset_part_collision",
    );
    Ok(())
}

#[test]
fn new_asset_part_and_manifest_relationship_apply_atomically_and_reopen() -> TestResult {
    let bytes = valid_archive()?;
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let payload = png(2, 2);
    let adapter = AssetStoreAdapter::default();
    let plan = adapter.build("image/png", &payload, &graph)?;
    let intents = adapter.build_patch_intents(&plan, &graph)?;
    assert_eq!(intents.len(), 2);
    let patch = PreservingPatchEngine::apply(&mut reader, &graph, &intents)?;
    patch.verify_artifact_integrity()?;
    assert_eq!(patch.added_parts(), 1);
    assert_eq!(patch.changed_parts(), 1);
    assert_eq!(patch.relationship_count(), 1);
    let asset = patch
        .parts()
        .iter()
        .find(|record| record.path() == plan.target_path())
        .ok_or("missing added asset")?;
    assert_eq!(asset.disposition(), PatchPartDisposition::Added);
    assert_eq!(hex::encode(asset.output_sha256()), plan.content_sha256());
    let artifact = PreservingWriter::build(
        &patch,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        IdIndexLimits::default(),
        WriterLimits::default(),
    )?;
    artifact.verify()?;
    Ok(())
}

#[test]
fn invalid_limit_values_and_error_codes_are_stable() {
    let zero = AssetLimits::new(AssetLimitConfig {
        max_asset_bytes: 0,
        ..AssetLimitConfig::default()
    });
    assert_code(zero, "asset_invalid_limit");
    let excessive = AssetLimits::new(AssetLimitConfig {
        max_asset_bytes: 256 * 1024 * 1024 + 1,
        ..AssetLimitConfig::default()
    });
    assert_code(excessive, "asset_invalid_limit");
}

fn adapter(config: AssetLimitConfig) -> Result<AssetStoreAdapter, Box<dyn Error>> {
    Ok(AssetStoreAdapter::new(
        AssetLimits::new(config)?,
        PackageLimits::default(),
        PackageGraphLimits::default(),
        PatchLimits::default(),
    ))
}

fn minimal_graph() -> Result<PackageGraph, Box<dyn Error>> {
    graph_from_archive(valid_archive()?)
}

fn graph_with_assets(
    payload: &[u8],
    count: usize,
    conflicting_media: bool,
) -> Result<PackageGraph, Box<dyn Error>> {
    let mut manifest = String::from(
        r#"<opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>"#,
    );
    let mut entries = vec![
        (
            "mimetype".to_owned(),
            b"application/hwp+zip".to_vec(),
            CompressionMethod::Stored,
        ),
        (
            "META-INF/container.xml".to_owned(),
            CONTAINER.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "version.xml".to_owned(),
            b"<v/>".to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/header.xml".to_owned(),
            HEADER.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/section0.xml".to_owned(),
            SECTION.as_bytes().to_vec(),
            CompressionMethod::Deflated,
        ),
    ];
    for index in 0..count {
        let media = if conflicting_media && index == 0 {
            "image/jpeg"
        } else {
            "image/png"
        };
        write!(
            manifest,
            "\n    <opf:item id=\"existing-{index}\" href=\"../BinData/existing-{index}.png\" media-type=\"{media}\"/>"
        )?;
        let bytes = if index == 0 {
            payload.to_vec()
        } else {
            let width = u32::try_from(index + 1).map_err(|_| "test asset count exceeds u32")?;
            png(width, 1)
        };
        entries.push((
            format!("BinData/existing-{index}.png"),
            bytes,
            CompressionMethod::Deflated,
        ));
    }
    let content = format!(
        r#"<opf:package xmlns:opf="http://www.idpf.org/2007/opf">
  <opf:manifest>{manifest}</opf:manifest>
  <opf:spine><opf:itemref idref="section0"/></opf:spine>
</opf:package>"#
    );
    entries.push((
        "Contents/content.hpf".to_owned(),
        content.into_bytes(),
        CompressionMethod::Deflated,
    ));
    graph_from_archive(archive_owned(&entries)?)
}

fn valid_archive() -> Result<Vec<u8>, Box<dyn Error>> {
    let content = r#"<opf:package xmlns:opf="http://www.idpf.org/2007/opf">
  <opf:manifest>
    <opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0"/></opf:spine>
</opf:package>"#;
    archive(&[
        (
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        (
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        ("version.xml", b"<v/>", CompressionMethod::Deflated),
        (
            "Contents/content.hpf",
            content.as_bytes(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/header.xml",
            HEADER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        (
            "Contents/section0.xml",
            SECTION.as_bytes(),
            CompressionMethod::Deflated,
        ),
    ])
}

fn archive(entries: &[(&str, &[u8], CompressionMethod)]) -> Result<Vec<u8>, Box<dyn Error>> {
    let cursor = Cursor::new(Vec::new());
    let mut writer = ZipWriter::new(cursor);
    for (name, bytes, compression) in entries {
        writer.start_file(
            *name,
            SimpleFileOptions::default().compression_method(*compression),
        )?;
        writer.write_all(bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn archive_owned(
    entries: &[(String, Vec<u8>, CompressionMethod)],
) -> Result<Vec<u8>, Box<dyn Error>> {
    let cursor = Cursor::new(Vec::new());
    let mut writer = ZipWriter::new(cursor);
    for (name, bytes, compression) in entries {
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(*compression),
        )?;
        writer.write_all(bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn graph_from_archive(bytes: Vec<u8>) -> Result<PackageGraph, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    Ok(PackageGraph::build(
        &mut reader,
        PackageGraphLimits::default(),
    )?)
}

fn png(width: u32, height: u32) -> Vec<u8> {
    let mut output = b"\x89PNG\r\n\x1a\n".to_vec();
    let mut ihdr = Vec::new();
    ihdr.extend_from_slice(&width.to_be_bytes());
    ihdr.extend_from_slice(&height.to_be_bytes());
    ihdr.extend_from_slice(&[8, 6, 0, 0, 0]);
    png_chunk(&mut output, *b"IHDR", &ihdr);
    png_chunk(&mut output, *b"IDAT", &[0]);
    png_chunk(&mut output, *b"IEND", &[]);
    output
}

fn png_chunk(output: &mut Vec<u8>, kind: [u8; 4], data: &[u8]) {
    let Ok(length) = u32::try_from(data.len()) else {
        panic!("test PNG chunk exceeds u32");
    };
    output.extend_from_slice(&length.to_be_bytes());
    output.extend_from_slice(&kind);
    output.extend_from_slice(data);
    let mut crc_data = kind.to_vec();
    crc_data.extend_from_slice(data);
    output.extend_from_slice(&crc32(&crc_data).to_be_bytes());
}

fn jpeg(width: u16, height: u16) -> Vec<u8> {
    let mut output = vec![0xff, 0xd8, 0xff, 0xc0, 0, 11, 8];
    output.extend_from_slice(&height.to_be_bytes());
    output.extend_from_slice(&width.to_be_bytes());
    output.extend_from_slice(&[1, 1, 0x11, 0]);
    output.extend_from_slice(&[0xff, 0xda, 0, 8, 1, 1, 0, 0, 63, 0]);
    output.extend_from_slice(&[0, 0xff, 0xd9]);
    output
}

fn gif(width: u16, height: u16) -> Vec<u8> {
    let mut output = b"GIF89a".to_vec();
    output.extend_from_slice(&width.to_le_bytes());
    output.extend_from_slice(&height.to_le_bytes());
    output.extend_from_slice(&[0x80, 0, 0]);
    output.extend_from_slice(&[0, 0, 0, 0xff, 0xff, 0xff]);
    output.push(0x2c);
    output.extend_from_slice(&[0, 0, 0, 0]);
    output.extend_from_slice(&width.to_le_bytes());
    output.extend_from_slice(&height.to_le_bytes());
    output.push(0);
    output.extend_from_slice(&[2, 1, 0, 0, 0x3b]);
    output
}

fn webp_lossless(width: u32, height: u32) -> Vec<u8> {
    let bits = (width - 1) | ((height - 1) << 14);
    let mut data = vec![0x2f];
    data.extend_from_slice(&bits.to_le_bytes());
    let riff_size = 4 + 8 + data.len() + (data.len() & 1);
    let Ok(riff_size) = u32::try_from(riff_size) else {
        panic!("test WebP RIFF exceeds u32");
    };
    let Ok(data_size) = u32::try_from(data.len()) else {
        panic!("test WebP data exceeds u32");
    };
    let mut output = b"RIFF".to_vec();
    output.extend_from_slice(&riff_size.to_le_bytes());
    output.extend_from_slice(b"WEBPVP8L");
    output.extend_from_slice(&data_size.to_le_bytes());
    output.extend_from_slice(&data);
    if data.len() & 1 != 0 {
        output.push(0);
    }
    output
}

fn bmp(width: u32, height: u32) -> Vec<u8> {
    let row_bytes = (width * 24).div_ceil(32) * 4;
    let pixel_bytes = row_bytes * height;
    let pixel_offset = 54_u32;
    let file_size = pixel_offset + pixel_bytes;
    let mut output = Vec::new();
    output.extend_from_slice(b"BM");
    output.extend_from_slice(&file_size.to_le_bytes());
    output.extend_from_slice(&[0; 4]);
    output.extend_from_slice(&pixel_offset.to_le_bytes());
    output.extend_from_slice(&40_u32.to_le_bytes());
    let Ok(width) = i32::try_from(width) else {
        panic!("test BMP width exceeds i32");
    };
    let Ok(height) = i32::try_from(height) else {
        panic!("test BMP height exceeds i32");
    };
    output.extend_from_slice(&width.to_le_bytes());
    output.extend_from_slice(&height.to_le_bytes());
    output.extend_from_slice(&1_u16.to_le_bytes());
    output.extend_from_slice(&24_u16.to_le_bytes());
    output.extend_from_slice(&[0; 24]);
    let Ok(file_size) = usize::try_from(file_size) else {
        panic!("test BMP size exceeds usize");
    };
    output.resize(file_size, 0);
    output
}

fn crc32(bytes: &[u8]) -> u32 {
    let mut crc = u32::MAX;
    for byte in bytes {
        crc ^= u32::from(*byte);
        for _ in 0..8 {
            crc = (crc >> 1) ^ (0xedb8_8320 & (0_u32.wrapping_sub(crc & 1)));
        }
    }
    !crc
}

fn assert_code<T>(result: Result<T, impl ErrorCode>, expected: &str) {
    match result {
        Ok(_) => panic!("expected {expected}"),
        Err(error) => assert_eq!(error.error_code(), expected),
    }
}

trait ErrorCode {
    fn error_code(&self) -> &str;
}

impl ErrorCode for hwpx_package::AssetError {
    fn error_code(&self) -> &str {
        self.code()
    }
}
